# tests/core/test_startup_checks.py
"""
Unit tests for core/startup_checks.py - StartupChecker.
Target coverage: 100% (Currently 23%)
"""
import pytest
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, ANY
from datetime import datetime

from core.startup_checks import (
    StartupCheckResult,
    StartupChecker,
    run_startup_checks
)


@pytest.mark.unit
class TestStartupCheckResult:
    """Test StartupCheckResult dataclass."""

    def test_result_creation_success(self):
        """Test creating a successful check result."""
        result = StartupCheckResult(
            name="Test Check",
            passed=True,
            message="Check passed",
            critical=True
        )

        assert result.name == "Test Check"
        assert result.passed is True
        assert result.message == "Check passed"
        assert result.critical is True
        assert isinstance(result.timestamp, datetime)

    def test_result_creation_failure(self):
        """Test creating a failed check result."""
        result = StartupCheckResult(
            name="Test Check",
            passed=False,
            message="Check failed",
            critical=False
        )

        assert result.passed is False
        assert result.critical is False

    def test_result_to_dict(self):
        """Test converting result to dictionary."""
        result = StartupCheckResult(
            name="Database",
            passed=True,
            message="Connected",
            critical=True
        )

        result_dict = result.to_dict()

        assert result_dict["name"] == "Database"
        assert result_dict["passed"] is True
        assert result_dict["message"] == "Connected"
        assert result_dict["critical"] is True
        assert "timestamp" in result_dict
        assert isinstance(result_dict["timestamp"], str)


