# Parallel Agent Execution Prompt

**Purpose**: Execute failing test remediation tasks in parallel using multiple agents
**Reference**: [failing_tests_taskcards.md](failing_tests_taskcards.md)

---

## Execution Strategy

Tasks are organized into **5 parallel waves**. Within each wave, all tasks can execute simultaneously without conflicts.

```
Wave 1: Database API    ─┬─ Agent A: Task 1.1 (Agent Tests)
                         └─ Agent B: Task 1.2 (API Tests)

Wave 2: Agent Contracts ─┬─ Agent A: Task 2.1 (BaseAgent)
                         ├─ Agent B: Task 2.2 (EnhancementAgent)
                         └─ Agent C: Task 2.3 (TruthManagerAgent)

Wave 3: Validators      ─┬─ Agent A: Task 3.1 (SEO Validator)
                         └─ Agent B: Task 3.2 (Validator Tests)

Wave 4: Infrastructure  ─┬─ Agent A: Task 4.1 (CacheManager)
                         ├─ Agent B: Task 4.2 (Logger API)
                         ├─ Agent C: Task 5.1 (Unicode)
                         └─ Agent D: Task 6.1 (Language Detection)

Wave 5: Cleanup         ─┬─ Agent A: Task 7.1 (Placeholders)
                         ├─ Agent B: Task 8.1 (Contract Tests)
                         └─ Agent C: Task 8.2 (Documentation)
```

---

## Wave 1: Database API Alignment (2 Parallel Agents)

### Agent A Prompt - Task 1.1

```
You are a senior engineer fixing test failures in the TBCV project.

TASK: Update DatabaseManager method calls in agent test files

CONTEXT:
- DatabaseManager API was refactored: save_* methods renamed to create_*
- Tests still use old method names causing ~22 errors
- db.close() was removed - context managers handle cleanup

ALLOWED FILES (modify):
- tests/agents/test_enhancement_agent_comprehensive.py
- tests/conftest.py (only db fixtures)

FORBIDDEN:
- Do NOT modify core/database.py
- Do NOT modify other test files

CHANGES REQUIRED:
1. Replace: db.save_validation_result(...) → db.create_validation_result(...)
2. Replace: db.save_recommendation(...) → db.create_recommendation(...)
3. Remove: all db.close() calls
4. Update mock specs if they reference old method names

ACCEPTANCE:
- Run: pytest tests/agents/test_enhancement_agent_comprehensive.py -v --import-mode=importlib -p no:capture
- Expected: 22 previously erroring tests now pass or show different failure

DELIVERABLES:
- Full replacement for test_enhancement_agent_comprehensive.py
- Any fixture updates in conftest.py

RULES:
- Windows paths (CRLF preserved)
- No new dependencies
- Keep test function signatures unchanged

Execute now:
1. Grep for all occurrences of old method names
2. Show the changes needed
3. Provide full updated file(s)
4. Run tests and show results
```

### Agent B Prompt - Task 1.2

```
You are a senior engineer fixing test failures in the TBCV project.

TASK: Update DatabaseManager method calls in API test files

CONTEXT:
- DatabaseManager API was refactored: save_* methods renamed to create_*
- Tests still use old method names causing ~50 errors
- db.close() was removed - context managers handle cleanup

ALLOWED FILES (modify):
- tests/api/test_export_endpoints_comprehensive.py
- tests/api/services/test_status_recalculator.py
- tests/api/services/test_recommendation_consolidator.py
- tests/test_checkpoints.py

FORBIDDEN:
- Do NOT modify core/database.py
- Do NOT modify agent test files

CHANGES REQUIRED:
1. Replace: db.save_validation_result(...) → db.create_validation_result(...)
2. Replace: db.save_recommendation(...) → db.create_recommendation(...)
3. Remove: all db.close() calls

ACCEPTANCE:
- Run: pytest tests/api/test_export_endpoints_comprehensive.py tests/api/services/ tests/test_checkpoints.py -v --import-mode=importlib -p no:capture
- Expected: ~50 previously erroring tests now pass or show different failure

DELIVERABLES:
- Full replacement for each modified test file

RULES:
- Windows paths (CRLF preserved)
- No new dependencies
- Keep test function signatures unchanged

Execute now:
1. Grep for all occurrences in each file
2. Show changes per file
3. Provide full updated files
4. Run tests and show results
```

