import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)

def test_verify_whatsapp_webhook_success(monkeypatch):
    monkeypatch.setattr(settings, "WHATSAPP_VERIFY_TOKEN", "sans_webhook_verify_2026")
    
    response = client.get(
        "/api/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "sans_webhook_verify_2026",
            "hub.challenge": "999999"
        }
    )
    
    assert response.status_code == 200
    assert response.text == "999999"

def test_verify_whatsapp_webhook_failure(monkeypatch):
    monkeypatch.setattr(settings, "WHATSAPP_VERIFY_TOKEN", "sans_webhook_verify_2026")
    
    response = client.get(
        "/api/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong_token",
            "hub.challenge": "999999"
        }
    )
    
    assert response.status_code == 403
    assert response.json() == {"detail": "Verification failed"}
