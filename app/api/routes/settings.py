from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.settings import AppSetting
from app.schemas.settings import SettingsUpdate
from app.core.encryption import encrypt_value, decrypt_value
from app.services.flight_api import flight_api_client
from app.services.passenger_api import passenger_api_client
from app.services.whatsapp import whatsapp_service
from app.services.onec import onec_client

router = APIRouter(prefix="/settings", tags=["Settings"])

ENCRYPTED_KEYS = {'flight_api_key', 'passenger_api_key', 'wa_token', 'webhook_secret', 'onec_password'}

@router.get("")
def get_settings(db: Session = Depends(get_db)):
    settings_items = db.query(AppSetting).all()
    res = {}
    for s in settings_items:
        val = decrypt_value(s.value) if s.is_encrypted else s.value
        res[s.key] = val

    # Defaults
    res.setdefault("mode", "mock")
    res.setdefault("poll_interval", "20")
    return res

@router.put("")
def update_settings(data: SettingsUpdate, db: Session = Depends(get_db)):
    for key, val in data.model_dump(exclude_unset=True).items():
        if val is None:
            continue
        is_enc = key in ENCRYPTED_KEYS
        stored_val = encrypt_value(str(val)) if is_enc else str(val)

        setting = db.query(AppSetting).filter_by(key=key).first()
        if setting:
            setting.value = stored_val
            setting.is_encrypted = is_enc
        else:
            db.add(AppSetting(key=key, value=stored_val, is_encrypted=is_enc))
    db.commit()
    return {"success": True, "message": "Configuration saved securely."}

@router.post("/test-connection")
def test_connection(db: Session = Depends(get_db)):
    mode = AppSetting.get(db, 'mode', 'mock')
    flight_url = AppSetting.get(db, 'flight_api_url', '')
    flight_key = decrypt_value(AppSetting.get(db, 'flight_api_key', ''))
    
    passenger_url = AppSetting.get(db, 'passenger_api_url', '')
    passenger_key = decrypt_value(AppSetting.get(db, 'passenger_api_key', ''))
    
    wa_token = decrypt_value(AppSetting.get(db, 'wa_token', ''))
    wa_phone_id = AppSetting.get(db, 'wa_phone_id', '')

    onec_url = AppSetting.get(db, 'onec_api_url', '')
    onec_login = AppSetting.get(db, 'onec_login', '')
    onec_pass = decrypt_value(AppSetting.get(db, 'onec_password', ''))

    # Run connection tests
    flight_api_client.get_flights(flight_url, flight_key, mode=mode)
    passenger_api_client.get_passengers_for_flight('KC721', passenger_url, passenger_key, mode=mode)
    whatsapp_service.send_whatsapp('+77011234567', 'Test Ping', wa_token, wa_phone_id, mode=mode)
    onec_client.send_statistics({'test': True}, onec_url, onec_login, onec_pass, mode=mode)

    return {
        "flight_api": flight_api_client.status,
        "passenger_api": passenger_api_client.status,
        "whatsapp_api": whatsapp_service.status,
        "onec_api": onec_client.status,
    }
