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

Approve one or more validation records. Supports both single ID (string) and multiple IDs (array).

**Parameters:**
- `ids` (string or array, required): Single validation ID or list of IDs to approve

**Request Example (Single ID):**
```json
{
  "jsonrpc": "2.0",
  "method": "approve",
  "params": {
    "ids": "val-123"
  },
  "id": 1
}
```

**Request Example (Multiple IDs):**
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
    "failed_count": 0,
    "errors": []
  },
  "id": 2
}
```

**Errors:**
- Returns partial success with error details if some IDs are not found
- `failed_count` indicates number of IDs that could not be approved
- `errors` array contains specific error messages for failed IDs

### 10. `reject`

Reject one or more validation records with optional reason. Supports both single ID (string) and multiple IDs (array).

**Parameters:**
- `ids` (string or array, required): Single validation ID or list of IDs to reject
- `reason` (string, optional): Rejection reason (appended to validation notes)

**Request Example (Single):**
```json
{
  "jsonrpc": "2.0",
  "method": "reject",
  "params": {
    "ids": "val-101",
    "reason": "Content needs revision"
  },
  "id": 1
}
```

**Request Example (Multiple):**
```json
{
  "jsonrpc": "2.0",
  "method": "reject",
  "params": {
    "ids": ["val-101", "val-102"],
    "reason": "Batch rejection for quality review"
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
    "failed_count": 0,
    "errors": []
  },
  "id": 3
}
```

### 11. `bulk_approve`

Efficiently approve large batches of validation records. Optimized for bulk operations with configurable batch processing and performance tracking.

**Parameters:**
- `ids` (array, required): List of validation IDs to approve
- `batch_size` (integer, optional): Processing batch size for transaction management (default: 100)

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "bulk_approve",
  "params": {
    "ids": ["val-1", "val-2", "val-3", "...val-150"],
    "batch_size": 50
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
    "total": 150,
    "approved_count": 148,
    "failed_count": 2,
    "errors": [
      "Validation val-x not found",
      "Validation val-y not found"
    ],
    "processing_time_ms": 42.5
  },
  "id": 4
}
```

**Performance:**
- Optimized for batches up to 1000 validations
- Processes in configurable batch sizes to avoid transaction timeouts
- Target performance: <100ms for 100 validations
- Returns processing time for performance monitoring

**Use Cases:**
- Approving all validations in a workflow
- Batch approval after manual review
- Automated approval of passing validations

### 12. `bulk_reject`

Efficiently reject large batches of validation records with optional reason. Optimized for bulk operations.

**Parameters:**
- `ids` (array, required): List of validation IDs to reject
- `reason` (string, optional): Rejection reason applied to all validations
- `batch_size` (integer, optional): Processing batch size (default: 100)

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "bulk_reject",
  "params": {
    "ids": ["val-1", "val-2", "val-3", "...val-100"],
    "reason": "Outdated content - requires update",
    "batch_size": 50
  },
  "id": 5
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "total": 100,
    "rejected_count": 100,
    "failed_count": 0,
    "errors": [],
    "processing_time_ms": 38.2
  },
  "id": 5
}
```

**Performance:**
- Same optimizations as `bulk_approve`
- Efficiently appends reason to validation notes
- Target performance: <100ms for 100 validations

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

### Example 4: Bulk Approval Workflow

```python
from svc.mcp_client import MCPSyncClient

client = MCPSyncClient()

# Step 1: Validate folder
result = client.validate_folder("./content")
print(f"Validated {result['results']['files_processed']} files")

# Step 2: Get all validation IDs
validations = client.list_validations(limit=1000, status="pending")
validation_ids = [v["id"] for v in validations["validations"]]

print(f"Found {len(validation_ids)} pending validations")

