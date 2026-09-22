from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.buses import router as buses_router
from app.api.routes import router as routes_router
from app.api.stops import router as stops_router
from app.api.assignments import router as assignments_router
from app.api.trips import router as trips_router
from app.api.tracking import router as tracking_router
from app.api.notifications import router as notifications_router
from app.api.reports import router as reports_router
from app.api.imports import router as imports_router
from app.api.passenger_location import router as passenger_location_router

api_router = APIRouter(prefix="/api")
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(buses_router)
api_router.include_router(routes_router)
api_router.include_router(stops_router)
api_router.include_router(assignments_router)
api_router.include_router(trips_router)
api_router.include_router(tracking_router)
api_router.include_router(notifications_router)
api_router.include_router(reports_router)
api_router.include_router(imports_router)
api_router.include_router(passenger_location_router)
