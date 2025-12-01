"""Audit logging infrastructure for TBCV MCP operations."""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from core.logging import get_logger

logger = get_logger(__name__)


class AuditLogger:
    """Manages audit logging for system operations."""

    def __init__(self, log_file: str = ".audit_log.jsonl"):
        """
        Initialize audit logger.

        Args:
            log_file: Path to audit log file (JSONL format)
        """
        self.log_file = Path(log_file)
        self.log_file.touch(exist_ok=True)

    def log_operation(
        self,
        operation: str,
        user: str = "system",
        details: Optional[Dict[str, Any]] = None,
        status: str = "success"
    ) -> None:
        """
        Log an operation to the audit log.

        Args:
            operation: Operation name
            user: User or system performing operation
            details: Additional operation details
            status: Operation status (success/failure)
        """
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "operation": operation,
            "user": user,
            "status": status,
            "details": details or {}
        }

        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")

    def get_logs(
        self,
        limit: int = 100,
        offset: int = 0,
        operation: Optional[str] = None,
        user: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get audit logs with filters.

        Args:
            limit: Maximum results to return
            offset: Offset for pagination
            operation: Filter by operation name
            user: Filter by user
            status: Filter by status
            start_date: Filter by start date (ISO format)
            end_date: Filter by end date (ISO format)

        Returns:
            List of audit log entries
        """
        logs = []

        if not self.log_file.exists():
            return []

        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())

                        # Apply filters
                        if operation and entry.get("operation") != operation:
                            continue
                        if user and entry.get("user") != user:
                            continue
                        if status and entry.get("status") != status:
                            continue
                        if start_date and entry.get("timestamp", "") < start_date:
                            continue
                        if end_date and entry.get("timestamp", "") > end_date:
                            continue

                        logs.append(entry)

                    except json.JSONDecodeError:
                        continue

            # Apply pagination
            logs = logs[offset:offset + limit]

            return logs

        except Exception as e:
            logger.error(f"Failed to read audit logs: {e}")
            return []

    def count_logs(
        self,
        operation: Optional[str] = None,
        user: Optional[str] = None,
        status: Optional[str] = None
    ) -> int:
        """Count audit logs matching filters."""
        logs = self.get_logs(
            limit=999999,
            operation=operation,
            user=user,
            status=status
        )
        return len(logs)


# Global audit logger instance
audit_logger = AuditLogger()
