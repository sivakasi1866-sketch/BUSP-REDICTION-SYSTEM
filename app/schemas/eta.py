from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class StopETAResponse(BaseModel):
    stop_id: int
    stop_name: str
    sequence: int
    latitude: float
    longitude: float
    
    # Distinction between timing methodologies
    scheduled_arrival_time: Optional[str] = None
    calculated_eta_minutes: float
    ml_predicted_eta_minutes: Optional[float] = None
    final_eta_minutes: float
    eta_timestamp: Optional[datetime] = None
    
    distance_remaining_km: float
    status: str # "PASSED", "NEXT", "UPCOMING", "ARRIVED"

class TripETAResponse(BaseModel):
    trip_id: int
    bus_number: str
    route_name: str
    current_speed_kmh: float
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None
    last_updated: Optional[datetime] = None
    stops_eta: list[StopETAResponse] = []
