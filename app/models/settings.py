from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from app.db.base import Base

class AppSetting(Base):
    __tablename__ = 'settings'

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    is_encrypted = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get(cls, db, key: str, default: str = None) -> str:
        setting = db.query(cls).filter_by(key=key).first()
        return setting.value if setting and setting.value is not None else default
