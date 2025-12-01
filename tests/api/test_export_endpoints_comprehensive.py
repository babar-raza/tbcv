"""
Comprehensive tests for export endpoints.

Tests:
- /api/export/validation/{validation_id} - Export validation in multiple formats
- /api/export/recommendations - Export recommendations in multiple formats
- /api/export/workflow/{workflow_id} - Export workflow data

Formats tested: JSON, YAML, CSV, TEXT
"""
import pytest
import json
import yaml as pyyaml
import sys
from pathlib import Path
from io import BytesIO

# Add project root to path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def api_client():
    """Provide FastAPI TestClient."""
    from fastapi.testclient import TestClient
    from api.server import app
    return TestClient(app)


@pytest.fixture
def db_manager():
    """Provide database manager."""
    from core.database import db_manager
    db_manager.init_database()
    yield db_manager


@pytest.fixture
def sample_validation(db_manager):
    """Create a sample validation for testing exports."""
    validation_data = {
        "file_path": "test_export.md",
        "rules_applied": ["yaml", "markdown", "code"],
        "validation_results": {
            "content_validation": {
                "confidence": 0.85,
                "issues": [
                    {
                        "level": "error",
                        "category": "yaml",
                        "message": "Missing required field 'title'",
                        "line": 1,
                        "suggestion": "Add title to frontmatter"
                    },
                    {
                        "level": "warning",
                        "category": "markdown",
                        "message": "Heading hierarchy violated",
                        "line": 15,
                        "suggestion": "Fix heading levels"
                    }
                ]
            },
            "fuzzy_detection": {
                "plugins_detected": ["document", "pdf-save"],
                "confidence": 0.92
            }
        },
        "validation_types": ["yaml", "markdown", "code"],
        "status": "fail",
        "severity": "high",
        "notes": "Test validation for export"
    }

    validation_obj = db_manager.create_validation_result(**validation_data)
    return validation_obj.id


@pytest.fixture
def sample_recommendations(db_manager, sample_validation):
    """Create sample recommendations for testing exports."""
    recommendations = [
        {
            "validation_id": sample_validation,
            "type": "yaml",
            "title": "Add missing title field",
            "description": "Frontmatter is missing required title field",
            "severity": "high",
            "status": "proposed",
            "confidence": 0.95,
            "instruction": "Add 'title: Document Title' to frontmatter",
            "rationale": "Title is required for SEO and indexing"
        },
        {
            "validation_id": sample_validation,
            "type": "markdown",
            "title": "Fix heading hierarchy",
            "description": "Heading levels skip from h1 to h3",
            "severity": "medium",
            "status": "approved",
            "confidence": 0.90,
            "instruction": "Change h3 to h2 or add intermediate h2",
            "rationale": "Proper heading hierarchy improves accessibility"
        },
        {
            "validation_id": sample_validation,
            "type": "link",
            "title": "Fix broken link",
            "description": "Link returns 404",
            "severity": "high",
            "status": "rejected",
            "confidence": 1.0,
            "instruction": "Update or remove broken link",
            "rationale": "Broken links harm SEO"
        }
    ]

    recommendation_ids = []
    for rec in recommendations:
        rec_obj = db_manager.create_recommendation(**rec)
        recommendation_ids.append(rec_obj.id)

    return recommendation_ids


@pytest.fixture
def sample_workflow(db_manager):
    """Create a sample workflow for testing exports."""
    # Create workflow with correct parameter names
    workflow = db_manager.create_workflow(
        workflow_type="validate_directory",
        input_params={
            "directory_path": "./content",
            "file_pattern": "*.md",
            "max_workers": 4
        },
        metadata={
            "files_total": 10,
            "files_validated": 10,
            "files_failed": 0,
            "started_at": "2025-11-22T10:00:00",
            "completed_at": "2025-11-22T10:05:30"
        }
    )

    # Update to completed state with progress
    db_manager.update_workflow(
        workflow_id=workflow.id,
        state="completed",
        total_steps=10,
        current_step=10,
        progress_percent=100
    )

    return workflow.id


# =============================================================================
# Test Export Validation Endpoint
# =============================================================================

def test_export_validation_json(api_client, sample_validation):
    """Test exporting validation in JSON format."""
    response = api_client.get(
        f"/api/export/validation/{sample_validation}",
        params={"format": "json"}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"

    # Parse JSON
    data = response.json()
    assert "validation_id" in data or "file_path" in data
    assert "validation_results" in data


def test_export_validation_yaml(api_client, sample_validation):
    """Test exporting validation in YAML format."""
    response = api_client.get(
        f"/api/export/validation/{sample_validation}",
        params={"format": "yaml"}
    )

    assert response.status_code == 200
    assert "application/x-yaml" in response.headers["content-type"] or \
           "text/yaml" in response.headers["content-type"]

    # Parse YAML
    data = pyyaml.safe_load(response.content)
    assert data is not None


def test_export_validation_csv(api_client, sample_validation):
    """Test exporting validation in CSV format."""
    response = api_client.get(
        f"/api/export/validation/{sample_validation}",
        params={"format": "csv"}
    )

    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]

    # Check CSV content
    csv_content = response.text
    assert len(csv_content) > 0
    assert "," in csv_content  # CSV has commas


