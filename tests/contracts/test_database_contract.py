"""
Contract tests for core.database.DatabaseManager.

These tests verify that the DatabaseManager public API remains stable.
Breaking changes here cause cascading failures across the test suite.
"""

import pytest
from core.database import DatabaseManager, db_manager


class TestDatabaseManagerContract:
    """Verify DatabaseManager has all required public methods."""

    def test_database_manager_interface(self):
        """DatabaseManager must have all required public methods."""
        required_methods = [
            # Connection/setup
            "init_database",
            "is_connected",
            "has_required_schema",
            "ensure_schema_idempotent",
            "create_tables",
            "get_session",

            # Workflow methods
            "get_workflow",
            "create_workflow",
            "update_workflow",
            "list_workflows",

            # Cache methods
            "get_cache_entry",
            "store_cache_entry",
            "cleanup_expired_cache",

            # ValidationResult methods
            "create_validation_result",
            "list_validation_results",
            "get_validation_result",
            "get_latest_validation_result",
            "get_validation_history",

            # Recommendation methods
            "create_recommendation",
            "get_recommendation",
            "list_recommendations",
            "update_recommendation_status",
            "mark_recommendation_applied",
            "calculate_recommendation_confidence",
            "update_recommendation_confidence",

            # AuditLog methods
            "create_audit_log",
            "list_audit_logs",

            # Cleanup/management methods
            "delete_recommendation",
            "soft_delete_workflows",
            "delete_all_validations",
            "delete_all_workflows",
            "delete_all_recommendations",
            "delete_all_audit_logs",
            "reset_system",

            # Workflow metrics
            "update_workflow_metrics",
            "get_workflow_metrics",
            "get_workflow_stats",

            # Reporting methods
            "generate_workflow_report",
            "generate_validation_report",
            "compare_validations",
            "get_validations_without_recommendations",

            # Test utilities
            "mark_ingested",
            "query_unknown_source",
        ]

        for method in required_methods:
            assert hasattr(DatabaseManager, method), \
                f"DatabaseManager missing required method: {method}"
            assert callable(getattr(DatabaseManager, method)), \
                f"DatabaseManager.{method} exists but is not callable"

    def test_singleton_instance_exists(self):
        """Verify db_manager singleton is available."""
        assert db_manager is not None
        assert isinstance(db_manager, DatabaseManager)

    def test_get_session_returns_session(self):
        """get_session() must return a session object."""
        session = db_manager.get_session()
        assert session is not None
        # Should have query method (basic session check)
        assert hasattr(session, 'query')
        assert hasattr(session, 'commit')
        assert hasattr(session, 'rollback')
        session.close()

    def test_is_connected_returns_bool(self):
        """is_connected() must return a boolean."""
        result = db_manager.is_connected()
        assert isinstance(result, bool)

    def test_has_required_schema_returns_bool(self):
        """has_required_schema() must return a boolean."""
        result = db_manager.has_required_schema()
        assert isinstance(result, bool)

    def test_list_workflows_returns_list(self):
        """list_workflows() must return a list."""
        result = db_manager.list_workflows(limit=1)
        assert isinstance(result, list)

    def test_list_validation_results_returns_list(self):
        """list_validation_results() must return a list."""
        result = db_manager.list_validation_results(limit=1)
        assert isinstance(result, list)

    def test_list_recommendations_returns_list(self):
        """list_recommendations() must return a list."""
        result = db_manager.list_recommendations(limit=1)
        assert isinstance(result, list)

    def test_list_audit_logs_returns_list(self):
        """list_audit_logs() must return a list."""
        result = db_manager.list_audit_logs(limit=1)
        assert isinstance(result, list)

    def test_get_statistics_method_exists(self):
        """get_statistics() method should exist for metrics."""
        # This is optional but commonly used
        result = db_manager.get_statistics() if hasattr(db_manager, 'get_statistics') else None
        # Just verify it doesn't crash if it exists
        if result is not None:
            assert isinstance(result, dict)

    def test_cleanup_expired_cache_returns_count(self):
        """cleanup_expired_cache() must return an integer count."""
        result = db_manager.cleanup_expired_cache()
        assert isinstance(result, int)
        assert result >= 0

    def test_create_validation_result_required_params(self):
        """create_validation_result() must accept all required parameters."""
        import inspect
        sig = inspect.signature(db_manager.create_validation_result)

        # These are the critical parameters
        required_params = {
            'file_path', 'rules_applied', 'validation_results',
            'notes', 'severity', 'status'
        }

        # Get actual parameters (excluding self)
        actual_params = set(sig.parameters.keys())

        for param in required_params:
            assert param in actual_params, \
                f"create_validation_result missing required parameter: {param}"

    def test_create_recommendation_required_params(self):
        """create_recommendation() must accept all required parameters."""
        import inspect
        sig = inspect.signature(db_manager.create_recommendation)

        required_params = {
            'validation_id', 'type', 'title', 'description'
        }

        actual_params = set(sig.parameters.keys())

        for param in required_params:
            assert param in actual_params, \
                f"create_recommendation missing required parameter: {param}"

    def test_create_workflow_required_params(self):
        """create_workflow() must accept all required parameters."""
        import inspect
        sig = inspect.signature(db_manager.create_workflow)

        required_params = {'workflow_type', 'input_params'}
        actual_params = set(sig.parameters.keys())

        for param in required_params:
            assert param in actual_params, \
                f"create_workflow missing required parameter: {param}"


