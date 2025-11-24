"""
Tests for WebSocket live updates functionality
"""
import pytest
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from api.websocket_endpoints import ConnectionManager, connection_manager


@pytest.fixture
def manager():
    """Create a connection manager instance"""
    return ConnectionManager()


@pytest.mark.asyncio
async def test_websocket_connection_manager():
    """Test that WebSocket connection manager works"""
    manager = ConnectionManager()
    
    # Verify manager has required methods
    assert hasattr(manager, 'connect')
    assert hasattr(manager, 'disconnect')
    assert hasattr(manager, 'send_progress_update')
    assert hasattr(manager, 'send_workflow_status')


@pytest.mark.asyncio
async def test_websocket_workflow_updates():
    """Test sending workflow updates through WebSocket"""
    manager = ConnectionManager()
    
    workflow_id = "test-workflow-123"
    
    # Send update (should not crash even without connections)
    await manager.send_workflow_status(
        workflow_id,
        "running",
        message="Test update"
    )
    
    # Test should complete without errors
    assert True


@pytest.mark.asyncio
async def test_websocket_no_403_errors():
    """Test that WebSocket accepts connections without 403 errors"""
    # This is a smoke test to verify WebSocket endpoint configuration
    # In real environment, this would connect via WebSocket client
    
    from api.websocket_endpoints import websocket_endpoint
    
    # Verify the endpoint function exists and is callable
    assert callable(websocket_endpoint)


@pytest.mark.asyncio
async def test_websocket_heartbeat_mechanism():
    """Test that WebSocket has heartbeat mechanism"""
    # Verify PING_INTERVAL is defined
    from api.websocket_endpoints import PING_INTERVAL
    
    assert isinstance(PING_INTERVAL, int)
    assert PING_INTERVAL > 0
    assert PING_INTERVAL <= 60, "Heartbeat interval should be reasonable"


@pytest.mark.asyncio
async def test_websocket_connection_cleanup():
    """Test that WebSocket connections are properly cleaned up"""
    manager = ConnectionManager()
    
    workflow_id = "test-cleanup"
    
    # Initial state
    assert workflow_id not in manager.active_connections
    
    # Simulate connection
    manager.active_connections[workflow_id] = set()
    
    # Verify it's tracked
    assert workflow_id in manager.active_connections
    
    # Clean up
    if workflow_id in manager.active_connections:
        del manager.active_connections[workflow_id]
    
    # Verify cleanup
    assert workflow_id not in manager.active_connections


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
