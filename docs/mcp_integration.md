# MCP (Model Context Protocol) Integration

## Overview

TBCV includes an MCP (Model Context Protocol) server that provides a JSON-RPC interface for validation operations. This enables external tools and integrations to interact with TBCV programmatically.

**Location**: `svc/mcp_server.py`

## What is MCP?

MCP (Model Context Protocol) is a JSON-RPC based protocol for communication between AI models and external systems. TBCV's MCP server allows external applications to:

- Validate markdown files in folders
- Approve/reject validation results
- Apply enhancements to approved content

## MCP Server Architecture

```
┌─────────────────────────────────────────────────┐
│                External Client                   │
│  (Claude, LLM Tool, Custom Integration)          │
└────────────────────────┬────────────────────────┘
                         │ JSON-RPC
                         ↓
┌─────────────────────────────────────────────────┐
│               MCPStdioServer                     │
│  - Reads JSON-RPC from stdin                    │
│  - Writes responses to stdout                    │
└────────────────────────┬────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────┐
│                  MCPServer                       │
│  - handle_request()                             │
│  - _validate_folder()                           │
│  - _approve()                                   │
│  - _reject()                                    │
│  - _enhance()                                   │
└────────────────────────┬────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────┐
│              Core TBCV Components                │
│  - DatabaseManager                              │
│  - RuleManager                                  │
│  - MarkdownIngestion                            │
│  - OllamaClient (for enhancements)              │
└─────────────────────────────────────────────────┘
```

## Available Methods

### 1. `validate_folder`

Validate all markdown files in a folder.

**Parameters:**
- `folder_path` (string, required): Path to folder containing markdown files
- `recursive` (boolean, optional): Whether to search recursively (default: true)

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "validate_folder",
  "params": {
    "folder_path": "/path/to/content",
    "recursive": true
  },
  "id": 1
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "message": "Validated 15 files",
    "results": {
      "files_processed": 15,
      "files_passed": 12,
      "files_failed": 3,
      "validations": [...]
    }
  },
  "id": 1
}
```

### 2. `validate_file`

Validate a single markdown file.

**Parameters:**
- `file_path` (string, required): Path to the file to validate
- `family` (string, optional): Plugin family (default: "words")
- `validation_types` (array, optional): List of specific validators to run

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "validate_file",
  "params": {
    "file_path": "/path/to/document.md",
    "family": "words",
    "validation_types": ["markdown", "seo", "links"]
  },
  "id": 2
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "validation_id": "val_abc123",
    "status": "pass",
    "issues": [],
    "file_path": "/path/to/document.md"
  },
  "id": 2
}
```

**Errors:**
- `ValueError`: File not found or invalid parameters

### 3. `validate_content`

Validate markdown content without requiring a physical file.

**Parameters:**
- `content` (string, required): Markdown content to validate
- `file_path` (string, optional): Virtual file path for context (default: "temp.md")
- `validation_types` (array, optional): List of validators to run

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "validate_content",
  "params": {
    "content": "# Title\n\nContent here.",
    "file_path": "virtual/document.md"
  },
  "id": 3
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "validation_id": "val_xyz789",
    "status": "pass",
    "issues": [
      {
        "type": "warning",
        "message": "Missing meta description",
        "line": 1
      }
    ]
  },
  "id": 3
}
```

### 4. `get_validation`

Retrieve a validation record by ID.

**Parameters:**
- `validation_id` (string, required): ID of validation to retrieve

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "get_validation",
  "params": {
    "validation_id": "val_abc123"
  },
  "id": 4
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "validation": {
      "id": "val_abc123",
      "file_path": "/path/to/document.md",
      "status": "approved",
      "severity": "info",
      "rules_applied": ["markdown", "seo"],
      "validation_results": {...},
      "notes": "Validated via MCP",
      "created_at": "2025-12-01T10:00:00Z",
      "updated_at": "2025-12-01T10:05:00Z"
    }
  },
  "id": 4
}
```

**Errors:**
- `ValueError`: Validation not found

### 5. `list_validations`

List validation records with optional filtering and pagination.

