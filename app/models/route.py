from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Route(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    route_name = Column(String(100), unique=True, index=True, nullable=False)
    route_code = Column(String(20), unique=True, index=True, nullable=False)
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)

    stops = relationship("Stop", back_populates="route", cascade="all, delete-orphan", order_by="Stop.sequence")
    buses = relationship("Bus", back_populates="default_route")
    trips = relationship("Trip", back_populates="route")

class Stop(Base):
    __tablename__ = "stops"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id", ondelete="CASCADE"), nullable=False)
    stop_name = Column(String(100), nullable=False)
    sequence = Column(Integer, nullable=False)
    latitude = Column(Float, nullable=False)  # Fixed infrastructure coordinate
    longitude = Column(Float, nullable=False) # Fixed infrastructure coordinate
    scheduled_offset_minutes = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True)

    route = relationship("Route", back_populates="stops")
    default_assignments = relationship("DefaultAssignment", back_populates="stop")
    special_assignments = relationship("SpecialAssignment", back_populates="stop")
    notifications = relationship("Notification", back_populates="stop")
