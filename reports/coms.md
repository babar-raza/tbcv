# Communication Architecture Analysis: Ensuring All Operations Use MCP

**Date**: 2025-11-30
**Status**: Architecture Analysis
**Purpose**: Analyze current operation flow and provide recommendations for routing all UI/CLI operations through MCP

---

## Executive Summary

Currently, TBCV has a **mixed architecture** where:
- **MCP Server exists** but is only partially utilized (4 methods: validate_folder, approve, reject, enhance)
- **API endpoints** mostly bypass MCP and call agents/database directly (only 3-4 endpoints use MCP with fallback)
- **CLI commands** completely bypass MCP and call agents/database directly
- **Result**: Inconsistent operation flow, difficult to maintain, no centralized control point

**Recommendation**: Implement a **unified MCP-first architecture** where all operations flow through MCP as the single source of truth.

---

## Current State Analysis

### 1. MCP Server (`svc/mcp_server.py`)

**Available Methods** (4 total):
```
1. validate_folder - Validates markdown files in a folder
2. approve - Approves validation records
3. reject - Rejects validation records
4. enhance - Enhances approved validations using LLM
```

**Architecture**:
```
MCPServer
  ├── DatabaseManager (direct access)
  ├── RuleManager (direct access)
  ├── MarkdownIngestion (direct access)
  └── OllamaClient (for enhancements)
```

**Usage Modes**:
- Stdio mode: `python -m svc.mcp_server` (for external tools)
- In-process mode: `create_mcp_client()` (for internal use)

**Current Limitations**:
- Only 4 methods vs ~50+ API endpoints
- No recommendation operations
- No workflow management
- No cache/admin operations
- No query/list operations
- Limited to basic CRUD on validations

### 2. API Server (`api/server.py`)

**Total Endpoints**: ~80 endpoints

**MCP Usage Analysis**:

| Operation Type | Uses MCP | Direct Access | Fallback Pattern |
|---------------|----------|---------------|------------------|
| Validation CRUD | ❌ No | ✅ Yes | N/A |
| Approve/Reject | ⚠️ Partial | ✅ Yes | Try MCP, fallback to direct |
| Enhancement | ⚠️ Partial | ✅ Yes | Try MCP, fallback to direct |
| Recommendations | ❌ No | ✅ Yes | N/A |
| Workflows | ❌ No | ✅ Yes | N/A |
| Admin/Cache | ❌ No | ✅ Yes | N/A |
| Health/Stats | ❌ No | ✅ Yes | N/A |
| Export | ❌ No | ✅ Yes | N/A |

**Example: Approve Endpoint** (lines 1833-1897):
```python
@app.post("/api/validations/{validation_id}/approve")
async def approve_validation(validation_id: str):
    # Try MCP first
    try:
        from svc.mcp_server import create_mcp_client
        mcp_client = create_mcp_client()
        response = mcp_client.handle_request({
            "method": "approve",
            "params": {"ids": [validation_id]},
            "id": 1
        })
        # Use MCP result
    except (ImportError, Exception):
        # Fallback: Direct database access
        db_manager.update_validation_status(validation_id, "approved")
```

**Problem**: Inconsistent - most endpoints skip MCP entirely and go straight to direct access.

**Direct Database Imports** (found in api/server.py):
```python
from core.database import db_manager  # Used ~50+ times
from core.cache import cache_manager  # Used ~15+ times
from agents.* import *  # Used throughout
```

### 3. CLI (`cli/main.py`)

**Total Commands**: ~30 commands across multiple groups

**MCP Usage**: **ZERO** ❌

**Current Architecture**:
```python
CLI Command
  └─→ Agent Registry (direct)
       └─→ OrchestratorAgent
            └─→ Validators/Enhancers
                 └─→ DatabaseManager
```

**Example: validate_file command** (lines 147-214):
```python
@cli.command()
def validate_file(file_path, family, types, output, output_format):
    orchestrator = agent_registry.get_agent("orchestrator")  # Direct access
    result = await orchestrator.process_request("validate_file", {...})
    # No MCP involved
```

**Direct Imports** (found in cli/main.py):
```python
from agents.base import agent_registry
from agents.orchestrator import OrchestratorAgent
from agents.truth_manager import TruthManagerAgent
from agents.content_validator import ContentValidatorAgent
from agents.content_enhancer import ContentEnhancerAgent
from agents.llm_validator import LLMValidatorAgent
from agents.recommendation_agent import RecommendationAgent
from core.database import db_manager  # Used ~30+ times
from core.cache import cache_manager  # Used ~10+ times
```

