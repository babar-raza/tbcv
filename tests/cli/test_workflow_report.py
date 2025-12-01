"""Tests for CLI workflow report commands (P1-T07, P1-T08)."""
import pytest
from click.testing import CliRunner
from unittest.mock import MagicMock, patch
from cli.main import cli


class TestWorkflowReport:
    """Test workflows report command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def mock_report(self):
        return {
            "workflow_id": "wf-123",
            "type": "batch_validation",
            "status": "completed",
            "created_at": "2025-01-01T00:00:00",
            "completed_at": "2025-01-01T00:05:00",
            "duration_ms": 300000,
            "summary": {
                "total_files": 10,
                "files_passed": 8,
                "files_failed": 2,
                "total_issues": 15,
                "total_recommendations": 15
            }
        }

    def test_report_workflow_not_found(self, runner):
        """Test report when workflow not found."""
        mock_db = MagicMock()
        mock_db.generate_workflow_report.side_effect = ValueError("Workflow not found")

        with patch('core.database.db_manager', mock_db):
            result = runner.invoke(cli, ['workflows', 'report', 'nonexistent'])

        assert result.exit_code == 1

    def test_report_text_format(self, runner, mock_report):
        """Test text format output."""
        mock_db = MagicMock()
        mock_db.generate_workflow_report.return_value = mock_report

        with patch('core.database.db_manager', mock_db):
            result = runner.invoke(cli, ['workflows', 'report', 'wf-123'])

        assert result.exit_code == 0
        assert "Workflow Report" in result.output
        assert "completed" in result.output.lower()

    def test_report_json_format(self, runner, mock_report):
        """Test JSON format output."""
        mock_db = MagicMock()
        mock_db.generate_workflow_report.return_value = mock_report

        with patch('core.database.db_manager', mock_db):
            result = runner.invoke(cli, ['workflows', 'report', 'wf-123', '--format', 'json'])

        assert result.exit_code == 0
        assert "workflow_id" in result.output
        assert "wf-123" in result.output

    def test_report_markdown_format(self, runner, mock_report):
        """Test markdown format output."""
        mock_db = MagicMock()
        mock_db.generate_workflow_report.return_value = mock_report

        with patch('core.database.db_manager', mock_db):
            result = runner.invoke(cli, ['workflows', 'report', 'wf-123', '--format', 'markdown'])

        assert result.exit_code == 0
        assert "# Workflow Report" in result.output

    def test_report_save_to_file(self, runner, mock_report, tmp_path):
        """Test saving report to file."""
        output_file = tmp_path / "report.txt"

        mock_db = MagicMock()
        mock_db.generate_workflow_report.return_value = mock_report

        with patch('core.database.db_manager', mock_db):
            result = runner.invoke(cli, ['workflows', 'report', 'wf-123', '--output', str(output_file)])

        assert result.exit_code == 0
        assert output_file.exists()
        assert "Workflow Report" in output_file.read_text()


class TestWorkflowSummary:
    """Test workflows summary command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_summary_text_output(self, runner):
        """Test summary text output."""
        mock_report = {
            "workflow_id": "wf-456",
            "type": "validate_file",
            "status": "completed",
            "created_at": "2025-01-01T00:00:00",
            "duration_ms": 5000,
            "summary": {
                "total_files": 1,
                "files_passed": 1,
                "files_failed": 0,
                "total_issues": 3,
                "total_recommendations": 3
            }
        }

        mock_db = MagicMock()
        mock_db.generate_workflow_report.return_value = mock_report

        with patch('core.database.db_manager', mock_db):
            result = runner.invoke(cli, ['workflows', 'summary', 'wf-456'])

        assert result.exit_code == 0
        assert "completed" in result.output.lower()

    def test_summary_json_output(self, runner):
        """Test summary JSON output."""
        mock_report = {
            "workflow_id": "wf-789",
            "type": "batch_validation",
            "status": "running",
            "created_at": "2025-01-01T00:00:00",
            "summary": {}
        }

        mock_db = MagicMock()
        mock_db.generate_workflow_report.return_value = mock_report

        with patch('core.database.db_manager', mock_db):
            result = runner.invoke(cli, ['workflows', 'summary', 'wf-789', '--format', 'json'])

        assert result.exit_code == 0
        assert "wf-789" in result.output
