"""Exception classes for MCP client operations."""

from typing import Any, Optional


class MCPError(Exception):
    """Base exception for all MCP errors."""

    def __init__(
        self,
        message: str,
        code: Optional[int] = None,
        data: Optional[Any] = None
    ):
        """
        Initialize MCP error.

        Args:
            message: Error message
            code: JSON-RPC error code
            data: Additional error data
        """
        super().__init__(message)
        self.code = code
        self.data = data


class MCPMethodNotFoundError(MCPError):
    """Raised when requested method does not exist."""
    pass


class MCPInvalidParamsError(MCPError):
    """Raised when method parameters are invalid."""
    pass


class MCPInternalError(MCPError):
    """Raised when MCP server encounters internal error."""
    pass


class MCPTimeoutError(MCPError):
    """Raised when MCP request times out."""
    pass


class MCPValidationError(MCPError):
    """Raised when validation fails."""
    pass


class MCPResourceNotFoundError(MCPError):
    """Raised when requested resource is not found."""
    pass


def exception_from_error_code(
    code: int,
    message: str,
    data: Optional[Any] = None
) -> MCPError:
    """
    Create appropriate exception based on JSON-RPC error code.

    Args:
        code: JSON-RPC error code
        message: Error message
        data: Additional error data

    Returns:
        Appropriate MCPError subclass instance
    """
    error_map = {
        -32601: MCPMethodNotFoundError,  # METHOD_NOT_FOUND
        -32602: MCPInvalidParamsError,   # INVALID_PARAMS
        -32603: MCPInternalError,        # INTERNAL_ERROR
        -32000: MCPValidationError,      # Custom: VALIDATION_FAILED
        -32001: MCPResourceNotFoundError,  # Custom: RESOURCE_NOT_FOUND
    }

    exc_class = error_map.get(code, MCPError)
    return exc_class(message, code=code, data=data)
