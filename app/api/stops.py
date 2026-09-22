from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.route import Route, Stop
from app.models.user import User
from app.schemas.route import StopCreate, StopUpdate, StopResponse
from app.api.deps import require_admin, get_current_user

router = APIRouter(prefix="/stops", tags=["Stop Management"])

@router.get("/route/{route_id}", response_model=List[StopResponse])
def list_stops_for_route(route_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Stop).filter(Stop.route_id == route_id).order_by(Stop.sequence.asc()).all()

@router.post("", response_model=StopResponse, status_code=status.HTTP_201_CREATED)
def create_stop(stop_in: StopCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    if not stop_in.route_id:
        raise HTTPException(status_code=400, detail="route_id is required to create a stop")

    route = db.query(Route).filter(Route.id == stop_in.route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    stop = Stop(
        route_id=stop_in.route_id,
        stop_name=stop_in.stop_name,
        sequence=stop_in.sequence,
        latitude=stop_in.latitude,
        longitude=stop_in.longitude,
        scheduled_offset_minutes=stop_in.scheduled_offset_minutes,
        is_active=stop_in.is_active
    )
    db.add(stop)
    db.commit()
    db.refresh(stop)
    return stop

@router.patch("/{stop_id}", response_model=StopResponse)
def update_stop(
    stop_id: int,
    stop_update: StopUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    stop = db.query(Stop).filter(Stop.id == stop_id).first()
    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found")

    if stop_update.stop_name is not None:
        stop.stop_name = stop_update.stop_name
    if stop_update.sequence is not None:
        stop.sequence = stop_update.sequence
    if stop_update.latitude is not None:
        stop.latitude = stop_update.latitude
    if stop_update.longitude is not None:
        stop.longitude = stop_update.longitude
    if stop_update.scheduled_offset_minutes is not None:
        stop.scheduled_offset_minutes = stop_update.scheduled_offset_minutes
    if stop_update.is_active is not None:
        stop.is_active = stop_update.is_active

    db.commit()
    db.refresh(stop)
    return stop

@router.delete("/{stop_id}")
def delete_stop(stop_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    stop = db.query(Stop).filter(Stop.id == stop_id).first()
    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found")
    db.delete(stop)
    db.commit()
    return {"detail": "Stop deleted successfully"}
