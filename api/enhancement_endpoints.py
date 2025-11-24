# file: api/enhancement_endpoints.py
"""
Enhancement API endpoints for preview-approve-apply workflow.

Provides:
- POST /api/enhance/preview - Generate preview without modifying files
- POST /api/enhance/apply - Apply approved preview
- GET /api/enhance/preview/{preview_id} - Get preview details
- DELETE /api/enhance/preview/{preview_id} - Cancel/delete preview
- GET /api/enhance/previews - List previews
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
from pathlib import Path

from agents.recommendation_enhancer import (
    RecommendationEnhancer,
    create_default_preservation_rules
)
from agents.enhancement_preview import (
    get_preview_manager,
    EnhancementPreview
)
from core.database import db_manager
from core.logging import get_logger

logger = get_logger(__name__)

# Create router
router = APIRouter(prefix="/api/enhance", tags=["enhancement"])


# ==============================================================================
# Request/Response Models
# ==============================================================================

class PreviewRequest(BaseModel):
    """Request to generate enhancement preview."""
    validation_id: str
    expiration_minutes: Optional[int] = 30
    created_by: Optional[str] = "user"


class ApplyRequest(BaseModel):
    """Request to apply enhancement."""
    preview_id: str
    user_confirmation: bool
    applied_by: Optional[str] = "user"
    create_backup: Optional[bool] = True


class PreviewResponse(BaseModel):
    """Response containing preview details."""
    success: bool
    preview_id: str
    message: str
    preview: Optional[dict] = None


class ApplyResponse(BaseModel):
    """Response for apply operation."""
    success: bool
    message: str
    file_path: Optional[str] = None
    enhancement_id: Optional[str] = None
    lines_changed: Optional[int] = None


class PreviewListResponse(BaseModel):
    """Response for list previews."""
    success: bool
    previews: List[dict]
    total: int


# ==============================================================================
# Endpoints
# ==============================================================================

@router.post("/preview", response_model=PreviewResponse)
async def generate_preview(request: PreviewRequest):
    """
    Generate enhancement preview without modifying files.

    This creates a temporary preview that expires after the specified time.
    No files are modified until the preview is explicitly applied.

    Args:
        request: PreviewRequest with validation_id

    Returns:
        PreviewResponse with preview_id and details
    """
    try:
        # Get validation record
        validation = db_manager.get_validation_result(request.validation_id)
        if not validation:
            raise HTTPException(
                status_code=404,
                detail=f"Validation {request.validation_id} not found"
            )

        # Get approved recommendations
        recommendations = db_manager.get_recommendations_by_validation(
            request.validation_id,
            status="approved"
        )

        if not recommendations:
            raise HTTPException(
                status_code=400,
                detail="No approved recommendations found for this validation"
            )

        # Read original content
        file_path = Path(validation.file_path)
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {validation.file_path}"
            )

        original_content = file_path.read_text(encoding='utf-8')

        # Create preservation rules (could be customized per file)
        preservation_rules = create_default_preservation_rules(validation.file_path)

        # Run enhancement
        enhancer = RecommendationEnhancer()
        enhancement_result = await enhancer.enhance_from_recommendations(
            content=original_content,
            recommendations=[rec.to_dict() if hasattr(rec, 'to_dict') else rec for rec in recommendations],
            preservation_rules=preservation_rules,
            file_path=validation.file_path
        )

        # Create preview
        preview_manager = get_preview_manager()
        preview = preview_manager.create_preview(
            validation_id=request.validation_id,
            file_path=validation.file_path,
            enhancement_result=enhancement_result,
            created_by=request.created_by,
            expiration_minutes=request.expiration_minutes
        )

        logger.info(
            f"Generated preview {preview.preview_id} for validation {request.validation_id} "
            f"(applied={len(preview.applied_recommendations)}, safety={preview.safety_score.get('overall_score', 0):.2f})"
        )

        return PreviewResponse(
            success=True,
            preview_id=preview.preview_id,
            message=f"Preview generated successfully (expires in {request.expiration_minutes} minutes)",
            preview=preview.to_dict()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to generate preview: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Preview generation failed: {str(e)}"
        )


@router.get("/preview/{preview_id}", response_model=PreviewResponse)
async def get_preview(preview_id: str):
    """
    Get enhancement preview details.

    Args:
        preview_id: Preview ID

    Returns:
        PreviewResponse with preview details
    """
    try:
        preview_manager = get_preview_manager()
        preview = preview_manager.get_preview(preview_id)

        if not preview:
            raise HTTPException(
                status_code=404,
                detail=f"Preview {preview_id} not found or expired"
            )

        return PreviewResponse(
            success=True,
            preview_id=preview_id,
            message="Preview retrieved successfully",
            preview=preview.to_dict()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get preview: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve preview: {str(e)}"
        )


@router.post("/apply", response_model=ApplyResponse)
async def apply_enhancement(
    request: ApplyRequest,
    background_tasks: BackgroundTasks
):
    """
    Apply approved enhancement preview.

    This modifies the actual file based on the approved preview.
    A backup is created before modification if requested.

    Args:
        request: ApplyRequest with preview_id and confirmation
        background_tasks: FastAPI background tasks

    Returns:
        ApplyResponse with result
    """
    try:
        if not request.user_confirmation:
            raise HTTPException(
                status_code=400,
                detail="User confirmation required to apply enhancement"
            )

        # Get preview
        preview_manager = get_preview_manager()
        preview = preview_manager.get_preview(request.preview_id)

        if not preview:
            raise HTTPException(
                status_code=404,
                detail=f"Preview {request.preview_id} not found or expired"
            )

        if preview.status == "applied":
            raise HTTPException(
                status_code=400,
                detail="Preview has already been applied"
            )

        if preview.status == "rejected":
            raise HTTPException(
                status_code=400,
                detail="Preview has been rejected and cannot be applied"
            )

        # Check safety score
        if not preview.is_safe_to_apply():
            raise HTTPException(
                status_code=400,
                detail=f"Preview safety score too low ({preview.safety_score.get('overall_score', 0):.2f}). Manual review required."
            )

        # Approve preview first
        preview_manager.approve_preview(request.preview_id, request.applied_by)

        # Create backup if requested
        file_path = Path(preview.file_path)
        if request.create_backup:
            backup_path = file_path.with_suffix(f"{file_path.suffix}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            backup_path.write_text(preview.original_content, encoding='utf-8')
            logger.info(f"Created backup: {backup_path}")

        # Apply enhancement (write to file)
        file_path.write_text(preview.enhanced_content, encoding='utf-8')

        # Mark preview as applied
        preview_manager.mark_applied(request.preview_id)

        # Update database - mark recommendations as applied
        for rec in preview.applied_recommendations:
            try:
                db_manager.mark_recommendation_applied(
                    rec["recommendation_id"],
                    applied_by=request.applied_by
                )
            except Exception as e:
                logger.warning(f"Failed to mark recommendation as applied: {e}")

        # Calculate lines changed
        lines_changed = (
            preview.diff_statistics.lines_added +
            preview.diff_statistics.lines_removed
            if preview.diff_statistics else 0
        )

        logger.info(
            f"Applied enhancement {request.preview_id} to {preview.file_path} "
            f"(lines_changed={lines_changed}, applied_by={request.applied_by})"
        )

        # Schedule cleanup in background
        background_tasks.add_task(
            preview_manager.cleanup_expired
        )

        return ApplyResponse(
            success=True,
            message="Enhancement applied successfully",
            file_path=preview.file_path,
            enhancement_id=request.preview_id,
            lines_changed=lines_changed
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to apply enhancement: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to apply enhancement: {str(e)}"
        )


@router.delete("/preview/{preview_id}")
async def delete_preview(preview_id: str, reason: Optional[str] = "user_cancelled"):
    """
    Delete/cancel enhancement preview.

    Args:
        preview_id: Preview ID to delete
        reason: Reason for deletion

    Returns:
        Success response
    """
    try:
        preview_manager = get_preview_manager()

        # Mark as rejected if exists
        preview = preview_manager.get_preview(preview_id)
        if preview:
            preview_manager.reject_preview(preview_id, "system", reason)

        # Delete from storage
        deleted = preview_manager.storage.delete(preview_id)

        if deleted:
            logger.info(f"Deleted preview {preview_id} (reason: {reason})")
            return {"success": True, "message": "Preview deleted successfully"}
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Preview {preview_id} not found"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to delete preview: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete preview: {str(e)}"
        )


@router.get("/previews", response_model=PreviewListResponse)
async def list_previews(
    validation_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
):
    """
    List enhancement previews with optional filters.

    Args:
        validation_id: Filter by validation ID
        status: Filter by status (pending, approved, rejected, applied)
        limit: Maximum number of previews to return

    Returns:
        PreviewListResponse with list of previews
    """
    try:
        preview_manager = get_preview_manager()
        previews = preview_manager.storage.list_previews(
            validation_id=validation_id,
            status=status
        )

        # Apply limit
        previews = previews[:limit]

        # Convert to dicts
        preview_dicts = [p.to_dict() for p in previews]

        return PreviewListResponse(
            success=True,
            previews=preview_dicts,
            total=len(preview_dicts)
        )

    except Exception as e:
        logger.exception(f"Failed to list previews: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list previews: {str(e)}"
        )


@router.post("/cleanup")
async def cleanup_expired_previews():
    """
    Cleanup expired previews (admin endpoint).

    Returns:
        Number of previews cleaned up
    """
    try:
        preview_manager = get_preview_manager()
        count = preview_manager.cleanup_expired()

        logger.info(f"Cleaned up {count} expired previews")

        return {
            "success": True,
            "message": f"Cleaned up {count} expired previews",
            "count": count
        }

    except Exception as e:
        logger.exception(f"Failed to cleanup previews: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cleanup previews: {str(e)}"
        )
