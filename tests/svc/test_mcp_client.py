"""
Tests for MCP client wrappers (sync and async).

Tests both synchronous and asynchronous client implementations
with error handling, retry logic, and integration with MCP server.
"""

import pytest
import asyncio
from pathlib import Path
from svc.mcp_client import (
    MCPSyncClient,
    MCPAsyncClient,
    get_mcp_sync_client,
    get_mcp_async_client
)
from svc.mcp_exceptions import (
    MCPError,
    MCPMethodNotFoundError,
    MCPInvalidParamsError,
    MCPInternalError,
    exception_from_error_code
)


class TestMCPExceptions:
    """Test MCP exception hierarchy."""

    def test_mcp_error_base(self):
        """Test MCPError base exception."""
        error = MCPError("Test error", code=-32000, data={"key": "value"})
        assert str(error) == "Test error"
        assert error.code == -32000
        assert error.data == {"key": "value"}

    def test_mcp_error_without_code(self):
        """Test MCPError without code."""
        error = MCPError("Test error")
        assert str(error) == "Test error"
        assert error.code is None
        assert error.data is None

    def test_method_not_found_error(self):
        """Test MCPMethodNotFoundError."""
        error = MCPMethodNotFoundError("Method not found")
        assert isinstance(error, MCPError)
        assert str(error) == "Method not found"

    def test_invalid_params_error(self):
        """Test MCPInvalidParamsError."""
        error = MCPInvalidParamsError("Invalid params")
        assert isinstance(error, MCPError)

    def test_internal_error(self):
        """Test MCPInternalError."""
        error = MCPInternalError("Internal error")
        assert isinstance(error, MCPError)

    def test_exception_from_error_code_method_not_found(self):
        """Test exception creation for method not found."""
        exc = exception_from_error_code(-32601, "Method not found")
        assert isinstance(exc, MCPMethodNotFoundError)
        assert exc.code == -32601
        assert str(exc) == "Method not found"

    def test_exception_from_error_code_invalid_params(self):
        """Test exception creation for invalid params."""
        exc = exception_from_error_code(-32602, "Invalid params")
        assert isinstance(exc, MCPInvalidParamsError)

    def test_exception_from_error_code_internal_error(self):
        """Test exception creation for internal error."""
        exc = exception_from_error_code(-32603, "Internal error")
        assert isinstance(exc, MCPInternalError)

    def test_exception_from_error_code_unknown(self):
        """Test exception creation for unknown error code."""
        exc = exception_from_error_code(-99999, "Unknown error")
        assert isinstance(exc, MCPError)
        assert not isinstance(exc, MCPMethodNotFoundError)

    def test_exception_from_error_code_with_data(self):
        """Test exception creation with data."""
        data = {"details": "More info"}
        exc = exception_from_error_code(-32601, "Error", data=data)
        assert exc.data == data


class TestMCPSyncClient:
    """Test synchronous MCP client."""

    @pytest.fixture
    def sync_client(self):
        """Create sync client instance."""
        return MCPSyncClient(timeout=5, max_retries=2)

    def test_client_initialization(self, sync_client):
        """Test client initializes correctly."""
        assert sync_client.timeout == 5
        assert sync_client.max_retries == 2
        assert sync_client._request_counter == 0
        assert sync_client._server is not None

    def test_validate_folder_missing_path(self, sync_client):
        """Test validate_folder with missing path raises error."""
        # This should raise an error because the method expects folder_path
        with pytest.raises(MCPError):
            sync_client._call("validate_folder", {})

    def test_approve_empty_list(self, sync_client):
        """Test approve with empty list."""
        result = sync_client.approve([])
        assert result["success"] is True
        assert result["approved_count"] == 0

    def test_approve_nonexistent_ids(self, sync_client):
        """Test approve with non-existent IDs."""
        result = sync_client.approve(["fake-id-1", "fake-id-2"])
        assert result["success"] is True
        assert result["approved_count"] == 0
        assert len(result["errors"]) > 0

    def test_reject_empty_list(self, sync_client):
        """Test reject with empty list."""
        result = sync_client.reject([])
        assert result["success"] is True
        assert result["rejected_count"] == 0

    def test_reject_nonexistent_ids(self, sync_client):
        """Test reject with non-existent IDs."""
        result = sync_client.reject(["fake-id-1"])
        assert result["success"] is True
        assert result["rejected_count"] == 0
        assert len(result["errors"]) > 0

    def test_enhance_empty_list(self, sync_client):
        """Test enhance with empty list."""
        result = sync_client.enhance([])
        assert result["success"] is True
        assert result["enhanced_count"] == 0
        assert result["enhancements"] == []

    def test_method_not_found(self, sync_client):
        """Test calling non-existent method."""
        with pytest.raises(MCPMethodNotFoundError):
            sync_client._call("nonexistent_method", {})

    def test_request_counter_increments(self, sync_client):
        """Test request counter increments."""
        assert sync_client._request_counter == 0
        sync_client.approve([])
        assert sync_client._request_counter == 1
        sync_client.reject([])
        assert sync_client._request_counter == 2

    def test_get_sync_client_singleton(self):
        """Test singleton pattern for sync client."""
        client1 = get_mcp_sync_client()
        client2 = get_mcp_sync_client()
        assert client1 is client2


