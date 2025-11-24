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
from datetime import datetime, timezone
from importlib import resources as ilres
import uuid

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Query, Response, status, WebSocket

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
    from agents.llm_validator import LLMValidatorAgent
    from agents.recommendation_agent import RecommendationAgent
    from agents.validators.seo_validator import SeoValidatorAgent
    from agents.validators.yaml_validator import YamlValidatorAgent
    from agents.validators.markdown_validator import MarkdownValidatorAgent
    from agents.validators.code_validator import CodeValidatorAgent
    from agents.validators.link_validator import LinkValidatorAgent
    from agents.validators.structure_validator import StructureValidatorAgent
    from agents.validators.truth_validator import TruthValidatorAgent
except ImportError:
    from agents.base import agent_registry
    from agents.truth_manager import TruthManagerAgent
    from agents.fuzzy_detector import FuzzyDetectorAgent
    from agents.content_validator import ContentValidatorAgent
    from agents.content_enhancer import ContentEnhancerAgent
    from agents.code_analyzer import CodeAnalyzerAgent
    from agents.orchestrator import OrchestratorAgent
    from agents.llm_validator import LLMValidatorAgent
    from agents.recommendation_agent import RecommendationAgent
    from agents.validators.seo_validator import SeoValidatorAgent
    from agents.validators.yaml_validator import YamlValidatorAgent
    from agents.validators.markdown_validator import MarkdownValidatorAgent
    from agents.validators.code_validator import CodeValidatorAgent
    from agents.validators.link_validator import LinkValidatorAgent
    from agents.validators.structure_validator import StructureValidatorAgent
    from agents.validators.truth_validator import TruthValidatorAgent

try:
    from core.config import get_settings
    from core.logging import setup_logging, get_logger
    from core.database import db_manager, WorkflowState, RecommendationStatus, ValidationResult
    from core.cache import cache_manager
    from core.language_utils import validate_english_content_batch, is_english_content, log_language_rejection
except ImportError:
    from core.config import get_settings
    from core.logging import setup_logging, get_logger
    from core.database import db_manager, WorkflowState, RecommendationStatus, ValidationResult
    from core.cache import cache_manager
    from core.language_utils import validate_english_content_batch, is_english_content, log_language_rejection

logger = get_logger(__name__)

# =============================================================================
# Global Server State
# =============================================================================

import time
SERVER_START_TIME = time.time()
MAINTENANCE_MODE = False

# =============================================================================
# Pydantic Models for API
# =============================================================================

class ContentValidationRequest(BaseModel):
    content: str
    file_path: str = "unknown"
    family: str = "words"
    validation_types: List[str] = ["yaml", "markdown", "code", "links", "structure", "Truth", "FuzzyLogic"]

class DirectoryValidationRequest(BaseModel):
    directory_path: str
    file_pattern: str = "*.md"
    workflow_type: str = "validate_file"
    max_workers: int = 4
    family: str = "words"

class FileContent(BaseModel):
    file_path: str
    content: str

class BatchValidationRequest(BaseModel):
    files: List[str] = Field(description="List of file paths to validate")
    family: str = "words"
    validation_types: List[str] = ["yaml", "markdown", "code", "links", "structure", "Truth", "FuzzyLogic"]
    max_workers: int = 4
    upload_mode: bool = Field(False, description="True if files are uploaded from client, False if server-side paths")
    file_contents: Optional[List[FileContent]] = Field(None, description="File contents when upload_mode is True")

class EnhanceContentRequest(BaseModel):
    validation_id: str = Field(description="Validation result ID to enhance from")
    file_path: str
    content: str
    recommendations: Optional[List[str]] = Field(None, description="Specific recommendation IDs to apply")
    preview: bool = Field(False, description="Preview changes without applying")

class BatchEnhanceRequest(BaseModel):
    validation_ids: List[str] = Field(description="List of validation IDs to enhance")
    parallel: bool = Field(True, description="Process in parallel (True) or sequentially (False)")
    persist: bool = Field(True, description="Persist results to database")
    require_recommendations: Optional[bool] = Field(None, description="Override for requiring recommendations")
    min_recommendations: Optional[int] = Field(None, description="Override for minimum recommendations required")
    apply_all: bool = Field(True, description="Apply all approved recommendations per validation")
    recommendation_ids_per_validation: Optional[Dict[str, List[str]]] = Field(
        None,
        description="Optional dict mapping validation_id to list of specific recommendation IDs to apply"
    )

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

    # Start live bus for real-time updates
    try:
        from api.services.live_bus import start_live_bus
        await start_live_bus()
        logger.info("Live bus started")
    except Exception:
        logger.exception("Failed to start live bus")

    # Register agents
    await register_agents()

    try:
        yield
    finally:
        # Shutdown
        logger.info("Shutting down TBCV API server")
        
        # Stop live bus
        try:
            from api.services.live_bus import stop_live_bus
            await stop_live_bus()
            logger.info("Live bus stopped")
        except Exception:
            logger.exception("Failed to stop live bus")
        
        agent_registry.clear()

async def register_agents():
    """Register all agents with the agent registry."""
    from core.config import get_settings
    try:
        settings = get_settings()

        # Create & register core agents
        truth_manager = TruthManagerAgent("truth_manager")
        agent_registry.register_agent(truth_manager)

        if getattr(settings.fuzzy_detector, "enabled", True):
            fuzzy_detector = FuzzyDetectorAgent("fuzzy_detector")
            agent_registry.register_agent(fuzzy_detector)
        else:
            logger.info("Fuzzy detector disabled via config")

        content_validator = ContentValidatorAgent("content_validator")
        agent_registry.register_agent(content_validator)

        content_enhancer = ContentEnhancerAgent("content_enhancer")
        agent_registry.register_agent(content_enhancer)

        llm_validator = LLMValidatorAgent("llm_validator")
        agent_registry.register_agent(llm_validator)

        code_analyzer = CodeAnalyzerAgent("code_analyzer")
        agent_registry.register_agent(code_analyzer)

        orchestrator = OrchestratorAgent("orchestrator")
        agent_registry.register_agent(orchestrator)

        recommendation_agent = RecommendationAgent("recommendation_agent")
        agent_registry.register_agent(recommendation_agent)

        # Enhancement agent - applies approved recommendations
        from agents.enhancement_agent import EnhancementAgent
        enhancement_agent = EnhancementAgent("enhancement_agent")
        agent_registry.register_agent(enhancement_agent)

        # New validator agents (Phase 1 & 2)
        if getattr(settings.validators.seo, "enabled", True):
            seo_validator = SeoValidatorAgent("seo_validator")
            agent_registry.register_agent(seo_validator)
            logger.info("SEO validator registered")

        if getattr(settings.validators.yaml, "enabled", True):
            yaml_validator = YamlValidatorAgent("yaml_validator")
            agent_registry.register_agent(yaml_validator)
            logger.info("YAML validator registered")

        if getattr(settings.validators.markdown, "enabled", True):
            markdown_validator = MarkdownValidatorAgent("markdown_validator")
            agent_registry.register_agent(markdown_validator)
            logger.info("Markdown validator registered")

        if getattr(settings.validators.code, "enabled", True):
            code_validator = CodeValidatorAgent("code_validator")
            agent_registry.register_agent(code_validator)
            logger.info("Code validator registered")

        if getattr(settings.validators.links, "enabled", True):
            link_validator = LinkValidatorAgent("link_validator")
            agent_registry.register_agent(link_validator)
            logger.info("Link validator registered")

        if getattr(settings.validators.structure, "enabled", True):
            structure_validator = StructureValidatorAgent("structure_validator")
            agent_registry.register_agent(structure_validator)
            logger.info("Structure validator registered")

        if getattr(settings.validators.truth, "enabled", True):
            truth_validator = TruthValidatorAgent("truth_validator")
            agent_registry.register_agent(truth_validator)
            logger.info("Truth validator registered")

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


# Custom OpenAPI schema to rename ugly auto-generated form schemas
def custom_openapi():
    """Custom OpenAPI schema generator that renames ugly auto-generated form schemas."""
    if app.openapi_schema:
        return app.openapi_schema

    from fastapi.openapi.utils import get_openapi

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Rename ugly auto-generated schemas to professional names
    schemas = openapi_schema.get("components", {}).get("schemas", {})
    schema_renames = {
        "Body_dashboard_review_recommendation_dashboard_recommendations__recommendation_id__review_post": "DashboardReviewForm",
        "Body_dashboard_bulk_review_dashboard_recommendations_bulk_review_post": "DashboardBulkReviewForm"
    }

    # Rename schemas
    for old_name, new_name in schema_renames.items():
        if old_name in schemas:
            schemas[new_name] = schemas.pop(old_name)

    # Update all references to renamed schemas
    import json
    schema_str = json.dumps(openapi_schema)
    for old_name, new_name in schema_renames.items():
        schema_str = schema_str.replace(f'"$ref": "#/components/schemas/{old_name}"', f'"$ref": "#/components/schemas/{new_name}"')
    openapi_schema = json.loads(schema_str)

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# NOTE: CORS middleware moved to AFTER WebSocket routes to avoid 403 errors
# WebSockets don't use CORS the same way as HTTP requests
# The middleware will be added later in the file

# Include dashboard router if available
try:
    from api.dashboard import router as dashboard_router
    app.include_router(dashboard_router)
except Exception:
    pass

# Include additional endpoints
try:
    from api.additional_endpoints import router as additional_router
    app.include_router(additional_router)
except Exception:
    logger.exception("Failed to include additional endpoints")
    pass


