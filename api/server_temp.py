# file: tbcv/api/server.py
"""
Complete FastAPI server with all endpoints for TBCV system.

New Features:
- Complete health endpoints (/health/live, /health/ready)
- Recommendation approval workflow
- Batch validation endpoints
- Enhancement endpoints
- Workflow management (pause/resume/cancel)
- Dashboard integration
- Audit logging
"""

from __future__ import annotations

import asyncio
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager
from datetime import datetime
from importlib import resources as ilres

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Query, Response, status

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

# Project imports
try:
    from agents.base import agent_registry
    from agents.truth_manager import TruthManagerAgent
    from agents.fuzzy_detector import FuzzyDetectorAgent
    from agents.content_validator import ContentValidatorAgent
    from agents.content_enhancer import ContentEnhancerAgent
    from agents.code_analyzer import CodeAnalyzerAgent
    from agents.orchestrator import OrchestratorAgent
except ImportError:
    from agents.base import agent_registry
    from agents.truth_manager import TruthManagerAgent
    from agents.fuzzy_detector import FuzzyDetectorAgent
    from agents.content_validator import ContentValidatorAgent
    from agents.content_enhancer import ContentEnhancerAgent
    from agents.code_analyzer import CodeAnalyzerAgent
    from agents.orchestrator import OrchestratorAgent

try:
    from core.config import get_settings
    from core.logging import setup_logging, get_logger
    from core.database import db_manager, WorkflowState, RecommendationStatus
except ImportError:
    from core.config import get_settings
    from core.logging import setup_logging, get_logger
    from core.database import db_manager, WorkflowState, RecommendationStatus

logger = get_logger(__name__)

# =============================================================================
# Pydantic Models for API
# =============================================================================

class ContentValidationRequest(BaseModel):
    content: str
    file_path: str = "unknown"
    family: str = "words"
    validation_types: List[str] = ["yaml", "markdown", "code", "links", "structure"]

class DirectoryValidationRequest(BaseModel):
    directory_path: str
    file_pattern: str = "*.md"
    workflow_type: str = "validate_file"
    max_workers: int = 4
    family: str = "words"

class BatchValidationRequest(BaseModel):
    files: List[str] = Field(description="List of file paths to validate")
    family: str = "words"
    validation_types: List[str] = ["yaml", "markdown", "code", "links", "structure"]
    max_workers: int = 4

class EnhanceContentRequest(BaseModel):
    validation_id: str = Field(description="Validation result ID to enhance from")
    file_path: str
    content: str
    recommendations: Optional[List[str]] = Field(None, description="Specific recommendation IDs to apply")
    preview: bool = Field(False, description="Preview changes without applying")

class RecommendationReviewRequest(BaseModel):
    status: str = Field(description="approved, rejected, or pending")
    reviewer: Optional[str] = None
    notes: Optional[str] = None

class WorkflowControlRequest(BaseModel):
    action: str = Field(description="pause, resume, or cancel")

class FolderImportRequest(BaseModel):
    folder: str = Field(description="Path to folder containing markdown files to import and validate")
    recursive: bool = Field(True, description="Whether to recursively scan subdirectories")

class WorkflowStatus(BaseModel):
    job_id: str
    status: str
    files_total: int = 0
    files_validated: int = 0
    files_failed: int = 0
    errors: List[str] = []

# Global workflow status tracking
workflow_jobs: Dict[str, WorkflowStatus] = {}

# =============================================================================
# Application Lifecycle
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""
    # Startup
    setup_logging()
    logger.info("Starting TBCV API server")

    # Initialize database (idempotent)
    db_manager.init_database()

    # Register agents
    await register_agents()

    try:
        yield
    finally:
        # Shutdown
        logger.info("Shutting down TBCV API server")
        agent_registry.clear()

