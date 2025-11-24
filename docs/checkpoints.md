# Checkpoint System

Comprehensive guide to TBCV's checkpoint and state management system for resumable operations and disaster recovery.

## Overview

The TBCV checkpoint system provides:
- **Workflow Resumability**: Save and restore workflow state at any point
- **Agent State Management**: Agents can create checkpoints during long-running operations
- **Disaster Recovery**: System-wide checkpoints for recovery from failures
- **Data Integrity**: MD5 validation ensures checkpoint data hasn't been corrupted

## Architecture

### Checkpoint Levels

TBCV supports two types of checkpoints:

1. **Agent Checkpoints**: Created by individual agents during processing
2. **System Checkpoints**: Comprehensive snapshots of the entire system state

### Storage

Checkpoints are stored in the SQLAlchemy database in the `checkpoints` table:

```python
class Checkpoint(Base):
    id: str                    # UUID
    workflow_id: str          # Associated workflow (or special sentinel ID)
    name: str                 # Human-readable name
    step_number: int          # Sequence number for workflow steps
    state_data: bytes         # Pickled state data
    created_at: datetime      # When checkpoint was created
    validation_hash: str      # MD5 hash for integrity checking
    can_resume_from: bool     # Whether this checkpoint is resumable
```

---

## Agent Checkpoints

### Creating Checkpoints

Agents can create checkpoints during long-running operations using the `create_checkpoint` method:

```python
from agents.base import BaseAgent

class MyAgent(BaseAgent):
    async def handle_long_operation(self, params):
        # Process some data...
        intermediate_results = {"processed": 100, "remaining": 900}

        # Create checkpoint
        checkpoint_id = self.create_checkpoint(
            name="batch_processing_step_1",
            data=intermediate_results,
            workflow_id="wf-12345"  # Optional
        )

        # Continue processing...
        # If operation fails, can resume from checkpoint
```

**Method Signature:**
```python
def create_checkpoint(
    self,
    name: str,
    data: Dict[str, Any],
    workflow_id: Optional[str] = None
) -> str
```

**Parameters:**
- `name`: Descriptive name for the checkpoint (e.g., "after_validation_phase")
- `data`: Dictionary of state data to persist (must be pickle-able)
- `workflow_id`: Optional workflow ID. If not provided, uses `agent_{agent_id}_{timestamp}`

**Returns:** UUID of the created checkpoint

**What Gets Saved:**
- All data in the `data` dictionary
- Timestamp of checkpoint creation
- MD5 hash of serialized data for integrity checking

---

### Restoring Checkpoints

Restore a previously saved checkpoint to resume operations:

```python
class MyAgent(BaseAgent):
    async def resume_operation(self, checkpoint_id: str):
        try:
            # Restore checkpoint data
            state_data = self.restore_checkpoint(checkpoint_id)

            # Resume from saved state
            processed = state_data.get("processed", 0)
            remaining = state_data.get("remaining", 0)

            # Continue operation...

        except ValueError as e:
            self.logger.error(f"Failed to restore: {e}")
```

**Method Signature:**
```python
def restore_checkpoint(self, checkpoint_id: str) -> Dict[str, Any]
```

**Returns:** Dictionary containing the restored state data

**Raises:**
- `ValueError`: If checkpoint not found, not resumable, or fails integrity check

**Integrity Checking:**
The system automatically validates the MD5 hash of the checkpoint data to ensure it hasn't been corrupted.

---

## System Checkpoints

### Creating System Checkpoints

System administrators can create comprehensive checkpoints via the Admin API:

```bash
curl -X POST http://localhost:8000/admin/system/checkpoint
```

**Response:**
```json
{
  "message": "System checkpoint created successfully",
  "checkpoint_id": "c7f9a8b4-1234-5678-9abc-def012345678",
  "timestamp": "2025-01-23T10:30:00Z",
  "summary": {
    "workflows": {
      "total": 1523,
      "active": 5,
      "active_ids": ["wf-1", "wf-2", "wf-3"]
    },
    "agents": {
      "registered": 12,
      "agent_ids": ["truth_manager", "content_validator", ...]
    },
    "cache": {
      "l1": {"size": 523, "hit_rate": 0.77},
      "l2": {"total_entries": 8456}
    },
    "system": {
      "uptime_seconds": 86400,
      "maintenance_mode": false
    }
  }
}
```

