# file: tests/cli/test_new_commands.py
"""
Tests for new CLI commands added for CLI/Web parity.

These tests cover:
- validations command group
- workflows command group
- admin command group
- Enhanced recommendations commands
"""

import pytest
from click.testing import CliRunner
from cli.main import cli
from core.database import db_manager

@pytest.fixture
def runner():
    """CLI test runner."""
    return CliRunner()


class TestValidationsCommands:
    """Tests for the validations command group."""

    def test_validations_list_basic(self, runner):
        """Test validations list basic functionality."""
        result = runner.invoke(cli, ['validations', 'list', '--limit', '5'])
        assert result.exit_code == 0

    def test_validations_list_with_filters(self, runner):
        """Test validations list with status filter."""
        result = runner.invoke(cli, ['validations', 'list', '--status', 'fail'])
        assert result.exit_code == 0

    def test_validations_list_json_output(self, runner):
        """Test validations list with JSON output."""
        result = runner.invoke(cli, ['validations', 'list', '--format', 'json'])
        assert result.exit_code == 0

    def test_validations_show_nonexistent(self, runner):
        """Test validations show with non-existent ID."""
        result = runner.invoke(cli, ['validations', 'show', 'nonexistent_id'])
        assert result.exit_code == 1
        assert 'not found' in result.output.lower()

    def test_validations_history_nonexistent_file(self, runner):
        """Test validations history for non-existent file."""
        result = runner.invoke(cli, ['validations', 'history', 'nonexistent.md'])
        assert result.exit_code == 0  # Should complete successfully with no results

    def test_validations_approve_nonexistent(self, runner):
        """Test validations approve with non-existent ID."""
        result = runner.invoke(cli, ['validations', 'approve', 'nonexistent_id'])
        assert result.exit_code == 1

    def test_validations_reject_nonexistent(self, runner):
        """Test validations reject with non-existent ID."""
        result = runner.invoke(cli, ['validations', 'reject', 'nonexistent_id'])
        assert result.exit_code == 1

    def test_validations_revalidate_nonexistent(self, runner):
        """Test validations revalidate with non-existent ID."""
        result = runner.invoke(cli, ['validations', 'revalidate', 'nonexistent_id'])
        assert result.exit_code == 1


class TestWorkflowsCommands:
    """Tests for the workflows command group."""

    def test_workflows_list_basic(self, runner):
        """Test workflows list basic functionality."""
        result = runner.invoke(cli, ['workflows', 'list', '--limit', '5'])
        assert result.exit_code == 0

    def test_workflows_list_with_state_filter(self, runner):
        """Test workflows list with state filter."""
        result = runner.invoke(cli, ['workflows', 'list', '--state', 'completed'])
        assert result.exit_code == 0

    def test_workflows_list_json_output(self, runner):
        """Test workflows list with JSON output."""
        result = runner.invoke(cli, ['workflows', 'list', '--format', 'json'])
        assert result.exit_code == 0

    def test_workflows_show_nonexistent(self, runner):
        """Test workflows show with non-existent ID."""
        result = runner.invoke(cli, ['workflows', 'show', 'nonexistent_id'])
        assert result.exit_code == 1
        assert 'not found' in result.output.lower()

    def test_workflows_cancel_nonexistent(self, runner):
        """Test workflows cancel with non-existent ID."""
        result = runner.invoke(cli, ['workflows', 'cancel', 'nonexistent_id'])
        assert result.exit_code == 1

    def test_workflows_delete_no_ids(self, runner):
        """Test workflows delete without IDs."""
        result = runner.invoke(cli, ['workflows', 'delete'])
        assert result.exit_code != 0

    def test_workflows_delete_with_confirmation(self, runner):
        """Test workflows delete with confirmation."""
        result = runner.invoke(cli, ['workflows', 'delete', 'fake_id', '--confirm'])
        # Should complete but may not find workflow
        assert result.exit_code in [0, 1]


