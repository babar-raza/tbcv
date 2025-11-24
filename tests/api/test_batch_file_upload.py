# file: tests/api/test_batch_file_upload.py
"""
Tests for batch file upload functionality in validation and workflow endpoints.
Tests both server-side file paths and client-side file uploads.
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch

# Set environment before imports
os.environ.setdefault("TBCV_ENV", "test")
os.environ.setdefault("OLLAMA_ENABLED", "false")

from api.server import app
from core.database import db_manager


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_markdown_content():
    """Sample markdown content for testing."""
    return """# Test Document

This is a test document for validation.

## Features
- Feature 1
- Feature 2

## Code Example
```python
print("Hello World")
```
"""


@pytest.fixture
def sample_file_contents():
    """Sample file contents for batch upload."""
    return [
        {
            "file_path": "test1.md",
            "content": "# Test 1\n\nThis is test file 1."
        },
        {
            "file_path": "test2.md",
            "content": "# Test 2\n\nThis is test file 2."
        },
        {
            "file_path": "test3.md",
            "content": "# Test 3\n\nThis is test file 3."
        }
    ]


# =============================================================================
# Batch Validation Upload Tests
# =============================================================================

@pytest.mark.integration
class TestBatchValidationUpload:
    """Test batch validation with file uploads."""

    @patch("api.server.agent_registry.get_agent")
    def test_batch_validation_upload_mode(self, mock_get_agent, client, sample_file_contents):
        """Test batch validation with client-side file upload."""
        # Mock validator agent
        mock_validator = AsyncMock()
        mock_validator.process_request.return_value = {
            "id": "test-validation-id",
            "status": "pass",
            "severity": "low"
        }
        mock_get_agent.return_value = mock_validator

        payload = {
            "files": ["test1.md", "test2.md", "test3.md"],
            "file_contents": sample_file_contents,
            "family": "words",
            "validation_types": ["yaml", "markdown"],
            "max_workers": 2,
            "upload_mode": True
        }

        response = client.post("/api/validate/batch", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "workflow_id" in data
        assert "job_id" in data
        assert data["status"] == "started"
        assert data["files_total"] == 3

    def test_batch_validation_server_mode(self, client):
        """Test batch validation with server-side file paths."""
        payload = {
            "files": ["/path/to/file1.md", "/path/to/file2.md"],
            "family": "words",
            "validation_types": ["yaml", "markdown"],
            "max_workers": 2,
            "upload_mode": False
        }

        response = client.post("/api/validate/batch", json=payload)

        # Should succeed (workflow creation) even if files don't exist
        # Files will fail during processing, but endpoint should accept request
        assert response.status_code == 200
        data = response.json()
        assert "workflow_id" in data
        assert "job_id" in data

    def test_batch_validation_missing_file_contents(self, client):
        """Test batch validation upload mode without file_contents fails gracefully."""
        payload = {
            "files": ["test1.md", "test2.md"],
            "family": "words",
            "validation_types": ["yaml"],
            "max_workers": 2,
            "upload_mode": True
            # Missing file_contents
        }

        response = client.post("/api/validate/batch", json=payload)

        # Should still create workflow, but will fail during processing
        assert response.status_code == 200
        data = response.json()
        assert "workflow_id" in data

    def test_batch_validation_empty_files_list(self, client):
        """Test batch validation with empty files list."""
        payload = {
            "files": [],
            "family": "words",
            "validation_types": ["yaml"],
            "max_workers": 2,
            "upload_mode": False
        }

        response = client.post("/api/validate/batch", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["files_total"] == 0

    def test_batch_validation_validation_types(self, client, sample_file_contents):
        """Test batch validation with different validation types."""
        payload = {
            "files": ["test1.md"],
            "file_contents": [sample_file_contents[0]],
            "family": "words",
            "validation_types": ["yaml", "markdown", "code", "links", "structure", "Truth"],
            "max_workers": 1,
            "upload_mode": True
        }

        response = client.post("/api/validate/batch", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "workflow_id" in data

    def test_batch_validation_different_families(self, client, sample_file_contents):
        """Test batch validation with different document families."""
        families = ["words", "cells", "slides", "pdf"]

        for family in families:
            payload = {
                "files": ["test1.md"],
                "file_contents": [sample_file_contents[0]],
                "family": family,
                "validation_types": ["yaml"],
                "max_workers": 1,
                "upload_mode": True
            }

            response = client.post("/api/validate/batch", json=payload)

            assert response.status_code == 200, f"Failed for family: {family}"
            data = response.json()
            assert "workflow_id" in data

    def test_batch_validation_max_workers(self, client, sample_file_contents):
        """Test batch validation with different max_workers values."""
        for max_workers in [1, 2, 4, 8, 16]:
            payload = {
                "files": ["test1.md", "test2.md"],
                "file_contents": sample_file_contents[:2],
                "family": "words",
                "validation_types": ["yaml"],
                "max_workers": max_workers,
                "upload_mode": True
            }

            response = client.post("/api/validate/batch", json=payload)

            assert response.status_code == 200
            data = response.json()
            assert "workflow_id" in data


# =============================================================================
# Model Validation Tests
# =============================================================================

@pytest.mark.unit
class TestBatchValidationRequestModel:
    """Test BatchValidationRequest model validation."""

    def test_model_with_upload_mode(self):
        """Test model accepts upload_mode and file_contents."""
        from api.server import BatchValidationRequest, FileContent

        file_contents = [
            FileContent(file_path="test.md", content="# Test")
        ]

        request = BatchValidationRequest(
            files=["test.md"],
            file_contents=file_contents,
            upload_mode=True,
            family="words",
            validation_types=["yaml"],
            max_workers=4
        )

        assert request.upload_mode is True
        assert len(request.file_contents) == 1
        assert request.file_contents[0].file_path == "test.md"

    def test_model_without_upload_mode(self):
        """Test model works without upload_mode (defaults to False)."""
        from api.server import BatchValidationRequest

        request = BatchValidationRequest(
            files=["/path/to/file.md"],
            family="words",
            validation_types=["yaml"],
            max_workers=4
        )

        assert request.upload_mode is False
        assert request.file_contents is None

    def test_file_content_model(self):
        """Test FileContent model."""
        from api.server import FileContent

        fc = FileContent(file_path="test.md", content="# Hello")

        assert fc.file_path == "test.md"
        assert fc.content == "# Hello"


# =============================================================================
# Integration Tests
# =============================================================================

@pytest.mark.integration
class TestBatchUploadIntegration:
    """Integration tests for batch upload workflow."""

    @patch("api.server.agent_registry.get_agent")
    def test_full_batch_upload_workflow(self, mock_get_agent, client, sample_file_contents):
        """Test complete batch upload workflow from submission to completion."""
        # Mock validator and recommendation agents
        mock_validator = AsyncMock()
        mock_validator.process_request.return_value = {
            "id": "validation-id-1",
            "status": "pass",
            "severity": "low"
        }

        mock_recommender = AsyncMock()
        mock_recommender.process_request.return_value = {
            "recommendations": []
        }

        def get_agent_side_effect(name):
            if name == "content_validator":
                return mock_validator
            elif name == "recommendation_agent":
                return mock_recommender
            return None

        mock_get_agent.side_effect = get_agent_side_effect

        # Submit batch validation
        payload = {
            "files": ["test1.md", "test2.md"],
            "file_contents": sample_file_contents[:2],
            "family": "words",
            "validation_types": ["yaml", "markdown"],
            "max_workers": 2,
            "upload_mode": True
        }

        response = client.post("/api/validate/batch", json=payload)

        assert response.status_code == 200
        data = response.json()
        workflow_id = data["workflow_id"]

        # Wait a moment for background task to start
        import time
        time.sleep(0.5)

        # Check workflow status
        workflow_response = client.get(f"/workflows/{workflow_id}")

        assert workflow_response.status_code == 200
        workflow_data = workflow_response.json()
        assert workflow_data["id"] == workflow_id
        assert workflow_data["type"] == "batch_validation"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
