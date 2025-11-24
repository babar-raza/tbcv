#!/usr/bin/env python3
"""
Migration: Add validation history tracking columns.

Adds file_hash and version_number columns to validation_results table
to support validation history tracking and trend analysis.
"""

import os
import sys

# Add parent directory to path to import from core
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import db_manager
from sqlalchemy import text


def run_migration():
    """Run the migration to add validation history columns."""
    print("Starting migration: Add validation history columns")

    with db_manager.engine.begin() as conn:
        # Check if columns already exist
        result = conn.execute(text("PRAGMA table_info(validation_results)"))
        existing_columns = {row[1] for row in result}

        migrations_run = []

        # Add file_hash column if it doesn't exist
        if "file_hash" not in existing_columns:
            print("Adding file_hash column...")
            conn.execute(text(
                """
                ALTER TABLE validation_results
                ADD COLUMN file_hash TEXT
                """
            ))
            migrations_run.append("file_hash")
            print("[OK] Added file_hash column")
        else:
            print("[SKIP] file_hash column already exists, skipping")

        # Add version_number column if it doesn't exist
        if "version_number" not in existing_columns:
            print("Adding version_number column...")
            conn.execute(text(
                """
                ALTER TABLE validation_results
                ADD COLUMN version_number INTEGER DEFAULT 1
                """
            ))
            migrations_run.append("version_number")
            print("[OK] Added version_number column")
        else:
            print("[SKIP] version_number column already exists, skipping")

        # Update existing records to populate file_hash where possible
        if "file_hash" in migrations_run:
            print("\nUpdating existing records with file hashes...")

            # Get all validation results with file paths
            results = conn.execute(text(
                """
                SELECT id, file_path
                FROM validation_results
                WHERE file_path IS NOT NULL AND file_hash IS NULL
                """
            ))

            import hashlib
            update_count = 0

            for row in results:
                validation_id, file_path = row

                # Calculate file hash if file exists
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'rb') as f:
                            file_hash = hashlib.sha256(f.read()).hexdigest()

                        conn.execute(text(
                            """
                            UPDATE validation_results
                            SET file_hash = :file_hash
                            WHERE id = :id
                            """
                        ), {"file_hash": file_hash, "id": validation_id})

                        update_count += 1
                    except Exception as e:
                        print(f"  Warning: Could not hash file {file_path}: {e}")

            print(f"[OK] Updated {update_count} records with file hashes")

        # Set version numbers for existing records
        if "version_number" in migrations_run:
            print("\nSetting version numbers for existing records...")

            # Group validations by file_path and set version numbers
            # based on created_at timestamp
            conn.execute(text(
                """
                WITH ranked_validations AS (
                    SELECT
                        id,
                        ROW_NUMBER() OVER (
                            PARTITION BY file_path
                            ORDER BY created_at ASC
                        ) as rn
                    FROM validation_results
                    WHERE file_path IS NOT NULL
                )
                UPDATE validation_results
                SET version_number = (
                    SELECT rn
                    FROM ranked_validations
                    WHERE ranked_validations.id = validation_results.id
                )
                WHERE id IN (SELECT id FROM ranked_validations)
                """
            ))

            print("[OK] Set version numbers for existing records")

    print("\n" + "="*60)
    if migrations_run:
        print(f"[SUCCESS] Migration complete! Added columns: {', '.join(migrations_run)}")
    else:
        print("[SUCCESS] Migration already applied, no changes needed")
    print("="*60)


if __name__ == "__main__":
    run_migration()
