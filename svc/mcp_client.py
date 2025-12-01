"""MCP client wrappers for synchronous and asynchronous usage."""

import time
import asyncio
from typing import Dict, Any, List, Optional, Union
from svc.mcp_server import create_mcp_client
from svc.mcp_exceptions import (
    MCPError,
    MCPInternalError,
    exception_from_error_code
)
from core.logging import get_logger

logger = get_logger(__name__)

# Singleton instances
_sync_client: Optional['MCPSyncClient'] = None
_async_client: Optional['MCPAsyncClient'] = None


class MCPSyncClient:
    """
    Synchronous MCP client for CLI usage.

    Provides convenient methods for all MCP operations with
    automatic error handling and retry logic.

    Example:
        >>> client = get_mcp_sync_client()
        >>> result = client.validate_folder("/path/to/docs")
        >>> print(result['files_processed'])
    """

    def __init__(self, timeout: int = 30, max_retries: int = 3):
        """
        Initialize synchronous MCP client.

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for transient errors
        """
        self._server = create_mcp_client()
        self.timeout = timeout
        self.max_retries = max_retries
        self._request_counter = 0

    def _call(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call MCP method and handle response.

        Args:
            method: Method name
            params: Method parameters

        Returns:
            Method result dictionary

        Raises:
            MCPError: If request fails
        """
        self._request_counter += 1
        request_id = self._request_counter

        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": request_id
        }

        logger.debug(f"MCP request: method={method}, id={request_id}")

        for attempt in range(self.max_retries):
            try:
                response = self._server.handle_request(request)

                if "error" in response:
                    error = response["error"]
                    raise exception_from_error_code(
                        error["code"],
                        error["message"],
                        error.get("data")
                    )

                logger.debug(f"MCP response: method={method}, id={request_id}")
                return response.get("result", {})

            except MCPError:
                # Don't retry on application errors
                raise
            except Exception as e:
                # Retry on transient errors
                if attempt == self.max_retries - 1:
                    raise MCPInternalError(f"MCP request failed: {e}")

                logger.warning(
                    f"MCP request failed (attempt {attempt + 1}), retrying..."
                )
                # Exponential backoff: 0.1s, 0.2s, 0.4s, etc.
                time.sleep(0.1 * (2 ** attempt))

    # ========================================================================
    # Validation Methods
    # ========================================================================

    def validate_folder(
        self,
        folder_path: str,
        recursive: bool = True
    ) -> Dict[str, Any]:
        """
        Validate all markdown files in a folder.

        Args:
            folder_path: Path to folder
            recursive: Whether to search recursively

        Returns:
            Validation results with files_processed count

        Raises:
            MCPError: If validation fails
        """
        return self._call("validate_folder", {
            "folder_path": folder_path,
            "recursive": recursive
        })

    def validate_file(
        self,
        file_path: str,
        family: str = "words",
        validation_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Validate a single file.

        Args:
            file_path: Path to file to validate
            family: Plugin family (default "words")
            validation_types: List of specific validators to run

        Returns:
            Validation results with validation_id and issues

        Raises:
            MCPError: If validation fails
        """
        return self._call("validate_file", {
            "file_path": file_path,
            "family": family,
            "validation_types": validation_types
        })

    def validate_content(
        self,
        content: str,
        file_path: str = "temp.md",
        validation_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Validate content string without requiring a physical file.

        Args:
            content: Markdown content to validate
            file_path: Virtual file path for context (default "temp.md")
            validation_types: List of specific validators to run

        Returns:
            Validation results with validation_id and issues

        Raises:
            MCPError: If validation fails
        """
        return self._call("validate_content", {
            "content": content,
            "file_path": file_path,
            "validation_types": validation_types
        })

    def get_validation(self, validation_id: str) -> Dict[str, Any]:
        """
        Get validation record by ID.

        Args:
            validation_id: ID of validation to retrieve

        Returns:
            Validation record dictionary

        Raises:
            MCPError: If validation not found
        """
        return self._call("get_validation", {
            "validation_id": validation_id
        })

    def list_validations(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None,
        file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List validation records with optional filtering.

        Args:
            limit: Maximum number of results (default 100)
            offset: Number of results to skip (default 0)
            status: Filter by status (optional)
            file_path: Filter by file path (optional)

        Returns:
            Dictionary with validations list and total count

        Raises:
            MCPError: If listing fails
        """
        return self._call("list_validations", {
            "limit": limit,
            "offset": offset,
            "status": status,
            "file_path": file_path
        })

    def update_validation(
        self,
        validation_id: str,
        notes: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update validation metadata.

        Args:
            validation_id: ID of validation to update
            notes: New notes (optional)
            status: New status (optional)

        Returns:
            Success status and validation_id

        Raises:
            MCPError: If update fails
        """
        return self._call("update_validation", {
            "validation_id": validation_id,
            "notes": notes,
            "status": status
        })

    def delete_validation(self, validation_id: str) -> Dict[str, Any]:
        """
        Delete validation record.

        Args:
            validation_id: ID of validation to delete

        Returns:
            Success status and validation_id

        Raises:
            MCPError: If deletion fails
        """
        return self._call("delete_validation", {
            "validation_id": validation_id
        })

    def revalidate(self, validation_id: str) -> Dict[str, Any]:
        """
        Re-run validation on the same file.

        Args:
            validation_id: ID of original validation

        Returns:
            Success status with new and original validation IDs

        Raises:
            MCPError: If revalidation fails
        """
        return self._call("revalidate", {
            "validation_id": validation_id
        })

    # ========================================================================
    # Approval Methods
    # ========================================================================

    def approve(self, validation_ids: Union[str, List[str]]) -> Dict[str, Any]:
        """
        Approve validation(s).

        Args:
            validation_ids: Single ID or list of IDs to approve

        Returns:
            Approval results with counts and errors

        Raises:
            MCPError: If approval fails
        """
        # Normalize to list for API
        if isinstance(validation_ids, str):
            ids = [validation_ids]
        else:
            ids = validation_ids

        return self._call("approve", {"ids": ids})

    def reject(
        self,
        validation_ids: Union[str, List[str]],
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Reject validation(s).

        Args:
            validation_ids: Single ID or list of IDs to reject
            reason: Optional rejection reason

        Returns:
            Rejection results with counts and errors

        Raises:
            MCPError: If rejection fails
        """
        # Normalize to list for API
        if isinstance(validation_ids, str):
            ids = [validation_ids]
        else:
            ids = validation_ids

        params = {"ids": ids}
        if reason is not None:
            params["reason"] = reason

        return self._call("reject", params)

    def bulk_approve(
        self,
        validation_ids: List[str],
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Bulk approve multiple validations efficiently.

        Args:
            validation_ids: List of validation IDs
            batch_size: Processing batch size (default 100)

        Returns:
            Bulk approval results with timing

        Raises:
            MCPError: If bulk approval fails
        """
        return self._call("bulk_approve", {
            "ids": validation_ids,
            "batch_size": batch_size
        })

    def bulk_reject(
        self,
        validation_ids: List[str],
        reason: Optional[str] = None,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Bulk reject multiple validations efficiently.

        Args:
            validation_ids: List of validation IDs
            reason: Optional rejection reason
            batch_size: Processing batch size (default 100)

        Returns:
            Bulk rejection results with timing

        Raises:
            MCPError: If bulk rejection fails
        """
        params = {
            "ids": validation_ids,
            "batch_size": batch_size
        }
        if reason is not None:
            params["reason"] = reason

        return self._call("bulk_reject", params)

    # ========================================================================
    # Enhancement Methods
    # ========================================================================

    def enhance(self, ids: List[str]) -> Dict[str, Any]:
        """
        Enhance approved validation records.

        Args:
            ids: List of validation IDs to enhance

        Returns:
            Results with enhanced_count, errors, and enhancements list

        Raises:
            MCPError: If enhancement fails
        """
        return self._call("enhance", {"ids": ids})

    def enhance_batch(
        self,
        validation_ids: List[str],
        batch_size: int = 10,
        threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Enhance multiple validations with progress tracking.

        Args:
            validation_ids: List of validation IDs to enhance
            batch_size: Processing batch size (default 10)
            threshold: Confidence threshold for recommendations (default 0.7)

        Returns:
            Batch enhancement results with counts and timing

        Raises:
            MCPError: If batch enhancement fails
        """
        return self._call("enhance_batch", {
            "ids": validation_ids,
            "batch_size": batch_size,
            "threshold": threshold
        })

    def enhance_preview(
        self,
        validation_id: str,
        recommendation_types: Optional[List[str]] = None,
        threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Preview enhancement without applying changes.

        Args:
            validation_id: Validation ID to preview
            recommendation_types: Filter by recommendation types (optional)
            threshold: Confidence threshold (default 0.7)

        Returns:
            Preview results with original, enhanced content, and diff

        Raises:
            MCPError: If preview fails
        """
        return self._call("enhance_preview", {
            "validation_id": validation_id,
            "recommendation_types": recommendation_types,
            "threshold": threshold
        })

    def enhance_auto_apply(
        self,
        validation_id: str,
        threshold: float = 0.9,
        recommendation_types: Optional[List[str]] = None,
        preview_first: bool = True
    ) -> Dict[str, Any]:
        """
        Auto-apply recommendations above threshold.

        Args:
            validation_id: Validation ID
            threshold: Confidence threshold (default 0.9)
            recommendation_types: Types to auto-apply (optional)
            preview_first: Generate preview before applying (default True)

        Returns:
            Auto-apply results with counts and optional preview

        Raises:
            MCPError: If auto-apply fails
        """
        return self._call("enhance_auto_apply", {
            "validation_id": validation_id,
            "threshold": threshold,
            "recommendation_types": recommendation_types,
            "preview_first": preview_first
        })

    def get_enhancement_comparison(
        self,
        validation_id: str,
        format: str = "unified"
    ) -> Dict[str, Any]:
        """
        Get before/after comparison of enhancement.

        Args:
            validation_id: Enhanced validation ID
            format: Diff format ("unified" or "side-by-side"), default "unified"

        Returns:
            Comparison with original, enhanced content, diff, and statistics

        Raises:
            MCPError: If comparison fails
        """
        return self._call("get_enhancement_comparison", {
            "validation_id": validation_id,
            "format": format
        })

    # ========================================================================
    # Admin Methods
    # ========================================================================

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get system health status.

        Returns:
            System status with component health and resource usage

        Raises:
            MCPError: If status check fails
        """
        return self._call("get_system_status", {})

    def clear_cache(self, cache_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Clear all caches.

        Args:
            cache_types: Optional list of specific cache types to clear

        Returns:
            Results with cleared_items count

        Raises:
            MCPError: If cache clear fails
        """
        return self._call("clear_cache", {"cache_types": cache_types})

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Cache statistics with totals and breakdowns

        Raises:
            MCPError: If stats retrieval fails
        """
        return self._call("get_cache_stats", {})

    def cleanup_cache(self, max_age_hours: int = 24) -> Dict[str, Any]:
        """
        Clean up stale cache entries.

        Args:
            max_age_hours: Maximum age in hours for cache entries

        Returns:
            Results with cleaned_items count

        Raises:
            MCPError: If cleanup fails
        """
        return self._call("cleanup_cache", {"max_age_hours": max_age_hours})

    def rebuild_cache(self) -> Dict[str, Any]:
        """
        Rebuild cache from scratch.

        Returns:
            Results with rebuilt_items count

        Raises:
            MCPError: If rebuild fails
        """
        return self._call("rebuild_cache", {})

    def reload_agent(self, agent_id: str) -> Dict[str, Any]:
        """
        Reload specific agent.

        Args:
            agent_id: Agent ID to reload

        Returns:
            Results with agent_id and reloaded_at timestamp

        Raises:
            MCPError: If reload fails
        """
        return self._call("reload_agent", {"agent_id": agent_id})

    def run_gc(self) -> Dict[str, Any]:
        """
        Run garbage collection.

        Returns:
            Results with collected_objects count

        Raises:
            MCPError: If GC fails
        """
        return self._call("run_gc", {})

    def enable_maintenance_mode(
        self,
        reason: str = "",
        enabled_by: str = "system"
    ) -> Dict[str, Any]:
        """
        Enable maintenance mode.

        Args:
            reason: Reason for maintenance
            enabled_by: User/system enabling maintenance

        Returns:
            Results with enabled_at timestamp

        Raises:
            MCPError: If enable fails
        """
        return self._call("enable_maintenance_mode", {
            "reason": reason,
            "enabled_by": enabled_by
        })

    def disable_maintenance_mode(self) -> Dict[str, Any]:
        """
        Disable maintenance mode.

        Returns:
            Results with disabled_at timestamp

        Raises:
            MCPError: If disable fails
        """
        return self._call("disable_maintenance_mode", {})

    def create_checkpoint(
        self,
        name: str = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create system checkpoint.

        Args:
            name: Optional checkpoint name
            metadata: Optional metadata dictionary

        Returns:
            Results with checkpoint_id and created_at timestamp

        Raises:
            MCPError: If checkpoint creation fails
        """
        return self._call("create_checkpoint", {
            "name": name,
            "metadata": metadata
        })

    # ========================================================================
    # Workflow Methods
    # ========================================================================

    def create_workflow(
        self,
        workflow_type: str,
        workflow_params: Dict[str, Any],
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new workflow.

        Args:
            workflow_type: Type of workflow (validate_directory, batch_enhance, etc.)
            workflow_params: Workflow-specific parameters
            name: Optional workflow name
            description: Optional workflow description

        Returns:
            Results with workflow_id and status

        Raises:
            MCPError: If workflow creation fails
        """
        return self._call("create_workflow", {
            "workflow_type": workflow_type,
            "params": workflow_params,
            "name": name,
            "description": description
        })

    def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get workflow by ID.

        Args:
            workflow_id: ID of workflow to retrieve

        Returns:
            Workflow details dictionary

        Raises:
            MCPError: If workflow not found
        """
        return self._call("get_workflow", {
            "workflow_id": workflow_id
        })

    def list_workflows(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None,
        workflow_type: Optional[str] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List workflows with filters.

        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            status: Filter by status (optional)
            workflow_type: Filter by type (optional)
            created_after: Filter by creation date (ISO 8601)
            created_before: Filter by creation date (ISO 8601)

        Returns:
            Dictionary with workflows list and total count

        Raises:
            MCPError: If listing fails
        """
        return self._call("list_workflows", {
            "limit": limit,
            "offset": offset,
            "status": status,
            "workflow_type": workflow_type,
            "created_after": created_after,
            "created_before": created_before
        })

    def control_workflow(
        self,
        workflow_id: str,
        action: str
    ) -> Dict[str, Any]:
        """
        Control workflow execution (pause/resume/cancel).

        Args:
            workflow_id: ID of workflow to control
            action: Action to perform (pause, resume, or cancel)

        Returns:
            Results with new status

        Raises:
            MCPError: If control action fails
        """
        return self._call("control_workflow", {
            "workflow_id": workflow_id,
            "action": action
        })

    def get_workflow_report(
        self,
        workflow_id: str,
        include_details: bool = True
    ) -> Dict[str, Any]:
        """
        Get detailed workflow report.

        Args:
            workflow_id: ID of workflow
            include_details: Whether to include detailed metrics

        Returns:
            Detailed report dictionary

        Raises:
            MCPError: If report generation fails
        """
        return self._call("get_workflow_report", {
            "workflow_id": workflow_id,
            "include_details": include_details
        })

    def get_workflow_summary(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get workflow summary for dashboards.

        Args:
            workflow_id: ID of workflow

        Returns:
            Summary dictionary with progress metrics

        Raises:
            MCPError: If summary generation fails
        """
        return self._call("get_workflow_summary", {
            "workflow_id": workflow_id
        })

    def delete_workflow(
        self,
        workflow_id: str,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Delete a workflow.

        Args:
            workflow_id: ID of workflow to delete
            force: Allow deleting running workflows

        Returns:
            Success status

        Raises:
            MCPError: If deletion fails
        """
        return self._call("delete_workflow", {
            "workflow_id": workflow_id,
            "force": force
        })

    def bulk_delete_workflows(
        self,
        workflow_ids: Optional[List[str]] = None,
        status: Optional[str] = None,
        workflow_type: Optional[str] = None,
        created_before: Optional[str] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Bulk delete workflows.

        Args:
            workflow_ids: Specific workflow IDs to delete
            status: Delete by status
            workflow_type: Delete by type
            created_before: Delete workflows created before date (ISO 8601)
            force: Allow deleting running workflows

        Returns:
            Results with deleted_count and errors list

        Raises:
            MCPError: If bulk deletion fails
        """
        return self._call("bulk_delete_workflows", {
            "workflow_ids": workflow_ids,
            "status": status,
            "workflow_type": workflow_type,
            "created_before": created_before,
            "force": force
        })

    # ========================================================================
    # Query & Statistics Methods
    # ========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """
        Get system statistics.

        Returns:
            Statistics dictionary with counts and metrics

        Raises:
            MCPError: If stats retrieval fails
        """
        return self._call("get_stats", {})

    def get_audit_log(
        self,
        limit: int = 100,
        offset: int = 0,
        operation: Optional[str] = None,
        user: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get audit log entries.

        Args:
            limit: Maximum number of entries to return
            offset: Offset for pagination
            operation: Filter by operation name
            user: Filter by user
            status: Filter by status
            start_date: Filter by start date (ISO format)
            end_date: Filter by end date (ISO format)

        Returns:
            Audit log dictionary with logs and total count

        Raises:
            MCPError: If audit log retrieval fails
        """
        return self._call("get_audit_log", {
            "limit": limit,
            "offset": offset,
            "operation": operation,
            "user": user,
            "status": status,
            "start_date": start_date,
            "end_date": end_date
        })

    def get_performance_report(
        self,
        time_range: str = "24h",
        operation: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get performance metrics report.

        Args:
            time_range: Time range (1h, 24h, 7d, 30d)
            operation: Filter by operation name

        Returns:
            Performance report dictionary

        Raises:
            MCPError: If report generation fails
        """
        return self._call("get_performance_report", {
            "time_range": time_range,
            "operation": operation
        })

    def get_health_report(self) -> Dict[str, Any]:
        """
        Get detailed health report.

        Returns:
            Health report with status and recommendations

        Raises:
            MCPError: If health check fails
        """
        return self._call("get_health_report", {})

    def get_validation_history(
        self,
        file_path: str,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get validation history for a file.

        Args:
            file_path: Path to file
            limit: Maximum number of history entries

        Returns:
            Validation history dictionary

        Raises:
            MCPError: If history retrieval fails
        """
        return self._call("get_validation_history", {
            "file_path": file_path,
            "limit": limit
        })

    def get_available_validators(
        self,
        validator_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get list of available validators.

        Args:
            validator_type: Filter by validator type

        Returns:
            Validators dictionary with list and total count

        Raises:
            MCPError: If validator discovery fails
        """
        return self._call("get_available_validators", {
            "validator_type": validator_type
        })

    def export_validation(
        self,
        validation_id: str,
        include_recommendations: bool = False
    ) -> Dict[str, Any]:
        """
        Export validation to JSON.

        Args:
            validation_id: ID of validation to export
            include_recommendations: Include recommendations in export

        Returns:
            Export result with JSON data and metadata

        Raises:
            MCPError: If export fails
        """
        return self._call("export_validation", {
            "validation_id": validation_id,
            "include_recommendations": include_recommendations
        })

    def export_recommendations(self, validation_id: str) -> Dict[str, Any]:
        """
        Export recommendations to JSON.

        Args:
            validation_id: ID of validation

        Returns:
            Export result with JSON data and metadata

        Raises:
            MCPError: If export fails
        """
        return self._call("export_recommendations", {
            "validation_id": validation_id
        })

    def export_workflow(
        self,
        workflow_id: str,
        include_validations: bool = False
    ) -> Dict[str, Any]:
        """
        Export workflow report to JSON.

        Args:
            workflow_id: ID of workflow to export
            include_validations: Include validations in export

        Returns:
            Export result with JSON data and metadata

        Raises:
            MCPError: If export fails
        """
        return self._call("export_workflow", {
            "workflow_id": workflow_id,
            "include_validations": include_validations
        })

    # ========================================================================
    # Recommendation Methods
    # ========================================================================

    def generate_recommendations(
        self,
        validation_id: str,
        threshold: float = 0.7,
        types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate recommendations for a validation.

        Args:
            validation_id: ID of validation to generate recommendations for
            threshold: Confidence threshold (0.0-1.0), default 0.7
            types: List of recommendation types to filter (optional)

        Returns:
            Dictionary with recommendations list and count

        Raises:
            MCPError: If generation fails
        """
        return self._call("generate_recommendations", {
            "validation_id": validation_id,
            "threshold": threshold,
            "types": types
        })

    def rebuild_recommendations(
        self,
        validation_id: str,
        threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Rebuild recommendations for a validation.

        Args:
            validation_id: ID of validation to rebuild recommendations for
            threshold: Confidence threshold (0.0-1.0), default 0.7

        Returns:
            Dictionary with deleted and generated counts

        Raises:
            MCPError: If rebuild fails
        """
        return self._call("rebuild_recommendations", {
            "validation_id": validation_id,
            "threshold": threshold
        })

    def get_recommendations(
        self,
        validation_id: str,
        status: Optional[str] = None,
        rec_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get recommendations for a validation.

        Args:
            validation_id: ID of validation to get recommendations for
            status: Filter by status (optional)
            rec_type: Filter by recommendation type (optional)

        Returns:
            Dictionary with recommendations list and total count

        Raises:
            MCPError: If retrieval fails
        """
        return self._call("get_recommendations", {
            "validation_id": validation_id,
            "status": status,
            "type": rec_type
        })

    def review_recommendation(
        self,
        recommendation_id: str,
        action: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Review (approve/reject) a recommendation.

        Args:
            recommendation_id: ID of recommendation to review
            action: Action to take ("approve" or "reject")
            notes: Optional review notes

        Returns:
            Success status and new status

        Raises:
            MCPError: If review fails
        """
        return self._call("review_recommendation", {
            "recommendation_id": recommendation_id,
            "action": action,
            "notes": notes
        })

    def bulk_review_recommendations(
        self,
        recommendation_ids: List[str],
        action: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Bulk review multiple recommendations.

        Args:
            recommendation_ids: List of recommendation IDs to review
            action: Action to take ("approve" or "reject")
            notes: Optional review notes

        Returns:
            Dictionary with reviewed count and errors

        Raises:
            MCPError: If bulk review fails
        """
        return self._call("bulk_review_recommendations", {
            "recommendation_ids": recommendation_ids,
            "action": action,
            "notes": notes
        })

    def apply_recommendations(
        self,
        validation_id: str,
        recommendation_ids: Optional[List[str]] = None,
        dry_run: bool = False,
        create_backup: bool = True
    ) -> Dict[str, Any]:
        """
        Apply recommendations to content.

        Args:
            validation_id: ID of validation with recommendations to apply
            recommendation_ids: Specific recommendation IDs to apply (optional, applies all approved if None)
            dry_run: If True, preview changes without applying (default False)
            create_backup: If True, create backup before applying (default True)

        Returns:
            Dictionary with applied count, skipped count, errors, and backup path

        Raises:
            MCPError: If application fails
        """
        return self._call("apply_recommendations", {
            "validation_id": validation_id,
            "recommendation_ids": recommendation_ids,
            "dry_run": dry_run,
            "create_backup": create_backup
        })

    def delete_recommendation(self, recommendation_id: str) -> Dict[str, Any]:
        """
        Delete a recommendation.

        Args:
            recommendation_id: ID of recommendation to delete

        Returns:
            Success status and recommendation_id

        Raises:
            MCPError: If deletion fails
        """
        return self._call("delete_recommendation", {
            "recommendation_id": recommendation_id
        })

    def mark_recommendations_applied(
        self,
        recommendation_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Mark recommendations as applied.

        Args:
            recommendation_ids: List of recommendation IDs to mark as applied

        Returns:
            Dictionary with marked count and errors

        Raises:
            MCPError: If marking fails
        """
        return self._call("mark_recommendations_applied", {
            "recommendation_ids": recommendation_ids
        })


class MCPAsyncClient:
    """
    Asynchronous MCP client for API usage.

    Provides the same interface as MCPSyncClient but with async/await
    support for use in FastAPI and other async frameworks.

    Example:
        >>> client = get_mcp_async_client()
        >>> result = await client.validate_folder("/path/to/docs")
        >>> print(result['files_processed'])
    """

    def __init__(self, timeout: int = 30, max_retries: int = 3):
        """
        Initialize asynchronous MCP client.

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for transient errors
        """
        self._server = create_mcp_client()
        self.timeout = timeout
        self.max_retries = max_retries
        self._request_counter = 0

    async def _call(
        self,
        method: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Call MCP method asynchronously and handle response.

        Args:
            method: Method name
            params: Method parameters

        Returns:
            Method result dictionary

        Raises:
            MCPError: If request fails
        """
        self._request_counter += 1
        request_id = self._request_counter

        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": request_id
        }

        logger.debug(f"MCP request: method={method}, id={request_id}")

        for attempt in range(self.max_retries):
            try:
                # Run sync handle_request in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    self._server.handle_request,
                    request
                )

                if "error" in response:
                    error = response["error"]
                    raise exception_from_error_code(
                        error["code"],
                        error["message"],
                        error.get("data")
                    )

                logger.debug(f"MCP response: method={method}, id={request_id}")
                return response.get("result", {})

            except MCPError:
                # Don't retry on application errors
                raise
            except Exception as e:
                # Retry on transient errors
                if attempt == self.max_retries - 1:
                    raise MCPInternalError(f"MCP request failed: {e}")

                logger.warning(
                    f"MCP request failed (attempt {attempt + 1}), retrying..."
                )
                # Exponential backoff: 0.1s, 0.2s, 0.4s, etc.
                await asyncio.sleep(0.1 * (2 ** attempt))

    # ========================================================================
    # Validation Methods
    # ========================================================================

    async def validate_folder(
        self,
        folder_path: str,
        recursive: bool = True
    ) -> Dict[str, Any]:
        """
        Validate all markdown files in a folder asynchronously.

        Args:
            folder_path: Path to folder
            recursive: Whether to search recursively

        Returns:
            Validation results with files_processed count

        Raises:
            MCPError: If validation fails
        """
        return await self._call("validate_folder", {
            "folder_path": folder_path,
            "recursive": recursive
        })

    async def validate_file(
        self,
        file_path: str,
        family: str = "words",
        validation_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Validate a single file asynchronously.

        Args:
            file_path: Path to file to validate
            family: Plugin family (default "words")
            validation_types: List of specific validators to run

        Returns:
            Validation results with validation_id and issues

        Raises:
            MCPError: If validation fails
        """
        return await self._call("validate_file", {
            "file_path": file_path,
            "family": family,
            "validation_types": validation_types
        })

    async def validate_content(
        self,
        content: str,
        file_path: str = "temp.md",
        validation_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Validate content string asynchronously.

        Args:
            content: Markdown content to validate
            file_path: Virtual file path for context (default "temp.md")
            validation_types: List of specific validators to run

        Returns:
            Validation results with validation_id and issues

        Raises:
            MCPError: If validation fails
        """
        return await self._call("validate_content", {
            "content": content,
            "file_path": file_path,
            "validation_types": validation_types
        })

    async def get_validation(self, validation_id: str) -> Dict[str, Any]:
        """
        Get validation record by ID asynchronously.

        Args:
            validation_id: ID of validation to retrieve

        Returns:
            Validation record dictionary

        Raises:
            MCPError: If validation not found
        """
        return await self._call("get_validation", {
            "validation_id": validation_id
        })

    async def list_validations(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None,
        file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List validation records asynchronously.

        Args:
            limit: Maximum number of results (default 100)
            offset: Number of results to skip (default 0)
            status: Filter by status (optional)
            file_path: Filter by file path (optional)

        Returns:
            Dictionary with validations list and total count

        Raises:
            MCPError: If listing fails
        """
        return await self._call("list_validations", {
            "limit": limit,
            "offset": offset,
            "status": status,
            "file_path": file_path
        })

    async def update_validation(
        self,
        validation_id: str,
        notes: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update validation metadata asynchronously.

        Args:
            validation_id: ID of validation to update
            notes: New notes (optional)
            status: New status (optional)

        Returns:
            Success status and validation_id

        Raises:
            MCPError: If update fails
        """
        return await self._call("update_validation", {
            "validation_id": validation_id,
            "notes": notes,
            "status": status
        })

    async def delete_validation(self, validation_id: str) -> Dict[str, Any]:
        """
        Delete validation record asynchronously.

        Args:
            validation_id: ID of validation to delete

        Returns:
            Success status and validation_id

        Raises:
            MCPError: If deletion fails
        """
        return await self._call("delete_validation", {
            "validation_id": validation_id
        })

    async def revalidate(self, validation_id: str) -> Dict[str, Any]:
        """
        Re-run validation asynchronously.

        Args:
            validation_id: ID of original validation

        Returns:
            Success status with new and original validation IDs

        Raises:
            MCPError: If revalidation fails
        """
        return await self._call("revalidate", {
            "validation_id": validation_id
        })

    # ========================================================================
    # Approval Methods
    # ========================================================================

    async def approve(self, validation_ids: Union[str, List[str]]) -> Dict[str, Any]:
        """
        Approve validation(s) asynchronously.

        Args:
            validation_ids: Single ID or list of IDs to approve

        Returns:
            Approval results with counts and errors

        Raises:
            MCPError: If approval fails
        """
        # Normalize to list for API
        if isinstance(validation_ids, str):
            ids = [validation_ids]
        else:
            ids = validation_ids

        return await self._call("approve", {"ids": ids})

    async def reject(
        self,
        validation_ids: Union[str, List[str]],
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Reject validation(s) asynchronously.

        Args:
            validation_ids: Single ID or list of IDs to reject
            reason: Optional rejection reason

        Returns:
            Rejection results with counts and errors

        Raises:
            MCPError: If rejection fails
        """
        # Normalize to list for API
        if isinstance(validation_ids, str):
            ids = [validation_ids]
        else:
            ids = validation_ids

        params = {"ids": ids}
        if reason is not None:
            params["reason"] = reason

        return await self._call("reject", params)

    async def bulk_approve(
        self,
        validation_ids: List[str],
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Bulk approve multiple validations efficiently asynchronously.

        Args:
            validation_ids: List of validation IDs
            batch_size: Processing batch size (default 100)

        Returns:
            Bulk approval results with timing

        Raises:
            MCPError: If bulk approval fails
        """
        return await self._call("bulk_approve", {
            "ids": validation_ids,
            "batch_size": batch_size
        })

    async def bulk_reject(
        self,
        validation_ids: List[str],
        reason: Optional[str] = None,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Bulk reject multiple validations efficiently asynchronously.

        Args:
            validation_ids: List of validation IDs
            reason: Optional rejection reason
            batch_size: Processing batch size (default 100)

        Returns:
            Bulk rejection results with timing

        Raises:
            MCPError: If bulk rejection fails
        """
        params = {
            "ids": validation_ids,
            "batch_size": batch_size
        }
        if reason is not None:
            params["reason"] = reason

        return await self._call("bulk_reject", params)

    # ========================================================================
    # Enhancement Methods
    # ========================================================================

    async def enhance(self, ids: List[str]) -> Dict[str, Any]:
        """
        Enhance approved validation records asynchronously.

        Args:
            ids: List of validation IDs to enhance

        Returns:
            Results with enhanced_count, errors, and enhancements list

        Raises:
            MCPError: If enhancement fails
        """
        return await self._call("enhance", {"ids": ids})

    async def enhance_batch(
        self,
        validation_ids: List[str],
        batch_size: int = 10,
        threshold: float = 0.7
    ) -> Dict[str, Any]:
        """Enhance multiple validations with progress tracking asynchronously."""
        return await self._call("enhance_batch", {
            "ids": validation_ids,
            "batch_size": batch_size,
            "threshold": threshold
        })

    async def enhance_preview(
        self,
        validation_id: str,
        recommendation_types: Optional[List[str]] = None,
        threshold: float = 0.7
    ) -> Dict[str, Any]:
        """Preview enhancement without applying changes asynchronously."""
        return await self._call("enhance_preview", {
            "validation_id": validation_id,
            "recommendation_types": recommendation_types,
            "threshold": threshold
        })

    async def enhance_auto_apply(
        self,
        validation_id: str,
        threshold: float = 0.9,
        recommendation_types: Optional[List[str]] = None,
        preview_first: bool = True
    ) -> Dict[str, Any]:
        """Auto-apply recommendations above threshold asynchronously."""
        return await self._call("enhance_auto_apply", {
            "validation_id": validation_id,
            "threshold": threshold,
            "recommendation_types": recommendation_types,
            "preview_first": preview_first
        })

    async def get_enhancement_comparison(
        self,
        validation_id: str,
        format: str = "unified"
    ) -> Dict[str, Any]:
        """Get before/after comparison of enhancement asynchronously."""
        return await self._call("get_enhancement_comparison", {
            "validation_id": validation_id,
            "format": format
        })

    # ========================================================================
    # Admin Methods
    # ========================================================================

    async def get_system_status(self) -> Dict[str, Any]:
        """Get system health status asynchronously."""
        return await self._call("get_system_status", {})

    async def clear_cache(self, cache_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """Clear all caches asynchronously."""
        return await self._call("clear_cache", {"cache_types": cache_types})

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics asynchronously."""
        return await self._call("get_cache_stats", {})

    async def cleanup_cache(self, max_age_hours: int = 24) -> Dict[str, Any]:
        """Clean up stale cache entries asynchronously."""
        return await self._call("cleanup_cache", {"max_age_hours": max_age_hours})

    async def rebuild_cache(self) -> Dict[str, Any]:
        """Rebuild cache from scratch asynchronously."""
        return await self._call("rebuild_cache", {})

    async def reload_agent(self, agent_id: str) -> Dict[str, Any]:
        """Reload specific agent asynchronously."""
        return await self._call("reload_agent", {"agent_id": agent_id})

    async def run_gc(self) -> Dict[str, Any]:
        """Run garbage collection asynchronously."""
        return await self._call("run_gc", {})

    async def enable_maintenance_mode(
        self,
        reason: str = "",
        enabled_by: str = "system"
    ) -> Dict[str, Any]:
        """Enable maintenance mode asynchronously."""
        return await self._call("enable_maintenance_mode", {
            "reason": reason,
            "enabled_by": enabled_by
        })

    async def disable_maintenance_mode(self) -> Dict[str, Any]:
        """Disable maintenance mode asynchronously."""
        return await self._call("disable_maintenance_mode", {})

    async def create_checkpoint(
        self,
        name: str = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create system checkpoint asynchronously."""
        return await self._call("create_checkpoint", {
            "name": name,
            "metadata": metadata
        })

    # ========================================================================
    # Workflow Methods
    # ========================================================================

    async def create_workflow(
        self,
        workflow_type: str,
        workflow_params: Dict[str, Any],
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new workflow asynchronously."""
        return await self._call("create_workflow", {
            "workflow_type": workflow_type,
            "params": workflow_params,
            "name": name,
            "description": description
        })

    async def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow by ID asynchronously."""
        return await self._call("get_workflow", {
            "workflow_id": workflow_id
        })

    async def list_workflows(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None,
        workflow_type: Optional[str] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None
    ) -> Dict[str, Any]:
        """List workflows with filters asynchronously."""
        return await self._call("list_workflows", {
            "limit": limit,
            "offset": offset,
            "status": status,
            "workflow_type": workflow_type,
            "created_after": created_after,
            "created_before": created_before
        })

    async def control_workflow(
        self,
        workflow_id: str,
        action: str
    ) -> Dict[str, Any]:
        """Control workflow execution asynchronously."""
        return await self._call("control_workflow", {
            "workflow_id": workflow_id,
            "action": action
        })

    async def get_workflow_report(
        self,
        workflow_id: str,
        include_details: bool = True
    ) -> Dict[str, Any]:
        """Get detailed workflow report asynchronously."""
        return await self._call("get_workflow_report", {
            "workflow_id": workflow_id,
            "include_details": include_details
        })

    async def get_workflow_summary(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow summary asynchronously."""
        return await self._call("get_workflow_summary", {
            "workflow_id": workflow_id
        })

    async def delete_workflow(
        self,
        workflow_id: str,
        force: bool = False
    ) -> Dict[str, Any]:
        """Delete a workflow asynchronously."""
        return await self._call("delete_workflow", {
            "workflow_id": workflow_id,
            "force": force
        })

    async def bulk_delete_workflows(
        self,
        workflow_ids: Optional[List[str]] = None,
        status: Optional[str] = None,
        workflow_type: Optional[str] = None,
        created_before: Optional[str] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """Bulk delete workflows asynchronously."""
        return await self._call("bulk_delete_workflows", {
            "workflow_ids": workflow_ids,
            "status": status,
            "workflow_type": workflow_type,
            "created_before": created_before,
            "force": force
        })

    # ========================================================================
    # Query & Statistics Methods
    # ========================================================================

    async def get_stats(self) -> Dict[str, Any]:
        """Get system statistics asynchronously."""
        return await self._call("get_stats", {})

    async def get_audit_log(
        self,
        limit: int = 100,
        offset: int = 0,
        operation: Optional[str] = None,
        user: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get audit log entries asynchronously."""
        return await self._call("get_audit_log", {
            "limit": limit,
            "offset": offset,
            "operation": operation,
            "user": user,
            "status": status,
            "start_date": start_date,
            "end_date": end_date
        })

    async def get_performance_report(
        self,
        time_range: str = "24h",
        operation: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get performance metrics report asynchronously."""
        return await self._call("get_performance_report", {
            "time_range": time_range,
            "operation": operation
        })

    async def get_health_report(self) -> Dict[str, Any]:
        """Get detailed health report asynchronously."""
        return await self._call("get_health_report", {})

    async def get_validation_history(
        self,
        file_path: str,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get validation history for a file asynchronously."""
        return await self._call("get_validation_history", {
            "file_path": file_path,
            "limit": limit
        })

    async def get_available_validators(
        self,
        validator_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get list of available validators asynchronously."""
        return await self._call("get_available_validators", {
            "validator_type": validator_type
        })

    async def export_validation(
        self,
        validation_id: str,
        include_recommendations: bool = False
    ) -> Dict[str, Any]:
        """Export validation to JSON asynchronously."""
        return await self._call("export_validation", {
            "validation_id": validation_id,
            "include_recommendations": include_recommendations
        })

    async def export_recommendations(self, validation_id: str) -> Dict[str, Any]:
        """Export recommendations to JSON asynchronously."""
        return await self._call("export_recommendations", {
            "validation_id": validation_id
        })

    async def export_workflow(
        self,
        workflow_id: str,
        include_validations: bool = False
    ) -> Dict[str, Any]:
        """Export workflow report to JSON asynchronously."""
        return await self._call("export_workflow", {
            "workflow_id": workflow_id,
            "include_validations": include_validations
        })

    # ========================================================================
    # Recommendation Methods
    # ========================================================================

    async def generate_recommendations(
        self,
        validation_id: str,
        threshold: float = 0.7,
        types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate recommendations for a validation asynchronously.

        Args:
            validation_id: ID of validation to generate recommendations for
            threshold: Confidence threshold (0.0-1.0), default 0.7
            types: List of recommendation types to filter (optional)

        Returns:
            Dictionary with recommendations list and count

        Raises:
            MCPError: If generation fails
        """
        return await self._call("generate_recommendations", {
            "validation_id": validation_id,
            "threshold": threshold,
            "types": types
        })

    async def rebuild_recommendations(
        self,
        validation_id: str,
        threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Rebuild recommendations for a validation asynchronously.

        Args:
            validation_id: ID of validation to rebuild recommendations for
            threshold: Confidence threshold (0.0-1.0), default 0.7

        Returns:
            Dictionary with deleted and generated counts

        Raises:
            MCPError: If rebuild fails
        """
        return await self._call("rebuild_recommendations", {
            "validation_id": validation_id,
            "threshold": threshold
        })

    async def get_recommendations(
        self,
        validation_id: str,
        status: Optional[str] = None,
        rec_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get recommendations for a validation asynchronously.

        Args:
            validation_id: ID of validation to get recommendations for
            status: Filter by status (optional)
            rec_type: Filter by recommendation type (optional)

        Returns:
            Dictionary with recommendations list and total count

        Raises:
            MCPError: If retrieval fails
        """
        return await self._call("get_recommendations", {
            "validation_id": validation_id,
            "status": status,
            "type": rec_type
        })

    async def review_recommendation(
        self,
        recommendation_id: str,
        action: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Review (approve/reject) a recommendation asynchronously.

        Args:
            recommendation_id: ID of recommendation to review
            action: Action to take ("approve" or "reject")
            notes: Optional review notes

        Returns:
            Success status and new status

        Raises:
            MCPError: If review fails
        """
        return await self._call("review_recommendation", {
            "recommendation_id": recommendation_id,
            "action": action,
            "notes": notes
        })

    async def bulk_review_recommendations(
        self,
        recommendation_ids: List[str],
        action: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Bulk review multiple recommendations asynchronously.

        Args:
            recommendation_ids: List of recommendation IDs to review
            action: Action to take ("approve" or "reject")
            notes: Optional review notes

        Returns:
            Dictionary with reviewed count and errors

        Raises:
            MCPError: If bulk review fails
        """
        return await self._call("bulk_review_recommendations", {
            "recommendation_ids": recommendation_ids,
            "action": action,
            "notes": notes
        })

    async def apply_recommendations(
        self,
        validation_id: str,
        recommendation_ids: Optional[List[str]] = None,
        dry_run: bool = False,
        create_backup: bool = True
    ) -> Dict[str, Any]:
        """
        Apply recommendations to content asynchronously.

        Args:
            validation_id: ID of validation with recommendations to apply
            recommendation_ids: Specific recommendation IDs to apply (optional, applies all approved if None)
            dry_run: If True, preview changes without applying (default False)
            create_backup: If True, create backup before applying (default True)

        Returns:
            Dictionary with applied count, skipped count, errors, and backup path

        Raises:
            MCPError: If application fails
        """
        return await self._call("apply_recommendations", {
            "validation_id": validation_id,
            "recommendation_ids": recommendation_ids,
            "dry_run": dry_run,
            "create_backup": create_backup
        })

    async def delete_recommendation(self, recommendation_id: str) -> Dict[str, Any]:
        """
        Delete a recommendation asynchronously.

        Args:
            recommendation_id: ID of recommendation to delete

        Returns:
            Success status and recommendation_id

        Raises:
            MCPError: If deletion fails
        """
        return await self._call("delete_recommendation", {
            "recommendation_id": recommendation_id
        })

    async def mark_recommendations_applied(
        self,
        recommendation_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Mark recommendations as applied asynchronously.

        Args:
            recommendation_ids: List of recommendation IDs to mark as applied

        Returns:
            Dictionary with marked count and errors

        Raises:
            MCPError: If marking fails
        """
        return await self._call("mark_recommendations_applied", {
            "recommendation_ids": recommendation_ids
        })


def get_mcp_sync_client(
    timeout: int = 30,
    max_retries: int = 3
) -> MCPSyncClient:
    """
    Get singleton instance of synchronous MCP client.

    Args:
        timeout: Request timeout in seconds
        max_retries: Maximum number of retries

    Returns:
        MCPSyncClient instance
    """
    global _sync_client
    if _sync_client is None:
        _sync_client = MCPSyncClient(timeout=timeout, max_retries=max_retries)
    return _sync_client


def get_mcp_async_client(
    timeout: int = 30,
    max_retries: int = 3
) -> MCPAsyncClient:
    """
    Get singleton instance of asynchronous MCP client.

    Args:
        timeout: Request timeout in seconds
        max_retries: Maximum number of retries

    Returns:
        MCPAsyncClient instance
    """
    global _async_client
    if _async_client is None:
        _async_client = MCPAsyncClient(timeout=timeout, max_retries=max_retries)
    return _async_client
