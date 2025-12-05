# TBCV Workflows

This document describes the validation and enhancement workflows in TBCV.

## Overview

TBCV implements four main workflow types, orchestrated by the OrchestratorAgent:

1. **validate_file** - Single file validation
2. **validate_directory** - Batch directory validation
3. **full_validation** - Comprehensive validation with LLM
4. **content_update** - Enhancement workflow

## Workflow Architecture

```
User Request
    ↓
OrchestratorAgent (receives request)
    ↓
Create Workflow (persist to database)
    ↓
Execute Agent Pipeline (with concurrency gating)
    ↓
Store Results (database + cache)
    ↓
Return Response
```

## 1. Single File Validation (validate_file)

### Pipeline

```
1. TruthManagerAgent.load_truth_data(family)
   └─> Load plugin definitions and indexes

2. FuzzyDetectorAgent.detect_plugins(content, family)
   └─> Pattern matching + fuzzy algorithms
   └─> Returns detected plugins with confidences

3. ContentValidatorAgent.validate_content(content, validation_types)
   └─> YAML frontmatter validation
   └─> Markdown structure validation
   └─> Code block validation
   └─> Link validation
   └─> Truth validation (declared vs used plugins)

4. LLMValidatorAgent.validate_plugins(content, fuzzy_detections) [if enabled]
   └─> Semantic validation via Ollama
   └─> Confirm/upgrade/downgrade fuzzy findings
   └─> Identify missing plugins

5. RecommendationAgent.generate_recommendations(validation, content)
   └─> Generate actionable suggestions
   └─> Persist with "proposed" status

6. Store ValidationResult + Recommendations to database

7. Return aggregated result to user
```

### Configuration

```yaml
# config/main.yaml
orchestrator:
  max_file_workers: 4        # For batch processing
  retry_timeout_s: 120
  agent_limits:
    llm_validator: 1         # Only 1 LLM call at a time
    content_validator: 2     # Max 2 concurrent validations
```

### API Example

```bash
curl -X POST http://localhost:8080/api/validate \
  -H "Content-Type: application/json" \
  -d '{
    "content": "...",
    "file_path": "tutorial.md",
    "family": "words",
    "validation_types": ["yaml", "markdown", "code", "links", "truth"]
  }'
```

### CLI Example

```bash
python -m cli.main validate-file tutorial.md \
  --family words \
  --format json \
  --output results.json
```

### Response Format

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
      "suggestion": "Add 'title: Your Title'"
    }
  ],
  "plugins_detected": 3,
  "plugins_declared": 2,
  "recommendations_generated": 5
}
```

## 2. Directory Validation (validate_directory)

### Pipeline

```
1. Scan directory for files matching pattern (e.g., *.md)

2. Create worker pool (default: 4 workers)

3. For each file in parallel:
   └─> Run validate_file pipeline
   └─> Track progress in workflow metadata
   └─> Collect errors

4. Aggregate results:
   └─> files_total
   └─> files_validated (success)
   └─> files_failed (errors)
   └─> errors (list of error messages)

5. Update workflow state to "completed"

6. Return summary
```

### Configuration

```yaml
batch_processing:
  default_workers: 4
  max_workers: 16
  worker_timeout_seconds: 300
  file_patterns:
    - "*.md"
    - "*.markdown"
  exclude_patterns:
    - ".git/*"
    - "node_modules/*"
```

### API Example

```bash
curl -X POST http://localhost:8080/workflows/validate-directory \
  -H "Content-Type: application/json" \
  -d '{
    "directory_path": "./content",
    "file_pattern": "*.md",
    "workflow_type": "validate_file",
    "max_workers": 4,
    "family": "words"
  }'
```

### CLI Example

```bash
python -m cli.main validate-directory ./content \
  --pattern "*.md" \
  --workers 4 \
  --recursive \
  --format summary
