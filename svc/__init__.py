# file: svc/__init__.py
"""
Service layer for TBCV validation system.
Contains MCP server, clients, and related service components.
"""

from . import mcp_server
from .mcp_client import (
    MCPSyncClient,
    MCPAsyncClient,
    get_mcp_sync_client,
    get_mcp_async_client
)
from .mcp_exceptions import (
    MCPError,
    MCPMethodNotFoundError,
    MCPInvalidParamsError,
    MCPInternalError,
    MCPTimeoutError,
    MCPValidationError,
    MCPResourceNotFoundError,
    exception_from_error_code
)

__all__ = [
    "mcp_server",
    "MCPSyncClient",
    "MCPAsyncClient",
    "get_mcp_sync_client",
    "get_mcp_async_client",
    "MCPError",
    "MCPMethodNotFoundError",
    "MCPInvalidParamsError",
    "MCPInternalError",
    "MCPTimeoutError",
    "MCPValidationError",
    "MCPResourceNotFoundError",
    "exception_from_error_code",
]
