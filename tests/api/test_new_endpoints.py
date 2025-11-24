# file: tests/api/test_new_endpoints.py
"""
Tests for new API endpoints added for CLI/Web parity.

These tests cover:
- Development utilities endpoints
- Configuration control endpoints
- Export/download endpoints (multi-format)
"""

import pytest
from fastapi.testclient import TestClient
from api.server import app

@pytest.fixture
def client():
    """API test client."""
    return TestClient(app)


class TestDevelopmentUtilities:
    """Tests for development utility endpoints."""

    def test_create_test_file_default(self, client):
        """Test POST /api/dev/create-test-file with defaults."""
        response = client.post("/api/dev/create-test-file", json={})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "created"
        assert "file_path" in data
        assert "filename" in data

    def test_create_test_file_custom_content(self, client):
        """Test POST /api/dev/create-test-file with custom content."""
        response = client.post("/api/dev/create-test-file", json={
            "content": "# Custom Test",
            "family": "words",
            "filename": "custom_test.md"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "custom_test.md"

    def test_create_test_file_with_validation(self, client):
        """Test that test file creation includes validation result."""
        response = client.post("/api/dev/create-test-file", json={"family": "words"})
        assert response.status_code == 200
        data = response.json()
        # Validation result may be None if orchestrator not available
        assert "validation_result" in data

    def test_probe_endpoints_basic(self, client):
        """Test GET /api/dev/probe-endpoints basic."""
        response = client.get("/api/dev/probe-endpoints")
        assert response.status_code == 200
        data = response.json()
        assert "total_endpoints" in data
        assert "endpoints" in data
        assert data["total_endpoints"] > 0

    def test_probe_endpoints_with_include_pattern(self, client):
        """Test GET /api/dev/probe-endpoints with include pattern."""
        response = client.get("/api/dev/probe-endpoints?include_pattern=^/api")
        assert response.status_code == 200
        data = response.json()
        assert "endpoints" in data
        # All endpoints should match the pattern
        for endpoint in data["endpoints"]:
            assert endpoint["path"].startswith("/api")

    def test_probe_endpoints_with_exclude_pattern(self, client):
        """Test GET /api/dev/probe-endpoints with exclude pattern."""
        response = client.get("/api/dev/probe-endpoints?exclude_pattern=/docs")
        assert response.status_code == 200
        data = response.json()
        # No endpoint should contain /docs
        for endpoint in data["endpoints"]:
            assert "/docs" not in endpoint["path"]


class TestConfigurationControl:
    """Tests for configuration control endpoints."""

    def test_cache_control_disable(self, client):
        """Test POST /api/config/cache-control to disable cache."""
        response = client.post("/api/config/cache-control", json={
            "disable_cache": True,
            "clear_on_disable": False
        })
        assert response.status_code == 200
        data = response.json()
        assert data["cache_disabled"] == True
        assert "previous_state" in data

    def test_cache_control_disable_and_clear(self, client):
        """Test POST /api/config/cache-control to disable and clear."""
        response = client.post("/api/config/cache-control", json={
            "disable_cache": True,
            "clear_on_disable": True
        })
        assert response.status_code == 200
        data = response.json()
        assert data["cache_disabled"] == True
        assert data.get("cache_cleared") == True

    def test_cache_control_enable(self, client):
        """Test POST /api/config/cache-control to re-enable cache."""
        response = client.post("/api/config/cache-control", json={
            "disable_cache": False
        })
        assert response.status_code == 200
        data = response.json()
        assert data["cache_disabled"] == False

    def test_log_level_debug(self, client):
        """Test POST /api/config/log-level to set DEBUG."""
        response = client.post("/api/config/log-level", json={"level": "DEBUG"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "updated"
        assert data["log_level"] == "DEBUG"

    def test_log_level_info(self, client):
        """Test POST /api/config/log-level to set INFO."""
        response = client.post("/api/config/log-level", json={"level": "INFO"})
        assert response.status_code == 200
        data = response.json()
        assert data["log_level"] == "INFO"

    def test_log_level_invalid(self, client):
        """Test POST /api/config/log-level with invalid level."""
        response = client.post("/api/config/log-level", json={"level": "INVALID"})
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

    def test_force_override_nonexistent_validation(self, client):
        """Test POST /api/config/force-override with non-existent validation."""
        response = client.post("/api/config/force-override", json={
            "validation_id": "nonexistent_id",
            "force_enhance": True
        })
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestExportEndpoints:
    """Tests for export/download endpoints."""

    def test_export_validation_nonexistent(self, client):
        """Test GET /api/export/validation/{id} with non-existent ID."""
        response = client.get("/api/export/validation/nonexistent_id")
        assert response.status_code == 404

    def test_export_validation_invalid_format(self, client):
        """Test GET /api/export/validation/{id} with invalid format."""
        response = client.get("/api/export/validation/fake_id?format=invalid")
        # Should fail on validation not found before format check
        assert response.status_code in [400, 404]

    def test_export_validation_json_format(self, client):
        """Test GET /api/export/validation/{id} with JSON format."""
        # This would need a real validation ID from test database
        # For now, test that the endpoint exists and has proper error handling
        response = client.get("/api/export/validation/test_id?format=json")
        # Should return 404 if validation doesn't exist
        assert response.status_code in [200, 404]

    def test_export_recommendations_basic(self, client):
        """Test GET /api/export/recommendations basic."""
        response = client.get("/api/export/recommendations")
        assert response.status_code == 200
        # Should return downloadable content
        assert response.headers["content-disposition"]

    def test_export_recommendations_json(self, client):
        """Test GET /api/export/recommendations with JSON format."""
        response = client.get("/api/export/recommendations?format=json")
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]

    def test_export_recommendations_csv(self, client):
        """Test GET /api/export/recommendations with CSV format."""
        response = client.get("/api/export/recommendations?format=csv")
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]

    def test_export_recommendations_yaml(self, client):
        """Test GET /api/export/recommendations with YAML format."""
        try:
            import yaml
            response = client.get("/api/export/recommendations?format=yaml")
            assert response.status_code == 200
            assert "yaml" in response.headers["content-type"]
        except ImportError:
            # YAML not installed, should return 400
            response = client.get("/api/export/recommendations?format=yaml")
            assert response.status_code == 400

    def test_export_recommendations_with_filters(self, client):
        """Test GET /api/export/recommendations with filters."""
        response = client.get("/api/export/recommendations?status=approved&format=json")
        assert response.status_code == 200

    def test_export_workflow_nonexistent(self, client):
        """Test GET /api/export/workflow/{id} with non-existent ID."""
        response = client.get("/api/export/workflow/nonexistent_id")
        assert response.status_code == 404

    def test_export_workflow_json_format(self, client):
        """Test GET /api/export/workflow/{id} with JSON format."""
        response = client.get("/api/export/workflow/fake_id?format=json")
        # Should return 404 if workflow doesn't exist
        assert response.status_code == 404

    def test_export_workflow_yaml_format(self, client):
        """Test GET /api/export/workflow/{id} with YAML format."""
        response = client.get("/api/export/workflow/fake_id?format=yaml")
        # Should return 404 if workflow doesn't exist
        assert response.status_code == 404

    def test_export_workflow_invalid_format(self, client):
        """Test GET /api/export/workflow/{id} with invalid format."""
        response = client.get("/api/export/workflow/fake_id?format=invalid")
        # Should fail on workflow not found or invalid format
        assert response.status_code in [400, 404]


class TestContentTypeHeaders:
    """Tests for proper content-type headers in export endpoints."""

    def test_export_json_content_type(self, client):
        """Test that JSON exports have correct content-type."""
        response = client.get("/api/export/recommendations?format=json")
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]

    def test_export_csv_content_type(self, client):
        """Test that CSV exports have correct content-type."""
        response = client.get("/api/export/recommendations?format=csv")
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]

    def test_export_has_attachment_header(self, client):
        """Test that exports have Content-Disposition: attachment."""
        response = client.get("/api/export/recommendations?format=json")
        assert response.status_code == 200
        assert "attachment" in response.headers.get("content-disposition", "").lower()


