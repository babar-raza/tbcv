# CLI Usage

## Overview

TBCV provides a comprehensive command-line interface for content validation, enhancement, and system management. The CLI uses the Click framework with Rich console output for an enhanced user experience.

## Installation

The CLI is installed as part of the TBCV package:

```bash
pip install -r requirements.txt
python -m tbcv.cli --help
```

## Global Options

```bash
tbcv --help                    # Show help
tbcv --verbose                 # Enable verbose logging
tbcv --config config/custom.yaml  # Use custom config file
tbcv --quiet                   # Minimal output
tbcv --mcp-debug               # Enable MCP request/response debugging
```

### MCP Integration

The CLI now uses the Model Context Protocol (MCP) for all backend communication. This provides:

- Standardized request/response format
- Automatic error handling and retry logic
- Better debugging and observability
- Consistent behavior across CLI and API

When `--mcp-debug` is enabled, you'll see detailed MCP communication logs including:
- Request IDs and methods
- Request/response payloads
- Retry attempts and backoff timing
- Error details and stack traces

## Core Commands

### validate-file

Validate a single content file via MCP.

```bash
tbcv validate-file <file_path> [OPTIONS]

Options:
  --family, -f TEXT          Plugin family (words, cells, slides, pdf, email)
  --types, -t TEXT           Comma-separated validator types (yaml,markdown,links,etc)
  --output, -o TEXT          Output file for results
  --format TEXT              Output format (json, text) [default: json]

Examples:
  # Basic validation
  tbcv validate-file docs/api.md --family words

  # Validation with specific validators
  tbcv validate-file content.md --types yaml,markdown,links,seo

  # JSON output to file
  tbcv validate-file code.cs --family cells --output results.json

  # Human-readable text format
  tbcv validate-file content.md --format text

  # Debug MCP communication
  tbcv --mcp-debug validate-file docs/api.md

MCP Integration:
  Uses MCP validate_file method with automatic retry on transient errors.
  Returns validation_id for tracking and further operations.
```

### validate-directory

Validate all files in a directory matching a pattern via MCP.

```bash
tbcv validate-directory <directory_path> [OPTIONS]

Options:
  --pattern, -p TEXT         File pattern [default: *.md]
  --family, -f TEXT          Plugin family
  --workers, -w INTEGER      Number of concurrent workers [default: 4]
  --output, -o TEXT          Output file for results
  --format TEXT              Output format (json, text, summary)
  --recursive, -r            Search subdirectories

Examples:
  # Recursive validation with high concurrency
  tbcv validate-directory docs/ --recursive --workers 8

  # Validate specific file type
  tbcv validate-directory code/ --pattern "*.cs" --family cells

  # Summary output to file
  tbcv validate-directory content/ --format summary --output summary.txt

  # Debug batch processing
  tbcv --mcp-debug validate-directory docs/ --recursive

MCP Integration:
  Uses MCP validate_folder method for efficient batch processing.
  Creates workflow for tracking progress and results.
```

### check-agents

Check agent status and configuration.

```bash
tbcv check-agents [OPTIONS]

Options:
  --family, -f TEXT          Plugin family to check

Examples:
  tbcv check-agents
  tbcv check-agents --family words
```

### validate

Validate a file via workflow (enhanced validation with tiered execution).

```bash
tbcv validate <file_path> [OPTIONS]

Options:
  --type TEXT                Validation type (basic, full, enhanced)
  --profile TEXT             Validation profile from validation_flow.yaml
                             (strict, default, quick, content_only)
  --confidence FLOAT         Confidence threshold (0.0-1.0) [default: 0.6]
  --output TEXT              Output format (table, json, yaml)
  --fix                      Apply automatic fixes
  --no-cache                 Skip cache lookup
  --validators TEXT          Comma-separated list of validators to run
                             (yaml,markdown,structure,code,links,seo,FuzzyLogic,Truth,llm)

Validation Profiles:
  strict       - All validators enabled, strict error checking, LLM enabled
  default      - Standard validation, LLM disabled by default
  quick        - Only Tier 1 validators (yaml, markdown, structure)
  content_only - Content validators only, no advanced truth/LLM checks

Examples:
  tbcv validate example.md --type full
  tbcv validate code.py --confidence 0.8 --output json
  tbcv validate content.md --profile strict  # Use strict profile
  tbcv validate docs/api.md --profile quick  # Fast validation
  tbcv validate tutorial.md --validators yaml,markdown,links  # Specific validators
```