```

### Response Format

```json
{
  "job_id": "job-xyz789",
  "workflow_id": "wf-abc123",
  "status": "started",
  "files_total": 45,
  "files_validated": 0,
  "files_failed": 0
}
```

### Polling for Status

```bash
curl http://localhost:8080/workflows/wf-abc123

# Returns:
{
  "workflow_id": "wf-abc123",
  "state": "running",
  "progress_percent": 60,
  "current_step": 27,
  "total_steps": 45,
  "files_validated": 27,
  "files_failed": 0,
  "errors": []
}
```

## 3. Full Validation (full_validation)

Same as `validate_file` but:
- Always enables LLM validation (ignores config)
- Uses two-stage mode (fuzzy → LLM)
- Higher thoroughness

### API Example

```bash
curl -X POST http://localhost:8080/workflows/start \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_type": "full_validation",
    "input_params": {
      "content": "...",
      "file_path": "tutorial.md",
      "confidence_threshold": 0.8
    }
  }'
```

## 4. Content Enhancement (content_update)

### Pipeline

```
1. Load ValidationResult by validation_id or file_path

2. Get approved recommendations (status="approved")

3. ContentEnhancerAgent.enhance_from_recommendations()
   └─> Safety gating:
       ├─> Check rewrite_ratio < 0.5
       └─> Check no blocked_topics present
   └─> Apply enhancements:
       ├─> Plugin hyperlinks (first mention only)
       ├─> Info text after code blocks
       └─> Approved recommendation edits
   └─> Generate diff

4. If preview_only=false:
   └─> Persist enhanced content
   └─> Mark recommendations as "applied"
   └─> Create AuditLog entries

5. Return enhanced content + diff + statistics
```

### API Example

```bash
curl -X POST http://localhost:8080/api/enhance \
  -H "Content-Type: application/json" \
  -d '{
    "validation_id": "val-abc123",
    "file_path": "tutorial.md",
    "content": "...",
    "recommendations": ["rec-1", "rec-2"],
    "preview": false
  }'
```

### CLI Example

```bash
python -m cli.main recommendations enhance tutorial.md \
  --validation-id val-abc123 \
  --backup \
  --output enhanced.md
```

### Response Format

```json
{
  "success": true,
  "message": "Applied 3 recommendations, skipped 1",
  "enhanced_content": "...",
  "diff": "--- original\n+++ enhanced\n...",
  "applied_count": 3,
  "skipped_count": 1,
  "results": [
    {
      "recommendation_id": "rec-1",
      "status": "applied",
      "reason": null
    },
    {
      "recommendation_id": "rec-2",
      "status": "skipped",
      "reason": "Safety gate: rewrite_ratio too high"
    }
  ]
}
```

## Validation Modes

The orchestrator supports three validation modes:

### 1. two_stage (Default)

```
FuzzyDetector → ContentValidator → LLMValidator
```

- Fuzzy detector identifies potential issues (heuristic)
- LLM validator confirms/adjusts (semantic)
- LLM can downgrade (confidence < 0.2), confirm (0.2-0.8), or upgrade (>0.8)

### 2. heuristic_only

```
FuzzyDetector → ContentValidator
```

- Skip LLM validation entirely
- Faster but less accurate
- Use when Ollama unavailable or for quick scans

### 3. llm_only

```
ContentValidator → LLMValidator
```

- Skip fuzzy detection
- LLM analyzes content directly
- Slower but potentially more thorough

### Configuration

```yaml
# config/main.yaml
validation:
  mode: "two_stage"  # or "heuristic_only" or "llm_only"
  llm_thresholds:
    downgrade: 0.2   # LLM confidence < 0.2 → downgrade severity
    confirm: 0.5     # 0.2-0.8 → confirm
    upgrade: 0.8     # > 0.8 → upgrade severity
```

## Concurrency Control

The orchestrator uses per-agent semaphores to prevent overload:

```python
# Default limits
agent_limits:
  llm_validator: 1      # Only 1 LLM call at a time
  content_validator: 2  # Max 2 concurrent validations
  truth_manager: 4      # Max 4 truth lookups
  fuzzy_detector: 2     # Max 2 fuzzy detections
