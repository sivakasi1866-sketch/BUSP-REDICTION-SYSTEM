from app.models.user import User, StudentProfile, StaffProfile
from app.schemas.user import UserResponse, StudentProfileResponse, StaffProfileResponse
from app.models.trip import GPSPing

def test_database_models_contain_no_passenger_location_columns():
    """Verify strictly that User, StudentProfile, and StaffProfile models have no GPS/location columns."""
    forbidden_terms = ["lat", "lon", "gps", "location", "coord"]

    user_cols = [c.name.lower() for c in User.__table__.columns]
    for term in forbidden_terms:
        assert not any(term in col for col in user_cols), f"User model contains forbidden location column matching '{term}'"

    student_cols = [c.name.lower() for c in StudentProfile.__table__.columns]
    for term in forbidden_terms:
        assert not any(term in col for col in student_cols), f"StudentProfile model contains forbidden location column matching '{term}'"

    staff_cols = [c.name.lower() for c in StaffProfile.__table__.columns]
    for term in forbidden_terms:
        assert not any(term in col for col in staff_cols), f"StaffProfile model contains forbidden location column matching '{term}'"

def test_pydantic_schemas_contain_no_passenger_location_fields():
    """Verify that serialization schemas never expose or accept student/staff location fields."""
    forbidden_terms = ["lat", "lon", "gps", "location", "coord"]

    user_fields = [f.lower() for f in UserResponse.model_fields.keys()]
    for term in forbidden_terms:
        assert not any(term in field for field in user_fields)

    student_fields = [f.lower() for f in StudentProfileResponse.model_fields.keys()]
    for term in forbidden_terms:
        assert not any(term in field for field in student_fields)

    staff_fields = [f.lower() for f in StaffProfileResponse.model_fields.keys()]
    for term in forbidden_terms:
        assert not any(term in field for field in staff_fields)

def test_gps_ping_model_strictly_linked_to_trips_not_passengers():
    """Verify GPSPing is only linked to trip_id, with no user_id or passenger reference."""
    gps_cols = [c.name.lower() for c in GPSPing.__table__.columns]
    assert "trip_id" in gps_cols
    assert "user_id" not in gps_cols
    assert "student_id" not in gps_cols

def test_student_cannot_view_other_users_private_data(client, student_token):
    """Verify student cannot access the admin user list or internal system data."""
    res = client.get("/api/users", headers={"Authorization": f"Bearer {student_token}"})
    assert res.status_code == 403
