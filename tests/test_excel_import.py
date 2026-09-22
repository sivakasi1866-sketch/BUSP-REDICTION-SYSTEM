import io
import openpyxl
from app.services.excel_service import parse_and_validate_excel, commit_excel_records
from app.models.user import User, StudentProfile

def create_in_memory_excel(headers, rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(headers)
    for r in rows:
        ws.append(r)
    stream = io.BytesIO()
    wb.save(stream)
    return stream.getvalue()

def test_excel_valid_student_preview(db_session):
    headers = ["username", "full_name", "email", "phone", "password", "roll_number", "department", "year", "semester"]
    rows = [
        ["newstudent1", "Rahul Kumar", "rahul@college.edu", "9988776655", "secret123", "23CS99", "CSE", 2, 3],
        ["newstudent2", "Sneha Roy", "sneha@college.edu", "9988776656", "secret123", "23CS98", "CSE", 2, 3]
    ]
    excel_bytes = create_in_memory_excel(headers, rows)

    res = parse_and_validate_excel(excel_bytes, "student", db_session)
    assert res["valid"] is True
    assert res["valid_count"] == 2
    assert len(res["errors"]) == 0
    # Ensure password is masked in preview
    assert res["preview_records"][0]["password"] == "••••••••"

def test_excel_privacy_violation_rejection(db_session):
    # Attempt to upload passenger file with GPS coordinates
    headers = ["username", "full_name", "password", "roll_number", "department", "latitude", "longitude"]
    rows = [
        ["badstudent", "Bad Student", "secret123", "23CS90", "CSE", 9.172, 77.872]
    ]
    excel_bytes = create_in_memory_excel(headers, rows)

    res = parse_and_validate_excel(excel_bytes, "student", db_session)
    assert res["valid"] is False
    assert any("Privacy violation" in err for err in res["errors"])

def test_excel_duplicate_detection(db_session):
    headers = ["username", "full_name", "password", "roll_number", "department"]
    rows = [
        ["teststudent", "Conflict User", "secret123", "ROLL-NEW", "CSE"] # teststudent already exists in db_session
    ]
    excel_bytes = create_in_memory_excel(headers, rows)

    res = parse_and_validate_excel(excel_bytes, "student", db_session)
    assert res["valid"] is False
    assert any("already exists in database" in err for err in res["errors"])

def test_excel_commit(db_session):
    records = [
        {
            "username": "importedstudent",
            "full_name": "Imported Student",
            "email": "imp@test.com",
            "phone": "9998887776",
            "password": "plainpass123",
            "roll_number": "ROLL-IMP-01",
            "department": "IT",
            "year": "1"
        }
    ]
    res = commit_excel_records(records, "student", db_session)
    assert res["status"] == "success"
    assert res["imported_count"] == 1

    saved = db_session.query(User).filter(User.username == "importedstudent").first()
    assert saved is not None
    assert saved.student_profile.roll_number == "ROLL-IMP-01"
    assert saved.hashed_password != "plainpass123"
