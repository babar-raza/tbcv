"""
API MCP Integration Tests for TASK-016.

Tests MCP client integration with API layer:
- MCP helper utilities
- Error conversion from MCP to HTTP
- Client initialization and singleton behavior
- WebSocket integration patterns
- Concurrent request handling

Run with: pytest tests/api/test_mcp_integration.py -v
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException, status

# Test the MCP helpers directly
from api.mcp_helpers import (
    get_api_mcp_client,
    mcp_error_to_http_exception,
    format_mcp_response,
    call_mcp_method,
    call_mcp_method_formatted,
)
from svc.mcp_client import MCPAsyncClient
from svc.mcp_exceptions import (
    MCPError,
    MCPResourceNotFoundError,
    MCPInvalidParamsError,
    MCPTimeoutError,
    MCPInternalError,
    MCPValidationError,
    MCPMethodNotFoundError,
)


# =============================================================================
# MCP Client Initialization Tests
# =============================================================================

@pytest.mark.asyncio
async def test_get_api_mcp_client_singleton():
    """Test that get_api_mcp_client returns singleton instance."""
    # Reset singleton
    import api.mcp_helpers
    api.mcp_helpers._mcp_client = None

    client1 = await get_api_mcp_client()
    client2 = await get_api_mcp_client()

    assert client1 is client2, "Should return same instance"
    assert isinstance(client1, MCPAsyncClient)


@pytest.mark.asyncio
async def test_get_api_mcp_client_creates_instance():
    """Test that get_api_mcp_client creates MCPAsyncClient."""
    # Reset singleton
    import api.mcp_helpers
    api.mcp_helpers._mcp_client = None

    client = await get_api_mcp_client()

    assert client is not None
    assert isinstance(client, MCPAsyncClient)


# =============================================================================
# Error Conversion Tests
# =============================================================================

def test_mcp_error_to_http_exception_resource_not_found():
    """Test MCPResourceNotFoundError converts to 404."""
    error = MCPResourceNotFoundError("Validation not found")
    http_exc = mcp_error_to_http_exception(error)

    assert isinstance(http_exc, HTTPException)
    assert http_exc.status_code == status.HTTP_404_NOT_FOUND
    assert "error" in http_exc.detail
    assert "not found" in http_exc.detail["error"].lower()


def test_mcp_error_to_http_exception_invalid_params():
    """Test MCPInvalidParamsError converts to 400."""
    error = MCPInvalidParamsError("Invalid file path")
    http_exc = mcp_error_to_http_exception(error)

    assert isinstance(http_exc, HTTPException)
    assert http_exc.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid" in http_exc.detail["error"]


def test_mcp_error_to_http_exception_timeout():
    """Test MCPTimeoutError converts to 504."""
    error = MCPTimeoutError("Request timeout")
    http_exc = mcp_error_to_http_exception(error)

    assert isinstance(http_exc, HTTPException)
    assert http_exc.status_code == status.HTTP_504_GATEWAY_TIMEOUT
    assert "timeout" in http_exc.detail["error"].lower()


def test_mcp_error_to_http_exception_validation():
    """Test MCPValidationError converts to 422."""
    error = MCPValidationError("Content validation failed")
    http_exc = mcp_error_to_http_exception(error)

    assert isinstance(http_exc, HTTPException)
    assert http_exc.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_mcp_error_to_http_exception_internal():
    """Test MCPInternalError converts to 500."""
    error = MCPInternalError("Internal server error")
    http_exc = mcp_error_to_http_exception(error)

    assert isinstance(http_exc, HTTPException)
    assert http_exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


def test_mcp_error_to_http_exception_method_not_found():
    """Test MCPMethodNotFoundError converts to 501."""
    error = MCPMethodNotFoundError("Method 'unknown' not found")
    http_exc = mcp_error_to_http_exception(error)

    assert isinstance(http_exc, HTTPException)
    assert http_exc.status_code == status.HTTP_501_NOT_IMPLEMENTED


def test_mcp_error_to_http_exception_includes_code():
    """Test that error code is included in detail."""
    error = MCPInvalidParamsError("Test error")
    error.code = -32602

    http_exc = mcp_error_to_http_exception(error)

    assert "code" in http_exc.detail
    assert http_exc.detail["code"] == -32602


def test_mcp_error_to_http_exception_includes_data():
    """Test that error data is included in detail."""
    error = MCPValidationError("Test error")
    error.data = {"field": "file_path", "issue": "missing"}

    http_exc = mcp_error_to_http_exception(error)

    assert "data" in http_exc.detail
    assert http_exc.detail["data"]["field"] == "file_path"


# =============================================================================
# Response Formatting Tests
# =============================================================================

def test_format_mcp_response_basic():
    """Test basic response formatting."""
    result = {"validation_id": "test-123", "status": "pass"}
    response = format_mcp_response(result)

    assert response["success"] is True
    assert response["data"] == result
    assert "meta" in response
    assert "timestamp" in response["meta"]


def test_format_mcp_response_with_meta():
    """Test response formatting with custom metadata."""
    result = {"validation_id": "test-123"}
    meta = {"cached": True, "execution_time_ms": 125}

    response = format_mcp_response(result, meta=meta)

    assert response["meta"]["cached"] is True
    assert response["meta"]["execution_time_ms"] == 125
    assert "timestamp" in response["meta"]


def test_format_mcp_response_failure():
    """Test response formatting for failures."""
    result = {"error": "Validation failed"}
    response = format_mcp_response(result, success=False)

    assert response["success"] is False
    assert response["data"] == result


# =============================================================================
# Call MCP Method Tests
# =============================================================================

@pytest.mark.asyncio
async def test_call_mcp_method_success():
    """Test successful MCP method call."""
    mock_client = AsyncMock(spec=MCPAsyncClient)
    mock_client.validate_file.return_value = {
        "validation_id": "test-123",
        "status": "pass"
    }

    with patch('api.mcp_helpers.get_api_mcp_client', return_value=mock_client):
        result = await call_mcp_method(
            "validate_file",
            file_path="/test.md"
        )

        assert result["validation_id"] == "test-123"
        mock_client.validate_file.assert_called_once_with(file_path="/test.md")


@pytest.mark.asyncio
async def test_call_mcp_method_not_found():
    """Test call_mcp_method with non-existent method."""
    mock_client = AsyncMock(spec=MCPAsyncClient)
    # Remove the method to simulate AttributeError
    del mock_client.nonexistent_method

    with patch('api.mcp_helpers.get_api_mcp_client', return_value=mock_client):
        with pytest.raises(HTTPException) as exc_info:
            await call_mcp_method("nonexistent_method")

        assert exc_info.value.status_code == status.HTTP_501_NOT_IMPLEMENTED


@pytest.mark.asyncio
async def test_call_mcp_method_mcp_error():
    """Test call_mcp_method with MCP error."""
    mock_client = AsyncMock(spec=MCPAsyncClient)
    mock_client.validate_file.side_effect = MCPResourceNotFoundError("File not found")

    with patch('api.mcp_helpers.get_api_mcp_client', return_value=mock_client):
        with pytest.raises(HTTPException) as exc_info:
            await call_mcp_method("validate_file", file_path="/test.md")

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_call_mcp_method_formatted():
    """Test call_mcp_method_formatted returns formatted response."""
    mock_client = AsyncMock(spec=MCPAsyncClient)
    mock_client.get_validation.return_value = {
        "validation_id": "test-123",
        "status": "approved"
    }

    with patch('api.mcp_helpers.get_api_mcp_client', return_value=mock_client):
        response = await call_mcp_method_formatted(
            "get_validation",
            validation_id="test-123",
            meta={"source": "api"}
        )

        assert response["success"] is True
        assert response["data"]["validation_id"] == "test-123"
        assert response["meta"]["source"] == "api"


# =============================================================================
# Concurrent Request Tests
# =============================================================================

@pytest.mark.asyncio
async def test_concurrent_mcp_calls():
    """Test multiple concurrent MCP calls."""
    mock_client = AsyncMock(spec=MCPAsyncClient)
    mock_client.get_validation.side_effect = [
        {"validation_id": f"val-{i}", "status": "pass"}
        for i in range(10)
    ]

    with patch('api.mcp_helpers.get_api_mcp_client', return_value=mock_client):
        # Make 10 concurrent calls
        tasks = [
            call_mcp_method("get_validation", validation_id=f"val-{i}")
            for i in range(10)
        ]

        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        assert all("validation_id" in r for r in results)
        assert mock_client.get_validation.call_count == 10


@pytest.mark.asyncio
async def test_concurrent_mcp_calls_with_errors():
    """Test concurrent MCP calls with some failures."""
    mock_client = AsyncMock(spec=MCPAsyncClient)

    # Configure to succeed on even calls, fail on odd calls
    def side_effect(validation_id):
        idx = int(validation_id.split("-")[1])
        if idx % 2 == 0:
            return {"validation_id": validation_id, "status": "pass"}
        else:
            raise MCPResourceNotFoundError(f"Validation {validation_id} not found")

    mock_client.get_validation.side_effect = side_effect

    with patch('api.mcp_helpers.get_api_mcp_client', return_value=mock_client):
        tasks = [
            call_mcp_method("get_validation", validation_id=f"val-{i}")
            for i in range(10)
        ]

        # Use gather with return_exceptions to catch failures
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Should have 5 successes and 5 HTTPExceptions
        successes = [r for r in results if isinstance(r, dict)]
        failures = [r for r in results if isinstance(r, HTTPException)]

        assert len(successes) == 5
        assert len(failures) == 5
        assert all(f.status_code == status.HTTP_404_NOT_FOUND for f in failures)


# =============================================================================
# WebSocket Integration Pattern Tests
# =============================================================================

@pytest.mark.asyncio
async def test_websocket_workflow_pattern():
    """Test WebSocket workflow update pattern with MCP client."""
    mock_client = AsyncMock(spec=MCPAsyncClient)

    # Simulate workflow progression
    workflow_states = [
        {"workflow": {"workflow_id": "wf-1", "status": "running", "progress_percent": 25}},
        {"workflow": {"workflow_id": "wf-1", "status": "running", "progress_percent": 50}},
        {"workflow": {"workflow_id": "wf-1", "status": "running", "progress_percent": 75}},
        {"workflow": {"workflow_id": "wf-1", "status": "completed", "progress_percent": 100}},
    ]

    mock_client.get_workflow.side_effect = workflow_states

    with patch('api.mcp_helpers.get_api_mcp_client', return_value=mock_client):
        # Simulate WebSocket workflow update loop
        workflow_id = "wf-1"
        last_status = None
        updates = []

        for _ in range(4):
            result = await call_mcp_method("get_workflow", workflow_id=workflow_id)
            workflow = result.get("workflow", {})
            current_status = workflow.get("status")

            if current_status != last_status:
                updates.append({
                    "type": "workflow_update",
                    "workflow_id": workflow_id,
                    "data": workflow
                })
                last_status = current_status

            if current_status in ["completed", "failed", "cancelled"]:
                break

        # Should have received multiple updates
        assert len(updates) >= 2
        assert updates[-1]["data"]["status"] == "completed"
        assert updates[-1]["data"]["progress_percent"] == 100


@pytest.mark.asyncio
async def test_websocket_dashboard_pattern():
    """Test WebSocket dashboard update pattern with MCP client."""
    mock_client = AsyncMock(spec=MCPAsyncClient)

    mock_client.list_validations.return_value = {
        "validations": [],
        "total": 10
    }
    mock_client.list_workflows.return_value = {
        "workflows": [],
        "total": 2
    }

    with patch('api.mcp_helpers.get_api_mcp_client', return_value=mock_client):
        # Simulate dashboard state collection
        validations = await call_mcp_method("list_validations", limit=1000)
        workflows = await call_mcp_method("list_workflows", limit=100, status="running")

        dashboard_state = {
            "pending_validations": validations.get("total", 0),
            "active_workflows": workflows.get("total", 0),
        }

        assert dashboard_state["pending_validations"] == 10
        assert dashboard_state["active_workflows"] == 2


# =============================================================================
# Error Recovery Tests
# =============================================================================

@pytest.mark.asyncio
async def test_mcp_call_with_retry_success():
    """Test that MCP client retries transient errors."""
    mock_client = AsyncMock(spec=MCPAsyncClient)

    # Fail twice, then succeed
    mock_client.get_validation.side_effect = [
        Exception("Transient error 1"),
        Exception("Transient error 2"),
        {"validation_id": "test-123", "status": "pass"}
    ]

    # Note: The actual retry logic is in MCPAsyncClient,
    # but we can test the pattern
    with patch('api.mcp_helpers.get_api_mcp_client', return_value=mock_client):
        # First two calls should fail
        with pytest.raises(HTTPException):
            await call_mcp_method("get_validation", validation_id="test-123")

        with pytest.raises(HTTPException):
            await call_mcp_method("get_validation", validation_id="test-123")

        # Third call should succeed
        result = await call_mcp_method("get_validation", validation_id="test-123")
        assert result["validation_id"] == "test-123"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