### batch

Batch process files in a directory.

```bash
tbcv batch <directory_path> [OPTIONS]

Options:
  --pattern TEXT             File pattern [default: *.md]
  --recursive, -r            Recursive directory traversal
  --workers INTEGER          Number of workers [default: 4]
  --continue-on-error        Continue on individual errors
  --report-file TEXT         Save detailed report to file
  --summary-only             Show summary only

Examples:
  tbcv batch docs/ --recursive --workers 16
  tbcv batch code/ --pattern "*.py" --report-file batch_report.json
```

### enhance

Enhance content with plugin links and information.

```bash
tbcv enhance <file_path> [OPTIONS]

Options:
  --dry-run                  Show changes without applying
  --backup                   Create backup before modification
  --plugin-links             Add plugin links [default: True]
  --info-text                Add informational text [default: True]
  --force                    Override safety checks

Examples:
  tbcv enhance content.md --dry-run
  tbcv enhance example.md --backup --plugin-links
```

### test

Create and process a test file.

```bash
tbcv test

# Creates a test markdown file and validates it
```

### status

Show system status via MCP.

```bash
tbcv status [OPTIONS]

Options:
  --format TEXT              Output format (table, json) [default: table]

Examples:
  # Display system status
  tbcv status

  # JSON format for monitoring
  tbcv status --format json

  # Debug system health check
  tbcv --mcp-debug status

MCP Integration:
  Uses MCP get_system_status method to retrieve:
  - Component health (database, cache, agents)
  - Resource usage (memory, disk)
  - Active workflows and validations
  - System uptime and performance metrics
```

## Validation Management

### validations list

List validation results with filtering.

```bash
tbcv validations list [OPTIONS]

Options:
  --status TEXT              Filter by status (pass, fail, warning, approved, rejected, enhanced)
  --severity TEXT            Filter by severity (low, medium, high, critical)
  --limit INTEGER            Max validations to show [default: 50]
  --format TEXT              Output format (table, json)

Examples:
  tbcv validations list --status fail --limit 20
  tbcv validations list --severity high --format json
```

### validations show

Show detailed validation information.

```bash
tbcv validations show <validation_id> [OPTIONS]

Options:
  --format TEXT              Output format (text, json)

Examples:
  tbcv validations show val_abc123
  tbcv validations show val_abc123 --format json
```

### validations history

Show validation history for a file.

```bash
tbcv validations history <file_path> [OPTIONS]

Options:
  --limit INTEGER            Max history entries [default: 10]
  --format TEXT              Output format (table, json)

Examples:
  tbcv validations history docs/api.md
  tbcv validations history content/guide.md --limit 20
```

### validations approve

Approve a validation result.

```bash
tbcv validations approve <validation_id> [OPTIONS]

Options:
  --notes TEXT               Approval notes

Examples:
  tbcv validations approve val_123 --notes "Reviewed and approved"
```

### validations reject

Reject a validation result.

```bash
tbcv validations reject <validation_id> [OPTIONS]

Options:
  --notes TEXT               Rejection notes

Examples:
  tbcv validations reject val_123 --notes "Requires additional work"
```

### validations revalidate

Re-validate content from a previous validation.

```bash
tbcv validations revalidate <validation_id>

Examples:
  tbcv validations revalidate val_123  # Re-run validation and compare results
```