class TestAdminCommands:
    """Tests for the admin command group."""

    def test_admin_cache_stats(self, runner):
        """Test admin cache-stats command."""
        result = runner.invoke(cli, ['admin', 'cache-stats'])
        assert result.exit_code == 0
        assert 'cache' in result.output.lower()

    def test_admin_cache_clear_all(self, runner):
        """Test admin cache-clear command."""
        result = runner.invoke(cli, ['admin', 'cache-clear'])
        assert result.exit_code == 0
        assert 'cleared' in result.output.lower()

    def test_admin_cache_clear_l1(self, runner):
        """Test admin cache-clear --l1."""
        result = runner.invoke(cli, ['admin', 'cache-clear', '--l1'])
        assert result.exit_code == 0

    def test_admin_cache_clear_l2(self, runner):
        """Test admin cache-clear --l2."""
        result = runner.invoke(cli, ['admin', 'cache-clear', '--l2'])
        assert result.exit_code == 0

    def test_admin_agents(self, runner):
        """Test admin agents command."""
        result = runner.invoke(cli, ['admin', 'agents'])
        assert result.exit_code == 0
        assert 'agent' in result.output.lower()

    def test_admin_health_basic(self, runner):
        """Test admin health basic command."""
        result = runner.invoke(cli, ['admin', 'health'])
        assert result.exit_code == 0
        assert 'health' in result.output.lower()

    def test_admin_health_full(self, runner):
        """Test admin health --full command."""
        result = runner.invoke(cli, ['admin', 'health', '--full'])
        assert result.exit_code == 0
        assert 'agent' in result.output.lower()

    def test_admin_reset_no_confirm(self, runner):
        """Test admin reset without confirmation (should prompt)."""
        # Provide empty input to cancel
        result = runner.invoke(cli, ['admin', 'reset', '--all'], input='CANCEL\n')
        assert result.exit_code == 0
        assert 'cancelled' in result.output.lower() or 'type' in result.output.lower()

    def test_admin_reset_with_confirm_flag(self, runner):
        """Test admin reset with --confirm flag (auto-confirm)."""
        result = runner.invoke(cli, ['admin', 'reset', '--validations', '--confirm'])
        # Should complete successfully (may delete 0 items if none exist)
        assert result.exit_code in [0, 1]  # 0 for success, 1 for expected errors

    def test_admin_reset_validations_only(self, runner):
        """Test admin reset --validations."""
        result = runner.invoke(cli, ['admin', 'reset', '--validations', '--confirm'])
        assert result.exit_code in [0, 1]
        # Should mention validations in output if successful
        if result.exit_code == 0:
            assert 'validations' in result.output.lower() or 'reset' in result.output.lower()

    def test_admin_reset_workflows_only(self, runner):
        """Test admin reset --workflows."""
        result = runner.invoke(cli, ['admin', 'reset', '--workflows', '--confirm'])
        assert result.exit_code in [0, 1]

    def test_admin_reset_recommendations_only(self, runner):
        """Test admin reset --recommendations."""
        result = runner.invoke(cli, ['admin', 'reset', '--recommendations', '--confirm'])
        assert result.exit_code in [0, 1]

    def test_admin_reset_multiple_options(self, runner):
        """Test admin reset with multiple options."""
        result = runner.invoke(cli, ['admin', 'reset', '--workflows', '--recommendations', '--confirm'])
        assert result.exit_code in [0, 1]

    def test_admin_reset_with_cache_clear(self, runner):
        """Test admin reset --clear-cache."""
        result = runner.invoke(cli, ['admin', 'reset', '--validations', '--clear-cache', '--confirm'])
        assert result.exit_code in [0, 1]
        # Should mention cache if successful
        if result.exit_code == 0:
            assert 'cache' in result.output.lower() or 'reset' in result.output.lower()

    def test_admin_reset_help(self, runner):
        """Test admin reset --help."""
        result = runner.invoke(cli, ['admin', 'reset', '--help'])
        assert result.exit_code == 0
        assert 'reset' in result.output.lower()
        assert 'dangerous' in result.output.lower() or 'delete' in result.output.lower()


