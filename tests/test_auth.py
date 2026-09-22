import pytest
from app.core.security import verify_password, get_password_hash
from app.models.user import User

def test_password_hashing():
    raw = "SuperSecretPassword123!"
    hashed = get_password_hash(raw)
    assert raw not in hashed
    assert "$" in hashed
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_login_success(client):
    res = client.post("/api/auth/login", json={"username": "testadmin", "password": "adminpass123"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["role"] == "ADMIN"
    assert "password" not in data

def test_login_invalid_password(client):
    res = client.post("/api/auth/login", json={"username": "testadmin", "password": "WrongPassword"})
    assert res.status_code == 401
    assert "Incorrect" in res.json()["detail"]

def test_passwords_never_returned_in_api(client, admin_token):
    res = client.get("/api/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    users = res.json()
    for u in users:
        assert "password" not in u
        assert "hashed_password" not in u

def test_rbac_student_blocked_from_admin_endpoint(client, student_token):
    # Student attempts to list all users (admin only)
    res = client.get("/api/users", headers={"Authorization": f"Bearer {student_token}"})
    assert res.status_code == 403
    assert "Access denied" in res.json()["detail"]

def test_rbac_driver_blocked_from_user_creation(client, driver_token):
    res = client.post("/api/users", json={
        "username": "intruder",
        "full_name": "Intruder User",
        "password": "pass",
        "role": "STUDENT"
    }, headers={"Authorization": f"Bearer {driver_token}"})
    assert res.status_code == 403
