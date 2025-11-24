# TBCV API Reference

Complete REST API documentation for TBCV validation and enhancement system.

## Base URL

```
http://localhost:8080
```

## API Documentation

- **Interactive Docs**: http://localhost:8080/docs (Swagger UI)
- **Alternative Docs**: http://localhost:8080/redoc (ReDoc)
- **API Version**: 2.0.0

### Additional API Documentation

- **[Admin API Reference](./admin_api.md)** - Administrative endpoints for system management, cache control, and monitoring
- **[Checkpoint System](./checkpoints.md)** - State management and disaster recovery

## Starting the Server

```bash
# Using Uvicorn (recommended)
uvicorn tbcv.api.server:app --host 0.0.0.0 --port 8080

# With reload for development
uvicorn tbcv.api.server:app --reload --host 0.0.0.0 --port 8080

# Multiple workers for production
uvicorn tbcv.api.server:app --workers 4 --host 0.0.0.0 --port 8080

# With Gunicorn (production)
gunicorn tbcv.api.server:app -w 4 -k uvicorn.workers.UvicornWorker
```

## Health Check Endpoints

### GET /health

Comprehensive health check with full system status.

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-19T16:48:00.000Z",
  "agents_registered": 8,
  "database_connected": true,
  "schema_present": true,
  "version": "2.0.0"
}
```

**Status Codes**:
- `200`: System healthy
- `503`: System unhealthy (database or agents unavailable)

### GET /health/live

Kubernetes liveness probe - checks if application is running.

**Response**:
```json
{
  "status": "alive",
  "timestamp": "2025-11-19T16:48:00.000Z"
}
```

**Status Codes**:
- `200`: Application is alive

### GET /health/ready

Kubernetes readiness probe - checks database connection and agent registration.

**Response**:
```json
{
  "status": "ready",
  "timestamp": "2025-11-19T16:48:00.000Z",
  "checks": {
    "database": true,
    "schema": true,
    "agents": true
  }
}
```

**Status Codes**:
- `200`: Application ready to receive traffic
- `503`: Not ready (database or agents not available)

## Agent Management

### GET /agents

List all registered agents with their capabilities.

**Response**:
```json
{
  "agents": [
    {
      "agent_id": "orchestrator",
      "agent_type": "OrchestratorAgent",
      "status": "active",
      "contract": {
        "name": "Orchestrator",
        "version": "1.0",
        "capabilities": ["execute_workflow", "coordinate_agents"]
      }
    },
    {
      "agent_id": "truth_manager",
      "agent_type": "TruthManagerAgent",
      "status": "active",
      "contract": {
        "name": "TruthManager",
        "version": "1.0",
        "capabilities": ["load_truth_data", "get_plugin_info"]
      }
    }
  ],
  "total_count": 8
}
```

**Status Codes**:
- `200`: Success

### GET /agents/{agent_id}

Get detailed information about a specific agent.

**Path Parameters**:
- `agent_id`: Agent identifier (e.g., "truth_manager", "fuzzy_detector")

**Response**:
```json
{
  "agent_id": "content_validator",
  "agent_type": "ContentValidatorAgent",
  "contract": {
    "name": "ContentValidator",
    "version": "1.0",
    "capabilities": [
      "validate_content",
      "validate_yaml",
      "validate_markdown",
      "validate_code",
      "validate_links"
    ]
  },
  "status": "active"
}
```

**Status Codes**:
- `200`: Success
- `404`: Agent not found

### GET /registry/agents

Get complete agent registry state including internal metadata.

**Response**: Similar to `/agents` but with additional registry metadata.

### POST /agents/validate

Validate content using specific agent directly (advanced usage).

**Request**:
```json
{
  "agent_id": "content_validator",
  "method": "validate_content",
  "params": {
    "content": "Sample content",
    "validation_types": ["yaml", "markdown"]
  }
}
```

## Content Validation

### POST /api/validate

Validate content directly (inline validation).

**Request**:
```json
{
  "content": "---\ntitle: Tutorial\n---\n# Document Title\n\nContent here.",
  "file_path": "tutorial.md",
  "family": "words",
  "validation_types": ["yaml", "markdown", "code", "links", "truth"]
}
```

**Request Fields**:
- `content` (required): Content to validate
- `file_path` (required): File path for context
- `family` (optional): Plugin family (words, cells, slides, pdf)
- `validation_types` (optional): List of validation types (default: all)

**Response**:
```json
{
  "validation_id": "val-abc123",
  "file_path": "tutorial.md",
  "status": "fail",
  "confidence": 0.75,
  "issues": [
    {
      "level": "error",
      "category": "yaml",
      "message": "Missing required field 'title'",
      "line": 1,
      "suggestion": "Add 'title: Your Title' to frontmatter"
    },
    {
      "level": "warning",
      "category": "truth",
      "message": "Plugin 'AutoSave' used but not declared",
      "line": 15,
      "suggestion": "Add 'AutoSave' to plugins list"
    }
  ],
  "plugins_detected": 3,
  "plugins_declared": 2,
  "recommendations_generated": 5
}
```

**Status Codes**:
- `200`: Validation completed
- `400`: Invalid request (missing required fields)
- `422`: Validation error (Pydantic)
- `500`: Internal server error

### POST /api/validate/batch

Start batch validation workflow for multiple files.

**Request**:
```json
{
  "files": ["doc1.md", "doc2.md", "doc3.md"],
  "family": "words",
  "validation_types": ["yaml", "markdown", "truth"],
  "max_workers": 4
}
```

**Request Fields**:
- `files` (required): List of file paths
- `family` (optional): Plugin family
- `validation_types` (optional): Types of validation
- `max_workers` (optional): Concurrent workers (default: 4)

**Response**:
```json
{
  "job_id": "job-xyz789",
  "workflow_id": "wf-abc123",
  "status": "started",
  "files_total": 3,
  "files_validated": 0,
  "files_failed": 0
}
```

**Status Codes**:
- `202`: Batch job started
- `400`: Invalid request

### POST /workflows/validate-directory

Start directory validation workflow (recursive file scanning).

**Request**:
```json
{
  "directory_path": "./content",
  "file_pattern": "*.md",
  "workflow_type": "validate_file",
  "max_workers": 8,
  "family": "words",
  "recursive": true
}
```

**Request Fields**:
- `directory_path` (required): Directory to scan
- `file_pattern` (optional): File pattern (default: "*.md")
- `workflow_type` (optional): Workflow type (default: "validate_file")
- `max_workers` (optional): Concurrent workers (default: 4)
- `family` (optional): Plugin family
- `recursive` (optional): Scan subdirectories (default: true)

**Response**:
```json
{
  "job_id": "job-123",
  "workflow_id": "wf-456",
  "status": "started",
  "directory_path": "./content",
  "files_total": 45
}
```

**Status Codes**:
- `202`: Directory validation started
- `400`: Invalid directory path
- `404`: Directory not found

### POST /api/detect-plugins

Detect plugins in content without full validation.

**Request**:
```json
{
  "content": "Enable AutoSave and Track Changes features.",
  "family": "words"
}
```

**Response**:
```json
{
  "plugins_detected": [
    {
      "plugin_name": "AutoSave",
      "confidence": 0.95,
      "method": "fuzzy_detection"
    },
    {
      "plugin_name": "Track Changes",
      "confidence": 0.88,
      "method": "pattern_match"
    }
  ],
  "total_count": 2
}
```

**Status Codes**:
- `200`: Detection completed
- `400`: Invalid request

## Validation Results

### GET /api/validations

List validation results with filtering and pagination.

**Query Parameters**:
- `file_path`: Filter by file path (partial match)
- `severity`: Filter by severity (error, warning, info)
- `status`: Filter by status (completed, failed, pending)
- `workflow_id`: Filter by workflow ID
- `family`: Filter by plugin family
- `limit`: Max results (default: 100, max: 500)
- `offset`: Pagination offset (default: 0)

**Example**:
```bash
GET /api/validations?status=completed&severity=error&limit=50
```

**Response**:
```json
{
  "results": [
    {
      "id": "val-123",
      "file_path": "tutorial.md",
      "status": "completed",
      "family": "words",
      "created_at": "2025-11-19T16:48:00.000Z",
      "validation_results": {
        "content_validation": {
          "confidence": 0.85,
          "issues_count": 3
        },
        "fuzzy_detection": {
          "plugins_detected": 5
        }
      },
      "recommendations_count": 7
    }
  ],
  "total": 1,
  "limit": 100,
  "offset": 0
}
```

**Status Codes**:
- `200`: Success
- `400`: Invalid query parameters

### GET /api/validations/{validation_id}

Get detailed validation result with all issues and recommendations.

**Path Parameters**:
- `validation_id`: Validation identifier

**Response**:
```json
{
  "validation": {
    "id": "val-123",
    "file_path": "tutorial.md",
    "family": "words",
    "status": "completed",
    "created_at": "2025-11-19T16:48:00.000Z",
    "validation_results": {
      "content_validation": {
        "confidence": 0.85,
        "issues": [
          {
            "level": "error",
            "category": "yaml",
            "message": "Invalid YAML frontmatter",
            "line": 1
          }
        ]
      },
      "fuzzy_detection": {
        "plugins_detected": [
          {
            "name": "AutoSave",
            "confidence": 0.95
          }
        ]
      },
      "llm_validation": {
        "confidence": 0.78,
        "semantic_issues": []
      }
    }
  },
  "recommendations": [
    {
      "id": "rec-456",
      "status": "proposed",
      "severity": "medium",
      "type": "plugin_link",
      "instruction": "Add hyperlink for AutoSave plugin",
      "confidence": 0.9,
      "created_at": "2025-11-19T16:48:00.000Z"
    }
  ]
}
```

**Status Codes**:
- `200`: Success
- `404`: Validation not found

### POST /api/validations/import

Import validation results from external source.

**Request**:
```json
{
  "file_path": "imported.md",
  "validation_results": {
    "content_validation": {...}
  },
  "metadata": {
    "source": "external_tool",
    "version": "1.0"
  }
}
```

**Status Codes**:
- `201`: Validation imported
- `400`: Invalid data

### POST /api/validations/{validation_id}/approve

Approve a validation result (legacy, use recommendations API instead).

### POST /api/validations/{validation_id}/reject

Reject a validation result (legacy).

## Recommendations Management

### GET /api/recommendations

List recommendations with filtering and pagination.

**Query Parameters**:
- `validation_id`: Filter by validation ID
- `status`: Filter by status (proposed, pending, approved, rejected, applied)
- `type`: Filter by recommendation type
- `severity`: Filter by severity (low, medium, high)
- `limit`: Max results (default: 100, max: 500)
- `offset`: Pagination offset

**Example**:
```bash
GET /api/recommendations?status=proposed&validation_id=val-123
```

**Response**:
```json
{
  "recommendations": [
    {
      "id": "rec-456",
      "validation_id": "val-123",
      "status": "proposed",
      "type": "plugin_link",
      "severity": "medium",
      "instruction": "Add plugin hyperlink",
      "rationale": "First mention of AutoSave plugin should be hyperlinked",
      "confidence": 0.9,
      "created_at": "2025-11-19T16:48:00.000Z"
    }
  ],
  "total": 1,
  "limit": 100,
  "offset": 0
}
```

**Status Codes**:
- `200`: Success
- `400`: Invalid query parameters

### GET /api/recommendations/{recommendation_id}

Get recommendation details with full audit trail.

**Path Parameters**:
- `recommendation_id`: Recommendation identifier

**Response**:
```json
{
  "recommendation": {
    "id": "rec-456",
    "validation_id": "val-123",
    "status": "approved",
    "type": "plugin_link",
    "severity": "medium",
    "instruction": "Add hyperlink for AutoSave plugin at line 15",
    "rationale": "First mention should be hyperlinked per style guide",
    "confidence": 0.9,
    "created_at": "2025-11-19T16:48:00.000Z",
    "reviewed_at": "2025-11-19T17:00:00.000Z",
    "reviewer": "admin@example.com",
    "review_notes": "Approved for consistency"
  },
  "audit_trail": [
    {
      "timestamp": "2025-11-19T16:48:00.000Z",
      "action": "created",
      "user": "system"
    },
    {
      "timestamp": "2025-11-19T17:00:00.000Z",
      "action": "approved",
      "user": "admin@example.com",
      "notes": "Approved for consistency"
    }
  ]
}
```

**Status Codes**:
- `200`: Success
- `404`: Recommendation not found

### POST /api/recommendations/{recommendation_id}/review

Review a recommendation (approve or reject).

**Path Parameters**:
- `recommendation_id`: Recommendation identifier

**Request**:
```json
{
  "status": "accepted",
  "reviewer": "admin@example.com",
  "notes": "Approved for v2.0 release"
}
```

**Request Fields**:
- `status` (required): "accepted" or "rejected"
- `reviewer` (optional): Reviewer identifier
- `notes` (optional): Review notes

**Response**:
```json
{
  "success": true,
  "recommendation_id": "rec-456",
  "status": "approved",
  "reviewed_at": "2025-11-19T17:00:00.000Z"
}
```

**Status Codes**:
- `200`: Review recorded
- `404`: Recommendation not found
- `400`: Invalid status

### POST /api/recommendations/bulk-review

Bulk approve or reject multiple recommendations.

**Request**:
```json
{
  "recommendation_ids": ["rec-123", "rec-456", "rec-789"],
  "action": "accepted",
  "reviewer": "admin@example.com",
  "notes": "Bulk approval for release"
}
```

**Request Fields**:
- `recommendation_ids` (required): List of recommendation IDs
- `action` (required): "accepted" or "rejected"
- `reviewer` (optional): Reviewer identifier
- `notes` (optional): Review notes

**Response**:
```json
{
  "success": true,
  "processed": 3,
  "accepted": 3,
  "rejected": 0,
  "results": [
    {
      "recommendation_id": "rec-123",
      "status": "approved"
    },
    {
      "recommendation_id": "rec-456",
      "status": "approved"
    },
    {
      "recommendation_id": "rec-789",
      "status": "approved"
    }
  ]
}
```

**Status Codes**:
- `200`: Bulk review completed
- `400`: Invalid request

### POST /api/validations/{validation_id}/recommendations/generate

Generate new recommendations for existing validation.

**Path Parameters**:
- `validation_id`: Validation identifier

**Request**:
```json
{
  "regenerate": false,
  "types": ["plugin_link", "info_text"]
}
```

**Response**:
```json
{
  "success": true,
  "recommendations_generated": 5,
  "validation_id": "val-123"
}
```

**Status Codes**:
- `200`: Recommendations generated
- `404`: Validation not found

## Content Enhancement

### GET /api/validations/{validation_id}/enhancement-comparison

Get comprehensive enhancement comparison data for side-by-side viewing.

**Description**: Returns detailed before/after comparison including original and enhanced content, line-by-line diff with change markers, statistics, and applied recommendations.

**Parameters**:
- `validation_id`: Validation result identifier (path parameter)

**Response**:
```json
{
  "success": true,
  "validation_id": "uuid",
  "file_path": "path/to/file.md",
  "original_content": "# Original Content\n...",
  "enhanced_content": "# Enhanced Content\n...",
  "diff_lines": [
    {
      "line_number_original": 5,
      "line_number_enhanced": 5,
      "content": "line text",
      "change_type": "modified",
      "recommendation_ids": ["rec1"]
    }
  ],
  "stats": {
    "original_length": 1000,
    "enhanced_length": 1200,
    "lines_added": 15,
    "lines_removed": 5,
    "lines_modified": 10,
    "recommendations_applied": 3,
    "recommendations_total": 5,
    "enhancement_timestamp": "2025-01-23T10:30:00"
  },
  "applied_recommendations": [
    {
      "id": "rec1",
      "title": "Fix plugin name",
      "instruction": "Replace 'Apose' with 'Aspose'",
      "confidence": 0.95,
      "status": "applied"
    }
  ],
  "unified_diff": "--- original\n+++ enhanced\n@@ -1,3 +1,3 @@\n...",
  "status": "success"
}
```

**Change Types**:
- `unchanged`: Line is the same in both versions
- `added`: Line was added in enhanced version
- `removed`: Line was removed from original
- `modified`: Line was changed

**Status Values**:
- `success`: Comparison generated successfully
- `not_enhanced`: Validation has not been enhanced yet
- `error`: Error occurred during comparison generation

**Status Codes**:
- `200`: Comparison data returned successfully
- `404`: Validation not found
- `500`: Server error generating comparison

**Example Usage**:
```javascript
const response = await fetch(
  `/api/validations/${validationId}/enhancement-comparison`
);
const comparison = await response.json();

