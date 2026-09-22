from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.schemas.bus import BusResponse
from app.schemas.route import RouteResponse
from app.schemas.user import UserResponse
from app.schemas.eta import StopETAResponse

class GPSPingCreate(BaseModel):
    trip_id: int
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    speed_kmh: float = Field(0.0, ge=0.0)
    heading: Optional[float] = None
    accuracy_meters: Optional[float] = None
    is_simulated: bool = False

class GPSPingResponse(BaseModel):
    id: int
    trip_id: int
    timestamp: datetime
    latitude: float
    longitude: float
    speed_kmh: float
    heading: Optional[float] = None
    is_simulated: bool
    model_config = ConfigDict(from_attributes=True)

class TripCreate(BaseModel):
    bus_id: int
    driver_id: int
    route_id: int
    trip_name: str
    trip_type: str = "MORNING_PICKUP"

class TripUpdate(BaseModel):
    status: Optional[str] = None

class TripResponse(BaseModel):
    id: int
    trip_name: str
    trip_type: str
    status: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None
    current_speed_kmh: float
    current_heading: Optional[float] = None
    current_stop_sequence: int
    last_ping_time: Optional[datetime] = None
    
    bus: Optional[BusResponse] = None
    driver: Optional[UserResponse] = None
    route: Optional[RouteResponse] = None
    model_config = ConfigDict(from_attributes=True)

class TripLiveStatusResponse(BaseModel):
    trip: TripResponse
    stops_eta: List[StopETAResponse] = []
