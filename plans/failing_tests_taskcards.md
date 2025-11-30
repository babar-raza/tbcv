# Failing Tests Remediation - Task Cards

**Parent Plan**: [failing_tests.md](failing_tests.md)
**Total Tasks**: 14 task cards across 8 phases
**Estimated Total Effort**: ~21 hours

---

## Phase 1: DatabaseManager API Alignment

### Task 1.1: Update DatabaseManager Method Calls in Agent Tests

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Tests using deprecated DatabaseManager method names (save_* → create_*)
- Allowed paths:
  - tests/agents/test_enhancement_agent_comprehensive.py
  - tests/conftest.py (only db-related fixtures)
- Forbidden: any other file, core/database.py

Brief:
- Replace all `db.save_validation_result(...)` with `db.create_validation_result(...)`
- Replace all `db.save_recommendation(...)` with `db.create_recommendation(...)`
- Remove all `db.close()` calls - DatabaseManager uses context managers
- Update fixture `mock_database` to use correct method names in MagicMock specs

Acceptance checks (must pass locally):
- CLI: N/A
- Web: N/A
- Tests: pytest tests/agents/test_enhancement_agent_comprehensive.py -v
- Expected: 22 previously erroring tests now pass or fail with different reason
- No mock data used in production paths

Deliverables:
- Full file replacement for test_enhancement_agent_comprehensive.py
- Updated db fixtures in conftest.py if needed
- No new tests needed (fixing existing)

Hard rules:
- Windows friendly paths, CRLF preserved
- Keep test function signatures unchanged
- Zero network calls in tests
- Deterministic runs: set seeds, stable ordering
- Do not introduce new dependencies

Self-review (answer yes/no at the end):
- Tests updated, method names match actual DatabaseManager API, no close() calls

Now:
1) Show grep output of all occurrences to replace
2) Provide the full updated test file
3) Run pytest and show results
4) Provide runbook: exact commands in order
```

---

### Task 1.2: Update DatabaseManager Method Calls in API Tests

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Tests using deprecated DatabaseManager method names in API test files
- Allowed paths:
  - tests/api/test_export_endpoints_comprehensive.py
  - tests/api/services/test_status_recalculator.py
  - tests/api/services/test_recommendation_consolidator.py
  - tests/test_checkpoints.py
- Forbidden: any other file, core/database.py

Brief:
- Replace `save_validation_result` → `create_validation_result`
- Replace `save_recommendation` → `create_recommendation`
- Remove `db.close()` calls
- Fix fixture setup/teardown that relies on close()

Acceptance checks (must pass locally):
- CLI: N/A
- Web: N/A
- Tests: pytest tests/api/test_export_endpoints_comprehensive.py tests/api/services/ tests/test_checkpoints.py -v
- Expected: 42+ previously erroring tests now pass or fail with different reason

Deliverables:
- Full file replacements for all listed test files
- No new tests needed (fixing existing)

Hard rules:
- Windows friendly paths, CRLF preserved
- Keep test function signatures unchanged
- Zero network calls in tests
- Deterministic runs
- Do not introduce new dependencies

Self-review (answer yes/no at the end):
- All API tests updated, method names correct, no deprecated calls remain

Now:
1) Show grep output of all occurrences per file
2) Provide the full updated files
3) Run pytest and show results
4) Provide runbook
```

---

## Phase 2: Agent Contract Alignment

### Task 2.1: Fix BaseAgent Test Expectations

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: BaseAgent tests expect .start()/.stop() methods that don't exist
- Allowed paths:
  - tests/agents/test_base.py
  - agents/base_agent.py (READ ONLY - to understand actual API)
- Forbidden: modifying agents/base_agent.py

Brief:
- Read agents/base_agent.py to understand current lifecycle API
- Agent lifecycle is managed via AgentBus registration, not start/stop methods
- Update tests to use AgentBus.register()/unregister() pattern
- Update tests checking .handlers to use get_contract().methods instead
- Fix ConcreteAgent test class if needed to match BaseAgent interface

Acceptance checks (must pass locally):
- Tests: pytest tests/agents/test_base.py -v
- Expected: 4 failures fixed (test_agent_start, test_agent_stop, test_agent_process_request_invalid_method, test_agent_handles_method_errors)

Deliverables:
- Full file replacement for test_base.py
- Document actual BaseAgent interface at top of test file in docstring

