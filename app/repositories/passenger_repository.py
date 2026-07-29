import uuid
from typing import List, Optional
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.models.passenger import Passenger
from app.models.flight import Flight
from app.schemas.passenger import PassengerCreate, PassengerUpdate

class PassengerRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all_passengers(self, search: Optional[str] = None, flight_id: Optional[str] = None, skip: int = 0, limit: Optional[int] = None) -> List[Passenger]:
        q = self.db.query(Passenger)
        if flight_id:
            q = q.filter(Passenger.flight_id == flight_id)
        if search:
            q = q.filter(or_(
                Passenger.last_name.ilike(f"%{search}%"),
                Passenger.first_name.ilike(f"%{search}%"),
                Passenger.phone_number.ilike(f"%{search}%"),
                Passenger.flight_id.ilike(f"%{search}%")
            ))
            
        q = q.order_by(Passenger.last_name)
        if skip:
            q = q.offset(skip)
        if limit:
            q = q.limit(limit)
            
        return q.all()

    def get_passenger_by_id(self, passenger_id: str) -> Optional[Passenger]:
        return self.db.query(Passenger).filter(Passenger.passenger_id == passenger_id).first()

    def check_flight_exists(self, flight_id: str) -> bool:
        return self.db.query(Flight).filter(Flight.flight_id == flight_id).first() is not None
        
    def get_passenger_flight(self, flight_id: str) -> Optional[Flight]:
        return self.db.query(Flight).filter(Flight.flight_id == flight_id).first()

    def create_passenger(self, data: PassengerCreate) -> Passenger:
        p = Passenger(
            passenger_id=f"P{uuid.uuid4().hex[:8].upper()}",
            **data.model_dump(exclude={"passenger_id"})
        )
        self.db.add(p)
        self.db.commit()
        self.db.refresh(p)
        return p

    def update_passenger(self, passenger: Passenger, data: PassengerUpdate) -> Passenger:
        for field, val in data.model_dump(exclude_unset=True).items():
            setattr(passenger, field, val)
        self.db.commit()
        self.db.refresh(passenger)
        return passenger

    def delete_passenger(self, passenger: Passenger) -> None:
        self.db.delete(passenger)
        self.db.commit()
