# CLI MCP Helper Utilities (TASK-015)

## Overview

The `cli/mcp_helpers.py` module provides helper functions and decorators for integrating MCP (Model Context Protocol) with CLI commands using Click. This is a critical component of the MCP migration that allows CLI commands to seamlessly use the MCP client instead of directly accessing agents.

## Key Features

1. **Singleton MCP Client Management** - Ensures all CLI commands share the same MCP client instance
2. **Click Decorator** - `@with_mcp_client` decorator for automatic client injection
3. **User-Friendly Error Handling** - Converts MCP exceptions to clear, actionable messages
4. **Multiple Output Formats** - Support for JSON, text, and table formatting
5. **Debug Mode Support** - `--mcp-debug` flag for detailed error traces
6. **Standard Exit Codes** - Unix-standard exit codes for different error types

## Core Functions

### 1. `get_cli_mcp_client(timeout=30, max_retries=3)`

Get or create the singleton MCP client for CLI operations.

```python
from cli.mcp_helpers import get_cli_mcp_client

client = get_cli_mcp_client()
result = client.validate_file("test.md")
```

**Parameters:**
- `timeout` (int): Request timeout in seconds (default: 30)
- `max_retries` (int): Maximum retries for transient errors (default: 3)

**Returns:** `MCPSyncClient` instance

### 2. `@with_mcp_client` Decorator

Injects MCP client into CLI commands automatically.

```python
import click
from cli.mcp_helpers import with_mcp_client

@click.command()
@click.argument('file_path')
@with_mcp_client
def validate(file_path: str, mcp_client: MCPSyncClient):
    result = mcp_client.validate_file(file_path)
    click.echo(f"Validated {file_path}")
```

**Features:**
- Automatic client creation/retrieval
- Exception handling with user-friendly messages
- Debug mode support via `--mcp-debug` flag
- Proper exit codes

### 3. `handle_mcp_error(error, debug=False)`

Converts MCP exceptions to user-friendly messages.

```python
from cli.mcp_helpers import handle_mcp_error
from svc.mcp_exceptions import MCPResourceNotFoundError

try:
    # ... MCP operation ...
    pass
except MCPError as e:
    msg = handle_mcp_error(e, debug=True)
    click.echo(f"Error: {msg}", err=True)
```

**Error Type Mapping:**
- `MCPMethodNotFoundError` → "Method not found: ..."
- `MCPInvalidParamsError` → "Invalid parameters: ..."
- `MCPResourceNotFoundError` → "Resource not found: ..."
- `MCPTimeoutError` → "Request timeout: ..."
- `MCPValidationError` → "Validation failed: ..."
- `MCPInternalError` → "Internal server error: ..."

### 4. `format_mcp_result(result, format='json', title=None)`

Formats MCP results for CLI output.

```python
from cli.mcp_helpers import format_mcp_result

result = {"files_processed": 5, "issues_found": 2}

# JSON format with syntax highlighting
formatted = format_mcp_result(result, format='json', title="Results")

# Human-readable text format
formatted = format_mcp_result(result, format='text')

# Table format for list results
formatted = format_mcp_result(result, format='table')
```

**Supported Formats:**
- `json` - Pretty-printed JSON with syntax highlighting
- `text` - Human-readable key-value pairs
- `table` - Rich table format (for list results)

### 5. `print_mcp_result(result, format='json', title=None, style=None)`

Convenience function that combines formatting and printing.

```python
from cli.mcp_helpers import print_mcp_result

result = mcp_client.get_system_status()
print_mcp_result(result, format='text', title="System Status", style='green')
```

### 6. `check_mcp_connection()`

Checks if MCP server is accessible.

```python
from cli.mcp_helpers import check_mcp_connection

if not check_mcp_connection():
    click.echo("Error: MCP server is not accessible", err=True)
    sys.exit(1)
```

**Returns:** `bool` - True if connection successful, False otherwise

### 7. `get_exit_code(error=None)`

Maps errors to standard Unix exit codes.

```python
from cli.mcp_helpers import get_exit_code

try:
    # ... operation ...
    pass
except Exception as e:
    exit_code = get_exit_code(e)
    sys.exit(exit_code)
```

**Exit Code Mapping:**
- `0` - Success
- `1` - General error / Internal error
- `2` - Invalid parameters
- `3` - Resource not found
- `4` - Timeout
- `5` - Validation failure
- `127` - Method not found

## Convenience Functions

### `validate_file_cli(file_path, family='words', validation_types=None, format='text')`

One-liner file validation with formatting.

```python
from cli.mcp_helpers import validate_file_cli

validate_file_cli("test.md", format='json')
```

### `list_validations_cli(limit=100, status=None, format='table')`

One-liner validation listing with formatting.

```python
from cli.mcp_helpers import list_validations_cli

list_validations_cli(limit=50, status='pending', format='table')
```

### `get_system_status_cli(format='text')`

One-liner system status check.

```python
from cli.mcp_helpers import get_system_status_cli

get_system_status_cli(format='text')
```

## Usage Patterns

### Pattern 1: Basic Command with Decorator

```python
import click
from cli.mcp_helpers import with_mcp_client, print_mcp_result

@click.command()
@click.argument('file_path')
@with_mcp_client
def validate(file_path: str, mcp_client):
    """Validate a file."""
    result = mcp_client.validate_file(file_path)
    print_mcp_result(result, format='text', title="Validation Results")
```

### Pattern 2: Command with Multiple MCP Calls

```python
@click.command()
@click.option('--limit', default=10)
@with_mcp_client
def list_recent(limit: int, mcp_client):
    """List recent validations."""
    # Get validations
    result = mcp_client.list_validations(limit=limit)
    print_mcp_result(result, format='table')

    # Get system status
    status = mcp_client.get_system_status()
    click.echo(f"\nSystem Status: {status['status']}")
```

