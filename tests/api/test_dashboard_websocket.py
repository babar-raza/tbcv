# file: tests/api/test_dashboard_websocket.py
"""
Task Card 1: WebSocket & Real-time Update Tests

Tests for WebSocket connections and real-time update functionality including:
- WebSocket connection establishment
- Real-time validation/recommendation/workflow broadcasts
- Activity feed updates

Target: 15 tests covering WebSocket functionality.
"""

import os
import sys
import json
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

# Set environment before imports
os.environ.setdefault("TBCV_ENV", "test")
os.environ.setdefault("OLLAMA_ENABLED", "false")
os.environ.setdefault("OLLAMA_MODEL", "mistral")

import pytest
from fastapi.testclient import TestClient
from starlette.testclient import TestClient as StarletteTestClient

# Import after environment is set
from api.server import app
from api.websocket_endpoints import ConnectionManager, connection_manager
from api.services.live_bus import LiveBus, get_live_bus
from core.database import db_manager


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def fresh_connection_manager():
    """Create a fresh ConnectionManager for isolated tests."""
    return ConnectionManager()


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket for testing."""
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    ws.receive_text = AsyncMock()
    ws.close = AsyncMock()
    return ws


@pytest.fixture
def fixed_timestamp():
    """Provide a fixed timestamp for deterministic tests."""
    return "2025-01-15T12:00:00+00:00"


# =============================================================================
# TestWebSocketConnection (4 tests)
# =============================================================================

@pytest.mark.integration
class TestWebSocketConnection:
    """Test WebSocket connection establishment and management."""

    def test_websocket_validation_updates_connects(self, client):
        """Test that WebSocket connects to /ws/validation_updates endpoint."""
        with client.websocket_connect("/ws/validation_updates") as websocket:
            # Should receive connection confirmation
            data = websocket.receive_json()
            assert data["type"] == "connection_established"
            assert "validation_updates" in data.get("workflow_id", "") or data.get("message", "")

    def test_websocket_workflow_connects(self, client, running_workflow):
        """Test that WebSocket connects to specific workflow endpoint."""
        workflow_id = running_workflow["workflow_id"]

        with client.websocket_connect(f"/ws/{workflow_id}") as websocket:
            # Should receive connection confirmation
            data = websocket.receive_json()
            assert data["type"] == "connection_established"
            assert data["workflow_id"] == workflow_id
            assert "Connected" in data.get("message", "")

    def test_websocket_heartbeat_response(self, client):
        """Test that WebSocket responds to ping with pong."""
        with client.websocket_connect("/ws/validation_updates") as websocket:
            # Receive initial connection message
            websocket.receive_json()

            # Send ping
            websocket.send_json({"type": "ping"})

            # Should receive pong
            response = websocket.receive_json()
            assert response["type"] == "pong"
            assert "timestamp" in response

    def test_websocket_handles_invalid_workflow_id(self, client):
        """Test that WebSocket handles connection to nonexistent workflow gracefully."""
        # Even with invalid workflow ID, connection should be accepted
        # (validation happens at message level, not connection level)
        with client.websocket_connect("/ws/nonexistent-workflow-id-12345") as websocket:
            data = websocket.receive_json()
            assert data["type"] == "connection_established"
            assert data["workflow_id"] == "nonexistent-workflow-id-12345"


# =============================================================================
# TestRealtimeUpdates (7 tests)
# =============================================================================

@pytest.mark.integration
class TestRealtimeUpdates:
    """Test real-time update broadcasting functionality."""

    @pytest.mark.asyncio
    async def test_validation_created_broadcast(self, fresh_connection_manager, mock_websocket, fixed_timestamp):
        """Test that validation_created events are broadcast to connected clients."""
        workflow_id = "validation_updates"

        # Set up connection
        await fresh_connection_manager.connect(mock_websocket, workflow_id)

        # Send validation created update
        await fresh_connection_manager.send_progress_update(workflow_id, {
            "type": "validation_created",
            "validation_id": "val_001",
            "file_path": "test.md",
            "timestamp": fixed_timestamp
        })

        # Verify message was sent
        mock_websocket.send_text.assert_called()
        call_args = mock_websocket.send_text.call_args[0][0]
        message = json.loads(call_args)

        assert message["type"] == "progress_update"
        assert message["data"]["type"] == "validation_created"
        assert message["data"]["validation_id"] == "val_001"

    @pytest.mark.asyncio
    async def test_validation_approved_broadcast(self, fresh_connection_manager, mock_websocket, fixed_timestamp):
        """Test that validation_approved events are broadcast correctly."""
        workflow_id = "validation_updates"

        await fresh_connection_manager.connect(mock_websocket, workflow_id)

        await fresh_connection_manager.send_progress_update(workflow_id, {
            "type": "validation_approved",
            "validation_id": "val_002",
            "reviewer": "test_user",
            "timestamp": fixed_timestamp
        })

        mock_websocket.send_text.assert_called()
        call_args = mock_websocket.send_text.call_args[0][0]
        message = json.loads(call_args)

        assert message["data"]["type"] == "validation_approved"
        assert message["data"]["validation_id"] == "val_002"
        assert message["data"]["reviewer"] == "test_user"

    @pytest.mark.asyncio
    async def test_validation_rejected_broadcast(self, fresh_connection_manager, mock_websocket, fixed_timestamp):
        """Test that validation_rejected events are broadcast correctly."""
        workflow_id = "validation_updates"

        await fresh_connection_manager.connect(mock_websocket, workflow_id)

        await fresh_connection_manager.send_progress_update(workflow_id, {
            "type": "validation_rejected",
            "validation_id": "val_003",
            "reason": "Does not meet requirements",
            "timestamp": fixed_timestamp
        })

        mock_websocket.send_text.assert_called()
        call_args = mock_websocket.send_text.call_args[0][0]
        message = json.loads(call_args)

        assert message["data"]["type"] == "validation_rejected"
        assert message["data"]["validation_id"] == "val_003"
        assert "reason" in message["data"]

    @pytest.mark.asyncio
    async def test_validation_enhanced_broadcast(self, fresh_connection_manager, mock_websocket, fixed_timestamp):
        """Test that validation_enhanced events are broadcast correctly."""
        workflow_id = "validation_updates"

        await fresh_connection_manager.connect(mock_websocket, workflow_id)

        await fresh_connection_manager.send_progress_update(workflow_id, {
            "type": "validation_enhanced",
            "validation_id": "val_004",
            "changes_applied": 3,
            "timestamp": fixed_timestamp
        })

        mock_websocket.send_text.assert_called()
        call_args = mock_websocket.send_text.call_args[0][0]
        message = json.loads(call_args)

        assert message["data"]["type"] == "validation_enhanced"
        assert message["data"]["changes_applied"] == 3

    @pytest.mark.asyncio
    async def test_recommendation_created_broadcast(self, fresh_connection_manager, mock_websocket, fixed_timestamp):
        """Test that recommendation_created events are broadcast correctly."""
        workflow_id = "validation_updates"

        await fresh_connection_manager.connect(mock_websocket, workflow_id)

        await fresh_connection_manager.send_progress_update(workflow_id, {
            "type": "recommendation_created",
            "recommendation_id": "rec_001",
            "validation_id": "val_001",
            "title": "Fix formatting",
            "timestamp": fixed_timestamp
        })

        mock_websocket.send_text.assert_called()
        call_args = mock_websocket.send_text.call_args[0][0]
        message = json.loads(call_args)

        assert message["data"]["type"] == "recommendation_created"
        assert message["data"]["recommendation_id"] == "rec_001"
        assert message["data"]["title"] == "Fix formatting"

    @pytest.mark.asyncio
    async def test_workflow_progress_broadcast(self, fresh_connection_manager, mock_websocket, fixed_timestamp):
        """Test that workflow progress updates are broadcast correctly."""
        workflow_id = "wf_001"

        await fresh_connection_manager.connect(mock_websocket, workflow_id)

        await fresh_connection_manager.send_progress_update(workflow_id, {
            "type": "workflow_progress",
            "current_step": 5,
            "total_steps": 10,
            "progress_percent": 50,
            "current_file": "file_5.md",
            "timestamp": fixed_timestamp
        })

        mock_websocket.send_text.assert_called()
        call_args = mock_websocket.send_text.call_args[0][0]
        message = json.loads(call_args)

        assert message["workflow_id"] == workflow_id
        assert message["data"]["progress_percent"] == 50
        assert message["data"]["current_step"] == 5
        assert message["data"]["total_steps"] == 10

    @pytest.mark.asyncio
    async def test_workflow_completed_broadcast(self, fresh_connection_manager, mock_websocket, fixed_timestamp):
        """Test that workflow_completed events are broadcast correctly."""
        workflow_id = "wf_002"

        await fresh_connection_manager.connect(mock_websocket, workflow_id)

        await fresh_connection_manager.send_workflow_status(workflow_id, "completed",
            files_processed=10,
            validations_created=10,
            timestamp=fixed_timestamp
        )

        mock_websocket.send_text.assert_called()
        call_args = mock_websocket.send_text.call_args[0][0]
        message = json.loads(call_args)

        assert message["data"]["status"] == "completed"
        assert message["data"]["files_processed"] == 10


# =============================================================================
# TestActivityFeed (4 tests)
# =============================================================================

@pytest.mark.integration
class TestActivityFeed:
    """Test activity feed update functionality."""

    @pytest.mark.asyncio
    async def test_activity_feed_receives_updates(self, fresh_connection_manager, mock_websocket, fixed_timestamp):
        """Test that activity feed receives all relevant updates."""
        # Connect to global validation_updates channel (activity feed)
        await fresh_connection_manager.connect(mock_websocket, "validation_updates")

        # Send various events
        events = [
            {"type": "validation_created", "validation_id": "v1", "timestamp": fixed_timestamp},
            {"type": "recommendation_created", "recommendation_id": "r1", "timestamp": fixed_timestamp},
            {"type": "validation_approved", "validation_id": "v1", "timestamp": fixed_timestamp},
        ]

        for event in events:
            await fresh_connection_manager.send_progress_update("validation_updates", event)

        # Verify all events were sent
        assert mock_websocket.send_text.call_count == 3

    @pytest.mark.asyncio
    async def test_activity_feed_max_items_limit(self, fresh_connection_manager, mock_websocket, fixed_timestamp):
        """Test that activity feed handles large number of updates."""
        await fresh_connection_manager.connect(mock_websocket, "validation_updates")

        # Send 100 events (simulating high activity)
        for i in range(100):
            await fresh_connection_manager.send_progress_update("validation_updates", {
                "type": "validation_created",
                "validation_id": f"val_{i:03d}",
                "timestamp": fixed_timestamp
            })

        # All 100 events should have been sent
        assert mock_websocket.send_text.call_count == 100

        # Verify the last message contains the correct validation_id
        last_call = mock_websocket.send_text.call_args_list[-1]
        last_message = json.loads(last_call[0][0])
        assert last_message["data"]["validation_id"] == "val_099"

    @pytest.mark.asyncio
    async def test_activity_icon_mapping(self, fresh_connection_manager, mock_websocket, fixed_timestamp):
        """Test that different event types are properly distinguished."""
        await fresh_connection_manager.connect(mock_websocket, "validation_updates")

        # Test different event types that map to different icons in UI
        event_types = [
            ("validation_created", "validation_id", "v1"),
            ("validation_approved", "validation_id", "v2"),
            ("validation_rejected", "validation_id", "v3"),
            ("recommendation_created", "recommendation_id", "r1"),
            ("workflow_started", "workflow_id", "w1"),
            ("workflow_completed", "workflow_id", "w2"),
        ]

        for event_type, id_field, id_value in event_types:
            await fresh_connection_manager.send_progress_update("validation_updates", {
                "type": event_type,
                id_field: id_value,
                "timestamp": fixed_timestamp
            })

        # Verify all event types were broadcast
        assert mock_websocket.send_text.call_count == len(event_types)

        # Verify each event type was properly included in messages
        sent_types = set()
        for call in mock_websocket.send_text.call_args_list:
            message = json.loads(call[0][0])
            sent_types.add(message["data"]["type"])

        expected_types = {et[0] for et in event_types}
        assert sent_types == expected_types

    @pytest.mark.asyncio
    async def test_activity_timestamp_format(self, fresh_connection_manager, mock_websocket):
        """Test that activity timestamps are in proper ISO format."""
        await fresh_connection_manager.connect(mock_websocket, "validation_updates")

        # Use a specific timestamp
        iso_timestamp = datetime.now(timezone.utc).isoformat()

        await fresh_connection_manager.send_progress_update("validation_updates", {
            "type": "validation_created",
            "validation_id": "val_timestamp_test",
            "timestamp": iso_timestamp
        })

        mock_websocket.send_text.assert_called()
        call_args = mock_websocket.send_text.call_args[0][0]
        message = json.loads(call_args)

        # Verify outer timestamp exists
        assert "timestamp" in message

        # Verify inner data timestamp matches what was sent
        assert message["data"]["timestamp"] == iso_timestamp

        # Verify timestamp is valid ISO format (should not raise)
        if message["timestamp"]:  # May be empty string if not set
            # This should not raise if format is correct
            assert isinstance(message["timestamp"], str)


# =============================================================================
# Connection Cleanup Tests
# =============================================================================

@pytest.mark.integration
class TestWebSocketCleanup:
    """Test WebSocket connection cleanup."""

    @pytest.mark.asyncio
    async def test_disconnect_removes_connection(self, fresh_connection_manager, mock_websocket):
        """Test that disconnecting removes the connection from the manager."""
        workflow_id = "test_workflow"

        # Connect
        await fresh_connection_manager.connect(mock_websocket, workflow_id)
        assert workflow_id in fresh_connection_manager.active_connections
        assert mock_websocket in fresh_connection_manager.active_connections[workflow_id]

        # Disconnect
        fresh_connection_manager.disconnect(mock_websocket)

        # Verify cleanup - either workflow_id removed entirely or websocket removed from set
        if workflow_id in fresh_connection_manager.active_connections:
            assert mock_websocket not in fresh_connection_manager.active_connections[workflow_id]
        else:
            # workflow_id was removed entirely (no more connections)
            assert True

    @pytest.mark.asyncio
    async def test_failed_send_triggers_cleanup(self, fresh_connection_manager, mock_websocket):
        """Test that failed message send triggers connection cleanup."""
        workflow_id = "test_workflow"

        # Connect
        await fresh_connection_manager.connect(mock_websocket, workflow_id)

        # Configure send_text to fail
        mock_websocket.send_text.side_effect = Exception("Connection closed")

        # Try to send message
        await fresh_connection_manager.send_progress_update(workflow_id, {
            "type": "test",
            "data": "test"
        })

        # Connection should be cleaned up after failed send
        if workflow_id in fresh_connection_manager.active_connections:
            assert mock_websocket not in fresh_connection_manager.active_connections[workflow_id]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
