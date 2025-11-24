**Goal:** Bring the **`tbcv` package** to high, structured coverage, with tests organized by module and split into **unit (with and without mocks)** and **integration/full-stack**.

### 1. Coverage priorities

**A. Must be ~100% covered (no margin, business-critical):**

These are the “truth-based” core and orchestrators. Require **100% line coverage** (or as close as practically possible; any unavoidable gap must be commented & justified in tests).

* **Agents (all business logic):**

  * `agents/base.py`
  * `agents/truth_manager.py`
  * `agents/fuzzy_detector.py`
  * `agents/content_validator.py`
  * `agents/content_enhancer.py`
  * `agents/llm_validator.py`
  * `agents/code_analyzer.py`
  * `agents/recommendation_agent.py`
  * `agents/enhancement_agent.py`
  * `agents/orchestrator.py`

* **Core truth / validation backbone:**

  * `core/config.py`
  * `core/validation_store.py`
  * `core/rule_manager.py`
  * `core/family_detector.py`
  * `core/ingestion.py`
  * `core/path_validator.py`
  * `core/startup_checks.py`
  * `core/prompt_loader.py`
  * `core/utilities.py`

* **Serving & orchestration entrypoints:**

  * `api/services/*.py` (all service modules)
  * `api/server.py` (FastAPI app & core endpoints, especially health + validation/recommendation/workflow)
  * `api/websocket_endpoints.py`
  * `api/additional_endpoints.py`
  * `api/export_endpoints.py`
  * `cli/main.py` (CLI commands & dispatch)
  * `svc/mcp_server.py` (MCP server logic; JSON-RPC handlers)

* **System health glue:**

  * `startup_check.py`
  * `validate_system.py`
  * `health.py`

For these, tests must cover:

* Happy paths
* Edge cases
* Failure / exception handling
* Behaviour both **with mocks (for external deps)** and **without mocks** (using in-memory or local resources).

---

**B. High coverage with small margin (target ≥90–95%):**

Important infrastructure, but lower business risk; allow a small margin if 100% is too brittle.

* `core/database.py` (test via in-memory / temp SQLite + fixtures)
* `core/cache.py`
* `core/logging.py`
* `core/ollama.py` and `core/ollama_validator.py`

  * *All* tests here must fully mock network / LLM calls; zero live calls.
* `core/io_win.py`
* `core/ollama_validator.py`
* `api/dashboard.py`
* `api/server_extensions.py`
* Top-level scripts that wrap main flows:

  * `run_all_tests.py`
  * `run_full_stack_test.py`
  * `run_smoke.py`
  * `inventory.py`
  * `diagnose.py`
  * `generate_docs.py`
  * `apply_patches.py`

---

**C. Best-effort coverage (no strict target; don’t fight the framework):**

Keep tests, but don’t block on 100%:

* `templates/` (Jinja/HTML rendering) – just smoke tests for core templates (`dashboard.html`, key detail/list views).
* `tools/*.py` (developer utilities: `validate_folder.py`, `endpoint_check.py`, `cleanup_db.py`, etc.) – aim for reasonable coverage but allow gaps.
* Any purely data-only or compatibility modules (e.g. `rules/`, `truth/*.json` – covered indirectly via the managers).

---

### 2. Test organization (target structure)

Reorganize tests so they mirror the module layout:

* Keep existing high-level tests (already in `tests/`) but add **per-module** tests:

```text
tests/
  __init__.py
  conftest.py
  # Existing integration/full-stack tests stay (possibly renamed/refined)
  test_cli_web_parity.py
  test_endpoints_offline.py
  test_enhancer_consumes_validation.py
  test_full_stack_local.py
  test_fuzzy_logic.py
  test_recommendations.py
  test_truth_validation.py
  test_validation_persistence.py
  test_websocket.py
  ...

  agents/
    test_truth_manager.py
    test_fuzzy_detector.py
    test_content_validator.py
    test_content_enhancer.py
    test_llm_validator.py
    test_code_analyzer.py
    test_recommendation_agent.py
    test_enhancement_agent.py
    test_orchestrator.py

  core/
    test_config.py
    test_validation_store.py
    test_rule_manager.py
    test_family_detector.py
    test_ingestion.py
    test_path_validator.py
    test_startup_checks.py
    test_prompt_loader.py
    test_utilities.py
    test_database.py
    test_cache.py
    test_logging.py
    test_ollama_validator.py  # fully mocked

  api/
    test_server_health.py
    test_server_validation_endpoints.py
    test_server_recommendation_endpoints.py
    test_websocket_endpoints.py
    test_additional_endpoints.py
    test_export_endpoints.py

  cli/
    test_cli_main.py

  svc/
    test_mcp_server.py

  tools/
    test_validate_folder.py
    test_endpoint_check.py
    ...
```

