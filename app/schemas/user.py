from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int
    username: str
    full_name: str

class TokenData(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None
    role: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

# Profile Schemas (Strictly no location/GPS fields!)
class StudentProfileBase(BaseModel):
    roll_number: str
    department: str
    year: int = 1
    semester: Optional[int] = None

class StudentProfileCreate(StudentProfileBase):
    pass

class StudentProfileResponse(StudentProfileBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class StaffProfileBase(BaseModel):
    employee_id: str
    department: str
    designation: str

class StaffProfileCreate(StaffProfileBase):
    pass

class StaffProfileResponse(StaffProfileBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class DriverProfileBase(BaseModel):
    license_number: str
    experience_years: int = 0

class DriverProfileCreate(DriverProfileBase):
    pass

class DriverProfileResponse(DriverProfileBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# User Schemas
class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    full_name: str
    role: str
    phone: Optional[str] = None
    is_active: bool = True

class UserCreate(UserBase):
    password: str
    student_profile: Optional[StudentProfileCreate] = None
    staff_profile: Optional[StaffProfileCreate] = None
    driver_profile: Optional[DriverProfileCreate] = None

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

class UserResponse(UserBase):
    id: int
    created_at: Optional[datetime] = None
    student_profile: Optional[StudentProfileResponse] = None
    staff_profile: Optional[StaffProfileResponse] = None
    driver_profile: Optional[DriverProfileResponse] = None

    model_config = ConfigDict(from_attributes=True)
