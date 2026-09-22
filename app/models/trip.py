import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.database import Base

class TripStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    bus_id = Column(Integer, ForeignKey("buses.id", ondelete="CASCADE"), nullable=False)
    driver_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    route_id = Column(Integer, ForeignKey("routes.id", ondelete="CASCADE"), nullable=False)

    trip_name = Column(String(100), nullable=False)
    trip_type = Column(String(50), default="MORNING_PICKUP") # MORNING_PICKUP, EVENING_DROPOFF, SPECIAL
    status = Column(String(20), nullable=False, default=TripStatus.NOT_STARTED.value)
    
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)

    # Latest live telemetry (bus-level only, never passengers)
    current_latitude = Column(Float, nullable=True)
    current_longitude = Column(Float, nullable=True)
    current_speed_kmh = Column(Float, default=0.0)
    current_heading = Column(Float, nullable=True)
    current_stop_sequence = Column(Integer, default=1)
    last_ping_time = Column(DateTime, nullable=True)

    # Relationships
    bus = relationship("Bus", back_populates="trips")
    driver = relationship("User", foreign_keys=[driver_id])
    route = relationship("Route", back_populates="trips")
    gps_pings = relationship("GPSPing", back_populates="trip", cascade="all, delete-orphan", order_by="GPSPing.timestamp")
    notifications = relationship("Notification", back_populates="trip", cascade="all, delete-orphan")

class GPSPing(Base):
    """Trip-scoped GPS pings. Strictly associated with an active bus trip."""
    __tablename__ = "gps_pings"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    speed_kmh = Column(Float, default=0.0)
    heading = Column(Float, nullable=True)
    accuracy_meters = Column(Float, nullable=True)
    is_simulated = Column(Boolean, default=False)

    trip = relationship("Trip", back_populates="gps_pings")
