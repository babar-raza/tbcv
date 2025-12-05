# TBCV Runtime Surfaces (Code-Based Evidence)

**Generated:** 2025-12-03
**Source:** Direct code inspection only
**Purpose:** Document all runtime entry points and invocation methods discovered in code

---

## Overview

This document catalogs **all ways the TBCV system can be invoked**, based on direct code inspection. Every claim is backed by file paths and line numbers.

---

## Runtime Surface 1: FastAPI HTTP Server

### Entry Point
**File:** [main.py](main.py)
**Function:** `run_api(host, port, reload, log_level, clean)` (Line 154)
**Command:** `python main.py --mode api [OPTIONS]`

### Command-Line Options (from main.py:226-243)
```
--mode api          (required) Run mode
--host HOST         (default: 127.0.0.1) Host to bind
--port PORT         (default: 8585) Port to bind
--reload            Enable auto reload
--log-level LEVEL   (default: info) Uvicorn log level
--no-clean          Skip purging __pycache__ and *.pyc
```

### Startup Sequence (from code)

**Step 1: Environment Setup (Lines 159-163)**
```python
project_root = _ensure_project_on_path()
if clean:
    d, f = _purge_bytecode(project_root)
```

**Step 2: Schema Validation (Lines 165-170)**
```python
if not _validate_schemas():
    print("Error: Schema validation failed. Aborting startup.")
    sys.exit(1)
```
- Validates all JSON files in `truth/` and `rules/` directories
- Ensures valid JSON and non-empty structure

**Step 3: Comprehensive Startup Checks (Lines 173-188)**
```python
from core.startup_checks import run_startup_checks
success, summary = run_startup_checks()
if not success:
    print("FATAL: Critical startup checks failed. Cannot start server.")
    sys.exit(1)
```

**Step 4: Import Uvicorn (Lines 190)**
```python
uvicorn = _import_uvicorn_or_die()
```
- Detects module shadowing issues
- Provides diagnostics on import failure

**Step 5: Start Server (Lines 193-216)**
```python
from api.server import app
uvicorn.run(
    app,
    host=host,
    port=port,
    reload=reload,
    log_level=log_level,
    ws="wsproto",  # WebSocket implementation
)
```

### FastAPI Application (api/server.py)

**Application Object:** `app = FastAPI(lifespan=lifespan)` (implicit from code structure)

**Lifecycle Management (Lines 173-199):**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    logger.info("Starting TBCV API server")
    db_manager.init_database()  # Idempotent

    # Start live bus for real-time updates
    from api.services.live_bus import start_live_bus
    await start_live_bus()

    # Register agents
    await register_agents()

    yield  # Server runs

    # Shutdown
    logger.info("Shutting down TBCV API server")
    # Stop live bus...
```

### API Endpoints (from api/server.py)

**Note:** Only first 200 lines read; full endpoint list requires complete file read.

**Endpoint Categories Evident from Imports:**
1. **Validation Endpoints** - ContentValidationRequest, FileValidationRequest, DirectoryValidationRequest, BatchValidationRequest (Lines 97-125)
2. **Enhancement Endpoints** - EnhanceContentRequest, BatchEnhanceRequest (Lines 127-144)
3. **Recommendation Endpoints** - RecommendationReviewRequest (Lines 146-149)
4. **Workflow Endpoints** - WorkflowControlRequest, WorkflowStatus (Lines 151-167)
5. **Dashboard Endpoints** - Likely in `api/dashboard.py`
6. **WebSocket Endpoints** - Likely in `api/websocket_endpoints.py`
7. **Export Endpoints** - Likely in `api/export_endpoints.py`
8. **Audit Endpoints** - Likely in `api/audit_endpoints.py`

**Health Endpoints (from Dockerfile:30 and code pattern):**
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe (implied)

**Middleware (Lines 26):**
- CORS middleware enabled

**Global State (Lines 89-91):**
```python
SERVER_START_TIME = time.time()
MAINTENANCE_MODE = False
workflow_jobs: Dict[str, WorkflowStatus] = {}
```

---

## Runtime Surface 2: CLI (Command-Line Interface)

### Entry Point
**File:** [__main__.py](__ main__.py)
**Chain:** `__main__.py:main()` → `cli.main:cli()` (Lines 25-32)
**Command:** `python -m tbcv [COMMAND] [OPTIONS]`

### CLI Framework
**Library:** Click (Line 114 in cli/main.py)
**Console:** Rich (Lines 29, 57 in cli/main.py)

### Global CLI Options (cli/main.py:114-141)
```python
@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--config', '-c', help='Configuration file path')
@click.option('--quiet', '-q', is_flag=True, help='Minimal output')
@click.option('--mcp-debug', is_flag=True, help='Enable MCP client debug logging')
def cli(ctx, verbose, config, quiet, mcp_debug):
    """TBCV Command Line Interface."""
