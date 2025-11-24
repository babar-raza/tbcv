#!/usr/bin/env python3
"""
Migration: Add validation_types column to validation_results table

This migration adds a validation_types column to track which validation types
were run for each validation result (e.g., ["yaml", "markdown", "Truth"]).

Usage:
    python migrations/add_validation_types_column.py
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import db_manager
from sqlalchemy import text


def migrate():
    """Add validation_types column to validation_results table."""
    print("Starting migration: add_validation_types_column")

    try:
        with db_manager.get_session() as session:
            # Check if column already exists
            result = session.execute(text(
                "SELECT COUNT(*) FROM pragma_table_info('validation_results') "
                "WHERE name='validation_types'"
            ))
            column_exists = result.scalar() > 0

            if column_exists:
                print("[OK] Column validation_types already exists, skipping migration")
                return True

            # Add the column (SQLite)
            print("Adding validation_types column to validation_results table...")
            session.execute(text(
                "ALTER TABLE validation_results ADD COLUMN validation_types TEXT"
            ))
            session.commit()

            print("[OK] Successfully added validation_types column")
            return True

    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        return False


def rollback():
    """Remove validation_types column from validation_results table."""
    print("Starting rollback: remove validation_types column")

    try:
        with db_manager.get_session() as session:
            # Note: SQLite doesn't support DROP COLUMN directly
            # This would require recreating the table
            print("[WARNING] SQLite doesn't support DROP COLUMN - manual rollback required")
            print("To rollback, you'll need to:")
            print("1. Create a new table without validation_types")
            print("2. Copy data from old table to new table")
            print("3. Drop old table and rename new table")
            return False

    except Exception as e:
        print(f"[ERROR] Rollback failed: {e}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Database migration for validation_types column")
    parser.add_argument("--rollback", action="store_true", help="Rollback the migration")
    args = parser.parse_args()

    if args.rollback:
        success = rollback()
    else:
        success = migrate()

    sys.exit(0 if success else 1)
