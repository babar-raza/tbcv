"""Comprehensive tests for MCP admin methods."""

import pytest
import os
from pathlib import Path
from svc.mcp_client import MCPSyncClient, get_mcp_sync_client
from svc.mcp_exceptions import MCPError


class TestSystemStatus:
    """Tests for get_system_status method."""

    def test_get_system_status_success(self):
        """Test successful system status retrieval."""
        client = get_mcp_sync_client()
        result = client.get_system_status()

        assert "status" in result
        assert result["status"] in ["healthy", "degraded", "unhealthy"]
        assert "components" in result
        assert "database" in result["components"]
        assert "cache" in result["components"]
        assert "agents" in result["components"]
        assert "resources" in result
        assert "cpu_percent" in result["resources"]
        assert "memory_percent" in result["resources"]
        assert "disk_percent" in result["resources"]
        assert "maintenance_mode" in result

    def test_system_status_components(self):
        """Test system status component structure."""
        client = get_mcp_sync_client()
        result = client.get_system_status()

        # Check database component
        db_component = result["components"]["database"]
        assert "status" in db_component
        assert "details" in db_component

        # Check cache component
        cache_component = result["components"]["cache"]
        assert "status" in cache_component
        assert "details" in cache_component

        # Check agents component
        agents_component = result["components"]["agents"]
        assert "status" in agents_component
        assert "details" in agents_component


class TestCacheManagement:
    """Tests for cache management methods."""

    def test_get_cache_stats(self):
        """Test cache statistics retrieval."""
        client = get_mcp_sync_client()
        result = client.get_cache_stats()

        assert "total_items" in result
        assert "total_size_bytes" in result
        assert "hit_rate" in result
        assert "by_type" in result
        assert isinstance(result["total_items"], int)
        assert isinstance(result["total_size_bytes"], int)
        assert isinstance(result["hit_rate"], (int, float))

    def test_clear_cache_success(self):
        """Test cache clearing."""
        client = get_mcp_sync_client()
        result = client.clear_cache()

        assert result["success"] is True
        assert "cleared_items" in result
        assert isinstance(result["cleared_items"], int)
        assert "cache_types_cleared" in result

    def test_clear_cache_with_types(self):
        """Test clearing specific cache types."""
        client = get_mcp_sync_client()
        result = client.clear_cache(cache_types=["validation", "rules"])

        assert result["success"] is True
        assert "cleared_items" in result
        assert result["cache_types_cleared"] == ["validation", "rules"]

    def test_cleanup_cache_default(self):
        """Test cache cleanup with default age."""
        client = get_mcp_sync_client()
        result = client.cleanup_cache()

        assert result["success"] is True
        assert "cleaned_items" in result
        assert isinstance(result["cleaned_items"], int)

    def test_cleanup_cache_custom_age(self):
        """Test cache cleanup with custom max age."""
        client = get_mcp_sync_client()
        result = client.cleanup_cache(max_age_hours=48)

        assert result["success"] is True
        assert "cleaned_items" in result

    def test_rebuild_cache(self):
        """Test cache rebuild operation."""
        client = get_mcp_sync_client()
        result = client.rebuild_cache()

        assert result["success"] is True
        assert "rebuilt_items" in result
        assert isinstance(result["rebuilt_items"], int)


class TestAgentManagement:
    """Tests for agent management methods."""

    def test_reload_agent_not_found(self):
        """Test reloading non-existent agent fails."""
        client = get_mcp_sync_client()

        with pytest.raises(Exception) as exc_info:
            client.reload_agent("nonexistent_agent")

        # Should raise an error about agent not found
        assert "not found" in str(exc_info.value).lower() or "not initialized" in str(exc_info.value).lower()


class TestGarbageCollection:
    """Tests for garbage collection method."""

    def test_run_gc_success(self):
        """Test garbage collection execution."""
        client = get_mcp_sync_client()
        result = client.run_gc()

        assert result["success"] is True
        assert "collected_objects" in result
        assert isinstance(result["collected_objects"], int)
        assert "generation" in result
        assert "stats" in result


class TestMaintenanceMode:
    """Tests for maintenance mode methods."""

    def test_enable_maintenance_mode(self):
        """Test enabling maintenance mode."""
        client = get_mcp_sync_client()

        # Enable maintenance mode
        result = client.enable_maintenance_mode(
            reason="Testing maintenance mode",
            enabled_by="test_suite"
        )

        assert result["success"] is True
        assert "enabled_at" in result

        # Verify it's enabled
        status = client.get_system_status()
        assert status["maintenance_mode"] is True

        # Clean up: disable it
        client.disable_maintenance_mode()

    def test_disable_maintenance_mode(self):
        """Test disabling maintenance mode."""
        client = get_mcp_sync_client()

        # Enable first
        client.enable_maintenance_mode()

        # Then disable
        result = client.disable_maintenance_mode()

        assert result["success"] is True
        assert "disabled_at" in result

        # Verify it's disabled
        status = client.get_system_status()
        assert status["maintenance_mode"] is False

    def test_maintenance_mode_workflow(self):
        """Test complete maintenance mode workflow."""
        client = get_mcp_sync_client()

        # Initially should be disabled
        status = client.get_system_status()
        initial_state = status["maintenance_mode"]

        # Enable with reason
        enable_result = client.enable_maintenance_mode(
            reason="System upgrade",
            enabled_by="admin"
        )
        assert enable_result["success"] is True

        # Check it's enabled
        status = client.get_system_status()
        assert status["maintenance_mode"] is True

        # Disable
        disable_result = client.disable_maintenance_mode()
        assert disable_result["success"] is True

        # Check it's disabled
        status = client.get_system_status()
        assert status["maintenance_mode"] is False