```

**Behavior (Lines 123-140):**
- Sets log level based on verbose/mcp_debug
- Sets `TBCV_LOG_LEVEL` environment variable
- Sets `TBCV_CONFIG` if custom config provided
- Displays banner unless `--quiet`

### CLI Agent Setup (cli/main.py:63-105)
**Function:** `setup_agents()` (async)

**Agents Registered:**
1. TruthManagerAgent (Line 72)
2. FuzzyDetectorAgent (Line 76, if enabled)
3. ContentValidatorAgent (Line 81)
4. ContentEnhancerAgent (Line 84)
5. LLMValidatorAgent (Line 87)
6. RecommendationAgent (Line 90)
7. EnhancementAgent (Line 95)
8. OrchestratorAgent (Line 98)

**Initialization:** `_agents_initialized = False` flag prevents re-initialization (Line 60)

### CLI Commands Discovered (from code read)

#### 1. `validate-file` (Lines 146-200)
```python
@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--family', '-f', default='words')
@click.option('--types', '-t', help='Comma-separated validation types')
@click.option('--output', '-o', help='Output file for results')
@click.option('--format', 'output_format', default='json', type=click.Choice(['json', 'text']))
@with_mcp_client
def validate_file(file_path, family, types, output, output_format, mcp_client):
    """Validate a single content file using MCP client."""
```

**Behavior (Lines 157-163):**
- Checks if content is English before processing
- Calls `mcp_client.validate_file()`
- Outputs JSON or text format

**MCP Integration (Line 153):**
Uses `@with_mcp_client` decorator from `cli.mcp_helpers`

#### 2. Additional Commands (Mentioned in Comments)
From cli/main.py line 8-15 comments:
- `validate_directory` - Batch directory validation
- `check_agents` - Agent diagnostics
- `validate` - Validation (generic)
- `batch` - Batch processing
- `enhance` - Enhancement operations
- `test` - Test operations
- `status` - System status

**Note:** Only first 200 lines read; full command list requires complete file read.

#### 3. `probe-endpoints` (Line 16 comment)
Delegates to `tbcv.tools.endpoint_probe.main`

### MCP Client Integration (cli/main.py:43)
```python
from cli.mcp_helpers import with_mcp_client, handle_mcp_error
from svc.mcp_exceptions import MCPError
```

**Pattern:** CLI commands use MCP client to communicate with validation system

### Language Enforcement (cli/main.py:157-163)
```python
is_english, reason = is_english_content(file_path)
if not is_english:
    click.echo(f"Error: Non-English content detected - {reason}", err=True)
    sys.exit(1)
```

---

## Runtime Surface 3: MCP Server (Model Context Protocol)

### Entry Point
**File:** [svc/mcp_server.py](svc/mcp_server.py)
**Class:** `MCPServer` (Line 22)
**Protocol:** JSON-RPC

**Note:** How MCP server is started is not yet clear from code read. Likely requires reading more files.

### Initialization (Lines 24-45)
```python
def __init__(self):
    self.db_manager = DatabaseManager()
    self.rule_manager = RuleManager()
    self.ingestion = MarkdownIngestion(self.db_manager, self.rule_manager)
    self.db_manager.init_database()

    from svc.mcp_methods import MCPMethodRegistry, ...
    self.registry = MCPMethodRegistry()

    self.agent_registry = None  # Placeholder
    self._register_methods()
