"""
Workflow manager for orchestrating complex validation and enhancement workflows.

This module provides thread-safe workflow execution, progress tracking, and
control operations (pause/resume/cancel) for long-running operations.
"""

import threading
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from pathlib import Path

from core.logging import get_logger
from core.database import DatabaseManager, WorkflowState

logger = get_logger(__name__)


class WorkflowManager:
    """
    Manager for workflow execution and control.

    Provides thread-safe workflow operations including:
    - Background workflow execution
    - Pause/resume/cancel control
    - Progress tracking and reporting
    - Workflow status monitoring
    """

    def __init__(self, db_manager: DatabaseManager, agent_registry=None):
        """
        Initialize workflow manager.

        Args:
            db_manager: Database manager instance
            agent_registry: Optional agent registry for validation/enhancement
        """
        self.db_manager = db_manager
        self.agent_registry = agent_registry
        self.logger = get_logger(__name__)

        # Thread-safe workflow tracking
        self._lock = threading.Lock()
        self._running_workflows: Dict[str, threading.Thread] = {}
        self._workflow_control: Dict[str, Dict[str, Any]] = {}

    def execute_workflow(self, workflow_id: str) -> None:
        """
        Execute workflow in background.

        This method is meant to be called in a separate thread.

        Args:
            workflow_id: ID of workflow to execute
        """
        try:
            # Get workflow from database
            workflow = self.db_manager.get_workflow(workflow_id)
            if not workflow:
                self.logger.error(f"Workflow {workflow_id} not found")
                return

            # Initialize control state
            with self._lock:
                self._workflow_control[workflow_id] = {
                    "should_pause": False,
                    "should_cancel": False,
                    "is_running": True
                }

            # Update workflow state to running
            self.db_manager.update_workflow(workflow_id, state=WorkflowState.RUNNING)

            self.logger.info(f"Starting workflow {workflow_id} (type={workflow.type})")

            # Execute based on workflow type
            if workflow.type == "validate_directory":
                self._execute_validate_directory(workflow_id, workflow.input_params)
            elif workflow.type == "batch_enhance":
                self._execute_batch_enhance(workflow_id, workflow.input_params)
            elif workflow.type == "full_audit":
                self._execute_full_audit(workflow_id, workflow.input_params)
            elif workflow.type == "recommendation_batch":
                self._execute_recommendation_batch(workflow_id, workflow.input_params)
            else:
                raise ValueError(f"Unknown workflow type: {workflow.type}")

            # Mark as completed
            with self._lock:
                if not self._workflow_control[workflow_id]["should_cancel"]:
                    self.db_manager.update_workflow(
                        workflow_id,
                        state=WorkflowState.COMPLETED,
                        completed_at=datetime.now(timezone.utc)
                    )
                    self.logger.info(f"Workflow {workflow_id} completed successfully")

        except Exception as e:
            self.logger.error(f"Workflow {workflow_id} failed: {e}")
            self.db_manager.update_workflow(
                workflow_id,
                state=WorkflowState.FAILED,
                error_message=str(e),
                completed_at=datetime.now(timezone.utc)
            )

        finally:
            # Clean up control state
            with self._lock:
                if workflow_id in self._workflow_control:
                    self._workflow_control[workflow_id]["is_running"] = False
                if workflow_id in self._running_workflows:
                    del self._running_workflows[workflow_id]

    def pause_workflow(self, workflow_id: str) -> WorkflowState:
        """
        Pause a running workflow.

        Args:
            workflow_id: ID of workflow to pause

        Returns:
            New workflow state

        Raises:
            ValueError: If workflow cannot be paused
        """
        with self._lock:
            if workflow_id not in self._workflow_control:
                raise ValueError(f"Workflow {workflow_id} is not running")

            workflow = self.db_manager.get_workflow(workflow_id)
            if workflow.state != WorkflowState.RUNNING:
                raise ValueError(f"Workflow {workflow_id} is not in running state")

            self._workflow_control[workflow_id]["should_pause"] = True
            self.db_manager.update_workflow(workflow_id, state=WorkflowState.PAUSED)

            self.logger.info(f"Workflow {workflow_id} paused")
            return WorkflowState.PAUSED

    def resume_workflow(self, workflow_id: str) -> WorkflowState:
        """
        Resume a paused workflow.

        Args:
            workflow_id: ID of workflow to resume

        Returns:
            New workflow state

        Raises:
            ValueError: If workflow cannot be resumed
        """
        with self._lock:
            workflow = self.db_manager.get_workflow(workflow_id)
            if workflow.state != WorkflowState.PAUSED:
                raise ValueError(f"Workflow {workflow_id} is not paused")

            if workflow_id in self._workflow_control:
                self._workflow_control[workflow_id]["should_pause"] = False

            self.db_manager.update_workflow(workflow_id, state=WorkflowState.RUNNING)

            self.logger.info(f"Workflow {workflow_id} resumed")
            return WorkflowState.RUNNING

    def cancel_workflow(self, workflow_id: str) -> WorkflowState:
        """
        Cancel a running or paused workflow.

        Args:
            workflow_id: ID of workflow to cancel

        Returns:
            New workflow state

        Raises:
            ValueError: If workflow cannot be cancelled
        """
        with self._lock:
            workflow = self.db_manager.get_workflow(workflow_id)
            if workflow.state in [WorkflowState.COMPLETED, WorkflowState.FAILED, WorkflowState.CANCELLED]:
                raise ValueError(f"Workflow {workflow_id} is already finished")

            if workflow_id in self._workflow_control:
                self._workflow_control[workflow_id]["should_cancel"] = True

            self.db_manager.update_workflow(
                workflow_id,
                state=WorkflowState.CANCELLED,
                completed_at=datetime.now(timezone.utc)
            )

            self.logger.info(f"Workflow {workflow_id} cancelled")
            return WorkflowState.CANCELLED

    def get_workflow_summary(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get workflow summary for dashboards.

        Args:
            workflow_id: ID of workflow

        Returns:
            Summary dictionary with progress metrics
        """
        workflow = self.db_manager.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        # Calculate duration
        duration_seconds = 0.0
        if workflow.created_at:
            # Ensure both datetimes are timezone-aware
            created_at = workflow.created_at
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)

            end_time = workflow.completed_at
            if end_time is None:
                end_time = datetime.now(timezone.utc)
            elif end_time.tzinfo is None:
                end_time = end_time.replace(tzinfo=timezone.utc)

            duration_seconds = (end_time - created_at).total_seconds()

        # Calculate ETA if running
        eta_seconds = 0.0
        if workflow.state == WorkflowState.RUNNING and workflow.progress_percent > 0:
            elapsed = duration_seconds
            estimated_total = elapsed / (workflow.progress_percent / 100.0)
            eta_seconds = max(0, estimated_total - elapsed)

        # Count errors
        errors_count = 0
        if workflow.error_message:
            errors_count = 1

        return {
            "progress_percent": workflow.progress_percent or 0,
            "files_processed": workflow.current_step or 0,
            "files_total": workflow.total_steps or 0,
            "errors_count": errors_count,
            "duration_seconds": duration_seconds,
            "eta_seconds": eta_seconds
        }

    def generate_workflow_report(
        self,
        workflow_id: str,
        include_details: bool = True
    ) -> Dict[str, Any]:
        """
        Generate detailed workflow report.

        Args:
            workflow_id: ID of workflow
            include_details: Whether to include detailed metrics

        Returns:
            Report dictionary with metrics and statistics
        """
        workflow = self.db_manager.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        report = {
            "workflow_id": workflow_id,
            "workflow_type": workflow.type,
            "state": workflow.state.value,
            "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
            "total_steps": workflow.total_steps or 0,
            "current_step": workflow.current_step or 0,
            "progress_percent": workflow.progress_percent or 0,
            "error_message": workflow.error_message
        }

        if include_details:
            # Add detailed metrics
            summary = self.get_workflow_summary(workflow_id)
            report["metrics"] = {
                "duration_seconds": summary["duration_seconds"],
                "files_processed": summary["files_processed"],
                "files_total": summary["files_total"],
                "errors_count": summary["errors_count"]
            }

            # Add metadata
            if workflow.workflow_metadata:
                report["metadata"] = workflow.workflow_metadata

        return report

    def _check_control_signals(self, workflow_id: str) -> bool:
        """
        Check if workflow should pause or cancel.

        Args:
            workflow_id: ID of workflow to check

        Returns:
            True if workflow should continue, False if cancelled
        """
        with self._lock:
            if workflow_id not in self._workflow_control:
                return True

            control = self._workflow_control[workflow_id]

            # Check for cancellation
            if control["should_cancel"]:
                return False

            # Check for pause
            while control["should_pause"]:
                # Release lock and wait
                self._lock.release()
                time.sleep(0.1)
                self._lock.acquire()

                # Check if cancelled while paused
                if control["should_cancel"]:
                    return False

            return True

    def _update_progress(
        self,
        workflow_id: str,
        current_step: int,
        total_steps: int
    ) -> None:
        """
        Update workflow progress.

        Args:
            workflow_id: ID of workflow
            current_step: Current step number
            total_steps: Total number of steps
        """
        progress_percent = int((current_step / total_steps) * 100) if total_steps > 0 else 0

        self.db_manager.update_workflow(
            workflow_id,
            current_step=current_step,
            total_steps=total_steps,
            progress_percent=progress_percent
        )

    def _execute_validate_directory(
        self,
        workflow_id: str,
        params: Dict[str, Any]
    ) -> None:
        """
        Execute validate_directory workflow.

        Args:
            workflow_id: ID of workflow
            params: Workflow parameters with directory_path and recursive
        """
        directory_path = params.get("directory_path")
        recursive = params.get("recursive", True)

        if not directory_path:
            raise ValueError("directory_path is required")

        # Find all markdown files
        path = Path(directory_path)
        if not path.exists():
            raise ValueError(f"Directory not found: {directory_path}")

        pattern = "**/*.md" if recursive else "*.md"
        files = list(path.glob(pattern))

        total_steps = len(files)
        self._update_progress(workflow_id, 0, total_steps)

        # Process each file
        for i, file_path in enumerate(files):
            # Check control signals
            if not self._check_control_signals(workflow_id):
                break

            # TODO: Perform actual validation when agent_registry is available
            # For now, just simulate
            time.sleep(0.01)

            # Update progress
            self._update_progress(workflow_id, i + 1, total_steps)

    def _execute_batch_enhance(
        self,
        workflow_id: str,
        params: Dict[str, Any]
    ) -> None:
        """
        Execute batch_enhance workflow.

        Args:
            workflow_id: ID of workflow
            params: Workflow parameters with validation_ids
        """
        validation_ids = params.get("validation_ids", [])

        if not validation_ids:
            raise ValueError("validation_ids is required")

        total_steps = len(validation_ids)
        self._update_progress(workflow_id, 0, total_steps)

        # Process each validation
        for i, validation_id in enumerate(validation_ids):
            # Check control signals
            if not self._check_control_signals(workflow_id):
                break

            # TODO: Perform actual enhancement when agent_registry is available
            # For now, just simulate
            time.sleep(0.01)

            # Update progress
            self._update_progress(workflow_id, i + 1, total_steps)

    def _execute_full_audit(
        self,
        workflow_id: str,
        params: Dict[str, Any]
    ) -> None:
        """
        Execute full_audit workflow.

        Args:
            workflow_id: ID of workflow
            params: Workflow parameters with directory_path
        """
        # Full audit is validate + enhance all files
        directory_path = params.get("directory_path")

        if not directory_path:
            raise ValueError("directory_path is required")

        # Step 1: Validate directory
        self._execute_validate_directory(workflow_id, params)

        # Step 2: Enhance all validated files
        # TODO: Implement when agent_registry is available

    def _execute_recommendation_batch(
        self,
        workflow_id: str,
        params: Dict[str, Any]
    ) -> None:
        """
        Execute recommendation_batch workflow.

        Args:
            workflow_id: ID of workflow
            params: Workflow parameters with recommendation_ids
        """
        recommendation_ids = params.get("recommendation_ids", [])

        if not recommendation_ids:
            raise ValueError("recommendation_ids is required")

        total_steps = len(recommendation_ids)
        self._update_progress(workflow_id, 0, total_steps)

        # Process each recommendation
        for i, recommendation_id in enumerate(recommendation_ids):
            # Check control signals
            if not self._check_control_signals(workflow_id):
                break

            # TODO: Perform actual recommendation processing
            # For now, just simulate
            time.sleep(0.01)

            # Update progress
            self._update_progress(workflow_id, i + 1, total_steps)
