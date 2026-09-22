from datetime import datetime, timedelta, timezone
import pandas as pd
from typing import List, Dict, Any, Optional

from app.models.trip import Trip
from app.models.route import Route, Stop
from app.ml.feature_engineering import haversine_distance, compute_ml_features, FEATURE_COLUMNS
from app.ml.train import load_trained_model

# Lazy load or cache model
_model_bundle = None

def get_model_bundle():
    global _model_bundle
    if _model_bundle is None:
        try:
            _model_bundle = load_trained_model()
        except Exception:
            _model_bundle = None
    return _model_bundle

def calculate_trip_stops_eta(
    trip: Trip,
    stops: List[Stop],
    current_lat: Optional[float],
    current_lon: Optional[float],
    current_speed_kmh: float = 0.0
) -> List[Dict[str, Any]]:
    """
    Computes ETAs for all stops in an active trip.
    Distinguishes clearly between:
    - Scheduled time
    - Calculated ETA (physics/heuristic)
    - ML-predicted ETA (trained regressor)
    - Status (PASSED, NEXT, UPCOMING, ARRIVED)
    """
    if not stops:
        return []

    # Sort stops by sequence
    ordered_stops = sorted(stops, key=lambda s: s.sequence)
    model_bundle = get_model_bundle()
    now = datetime.now(timezone.utc)
    trip_start = trip.start_time or now

    results = []
    
    # If no GPS coordinates yet, use first stop or default
    bus_lat = current_lat if current_lat is not None else ordered_stops[0].latitude
    bus_lon = current_lon if current_lon is not None else ordered_stops[0].longitude

    # Find the nearest stop and determine which stops are passed
    # A stop is considered "PASSED" if sequence < current_stop_sequence or bus is already past it
    # We find the stop with minimum distance or index
    distances_to_bus = [
        (s.sequence, haversine_distance(bus_lat, bus_lon, s.latitude, s.longitude))
        for s in ordered_stops
    ]
    
    # Active stop sequence estimation:
    # A stop within 0.15 km (150 meters) with low speed can be considered "ARRIVED" at that stop
    active_seq = trip.current_stop_sequence or 1

    # Check if bus has reached or passed stops
    for idx, stop in enumerate(ordered_stops):
        dist_to_this_stop = haversine_distance(bus_lat, bus_lon, stop.latitude, stop.longitude)
        
        # Determine status
        if stop.sequence < active_seq:
            status = "PASSED"
        elif stop.sequence == active_seq:
            if dist_to_this_stop <= 0.15:
                status = "ARRIVED"
            else:
                status = "NEXT"
        else:
            status = "UPCOMING"

        # Calculate remaining cumulative route distance from bus to this stop
        # If passed: 0 km
        if status == "PASSED":
            distance_remaining_km = 0.0
            calc_eta_min = 0.0
            ml_eta_min = 0.0
            final_eta_min = 0.0
        elif status == "ARRIVED":
            distance_remaining_km = round(dist_to_this_stop, 2)
            calc_eta_min = 0.0
            ml_eta_min = 0.0
            final_eta_min = 0.0
        else:
            # Bus to next stop, then sum of inter-stop distances up to this stop
            # 1. Bus to stop idx:
            # Approximation: distance to next stop + sum of distances between subsequent stops
            next_stop = next((s for s in ordered_stops if s.sequence >= active_seq), ordered_stops[-1])
            dist_bus_to_next = haversine_distance(bus_lat, bus_lon, next_stop.latitude, next_stop.longitude)
            
            inter_stops_dist = 0.0
            for i in range(next_stop.sequence - 1, stop.sequence - 1):
                if i + 1 < len(ordered_stops):
                    s1 = ordered_stops[i]
                    s2 = ordered_stops[i + 1]
                    inter_stops_dist += haversine_distance(s1.latitude, s1.longitude, s2.latitude, s2.longitude)
            
            distance_remaining_km = round(dist_bus_to_next + inter_stops_dist, 2)
            stops_remaining = max(1, stop.sequence - active_seq + 1)
            
            # Scheduled travel time relative to trip start or offset
            scheduled_travel_min = max(0, stop.scheduled_offset_minutes)

            # Heuristic calculation:
            effective_speed = max(current_speed_kmh, 20.0) if current_speed_kmh > 0 else 25.0
            calc_eta_min = round((distance_remaining_km / effective_speed) * 60.0 + (stops_remaining * 1.0), 1)

            # ML prediction
            ml_eta_min = None
            if model_bundle and "model" in model_bundle:
                try:
                    feat_dict = compute_ml_features(
                        distance_km=distance_remaining_km,
                        speed_kmh=current_speed_kmh,
                        stop_count_remaining=stops_remaining,
                        scheduled_travel_min=scheduled_travel_min,
                        current_time=datetime.now()
                    )
                    X_df = pd.DataFrame([feat_dict])[FEATURE_COLUMNS]
                    pred = model_bundle["model"].predict(X_df)[0]
                    ml_eta_min = round(max(0.5, float(pred)), 1)
                except Exception:
                    ml_eta_min = None

            final_eta_min = ml_eta_min if ml_eta_min is not None else calc_eta_min

        # Scheduled arrival timestamp calculation
        scheduled_arrival = (trip_start + timedelta(minutes=stop.scheduled_offset_minutes)).strftime("%I:%M %p")
        eta_timestamp = now + timedelta(minutes=final_eta_min) if final_eta_min > 0 else now

        results.append({
            "stop_id": stop.id,
            "stop_name": stop.stop_name,
            "sequence": stop.sequence,
            "latitude": stop.latitude,
            "longitude": stop.longitude,
            "scheduled_arrival_time": scheduled_arrival,
            "calculated_eta_minutes": calc_eta_min,
            "ml_predicted_eta_minutes": ml_eta_min,
            "final_eta_minutes": final_eta_min,
            "eta_timestamp": eta_timestamp,
            "distance_remaining_km": distance_remaining_km,
            "status": status
        })

    return results