---

## Wave 2: Agent Contract Alignment (3 Parallel Agents)

### Agent A Prompt - Task 2.1

```
You are a senior engineer fixing test failures in the TBCV project.

TASK: Fix BaseAgent test expectations

CONTEXT:
- BaseAgent no longer has .start()/.stop() methods
- Agent lifecycle managed via AgentBus.register()/unregister()
- .handlers is now internal (_handlers), use get_contract().methods

ALLOWED FILES:
- tests/agents/test_base.py (modify)
- agents/base_agent.py (READ ONLY - understand current API)

FORBIDDEN:
- Do NOT modify agents/base_agent.py

INVESTIGATION FIRST:
1. Read agents/base_agent.py to understand actual interface
2. Document what methods/properties actually exist

CHANGES REQUIRED:
- Update tests expecting .start()/.stop() to use AgentBus pattern
- Update tests accessing .handlers to use get_contract()
- Fix ConcreteAgent test helper class if needed

ACCEPTANCE:
- Run: pytest tests/agents/test_base.py -v --import-mode=importlib -p no:capture
- Expected: 4 failures fixed

DELIVERABLES:
- Full replacement for test_base.py

Execute now:
1. Read and show BaseAgent interface
2. Map old expectations → new API
3. Provide full updated test file
4. Run tests and show results
```

### Agent B Prompt - Task 2.2

```
You are a senior engineer fixing test failures in the TBCV project.

TASK: Fix EnhancementAgent test expectations

CONTEXT:
- EnhancementAgent API changed:
  - .capabilities → get_contract().methods
  - EnhancementResult.applied_count → len(result.results) or similar
  - Method names may have changed

ALLOWED FILES:
- tests/agents/test_enhancement_agent.py (modify)
- agents/enhancement_agent.py (READ ONLY)

FORBIDDEN:
- Do NOT modify agents/enhancement_agent.py

INVESTIGATION FIRST:
1. Read agents/enhancement_agent.py for actual API
2. Read EnhancementResult class definition

CHANGES REQUIRED:
- Replace .capabilities checks with get_contract() pattern
- Fix EnhancementResult attribute access
- Update method name expectations

ACCEPTANCE:
- Run: pytest tests/agents/test_enhancement_agent.py -v --import-mode=importlib -p no:capture
- Expected: 12 failures fixed

DELIVERABLES:
- Full replacement for test_enhancement_agent.py

Execute now:
1. Read and show EnhancementAgent interface
2. Map each failing test to its fix
3. Provide full updated test file
4. Run tests and show results
```

### Agent C Prompt - Task 2.3

```
You are a senior engineer fixing test failures in the TBCV project.

TASK: Fix TruthManagerAgent test expectations

CONTEXT:
- Agent ID now auto-generated: truthmanageragent_<hash>
- Tests expect fixed "truth_manager" ID
- .handlers attribute is internal, use get_contract()

ALLOWED FILES:
- tests/agents/test_truth_manager.py (modify)
- agents/truth_manager.py (READ ONLY)

FORBIDDEN:
- Do NOT modify agents/truth_manager.py

CHANGES REQUIRED:
- Fix agent_id assertions: either pass explicit ID or check prefix
- Replace .handlers access with get_contract()
- Fix get_truth_statistics response structure assertions

ACCEPTANCE:
- Run: pytest tests/agents/test_truth_manager.py -v --import-mode=importlib -p no:capture
- Expected: 9 failures fixed

DELIVERABLES:
- Full replacement for test_truth_manager.py

Execute now:
1. Read TruthManagerAgent.__init__ and get_contract
2. List each failing assertion and fix
3. Provide full updated test file
4. Run tests and show results
```

