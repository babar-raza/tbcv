# tests/api/test_export_endpoints.py
"""
Unit tests for api/export_endpoints.py - Export endpoints.
Target coverage: 100%
"""
import pytest

import json
import csv
import io
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch, ANY
from fastapi.testclient import TestClient
from fastapi import FastAPI

from api.export_endpoints import router, generate_diff_report


@pytest.fixture
def app():
    """Create test FastAPI app with export router."""
    test_app = FastAPI()
    test_app.include_router(router)
    return test_app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_validation():
    """Mock validation result."""
    mock = MagicMock()
    mock.id = "val_001"
    mock.file_path = "/path/to/file.md"
    mock.family = "words"
    mock.status = MagicMock(value="completed")
    mock.severity = "medium"
    mock.owner_score = 85
    mock.risk_level = "low"
    mock.created_at = datetime(2025, 1, 1, 12, 0, 0)
    mock.updated_at = datetime(2025, 1, 1, 13, 0, 0)
    mock.summary = "Validation completed successfully"
    mock.to_dict.return_value = {
        "id": "val_001",
        "file_path": "/path/to/file.md",
        "family": "words",
        "status": "completed",
        "severity": "medium"
    }
    return mock


@pytest.fixture
def mock_recommendation():
    """Mock recommendation."""
    mock = MagicMock()
    mock.id = "rec_001"
    mock.title = "Improve documentation"
    mock.type = "enhancement"
    mock.status = MagicMock(value="pending")
    mock.priority = "high"
    mock.confidence = 0.9
    mock.description = "Add more examples"
    mock.diff = "some diff content"
    mock.original_content = "original"
    mock.proposed_content = "proposed"
    mock.to_dict.return_value = {
        "id": "rec_001",
        "title": "Improve documentation",
        "type": "enhancement"
    }
    return mock


@pytest.fixture
def mock_audit_log():
    """Mock audit log."""
    mock = MagicMock()
    mock.action = "validation_created"
    mock.actor = "user@example.com"
    mock.actor_type = "user"
    mock.created_at = datetime(2025, 1, 1, 12, 0, 0)
    mock.notes = "Manual validation"
    mock.to_dict.return_value = {
        "action": "validation_created",
        "actor": "user@example.com"
    }
    return mock


@pytest.fixture
def mock_workflow():
    """Mock workflow."""
    mock = MagicMock()
    mock.id = "wf_001"
    mock.state = "running"
    mock.to_dict.return_value = {
        "id": "wf_001",
        "state": "running"
    }
    return mock


@pytest.mark.unit
class TestExportValidationsJson:
    """Test /api/export/validations.json endpoint."""

    def test_export_validations_json_success(self, client, mock_validation):
        """Test successful JSON export of validations."""
        with patch('api.export_endpoints.db_manager') as mock_db:
            mock_db.list_validation_results.return_value = [mock_validation]

            response = client.get("/api/export/validations.json")

            assert response.status_code == 200
            assert response.headers["content-type"] == "application/json"
            assert "attachment" in response.headers.get("content-disposition", "")

            data = json.loads(response.text)
            assert "export_timestamp" in data
            assert "filters" in data
            assert data["total_records"] == 1
            assert "validations" in data
            assert len(data["validations"]) == 1

    def test_export_validations_json_with_filters(self, client, mock_validation):
        """Test JSON export with status and severity filters."""
        with patch('api.export_endpoints.db_manager') as mock_db:
            mock_db.list_validation_results.return_value = [mock_validation]

            response = client.get(
                "/api/export/validations.json",
                params={"status": "completed", "severity": "high", "limit": 500}
            )

            assert response.status_code == 200
            data = json.loads(response.text)
            assert data["filters"]["status"] == "completed"
            assert data["filters"]["severity"] == "high"
            assert data["filters"]["limit"] == 500

            mock_db.list_validation_results.assert_called_once_with(
                status="completed",
                severity="high",
                limit=500
            )

    def test_export_validations_json_empty_results(self, client):
        """Test JSON export with no results."""
        with patch('api.export_endpoints.db_manager') as mock_db:
            mock_db.list_validation_results.return_value = []

            response = client.get("/api/export/validations.json")

            assert response.status_code == 200
            data = json.loads(response.text)
            assert data["total_records"] == 0
            assert data["validations"] == []

    def test_export_validations_json_error(self, client):
        """Test JSON export with database error."""
        with patch('api.export_endpoints.db_manager') as mock_db:
            mock_db.list_validation_results.side_effect = Exception("DB error")

            response = client.get("/api/export/validations.json")

            assert response.status_code == 500
            assert "Export failed" in response.json()["detail"]