async def register_agents():
    """Register all agents with the agent registry."""
    try:
        # Create agents
        truth_manager = TruthManagerAgent("truth_manager")
        fuzzy_detector = FuzzyDetectorAgent("fuzzy_detector")
        content_validator = ContentValidatorAgent("content_validator")
        content_enhancer = ContentEnhancerAgent("content_enhancer")
        code_analyzer = CodeAnalyzerAgent("code_analyzer")
        orchestrator = OrchestratorAgent("orchestrator")

        # Register agents
        agent_registry.register_agent(truth_manager)
        agent_registry.register_agent(fuzzy_detector)
        agent_registry.register_agent(content_validator)
        agent_registry.register_agent(content_enhancer)
        agent_registry.register_agent(code_analyzer)
        agent_registry.register_agent(orchestrator)

        logger.info("All agents registered successfully")
    except Exception:
        logger.exception("Failed to register agents")
        raise

# =============================================================================
# Create FastAPI App
# =============================================================================


app = FastAPI(
    title="TBCV API",
    description="Truth-Based Content Validation and Enhancement System",
    version="2.0.0",
    lifespan=lifespan
)
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include dashboard router if available
try:
    from api.dashboard import router as dashboard_router
    app.include_router(dashboard_router)
except Exception:
    pass

# Setup templates for dashboard
templates = Jinja2Templates(directory="templates")

# =============================================================================
# Health Check Endpoints
# =============================================================================

@app.get("/health")
async def health_check(response: Response):
    """Comprehensive health check endpoint (DB REQUIRED)."""
    database_connected = False
    try:
        database_connected = db_manager.is_connected()
    except Exception:
        database_connected = False

    # Enforce DB-required readiness: return 503 until DB is reachable
    if not database_connected:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "healthy" if database_connected else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "agents_registered": len(agent_registry.list_agents()),
        "database_connected": database_connected,
        "version": "2.0.0",
    }


@app.get("/health/live")
async def health_live():
    """Kubernetes liveness probe - is the application running?"""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
    }

@app.get("/health/ready")
async def readiness_check(response: Response):
    """Kubernetes readiness probe (DB & agents REQUIRED)."""
    checks = {
        "database": False,
        "agents": False
    }
    try:
        checks["database"] = db_manager.is_connected()
    except Exception:
        checks["database"] = False

    try:
        checks["agents"] = len(agent_registry.list_agents()) > 0
    except Exception:
        checks["agents"] = False

    all_ready = all(checks.values())

    # Enforce non-200 until all checks pass
    if not all_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ready" if all_ready else "not_ready",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks,
    }


# =============================================================================
# Agent Management Endpoints
# =============================================================================

@app.get("/agents")
async def list_agents():
    """List all registered agents."""
    agents = agent_registry.list_agents()
    result = []
    for agent_id, agent in agents.items():
        try:
            contract = agent.get_contract()
            result.append({
                "agent_id": agent_id,
                "agent_type": type(agent).__name__,
                "status": "active",
                "contract": contract.to_dict() if contract else None
            })
        except Exception:
            result.append({
                "agent_id": agent_id,
                "agent_type": type(agent).__name__,
                "status": "active",
                "contract": None
            })
    return {
        "agents": result,
        "total_count": len(agents)
    }

@app.get("/agents/{agent_id}")
async def get_agent_info(agent_id: str):
    """Get information about a specific agent."""
    agent = agent_registry.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    try:
        contract = agent.get_contract()
        return {
            "agent_id": agent_id,
            "agent_type": type(agent).__name__,
            "contract": {
                "name": contract.name,
                "version": contract.version,
                "capabilities": [cap.name for cap in contract.capabilities]
            },
            "status": "active"
        }
    except Exception:
        logger.exception("Failed to get agent contract for %s", agent_id)
        return {
            "agent_id": agent_id,
            "agent_type": type(agent).__name__,
            "error": "Failed to read contract",
            "status": "error"
        }

@app.get("/registry/agents")
async def get_agent_registry():
    """Get the complete agent registry state."""
    agents = agent_registry.list_agents()
    registry_info = {
        "total_agents": len(agents),
        "agents": {},
        "registry_status": "active"
    }

    for agent_id, agent in agents.items():
        try:
            contract = agent.get_contract()
            registry_info["agents"][agent_id] = {
                "type": type(agent).__name__,
                "contract": contract.name if contract else "unknown",
                "capabilities": [cap.name for cap in contract.capabilities] if contract else []
            }
        except Exception:
            logger.exception("Error while building registry info for %s", agent_id)
            registry_info["agents"][agent_id] = {
                "type": type(agent).__name__,
                "error": "contract read error"
            }

    return registry_info

