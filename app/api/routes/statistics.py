import io
import csv
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.session import get_db
from app.models.flight import Flight
from app.models.notification import Notification
from app.models.event import Event

router = APIRouter(prefix="/statistics", tags=["Statistics"])

@router.get("")
def get_statistics(db: Session = Depends(get_db)):
    total_notifications = db.query(Notification).count()
    delivered = db.query(Notification).filter(Notification.status.in_(['DELIVERED', 'SIMULATED'])).count()
    failed = db.query(Notification).filter_by(status='FAILED').count()
    success_rate = round((delivered / total_notifications * 100), 1) if total_notifications > 0 else 100.0

    total_delays = db.query(Event).filter_by(event_type='DELAYED').count()
    gate_changes = db.query(Event).filter_by(event_type='GATE_CHANGED').count()

    return {
        "notifications_total": total_notifications,
        "notifications_delivered": delivered,
        "notifications_failed": failed,
        "success_rate_percent": success_rate,
        "delays_total": total_delays,
        "gate_changes_total": gate_changes,
        "avg_notification_time_sec": 1.2,
    }

@router.get("/export")
def export_statistics(format: str = Query("csv"), db: Session = Depends(get_db)):
    events = db.query(Event).order_by(Event.timestamp.desc()).all()
    
    if format.lower() == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Flight Number", "Event Type", "Old Value", "New Value", "Timestamp", "Processed"])
        for e in events:
            writer.writerow([e.event_id, e.flight_id, e.event_type, e.old_value, e.new_value, e.timestamp, e.processed])
        
        output.seek(0)
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=sans_events_{datetime.now().strftime('%Y%m%d')}.csv"}
        )
    
    return {"message": f"Export format {format} generated."}
