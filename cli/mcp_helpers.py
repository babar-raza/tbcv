"""CLI MCP helper utilities for TASK-015.

This module provides helper functions and decorators for integrating
MCP (Model Context Protocol) with CLI commands using Click.

Key Features:
- Singleton MCP client management for CLI
- Click decorator for automatic MCP client injection
- MCP error handling with user-friendly messages
- Result formatting for CLI output (JSON, text, table)

Usage:
    @cli.command()
    @with_mcp_client
    def my_command(mcp_client: MCPSyncClient):
        result = mcp_client.validate_file("path/to/file.md")
        console.print(format_mcp_result(result, format='json'))
"""

import functools
import sys
import json
import traceback
from typing import Callable, Any, Dict, Optional, List
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax

from svc.mcp_client import MCPSyncClient, get_mcp_sync_client
from svc.mcp_exceptions import (
    MCPError,
    MCPMethodNotFoundError,
    MCPInvalidParamsError,
    MCPResourceNotFoundError,
    MCPTimeoutError,
    MCPInternalError,
    MCPValidationError,
)

console = Console()
console_err = Console(stderr=True)

# Global singleton client for CLI
_cli_mcp_client: Optional[MCPSyncClient] = None


def get_cli_mcp_client(timeout: int = 30, max_retries: int = 3) -> MCPSyncClient:
    """
    Get or create singleton MCP client for CLI operations.

    This ensures all CLI commands share the same MCP client instance,
    providing consistent connection handling and caching.

    Args:
        timeout: Request timeout in seconds (default 30)
        max_retries: Maximum number of retries for transient errors (default 3)

    Returns:
        Singleton MCPSyncClient instance

    Example:
        >>> client = get_cli_mcp_client()
        >>> result = client.validate_file("test.md")
    """
    global _cli_mcp_client
    if _cli_mcp_client is None:
        _cli_mcp_client = get_mcp_sync_client(
            timeout=timeout,
            max_retries=max_retries
        )
    return _cli_mcp_client