Each of these should include:

* **Unit tests without mocks** where feasible (pure logic, config, rules resolving, etc.)
* **Unit tests with mocks** where external systems are involved (DB failures, LLM calls, HTTP, filesystem side-effects, time).

---

## TASKCARD — Test Suite Upgrade & Coverage Enforcement for TBCV

You are operating on the attached **TBCV repo** (multi-agent “Truth-Based Content Validation” system).
Treat this task as **self-driving**: you must track progress, loop, and keep going until everything in this card is satisfied.

---

### Role

Senior engineer. Produce drop-in, production-ready code.

---

### Scope (only this)

* **Fix:** Test coverage, structure, and reliability for the **TBCV system** so that:

  * Business-critical components (see **Coverage priorities**) hit **~100% coverage**.
  * Remaining core components reach at least **90–95% coverage**.
  * The **overall `tbcv` package coverage is ≥90%**.
  * The `tests/` tree is **organized by module** and clearly separates:

    * Unit tests (with and without mocks)
    * Integration / full-stack tests
* **No feature changes** beyond minimal refactors strictly required to make code testable.

---

### Allowed paths

You may create/modify files **only** in:

* `tests/` and its subfolders
* `agents/`
* `core/`
* `api/`
* `cli/`
* `svc/`
* `tools/` (only if needed for testability)
* Top-level helper scripts **related to test orchestration**, e.g.:

  * `run_all_tests.py`
  * `run_full_stack_test.py`
  * `run_smoke.py`
  * `validate_system.py`
  * `startup_check.py`
  * `health.py`

---

### Forbidden

* Any other files or directories not mentioned above.
* Changes to JSON truth files (`truth/*.json`) or rule data (`rules/*.json`), except for:

  * Adding **test fixtures** under `tests/fixtures/` that copy or subset those structures.

---

### Coverage priorities (TBCV-specific)

You must use these targets when designing and verifying tests:

**Tier A — 100% required (no margin):**

* `agents/*.py`
* `core/config.py`
* `core/validation_store.py`
* `core/rule_manager.py`
* `core/family_detector.py`
* `core/ingestion.py`
* `core/path_validator.py`
* `core/startup_checks.py`
* `core/prompt_loader.py`
* `core/utilities.py`
* `api/services/*.py`
* `api/server.py`
* `api/websocket_endpoints.py`
* `api/additional_endpoints.py`
* `api/export_endpoints.py`
* `cli/main.py`
* `svc/mcp_server.py`
* `startup_check.py`
* `validate_system.py`
* `health.py`

**Tier B — High coverage (≥90–95%):**

* `core/database.py`
* `core/cache.py`
* `core/logging.py`
* `core/ollama.py`
* `core/ollama_validator.py`
* `core/io_win.py`
* `api/dashboard.py`
* `api/server_extensions.py`
* Top-level orchestration scripts:

  * `run_all_tests.py`
  * `run_full_stack_test.py`
  * `run_smoke.py`
  * `inventory.py`
  * `diagnose.py`
  * `generate_docs.py`
  * `apply_patches.py`

**Tier C — Best effort (no strict target):**

* `templates/` (Jinja/HTML) – smoke tests on key templates only
* `tools/*.py` – reasonable coverage, no need to be exhaustive
* Data-only modules (rules & truth JSON) – covered indirectly via Tier A/B modules

---

### Progress tracker (you must update this as you go)

Maintain this table in your own responses and **update Status** as you complete each phase. Never stop before all are `DONE`.

| Phase | Description                                               | Status      |
| ----- | --------------------------------------------------------- | ----------- |
| P1    | Repo + docs review, test inventory, coverage baseline     | DONE        |
| P2    | Detailed coverage plan per module (Tier A/B/C)            | DONE        |
| P3    | Test layout refactor (`tests/` mirrored to modules)       | IN PROGRESS |
| P4    | Tier A modules brought to ~100% coverage                  | IN PROGRESS |
| P5    | Tier B modules raised to ≥90–95% coverage                 | TODO        |
| P6    | Tier C best-effort tests added                            | TODO        |
| P7    | Full suite stabilization (all tests green, deterministic) | TODO        |
| P8    | Final coverage run + acceptance checks + runbook          | TODO        |

