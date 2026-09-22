"""
Generate realistic RPSIT-style Excel files for bulk import demo.
Creates 3 files:
  - rpsit_students.xlsx  (30 students across departments)
  - rpsit_staff.xlsx     (12 faculty members)
  - rpsit_drivers.xlsx   (5 additional drivers)
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "sample_excel")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# -------------------------------------------------------------------
# REALISTIC RPSIT STUDENT DATA
# Roll format: YY{DEPT_CODE}{SEQ}  e.g. 22CS001 = 2022 batch, CSE
# Departments: CS, EC, ME, EE, CE, IT
# -------------------------------------------------------------------
STUDENTS = [
    # (username, full_name, email, phone, password, roll_number, department, year, semester)
    # --- CSE Batch 2022 ---
    ("cs22001", "Aakash Murugan",       "cs22001@rpsit.ac.in", "9751100001", "Pass@1234", "22CS001", "Computer Science & Engineering", 3, 5),
    ("cs22002", "Abinaya Selvam",       "cs22002@rpsit.ac.in", "9751100002", "Pass@1234", "22CS002", "Computer Science & Engineering", 3, 5),
    ("cs22003", "Aravind Kumar R",      "cs22003@rpsit.ac.in", "9751100003", "Pass@1234", "22CS003", "Computer Science & Engineering", 3, 5),
    ("cs22004", "Barathi Devi P",       "cs22004@rpsit.ac.in", "9751100004", "Pass@1234", "22CS004", "Computer Science & Engineering", 3, 5),
    ("cs22005", "Chandru Prakash",      "cs22005@rpsit.ac.in", "9751100005", "Pass@1234", "22CS005", "Computer Science & Engineering", 3, 5),
    # --- ECE Batch 2022 ---
    ("ec22001", "Dinesh Babu K",        "ec22001@rpsit.ac.in", "9751100011", "Pass@1234", "22EC001", "Electronics & Communication Engg", 3, 5),
    ("ec22002", "Eswari Lakshmi",       "ec22002@rpsit.ac.in", "9751100012", "Pass@1234", "22EC002", "Electronics & Communication Engg", 3, 5),
    ("ec22003", "Ganesh Prabhu M",      "ec22003@rpsit.ac.in", "9751100013", "Pass@1234", "22EC003", "Electronics & Communication Engg", 3, 5),
    ("ec22004", "Harini Devi S",        "ec22004@rpsit.ac.in", "9751100014", "Pass@1234", "22EC004", "Electronics & Communication Engg", 3, 5),
    ("ec22005", "Ilayaraja T",          "ec22005@rpsit.ac.in", "9751100015", "Pass@1234", "22EC005", "Electronics & Communication Engg", 3, 5),
    # --- Mechanical Batch 2023 ---
    ("me23001", "Jayakumar S",          "me23001@rpsit.ac.in", "9751100021", "Pass@1234", "23ME001", "Mechanical Engineering", 2, 3),
    ("me23002", "Kalaiyarasi G",        "me23002@rpsit.ac.in", "9751100022", "Pass@1234", "23ME002", "Mechanical Engineering", 2, 3),
    ("me23003", "Karthikeyan R",        "me23003@rpsit.ac.in", "9751100023", "Pass@1234", "23ME003", "Mechanical Engineering", 2, 3),
    ("me23004", "Lavanya Priya",        "me23004@rpsit.ac.in", "9751100024", "Pass@1234", "23ME004", "Mechanical Engineering", 2, 3),
    ("me23005", "Manikandan V",         "me23005@rpsit.ac.in", "9751100025", "Pass@1234", "23ME005", "Mechanical Engineering", 2, 3),
    # --- EEE Batch 2023 ---
    ("ee23001", "Nandha Kumar A",       "ee23001@rpsit.ac.in", "9751100031", "Pass@1234", "23EE001", "Electrical & Electronics Engg", 2, 3),
    ("ee23002", "Oviya Shri",           "ee23002@rpsit.ac.in", "9751100032", "Pass@1234", "23EE002", "Electrical & Electronics Engg", 2, 3),
    ("ee23003", "Palaniswamy K",        "ee23003@rpsit.ac.in", "9751100033", "Pass@1234", "23EE003", "Electrical & Electronics Engg", 2, 3),
    ("ee23004", "Pavithra M",           "ee23004@rpsit.ac.in", "9751100034", "Pass@1234", "23EE004", "Electrical & Electronics Engg", 2, 3),
    ("ee23005", "Ranjith Babu",         "ee23005@rpsit.ac.in", "9751100035", "Pass@1234", "23EE005", "Electrical & Electronics Engg", 2, 3),
    # --- Civil Batch 2024 ---
    ("ce24001", "Sakthivel P",          "ce24001@rpsit.ac.in", "9751100041", "Pass@1234", "24CE001", "Civil Engineering", 1, 1),
    ("ce24002", "Sangeetha R",          "ce24002@rpsit.ac.in", "9751100042", "Pass@1234", "24CE002", "Civil Engineering", 1, 1),
    ("ce24003", "Senthil Kumar G",      "ce24003@rpsit.ac.in", "9751100043", "Pass@1234", "24CE003", "Civil Engineering", 1, 1),
    ("ce24004", "Sharmila Devi",        "ce24004@rpsit.ac.in", "9751100044", "Pass@1234", "24CE004", "Civil Engineering", 1, 1),
    ("ce24005", "Sivakumar A",          "ce24005@rpsit.ac.in", "9751100045", "Pass@1234", "24CE005", "Civil Engineering", 1, 1),
    # --- IT Batch 2022 ---
    ("it22001", "Suresh Babu D",        "it22001@rpsit.ac.in", "9751100051", "Pass@1234", "22IT001", "Information Technology", 3, 5),
    ("it22002", "Tamil Selvi K",        "it22002@rpsit.ac.in", "9751100052", "Pass@1234", "22IT002", "Information Technology", 3, 5),
    ("it22003", "Thirumaran S",         "it22003@rpsit.ac.in", "9751100053", "Pass@1234", "22IT003", "Information Technology", 3, 5),
    ("it22004", "Umamaheswari",         "it22004@rpsit.ac.in", "9751100054", "Pass@1234", "22IT004", "Information Technology", 3, 5),
    ("it22005", "Vasantharaj M",        "it22005@rpsit.ac.in", "9751100055", "Pass@1234", "22IT005", "Information Technology", 3, 5),
]

# -------------------------------------------------------------------
# REALISTIC RPSIT FACULTY DATA
# -------------------------------------------------------------------
STAFF = [
    # (username, full_name, email, phone, password, employee_id, department, designation)
    ("fac004", "Dr. K. Annamalai",         "fac004@rpsit.ac.in", "9443001001", "Pass@1234", "FAC-004", "Computer Science & Engineering", "Professor & Head"),
    ("fac005", "Dr. S. Malathi",           "fac005@rpsit.ac.in", "9443001002", "Pass@1234", "FAC-005", "Computer Science & Engineering", "Associate Professor"),
    ("fac006", "Mr. T. Rajendran",         "fac006@rpsit.ac.in", "9443001003", "Pass@1234", "FAC-006", "Computer Science & Engineering", "Assistant Professor"),
    ("fac007", "Dr. M. Balasubramanian",   "fac007@rpsit.ac.in", "9443001004", "Pass@1234", "FAC-007", "Electronics & Communication Engg", "Professor & Head"),
    ("fac008", "Mrs. P. Vijayalakshmi",    "fac008@rpsit.ac.in", "9443001005", "Pass@1234", "FAC-008", "Electronics & Communication Engg", "Associate Professor"),
    ("fac009", "Mr. G. Subramanian",       "fac009@rpsit.ac.in", "9443001006", "Pass@1234", "FAC-009", "Mechanical Engineering", "Associate Professor"),
    ("fac010", "Dr. N. Krishnamurthy",     "fac010@rpsit.ac.in", "9443001007", "Pass@1234", "FAC-010", "Mechanical Engineering", "Professor & Head"),
    ("fac011", "Mrs. L. Sumathy",          "fac011@rpsit.ac.in", "9443001008", "Pass@1234", "FAC-011", "Electrical & Electronics Engg", "Associate Professor"),
    ("fac012", "Mr. A. Pandiarajan",       "fac012@rpsit.ac.in", "9443001009", "Pass@1234", "FAC-012", "Civil Engineering", "Assistant Professor"),
    ("fac013", "Dr. R. Jayanthi",          "fac013@rpsit.ac.in", "9443001010", "Pass@1234", "FAC-013", "Information Technology", "Associate Professor"),
    ("fac014", "Mr. C. Muthukumar",        "fac014@rpsit.ac.in", "9443001011", "Pass@1234", "FAC-014", "Mathematics", "Assistant Professor"),
    ("fac015", "Mrs. S. Meenakshi",        "fac015@rpsit.ac.in", "9443001012", "Pass@1234", "FAC-015", "Physics", "Assistant Professor"),
]

# -------------------------------------------------------------------
# ADDITIONAL DRIVERS
# -------------------------------------------------------------------
DRIVERS = [
    # (username, full_name, email, phone, password, license_number, experience_years)
    ("driver6", "Pandi Raj A",     "driver6@rpsit.ac.in", "9843001006", "Pass@1234", "TN-38-DL-2016-006", 8),
    ("driver7", "Rajan M",         "driver7@rpsit.ac.in", "9843001007", "Pass@1234", "TN-38-DL-2021-007", 3),
    ("driver8", "Sundaram K",      "driver8@rpsit.ac.in", "9843001008", "Pass@1234", "TN-38-DL-2014-008", 10),
    ("driver9", "Velmurugan S",    "driver9@rpsit.ac.in", "9843001009", "Pass@1234", "TN-38-DL-2022-009", 2),
    ("driver10","Govindasamy P",   "driver10@rpsit.ac.in","9843001010", "Pass@1234", "TN-38-DL-2013-010", 11),
]


def style_header_row(ws, headers, header_color="1E40AF"):
    """Apply professional styling to the header row."""
    fill = PatternFill(start_color=header_color, end_color=header_color, fill_type="solid")
    font = Font(color="FFFFFF", bold=True, size=11)
    border = Border(
        bottom=Side(style="medium", color="000000"),
        right=Side(style="thin", color="CCCCCC")
    )
    
    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.fill = fill
        cell.font = font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border
    
    ws.row_dimensions[1].height = 30


def style_data_rows(ws, total_rows, total_cols):
    """Apply alternating row colors and border styling."""
    light_fill = PatternFill(start_color="EFF6FF", end_color="EFF6FF", fill_type="solid")
    normal_font = Font(size=10)
    border = Border(
        bottom=Side(style="thin", color="E2E8F0"),
        right=Side(style="thin", color="E2E8F0")
    )
    
    for row_idx in range(2, total_rows + 2):
        for col_idx in range(1, total_cols + 1):
            cell = ws.cell(row=row_idx, column=col_idx)
            if row_idx % 2 == 0:
                cell.fill = light_fill
            cell.font = normal_font
            cell.border = border
            cell.alignment = Alignment(vertical="center")
        ws.row_dimensions[row_idx].height = 22


def auto_fit_columns(ws, min_width=12, max_width=45):
    for col_cells in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col_cells[0].column)
        for cell in col_cells:
            if cell.value:
                max_len = max(max_len, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = min(max_width, max(min_width, max_len + 2))


def create_student_excel():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "RPSIT Students"

    # Title banner
    ws.merge_cells("A1:I1")
    title_cell = ws["A1"]
    title_cell.value = "R.P. SARATHY INSTITUTE OF TECHNOLOGY - Student Bus Allocation Data"
    title_cell.font = Font(bold=True, size=13, color="1E40AF")
    title_cell.fill = PatternFill(start_color="EFF6FF", end_color="EFF6FF", fill_type="solid")
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 32

    headers = ["username", "full_name", "email", "phone", "password", "roll_number", "department", "year", "semester"]
    for col_idx, h in enumerate(headers, 1):
        cell = ws.cell(row=2, column=col_idx, value=h)
        cell.fill = PatternFill(start_color="1E40AF", end_color="1E40AF", fill_type="solid")
        cell.font = Font(color="FFFFFF", bold=True, size=11)
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = Border(bottom=Side(style="medium"))
    ws.row_dimensions[2].height = 28

    light = PatternFill(start_color="EFF6FF", end_color="EFF6FF", fill_type="solid")
    for row_idx, s in enumerate(STUDENTS, 3):
        row_data = list(s)
        for col_idx, val in enumerate(row_data, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            cell.font = Font(size=10)
            if row_idx % 2 == 0:
                cell.fill = light
            cell.alignment = Alignment(vertical="center")
        ws.row_dimensions[row_idx].height = 20

    # Notes row
    note_row = len(STUDENTS) + 4
    ws.merge_cells(f"A{note_row}:I{note_row}")
    note_cell = ws.cell(row=note_row, column=1,
        value="NOTE: Password column is required. Passwords will be hashed with PBKDF2-SHA256 before storage. No GPS/location columns are collected per privacy policy.")
    note_cell.font = Font(italic=True, color="64748B", size=9)
    note_cell.alignment = Alignment(horizontal="left", vertical="center")

    auto_fit_columns(ws)
    ws.freeze_panes = "A3"

    path = os.path.join(OUTPUT_DIR, "rpsit_students.xlsx")
    wb.save(path)
    print(f"  [OK] Created: {path} ({len(STUDENTS)} students)")
    return path


def create_staff_excel():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "RPSIT Faculty Staff"

    ws.merge_cells("A1:H1")
    title_cell = ws["A1"]
    title_cell.value = "R.P. SARATHY INSTITUTE OF TECHNOLOGY - Faculty & Staff Bus Allocation Data"
    title_cell.font = Font(bold=True, size=13, color="166534")
    title_cell.fill = PatternFill(start_color="F0FDF4", end_color="F0FDF4", fill_type="solid")
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 32

    headers = ["username", "full_name", "email", "phone", "password", "employee_id", "department", "designation"]
    for col_idx, h in enumerate(headers, 1):
        cell = ws.cell(row=2, column=col_idx, value=h)
        cell.fill = PatternFill(start_color="166534", end_color="166534", fill_type="solid")
        cell.font = Font(color="FFFFFF", bold=True, size=11)
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = Border(bottom=Side(style="medium"))
    ws.row_dimensions[2].height = 28

    light = PatternFill(start_color="F0FDF4", end_color="F0FDF4", fill_type="solid")
    for row_idx, s in enumerate(STAFF, 3):
        row_data = list(s)
        for col_idx, val in enumerate(row_data, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            cell.font = Font(size=10)
            if row_idx % 2 == 0:
                cell.fill = light
            cell.alignment = Alignment(vertical="center")
        ws.row_dimensions[row_idx].height = 20

    auto_fit_columns(ws)
    ws.freeze_panes = "A3"

    path = os.path.join(OUTPUT_DIR, "rpsit_staff.xlsx")
    wb.save(path)
    print(f"  [OK] Created: {path} ({len(STAFF)} faculty)")
    return path


def create_driver_excel():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "RPSIT Drivers"

    ws.merge_cells("A1:G1")
    title_cell = ws["A1"]
    title_cell.value = "R.P. SARATHY INSTITUTE OF TECHNOLOGY - Bus Drivers Data"
    title_cell.font = Font(bold=True, size=13, color="92400E")
    title_cell.fill = PatternFill(start_color="FFFBEB", end_color="FFFBEB", fill_type="solid")
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 32

    headers = ["username", "full_name", "email", "phone", "password", "license_number", "experience_years"]
    for col_idx, h in enumerate(headers, 1):
        cell = ws.cell(row=2, column=col_idx, value=h)
        cell.fill = PatternFill(start_color="B45309", end_color="B45309", fill_type="solid")
        cell.font = Font(color="FFFFFF", bold=True, size=11)
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = Border(bottom=Side(style="medium"))
    ws.row_dimensions[2].height = 28

    light = PatternFill(start_color="FFFBEB", end_color="FFFBEB", fill_type="solid")
    for row_idx, d in enumerate(DRIVERS, 3):
        row_data = list(d)
        for col_idx, val in enumerate(row_data, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            cell.font = Font(size=10)
            if row_idx % 2 == 0:
                cell.fill = light
            cell.alignment = Alignment(vertical="center")
        ws.row_dimensions[row_idx].height = 20

    auto_fit_columns(ws)
    ws.freeze_panes = "A3"

    path = os.path.join(OUTPUT_DIR, "rpsit_drivers.xlsx")
    wb.save(path)
    print(f"  [OK] Created: {path} ({len(DRIVERS)} drivers)")
    return path


def create_blank_templates():
    """Create blank import templates for the college to fill with real data."""
    
    # Blank Student Template
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Students"
    ws.merge_cells("A1:I1")
    ws["A1"].value = "RPSIT Student Import Template - Fill this with real student data"
    ws["A1"].font = Font(bold=True, size=12, color="1E40AF")
    ws["A1"].fill = PatternFill(start_color="DBEAFE", end_color="DBEAFE", fill_type="solid")
    ws["A1"].alignment = Alignment(horizontal="center")
    ws.row_dimensions[1].height = 28

    headers = ["username", "full_name", "email", "phone", "password", "roll_number", "department", "year", "semester"]
    for col_idx, h in enumerate(headers, 1):
        cell = ws.cell(row=2, column=col_idx, value=h)
        cell.fill = PatternFill(start_color="1E40AF", end_color="1E40AF", fill_type="solid")
        cell.font = Font(color="FFFFFF", bold=True)
        cell.alignment = Alignment(horizontal="center")
    
    # Example row
    example = ["cs22xxx", "Student Full Name", "rollno@rpsit.ac.in", "9XXXXXXXXX", "Pass@1234", "22CS0XX", "Computer Science & Engineering", 3, 5]
    for col_idx, val in enumerate(example, 1):
        cell = ws.cell(row=3, column=col_idx, value=val)
        cell.font = Font(italic=True, color="94A3B8")
    
    for col_cells in ws.columns:
        ws.column_dimensions[get_column_letter(col_cells[0].column)].width = 30

    path = os.path.join(OUTPUT_DIR, "template_students.xlsx")
    wb.save(path)
    print(f"  [OK] Blank template: {path}")

    # Blank Staff Template
    wb2 = openpyxl.Workbook()
    ws2 = wb2.active
    ws2.title = "Staff"
    ws2.merge_cells("A1:H1")
    ws2["A1"].value = "RPSIT Staff/Faculty Import Template - Fill with real faculty data"
    ws2["A1"].font = Font(bold=True, size=12, color="166534")
    ws2["A1"].fill = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")
    ws2["A1"].alignment = Alignment(horizontal="center")
    ws2.row_dimensions[1].height = 28

    headers2 = ["username", "full_name", "email", "phone", "password", "employee_id", "department", "designation"]
    for col_idx, h in enumerate(headers2, 1):
        cell = ws2.cell(row=2, column=col_idx, value=h)
        cell.fill = PatternFill(start_color="166534", end_color="166534", fill_type="solid")
        cell.font = Font(color="FFFFFF", bold=True)
        cell.alignment = Alignment(horizontal="center")

    example2 = ["fac0XX", "Dr./Mr./Mrs. Full Name", "facid@rpsit.ac.in", "9XXXXXXXXX", "Pass@1234", "FAC-0XX", "Department Name", "Professor/Asst. Professor"]
    for col_idx, val in enumerate(example2, 1):
        cell = ws2.cell(row=3, column=col_idx, value=val)
        cell.font = Font(italic=True, color="94A3B8")

    for col_cells in ws2.columns:
        ws2.column_dimensions[get_column_letter(col_cells[0].column)].width = 32

    path2 = os.path.join(OUTPUT_DIR, "template_staff.xlsx")
    wb2.save(path2)
    print(f"  [OK] Blank template: {path2}")


def auto_import_to_db(student_path, staff_path, driver_path):
    """Auto-import the generated Excel files into the live RPSIT database."""
    from app.services.excel_service import parse_and_validate_excel, commit_excel_records
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        results = []
        for fpath, import_type in [
            (student_path, "student"),
            (staff_path, "staff"),
            (driver_path, "driver")
        ]:
            with open(fpath, "rb") as f:
                content = f.read()
            
            print(f"\n  Validating {import_type} Excel file...")
            preview = parse_and_validate_excel(content, import_type, db)
            
            if preview["valid"]:
                print(f"    Valid: {preview['valid_count']} records found, 0 errors")
                result = commit_excel_records(preview["raw_valid_data"], import_type, db)
                print(f"    Imported: {result['imported_count']} {import_type} records committed to database")
                results.append(result)
            else:
                print(f"    Skipped ({len(preview['errors'])} errors):")
                for err in preview["errors"][:3]:
                    print(f"      - {err}")
                if len(preview["errors"]) > 3:
                    print(f"      ... and {len(preview['errors']) - 3} more")
        
        return results
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("RPSIT Excel Data Generator")
    print("=" * 60)
    print("\n[1/3] Generating demo Excel files with realistic RPSIT data...")
    student_path = create_student_excel()
    staff_path   = create_staff_excel()
    driver_path  = create_driver_excel()
    create_blank_templates()

    print("\n[2/3] Auto-importing generated data into live database...")
    auto_import_to_db(student_path, staff_path, driver_path)

    print("\n[3/3] Summary:")
    print(f"  Excel files saved in: {OUTPUT_DIR}")
    print("  - rpsit_students.xlsx  (30 students, ready to import or customize)")
    print("  - rpsit_staff.xlsx     (12 faculty members)")
    print("  - rpsit_drivers.xlsx   (5 additional drivers)")
    print("  - template_students.xlsx  (blank template for real student data)")
    print("  - template_staff.xlsx     (blank template for real faculty data)")
    print("\nYou can now:")
    print("  1. Upload real student data into the blank templates")
    print("  2. Import via Admin Panel > Excel Bulk Import")
    print("  3. Or re-run this script to regenerate demo data")