# Step 3: Bulk approve efficiently
if len(validation_ids) > 10:
    # Use bulk_approve for better performance with large batches
    bulk_result = client.bulk_approve(
        validation_ids,
        batch_size=100  # Process in batches of 100
    )
    print(f"Bulk approved {bulk_result['approved_count']}/{bulk_result['total']} validations")
    print(f"Processing time: {bulk_result['processing_time_ms']:.2f}ms")

    if bulk_result['errors']:
        print(f"Errors: {bulk_result['errors']}")
else:
    # Use regular approve for small batches
    result = client.approve(validation_ids)
    print(f"Approved {result['approved_count']} validations")
```

### Example 5: Bulk Rejection with Reason

```python
from svc.mcp_client import MCPSyncClient

client = MCPSyncClient()

# Get validations that failed specific checks
validations = client.list_validations(limit=1000)
failed_seo_ids = [
    v["id"] for v in validations["validations"]
    if "seo" in str(v.get("validation_results", {}))
]

if failed_seo_ids:
    # Bulk reject with reason
    result = client.bulk_reject(
        failed_seo_ids,
        reason="Failed SEO validation - requires meta description and keywords",
        batch_size=50
    )

    print(f"Rejected {result['rejected_count']} validations")
    print(f"Processing time: {result['processing_time_ms']:.2f}ms")

    # Check if within performance target
    if result['rejected_count'] == 100:
        if result['processing_time_ms'] < 100:
            print("Performance target met: <100ms for 100 validations")
        else:
            print(f"Performance warning: {result['processing_time_ms']:.2f}ms for 100 validations")
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

## Workflow Methods

The MCP server supports comprehensive workflow management for orchestrating complex validation and enhancement operations.

### 15. `create_workflow`

Create and start a new workflow for background execution.

**Parameters:**
- `workflow_type` (string, required): Type of workflow (`validate_directory`, `batch_enhance`, `full_audit`, `recommendation_batch`)
- `params` (object, required): Workflow-specific parameters
- `name` (string, optional): Workflow name for display
- `description` (string, optional): Workflow description

**Workflow Types:**
- `validate_directory`: Validate all files in a directory
- `batch_enhance`: Enhance multiple validations
- `full_audit`: Complete validation and enhancement audit
- `recommendation_batch`: Process batch of recommendations

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "create_workflow",
  "params": {
    "workflow_type": "validate_directory",
    "params": {
      "directory_path": "/content",
      "recursive": true
    },
    "name": "Validate Content Directory",
    "description": "Full validation of content directory"
  },
  "id": 15
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "workflow_id": "wf-abc123",
    "workflow_type": "validate_directory",
    "status": "running",
    "created_at": "2025-12-01T12:00:00Z"
  },
  "id": 15
}
```

**Errors:**
- `ValueError`: Invalid workflow type or parameters

### 16. `get_workflow`

Retrieve complete workflow details by ID.

**Parameters:**
- `workflow_id` (string, required): ID of workflow to retrieve

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "get_workflow",
  "params": {
    "workflow_id": "wf-abc123"
  },
  "id": 16
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "workflow": {
      "id": "wf-abc123",
      "workflow_type": "validate_directory",
      "name": "Validate Content Directory",
      "description": "Full validation of content directory",
      "status": "running",
      "params": {
        "directory_path": "/content",
        "recursive": true
      },
      "progress": 45,
      "error_message": null,
      "created_at": "2025-12-01T12:00:00Z",
      "started_at": "2025-12-01T12:00:01Z",
      "completed_at": null,
      "updated_at": "2025-12-01T12:00:30Z",
      "total_steps": 100,
      "current_step": 45
    }
  },
  "id": 16
}
```

**Errors:**
- `ValueError`: Workflow not found

### 17. `list_workflows`

List workflows with filtering and pagination.

