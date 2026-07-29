from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from app.db.base import Base

class Notification(Base):
    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True, index=True)
    passenger_id = Column(String(50), nullable=False, index=True)
    flight_id = Column(String(20), nullable=False, index=True)
    event_id = Column(String(50), nullable=True, index=True)
    phone_number = Column(String(30), nullable=False)
    message_text = Column(Text, nullable=False)
    template_type = Column(String(50), nullable=False, default='STATUS_CHANGE')
    status = Column(String(20), nullable=False, default='PENDING', index=True)  # PENDING, DELIVERED, FAILED, SIMULATED, READ
    attempts = Column(Integer, default=0)
    retry_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime, default=datetime.utcnow, index=True)
