# TBCV Database Schema

This document describes the SQLite database schema used by TBCV.

**Location**: `data/tbcv.db` (default)
**ORM**: SQLAlchemy (`core/database.py`)

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
│   CacheEntry     │     │   MetricEntry    │
│                  │     │                  │
│  cache_key (PK)  │     │  id (PK)         │
│  agent_id        │     │  name            │
│  method_name     │     │  value           │
│  result_data     │     │  metadata        │
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

Stores system performance metrics.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | VARCHAR(36) | No | Primary key (UUID) |
| name | VARCHAR(100) | Yes | Metric name |
| value | FLOAT | Yes | Metric value |
| metadata | JSON | Yes | Additional context |
| created_at | DATETIME | Yes | Timestamp |

**Indexes**:
- Index on `name`
- Index on `created_at`

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

# Get validation by ID
with db_manager.get_session() as session:
    validation = session.query(ValidationResult).filter_by(id=val_id).first()

# Get recommendations for validation
with db_manager.get_session() as session:
    recs = session.query(Recommendation).filter_by(
        validation_id=val_id,
        status=RecommendationStatus.PENDING
    ).all()

# Count by status
with db_manager.get_session() as session:
    pending_count = session.query(Recommendation).filter_by(
        status=RecommendationStatus.PENDING
    ).count()
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
