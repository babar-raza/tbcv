"""Tests for CLI MCP helper utilities (TASK-015)."""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner
import click

from cli.mcp_helpers import (
    get_cli_mcp_client,
    with_mcp_client,
    handle_mcp_error,
    format_mcp_result,
    print_mcp_result,
    check_mcp_connection,
    get_exit_code,
    _extract_method,
    _format_json,
    _format_text,
    _format_table,
)
from svc.mcp_exceptions import (
    MCPError,
    MCPMethodNotFoundError,
    MCPInvalidParamsError,
    MCPResourceNotFoundError,
    MCPTimeoutError,
    MCPInternalError,
    MCPValidationError,
)


class TestGetCliMCPClient:
    """Tests for get_cli_mcp_client function."""

    def test_returns_singleton(self):
        """Test that get_cli_mcp_client returns singleton instance."""
        # Reset singleton
        import cli.mcp_helpers
        cli.mcp_helpers._cli_mcp_client = None

        client1 = get_cli_mcp_client()
        client2 = get_cli_mcp_client()

        assert client1 is client2

    def test_creates_client_with_defaults(self):
        """Test that client is created with default parameters."""
        import cli.mcp_helpers
        cli.mcp_helpers._cli_mcp_client = None

        client = get_cli_mcp_client()

        assert client is not None
        assert hasattr(client, 'timeout')
        assert hasattr(client, 'max_retries')


class TestWithMCPClient:
    """Tests for with_mcp_client decorator."""

    def test_injects_mcp_client(self):
        """Test that decorator injects mcp_client parameter."""
        mcp_client_received = []

        @click.command()
        @click.pass_context
        @with_mcp_client
        def test_command(ctx, mcp_client):
            mcp_client_received.append(mcp_client)
            click.echo("Success")

        runner = CliRunner()
        result = runner.invoke(test_command, obj={})

        # Should succeed without errors
        assert result.exit_code == 0
        assert len(mcp_client_received) == 1
        assert mcp_client_received[0] is not None

    def test_handles_mcp_error(self):
        """Test that decorator handles MCP errors."""
        @click.command()
        @click.pass_context
        @with_mcp_client
        def test_command(ctx, mcp_client):
            raise MCPResourceNotFoundError("Test error")

        runner = CliRunner()
        result = runner.invoke(test_command, obj={})

        assert result.exit_code == 1
        assert "Resource not found" in result.output or "Error" in result.output

    def test_handles_generic_exception(self):
        """Test that decorator handles generic exceptions."""
        @click.command()
        @click.pass_context
        @with_mcp_client
        def test_command(ctx, mcp_client):
            raise ValueError("Test error")

        runner = CliRunner()
        result = runner.invoke(test_command, obj={})

        assert result.exit_code == 1

    def test_respects_debug_flag(self):
        """Test that decorator respects mcp_debug flag."""
        @click.command()
        @click.pass_context
        @with_mcp_client
        def test_command(ctx, mcp_client):
            raise MCPInvalidParamsError("Test error", code=-32602)

        runner = CliRunner()

        # Without debug
        result1 = runner.invoke(test_command, obj={'mcp_debug': False})
        assert result1.exit_code == 1

        # With debug
        result2 = runner.invoke(test_command, obj={'mcp_debug': True})
        assert result2.exit_code == 1