**Parameters:**
- `limit` (integer, optional): Maximum results to return (default: 100)
- `offset` (integer, optional): Number of results to skip (default: 0)
- `status` (string, optional): Filter by status (pass/fail/warning/approved/rejected/enhanced)
- `file_path` (string, optional): Filter by file path

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "list_validations",
  "params": {
    "limit": 10,
    "offset": 0,
    "status": "pass"
  },
  "id": 5
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "validations": [
      {
        "id": "val_1",
        "file_path": "/path/to/doc1.md",
        "status": "pass",
        "created_at": "2025-12-01T10:00:00Z"
      },
      {
        "id": "val_2",
        "file_path": "/path/to/doc2.md",
        "status": "pass",
        "created_at": "2025-12-01T10:01:00Z"
      }
    ],
    "total": 42
  },
  "id": 5
}
```

### 6. `update_validation`

Update validation metadata (notes, status).

**Parameters:**
- `validation_id` (string, required): ID of validation to update
- `notes` (string, optional): New notes for the validation
- `status` (string, optional): New status (pass/fail/warning/approved/rejected)

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "update_validation",
  "params": {
    "validation_id": "val_abc123",
    "notes": "Fixed issues",
    "status": "approved"
  },
  "id": 6
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "validation_id": "val_abc123"
  },
  "id": 6
}
```

**Errors:**
- `ValueError`: Validation not found or invalid status

### 7. `delete_validation`

Delete a validation record from the database.

**Parameters:**
- `validation_id` (string, required): ID of validation to delete

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "delete_validation",
  "params": {
    "validation_id": "val_abc123"
  },
  "id": 7
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "validation_id": "val_abc123"
  },
  "id": 7
}
```

### 8. `revalidate`

Re-run validation on the same file with the same settings.

**Parameters:**
- `validation_id` (string, required): ID of original validation

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "revalidate",
  "params": {
    "validation_id": "val_abc123"
  },
  "id": 8
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "new_validation_id": "val_new456",
    "original_validation_id": "val_abc123"
  },
  "id": 8
}
```

**Errors:**
- `ValueError`: Original validation not found

### 9. `approve`

Approve validation records by their IDs.

**Parameters:**
- `ids` (array, required): List of validation IDs to approve

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "approve",
  "params": {
    "ids": ["val-123", "val-456", "val-789"]
  },
  "id": 2
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "approved_count": 3,
    "errors": []
  },
  "id": 2
}
```

### 3. `reject`

Reject validation records by their IDs.

**Parameters:**
- `ids` (array, required): List of validation IDs to reject

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "reject",
  "params": {
    "ids": ["val-101", "val-102"]
  },
  "id": 3
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "rejected_count": 2,
    "errors": []
  },
  "id": 3
}
```

### 4. `enhance`

Enhance approved validation records using LLM (requires Ollama).

**Parameters:**
- `ids` (array, required): List of approved validation IDs to enhance

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "enhance",
  "params": {
    "ids": ["val-123"]
  },
  "id": 4
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "enhanced_count": 1,
    "errors": [],
    "enhancements": [
      {
        "validation_id": "val-123",
        "action": "enhance",
        "timestamp": "2024-01-15T10:30:00Z",
        "original_size": 1500,
        "enhanced_size": 1650,
        "model_used": "llama2:7b"
      }
    ]
  },
  "id": 4
}
```

## Admin & Maintenance Methods

### 5. `get_system_status`

Get comprehensive system health status.

**Parameters:** None

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "get_system_status",
  "params": {},
  "id": 5
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "status": "healthy",
    "components": {
      "database": {
        "status": "healthy",
        "details": {
          "connected": true,
          "validation_count": 150
        }
      },
      "cache": {
        "status": "healthy",
        "details": {
          "l1": {"enabled": true, "size": 42, "hit_rate": 0.85},
          "l2": {"enabled": true, "total_entries": 320}
        }
      },
      "agents": {
        "status": "healthy",
        "details": {
          "agent_count": 5,
          "agents": ["validator", "enhancer", "critic", "truth_manager", "recommendation"]
        }
      }
    },
    "resources": {
      "cpu_percent": 15.2,
      "memory_percent": 42.8,
      "disk_percent": 68.5
    },
    "maintenance_mode": false
  },
  "id": 5
}
```

### 6. `clear_cache`

Clear all caches or specific cache types.

**Parameters:**
- `cache_types` (array, optional): Specific cache types to clear (default: all)

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "clear_cache",
  "params": {
    "cache_types": ["validation", "rules"]
  },
  "id": 6
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "cleared_items": 150,
    "cache_types_cleared": ["validation", "rules"]
  },
  "id": 6
}
```

### 7. `get_cache_stats`

Get cache statistics.

**Parameters:** None

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "get_cache_stats",
  "params": {},
  "id": 7
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "total_items": 362,
    "total_size_bytes": 2458624,
    "hit_rate": 0.85,
    "by_type": {
      "l1": {
        "enabled": true,
        "size": 42,
        "max_size": 1000,
        "hits": 850,
        "misses": 150,
        "hit_rate": 0.85
      },
      "l2": {
        "enabled": true,
        "total_entries": 320,
        "total_size_bytes": 2458624,
        "total_size_mb": 2.34
      }
    }
  },
  "id": 7
}
```

