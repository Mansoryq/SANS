import pytest
from datetime import datetime, timedelta

def test_create_and_list_flights(client, db_session):
    flight_data = {
        "flight_id": "TEST123",
        "airline": "SANS Airline",
        "origin": "DXB",
        "destination": "LHR",
        "scheduled_departure": (datetime.utcnow() + timedelta(days=1)).isoformat(),
        "scheduled_arrival": (datetime.utcnow() + timedelta(days=1, hours=7)).isoformat(),
        "status": "ON_TIME",
        "delay_minutes": 0,
        "gate": "A1",
        "terminal": "3"
    }
    
    # 1. Create Flight
    response = client.post("/api/flights", json=flight_data)
    assert response.status_code == 201
    assert response.json()["success"] is True
    assert response.json()["flight_id"] == "TEST123"
    
    # 2. List Flights (backward compatibility check - should return list)
    response = client.get("/api/flights")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["flight_id"] == "TEST123"
    assert data[0]["passenger_count"] == 0
    assert len(data[0]["timeline"]) == 1
    assert data[0]["timeline"][0]["event_type"] == "CREATED"
    
    # 3. Get Single Flight
    response = client.get("/api/flights/TEST123")
    assert response.status_code == 200
    data = response.json()
    assert data["flight_id"] == "TEST123"
    
def test_update_flight(client, db_session):
    flight_data = {
        "flight_id": "TEST456",
        "origin": "NYC",
        "destination": "LAX",
        "scheduled_departure": (datetime.utcnow() + timedelta(days=1)).isoformat(),
        "scheduled_arrival": (datetime.utcnow() + timedelta(days=1, hours=5)).isoformat()
    }
    client.post("/api/flights", json=flight_data)
    
    update_data = {
        "status": "DELAYED",
        "delay_minutes": 45,
        "gate": "B2"
    }
    response = client.put("/api/flights/TEST456", json=update_data)
    assert response.status_code == 200
    
    # Verify update and timeline
    res = client.get("/api/flights/TEST456")
    assert res.json()["status"] == "DELAYED"
    assert res.json()["delay_minutes"] == 45
    timeline = res.json()["timeline"]
    assert any(t["event_type"] == "DELAYED" for t in timeline)

def test_delete_flight(client, db_session):
    flight_data = {
        "flight_id": "TEST789",
        "origin": "NYC",
        "destination": "LAX",
        "scheduled_departure": (datetime.utcnow() + timedelta(days=1)).isoformat(),
        "scheduled_arrival": (datetime.utcnow() + timedelta(days=1, hours=5)).isoformat()
    }
    client.post("/api/flights", json=flight_data)
    
    response = client.delete("/api/flights/TEST789")
    assert response.status_code == 204
    
    response = client.get("/api/flights/TEST789")
    assert response.status_code == 404
