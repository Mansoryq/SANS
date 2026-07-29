import uuid
import logging
import threading
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.models.flight import Flight, FlightTimeline
from app.models.passenger import Passenger
from app.models.event import Event
from app.models.notification import Notification
from app.models.settings import AppSetting
from app.models.log import AuditLog

from app.services.flight_api import flight_api_client
from app.services.passenger_api import passenger_api_client
from app.services.whatsapp import whatsapp_service
from app.services.queue import notification_queue_worker
from app.core.encryption import decrypt_value
from app.services.analytics import analytics_service

logger = logging.getLogger(__name__)

_flight_snapshot_cache: Dict[str, Dict[str, Any]] = {}
_cache_lock = threading.Lock()

class EventEngineService:
    """
    Production-Grade Flight Monitor & Event Engine.
    Features:
    - Thread-safe snapshot caching
    - Full transaction rollback on errors
    - Detects 7 Event Types + Flight Timelines
    - Automatic Notification Enqueueing
    """

    @staticmethod
    def run_polling_workflow(db: Session):
        try:
            mode = AppSetting.get(db, 'mode', 'mock')
            api_url = AppSetting.get(db, 'flight_api_url', '')
            api_key_enc = AppSetting.get(db, 'flight_api_key', '')
            api_key = decrypt_value(api_key_enc)

            # 1. Download flights from Flight API
            remote_flights = flight_api_client.get_flights(api_url=api_url, api_key=api_key, mode=mode)
            if not remote_flights:
                db_flights = db.query(Flight).all()
                if not db_flights:
                    EventEngineService._seed_demo_flights(db)
                    db_flights = db.query(Flight).all()
                remote_flights = [
                    {
                        "flight_number": f.flight_id,
                        "airline": f.airline,
                        "origin": f.origin,
                        "destination": f.destination,
                        "departure_time": f.scheduled_departure.isoformat(),
                        "arrival_time": f.scheduled_arrival.isoformat(),
                        "gate": f.gate,
                        "terminal": f.terminal,
                        "status": f.status,
                        "delay_minutes": f.delay_minutes
                    }
                    for f in db_flights
                ]

            # 2. Compare snapshots & Detect Events thread-safely
            with _cache_lock:
                for f_data in remote_flights:
                    fid = f_data["flight_number"]
                    prev = _flight_snapshot_cache.get(fid)

                    # Upsert Flight in DB
                    flight = db.query(Flight).filter_by(flight_id=fid).first()
                    if not flight:
                        flight = Flight(
                            flight_id=fid,
                            airline=f_data.get("airline", "Air SANS"),
                            origin=f_data["origin"],
                            destination=f_data["destination"],
                            scheduled_departure=datetime.fromisoformat(f_data["departure_time"]),
                            scheduled_arrival=datetime.fromisoformat(f_data["arrival_time"]),
                            gate=f_data.get("gate"),
                            terminal=f_data.get("terminal"),
                            status=f_data.get("status", "ON_TIME"),
                            delay_minutes=f_data.get("delay_minutes", 0)
                        )
                        db.add(flight)
                        db.flush()
                        tl = FlightTimeline(flight_id=fid, event_type="CREATED", description=f"Flight {fid} registered.")
                        db.add(tl)
                        db.commit()

                    # Synchronize Passengers for Flight
                    EventEngineService._sync_passengers_for_flight(db, fid, mode)

                    if prev is not None:
                        detected_events = EventEngineService._detect_events(prev, f_data)
                        for ev in detected_events:
                            EventEngineService.create_and_process_event(
                                db=db,
                                flight=flight,
                                event_type=ev["type"],
                                old_val=ev["old"],
                                new_val=ev["new"]
                            )

                    _flight_snapshot_cache[fid] = f_data

            # 3. Process Notification Queue
            notification_queue_worker.process_pending_queue(db)

        except Exception as e:
            db.rollback()
            logger.error(f"[EventEngineService] Polling workflow failed: {e}")

    @staticmethod
    def _detect_events(prev: Dict[str, Any], curr: Dict[str, Any]) -> List[Dict[str, Any]]:
        events = []
        if prev.get("status") != curr.get("status"):
            st = curr.get("status")
            events.append({"type": st, "old": prev.get("status"), "new": st})
        elif prev.get("gate") != curr.get("gate") and curr.get("gate"):
            events.append({"type": "GATE_CHANGED", "old": prev.get("gate", ""), "new": curr.get("gate", "")})
        elif prev.get("terminal") != curr.get("terminal") and curr.get("terminal"):
            events.append({"type": "TERMINAL_CHANGED", "old": prev.get("terminal", ""), "new": curr.get("terminal", "")})
        elif prev.get("departure_time") != curr.get("departure_time"):
            events.append({"type": "TIME_CHANGED", "old": prev.get("departure_time"), "new": curr.get("departure_time")})
        return events

    @staticmethod
    def create_and_process_event(db: Session, flight: Flight, event_type: str, old_val: str, new_val: str):
        try:
            event_uuid = str(uuid.uuid4())
            ev = Event(
                event_id=event_uuid,
                flight_id=flight.flight_id,
                event_type=event_type,
                old_value=str(old_val),
                new_value=str(new_val),
                processed=True,
                processed_time=datetime.utcnow()
            )
            db.add(ev)

            descriptions = {
                'DELAYED': f"Flight delayed (+{flight.delay_minutes} min)",
                'CANCELLED': "Flight CANCELLED",
                'GATE_CHANGED': f"Gate changed from {old_val} to {new_val}",
                'TERMINAL_CHANGED': f"Terminal changed from {old_val} to {new_val}",
                'BOARDING': f"Boarding started at Gate {flight.gate}",
                'BOARDING_CLOSED': "Boarding closed",
                'TIME_CHANGED': f"Departure time changed to {new_val}",
                'ON_TIME': "Flight on time"
            }
            tl = FlightTimeline(
                flight_id=flight.flight_id,
                event_type=event_type,
                description=descriptions.get(event_type, f"Event {event_type}: {old_val} -> {new_val}")
            )
            db.add(tl)

            log = AuditLog(
                action_type="FlightChange",
                flight_id=flight.flight_id,
                details=f"Event {event_type} generated for {flight.flight_id}",
                status="SUCCESS"
            )
            db.add(log)
            db.commit()
            
            # PostHog Analytics
            analytics_service.capture(
                user_id="system_event_engine",
                event="flight_event_created",
                properties={
                    "flight_id": flight.flight_id,
                    "event_type": event_type,
                    "airline": flight.airline
                }
            )

            passengers = db.query(Passenger).filter_by(flight_id=flight.flight_id).all()
            for p in passengers:
                msg_text = whatsapp_service.build_message_text(event_type, flight, p)
                notif = Notification(
                    passenger_id=p.passenger_id,
                    flight_id=flight.flight_id,
                    event_id=event_uuid,
                    phone_number=p.phone_number,
                    message_text=msg_text,
                    template_type=event_type,
                    status='PENDING',
                    attempts=0
                )
                db.add(notif)
            db.commit()

            notification_queue_worker.process_pending_queue(db)

        except Exception as e:
            db.rollback()
            logger.error(f"[EventEngineService] Event creation failed: {e}")

    @staticmethod
    def _sync_passengers_for_flight(db: Session, flight_id: str, mode: str):
        try:
            api_url = AppSetting.get(db, 'passenger_api_url', '')
            api_key_enc = AppSetting.get(db, 'passenger_api_key', '')
            api_key = decrypt_value(api_key_enc)

            remote_passengers = passenger_api_client.get_passengers_for_flight(flight_id, api_url, api_key, mode)
            
            # Fetch existing passengers in one query to avoid N+1
            existing_passengers = db.query(Passenger).filter(Passenger.flight_id == flight_id).all()
            passenger_map = {p.passenger_id: p for p in existing_passengers}
            
            for p_data in remote_passengers:
                pid = p_data["passenger_id"]
                p = passenger_map.get(pid)
                if not p:
                    p = Passenger(
                        passenger_id=pid,
                        first_name=p_data["first_name"],
                        last_name=p_data.get("last_name", ""),
                        phone_number=p_data["phone_number"],
                        flight_id=flight_id,
                        seat_number=p_data.get("seat_number"),
                        booking_reference=p_data.get("booking_reference", "N/A"),
                        ticket_number=p_data.get("ticket_number"),
                        preferred_language=p_data.get("preferred_language", "ru")
                    )
                    db.add(p)
                else:
                    p.phone_number = p_data["phone_number"]
                    p.preferred_language = p_data.get("preferred_language", "ru")
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"[EventEngineService] Passenger sync failed: {e}")

    @staticmethod
    def _seed_demo_flights(db: Session):
        if db.query(Flight).count() > 0:
            return

        from datetime import timedelta
        import random
        now = datetime.utcnow()
        demo_data = [
            {'flight_id': 'KC721', 'origin': 'Turkistan', 'destination': 'Almaty', 'gate': 'A3', 'terminal': '1'},
            {'flight_id': 'KC952', 'origin': 'Turkistan', 'destination': 'Astana', 'gate': 'A5', 'terminal': '1'},
            {'flight_id': 'DV701', 'origin': 'Turkistan', 'destination': 'Shymkent', 'gate': 'B2', 'terminal': '2'},
            {'flight_id': 'KC404', 'origin': 'Turkistan', 'destination': 'Istanbul', 'gate': 'B5', 'terminal': '2'},
            {'flight_id': 'FZ890', 'origin': 'Turkistan', 'destination': 'Dubai', 'gate': 'C1', 'terminal': '2'},
        ]
        for fd in demo_data:
            if not db.query(Flight).filter_by(flight_id=fd['flight_id']).first():
                dep = now + timedelta(hours=random.randint(1, 8))
                arr = dep + timedelta(hours=random.randint(2, 4))
                f = Flight(
                    flight_id=fd['flight_id'], airline='Air SANS',
                    origin=fd['origin'], destination=fd['destination'],
                    scheduled_departure=dep, scheduled_arrival=arr,
                    gate=fd['gate'], terminal=fd['terminal'], status='ON_TIME'
                )
                db.add(f)
                db.flush()
                tl = FlightTimeline(flight_id=fd['flight_id'], event_type="CREATED", description=f"Flight {fd['flight_id']} registered.")
                db.add(tl)
        db.commit()

event_engine_service = EventEngineService()
