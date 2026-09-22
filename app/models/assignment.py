from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Date
from sqlalchemy.orm import relationship
from app.database import Base

class DefaultAssignment(Base):
    __tablename__ = "default_assignments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    bus_id = Column(Integer, ForeignKey("buses.id", ondelete="CASCADE"), nullable=False)
    stop_id = Column(Integer, ForeignKey("stops.id", ondelete="CASCADE"), nullable=False)
    academic_year = Column(String(20), default="2025-2026")
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="default_assignment")
    bus = relationship("Bus", back_populates="default_assignments")
    stop = relationship("Stop", back_populates="default_assignments")

class SpecialAssignment(Base):
    """Temporary or Exam-day assignment override."""
    __tablename__ = "special_assignments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    bus_id = Column(Integer, ForeignKey("buses.id", ondelete="CASCADE"), nullable=False)
    stop_id = Column(Integer, ForeignKey("stops.id", ondelete="CASCADE"), nullable=False)
    effective_date = Column(Date, nullable=False)
    reason = Column(String(100), default="Exam Day Assignment")
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="special_assignments")
    bus = relationship("Bus", back_populates="special_assignments")
    stop = relationship("Stop", back_populates="special_assignments")