---

## Wave 3: Validator Architecture (2 Parallel Agents)

### Agent A Prompt - Task 3.1

```
You are a senior engineer fixing test failures in the TBCV project.

TASK: Implement SEO Validator

CONTEXT:
- SEOValidator.validate() currently returns empty list
- 13 tests expect heading validation (H1 presence, count, length, hierarchy)

ALLOWED FILES (modify):
- agents/validators/seo_validator.py
- config/seo.yaml

READ ONLY:
- tests/agents/test_seo_validation.py (understand expected behavior)

REQUIREMENTS FROM TESTS:
1. H1 presence - error if missing
2. H1 count - warning if multiple
3. H1 length - warning if <20 or >60 chars
4. Heading hierarchy - error if levels skipped (H1→H3)
5. Empty headings - warning
6. H1 position - should be first heading

IMPLEMENTATION:
- Use regex to extract headings (no BeautifulSoup)
- Load thresholds from config/seo.yaml
- Return list of Issue objects

ACCEPTANCE:
- Run: pytest tests/agents/test_seo_validation.py -v --import-mode=importlib -p no:capture
- Expected: 13 failures fixed

DELIVERABLES:
- Full seo_validator.py implementation
- Updated config/seo.yaml with thresholds

Execute now:
1. Read test file for exact expectations
2. Show config structure
3. Provide full seo_validator.py
4. Run tests and show results
```

### Agent B Prompt - Task 3.2

```
You are a senior engineer fixing test failures in the TBCV project.

TASK: Fix modular validators test architecture

CONTEXT:
- Validator system was refactored to use router-based dispatch
- Tests use old direct-call patterns
- Need async patterns for async validators

ALLOWED FILES (modify):
- tests/agents/test_modular_validators.py

READ ONLY:
- agents/validators/base_validator.py
- agents/validators/*.py (all validators)
- core/validator_router.py

INVESTIGATION FIRST:
1. Read BaseValidator interface
2. Read ValidatorRouter API
3. Understand how validators are invoked now

CHANGES REQUIRED:
- Update to async test patterns where needed
- Use ValidatorRouter for dispatch tests
- Fix validator instantiation patterns

ACCEPTANCE:
- Run: pytest tests/agents/test_modular_validators.py -v --import-mode=importlib -p no:capture
- Expected: 20 failures fixed

DELIVERABLES:
- Full replacement for test_modular_validators.py

Execute now:
1. Read current validator architecture
2. Map old patterns → new patterns
3. Provide full updated test file
4. Run tests and show results
```

---

## Wave 4: Infrastructure (4 Parallel Agents)

### Agent A Prompt - Task 4.1

```
You are a senior engineer fixing test failures in the TBCV project.

TASK: Fix CacheManager.clear() API

CONTEXT:
- Tests call CacheManager.clear() which doesn't exist
- May have clear_l1(), clear_l2(), clear_all() instead

ALLOWED FILES:
- core/cache.py (modify if needed)
- api/server.py (cache endpoint only)
- tests/api/test_new_endpoints.py (cache tests)
- tests/cli/test_new_commands.py (cache tests)

APPROACH:
1. Read core/cache.py for actual clear methods
2. Prefer updating callers over adding aliases
3. If method truly missing, add it

ACCEPTANCE:
- Run: pytest tests/api/test_new_endpoints.py -k cache -v --import-mode=importlib -p no:capture
- Run: pytest tests/cli/test_new_commands.py -k cache -v --import-mode=importlib -p no:capture
- Expected: 8 failures fixed

Execute now:
1. Show CacheManager interface
2. Identify correct method names
3. Update callers or add method
4. Run tests and show results
```

### Agent B Prompt - Task 4.2

