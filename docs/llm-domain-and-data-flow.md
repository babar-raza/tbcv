# TBCV Domain Model & Data Flow (Code-Based Evidence)

**Generated:** 2025-12-03
**Source:** Direct code inspection only
**Purpose:** Document domain entities, relationships, and data flows discovered in code

---

## Overview

This document describes the **domain model** and **data flows** of the TBCV system, based exclusively on code evidence from:
- Database models in `core/database.py`
- Agent imports in `api/server.py` and `cli/main.py`
- Configuration in `config/*.yaml`
- Import chains and type definitions

---

## Domain Entities (From Database Schema)

**Source:** [core/database.py](core/database.py) Lines 111-415

### Entity Relationship Diagram (Code-Derived)

```
Workflow (1) ----< (M) ValidationResult
   |                         |
   |                         |
   | (1)                     | (1)
   |                         |
   v                         v
   (M) Checkpoint            (M) Recommendation
                                  |
                                  | (1)
                                  v
                                  (M) AuditLog

CacheEntry (standalone)
MetricEntry (standalone)
```

---

## Entity 1: Workflow

**Purpose:** Orchestrate multi-step validation and enhancement processes

**Table:** `workflows` (Line 112)
**Primary Key:** `id` (UUID String(36))

### Attributes
| Column | Type | Purpose | Indexed |
|--------|------|---------|---------|
| `id` | String(36) | UUID primary key | PK |
| `type` | String(50) | Workflow type (e.g., "validate_file", "enhance_batch") | Yes |
| `state` | Enum(WorkflowState) | Current state | Yes |
| `input_params` | JSONField | Input parameters | No |
| `created_at` | DateTime | Creation timestamp | Yes |
| `updated_at` | DateTime | Last update timestamp | No |
| `completed_at` | DateTime | Completion timestamp | No |
| `metadata` | JSONField | Additional metadata | No |
| `total_steps` | Integer | Total steps in workflow | No |
| `current_step` | Integer | Current step number | No |
| `progress_percent` | Integer | Progress percentage (0-100) | No |
| `error_message` | Text | Error message if failed | No |

### State Machine (Line 82-88)
```python
class WorkflowState(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
```

**State Transitions (Inferred from states):**
```
PENDING → RUNNING → COMPLETED
    ↓        ↓           ↓
    ↓     PAUSED      FAILED
    ↓        ↓
    ↓────→ CANCELLED
```

### Relationships
- **ONE workflow** HAS MANY **checkpoints** (Line 127, cascade delete)
- **ONE workflow** HAS MANY **validation_results** (Line 128, no cascade)

### Composite Indexes (Lines 130-133)
1. `idx_workflows_state_created` (state, created_at)
2. `idx_workflows_type_state` (type, state)

**Usage Pattern:** Query workflows by state and creation time, or by type and state

---

## Entity 2: Checkpoint

**Purpose:** Save workflow state for pause/resume capability

**Table:** `checkpoints` (Line 154)
**Primary Key:** `id` (UUID String(36))
**Foreign Key:** `workflow_id` → workflows.id

### Attributes
| Column | Type | Purpose |
|--------|------|---------|
| `id` | String(36) | UUID primary key |
| `workflow_id` | String(36) | Parent workflow (indexed) |
| `name` | String(100) | Checkpoint name |
| `step_number` | Integer | Step number in workflow |
| `state_data` | LargeBinary | Serialized state data |
| `created_at` | DateTime | Creation timestamp |
| `validation_hash` | String(32) | State validation hash (MD5) |
| `can_resume_from` | Boolean | Whether resumption is safe |

### Index (Line 167)
`idx_checkpoints_workflow_step` (workflow_id, step_number)

**Usage Pattern:** Retrieve checkpoints by workflow and step for resume operations

---

## Entity 3: CacheEntry

**Purpose:** L2 (disk) cache for agent method results

**Table:** `cache_entries` (Line 183)
**Primary Key:** `cache_key` (String(200))

### Attributes
| Column | Type | Purpose | Indexed |
|--------|------|---------|---------|
| `cache_key` | String(200) | Composite cache key | PK |
| `agent_id` | String(100) | Agent identifier | Yes |
| `method_name` | String(100) | Method name | Yes |
| `input_hash` | String(64) | Hash of input parameters (SHA256) | No |
| `result_data` | LargeBinary | Serialized result | No |
| `created_at` | DateTime | Creation timestamp | No |
| `expires_at` | DateTime | Expiration timestamp | Yes |
| `access_count` | Integer | Access counter (default 1) | No |
| `last_accessed` | DateTime | Last access timestamp | No |
| `size_bytes` | Integer | Result data size | No |