Hard rules:
- Windows friendly paths, CRLF preserved
- Don't modify production code - only tests
- Zero network calls in tests
- Deterministic runs

Self-review (answer yes/no at the end):
- Tests match actual BaseAgent API, lifecycle tests use AgentBus pattern

Now:
1) Show current BaseAgent interface (read agents/base_agent.py)
2) Show minimal design for test changes
3) Provide full updated test_base.py
4) Provide runbook
```

---

### Task 2.2: Fix EnhancementAgent Test Expectations

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: EnhancementAgent tests expect old API (.capabilities, .applied_count)
- Allowed paths:
  - tests/agents/test_enhancement_agent.py
  - agents/enhancement_agent.py (READ ONLY)
- Forbidden: modifying agents/enhancement_agent.py

Brief:
- Read agents/enhancement_agent.py to understand current API
- Replace .capabilities checks with get_contract().methods
- Replace EnhancementResult.applied_count with len(result.results) or equivalent
- Update method name expectations (enhance_with_recommendations → enhance_content)
- Fix all 12 failing tests in this file

Acceptance checks (must pass locally):
- Tests: pytest tests/agents/test_enhancement_agent.py -v
- Expected: 12 failures fixed

Deliverables:
- Full file replacement for test_enhancement_agent.py
- Document actual EnhancementAgent API in test file docstring

Hard rules:
- Windows friendly paths, CRLF preserved
- Don't modify production code - only tests
- Zero network calls in tests
- Deterministic runs

Self-review (answer yes/no at the end):
- Tests use correct API, all assertions match actual EnhancementAgent behavior

Now:
1) Show current EnhancementAgent interface
2) Map old API → new API for each failing test
3) Provide full updated test file
4) Provide runbook
```

---

### Task 2.3: Fix TruthManagerAgent Test Expectations

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: TruthManagerAgent tests expect fixed agent_id and .handlers attribute
- Allowed paths:
  - tests/agents/test_truth_manager.py
  - agents/truth_manager.py (READ ONLY)
- Forbidden: modifying agents/truth_manager.py

Brief:
- Agent ID is now auto-generated (truthmanageragent_<hash>) unless specified
- Tests checking agent_id == "truth_manager" should either:
  a) Pass agent_id="truth_manager" to constructor, OR
  b) Check agent_id.startswith("truthmanageragent_")
- Replace .handlers access with get_contract() or internal _handlers
- Fix get_truth_statistics assertions to match actual response structure

Acceptance checks (must pass locally):
- Tests: pytest tests/agents/test_truth_manager.py -v
- Expected: 9 failures fixed

Deliverables:
- Full file replacement for test_truth_manager.py

Hard rules:
- Windows friendly paths, CRLF preserved
- Don't modify production code
- Zero network calls in tests
- Deterministic runs

Self-review (answer yes/no at the end):
- Tests handle dynamic agent IDs, use correct handler access pattern

Now:
1) Show current TruthManagerAgent init and contract
2) List each failing assertion and its fix
3) Provide full updated test file
4) Provide runbook
```

---

## Phase 3: Validator Architecture Remediation

### Task 3.1: Implement SEO Validator

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: SEOValidator.validate() returns empty list - needs implementation
- Allowed paths:
  - agents/validators/seo_validator.py
  - config/seo.yaml
  - tests/agents/test_seo_validation.py (to understand expected behavior)
- Forbidden: other validators, core files

Brief:
- Read test_seo_validation.py to understand all expected validations:
  - H1 presence (required)
  - H1 count (only one allowed)
  - H1 length (min 20, max 60 chars typical)
  - Heading hierarchy (no skipping levels: H1→H3 is invalid)
  - Empty headings detection
  - H1 position (should be first heading)
- Implement validate() method to return Issue objects for each violation
- Load thresholds from config/seo.yaml

Acceptance checks (must pass locally):
- Tests: pytest tests/agents/test_seo_validation.py -v
- Expected: 13 failures fixed
- Validator must work standalone without database

Deliverables:
- Full file replacement for seo_validator.py
- Updated config/seo.yaml with all configurable thresholds
- New unit tests for edge cases not covered

Hard rules:
- Windows friendly paths, CRLF preserved
- No external dependencies (no BeautifulSoup, use regex)
- Zero network calls
- Deterministic: same input = same output

Self-review (answer yes/no at the end):
- All 13 SEO test cases pass, config-driven thresholds, no hardcoded values

Now:
1) Show expected behavior from test file
2) Show config/seo.yaml structure
3) Provide full seo_validator.py implementation
4) Provide runbook
```

