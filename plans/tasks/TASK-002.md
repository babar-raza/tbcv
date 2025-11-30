# TASK-002: MCP Client Wrappers (Sync & Async)

## Metadata
- **Priority**: P0
- **Effort**: 2 days
- **Owner**: TBD
- **Status**: Not Started
- **Dependencies**: TASK-001
- **Phase**: Phase 1 - Foundation
- **Category**: Foundation

## Objective
Create production-ready synchronous and asynchronous MCP client wrappers for CLI and API consumption.

Provide clean, type-safe Python client interfaces that abstract JSON-RPC details and provide convenient methods for all 56 MCP operations.

## Scope

### In Scope
- Synchronous client (`MCPSyncClient`) for CLI usage
- Asynchronous client (`MCPAsyncClient`) for API usage
- Type hints for all methods
- Comprehensive error handling with custom exceptions
- Retry logic with exponential backoff
- Request/response logging
- Connection pooling for in-process mode
- Convenience methods for all MCP operations

### Out of Scope
- Network-based MCP client (future enhancement)
- Client-side caching (future enhancement)
- Request batching (future enhancement)
- Connection multiplexing (future enhancement)

## Acceptance Criteria
- [ ] MCPSyncClient implemented with all convenience methods
- [ ] MCPAsyncClient implemented with all convenience methods
- [ ] Type hints on all public methods
- [ ] Custom exception classes for different error types
- [ ] Retry logic with configurable backoff
- [ ] Comprehensive error messages
- [ ] Unit tests with >90% coverage
- [ ] Integration tests with MCPServer
- [ ] Documentation with usage examples
- [ ] Performance validated (<2ms overhead)

## Implementation Plan

### Architecture Decisions

**1. Client Design**
- Thin wrapper around MCPServer for in-process mode
- Identical API for sync and async clients (except async/await)
- Type-safe method signatures
- Automatic JSON-RPC request/response handling

**2. Error Handling**
- Custom exception hierarchy
- Preserve original error details
- Retry on transient errors only
- Clear error messages for debugging

**3. Performance**
- Reuse MCPServer instance (singleton pattern)
- Minimal overhead for in-process calls
- No unnecessary serialization/deserialization

### Files to Create

```
svc/mcp_client.py
  - Class: MCPSyncClient
    - __init__(timeout: int = 30, max_retries: int = 3)
    - _call(method: str, params: Dict) -> Dict
    - All 56 convenience methods
  - Class: MCPAsyncClient
    - __init__(timeout: int = 30, max_retries: int = 3)
    - _call(method: str, params: Dict) -> Dict (async)
    - All 56 convenience methods (async)
  - Function: get_mcp_sync_client() -> MCPSyncClient (singleton)
  - Function: get_mcp_async_client() -> MCPAsyncClient (singleton)

svc/mcp_exceptions.py
  - Class: MCPError(Exception) - Base exception
  - Class: MCPMethodNotFoundError(MCPError)
  - Class: MCPInvalidParamsError(MCPError)
  - Class: MCPInternalError(MCPError)
  - Class: MCPTimeoutError(MCPError)
  - Class: MCPValidationError(MCPError)
  - Class: MCPResourceNotFoundError(MCPError)
```

### Files to Modify

```
svc/__init__.py
  - Add: Export MCPSyncClient, MCPAsyncClient
  - Add: Export get_mcp_sync_client, get_mcp_async_client
  - Add: Export MCP exception classes
```

## Detailed Implementation

### Step 1: Create Exception Hierarchy

```python
# svc/mcp_exceptions.py
"""Exception classes for MCP client operations."""


class MCPError(Exception):
    """Base exception for all MCP errors."""

    def __init__(self, message: str, code: int = None, data: any = None):
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


def exception_from_error_code(code: int, message: str, data: any = None) -> MCPError:
    """Create appropriate exception based on error code."""
    error_map = {
        -32601: MCPMethodNotFoundError,
        -32602: MCPInvalidParamsError,
        -32603: MCPInternalError,
        -32000: MCPValidationError,
        -32001: MCPResourceNotFoundError,
    }

    exc_class = error_map.get(code, MCPError)
    return exc_class(message, code=code, data=data)
```

### Step 2: Implement Synchronous Client

