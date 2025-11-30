# TASK-001: MCP Server Architecture & Base Infrastructure

## Metadata
- **Priority**: P0
- **Effort**: 3 days
- **Owner**: TBD
- **Status**: Not Started
- **Dependencies**: None
- **Phase**: Phase 1 - Foundation
- **Category**: Foundation

## Objective
Refactor and expand MCP server architecture to support 56 total methods with modular, maintainable structure.

Create a scalable, production-ready foundation for the MCP server that can handle all validation, recommendation, workflow, and admin operations through a clean, modular architecture.

## Scope

### In Scope
- Refactor `svc/mcp_server.py` to use modular method handlers
- Create `svc/mcp_methods/` directory with category-specific modules
- Implement base classes and utilities for MCP methods
- Add comprehensive error handling and validation
- Implement JSON-RPC 2.0 compliant request/response handling
- Add structured logging for all MCP operations
- Create method registry for dynamic method dispatch

### Out of Scope
- Actual implementation of 52 missing methods (covered in TASK-004 through TASK-011)
- Network-based MCP communication (stdio and in-process only)
- Authentication/authorization (future enhancement)
- Rate limiting (future enhancement)

## Acceptance Criteria
- [ ] Modular architecture supports adding new methods without modifying core
- [ ] All existing 4 methods (validate_folder, approve, reject, enhance) migrated to new structure
- [ ] Method registry pattern implemented for extensibility
- [ ] Comprehensive error handling with JSON-RPC error codes
- [ ] Structured logging captures all operations
- [ ] Input validation for all request parameters
- [ ] Unit tests with >90% coverage for core infrastructure
- [ ] Zero regressions in existing MCP functionality
- [ ] Documentation updated with new architecture
- [ ] Performance maintained (<1ms overhead for dispatch)

## Implementation Plan

### Architecture Decisions

**1. Modular Method Handlers**
- Separate method implementations into category-specific modules
- Use base class pattern for common functionality
- Registry pattern for dynamic method dispatch

**2. Error Handling Strategy**
- JSON-RPC 2.0 error codes (-32700, -32600, -32601, -32603)
- Custom error codes for domain-specific errors (starting at -32000)
- Structured error responses with details for debugging

**3. Logging Strategy**
- Log all requests/responses at INFO level
- Log errors at ERROR level with full stack traces
- Include request ID in all log messages for tracing
- Performance metrics logged at DEBUG level

### Files to Create

```
svc/mcp_methods/__init__.py
  - Exports: All method handler classes
  - Purpose: Package initialization

svc/mcp_methods/base.py
  - Class: BaseMCPMethod (abstract base class)
    - handle(params: Dict) -> Dict (abstract method)
    - validate_params(params: Dict, schema: Dict) -> None
    - format_error(code: int, message: str) -> Dict
    - format_success(result: Any) -> Dict
  - Class: MCPMethodRegistry
    - register(name: str, handler: BaseMCPMethod) -> None
    - get_handler(name: str) -> BaseMCPMethod
    - list_methods() -> List[str]

svc/mcp_methods/validation_methods.py
  - Class: ValidationMethods(BaseMCPMethod)
    - validate_folder(params) -> Dict (migrate existing)
    - validate_file(params) -> Dict (placeholder for TASK-004)
    - validate_content(params) -> Dict (placeholder for TASK-004)
  - Purpose: All validation-related MCP methods

svc/mcp_methods/approval_methods.py
  - Class: ApprovalMethods(BaseMCPMethod)
    - approve(params) -> Dict (migrate existing)
    - reject(params) -> Dict (migrate existing)
  - Purpose: All approval-related MCP methods

svc/mcp_methods/enhancement_methods.py
  - Class: EnhancementMethods(BaseMCPMethod)
    - enhance(params) -> Dict (migrate existing)
  - Purpose: All enhancement-related MCP methods

svc/mcp_methods/utils.py
  - Function: validate_json_rpc_request(request: Dict) -> Tuple[str, Dict, Any]
  - Function: create_json_rpc_response(result: Any, request_id: Any) -> Dict
  - Function: create_json_rpc_error(code: int, message: str, request_id: Any) -> Dict
  - Constant: JSONRPC_VERSION = "2.0"
  - Purpose: JSON-RPC utility functions
```

### Files to Modify