## Workflow Management

### workflows list

List workflows with filtering.

```bash
tbcv workflows list [OPTIONS]

Options:
  --state TEXT               Filter by state (pending, running, paused, completed, failed, cancelled)
  --limit INTEGER            Max workflows to show [default: 50]
  --format TEXT              Output format (table, json)

Examples:
  tbcv workflows list --state running
  tbcv workflows list --state completed --limit 100
```

### workflows show

Show detailed workflow information.

```bash
tbcv workflows show <workflow_id> [OPTIONS]

Options:
  --format TEXT              Output format (text, json)

Examples:
  tbcv workflows show wf_abc123
  tbcv workflows show wf_abc123 --format json
```

### workflows cancel

Cancel a running workflow.

```bash
tbcv workflows cancel <workflow_id>

Examples:
  tbcv workflows cancel wf_123
```

### workflows delete

Delete one or more workflows.

```bash
tbcv workflows delete <workflow_ids>... [OPTIONS]

Options:
  --confirm                  Skip confirmation prompt

Examples:
  tbcv workflows delete wf_123
  tbcv workflows delete wf_123 wf_456 --confirm
```

## Recommendations Management

### recommendations list

List recommendations with filtering.

```bash
tbcv recommendations list [OPTIONS]

Options:
  --status TEXT              Filter by status (proposed, pending, approved, rejected, applied)
  --validation-id TEXT       Filter by validation ID
  --limit INTEGER            Max recommendations to show [default: 50]
  --format TEXT              Output format (table, json)

Examples:
  tbcv recommendations list --status pending
  tbcv recommendations list --validation-id val_123 --format json
```

### recommendations show

Show detailed information about a recommendation.

```bash
tbcv recommendations show <recommendation_id> [OPTIONS]

Options:
  --format TEXT              Output format (text, json)

Examples:
  tbcv recommendations show rec_abc123
  tbcv recommendations show rec_abc123 --format json
```

### recommendations approve

Approve one or more recommendations.

```bash
tbcv recommendations approve <recommendation_ids>... [OPTIONS]

Options:
  --reviewer TEXT            Reviewer name [default: cli_user]
  --notes TEXT               Review notes

Examples:
  tbcv recommendations approve rec_123 rec_456
  tbcv recommendations approve rec_789 --reviewer "John Doe" --notes "Approved for v2.0"
```

### recommendations reject

Reject one or more recommendations.

```bash
tbcv recommendations reject <recommendation_ids>... [OPTIONS]

Options:
  --reviewer TEXT            Reviewer name [default: cli_user]
  --notes TEXT               Review notes (reason for rejection)

Examples:
  tbcv recommendations reject rec_123 --notes "Not applicable"
```

### recommendations generate

Generate recommendations for a validation.

```bash
tbcv recommendations generate <validation_id> [OPTIONS]

Options:
  --force                    Force regeneration even if recommendations exist

Examples:
  tbcv recommendations generate val_123
  tbcv recommendations generate val_456 --force
```

### recommendations rebuild

Rebuild recommendations for a validation (delete and regenerate).

```bash
tbcv recommendations rebuild <validation_id>

Examples:
  tbcv recommendations rebuild val_123
```

### recommendations delete

Delete one or more recommendations.

```bash
tbcv recommendations delete <recommendation_ids>... [OPTIONS]

Options:
  --confirm                  Skip confirmation prompt

Examples:
  tbcv recommendations delete rec_123
  tbcv recommendations delete rec_123 rec_456 --confirm
```

### recommendations auto-apply

Auto-apply high-confidence recommendations.

```bash
tbcv recommendations auto-apply <validation_id> [OPTIONS]

Options:
  --threshold FLOAT          Confidence threshold [default: 0.95]
  --dry-run                  Show what would be applied without applying

Examples:
  tbcv recommendations auto-apply val_123 --dry-run
  tbcv recommendations auto-apply val_123 --threshold 0.90
```