class TestMCPAsyncClient:
    """Test asynchronous MCP client."""

    @pytest.fixture
    def async_client(self):
        """Create async client instance."""
        return MCPAsyncClient(timeout=5, max_retries=2)

    def test_client_initialization(self, async_client):
        """Test async client initializes correctly."""
        assert async_client.timeout == 5
        assert async_client.max_retries == 2
        assert async_client._request_counter == 0
        assert async_client._server is not None

    @pytest.mark.asyncio
    async def test_validate_folder_missing_path(self, async_client):
        """Test async validate_folder with missing path raises error."""
        with pytest.raises(MCPError):
            await async_client._call("validate_folder", {})

    @pytest.mark.asyncio
    async def test_approve_empty_list(self, async_client):
        """Test async approve with empty list."""
        result = await async_client.approve([])
        assert result["success"] is True
        assert result["approved_count"] == 0

    @pytest.mark.asyncio
    async def test_approve_nonexistent_ids(self, async_client):
        """Test async approve with non-existent IDs."""
        result = await async_client.approve(["fake-id-1", "fake-id-2"])
        assert result["success"] is True
        assert result["approved_count"] == 0
        assert len(result["errors"]) > 0

    @pytest.mark.asyncio
    async def test_reject_empty_list(self, async_client):
        """Test async reject with empty list."""
        result = await async_client.reject([])
        assert result["success"] is True
        assert result["rejected_count"] == 0

    @pytest.mark.asyncio
    async def test_reject_nonexistent_ids(self, async_client):
        """Test async reject with non-existent IDs."""
        result = await async_client.reject(["fake-id-1"])
        assert result["success"] is True
        assert result["rejected_count"] == 0
        assert len(result["errors"]) > 0

    @pytest.mark.asyncio
    async def test_enhance_empty_list(self, async_client):
        """Test async enhance with empty list."""
        result = await async_client.enhance([])
        assert result["success"] is True
        assert result["enhanced_count"] == 0
        assert result["enhancements"] == []

    @pytest.mark.asyncio
    async def test_method_not_found(self, async_client):
        """Test calling non-existent method asynchronously."""
        with pytest.raises(MCPMethodNotFoundError):
            await async_client._call("nonexistent_method", {})

    @pytest.mark.asyncio
    async def test_request_counter_increments(self, async_client):
        """Test async request counter increments."""
        assert async_client._request_counter == 0
        await async_client.approve([])
        assert async_client._request_counter == 1
        await async_client.reject([])
        assert async_client._request_counter == 2

    def test_get_async_client_singleton(self):
        """Test singleton pattern for async client."""
        client1 = get_mcp_async_client()
        client2 = get_mcp_async_client()
        assert client1 is client2


class TestMCPClientIntegration:
    """Integration tests for MCP clients with server."""

    @pytest.fixture
    def sync_client(self):
        """Create sync client for integration tests."""
        return MCPSyncClient()

    @pytest.fixture
    def async_client(self):
        """Create async client for integration tests."""
        return MCPAsyncClient()

    def test_sync_approve_reject_workflow(self, sync_client):
        """Test approval/rejection workflow with sync client."""
        # Approve non-existent IDs (should succeed but with 0 count)
        approve_result = sync_client.approve(["test-id-1"])
        assert approve_result["success"] is True
        assert approve_result["approved_count"] == 0

        # Reject non-existent IDs (should succeed but with 0 count)
        reject_result = sync_client.reject(["test-id-2"])
        assert reject_result["success"] is True
        assert reject_result["rejected_count"] == 0

    @pytest.mark.asyncio
    async def test_async_approve_reject_workflow(self, async_client):
        """Test approval/rejection workflow with async client."""
        # Approve non-existent IDs (should succeed but with 0 count)
        approve_result = await async_client.approve(["test-id-1"])
        assert approve_result["success"] is True
        assert approve_result["approved_count"] == 0

        # Reject non-existent IDs (should succeed but with 0 count)
        reject_result = await async_client.reject(["test-id-2"])
        assert reject_result["success"] is True
        assert reject_result["rejected_count"] == 0

    def test_sync_error_handling(self, sync_client):
        """Test error handling in sync client."""
        with pytest.raises(MCPMethodNotFoundError) as exc_info:
            sync_client._call("invalid_method", {})

        assert "Method not found" in str(exc_info.value)
        assert exc_info.value.code == -32601

    @pytest.mark.asyncio
    async def test_async_error_handling(self, async_client):
        """Test error handling in async client."""
        with pytest.raises(MCPMethodNotFoundError) as exc_info:
            await async_client._call("invalid_method", {})

        assert "Method not found" in str(exc_info.value)
        assert exc_info.value.code == -32601

    @pytest.mark.asyncio
    async def test_async_concurrent_requests(self, async_client):
        """Test concurrent async requests."""
        # Make multiple concurrent requests
        tasks = [
            async_client.approve([]),
            async_client.reject([]),
            async_client.enhance([])
        ]

        results = await asyncio.gather(*tasks)

        # All should succeed
        assert all(r["success"] for r in results)
        assert results[0]["approved_count"] == 0
        assert results[1]["rejected_count"] == 0
        assert results[2]["enhanced_count"] == 0
