"""
Passenger Location Service — "I'm On This Bus" Feature

Core responsibilities:
  1. Validate individual passenger GPS pings (outlier detection, accuracy, speed)
  2. Aggregate multiple passenger signals into a consensus bus position
  3. Determine bus location source priority (Driver GPS > Passenger > Schedule)
  4. Expire stale/invalid sessions
  5. NEVER expose individual passenger identity or exact location externally
"""
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
import statistics

from sqlalchemy.orm import Session

from app.models.trip import Trip, TripStatus
from app.models.passenger_session import PassengerSession, PassengerLocationPing, SessionStatus, PingValidation
from app.models.route import Stop
from app.ml.feature_engineering import haversine_distance

# ── Validation thresholds ────────────────────────────────────────────────────
MAX_ACCURACY_METERS  = 150.0   # Reject if GPS accuracy worse than 150 m
MAX_SPEED_KMH        = 120.0   # Reject if reported speed is physically impossible for a bus
MAX_ROUTE_OFFSET_KM  = 2.0     # Reject if ping is > 2 km from nearest route stop
MAX_PING_AGE_SECONDS = 90      # Reject stale pings older than 90 seconds
DRIVER_GPS_STALE_SEC = 45      # Driver GPS older than 45s → consider unavailable

# ── Session settings ─────────────────────────────────────────────────────────
SESSION_MAX_HOURS    = 4       # Hard session expiry


def _nearest_stop_distance(lat: float, lon: float, stops: List[Stop]) -> float:
    """Returns the distance in km to the nearest route stop."""
    if not stops:
        return 999.0
    return min(haversine_distance(lat, lon, s.latitude, s.longitude) for s in stops)


def validate_passenger_ping(
    lat: float,
    lon: float,
    accuracy_meters: Optional[float],
    speed_kmh: Optional[float],
    timestamp: datetime,
    stops: List[Stop],
) -> tuple[str, float]:
    """
    Validates a single passenger GPS ping.
    Returns (validation_status, confidence_score 0.0–1.0).
    """
    now = datetime.now(timezone.utc)
    ts  = timestamp if timestamp.tzinfo else timestamp.replace(tzinfo=timezone.utc)
    age = (now - ts).total_seconds()

    # 1. Stale ping
    if age > MAX_PING_AGE_SECONDS:
        return PingValidation.STALE.value, 0.0

    # 2. Poor GPS accuracy
    if accuracy_meters is not None and accuracy_meters > MAX_ACCURACY_METERS:
        return PingValidation.REJECTED.value, 0.0

    # 3. Impossible speed
    if speed_kmh is not None and speed_kmh > MAX_SPEED_KMH:
        return PingValidation.REJECTED.value, 0.0

    # 4. Location far outside route corridor
    nearest_km = _nearest_stop_distance(lat, lon, stops)
    if nearest_km > MAX_ROUTE_OFFSET_KM:
        return PingValidation.OUTLIER.value, 0.1

    # ── Compute confidence score ──────────────────────────────────────────────
    confidence = 1.0

    # Penalise by age (0 → 1.0, 90s → 0.1)
    confidence *= max(0.1, 1.0 - (age / MAX_PING_AGE_SECONDS) * 0.9)

    # Penalise by accuracy (0 m → 1.0, 150 m → 0.3)
    if accuracy_meters is not None:
        acc_factor = max(0.3, 1.0 - (accuracy_meters / MAX_ACCURACY_METERS) * 0.7)
        confidence *= acc_factor

    # Penalise by distance from route (0 km → 1.0, 2 km → 0.3)
    route_factor = max(0.3, 1.0 - (nearest_km / MAX_ROUTE_OFFSET_KM) * 0.7)
    confidence *= route_factor

    return PingValidation.VALID.value, round(confidence, 3)


