from pydantic import BaseModel
from typing import Optional

class SettingsUpdate(BaseModel):
    mode: Optional[str] = None
    poll_interval: Optional[str] = None
    flight_api_url: Optional[str] = None
    flight_api_key: Optional[str] = None
    passenger_api_url: Optional[str] = None
    passenger_api_key: Optional[str] = None
    wa_token: Optional[str] = None
    wa_phone_id: Optional[str] = None
    meta_verify_token: Optional[str] = None
    webhook_secret: Optional[str] = None
    onec_api_url: Optional[str] = None
    onec_login: Optional[str] = None
    onec_password: Optional[str] = None
