# TBCV Test Coverage Remediation Plan

## Executive Summary

**Current State**: 1130 passed, 386 failed, 44 skipped, 14 errors
**Target State**: 95%+ pass rate with meaningful test coverage

This plan categorizes all failing tests and provides a systematic approach to fix them while ensuring system stability.

---

## Failure Categories

### Category 1: Async Event Loop Issues (INFRASTRUCTURE)
**Impact**: ~200 tests affected
**Root Cause**: Tests using `asyncio.run()` directly or not properly managing async fixtures
**Risk Level**: LOW (test infrastructure only, no system changes needed)

#### Affected Files:
| File | Tests | Priority |
|------|-------|----------|
| tests/test_performance.py | 9 | P2 |
| tests/test_fuzzy_logic.py | 6 | P2 |
| tests/test_websocket.py | 5 | P2 |
| tests/test_recommendations.py | 7 | P2 |
| tests/test_truth_validation.py | 14 | P2 |
| tests/test_truth_llm_validation.py | 10 | P2 |
| tests/test_idempotence_and_schemas.py | 7 | P2 |
| tests/api/test_batch_enhancement.py | 7 | P2 |
| tests/agents/test_*.py | ~50 | P2 |
| tests/api/test_dashboard_*.py | ~60 | P2 |
| tests/cli/test_*.py | ~30 | P2 |

#### Solution:
```python
# Add to tests/conftest.py
import pytest
import asyncio

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

# All async tests must use @pytest.mark.asyncio decorator
```

#### Action Type: TEST UPDATE
- No system changes required
- Update test infrastructure in conftest.py
- Add `@pytest.mark.asyncio` to async tests

---

### Category 2: Missing Fixture 'test_agent' (TEST UPDATE)
**Impact**: 3 tests in tests/test_checkpoints.py
**Root Cause**: Fixture was renamed or removed during refactoring
**Risk Level**: LOW

#### Affected Tests:
- test_checkpoint_stored_in_database
- test_checkpoint_has_timestamp
- test_checkpoint_to_dict

#### Solution:
Either add `test_agent` fixture to conftest.py or update tests to use existing `mock_orchestrator` or similar fixture.

#### Action Type: TEST UPDATE

---

### Category 3: Database API Mismatch - create_workflow() (TEST UPDATE)
**Impact**: 4 tests in tests/api/test_export_endpoints_comprehensive.py
**Root Cause**: `create_workflow()` doesn't accept `type` parameter
**Risk Level**: LOW

#### Error:
```
TypeError: DatabaseManager.create_workflow() got an unexpected keyword argument 'type'
```

#### Solution:
Check `core/database.py` for actual `create_workflow()` signature and update test fixtures.

#### Action Type: TEST UPDATE

---

### Category 4: Missing Module 'rule_manager' (OBSOLETE TESTS)
**Impact**: 10 tests in tests/test_generic_validator.py
**Root Cause**: Module was moved to `core.rule_manager`
**Risk Level**: LOW

#### Affected Tests:
- TestRuleManager::test_load_family_rules_words
- TestRuleManager::test_api_patterns_loaded
- TestRuleManager::test_non_editable_fields_include_global
- TestGenericContentValidator::* (7 tests)

#### Solution Options:
1. **PREFERRED**: Update imports from `rule_manager` to `core.rule_manager`
2. **ALTERNATIVE**: Mark tests as skipped if module is deprecated

#### Action Type: TEST UPDATE

---

### Category 5: Method Not Found - enhance_with_recommendations (API CHANGE)
**Impact**: ~20 tests across multiple files
**Root Cause**: EnhancementAgent API changed, method renamed or signature modified
**Risk Level**: MEDIUM

#### Affected Files:
- tests/test_e2e_workflows.py
- tests/agents/test_enhancement_agent.py
- tests/agents/test_enhancement_agent_comprehensive.py

#### Error:
```
Exception: Agent error: Method not found: enhance_with_recommendations
```

#### Investigation Required:
1. Check `agents/enhancement_agent.py` for current method names
2. Determine if method was renamed or removed
3. Update tests to use new API

#### Action Type: TEST UPDATE (likely) or POTENTIAL SYSTEM ISSUE

---

### Category 6: Response Format Changes (TEST UPDATE)
**Impact**: ~15 tests
**Root Cause**: API response structures changed

#### Specific Issues:

##### 6.1 Health Status String
```python
# OLD: Expected 'healthy', 'ok', 'live'
# NEW: Returns 'alive'
assert status in ['healthy', 'ok', 'live', 'alive']  # Add 'alive'
```
**Files**: tests/test_everything.py

