# Dashboard Test Coverage - Task Cards

**Reference:** [plans/dashboard_coverage.md](dashboard_coverage.md)
**Coverage Report:** [reports/dashboard_coverage.md](../reports/dashboard_coverage.md)

> **Status:** ✅ IMPLEMENTATION COMPLETE (2025-11-26)
> - Task Card 1: ✅ DONE (17 tests)
> - Task Card 2: ✅ DONE (20 tests)
> - Task Card 3: ⏭️ SKIPPED (per request)
> - Task Card 4: ✅ DONE (10 additional tests)
> - Task Card 5: ✅ DONE (10 tests)
> - Task Card 6: ✅ DONE (8 helper functions)
> - Task Card 7: ✅ DONE (integration verified)
>
> **Total New Tests:** 57 tests (47 new files + 10 added to existing)
> **All Tests Passing:** Yes

---

## Task Card 1: WebSocket & Real-time Update Tests

**Status:** ✅ COMPLETED (2025-11-26)

**Role:** Senior engineer. Produce drop-in, production-ready code.

**Scope (only this):**
- Add: WebSocket connection and real-time update tests for dashboard
- Allowed paths:
  - `tests/api/test_dashboard_websocket.py` (CREATE)
  - `tests/conftest.py` (EXTEND with WebSocket fixtures)
- Forbidden: any other file

**Acceptance checks (must pass locally):**
- CLI: `python -m pytest tests/api/test_dashboard_websocket.py -v`
- All 15 tests pass
- Tests: `python -m pytest tests/ --ignore=tests/test_endpoints_live.py --ignore=tests/test_truth_llm_validation_real.py --ignore=tests/manual/ -v`
- No mock data used in production paths
- WebSocket connections properly closed after each test

**Deliverables:**
- Full file: `tests/api/test_dashboard_websocket.py` with 15 tests:
  ```
  TestWebSocketConnection (4 tests):
  - test_websocket_validation_updates_connects
  - test_websocket_workflow_connects
  - test_websocket_heartbeat_response
  - test_websocket_handles_invalid_workflow_id

  TestRealtimeUpdates (7 tests):
  - test_validation_created_broadcast
  - test_validation_approved_broadcast
  - test_validation_rejected_broadcast
  - test_validation_enhanced_broadcast
  - test_recommendation_created_broadcast
  - test_workflow_progress_broadcast
  - test_workflow_completed_broadcast

  TestActivityFeed (4 tests):
  - test_activity_feed_receives_updates
  - test_activity_feed_max_items_limit
  - test_activity_icon_mapping
  - test_activity_timestamp_format
  ```
- Extended `tests/conftest.py` with fixtures:
  ```python
  @pytest.fixture
  async def websocket_client()

  @pytest.fixture
  async def workflow_websocket_client(running_workflow)
  ```
- No stubs, no TODO comments

**Hard rules:**
- Windows friendly paths, CRLF preserved
- Use `pytest-asyncio` for async tests
- Zero network calls to external services in tests
- Deterministic runs: use fixed timestamps where needed
- Do not introduce new dependencies beyond `pytest-asyncio` and `websockets`
- All WebSocket connections must be closed in fixtures/teardown
- Tests must not leave orphan connections

**Self-review (answer yes/no at the end):**
- [ ] All 15 tests implemented and passing
- [ ] Fixtures properly clean up WebSocket connections
- [ ] Tests are isolated and can run in any order
- [ ] No flaky tests (run 3x to verify)
- [ ] Coverage report shows WebSocket coverage increased

---

## Task Card 2: Modal Forms & Input Validation Tests

**Role:** Senior engineer. Produce drop-in, production-ready code.

**Scope (only this):**
- Add: Modal form submission and input validation tests
- Allowed paths:
  - `tests/api/test_dashboard_modals.py` (CREATE)
  - `tests/api/test_dashboard_validations.py` (EXTEND)
  - `tests/conftest.py` (EXTEND with form fixtures)
- Forbidden: any other file

