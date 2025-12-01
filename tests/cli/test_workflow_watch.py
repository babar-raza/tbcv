"""Tests for CLI workflow watch command (P2-T05)."""
import pytest
from click.testing import CliRunner
from unittest.mock import MagicMock, patch
from cli.main import cli, _make_progress_bar


class TestWorkflowWatch:
    """Test workflows watch command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_watch_workflow_not_found(self, runner):
        """Test watch when workflow not found."""
        mock_db = MagicMock()
        mock_db.get_workflow.return_value = None

        with patch('core.database.db_manager', mock_db):
            result = runner.invoke(cli, ['workflows', 'watch', 'nonexistent'])

        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_watch_completed_workflow(self, runner):
        """Test watching already completed workflow."""
        mock_workflow = MagicMock()
        mock_workflow.state.value = "completed"
        mock_workflow.progress_percent = 100

        mock_db = MagicMock()
        mock_db.get_workflow.return_value = mock_workflow

        with patch('core.database.db_manager', mock_db):
            result = runner.invoke(cli, ['workflows', 'watch', 'wf-123'])

        assert result.exit_code == 0
        assert "completed" in result.output.lower()

    def test_watch_failed_workflow(self, runner):
        """Test watching failed workflow."""
        mock_workflow = MagicMock()
        mock_workflow.state.value = "failed"
        mock_workflow.progress_percent = 50

        mock_db = MagicMock()
        mock_db.get_workflow.return_value = mock_workflow

        with patch('core.database.db_manager', mock_db):
            result = runner.invoke(cli, ['workflows', 'watch', 'wf-456'])

        assert result.exit_code == 0
        assert "failed" in result.output.lower()

    def test_watch_cancelled_workflow(self, runner):
        """Test watching cancelled workflow."""
        mock_workflow = MagicMock()
        mock_workflow.state.value = "cancelled"
        mock_workflow.progress_percent = 25

        mock_db = MagicMock()
        mock_db.get_workflow.return_value = mock_workflow

        with patch('core.database.db_manager', mock_db):
            result = runner.invoke(cli, ['workflows', 'watch', 'wf-789'])

        assert result.exit_code == 0
        assert "cancelled" in result.output.lower()


class TestProgressBarGeneration:
    """Test progress bar generation helper."""

    def test_progress_bar_zero(self):
        """Test progress bar at 0%."""
        bar = _make_progress_bar(0)
        assert "--------------------" in bar
        assert "[" in bar
        assert "]" in bar

    def test_progress_bar_fifty(self):
        """Test progress bar at 50%."""
        bar = _make_progress_bar(50)
        assert "==========" in bar
        assert "----------" in bar

    def test_progress_bar_hundred(self):
        """Test progress bar at 100%."""
        bar = _make_progress_bar(100)
        assert "====================" in bar

    def test_progress_bar_custom_width(self):
        """Test progress bar with custom width."""
        bar = _make_progress_bar(50, width=10)
        assert "=====" in bar
        assert "-----" in bar
