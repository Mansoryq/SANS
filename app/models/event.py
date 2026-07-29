from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from app.db.base import Base

class Event(Base):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(50), unique=True, nullable=False, index=True)  # UUID
    flight_id = Column(String(20), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)  # DELAY, CANCEL, TIME_CHANGED, BOARDING, GATE_CHANGED, TERMINAL_CHANGED
    old_value = Column(String(255), nullable=True)
    new_value = Column(String(255), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    processed = Column(Boolean, default=False)
    processed_time = Column(DateTime, nullable=True)
