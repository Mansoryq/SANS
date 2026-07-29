from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.schemas.flight import FlightOut, FlightCreate, FlightUpdate
from app.services.flight_service import FlightService

router = APIRouter(prefix="/flights", tags=["Flights"])

def get_flight_service(db: Session = Depends(get_db)) -> FlightService:
    return FlightService(db)

@router.get("", response_model=List[FlightOut])
def list_flights(
    status: Optional[str] = Query(None, description="Filter by flight status"),
    airline: Optional[str] = Query(None, description="Filter by airline name"),
    skip: int = Query(0, ge=0, description="Pagination skip"),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Pagination limit"),
    service: FlightService = Depends(get_flight_service)
):
    """
    Get all flights. By default returns all flights to maintain backward compatibility.
    Pagination can be optionally triggered via skip/limit query parameters.
    """
    flights = service.list_flights(status=status, airline=airline, skip=skip, limit=limit)
    return [FlightOut.model_validate(f) for f in flights]

@router.get("/{flight_id}", response_model=FlightOut)
def get_flight(flight_id: str, service: FlightService = Depends(get_flight_service)):
    f = service.get_flight(flight_id)
    if not f:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found")
    return FlightOut.model_validate(f)

@router.post("", status_code=status.HTTP_201_CREATED)
def create_flight(data: FlightCreate, service: FlightService = Depends(get_flight_service)):
    f = service.create_flight(data)
    if not f:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Flight already exists")
    return {"success": True, "flight_id": f.flight_id}

@router.put("/{flight_id}")
def update_flight(flight_id: str, data: FlightUpdate, service: FlightService = Depends(get_flight_service)):
    f = service.update_flight(flight_id, data)
    if not f:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found")
    return {"success": True, "flight_id": flight_id}

@router.delete("/{flight_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_flight(flight_id: str, service: FlightService = Depends(get_flight_service)):
    success = service.delete_flight(flight_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flight not found")
    return None
