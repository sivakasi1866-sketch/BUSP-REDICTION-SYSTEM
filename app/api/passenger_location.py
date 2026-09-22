"""
API Router — Passenger-Assisted Bus Location ("I'm On This Bus")

Endpoints:
  POST   /api/passenger-location/start-session   → consent + create session
  POST   /api/passenger-location/ping            → submit location ping
  DELETE /api/passenger-location/stop-session    → stop own session
  GET    /api/passenger-location/my-session      → own session status only
  GET    /api/passenger-location/bus-position/{trip_id} → anonymised bus position

Security:
  - All endpoints require authentication (student or staff)
  - Passengers can only touch their own session
  - bus-position returns aggregated position only — no individual coordinates
"""
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from app.database import get_db
from app.models.passenger_session import PassengerSession, PassengerLocationPing, SessionStatus
from app.models.trip import Trip, TripStatus
from app.models.assignment import DefaultAssignment, SpecialAssignment
from app.models.route import Stop
from app.models.user import User, UserRole
from app.schemas.passenger_session import (
    StartSessionRequest, PassengerPingCreate,
    SessionStatusResponse, PassengerPingResponse, BusPositionResponse
)
from app.api.deps import get_current_user
from app.services.passenger_location_service import (
    validate_passenger_ping, estimate_bus_position, expire_timed_out_sessions
)

router = APIRouter(prefix="/passenger-location", tags=["Passenger-Assisted Location"])


def _require_passenger(current_user: User = Depends(get_current_user)) -> User:
    """Only STUDENT or STAFF can use passenger-location endpoints."""
    if current_user.role not in (UserRole.STUDENT.value, UserRole.STAFF.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students and staff can use passenger-assisted location"
        )
    return current_user


def _get_user_bus_and_trip(current_user: User, db: Session):
    """
    Resolves the passenger's assigned bus and its active trip.
    Returns (bus_id, active_trip | None).
    """
    today = date.today()
    special = db.query(SpecialAssignment).filter(
        SpecialAssignment.user_id      == current_user.id,
        SpecialAssignment.effective_date == today,
        SpecialAssignment.is_active    == True,
    ).first()
    bus_id = special.bus_id if special else None

    if not bus_id:
        default = db.query(DefaultAssignment).filter(
            DefaultAssignment.user_id  == current_user.id,
            DefaultAssignment.is_active == True,
        ).first()
        bus_id = default.bus_id if default else None

    if not bus_id:
        return None, None

    active_trip = db.query(Trip).filter(
        Trip.bus_id == bus_id,
        Trip.status == TripStatus.ACTIVE.value,
    ).order_by(Trip.id.desc()).first()

    return bus_id, active_trip


# ── POST /start-session ───────────────────────────────────────────────────────

@router.post("/start-session", response_model=SessionStatusResponse,
             status_code=status.HTTP_201_CREATED)
