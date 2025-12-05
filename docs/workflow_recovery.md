# Workflow Recovery Guide

## Overview

TBCV workflows support automatic checkpointing and recovery mechanisms. If a workflow fails due to system crashes, errors, or interruptions, it can be recovered from the last successful checkpoint, ensuring work is not lost and workflows can continue from where they stopped.

## Table of Contents

- [How It Works](#how-it-works)
- [Checkpoint Lifecycle](#checkpoint-lifecycle)
- [CLI Commands](#cli-commands)
- [API Endpoints](#api-endpoints)
- [Recovery Best Practices](#recovery-best-practices)
- [Troubleshooting](#troubleshooting)
- [Manual Recovery](#manual-recovery)
- [Advanced Topics](#advanced-topics)

## How It Works

The checkpoint and recovery system operates in two layers:

### 1. Database Checkpoints (Workflow State)

Workflow checkpoints are stored in the database and track:
- Workflow ID and type
- Current step number
- Workflow state data (serialized)
- Validation hash for integrity
- Timestamp of checkpoint creation
- Whether checkpoint can be resumed from

### 2. System Checkpoints (Full State)

System checkpoints are file-based and include:
- Complete database snapshot
- Cache statistics
- System metadata
- Checkpoint creation timestamp

## Checkpoint Lifecycle

```
[Start Workflow]
    ↓
[Step 1] → [Checkpoint 1: Database checkpoint created]
    ↓
[Step 2] → [Checkpoint 2: State saved with progress]
    ↓
[Step 3] → [Checkpoint 3: Files processed recorded]
    ↓
[FAILURE OCCURS]
    ↓
[Recovery Mode]
    ├→ [Load Latest Checkpoint]
    ├→ [Validate Checkpoint Integrity]
    ├→ [Restore Workflow State]
    └→ [Resume from Step 3]
    ↓
[Step 4] → Continue processing
    ↓
[Complete]
```

## CLI Commands

### List Workflow Checkpoints

List all checkpoints for a specific workflow:

```bash
python -m tbcv workflow checkpoints <workflow_id>
```

Example:
```bash
python -m tbcv workflow checkpoints wf-123456
```

Output:
```
Checkpoints for workflow wf-123456:
1. ID: cp-001 | Step: 1 | Created: 2024-01-15 10:30:00 | Name: step_1_complete
2. ID: cp-002 | Step: 2 | Created: 2024-01-15 10:35:00 | Name: step_2_complete
3. ID: cp-003 | Step: 3 | Created: 2024-01-15 10:40:00 | Name: step_3_complete
```

### Recover Workflow from Checkpoint

Recover a failed workflow from a specific checkpoint:

```bash
python -m tbcv workflow recover <workflow_id> --checkpoint-id <checkpoint_id>
```

Example:
```bash
python -m tbcv workflow recover wf-123456 --checkpoint-id cp-002
```

### Resume Workflow from Last Checkpoint

Automatically resume from the most recent checkpoint:

```bash
python -m tbcv workflow resume <workflow_id>
```

### Rollback to Previous Checkpoint

Rollback workflow to an earlier checkpoint:

```bash
python -m tbcv workflow rollback <workflow_id> --checkpoint-id <checkpoint_id>
```

Example:
```bash
python -m tbcv workflow rollback wf-123456 --checkpoint-id cp-001
```

### List System Checkpoints

List all system-level checkpoints:

```bash
python -m tbcv system checkpoints list
```

### Create System Checkpoint

Manually create a system checkpoint:

```bash
python -m tbcv system checkpoints create --name "pre_upgrade_backup"
```

### Recover System from Checkpoint

Restore entire system state from a system checkpoint:

```bash
python -m tbcv system checkpoints recover <checkpoint_id>
```

## API Endpoints

### GET /api/workflows/{workflow_id}/checkpoints

List all checkpoints for a workflow.

**Response:**
```json
{
  "workflow_id": "wf-123456",
  "checkpoints": [
    {
      "id": "cp-001",
      "workflow_id": "wf-123456",
      "name": "step_1_complete",
      "step_number": 1,
      "created_at": "2024-01-15T10:30:00Z",
      "validation_hash": "abc123",
      "can_resume_from": true
    }
  ]
}
```

### POST /api/workflows/{workflow_id}/recover

Recover workflow from a specific checkpoint.

**Request:**
```json
{
  "checkpoint_id": "cp-002"
}
```

**Response:**
```json
{
  "success": true,
  "workflow_id": "wf-123456",
  "recovered_from": "cp-002",
  "current_step": 2,
  "state": "running"
}
```

### POST /api/workflows/{workflow_id}/resume

Resume workflow from last checkpoint.

**Response:**
```json
{
  "success": true,
  "workflow_id": "wf-123456",
  "resumed_from": "cp-003",
  "current_step": 3,
  "state": "running"
}
```

### POST /api/workflows/{workflow_id}/rollback

Rollback workflow to earlier checkpoint.

**Request:**
```json
{
  "checkpoint_id": "cp-001"
}
```

**Response:**
```json
{
  "success": true,
  "workflow_id": "wf-123456",
  "rolled_back_to": "cp-001",
  "current_step": 1,
  "state": "running"
}
```

## Recovery Best Practices

### 1. Checkpoint Frequently

Create checkpoints after expensive or time-consuming operations:

```python
# After processing a batch of files
checkpoint_id = db_manager.create_checkpoint(
    workflow_id=workflow_id,
    name=f"batch_{batch_num}_complete",
    step_number=current_step,
    state_data=state_data,
    validation_hash=compute_hash(state_data)
)
```

### 2. Keep Recent Checkpoints

Don't delete checkpoints until workflow completes successfully:

```python
# Only cleanup after workflow completion
if workflow.state == WorkflowState.COMPLETED:
    # Keep last 3 checkpoints for historical reference
    cleanup_old_checkpoints(workflow_id, keep_last=3)
```

### 3. Validate Before Recovery

Always validate checkpoint integrity before attempting recovery:

```python
from core.checkpoint_manager import CheckpointManager

checkpoint_mgr = CheckpointManager()
if checkpoint_mgr.validate_checkpoint(checkpoint_id):
    checkpoint_mgr.recover_from_checkpoint(checkpoint_id)
else:
    # Try previous checkpoint or report error
    logger.error(f"Checkpoint {checkpoint_id} is corrupted")
```

### 4. Test Recovery Regularly

Periodically test your recovery process:

```bash
# Test recovery in non-production environment
pytest tests/workflows/test_checkpoint_recovery.py -v
```

### 5. Monitor Recovery Success Rate

Track recovery metrics to identify issues:

```python
recovery_metrics = {
    "total_recoveries": 100,
    "successful_recoveries": 95,
    "failed_recoveries": 5,
    "success_rate": 95.0
}
```

## Troubleshooting

### Checkpoint Not Found

**Symptom:** Error message "Checkpoint not found: cp-xxx"

**Causes:**
- Checkpoint was deleted
- Checkpoint ID is incorrect
- Database connection issue

**Solutions:**
1. List all checkpoints for the workflow:
   ```bash
   python -m tbcv workflow checkpoints <workflow_id>
   ```

2. Verify checkpoint ID is correct

3. Check database connectivity:
   ```bash
   python -m tbcv system status
   ```

4. Try recovering from an earlier checkpoint:
   ```bash
   python -m tbcv workflow recover <workflow_id> --checkpoint-id <earlier_cp_id>
   ```

### Corrupted Checkpoint

**Symptom:** Error message "Failed to load checkpoint data"

**Causes:**
- Checkpoint data is corrupted
- Serialization format changed
- Disk corruption

**Solutions:**
1. Try previous checkpoint:
   ```bash
   python -m tbcv workflow checkpoints <workflow_id>
   # Find earlier checkpoint
   python -m tbcv workflow recover <workflow_id> --checkpoint-id <earlier_cp_id>
   ```

2. Check disk integrity

3. Restore from system checkpoint if available:
   ```bash
   python -m tbcv system checkpoints recover <system_cp_id>
   ```

4. If all checkpoints corrupted, restart workflow from beginning

### Recovery Fails

**Symptom:** Recovery attempt fails with various errors

**Causes:**
- Workflow state inconsistency
- Database connection lost
- Missing dependencies
- System resources exhausted

**Solutions:**
1. Check workflow state:
   ```bash
   python -m tbcv workflow status <workflow_id>
   ```

2. Verify database connection:
   ```bash
   python -m tbcv system status
   ```

3. Check system logs:
   ```bash
   tail -f logs/tbcv.log
   ```

4. Reset workflow if necessary:
   ```bash
   python -m tbcv workflow reset <workflow_id>
   ```

5. Contact support with workflow ID and error logs

### State Inconsistency After Recovery

**Symptom:** Workflow resumes but state doesn't match expected values

**Causes:**
- Checkpoint created at wrong time
- State data not fully serialized
- Concurrent modifications

**Solutions:**
1. Verify checkpoint data:
   ```python
   from core.database import DatabaseManager

   db = DatabaseManager()
   with db.get_session() as session:
       checkpoint = session.query(Checkpoint).filter(
           Checkpoint.id == checkpoint_id
       ).first()
       # Inspect checkpoint.state_data
   ```

2. Rollback to earlier checkpoint:
   ```bash
   python -m tbcv workflow rollback <workflow_id> --checkpoint-id <earlier_cp_id>
   ```

3. If state critically inconsistent, restart workflow

## Manual Recovery

If automatic recovery fails, you can manually recover workflow state.

### Step 1: Query Checkpoint Data

```sql
-- Connect to database
sqlite3 tbcv.db

-- List checkpoints for workflow
SELECT * FROM checkpoints WHERE workflow_id = 'wf-123456';

-- Get specific checkpoint
SELECT * FROM checkpoints WHERE id = 'cp-002';
```

### Step 2: Extract State Data

```python
import pickle
from core.database import DatabaseManager

db = DatabaseManager()
with db.get_session() as session:
    checkpoint = session.query(Checkpoint).filter(
        Checkpoint.id == 'cp-002'
    ).first()

    # Deserialize state data
    state_data = pickle.loads(checkpoint.state_data)
    print(state_data)
```

### Step 3: Manually Restore State

```python
from core.database import DatabaseManager, WorkflowState

db = DatabaseManager()

# Update workflow to recovered state
db.update_workflow(
    workflow_id='wf-123456',
    state=WorkflowState.RUNNING,
    current_step=2,
    error_message=None
)
```

### Step 4: Resume Execution

```python
from core.workflow_manager import WorkflowManager

workflow_mgr = WorkflowManager(db_manager=db)

# Resume workflow execution
# Note: You may need to manually set state before resuming
workflow_mgr.resume_workflow('wf-123456')
```

## Advanced Topics

### Custom Checkpoint Strategies

Implement custom checkpoint strategies for specific workflow types:

```python
class AdaptiveCheckpointStrategy:
    """Create checkpoints based on time and progress."""

    def should_checkpoint(self, workflow_id, elapsed_time, progress_delta):
        # Checkpoint every 5 minutes
        if elapsed_time > 300:
            return True

        # Checkpoint on significant progress
        if progress_delta > 0.1:  # 10% progress
            return True

        return False
```

### Checkpoint Compression

For large state data, enable compression:

```python
import gzip
import pickle

def create_compressed_checkpoint(state_data):
    pickled = pickle.dumps(state_data)
    compressed = gzip.compress(pickled)
    return compressed

def load_compressed_checkpoint(compressed_data):
    decompressed = gzip.decompress(compressed_data)
    return pickle.loads(decompressed)
```

### Checkpoint Retention Policies

Configure automatic cleanup of old checkpoints:

```python
CHECKPOINT_RETENTION_POLICY = {
    "keep_completed": 3,      # Keep 3 most recent for completed workflows
    "keep_failed": 10,        # Keep 10 most recent for failed workflows
    "max_age_days": 30,       # Delete checkpoints older than 30 days
    "keep_system_checkpoints": 5  # Keep 5 system checkpoints
}
```

### Distributed Checkpoints

For distributed systems, coordinate checkpoints across nodes:

```python
class DistributedCheckpointCoordinator:
    """Coordinate checkpoints across multiple workflow nodes."""

    def create_distributed_checkpoint(self, workflow_id, node_states):
        # Collect state from all nodes
        all_states = {}
        for node_id, state in node_states.items():
            all_states[node_id] = state

        # Create coordinated checkpoint
        checkpoint_id = self.create_checkpoint(
            workflow_id=workflow_id,
            name="distributed_checkpoint",
            state_data=all_states
        )

        return checkpoint_id
```

## See Also

- [Workflows Guide](workflows.md) - General workflow documentation
- [Troubleshooting Guide](troubleshooting.md) - General troubleshooting
- [Database Schema](database_schema.md) - Database structure
- [API Documentation](api.md) - Complete API reference

## Support

For additional help with checkpoint recovery:

1. Check the logs: `logs/tbcv.log`
2. Run system diagnostics: `python -m tbcv system diagnostics`
3. Review checkpoint integrity: `python -m tbcv system checkpoints validate`
4. Contact support with workflow ID and checkpoint IDs