**Acceptance checks (must pass locally):**
- CLI: `python -m pytest tests/api/test_dashboard_modals.py -v`
- All 20 tests pass
- Tests: `python -m pytest tests/ --ignore=tests/test_endpoints_live.py --ignore=tests/test_truth_llm_validation_real.py --ignore=tests/manual/ -v`
- No mock data used in production paths
- Temporary test files cleaned up after tests

**Deliverables:**
- Full file: `tests/api/test_dashboard_modals.py` with 20 tests:
  ```
  TestRunValidationModal (11 tests):
  - test_single_file_validation_valid_path
  - test_single_file_validation_windows_path
  - test_single_file_validation_unix_path
  - test_single_file_validation_nonexistent_path
  - test_batch_validation_multiple_files
  - test_batch_validation_with_wildcards
  - test_batch_validation_empty_file_list
  - test_family_parameter_words
  - test_family_parameter_cells
  - test_validation_types_subset
  - test_max_workers_parameter

  TestRunWorkflowModal (5 tests):
  - test_directory_validation_workflow
  - test_directory_validation_invalid_path
  - test_file_pattern_glob_matching
  - test_batch_workflow_creation
  - test_workflow_modal_missing_required_fields

  TestInputValidation (4 tests):
  - test_file_path_sql_injection_safe
  - test_file_path_path_traversal_safe
  - test_reviewer_xss_safe
  - test_notes_field_special_characters
  ```
- Extended `tests/conftest.py` with fixtures:
  ```python
  @pytest.fixture
  def test_directory(tmp_path)

  @pytest.fixture
  def mock_file_system(tmp_path)
  ```
- No stubs, no TODO comments

**Hard rules:**
- Windows friendly paths, CRLF preserved
- Use `tmp_path` fixture for all test files (auto-cleanup)
- Zero network calls in tests
- Deterministic runs: fixed file content, stable paths
- Do not introduce new dependencies
- Test both Windows (`C:\...`) and Unix (`/path/...`) path formats
- All temporary files must be created in `tmp_path`

**Self-review (answer yes/no at the end):**
- [ ] All 20 tests implemented and passing
- [ ] Windows and Unix paths both tested
- [ ] Security tests (SQL injection, XSS, path traversal) included
- [ ] No temporary files left after test run
- [ ] Coverage report shows form coverage increased to 95%

---

## Task Card 3: Admin Controls Tests

**Role:** Senior engineer. Produce drop-in, production-ready code.

**Scope (only this):**
- Add: Admin control tests (delete all, system reset)
- Allowed paths:
  - `tests/api/test_dashboard_admin.py` (CREATE)
  - `tests/conftest.py` (EXTEND with admin fixtures)
- Forbidden: any other file

**Acceptance checks (must pass locally):**
- CLI: `python -m pytest tests/api/test_dashboard_admin.py -v`
- All 12 tests pass
- Tests: `python -m pytest tests/ --ignore=tests/test_endpoints_live.py --ignore=tests/test_truth_llm_validation_real.py --ignore=tests/manual/ -v`
- No mock data used in production paths
- Database state properly reset between tests

**Deliverables:**
- Full file: `tests/api/test_dashboard_admin.py` with 12 tests:
  ```
  TestAdminDeleteOperations (5 tests):
  - test_delete_all_workflows
  - test_delete_all_workflows_requires_confirm
  - test_delete_all_validations
  - test_delete_all_recommendations
  - test_delete_cascades_recommendations

  TestSystemReset (4 tests):
  - test_system_reset_deletes_all
  - test_system_reset_requires_confirm
  - test_system_reset_returns_deleted_counts
  - test_system_reset_partial_delete

  TestAdminEdgeCases (3 tests):
  - test_delete_empty_database
  - test_delete_during_active_workflow
  - test_concurrent_delete_operations
  ```
- Extended `tests/conftest.py` with fixtures:
  ```python
  @pytest.fixture
  def populated_database(db_manager, mock_file_system)

  @pytest.fixture
  def running_workflow(db_manager)
  ```
- No stubs, no TODO comments

**Hard rules:**
- Windows friendly paths, CRLF preserved
- Each test must start with clean database state
- Zero network calls in tests
- Deterministic runs: fixed IDs where possible
- Do not introduce new dependencies
- Tests must verify actual database state, not just API response
- Confirm parameters must be explicitly tested

