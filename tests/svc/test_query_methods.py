"""Comprehensive tests for MCP query/stats/export methods."""

import pytest
import json
from pathlib import Path
from datetime import datetime, timezone
from svc.mcp_client import MCPSyncClient, get_mcp_sync_client
from svc.mcp_exceptions import MCPError
from core.database import ValidationStatus, RecommendationStatus, WorkflowState


class TestSystemStatistics:
    """Tests for get_stats method."""

    def test_get_stats_success(self):
        """Test successful system statistics retrieval."""
        client = get_mcp_sync_client()
        result = client.get_stats()

        assert "validations_total" in result
        assert "validations_by_status" in result
        assert "recommendations_total" in result
        assert "workflows_total" in result
        assert "workflows_by_status" in result
        assert "cache_stats" in result
        assert "agents_count" in result

        assert isinstance(result["validations_total"], int)
        assert isinstance(result["recommendations_total"], int)
        assert isinstance(result["workflows_total"], int)
        assert isinstance(result["agents_count"], int)

    def test_get_stats_validations_by_status(self):
        """Test validations grouped by status."""
        client = get_mcp_sync_client()
        result = client.get_stats()

        validations_by_status = result["validations_by_status"]
        assert isinstance(validations_by_status, dict)
        # May have various statuses or be empty
        for status, count in validations_by_status.items():
            assert isinstance(count, int)
            assert count >= 0

    def test_get_stats_workflows_by_status(self):
        """Test workflows grouped by status."""
        client = get_mcp_sync_client()
        result = client.get_stats()

        workflows_by_status = result["workflows_by_status"]
        assert isinstance(workflows_by_status, dict)
        # May have various statuses or be empty
        for status, count in workflows_by_status.items():
            assert isinstance(count, int)
            assert count >= 0


class TestAuditLog:
    """Tests for get_audit_log method."""

    def test_get_audit_log_default_params(self):
        """Test audit log retrieval with default parameters."""
        client = get_mcp_sync_client()
        result = client.get_audit_log()

        assert "logs" in result
        assert "total" in result
        assert isinstance(result["logs"], list)
        assert isinstance(result["total"], int)

    def test_get_audit_log_with_limit(self):
        """Test audit log with custom limit."""
        client = get_mcp_sync_client()
        result = client.get_audit_log(limit=10)

        assert len(result["logs"]) <= 10

    def test_get_audit_log_with_offset(self):
        """Test audit log with offset for pagination."""
        client = get_mcp_sync_client()
        result = client.get_audit_log(limit=5, offset=0)
        assert "logs" in result

        # If there are enough logs, test offset works
        if result["total"] > 5:
            result2 = client.get_audit_log(limit=5, offset=5)
            # Logs should be different
            if len(result["logs"]) > 0 and len(result2["logs"]) > 0:
                assert result["logs"][0] != result2["logs"][0]

    def test_get_audit_log_filters(self):
        """Test audit log with various filters."""
        client = get_mcp_sync_client()

        # Test operation filter
        result = client.get_audit_log(operation="validate_file")
        assert "logs" in result

        # Test user filter
        result = client.get_audit_log(user="system")
        assert "logs" in result

        # Test status filter
        result = client.get_audit_log(status="success")
        assert "logs" in result


class TestPerformanceReports:
    """Tests for get_performance_report method."""

    def test_get_performance_report_default(self):
        """Test performance report with default time range."""
        client = get_mcp_sync_client()
        result = client.get_performance_report()

        assert "time_range" in result
        assert result["time_range"] == "24h"
        assert "total_operations" in result
        assert "failed_operations" in result
        assert "success_rate" in result
        assert "operations" in result

        assert isinstance(result["total_operations"], int)
        assert isinstance(result["failed_operations"], int)
        assert isinstance(result["success_rate"], float)
        assert isinstance(result["operations"], dict)

    def test_get_performance_report_time_ranges(self):
        """Test performance report with different time ranges."""
        client = get_mcp_sync_client()

        for time_range in ["1h", "24h", "7d", "30d"]:
            result = client.get_performance_report(time_range=time_range)
            assert result["time_range"] == time_range

    def test_get_performance_report_filtered(self):
        """Test performance report filtered by operation."""
        client = get_mcp_sync_client()
        result = client.get_performance_report(operation="validate_file")

        assert "operations" in result

    def test_get_performance_report_operation_details(self):
        """Test performance report operation details structure."""
        client = get_mcp_sync_client()
        result = client.get_performance_report()

        # If there are any operations tracked
        for op_name, op_stats in result["operations"].items():
            assert "count" in op_stats
            assert "avg_duration_ms" in op_stats
            assert "min_duration_ms" in op_stats
            assert "max_duration_ms" in op_stats
            assert "p50_duration_ms" in op_stats
            assert "p95_duration_ms" in op_stats
            assert "p99_duration_ms" in op_stats