@pytest.mark.unit
class TestExportValidationsCsv:
    """Test /api/export/validations.csv endpoint."""

    def test_export_validations_csv_success(self, client, mock_validation):
        """Test successful CSV export of validations."""
        with patch('api.export_endpoints.db_manager') as mock_db:
            mock_db.list_validation_results.return_value = [mock_validation]

            response = client.get("/api/export/validations.csv")

            assert response.status_code == 200
            assert response.headers["content-type"] == "text/csv; charset=utf-8"
            assert "attachment" in response.headers.get("content-disposition", "")

            # Parse CSV
            csv_content = io.StringIO(response.text)
            reader = csv.reader(csv_content)
            rows = list(reader)

            assert len(rows) >= 2  # Header + at least 1 data row
            assert rows[0][0] == "ID"
            assert rows[0][1] == "File Path"
            assert rows[1][0] == "val_001"

    def test_export_validations_csv_with_filters(self, client, mock_validation):
        """Test CSV export with filters."""
        with patch('api.export_endpoints.db_manager') as mock_db:
            mock_db.list_validation_results.return_value = [mock_validation]

            response = client.get(
                "/api/export/validations.csv",
                params={"status": "pending", "limit": 100}
            )

            assert response.status_code == 200
            mock_db.list_validation_results.assert_called_once_with(
                status="pending",
                severity=None,
                limit=100
            )

    def test_export_validations_csv_empty_results(self, client):
        """Test CSV export with no results."""
        with patch('api.export_endpoints.db_manager') as mock_db:
            mock_db.list_validation_results.return_value = []

            response = client.get("/api/export/validations.csv")

            assert response.status_code == 200
            csv_content = io.StringIO(response.text)
            reader = csv.reader(csv_content)
            rows = list(reader)
            assert len(rows) == 1  # Just header

    def test_export_validations_csv_error(self, client):
        """Test CSV export with error."""
        with patch('api.export_endpoints.db_manager') as mock_db:
            mock_db.list_validation_results.side_effect = Exception("DB error")

            response = client.get("/api/export/validations.csv")

            assert response.status_code == 500


@pytest.mark.unit
class TestExportRecommendationsJson:
    """Test /api/export/recommendations.json endpoint."""

    def test_export_recommendations_json_success(self, client, mock_recommendation):
        """Test successful JSON export of recommendations."""
        with patch('api.export_endpoints.db_manager') as mock_db:
            mock_db.list_recommendations.return_value = [mock_recommendation]

            response = client.get("/api/export/recommendations.json")

            assert response.status_code == 200
            data = json.loads(response.text)
            assert data["total_records"] == 1
            assert "recommendations" in data

    def test_export_recommendations_json_with_filters(self, client, mock_recommendation):
        """Test recommendations export with filters."""
        with patch('api.export_endpoints.db_manager') as mock_db:
            mock_db.list_recommendations.return_value = [mock_recommendation]

            response = client.get(
                "/api/export/recommendations.json",
                params={"status": "approved", "type": "critical", "limit": 200}
            )

            assert response.status_code == 200
            data = json.loads(response.text)
            assert data["filters"]["status"] == "approved"
            assert data["filters"]["type"] == "critical"

    def test_export_recommendations_json_error(self, client):
        """Test recommendations export error."""
        with patch('api.export_endpoints.db_manager') as mock_db:
            mock_db.list_recommendations.side_effect = Exception("Error")

            response = client.get("/api/export/recommendations.json")

            assert response.status_code == 500


@pytest.mark.unit
class TestExportAuditLogsJson:
    """Test /api/export/audit-logs.json endpoint."""

    def test_export_audit_logs_json_success(self, client, mock_audit_log):
        """Test successful audit logs export."""
        with patch('api.export_endpoints.db_manager') as mock_db:
            mock_db.list_audit_logs.return_value = [mock_audit_log]

            response = client.get("/api/export/audit-logs.json")

            assert response.status_code == 200
            data = json.loads(response.text)
            assert data["total_records"] == 1
            assert "audit_logs" in data

    def test_export_audit_logs_json_with_action_filter(self, client, mock_audit_log):
        """Test audit logs export with action filter."""
        with patch('api.export_endpoints.db_manager') as mock_db:
            mock_db.list_audit_logs.return_value = [mock_audit_log]

            response = client.get(
                "/api/export/audit-logs.json",
                params={"action": "validation_created", "limit": 500}
            )

            assert response.status_code == 200
            data = json.loads(response.text)
            assert data["filters"]["action"] == "validation_created"

    def test_export_audit_logs_json_error(self, client):
        """Test audit logs export error."""
        with patch('api.export_endpoints.db_manager') as mock_db:
            mock_db.list_audit_logs.side_effect = Exception("Error")

            response = client.get("/api/export/audit-logs.json")

            assert response.status_code == 500