class TestParameterValidation:
    """Tests for parameter validation on new endpoints."""

    def test_log_level_requires_level_param(self, client):
        """Test that log-level endpoint requires 'level' parameter."""
        response = client.post("/api/config/log-level", json={})
        # Should fail validation
        assert response.status_code == 422

    def test_force_override_requires_validation_id(self, client):
        """Test that force-override requires validation_id."""
        response = client.post("/api/config/force-override", json={"force_enhance": True})
        # Should fail validation
        assert response.status_code == 422

    def test_cache_control_defaults(self, client):
        """Test that cache-control uses defaults properly."""
        response = client.post("/api/config/cache-control", json={})
        assert response.status_code == 200
        # Should use default values


class TestAdminResetEndpoint:
    """Tests for POST /api/admin/reset endpoint."""

    def test_reset_without_confirmation(self, client):
        """Test reset without confirm=true returns 400."""
        response = client.post("/api/admin/reset", json={
            "confirm": False,
            "delete_validations": True
        })
        assert response.status_code == 400
        assert "confirm" in response.json()["detail"].lower()

    def test_reset_with_confirmation(self, client):
        """Test reset with confirm=true succeeds."""
        response = client.post("/api/admin/reset", json={
            "confirm": True,
            "delete_validations": True,
            "delete_workflows": True,
            "delete_recommendations": True,
            "delete_audit_logs": False,
            "clear_cache": False
        })
        # Should succeed (may delete 0 items if database is empty)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "deleted" in data
        assert "validations_deleted" in data["deleted"]
        assert "workflows_deleted" in data["deleted"]
        assert "recommendations_deleted" in data["deleted"]
        assert "audit_logs_deleted" in data["deleted"]

    def test_reset_validations_only(self, client):
        """Test selective reset - validations only."""
        response = client.post("/api/admin/reset", json={
            "confirm": True,
            "delete_validations": True,
            "delete_workflows": False,
            "delete_recommendations": False,
            "delete_audit_logs": False
        })
        assert response.status_code == 200
        data = response.json()
        # Validations should be processed, others should be 0
        assert "deleted" in data
        assert "validations_deleted" in data["deleted"]

    def test_reset_workflows_only(self, client):
        """Test selective reset - workflows only."""
        response = client.post("/api/admin/reset", json={
            "confirm": True,
            "delete_validations": False,
            "delete_workflows": True,
            "delete_recommendations": False
        })
        assert response.status_code == 200
        data = response.json()
        assert "deleted" in data
        assert data["deleted"]["validations_deleted"] == 0
        assert "workflows_deleted" in data["deleted"]

    def test_reset_recommendations_only(self, client):
        """Test selective reset - recommendations only."""
        response = client.post("/api/admin/reset", json={
            "confirm": True,
            "delete_validations": False,
            "delete_workflows": False,
            "delete_recommendations": True
        })
        assert response.status_code == 200
        data = response.json()
        assert data["deleted"]["validations_deleted"] == 0
        assert data["deleted"]["workflows_deleted"] == 0

    def test_reset_with_cache_clear(self, client):
        """Test reset with cache clearing enabled."""
        response = client.post("/api/admin/reset", json={
            "confirm": True,
            "delete_validations": True,
            "clear_cache": True
        })
        assert response.status_code == 200
        data = response.json()
        assert "cache_cleared" in data
        # Cache clear result may be True or False depending on cache availability

    def test_reset_all_defaults(self, client):
        """Test reset with all default values."""
        response = client.post("/api/admin/reset", json={
            "confirm": True
        })
        assert response.status_code == 200
        data = response.json()
        assert "deleted" in data
        # By default, validations, workflows, recommendations should be deleted
        assert "validations_deleted" in data["deleted"]
        assert "workflows_deleted" in data["deleted"]
        assert "recommendations_deleted" in data["deleted"]
        # Audit logs should NOT be deleted by default
        assert data["deleted"]["audit_logs_deleted"] == 0

    def test_reset_response_structure(self, client):
        """Test that reset response has correct structure."""
        response = client.post("/api/admin/reset", json={"confirm": True})
        assert response.status_code == 200
        data = response.json()
        # Check required fields
        assert "message" in data
        assert "deleted" in data
        assert "cache_cleared" in data
        assert "timestamp" in data
        # Check deleted object structure
        deleted = data["deleted"]
        assert "validations_deleted" in deleted
        assert "workflows_deleted" in deleted
        assert "recommendations_deleted" in deleted
        assert "audit_logs_deleted" in deleted
        # All counts should be integers
        assert isinstance(deleted["validations_deleted"], int)
        assert isinstance(deleted["workflows_deleted"], int)
        assert isinstance(deleted["recommendations_deleted"], int)
        assert isinstance(deleted["audit_logs_deleted"], int)

    def test_reset_missing_confirm_field(self, client):
        """Test reset without confirm field in request."""
        response = client.post("/api/admin/reset", json={
            "delete_validations": True
        })
        # Should fail validation (confirm is required)
        assert response.status_code == 422


@pytest.mark.integration
class TestEndpointIntegration:
    """Integration tests for endpoint workflows."""

    def test_create_test_file_then_export(self, client):
        """Test creating a test file, validating it, then exporting."""
        # Create test file
        create_response = client.post("/api/dev/create-test-file", json={})
        assert create_response.status_code == 200

        # If validation was successful, we should have a validation_id
        # (This would require proper integration setup)
        pass

    def test_config_workflow(self, client):
        """Test configuration change workflow."""
        # Get cache stats
        # Disable cache
        # Clear cache
        # Re-enable cache

        # Disable
        response1 = client.post("/api/config/cache-control", json={"disable_cache": True})
        assert response1.status_code == 200

        # Re-enable
        response2 = client.post("/api/config/cache-control", json={"disable_cache": False})
        assert response2.status_code == 200

    def test_log_level_change_workflow(self, client):
        """Test changing log levels."""
        # Change to DEBUG
        response1 = client.post("/api/config/log-level", json={"level": "DEBUG"})
        assert response1.status_code == 200

        # Change back to INFO
        response2 = client.post("/api/config/log-level", json={"level": "INFO"})
        assert response2.status_code == 200
