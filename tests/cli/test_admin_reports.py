"""Tests for CLI admin report commands (P2-T04)."""
import pytest
from click.testing import CliRunner
from unittest.mock import MagicMock, patch
from cli.main import cli


class TestAdminPerformanceReport:
    """Test admin report performance command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_performance_report_empty(self, runner):
        """Test report with no workflows."""
        mock_db = MagicMock()
        mock_db.list_workflows.return_value = []

        mock_cache = MagicMock()
        mock_cache.get_statistics.return_value = {"l1": {"hit_rate": 0.0}}

        with patch('core.database.db_manager', mock_db), \
             patch('core.cache.cache_manager', mock_cache):
            result = runner.invoke(cli, ['admin', 'report', 'performance'])

        assert result.exit_code == 0
        assert "Performance" in result.output

    def test_performance_report_with_workflows(self, runner):
        """Test report with workflow data."""
        from datetime import datetime, timezone, timedelta
        from unittest.mock import MagicMock

        # Create mock workflows
        mock_workflow1 = MagicMock()
        mock_workflow1.created_at = datetime.now(timezone.utc) - timedelta(days=1)
        mock_workflow1.updated_at = datetime.now(timezone.utc)
        mock_workflow1.state = MagicMock()
        mock_workflow1.state.name = "COMPLETED"

        mock_db = MagicMock()
        mock_db.list_workflows.return_value = [mock_workflow1]

        mock_cache = MagicMock()
        mock_cache.get_statistics.return_value = {"l1": {"hit_rate": 0.75}}

        # We need to patch WorkflowState for the comparison
        with patch('core.database.db_manager', mock_db), \
             patch('core.cache.cache_manager', mock_cache):
            result = runner.invoke(cli, ['admin', 'report', 'performance'])

        assert result.exit_code == 0

    def test_performance_report_json(self, runner):
        """Test JSON output."""
        mock_db = MagicMock()
        mock_db.list_workflows.return_value = []

        mock_cache = MagicMock()
        mock_cache.get_statistics.return_value = {"l1": {"hit_rate": 0.5}}

        with patch('core.database.db_manager', mock_db), \
             patch('core.cache.cache_manager', mock_cache):
            result = runner.invoke(cli, ['admin', 'report', 'performance', '--format', 'json'])

        assert result.exit_code == 0
        assert "total_workflows" in result.output

    def test_performance_report_custom_days(self, runner):
        """Test report with custom days parameter."""
        mock_db = MagicMock()
        mock_db.list_workflows.return_value = []

        mock_cache = MagicMock()
        mock_cache.get_statistics.return_value = {"l1": {"hit_rate": 0.0}}

        with patch('core.database.db_manager', mock_db), \
             patch('core.cache.cache_manager', mock_cache):
            result = runner.invoke(cli, ['admin', 'report', 'performance', '--days', '30'])

        assert result.exit_code == 0
        assert "30 days" in result.output


class TestAdminHealthReport:
    """Test admin report health command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_health_report_healthy(self, runner):
        """Test health report when system healthy."""
        mock_db = MagicMock()
        mock_db.is_connected.return_value = True

        mock_registry = MagicMock()
        mock_registry.agents = {"agent1": MagicMock()}

        with patch('core.database.db_manager', mock_db), \
             patch('cli.main.agent_registry', mock_registry):
            result = runner.invoke(cli, ['admin', 'report', 'health'])

        assert result.exit_code == 0
        assert "HEALTHY" in result.output or "healthy" in result.output.lower()

    def test_health_report_degraded(self, runner):
        """Test health report when database disconnected."""
        mock_db = MagicMock()
        mock_db.is_connected.return_value = False

        mock_registry = MagicMock()
        mock_registry.agents = {}

        with patch('core.database.db_manager', mock_db), \
             patch('cli.main.agent_registry', mock_registry):
            result = runner.invoke(cli, ['admin', 'report', 'health'])

        assert result.exit_code == 0
        assert "degraded" in result.output.lower() or "DEGRADED" in result.output

    def test_health_report_json(self, runner):
        """Test JSON output."""
        mock_db = MagicMock()
        mock_db.is_connected.return_value = True

        mock_registry = MagicMock()
        mock_registry.agents = {"agent1": MagicMock()}

        with patch('core.database.db_manager', mock_db), \
             patch('cli.main.agent_registry', mock_registry):
            result = runner.invoke(cli, ['admin', 'report', 'health', '--format', 'json'])

        assert result.exit_code == 0
        assert "database_connected" in result.output
        assert "status" in result.output
