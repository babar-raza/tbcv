# file: core/performance.py
"""
Performance Optimization Module for TBCV.

Provides:
- Performance metrics collection
- Validation timing and statistics
- Optimization utilities
- Performance monitoring
"""

from __future__ import annotations

import time
import asyncio
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict
import threading

from core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TimingMetric:
    """Single timing measurement."""
    name: str
    start_time: float
    end_time: float = 0.0
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def complete(self):
        """Mark timing as complete."""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000


@dataclass
class PerformanceStats:
    """Aggregated performance statistics."""
    operation: str
    count: int = 0
    total_ms: float = 0.0
    min_ms: float = float('inf')
    max_ms: float = 0.0
    avg_ms: float = 0.0
    last_run: Optional[datetime] = None

    def add_timing(self, duration_ms: float):
        """Add a timing measurement."""
        self.count += 1
        self.total_ms += duration_ms
        self.min_ms = min(self.min_ms, duration_ms)
        self.max_ms = max(self.max_ms, duration_ms)
        self.avg_ms = self.total_ms / self.count
        self.last_run = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "operation": self.operation,
            "count": self.count,
            "total_ms": round(self.total_ms, 2),
            "min_ms": round(self.min_ms, 2) if self.min_ms != float('inf') else 0,
            "max_ms": round(self.max_ms, 2),
            "avg_ms": round(self.avg_ms, 2),
            "last_run": self.last_run.isoformat() if self.last_run else None
        }


