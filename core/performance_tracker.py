"""Performance metrics tracking for TBCV MCP operations."""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from collections import defaultdict

from core.logging import get_logger

logger = get_logger(__name__)


class PerformanceTracker:
    """Tracks performance metrics for system operations."""

    def __init__(self, metrics_file: str = ".performance_metrics.jsonl"):
        """
        Initialize performance tracker.

        Args:
            metrics_file: Path to metrics file (JSONL format)
        """
        self.metrics_file = Path(metrics_file)
        self.metrics_file.touch(exist_ok=True)

    def record_operation(
        self,
        operation: str,
        duration_ms: float,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record an operation's performance.

        Args:
            operation: Operation name
            duration_ms: Duration in milliseconds
            success: Whether operation succeeded
            metadata: Additional metadata
        """
        metric_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "operation": operation,
            "duration_ms": duration_ms,
            "success": success,
            "metadata": metadata or {}
        }

        try:
            with open(self.metrics_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(metric_entry) + '\n')
        except Exception as e:
            logger.error(f"Failed to record performance metric: {e}")

    def get_report(
        self,
        time_range: str = "24h",
        operation: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get performance report for time range.

        Args:
            time_range: Time range (1h, 24h, 7d, 30d)
            operation: Filter by operation name

        Returns:
            Performance report dictionary
        """
        # Parse time range
        hours_map = {"1h": 1, "24h": 24, "7d": 168, "30d": 720}
        hours = hours_map.get(time_range, 24)

        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        cutoff_iso = cutoff.isoformat()

        # Collect metrics
        metrics = defaultdict(list)
        total_operations = 0
        failed_operations = 0

        if not self.metrics_file.exists():
            return {
                "time_range": time_range,
                "total_operations": 0,
                "failed_operations": 0,
                "success_rate": 0.0,
                "operations": {}
            }

        try:
            with open(self.metrics_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())

                        # Filter by time
                        if entry.get("timestamp", "") < cutoff_iso:
                            continue

                        # Filter by operation
                        if operation and entry.get("operation") != operation:
                            continue

                        op_name = entry["operation"]
                        duration = entry["duration_ms"]
                        success = entry.get("success", True)

                        metrics[op_name].append(duration)
                        total_operations += 1
                        if not success:
                            failed_operations += 1

                    except (json.JSONDecodeError, KeyError):
                        continue

        except Exception as e:
            logger.error(f"Failed to read performance metrics: {e}")

        # Calculate statistics
        report = {
            "time_range": time_range,
            "total_operations": total_operations,
            "failed_operations": failed_operations,
            "success_rate": (total_operations - failed_operations) / total_operations if total_operations > 0 else 0.0,
            "operations": {}
        }

        for op_name, durations in metrics.items():
            if not durations:
                continue

            durations_sorted = sorted(durations)
            count = len(durations)

            report["operations"][op_name] = {
                "count": count,
                "avg_duration_ms": sum(durations) / count,
                "min_duration_ms": min(durations),
                "max_duration_ms": max(durations),
                "p50_duration_ms": durations_sorted[count // 2] if count > 0 else 0,
                "p95_duration_ms": durations_sorted[int(count * 0.95)] if count > 0 else 0,
                "p99_duration_ms": durations_sorted[int(count * 0.99)] if count > 0 else 0
            }

        return report

    def get_metrics(self, operation: str) -> Dict[str, Any]:
        """Get metrics for specific operation."""
        return self.get_report(time_range="24h", operation=operation)


# Global performance tracker instance
performance_tracker = PerformanceTracker()
