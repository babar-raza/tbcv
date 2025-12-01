# file: tests/core/test_performance.py
"""Tests for Performance Optimization module."""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch

from core.performance import (
    PerformanceMonitor,
    ValidationProfiler,
    TimingMetric,
    PerformanceStats,
    timed,
    run_with_concurrency_limit,
    batch_process
)


# --- TimingMetric Tests ---

class TestTimingMetric:
    """Tests for TimingMetric dataclass."""

    def test_create_timing_metric(self):
        """Should create timing metric."""
        metric = TimingMetric(
            name="test_op",
            start_time=time.time()
        )
        assert metric.name == "test_op"
        assert metric.end_time == 0.0
        assert metric.duration_ms == 0.0

    def test_complete_timing(self):
        """Should calculate duration on complete."""
        start = time.time()
        metric = TimingMetric(name="test", start_time=start)

        time.sleep(0.01)  # 10ms
        metric.complete()

        assert metric.end_time > start
        assert metric.duration_ms > 0


# --- PerformanceStats Tests ---

class TestPerformanceStats:
    """Tests for PerformanceStats dataclass."""

    def test_add_timing(self):
        """Should update stats on add_timing."""
        stats = PerformanceStats(operation="test_op")

        stats.add_timing(100)
        stats.add_timing(200)
        stats.add_timing(300)

        assert stats.count == 3
        assert stats.total_ms == 600
        assert stats.avg_ms == 200
        assert stats.min_ms == 100
        assert stats.max_ms == 300

    def test_to_dict(self):
        """Should convert to dictionary."""
        stats = PerformanceStats(operation="test_op")
        stats.add_timing(100)

        result = stats.to_dict()

        assert result["operation"] == "test_op"
        assert result["count"] == 1
        assert result["total_ms"] == 100
        assert "last_run" in result


# --- PerformanceMonitor Tests ---

