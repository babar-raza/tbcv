"""Tests for CLI admin maintenance commands (P2-T01)."""
import pytest
from click.testing import CliRunner
from unittest.mock import MagicMock, patch
from cli.main import cli


class TestAdminMaintenance:
    """Test admin maintenance commands."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_maintenance_enable_success(self, runner):
        """Test enabling maintenance mode."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"maintenance_mode": True}
        mock_response.raise_for_status = MagicMock()

        with patch('requests.post', return_value=mock_response):
            result = runner.invoke(cli, ['admin', 'maintenance', 'enable'])

        assert result.exit_code == 0
        assert "ENABLED" in result.output

    def test_maintenance_disable_success(self, runner):
        """Test disabling maintenance mode."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"maintenance_mode": False}
        mock_response.raise_for_status = MagicMock()

        with patch('requests.post', return_value=mock_response):
            result = runner.invoke(cli, ['admin', 'maintenance', 'disable'])

        assert result.exit_code == 0
        assert "DISABLED" in result.output

    def test_maintenance_status_enabled(self, runner):
        """Test checking status when enabled."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"system": {"maintenance_mode": True}}
        mock_response.raise_for_status = MagicMock()

        with patch('requests.get', return_value=mock_response):
            result = runner.invoke(cli, ['admin', 'maintenance', 'status'])

        assert result.exit_code == 0
        assert "ENABLED" in result.output

    def test_maintenance_status_disabled(self, runner):
        """Test checking status when disabled."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"system": {"maintenance_mode": False}}
        mock_response.raise_for_status = MagicMock()

        with patch('requests.get', return_value=mock_response):
            result = runner.invoke(cli, ['admin', 'maintenance', 'status'])

        assert result.exit_code == 0
        assert "DISABLED" in result.output

    def test_maintenance_connection_error(self, runner):
        """Test handling connection error."""
        import requests

        with patch('requests.post', side_effect=requests.exceptions.ConnectionError()):
            result = runner.invoke(cli, ['admin', 'maintenance', 'enable'])

        assert result.exit_code == 1
        assert "connect" in result.output.lower()
