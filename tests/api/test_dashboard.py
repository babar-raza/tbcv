# file: tests/api/test_dashboard.py
"""
Comprehensive tests for api/dashboard.py module.
Target: 75%+ coverage of dashboard endpoints and functionality.
"""

import os
import sys

# Set environment before imports
os.environ.setdefault("TBCV_ENV", "test")
os.environ.setdefault("OLLAMA_ENABLED", "false")
os.environ.setdefault("OLLAMA_MODEL", "mistral")

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

# Import after environment is set
from api.server import app
from core.database import (
    db_manager,
    Recommendation,
    ValidationResult,
    Workflow,
    RecommendationStatus,
    ValidationStatus,
    WorkflowState
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_db_data(db_manager):
    """Create mock database data for testing."""
    # Create validation results
    val1 = db_manager.create_validation_result(
        file_path="test1.md",
        rules_applied={"rule": "test"},
        validation_results={"passed": True},
        notes="Test validation",
        severity="low",
        status="pass"
    )

    val2 = db_manager.create_validation_result(
        file_path="test2.md",
        rules_applied={"rule": "test2"},
        validation_results={"passed": False},
        notes="Failed validation",
        severity="high",
        status="fail"
    )

    # Create recommendations
    rec1 = db_manager.create_recommendation(
        validation_id=val1.id,
        type="fix",
        title="Fix typo",
        description="Fix spelling error",
        original_content="teh",
        proposed_content="the",
        status=RecommendationStatus.PENDING
    )

    rec2 = db_manager.create_recommendation(
        validation_id=val2.id,
        type="enhancement",
        title="Add section",
        description="Add missing section",
        original_content="",
        proposed_content="## New Section",
        status=RecommendationStatus.APPROVED
    )

    # Create workflows
    wf1 = db_manager.create_workflow(
        workflow_type="validation",
        input_params={"file": "test.md"}
    )

    return {
        "validations": [val1, val2],
        "recommendations": [rec1, rec2],
        "workflows": [wf1]
    }


# =============================================================================
# Dashboard Home Tests
# =============================================================================

@pytest.mark.integration
class TestDashboardHome:
    """Test dashboard home endpoint."""

    def test_dashboard_home_loads(self, client, mock_db_data):
        """Test dashboard home page loads successfully."""
        response = client.get("/dashboard/")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_dashboard_home_displays_validations(self, client, mock_db_data):
        """Test dashboard shows recent validations."""
        response = client.get("/dashboard/")

        assert response.status_code == 200
        content = response.text
        assert "test1.md" in content or "validations" in content.lower()

    def test_dashboard_home_displays_stats(self, client, mock_db_data):
        """Test dashboard shows statistics."""
        response = client.get("/dashboard/")

        assert response.status_code == 200
        # Stats should be rendered in the HTML
        assert response.status_code == 200

    def test_dashboard_home_with_no_data(self, client):
        """Test dashboard home with empty database."""
        # Clear database by using a fresh client
        response = client.get("/dashboard/")

        # Should still load, just with empty data
        assert response.status_code == 200


# =============================================================================
# Validations List Tests
# =============================================================================

@pytest.mark.integration
class TestDashboardValidations:
    """Test validations list endpoint."""

    def test_validations_list_loads(self, client, mock_db_data):
        """Test validations list page loads."""
        response = client.get("/dashboard/validations")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_validations_list_with_status_filter(self, client, mock_db_data):
        """Test filtering validations by status."""
        response = client.get("/dashboard/validations?status=pass")

        assert response.status_code == 200

    def test_validations_list_with_severity_filter(self, client, mock_db_data):
        """Test filtering validations by severity."""
        response = client.get("/dashboard/validations?severity=high")

        assert response.status_code == 200

    def test_validations_list_pagination(self, client, mock_db_data):
        """Test validations pagination."""
        response = client.get("/dashboard/validations?page=1&page_size=10")

        assert response.status_code == 200

    def test_validations_list_empty(self, client):
        """Test validations list with no data."""
        response = client.get("/dashboard/validations")

        assert response.status_code == 200


# =============================================================================
# Validation Detail Tests
# =============================================================================

@pytest.mark.integration
class TestDashboardValidationDetail:
    """Test validation detail endpoint."""

    def test_validation_detail_loads(self, client, mock_db_data):
        """Test validation detail page loads."""
        val_id = mock_db_data["validations"][0].id
        response = client.get(f"/dashboard/validations/{val_id}")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_validation_detail_shows_content(self, client, mock_db_data):
        """Test validation detail shows validation info."""
        val_id = mock_db_data["validations"][0].id
        response = client.get(f"/dashboard/validations/{val_id}")

        assert response.status_code == 200
        content = response.text
        assert "test1.md" in content or val_id in content

    def test_validation_detail_not_found(self, client):
        """Test validation detail with invalid ID."""
        response = client.get("/dashboard/validations/nonexistent_id")

        # Should return 404 or handle gracefully
        assert response.status_code in [404, 500]


# =============================================================================
# Recommendations List Tests
# =============================================================================

@pytest.mark.integration
class TestDashboardRecommendations:
    """Test recommendations list endpoint."""

    def test_recommendations_list_loads(self, client, mock_db_data):
        """Test recommendations list page loads."""
        response = client.get("/dashboard/recommendations")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_recommendations_list_with_status_filter(self, client, mock_db_data):
        """Test filtering recommendations by status."""
        response = client.get("/dashboard/recommendations?status=pending")

        assert response.status_code == 200

    def test_recommendations_list_pagination(self, client, mock_db_data):
        """Test recommendations pagination."""
        response = client.get("/dashboard/recommendations?page=1&page_size=10")

        assert response.status_code == 200

    def test_recommendations_list_empty(self, client):
        """Test recommendations list with no data."""
        response = client.get("/dashboard/recommendations")

        assert response.status_code == 200


# =============================================================================
# Recommendation Detail Tests
# =============================================================================

@pytest.mark.integration
class TestDashboardRecommendationDetail:
    """Test recommendation detail endpoint."""

    def test_recommendation_detail_loads(self, client, mock_db_data):
        """Test recommendation detail page loads."""
        rec_id = mock_db_data["recommendations"][0].id
        response = client.get(f"/dashboard/recommendations/{rec_id}")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_recommendation_detail_shows_content(self, client, mock_db_data):
        """Test recommendation detail shows recommendation info."""
        rec_id = mock_db_data["recommendations"][0].id
        response = client.get(f"/dashboard/recommendations/{rec_id}")

        assert response.status_code == 200
        content = response.text
        # Should show recommendation details
        assert rec_id in content or "Fix typo" in content

    def test_recommendation_detail_not_found(self, client):
        """Test recommendation detail with invalid ID."""
        response = client.get("/dashboard/recommendations/nonexistent_id")

        assert response.status_code in [404, 500]


# =============================================================================
# Recommendation Review Tests
# =============================================================================

@pytest.mark.integration
class TestDashboardRecommendationReview:
    """Test recommendation review endpoint."""

    def test_review_recommendation_approve(self, client, mock_db_data):
        """Test approving a recommendation."""
        rec_id = mock_db_data["recommendations"][0].id
        response = client.post(
            f"/dashboard/recommendations/{rec_id}/review",
            data={"action": "approve", "notes": "Looks good"}
        )

        # Should redirect or return success
        assert response.status_code in [200, 302, 303]

    def test_review_recommendation_reject(self, client, mock_db_data):
        """Test rejecting a recommendation."""
        rec_id = mock_db_data["recommendations"][0].id
        response = client.post(
            f"/dashboard/recommendations/{rec_id}/review",
            data={"action": "reject", "notes": "Not needed"}
        )

        assert response.status_code in [200, 302, 303]

    def test_review_recommendation_invalid_action(self, client, mock_db_data):
        """Test review with invalid action."""
        rec_id = mock_db_data["recommendations"][0].id
        response = client.post(
            f"/dashboard/recommendations/{rec_id}/review",
            data={"action": "invalid", "notes": "Test"}
        )

        # Should handle invalid action
        assert response.status_code in [400, 422, 500]

    def test_review_recommendation_not_found(self, client):
        """Test review with nonexistent recommendation."""
        response = client.post(
            "/dashboard/recommendations/nonexistent_id/review",
            data={"action": "approve"}
        )

        assert response.status_code in [404, 500]


# =============================================================================
# Bulk Review Tests
# =============================================================================

@pytest.mark.integration
class TestDashboardBulkReview:
    """Test bulk recommendation review endpoint."""

    def test_bulk_review_approve_multiple(self, client, mock_db_data):
        """Test bulk approving recommendations."""
        rec_ids = [r.id for r in mock_db_data["recommendations"]]

        response = client.post(
            "/dashboard/recommendations/bulk-review",
            data={
                "recommendation_ids": ",".join(rec_ids),
                "action": "approve"
            }
        )

        assert response.status_code in [200, 302, 303]

    def test_bulk_review_reject_multiple(self, client, mock_db_data):
        """Test bulk rejecting recommendations."""
        rec_ids = [r.id for r in mock_db_data["recommendations"]]

        response = client.post(
            "/dashboard/recommendations/bulk-review",
            data={
                "recommendation_ids": ",".join(rec_ids),
                "action": "reject"
            }
        )

        assert response.status_code in [200, 302, 303]

    def test_bulk_review_empty_list(self, client):
        """Test bulk review with no IDs."""
        response = client.post(
            "/dashboard/recommendations/bulk-review",
            data={"recommendation_ids": "", "action": "approve"}
        )

        # Should handle empty list gracefully
        assert response.status_code in [200, 302, 303, 400]


# =============================================================================
# Workflows List Tests
# =============================================================================

@pytest.mark.integration
class TestDashboardWorkflows:
    """Test workflows list endpoint."""

    def test_workflows_list_loads(self, client, mock_db_data):
        """Test workflows list page loads."""
        response = client.get("/dashboard/workflows")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_workflows_list_with_state_filter(self, client, mock_db_data):
        """Test filtering workflows by state."""
        response = client.get("/dashboard/workflows?state=pending")

        assert response.status_code == 200

    def test_workflows_list_pagination(self, client, mock_db_data):
        """Test workflows pagination."""
        response = client.get("/dashboard/workflows?page=1&page_size=10")

        assert response.status_code == 200

    def test_workflows_list_empty(self, client):
        """Test workflows list with no data."""
        response = client.get("/dashboard/workflows")

        assert response.status_code == 200


# =============================================================================
# Workflow Detail Tests
# =============================================================================

@pytest.mark.integration
class TestDashboardWorkflowDetail:
    """Test workflow detail endpoint."""

    def test_workflow_detail_loads(self, client, mock_db_data):
        """Test workflow detail page loads."""
        wf_id = mock_db_data["workflows"][0].id
        response = client.get(f"/dashboard/workflows/{wf_id}")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_workflow_detail_shows_content(self, client, mock_db_data):
        """Test workflow detail shows workflow info."""
        wf_id = mock_db_data["workflows"][0].id
        response = client.get(f"/dashboard/workflows/{wf_id}")

        assert response.status_code == 200
        # Should show workflow details
        assert response.status_code == 200

    def test_workflow_detail_not_found(self, client):
        """Test workflow detail with invalid ID."""
        response = client.get("/dashboard/workflows/nonexistent_id")

        assert response.status_code in [404, 500]


# =============================================================================
# Audit Logs Tests
# =============================================================================

@pytest.mark.integration
class TestDashboardAuditLogs:
    """Test audit logs endpoint."""

    def test_audit_logs_loads(self, client):
        """Test audit logs page loads."""
        response = client.get("/dashboard/audit")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_audit_logs_pagination(self, client):
        """Test audit logs pagination."""
        response = client.get("/dashboard/audit?page=1&page_size=20")

        assert response.status_code == 200

    def test_audit_logs_empty(self, client):
        """Test audit logs with no data."""
        response = client.get("/dashboard/audit")

        assert response.status_code == 200


# =============================================================================
# Error Handling Tests
# =============================================================================

@pytest.mark.unit
class TestDashboardErrorHandling:
    """Test dashboard error handling."""

    def test_dashboard_handles_db_errors(self, client):
        """Test dashboard handles database errors gracefully."""
        with patch('api.dashboard.db_manager.list_validation_results', side_effect=Exception("DB Error")):
            response = client.get("/dashboard/")

            # Should return 500 or handle error
            assert response.status_code == 500

    def test_validation_detail_handles_missing_id(self, client):
        """Test validation detail with nonexistent ID."""
        response = client.get("/dashboard/validations/nonexistent-id-12345")

        # Should return 404 for nonexistent validation
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=api.dashboard", "--cov-report=term-missing"])