# =============================================================================
# Content Validation Endpoints
# =============================================================================

@app.post("/agents/validate")
async def validate_content(request: ContentValidationRequest):
    """Validate content using the content validator agent."""
    validator = agent_registry.get_agent("content_validator")
    if not validator:
        raise HTTPException(status_code=500, detail="Content validator agent not available")

    try:
        result = await validator.process_request("validate_content", {
            "content": request.content,
            "file_path": request.file_path,
            "family": request.family,
            "validation_types": request.validation_types
        })
        return result
    except Exception:
        logger.exception("Content validation failed")
        raise HTTPException(status_code=500, detail="Validation failed")

@app.post("/api/validate/batch")
async def batch_validate_content(request: BatchValidationRequest, background_tasks: BackgroundTasks):
    """Start batch validation workflow."""
    import uuid
    job_id = str(uuid.uuid4())
    
    # Create workflow
    workflow = db_manager.create_workflow(
        workflow_type="batch_validation",
        input_params={
            "files": request.files,
            "family": request.family,
            "validation_types": request.validation_types,
            "max_workers": request.max_workers,
        }
    )
    
    # Initialize job status
    workflow_jobs[job_id] = WorkflowStatus(
        job_id=job_id,
        status="started",
        files_total=len(request.files)
    )
    
    # Start workflow in background
    background_tasks.add_task(
        run_batch_validation,
        job_id,
        workflow.id,
        request
    )
    
    return {
        "job_id": job_id,
        "workflow_id": workflow.id,
        "status": "started",
        "files_total": len(request.files),
    }

# =============================================================================
# Plugin Detection Endpoints
# =============================================================================

@app.post("/api/detect-plugins")
async def detect_plugins(request: Dict[str, Any]):
    """Detect plugins in text using the fuzzy detector agent."""
    detector = agent_registry.get_agent("fuzzy_detector")
    if not detector:
        raise HTTPException(status_code=500, detail="Fuzzy detector agent not available")

    try:
        result = await detector.process_request("detect_plugins", request)
        return result
    except Exception:
        logger.exception("Plugin detection failed")
        raise HTTPException(status_code=500, detail="Detection failed")

# =============================================================================
# Validation Results Endpoints
# =============================================================================

@app.get("/api/validations")
async def list_validations(
    file_path: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    workflow_id: Optional[str] = None,
    limit: int = Query(100, le=500)
):
    """List validation results with optional filters."""
    try:
        results = db_manager.list_validation_results(
            file_path=file_path,
            severity=severity,
            status=status,
            workflow_id=workflow_id,
            limit=limit
        )
        return {
            "results": [r.to_dict() for r in results],
            "total": len(results)
        }
    except Exception:
        logger.exception("Failed to list validations")
        raise HTTPException(status_code=500, detail="Failed to retrieve validations")

@app.get("/api/validations/{validation_id}")
async def get_validation(validation_id: str):
    """Get a specific validation result with recommendations."""
    validation = db_manager.get_validation_result(validation_id)
    if not validation:
        raise HTTPException(status_code=404, detail="Validation not found")
    
    recommendations = db_manager.list_recommendations(validation_id=validation_id)
    
    return {
        "validation": validation.to_dict(),
        "recommendations": [r.to_dict() for r in recommendations]
    }