**Latest Update (2025-11-19 - Autonomous Session Complete):**
- ✅ P4 Option A: Fixed 32 legacy test failures, achieved 85.6% pass rate
- ✅ Fixed critical Pydantic 2.11 config issue (unblocked all testing)
- ✅ P4 Option B Session 1: Created tests/core/test_database.py (29 tests, 18 passing, 52% module coverage)
- ✅ P4 Option B Session 2: Created tests/agents/test_truth_manager.py (34 tests, 25 passing, 84.3% module coverage)
- **Current: 483 passing tests (+42), 45.9% coverage (+1.9%)**
- **Total new tests: 63 | Net improvement: +42 passing tests**
- See: reports/autonomous_session_final_report.md for complete details

**Rule:**
If at any point:

* Coverage for a Tier A/B module is below its target, **or**
* Any test is flaky / non-deterministic, **or**
* Any acceptance check fails

→ you must go back to the relevant phase, adjust code/tests, and re-run until the table is all `DONE`.

---

### Execution plan (what you must actually do)

#### P1 — Understand & measure

1. Read `README.md` and `docs/architecture.md`, `docs/testing.md`.

2. Build a mental model of:

   * Agents (`agents/`)
   * Core utilities (`core/`)
   * API (`api/`)
   * CLI (`cli/`)
   * MCP (`svc/mcp_server.py`)

3. Inventory existing tests in `tests/`:

   * `test_cli_web_parity.py`
   * `test_endpoints_offline.py`
   * `test_enhancer_consumes_validation.py`
   * `test_full_stack_local.py`
   * `test_fuzzy_logic.py`
   * `test_recommendations.py`
   * `test_truth_validation.py`
   * `test_validation_persistence.py`
   * `test_websocket.py`
   * etc.

4. Run the baseline:

   ```bash
   pytest -q
   pytest --cov=tbcv --cov-report=term-missing
   ```

5. Capture:

   * Overall coverage
   * Per-module coverage for all Tier A and Tier B modules
   * List of completely untested files

Update progress table: set `P1` to `DONE` once you have this.

---

#### P2 — Concrete coverage map

1. For each Tier A / B module, list:

   * Public functions / classes / methods
   * Key branches (feature flags, error paths, conditionals)
2. Decide for each module:

   * **Unit tests without mocks**: which behaviours can be tested purely
   * **Unit tests with mocks**: which external dependencies must be mocked (DB, filesystem, LLMs, network)
   * **Integration tests**: which flows will be covered by existing or new full-stack tests
3. Produce a short mapping (in comments or design section) like:

   ```text
   agents/truth_manager.py
     - unit (no mocks): plugin loading, B-tree indexing, lookup logic
     - unit (mocks): corrupted truth data, missing plugin paths
     - integration: end-to-end validation via orchestrator + truth manager
   ```

Update the progress table: `P2` → `DONE`.

---

#### P3 — Test layout refactor

1. Create or adjust subdirectories under `tests/`:

   * `tests/agents/`
   * `tests/core/`
   * `tests/api/`
   * `tests/cli/`
   * `tests/svc/`
   * `tests/tools/`
   * Optional: `tests/fixtures/` for reusable truth/rule/DB fixtures

2. Move or split existing tests where appropriate so that:

   * Module-specific logic lives in `tests/<package>/test_<module>.py`
   * End-to-end tests remain at `tests/test_*.py` (but may be renamed for clarity)

3. Extract shared fixtures into `tests/conftest.py`:

   * In-memory DB/session
   * Sample truth/rule data
   * FastAPI test client
   * CLI runner (e.g. with `click` or `subprocess` patterns)
   * Mocked LLM client for ollama/Gemini

Update `P3` → `DONE` once layout is consistent and tests still run.

---

#### P4 — Tier A to ~100% coverage

For each Tier A module:

1. Add **unit tests without mocks** covering:

   * Normal flows
   * Edge inputs (empty plugin sets, missing metadata, etc.)
   * Idempotency where promised

2. Add **unit tests with mocks**:

   * DB failures
   * LLM/ollama timeouts & errors (must be mocked; no real calls)
   * Misconfigured rules/truth

3. Add any necessary micro-refactors to enable DI (dependency injection) instead of hard-coded singletons, but:

   * Keep public signatures stable; if you must change, update all call sites.

