from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.base import Base

class Flight(Base):
    __tablename__ = 'flights'

    id = Column(Integer, primary_key=True, index=True)
    flight_id = Column(String(20), unique=True, nullable=False, index=True)
    airline = Column(String(100), nullable=False, default="SANS Airline")
    origin = Column(String(100), nullable=False)
    destination = Column(String(100), nullable=False)
    scheduled_departure = Column(DateTime, nullable=False)
    scheduled_arrival = Column(DateTime, nullable=False)
    actual_departure = Column(DateTime, nullable=True)
    actual_arrival = Column(DateTime, nullable=True)
    status = Column(String(50), nullable=False, default='ON_TIME')
    delay_minutes = Column(Integer, default=0)
    gate = Column(String(20), nullable=True)
    terminal = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    passengers = relationship("Passenger", back_populates="flight", cascade="all, delete-orphan")
    timeline_entries = relationship("FlightTimeline", back_populates="flight", cascade="all, delete-orphan", order_by="FlightTimeline.timestamp.desc()")


class FlightTimeline(Base):
    __tablename__ = 'flight_timelines'

    id = Column(Integer, primary_key=True, index=True)
    flight_id = Column(String(20), ForeignKey('flights.flight_id'), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    flight = relationship("Flight", back_populates="timeline_entries")
