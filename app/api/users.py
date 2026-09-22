from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.user import User, StudentProfile, StaffProfile, DriverProfile, UserRole
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.core.security import get_password_hash
from app.api.deps import require_admin

router = APIRouter(prefix="/users", tags=["User Management"])

@router.get("", response_model=List[UserResponse])
def list_users(
    role: Optional[str] = Query(None, description="Filter by role (ADMIN, DRIVER, STUDENT, STAFF)"),
    search: Optional[str] = Query(None, description="Search by username or full_name"),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role.upper())
    if search:
        query = query.filter(
            (User.username.ilike(f"%{search}%")) | (User.full_name.ilike(f"%{search}%"))
        )
    return query.order_by(User.id.desc()).all()

@router.get("/{user_id}", response_model=UserResponse)
def get_user_detail(user_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user_in: UserCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    # Check existing username
    existing_username = db.query(User).filter(User.username == user_in.username).first()
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already exists")

    if user_in.email:
        existing_email = db.query(User).filter(User.email == user_in.email).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        username=user_in.username,
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        role=user_in.role.upper(),
        phone=user_in.phone,
        is_active=user_in.is_active
    )
    db.add(user)
    db.flush()

    # Create associated profile based on role
    if user.role == UserRole.STUDENT.value and user_in.student_profile:
        profile = StudentProfile(
            user_id=user.id,
            roll_number=user_in.student_profile.roll_number,
            department=user_in.student_profile.department,
            year=user_in.student_profile.year,
            semester=user_in.student_profile.semester
        )
        db.add(profile)
    elif user.role == UserRole.STAFF.value and user_in.staff_profile:
        profile = StaffProfile(
            user_id=user.id,
            employee_id=user_in.staff_profile.employee_id,
            department=user_in.staff_profile.department,
            designation=user_in.staff_profile.designation
        )
        db.add(profile)
    elif user.role == UserRole.DRIVER.value and user_in.driver_profile:
        profile = DriverProfile(
            user_id=user.id,
            license_number=user_in.driver_profile.license_number,
            experience_years=user_in.driver_profile.experience_years
        )
        db.add(profile)

    db.commit()
    db.refresh(user)
    return user

@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_update.email is not None:
        user.email = user_update.email
    if user_update.full_name is not None:
        user.full_name = user_update.full_name
    if user_update.phone is not None:
        user.phone = user_update.phone
    if user_update.is_active is not None:
        user.is_active = user_update.is_active
    if user_update.password:
        user.hashed_password = get_password_hash(user_update.password)

    db.commit()
    db.refresh(user)
    return user

@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
def deactivate_user(user_id: int, db: Session = Depends(get_db), current_admin: User = Depends(require_admin)):
    if user_id == current_admin.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = False
    db.commit()
    return {"detail": f"User {user.username} deactivated successfully"}