// Display statistics
console.log(`Lines added: ${comparison.stats.lines_added}`);
console.log(`Lines removed: ${comparison.stats.lines_removed}`);

// Render side-by-side diff
comparison.diff_lines.forEach(line => {
  renderDiffLine(line.content, line.change_type);
});
```

### POST /api/enhance

Apply approved recommendations to content.

**Request**:
```json
{
  "validation_id": "val-123",
  "content": "Original content...",
  "file_path": "tutorial.md",
  "recommendations": ["rec-456", "rec-789"],
  "preview": false
}
```

**Request Fields**:
- `validation_id` (required): Validation identifier
- `content` (required): Original content
- `file_path` (required): File path
- `recommendations` (optional): Specific recommendation IDs (default: all approved)
- `preview` (optional): Preview mode without persisting (default: false)

**Response**:
```json
{
  "success": true,
  "message": "Applied 2 recommendations, skipped 0",
  "enhanced_content": "Enhanced content with plugin links...",
  "diff": "--- original\n+++ enhanced\n@@ -15,7 +15,7 @@\n- Enable AutoSave feature\n+ Enable [AutoSave](https://example.com/autosave) feature",
  "applied_count": 2,
  "skipped_count": 0,
  "results": [
    {
      "recommendation_id": "rec-456",
      "status": "applied",
      "reason": null
    },
    {
      "recommendation_id": "rec-789",
      "status": "applied",
      "reason": null
    }
  ]
}
```

**Status Codes**:
- `200`: Enhancement completed
- `400`: Invalid request
- `404`: Validation or recommendations not found

### POST /api/enhance/{validation_id}

Convenience endpoint for enhancing by validation ID only.

**Path Parameters**:
- `validation_id`: Validation identifier

**Request**:
```json
{
  "content": "Original content...",
  "preview": true
}
```

**Status Codes**:
- `200`: Enhancement completed
- `404`: Validation not found

### POST /api/enhance/auto-apply

Automatically apply high-confidence recommendations.

**Request**:
```json
{
  "validation_id": "val-123",
  "content": "Original content...",
  "confidence_threshold": 0.9,
  "max_recommendations": 10
}
```

**Request Fields**:
- `validation_id` (required): Validation identifier
- `content` (required): Original content
- `confidence_threshold` (optional): Minimum confidence (default: 0.9)
- `max_recommendations` (optional): Max recs to apply (default: unlimited)

**Response**:
```json
{
  "success": true,
  "enhanced_content": "...",
  "applied_count": 5,
  "skipped_count": 2,
  "diff": "..."
}
```

**Status Codes**:
- `200`: Auto-apply completed
- `400`: Invalid request

## Workflow Management

### GET /workflows

List workflows with filtering.

**Query Parameters**:
- `state`: Filter by state (pending, running, paused, completed, failed, cancelled)
- `type`: Filter by workflow type (validate_file, validate_directory, etc.)
- `limit`: Max results (default: 50, max: 200)
- `offset`: Pagination offset

**Example**:
```bash
GET /workflows?state=running&limit=10
```

**Response**:
```json
{
  "workflows": [
    {
      "workflow_id": "wf-abc123",
      "type": "validate_directory",
      "state": "running",
      "started_at": "2025-11-19T16:00:00.000Z",
      "progress_percent": 60,
      "current_step": 27,
      "total_steps": 45,
      "metadata": {
        "directory_path": "./content",
        "files_validated": 27,
        "files_failed": 0
      }
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

**Status Codes**:
- `200`: Success
- `400`: Invalid query parameters

### GET /workflows/{workflow_id}

Get detailed workflow information.

**Path Parameters**:
- `workflow_id`: Workflow identifier

**Response**:
```json
{
  "workflow_id": "wf-abc123",
  "type": "validate_directory",
  "state": "completed",
  "started_at": "2025-11-19T16:00:00.000Z",
  "completed_at": "2025-11-19T16:05:30.000Z",
  "duration_seconds": 330,
  "progress_percent": 100,
  "metadata": {
    "directory_path": "./content",
    "files_total": 45,
    "files_validated": 43,
    "files_failed": 2,
    "errors": [
      "file1.md: FileNotFoundError",
      "file2.md: ValidationTimeout"
    ]
  },
  "checkpoints": [
    {
      "name": "workflow_start",
      "timestamp": "2025-11-19T16:00:00.000Z"
    },
    {
      "name": "detection_start",
      "timestamp": "2025-11-19T16:00:05.000Z"
    },
    {
      "name": "workflow_complete",
      "timestamp": "2025-11-19T16:05:30.000Z"
    }
  ]
}
```

**Status Codes**:
- `200`: Success
- `404`: Workflow not found

### POST /workflows/{workflow_id}/control

Control workflow execution (pause, resume, cancel).

**Path Parameters**:
- `workflow_id`: Workflow identifier

**Request**:
```json
{
  "action": "pause"
}
```

**Request Fields**:
- `action` (required): "pause", "resume", or "cancel"

**Response**:
```json
{
  "success": true,
  "workflow_id": "wf-abc123",
  "state": "paused",
  "message": "Workflow paused successfully"
}
```

**Status Codes**:
- `200`: Action executed
- `404`: Workflow not found
- `400`: Invalid action or state transition

### DELETE /workflows/{workflow_id}

Delete a workflow and its associated data.

**Path Parameters**:
- `workflow_id`: Workflow identifier

**Response**:
```json
{
  "success": true,
  "workflow_id": "wf-abc123",
  "message": "Workflow deleted"
}
```

**Status Codes**:
- `200`: Workflow deleted
- `404`: Workflow not found

### POST /workflows/cancel-batch

Cancel multiple workflows at once.

**Request**:
```json
{
  "workflow_ids": ["wf-123", "wf-456", "wf-789"]
}
```

**Response**:
```json
{
  "success": true,
  "cancelled": 3,
  "results": [
    {
      "workflow_id": "wf-123",
      "status": "cancelled"
    },
    {
      "workflow_id": "wf-456",
      "status": "cancelled"
    },
    {
      "workflow_id": "wf-789",
      "status": "cancelled"
    }
  ]
}
```

**Status Codes**:
- `200`: Batch cancellation completed
- `400`: Invalid request

### GET /api/workflows

Alternative endpoint for listing workflows (same as GET /workflows).

### POST /api/workflows/bulk-delete

Bulk delete workflows.

**Request**:
```json
{
  "workflow_ids": ["wf-123", "wf-456"],
  "force": false
}
```

**Status Codes**:
- `200`: Bulk deletion completed
- `400`: Invalid request

## Real-Time Updates

### WebSocket: /ws/{workflow_id}

Real-time updates for specific workflow progress.

**Connection**:
```javascript
const ws = new WebSocket('ws://localhost:8080/ws/wf-abc123');

ws.onopen = () => {
  console.log('Connected to workflow updates');
};

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log(`Progress: ${update.progress_percent}%`);
  console.log(`Status: ${update.state}`);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Connection closed');
};
```

**Message Format**:
```json
{
  "type": "workflow_update",
  "workflow_id": "wf-abc123",
  "state": "running",
  "progress_percent": 65,
  "current_step": 29,
  "total_steps": 45,
  "timestamp": "2025-11-19T16:02:30.000Z"
}
```

### WebSocket: /ws/validation_updates

Global validation event stream for all validations.

**Message Types**:
- `validation_started`
- `validation_completed`
- `recommendation_generated`
- `workflow_state_changed`

### GET /api/stream/updates

Server-Sent Events (SSE) for live updates.

**Query Parameters**:
- `topic` (optional): Filter by topic (validation, workflow, recommendation)

**Connection**:
```javascript
const eventSource = new EventSource('http://localhost:8080/api/stream/updates?topic=workflow');

eventSource.addEventListener('message', (event) => {
  const data = JSON.parse(event.data);
  console.log('Update:', data);
});

eventSource.addEventListener('error', (event) => {
  console.error('SSE error:', event);
});
```

**Event Format**:
```
data: {"type":"workflow_update","workflow_id":"wf-123","state":"running"}

data: {"type":"validation_completed","validation_id":"val-456"}
```

## Admin Endpoints

### GET /admin/status

Comprehensive system status and metrics.

**Response**:
```json
{
  "status": "healthy",
  "uptime_seconds": 3600,
  "agents": {
    "registered": 8,
    "active": 8,
    "busy": 1
  },
  "database": {
    "connected": true,
    "tables": 6,
    "validations_count": 1234,
    "recommendations_count": 5678
  },
  "cache": {
    "l1_size": "128MB",
    "l2_size": "512MB",
    "hit_rate": 0.85
  },
  "workflows": {
    "active": 3,
    "pending": 5,
    "completed_today": 42
  }
}
```

**Status Codes**:
- `200`: Success

### GET /admin/workflows/active

Get all currently active workflows.

**Response**:
```json
{
  "active_workflows": [
    {
      "workflow_id": "wf-123",
      "type": "validate_directory",
      "state": "running",
      "started_at": "2025-11-19T16:00:00.000Z",
      "progress_percent": 60
    }
  ],
  "count": 1
}
```

**Status Codes**:
- `200`: Success

### POST /admin/cache/clear

Clear all caches (L1 and L2).

**Request**:
```json
{
  "cache_level": "all"
}
```

**Request Fields**:
- `cache_level` (optional): "all", "l1", or "l2" (default: "all")

**Response**:
```json
{
  "success": true,
  "message": "Cache cleared",
  "l1_cleared": true,
  "l2_cleared": true
}
```

**Status Codes**:
- `200`: Cache cleared

### GET /admin/cache/stats

Get cache statistics.

**Response**:
```json
{
  "l1": {
    "size": "128MB",
    "entries": 1024,
    "hit_rate": 0.85,
    "max_size": "256MB"
  },
  "l2": {
    "size": "512MB",
    "entries": 4096,
    "hit_rate": 0.92,
    "max_size": "1GB"
  }
}
```

**Status Codes**:
- `200`: Success

### POST /admin/cache/cleanup

Clean up expired cache entries.

**Response**:
```json
{
  "success": true,
  "entries_removed": 42
}
```

### POST /admin/cache/rebuild

Rebuild cache indexes.

**Response**:
```json
{
  "success": true,
  "message": "Cache rebuilt"
}
```

### GET /admin/reports/performance

Get performance metrics report.

**Response**:
```json
{
  "avg_response_time_ms": 125,
  "p95_response_time_ms": 450,
  "p99_response_time_ms": 850,
  "requests_per_second": 42.5,
  "agent_performance": {
    "fuzzy_detector": {
      "avg_time_ms": 50,
      "call_count": 1000
    }
  }
}
```

### GET /admin/reports/health

Get system health report.

**Response**: Similar to `/admin/status` with additional diagnostic info.

### POST /admin/agents/reload/{agent_id}

Reload specific agent configuration.

**Path Parameters**:
- `agent_id`: Agent identifier

**Response**:
```json
{
  "success": true,
  "agent_id": "fuzzy_detector",
  "message": "Agent reloaded"
}
```

**Status Codes**:
- `200`: Agent reloaded
- `404`: Agent not found

### POST /admin/system/gc

Trigger garbage collection (Python GC).

**Response**:
```json
{
  "success": true,
  "collected": 42
}
```

### POST /admin/maintenance/enable

Enable maintenance mode (reject new requests).

**Response**:
```json
{
  "success": true,
  "maintenance_mode": true
}
```

### POST /admin/maintenance/disable

Disable maintenance mode.

**Response**:
```json
{
  "success": true,
  "maintenance_mode": false
}
```

### POST /admin/system/checkpoint

Create system checkpoint for backup/recovery.

**Response**:
```json
{
  "success": true,
  "checkpoint_id": "chk-123",
  "timestamp": "2025-11-19T16:48:00.000Z"
}
```

### POST /api/admin/reset

Reset system by permanently deleting data. **DANGEROUS OPERATION**.

**Use Cases**:
- Clean up test data before production
- Reset development environment
- Clear all data during testing

**Request**:
```json
{
  "confirm": true,
  "delete_validations": true,
  "delete_workflows": true,
  "delete_recommendations": true,
  "delete_audit_logs": false,
  "clear_cache": true
}
```

**Request Fields**:
- `confirm` (required, boolean): Must be `true` to confirm deletion (safety check)
- `delete_validations` (optional, boolean): Delete all validation results (default: `true`)
- `delete_workflows` (optional, boolean): Delete all workflows (default: `true`)
- `delete_recommendations` (optional, boolean): Delete all recommendations (default: `true`)
- `delete_audit_logs` (optional, boolean): Delete audit logs (default: `false`, preserved for compliance)
- `clear_cache` (optional, boolean): Clear cache after reset (default: `true`)

**Response**:
```json
{
  "message": "System reset completed",
  "deleted": {
    "validations_deleted": 150,
    "workflows_deleted": 45,
    "recommendations_deleted": 320,
    "audit_logs_deleted": 0
  },
  "cache_cleared": true,
  "timestamp": "2025-11-21T18:50:00.000000"
}
```

**Safety Features**:
- Requires explicit confirmation (`confirm: true`)
- Selective deletion (choose what to delete)
- Audit logs preserved by default
- Detailed response with deletion counts
- Operation logged with warning level

**Status Codes**:
- `200`: System reset successful
- `400`: Invalid request or confirmation not provided
- `500`: Server error during reset

**Examples**:

```bash
# Reset everything
curl -X POST http://localhost:8080/api/admin/reset \
  -H "Content-Type: application/json" \
  -d '{
    "confirm": true,
    "delete_validations": true,
    "delete_workflows": true,
    "delete_recommendations": true,
    "delete_audit_logs": false,
    "clear_cache": true
  }'

# Delete only validations
curl -X POST http://localhost:8080/api/admin/reset \
  -H "Content-Type: application/json" \
  -d '{
    "confirm": true,
    "delete_validations": true,
    "delete_workflows": false,
    "delete_recommendations": false
  }'

# Full reset including audit logs
curl -X POST http://localhost:8080/api/admin/reset \
  -H "Content-Type: application/json" \
  -d '{
    "confirm": true,
    "delete_validations": true,
    "delete_workflows": true,
    "delete_recommendations": true,
    "delete_audit_logs": true,
    "clear_cache": true
  }'
```

**Warning**: This operation is irreversible. All deleted data is permanently lost.

## Audit and Logging

### GET /api/audit

Get audit logs with filtering.

**Query Parameters**:
- `action`: Filter by action type
- `user`: Filter by user
- `resource_type`: Filter by resource type
- `resource_id`: Filter by resource ID
- `start_date`: Filter by start date
- `end_date`: Filter by end date
- `limit`: Max results (default: 100)

**Response**:
```json
{
  "audit_logs": [
    {
      "id": "audit-123",
      "timestamp": "2025-11-19T16:48:00.000Z",
      "action": "recommendation_approved",
      "user": "admin@example.com",
      "resource_type": "recommendation",
      "resource_id": "rec-456",
      "details": {
        "reviewer": "admin@example.com",
        "notes": "Approved for release"
      }
    }
  ],
  "total": 1
}
```

**Status Codes**:
- `200`: Success
- `400`: Invalid query parameters

## Metrics

### GET /metrics

Prometheus-compatible metrics endpoint.

**Response** (Prometheus format):
```
# HELP tbcv_requests_total Total number of requests
# TYPE tbcv_requests_total counter
tbcv_requests_total{endpoint="/api/validate",method="POST"} 1234

# HELP tbcv_response_time_seconds Response time in seconds
# TYPE tbcv_response_time_seconds histogram
tbcv_response_time_seconds_bucket{le="0.1"} 890
tbcv_response_time_seconds_bucket{le="0.5"} 1200
tbcv_response_time_seconds_bucket{le="+Inf"} 1234

# HELP tbcv_cache_hit_rate Cache hit rate
# TYPE tbcv_cache_hit_rate gauge
tbcv_cache_hit_rate{cache_level="l1"} 0.85
tbcv_cache_hit_rate{cache_level="l2"} 0.92
```

**Status Codes**:
- `200`: Success

## Error Handling

### Standard Error Response

```json
{
  "detail": "Validation failed: Missing required field 'family'",
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2025-11-19T16:48:00.000Z",
  "request_id": "req-abc123"
}
```

### Common HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created
- `202 Accepted`: Request accepted (async processing)
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Pydantic validation error
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily unavailable

### Error Codes

- `VALIDATION_ERROR`: Request validation failed
- `AGENT_UNAVAILABLE`: Required agent not available
- `WORKFLOW_TIMEOUT`: Workflow execution timeout
- `DATABASE_ERROR`: Database operation failed
- `CACHE_ERROR`: Cache operation failed
- `INVALID_STATE`: Invalid state transition
- `RESOURCE_NOT_FOUND`: Requested resource not found

## Rate Limiting

Current implementation has no rate limiting. Production deployments should add:

- Per-client rate limits (e.g., 100 requests/minute)
- Burst handling
- API key-based quotas
- Response headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

## Authentication

The API currently has no authentication. Future versions will support:

- **JWT Token Authentication**: Bearer token in Authorization header
- **API Key Authentication**: `X-API-Key` header
- **OAuth2**: OAuth2 authorization code flow
- **Role-Based Access Control (RBAC)**: User roles and permissions

## CORS Configuration

CORS is configurable via `config/main.yaml`:

```yaml
server:
  enable_cors: true
  cors_origins:
    - "http://localhost:3000"
    - "https://yourdomain.com"
  cors_methods:
    - "GET"
    - "POST"
    - "PUT"
    - "DELETE"
  cors_headers:
    - "Content-Type"
    - "Authorization"
```

## Client Libraries

### Python Client

```python
import requests

class TBCVClient:
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url

    def validate(self, content, file_path, family="words"):
        response = requests.post(
            f"{self.base_url}/api/validate",
            json={
                "content": content,
                "file_path": file_path,
                "family": family
            }
        )
        return response.json()

    def get_recommendations(self, validation_id):
        response = requests.get(
            f"{self.base_url}/api/recommendations",
            params={"validation_id": validation_id}
        )
        return response.json()

# Usage
client = TBCVClient()
result = client.validate("# Title\n\nContent", "test.md")
print(f"Validation ID: {result['validation_id']}")
```

### JavaScript/TypeScript Client

```typescript
class TBCVClient {
  constructor(private baseUrl: string = 'http://localhost:8080') {}

  async validate(content: string, filePath: string, family: string = 'words') {
    const response = await fetch(`${this.baseUrl}/api/validate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content, file_path: filePath, family })
    });
    return response.json();
  }

  async getRecommendations(validationId: string) {
    const response = await fetch(
      `${this.baseUrl}/api/recommendations?validation_id=${validationId}`
    );
    return response.json();
  }
}

