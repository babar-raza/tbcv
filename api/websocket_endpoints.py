from __future__ import annotations

# file: tbcv/api/websocket_endpoints.py
"""
WebSocket endpoints for real-time progress updates (O05, I05, I20).
This module provides WebSocket support for the TBCV system.
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Set
from fastapi import WebSocket, WebSocketDisconnect
from core.logging import get_logger

logger = get_logger(__name__)

PING_INTERVAL = 30  # seconds

class ConnectionManager:
    """Manages WebSocket connections for real-time progress updates."""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.connection_workflows: Dict[WebSocket, str] = {}
    
    async def connect(self, websocket: WebSocket, workflow_id: str):
        """Accept a new WebSocket connection for a specific workflow."""
        await websocket.accept()
        
        if workflow_id not in self.active_connections:
            self.active_connections[workflow_id] = set()
        
        self.active_connections[workflow_id].add(websocket)
        self.connection_workflows[websocket] = workflow_id
        
        logger.info(f"WebSocket connected for workflow {workflow_id}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        workflow_id = self.connection_workflows.pop(websocket, None)
        if workflow_id and workflow_id in self.active_connections:
            self.active_connections[workflow_id].discard(websocket)
            if not self.active_connections[workflow_id]:
                del self.active_connections[workflow_id]
        
        logger.info(f"WebSocket disconnected for workflow {workflow_id}")
    
    async def send_progress_update(self, workflow_id: str, data: Dict[str, Any]):
        """Send progress update to all connections listening to a workflow."""
        if workflow_id not in self.active_connections:
            return
        
        message = json.dumps({
            "type": "progress_update",
            "workflow_id": workflow_id,
            "timestamp": data.get("timestamp", ""),
            "data": data
        })
        
        # Send to all connections for this workflow
        disconnected = []
        for connection in self.active_connections[workflow_id]:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(f"Failed to send message to WebSocket: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
    
    async def send_workflow_status(self, workflow_id: str, status: str, **kwargs):
        """Send workflow status update."""
        data = {
            "status": status,
            "timestamp": kwargs.get("timestamp", ""),
            **kwargs
        }
        await self.send_progress_update(workflow_id, data)
    
    async def send_file_progress(self, workflow_id: str, file_path: str, status: str, **kwargs):
        """Send individual file progress update."""
        data = {
            "file_path": file_path,
            "file_status": status,
            "timestamp": kwargs.get("timestamp", ""),
            **kwargs
        }
        await self.send_progress_update(workflow_id, data)

# Global connection manager
connection_manager = ConnectionManager()

async def websocket_endpoint(websocket: WebSocket, workflow_id: str):
    """
    WebSocket endpoint for real-time progress updates.
    Clients can connect to receive updates about workflow progress.
    """
    # Accept connection immediately to avoid 403
    await websocket.accept()
    
    # Create a heartbeat task to keep connection alive
    heartbeat_task = None
    
    async def send_heartbeat():
        """Send periodic pings to keep connection alive"""
        try:
            while True:
                await asyncio.sleep(30)  # Send heartbeat every 30 seconds
                try:
                    await websocket.send_text(json.dumps({
                        "type": "heartbeat",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }))
                except Exception:
                    break
        except asyncio.CancelledError:
            pass
    
    try:
        # Register connection after accepting
        if workflow_id not in connection_manager.active_connections:
            connection_manager.active_connections[workflow_id] = set()
        
        connection_manager.active_connections[workflow_id].add(websocket)
        connection_manager.connection_workflows[websocket] = workflow_id
        
        logger.info(f"WebSocket connected for workflow {workflow_id}")
        
        # Start heartbeat task
        heartbeat_task = asyncio.create_task(send_heartbeat())
        
        # Send initial connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "workflow_id": workflow_id,
            "message": "Connected to workflow progress updates"
        }))
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages from client (e.g., pause/resume commands)
                # Use timeout to allow checking if connection is still alive
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                message = json.loads(data)
                
                # Handle client commands
                if message.get("type") == "pause_workflow":
                    await handle_workflow_command(workflow_id, "pause")
                elif message.get("type") == "resume_workflow":
                    await handle_workflow_command(workflow_id, "resume")
                elif message.get("type") == "cancel_workflow":
                    await handle_workflow_command(workflow_id, "cancel")
                elif message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }))
                elif message.get("type") == "pong":
                    # Client acknowledged heartbeat
                    pass
                    
            except asyncio.TimeoutError:
                # No message received in timeout period, continue loop
                # The heartbeat task will keep connection alive
                continue
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected normally for workflow {workflow_id}")
                break
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON from WebSocket: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": str(e)
                }))
                
    except Exception as e:
        logger.error(f"WebSocket error for workflow {workflow_id}: {e}", exc_info=True)
    finally:
        # Cancel heartbeat task
        if heartbeat_task:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
        
        connection_manager.disconnect(websocket)

async def handle_workflow_command(workflow_id: str, command: str):
    """Handle workflow control commands from WebSocket clients."""
    from core.database import db_manager
    
    try:
        workflow = db_manager.get_workflow(workflow_id)
        if not workflow:
            return
        
        if command == "pause":
            db_manager.update_workflow_state(workflow_id, "paused")
            await connection_manager.send_workflow_status(
                workflow_id, "paused", message="Workflow paused by user"
            )
        elif command == "resume":
            db_manager.update_workflow_state(workflow_id, "running")
            await connection_manager.send_workflow_status(
                workflow_id, "running", message="Workflow resumed by user"
            )
        elif command == "cancel":
            db_manager.update_workflow_state(workflow_id, "cancelled")
            await connection_manager.send_workflow_status(
                workflow_id, "cancelled", message="Workflow cancelled by user"
            )
            
    except Exception as e:
        logger.error(f"Error handling workflow command {command} for {workflow_id}: {e}")

# Helper functions for agents to send progress updates
async def notify_workflow_started(workflow_id: str, total_files: int = 0):
    """Notify WebSocket clients that a workflow has started."""
    await connection_manager.send_workflow_status(
        workflow_id, "started", 
        total_files=total_files,
        files_completed=0,
        message="Workflow started"
    )

async def notify_file_progress(workflow_id: str, file_path: str, status: str, **kwargs):
    """Notify WebSocket clients about individual file progress."""
    await connection_manager.send_file_progress(
        workflow_id, file_path, status, **kwargs
    )

async def notify_workflow_completed(workflow_id: str, **kwargs):
    """Notify WebSocket clients that a workflow has completed."""
    await connection_manager.send_workflow_status(
        workflow_id, "completed", 
        message="Workflow completed successfully",
        **kwargs
    )

async def notify_workflow_error(workflow_id: str, error: str):
    """Notify WebSocket clients about workflow errors."""
    await connection_manager.send_workflow_status(
        workflow_id, "error",
        error=error,
        message=f"Workflow failed: {error}"
    )