def start_passenger_session(
    body: StartSessionRequest,
    db:   Session = Depends(get_db),
    current_user: User = Depends(_require_passenger),
):
    """
    Creates a passenger location-sharing session.
    Requires explicit consent (body.consent == True).
    Passenger must have an active trip on their allocated bus.
    """
    if not body.consent:
        raise HTTPException(
            status_code=400,
            detail="Explicit consent is required to start a passenger location session."
        )

    # Expire any timed-out sessions first (lightweight housekeeping)
    expire_timed_out_sessions(db)

    # Resolve bus and active trip
    bus_id, active_trip = _get_user_bus_and_trip(current_user, db)
    if not bus_id:
        raise HTTPException(status_code=404, detail="No bus assignment found for your account.")
    if not active_trip:
        raise HTTPException(
            status_code=400,
            detail="Your bus is not currently on an active trip. Passenger location sharing requires an active trip."
        )

    # Check for an already-active session for this user+trip
    existing = db.query(PassengerSession).filter(
        PassengerSession.user_id == current_user.id,
        PassengerSession.trip_id == active_trip.id,
        PassengerSession.status  == SessionStatus.ACTIVE.value,
    ).first()
    if existing:
        return existing  # Return existing session idempotently

    now = datetime.now(timezone.utc)
    session = PassengerSession(
        user_id       = current_user.id,
        trip_id       = active_trip.id,
        bus_id        = bus_id,
        status        = SessionStatus.ACTIVE.value,
        consent_given = True,
        started_at    = now,
        expires_at    = now + timedelta(hours=4),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


# ── POST /ping ────────────────────────────────────────────────────────────────

@router.post("/ping", response_model=PassengerPingResponse,
             status_code=status.HTTP_201_CREATED)
def submit_passenger_ping(
    ping_in:      PassengerPingCreate,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(_require_passenger),
):
    """
    Submits a single passenger GPS ping.
    The ping is validated, confidence-scored, and stored anonymously.
    """
    # Verify session ownership — passenger cannot post to another user's session
    session = db.query(PassengerSession).filter(
        PassengerSession.id      == ping_in.session_id,
        PassengerSession.user_id == current_user.id,
        PassengerSession.status  == SessionStatus.ACTIVE.value,
    ).first()
    if not session:
        raise HTTPException(
            status_code=403,
            detail="No active passenger session found. Start a session first."
        )

    # Verify the session's trip is still ACTIVE
    trip = db.query(Trip).filter(Trip.id == session.trip_id).first()
    if not trip or trip.status != TripStatus.ACTIVE.value:
        # Auto-expire the session
        session.status   = SessionStatus.EXPIRED.value
        session.ended_at = datetime.now(timezone.utc)
        db.commit()
        raise HTTPException(
            status_code=400,
            detail="Trip is no longer active. Passenger location session has been ended."
        )

    # Check session hard expiry
    now = datetime.now(timezone.utc)
    exp = session.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    if now > exp:
        session.status   = SessionStatus.EXPIRED.value
        session.ended_at = now
        db.commit()
        raise HTTPException(status_code=400, detail="Passenger location session has expired.")

    # Load route stops for validation
    stops = db.query(Stop).filter(Stop.route_id == trip.route_id).all()

    # Validate ping
    validation_status, confidence_score = validate_passenger_ping(
        lat             = ping_in.latitude,
        lon             = ping_in.longitude,
        accuracy_meters = ping_in.accuracy_meters,
        speed_kmh       = ping_in.speed_kmh,
        timestamp       = now,
        stops           = stops,
    )

    ping_record = PassengerLocationPing(
        session_id        = session.id,
        trip_id           = trip.id,
        timestamp         = now,
        latitude          = ping_in.latitude,
        longitude         = ping_in.longitude,
        accuracy_meters   = ping_in.accuracy_meters,
        speed_kmh         = ping_in.speed_kmh,
        heading           = ping_in.heading,
        validation_status = validation_status,
        confidence_score  = confidence_score,
    )
    db.add(ping_record)
    session.last_ping_at = now
    db.commit()
    db.refresh(ping_record)
    return ping_record


# ── DELETE /stop-session ──────────────────────────────────────────────────────

@router.delete("/stop-session", status_code=status.HTTP_200_OK)
def stop_passenger_session(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(_require_passenger),
):
    """Immediately stops the caller's active passenger location session."""
    session = db.query(PassengerSession).filter(
        PassengerSession.user_id == current_user.id,
        PassengerSession.status  == SessionStatus.ACTIVE.value,
    ).order_by(PassengerSession.id.desc()).first()

    if not session:
        return {"detail": "No active passenger location session found.", "stopped": False}

    session.status   = SessionStatus.STOPPED.value
    session.ended_at = datetime.now(timezone.utc)
    db.commit()
    return {"detail": "Location sharing stopped.", "stopped": True, "session_id": session.id}


# ── GET /my-session ───────────────────────────────────────────────────────────

@router.get("/my-session", response_model=Optional[SessionStatusResponse])
def get_my_session(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(_require_passenger),
):
    """Returns the caller's own active session status. Never returns other users' data."""
    session = db.query(PassengerSession).filter(
        PassengerSession.user_id == current_user.id,
        PassengerSession.status  == SessionStatus.ACTIVE.value,
    ).order_by(PassengerSession.id.desc()).first()
    return session


# ── GET /bus-position/{trip_id} ───────────────────────────────────────────────

@router.get("/bus-position/{trip_id}", response_model=BusPositionResponse)
def get_bus_position(
    trip_id:      int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    """
    Returns the aggregated, anonymised bus position for a trip.
    Safe for all authenticated users — contains NO passenger identity or exact location.
    """
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found.")

    position = estimate_bus_position(trip=trip, db=db)
    return position


# ── GET /trip-status ─────────────────────────────────────────────────────────

@router.get("/trip-status")
def get_my_trip_status(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(_require_passenger),
):
    """
    Returns the passenger's allocated bus and its trip status.
    Used by the frontend to decide whether to show the I'M ON THIS BUS button.
    """
    bus_id, active_trip = _get_user_bus_and_trip(current_user, db)

    if not bus_id:
        return {"has_assignment": False, "has_active_trip": False}

    # Check for existing active session
    existing_session = None
    if active_trip:
        existing_session = db.query(PassengerSession).filter(
            PassengerSession.user_id == current_user.id,
            PassengerSession.trip_id == active_trip.id,
            PassengerSession.status  == SessionStatus.ACTIVE.value,
        ).first()

    return {
        "has_assignment":  True,
        "has_active_trip": active_trip is not None,
        "bus_id":          bus_id,
        "trip_id":         active_trip.id if active_trip else None,
        "bus_number":      active_trip.bus.bus_number if active_trip and active_trip.bus else None,
        "route_name":      active_trip.route.route_name if active_trip and active_trip.route else None,
        "trip_status":     active_trip.status if active_trip else None,
        "session_active":  existing_session is not None,
        "session_id":      existing_session.id if existing_session else None,
    }
