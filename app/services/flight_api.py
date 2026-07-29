import time
import httpx
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

logger = logging.getLogger(__name__)

class FlightAPIConnector:
    """
    Enterprise Reusable Flight API Client supporting:
    - Retries with exponential backoff
    - Strict timeouts
    """
    def __init__(self):
        self.last_sync: str = "Never"
        self.response_time_ms: int = 0
        self.status: str = "Unknown"
        self.last_error: str = ""
        # Setup standard httpx client with timeout
        self.client = httpx.Client(timeout=httpx.Timeout(5.0, read=10.0))

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException)),
        reraise=True
    )
    def _fetch_data(self, url: str, headers: dict) -> httpx.Response:
        logger.info(f"Fetching flights from external API: {url}")
        resp = self.client.get(url, headers=headers)
        resp.raise_for_status()
        return resp

    def get_flights(self, api_url: str, api_key: str, auth_type: str = "Bearer", mode: str = "mock") -> List[Dict[str, Any]]:
        start_t = time.perf_counter()
        if mode == "mock" or not api_url:
            self.status = "Connected"
            self.response_time_ms = int((time.perf_counter() - start_t) * 1000)
            self.last_sync = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            return self._generate_demo_flights()

        headers = {}
        if auth_type == "Bearer":
            headers["Authorization"] = f"Bearer {api_key}"
        elif auth_type == "APIKey":
            headers["X-API-Key"] = api_key

        try:
            resp = self._fetch_data(api_url, headers)
            self.response_time_ms = int((time.perf_counter() - start_t) * 1000)
            self.last_sync = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            self.status = "Connected"
            self.last_error = ""
            return resp.json()
        except Exception as e:
            self.response_time_ms = int((time.perf_counter() - start_t) * 1000)
            self.last_sync = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            self.status = "Disconnected"
            self.last_error = str(e)
            logger.error(f"[FlightAPIConnector] Error fetching flights: {e}", exc_info=True)
            # Graceful degradation: return empty list so the app doesn't crash
            return []

    def _generate_demo_flights(self) -> List[Dict[str, Any]]:
        now = datetime.utcnow()
        return [
            {
                "flight_number": "KC721",
                "airline": "Air SANS",
                "origin": "Turkistan",
                "destination": "Almaty",
                "departure_time": (now + timedelta(hours=2)).isoformat(),
                "arrival_time": (now + timedelta(hours=4)).isoformat(),
                "gate": "A3",
                "terminal": "1",
                "status": "ON_TIME",
                "delay_minutes": 0,
            }
        ]

flight_api_client = FlightAPIConnector()