```

### Behavior

- When agent is busy (semaphore locked), orchestrator waits
- Exponential backoff: 0.5s → 1s → 2s → 4s → 8s (max)
- Timeout after `retry_timeout_s` (default: 120 seconds)
- If timeout, workflow fails with error

### Example Trace

```
[0.0s] Request validate_file for tutorial.md
[0.0s] Acquiring llm_validator semaphore... LOCKED (busy)
[0.5s] Retry... still locked
[1.5s] Retry... still locked
[3.5s] Acquired semaphore, proceeding
[3.8s] LLM validation complete, releasing semaphore
```

## Workflow State Management

### States

- **PENDING** - Created, not started
- **RUNNING** - In progress
- **PAUSED** - Manually paused
- **COMPLETED** - Successfully finished
- **FAILED** - Error occurred
- **CANCELLED** - Manually cancelled

### State Transitions

```
PENDING → RUNNING → COMPLETED
    ↓         ↓          ↓
    └─────> PAUSED → RUNNING
              ↓
          CANCELLED

RUNNING → FAILED (on error)
```

### Control Endpoints

```bash
# Pause workflow
curl -X POST http://localhost:8080/workflows/wf-123/control \
  -d '{"action": "pause"}'

# Resume workflow
curl -X POST http://localhost:8080/workflows/wf-123/control \
  -d '{"action": "resume"}'

# Cancel workflow
curl -X POST http://localhost:8080/workflows/wf-123/control \
  -d '{"action": "cancel"}'
```

## Checkpoints and Recovery

Workflows support comprehensive checkpointing and recovery mechanisms to ensure work is not lost due to failures, crashes, or interruptions.

### Checkpoint Types

TBCV uses two types of checkpoints:

#### 1. Workflow Checkpoints (Database)

Stored in the database and track workflow execution state:

```yaml
workflows:
  checkpoints:
    - "workflow_start"
    - "detection_start"
    - "fuzzy_analysis"
    - "validation_start"
    - "validation_complete"
    - "enhancement_start"
    - "enhancement_complete"
    - "workflow_complete"
```

Each checkpoint includes:
- Workflow ID and type
- Current step number
- Serialized state data
- Validation hash for integrity
- Timestamp
- Resume capability flag

#### 2. System Checkpoints (File-based)

Complete system snapshots including:
- Full database backup
- Cache statistics
- System metadata
- Creation timestamp

### Creating Checkpoints

#### Automatic Checkpoints

Workflows automatically create checkpoints at key stages:

```python
# Checkpoint created automatically after each major step
db_manager.create_checkpoint(
    workflow_id=workflow_id,
    name="step_1_complete",
    step_number=1,
    state_data=serialized_state,
    validation_hash=compute_hash(state)
)
```

#### Manual Checkpoints

Create system checkpoints manually:

```bash
# CLI
python -m tbcv system checkpoints create --name "pre_upgrade_backup"

# API
curl -X POST http://localhost:8080/api/checkpoints \
  -d '{"name": "manual_checkpoint", "metadata": {"reason": "before_maintenance"}}'
```

### Recovery Operations

#### List Available Checkpoints

```bash
# List workflow checkpoints
python -m tbcv workflow checkpoints <workflow_id>

# API
curl http://localhost:8080/api/workflows/<workflow_id>/checkpoints
```

Response:
```json
{
  "workflow_id": "wf-123",
  "checkpoints": [
    {
      "id": "cp-001",
      "name": "step_1_complete",
      "step_number": 1,
      "created_at": "2024-01-15T10:30:00Z",
      "can_resume_from": true
    }
  ]
}
```

#### Recover from Checkpoint

```bash
# CLI - Recover from specific checkpoint
python -m tbcv workflow recover <workflow_id> --checkpoint-id <checkpoint_id>