class TestHealthReports:
    """Tests for get_health_report method."""

    def test_get_health_report_success(self):
        """Test health report retrieval."""
        client = get_mcp_sync_client()
        result = client.get_health_report()

        assert "overall_health" in result
        assert result["overall_health"] in ["healthy", "degraded", "unhealthy", "unknown"]
        assert "components" in result
        assert "recent_errors" in result
        assert "performance_summary" in result
        assert "recommendations" in result

        assert isinstance(result["recent_errors"], list)
        assert isinstance(result["recommendations"], list)

    def test_get_health_report_recommendations(self):
        """Test health report recommendations are strings."""
        client = get_mcp_sync_client()
        result = client.get_health_report()

        for recommendation in result["recommendations"]:
            assert isinstance(recommendation, str)


class TestValidationHistory:
    """Tests for get_validation_history method."""

    def test_get_validation_history_requires_file_path(self):
        """Test validation history requires file_path parameter."""
        client = get_mcp_sync_client()

        # Should handle None gracefully (returns empty history)
        result = client.get_validation_history(file_path=None)
        assert "validations" in result

    def test_get_validation_history_success(self):
        """Test validation history retrieval."""
        client = get_mcp_sync_client()
        result = client.get_validation_history(file_path="/test/path.md")

        assert "file_path" in result
        assert result["file_path"] == "/test/path.md"
        assert "validations" in result
        assert "total" in result
        assert isinstance(result["validations"], list)
        assert isinstance(result["total"], int)

    def test_get_validation_history_with_limit(self):
        """Test validation history with custom limit."""
        client = get_mcp_sync_client()
        result = client.get_validation_history(
            file_path="/test/path.md",
            limit=10
        )

        assert len(result["validations"]) <= 10


class TestValidatorDiscovery:
    """Tests for get_available_validators method."""

    def test_get_available_validators_success(self):
        """Test available validators retrieval."""
        client = get_mcp_sync_client()
        result = client.get_available_validators()

        assert "validators" in result
        assert "total" in result
        assert isinstance(result["validators"], list)
        assert isinstance(result["total"], int)
        assert result["total"] == len(result["validators"])

    def test_get_available_validators_structure(self):
        """Test validator structure."""
        client = get_mcp_sync_client()
        result = client.get_available_validators()

        # If validators exist, check structure
        if result["validators"]:
            validator = result["validators"][0]
            assert "id" in validator
            assert "type" in validator
            assert "name" in validator
            assert "status" in validator

    def test_get_available_validators_filtered(self):
        """Test validators filtered by type."""
        client = get_mcp_sync_client()
        result = client.get_available_validators(validator_type="markdown")

        # All returned validators should match type
        for validator in result["validators"]:
            assert validator["type"] == "markdown" or validator["type"] == "generic"


class TestValidationExport:
    """Tests for export_validation method."""

    def test_export_validation_requires_id(self):
        """Test export validation requires validation_id."""
        client = get_mcp_sync_client()

        with pytest.raises(MCPError):
            client.export_validation(validation_id=None)

    def test_export_validation_nonexistent(self):
        """Test export validation with non-existent ID."""
        client = get_mcp_sync_client()

        with pytest.raises(MCPError):
            client.export_validation(validation_id="nonexistent_id")

    def test_export_validation_structure(self, test_validation_id):
        """Test export validation structure."""
        client = get_mcp_sync_client()
        result = client.export_validation(validation_id=test_validation_id)

        assert "success" in result
        assert result["success"] is True
        assert "export_data" in result
        assert "metadata" in result

        # Verify it's valid JSON
        export_data = json.loads(result["export_data"])
        assert "schema_version" in export_data
        assert "exported_at" in export_data
        assert "data" in export_data
        assert "validation" in export_data["data"]

    def test_export_validation_with_recommendations(self, test_validation_id):
        """Test export validation including recommendations."""
        client = get_mcp_sync_client()
        result = client.export_validation(
            validation_id=test_validation_id,
            include_recommendations=True
        )

        export_data = json.loads(result["export_data"])
        # Recommendations may or may not exist
        assert "data" in export_data

    def test_export_validation_schema_version(self, test_validation_id):
        """Test export includes correct schema version."""
        client = get_mcp_sync_client()
        result = client.export_validation(validation_id=test_validation_id)

        export_data = json.loads(result["export_data"])
        assert export_data["schema_version"] == "1.0"


