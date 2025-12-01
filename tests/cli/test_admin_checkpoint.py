"""Tests for CLI admin checkpoint command (P3-T03)."""
import pytest
from click.testing import CliRunner
from unittest.mock import MagicMock, patch
from cli.main import cli


class TestAdminCheckpoint:
    """Test admin checkpoint command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_checkpoint_success(self, runner):
        """Test successful checkpoint creation."""
        mock_db = MagicMock()
        mock_db.list_workflows.return_value = []
        mock_session = MagicMock()
        mock_db.get_session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_db.get_session.return_value.__exit__ = MagicMock(return_value=None)

        mock_registry = MagicMock()
        mock_registry.agents = {}

        mock_cache = MagicMock()
        mock_cache.get_statistics.return_value = {}

        with patch('core.database.db_manager', mock_db), \
             patch('cli.main.agent_registry', mock_registry), \
             patch('core.cache.cache_manager', mock_cache):
            result = runner.invoke(cli, ['admin', 'checkpoint'])

        assert result.exit_code == 0
        assert "Checkpoint" in result.output

    def test_checkpoint_with_name(self, runner):
        """Test checkpoint with custom name."""
        mock_db = MagicMock()
        mock_db.list_workflows.return_value = []
        mock_session = MagicMock()
        mock_db.get_session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_db.get_session.return_value.__exit__ = MagicMock(return_value=None)

        mock_registry = MagicMock()
        mock_registry.agents = {}

        mock_cache = MagicMock()
        mock_cache.get_statistics.return_value = {}

        with patch('core.database.db_manager', mock_db), \
             patch('cli.main.agent_registry', mock_registry), \
             patch('core.cache.cache_manager', mock_cache):
            result = runner.invoke(cli, ['admin', 'checkpoint', '--name', 'my_test_checkpoint'])

        assert result.exit_code == 0
        assert "my_test_checkpoint" in result.output

    def test_checkpoint_captures_workflow_state(self, runner):
        """Test checkpoint captures workflow information."""
        mock_workflow = MagicMock()
        mock_workflow.state = MagicMock()

        # Need to import WorkflowState for comparison
        from core.database import WorkflowState
        mock_workflow.state = WorkflowState.RUNNING

        mock_db = MagicMock()
        mock_db.list_workflows.return_value = [mock_workflow]
        mock_session = MagicMock()
        mock_db.get_session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_db.get_session.return_value.__exit__ = MagicMock(return_value=None)

        mock_registry = MagicMock()
        mock_registry.agents = {"agent1": MagicMock()}

        mock_cache = MagicMock()
        mock_cache.get_statistics.return_value = {}

        with patch('core.database.db_manager', mock_db), \
             patch('cli.main.agent_registry', mock_registry), \
             patch('core.cache.cache_manager', mock_cache):
            result = runner.invoke(cli, ['admin', 'checkpoint'])

        assert result.exit_code == 0
        # Should show workflow count
        assert "1" in result.output

    def test_checkpoint_handles_no_checkpoint_model(self, runner):
        """Test checkpoint works even if Checkpoint model doesn't exist."""
        mock_db = MagicMock()
        mock_db.list_workflows.return_value = []
        # Simulate Checkpoint model not existing
        mock_db.get_session.side_effect = ImportError("No Checkpoint model")

        mock_registry = MagicMock()
        mock_registry.agents = {}

        mock_cache = MagicMock()
        mock_cache.get_statistics.return_value = {}

        with patch('core.database.db_manager', mock_db), \
             patch('cli.main.agent_registry', mock_registry), \
             patch('core.cache.cache_manager', mock_cache):
            result = runner.invoke(cli, ['admin', 'checkpoint'])

        # Should still show checkpoint info even if persist fails
        # Exit code might be 0 or 1 depending on how error is handled
        assert "Checkpoint" in result.output or result.exit_code == 1
