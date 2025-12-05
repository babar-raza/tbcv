# TBCV Database Schema

This document describes the SQLite database schema used by TBCV.

**Location**: `data/tbcv.db` (default)
**ORM**: SQLAlchemy (`core/database.py`)
**Total Tables**: 7 (workflows, validation_results, recommendations, checkpoints, audit_logs, cache_entries, metrics)

## Entity Relationship Diagram

```
┌──────────────────┐     ┌────────────────────┐
│    Workflow      │────<│  ValidationResult  │
│                  │     │                    │
│  id (PK)         │     │  id (PK)           │
│  type            │     │  workflow_id (FK)  │
│  state           │     │  file_path         │
│  input_params    │     │  status            │
│  metadata        │     │  validation_results│
│  progress        │     │                    │
└────────┬─────────┘     └─────────┬──────────┘
         │                         │
         │                         │
┌────────▼─────────┐     ┌─────────▼──────────┐
│    Checkpoint    │     │   Recommendation   │
│                  │     │                    │
│  id (PK)         │     │  id (PK)           │
│  workflow_id (FK)│     │  validation_id (FK)│
│  name            │     │  type              │
│  step_number     │     │  status            │
│  state_data      │     │  instruction       │
└──────────────────┘     └─────────┬──────────┘
                                   │
                         ┌─────────▼──────────┐
                         │     AuditLog       │
                         │                    │
                         │  id (PK)           │
                         │  recommendation_id │
                         │  action            │
                         │  actor             │
                         └────────────────────┘

┌──────────────────┐     ┌──────────────────┐
│   CacheEntry     │     │    Metrics       │
│                  │     │                  │
│  cache_key (PK)  │     │  id (PK)         │
│  agent_id        │     │  name (indexed)  │
│  method_name     │     │  value           │
│  result_data     │     │  created_at      │
│  expires_at      │     │  metadata        │
│  access_count    │     │                  │
│  last_accessed   │     │                  │
│  size_bytes      │     │                  │
└──────────────────┘     └──────────────────┘
```

## Tables

### workflows

Stores workflow execution state and progress.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | VARCHAR(36) | No | Primary key (UUID) |
| type | VARCHAR(50) | No | Workflow type (validate_file, validate_directory, etc.) |
| state | ENUM | No | Current state (pending, running, paused, completed, failed, cancelled) |
| input_params | JSON | Yes | Workflow input parameters |
| metadata | JSON | Yes | Additional metadata |
| total_steps | INTEGER | Yes | Total number of steps |
| current_step | INTEGER | Yes | Current step number |
| progress_percent | INTEGER | Yes | Progress percentage (0-100) |
| error_message | TEXT | Yes | Error message if failed |
| created_at | DATETIME | Yes | Creation timestamp |
| updated_at | DATETIME | Yes | Last update timestamp |
| completed_at | DATETIME | Yes | Completion timestamp |

**Indexes**:
- `idx_workflows_state_created` (state, created_at)
- `idx_workflows_type_state` (type, state)

### validation_results

Stores validation results for content files.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | VARCHAR(36) | No | Primary key (UUID) |
| workflow_id | VARCHAR(36) | Yes | Foreign key to workflows |
| file_path | VARCHAR(1024) | Yes | Path to validated file |
| rules_applied | JSON | Yes | List of validation rules applied |
| validation_results | JSON | Yes | Detailed validation results |
| validation_types | JSON | Yes | Types of validation run (yaml, markdown, Truth, etc.) |
| parent_validation_id | VARCHAR(36) | Yes | FK to previous validation (for re-validation) |
| comparison_data | JSON | Yes | Comparison results for re-validation |
| notes | TEXT | Yes | User notes |
| severity | VARCHAR(20) | Yes | Severity level |
| status | ENUM | Yes | Status (pass, fail, warning, skipped, approved, rejected, enhanced) |
| content_hash | VARCHAR(64) | Yes | Hash of content at validation time |
| ast_hash | VARCHAR(64) | Yes | AST hash for structural comparison |
| run_id | VARCHAR(64) | Yes | Unique run identifier |
| file_hash | VARCHAR(64) | Yes | Hash of file for history tracking |
| version_number | INTEGER | Yes | Version number for file path |
| created_at | DATETIME | Yes | Creation timestamp |
| updated_at | DATETIME | Yes | Last update timestamp |

**Indexes**:
- `idx_validation_file_status` (file_path, status)
- `idx_validation_file_severity` (file_path, severity)
- `idx_validation_created` (created_at)