class TestHandleMCPError:
    """Tests for handle_mcp_error function."""

    def test_handles_method_not_found(self):
        """Test handling of MCPMethodNotFoundError."""
        error = MCPMethodNotFoundError("Method 'foo' not found", code=-32601)
        msg = handle_mcp_error(error)

        assert "Method not found" in msg
        assert "foo" in msg or "operation" in msg

    def test_handles_invalid_params(self):
        """Test handling of MCPInvalidParamsError."""
        error = MCPInvalidParamsError("Invalid param 'x'", code=-32602)
        msg = handle_mcp_error(error)

        assert "Invalid parameters" in msg

    def test_handles_resource_not_found(self):
        """Test handling of MCPResourceNotFoundError."""
        error = MCPResourceNotFoundError("Validation not found", code=-32001)
        msg = handle_mcp_error(error)

        assert "Resource not found" in msg

    def test_handles_timeout(self):
        """Test handling of MCPTimeoutError."""
        error = MCPTimeoutError("Request timeout", code=-32000)
        msg = handle_mcp_error(error)

        assert "timeout" in msg.lower()

    def test_handles_validation_error(self):
        """Test handling of MCPValidationError."""
        error = MCPValidationError("Validation failed", code=-32000)
        msg = handle_mcp_error(error)

        assert "Validation failed" in msg

    def test_handles_internal_error(self):
        """Test handling of MCPInternalError."""
        error = MCPInternalError("Server error", code=-32603)
        msg = handle_mcp_error(error)

        assert "Internal server error" in msg or "server" in msg.lower()

    def test_handles_generic_error(self):
        """Test handling of generic MCPError."""
        error = MCPError("Generic error", code=-32000)
        msg = handle_mcp_error(error)

        assert "error" in msg.lower()


class TestExtractMethod:
    """Tests for _extract_method function."""

    def test_extracts_method_from_message(self):
        """Test extracting method name from error message."""
        error = MCPError("Method 'validate_file' not found")
        method = _extract_method(error)

        assert method == "validate_file"

    def test_returns_unknown_for_invalid_format(self):
        """Test returning 'unknown' for invalid format."""
        error = MCPError("Some other error")
        method = _extract_method(error)

        assert method == "unknown"


class TestFormatMCPResult:
    """Tests for format_mcp_result function."""

    def test_format_json(self):
        """Test JSON formatting."""
        result = {"files_processed": 5, "issues_found": 2}
        formatted = format_mcp_result(result, format='json')

        assert formatted is not None
        assert isinstance(formatted, str)

    def test_format_text(self):
        """Test text formatting."""
        result = {"files_processed": 5, "issues_found": 2}
        formatted = format_mcp_result(result, format='text')

        assert "Files Processed" in formatted or "files" in formatted.lower()
        assert "5" in formatted

    def test_format_table(self):
        """Test table formatting."""
        result = {
            "validations": [
                {"id": "1", "status": "approved"},
                {"id": "2", "status": "pending"}
            ],
            "total": 2
        }
        formatted = format_mcp_result(result, format='table')

        assert formatted is not None
        assert isinstance(formatted, str)

    def test_invalid_format_raises_error(self):
        """Test that invalid format raises ValueError."""
        result = {"test": "data"}

        with pytest.raises(ValueError, match="Unsupported format"):
            format_mcp_result(result, format='invalid')

    def test_format_with_title(self):
        """Test formatting with title."""
        result = {"test": "data"}
        formatted = format_mcp_result(result, format='text', title="Test Title")

        assert "Test Title" in formatted


class TestFormatHelpers:
    """Tests for format helper functions."""

    def test_format_json_with_title(self):
        """Test _format_json with title."""
        result = {"test": "data"}
        formatted = _format_json(result, title="Test")

        assert formatted is not None

    def test_format_text_with_complex_values(self):
        """Test _format_text with complex values."""
        result = {
            "string": "value",
            "number": 42,
            "bool": True,
            "none": None,
            "list": [1, 2, 3],
            "dict": {"nested": "value"}
        }
        formatted = _format_text(result)

        assert "String: value" in formatted
        assert "Number: 42" in formatted
        assert "Bool: Yes" in formatted
        assert "None: N/A" in formatted

    def test_format_table_fallback_to_text(self):
        """Test _format_table falls back to text for non-list data."""
        result = {"simple": "data"}
        formatted = _format_table(result)

        # Should fall back to text format
        assert "Simple" in formatted or "simple" in formatted


class TestCheckMCPConnection:
    """Tests for check_mcp_connection function."""

    @patch('cli.mcp_helpers.get_cli_mcp_client')
    def test_returns_true_on_success(self, mock_get_client):
        """Test returns True when connection is successful."""
        mock_client = Mock()
        mock_client.get_system_status.return_value = {"status": "ok"}
        mock_get_client.return_value = mock_client

        result = check_mcp_connection()

        assert result is True

    @patch('cli.mcp_helpers.get_cli_mcp_client')
    def test_returns_false_on_error(self, mock_get_client):
        """Test returns False when connection fails."""
        mock_get_client.side_effect = Exception("Connection error")

        result = check_mcp_connection()

        assert result is False


