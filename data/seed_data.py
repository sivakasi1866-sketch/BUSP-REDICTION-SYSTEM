import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal, Base, engine
from app.models.user import User, StudentProfile, StaffProfile, DriverProfile, UserRole
from app.models.bus import Bus
from app.models.route import Route, Stop
from app.models.assignment import DefaultAssignment
from app.models.trip import Trip, TripStatus
from app.core.security import get_password_hash
from app.ml.train import train_and_evaluate_model

# ============================================================
# R.P. SARATHY INSTITUTE OF TECHNOLOGY (RPSIT)
# Poosaripatty, Kadayampatti Taluk, Salem District, Tamil Nadu
# College GPS: 11.7210 N, 78.0350 E
#
# REAL BUS ROUTES (official RPSIT transport network):
#   Route 1: Dharmapuri -> Harur -> Thoppur -> Omalur -> RPSIT
#   Route 2: Mettur Dam -> Mecheri -> Omalur -> RPSIT
#   Route 3: Attur -> Mallur -> Omalur -> RPSIT
#   Route 4: Neikarapatty -> Sankari -> Omalur -> RPSIT
#   Route 5: Kannankurichi -> Salem Town -> Omalur -> RPSIT
# ============================================================

RPSIT_LAT = 11.7210
RPSIT_LON = 78.0350