### Pattern 3: Command Group with Shared Debug Flag

```python
@click.group()
@click.option('--mcp-debug', is_flag=True, help='Enable MCP debug mode')
@click.pass_context
def cli(ctx, mcp_debug):
    """CLI with MCP support."""
    ctx.ensure_object(dict)
    ctx.obj['mcp_debug'] = mcp_debug

@cli.command()
@with_mcp_client
def status(mcp_client):
    """Get system status."""
    result = mcp_client.get_system_status()
    print_mcp_result(result, format='text')
```

### Pattern 4: Manual Error Handling

```python
@click.command()
@click.argument('validation_ids', nargs=-1)
def approve(validation_ids):
    """Approve validations with custom error handling."""
    from cli.mcp_helpers import get_cli_mcp_client, handle_mcp_error
    from svc.mcp_exceptions import MCPError

    try:
        client = get_cli_mcp_client()
        result = client.approve(list(validation_ids))
        click.echo(f"Approved {result['approved_count']} validations")
    except MCPError as e:
        error_msg = handle_mcp_error(e)
        click.echo(f"Error: {error_msg}", err=True)
        sys.exit(get_exit_code(e))
```

### Pattern 5: Health Check Before Operation

```python
@click.command()
@with_mcp_client
def batch_process(mcp_client):
    """Process batch with health check."""
    from cli.mcp_helpers import check_mcp_connection

    if not check_mcp_connection():
        click.echo("Error: MCP server is not accessible", err=True)
        sys.exit(1)

    # Continue with processing
    result = mcp_client.create_workflow(...)
    print_mcp_result(result)
```

## Testing

The module includes comprehensive tests covering:

- Singleton client management
- Decorator injection and error handling
- Error message formatting
- Result formatting (JSON, text, table)
- Exit code mapping
- Convenience functions

Run tests:
```bash
pytest tests/cli/test_mcp_helpers.py -v
```

## Migration Guidelines

When migrating CLI commands to use MCP:

1. **Replace direct agent access** with MCP client calls
2. **Use `@with_mcp_client` decorator** for automatic client injection
3. **Use `print_mcp_result()`** for consistent output formatting
4. **Add `--mcp-debug` flag** to command groups for debugging
5. **Remove manual error handling** - let decorator handle it

### Before (Direct Agent Access)

```python
@click.command()
def validate(file_path: str):
    from agents.content_validator import ContentValidatorAgent

    validator = ContentValidatorAgent("validator")
    result = validator.validate_file(file_path)
    click.echo(json.dumps(result, indent=2))
```

### After (MCP Client)

```python
@click.command()
@with_mcp_client
def validate(file_path: str, mcp_client):
    result = mcp_client.validate_file(file_path)
    print_mcp_result(result, format='text', title="Validation Results")
```

## Error Handling

The decorator provides automatic error handling:

```bash
# User runs command with invalid ID
$ tbcv get-validation abc123

Error: Resource not found: Validation 'abc123' not found.
The requested validation, workflow, or file does not exist.

# With debug flag
$ tbcv --mcp-debug get-validation abc123

Error: Resource not found: Validation 'abc123' not found.
The requested validation, workflow, or file does not exist.

Debug Information:
Error Code: -32001
Error Data: {
  "validation_id": "abc123",
  "searched_in": "database"
}
```

## Output Formatting Examples

### JSON Format
```json
{
  "validation_id": "val_123",
  "file_path": "test.md",
  "status": "approved",
  "issues_found": 2
}
```

### Text Format
```
Validation Id: val_123
File Path: test.md
Status: approved
Issues Found: 2
```

### Table Format
```
┌──────────┬────────────┬──────────┬──────────────┐
│ Id       │ File Path  │ Status   │ Issues Found │
├──────────┼────────────┼──────────┼──────────────┤
│ val_123  │ test.md    │ approved │ 2            │
│ val_124  │ demo.md    │ pending  │ 5            │
└──────────┴────────────┴──────────┴──────────────┘
Total: 2
```

## Best Practices

1. **Always use the decorator** - It handles errors, debug mode, and exit codes automatically
2. **Use appropriate format** - JSON for piping, text for readability, table for lists
3. **Add --mcp-debug support** - Include in command groups for troubleshooting
4. **Check connection first** - Use `check_mcp_connection()` for long-running operations
5. **Use convenience functions** - For simple operations, use the one-liner helpers

## Related Files

- **Implementation**: `cli/mcp_helpers.py`
- **Tests**: `tests/cli/test_mcp_helpers.py`
- **Examples**: `cli/mcp_helpers_example.py`
- **MCP Client**: `svc/mcp_client.py`
- **MCP Exceptions**: `svc/mcp_exceptions.py`

## Next Steps

1. Migrate CLI commands in `cli/main.py` to use `@with_mcp_client`
2. Replace direct agent imports with MCP client calls
3. Update CLI tests to use MCP client
4. Add `--mcp-debug` flag to main CLI group
5. Document migrated commands

## Status

✅ **COMPLETE** - All utilities implemented and tested (38/38 tests passing)

- [x] `get_cli_mcp_client()` - Singleton client management
- [x] `@with_mcp_client` - Decorator with injection and error handling
- [x] `handle_mcp_error()` - User-friendly error messages
- [x] `format_mcp_result()` - Multiple output formats
- [x] `print_mcp_result()` - Convenience printing
- [x] `check_mcp_connection()` - Health check
- [x] `get_exit_code()` - Exit code mapping
- [x] Convenience functions - One-liner helpers
- [x] Comprehensive tests - 38 tests covering all functionality
- [x] Example usage - `cli/mcp_helpers_example.py`
