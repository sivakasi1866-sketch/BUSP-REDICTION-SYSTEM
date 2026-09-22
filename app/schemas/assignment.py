from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date
from app.schemas.user import UserResponse
from app.schemas.bus import BusResponse
from app.schemas.route import StopResponse

class DefaultAssignmentBase(BaseModel):
    user_id: int
    bus_id: int
    stop_id: int
    academic_year: str = "2025-2026"
    is_active: bool = True

class DefaultAssignmentCreate(DefaultAssignmentBase):
    pass

class DefaultAssignmentResponse(DefaultAssignmentBase):
    id: int
    user: Optional[UserResponse] = None
    bus: Optional[BusResponse] = None
    stop: Optional[StopResponse] = None
    model_config = ConfigDict(from_attributes=True)

class SpecialAssignmentBase(BaseModel):
    user_id: int
    bus_id: int
    stop_id: int
    effective_date: date
    reason: str = "Exam Day Assignment"
    is_active: bool = True

class SpecialAssignmentCreate(SpecialAssignmentBase):
    pass

class SpecialAssignmentResponse(SpecialAssignmentBase):
    id: int
    user: Optional[UserResponse] = None
    bus: Optional[BusResponse] = None
    stop: Optional[StopResponse] = None
    model_config = ConfigDict(from_attributes=True)