---

### Task 3.2: Fix Modular Validators Test Architecture

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: test_modular_validators.py uses old validator architecture
- Allowed paths:
  - tests/agents/test_modular_validators.py
  - agents/validators/*.py (READ ONLY)
  - core/validator_router.py (READ ONLY)
- Forbidden: modifying production validator code

Brief:
- Read current validator architecture:
  - BaseValidator interface
  - ValidatorRouter dispatch mechanism
  - Individual validator implementations
- Update tests to use new patterns:
  - Async validate() calls
  - Router-based dispatch
  - Config loader integration
- Fix all 20 failing tests

Acceptance checks (must pass locally):
- Tests: pytest tests/agents/test_modular_validators.py -v
- Expected: 20 failures fixed

Deliverables:
- Full file replacement for test_modular_validators.py
- Add validator test fixtures to conftest.py if needed

Hard rules:
- Windows friendly paths, CRLF preserved
- Tests must be async where validators are async
- Zero network calls
- Deterministic runs

Self-review (answer yes/no at the end):
- Tests match current validator architecture, all use async patterns

Now:
1) Show current BaseValidator interface
2) Show ValidatorRouter API
3) Map old test patterns → new patterns
4) Provide full updated test file
5) Provide runbook
```

---

## Phase 4: Infrastructure API Updates

### Task 4.1: Fix CacheManager API

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: CacheManager.clear() method doesn't exist
- Allowed paths:
  - core/cache.py
  - api/server.py (cache control endpoint only)
  - tests/api/test_new_endpoints.py (cache tests only)
  - tests/cli/test_new_commands.py (cache tests only)
- Forbidden: other endpoints, other CLI commands

Brief:
- Check CacheManager for existing clear methods (clear_l1, clear_l2, clear_all)
- If clear_all() exists: update callers to use correct name
- If missing: add clear() as alias or implement it
- Update /admin/cache/clear endpoint to use correct method
- Update CLI cache clear commands

Acceptance checks (must pass locally):
- Tests: pytest tests/api/test_new_endpoints.py::TestConfigurationControl -k cache -v
- Tests: pytest tests/cli/test_new_commands.py::TestAdminCommands -k cache -v
- Expected: 8 failures fixed (4 API + 4 CLI)

Deliverables:
- Updated core/cache.py (if method missing)
- Updated api/server.py (cache endpoint)
- Updated test files with correct assertions

Hard rules:
- Windows friendly paths, CRLF preserved
- Backward compatible if adding method
- Zero network calls in tests
- Deterministic runs

Self-review (answer yes/no at the end):
- Cache clear works via API and CLI, tests pass, method names consistent

Now:
1) Show current CacheManager interface
2) Show what callers expect
3) Provide minimal fix (prefer updating callers over adding aliases)
4) Provide full updated files
5) Provide runbook
```

---

### Task 4.2: Fix Logger Level API

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: structlog BoundLogger doesn't have setLevel() - wrong API used
- Allowed paths:
  - api/server.py (log level endpoint only)
  - core/logging.py (if exists)
  - tests/api/test_new_endpoints.py (log level tests only)
- Forbidden: other endpoints

Brief:
- structlog bound loggers don't have setLevel() (that's stdlib logging)
- Fix /admin/log-level endpoint to use correct approach:
  - Option A: Configure stdlib root logger level
  - Option B: Reconfigure structlog wrapper class
- Update tests to verify log level actually changes

Acceptance checks (must pass locally):
- Tests: pytest tests/api/test_new_endpoints.py::TestConfigurationControl -k log -v
- Expected: 4 failures fixed

Deliverables:
- Updated api/server.py (log level endpoint)
- Updated core/logging.py if needed
- Updated tests with correct assertions

Hard rules:
- Windows friendly paths, CRLF preserved
- Log level must actually change (not just return success)
- Zero network calls in tests
- Deterministic runs

Self-review (answer yes/no at the end):
- Log level endpoint works, actually changes logging behavior, tests verify it

Now:
1) Show current log level endpoint implementation
2) Show structlog configuration
3) Provide fix using stdlib logging integration
4) Provide full updated files
5) Provide runbook
```

---

## Phase 5: Windows Compatibility

### Task 5.1: Fix Unicode Encoding Issues

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: cp1252 codec can't encode Unicode chars (✓, ✗) on Windows
- Allowed paths:
  - tests/conftest.py (add encoding setup)
  - pytest.ini (add env vars)
  - tests/api/test_websocket_connection.py
  - tests/api/test_export_endpoints_comprehensive.py
- Forbidden: production code

Brief:
- Add UTF-8 encoding setup to conftest.py for Windows
- Set PYTHONIOENCODING=utf-8 in pytest.ini
- Replace Unicode symbols in test output with ASCII equivalents:
  - ✓ → [PASS] or [OK]
  - ✗ → [FAIL] or [ERR]
  - → → ->
- Ensure WebSocket tests handle encoding properly

Acceptance checks (must pass locally):
- Tests: pytest tests/api/test_websocket_connection.py -v (on Windows)
- Tests: pytest tests/api/test_export_endpoints_comprehensive.py -v
- Expected: ~43 encoding errors fixed
- Must work on both Windows and Linux

Deliverables:
- Updated conftest.py with Windows encoding setup
- Updated pytest.ini with env configuration
- Updated test files with ASCII-safe output

Hard rules:
- Windows friendly paths, CRLF preserved
- Cross-platform: must work on Linux too
- Zero network calls in tests
- Deterministic runs

Self-review (answer yes/no at the end):
- Tests pass on Windows, no UnicodeEncodeError, works on Linux too

Now:
1) Show encoding setup code for conftest.py
2) Show pytest.ini changes
3) List files with Unicode chars to replace
4) Provide full updated files
5) Provide runbook
```

---

## Phase 6: Logic Fixes

### Task 6.1: Fix Language Detection Logic

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Language detection returns wrong values for certain path patterns
- Allowed paths:
  - core/language_utils.py
  - tests/test_language_detection.py
- Forbidden: other core files

Brief:
- Read failing tests to understand expected behavior:
  - /docs/en/guide.md → "en"
  - C:\docs\en\guide.md → "en" (Windows path)
  - /blog/en/post.md → "en" (subdomain pattern)
- Fix path parsing to:
  - Normalize Windows backslashes to forward slashes
  - Handle both /en/ and /en-us/ patterns
  - Case-insensitive matching
- Fix 4 failing tests

Acceptance checks (must pass locally):
- Tests: pytest tests/test_language_detection.py -v
- Expected: 4 failures fixed

Deliverables:
- Full file replacement for core/language_utils.py
- Add edge case tests for Windows paths

Hard rules:
- Windows friendly paths, CRLF preserved
- Must handle: /en/, /en-us/, /en_US/, subdomain patterns
- Zero network calls
- Deterministic runs

Self-review (answer yes/no at the end):
- Language detection works for all test cases, handles Windows paths

Now:
1) Show failing test expectations
2) Show current implementation
3) Provide fixed language_utils.py
4) Add new edge case tests
5) Provide runbook
```

---

## Phase 7: Cleanup and Maintenance

### Task 7.1: Handle Placeholder and Missing Module Tests

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Placeholder tests with `assert 1 == 0` and missing module imports
- Allowed paths:
  - tests/cli/test_new_commands.py
  - tests/startup/test_rule_manager_imports.py
- Forbidden: production code

Brief:
- For placeholder tests (assert 1 == 0):
  - If feature exists: implement the test properly
  - If feature planned but not ready: mark @pytest.mark.skip(reason="...")
  - If feature abandoned: delete the test
- For rule_manager import tests:
  - Check if module exists under different name
  - If renamed: update import path
  - If removed: delete tests or skip with reason
- Document decisions in test file comments

Acceptance checks (must pass locally):
- Tests: pytest tests/cli/test_new_commands.py -v
- Tests: pytest tests/startup/test_rule_manager_imports.py -v
- Expected: 8 failures resolved (either fixed, skipped, or deleted)

Deliverables:
- Updated test_new_commands.py
- Updated or deleted test_rule_manager_imports.py
- Comment documenting why tests were skipped/deleted

Hard rules:
- Windows friendly paths, CRLF preserved
- Prefer skip with reason over delete (preserves intent)
- Zero network calls
- Deterministic runs

Self-review (answer yes/no at the end):
- No placeholder assertions remain, missing modules handled, decisions documented

Now:
1) Show each placeholder test and determine correct action
2) Check if rule_manager exists elsewhere
3) Provide updated files
4) Provide runbook
```

---

## Phase 8: Test Infrastructure Improvements

### Task 8.1: Add API Contract Tests

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Prevent future API drift by adding contract tests
- Allowed paths:
  - tests/contracts/ (new directory)
  - tests/contracts/test_database_contract.py (new)
  - tests/contracts/test_agent_contract.py (new)
  - tests/contracts/test_cache_contract.py (new)
- Forbidden: production code

Brief:
- Create contract tests that verify public APIs exist:
  - DatabaseManager: create_*, get_*, update_*, delete_* methods
  - BaseAgent: __init__, get_contract, handle methods
  - CacheManager: get, set, invalidate, clear_* methods
- Tests should fail if methods are renamed/removed
- Include method signature checks (parameter names, types if annotated)

Acceptance checks (must pass locally):
- Tests: pytest tests/contracts/ -v
- Expected: All new tests pass against current implementation
- Tests should be fast (<1s total)

Deliverables:
- New tests/contracts/__init__.py
- New tests/contracts/test_database_contract.py
- New tests/contracts/test_agent_contract.py
- New tests/contracts/test_cache_contract.py

Hard rules:
- Windows friendly paths, CRLF preserved
- No instantiation of classes - just interface checks
- Zero network calls
- Deterministic runs
- No new dependencies

Self-review (answer yes/no at the end):
- Contract tests cover all public APIs, fail on interface changes, fast execution

Now:
1) List all public methods to test per class
2) Show contract test pattern
3) Provide all new test files
4) Provide runbook
```

---

### Task 8.2: Add Test Documentation and CI Integration

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Document test patterns and add coverage requirements
- Allowed paths:
  - tests/README.md (new)
  - pytest.ini
  - .github/workflows/test.yml (if exists)
- Forbidden: production code, test logic

Brief:
- Create tests/README.md documenting:
  - Fixture usage patterns
  - Mocking guidelines
  - Naming conventions
  - How to run tests locally
- Update pytest.ini:
  - Add coverage threshold (--cov-fail-under=80)
  - Add common pytest options
- Update CI workflow (if exists) to enforce coverage

Acceptance checks (must pass locally):
- Tests: pytest tests/ --ignore=tests/manual/ --cov=. --cov-fail-under=70 -q
- Expected: Tests pass with coverage report
- README.md is clear and complete

Deliverables:
- New tests/README.md
- Updated pytest.ini
- Updated .github/workflows/test.yml (if exists)

Hard rules:
- Windows friendly paths, CRLF preserved
- Coverage threshold should be achievable (start at 70%, increase later)
- Documentation matches actual patterns in codebase
- No new dependencies

Self-review (answer yes/no at the end):
- Documentation complete, coverage enforced, CI updated

Now:
1) Show current pytest.ini
2) Show common fixture patterns from conftest.py
3) Provide tests/README.md
4) Provide updated pytest.ini
5) Provide runbook
```

---

## Execution Order

Execute task cards in this order for minimal conflicts:

```
Week 1: Foundation
├── Task 1.1: DatabaseManager in Agent Tests
├── Task 1.2: DatabaseManager in API Tests
├── Task 2.1: BaseAgent Tests
├── Task 2.2: EnhancementAgent Tests
└── Task 2.3: TruthManagerAgent Tests

Week 2: Features
├── Task 3.1: Implement SEO Validator
├── Task 3.2: Fix Modular Validators Tests
├── Task 4.1: Fix CacheManager API
└── Task 4.2: Fix Logger Level API

Week 3: Polish
├── Task 5.1: Fix Unicode Encoding
├── Task 6.1: Fix Language Detection
├── Task 7.1: Handle Placeholder Tests
├── Task 8.1: Add Contract Tests
└── Task 8.2: Add Documentation
```

---

## Verification After All Tasks

```bash
# Full test suite (should pass)
pytest tests/ --ignore=tests/manual/ --ignore=tests/test_endpoints_live.py --ignore=tests/test_truth_llm_validation_real.py -v --import-mode=importlib -p no:capture

# With coverage
pytest tests/ --ignore=tests/manual/ --cov=. --cov-report=term-missing --cov-fail-under=70

# Contract tests only (fast check)
pytest tests/contracts/ -v

# Performance check
pytest tests/ --ignore=tests/manual/ --durations=20 -q
```

**Success Criteria**:
- [ ] 0 failures
- [ ] 0 errors
- [ ] <10 skipped (with documented reasons)
- [ ] Coverage ≥70%
- [ ] Execution <5 minutes
