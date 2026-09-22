from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.bus import Bus
from app.models.user import User, UserRole
from app.schemas.bus import BusCreate, BusUpdate, BusResponse
from app.api.deps import require_admin, get_current_user

router = APIRouter(prefix="/buses", tags=["Bus Management"])

@router.get("", response_model=List[BusResponse])
def list_buses(
    is_active: Optional[bool] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user)
):
    query = db.query(Bus)
    if is_active is not None:
        query = query.filter(Bus.is_active == is_active)
    if status:
        query = query.filter(Bus.status == status.upper())
    return query.order_by(Bus.bus_number.asc()).all()

@router.get("/{bus_id}", response_model=BusResponse)
def get_bus_details(bus_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    bus = db.query(Bus).filter(Bus.id == bus_id).first()
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")
    return bus

@router.post("", response_model=BusResponse, status_code=status.HTTP_201_CREATED)
def create_bus(bus_in: BusCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    # Check uniqueness of bus_number and registration_number
    if db.query(Bus).filter(Bus.bus_number == bus_in.bus_number).first():
        raise HTTPException(status_code=400, detail=f"Bus with identifier '{bus_in.bus_number}' already exists")
    if db.query(Bus).filter(Bus.registration_number == bus_in.registration_number).first():
        raise HTTPException(status_code=400, detail=f"Bus with registration '{bus_in.registration_number}' already exists")

    bus = Bus(
        bus_number=bus_in.bus_number,
        registration_number=bus_in.registration_number,
        capacity=bus_in.capacity,
        is_active=bus_in.is_active,
        status=bus_in.status.upper() if bus_in.status else "IDLE",
        current_driver_id=bus_in.current_driver_id,
        default_route_id=bus_in.default_route_id
    )
    db.add(bus)
    db.commit()
    db.refresh(bus)
    return bus

@router.patch("/{bus_id}", response_model=BusResponse)
def update_bus(
    bus_id: int,
    bus_update: BusUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    bus = db.query(Bus).filter(Bus.id == bus_id).first()
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")

    if bus_update.bus_number and bus_update.bus_number != bus.bus_number:
        if db.query(Bus).filter(Bus.bus_number == bus_update.bus_number).first():
            raise HTTPException(status_code=400, detail="Bus number already in use")
        bus.bus_number = bus_update.bus_number

    if bus_update.registration_number and bus_update.registration_number != bus.registration_number:
        if db.query(Bus).filter(Bus.registration_number == bus_update.registration_number).first():
            raise HTTPException(status_code=400, detail="Registration number already in use")
        bus.registration_number = bus_update.registration_number

    if bus_update.capacity is not None:
        bus.capacity = bus_update.capacity
    if bus_update.is_active is not None:
        bus.is_active = bus_update.is_active
    if bus_update.status is not None:
        bus.status = bus_update.status.upper()
    if bus_update.current_driver_id is not None:
        bus.current_driver_id = bus_update.current_driver_id
    if bus_update.default_route_id is not None:
        bus.default_route_id = bus_update.default_route_id

    db.commit()
    db.refresh(bus)
    return bus

@router.delete("/{bus_id}")
def deactivate_bus(bus_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    bus = db.query(Bus).filter(Bus.id == bus_id).first()
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")
    bus.is_active = False
    bus.status = "INACTIVE"
    db.commit()
    return {"detail": f"Bus {bus.bus_number} marked inactive"}
