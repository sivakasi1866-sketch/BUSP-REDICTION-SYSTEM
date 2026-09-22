"""
Tests for the "I'm On This Bus" Passenger-Assisted Location Feature.
Uses a completely isolated in-memory SQLite database, separate from other test modules.
"""
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.core.security import get_password_hash
from app.services.passenger_location_service import (
    validate_passenger_ping, estimate_bus_position,
    expire_old_sessions, expire_timed_out_sessions
)
from app.models.passenger_session import PassengerSession, PassengerLocationPing, SessionStatus, PingValidation

# ── Isolated test DB ──────────────────────────────────────────────────────────
_DB_URL = "sqlite:///./test_passenger_isolated.db"
_engine = create_engine(_DB_URL, connect_args={"check_same_thread": False})
_Session = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def _override_get_db():
    db = _Session()
    try:
        yield db
    finally:
        db.close()


# Build and tear down the schema once per module
@pytest.fixture(scope="module", autouse=True)
def _schema():
    Base.metadata.create_all(bind=_engine)
    yield
    _engine.dispose()
    Base.metadata.drop_all(bind=_engine)
    import os
    try:
        os.remove("test_passenger_isolated.db")
    except (PermissionError, FileNotFoundError):
        pass  # Windows may hold the file; harmless — file will be cleaned on next run


@pytest.fixture(scope="module")
def _app():
    """Return FastAPI app with DB override applied."""
    from app.main import app
    app.dependency_overrides[get_db] = _override_get_db
    yield app
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture(scope="module")
def client(_app):
    return TestClient(_app)


@pytest.fixture(scope="module")
def seed(_app):
    """
    Seeds a self-contained set of test data into the isolated DB.
    All tests in this module share this seed (module scope).
    """
    from app.models.user import User, UserRole, StudentProfile
    from app.models.bus import Bus
    from app.models.route import Route, Stop
    from app.models.assignment import DefaultAssignment
    from app.models.trip import Trip, TripStatus

    db = _Session()

    # Route + stops (Salem-area coordinates close together)
    route = Route(route_name="Passenger Test Route",
                  route_code="PT-99", is_active=True)
    db.add(route); db.flush()

    stops = []
    for i, (lat, lon) in enumerate([(11.720, 78.030), (11.730, 78.040), (11.740, 78.050)]):
        s = Stop(route_id=route.id, stop_name=f"PTest Stop {i+1}",
                 sequence=i+1, latitude=lat, longitude=lon,
                 scheduled_offset_minutes=i*10, is_active=True)
        db.add(s); stops.append(s)
    db.flush()

    # Bus
    bus = Bus(bus_number="PTEST-01", registration_number="TN-38-CB-PTEST",
              capacity=50, is_active=True, status="IDLE", default_route_id=route.id)
    db.add(bus); db.flush()

    # Driver
    driver = User(username="ptest_driver", email="pdriver@test.ac.in",
                  full_name="PTest Driver",
                  hashed_password=get_password_hash("drv123"),
                  role=UserRole.DRIVER.value, is_active=True)
    db.add(driver); db.flush()

    # Two students
    s1 = User(username="ptest_s1", email="ps1@test.ac.in", full_name="PTest Student 1",
              hashed_password=get_password_hash("stu123"),
              role=UserRole.STUDENT.value, is_active=True)
    s2 = User(username="ptest_s2", email="ps2@test.ac.in", full_name="PTest Student 2",
              hashed_password=get_password_hash("stu123"),
              role=UserRole.STUDENT.value, is_active=True)
    db.add_all([s1, s2]); db.flush()
    db.add(StudentProfile(user_id=s1.id, roll_number="PT001", department="CS", year=2, semester=3))
    db.add(StudentProfile(user_id=s2.id, roll_number="PT002", department="EC", year=2, semester=3))

    # Assign both students to bus
    db.add(DefaultAssignment(user_id=s1.id, bus_id=bus.id,
                             stop_id=stops[0].id, academic_year="2025-2026"))
    db.add(DefaultAssignment(user_id=s2.id, bus_id=bus.id,
                             stop_id=stops[1].id, academic_year="2025-2026"))

    # Active trip (driver GPS is stale by default — 120s old)
    trip = Trip(
        bus_id=bus.id, driver_id=driver.id, route_id=route.id,
        trip_name="PTest Morning Pickup", trip_type="MORNING_PICKUP",
        status=TripStatus.ACTIVE.value,
        start_time=datetime.now(timezone.utc),
        current_latitude=11.720, current_longitude=78.030,
        current_speed_kmh=30.0, current_stop_sequence=1,
        last_ping_time=datetime.now(timezone.utc) - timedelta(seconds=120)
    )
    db.add(trip); db.flush()
    bus.status = "ON_TRIP"
    db.commit()

    yield {
        "route": route, "stops": stops, "bus": bus,
        "driver": driver, "s1": s1, "s2": s2, "trip": trip,
    }

    db.close()


