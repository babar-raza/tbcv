"""Tests for CLI admin enhancement commands (P1-T03, P1-T04)."""
import pytest
from click.testing import CliRunner
from unittest.mock import MagicMock, patch
from cli.main import cli


class TestAdminEnhancements:
    """Test admin enhancements command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_list_enhancements_empty(self, runner):
        """Test listing when no enhancements exist."""
        mock_history = MagicMock()
        mock_history.list_enhancements.return_value = []

        with patch('agents.enhancement_history.get_history_manager', return_value=mock_history):
            result = runner.invoke(cli, ['admin', 'enhancements'])

        assert result.exit_code == 0
        assert "No enhancement" in result.output

    def test_list_enhancements_with_records(self, runner):
        """Test listing with enhancement records."""
        from datetime import datetime, timezone

        mock_record = MagicMock()
        mock_record.enhancement_id = "enh-123"
        mock_record.file_path = "/test/file.md"
        mock_record.rolled_back = False
        mock_record.applied_at = datetime.now(timezone.utc)
        mock_record.applied_by = "test_user"
        mock_record.recommendations_count = 5

        mock_history = MagicMock()
        mock_history.list_enhancements.return_value = [mock_record]

        with patch('agents.enhancement_history.get_history_manager', return_value=mock_history):
            result = runner.invoke(cli, ['admin', 'enhancements'])

        assert result.exit_code == 0
        assert "enh-123" in result.output or "Enhancement" in result.output

    def test_list_enhancements_json_format(self, runner):
        """Test JSON output format."""
        from datetime import datetime, timezone

        mock_record = MagicMock()
        mock_record.enhancement_id = "enh-456"
        mock_record.file_path = "/test/file.md"
        mock_record.rolled_back = False
        mock_record.applied_at = datetime.now(timezone.utc)
        mock_record.applied_by = "test_user"
        mock_record.recommendations_count = 3

        mock_history = MagicMock()
        mock_history.list_enhancements.return_value = [mock_record]

        with patch('agents.enhancement_history.get_history_manager', return_value=mock_history):
            result = runner.invoke(cli, ['admin', 'enhancements', '--format', 'json'])

        assert result.exit_code == 0
        assert "enh-456" in result.output

    def test_list_enhancements_with_file_filter(self, runner):
        """Test filtering by file path."""
        mock_history = MagicMock()
        mock_history.list_enhancements.return_value = []

        with patch('agents.enhancement_history.get_history_manager', return_value=mock_history):
            result = runner.invoke(cli, ['admin', 'enhancements', '--file-path', '/test/path.md'])

        mock_history.list_enhancements.assert_called_once_with(
            file_path='/test/path.md', limit=50
        )


class TestAdminEnhancementDetail:
    """Test admin enhancement-detail command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_enhancement_detail_not_found(self, runner):
        """Test detail when enhancement not found."""
        mock_history = MagicMock()
        mock_history.get_enhancement_record.return_value = None

        with patch('agents.enhancement_history.get_history_manager', return_value=mock_history):
            result = runner.invoke(cli, ['admin', 'enhancement-detail', 'nonexistent'])

        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_enhancement_detail_success(self, runner):
        """Test successful detail retrieval."""
        from datetime import datetime, timezone

        mock_record = MagicMock()
        mock_record.enhancement_id = "enh-789"
        mock_record.file_path = "/test/file.md"
        mock_record.validation_id = "val-123"
        mock_record.rolled_back = False
        mock_record.applied_at = datetime.now(timezone.utc)
        mock_record.applied_by = "user"
        mock_record.recommendations_applied = 3
        mock_record.recommendations_count = 5
        mock_record.safety_score = 0.95
        mock_record.rollback_available = True
        mock_record.rolled_back_at = None
        mock_record.rolled_back_by = None

        mock_history = MagicMock()
        mock_history.get_enhancement_record.return_value = mock_record

        with patch('agents.enhancement_history.get_history_manager', return_value=mock_history):
            result = runner.invoke(cli, ['admin', 'enhancement-detail', 'enh-789'])

        assert result.exit_code == 0


class TestAdminRollback:
    """Test admin rollback command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_rollback_requires_confirm(self, runner):
        """Test rollback requires --confirm flag."""
        result = runner.invoke(cli, ['admin', 'rollback', 'enh-123'])

        assert result.exit_code == 0  # Exits gracefully with message
        assert "confirm" in result.output.lower()

    def test_rollback_enhancement_not_found(self, runner):
        """Test rollback when enhancement not found."""
        mock_history = MagicMock()
        mock_history.get_enhancement_record.return_value = None

        with patch('agents.enhancement_history.get_history_manager', return_value=mock_history):
            result = runner.invoke(cli, ['admin', 'rollback', 'nonexistent', '--confirm'])

        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_rollback_success(self, runner):
        """Test successful rollback."""
        from datetime import datetime, timezone

        mock_record = MagicMock()
        mock_record.enhancement_id = "enh-123"
        mock_record.file_path = "/test/file.md"
        mock_record.applied_at = datetime.now(timezone.utc)

        mock_history = MagicMock()
        mock_history.get_enhancement_record.return_value = mock_record
        mock_history.rollback_enhancement.return_value = True

        with patch('agents.enhancement_history.get_history_manager', return_value=mock_history):
            result = runner.invoke(cli, ['admin', 'rollback', 'enh-123', '--confirm'])

        assert result.exit_code == 0
        assert "successful" in result.output.lower()

    def test_rollback_failure(self, runner):
        """Test rollback failure (expired/not found)."""
        from datetime import datetime, timezone

        mock_record = MagicMock()
        mock_record.enhancement_id = "enh-123"
        mock_record.file_path = "/test/file.md"
        mock_record.applied_at = datetime.now(timezone.utc)

        mock_history = MagicMock()
        mock_history.get_enhancement_record.return_value = mock_record
        mock_history.rollback_enhancement.return_value = False

        with patch('agents.enhancement_history.get_history_manager', return_value=mock_history):
            result = runner.invoke(cli, ['admin', 'rollback', 'enh-123', '--confirm'])

        assert result.exit_code == 1
        assert "failed" in result.output.lower()
