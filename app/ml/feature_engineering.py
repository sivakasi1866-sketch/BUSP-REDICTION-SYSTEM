import math
from datetime import datetime

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in kilometers between two geo coordinates using Haversine formula."""
    R = 6371.0  # Earth's radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2.0) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 3)

def compute_ml_features(
    distance_km: float,
    speed_kmh: float,
    stop_count_remaining: int,
    scheduled_travel_min: float,
    current_time: datetime | None = None
) -> dict:
    """
    Extract the 11 key ML features required by the project specifications:
    - distance_km
    - speed_kmh
    - stop_count_remaining
    - scheduled_travel_min
    - theoretical_minutes
    - time_sin
    - time_cos
    - day_sin
    - day_cos
    - is_peak_hour
    - log_distance
    """
    if current_time is None:
        current_time = datetime.now()

    # Effective speed heuristic to avoid division by zero
    effective_speed = max(speed_kmh, 15.0) if speed_kmh > 0 else 25.0
    theoretical_minutes = (distance_km / effective_speed) * 60.0 + (stop_count_remaining * 1.0)

    # Time cyclic features
    hour_float = current_time.hour + current_time.minute / 60.0
    time_sin = math.sin(2 * math.pi * hour_float / 24.0)
    time_cos = math.cos(2 * math.pi * hour_float / 24.0)

    # Day cyclic features (0 = Monday, 6 = Sunday)
    day_of_week = current_time.weekday()
    day_sin = math.sin(2 * math.pi * day_of_week / 7.0)
    day_cos = math.cos(2 * math.pi * day_of_week / 7.0)

    # Peak hour: Morning (07:30 to 09:30) or Evening (16:00 to 18:30)
    is_morning_peak = 7.5 <= hour_float <= 9.5
    is_evening_peak = 16.0 <= hour_float <= 18.5
    is_peak_hour = 1 if (is_morning_peak or is_evening_peak) and day_of_week < 6 else 0

    log_distance = math.log1p(max(0.0, distance_km))

    return {
        "distance_km": round(distance_km, 3),
        "speed_kmh": round(speed_kmh, 2),
        "stop_count_remaining": stop_count_remaining,
        "scheduled_travel_min": round(scheduled_travel_min, 2),
        "theoretical_minutes": round(theoretical_minutes, 2),
        "time_sin": round(time_sin, 4),
        "time_cos": round(time_cos, 4),
        "day_sin": round(day_sin, 4),
        "day_cos": round(day_cos, 4),
        "is_peak_hour": is_peak_hour,
        "log_distance": round(log_distance, 4)
    }

FEATURE_COLUMNS = [
    "distance_km",
    "speed_kmh",
    "stop_count_remaining",
    "scheduled_travel_min",
    "theoretical_minutes",
    "time_sin",
    "time_cos",
    "day_sin",
    "day_cos",
    "is_peak_hour",
    "log_distance"
]