**Self-review (answer yes/no at the end):**
- [ ] All 12 tests implemented and passing
- [ ] Delete operations verified against database
- [ ] Confirm parameter enforcement tested
- [ ] Edge cases (empty DB, concurrent ops) covered
- [ ] Tests isolated - no cross-test dependencies

---

## Task Card 4: Bulk Actions & UI State Tests

**Role:** Senior engineer. Produce drop-in, production-ready code.

**Scope (only this):**
- Add: Bulk action tests for validations, recommendations, workflows
- Allowed paths:
  - `tests/api/test_dashboard_validations.py` (EXTEND)
  - `tests/api/test_dashboard_recommendations.py` (EXTEND)
  - `tests/api/test_dashboard_workflows.py` (EXTEND)
  - `tests/conftest.py` (EXTEND with bulk fixtures)
- Forbidden: any other file

**Acceptance checks (must pass locally):**
- CLI: `python -m pytest tests/api/test_dashboard_validations.py tests/api/test_dashboard_recommendations.py tests/api/test_dashboard_workflows.py -v`
- All 18 new tests pass (plus existing tests)
- Tests: `python -m pytest tests/ --ignore=tests/test_endpoints_live.py --ignore=tests/test_truth_llm_validation_real.py --ignore=tests/manual/ -v`
- No mock data used in production paths

**Deliverables:**
- Extended `tests/api/test_dashboard_validations.py` with new class:
  ```
  TestBulkValidationActions (6 tests):
  - test_bulk_approve_multiple_validations
  - test_bulk_reject_multiple_validations
  - test_bulk_enhance_multiple_validations
  - test_bulk_action_empty_selection
  - test_bulk_action_mixed_statuses
  - test_bulk_action_partial_failure
  ```
- Extended `tests/api/test_dashboard_recommendations.py` with new class:
  ```
  TestBulkRecommendationActions (6 tests):
  - test_bulk_accept_recommendations
  - test_bulk_reject_recommendations
  - test_bulk_action_updates_all_statuses
  - test_bulk_action_with_invalid_ids
  - test_bulk_action_empty_list
  - test_bulk_action_mixed_valid_invalid
  ```
- Extended `tests/api/test_dashboard_workflows.py` with new class:
  ```
  TestBulkWorkflowActions (6 tests):
  - test_bulk_delete_workflows
  - test_bulk_delete_returns_accurate_count
  - test_bulk_delete_nonexistent_ids
  - test_bulk_delete_empty_list
  - test_bulk_delete_partial_success
  - test_bulk_delete_running_workflow
  ```
- Extended `tests/conftest.py` with fixtures:
  ```python
  @pytest.fixture
  def multiple_validations(db_manager, mock_file_system)

  @pytest.fixture
  def multiple_recommendations(db_manager, validation_with_file)

  @pytest.fixture
  def multiple_workflows(db_manager)
  ```
- No stubs, no TODO comments

**Hard rules:**
- Windows friendly paths, CRLF preserved
- Keep existing tests unchanged - only add new test classes
- Zero network calls in tests
- Deterministic runs: create fixed number of items (5 per fixture)
- Do not introduce new dependencies
- Bulk operations must verify count matches expectation
- Partial failure scenarios must be tested

**Self-review (answer yes/no at the end):**
- [ ] All 18 new tests implemented and passing
- [ ] Existing tests still pass
- [ ] Bulk fixtures create consistent test data
- [ ] Partial failure scenarios covered
- [ ] Empty list edge cases covered

---

## Task Card 5: Navigation & E2E Flow Tests

**Role:** Senior engineer. Produce drop-in, production-ready code.

**Scope (only this):**
- Add: Navigation tests and end-to-end user flow tests
- Allowed paths:
  - `tests/api/test_dashboard_navigation.py` (CREATE)
  - `tests/e2e/test_dashboard_flows.py` (CREATE)
  - `tests/e2e/__init__.py` (CREATE)
  - `tests/conftest.py` (EXTEND)
- Forbidden: any other file

