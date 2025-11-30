# file: svc/__init__.py
"""
Service layer for TBCV validation system.
Contains MCP server and related service components.
"""

from . import mcp_server

__all__ = ["mcp_server"]
