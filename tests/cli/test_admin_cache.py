"""Tests for CLI admin cache commands (P2-T02, P2-T03)."""
import pytest
from click.testing import CliRunner
from unittest.mock import MagicMock, patch
from cli.main import cli


class TestAdminCacheCleanup:
    """Test admin cache-cleanup command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_cache_cleanup_success(self, runner):
        """Test successful cache cleanup."""
        mock_cache = MagicMock()
        mock_cache.cleanup_expired.return_value = {
            "l1_cleaned": 5,
            "l2_cleaned": 10
        }

        with patch('core.cache.cache_manager', mock_cache):
            result = runner.invoke(cli, ['admin', 'cache-cleanup'])

        assert result.exit_code == 0
        assert "Cleanup" in result.output

    def test_cache_cleanup_empty(self, runner):
        """Test cleanup when nothing to clean."""
        mock_cache = MagicMock()
        mock_cache.cleanup_expired.return_value = {
            "l1_cleaned": 0,
            "l2_cleaned": 0
        }

        with patch('core.cache.cache_manager', mock_cache):
            result = runner.invoke(cli, ['admin', 'cache-cleanup'])

        assert result.exit_code == 0


class TestAdminCacheRebuild:
    """Test admin cache-rebuild command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_cache_rebuild_success(self, runner):
        """Test successful cache rebuild."""
        mock_cache = MagicMock()
        mock_cache.l1_cache = MagicMock()
        mock_cache.l1_cache.size.return_value = 10
        mock_cache.clear_l1 = MagicMock()
        mock_cache.clear_l2 = MagicMock(return_value=20)

        mock_db = MagicMock()

        with patch('core.cache.cache_manager', mock_cache), \
             patch('core.database.db_manager', mock_db):
            result = runner.invoke(cli, ['admin', 'cache-rebuild'])

        assert result.exit_code == 0
        assert "rebuild" in result.output.lower()

    def test_cache_rebuild_with_preload(self, runner):
        """Test rebuild with truth preload."""
        mock_cache = MagicMock()
        mock_cache.l1_cache = MagicMock()
        mock_cache.l1_cache.size.return_value = 0
        mock_cache.clear_l1 = MagicMock()
        mock_cache.clear_l2 = MagicMock(return_value=0)

        mock_db = MagicMock()

        mock_registry = MagicMock()
        mock_registry.get_agent.return_value = None

        with patch('core.cache.cache_manager', mock_cache), \
             patch('core.database.db_manager', mock_db), \
             patch('agents.base.agent_registry', mock_registry):
            result = runner.invoke(cli, ['admin', 'cache-rebuild', '--preload-truth'])

        assert result.exit_code == 0
