from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from app.db.base import Base

class AuditLog(Base):
    __tablename__ = 'logs'

    id = Column(Integer, primary_key=True, index=True)
    action_type = Column(String(100), nullable=False, index=True)  # Auth, APIRequest, FlightChange, ConfigChange, Error
    flight_id = Column(String(20), nullable=True, index=True)
    passenger_id = Column(String(50), nullable=True)
    phone_number = Column(String(30), nullable=True)
    details = Column(Text, nullable=True)
    status = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