ROUTES_DATA = [
    {
        "route_name": "Route 1 - Dharmapuri via Harur to RPSIT Campus",
        "route_code": "R-01-DPR",
        "description": "Dharmapuri town via Harur -> Thoppur -> Omalur -> RPSIT Poosaripatty (~80 km)",
        "stops": [
            {"name": "Dharmapuri New Bus Stand",        "lat": 12.1272, "lon": 78.1572, "offset": 0},
            {"name": "Mathurappadi Highway Junction",    "lat": 12.0841, "lon": 78.1623, "offset": 8},
            {"name": "Harur Bus Stand",                 "lat": 12.0537, "lon": 78.4775, "offset": 25},
            {"name": "Thoppur Junction",                "lat": 11.9342, "lon": 78.3128, "offset": 42},
            {"name": "Omalur New Bus Stand",            "lat": 11.7421, "lon": 78.0452, "offset": 65},
            {"name": "Poosaripatty Junction",           "lat": 11.7310, "lon": 78.0375, "offset": 72},
            {"name": "RPSIT College Main Gate",         "lat": RPSIT_LAT, "lon": RPSIT_LON, "offset": 80},
        ]
    },
    {
        "route_name": "Route 2 - Mettur Dam via Mecheri to RPSIT Campus",
        "route_code": "R-02-MTR",
        "description": "Mettur Dam -> Mecheri -> Omalur -> RPSIT Poosaripatty (~50 km)",
        "stops": [
            {"name": "Mettur Dam Bus Stand",            "lat": 11.7996, "lon": 77.7996, "offset": 0},
            {"name": "Mettur Town Samundisaravali",     "lat": 11.7889, "lon": 77.8201, "offset": 8},
            {"name": "Mecheri Bus Stop",                "lat": 11.7658, "lon": 77.9124, "offset": 18},
            {"name": "Karungalpatti Signal",            "lat": 11.7529, "lon": 77.9748, "offset": 27},
            {"name": "Omalur New Bus Stand",            "lat": 11.7421, "lon": 78.0452, "offset": 38},
            {"name": "Poosaripatty Junction",           "lat": 11.7310, "lon": 78.0375, "offset": 44},
            {"name": "RPSIT College Main Gate",         "lat": RPSIT_LAT, "lon": RPSIT_LON, "offset": 50},
        ]
    },
    {
        "route_name": "Route 3 - Attur via Mallur to RPSIT Campus",
        "route_code": "R-03-ATR",
        "description": "Attur -> Mallur -> Nangavalli -> Omalur -> RPSIT Poosaripatty (~56 km)",
        "stops": [
            {"name": "Attur New Bus Stand",             "lat": 11.5983, "lon": 78.5997, "offset": 0},
            {"name": "Attur Collectorate Junction",     "lat": 11.5931, "lon": 78.5924, "offset": 5},
            {"name": "Ayothiyapattinam Highway Stop",   "lat": 11.6103, "lon": 78.5312, "offset": 15},
            {"name": "Mallur Bus Stand",                "lat": 11.6248, "lon": 78.4523, "offset": 24},
            {"name": "Nangavalli Junction",             "lat": 11.6581, "lon": 78.3421, "offset": 33},
            {"name": "Omalur New Bus Stand",            "lat": 11.7421, "lon": 78.0452, "offset": 44},
            {"name": "Poosaripatty Junction",           "lat": 11.7310, "lon": 78.0375, "offset": 50},
            {"name": "RPSIT College Main Gate",         "lat": RPSIT_LAT, "lon": RPSIT_LON, "offset": 56},
        ]
    },
    {
        "route_name": "Route 4 - Neikarapatty via Sankari to RPSIT Campus",
        "route_code": "R-04-NKP",
        "description": "Neikarapatty -> Sankari -> Omalur -> RPSIT Poosaripatty (~43 km)",
        "stops": [
            {"name": "Neikarapatty Bus Stand",          "lat": 11.6512, "lon": 77.9124, "offset": 0},
            {"name": "Neikarapatty Town Arch Stop",     "lat": 11.6548, "lon": 77.9180, "offset": 4},
            {"name": "Sankari New Bus Stand",           "lat": 11.7312, "lon": 77.9124, "offset": 15},
            {"name": "Sankari Police Station Stop",     "lat": 11.7378, "lon": 77.9298, "offset": 20},
            {"name": "Kattur Bypass Signal",            "lat": 11.7398, "lon": 77.9812, "offset": 28},
            {"name": "Omalur New Bus Stand",            "lat": 11.7421, "lon": 78.0452, "offset": 33},
            {"name": "Poosaripatty Junction",           "lat": 11.7310, "lon": 78.0375, "offset": 38},
            {"name": "RPSIT College Main Gate",         "lat": RPSIT_LAT, "lon": RPSIT_LON, "offset": 43},
        ]
    },
    {
        "route_name": "Route 5 - Kannankurichi via Salem Town to RPSIT Campus",
        "route_code": "R-05-KNK",
        "description": "Kannankurichi -> Salem New Bus Stand -> Ammapet -> Omalur -> RPSIT (~45 km)",
        "stops": [
            {"name": "Kannankurichi Bus Stop",          "lat": 11.6287, "lon": 78.1421, "offset": 0},
            {"name": "Salem New Bus Stand Main",        "lat": 11.6643, "lon": 78.1460, "offset": 10},
            {"name": "Salem Junction Railway Gate",     "lat": 11.6656, "lon": 78.1485, "offset": 13},
            {"name": "Ammapet Flyover Junction",        "lat": 11.6821, "lon": 78.1125, "offset": 20},
            {"name": "Kondalampatti Crossroads",        "lat": 11.7012, "lon": 78.0921, "offset": 28},
            {"name": "Omalur New Bus Stand",            "lat": 11.7421, "lon": 78.0452, "offset": 36},
            {"name": "Poosaripatty Junction",           "lat": 11.7310, "lon": 78.0375, "offset": 40},
            {"name": "RPSIT College Main Gate",         "lat": RPSIT_LAT, "lon": RPSIT_LON, "offset": 45},
        ]
    },
]


