from app.models.trip import Trip, TripStatus

def test_gps_ping_rejected_before_trip_starts(client, driver_token, db_session):
    trip = db_session.query(Trip).first()
    assert trip.status == TripStatus.NOT_STARTED.value

    # Attempt to send GPS before trip starts
    res = client.post("/api/tracking/ping", json={
        "trip_id": trip.id,
        "latitude": 9.172,
        "longitude": 77.872,
        "speed_kmh": 30.0
    }, headers={"Authorization": f"Bearer {driver_token}"})

    assert res.status_code == 400
    assert "GPS tracking is disabled" in res.json()["detail"]

def test_trip_lifecycle_and_trip_scoped_gps(client, driver_token, db_session):
    trip = db_session.query(Trip).first()

    # 1. Start Trip
    start_res = client.post(f"/api/trips/{trip.id}/start", headers={"Authorization": f"Bearer {driver_token}"})
    assert start_res.status_code == 200
    assert start_res.json()["status"] == TripStatus.ACTIVE.value

    # 2. GPS Tracking is now permitted
    ping_res = client.post("/api/tracking/ping", json={
        "trip_id": trip.id,
        "latitude": 9.175,
        "longitude": 77.868,
        "speed_kmh": 35.0,
        "heading": 120.0
    }, headers={"Authorization": f"Bearer {driver_token}"})

    assert ping_res.status_code == 201
    assert ping_res.json()["speed_kmh"] == 35.0

    # 3. Stop Trip
    stop_res = client.post(f"/api/trips/{trip.id}/stop", headers={"Authorization": f"Bearer {driver_token}"})
    assert stop_res.status_code == 200
    assert stop_res.json()["status"] == TripStatus.COMPLETED.value

    # 4. GPS Tracking must immediately reject any further pings
    post_stop_ping = client.post("/api/tracking/ping", json={
        "trip_id": trip.id,
        "latitude": 9.180,
        "longitude": 77.865,
        "speed_kmh": 0.0
    }, headers={"Authorization": f"Bearer {driver_token}"})

    assert post_stop_ping.status_code == 400
    assert "GPS tracking is disabled" in post_stop_ping.json()["detail"]

def test_student_cannot_submit_gps(client, student_token, db_session):
    trip = db_session.query(Trip).first()
    res = client.post("/api/tracking/ping", json={
        "trip_id": trip.id,
        "latitude": 9.175,
        "longitude": 77.868
    }, headers={"Authorization": f"Bearer {student_token}"})
    assert res.status_code == 403
