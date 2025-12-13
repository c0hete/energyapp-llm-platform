# Hub Integration — Next Steps for EnergyApp

**Status:** ✅ Hub POST endpoint ready
**Your design:** ✅ Complete (`HUB_INTEGRATION_DESIGN.md`)
**Next action:** Implement `HubEventReporter`

---

## 📋 What's Ready

1. ✅ **Hub API POST endpoint** is now live (locally tested)
2. ✅ **Your integration design** is complete and approved
3. ✅ **Knowledge Base** documented in `/srv/knowledge-base/`
4. ⏳ **Token generation** pending (will be done after Hub deploys to production)

---

## 🎯 Your Next Tasks (in order)

### **Phase 1: Implementation (Now)**

#### **1. Create `src/hub_reporter.py`**

Implement exactly as designed in `HUB_INTEGRATION_DESIGN.md`:

```python
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
```

---

#### **2. Add Dependencies**

```bash
cd C:\Users\JoseA\energyapp-llm-platform
pip install httpx python-ulid
```

Or add to `requirements.txt`:
```txt
httpx>=0.27.0
python-ulid>=2.0.0
```

---

#### **3. Configure `.env`**

Add variables from `.env.hub` to your main `.env`:

```env
# Hub Integration
HUB_API_URL=https://hub.alvaradomazzei.cl/api/v1/hub
HUB_API_TOKEN=  # Will be generated after Hub deploys
HUB_EVENTS_ENABLED=false  # Keep false until token is ready
HUB_SOURCE=energyapp
HUB_ENV=production
```

---

#### **4. Implement Event Emission**

Follow the plan in `HUB_INTEGRATION_DESIGN.md`:

**Example (AppRegistered):**
```python
# src/main.py
from src.hub_reporter import get_hub_reporter

# At app startup
@app.on_event("startup")
async def startup_event():
    hub = get_hub_reporter()
    hub.report_app_registered(version="2.1.0", env="production")
```

**Example (Interaction):**
```python
# src/routes/conversations.py
from ..hub_reporter import get_hub_reporter

@router.post("")
def create_conversation(...):
    conv = Conversation(...)
    db.add(conv)
    db.commit()

    # Report to Hub
    hub = get_hub_reporter()
    hub.report_interaction(
        action="conversation_created",
        conversation_id=conv.id,
        user_id=user.id
    )

    return conv
```

---

#### **5. Create Scripts (Metrics & Heartbeat)**

**A. `scripts/send_heartbeat.py`**
```python
import sys
sys.path.append('/root/energyapp-llm-platform')

from src.hub_reporter import get_hub_reporter

if __name__ == "__main__":
    hub = get_hub_reporter()
    hub.report_heartbeat(status="healthy")
```

**B. `scripts/report_daily_metrics.py`**
```python
import sys
sys.path.append('/root/energyapp-llm-platform')

from src.database import SessionLocal
from src.models import Conversation, Message
from datetime import datetime, timedelta
from src.hub_reporter import get_hub_reporter

def calculate_metrics():
    db = SessionLocal()
    today = datetime.now().date()

    # Conversations today
    conversations_today = db.query(Conversation).filter(
        Conversation.created_at >= today
    ).count()

    # Messages today
    messages_today = db.query(Message).filter(
        Message.created_at >= today
    ).count()

    db.close()

    return {
        "daily_conversations": conversations_today,
        "daily_messages": messages_today
    }

if __name__ == "__main__":
    metrics = calculate_metrics()
    hub = get_hub_reporter()

    hub.report_metric("daily_conversations", metrics["daily_conversations"], period="24h")
    hub.report_metric("daily_messages", metrics["daily_messages"], period="24h")
```

---

#### **6. Test Locally (Logging Only)**

```bash
cd C:\Users\JoseA\energyapp-llm-platform

# Make sure HUB_EVENTS_ENABLED=false
python scripts/send_heartbeat.py

# Expected output:
# [HUB] Would send: AgentHeartbeat - {'status': 'healthy'}
```

---

### **Phase 2: Production Integration (After Hub Deploys)**

#### **1. Wait for Hub deployment**
José will deploy Hub to production and generate your token.

#### **2. Add token to `.env`**
```env
HUB_API_TOKEN=<generated_token>
HUB_EVENTS_ENABLED=true  # Enable actual sending
```

#### **3. Test end-to-end**
```bash
python scripts/send_heartbeat.py

# Expected output:
# [HUB] ✅ Event sent: AgentHeartbeat
```

#### **4. Configure cron jobs (on server)**
```bash
# /etc/cron.d/energyapp-hub

# Heartbeat every 5 minutes
*/5 * * * * /root/energyapp-llm-platform/venv/bin/python /root/energyapp-llm-platform/scripts/send_heartbeat.py >> /var/log/energyapp-hub.log 2>&1

# Daily metrics at 23:00 UTC
0 23 * * * /root/energyapp-llm-platform/venv/bin/python /root/energyapp-llm-platform/scripts/report_daily_metrics.py >> /var/log/energyapp-hub.log 2>&1
```

---

## ✅ Acceptance Criteria

Before marking this integration as "done":

- [ ] `src/hub_reporter.py` implemented
- [ ] Dependencies installed (`httpx`, `python-ulid`)
- [ ] `.env` configured
- [ ] `AppRegistered` emitted at startup
- [ ] At least 2 interaction events implemented
- [ ] Heartbeat script working
- [ ] Daily metrics script working
- [ ] Tested locally (logging mode)
- [ ] Tested in production (when token ready)
- [ ] Cron jobs configured
- [ ] Events visible in Hub (`GET /api/v1/hub/events`)

---

## 📚 References

- **Your design:** `HUB_INTEGRATION_DESIGN.md` (this directory)
- **Knowledge Base:** `/srv/knowledge-base/` (server) or https://github.com/c0hete/knowledge-base
- **Event Model:** `/srv/knowledge-base/supervisor/03_EVENT_MODEL.md`
- **Protocols:** `/srv/knowledge-base/supervisor/04_PROTOCOLS_AND_CONTRACTS.md`
- **Integration Doc:** `/srv/knowledge-base/projects/energyapp/SUPERVISOR_INTEGRATION.md`

---

## 💡 Tips

1. **Start with logging only** (`HUB_EVENTS_ENABLED=false`) to debug without hitting the API
2. **Implement incrementally**: AppRegistered → Heartbeat → 1 Interaction → Rest
3. **Don't block on failures**: Wrap all Hub calls in try/except
4. **Test with curl** before implementing in Python
5. **Monitor logs**: `tail -f /var/log/energyapp-hub.log`

---

## 📞 Questions?

Ask José or check:
- Knowledge Base docs
- Hub API error responses (they're descriptive)
- Existing integration in Portfolio (when it's implemented)

---

**Status:** Ready to implement ✅
**Estimated time:** 2-3 hours for Phase 1, 1 hour for Phase 2