**Parameters:**
- `limit` (integer, optional): Maximum results (default: 100)
- `offset` (integer, optional): Results to skip (default: 0)
- `status` (string, optional): Filter by status (pending/running/paused/completed/failed/cancelled)
- `workflow_type` (string, optional): Filter by workflow type
- `created_after` (string, optional): Filter by creation date (ISO 8601)
- `created_before` (string, optional): Filter by creation date (ISO 8601)

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "list_workflows",
  "params": {
    "limit": 50,
    "offset": 0,
    "status": "running",
    "workflow_type": "validate_directory"
  },
  "id": 17
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "workflows": [
      {
        "id": "wf-1",
        "workflow_type": "validate_directory",
        "status": "running",
        "progress": 45,
        "created_at": "2025-12-01T12:00:00Z"
      },
      {
        "id": "wf-2",
        "workflow_type": "batch_enhance",
        "status": "running",
        "progress": 75,
        "created_at": "2025-12-01T11:30:00Z"
      }
    ],
    "total": 2,
    "limit": 50,
    "offset": 0
  },
  "id": 17
}
```

### 18. `control_workflow`

Control workflow execution (pause/resume/cancel).

**Parameters:**
- `workflow_id` (string, required): ID of workflow to control
- `action` (string, required): Control action (`pause`, `resume`, or `cancel`)

**Request (Pause):**
```json
{
  "jsonrpc": "2.0",
  "method": "control_workflow",
  "params": {
    "workflow_id": "wf-abc123",
    "action": "pause"
  },
  "id": 18
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "workflow_id": "wf-abc123",
    "action": "pause",
    "new_status": "paused"
  },
  "id": 18
}
```

**Actions:**
- `pause`: Pause a running workflow (can be resumed)
- `resume`: Resume a paused workflow
- `cancel`: Cancel workflow and mark as cancelled (cannot be resumed)

**Errors:**
- `ValueError`: Invalid action or workflow cannot be controlled in current state

### 19. `get_workflow_report`

Generate detailed workflow report with metrics and statistics.

**Parameters:**
- `workflow_id` (string, required): ID of workflow
- `include_details` (boolean, optional): Include detailed metrics (default: true)

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "get_workflow_report",
  "params": {
    "workflow_id": "wf-abc123",
    "include_details": true
  },
  "id": 19
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "workflow_id": "wf-abc123",
    "report": {
      "workflow_id": "wf-abc123",
      "workflow_type": "validate_directory",
      "state": "completed",
      "created_at": "2025-12-01T12:00:00Z",
      "completed_at": "2025-12-01T12:05:00Z",
      "total_steps": 100,
      "current_step": 100,
      "progress_percent": 100,
      "error_message": null,
      "metrics": {
        "duration_seconds": 300.5,
        "files_processed": 100,
        "files_total": 100,
        "errors_count": 0
      },
      "metadata": {
        "name": "Validate Content Directory",
        "description": "Full validation of content directory"
      }
    }
  },
  "id": 19
}
```

### 20. `get_workflow_summary`

Get workflow summary for dashboards (lightweight version of report).

**Parameters:**
- `workflow_id` (string, required): ID of workflow

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "get_workflow_summary",
  "params": {
    "workflow_id": "wf-abc123"
  },
  "id": 20
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "workflow_id": "wf-abc123",
    "status": "running",
    "progress_percent": 45,
    "files_processed": 45,
    "files_total": 100,
    "errors_count": 0,
    "duration_seconds": 120.5,
    "eta_seconds": 147.2
  },
  "id": 20
}
```

**Fields:**
- `progress_percent`: Progress percentage (0-100)
- `files_processed`: Number of items processed
- `files_total`: Total number of items
- `errors_count`: Number of errors encountered
- `duration_seconds`: Time elapsed since workflow started
- `eta_seconds`: Estimated time remaining (only for running workflows)

### 21. `delete_workflow`

Delete a workflow record from the database.

**Parameters:**
- `workflow_id` (string, required): ID of workflow to delete
- `force` (boolean, optional): Allow deleting running workflows (default: false)

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "delete_workflow",
  "params": {
    "workflow_id": "wf-abc123",
    "force": false
  },
  "id": 21
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "workflow_id": "wf-abc123"
  },
  "id": 21
}
```

**Errors:**
- `ValueError`: Cannot delete running workflow without force=true

