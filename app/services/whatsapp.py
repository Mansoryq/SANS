import time
import httpx
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

TEMPLATES = {
    'ru': {
        'DELAYED': "Уважаемый {name}!\nРейс {flight} из {origin} в {dest} задержан.\nНовое время вылета: {time}.\nГейт: {gate}\nАэропорт Туркестан.",
        'CANCELLED': "Уважаемый {name}!\nРейс {flight} из {origin} в {dest} ОТМЕНЁН.\nПожалуйста, обратитесь к представителям авиакомпании.\nАэропорт Туркестан.",
        'GATE_CHANGED': "Уважаемый {name}!\nВнимание! Рейс {flight}.\nПосадка теперь осуществляется у гейта {gate}.\nАэропорт Туркестан.",
        'BOARDING': "Уважаемый {name}!\nРейс {flight} из {origin} в {dest}.\nПосадка началась! Пожалуйста, пройдите к гейту {gate}.\nАэропорт Туркестан.",
        'BOARDING_CLOSED': "Уважаемый {name}!\nПосадка на рейс {flight} закрыта.\nАэропорт Туркестан.",
        'TIME_CHANGED': "Уважаемый {name}!\nВремя вылета рейса {flight} изменено на {time}.\nАэропорт Туркестан.",
        'TERMINAL_CHANGED': "Уважаемый {name}!\nТерминал рейса {flight} изменён на {terminal}.\nАэропорт Туркестан.",
        'ON_TIME': "Уважаемый {name}!\nРейс {flight} вылетает по расписанию.\nГейт: {gate}. Аэропорт Туркестан.",
    },
    'kk': {
        'DELAYED': "Құрметті {name}!\n{flight} рейсі {origin} - {dest} бағытында кешіктірілді.\nЖаңа ұшу уақыты: {time}.\nГейт: {gate}. Түркістан әуежайы.",
        'CANCELLED': "Құрметті {name}!\n{flight} рейсі БОЛДЫРЫЛМАДЫ.\nАвиакомпания өкілдеріне хабарласыңыз.\nТүркістан әуежайы.",
        'GATE_CHANGED': "Құрметті {name}!\nНазар аударыңыз! {flight} рейсіне отыру {gate} гейтінен жүргізіледі.\nТүркістан әуежайы.",
        'BOARDING': "Құрметті {name}!\n{flight} рейсіне отыру басталды!\n{gate} гейтіне өтіңіз. Түркістан әуежайы.",
        'BOARDING_CLOSED': "Құрметті {name}!\n{flight} рейсіне отыру жабылды.\nТүркістан әуежайы.",
        'TIME_CHANGED': "Құрметті {name}!\n{flight} рейсінің ұшу уақыты {time} болып өзгертілді.\nТүркістан әуежайы.",
        'TERMINAL_CHANGED': "Құрметті {name}!\n{flight} рейсінің терминалы {terminal} болып өзгерді.\nТүркістан әуежайы.",
        'ON_TIME': "Құрметті {name}!\n{flight} рейсі кестеде ұшады.\nГейт: {gate}. Түркістан әуежайы.",
    },
    'en': {
        'DELAYED': "Dear {name}!\nFlight {flight} from {origin} to {dest} is DELAYED.\nNew departure time: {time}.\nGate: {gate}. Turkestan Airport.",
        'CANCELLED': "Dear {name}!\nFlight {flight} from {origin} to {dest} has been CANCELLED.\nPlease contact the airline staff.\nTurkestan Airport.",
        'GATE_CHANGED': "Dear {name}!\nAttention! Flight {flight} boarding is now at Gate {gate}.\nTurkestan Airport.",
        'BOARDING': "Dear {name}!\nFlight {flight} from {origin} to {dest} is now boarding.\nPlease proceed to Gate {gate}. Turkestan Airport.",
        'BOARDING_CLOSED': "Dear {name}!\nBoarding for flight {flight} is now closed.\nTurkestan Airport.",
        'TIME_CHANGED': "Dear {name}!\nDeparture time for flight {flight} changed to {time}.\nTurkestan Airport.",
        'TERMINAL_CHANGED': "Dear {name}!\nTerminal for flight {flight} changed to {terminal}.\nTurkestan Airport.",
        'ON_TIME': "Dear {name}!\nFlight {flight} is on time.\nGate: {gate}. Turkestan Airport.",
    }
}

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
        Since we use Baileys, we don't need Meta templates anymore.
        We can just send normal text messages!
        """
        # Pick language
        lang = passenger.language if hasattr(passenger, 'language') and passenger.language else 'ru'
        if lang not in TEMPLATES:
            lang = 'ru'
            
        template = TEMPLATES[lang].get(event_type)
        if not template:
            return ""
            
        # Format template
        try:
            return template.format(
                name=passenger.name if hasattr(passenger, 'name') else "Пассажир",
                flight=flight.flight_number if hasattr(flight, 'flight_number') else "",
                origin=flight.origin if hasattr(flight, 'origin') else "",
                dest=flight.destination if hasattr(flight, 'destination') else "",
                time=flight.scheduled_departure.strftime("%H:%M") if hasattr(flight, 'scheduled_departure') else "",
                gate=flight.gate if hasattr(flight, 'gate') and flight.gate else "TBD",
                terminal=flight.terminal if hasattr(flight, 'terminal') and flight.terminal else "TBD"
            )
        except KeyError as e:
            logger.error(f"Template formatting error: missing {e}")
            return template

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