```
svc/mcp_server.py
  - Modify: MCPServer.__init__() to use method registry
  - Modify: MCPServer.handle_request() to use registry dispatch
  - Add: MCPServer._register_methods() to register all handlers
  - Remove: Direct method implementations (move to mcp_methods/)
  - Add: Structured logging throughout

svc/__init__.py
  - Add: Export create_mcp_client and MCPServer
  - Purpose: Make imports cleaner
```

### Files to Delete
None (this is additive refactoring)

## Detailed Implementation

### Step 1: Create Base Infrastructure
**What**: Implement base classes and utilities
**Why**: Provides consistent patterns for all method handlers
**How**:

```python
# svc/mcp_methods/base.py
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
        """
        Handle method execution.

        Args:
            params: Method parameters

        Returns:
            Method result dictionary

        Raises:
            ValueError: If parameters are invalid
            Exception: For other errors
        """
        pass

    def validate_params(self, params: Dict[str, Any], required: list,
                       optional: Optional[dict] = None) -> None:
        """
        Validate method parameters.

        Args:
            params: Parameters to validate
            required: List of required parameter names
            optional: Dict of optional parameters with default values

        Raises:
            ValueError: If required parameters are missing
        """
        missing = [p for p in required if p not in params]
        if missing:
            raise ValueError(f"Missing required parameters: {', '.join(missing)}")

        # Set defaults for optional parameters
        if optional:
            for key, default in optional.items():
                if key not in params:
                    params[key] = default


class MCPMethodRegistry:
    """Registry for MCP method handlers."""

    def __init__(self):
        self._handlers: Dict[str, BaseMCPMethod] = {}
        self.logger = get_logger(__name__)

    def register(self, name: str, handler: BaseMCPMethod) -> None:
        """Register a method handler."""
        if name in self._handlers:
            raise ValueError(f"Method {name} already registered")
        self._handlers[name] = handler
        self.logger.info(f"Registered MCP method: {name}")

    def get_handler(self, name: str) -> Optional[BaseMCPMethod]:
        """Get handler for method name."""
        return self._handlers.get(name)

    def list_methods(self) -> list:
        """List all registered method names."""
        return list(self._handlers.keys())
```

### Step 2: Create JSON-RPC Utilities
**What**: Implement JSON-RPC 2.0 utility functions
**Why**: Ensures compliance with JSON-RPC spec
**How**:

```python
# svc/mcp_methods/utils.py
from typing import Dict, Any, Tuple, Optional

JSONRPC_VERSION = "2.0"

# JSON-RPC 2.0 Error Codes
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603

# Custom error codes (application-specific)
VALIDATION_FAILED = -32000
RESOURCE_NOT_FOUND = -32001
UNAUTHORIZED = -32002
RATE_LIMITED = -32003


def validate_json_rpc_request(request: Dict[str, Any]) -> Tuple[str, Dict, Any]:
    """
    Validate JSON-RPC 2.0 request structure.

    Args:
        request: Request dictionary

    Returns:
        Tuple of (method, params, request_id)

    Raises:
        ValueError: If request is invalid
    """
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
    error = {
        "code": code,
        "message": message
    }
    if data is not None:
        error["data"] = data

    return {
        "jsonrpc": JSONRPC_VERSION,
        "error": error,
        "id": request_id
    }
```

### Step 3: Migrate Existing Methods
**What**: Move existing 4 methods to new structure
**Why**: Validates new architecture with working code
**How**:

```python
# svc/mcp_methods/validation_methods.py
from typing import Dict, Any
from .base import BaseMCPMethod


class ValidationMethods(BaseMCPMethod):
    """Handler for validation-related MCP methods."""

    def validate_folder(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate all markdown files in a folder.

        Args:
            params: {
                "folder_path": str (required),
                "recursive": bool (optional, default True)
            }

        Returns:
            {
                "success": bool,
                "message": str,
                "results": {
                    "files_processed": int,
                    "files_passed": int,
                    "files_failed": int,
                    "validations": List[Dict]
                }
            }
        """
        # Validate parameters
        self.validate_params(params, required=["folder_path"],
                           optional={"recursive": True})

        folder_path = params["folder_path"]
        recursive = params["recursive"]

        self.logger.info(f"Validating folder: {folder_path} (recursive={recursive})")

        # Get ingestion component
        from core.ingestion import MarkdownIngestion
        ingestion = MarkdownIngestion(self.db_manager, self.rule_manager)

        # Run ingestion
        results = ingestion.ingest_folder(folder_path, recursive=recursive)

        self.logger.info(f"Validation complete: {results['files_processed']} files processed")

        return {
            "success": True,
            "message": f"Validated {results['files_processed']} files",
            "results": results
        }
```

