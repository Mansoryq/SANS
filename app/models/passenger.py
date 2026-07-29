from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class Passenger(Base):
    __tablename__ = 'passengers'

    id = Column(Integer, primary_key=True, index=True)
    passenger_id = Column(String(50), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False, default='')
    phone_number = Column(String(30), nullable=False, index=True)
    email = Column(String(200), nullable=True)
    flight_id = Column(String(20), ForeignKey('flights.flight_id'), nullable=False, index=True)
    seat_number = Column(String(10), nullable=True)
    booking_reference = Column(String(20), nullable=False, default='N/A')
    ticket_number = Column(String(50), nullable=True)
    preferred_language = Column(String(10), default='ru')
    created_at = Column(DateTime, default=datetime.utcnow)

    flight = relationship("Flight", back_populates="passengers")
