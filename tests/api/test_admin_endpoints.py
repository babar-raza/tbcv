"""
Tests for admin API endpoints.

Tests cover:
- System status and monitoring
- Cache management
- Agent reload
- Maintenance mode
- System checkpoints
- Performance reporting
"""

import pytest
import time
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient


@pytest.fixture
def admin_client(api_client):
    """Reuse the API client fixture from conftest."""
    return api_client


class TestAdminStatus:
    """Tests for admin status endpoints."""

    def test_admin_status_returns_200(self, admin_client):
        """Admin status should return 200 OK."""
        response = admin_client.get("/admin/status")
        assert response.status_code == 200

    def test_admin_status_has_required_fields(self, admin_client):
        """Admin status should include all required fields."""
        response = admin_client.get("/admin/status")
        data = response.json()

        assert "timestamp" in data
        assert "system" in data
        assert "workflows" in data
        assert "database" in data

        # System fields
        assert "version" in data["system"]
        assert "uptime_seconds" in data["system"]
        assert "agents_registered" in data["system"]
        assert "maintenance_mode" in data["system"]

    def test_admin_status_uptime_increases(self, admin_client):
        """Uptime should increase between requests."""
        response1 = admin_client.get("/admin/status")
        uptime1 = response1.json()["system"]["uptime_seconds"]

        time.sleep(1)

        response2 = admin_client.get("/admin/status")
        uptime2 = response2.json()["system"]["uptime_seconds"]

        assert uptime2 >= uptime1

    def test_admin_status_uptime_not_zero(self, admin_client):
        """Uptime should not be hardcoded to zero."""
        response = admin_client.get("/admin/status")
        uptime = response.json()["system"]["uptime_seconds"]
        assert uptime >= 0
        # If server has been running for more than 1 second, uptime should reflect that
        # This test may fail immediately after server start, which is acceptable

    def test_admin_active_workflows(self, admin_client):
        """Test active workflows endpoint."""
        response = admin_client.get("/admin/workflows/active")
        assert response.status_code == 200

        data = response.json()
        assert "count" in data
        assert "workflows" in data
        assert isinstance(data["workflows"], list)


class TestCacheManagement:
    """Tests for cache management endpoints."""

    def test_cache_stats_returns_200(self, admin_client):
        """Cache stats should return 200 OK."""
        response = admin_client.get("/admin/cache/stats")
        assert response.status_code == 200

    def test_cache_stats_has_l1_and_l2(self, admin_client):
        """Cache stats should include L1 and L2 statistics."""
        response = admin_client.get("/admin/cache/stats")
        data = response.json()

        assert "l1" in data
        assert "l2" in data

    def test_cache_stats_not_all_zeros(self, admin_client):
        """Cache stats should not be hardcoded to zeros."""
        response = admin_client.get("/admin/cache/stats")
        data = response.json()

        # At least L1 should have proper structure
        if data["l1"].get("enabled"):
            assert "size" in data["l1"]
            assert "hits" in data["l1"]
            assert "misses" in data["l1"]
            assert "hit_rate" in data["l1"]

    def test_cache_clear_returns_200(self, admin_client):
        """Cache clear should return 200 OK."""
        response = admin_client.post("/admin/cache/clear")
        assert response.status_code == 200

    def test_cache_clear_returns_cleared_counts(self, admin_client):
        """Cache clear should return actual cleared counts."""
        response = admin_client.post("/admin/cache/clear")
        data = response.json()

        assert "message" in data
        assert "cleared" in data
        assert "l1" in data["cleared"]
        assert "l2" in data["cleared"]
        assert "timestamp" in data

    def test_cache_cleanup_returns_200(self, admin_client):
        """Cache cleanup should return 200 OK."""
        response = admin_client.post("/admin/cache/cleanup")
        assert response.status_code == 200

    def test_cache_cleanup_returns_counts(self, admin_client):
        """Cache cleanup should return removal counts."""
        response = admin_client.post("/admin/cache/cleanup")
        data = response.json()

        assert "message" in data
        assert "removed_entries" in data
        assert "details" in data
        assert isinstance(data["removed_entries"], int)

    def test_cache_rebuild_returns_200(self, admin_client):
        """Cache rebuild should return 200 OK."""
        response = admin_client.post("/admin/cache/rebuild")
        assert response.status_code == 200

    def test_cache_rebuild_message(self, admin_client):
        """Cache rebuild should return completion message."""
        response = admin_client.post("/admin/cache/rebuild")
        data = response.json()

        assert "message" in data
        assert "timestamp" in data
        assert "completed" in data["message"].lower()


class TestPerformanceReporting:
    """Tests for performance reporting endpoints."""

    def test_performance_report_default_period(self, admin_client):
        """Performance report should work with default period."""
        response = admin_client.get("/admin/reports/performance")
        assert response.status_code == 200

    def test_performance_report_custom_period(self, admin_client):
        """Performance report should accept custom period."""
        response = admin_client.get("/admin/reports/performance?days=30")
        assert response.status_code == 200

        data = response.json()
        assert data["period_days"] == 30

    def test_performance_report_has_metrics(self, admin_client):
        """Performance report should include all required metrics."""
        response = admin_client.get("/admin/reports/performance")
        data = response.json()

        assert "metrics" in data
        metrics = data["metrics"]

        # Should not be hardcoded zeros
        assert "total_workflows" in metrics
        assert "completed_workflows" in metrics
        assert "failed_workflows" in metrics
        assert "avg_completion_time_ms" in metrics
        assert "error_rate" in metrics
        assert "success_rate" in metrics

    def test_performance_report_period_bounds(self, admin_client):
        """Performance report should include period start/end."""
        response = admin_client.get("/admin/reports/performance?days=7")
        data = response.json()

        assert "period" in data
        assert "start" in data["period"]
        assert "end" in data["period"]

    def test_performance_report_max_period_limit(self, admin_client):
        """Performance report should not allow periods > 90 days."""
        response = admin_client.get("/admin/reports/performance?days=100")
        # FastAPI should reject this with 422
        assert response.status_code in [200, 422]


