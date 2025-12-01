"""Example integration of MCP helpers in FastAPI endpoints.

This file demonstrates how to use the MCP helper utilities to migrate
existing API endpoints to use the MCP async client.

MIGRATION PATTERN:

Before (Direct Agent Access):
    from agents.orchestrator import OrchestratorAgent

    @app.get("/validations/{validation_id}")
    async def get_validation(validation_id: str):
        orchestrator = OrchestratorAgent()
        result = orchestrator.get_validation(validation_id)
        return result

After (MCP Client):
    from fastapi import Depends
    from api.mcp_helpers import MCPClientDependency, format_mcp_response

    mcp_client = MCPClientDependency()

    @app.get("/validations/{validation_id}")
    async def get_validation(
        validation_id: str,
        client: MCPAsyncClient = Depends(mcp_client)
    ):
        result = await client.get_validation(validation_id)
        return format_mcp_response(result)
"""

from typing import List, Optional
from fastapi import FastAPI, Depends, Query
from pydantic import BaseModel

from svc.mcp_client import MCPAsyncClient
from api.mcp_helpers import (
    MCPClientDependency,
    format_mcp_response,
    call_mcp_method_formatted,
)
from api.error_handlers import register_error_handlers

# =============================================================================
# Application Setup
# =============================================================================

app = FastAPI(title="TBCV API with MCP Integration")

# Register error handlers
register_error_handlers(app)

# Create dependency instance
mcp_client = MCPClientDependency()


# =============================================================================
# Request Models
# =============================================================================


class ValidateFileRequest(BaseModel):
    """Request model for file validation."""
    file_path: str
    family: str = "words"
    validation_types: Optional[List[str]] = None


class ValidateContentRequest(BaseModel):
    """Request model for content validation."""
    content: str
    file_path: str = "temp.md"
    validation_types: Optional[List[str]] = None


class ApproveRequest(BaseModel):
    """Request model for approval."""
    validation_ids: List[str]


class RejectRequest(BaseModel):
    """Request model for rejection."""
    validation_ids: List[str]
    reason: Optional[str] = None


# =============================================================================
# Pattern 1: Dependency Injection
# =============================================================================
# Use this pattern when you need fine-grained control over the MCP client
# and want to explicitly handle errors.


@app.post("/api/v1/validate/file")
async def validate_file_with_dependency(
    request: ValidateFileRequest,
    client: MCPAsyncClient = Depends(mcp_client)
):
    """
    Validate a file using dependency injection pattern.

    This pattern gives you:
    - Full control over the client
    - Type hints and IDE support
    - Easy to test with mocked clients
    """
    result = await client.validate_file(
        file_path=request.file_path,
        family=request.family,
        validation_types=request.validation_types
    )
    return format_mcp_response(result, meta={"endpoint": "validate_file"})


@app.get("/api/v1/validations/{validation_id}")
async def get_validation_with_dependency(
    validation_id: str,
    client: MCPAsyncClient = Depends(mcp_client)
):
    """
    Get validation by ID using dependency injection.

    MCP errors are automatically converted to HTTP exceptions
    by the error handler.
    """
    result = await client.get_validation(validation_id)
    return format_mcp_response(result)


@app.get("/api/v1/validations")
async def list_validations_with_dependency(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    status: Optional[str] = None,
    file_path: Optional[str] = None,
    client: MCPAsyncClient = Depends(mcp_client)
):
    """
    List validations with filtering using dependency injection.

    Query parameters are validated by FastAPI before the handler runs.
    """
    result = await client.list_validations(
        limit=limit,
        offset=offset,
        status=status,
        file_path=file_path
    )
    return format_mcp_response(
        result,
        meta={
            "pagination": {
                "limit": limit,
                "offset": offset,
                "has_more": len(result.get("validations", [])) == limit
            }
        }
    )


# =============================================================================
# Pattern 2: Convenience Functions
# =============================================================================
# Use this pattern for simple endpoints that just forward to MCP methods.


@app.post("/api/v1/validate/content")
async def validate_content_simple(request: ValidateContentRequest):
    """
    Validate content using convenience function.

    This pattern is simpler and more concise for straightforward endpoints.
    """
    return await call_mcp_method_formatted(
        "validate_content",
        content=request.content,
        file_path=request.file_path,
        validation_types=request.validation_types,
        meta={"endpoint": "validate_content"}
    )


@app.post("/api/v1/approve")
async def approve_validations_simple(request: ApproveRequest):
    """
    Approve validations using convenience function.
    """
    return await call_mcp_method_formatted(
        "approve",
        validation_ids=request.validation_ids,
        meta={"count": len(request.validation_ids)}
    )


@app.post("/api/v1/reject")
async def reject_validations_simple(request: RejectRequest):
    """
    Reject validations using convenience function.
    """
    return await call_mcp_method_formatted(
        "reject",
        validation_ids=request.validation_ids,
        reason=request.reason,
        meta={"count": len(request.validation_ids)}
    )


