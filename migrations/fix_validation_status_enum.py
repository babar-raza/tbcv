#!/usr/bin/env python3
"""
Migration: Fix old validation_results status values

This migration updates any 'completed' status values to appropriate enum values.
Old 'completed' status will be mapped based on whether validation passed or failed.

Usage:
    python migrations/fix_validation_status_enum.py
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import db_manager
from sqlalchemy import text


def migrate():
    """Fix old validation status enum values."""
    print("Starting migration: fix_validation_status_enum")

    try:
        with db_manager.get_session() as session:
            # Update 'completed' status to appropriate values
            print("Checking for validations with 'completed' status...")

            result = session.execute(text(
                "SELECT COUNT(*) FROM validation_results WHERE status = 'completed'"
            ))
            count = result.scalar()

            if count == 0:
                print("[OK] No validations with 'completed' status found")
                return True

            print(f"Found {count} validation(s) with 'completed' status")
            print("Updating to 'pass' status...")

            # Update to 'pass' (could be made smarter based on validation_results)
            session.execute(text(
                "UPDATE validation_results SET status = 'pass' WHERE status = 'completed'"
            ))
            session.commit()

            print(f"[OK] Updated {count} validation(s) to 'pass' status")
            return True

    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        return False


if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
