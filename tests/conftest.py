import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock

from app.main import app
from app.db.base import Base
from app.db.session import get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(setup_db):
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
            
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    del app.dependency_overrides[get_db]

@pytest.fixture(autouse=True)
def mock_external_services():
    with patch("app.services.flight_api.FlightAPIClient.get_flights") as mock_flights, \
         patch("app.services.passenger_api.PassengerAPIClient.get_passengers_for_flight") as mock_passengers, \
         patch("app.services.whatsapp.WhatsAppService.send_template_message") as mock_wa:
        
        mock_flights.return_value = []
        mock_passengers.return_value = []
        mock_wa.return_value = True
        
        yield {
            "flights": mock_flights,
            "passengers": mock_passengers,
            "whatsapp": mock_wa
        }
