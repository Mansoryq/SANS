import random
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.session import get_db
from app.models.flight import Flight
from app.models.passenger import Passenger
from app.services.event_engine import event_engine_service
from app.api.websockets import ws_manager

router = APIRouter(prefix="/simulation", tags=["Simulation Center"])

@router.post("/trigger")
def trigger_event(payload: dict, db: Session = Depends(get_db)):
    action = payload.get("action", "RANDOM")
    flight_id = payload.get("flight_id")
    delay_min = payload.get("delay_minutes", 45)
    new_gate = payload.get("gate", "B7")
    new_terminal = payload.get("terminal", "2")

    if action == "RANDOM":
        flights = db.query(Flight).all()
        if not flights:
            raise HTTPException(status_code=400, detail="No flights available")
        f = random.choice(flights)
        action = random.choice(["DELAYED", "CANCELLED", "GATE_CHANGED", "BOARDING", "TERMINAL_CHANGED"])
        flight_id = f.flight_id

    f = db.query(Flight).filter_by(flight_id=flight_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Flight not found")

    old_status = f.status
    old_gate = f.gate or "A1"
    old_terminal = f.terminal or "1"

    if action == "DELAYED":
        f.status = "DELAYED"
        f.delay_minutes = delay_min
        db.commit()
        event_engine_service.create_and_process_event(db, f, "DELAYED", old_status, "DELAYED")

    elif action == "CANCELLED":
        f.status = "CANCELLED"
        db.commit()
        event_engine_service.create_and_process_event(db, f, "CANCELLED", old_status, "CANCELLED")

    elif action == "GATE_CHANGED":
        f.gate = new_gate
        db.commit()
        event_engine_service.create_and_process_event(db, f, "GATE_CHANGED", old_gate, new_gate)

    elif action == "TERMINAL_CHANGED":
        f.terminal = new_terminal
        db.commit()
        event_engine_service.create_and_process_event(db, f, "TERMINAL_CHANGED", old_terminal, new_terminal)

    elif action in ["BOARDING", "BOARDING_CLOSED", "ON_TIME"]:
        f.status = action
        db.commit()
        event_engine_service.create_and_process_event(db, f, action, old_status, action)

    return {"success": True, "flight_id": flight_id, "action": action}

@router.post("/generate-passenger")
def generate_random_passenger(flight_id: str, db: Session = Depends(get_db)):
    f = db.query(Flight).filter_by(flight_id=flight_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Flight not found")
    
    names = [("Айдар", "Касымов"), ("Самал", "Ибраева"), ("Ерлан", "Тулегенов")]
    fn, ln = random.choice(names)
    pid = f"P{uuid.uuid4().hex[:8].upper()}"
    p = Passenger(
        passenger_id=pid,
        first_name=fn,
        last_name=ln,
        phone_number=f"+7701{random.randint(1000000, 9999999)}",
        flight_id=flight_id,
        seat_number=f"{random.randint(1,30)}{random.choice('ABCDEF')}",
        booking_reference=uuid.uuid4().hex[:6].upper(),
        ticket_number=f"TKT-{random.randint(1000,9999)}",
        preferred_language=random.choice(["ru", "kk", "en"])
    )
    db.add(p)
    db.commit()
    return {"success": True, "passenger_id": pid}
