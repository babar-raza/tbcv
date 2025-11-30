"""
Tests for MCP server architecture and registry pattern.

Tests the new modular architecture with:
- Method registry pattern
- Modular method handlers
- JSON-RPC compliance
"""

import pytest
from pathlib import Path
from datetime import datetime, timezone
from svc.mcp_server import MCPServer
from svc.mcp_methods import (
    MCPMethodRegistry,
    ValidationMethods,
    ApprovalMethods,
    EnhancementMethods,
    validate_json_rpc_request,
    create_json_rpc_response,
    create_json_rpc_error,
    JSONRPC_VERSION,
    METHOD_NOT_FOUND,
    INTERNAL_ERROR,
)
from core.database import DatabaseManager, ValidationStatus


class TestJSONRPCUtilities:
    """Test JSON-RPC utility functions."""

    def test_validate_json_rpc_request_success(self):
        """Test successful JSON-RPC request validation."""
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

    def test_validate_json_rpc_request_no_params(self):
        """Test JSON-RPC request validation without params."""
        request = {
            "jsonrpc": "2.0",
            "method": "test_method",
            "id": 1
        }
        method, params, request_id = validate_json_rpc_request(request)
        assert method == "test_method"
        assert params == {}
        assert request_id == 1

    def test_validate_json_rpc_request_invalid_version(self):
        """Test JSON-RPC request with invalid version."""
        request = {
            "jsonrpc": "1.0",
            "method": "test_method",
            "id": 1
        }
        with pytest.raises(ValueError, match="Invalid JSON-RPC version"):
            validate_json_rpc_request(request)

    def test_validate_json_rpc_request_missing_method(self):
        """Test JSON-RPC request without method."""
        request = {
            "jsonrpc": "2.0",
            "id": 1
        }
        with pytest.raises(ValueError, match="Method must be a non-empty string"):
            validate_json_rpc_request(request)

    def test_validate_json_rpc_request_not_dict(self):
        """Test JSON-RPC request that's not a dictionary."""
        with pytest.raises(ValueError, match="Request must be a dictionary"):
            validate_json_rpc_request("not a dict")

    def test_create_json_rpc_response(self):
        """Test creating JSON-RPC success response."""
        result = {"status": "ok"}
        response = create_json_rpc_response(result, 1)
        assert response["jsonrpc"] == "2.0"
        assert response["result"] == result
        assert response["id"] == 1

    def test_create_json_rpc_error(self):
        """Test creating JSON-RPC error response."""
        response = create_json_rpc_error(
            METHOD_NOT_FOUND,
            "Method not found",
            1
        )
        assert response["jsonrpc"] == "2.0"
        assert "error" in response
        assert response["error"]["code"] == METHOD_NOT_FOUND
        assert response["error"]["message"] == "Method not found"
        assert response["id"] == 1

    def test_create_json_rpc_error_with_data(self):
        """Test creating JSON-RPC error response with additional data."""
        error_data = {"details": "Additional error information"}
        response = create_json_rpc_error(
            INTERNAL_ERROR,
            "Internal error",
            1,
            data=error_data
        )
        assert response["error"]["data"] == error_data


class TestMCPMethodRegistry:
    """Test MCP method registry."""

    def test_register_method(self):
        """Test registering a method handler."""
        registry = MCPMethodRegistry()

        def test_handler(params):
            return {"result": "ok"}

        registry.register("test_method", test_handler)
        assert "test_method" in registry.list_methods()

    def test_register_duplicate_method(self):
        """Test registering duplicate method raises error."""
        registry = MCPMethodRegistry()

        def test_handler(params):
            return {"result": "ok"}

        registry.register("test_method", test_handler)

        with pytest.raises(ValueError, match="Method test_method already registered"):
            registry.register("test_method", test_handler)

    def test_get_handler(self):
        """Test getting handler from registry."""
        registry = MCPMethodRegistry()

        def test_handler(params):
            return {"result": "ok"}

        registry.register("test_method", test_handler)
        handler = registry.get_handler("test_method")
        assert handler is not None
        assert handler({"test": "params"}) == {"result": "ok"}

    def test_get_nonexistent_handler(self):
        """Test getting non-existent handler returns None."""
        registry = MCPMethodRegistry()
        handler = registry.get_handler("nonexistent")
        assert handler is None

    def test_list_methods(self):
        """Test listing all registered methods."""
        registry = MCPMethodRegistry()

        def handler1(params):
            return {}

        def handler2(params):
            return {}

        registry.register("method1", handler1)
        registry.register("method2", handler2)

        methods = registry.list_methods()
        assert len(methods) == 2
        assert "method1" in methods
        assert "method2" in methods


class TestMCPServer:
    """Test MCP server integration."""

    @pytest.fixture
    def mcp_server(self, tmp_path):
        """Create MCP server instance for testing."""
        server = MCPServer()
        yield server
        # No explicit cleanup needed - DatabaseManager handles its own cleanup

    def test_server_initialization(self, mcp_server):
        """Test MCP server initializes correctly."""
        assert mcp_server.db_manager is not None
        assert mcp_server.rule_manager is not None
        assert mcp_server.registry is not None

    def test_server_has_registry(self, mcp_server):
        """Test server has method registry."""
        assert hasattr(mcp_server, 'registry')
        assert isinstance(mcp_server.registry, MCPMethodRegistry)

    def test_server_registered_methods(self, mcp_server):
        """Test server registers all required methods."""
        methods = mcp_server.registry.list_methods()
        assert "validate_folder" in methods
        assert "approve" in methods
        assert "reject" in methods
        assert "enhance" in methods

    def test_handle_request_method_not_found(self, mcp_server):
        """Test handling request for non-existent method."""
        request = {
            "jsonrpc": "2.0",
            "method": "nonexistent_method",
            "params": {},
            "id": 1
        }
        response = mcp_server.handle_request(request)
        assert "error" in response
        assert response["error"]["code"] == METHOD_NOT_FOUND
        assert "Method not found" in response["error"]["message"]

    def test_handle_request_invalid_jsonrpc(self, mcp_server):
        """Test handling request with invalid JSON-RPC version."""
        request = {
            "jsonrpc": "1.0",
            "method": "validate_folder",
            "params": {},
            "id": 1
        }
        response = mcp_server.handle_request(request)
        assert "error" in response
        assert "Invalid JSON-RPC version" in response["error"]["message"]

    def test_handle_request_missing_method(self, mcp_server):
        """Test handling request without method field."""
        request = {
            "jsonrpc": "2.0",
            "params": {},
            "id": 1
        }
        response = mcp_server.handle_request(request)
        assert "error" in response
        assert "Invalid parameters" in response["error"]["message"]