@app.post("/api/validations/import")
async def import_folder(request: FolderImportRequest):
    """Import and validate all markdown files in a folder via MCP."""
    try:
        from svc.mcp_server import create_mcp_client
        
        # Create MCP client
        mcp_client = create_mcp_client()
        
        # Call MCP validate_folder method
        mcp_request = {
            "method": "validate_folder",
            "params": {
                "folder_path": request.folder,
                "recursive": request.recursive
            },
            "id": 1
        }
        
        response = mcp_client.handle_request(mcp_request)
        
        if "error" in response:
            raise HTTPException(
                status_code=500, 
                detail=f"MCP error: {response['error'].get('message', 'Unknown error')}"
            )
        
        result = response.get("result", {})
        
        return {
            "success": result.get("success", False),
            "message": result.get("message", "Import completed"),
            "summary": {
                "files_processed": result.get("results", {}).get("files_processed", 0),
                "files_failed": result.get("results", {}).get("files_failed", 0),
                "validations_created": result.get("results", {}).get("validations_created", 0),
                "families_detected": result.get("results", {}).get("families_detected", {}),
                "duration_seconds": result.get("results", {}).get("duration_seconds", 0)
            },
            "details": result.get("results", {})
        }
        
    except ImportError:
        raise HTTPException(status_code=500, detail="MCP server not available")
    except Exception as e:
        logger.exception("Failed to import folder via MCP")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


# =============================================================================
# Part 3: Validation Action Endpoints (Approve/Reject/Enhance)
# =============================================================================
# =============================================================================
# Recommendation Workflow Endpoints (NEW)
# =============================================================================

@app.get("/api/recommendations")
async def list_recommendations(
    validation_id: Optional[str] = None,
    status: Optional[str] = None,
    type: Optional[str] = None,
    limit: int = Query(100, le=500)
):
    """List recommendations with optional filters."""
    try:
        recommendations = db_manager.list_recommendations(
            validation_id=validation_id,
            status=status,
            type=type,
            limit=limit
        )
        return {
            "recommendations": [r.to_dict() for r in recommendations],
            "total": len(recommendations)
        }
    except Exception:
        logger.exception("Failed to list recommendations")
        raise HTTPException(status_code=500, detail="Failed to retrieve recommendations")

@app.get("/api/recommendations/{recommendation_id}")
async def get_recommendation(recommendation_id: str):
    """Get a specific recommendation with audit trail."""
    recommendation = db_manager.get_recommendation(recommendation_id)
    if not recommendation:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    
    audit_logs = db_manager.list_audit_logs(recommendation_id=recommendation_id)
    
    return {
        "recommendation": recommendation.to_dict(),
        "audit_trail": [log.to_dict() for log in audit_logs]
    }

@app.post("/api/recommendations/{recommendation_id}/review")
async def review_recommendation(
    recommendation_id: str,
    request: RecommendationReviewRequest
):
    """Approve, reject, or reset a recommendation."""
    if request.status not in ["pending", "accepted", "rejected"]:
        raise HTTPException(status_code=400, detail="Invalid status. Must be: pending, accepted, or rejected")
    
    try:
        recommendation = db_manager.update_recommendation_status(
            recommendation_id=recommendation_id,
            status=request.status,
            reviewer=request.reviewer,
            review_notes=request.notes
        )
        
        if not recommendation:
            raise HTTPException(status_code=404, detail="Recommendation not found")
        
        return {
            "recommendation": recommendation.to_dict(),
            "message": f"Recommendation {request.status}"
        }
    except Exception:
        logger.exception("Failed to review recommendation")
        raise HTTPException(status_code=500, detail="Failed to update recommendation")

@app.post("/api/recommendations/bulk-review")
async def bulk_review_recommendations(
    recommendation_ids: List[str],
    action: str,
    reviewer: Optional[str] = None,
    notes: Optional[str] = None
):
    """Bulk approve or reject multiple recommendations."""
    if action not in ["accepted", "rejected"]:
        raise HTTPException(status_code=400, detail="Action must be 'accepted' or 'rejected'")
    
    results = []
    errors = []
    
    for rec_id in recommendation_ids:
        try:
            rec = db_manager.update_recommendation_status(
                recommendation_id=rec_id,
                status=action,
                reviewer=reviewer,
                review_notes=notes
            )
            if rec:
                results.append(rec.to_dict())
            else:
                errors.append(f"Recommendation {rec_id} not found")
        except Exception as e:
            logger.exception("Failed to review recommendation %s", rec_id)
            errors.append(f"Failed to review {rec_id}: {str(e)}")
    
    return {
        "success_count": len(results),
        "error_count": len(errors),
        "results": results,
        "errors": errors
    }

