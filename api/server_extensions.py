# file: tbcv/api/server_extensions.py
"""
Server extensions for WebSocket and export functionality.
This module extends the main server with missing critical features.
"""

from __future__ import annotations

import json
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional

from .websocket_endpoints import websocket_endpoint, connection_manager
from .export_endpoints import router as export_router

# Create router for WebSocket endpoints
websocket_router = APIRouter(tags=["websocket"])

@websocket_router.websocket("/ws/workflow/{workflow_id}")
async def workflow_progress_websocket(websocket: WebSocket, workflow_id: str):
    """
    WebSocket endpoint for real-time workflow progress updates (O05, I05, I20).
    
    Clients can connect to receive real-time updates about:
    - Workflow status changes (started, paused, resumed, completed, failed)
    - Individual file progress 
    - Error notifications
    - Performance metrics
    
    Clients can also send commands:
    - pause_workflow: Pause the workflow
    - resume_workflow: Resume the workflow  
    - cancel_workflow: Cancel the workflow
    - ping: Keep connection alive
    """
    await websocket_endpoint(websocket, workflow_id)

@websocket_router.websocket("/ws/live-dashboard")
async def dashboard_live_updates(websocket: WebSocket):
    """
    WebSocket endpoint for live dashboard updates.
    Broadcasts dashboard metrics and status updates to all connected clients.
    """
    await websocket.accept()
    
    try:
        # Send initial dashboard state
        from core.database import db_manager
        
        initial_state = {
            "type": "dashboard_state",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "pending_validations": len(db_manager.list_validation_results(limit=1000)),
                "pending_recommendations": len(db_manager.list_recommendations(status="pending", limit=1000)),
                "active_workflows": len(db_manager.list_workflows(state="running", limit=100)),
            }
        }
        
        await websocket.send_text(json.dumps(initial_state))
        
        # Keep connection alive and send periodic updates
        while True:
            try:
                # Wait for client messages or timeout after 30 seconds
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }))
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": str(e)
                }))
                
    except Exception:
        pass  # Connection closed
    
# API endpoints for workflow control
control_router = APIRouter(prefix="/api/workflows", tags=["workflow-control"])

@control_router.post("/{workflow_id}/pause")
async def pause_workflow(workflow_id: str):
    """Pause a running workflow."""
    from core.database import db_manager
    
    workflow = db_manager.get_workflow(workflow_id)
    if not workflow:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    db_manager.update_workflow_state(workflow_id, "paused")
    
    # Notify WebSocket clients
    await connection_manager.send_workflow_status(
        workflow_id, "paused", message="Workflow paused via API"
    )
    
    return {"status": "paused", "workflow_id": workflow_id}

@control_router.post("/{workflow_id}/resume")
async def resume_workflow(workflow_id: str):
    """Resume a paused workflow."""
    from core.database import db_manager
    
    workflow = db_manager.get_workflow(workflow_id)
    if not workflow:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    db_manager.update_workflow_state(workflow_id, "running")
    
    # Notify WebSocket clients
    await connection_manager.send_workflow_status(
        workflow_id, "running", message="Workflow resumed via API"
    )
    
    return {"status": "running", "workflow_id": workflow_id}

@control_router.post("/{workflow_id}/cancel") 
async def cancel_workflow(workflow_id: str):
    """Cancel a workflow."""
    from core.database import db_manager
    
    workflow = db_manager.get_workflow(workflow_id)
    if not workflow:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    db_manager.update_workflow_state(workflow_id, "cancelled")
    
    # Notify WebSocket clients
    await connection_manager.send_workflow_status(
        workflow_id, "cancelled", message="Workflow cancelled via API"
    )
    
    return {"status": "cancelled", "workflow_id": workflow_id}

@control_router.get("/{workflow_id}/status")
async def get_workflow_status(workflow_id: str):
    """Get current workflow status and progress."""
    from core.database import db_manager
    
    workflow = db_manager.get_workflow(workflow_id)
    if not workflow:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Get associated validations for progress calculation
    validations = db_manager.list_validation_results(workflow_id=workflow_id, limit=1000)
    
    return {
        "workflow": workflow.to_dict(),
        "progress": {
            "total_files": workflow.total_steps,
            "completed_files": workflow.current_step,
            "progress_percent": workflow.progress_percent,
            "validations_count": len(validations)
        }
    }

# Combine all extension routers
def get_extension_routers():
    """Get all extension routers to include in main app."""
    return [
        websocket_router,
        export_router,
        control_router
    ]

# Helper functions for integration with existing server
async def notify_dashboard_update(update_type: str, data: dict):
    """Helper to notify dashboard WebSocket clients of updates."""
    # This would be called from other parts of the system
    # to notify connected dashboard clients of changes
    pass

def setup_websocket_handlers(app):
    """Setup WebSocket handlers in the main FastAPI app."""
    # Include all extension routers
    for router in get_extension_routers():
        app.include_router(router)
    
    return app