### 8. `cleanup_cache`

Clean up stale cache entries older than specified age.

**Parameters:**
- `max_age_hours` (integer, optional): Maximum age in hours (default: 24)

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "cleanup_cache",
  "params": {
    "max_age_hours": 48
  },
  "id": 8
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "cleaned_items": 25
  },
  "id": 8
}
```

### 9. `rebuild_cache`

Rebuild cache from scratch.

**Parameters:** None

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "rebuild_cache",
  "params": {},
  "id": 9
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "rebuilt_items": 0
  },
  "id": 9
}
```

### 10. `reload_agent`

Reload a specific agent.

**Parameters:**
- `agent_id` (string, required): Agent ID to reload

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "reload_agent",
  "params": {
    "agent_id": "content_validator"
  },
  "id": 10
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "agent_id": "content_validator",
    "reloaded_at": "2025-12-01T14:30:00Z"
  },
  "id": 10
}
```

### 11. `run_gc`

Run garbage collection.

**Parameters:** None

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "run_gc",
  "params": {},
  "id": 11
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "collected_objects": 542,
    "generation": 2,
    "stats": [
      {"collections": 120, "collected": 1024, "uncollectable": 0},
      {"collections": 10, "collected": 256, "uncollectable": 0},
      {"collections": 3, "collected": 542, "uncollectable": 0}
    ]
  },
  "id": 11
}
```

### 12. `enable_maintenance_mode`

Enable system maintenance mode.

**Parameters:**
- `reason` (string, optional): Reason for maintenance
- `enabled_by` (string, optional): User/system enabling maintenance (default: "system")

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "enable_maintenance_mode",
  "params": {
    "reason": "System upgrade",
    "enabled_by": "admin"
  },
  "id": 12
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "enabled_at": "2025-12-01T14:30:00Z"
  },
  "id": 12
}
```

### 13. `disable_maintenance_mode`

Disable system maintenance mode.

**Parameters:** None

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "disable_maintenance_mode",
  "params": {},
  "id": 13
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "disabled_at": "2025-12-01T14:45:00Z"
  },
  "id": 13
}
```

### 14. `create_checkpoint`

Create a system checkpoint for backup/recovery.

**Parameters:**
- `name` (string, optional): Checkpoint name
- `metadata` (object, optional): Additional metadata

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "create_checkpoint",
  "params": {
    "name": "before_migration",
    "metadata": {
      "reason": "Pre-migration backup",
      "version": "1.0.0"
    }
  },
  "id": 14
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "checkpoint_id": "20251201_143000_before_migration",
    "created_at": "2025-12-01T14:30:00Z"
  },
  "id": 14
}
```

## Usage Modes

### 1. Stdio Mode (MCPStdioServer)

Run the MCP server as a subprocess that communicates via stdin/stdout:

```bash
# Start the MCP server in stdio mode
python -m svc.mcp_server
```

The server reads JSON-RPC requests line-by-line from stdin and writes responses to stdout.

**Example interaction:**
```bash
# Send request (one line)
echo '{"jsonrpc":"2.0","method":"validate_folder","params":{"folder_path":"./content"},"id":1}' | python -m svc.mcp_server
```

### 2. In-Process Mode (MCPServer)

Use the MCP server directly from Python code:

```python
from svc.mcp_server import MCPServer

# Create server instance
server = MCPServer()

# Build request
request = {
    "jsonrpc": "2.0",
    "method": "validate_folder",
    "params": {
        "folder_path": "./content",
        "recursive": True
    },
    "id": 1
}

# Handle request
response = server.handle_request(request)
print(response)
```

### 3. Using create_mcp_client()

Helper function for in-process usage:

```python
from svc.mcp_server import create_mcp_client

# Create client (returns MCPServer instance)
client = create_mcp_client()

# Use directly
response = client.handle_request({
    "jsonrpc": "2.0",
    "method": "approve",
    "params": {"ids": ["val-123"]},
    "id": 1
})
```

## Error Handling

### JSON-RPC Error Codes

| Code | Message | Description |
|------|---------|-------------|
| -32700 | Parse error | Invalid JSON received |
| -32601 | Method not found | Unknown method name |
| -32603 | Internal error | Server-side error during execution |

### Error Response Format

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32601,
    "message": "Method not found: invalid_method"
  },
  "id": 1
}
```

### Common Errors