# CLI - Auto-resume from latest checkpoint
python -m tbcv workflow resume <workflow_id>

# API
curl -X POST http://localhost:8080/api/workflows/<workflow_id>/recover \
  -d '{"checkpoint_id": "cp-002"}'
```

#### Rollback to Previous State

```bash
# Rollback to earlier checkpoint
python -m tbcv workflow rollback <workflow_id> --checkpoint-id <checkpoint_id>

# API
curl -X POST http://localhost:8080/api/workflows/<workflow_id>/rollback \
  -d '{"checkpoint_id": "cp-001"}'
```

### Recovery Scenarios

#### Scenario 1: System Crash During Workflow

```bash
# 1. Identify failed workflow
python -m tbcv workflow list --state failed

# 2. List available checkpoints
python -m tbcv workflow checkpoints wf-123

# 3. Resume from latest checkpoint
python -m tbcv workflow resume wf-123
```

#### Scenario 2: Workflow Error at Specific Step

```bash
# 1. Check workflow status
python -m tbcv workflow status wf-123

# 2. Find checkpoint before failure
python -m tbcv workflow checkpoints wf-123

# 3. Recover from checkpoint before error
python -m tbcv workflow recover wf-123 --checkpoint-id cp-002
```

#### Scenario 3: Need to Revert Changes

```bash
# 1. List checkpoints to find desired state
python -m tbcv workflow checkpoints wf-123

# 2. Rollback to earlier checkpoint
python -m tbcv workflow rollback wf-123 --checkpoint-id cp-001

# 3. Continue from that point
python -m tbcv workflow resume wf-123
```

### Checkpoint Validation

Always validate checkpoints before recovery:

```python
from core.checkpoint_manager import CheckpointManager

checkpoint_mgr = CheckpointManager()

# Validate checkpoint integrity
if checkpoint_mgr.validate_checkpoint(checkpoint_id):
    # Safe to recover
    checkpoint_mgr.recover_from_checkpoint(checkpoint_id)
else:
    # Try previous checkpoint or report error
    print("Checkpoint validation failed")
```

### Checkpoint Management

#### Cleanup Old Checkpoints

```python
# Keep only last 3 checkpoints
with db_manager.get_session() as session:
    checkpoints = session.query(Checkpoint).filter(
        Checkpoint.workflow_id == workflow_id
    ).order_by(Checkpoint.step_number).all()

    # Delete all but last 3
    for cp in checkpoints[:-3]:
        session.delete(cp)
    session.commit()
```

#### Checkpoint Retention Policy

```yaml
# config/main.yaml
checkpoints:
  retention:
    keep_completed: 3        # Keep 3 most recent for completed workflows
    keep_failed: 10          # Keep 10 most recent for failed workflows
    max_age_days: 30         # Delete checkpoints older than 30 days
    auto_cleanup: true       # Automatically cleanup old checkpoints