### recommendations

Stores human-in-the-loop recommendations for content enhancement.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | VARCHAR(36) | No | Primary key (UUID) |
| validation_id | VARCHAR(36) | No | Foreign key to validation_results |
| type | VARCHAR(50) | No | Recommendation type (link_plugin, fix_format, add_info_text) |
| title | VARCHAR(200) | No | Brief title |
| description | TEXT | Yes | Detailed description |
| scope | VARCHAR(200) | Yes | Location scope (line:42, section:intro, global) |
| instruction | TEXT | Yes | Concrete, actionable instruction |
| rationale | TEXT | Yes | Explanation of why this fixes the issue |
| severity | VARCHAR(20) | Yes | Severity (critical, high, medium, low) |
| original_content | TEXT | Yes | Original content to change |
| proposed_content | TEXT | Yes | Proposed replacement content |
| diff | TEXT | Yes | Unified diff of changes |
| confidence | FLOAT | Yes | Confidence score (0.0-1.0) |
| priority | VARCHAR(20) | Yes | Priority level |
| status | ENUM | No | Status (proposed, pending, approved, rejected, applied) |
| reviewed_by | VARCHAR(100) | Yes | Reviewer identifier |
| reviewed_at | DATETIME | Yes | Review timestamp |
| review_notes | TEXT | Yes | Reviewer notes |
| applied_at | DATETIME | Yes | Application timestamp |
| applied_by | VARCHAR(100) | Yes | Who applied the change |
| metadata | JSON | Yes | Additional metadata |
| created_at | DATETIME | Yes | Creation timestamp |
| updated_at | DATETIME | Yes | Last update timestamp |

**Indexes**:
- `idx_recommendations_status` (status)
- `idx_recommendations_validation` (validation_id, status)
- `idx_recommendations_type` (type)

### checkpoints

Stores workflow checkpoints for resumption and recovery.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | VARCHAR(36) | No | Primary key (UUID) |
| workflow_id | VARCHAR(36) | No | Foreign key to workflows |
| name | VARCHAR(100) | No | Checkpoint name |
| step_number | INTEGER | No | Step number in workflow |
| state_data | BLOB | Yes | Serialized state data |
| validation_hash | VARCHAR(32) | Yes | Hash for integrity check |
| can_resume_from | BOOLEAN | Yes | Whether workflow can resume from here |
| created_at | DATETIME | Yes | Creation timestamp |

**Indexes**:
- `idx_checkpoints_workflow_step` (workflow_id, step_number)

### audit_logs

Tracks all changes to recommendations for compliance and debugging.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | VARCHAR(36) | No | Primary key (UUID) |
| recommendation_id | VARCHAR(36) | Yes | Foreign key to recommendations |
| action | VARCHAR(50) | No | Action type (created, approved, rejected, applied, modified) |
| actor | VARCHAR(100) | Yes | Who performed the action |
| actor_type | VARCHAR(20) | Yes | Actor type (user, system, agent) |
| before_state | JSON | Yes | State before change |
| after_state | JSON | Yes | State after change |
| changes | JSON | Yes | Specific changes made |
| notes | TEXT | Yes | Additional notes |
| metadata | JSON | Yes | Additional metadata |
| created_at | DATETIME | Yes | Timestamp |

**Indexes**:
- `idx_audit_action` (action)
- `idx_audit_created` (created_at)

### cache_entries

Stores L2 persistent cache entries for validation results and LLM responses.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| cache_key | VARCHAR(200) | No | Primary key (cache key) |
| agent_id | VARCHAR(100) | No | Agent that created entry |
| method_name | VARCHAR(100) | No | Method that was cached |
| input_hash | VARCHAR(64) | No | Hash of input parameters |
| result_data | BLOB | Yes | Serialized result |
| expires_at | DATETIME | No | Expiration timestamp |
| access_count | INTEGER | Yes | Number of cache hits |
| last_accessed | DATETIME | Yes | Last access timestamp |
| size_bytes | INTEGER | Yes | Size of cached data |
| created_at | DATETIME | Yes | Creation timestamp |

**Indexes**:
- `idx_cache_expires` (expires_at)
- `idx_cache_agent_method` (agent_id, method_name)

### metrics

Stores application performance metrics for monitoring, alerting, and performance analysis.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | VARCHAR(36) | No | Primary key (UUID) |
| name | VARCHAR(100) | No | Metric name (e.g., "validation_duration", "cache_hit_rate", "agent_execution_time") |
| value | FLOAT | No | Metric value (numeric measurement) |
| created_at | DATETIME | No | Timestamp when metric was recorded |
| metadata | JSON | Yes | Additional context (tags, labels, dimensions, source) |

