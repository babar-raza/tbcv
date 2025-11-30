# TBCV Test Coverage Remediation - Task Cards

## Overview
- **Total Failing Tests**: 386 failed, 14 errors
- **Total Passing Tests**: 1130 passed, 44 skipped
- **Target**: 95%+ pass rate (1500+ passing)

Each task must be implemented end-to-end with no TODOs or partial implementations.

---

## Wave 1: Async Event Loop Infrastructure

### Task 1.1: Fix Pytest-Asyncio Event Loop Configuration

**Role**: Senior engineer. Produce drop-in, production-ready code.

**Scope (only this)**:
- Fix: Async event loop not properly managed across test session
- Root cause: Tests use `asyncio.run()` or lack proper event loop fixture
- Impact: ~200 tests failing with "RuntimeError: Event loop is closed"

**Allowed paths**:
- tests/conftest.py
- pytest.ini

**Forbidden**: Any production code, any other test files (those come in later tasks)

**Investigation first**:
1. Read current conftest.py event_loop fixture (if any)
2. Check pytest.ini asyncio_mode setting
3. Verify pytest-asyncio version compatibility

**Changes required**:
```python
# In tests/conftest.py - add or replace event_loop fixture
@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()
```

**pytest.ini changes**:
```ini
[pytest]
asyncio_mode = auto
```

**Acceptance checks (must pass locally)**:
```powershell
# Verify event loop fixture is recognized
powershell -NoProfile -Command "cd 'c:\Users\prora\OneDrive\Documents\GitHub\tbcv'; C:\Users\prora\anaconda3\shell\condabin\conda-hook.ps1; conda activate llm; python -m pytest tests/test_performance.py -v --import-mode=importlib -p no:capture"

# Expected: No "Event loop is closed" errors
```

**Deliverables**:
- Full replacement for relevant sections of tests/conftest.py
- Updated pytest.ini with asyncio configuration

**Hard rules**:
- Windows friendly paths, CRLF preserved
- Do not break existing fixtures
- Scope must be "session" to avoid loop recreation
- Zero new dependencies

**Self-review checklist**:
- [ ] Event loop persists across entire test session
- [ ] No "Event loop is closed" errors in test_performance.py
- [ ] Existing fixtures still work
- [ ] pytest.ini is valid

---

### Task 1.2: Add Missing @pytest.mark.asyncio Decorators

**Role**: Senior engineer. Produce drop-in, production-ready code.

**Scope (only this)**:
- Fix: Async tests missing proper pytest-asyncio markers
- Impact: Tests that need async but don't have decorators

**Allowed paths**:
- tests/test_performance.py
- tests/test_fuzzy_logic.py
- tests/test_websocket.py
- tests/test_recommendations.py
- tests/test_truth_validation.py
- tests/test_truth_llm_validation.py
- tests/test_idempotence_and_schemas.py

**Forbidden**: Production code, tests/conftest.py (done in 1.1)

**Investigation first**:
1. Grep for `async def test_` in each file
2. Check if `@pytest.mark.asyncio` is present
3. Check if `asyncio.run()` is used (should be replaced with await)

**Changes required**:
- Add `@pytest.mark.asyncio` to all async test functions
- Replace `asyncio.run(coroutine())` with `await coroutine()`
- Ensure test functions are `async def` where needed

**Acceptance checks**:
```powershell
# Run all affected files
powershell -NoProfile -Command "cd 'c:\Users\prora\OneDrive\Documents\GitHub\tbcv'; C:\Users\prora\anaconda3\shell\condabin\conda-hook.ps1; conda activate llm; python -m pytest tests/test_performance.py tests/test_fuzzy_logic.py tests/test_websocket.py -v --import-mode=importlib -p no:capture -q 2>&1 | Select-Object -Last 20"

# Expected: 0 "Event loop is closed" errors
```

**Deliverables**:
- Full file replacements for each affected test file

**Hard rules**:
- Do not change test logic, only async handling
- Preserve all existing test assertions
- Windows CRLF preserved

---

## Wave 2: API and Method Alignment

### Task 2.1: Fix EnhancementAgent Method Names in Tests

**Role**: Senior engineer. Produce drop-in, production-ready code.

**Scope (only this)**:
- Fix: Tests call `enhance_with_recommendations` which no longer exists
- Error: "Agent error: Method not found: enhance_with_recommendations"

