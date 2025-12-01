# file: tbcv/svc/mcp_server.py
"""
MCP (Model Context Protocol) server for TBCV validation system.
Provides a JSON-RPC interface for validation operations.
"""
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import asyncio
# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.database import DatabaseManager, ValidationResult, ValidationStatus
from core.path_validator import is_safe_path, validate_write_path
from core.rule_manager import RuleManager
from core.ingestion import MarkdownIngestion
from core.validation_store import list_validation_records
from core.database import ValidationResult
from core.io_win import write_text_crlf
class MCPServer:
    """MCP server for TBCV validation operations."""
    def __init__(self):
        """Initialize MCP server with required components."""
        self.db_manager = DatabaseManager()
        self.rule_manager = RuleManager()
        self.ingestion = MarkdownIngestion(self.db_manager, self.rule_manager)
        # Initialize database
        self.db_manager.init_database()

        # Initialize method registry
        from svc.mcp_methods import (
            MCPMethodRegistry,
            ValidationMethods,
            ApprovalMethods,
            EnhancementMethods
        )
        self.registry = MCPMethodRegistry()

        # Placeholder for agent registry (will be implemented in later tasks)
        self.agent_registry = None

        # Register all method handlers
        self._register_methods()

    def _register_methods(self):
        """Register all MCP method handlers."""
        from svc.mcp_methods import (
            ValidationMethods,
            ApprovalMethods,
            EnhancementMethods,
            AdminMethods
        )

        # Initialize method handler instances
        validation_handler = ValidationMethods(
            self.db_manager,
            self.rule_manager,
            self.agent_registry
        )
        approval_handler = ApprovalMethods(
            self.db_manager,
            self.rule_manager,
            self.agent_registry
        )
        enhancement_handler = EnhancementMethods(
            self.db_manager,
            self.rule_manager,
            self.agent_registry
        )
        admin_handler = AdminMethods(
            self.db_manager,
            self.rule_manager,
            self.agent_registry
        )

        # Register validation methods
        self.registry.register("validate_folder", validation_handler.validate_folder)
        self.registry.register("validate_file", validation_handler.validate_file)
        self.registry.register("validate_content", validation_handler.validate_content)
        self.registry.register("get_validation", validation_handler.get_validation)
        self.registry.register("list_validations", validation_handler.list_validations)
        self.registry.register("update_validation", validation_handler.update_validation)
        self.registry.register("delete_validation", validation_handler.delete_validation)
        self.registry.register("revalidate", validation_handler.revalidate)

        # Register approval methods
        self.registry.register("approve", approval_handler.approve)
        self.registry.register("reject", approval_handler.reject)

        # Register enhancement methods
        self.registry.register("enhance", enhancement_handler.enhance)

        # Register admin methods
        self.registry.register("get_system_status", admin_handler.get_system_status)
        self.registry.register("clear_cache", admin_handler.clear_cache)
        self.registry.register("get_cache_stats", admin_handler.get_cache_stats)
        self.registry.register("cleanup_cache", admin_handler.cleanup_cache)
        self.registry.register("rebuild_cache", admin_handler.rebuild_cache)
        self.registry.register("reload_agent", admin_handler.reload_agent)
        self.registry.register("run_gc", admin_handler.run_gc)
        self.registry.register("enable_maintenance_mode", admin_handler.enable_maintenance_mode)
        self.registry.register("disable_maintenance_mode", admin_handler.disable_maintenance_mode)
        self.registry.register("create_checkpoint", admin_handler.create_checkpoint)
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle JSON-RPC request using registry pattern.

        Args:
            request: JSON-RPC request object

        Returns:
            JSON-RPC response object
        """
        from svc.mcp_methods import (
            validate_json_rpc_request,
            create_json_rpc_response,
            create_json_rpc_error,
            METHOD_NOT_FOUND,
            INTERNAL_ERROR
        )

        try:
            # Validate request structure
            method, params, request_id = validate_json_rpc_request(request)

            # Get handler from registry
            handler = self.registry.get_handler(method)
            if not handler:
                return create_json_rpc_error(
                    METHOD_NOT_FOUND,
                    f"Method not found: {method}",
                    request_id
                )

            # Execute handler
            result = handler(params)

            return create_json_rpc_response(result, request_id)

        except ValueError as e:
            # Parameter validation errors
            return create_json_rpc_error(
                INTERNAL_ERROR,
                f"Invalid parameters: {str(e)}",
                request.get("id")
            )
        except Exception as e:
            # Other internal errors
            return create_json_rpc_error(
                INTERNAL_ERROR,
                f"Internal error: {str(e)}",
                request.get("id")
            )


class MCPStdioServer:
    """MCP server that communicates via stdin/stdout."""
    def __init__(self):
        """Initialize stdio MCP server."""
        self.server = MCPServer()
    async def run(self):
        """Run the stdio MCP server."""
        while True:
            try:
                # Read line from stdin
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )
                if not line:
                    break
                line = line.strip()
                if not line:
                    continue
                # Parse JSON-RPC request
                try:
                    request = json.loads(line)
                except json.JSONDecodeError as e:
                    response = {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32700,
                            "message": f"Parse error: {str(e)}"
                        },
                        "id": None
                    }
                    print(json.dumps(response))
                    continue
                # Handle request
                response = self.server.handle_request(request)
                # Send response
                print(json.dumps(response))
                sys.stdout.flush()
            except KeyboardInterrupt:
                break
            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": f"Server error: {str(e)}"
                    },
                    "id": None
                }
                print(json.dumps(error_response))
def create_mcp_client() -> MCPServer:
    """
    Create an in-process MCP client.
    Returns:
        MCP server instance for direct method calls
    """
    return MCPServer()
async def main():
    """Main entry point for stdio MCP server."""
    server = MCPStdioServer()
    await server.run()
if __name__ == "__main__":
    asyncio.run(main())
