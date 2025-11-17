# file: tbcv/svc/mcp_server.py
"""
MCP (Model Context Protocol) server for TBCV validation system.
Provides a JSON-RPC interface for validation operations.
"""
import json
import sys
import uuid
from datetime import datetime
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
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle JSON-RPC request.
        Args:
            request: JSON-RPC request object
        Returns:
            JSON-RPC response object
        """
        try:
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")
            if method == "validate_folder":
                result = self._validate_folder(params)
            elif method == "approve":
                result = self._approve(params)
            elif method == "reject":
                result = self._reject(params)
            elif method == "enhance":
                result = self._enhance(params)
            else:
                return {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    },
                    "id": request_id
                }
            return {
                "jsonrpc": "2.0",
                "result": result,
                "id": request_id
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                },
                "id": request.get("id")
            }
    def _validate_folder(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate all markdown files in a folder.
        Args:
            params: Parameters containing folder_path
        Returns:
            Validation results
        """
        folder_path = params.get("folder_path")
        if not folder_path:
            raise ValueError("folder_path parameter is required")
        recursive = params.get("recursive", True)
        # Run ingestion
        results = self.ingestion.ingest_folder(folder_path, recursive=recursive)
        return {
            "success": True,
            "message": f"Validated {results['files_processed']} files",
            "results": results
        }
    def _approve(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Approve validation records.
        Args:
            params: Parameters containing ids list
        Returns:
            Approval results
        """
        ids = params.get("ids", [])
        if not ids:
            raise ValueError("ids parameter is required")
        approved_count = 0
        errors = []
        for validation_id in ids:
            try:
                # For Part 3, implement proper database updates
                # Get all validation records and find the one we need
                records = self.db_manager.list_validation_results(limit=1000)
                validation = None
                for record in records:
                    if record.id == validation_id:
                        validation = record
                        break
                if not validation:
                    errors.append(f"Validation {validation_id} not found")
                    continue
                # Update status directly in database
                with self.db_manager.get_session() as session:
                    db_record = session.query(ValidationResult).filter(ValidationResult.id == validation_id).first()
                    if db_record:
                        db_record.status = ValidationStatus.APPROVED
                        db_record.updated_at = datetime.utcnow()
                        session.commit()
                        approved_count += 1
                    else:
                        errors.append(f"Validation {validation_id} not found in database")
            except Exception as e:
                errors.append(f"Error approving {validation_id}: {str(e)}")
        return {
            "success": True,
            "approved_count": approved_count,
            "errors": errors
        }
    def _reject(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reject validation records.
        Args:
            params: Parameters containing ids list
        Returns:
            Rejection results
        """
        ids = params.get("ids", [])
        if not ids:
            raise ValueError("ids parameter is required")
        rejected_count = 0
        errors = []
        for validation_id in ids:
            try:
                # Get all validation records and find the one we need
                records = self.db_manager.list_validation_results(limit=1000)
                validation = None
                for record in records:
                    if record.id == validation_id:
                        validation = record
                        break
                if not validation:
                    errors.append(f"Validation {validation_id} not found")
                    continue
                # Update status directly in database
                with self.db_manager.get_session() as session:
                    db_record = session.query(ValidationResult).filter(ValidationResult.id == validation_id).first()
                    if db_record:
                        db_record.status = ValidationStatus.REJECTED
                        db_record.updated_at = datetime.utcnow()
                        session.commit()
                        rejected_count += 1
                    else:
                        errors.append(f"Validation {validation_id} not found in database")
            except Exception as e:
                errors.append(f"Error rejecting {validation_id}: {str(e)}")
        return {
            "success": True,
            "rejected_count": rejected_count,
            "errors": errors
        }
    def _enhance(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance approved validation records.
        Args:
            params: Parameters containing ids list
        Returns:
            Enhancement results
        """
        ids = params.get("ids", [])
        if not ids:
            raise ValueError("ids parameter is required")
        enhanced_count = 0
        errors = []
        enhancements = []  # FIX: Initialize the enhancements list
        for validation_id in ids:
            try:
                # Get validation record
                records = self.db_manager.list_validation_results(limit=1000)
                validation = None
                for record in records:
                    if record.id == validation_id:
                        validation = record
                        break
                if not validation:
                    errors.append(f"Validation {validation_id} not found")
                    continue
                # Check if validation is approved
                if validation.status != ValidationStatus.APPROVED:
                    errors.append(f"Validation {validation_id} not approved (status: {validation.status})")
                    continue
                # Load original markdown file
                file_path = Path(validation.file_path)
                
                # FIX: Validate path safety
                if not is_safe_path(file_path):
                    errors.append(f"Unsafe file path: {file_path}")
                    continue
                
                if not file_path.exists():
                    errors.append(f"File not found: {file_path}")
                    continue
                
                # FIX: Validate write permissions
                if not validate_write_path(file_path):
                    errors.append(f"Cannot write to file: {file_path}")
                    continue
                # Read original content
                from core.io_win import read_text, write_text_crlf
                original_content = read_text(file_path)
                # Get enhancement prompts
                from core.prompt_loader import get_prompt
                try:
                    enhancement_prompt = get_prompt("enhancer", "enhance_markdown")
                except Exception:
                    # Fallback prompt if loader fails
                    enhancement_prompt = """Please enhance this markdown document by:
1. Improving clarity and readability
2. Fixing any grammatical issues
3. Ensuring proper formatting
4. Adding missing sections if needed
5. Maintaining the original meaning and structure
Original content:
{content}
Enhanced content:"""
                # Call Ollama for enhancement
                from core.ollama import chat
                try:
                    messages = [
                        {"role": "system", "content": "You are a technical writing assistant. Enhance markdown documents while preserving their structure and meaning."},
                        {"role": "user", "content": enhancement_prompt.format(content=original_content)}
                    ]
                    # Get model from environment or use default
                    import os
                    model = os.getenv("OLLAMA_MODEL", "llama2")
                    response = chat(model, messages)
                    enhanced_content = response.strip()
                    # Write enhanced content atomically
                    write_text_crlf(file_path, enhanced_content, atomic=True)
                    # Create audit log entry
                    audit_entry = {
                        "validation_id": validation_id,
                        "action": "enhance",
                        "timestamp": datetime.utcnow().isoformat(),
                        "original_size": len(original_content),
                        "enhanced_size": len(enhanced_content),
                        "model_used": model
                    }
                    # Update validation status to enhanced
                    with self.db_manager.get_session() as session:
                        db_record = session.query(ValidationResult).filter(ValidationResult.id == validation_id).first()
                        if db_record:
                            db_record.status = ValidationStatus.ENHANCED
                            db_record.updated_at = datetime.utcnow()
                            # Store enhancement details in notes
                            current_notes = db_record.notes or ""
                            db_record.notes = f"{current_notes}\n\nEnhanced: {audit_entry}"
                            session.commit()
                    enhanced_count += 1
                    enhancements.append(audit_entry)
                except Exception as ollama_error:
                    errors.append(f"Enhancement failed for {validation_id}: {str(ollama_error)}")
            except Exception as e:
                errors.append(f"Error enhancing {validation_id}: {str(e)}")
        return {
            "success": True,
            "enhanced_count": enhanced_count,
            "errors": errors,
            "enhancements": enhancements  # FIX: Return the enhancements list
        }
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
