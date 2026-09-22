from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any

from app.database import get_db
from app.models.user import User
from app.api.deps import require_admin
from app.services.excel_service import parse_and_validate_excel, commit_excel_records

router = APIRouter(prefix="/imports", tags=["Bulk Import"])

class ImportConfirmRequest(BaseModel):
    import_type: str
    records: List[Dict[str, Any]]

@router.post("/preview")
async def preview_excel_import(
    file: UploadFile = File(...),
    import_type: str = Form(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    """
    Step 1 of Excel Bulk Import: Validates uploaded spreadsheet.
    Detects missing fields, invalid formats, database conflicts,
    and strictly forbids passenger GPS/location fields.
    """
    if not file.filename.endswith((".xlsx", ".xlsm")):
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xlsm) are supported")

    content = await file.read()
    result = parse_and_validate_excel(content, import_type.lower(), db)
    return result

@router.post("/confirm")
def confirm_excel_import(
    req: ImportConfirmRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    """
    Step 2 of Excel Bulk Import: Saves validated records to the database.
    """
    if not req.records:
        raise HTTPException(status_code=400, detail="No records provided to import")

    result = commit_excel_records(req.records, req.import_type.lower(), db)
    return result
