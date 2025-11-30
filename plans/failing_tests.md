# Plan: Comprehensive Test Suite Remediation

**Current State**: ~147 failing tests, ~67 errors across test suite
**Target State**: 100% test pass rate with sustainable test architecture
**Priority**: HIGH - Tests are the safety net for the codebase

---

## Executive Summary

The TBCV test suite has accumulated significant technical debt due to API evolution without corresponding test updates. This plan addresses **12 distinct root causes** affecting **~220 tests** through a systematic, phased approach.

### Key Findings

| Category | Tests Affected | Effort | Priority |
|----------|---------------|--------|----------|
| DatabaseManager API Mismatch | ~50 | Low | P1 |
| Agent API Contract Changes | ~25 | Medium | P1 |
| Validator Architecture Refactor | ~33 | Medium | P2 |
| Cache/Logger API Changes | ~14 | Low | P2 |
| Windows Encoding Issues | ~43 | Low | P2 |
| Language Detection Logic | 4 | Medium | P3 |
| Placeholder/Unimplemented Tests | 8 | N/A | P4 |

### Success Criteria

1. All tests pass with exit code 0
2. No tests skip due to missing fixtures
3. Test execution time < 5 minutes for full suite
4. Zero false positives (flaky tests)
5. Test coverage maintained or improved

---

## Phase 1: Foundation Fixes (DatabaseManager API)

**Goal**: Fix ~50 tests failing due to renamed DatabaseManager methods
**Estimated Effort**: 2 hours
**Priority**: P1 - Blocks all database-related tests

### 1.1 Root Cause Analysis

The `DatabaseManager` class was refactored to use more explicit method names:

| Old Method (in Tests) | Current Method | Reason for Change |
|----------------------|----------------|-------------------|
| `save_validation_result()` | `create_validation_result()` | Clarity: "save" was ambiguous |
| `save_recommendation()` | `create_recommendation()` | Consistency with "create" pattern |
| `close()` | *(removed)* | Context manager handles cleanup |

### 1.2 Affected Files

```
tests/agents/test_enhancement_agent_comprehensive.py  (22 errors)
tests/api/test_export_endpoints_comprehensive.py      (42 errors)
tests/api/services/test_status_recalculator.py        (5 failures)
tests/api/services/test_recommendation_consolidator.py (2 failures)
tests/test_checkpoints.py                             (3 errors)
```

### 1.3 Solution Strategy

**Option A: Update Tests (Recommended)**
- Update all test files to use new method names
- Removes technical debt
- Tests reflect actual API

**Option B: Add Compatibility Layer (Not Recommended)**
- Add aliases in DatabaseManager
- Increases complexity
- Hides actual API from tests

### 1.4 Implementation Steps

1. **Create test helper module** for common database operations:
   ```python
   # tests/utils/db_helpers.py
   from core.database import DatabaseManager

   async def create_test_validation(db: DatabaseManager, **kwargs):
       """Wrapper for creating test validations with defaults."""
       defaults = {
           "file_path": "/test/file.md",
           "status": "pending",
           "issues": [],
           "confidence": 1.0
       }
       return await db.create_validation_result(**{**defaults, **kwargs})
   ```

2. **Update test fixtures** in `conftest.py`:
   ```python
   @pytest.fixture
   async def db_with_validation(db_session):
       """Fixture providing database with pre-created validation."""
       validation = await db_session.create_validation_result(...)
       yield db_session, validation
   ```

3. **Batch update method calls** using search-and-replace:
   ```bash
   # Find all occurrences
   grep -r "save_validation_result" tests/
   grep -r "save_recommendation" tests/
   grep -r "\.close()" tests/ | grep -i database
   ```

4. **Remove `close()` calls** - DatabaseManager uses context managers:
   ```python
   # Before (incorrect)
   db = DatabaseManager()
   db.close()

   # After (correct)
   async with DatabaseManager() as db:
       # operations
   # Auto-cleanup on exit
   ```

