from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from app.schemas.user import UserResponse
from app.schemas.route import RouteResponse

class BusBase(BaseModel):
    bus_number: str
    registration_number: str
    capacity: int = Field(..., gt=0, le=120)
    is_active: bool = True
    status: str = "IDLE"
    current_driver_id: Optional[int] = None
    default_route_id: Optional[int] = None

class BusCreate(BusBase):
    pass

class BusUpdate(BaseModel):
    bus_number: Optional[str] = None
    registration_number: Optional[str] = None
    capacity: Optional[int] = Field(None, gt=0, le=120)
    is_active: Optional[bool] = None
    status: Optional[str] = None
    current_driver_id: Optional[int] = None
    default_route_id: Optional[int] = None

class BusResponse(BusBase):
    id: int
    current_driver: Optional[UserResponse] = None
    default_route: Optional[RouteResponse] = None
    model_config = ConfigDict(from_attributes=True)