def test_export_validation_text(api_client, sample_validation):
    """Test exporting validation in TEXT format."""
    response = api_client.get(
        f"/api/export/validation/{sample_validation}",
        params={"format": "text"}
    )

    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]

    # Check text content
    text_content = response.text
    assert len(text_content) > 0


def test_export_validation_default_format(api_client, sample_validation):
    """Test export validation defaults to JSON."""
    response = api_client.get(f"/api/export/validation/{sample_validation}")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"


def test_export_validation_not_found(api_client):
    """Test exporting non-existent validation returns 404."""
    response = api_client.get("/api/export/validation/nonexistent-id")

    assert response.status_code == 404


def test_export_validation_invalid_format(api_client, sample_validation):
    """Test invalid format returns 400."""
    response = api_client.get(
        f"/api/export/validation/{sample_validation}",
        params={"format": "xml"}  # Unsupported format
    )

    assert response.status_code == 400


# =============================================================================
# Test Export Recommendations Endpoint
# =============================================================================

def test_export_recommendations_json(api_client, sample_recommendations):
    """Test exporting recommendations in JSON format."""
    response = api_client.get(
        "/api/export/recommendations",
        params={"format": "json"}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"

    # Parse JSON
    data = response.json()
    assert isinstance(data, (list, dict))

    if isinstance(data, list):
        assert len(data) > 0
    elif isinstance(data, dict):
        assert "recommendations" in data


def test_export_recommendations_yaml(api_client, sample_recommendations):
    """Test exporting recommendations in YAML format."""
    response = api_client.get(
        "/api/export/recommendations",
        params={"format": "yaml"}
    )

    assert response.status_code == 200
    assert "application/x-yaml" in response.headers["content-type"] or \
           "text/yaml" in response.headers["content-type"]

    # Parse YAML
    data = pyyaml.safe_load(response.content)
    assert data is not None


def test_export_recommendations_csv(api_client, sample_recommendations):
    """Test exporting recommendations in CSV format."""
    response = api_client.get(
        "/api/export/recommendations",
        params={"format": "csv"}
    )

    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]

    # Check CSV has headers
    csv_content = response.text
    lines = csv_content.split('\n')
    assert len(lines) > 1  # Header + data


def test_export_recommendations_filter_by_status(api_client, sample_recommendations):
    """Test exporting recommendations filtered by status."""
    response = api_client.get(
        "/api/export/recommendations",
        params={"status": "approved", "format": "json"}
    )

    assert response.status_code == 200
    data = response.json()

    # Check all returned recommendations are approved
    recommendations = data if isinstance(data, list) else data.get("recommendations", [])
    for rec in recommendations:
        assert rec.get("status") == "approved"


