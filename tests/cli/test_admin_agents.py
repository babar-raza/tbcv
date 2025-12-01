"""Tests for CLI admin agent commands (P3-T02)."""
import pytest
from click.testing import CliRunner
from unittest.mock import MagicMock, patch
from cli.main import cli


class TestAdminAgentReload:
    """Test admin agent-reload command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_agent_reload_not_found(self, runner):
        """Test reload when agent not found."""
        mock_registry = MagicMock()
        mock_registry.get_agent.return_value = None

        with patch('cli.main.agent_registry', mock_registry):
            result = runner.invoke(cli, ['admin', 'agent-reload', 'nonexistent'])

        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_agent_reload_success(self, runner):
        """Test successful agent reload."""
        mock_agent = MagicMock()
        # Agent without reload methods
        del mock_agent.reload_config
        del mock_agent.reset_state

        mock_registry = MagicMock()
        mock_registry.get_agent.return_value = mock_agent

        mock_cache = MagicMock()
        mock_cache.clear_agent_cache = MagicMock()

        with patch('cli.main.agent_registry', mock_registry), \
             patch('core.cache.cache_manager', mock_cache):
            result = runner.invoke(cli, ['admin', 'agent-reload', 'content_validator'])

        assert result.exit_code == 0
        assert "reloaded" in result.output.lower()

    def test_agent_reload_with_config(self, runner):
        """Test reload with config reload method."""
        mock_agent = MagicMock()
        mock_agent.reload_config = MagicMock()

        mock_registry = MagicMock()
        mock_registry.get_agent.return_value = mock_agent

        mock_cache = MagicMock()
        mock_cache.clear_agent_cache = MagicMock()

        with patch('cli.main.agent_registry', mock_registry), \
             patch('core.cache.cache_manager', mock_cache):
            result = runner.invoke(cli, ['admin', 'agent-reload', 'truth_manager'])

        assert result.exit_code == 0

    def test_agent_reload_with_reset_state(self, runner):
        """Test reload with reset_state method."""
        mock_agent = MagicMock()
        mock_agent.reset_state = MagicMock()
        del mock_agent.reload_config

        mock_registry = MagicMock()
        mock_registry.get_agent.return_value = mock_agent

        mock_cache = MagicMock()
        mock_cache.clear_agent_cache = MagicMock()

        with patch('cli.main.agent_registry', mock_registry), \
             patch('core.cache.cache_manager', mock_cache):
            result = runner.invoke(cli, ['admin', 'agent-reload', 'seo_validator'])

        assert result.exit_code == 0
        mock_agent.reset_state.assert_called_once()