**Allowed paths (modify)**:
- tests/agents/test_enhancement_agent.py
- tests/agents/test_enhancement_agent_comprehensive.py
- tests/test_e2e_workflows.py

**Allowed paths (read only)**:
- agents/enhancement_agent.py (to find correct method names)

**Forbidden**: Modifying agents/enhancement_agent.py

**Investigation first**:
1. Read agents/enhancement_agent.py to find actual method names
2. List all methods registered via `register_handler`
3. Map old method names to new ones

**Expected mapping** (verify by reading actual file):
```
OLD                          -> NEW
enhance_with_recommendations -> enhance_content (or similar)
```

**Acceptance checks**:
```powershell
powershell -NoProfile -Command "cd 'c:\Users\prora\OneDrive\Documents\GitHub\tbcv'; C:\Users\prora\anaconda3\shell\condabin\conda-hook.ps1; conda activate llm; python -m pytest tests/agents/test_enhancement_agent.py tests/agents/test_enhancement_agent_comprehensive.py -v --import-mode=importlib -p no:capture -q 2>&1 | Select-Object -Last 30"

# Expected: No "Method not found" errors
```

**Deliverables**:
- Full file replacements for each test file
- Updated method calls matching actual API

---

### Task 2.2: Fix Agent Registration in Test Fixtures

**Role**: Senior engineer. Produce drop-in, production-ready code.

**Scope (only this)**:
- Fix: Tests fail with "Content validator agent not available" or "Validation not found"
- Root cause: Agents not registered before tests run

**Allowed paths (modify)**:
- tests/conftest.py (add agent registration fixtures)
- tests/test_enhancer_consumes_validation.py
- tests/test_validation_persistence.py
- tests/test_truths_and_rules.py

