"""Tests for CLI admin health probe commands (P3-T01)."""
import pytest
from click.testing import CliRunner
from unittest.mock import MagicMock, patch
from cli.main import cli


class TestAdminHealthProbes:
    """Test admin health probe commands."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_health_live_always_succeeds(self, runner):
        """Test liveness probe always returns success."""
        result = runner.invoke(cli, ['admin', 'health-live'])

        assert result.exit_code == 0
        assert "alive" in result.output.lower()

    def test_health_ready_all_checks_pass(self, runner):
        """Test readiness when all checks pass."""
        mock_db = MagicMock()
        mock_db.is_connected.return_value = True

        mock_registry = MagicMock()
        mock_registry.agents = {"agent1": MagicMock()}

        with patch('core.database.db_manager', mock_db), \
             patch('cli.main.agent_registry', mock_registry):
            result = runner.invoke(cli, ['admin', 'health-ready'])

        assert result.exit_code == 0
        assert "READY" in result.output

    def test_health_ready_database_fail(self, runner):
        """Test readiness when database disconnected."""
        mock_db = MagicMock()
        mock_db.is_connected.return_value = False

        mock_registry = MagicMock()
        mock_registry.agents = {"agent1": MagicMock()}

        with patch('core.database.db_manager', mock_db), \
             patch('cli.main.agent_registry', mock_registry):
            result = runner.invoke(cli, ['admin', 'health-ready'])

        assert result.exit_code == 1
        assert "NOT READY" in result.output

    def test_health_ready_no_agents(self, runner):
        """Test readiness when no agents registered."""
        mock_db = MagicMock()
        mock_db.is_connected.return_value = True

        mock_registry = MagicMock()
        mock_registry.agents = {}

        with patch('core.database.db_manager', mock_db), \
             patch('cli.main.agent_registry', mock_registry):
            result = runner.invoke(cli, ['admin', 'health-ready'])

        assert result.exit_code == 1

    def test_health_ready_database_exception(self, runner):
        """Test readiness when database check throws exception."""
        mock_db = MagicMock()
        mock_db.is_connected.side_effect = Exception("Connection failed")

        mock_registry = MagicMock()
        mock_registry.agents = {"agent1": MagicMock()}

        with patch('core.database.db_manager', mock_db), \
             patch('cli.main.agent_registry', mock_registry):
            result = runner.invoke(cli, ['admin', 'health-ready'])

        # Should still return NOT READY gracefully
        assert result.exit_code == 1
        assert "NOT READY" in result.output
