import httpx
from unittest.mock import patch
from app.services.flight_api import flight_api_client

def test_flight_api_retry_logic():
    # We will mock the internal _fetch_data to raise TimeoutException twice, then succeed
    call_count = {"count": 0}
    
    def mock_fetch(*args, **kwargs):
        call_count["count"] += 1
        if call_count["count"] <= 2:
            raise httpx.TimeoutException("Mock Timeout")
        else:
            # Succeed on the 3rd try
            response = httpx.Response(200, json=[{"flight_number": "KC123"}])
            return response
            
    with patch.object(flight_api_client, "_fetch_data", side_effect=mock_fetch):
        # We also need to bypass the _fetch_data retry decorator for this specific test,
        # or better yet, mock the httpx client inside _fetch_data.
        pass

def test_flight_api_client_backoff():
    # Let's mock the httpx client itself
    call_count = {"count": 0}
    
    def mock_get(*args, **kwargs):
        call_count["count"] += 1
        if call_count["count"] <= 2:
            raise httpx.TimeoutException("Mock Timeout")
        return httpx.Response(200, json=[{"flight_number": "KC123"}])
        
    # We must patch the client instance that FlightAPIConnector uses
    with patch.object(flight_api_client.client, "get", side_effect=mock_get):
        result = flight_api_client.get_flights("http://fake.api", "key", "Bearer", mode="live")
        assert len(result) == 1
        assert result[0]["flight_number"] == "KC123"
        assert call_count["count"] == 3  # Attempted 3 times

def test_flight_api_client_graceful_degradation():
    def mock_get_fail(*args, **kwargs):
        raise httpx.TimeoutException("Mock Timeout")
        
    with patch.object(flight_api_client.client, "get", side_effect=mock_get_fail):
        result = flight_api_client.get_flights("http://fake.api", "key", "Bearer", mode="live")
        # Should return empty list instead of crashing
        assert result == []
        assert flight_api_client.status == "Disconnected"
