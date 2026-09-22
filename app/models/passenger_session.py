"""
Passenger Session Models — "I'm On This Bus" Feature

Two tables:
  - PassengerSession   : one per passenger per trip, tracks consent + lifetime
  - PassengerLocationPing : individual GPS reports, validated + confidence-scored

Privacy guarantees:
  - No personal identity in public-facing APIs
  - Pings are anonymized before being served externally
  - Sessions tied strictly to active trips; auto-expire when trip ends
"""
import enum
from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class SessionStatus(str, enum.Enum):
    ACTIVE  = "ACTIVE"
    STOPPED = "STOPPED"
    EXPIRED = "EXPIRED"


class PingValidation(str, enum.Enum):
    VALID    = "VALID"
    OUTLIER  = "OUTLIER"
    STALE    = "STALE"
    REJECTED = "REJECTED"


class PassengerSession(Base):
    """
    One session per passenger per active trip.
    Created only after explicit consent. Terminated on stop, expiry, or trip end.
    """
    __tablename__ = "passenger_sessions"

    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey("users.id",  ondelete="CASCADE"), nullable=False, index=True)
    trip_id      = Column(Integer, ForeignKey("trips.id",  ondelete="CASCADE"), nullable=False, index=True)
    bus_id       = Column(Integer, ForeignKey("buses.id",  ondelete="CASCADE"), nullable=False)

    status       = Column(String(20), nullable=False, default=SessionStatus.ACTIVE.value)
    consent_given = Column(Boolean, nullable=False, default=False)

    started_at   = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    ended_at     = Column(DateTime, nullable=True)
    last_ping_at = Column(DateTime, nullable=True)
    # Hard expiry: max 4 hours per session regardless of trip state
    expires_at   = Column(DateTime, nullable=False,
                          default=lambda: datetime.now(timezone.utc) + timedelta(hours=4))

    # Relationships
    user         = relationship("User",  foreign_keys=[user_id])
    trip         = relationship("Trip",  foreign_keys=[trip_id])
    bus          = relationship("Bus",   foreign_keys=[bus_id])
    pings        = relationship("PassengerLocationPing", back_populates="session",
                                cascade="all, delete-orphan",
                                order_by="PassengerLocationPing.timestamp")


class PassengerLocationPing(Base):
    """
    Single GPS report from a passenger. Validated and confidence-scored.
    Never exposed externally with user identity.
    """
    __tablename__ = "passenger_location_pings"

    id               = Column(Integer, primary_key=True, index=True)
    session_id       = Column(Integer, ForeignKey("passenger_sessions.id", ondelete="CASCADE"),
                              nullable=False, index=True)
    trip_id          = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"),
                              nullable=False, index=True)

    timestamp        = Column(DateTime, nullable=False,
                              default=lambda: datetime.now(timezone.utc), index=True)
    latitude         = Column(Float, nullable=False)
    longitude        = Column(Float, nullable=False)
    accuracy_meters  = Column(Float, nullable=True)
    speed_kmh        = Column(Float, nullable=True)
    heading          = Column(Float, nullable=True)

    # Validation outcome
    validation_status = Column(String(20), nullable=False, default=PingValidation.VALID.value)
    confidence_score  = Column(Float, nullable=False, default=1.0)  # 0.0 – 1.0

    session  = relationship("PassengerSession", back_populates="pings")