### Indexes (Lines 196-199)
1. `idx_cache_expires` (expires_at) - For TTL cleanup
2. `idx_cache_agent_method` (agent_id, method_name) - For lookup

**Cache Key Format (Inferred):**
`{agent_id}:{method_name}:{input_hash}`

**TTL Configuration (from config/main.yaml:73-74):**
- Truth Manager: 604800 seconds (7 days)
- Fuzzy Detector: Likely 24 hours (from README claim, unverified)
- Validators: Likely 30 minutes (from README claim, unverified)

---

## Entity 4: MetricEntry

**Purpose:** Store performance metrics and system measurements

**Table:** `metrics` (Line 204)
**Primary Key:** `id` (UUID String(36))

### Attributes
| Column | Type | Purpose | Indexed |
|--------|------|---------|---------|
| `id` | String(36) | UUID primary key | PK |
| `name` | String(100) | Metric name | Yes |
| `value` | Float | Metric value | No |
| `created_at` | DateTime | Measurement timestamp | Yes |
| `metadata` | JSONField | Additional context | No |

**Usage Pattern:** Time-series metrics storage with name-based queries

**Integration:** Likely used with prometheus-client (from requirements.txt)

---

## Entity 5: ValidationResult

**Purpose:** Store validation outcomes for files/content

**Table:** `validation_results` (Line 215)
**Primary Key:** `id` (UUID String(36))
**Foreign Keys:**
- `workflow_id` → workflows.id (nullable)
- `parent_validation_id` → validation_results.id (nullable, for re-validation)

### Attributes
| Column | Type | Purpose | Indexed |
|--------|------|---------|---------|
| `id` | String(36) | UUID primary key | PK |
| `workflow_id` | String(36) | Parent workflow (nullable) | Yes |
| `file_path` | String(1024) | Path to validated file | Yes |
| `rules_applied` | JSONField | List of rules used | No |
| `validation_results` | JSONField | Validation outcomes by type | No |
| `validation_types` | JSONField | Types run (e.g., ["yaml", "markdown", "Truth"]) | No |
| `parent_validation_id` | String(36) | Previous validation (re-validation feature) | No |
| `comparison_data` | JSONField | Comparison with parent (re-validation) | No |
| `notes` | Text | Additional notes | No |
| `severity` | String(20) | Severity level | Yes |
| `status` | Enum(ValidationStatus) | Validation status | Yes |
| `content_hash` | String(64) | Hash of content validated (SHA256) | Yes |
| `ast_hash` | String(64) | AST hash (for code) | No |
| `run_id` | String(64) | Batch run identifier | Yes |
| `file_hash` | String(64) | Hash of actual file (for history) | Yes |
| `version_number` | Integer | Version number (default 1) | No |
| `created_at` | DateTime | Creation timestamp | Yes |
| `updated_at` | DateTime | Last update timestamp | No |

### Status Enum (Lines 72-79)
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

### Relationships
- **MANY ValidationResults** BELONG TO **ONE workflow** (Line 246)
- **ONE ValidationResult** HAS MANY **recommendations** (Line 247, cascade delete)
- **ONE ValidationResult** MAY REFERENCE **ONE parent ValidationResult** (Line 225, for re-validation)

### Indexes (Lines 249-253)
1. `idx_validation_file_status` (file_path, status)
2. `idx_validation_file_severity` (file_path, severity)
3. `idx_validation_created` (created_at)

**Usage Patterns:**
- Query validations by file and status
- Find all validations for a file sorted by severity
- Time-based queries on created_at
- Re-validation: Compare current validation with parent via `parent_validation_id`

---

## Entity 6: Recommendation

**Purpose:** Store improvement suggestions for human approval

**Table:** `recommendations` (Line 289)
**Primary Key:** `id` (UUID String(36))
**Foreign Key:** `validation_id` → validation_results.id

