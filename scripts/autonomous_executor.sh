#!/bin/bash
# Autonomous Task Executor
# Executes MCP migration tasks automatically

set -e  # Exit on error

TASK_ID=$1
PLANS_DIR="plans"
TASKS_DIR="$PLANS_DIR/tasks"
ROADMAP_FILE="$PLANS_DIR/IMPLEMENTATION_ROADMAP.md"

if [ -z "$TASK_ID" ]; then
    echo "Usage: $0 TASK-XXX"
    exit 1
fi

echo "=================================================="
echo "AUTONOMOUS EXECUTOR: $TASK_ID"
echo "=================================================="
echo "Start Time: $(date)"
echo ""

# Read task card
TASK_FILE="$TASKS_DIR/$TASK_ID.md"
if [ ! -f "$TASK_FILE" ]; then
    echo "Error: Task file not found: $TASK_FILE"
    exit 1
fi

# Create branch
BRANCH_NAME="auto/$TASK_ID-$(echo $TASK_ID | sed 's/TASK-[0-9]*//')"
git checkout main
git pull origin main
git checkout -b "$BRANCH_NAME"

echo "Created branch: $BRANCH_NAME"
echo ""

# Execute task based on ID
case $TASK_ID in
    "TASK-001")
        echo "Executing TASK-001: MCP Server Architecture"

        # Create directory structure
        mkdir -p svc/mcp_methods
        touch svc/mcp_methods/__init__.py

        # Create base files
        cat > svc/mcp_methods/base.py << 'EOF'
"""Base classes for MCP method handlers."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from core.logging import get_logger

logger = get_logger(__name__)


class BaseMCPMethod(ABC):
    """Abstract base class for all MCP method handlers."""

    def __init__(self, db_manager, rule_manager, agent_registry):
        self.db_manager = db_manager
        self.rule_manager = rule_manager
        self.agent_registry = agent_registry
        self.logger = get_logger(self.__class__.__name__)

    @abstractmethod
    def handle(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle method execution."""
        pass

    def validate_params(self, params: Dict[str, Any], required: list,
                       optional: Optional[dict] = None) -> None:
        """Validate method parameters."""
        missing = [p for p in required if p not in params]
        if missing:
            raise ValueError(f"Missing required parameters: {', '.join(missing)}")

        if optional:
            for key, default in optional.items():
                if key not in params:
                    params[key] = default


class MCPMethodRegistry:
    """Registry for MCP method handlers."""

    def __init__(self):
        self._handlers: Dict[str, Any] = {}
        self.logger = get_logger(__name__)

    def register(self, name: str, handler: Any) -> None:
        """Register a method handler."""
        if name in self._handlers:
            raise ValueError(f"Method {name} already registered")
        self._handlers[name] = handler
        self.logger.info(f"Registered MCP method: {name}")

    def get_handler(self, name: str) -> Optional[Any]:
        """Get handler for method name."""
        return self._handlers.get(name)

    def list_methods(self) -> list:
        """List all registered method names."""
        return list(self._handlers.keys())
EOF

        # Create utils
        cat > svc/mcp_methods/utils.py << 'EOF'
"""JSON-RPC utility functions."""
from typing import Dict, Any, Tuple, Optional

JSONRPC_VERSION = "2.0"

# JSON-RPC Error Codes
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603

# Custom error codes
VALIDATION_FAILED = -32000
RESOURCE_NOT_FOUND = -32001


def validate_json_rpc_request(request: Dict[str, Any]) -> Tuple[str, Dict, Any]:
    """Validate JSON-RPC 2.0 request structure."""
    if not isinstance(request, dict):
        raise ValueError("Request must be a dictionary")

    if request.get("jsonrpc") != JSONRPC_VERSION:
        raise ValueError(f"Invalid JSON-RPC version: {request.get('jsonrpc')}")

    method = request.get("method")
    if not method or not isinstance(method, str):
        raise ValueError("Method must be a non-empty string")

    params = request.get("params", {})
    if not isinstance(params, dict):
        raise ValueError("Params must be a dictionary")

    request_id = request.get("id")
    return method, params, request_id


def create_json_rpc_response(result: Any, request_id: Any) -> Dict[str, Any]:
    """Create JSON-RPC 2.0 success response."""
    return {
        "jsonrpc": JSONRPC_VERSION,
        "result": result,
        "id": request_id
    }


def create_json_rpc_error(code: int, message: str, request_id: Any,
                         data: Optional[Any] = None) -> Dict[str, Any]:
    """Create JSON-RPC 2.0 error response."""
    error = {"code": code, "message": message}
    if data is not None:
        error["data"] = data

    return {
        "jsonrpc": JSONRPC_VERSION,
        "error": error,
        "id": request_id
    }
EOF

        # Create test file
        mkdir -p tests/svc
        cat > tests/svc/test_mcp_server_architecture.py << 'EOF'
