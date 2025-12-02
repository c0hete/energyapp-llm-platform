#!/usr/bin/env python3
"""
Test script for PHASE 0 session functionality
Tests: session creation, validation, revocation, and logging
"""

import sys
import os
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.db import SessionLocal, engine
from src.models import Base, User, Session as SessionModel
from src.sessions import (
    generate_session_token,
    create_session,
    validate_session,
    revoke_session,
    get_active_sessions_count,
)
from src.config import get_settings

def test_session_flow():
    """Test complete session lifecycle"""
    print("\n" + "="*60)
    print("PHASE 0: Session Management Test")
    print("="*60 + "\n")

    # Create tables
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Create or get test user
        print("[1] Creating/Getting test user...")
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        if not test_user:
            test_user = User(
                email="test@example.com",
                password_hash="dummy",
                active=True,
                role="trabajador"
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
            print(f"    ✓ Created user: {test_user.email} (id={test_user.id})")
        else:
            print(f"    ✓ Using existing user: {test_user.email} (id={test_user.id})")

        # 2. Test session token generation
        print("\n[2] Testing session token generation...")
        token = generate_session_token()
        print(f"    ✓ Generated token: {token[:20]}... (length: {len(token)})")

        # 3. Create session
        print("\n[3] Creating session...")
        session_token = create_session(
            db=db,
            user_id=test_user.id,
            ip_address="127.0.0.1",
            user_agent="Test Client/1.0",
            hours=24
        )
        print(f"    ✓ Session created: {session_token[:20]}...")

        # Verify session in database
        session_record = db.query(SessionModel).filter(SessionModel.token == session_token).first()
        if session_record:
            print(f"    ✓ Session found in DB: is_active={session_record.is_active}")
            print(f"      - Created: {session_record.created_at}")
            print(f"      - Expires: {session_record.expires_at}")
            print(f"      - Last used: {session_record.last_used_at}")

        # 4. Validate session
        print("\n[4] Validating session...")
        validated_user = validate_session(
            db=db,
            token=session_token,
            ip_address="127.0.0.1",
            update_last_used=True
        )
        if validated_user:
            print(f"    ✓ Session validated: {validated_user.email}")

            # Check if last_used_at was updated
            db.refresh(session_record)
            print(f"      - Last used updated: {session_record.last_used_at}")
        else:
            print("    ✗ Session validation failed!")
            return False

        # 5. Get active sessions count
        print("\n[5] Checking active sessions count...")
        count = get_active_sessions_count(db=db, user_id=test_user.id)
        print(f"    ✓ Active sessions: {count}")

        # 6. Revoke session
        print("\n[6] Revoking session...")
        revoked = revoke_session(db=db, token=session_token)
        if revoked:
            print(f"    ✓ Session revoked successfully")

            # Verify revocation
            db.refresh(session_record)
            print(f"      - is_active now: {session_record.is_active}")
        else:
            print("    ✗ Session revocation failed!")
            return False

        # 7. Try to validate revoked session
        print("\n[7] Attempting to validate revoked session...")
        invalid_user = validate_session(
            db=db,
            token=session_token,
            ip_address="127.0.0.1",
            update_last_used=False
        )
        if invalid_user is None:
            print(f"    ✓ Correctly rejected revoked session")
        else:
            print(f"    ✗ Should have rejected revoked session!")
            return False

        # Check logs
        print("\n[8] Checking log files...")
        settings = get_settings()
        log_dir = Path("./logs")

        if log_dir.exists():
            log_files = list(log_dir.glob("*.log"))
            print(f"    ✓ Log files found: {len(log_files)}")
            for log_file in log_files:
                print(f"      - {log_file.name} ({log_file.stat().st_size} bytes)")
        else:
            print(f"    ⚠ Logs directory not found at {log_dir}")

        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED")
        print("="*60 + "\n")
        return True

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_session_flow()
    sys.exit(0 if success else 1)
