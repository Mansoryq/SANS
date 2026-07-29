from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.settings import AppSetting
from app.services.flight_api import flight_api_client
from app.services.passenger_api import passenger_api_client
from app.services.whatsapp import whatsapp_service
from app.services.onec import onec_client

router = APIRouter(prefix="/monitor", tags=["API Monitor"])

@router.get("")
def get_api_monitor_status(db: Session = Depends(get_db)):
    mode = AppSetting.get(db, 'mode', 'mock')
    
    apis = {
        "flight_api": {
            "name": "Flight API",
            "status": flight_api_client.status if mode == "real" else "Connected",
            "response_time_ms": flight_api_client.response_time_ms if mode == "real" else 45,
            "last_sync": flight_api_client.last_sync,
            "http_code": 200 if (mode == "mock" or flight_api_client.status == "Connected") else 500,
            "error_message": flight_api_client.last_error if mode == "real" else None
        },
        "passenger_api": {
            "name": "Passenger API",
            "status": passenger_api_client.status if mode == "real" else "Connected",
            "response_time_ms": passenger_api_client.response_time_ms if mode == "real" else 38,
            "last_sync": passenger_api_client.last_sync,
            "http_code": 200 if (mode == "mock" or passenger_api_client.status == "Connected") else 500,
            "error_message": passenger_api_client.last_error if mode == "real" else None
        },
        "whatsapp_api": {
            "name": "WhatsApp Cloud API",
            "status": whatsapp_service.status if mode == "real" else "Connected",
            "response_time_ms": whatsapp_service.response_time_ms if mode == "real" else 62,
            "last_sync": whatsapp_service.last_sync,
            "http_code": 200 if (mode == "mock" or whatsapp_service.status == "Connected") else 500,
            "error_message": whatsapp_service.last_error if mode == "real" else None
        },
        "onec_api": {
            "name": "1C Enterprise API",
            "status": onec_client.status if mode == "real" else "Connected",
            "response_time_ms": onec_client.response_time_ms if mode == "real" else 85,
            "last_sync": onec_client.last_sync,
            "http_code": 200 if (mode == "mock" or onec_client.status == "Connected") else 500,
            "error_message": onec_client.last_error if mode == "real" else None
        }
    }
    return apis