@pytest.mark.unit
class TestExportReportMarkdown:
    """Test /api/export/report.md endpoint."""

    def test_export_markdown_report_all_sections(self, client, mock_validation, mock_recommendation, mock_audit_log):
        """Test markdown report with all sections."""
        with patch('api.export_endpoints.db_manager') as mock_db:
            mock_db.list_validation_results.return_value = [mock_validation]
            mock_db.list_recommendations.return_value = [mock_recommendation]
            mock_db.list_audit_logs.return_value = [mock_audit_log]

            response = client.get(
                "/api/export/report.md",
                params={
                    "include_validations": True,
                    "include_recommendations": True,
                    "include_audit_logs": True
                }
            )

            assert response.status_code == 200
            assert response.headers["content-type"] == "text/markdown; charset=utf-8"

            content = response.text
            assert "# TBCV System Report" in content
            assert "## Validation Summary" in content
            assert "## Recommendations Summary" in content
            assert "## Recent Audit Activity" in content

    def test_export_markdown_report_validations_only(self, client, mock_validation):
        """Test markdown report with only validations."""
        with patch('api.export_endpoints.db_manager') as mock_db:
            mock_db.list_validation_results.return_value = [mock_validation]

            response = client.get(
                "/api/export/report.md",
                params={
                    "include_validations": True,
                    "include_recommendations": False,
                    "include_audit_logs": False
                }
            )

            assert response.status_code == 200
            content = response.text
            assert "## Validation Summary" in content
            assert "## Recommendations Summary" not in content

    def test_export_markdown_report_recommendations_only(self, client, mock_recommendation):
        """Test markdown report with only recommendations."""
        with patch('api.export_endpoints.db_manager') as mock_db:
            mock_db.list_recommendations.return_value = [mock_recommendation]

            response = client.get(
                "/api/export/report.md",
                params={
                    "include_validations": False,
                    "include_recommendations": True,
                    "include_audit_logs": False
                }
            )

            assert response.status_code == 200
            content = response.text
            assert "## Recommendations Summary" in content

    def test_export_markdown_report_empty_data(self, client):
        """Test markdown report with no data."""
        with patch('api.export_endpoints.db_manager') as mock_db:
            mock_db.list_validation_results.return_value = []
            mock_db.list_recommendations.return_value = []
            mock_db.list_audit_logs.return_value = []

            response = client.get("/api/export/report.md")

            assert response.status_code == 200
            content = response.text
            assert "# TBCV System Report" in content


@pytest.mark.unit
class TestExportWorkflowsJson:
    """Test /api/export/workflows.json endpoint."""

    def test_export_workflows_json_success(self, client, mock_workflow):
        """Test successful workflows export."""
        with patch('api.export_endpoints.db_manager') as mock_db:
            mock_db.list_workflows.return_value = [mock_workflow]

            response = client.get("/api/export/workflows.json")

            assert response.status_code == 200
            data = json.loads(response.text)
            assert data["total_records"] == 1
            assert "workflows" in data

    def test_export_workflows_json_with_state_filter(self, client, mock_workflow):
        """Test workflows export with state filter."""
        with patch('api.export_endpoints.db_manager') as mock_db:
            mock_db.list_workflows.return_value = [mock_workflow]

            response = client.get(
                "/api/export/workflows.json",
                params={"state": "completed", "limit": 300}
            )

            assert response.status_code == 200
            data = json.loads(response.text)
            assert data["filters"]["state"] == "completed"

    def test_export_workflows_json_error(self, client):
        """Test workflows export error."""
        with patch('api.export_endpoints.db_manager') as mock_db:
            mock_db.list_workflows.side_effect = Exception("Error")

            response = client.get("/api/export/workflows.json")

            assert response.status_code == 500