### 1.5 Verification

```bash
# Run affected tests after changes
pytest tests/agents/test_enhancement_agent_comprehensive.py -v
pytest tests/api/test_export_endpoints_comprehensive.py -v
pytest tests/api/services/ -v
pytest tests/test_checkpoints.py -v
```

---

## Phase 2: Agent Contract Alignment

**Goal**: Fix ~25 tests failing due to Agent API evolution
**Estimated Effort**: 4 hours
**Priority**: P1 - Core agent functionality

### 2.1 Root Cause Analysis

Agent base class and specific agents have evolved but tests still expect old interfaces:

| Component | Old API | Current API | Impact |
|-----------|---------|-------------|--------|
| `BaseAgent` | `.start()`, `.stop()` | Lifecycle via `AgentBus` | 4 tests |
| `BaseAgent` | `.handlers` dict | `._handlers` internal | 5 tests |
| `EnhancementAgent` | `.capabilities` | `get_contract()` | 8 tests |
| `EnhancementResult` | `.applied_count` | `.results` list length | 4 tests |
| `TruthManagerAgent` | Fixed `agent_id` | Generated ID | 4 tests |

### 2.2 Affected Files

```
tests/agents/test_base.py                    (4 failures)
tests/agents/test_enhancement_agent.py       (12 failures)
tests/agents/test_truth_manager.py           (9 failures)
```

### 2.3 Solution Strategy

This requires understanding the **intended** agent architecture vs what tests expect.

**Step 1: Document Current Agent Contract**

Create `docs/architecture/AGENT_CONTRACT.md`:
```markdown
# Agent Contract Specification

## BaseAgent Interface
- `__init__(agent_id: Optional[str] = None)`
- `get_contract() -> AgentContract`
- `handle(message: AgentMessage) -> AgentResponse`

## Lifecycle Management
- Agents are registered/unregistered via AgentBus
- No explicit start/stop methods on agent instances
- AgentBus manages lifecycle

## Handler Registration
- Handlers registered via `@handler` decorator
- Internal storage in `_handlers` (implementation detail)
- Access via `get_contract().methods`
```

**Step 2: Update Test Expectations**

For `test_base.py`:
```python
# Before (incorrect)
def test_agent_start(self):
    agent = ConcreteAgent()
    agent.start()  # AttributeError

# After (correct)
async def test_agent_lifecycle(self, agent_bus):
    agent = ConcreteAgent()
    await agent_bus.register(agent)
    # Verify registration
    assert agent.agent_id in agent_bus.agents
    await agent_bus.unregister(agent.agent_id)
```

For `test_enhancement_agent.py`:
```python
# Before (incorrect)
def test_agent_capabilities(self):
    agent = EnhancementAgent()
    assert "enhance" in agent.capabilities  # AttributeError

# After (correct)
def test_agent_contract(self):
    agent = EnhancementAgent()
    contract = agent.get_contract()
    assert "enhance_content" in [m.name for m in contract.methods]
```

For `test_truth_manager.py`:
```python
# Before (incorrect)
def test_truth_manager_default_id(self):
    agent = TruthManagerAgent()
    assert agent.agent_id == "truth_manager"  # Now generates unique ID

# After (correct)
def test_truth_manager_default_id(self):
    agent = TruthManagerAgent()
    assert agent.agent_id.startswith("truthmanageragent_")
    # Or if specific ID needed:
    agent = TruthManagerAgent(agent_id="truth_manager")
    assert agent.agent_id == "truth_manager"
```

### 2.4 Implementation Steps

1. **Read current agent implementations**:
   ```
   agents/base_agent.py
   agents/enhancement_agent.py
   agents/truth_manager.py
   ```

2. **Document actual contract** in each agent

3. **Update test base classes** to use new patterns

4. **Create agent test fixtures**:
   ```python
   @pytest.fixture
   async def registered_agent(agent_bus):
       """Fixture for fully initialized agent."""
       agent = EnhancementAgent()
       await agent_bus.register(agent)
       yield agent
       await agent_bus.unregister(agent.agent_id)
   ```

