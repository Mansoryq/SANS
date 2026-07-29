from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.models.flight import Flight
from app.models.passenger import Passenger
from app.models.event import Event
from app.models.notification import Notification
from app.models.settings import AppSetting
from app.services.flight_api import flight_api_client
from app.services.whatsapp import whatsapp_service

router = APIRouter(tags=["Dashboard"])

@router.get("/dashboard")
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_flights = db.query(Flight).count()
    active_flights = db.query(Flight).filter(Flight.status.in_(['ON_TIME', 'DELAYED', 'BOARDING', 'DEPARTED'])).count()
    delayed_flights = db.query(Flight).filter_by(status='DELAYED').count()
    cancelled_flights = db.query(Flight).filter_by(status='CANCELLED').count()
    
    total_passengers = db.query(Passenger).count()
    total_notifications = db.query(Notification).count()
    failed_notifications = db.query(Notification).filter_by(status='FAILED').count()
    queue_size = db.query(Notification).filter_by(status='PENDING').count()

    recent_events = db.query(Event).order_by(Event.timestamp.desc()).limit(10).all()
    avg_response_time = (flight_api_client.response_time_ms + whatsapp_service.response_time_ms) // 2 or 50

    return {
        "total_flights": total_flights,
        "active_flights": active_flights,
        "delayed_flights": delayed_flights,
        "cancelled_flights": cancelled_flights,
        "total_passengers": total_passengers,
        "total_notifications": total_notifications,
        "failed_notifications": failed_notifications,
        "queue_size": queue_size,
        "avg_response_time_ms": avg_response_time,
        "api_health": "Healthy",
        "recent_changes": [
            {
                "id": e.id,
                "change_id": e.event_id,
                "flight_id": e.flight_id,
                "old_status": e.old_value,
                "new_status": e.new_value,
                "change_description": f"{e.event_type}: {e.old_value} → {e.new_value}",
                "change_time": e.timestamp.isoformat(),
                "notifications_count": db.query(Notification).filter_by(event_id=e.event_id).count()
            }
            for e in recent_events
        ],
        "airline_stats": []
    }

@router.get("/scheduler/status")
def get_scheduler_status(db: Session = Depends(get_db)):
    poll_interval = AppSetting.get(db, "poll_interval", "20")
    return {
        "status": "active",
        "running": True,
        "poll_interval": poll_interval,
        "next_poll": f"{poll_interval}s"
    }

@router.get("/logs/changes")
def get_change_logs(flight_id: Optional[str] = Query(None), limit: int = Query(100), db: Session = Depends(get_db)):
    q = db.query(Event)
    if flight_id:
        q = q.filter_by(flight_id=flight_id)
    events = q.order_by(Event.timestamp.desc()).limit(limit).all()
    return [
        {
            "id": e.id,
            "change_id": e.event_id,
            "flight_id": e.flight_id,
            "old_status": e.old_value,
            "new_status": e.new_value,
            "change_description": f"{e.event_type}: {e.old_value} → {e.new_value}",
            "change_time": e.timestamp.isoformat(),
            "notification_sent": e.processed,
            "notifications_count": db.query(Notification).filter_by(event_id=e.event_id).count()
        }
        for e in events
    ]

@router.get("/logs/notifications")
def get_notification_logs(flight_id: Optional[str] = Query(None), limit: int = Query(100), db: Session = Depends(get_db)):
    q = db.query(Notification)
    if flight_id:
        q = q.filter_by(flight_id=flight_id)
    notifs = q.order_by(Notification.sent_at.desc()).limit(limit).all()
    return [
        {
            "id": n.id,
            "passenger_id": n.passenger_id,
            "flight_id": n.flight_id,
            "phone_number": n.phone_number,
            "message_text": n.message_text,
            "template_type": n.template_type,
            "status": n.status,
            "error_message": n.error_message,
            "sent_at": n.sent_at.isoformat()
        }
        for n in notifs
    ]
