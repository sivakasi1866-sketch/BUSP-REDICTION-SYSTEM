from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.database import get_db
from app.models.assignment import DefaultAssignment, SpecialAssignment
from app.models.user import User, UserRole
from app.models.bus import Bus
from app.models.route import Stop
from app.schemas.assignment import (
    DefaultAssignmentCreate, DefaultAssignmentResponse,
    SpecialAssignmentCreate, SpecialAssignmentResponse
)
from app.api.deps import require_admin, get_current_user

router = APIRouter(prefix="/assignments", tags=["Assignment Management"])

@router.get("/default", response_model=List[DefaultAssignmentResponse])
def list_default_assignments(
    bus_id: Optional[int] = Query(None),
    stop_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    query = db.query(DefaultAssignment)
    if bus_id:
        query = query.filter(DefaultAssignment.bus_id == bus_id)
    if stop_id:
        query = query.filter(DefaultAssignment.stop_id == stop_id)
    return query.all()

@router.post("/default", response_model=DefaultAssignmentResponse, status_code=status.HTTP_201_CREATED)
def create_or_update_default_assignment(
    assign_in: DefaultAssignmentCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    # Validate user, bus, stop
    user = db.query(User).filter(User.id == assign_in.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    bus = db.query(Bus).filter(Bus.id == assign_in.bus_id).first()
    if not bus or not bus.is_active:
        raise HTTPException(status_code=404, detail="Active bus not found")
    stop = db.query(Stop).filter(Stop.id == assign_in.stop_id).first()
    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found")

    # Check existing assignment for this user
    assignment = db.query(DefaultAssignment).filter(DefaultAssignment.user_id == assign_in.user_id).first()
    if assignment:
        assignment.bus_id = assign_in.bus_id
        assignment.stop_id = assign_in.stop_id
        assignment.academic_year = assign_in.academic_year
        assignment.is_active = assign_in.is_active
    else:
        assignment = DefaultAssignment(
            user_id=assign_in.user_id,
            bus_id=assign_in.bus_id,
            stop_id=assign_in.stop_id,
            academic_year=assign_in.academic_year,
            is_active=assign_in.is_active
        )
        db.add(assignment)

    db.commit()
    db.refresh(assignment)
    return assignment

@router.get("/special", response_model=List[SpecialAssignmentResponse])
def list_special_assignments(
    effective_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    query = db.query(SpecialAssignment)
    if effective_date:
        query = query.filter(SpecialAssignment.effective_date == effective_date)
    return query.all()

@router.post("/special", response_model=SpecialAssignmentResponse, status_code=status.HTTP_201_CREATED)
def create_special_assignment(
    assign_in: SpecialAssignmentCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    user = db.query(User).filter(User.id == assign_in.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    bus = db.query(Bus).filter(Bus.id == assign_in.bus_id).first()
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")
    stop = db.query(Stop).filter(Stop.id == assign_in.stop_id).first()
    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found")

    special = SpecialAssignment(
        user_id=assign_in.user_id,
        bus_id=assign_in.bus_id,
        stop_id=assign_in.stop_id,
        effective_date=assign_in.effective_date,
        reason=assign_in.reason,
        is_active=assign_in.is_active
    )
    db.add(special)
    db.commit()
    db.refresh(special)
    return special

@router.get("/my-assignment")
def get_my_assignment(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns the current user's effective bus and stop assignment."""
    today = date.today()
    # Check special assignment first (e.g. exam day)
    special = db.query(SpecialAssignment).filter(
        SpecialAssignment.user_id == current_user.id,
        SpecialAssignment.effective_date == today,
        SpecialAssignment.is_active == True
    ).first()

    if special:
        return {
            "type": "SPECIAL",
            "reason": special.reason,
            "bus": special.bus,
            "stop": special.stop,
            "route": special.stop.route if special.stop else None
        }

    default = db.query(DefaultAssignment).filter(
        DefaultAssignment.user_id == current_user.id,
        DefaultAssignment.is_active == True
    ).first()

    if default:
        return {
            "type": "DEFAULT",
            "reason": "Standard Academic Assignment",
            "bus": default.bus,
            "stop": default.stop,
            "route": default.stop.route if default.stop else None
        }

    return {"type": "NONE", "message": "No bus or stop assigned yet. Please contact admin."}