##### 6.2 Dict vs Object Access
```python
# OLD: response.method
# NEW: response['method'] or response is a dict
```
**Files**: tests/test_endpoints_offline.py

##### 6.3 String vs Dict Response
```python
# OLD: string indices must be integers
# NEW: Response is now dict, not string
```
**Files**: tests/test_everything.py

#### Action Type: TEST UPDATE

---

### Category 7: Agent Registration Issues (SYSTEM CHECK)
**Impact**: ~5 tests
**Root Cause**: Agents not properly registered at test time
**Risk Level**: MEDIUM - May indicate actual system issue

#### Errors:
- "Validation not found"
- "Content validator agent not available"

#### Affected Files:
- tests/test_enhancer_consumes_validation.py
- tests/test_validation_persistence.py
- tests/test_truths_and_rules.py

#### Investigation Required:
1. Check if agents are registered in test fixtures
2. Verify agent registration in server startup
3. May need to add agent setup in conftest.py

#### Action Type: TEST UPDATE or SYSTEM FIX

---

### Category 8: Path Comparison Issues (TEST UPDATE)
**Impact**: 2 tests
**Root Cause**: Windows absolute paths vs relative paths

#### Error:
```
AssertionError: assert 'C:\\Users\\p..._flow_test.md' == 'data_flow_test.md'
```

#### Solution:
Use `os.path.basename()` or normalize paths before comparison.

#### Action Type: TEST UPDATE

---

### Category 9: Placeholder Tests (TEST REMOVAL)
**Impact**: ~5 tests
**Root Cause**: Tests with `assert 1 == 0` or incomplete implementations

#### Solution:
Either implement the tests or mark as `@pytest.mark.skip(reason="TODO: ...")`

#### Action Type: TEST UPDATE or REMOVAL

---

## Priority Matrix

### P0 - Critical (Block Release)
None - all issues are test-related

### P1 - High (Fix This Week)
| Category | Tests | Effort | Action |
|----------|-------|--------|--------|
| Cat 1 - Event Loop | ~200 | 2h | Infrastructure fix in conftest.py |
| Cat 5 - Method Names | ~20 | 2h | Update to new API |
| Cat 7 - Agent Registration | ~5 | 1h | Verify system + fix tests |

### P2 - Medium (Fix This Sprint)
| Category | Tests | Effort | Action |
|----------|-------|--------|--------|
| Cat 2 - Missing Fixture | 3 | 30m | Add fixture or update tests |
| Cat 3 - create_workflow | 4 | 30m | Update fixture parameters |
| Cat 4 - Module Import | 10 | 1h | Update import paths |
| Cat 6 - Response Formats | ~15 | 1h | Update assertions |
| Cat 8 - Path Comparison | 2 | 15m | Normalize paths |

### P3 - Low (Backlog)
| Category | Tests | Effort | Action |
|----------|-------|--------|--------|
| Cat 9 - Placeholders | ~5 | - | Skip or remove |

---

## Implementation Waves

### Wave 1: Infrastructure (P1) - Estimated 4 hours
**Goal**: Fix event loop issues affecting ~200 tests

#### Tasks:
1. **Task 1.1**: Update conftest.py with session-scoped event loop
   - Add `event_loop` fixture
   - Configure pytest-asyncio properly

2. **Task 1.2**: Audit all async tests
   - Ensure `@pytest.mark.asyncio` decorator is present
   - Replace `asyncio.run()` with proper await patterns

#### Files to Modify:
- tests/conftest.py
- pytest.ini (asyncio_mode setting)

#### Verification:
```bash
pytest tests/test_performance.py tests/test_fuzzy_logic.py tests/test_websocket.py -v
```

---

### Wave 2: API Alignment (P1) - Estimated 3 hours
**Goal**: Fix method/API mismatches

#### Tasks:
1. **Task 2.1**: EnhancementAgent API alignment
   - Read agents/enhancement_agent.py for current methods
   - Update test expectations to match

2. **Task 2.2**: Agent registration in tests
   - Add agent setup fixtures
   - Ensure agents are available before tests run

#### Files to Modify:
- tests/agents/test_enhancement_agent.py
- tests/agents/test_enhancement_agent_comprehensive.py
- tests/test_e2e_workflows.py
- tests/conftest.py (agent fixtures)

---

### Wave 3: Test Updates (P2) - Estimated 3 hours
**Goal**: Fix fixture and assertion issues

#### Tasks:
1. **Task 3.1**: Add missing fixtures
   - `test_agent` fixture for checkpoint tests

2. **Task 3.2**: Fix create_workflow parameters
   - Remove or rename `type` parameter