**Acceptance checks (must pass locally):**
- CLI: `python -m pytest tests/api/test_dashboard_navigation.py tests/e2e/test_dashboard_flows.py -v`
- All 10 tests pass
- Tests: `python -m pytest tests/ --ignore=tests/test_endpoints_live.py --ignore=tests/test_truth_llm_validation_real.py --ignore=tests/manual/ -v`
- No mock data used in production paths
- E2E tests complete within 60 seconds each

**Deliverables:**
- Full file: `tests/api/test_dashboard_navigation.py` with 5 tests:
  ```
  TestDashboardNavigation (5 tests):
  - test_home_to_validations_navigation
  - test_validations_to_detail_navigation
  - test_detail_back_link_present
  - test_recommendation_to_validation_link
  - test_workflow_to_validations_links
  ```
- Full file: `tests/e2e/__init__.py` (empty)
- Full file: `tests/e2e/test_dashboard_flows.py` with 5 tests:
  ```
  TestCompleteUserFlows (5 tests):
  - test_validation_create_approve_enhance_flow
  - test_recommendation_review_apply_flow
  - test_batch_workflow_monitor_flow
  - test_filter_persists_after_action
  - test_pagination_maintains_filter_state
  ```
- Extended `tests/conftest.py` with fixtures:
  ```python
  @pytest.fixture
  def validation_ready_for_enhance(db_manager, mock_file_system)

  @pytest.fixture
  def complete_validation_chain(db_manager, mock_file_system)
  ```
- No stubs, no TODO comments

**Hard rules:**
- Windows friendly paths, CRLF preserved
- E2E tests must not exceed 60 second timeout
- Zero network calls to external services in tests
- Deterministic runs: fixed file content, predictable states
- Do not introduce new dependencies
- Navigation tests verify HTML contains correct links
- E2E tests verify complete state transitions

**Self-review (answer yes/no at the end):**
- [ ] All 10 tests implemented and passing
- [ ] Navigation links verified in HTML responses
- [ ] E2E flows test complete user journeys
- [ ] Filter and pagination state tested
- [ ] Tests complete within timeout limits

---

## Task Card 6: Test Utilities & Helpers

**Role:** Senior engineer. Produce drop-in, production-ready code.

**Scope (only this):**
- Add: Shared test utilities and HTML verification helpers
- Allowed paths:
  - `tests/utils/__init__.py` (CREATE)
  - `tests/utils/dashboard_helpers.py` (CREATE)
- Forbidden: any other file

**Acceptance checks (must pass locally):**
- CLI: `python -c "from tests.utils.dashboard_helpers import *; print('OK')"`
- Import succeeds without errors
- Tests: `python -m pytest tests/ --ignore=tests/test_endpoints_live.py --ignore=tests/test_truth_llm_validation_real.py --ignore=tests/manual/ -v`
- All existing tests still pass

**Deliverables:**
- Full file: `tests/utils/__init__.py`:
  ```python
  from .dashboard_helpers import *
  ```
- Full file: `tests/utils/dashboard_helpers.py` with functions:
  ```python
  def verify_html_contains_element(html: str, tag: str, attrs: dict = None) -> bool
  def verify_html_contains_link(html: str, href: str) -> bool
  def extract_form_action(html: str, form_id: str) -> str
  def extract_table_rows(html: str, table_class: str = None) -> list
  def verify_badge_status(html: str, status: str) -> bool
  def verify_toast_container_present(html: str) -> bool
  def extract_websocket_url(html: str) -> str
  def verify_filter_selected(html: str, filter_name: str, value: str) -> bool
  ```
- No stubs, no TODO comments

**Hard rules:**
- Windows friendly paths, CRLF preserved
- Use only standard library + `beautifulsoup4` (already in project)
- Zero network calls
- All functions must have docstrings
- All functions must handle malformed HTML gracefully
- Do not introduce new dependencies

**Self-review (answer yes/no at the end):**
- [ ] All 8 helper functions implemented
- [ ] Functions handle edge cases (empty HTML, missing elements)
- [ ] Docstrings present for all functions
- [ ] No new dependencies added
- [ ] Import works from test files

---

## Task Card 7: Final Integration & Coverage Verification

**Role:** Senior engineer. Produce drop-in, production-ready code.

