import time
import httpx
import random
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class PassengerAPIConnector:
    """
    Passenger API Client: Synchronizes passengers per flight.
    Detects new passengers, phone changes, language changes.
    """
    def __init__(self):
        self.last_sync: str = "Never"
        self.response_time_ms: int = 0
        self.status: str = "Unknown"
        self.last_error: str = ""

    def get_passengers_for_flight(self, flight_id: str, api_url: str, api_key: str, mode: str = "mock") -> List[Dict[str, Any]]:
        start_t = time.time()
        if mode == "mock" or not api_url:
            self.status = "Connected"
            self.response_time_ms = int((time.time() - start_t) * 1000)
            self.last_sync = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            return self._generate_demo_passengers(flight_id)

        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(f"{api_url}?flight={flight_id}", headers={"Authorization": f"Bearer {api_key}"})
                self.response_time_ms = int((time.time() - start_t) * 1000)
                self.last_sync = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                if resp.status_code == 200:
                    self.status = "Connected"
                    self.last_error = ""
                    return resp.json()
                else:
                    self.status = "Disconnected"
                    self.last_error = f"HTTP {resp.status_code}"
                    return []
        except Exception as e:
            self.response_time_ms = int((time.time() - start_t) * 1000)
            self.last_sync = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            self.status = "Disconnected"
            self.last_error = str(e)
            logger.error(f"[PassengerAPIConnector] Error: {e}")
            return []

    def _generate_demo_passengers(self, flight_id: str) -> List[Dict[str, Any]]:
        names = [
            ("Алихан", "Сейткали"), ("Гульнара", "Ахметова"), ("Данияр", "Бекова"),
            ("Айгерим", "Нурланова"), ("Серик", "Касымов"), ("Зарина", "Джаксыбекова"),
            ("Нурлан", "Токтаров"), ("Мадина", "Сулейменова"), ("Азамат", "Ержанов"),
            ("Диана", "Курбанова"), ("Берик", "Абенов"), ("Камила", "Мусина")
        ]
        results = []
        for i, (fn, ln) in enumerate(names[:10]):
            pid = f"P{hash(flight_id + fn) & 0xFFFFFF:06X}"
            
            # Map specific phone numbers to the first two passengers for testing
            if i == 0:
                phone_number = "77763348996"
            elif i == 1:
                phone_number = "77763367314"
            else:
                phone_number = f"7701{1000000 + (hash(pid) % 8999999)}"
                
            results.append({
                "passenger_id": pid,
                "first_name": fn,
                "last_name": ln,
                "phone_number": phone_number,
                "flight_id": flight_id,
                "seat_number": f"{i+1}{random.choice('ABCDEF')}",
                "booking_reference": f"REF{i+100}",
                "ticket_number": f"TKT-99{i+10}",
                "preferred_language": random.choice(["ru", "kk", "en"])
            })
        return results

passenger_api_client = PassengerAPIConnector()