5. **Update assertions** to match new API

### 2.5 Verification

```bash
pytest tests/agents/test_base.py -v
pytest tests/agents/test_enhancement_agent.py -v
pytest tests/agents/test_truth_manager.py -v
```

---

## Phase 3: Validator Architecture Remediation

**Goal**: Fix ~33 tests for refactored validator system
**Estimated Effort**: 6 hours
**Priority**: P2 - Validators are core feature

### 3.1 Root Cause Analysis

The validator system underwent significant refactoring:

| Old Architecture | New Architecture |
|-----------------|------------------|
| Monolithic `ContentValidator` | Modular validators per concern |
| Direct method calls | Router-based dispatch |
| In-memory validation | Database-backed with caching |
| Single validation pass | Tiered validation (quick → thorough) |

### 3.2 Affected Files

```
tests/agents/test_modular_validators.py  (20 failures)
tests/agents/test_seo_validation.py      (13 failures)
```

### 3.3 SEO Validator Analysis

**Current State**: `SEOValidator.validate()` returns empty list
**Expected State**: Should validate heading hierarchy, lengths, etc.

**Investigation Required**:
1. Check if `SEOValidator` is implemented in `agents/validators/seo_validator.py`
2. Verify configuration in `config/seo.yaml`
3. Check if validator is registered with router

**Solution Options**:

**Option A: Implement SEO Validator** (if missing)
```python
# agents/validators/seo_validator.py
class SEOValidator(BaseValidator):
    def __init__(self, config: dict):
        self.config = config
        self.min_h1_length = config.get("min_h1_length", 20)
        self.max_h1_length = config.get("max_h1_length", 60)

    async def validate(self, content: str, metadata: dict) -> List[Issue]:
        issues = []
        headings = self._extract_headings(content)

        # Check H1 presence
        h1_headings = [h for h in headings if h.level == 1]
        if not h1_headings:
            issues.append(Issue(
                level="error",
                category="seo",
                message="Missing H1 heading",
                suggestion="Add an H1 heading at the start of the document"
            ))
        elif len(h1_headings) > 1:
            issues.append(Issue(
                level="warning",
                category="seo",
                message=f"Multiple H1 headings found ({len(h1_headings)})",
                suggestion="Use only one H1 heading per page"
            ))

        # Check H1 length
        for h1 in h1_headings:
            if len(h1.text) < self.min_h1_length:
                issues.append(Issue(
                    level="warning",
                    category="seo",
                    message=f"H1 too short ({len(h1.text)} chars)",
                    suggestion=f"Expand H1 to at least {self.min_h1_length} characters"
                ))

        # Check heading hierarchy
        issues.extend(self._check_hierarchy(headings))

        return issues
```

**Option B: Update Tests to Match Current Behavior** (if intentionally simplified)
```python
# If SEO validation is now handled differently
@pytest.mark.skip(reason="SEO validation moved to external tool")
class TestSEOHeadingValidation:
    ...
```

### 3.4 Modular Validators Analysis

**Key Changes**:
1. `ValidatorRouter` now dispatches to validators by type
2. Validators implement `BaseValidator` interface
3. Configuration loaded from YAML files

**Test Updates Required**:

```python
# Before (old architecture)
def test_validator_router_routing(self):
    router = ValidatorRouter()
    result = router.route("yaml", content)  # Old API

# After (new architecture)
async def test_validator_router_routing(self, config_loader):
    router = ValidatorRouter(config_loader)
    await router.initialize()
    result = await router.validate(
        content=content,
        file_path="test.yaml",
        validation_types=["yaml"]
    )
```

### 3.5 Implementation Steps

1. **Audit current validator architecture**:
   ```
   agents/validators/base_validator.py
   agents/validators/yaml_validator.py
   agents/validators/markdown_validator.py
   agents/validators/seo_validator.py
   core/validator_router.py
   ```