class TestPerformanceMonitor:
    """Tests for PerformanceMonitor class."""

    @pytest.fixture
    def monitor(self):
        """Create fresh monitor for each test."""
        return PerformanceMonitor()

    def test_start_and_end_timing(self, monitor):
        """Should track timing of operations."""
        timing_id = monitor.start_timing("test_op")

        time.sleep(0.01)
        duration = monitor.end_timing(timing_id)

        assert duration is not None
        assert duration >= 10  # At least 10ms

    def test_record_timing_directly(self, monitor):
        """Should record timing directly."""
        monitor.record_timing("direct_op", 150)

        stats = monitor.get_stats("direct_op")

        assert stats["count"] == 1
        assert stats["avg_ms"] == 150

    def test_get_stats_all(self, monitor):
        """Should get stats for all operations."""
        monitor.record_timing("op1", 100)
        monitor.record_timing("op2", 200)

        stats = monitor.get_stats()

        assert "op1" in stats
        assert "op2" in stats

    def test_get_stats_specific(self, monitor):
        """Should get stats for specific operation."""
        monitor.record_timing("target_op", 100)

        stats = monitor.get_stats("target_op")

        assert stats["operation"] == "target_op"

    def test_get_slowest_operations(self, monitor):
        """Should return operations sorted by avg time."""
        monitor.record_timing("fast_op", 50)
        monitor.record_timing("slow_op", 500)
        monitor.record_timing("medium_op", 200)

        slowest = monitor.get_slowest_operations(limit=2)

        assert len(slowest) == 2
        assert slowest[0]["operation"] == "slow_op"
        assert slowest[1]["operation"] == "medium_op"

    def test_clear_stats(self, monitor):
        """Should clear all statistics."""
        monitor.record_timing("op1", 100)

        monitor.clear_stats()

        stats = monitor.get_stats()
        assert len(stats) == 0

    def test_end_timing_invalid_id(self, monitor):
        """Should return None for invalid timing ID."""
        duration = monitor.end_timing("invalid_id")
        assert duration is None

    def test_thread_safety(self, monitor):
        """Should handle concurrent access."""
        import threading

        def record_timings():
            for i in range(100):
                monitor.record_timing(f"thread_op_{threading.current_thread().name}", i)

        threads = [threading.Thread(target=record_timings) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should not raise and have recorded data
        stats = monitor.get_stats()
        assert len(stats) == 5


# --- ValidationProfiler Tests ---

class TestValidationProfiler:
    """Tests for ValidationProfiler class."""

    @pytest.fixture
    def profiler(self):
        """Create profiler with fresh monitor."""
        monitor = PerformanceMonitor()
        return ValidationProfiler(monitor)

    def test_profile_validator_context(self, profiler):
        """Should profile validator with context manager."""
        with profiler.profile_validator("yaml"):
            time.sleep(0.01)

        stats = profiler.get_validator_stats()
        assert "yaml" in stats
        assert stats["yaml"]["count"] == 1

    def test_record_validator_timing(self, profiler):
        """Should record validator timing directly."""
        profiler.record_validator_timing("markdown", 150)

        stats = profiler.get_validator_stats()
        assert stats["markdown"]["avg_ms"] == 150

    def test_record_tier_timing(self, profiler):
        """Should record tier timing."""
        profiler.record_tier_timing("tier1", 500)
        profiler.record_tier_timing("tier1", 600)

        stats = profiler.get_tier_stats()
        assert stats["tier1"]["count"] == 2
        assert stats["tier1"]["avg_ms"] == 550

    def test_get_optimization_suggestions_slow(self, profiler):
        """Should suggest optimization for slow validators."""
        # Record a slow validator (> 1000ms)
        for _ in range(5):
            profiler.record_validator_timing("slow_validator", 1500)

        suggestions = profiler.get_optimization_suggestions()

        assert len(suggestions) > 0
        assert suggestions[0]["priority"] == "high"
        assert suggestions[0]["validator"] == "slow_validator"

    def test_get_optimization_suggestions_variance(self, profiler):
        """Should detect high variance."""
        # Record with high variance
        profiler.record_validator_timing("var_validator", 100)
        profiler.record_validator_timing("var_validator", 200)
        profiler.record_validator_timing("var_validator", 300)
        profiler.record_validator_timing("var_validator", 400)
        profiler.record_validator_timing("var_validator", 500)

        suggestions = profiler.get_optimization_suggestions()

        # Should have variance warning
        variance_suggestions = [s for s in suggestions if s["issue"] == "high_variance"]
        assert len(variance_suggestions) > 0


# --- Async Profiler Tests ---

class TestAsyncProfiler:
    """Tests for async profiling."""

    @pytest.fixture
    def profiler(self):
        """Create profiler with fresh monitor."""
        monitor = PerformanceMonitor()
        return ValidationProfiler(monitor)

    @pytest.mark.asyncio
    async def test_async_profile_context(self, profiler):
        """Should profile async operations."""
        async with profiler.profile_validator("async_validator"):
            await asyncio.sleep(0.01)

        stats = profiler.get_validator_stats()
        assert "async_validator" in stats


# --- Timed Decorator Tests ---

class TestTimedDecorator:
    """Tests for @timed decorator."""

    def test_timed_sync_function(self):
        """Should time synchronous function."""
        @timed("sync_test")
        def slow_function():
            time.sleep(0.01)
            return "done"

        result = slow_function()
        assert result == "done"

    @pytest.mark.asyncio
    async def test_timed_async_function(self):
        """Should time async function."""
        @timed("async_test")
        async def async_slow_function():
            await asyncio.sleep(0.01)
            return "done"

        result = await async_slow_function()
        assert result == "done"

    def test_timed_uses_function_name(self):
        """Should use function name when no name provided."""
        @timed()
        def my_named_function():
            return "done"

        result = my_named_function()
        assert result == "done"


# --- Concurrency Limit Tests ---

class TestConcurrencyLimit:
    """Tests for run_with_concurrency_limit."""

    @pytest.mark.asyncio
    async def test_basic_execution(self):
        """Should execute all tasks."""
        results = []

        async def task():
            results.append(1)
            return len(results)

        tasks = [lambda: task() for _ in range(5)]
        await run_with_concurrency_limit(tasks, limit=2)

        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_respects_limit(self):
        """Should respect concurrency limit."""
        concurrent_count = 0
        max_concurrent = 0

        async def task():
            nonlocal concurrent_count, max_concurrent
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            await asyncio.sleep(0.01)
            concurrent_count -= 1
            return True

        tasks = [lambda: task() for _ in range(10)]
        await run_with_concurrency_limit(tasks, limit=3)

        assert max_concurrent <= 3

    @pytest.mark.asyncio
    async def test_handles_exceptions(self):
        """Should handle task exceptions."""
        async def failing_task():
            raise ValueError("test error")

        async def passing_task():
            return "ok"

        tasks = [
            lambda: passing_task(),
            lambda: failing_task(),
            lambda: passing_task()
        ]

        results = await run_with_concurrency_limit(tasks, limit=2)

        assert len(results) == 3
        assert results[0] == "ok"
        assert isinstance(results[1], ValueError)
        assert results[2] == "ok"

    @pytest.mark.asyncio
    async def test_with_timeout(self):
        """Should handle timeouts."""
        async def slow_task():
            await asyncio.sleep(1)
            return "done"

        tasks = [lambda: slow_task()]
        results = await run_with_concurrency_limit(tasks, limit=1, timeout=0.01)

        assert len(results) == 1
        assert isinstance(results[0], asyncio.TimeoutError)


# --- Batch Process Tests ---

class TestBatchProcess:
    """Tests for batch_process utility."""

    def test_basic_batching(self):
        """Should split items into batches."""
        items = list(range(10))

        batches = list(batch_process(items, batch_size=3))

        assert len(batches) == 4
        assert batches[0] == [0, 1, 2]
        assert batches[1] == [3, 4, 5]
        assert batches[2] == [6, 7, 8]
        assert batches[3] == [9]

    def test_exact_batch_size(self):
        """Should handle exact multiples."""
        items = list(range(6))

        batches = list(batch_process(items, batch_size=2))

        assert len(batches) == 3
        assert all(len(b) == 2 for b in batches)

    def test_empty_list(self):
        """Should handle empty list."""
        batches = list(batch_process([], batch_size=10))
        assert len(batches) == 0

    def test_batch_size_larger_than_items(self):
        """Should handle batch size larger than item count."""
        items = [1, 2, 3]

        batches = list(batch_process(items, batch_size=10))

        assert len(batches) == 1
        assert batches[0] == [1, 2, 3]