# Root API index endpoint
@app.get("/")
async def api_root(request: Request):
    """
    Root endpoint that provides an index of available API endpoints.
    Returns JSON by default, or HTML for browser requests.
    """
    base_url = str(request.base_url).rstrip("/")
    
    endpoints = {
        "health": {
            "name": "Health Check",
            "url": f"{base_url}/health",
            "description": "System health status with database connectivity"
        },
        "health_ready": {
            "name": "Readiness Check",
            "url": f"{base_url}/health/ready",
            "description": "Check if system is ready to accept requests"
        },
        "health_live": {
            "name": "Liveness Check",
            "url": f"{base_url}/health/live",
            "description": "Check if system is alive"
        },
        "agents": {
            "name": "List Agents",
            "url": f"{base_url}/agents",
            "description": "List all available agents"
        },
        "agent_registry": {
            "name": "Agent Registry",
            "url": f"{base_url}/registry/agents",
            "description": "Get registered agents and their contracts"
        },
        "validations": {
            "name": "List Validations",
            "url": f"{base_url}/api/validations",
            "description": "List validation results with filtering"
        },
        "recommendations": {
            "name": "List Recommendations",
            "url": f"{base_url}/api/recommendations",
            "description": "List recommendations with filtering"
        },
        "workflows": {
            "name": "List Workflows",
            "url": f"{base_url}/api/workflows",
            "description": "List workflow runs with statistics"
        },
        "dashboard": {
            "name": "Dashboard Home",
            "url": f"{base_url}/dashboard",
            "description": "Web UI for managing validations and recommendations"
        },
        "dashboard_validations": {
            "name": "Dashboard Validations",
            "url": f"{base_url}/dashboard/validations",
            "description": "Browse validations in web UI"
        },
        "dashboard_recommendations": {
            "name": "Dashboard Recommendations",
            "url": f"{base_url}/dashboard/recommendations",
            "description": "Browse and manage recommendations in web UI"
        },
        "dashboard_workflows": {
            "name": "Dashboard Workflows",
            "url": f"{base_url}/dashboard/workflows",
            "description": "View workflow history and statistics in web UI"
        },
        "docs": {
            "name": "API Documentation",
            "url": f"{base_url}/docs",
            "description": "Interactive API documentation (Swagger UI)"
        },
        "redoc": {
            "name": "API Documentation (ReDoc)",
            "url": f"{base_url}/redoc",
            "description": "Alternative API documentation"
        }
    }
    
    # Check if request is from a browser
    accept_header = request.headers.get("accept", "")
    if "text/html" in accept_header:
        # Return HTML for browsers
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>TBCV API</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 1200px; margin: 50px auto; padding: 20px; background: #f5f5f5; }
                h1 { color: #333; border-bottom: 3px solid #0066cc; padding-bottom: 10px; }
                .intro { margin: 20px 0; color: #666; }
                .endpoint { margin: 15px 0; padding: 15px; background: white; border-left: 4px solid #0066cc; border-radius: 3px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .endpoint h3 { margin-top: 0; color: #0066cc; font-size: 16px; }
                .endpoint a { color: #0066cc; text-decoration: none; font-family: monospace; }
                .endpoint a:hover { text-decoration: underline; }
                .description { color: #666; margin-top: 8px; font-size: 14px; }
                .category { margin-top: 30px; }
                .category h2 { color: #555; font-size: 18px; margin-bottom: 15px; }
            </style>
        </head>
        <body>
            <h1>TBCV API - Truth-Based Content Validation System</h1>
            <div class="intro">
                <p>Welcome to the TBCV API. This system provides comprehensive content validation, recommendation generation, and enhancement capabilities.</p>
            </div>
            
            <div class="category">
                <h2>System Status</h2>
        """
        
        # Add health endpoints
        for key in ["health", "health_ready", "health_live"]:
            endpoint = endpoints[key]
            html_content += f"""
                <div class="endpoint">
                    <h3>{endpoint['name']}</h3>
                    <a href="{endpoint['url']}">{endpoint['url']}</a>
                    <div class="description">{endpoint['description']}</div>
                </div>
            """
        
        html_content += """
            </div>
            <div class="category">
                <h2>Agents</h2>
        """
        
        for key in ["agents", "agent_registry"]:
            endpoint = endpoints[key]
            html_content += f"""
                <div class="endpoint">
                    <h3>{endpoint['name']}</h3>
                    <a href="{endpoint['url']}">{endpoint['url']}</a>
                    <div class="description">{endpoint['description']}</div>
                </div>
            """
        
        html_content += """
            </div>
            <div class="category">
                <h2>API Endpoints</h2>
        """
        
        for key in ["validations", "recommendations", "workflows"]:
            endpoint = endpoints[key]
            html_content += f"""
                <div class="endpoint">
                    <h3>{endpoint['name']}</h3>
                    <a href="{endpoint['url']}">{endpoint['url']}</a>
                    <div class="description">{endpoint['description']}</div>
                </div>
            """
        
        html_content += """
            </div>
            <div class="category">
                <h2>Dashboard (Web UI)</h2>
        """
        
        for key in ["dashboard", "dashboard_validations", "dashboard_recommendations", "dashboard_workflows"]:
            endpoint = endpoints[key]
            html_content += f"""
                <div class="endpoint">
                    <h3>{endpoint['name']}</h3>
                    <a href="{endpoint['url']}">{endpoint['url']}</a>
                    <div class="description">{endpoint['description']}</div>
                </div>
            """
        
        html_content += """
            </div>
            <div class="category">
                <h2>Documentation</h2>
        """
        
        for key in ["docs", "redoc"]:
            endpoint = endpoints[key]
            html_content += f"""
                <div class="endpoint">
                    <h3>{endpoint['name']}</h3>
                    <a href="{endpoint['url']}">{endpoint['url']}</a>
                    <div class="description">{endpoint['description']}</div>
                </div>
            """
        
        html_content += """
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
    else:
        # Return JSON for API clients
        return {
            "name": "TBCV API",
            "version": "2.0.0",
            "description": "Truth-Based Content Validation and Enhancement System",
            "endpoints": endpoints
        }


# Test minimal WebSocket endpoint
@app.websocket("/ws/test")
async def test_websocket(websocket: WebSocket):
    """Minimal test WebSocket endpoint."""
    await websocket.accept()
    await websocket.send_text("Hello from test WebSocket!")
    await websocket.close()

# WebSocket endpoint for live updates
@app.websocket("/ws/{workflow_id}")
async def websocket_endpoint(websocket: WebSocket, workflow_id: str):
    """WebSocket endpoint for real-time updates."""
    from api.websocket_endpoints import websocket_endpoint as ws_handler
    await ws_handler(websocket, workflow_id)

# WebSocket endpoint for global validation updates
@app.websocket("/ws/validation_updates")
async def validation_updates_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for global validation updates.
    This provides a broadcast channel for all validation events.
    """
    from api.websocket_endpoints import websocket_endpoint as ws_handler
    await ws_handler(websocket, "validation_updates")


# Add CORS middleware AFTER WebSocket routes to avoid conflicts
# Note: WebSocket connections use HTTP origins, not ws:// origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)


# SSE endpoint for live updates
@app.get("/api/stream/updates")
async def stream_updates(request: Request, topic: Optional[str] = Query(None)):
    """
    Server-Sent Events endpoint for live updates.
    Supports filtering by topic.
    """
    from fastapi.responses import StreamingResponse
    from api.services.live_bus import get_live_bus
    import json
    
    async def event_generator():
        live_bus = get_live_bus()
        queue = live_bus.subscribe(topic)
        
        try:
            # Send initial connection event
            yield f"data: {json.dumps({'type': 'connected', 'topic': topic})}\n\n"
            
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break
                
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(message)}\n\n"
                except asyncio.TimeoutError:
                    # Send heartbeat
                    yield f": heartbeat\n\n"
                except Exception as e:
                    logger.error(f"Error in SSE stream: {e}")
                    break
                    
        finally:
            live_bus.unsubscribe(queue, topic)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable buffering in nginx
        }
    )


# Setup templates for dashboard
templates = Jinja2Templates(directory="templates")

# =============================================================================
# Health Check Endpoints
# =============================================================================

@app.get("/health")
async def health_check(response: Response):
    """Comprehensive health check endpoint (DB REQUIRED with schema check)."""
    database_connected = False
    schema_present = False
    
    try:
        database_connected = db_manager.is_connected()
        if database_connected:
            schema_present = db_manager.has_required_schema()
    except Exception:
        database_connected = False
        schema_present = False

    # Enforce DB-required readiness: return 503 until DB is reachable AND schema is present
    healthy = database_connected and schema_present
    if not healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "healthy" if healthy else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agents_registered": len(agent_registry.list_agents()),
        "database_connected": database_connected,
        "schema_present": schema_present,
        "version": "2.0.0",
    }
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
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agents_registered": len(agent_registry.list_agents()),
        "database_connected": database_connected,
        "version": "2.0.0",
    }


@app.get("/health/live")
async def health_live():
    """Kubernetes liveness probe - is the application running?"""
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

@app.get("/health/ready")
async def readiness_check(response: Response):
    """Kubernetes readiness probe (DB & agents & schema REQUIRED)."""
    checks = {
        "database": False,
        "schema": False,
        "agents": False
    }
    try:
        checks["database"] = db_manager.is_connected()
        if checks["database"]:
            checks["schema"] = db_manager.has_required_schema()
    except Exception:
        checks["database"] = False
        checks["schema"] = False

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
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
    }
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
        "timestamp": datetime.now(timezone.utc).isoformat(),
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

def _determine_severity(validation_result: Dict[str, Any]) -> str:
    """
    Determine severity level from validation result.
    """
    # Check for issues in final_issues
    issues = validation_result.get("final_issues", [])
    if not issues:
        # Check in content_validation
        content_val = validation_result.get("content_validation", {})
        issues = content_val.get("issues", [])

    # Count issue levels
    critical = sum(1 for issue in issues if issue.get("level", "").lower() == "critical")
    errors = sum(1 for issue in issues if issue.get("level", "").lower() == "error")
    warnings = sum(1 for issue in issues if issue.get("level", "").lower() == "warning")

    if critical > 0:
        return "critical"
    elif errors > 0:
        return "high"
    elif warnings > 0:
        return "medium"
    else:
        return "info"


def _determine_status(validation_result: Dict[str, Any]) -> str:
    """
    Determine validation status from result.
    """
    # Check for issues in final_issues
    issues = validation_result.get("final_issues", [])
    if not issues:
        # Check in content_validation
        content_val = validation_result.get("content_validation", {})
        issues = content_val.get("issues", [])

    # Count issue levels
    critical = sum(1 for issue in issues if issue.get("level", "").lower() == "critical")
    errors = sum(1 for issue in issues if issue.get("level", "").lower() == "error")
    warnings = sum(1 for issue in issues if issue.get("level", "").lower() == "warning")

    if critical > 0 or errors > 0:
        return "fail"
    elif warnings > 0:
        return "warning"
    else:
        return "pass"


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

@app.post("/api/validate")
async def validate_content_api(request: ContentValidationRequest):
    """
    Validate content using the full orchestrator pipeline.
    This includes fuzzy detection, content validation, and LLM validation.
    """
    orchestrator = agent_registry.get_agent("orchestrator")
    if not orchestrator:
        # Fallback to content_validator only if orchestrator not available
        logger.warning("Orchestrator not available, falling back to content_validator only")
        return await validate_content(request)

    try:
        # Save content to temporary file for orchestrator
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as tmp:
            tmp.write(request.content)
            tmp_path = tmp.name

        try:
            # Use orchestrator for full validation pipeline (fuzzy + LLM + content)
            result = await orchestrator.process_request("validate_file", {
                "file_path": tmp_path,
                "family": request.family,
                "validation_types": request.validation_types
            })

            # Update file_path in result to use the original request file_path
            if isinstance(result, dict):
                result["file_path"] = request.file_path

            # Store validation result to database
            validation_result = db_manager.create_validation_result(
                file_path=request.file_path,
                rules_applied=result.get("validation_types", request.validation_types),
                validation_results=result,
                notes=f"Validation completed via API",
                severity=_determine_severity(result),
                status=_determine_status(result),
                content=request.content,
                validation_types=request.validation_types
            )

            # Add validation ID to response
            result["id"] = validation_result.id
            result["validation_id"] = validation_result.id

            # Publish validation update
            try:
                from api.services.live_bus import get_live_bus
                live_bus = get_live_bus()
                await live_bus.publish_validation_update(
                    validation_result.id,
                    "validation_created",
                    {"file_path": request.file_path, "status": result.get("status", "completed")}
                )
            except Exception as e:
                logger.warning(f"Failed to publish validation update: {e}")

            return result

        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    except Exception:
        logger.exception("Validation failed")
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

@app.get("/api/validations/{validation_id}/report")
async def get_validation_report(validation_id: str):
    """Get a comprehensive report for a validation including issues and recommendations."""
    try:
        report = db_manager.generate_validation_report(validation_id)
        return report
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        logger.exception("Failed to generate validation report")
        raise HTTPException(status_code=500, detail="Failed to generate validation report")


@app.get("/api/validations/history/{file_path:path}")
async def get_validation_history(
    file_path: str,
    limit: Optional[int] = Query(None, description="Maximum number of historical records"),
    include_trends: bool = Query(True, description="Include trend analysis")
):
    """
    Get validation history for a file path with optional trend analysis.

    Returns all validation records for the specified file path, ordered from
    newest to oldest, with trend analysis showing improvement or degradation over time.
    """
    try:
        history = db_manager.get_validation_history(
            file_path=file_path,
            limit=limit,
            include_trends=include_trends
        )

        if history["total_validations"] == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No validation history found for file: {file_path}"
            )

        return history

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get validation history for {file_path}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve validation history: {str(e)}"
        )


@app.post("/api/validations/{original_id}/revalidate")
async def revalidate_content(original_id: str, enhanced_content: str, compare: bool = True):
    """
    Re-validate enhanced content and optionally compare with original validation.

    Args:
        original_id: ID of the original validation
        enhanced_content: The enhanced/modified content to validate
        compare: Whether to compare results with original validation

    Returns:
        Dict with new validation ID and optional comparison data
    """
    try:
        # Get original validation to know the file path and family
        original = db_manager.get_validation_result(original_id)
        if not original:
            raise HTTPException(status_code=404, detail=f"Original validation {original_id} not found")

        # Get content validator
        validator = agent_registry.get_agent("content_validator")
        if not validator:
            raise HTTPException(status_code=500, detail="Content validator not available")

        # Run validation on enhanced content (use same validation types as original if available)
        validation_types = original.validation_types if original.validation_types else [
            "yaml", "markdown", "code", "links", "structure", "Truth", "FuzzyLogic"
        ]

        result = await validator.process_request("validate_content", {
            "content": enhanced_content,
            "file_path": original.file_path,
            "family": "words",  # Could extract from original
            "validation_types": validation_types
        })

        # Get the new validation ID (it was just created)
        # For simplicity, find the most recent validation for this file
        recent_validations = db_manager.list_validation_results(
            file_path=original.file_path,
            limit=1
        )

        if not recent_validations:
            raise HTTPException(status_code=500, detail="New validation not found after creation")

        new_validation = recent_validations[0]
        new_validation_id = new_validation.id

        # Update new validation to reference the original
        with db_manager.get_session() as session:
            new_val = session.query(ValidationResult).filter_by(id=new_validation_id).first()
            if new_val:
                new_val.parent_validation_id = original_id
                session.commit()

        response = {
            "new_validation_id": new_validation_id,
            "original_validation_id": original_id,
            "success": True
        }

        # Compare if requested
        if compare:
            comparison = db_manager.compare_validations(original_id, new_validation_id)

            # Store comparison data in new validation
            with db_manager.get_session() as session:
                new_val = session.query(ValidationResult).filter_by(id=new_validation_id).first()
                if new_val:
                    new_val.comparison_data = comparison
                    session.commit()

            response["comparison"] = comparison

        return response

    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to revalidate content")
        raise HTTPException(status_code=500, detail="Re-validation failed")

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
# Dashboard Support Endpoints
# =============================================================================

@app.get("/api/files/read")
async def read_file_content(path: str = Query(..., description="File path to read")):
    """
    Read file content from disk for dashboard enhancement feature.

    Args:
        path: Absolute or relative file path

    Returns:
        Dict with file content and metadata
    """
    try:
        from pathlib import Path

        file_path = Path(path)

        # Security check: ensure file exists and is a file
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {path}")

        if not file_path.is_file():
            raise HTTPException(status_code=400, detail=f"Path is not a file: {path}")

        # Read file content
        try:
            content = file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            # Try with different encoding
            content = file_path.read_text(encoding='latin-1')

        # Get file metadata
        stat = file_path.stat()

        return {
            "success": True,
            "file_path": str(file_path.absolute()),
            "content": content,
            "size_bytes": stat.st_size,
            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "encoding": "utf-8"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to read file: {path}")
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")


@app.get("/api/validators/available")
async def get_available_validators():
    """
    Get list of all available validator agents.

    Returns information about which validators are available in the system,
    including both new modular validators and legacy validators.

    Returns:
        Dict containing list of validators with their metadata
    """
    try:
        # Get orchestrator to access validator router
        orchestrator = agent_registry.get_agent("orchestrator")
        if not orchestrator or not hasattr(orchestrator, "validator_router"):
            # Fallback: Create minimal list from agent registry
            validators = []
            validator_definitions = [
                {"id": "yaml", "label": "YAML", "description": "Validate YAML frontmatter", "category": "standard"},
                {"id": "markdown", "label": "Markdown", "description": "Validate Markdown syntax", "category": "standard"},
                {"id": "code", "label": "Code", "description": "Validate code blocks", "category": "standard"},
                {"id": "links", "label": "Links", "description": "Check link validity", "category": "standard"},
                {"id": "structure", "label": "Structure", "description": "Validate document structure", "category": "standard"},
                {"id": "Truth", "label": "Truth", "description": "Validate against truth data", "category": "standard"},
                {"id": "FuzzyLogic", "label": "Fuzzy Logic", "description": "Fuzzy plugin detection", "category": "standard"},
                {"id": "seo", "label": "SEO Headings", "description": "Validate SEO-friendly heading structure", "category": "advanced"},
                {"id": "heading_sizes", "label": "Heading Sizes", "description": "Validate heading length limits", "category": "advanced"},
                {"id": "llm", "label": "LLM Analysis", "description": "Semantic validation via LLM", "category": "advanced"}
            ]

            for val_def in validator_definitions:
                validators.append({
                    **val_def,
                    "available": True,  # Assume available via legacy
                    "enabled_by_default": val_def["category"] == "standard"
                })

            return {"validators": validators}

        # Use validator router's method
        validators = orchestrator.validator_router.get_available_validators()
        return {"validators": validators}

    except Exception as e:
        logger.exception("Failed to get available validators")
        raise HTTPException(status_code=500, detail=f"Failed to get validators: {str(e)}")


@app.get("/api/stats")
async def get_dashboard_stats():
    """
    Get dashboard statistics for real-time metrics.

    Returns:
        Dict with current system statistics
    """
    try:
        # Get all validations count
        all_validations = db_manager.list_validation_results(limit=10000)
        total_validations = len(all_validations)

        # Get all recommendations and calculate stats
        all_recommendations = db_manager.list_recommendations(limit=10000)
        total_recommendations = len(all_recommendations)

        # Count by status
        pending_count = len([r for r in all_recommendations if r.status.value == "pending"])
        accepted_count = len([r for r in all_recommendations if r.status.value in ["accepted", "approved"]])
        rejected_count = len([r for r in all_recommendations if r.status.value == "rejected"])
        applied_count = len([r for r in all_recommendations if r.status.value == "applied"])

        # Get recent activity (last 24 hours)
        from datetime import timedelta
        recent_cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        recent_validations = [v for v in all_validations if v.created_at and v.created_at > recent_cutoff]

        return {
            "success": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_validations": total_validations,
            "total_recommendations": total_recommendations,
            "pending_recommendations": pending_count,
            "accepted_recommendations": accepted_count,
            "rejected_recommendations": rejected_count,
            "applied_recommendations": applied_count,
            "recent_validations_24h": len(recent_validations),
            "database_connected": db_manager.is_connected()
        }

    except Exception as e:
        logger.exception("Failed to get dashboard stats")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@app.get("/api/validations/{validation_id}/diff")
async def get_validation_diff(validation_id: str):
    """
    Get the content diff for an enhanced validation.

    Args:
        validation_id: Validation result ID

    Returns:
        Dict with diff information
    """
    try:
        # Get validation
        validation = db_manager.get_validation_result(validation_id)
        if not validation:
            raise HTTPException(status_code=404, detail="Validation not found")

        # Check if validation has enhancement data
        if not validation.validation_results or not isinstance(validation.validation_results, dict):
            raise HTTPException(status_code=404, detail="No validation results found")

        results = validation.validation_results

        # Look for diff in validation_results metadata
        diff = results.get("diff")
        original_content = results.get("original_content")
        enhanced_content = results.get("enhanced_content")

        # If diff not stored, try to generate it from original and enhanced content
        if not diff and original_content and enhanced_content:
            import difflib

            original_lines = original_content.splitlines(keepends=True)
            enhanced_lines = enhanced_content.splitlines(keepends=True)

            diff_gen = difflib.unified_diff(
                original_lines,
                enhanced_lines,
                fromfile='Original',
                tofile='Enhanced',
                lineterm=''
            )

            diff = '\n'.join(diff_gen)

        # If still no diff, check if file exists and compare with current
        if not diff and validation.file_path:
            try:
                from pathlib import Path
                file_path = Path(validation.file_path)

                if file_path.exists():
                    current_content = file_path.read_text(encoding='utf-8')

                    # Use original content if available, otherwise current is the enhanced
                    if original_content:
                        import difflib
                        original_lines = original_content.splitlines(keepends=True)
                        current_lines = current_content.splitlines(keepends=True)

                        diff_gen = difflib.unified_diff(
                            original_lines,
                            current_lines,
                            fromfile='Original',
                            tofile='Current',
                            lineterm=''
                        )

                        diff = '\n'.join(diff_gen)
            except Exception:
                pass  # Fail silently if file reading fails

        if not diff:
            raise HTTPException(
                status_code=404,
                detail="No diff available - validation may not have been enhanced yet"
            )

        return {
            "success": True,
            "validation_id": validation_id,
            "diff": diff,
            "has_original": bool(original_content),
            "has_enhanced": bool(enhanced_content),
            "file_path": validation.file_path
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get diff for validation {validation_id}")
        raise HTTPException(status_code=500, detail=f"Failed to get diff: {str(e)}")


@app.get("/api/validations/{validation_id}/enhancement-comparison")
async def get_enhancement_comparison(validation_id: str):
    """
    Get comprehensive enhancement comparison data for side-by-side viewing.

    This endpoint provides detailed before/after comparison including:
    - Original and enhanced content
    - Line-by-line diff with change markers
    - Statistics (lines added/removed/modified)
    - Applied recommendations
    - Unified diff

    Args:
        validation_id: Validation result ID

    Returns:
        Dict with comprehensive comparison data

    Raises:
        HTTPException: If validation not found or error occurs
    """
    try:
        from api.services.enhancement_comparison import get_enhancement_comparison_service

        service = get_enhancement_comparison_service()
        comparison = await service.get_enhancement_comparison(validation_id)

        if comparison.status == "error":
            raise HTTPException(
                status_code=500,
                detail=f"Error generating comparison: {comparison.error_message}"
            )

        # Convert dataclass to dict for JSON response
        return {
            "success": True,
            "validation_id": comparison.validation_id,
            "file_path": comparison.file_path,
            "original_content": comparison.original_content,
            "enhanced_content": comparison.enhanced_content,
            "diff_lines": comparison.diff_lines,
            "stats": comparison.stats,
            "applied_recommendations": comparison.applied_recommendations,
            "unified_diff": comparison.unified_diff,
            "status": comparison.status
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error getting enhancement comparison")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get enhancement comparison: {str(e)}"
        )


# =============================================================================
# Part 3: Validation Action Endpoints (Approve/Reject/Enhance)
# =============================================================================

@app.post("/api/validations/{validation_id}/approve")
async def approve_validation(validation_id: str):
    """Approve a single validation record via MCP."""
    try:
        from svc.mcp_server import create_mcp_client
        from api.websocket_endpoints import connection_manager
        
        # Create MCP client
        mcp_client = create_mcp_client()
        
        # Call MCP approve method
        mcp_request = {
            "method": "approve",
            "params": {
                "ids": [validation_id]
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
        
        # Notify WebSocket clients about the status change
        await connection_manager.send_progress_update("validation_updates", {
            "type": "validation_approved",
            "validation_id": validation_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {
            "success": result.get("success", False),
            "message": f"Validation {validation_id} approved",
            "approved_count": result.get("approved_count", 0),
            "errors": result.get("errors", [])
        }
        
    except ImportError:
        raise HTTPException(status_code=500, detail="MCP server not available")
    except Exception as e:
        logger.exception("Failed to approve validation")
        raise HTTPException(status_code=500, detail=f"Approval failed: {str(e)}")

@app.post("/api/validations/{validation_id}/reject")
async def reject_validation(validation_id: str):
    """Reject a single validation record via MCP."""
    try:
        from svc.mcp_server import create_mcp_client
        from api.websocket_endpoints import connection_manager
        
        # Create MCP client
        mcp_client = create_mcp_client()
        
        # Call MCP reject method
        mcp_request = {
            "method": "reject",
            "params": {
                "ids": [validation_id]
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
        
        # Notify WebSocket clients about the status change
        await connection_manager.send_progress_update("validation_updates", {
            "type": "validation_rejected",
            "validation_id": validation_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {
            "success": result.get("success", False),
            "message": f"Validation {validation_id} rejected",
            "rejected_count": result.get("rejected_count", 0),
            "errors": result.get("errors", [])
        }
        
    except ImportError:
        raise HTTPException(status_code=500, detail="MCP server not available")
    except Exception as e:
        logger.exception("Failed to reject validation")
        raise HTTPException(status_code=500, detail=f"Rejection failed: {str(e)}")

@app.post("/api/enhance/{validation_id}")
async def enhance_validation(validation_id: str):
    """Enhance a single approved validation record via MCP."""
    try:
        from svc.mcp_server import create_mcp_client
        from api.websocket_endpoints import connection_manager
        
        # Create MCP client
        mcp_client = create_mcp_client()
        
        # Call MCP enhance method
        mcp_request = {
            "method": "enhance",
            "params": {
                "ids": [validation_id]
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
        
        # Notify WebSocket clients about the enhancement
        await connection_manager.send_progress_update("validation_updates", {
            "type": "validation_enhanced",
            "validation_id": validation_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "enhanced_count": result.get("enhanced_count", 0)
        })
        
        return {
            "success": result.get("success", False),
            "message": f"Validation {validation_id} enhanced",
            "enhanced_count": result.get("enhanced_count", 0),
            "errors": result.get("errors", []),
            "enhancements": result.get("enhancements", [])
        }
        
    except ImportError:
        raise HTTPException(status_code=500, detail="MCP server not available")
    except Exception as e:
        logger.exception("Failed to enhance validation")
        raise HTTPException(status_code=500, detail=f"Enhancement failed: {str(e)}")


@app.post("/api/enhance")
async def enhance_content_with_recommendations(request: EnhanceContentRequest):
    """
    Enhance content using approved recommendations via MCP.

    This endpoint applies approved recommendations to content, producing:
    - Enhanced content
    - Structured diff
    - Per-recommendation result (applied or skipped with reason)
    - Marks applied recommendations as 'actioned'
    """
    try:
        from svc.mcp_server import create_mcp_client

        # Get validation and its recommendations
        validation = db_manager.get_validation_result(request.validation_id)
        if not validation:
            raise HTTPException(status_code=404, detail="Validation not found")

        # Create MCP client and call enhance
        mcp_client = create_mcp_client()
        mcp_request = {
            "method": "enhance",
            "params": {
                "ids": [request.validation_id]
            },
            "id": 1
        }

        response = mcp_client.handle_request(mcp_request)

        if "error" in response:
            raise HTTPException(
                status_code=500,
                detail=f"Enhancement failed: {response['error'].get('message', 'Unknown error')}"
            )

        result = response.get("result", {})

        # Get enhanced_count from MCP result
        enhanced_count = result.get("enhanced_count", 0)

        # Update workflow metrics if in a workflow
        if validation.workflow_id:
            db_manager.update_workflow_metrics(
                validation.workflow_id,
                recommendations_actioned=enhanced_count
            )

        return {
            "success": result.get("success", False),
            "message": f"Enhancement complete",
            "applied_count": enhanced_count,
            "enhanced_count": enhanced_count,
            "enhancements": result.get("enhancements", []),
            "errors": result.get("errors", [])
        }
        
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to enhance content with recommendations")
        raise HTTPException(status_code=500, detail="Enhancement failed")


@app.post("/api/enhance/batch")
async def enhance_batch(request: BatchEnhanceRequest):
    """
    Enhance multiple validations in batch mode.

    Processes multiple validations either in parallel or sequentially,
    applying approved recommendations to each validation.

    Returns batch processing results with success/failure status per validation.
    """
    try:
        # Get the enhancement agent
        enhancement_agent = agent_registry.get_agent("enhancement_agent")
        if not enhancement_agent:
            raise HTTPException(status_code=500, detail="Enhancement agent not available")

        # Validate that all validation IDs exist
        missing_validations = []
        for validation_id in request.validation_ids:
            validation = db_manager.get_validation(validation_id)
            if not validation:
                missing_validations.append(validation_id)

        if missing_validations:
            raise HTTPException(
                status_code=404,
                detail=f"Validation(s) not found: {', '.join(missing_validations[:3])}"
                + (f" and {len(missing_validations) - 3} more" if len(missing_validations) > 3 else "")
            )

        # Call batch enhancement method
        result = await enhancement_agent.enhance_batch(
            validation_ids=request.validation_ids,
            parallel=request.parallel,
            persist=request.persist,
            require_recommendations=request.require_recommendations,
            min_recommendations=request.min_recommendations,
            apply_all=request.apply_all,
            recommendation_ids_per_validation=request.recommendation_ids_per_validation
        )

        return {
            "success": True,
            "message": f"Batch enhancement complete: {result['successful_count']} successful, {result['failed_count']} failed",
            **result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to process batch enhancement")
        raise HTTPException(status_code=500, detail=f"Batch enhancement failed: {str(e)}")


# Bulk action endpoints
class BulkActionRequest(BaseModel):
    ids: List[str] = Field(description="List of validation IDs to process")

@app.post("/api/validations/bulk/approve")
async def bulk_approve_validations(request: BulkActionRequest):
    """Approve multiple validation records via MCP."""
    try:
        from svc.mcp_server import create_mcp_client
        from api.websocket_endpoints import connection_manager
        
        if not request.ids:
            raise HTTPException(status_code=400, detail="No validation IDs provided")
        
        # Create MCP client
        mcp_client = create_mcp_client()
        
        # Call MCP approve method
        mcp_request = {
            "method": "approve",
            "params": {
                "ids": request.ids
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
        
        # Notify WebSocket clients about bulk approval
        await connection_manager.send_progress_update("validation_updates", {
            "type": "bulk_validation_approved",
            "validation_ids": request.ids,
            "approved_count": result.get("approved_count", 0),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {
            "success": result.get("success", False),
            "message": f"Bulk approved {result.get('approved_count', 0)} validations",
            "approved_count": result.get("approved_count", 0),
            "errors": result.get("errors", [])
        }
        
    except ImportError:
        raise HTTPException(status_code=500, detail="MCP server not available")
    except Exception as e:
        logger.exception("Failed to bulk approve validations")
        raise HTTPException(status_code=500, detail=f"Bulk approval failed: {str(e)}")

@app.post("/api/validations/bulk/reject")
async def bulk_reject_validations(request: BulkActionRequest):
    """Reject multiple validation records via MCP."""
    try:
        from svc.mcp_server import create_mcp_client
        from api.websocket_endpoints import connection_manager
        
        if not request.ids:
            raise HTTPException(status_code=400, detail="No validation IDs provided")
        
        # Create MCP client
        mcp_client = create_mcp_client()
        
        # Call MCP reject method
        mcp_request = {
            "method": "reject",
            "params": {
                "ids": request.ids
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
        
        # Notify WebSocket clients about bulk rejection
        await connection_manager.send_progress_update("validation_updates", {
            "type": "bulk_validation_rejected",
            "validation_ids": request.ids,
            "rejected_count": result.get("rejected_count", 0),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {
            "success": result.get("success", False),
            "message": f"Bulk rejected {result.get('rejected_count', 0)} validations",
            "rejected_count": result.get("rejected_count", 0),
            "errors": result.get("errors", [])
        }
        
    except ImportError:
        raise HTTPException(status_code=500, detail="MCP server not available")
    except Exception as e:
        logger.exception("Failed to bulk reject validations")
        raise HTTPException(status_code=500, detail=f"Bulk rejection failed: {str(e)}")

@app.post("/api/validations/bulk/enhance")
async def bulk_enhance_validations(request: BulkActionRequest):
    """Enhance multiple approved validation records via MCP."""
    try:
        from svc.mcp_server import create_mcp_client
        from api.websocket_endpoints import connection_manager
        
        if not request.ids:
            raise HTTPException(status_code=400, detail="No validation IDs provided")
        
        # Create MCP client
        mcp_client = create_mcp_client()
        
        # Call MCP enhance method
        mcp_request = {
            "method": "enhance",
            "params": {
                "ids": request.ids
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
        
        # Notify WebSocket clients about bulk enhancement
        await connection_manager.send_progress_update("validation_updates", {
            "type": "bulk_validation_enhanced",
            "validation_ids": request.ids,
            "enhanced_count": result.get("enhanced_count", 0),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {
            "success": result.get("success", False),
            "message": f"Bulk enhanced {result.get('enhanced_count', 0)} validations",
            "enhanced_count": result.get("enhanced_count", 0),
            "errors": result.get("errors", []),
            "enhancements": result.get("enhancements", [])
        }
        
    except ImportError:
        raise HTTPException(status_code=500, detail="MCP server not available")
    except Exception as e:
        logger.exception("Failed to bulk enhance validations")
        raise HTTPException(status_code=500, detail=f"Bulk enhancement failed: {str(e)}")


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

@app.get("/workflows/{workflow_id}/report")
async def get_workflow_report(workflow_id: str):
    """Get a comprehensive report for a workflow including all validations and recommendations."""
    try:
        report = db_manager.generate_workflow_report(workflow_id)
        return report
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        logger.exception("Failed to generate workflow report")
        raise HTTPException(status_code=500, detail="Failed to generate workflow report")

@app.get("/workflows/{workflow_id}/summary")
async def get_workflow_summary(workflow_id: str):
    """Get a summary of workflow results (summary only, no detailed validations)."""
    try:
        report = db_manager.generate_workflow_report(workflow_id)
        # Return only summary without detailed validations and recommendations
        return {
            "workflow_id": report["workflow_id"],
            "status": report["status"],
            "type": report["type"],
            "created_at": report["created_at"],
            "completed_at": report["completed_at"],
            "duration_ms": report["duration_ms"],
            "summary": report["summary"]
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        logger.exception("Failed to generate workflow summary")
        raise HTTPException(status_code=500, detail="Failed to generate workflow summary")

@app.delete("/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """Delete a specific workflow."""
    try:
        workflow = db_manager.get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")

        # Soft delete using metadata
        count = db_manager.soft_delete_workflows([workflow_id])

        return {
            "message": "Workflow deleted successfully",
            "workflow_id": workflow_id,
            "deleted": count > 0
        }
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to delete workflow")
        raise HTTPException(status_code=500, detail="Failed to delete workflow")

@app.post("/workflows/delete")
async def delete_workflows_bulk(workflow_ids: List[str]):
    """Delete multiple workflows (bulk operation)."""
    try:
        count = db_manager.soft_delete_workflows(workflow_ids)
        
        return {
            "message": f"Deleted {count} workflow(s)",
            "deleted_count": count,
            "requested_count": len(workflow_ids)
        }
    except Exception:
        logger.exception("Failed to bulk delete workflows")
        raise HTTPException(status_code=500, detail="Failed to delete workflows")

@app.delete("/workflows")
async def delete_all_workflows(confirm: bool = Query(False)):
    """
    Delete all workflows. Requires confirmation.
    Use ?confirm=true to actually delete.
    """
    if not confirm:
        return {
            "message": "Confirmation required. Use ?confirm=true to delete all workflows.",
            "total_workflows": len(db_manager.list_workflows(limit=10000))
        }
    
    try:
        workflows = db_manager.list_workflows(limit=10000)
        workflow_ids = [w.id for w in workflows]
        count = db_manager.soft_delete_workflows(workflow_ids)
        
        return {
            "message": f"Deleted all {count} workflow(s)",
            "deleted_count": count
        }
    except Exception:
        logger.exception("Failed to delete all workflows")
        raise HTTPException(status_code=500, detail="Failed to delete all workflows")


@app.get("/api/workflows")
async def list_workflows_with_stats(
    state: Optional[str] = None,
    limit: int = Query(100, le=500),
    include_stats: bool = Query(True)
):
    """
    List all workflows with comprehensive statistics.
    
    Each workflow includes:
    - workflow_id: Unique identifier
    - type: Workflow type (validate_file, batch_validation, etc.)
    - state: Current state (pending, running, completed, failed, cancelled)
    - started_at: Start timestamp
    - completed_at: Completion timestamp
    - pages_processed: Number of pages/files processed
    - validations_found: Total validations detected
    - validations_approved: Number of validations approved
    - recommendations_generated: Total recommendations created
    - recommendations_approved: Number of recommendations approved
    - recommendations_actioned: Number of recommendations applied
    """
    try:
        workflows = db_manager.list_workflows(state=state, limit=limit)
        
        workflow_data = []
        for w in workflows:
            workflow_dict = w.to_dict()
            
            if include_stats:
                # Get comprehensive statistics
                stats = db_manager.get_workflow_stats(w.id)
                workflow_dict.update(stats)
            
            workflow_data.append(workflow_dict)
        
        return {
            "workflows": workflow_data,
            "total": len(workflow_data),
            "state_filter": state
        }
    except Exception:
        logger.exception("Failed to list workflows with stats")
        raise HTTPException(status_code=500, detail="Failed to retrieve workflows")


@app.post("/api/workflows/bulk-delete")
async def bulk_delete_workflows(workflow_ids: List[str]):
    """Delete multiple workflows by ID."""
    if not workflow_ids:
        raise HTTPException(status_code=400, detail="No workflow IDs provided")
    
    try:
        count = db_manager.soft_delete_workflows(workflow_ids)
        return {
            "message": f"Deleted {count} workflow(s)",
            "deleted_count": count,
            "requested_ids": workflow_ids
        }
    except Exception:
        logger.exception("Failed to bulk delete workflows")
        raise HTTPException(status_code=500, detail="Failed to delete workflows")


@app.post("/workflows/cancel-batch")
async def cancel_batch_workflows(workflow_ids: List[str]):
    """Cancel multiple workflows in batch."""
    if not workflow_ids:
        raise HTTPException(status_code=400, detail="No workflow IDs provided")
    
    try:
        cancelled = 0
        for wf_id in workflow_ids:
            wf = db_manager.get_workflow(wf_id)
            if wf and wf.state in [WorkflowState.PENDING, WorkflowState.RUNNING, WorkflowState.PAUSED]:
                db_manager.update_workflow(wf_id, state="cancelled")
                cancelled += 1
        
        return {
            "message": f"Cancelled {cancelled} workflow(s)",
            "cancelled_count": cancelled,
            "requested_count": len(workflow_ids)
        }
    except Exception:
        logger.exception("Failed to cancel batch workflows")
        raise HTTPException(status_code=500, detail="Failed to cancel workflows")

# =============================================================================
# Admin Endpoints
# =============================================================================

@app.get("/admin/status")
async def admin_status():
    """Get comprehensive admin status."""
    try:
        workflows = db_manager.list_workflows(limit=10000)
        active = [w for w in workflows if w.state in [WorkflowState.RUNNING, WorkflowState.PENDING]]
        
        uptime_seconds = int(time.time() - SERVER_START_TIME)
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "system": {
                "version": "1.0.0",
                "uptime_seconds": uptime_seconds,
                "agents_registered": len(agent_registry.list_agents()),
                "maintenance_mode": MAINTENANCE_MODE
            },
            "workflows": {
                "total": len(workflows),
                "active": len(active),
                "pending": len([w for w in workflows if w.state == WorkflowState.PENDING]),
                "running": len([w for w in workflows if w.state == WorkflowState.RUNNING]),
                "completed": len([w for w in workflows if w.state == WorkflowState.COMPLETED]),
                "failed": len([w for w in workflows if w.state == WorkflowState.FAILED])
            },
            "database": {
                "connected": db_manager.is_connected()
            }
        }
    except Exception:
        logger.exception("Failed to get admin status")
        raise HTTPException(status_code=500, detail="Failed to retrieve admin status")

@app.get("/admin/workflows/active")
async def admin_active_workflows():
    """Get all active workflows."""
    try:
        workflows = db_manager.list_workflows(limit=10000)
        active = [w for w in workflows if w.state in [WorkflowState.RUNNING, WorkflowState.PENDING, WorkflowState.PAUSED]]
        
        return {
            "count": len(active),
            "workflows": [w.to_dict() for w in active]
        }
    except Exception:
        logger.exception("Failed to get active workflows")
        raise HTTPException(status_code=500, detail="Failed to retrieve active workflows")

@app.post("/admin/cache/clear")
async def admin_clear_cache():
    """Clear all caches."""
    try:
        cleared = {"l1": False, "l2": False, "l1_entries": 0, "l2_entries": 0}

        # Clear L1 cache
        if cache_manager.l1_cache:
            l1_size = cache_manager.l1_cache.size()
            cache_manager.l1_cache.clear()
            cleared["l1"] = True
            cleared["l1_entries"] = l1_size
            logger.info("L1 cache cleared", entries=l1_size)

        # Clear L2 cache
        from core.database import CacheEntry
        with db_manager.get_session() as session:
            l2_count = session.query(CacheEntry).count()
            session.query(CacheEntry).delete()
            session.commit()
            cleared["l2"] = True
            cleared["l2_entries"] = l2_count
            logger.info("L2 cache cleared", entries=l2_count)

        return {
            "message": "Cache cleared successfully",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cleared": cleared
        }
    except Exception:
        logger.exception("Failed to clear cache")
        raise HTTPException(status_code=500, detail="Failed to clear cache")

@app.get("/admin/cache/stats")
async def admin_cache_stats():
    """Get cache statistics."""
    try:
        stats = cache_manager.get_statistics()
        return stats
    except Exception:
        logger.exception("Failed to get cache stats")
        raise HTTPException(status_code=500, detail="Failed to retrieve cache statistics")

@app.post("/admin/cache/cleanup")
async def admin_cleanup_cache():
    """Cleanup expired cache entries."""
    try:
        result = cache_manager.cleanup_expired()
        total_removed = result.get("l1_cleaned", 0) + result.get("l2_cleaned", 0)

        return {
            "message": "Cache cleanup completed",
            "removed_entries": total_removed,
            "details": result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception:
        logger.exception("Failed to cleanup cache")
        raise HTTPException(status_code=500, detail="Failed to cleanup cache")

@app.post("/admin/cache/rebuild")
async def admin_rebuild_cache():
    """Rebuild cache from scratch."""
    try:
        # Clear all existing cache
        if cache_manager.l1_cache:
            cache_manager.l1_cache.clear()

        from core.database import CacheEntry
        with db_manager.get_session() as session:
            session.query(CacheEntry).delete()
            session.commit()

        logger.info("Cache rebuild: all caches cleared, will repopulate on demand")

        # Optionally preload critical data (truth data)
        try:
            truth_manager = agent_registry.get_agent("truth_manager")
            if truth_manager:
                # This will cache the truth data on first load
                await truth_manager.handle_message({
                    "type": "REQUEST",
                    "method": "load_truth",
                    "params": {"family": "words"}
                })
                logger.info("Cache rebuild: preloaded truth data for 'words' family")
        except Exception as e:
            logger.warning("Cache rebuild: failed to preload truth data", error=str(e))

        return {
            "message": "Cache rebuild completed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "note": "Cache cleared and will repopulate on demand"
        }
    except Exception:
        logger.exception("Failed to rebuild cache")
        raise HTTPException(status_code=500, detail="Failed to rebuild cache")

@app.get("/admin/reports/performance")
async def admin_performance_report(days: int = Query(7, le=90)):
    """Get performance report based on workflow analysis."""
    try:
        from datetime import timedelta
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        # Get all workflows from the period
        all_workflows = db_manager.list_workflows(limit=100000)
        # Ensure timezone-aware comparison
        period_workflows = [
            w for w in all_workflows
            if w.created_at and (
                w.created_at.replace(tzinfo=timezone.utc) if w.created_at.tzinfo is None else w.created_at
            ) >= cutoff_date
        ]

        total = len(period_workflows)
        completed = len([w for w in period_workflows if w.state == WorkflowState.COMPLETED])
        failed = len([w for w in period_workflows if w.state == WorkflowState.FAILED])
        running = len([w for w in period_workflows if w.state == WorkflowState.RUNNING])

        # Calculate average completion time for completed workflows
        completion_times = []
        for w in period_workflows:
            if w.state == WorkflowState.COMPLETED and w.created_at and w.updated_at:
                delta = (w.updated_at - w.created_at).total_seconds() * 1000  # ms
                completion_times.append(delta)

        avg_completion_ms = sum(completion_times) / len(completion_times) if completion_times else 0
        error_rate = (failed / total) if total > 0 else 0.0
        success_rate = (completed / total) if total > 0 else 0.0

        # Cache statistics
        cache_stats = cache_manager.get_statistics()
        l1_hit_rate = cache_stats.get("l1", {}).get("hit_rate", 0.0)

        return {
            "period_days": days,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": {
                "total_workflows": total,
                "completed_workflows": completed,
                "failed_workflows": failed,
                "running_workflows": running,
                "avg_completion_time_ms": round(avg_completion_ms, 2),
                "error_rate": round(error_rate, 4),
                "success_rate": round(success_rate, 4),
                "cache_hit_rate_l1": round(l1_hit_rate, 4)
            },
            "period": {
                "start": cutoff_date.isoformat(),
                "end": datetime.now(timezone.utc).isoformat()
            }
        }
    except Exception:
        logger.exception("Failed to get performance report")
        raise HTTPException(status_code=500, detail="Failed to retrieve performance report")

@app.get("/admin/reports/health")
async def admin_health_report(period: str = Query("7days")):
    """Get system health report."""
    try:
        return {
            "period": period,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "database": db_manager.is_connected(),
            "agents": len(agent_registry.list_agents()),
            "status": "healthy"
        }
    except Exception:
        logger.exception("Failed to get health report")
        raise HTTPException(status_code=500, detail="Failed to retrieve health report")

@app.post("/admin/agents/reload/{agent_id}")
async def admin_reload_agent(agent_id: str):
    """Reload a specific agent by clearing its cache and reinitializing."""
    try:
        agent = agent_registry.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

        # Clear agent's cache
        cache_manager.clear_agent_cache(agent_id)
        logger.info(f"Cleared cache for agent {agent_id}")

        # Reload configuration if agent has a config reload method
        if hasattr(agent, 'reload_config'):
            await agent.reload_config()
            logger.info(f"Reloaded configuration for agent {agent_id}")

        # Reset internal state if applicable
        if hasattr(agent, 'reset_state'):
            agent.reset_state()
            logger.info(f"Reset state for agent {agent_id}")

        return {
            "message": f"Agent {agent_id} reloaded successfully",
            "agent_id": agent_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actions": ["cache_cleared", "config_reloaded" if hasattr(agent, 'reload_config') else "no_config_reload"]
        }
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Failed to reload agent {agent_id}")
        raise HTTPException(status_code=500, detail="Failed to reload agent")

@app.post("/admin/system/gc")
async def admin_garbage_collect():
    """Trigger garbage collection."""
    try:
        import gc
        gc.collect()
        return {
            "message": "Garbage collection completed",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception:
        logger.exception("Failed to trigger GC")
        raise HTTPException(status_code=500, detail="Failed to trigger garbage collection")

@app.post("/admin/maintenance/enable")
async def admin_enable_maintenance():
    """Enable maintenance mode."""
    try:
        global MAINTENANCE_MODE
        MAINTENANCE_MODE = True
        logger.warning("Maintenance mode ENABLED - system is now in maintenance mode")

        return {
            "message": "Maintenance mode enabled",
            "maintenance_mode": MAINTENANCE_MODE,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "note": "New workflow submissions will be rejected while in maintenance mode"
        }
    except Exception:
        logger.exception("Failed to enable maintenance mode")
        raise HTTPException(status_code=500, detail="Failed to enable maintenance mode")

@app.post("/admin/maintenance/disable")
async def admin_disable_maintenance():
    """Disable maintenance mode."""
    try:
        global MAINTENANCE_MODE
        MAINTENANCE_MODE = False
        logger.info("Maintenance mode DISABLED - system is now operational")

        return {
            "message": "Maintenance mode disabled",
            "maintenance_mode": MAINTENANCE_MODE,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "note": "System is now accepting new workflows"
        }
    except Exception:
        logger.exception("Failed to disable maintenance mode")
        raise HTTPException(status_code=500, detail="Failed to disable maintenance mode")

@app.post("/admin/system/checkpoint")
async def admin_system_checkpoint():
    """Create system checkpoint for disaster recovery."""
    try:
        import json
        import pickle

        checkpoint_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc)

        # Gather system state
        workflows = db_manager.list_workflows(limit=10000)
        active_workflows = [w for w in workflows if w.state in [WorkflowState.RUNNING, WorkflowState.PENDING]]

        system_state = {
            "checkpoint_id": checkpoint_id,
            "timestamp": timestamp.isoformat(),
            "workflows": {
                "total": len(workflows),
                "active": len(active_workflows),
                "active_ids": [w.id for w in active_workflows]
            },
            "agents": {
                "registered": len(agent_registry.list_agents()),
                "agent_ids": [a["agent_id"] for a in agent_registry.list_agents()]
            },
            "cache": cache_manager.get_statistics(),
            "system": {
                "uptime_seconds": int(time.time() - SERVER_START_TIME),
                "maintenance_mode": MAINTENANCE_MODE
            }
        }

        # Store checkpoint in database using a special sentinel workflow
        from core.database import Checkpoint
        state_data = pickle.dumps(system_state)

        # Create a system checkpoint entry (workflow_id can be null for system checkpoints)
        # But since the schema requires it, we'll use a special ID
        SYSTEM_CHECKPOINT_WORKFLOW_ID = "00000000-0000-0000-0000-000000000000"

        with db_manager.get_session() as session:
            checkpoint = Checkpoint(
                id=checkpoint_id,
                workflow_id=SYSTEM_CHECKPOINT_WORKFLOW_ID,
                name=f"system_checkpoint_{timestamp.strftime('%Y%m%d_%H%M%S')}",
                step_number=0,
                state_data=state_data,
                created_at=timestamp,
                can_resume_from=True
            )
            session.add(checkpoint)
            session.commit()

        logger.info("System checkpoint created", checkpoint_id=checkpoint_id)

        return {
            "message": "System checkpoint created successfully",
            "checkpoint_id": checkpoint_id,
            "timestamp": timestamp.isoformat(),
            "summary": system_state
        }
    except Exception:
        logger.exception("Failed to create checkpoint")
        raise HTTPException(status_code=500, detail="Failed to create system checkpoint")


# System Reset Request Model
class SystemResetRequest(BaseModel):
    """Request model for system reset operation."""
    confirm: bool = Field(..., description="Must be true to confirm deletion (safety check)")
    delete_validations: bool = Field(True, description="Delete all validation results")
    delete_workflows: bool = Field(True, description="Delete all workflows")
    delete_recommendations: bool = Field(True, description="Delete all recommendations")
    delete_audit_logs: bool = Field(False, description="Delete audit logs (normally preserved for compliance)")
    clear_cache: bool = Field(True, description="Clear cache after reset")


@app.post("/api/admin/reset",
    tags=["admin"],
    summary="Reset system data",
    description="Permanently delete data from the database. Use this to clean up before production or during development. DANGEROUS OPERATION.",
    responses={
        200: {"description": "System reset successful", "content": {"application/json": {"example": {
            "message": "System reset completed",
            "deleted": {
                "validations_deleted": 150,
                "workflows_deleted": 45,
                "recommendations_deleted": 320,
                "audit_logs_deleted": 0
            },
            "cache_cleared": True,
            "timestamp": "2025-11-21T18:50:00.000000"
        }}}},
        400: {"description": "Invalid request or confirmation not provided"},
        500: {"description": "Server error during reset"}
    }
)
async def admin_reset_system(reset_request: SystemResetRequest):
    """
    Reset the system by permanently deleting data.

    **DANGEROUS OPERATION**: This permanently deletes data from the database.

    Use this endpoint to:
    - Clean up test data before production
    - Reset development environment
    - Clear all data during testing

    Safety Features:
    - Requires explicit confirmation (`confirm: true`)
    - Selective deletion (choose what to delete)
    - Audit logs preserved by default
    - Detailed response with deletion counts

    Returns:
        Dictionary with counts of deleted items and operation details
    """
    try:
        if not reset_request.confirm:
            raise HTTPException(
                status_code=400,
                detail="Must explicitly confirm system reset by setting confirm=true"
            )

        logger.warning("System reset requested via API", extra={
            "delete_validations": reset_request.delete_validations,
            "delete_workflows": reset_request.delete_workflows,
            "delete_recommendations": reset_request.delete_recommendations,
            "delete_audit_logs": reset_request.delete_audit_logs
        })

        # Perform reset
        results = db_manager.reset_system(
            confirm=True,
            delete_validations=reset_request.delete_validations,
            delete_workflows=reset_request.delete_workflows,
            delete_recommendations=reset_request.delete_recommendations,
            delete_audit_logs=reset_request.delete_audit_logs
        )

        # Clear cache if requested
        cache_cleared = False
        if reset_request.clear_cache:
            try:
                from core.cache import cache_manager
                # Clear L1 cache
                if cache_manager.l1_cache:
                    cache_manager.l1_cache.clear()
                # Clear L2 cache from database
                db_manager.cleanup_expired_cache()
                cache_cleared = True
                logger.info("Cache cleared after system reset")
            except Exception as e:
                logger.warning(f"Failed to clear cache after reset: {e}")

        total_deleted = sum(results.values())
        logger.warning(f"System reset completed: {total_deleted} items deleted", extra=results)

        return {
            "message": "System reset completed",
            "deleted": results,
            "cache_cleared": cache_cleared,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except HTTPException:
        # Re-raise HTTPExceptions without modification
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Failed to reset system")
        raise HTTPException(status_code=500, detail=f"Failed to reset system: {str(e)}")


# =============================================================================
# Audit Trail Endpoints (DEFERRED)
# =============================================================================

@app.get("/api/audit")
async def list_audit_logs(
    recommendation_id: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = Query(100, le=500)
):
    """
    Audit logs feature - Currently deferred.
    
    Future implementation will provide:
    - Centralized log of user actions (approvals, rejections)
    - Agent actions (recommendations generated, enhancements applied)
    - Content changes with before/after snapshots
    - Full audit trail for compliance and debugging
    """
    raise HTTPException(
        status_code=404,
        detail="Audit logs feature is currently being redesigned. Check back soon for centralized logging of user actions, agent actions, and content changes."
    )

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
            completed_at=datetime.now(timezone.utc)
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
    """Run batch validation workflow with automatic recommendation generation."""
    validator = agent_registry.get_agent("content_validator")
    recommendation_agent = agent_registry.get_agent("recommendation_agent")

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
        total_recommendations = 0

        # Filter for English content only
        english_file_paths, rejected_files = validate_english_content_batch(request.files)

        # Log rejected files
        if rejected_files:
            logger.info(f"Filtered out {len(rejected_files)} non-English files from batch validation")
            for file_path, reason in rejected_files[:10]:  # Log first 10 rejections
                errors.append(f"Skipped (non-English): {file_path} - {reason}")
                logger.debug(f"Rejected: {file_path} - {reason}")

        # Update workflow with filtered file count
        workflow_jobs[job_id].files_total = len(english_file_paths)

        # Create a mapping of file_path to content if in upload mode
        content_map = {}
        if request.upload_mode and request.file_contents:
            content_map = {fc.file_path: fc.content for fc in request.file_contents}

        for file_path in english_file_paths:
            try:
                # Read file content - either from upload or server filesystem
                if request.upload_mode:
                    content = content_map.get(file_path)
                    if not content:
                        raise ValueError(f"Content not found for uploaded file: {file_path}")
                else:
                    # Read from server filesystem
                    from pathlib import Path
                    content = Path(file_path).read_text()
                
                # Step 1: Validate
                validation_result = await validator.process_request("validate_content", {
                    "content": content,
                    "file_path": file_path,
                    "family": request.family,
                    "validation_types": request.validation_types,
                    "workflow_id": workflow_id
                })
                
                # Step 2: Get validation ID from result or database
                validation_id = validation_result.get("id")
                if not validation_id:
                    # Find most recent validation for this file
                    validations = db_manager.list_validation_results(
                        file_path=file_path, 
                        workflow_id=workflow_id,
                        limit=1
                    )
                    if validations:
                        validation_id = validations[0].id
                
                # Step 3: Generate recommendations if validation found issues
                if validation_id and recommendation_agent:
                    try:
                        rec_result = await recommendation_agent.process_request(
                            "generate_recommendations",
                            {
                                "validation": validation_result,
                                "content": content,
                                "context": {
                                    "file_path": file_path,
                                    "validation_id": validation_id,
                                    "workflow_id": workflow_id
                                },
                                "persist": True
                            }
                        )
                        rec_count = rec_result.get("count", 0)
                        total_recommendations += rec_count
                        logger.info(f"Generated {rec_count} recommendations for {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to generate recommendations for {file_path}: {e}")
                
                validated += 1
            except Exception as e:
                failed += 1
                errors.append(f"{file_path}: {str(e)}")
            
            # Update progress
            progress = int((validated + failed) / len(english_file_paths) * 100) if english_file_paths else 100
            workflow_jobs[job_id].files_validated = validated
            workflow_jobs[job_id].files_failed = failed
            workflow_jobs[job_id].errors = errors[:10]  # Keep last 10 errors

            db_manager.update_workflow(
                workflow_id,
                current_step=validated + failed,
                total_steps=len(english_file_paths),
                progress_percent=progress
            )
        
        # Update workflow metrics
        db_manager.update_workflow_metrics(
            workflow_id,
            pages_processed=validated,
            validations_found=validated,  # Simplified: assume 1 validation per file
            recommendations_generated=total_recommendations
        )
        
        # Complete
        workflow_jobs[job_id].status = "completed"
        db_manager.update_workflow(
            workflow_id,
            state="completed",
            completed_at=datetime.now(timezone.utc)
        )
        
        logger.info(
            f"Batch validation complete: {validated} validated, {failed} failed, "
            f"{total_recommendations} recommendations generated"
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

@app.post("/api/enhance")
async def enhance_content_with_recommendations(
    file_id: Optional[str] = None,
    validation_id: Optional[str] = None,
    recommendation_ids: Optional[List[str]] = None,
    apply_all: bool = False,
    file_path: Optional[str] = None,
    require_recommendations: Optional[bool] = None,
    min_recommendations: Optional[int] = None
):
    """
    Apply approved recommendations to content and revalidate.

    Args:
        file_id: File identifier
        validation_id: Validation result ID
        recommendation_ids: Specific recommendation IDs to apply
        apply_all: Apply all approved recommendations
        file_path: Path to the file
        require_recommendations: Override config - require recommendations before enhancement
        min_recommendations: Override config - minimum number of approved recommendations required
    """
    try:
        from agents.base import agent_registry
        
        # Get enhancement agent
        enhancement_agent = agent_registry.get_agent("enhancement_agent")
        if not enhancement_agent:
            raise HTTPException(status_code=500, detail="Enhancement agent not available")
        
        # Load validation result
        validation = db_manager.get_validation_result(validation_id) if validation_id else None
        if not validation and not file_path:
            raise HTTPException(status_code=400, detail="Must provide validation_id or file_path")
        
        target_file_path = file_path or (validation.file_path if validation else None)
        if not target_file_path:
            raise HTTPException(status_code=400, detail="Could not determine file path")
        
        # Load current content
        try:
            with open(target_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"File not found: {target_file_path}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")
        
        # Get recommendations to apply
        if apply_all:
            recommendations = db_manager.list_recommendations(
                validation_id=validation_id,
                status="approved"
            )
        elif recommendation_ids:
            recommendations = [
                db_manager.get_recommendation(rec_id) 
                for rec_id in recommendation_ids
                if db_manager.get_recommendation(rec_id)
            ]
        else:
            raise HTTPException(status_code=400, detail="Must specify recommendation_ids or set apply_all=true")
        
        if not recommendations:
            return {
                "success": False,
                "message": "No recommendations to apply",
                "applied_count": 0
            }
        
        # Apply recommendations
        result = await enhancement_agent.process_request("enhance_with_recommendations", {
            "content": content,
            "file_path": target_file_path,
            "validation_id": validation_id,
            "recommendation_ids": [r.id for r in recommendations],
            "require_recommendations": require_recommendations,
            "min_recommendations": min_recommendations
        })
        
        # Save enhanced content
        try:
            with open(target_file_path, 'w', encoding='utf-8') as f:
                f.write(result["enhanced_content"])
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to write enhanced content: {str(e)}")
        
        # Revalidate the file
        validator = agent_registry.get_agent("content_validator")
        if validator:
            revalidation_result = await validator.process_request("validate_content", {
                "content": result["enhanced_content"],
                "file_path": target_file_path,
                "validation_types": ["yaml", "markdown", "code", "links", "Truth", "FuzzyLogic"]
            })
        else:
            revalidation_result = None
        
        return {
            "success": True,
            "file_path": target_file_path,
            "applied_count": result.get("applied_count", 0),
            "skipped_count": result.get("skipped_count", 0),
            "diff": result.get("diff", ""),
            "revalidation": revalidation_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Enhancement failed")
        raise HTTPException(status_code=500, detail=f"Enhancement failed: {str(e)}")

@app.post("/api/validations/{validation_id}/recommendations/generate")
async def generate_recommendations_for_validation(validation_id: str):
    """
    Generate recommendations for a specific validation result.
    Useful for on-demand recommendation generation even if auto-generation failed.
    """
    try:
        from agents.base import agent_registry
        
        # Get validation result
        validation = db_manager.get_validation_result(validation_id)
        if not validation:
            raise HTTPException(status_code=404, detail="Validation not found")
        
        # Get recommendation agent
        rec_agent = agent_registry.get_agent("recommendation_agent")
        if not rec_agent:
            raise HTTPException(status_code=500, detail="Recommendation agent not available")
        
        # Load file content
        try:
            with open(validation.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            content = ""
        
        # Parse validation results
        validation_results = validation.validation_results or {}
        issues = validation_results.get("issues", [])
        
        recommendations_generated = 0
        for issue in issues:
            if issue.get("level") in ["error", "warning"]:
                validation_dict = {
                    "id": validation_id,
                    "validation_type": issue.get("category", "unknown"),
                    "status": "fail",
                    "message": issue.get("message", ""),
                    "details": issue
                }
                
                result = await rec_agent.process_request("generate_recommendations", {
                    "validation": validation_dict,
                    "content": content,
                    "context": {"file_path": validation.file_path, "validation_id": validation_id},
                    "persist": True
                })
                
                recommendations_generated += result.get("count", 0)
        
        return {
            "validation_id": validation_id,
            "recommendations_generated": recommendations_generated
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to generate recommendations")
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendations: {str(e)}")

@app.get("/api/validations/{validation_id}/recommendations")
async def get_validation_recommendations(validation_id: str):
    """
    Get all recommendations for a specific validation.
    """
    try:
        # Verify validation exists
        validation = db_manager.get_validation_result(validation_id)
        if not validation:
            raise HTTPException(status_code=404, detail="Validation not found")

        # Get recommendations
        recommendations = db_manager.list_recommendations(validation_id=validation_id)

        return {
            "validation_id": validation_id,
            "count": len(recommendations),
            "recommendations": [
                {
                    "id": rec.id,
                    "type": rec.type,
                    "title": rec.title,
                    "description": rec.description,
                    "status": rec.status.value if hasattr(rec.status, 'value') else rec.status,
                    "priority": rec.priority,
                    "confidence": rec.confidence,
                    "instruction": rec.instruction,
                    "original_content": rec.original_content,
                    "proposed_content": rec.proposed_content,
                    "created_at": rec.created_at.isoformat() if rec.created_at else None
                }
                for rec in recommendations
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get recommendations")
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")

@app.delete("/api/validations/{validation_id}/recommendations/{recommendation_id}")
async def delete_recommendation(validation_id: str, recommendation_id: str):
    """
    Delete a specific recommendation.
    """
    try:
        # Verify validation exists
        validation = db_manager.get_validation_result(validation_id)
        if not validation:
            raise HTTPException(status_code=404, detail="Validation not found")

        # Get recommendation to verify it belongs to this validation
        recommendation = db_manager.get_recommendation(recommendation_id)
        if not recommendation:
            raise HTTPException(status_code=404, detail="Recommendation not found")

        if recommendation.validation_id != validation_id:
            raise HTTPException(status_code=400, detail="Recommendation does not belong to this validation")

        # Delete recommendation
        success = db_manager.delete_recommendation(recommendation_id)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete recommendation")

        return {
            "success": True,
            "message": "Recommendation deleted successfully",
            "recommendation_id": recommendation_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to delete recommendation")
        raise HTTPException(status_code=500, detail=f"Failed to delete recommendation: {str(e)}")

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
async def root(request: Request):
    """
    API root with comprehensive endpoint index.
    Returns JSON for API clients, or HTML for browsers.
    """
    endpoints = {
        "health": {
            "url": "/health",
            "description": "Comprehensive health check with database and schema status"
        },
        "health_live": {
            "url": "/health/live",
            "description": "Kubernetes liveness probe"
        },
        "health_ready": {
            "url": "/health/ready",
            "description": "Kubernetes readiness probe"
        },
        "status": {
            "url": "/status",
            "description": "System status with component details"
        },
        "agents": {
            "url": "/agents",
            "description": "List all registered agents"
        },
        "validations": {
            "url": "/api/validations",
            "description": "List validation results"
        },
        "validate_content": {
            "url": "/api/validate",
            "description": "Validate content (POST)"
        },
        "validate_batch": {
            "url": "/api/validate/batch",
            "description": "Batch validation (POST)"
        },
        "recommendations": {
            "url": "/api/recommendations",
            "description": "List recommendations"
        },
        "recommendation_detail": {
            "url": "/api/recommendations/{id}",
            "description": "Get recommendation details"
        },
        "review_recommendation": {
            "url": "/api/recommendations/{id}/review",
            "description": "Review recommendation (approve/reject)"
        },
        "enhance_content": {
            "url": "/api/enhance",
            "description": "Enhance content with approved recommendations (POST)"
        },
        "workflows": {
            "url": "/workflows",
            "description": "List workflow runs"
        },
        "workflow_detail": {
            "url": "/workflows/{id}",
            "description": "Get workflow details"
        },
        "dashboard": {
            "url": "/dashboard",
            "description": "Web dashboard for validations and recommendations"
        },
        "dashboard_validations": {
            "url": "/dashboard/validations",
            "description": "Dashboard validations view"
        },
        "dashboard_recommendations": {
            "url": "/dashboard/recommendations",
            "description": "Dashboard recommendations view"
        },
        "dashboard_workflows": {
            "url": "/dashboard/workflows",
            "description": "Dashboard workflows view"
        },
        "api_docs": {
            "url": "/docs",
            "description": "Interactive API documentation (Swagger UI)"
        },
        "api_schema": {
            "url": "/openapi.json",
            "description": "OpenAPI schema"
        },
    }
    
    # Detect if request is from browser (basic heuristic)
    accept_header = request.headers.get("accept", "")
    is_browser = "text/html" in accept_header
    
    if is_browser:
        # Return simple HTML page with links
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>TBCV API</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 1200px; margin: 40px auto; padding: 20px; }
                h1 { color: #333; }
                .endpoint { margin: 20px 0; padding: 15px; background: #f5f5f5; border-radius: 5px; }
                .endpoint h3 { margin: 0 0 10px 0; color: #0066cc; }
                .endpoint a { text-decoration: none; color: #0066cc; font-weight: bold; }
                .endpoint p { margin: 5px 0; color: #666; }
                .version { color: #999; font-size: 0.9em; }
            </style>
        </head>
        <body>
            <h1>TBCV API <span class="version">v2.0.0</span></h1>
            <p>Truth-Based Content Validation and Enhancement System</p>
            <hr>
        """
        
        for name, info in endpoints.items():
            html_content += f"""
            <div class="endpoint">
                <h3>{name.replace('_', ' ').title()}</h3>
                <a href="{info['url']}">{info['url']}</a>
                <p>{info['description']}</p>
            </div>
            """
        
        html_content += """
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
    else:
        # Return JSON for API clients
        return {
            "name": "TBCV API",
            "version": "2.0.0",
            "description": "Truth-Based Content Validation and Enhancement System",
            "endpoints": endpoints
        }

@app.get("/status")
async def system_status():
    """Comprehensive system status."""
    agents = agent_registry.list_agents()
    
    return {
        "status": "operational",
        "timestamp": datetime.now(timezone.utc).isoformat(),
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
# Development Utilities Endpoints (CLI Parity)
# =============================================================================

class TestFileRequest(BaseModel):
    content: Optional[str] = Field(None, description="Custom content for test file")
    family: str = Field("words", description="Plugin family")
    filename: Optional[str] = Field(None, description="Custom filename")

@app.post("/api/dev/create-test-file",
    tags=["development"],
    summary="Create test file for validation",
    description="Creates a test markdown file with sample content and optionally validates it. Useful for testing validation workflows.",
    response_description="Test file created successfully with validation results"
)
async def create_test_file(request: TestFileRequest):
    """Create a test file for validation testing.

    Creates a temporary test file with either default or custom content,
    and optionally runs validation on it using the orchestrator.

    Returns:
        - status: Creation status
        - file_path: Path to created file
        - filename: Name of created file
        - validation_result: Validation results (if orchestrator available)
    """
    import tempfile
    from pathlib import Path

    default_content = """---
title: Test Document
description: This is a test document for TBCV validation
plugins:
  - Aspose.Words for .NET
  - PDF Converter
---

# Test Document

This is a test document with some plugin references.

## Code Example

```csharp
using Aspose.Words;

Document doc = new Document("input.docx");
doc.Save("output.pdf", SaveFormat.Pdf);
```

## Links

- [Aspose.Words Documentation](https://docs.aspose.com/words/)
"""

    content = request.content or default_content
    filename = request.filename or f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

    # Create temporary file
    temp_dir = Path("data/temp")
    temp_dir.mkdir(parents=True, exist_ok=True)

    test_file = temp_dir / filename
    test_file.write_text(content, encoding='utf-8')

    # Optionally validate it
    orchestrator = agent_registry.get_agent("orchestrator")
    validation_result = None

    if orchestrator:
        try:
            validation_result = await orchestrator.process_request("validate_file", {
                "file_path": str(test_file),
                "family": request.family
            })
        except Exception as e:
            logger.warning(f"Validation failed: {e}")

    return {
        "status": "created",
        "file_path": str(test_file),
        "filename": filename,
        "validation_result": validation_result
    }


@app.get("/api/dev/probe-endpoints",
    tags=["development"],
    summary="Discover and probe API endpoints",
    description="Returns a list of all registered API endpoints with their methods, paths, and tags. Supports filtering with regex patterns.",
    response_description="List of discovered endpoints"
)
async def probe_endpoints(
    include_pattern: Optional[str] = Query(None, description="Regex pattern to include only matching endpoint paths"),
    exclude_pattern: Optional[str] = Query(None, description="Regex pattern to exclude matching endpoint paths")
):
    """Discover and probe all registered API endpoints.

    Useful for API exploration, testing, and documentation generation.
    Supports filtering endpoints using regex patterns.

    Returns:
        - total_endpoints: Count of discovered endpoints
        - endpoints: List of endpoint objects with path, methods, name, and tags
    """
    import re

    endpoints = []

    for route in app.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            path = route.path

            # Apply filters
            if include_pattern and not re.search(include_pattern, path):
                continue
            if exclude_pattern and re.search(exclude_pattern, path):
                continue

            endpoints.append({
                "path": path,
                "methods": list(route.methods) if route.methods else [],
                "name": route.name if hasattr(route, "name") else None,
                "tags": route.tags if hasattr(route, "tags") else []
            })

    return {
        "total_endpoints": len(endpoints),
        "endpoints": sorted(endpoints, key=lambda x: x["path"])
    }


# =============================================================================
# Configuration & Control Endpoints (CLI Parity)
# =============================================================================

class CacheControlRequest(BaseModel):
    disable_cache: bool = Field(False, description="Disable caching for this session")
    clear_on_disable: bool = Field(False, description="Clear cache when disabling")

@app.post("/api/config/cache-control",
    tags=["configuration"],
    summary="Control cache behavior at runtime",
    description="Enable, disable, or clear the application cache dynamically without restart. Useful for testing and performance tuning.",
    response_description="Cache control status updated"
)
async def cache_control(request: CacheControlRequest):
    """Control cache behavior at runtime.

    Allows dynamic cache management:
    - Enable/disable caching
    - Clear cache when disabling
    - Check previous state

    Returns:
        - cache_disabled: Current cache state
        - previous_state: Previous cache state
        - cache_cleared: Whether cache was cleared (if requested)
    """
    from core.cache import cache_manager

    result = {
        "cache_disabled": request.disable_cache,
        "previous_state": getattr(cache_manager, '_disabled', False)
    }

    if request.disable_cache:
        cache_manager._disabled = True
        if request.clear_on_disable:
            cache_manager.clear()
            result["cache_cleared"] = True
    else:
        cache_manager._disabled = False

    return result


class LogLevelRequest(BaseModel):
    level: str = Field(..., description="Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL")

@app.post("/api/config/log-level",
    tags=["configuration"],
    summary="Set runtime log level",
    description="Change application log level dynamically without restart. Useful for debugging and troubleshooting in production.",
    response_description="Log level updated successfully",
    responses={
        200: {"description": "Log level updated"},
        400: {"description": "Invalid log level provided"}
    }
)
async def set_log_level(request: LogLevelRequest):
    """Set runtime log level.

    Valid log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

    Changes take effect immediately for all loggers.

    Returns:
        - status: Update status
        - log_level: New log level set
    """
    import logging

    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    level = request.level.upper()

    if level not in valid_levels:
        raise HTTPException(status_code=400, detail=f"Invalid log level. Must be one of: {valid_levels}")

    # Set for root logger and app logger
    logging.getLogger().setLevel(getattr(logging, level))
    logger.setLevel(getattr(logging, level))

    return {
        "status": "updated",
        "log_level": level
    }


class ForceOverrideRequest(BaseModel):
    validation_id: str
    force_enhance: bool = Field(True, description="Force enhancement even with safety warnings")

@app.post("/api/config/force-override",
    tags=["configuration"],
    summary="Force override safety checks",
    description="Override safety checks for content enhancement. Use with caution - bypasses rewrite ratio thresholds and other safety gates.",
    response_description="Force override flag set successfully",
    responses={
        200: {"description": "Override flag updated"},
        404: {"description": "Validation not found"}
    }
)
async def force_override_safety(request: ForceOverrideRequest):
    """Force override safety checks for content enhancement.

    Sets a force override flag on the validation metadata to bypass:
    - Rewrite ratio thresholds
    - Blocked topics filtering
    - Other safety gates

    Use with caution in production.

    Returns:
        - status: Update status
        - validation_id: Validation ID updated
        - force_override: Override flag value
    """
    val = db_manager.get_validation_result(request.validation_id)

    if not val:
        raise HTTPException(status_code=404, detail="Validation not found")

    # Store force flag in validation metadata
    if not val.validation_result.get('metadata'):
        val.validation_result['metadata'] = {}

    val.validation_result['metadata']['force_override'] = request.force_enhance
    db_manager.session.commit()

    return {
        "status": "updated",
        "validation_id": request.validation_id,
        "force_override": request.force_enhance
    }


# =============================================================================
# Export & Download Endpoints (CLI Parity - Multiple Formats)
# =============================================================================

@app.get("/api/export/validation/{validation_id}",
    tags=["export"],
    summary="Export validation result",
    description="Export a validation result in multiple formats (JSON, YAML, CSV, or plain text). Returns downloadable file.",
    response_description="Validation data in requested format",
    responses={
        200: {"description": "Export successful - file download"},
        404: {"description": "Validation not found"},
        400: {"description": "Unsupported format"}
    }
)
async def export_validation(
    validation_id: str,
    format: str = Query("json", description="Export format: json, yaml, text, or csv")
):
    """Export validation result in multiple formats.

    Supported formats:
    - json: Structured JSON (default)
    - yaml: YAML format (requires PyYAML)
    - csv: Comma-separated values with issues
    - text: Human-readable plain text report

    Returns a downloadable file with appropriate content-type and filename.
    """
    import json
    import csv
    from io import StringIO

    val = db_manager.get_validation_result(validation_id)

    if not val:
        raise HTTPException(status_code=404, detail="Validation not found")

    val_dict = val.to_dict()

    if format == "json":
        content = json.dumps(val_dict, indent=2)
        media_type = "application/json"
        filename = f"validation_{validation_id[:8]}.json"

    elif format == "yaml":
        try:
            import yaml
            content = yaml.dump(val_dict, default_flow_style=False)
            media_type = "application/x-yaml"
            filename = f"validation_{validation_id[:8]}.yaml"
        except ImportError:
            raise HTTPException(status_code=400, detail="PyYAML not installed")

    elif format == "text":
        lines = []
        lines.append(f"Validation Report: {validation_id}")
        lines.append("=" * 60)
        lines.append(f"File Path: {val_dict.get('file_path', 'N/A')}")
        lines.append(f"Status: {val_dict.get('status', 'N/A')}")
        lines.append(f"Severity: {val_dict.get('severity', 'N/A')}")
        lines.append(f"Created: {val_dict.get('created_at', 'N/A')}")
        lines.append("")

        issues = val_dict.get('validation_result', {}).get('content_validation', {}).get('issues', [])
        if issues:
            lines.append(f"Issues ({len(issues)}):")
            lines.append("-" * 60)
            for issue in issues:
                lines.append(f"  [{issue.get('level', 'UNKNOWN')}] {issue.get('category', '')}: {issue.get('message', '')}")

        content = "\n".join(lines)
        media_type = "text/plain"
        filename = f"validation_{validation_id[:8]}.txt"

    elif format == "csv":
        output = StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(['Validation ID', 'File Path', 'Status', 'Severity', 'Created'])
        writer.writerow([
            validation_id,
            val_dict.get('file_path', 'N/A'),
            val_dict.get('status', 'N/A'),
            val_dict.get('severity', 'N/A'),
            val_dict.get('created_at', 'N/A')
        ])

        # Issues
        writer.writerow([])
        writer.writerow(['Issue Level', 'Category', 'Message', 'Line'])

        issues = val_dict.get('validation_result', {}).get('content_validation', {}).get('issues', [])
        for issue in issues:
            writer.writerow([
                issue.get('level', ''),
                issue.get('category', ''),
                issue.get('message', ''),
                issue.get('line', '')
            ])

        content = output.getvalue()
        media_type = "text/csv"
        filename = f"validation_{validation_id[:8]}.csv"

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@app.get("/api/export/recommendations",
    tags=["export"],
    summary="Export recommendations",
    description="Export recommendations in multiple formats with optional filtering by validation ID or status. Returns downloadable file.",
    response_description="Recommendations data in requested format",
    responses={
        200: {"description": "Export successful - file download"},
        400: {"description": "Unsupported format"}
    }
)
async def export_recommendations(
    validation_id: Optional[str] = Query(None, description="Filter by validation ID"),
    status: Optional[str] = Query(None, description="Filter by status (proposed, approved, rejected, applied)"),
    format: str = Query("json", description="Export format: json, yaml, or csv")
):
    """Export recommendations in multiple formats.

    Supports filtering by validation ID and/or status.

    Supported formats:
    - json: Structured JSON (default)
    - yaml: YAML format (requires PyYAML)
    - csv: Comma-separated values

    Returns a downloadable file with appropriate content-type and filename.
    """
    import json
    import csv
    from io import StringIO

    recommendations = db_manager.list_recommendations(
        validation_id=validation_id,
        status=status,
        limit=10000
    )

    recs_data = [r.to_dict() for r in recommendations]

    if format == "json":
        content = json.dumps(recs_data, indent=2)
        media_type = "application/json"
        filename = "recommendations.json"

    elif format == "yaml":
        try:
            import yaml
            content = yaml.dump(recs_data, default_flow_style=False)
            media_type = "application/x-yaml"
            filename = "recommendations.yaml"
        except ImportError:
            raise HTTPException(status_code=400, detail="PyYAML not installed")

    elif format == "csv":
        output = StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(['ID', 'Status', 'Severity', 'Confidence', 'Instruction', 'Rationale', 'Created'])

        for rec in recs_data:
            writer.writerow([
                rec['id'],
                rec.get('status', ''),
                rec.get('severity', ''),
                rec.get('confidence', ''),
                rec.get('instruction', ''),
                rec.get('rationale', ''),
                rec.get('created_at', '')
            ])

        content = output.getvalue()
        media_type = "text/csv"
        filename = "recommendations.csv"

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@app.get("/api/export/workflow/{workflow_id}",
    tags=["export"],
    summary="Export workflow data",
    description="Export workflow execution data in JSON or YAML format. Includes workflow state, configuration, and progress. Returns downloadable file.",
    response_description="Workflow data in requested format",
    responses={
        200: {"description": "Export successful - file download"},
        404: {"description": "Workflow not found"},
        400: {"description": "Unsupported format"}
    }
)
async def export_workflow(
    workflow_id: str,
    format: str = Query("json", description="Export format: json or yaml")
):
    """Export workflow data in multiple formats.

    Supported formats:
    - json: Structured JSON (default)
    - yaml: YAML format (requires PyYAML)

    Returns a downloadable file with workflow state, configuration, and progress information.
    """
    import json

    wf = db_manager.get_workflow(workflow_id)

    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")

    wf_dict = wf.to_dict()

    if format == "json":
        content = json.dumps(wf_dict, indent=2)
        media_type = "application/json"
        filename = f"workflow_{workflow_id[:8]}.json"

    elif format == "yaml":
        try:
            import yaml
            content = yaml.dump(wf_dict, default_flow_style=False)
            media_type = "application/x-yaml"
            filename = f"workflow_{workflow_id[:8]}.yaml"
        except ImportError:
            raise HTTPException(status_code=400, detail="PyYAML not installed")

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


# =============================================================================
# Development Server Entry Point
# =============================================================================

if __name__ == "__main__":
    settings = get_settings()
    import uvicorn
    uvicorn.run(
        "tbcv.api.server:app",
        host="0.0.0.0",
        port=8585,
        reload=True,
        log_level="info"
    )