class TestRecommendationsEnhanced:
    """Tests for enhanced recommendations commands."""

    def test_recommendations_generate_nonexistent(self, runner):
        """Test recommendations generate with non-existent validation ID."""
        result = runner.invoke(cli, ['recommendations', 'generate', 'nonexistent_id'])
        assert result.exit_code == 1

    def test_recommendations_generate_with_force(self, runner):
        """Test recommendations generate with --force flag."""
        result = runner.invoke(cli, ['recommendations', 'generate', 'fake_id', '--force'])
        assert result.exit_code == 1  # Should fail on non-existent ID

    def test_recommendations_rebuild_nonexistent(self, runner):
        """Test recommendations rebuild with non-existent validation ID."""
        result = runner.invoke(cli, ['recommendations', 'rebuild', 'nonexistent_id'])
        assert result.exit_code == 1

    def test_recommendations_delete_no_ids(self, runner):
        """Test recommendations delete without IDs."""
        result = runner.invoke(cli, ['recommendations', 'delete'])
        assert result.exit_code != 0

    def test_recommendations_delete_with_confirmation(self, runner):
        """Test recommendations delete with confirmation."""
        result = runner.invoke(cli, ['recommendations', 'delete', 'fake_id', '--confirm'])
        # Should complete but may not find recommendation
        assert result.exit_code in [0, 1]

    def test_recommendations_auto_apply_nonexistent(self, runner):
        """Test recommendations auto-apply with non-existent validation ID."""
        result = runner.invoke(cli, ['recommendations', 'auto-apply', 'nonexistent_id'])
        assert result.exit_code == 1

    def test_recommendations_auto_apply_dry_run(self, runner):
        """Test recommendations auto-apply --dry-run."""
        result = runner.invoke(cli, ['recommendations', 'auto-apply', 'fake_id', '--dry-run'])
        assert result.exit_code == 1  # Should fail on non-existent ID

    def test_recommendations_auto_apply_threshold(self, runner):
        """Test recommendations auto-apply with custom threshold."""
        result = runner.invoke(cli, ['recommendations', 'auto-apply', 'fake_id', '--threshold', '0.90'])
        assert result.exit_code == 1  # Should fail on non-existent ID


class TestCommandHelp:
    """Test that all commands have help text."""

    def test_validations_help(self, runner):
        """Test validations --help."""
        result = runner.invoke(cli, ['validations', '--help'])
        assert result.exit_code == 0
        assert 'validation' in result.output.lower()

    def test_workflows_help(self, runner):
        """Test workflows --help."""
        result = runner.invoke(cli, ['workflows', '--help'])
        assert result.exit_code == 0
        assert 'workflow' in result.output.lower()

    def test_admin_help(self, runner):
        """Test admin --help."""
        result = runner.invoke(cli, ['admin', '--help'])
        assert result.exit_code == 0
        assert 'admin' in result.output.lower()

    def test_recommendations_help(self, runner):
        """Test recommendations --help."""
        result = runner.invoke(cli, ['recommendations', '--help'])
        assert result.exit_code == 0
        assert 'recommendation' in result.output.lower()


@pytest.mark.integration
class TestIntegrationWorkflows:
    """Integration tests for complete workflows."""

    def test_validate_to_recommendations_workflow(self, runner):
        """Test complete workflow from validation to recommendations."""
        # This would require a real file and database setup
        # Placeholder for integration test
        pass

    def test_admin_workflow(self, runner):
        """Test admin operations workflow."""
        # Test cache stats → clear → stats again
        result1 = runner.invoke(cli, ['admin', 'cache-stats'])
        assert result1.exit_code == 0

        result2 = runner.invoke(cli, ['admin', 'cache-clear'])
        assert result2.exit_code == 0

        result3 = runner.invoke(cli, ['admin', 'cache-stats'])
        assert result3.exit_code == 0
