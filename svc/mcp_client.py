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

    def validate_file(
        self,
        file_path: str,
        family: str = "words",
        validation_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Validate a single file.

        Args:
            file_path: Path to file to validate
            family: Plugin family (default "words")
            validation_types: List of specific validators to run

        Returns:
            Validation results with validation_id and issues

        Raises:
            MCPError: If validation fails
        """
        return self._call("validate_file", {
            "file_path": file_path,
            "family": family,
            "validation_types": validation_types
        })

    def validate_content(
        self,
        content: str,
        file_path: str = "temp.md",
        validation_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Validate content string without requiring a physical file.

        Args:
            content: Markdown content to validate
            file_path: Virtual file path for context (default "temp.md")
            validation_types: List of specific validators to run

        Returns:
            Validation results with validation_id and issues

        Raises:
            MCPError: If validation fails
        """
        return self._call("validate_content", {
            "content": content,
            "file_path": file_path,
            "validation_types": validation_types
        })

    def get_validation(self, validation_id: str) -> Dict[str, Any]:
        """
        Get validation record by ID.

        Args:
            validation_id: ID of validation to retrieve

        Returns:
            Validation record dictionary

        Raises:
            MCPError: If validation not found
        """
        return self._call("get_validation", {
            "validation_id": validation_id
        })

    def list_validations(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None,
        file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List validation records with optional filtering.

        Args:
            limit: Maximum number of results (default 100)
            offset: Number of results to skip (default 0)
            status: Filter by status (optional)
            file_path: Filter by file path (optional)

        Returns:
            Dictionary with validations list and total count

        Raises:
            MCPError: If listing fails
        """
        return self._call("list_validations", {
            "limit": limit,
            "offset": offset,
            "status": status,
            "file_path": file_path
        })

    def update_validation(
        self,
        validation_id: str,
        notes: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update validation metadata.

        Args:
            validation_id: ID of validation to update
            notes: New notes (optional)
            status: New status (optional)

        Returns:
            Success status and validation_id

        Raises:
            MCPError: If update fails
        """
        return self._call("update_validation", {
            "validation_id": validation_id,
            "notes": notes,
            "status": status
        })

    def delete_validation(self, validation_id: str) -> Dict[str, Any]:
        """
        Delete validation record.

        Args:
            validation_id: ID of validation to delete

        Returns:
            Success status and validation_id

        Raises:
            MCPError: If deletion fails
        """
        return self._call("delete_validation", {
            "validation_id": validation_id
        })

    def revalidate(self, validation_id: str) -> Dict[str, Any]:
        """
        Re-run validation on the same file.

        Args:
            validation_id: ID of original validation

        Returns:
            Success status with new and original validation IDs

        Raises:
            MCPError: If revalidation fails
        """
        return self._call("revalidate", {
            "validation_id": validation_id
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

    # ========================================================================
    # Admin Methods
    # ========================================================================

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get system health status.

        Returns:
            System status with component health and resource usage

        Raises:
            MCPError: If status check fails
        """
        return self._call("get_system_status", {})

    def clear_cache(self, cache_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Clear all caches.

        Args:
            cache_types: Optional list of specific cache types to clear

        Returns:
            Results with cleared_items count

        Raises:
            MCPError: If cache clear fails
        """
        return self._call("clear_cache", {"cache_types": cache_types})

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Cache statistics with totals and breakdowns

        Raises:
            MCPError: If stats retrieval fails
        """
        return self._call("get_cache_stats", {})

    def cleanup_cache(self, max_age_hours: int = 24) -> Dict[str, Any]:
        """
        Clean up stale cache entries.

        Args:
            max_age_hours: Maximum age in hours for cache entries

        Returns:
            Results with cleaned_items count

        Raises:
            MCPError: If cleanup fails
        """
        return self._call("cleanup_cache", {"max_age_hours": max_age_hours})

    def rebuild_cache(self) -> Dict[str, Any]:
        """
        Rebuild cache from scratch.

        Returns:
            Results with rebuilt_items count

        Raises:
            MCPError: If rebuild fails
        """
        return self._call("rebuild_cache", {})

    def reload_agent(self, agent_id: str) -> Dict[str, Any]:
        """
        Reload specific agent.

        Args:
            agent_id: Agent ID to reload

        Returns:
            Results with agent_id and reloaded_at timestamp

        Raises:
            MCPError: If reload fails
        """
        return self._call("reload_agent", {"agent_id": agent_id})

    def run_gc(self) -> Dict[str, Any]:
        """
        Run garbage collection.

        Returns:
            Results with collected_objects count

        Raises:
            MCPError: If GC fails
        """
        return self._call("run_gc", {})

    def enable_maintenance_mode(
        self,
        reason: str = "",
        enabled_by: str = "system"
    ) -> Dict[str, Any]:
        """
        Enable maintenance mode.

        Args:
            reason: Reason for maintenance
            enabled_by: User/system enabling maintenance

        Returns:
            Results with enabled_at timestamp

        Raises:
            MCPError: If enable fails
        """
        return self._call("enable_maintenance_mode", {
            "reason": reason,
            "enabled_by": enabled_by
        })

    def disable_maintenance_mode(self) -> Dict[str, Any]:
        """
        Disable maintenance mode.

        Returns:
            Results with disabled_at timestamp

        Raises:
            MCPError: If disable fails
        """
        return self._call("disable_maintenance_mode", {})

    def create_checkpoint(
        self,
        name: str = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create system checkpoint.

        Args:
            name: Optional checkpoint name
            metadata: Optional metadata dictionary

        Returns:
            Results with checkpoint_id and created_at timestamp

        Raises:
            MCPError: If checkpoint creation fails
        """
        return self._call("create_checkpoint", {
            "name": name,
            "metadata": metadata
        })


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

    async def validate_file(
        self,
        file_path: str,
        family: str = "words",
        validation_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Validate a single file asynchronously.

        Args:
            file_path: Path to file to validate
            family: Plugin family (default "words")
            validation_types: List of specific validators to run

        Returns:
            Validation results with validation_id and issues

        Raises:
            MCPError: If validation fails
        """
        return await self._call("validate_file", {
            "file_path": file_path,
            "family": family,
            "validation_types": validation_types
        })

    async def validate_content(
        self,
        content: str,
        file_path: str = "temp.md",
        validation_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Validate content string asynchronously.

        Args:
            content: Markdown content to validate
            file_path: Virtual file path for context (default "temp.md")
            validation_types: List of specific validators to run

        Returns:
            Validation results with validation_id and issues

        Raises:
            MCPError: If validation fails
        """
        return await self._call("validate_content", {
            "content": content,
            "file_path": file_path,
            "validation_types": validation_types
        })

    async def get_validation(self, validation_id: str) -> Dict[str, Any]:
        """
        Get validation record by ID asynchronously.

        Args:
            validation_id: ID of validation to retrieve

        Returns:
            Validation record dictionary

        Raises:
            MCPError: If validation not found
        """
        return await self._call("get_validation", {
            "validation_id": validation_id
        })

    async def list_validations(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None,
        file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List validation records asynchronously.

        Args:
            limit: Maximum number of results (default 100)
            offset: Number of results to skip (default 0)
            status: Filter by status (optional)
            file_path: Filter by file path (optional)

        Returns:
            Dictionary with validations list and total count

        Raises:
            MCPError: If listing fails
        """
        return await self._call("list_validations", {
            "limit": limit,
            "offset": offset,
            "status": status,
            "file_path": file_path
        })

    async def update_validation(
        self,
        validation_id: str,
        notes: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update validation metadata asynchronously.

        Args:
            validation_id: ID of validation to update
            notes: New notes (optional)
            status: New status (optional)

        Returns:
            Success status and validation_id

        Raises:
            MCPError: If update fails
        """
        return await self._call("update_validation", {
            "validation_id": validation_id,
            "notes": notes,
            "status": status
        })

    async def delete_validation(self, validation_id: str) -> Dict[str, Any]:
        """
        Delete validation record asynchronously.

        Args:
            validation_id: ID of validation to delete

        Returns:
            Success status and validation_id

        Raises:
            MCPError: If deletion fails
        """
        return await self._call("delete_validation", {
            "validation_id": validation_id
        })

    async def revalidate(self, validation_id: str) -> Dict[str, Any]:
        """
        Re-run validation asynchronously.

        Args:
            validation_id: ID of original validation

        Returns:
            Success status with new and original validation IDs

        Raises:
            MCPError: If revalidation fails
        """
        return await self._call("revalidate", {
            "validation_id": validation_id
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

    # ========================================================================
    # Admin Methods
    # ========================================================================

    async def get_system_status(self) -> Dict[str, Any]:
        """Get system health status asynchronously."""
        return await self._call("get_system_status", {})

    async def clear_cache(self, cache_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """Clear all caches asynchronously."""
        return await self._call("clear_cache", {"cache_types": cache_types})

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics asynchronously."""
        return await self._call("get_cache_stats", {})

    async def cleanup_cache(self, max_age_hours: int = 24) -> Dict[str, Any]:
        """Clean up stale cache entries asynchronously."""
        return await self._call("cleanup_cache", {"max_age_hours": max_age_hours})

    async def rebuild_cache(self) -> Dict[str, Any]:
        """Rebuild cache from scratch asynchronously."""
        return await self._call("rebuild_cache", {})

    async def reload_agent(self, agent_id: str) -> Dict[str, Any]:
        """Reload specific agent asynchronously."""
        return await self._call("reload_agent", {"agent_id": agent_id})

    async def run_gc(self) -> Dict[str, Any]:
        """Run garbage collection asynchronously."""
        return await self._call("run_gc", {})

    async def enable_maintenance_mode(
        self,
        reason: str = "",
        enabled_by: str = "system"
    ) -> Dict[str, Any]:
        """Enable maintenance mode asynchronously."""
        return await self._call("enable_maintenance_mode", {
            "reason": reason,
            "enabled_by": enabled_by
        })

    async def disable_maintenance_mode(self) -> Dict[str, Any]:
        """Disable maintenance mode asynchronously."""
        return await self._call("disable_maintenance_mode", {})

    async def create_checkpoint(
        self,
        name: str = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create system checkpoint asynchronously."""
        return await self._call("create_checkpoint", {
            "name": name,
            "metadata": metadata
        })


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
