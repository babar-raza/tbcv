### TASKCARD 1 – Robust fuzzy matching and pattern coverage

Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):

* Fix: Fuzzy plugin detection uses limited regex patterns and fixed confidence instead of multi algorithm matching and broader coverage
* Allowed paths:

  * agents/fuzzy_detector.py
  * core/rule_manager.py
  * truth/
  * config/
  * tests/test_fuzzy_logic.py
* Forbidden: any other file

Acceptance checks (must pass locally):

* CLI: `python cli/main.py validate-file path/to/your_spec.md --family words` runs to completion and reports detections using the new confidence model
* Web: `python main.py --mode api` then open `http://127.0.0.1:8080/dashboard`, validate a spec, and see fuzzy detections reflected in workflow details
* Tests: `pytest tests/test_fuzzy_logic.py -q`
* No mock data used in production paths
* Configs in `./config/` are enforced end to end

Deliverables:

* Full file replacements only (no diffs, no stubs, no TODO)
* New or updated tests in `tests/` covering:

  * Happy path: correctly detected plugins with realistic near matches
  * Failing path: ambiguous or invalid names produce low confidence or no match
* If schemas change, include forward compatible migration code

Hard rules:

* Windows friendly paths, CRLF preserved
* Keep public function signatures unless you justify and update all call sites
* Zero network calls in tests
* Deterministic runs: set seeds, stable ordering for match lists
* Do not introduce new dependencies (implement matching using standard library or existing deps only)

Now:

1. Show the minimal design for the change
2. Provide the full updated files
3. Provide the tests
4. Provide a short runbook: exact commands in order

---

### TASKCARD 2 – Truth manager indexing and lookup model

Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):

* Fix: Truth manager indexing does not match documented structure and is not optimized or clearly modeled
* Allowed paths:

  * agents/truth_manager.py
  * core/rule_manager.py
  * truth/
  * core/validation_store.py
  * tests/test_truth_validation.py
* Forbidden: any other file

Acceptance checks (must pass locally):

* CLI: `python cli/main.py validate-file path/to/your_spec.md --family words` correctly validates declared plugins and combinations using the new indexing
* Web: `python main.py --mode api`, validate via dashboard, and see accurate truth validation (no false unknown plugin errors for valid specs)
* Tests: `pytest tests/test_truth_validation.py -q`
* No mock data used in production paths
* Configs in `./config/` are enforced end to end

Deliverables:

* Full file replacements only
* New or updated tests in `tests/` covering:

  * Happy path: fast repeated lookups for many plugins and combinations
  * Failing path: unknown plugin or invalid combination correctly flagged
* If data layout changes, provide migration that preserves existing `truth/` JSONs or clearly transforms them

Hard rules:

* Windows friendly paths, CRLF preserved
* Keep public function signatures unless you justify and update all call sites
* Zero network calls in tests
* Deterministic runs: stable ordering of truth listings and errors
* Do not introduce new dependencies (implement indexing using standard library data structures)

Now:

1. Show the minimal design for the change
2. Provide the full updated files
3. Provide the tests
4. Provide a short runbook: exact commands in order

---

### TASKCARD 3 – Weighted confidence aggregation for detection

Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):

* Fix: Confidence scoring does not combine multiple detection signals as described; everything uses a fixed confidence
* Allowed paths:

  * agents/fuzzy_detector.py
  * agents/orchestrator.py
  * core/config.py
  * tests/test_fuzzy_logic.py
  * tests/test_truth_validation.py
* Forbidden: any other file

Acceptance checks (must pass locally):

* CLI: `python cli/main.py validate-file path/to/your_spec.md --family words` produces per plugin confidence that reflects multiple signals
* Web: `python main.py --mode api`, run validation from dashboard and confirm that confidence shown in workflows is consistent and stable across runs
* Tests: `pytest tests/test_fuzzy_logic.py -q`
* No mock data used in production paths
* Configs in `./config/` are enforced end to end (weights and thresholds configurable)

Deliverables:

* Full file replacements only
* New or updated tests in `tests/` covering:

  * Happy path: multiple algorithms or signals combined into a single confidence score
  * Failing path: low quality matches fall below configured threshold and are dropped
* If result schemas change, provide forward compatible adjustments in orchestrator and any consumers

Hard rules:

* Windows friendly paths, CRLF preserved
* Keep public function signatures unless you justify and update all call sites
* Zero network calls in tests
* Deterministic runs: same input content and config always yields identical confidence scores
* Do not introduce new dependencies

Now:

1. Show the minimal design for the change
2. Provide the full updated files
3. Provide the tests
4. Provide a short runbook: exact commands in order

---

### TASKCARD 4 – Two stage validation with LLM gating

Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):

* Fix: Heuristic and LLM validation are not wired into a documented two stage gating pipeline
* Allowed paths:

  * agents/orchestrator.py
  * agents/content_validator.py
  * agents/llm_validator.py
  * core/config.py
  * core/validation_store.py
  * tests/test_truth_validation.py
  * tests/test_recommendations.py
* Forbidden: any other file

Acceptance checks (must pass locally):

* CLI: `python cli/main.py validate-file path/to/your_spec.md --family words` runs a two stage validation when LLM is enabled in config and records gated results
* Web: `python main.py --mode api`, enable LLM in config, run validation from dashboard, and verify that:

  * Heuristic issues are produced
  * LLM validation can downgrade, confirm, or escalate issues per config
* Tests: `pytest tests/test_truth_validation.py -q`
* No mock data used in production paths
* Configs in `./config/` control whether LLM gating is enabled and define thresholds

Deliverables:

* Full file replacements only
* New or updated tests in `tests/` covering:

  * Happy path: both stages run; final `ValidationRecord`s reflect combined decisions
  * Failing path: LLM unavailable or disabled falls back to heuristics with predictable behavior
* If schemas change, provide forward compatible migration for stored validation records

Hard rules:

* Windows friendly paths, CRLF preserved
* Keep public function signatures unless you justify and update all call sites
* Zero network calls in tests (LLM calls must be mocked or disabled under tests)
* Deterministic runs: same content and configuration produce the same set of issues
* Do not introduce new dependencies

Now:

1. Show the minimal design for the change
2. Provide the full updated files
3. Provide the tests
4. Provide a short runbook: exact commands in order

---

### TASKCARD 5 – Enhancement safety (rewrite ratio and blocked topics)

Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):

* Fix: Enhancer does not enforce rewrite ratio gates or blocked topic checks described in docs
* Allowed paths:

  * agents/content_enhancer.py
  * agents/enhancement_agent.py
  * core/config.py
  * prompts/enhancer.json
  * tests/test_recommendations.py
* Forbidden: any other file

Acceptance checks (must pass locally):

* CLI: `python cli/main.py enhance path/to/your_spec.md --family words` respects configured rewrite ratio and blocked topics
* Web: `python main.py --mode api`, trigger enhancement via dashboard and see:

  * Enhancements are applied when within allowed ratio
  * Over aggressive rewrites are gated or flagged with a clear status
* Tests: `pytest tests/test_recommendations.py -q`
* No mock data used in production paths
* Configs in `./config/` define rewrite ratio thresholds and blocked topics

Deliverables:

* Full file replacements only
* New or updated tests in `tests/` covering:

  * Happy path: safe enhancements under threshold with no blocked topics
  * Failing path: content that would violate ratio or introduces blocked phrases is rejected or downgraded
* If enhancement result schema changes, provide migration and keep existing flows working

Hard rules:

* Windows friendly paths, CRLF preserved
* Keep public function signatures unless you justify and update all call sites
* Zero network calls in tests
* Deterministic runs: same inputs and config yield the same decision about gating
* Do not introduce new dependencies

Now:

1. Show the minimal design for the change
2. Provide the full updated files
3. Provide the tests
4. Provide a short runbook: exact commands in order

---

### TASKCARD 6 – Owner identification and persistence

Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):

* Fix: Owner identification for content is completely missing despite being promised in docs
* Allowed paths:

  * agents/

    * agents/base.py
    * agents/orchestrator.py
    * (new) agents/owner_detector.py
  * core/database.py
  * core/validation_store.py
  * core/config.py
  * api/server.py
  * templates/dashboard_home.html
  * templates/dashboard_home_enhanced.html
  * tests/test_cli_web_parity.py
  * tests/test_truth_validation.py
* Forbidden: any other file

Acceptance checks (must pass locally):

* CLI: `python cli/main.py validate-file path/to/your_spec.md --family words` records an inferred owner on the created workflow
* Web: `python main.py --mode api`, run a validation via dashboard and see the owner displayed on workflow details
* Tests: `pytest tests/test_truth_validation.py -q`
* No mock data used in production paths for owner; use deterministic heuristics from path, metadata or config
* Configs in `./config/` allow tuning or disabling owner inference

Deliverables:

* Full file replacements only
* New or updated tests in `tests/` covering:

  * Happy path: consistent owner inference for typical content locations
  * Failing path: unknown or ambiguous cases fall back to a safe default without crashing
* If database schema changes (owner fields), include forward compatible migration code

Hard rules:

* Windows friendly paths, CRLF preserved
* Keep public function signatures unless you justify and update all call sites
* Zero network calls in tests (no git or external APIs in test runs)
* Deterministic runs: same file and configuration always infer the same owner
* Do not introduce new dependencies

Now:

1. Show the minimal design for the change
2. Provide the full updated files
3. Provide the tests
4. Provide a short runbook: exact commands in order

---

### TASKCARD 7 – Authentication and role based access control

Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):

* Fix: API and dashboard have no authentication or role based access despite docs promising Reviewer, Operator, Auditor roles
* Allowed paths:

  * api/server.py
  * api/server_extensions.py
  * api/dashboard.py
  * api/additional_endpoints.py
  * api/websocket_endpoints.py
  * core/database.py
  * core/config.py
  * templates/*.html
  * tests/test_cli_web_parity.py
  * tests/test_websocket.py
  * test_endpoints.py
* Forbidden: any other file

Acceptance checks (must pass locally):

* CLI: `python cli/main.py status` or another non privileged command works without auth as today (do not break CLI)
* Web: `python main.py --mode api`, access:

  * Anonymous user is blocked or redirected from protected views
  * Role based permissions enforce who can validate, enhance, or change status
* Tests: `pytest tests/test_cli_web_parity.py tests/test_websocket.py test_endpoints.py -q`
* No mock data used in production auth; tests can use in memory users and roles
* Configs in `./config/` define auth mode and role mappings

Deliverables:

* Full file replacements only
* New or updated tests in `tests/` and `test_endpoints.py` covering:

  * Happy path: each role can access the allowed endpoints and UI actions
  * Failing path: unauthorized access is rejected with correct HTTP status and UI handling
* If database schema changes (users, roles, permissions), include forward compatible migration code

Hard rules:

* Windows friendly paths, CRLF preserved
* Keep public function signatures unless you justify and update all call sites
* Zero network calls in tests
* Deterministic runs: same user and role configuration always yields the same access decisions
* Do not introduce new dependencies (implement auth with FastAPI and standard libraries or existing deps)

Now:

1. Show the minimal design for the change
2. Provide the full updated files
3. Provide the tests
4. Provide a short runbook: exact commands in order

---

### TASKCARD 8 – Audit logging for actions and workflows

Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):

* Fix: There is no persistent audit log for actions even though the docs describe full auditability
* Allowed paths:

  * core/database.py
  * core/logging.py
  * core/validation_store.py
  * api/server.py
  * api/additional_endpoints.py
  * api/services/status_recalculator.py
  * templates/audit_logs.html
  * tests/test_cli_web_parity.py
  * test_endpoints.py
* Forbidden: any other file

Acceptance checks (must pass locally):

* CLI: typical operations (validate file, enhance) write audit records without breaking existing workflows
* Web: `python main.py --mode api`, perform validations and enhancements, then:

  * View audit log via dashboard page that lists actions with user, time, entity and severity
* Tests: `pytest tests/test_cli_web_parity.py test_endpoints.py -q`
* No mock data used in production paths; tests can create temporary users or roles in test database
* Configs in `./config/` can enable or disable detailed audit logging

Deliverables:

* Full file replacements only
* New or updated tests in `tests/` and `test_endpoints.py` covering:

  * Happy path: each major operation writes at least one audit record
  * Failing path: audit logging failure does not break main workflow but is surfaced appropriately
* If database schema changes (AuditLog model), ship forward compatible migration code

Hard rules:

* Windows friendly paths, CRLF preserved
* Keep public function signatures unless you justify and update all call sites
* Zero network calls in tests
* Deterministic runs: same sequence of operations yields a predictable sequence of audit records
* Do not introduce new dependencies

Now:

1. Show the minimal design for the change
2. Provide the full updated files
3. Provide the tests
4. Provide a short runbook: exact commands in order

---

### TASKCARD 9 – Dashboard batch actions, filters, and metrics

Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):

* Fix: Dashboard does not expose batch actions, deferral, filtering, or metrics widgets described in the documentation
* Allowed paths:

  * api/dashboard.py
  * api/additional_endpoints.py
  * api/services/recommendation_consolidator.py
  * templates/dashboard_home.html
  * templates/dashboard_home_enhanced.html
  * templates/base.html
  * tests/test_cli_web_parity.py
* Forbidden: any other file

Acceptance checks (must pass locally):

* CLI: unchanged behavior
* Web: `python main.py --mode api`, open dashboard:

  * Can filter workflows and recommendations by status, severity, and date
  * Can perform batch actions (approve, defer, apply) where supported
  * Metrics widgets display basic counts (errors, warnings, pending workflows) without breaking performance
* Tests: `pytest tests/test_cli_web_parity.py -q`
* No mock data used in production; tests use seeded workflows and recommendations in a test database

Deliverables:

* Full file replacements only
* New or updated tests in `tests/` covering:

  * Happy path: batch actions correctly update state and UI
  * Failing path: invalid batch actions are rejected and UI shows clear feedback
* No schema changes expected; if needed, keep them forward compatible

Hard rules:

* Windows friendly paths, CRLF preserved
* Keep public function signatures unless you justify and update all call sites
* Zero network calls in tests
* Deterministic runs: same seed data yields the same metrics and filtered lists
* Do not introduce new dependencies

Now:

1. Show the minimal design for the change
2. Provide the full updated files
3. Provide the tests
4. Provide a short runbook: exact commands in order

---

### TASKCARD 10 – Endpoint completion and MCP integration

Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):

* Fix: Several documented endpoints and MCP behaviors are missing or stubbed (`list_truths`, `clear_cache`, `drop_cache`, real MCP apply)
* Allowed paths:

  * api/additional_endpoints.py
  * api/export_endpoints.py
  * api/services/mcp_client.py
  * core/cache.py
  * core/config.py
  * tests/test_cli_web_parity.py
  * test_endpoints.py
* Forbidden: any other file

Acceptance checks (must pass locally):

* CLI: unchanged behavior
* Web/API: `python main.py --mode api`, then via curl or test scripts:

  * `list_truths`, `clear_cache`, `drop_cache`, and report export endpoints all exist and behave as documented
  * MCP client functions are no longer pure stubs in production code paths, but tests use safe mocks
* Tests: `pytest test_endpoints.py tests/test_cli_web_parity.py -q`
* No mock data used in production paths; tests can mock MCP behavior
* Configs in `./config/` define MCP behavior and cache policies

Deliverables:

* Full file replacements only
* New or updated tests covering:

  * Happy path: all endpoints respond with correct status, payload shapes, and side effects
  * Failing path: invalid requests or MCP failures are handled gracefully
* If any response schema changes, document and keep them backward compatible where possible

Hard rules:

* Windows friendly paths, CRLF preserved
* Keep public function signatures unless you justify and update all call sites
* Zero network calls in tests (MCP and external calls must be mocked)
* Deterministic runs: idempotent cache operations with predictable effects
* Do not introduce new dependencies

Now:

1. Show the minimal design for the change
2. Provide the full updated files
3. Provide the tests
4. Provide a short runbook: exact commands in order

---

### TASKCARD 11 – Scheduled jobs for health checks and cache maintenance

Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):

* Fix: Jobs and scheduling layer for periodic health checks and cache eviction is missing; `jobs/` is empty
* Allowed paths:

  * jobs/
  * core/cache.py
  * core/startup_checks.py
  * core/config.py
  * api/server_extensions.py
  * api/server.py
  * tests/test_cli_web_parity.py
  * tests/test_truth_validation.py
* Forbidden: any other file

Acceptance checks (must pass locally):

* CLI: optional scheduled tasks can be triggered in a controlled way for testing (no background daemons started unexpectedly by CLI)
* Web: `python main.py --mode api`:

  * Periodic jobs run in process using existing libraries and configuration only
  * Cache eviction and health checks happen without blocking main request handling
* Tests: `pytest tests/test_cli_web_parity.py tests/test_truth_validation.py -q`
* No mock data used in production paths
* Configs in `./config/` allow enabling, disabling, and tuning job intervals

Deliverables:

* Full file replacements only
* New or updated tests in `tests/` covering:

  * Happy path: scheduled tasks execute at least once in a controlled test environment and perform expected side effects
  * Failing path: job failures do not crash the server and are logged appropriately
* No external scheduler dependencies; use existing async or threading primitives

Hard rules:

* Windows friendly paths, CRLF preserved
* Keep public function signatures unless you justify and update all call sites
* Zero network calls in tests
* Deterministic runs: under test, job scheduling and execution order are predictable and controlled
* Do not introduce new dependencies

Now:

1. Show the minimal design for the change
2. Provide the full updated files
3. Provide the tests
4. Provide a short runbook: exact commands in order

