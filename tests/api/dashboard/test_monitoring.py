# file: tbcv/tests/api/dashboard/test_monitoring.py
"""
Tests for performance monitoring dashboard.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

try:
    from api.dashboard.routes_monitoring import (
        _get_system_resources,
        _get_cache_metrics,
        _get_validation_throughput,
        _get_agent_performance,
        _get_database_performance,
        router
    )
except ImportError:
    pytest.skip("Monitoring routes not available", allow_module_level=True)


class TestSystemResources:
    """Tests for system resource metrics."""

    @patch('api.dashboard.routes_monitoring.psutil')
    def test_get_system_resources_success(self, mock_psutil):
        """Test successful system resource retrieval."""
        # Mock psutil responses
        mock_psutil.cpu_percent.return_value = 45.5
        mock_psutil.virtual_memory.return_value = Mock(
            percent=60.2,
            used=8589934592,  # 8GB
            total=17179869184  # 16GB
        )
        mock_psutil.disk_usage.return_value = Mock(
            percent=75.3,
            used=161061273600,  # 150GB
            total=214748364800  # 200GB
        )

        mock_process = Mock()
        mock_process.memory_info.return_value = Mock(rss=536870912)  # 512MB
        mock_process.num_threads.return_value = 8
        mock_psutil.Process.return_value = mock_process

        resources = _get_system_resources()

        assert resources['cpu_percent'] == 45.5
        assert resources['memory_percent'] == 60.2
        assert resources['memory_used_mb'] > 0
        assert resources['memory_total_mb'] > 0
        assert resources['disk_percent'] == 75.3
        assert resources['process_memory_mb'] > 0
        assert resources['active_threads'] == 8
        assert 'timestamp' in resources

    @patch('api.dashboard.routes_monitoring.psutil')
    def test_get_system_resources_error(self, mock_psutil):
        """Test system resource retrieval with error."""
        mock_psutil.cpu_percent.side_effect = Exception("CPU unavailable")

        resources = _get_system_resources()

        assert 'error' in resources
        assert resources['cpu_percent'] == 0


class TestCacheMetrics:
    """Tests for cache performance metrics."""

    @patch('api.dashboard.routes_monitoring.cache_manager')
    def test_get_cache_metrics_success(self, mock_cache):
        """Test successful cache metrics retrieval."""
        mock_cache.get_stats.return_value = {
            "hits": 850,
            "misses": 150,
            "size": 1000,
            "evictions": 50
        }

        metrics = _get_cache_metrics()

        assert metrics['hit_rate'] == 85.0
        assert metrics['total_hits'] == 850
        assert metrics['total_misses'] == 150
        assert metrics['cache_size'] == 1000
        assert metrics['evictions'] == 50
        assert 'timestamp' in metrics

    @patch('api.dashboard.routes_monitoring.cache_manager')
    def test_get_cache_metrics_no_requests(self, mock_cache):
        """Test cache metrics with no requests."""
        mock_cache.get_stats.return_value = {
            "hits": 0,
            "misses": 0,
            "size": 0,
            "evictions": 0
        }

        metrics = _get_cache_metrics()

        assert metrics['hit_rate'] == 0
        assert metrics['total_hits'] == 0
        assert metrics['total_misses'] == 0


class TestValidationThroughput:
    """Tests for validation throughput metrics."""

    @patch('api.dashboard.routes_monitoring.db_manager')
    def test_get_validation_throughput_1h(self, mock_db):
        """Test validation throughput for 1 hour."""
        # Create mock validations
        mock_validations = []
        now = datetime.now(timezone.utc)

        for i in range(120):  # 120 validations in the last hour
            mock_val = Mock()
            mock_val.created_at = now
            mock_val.status = Mock(value='pass')
            mock_validations.append(mock_val)

        mock_db.list_validation_results.return_value = mock_validations

        throughput = _get_validation_throughput("1h")

        assert throughput['total_count'] == 120
        assert throughput['per_minute'] == 2.0
        assert throughput['per_hour'] == 120.0
        assert throughput['success_rate'] == 100.0
        assert throughput['time_range'] == "1h"

    @patch('api.dashboard.routes_monitoring.db_manager')
    def test_get_validation_throughput_mixed_status(self, mock_db):
        """Test validation throughput with mixed statuses."""
        mock_validations = []
        now = datetime.now(timezone.utc)

        # 80 passed, 20 failed
        for i in range(80):
            mock_val = Mock()
            mock_val.created_at = now
            mock_val.status = Mock(value='pass')
            mock_validations.append(mock_val)

        for i in range(20):
            mock_val = Mock()
            mock_val.created_at = now
            mock_val.status = Mock(value='fail')
            mock_validations.append(mock_val)

        mock_db.list_validation_results.return_value = mock_validations

        throughput = _get_validation_throughput("24h")

        assert throughput['total_count'] == 100
        assert throughput['success_rate'] == 80.0


class TestAgentPerformance:
    """Tests for agent performance metrics."""

    @patch('api.dashboard.routes_monitoring.performance_tracker')
    def test_get_agent_performance_success(self, mock_tracker):
        """Test successful agent performance retrieval."""
        mock_tracker.get_report.return_value = {
            "success_rate": 0.95,
            "operations": {
                "agent_validate_content": {
                    "count": 100,
                    "avg_duration_ms": 250.5,
                    "min_duration_ms": 100.0,
                    "max_duration_ms": 500.0,
                    "p50_duration_ms": 240.0,
                    "p95_duration_ms": 450.0,
                    "p99_duration_ms": 490.0
                },
                "agent_enhance_content": {
                    "count": 50,
                    "avg_duration_ms": 350.0,
                    "min_duration_ms": 200.0,
                    "max_duration_ms": 600.0,
                    "p50_duration_ms": 340.0,
                    "p95_duration_ms": 550.0,
                    "p99_duration_ms": 590.0
                }
            }
        }

        performance = _get_agent_performance("24h")

        assert performance['overall_avg_ms'] > 0
        assert performance['total_operations'] == 150
        assert performance['success_rate'] == 95.0
        assert len(performance['agent_metrics']) == 2

    @patch('api.dashboard.routes_monitoring.performance_tracker')
    def test_get_agent_performance_no_data(self, mock_tracker):
        """Test agent performance with no data."""
        mock_tracker.get_report.return_value = {
            "success_rate": 0,
            "operations": {}
        }

        performance = _get_agent_performance("1h")

        assert performance['overall_avg_ms'] == 0
        assert performance['total_operations'] == 0
        assert len(performance['agent_metrics']) == 0


class TestDatabasePerformance:
    """Tests for database performance metrics."""

    @patch('api.dashboard.routes_monitoring.performance_tracker')
    def test_get_database_performance_success(self, mock_tracker):
        """Test successful database performance retrieval."""
        mock_tracker.get_report.return_value = {
            "operations": {
                "db_query_validations": {
                    "count": 200,
                    "avg_duration_ms": 50.5,
                    "min_duration_ms": 10.0,
                    "max_duration_ms": 150.0,
                    "p95_duration_ms": 120.0,
                    "p99_duration_ms": 145.0
                },
                "db_insert_recommendation": {
                    "count": 150,
                    "avg_duration_ms": 35.2,
                    "min_duration_ms": 15.0,
                    "max_duration_ms": 100.0,
                    "p95_duration_ms": 80.0,
                    "p99_duration_ms": 95.0
                }
            }
        }

        performance = _get_database_performance("24h")

        assert performance['overall_avg_ms'] > 0
        assert performance['total_operations'] == 350
        assert len(performance['db_metrics']) == 2


class TestMonitoringEndpoints:
    """Tests for monitoring API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)

        return TestClient(app)

    @patch('api.dashboard.routes_monitoring._get_system_resources')
    @patch('api.dashboard.routes_monitoring._get_cache_metrics')
    @patch('api.dashboard.routes_monitoring._get_validation_throughput')
    @patch('api.dashboard.routes_monitoring._get_agent_performance')
    @patch('api.dashboard.routes_monitoring._get_database_performance')
    def test_get_metrics_endpoint(
        self,
        mock_db_perf,
        mock_agent_perf,
        mock_throughput,
        mock_cache,
        mock_resources,
        client
    ):
        """Test GET /monitoring/metrics endpoint."""
        # Setup mocks
        mock_resources.return_value = {"cpu_percent": 50.0, "timestamp": "2024-01-01T00:00:00"}
        mock_cache.return_value = {"hit_rate": 80.0, "timestamp": "2024-01-01T00:00:00"}
        mock_throughput.return_value = {"per_minute": 5.0, "timestamp": "2024-01-01T00:00:00"}
        mock_agent_perf.return_value = {"overall_avg_ms": 250.0, "timestamp": "2024-01-01T00:00:00"}
        mock_db_perf.return_value = {"overall_avg_ms": 50.0, "timestamp": "2024-01-01T00:00:00"}

        response = client.get("/monitoring/metrics?time_range=1h")

        assert response.status_code == 200
        data = response.json()
        assert "system_resources" in data
        assert "cache" in data
        assert "validation_throughput" in data
        assert "agent_performance" in data
        assert "database_performance" in data
        assert data["time_range"] == "1h"

    def test_get_metrics_invalid_time_range(self, client):
        """Test GET /monitoring/metrics with invalid time range."""
        response = client.get("/monitoring/metrics?time_range=invalid")

        assert response.status_code == 422  # Validation error

    def test_get_historical_metrics(self, client):
        """Test GET /monitoring/metrics/historical endpoint."""
        response = client.get("/monitoring/metrics/historical?time_range=24h&interval=5m")

        assert response.status_code == 200
        data = response.json()
        assert "time_range" in data
        assert "interval" in data
        assert "data_points" in data
        assert isinstance(data["data_points"], list)

    def test_export_metrics_json(self, client):
        """Test GET /monitoring/export endpoint with JSON format."""
        with patch('api.dashboard.routes_monitoring._get_system_resources') as mock_resources, \
             patch('api.dashboard.routes_monitoring._get_cache_metrics') as mock_cache, \
             patch('api.dashboard.routes_monitoring._get_validation_throughput') as mock_throughput, \
             patch('api.dashboard.routes_monitoring._get_agent_performance') as mock_agent, \
             patch('api.dashboard.routes_monitoring._get_database_performance') as mock_db:

            mock_resources.return_value = {"cpu_percent": 50.0, "timestamp": "2024-01-01T00:00:00"}
            mock_cache.return_value = {"hit_rate": 80.0, "timestamp": "2024-01-01T00:00:00"}
            mock_throughput.return_value = {"per_minute": 5.0, "timestamp": "2024-01-01T00:00:00"}
            mock_agent.return_value = {"overall_avg_ms": 250.0, "agent_metrics": {}, "timestamp": "2024-01-01T00:00:00"}
            mock_db.return_value = {"overall_avg_ms": 50.0, "db_metrics": {}, "timestamp": "2024-01-01T00:00:00"}

            response = client.get("/monitoring/export?format=json&time_range=24h")

            assert response.status_code == 200
            assert "application/json" in response.headers["content-type"]

    def test_export_metrics_csv(self, client):
        """Test GET /monitoring/export endpoint with CSV format."""
        with patch('api.dashboard.routes_monitoring._get_system_resources') as mock_resources, \
             patch('api.dashboard.routes_monitoring._get_cache_metrics') as mock_cache, \
             patch('api.dashboard.routes_monitoring._get_validation_throughput') as mock_throughput, \
             patch('api.dashboard.routes_monitoring._get_agent_performance') as mock_agent, \
             patch('api.dashboard.routes_monitoring._get_database_performance') as mock_db:

            mock_resources.return_value = {"cpu_percent": 50.0, "timestamp": "2024-01-01T00:00:00"}
            mock_cache.return_value = {"hit_rate": 80.0, "timestamp": "2024-01-01T00:00:00"}
            mock_throughput.return_value = {"per_minute": 5.0, "timestamp": "2024-01-01T00:00:00"}
            mock_agent.return_value = {"overall_avg_ms": 250.0, "agent_metrics": {}, "timestamp": "2024-01-01T00:00:00"}
            mock_db.return_value = {"overall_avg_ms": 50.0, "db_metrics": {}, "timestamp": "2024-01-01T00:00:00"}

            response = client.get("/monitoring/export?format=csv&time_range=24h")

            assert response.status_code == 200
            assert "text/csv" in response.headers["content-type"]
            assert "metric,value,timestamp" in response.text

    def test_monitoring_health(self, client):
        """Test GET /monitoring/health endpoint."""
        response = client.get("/monitoring/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "metrics_available" in data