### recommendations enhance

Enhance content by applying approved recommendations.

```bash
tbcv recommendations enhance <file_path> [OPTIONS]

Options:
  --validation-id TEXT       Validation ID with recommendations [required]
  --preview                  Preview changes without applying
  --backup                   Create backup [default: True]
  --output TEXT              Output file (default: overwrite original)

Examples:
  tbcv recommendations enhance content.md --validation-id val_123 --preview
  tbcv recommendations enhance example.md --validation-id val_456 --backup
```

## System Administration

### admin cache-stats

Show cache statistics.

```bash
tbcv admin cache-stats

# Displays cache performance metrics including hit rate, L1/L2 sizes
```

### admin cache-clear

Clear cache.

```bash
tbcv admin cache-clear [OPTIONS]

Options:
  --l1                       Clear L1 cache only
  --l2                       Clear L2 cache only

Examples:
  tbcv admin cache-clear          # Clear all caches
  tbcv admin cache-clear --l1     # Clear L1 only
  tbcv admin cache-clear --l2     # Clear L2 only
```

### admin agents

List all registered agents.

```bash
tbcv admin agents

# Displays agent ID, status, version, and capability count
```

### admin health

Perform system health check.

```bash
tbcv admin health [OPTIONS]

Options:
  --full                     Show full health report with agent details

Examples:
  tbcv admin health
  tbcv admin health --full
```

### admin reset

Reset system by permanently deleting data.

**DANGEROUS**: This permanently deletes data from the database. Use this to clean up before production or during development.

```bash
tbcv admin reset [OPTIONS]

Options:
  --confirm                  Skip confirmation prompt (DANGEROUS)
  --validations              Delete only validations
  --workflows                Delete only workflows
  --recommendations          Delete only recommendations
  --audit-logs               Delete audit logs (normally preserved)
  --all                      Delete everything (default if no specific options)
  --clear-cache              Clear cache after reset

Examples:
  # Reset everything (requires typing "DELETE" to confirm)
  tbcv admin reset --all

  # Reset everything with auto-confirm (DANGEROUS)
  tbcv admin reset --all --confirm

  # Delete only validations
  tbcv admin reset --validations --confirm

  # Delete workflows and recommendations, preserve validations
  tbcv admin reset --workflows --recommendations --confirm

  # Full reset including audit logs and cache
  tbcv admin reset --all --audit-logs --clear-cache --confirm

Safety Features:
  - Requires typing "DELETE" to confirm (unless --confirm flag used)
  - Selective deletion (choose what to delete)
  - Audit logs preserved by default for compliance
  - Cache clearing optional
  - Detailed summary of deleted items
```

## Advanced Commands

### probe-endpoints

Discover and probe API endpoints.

```bash
tbcv probe-endpoints [OPTIONS]

Options:
  --mode TEXT                Probe mode (offline, live) [default: offline]
  --base-url TEXT            Base URL for live mode [default: http://127.0.0.1:8080]
  --scan TEXT                Additional Python files to scan
  --include TEXT             Regex pattern to include paths
  --exclude TEXT             Regex pattern to exclude paths
  --strict                   Exit with error if any endpoint fails
  --output-dir TEXT          Output directory [default: data/reports]

Examples:
  tbcv probe-endpoints --mode offline
  tbcv probe-endpoints --mode live --base-url http://localhost:8080
  tbcv probe-endpoints --include "^/api" --strict
```

## Output Formats

### JSON Format
Structured data for programmatic processing:

```json
{
  "status": "completed",
  "validation_result": {
    "content_validation": {
      "confidence": 0.85,
      "issues": [
        {
          "level": "warning",
          "category": "link",
          "message": "Broken link detected",
          "line": 42
        }
      ]
    }
  }
}
```

### Text Format
Human-readable output:

