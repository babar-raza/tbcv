# TBCV Backup and Recovery Guide

## Table of Contents

1. [Overview](#overview)
2. [What to Backup](#what-to-backup)
3. [Database Backup](#database-backup)
4. [Truth Data Backup](#truth-data-backup)
5. [Checkpoint Backup](#checkpoint-backup)
6. [Configuration Backup](#configuration-backup)
7. [Backup Automation](#backup-automation)
8. [Restore Procedures](#restore-procedures)
9. [Disaster Recovery](#disaster-recovery)
10. [Backup Best Practices](#backup-best-practices)
11. [Recovery Scenarios](#recovery-scenarios)
12. [Backup Checklist](#backup-checklist)

---

## Overview

### Why Backups Are Critical

The TBCV system maintains critical operational data that must be protected:

- **Validation Results**: Historical records of content validation runs, issues detected, and approval status
- **Recommendations**: AI-generated and human-approved recommendations for content improvements
- **Audit Logs**: Complete audit trail of all changes, approvals, and system actions
- **Workflows**: State and progress of validation and enhancement workflows
- **Configuration**: System settings, rules, and validation parameters
- **Checkpoints**: Saved workflow states enabling recovery from failures or resumption of work

Data loss scenarios can occur due to:
- Hardware failures (disk corruption, media degradation)
- Software errors (bugs, failed updates, migrations)
- Accidental deletion (user error, improper commands)
- Security incidents (ransomware, unauthorized access)
- Natural disasters (power outages, environmental damage)

### Backup Strategies

Three primary strategies are available:

**Full Backup**: Complete copy of all data
- Pros: Simple recovery, comprehensive protection
- Cons: Large storage requirements, longer backup time
- Use Case: Initial backup, weekly/monthly archival

**Incremental Backup**: Only changes since last backup
- Pros: Fast, minimal storage, frequent scheduling
- Cons: Requires multiple backups for full recovery
- Use Case: Daily operational backups

**Differential Backup**: All changes since last full backup
- Pros: Balance of speed and completeness
- Cons: Moderate storage, medium recovery complexity
- Use Case: Daily backups with weekly full backups

### RTO and RPO Considerations

**Recovery Time Objective (RTO)**: Maximum acceptable downtime
- Critical systems: < 1 hour
- Standard systems: < 4 hours
- Non-critical: < 24 hours

**Recovery Point Objective (RPO)**: Maximum acceptable data loss
- Critical data: < 15 minutes (hourly backups)
- Important data: < 4 hours (daily backups)
- Archival data: < 24 hours (daily backups)

For TBCV systems:
- Database: RTO 1 hour, RPO 1 hour (hourly backups recommended)
- Truth Data: RTO 4 hours, RPO 4 hours (daily backups)
- Checkpoints: RTO immediate, RPO 0 (retained locally, redundant copies)
- Configuration: RTO 1 hour, RPO permanent (version control recommended)

---

## What to Backup

### Complete Backup Inventory

The following data components require backup protection:

```
TBCV System Backup Structure
├── Database
│   ├── tbcv.db (SQLite primary database)
│   ├── Workflows table
│   ├── Validation results table
│   ├── Recommendations table
│   ├── Audit logs table
│   └── Cache entries table
├── Truth Data
│   ├── Configuration files (*.yaml)
│   ├── Validation rules
│   ├── Plugins configuration
│   └── Custom validators
├── Checkpoints
│   ├── Workflow state snapshots
│   ├── Database checkpoints
│   ├── State validation hashes
│   └── Checkpoint metadata
├── Configuration
│   ├── config/main.yaml
│   ├── config/*.yaml (all rules and settings)
│   ├── .env / Environment variables
│   ├── alembic.ini (database migrations)
│   └── Settings and secrets
├── Application Files
│   ├── agents/ (custom validators and agents)
│   ├── core/ (core business logic)
│   ├── api/ (API definitions)
│   └── cli/ (CLI implementations)
├── Logs & Reports
│   ├── data/logs/ (operational logs)
│   ├── data/reports/ (generated reports)
│   └── .audit_log.jsonl (audit trail)
└── Metadata
    ├── .performance_metrics.jsonl
    ├── .maintenance_mode file
    └── Version information
```

### Backup Priorities

**Priority 1 - Critical (Must Backup)**
- Database (tbcv.db)
- Audit logs (.audit_log.jsonl)
- Configuration files (config/*.yaml)
- Environment variables (.env)

**Priority 2 - Important (Should Backup)**
- Validation results
- Recommendations
- Checkpoints (.checkpoints/)
- Custom agents and validators

**Priority 3 - Reference (Nice to Have)**
- Logs (data/logs/)
- Reports (data/reports/)
- Performance metrics (.performance_metrics.jsonl)
- Cache (data/cache/)

---

## Database Backup

### Understanding the Database

TBCV can use SQLite or PostgreSQL depending on configuration:

**SQLite (Development/Small Deployments)**
- Single file: `data/tbcv.db` (typically 80-500 MB)
- No server required
- File-based, easy to backup
- Location specified by `DATABASE_URL` environment variable

**PostgreSQL (Production/Large Deployments)**
- Server-based database
- Multiple tables and indexes
- Requires pg_dump or pg_basebackup
- More complex recovery procedures

### SQLite Backup Procedures

#### Backup SQLite Database - Manual

```bash
#!/bin/bash
# backup_sqlite.sh - Manual SQLite backup

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_FILE="./data/tbcv.db"
BACKUP_FILE="${BACKUP_DIR}/tbcv_${TIMESTAMP}.db"

# Create backup directory if needed
mkdir -p "${BACKUP_DIR}"

# Copy database file (SQLite handles concurrent access)
cp "${DB_FILE}" "${BACKUP_FILE}"

# Compress backup for storage efficiency
gzip "${BACKUP_FILE}"

# Verify backup integrity
echo "Verifying backup integrity..."
sqlite3 "${BACKUP_FILE%.gz}" "PRAGMA integrity_check;" > /dev/null
if [ $? -eq 0 ]; then
    echo "Backup successful: ${BACKUP_FILE}.gz"
    echo "Size: $(du -h ${BACKUP_FILE}.gz | cut -f1)"
else
    echo "ERROR: Backup verification failed!"
    rm "${BACKUP_FILE}.gz"
    exit 1
fi

# Generate backup summary
BACKUP_SIZE=$(du -h "${BACKUP_FILE}.gz" | cut -f1)
ORIGINAL_SIZE=$(du -h "${DB_FILE}" | cut -f1)
echo "Summary: Original=${ORIGINAL_SIZE}, Compressed=${BACKUP_SIZE}"
```

#### Backup SQLite Database - Optimized

```bash
#!/bin/bash
# backup_sqlite_optimized.sh - Optimized SQLite backup with checksums

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_FILE="./data/tbcv.db"
BACKUP_NAME="tbcv_${TIMESTAMP}"
BACKUP_DIR_TIMESTAMPED="${BACKUP_DIR}/${BACKUP_NAME}"

# Create timestamped backup directory
mkdir -p "${BACKUP_DIR_TIMESTAMPED}"

# Copy database
cp "${DB_FILE}" "${BACKUP_DIR_TIMESTAMPED}/tbcv.db"

# Generate checksum for verification
cd "${BACKUP_DIR_TIMESTAMPED}"
sha256sum tbcv.db > tbcv.db.sha256
cd - > /dev/null

# Backup database metadata
sqlite3 "${DB_FILE}" ".schema" > "${BACKUP_DIR_TIMESTAMPED}/schema.sql"
sqlite3 "${DB_FILE}" "SELECT count(*) as workflows FROM workflows;" > "${BACKUP_DIR_TIMESTAMPED}/metadata.txt"
sqlite3 "${DB_FILE}" "SELECT count(*) as validations FROM validation_results;" >> "${BACKUP_DIR_TIMESTAMPED}/metadata.txt"
sqlite3 "${DB_FILE}" "SELECT count(*) as recommendations FROM recommendations;" >> "${BACKUP_DIR_TIMESTAMPED}/metadata.txt"
sqlite3 "${DB_FILE}" "SELECT count(*) as audit_logs FROM audit_logs;" >> "${BACKUP_DIR_TIMESTAMPED}/metadata.txt"

# Create tar archive
cd "${BACKUP_DIR}"
tar -czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}/"
cd - > /dev/null

# Verify tar archive integrity
tar -tzf "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" > /dev/null
if [ $? -eq 0 ]; then
    echo "Backup successful: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
    # Cleanup temporary directory
    rm -rf "${BACKUP_DIR_TIMESTAMPED}"
else
    echo "ERROR: Tar archive verification failed!"
    exit 1
fi
```

#### SQLite Backup - Python Implementation

```python
#!/usr/bin/env python3
# backup_sqlite.py - Python-based SQLite backup with validation

import os
import shutil
import sqlite3
import hashlib
import json
from datetime import datetime
from pathlib import Path

class SQLiteBackup:
    def __init__(self, db_path: str, backup_dir: str = "./backups"):
        self.db_path = db_path
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def calculate_checksum(self, filepath: str) -> str:
        """Calculate SHA256 checksum of file."""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def verify_database(self, db_path: str) -> bool:
        """Verify database integrity."""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check;")
            result = cursor.fetchone()
            conn.close()
            return result[0] == "ok"
        except Exception as e:
            print(f"Database verification failed: {e}")
            return False

    def get_table_counts(self) -> dict:
        """Get row counts for all tables."""
        counts = {}
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()

            for (table_name,) in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                counts[table_name] = cursor.fetchone()[0]

            conn.close()
        except Exception as e:
            print(f"Error getting table counts: {e}")

        return counts

    def backup(self) -> bool:
        """Create backup with metadata."""
        backup_name = f"tbcv_{self.timestamp}"
        backup_path = self.backup_dir / backup_name / "tbcv.db"
        backup_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy database file
        try:
            shutil.copy2(self.db_path, backup_path)
        except Exception as e:
            print(f"Failed to copy database: {e}")
            return False

        # Verify backup
        if not self.verify_database(str(backup_path)):
            print("Backup verification failed!")
            return False

        # Calculate checksums
        original_checksum = self.calculate_checksum(self.db_path)
        backup_checksum = self.calculate_checksum(str(backup_path))

        if original_checksum != backup_checksum:
            print("Checksum mismatch!")
            return False

        # Get table counts
        table_counts = self.get_table_counts()

        # Create metadata file
        metadata = {
            "backup_timestamp": self.timestamp,
            "database_path": self.db_path,
            "backup_path": str(backup_path),
            "checksum": backup_checksum,
            "file_size_bytes": os.path.getsize(str(backup_path)),
            "table_counts": table_counts,
            "verification_status": "passed"
        }

        metadata_path = backup_path.parent / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        # Create tar archive
        archive_path = self.backup_dir / f"{backup_name}.tar.gz"
        shutil.make_archive(str(archive_path.with_suffix('')), 'gztar',
                          str(backup_path.parent.parent), backup_name)

        # Cleanup directory
        shutil.rmtree(backup_path.parent.parent)

        print(f"Backup completed successfully!")
        print(f"Archive: {archive_path}")
        print(f"Size: {os.path.getsize(archive_path) / 1024 / 1024:.2f} MB")
        print(f"Checksum: {backup_checksum}")

        return True

# Usage
if __name__ == "__main__":
    db_path = os.getenv("DATABASE_URL", "sqlite:///./data/tbcv.db")
    if db_path.startswith("sqlite:///"):
        db_path = db_path.replace("sqlite:///", "")

    backup = SQLiteBackup(db_path)
    success = backup.backup()
    exit(0 if success else 1)
```

### PostgreSQL Backup Procedures

#### PostgreSQL Full Backup with pg_dump

```bash
#!/bin/bash
# backup_postgres.sh - PostgreSQL full backup with pg_dump

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME="${POSTGRES_DB:-tbcv}"
DB_USER="${POSTGRES_USER:-postgres}"
DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5432}"

mkdir -p "${BACKUP_DIR}"

# Full database dump (includes schema and data)
BACKUP_FILE="${BACKUP_DIR}/tbcv_${TIMESTAMP}.sql"
pg_dump \
    -h "${DB_HOST}" \
    -p "${DB_PORT}" \
    -U "${DB_USER}" \
    -d "${DB_NAME}" \
    --verbose \
    --format=plain \
    --file="${BACKUP_FILE}"

if [ $? -ne 0 ]; then
    echo "ERROR: pg_dump failed!"
    exit 1
fi

# Compress backup
gzip "${BACKUP_FILE}"
COMPRESSED_FILE="${BACKUP_FILE}.gz"

echo "Backup successful: ${COMPRESSED_FILE}"
echo "Size: $(du -h ${COMPRESSED_FILE} | cut -f1)"

# Verify backup is readable
if gzip -t "${COMPRESSED_FILE}" 2>/dev/null; then
    echo "Backup verification: PASSED"
else
    echo "ERROR: Backup verification failed!"
    exit 1
fi
```

#### PostgreSQL Continuous Archiving

```bash
#!/bin/bash
# backup_postgres_continuous.sh - PostgreSQL continuous archiving backup

# Configure WAL archiving in postgresql.conf:
# archive_mode = on
# archive_command = 'test ! -f /archive/%f && cp %p /archive/%f'
# archive_timeout = 300

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="tbcv_${TIMESTAMP}"

mkdir -p "${BACKUP_DIR}/${BACKUP_NAME}"

# Start backup
echo "Starting PostgreSQL backup..."
BACKUP_LABEL=$(psql -h localhost -U postgres -d tbcv \
    -t -c "SELECT pg_start_backup('${BACKUP_NAME}');")

# Copy data directory
echo "Copying data directory..."
pg_basebackup \
    -h localhost \
    -D "${BACKUP_DIR}/${BACKUP_NAME}/data" \
    -Ft -z \
    -X stream

# Stop backup
echo "Stopping backup..."
psql -h localhost -U postgres -d tbcv \
    -c "SELECT pg_stop_backup();"

# Create tar archive
echo "Creating archive..."
tar -czf "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" \
    -C "${BACKUP_DIR}" "${BACKUP_NAME}"

# Cleanup
rm -rf "${BACKUP_DIR}/${BACKUP_NAME}"

echo "Backup completed: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
```

### Backup Verification

```python
#!/usr/bin/env python3
# verify_backup.py - Verify database backup integrity

import sqlite3
import os
from datetime import datetime

def verify_sqlite_backup(backup_path: str) -> dict:
    """Verify SQLite backup integrity and content."""
    result = {
        "status": "unknown",
        "verified_at": datetime.now().isoformat(),
        "checks": {}
    }

    # Check 1: File exists
    if not os.path.exists(backup_path):
        result["status"] = "failed"
        result["checks"]["file_exists"] = False
        return result
    result["checks"]["file_exists"] = True

    # Check 2: File is readable
    if not os.access(backup_path, os.R_OK):
        result["status"] = "failed"
        result["checks"]["file_readable"] = False
        return result
    result["checks"]["file_readable"] = True

    # Check 3: Database integrity
    try:
        conn = sqlite3.connect(backup_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check;")
        integrity_result = cursor.fetchone()[0]
        result["checks"]["database_integrity"] = (integrity_result == "ok")
        conn.close()
    except Exception as e:
        result["checks"]["database_integrity"] = False
        result["error"] = str(e)
        result["status"] = "failed"
        return result

    # Check 4: Required tables
    try:
        conn = sqlite3.connect(backup_path)
        cursor = conn.cursor()
        required_tables = ['workflows', 'validation_results', 'recommendations', 'audit_logs']

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        existing_tables = set([row[0] for row in cursor.fetchall()])

        missing_tables = set(required_tables) - existing_tables
        result["checks"]["required_tables_present"] = len(missing_tables) == 0

        if missing_tables:
            result["missing_tables"] = list(missing_tables)

        conn.close()
    except Exception as e:
        result["checks"]["required_tables_present"] = False
        result["error"] = str(e)

    # Check 5: Row counts
    try:
        conn = sqlite3.connect(backup_path)
        cursor = conn.cursor()

        table_counts = {}
        for table in required_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                table_counts[table] = cursor.fetchone()[0]
            except:
                pass

        result["table_counts"] = table_counts
        result["total_rows"] = sum(table_counts.values())
        conn.close()
    except Exception as e:
        result["error"] = str(e)

    # Determine final status
    all_checks_pass = all(result["checks"].values())
    result["status"] = "passed" if all_checks_pass else "failed"

    return result

# Usage
if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: verify_backup.py <backup_file>")
        sys.exit(1)

    result = verify_sqlite_backup(sys.argv[1])
    print(json.dumps(result, indent=2))

    sys.exit(0 if result["status"] == "passed" else 1)
```

---

## Truth Data Backup

### Truth Data Components

The truth data directory contains validation rules and configuration:

```
config/
├── main.yaml              # Main system configuration
├── truth.yaml             # Truth validation rules
├── validation_flow.yaml   # Validation workflow definitions
├── markdown.yaml          # Markdown validation rules
├── links.yaml             # Link validation rules
├── code.yaml              # Code validation rules
├── frontmatter.yaml       # Frontmatter validation rules
├── seo.yaml               # SEO validation rules
├── structure.yaml         # Document structure rules
├── cache.yaml             # Caching configuration
├── access_guards.yaml     # Access control configuration
├── llm.yaml               # LLM integration configuration
├── rag.yaml               # RAG configuration
├── reflection.yaml        # Reflection configuration
├── enhancement.yaml       # Enhancement configuration
└── agent.yaml             # Agent configuration
```

### Truth Data Backup Script

```bash
#!/bin/bash
# backup_truth_data.sh - Backup configuration and truth data

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
TRUTH_DIR="./config"
ARCHIVE_NAME="truth_data_${TIMESTAMP}.tar.gz"

mkdir -p "${BACKUP_DIR}"

# Backup all configuration files
tar -czf "${BACKUP_DIR}/${ARCHIVE_NAME}" \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    -C . config/

echo "Truth data backup: ${BACKUP_DIR}/${ARCHIVE_NAME}"
echo "Contents:"
tar -tzf "${BACKUP_DIR}/${ARCHIVE_NAME}" | head -20

# Generate checksum
sha256sum "${BACKUP_DIR}/${ARCHIVE_NAME}" > "${BACKUP_DIR}/${ARCHIVE_NAME}.sha256"
```

### Truth Data Version Control

```bash
#!/bin/bash
# truth_data_version_control.sh - Use git for truth data versioning

# Initialize git tracking for config directory if not present
if [ ! -d "config/.git" ]; then
    cd config
    git init
    git config user.email "system@tbcv"
    git config user.name "TBCV System"
fi

# Stage all changes
cd config
git add -A

# Create commit with timestamp
COMMIT_MSG="Truth data update $(date '+%Y-%m-%d %H:%M:%S')"
git commit -m "${COMMIT_MSG}" || echo "No changes to commit"

# Show version
VERSION=$(git log -1 --format=%H 2>/dev/null || echo "unversioned")
echo "Truth data version: ${VERSION}"
```

---

## Checkpoint Backup

### Checkpoint Structure

```
.checkpoints/
├── 20251203_163011_test_workflow_1764779411/
│   ├── database.db                 # Database state at checkpoint
│   ├── workflow_state.json         # Workflow state data
│   ├── metadata.json               # Checkpoint metadata
│   └── manifest.json               # Files included in checkpoint
├── 20251203_163048_test_workflow_1764779448/
│   └── [same structure]
└── [more checkpoints...]
```

### Checkpoint Retention Policy

```python
#!/usr/bin/env python3
# checkpoint_retention.py - Manage checkpoint retention

import os
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path

class CheckpointManager:
    def __init__(self, checkpoint_dir: str = "./.checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)

    def cleanup_old_checkpoints(self,
                               days_to_keep: int = 7,
                               min_checkpoints: int = 1,
                               dry_run: bool = False) -> dict:
        """Clean up checkpoints older than specified days.

        Args:
            days_to_keep: Keep checkpoints from last N days
            min_checkpoints: Always keep at least this many recent checkpoints
            dry_run: If True, only report what would be deleted

        Returns:
            Dictionary with cleanup statistics
        """

        result = {
            "deleted": [],
            "retained": [],
            "total_freed_bytes": 0
        }

        if not self.checkpoint_dir.exists():
            return result

        # Get all checkpoints sorted by date (newest first)
        checkpoints = []
        for cp_dir in self.checkpoint_dir.iterdir():
            if cp_dir.is_dir():
                try:
                    stat = cp_dir.stat()
                    checkpoints.append((cp_dir, stat.st_mtime))
                except:
                    pass

        checkpoints.sort(key=lambda x: x[1], reverse=True)

        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cutoff_timestamp = cutoff_date.timestamp()

        # Determine which to delete
        for idx, (cp_dir, mtime) in enumerate(checkpoints):
            # Keep minimum number of recent checkpoints
            if idx < min_checkpoints:
                result["retained"].append(str(cp_dir))
                continue

            # Delete if older than cutoff date
            if mtime < cutoff_timestamp:
                size = sum(f.stat().st_size for f in cp_dir.rglob('*')
                          if f.is_file())

                if not dry_run:
                    shutil.rmtree(cp_dir)

                result["deleted"].append(str(cp_dir))
                result["total_freed_bytes"] += size
            else:
                result["retained"].append(str(cp_dir))

        return result

# Usage
if __name__ == "__main__":
    manager = CheckpointManager()

    # Dry run first
    print("Dry run - what would be deleted:")
    dry_result = manager.cleanup_old_checkpoints(
        days_to_keep=7,
        min_checkpoints=2,
        dry_run=True
    )
    print(json.dumps(dry_result, indent=2, default=str))

    # Actual cleanup
    print("\nExecuting cleanup...")
    result = manager.cleanup_old_checkpoints(
        days_to_keep=7,
        min_checkpoints=2,
        dry_run=False
    )

    freed_mb = result["total_freed_bytes"] / 1024 / 1024
    print(f"Deleted: {len(result['deleted'])} checkpoints")
    print(f"Retained: {len(result['retained'])} checkpoints")
    print(f"Space freed: {freed_mb:.2f} MB")
```

### Checkpoint Archival

```bash
#!/bin/bash
# archive_checkpoints.sh - Archive old checkpoints for long-term storage

CHECKPOINT_DIR="./.checkpoints"
ARCHIVE_DIR="./backup_archive"
ARCHIVE_AGE_DAYS=30

mkdir -p "${ARCHIVE_DIR}"

# Find checkpoints older than ARCHIVE_AGE_DAYS
find "${CHECKPOINT_DIR}" -maxdepth 1 -type d -mtime +${ARCHIVE_AGE_DAYS} | while read -r checkpoint; do
    checkpoint_name=$(basename "${checkpoint}")

    # Create archive
    tar -czf "${ARCHIVE_DIR}/${checkpoint_name}.tar.gz" \
        -C "${CHECKPOINT_DIR}" "${checkpoint_name}"

    if [ $? -eq 0 ]; then
        # Verify archive
        if tar -tzf "${ARCHIVE_DIR}/${checkpoint_name}.tar.gz" > /dev/null 2>&1; then
            # Archive verified, remove original
            rm -rf "${checkpoint}"
            echo "Archived: ${checkpoint_name}"
        else
            echo "ERROR: Failed to archive ${checkpoint_name}"
        fi
    fi
done

echo "Checkpoint archival completed"
```

---

## Configuration Backup

### Essential Configuration Files

```python
#!/usr/bin/env python3
# backup_configuration.py - Backup all configuration files

import os
import shutil
import json
from datetime import datetime
from pathlib import Path

class ConfigurationBackup:
    def __init__(self, backup_dir: str = "./backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def backup_config(self, config_dir: str = "./config") -> dict:
        """Backup all configuration files."""

        result = {
            "timestamp": self.timestamp,
            "files_backed_up": [],
            "files_failed": [],
            "total_size": 0
        }

        config_path = Path(config_dir)
        if not config_path.exists():
            result["error"] = f"Config directory not found: {config_dir}"
            return result

        # Create backup directory
        backup_name = f"config_{self.timestamp}"
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)

        # Backup all YAML files
        for yaml_file in config_path.glob("*.yaml"):
            try:
                shutil.copy2(yaml_file, backup_path / yaml_file.name)
                result["files_backed_up"].append(yaml_file.name)
                result["total_size"] += yaml_file.stat().st_size
            except Exception as e:
                result["files_failed"].append({
                    "file": yaml_file.name,
                    "error": str(e)
                })

        # Backup JSON files
        for json_file in config_path.glob("*.json"):
            try:
                shutil.copy2(json_file, backup_path / json_file.name)
                result["files_backed_up"].append(json_file.name)
                result["total_size"] += json_file.stat().st_size
            except Exception as e:
                result["files_failed"].append({
                    "file": json_file.name,
                    "error": str(e)
                })

        # Backup environment variables if .env exists
        if Path(".env").exists():
            try:
                shutil.copy2(".env", backup_path / ".env")
                result["files_backed_up"].append(".env")
                result["total_size"] += Path(".env").stat().st_size
            except Exception as e:
                result["files_failed"].append({
                    "file": ".env",
                    "error": str(e)
                })

        # Create archive
        archive_path = self.backup_dir / f"{backup_name}.tar.gz"
        shutil.make_archive(str(archive_path.with_suffix('')), 'gztar',
                          str(backup_path.parent), backup_name)

        # Cleanup temporary directory
        shutil.rmtree(backup_path)

        result["archive_path"] = str(archive_path)
        result["archive_size"] = archive_path.stat().st_size

        return result

# Usage
if __name__ == "__main__":
    backup = ConfigurationBackup()
    result = backup.backup_config()
    print(json.dumps(result, indent=2))
```

### Environment Variables Backup

```bash
#!/bin/bash
# backup_env.sh - Backup environment variables securely

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ENV_BACKUP="${BACKUP_DIR}/.env.backup.${TIMESTAMP}"

mkdir -p "${BACKUP_DIR}"

# Copy .env file
if [ -f ".env" ]; then
    cp ".env" "${ENV_BACKUP}"
    # Restrict permissions
    chmod 600 "${ENV_BACKUP}"
    echo "Environment backup: ${ENV_BACKUP}"
else
    echo "WARNING: .env file not found"
fi

# Create encrypted backup with GPG (if available)
if command -v gpg &> /dev/null; then
    gpg --symmetric --cipher-algo AES256 \
        --output "${ENV_BACKUP}.gpg" \
        "${ENV_BACKUP}"

    if [ $? -eq 0 ]; then
        echo "Encrypted backup: ${ENV_BACKUP}.gpg"
        # Securely delete original
        shred -vfz "${ENV_BACKUP}" 2>/dev/null || rm "${ENV_BACKUP}"
    fi
fi
```

---

## Backup Automation

### Cron Job Examples

#### Linux/macOS Cron Jobs

```bash
# Backup crontab entries for TBCV
# crontab -e

# Hourly database backup (5 AM each hour)
5 * * * * /opt/tbcv/scripts/backup_sqlite.sh >> /var/log/tbcv_backup.log 2>&1

# Daily configuration backup (3 AM)
0 3 * * * /opt/tbcv/scripts/backup_configuration.py >> /var/log/tbcv_backup.log 2>&1

# Weekly truth data backup (Sunday at 2 AM)
0 2 * * 0 /opt/tbcv/scripts/backup_truth_data.sh >> /var/log/tbcv_backup.log 2>&1

# Checkpoint cleanup - keep 7 days (Daily at 1 AM)
0 1 * * * /opt/tbcv/scripts/checkpoint_retention.py >> /var/log/tbcv_cleanup.log 2>&1

# Backup verification (every 6 hours)
0 */6 * * * /opt/tbcv/scripts/verify_backup.py /opt/tbcv/backups/latest.db >> /var/log/tbcv_verify.log 2>&1

# Backup to cloud storage (Daily at 4 AM)
0 4 * * * /opt/tbcv/scripts/backup_to_s3.sh >> /var/log/tbcv_cloud_backup.log 2>&1
```

#### Windows Task Scheduler

```powershell
# backup_scheduler.ps1 - Windows backup scheduling

# Hourly database backup
$trigger = New-ScheduledTaskTrigger -AtStartup -RepetitionInterval (New-TimeSpan -Hours 1)
$action = New-ScheduledTaskAction -Execute "python" -Argument "C:\tbcv\scripts\backup_sqlite.py"
Register-ScheduledTask -TaskName "TBCV_Backup_SQLite" -Trigger $trigger -Action $action -RunLevel Highest

# Daily configuration backup at 3 AM
$trigger = New-ScheduledTaskTrigger -Daily -At 03:00
$action = New-ScheduledTaskAction -Execute "python" -Argument "C:\tbcv\scripts\backup_configuration.py"
Register-ScheduledTask -TaskName "TBCV_Backup_Config" -Trigger $trigger -Action $action -RunLevel Highest

# Checkpoint cleanup daily at 1 AM
$trigger = New-ScheduledTaskTrigger -Daily -At 01:00
$action = New-ScheduledTaskAction -Execute "python" -Argument "C:\tbcv\scripts\checkpoint_retention.py"
Register-ScheduledTask -TaskName "TBCV_Cleanup_Checkpoints" -Trigger $trigger -Action $action -RunLevel Highest
```

### Backup Monitoring and Alerts

```python
#!/usr/bin/env python3
# backup_monitor.py - Monitor backup job status and health

import os
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

class BackupMonitor:
    def __init__(self, backup_dir: str = "./backups"):
        self.backup_dir = Path(backup_dir)

    def check_backup_freshness(self,
                              max_age_hours: int = 25) -> Dict[str, bool]:
        """Check if backups are recent enough."""

        result = {
            "checks_passed": True,
            "backups": {}
        }

        now = datetime.now()

        # Find latest backups by type
        backup_types = {
            "database": "tbcv_*.db*",
            "config": "config_*.tar.gz",
            "truth_data": "truth_data_*.tar.gz"
        }

        for backup_type, pattern in backup_types.items():
            latest = None
            for backup_file in self.backup_dir.glob(pattern):
                if backup_file.is_file():
                    if latest is None or backup_file.stat().st_mtime > latest[1]:
                        latest = (backup_file, backup_file.stat().st_mtime)

            if latest:
                backup_time = datetime.fromtimestamp(latest[1])
                age_hours = (now - backup_time).total_seconds() / 3600
                is_fresh = age_hours < max_age_hours

                result["backups"][backup_type] = {
                    "path": str(latest[0]),
                    "age_hours": round(age_hours, 2),
                    "is_fresh": is_fresh,
                    "timestamp": backup_time.isoformat()
                }

                if not is_fresh:
                    result["checks_passed"] = False
            else:
                result["backups"][backup_type] = {
                    "path": None,
                    "is_fresh": False,
                    "error": "No backup found"
                }
                result["checks_passed"] = False

        return result

    def check_backup_space(self) -> Dict[str, any]:
        """Check available storage space."""

        result = {
            "total_backups_size_mb": 0,
            "total_backups_size_gb": 0,
            "backup_count": 0,
            "disk_usage": None
        }

        if not self.backup_dir.exists():
            return result

        total_size = 0
        file_count = 0

        for file in self.backup_dir.rglob("*"):
            if file.is_file():
                total_size += file.stat().st_size
                file_count += 1

        result["total_backups_size_mb"] = round(total_size / 1024 / 1024, 2)
        result["total_backups_size_gb"] = round(total_size / 1024 / 1024 / 1024, 2)
        result["backup_count"] = file_count

        # Get disk usage statistics
        try:
            stat_result = os.statvfs(str(self.backup_dir))
            total_disk = stat_result.f_blocks * stat_result.f_frsize / 1024 / 1024 / 1024
            free_disk = stat_result.f_bavail * stat_result.f_frsize / 1024 / 1024 / 1024
            used_percent = 100 * (total_disk - free_disk) / total_disk

            result["disk_usage"] = {
                "total_gb": round(total_disk, 2),
                "free_gb": round(free_disk, 2),
                "used_percent": round(used_percent, 2)
            }
        except:
            pass

        return result

    def send_alert(self, message: str, severity: str = "warning"):
        """Send alert notification."""

        alert = {
            "timestamp": datetime.now().isoformat(),
            "severity": severity,
            "message": message
        }

        # Log to file
        log_path = self.backup_dir.parent / "backup_alerts.log"
        with open(log_path, "a") as f:
            f.write(json.dumps(alert) + "\n")

        # Could also send email, webhook, etc.
        print(f"[{severity.upper()}] {message}")

# Usage
if __name__ == "__main__":
    monitor = BackupMonitor()

    # Check freshness
    freshness = monitor.check_backup_freshness(max_age_hours=25)
    print("Backup Freshness:")
    print(json.dumps(freshness, indent=2))

    # Check space
    space = monitor.check_backup_space()
    print("\nBackup Storage:")
    print(json.dumps(space, indent=2))

    # Alert if backups are stale
    if not freshness["checks_passed"]:
        monitor.send_alert("Stale backups detected!", severity="warning")

    # Alert if low disk space
    if space["disk_usage"] and space["disk_usage"]["used_percent"] > 80:
        monitor.send_alert(
            f"Low disk space: {space['disk_usage']['used_percent']}% used",
            severity="critical"
        )
```

### Cloud Storage Backup (AWS S3)

```python
#!/usr/bin/env python3
# backup_to_s3.py - Backup files to AWS S3

import boto3
import os
import json
from datetime import datetime
from pathlib import Path

class S3Backup:
    def __init__(self, bucket_name: str, region: str = "us-east-1"):
        self.s3_client = boto3.client('s3', region_name=region)
        self.bucket_name = bucket_name

    def backup_file(self, local_path: str, s3_key: str = None) -> dict:
        """Upload a file to S3."""

        if s3_key is None:
            s3_key = Path(local_path).name

        try:
            self.s3_client.upload_file(
                local_path,
                self.bucket_name,
                s3_key,
                ExtraArgs={'ServerSideEncryption': 'AES256'}
            )

            return {
                "status": "success",
                "local_path": local_path,
                "s3_key": s3_key,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "failed",
                "local_path": local_path,
                "error": str(e)
            }

    def backup_directory(self, local_dir: str, s3_prefix: str = "") -> dict:
        """Upload entire directory to S3."""

        result = {
            "total_files": 0,
            "successful_uploads": 0,
            "failed_uploads": 0,
            "total_bytes": 0,
            "failures": []
        }

        local_path = Path(local_dir)

        for file_path in local_path.rglob("*"):
            if file_path.is_file():
                result["total_files"] += 1

                # Calculate S3 key
                relative_path = file_path.relative_to(local_path)
                if s3_prefix:
                    s3_key = f"{s3_prefix}/{relative_path}"
                else:
                    s3_key = str(relative_path)

                # Upload file
                upload_result = self.backup_file(str(file_path), s3_key)

                if upload_result["status"] == "success":
                    result["successful_uploads"] += 1
                    result["total_bytes"] += file_path.stat().st_size
                else:
                    result["failed_uploads"] += 1
                    result["failures"].append(upload_result)

        return result

    def restore_file(self, s3_key: str, local_path: str) -> dict:
        """Download a file from S3."""

        try:
            self.s3_client.download_file(
                self.bucket_name,
                s3_key,
                local_path
            )

            return {
                "status": "success",
                "s3_key": s3_key,
                "local_path": local_path
            }
        except Exception as e:
            return {
                "status": "failed",
                "s3_key": s3_key,
                "error": str(e)
            }

# Usage
if __name__ == "__main__":
    bucket = os.getenv("BACKUP_S3_BUCKET", "tbcv-backups")
    s3_backup = S3Backup(bucket)

    # Backup database
    db_result = s3_backup.backup_file(
        "./data/tbcv.db",
        f"backups/tbcv_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    )
    print("Database backup:", json.dumps(db_result, indent=2))

    # Backup configuration
    config_result = s3_backup.backup_directory(
        "./config",
        "backups/config"
    )
    print("Config backup:", json.dumps(config_result, indent=2))
```

---

## Restore Procedures

### Full System Restore

```bash
#!/bin/bash
# restore_full_system.sh - Complete system restore from backup

set -e

BACKUP_DIR="./backups"
RESTORE_DB_FILE="./data/tbcv.db"
RESTORE_CONFIG_DIR="./config"

echo "=== TBCV Full System Restore ==="
echo "WARNING: This will overwrite existing data!"
echo "Backup directory: ${BACKUP_DIR}"
read -p "Continue? (yes/no): " confirm

if [ "${confirm}" != "yes" ]; then
    echo "Restore cancelled"
    exit 0
fi

# Restore database
echo "Restoring database..."
if [ ! -f "${RESTORE_DB_FILE}" ]; then
    # Find latest database backup
    LATEST_DB=$(ls -t ${BACKUP_DIR}/tbcv_*.db* 2>/dev/null | head -1)
    if [ -z "${LATEST_DB}" ]; then
        echo "ERROR: No database backup found"
        exit 1
    fi

    # Handle compressed backup
    if [ "${LATEST_DB}" = *.gz ]; then
        gunzip -c "${LATEST_DB}" > "${RESTORE_DB_FILE}"
    else
        cp "${LATEST_DB}" "${RESTORE_DB_FILE}"
    fi
fi

echo "Database restored: ${RESTORE_DB_FILE}"

# Restore configuration
echo "Restoring configuration..."
if [ -d "${BACKUP_DIR}/config" ]; then
    cp -r "${BACKUP_DIR}/config/"* "${RESTORE_CONFIG_DIR}/"
    echo "Configuration restored"
fi

# Restore environment variables
if [ -f "${BACKUP_DIR}/.env" ]; then
    cp "${BACKUP_DIR}/.env" "./.env"
    echo "Environment variables restored"
fi

echo "=== Restore Complete ==="
```

### Database-Only Restore

```python
#!/usr/bin/env python3
# restore_database.py - Restore database from backup

import os
import sys
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime

def restore_database(backup_path: str, restore_to: str = "./data/tbcv.db") -> bool:
    """Restore database from backup file."""

    if not os.path.exists(backup_path):
        print(f"ERROR: Backup file not found: {backup_path}")
        return False

    # Verify backup
    print(f"Verifying backup: {backup_path}")
    try:
        conn = sqlite3.connect(backup_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check;")
        result = cursor.fetchone()
        conn.close()

        if result[0] != "ok":
            print(f"ERROR: Backup verification failed: {result[0]}")
            return False
    except Exception as e:
        print(f"ERROR: Could not verify backup: {e}")
        return False

    # Backup current database
    if os.path.exists(restore_to):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_current = f"{restore_to}.backup.{timestamp}"
        shutil.copy2(restore_to, backup_current)
        print(f"Current database backed up: {backup_current}")

    # Restore
    try:
        shutil.copy2(backup_path, restore_to)
        print(f"Database restored: {restore_to}")

        # Verify restored database
        conn = sqlite3.connect(restore_to)
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM workflows;")
        workflow_count = cursor.fetchone()[0]
        conn.close()

        print(f"Verification: {workflow_count} workflows in restored database")
        return True
    except Exception as e:
        print(f"ERROR: Restore failed: {e}")
        return False

def list_available_backups(backup_dir: str = "./backups") -> list:
    """List available database backups."""

    backups = []
    backup_path = Path(backup_dir)

    if not backup_path.exists():
        return backups

    for backup_file in sorted(backup_path.glob("tbcv_*.db*"), reverse=True):
        stat = backup_file.stat()
        backups.append({
            "file": str(backup_file),
            "size_mb": stat.st_size / 1024 / 1024,
            "mtime": datetime.fromtimestamp(stat.st_mtime).isoformat()
        })

    return backups

# Usage
if __name__ == "__main__":
    import json

    # List available backups
    backups = list_available_backups()
    print("Available backups:")
    for idx, backup in enumerate(backups):
        print(f"{idx}: {backup['file']} ({backup['size_mb']:.2f} MB) - {backup['mtime']}")

    if not backups:
        print("No backups available")
        sys.exit(1)

    # Restore from first argument or latest
    if len(sys.argv) > 1:
        backup_path = sys.argv[1]
    else:
        backup_path = backups[0]["file"]

    print(f"\nRestoring from: {backup_path}")
    success = restore_database(backup_path)
    sys.exit(0 if success else 1)
```

### Point-in-Time Recovery

```bash
#!/bin/bash
# restore_point_in_time.sh - Restore to specific point in time

TARGET_DATE="2024-12-03 14:30:00"
BACKUP_DIR="./backups"

echo "Finding backup for: ${TARGET_DATE}"

# Find backups around target date
find "${BACKUP_DIR}" -name "tbcv_*.db*" -type f -newer \
    <(touch -d "${TARGET_DATE}" /tmp/target_time) \
    -print | while read backup; do
    echo "Suitable backup: ${backup}"
done

# Alternative: Extract from timestamped backup name
SEARCH_DATE=$(date -d "${TARGET_DATE}" +"%Y%m%d_%H%M")
BACKUPS=$(ls -1 "${BACKUP_DIR}"/tbcv_${SEARCH_DATE}* 2>/dev/null)

if [ -z "${BACKUPS}" ]; then
    echo "No suitable backup found for ${TARGET_DATE}"
    exit 1
fi

echo "Found backup: ${BACKUPS}"
```

---

## Disaster Recovery

### Disaster Recovery Plan

#### Level 1: Data Corruption (RPO: 1 hour, RTO: 1 hour)

**Symptoms**: Database integrity errors, missing records

**Recovery Steps**:
1. Stop application
2. Restore from latest backup (< 1 hour old)
3. Verify data integrity
4. Resume application
5. Run validation workflow on key files

#### Level 2: Hardware Failure (RPO: 1 day, RTO: 4 hours)

**Symptoms**: Server not accessible, disk failure

**Recovery Steps**:
1. Provision new hardware/cloud instance
2. Install TBCV application
3. Restore database from latest backup
4. Restore configuration from backup
5. Restore checkpoints (optional, for workflow recovery)
6. Update DNS/routing to new instance
7. Run full validation suite

#### Level 3: Site Failure (RPO: varies, RTO: varies)

**Symptoms**: Entire data center down

**Recovery Steps**:
1. Activate disaster recovery site (hot standby or cold backup)
2. Restore all data from offsite backups
3. Reconfigure application servers
4. Test all services
5. Switch production traffic

### Failover Procedures

```bash
#!/bin/bash
# failover_to_dr.sh - Failover to disaster recovery site

echo "=== Initiating Failover to DR Site ==="

# Step 1: Notify operations
echo "Step 1: Notifying operations team..."
# curl -X POST https://ops-incident/api/failover/start

# Step 2: Stop primary application
echo "Step 2: Stopping primary TBCV instance..."
systemctl stop tbcv || true

# Step 3: Restore from offsite backup
echo "Step 3: Restoring from DR backup location..."
DR_BACKUP_URL="s3://dr-backups/tbcv/latest.db"
aws s3 cp "${DR_BACKUP_URL}" ./data/tbcv.db

# Step 4: Verify restored database
echo "Step 4: Verifying restored database..."
python3 scripts/verify_backup.py ./data/tbcv.db
if [ $? -ne 0 ]; then
    echo "ERROR: Database verification failed!"
    exit 1
fi

# Step 5: Start application
echo "Step 5: Starting TBCV on DR site..."
systemctl start tbcv

# Step 6: Health check
echo "Step 6: Running health checks..."
sleep 5
curl -f http://localhost:8000/health
if [ $? -eq 0 ]; then
    echo "DR failover SUCCESSFUL"
else
    echo "ERROR: Health check failed!"
    exit 1
fi

echo "=== Failover Complete ==="
```

---

## Backup Best Practices

### Backup Frequency Recommendations

```
Database:
- Frequency: Hourly
- Retention: 7 days (168 backups)
- Total Space: 500 MB/hour * 168 = ~80 GB

Configuration:
- Frequency: Daily (or on change)
- Retention: 30 days
- Total Space: ~50 MB * 30 = ~1.5 GB

Truth Data:
- Frequency: Daily
- Retention: 30 days
- Total Space: ~100 MB * 30 = ~3 GB

Checkpoints:
- Frequency: Automatic (per workflow)
- Retention: 7 days
- Total Space: ~50 MB * 50 checkpoints = ~2.5 GB

Total Recommended Storage: ~90 GB for on-site + offsite

```

### Off-Site Backup Storage

```python
#!/usr/bin/env python3
# offsite_backup_sync.py - Sync backups to offsite location

import os
import subprocess
from pathlib import Path
from datetime import datetime

class OffsiteBackupSync:
    def __init__(self, local_backup_dir: str, remote_location: str):
        self.local_dir = Path(local_backup_dir)
        self.remote_location = remote_location  # s3://bucket or /mnt/nfs_backup

    def sync_to_s3(self) -> dict:
        """Sync backups to AWS S3."""

        cmd = [
            "aws", "s3", "sync",
            str(self.local_dir),
            self.remote_location,
            "--delete",
            "--exclude", "*.tmp",
            "--storage-class", "GLACIER"  # Use cheaper storage for archives
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        return {
            "status": "success" if result.returncode == 0 else "failed",
            "command": " ".join(cmd),
            "stdout": result.stdout,
            "stderr": result.stderr,
            "timestamp": datetime.now().isoformat()
        }

    def sync_to_nfs(self) -> dict:
        """Sync backups to NFS mount."""

        # Verify NFS is mounted
        mount_check = subprocess.run(
            ["mountpoint", self.remote_location],
            capture_output=True
        )

        if mount_check.returncode != 0:
            return {
                "status": "failed",
                "error": f"NFS not mounted at {self.remote_location}"
            }

        cmd = [
            "rsync", "-avz", "--delete",
            str(self.local_dir) + "/",
            self.remote_location + "/"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        return {
            "status": "success" if result.returncode == 0 else "failed",
            "command": " ".join(cmd),
            "stdout": result.stdout,
            "timestamp": datetime.now().isoformat()
        }

    def verify_offsite_backups(self) -> dict:
        """Verify backups exist in offsite location."""

        # For S3
        if self.remote_location.startswith("s3://"):
            cmd = ["aws", "s3", "ls", self.remote_location, "--recursive"]
            result = subprocess.run(cmd, capture_output=True, text=True)

            file_count = len(result.stdout.strip().split("\n"))
            return {
                "status": "success",
                "file_count": file_count,
                "location": self.remote_location
            }

        # For NFS
        else:
            if os.path.exists(self.remote_location):
                file_count = sum(1 for _ in Path(self.remote_location).rglob("*"))
                return {
                    "status": "success",
                    "file_count": file_count,
                    "location": self.remote_location
                }
            else:
                return {
                    "status": "failed",
                    "error": f"Location not found: {self.remote_location}"
                }
```

### Backup Encryption

```bash
#!/bin/bash
# backup_with_encryption.sh - Create encrypted backups

BACKUP_DIR="./backups"
DB_FILE="./data/tbcv.db"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="tbcv_${TIMESTAMP}"

mkdir -p "${BACKUP_DIR}"

# Create backup
cp "${DB_FILE}" "${BACKUP_DIR}/${BACKUP_NAME}.db"

# Encrypt with GPG
gpg --symmetric \
    --cipher-algo AES256 \
    --output "${BACKUP_DIR}/${BACKUP_NAME}.db.gpg" \
    "${BACKUP_DIR}/${BACKUP_NAME}.db"

# Remove unencrypted backup
rm "${BACKUP_DIR}/${BACKUP_NAME}.db"

echo "Encrypted backup: ${BACKUP_DIR}/${BACKUP_NAME}.db.gpg"

# To decrypt and restore:
# gpg --output tbcv.db --decrypt tbcv_YYYYMMDD_HHMMSS.db.gpg
```

### Backup Testing Schedule

```yaml
# backup_test_schedule.yaml
# Regular backup restoration testing

backup_test_schedule:

  # Weekly full restoration test (Friday night)
  weekly_full_test:
    frequency: "0 22 * * 5"  # Friday 10 PM
    action: "restore_latest_backup_to_test_environment"
    verify:
      - database_integrity
      - table_row_counts
      - index_integrity
    notify: "ops-team@company.com"

  # Monthly point-in-time recovery test (1st of month)
  monthly_pitr_test:
    frequency: "0 23 1 * *"  # 1st at 11 PM
    action: "restore_30_days_old_backup"
    verify:
      - data_consistency
      - missing_recent_records
    notify: "ops-team@company.com"

  # Quarterly full site recovery test
  quarterly_dr_test:
    frequency: "0 0 1 */3 0"  # Quarterly, midnight
    action: "failover_to_dr_site"
    duration: "4 hours"
    verify:
      - all_systems_operational
      - data_sync_complete
      - dns_updated
    notify: "full-team@company.com"
```

### Retention Policies

```
Backup Retention Schedule:

7-Day Retention (Recent):
- Daily backups kept for 7 days
- Quick recovery for recent issues
- ~500 MB/day * 7 = 3.5 GB storage

30-Day Retention (Monthly):
- Full backup on 1st of each month
- 1 backup per week for other weeks
- ~1 GB/week * 4 = 4 GB storage

Annual Retention (Archival):
- Full backup on Jan 1st
- Stored in cold storage (Glacier)
- ~80 GB compressed

Total Storage:
- Hot (7-day): 3.5 GB
- Warm (30-day): 4 GB
- Cold (annual): 80 GB (Glacier)
- Total: 87.5 GB
- Cost: ~$2-3/month
```

---

## Recovery Scenarios

### Scenario 1: Database Corruption

**Problem**: Database integrity check fails

**Steps**:
```bash
#!/bin/bash
# Scenario 1: Database Corruption Recovery

echo "Database Corruption Detected"

# Step 1: Verify corruption
sqlite3 data/tbcv.db "PRAGMA integrity_check;"

# Step 2: Find backup from before corruption
ls -lt backups/tbcv_*.db | head -5

# Step 3: Restore from backup
cp backups/tbcv_20240103_140000.db data/tbcv.db

# Step 4: Verify restored database
sqlite3 data/tbcv.db "PRAGMA integrity_check;"

# Step 5: Run integrity checks
sqlite3 data/tbcv.db "PRAGMA quick_check;"
sqlite3 data/tbcv.db "ANALYZE;"

echo "Database recovery complete"
```

### Scenario 2: Accidental Data Deletion

**Problem**: Important records were deleted

**Steps**:
1. Stop application immediately
2. Find backup from before deletion
3. Query backup to identify deleted records
4. Restore specific records (if possible) or full database
5. Resume application with verification

### Scenario 3: Hardware Failure

**Problem**: Server hardware failed

**Steps**:
1. Provision new server
2. Install TBCV
3. Restore database from S3 backup
4. Restore configuration
5. Update DNS records
6. Verify all services

### Scenario 4: Ransomware Attack

**Problem**: All files encrypted

**Steps**:
1. Isolate affected system immediately
2. Activate backup from known-clean time
3. Restore to clean environment
4. Scan for indicators of compromise
5. Update security policies

### Scenario 5: Partial Data Loss

**Problem**: Some records missing, some corrupt

**Steps**:
1. Identify range of data loss
2. Restore from multiple backups
3. Compare versions
4. Recover uncorrupted records
5. Rebuild missing data if possible

---

## Backup Checklist

### Pre-Backup Checklist

- [ ] Application is running normally
- [ ] Database connectivity verified
- [ ] Sufficient disk space available (check `df -h`)
- [ ] Backup directories exist and are writable
- [ ] Recent validation workflows completed successfully
- [ ] No long-running transactions in progress
- [ ] Network connectivity to backup destination working
- [ ] Credentials/tokens for backup services valid
- [ ] Previous backup verification passed
- [ ] Backup monitoring and alerting configured

### Post-Backup Verification Checklist

- [ ] Backup file created successfully
- [ ] Backup file size is reasonable (within expected range)
- [ ] Backup file checksum calculated
- [ ] Database integrity check passed
- [ ] All required tables present
- [ ] Row counts match expectations
- [ ] Backup is accessible from backup location
- [ ] Backup is readable and extractable
- [ ] Backup metadata recorded accurately
- [ ] Backup monitoring confirms completion

### Restore Testing Checklist

- [ ] Test environment isolated from production
- [ ] Latest backup selected for testing
- [ ] Backup file integrity verified
- [ ] Restore process completed successfully
- [ ] Database integrity check passed after restore
- [ ] Row counts verified in restored database
- [ ] Sample records verified for accuracy
- [ ] Application started successfully
- [ ] API endpoints responding
- [ ] Validation workflow executed successfully
- [ ] Results compared with pre-backup state
- [ ] Restore time documented (for RTO planning)

### Monthly Maintenance Checklist

- [ ] Review backup job logs for errors
- [ ] Verify backup storage usage trends
- [ ] Test restore procedure on test environment
- [ ] Test failover procedure if applicable
- [ ] Update backup documentation if needed
- [ ] Review and adjust retention policies
- [ ] Verify offsite backup synchronization
- [ ] Check backup encryption keys are secure
- [ ] Review access logs for backup storage
- [ ] Update disaster recovery contacts
- [ ] Review and test alert notifications

---

## Emergency Contact & Escalation

```
TBCV Backup & Recovery Escalation

Level 1 - Backup Job Failure:
- Contact: DevOps Team
- Response Time: 1 hour
- Action: Check logs, restart job, verify backup

Level 2 - Data Corruption Detected:
- Contact: DBA + DevOps Lead
- Response Time: 15 minutes
- Action: Initiate recovery procedure

Level 3 - Complete System Failure:
- Contact: VP Engineering + Security Lead
- Response Time: Immediate
- Action: Activate disaster recovery plan

Backup Status Dashboard:
- URL: https://ops.company.com/backup-status
- Email Alerts: backup-alerts@company.com
- Slack Channel: #tbcv-backup-alerts
```

---

## Related Documentation

- [Database Schema](./database_schema.md)
- [Deployment Guide](./deployment.md)
- [Production Readiness](./production_readiness.md)
- [Troubleshooting](./troubleshooting.md)
- [Configuration Guide](./configuration.md)

---

**Last Updated**: December 5, 2024
**Version**: 1.0
**Status**: Production Ready