# =============================================================================
# Pattern 3: Hybrid (Dependency + Custom Logic)
# =============================================================================
# Use this pattern when you need to add business logic around MCP calls.


@app.post("/api/v1/validate/folder")
async def validate_folder_hybrid(
    folder_path: str,
    recursive: bool = True,
    client: MCPAsyncClient = Depends(mcp_client)
):
    """
    Validate folder with additional business logic.

    This pattern combines dependency injection with custom logic
    for more complex scenarios.
    """
    import time
    from pathlib import Path

    start_time = time.time()

    # Validate input
    if not Path(folder_path).exists():
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Folder does not exist")

    # Call MCP method
    result = await client.validate_folder(
        folder_path=folder_path,
        recursive=recursive
    )

    # Add custom metadata
    execution_time = time.time() - start_time
    return format_mcp_response(
        result,
        meta={
            "endpoint": "validate_folder",
            "execution_time_seconds": round(execution_time, 3),
            "folder_path": folder_path,
            "recursive": recursive,
        }
    )


@app.delete("/api/v1/validations/{validation_id}")
async def delete_validation_hybrid(
    validation_id: str,
    client: MCPAsyncClient = Depends(mcp_client)
):
    """
    Delete validation with audit logging.

    Adds custom audit logic before/after the MCP call.
    """
    from core.logging import get_logger
    logger = get_logger(__name__)

    # Log the deletion attempt
    logger.info(f"Attempting to delete validation: {validation_id}")

    # Call MCP method
    result = await client.delete_validation(validation_id)

    # Log success
    logger.info(f"Successfully deleted validation: {validation_id}")

    return format_mcp_response(
        result,
        meta={
            "action": "delete",
            "validation_id": validation_id
        }
    )


# =============================================================================
# Pattern 4: Batch Operations
# =============================================================================
# Use this pattern for operations that process multiple items.


@app.post("/api/v1/enhance/batch")
async def enhance_batch(
    validation_ids: List[str],
    batch_size: int = Query(10, ge=1, le=100),
    threshold: float = Query(0.7, ge=0.0, le=1.0),
    client: MCPAsyncClient = Depends(mcp_client)
):
    """
    Enhance multiple validations in batches.

    Shows how to handle batch operations with progress tracking.
    """
    result = await client.enhance_batch(
        validation_ids=validation_ids,
        batch_size=batch_size,
        threshold=threshold
    )

    return format_mcp_response(
        result,
        meta={
            "total_items": len(validation_ids),
            "batch_size": batch_size,
            "threshold": threshold,
        }
    )


# =============================================================================
# Pattern 5: Health and Status Endpoints
# =============================================================================
# Use this pattern for operational endpoints that check system status.


@app.get("/api/v1/health/system")
async def system_health(client: MCPAsyncClient = Depends(mcp_client)):
    """
    Get system health status.

    Returns system status for monitoring and alerting.
    """
    result = await client.get_system_status()

    # Determine overall health
    is_healthy = result.get("status") == "healthy"

    return format_mcp_response(
        result,
        success=is_healthy,
        meta={
            "check_type": "system_health",
            "is_healthy": is_healthy
        }
    )


@app.get("/api/v1/stats")
async def get_stats(client: MCPAsyncClient = Depends(mcp_client)):
    """
    Get system statistics.

    Returns statistics for dashboard and reporting.
    """
    result = await client.get_stats()

    return format_mcp_response(
        result,
        meta={
            "endpoint": "stats",
            "cached": False
        }
    )


# =============================================================================
# Migration Checklist
# =============================================================================

"""
MIGRATION CHECKLIST FOR EXISTING ENDPOINTS:

1. Import Dependencies:
   - Add: from api.mcp_helpers import MCPClientDependency, format_mcp_response
   - Add: from svc.mcp_client import MCPAsyncClient

2. Update Endpoint Signature:
   - Add: client: MCPAsyncClient = Depends(mcp_client)
   - Or use: call_mcp_method_formatted() for simple cases

3. Replace Direct Agent Calls:
   - Before: orchestrator.validate_file(...)
   - After: await client.validate_file(...)

4. Format Response:
   - Add: return format_mcp_response(result, meta={...})

5. Error Handling:
   - Remove try/except blocks (handled by error_handlers.py)
   - MCP errors automatically convert to HTTP exceptions

6. Testing:
   - Update tests to mock MCPAsyncClient
   - Test error scenarios (404, 422, 500, etc.)
   - Verify response format matches new standard

EXAMPLE MIGRATION:

# BEFORE
@app.get("/validations/{validation_id}")
async def get_validation(validation_id: str):
    try:
        orchestrator = OrchestratorAgent()
        result = orchestrator.get_validation(validation_id)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# AFTER
@app.get("/validations/{validation_id}")
async def get_validation(
    validation_id: str,
    client: MCPAsyncClient = Depends(mcp_client)
):
    result = await client.get_validation(validation_id)
    return format_mcp_response(result)
"""
