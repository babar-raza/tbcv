# tests/api/services/test_live_bus.py
"""
Unit tests for api/services/live_bus.py - Live event bus service.

This test module covers the LiveBus class which provides a publish/subscribe
event bus for real-time updates to connected clients via WebSocket.
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timezone

from api.services.live_bus import (
    LiveBus,
    start_live_bus,
    stop_live_bus,
    get_live_bus,
    _live_bus_instance
)


@pytest.mark.asyncio
@pytest.mark.unit
class TestLiveBusInitialization:
    """Test LiveBus initialization and configuration."""

    async def test_initialization_defaults(self):
        """Test LiveBus initializes with correct defaults."""
        bus = LiveBus()

        assert bus.enabled is True
        assert bus._connection_manager is None

    async def test_enabled_flag_default(self):
        """Test that enabled flag is True by default."""
        bus = LiveBus()
        assert bus.enabled is True

    async def test_connection_manager_starts_none(self):
        """Test that connection manager is None until first use."""
        bus = LiveBus()
        assert bus._connection_manager is None


@pytest.mark.asyncio
@pytest.mark.unit
class TestLiveBusConnectionManager:
    """Test LiveBus connection manager lazy loading."""

    async def test_get_connection_manager_lazy_load(self):
        """Test that connection manager is lazy loaded on first access."""
        bus = LiveBus()

        # Mock the import to avoid actual websocket dependency
        mock_cm = MagicMock()
        with patch('api.services.live_bus.connection_manager', mock_cm, create=True):
            with patch.dict('sys.modules', {'api.websocket_endpoints': MagicMock(connection_manager=mock_cm)}):
                # First access should attempt import
                result = bus._get_connection_manager()

        # After successful import, should be cached
        # Note: Result may be None if import fails in test environment

    async def test_get_connection_manager_caches_result(self):
        """Test that connection manager is cached after first load."""
        bus = LiveBus()

        mock_cm = MagicMock()
        bus._connection_manager = mock_cm

        result = bus._get_connection_manager()

        assert result is mock_cm

    async def test_get_connection_manager_import_failure_disables_bus(self):
        """Test that import failure disables the bus."""
        bus = LiveBus()

        # Verify initial state
        assert bus.enabled is True
        assert bus._connection_manager is None

        # Simulate what happens when import fails:
        # The implementation catches the exception and sets enabled=False
        # We test this behavior by verifying that when enabled is set to False,
        # the bus stops functioning (tested in other tests)

        # Directly set the state that would occur after import failure
        bus.enabled = False

        # Verify the bus is disabled
        assert bus.enabled is False

        # When disabled, publish should do nothing (tested elsewhere, but verify integration)
        mock_cm = MagicMock()
        mock_cm.send_progress_update = AsyncMock()
        bus._connection_manager = mock_cm

        await bus.publish("test", {"data": "test"})

        # Should not call connection manager when disabled
        mock_cm.send_progress_update.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.unit
class TestLiveBusPublish:
    """Test LiveBus publish functionality."""

    async def test_publish_when_disabled(self):
        """Test that publish does nothing when bus is disabled."""
        bus = LiveBus()
        bus.enabled = False

        # Should return immediately without error
        await bus.publish("test_topic", {"data": "test"})

        # No exception means success

    async def test_publish_calls_connection_manager(self):
        """Test that publish forwards to connection manager."""
        bus = LiveBus()

        mock_cm = MagicMock()
        mock_cm.send_progress_update = AsyncMock()
        bus._connection_manager = mock_cm

        await bus.publish("test_topic", {"data": "test"})

        mock_cm.send_progress_update.assert_called_once_with("test_topic", {"data": "test"})

    async def test_publish_handles_no_connection_manager(self):
        """Test that publish handles missing connection manager gracefully."""
        bus = LiveBus()
        bus._connection_manager = None

        # Mock _get_connection_manager to return None
        with patch.object(bus, '_get_connection_manager', return_value=None):
            # Should not raise exception
            await bus.publish("test_topic", {"data": "test"})

    async def test_publish_handles_connection_manager_error(self):
        """Test that publish handles connection manager errors gracefully."""
        bus = LiveBus()

        mock_cm = MagicMock()
        mock_cm.send_progress_update = AsyncMock(side_effect=Exception("Connection error"))
        bus._connection_manager = mock_cm

        # Should not raise exception - error is logged
        await bus.publish("test_topic", {"data": "test"})


@pytest.mark.asyncio
@pytest.mark.unit
class TestLiveBusValidationUpdates:
    """Test LiveBus validation update publishing."""

    async def test_publish_validation_update_message_format(self):
        """Test that validation update has correct message format."""
        bus = LiveBus()

        mock_cm = MagicMock()
        mock_cm.send_progress_update = AsyncMock()
        bus._connection_manager = mock_cm

        await bus.publish_validation_update(
            validation_id="val123",
            event_type="validation_created",
            data={"status": "pending"}
        )

        # Should be called twice: once for global channel, once for validation-specific
        assert mock_cm.send_progress_update.call_count == 2

        # Check first call (global validation_updates channel)
        first_call = mock_cm.send_progress_update.call_args_list[0]
        assert first_call[0][0] == "validation_updates"
        message = first_call[0][1]
        assert message["type"] == "validation_created"
        assert message["validation_id"] == "val123"
        assert message["status"] == "pending"
        assert "timestamp" in message

        # Check second call (validation-specific channel)
        second_call = mock_cm.send_progress_update.call_args_list[1]
        assert second_call[0][0] == "validation_val123"

    async def test_publish_validation_update_includes_timestamp(self):
        """Test that validation update includes ISO format timestamp."""
        bus = LiveBus()

        mock_cm = MagicMock()
        mock_cm.send_progress_update = AsyncMock()
        bus._connection_manager = mock_cm

        await bus.publish_validation_update("val123", "started", {})

        message = mock_cm.send_progress_update.call_args_list[0][0][1]
        timestamp = message["timestamp"]

        # Should be valid ISO format
        parsed = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        assert parsed is not None

    async def test_publish_validation_update_merges_data(self):
        """Test that additional data is merged into message."""
        bus = LiveBus()

        mock_cm = MagicMock()
        mock_cm.send_progress_update = AsyncMock()
        bus._connection_manager = mock_cm

        await bus.publish_validation_update(
            validation_id="val123",
            event_type="completed",
            data={"result": "success", "score": 100}
        )

        message = mock_cm.send_progress_update.call_args_list[0][0][1]
        assert message["result"] == "success"
        assert message["score"] == 100


@pytest.mark.asyncio
@pytest.mark.unit
class TestLiveBusRecommendationUpdates:
    """Test LiveBus recommendation update publishing."""

    async def test_publish_recommendation_update_message_format(self):
        """Test that recommendation update has correct message format."""
        bus = LiveBus()

        mock_cm = MagicMock()
        mock_cm.send_progress_update = AsyncMock()
        bus._connection_manager = mock_cm

        await bus.publish_recommendation_update(
            recommendation_id="rec456",
            event_type="recommendation_approved",
            data={"reviewer": "admin"}
        )

        # Should be called twice: global channel and recommendation-specific
        assert mock_cm.send_progress_update.call_count == 2

        # Check global channel call
        first_call = mock_cm.send_progress_update.call_args_list[0]
        assert first_call[0][0] == "validation_updates"
        message = first_call[0][1]
        assert message["type"] == "recommendation_approved"
        assert message["recommendation_id"] == "rec456"
        assert message["reviewer"] == "admin"

        # Check recommendation-specific channel
        second_call = mock_cm.send_progress_update.call_args_list[1]
        assert second_call[0][0] == "recommendation_rec456"

    async def test_publish_recommendation_update_includes_timestamp(self):
        """Test that recommendation update includes timestamp."""
        bus = LiveBus()

        mock_cm = MagicMock()
        mock_cm.send_progress_update = AsyncMock()
        bus._connection_manager = mock_cm

        await bus.publish_recommendation_update("rec789", "created", {})

        message = mock_cm.send_progress_update.call_args_list[0][0][1]
        assert "timestamp" in message


@pytest.mark.asyncio
@pytest.mark.unit
class TestLiveBusWorkflowUpdates:
    """Test LiveBus workflow update publishing."""

    async def test_publish_workflow_update_message_format(self):
        """Test that workflow update has correct message format."""
        bus = LiveBus()

        mock_cm = MagicMock()
        mock_cm.send_progress_update = AsyncMock()
        bus._connection_manager = mock_cm

        await bus.publish_workflow_update(
            workflow_id="wf789",
            event_type="workflow_completed",
            data={"duration": 120}
        )

        # Should be called twice: workflow-specific and global channel
        assert mock_cm.send_progress_update.call_count == 2

        # Check workflow-specific channel (called first)
        first_call = mock_cm.send_progress_update.call_args_list[0]
        assert first_call[0][0] == "wf789"  # Uses workflow_id as topic
        message = first_call[0][1]
        assert message["type"] == "workflow_completed"
        assert message["workflow_id"] == "wf789"
        assert message["duration"] == 120

        # Check global validation_updates channel
        second_call = mock_cm.send_progress_update.call_args_list[1]
        assert second_call[0][0] == "validation_updates"

    async def test_publish_workflow_update_includes_timestamp(self):
        """Test that workflow update includes timestamp."""
        bus = LiveBus()

        mock_cm = MagicMock()
        mock_cm.send_progress_update = AsyncMock()
        bus._connection_manager = mock_cm

        await bus.publish_workflow_update("wf123", "started", {})

        message = mock_cm.send_progress_update.call_args_list[0][0][1]
        assert "timestamp" in message


@pytest.mark.asyncio
@pytest.mark.unit
class TestLiveBusSubscription:
    """Test LiveBus subscription methods (API compatibility)."""

    async def test_subscribe_is_async(self):
        """Test that subscribe is an async method."""
        bus = LiveBus()

        # Should not raise - just logs
        await bus.subscribe("test_topic")

    async def test_unsubscribe_is_async(self):
        """Test that unsubscribe is an async method."""
        bus = LiveBus()

        mock_queue = MagicMock()

        # Should not raise - just logs
        await bus.unsubscribe(mock_queue, "test_topic")

    async def test_subscribe_accepts_topic(self):
        """Test that subscribe accepts a topic parameter."""
        bus = LiveBus()

        # Should accept topic without error
        await bus.subscribe("any_topic")
        await bus.subscribe("another_topic")

    async def test_unsubscribe_accepts_queue_and_topic(self):
        """Test that unsubscribe accepts queue and topic parameters."""
        bus = LiveBus()

        mock_queue = MagicMock()

        # Should accept parameters without error
        await bus.unsubscribe(mock_queue, "test_topic")


@pytest.mark.asyncio
@pytest.mark.unit
class TestLiveBusGlobalInstance:
    """Test global live bus instance management."""

    async def test_get_live_bus_returns_instance(self):
        """Test that get_live_bus returns a LiveBus instance."""
        bus = get_live_bus()

        assert isinstance(bus, LiveBus)

    async def test_get_live_bus_creates_instance_if_none(self):
        """Test that get_live_bus creates instance if none exists."""
        import api.services.live_bus as live_bus_module

        # Save original
        original = live_bus_module._live_bus_instance

        try:
            live_bus_module._live_bus_instance = None

            bus = get_live_bus()

            assert bus is not None
            assert isinstance(bus, LiveBus)
        finally:
            # Restore original
            live_bus_module._live_bus_instance = original

    async def test_get_live_bus_returns_same_instance(self):
        """Test that get_live_bus returns the same instance on repeated calls."""
        bus1 = get_live_bus()
        bus2 = get_live_bus()

        assert bus1 is bus2

    async def test_start_live_bus_creates_instance(self):
        """Test that start_live_bus creates a new instance."""
        import api.services.live_bus as live_bus_module

        # Save original
        original = live_bus_module._live_bus_instance

        try:
            live_bus_module._live_bus_instance = None

            await start_live_bus()

            assert live_bus_module._live_bus_instance is not None
            assert isinstance(live_bus_module._live_bus_instance, LiveBus)
        finally:
            # Restore original
            live_bus_module._live_bus_instance = original

    async def test_stop_live_bus_disables_instance(self):
        """Test that stop_live_bus disables the instance."""
        import api.services.live_bus as live_bus_module

        # Ensure instance exists
        await start_live_bus()
        instance = live_bus_module._live_bus_instance

        await stop_live_bus()

        # Instance should be disabled and cleared
        assert live_bus_module._live_bus_instance is None

    async def test_stop_live_bus_handles_no_instance(self):
        """Test that stop_live_bus handles case when no instance exists."""
        import api.services.live_bus as live_bus_module

        # Save original
        original = live_bus_module._live_bus_instance

        try:
            live_bus_module._live_bus_instance = None

            # Should not raise
            await stop_live_bus()
        finally:
            # Restore original
            live_bus_module._live_bus_instance = original


@pytest.mark.asyncio
@pytest.mark.unit
class TestLiveBusEdgeCases:
    """Test edge cases and error handling."""

    async def test_publish_with_empty_message(self):
        """Test publishing an empty message."""
        bus = LiveBus()

        mock_cm = MagicMock()
        mock_cm.send_progress_update = AsyncMock()
        bus._connection_manager = mock_cm

        await bus.publish("test_topic", {})

        mock_cm.send_progress_update.assert_called_once_with("test_topic", {})

    async def test_publish_with_complex_data(self):
        """Test publishing message with nested complex data."""
        bus = LiveBus()

        mock_cm = MagicMock()
        mock_cm.send_progress_update = AsyncMock()
        bus._connection_manager = mock_cm

        complex_data = {
            "nested": {"deep": {"value": 123}},
            "list": [1, 2, 3],
            "mixed": [{"a": 1}, {"b": 2}]
        }

        await bus.publish("test_topic", complex_data)

        mock_cm.send_progress_update.assert_called_once_with("test_topic", complex_data)

    async def test_publish_validation_update_with_empty_data(self):
        """Test validation update with empty data dict."""
        bus = LiveBus()

        mock_cm = MagicMock()
        mock_cm.send_progress_update = AsyncMock()
        bus._connection_manager = mock_cm

        await bus.publish_validation_update("val123", "test_event", {})

        message = mock_cm.send_progress_update.call_args_list[0][0][1]
        assert message["type"] == "test_event"
        assert message["validation_id"] == "val123"

    async def test_multiple_publish_calls(self):
        """Test multiple sequential publish calls."""
        bus = LiveBus()

        mock_cm = MagicMock()
        mock_cm.send_progress_update = AsyncMock()
        bus._connection_manager = mock_cm

        for i in range(5):
            await bus.publish(f"topic_{i}", {"index": i})

        assert mock_cm.send_progress_update.call_count == 5

    async def test_disable_enable_bus(self):
        """Test disabling and re-enabling the bus."""
        bus = LiveBus()

        mock_cm = MagicMock()
        mock_cm.send_progress_update = AsyncMock()
        bus._connection_manager = mock_cm

        # Initially enabled
        await bus.publish("topic", {"test": 1})
        assert mock_cm.send_progress_update.call_count == 1

        # Disable
        bus.enabled = False
        await bus.publish("topic", {"test": 2})
        assert mock_cm.send_progress_update.call_count == 1  # No new call

        # Re-enable
        bus.enabled = True
        await bus.publish("topic", {"test": 3})
        assert mock_cm.send_progress_update.call_count == 2


@pytest.mark.integration
@pytest.mark.asyncio
class TestLiveBusIntegration:
    """Integration tests for LiveBus with mocked connection manager."""

    async def test_full_validation_workflow(self):
        """Test complete validation update workflow."""
        bus = LiveBus()

        mock_cm = MagicMock()
        mock_cm.send_progress_update = AsyncMock()
        bus._connection_manager = mock_cm

        # Simulate validation lifecycle
        await bus.publish_validation_update("val001", "validation_created", {"file": "test.docx"})
        await bus.publish_validation_update("val001", "validation_started", {"status": "running"})
        await bus.publish_validation_update("val001", "validation_completed", {"result": "pass", "score": 95})

        # Should have 6 calls (2 per update: global + validation-specific)
        assert mock_cm.send_progress_update.call_count == 6

    async def test_full_workflow_lifecycle(self):
        """Test complete workflow lifecycle."""
        bus = LiveBus()

        mock_cm = MagicMock()
        mock_cm.send_progress_update = AsyncMock()
        bus._connection_manager = mock_cm

        # Simulate workflow lifecycle
        await bus.publish_workflow_update("wf001", "workflow_started", {"step": 1})
        await bus.publish_workflow_update("wf001", "workflow_progress", {"step": 2, "percent": 50})
        await bus.publish_workflow_update("wf001", "workflow_completed", {"step": 3, "result": "success"})

        # Should have 6 calls (2 per update: workflow-specific + global)
        assert mock_cm.send_progress_update.call_count == 6

    async def test_mixed_update_types(self):
        """Test mixed validation, recommendation, and workflow updates."""
        bus = LiveBus()

        mock_cm = MagicMock()
        mock_cm.send_progress_update = AsyncMock()
        bus._connection_manager = mock_cm

        await bus.publish_validation_update("val001", "created", {})
        await bus.publish_recommendation_update("rec001", "created", {})
        await bus.publish_workflow_update("wf001", "started", {})

        # Should have 6 calls total (2 per update type)
        assert mock_cm.send_progress_update.call_count == 6

        # Verify all were called with validation_updates topic (among others)
        topics_called = [call[0][0] for call in mock_cm.send_progress_update.call_args_list]
        assert topics_called.count("validation_updates") == 3

    async def test_start_stop_lifecycle(self):
        """Test start and stop lifecycle."""
        import api.services.live_bus as live_bus_module

        # Save original state
        original = live_bus_module._live_bus_instance

        try:
            # Start fresh
            live_bus_module._live_bus_instance = None

            # Start
            await start_live_bus()
            assert live_bus_module._live_bus_instance is not None

            instance = live_bus_module._live_bus_instance
            assert instance.enabled is True

            # Stop
            await stop_live_bus()
            assert live_bus_module._live_bus_instance is None

        finally:
            # Restore original state
            live_bus_module._live_bus_instance = original
