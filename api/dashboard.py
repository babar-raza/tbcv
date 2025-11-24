# file: tbcv/api/dashboard.py
"""
Dashboard interface for TBCV system.
Provides browser-accessible UI for viewing and managing validations and recommendations.
"""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
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


# Pydantic models for form request bodies
class ReviewRecommendationRequest(BaseModel):
    """Request model for reviewing a single recommendation."""
    action: str = Field(..., description="Review action: approve, reject, accept, or pending")
    reviewer: str = Field("dashboard_user", description="Name of the reviewer")
    notes: Optional[str] = Field(None, description="Optional review notes")


class BulkReviewRequest(BaseModel):
    """Request model for bulk reviewing multiple recommendations."""
    recommendation_ids: str = Field(..., description="Comma-separated recommendation IDs")
    action: str = Field(..., description="Review action: approve, reject, or accept")
    reviewer: str = Field("dashboard_user", description="Name of the reviewer")
    notes: Optional[str] = Field(None, description="Optional review notes")


# Dependency functions for form data parsing
async def parse_review_form(
    action: str = Form(..., description="Review action: approve, reject, accept, or pending"),
    reviewer: str = Form("dashboard_user", description="Name of the reviewer"),
    notes: Optional[str] = Form(None, description="Optional review notes")
) -> ReviewRecommendationRequest:
    """Parse form data into ReviewRecommendationRequest model."""
    return ReviewRecommendationRequest(action=action, reviewer=reviewer, notes=notes)


async def parse_bulk_review_form(
    recommendation_ids: str = Form(..., description="Comma-separated recommendation IDs"),
    action: str = Form(..., description="Review action: approve, reject, or accept"),
    reviewer: str = Form("dashboard_user", description="Name of the reviewer"),
    notes: Optional[str] = Form(None, description="Optional review notes")
) -> BulkReviewRequest:
    """Parse form data into BulkReviewRequest model."""
    return BulkReviewRequest(recommendation_ids=recommendation_ids, action=action, reviewer=reviewer, notes=notes)


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
            "accepted_recommendations": len([r for r in all_recommendations if r.status.value == "accepted" or r.status.value == "approved"]),
            "rejected_recommendations": len([r for r in all_recommendations if r.status.value == "rejected"]),
            "applied_recommendations": len([r for r in all_recommendations if r.status.value == "applied"]),
        }

        return templates.TemplateResponse(
            "dashboard_home_realtime.html",
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
            "validation_detail_enhanced.html",
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
    review_data: ReviewRecommendationRequest = Depends(parse_review_form)
):
    """Review a recommendation (approve/reject) from the dashboard."""
    # Normalize action: approve->approved, reject->rejected, accept->approved
    action_map = {
        "approve": "approved",
        "approved": "approved",
        "accept": "approved",
        "accepted": "approved",
        "reject": "rejected",
        "rejected": "rejected",
        "pending": "pending"
    }

    normalized_action = action_map.get(review_data.action.lower())
    if not normalized_action:
        raise HTTPException(status_code=400, detail=f"Invalid action: {review_data.action}")

    try:
        # Check if recommendation exists
        rec = db_manager.get_recommendation(recommendation_id)
        if not rec:
            raise HTTPException(status_code=404, detail="Recommendation not found")

        # Update status
        db_manager.update_recommendation_status(
            recommendation_id=recommendation_id,
            status=normalized_action,
            reviewer=review_data.reviewer,
            review_notes=review_data.notes
        )

        # Redirect back to recommendation detail
        return RedirectResponse(
            url=f"/dashboard/recommendations/{recommendation_id}",
            status_code=303
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to review recommendation")
        raise HTTPException(status_code=500, detail="Failed to review recommendation")


@router.post("/recommendations/bulk-review")
async def dashboard_bulk_review(
    request: Request,
    bulk_data: BulkReviewRequest = Depends(parse_bulk_review_form)
):
    """Bulk review multiple recommendations."""
    # Normalize action (same as single review)
    action_map = {
        "approve": "approved",
        "approved": "approved",
        "accept": "approved",
        "accepted": "approved",
        "reject": "rejected",
        "rejected": "rejected"
    }

    normalized_action = action_map.get(bulk_data.action.lower())
    if not normalized_action:
        raise HTTPException(status_code=400, detail=f"Invalid action: {bulk_data.action}")

    ids = [id.strip() for id in bulk_data.recommendation_ids.split(",") if id.strip()]
    if not ids:
        raise HTTPException(status_code=400, detail="No recommendation IDs provided")

    success_count = 0
    failed_ids = []

    for rec_id in ids:
        try:
            # Check if recommendation exists
            rec = db_manager.get_recommendation(rec_id)
            if not rec:
                failed_ids.append((rec_id, "Not found"))
                continue

            db_manager.update_recommendation_status(
                recommendation_id=rec_id,
                status=normalized_action,
                reviewer=bulk_data.reviewer,
                review_notes=bulk_data.notes
            )
            success_count += 1
        except Exception as e:
            logger.exception("Failed to review recommendation %s", rec_id)
            failed_ids.append((rec_id, str(e)))

    # Log results
    logger.info(f"Bulk review completed: {success_count} succeeded, {len(failed_ids)} failed")

    # Redirect to recommendations list with status message
    url = f"/dashboard/recommendations?status=pending&bulk_reviewed={success_count}"
    if failed_ids:
        url += f"&bulk_failed={len(failed_ids)}"

    return RedirectResponse(url=url, status_code=303)


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
        
        # Get comprehensive workflow stats
        workflow_stats = db_manager.get_workflow_stats(workflow_id)
        
        return templates.TemplateResponse(
            "workflow_detail_realtime.html",
            {
                "request": request,
                "workflow": workflow.to_dict(),
                "validations": [v.to_dict() for v in validations],
                "workflow_stats": workflow_stats,
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
    """Audit logs - feature deferred until spec is complete."""
    raise HTTPException(
        status_code=404,
        detail="Audit logs feature is currently being redesigned. Check back soon for centralized logging of user actions, agent actions, and content changes."
    )
