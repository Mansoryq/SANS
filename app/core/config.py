import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Smart Airport Notification System (SANS)"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sans.db")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "sans-enterprise-secret-key-32bytes-long!")
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "uH8-Xl0r2-j-9K1r_yv_P9M9M9M9M9M9M9M9M9M9M9M=")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Polling & Worker
    DEFAULT_POLL_INTERVAL: int = 20
    MAX_NOTIFICATION_RETRIES: int = 5

    # Observability & Analytics
    SENTRY_DSN: str | None = os.getenv("SENTRY_DSN", None)
    POSTHOG_API_KEY: str | None = os.getenv("POSTHOG_API_KEY", None)
    POSTHOG_HOST: str = os.getenv("POSTHOG_HOST", "https://eu.i.posthog.com")
    ANALYTICS_ENABLED: bool = os.getenv("ANALYTICS_ENABLED", "True").lower() in ("true", "1", "yes")
    
    # Supabase (Storage)
    SUPABASE_URL: str | None = os.getenv("SUPABASE_URL", None)
    SUPABASE_KEY: str | None = os.getenv("SUPABASE_KEY", None)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