4. Re-run:

   ```bash
   pytest tests/agents tests/core tests/api tests/cli tests/svc -q
   pytest --cov=tbcv --cov-report=term-missing
   ```

5. Confirm each Tier A file hits **~100% coverage**; if any doesn’t, add tests until it does (or add comments explaining truly unreachable lines).

Set `P4` → `DONE` only when **all** Tier A modules reach their target.

---

#### P5 — Tier B to ≥90–95% coverage

1. For each Tier B module, add tests (unit + integration) to cover:

   * Happy paths
   * Representative errors (e.g., DB unavailable, cache miss, logging failures)
2. For `core/ollama.py` and `core/ollama_validator.py`:

   * All tests must mock HTTP/LLM calls.
   * Verify:

     * Request payload construction
     * Handling of success and failure responses
     * Retry / backoff behaviour (if implemented)
3. Re-run coverage checks and raise each Tier B file to ≥90–95%.

Set `P5` → `DONE` once all Tier B modules meet the threshold.

---

#### P6 — Tier C best effort

1. Add smoke tests for key templates in `templates/`:

   * Ensure rendering works with minimal context.
2. Add tests for at least the most frequently used tools under `tools/`:

   * `validate_folder.py`
   * `endpoint_check.py`
3. Do not overfit; focus on catching regressions, not perfect coverage.

Set `P6` → `DONE` when Tier C has basic coverage.

---

#### P7 — Stabilization

1. Run the full suite multiple times to ensure determinism:

   ```bash
   pytest -q
   pytest -q
   ```

2. Fix flakiness by:

   * Seeding RNG
   * Freezing time
   * Avoiding race conditions or real networking

3. Ensure no tests depend on external services, internet access, or real LLMs.

Set `P7` → `DONE` when the suite is stable.

---

#### P8 — Final acceptanh p7
inue witcontce and runbook

**Acceptance checks (must pass locally):**

* **CLI sanity:**

  ```bash
  # Adjust if an entry point script exists; this is the canonical form:
  python -m tbcv.cli.main --help
  ```

* **Web / API health:**

  ```bash
  python -m tbcv.api.server &
  # In another shell (or via HTTP client within tests)
  curl http://127.0.0.1:8080/health/live
  curl http://127.0.0.1:8080/health/ready
  ```

  > Note: For tests, prefer FastAPI’s `TestClient` instead of real processes.

* **Tests & coverage:**

  ```bash
  pytest -q
  pytest --cov=tbcv --cov-report=term-missing
  ```

  * Overall `tbcv` coverage ≥90%
  * Tier A ~100% covered
  * Tier B ≥90–95%

Once all green, set `P8` → `DONE`.

---

### Hard rules

* Windows-friendly paths, **CRLF preserved** in existing files.
* **Keep public function signatures** unless you justify and update all call sites.
* **Zero network calls in tests** (this includes HTTP, LLM/ollama, external DBs).
* Deterministic runs:

  * Set seeds where randomness is used.
  * Avoid time-based flakiness (freeze time or inject clocks).
* Do **not** introduce new dependencies:

  * Use only stdlib + existing test stack (pytest, FastAPI test client, etc.).
* No mock data in production paths; mocks only in tests.

---

### Deliverables

* Full file replacements only (no patch/diff format), for:

  * New/updated tests under `tests/`
  * Any code changes under allowed paths required for testability
* New tests in `/tests/` covering:

  * Happy paths
  * Failing paths that used to break or were previously untested
* If any schemas or DB models change:

  * Include forward-compatible migration code

---

### Self-review (answer yes/no at the very end)

You must explicitly answer **yes/no** to each:

* Thorough, systematic
* Wired UI and backend
* MCP usage intact
* CLI and Web in sync
* Tests added and passing
* Tier A ~100% covered; Tier B ≥90–95%; overall ≥90%
* No flaky tests; deterministic runs

---

### When you respond (final output shape)

At the end of your work (when all phases are `DONE`), your **final** response must:

1. **Show the minimal design for the change**

   * Short summary of coverage strategy and test layout applied (can reuse/condense from above).
2. **Provide the full updated files**

   * Include the complete content of any new/modified `.py` files under allowed paths.
3. **Provide the tests**

   * All new/updated test files under `tests/` in full content.
4. **Provide a short runbook (exact commands in order)** to:

   * Run the full test suite
   * Check coverage
   * Perform the basic CLI and API health checks
