from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.route import Route, Stop
from app.models.user import User
from app.schemas.route import RouteCreate, RouteUpdate, RouteResponse
from app.api.deps import require_admin, get_current_user

router = APIRouter(prefix="/routes", tags=["Route Management"])

@router.get("", response_model=List[RouteResponse])
def list_routes(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Route).order_by(Route.route_code.asc()).all()

@router.get("/{route_id}", response_model=RouteResponse)
def get_route(route_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    route = db.query(Route).filter(Route.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    return route

@router.post("", response_model=RouteResponse, status_code=status.HTTP_201_CREATED)
def create_route(route_in: RouteCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    if db.query(Route).filter(Route.route_name == route_in.route_name).first():
        raise HTTPException(status_code=400, detail="Route name already exists")
    if db.query(Route).filter(Route.route_code == route_in.route_code).first():
        raise HTTPException(status_code=400, detail="Route code already exists")

    route = Route(
        route_name=route_in.route_name,
        route_code=route_in.route_code,
        description=route_in.description,
        is_active=route_in.is_active
    )
    db.add(route)
    db.flush()

    if route_in.stops:
        for s in route_in.stops:
            stop = Stop(
                route_id=route.id,
                stop_name=s.stop_name,
                sequence=s.sequence,
                latitude=s.latitude,
                longitude=s.longitude,
                scheduled_offset_minutes=s.scheduled_offset_minutes,
                is_active=s.is_active
            )
            db.add(stop)

    db.commit()
    db.refresh(route)
    return route

@router.patch("/{route_id}", response_model=RouteResponse)
def update_route(
    route_id: int,
    route_update: RouteUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    route = db.query(Route).filter(Route.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    if route_update.route_name and route_update.route_name != route.route_name:
        if db.query(Route).filter(Route.route_name == route_update.route_name).first():
            raise HTTPException(status_code=400, detail="Route name already in use")
        route.route_name = route_update.route_name

    if route_update.route_code and route_update.route_code != route.route_code:
        if db.query(Route).filter(Route.route_code == route_update.route_code).first():
            raise HTTPException(status_code=400, detail="Route code already in use")
        route.route_code = route_update.route_code

    if route_update.description is not None:
        route.description = route_update.description
    if route_update.is_active is not None:
        route.is_active = route_update.is_active

    db.commit()
    db.refresh(route)
    return route
