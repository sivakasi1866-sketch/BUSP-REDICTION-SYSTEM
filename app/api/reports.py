from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

from app.database import get_db
from app.models.trip import Trip, TripStatus, GPSPing
from app.models.bus import Bus
from app.models.route import Route, Stop
from app.models.user import User, UserRole
from app.api.deps import require_admin
from app.ml.train import load_trained_model

router = APIRouter(prefix="/reports", tags=["Reports & Analytics"])

@router.get("/dashboard-summary")
def get_dashboard_summary(db: Session = Depends(get_db), _: User = Depends(require_admin)) -> Dict[str, Any]:
    """Admin dashboard summary metrics."""
    total_buses = db.query(Bus).count()
    active_buses = db.query(Bus).filter(Bus.is_active == True).count()
    inactive_buses = total_buses - active_buses

    active_trips_count = db.query(Trip).filter(Trip.status == TripStatus.ACTIVE.value).count()
    completed_trips_count = db.query(Trip).filter(Trip.status == TripStatus.COMPLETED.value).count()
    total_trips_count = db.query(Trip).count()

    total_drivers = db.query(User).filter(User.role == UserRole.DRIVER.value, User.is_active == True).count()
    total_students = db.query(User).filter(User.role == UserRole.STUDENT.value, User.is_active == True).count()
    total_staff = db.query(User).filter(User.role == UserRole.STAFF.value, User.is_active == True).count()
    total_routes = db.query(Route).filter(Route.is_active == True).count()
    total_stops = db.query(Stop).filter(Stop.is_active == True).count()

    # Recent trips
    recent_trips = db.query(Trip).order_by(Trip.id.desc()).limit(5).all()
    recent_trips_summary = [
        {
            "id": t.id,
            "trip_name": t.trip_name,
            "bus_number": t.bus.bus_number if t.bus else "N/A",
            "route_name": t.route.route_name if t.route else "N/A",
            "driver_name": t.driver.full_name if t.driver else "N/A",
            "status": t.status,
            "start_time": t.start_time.strftime("%I:%M %p") if t.start_time else "—",
            "end_time": t.end_time.strftime("%I:%M %p") if t.end_time else "—"
        }
        for t in recent_trips
    ]

    return {
        "fleet": {
            "total_buses": total_buses,
            "active_buses": active_buses,
            "inactive_buses": inactive_buses,
            "buses_on_trip": db.query(Bus).filter(Bus.status == "ON_TRIP").count(),
            "buses_idle": db.query(Bus).filter(Bus.status == "IDLE", Bus.is_active == True).count()
        },
        "trips": {
            "active": active_trips_count,
            "completed": completed_trips_count,
            "total": total_trips_count
        },
        "users": {
            "drivers": total_drivers,
            "students": total_students,
            "staff": total_staff,
            "total_passengers": total_students + total_staff
        },
        "infrastructure": {
            "routes": total_routes,
            "stops": total_stops
        },
        "recent_trips": recent_trips_summary
    }

@router.get("/eta-model-metrics")
def get_eta_model_metrics(_: User = Depends(require_admin)) -> Dict[str, Any]:
    """Returns Machine Learning ETA evaluation performance against historical baseline."""
    bundle = load_trained_model()
    metrics = bundle.get("metrics", {})
    return {
        "model_type": "Gradient Boosting Regressor",
        "features": bundle.get("features", []),
        "evaluation": metrics,
        "historical_baseline": {
            "mae": 4.72,
            "rmse": 5.88,
            "r2": 0.2980
        },
        "comparison": {
            "mae_status": "Outperforming baseline" if metrics.get("mae", 99) < 4.72 else "At baseline",
            "rmse_status": "Outperforming baseline" if metrics.get("rmse", 99) < 5.88 else "At baseline",
            "r2_status": "Higher explanatory power" if metrics.get("r2", 0) > 0.2980 else "At baseline"
        }
    }