```
File: example.md
Family: words
Status: completed
Confidence: 0.85
Issues: 2

Issues found:
  [WARNING] link: Broken link detected at line 42
  [INFO] plugin: Missing plugin reference for Document.Save()
```

### Table Format
Rich console tables for interactive use:

```
Validation Results
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━┓
┃ Category          ┃ Status     ┃ Issues ┃ Confidence  ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━┩
│ Overall           │ Completed  │ 0      │ 0.85        │
│ Plugin Detection  │ Passed     │ 0      │ 0.90        │
│ Content Validation│ Warning    │ 2      │ 0.75        │
│ Code Quality      │ Passed     │ 1      │ 0.80        │
└───────────────────┴────────────┴────────┴─────────────┘
```

## Error Handling

The CLI provides comprehensive error handling:

- **Network Errors**: Automatic retry with backoff
- **File Access**: Clear error messages for permission issues
- **Validation Failures**: Detailed issue reporting
- **Agent Unavailable**: Graceful degradation with warnings

### MCP Error Codes

The MCP integration uses standardized error codes:

| Error Code | Type | Description | Resolution |
|------------|------|-------------|------------|
| -32700 | Parse Error | Invalid JSON-RPC | Check request format |
| -32600 | Invalid Request | Missing required fields | Verify parameters |
| -32601 | Method Not Found | Unknown MCP method | Update CLI version |
| -32602 | Invalid Params | Wrong parameter types | Check command syntax |
| -32603 | Internal Error | Server error | Check logs, retry |
| -32001 | Validation Error | Validation failed | Review validation rules |
| -32002 | Not Found | Resource not found | Verify ID exists |
| -32003 | Permission Denied | Insufficient permissions | Check access rights |

### Troubleshooting MCP Errors

#### Connection Errors

```bash
# Error: Cannot connect to MCP server
# Solution: Check if server is running
tbcv status

# Enable debug mode to see connection details
tbcv --mcp-debug status
```

#### Validation Errors

```bash
# Error: MCPValidationError - Invalid file format
# Example output:
# Error: Validation failed
# Details: File must be markdown format
# Expected: .md extension
# Got: .txt

# Solution: Check file format and validator requirements
tbcv validate-file docs/file.md --types yaml,markdown
```

#### Not Found Errors

```bash
# Error: MCPNotFoundError - Validation not found
# Example output:
# Error: Validation 'val_xyz' not found
# Possible causes:
# - Validation ID is incorrect
# - Validation was deleted
# - Database connection issue

# Solution: List available validations
tbcv validations list --limit 50

# Verify validation exists
tbcv validations show val_xyz
```

#### Internal Server Errors

```bash
# Error: MCPInternalError - Database connection failed
# Example output:
# Error: Internal server error
# Message: Failed to connect to database
# Details: Connection timeout after 30s

# Solution 1: Check system health
tbcv admin health --full

# Solution 2: Enable maintenance mode and restart
tbcv admin enable-maintenance-mode --reason "Troubleshooting"
# ... restart services ...
tbcv admin disable-maintenance-mode
```

#### Retry Logic

The MCP client automatically retries transient errors with exponential backoff:

- Attempt 1: Immediate
- Attempt 2: 100ms delay
- Attempt 3: 200ms delay
- Attempt 4: 400ms delay (final)

```bash
# Example with retry debugging
tbcv --mcp-debug validate-file docs/api.md

# Output shows retry attempts:
# [DEBUG] MCP request: method=validate_file, id=1
# [WARNING] MCP request failed (attempt 1), retrying...
# [DEBUG] Retrying after 0.1s
# [DEBUG] MCP request: method=validate_file, id=1
# [DEBUG] MCP response: method=validate_file, id=1
```

#### Common Issues and Solutions

**Issue: "MCP server not responding"**
```bash
# Check if server process is running
tbcv admin health

# Check logs for errors
tail -f logs/tbcv.log

# Restart server if needed
python -m api.server
```

