import io
import openpyxl
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.user import User, StudentProfile, StaffProfile, DriverProfile, UserRole
from app.core.security import get_password_hash

# Forbidden fields that violate privacy (never accepted)
FORBIDDEN_FIELDS = {"latitude", "longitude", "gps", "location", "live_location", "coords", "current_lat", "current_lon"}

EXPECTED_HEADERS = {
    "student": ["username", "full_name", "email", "phone", "password", "roll_number", "department", "year", "semester"],
    "staff": ["username", "full_name", "email", "phone", "password", "employee_id", "department", "designation"],
    "driver": ["username", "full_name", "email", "phone", "password", "license_number", "experience_years"]
}

REQUIRED_FIELDS = {
    "student": ["username", "full_name", "password", "roll_number", "department"],
    "staff": ["username", "full_name", "password", "employee_id", "department"],
    "driver": ["username", "full_name", "password", "license_number"]
}

def parse_and_validate_excel(file_bytes: bytes, import_type: str, db: Session) -> Dict[str, Any]:
    """
    Parses an uploaded Excel file for preview.
    Validates headers, detects duplicates, checks for existing DB conflicts,
    and strictly forbids passenger GPS/location columns.
    """
    if import_type not in EXPECTED_HEADERS:
        return {"valid": False, "errors": [f"Invalid import type: '{import_type}'. Must be 'student', 'staff', or 'driver'."]}

    # Check file size (max 5 MB)
    if len(file_bytes) > 5 * 1024 * 1024:
        return {"valid": False, "errors": ["File size exceeds 5MB limit."]}

    try:
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
    except Exception as e:
        return {"valid": False, "errors": [f"Invalid Excel file format: {str(e)}"]}

    sheet = wb.active
    rows = list(sheet.iter_rows(values_only=True))
    if not rows:
        return {"valid": False, "errors": ["Uploaded Excel file is empty."]}

    # Validate header
    raw_headers = [str(cell).strip().lower() if cell is not None else "" for cell in rows[0]]
    
    # Check for forbidden privacy-violating columns
    for h in raw_headers:
        if any(f in h for f in FORBIDDEN_FIELDS):
            return {
                "valid": False,
                "errors": [f"Privacy violation: Column '{h}' is strictly forbidden. Student/Staff locations cannot be tracked or imported."]
            }

    # Check expected headers
    expected = EXPECTED_HEADERS[import_type]
    missing_headers = [req for req in REQUIRED_FIELDS[import_type] if req not in raw_headers]
    if missing_headers:
        return {
            "valid": False,
            "errors": [f"Missing required columns in Excel: {', '.join(missing_headers)}. Expected columns: {', '.join(expected)}"]
        }

    # Header map
    header_indices = {h: idx for idx, h in enumerate(raw_headers) if h}

    valid_records = []
    errors = []
    seen_usernames = set()
    seen_identifiers = set() # roll_number / employee_id / license_number

    # Pre-fetch existing usernames
    existing_users = {u.username.lower() for u in db.query(User.username).all()}
    
    identifier_col = "roll_number" if import_type == "student" else ("employee_id" if import_type == "staff" else "license_number")
    
    existing_identifiers = set()
    if import_type == "student":
        existing_identifiers = {s.roll_number.lower() for s in db.query(StudentProfile.roll_number).all()}
    elif import_type == "staff":
        existing_identifiers = {s.employee_id.lower() for s in db.query(StaffProfile.employee_id).all()}
    elif import_type == "driver":
        existing_identifiers = {d.license_number.lower() for d in db.query(DriverProfile.license_number).all()}

    for row_idx, row in enumerate(rows[1:], start=2):
        if not any(row):
            continue # Skip completely empty rows

        record = {}
        for col_name, col_idx in header_indices.items():
            val = row[col_idx] if col_idx < len(row) else None
            record[col_name] = str(val).strip() if val is not None else ""

        row_errors = []

        # Check required fields
        for rf in REQUIRED_FIELDS[import_type]:
            if not record.get(rf):
                row_errors.append(f"Missing required field '{rf}'")

        # Check username conflicts
        u_name = record.get("username", "").lower()
        if u_name:
            if u_name in seen_usernames:
                row_errors.append(f"Duplicate username '{record['username']}' within file")
            elif u_name in existing_users:
                row_errors.append(f"Username '{record['username']}' already exists in database")
            seen_usernames.add(u_name)

        # Check identifier conflicts
        ident = record.get(identifier_col, "").lower()
        if ident:
            if ident in seen_identifiers:
                row_errors.append(f"Duplicate {identifier_col} '{record[identifier_col]}' within file")
            elif ident in existing_identifiers:
                row_errors.append(f"{identifier_col} '{record[identifier_col]}' already registered in database")
            seen_identifiers.add(ident)

        if row_errors:
            errors.append(f"Row {row_idx}: {'; '.join(row_errors)}")
        else:
            # Mask password in preview
            preview_record = record.copy()
            preview_record["password"] = "••••••••"
            valid_records.append({"row_num": row_idx, "data": record, "preview": preview_record})

    return {
        "valid": len(errors) == 0,
        "import_type": import_type,
        "total_rows": len(rows) - 1,
        "valid_count": len(valid_records),
        "error_count": len(errors),
        "errors": errors,
        "preview_records": [r["preview"] for r in valid_records[:10]],
        "raw_valid_data": [r["data"] for r in valid_records]
    }

def commit_excel_records(valid_data: List[Dict[str, Any]], import_type: str, db: Session) -> Dict[str, Any]:
    """
    Persists validated records to database with appropriate profiles and roles.
    """
    imported_count = 0
    role = (
        UserRole.STUDENT.value if import_type == "student"
        else (UserRole.STAFF.value if import_type == "staff" else UserRole.DRIVER.value)
    )

    for item in valid_data:
        user = User(
            username=item["username"],
            email=item.get("email") or None,
            full_name=item["full_name"],
            hashed_password=get_password_hash(item["password"]),
            role=role,
            phone=item.get("phone") or None,
            is_active=True
        )
        db.add(user)
        db.flush()

        if import_type == "student":
            profile = StudentProfile(
                user_id=user.id,
                roll_number=item["roll_number"],
                department=item.get("department", "General"),
                year=int(item.get("year", 1)) if item.get("year", "").isdigit() else 1,
                semester=int(item.get("semester", 1)) if item.get("semester", "").isdigit() else None
            )
            db.add(profile)
        elif import_type == "staff":
            profile = StaffProfile(
                user_id=user.id,
                employee_id=item["employee_id"],
                department=item.get("department", "General"),
                designation=item.get("designation", "Faculty")
            )
            db.add(profile)
        elif import_type == "driver":
            profile = DriverProfile(
                user_id=user.id,
                license_number=item["license_number"],
                experience_years=int(item.get("experience_years", 0)) if item.get("experience_years", "").isdigit() else 0
            )
            db.add(profile)

        imported_count += 1

    db.commit()
    return {"status": "success", "imported_count": imported_count, "import_type": import_type}
