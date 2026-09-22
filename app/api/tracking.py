from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.trip import Trip, TripStatus, GPSPing
from app.models.bus import Bus
from app.models.route import Route, Stop
from app.models.assignment import DefaultAssignment, SpecialAssignment
from app.models.user import User, UserRole
from app.schemas.trip import GPSPingCreate, GPSPingResponse, TripLiveStatusResponse, TripResponse
from app.schemas.eta import StopETAResponse
from app.api.deps import require_driver, get_current_user, require_admin
from app.services.eta_service import calculate_trip_stops_eta
from app.services.notification_service import check_and_create_arrival_notifications
from app.ml.feature_engineering import haversine_distance

router = APIRouter(prefix="/tracking", tags=["Live Tracking & GPS"])

@router.post("/ping", response_model=GPSPingResponse, status_code=status.HTTP_201_CREATED)
def submit_gps_ping(
    ping_in: GPSPingCreate,
    db: Session = Depends(get_db),
    current_driver: User = Depends(require_driver)
):
    """
    Trip-scoped GPS ping ingestion.
    Strictly requires an ACTIVE trip. Rejects pings before trip starts or after trip ends.
    """
    trip = db.query(Trip).filter(Trip.id == ping_in.trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    # Ensure only assigned driver or admin can submit GPS
    if current_driver.role == UserRole.DRIVER.value and trip.driver_id != current_driver.id:
        raise HTTPException(status_code=403, detail="Not authorized to submit GPS for this trip")

    # Strict trip-scoped validation
    if trip.status != TripStatus.ACTIVE.value:
        raise HTTPException(
            status_code=400,
            detail=f"GPS tracking is disabled. Trip is currently {trip.status}. Tracking is only permitted for ACTIVE trips."
        )

    # Record GPS Ping
    now = datetime.now(timezone.utc)
    gps_record = GPSPing(
        trip_id=trip.id,
        timestamp=now,
        latitude=ping_in.latitude,
        longitude=ping_in.longitude,
        speed_kmh=ping_in.speed_kmh,
        heading=ping_in.heading,
        accuracy_meters=ping_in.accuracy_meters,
        is_simulated=ping_in.is_simulated
    )
    db.add(gps_record)

    # Update latest trip state
    trip.current_latitude = ping_in.latitude
    trip.current_longitude = ping_in.longitude
    trip.current_speed_kmh = ping_in.speed_kmh
    trip.current_heading = ping_in.heading
    trip.last_ping_time = now

    # Check progress along route stops
    stops = db.query(Stop).filter(Stop.route_id == trip.route_id).order_by(Stop.sequence.asc()).all()
    if stops:
        # Check if bus has arrived near current stop or next stop
        current_seq = trip.current_stop_sequence or 1
        for s in stops:
            if s.sequence >= current_seq:
                dist = haversine_distance(ping_in.latitude, ping_in.longitude, s.latitude, s.longitude)
                # Within 120m considered passed/reached
                if dist <= 0.12 and s.sequence == current_seq:
                    # Move to next stop if not the last stop
                    if current_seq < len(stops):
                        trip.current_stop_sequence = current_seq + 1
                    break

        # Calculate ETAs for all stops
        stops_eta = calculate_trip_stops_eta(
            trip=trip,
            stops=stops,
            current_lat=ping_in.latitude,
            current_lon=ping_in.longitude,
            current_speed_kmh=ping_in.speed_kmh
        )

        # Trigger arrival notifications for stops
        for s_eta in stops_eta:
            check_and_create_arrival_notifications(
                db=db,
                trip=trip,
                stop_id=s_eta["stop_id"],
                stop_name=s_eta["stop_name"],
                eta_minutes=s_eta["final_eta_minutes"]
            )

    db.commit()
    db.refresh(gps_record)
    return gps_record

@router.get("/trip/{trip_id}/live", response_model=TripLiveStatusResponse)
def get_trip_live_status(
    trip_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user)
):
    """Returns live telemetry, bus position, and stop-by-stop ETAs for a given trip."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    stops = db.query(Stop).filter(Stop.route_id == trip.route_id).order_by(Stop.sequence.asc()).all()
    stops_eta = []
    if stops:
        stops_eta = calculate_trip_stops_eta(
            trip=trip,
            stops=stops,
            current_lat=trip.current_latitude,
            current_lon=trip.current_longitude,
            current_speed_kmh=trip.current_speed_kmh or 0.0
        )

    return {
        "trip": trip,
        "stops_eta": stops_eta
    }

@router.get("/my-bus", response_model=Optional[TripLiveStatusResponse])
def get_my_bus_tracking(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns live tracking for the student or staff member's allocated bus.
    Enforces privacy: Never tracks the student; only tracks the bus!
    """
    from datetime import date
    today = date.today()

    # 1. Check special assignment
    special = db.query(SpecialAssignment).filter(
        SpecialAssignment.user_id == current_user.id,
        SpecialAssignment.effective_date == today,
        SpecialAssignment.is_active == True
    ).first()

    bus_id = special.bus_id if special else None

    # 2. Fall back to default assignment
    if not bus_id:
        default = db.query(DefaultAssignment).filter(
            DefaultAssignment.user_id == current_user.id,
            DefaultAssignment.is_active == True
        ).first()
        if default:
            bus_id = default.bus_id

    if not bus_id:
        return None

    # Find active trip for this bus
    active_trip = db.query(Trip).filter(
        Trip.bus_id == bus_id,
        Trip.status == TripStatus.ACTIVE.value
    ).order_by(Trip.id.desc()).first()

    if not active_trip:
        # If no active trip, check most recent or upcoming trip
        recent_trip = db.query(Trip).filter(
            Trip.bus_id == bus_id
        ).order_by(Trip.id.desc()).first()
        if not recent_trip:
            return None
        active_trip = recent_trip

    stops = db.query(Stop).filter(Stop.route_id == active_trip.route_id).order_by(Stop.sequence.asc()).all()
    stops_eta = calculate_trip_stops_eta(
        trip=active_trip,
        stops=stops,
        current_lat=active_trip.current_latitude,
        current_lon=active_trip.current_longitude,
        current_speed_kmh=active_trip.current_speed_kmh or 0.0
    )

    # Enrich with passenger-assisted location position/confidence
    from app.services.passenger_location_service import estimate_bus_position
    bus_position = estimate_bus_position(trip=active_trip, db=db)

    return {
        "trip": active_trip,
        "stops_eta": stops_eta,
        "location_source":     bus_position["source"],
        "location_confidence": bus_position["confidence"],
        "location_label":      bus_position["label"],
        "contributor_count":   bus_position["contributor_count"],
        "effective_latitude":  bus_position["latitude"],
        "effective_longitude": bus_position["longitude"],
    }

