#!/usr/bin/env python3
"""
Test script for Hub event reporting.
Tests all event types locally without sending to API.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv(project_root / '.env')

from src.hub_reporter import get_hub_reporter

def test_all_events():
    """Test all event types"""
    hub = get_hub_reporter()

    print("=" * 60)
    print("Testing Hub Event Reporting (Local Mode)")
    print("=" * 60)
    print()

    # 1. AppRegistered
    print("1. Testing AppRegistered...")
    hub.report_app_registered(version="0.2.0", env="dev")
    print()

    # 2. AgentHeartbeat
    print("2. Testing AgentHeartbeat...")
    hub.report_heartbeat(status="healthy")
    print()

    # 3. InteractionDetected - Conversation
    print("3. Testing InteractionDetected (conversation_created)...")
    hub.report_interaction(
        action="conversation_created",
        conversation_id=123,
        user_id=1,
        title="Test Conversation"
    )
    print()

    # 4. InteractionDetected - Message
    print("4. Testing InteractionDetected (message_sent - user)...")
    hub.report_interaction(
        action="message_sent",
        role="user",
        conversation_id=123,
        user_id=1,
        message_length=50
    )
    print()

    # 5. InteractionDetected - Message Assistant
    print("5. Testing InteractionDetected (message_sent - assistant)...")
    hub.report_interaction(
        action="message_sent",
        role="assistant",
        conversation_id=123,
        message_length=200
    )
    print()

    # 6. InteractionDetected - Login
    print("6. Testing InteractionDetected (user_login)...")
    hub.report_interaction(
        action="user_login",
        user_id=1,
        email="test@example.com"
    )
    print()

    # 7. InteractionDetected - Logout
    print("7. Testing InteractionDetected (user_logout)...")
    hub.report_interaction(
        action="user_logout",
        user_id=1,
        email="test@example.com"
    )
    print()

    # 8. MetricReported
    print("8. Testing MetricReported...")
    hub.report_metric("daily_conversations", 15, period="24h")
    print()

    # 9. ErrorReported
    print("9. Testing ErrorReported...")
    hub.report_error(
        severity="high",
        message="Test error message",
        trace="Stack trace here..."
    )
    print()

    print("=" * 60)
    print("All event types tested successfully!")
    print("=" * 60)
    print()
    print("Note: HUB_EVENTS_ENABLED is set to 'false'")
    print("Events are being logged but not sent to the Hub API.")
    print("This is expected behavior for local testing.")
    print()

if __name__ == "__main__":
    test_all_events()