class PerformanceMonitor:
    """
    Monitors and collects performance metrics.

    Thread-safe collection of timing data across all validators and operations.
    """

    def __init__(self):
        self._stats: Dict[str, PerformanceStats] = defaultdict(lambda: PerformanceStats(""))
        self._lock = threading.RLock()
        self._active_timings: Dict[str, TimingMetric] = {}

    def start_timing(self, operation: str, **metadata) -> str:
        """
        Start timing an operation.

        Args:
            operation: Name of the operation being timed
            **metadata: Additional metadata to store

        Returns:
            Timing ID for later completion
        """
        timing_id = f"{operation}_{time.time()}"
        timing = TimingMetric(
            name=operation,
            start_time=time.time(),
            metadata=metadata
        )
        with self._lock:
            self._active_timings[timing_id] = timing
        return timing_id

    def end_timing(self, timing_id: str) -> Optional[float]:
        """
        End timing an operation.

        Args:
            timing_id: ID returned from start_timing

        Returns:
            Duration in milliseconds, or None if timing not found
        """
        with self._lock:
            timing = self._active_timings.pop(timing_id, None)
            if timing:
                timing.complete()
                # Update stats
                if timing.name not in self._stats:
                    self._stats[timing.name] = PerformanceStats(timing.name)
                self._stats[timing.name].add_timing(timing.duration_ms)
                return timing.duration_ms
        return None

    def record_timing(self, operation: str, duration_ms: float, **metadata):
        """
        Record a timing measurement directly.

        Args:
            operation: Name of the operation
            duration_ms: Duration in milliseconds
            **metadata: Additional metadata
        """
        with self._lock:
            if operation not in self._stats:
                self._stats[operation] = PerformanceStats(operation)
            self._stats[operation].add_timing(duration_ms)

    def get_stats(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """
        Get performance statistics.

        Args:
            operation: Optional specific operation to get stats for

        Returns:
            Dict with stats for all or specified operation
        """
        with self._lock:
            if operation:
                stats = self._stats.get(operation)
                return stats.to_dict() if stats else {}
            return {name: stats.to_dict() for name, stats in self._stats.items()}

    def get_slowest_operations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the slowest operations by average time.

        Args:
            limit: Maximum number of operations to return

        Returns:
            List of stats dicts sorted by avg_ms descending
        """
        with self._lock:
            sorted_stats = sorted(
                self._stats.values(),
                key=lambda s: s.avg_ms,
                reverse=True
            )
            return [s.to_dict() for s in sorted_stats[:limit]]

    def clear_stats(self):
        """Clear all statistics."""
        with self._lock:
            self._stats.clear()
            self._active_timings.clear()


class ValidationProfiler:
    """
    Profiles validation execution for performance analysis.

    Tracks timing for each validator and provides optimization insights.
    """

    def __init__(self, monitor: Optional[PerformanceMonitor] = None):
        self.monitor = monitor or performance_monitor
        self._validator_timings: Dict[str, List[float]] = defaultdict(list)
        self._tier_timings: Dict[str, List[float]] = defaultdict(list)

    def profile_validator(self, validator_id: str):
        """
        Context manager for profiling a validator.

        Usage:
            with profiler.profile_validator("yaml"):
                result = await validator.validate(content, context)
        """
        return ValidatorProfileContext(self, validator_id)

    def record_validator_timing(self, validator_id: str, duration_ms: float):
        """Record timing for a specific validator."""
        self._validator_timings[validator_id].append(duration_ms)
        self.monitor.record_timing(f"validator.{validator_id}", duration_ms)

    def record_tier_timing(self, tier: str, duration_ms: float):
        """Record timing for a tier execution."""
        self._tier_timings[tier].append(duration_ms)
        self.monitor.record_timing(f"tier.{tier}", duration_ms)

    def get_validator_stats(self) -> Dict[str, Dict[str, float]]:
        """Get statistics per validator."""
        stats = {}
        for validator_id, timings in self._validator_timings.items():
            if timings:
                stats[validator_id] = {
                    "count": len(timings),
                    "total_ms": sum(timings),
                    "avg_ms": sum(timings) / len(timings),
                    "min_ms": min(timings),
                    "max_ms": max(timings)
                }
        return stats

    def get_tier_stats(self) -> Dict[str, Dict[str, float]]:
        """Get statistics per tier."""
        stats = {}
        for tier, timings in self._tier_timings.items():
            if timings:
                stats[tier] = {
                    "count": len(timings),
                    "total_ms": sum(timings),
                    "avg_ms": sum(timings) / len(timings),
                    "min_ms": min(timings),
                    "max_ms": max(timings)
                }
        return stats

    def get_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """
        Analyze timings and provide optimization suggestions.

        Returns:
            List of suggestions with priority and description
        """
        suggestions = []
        validator_stats = self.get_validator_stats()

        for validator_id, stats in validator_stats.items():
            avg_ms = stats.get("avg_ms", 0)

            # Slow validator warning
            if avg_ms > 1000:  # > 1 second
                suggestions.append({
                    "priority": "high",
                    "validator": validator_id,
                    "issue": "slow_validator",
                    "avg_ms": avg_ms,
                    "suggestion": f"Consider caching or optimizing {validator_id} - avg time {avg_ms:.0f}ms"
                })
            elif avg_ms > 500:  # > 500ms
                suggestions.append({
                    "priority": "medium",
                    "validator": validator_id,
                    "issue": "moderate_latency",
                    "avg_ms": avg_ms,
                    "suggestion": f"Monitor {validator_id} performance - avg time {avg_ms:.0f}ms"
                })

            # High variance warning
            if stats.get("count", 0) >= 5:
                variance = stats.get("max_ms", 0) - stats.get("min_ms", 0)
                if variance > stats.get("avg_ms", 0):
                    suggestions.append({
                        "priority": "low",
                        "validator": validator_id,
                        "issue": "high_variance",
                        "variance_ms": variance,
                        "suggestion": f"High timing variance in {validator_id} - may indicate inconsistent load"
                    })

        return sorted(suggestions, key=lambda s: {"high": 0, "medium": 1, "low": 2}[s["priority"]])


class ValidatorProfileContext:
    """Context manager for profiling validator execution."""

    def __init__(self, profiler: ValidationProfiler, validator_id: str):
        self.profiler = profiler
        self.validator_id = validator_id
        self.start_time = 0.0

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000
        self.profiler.record_validator_timing(self.validator_id, duration_ms)
        return False

    async def __aenter__(self):
        self.start_time = time.time()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000
        self.profiler.record_validator_timing(self.validator_id, duration_ms)
        return False


def timed(operation_name: Optional[str] = None):
    """
    Decorator to time function execution.

    Args:
        operation_name: Optional name for the operation (defaults to function name)
    """
    def decorator(func):
        name = operation_name or func.__name__

        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                duration_ms = (time.time() - start) * 1000
                performance_monitor.record_timing(name, duration_ms)

        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                duration_ms = (time.time() - start) * 1000
                performance_monitor.record_timing(name, duration_ms)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# Batch processing utilities
async def run_with_concurrency_limit(
    tasks: List[Callable],
    limit: int = 5,
    timeout: Optional[float] = None
) -> List[Any]:
    """
    Run async tasks with a concurrency limit.

    Args:
        tasks: List of async callables
        limit: Maximum concurrent tasks
        timeout: Optional timeout per task

    Returns:
        List of results in order
    """
    semaphore = asyncio.Semaphore(limit)

    async def limited_task(task):
        async with semaphore:
            if timeout:
                return await asyncio.wait_for(task(), timeout=timeout)
            return await task()

    return await asyncio.gather(*[limited_task(t) for t in tasks], return_exceptions=True)


def batch_process(items: List[Any], batch_size: int = 100):
    """
    Generator to process items in batches.

    Args:
        items: List of items to batch
        batch_size: Size of each batch

    Yields:
        Batches of items
    """
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]


# Global instances
performance_monitor = PerformanceMonitor()
validation_profiler = ValidationProfiler(performance_monitor)
