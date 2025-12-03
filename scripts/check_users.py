#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/energyapp-llm-platform')

from src.db import SessionLocal
from src.models import User

try:
    session = SessionLocal()
    users = session.query(User).all()

    print("\n" + "="*70)
    print("USERS IN PRODUCTION DATABASE")
    print("="*70)

    if not users:
        print("No users found in database")
    else:
        for user in users:
            status = "ACTIVE" if user.active else "INACTIVE"
            print("ID: %d | Email: %-30s | Role: %-15s | %s" % (user.id, user.email, user.role, status))

    print("="*70)
    print("Total users: %d" % len(users))

    # Check for role issues
    problematic = [u for u in users if u.role == "administrador"]
    if problematic:
        print("\nWARNING: Found %d users with 'administrador' role (system expects 'admin'):" % len(problematic))
        for u in problematic:
            print("  - %s" % u.email)

    session.close()
except Exception as e:
    print("Error: %s" % str(e))
    import traceback
    traceback.print_exc()
    sys.exit(1)
