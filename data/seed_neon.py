"""
Neon PostgreSQL Seed Script for Partners Bus Prediction
Run this ONCE after connecting Neon to Vercel to populate the database.

Usage:
  set DATABASE_URL=postgresql://user:pass@ep-xxx.neon.tech/neondb?sslmode=require
  python data/seed_neon.py
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Must set DATABASE_URL before importing app modules
db_url = os.environ.get("DATABASE_URL", "")
if not db_url or "postgresql" not in db_url:
    print("ERROR: Set DATABASE_URL to your Neon PostgreSQL connection string first.")
    print("  Example:")
    print("  set DATABASE_URL=postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require")
    sys.exit(1)

print("Connecting to Neon PostgreSQL...")

from app.database import engine, Base, SessionLocal
from app.models import *  # noqa - registers all models
from app.core.security import get_password_hash
from app.models.user import User, UserRole, StudentProfile, StaffProfile
from app.models.bus import Bus
from app.models.route import Route, Stop
from app.models.assignment import DefaultAssignment
from app.models.trip import Trip, TripStatus
from datetime import datetime, timezone

# ── Create all tables ────────────────────────────────────────────────────────
print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Tables created.")

db = SessionLocal()

try:
    # ── Check if already seeded ───────────────────────────────────────────────
    if db.query(User).filter_by(username="admin").first():
        print("Database already seeded. Skipping.")
        sys.exit(0)

    print("Seeding data...")

    # ── Admin ─────────────────────────────────────────────────────────────────
    admin = User(
        username="admin", email="admin@rpsit.ac.in",
        full_name="System Administrator",
        hashed_password=get_password_hash("admin123"),
        role=UserRole.ADMIN.value, is_active=True
    )
    db.add(admin)

    # ── Drivers ───────────────────────────────────────────────────────────────
    drivers = []
    driver_data = [
        ("driver1", "Murugan K",     "driver1@rpsit.ac.in",  "driver123"),
        ("driver2", "Selvam R",      "driver2@rpsit.ac.in",  "driver123"),
        ("driver3", "Kannan P",      "driver3@rpsit.ac.in",  "driver123"),
        ("driver4", "Rajan S",       "driver4@rpsit.ac.in",  "driver123"),
        ("driver5", "Thangavel M",   "driver5@rpsit.ac.in",  "driver123"),
    ]
    for uname, fname, email, pwd in driver_data:
        d = User(username=uname, email=email, full_name=fname,
                 hashed_password=get_password_hash(pwd),
                 role=UserRole.DRIVER.value, is_active=True)
        db.add(d); drivers.append(d)

    # ── Students ──────────────────────────────────────────────────────────────
    students = []
    student_data = [
        ("student1", "Arun Kumar",      "s1@rpsit.ac.in",  "CS001", "CSE", 3, 5),
        ("student2", "Priya Lakshmi",   "s2@rpsit.ac.in",  "CS002", "CSE", 2, 3),
        ("student3", "Vikram S",        "s3@rpsit.ac.in",  "EC001", "ECE", 3, 5),
        ("student4", "Deepa R",         "s4@rpsit.ac.in",  "ME001", "MECH",2, 3),
        ("student5", "Suresh P",        "s5@rpsit.ac.in",  "CE001", "CIVIL",1,2),
    ]
    for uname, fname, email, roll, dept, yr, sem in student_data:
        s = User(username=uname, email=email, full_name=fname,
                 hashed_password=get_password_hash("student123"),
                 role=UserRole.STUDENT.value, is_active=True)
        db.add(s); students.append(s)

    # ── Staff ─────────────────────────────────────────────────────────────────
    staff_list = []
    staff_data = [
        ("staff1", "Dr. Rajendran M",   "staff1@rpsit.ac.in", "Mathematics",    "HOD"),
        ("staff2", "Dr. Vijayalakshmi", "staff2@rpsit.ac.in", "Computer Science","Professor"),
        ("staff3", "Mr. Senthil Kumar", "staff3@rpsit.ac.in", "Electronics",     "Asst. Professor"),
    ]
    for uname, fname, email, dept, desg in staff_data:
        st = User(username=uname, email=email, full_name=fname,
                  hashed_password=get_password_hash("staff123"),
                  role=UserRole.STAFF.value, is_active=True)
        db.add(st); staff_list.append(st)

    db.flush()

    # ── Student Profiles ──────────────────────────────────────────────────────
    for i, (s, row) in enumerate(zip(students, student_data)):
        _, _, _, roll, dept, yr, sem = row
        db.add(StudentProfile(user_id=s.id, roll_number=roll,
                              department=dept, year=yr, semester=sem))

    # ── Staff Profiles ────────────────────────────────────────────────────────
    for st, row in zip(staff_list, staff_data):
        _, _, _, dept, desg = row
        db.add(StaffProfile(user_id=st.id, department=dept, designation=desg))

    db.flush()

    # ── Routes ────────────────────────────────────────────────────────────────
    # Real RPSIT Salem routes
    routes_data = [
        ("Dharmapuri - RPSIT",  "R-01-DPR", [
            ("Dharmapuri Bus Stand",   12.1211, 78.1582, 0),
            ("Harur",                  12.0474, 78.4820, 20),
            ("Palacode",               12.2036, 78.3586, 30),
            ("Thoppur",                11.9731, 78.4264, 50),
            ("Omalur",                 11.7373, 77.9987, 70),
            ("Kannankurichi",          11.7650, 78.0100, 80),
            ("RPSIT Campus",           11.7210, 78.0350, 90),
        ]),
        ("Mettur Dam - RPSIT",  "R-02-MTR", [
            ("Mettur Dam",             11.7963, 77.8001, 0),
            ("Mecheri",                11.7500, 77.8700, 15),
            ("Taramangalam",           11.7130, 77.9700, 30),
            ("Omalur",                 11.7373, 77.9987, 45),
            ("Kannankurichi",          11.7650, 78.0100, 55),
            ("Ammapet",                11.6870, 78.1100, 65),
            ("RPSIT Campus",           11.7210, 78.0350, 75),
        ]),
        ("Attur - RPSIT",       "R-03-ATR", [
            ("Attur Bus Stand",        11.5993, 78.6017, 0),
            ("Mallur",                 11.6700, 78.4500, 20),
            ("Nangavalli",             11.7000, 78.2500, 35),
            ("Edappadi",               11.7761, 77.9958, 50),
            ("Omalur",                 11.7373, 77.9987, 60),
            ("Kannankurichi",          11.7650, 78.0100, 70),
            ("RPSIT Campus",           11.7210, 78.0350, 80),
        ]),
        ("Neikarapatty - RPSIT","R-04-NKP", [
            ("Neikarapatty",           11.8478, 78.1526, 0),
            ("Sankari",                11.8467, 77.9150, 15),
            ("Konganapuram",           11.7900, 77.9500, 30),
            ("Omalur",                 11.7373, 77.9987, 45),
            ("Kannankurichi",          11.7650, 78.0100, 55),
            ("Ammapet",                11.6870, 78.1100, 62),
            ("RPSIT Campus",           11.7210, 78.0350, 70),
        ]),
        ("Kannankurichi - RPSIT","R-05-KNK", [
            ("Kannankurichi",          11.7650, 78.0100, 0),
            ("Salem Bus Stand",        11.6643, 78.1460, 15),
            ("Ammapet",                11.6870, 78.1100, 22),
            ("Alagapuram",             11.6991, 78.0980, 30),
            ("Omalur",                 11.7373, 77.9987, 40),
            ("Kadayampatti",           11.7100, 78.0200, 50),
            ("RPSIT Campus",           11.7210, 78.0350, 55),
        ]),
    ]

    routes = []
    all_first_stops = []

    for rname, rcode, stops_data in routes_data:
        route = Route(route_name=rname, route_code=rcode, is_active=True)
        db.add(route); db.flush()
        routes.append(route)

        first_stop = None
        for seq, (sname, lat, lon, offset) in enumerate(stops_data, 1):
            stop = Stop(
                route_id=route.id, stop_name=sname,
                sequence=seq, latitude=lat, longitude=lon,
                scheduled_offset_minutes=offset, is_active=True
            )
            db.add(stop)
            if seq == 1:
                first_stop = stop
        db.flush()
        all_first_stops.append(first_stop)

    # ── Buses ─────────────────────────────────────────────────────────────────
    buses = []
    bus_data = [
        ("RPSIT-01", "TN-38-N-1001", 52, routes[0].id),
        ("RPSIT-02", "TN-38-N-1002", 52, routes[1].id),
        ("RPSIT-03", "TN-38-N-1003", 48, routes[2].id),
        ("RPSIT-04", "TN-38-N-1004", 48, routes[3].id),
        ("RPSIT-05", "TN-38-N-1005", 44, routes[4].id),
    ]
    for bnum, reg, cap, rid in bus_data:
        b = Bus(bus_number=bnum, registration_number=reg,
                capacity=cap, is_active=True, status="IDLE", default_route_id=rid)
        db.add(b); buses.append(b)
    db.flush()

    # ── Default Assignments ───────────────────────────────────────────────────
    # Assign students to buses
    student_assignments = [
        (students[0], buses[0], all_first_stops[0]),
        (students[1], buses[1], all_first_stops[1]),
        (students[2], buses[2], all_first_stops[2]),
        (students[3], buses[3], all_first_stops[3]),
        (students[4], buses[4], all_first_stops[4]),
    ]
    for user, bus, stop in student_assignments:
        db.add(DefaultAssignment(user_id=user.id, bus_id=bus.id,
                                 stop_id=stop.id, academic_year="2025-2026"))

    # Assign staff to buses
    staff_assignments = [
        (staff_list[0], buses[0], all_first_stops[0]),
        (staff_list[1], buses[1], all_first_stops[1]),
        (staff_list[2], buses[2], all_first_stops[2]),
    ]
    for user, bus, stop in staff_assignments:
        db.add(DefaultAssignment(user_id=user.id, bus_id=bus.id,
                                 stop_id=stop.id, academic_year="2025-2026"))

    # ── Trips (Morning Pickup — NOT_STARTED) ──────────────────────────────────
    for i, (bus, driver, route) in enumerate(zip(buses, drivers, routes)):
        trip = Trip(
            bus_id=bus.id, driver_id=driver.id, route_id=route.id,
            trip_name=f"{route.route_name} Morning Pickup",
            trip_type="MORNING_PICKUP",
            status=TripStatus.NOT_STARTED.value,
            start_time=datetime.now(timezone.utc),
        )
        db.add(trip)

    db.commit()
    print("Done! Database seeded successfully.")
    print("Users created:")
    print("  Admin:    admin / admin123")
    print("  Drivers:  driver1-driver5 / driver123")
    print("  Students: student1-student5 / student123")
    print("  Staff:    staff1-staff3 / staff123")

except Exception as e:
    db.rollback()
    print(f"ERROR: {e}")
    raise
finally:
    db.close()