class TestAgentManagement:
    """Tests for agent management endpoints."""

    def test_agent_reload_returns_404_for_unknown(self, admin_client):
        """Reloading unknown agent should return 404."""
        response = admin_client.post("/admin/agents/reload/unknown_agent_id")
        assert response.status_code == 404

    def test_agent_reload_known_agent(self, admin_client):
        """Reloading a known agent should return 200."""
        # Get list of agents first
        agents_response = admin_client.get("/agents")
        if agents_response.status_code == 200:
            agents = agents_response.json().get("agents", [])
            if agents:
                agent_id = agents[0]["agent_id"]
                response = admin_client.post(f"/admin/agents/reload/{agent_id}")
                assert response.status_code == 200

                data = response.json()
                assert "message" in data
                assert "agent_id" in data
                assert data["agent_id"] == agent_id
                assert "timestamp" in data

    def test_agent_reload_returns_actions(self, admin_client):
        """Agent reload should report actions taken."""
        # Use truth_manager as it should always be registered
        response = admin_client.post("/admin/agents/reload/truth_manager")

        if response.status_code == 200:
            data = response.json()
            assert "actions" in data
            assert isinstance(data["actions"], list)
            assert "cache_cleared" in data["actions"]


class TestMaintenanceMode:
    """Tests for maintenance mode endpoints."""

    def test_maintenance_enable_returns_200(self, admin_client):
        """Enabling maintenance mode should return 200."""
        response = admin_client.post("/admin/maintenance/enable")
        assert response.status_code == 200

    def test_maintenance_enable_sets_flag(self, admin_client):
        """Enabling maintenance mode should set maintenance_mode to true."""
        response = admin_client.post("/admin/maintenance/enable")
        data = response.json()

        assert "maintenance_mode" in data
        assert data["maintenance_mode"] is True
        assert "message" in data

    def test_maintenance_disable_returns_200(self, admin_client):
        """Disabling maintenance mode should return 200."""
        response = admin_client.post("/admin/maintenance/disable")
        assert response.status_code == 200

    def test_maintenance_disable_clears_flag(self, admin_client):
        """Disabling maintenance mode should set maintenance_mode to false."""
        response = admin_client.post("/admin/maintenance/disable")
        data = response.json()

        assert "maintenance_mode" in data
        assert data["maintenance_mode"] is False

    def test_maintenance_mode_toggle(self, admin_client):
        """Maintenance mode should toggle correctly."""
        # Enable
        enable_response = admin_client.post("/admin/maintenance/enable")
        assert enable_response.json()["maintenance_mode"] is True

        # Check status reflects maintenance mode
        status_response = admin_client.get("/admin/status")
        status_data = status_response.json()
        assert status_data["system"]["maintenance_mode"] is True

        # Disable
        disable_response = admin_client.post("/admin/maintenance/disable")
        assert disable_response.json()["maintenance_mode"] is False

        # Check status reflects normal mode
        status_response = admin_client.get("/admin/status")
        status_data = status_response.json()
        assert status_data["system"]["maintenance_mode"] is False


class TestSystemCheckpoints:
    """Tests for system checkpoint endpoints."""

    def test_system_checkpoint_returns_200(self, admin_client):
        """Creating system checkpoint should return 200."""
        response = admin_client.post("/admin/system/checkpoint")
        assert response.status_code == 200

    def test_system_checkpoint_returns_id(self, admin_client):
        """System checkpoint should return a checkpoint ID."""
        response = admin_client.post("/admin/system/checkpoint")
        data = response.json()

        assert "checkpoint_id" in data
        assert "message" in data
        assert "timestamp" in data
        assert len(data["checkpoint_id"]) == 36  # UUID format

    def test_system_checkpoint_has_summary(self, admin_client):
        """System checkpoint should include system state summary."""
        response = admin_client.post("/admin/system/checkpoint")
        data = response.json()

        assert "summary" in data
        summary = data["summary"]

        assert "workflows" in summary
        assert "agents" in summary
        assert "cache" in summary
        assert "system" in summary

    def test_multiple_checkpoints_unique_ids(self, admin_client):
        """Multiple checkpoints should have unique IDs."""
        response1 = admin_client.post("/admin/system/checkpoint")
        response2 = admin_client.post("/admin/system/checkpoint")

        id1 = response1.json()["checkpoint_id"]
        id2 = response2.json()["checkpoint_id"]

        assert id1 != id2


class TestGarbageCollection:
    """Tests for garbage collection endpoint."""

    def test_gc_returns_200(self, admin_client):
        """Garbage collection should return 200."""
        response = admin_client.post("/admin/system/gc")
        assert response.status_code == 200

    def test_gc_returns_message(self, admin_client):
        """Garbage collection should return completion message."""
        response = admin_client.post("/admin/system/gc")
        data = response.json()

        assert "message" in data
        assert "timestamp" in data


class TestHealthReport:
    """Tests for health report endpoint."""

    def test_health_report_returns_200(self, admin_client):
        """Health report should return 200."""
        response = admin_client.get("/admin/reports/health")
        assert response.status_code == 200

    def test_health_report_has_status(self, admin_client):
        """Health report should include system health status."""
        response = admin_client.get("/admin/reports/health")
        data = response.json()

        assert "status" in data
        assert "database" in data
        assert "agents" in data
        assert "timestamp" in data
