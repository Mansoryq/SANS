from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories.passenger_repository import PassengerRepository
from app.schemas.passenger import PassengerCreate, PassengerUpdate
from app.models.passenger import Passenger
from app.models.notification import Notification
from app.services.whatsapp import whatsapp_service

class PassengerService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = PassengerRepository(db)

    def list_passengers(self, search: Optional[str] = None, flight_id: Optional[str] = None, skip: int = 0, limit: Optional[int] = None) -> List[Passenger]:
        return self.repo.get_all_passengers(search=search, flight_id=flight_id, skip=skip, limit=limit)

    def get_passenger(self, passenger_id: str) -> Optional[Passenger]:
        return self.repo.get_passenger_by_id(passenger_id)

    def create_passenger(self, data: PassengerCreate) -> Optional[Passenger]:
        if not self.repo.check_flight_exists(data.flight_id):
            return None
        return self.repo.create_passenger(data)

    def update_passenger(self, passenger_id: str, data: PassengerUpdate) -> Optional[Passenger]:
        p = self.repo.get_passenger_by_id(passenger_id)
        if not p:
            return None
        return self.repo.update_passenger(p, data)

    def delete_passenger(self, passenger_id: str) -> bool:
        p = self.repo.get_passenger_by_id(passenger_id)
        if not p:
            return False
        self.repo.delete_passenger(p)
        return True

    def notify_passenger(self, passenger_id: str, payload: dict) -> Optional[str]:
        p = self.repo.get_passenger_by_id(passenger_id)
        if not p:
            return None
        
        f = self.repo.get_passenger_flight(p.flight_id)
        if not f:
            return None
            
        msg = payload.get("message") or whatsapp_service.build_message_text("ON_TIME", f, p)
        notif = Notification(
            passenger_id=p.passenger_id,
            flight_id=p.flight_id,
            phone_number=p.phone_number,
            message_text=msg,
            template_type="MANUAL",
            status="SIMULATED"
        )
        self.db.add(notif)
        self.db.commit()
        return msg
