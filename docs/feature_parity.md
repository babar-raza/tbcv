# CLI vs Web API Feature Parity

This document tracks feature parity between the CLI (`cli/main.py`) and the Web API (`api/server.py`, `api/dashboard.py`).

## Feature Matrix

| Feature | CLI | Web API | Notes |
|---------|-----|---------|-------|
| **Validation** |
| Validate single file | `validate <file>` | `POST /api/validate` | Full parity |
| Validate directory | `validate-directory <dir>` | `POST /workflows/validate-directory` | Full parity |
| Batch validation | `batch <dir>` | `POST /api/validate/batch` | Full parity |
| Plugin detection | `detect-plugins` | `POST /api/detect-plugins` | Full parity |
| **Validation Management** |
| List validations | `validations list` | `GET /api/validations` | Full parity |
| Show validation | `validations show <id>` | `GET /api/validations/{id}` | Full parity |
| Approve validation | `validations approve <id>` | `POST /api/validations/{id}/approve` | Full parity |
| Reject validation | `validations reject <id>` | `POST /api/validations/{id}/reject` | Full parity |
| Validation history | `validations history <file>` | - | CLI only |
| Revalidate | `validations revalidate <id>` | - | CLI only |
| **Recommendations** |
| List recommendations | `recommendations list` | `GET /api/recommendations` | Full parity |
| Show recommendation | `recommendations show <id>` | `GET /api/recommendations/{id}` | Full parity |
| Approve recommendations | `recommendations approve <ids>` | `POST /api/recommendations/{id}/review` | Parity (different endpoints) |
| Reject recommendations | `recommendations reject <ids>` | `POST /api/recommendations/{id}/review` | Parity (different endpoints) |
| Bulk review | `recommendations approve <ids>...` | `POST /api/recommendations/bulk-review` | Full parity |
| Generate recommendations | `recommendations generate <val_id>` | `POST /api/validations/{id}/recommendations/generate` | Full parity |
| Auto-apply | `recommendations auto-apply <id>` | `POST /api/enhance/auto-apply` | Full parity |
| Delete recommendations | `recommendations delete <ids>` | - | CLI only |
| Rebuild recommendations | `recommendations rebuild <id>` | - | CLI only |
| **Enhancement** |
| Enhance file | `enhance <file>` | `POST /api/enhance` | Full parity |
| Preview enhancement | `enhance --dry-run` | `POST /api/enhance` with `preview: true` | Full parity |
| Enhancement comparison | - | `GET /api/validations/{id}/enhancement-comparison` | Web only |
| **Workflows** |
| List workflows | `workflows list` | `GET /workflows` | Full parity |
| Show workflow | `workflows show <id>` | `GET /workflows/{id}` | Full parity |
| Cancel workflow | `workflows cancel <id>` | `POST /workflows/{id}/control` | Full parity |
| Delete workflow | `workflows delete <ids>` | `DELETE /workflows/{id}` | Full parity |
| Bulk delete | `workflows delete <ids>...` | `POST /api/workflows/bulk-delete` | Full parity |
| Real-time progress | - | `WebSocket /ws/{id}` | Web only |
| **Administration** |
| System status | `status` | `GET /admin/status` | Full parity |
| Health check | `admin health` | `GET /health`, `/health/live`, `/health/ready` | Full parity |
| List agents | `admin agents` | `GET /agents` | Full parity |
| Cache stats | `admin cache-stats` | `GET /admin/cache/stats` | Full parity |
| Clear cache | `admin cache-clear` | `POST /admin/cache/clear` | Full parity |
| System reset | `admin reset` | `POST /api/admin/reset` | Full parity |
| Agent reload | - | `POST /admin/agents/reload/{id}` | Web only |
| Maintenance mode | - | `POST /admin/maintenance/enable` | Web only |
| **Export** |
| Export validation | - | `GET /api/export/validation/{id}` | Web only |
| Export recommendations | - | `GET /api/export/recommendations` | Web only |
| Export workflow | - | `GET /api/export/workflow/{id}` | Web only |
| **Development** |
| Create test file | `test` | `POST /api/dev/create-test-file` | Full parity |
| Probe endpoints | `probe-endpoints` | `GET /api/dev/probe-endpoints` | Full parity |
| **Configuration** |
| Cache control | - | `POST /api/config/cache-control` | Web only |
| Log level | - | `POST /api/config/log-level` | Web only |
| Force override | - | `POST /api/config/force-override` | Web only |
| **Real-time** |
| WebSocket updates | - | `WebSocket /ws/{id}` | Web only |
| SSE stream | - | `GET /api/stream/updates` | Web only |
| Activity feed | - | Dashboard UI | Web only |

## Legend

- **Full parity**: Feature available in both CLI and Web API with equivalent functionality
- **CLI only**: Feature available only via command line
- **Web only**: Feature available only via Web API or Dashboard

## CLI-Only Features

1. **Validation history** - View historical validations for a specific file
2. **Revalidate** - Re-run validation for a previous result
3. **Delete recommendations** - Remove recommendations from database
4. **Rebuild recommendations** - Delete and regenerate recommendations

## Web-Only Features

1. **Enhancement comparison** - Side-by-side diff view of original vs enhanced content
2. **Real-time WebSocket updates** - Live progress updates for workflows
3. **SSE stream** - Server-sent events for notifications
4. **Agent reload** - Hot reload agent configuration
5. **Maintenance mode** - Enable/disable maintenance mode
6. **Export endpoints** - Download validation/recommendation data in various formats
7. **Configuration endpoints** - Runtime configuration changes
8. **Dashboard UI** - Visual interface for all operations

## Achieving Full Parity

To achieve full CLI-Web parity, the following additions would be needed:

### CLI Additions Needed
```bash
# Export commands
tbcv export validation <id> --format json|yaml|csv
tbcv export recommendations --validation-id <id> --format json|yaml|csv
tbcv export workflow <id> --format json|yaml

# Configuration commands
tbcv config cache-control --disable|--enable
tbcv config log-level DEBUG|INFO|WARNING|ERROR
tbcv config force-override <validation_id>

# Enhancement comparison
tbcv validations compare <id>  # Show diff

# Maintenance
tbcv admin maintenance --enable|--disable
tbcv admin agents reload <agent_id>
```

### Web API Additions Needed
```
# Validation history
GET /api/validations/history/{file_path}

# Revalidate
POST /api/validations/{id}/revalidate

# Delete recommendations
DELETE /api/recommendations/{id}

# Rebuild recommendations
POST /api/validations/{id}/recommendations/rebuild
```

## Current Status

- **CLI Coverage**: ~85% of features
- **Web API Coverage**: ~90% of features
- **Bidirectional Parity**: ~75%

Most differences are due to the interactive nature of the Dashboard UI vs the stateless CLI approach.