### Attributes
| Column | Type | Purpose | Indexed |
|--------|------|---------|---------|
| `id` | String(36) | UUID primary key | PK |
| `validation_id` | String(36) | Parent validation | Yes |
| `type` | String(50) | Recommendation type | Yes |
| `title` | String(200) | Short title | No |
| `description` | Text | Detailed description | No |
| `scope` | String(200) | Target scope (e.g., "line:42") | No |
| `instruction` | Text | Actionable instruction | No |
| `rationale` | Text | Why this fixes the issue | No |
| `severity` | String(20) | Severity (critical/high/medium/low) | No |
| `original_content` | Text | Before state | No |
| `proposed_content` | Text | After state | No |
| `diff` | Text | Unified diff | No |
| `confidence` | Float | Confidence score (0.0-1.0) | No |
| `priority` | String(20) | Priority (low/medium/high/critical) | No |
| `status` | Enum(RecommendationStatus) | Approval status | Yes |
| `reviewed_by` | String(100) | Reviewer name | No |
| `reviewed_at` | DateTime | Review timestamp | No |
| `review_notes` | Text | Reviewer notes | No |
| `applied_at` | DateTime | Application timestamp | No |
| `applied_by` | String(100) | Who applied it | No |
| `created_at` | DateTime | Creation timestamp | Yes |
| `updated_at` | DateTime | Last update timestamp | No |
| `metadata` | JSONField | Additional metadata | No |

### Status Enum (Lines 64-69)
```python
class RecommendationStatus(enum.Enum):
    PROPOSED = "proposed"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
```

### Recommendation Types (from code comment Line 294)
- `link_plugin` - Add plugin hyperlink
- `fix_format` - Fix formatting issue
- `add_info_text` - Add informational text
- (Others to be discovered)

### State Machine (Inferred)
```
PROPOSED → PENDING → APPROVED → APPLIED
              ↓
           REJECTED
```

### Relationships
- **MANY Recommendations** BELONG TO **ONE ValidationResult** (Line 332)
- **ONE Recommendation** HAS MANY **AuditLogs** (Line 333, cascade delete)

### Indexes (Lines 335-339)
1. `idx_recommendations_status` (status)
2. `idx_recommendations_validation` (validation_id, status)
3. `idx_recommendations_type` (type)

**Usage Patterns:**
- List all recommendations by status
- Find recommendations for a validation by status
- Filter recommendations by type

---

## Entity 7: AuditLog

**Purpose:** Immutable audit trail for all changes

**Table:** `audit_logs` (Line 375)
**Primary Key:** `id` (UUID String(36))
**Foreign Key:** `recommendation_id` → recommendations.id (nullable)

### Attributes
| Column | Type | Purpose | Indexed |
|--------|------|---------|---------|
| `id` | String(36) | UUID primary key | PK |
| `recommendation_id` | String(36) | Related recommendation (nullable) | Yes |
| `action` | String(50) | Action type | Yes |
| `actor` | String(100) | Who performed action | No |
| `actor_type` | String(20) | user / system / agent | No |
| `before_state` | JSONField | State before change | No |
| `after_state` | JSONField | State after change | No |
| `changes` | JSONField | Specific changes made | No |
| `notes` | Text | Additional notes | No |
| `created_at` | DateTime | Action timestamp | Yes |
| `metadata` | JSONField | Additional metadata | No |

### Action Types (from code comment Line 379)
- `created` - Entity created
- `approved` - Recommendation approved
- `rejected` - Recommendation rejected
- `applied` - Recommendation applied
- `modified` - Entity modified

### Actor Types (Line 381)
- `user` - Human user
- `system` - System-initiated action
- `agent` - AI agent action

### Relationships
- **MANY AuditLogs** BELONG TO **ONE Recommendation** (Line 394)

### Indexes (Lines 396-399)
1. `idx_audit_action` (action)
2. `idx_audit_created` (created_at)

**Usage Pattern:** Immutable event log for compliance and debugging

---

## Data Flows (Code-Inferred)

### Flow 1: Single File Validation

**Entry Point:** `python -m tbcv validate-file FILE_PATH` or `POST /api/validate`

**Sequence (from code):**

1. **CLI/API receives request** (cli/main.py:154 or api/server.py)
   - Input: file_path, family, validation_types
   - Language check: `is_english_content(file_path)` (cli/main.py:157)

2. **MCP Client called** (cli/main.py:172)
   ```python
   result = mcp_client.validate_file(file_path, family, validation_types)
   ```

3. **MCP Server handles request** (svc/mcp_server.py:98)
   - Method: `ValidationMethods.validate_file`
   - Creates or finds workflow (inferred)