**Issue: "Timeout waiting for validation"**
```bash
# Increase timeout for large files
export TBCV_MCP_TIMEOUT=60
tbcv validate-file large-document.md

# Or use async workflow
tbcv validate-directory docs/ --workers 4
tbcv workflows list --state running
```

**Issue: "Cache inconsistency"**
```bash
# Clear cache and retry
tbcv admin cache-clear
tbcv validate-file docs/api.md --no-cache
```

**Issue: "Permission denied"**
```bash
# Check file permissions
ls -la docs/api.md

# Run with proper user context
sudo -u tbcv tbcv validate-file docs/api.md
```

## Performance Tuning

### Concurrent Processing
Control worker count for batch operations:

```bash
# Use all CPU cores
tbcv batch docs/ --workers 0  # Auto-detect

# Limit concurrency
tbcv validate-directory content/ --workers 2
```

### Caching
Skip cache for fresh validation:

```bash
tbcv validate content.md --no-cache
```

### Progress Tracking
Long-running operations show progress bars:

```
Batch processing directory: docs/
Pattern: *.md, Workers: 8
Processing files...
├── 00:00:15 [████████████░░░░░░░░] 45% • 45/100 files
```

## Integration Examples

### CI/CD Pipeline
```yaml
# .github/workflows/validate.yml
name: Content Validation
on: [push, pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt
      - run: python -m tbcv.cli validate-directory docs/ --format json --output validation.json
```

### Pre-commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit
python -m tbcv.cli validate-file $1
if [ $? -ne 0 ]; then
    echo "Content validation failed"
    exit 1
fi
```

### Docker Usage
```bash
# Run CLI in container
docker run --rm -v $(pwd):/app tbcv:latest \
  python -m tbcv.cli validate-directory /app/docs --recursive
```

## MCP Integration Details

### Architecture

The CLI uses MCP (Model Context Protocol) for all backend communication:

```
┌─────────────┐          ┌──────────────┐          ┌──────────────┐
│   CLI       │          │  MCP Client  │          │  MCP Server  │
│  Commands   │──────────│  (Sync/Async)│──────────│  (Backend)   │
└─────────────┘  invoke  └──────────────┘  JSON-RPC └──────────────┘
                                                           │
                                                           ├─ Validators
                                                           ├─ Workflows
                                                           ├─ Cache
                                                           └─ Database
```

### MCP Client Features

**Synchronous Client** (`MCPSyncClient`):
- Used by CLI commands
- Blocking I/O for simple command execution
- Automatic retry with exponential backoff
- Thread-safe singleton instance

**Asynchronous Client** (`MCPAsyncClient`):
- Used by API endpoints
- Non-blocking I/O for concurrent requests
- Same interface as sync client
- Event loop integration

### Request/Response Format

All MCP communication uses JSON-RPC 2.0:

**Request Example:**
```json
{
  "jsonrpc": "2.0",
  "method": "validate_file",
  "params": {
    "file_path": "/path/to/file.md",
    "family": "words",
    "validation_types": ["yaml", "markdown"]
  },
  "id": 1
}
```

**Success Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "validation_id": "val_abc123",
    "status": "completed",
    "issues_count": 2,
    "confidence": 0.85
  },
  "id": 1
}
```

**Error Response:**
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32001,
    "message": "Validation failed",
    "data": {
      "details": "File format not supported",
      "supported_formats": [".md", ".markdown"]
    }
  },
  "id": 1
}
```

### Debugging with --mcp-debug

Enable detailed MCP logging:

```bash
# Basic debug output
tbcv --mcp-debug validate-file docs/api.md

# Sample output:
# [DEBUG] MCP request: method=validate_file, id=1
# [DEBUG]   params={'file_path': '/path/to/docs/api.md', 'family': 'words'}
# [DEBUG] MCP response: method=validate_file, id=1, duration=1.23s
# [DEBUG]   result={'validation_id': 'val_123', 'success': true}