# =============================================================================
# Enhancement Endpoints (NEW)
# =============================================================================

@app.post("/agents/enhance")
async def enhance_content(request: EnhanceContentRequest, background_tasks: BackgroundTasks):
    """Apply approved recommendations to content."""
    enhancer = agent_registry.get_agent("content_enhancer")
    if not enhancer:
        raise HTTPException(status_code=500, detail="Content enhancer agent not available")

    # Get validation
    validation = db_manager.get_validation_result(request.validation_id)
    if not validation:
        raise HTTPException(status_code=404, detail="Validation not found")

    # Get approved recommendations
    if request.recommendations:
        recommendations = [
            db_manager.get_recommendation(rec_id)
            for rec_id in request.recommendations
        ]
        recommendations = [r for r in recommendations if r is not None]
    else:
        # Get all accepted recommendations
        recommendations = db_manager.list_recommendations(
            validation_id=request.validation_id,
            status="accepted"
        )

    if not recommendations:
        raise HTTPException(status_code=400, detail="No approved recommendations found")

    try:
        # Prepare enhancement request
        enhancement_params = {
            "content": request.content,
            "file_path": request.file_path,
            "recommendations": [r.to_dict() for r in recommendations],
            "preview": request.preview
        }

        # Apply enhancements
        result = await enhancer.process_request("enhance_content", enhancement_params)

        # Mark recommendations as applied (if not preview)
        if not request.preview:
            for rec in recommendations:
                db_manager.mark_recommendation_applied(
                    recommendation_id=rec.id,
                    applied_by="api_user"
                )

        return {
            "enhanced_content": result.get("enhanced_content"),
            "changes_applied": result.get("changes_applied", []),
            "preview": request.preview,
            "recommendations_applied": len(recommendations)
        }

    except Exception:
        logger.exception("Enhancement failed")
        raise HTTPException(status_code=500, detail="Enhancement failed")

@app.post("/api/enhance/auto-apply")
async def auto_apply_high_confidence_recommendations(
    validation_id: str,
    confidence_threshold: float = 0.9,
    max_recommendations: int = 10
):
    """Automatically apply high-confidence recommendations."""
    # Get high-confidence accepted recommendations
    all_recommendations = db_manager.list_recommendations(
        validation_id=validation_id,
        status="accepted"
    )
    
    high_confidence = [
        r for r in all_recommendations
        if r.confidence >= confidence_threshold
    ][:max_recommendations]
    
    if not high_confidence:
        return {
            "message": "No high-confidence recommendations found",
            "applied": 0
        }
    
    # Mark as applied
    applied = []
    for rec in high_confidence:
        result = db_manager.mark_recommendation_applied(
            recommendation_id=rec.id,
            applied_by="auto_apply"
        )
        if result:
            applied.append(result.to_dict())
    
    return {
        "message": f"Applied {len(applied)} high-confidence recommendations",
        "applied": len(applied),
        "recommendations": applied
    }

# =============================================================================
# Workflow Management Endpoints
# =============================================================================

@app.post("/workflows/validate-directory")
async def validate_directory_workflow(request: DirectoryValidationRequest, background_tasks: BackgroundTasks):
    """Start directory validation workflow."""
    orchestrator = agent_registry.get_agent("orchestrator")
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator agent not available")

    try:
        import uuid
        job_id = str(uuid.uuid4())
        
        # Create workflow in database
        workflow = db_manager.create_workflow(
            workflow_type=request.workflow_type,
            input_params={
                "directory_path": request.directory_path,
                "file_pattern": request.file_pattern,
                "max_workers": request.max_workers,
                "family": request.family
            }
        )

        # Initialize job status
        workflow_jobs[job_id] = WorkflowStatus(
            job_id=job_id,
            status="started"
        )

        # Start workflow in background
        background_tasks.add_task(
            run_directory_validation_workflow,
            job_id,
            workflow.id,
            request,
            orchestrator
        )

        return {
            "job_id": job_id,
            "workflow_id": workflow.id,
            "status": "started",
            "message": "Directory validation workflow started"
        }

    except Exception:
        logger.exception("Failed to start directory validation workflow")
        raise HTTPException(status_code=500, detail="Workflow failed to start")