2. **Document expected validator interface**

3. **Implement missing validators** (SEO, etc.)

4. **Update test fixtures** for new architecture:
   ```python
   @pytest.fixture
   async def validator_router(config_loader):
       router = ValidatorRouter(config_loader)
       await router.initialize()
       return router
   ```

5. **Rewrite tests** to use new API patterns

### 3.6 Verification

```bash
pytest tests/agents/test_modular_validators.py -v
pytest tests/agents/test_seo_validation.py -v
```

---

## Phase 4: Infrastructure API Updates

**Goal**: Fix ~14 tests for Cache/Logger API changes
**Estimated Effort**: 2 hours
**Priority**: P2 - Infrastructure components

### 4.1 CacheManager API

**Issue**: `CacheManager.clear()` doesn't exist

**Current API Investigation**:
```python
# Check actual CacheManager interface
# core/cache.py
class CacheManager:
    async def invalidate(self, key: str) -> bool: ...
    async def invalidate_pattern(self, pattern: str) -> int: ...
    async def clear_l1(self) -> None: ...
    async def clear_l2(self) -> None: ...
    async def clear_all(self) -> None: ...  # This might exist
```

**Solution**:
```python
# If clear_all() exists but named differently
cache.clear_all()  # instead of cache.clear()

# If truly missing, add to CacheManager:
async def clear(self) -> None:
    """Clear all cache entries."""
    await self.clear_l1()
    await self.clear_l2()
```

**Affected Tests**:
```
tests/api/test_new_endpoints.py::TestConfigurationControl::test_cache_control_*
tests/cli/test_new_commands.py::TestAdminCommands::test_admin_cache_*
```

### 4.2 Logger API (structlog)

**Issue**: `BoundLoggerFilteringAtNotset.setLevel()` doesn't exist

**Root Cause**: structlog's bound loggers don't have `setLevel()` - that's a stdlib logging method

**Solution**:
```python
# Wrong approach
logger.setLevel(logging.DEBUG)  # AttributeError

# Correct approach for structlog
import structlog
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG)
)

# Or use stdlib logger configuration
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

**Server Code Fix** (`api/server.py`):
```python
# Before
@app.post("/admin/log-level")
async def set_log_level(level: str):
    logger.setLevel(level)  # Wrong

# After
@app.post("/admin/log-level")
async def set_log_level(level: str):
    import logging
    numeric_level = getattr(logging, level.upper())
    logging.getLogger().setLevel(numeric_level)
    # Reconfigure structlog if needed
```

### 4.3 Implementation Steps

1. **Audit CacheManager interface** in `core/cache.py`
2. **Add missing methods** or update tests
3. **Fix logger level endpoint** in `api/server.py`
4. **Update test expectations**

### 4.4 Verification

```bash
pytest tests/api/test_new_endpoints.py::TestConfigurationControl -v
pytest tests/cli/test_new_commands.py::TestAdminCommands -v
```

---

## Phase 5: Windows Compatibility

**Goal**: Fix ~43 tests failing due to encoding issues
**Estimated Effort**: 1 hour
**Priority**: P2 - Platform compatibility

### 5.1 Root Cause

Windows default encoding `cp1252` cannot encode Unicode characters like `✓`, `✗`, `→`

**Error**: `UnicodeEncodeError: 'charmap' codec can't encode character`

### 5.2 Solution

**Fix 1: Set UTF-8 encoding in pytest.ini**
```ini
[pytest]
# Add to existing pytest.ini
env =
    PYTHONIOENCODING=utf-8
```

**Fix 2: Configure test environment in conftest.py**
```python
# tests/conftest.py - add at top
import sys
import os

# Ensure UTF-8 encoding on Windows
if sys.platform == "win32":
    # Set environment for subprocesses
    os.environ["PYTHONIOENCODING"] = "utf-8"

    # Reconfigure stdout/stderr if needed
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')
```