```
You are a senior engineer fixing test failures in the TBCV project.

TASK: Fix logger level API

CONTEXT:
- structlog BoundLogger doesn't have setLevel()
- /admin/log-level endpoint uses wrong API

ALLOWED FILES:
- api/server.py (log level endpoint only)
- core/logging.py (if exists)
- tests/api/test_new_endpoints.py (log tests)

FIX APPROACH:
- Use stdlib logging.getLogger().setLevel()
- Or reconfigure structlog wrapper class

ACCEPTANCE:
- Run: pytest tests/api/test_new_endpoints.py -k log -v --import-mode=importlib -p no:capture
- Expected: 4 failures fixed

Execute now:
1. Show current log level endpoint
2. Show correct approach
3. Provide fixed implementation
4. Run tests and show results
```

### Agent C Prompt - Task 5.1

```
You are a senior engineer fixing test failures in the TBCV project.

TASK: Fix Windows Unicode encoding issues

CONTEXT:
- cp1252 codec can't encode ✓, ✗, → on Windows
- ~43 tests fail with UnicodeEncodeError

ALLOWED FILES:
- tests/conftest.py (add encoding setup)
- pytest.ini (add PYTHONIOENCODING)
- tests/api/test_websocket_connection.py
- tests/api/test_export_endpoints_comprehensive.py

CHANGES:
1. Add UTF-8 setup to conftest.py for Windows
2. Set PYTHONIOENCODING=utf-8 in pytest environment
3. Replace Unicode symbols with ASCII: ✓→[OK], ✗→[FAIL]

ACCEPTANCE:
- Run: pytest tests/api/test_websocket_connection.py -v --import-mode=importlib -p no:capture
- Expected: No UnicodeEncodeError

Execute now:
1. Show conftest.py encoding setup
2. Show pytest.ini changes
3. Find and replace Unicode in test files
4. Run tests and show results
```

### Agent D Prompt - Task 6.1

```
You are a senior engineer fixing test failures in the TBCV project.

TASK: Fix language detection logic

CONTEXT:
- detect_language() returns wrong values for some paths
- Windows paths not handled correctly

ALLOWED FILES:
- core/language_utils.py (modify)
- tests/test_language_detection.py (read and possibly add tests)

EXPECTED BEHAVIOR:
- /docs/en/guide.md → "en"
- C:\docs\en\guide.md → "en"
- /blog/en/post.md → "en"

FIX:
- Normalize backslashes to forward slashes
- Case-insensitive matching
- Handle /en/, /en-us/, /en_US/ patterns

ACCEPTANCE:
- Run: pytest tests/test_language_detection.py -v --import-mode=importlib -p no:capture
- Expected: 4 failures fixed

Execute now:
1. Show failing test cases
2. Show current implementation
3. Provide fixed language_utils.py
4. Run tests and show results
```

---

## Wave 5: Cleanup (3 Parallel Agents)

### Agent A Prompt - Task 7.1

```
You are a senior engineer fixing test failures in the TBCV project.

TASK: Handle placeholder and missing module tests

CONTEXT:
- Some tests have `assert 1 == 0` (placeholders)
- Some tests import non-existent `rule_manager` module

ALLOWED FILES:
- tests/cli/test_new_commands.py
- tests/startup/test_rule_manager_imports.py

APPROACH:
- Placeholder tests: mark @pytest.mark.skip(reason="TODO: ...")
- Missing module: check if renamed, update or skip

ACCEPTANCE:
- Run: pytest tests/cli/test_new_commands.py tests/startup/test_rule_manager_imports.py -v --import-mode=importlib -p no:capture
- Expected: 8 failures resolved (fixed or skipped with reason)

Execute now:
1. List each placeholder/missing module test
2. Determine correct action per test
3. Provide updated files
4. Run tests and show results
```

### Agent B Prompt - Task 8.1

```
You are a senior engineer improving test infrastructure in the TBCV project.

TASK: Add API contract tests

CONTEXT:
- API drift caused 147+ test failures
- Need contract tests to catch future changes

CREATE:
- tests/contracts/__init__.py
- tests/contracts/test_database_contract.py
- tests/contracts/test_agent_contract.py
- tests/contracts/test_cache_contract.py

PATTERN:
```python
def test_database_manager_interface():
    from core.database import DatabaseManager
    required = ["create_validation_result", "get_validation", ...]
    for method in required:
        assert hasattr(DatabaseManager, method), f"Missing: {method}"