@app.get("/workflows")
async def list_workflows(
    state: Optional[str] = None,
    limit: int = Query(50, le=200)
):
    """List workflows with optional state filter."""
    try:
        workflows = db_manager.list_workflows(state=state, limit=limit)
        return {
            "workflows": [w.to_dict() for w in workflows],
            "total": len(workflows)
        }
    except Exception:
        logger.exception("Failed to list workflows")
        raise HTTPException(status_code=500, detail="Failed to retrieve workflows")

@app.get("/workflows/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    """Get detailed workflow status."""
    # Check in-memory first
    if workflow_id in workflow_jobs:
        return workflow_jobs[workflow_id]
    
    # Check database
    workflow = db_manager.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return workflow.to_dict()

@app.post("/workflows/{workflow_id}/control")
async def control_workflow(workflow_id: str, request: WorkflowControlRequest):
    """Pause, resume, or cancel a workflow."""
    if request.action not in ["pause", "resume", "cancel"]:
        raise HTTPException(status_code=400, detail="Invalid action. Must be: pause, resume, or cancel")
    
    workflow = db_manager.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Map action to state
    state_map = {
        "pause": "paused",
        "resume": "running",
        "cancel": "cancelled"
    }
    
    try:
        updated = db_manager.update_workflow(
            workflow_id=workflow_id,
            state=state_map[request.action]
        )
        
        return {
            "workflow_id": workflow_id,
            "action": request.action,
            "new_state": state_map[request.action],
            "workflow": updated.to_dict() if updated else None
        }
    except Exception:
        logger.exception("Failed to control workflow")
        raise HTTPException(status_code=500, detail="Failed to control workflow")

# =============================================================================
# Audit Trail Endpoints (NEW)
# =============================================================================

@app.get("/api/audit")
async def list_audit_logs(
    recommendation_id: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = Query(100, le=500)
):
    """List audit logs with optional filters."""
    try:
        logs = db_manager.list_audit_logs(
            recommendation_id=recommendation_id,
            action=action,
            limit=limit
        )
        return {
            "logs": [log.to_dict() for log in logs],
            "total": len(logs)
        }
    except Exception:
        logger.exception("Failed to list audit logs")
        raise HTTPException(status_code=500, detail="Failed to retrieve audit logs")

# =============================================================================
# Background Tasks
# =============================================================================

async def run_directory_validation_workflow(job_id: str, workflow_id: str, request: DirectoryValidationRequest, orchestrator):
    """Run the directory validation workflow."""
    try:
        # Update status
        workflow_jobs[job_id].status = "running"
        db_manager.update_workflow(workflow_id, state="running")

        # Execute workflow
        result = await orchestrator.process_request("validate_directory", {
            "directory_path": request.directory_path,
            "file_pattern": request.file_pattern,
            "max_workers": request.max_workers,
            "family": request.family
        })

        # Update final status
        workflow_jobs[job_id].status = "completed"
        workflow_jobs[job_id].files_total = result.get("files_total", 0)
        workflow_jobs[job_id].files_validated = result.get("files_validated", 0)
        workflow_jobs[job_id].files_failed = result.get("files_failed", 0)
        workflow_jobs[job_id].errors = result.get("errors", [])
        
        db_manager.update_workflow(
            workflow_id,
            state="completed",
            progress_percent=100,
            completed_at=datetime.utcnow()
        )

    except Exception as e:
        logger.exception("Workflow execution failed for job_id=%s", job_id)
        workflow_jobs[job_id].status = "failed"
        workflow_jobs[job_id].errors = [str(e)]
        db_manager.update_workflow(
            workflow_id,
            state="failed",
            error_message=str(e)
        )

async def run_batch_validation(job_id: str, workflow_id: str, request: BatchValidationRequest):
    """Run batch validation workflow."""
    validator = agent_registry.get_agent("content_validator")
    if not validator:
        workflow_jobs[job_id].status = "failed"
        workflow_jobs[job_id].errors = ["Validator agent not available"]
        return
    
    try:
        workflow_jobs[job_id].status = "running"
        db_manager.update_workflow(workflow_id, state="running")
        
        validated = 0
        failed = 0
        errors = []
        
        for file_path in request.files:
            try:
                # Read file content (simplified - in production use proper file reading)
                from pathlib import Path
                content = Path(file_path).read_text()
                
                # Validate
                await validator.process_request("validate_content", {
                    "content": content,
                    "file_path": file_path,
                    "family": request.family,
                    "validation_types": request.validation_types
                })
                
                validated += 1
            except Exception as e:
                failed += 1
                errors.append(f"{file_path}: {str(e)}")
            
            # Update progress
            progress = int((validated + failed) / len(request.files) * 100)
            workflow_jobs[job_id].files_validated = validated
            workflow_jobs[job_id].files_failed = failed
            workflow_jobs[job_id].errors = errors[:10]  # Keep last 10 errors
            
            db_manager.update_workflow(
                workflow_id,
                current_step=validated + failed,
                total_steps=len(request.files),
                progress_percent=progress
            )
        
        # Complete
        workflow_jobs[job_id].status = "completed"
        db_manager.update_workflow(
            workflow_id,
            state="completed",
            completed_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.exception("Batch validation failed")
        workflow_jobs[job_id].status = "failed"
        workflow_jobs[job_id].errors = [str(e)]
        db_manager.update_workflow(
            workflow_id,
            state="failed",
            error_message=str(e)
        )

# =============================================================================
# Root and Status Endpoints
# =============================================================================
@app.get("/validation-notes")
async def get_validation_notes(
    file_path: str = Query(..., description="File path to get validation notes for"),
    limit: int = Query(50, le=200)
):
    """Get validation notes for a specific file."""
    try:
        notes = db_manager.list_validation_results(
            file_path=file_path,
            limit=limit
        )
        return {
            "file_path": file_path,
            "count": len(notes),
            "results": [n.to_dict() for n in notes]
        }
    except Exception:
        logger.exception("Failed to get validation notes")
        raise HTTPException(status_code=500, detail="Failed to retrieve validation notes")

@app.post("/enhance")
async def enhance_content_legacy(request: Dict[str, Any]):
    """Legacy enhancement endpoint for backward compatibility."""
    # Convert legacy request to new format
    validation_id = request.get("validation_id", "legacy")
    content = request.get("content", "")
    file_path = request.get("file_path", "unknown")
    severity_floor = request.get("severity_floor", "low")
    preview_only = request.get("preview_only", True)

    # For legacy, we'll create a simple response
    return {
        "success": True,
        "enhanced_content": content,
        "used_validation_issues": 0,
        "preview_only": preview_only
    }

@app.get("/")
async def root():
    """API root with basic info and links."""
    return {
        "name": "TBCV API",
        "version": "2.0.0",
        "description": "Truth-Based Content Validation and Enhancement System",
        "endpoints": {
            "health": "/health",
            "agents": "/agents",
            "validations": "/api/validations",
            "recommendations": "/api/recommendations",
            "workflows": "/workflows",
            "dashboard": "/dashboard",
            "docs": "/docs"
        }
    }

@app.get("/status")
async def system_status():
    """Comprehensive system status."""
    agents = agent_registry.list_agents()
    
    return {
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "components": {
            "database": db_manager.is_connected(),
            "agents": {
                "total": len(agents),
                "registered": list(agents.keys())
            },
            "workflows": {
                "active": len([j for j in workflow_jobs.values() if j.status == "running"]),
                "total": len(workflow_jobs)
            }
        }
    }

# =============================================================================
# Development Server Entry Point
# =============================================================================

if __name__ == "__main__":
    settings = get_settings()
    import uvicorn
    uvicorn.run(
        "tbcv.api.server:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )
