import logging
from typing import Dict, Any, Optional
from posthog import Posthog
from app.core.config import settings

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self):
        self.client: Optional[Posthog] = None
        self.enabled = settings.ANALYTICS_ENABLED
        
        # Use provided keys as fallbacks if not in env
        api_key = settings.POSTHOG_API_KEY or "phc_CoiBttZRiisz79phEy5yr6KoUjy3JkcNq8PHGTDREhH3"
        host = settings.POSTHOG_HOST or "https://us.i.posthog.com"
        
        if self.enabled and api_key:
            try:
                self.client = Posthog(api_key, host=host)
                # Catch errors internally
                self.client.on_error = self._on_error
                logger.info("PostHog Analytics client initialized.")
            except Exception as e:
                logger.error(f"Failed to initialize PostHog: {e}")
                self.enabled = False
        else:
            if not self.enabled:
                logger.info("Analytics is disabled via ANALYTICS_ENABLED configuration.")
            else:
                logger.info("PostHog API key not found. Analytics disabled.")
            self.enabled = False

    def _on_error(self, err: Exception):
        logger.error(f"PostHog error: {err}")

    def capture(self, user_id: str, event: str, properties: Optional[Dict[str, Any]] = None):
        """Capture an event safely. Fails silently if not enabled."""
        if not self.enabled or not self.client:
            return
            
        try:
            self.client.capture(user_id, event=event, properties=properties)
        except Exception as e:
            logger.error(f"Failed to capture analytics event '{event}': {e}")

    def identify(self, user_id: str, properties: Dict[str, Any]):
        """Identify a user with properties."""
        if not self.enabled or not self.client:
            return
            
        try:
            self.client.identify(user_id, properties)
        except Exception as e:
            logger.error(f"Failed to identify analytics user '{user_id}': {e}")

    def shutdown(self):
        """Flush and shutdown the client."""
        if self.client:
            self.client.shutdown()

analytics_service = AnalyticsService()
