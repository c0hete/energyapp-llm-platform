#!/usr/bin/env python3
"""
Report daily metrics to Hub.
Usage: python scripts/report_daily_metrics.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv(project_root / '.env')

from src.db import SessionLocal
from src.models import Conversation, Message, User
from src.hub_reporter import get_hub_reporter
from sqlalchemy import func

def calculate_metrics():
    """Calculate daily metrics from database"""
    db = SessionLocal()
    hub = get_hub_reporter()

    try:
        today = datetime.utcnow().date()
        yesterday = datetime.utcnow() - timedelta(days=1)

        # 1. Conversations today
        daily_convs = db.query(func.count(Conversation.id)).filter(
            Conversation.created_at >= yesterday
        ).scalar()
        hub.report_metric('daily_conversations', daily_convs or 0, period='24h')
        print(f"[METRICS] Daily conversations: {daily_convs}")

        # 2. Messages today
        daily_msgs = db.query(func.count(Message.id)).filter(
            Message.created_at >= yesterday
        ).scalar()
        hub.report_metric('daily_messages', daily_msgs or 0, period='24h')
        print(f"[METRICS] Daily messages: {daily_msgs}")

        # 3. Active users (with conversations today)
        active_users = db.query(func.count(func.distinct(Conversation.user_id))).filter(
            Conversation.created_at >= yesterday
        ).scalar()
        hub.report_metric('daily_active_users', active_users or 0, period='24h')
        print(f"[METRICS] Active users: {active_users}")

        # 4. Total active users
        total_users = db.query(func.count(User.id)).filter(User.active == True).scalar()
        hub.report_metric('total_active_users', total_users or 0, unit='count', period='instant')
        print(f"[METRICS] Total active users: {total_users}")

        print("[METRICS] All metrics reported successfully")

    except Exception as e:
        print(f"[METRICS] Error calculating metrics: {e}")
        hub.report_error(
            severity='high',
            message=f"Failed to calculate daily metrics: {str(e)}",
            trace=str(e)
        )
    finally:
        db.close()

if __name__ == "__main__":
    calculate_metrics()