**Indexes**:
- `idx_metrics_name` (name)
- `idx_metrics_created` (created_at)

**Purpose**:
- Store application performance metrics for real-time monitoring
- Track validation processing times and throughput
- Monitor cache hit rates and performance
- Record agent execution times and resource usage
- Support performance alerting and anomaly detection
- Enable performance trend analysis and capacity planning

**Example Queries**:

```sql
-- Get average validation duration over last hour
SELECT AVG(value)
FROM metrics
WHERE name = 'validation_duration'
  AND created_at >= datetime('now', '-1 hour');

-- Get cache hit rate for last 24 hours
SELECT
  SUM(CASE WHEN name = 'cache_hit' THEN value ELSE 0 END) /
  (SUM(CASE WHEN name = 'cache_hit' THEN value ELSE 0 END) +
   SUM(CASE WHEN name = 'cache_miss' THEN value ELSE 0 END)) as hit_rate
FROM metrics
WHERE created_at >= datetime('now', '-1 day')
  AND name IN ('cache_hit', 'cache_miss');

-- Get top 10 agents by average execution time
SELECT
  metadata->>'$.agent_id' as agent_id,
  AVG(value) as avg_execution_time,
  COUNT(*) as sample_count
FROM metrics
WHERE name = 'agent_execution_time'
  AND created_at >= datetime('now', '-7 days')
GROUP BY metadata->>'$.agent_id'
ORDER BY avg_execution_time DESC
LIMIT 10;

-- Get metrics recorded in last 24 hours grouped by type
SELECT
  name,
  COUNT(*) as count,
  MIN(value) as min_val,
  AVG(value) as avg_val,
  MAX(value) as max_val
FROM metrics
WHERE created_at >= datetime('now', '-1 day')
GROUP BY name
ORDER BY count DESC;
```

**Data Retention**:
- Metrics are retained for 30 days by default
- Older metrics can be archived for long-term analysis
- Configurable via application settings

## Enums

### WorkflowState
```python
class WorkflowState(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
```

### ValidationStatus
```python
class ValidationStatus(enum.Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    SKIPPED = "skipped"
    APPROVED = "approved"
    REJECTED = "rejected"
    ENHANCED = "enhanced"
```

### RecommendationStatus
```python
class RecommendationStatus(enum.Enum):
    PROPOSED = "proposed"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
```

## Foreign Key Relationships

| Parent Table | Child Table | Relationship |
|--------------|-------------|--------------|
| workflows | validation_results | One-to-Many |
| workflows | checkpoints | One-to-Many (cascade delete) |
| validation_results | recommendations | One-to-Many (cascade delete) |
| validation_results | validation_results | Self-referential (parent_validation_id) |
| recommendations | audit_logs | One-to-Many (cascade delete) |

## Database Operations

### Initialization

```python
from core.database import db_manager

# Initialize database (creates tables if needed)
db_manager.init_database()

# Check connection
if db_manager.is_connected():
    print("Database ready")
```

### Common Queries

```python
from core.database import db_manager, ValidationResult, Recommendation
from core.database import RecommendationStatus, Workflow, WorkflowState
from sqlalchemy import func, and_

# Get validation by ID
with db_manager.get_session() as session:
    validation = session.query(ValidationResult).filter_by(id='val-123').first()
    if validation:
        print(f"File: {validation.file_path}")
        print(f"Status: {validation.status}")

# Get recommendations for validation with specific status
with db_manager.get_session() as session:
    recs = session.query(Recommendation).filter(
        Recommendation.validation_id == 'val-123',
        Recommendation.status == RecommendationStatus.PENDING
    ).all()

    print(f"Found {len(recs)} pending recommendations")

# Count recommendations by status
with db_manager.get_session() as session:
    status_counts = session.query(
        Recommendation.status,
        func.count(Recommendation.id).label('count')
    ).group_by(Recommendation.status).all()

    for status, count in status_counts:
        print(f"{status.value}: {count}")

# Get recent validations (last 7 days)
from datetime import datetime, timedelta, timezone

with db_manager.get_session() as session:
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent = session.query(ValidationResult).filter(
        ValidationResult.created_at >= week_ago
    ).order_by(ValidationResult.created_at.desc()).limit(50).all()

    print(f"Found {len(recent)} validations in the last 7 days")

# Get validations by file path pattern
with db_manager.get_session() as session:
    docs = session.query(ValidationResult).filter(
        ValidationResult.file_path.like('docs/%')
    ).all()

    print(f"Found {len(docs)} validations in docs/")

# Get high-confidence recommendations
with db_manager.get_session() as session:
    high_conf = session.query(Recommendation).filter(
        Recommendation.confidence >= 0.9
    ).all()

    print(f"Found {len(high_conf)} high-confidence recommendations")

# Get validations with most issues
with db_manager.get_session() as session:
    problematic = session.query(ValidationResult).filter(
        ValidationResult.severity.in_(['error', 'critical'])
    ).order_by(ValidationResult.created_at.desc()).limit(10).all()

    print("Most problematic validations:")
    for val in problematic:
        print(f"  - {val.file_path}: {val.severity}")
```

