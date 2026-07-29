from typing import List, Optional, Tuple
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload
from app.models.flight import Flight, FlightTimeline
from app.models.passenger import Passenger
from app.schemas.flight import FlightCreate, FlightUpdate

class FlightRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all_flights(self, status: Optional[str] = None, airline: Optional[str] = None, skip: int = 0, limit: Optional[int] = None) -> List[Flight]:
        """
        Get all flights with their timeline entries (eagerly loaded) and passenger counts (aggregated).
        Eliminates N+1 queries.
        """
        subq = self.db.query(
            Passenger.flight_id, 
            func.count(Passenger.id).label("p_count")
        ).group_by(Passenger.flight_id).subquery()
        
        q = self.db.query(Flight, func.coalesce(subq.c.p_count, 0).label('passenger_count'))
        q = q.outerjoin(subq, Flight.flight_id == subq.c.flight_id)
        q = q.options(selectinload(Flight.timeline_entries))
        
        if status:
            q = q.filter(Flight.status == status)
        if airline:
            q = q.filter(Flight.airline == airline)
            
        q = q.order_by(Flight.scheduled_departure)
        
        if skip:
            q = q.offset(skip)
        if limit:
            q = q.limit(limit)
            
        results = q.all()
        
        out_flights = []
        for flight, p_count in results:
            flight.passenger_count = p_count
            out_flights.append(flight)
            
        return out_flights

    def get_flight_by_id(self, flight_id: str) -> Optional[Flight]:
        """Get a single flight by its string flight_id with passenger count."""
        subq = self.db.query(
            Passenger.flight_id, 
            func.count(Passenger.id).label("p_count")
        ).filter(Passenger.flight_id == flight_id).group_by(Passenger.flight_id).subquery()
        
        q = self.db.query(Flight, func.coalesce(subq.c.p_count, 0).label('passenger_count'))
        q = q.outerjoin(subq, Flight.flight_id == subq.c.flight_id)
        q = q.options(selectinload(Flight.timeline_entries))
        q = q.filter(Flight.flight_id == flight_id)
        
        result = q.first()
        if not result:
            return None
            
        flight, p_count = result
        flight.passenger_count = p_count
        return flight

    def get_internal_flight(self, flight_id: str) -> Optional[Flight]:
        """Get a flight without passenger counts, just the DB model."""
        return self.db.query(Flight).filter(Flight.flight_id == flight_id).first()

    def create_flight(self, data: FlightCreate) -> Flight:
        flight = Flight(**data.model_dump())
        self.db.add(flight)
        self.db.flush()
        
        tl = FlightTimeline(
            flight_id=flight.flight_id, 
            event_type="CREATED", 
            description=f"Flight {flight.flight_id} created."
        )
        self.db.add(tl)
        self.db.commit()
        return flight

    def update_flight(self, flight: Flight, data: FlightUpdate) -> Flight:
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(flight, field, value)
            
        self.db.commit()
        self.db.refresh(flight)
        return flight

    def delete_flight(self, flight: Flight) -> None:
        self.db.delete(flight)
        self.db.commit()
