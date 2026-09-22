from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Bus(Base):
    __tablename__ = "buses"

    id = Column(Integer, primary_key=True, index=True)
    bus_number = Column(String(50), unique=True, index=True, nullable=False) # e.g. "BUS-01"
    registration_number = Column(String(50), unique=True, index=True, nullable=False) # e.g. "TN-67-AB-1234"
    capacity = Column(Integer, nullable=False, default=50)
    is_active = Column(Boolean, default=True)
    status = Column(String(30), default="IDLE") # IDLE, ON_TRIP, MAINTENANCE, INACTIVE

    current_driver_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    default_route_id = Column(Integer, ForeignKey("routes.id", ondelete="SET NULL"), nullable=True)

    current_driver = relationship("User", foreign_keys=[current_driver_id])
    default_route = relationship("Route", back_populates="buses")
    trips = relationship("Trip", back_populates="bus")
    default_assignments = relationship("DefaultAssignment", back_populates="bus")
    special_assignments = relationship("SpecialAssignment", back_populates="bus")