class TestValidationMethods:
    """Test validation method handlers."""

    @pytest.fixture
    def validation_handler(self, tmp_path):
        """Create validation handler for testing."""
        db_manager = DatabaseManager()
        db_manager.init_database()

        from core.rule_manager import RuleManager
        rule_manager = RuleManager()

        handler = ValidationMethods(db_manager, rule_manager, None)
        yield handler
        # No explicit cleanup needed

    def test_validate_folder_missing_params(self, validation_handler):
        """Test validate_folder with missing parameters."""
        with pytest.raises(ValueError, match="Missing required parameters"):
            validation_handler.validate_folder({})

    def test_validate_folder_invalid_path(self, validation_handler):
        """Test validate_folder with non-existent path."""
        params = {
            "folder_path": "/nonexistent/path"
        }
        # This should raise an exception from the ingestion system
        with pytest.raises(Exception):
            validation_handler.validate_folder(params)


class TestApprovalMethods:
    """Test approval method handlers."""

    @pytest.fixture
    def approval_handler(self, tmp_path):
        """Create approval handler for testing."""
        db_manager = DatabaseManager()
        db_manager.init_database()

        from core.rule_manager import RuleManager
        rule_manager = RuleManager()

        handler = ApprovalMethods(db_manager, rule_manager, None)
        yield handler
        # No explicit cleanup needed

    def test_approve_missing_params(self, approval_handler):
        """Test approve with missing parameters."""
        with pytest.raises(ValueError, match="Missing required parameters"):
            approval_handler.approve({})

    def test_approve_invalid_ids_type(self, approval_handler):
        """Test approve with invalid ids type."""
        params = {"ids": "not a list"}
        with pytest.raises(ValueError, match="ids must be a list"):
            approval_handler.approve(params)

    def test_approve_empty_list(self, approval_handler):
        """Test approve with empty ids list."""
        params = {"ids": []}
        result = approval_handler.approve(params)
        assert result["success"] is True
        assert result["approved_count"] == 0

    def test_approve_nonexistent_id(self, approval_handler):
        """Test approve with non-existent validation ID."""
        params = {"ids": ["nonexistent-id"]}
        result = approval_handler.approve(params)
        assert result["success"] is True
        assert result["approved_count"] == 0
        assert len(result["errors"]) > 0

    def test_reject_missing_params(self, approval_handler):
        """Test reject with missing parameters."""
        with pytest.raises(ValueError, match="Missing required parameters"):
            approval_handler.reject({})

    def test_reject_invalid_ids_type(self, approval_handler):
        """Test reject with invalid ids type."""
        params = {"ids": "not a list"}
        with pytest.raises(ValueError, match="ids must be a list"):
            approval_handler.reject(params)

    def test_reject_empty_list(self, approval_handler):
        """Test reject with empty ids list."""
        params = {"ids": []}
        result = approval_handler.reject(params)
        assert result["success"] is True
        assert result["rejected_count"] == 0

    def test_reject_nonexistent_id(self, approval_handler):
        """Test reject with non-existent validation ID."""
        params = {"ids": ["nonexistent-id"]}
        result = approval_handler.reject(params)
        assert result["success"] is True
        assert result["rejected_count"] == 0
        assert len(result["errors"]) > 0


class TestEnhancementMethods:
    """Test enhancement method handlers."""

    @pytest.fixture
    def enhancement_handler(self, tmp_path):
        """Create enhancement handler for testing."""
        db_manager = DatabaseManager()
        db_manager.init_database()

        from core.rule_manager import RuleManager
        rule_manager = RuleManager()

        handler = EnhancementMethods(db_manager, rule_manager, None)
        yield handler
        # No explicit cleanup needed

    def test_enhance_missing_params(self, enhancement_handler):
        """Test enhance with missing parameters."""
        with pytest.raises(ValueError, match="Missing required parameters"):
            enhancement_handler.enhance({})

    def test_enhance_invalid_ids_type(self, enhancement_handler):
        """Test enhance with invalid ids type."""
        params = {"ids": "not a list"}
        with pytest.raises(ValueError, match="ids must be a list"):
            enhancement_handler.enhance(params)

    def test_enhance_empty_list(self, enhancement_handler):
        """Test enhance with empty ids list."""
        params = {"ids": []}
        result = enhancement_handler.enhance(params)
        assert result["success"] is True
        assert result["enhanced_count"] == 0
        assert result["enhancements"] == []

    def test_enhance_nonexistent_id(self, enhancement_handler):
        """Test enhance with non-existent validation ID."""
        params = {"ids": ["nonexistent-id"]}
        result = enhancement_handler.enhance(params)
        assert result["success"] is True
        assert result["enhanced_count"] == 0
        assert len(result["errors"]) > 0