def seed_database():
    print("=" * 60)
    print("R.P. SARATHY INSTITUTE OF TECHNOLOGY")
    print("Partners Bus Prediction - Database Initialisation")
    print("=" * 60)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        if db.query(User).filter(User.username == "admin").first():
            print("Database already seeded. Skipping.")
            return

        # ---- USERS -------------------------------------------------------
        print("\n[1/5] Creating Users...")

        admin = User(username="admin", email="transport@rpsit.ac.in",
                     full_name="RPSIT Fleet Admin",
                     hashed_password=get_password_hash("admin123"),
                     role=UserRole.ADMIN.value, phone="9344972275")
        db.add(admin)

        # Drivers - one per route
        drivers_data = [
            ("driver1", "Murugan R",   "9876543211", "TN-38-DL-2015-001", 9),
            ("driver2", "Kuppusamy V", "9876543212", "TN-38-DL-2017-002", 7),
            ("driver3", "Selvaraj M",  "9876543213", "TN-38-DL-2019-003", 5),
            ("driver4", "Arumugam P",  "9876543214", "TN-38-DL-2018-004", 6),
            ("driver5", "Babu S",      "9876543215", "TN-38-DL-2020-005", 4),
        ]
        driver_users = []
        for uname, fname, phone, lic, exp in drivers_data:
            d = User(username=uname, email=f"{uname}@rpsit.ac.in",
                     full_name=fname,
                     hashed_password=get_password_hash("driver123"),
                     role=UserRole.DRIVER.value, phone=phone)
            db.add(d)
            db.flush()
            db.add(DriverProfile(user_id=d.id, license_number=lic, experience_years=exp))
            driver_users.append(d)
            print(f"   Driver created: {fname}")

        # Students
        students_data = [
            ("student1", "Ananya Krishnamurthy", "9751234561", "22CS001", "Computer Science", 3, 5),
            ("student2", "Karthik Selvam",        "9751234562", "22EC014", "ECE", 3, 5),
            ("student3", "Priya Ramasamy",        "9751234563", "23ME021", "Mechanical", 2, 3),
            ("student4", "Arun Kumar S",          "9751234564", "23CS042", "Computer Science", 2, 3),
            ("student5", "Deepika Balaji",        "9751234565", "22EE009", "EEE", 3, 5),
        ]
        student_users = []
        for uname, fname, phone, roll, dept, yr, sem in students_data:
            s = User(username=uname, email=f"{uname}@rpsit.ac.in",
                     full_name=fname,
                     hashed_password=get_password_hash("student123"),
                     role=UserRole.STUDENT.value, phone=phone)
            db.add(s)
            db.flush()
            db.add(StudentProfile(user_id=s.id, roll_number=roll,
                                  department=dept, year=yr, semester=sem))
            student_users.append(s)
            print(f"   Student created: {fname} ({roll})")

        # Staff
        staff_data = [
            ("staff1", "Dr. P. Saravanan",   "9751234571", "FAC-001", "Computer Science", "Associate Professor"),
            ("staff2", "Mrs. R. Kavitha",    "9751234572", "FAC-002", "ECE",              "Assistant Professor"),
            ("staff3", "Mr. V. Ramamoorthi", "9751234573", "FAC-003", "Mechanical",       "Assistant Professor"),
        ]
        staff_users = []
        for uname, fname, phone, eid, dept, desig in staff_data:
            st = User(username=uname, email=f"{uname}@rpsit.ac.in",
                      full_name=fname,
                      hashed_password=get_password_hash("staff123"),
                      role=UserRole.STAFF.value, phone=phone)
            db.add(st)
            db.flush()
            db.add(StaffProfile(user_id=st.id, employee_id=eid,
                                department=dept, designation=desig))
            staff_users.append(st)
            print(f"   Staff created: {fname} ({eid})")

        # ---- ROUTES & STOPS -----------------------------------------------
        print("\n[2/5] Seeding RPSIT Real Routes & Infrastructure Stops...")
        route_objects = []
        stop_objects_by_route = []

        for r_data in ROUTES_DATA:
            route = Route(
                route_name=r_data["route_name"],
                route_code=r_data["route_code"],
                description=r_data["description"],
                is_active=True
            )
            db.add(route)
            db.flush()

            stops = []
            for idx, s in enumerate(r_data["stops"]):
                stop = Stop(
                    route_id=route.id,
                    stop_name=s["name"],
                    sequence=idx + 1,
                    latitude=s["lat"],
                    longitude=s["lon"],
                    scheduled_offset_minutes=s["offset"],
                    is_active=True
                )
                db.add(stop)
                stops.append(stop)

            db.flush()
            route_objects.append(route)
            stop_objects_by_route.append(stops)
            print(f"   [OK] {r_data['route_code']}: {len(stops)} stops seeded")

        # ---- BUSES --------------------------------------------------------
        print("\n[3/5] Registering College Fleet Buses...")
        bus_data = [
            ("RPSIT-01", "TN-38-CB-1001", 55),
            ("RPSIT-02", "TN-38-CB-1002", 52),
            ("RPSIT-03", "TN-38-CB-1003", 48),
            ("RPSIT-04", "TN-38-CB-1004", 52),
            ("RPSIT-05", "TN-38-CB-1005", 50),
        ]
        bus_objects = []
        for i, (bnum, reg, cap) in enumerate(bus_data):
            bus = Bus(
                bus_number=bnum,
                registration_number=reg,
                capacity=cap,
                is_active=True,
                status="IDLE",
                current_driver_id=driver_users[i].id,
                default_route_id=route_objects[i].id
            )
            db.add(bus)
            bus_objects.append(bus)
        db.flush()
        print(f"   [OK] {len(bus_objects)} buses registered.")

        # ---- ASSIGNMENTS --------------------------------------------------
        print("\n[4/5] Assigning Students & Staff to Routes/Stops...")

        # (student_idx, bus_idx, stop_idx_within_route)
        student_assignments = [
            (0, 0, 1),   # Ananya     -> Route1, Mathurappadi
            (1, 1, 2),   # Karthik    -> Route2, Mecheri
            (2, 2, 3),   # Priya      -> Route3, Mallur
            (3, 3, 2),   # Arun Kumar -> Route4, Sankari New Bus Stand
            (4, 4, 1),   # Deepika    -> Route5, Salem New Bus Stand
        ]
        for s_idx, b_idx, stop_idx in student_assignments:
            db.add(DefaultAssignment(
                user_id=student_users[s_idx].id,
                bus_id=bus_objects[b_idx].id,
                stop_id=stop_objects_by_route[b_idx][stop_idx].id,
                academic_year="2025-2026"
            ))
            print(f"   Student {student_users[s_idx].full_name} -> {bus_objects[b_idx].bus_number} | Stop: {stop_objects_by_route[b_idx][stop_idx].stop_name}")

        staff_assignments = [
            (0, 4, 1),   # Dr. Saravanan  -> Route5, Salem New Bus Stand
            (1, 1, 2),   # Mrs. Kavitha   -> Route2, Mecheri
            (2, 3, 2),   # Mr. Ramamoorthi-> Route4, Sankari
        ]
        for st_idx, b_idx, stop_idx in staff_assignments:
            db.add(DefaultAssignment(
                user_id=staff_users[st_idx].id,
                bus_id=bus_objects[b_idx].id,
                stop_id=stop_objects_by_route[b_idx][stop_idx].id,
                academic_year="2025-2026"
            ))
            print(f"   Staff {staff_users[st_idx].full_name} -> {bus_objects[b_idx].bus_number} | Stop: {stop_objects_by_route[b_idx][stop_idx].stop_name}")

        # ---- INITIAL TRIPS ------------------------------------------------
        print("\n[5/5] Creating Today's Morning Pickup Trips (NOT_STARTED)...")
        trip_names = [
            "Morning Pickup - Dharmapuri Route (RPSIT-01)",
            "Morning Pickup - Mettur Route (RPSIT-02)",
            "Morning Pickup - Attur Route (RPSIT-03)",
            "Morning Pickup - Neikarapatty Route (RPSIT-04)",
            "Morning Pickup - Salem City Route (RPSIT-05)",
        ]
        for i, tname in enumerate(trip_names):
            first_stop = stop_objects_by_route[i][0]
            trip = Trip(
                bus_id=bus_objects[i].id,
                driver_id=driver_users[i].id,
                route_id=route_objects[i].id,
                trip_name=tname,
                trip_type="MORNING_PICKUP",
                status=TripStatus.NOT_STARTED.value,
                current_stop_sequence=1,
                current_latitude=first_stop.latitude,
                current_longitude=first_stop.longitude,
                current_speed_kmh=0.0
            )
            db.add(trip)
            print(f"   Trip created: {tname}")

        db.commit()
        print("\nDatabase seeding completed successfully!")
        print("\nDemo Login Credentials:")
        print("  Admin   : admin / admin123")
        print("  Drivers : driver1 to driver5 / driver123")
        print("  Students: student1 to student5 / student123")
        print("  Staff   : staff1 to staff3 / staff123")

    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Seeding failed: {e}")
        raise
    finally:
        db.close()

    print("\nTraining ML ETA model on RPSIT route data...")
    metrics = train_and_evaluate_model(save_model=True)
    print(f"ML Model: MAE={metrics['mae']} min | RMSE={metrics['rmse']} min | R2={metrics['r2']}")
    print("Done.")


if __name__ == "__main__":
    db_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "partners_bus.db")
    if os.path.exists(db_file):
        os.remove(db_file)
        print(f"Removed old database: {db_file}")
    seed_database()