@pytest.mark.unit
class TestGenerateDiffReport:
    """Test generate_diff_report helper function."""

    def test_generate_diff_report_success(self, mock_validation, mock_recommendation):
        """Test successful diff report generation."""
        with patch('api.export_endpoints.db_manager') as mock_db:
            mock_db.get_validation_result.return_value = mock_validation
            mock_db.list_recommendations.return_value = [mock_recommendation]

            result = generate_diff_report("val_001")

            assert "validation" in result
            assert "recommendations" in result
            assert "diffs" in result
            assert len(result["diffs"]) == 1
            assert result["diffs"][0]["recommendation_id"] == "rec_001"

    def test_generate_diff_report_no_validation(self):
        """Test diff report when validation not found."""
        with patch('api.export_endpoints.db_manager') as mock_db:
            mock_db.get_validation_result.return_value = None

            result = generate_diff_report("nonexistent")

            assert result == {}

    def test_generate_diff_report_no_recommendations(self, mock_validation):
        """Test diff report with no recommendations."""
        with patch('api.export_endpoints.db_manager') as mock_db:
            mock_db.get_validation_result.return_value = mock_validation
            mock_db.list_recommendations.return_value = []

            result = generate_diff_report("val_001")

            assert result["validation"] is not None
            assert result["recommendations"] == []
            assert result["diffs"] == []

    def test_generate_diff_report_recommendations_without_diff(self, mock_validation):
        """Test diff report with recommendations that have no diff."""
        mock_rec_no_diff = MagicMock()
        mock_rec_no_diff.diff = None
        mock_rec_no_diff.to_dict.return_value = {"id": "rec_002"}

        with patch('api.export_endpoints.db_manager') as mock_db:
            mock_db.get_validation_result.return_value = mock_validation
            mock_db.list_recommendations.return_value = [mock_rec_no_diff]

            result = generate_diff_report("val_001")

            assert len(result["diffs"]) == 0  # No diffs because diff is None


@pytest.mark.unit
class TestExportValidationDiffJson:
    """Test /api/export/validation/{validation_id}/diff.json endpoint."""

    def test_export_validation_diff_json_success(self, client, mock_validation, mock_recommendation):
        """Test successful validation diff export."""
        with patch('api.export_endpoints.db_manager') as mock_db:
            mock_db.get_validation_result.return_value = mock_validation
            mock_db.list_recommendations.return_value = [mock_recommendation]

            response = client.get("/api/export/validation/val_001/diff.json")

            assert response.status_code == 200
            data = json.loads(response.text)
            assert "validation" in data
            assert "recommendations" in data
            assert "diffs" in data

    def test_export_validation_diff_json_not_found(self, client):
        """Test validation diff export when validation not found."""
        with patch('api.export_endpoints.db_manager') as mock_db:
            mock_db.get_validation_result.return_value = None

            response = client.get("/api/export/validation/nonexistent/diff.json")

            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

    def test_export_validation_diff_json_error(self, client):
        """Test validation diff export with error."""
        with patch('api.export_endpoints.db_manager') as mock_db:
            mock_db.get_validation_result.side_effect = Exception("Error")

            response = client.get("/api/export/validation/val_001/diff.json")

            assert response.status_code == 500


@pytest.mark.integration
class TestExportEndpointsIntegration:
    """Integration tests for export endpoints."""

    def test_multiple_export_formats(self, client, mock_validation):
        """Test exporting same data in different formats."""
        with patch('api.export_endpoints.db_manager') as mock_db:
            mock_db.list_validation_results.return_value = [mock_validation]

            # Export as JSON
            json_response = client.get("/api/export/validations.json")
            assert json_response.status_code == 200
            json_data = json.loads(json_response.text)

            # Export as CSV
            csv_response = client.get("/api/export/validations.csv")
            assert csv_response.status_code == 200

            # Both should have same record count
            csv_rows = list(csv.reader(io.StringIO(csv_response.text)))
            assert json_data["total_records"] == len(csv_rows) - 1  # Exclude header

    def test_full_report_workflow(self, client, mock_validation, mock_recommendation):
        """Test complete report generation workflow."""
        with patch('api.export_endpoints.db_manager') as mock_db:
            mock_db.list_validation_results.return_value = [mock_validation] * 3
            mock_db.list_recommendations.return_value = [mock_recommendation] * 5

            response = client.get(
                "/api/export/report.md",
                params={"include_validations": True, "include_recommendations": True}
            )

            assert response.status_code == 200
            content = response.text

            # Verify structure
            assert "# TBCV System Report" in content
            assert "Total Validations:** 3" in content
            assert "Total Recommendations:** 5" in content
