import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.db.base import Base

connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}

# Production Connection Pooling Defaults
pool_size = int(os.getenv("DB_POOL_SIZE", "10"))
max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "20"))
pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "1800")) # 30 mins
pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))

engine_kwargs = {
    "pool_pre_ping": True,
    "echo": False,
    "connect_args": connect_args
}

if "sqlite" not in settings.DATABASE_URL:
    engine_kwargs.update({
        "pool_size": pool_size,
        "max_overflow": max_overflow,
        "pool_recycle": pool_recycle,
        "pool_timeout": pool_timeout
    })

engine = create_engine(settings.DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