# ── Helper ────────────────────────────────────────────────────────────────────
def tok(client, username, password="stu123"):
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, f"Login failed for {username}: {r.json()}"
    return r.json()["access_token"]


def hdr(token):
    return {"Authorization": f"Bearer {token}"}


# ─────────────────────────────────────────────────────────────────────────────
# Session creation & consent
# ─────────────────────────────────────────────────────────────────────────────

def test_session_requires_explicit_consent(client, seed):
    """Consent must be True — session blocked if False."""
    t = tok(client, "ptest_s1")
    r = client.post("/api/passenger-location/start-session",
                    json={"consent": False}, headers=hdr(t))
    assert r.status_code == 400
    assert "consent" in r.json()["detail"].lower()


def test_session_starts_with_consent_and_active_trip(client, seed):
    """Session created when consent=True and trip is ACTIVE."""
    t = tok(client, "ptest_s1")
    r = client.post("/api/passenger-location/start-session",
                    json={"consent": True}, headers=hdr(t))
    assert r.status_code == 201
    d = r.json()
    assert d["status"] == "ACTIVE"
    assert d["consent_given"] is True
    assert d["trip_id"] == seed["trip"].id
    assert d["bus_id"]  == seed["bus"].id


def test_second_session_returns_existing_idempotently(client, seed):
    """Starting session twice returns the same session (no duplicate)."""
    t = tok(client, "ptest_s1")
    h = hdr(t)
    r1 = client.post("/api/passenger-location/start-session", json={"consent": True}, headers=h)
    r2 = client.post("/api/passenger-location/start-session", json={"consent": True}, headers=h)
    assert r1.json()["id"] == r2.json()["id"]


def test_driver_cannot_start_passenger_session(client, seed):
    """Only STUDENT or STAFF may start a passenger session."""
    t = tok(client, "ptest_driver", "drv123")
    r = client.post("/api/passenger-location/start-session",
                    json={"consent": True}, headers=hdr(t))
    assert r.status_code == 403


# ─────────────────────────────────────────────────────────────────────────────
# Ping submission & security
# ─────────────────────────────────────────────────────────────────────────────

def _get_session_id(client, username):
    """Ensure an active session exists for username and return its id."""
    t = tok(client, username)
    r = client.post("/api/passenger-location/start-session",
                    json={"consent": True}, headers=hdr(t))
    return r.json()["id"], t


def test_ping_rejected_with_fake_session(client, seed):
    """Ping using a nonexistent session_id is rejected."""
    t = tok(client, "ptest_s2")
    # Stop any existing session first
    client.delete("/api/passenger-location/stop-session", headers=hdr(t))
    r = client.post("/api/passenger-location/ping",
                    json={"session_id": 999999, "latitude": 11.72,
                          "longitude": 78.03, "accuracy_meters": 10.0},
                    headers=hdr(t))
    assert r.status_code == 403


def test_valid_ping_accepted(client, seed):
    """Valid ping near route is accepted with VALID status."""
    sid, t = _get_session_id(client, "ptest_s1")
    r = client.post("/api/passenger-location/ping",
                    json={"session_id": sid, "latitude": 11.725,
                          "longitude": 78.035, "accuracy_meters": 12.0,
                          "speed_kmh": 30.0},
                    headers=hdr(t))
    assert r.status_code == 201
    assert r.json()["validation_status"] == "VALID"
    assert r.json()["confidence_score"] > 0.5


def test_inaccurate_ping_rejected(client, seed):
    """Ping with accuracy > 150 m is REJECTED."""
    sid, t = _get_session_id(client, "ptest_s1")
    r = client.post("/api/passenger-location/ping",
                    json={"session_id": sid, "latitude": 11.72,
                          "longitude": 78.03, "accuracy_meters": 200.0},
                    headers=hdr(t))
    assert r.status_code == 201
    assert r.json()["validation_status"] == "REJECTED"


def test_impossible_speed_ping_rejected(client, seed):
    """Ping with speed > 120 km/h is REJECTED."""
    sid, t = _get_session_id(client, "ptest_s1")
    r = client.post("/api/passenger-location/ping",
                    json={"session_id": sid, "latitude": 11.72,
                          "longitude": 78.03, "accuracy_meters": 10.0,
                          "speed_kmh": 200.0},
                    headers=hdr(t))
    assert r.status_code == 201
    assert r.json()["validation_status"] == "REJECTED"