4. **Workflow created** (core/database.py:Workflow)
   - State: PENDING → RUNNING
   - Type: "validate_file"
   - Input params stored

5. **Agents invoked** (from agent imports)
   - **TruthManagerAgent**: Load plugin definitions from `truth/`
   - **FuzzyDetectorAgent**: Detect plugin usage patterns (if enabled)
   - **Modular Validators**: Execute in tiers (config/validation_flow.yaml)

**Tier 1 (parallel):**
   - YamlValidatorAgent
   - MarkdownValidatorAgent
   - StructureValidatorAgent

**Tier 2 (parallel):**
   - CodeValidatorAgent
   - LinkValidatorAgent
   - SeoValidatorAgent

**Tier 3 (sequential, with dependencies):**
   - FuzzyDetectorAgent (fuzzy matching)
   - TruthValidatorAgent (uses fuzzy results)
   - LLMValidatorAgent (optional, uses truth results)

6. **ValidationResult created** (core/database.py:ValidationResult)
   - Linked to workflow
   - Contains aggregated results from all validators
   - Status: PASS / FAIL / WARNING
   - Severity: Highest severity found

7. **Recommendations generated** (agents/recommendation_agent.py inferred)
   - RecommendationAgent analyzes validation failures
   - Creates Recommendation entities
   - Status: PENDING
   - Linked to ValidationResult

8. **Workflow completed**
   - State: RUNNING → COMPLETED
   - Progress: 100%
   - completed_at timestamp set

9. **Response returned**
   - ValidationResult.to_dict()
   - Includes recommendations_count

### Flow 2: Human-in-the-Loop Recommendation Approval

**Entry Point:** Web Dashboard or CLI

**Sequence:**

1. **User views recommendations**
   - Query: SELECT * FROM recommendations WHERE validation_id = ? AND status = 'PENDING'

2. **User reviews recommendation**
   - Views: title, description, original_content, proposed_content, diff

3. **User approves/rejects** (api endpoint or CLI command)
   - Action: `POST /api/recommendations/{id}/review`
   - Body: `{status: "approved", reviewer: "john", notes: "LGTM"}`

4. **AuditLog created** (core/database.py:AuditLog)
   - action: "approved" or "rejected"
   - actor: reviewer name
   - actor_type: "user"
   - before_state: {status: "pending"}
   - after_state: {status: "approved"}

5. **Recommendation updated**
   - status: PENDING → APPROVED
   - reviewed_by: reviewer name
   - reviewed_at: timestamp
   - review_notes: notes

### Flow 3: Content Enhancement (Applying Recommendations)

**Entry Point:** `python -m tbcv enhance FILE_PATH` or `POST /api/enhance`

**Sequence:**

1. **Enhancement request**
   - Input: validation_id, file_path, recommendations (optional list of IDs)

2. **Filter recommendations**
   - Query: SELECT * FROM recommendations WHERE validation_id = ? AND status = 'APPROVED'
   - If specific IDs provided: AND id IN (...)

3. **EnhancementAgent invoked** (agents/enhancement_agent.py inferred)
   - Loads file content
   - Applies approved recommendations sequentially
   - Validates safety gates (config/main.yaml:56-60):
     - rewrite_ratio_threshold: 0.5 (max ±50% content change)
     - blocked_topics: ["forbidden"]

4. **EditValidatorAgent invoked** (agents/edit_validator.py)
   - Validates before/after states
   - Ensures changes match recommendations

5. **For each applied recommendation:**
   - Update recommendation:
     - status: APPROVED → APPLIED
     - applied_at: timestamp
     - applied_by: actor
   - Create AuditLog:
     - action: "applied"
     - before_state: original file content
     - after_state: enhanced file content

6. **Enhanced content returned**
   - May be preview (preview=True) or actual file write

7. **ValidationResult updated** (optional)
   - status: PASS/FAIL → ENHANCED
   - updated_at: timestamp

### Flow 4: Workflow Checkpointing

**Entry Point:** Long-running workflow (e.g., batch validation)

**Sequence (inferred from schema):**

1. **Workflow starts**
   - State: PENDING → RUNNING
   - total_steps set

2. **At each significant step:**
   - current_step incremented
   - progress_percent calculated: (current_step / total_steps) * 100

3. **Checkpoint created** (every N seconds, config/main.yaml:67)
   ```python
   checkpoint_interval_seconds: 30
   ```
   - Serializes workflow state to checkpoint.state_data
   - Computes validation_hash (MD5)
   - Sets can_resume_from = True

