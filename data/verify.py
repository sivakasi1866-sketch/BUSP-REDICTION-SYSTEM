from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Admin login
token = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"}).json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Verify RPSIT routes
routes = client.get("/api/routes", headers=headers).json()
print("=== RPSIT ROUTES LOADED ===")
for r in routes:
    print(f"  {r['route_code']}: {r['route_name']} ({len(r['stops'])} stops)")

# Verify buses
buses = client.get("/api/buses", headers=headers).json()
print(f"\nTotal Buses: {len(buses)}")
for b in buses:
    print(f"  {b['bus_number']} ({b['registration_number']}) - Capacity: {b['capacity']} - Status: {b['status']}")

# Dashboard summary
summary = client.get("/api/reports/dashboard-summary", headers=headers).json()
print(f"\nDashboard Summary:")
print(f"  Total Buses : {summary['fleet']['total_buses']}")
print(f"  Active Trips: {summary['trips']['active']}")
print(f"  Students    : {summary['users']['students']}")
print(f"  Staff       : {summary['users']['staff']}")
print(f"  Routes      : {summary['infrastructure']['routes']}")
print(f"  Total Stops : {summary['infrastructure']['stops']}")
print(f"  Recent Trips:")
for t in summary["recent_trips"]:
    print(f"    - {t['trip_name']} | Bus: {t['bus_number']} | Status: {t['status']}")

# Driver1 trip
dtoken = client.post("/api/auth/login", json={"username": "driver1", "password": "driver123"}).json()["access_token"]
dheaders = {"Authorization": f"Bearer {dtoken}"}
dtrip = client.get("/api/trips/driver/active", headers=dheaders).json()
print(f"\nDriver1 Trip: {dtrip['trip_name']} | Status: {dtrip['status']}")

# Student1 assignment
stoken = client.post("/api/auth/login", json={"username": "student1", "password": "student123"}).json()["access_token"]
sheaders = {"Authorization": f"Bearer {stoken}"}
assign = client.get("/api/assignments/my-assignment", headers=sheaders).json()
print(f"\nStudent1 Assignment:")
print(f"  Bus  : {assign['bus']['bus_number']} ({assign['bus']['registration_number']})")
print(f"  Stop : {assign['stop']['stop_name']}")
print(f"  Route: {assign['route']['route_name']}")

print("\nAll verifications passed!")