3. **Task 3.3**: Update import paths
   - `rule_manager` → `core.rule_manager`

4. **Task 3.4**: Fix response format assertions
   - Add 'alive' to health status options
   - Update dict/object access patterns

5. **Task 3.5**: Normalize path comparisons
   - Use os.path.basename() for file comparisons

---

### Wave 4: Cleanup (P3) - Estimated 1 hour
**Goal**: Handle placeholder and obsolete tests

#### Tasks:
1. **Task 4.1**: Skip or implement placeholder tests
2. **Task 4.2**: Remove truly obsolete tests
3. **Task 4.3**: Update test documentation

---

## System Changes Assessment

### SAFE Changes (Test Only)
- Event loop fixture updates
- Import path corrections
- Assertion updates
- Fixture additions

### REQUIRES REVIEW (Potential System Impact)
None identified - all failures appear to be test-related

### DO NOT CHANGE
- Core system behavior should NOT be modified to make tests pass
- If a test fails due to legitimate behavior change, update the test

---

## Detailed Test File Analysis

### Files to UPDATE (Test Changes Only)
| File | Issue Count | Categories |
|------|-------------|------------|
| tests/conftest.py | N/A | Cat 1, 2, 7 |
| tests/test_performance.py | 9 | Cat 1 |
| tests/test_fuzzy_logic.py | 6 | Cat 1 |
| tests/test_websocket.py | 5 | Cat 1 |
| tests/test_generic_validator.py | 10 | Cat 4 |
| tests/test_e2e_workflows.py | 5 | Cat 5, 8 |
| tests/test_everything.py | 5 | Cat 6 |
| tests/test_checkpoints.py | 3 | Cat 2 |
| tests/api/test_export_endpoints_comprehensive.py | 4 | Cat 3 |
| tests/agents/test_enhancement_agent*.py | ~30 | Cat 1, 5 |

### Files to SKIP (Stub/Placeholder)
| File | Reason |
|------|--------|
| tests/api/test_export_endpoints.py | Already skipped - stub module |

### Files to DELETE (Obsolete)
None recommended at this time - all tests appear to have valid purposes

---

## Verification Plan

After each wave, run:
```bash
# Full test suite
pytest tests/ --ignore=tests/manual/ --ignore=tests/test_endpoints_live.py --ignore=tests/test_truth_llm_validation_real.py -v --tb=short

# Specific category verification
pytest tests/test_performance.py -v  # Wave 1
pytest tests/agents/ -v               # Wave 2
pytest tests/test_checkpoints.py -v   # Wave 3
```

---

## Risk Mitigation

1. **Backup**: Create git branch before starting
2. **Incremental**: Fix one category at a time
3. **Verify**: Run full test suite after each wave
4. **Document**: Update this plan with actual results

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Passed | 1130 | 1500+ |
| Failed | 386 | <20 |
| Skipped | 44 | <50 |
| Errors | 14 | 0 |
| Pass Rate | 72% | 95%+ |

---

## Appendix A: Full Failure List by File

### tests/ (root level)
- test_cli_web_parity.py: 1
- test_e2e_workflows.py: 5
- test_endpoints_offline.py: 1
- test_enhancer_consumes_validation.py: 1
- test_everything.py: 5
- test_framework.py: 1
- test_fuzzy_logic.py: 6
- test_generic_validator.py: 10
- test_idempotence_and_schemas.py: 7
- test_performance.py: 9
- test_recommendation_enhancer.py: 11
- test_recommendations.py: 7
- test_truth_llm_validation.py: 10
- test_truth_validation.py: 14
- test_truths_and_rules.py: 6
- test_validation_persistence.py: 1
- test_websocket.py: 5
- test_checkpoints.py: 3 (ERROR)

### tests/agents/
- test_base.py: 5
- test_enhancement_agent.py: 11
- test_enhancement_agent_comprehensive.py: 17
- test_fuzzy_detector.py: 6
- test_heading_sizes.py: 13
- test_modular_validators.py: 38
- test_orchestrator.py: 17
- test_seo_validation.py: 12 (partial)

### tests/api/
- test_batch_enhancement.py: 7 (ERROR)
- test_export_endpoints_comprehensive.py: 4 (ERROR)
- test_dashboard_*.py: ~60 combined

### tests/cli/
- test_workflow_*.py: ~30 combined

### tests/core/
- test_database.py: 2
- test_ingestion.py: 1
- test_ollama.py: 1
- test_performance.py: 6
- test_prompt_loader.py: 1
- test_validator_router.py: 15

### tests/e2e/
- test_dashboard_flows.py: 2
