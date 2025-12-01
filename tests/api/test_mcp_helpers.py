"""Tests for MCP helper utilities.

Tests cover:
- Singleton client management
- Dependency injection
- Error conversion to HTTP exceptions
- Response formatting
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi import HTTPException

from svc.mcp_exceptions import (
    MCPError,
    MCPMethodNotFoundError,
    MCPInvalidParamsError,
    MCPResourceNotFoundError,
    MCPTimeoutError,
    MCPValidationError,
    MCPInternalError,
)
from api.mcp_helpers import (
    get_api_mcp_client,
    MCPClientDependency,
    mcp_error_to_http_exception,
    format_mcp_response,
    call_mcp_method,
    call_mcp_method_formatted,
)


class TestSingletonClientManagement:
    """Test singleton MCP client management."""

    @pytest.mark.asyncio
    async def test_get_api_mcp_client_returns_same_instance(self):
        """Test that get_api_mcp_client returns the same instance."""
        # Reset singleton
        import api.mcp_helpers
        api.mcp_helpers._mcp_client = None

        # Get client twice
        client1 = await get_api_mcp_client()
        client2 = await get_api_mcp_client()

        # Should be the same instance
        assert client1 is client2

    @pytest.mark.asyncio
    async def test_mcp_client_dependency_returns_client(self):
        """Test MCPClientDependency callable returns client."""
        dependency = MCPClientDependency()
        client = await dependency()

        assert client is not None
        assert hasattr(client, 'validate_file')
        assert hasattr(client, 'get_validation')


class TestErrorConversion:
    """Test MCP error to HTTP exception conversion."""

    def test_method_not_found_error_to_501(self):
        """Test MCPMethodNotFoundError converts to 501."""
        error = MCPMethodNotFoundError("Method not found", code=-32601)
        http_exc = mcp_error_to_http_exception(error)

        assert http_exc.status_code == 501
        assert "MCPMethodNotFoundError" in str(http_exc.detail)

    def test_invalid_params_error_to_400(self):
        """Test MCPInvalidParamsError converts to 400."""
        error = MCPInvalidParamsError("Invalid parameters", code=-32602)
        http_exc = mcp_error_to_http_exception(error)

        assert http_exc.status_code == 400
        assert "MCPInvalidParamsError" in str(http_exc.detail)

    def test_resource_not_found_error_to_404(self):
        """Test MCPResourceNotFoundError converts to 404."""
        error = MCPResourceNotFoundError("Resource not found", code=-32001)
        http_exc = mcp_error_to_http_exception(error)

        assert http_exc.status_code == 404
        assert "MCPResourceNotFoundError" in str(http_exc.detail)

    def test_timeout_error_to_504(self):
        """Test MCPTimeoutError converts to 504."""
        error = MCPTimeoutError("Request timeout")
        http_exc = mcp_error_to_http_exception(error)

        assert http_exc.status_code == 504
        assert "MCPTimeoutError" in str(http_exc.detail)

    def test_validation_error_to_422(self):
        """Test MCPValidationError converts to 422."""
        error = MCPValidationError("Validation failed", code=-32000)
        http_exc = mcp_error_to_http_exception(error)

        assert http_exc.status_code == 422
        assert "MCPValidationError" in str(http_exc.detail)

    def test_internal_error_to_500(self):
        """Test MCPInternalError converts to 500."""
        error = MCPInternalError("Internal error", code=-32603)
        http_exc = mcp_error_to_http_exception(error)

        assert http_exc.status_code == 500
        assert "MCPInternalError" in str(http_exc.detail)

    def test_generic_error_to_500(self):
        """Test generic MCPError converts to 500."""
        error = MCPError("Unknown error")
        http_exc = mcp_error_to_http_exception(error)

        assert http_exc.status_code == 500
        assert "MCPError" in str(http_exc.detail)

    def test_error_with_additional_data(self):
        """Test error with additional data is preserved."""
        error = MCPResourceNotFoundError(
            "Validation not found",
            code=-32001,
            data={"validation_id": "abc123"}
        )
        http_exc = mcp_error_to_http_exception(error)

        assert http_exc.status_code == 404
        assert isinstance(http_exc.detail, dict)
        assert http_exc.detail["data"]["validation_id"] == "abc123"


class TestResponseFormatting:
    """Test response formatting utilities."""

    def test_format_mcp_response_basic(self):
        """Test basic response formatting."""
        result = {"validation_id": "test123", "status": "completed"}
        response = format_mcp_response(result)

        assert response["success"] is True
        assert response["data"] == result
        assert "meta" in response
        assert "timestamp" in response["meta"]

    def test_format_mcp_response_with_meta(self):
        """Test response formatting with metadata."""
        result = {"count": 42}
        meta = {"cached": True, "execution_time_ms": 125}
        response = format_mcp_response(result, meta=meta)

        assert response["success"] is True
        assert response["data"] == result
        assert response["meta"]["cached"] is True
        assert response["meta"]["execution_time_ms"] == 125
        assert "timestamp" in response["meta"]

    def test_format_mcp_response_failure(self):
        """Test response formatting for failures."""
        result = {"error": "Something went wrong"}
        response = format_mcp_response(result, success=False)

        assert response["success"] is False
        assert response["data"] == result


class TestConvenienceFunctions:
    """Test convenience functions for calling MCP methods."""

    @pytest.mark.asyncio
    async def test_call_mcp_method_success(self):
        """Test successful MCP method call."""
        with patch('api.mcp_helpers.get_api_mcp_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_validation = AsyncMock(
                return_value={"validation_id": "test123"}
            )
            mock_get_client.return_value = mock_client

            result = await call_mcp_method(
                "get_validation",
                validation_id="test123"
            )

            assert result["validation_id"] == "test123"
            mock_client.get_validation.assert_awaited_once_with(
                validation_id="test123"
            )

    @pytest.mark.asyncio
    async def test_call_mcp_method_mcp_error(self):
        """Test MCP error handling in call_mcp_method."""
        with patch('api.mcp_helpers.get_api_mcp_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_validation = AsyncMock(
                side_effect=MCPResourceNotFoundError("Not found", code=-32001)
            )
            mock_get_client.return_value = mock_client

            with pytest.raises(HTTPException) as exc_info:
                await call_mcp_method("get_validation", validation_id="test123")

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_call_mcp_method_invalid_method(self):
        """Test calling non-existent method."""
        with patch('api.mcp_helpers.get_api_mcp_client') as mock_get_client:
            mock_client = AsyncMock()
            # Configure client to raise MCPMethodNotFoundError when method doesn't exist
            mock_client.invalid_method = AsyncMock(
                side_effect=MCPMethodNotFoundError("Method 'invalid_method' not found")
            )
            mock_get_client.return_value = mock_client

            with pytest.raises(HTTPException) as exc_info:
                await call_mcp_method("invalid_method", param="value")

            assert exc_info.value.status_code == 501

    @pytest.mark.asyncio
    async def test_call_mcp_method_formatted_success(self):
        """Test formatted MCP method call."""
        with patch('api.mcp_helpers.get_api_mcp_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_validation = AsyncMock(
                return_value={"validation_id": "test123"}
            )
            mock_get_client.return_value = mock_client

            response = await call_mcp_method_formatted(
                "get_validation",
                validation_id="test123",
                meta={"source": "test"}
            )

            assert response["success"] is True
            assert response["data"]["validation_id"] == "test123"
            assert response["meta"]["source"] == "test"
            assert "timestamp" in response["meta"]


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple components."""

    @pytest.mark.asyncio
    async def test_full_request_flow_success(self):
        """Test complete request flow from endpoint to response."""
        with patch('api.mcp_helpers.get_api_mcp_client') as mock_get_client:
            # Setup mock client
            mock_client = AsyncMock()
            mock_client.validate_file = AsyncMock(return_value={
                "validation_id": "val123",
                "status": "completed",
                "issues": []
            })
            mock_get_client.return_value = mock_client

            # Simulate endpoint logic
            dependency = MCPClientDependency()
            client = await dependency()
            result = await client.validate_file(
                file_path="/path/to/file.md",
                family="words"
            )
            response = format_mcp_response(result)

            # Verify response
            assert response["success"] is True
            assert response["data"]["validation_id"] == "val123"
            assert response["data"]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_full_request_flow_error(self):
        """Test complete request flow with error handling."""
        with patch('api.mcp_helpers.get_api_mcp_client') as mock_get_client:
            # Setup mock client to raise error
            mock_client = AsyncMock()
            mock_client.get_validation = AsyncMock(
                side_effect=MCPResourceNotFoundError(
                    "Validation not found",
                    code=-32001,
                    data={"validation_id": "notfound"}
                )
            )
            mock_get_client.return_value = mock_client

            # Simulate endpoint logic with error
            dependency = MCPClientDependency()
            client = await dependency()

            with pytest.raises(HTTPException) as exc_info:
                try:
                    await client.get_validation("notfound")
                except MCPError as e:
                    raise mcp_error_to_http_exception(e)

            # Verify HTTP exception
            assert exc_info.value.status_code == 404
            assert "validation_id" in str(exc_info.value.detail)


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_format_mcp_response_empty_result(self):
        """Test formatting empty result."""
        result = {}
        response = format_mcp_response(result)

        assert response["success"] is True
        assert response["data"] == {}
        assert "meta" in response

    def test_format_mcp_response_none_meta(self):
        """Test formatting with None metadata."""
        result = {"test": "value"}
        response = format_mcp_response(result, meta=None)

        assert response["success"] is True
        assert response["data"] == result
        assert "timestamp" in response["meta"]

    def test_error_conversion_with_none_code(self):
        """Test error conversion when code is None."""
        error = MCPError("Error without code")
        http_exc = mcp_error_to_http_exception(error)

        assert http_exc.status_code == 500
        assert isinstance(http_exc.detail, dict)

    def test_error_conversion_with_none_data(self):
        """Test error conversion when data is None."""
        error = MCPInternalError("Error without data", code=-32603)
        http_exc = mcp_error_to_http_exception(error)

        assert http_exc.status_code == 500
        assert "data" not in http_exc.detail or http_exc.detail.get("data") is None