**Problem**: CLI has its own parallel implementation that duplicates logic from API endpoints.

---

## Gap Analysis

### Missing MCP Methods

To support full operation flow through MCP, the following methods need to be added:

#### Validation Operations (8 methods)
```
✅ validate_folder (exists)
❌ validate_file
❌ validate_content
❌ get_validation
❌ list_validations
❌ update_validation
❌ delete_validation
❌ revalidate
```

#### Approval Operations (4 methods)
```
✅ approve (exists)
✅ reject (exists)
❌ bulk_approve
❌ bulk_reject
```

#### Enhancement Operations (5 methods)
```
✅ enhance (exists)
❌ enhance_batch
❌ enhance_preview
❌ enhance_auto_apply
❌ get_enhancement_comparison
```

#### Recommendation Operations (8 methods)
```
❌ generate_recommendations
❌ rebuild_recommendations
❌ get_recommendations
❌ review_recommendation
❌ bulk_review_recommendations
❌ apply_recommendations
❌ delete_recommendation
❌ mark_recommendations_applied
```

#### Workflow Operations (8 methods)
```
❌ create_workflow
❌ get_workflow
❌ list_workflows
❌ control_workflow (pause/resume/cancel)
❌ get_workflow_report
❌ get_workflow_summary
❌ delete_workflow
❌ bulk_delete_workflows
```

#### Admin/Maintenance Operations (10 methods)
```
❌ get_system_status
❌ clear_cache
❌ get_cache_stats
❌ cleanup_cache
❌ rebuild_cache
❌ reload_agent
❌ run_gc
❌ enable_maintenance_mode
❌ disable_maintenance_mode
❌ create_checkpoint
```

#### Query/Stats Operations (6 methods)
```
❌ get_stats
❌ get_audit_log
❌ get_performance_report
❌ get_health_report
❌ get_validation_history
❌ get_available_validators
```

#### Export Operations (3 methods)
```
❌ export_validation
❌ export_recommendations
❌ export_workflow
```

**Total Missing**: 52 methods
**Total Existing**: 4 methods
**Coverage**: 7.1% (4/56)

---

## Recommended Architecture

### Target State: MCP-First Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interfaces                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │     CLI      │  │   REST API   │  │  Web Dashboard   │   │
│  │   (Click)    │  │  (FastAPI)   │  │     (HTML)       │   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────────┘   │
└─────────┼──────────────────┼──────────────────┼──────────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             ↓
          ┌──────────────────────────────────────────┐
          │          MCP Client Wrapper               │
          │  - Request formatting                     │
          │  - Response parsing                       │
          │  - Error handling                         │
          │  - Retry logic                            │
          └──────────────────┬───────────────────────┘
                             ↓
          ┌──────────────────────────────────────────┐
          │          MCP Server (Enhanced)            │
          │  ┌────────────────────────────────────┐   │
          │  │ JSON-RPC Handler                   │   │
          │  │  - Method routing                  │   │
          │  │  - Input validation                │   │
          │  │  - Authentication (future)         │   │
          │  │  - Rate limiting (future)          │   │
          │  └────────────────┬───────────────────┘   │
          │                   ↓                       │
          │  ┌────────────────────────────────────┐   │
          │  │ Method Handlers (56 total)         │   │
          │  │  - validate_*                      │   │
          │  │  - approve/reject                  │   │
          │  │  - enhance_*                       │   │
          │  │  - recommend_*                     │   │
          │  │  - workflow_*                      │   │
          │  │  - admin_*                         │   │
          │  │  - export_*                        │   │
          │  └────────────────┬───────────────────┘   │
          └───────────────────┼────────────────────────┘
                              ↓
          ┌──────────────────────────────────────────┐
          │      Business Logic Layer                │
          │  ┌────────────────────────────────────┐   │
          │  │  Agent Registry & Orchestration    │   │
          │  │  - OrchestratorAgent              │   │
          │  │  - ContentValidatorAgent          │   │
          │  │  - RecommendationAgent            │   │
          │  │  - EnhancementAgent               │   │
          │  │  - TruthManagerAgent              │   │
          │  │  - FuzzyDetectorAgent             │   │
          │  │  - LLMValidatorAgent              │   │
          │  │  - 7 Modular Validators           │   │
          │  └────────────────┬───────────────────┘   │
          └───────────────────┼────────────────────────┘
                              ↓
          ┌──────────────────────────────────────────┐
          │      Data Access Layer                   │
          │  ┌────────────────────────────────────┐   │
          │  │  - DatabaseManager                 │   │
          │  │  - CacheManager                    │   │
          │  │  - ValidationStore                 │   │
          │  │  - ConfigLoader                    │   │
          │  └────────────────────────────────────┘   │
          └──────────────────────────────────────────┘
                              ↓
          ┌──────────────────────────────────────────┐
          │      External Services                   │
          │  - SQLite Database                       │
          │  - Ollama LLM (optional)                 │
          │  - Truth Store (JSON files)              │
          └──────────────────────────────────────────┘
