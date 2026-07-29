import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, Query, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.settings import AppSetting
from app.services.analytics import analytics_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

from fastapi.responses import PlainTextResponse
from app.core.config import settings

@router.get("/whatsapp")
def verify_whatsapp_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Webhook verification endpoint for WhatsApp Business API.
    Meta will send a GET request here when you configure the webhook URL.
    """
    
    # Extract query parameters
    verify_token = request.query_params.get("hub.verify_token", "")
    challenge = request.query_params.get("hub.challenge", "")
    mode = request.query_params.get("hub.mode", "")
    
    # Priority 1: Database
    # Priority 2: Environment variable / settings
    db_token = AppSetting.get(db, 'meta_verify_token', None)
    expected_token = db_token if db_token else settings.WHATSAPP_VERIFY_TOKEN
    
    logger.info(
        f"WhatsApp webhook verification | mode={mode} | "
        f"received_token={verify_token[:5] + '***' if verify_token else 'None'} | "
        f"expected_token={expected_token[:5] + '***' if expected_token else 'None'}"
    )
    
    if mode == "subscribe" and verify_token == expected_token:
        logger.info("WhatsApp webhook verified successfully.")
        return PlainTextResponse(content=str(challenge), status_code=200)
    
    logger.warning("Webhook verification failed. Token mismatch.")
    raise HTTPException(status_code=403, detail="Verification failed")

@router.post("/whatsapp")
async def receive_whatsapp_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Receive incoming messages and status updates from WhatsApp.
    """
    try:
        payload = await request.json()
        logger.debug(f"Received WhatsApp Webhook: {payload}")
        
        # Track webhook received in PostHog
        analytics_service.capture(
            user_id="system_webhook",
            event="whatsapp_webhook_received",
            properties={"payload_object": payload.get("object")}
        )

        if payload.get("object") == "whatsapp_business_account":
            for entry in payload.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    
                    # 1. Handle Message Status Updates (Sent, Delivered, Read, Failed)
                    if "statuses" in value:
                        for status in value["statuses"]:
                            msg_id = status.get("id")
                            msg_status = status.get("status")
                            recipient = status.get("recipient_id")
                            
                            logger.info(f"WhatsApp Message {msg_id} status updated to {msg_status} for {recipient}")
                            
                            # Analytics tracking
                            analytics_service.capture(
                                user_id="system_webhook",
                                event="whatsapp_message_status_update",
                                properties={
                                    "message_id": msg_id,
                                    "status": msg_status,
                                    "recipient_id": recipient
                                }
                            )
                            
                    # 2. Handle Incoming Messages (User replies)
                    if "messages" in value:
                        for message in value["messages"]:
                            msg_from = message.get("from")
                            msg_id = message.get("id")
                            msg_type = message.get("type")
                            
                            text_body = message.get("text", {}).get("body", "") if msg_type == "text" else f"Received {msg_type}"
                            
                            logger.info(f"Incoming WhatsApp message from {msg_from}: {text_body}")
                            
                            # Analytics tracking
                            analytics_service.capture(
                                user_id="system_webhook",
                                event="whatsapp_message_received",
                                properties={
                                    "message_id": msg_id,
                                    "from": msg_from,
                                    "type": msg_type
                                }
                            )

        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Error processing WhatsApp Webhook: {e}", exc_info=True)
        # Always return 200 to Meta to prevent retries on processing errors, unless it's a critical parsing issue.
        return {"status": "error", "message": str(e)}