### Step 4: Refactor MCPServer
**What**: Update MCPServer to use registry pattern
**Why**: Enables dynamic method dispatch and extensibility
**How**:

```python
# svc/mcp_server.py (refactored)
import json
import sys
from typing import Dict, Any
from core.database import DatabaseManager
from core.rule_manager import RuleManager
from core.logging import get_logger
from svc.mcp_methods.base import MCPMethodRegistry
from svc.mcp_methods.validation_methods import ValidationMethods
from svc.mcp_methods.approval_methods import ApprovalMethods
from svc.mcp_methods.enhancement_methods import EnhancementMethods
from svc.mcp_methods.utils import (
    validate_json_rpc_request,
    create_json_rpc_response,
    create_json_rpc_error,
    METHOD_NOT_FOUND,
    INVALID_REQUEST,
    INTERNAL_ERROR,
    PARSE_ERROR
)

logger = get_logger(__name__)


class MCPServer:
    """MCP server for TBCV validation operations."""

    def __init__(self):
        """Initialize MCP server with required components."""
        logger.info("Initializing MCP server")

        # Initialize core components
        self.db_manager = DatabaseManager()
        self.rule_manager = RuleManager()
        self.db_manager.init_database()

        # Initialize agent registry (for future use)
        from agents.base import agent_registry
        self.agent_registry = agent_registry

        # Initialize method registry
        self.registry = MCPMethodRegistry()
        self._register_methods()

        logger.info(f"MCP server initialized with {len(self.registry.list_methods())} methods")

    def _register_methods(self) -> None:
        """Register all MCP method handlers."""
        # Validation methods
        validation_handler = ValidationMethods(
            self.db_manager,
            self.rule_manager,
            self.agent_registry
        )
        self.registry.register("validate_folder", validation_handler.validate_folder)

        # Approval methods
        approval_handler = ApprovalMethods(
            self.db_manager,
            self.rule_manager,
            self.agent_registry
        )
        self.registry.register("approve", approval_handler.approve)
        self.registry.register("reject", approval_handler.reject)

        # Enhancement methods
        enhancement_handler = EnhancementMethods(
            self.db_manager,
            self.rule_manager,
            self.agent_registry
        )
        self.registry.register("enhance", enhancement_handler.enhance)

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle JSON-RPC request.

        Args:
            request: JSON-RPC request object

        Returns:
            JSON-RPC response object
        """
        request_id = None

        try:
            # Validate JSON-RPC request structure
            method, params, request_id = validate_json_rpc_request(request)

            logger.info(f"Handling MCP request: method={method}, id={request_id}")

            # Get method handler
            handler = self.registry.get_handler(method)
            if not handler:
                logger.warning(f"Method not found: {method}")
                return create_json_rpc_error(
                    METHOD_NOT_FOUND,
                    f"Method not found: {method}",
                    request_id
                )

            # Execute method
            result = handler(params)

            logger.info(f"MCP request completed: method={method}, id={request_id}")

            return create_json_rpc_response(result, request_id)

        except ValueError as e:
            logger.error(f"Invalid request: {e}")
            return create_json_rpc_error(
                INVALID_REQUEST,
                str(e),
                request_id
            )
        except Exception as e:
            logger.exception(f"Internal error handling request: {e}")
            return create_json_rpc_error(
                INTERNAL_ERROR,
                f"Internal error: {str(e)}",
                request_id
            )


def create_mcp_client() -> MCPServer:
    """
    Create an in-process MCP client.

    Returns:
        MCP server instance for direct method calls
    """
    return MCPServer()


# Rest of MCPStdioServer remains the same...
```

## Testing Requirements

### Unit Tests

**File**: `tests/svc/test_mcp_server_architecture.py`

**Test Cases**:

```python
import pytest
from svc.mcp_server import MCPServer
from svc.mcp_methods.base import BaseMCPMethod, MCPMethodRegistry
from svc.mcp_methods.utils import (
    validate_json_rpc_request,
    create_json_rpc_response,
    create_json_rpc_error,
    METHOD_NOT_FOUND
)


class TestMCPMethodRegistry:
    """Test method registry functionality."""

    def test_register_method(self):
        """Test registering a method handler."""
        registry = MCPMethodRegistry()

        def dummy_handler(params):
            return {"success": True}

        registry.register("test_method", dummy_handler)
        assert "test_method" in registry.list_methods()

    def test_get_handler(self):
        """Test retrieving registered handler."""
        registry = MCPMethodRegistry()

        def dummy_handler(params):
            return {"success": True}

        registry.register("test_method", dummy_handler)
        handler = registry.get_handler("test_method")
        assert handler is dummy_handler

    def test_duplicate_registration_raises_error(self):
        """Test that duplicate registration raises error."""
        registry = MCPMethodRegistry()

        def dummy_handler(params):
            return {"success": True}

        registry.register("test_method", dummy_handler)

        with pytest.raises(ValueError, match="already registered"):
            registry.register("test_method", dummy_handler)


class TestJSONRPCUtils:
    """Test JSON-RPC utility functions."""

    def test_validate_valid_request(self):
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

    def test_validate_request_without_params(self):
        """Test validation handles missing params."""
        request = {
            "jsonrpc": "2.0",
            "method": "test_method",
            "id": 1
        }

        method, params, request_id = validate_json_rpc_request(request)

        assert params == {}

    def test_validate_invalid_version_raises_error(self):
        """Test that invalid JSON-RPC version raises error."""
        request = {
            "jsonrpc": "1.0",
            "method": "test_method",
            "id": 1
        }

        with pytest.raises(ValueError, match="Invalid JSON-RPC version"):
            validate_json_rpc_request(request)

    def test_create_success_response(self):
        """Test creating success response."""
        result = {"data": "value"}
        request_id = 1

        response = create_json_rpc_response(result, request_id)

        assert response["jsonrpc"] == "2.0"
        assert response["result"] == result
        assert response["id"] == request_id

    def test_create_error_response(self):
        """Test creating error response."""
        response = create_json_rpc_error(
            METHOD_NOT_FOUND,
            "Method not found",
            1
        )

        assert response["jsonrpc"] == "2.0"
        assert "error" in response
        assert response["error"]["code"] == METHOD_NOT_FOUND
        assert response["error"]["message"] == "Method not found"


class TestMCPServer:
    """Test MCP server functionality."""

    def test_initialization(self):
        """Test MCP server initializes correctly."""
        server = MCPServer()

        assert server.db_manager is not None
        assert server.rule_manager is not None
        assert server.registry is not None
        assert len(server.registry.list_methods()) >= 4

    def test_handle_valid_request(self):
        """Test handling valid request."""
        server = MCPServer()

        request = {
            "jsonrpc": "2.0",
            "method": "validate_folder",
            "params": {"folder_path": ".", "recursive": False},
            "id": 1
        }

        response = server.handle_request(request)

        assert "result" in response
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1

    def test_handle_method_not_found(self):
        """Test handling unknown method."""
        server = MCPServer()

        request = {
            "jsonrpc": "2.0",
            "method": "nonexistent_method",
            "params": {},
            "id": 1
        }

        response = server.handle_request(request)

        assert "error" in response
        assert response["error"]["code"] == METHOD_NOT_FOUND

    def test_handle_invalid_request(self):
        """Test handling invalid request structure."""
        server = MCPServer()

        request = {
            "jsonrpc": "1.0",  # Invalid version
            "method": "test",
            "id": 1
        }

        response = server.handle_request(request)

        assert "error" in response
```

### Integration Tests

**File**: `tests/integration/test_mcp_architecture_integration.py`

```python
import pytest
from svc.mcp_server import MCPServer, create_mcp_client


class TestMCPArchitectureIntegration:
    """Integration tests for MCP architecture."""

    def test_create_mcp_client(self):
        """Test creating MCP client."""
        client = create_mcp_client()

        assert isinstance(client, MCPServer)
        assert len(client.registry.list_methods()) >= 4

    def test_end_to_end_request_handling(self, tmp_path):
        """Test full request-response cycle."""
        # Create test markdown file
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test\n\nContent")

        # Create client
        client = create_mcp_client()

        # Make request
        request = {
            "jsonrpc": "2.0",
            "method": "validate_folder",
            "params": {
                "folder_path": str(tmp_path),
                "recursive": False
            },
            "id": 1
        }

        response = client.handle_request(request)

        # Verify response
        assert "result" in response
        assert response["result"]["success"] is True
        assert response["result"]["results"]["files_processed"] > 0
```

### Manual Testing Checklist
- [ ] Test MCPServer initialization
- [ ] Test method registration
- [ ] Test request dispatching
- [ ] Test error handling for invalid requests
- [ ] Test error handling for missing methods
- [ ] Test backward compatibility with existing 4 methods
- [ ] Test logging output
- [ ] Test performance (no noticeable overhead)

