"""Query, statistics, and export MCP methods."""

from typing import Dict, Any, Optional, List
from .base import BaseMCPMethod
from core.audit_logger import AuditLogger
from core.performance_tracker import PerformanceTracker
from core.export_utils import export_to_json, create_export_metadata
from core.logging import get_logger

logger = get_logger(__name__)


class QueryMethods(BaseMCPMethod):
    """Handler for query, statistics, and export MCP methods."""

    def __init__(self, db_manager, rule_manager, agent_registry):
        super().__init__(db_manager, rule_manager, agent_registry)
        self.audit_logger = AuditLogger()
        self.performance_tracker = PerformanceTracker()

    def handle(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle query method execution.

        Args:
            params: Method parameters

        Returns:
            Method result dictionary

        Raises:
            ValueError: If parameters are invalid
        """
        # This is called via registry, specific methods are called directly
        raise NotImplementedError("Use specific query methods via registry")

    # ========================================================================
    # Statistics & Analytics
    # ========================================================================

    def get_stats(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get system statistics.

        Args:
            params: {} (no parameters)

        Returns:
            {
                "validations_total": int,
                "validations_by_status": Dict[str, int],
                "recommendations_total": int,
                "workflows_total": int,
                "workflows_by_status": Dict[str, int],
                "cache_stats": Dict,
                "agents_count": int
            }
        """
        self.logger.info("Getting system statistics")

        # Get validation stats
        validation_count = self.db_manager.count_validations()
        validations_by_status = self.db_manager.get_validations_by_status()

        # Get recommendation stats
        recommendation_count = self.db_manager.count_recommendations()

        # Get workflow stats
        workflow_count = self.db_manager.count_workflows()
        workflows_by_status = self.db_manager.get_workflows_by_status()

        # Get cache stats
        from core.cache import CacheManager
        try:
            cache_manager = CacheManager()
            cache_stats = cache_manager.get_stats()
        except Exception as e:
            self.logger.warning(f"Failed to get cache stats: {e}")
            cache_stats = {"error": str(e)}

        # Get agent stats
        agents_count = 0
        if self.agent_registry:
            agents = self.agent_registry.list_agents()
            agents_count = len(agents)

        return {
            "validations_total": validation_count,
            "validations_by_status": validations_by_status,
            "recommendations_total": recommendation_count,
            "workflows_total": workflow_count,
            "workflows_by_status": workflows_by_status,
            "cache_stats": cache_stats,
            "agents_count": agents_count
        }

    def get_audit_log(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get audit log entries.

        Args:
            params: {
                "limit": int (optional, default 100),
                "offset": int (optional, default 0),
                "operation": str (optional),
                "user": str (optional),
                "status": str (optional),
                "start_date": str (optional),
                "end_date": str (optional)
            }

        Returns:
            {
                "logs": List[Dict],
                "total": int
            }
        """
        self.validate_params(params, required=[],
                           optional={
                               "limit": 100,
                               "offset": 0,
                               "operation": None,
                               "user": None,
                               "status": None,
                               "start_date": None,
                               "end_date": None
                           })

        logs = self.audit_logger.get_logs(
            limit=params["limit"],
            offset=params["offset"],
            operation=params["operation"],
            user=params["user"],
            status=params["status"],
            start_date=params["start_date"],
            end_date=params["end_date"]
        )

        total = self.audit_logger.count_logs(
            operation=params["operation"],
            user=params["user"],
            status=params["status"]
        )

        return {
            "logs": logs,
            "total": total
        }

    def get_performance_report(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get performance metrics report.

        Args:
            params: {
                "time_range": str (optional, default "24h"),
                "operation": str (optional)
            }

        Returns:
            {
                "time_range": str,
                "total_operations": int,
                "failed_operations": int,
                "success_rate": float,
                "operations": Dict[str, Dict]
            }
        """
        self.validate_params(params, required=[],
                           optional={"time_range": "24h", "operation": None})

        report = self.performance_tracker.get_report(
            time_range=params["time_range"],
            operation=params["operation"]
        )

        return report

    def get_health_report(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get detailed health report.

        Args:
            params: {} (no parameters)

        Returns:
            {
                "overall_health": str,
                "components": Dict,
                "recent_errors": List[Dict],
                "performance_summary": Dict,
                "recommendations": List[str]
            }
        """
        self.logger.info("Generating health report")

        # Get system status
        from svc.mcp_methods.admin_methods import AdminMethods
        try:
            admin_handler = AdminMethods(
                self.db_manager,
                self.rule_manager,
                self.agent_registry
            )
            system_status = admin_handler.get_system_status({})
        except Exception as e:
            self.logger.error(f"Failed to get system status: {e}")
            system_status = {
                "status": "unknown",
                "components": {},
                "resources": {"cpu_percent": 0, "memory_percent": 0}
            }

        # Get recent errors from audit log
        recent_errors = self.audit_logger.get_logs(
            limit=10,
            status="failure"
        )

        # Get performance summary
        performance_summary = self.performance_tracker.get_report(time_range="1h")

        # Generate recommendations
        recommendations = []
        overall_status = system_status.get("status", "unknown")
        if overall_status == "degraded":
            recommendations.append("Some system components are degraded - check component details")
        if overall_status == "unhealthy":
            recommendations.append("System is unhealthy - immediate attention required")
        if performance_summary.get("failed_operations", 0) > 10:
            recommendations.append("High failure rate detected - investigate error logs")

        resources = system_status.get("resources", {})
        if resources.get("cpu_percent", 0) > 80:
            recommendations.append("CPU usage high - consider scaling or optimization")
        if resources.get("memory_percent", 0) > 80:
            recommendations.append("Memory usage high - check for leaks or increase capacity")

        return {
            "overall_health": overall_status,
            "components": system_status.get("components", {}),
            "recent_errors": recent_errors,
            "performance_summary": performance_summary,
            "recommendations": recommendations
        }

    # ========================================================================
    # Validation History & Discovery
    # ========================================================================

    def get_validation_history(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get validation history for a file.

        Args:
            params: {
                "file_path": str (required),
                "limit": int (optional, default 50)
            }

        Returns:
            {
                "file_path": str,
                "validations": List[Dict],
                "total": int
            }
        """
        self.validate_params(params, required=["file_path"],
                           optional={"limit": 50})

        file_path = params["file_path"]
        limit = params["limit"]

        self.logger.info(f"Getting validation history for: {file_path}")

        # Get validation history from database
        history_data = self.db_manager.get_validation_history(
            file_path=file_path,
            limit=limit
        )

        # Extract validations list
        if isinstance(history_data, dict):
            validations = history_data.get("validations", [])
            total = history_data.get("total_validations", len(validations))
        else:
            # Fallback if get_validation_history returns a list
            validations = history_data if isinstance(history_data, list) else []
            total = len(validations)

        return {
            "file_path": file_path,
            "validations": validations,
            "total": total
        }

    def get_available_validators(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get list of available validators.

        Args:
            params: {
                "validator_type": str (optional)
            }

        Returns:
            {
                "validators": List[Dict],
                "total": int
            }
        """
        self.validate_params(params, required=[],
                           optional={"validator_type": None})

        validator_type = params["validator_type"]

        self.logger.info(f"Getting available validators (type: {validator_type})")

        # Get validators from agent registry
        validators = []
        if self.agent_registry:
            try:
                validators = self.agent_registry.list_validators()
            except Exception as e:
                self.logger.error(f"Failed to list validators: {e}")
                validators = []

        # Filter by type if specified
        if validator_type:
            validators = [v for v in validators if v.get("type") == validator_type]

        return {
            "validators": validators,
            "total": len(validators)
        }

    # ========================================================================
    # Export Methods
    # ========================================================================

    def export_validation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Export validation to JSON.

        Args:
            params: {
                "validation_id": str (required),
                "include_recommendations": bool (optional, default False)
            }

        Returns:
            {
                "success": bool,
                "export_data": str (JSON string),
                "metadata": Dict
            }
        """
        self.validate_params(params, required=["validation_id"],
                           optional={"include_recommendations": False})

        validation_id = params["validation_id"]
        include_recommendations = params["include_recommendations"]

        self.logger.info(f"Exporting validation: {validation_id}")

        # Get validation
        validation = self.db_manager.get_validation_result(validation_id)
        if not validation:
            raise ValueError(f"Validation {validation_id} not found")

        # Build export data
        export_data = {
            "validation": self._serialize_validation(validation)
        }

        # Optionally include recommendations
        if include_recommendations:
            recommendations = self.db_manager.get_recommendations(validation_id)
            export_data["recommendations"] = [
                self._serialize_recommendation(r) for r in recommendations
            ]

        # Create export
        json_export = export_to_json(export_data)
        metadata = create_export_metadata({"validation_id": validation_id})

        return {
            "success": True,
            "export_data": json_export,
            "metadata": metadata
        }

    def export_recommendations(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Export recommendations to JSON.

        Args:
            params: {
                "validation_id": str (required)
            }

        Returns:
            {
                "success": bool,
                "export_data": str (JSON string),
                "metadata": Dict
            }
        """
        self.validate_params(params, required=["validation_id"])

        validation_id = params["validation_id"]

        self.logger.info(f"Exporting recommendations for: {validation_id}")

        # Get recommendations
        recommendations = self.db_manager.get_recommendations(validation_id)

        # Build export data
        export_data = {
            "validation_id": validation_id,
            "recommendations": [
                self._serialize_recommendation(r) for r in recommendations
            ]
        }

        # Create export
        json_export = export_to_json(export_data)
        metadata = create_export_metadata({"validation_id": validation_id})

        return {
            "success": True,
            "export_data": json_export,
            "metadata": metadata
        }

    def export_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Export workflow report to JSON.

        Args:
            params: {
                "workflow_id": str (required),
                "include_validations": bool (optional, default False)
            }

        Returns:
            {
                "success": bool,
                "export_data": str (JSON string),
                "metadata": Dict
            }
        """
        self.validate_params(params, required=["workflow_id"],
                           optional={"include_validations": False})

        workflow_id = params["workflow_id"]
        include_validations = params["include_validations"]

        self.logger.info(f"Exporting workflow: {workflow_id}")

        # Get workflow
        workflow = self.db_manager.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        # Build export data
        export_data = {
            "workflow": self._serialize_workflow(workflow)
        }

        # Optionally include validations
        if include_validations:
            validations = self.db_manager.get_workflow_validations(workflow_id)
            export_data["validations"] = [
                self._serialize_validation(v) for v in validations
            ]

        # Create export
        json_export = export_to_json(export_data)
        metadata = create_export_metadata({"workflow_id": workflow_id})

        return {
            "success": True,
            "export_data": json_export,
            "metadata": metadata
        }

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _serialize_validation(self, validation) -> Dict[str, Any]:
        """Serialize validation record."""
        return {
            "id": validation.id,
            "file_path": validation.file_path,
            "status": validation.status.value if hasattr(validation.status, 'value') else str(validation.status),
            "severity": validation.severity,
            "rules_applied": validation.rules_applied,
            "validation_results": validation.validation_results,
            "notes": validation.notes,
            "created_at": validation.created_at.isoformat() if validation.created_at else None,
            "updated_at": validation.updated_at.isoformat() if validation.updated_at else None
        }

    def _serialize_recommendation(self, recommendation) -> Dict[str, Any]:
        """Serialize recommendation record."""
        return {
            "id": recommendation.id,
            "validation_id": recommendation.validation_id,
            "type": recommendation.type,
            "title": recommendation.title,
            "description": recommendation.description,
            "confidence": recommendation.confidence,
            "status": recommendation.status.value if hasattr(recommendation.status, 'value') else str(recommendation.status),
            "created_at": recommendation.created_at.isoformat() if recommendation.created_at else None
        }

    def _serialize_workflow(self, workflow) -> Dict[str, Any]:
        """Serialize workflow record."""
        return {
            "id": workflow.id,
            "type": workflow.type,
            "status": workflow.state.value if hasattr(workflow.state, 'value') else str(workflow.state),
            "params": workflow.input_params,
            "metadata": workflow.workflow_metadata,
            "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
            "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None,
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None
        }
