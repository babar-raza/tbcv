"""MCP helper utilities for FastAPI integration.

This module provides utilities for integrating MCP async client with FastAPI:
- Singleton client management
- Dependency injection
- Error conversion to HTTP exceptions
- Response formatting

Example:
    from fastapi import Depends
    from api.mcp_helpers import MCPClientDependency, format_mcp_response

    @app.get("/validations/{validation_id}")
    async def get_validation(
        validation_id: str,
        client: MCPAsyncClient = Depends(MCPClientDependency())
    ):
        result = await client.get_validation(validation_id)
        return format_mcp_response(result)
"""

from typing import Dict, Any, Optional
from fastapi import Depends, HTTPException, status

from svc.mcp_client import MCPAsyncClient, get_mcp_async_client
from svc.mcp_exceptions import (
    MCPError,
    MCPMethodNotFoundError,
    MCPInvalidParamsError,
    MCPResourceNotFoundError,
    MCPTimeoutError,
    MCPValidationError,
    MCPInternalError,
)
from core.logging import get_logger

logger = get_logger(__name__)

# =============================================================================
# Singleton Client Management
# =============================================================================

_mcp_client: Optional[MCPAsyncClient] = None


async def get_api_mcp_client() -> MCPAsyncClient:
    """
    Get singleton async MCP client for API.

    This ensures a single MCP client instance is shared across all API
    requests, improving performance and resource utilization.

    Returns:
        MCPAsyncClient: The singleton MCP async client instance

    Example:
        >>> client = await get_api_mcp_client()
        >>> result = await client.validate_file("/path/to/file.md")
    """
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = get_mcp_async_client()
        logger.info("Initialized singleton MCP async client for API")
    return _mcp_client


# =============================================================================
# FastAPI Dependency Injection
# =============================================================================


class MCPClientDependency:
    """
    FastAPI dependency for MCP client injection.

    This dependency can be used in FastAPI route handlers to automatically
    inject the MCP client, enabling clean separation of concerns and easier
    testing.

    Example:
        from fastapi import Depends
        from api.mcp_helpers import MCPClientDependency

        mcp_client = MCPClientDependency()

        @app.get("/validations")
        async def list_validations(
            client: MCPAsyncClient = Depends(mcp_client)
        ):
            return await client.list_validations()
    """

    async def __call__(self) -> MCPAsyncClient:
        """
        Return the singleton MCP client instance.

        Returns:
            MCPAsyncClient: The MCP async client
        """
        return await get_api_mcp_client()


# =============================================================================
# Error Conversion
# =============================================================================


def mcp_error_to_http_exception(error: MCPError) -> HTTPException:
    """
    Convert MCP error to HTTP exception with appropriate status code.

    This function maps MCP-specific errors to standard HTTP status codes,
    providing consistent error responses across the API.

    Status Code Mapping:
    - MCPMethodNotFoundError → 501 Not Implemented
    - MCPInvalidParamsError → 400 Bad Request
    - MCPResourceNotFoundError → 404 Not Found
    - MCPTimeoutError → 504 Gateway Timeout
    - MCPValidationError → 422 Unprocessable Entity
    - MCPInternalError → 500 Internal Server Error
    - MCPError (generic) → 500 Internal Server Error

    Args:
        error: The MCP error to convert

    Returns:
        HTTPException: FastAPI HTTP exception with appropriate status code

    Example:
        try:
            result = await client.get_validation(validation_id)
        except MCPError as e:
            raise mcp_error_to_http_exception(e)
    """
    # Map MCP error types to HTTP status codes
    error_mapping = {
        MCPMethodNotFoundError: (
            status.HTTP_501_NOT_IMPLEMENTED,
            "Method not implemented"
        ),
        MCPInvalidParamsError: (
            status.HTTP_400_BAD_REQUEST,
            "Invalid parameters"
        ),
        MCPResourceNotFoundError: (
            status.HTTP_404_NOT_FOUND,
            "Resource not found"
        ),
        MCPTimeoutError: (
            status.HTTP_504_GATEWAY_TIMEOUT,
            "Request timeout"
        ),
        MCPValidationError: (
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Validation failed"
        ),
        MCPInternalError: (
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Internal server error"
        ),
    }

    # Get status code and default detail for error type
    error_type = type(error)
    status_code, default_detail = error_mapping.get(
        error_type,
        (status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal server error")
    )

    # Build error detail
    detail = {
        "error": str(error),
        "type": error_type.__name__,
    }

    # Include additional error data if available
    if error.code is not None:
        detail["code"] = error.code
    if error.data is not None:
        detail["data"] = error.data

    logger.error(
        f"MCP error converted to HTTP {status_code}: {error_type.__name__} - {error}",
        extra={
            "error_type": error_type.__name__,
            "error_code": error.code,
            "http_status": status_code,
        }
    )

    return HTTPException(
        status_code=status_code,
        detail=detail
    )


# =============================================================================
# Response Formatting
# =============================================================================


def format_mcp_response(
    result: Dict[str, Any],
    success: bool = True,
    meta: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Format MCP result as standard API response.

    This function provides consistent response formatting across all API
    endpoints, with standard fields for success status, data, and metadata.

    Response Structure:
        {
            "success": true,
            "data": { ... },
            "meta": {
                "timestamp": "2024-01-15T10:30:00Z",
                "version": "1.0.0",
                ...
            }
        }

    Args:
        result: The MCP method result dictionary
        success: Success status (default True)
        meta: Optional metadata to include in response

    Returns:
        Dict[str, Any]: Formatted API response

    Example:
        result = await client.get_validation(validation_id)
        return format_mcp_response(
            result,
            meta={"cached": False, "execution_time_ms": 125}
        )
    """
    from datetime import datetime, timezone

    # Build base response
    response = {
        "success": success,
        "data": result,
    }

    # Build metadata
    meta_dict = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Merge additional metadata if provided
    if meta is not None:
        meta_dict.update(meta)

    response["meta"] = meta_dict

    return response


# =============================================================================
# Convenience Functions
# =============================================================================


async def call_mcp_method(
    method_name: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Call MCP method by name with automatic error handling.

    This is a convenience function that combines client access, method
    invocation, and error handling in a single call.

    Args:
        method_name: Name of the MCP client method to call
        **kwargs: Keyword arguments to pass to the method

    Returns:
        Dict[str, Any]: Method result

    Raises:
        HTTPException: If the MCP call fails

    Example:
        result = await call_mcp_method(
            "validate_file",
            file_path="/path/to/file.md",
            family="words"
        )
    """
    try:
        client = await get_api_mcp_client()
        method = getattr(client, method_name)
        return await method(**kwargs)
    except MCPError as e:
        raise mcp_error_to_http_exception(e)
    except AttributeError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"Method '{method_name}' not found"
        )
    except Exception as e:
        logger.exception(f"Unexpected error calling MCP method '{method_name}'")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


async def call_mcp_method_formatted(
    method_name: str,
    meta: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Call MCP method and return formatted response.

    This combines call_mcp_method and format_mcp_response for the most
    common use case: calling an MCP method and returning a formatted response.

    Args:
        method_name: Name of the MCP client method to call
        meta: Optional metadata to include in response
        **kwargs: Keyword arguments to pass to the method

    Returns:
        Dict[str, Any]: Formatted API response

    Raises:
        HTTPException: If the MCP call fails

    Example:
        return await call_mcp_method_formatted(
            "validate_file",
            file_path="/path/to/file.md",
            meta={"source": "api"}
        )
    """
    result = await call_mcp_method(method_name, **kwargs)
    return format_mcp_response(result, meta=meta)
