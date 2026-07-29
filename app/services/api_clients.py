import httpx
import uuid
from datetime import datetime, timedelta
import random
import logging

logger = logging.getLogger(__name__)

class FlightAPIClient:
    async def get_flights(self, api_url: str, api_key: str, mode: str):
        if mode == "mock":
            return self._generate_mock_flights()
        
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(api_url, headers={"Authorization": f"Bearer {api_key}"})
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                logger.error(f"Flight API Error: {e}")
                return []

    def _generate_mock_flights(self):
        # Fake data logic
        now = datetime.utcnow()
        return [
            {
                "flight_number": "KC721",
                "origin": "Turkistan",
                "destination": "Almaty",
                "departure_time": (now + timedelta(hours=1)).isoformat(),
                "arrival_time": (now + timedelta(hours=2, minutes=30)).isoformat(),
                "gate": "A3",
                "terminal": "1",
                "status": "ON_TIME",
                "updated_time": now.isoformat()
            },
            {
                "flight_number": "DV701",
                "origin": "Turkistan",
                "destination": "Shymkent",
                "departure_time": (now + timedelta(hours=3)).isoformat(),
                "arrival_time": (now + timedelta(hours=3, minutes=45)).isoformat(),
                "gate": "B5",
                "terminal": "1",
                "status": "DELAYED",
                "updated_time": now.isoformat()
            }
        ]

class PassengerAPIClient:
    async def get_passengers(self, flight_id: str, api_url: str, api_key: str, mode: str):
        if mode == "mock":
            return self._generate_mock_passengers(flight_id)
        
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(f"{api_url}?flight={flight_id}", headers={"Authorization": f"Bearer {api_key}"})
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                logger.error(f"Passenger API Error: {e}")
                return []

    def _generate_mock_passengers(self, flight_id: str):
        langs = ["ru", "kk", "en"]
        passengers = []
        for i in range(5):
            pid = f"P{uuid.uuid4().hex[:8].upper()}"
            passengers.append({
                "flight_number": flight_id,
                "passenger_id": pid,
                "full_name": f"Test Passenger {i}",
                "phone_number": f"+7701{random.randint(1000000, 9999999)}",
                "preferred_language": random.choice(langs),
                "ticket_number": f"TKT-{random.randint(1000,9999)}"
            })
        return passengers

class WhatsAppClient:
    async def send_message(self, phone: str, template: str, params: list, token: str, phone_id: str, mode: str):
        if mode == "mock":
            logger.info(f"[SIMULATED WA] To {phone}: {template} {params}")
            return {"success": True, "status": "SIMULATED", "message_id": str(uuid.uuid4())}
        
        url = f"https://graph.facebook.com/v17.0/{phone_id}/messages"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "template",
            "template": {
                "name": template,
                "language": {"code": "ru"},
                "components": [{"type": "body", "parameters": params}]
            }
        }
        
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                return {"success": True, "status": "SENT", "message_id": resp.json().get("messages", [{}])[0].get("id")}
            except Exception as e:
                logger.error(f"WhatsApp API Error: {e}")
                return {"success": False, "status": "FAILED", "error": str(e)}

class OneCAPIClient:
    async def send_statistics(self, stats: dict, api_url: str, user: str, password: str, mode: str):
        if mode == "mock":
            logger.info(f"[SIMULATED 1C] Stats sent: {stats}")
            return True
        
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(api_url, json=stats, auth=(user, password))
                resp.raise_for_status()
                return True
            except Exception as e:
                logger.error(f"1C API Error: {e}")
                return False