def test_off_route_ping_is_outlier(client, seed):
    """Ping > 2 km from all route stops is OUTLIER or REJECTED."""
    sid, t = _get_session_id(client, "ptest_s1")
    r = client.post("/api/passenger-location/ping",
                    json={"session_id": sid,
                          "latitude": 13.0827, "longitude": 80.2707,  # Chennai
                          "accuracy_meters": 10.0},
                    headers=hdr(t))
    assert r.status_code == 201
    assert r.json()["validation_status"] in ("OUTLIER", "REJECTED")


def test_student_cannot_use_another_students_session(client, seed):
    """Student 1 cannot submit a ping using Student 2's session_id."""
    sid2, _ = _get_session_id(client, "ptest_s2")
    t1 = tok(client, "ptest_s1")
    r = client.post("/api/passenger-location/ping",
                    json={"session_id": sid2, "latitude": 11.72,
                          "longitude": 78.03, "accuracy_meters": 10.0},
                    headers=hdr(t1))
    assert r.status_code == 403


# ─────────────────────────────────────────────────────────────────────────────
# Bus position estimation & privacy
# ─────────────────────────────────────────────────────────────────────────────

def test_bus_position_driver_gps_fresh(seed):
    """estimate_bus_position returns DRIVER_GPS / HIGH when driver ping is recent."""
    db = _Session()
    trip = db.query(__import__("app.models.trip", fromlist=["Trip"]).Trip
                    ).filter_by(id=seed["trip"].id).first()
    trip.last_ping_time = datetime.now(timezone.utc) - timedelta(seconds=10)
    trip.current_latitude  = 11.725
    trip.current_longitude = 78.035
    db.commit()

    pos = estimate_bus_position(trip=trip, db=db)
    assert pos["source"]     == "DRIVER_GPS"
    assert pos["confidence"] == "HIGH"
    assert pos["label"]      == "Live GPS"
    db.close()


def test_bus_position_passenger_fallback_when_driver_stale(seed):
    """estimate_bus_position uses passenger data when driver GPS > 45 s stale."""
    from app.models.trip import Trip
    db = _Session()
    trip = db.query(Trip).filter_by(id=seed["trip"].id).first()
    trip.last_ping_time = datetime.now(timezone.utc) - timedelta(seconds=90)
    db.commit()

    # Create a fresh valid passenger ping
    sess = PassengerSession(
        user_id=seed["s1"].id, trip_id=trip.id, bus_id=seed["bus"].id,
        status=SessionStatus.ACTIVE.value, consent_given=True,
        started_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
    )
    db.add(sess); db.flush()
    ping = PassengerLocationPing(
        session_id=sess.id, trip_id=trip.id,
        timestamp=datetime.now(timezone.utc),
        latitude=11.727, longitude=78.037,
        accuracy_meters=15.0, speed_kmh=30.0,
        validation_status=PingValidation.VALID.value,
        confidence_score=0.9,
    )
    db.add(ping); db.commit()

    pos = estimate_bus_position(trip=trip, db=db)
    assert pos["source"] in ("PASSENGER_ASSISTED", "COMBINED")
    assert pos["confidence"] in ("MEDIUM", "HIGH")
    assert pos["contributor_count"] >= 1
    db.close()


def test_bus_position_api_hides_passenger_identity(client, seed):
    """GET /bus-position/{trip_id} must never expose passenger identity."""
    t = tok(client, "ptest_s1")
    trip_id = seed["trip"].id
    r = client.get(f"/api/passenger-location/bus-position/{trip_id}", headers=hdr(t))
    assert r.status_code == 200
    d = r.json()
    for forbidden in ("user_id", "username", "full_name", "phone", "email"):
        assert forbidden not in d, f"Privacy violation: '{forbidden}' found in bus-position response"
    for required in ("source", "confidence", "contributor_count", "label"):
        assert required in d


def test_my_session_returns_only_own_session(client, seed):
    """my-session returns the caller's own session, not another user's."""
    t1 = tok(client, "ptest_s1")
    t2 = tok(client, "ptest_s2")
    # Clean slate — stop any running sessions
    client.delete("/api/passenger-location/stop-session", headers=hdr(t1))
    client.delete("/api/passenger-location/stop-session", headers=hdr(t2))
    # Start fresh sessions
    r1s = client.post("/api/passenger-location/start-session",
                      json={"consent": True}, headers=hdr(t1))
    r2s = client.post("/api/passenger-location/start-session",
                      json={"consent": True}, headers=hdr(t2))
    assert r1s.json()["status"] == "ACTIVE"
    assert r2s.json()["status"] == "ACTIVE"

    r1 = client.get("/api/passenger-location/my-session", headers=hdr(t1)).json()
    r2 = client.get("/api/passenger-location/my-session", headers=hdr(t2)).json()
    assert r1 is not None and r1["user_id"] == seed["s1"].id
    assert r2 is not None and r2["user_id"] == seed["s2"].id