4. **If workflow paused/interrupted:**
   - State: RUNNING → PAUSED

5. **Resume workflow:**
   - Query: SELECT * FROM checkpoints WHERE workflow_id = ? ORDER BY step_number DESC LIMIT 1
   - Deserialize state_data
   - Validate hash
   - Check can_resume_from
   - Continue from current_step

6. **Workflow completes:**
   - State: RUNNING → COMPLETED
   - completed_at set
   - Checkpoints retained for audit

---

## Configuration-Driven Data Flow

**Source:** [config/validation_flow.yaml](config/validation_flow.yaml)

### Validator Orchestration (Lines 5-62)

**Profile:** `default` (Line 7)

**Tier Execution:**
1. **Tier 1: Quick Checks** (Lines 26-36)
   - Parallel: true
   - Timeout: 30s
   - Validators: yaml, markdown, structure

2. **Tier 2: Content Analysis** (Lines 38-48)
   - Parallel: true
   - Timeout: 60s
   - Validators: code, links, seo, heading_sizes

3. **Tier 3: Advanced Validation** (Lines 50-61)
   - Parallel: false (sequential)
   - Timeout: 120s
   - Validators: FuzzyLogic, Truth, llm
   - Respects dependencies

**Dependencies (Lines 65-69):**
```yaml
Truth: [FuzzyLogic]  # Truth needs fuzzy results
llm: [Truth]          # LLM needs truth data
```

**Early Termination (Lines 12-14):**
- If critical errors >= 3: stop validation
- Setting: `max_critical_errors: 3`

---

## Agent Communication Pattern (Inferred)

**From code imports and registration:**

**Agent Registry Pattern:**
```python
# agents/base.py (inferred)
agent_registry.register_agent(agent_instance)
```

**Agent Invocation:**
1. Orchestrator receives workflow
2. Looks up agents by ID from registry
3. Calls agent methods (synchronous or async)
4. Agents return results
5. Orchestrator aggregates

**Cache Integration:**
- Agents check L1 cache (in-memory)
- If miss, check L2 cache (database:cache_entries)
- If miss, execute and store
- TTL enforced via expires_at

---

## Summary: Domain Model

**Entities: 7**
1. Workflow - Orchestration
2. Checkpoint - State persistence
3. CacheEntry - Performance
4. MetricEntry - Monitoring
5. ValidationResult - Validation outcomes
6. Recommendation - Improvement suggestions
7. AuditLog - Audit trail

**Relationships:**
- Workflow → ValidationResult (1:M)
- Workflow → Checkpoint (1:M)
- ValidationResult → Recommendation (1:M)
- ValidationResult → ValidationResult (parent, 1:1)
- Recommendation → AuditLog (1:M)

**Key Workflows:**
1. Validation: File → ValidationResult → Recommendations
2. Approval: Recommendation PENDING → APPROVED/REJECTED (with AuditLog)
3. Enhancement: APPROVED Recommendations → Applied changes (with AuditLog)
4. Checkpointing: Long workflow → Periodic checkpoints → Resume capability

---

## Open Questions for Phase 2

1. **How does Orchestrator dispatch to agents?**
   - Need to read `agents/orchestrator.py`

2. **How do agents communicate results?**
   - Return values? Callbacks? Events?

3. **What is the actual format of validation_results JSON?**
   - Need to see agent implementations

4. **How does caching actually work?**
   - Need to read `core/cache.py`

5. **What triggers recommendation generation?**
   - Automatic after validation? Manual?
   - Need to read `agents/recommendation_agent.py`

6. **How is content actually enhanced?**
   - String replacement? AST manipulation?
   - Need to read `agents/enhancement_agent.py`

7. **What is LangChain used for?**
   - ChromaDB suggests vector embeddings
   - RAG configuration exists (config/rag.yaml)
   - Need to find usage in code

8. **What is the role of LLMValidatorAgent?**
   - Optional semantic validation
   - How does it use Ollama/Gemini?
   - Need to read `agents/llm_validator.py`

---

## Phase 2 Status: Foundational Understanding from Database

**Database schema: ✅ Complete**
**Data flows: 🟡 Inferred from schema and config**
**Agent implementations: ⏳ Not yet read**

**Next Phase Actions:**
- Deep-read all agent implementations
- Trace actual validation workflows in code
- Understand recommendation generation logic
- Map enhancement application process
