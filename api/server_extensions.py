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

    Uses MCP async client to stream workflow status updates.

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
    from api.mcp_helpers import get_api_mcp_client
    import asyncio

    await websocket.accept()
    mcp = await get_api_mcp_client()

    # Track last known workflow status
    last_status = None

    try:
        while True:
            # Get workflow status from MCP
            try:
                result = await mcp.get_workflow(workflow_id)
                workflow = result.get("workflow", {})
                current_status = workflow.get("status", "unknown")

                # Send update if status changed or first time
                if current_status != last_status:
                    await websocket.send_json({
                        "type": "workflow_update",
                        "workflow_id": workflow_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "data": workflow
                    })
                    last_status = current_status

                # Exit if workflow completed or failed
                if current_status in ["completed", "failed", "cancelled"]:
                    await websocket.send_json({
                        "type": "workflow_complete",
                        "workflow_id": workflow_id,
                        "status": current_status,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    break

            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Failed to fetch workflow: {str(e)}"
                })

            # Check for client commands
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.5)
                message = json.loads(data)

                if message.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    })
            except asyncio.TimeoutError:
                pass  # No message received, continue
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON"
                })

    except WebSocketDisconnect:
        pass  # Client disconnected
    except Exception as e:
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass  # Connection may be closed

@websocket_router.websocket("/ws/live-dashboard")
async def dashboard_live_updates(websocket: WebSocket):
    """
    WebSocket endpoint for live dashboard updates.

    Uses MCP async client to stream dashboard metrics and status updates.
    Broadcasts dashboard metrics and status updates to all connected clients.
    """
    from api.mcp_helpers import get_api_mcp_client
    import asyncio

    await websocket.accept()
    mcp = await get_api_mcp_client()

    try:
        # Send initial dashboard state using MCP
        try:
            validations = await mcp.list_validations(limit=1000)
            recommendations = await mcp.list_recommendations(limit=1000, status="pending")
            workflows = await mcp.list_workflows(limit=100, status="running")

            initial_state = {
                "type": "dashboard_state",
                "timestamp": datetime.utcnow().isoformat(),
                "data": {
                    "pending_validations": validations.get("total", 0),
                    "pending_recommendations": recommendations.get("total", 0),
                    "active_workflows": workflows.get("total", 0),
                }
            }

            await websocket.send_text(json.dumps(initial_state))
        except Exception as e:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"Failed to load dashboard state: {str(e)}"
            }))

        # Keep connection alive and send periodic updates
        while True:
            try:
                # Wait for client messages with timeout
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                message = json.loads(data)

                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }))
                elif message.get("type") == "refresh":
                    # Client requested dashboard refresh
                    try:
                        validations = await mcp.list_validations(limit=1000)
                        recommendations = await mcp.list_recommendations(limit=1000, status="pending")
                        workflows = await mcp.list_workflows(limit=100, status="running")

                        await websocket.send_text(json.dumps({
                            "type": "dashboard_update",
                            "timestamp": datetime.utcnow().isoformat(),
                            "data": {
                                "pending_validations": validations.get("total", 0),
                                "pending_recommendations": recommendations.get("total", 0),
                                "active_workflows": workflows.get("total", 0),
                            }
                        }))
                    except Exception as e:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": f"Failed to refresh dashboard: {str(e)}"
                        }))

            except asyncio.TimeoutError:
                # Send heartbeat after timeout
                await websocket.send_text(json.dumps({
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat()
                }))
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON"
                }))
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