```

### Key Principles

1. **Single Entry Point**: All operations must go through MCP server
2. **No Direct Access**: CLI and API cannot directly import agents or database
3. **Unified Interface**: Same operations available via CLI, API, and Dashboard
4. **Consistent Behavior**: Operations behave identically regardless of entry point
5. **Centralized Control**: Auth, rate limiting, logging at MCP layer

---

## Implementation Plan

### Phase 1: Expand MCP Server (High Priority)

**Goal**: Add all missing methods to MCP server

**Tasks**:
1. Add validation operations (validate_file, validate_content, get_validation, list_validations)
2. Add recommendation operations (generate, get, review, apply, delete)
3. Add workflow operations (create, get, list, control, delete)
4. Add admin operations (cache, health, stats, maintenance)
5. Add export operations (export_validation, export_recommendations, export_workflow)

**Files to Modify**:
- [svc/mcp_server.py](svc/mcp_server.py) - Add ~52 new method handlers
- Create `svc/mcp_methods/` directory for organized method implementations:
  - `validation_methods.py`
  - `recommendation_methods.py`
  - `workflow_methods.py`
  - `admin_methods.py`
  - `export_methods.py`

**Example Structure**:
```python
# svc/mcp_methods/validation_methods.py
class ValidationMethods:
    def __init__(self, db_manager, rule_manager, orchestrator):
        self.db_manager = db_manager
        self.rule_manager = rule_manager
        self.orchestrator = orchestrator

    def validate_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a single file."""
        # Implementation

    def validate_content(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate content string."""
        # Implementation

    def get_validation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get validation by ID."""
        # Implementation
```

### Phase 2: Create MCP Client Wrapper (High Priority)

**Goal**: Provide a clean Python client for MCP operations

**Tasks**:
1. Create `svc/mcp_client.py` (note: different from `api/services/mcp_client.py`)
2. Implement synchronous wrapper: `MCPSyncClient`
3. Implement async wrapper: `MCPAsyncClient`
4. Add retry logic, error handling, type hints
5. Add convenience methods for each MCP operation

**File**: `svc/mcp_client.py`

```python
from typing import Dict, Any, List, Optional
from svc.mcp_server import create_mcp_client

class MCPSyncClient:
    """Synchronous MCP client for CLI usage."""

    def __init__(self):
        self._server = create_mcp_client()

    def _call(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call MCP method and handle response."""
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1
        }
        response = self._server.handle_request(request)

        if "error" in response:
            raise MCPError(response["error"])

        return response.get("result", {})

    # Validation methods
    def validate_file(self, file_path: str, family: str = "words",
                     validation_types: Optional[List[str]] = None) -> Dict[str, Any]:
        return self._call("validate_file", {
            "file_path": file_path,
            "family": family,
            "validation_types": validation_types
        })

    def validate_folder(self, folder_path: str, recursive: bool = True) -> Dict[str, Any]:
        return self._call("validate_folder", {
            "folder_path": folder_path,
            "recursive": recursive
        })

    def get_validation(self, validation_id: str) -> Dict[str, Any]:
        return self._call("get_validation", {"validation_id": validation_id})

    def list_validations(self, limit: int = 100, offset: int = 0,
                        status: Optional[str] = None) -> Dict[str, Any]:
        return self._call("list_validations", {
            "limit": limit,
            "offset": offset,
            "status": status
        })

    # Approval methods
    def approve(self, validation_ids: List[str]) -> Dict[str, Any]:
        return self._call("approve", {"ids": validation_ids})

    def reject(self, validation_ids: List[str]) -> Dict[str, Any]:
        return self._call("reject", {"ids": validation_ids})

    # Enhancement methods
    def enhance(self, validation_ids: List[str]) -> Dict[str, Any]:
        return self._call("enhance", {"ids": validation_ids})

    # Recommendation methods
    def generate_recommendations(self, validation_id: str) -> Dict[str, Any]:
        return self._call("generate_recommendations", {
            "validation_id": validation_id
        })

    def get_recommendations(self, validation_id: str) -> Dict[str, Any]:
        return self._call("get_recommendations", {
            "validation_id": validation_id
        })

    # Workflow methods
    def create_workflow(self, workflow_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        return self._call("create_workflow", {
            "workflow_type": workflow_type,
            "params": params
        })

    def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        return self._call("get_workflow", {"workflow_id": workflow_id})

    # Admin methods
    def clear_cache(self) -> Dict[str, Any]:
        return self._call("clear_cache", {})

    def get_stats(self) -> Dict[str, Any]:
        return self._call("get_stats", {})


class MCPAsyncClient:
    """Async MCP client for API usage."""

    async def validate_file(self, file_path: str, **kwargs) -> Dict[str, Any]:
        # Async implementation
        pass
```

### Phase 3: Refactor CLI to Use MCP (High Priority)

**Goal**: Remove all direct agent/database access from CLI

**Tasks**:
1. Replace all `agent_registry.get_agent()` calls with `mcp_client` calls
2. Replace all `db_manager` imports with MCP operations
3. Replace all `cache_manager` imports with MCP operations
4. Update command implementations to use `MCPSyncClient`
5. Remove direct imports of agents and core modules

**File**: [cli/main.py](cli/main.py)

**Before** (current):
```python
from agents.base import agent_registry
from core.database import db_manager

@cli.command()
def validate_file(file_path, family, types, output, output_format):
    orchestrator = agent_registry.get_agent("orchestrator")  # ❌ Direct access
    result = await orchestrator.process_request("validate_file", {...})
```

**After** (MCP-based):
```python
from svc.mcp_client import MCPSyncClient

@cli.command()
def validate_file(file_path, family, types, output, output_format):
    mcp = MCPSyncClient()  # ✅ Via MCP
    result = mcp.validate_file(file_path, family=family,
                               validation_types=types.split(',') if types else None)
```

### Phase 4: Refactor API to Use MCP (High Priority)

**Goal**: Remove all direct agent/database access from API

**Tasks**:
1. Replace all direct `db_manager` calls with MCP operations
2. Replace all direct agent calls with MCP operations
3. Use `MCPAsyncClient` for all endpoints
4. Remove try/catch fallback patterns
5. Make MCP the only code path

**File**: [api/server.py](api/server.py)

**Before** (current):
```python
from core.database import db_manager
from agents.base import agent_registry

@app.get("/api/validations")
async def list_validations(limit: int = 100, offset: int = 0):
    validations = db_manager.list_validation_results(limit, offset)  # ❌ Direct
    return validations
```

**After** (MCP-based):
```python
from svc.mcp_client import MCPAsyncClient

@app.get("/api/validations")
async def list_validations(limit: int = 100, offset: int = 0):
    mcp = MCPAsyncClient()  # ✅ Via MCP
    result = await mcp.list_validations(limit=limit, offset=offset)
    return result["validations"]
```

### Phase 5: Enforce MCP-Only Policy (Medium Priority)

**Goal**: Prevent direct access to agents/database outside MCP

**Tasks**:
1. Create `core/access_guard.py` - raises error if direct access attempted
2. Add runtime checks in `DatabaseManager.__init__()` and agents
3. Only allow MCP server to instantiate agents/database
4. Document MCP-first architecture in [docs/architecture.md](docs/architecture.md)

**File**: `core/access_guard.py`

```python
import inspect
import sys

ALLOWED_CALLERS = [
    'svc.mcp_server',
    'svc.mcp_methods',
    'tests.',  # Allow tests
]

def verify_mcp_access():
    """Verify that caller is authorized to access this component."""
    frame = inspect.currentframe().f_back.f_back
    caller_file = frame.f_code.co_filename

    # Check if caller is in allowed list
    for allowed in ALLOWED_CALLERS:
        if allowed in caller_file:
            return

    raise RuntimeError(
        f"Direct access to core components is not allowed. "
        f"All operations must go through MCP server. "
        f"Caller: {caller_file}"
    )
```

**Usage in DatabaseManager**:
```python
from core.access_guard import verify_mcp_access

class DatabaseManager:
    def __init__(self):
        verify_mcp_access()  # Enforce MCP-only access
        # ... rest of init
```

### Phase 6: Testing & Validation (High Priority)

**Goal**: Ensure MCP-based operations work correctly

**Tasks**:
1. Update all tests to use MCP client
2. Add MCP integration tests
3. Add CLI→MCP→Agent→DB integration tests
4. Add API→MCP→Agent→DB integration tests
5. Add performance benchmarks (MCP overhead measurement)

**New Test Files**:
- `tests/svc/test_mcp_server_complete.py` - Test all 56 MCP methods
- `tests/svc/test_mcp_client.py` - Test sync and async clients
- `tests/integration/test_cli_mcp_integration.py` - CLI→MCP flow
- `tests/integration/test_api_mcp_integration.py` - API→MCP flow
- `tests/performance/test_mcp_overhead.py` - Performance impact

---

## Benefits of MCP-First Architecture

### 1. **Consistency**
- Same behavior across CLI, API, and Dashboard
- Single source of truth for business logic
- Easier to reason about system behavior

### 2. **Maintainability**
- Changes in one place (MCP server) affect all interfaces
- No duplicate logic across CLI and API
- Easier to add new features

### 3. **Security**
- Single point for authentication/authorization
- Centralized rate limiting
- Easier to audit and log operations

### 4. **Testability**
- Test MCP methods once, covers all interfaces
- Mock MCP server for integration tests
- Clear separation of concerns

### 5. **Extensibility**
- Easy to add new interfaces (GraphQL, gRPC, etc.)
- External tools can use MCP directly
- Plugin ecosystem via MCP protocol

### 6. **Observability**
- All operations logged at MCP layer
- Performance metrics in one place
- Easier to trace issues

---

## Challenges & Mitigations

### Challenge 1: Performance Overhead

**Issue**: Extra layer introduces latency

**Mitigation**:
- Use in-process MCP client (no network overhead)
- Implement connection pooling
- Add caching at MCP layer
- Benchmark and optimize hot paths

**Expected Impact**: <5ms overhead per operation (negligible)

### Challenge 2: Migration Effort

**Issue**: Large codebase refactoring required

**Mitigation**:
- Incremental migration (phase-by-phase)
- Keep fallback paths during transition
- Automated tests to catch regressions
- Feature flags for gradual rollout

**Estimated Effort**: 3-4 weeks for full migration

### Challenge 3: Backward Compatibility

**Issue**: Existing code/scripts may break

**Mitigation**:
- Deprecation warnings before removal
- Provide migration guide
- Keep legacy imports with warnings for 1-2 releases
- Clear documentation of breaking changes

### Challenge 4: Error Handling

**Issue**: Errors must propagate through MCP layer

**Mitigation**:
- Standardize error responses (JSON-RPC error codes)
- Preserve stack traces in error details
- Add error context at each layer
- Comprehensive error documentation

---

## Migration Checklist

### Pre-Migration
- [ ] Review and approve architecture plan
- [ ] Set up feature branch for MCP expansion
- [ ] Create tracking issue for migration progress
- [ ] Document current behavior for comparison

### Phase 1: Expand MCP Server
- [ ] Design MCP method signatures for all 52 operations
- [ ] Create `svc/mcp_methods/` directory structure
- [ ] Implement validation methods (8 methods)
- [ ] Implement recommendation methods (8 methods)
- [ ] Implement workflow methods (8 methods)
- [ ] Implement admin methods (10 methods)
- [ ] Implement export methods (3 methods)
- [ ] Add comprehensive unit tests for each method

### Phase 2: Create MCP Client
- [ ] Implement `MCPSyncClient` for CLI usage
- [ ] Implement `MCPAsyncClient` for API usage
- [ ] Add retry logic and error handling
- [ ] Add type hints and documentation
- [ ] Add client unit tests

### Phase 3: Refactor CLI
- [ ] Create backup of current cli/main.py
- [ ] Replace agent imports with MCP client
- [ ] Update all command implementations
- [ ] Test each CLI command manually
- [ ] Run CLI integration tests

### Phase 4: Refactor API
- [ ] Create backup of current api/server.py
- [ ] Replace database/agent imports with MCP client
- [ ] Update all endpoint implementations
- [ ] Remove try/catch fallback patterns
- [ ] Test each API endpoint manually
- [ ] Run API integration tests

### Phase 5: Enforce MCP-Only
- [ ] Implement access guards in core components
- [ ] Add runtime verification
- [ ] Update documentation
- [ ] Test that direct access is blocked

### Phase 6: Testing & Validation
- [ ] Run full test suite
- [ ] Perform manual regression testing
- [ ] Run performance benchmarks
- [ ] Check for memory leaks
- [ ] Validate error handling

### Post-Migration
- [ ] Update all documentation
- [ ] Create migration guide for users
- [ ] Announce breaking changes
- [ ] Monitor production for issues

---

## Code Examples

### Example 1: CLI Command (Before vs After)

**Before** (Direct Access):
```python
# cli/main.py - validate_file command
from agents.base import agent_registry
from core.database import db_manager

@cli.command()
def validate_file(file_path, family, types, output, output_format):
    # Direct agent access ❌
    orchestrator = agent_registry.get_agent("orchestrator")
    result = await orchestrator.process_request("validate_file", {
        "file_path": file_path,
        "family": family,
        "validation_types": types.split(',') if types else None
    })

    # Direct database access ❌
    db_manager.create_validation_result(
        file_path=file_path,
        rules_applied=types,
        validation_results=result,
        status="pending"
    )
```

**After** (MCP-First):
```python
# cli/main.py - validate_file command
from svc.mcp_client import MCPSyncClient

@cli.command()
def validate_file(file_path, family, types, output, output_format):
    # MCP client ✅
    mcp = MCPSyncClient()

    # Single call handles both validation and storage
    result = mcp.validate_file(
        file_path=file_path,
        family=family,
        validation_types=types.split(',') if types else None,
        store_result=True  # MCP handles storage
    )

    # Result is already stored in database by MCP
    click.echo(f"Validation ID: {result['validation_id']}")
```

### Example 2: API Endpoint (Before vs After)

**Before** (Mixed Access):
```python
# api/server.py - approve endpoint
from core.database import db_manager
from svc.mcp_server import create_mcp_client

@app.post("/api/validations/{validation_id}/approve")
async def approve_validation(validation_id: str):
    # Try MCP with fallback ⚠️
    try:
        mcp_client = create_mcp_client()
        response = mcp_client.handle_request({
            "method": "approve",
            "params": {"ids": [validation_id]},
            "id": 1
        })
    except Exception:
        # Fallback to direct database ❌
        db_manager.update_validation_status(validation_id, "approved")

    return {"success": True}
```

**After** (MCP-Only):
```python
# api/server.py - approve endpoint
from svc.mcp_client import MCPAsyncClient

@app.post("/api/validations/{validation_id}/approve")
async def approve_validation(validation_id: str):
    # MCP client only ✅
    mcp = MCPAsyncClient()
    result = await mcp.approve([validation_id])

    # MCP handles all logic
    return {
        "success": result["success"],
        "approved_count": result["approved_count"],
        "errors": result.get("errors", [])
    }
```

### Example 3: MCP Server Method Implementation

```python
# svc/mcp_methods/recommendation_methods.py
from typing import Dict, Any, List
from core.database import DatabaseManager
from agents.recommendation_agent import RecommendationAgent

class RecommendationMethods:
    def __init__(self, db_manager: DatabaseManager, agent_registry):
        self.db_manager = db_manager
        self.recommendation_agent = agent_registry.get_agent("recommendation")

    def generate_recommendations(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate recommendations for a validation.

        Args:
            params: {
                "validation_id": str - ID of validation to generate recommendations for
                "threshold": float - Confidence threshold (optional, default 0.7)
            }

        Returns:
            {
                "success": bool,
                "recommendation_count": int,
                "recommendations": List[Dict],
                "errors": List[str]
            }
        """
        validation_id = params.get("validation_id")
        if not validation_id:
            raise ValueError("validation_id is required")

        threshold = params.get("threshold", 0.7)

        # Get validation from database
        validation = self.db_manager.get_validation_result(validation_id)
        if not validation:
            return {
                "success": False,
                "error": f"Validation {validation_id} not found"
            }

        # Generate recommendations via agent
        recommendations = await self.recommendation_agent.generate_recommendations(
            validation_id=validation_id,
            threshold=threshold
        )

        # Store in database
        stored_recommendations = []
        for rec in recommendations:
            stored_rec = self.db_manager.create_recommendation(
                validation_id=validation_id,
                recommendation_type=rec["type"],
                description=rec["description"],
                proposed_content=rec["proposed_content"],
                confidence=rec["confidence"],
                metadata=rec.get("metadata", {})
            )
            stored_recommendations.append(stored_rec)

        return {
            "success": True,
            "recommendation_count": len(stored_recommendations),
            "recommendations": [self._serialize_recommendation(r)
                               for r in stored_recommendations],
            "errors": []
        }

    def get_recommendations(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get recommendations for a validation."""
        validation_id = params.get("validation_id")
        if not validation_id:
            raise ValueError("validation_id is required")

        recommendations = self.db_manager.get_recommendations_for_validation(
            validation_id
        )

        return {
            "success": True,
            "recommendations": [self._serialize_recommendation(r)
                               for r in recommendations]
        }

    def review_recommendation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Review (approve/reject) a recommendation."""
        recommendation_id = params.get("recommendation_id")
        action = params.get("action")  # "approve" or "reject"
        notes = params.get("notes", "")

        if not recommendation_id or not action:
            raise ValueError("recommendation_id and action are required")

        if action not in ["approve", "reject"]:
            raise ValueError("action must be 'approve' or 'reject'")

        # Update recommendation status
        self.db_manager.update_recommendation_status(
            recommendation_id=recommendation_id,
            status=action + "d",  # "approved" or "rejected"
            notes=notes
        )

        return {
            "success": True,
            "recommendation_id": recommendation_id,
            "action": action
        }

    def _serialize_recommendation(self, rec) -> Dict[str, Any]:
        """Convert database recommendation to dict."""
        return {
            "id": rec.id,
            "validation_id": rec.validation_id,
            "type": rec.recommendation_type,
            "description": rec.description,
            "proposed_content": rec.proposed_content,
            "confidence": rec.confidence,
            "status": rec.status,
            "created_at": rec.created_at.isoformat(),
            "metadata": rec.metadata
        }
```

---

## Metrics & Success Criteria

### Completion Metrics

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| MCP method coverage | 7.1% (4/56) | 100% (56/56) | 🔴 Not started |
| CLI commands using MCP | 0% (0/30) | 100% (30/30) | 🔴 Not started |
| API endpoints using MCP | 3.8% (3/80) | 100% (80/80) | 🔴 Not started |
| Direct database imports in CLI | ~30 | 0 | 🔴 Not started |
| Direct database imports in API | ~50 | 0 | 🔴 Not started |
| Direct agent imports in CLI | ~15 | 0 | 🔴 Not started |
| Direct agent imports in API | ~20 | 0 | 🔴 Not started |

### Quality Metrics

| Metric | Target |
|--------|--------|
| Test coverage for MCP methods | >90% |
| MCP operation latency overhead | <5ms |
| Zero direct access violations | 100% enforcement |
| Documentation completeness | All methods documented |

---

## Timeline Estimate

| Phase | Duration | Effort |
|-------|----------|--------|
| Phase 1: Expand MCP Server | 1.5 weeks | 52 methods, ~15 hours |
| Phase 2: Create MCP Client | 0.5 weeks | 2 clients, ~5 hours |
| Phase 3: Refactor CLI | 1 week | 30 commands, ~10 hours |
| Phase 4: Refactor API | 1 week | 80 endpoints, ~10 hours |
| Phase 5: Enforce MCP-Only | 0.5 weeks | Guards, ~5 hours |
| Phase 6: Testing & Validation | 1 week | Comprehensive testing, ~10 hours |
| **Total** | **5-6 weeks** | **~55 hours** |

---

## Conclusion

The current architecture has **inconsistent operation flow** with only 7.1% MCP coverage. To ensure all UI and CLI operations go through MCP:

### Required Changes

1. **Expand MCP server** from 4 to 56 methods (+52 methods)
2. **Create MCP client wrappers** (sync for CLI, async for API)
3. **Refactor CLI** to remove all direct agent/database access
4. **Refactor API** to remove all direct agent/database access
5. **Enforce MCP-only policy** with runtime guards
6. **Comprehensive testing** of all paths

### Benefits

- ✅ Consistent behavior across all interfaces
- ✅ Single source of truth for business logic
- ✅ Easier to maintain and extend
- ✅ Centralized security and observability
- ✅ Better testability

### Next Steps

1. **Review and approve** this architecture plan
2. **Create implementation issues** for each phase
3. **Start with Phase 1**: Expand MCP server (highest priority)
4. **Incremental rollout**: One phase at a time with full testing
5. **Monitor and iterate**: Collect feedback and adjust

---

## Appendix A: MCP Method Signatures

### Validation Methods

```python
# validate_file
Params: {"file_path": str, "family": str, "validation_types": List[str]}
Returns: {"validation_id": str, "status": str, "issues": List[Dict], ...}

# validate_folder
Params: {"folder_path": str, "recursive": bool}
Returns: {"files_processed": int, "validations": List[Dict], ...}

# validate_content
Params: {"content": str, "file_path": str, "validation_types": List[str]}
Returns: {"validation_id": str, "status": str, "issues": List[Dict], ...}

# get_validation
Params: {"validation_id": str}
Returns: {"validation": Dict}

# list_validations
Params: {"limit": int, "offset": int, "status": str}
Returns: {"validations": List[Dict], "total": int}

# delete_validation
Params: {"validation_id": str}
Returns: {"success": bool}

# revalidate
Params: {"validation_id": str}
Returns: {"new_validation_id": str, ...}
```

### Recommendation Methods

```python
# generate_recommendations
Params: {"validation_id": str, "threshold": float}
Returns: {"recommendations": List[Dict], "count": int}

# get_recommendations
Params: {"validation_id": str}
Returns: {"recommendations": List[Dict]}

# review_recommendation
Params: {"recommendation_id": str, "action": str, "notes": str}
Returns: {"success": bool}

# apply_recommendations
Params: {"validation_id": str, "recommendation_ids": List[str]}
Returns: {"applied_count": int, "enhanced_content": str}

# delete_recommendation
Params: {"recommendation_id": str}
Returns: {"success": bool}
```

### Workflow Methods

```python
# create_workflow
Params: {"workflow_type": str, "params": Dict}
Returns: {"workflow_id": str, "status": str}

# get_workflow
Params: {"workflow_id": str}
Returns: {"workflow": Dict}

# list_workflows
Params: {"limit": int, "offset": int, "status": str}
Returns: {"workflows": List[Dict], "total": int}

# control_workflow
Params: {"workflow_id": str, "action": str}  # pause/resume/cancel
Returns: {"success": bool, "new_status": str}

# delete_workflow
Params: {"workflow_id": str}
Returns: {"success": bool}
```

### Admin Methods

```python
# get_stats
Params: {}
Returns: {"validations_total": int, "recommendations_total": int, ...}

# get_system_status
Params: {}
Returns: {"healthy": bool, "components": Dict}

# clear_cache
Params: {}
Returns: {"success": bool, "cleared_items": int}

# get_cache_stats
Params: {}
Returns: {"size": int, "hit_rate": float, ...}

# reload_agent
Params: {"agent_id": str}
Returns: {"success": bool}
```

---

## Appendix B: File Locations

| Component | File Path | Purpose |
|-----------|-----------|---------|
| MCP Server | [svc/mcp_server.py](svc/mcp_server.py) | Main MCP server implementation |
| MCP Client | `svc/mcp_client.py` | Client wrappers (to be created) |
| Validation Methods | `svc/mcp_methods/validation_methods.py` | Validation MCP handlers (to be created) |
| Recommendation Methods | `svc/mcp_methods/recommendation_methods.py` | Recommendation MCP handlers (to be created) |
| Workflow Methods | `svc/mcp_methods/workflow_methods.py` | Workflow MCP handlers (to be created) |
| Admin Methods | `svc/mcp_methods/admin_methods.py` | Admin MCP handlers (to be created) |
| CLI | [cli/main.py](cli/main.py) | Command-line interface (to be refactored) |
| API Server | [api/server.py](api/server.py) | REST API endpoints (to be refactored) |
| Access Guards | `core/access_guard.py` | Runtime MCP enforcement (to be created) |
| MCP Docs | [docs/mcp_integration.md](docs/mcp_integration.md) | MCP documentation (to be updated) |
| Architecture Docs | [docs/architecture.md](docs/architecture.md) | System architecture (to be updated) |

---

**End of Report**
