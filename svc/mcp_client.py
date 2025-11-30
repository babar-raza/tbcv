"""MCP client wrappers for synchronous and asynchronous usage."""

import time
import asyncio
from typing import Dict, Any, List, Optional
from svc.mcp_server import create_mcp_client
from svc.mcp_exceptions import (
    MCPError,
    MCPInternalError,
    exception_from_error_code
)
from core.logging import get_logger

logger = get_logger(__name__)

# Singleton instances
_sync_client: Optional['MCPSyncClient'] = None
_async_client: Optional['MCPAsyncClient'] = None


class MCPSyncClient:
    """
    Synchronous MCP client for CLI usage.

    Provides convenient methods for all MCP operations with
    automatic error handling and retry logic.

    Example:
        >>> client = get_mcp_sync_client()
        >>> result = client.validate_folder("/path/to/docs")
        >>> print(result['files_processed'])
    """

    def __init__(self, timeout: int = 30, max_retries: int = 3):
        """
        Initialize synchronous MCP client.

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for transient errors
        """
        self._server = create_mcp_client()
        self.timeout = timeout
        self.max_retries = max_retries
        self._request_counter = 0

    def _call(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call MCP method and handle response.

        Args:
            method: Method name
            params: Method parameters

        Returns:
            Method result dictionary

        Raises:
            MCPError: If request fails
        """
        self._request_counter += 1
        request_id = self._request_counter

        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": request_id
        }

        logger.debug(f"MCP request: method={method}, id={request_id}")

        for attempt in range(self.max_retries):
            try:
                response = self._server.handle_request(request)

                if "error" in response:
                    error = response["error"]
                    raise exception_from_error_code(
                        error["code"],
                        error["message"],
                        error.get("data")
                    )

                logger.debug(f"MCP response: method={method}, id={request_id}")
                return response.get("result", {})

            except MCPError:
                # Don't retry on application errors
                raise
            except Exception as e:
                # Retry on transient errors
                if attempt == self.max_retries - 1:
                    raise MCPInternalError(f"MCP request failed: {e}")

                logger.warning(
                    f"MCP request failed (attempt {attempt + 1}), retrying..."
                )
                # Exponential backoff: 0.1s, 0.2s, 0.4s, etc.
                time.sleep(0.1 * (2 ** attempt))

    # ========================================================================
    # Validation Methods
    # ========================================================================

    def validate_folder(
        self,
        folder_path: str,
        recursive: bool = True
    ) -> Dict[str, Any]:
        """
        Validate all markdown files in a folder.

        Args:
            folder_path: Path to folder
            recursive: Whether to search recursively

        Returns:
            Validation results with files_processed count

        Raises:
            MCPError: If validation fails
        """
        return self._call("validate_folder", {
            "folder_path": folder_path,
            "recursive": recursive
        })

    # ========================================================================
    # Approval Methods
    # ========================================================================

    def approve(self, ids: List[str]) -> Dict[str, Any]:
        """
        Approve validation records.

        Args:
            ids: List of validation IDs to approve

        Returns:
            Results with approved_count and errors list

        Raises:
            MCPError: If approval fails
        """
        return self._call("approve", {"ids": ids})

    def reject(self, ids: List[str]) -> Dict[str, Any]:
        """
        Reject validation records.

        Args:
            ids: List of validation IDs to reject

        Returns:
            Results with rejected_count and errors list

        Raises:
            MCPError: If rejection fails
        """
        return self._call("reject", {"ids": ids})

    # ========================================================================
    # Enhancement Methods
    # ========================================================================

    def enhance(self, ids: List[str]) -> Dict[str, Any]:
        """
        Enhance approved validation records.

        Args:
            ids: List of validation IDs to enhance

        Returns:
            Results with enhanced_count, errors, and enhancements list

        Raises:
            MCPError: If enhancement fails
        """
        return self._call("enhance", {"ids": ids})


class MCPAsyncClient:
    """
    Asynchronous MCP client for API usage.

    Provides the same interface as MCPSyncClient but with async/await
    support for use in FastAPI and other async frameworks.

    Example:
        >>> client = get_mcp_async_client()
        >>> result = await client.validate_folder("/path/to/docs")
        >>> print(result['files_processed'])
    """

    def __init__(self, timeout: int = 30, max_retries: int = 3):
        """
        Initialize asynchronous MCP client.

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for transient errors
        """
        self._server = create_mcp_client()
        self.timeout = timeout
        self.max_retries = max_retries
        self._request_counter = 0

    async def _call(
        self,
        method: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Call MCP method asynchronously and handle response.

        Args:
            method: Method name
            params: Method parameters

        Returns:
            Method result dictionary

        Raises:
            MCPError: If request fails
        """
        self._request_counter += 1
        request_id = self._request_counter

        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": request_id
        }

        logger.debug(f"MCP request: method={method}, id={request_id}")

        for attempt in range(self.max_retries):
            try:
                # Run sync handle_request in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    self._server.handle_request,
                    request
                )

                if "error" in response:
                    error = response["error"]
                    raise exception_from_error_code(
                        error["code"],
                        error["message"],
                        error.get("data")
                    )

                logger.debug(f"MCP response: method={method}, id={request_id}")
                return response.get("result", {})

            except MCPError:
                # Don't retry on application errors
                raise
            except Exception as e:
                # Retry on transient errors
                if attempt == self.max_retries - 1:
                    raise MCPInternalError(f"MCP request failed: {e}")

                logger.warning(
                    f"MCP request failed (attempt {attempt + 1}), retrying..."
                )
                # Exponential backoff: 0.1s, 0.2s, 0.4s, etc.
                await asyncio.sleep(0.1 * (2 ** attempt))

    # ========================================================================
    # Validation Methods
    # ========================================================================

    async def validate_folder(
        self,
        folder_path: str,
        recursive: bool = True
    ) -> Dict[str, Any]:
        """
        Validate all markdown files in a folder asynchronously.

        Args:
            folder_path: Path to folder
            recursive: Whether to search recursively

        Returns:
            Validation results with files_processed count

        Raises:
            MCPError: If validation fails
        """
        return await self._call("validate_folder", {
            "folder_path": folder_path,
            "recursive": recursive
        })

    # ========================================================================
    # Approval Methods
    # ========================================================================

    async def approve(self, ids: List[str]) -> Dict[str, Any]:
        """
        Approve validation records asynchronously.

        Args:
            ids: List of validation IDs to approve

        Returns:
            Results with approved_count and errors list

        Raises:
            MCPError: If approval fails
        """
        return await self._call("approve", {"ids": ids})

    async def reject(self, ids: List[str]) -> Dict[str, Any]:
        """
        Reject validation records asynchronously.

        Args:
            ids: List of validation IDs to reject

        Returns:
            Results with rejected_count and errors list

        Raises:
            MCPError: If rejection fails
        """
        return await self._call("reject", {"ids": ids})

    # ========================================================================
    # Enhancement Methods
    # ========================================================================

    async def enhance(self, ids: List[str]) -> Dict[str, Any]:
        """
        Enhance approved validation records asynchronously.

        Args:
            ids: List of validation IDs to enhance

        Returns:
            Results with enhanced_count, errors, and enhancements list

        Raises:
            MCPError: If enhancement fails
        """
        return await self._call("enhance", {"ids": ids})


def get_mcp_sync_client(
    timeout: int = 30,
    max_retries: int = 3
) -> MCPSyncClient:
    """
    Get singleton instance of synchronous MCP client.

    Args:
        timeout: Request timeout in seconds
        max_retries: Maximum number of retries

    Returns:
        MCPSyncClient instance
    """
    global _sync_client
    if _sync_client is None:
        _sync_client = MCPSyncClient(timeout=timeout, max_retries=max_retries)
    return _sync_client


def get_mcp_async_client(
    timeout: int = 30,
    max_retries: int = 3
) -> MCPAsyncClient:
    """
    Get singleton instance of asynchronous MCP client.

    Args:
        timeout: Request timeout in seconds
        max_retries: Maximum number of retries

    Returns:
        MCPAsyncClient instance
    """
    global _async_client
    if _async_client is None:
        _async_client = MCPAsyncClient(timeout=timeout, max_retries=max_retries)
    return _async_client