### 22. `bulk_delete_workflows`

Bulk delete workflows with filtering options.

**Parameters:**
- `workflow_ids` (array, optional): Specific workflow IDs to delete
- `status` (string, optional): Delete all workflows with this status
- `workflow_type` (string, optional): Delete all workflows of this type
- `created_before` (string, optional): Delete workflows created before this date (ISO 8601)
- `force` (boolean, optional): Allow deleting running workflows (default: false)

**Request (Delete by Status):**
```json
{
  "jsonrpc": "2.0",
  "method": "bulk_delete_workflows",
  "params": {
    "status": "completed",
    "created_before": "2025-11-01T00:00:00Z",
    "force": false
  },
  "id": 22
}
```

**Request (Delete Specific IDs):**
```json
{
  "jsonrpc": "2.0",
  "method": "bulk_delete_workflows",
  "params": {
    "workflow_ids": ["wf-1", "wf-2", "wf-3"],
    "force": true
  },
  "id": 23
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "deleted_count": 15,
    "errors": [
      {
        "workflow_id": "wf-999",
        "error": "Workflow not found"
      }
    ]
  },
  "id": 22
}
```

### Example: Complete Workflow Lifecycle

```python
from svc.mcp_client import get_mcp_sync_client
import time

client = get_mcp_sync_client()

# Step 1: Create workflow
create_result = client.create_workflow(
    workflow_type="validate_directory",
    workflow_params={
        "directory_path": "/content",
        "recursive": True
    },
    name="Monthly Content Audit"
)
workflow_id = create_result["workflow_id"]
print(f"Created workflow: {workflow_id}")

# Step 2: Monitor progress
while True:
    summary = client.get_workflow_summary(workflow_id)
    print(f"Progress: {summary['progress_percent']}% "
          f"({summary['files_processed']}/{summary['files_total']})")

    if summary["status"] in ["completed", "failed", "cancelled"]:
        break

    time.sleep(5)

# Step 3: Get detailed report
report = client.get_workflow_report(workflow_id, include_details=True)
print(f"Workflow completed in {report['report']['metrics']['duration_seconds']}s")
print(f"Processed {report['report']['metrics']['files_processed']} files")

# Step 4: Clean up
client.delete_workflow(workflow_id)
```

### Example: Workflow Control

```python
from svc.mcp_client import get_mcp_sync_client

client = get_mcp_sync_client()

# Create long-running workflow
result = client.create_workflow(
    workflow_type="full_audit",
    workflow_params={"directory_path": "/large-content-dir", "recursive": True}
)
workflow_id = result["workflow_id"]

# Pause for maintenance window
client.control_workflow(workflow_id, "pause")
print("Workflow paused for maintenance")

# ... perform maintenance ...

# Resume workflow
client.control_workflow(workflow_id, "resume")
print("Workflow resumed")

# Or cancel if needed
# client.control_workflow(workflow_id, "cancel")
```

## Query & Analytics Methods

### `get_stats`

Get comprehensive system statistics.

**Parameters:** None

**Request:**
```json
{"jsonrpc": "2.0", "method": "get_stats", "params": {}, "id": 24}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "validations_total": 1250,
    "validations_by_status": {
      "pass": 800,
      "fail": 200,
      "warning": 200,
      "approved": 50
    },
    "recommendations_total": 3500,
    "workflows_total": 45,
    "workflows_by_status": {
      "pending": 5,
      "running": 2,
      "completed": 35,
      "failed": 3
    },
    "cache_stats": {
      "total_items": 150,
      "total_size_bytes": 2048576,
      "hit_rate": 0.85
    },
    "agents_count": 12
  },
  "id": 24
}
```

### `get_audit_log`

Get audit log entries with filtering and pagination.