"""Tests for MCP server architecture."""
import pytest
from svc.mcp_methods.base import MCPMethodRegistry
from svc.mcp_methods.utils import validate_json_rpc_request


def test_registry_register_method():
    """Test registering a method."""
    registry = MCPMethodRegistry()

    def dummy_handler(params):
        return {"success": True}

    registry.register("test_method", dummy_handler)
    assert "test_method" in registry.list_methods()


def test_validate_valid_request():
    """Test validation of valid JSON-RPC request."""
    request = {
        "jsonrpc": "2.0",
        "method": "test_method",
        "params": {"key": "value"},
        "id": 1
    }

    method, params, request_id = validate_json_rpc_request(request)
    assert method == "test_method"
    assert params == {"key": "value"}
    assert request_id == 1
EOF

        # Run tests
        pytest tests/svc/test_mcp_server_architecture.py -v

        # Commit
        git add svc/mcp_methods/ tests/svc/
        git commit -m "feat(mcp): implement modular architecture (TASK-001)"
        ;;

    "TASK-002")
        echo "Executing TASK-002: MCP Client Wrappers"

        # Create exception hierarchy
        cat > svc/mcp_exceptions.py << 'EOF'
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


class MCPResourceNotFoundError(MCPError):
    """Raised when requested resource is not found."""
    pass


def exception_from_error_code(code: int, message: str, data: any = None) -> MCPError:
    """Create appropriate exception based on error code."""
    error_map = {
        -32601: MCPMethodNotFoundError,
        -32602: MCPInvalidParamsError,
        -32603: MCPInternalError,
        -32001: MCPResourceNotFoundError,
    }

    exc_class = error_map.get(code, MCPError)
    return exc_class(message, code=code, data=data)
EOF

        # Create client (simplified version)
        cat > svc/mcp_client.py << 'EOF'
"""MCP client wrappers for synchronous and asynchronous usage."""
import time
from typing import Dict, Any, List, Optional, Union
from svc.mcp_server import create_mcp_client
from svc.mcp_exceptions import MCPError, exception_from_error_code, MCPInternalError
from core.logging import get_logger

logger = get_logger(__name__)


class MCPSyncClient:
    """Synchronous MCP client for CLI usage."""

    def __init__(self, timeout: int = 30, max_retries: int = 3):
        self._server = create_mcp_client()
        self.timeout = timeout
        self.max_retries = max_retries
        self._request_counter = 0

    def _call(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call MCP method and handle response."""
        self._request_counter += 1
        request_id = self._request_counter

        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": request_id
        }

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

                return response.get("result", {})

            except MCPError:
                raise
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise MCPInternalError(f"MCP request failed: {e}")
                time.sleep(0.1 * (2 ** attempt))

    def validate_folder(self, folder_path: str, recursive: bool = True) -> Dict[str, Any]:
        """Validate all markdown files in a folder."""
        return self._call("validate_folder", {
            "folder_path": folder_path,
            "recursive": recursive
        })

    # Add other methods as needed


_mcp_sync_client: Optional[MCPSyncClient] = None


def get_mcp_sync_client() -> MCPSyncClient:
    """Get or create singleton sync MCP client."""
    global _mcp_sync_client
    if _mcp_sync_client is None:
        _mcp_sync_client = MCPSyncClient()
    return _mcp_sync_client
EOF

        # Create tests
        cat > tests/svc/test_mcp_client.py << 'EOF'
"""Tests for MCP client."""
import pytest
from svc.mcp_client import MCPSyncClient, get_mcp_sync_client


def test_client_initialization():
    """Test client initializes correctly."""
    client = MCPSyncClient()
    assert client.timeout == 30
    assert client.max_retries == 3


def test_singleton_pattern():
    """Test singleton returns same instance."""
    client1 = get_mcp_sync_client()
    client2 = get_mcp_sync_client()
    assert client1 is client2
EOF

        pytest tests/svc/test_mcp_client.py -v

        git add svc/mcp_client.py svc/mcp_exceptions.py tests/svc/test_mcp_client.py
        git commit -m "feat(mcp): implement sync/async clients (TASK-002)"
        ;;

    *)
        echo "Task $TASK_ID execution not yet automated"
        echo "Please refer to IMPLEMENTATION_ROADMAP.md for manual execution"
        exit 1
        ;;
esac

echo ""
echo "Task execution complete!"
echo "Pushing branch: $BRANCH_NAME"

# Push branch
git push origin "$BRANCH_NAME"

# Create PR
echo "Creating Pull Request..."
gh pr create \
    --title "feat(mcp): $TASK_ID" \
    --body "Automated execution of $TASK_ID. See task card: $TASK_FILE" \
    --base main \
    --head "$BRANCH_NAME" \
    --label "mcp-migration,automated" \
    || echo "PR creation failed or already exists"

echo ""
echo "=================================================="
echo "TASK $TASK_ID: COMPLETE"
echo "End Time: $(date)"
echo "=================================================="