### What System Checkpoints Capture

System checkpoints save:
1. **Workflow States**: All active workflow IDs and states
2. **Agent Registry**: List of registered agents
3. **Cache Statistics**: L1 and L2 cache metrics
4. **System Metadata**: Uptime, maintenance mode, version info

**Special Workflow ID:** System checkpoints use the sentinel ID `00000000-0000-0000-0000-000000000000` to distinguish them from workflow-specific checkpoints.

---

## Database Schema

### Checkpoint Table Structure

```sql
CREATE TABLE checkpoints (
    id VARCHAR(36) PRIMARY KEY,
    workflow_id VARCHAR(36) NOT NULL,
    name VARCHAR(100) NOT NULL,
    step_number INTEGER NOT NULL,
    state_data BLOB,
    created_at DATETIME,
    validation_hash VARCHAR(32),
    can_resume_from BOOLEAN DEFAULT 1,

    FOREIGN KEY (workflow_id) REFERENCES workflows(id),
    INDEX idx_checkpoints_workflow_step (workflow_id, step_number)
);
```

### Querying Checkpoints

```python
from core.database import Checkpoint, db_manager

# List all checkpoints for a workflow
with db_manager.get_session() as session:
    checkpoints = session.query(Checkpoint).filter(
        Checkpoint.workflow_id == "wf-12345"
    ).order_by(Checkpoint.step_number).all()

# Get system checkpoints
system_checkpoints = session.query(Checkpoint).filter(
    Checkpoint.workflow_id == "00000000-0000-0000-0000-000000000000"
).all()
```

---

## Best Practices

### When to Create Checkpoints

✅ **Good Use Cases:**
- Before/after long-running operations (> 30 seconds)
- After expensive computations
- Before risky operations that might fail
- At logical phase boundaries in multi-step workflows
- Before external API calls

❌ **Avoid:**
- Creating checkpoints in tight loops (performance impact)
- Checkpointing trivial operations (< 1 second)
- Saving non-serializable objects (will fail)

### Checkpoint Naming

Use descriptive, hierarchical names:

```python
# Good ✅
"validation_phase_1_complete"
"after_llm_analysis"
"before_content_enhancement"

# Bad ❌
"checkpoint1"
"temp"
"state"
```

### Data to Save

**Include:**
- Current progress/position
- Intermediate results
- Configuration used
- Timestamps
- Error counts/retry state

**Exclude:**
- Large binary data (use references instead)
- Database connections
- File handles
- Thread/async objects
- Non-pickle-able objects

### Example: Complete Workflow with Checkpoints

```python
class ValidationWorkflow:
    def __init__(self, agent: BaseAgent):
        self.agent = agent

    async def run(self, file_path: str, workflow_id: str):
        # Phase 1: Load file
        content = await self.load_file(file_path)
        checkpoint_1 = self.agent.create_checkpoint(
            name="file_loaded",
            data={"file_path": file_path, "size": len(content)},
            workflow_id=workflow_id
        )

        # Phase 2: Validate
        validation_results = await self.validate(content)
        checkpoint_2 = self.agent.create_checkpoint(
            name="validation_complete",
            data={
                "file_path": file_path,
                "validation_results": validation_results
            },
            workflow_id=workflow_id
        )

        # Phase 3: Generate report
        report = await self.generate_report(validation_results)
        checkpoint_3 = self.agent.create_checkpoint(
            name="report_generated",
            data={
                "file_path": file_path,
                "report": report,
                "completed": True
            },
            workflow_id=workflow_id
        )

        return report

    async def resume(self, checkpoint_id: str):
        """Resume from a checkpoint."""
        state = self.agent.restore_checkpoint(checkpoint_id)

        if "completed" in state:
            return state["report"]
        elif "validation_results" in state:
            # Resume from phase 3
            return await self.generate_report(state["validation_results"])
        elif "size" in state:
            # Resume from phase 2
            content = await self.load_file(state["file_path"])
            validation_results = await self.validate(content)
            return await self.generate_report(validation_results)
```