**Allowed paths (read only)**:
- agents/*.py (to understand registration)
- api/server.py (to see how agents are registered at startup)

**Forbidden**: Modifying production agent code

**Investigation first**:
1. Check how agents are registered in api/server.py startup
2. Check existing mock_* fixtures in conftest.py
3. Determine if tests need real agents or mocks

**Changes required**:
- Add fixtures that register required agents before tests
- Or update tests to properly mock agent responses

**Acceptance checks**:
```powershell
powershell -NoProfile -Command "cd 'c:\Users\prora\OneDrive\Documents\GitHub\tbcv'; C:\Users\prora\anaconda3\shell\condabin\conda-hook.ps1; conda activate llm; python -m pytest tests/test_enhancer_consumes_validation.py tests/test_validation_persistence.py -v --import-mode=importlib -p no:capture"

# Expected: No "agent not available" errors
```

**Deliverables**:
- Updated conftest.py with agent fixtures
- Updated test files with proper fixture usage

---

## Wave 3: Fixture and Import Fixes

### Task 3.1: Add Missing 'test_agent' Fixture

**Role**: Senior engineer. Produce drop-in, production-ready code.

**Scope (only this)**:
- Fix: `fixture 'test_agent' not found` in tests/test_checkpoints.py
- Impact: 3 tests failing at setup

**Allowed paths (modify)**:
- tests/conftest.py
- tests/test_checkpoints.py

**Forbidden**: Production code

**Investigation first**:
1. Read tests/test_checkpoints.py to understand what `test_agent` should provide
2. Check if similar fixtures exist (mock_orchestrator, etc.)
3. Determine fixture requirements

**Changes required**:
Either:
1. Add `test_agent` fixture to conftest.py matching expected interface
2. Or update tests to use existing fixtures

**Acceptance checks**:
```powershell
powershell -NoProfile -Command "cd 'c:\Users\prora\OneDrive\Documents\GitHub\tbcv'; C:\Users\prora\anaconda3\shell\condabin\conda-hook.ps1; conda activate llm; python -m pytest tests/test_checkpoints.py -v --import-mode=importlib -p no:capture"

# Expected: All 3 checkpoint tests pass or show different failure (not fixture error)
```

**Deliverables**:
- Updated conftest.py with test_agent fixture
- Or updated test_checkpoints.py with correct fixture usage

---

### Task 3.2: Fix create_workflow() Parameter Mismatch

**Role**: Senior engineer. Produce drop-in, production-ready code.

**Scope (only this)**:
- Fix: `TypeError: DatabaseManager.create_workflow() got an unexpected keyword argument 'type'`
- Impact: 4 tests in tests/api/test_export_endpoints_comprehensive.py

**Allowed paths (modify)**:
- tests/api/test_export_endpoints_comprehensive.py

**Allowed paths (read only)**:
- core/database.py (to find correct signature)

**Forbidden**: Modifying core/database.py

**Investigation first**:
1. Read core/database.py `create_workflow()` method signature
2. Find what parameters it actually accepts
3. Map old parameter names to new ones

**Changes required**:
- Update test fixtures that call `create_workflow()`
- Remove or rename `type` parameter to match actual signature

**Acceptance checks**:
```powershell
powershell -NoProfile -Command "cd 'c:\Users\prora\OneDrive\Documents\GitHub\tbcv'; C:\Users\prora\anaconda3\shell\condabin\conda-hook.ps1; conda activate llm; python -m pytest tests/api/test_export_endpoints_comprehensive.py -v --import-mode=importlib -p no:capture -q 2>&1 | Select-Object -Last 20"

# Expected: No TypeError about 'type' argument
```

**Deliverables**:
- Full file replacement for test_export_endpoints_comprehensive.py

---

### Task 3.3: Fix 'rule_manager' Import Path

**Role**: Senior engineer. Produce drop-in, production-ready code.

**Scope (only this)**:
- Fix: `ModuleNotFoundError: No module named 'rule_manager'`
- Actual path: `core.rule_manager`
- Impact: 10 tests in tests/test_generic_validator.py

**Allowed paths (modify)**:
- tests/test_generic_validator.py

**Forbidden**: Moving or renaming production modules

**Changes required**:
```python
# OLD
from rule_manager import RuleManager

# NEW
from core.rule_manager import RuleManager
```

**Acceptance checks**:
```powershell
powershell -NoProfile -Command "cd 'c:\Users\prora\OneDrive\Documents\GitHub\tbcv'; C:\Users\prora\anaconda3\shell\condabin\conda-hook.ps1; conda activate llm; python -m pytest tests/test_generic_validator.py -v --import-mode=importlib -p no:capture -q 2>&1 | Select-Object -Last 20"

# Expected: No ModuleNotFoundError
```

**Deliverables**:
- Full file replacement for tests/test_generic_validator.py

---

### Task 3.4: Fix Response Format Assertions

**Role**: Senior engineer. Produce drop-in, production-ready code.

**Scope (only this)**:
- Fix: Tests expecting wrong response values/formats

**Specific issues**:
1. Health status: expects `'healthy'/'ok'/'live'` but gets `'alive'`
2. Dict access: expects `response.method` but response is dict
3. String indices: expects string but gets dict

**Allowed paths (modify)**:
- tests/test_everything.py
- tests/test_endpoints_offline.py

**Forbidden**: Changing actual API response formats

**Changes required**:
```python
# Issue 1: Health status
# OLD
assert status in ['healthy', 'ok', 'live']
# NEW
assert status in ['healthy', 'ok', 'live', 'alive']

# Issue 2: Dict access
# OLD
assert response.method == 'GET'
# NEW
assert response['method'] == 'GET'
# OR
assert response.get('method') == 'GET'
```

**Acceptance checks**:
```powershell
powershell -NoProfile -Command "cd 'c:\Users\prora\OneDrive\Documents\GitHub\tbcv'; C:\Users\prora\anaconda3\shell\condabin\conda-hook.ps1; conda activate llm; python -m pytest tests/test_everything.py tests/test_endpoints_offline.py -v --import-mode=importlib -p no:capture -q 2>&1 | Select-Object -Last 30"

# Expected: No assertion errors about status or attribute access
```

**Deliverables**:
- Full file replacements for each test file

---

### Task 3.5: Fix Path Comparison in E2E Tests

**Role**: Senior engineer. Produce drop-in, production-ready code.

**Scope (only this)**:
- Fix: Path comparison fails due to absolute vs relative paths
- Error: `assert 'C:\\Users\\p..._flow_test.md' == 'data_flow_test.md'`

**Allowed paths (modify)**:
- tests/test_e2e_workflows.py

**Forbidden**: Changing how system stores paths

**Changes required**:
```python
import os

# OLD
assert result['file_path'] == 'data_flow_test.md'

# NEW
assert os.path.basename(result['file_path']) == 'data_flow_test.md'
# OR
assert result['file_path'].endswith('data_flow_test.md')
```

**Acceptance checks**:
```powershell
powershell -NoProfile -Command "cd 'c:\Users\prora\OneDrive\Documents\GitHub\tbcv'; C:\Users\prora\anaconda3\shell\condabin\conda-hook.ps1; conda activate llm; python -m pytest tests/test_e2e_workflows.py -v --import-mode=importlib -p no:capture -q 2>&1 | Select-Object -Last 20"

# Expected: No assertion errors about path comparison
```

**Deliverables**:
- Full file replacement for tests/test_e2e_workflows.py

---

## Wave 4: Agent Test Fixes

### Task 4.1: Fix tests/agents/test_modular_validators.py

**Role**: Senior engineer. Produce drop-in, production-ready code.

**Scope (only this)**:
- Fix: 38 failing tests in modular validators
- Root cause: Validator API/architecture changed

**Allowed paths (modify)**:
- tests/agents/test_modular_validators.py

**Allowed paths (read only)**:
- agents/validators/base_validator.py
- agents/validators/*.py
- core/validator_router.py

**Forbidden**: Modifying production validator code

**Investigation first**:
1. Read BaseValidator interface
2. Read ValidatorRouter API
3. Map old test expectations to new API

**Changes required**:
- Update validator instantiation
- Update to async patterns where needed
- Fix return type expectations

**Acceptance checks**:
```powershell
powershell -NoProfile -Command "cd 'c:\Users\prora\OneDrive\Documents\GitHub\tbcv'; C:\Users\prora\anaconda3\shell\condabin\conda-hook.ps1; conda activate llm; python -m pytest tests/agents/test_modular_validators.py -v --import-mode=importlib -p no:capture -q 2>&1 | Select-Object -Last 30"

# Expected: 38 tests pass
```

**Deliverables**:
- Full file replacement for tests/agents/test_modular_validators.py

---

### Task 4.2: Fix tests/agents/test_orchestrator.py

**Role**: Senior engineer. Produce drop-in, production-ready code.

**Scope (only this)**:
- Fix: 17 failing tests in orchestrator tests
- Root cause: Orchestrator API changed

**Allowed paths (modify)**:
- tests/agents/test_orchestrator.py

**Allowed paths (read only)**:
- agents/orchestrator.py

**Forbidden**: Modifying production orchestrator code

**Investigation first**:
1. Read agents/orchestrator.py for current API
2. Check handler registrations
3. Map old test expectations to new API

**Acceptance checks**:
```powershell
powershell -NoProfile -Command "cd 'c:\Users\prora\OneDrive\Documents\GitHub\tbcv'; C:\Users\prora\anaconda3\shell\condabin\conda-hook.ps1; conda activate llm; python -m pytest tests/agents/test_orchestrator.py -v --import-mode=importlib -p no:capture -q 2>&1 | Select-Object -Last 30"

# Expected: 17 tests pass
```

**Deliverables**:
- Full file replacement for tests/agents/test_orchestrator.py

---

### Task 4.3: Fix tests/agents/test_heading_sizes.py

**Role**: Senior engineer. Produce drop-in, production-ready code.

**Scope (only this)**:
- Fix: 13 failing tests in heading size validation
- Root cause: SEO/heading validation API changed

**Allowed paths (modify)**:
- tests/agents/test_heading_sizes.py

**Allowed paths (read only)**:
- agents/validators/seo_validator.py
- agents/content_validator.py
- config/seo.yaml

**Forbidden**: Modifying production code

**Acceptance checks**:
```powershell
powershell -NoProfile -Command "cd 'c:\Users\prora\OneDrive\Documents\GitHub\tbcv'; C:\Users\prora\anaconda3\shell\condabin\conda-hook.ps1; conda activate llm; python -m pytest tests/agents/test_heading_sizes.py -v --import-mode=importlib -p no:capture"

# Expected: 13 tests pass
```

**Deliverables**:
- Full file replacement for tests/agents/test_heading_sizes.py

---

### Task 4.4: Fix tests/agents/test_fuzzy_detector.py

**Role**: Senior engineer. Produce drop-in, production-ready code.

**Scope (only this)**:
- Fix: 6 failing tests in fuzzy detector
- Root cause: FuzzyDetector API changed

**Allowed paths (modify)**:
- tests/agents/test_fuzzy_detector.py

**Allowed paths (read only)**:
- agents/fuzzy_detector.py

**Forbidden**: Modifying production fuzzy detector

**Acceptance checks**:
```powershell
powershell -NoProfile -Command "cd 'c:\Users\prora\OneDrive\Documents\GitHub\tbcv'; C:\Users\prora\anaconda3\shell\condabin\conda-hook.ps1; conda activate llm; python -m pytest tests/agents/test_fuzzy_detector.py -v --import-mode=importlib -p no:capture"

# Expected: 6 tests pass
```

**Deliverables**:
- Full file replacement for tests/agents/test_fuzzy_detector.py

---

## Wave 5: Dashboard and CLI Test Fixes

### Task 5.1: Fix tests/api/test_dashboard_*.py Files

**Role**: Senior engineer. Produce drop-in, production-ready code.

**Scope (only this)**:
- Fix: ~60 failing tests across dashboard test files
- Root cause: Dashboard API changes, async issues

**Allowed paths (modify)**:
- tests/api/test_dashboard_enhancements.py
- tests/api/test_dashboard_modals.py
- tests/api/test_dashboard_navigation.py
- tests/api/test_dashboard_recommendations.py
- tests/api/test_dashboard_validations.py
- tests/api/test_dashboard_websocket.py
- tests/api/test_dashboard_workflows.py

**Allowed paths (read only)**:
- api/dashboard.py
- api/server.py

**Forbidden**: Modifying production dashboard code

**Acceptance checks**:
```powershell
powershell -NoProfile -Command "cd 'c:\Users\prora\OneDrive\Documents\GitHub\tbcv'; C:\Users\prora\anaconda3\shell\condabin\conda-hook.ps1; conda activate llm; python -m pytest tests/api/test_dashboard_enhancements.py tests/api/test_dashboard_validations.py -v --import-mode=importlib -p no:capture -q 2>&1 | Select-Object -Last 30"

# Expected: Majority of tests pass
```

**Deliverables**:
- Full file replacements for each dashboard test file

---

### Task 5.2: Fix tests/cli/test_workflow_*.py Files

**Role**: Senior engineer. Produce drop-in, production-ready code.

**Scope (only this)**:
- Fix: ~30 failing tests across CLI workflow tests
- Root cause: CLI command API changes

**Allowed paths (modify)**:
- tests/cli/test_workflow_report.py
- tests/cli/test_workflow_watch.py

**Allowed paths (read only)**:
- cli/main.py

**Forbidden**: Modifying CLI production code

**Acceptance checks**:
```powershell
powershell -NoProfile -Command "cd 'c:\Users\prora\OneDrive\Documents\GitHub\tbcv'; C:\Users\prora\anaconda3\shell\condabin\conda-hook.ps1; conda activate llm; python -m pytest tests/cli/test_workflow_report.py tests/cli/test_workflow_watch.py -v --import-mode=importlib -p no:capture"

# Expected: Tests pass
```

**Deliverables**:
- Full file replacements for each CLI test file

---

## Wave 6: Core and Validator Router Fixes

### Task 6.1: Fix tests/core/test_validator_router.py

**Role**: Senior engineer. Produce drop-in, production-ready code.

**Scope (only this)**:
- Fix: 15 failing tests in validator router
- Root cause: Router API/architecture changed

**Allowed paths (modify)**:
- tests/core/test_validator_router.py

**Allowed paths (read only)**:
- core/validator_router.py

**Forbidden**: Modifying production router code

**Acceptance checks**:
```powershell
powershell -NoProfile -Command "cd 'c:\Users\prora\OneDrive\Documents\GitHub\tbcv'; C:\Users\prora\anaconda3\shell\condabin\conda-hook.ps1; conda activate llm; python -m pytest tests/core/test_validator_router.py -v --import-mode=importlib -p no:capture"

# Expected: 15 tests pass
```

**Deliverables**:
- Full file replacement for tests/core/test_validator_router.py

---

### Task 6.2: Fix tests/core/test_performance.py

**Role**: Senior engineer. Produce drop-in, production-ready code.

**Scope (only this)**:
- Fix: 6 failing tests in core performance
- Root cause: Async/performance API changes

**Allowed paths (modify)**:
- tests/core/test_performance.py

**Allowed paths (read only)**:
- core/performance.py

**Forbidden**: Modifying production performance code

**Acceptance checks**:
```powershell
powershell -NoProfile -Command "cd 'c:\Users\prora\OneDrive\Documents\GitHub\tbcv'; C:\Users\prora\anaconda3\shell\condabin\conda-hook.ps1; conda activate llm; python -m pytest tests/core/test_performance.py -v --import-mode=importlib -p no:capture"

# Expected: 6 tests pass
```

**Deliverables**:
- Full file replacement for tests/core/test_performance.py

---

## Wave 7: Integration and E2E Fixes

### Task 7.1: Fix tests/test_recommendation_enhancer.py

**Role**: Senior engineer. Produce drop-in, production-ready code.

**Scope (only this)**:
- Fix: 11 failing tests in recommendation enhancer
- Root cause: Enhancer API changed

**Allowed paths (modify)**:
- tests/test_recommendation_enhancer.py

**Allowed paths (read only)**:
- agents/enhancement_agent.py
- agents/recommendation_agent.py

**Forbidden**: Modifying production enhancer code

**Acceptance checks**:
```powershell
powershell -NoProfile -Command "cd 'c:\Users\prora\OneDrive\Documents\GitHub\tbcv'; C:\Users\prora\anaconda3\shell\condabin\conda-hook.ps1; conda activate llm; python -m pytest tests/test_recommendation_enhancer.py -v --import-mode=importlib -p no:capture"

# Expected: 11 tests pass
```

**Deliverables**:
- Full file replacement for tests/test_recommendation_enhancer.py

---

### Task 7.2: Fix tests/e2e/test_dashboard_flows.py

**Role**: Senior engineer. Produce drop-in, production-ready code.

**Scope (only this)**:
- Fix: 2 failing E2E dashboard flow tests
- Root cause: Flow API/sequence changed

**Allowed paths (modify)**:
- tests/e2e/test_dashboard_flows.py

**Allowed paths (read only)**:
- api/dashboard.py
- api/server.py

**Forbidden**: Modifying production code

**Acceptance checks**:
```powershell
powershell -NoProfile -Command "cd 'c:\Users\prora\OneDrive\Documents\GitHub\tbcv'; C:\Users\prora\anaconda3\shell\condabin\conda-hook.ps1; conda activate llm; python -m pytest tests/e2e/test_dashboard_flows.py -v --import-mode=importlib -p no:capture"

# Expected: 2 tests pass
```

**Deliverables**:
- Full file replacement for tests/e2e/test_dashboard_flows.py

---

## Final Verification Task

### Task 8.1: Full Test Suite Verification

**Role**: Senior engineer. Verify complete remediation.

**Scope**:
- Run full test suite
- Document any remaining failures
- Ensure no regressions introduced

**Commands**:
```powershell
# Full test suite
powershell -NoProfile -Command "cd 'c:\Users\prora\OneDrive\Documents\GitHub\tbcv'; C:\Users\prora\anaconda3\shell\condabin\conda-hook.ps1; conda activate llm; python -m pytest tests/ --ignore=tests/manual/ --ignore=tests/test_endpoints_live.py --ignore=tests/test_truth_llm_validation_real.py -v --import-mode=importlib --tb=short -q 2>&1 | Tee-Object -FilePath final_verification.txt; Get-Content final_verification.txt | Select-Object -Last 30"
```

**Success Criteria**:
- Passed: 1500+ (was 1130)
- Failed: <20 (was 386)
- Errors: 0 (was 14)
- Pass rate: 95%+

**Deliverables**:
- Final test results summary
- List of any remaining failures with justification
- Updated tests/README.md if needed

---

## Execution Order

| Wave | Tasks | Estimated Time | Cumulative Pass Rate |
|------|-------|----------------|---------------------|
| 1 | 1.1, 1.2 | 4h | 80% |
| 2 | 2.1, 2.2 | 3h | 85% |
| 3 | 3.1-3.5 | 3h | 88% |
| 4 | 4.1-4.4 | 4h | 92% |
| 5 | 5.1, 5.2 | 3h | 94% |
| 6 | 6.1, 6.2 | 2h | 95% |
| 7 | 7.1, 7.2 | 2h | 96% |
| 8 | 8.1 | 1h | Final |

**Total Estimated Time**: 22 hours

---

## Notes

### DO NOT CHANGE (Production Code)
- agents/*.py (read only)
- core/*.py (read only)
- api/*.py (read only)
- cli/*.py (read only)
- config/*.yaml (read only)

### SAFE TO MODIFY (Test Infrastructure)
- tests/conftest.py
- tests/**/*.py
- pytest.ini

### INVESTIGATION REQUIRED
If any test failure appears to be a genuine system bug:
1. Document the issue
2. Create separate task for production fix
3. Do not modify production code within test fix tasks
