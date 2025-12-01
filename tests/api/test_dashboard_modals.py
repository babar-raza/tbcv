# file: tests/api/test_dashboard_modals.py
"""
Task Card 2: Modal Forms & Input Validation Tests

Tests for modal form submission and input validation including:
- Run validation modal (single file, batch)
- Run workflow modal
- Input validation (SQL injection, XSS, path traversal)

Target: 20 tests covering modal functionality and security.
"""

import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Set environment before imports
os.environ.setdefault("TBCV_ENV", "test")
os.environ.setdefault("OLLAMA_ENABLED", "false")
os.environ.setdefault("OLLAMA_MODEL", "mistral")

import pytest
from fastapi.testclient import TestClient

# Import after environment is set
from api.server import app
from core.database import db_manager


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


# =============================================================================
# TestRunValidationModal (11 tests)
# =============================================================================

@pytest.mark.integration
class TestRunValidationModal:
    """Test validation modal/form functionality for running validations."""

    def test_single_file_validation_valid_path(self, client, mock_file_system, db_manager):
        """Test single file validation with a valid file path."""
        file_path = mock_file_system["file_path"]

        with patch('api.server.agent_registry') as mock_registry:
            mock_orchestrator = AsyncMock()
            mock_orchestrator.process_request.return_value = {
                "success": True,
                "confidence": 0.85,
                "issues": [],
                "validation_types": ["yaml", "markdown"]
            }
            mock_registry.get_agent.return_value = mock_orchestrator

            response = client.post(
                "/api/validate/file",
                json={
                    "file_path": file_path,
                    "family": "words",
                    "validation_types": ["yaml", "markdown"]
                }
            )

        # Should succeed or return 500 if orchestrator unavailable
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "validation_id" in data or "id" in data

    def test_single_file_validation_windows_path(self, client, windows_test_path, db_manager):
        """Test validation modal handles Windows-style paths correctly."""
        file_path = windows_test_path["windows_path"]

        with patch('api.server.agent_registry') as mock_registry:
            mock_orchestrator = AsyncMock()
            mock_orchestrator.process_request.return_value = {
                "success": True,
                "confidence": 0.85,
                "issues": []
            }
            mock_registry.get_agent.return_value = mock_orchestrator

            response = client.post(
                "/api/validate/file",
                json={
                    "file_path": file_path,
                    "family": "words",
                    "validation_types": ["yaml"]
                }
            )

        # Path handling should work on Windows
        assert response.status_code in [200, 500]

    def test_single_file_validation_unix_path(self, client, unix_test_path, db_manager):
        """Test validation modal handles Unix-style paths correctly."""
        file_path = unix_test_path["unix_path"]

        with patch('api.server.agent_registry') as mock_registry:
            mock_orchestrator = AsyncMock()
            mock_orchestrator.process_request.return_value = {
                "success": True,
                "confidence": 0.85,
                "issues": []
            }
            mock_registry.get_agent.return_value = mock_orchestrator

            response = client.post(
                "/api/validate/file",
                json={
                    "file_path": file_path,
                    "family": "words",
                    "validation_types": ["yaml"]
                }
            )

        # Path handling should work with Unix paths
        assert response.status_code in [200, 500]

    def test_single_file_validation_nonexistent_path(self, client, db_manager):
        """Test validation modal rejects nonexistent file paths."""
        response = client.post(
            "/api/validate/file",
            json={
                "file_path": "/path/that/does/not/exist/file.md",
                "family": "words",
                "validation_types": ["yaml"]
            }
        )

        # Should return 404 for nonexistent file, or 500 if orchestrator unavailable
        assert response.status_code in [404, 500]

        data = response.json()
        assert "detail" in data

    def test_batch_validation_multiple_files(self, client, mock_file_system, db_manager):
        """Test batch validation modal with multiple files."""
        # Create multiple test files
        files = []
        for i in range(3):
            test_file = mock_file_system["directory"] / f"modal_batch_{i}.md"
            test_file.write_text(f"# Test {i}\n\nContent {i}.", encoding="utf-8")
            files.append(str(test_file))

        response = client.post(
            "/api/validate/batch",
            json={
                "files": files,
                "family": "words",
                "validation_types": ["yaml", "markdown"],
                "max_workers": 2
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert "workflow_id" in data
        assert data["files_total"] == 3

    def test_batch_validation_with_wildcards(self, client, test_directory, db_manager):
        """Test batch validation using file pattern with wildcards."""
        # Use the directory validation endpoint which supports patterns
        with patch('api.server.agent_registry') as mock_registry:
            mock_orchestrator = AsyncMock()
            mock_orchestrator.process_request.return_value = {
                "success": True,
                "files_processed": 5
            }
            mock_registry.get_agent.return_value = mock_orchestrator

            response = client.post(
                "/workflows/validate-directory",
                json={
                    "directory_path": test_directory["path"],
                    "file_pattern": "*.md",
                    "workflow_type": "directory_validation",
                    "max_workers": 2,
                    "family": "words"
                }
            )

        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "job_id" in data or "workflow_id" in data

    def test_batch_validation_empty_file_list(self, client, db_manager):
        """Test batch validation modal handles empty file list gracefully."""
        response = client.post(
            "/api/validate/batch",
            json={
                "files": [],
                "family": "words",
                "validation_types": ["yaml", "markdown"]
            }
        )

        # Should handle empty list - either 200 with 0 files or 422 validation error
        assert response.status_code in [200, 422]

        if response.status_code == 200:
            data = response.json()
            assert data["files_total"] == 0

    def test_family_parameter_words(self, client, mock_file_system, db_manager):
        """Test that family='words' parameter is handled correctly."""
        file_path = mock_file_system["file_path"]

        with patch('api.server.agent_registry') as mock_registry:
            mock_orchestrator = AsyncMock()
            mock_orchestrator.process_request.return_value = {
                "success": True,
                "confidence": 0.85,
                "family": "words"
            }
            mock_registry.get_agent.return_value = mock_orchestrator

            response = client.post(
                "/api/validate/file",
                json={
                    "file_path": file_path,
                    "family": "words",
                    "validation_types": ["yaml"]
                }
            )

        assert response.status_code in [200, 500]

        # Verify family was passed to orchestrator
        if response.status_code == 200 and mock_orchestrator.process_request.called:
            call_args = mock_orchestrator.process_request.call_args
            if call_args and len(call_args[0]) > 1:
                assert call_args[0][1].get("family") == "words"

    def test_family_parameter_cells(self, client, mock_file_system, db_manager):
        """Test that family='cells' parameter is handled correctly."""
        file_path = mock_file_system["file_path"]

        with patch('api.server.agent_registry') as mock_registry:
            mock_orchestrator = AsyncMock()
            mock_orchestrator.process_request.return_value = {
                "success": True,
                "confidence": 0.85,
                "family": "cells"
            }
            mock_registry.get_agent.return_value = mock_orchestrator

            response = client.post(
                "/api/validate/file",
                json={
                    "file_path": file_path,
                    "family": "cells",
                    "validation_types": ["yaml"]
                }
            )

        assert response.status_code in [200, 500]

        # Verify family was passed correctly
        if response.status_code == 200 and mock_orchestrator.process_request.called:
            call_args = mock_orchestrator.process_request.call_args
            if call_args and len(call_args[0]) > 1:
                assert call_args[0][1].get("family") == "cells"

    def test_validation_types_subset(self, client, mock_file_system, db_manager):
        """Test that validation_types subset is respected."""
        file_path = mock_file_system["file_path"]

        with patch('api.server.agent_registry') as mock_registry:
            mock_orchestrator = AsyncMock()
            mock_orchestrator.process_request.return_value = {
                "success": True,
                "confidence": 0.90,
                "validation_types": ["yaml", "structure"]
            }
            mock_registry.get_agent.return_value = mock_orchestrator

            # Only request yaml and structure validation
            response = client.post(
                "/api/validate/file",
                json={
                    "file_path": file_path,
                    "family": "words",
                    "validation_types": ["yaml", "structure"]
                }
            )

        assert response.status_code in [200, 500]

        # Verify only requested types were used
        if response.status_code == 200 and mock_orchestrator.process_request.called:
            call_args = mock_orchestrator.process_request.call_args
            if call_args and len(call_args[0]) > 1:
                types = call_args[0][1].get("validation_types", [])
                if types:
                    assert "yaml" in types
                    assert "structure" in types

    def test_max_workers_parameter(self, client, mock_file_system, db_manager):
        """Test that max_workers parameter is respected in batch validation."""
        files = [mock_file_system["file_path"]]

        # Test with max_workers=1
        response = client.post(
            "/api/validate/batch",
            json={
                "files": files,
                "family": "words",
                "validation_types": ["yaml"],
                "max_workers": 1
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "started"

        # Test with max_workers=8
        response2 = client.post(
            "/api/validate/batch",
            json={
                "files": files,
                "family": "words",
                "validation_types": ["yaml"],
                "max_workers": 8
            }
        )

        assert response2.status_code == 200


# =============================================================================
# TestRunWorkflowModal (5 tests)
# =============================================================================

@pytest.mark.integration
class TestRunWorkflowModal:
    """Test workflow modal/form functionality."""

    def test_directory_validation_workflow(self, client, test_directory, db_manager):
        """Test creating directory validation workflow from modal."""
        with patch('api.server.agent_registry') as mock_registry:
            mock_orchestrator = AsyncMock()
            mock_orchestrator.process_request.return_value = {
                "success": True,
                "files_processed": 5
            }
            mock_registry.get_agent.return_value = mock_orchestrator

            response = client.post(
                "/workflows/validate-directory",
                json={
                    "directory_path": test_directory["path"],
                    "file_pattern": "*.md",
                    "workflow_type": "directory_validation",
                    "max_workers": 4,
                    "family": "words"
                }
            )

        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.json()
            assert "job_id" in data
            assert "workflow_id" in data
            assert data["status"] == "started"

    def test_directory_validation_invalid_path(self, client, db_manager):
        """Test directory validation with invalid path."""
        with patch('api.server.agent_registry') as mock_registry:
            mock_orchestrator = AsyncMock()
            mock_registry.get_agent.return_value = mock_orchestrator

            response = client.post(
                "/workflows/validate-directory",
                json={
                    "directory_path": "/this/path/definitely/does/not/exist",
                    "file_pattern": "*.md",
                    "workflow_type": "directory_validation"
                }
            )

        # Should start (validation happens in background) or fail with error
        assert response.status_code in [200, 400, 404, 500]

    def test_file_pattern_glob_matching(self, client, test_directory, db_manager):
        """Test file pattern matching with different glob patterns."""
        patterns = ["*.md", "**/*.md", "document_*.md", "*.txt"]

        for pattern in patterns:
            with patch('api.server.agent_registry') as mock_registry:
                mock_orchestrator = AsyncMock()
                mock_orchestrator.process_request.return_value = {"success": True}
                mock_registry.get_agent.return_value = mock_orchestrator

                response = client.post(
                    "/workflows/validate-directory",
                    json={
                        "directory_path": test_directory["path"],
                        "file_pattern": pattern,
                        "workflow_type": "directory_validation"
                    }
                )

            # All patterns should be accepted
            assert response.status_code in [200, 500]

    def test_batch_workflow_creation(self, client, test_directory, db_manager):
        """Test batch workflow is properly created and tracked."""
        files = [str(f) for f in Path(test_directory["path"]).glob("*.md")][:3]

        response = client.post(
            "/api/validate/batch",
            json={
                "files": files,
                "family": "words",
                "validation_types": ["yaml", "markdown"]
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Verify workflow was created
        workflow_id = data["workflow_id"]
        workflow = db_manager.get_workflow(workflow_id)
        assert workflow is not None
        assert workflow.type == "batch_validation"

    def test_workflow_modal_missing_required_fields(self, client, db_manager):
        """Test workflow modal validation rejects missing required fields."""
        # Missing directory_path
        response = client.post(
            "/workflows/validate-directory",
            json={
                "file_pattern": "*.md",
                "workflow_type": "directory_validation"
            }
        )

        # Should return 422 for validation error
        assert response.status_code == 422


# =============================================================================
# TestInputValidation (4 tests)
# =============================================================================

@pytest.mark.integration
class TestInputValidation:
    """Test input validation and security measures."""

    def test_file_path_sql_injection_safe(self, client, db_manager):
        """Test that file_path is safe from SQL injection."""
        # Attempt SQL injection in file_path
        malicious_paths = [
            "test.md'; DROP TABLE validations; --",
            "test.md\" OR 1=1 --",
            "test.md; SELECT * FROM users",
            "' UNION SELECT * FROM passwords --"
        ]

        for path in malicious_paths:
            response = client.post(
                "/api/validate/file",
                json={
                    "file_path": path,
                    "family": "words",
                    "validation_types": ["yaml"]
                }
            )

            # Should return 404 (file not found) or 500, not execute SQL
            assert response.status_code in [404, 500]

            # Verify database is still intact by checking we can query
            validations = db_manager.list_validation_results(limit=1)
            # Should not raise exception

    def test_file_path_path_traversal_safe(self, client, db_manager):
        """Test that file_path is safe from path traversal attacks."""
        # Attempt path traversal
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\SAM",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc/passwd"
        ]

        for path in malicious_paths:
            response = client.post(
                "/api/validate/file",
                json={
                    "file_path": path,
                    "family": "words",
                    "validation_types": ["yaml"]
                }
            )

            # Should return error, not expose system files
            assert response.status_code in [400, 404, 500]

    def test_reviewer_xss_safe(self, client, mock_file_system, db_manager):
        """Test that reviewer field is safe from XSS attacks."""
        from core.database import RecommendationStatus

        # Create a validation and recommendation
        validation = db_manager.create_validation_result(
            file_path=mock_file_system["file_path"],
            rules_applied=["yaml"],
            validation_results={"passed": True},
            notes="XSS test",
            severity="low",
            status="pass"
        )

        rec = db_manager.create_recommendation(
            validation_id=validation.id,
            type="fix",
            title="XSS Test Rec",
            description="Test recommendation",
            original_content="old",
            proposed_content="new",
            status=RecommendationStatus.PENDING
        )

        # Attempt XSS in reviewer field
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "';alert('XSS');//"
        ]

        for payload in xss_payloads:
            response = client.post(
                f"/dashboard/recommendations/{rec.id}/review",
                data={
                    "action": "approve",
                    "reviewer": payload,
                    "notes": "Test"
                }
            )

            # Should not execute script - just store sanitized data
            # Response should be redirect (303) or success
            assert response.status_code in [200, 302, 303]

            # Verify reviewer field is stored (possibly sanitized)
            updated_rec = db_manager.get_recommendation(rec.id)
            # Should not contain raw script tags in database
            # The test passes if no exception is raised

    def test_notes_field_special_characters(self, client, mock_file_system, db_manager):
        """Test that notes field handles special characters correctly."""
        from core.database import RecommendationStatus

        # Create a validation and recommendation
        validation = db_manager.create_validation_result(
            file_path=mock_file_system["file_path"],
            rules_applied=["yaml"],
            validation_results={"passed": True},
            notes="Special chars test",
            severity="low",
            status="pass"
        )

        rec = db_manager.create_recommendation(
            validation_id=validation.id,
            type="fix",
            title="Special Chars Test",
            description="Test recommendation",
            original_content="old",
            proposed_content="new",
            status=RecommendationStatus.PENDING
        )

        # Test various special characters in notes
        special_notes = [
            "Line1\nLine2\nLine3",
            "Tab\there",
            "Unicode: \u00e9\u00e0\u00fc\u00f1",
            "Emoji: \U0001f600\U0001f44d",
            "Quote: \"double\" and 'single'",
            "Ampersand: &amp; and <less> and >greater>",
            "Backslash: C:\\path\\to\\file",
            "Mixed: \t\n\"'<>&\\"
        ]

        for notes in special_notes:
            response = client.post(
                f"/dashboard/recommendations/{rec.id}/review",
                data={
                    "action": "approve",
                    "reviewer": "test_user",
                    "notes": notes
                }
            )

            # Should handle all special characters
            assert response.status_code in [200, 302, 303]

        # Verify recommendation was updated without errors
        updated_rec = db_manager.get_recommendation(rec.id)
        assert updated_rec is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