---

## Recovery Scenarios

### Agent Crash Recovery

If an agent crashes during a long operation:

```python
# In recovery handler
async def recover_from_crash(workflow_id: str):
    # Find latest checkpoint for workflow
    with db_manager.get_session() as session:
        latest_checkpoint = session.query(Checkpoint).filter(
            Checkpoint.workflow_id == workflow_id,
            Checkpoint.can_resume_from == True
        ).order_by(Checkpoint.created_at.desc()).first()

        if latest_checkpoint:
            # Restore and resume
            state = agent.restore_checkpoint(latest_checkpoint.id)
            await workflow.resume_from_state(state)
```

### System Recovery

After system restart or crash:

```bash
# List recent system checkpoints
curl http://localhost:8000/admin/system/checkpoints

# Restore from checkpoint (future feature)
curl -X POST http://localhost:8000/admin/system/restore \
  -d '{"checkpoint_id": "c7f9a8b4-..."}'
```

---

## Performance Considerations

### Checkpoint Size

- **Small** (< 1 KB): Negligible impact
- **Medium** (1-100 KB): Minimal impact, recommended
- **Large** (> 1 MB): Consider optimization

### Optimization Tips

1. **Compress large data:**
```python
import gzip
compressed = gzip.compress(large_data.encode())
```

2. **Reference instead of embed:**
```python
# Instead of:
data = {"content": large_file_content}  # Bad

# Do:
data = {"content_path": "/path/to/file"}  # Good
```

3. **Selective saving:**
```python
# Only save what's needed for resumption
data = {
    "current_position": 1000,
    "batch_size": 100,
    # Don't save full results, recompute on resume
}
```

---

## Monitoring & Maintenance

### Cleanup Old Checkpoints

```sql
-- Delete checkpoints older than 30 days
DELETE FROM checkpoints
WHERE created_at < datetime('now', '-30 days')
  AND workflow_id NOT IN (
    SELECT id FROM workflows WHERE state IN ('running', 'pending')
  );
```

### Monitor Checkpoint Usage

```python
# Get checkpoint statistics
with db_manager.get_session() as session:
    total = session.query(Checkpoint).count()
    by_workflow = session.query(
        Checkpoint.workflow_id,
        func.count(Checkpoint.id)
    ).group_by(Checkpoint.workflow_id).all()

    avg_size = session.query(
        func.avg(func.length(Checkpoint.state_data))
    ).scalar()
```

---

## API Reference

### BaseAgent Methods

#### create_checkpoint()
```python
def create_checkpoint(
    self,
    name: str,
    data: Dict[str, Any],
    workflow_id: Optional[str] = None
) -> str
```
Create and persist a checkpoint.

**Raises:** `Exception` if serialization or database storage fails

---

#### restore_checkpoint()
```python
def restore_checkpoint(self, checkpoint_id: str) -> Dict[str, Any]
```
Restore a checkpoint and return its data.

**Raises:**
- `ValueError`: Checkpoint not found or integrity check failed
- `Exception`: Database or deserialization error

---

## Troubleshooting

### "Checkpoint not found"
- Verify checkpoint ID is correct
- Check if checkpoint was deleted
- Ensure database connection is active

### "Failed integrity check"
- Database corruption detected
- Do not use this checkpoint
- Restore from an earlier checkpoint

### "Cannot deserialize checkpoint"
- Checkpoint created with incompatible Python version
- pickle protocol mismatch
- Try restoring from a newer checkpoint

### Large Checkpoint Creation Failing
- Reduce data size
- Use compression
- Store large objects externally and save references

---

## Related Documentation

- [Admin API](./admin_api.md) - System checkpoint endpoints
- [Architecture](./architecture.md) - System design overview
- [Workflows](./workflows.md) - Workflow state management
- [Database](./development.md#database) - Database schema details
