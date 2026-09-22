"""Pydantic v2 schemas for the Passenger-Assisted Location ("I'm On This Bus") feature."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class StartSessionRequest(BaseModel):
    """Passenger explicitly consents and starts a location-sharing session."""
    consent: bool = Field(..., description="Must be True — explicit passenger consent required")


class PassengerPingCreate(BaseModel):
    """Single GPS report submitted by a passenger during an active session."""
    session_id: int
    latitude:  float = Field(..., ge=-90,  le=90)
    longitude: float = Field(..., ge=-180, le=180)
    accuracy_meters: Optional[float] = Field(None, ge=0)
    speed_kmh:       Optional[float] = Field(None, ge=0)
    heading:         Optional[float] = Field(None, ge=0, le=360)


class SessionStatusResponse(BaseModel):
    """Own session status — returned only to the session owner."""
    model_config = ConfigDict(from_attributes=True)

    id:           int
    user_id:      int
    trip_id:      int
    bus_id:       int
    status:       str
    consent_given: bool
    started_at:   datetime
    ended_at:     Optional[datetime] = None
    last_ping_at: Optional[datetime] = None
    expires_at:   datetime


class PassengerPingResponse(BaseModel):
    """Acknowledgement returned after a successful ping submission."""
    model_config = ConfigDict(from_attributes=True)

    id:                int
    session_id:        int
    timestamp:         datetime
    validation_status: str
    confidence_score:  float


class BusPositionResponse(BaseModel):
    """
    Aggregated, fully anonymized bus position.
    No passenger identity, no individual passenger coordinates.
    """
    trip_id:              int
    bus_id:               int
    bus_number:           str
    latitude:             Optional[float]   = None
    longitude:            Optional[float]   = None
    source:               str               # DRIVER_GPS | PASSENGER_ASSISTED | COMBINED | SCHEDULE_ESTIMATE | UNKNOWN
    confidence:           str               # HIGH | MEDIUM | LOW | UNKNOWN
    label:                str               # "Live GPS" | "Passenger-assisted" | "Estimated" | "Unavailable"
    contributor_count:    int = 0           # Anonymous count of helping passengers
    driver_gps_age_sec:   Optional[int]     = None
    computed_at:          datetime
