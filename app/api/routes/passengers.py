from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.schemas.passenger import PassengerOut, PassengerCreate, PassengerUpdate
from app.services.passenger_service import PassengerService

router = APIRouter(prefix="/passengers", tags=["Passengers"])

def get_passenger_service(db: Session = Depends(get_db)) -> PassengerService:
    return PassengerService(db)

@router.get("", response_model=List[PassengerOut])
def list_passengers(
    search: Optional[str] = Query(None, description="Search by name, phone, or flight"),
    flight_id: Optional[str] = Query(None, description="Filter by flight ID"),
    skip: int = Query(0, ge=0),
    limit: Optional[int] = Query(None, ge=1, le=1000),
    service: PassengerService = Depends(get_passenger_service)
):
    """List passengers with optional non-breaking pagination and filtering."""
    return service.list_passengers(search=search, flight_id=flight_id, skip=skip, limit=limit)

@router.get("/{passenger_id}", response_model=PassengerOut)
def get_passenger(passenger_id: str, service: PassengerService = Depends(get_passenger_service)):
    p = service.get_passenger(passenger_id)
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Passenger not found")
    return p

@router.post("", response_model=PassengerOut, status_code=status.HTTP_201_CREATED)
def create_passenger(data: PassengerCreate, service: PassengerService = Depends(get_passenger_service)):
    p = service.create_passenger(data)
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found")
    return p

@router.put("/{passenger_id}", response_model=PassengerOut)
def update_passenger(passenger_id: str, data: PassengerUpdate, service: PassengerService = Depends(get_passenger_service)):
    p = service.update_passenger(passenger_id, data)
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Passenger not found")
    return p

@router.delete("/{passenger_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_passenger(passenger_id: str, service: PassengerService = Depends(get_passenger_service)):
    success = service.delete_passenger(passenger_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Passenger not found")
    return None

@router.post("/{passenger_id}/notify", status_code=status.HTTP_201_CREATED)
def notify_passenger(
    passenger_id: str, 
    payload: dict = {}, 
    service: PassengerService = Depends(get_passenger_service)
):
    msg = service.notify_passenger(passenger_id, payload)
    if not msg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Passenger or Flight not found")
    return {"success": True, "message": msg}
