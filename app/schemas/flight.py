from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class FlightBase(BaseModel):
    flight_id: str
    airline: str = "SANS Airline"
    origin: str
    destination: str
    scheduled_departure: datetime
    scheduled_arrival: datetime
    actual_departure: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None
    status: str = "ON_TIME"
    delay_minutes: int = 0
    gate: Optional[str] = None
    terminal: Optional[str] = None

class FlightCreate(FlightBase):
    pass

class FlightUpdate(BaseModel):
    airline: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    scheduled_departure: Optional[datetime] = None
    scheduled_arrival: Optional[datetime] = None
    actual_departure: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None
    status: Optional[str] = None
    delay_minutes: Optional[int] = None
    gate: Optional[str] = None
    terminal: Optional[str] = None

class TimelineItem(BaseModel):
    event_type: str
    description: str
    timestamp: datetime

    class Config:
        from_attributes = True

class FlightOut(FlightBase):
    id: int
    created_at: datetime
    updated_at: datetime
    passenger_count: int = 0
    timeline: List[TimelineItem] = []

    class Config:
        from_attributes = True