```

### Method Registration (Lines 47-150)
**Method Handlers:**
1. **ValidationMethods** (Lines 60-64, 97-104)
2. **ApprovalMethods** (Lines 66-69, 107-110)
3. **EnhancementMethods** (Lines 71-74, 113-117)
4. **AdminMethods** (Lines 76-79, 120-129)
5. **WorkflowMethods** (Lines 80-84, 132-139)
6. **QueryMethods** (Lines 86-89, 142-150)
7. **RecommendationMethods** (Lines 90-94)

### MCP Methods Registered (40+ total)

**Validation Methods (8):**
1. `validate_folder` (Line 97)
2. `validate_file` (Line 98)
3. `validate_content` (Line 99)
4. `get_validation` (Line 100)
5. `list_validations` (Line 101)
6. `update_validation` (Line 102)
7. `delete_validation` (Line 103)
8. `revalidate` (Line 104)

**Approval Methods (4):**
1. `approve` (Line 107)
2. `reject` (Line 108)
3. `bulk_approve` (Line 109)
4. `bulk_reject` (Line 110)

**Enhancement Methods (5):**
1. `enhance` (Line 113)
2. `enhance_batch` (Line 114)
3. `enhance_preview` (Line 115)
4. `enhance_auto_apply` (Line 116)
5. `get_enhancement_comparison` (Line 117)

**Admin Methods (10):**
1. `get_system_status` (Line 120)
2. `clear_cache` (Line 121)
3. `get_cache_stats` (Line 122)
4. `cleanup_cache` (Line 123)
5. `rebuild_cache` (Line 124)
6. `reload_agent` (Line 125)
7. `run_gc` (Line 126)
8. `enable_maintenance_mode` (Line 127)
9. `disable_maintenance_mode` (Line 128)
10. `create_checkpoint` (Line 129)

**Workflow Methods (8):**
1. `create_workflow` (Line 132)
2. `get_workflow` (Line 133)
3. `list_workflows` (Line 134)
4. `control_workflow` (Line 135)
5. `get_workflow_report` (Line 136)
6. `get_workflow_summary` (Line 137)
7. `delete_workflow` (Line 138)
8. `bulk_delete_workflows` (Line 139)

**Query Methods (9):**
1. `get_stats` (Line 142)
2. `get_audit_log` (Line 143)
3. `get_performance_report` (Line 144)
4. `get_health_report` (Line 145)
5. `get_validation_history` (Line 146)
6. `get_available_validators` (Line 147)
7. `export_validation` (Line 148)
8. `export_recommendations` (Line 149)
9. `export_workflow` (Line 150)

**Recommendation Methods:**
- Count unknown (need to read svc/mcp_methods/recommendation_methods.py)

---

## Runtime Surface 4: Docker Deployment

### Dockerfile Entry Point
**File:** [Dockerfile](Dockerfile)
**Command:** `CMD ["python", "main.py", "--mode", "api", "--host", "0.0.0.0", "--port", "8080"]` (Line 40)

**Base Image:** `python:3.12-slim` (Line 1)

**Build Steps:**
1. Install system dependencies: build-essential, git (Lines 7-10)
2. Copy and install requirements (Lines 13-14)
3. Copy application code (Line 17)
4. Create directories: data, data/logs, data/cache (Line 20)
5. Run optional startup_check.py (Line 23)

**Exposed Port:** 8080 (Line 26)

**Health Check (Lines 29-30):**
```
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8080/health/live').raise_for_status()"
```

**Environment Variables (Lines 33-37):**
```
TBCV_SYSTEM_ENVIRONMENT=production
TBCV_SYSTEM_DEBUG=false
TBCV_SYSTEM_LOG_LEVEL=info
TBCV_SERVER_HOST=0.0.0.0
TBCV_SERVER_PORT=8080
```

### Docker Compose Entry Point
**File:** [docker-compose.yml](docker-compose.yml)
**Service:** `tbcv` (Lines 4-28)

**Configuration:**
- Container name: `tbcv-app` (Line 6)
- Ports: 8080:8080 (Line 8)
- Volumes:
  - `./data:/app/data` (Line 10) - Persistent data
  - `./config:/app/config:ro` (Line 11) - Read-only config
  - `./truth:/app/truth:ro` (Line 12) - Read-only truth data
- Restart policy: unless-stopped (Line 22)
- Health check: Same as Dockerfile (Lines 23-28)

**Environment Variables (Lines 13-21):**
- Database: `TBCV_DATABASE_URL=sqlite:///./data/tbcv.db`
- Performance: Worker pool=8, Max workflows=50

