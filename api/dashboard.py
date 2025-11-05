# file: tbcv/api/dashboard.py
"""
Dashboard interface for TBCV system.
Provides browser-accessible UI for viewing and managing validations and recommendations.
"""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from importlib import resources as _res

try:
    from core.database import db_manager
    from core.logging import get_logger
except ImportError:
    from core.database import db_manager
    from core.logging import get_logger

logger = get_logger(__name__)

# Any-CWD safe: resolve templates via relative path from current working directory
TEMPLATE_DIR = Path("templates")

templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

# Create router
router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Dashboard home page with overview."""
    try:
        # Get recent validations
        validations = db_manager.list_validation_results(limit=10)
        
        # Get pending recommendations
        pending_recommendations = db_manager.list_recommendations(status="pending", limit=10)
        
        # Get recent workflows
        workflows = db_manager.list_workflows(limit=10)
        
        # Calculate stats
        all_recommendations = db_manager.list_recommendations(limit=1000)
        stats = {
            "total_validations": len(validations),
            "total_recommendations": len(all_recommendations),
            "pending_recommendations": len([r for r in all_recommendations if r.status.value == "pending"]),
            "accepted_recommendations": len([r for r in all_recommendations if r.status.value == "accepted"]),
            "rejected_recommendations": len([r for r in all_recommendations if r.status.value == "rejected"]),
            "applied_recommendations": len([r for r in all_recommendations if r.status.value == "applied"]),
        }
        
        return templates.TemplateResponse(
            "dashboard_home.html",
            {
                "request": request,
                "validations": [v.to_dict() for v in validations],
                "recommendations": [r.to_dict() for r in pending_recommendations],
                "workflows": [w.to_dict() for w in workflows],
                "stats": stats,
            }
        )
    except Exception:
        logger.exception("Failed to load dashboard home")
        raise HTTPException(status_code=500, detail="Failed to load dashboard")


@router.get("/validations", response_class=HTMLResponse)
async def dashboard_validations(
    request: Request,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
):
    """List all validations with filtering."""
    try:
        validations = db_manager.list_validation_results(
            status=status,
            severity=severity,
            limit=page_size * page
        )
        
        # Simple pagination
        start = (page - 1) * page_size
        end = start + page_size
        page_validations = validations[start:end]
        
        return templates.TemplateResponse(
            "validations_list.html",
            {
                "request": request,
                "validations": [v.to_dict() for v in page_validations],
                "status_filter": status,
                "severity_filter": severity,
                "page": page,
                "page_size": page_size,
                "has_next": len(validations) > end,
                "has_prev": page > 1,
            }
        )
    except Exception:
        logger.exception("Failed to load validations list")
        raise HTTPException(status_code=500, detail="Failed to load validations")


@router.get("/validations/{validation_id}", response_class=HTMLResponse)
async def dashboard_validation_detail(request: Request, validation_id: str):
    """View detailed validation result with recommendations."""
    try:
        validation = db_manager.get_validation_result(validation_id)
        if not validation:
            raise HTTPException(status_code=404, detail="Validation not found")
        
        recommendations = db_manager.list_recommendations(validation_id=validation_id)
        
        return templates.TemplateResponse(
            "validation_detail.html",
            {
                "request": request,
                "validation": validation.to_dict(),
                "recommendations": [r.to_dict() for r in recommendations],
            }
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to load validation detail")
        raise HTTPException(status_code=500, detail="Failed to load validation")


@router.get("/recommendations", response_class=HTMLResponse)
async def dashboard_recommendations(
    request: Request,
    status: Optional[str] = None,
    type: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
):
    """List all recommendations with filtering."""
    try:
        recommendations = db_manager.list_recommendations(
            status=status,
            type=type,
            limit=page_size * page
        )
        
        # Simple pagination
        start = (page - 1) * page_size
        end = start + page_size
        page_recommendations = recommendations[start:end]
        
        return templates.TemplateResponse(
            "recommendations_list.html",
            {
                "request": request,
                "recommendations": [r.to_dict() for r in page_recommendations],
                "status_filter": status,
                "type_filter": type,
                "page": page,
                "page_size": page_size,
                "has_next": len(recommendations) > end,
                "has_prev": page > 1,
            }
        )
    except Exception:
        logger.exception("Failed to load recommendations list")
        raise HTTPException(status_code=500, detail="Failed to load recommendations")


@router.get("/recommendations/{recommendation_id}", response_class=HTMLResponse)
async def dashboard_recommendation_detail(request: Request, recommendation_id: str):
    """View detailed recommendation with audit trail."""
    try:
        recommendation = db_manager.get_recommendation(recommendation_id)
        if not recommendation:
            raise HTTPException(status_code=404, detail="Recommendation not found")
        
        validation = db_manager.get_validation_result(recommendation.validation_id)
        audit_logs = db_manager.list_audit_logs(recommendation_id=recommendation_id)
        
        return templates.TemplateResponse(
            "recommendation_detail.html",
            {
                "request": request,
                "recommendation": recommendation.to_dict(),
                "validation": validation.to_dict() if validation else None,
                "audit_logs": [log.to_dict() for log in audit_logs],
            }
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to load recommendation detail")
        raise HTTPException(status_code=500, detail="Failed to load recommendation")


@router.post("/recommendations/{recommendation_id}/review")
async def dashboard_review_recommendation(
    request: Request,
    recommendation_id: str,
    action: str = Form(...),
    reviewer: str = Form("dashboard_user"),
    notes: Optional[str] = Form(None)
):
    """Review a recommendation (approve/reject) from the dashboard."""
    if action not in ["accepted", "rejected", "pending"]:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    try:
        db_manager.update_recommendation_status(
            recommendation_id=recommendation_id,
            status=action,
            reviewer=reviewer,
            review_notes=notes
        )
        
        # Redirect back to recommendation detail
        return RedirectResponse(
            url=f"/dashboard/recommendations/{recommendation_id}",
            status_code=303
        )
    except Exception:
        logger.exception("Failed to review recommendation")
        raise HTTPException(status_code=500, detail="Failed to review recommendation")


@router.post("/recommendations/bulk-review")
async def dashboard_bulk_review(
    request: Request,
    recommendation_ids: str = Form(...),  # Comma-separated IDs
    action: str = Form(...),
    reviewer: str = Form("dashboard_user"),
    notes: Optional[str] = Form(None)
):
    """Bulk review multiple recommendations."""
    if action not in ["accepted", "rejected"]:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    ids = [id.strip() for id in recommendation_ids.split(",") if id.strip()]
    
    success_count = 0
    for rec_id in ids:
        try:
            db_manager.update_recommendation_status(
                recommendation_id=rec_id,
                status=action,
                reviewer=reviewer,
                review_notes=notes
            )
            success_count += 1
        except Exception:
            logger.exception("Failed to review recommendation %s", rec_id)
    
    # Redirect to recommendations list
    return RedirectResponse(
        url=f"/dashboard/recommendations?status=pending",
        status_code=303
    )


@router.get("/workflows", response_class=HTMLResponse)
async def dashboard_workflows(
    request: Request,
    state: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
):
    """List all workflows."""
    try:
        workflows = db_manager.list_workflows(
            state=state,
            limit=page_size * page
        )
        
        # Simple pagination
        start = (page - 1) * page_size
        end = start + page_size
        page_workflows = workflows[start:end]
        
        return templates.TemplateResponse(
            "workflows_list.html",
            {
                "request": request,
                "workflows": [w.to_dict() for w in page_workflows],
                "state_filter": state,
                "page": page,
                "page_size": page_size,
                "has_next": len(workflows) > end,
                "has_prev": page > 1,
            }
        )
    except Exception:
        logger.exception("Failed to load workflows list")
        raise HTTPException(status_code=500, detail="Failed to load workflows")


@router.get("/workflows/{workflow_id}", response_class=HTMLResponse)
async def dashboard_workflow_detail(request: Request, workflow_id: str):
    """View detailed workflow information."""
    try:
        workflow = db_manager.get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Get associated validation results
        validations = db_manager.list_validation_results(workflow_id=workflow_id, limit=100)
        
        return templates.TemplateResponse(
            "workflow_detail.html",
            {
                "request": request,
                "workflow": workflow.to_dict(),
                "validations": [v.to_dict() for v in validations],
            }
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to load workflow detail")
        raise HTTPException(status_code=500, detail="Failed to load workflow")


@router.get("/audit", response_class=HTMLResponse)
async def dashboard_audit_logs(
    request: Request,
    action: Optional[str] = None,
    page: int = 1,
    page_size: int = 50
):
    """View audit logs."""
    try:
        logs = db_manager.list_audit_logs(
            action=action,
            limit=page_size * page
        )
        
        # Simple pagination
        start = (page - 1) * page_size
        end = start + page_size
        page_logs = logs[start:end]
        
        return templates.TemplateResponse(
            "audit_logs.html",
            {
                "request": request,
                "logs": [log.to_dict() for log in page_logs],
                "action_filter": action,
                "page": page,
                "page_size": page_size,
                "has_next": len(logs) > end,
                "has_prev": page > 1,
            }
        )
    except Exception:
        logger.exception("Failed to load audit logs")
        raise HTTPException(status_code=500, detail="Failed to load audit logs")