// Usage
const client = new TBCVClient();
const result = await client.validate('# Title\n\nContent', 'test.md');
console.log(`Validation ID: ${result.validation_id}`);
```

## Development Utilities (CLI Parity)

### POST /api/dev/create-test-file

Create a test file for validation testing.

**Request Body**:
```json
{
  "content": "# Test Content",  // Optional custom content
  "family": "words",             // Plugin family
  "filename": "test.md"          // Optional filename
}
```

**Response**:
```json
{
  "status": "created",
  "file_path": "data/temp/test_20251121_143000.md",
  "filename": "test_20251121_143000.md",
  "validation_result": {
    "status": "completed",
    "validation_result": {...}
  }
}
```

**Status Codes**:
- `200`: Test file created successfully
- `500`: Creation failed

### GET /api/dev/probe-endpoints

Discover and probe API endpoints.

**Query Parameters**:
- `include_pattern` (optional): Regex to include only matching paths
- `exclude_pattern` (optional): Regex to exclude matching paths

**Response**:
```json
{
  "total_endpoints": 65,
  "endpoints": [
    {
      "path": "/api/validate",
      "methods": ["POST"],
      "name": "validate_content",
      "tags": ["validation"]
    },
    ...
  ]
}
```

**Status Codes**:
- `200`: Endpoints discovered successfully

## Configuration & Control (CLI Parity)

### POST /api/config/cache-control

Control cache behavior at runtime.

**Request Body**:
```json
{
  "disable_cache": true,      // Enable/disable caching
  "clear_on_disable": false   // Clear cache when disabling
}
```

**Response**:
```json
{
  "cache_disabled": true,
  "previous_state": false,
  "cache_cleared": false
}
```

**Status Codes**:
- `200`: Cache control updated

### POST /api/config/log-level

Set runtime log level.

**Request Body**:
```json
{
  "level": "DEBUG"  // DEBUG, INFO, WARNING, ERROR, CRITICAL
}
```

**Response**:
```json
{
  "status": "updated",
  "log_level": "DEBUG"
}
```

**Status Codes**:
- `200`: Log level updated
- `400`: Invalid log level

### POST /api/config/force-override

Force override safety checks for enhancement.

**Request Body**:
```json
{
  "validation_id": "val_abc123",
  "force_enhance": true
}
```

**Response**:
```json
{
  "status": "updated",
  "validation_id": "val_abc123",
  "force_override": true
}
```

**Status Codes**:
- `200`: Override flag set
- `404`: Validation not found

## Export & Download (Multi-Format)

### GET /api/export/validation/{validation_id}

Export validation result in multiple formats.

**Path Parameters**:
- `validation_id`: Validation ID to export

**Query Parameters**:
- `format`: Export format - `json`, `yaml`, `text`, `csv` (default: `json`)

**Response**:
Downloads file with appropriate content-type:
- `application/json` for JSON
- `application/x-yaml` for YAML
- `text/plain` for TEXT
- `text/csv` for CSV

**Example**:
```bash
curl "http://localhost:8080/api/export/validation/val_123?format=csv" -O
```

**Status Codes**:
- `200`: Export successful
- `404`: Validation not found
- `400`: Unsupported format

### GET /api/export/recommendations

Export recommendations in multiple formats.

**Query Parameters**:
- `validation_id` (optional): Filter by validation ID
- `status` (optional): Filter by status
- `format`: Export format - `json`, `yaml`, `csv` (default: `json`)

**Response**:
Downloads file with all recommendations matching filters.

**Example**:
```bash
curl "http://localhost:8080/api/export/recommendations?status=approved&format=csv" -O
```

**Status Codes**:
- `200`: Export successful
- `400`: Unsupported format

### GET /api/export/workflow/{workflow_id}

Export workflow data in multiple formats.

**Path Parameters**:
- `workflow_id`: Workflow ID to export

**Query Parameters**:
- `format`: Export format - `json`, `yaml` (default: `json`)

**Response**:
Downloads workflow data file.

**Example**:
```bash
curl "http://localhost:8080/api/export/workflow/wf_456?format=yaml" -O
```

**Status Codes**:
- `200`: Export successful
- `404`: Workflow not found
- `400`: Unsupported format

## Performance Tuning

### Server Configuration

```bash
# Production configuration
uvicorn tbcv.api.server:app \
  --host 0.0.0.0 \
  --port 8080 \
  --workers 4 \
  --timeout-keep-alive 65 \
  --limit-concurrency 1000 \
  --backlog 2048
```

### Database Optimization

- Connection pooling: 20-50 connections
- Query optimization with indexes
- Asynchronous database operations
- Regular vacuum operations

### Caching Strategy

- L1 memory cache: 256MB-1GB
- L2 persistent cache: 1-4GB
- TTL-based expiration
- Cache warming on startup

## API Versioning

Current API version: `2.0.0`

Version strategy:
- URL path versioning: `/api/v2/`
- Backward compatibility maintained for 1 major version
- Deprecation notices in response headers: `X-API-Deprecated: true`
- Migration guides provided for breaking changes

## Related Documentation

- [Web Dashboard](web_dashboard.md) - Web UI documentation
- [Workflows](workflows.md) - Workflow details
- [Troubleshooting](troubleshooting.md) - Common API issues
- [CLI Usage](cli_usage.md) - CLI alternative to API
