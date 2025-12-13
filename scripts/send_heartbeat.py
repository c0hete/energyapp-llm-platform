#!/usr/bin/env python3
"""
Send heartbeat event to Hub.
Usage: python scripts/send_heartbeat.py
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

if __name__ == "__main__":
    hub = get_hub_reporter()
    hub.report_heartbeat(status="healthy")
    print("[HEARTBEAT] Script completed")