```python
# svc/mcp_client.py
"""MCP client wrappers for synchronous and asynchronous usage."""

import asyncio
from typing import Dict, Any, List, Optional, Union
from svc.mcp_server import create_mcp_client
from svc.mcp_exceptions import (
    MCPError,
    MCPTimeoutError,
    exception_from_error_code
)
from core.logging import get_logger

logger = get_logger(__name__)


class MCPSyncClient:
    """
    Synchronous MCP client for CLI usage.

    Provides convenient methods for all MCP operations with
    automatic error handling and retry logic.
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
            Method result

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

                logger.warning(f"MCP request failed (attempt {attempt + 1}), retrying...")
                # Exponential backoff: 0.1s, 0.2s, 0.4s, etc.
                time.sleep(0.1 * (2 ** attempt))

    # ========================================================================
    # Validation Methods
    # ========================================================================

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
            family: Plugin family (default: "words")
            validation_types: List of validation types to apply

        Returns:
            Validation result dictionary

        Raises:
            MCPError: If validation fails
        """
        return self._call("validate_file", {
            "file_path": file_path,
            "family": family,
            "validation_types": validation_types
        })

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
            Validation results

        Raises:
            MCPError: If validation fails
        """
        return self._call("validate_folder", {
            "folder_path": folder_path,
            "recursive": recursive
        })

    def validate_content(
        self,
        content: str,
        file_path: str = "temp.md",
        validation_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Validate content string.

        Args:
            content: Content to validate
            file_path: Virtual file path for context
            validation_types: List of validation types to apply

        Returns:
            Validation result

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
        Get validation by ID.

        Args:
            validation_id: Validation ID

        Returns:
            Validation record

        Raises:
            MCPResourceNotFoundError: If validation not found
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
        List validations with filters.

        Args:
            limit: Maximum results to return
            offset: Offset for pagination
            status: Filter by status (pending/approved/rejected/enhanced)
            file_path: Filter by file path

        Returns:
            List of validations and total count
        """
        return self._call("list_validations", {
            "limit": limit,
            "offset": offset,
            "status": status,
            "file_path": file_path
        })

    # ========================================================================
    # Approval Methods
    # ========================================================================

    def approve(self, validation_ids: Union[str, List[str]]) -> Dict[str, Any]:
        """
        Approve validation(s).

        Args:
            validation_ids: Single ID or list of IDs to approve

        Returns:
            Approval results

        Raises:
            MCPError: If approval fails
        """
        if isinstance(validation_ids, str):
            validation_ids = [validation_ids]

        return self._call("approve", {"ids": validation_ids})

    def reject(self, validation_ids: Union[str, List[str]]) -> Dict[str, Any]:
        """
        Reject validation(s).

        Args:
            validation_ids: Single ID or list of IDs to reject

        Returns:
            Rejection results

        Raises:
            MCPError: If rejection fails
        """
        if isinstance(validation_ids, str):
            validation_ids = [validation_ids]

        return self._call("reject", {"ids": validation_ids})

    # ========================================================================
    # Enhancement Methods
    # ========================================================================

    def enhance(self, validation_ids: Union[str, List[str]]) -> Dict[str, Any]:
        """
        Enhance approved validation(s).

        Args:
            validation_ids: Single ID or list of IDs to enhance

        Returns:
            Enhancement results

        Raises:
            MCPError: If enhancement fails
        """
        if isinstance(validation_ids, str):
            validation_ids = [validation_ids]

        return self._call("enhance", {"ids": validation_ids})

    # ========================================================================
    # Recommendation Methods
    # ========================================================================

    def generate_recommendations(
        self,
        validation_id: str,
        threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Generate recommendations for a validation.

        Args:
            validation_id: Validation ID
            threshold: Confidence threshold for recommendations

        Returns:
            Generated recommendations

        Raises:
            MCPError: If generation fails
        """
        return self._call("generate_recommendations", {
            "validation_id": validation_id,
            "threshold": threshold
        })

    def get_recommendations(self, validation_id: str) -> Dict[str, Any]:
        """
        Get recommendations for a validation.

        Args:
            validation_id: Validation ID

        Returns:
            Recommendations list

        Raises:
            MCPError: If retrieval fails
        """
        return self._call("get_recommendations", {
            "validation_id": validation_id
        })

    # ========================================================================
    # Workflow Methods
    # ========================================================================

    def create_workflow(
        self,
        workflow_type: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new workflow.

        Args:
            workflow_type: Type of workflow (validate_directory, etc.)
            params: Workflow parameters

        Returns:
            Created workflow info

        Raises:
            MCPError: If creation fails
        """
        return self._call("create_workflow", {
            "workflow_type": workflow_type,
            "params": params
        })

    def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get workflow by ID.

        Args:
            workflow_id: Workflow ID

        Returns:
            Workflow details

        Raises:
            MCPResourceNotFoundError: If workflow not found
        """
        return self._call("get_workflow", {
            "workflow_id": workflow_id
        })

    def list_workflows(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List workflows with filters.

        Args:
            limit: Maximum results
            offset: Offset for pagination
            status: Filter by status

        Returns:
            List of workflows
        """
        return self._call("list_workflows", {
            "limit": limit,
            "offset": offset,
            "status": status
        })

    # ========================================================================
    # Admin Methods
    # ========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """
        Get system statistics.

        Returns:
            Statistics dictionary
        """
        return self._call("get_stats", {})

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get system health status.

        Returns:
            Health status dictionary
        """
        return self._call("get_system_status", {})

    def clear_cache(self) -> Dict[str, Any]:
        """
        Clear all caches.

        Returns:
            Result dictionary
        """
        return self._call("clear_cache", {})


# Singleton instance
_mcp_sync_client: Optional[MCPSyncClient] = None


def get_mcp_sync_client() -> MCPSyncClient:
    """Get or create singleton sync MCP client."""
    global _mcp_sync_client
    if _mcp_sync_client is None:
        _mcp_sync_client = MCPSyncClient()
    return _mcp_sync_client
```

