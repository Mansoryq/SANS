from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories.flight_repository import FlightRepository
from app.schemas.flight import FlightCreate, FlightUpdate
from app.models.flight import Flight
from app.services.event_engine import event_engine_service
from app.core.cache import cache_response, invalidate_cache

class FlightService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = FlightRepository(db)

    @cache_response(ttl_seconds=30)
    def list_flights(self, status: Optional[str] = None, airline: Optional[str] = None, skip: int = 0, limit: Optional[int] = None) -> List[Flight]:
        # TODO: Implement Redis caching here for expensive read operations
        return self.repo.get_all_flights(status=status, airline=airline, skip=skip, limit=limit)

    def get_flight(self, flight_id: str) -> Optional[Flight]:
        return self.repo.get_flight_by_id(flight_id)

    def create_flight(self, data: FlightCreate) -> Optional[Flight]:
        if self.repo.get_internal_flight(data.flight_id):
            return None
        flight = self.repo.create_flight(data)
        invalidate_cache("list_flights")
        return flight

    def update_flight(self, flight_id: str, data: FlightUpdate) -> Optional[Flight]:
        flight = self.repo.get_internal_flight(flight_id)
        if not flight:
            return None

        old_status = flight.status
        old_gate = flight.gate
        old_terminal = flight.terminal

        updated_flight = self.repo.update_flight(flight, data)

        # Trigger events based on changes (Business Logic moved from Router to Service)
        if old_status != updated_flight.status:
            event_engine_service.create_and_process_event(self.db, updated_flight, updated_flight.status, old_status, updated_flight.status)
        elif old_gate != updated_flight.gate and updated_flight.gate:
            event_engine_service.create_and_process_event(self.db, updated_flight, "GATE_CHANGED", old_gate or "", updated_flight.gate)
        elif old_terminal != updated_flight.terminal and updated_flight.terminal:
            event_engine_service.create_and_process_event(self.db, updated_flight, "TERMINAL_CHANGED", old_terminal or "", updated_flight.terminal)

        invalidate_cache("list_flights")
        return updated_flight

    def delete_flight(self, flight_id: str) -> bool:
        flight = self.repo.get_internal_flight(flight_id)
        if not flight:
            return False
        self.repo.delete_flight(flight)
        invalidate_cache("list_flights")
        return True
