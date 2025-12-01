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
            AdminMethods,
            QueryMethods
        )
        from svc.mcp_methods.workflow_methods import WorkflowMethods
        from svc.mcp_methods.recommendation_methods import RecommendationMethods

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
        workflow_handler = WorkflowMethods(
            self.db_manager,
            self.rule_manager,
            self.agent_registry
        )
        query_handler = QueryMethods(
            self.db_manager,
            self.rule_manager,
            self.agent_registry
        )
        recommendation_handler = RecommendationMethods(
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
        self.registry.register("bulk_approve", approval_handler.bulk_approve)
        self.registry.register("bulk_reject", approval_handler.bulk_reject)

        # Register enhancement methods
        self.registry.register("enhance", enhancement_handler.enhance)
        self.registry.register("enhance_batch", enhancement_handler.enhance_batch)
        self.registry.register("enhance_preview", enhancement_handler.enhance_preview)
        self.registry.register("enhance_auto_apply", enhancement_handler.enhance_auto_apply)
        self.registry.register("get_enhancement_comparison", enhancement_handler.get_enhancement_comparison)

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

        # Register workflow methods
        self.registry.register("create_workflow", workflow_handler.create_workflow)
        self.registry.register("get_workflow", workflow_handler.get_workflow)
        self.registry.register("list_workflows", workflow_handler.list_workflows)
        self.registry.register("control_workflow", workflow_handler.control_workflow)
        self.registry.register("get_workflow_report", workflow_handler.get_workflow_report)
        self.registry.register("get_workflow_summary", workflow_handler.get_workflow_summary)
        self.registry.register("delete_workflow", workflow_handler.delete_workflow)
        self.registry.register("bulk_delete_workflows", workflow_handler.bulk_delete_workflows)

        # Register query methods
        self.registry.register("get_stats", query_handler.get_stats)
        self.registry.register("get_audit_log", query_handler.get_audit_log)
        self.registry.register("get_performance_report", query_handler.get_performance_report)
        self.registry.register("get_health_report", query_handler.get_health_report)
        self.registry.register("get_validation_history", query_handler.get_validation_history)
        self.registry.register("get_available_validators", query_handler.get_available_validators)
        self.registry.register("export_validation", query_handler.export_validation)
        self.registry.register("export_recommendations", query_handler.export_recommendations)
        self.registry.register("export_workflow", query_handler.export_workflow)

        # Register recommendation methods
        self.registry.register("generate_recommendations", recommendation_handler.generate_recommendations)
        self.registry.register("rebuild_recommendations", recommendation_handler.rebuild_recommendations)
        self.registry.register("get_recommendations", recommendation_handler.get_recommendations)
        self.registry.register("review_recommendation", recommendation_handler.review_recommendation)
        self.registry.register("bulk_review_recommendations", recommendation_handler.bulk_review_recommendations)
        self.registry.register("apply_recommendations", recommendation_handler.apply_recommendations)
        self.registry.register("delete_recommendation", recommendation_handler.delete_recommendation)
        self.registry.register("mark_recommendations_applied", recommendation_handler.mark_recommendations_applied)

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
