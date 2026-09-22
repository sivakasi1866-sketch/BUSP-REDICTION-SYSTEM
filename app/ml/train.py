import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
import joblib

from app.ml.feature_engineering import compute_ml_features, FEATURE_COLUMNS

MODEL_PATH = os.path.join(os.path.dirname(__file__), "eta_model.joblib")

def generate_synthetic_training_data(n_samples: int = 5000, random_state: int = 42) -> pd.DataFrame:
    """
    Generate synthetic trip telemetry dataset clearly identified as synthetic.
    Simulates real-world traffic variations, peak hour slowdowns, and stop dwell times.
    """
    random.seed(random_state)
    np.random.seed(random_state)

    records = []
    base_date = datetime(2026, 1, 1, 6, 0)

    for i in range(n_samples):
        # Sample realistic route parameters
        total_route_distance = random.uniform(5.0, 35.0) # km
        progress_ratio = random.uniform(0.05, 0.95)
        distance_remaining = total_route_distance * (1 - progress_ratio)
        
        stops_remaining = max(1, int(round(distance_remaining / random.uniform(1.2, 2.5))))
        scheduled_travel_min = (distance_remaining / 30.0) * 60.0 + (stops_remaining * 1.5)

        # Random timestamp across college operating days (Mon-Sat, 6:30 to 19:00)
        day_offset = random.randint(0, 120)
        hour = random.choice([7, 8, 9, 15, 16, 17, 18]) + random.uniform(0, 0.9)
        sample_time = base_date + timedelta(days=day_offset, hours=hour)

        # Instantaneous speed (0 to 60 km/h with traffic conditions)
        is_peak = (7.5 <= hour <= 9.5) or (16.0 <= hour <= 18.5)
        base_speed = random.uniform(18.0, 35.0) if is_peak else random.uniform(30.0, 50.0)
        # Add random stop/slowdown noise
        speed_kmh = max(0.0, base_speed + np.random.normal(0, 6.0))

        features = compute_ml_features(
            distance_km=distance_remaining,
            speed_kmh=speed_kmh,
            stop_count_remaining=stops_remaining,
            scheduled_travel_min=scheduled_travel_min,
            current_time=sample_time
        )

        # Ground truth actual arrival duration with realistic physical noise
        # Traffic delay factor
        traffic_multiplier = 1.35 if is_peak else 1.05
        dwell_time_per_stop = random.uniform(0.75, 1.75) # minutes
        cruising_minutes = (distance_remaining / max(base_speed, 15.0)) * 60.0 * traffic_multiplier
        noise = np.random.normal(0, 1.2)
        
        actual_eta_minutes = max(0.5, cruising_minutes + (stops_remaining * dwell_time_per_stop) + noise)
        features["actual_eta_minutes"] = round(actual_eta_minutes, 2)
        features["is_synthetic"] = True

        records.append(features)

    df = pd.DataFrame(records)
    return df

def train_and_evaluate_model(save_model: bool = True) -> dict:
    """
    Train Gradient Boosting Regressor on engineered features,
    evaluate against baseline (MAE ~4.72, RMSE ~5.88, R2 ~0.2980),
    and serialize to disk.
    """
    df = generate_synthetic_training_data(n_samples=6000, random_state=42)

    X = df[FEATURE_COLUMNS]
    y = df["actual_eta_minutes"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = GradientBoostingRegressor(
        n_estimators=120,
        learning_rate=0.08,
        max_depth=5,
        random_state=42
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    mae = float(mean_absolute_error(y_test, y_pred))
    rmse = float(root_mean_squared_error(y_test, y_pred))
    r2 = float(r2_score(y_test, y_pred))

    metrics = {
        "dataset_type": "SYNTHETIC (clearly identified as per Project Section 23)",
        "samples_count": len(df),
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "r2": round(r2, 4),
        "baseline_mae": 4.72,
        "baseline_rmse": 5.88,
        "baseline_r2": 0.2980,
        "improved_over_baseline": (mae < 4.72 and rmse < 5.88 and r2 > 0.2980),
        "trained_at": datetime.now().isoformat()
    }

    if save_model:
        joblib.dump({"model": model, "metrics": metrics, "features": FEATURE_COLUMNS}, MODEL_PATH)

    return metrics

def load_trained_model():
    """Load cached model artifact or train if not present."""
    if os.path.exists(MODEL_PATH):
        try:
            return joblib.load(MODEL_PATH)
        except Exception:
            pass
    train_and_evaluate_model(save_model=True)
    return joblib.load(MODEL_PATH)

if __name__ == "__main__":
    results = train_and_evaluate_model(save_model=True)
    print("Training Results:", results)