**Parameters:**
- `limit` (integer, optional): Maximum entries to return (default: 100)
- `offset` (integer, optional): Pagination offset (default: 0)
- `operation` (string, optional): Filter by operation name
- `user` (string, optional): Filter by user
- `status` (string, optional): Filter by status (success/failure)
- `start_date` (string, optional): Filter by start date (ISO 8601)
- `end_date` (string, optional): Filter by end date (ISO 8601)

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "get_audit_log",
  "params": {
    "limit": 50,
    "offset": 0,
    "operation": "validate_file",
    "status": "success"
  },
  "id": 25
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "logs": [
      {
        "timestamp": "2025-12-01T14:30:00Z",
        "operation": "validate_file",
        "user": "system",
        "status": "success",
        "details": {"file_path": "/test.md"}
      }
    ],
    "total": 125
  },
  "id": 25
}
```

### `get_performance_report`

Get performance metrics for operations.

**Parameters:**
- `time_range` (string, optional): Time range - "1h", "24h", "7d", "30d" (default: "24h")
- `operation` (string, optional): Filter by specific operation

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "get_performance_report",
  "params": {
    "time_range": "24h"
  },
  "id": 26
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "time_range": "24h",
    "total_operations": 5420,
    "failed_operations": 12,
    "success_rate": 0.9978,
    "operations": {
      "validate_file": {
        "count": 3200,
        "avg_duration_ms": 45.2,
        "min_duration_ms": 12.1,
        "max_duration_ms": 234.5,
        "p50_duration_ms": 42.0,
        "p95_duration_ms": 89.3,
        "p99_duration_ms": 156.8
      }
    }
  },
  "id": 26
}
```

### `get_health_report`

Get detailed system health report with recommendations.

**Parameters:** None

**Request:**
```json
{"jsonrpc": "2.0", "method": "get_health_report", "params": {}, "id": 27}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "overall_health": "healthy",
    "components": {
      "database": {"status": "healthy", "details": {}},
      "cache": {"status": "healthy", "details": {}},
      "agents": {"status": "healthy", "details": {}}
    },
    "recent_errors": [],
    "performance_summary": {
      "time_range": "1h",
      "total_operations": 450,
      "failed_operations": 2,
      "success_rate": 0.9956
    },
    "recommendations": []
  },
  "id": 27
}
```

### `get_validation_history`

Get validation history for a specific file.

**Parameters:**
- `file_path` (string, required): Path to file
- `limit` (integer, optional): Maximum history entries (default: 50)

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "get_validation_history",
  "params": {
    "file_path": "/content/guide.md",
    "limit": 20
  },
  "id": 28
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "file_path": "/content/guide.md",
    "validations": [
      {
        "id": "val-123",
        "status": "pass",
        "severity": "info",
        "created_at": "2025-12-01T14:00:00Z",
        "validation_results": {}
      }
    ],
    "total": 15
  },
  "id": 28
}
```

### `get_available_validators`

Get list of available validators.

**Parameters:**
- `validator_type` (string, optional): Filter by validator type

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "get_available_validators",
  "params": {},
  "id": 29
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "validators": [
      {
        "id": "markdown_validator",
        "type": "markdown",
        "name": "Markdown Validator",
        "description": "Validates markdown syntax and structure",
        "status": "active"
      }
    ],
    "total": 12
  },
  "id": 29
}
```

### `export_validation`

Export validation results to JSON.

**Parameters:**
- `validation_id` (string, required): ID of validation to export
- `include_recommendations` (boolean, optional): Include recommendations (default: false)

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "export_validation",
  "params": {
    "validation_id": "val-123",
    "include_recommendations": true
  },
  "id": 30
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "export_data": "{\"schema_version\":\"1.0\",\"exported_at\":\"2025-12-01T14:30:00Z\",\"data\":{...}}",
    "metadata": {
      "exported_at": "2025-12-01T14:30:00Z",
      "schema_version": "1.0",
      "filters": {"validation_id": "val-123"}
    }
  },
  "id": 30
}
```

### `export_recommendations`

Export recommendations to JSON.

**Parameters:**
- `validation_id` (string, required): ID of validation

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "export_recommendations",
  "params": {
    "validation_id": "val-123"
  },
  "id": 31
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "export_data": "{\"schema_version\":\"1.0\",\"exported_at\":\"2025-12-01T14:30:00Z\",\"data\":{...}}",
    "metadata": {
      "exported_at": "2025-12-01T14:30:00Z",
      "schema_version": "1.0",
      "filters": {"validation_id": "val-123"}
    }
  },
  "id": 31
}
```