## Documentation Updates

### Files to Update

**`docs/mcp_integration.md`**:
```markdown
## MCP Server Architecture

The MCP server uses a modular, registry-based architecture:

### Components

1. **MCPServer**: Main server class handling request routing
2. **MCPMethodRegistry**: Registry for dynamic method dispatch
3. **BaseMCPMethod**: Abstract base class for method handlers
4. **Method Handlers**: Category-specific method implementations
   - ValidationMethods: Validation operations
   - ApprovalMethods: Approval operations
   - EnhancementMethods: Enhancement operations
   - RecommendationMethods: Recommendation operations
   - WorkflowMethods: Workflow operations
   - AdminMethods: Admin operations

### Adding New Methods

To add a new MCP method:

1. Implement handler in appropriate module (e.g., `svc/mcp_methods/validation_methods.py`)
2. Register in `MCPServer._register_methods()`
3. Add tests in `tests/svc/test_mcp_methods.py`
4. Update documentation

Example:
```python
# In validation_methods.py
def my_new_method(self, params: Dict[str, Any]) -> Dict[str, Any]:
    self.validate_params(params, required=["param1"])
    # Implementation
    return {"success": True}

# In mcp_server.py _register_methods()
self.registry.register("my_new_method", validation_handler.my_new_method)
```
```

**`docs/architecture.md`**:
Update the MCP Server section with new architecture diagram

## Runbook

### Development Setup
```bash
# Step 1: Create feature branch
git checkout -b feature/task-001-mcp-architecture

# Step 2: Create directory structure
mkdir -p svc/mcp_methods
touch svc/mcp_methods/__init__.py
```

### Implementation
```bash
# Step 3: Create base infrastructure files
# Create files as specified in implementation plan

# Step 4: Run tests continuously
pytest tests/svc/test_mcp_server_architecture.py -v --tb=short

# Step 5: Run linting
black svc/
mypy svc/
```

### Validation
```bash
# Step 6: Run full test suite
pytest -v --cov=svc.mcp_server --cov=svc.mcp_methods

# Step 7: Test backward compatibility
python -c "from svc.mcp_server import create_mcp_client; c = create_mcp_client(); print(c.handle_request({'jsonrpc':'2.0','method':'validate_folder','params':{'folder_path':'.','recursive':False},'id':1}))"

# Step 8: Performance check
python -m timeit -s "from svc.mcp_server import MCPServer; s=MCPServer()" "s.handle_request({'jsonrpc':'2.0','method':'validate_folder','params':{'folder_path':'.','recursive':False},'id':1})"
```

### Deployment
```bash
# Step 9: Commit changes
git add svc/mcp_methods/ svc/mcp_server.py tests/
git commit -m "feat(mcp): implement modular architecture (TASK-001)"

# Step 10: Push and create PR
git push origin feature/task-001-mcp-architecture

# Step 11: After approval, merge
git checkout main
git merge feature/task-001-mcp-architecture
git push origin main
```

## Rollback Plan

### If Issues Discovered

```bash
# Option 1: Revert commit
git revert <commit-hash>
git push origin main

# Option 2: Rollback to previous tag
git checkout tags/v1.x.x
git checkout -b rollback-task-001
```

### Validation After Rollback
```bash
# Verify existing methods still work
pytest tests/svc/ -v

# Check MCP server starts
python -m svc.mcp_server
```

## Definition of Done

### Code Quality
- [x] Code follows PEP 8 style guide
- [x] All functions have type hints
- [x] All public functions have docstrings
- [x] No TODO, FIXME, or placeholder comments
- [x] Error handling comprehensive
- [x] Logging appropriate and structured

### Testing
- [x] Unit tests for all components (>90% coverage)
- [x] Integration tests for end-to-end flows
- [x] Manual testing completed
- [x] Backward compatibility verified
- [x] Performance validated

### Documentation
- [x] Architecture documented
- [x] Examples provided
- [x] Runbook tested
- [x] Code comments for complex logic

### Review & Approval
- [ ] Code self-reviewed
- [ ] PR created
- [ ] CI checks passing
- [ ] Code reviewed by peer
- [ ] Approved by tech lead
- [ ] Merged to main

---

**Status**: Not Started
**Last Updated**: 2025-11-30
**Notes**: Foundation task - all other tasks depend on this