```

### Recovery Best Practices

1. **Checkpoint Frequently**: Create checkpoints after expensive operations
   ```python
   # After processing a batch
   if processed_count % batch_size == 0:
       create_checkpoint(workflow_id, f"batch_{batch_num}")
   ```

2. **Validate Before Recovery**: Always validate checkpoint integrity
   ```python
   if checkpoint_mgr.validate_checkpoint(cp_id):
       checkpoint_mgr.recover_from_checkpoint(cp_id)
   ```

3. **Keep Recent Checkpoints**: Don't delete until workflow completes
   ```python
   if workflow.state == WorkflowState.COMPLETED:
       cleanup_old_checkpoints(workflow_id, keep_last=3)
   ```

4. **Test Recovery**: Periodically test recovery process
   ```bash
   pytest tests/workflows/test_checkpoint_recovery.py -v
   ```

5. **Monitor Recovery Success**: Track recovery metrics
   ```python
   recovery_metrics = {
       "total_recoveries": 100,
       "successful_recoveries": 95,
       "success_rate": 95.0
   }
   ```

### Recovery Troubleshooting

**Checkpoint Not Found:**
- List all checkpoints: `python -m tbcv workflow checkpoints <workflow_id>`
- Verify checkpoint ID is correct
- Check database connectivity
- Try earlier checkpoint

**Corrupted Checkpoint:**
- Try previous checkpoint
- Restore from system checkpoint
- Check disk integrity
- Restart workflow if necessary

**Recovery Fails:**
- Check workflow state: `python -m tbcv workflow status <workflow_id>`
- Verify database connection
- Check system logs
- Reset workflow: `python -m tbcv workflow reset <workflow_id>`

For detailed recovery procedures and troubleshooting, see:
- [Workflow Recovery Guide](workflow_recovery.md) - Complete recovery documentation
- [Troubleshooting Guide](troubleshooting.md) - General troubleshooting

## Error Handling

### Workflow-Level Errors

```json
{
  "workflow_id": "wf-123",
  "state": "failed",
  "error_message": "Timeout waiting for llm_validator agent",
  "failed_at": "2024-01-15T10:30:00Z"
}
```

### File-Level Errors (Batch Processing)

```json
{
  "workflow_id": "wf-123",
  "state": "completed",
  "files_total": 10,
  "files_validated": 8,
  "files_failed": 2,
  "errors": [
    "tutorial1.md: FileNotFoundError",
    "tutorial2.md: ValidationTimeout"
  ]
}
```

### Error Recovery

- Individual file failures don't stop batch processing
- Workflow continues with `files_failed` counter
- Errors collected in `errors` array
- Final state: "completed" (with partial failures) or "failed" (critical error)

## Performance Optimization

### Caching Strategy

- Truth data cached for 7 days
- Fuzzy detection results cached for 24 hours
- Validation results cached for 30 minutes
- L1 (memory) + L2 (disk) caching

### Batch Processing Tips

```bash
# Small files: increase workers
--workers 8

# Large files: decrease workers to avoid memory pressure
--workers 2

# Mixed sizes: use default (4 workers)
```

### LLM Optimization

```yaml
# Disable LLM for speed
validation:
  mode: "heuristic_only"

# Or increase timeout for thorough analysis
llm_validator:
  timeout_seconds: 60