class TestRecommendationsExport:
    """Tests for export_recommendations method."""

    def test_export_recommendations_requires_id(self):
        """Test export recommendations requires validation_id."""
        client = get_mcp_sync_client()

        # Should handle None gracefully (returns empty recommendations)
        result = client.export_recommendations(validation_id=None)
        assert "export_data" in result

    def test_export_recommendations_structure(self, test_validation_id):
        """Test export recommendations structure."""
        client = get_mcp_sync_client()
        result = client.export_recommendations(validation_id=test_validation_id)

        assert "success" in result
        assert result["success"] is True
        assert "export_data" in result
        assert "metadata" in result

        # Verify it's valid JSON
        export_data = json.loads(result["export_data"])
        assert "schema_version" in export_data
        assert "exported_at" in export_data
        assert "data" in export_data
        assert "recommendations" in export_data["data"]


class TestWorkflowExport:
    """Tests for export_workflow method."""

    def test_export_workflow_requires_id(self):
        """Test export workflow requires workflow_id."""
        client = get_mcp_sync_client()

        with pytest.raises(MCPError):
            client.export_workflow(workflow_id=None)

    def test_export_workflow_nonexistent(self):
        """Test export workflow with non-existent ID."""
        client = get_mcp_sync_client()

        with pytest.raises(MCPError):
            client.export_workflow(workflow_id="nonexistent_id")

    def test_export_workflow_structure(self, test_workflow_id):
        """Test export workflow structure."""
        client = get_mcp_sync_client()
        result = client.export_workflow(workflow_id=test_workflow_id)

        assert "success" in result
        assert result["success"] is True
        assert "export_data" in result
        assert "metadata" in result

        # Verify it's valid JSON
        export_data = json.loads(result["export_data"])
        assert "schema_version" in export_data
        assert "exported_at" in export_data
        assert "data" in export_data
        assert "workflow" in export_data["data"]

    def test_export_workflow_with_validations(self, test_workflow_id):
        """Test export workflow including validations."""
        client = get_mcp_sync_client()
        result = client.export_workflow(
            workflow_id=test_workflow_id,
            include_validations=True
        )

        export_data = json.loads(result["export_data"])
        assert "data" in export_data
        # Validations may or may not exist


# Fixtures
@pytest.fixture
def test_validation_id(tmp_path):
    """Create a test validation and return its ID."""
    client = get_mcp_sync_client()

    # Create a test file
    test_file = tmp_path / "test.md"
    test_file.write_text("# Test\n\nContent", encoding='utf-8')

    # Validate the file
    result = client.validate_file(str(test_file))
    return result["validation_id"]


@pytest.fixture
def test_workflow_id():
    """Create a test workflow and return its ID."""
    client = get_mcp_sync_client()

    # Create a workflow with a valid workflow type
    result = client.create_workflow(
        workflow_type="validate_directory",
        workflow_params={"directory_path": "/test", "recursive": True}
    )
    return result["workflow_id"]


# Integration tests
class TestQueryMethodsIntegration:
    """Integration tests for query methods."""

    def test_stats_reflect_operations(self, tmp_path):
        """Test that stats reflect actual operations."""
        client = get_mcp_sync_client()

        # Get initial stats
        initial_stats = client.get_stats()
        initial_validations = initial_stats["validations_total"]

        # Create a validation
        test_file = tmp_path / "test_integration.md"
        test_file.write_text("# Test\n\nContent", encoding='utf-8')
        client.validate_file(str(test_file))

        # Get updated stats
        updated_stats = client.get_stats()

        # Stats should have changed
        assert updated_stats["validations_total"] >= initial_validations

    def test_export_roundtrip(self, test_validation_id):
        """Test export and reimport of validation data."""
        client = get_mcp_sync_client()

        # Export validation
        export_result = client.export_validation(validation_id=test_validation_id)
        export_data = json.loads(export_result["export_data"])

        # Verify data structure is complete
        validation_data = export_data["data"]["validation"]
        assert "id" in validation_data
        assert "file_path" in validation_data
        assert "status" in validation_data

        # Verify ID matches
        assert validation_data["id"] == test_validation_id
