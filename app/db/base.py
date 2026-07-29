try:
    from sqlalchemy.orm import DeclarativeBase
    class Base(DeclarativeBase):
        pass
except ImportError:
    from sqlalchemy.ext.declarative import declarative_base
    Base = declarative_base()

# Import all models here for Alembic autogenerate support
from app.models.user import User
from app.models.flight import Flight, FlightTimeline
from app.models.passenger import Passenger
from app.models.event import Event
from app.models.notification import Notification
from app.models.settings import AppSetting
from app.models.log import AuditLog
