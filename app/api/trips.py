from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.trip import Trip, TripStatus
from app.models.bus import Bus
from app.models.route import Route
from app.models.user import User, UserRole
from app.schemas.trip import TripCreate, TripResponse
from app.api.deps import require_driver, get_current_user, require_admin

router = APIRouter(prefix="/trips", tags=["Trip Management"])

@router.get("", response_model=List[TripResponse])
def list_trips(
    status: Optional[str] = Query(None),
    bus_id: Optional[int] = Query(None),
    driver_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user)
):
    query = db.query(Trip)
    if status:
        query = query.filter(Trip.status == status.upper())
    if bus_id:
        query = query.filter(Trip.bus_id == bus_id)
    if driver_id:
        query = query.filter(Trip.driver_id == driver_id)
    return query.order_by(Trip.id.desc()).all()

@router.get("/driver/active", response_model=Optional[TripResponse])
def get_driver_active_trip(
    db: Session = Depends(get_db),
    current_driver: User = Depends(require_driver)
):
    """Returns the driver's currently active trip, or assigned upcoming trip."""
    # First check ACTIVE trip
    trip = db.query(Trip).filter(
        Trip.driver_id == current_driver.id,
        Trip.status == TripStatus.ACTIVE.value
    ).first()

    if not trip:
        # Check NOT_STARTED trip
        trip = db.query(Trip).filter(
            Trip.driver_id == current_driver.id,
            Trip.status == TripStatus.NOT_STARTED.value
        ).order_by(Trip.id.asc()).first()

    return trip

@router.post("", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
def create_trip(
    trip_in: TripCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_driver)
):
    # Verify bus and route exist
    bus = db.query(Bus).filter(Bus.id == trip_in.bus_id).first()
    if not bus or not bus.is_active:
        raise HTTPException(status_code=404, detail="Active bus not found")

    route = db.query(Route).filter(Route.id == trip_in.route_id).first()
    if not route or not route.is_active:
        raise HTTPException(status_code=404, detail="Active route not found")

    # If driver is creating, ensure they are assigned or admin
    driver_id = trip_in.driver_id
    if current_user.role == UserRole.DRIVER.value:
        driver_id = current_user.id

    trip = Trip(
        bus_id=trip_in.bus_id,
        driver_id=driver_id,
        route_id=trip_in.route_id,
        trip_name=trip_in.trip_name,
        trip_type=trip_in.trip_type,
        status=TripStatus.NOT_STARTED.value
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip

@router.post("/{trip_id}/start", response_model=TripResponse)
def start_trip(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_driver)
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if current_user.role == UserRole.DRIVER.value and trip.driver_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to start this trip")

    if trip.status == TripStatus.ACTIVE.value:
        return trip # Already active

    if trip.status in [TripStatus.COMPLETED.value, TripStatus.CANCELLED.value]:
        raise HTTPException(status_code=400, detail=f"Cannot start a {trip.status.lower()} trip")

    trip.status = TripStatus.ACTIVE.value
    trip.start_time = datetime.now(timezone.utc)
    
    # Update bus status
    if trip.bus:
        trip.bus.status = "ON_TRIP"

    db.commit()
    db.refresh(trip)
    return trip

@router.post("/{trip_id}/stop", response_model=TripResponse)
def stop_trip(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_driver)
):
    """Stops an active trip. GPS tracking immediately shuts down."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if current_user.role == UserRole.DRIVER.value and trip.driver_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to stop this trip")

    if trip.status != TripStatus.ACTIVE.value:
        raise HTTPException(status_code=400, detail="Only active trips can be stopped")

    trip.status = TripStatus.COMPLETED.value
    trip.end_time = datetime.now(timezone.utc)

    # Bus is now IDLE
    if trip.bus:
        trip.bus.status = "IDLE"

    # Expire all active passenger sessions for this trip
    from app.services.passenger_location_service import expire_old_sessions
    expire_old_sessions(trip_id=trip.id, db=db)

    db.commit()
    db.refresh(trip)
    return trip

@router.post("/{trip_id}/cancel", response_model=TripResponse)
def cancel_trip(
    trip_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    trip.status = TripStatus.CANCELLED.value
    trip.end_time = datetime.now(timezone.utc)
    if trip.bus:
        trip.bus.status = "IDLE"
    from app.services.passenger_location_service import expire_old_sessions
    expire_old_sessions(trip_id=trip.id, db=db)
    db.commit()
    db.refresh(trip)
    return trip