**Fix 3: Use ASCII-safe characters in test output**
```python
# Before
print("✓ Test passed")
print("✗ Test failed")

# After (cross-platform)
print("[PASS] Test passed")
print("[FAIL] Test failed")
```

**Fix 4: Encode output explicitly where needed**
```python
# For test assertions with unicode
def safe_str(s: str) -> str:
    """Encode string safely for Windows console."""
    try:
        return s.encode('cp1252', errors='replace').decode('cp1252')
    except:
        return s.encode('ascii', errors='replace').decode('ascii')
```

### 5.3 Affected Files

```
tests/api/test_websocket_connection.py
tests/api/test_export_endpoints_comprehensive.py (many tests)
```

### 5.4 Verification

```bash
# Run on Windows with verbose output
pytest tests/api/test_websocket_connection.py -v
pytest tests/api/test_export_endpoints_comprehensive.py -v
```

---

## Phase 6: Logic Fixes

**Goal**: Fix 4 language detection tests + misc logic issues
**Estimated Effort**: 2 hours
**Priority**: P3 - Feature correctness

### 6.1 Language Detection

**File**: `core/language_utils.py`

**Issue**: Path patterns not correctly identifying English paths

**Test Expectations**:
```python
# Expected: "en" for English paths
assert detect_language("/docs/en/guide.md") == "en"
assert detect_language("C:\\docs\\en\\guide.md") == "en"
assert detect_language("/blog/en/post.md") == "en"
```

**Investigation**:
1. Read current implementation in `core/language_utils.py`
2. Check path parsing logic for Windows vs Unix paths
3. Verify subdomain vs path-based language detection

**Potential Fixes**:
```python
def detect_language(file_path: str) -> str:
    """Detect language from file path."""
    # Normalize path separators
    normalized = file_path.replace("\\", "/").lower()

    # Check for language codes in path segments
    segments = normalized.split("/")
    for segment in segments:
        if segment in LANGUAGE_CODES:
            return segment

    # Default to English
    return "en"
```

### 6.2 Implementation Steps

1. **Read test expectations** in `tests/test_language_detection.py`
2. **Read current implementation** in `core/language_utils.py`
3. **Identify logic gaps**
4. **Fix implementation** to match expected behavior
5. **Add edge case tests**

### 6.3 Verification

```bash
pytest tests/test_language_detection.py -v
```

---

## Phase 7: Cleanup and Maintenance

**Goal**: Handle placeholder tests and missing modules
**Estimated Effort**: 1 hour
**Priority**: P4 - Housekeeping

### 7.1 Placeholder Tests (`assert 1 == 0`)

These tests were written as placeholders but never implemented.

**Options**:
1. **Implement the tests** if feature exists
2. **Mark as skip** with reason if feature is planned
3. **Delete** if feature was abandoned

**Affected Tests**:
```
tests/cli/test_new_commands.py::TestValidationsCommands::test_validations_history_nonexistent_file
tests/cli/test_new_commands.py::TestAdminCommands::test_admin_cache_* (4 tests)
tests/cli/test_new_commands.py::TestIntegrationWorkflows::test_admin_workflow
```

**Recommendation**: Mark as skip with TODO
```python
@pytest.mark.skip(reason="TODO: Implement cache admin commands")
def test_admin_cache_stats(self):
    pass
```

### 7.2 Missing Module: `rule_manager`

**Tests**:
```
tests/startup/test_rule_manager_imports.py::test_import_rule_manager_top_level
tests/startup/test_rule_manager_imports.py::test_import_rule_manager_from_top_level
```

**Investigation**:
1. Check if `rule_manager` module ever existed
2. Check if it was renamed or moved
3. Check if tests are obsolete

**Solution Options**:
- If module was renamed: Update import paths
- If module was removed: Delete tests
- If module should exist: Create it

### 7.3 Verification

```bash
pytest tests/cli/test_new_commands.py -v
pytest tests/startup/test_rule_manager_imports.py -v
```