@pytest.mark.unit
class TestStartupChecker:
    """Test StartupChecker class."""

    def test_initialization(self):
        """Test StartupChecker initialization."""
        checker = StartupChecker()

        assert checker.results == []
        assert checker.critical_failures == 0

    def test_check_ollama_connectivity_success(self):
        """Test Ollama connectivity check when available."""
        checker = StartupChecker()

        mock_client = MagicMock()
        mock_client.is_available.return_value = True

        with patch('core.ollama.OllamaClient', return_value=mock_client):
            result = checker.check_ollama_connectivity()

            assert result.name == "Ollama Connectivity"
            assert result.passed is True
            assert "reachable" in result.message
            assert result.critical is False

    def test_check_ollama_connectivity_failure(self):
        """Test Ollama connectivity check when not available."""
        checker = StartupChecker()

        mock_client = MagicMock()
        mock_client.is_available.return_value = False

        with patch('core.ollama.OllamaClient', return_value=mock_client):
            result = checker.check_ollama_connectivity()

            assert result.name == "Ollama Connectivity"
            assert result.passed is False
            assert "not responding" in result.message
            assert result.critical is False

    def test_check_ollama_connectivity_exception(self):
        """Test Ollama connectivity check with exception."""
        checker = StartupChecker()

        with patch('core.ollama.OllamaClient', side_effect=Exception("Connection error")):
            result = checker.check_ollama_connectivity()

            assert result.passed is False
            assert "Failed to connect" in result.message
            assert "Connection error" in result.message

    def test_check_ollama_models_success(self):
        """Test Ollama models check when all required models available."""
        checker = StartupChecker()

        mock_client = MagicMock()
        mock_client.list_models.return_value = ["llama2:latest", "mistral:latest", "other:v1"]

        with patch('core.ollama.OllamaClient', return_value=mock_client):
            result = checker.check_ollama_models(required_models=["llama2", "mistral"])

            assert result.name == "Ollama Models"
            assert result.passed is True
            assert "All required models available" in result.message
            assert "llama2" in result.message
            assert "mistral" in result.message

    def test_check_ollama_models_missing(self):
        """Test Ollama models check when models are missing."""
        checker = StartupChecker()

        mock_client = MagicMock()
        mock_client.list_models.return_value = ["llama2:latest"]

        with patch('core.ollama.OllamaClient', return_value=mock_client):
            result = checker.check_ollama_models(required_models=["llama2", "mistral", "gpt"])

            assert result.passed is False
            assert "Missing required models" in result.message
            assert "mistral" in result.message
            assert "gpt" in result.message

    def test_check_ollama_models_default_models(self):
        """Test Ollama models check with default models."""
        checker = StartupChecker()

        mock_client = MagicMock()
        mock_client.list_models.return_value = ["llama2:latest", "mistral:latest"]

        with patch('core.ollama.OllamaClient', return_value=mock_client):
            result = checker.check_ollama_models()  # No required_models specified

            assert result.passed is True

    def test_check_ollama_models_exception(self):
        """Test Ollama models check with exception."""
        checker = StartupChecker()

        with patch('core.ollama.OllamaClient', side_effect=Exception("API error")):
            result = checker.check_ollama_models()

            assert result.passed is False
            assert "Failed to check models" in result.message

    def test_check_database_connectivity_success(self):
        """Test database connectivity check when connected."""
        checker = StartupChecker()

        mock_db = MagicMock()
        mock_db.is_connected.return_value = True

        with patch('core.database.db_manager', mock_db):
            result = checker.check_database_connectivity()

            assert result.name == "Database Connectivity"
            assert result.passed is True
            assert "connected" in result.message
            assert result.critical is True

    def test_check_database_connectivity_failure(self):
        """Test database connectivity check when not connected."""
        checker = StartupChecker()

        mock_db = MagicMock()
        mock_db.is_connected.return_value = False

        with patch('core.database.db_manager', mock_db):
            result = checker.check_database_connectivity()

            assert result.passed is False
            assert "not connected" in result.message
            assert result.critical is True

    def test_check_database_connectivity_exception(self):
        """Test database connectivity check with exception."""
        checker = StartupChecker()

        mock_db = MagicMock()
        mock_db.is_connected.side_effect = Exception("DB error")

        with patch('core.database.db_manager', mock_db):
            result = checker.check_database_connectivity()

            assert result.passed is False
            assert "Failed to connect" in result.message

    def test_check_database_schema_success(self):
        """Test database schema check when schema is valid."""
        checker = StartupChecker()

        mock_db = MagicMock()
        mock_db.has_required_schema.return_value = True

        with patch('core.database.db_manager', mock_db):
            result = checker.check_database_schema()

            assert result.name == "Database Schema"
            assert result.passed is True
            assert "valid and up-to-date" in result.message
            mock_db.init_database.assert_called_once()

    def test_check_database_schema_failure(self):
        """Test database schema check when schema is invalid."""
        checker = StartupChecker()

        mock_db = MagicMock()
        mock_db.has_required_schema.return_value = False

        with patch('core.database.db_manager', mock_db):
            result = checker.check_database_schema()

            assert result.passed is False
            assert "missing or incomplete" in result.message

    def test_check_database_schema_exception(self):
        """Test database schema check with exception."""
        checker = StartupChecker()

        mock_db = MagicMock()
        mock_db.init_database.side_effect = Exception("Schema error")

        with patch('core.database.db_manager', mock_db):
            result = checker.check_database_schema()

            assert result.passed is False
            assert "Failed to verify schema" in result.message

    def test_check_writable_paths_success(self, temp_dir):
        """Test writable paths check when all paths are writable."""
        checker = StartupChecker()

        # Create test directories
        test_paths = [str(temp_dir / "reports"), str(temp_dir / "output")]

        result = checker.check_writable_paths(paths=test_paths)

        assert result.name == "Writable Paths"
        assert result.passed is True
        assert "All required paths are writable" in result.message

    def test_check_writable_paths_create_missing(self, temp_dir):
        """Test writable paths check creates missing directories."""
        checker = StartupChecker()

        test_path = str(temp_dir / "new_dir")
        assert not Path(test_path).exists()

        result = checker.check_writable_paths(paths=[test_path])

        assert result.passed is True
        assert Path(test_path).exists()

    def test_check_writable_paths_cannot_create(self):
        """Test writable paths check when directory cannot be created."""
        checker = StartupChecker()

        with patch('pathlib.Path.mkdir', side_effect=PermissionError("Cannot create")):
            result = checker.check_writable_paths(paths=["test_path"])

            assert result.passed is False
            assert "Cannot create" in result.message

    def test_check_writable_paths_readonly(self, temp_dir):
        """Test writable paths check with read-only directory."""
        checker = StartupChecker()

        test_path = temp_dir / "readonly"
        test_path.mkdir()

        with patch('pathlib.Path.write_text', side_effect=PermissionError("Read-only")):
            result = checker.check_writable_paths(paths=[str(test_path)])

            assert result.passed is False
            assert "Read-only" in result.message

    def test_check_writable_paths_default_paths(self):
        """Test writable paths check with default paths."""
        checker = StartupChecker()

        with patch('pathlib.Path.mkdir'):
            with patch('pathlib.Path.write_text'):
                with patch('pathlib.Path.unlink'):
                    result = checker.check_writable_paths()  # Use default paths

                    # Should check default paths: reports, output, jobs, logs
                    assert result.name == "Writable Paths"

    def test_check_agents_smoke_test_success(self):
        """Test agents smoke test when agents can be instantiated."""
        checker = StartupChecker()

        mock_validator = MagicMock()
        mock_recommender = MagicMock()

        with patch('agents.content_validator.ContentValidatorAgent', return_value=mock_validator):
            with patch('agents.recommendation_agent.RecommendationAgent', return_value=mock_recommender):
                result = checker.check_agents_smoke_test()

                assert result.name == "Agent Smoke Test"
                assert result.passed is True
                assert "instantiated successfully" in result.message
                assert result.critical is False

    def test_check_agents_smoke_test_failure(self):
        """Test agents smoke test when agent instantiation fails."""
        checker = StartupChecker()

        with patch('agents.content_validator.ContentValidatorAgent', side_effect=Exception("Import error")):
            result = checker.check_agents_smoke_test()

            assert result.passed is False
            assert "smoke test failed" in result.message
            assert "Import error" in result.message


