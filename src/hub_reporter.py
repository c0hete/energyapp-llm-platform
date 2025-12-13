# src/hub_reporter.py
import os
import httpx
from datetime import datetime, timezone
from ulid import ULID
from typing import Optional, Dict, Any

class HubEventReporter:
    def __init__(self):
        self.base_url = os.getenv('HUB_API_URL')
        self.token = os.getenv('HUB_API_TOKEN')
        self.enabled = os.getenv('HUB_EVENTS_ENABLED', 'false').lower() == 'true'
        self.source = os.getenv('HUB_SOURCE', 'energyapp')

    def _send_event(self, event_type: str, payload: Dict[str, Any], occurred_at: Optional[str] = None):
        if not self.enabled:
            print(f"[HUB] Would send: {event_type} - {payload}")
            return

        if not self.base_url or not self.token:
            print(f"[HUB] Error: Missing HUB_API_URL or HUB_API_TOKEN")
            return

        event = {
            "type": event_type,
            "source": self.source,
            "occurred_at": occurred_at or datetime.now(timezone.utc).isoformat(),
            "payload": payload
        }

        try:
            response = httpx.post(
                f"{self.base_url}/events",
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json"
                },
                json=event,
                timeout=5.0
            )
            response.raise_for_status()
            print(f"[HUB] ✅ Event sent: {event_type}")
        except Exception as e:
            print(f"[HUB] ❌ Error sending event: {e}")

    def report_app_registered(self, version: str, env: str):
        self._send_event("AppRegistered", {"version": version, "env": env})

    def report_heartbeat(self, status: str = "healthy"):
        self._send_event("AgentHeartbeat", {"status": status})

    def report_interaction(self, action: str, **kwargs):
        payload = {"action": action, **kwargs}
        self._send_event("InteractionDetected", payload)

    def report_metric(self, metric: str, value: float, unit: str = "count", period: str = "24h"):
        payload = {"metric": metric, "value": value, "unit": unit, "period": period}
        self._send_event("MetricReported", payload)

    def report_error(self, severity: str, message: str, trace: Optional[str] = None):
        payload = {"severity": severity, "message": message}
        if trace:
            payload["trace"] = trace
        self._send_event("ErrorReported", payload)

# Singleton
_hub_reporter = None

def get_hub_reporter() -> HubEventReporter:
    global _hub_reporter
    if _hub_reporter is None:
        _hub_reporter = HubEventReporter()
    return _hub_reporter