```

ACCEPTANCE:
- Run: pytest tests/contracts/ -v
- Expected: All pass, fast execution (<1s)

Execute now:
1. List public methods per class
2. Create contract test files
3. Run tests and show results
```

### Agent C Prompt - Task 8.2

```
You are a senior engineer improving test infrastructure in the TBCV project.

TASK: Add test documentation and coverage requirements

CREATE/MODIFY:
- tests/README.md (new - document patterns)
- pytest.ini (add coverage requirements)

TESTS README CONTENT:
- How to run tests
- Fixture usage (db_session, agent_bus, test_client)
- Mocking guidelines
- Naming conventions

PYTEST.INI ADDITIONS:
- --cov-fail-under=70 (achievable threshold)
- Document existing options

ACCEPTANCE:
- Run: pytest tests/ --ignore=tests/manual/ --cov=. --cov-fail-under=70 -q
- README is comprehensive

Execute now:
1. Show current pytest.ini
2. Show common fixture patterns
3. Create tests/README.md
4. Update pytest.ini
5. Run coverage check
```

---

## Master Orchestration Prompt

Use this prompt to orchestrate all waves:

```
You are orchestrating parallel test remediation for the TBCV project.

TASK: Execute failing_tests_taskcards.md in parallel waves

WAVE EXECUTION:
For each wave, spawn agents in parallel using the Task tool with the prompts above.
Wait for all agents in a wave to complete before starting the next wave.

WAVE 1 (2 agents): Tasks 1.1, 1.2 - Database API
WAVE 2 (3 agents): Tasks 2.1, 2.2, 2.3 - Agent Contracts
WAVE 3 (2 agents): Tasks 3.1, 3.2 - Validators
WAVE 4 (4 agents): Tasks 4.1, 4.2, 5.1, 6.1 - Infrastructure
WAVE 5 (3 agents): Tasks 7.1, 8.1, 8.2 - Cleanup

AFTER EACH WAVE:
1. Collect results from all agents
2. Run integration check: pytest tests/ --ignore=tests/manual/ -q --import-mode=importlib -p no:capture
3. Report failures fixed vs remaining
4. Proceed to next wave

FINAL VERIFICATION:
pytest tests/ --ignore=tests/manual/ --ignore=tests/test_endpoints_live.py --ignore=tests/test_truth_llm_validation_real.py -v --import-mode=importlib -p no:capture

SUCCESS CRITERIA:
- 0 failures
- 0 errors
- <10 skipped (documented)
- Coverage ≥70%

Execute Wave 1 now by spawning 2 parallel agents.
```

---

## Quick Reference: Parallel Execution Commands

```bash
# Wave 1 verification
pytest tests/agents/test_enhancement_agent_comprehensive.py tests/api/test_export_endpoints_comprehensive.py tests/api/services/ tests/test_checkpoints.py -v --import-mode=importlib -p no:capture -q

# Wave 2 verification
pytest tests/agents/test_base.py tests/agents/test_enhancement_agent.py tests/agents/test_truth_manager.py -v --import-mode=importlib -p no:capture -q

# Wave 3 verification
pytest tests/agents/test_seo_validation.py tests/agents/test_modular_validators.py -v --import-mode=importlib -p no:capture -q

# Wave 4 verification
pytest tests/api/test_new_endpoints.py tests/cli/test_new_commands.py tests/api/test_websocket_connection.py tests/test_language_detection.py -v --import-mode=importlib -p no:capture -q

# Wave 5 verification
pytest tests/cli/test_new_commands.py tests/startup/ tests/contracts/ -v --import-mode=importlib -p no:capture -q

# Full suite verification
pytest tests/ --ignore=tests/manual/ --ignore=tests/test_endpoints_live.py --ignore=tests/test_truth_llm_validation_real.py --import-mode=importlib -p no:capture -q
```