@router.get("/fleet/live")
def get_live_fleet(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    """Admin live fleet tracking: returns all active buses, GPS state, and passenger contributor info."""
    from app.services.passenger_location_service import estimate_bus_position
    active_trips = db.query(Trip).filter(Trip.status == TripStatus.ACTIVE.value).all()
    fleet = []
    for t in active_trips:
        pos = estimate_bus_position(trip=t, db=db)
        fleet.append({
            "trip_id":              t.id,
            "bus_id":               t.bus_id,
            "bus_number":           t.bus.bus_number if t.bus else "Unknown",
            "registration_number":  t.bus.registration_number if t.bus else "",
            "route_name":           t.route.route_name if t.route else "",
            "driver_name":          t.driver.full_name if t.driver else "",
            "latitude":             pos["latitude"],
            "longitude":            pos["longitude"],
            "speed_kmh":            t.current_speed_kmh,
            "heading":              t.current_heading,
            "last_ping_time":       t.last_ping_time,
            # Location source metadata (privacy-safe — no passenger identity)
            "location_source":      pos["source"],
            "location_confidence":  pos["confidence"],
            "location_label":       pos["label"],
            "contributor_count":    pos["contributor_count"],
            "driver_gps_age_sec":   pos["driver_gps_age_sec"],
        })
    return fleet
