from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List

class StopBase(BaseModel):
    stop_name: str
    sequence: int = Field(..., ge=1)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    scheduled_offset_minutes: int = Field(0, ge=0)
    is_active: bool = True

class StopCreate(StopBase):
    route_id: Optional[int] = None

class StopUpdate(BaseModel):
    stop_name: Optional[str] = None
    sequence: Optional[int] = Field(None, ge=1)
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    scheduled_offset_minutes: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None

class StopResponse(StopBase):
    id: int
    route_id: int
    model_config = ConfigDict(from_attributes=True)

class RouteBase(BaseModel):
    route_name: str
    route_code: str
    description: Optional[str] = None
    is_active: bool = True

class RouteCreate(RouteBase):
    stops: Optional[List[StopCreate]] = None

class RouteUpdate(BaseModel):
    route_name: Optional[str] = None
    route_code: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class RouteResponse(RouteBase):
    id: int
    stops: List[StopResponse] = []
    model_config = ConfigDict(from_attributes=True)