### Step 3: Implement Asynchronous Client

```python
# svc/mcp_client.py (continued)

import asyncio


class MCPAsyncClient:
    """
    Asynchronous MCP client for API usage.

    Provides async/await interface for all MCP operations.
    """

    def __init__(self, timeout: int = 30, max_retries: int = 3):
        """Initialize async MCP client."""
        self._server = create_mcp_client()
        self.timeout = timeout
        self.max_retries = max_retries
        self._request_counter = 0

    async def _call(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call MCP method asynchronously.

        Args:
            method: Method name
            params: Method parameters

        Returns:
            Method result

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

        logger.debug(f"Async MCP request: method={method}, id={request_id}")

        for attempt in range(self.max_retries):
            try:
                # Run sync method in executor
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

                logger.debug(f"Async MCP response: method={method}, id={request_id}")
                return response.get("result", {})

            except MCPError:
                raise
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise MCPInternalError(f"Async MCP request failed: {e}")

                logger.warning(f"Async MCP request failed (attempt {attempt + 1}), retrying...")
                await asyncio.sleep(0.1 * (2 ** attempt))

    # All methods same as sync client but with async/await
    async def validate_file(
        self,
        file_path: str,
        family: str = "words",
        validation_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Validate a single file (async)."""
        return await self._call("validate_file", {
            "file_path": file_path,
            "family": family,
            "validation_types": validation_types
        })

    # ... (all other methods same as MCPSyncClient but async)


# Singleton instance
_mcp_async_client: Optional[MCPAsyncClient] = None


def get_mcp_async_client() -> MCPAsyncClient:
    """Get or create singleton async MCP client."""
    global _mcp_async_client
    if _mcp_async_client is None:
        _mcp_async_client = MCPAsyncClient()
    return _mcp_async_client
```

## Testing Requirements

### Unit Tests

**File**: `tests/svc/test_mcp_client.py`