@pytest.mark.unit
class TestRunAllChecks:
    """Test run_all_checks method."""

    def test_run_all_checks_all_pass(self):
        """Test running all checks when everything passes."""
        checker = StartupChecker()

        # Mock all checks to pass
        with patch.object(checker, 'check_database_connectivity', return_value=StartupCheckResult("DB", True, "OK", True)):
            with patch.object(checker, 'check_database_schema', return_value=StartupCheckResult("Schema", True, "OK", True)):
                with patch.object(checker, 'check_ollama_connectivity', return_value=StartupCheckResult("Ollama", True, "OK", False)):
                    with patch.object(checker, 'check_ollama_models', return_value=StartupCheckResult("Models", True, "OK", False)):
                        with patch.object(checker, 'check_writable_paths', return_value=StartupCheckResult("Paths", True, "OK", True)):
                            with patch.object(checker, 'check_agents_smoke_test', return_value=StartupCheckResult("Agents", True, "OK", False)):
                                success, summary = checker.run_all_checks()

                                assert success is True
                                assert summary["total_checks"] == 6
                                assert summary["passed"] == 6
                                assert summary["failed"] == 0
                                assert summary["critical_failures"] == 0

    def test_run_all_checks_non_critical_failure(self):
        """Test running all checks with non-critical failures."""
        checker = StartupChecker()

        # Mock checks with non-critical failure
        with patch.object(checker, 'check_database_connectivity', return_value=StartupCheckResult("DB", True, "OK", True)):
            with patch.object(checker, 'check_database_schema', return_value=StartupCheckResult("Schema", True, "OK", True)):
                with patch.object(checker, 'check_ollama_connectivity', return_value=StartupCheckResult("Ollama", False, "Failed", False)):
                    with patch.object(checker, 'check_ollama_models', return_value=StartupCheckResult("Models", False, "Failed", False)):
                        with patch.object(checker, 'check_writable_paths', return_value=StartupCheckResult("Paths", True, "OK", True)):
                            with patch.object(checker, 'check_agents_smoke_test', return_value=StartupCheckResult("Agents", True, "OK", False)):
                                success, summary = checker.run_all_checks()

                                assert success is True  # Still can start
                                assert summary["failed"] == 2
                                assert summary["critical_failures"] == 0

    def test_run_all_checks_critical_failure(self):
        """Test running all checks with critical failure."""
        checker = StartupChecker()

        # Mock checks with critical failure
        with patch.object(checker, 'check_database_connectivity', return_value=StartupCheckResult("DB", False, "Failed", True)):
            with patch.object(checker, 'check_database_schema', return_value=StartupCheckResult("Schema", True, "OK", True)):
                with patch.object(checker, 'check_ollama_connectivity', return_value=StartupCheckResult("Ollama", True, "OK", False)):
                    with patch.object(checker, 'check_ollama_models', return_value=StartupCheckResult("Models", True, "OK", False)):
                        with patch.object(checker, 'check_writable_paths', return_value=StartupCheckResult("Paths", True, "OK", True)):
                            with patch.object(checker, 'check_agents_smoke_test', return_value=StartupCheckResult("Agents", True, "OK", False)):
                                success, summary = checker.run_all_checks()

                                assert success is False  # Cannot start
                                assert summary["critical_failures"] == 1
                                assert checker.critical_failures == 1

    def test_run_all_checks_multiple_critical_failures(self):
        """Test running all checks with multiple critical failures."""
        checker = StartupChecker()

        # Mock checks with multiple critical failures
        with patch.object(checker, 'check_database_connectivity', return_value=StartupCheckResult("DB", False, "Failed", True)):
            with patch.object(checker, 'check_database_schema', return_value=StartupCheckResult("Schema", False, "Failed", True)):
                with patch.object(checker, 'check_ollama_connectivity', return_value=StartupCheckResult("Ollama", True, "OK", False)):
                    with patch.object(checker, 'check_ollama_models', return_value=StartupCheckResult("Models", True, "OK", False)):
                        with patch.object(checker, 'check_writable_paths', return_value=StartupCheckResult("Paths", False, "Failed", True)):
                            with patch.object(checker, 'check_agents_smoke_test', return_value=StartupCheckResult("Agents", True, "OK", False)):
                                success, summary = checker.run_all_checks()

                                assert success is False
                                assert summary["critical_failures"] == 3
                                assert summary["failed"] == 3


