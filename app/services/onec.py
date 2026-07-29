import time
import httpx
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

class OneCAPIClient:
    """
    1C Enterprise REST Integration Client.
    Sends statistics (sent, failed, delays, reports) to 1C API.
    """
    def __init__(self):
        self.status: str = "Unknown"
        self.response_time_ms: int = 0
        self.last_sync: str = "Never"
        self.last_error: str = ""

    def send_statistics(self, stats_data: Dict[str, Any], onec_url: str, onec_login: str, onec_password: str, mode: str = "mock") -> bool:
        start_t = time.time()
        if mode == "mock" or not onec_url:
            self.status = "Connected"
            self.response_time_ms = int((time.time() - start_t) * 1000)
            self.last_sync = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"[1C SIMULATION] Exported statistics: {stats_data}")
            return True

        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.post(onec_url, json=stats_data, auth=(onec_login, onec_password))
                self.response_time_ms = int((time.time() - start_t) * 1000)
                self.last_sync = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                if resp.status_code in [200, 201]:
                    self.status = "Connected"
                    self.last_error = ""
                    return True
                else:
                    self.status = "Disconnected"
                    self.last_error = f"HTTP {resp.status_code}: {resp.text}"
                    return False
        except Exception as e:
            self.response_time_ms = int((time.time() - start_t) * 1000)
            self.last_sync = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            self.status = "Disconnected"
            self.last_error = str(e)
            logger.error(f"[OneCAPIClient] Error: {e}")
            return False

onec_client = OneCAPIClient()