---

## Phase 8: Test Infrastructure Improvements

**Goal**: Prevent future test drift
**Estimated Effort**: 3 hours
**Priority**: P3 - Long-term maintainability

### 8.1 Add API Contract Tests

Create tests that verify public APIs haven't changed:

```python
# tests/contracts/test_database_contract.py
def test_database_manager_has_required_methods():
    """Ensure DatabaseManager maintains expected interface."""
    from core.database import DatabaseManager

    required_methods = [
        "create_validation_result",
        "create_recommendation",
        "get_validation",
        "get_recommendations",
        "update_validation_status"
    ]

    for method in required_methods:
        assert hasattr(DatabaseManager, method), f"Missing: {method}"
```

### 8.2 Add Type Checking to CI

```yaml
# .github/workflows/test.yml
- name: Type Check
  run: |
    pip install mypy
    mypy agents/ api/ core/ --ignore-missing-imports
```

### 8.3 Add Test Coverage Requirements

```ini
# pytest.ini
[pytest]
addopts = --cov=agents --cov=api --cov=core --cov-fail-under=80
```

### 8.4 Document Test Patterns

Create `tests/README.md`:
```markdown
# Test Patterns

## Fixtures
- Use `db_session` for database access
- Use `agent_bus` for agent lifecycle
- Use `test_client` for API tests

## Mocking
- Mock external services (Ollama, etc.)
- Don't mock internal components unless necessary

## Naming
- `test_<feature>_<scenario>_<expected_result>`
- Example: `test_validation_missing_file_returns_error`
```

---

## Execution Schedule

### Week 1: Foundation (Phases 1-2)
- [ ] Day 1-2: DatabaseManager API fixes (Phase 1)
- [ ] Day 3-4: Agent contract alignment (Phase 2)
- [ ] Day 5: Review and verification

### Week 2: Features (Phases 3-4)
- [ ] Day 1-3: Validator architecture (Phase 3)
- [ ] Day 4: Infrastructure APIs (Phase 4)
- [ ] Day 5: Review and verification

### Week 3: Polish (Phases 5-8)
- [ ] Day 1: Windows compatibility (Phase 5)
- [ ] Day 2: Logic fixes (Phase 6)
- [ ] Day 3: Cleanup (Phase 7)
- [ ] Day 4-5: Infrastructure improvements (Phase 8)

---

## Verification Checklist

### Per-Phase Verification
- [ ] All targeted tests pass
- [ ] No new test failures introduced
- [ ] No test warnings (unless documented)
- [ ] Code changes documented

### Final Verification
```bash
# Full test suite
pytest tests/ --ignore=tests/manual/ -v

# With coverage
pytest tests/ --ignore=tests/manual/ --cov=. --cov-report=term-missing

# Performance check
pytest tests/ --ignore=tests/manual/ --durations=10
```

### Acceptance Criteria
- [ ] 0 test failures
- [ ] 0 test errors
- [ ] < 10 skipped tests (with documented reasons)
- [ ] Test execution < 5 minutes
- [ ] Coverage > 80%

---

## Appendix A: Quick Reference Commands

```bash
# Run specific test file
pytest tests/agents/test_base.py -v

# Run tests matching pattern
pytest -k "database" -v

# Run with verbose failure output
pytest --tb=long -v

# Run and stop on first failure
pytest -x -v

# Run with coverage for specific module
pytest --cov=core.database tests/

# List all tests without running
pytest --collect-only

# Run only previously failed tests
pytest --lf -v
```

## Appendix B: File Reference

| File | Purpose |
|------|---------|
| `tests/conftest.py` | Shared fixtures and configuration |
| `tests/utils/` | Test utility functions |
| `core/database.py` | DatabaseManager implementation |
| `agents/base_agent.py` | Base agent class |
| `core/cache.py` | CacheManager implementation |
| `core/language_utils.py` | Language detection |
| `agents/validators/` | Validator implementations |