```

## Workflow Control: Pause and Resume

Long-running workflows can be paused and resumed at any time, allowing you to manage system resources and control workflow execution.

### Pause a Workflow

Pauses an active (running or pending) workflow. The workflow progress is preserved and can be resumed later.

**API Endpoint:**
```bash
POST /api/workflows/{workflow_id}/pause
```

**Example:**
```bash
curl -X POST http://localhost:8080/api/workflows/wf-abc123/pause
```

**Response:**
```json
{
  "success": true,
  "workflow_id": "wf-abc123",
  "state": "paused",
  "progress_percent": 45,
  "current_step": 45,
  "total_steps": 100,
  "message": "Workflow paused successfully"
}
```

**CLI Example:**
```bash
python -m cli.main workflow pause wf-abc123
```

### Resume a Workflow

Resumes a paused workflow from where it left off. All progress metrics are preserved.

**API Endpoint:**
```bash
POST /api/workflows/{workflow_id}/resume
```

**Example:**
```bash
curl -X POST http://localhost:8080/api/workflows/wf-abc123/resume
```

**Response:**
```json
{
  "success": true,
  "workflow_id": "wf-abc123",
  "state": "running",
  "progress_percent": 45,
  "current_step": 45,
  "total_steps": 100,
  "message": "Workflow resumed successfully"
}
```

**CLI Example:**
```bash
python -m cli.main workflow resume wf-abc123
```

### Supported States

**Can be paused:**
- RUNNING - Currently executing
- PENDING - Queued and waiting to start

**Cannot be paused:**
- COMPLETED - Already finished
- FAILED - Execution failed
- CANCELLED - Already cancelled
- PAUSED - Already paused (idempotent)

**Can be resumed:**
- PAUSED - Currently paused

**Cannot be resumed:**
- RUNNING - Already running
- COMPLETED - Already finished
- FAILED - Execution failed
- CANCELLED - Already cancelled

### Progress Preservation

When a workflow is paused and resumed:

- **Progress metrics preserved:** current_step, total_steps, progress_percent
- **Metadata preserved:** input_params, workflow_metadata, created_at
- **State preserved:** No data loss during pause/resume cycle
- **Results preserved:** Partial results already computed are retained

### Concurrent Pause/Resume

Multiple workflows can be paused and resumed concurrently. Each operation is thread-safe and atomic.

**Example - Pause all running workflows:**
```bash
# Get all running workflows
workflows=$(curl http://localhost:8080/api/workflows?state=running | jq -r '.[].id')

# Pause each one
for wf_id in $workflows; do
  curl -X POST http://localhost:8080/api/workflows/$wf_id/pause &
done
wait

# All workflows are now paused
```

**Example - Resume all paused workflows:**
```bash
# Get all paused workflows
workflows=$(curl http://localhost:8080/api/workflows?state=paused | jq -r '.[].id')

# Resume each one
for wf_id in $workflows; do
  curl -X POST http://localhost:8080/api/workflows/$wf_id/resume &
done
wait

# All workflows are now running
```

### Error Handling

**Invalid state transitions:**
```json
{
  "success": false,
  "error": "Cannot pause workflow in state: completed. Only running/pending workflows can be paused",
  "workflow_id": "wf-abc123"
}
```

**Workflow not found:**
```json
{
  "success": false,
  "error": "Workflow wf-notfound not found",
  "workflow_id": "wf-notfound"
}
```

## Monitoring Workflows

### List All Workflows

```bash
curl http://localhost:8080/api/workflows?state=running&limit=50
```

### Workflow Statistics

```bash
curl http://localhost:8080/api/workflows/wf-123
```

Returns:
```json
{
  "workflow_id": "wf-123",
  "type": "validate_directory",
  "state": "completed",
  "started_at": "2024-01-15T10:00:00Z",
  "completed_at": "2024-01-15T10:05:30Z",
  "duration_seconds": 330,
  "pages_processed": 45,
  "validations_found": 45,
  "validations_approved": 30,
  "recommendations_generated": 120,
  "recommendations_approved": 80,
  "recommendations_actioned": 60
}
```

### Real-Time Updates

```javascript
// WebSocket
const ws = new WebSocket('ws://localhost:8080/ws/wf-123');
ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log(`Progress: ${update.progress_percent}%`);
};

// Server-Sent Events (SSE)
const eventSource = new EventSource('http://localhost:8080/api/stream/updates?topic=wf-123');
eventSource.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log(update);
};
```

## Best Practices

1. **Start small**: Test with single files before batch processing
2. **Monitor progress**: Use WebSocket/SSE for real-time updates
3. **Tune workers**: Adjust based on file sizes and available memory
4. **Enable caching**: Improves performance for repeated validations
5. **Use preview mode**: Test enhancements before applying
6. **Check logs**: Review `data/logs/tbcv.log` for errors
7. **Backup content**: Always backup before enhancement

## Troubleshooting

**Workflow stuck in RUNNING:**
```bash
# Check workflow status
curl http://localhost:8080/workflows/wf-123

# Cancel if needed
curl -X POST http://localhost:8080/workflows/wf-123/control -d '{"action":"cancel"}'
```

**Agent timeout:**
```yaml
# Increase timeout in config
orchestrator:
  retry_timeout_s: 300  # 5 minutes
```

**Memory issues during batch:**
```yaml
# Reduce workers
orchestrator:
  max_file_workers: 2

# Or set memory limit
performance:
  memory_limit_per_worker_mb: 256
```

See [Troubleshooting Guide](troubleshooting.md) for more solutions.
