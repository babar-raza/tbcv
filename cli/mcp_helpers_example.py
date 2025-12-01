"""Example usage of CLI MCP helpers for TASK-015.

This file demonstrates how to use the MCP helper utilities in CLI commands.
DO NOT IMPORT THIS IN PRODUCTION - IT'S FOR REFERENCE ONLY.
"""

import click
from cli.mcp_helpers import (
    with_mcp_client,
    format_mcp_result,
    print_mcp_result,
    check_mcp_connection,
    get_exit_code,
)
from svc.mcp_client import MCPSyncClient


# Example 1: Basic command with MCP client injection
@click.command()
@click.argument('file_path')
@click.option('--format', default='text', type=click.Choice(['json', 'text', 'table']))
@with_mcp_client
def validate_file(file_path: str, format: str, mcp_client: MCPSyncClient):
    """
    Validate a file using MCP client.

    The @with_mcp_client decorator automatically injects the mcp_client parameter.
    """
    # Call MCP method
    result = mcp_client.validate_file(file_path)

    # Format and print result
    print_mcp_result(result, format=format, title="Validation Results")


# Example 2: Command with error handling
@click.command()
@click.argument('validation_id')
@with_mcp_client
def get_validation(validation_id: str, mcp_client: MCPSyncClient):
    """
    Get validation by ID.

    The @with_mcp_client decorator handles MCP errors automatically.
    """
    result = mcp_client.get_validation(validation_id)
    print_mcp_result(result, format='json', title=f"Validation {validation_id}")


# Example 3: Command with health check
@click.command()
@with_mcp_client
def system_status(mcp_client: MCPSyncClient):
    """
    Get system status with connection check.
    """
    # Check connection first
    if not check_mcp_connection():
        click.echo("Error: MCP server is not accessible", err=True)
        raise click.Abort()

    # Get status
    result = mcp_client.get_system_status()
    print_mcp_result(result, format='text', title="System Status")


# Example 4: Command with custom error handling
@click.command()
@click.argument('workflow_id')
@with_mcp_client
def delete_workflow(workflow_id: str, mcp_client: MCPSyncClient):
    """
    Delete workflow with confirmation.
    """
    if not click.confirm(f"Are you sure you want to delete workflow {workflow_id}?"):
        click.echo("Aborted.")
        return

    # The decorator handles errors, but you can catch them too
    result = mcp_client.delete_workflow(workflow_id)
    click.echo(f"Workflow {workflow_id} deleted successfully.")


# Example 5: Command with multiple MCP calls
@click.command()
@click.option('--limit', default=10, help='Number of validations to list')
@click.option('--status', help='Filter by status')
@with_mcp_client
def list_recent_validations(limit: int, status: str, mcp_client: MCPSyncClient):
    """
    List recent validations with filtering.
    """
    result = mcp_client.list_validations(
        limit=limit,
        status=status
    )

    # Use table format for list results
    print_mcp_result(result, format='table', title="Recent Validations")


# Example 6: Command group with shared MCP client
@click.group()
@click.option('--mcp-debug', is_flag=True, help='Enable MCP debug mode')
@click.pass_context
def cli(ctx, mcp_debug):
    """
    CLI with MCP debug flag support.

    The --mcp-debug flag is automatically picked up by @with_mcp_client decorator.
    """
    # Ensure ctx.obj exists
    ctx.ensure_object(dict)
    ctx.obj['mcp_debug'] = mcp_debug


@cli.command()
@click.argument('file_path')
@with_mcp_client
def validate(file_path: str, mcp_client: MCPSyncClient):
    """Validate a file."""
    result = mcp_client.validate_file(file_path)
    print_mcp_result(result, format='text')


@cli.command()
@with_mcp_client
def status(mcp_client: MCPSyncClient):
    """Get system status."""
    result = mcp_client.get_system_status()
    print_mcp_result(result, format='text')


# Example 7: Manual error handling (without decorator)
@click.command()
@click.argument('validation_ids', nargs=-1)
def approve_manual(validation_ids):
    """
    Approve validations with manual error handling.

    This shows how to handle errors manually if you need custom logic.
    """
    from cli.mcp_helpers import get_cli_mcp_client, handle_mcp_error
    from svc.mcp_exceptions import MCPError

    try:
        client = get_cli_mcp_client()
        result = client.approve(list(validation_ids))
        print_mcp_result(result, format='json')
    except MCPError as e:
        error_msg = handle_mcp_error(e, debug=False)
        click.echo(f"Error: {error_msg}", err=True)
        exit_code = get_exit_code(e)
        raise SystemExit(exit_code)


# Example 8: Convenience function usage
@click.command()
@click.argument('file_path')
@click.option('--format', default='text', type=click.Choice(['json', 'text', 'table']))
def quick_validate(file_path: str, format: str):
    """
    Quick validation using convenience function.
    """
    from cli.mcp_helpers import validate_file_cli

    # One-liner validation with built-in formatting
    validate_file_cli(file_path, format=format)


# Example 9: Format result examples
@click.command()
@with_mcp_client
def format_examples(mcp_client: MCPSyncClient):
    """
    Show different format options.
    """
    result = mcp_client.get_stats()

    # JSON format with syntax highlighting
    click.echo("\n=== JSON Format ===")
    print_mcp_result(result, format='json', title="Statistics")

    # Text format (human-readable)
    click.echo("\n=== Text Format ===")
    print_mcp_result(result, format='text', title="Statistics")

    # Table format (for list results)
    click.echo("\n=== Table Format ===")
    validations = mcp_client.list_validations(limit=5)
    print_mcp_result(validations, format='table', title="Validations")


if __name__ == '__main__':
    # For testing individual commands
    # Run with: python cli/mcp_helpers_example.py
    cli()
