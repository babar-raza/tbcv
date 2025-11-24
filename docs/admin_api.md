# Admin API Reference

Complete reference for TBCV administrative endpoints used for system management, monitoring, and maintenance.

## Overview

The Admin API provides system administrators with tools to:
- Monitor system health and performance
- Manage caches and optimize performance
- Control maintenance mode
- Reload agent configurations
- Create system checkpoints for disaster recovery
- Trigger garbage collection

All admin endpoints are prefixed with `/admin/`.

## Authentication & Authorization

**Note:** Admin endpoints should be protected with authentication in production environments. Consider implementing API key authentication or role-based access control.

---

## System Status & Monitoring

### GET /admin/status

Get comprehensive system status including uptime, agent registration, workflow statistics, and maintenance mode status.

**Response:**
```json
{
  "timestamp": "2025-01-23T10:30:00Z",
  "system": {
    "version": "1.0.0",
    "uptime_seconds": 86400,
    "agents_registered": 12,
    "maintenance_mode": false
  },
  "workflows": {
    "total": 1523,
    "active": 5,
    "pending": 2,
    "running": 3,
    "completed": 1450,
    "failed": 68
  },
  "database": {
    "connected": true
  }
}
```

**Fields:**
- `uptime_seconds`: Server uptime in seconds since last restart
- `agents_registered`: Number of active agents in the registry
- `maintenance_mode`: Whether system is in maintenance mode
- `workflows.*`: Current workflow statistics across all states

---

### GET /admin/workflows/active

Get detailed list of all currently active workflows (running, pending, or paused).

**Response:**
```json
{
  "count": 5,
  "workflows": [
    {
      "id": "wf-123",
      "type": "validate_file",
      "state": "running",
      "created_at": "2025-01-23T10:15:00Z",
      "progress": 65.5
    }
  ]
}
```

---

### GET /admin/reports/performance

Get performance metrics for a specified time period based on workflow analysis.

**Query Parameters:**
- `days` (integer, default: 7, max: 90): Number of days to analyze

**Request:**
```
GET /admin/reports/performance?days=30
```

**Response:**
```json
{
  "period_days": 30,
  "timestamp": "2025-01-23T10:30:00Z",
  "metrics": {
    "total_workflows": 1250,
    "completed_workflows": 1180,
    "failed_workflows": 45,
    "running_workflows": 25,
    "avg_completion_time_ms": 2345.67,
    "error_rate": 0.036,
    "success_rate": 0.944,
    "cache_hit_rate_l1": 0.72
  },
  "period": {
    "start": "2024-12-24T10:30:00Z",
    "end": "2025-01-23T10:30:00Z"
  }
}
```

**Metrics Explanation:**
- `avg_completion_time_ms`: Average time for workflows to complete (in milliseconds)
- `error_rate`: Percentage of failed workflows (0.0 - 1.0)
- `success_rate`: Percentage of successfully completed workflows (0.0 - 1.0)
- `cache_hit_rate_l1`: L1 cache hit rate for performance optimization

---

### GET /admin/reports/health

Get system health report with database and agent status.

**Query Parameters:**
- `period` (string, default: "7days"): Health check period

**Response:**
```json
{
  "period": "7days",
  "timestamp": "2025-01-23T10:30:00Z",
  "database": true,
  "agents": 12,
  "status": "healthy"
}
```

---

## Cache Management

TBCV uses a two-level caching system (L1: in-memory LRU, L2: persistent SQLite). These endpoints allow administrators to manage and monitor cache performance.

### GET /admin/cache/stats

Get detailed statistics for both L1 and L2 caches.

**Response:**
```json
{
  "l1": {
    "enabled": true,
    "size": 523,
    "max_size": 1000,
    "hits": 15234,
    "misses": 4521,
    "hit_rate": 0.7709,
    "ttl_seconds": 3600
  },
  "l2": {
    "enabled": true,
    "total_entries": 8456,
    "total_size_bytes": 45678912,
    "total_size_mb": 43.55,
    "database_path": "./data/cache/tbcv_cache.db"
  }
}
```

**Understanding Cache Levels:**
- **L1 Cache**: Fast in-memory cache with LRU eviction
- **L2 Cache**: Persistent database-backed cache for longer retention

---

### POST /admin/cache/clear

Clear all cache entries from both L1 and L2 caches. Use this after configuration changes or to force re-validation.

**⚠️ Warning:** This will clear ALL cached data. System performance may be temporarily degraded while caches rebuild.

**Response:**
```json
{
  "message": "Cache cleared successfully",
  "timestamp": "2025-01-23T10:30:00Z",
  "cleared": {
    "l1": true,
    "l1_entries": 523,
    "l2": true,
    "l2_entries": 8456
  }
}
```

---

### POST /admin/cache/cleanup

Remove only expired cache entries from both cache levels. Safe for regular maintenance.

**Response:**
```json
{
  "message": "Cache cleanup completed",
  "removed_entries": 342,
  "details": {
    "l1_cleaned": 87,
    "l2_cleaned": 255
  },
  "timestamp": "2025-01-23T10:30:00Z"
}
```

**Recommended Schedule:** Run daily via cron job for optimal cache hygiene.

---

### POST /admin/cache/rebuild

Rebuild cache from scratch by clearing all entries and optionally preloading critical data (truth data).

