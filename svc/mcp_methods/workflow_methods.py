"""Workflow-related MCP methods."""

import threading
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from svc.mcp_methods.base import BaseMCPMethod
from core.workflow_manager import WorkflowManager
from core.database import WorkflowState


class WorkflowMethods(BaseMCPMethod):
    """Handler for workflow-related MCP methods."""

    def __init__(self, db_manager, rule_manager, agent_registry):
        super().__init__(db_manager, rule_manager, agent_registry)
        self.workflow_manager = WorkflowManager(db_manager, agent_registry)

    def handle(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle workflow method execution.

        Args:
            params: Method parameters

        Returns:
            Workflow results

        Raises:
            ValueError: If parameters are invalid
        """
        # This is called via registry, specific methods are called directly
        raise NotImplementedError("Use specific workflow methods via registry")

    def create_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new workflow.

        Args:
            params: {
                "workflow_type": str (required - validate_directory, batch_enhance, etc.),
                "params": Dict (required - workflow-specific parameters),
                "name": str (optional - workflow name),
                "description": str (optional - workflow description)
            }

        Returns:
            {
                "success": bool,
                "workflow_id": str,
                "workflow_type": str,
                "status": str,
                "created_at": str
            }
        """
        self.validate_params(
            params,
            required=["workflow_type", "params"],
            optional={"name": None, "description": None}
        )

        workflow_type = params["workflow_type"]
        workflow_params = params["params"]
        name = params.get("name")
        description = params.get("description")

        self.logger.info(f"Creating workflow: type={workflow_type}")

        # Validate workflow type
        valid_types = [
            "validate_directory",
            "batch_enhance",
            "full_audit",
            "recommendation_batch"
        ]
        if workflow_type not in valid_types:
            raise ValueError(
                f"Invalid workflow type: {workflow_type}. "
                f"Valid types: {', '.join(valid_types)}"
            )

        # Create workflow in database
        workflow = self.db_manager.create_workflow(
            workflow_type=workflow_type,
            input_params=workflow_params,
            metadata={"name": name, "description": description}
        )

        # Start workflow execution in background
        thread = threading.Thread(
            target=self.workflow_manager.execute_workflow,
            args=(workflow.id,),
            daemon=True
        )
        thread.start()

        return {
            "success": True,
            "workflow_id": workflow.id,
            "workflow_type": workflow_type,
            "status": workflow.state.value,
            "created_at": workflow.created_at.isoformat() if workflow.created_at else None
        }

    def get_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get workflow by ID.

        Args:
            params: {
                "workflow_id": str (required)
            }

        Returns:
            {
                "workflow": Dict (workflow details with full metadata)
            }
        """
        self.validate_params(params, required=["workflow_id"])

        workflow_id = params["workflow_id"]

        self.logger.info(f"Retrieving workflow: {workflow_id}")

        # Get workflow from database
        workflow = self.db_manager.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        return {
            "workflow": self._serialize_workflow(workflow)
        }

    def list_workflows(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        List workflows with filters.

        Args:
            params: {
                "limit": int (optional, default 100),
                "offset": int (optional, default 0),
                "status": str (optional - filter by status),
                "workflow_type": str (optional - filter by type),
                "created_after": str (optional - ISO 8601 datetime),
                "created_before": str (optional - ISO 8601 datetime)
            }

        Returns:
            {
                "workflows": List[Dict],
                "total": int,
                "limit": int,
                "offset": int
            }
        """
        self.validate_params(
            params,
            required=[],
            optional={
                "limit": 100,
                "offset": 0,
                "status": None,
                "workflow_type": None,
                "created_after": None,
                "created_before": None
            }
        )

        limit = params["limit"]
        offset = params["offset"]
        status = params["status"]
        workflow_type = params["workflow_type"]
        created_after = params["created_after"]
        created_before = params["created_before"]

        self.logger.info(f"Listing workflows: limit={limit}, offset={offset}")

        # Get workflows from database (with state filter if provided)
        state_enum = None
        if status:
            try:
                state_enum = status
            except (KeyError, ValueError):
                raise ValueError(f"Invalid status: {status}")

        workflows = self.db_manager.list_workflows(state=state_enum, limit=limit + offset)

        # Apply additional filters
        filtered_workflows = []
        for workflow in workflows:
            # Filter by type
            if workflow_type and workflow.type != workflow_type:
                continue

            # Filter by created_after
            if created_after:
                after_dt = datetime.fromisoformat(created_after.replace('Z', '+00:00'))
                if workflow.created_at < after_dt:
                    continue

            # Filter by created_before
            if created_before:
                before_dt = datetime.fromisoformat(created_before.replace('Z', '+00:00'))
                if workflow.created_at > before_dt:
                    continue

            filtered_workflows.append(workflow)

        # Apply pagination
        total = len(filtered_workflows)
        paginated = filtered_workflows[offset:offset + limit]

        return {
            "workflows": [self._serialize_workflow(w) for w in paginated],
            "total": total,
            "limit": limit,
            "offset": offset
        }

    def control_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Control workflow execution (pause/resume/cancel).

        Args:
            params: {
                "workflow_id": str (required),
                "action": str (required - "pause", "resume", or "cancel")
            }

        Returns:
            {
                "success": bool,
                "workflow_id": str,
                "action": str,
                "new_status": str
            }
        """
        self.validate_params(params, required=["workflow_id", "action"])

        workflow_id = params["workflow_id"]
        action = params["action"]

        if action not in ["pause", "resume", "cancel"]:
            raise ValueError(
                f"Invalid action: {action}. "
                f"Must be 'pause', 'resume', or 'cancel'"
            )

        self.logger.info(f"Controlling workflow {workflow_id}: {action}")

        # Get workflow
        workflow = self.db_manager.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        # Execute action
        if action == "pause":
            new_status = self.workflow_manager.pause_workflow(workflow_id)
        elif action == "resume":
            new_status = self.workflow_manager.resume_workflow(workflow_id)
        elif action == "cancel":
            new_status = self.workflow_manager.cancel_workflow(workflow_id)

        return {
            "success": True,
            "workflow_id": workflow_id,
            "action": action,
            "new_status": new_status.value
        }

    def get_workflow_report(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get detailed workflow report.

        Args:
            params: {
                "workflow_id": str (required),
                "include_details": bool (optional, default True)
            }

        Returns:
            {
                "workflow_id": str,
                "report": Dict (detailed metrics and statistics)
            }
        """
        self.validate_params(
            params,
            required=["workflow_id"],
            optional={"include_details": True}
        )

        workflow_id = params["workflow_id"]
        include_details = params["include_details"]

        self.logger.info(f"Generating workflow report: {workflow_id}")

        # Get workflow
        workflow = self.db_manager.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        # Generate report
        report = self.workflow_manager.generate_workflow_report(
            workflow_id,
            include_details=include_details
        )

        return {
            "workflow_id": workflow_id,
            "report": report
        }

    def get_workflow_summary(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get workflow summary for dashboards.

        Args:
            params: {
                "workflow_id": str (required)
            }

        Returns:
            {
                "workflow_id": str,
                "status": str,
                "progress_percent": float,
                "files_processed": int,
                "files_total": int,
                "errors_count": int,
                "duration_seconds": float,
                "eta_seconds": float (estimated time remaining)
            }
        """
        self.validate_params(params, required=["workflow_id"])

        workflow_id = params["workflow_id"]

        self.logger.info(f"Getting workflow summary: {workflow_id}")

        # Get workflow
        workflow = self.db_manager.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        # Calculate summary metrics
        summary = self.workflow_manager.get_workflow_summary(workflow_id)

        return {
            "workflow_id": workflow_id,
            "status": workflow.state.value,
            "progress_percent": summary["progress_percent"],
            "files_processed": summary["files_processed"],
            "files_total": summary["files_total"],
            "errors_count": summary["errors_count"],
            "duration_seconds": summary["duration_seconds"],
            "eta_seconds": summary.get("eta_seconds", 0)
        }

    def delete_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Delete a workflow record.

        Args:
            params: {
                "workflow_id": str (required),
                "force": bool (optional, default False - allow deleting running workflows)
            }

        Returns:
            {
                "success": bool,
                "workflow_id": str
            }
        """
        self.validate_params(
            params,
            required=["workflow_id"],
            optional={"force": False}
        )

        workflow_id = params["workflow_id"]
        force = params["force"]

        self.logger.info(f"Deleting workflow: {workflow_id}")

        # Get workflow
        workflow = self.db_manager.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        # Check if running
        if workflow.state == WorkflowState.RUNNING and not force:
            raise ValueError(
                f"Cannot delete running workflow {workflow_id}. "
                f"Cancel it first or use force=True"
            )

        # Cancel if running
        if workflow.state == WorkflowState.RUNNING:
            self.workflow_manager.cancel_workflow(workflow_id)

        # Delete from database
        self.db_manager.soft_delete_workflows([workflow_id])

        return {
            "success": True,
            "workflow_id": workflow_id
        }

    def bulk_delete_workflows(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Bulk delete workflows with filters.

        Args:
            params: {
                "workflow_ids": List[str] (optional - specific IDs to delete),
                "status": str (optional - delete by status),
                "workflow_type": str (optional - delete by type),
                "created_before": str (optional - ISO 8601 datetime),
                "force": bool (optional, default False)
            }

        Returns:
            {
                "success": bool,
                "deleted_count": int,
                "errors": List[Dict]
            }
        """
        self.validate_params(
            params,
            required=[],
            optional={
                "workflow_ids": None,
                "status": None,
                "workflow_type": None,
                "created_before": None,
                "force": False
            }
        )

        workflow_ids = params["workflow_ids"]
        status = params["status"]
        workflow_type = params["workflow_type"]
        created_before = params["created_before"]
        force = params["force"]

        self.logger.info(f"Bulk deleting workflows")

        # Get workflows to delete
        if workflow_ids:
            workflows = [
                self.db_manager.get_workflow(wid)
                for wid in workflow_ids
            ]
            workflows = [w for w in workflows if w is not None]
        else:
            # Get all and filter
            workflows = self.db_manager.list_workflows(limit=10000)

            # Apply filters
            if status:
                workflows = [w for w in workflows if w.state.value == status]
            if workflow_type:
                workflows = [w for w in workflows if w.type == workflow_type]
            if created_before:
                before_dt = datetime.fromisoformat(created_before.replace('Z', '+00:00'))
                workflows = [w for w in workflows if w.created_at <= before_dt]

        # Delete each workflow
        deleted_count = 0
        errors = []

        for workflow in workflows:
            try:
                self.delete_workflow({
                    "workflow_id": workflow.id,
                    "force": force
                })
                deleted_count += 1
            except Exception as e:
                errors.append({
                    "workflow_id": workflow.id,
                    "error": str(e)
                })

        return {
            "success": True,
            "deleted_count": deleted_count,
            "errors": errors
        }

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _serialize_workflow(self, workflow) -> Dict[str, Any]:
        """Serialize workflow record to dictionary."""
        return {
            "id": workflow.id,
            "workflow_type": workflow.type,
            "name": workflow.workflow_metadata.get("name") if workflow.workflow_metadata else None,
            "description": workflow.workflow_metadata.get("description") if workflow.workflow_metadata else None,
            "status": workflow.state.value,
            "params": workflow.input_params,
            "progress": workflow.progress_percent,
            "error_message": workflow.error_message,
            "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
            "started_at": workflow.updated_at.isoformat() if workflow.updated_at else None,
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
            "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None,
            "total_steps": workflow.total_steps,
            "current_step": workflow.current_step
        }