**Optional Redis Service (Commented Out):**
```yaml
# redis:
#   image: redis:7-alpine
#   ports: ["6379:6379"]
```

---

## Runtime Surface 5: Standalone Scripts

**Total Scripts with `if __name__ == "__main__":` blocks: 98**

### Categories of Standalone Scripts

#### A. Maintenance Scripts (`scripts/maintenance/`)
1. `validate_system.py` - System validation
2. `startup_check.py` - Startup checks (also called by Dockerfile)
3. `health.py` - Health checks
4. `diagnose.py` - System diagnostics
5. `inventory.py` - System inventory
6. `validate_quick.py` - Quick validation

#### B. Testing Scripts (`scripts/testing/`)
1. `run_all_tests.py` - Run all tests
2. `run_smoke.py` - Smoke tests
3. `run_full_stack_test.py` - Full stack tests

#### C. Utility Scripts (`scripts/utilities/`)
1. `approve_recommendations.py` - Recommendation approval utility

#### D. Tools (`tools/`)
1. `cleanup_db.py` - Database cleanup
2. `validate_folder.py` - Folder validation
3. `endpoint_check.py` - Endpoint testing
4. `analyze_validators.py` - Validator analysis
5. `apply_patches.py` - Patch application

#### E. Migration Scripts (`migrations/`)
1. `add_validation_history_columns.py`
2. `fix_validation_status_enum.py`
3. `add_revalidation_columns.py`
4. `add_validation_types_column.py`

#### F. Agent Standalone Execution
From grep results, these agents have `__main__` blocks:
1. `agents/truth_manager.py` (Line in grep results)
2. `agents/orchestrator.py`
3. `agents/content_enhancer.py`
4. `agents/code_analyzer.py`

#### G. Core Module Execution
1. `core/logging.py` - Logging setup test
2. `core/access_guard.py` - Access guard demo
3. `core/config.py` - Config display
4. `core/__main__.py` - Core package entry

#### H. Test Execution Scripts
- 98 test files with `__main__` blocks
- Allow individual test file execution: `python test_xyz.py`

---

## Runtime Surface 6: CI/CD Pipeline

### GitHub Actions Workflow
**File:** [.github/workflows/ui-tests.yml](.github/workflows/ui-tests.yml)
**Name:** UI Tests

**Triggers (Lines 4-8):**
- Push to main branch
- Pull requests to main
- Manual dispatch (`workflow_dispatch`)

**Jobs:**

#### Job 1: `ui-tests` (Lines 11-56)
**Runs on:** ubuntu-latest
**Timeout:** 15 minutes

**Steps:**
1. Checkout repository (actions/checkout@v4)
2. Set up Python 3.11 (actions/setup-python@v5) with pip cache
3. Install dependencies: `pip install -e ".[test]"`
4. Install Playwright: `playwright install chromium --with-deps`
5. Run UI tests: `pytest tests/ui/ -v --browser chromium --screenshot=only-on-failure --timeout=120`
6. Upload screenshots on failure (retention: 7 days)
7. Upload test results (retention: 7 days)

