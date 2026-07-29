import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import HTMLResponse

# Prometheus and OTEL
from prometheus_client import make_asgi_app
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from app.core.config import settings
from app.db.session import init_db, SessionLocal
from app.models.settings import AppSetting
from app.api.websockets import ws_manager

from app.core.logging.setup import setup_logging
from app.core.middleware import RequestIDMiddleware

# Import Routers
from app.api.routes.auth import router as auth_router
from app.api.routes.flights import router as flights_router
from app.api.routes.passengers import router as passengers_router
from app.api.routes.settings import router as settings_router
from app.api.routes.simulation import router as simulation_router
from app.api.routes.monitor import router as monitor_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.statistics import router as statistics_router

setup_logging()
logger = logging.getLogger("SANS")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB Schema
    logger.info("Initializing SANS Database schema...")
    init_db()

    # Seed Default App Settings
    db = SessionLocal()
    try:
        default_settings = [
            ('mode', 'prod'),
            ('poll_interval', '20'),
            ('flight_api_url', ''),
            ('flight_api_key', ''),
            ('passenger_api_url', ''),
            ('passenger_api_key', ''),
            ('wa_token', 'EAAMb1UMmobsBSIWSlQpNGa0SZAQstobkHfsI4KCKOTUGWRHojsKVrlX2OVwN3ZC0pZC1b7Yq0ylN5IhATZCBZAIoQ3KUNRG76cZCZCRs5LZCVOnwWAxbx7haABNcDVIZBdHsIQG7Cjor65pVsSUeXWpvgFOFzsAk4GhEtkTv882ZA5VrTciCTHVN9ekQSZBqYGv4SLkmiHap42wODiuio3l5XXgAY8HkmqEZB8jFNI8N2JS34ZAshvmH1giEK15OE23bNT2PXoZC6828fTQCBqqccfVkuPj0Kt8elSzYNF6gZDZD'),
            ('wa_phone_id', '1309636498890779'),
            ('meta_verify_token', 'sans-verify-token'),
            ('webhook_secret', ''),
            ('onec_api_url', ''),
            ('onec_login', ''),
            ('onec_password', ''),
        ]
        from app.core.encryption import encrypt_value
        for key, val in default_settings:
            if key in ['wa_token', 'flight_api_key', 'passenger_api_key'] and val:
                val = encrypt_value(val)
            existing = db.query(AppSetting).filter_by(key=key).first()
            if not existing:
                db.add(AppSetting(key=key, value=val))
            elif key in ['wa_token', 'wa_phone_id', 'mode']:
                # Update with the newly provided values if they already exist
                existing.value = val
        db.commit()
    except Exception as e:
        logger.error(f"Initialization error: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()

    yield
    logger.info("Shutting down SANS web service...")

import sentry_sdk

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=1.0,
        environment=os.getenv("ENVIRONMENT", "development"),
        release=f"{settings.PROJECT_NAME}@{settings.VERSION}",
    )
    logger.info("Sentry SDK initialized.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

# --- Middlewares ---
app.add_middleware(RequestIDMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    TrustedHostMiddleware, allowed_hosts=["*"]  # Set to specific domains in prod
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Instrumentation ---
FastAPIInstrumentor.instrument_app(app)

# --- Endpoints ---
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

from app.api.routes.webhooks import router as webhooks_router

# Register API Routers under /api
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(flights_router, prefix=settings.API_V1_STR)
app.include_router(passengers_router, prefix=settings.API_V1_STR)
app.include_router(settings_router, prefix=settings.API_V1_STR)
app.include_router(simulation_router, prefix=settings.API_V1_STR)
app.include_router(monitor_router, prefix=settings.API_V1_STR)
app.include_router(dashboard_router, prefix=settings.API_V1_STR)
app.include_router(statistics_router, prefix=settings.API_V1_STR)
app.include_router(webhooks_router, prefix=settings.API_V1_STR)

@app.get("/api/health", tags=["Monitoring"])
def health_check():
    return {"status": "healthy", "project": settings.PROJECT_NAME, "version": settings.VERSION}

@app.get("/api/ready", tags=["Monitoring"])
def readiness_check():
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Database not ready")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def serve_index():
    index_path = os.path.join("templates", "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>SANS Enterprise Application Ready</h1>"
