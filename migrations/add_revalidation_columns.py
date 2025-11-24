#!/usr/bin/env python3
"""
Migration: Add re-validation support columns to validation_results table

This migration adds two columns:
- parent_validation_id: Links a re-validation to its original validation
- comparison_data: Stores comparison results between validations

Usage:
    python migrations/add_revalidation_columns.py
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import db_manager
from sqlalchemy import text


def migrate():
    """Add re-validation columns to validation_results table."""
    print("Starting migration: add_revalidation_columns")

    try:
        with db_manager.get_session() as session:
            # Check if parent_validation_id column exists
            result = session.execute(text(
                "SELECT COUNT(*) FROM pragma_table_info('validation_results') "
                "WHERE name='parent_validation_id'"
            ))
            parent_col_exists = result.scalar() > 0

            # Check if comparison_data column exists
            result = session.execute(text(
                "SELECT COUNT(*) FROM pragma_table_info('validation_results') "
                "WHERE name='comparison_data'"
            ))
            comparison_col_exists = result.scalar() > 0

            if parent_col_exists and comparison_col_exists:
                print("[OK] Columns already exist, skipping migration")
                return True

            # Add parent_validation_id column
            if not parent_col_exists:
                print("Adding parent_validation_id column to validation_results table...")
                session.execute(text(
                    "ALTER TABLE validation_results ADD COLUMN parent_validation_id TEXT"
                ))
                print("[OK] Added parent_validation_id column")

            # Add comparison_data column
            if not comparison_col_exists:
                print("Adding comparison_data column to validation_results table...")
                session.execute(text(
                    "ALTER TABLE validation_results ADD COLUMN comparison_data TEXT"
                ))
                print("[OK] Added comparison_data column")

            session.commit()
            print("[OK] Migration completed successfully")
            return True

    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        return False


def rollback():
    """Remove re-validation columns from validation_results table."""
    print("Starting rollback: remove re-validation columns")

    try:
        with db_manager.get_session() as session:
            # Note: SQLite doesn't support DROP COLUMN directly
            print("[WARNING] SQLite doesn't support DROP COLUMN - manual rollback required")
            print("To rollback, you'll need to:")
            print("1. Create a new table without parent_validation_id and comparison_data")
            print("2. Copy data from old table to new table")
            print("3. Drop old table and rename new table")
            return False

    except Exception as e:
        print(f"[ERROR] Rollback failed: {e}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Database migration for re-validation columns")
    parser.add_argument("--rollback", action="store_true", help="Rollback the migration")
    args = parser.parse_args()

    if args.rollback:
        success = rollback()
    else:
        success = migrate()

    sys.exit(0 if success else 1)
