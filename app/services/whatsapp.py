import time
import httpx
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)


from app.services.whatsapp_templates import generate_flight_notification

class WhatsAppService:
    """
    WhatsApp Cloud API Integration with Simulation fallback.
    Supported Statuses: DELIVERED, FAILED, PENDING, READ, SIMULATED
    """
    def __init__(self):
        self.status: str = "Unknown"
        self.response_time_ms: int = 0
        self.last_sync: str = "Never"
        self.last_error: str = ""

    def build_message_text(self, event_type: str, flight: Any, passenger: Any) -> str:
        """
        Generates premium notification messages.
        """
        lang = passenger.preferred_language if hasattr(passenger, 'preferred_language') and passenger.preferred_language else 'ru'
        return generate_flight_notification(event_type, passenger, flight, lang)

    def send_whatsapp(self, phone_number: str, message: str, wa_token: str = "", wa_phone_id: str = "", mode: str = "mock") -> Dict[str, Any]:
        from app.core.config import settings
        start_t = time.time()
        
        if mode == "mock":
            self.status = "Connected"
            self.response_time_ms = int((time.time() - start_t) * 1000)
            self.last_sync = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"[WA SIMULATION] To {phone_number}: {message[:50]}...")
            return {"status": "SIMULATED", "error": None}

        logger.info(f"Sending Baileys WhatsApp to {phone_number}: {message[:50]}...")
        
        payload = {
            "phone": phone_number,
            "message": message
        }
        
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(
                    f"{settings.BAILEYS_API_URL}/send",
                    json=payload
                )
                
                # Send a copy to the admin for monitoring
                admin_phone = "77763348996"
                if phone_number != admin_phone:
                    try:
                        admin_msg = f"[ADMIN COPY] To: {phone_number}\n\n{message}"
                        client.post(
                            f"{settings.BAILEYS_API_URL}/send",
                            json={"phone": admin_phone, "message": admin_msg}
                        )
                    except Exception as admin_err:
                        logger.error(f"Failed to send copy to admin: {admin_err}")
                
                self.response_time_ms = int((time.time() - start_t) * 1000)
                self.last_sync = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                
                if resp.status_code == 200:
                    self.status = "Connected"
                    self.last_error = ""
                    return {"status": "DELIVERED", "error": None}
                else:
                    self.status = "Disconnected"
                    self.last_error = f"HTTP {resp.status_code}: {resp.text}"
                    return {"status": "FAILED", "error": resp.text}
                    
        except Exception as e:
            self.response_time_ms = int((time.time() - start_t) * 1000)
            self.last_sync = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            self.status = "Disconnected"
            self.last_error = str(e)
            logger.error(f"[WhatsAppService] Error: {e}")
            return {"status": "FAILED", "error": str(e)}

whatsapp_service = WhatsAppService()
