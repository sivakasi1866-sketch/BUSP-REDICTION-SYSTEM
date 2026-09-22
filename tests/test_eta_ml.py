from datetime import datetime
from app.ml.feature_engineering import haversine_distance, compute_ml_features, FEATURE_COLUMNS
from app.ml.train import train_and_evaluate_model, load_trained_model
from app.services.eta_service import calculate_trip_stops_eta
from app.models.trip import Trip
from app.models.route import Stop

def test_haversine_distance():
    # Kovilpatti to nearby junction (~1.5 to 2.5 km)
    dist = haversine_distance(9.1724, 77.8765, 9.1758, 77.8722)
    assert 0.4 < dist < 1.5

def test_ml_feature_engineering_extracts_all_required_features():
    features = compute_ml_features(
        distance_km=12.5,
        speed_kmh=32.0,
        stop_count_remaining=4,
        scheduled_travel_min=25.0,
        current_time=datetime(2026, 9, 22, 8, 30) # peak morning
    )

    for col in FEATURE_COLUMNS:
        assert col in features, f"Missing feature {col}"

    assert features["is_peak_hour"] == 1
    assert features["distance_km"] == 12.5
    assert features["stop_count_remaining"] == 4
    assert "log_distance" in features

def test_ml_model_evaluation_metrics():
    model_bundle = load_trained_model()
    assert "model" in model_bundle
    assert "metrics" in model_bundle
    metrics = model_bundle["metrics"]

    # Verify metric keys
    assert "mae" in metrics
    assert "rmse" in metrics
    assert "r2" in metrics
    # Metrics must be non-negative and valid floats
    assert metrics["mae"] > 0
    assert metrics["rmse"] > 0
    assert metrics["r2"] > 0

def test_eta_service_distinguishes_timings(db_session):
    trip = db_session.query(Trip).first()
    stops = db_session.query(Stop).order_by(Stop.sequence.asc()).all()

    etas = calculate_trip_stops_eta(
        trip=trip,
        stops=stops,
        current_lat=stops[0].latitude,
        current_lon=stops[0].longitude,
        current_speed_kmh=30.0
    )

    assert len(etas) == len(stops)
    for s_eta in etas:
        # Check required fields
        assert "scheduled_arrival_time" in s_eta
        assert "calculated_eta_minutes" in s_eta
        assert "ml_predicted_eta_minutes" in s_eta
        assert "final_eta_minutes" in s_eta
        assert "status" in s_eta
