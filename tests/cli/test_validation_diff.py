"""Tests for CLI validation diff and compare commands (P1-T05, P1-T06)."""
import pytest
from click.testing import CliRunner
from unittest.mock import MagicMock, patch
from cli.main import cli


class TestValidationDiff:
    """Test validations diff command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def mock_validation_with_diff(self):
        mock = MagicMock()
        mock.file_path = "/test/file.md"
        mock.validation_results = {
            "original_content": "Line 1\nLine 2\nLine 3",
            "enhanced_content": "Line 1\nModified Line 2\nLine 3\nLine 4"
        }
        return mock

    def test_diff_validation_not_found(self, runner):
        """Test diff when validation not found."""
        mock_db = MagicMock()
        mock_db.get_validation_result.return_value = None

        with patch('core.database.db_manager', mock_db):
            result = runner.invoke(cli, ['validations', 'diff', 'nonexistent'])

        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_diff_no_enhancement(self, runner):
        """Test diff when validation not enhanced."""
        mock_validation = MagicMock()
        mock_validation.validation_results = {}

        mock_db = MagicMock()
        mock_db.get_validation_result.return_value = mock_validation

        with patch('core.database.db_manager', mock_db):
            result = runner.invoke(cli, ['validations', 'diff', 'test-id'])

        assert result.exit_code == 1
        assert "not have been enhanced" in result.output.lower() or "no diff" in result.output.lower()

    def test_diff_unified_format(self, runner, mock_validation_with_diff):
        """Test unified diff format."""
        mock_db = MagicMock()
        mock_db.get_validation_result.return_value = mock_validation_with_diff

        with patch('core.database.db_manager', mock_db):
            result = runner.invoke(cli, ['validations', 'diff', 'test-id'])

        assert result.exit_code == 0
        # Should show diff markers
        assert "+" in result.output or "-" in result.output or "@@" in result.output

    def test_diff_json_format(self, runner, mock_validation_with_diff):
        """Test JSON output format."""
        mock_db = MagicMock()
        mock_db.get_validation_result.return_value = mock_validation_with_diff

        with patch('core.database.db_manager', mock_db):
            result = runner.invoke(cli, ['validations', 'diff', 'test-id', '--format', 'json'])

        assert result.exit_code == 0
        assert "validation_id" in result.output
        assert "has_diff" in result.output

    def test_diff_side_by_side_format(self, runner, mock_validation_with_diff):
        """Test side-by-side format."""
        mock_db = MagicMock()
        mock_db.get_validation_result.return_value = mock_validation_with_diff

        with patch('core.database.db_manager', mock_db):
            result = runner.invoke(cli, ['validations', 'diff', 'test-id', '--format', 'side-by-side'])

        assert result.exit_code == 0
        assert "Original" in result.output or "Enhanced" in result.output


class TestValidationCompare:
    """Test validations compare command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_compare_validation_not_found(self, runner):
        """Test compare when validation not found."""
        mock_db = MagicMock()
        mock_db.get_validation_result.return_value = None

        with patch('core.database.db_manager', mock_db):
            result = runner.invoke(cli, ['validations', 'compare', 'nonexistent'])

        assert result.exit_code == 1

    def test_compare_shows_statistics(self, runner):
        """Test compare shows statistics."""
        mock_validation = MagicMock()
        mock_validation.file_path = "/test/file.md"
        mock_validation.validation_results = {
            "original_content": "Line 1\nLine 2",
            "enhanced_content": "Line 1\nLine 2\nLine 3",
            "applied_recommendations": 2
        }

        mock_db = MagicMock()
        mock_db.get_validation_result.return_value = mock_validation

        with patch('core.database.db_manager', mock_db):
            result = runner.invoke(cli, ['validations', 'compare', 'test-id'])

        assert result.exit_code == 0
        assert "Statistics" in result.output or "lines" in result.output.lower()

    def test_compare_json_format(self, runner):
        """Test compare JSON output."""
        mock_validation = MagicMock()
        mock_validation.file_path = "/test/file.md"
        mock_validation.validation_results = {
            "original_content": "Line 1",
            "enhanced_content": "Line 1\nLine 2",
            "applied_recommendations": 1
        }

        mock_db = MagicMock()
        mock_db.get_validation_result.return_value = mock_validation

        with patch('core.database.db_manager', mock_db):
            result = runner.invoke(cli, ['validations', 'compare', 'test-id', '--format', 'json'])

        assert result.exit_code == 0
        assert "similarity_ratio" in result.output
        assert "lines_added" in result.output