**Response:**
```json
{
  "message": "Cache rebuild completed",
  "timestamp": "2025-01-23T10:30:00Z",
  "note": "Cache cleared and will repopulate on demand"
}
```

**Use Cases:**
- After major system updates
- When cache corruption is suspected
- Following configuration changes to truth data

---

## Agent Management

### POST /admin/agents/reload/{agent_id}

Reload a specific agent by clearing its cache and reinitializing its configuration.

**Path Parameters:**
- `agent_id` (string): ID of the agent to reload (e.g., "content_validator", "truth_manager")

**Request:**
```
POST /admin/agents/reload/truth_manager
```

**Response:**
```json
{
  "message": "Agent truth_manager reloaded successfully",
  "agent_id": "truth_manager",
  "timestamp": "2025-01-23T10:30:00Z",
  "actions": ["cache_cleared", "config_reloaded"]
}
```

**Common Agent IDs:**
- `truth_manager`
- `content_validator`
- `content_enhancer`
- `fuzzy_detector`
- `code_analyzer`
- `orchestrator`

---

## Maintenance Mode

Maintenance mode prevents new workflow submissions while allowing system maintenance operations.

### POST /admin/maintenance/enable

Enable maintenance mode. New workflow submissions will be rejected while existing workflows can continue.

**Response:**
```json
{
  "message": "Maintenance mode enabled",
  "maintenance_mode": true,
  "timestamp": "2025-01-23T10:30:00Z",
  "note": "New workflow submissions will be rejected while in maintenance mode"
}
```

---

### POST /admin/maintenance/disable

Disable maintenance mode and resume normal operations.

**Response:**
```json
{
  "message": "Maintenance mode disabled",
  "maintenance_mode": false,
  "timestamp": "2025-01-23T10:30:00Z",
  "note": "System is now accepting new workflows"
}
```

---

## System Management

### POST /admin/system/gc

Manually trigger Python garbage collection. Useful for freeing memory after large operations.

**Response:**
```json
{
  "message": "Garbage collection completed",
  "timestamp": "2025-01-23T10:30:00Z"
}
```

---

### POST /admin/system/checkpoint

Create a system-wide checkpoint for disaster recovery purposes. Captures current system state including active workflows, agent states, and cache statistics.

**Response:**
```json
{
  "message": "System checkpoint created successfully",
  "checkpoint_id": "c7f9a8b4-1234-5678-9abc-def012345678",
  "timestamp": "2025-01-23T10:30:00Z",
  "summary": {
    "checkpoint_id": "c7f9a8b4-1234-5678-9abc-def012345678",
    "timestamp": "2025-01-23T10:30:00Z",
    "workflows": {
      "total": 1523,
      "active": 5,
      "active_ids": ["wf-1", "wf-2", "wf-3", "wf-4", "wf-5"]
    },
    "agents": {
      "registered": 12,
      "agent_ids": ["truth_manager", "content_validator", ...]
    },
    "cache": {
      "l1": {...},
      "l2": {...}
    },
    "system": {
      "uptime_seconds": 86400,
      "maintenance_mode": false
    }
  }
}
```

**Checkpoint Data:**
Checkpoints are stored in the database and can be used for:
- Disaster recovery
- System state auditing
- Troubleshooting system issues
- Rollback capabilities (future feature)

---

## Common Administrative Workflows

### Daily Maintenance Routine

```bash
# 1. Clean up expired cache entries
curl -X POST http://localhost:8000/admin/cache/cleanup

# 2. Check system health
curl http://localhost:8000/admin/status

# 3. Review performance metrics
curl http://localhost:8000/admin/reports/performance?days=1
```

### Before System Update

```bash
# 1. Create system checkpoint
curl -X POST http://localhost:8000/admin/system/checkpoint

# 2. Enable maintenance mode
curl -X POST http://localhost:8000/admin/maintenance/enable

# 3. Perform update...

# 4. Disable maintenance mode
curl -X POST http://localhost:8000/admin/maintenance/disable

# 5. Rebuild caches
curl -X POST http://localhost:8000/admin/cache/rebuild
```

### Performance Troubleshooting

```bash
# 1. Check cache statistics
curl http://localhost:8000/admin/cache/stats

# 2. If hit rate is low, rebuild cache
curl -X POST http://localhost:8000/admin/cache/rebuild

# 3. Reload specific agent if issues persist
curl -X POST http://localhost:8000/admin/agents/reload/content_validator

# 4. Trigger garbage collection
curl -X POST http://localhost:8000/admin/system/gc
```

---

## Error Responses

All admin endpoints return standard HTTP error codes:

**404 Not Found** - Agent ID not found:
```json
{
  "detail": "Agent truth_manager_typo not found"
}
```

**500 Internal Server Error** - Operation failed:
```json
{
  "detail": "Failed to clear cache"
}
```

---

## Security Recommendations

1. **API Gateway**: Place admin endpoints behind an API gateway with authentication
2. **IP Whitelisting**: Restrict access to known admin IP addresses
3. **Audit Logging**: All admin operations are logged for security audit
4. **Rate Limiting**: Implement rate limiting to prevent abuse
5. **HTTPS Only**: Always use HTTPS in production environments

---

## Related Documentation

- [API Reference](./api_reference.md) - Main API endpoints
- [Checkpoint System](./checkpoints.md) - Detailed checkpoint system documentation
- [Architecture](./architecture.md) - System architecture overview
- [Configuration](./configuration.md) - Cache and system configuration
