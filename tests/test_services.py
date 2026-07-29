import pytest
from unittest.mock import MagicMock
from app.services.flight_service import FlightService
from app.schemas.flight import FlightCreate

def test_flight_service_create(db_session):
    # Setup service with real test DB
    service = FlightService(db_session)
    
    # Use schema for creation
    data = FlightCreate(
        flight_id="SRV100",
        airline="TestAirline",
        origin="AAA",
        destination="BBB",
        scheduled_departure="2030-01-01T10:00:00",
        scheduled_arrival="2030-01-01T12:00:00"
    )
    
    # 1. Create Flight
    f = service.create_flight(data)
    assert f is not None
    assert f.flight_id == "SRV100"
    
    # 2. Prevent duplicate
    f2 = service.create_flight(data)
    assert f2 is None
    
    # 3. Retrieve
    f_get = service.get_flight("SRV100")
    assert f_get is not None
    assert f_get.airline == "TestAirline"
    
    # 4. List caching simulation
    lst1 = service.list_flights()
    assert len(lst1) >= 1
    
    # 5. Delete
    service.delete_flight("SRV100")
    assert service.get_flight("SRV100") is None