def estimate_bus_position(trip: Trip, db: Session) -> Dict[str, Any]:
    """
    Determines the best available bus position and its source/confidence.

    Priority:
      1. Recent driver GPS          → DRIVER_GPS / HIGH
      2. Valid passenger pings      → PASSENGER_ASSISTED / MEDIUM or HIGH
      3. Schedule fallback          → SCHEDULE_ESTIMATE / LOW
      4. Nothing                    → UNKNOWN

    Returns a dict safe for public consumption (no passenger identity/exact location).
    """
    now = datetime.now(timezone.utc)
    result_base: Dict[str, Any] = {
        "trip_id":            trip.id,
        "bus_id":             trip.bus_id,
        "bus_number":         trip.bus.bus_number if trip.bus else "Unknown",
        "latitude":           None,
        "longitude":          None,
        "source":             "UNKNOWN",
        "confidence":         "UNKNOWN",
        "label":              "Unavailable",
        "contributor_count":  0,
        "driver_gps_age_sec": None,
        "computed_at":        now,
    }

    # ── 1. Driver GPS check ──────────────────────────────────────────────────
    driver_age_sec = None
    if trip.last_ping_time:
        lpt = trip.last_ping_time
        if lpt.tzinfo is None:
            lpt = lpt.replace(tzinfo=timezone.utc)
        driver_age_sec = int((now - lpt).total_seconds())

    driver_fresh = (
        driver_age_sec is not None
        and driver_age_sec <= DRIVER_GPS_STALE_SEC
        and trip.current_latitude  is not None
        and trip.current_longitude is not None
    )

    if driver_fresh:
        result_base.update({
            "latitude":          trip.current_latitude,
            "longitude":         trip.current_longitude,
            "source":            "DRIVER_GPS",
            "confidence":        "HIGH",
            "label":             "Live GPS",
            "driver_gps_age_sec": driver_age_sec,
        })
        # Annotate contributor count even when driver GPS is primary
        result_base["contributor_count"] = _count_active_contributors(trip.id, db)
        return result_base

    # ── 2. Passenger-assisted location ───────────────────────────────────────
    cutoff = now - timedelta(seconds=60)
    valid_pings: List[PassengerLocationPing] = (
        db.query(PassengerLocationPing)
        .filter(
            PassengerLocationPing.trip_id          == trip.id,
            PassengerLocationPing.timestamp        >= cutoff,
            PassengerLocationPing.validation_status == PingValidation.VALID.value,
        )
        .order_by(PassengerLocationPing.timestamp.desc())
        .all()
    )

    if valid_pings:
        # Deduplicate: one most-recent ping per session
        seen_sessions: set = set()
        unique_pings: List[PassengerLocationPing] = []
        for p in valid_pings:
            if p.session_id not in seen_sessions:
                seen_sessions.add(p.session_id)
                unique_pings.append(p)

        # Outlier filtering: median cluster if ≥ 3 pings
        est_lat, est_lon = _consensus_position(unique_pings)

        contributor_count = len(unique_pings)
        confidence = "MEDIUM" if contributor_count == 1 else "HIGH"

        # If driver GPS exists but is stale, blend and mark COMBINED
        source = "PASSENGER_ASSISTED"
        if (driver_age_sec is not None
                and driver_age_sec <= 120
                and trip.current_latitude is not None):
            # Weight: driver 0.3, passengers 0.7 (driver is stale but not ancient)
            weight_d = 0.3
            weight_p = 0.7
            est_lat = weight_d * trip.current_latitude  + weight_p * est_lat
            est_lon = weight_d * trip.current_longitude + weight_p * est_lon
            source = "COMBINED"
            confidence = "MEDIUM"

        result_base.update({
            "latitude":           round(est_lat, 6),
            "longitude":          round(est_lon, 6),
            "source":             source,
            "confidence":         confidence,
            "label":              "Passenger-assisted" if source == "PASSENGER_ASSISTED" else "Estimated (combined)",
            "contributor_count":  contributor_count,
            "driver_gps_age_sec": driver_age_sec,
        })
        return result_base

    # ── 3. Last known driver position (stale fallback) ───────────────────────
    if trip.current_latitude is not None:
        result_base.update({
            "latitude":           trip.current_latitude,
            "longitude":          trip.current_longitude,
            "source":             "SCHEDULE_ESTIMATE",
            "confidence":         "LOW",
            "label":              "Estimated (last known)",
            "driver_gps_age_sec": driver_age_sec,
        })
        return result_base

    return result_base


def _consensus_position(pings: List[PassengerLocationPing]) -> tuple[float, float]:
    """
    Weighted centroid of valid pings. With 3+ pings, applies outlier rejection
    (drops pings > 1 std-dev from mean position).
    """
    if len(pings) == 1:
        return pings[0].latitude, pings[0].longitude

    weights    = [p.confidence_score for p in pings]
    total_w    = sum(weights) or 1.0
    w_lat = sum(p.latitude  * w for p, w in zip(pings, weights)) / total_w
    w_lon = sum(p.longitude * w for p, w in zip(pings, weights)) / total_w

    if len(pings) < 3:
        return w_lat, w_lon

    # Outlier rejection using distance from weighted centroid
    dists = [haversine_distance(p.latitude, p.longitude, w_lat, w_lon) for p in pings]
    try:
        mean_d = statistics.mean(dists)
        std_d  = statistics.stdev(dists)
        threshold = mean_d + std_d
        filtered = [(p, w) for p, w, d in zip(pings, weights, dists) if d <= threshold]
        if filtered:
            pings_f, weights_f = zip(*filtered)
            total_wf = sum(weights_f) or 1.0
            w_lat = sum(p.latitude  * w for p, w in zip(pings_f, weights_f)) / total_wf
            w_lon = sum(p.longitude * w for p, w in zip(pings_f, weights_f)) / total_wf
    except statistics.StatisticsError:
        pass

    return w_lat, w_lon


def _count_active_contributors(trip_id: int, db: Session) -> int:
    """Anonymous count of passengers currently sharing location for this trip."""
    return (
        db.query(PassengerSession)
        .filter(
            PassengerSession.trip_id == trip_id,
            PassengerSession.status  == SessionStatus.ACTIVE.value,
        )
        .count()
    )


def expire_old_sessions(trip_id: int, db: Session) -> int:
    """
    Terminates all active passenger sessions for a given trip.
    Called when a trip is stopped or cancelled.
    Returns the number of sessions expired.
    """
    now = datetime.now(timezone.utc)
    sessions = (
        db.query(PassengerSession)
        .filter(
            PassengerSession.trip_id == trip_id,
            PassengerSession.status  == SessionStatus.ACTIVE.value,
        )
        .all()
    )
    for s in sessions:
        s.status   = SessionStatus.EXPIRED.value
        s.ended_at = now
    db.commit()
    return len(sessions)


def expire_timed_out_sessions(db: Session) -> int:
    """Global sweep: expire sessions past their hard expiry time."""
    now = datetime.now(timezone.utc)
    sessions = (
        db.query(PassengerSession)
        .filter(
            PassengerSession.status    == SessionStatus.ACTIVE.value,
            PassengerSession.expires_at <= now,
        )
        .all()
    )
    for s in sessions:
        s.status   = SessionStatus.EXPIRED.value
        s.ended_at = now
    db.commit()
    return len(sessions)
