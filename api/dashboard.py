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


def _can_enhance_validation(validation) -> bool:
    """
    Check if a validation can be enhanced.

    Returns False if:
    - File path is invalid (e.g., "unknown", empty, or None)
    - File path doesn't exist
    - Status is not APPROVED
    """
    from core.database import ValidationStatus

    # Check status
    if validation.status != ValidationStatus.APPROVED:
        return False

    # Check file path validity
    if not validation.file_path or validation.file_path.strip() == "":
        return False

    # Check if file path is a placeholder (contains or ends with "unknown")
    file_path = Path(validation.file_path)
    if file_path.name.lower() == "unknown" or validation.file_path.lower() == "unknown":
        return False

    # Check if file exists
    if not file_path.exists():
        return False

    return True


def _get_cannot_enhance_reason(validation) -> str:
    """Get a human-readable reason why a validation cannot be enhanced."""
    from core.database import ValidationStatus

    if validation.status != ValidationStatus.APPROVED:
        return f"Validation must be approved before enhancement (current status: {validation.status})"

    if not validation.file_path or validation.file_path.strip() == "":
        return "Validation has no valid file path. This validation was created from content upload without a file reference."

    # Check if file path is a placeholder
    file_path = Path(validation.file_path)
    if file_path.name.lower() == "unknown" or validation.file_path.lower() == "unknown":
        return "Validation has no valid file path. This validation was created from content upload without a file reference."

    if not file_path.exists():
        return f"File does not exist: {validation.file_path}"

    return "Enhancement not available"

def _get_source_context(file_path: str, scope: str = None) -> dict:
    """
    Get complete source file content with optional target line highlighting.

    Returns a dict with:
    - lines: list of (line_number, content) tuples for the ENTIRE file
    - target_line: the main line number if scope specifies one (for highlighting)
    - file_exists: whether the file was found
    - error: any error message
    """
    import re

    result = {
        "lines": [],
        "target_line": None,
        "file_exists": False,
        "error": None,
        "file_path": file_path
    }

    try:
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            result["error"] = f"File not found: {file_path}"
            return result

        result["file_exists"] = True

        # Read file content
        try:
            content = file_path_obj.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            content = file_path_obj.read_text(encoding='latin-1')

        all_lines = content.split('\n')

        # Parse scope to determine target line for highlighting
        target_line = None
        if scope:
            # Try to parse scope formats like "line:42", "lines:10-20", "section:intro"
            line_match = re.match(r'line[s]?:(\d+)(?:-(\d+))?', scope, re.IGNORECASE)
            if line_match:
                target_line = int(line_match.group(1))

        result["target_line"] = target_line

        # Return ALL lines with 1-based line numbers
        for i, line in enumerate(all_lines):
            result["lines"].append((i + 1, line))

        return result

    except Exception as e:
        result["error"] = str(e)
        return result


def _can_apply_recommendation(recommendation, validation) -> bool:
    """Check if a single recommendation can be applied."""
    from core.database import RecommendationStatus, ValidationStatus

    # Must be in a reviewable state (APPROVED is the accepted state)
    if recommendation.status not in [
        RecommendationStatus.PENDING,
        RecommendationStatus.PROPOSED,
        RecommendationStatus.APPROVED,
    ]:
        return False

    # Validation must exist and have a valid file
    if not validation:
        return False

    if not validation.file_path or validation.file_path.strip() == "":
        return False

    file_path = Path(validation.file_path)
    if file_path.name.lower() == "unknown" or validation.file_path.lower() == "unknown":
        return False

    if not file_path.exists():
        return False

    return True


def _get_cannot_apply_reason(recommendation, validation) -> str:
    """Get reason why a recommendation cannot be applied."""
    from core.database import RecommendationStatus

    if recommendation.status == RecommendationStatus.APPLIED:
        return "This recommendation has already been applied"

    if recommendation.status == RecommendationStatus.REJECTED:
        return "This recommendation was rejected and cannot be applied"

    if not validation:
        return "No validation found for this recommendation"

    if not validation.file_path or validation.file_path.strip() == "":
        return "Validation has no valid file path"

    file_path = Path(validation.file_path)
    if file_path.name.lower() == "unknown" or validation.file_path.lower() == "unknown":
        return "Validation has no valid file path (placeholder value)"

    if not file_path.exists():
        return f"Source file not found: {validation.file_path}"

    return "Cannot apply recommendation"


templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

# Create router
router = APIRouter(prefix="/dashboard", tags=["dashboard"])