**Validation not found:**
```json
{
  "result": {
    "success": true,
    "approved_count": 0,
    "errors": ["Validation val-999 not found"]
  }
}
```

**Not approved for enhancement:**
```json
{
  "result": {
    "success": true,
    "enhanced_count": 0,
    "errors": ["Validation val-123 not approved (status: pending)"]
  }
}
```

**File not found:**
```json
{
  "result": {
    "success": true,
    "enhanced_count": 0,
    "errors": ["File not found: /path/to/missing.md"]
  }
}
```

## Integration Examples

### Example 1: Claude Desktop Integration

Configure Claude Desktop to use TBCV MCP server:

```json
{
  "mcpServers": {
    "tbcv": {
      "command": "python",
      "args": ["-m", "svc.mcp_server"],
      "cwd": "/path/to/tbcv"
    }
  }
}
```

### Example 2: Custom Python Integration

```python
import subprocess
import json

def call_mcp_server(method: str, params: dict) -> dict:
    """Call TBCV MCP server and return response."""
    request = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }

    # Start MCP server process
    proc = subprocess.Popen(
        ["python", "-m", "svc.mcp_server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        cwd="/path/to/tbcv"
    )

    # Send request
    proc.stdin.write(json.dumps(request).encode() + b"\n")
    proc.stdin.flush()

    # Read response
    response_line = proc.stdout.readline()
    return json.loads(response_line)

# Usage
result = call_mcp_server("validate_folder", {"folder_path": "./content"})
print(f"Validated {result['result']['results']['files_processed']} files")
```

### Example 3: Batch Workflow

```python
from svc.mcp_server import create_mcp_client

client = create_mcp_client()

# Step 1: Validate folder
validate_response = client.handle_request({
    "jsonrpc": "2.0",
    "method": "validate_folder",
    "params": {"folder_path": "./content"},
    "id": 1
})

# Step 2: Get validation IDs that passed
validation_ids = [
    v["id"] for v in validate_response["result"]["results"]["validations"]
    if v["status"] == "pending"
]

# Step 3: Approve passing validations
if validation_ids:
    approve_response = client.handle_request({
        "jsonrpc": "2.0",
        "method": "approve",
        "params": {"ids": validation_ids},
        "id": 2
    })
    print(f"Approved {approve_response['result']['approved_count']} validations")

# Step 4: Enhance approved content (requires Ollama)
if validation_ids:
    enhance_response = client.handle_request({
        "jsonrpc": "2.0",
        "method": "enhance",
        "params": {"ids": validation_ids},
        "id": 3
    })
    print(f"Enhanced {enhance_response['result']['enhanced_count']} files")
```

## Configuration

The MCP server uses TBCV's standard configuration:

```yaml
# config/main.yaml

# Database settings (used by MCP server)
database:
  url: "sqlite:///./data/tbcv.db"

# LLM settings (used for enhance method)
llm_validator:
  enabled: true
  provider: ollama
  model: llama2:7b
```

### Environment Variables

```bash
# Ollama configuration for enhancements
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_MODEL=llama2:7b
```

## Security Considerations

### Path Validation

The MCP server validates all file paths to prevent:
- Path traversal attacks
- Access to files outside allowed directories
- Writing to restricted locations

```python
# Internal path validation
if not is_safe_path(file_path):
    errors.append(f"Unsafe file path: {file_path}")
    continue
```

### Write Permissions

Before enhancing files, the server validates write permissions:

```python
if not validate_write_path(file_path):
    errors.append(f"Cannot write to file: {file_path}")
    continue
```

## Limitations

1. **Single-threaded**: The stdio server processes one request at a time
2. **No authentication**: The MCP server doesn't implement authentication (rely on process-level security)
3. **LLM required for enhance**: The `enhance` method requires Ollama to be running
4. **SQLite only**: Uses SQLite database (no PostgreSQL support in MCP mode)

## Troubleshooting

### Server not responding

```bash
# Check if server starts
python -m svc.mcp_server

# If import errors, ensure PYTHONPATH is set
export PYTHONPATH=/path/to/tbcv:$PYTHONPATH
```

### Ollama errors during enhance

```bash
# Ensure Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if needed
ollama serve

# Pull required model
ollama pull llama2:7b
```

### Database errors

```bash
# Initialize database if needed
python -c "from core.database import DatabaseManager; DatabaseManager().init_database()"
```

## Related Documentation

- [Architecture](architecture.md) - System architecture overview
- [API Reference](api_reference.md) - REST API documentation
- [CLI Usage](cli_usage.md) - Command-line interface
- [Workflows](workflows.md) - Validation workflows