def with_mcp_client(func: Callable) -> Callable:
    """
    Decorator to inject MCP client into CLI commands.

    This decorator automatically:
    1. Creates/gets the singleton MCP client
    2. Injects it as 'mcp_client' kwarg
    3. Handles MCP errors gracefully
    4. Respects --mcp-debug flag for detailed error output
    5. Returns appropriate exit codes

    Args:
        func: Click command function to decorate

    Returns:
        Decorated function with MCP client injection

    Example:
        @click.command()
        @with_mcp_client
        def validate(mcp_client: MCPSyncClient, file_path: str):
            result = mcp_client.validate_file(file_path)
            console.print(format_mcp_result(result))

    Note:
        - Function must accept 'mcp_client' as a keyword argument
        - Use --mcp-debug flag for detailed error traces
        - Automatically exits with code 1 on errors
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Get click context to access global flags
        ctx = click.get_current_context()
        debug = ctx.obj.get('mcp_debug', False) if ctx.obj else False

        try:
            # Get or create MCP client
            client = get_cli_mcp_client()

            # Inject client into function
            kwargs['mcp_client'] = client

            # Call the decorated function
            return func(*args, **kwargs)

        except MCPError as e:
            # Handle MCP-specific errors
            error_msg = handle_mcp_error(e, debug)
            console_err.print(f"[red]Error: {error_msg}[/red]")

            if debug:
                console_err.print("\n[yellow]Debug Information:[/yellow]")
                console_err.print(f"[dim]Error Code: {e.code}[/dim]")
                if e.data:
                    console_err.print(f"[dim]Error Data: {json.dumps(e.data, indent=2)}[/dim]")

            sys.exit(1)

        except Exception as e:
            # Handle unexpected errors
            console_err.print(f"[red]Unexpected error: {e}[/red]")

            if debug:
                console_err.print("\n[yellow]Stack Trace:[/yellow]")
                traceback.print_exc()

            sys.exit(1)

    return wrapper


def handle_mcp_error(error: MCPError, debug: bool = False) -> str:
    """
    Convert MCP exception to user-friendly CLI error message.

    Maps MCP error types to clear, actionable error messages
    that users can understand and act upon.

    Args:
        error: MCP error to convert
        debug: Whether to include debug information

    Returns:
        User-friendly error message string

    Example:
        >>> error = MCPMethodNotFoundError("Method 'foo' not found")
        >>> msg = handle_mcp_error(error)
        >>> print(msg)
        Method not found: 'foo'...

    Error Types Handled:
        - MCPMethodNotFoundError: Method doesn't exist
        - MCPInvalidParamsError: Invalid parameters
        - MCPResourceNotFoundError: Resource not found
        - MCPTimeoutError: Request timeout
        - MCPValidationError: Validation failure
        - MCPInternalError: Internal server error
        - MCPError: Generic error
    """
    error_messages = {
        MCPMethodNotFoundError: lambda e: (
            f"Method not found: The requested operation '{_extract_method(e)}' is not available. "
            f"This may be due to an outdated CLI version or misconfiguration."
        ),
        MCPInvalidParamsError: lambda e: (
            f"Invalid parameters: {e}. "
            f"Please check your command arguments and try again."
        ),
        MCPResourceNotFoundError: lambda e: (
            f"Resource not found: {e}. "
            f"The requested validation, workflow, or file does not exist."
        ),
        MCPTimeoutError: lambda e: (
            f"Request timeout: The operation took too long to complete. "
            f"This may be due to server load or network issues. Try again in a moment."
        ),
        MCPValidationError: lambda e: (
            f"Validation failed: {e}. "
            f"The content or parameters did not pass validation checks."
        ),
        MCPInternalError: lambda e: (
            f"Internal server error: {e}. "
            f"The MCP server encountered an unexpected problem. "
            f"Check server logs for details."
        ),
    }

    # Get appropriate error message
    for error_type, message_func in error_messages.items():
        if isinstance(error, error_type):
            return message_func(error)

    # Generic fallback
    return f"{error.__class__.__name__}: {error}"


def _extract_method(error: MCPError) -> str:
    """Extract method name from error message."""
    msg = str(error)
    # Try to extract method name from common error message formats
    if "Method " in msg and " not found" in msg:
        parts = msg.split("'")
        if len(parts) >= 2:
            return parts[1]
    return "unknown"


def format_mcp_result(
    result: Dict[str, Any],
    format: str = 'json',
    title: Optional[str] = None
) -> str:
    """
    Format MCP result for CLI output.

    Supports multiple output formats for flexibility:
    - json: Pretty-printed JSON with syntax highlighting
    - text: Human-readable text format
    - table: Rich table format (for list results)

    Args:
        result: MCP result dictionary to format
        format: Output format ('json', 'text', 'table')
        title: Optional title for the output

    Returns:
        Formatted string ready for console output

    Example:
        >>> result = {"files_processed": 5, "issues_found": 2}
        >>> print(format_mcp_result(result, format='text'))
        Files Processed: 5
        Issues Found: 2

    Raises:
        ValueError: If format is not supported
    """
    if format == 'json':
        return _format_json(result, title)
    elif format == 'text':
        return _format_text(result, title)
    elif format == 'table':
        return _format_table(result, title)
    else:
        raise ValueError(f"Unsupported format: {format}. Use 'json', 'text', or 'table'.")


def _format_json(result: Dict[str, Any], title: Optional[str] = None) -> str:
    """Format result as pretty-printed JSON with syntax highlighting."""
    json_str = json.dumps(result, indent=2, default=str)

    # Create syntax-highlighted JSON
    syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)

    if title:
        # Wrap in panel with title
        from io import StringIO
        from contextlib import redirect_stdout

        buffer = StringIO()
        temp_console = Console(file=buffer, force_terminal=True)
        temp_console.print(Panel(syntax, title=title, border_style="blue"))
        return buffer.getvalue()
    else:
        # Return raw syntax
        from io import StringIO
        from contextlib import redirect_stdout

        buffer = StringIO()
        temp_console = Console(file=buffer, force_terminal=True)
        temp_console.print(syntax)
        return buffer.getvalue()


def _format_text(result: Dict[str, Any], title: Optional[str] = None) -> str:
    """Format result as human-readable text."""
    lines = []

    if title:
        lines.append(f"\n{title}")
        lines.append("=" * len(title))

    for key, value in result.items():
        # Convert snake_case to Title Case
        label = key.replace('_', ' ').title()

        # Format value based on type
        if isinstance(value, (list, dict)):
            # For complex types, use JSON
            value_str = json.dumps(value, indent=2, default=str)
        elif isinstance(value, bool):
            value_str = "Yes" if value else "No"
        elif value is None:
            value_str = "N/A"
        else:
            value_str = str(value)

        lines.append(f"{label}: {value_str}")

    return "\n".join(lines)


def _format_table(result: Dict[str, Any], title: Optional[str] = None) -> str:
    """Format result as a Rich table."""
    # Check if result contains a list that can be tablified
    table_data = None
    table_key = None

    for key, value in result.items():
        if isinstance(value, list) and value and isinstance(value[0], dict):
            table_data = value
            table_key = key
            break

    if not table_data:
        # Fallback to text format if no suitable list found
        return _format_text(result, title)

    # Create Rich table
    table = Table(title=title or table_key.replace('_', ' ').title())

    # Add columns from first item
    if table_data:
        first_item = table_data[0]
        for key in first_item.keys():
            table.add_column(key.replace('_', ' ').title(), style="cyan")

        # Add rows
        for item in table_data:
            row = []
            for key in first_item.keys():
                value = item.get(key, "")
                if isinstance(value, (dict, list)):
                    value = json.dumps(value)
                row.append(str(value))
            table.add_row(*row)

    # Render table to string
    from io import StringIO
    from contextlib import redirect_stdout

    buffer = StringIO()
    temp_console = Console(file=buffer, force_terminal=True)
    temp_console.print(table)

    # Add summary info if available
    summary_lines = []
    for key, value in result.items():
        if key != table_key and not isinstance(value, (list, dict)):
            label = key.replace('_', ' ').title()
            summary_lines.append(f"{label}: {value}")

    if summary_lines:
        temp_console.print("\n" + "\n".join(summary_lines))

    return buffer.getvalue()


def print_mcp_result(
    result: Dict[str, Any],
    format: str = 'json',
    title: Optional[str] = None,
    style: Optional[str] = None
) -> None:
    """
    Print MCP result to console with formatting.

    Convenience function that combines formatting and printing.

    Args:
        result: MCP result dictionary to print
        format: Output format ('json', 'text', 'table')
        title: Optional title for the output
        style: Optional Rich style for the output (e.g., 'green', 'bold')

    Example:
        >>> result = mcp_client.validate_file("test.md")
        >>> print_mcp_result(result, format='text', title="Validation Results")
    """
    formatted = format_mcp_result(result, format=format, title=title)

    if style:
        console.print(formatted, style=style)
    else:
        console.print(formatted)


def check_mcp_connection() -> bool:
    """
    Check if MCP server is accessible.

    Useful for health checks and diagnostics.

    Returns:
        True if connection is successful, False otherwise

    Example:
        >>> if not check_mcp_connection():
        >>>     console.print("[red]MCP server is not accessible[/red]")
        >>>     sys.exit(1)
    """
    try:
        client = get_cli_mcp_client(timeout=5, max_retries=1)
        # Try a simple operation to check connectivity
        client.get_system_status()
        return True
    except Exception:
        return False


def get_exit_code(error: Optional[Exception] = None) -> int:
    """
    Get appropriate exit code for CLI commands.

    Maps errors to standard Unix exit codes.

    Args:
        error: Optional exception that occurred

    Returns:
        Exit code (0 for success, non-zero for errors)

    Exit Codes:
        - 0: Success
        - 1: General error
        - 2: Invalid parameters
        - 3: Resource not found
        - 4: Timeout
        - 5: Validation failure
        - 127: Method not found
    """
    if error is None:
        return 0

    exit_codes = {
        MCPMethodNotFoundError: 127,
        MCPInvalidParamsError: 2,
        MCPResourceNotFoundError: 3,
        MCPTimeoutError: 4,
        MCPValidationError: 5,
        MCPInternalError: 1,
    }

    for error_type, code in exit_codes.items():
        if isinstance(error, error_type):
            return code

    return 1  # Generic error


# Convenience functions for common operations

def validate_file_cli(
    file_path: str,
    family: str = "words",
    validation_types: Optional[List[str]] = None,
    format: str = 'text'
) -> None:
    """
    Validate a file via MCP and print results.

    Convenience function for CLI commands.

    Args:
        file_path: Path to file to validate
        family: Plugin family (default "words")
        validation_types: List of specific validators to run
        format: Output format ('json', 'text', 'table')
    """
    client = get_cli_mcp_client()
    result = client.validate_file(
        file_path=file_path,
        family=family,
        validation_types=validation_types
    )
    print_mcp_result(result, format=format, title="Validation Results")


def list_validations_cli(
    limit: int = 100,
    status: Optional[str] = None,
    format: str = 'table'
) -> None:
    """
    List validations via MCP and print results.

    Convenience function for CLI commands.

    Args:
        limit: Maximum number of results
        status: Filter by status (optional)
        format: Output format ('json', 'text', 'table')
    """
    client = get_cli_mcp_client()
    result = client.list_validations(limit=limit, status=status)
    print_mcp_result(result, format=format, title="Validations")


def get_system_status_cli(format: str = 'text') -> None:
    """
    Get system status via MCP and print results.

    Convenience function for CLI commands.

    Args:
        format: Output format ('json', 'text', 'table')
    """
    client = get_cli_mcp_client()
    result = client.get_system_status()
    print_mcp_result(result, format=format, title="System Status")