class TestDatabaseEnums:
    """Verify all required enums exist."""

    def test_validation_status_enum_exists(self):
        """ValidationStatus enum must exist with required values."""
        from core.database import ValidationStatus

        required_values = ['PASS', 'FAIL', 'WARNING', 'SKIPPED', 'APPROVED', 'REJECTED', 'ENHANCED']

        for value in required_values:
            assert hasattr(ValidationStatus, value), \
                f"ValidationStatus missing value: {value}"

    def test_recommendation_status_enum_exists(self):
        """RecommendationStatus enum must exist with required values."""
        from core.database import RecommendationStatus

        required_values = ['PROPOSED', 'PENDING', 'APPROVED', 'REJECTED', 'APPLIED']

        for value in required_values:
            assert hasattr(RecommendationStatus, value), \
                f"RecommendationStatus missing value: {value}"

    def test_workflow_state_enum_exists(self):
        """WorkflowState enum must exist with required values."""
        from core.database import WorkflowState

        required_values = ['PENDING', 'RUNNING', 'PAUSED', 'COMPLETED', 'FAILED', 'CANCELLED']

        for value in required_values:
            assert hasattr(WorkflowState, value), \
                f"WorkflowState missing value: {value}"


class TestDatabaseModels:
    """Verify ORM models exist with required methods."""

    def test_validation_result_model_exists(self):
        """ValidationResult model must exist with to_dict() method."""
        from core.database import ValidationResult

        assert hasattr(ValidationResult, 'to_dict')
        assert callable(ValidationResult.to_dict)

    def test_recommendation_model_exists(self):
        """Recommendation model must exist with to_dict() method."""
        from core.database import Recommendation

        assert hasattr(Recommendation, 'to_dict')
        assert callable(Recommendation.to_dict)

    def test_workflow_model_exists(self):
        """Workflow model must exist with to_dict() method."""
        from core.database import Workflow

        assert hasattr(Workflow, 'to_dict')
        assert callable(Workflow.to_dict)

    def test_audit_log_model_exists(self):
        """AuditLog model must exist with to_dict() method."""
        from core.database import AuditLog

        assert hasattr(AuditLog, 'to_dict')
        assert callable(AuditLog.to_dict)

    def test_checkpoint_model_exists(self):
        """Checkpoint model must exist with to_dict() method."""
        from core.database import Checkpoint

        assert hasattr(Checkpoint, 'to_dict')
        assert callable(Checkpoint.to_dict)

    def test_cache_entry_model_exists(self):
        """CacheEntry model must exist."""
        from core.database import CacheEntry

        # CacheEntry is a simple ORM model without to_dict
        assert CacheEntry is not None
        assert hasattr(CacheEntry, '__tablename__')
        assert CacheEntry.__tablename__ == 'cache_entries'