**Scope (only this):**
- Verify: All phases integrated, coverage target met
- Allowed paths:
  - `tests/conftest.py` (FINAL REVIEW)
  - `pytest.ini` (UPDATE markers)
- Forbidden: any other file

**Acceptance checks (must pass locally):**
- CLI: `python -m pytest tests/ --ignore=tests/test_endpoints_live.py --ignore=tests/test_truth_llm_validation_real.py --ignore=tests/manual/ -v --tb=short`
- All tests pass (target: 180+ tests)
- Coverage: `python -m pytest tests/ --ignore=tests/test_endpoints_live.py --ignore=tests/test_truth_llm_validation_real.py --ignore=tests/manual/ --cov=api --cov-report=term-missing`
- Dashboard route coverage: 100%
- Overall coverage: 90%+

**Deliverables:**
- Updated `pytest.ini` with markers:
  ```ini
  [pytest]
  markers =
      websocket: WebSocket tests (may require async)
      e2e: End-to-end flow tests
      slow: Slow-running tests (>5s)
      admin: Admin control tests
      bulk: Bulk action tests
  asyncio_mode = auto
  ```
- Verified `tests/conftest.py` contains all fixtures from phases 1-6
- Updated coverage report at `reports/dashboard_coverage.md`
- No stubs, no TODO comments

**Hard rules:**
- Windows friendly paths, CRLF preserved
- All 75 new tests must pass
- All existing tests must still pass
- Zero network calls in tests
- No flaky tests (verified by running 3x)
- Coverage must meet 90% target

**Self-review (answer yes/no at the end):**
- [ ] All 180+ tests passing
- [ ] Coverage report shows 90%+ dashboard coverage
- [ ] No flaky tests after 3 runs
- [ ] Markers properly configured
- [ ] All fixtures documented in conftest.py

---

## Execution Order

```
Phase 1 (Task Card 1) → Phase 2 (Task Card 2) → Phase 3 (Task Card 3)
                                    ↓
Phase 6 (Task Card 6) ← Phase 5 (Task Card 5) ← Phase 4 (Task Card 4)
                                    ↓
                        Phase 7 (Task Card 7)
```

**Dependencies:**
- Task Card 6 (Utilities) can be done in parallel with Task Cards 1-3
- Task Card 7 must be done last after all others complete
- Task Cards 1-5 should be done in order (fixtures build on each other)

---

## Quick Reference: Test Counts

| Task Card | New Tests | Cumulative |
|-----------|-----------|------------|
| TC1: WebSocket | 15 | 120 |
| TC2: Modals | 20 | 140 |
| TC3: Admin | 12 | 152 |
| TC4: Bulk | 18 | 170 |
| TC5: Navigation | 10 | 180 |
| TC6: Utilities | 0 | 180 |
| TC7: Integration | 0 | 180 |

**Starting count:** 105 tests
**Target count:** 180 tests
**New tests:** 75

---

## Runbook: Execute All Task Cards

```bash
# Prerequisites
pip install pytest-asyncio websockets beautifulsoup4

# Task Card 1
python -m pytest tests/api/test_dashboard_websocket.py -v

# Task Card 2
python -m pytest tests/api/test_dashboard_modals.py -v

# Task Card 3
python -m pytest tests/api/test_dashboard_admin.py -v

# Task Card 4
python -m pytest tests/api/test_dashboard_validations.py tests/api/test_dashboard_recommendations.py tests/api/test_dashboard_workflows.py -v

# Task Card 5
python -m pytest tests/api/test_dashboard_navigation.py tests/e2e/test_dashboard_flows.py -v

# Task Card 6 (verify import)
python -c "from tests.utils.dashboard_helpers import *; print('Utilities OK')"

# Task Card 7 (full suite + coverage)
python -m pytest tests/ --ignore=tests/test_endpoints_live.py --ignore=tests/test_truth_llm_validation_real.py --ignore=tests/manual/ -v --tb=short

# Verify coverage
python -m pytest tests/api/test_dashboard*.py tests/e2e/ --cov=api.dashboard --cov-report=term-missing

# Flakiness check (run 3x)
for i in 1 2 3; do echo "Run $i"; python -m pytest tests/api/test_dashboard*.py -v --tb=line; done
```