def test_export_recommendations_filter_by_validation(api_client, sample_validation, sample_recommendations):
    """Test exporting recommendations filtered by validation_id."""
    response = api_client.get(
        "/api/export/recommendations",
        params={"validation_id": sample_validation, "format": "json"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0 or "recommendations" in data


def test_export_recommendations_empty(api_client):
    """Test exporting when no recommendations match filters."""
    # Use a non-existent validation_id to get empty results
    response = api_client.get(
        "/api/export/recommendations",
        params={"validation_id": "nonexistent-validation-id", "format": "json"}
    )

    assert response.status_code == 200
    data = response.json()

    # Should return empty list or empty recommendations
    if isinstance(data, list):
        assert len(data) == 0
    elif isinstance(data, dict):
        assert len(data.get("recommendations", [])) == 0


# =============================================================================
# Test Export Workflow Endpoint
# =============================================================================

def test_export_workflow_json(api_client, sample_workflow):
    """Test exporting workflow in JSON format."""
    response = api_client.get(
        f"/api/export/workflow/{sample_workflow}",
        params={"format": "json"}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"

    # Parse JSON
    data = response.json()
    assert "workflow_id" in data or "type" in data
    assert "state" in data or "status" in data


def test_export_workflow_yaml(api_client, sample_workflow):
    """Test exporting workflow in YAML format."""
    response = api_client.get(
        f"/api/export/workflow/{sample_workflow}",
        params={"format": "yaml"}
    )

    assert response.status_code == 200
    assert "application/x-yaml" in response.headers["content-type"] or \
           "text/yaml" in response.headers["content-type"]

    # Parse YAML
    data = pyyaml.safe_load(response.content)
    assert data is not None


def test_export_workflow_not_found(api_client):
    """Test exporting non-existent workflow returns 404."""
    response = api_client.get("/api/export/workflow/nonexistent-id")

    assert response.status_code == 404


def test_export_workflow_default_format(api_client, sample_workflow):
    """Test workflow export defaults to JSON."""
    response = api_client.get(f"/api/export/workflow/{sample_workflow}")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"


# =============================================================================
# Content Validation Tests
# =============================================================================

def test_export_validation_contains_all_data(api_client, sample_validation):
    """Test exported validation contains all expected data."""
    response = api_client.get(
        f"/api/export/validation/{sample_validation}",
        params={"format": "json"}
    )

    data = response.json()

    # Check for essential fields
    assert "file_path" in data
    assert "validation_results" in data
    assert "status" in data

    # Check validation results structure
    validation_results = data["validation_results"]
    assert "content_validation" in validation_results
    assert "fuzzy_detection" in validation_results


def test_export_recommendations_contains_all_fields(api_client, sample_recommendations):
    """Test exported recommendations contain all fields."""
    response = api_client.get(
        "/api/export/recommendations",
        params={"format": "json"}
    )

    data = response.json()
    recommendations = data if isinstance(data, list) else data.get("recommendations", [])

    assert len(recommendations) > 0

    # Check first recommendation has required fields
    rec = recommendations[0]
    required_fields = ["type", "title", "status", "confidence"]

    for field in required_fields:
        assert field in rec


def test_export_workflow_contains_metadata(api_client, sample_workflow):
    """Test exported workflow contains metadata."""
    response = api_client.get(
        f"/api/export/workflow/{sample_workflow}",
        params={"format": "json"}
    )

    data = response.json()

    # Check for workflow metadata
    assert "type" in data
    assert "state" in data
    assert "metadata" in data or "input_params" in data


# =============================================================================
# Format Conversion Tests
# =============================================================================

def test_json_to_yaml_conversion(api_client, sample_validation):
    """Test JSON and YAML exports contain same data."""
    # Get JSON export
    json_response = api_client.get(
        f"/api/export/validation/{sample_validation}",
        params={"format": "json"}
    )
    json_data = json_response.json()

    # Get YAML export
    yaml_response = api_client.get(
        f"/api/export/validation/{sample_validation}",
        params={"format": "yaml"}
    )
    yaml_data = pyyaml.safe_load(yaml_response.content)

    # Compare key fields
    assert json_data.get("file_path") == yaml_data.get("file_path")
    assert json_data.get("status") == yaml_data.get("status")


def test_csv_export_format(api_client, sample_recommendations):
    """Test CSV export has proper format."""
    response = api_client.get(
        "/api/export/recommendations",
        params={"format": "csv"}
    )

    csv_content = response.text
    lines = csv_content.split('\n')

    # Should have header line
    assert len(lines) > 0

    # Header should have expected columns based on actual API output
    header = lines[0].lower()
    # Actual columns are: ID,Status,Severity,Confidence,Instruction,Rationale,Created
    expected_columns = ["id", "status", "confidence"]

    for col in expected_columns:
        assert col in header, f"Expected column '{col}' not in header: {header}"


# =============================================================================
# Edge Cases
# =============================================================================

def test_export_large_validation(api_client, db_manager):
    """Test exporting validation with large amount of data."""
    # Create validation with many issues
    large_issues = [
        {
            "level": "warning",
            "category": "test",
            "message": f"Issue {i}",
            "line": i
        }
        for i in range(100)
    ]

    validation_data = {
        "file_path": "large_test.md",
        "rules_applied": ["test"],
        "validation_results": {
            "content_validation": {
                "issues": large_issues,
                "confidence": 0.5
            }
        },
        "status": "fail",
        "severity": "medium",
        "notes": "Large validation test"
    }

    validation_obj = db_manager.create_validation_result(**validation_data)
    validation_id = validation_obj.id

    response = api_client.get(
        f"/api/export/validation/{validation_id}",
        params={"format": "json"}
    )

    assert response.status_code == 200
    data = response.json()

    # Should contain all issues
    issues = data["validation_results"]["content_validation"]["issues"]
    assert len(issues) == 100


def test_export_with_special_characters(api_client, db_manager):
    """Test export handles special characters correctly."""
    validation_data = {
        "file_path": "test_特殊文字.md",
        "rules_applied": ["test"],
        "validation_results": {
            "content_validation": {
                "issues": [
                    {
                        "message": "Test with émojis 🎉 and spëcial chàrs"
                    }
                ],
                "confidence": 0.9
            }
        },
        "status": "pass",
        "severity": "low",
        "notes": "Special character test"
    }

    validation_obj = db_manager.create_validation_result(**validation_data)
    validation_id = validation_obj.id

    # Test JSON export
    response = api_client.get(
        f"/api/export/validation/{validation_id}",
        params={"format": "json"}
    )

    assert response.status_code == 200

    # Should handle UTF-8
    data = response.json()
    assert "特殊文字" in data["file_path"]


def test_concurrent_exports(api_client, sample_validation):
    """Test multiple concurrent export requests."""
    import concurrent.futures

    def export_validation():
        return api_client.get(
            f"/api/export/validation/{sample_validation}",
            params={"format": "json"}
        )

    # Make 10 concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(export_validation) for _ in range(10)]
        results = [f.result() for f in futures]

    # All should succeed
    for response in results:
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