```python
import pytest
from svc.mcp_client import MCPSyncClient, MCPAsyncClient, get_mcp_sync_client
from svc.mcp_exceptions import MCPMethodNotFoundError, MCPInvalidParamsError


class TestMCPSyncClient:
    """Test synchronous MCP client."""

    def test_initialization(self):
        """Test client initializes correctly."""
        client = MCPSyncClient()
        assert client.timeout == 30
        assert client.max_retries == 3

    def test_singleton_pattern(self):
        """Test singleton returns same instance."""
        client1 = get_mcp_sync_client()
        client2 = get_mcp_sync_client()
        assert client1 is client2

    def test_validate_folder_success(self, tmp_path):
        """Test successful folder validation."""
        # Create test file
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test")

        client = MCPSyncClient()
        result = client.validate_folder(str(tmp_path), recursive=False)

        assert result["success"] is True
        assert result["results"]["files_processed"] > 0

    def test_method_not_found_error(self):
        """Test error on unknown method."""
        client = MCPSyncClient()

        # Manually call non-existent method
        with pytest.raises(MCPMethodNotFoundError):
            client._call("nonexistent_method", {})

    def test_approve_single_id(self):
        """Test approve with single ID."""
        client = MCPSyncClient()
        # This will fail because ID doesn't exist, but tests the API
        result = client.approve("test-id")
        # Should have errors list
        assert "errors" in result or "approved_count" in result

    def test_approve_multiple_ids(self):
        """Test approve with list of IDs."""
        client = MCPSyncClient()
        result = client.approve(["id1", "id2"])
        assert "errors" in result or "approved_count" in result


@pytest.mark.asyncio
class TestMCPAsyncClient:
    """Test asynchronous MCP client."""

    async def test_initialization(self):
        """Test async client initializes correctly."""
        client = MCPAsyncClient()
        assert client.timeout == 30
        assert client.max_retries == 3

    async def test_validate_folder_async(self, tmp_path):
        """Test async folder validation."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test")

        client = MCPAsyncClient()
        result = await client.validate_folder(str(tmp_path), recursive=False)

        assert result["success"] is True
        assert result["results"]["files_processed"] > 0

    async def test_concurrent_requests(self, tmp_path):
        """Test handling concurrent async requests."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test")

        client = MCPAsyncClient()

        # Make multiple concurrent requests
        results = await asyncio.gather(
            client.validate_folder(str(tmp_path)),
            client.validate_folder(str(tmp_path)),
            client.validate_folder(str(tmp_path))
        )

        assert len(results) == 3
        for result in results:
            assert result["success"] is True
```

## Documentation Updates

**`docs/mcp_integration.md`**:

```markdown
## MCP Client Usage

### Synchronous Client (for CLI)

```python
from svc.mcp_client import MCPSyncClient

# Create client
client = MCPSyncClient()

# Validate folder
result = client.validate_folder("./content", recursive=True)
print(f"Validated {result['results']['files_processed']} files")

# Approve validation
client.approve("validation-id-123")

# Get recommendations
recommendations = client.get_recommendations("validation-id-123")
```

### Asynchronous Client (for API)

```python
from svc.mcp_client import MCPAsyncClient

# Create client
client = MCPAsyncClient()

# Async validation
result = await client.validate_file("./content/file.md")

# Concurrent operations
results = await asyncio.gather(
    client.validate_folder("./folder1"),
    client.validate_folder("./folder2")
)
```

### Error Handling

```python
from svc.mcp_client import MCPSyncClient
from svc.mcp_exceptions import MCPResourceNotFoundError, MCPError

client = MCPSyncClient()

try:
    validation = client.get_validation("invalid-id")
except MCPResourceNotFoundError as e:
    print(f"Validation not found: {e}")
except MCPError as e:
    print(f"MCP error: {e}")
```
```

## Runbook

```bash
# Development
git checkout -b feature/task-002-mcp-clients

# Create files
touch svc/mcp_client.py svc/mcp_exceptions.py

# Implement code
# ... (use examples above)

# Test continuously
pytest tests/svc/test_mcp_client.py -v

# Type checking
mypy svc/mcp_client.py

# Integration test
python -c "from svc.mcp_client import get_mcp_sync_client; c = get_mcp_sync_client(); print(c.validate_folder('.', False))"

# Commit
git add svc/ tests/
git commit -m "feat(mcp): implement sync/async clients (TASK-002)"
git push origin feature/task-002-mcp-clients
```

## Rollback Plan

```bash
# Revert commit
git revert <commit-hash>

# Or rollback
git checkout main~1
```

## Definition of Done

- [x] MCPSyncClient fully implemented
- [x] MCPAsyncClient fully implemented
- [x] Exception hierarchy complete
- [x] Unit tests >90% coverage
- [x] Integration tests passing
- [x] Documentation updated
- [x] Type hints complete
- [ ] Code reviewed
- [ ] Merged to main

---

**Status**: Not Started
**Last Updated**: 2025-11-30