@pytest.mark.unit
class TestRunStartupChecks:
    """Test run_startup_checks convenience function."""

    def test_run_startup_checks_function(self):
        """Test the global run_startup_checks function."""
        with patch('core.startup_checks.StartupChecker') as mock_checker_class:
            mock_checker = MagicMock()
            mock_checker.run_all_checks.return_value = (True, {"passed": 6})
            mock_checker_class.return_value = mock_checker

            success, summary = run_startup_checks()

            assert success is True
            assert summary["passed"] == 6
            mock_checker.run_all_checks.assert_called_once()


@pytest.mark.integration
class TestStartupChecksIntegration:
    """Integration tests for startup checks."""

    def test_full_check_workflow_with_mocks(self, db_manager):
        """Test complete startup check workflow with mocked dependencies."""
        checker = StartupChecker()

        # Mock Ollama to be unavailable (non-critical)
        with patch('core.ollama.OllamaClient') as mock_ollama:
            mock_client = MagicMock()
            mock_client.is_available.return_value = False
            mock_ollama.return_value = mock_client

            # Mock agents to be available
            with patch('agents.content_validator.ContentValidatorAgent'):
                with patch('agents.recommendation_agent.RecommendationAgent'):
                    success, summary = checker.run_all_checks()

                    # Should succeed even if Ollama fails (non-critical)
                    assert summary["total_checks"] == 6
                    assert summary["failed"] >= 1  # At least Ollama connectivity
                    # Critical checks (DB, schema, paths) should pass with mocked DB

    def test_check_results_structure(self):
        """Test that check results have proper structure."""
        checker = StartupChecker()

        # Mock all checks
        with patch.object(checker, 'check_database_connectivity', return_value=StartupCheckResult("DB", True, "OK", True)):
            with patch.object(checker, 'check_database_schema', return_value=StartupCheckResult("Schema", True, "OK", True)):
                with patch.object(checker, 'check_ollama_connectivity', return_value=StartupCheckResult("Ollama", True, "OK", False)):
                    with patch.object(checker, 'check_ollama_models', return_value=StartupCheckResult("Models", True, "OK", False)):
                        with patch.object(checker, 'check_writable_paths', return_value=StartupCheckResult("Paths", True, "OK", True)):
                            with patch.object(checker, 'check_agents_smoke_test', return_value=StartupCheckResult("Agents", True, "OK", False)):
                                success, summary = checker.run_all_checks()

                                # Validate summary structure
                                assert "total_checks" in summary
                                assert "passed" in summary
                                assert "failed" in summary
                                assert "critical_failures" in summary
                                assert "checks" in summary
                                assert isinstance(summary["checks"], list)
                                assert len(summary["checks"]) == 6

                                # Validate check structure
                                for check in summary["checks"]:
                                    assert "name" in check
                                    assert "passed" in check
                                    assert "message" in check
                                    assert "critical" in check
                                    assert "timestamp" in check