# Form dependency classes - FastAPI uses class names for OpenAPI schema naming
# Note: We avoid using Annotated inside __init__ due to issues with
# "from __future__ import annotations" and runtime type evaluation.
class DashboardReviewForm:
    """Form data for reviewing a single recommendation."""

    def __init__(
        self,
        action: str = Form(..., description="Review action: approve, reject, accept, or pending"),
        reviewer: str = Form("dashboard_user", description="Name of the reviewer"),
        notes: str = Form(None, description="Optional review notes"),
    ):
        self.action = action
        self.reviewer = reviewer
        self.notes = notes


class DashboardBulkReviewForm:
    """Form data for bulk reviewing multiple recommendations."""

    def __init__(
        self,
        recommendation_ids: str = Form(..., description="Comma-separated recommendation IDs"),
        action: str = Form(..., description="Review action: approve, reject, or accept"),
        reviewer: str = Form("dashboard_user", description="Name of the reviewer"),
        notes: str = Form(None, description="Optional review notes"),
    ):
        self.recommendation_ids = recommendation_ids
        self.action = action
        self.reviewer = reviewer
        self.notes = notes


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

        # Check if validation can be enhanced
        can_enhance = _can_enhance_validation(validation)
        validation_dict = validation.to_dict()
        validation_dict['can_enhance'] = can_enhance

        # Add reason if cannot enhance
        if not can_enhance:
            validation_dict['cannot_enhance_reason'] = _get_cannot_enhance_reason(validation)

        return templates.TemplateResponse(
            "validation_detail_enhanced.html",
            {
                "request": request,
                "validation": validation_dict,
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
    """View detailed recommendation with audit trail, related recommendations, and source context."""
    try:
        recommendation = db_manager.get_recommendation(recommendation_id)
        if not recommendation:
            raise HTTPException(status_code=404, detail="Recommendation not found")

        validation = db_manager.get_validation_result(recommendation.validation_id)
        audit_logs = db_manager.list_audit_logs(recommendation_id=recommendation_id)

        # Get related recommendations (other recommendations for the same validation)
        related_recommendations = []
        if recommendation.validation_id:
            all_recs = db_manager.list_recommendations(validation_id=recommendation.validation_id)
            related_recommendations = [
                r.to_dict() for r in all_recs
                if r.id != recommendation_id
            ][:10]  # Limit to 10 related recommendations

        # Get source file context if file exists
        source_context = None
        if validation and validation.file_path:
            source_context = _get_source_context(
                validation.file_path,
                recommendation.scope
            )

        # Check if this recommendation can be applied
        can_apply = _can_apply_recommendation(recommendation, validation)
        cannot_apply_reason = None
        if not can_apply:
            cannot_apply_reason = _get_cannot_apply_reason(recommendation, validation)

        rec_dict = recommendation.to_dict()
        rec_dict['can_apply'] = can_apply
        rec_dict['cannot_apply_reason'] = cannot_apply_reason

        return templates.TemplateResponse(
            "recommendation_detail.html",
            {
                "request": request,
                "recommendation": rec_dict,
                "validation": validation.to_dict() if validation else None,
                "audit_logs": [log.to_dict() for log in audit_logs],
                "related_recommendations": related_recommendations,
                "source_context": source_context,
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
    review_data: DashboardReviewForm = Depends(),
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
    bulk_data: DashboardBulkReviewForm = Depends(),
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
    """View audit logs."""
    try:
        audit_logs = db_manager.list_audit_logs(
            action=action,
            limit=page_size * page
        )

        # Simple pagination
        start = (page - 1) * page_size
        end = start + page_size
        page_logs = audit_logs[start:end]

        # Convert to dicts for template
        logs_data = []
        for log in page_logs:
            if hasattr(log, 'to_dict'):
                logs_data.append(log.to_dict())
            else:
                logs_data.append({
                    "action": getattr(log, 'action', ''),
                    "actor": getattr(log, 'actor', 'system'),
                    "actor_type": getattr(log, 'actor_type', 'system'),
                    "created_at": getattr(log, 'created_at', ''),
                    "notes": getattr(log, 'notes', '')
                })

        return templates.TemplateResponse(
            "audit_logs.html",
            {
                "request": request,
                "logs": logs_data,
                "action_filter": action,
                "page": page,
                "page_size": page_size,
                "has_next": len(audit_logs) > end,
                "has_prev": page > 1,
            }
        )
    except Exception:
        logger.exception("Failed to load audit logs")
        raise HTTPException(status_code=500, detail="Failed to load audit logs")


@router.get("/monitoring", response_class=HTMLResponse)
async def dashboard_monitoring(request: Request):
    """Performance monitoring dashboard."""
    try:
        return templates.TemplateResponse(
            "monitoring.html",
            {
                "request": request,
            }
        )
    except Exception:
        logger.exception("Failed to load monitoring dashboard")
        raise HTTPException(status_code=500, detail="Failed to load monitoring dashboard")


# Include monitoring routes
from api.dashboard import routes_monitoring
router.include_router(routes_monitoring.router)