**Environment:**
```
TBCV_TEST_MODE=1
```

#### Job 2: `ui-tests-cross-browser` (Lines 59-101)
**Runs on:** ubuntu-latest
**Timeout:** 20 minutes
**Condition:** Only on push to main (Line 62)
**Depends on:** ui-tests job (Line 63)

**Matrix Strategy (Lines 65-68):**
- Browsers: firefox, webkit
- Fail-fast: false

**Similar steps to Job 1, but with matrix browser parameter**

---

## Runtime Surface 7: Systemd Service (Linux)

### Service Definition
**File:** `tbcv.service` (not yet read, but referenced in README)
**Location:** Should be in `scripts/systemd/` based on directory structure

**Implied Commands:**
```bash
sudo systemctl enable tbcv
sudo systemctl start tbcv
sudo systemctl stop tbcv
sudo systemctl restart tbcv
sudo systemctl status tbcv
```

---

## Runtime Surface 8: Windows Service

### Service Management
**Location:** `scripts/windows/` directory exists
**Files:** Not yet inspected

**Referenced in README (untrusted):**
- Windows service setup scripts exist
- Details require code inspection

---

## Summary: All Runtime Surfaces

| # | Surface | Entry Point | Invocation Method |
|---|---------|-------------|-------------------|
| 1 | **HTTP API Server** | `main.py --mode api` | `python main.py --mode api --host HOST --port PORT` |
| 2 | **CLI** | `__main__.py` | `python -m tbcv [COMMAND] [OPTIONS]` |
| 3 | **MCP Server** | `svc/mcp_server.py:MCPServer` | JSON-RPC calls (launch method TBD) |
| 4 | **Docker** | Dockerfile CMD | `docker run` or `docker-compose up` |
| 5 | **Standalone Scripts** | 98 files with `__main__` | `python script.py` |
| 6 | **CI/CD** | GitHub Actions | Automatic on push/PR/manual |
| 7 | **Systemd** | `tbcv.service` | `systemctl start tbcv` |
| 8 | **Windows Service** | `scripts/windows/` | Windows service commands |

---

## Open Questions for Phase 1 Deep-Read

1. **How is MCP Server started?**
   - Not evident from partial code read
   - Need to search for MCP server instantiation and launch

2. **Full API endpoint list?**
   - Only saw first 200 lines of api/server.py
   - Need complete file read for all endpoints

3. **Full CLI command list?**
   - Only saw first 200 lines of cli/main.py
   - Need complete file read for all commands

4. **Web Dashboard access?**
   - Jinja2 templates exist
   - Dashboard routes in api/dashboard.py
   - What is the URL? How is it accessed?

5. **WebSocket endpoints?**
   - Referenced in api/websocket_endpoints.py
   - What WebSocket APIs are available?

6. **How do agents communicate?**
   - Agent registry pattern evident
   - Orchestrator exists
   - What is the actual communication mechanism?

7. **Background jobs/workers?**
   - No evidence of Celery or similar task queue found yet
   - Are there background workers beyond the main server?

---

## Phase 1 Requirements

To complete Phase 1 (Runtime Surfaces), must deep-read:

**Priority 1 (Required):**
1. ✅ `main.py` - DONE
2. ⏳ `api/server.py` - FULL FILE (all endpoints)
3. ⏳ `cli/main.py` - FULL FILE (all commands)
4. ⏳ `svc/mcp_server.py` - FULL FILE (MCP launch)
5. ⏳ `agents/orchestrator.py` - Workflow coordination

**Priority 2 (Important):**
6. ⏳ `api/dashboard.py` - Web UI routes
7. ⏳ `api/websocket_endpoints.py` - WebSocket APIs
8. ⏳ `core/startup_checks.py` - What startup checks run
9. ⏳ `api/services/live_bus.py` - Real-time event bus
10. ⏳ Key scripts in `scripts/maintenance/`

**Phase 1 Status:** Partial (30% complete)
**Next Actions:** Deep-read full files listed above