# Debug with verbose logging
tbcv --verbose --mcp-debug validate-file docs/api.md

# Full request/response payloads
export TBCV_MCP_DEBUG=full
tbcv validate-file docs/api.md
```

### Performance Optimization

**Connection Pooling:**
- MCP client uses singleton pattern
- Connection reused across commands
- No overhead for multiple operations

**Retry Strategy:**
```python
# Default retry configuration
timeout = 30  # seconds
max_retries = 3
backoff = [0.1, 0.2, 0.4]  # exponential

# Customize via environment
export TBCV_MCP_TIMEOUT=60
export TBCV_MCP_MAX_RETRIES=5
```

**Batch Operations:**
```bash
# Use workflows for large batches
tbcv validate-directory docs/ --workers 8
# Creates workflow, tracks progress, handles failures

# Use bulk operations when available
tbcv validations approve val_1 val_2 val_3
# Single MCP call, efficient batch processing
```

### Best Practices

1. **Use appropriate output formats:**
   ```bash
   # JSON for scripting
   tbcv validate-file doc.md --format json | jq '.validation_id'

   # Text for humans
   tbcv validate-file doc.md --format text

   # Table for lists
   tbcv validations list --format table
   ```

2. **Handle errors gracefully:**
   ```bash
   # Check exit codes
   if tbcv validate-file doc.md; then
     echo "Validation passed"
   else
     echo "Validation failed: $?"
   fi

   # Capture output
   result=$(tbcv validate-file doc.md --format json)
   validation_id=$(echo "$result" | jq -r '.validation_id')
   ```

3. **Use workflows for long operations:**
   ```bash
   # Start workflow
   tbcv validate-directory docs/ --recursive > workflow.json
   workflow_id=$(cat workflow.json | jq -r '.workflow_id')

   # Monitor progress
   watch -n 5 "tbcv workflows show $workflow_id"

   # Get final report
   tbcv workflows show $workflow_id --format json
   ```

4. **Enable caching for repeated operations:**
   ```bash
   # First run (slow)
   tbcv validate-file doc.md

   # Second run (fast, from cache)
   tbcv validate-file doc.md

   # Force fresh validation
   tbcv validate-file doc.md --no-cache
   ```

5. **Use --mcp-debug for troubleshooting:**
   ```bash
   # Debug single command
   tbcv --mcp-debug validate-file doc.md 2>&1 | tee debug.log

   # Debug with timestamps
   tbcv --mcp-debug validate-file doc.md 2>&1 | ts

   # Debug and analyze
   tbcv --mcp-debug validate-file doc.md 2>&1 | grep "MCP request"
   ```

### Environment Variables

Configure MCP behavior via environment variables:

```bash
# MCP client configuration
export TBCV_MCP_TIMEOUT=30        # Request timeout (seconds)
export TBCV_MCP_MAX_RETRIES=3     # Maximum retry attempts
export TBCV_MCP_DEBUG=true        # Enable debug logging

# Server configuration
export TBCV_MCP_SERVER_HOST=localhost
export TBCV_MCP_SERVER_PORT=8080

# Feature flags
export TBCV_MCP_ENABLE_CACHE=true
export TBCV_MCP_ENABLE_COMPRESSION=false
```

### Migration from Direct Agent Calls

Old (direct agent calls):
```bash
# This approach is deprecated
python -c "from agents.validator import validate; validate('file.md')"
```

New (via MCP):
```bash
# Use CLI with MCP integration
tbcv validate-file file.md

# Or use MCP client in Python
from svc.mcp_client import get_mcp_sync_client
client = get_mcp_sync_client()
result = client.validate_file('file.md')
```

Benefits of MCP approach:
- Standardized error handling
- Automatic retry logic
- Better logging and debugging
- Consistent behavior across CLI and API
- Support for async operations
- Future-proof architecture