import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.core.security import get_password_hash, create_access_token
from app.models.user import User, UserRole, StudentProfile, DriverProfile
from app.models.bus import Bus
from app.models.route import Route, Stop
from app.models.assignment import DefaultAssignment
from app.models.trip import Trip, TripStatus

# In-memory SQLite for isolated test runs
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    
    # Create baseline test fixtures
    admin = User(
        username="testadmin",
        email="admin@test.com",
        full_name="Test Administrator",
        hashed_password=get_password_hash("adminpass123"),
        role=UserRole.ADMIN.value
    )
    driver = User(
        username="testdriver",
        email="driver@test.com",
        full_name="Test Driver",
        hashed_password=get_password_hash("driverpass123"),
        role=UserRole.DRIVER.value
    )
    student = User(
        username="teststudent",
        email="student@test.com",
        full_name="Test Student",
        hashed_password=get_password_hash("studentpass123"),
        role=UserRole.STUDENT.value
    )
    session.add_all([admin, driver, student])
    session.flush()

    session.add(DriverProfile(user_id=driver.id, license_number="DL-TEST-99"))
    session.add(StudentProfile(user_id=student.id, roll_number="TEST-2026-01", department="CS", year=2))

    route = Route(route_name="Campus Line", route_code="R-TEST", is_active=True)
    session.add(route)
    session.flush()

    stop1 = Stop(route_id=route.id, stop_name="Origin Stop", sequence=1, latitude=9.170, longitude=77.870, scheduled_offset_minutes=0)
    stop2 = Stop(route_id=route.id, stop_name="Student Stop", sequence=2, latitude=9.180, longitude=77.860, scheduled_offset_minutes=15)
    stop3 = Stop(route_id=route.id, stop_name="College Gate", sequence=3, latitude=9.200, longitude=77.840, scheduled_offset_minutes=35)
    session.add_all([stop1, stop2, stop3])
    session.flush()

    bus = Bus(
        bus_number="TEST-BUS-01",
        registration_number="TN-99-TEST",
        capacity=50,
        is_active=True,
        status="IDLE",
        current_driver_id=driver.id,
        default_route_id=route.id
    )
    session.add(bus)
    session.flush()

    # Assign student to stop2 on this bus
    session.add(DefaultAssignment(user_id=student.id, bus_id=bus.id, stop_id=stop2.id))

    trip = Trip(
        bus_id=bus.id,
        driver_id=driver.id,
        route_id=route.id,
        trip_name="Test Morning Trip",
        status=TripStatus.NOT_STARTED.value,
        current_stop_sequence=1,
        current_latitude=stop1.latitude,
        current_longitude=stop1.longitude
    )
    session.add(trip)
    session.commit()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def admin_token(db_session):
    user = db_session.query(User).filter(User.username == "testadmin").first()
    return create_access_token({"user_id": user.id, "username": user.username, "role": user.role})

@pytest.fixture
def driver_token(db_session):
    user = db_session.query(User).filter(User.username == "testdriver").first()
    return create_access_token({"user_id": user.id, "username": user.username, "role": user.role})

@pytest.fixture
def student_token(db_session):
    user = db_session.query(User).filter(User.username == "teststudent").first()
    return create_access_token({"user_id": user.id, "username": user.username, "role": user.role})