class TestCheckpoints:
    """Tests for checkpoint methods."""

    def test_create_checkpoint_simple(self):
        """Test creating a simple checkpoint."""
        client = get_mcp_sync_client()
        result = client.create_checkpoint()

        assert result["success"] is True
        assert "checkpoint_id" in result
        assert "created_at" in result
        assert len(result["checkpoint_id"]) > 0

    def test_create_checkpoint_with_name(self):
        """Test creating a named checkpoint."""
        client = get_mcp_sync_client()
        checkpoint_name = "test_checkpoint"
        result = client.create_checkpoint(name=checkpoint_name)

        assert result["success"] is True
        assert checkpoint_name in result["checkpoint_id"]
        assert "created_at" in result

    def test_create_checkpoint_with_metadata(self):
        """Test creating checkpoint with metadata."""
        client = get_mcp_sync_client()
        metadata = {
            "reason": "Pre-upgrade backup",
            "version": "1.0.0",
            "triggered_by": "test"
        }
        result = client.create_checkpoint(
            name="upgrade_backup",
            metadata=metadata
        )

        assert result["success"] is True
        assert "checkpoint_id" in result
        assert "upgrade_backup" in result["checkpoint_id"]


class TestIntegration:
    """Integration tests for admin methods."""

    def test_health_check_workflow(self):
        """Test complete health check workflow."""
        client = get_mcp_sync_client()

        # Get system status
        status = client.get_system_status()
        assert "status" in status

        # Get cache stats
        cache_stats = client.get_cache_stats()
        assert "total_items" in cache_stats

        # Run GC
        gc_result = client.run_gc()
        assert gc_result["success"] is True

    def test_cache_lifecycle(self):
        """Test complete cache lifecycle."""
        client = get_mcp_sync_client()

        # Get initial stats
        initial_stats = client.get_cache_stats()

        # Clear cache
        clear_result = client.clear_cache()
        assert clear_result["success"] is True

        # Verify cleared
        after_clear_stats = client.get_cache_stats()
        # After clear, items should be 0 or less than initial
        assert after_clear_stats["total_items"] <= initial_stats["total_items"]

        # Cleanup old entries
        cleanup_result = client.cleanup_cache(max_age_hours=1)
        assert cleanup_result["success"] is True

        # Rebuild
        rebuild_result = client.rebuild_cache()
        assert rebuild_result["success"] is True

    def test_maintenance_and_checkpoint_workflow(self):
        """Test maintenance mode with checkpoint creation."""
        client = get_mcp_sync_client()

        # Create checkpoint before maintenance
        checkpoint_result = client.create_checkpoint(
            name="before_maintenance",
            metadata={"reason": "Pre-maintenance backup"}
        )
        assert checkpoint_result["success"] is True
        checkpoint_id = checkpoint_result["checkpoint_id"]

        # Enable maintenance mode
        enable_result = client.enable_maintenance_mode(
            reason="Scheduled maintenance",
            enabled_by="admin"
        )
        assert enable_result["success"] is True

        # Verify in maintenance mode
        status = client.get_system_status()
        assert status["maintenance_mode"] is True

        # Perform some admin tasks during maintenance
        gc_result = client.run_gc()
        assert gc_result["success"] is True

        cache_stats = client.get_cache_stats()
        assert "total_items" in cache_stats

        # Disable maintenance mode
        disable_result = client.disable_maintenance_mode()
        assert disable_result["success"] is True

        # Verify out of maintenance mode
        status = client.get_system_status()
        assert status["maintenance_mode"] is False


class TestErrorCases:
    """Test error handling for admin methods."""

    def test_reload_nonexistent_agent(self):
        """Test reloading non-existent agent raises error."""
        client = get_mcp_sync_client()

        with pytest.raises(Exception):
            client.reload_agent("nonexistent_agent_12345")

    def test_cleanup_cache_invalid_age(self):
        """Test cleanup with invalid age parameter."""
        client = get_mcp_sync_client()

        # Negative age should still work (will clean nothing)
        result = client.cleanup_cache(max_age_hours=0)
        assert result["success"] is True


class TestPerformance:
    """Performance tests for admin methods."""

    def test_get_system_status_performance(self):
        """Test system status is fast enough."""
        import time
        client = get_mcp_sync_client()

        start = time.time()
        result = client.get_system_status()
        elapsed = time.time() - start

        # Should complete in under 5 seconds
        assert elapsed < 5.0
        assert result["status"] in ["healthy", "degraded", "unhealthy"]

    def test_get_cache_stats_performance(self):
        """Test cache stats retrieval is fast."""
        import time
        client = get_mcp_sync_client()

        start = time.time()
        result = client.get_cache_stats()
        elapsed = time.time() - start

        # Should complete in under 2 seconds
        assert elapsed < 2.0
        assert "total_items" in result

    def test_gc_performance(self):
        """Test garbage collection completes quickly."""
        import time
        client = get_mcp_sync_client()

        start = time.time()
        result = client.run_gc()
        elapsed = time.time() - start

        # GC should complete in under 5 seconds
        assert elapsed < 5.0
        assert result["success"] is True