### Advanced Query Examples

```python
from core.database import db_manager, ValidationResult, Recommendation
from core.database import AuditLog, Workflow, WorkflowState
from sqlalchemy import func, and_, or_

# Get validation statistics
with db_manager.get_session() as session:
    stats = session.query(
        ValidationResult.status,
        func.count(ValidationResult.id).label('count'),
        func.avg(func.length(ValidationResult.file_path)).label('avg_file_length')
    ).group_by(ValidationResult.status).all()

    for status, count, avg_len in stats:
        print(f"{status}: {count} validations (avg file length: {avg_len:.1f})")

# Get workflow progress statistics
with db_manager.get_session() as session:
    workflow_stats = session.query(
        Workflow.type,
        Workflow.state,
        func.count(Workflow.id).label('count'),
        func.avg(Workflow.progress_percent).label('avg_progress')
    ).filter(
        Workflow.state != WorkflowState.CANCELLED
    ).group_by(Workflow.type, Workflow.state).all()

    for wf_type, state, count, avg_progress in workflow_stats:
        print(f"{wf_type} ({state}): {count} workflows, {avg_progress:.1f}% avg progress")

# Get recommendations with audit trail
with db_manager.get_session() as session:
    rec = session.query(Recommendation).filter_by(id='rec-123').first()

    if rec:
        audit = session.query(AuditLog).filter_by(
            recommendation_id=rec.id
        ).order_by(AuditLog.created_at).all()

        print(f"Recommendation {rec.id}:")
        for entry in audit:
            print(f"  {entry.created_at}: {entry.action} by {entry.actor}")

# Find recommendations that haven't been applied yet
with db_manager.get_session() as session:
    unapplied = session.query(Recommendation).filter(
        Recommendation.status.in_([
            RecommendationStatus.PROPOSED,
            RecommendationStatus.APPROVED
        ])
    ).order_by(Recommendation.confidence.desc()).limit(20).all()

    print(f"Unapplied recommendations: {len(unapplied)}")

# Get files with most validations
with db_manager.get_session() as session:
    top_files = session.query(
        ValidationResult.file_path,
        func.count(ValidationResult.id).label('validation_count')
    ).group_by(ValidationResult.file_path).order_by(
        func.count(ValidationResult.id).desc()
    ).limit(10).all()

    print("Files with most validations:")
    for file_path, count in top_files:
        print(f"  {file_path}: {count} validations")

# Get cache entry statistics
with db_manager.get_session() as session:
    cache_stats = session.query(
        CacheEntry.agent_id,
        func.count(CacheEntry.cache_key).label('entries'),
        func.sum(CacheEntry.size_bytes).label('total_size'),
        func.avg(CacheEntry.access_count).label('avg_accesses')
    ).group_by(CacheEntry.agent_id).all()

    for agent_id, entries, total_size, avg_access in cache_stats:
        print(f"{agent_id}: {entries} entries, {total_size/1024:.1f}KB, "
              f"{avg_access:.1f} avg accesses")
```

### Database Maintenance

```bash
# Backup database
sqlite3 data/tbcv.db ".backup backup.db"

# Vacuum to reclaim space
sqlite3 data/tbcv.db "VACUUM"

# Check integrity
sqlite3 data/tbcv.db "PRAGMA integrity_check"

# Enable WAL mode for better concurrency
sqlite3 data/tbcv.db "PRAGMA journal_mode=WAL"
```

## Migration Notes

- Database tables are created automatically via SQLAlchemy `create_all()`
- No formal migration framework (Alembic) is currently used
- Schema changes require manual migration scripts
- Always backup before schema changes