class TestGetExitCode:
    """Tests for get_exit_code function."""

    def test_returns_zero_for_no_error(self):
        """Test returns 0 for no error."""
        assert get_exit_code(None) == 0

    def test_returns_correct_code_for_method_not_found(self):
        """Test returns 127 for MCPMethodNotFoundError."""
        error = MCPMethodNotFoundError("Method not found")
        assert get_exit_code(error) == 127

    def test_returns_correct_code_for_invalid_params(self):
        """Test returns 2 for MCPInvalidParamsError."""
        error = MCPInvalidParamsError("Invalid params")
        assert get_exit_code(error) == 2

    def test_returns_correct_code_for_resource_not_found(self):
        """Test returns 3 for MCPResourceNotFoundError."""
        error = MCPResourceNotFoundError("Not found")
        assert get_exit_code(error) == 3

    def test_returns_correct_code_for_timeout(self):
        """Test returns 4 for MCPTimeoutError."""
        error = MCPTimeoutError("Timeout")
        assert get_exit_code(error) == 4

    def test_returns_correct_code_for_validation_error(self):
        """Test returns 5 for MCPValidationError."""
        error = MCPValidationError("Validation failed")
        assert get_exit_code(error) == 5

    def test_returns_correct_code_for_internal_error(self):
        """Test returns 1 for MCPInternalError."""
        error = MCPInternalError("Internal error")
        assert get_exit_code(error) == 1

    def test_returns_one_for_generic_error(self):
        """Test returns 1 for generic error."""
        error = Exception("Generic error")
        assert get_exit_code(error) == 1


class TestPrintMCPResult:
    """Tests for print_mcp_result function."""

    @patch('cli.mcp_helpers.console')
    def test_prints_formatted_result(self, mock_console):
        """Test prints formatted result."""
        result = {"test": "data"}

        print_mcp_result(result, format='text')

        assert mock_console.print.called

    @patch('cli.mcp_helpers.console')
    def test_prints_with_style(self, mock_console):
        """Test prints with style."""
        result = {"test": "data"}

        print_mcp_result(result, format='text', style='green')

        assert mock_console.print.called


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    @patch('cli.mcp_helpers.get_cli_mcp_client')
    @patch('cli.mcp_helpers.print_mcp_result')
    def test_validate_file_cli(self, mock_print, mock_get_client):
        """Test validate_file_cli convenience function."""
        from cli.mcp_helpers import validate_file_cli

        mock_client = Mock()
        mock_client.validate_file.return_value = {"validation_id": "123"}
        mock_get_client.return_value = mock_client

        validate_file_cli("test.md")

        mock_client.validate_file.assert_called_once()
        mock_print.assert_called_once()

    @patch('cli.mcp_helpers.get_cli_mcp_client')
    @patch('cli.mcp_helpers.print_mcp_result')
    def test_list_validations_cli(self, mock_print, mock_get_client):
        """Test list_validations_cli convenience function."""
        from cli.mcp_helpers import list_validations_cli

        mock_client = Mock()
        mock_client.list_validations.return_value = {"validations": [], "total": 0}
        mock_get_client.return_value = mock_client

        list_validations_cli()

        mock_client.list_validations.assert_called_once()
        mock_print.assert_called_once()

    @patch('cli.mcp_helpers.get_cli_mcp_client')
    @patch('cli.mcp_helpers.print_mcp_result')
    def test_get_system_status_cli(self, mock_print, mock_get_client):
        """Test get_system_status_cli convenience function."""
        from cli.mcp_helpers import get_system_status_cli

        mock_client = Mock()
        mock_client.get_system_status.return_value = {"status": "ok"}
        mock_get_client.return_value = mock_client

        get_system_status_cli()

        mock_client.get_system_status.assert_called_once()
        mock_print.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
