# file: api/additional_endpoints.py
"""
Additional API endpoints for TBCV.

This module is reserved for future expansion endpoints that don't fit
into the main categories (validation, enhancement, workflows, etc.).

Status: NOT YET IMPLEMENTED
"""

from fastapi import APIRouter

# Create router for when this is implemented
router = APIRouter(prefix="/additional", tags=["additional"])


# Placeholder - to be implemented
@router.get("/")
async def additional_info():
    """Information about additional functionality."""
    return {
        "status": "not_implemented",
        "message": "Additional endpoints are reserved for future features"
    }