### `export_workflow`

Export workflow report to JSON.

**Parameters:**
- `workflow_id` (string, required): ID of workflow to export
- `include_validations` (boolean, optional): Include validations (default: false)

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "export_workflow",
  "params": {
    "workflow_id": "wf-456",
    "include_validations": true
  },
  "id": 32
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "export_data": "{\"schema_version\":\"1.0\",\"exported_at\":\"2025-12-01T14:30:00Z\",\"data\":{...}}",
    "metadata": {
      "exported_at": "2025-12-01T14:30:00Z",
      "schema_version": "1.0",
      "filters": {"workflow_id": "wf-456"}
    }
  },
  "id": 32
}
```

### Example: Query and Export Workflow

```python
from svc.mcp_client import get_mcp_sync_client
import json

client = get_mcp_sync_client()

# Get system statistics
stats = client.get_stats()
print(f"Total validations: {stats['validations_total']}")
print(f"Total recommendations: {stats['recommendations_total']}")

# Check system health
health = client.get_health_report()
print(f"System status: {health['overall_health']}")
for recommendation in health['recommendations']:
    print(f"  - {recommendation}")

# Get performance metrics
perf = client.get_performance_report(time_range="24h")
print(f"Operations in last 24h: {perf['total_operations']}")
print(f"Success rate: {perf['success_rate']:.2%}")

# Export validation with recommendations
validation_id = "val-123"
export_result = client.export_validation(
    validation_id=validation_id,
    include_recommendations=True
)

# Save export to file
export_data = json.loads(export_result["export_data"])
with open(f"validation_{validation_id}.json", "w") as f:
    json.dump(export_data, f, indent=2)

print(f"Exported validation {validation_id} with schema version {export_data['schema_version']}")
```

### Example: Audit and Performance Analysis

```python
from svc.mcp_client import get_mcp_sync_client
from datetime import datetime, timedelta

client = get_mcp_sync_client()

# Get audit logs for the last hour
end_date = datetime.now().isoformat()
start_date = (datetime.now() - timedelta(hours=1)).isoformat()

audit_logs = client.get_audit_log(
    limit=100,
    start_date=start_date,
    end_date=end_date,
    status="failure"
)

print(f"Found {audit_logs['total']} failed operations in the last hour:")
for log in audit_logs['logs']:
    print(f"  - {log['timestamp']}: {log['operation']} - {log['details']}")

# Get performance metrics for specific operation
perf_report = client.get_performance_report(
    time_range="24h",
    operation="validate_file"
)

if "validate_file" in perf_report["operations"]:
    metrics = perf_report["operations"]["validate_file"]
    print(f"\nValidate file performance:")
    print(f"  Count: {metrics['count']}")
    print(f"  Average: {metrics['avg_duration_ms']:.2f}ms")
    print(f"  P95: {metrics['p95_duration_ms']:.2f}ms")
    print(f"  P99: {metrics['p99_duration_ms']:.2f}ms")

# Get validation history for trending
history = client.get_validation_history(
    file_path="/important/guide.md",
    limit=50
)

print(f"\nValidation history for guide.md:")
print(f"  Total validations: {history['total']}")
for validation in history['validations'][:5]:  # Show last 5
    print(f"  - {validation['created_at']}: {validation['status']}")
```

## Related Documentation

- [Architecture](architecture.md) - System architecture overview
- [API Reference](api_reference.md) - REST API documentation
- [CLI Usage](cli_usage.md) - Command-line interface
- [Workflows](workflows.md) - Validation workflows
