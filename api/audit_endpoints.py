# file: api/audit_endpoints.py
"""
Audit and Rollback API endpoints.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from agents.enhancement_history import get_history_manager
from core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/audit", tags=["audit"])


class RollbackRequest(BaseModel):
    """Request to rollback an enhancement."""
    enhancement_id: str
    rolled_back_by: str
    confirmation: bool


@router.get("/enhancements")
async def list_enhancements(
    file_path: Optional[str] = None,
    limit: int = 50
):
    """List enhancement history."""
    try:
        history = get_history_manager()
        records = history.list_enhancements(file_path=file_path, limit=limit)

        return {
            "success": True,
            "enhancements": [r.to_dict() for r in records],
            "total": len(records)
        }

    except Exception as e:
        logger.exception("Failed to list enhancements")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/enhancements/{enhancement_id}")
async def get_enhancement(enhancement_id: str):
    """Get specific enhancement record."""
    try:
        history = get_history_manager()
        record = history.get_enhancement_record(enhancement_id)

        if not record:
            raise HTTPException(status_code=404, detail="Enhancement not found")

        return {
            "success": True,
            "enhancement": record.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get enhancement {enhancement_id}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rollback")
async def rollback_enhancement(request: RollbackRequest):
    """Rollback an enhancement."""
    try:
        if not request.confirmation:
            raise HTTPException(
                status_code=400,
                detail="Confirmation required"
            )

        history = get_history_manager()
        success = history.rollback_enhancement(
            request.enhancement_id,
            request.rolled_back_by
        )

        if success:
            logger.info(
                f"Rolled back enhancement {request.enhancement_id} "
                f"by {request.rolled_back_by}"
            )
            return {
                "success": True,
                "message": "Enhancement rolled back successfully"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="Rollback failed - point not found or expired"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to rollback {request.enhancement_id}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup")
async def cleanup_expired_rollbacks():
    """Cleanup expired rollback points."""
    try:
        history = get_history_manager()
        count = history.cleanup_expired_rollbacks()

        return {
            "success": True,
            "message": f"Cleaned up {count} expired rollback points",
            "count": count
        }

    except Exception as e:
        logger.exception("Failed to cleanup rollbacks")
        raise HTTPException(status_code=500, detail=str(e))
