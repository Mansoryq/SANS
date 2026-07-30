import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Smart Airport Notification System (SANS)"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api"
    ENVIRONMENT: str = "production"
    
    # Database
    DATABASE_URL: str = "sqlite:///./sans.db"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE: int = 1800
    DB_POOL_TIMEOUT: int = 30
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security
    SECRET_KEY: str = "sans-enterprise-secret-key-32bytes-long!"
    ENCRYPTION_KEY: str = "uH8-Xl0r2-j-9K1r_yv_P9M9M9M9M9M9M9M9M9M9M9M="
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Polling & Worker
    DEFAULT_POLL_INTERVAL: int = 20
    MAX_NOTIFICATION_RETRIES: int = 5

    # Observability & Analytics
    SENTRY_DSN: str | None = None
    POSTHOG_API_KEY: str | None = None
    POSTHOG_HOST: str = "https://eu.i.posthog.com"
    ANALYTICS_ENABLED: bool = True
    
    # WhatsApp
    WHATSAPP_VERIFY_TOKEN: str = "kamo2008"
    BAILEYS_API_URL: str = "http://whatsapp-baileys:3000"
    
    # Supabase (Storage)
    SUPABASE_URL: str | None = None
    SUPABASE_KEY: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
