from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PassengerBase(BaseModel):
    passenger_id: str
    first_name: str
    last_name: str = ""
    phone_number: str
    email: Optional[str] = None
    flight_id: str
    seat_number: Optional[str] = None
    booking_reference: str = "N/A"
    ticket_number: Optional[str] = None
    preferred_language: str = "ru"

class PassengerCreate(PassengerBase):
    passenger_id: Optional[str] = None

class PassengerUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    flight_id: Optional[str] = None
    seat_number: Optional[str] = None
    booking_reference: Optional[str] = None
    ticket_number: Optional[str] = None
    preferred_language: Optional[str] = None

class PassengerOut(PassengerBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
