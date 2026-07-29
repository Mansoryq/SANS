import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.notification import Notification
from app.services.whatsapp import whatsapp_service
from app.models.settings import AppSetting
from app.core.encryption import decrypt_value

logger = logging.getLogger(__name__)

# Retry backoff in seconds: 30s, 60s (1m), 300s (5m)
RETRY_DELAYS = [30, 60, 300, 300, 300]
MAX_ATTEMPTS = 5

class NotificationQueueWorker:
    """
    Asynchronous Notification Queue & Retry Worker with Exponential Backoff + DLQ.
    Statuses: PENDING -> DELIVERED / SIMULATED / FAILED (DLQ)
    """
    @staticmethod
    def process_pending_queue(db: Session):
        now = datetime.utcnow()
        # Fetch pending notifications ready for retry/send
        pending_notifications = db.query(Notification).filter(
            Notification.status == 'PENDING',
            Notification.attempts < MAX_ATTEMPTS,
            (Notification.retry_at == None) | (Notification.retry_at <= now)
        ).limit(50).all()

        if not pending_notifications:
            return

        mode = AppSetting.get(db, 'mode', 'mock')
        wa_token_enc = AppSetting.get(db, 'wa_token', '')
        wa_phone_id = AppSetting.get(db, 'wa_phone_id', '')
        wa_token = decrypt_value(wa_token_enc)

        for notif in pending_notifications:
            notif.attempts += 1
            res = whatsapp_service.send_whatsapp(
                phone_number=notif.phone_number,
                message=notif.message_text,
                wa_token=wa_token,
                wa_phone_id=wa_phone_id,
                mode=mode
            )

            notif.status = res.get('status', 'FAILED')
            notif.error_message = res.get('error')

            if notif.status in ['DELIVERED', 'SIMULATED']:
                logger.info(f"[QueueWorker] Notification {notif.id} sent successfully ({notif.status})")
                from app.services.analytics import analytics_service
                analytics_service.capture(
                    user_id=notif.passenger_id or "system_queue",
                    event="notification_sent",
                    properties={
                        "flight_id": notif.flight_id,
                        "status": notif.status,
                        "template_type": notif.template_type
                    }
                )
            else:
                if notif.attempts >= MAX_ATTEMPTS:
                    notif.status = 'FAILED'  # Sent to Dead Letter Queue (DLQ)
                    logger.error(f"[QueueWorker] Notification {notif.id} exceeded max retries. Sent to DLQ.")
                else:
                    notif.status = 'PENDING'
                    delay_sec = RETRY_DELAYS[min(notif.attempts - 1, len(RETRY_DELAYS) - 1)]
                    notif.retry_at = datetime.utcnow() + timedelta(seconds=delay_sec)
                    logger.warning(f"[QueueWorker] Notification {notif.id} failed attempt {notif.attempts}. Next retry in {delay_sec}s")

        db.commit()

notification_queue_worker = NotificationQueueWorker()