# ─────────────────────────────────────────────────────────────────────────────
# Stop sharing & expiry
# ─────────────────────────────────────────────────────────────────────────────

def test_stop_sharing_immediately_ends_session(client, seed):
    """Stop Sharing sets session status to STOPPED instantly."""
    t = tok(client, "ptest_s1")
    h = hdr(t)
    client.post("/api/passenger-location/start-session", json={"consent": True}, headers=h)
    r = client.delete("/api/passenger-location/stop-session", headers=h)
    assert r.status_code == 200
    assert r.json()["stopped"] is True

    check = client.get("/api/passenger-location/my-session", headers=h).json()
    assert check is None


def test_session_expires_when_trip_ends(seed):
    """expire_old_sessions sets all active sessions for a trip to EXPIRED."""
    db = _Session()
    s = PassengerSession(
        user_id=seed["s1"].id, trip_id=seed["trip"].id,
        bus_id=seed["bus"].id, status=SessionStatus.ACTIVE.value,
        consent_given=True,
        started_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
    )
    db.add(s); db.commit()

    count = expire_old_sessions(trip_id=seed["trip"].id, db=db)
    assert count >= 1
    db.refresh(s)
    assert s.status == SessionStatus.EXPIRED.value
    assert s.ended_at is not None
    db.close()


def test_hard_expiry_sweep(seed):
    """expire_timed_out_sessions cleans up sessions past their expiry time."""
    db = _Session()
    old = PassengerSession(
        user_id=seed["s2"].id, trip_id=seed["trip"].id,
        bus_id=seed["bus"].id, status=SessionStatus.ACTIVE.value,
        consent_given=True,
        started_at=datetime.now(timezone.utc) - timedelta(hours=5),
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    db.add(old); db.commit()
    count = expire_timed_out_sessions(db=db)
    assert count >= 1
    db.refresh(old)
    assert old.status == SessionStatus.EXPIRED.value
    db.close()


# ─────────────────────────────────────────────────────────────────────────────
# Unit: validation logic
# ─────────────────────────────────────────────────────────────────────────────

def test_validate_valid_ping(seed):
    stops = seed["stops"]
    now = datetime.now(timezone.utc)
    status, score = validate_passenger_ping(
        lat=11.725, lon=78.035,
        accuracy_meters=10.0, speed_kmh=30.0,
        timestamp=now, stops=stops)
    assert status == PingValidation.VALID.value
    assert score > 0.5


def test_validate_stale_ping():
    old_ts = datetime.now(timezone.utc) - timedelta(seconds=100)
    status, score = validate_passenger_ping(
        lat=11.72, lon=78.03, accuracy_meters=10.0,
        speed_kmh=20.0, timestamp=old_ts, stops=[])
    assert status == PingValidation.STALE.value
    assert score == 0.0


def test_validate_impossible_speed():
    status, score = validate_passenger_ping(
        lat=11.72, lon=78.03, accuracy_meters=10.0,
        speed_kmh=150.0, timestamp=datetime.now(timezone.utc), stops=[])
    assert status == PingValidation.REJECTED.value
    assert score == 0.0


def test_validate_poor_accuracy():
    status, score = validate_passenger_ping(
        lat=11.72, lon=78.03, accuracy_meters=200.0,
        speed_kmh=20.0, timestamp=datetime.now(timezone.utc), stops=[])
    assert status == PingValidation.REJECTED.value
    assert score == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Privacy model preservation
# ─────────────────────────────────────────────────────────────────────────────

def test_no_gps_columns_on_user_models():
    """User, StudentProfile and StaffProfile must have no GPS/location columns."""
    from app.models.user import User, StudentProfile, StaffProfile
    forbidden = {"latitude", "longitude", "location", "gps", "geo", "position"}
    for model in [User, StudentProfile, StaffProfile]:
        cols = {c.name.lower() for c in model.__table__.columns}
        hit = forbidden & cols
        assert not hit, f"{model.__name__} has forbidden GPS columns: {hit}"


def test_passenger_ping_model_has_no_identity_columns():
    """PassengerLocationPing must not store name/email/phone."""
    forbidden = {"username", "full_name", "email", "phone"}
    cols = {c.name.lower() for c in PassengerLocationPing.__table__.columns}
    hit = forbidden & cols
    assert not hit, f"PassengerLocationPing has identity columns: {hit}"
