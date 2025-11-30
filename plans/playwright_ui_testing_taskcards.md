# Playwright UI Testing - Task Cards

**Reference:** [plans/playwright_ui_testing.md](playwright_ui_testing.md)

> **Status:** COMPLETE (2025-11-27)
> - Task Card 1: DONE (Setup & Dependencies)
> - Task Card 2: DONE (Base Infrastructure)
> - Task Card 3: DONE (Page Object Models - 8 files)
> - Task Card 4: DONE (Navigation Tests - 10 tests)
> - Task Card 5: DONE (Validation Flow Tests - 12 tests)
> - Task Card 6: DONE (Recommendation Flow Tests - 10 tests)
> - Task Card 7: DONE (Form & Modal Tests - 15 tests)
> - Task Card 8: DONE (Real-time/WebSocket Tests - 8 tests)
> - Task Card 9: DONE (Bulk Action Tests - 10 tests)
> - Task Card 10: DONE (CI/CD Integration)
> - Task Card 11: DONE (Documentation Update)
>
> **Total UI Tests:** 65 tests collected

---

## Task Card 1: Setup & Dependencies

**Status:** PENDING

**Role:** Senior engineer. Produce drop-in, production-ready code.

**Scope (only this):**
- Add: Playwright and pytest-playwright dependencies
- Update: pyproject.toml with new test dependencies
- Install: Playwright browsers
- Allowed paths:
  - `pyproject.toml` (EXTEND test dependencies)
  - `pytest.ini` (EXTEND with ui marker)
- Forbidden: any other file

**Acceptance checks (must pass locally):**
- CLI: `pip install -e ".[test]"` succeeds
- CLI: `playwright --version` shows installed version
- CLI: `python -c "from playwright.sync_api import sync_playwright; print('OK')"`
- CLI: `python -m pytest --co -q -m ui` shows 0 tests (no tests yet)
- Existing tests still pass

**Deliverables:**
- Updated `pyproject.toml` with dependencies:
  ```toml
  [project.optional-dependencies]
  test = [
      # ... existing deps
      "playwright>=1.40.0",
      "pytest-playwright>=0.4.0",
  ]
  ```
- Updated `pytest.ini` with marker:
  ```ini
  markers =
      # ... existing markers
      ui: UI/browser tests requiring Playwright
      ui_slow: Slow UI tests (visual regression, full flows)
  ```
- No stubs, no TODO comments

**Hard rules:**
- Windows friendly paths
- Do not modify any existing test code
- Do not break existing tests
- Use stable Playwright version (>=1.40.0)

**Self-review (answer yes/no at the end):**
- [ ] Playwright imports successfully
- [ ] pytest-playwright plugin loads
- [ ] Existing tests unaffected
- [ ] UI marker registered in pytest

---

## Task Card 2: Base Infrastructure & Fixtures

**Status:** PENDING

**Role:** Senior engineer. Produce drop-in, production-ready code.

**Scope (only this):**
- Create: UI test directory structure
- Create: Base Playwright fixtures and configuration
- Create: Server management fixtures for UI tests
- Allowed paths:
  - `tests/ui/__init__.py` (CREATE)
  - `tests/ui/conftest.py` (CREATE)
  - `tests/ui/pages/__init__.py` (CREATE)
- Forbidden: any other file

**Acceptance checks (must pass locally):**
- CLI: `python -c "from tests.ui.conftest import *; print('OK')"`
- CLI: `python -m pytest tests/ui/ --collect-only` shows fixtures available
- Server fixture starts and stops cleanly
- No orphan processes after test

**Deliverables:**
- Full file: `tests/ui/__init__.py` (empty, package marker)
- Full file: `tests/ui/pages/__init__.py`:
  ```python
  """Page Object Models for Playwright UI tests."""
  ```
- Full file: `tests/ui/conftest.py` with fixtures:
  ```python
  import pytest
  import subprocess
  import time
  import socket
  from contextlib import closing
  from playwright.sync_api import Page, BrowserContext

  def find_free_port():
      """Find a free port for the test server."""
      with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
          s.bind(('', 0))
          s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
          return s.getsockname()[1]

  @pytest.fixture(scope="session")
  def browser_context_args():
      """Configure browser context for UI tests."""
      return {
          "viewport": {"width": 1920, "height": 1080},
          "ignore_https_errors": True,
      }

  @pytest.fixture(scope="session")
  def test_server_port():
      """Get a free port for the test server."""
      return find_free_port()

  @pytest.fixture(scope="session")
  def live_server(test_server_port):
      """Start FastAPI server for UI tests."""
      import sys
      proc = subprocess.Popen(
          [sys.executable, "-m", "uvicorn", "api.server:app",
           "--host", "127.0.0.1", "--port", str(test_server_port)],
          stdout=subprocess.PIPE,
          stderr=subprocess.PIPE,
      )
      # Wait for server to be ready
      max_wait = 10
      for _ in range(max_wait * 10):
          try:
              with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
                  s.connect(("127.0.0.1", test_server_port))
                  break
          except ConnectionRefusedError:
              time.sleep(0.1)
      yield {"port": test_server_port, "process": proc}
      proc.terminate()
      proc.wait(timeout=5)

  @pytest.fixture
  def base_url(live_server):
      """Base URL for the test server."""
      return f"http://127.0.0.1:{live_server['port']}"

  @pytest.fixture
  def dashboard_url(base_url):
      """Dashboard base URL."""
      return f"{base_url}/dashboard"
  ```
- No stubs, no TODO comments

**Hard rules:**
- Windows friendly paths, handle subprocess on Windows
- Server must start reliably (with retry logic)
- Server must terminate cleanly (no orphan processes)
- Use session scope for server (start once per test session)
- Port must be dynamically allocated to avoid conflicts

**Self-review (answer yes/no at the end):**
- [ ] Server fixture starts successfully
- [ ] Server fixture terminates cleanly
- [ ] No port conflicts with other services
- [ ] Fixtures importable from test files
- [ ] Works on Windows

---

## Task Card 3: Page Object Models

**Status:** PENDING

**Role:** Senior engineer. Produce drop-in, production-ready code.

**Scope (only this):**
- Create: Base page class with common functionality
- Create: Page Object Models for all 7 dashboard pages
- Allowed paths:
  - `tests/ui/pages/base_page.py` (CREATE)
  - `tests/ui/pages/dashboard_home.py` (CREATE)
  - `tests/ui/pages/validations_page.py` (CREATE)
  - `tests/ui/pages/validation_detail.py` (CREATE)
  - `tests/ui/pages/recommendations_page.py` (CREATE)
  - `tests/ui/pages/recommendation_detail.py` (CREATE)
  - `tests/ui/pages/workflows_page.py` (CREATE)
  - `tests/ui/pages/workflow_detail.py` (CREATE)
  - `tests/ui/pages/__init__.py` (EXTEND exports)
- Forbidden: any other file

**Acceptance checks (must pass locally):**
- CLI: `python -c "from tests.ui.pages import *; print('OK')"`
- All page classes importable
- No syntax errors
- Type hints present on all public methods

**Deliverables:**
- Full file: `tests/ui/pages/base_page.py`:
  ```python
  """Base page class for all Page Object Models."""
  from playwright.sync_api import Page, Locator, expect

  class BasePage:
      """Base class with common page functionality."""

      URL_PATH: str = "/"

      def __init__(self, page: Page, base_url: str):
          self.page = page
          self.base_url = base_url

      def navigate(self) -> "BasePage":
          """Navigate to this page."""
          self.page.goto(f"{self.base_url}{self.URL_PATH}")
          self.page.wait_for_load_state("networkidle")
          return self

      @property
      def header(self) -> Locator:
          """Header element."""
          return self.page.locator("header")

      @property
      def nav_links(self) -> Locator:
          """Navigation links in header."""
          return self.header.get_by_role("link")

      def click_nav_link(self, name: str) -> None:
          """Click a navigation link by name."""
          self.page.get_by_role("link", name=name).click()
          self.page.wait_for_load_state("networkidle")

      def get_page_title(self) -> str:
          """Get the page title."""
          return self.page.title()

      def has_text(self, text: str) -> bool:
          """Check if page contains text."""
          return self.page.get_by_text(text).is_visible()

      def wait_for_text(self, text: str, timeout: int = 5000) -> None:
          """Wait for text to appear on page."""
          self.page.get_by_text(text).wait_for(state="visible", timeout=timeout)
  ```
- Full file: `tests/ui/pages/dashboard_home.py`:
  ```python
  """Dashboard home page object model."""
  from playwright.sync_api import Locator, expect
  from .base_page import BasePage

  class DashboardHome(BasePage):
      """Dashboard home page with metrics and activity feed."""

      URL_PATH = "/dashboard/"

      @property
      def metrics_grid(self) -> Locator:
          """Metrics grid container."""
          return self.page.locator(".metrics, .stats, [class*='metric']").first

      @property
      def total_validations(self) -> Locator:
          """Total validations metric."""
          return self.page.locator("text=Total").locator("..").locator("text=/\\d+/")

      @property
      def activity_feed(self) -> Locator:
          """Activity feed container."""
          return self.page.locator(".activity, [class*='activity'], [class*='feed']").first

      @property
      def websocket_status(self) -> Locator:
          """WebSocket connection status indicator."""
          return self.page.locator("[class*='status'], [class*='connection']").first

      @property
      def recent_validations_table(self) -> Locator:
          """Recent validations table."""
          return self.page.locator("table").first

      @property
      def view_all_validations_link(self) -> Locator:
          """View all validations link."""
          return self.page.get_by_role("link", name="View All").first

      def wait_for_metrics_loaded(self, timeout: int = 5000) -> None:
          """Wait for metrics to load."""
          self.page.wait_for_load_state("networkidle", timeout=timeout)

      def get_metric_value(self, metric_name: str) -> str:
          """Get value of a specific metric."""
          metric = self.page.locator(f"text={metric_name}").locator("..")
          return metric.locator("text=/\\d+/").first.inner_text()
  ```
- Full file: `tests/ui/pages/validations_page.py`:
  ```python
  """Validations list page object model."""
  from playwright.sync_api import Locator, expect
  from .base_page import BasePage

  class ValidationsPage(BasePage):
      """Validations list page with filtering and pagination."""

      URL_PATH = "/dashboard/validations"

      @property
      def status_filter(self) -> Locator:
          """Status filter dropdown."""
          return self.page.locator("select[name='status'], select[id*='status']").first

      @property
      def severity_filter(self) -> Locator:
          """Severity filter dropdown."""
          return self.page.locator("select[name='severity'], select[id*='severity']").first

      @property
      def validations_table(self) -> Locator:
          """Validations table."""
          return self.page.locator("table").first

      @property
      def table_rows(self) -> Locator:
          """Table body rows."""
          return self.validations_table.locator("tbody tr")

      @property
      def run_validation_button(self) -> Locator:
          """Run validation button."""
          return self.page.get_by_role("button", name="Run Validation")

      @property
      def run_validation_modal(self) -> Locator:
          """Run validation modal dialog."""
          return self.page.locator(".modal, [role='dialog']").first

      @property
      def pagination(self) -> Locator:
          """Pagination controls."""
          return self.page.locator(".pagination, [class*='pag']").first

      def filter_by_status(self, status: str) -> None:
          """Filter validations by status."""
          self.status_filter.select_option(status)
          self.page.wait_for_load_state("networkidle")

      def filter_by_severity(self, severity: str) -> None:
          """Filter validations by severity."""
          self.severity_filter.select_option(severity)
          self.page.wait_for_load_state("networkidle")

      def get_row_count(self) -> int:
          """Get number of validation rows."""
          return self.table_rows.count()

      def click_view_button(self, row_index: int = 0) -> None:
          """Click view button on a row."""
          self.table_rows.nth(row_index).get_by_role("link", name="View").click()

      def open_run_validation_modal(self) -> None:
          """Open the run validation modal."""
          self.run_validation_button.click()
          expect(self.run_validation_modal).to_be_visible()

      def go_to_page(self, page_num: int) -> None:
          """Navigate to a specific page."""
          self.pagination.get_by_role("link", name=str(page_num)).click()
          self.page.wait_for_load_state("networkidle")
  ```
- Full file: `tests/ui/pages/validation_detail.py`:
  ```python
  """Validation detail page object model."""
  from playwright.sync_api import Locator, expect
  from .base_page import BasePage

  class ValidationDetailPage(BasePage):
      """Validation detail page with approve/reject/enhance actions."""

      URL_PATH = "/dashboard/validations/{id}"

      def navigate_to(self, validation_id: int) -> "ValidationDetailPage":
          """Navigate to a specific validation."""
          self.page.goto(f"{self.base_url}/dashboard/validations/{validation_id}")
          self.page.wait_for_load_state("networkidle")
          return self

      @property
      def status_badge(self) -> Locator:
          """Status badge element."""
          return self.page.locator(".badge, .status, [class*='badge']").first

      @property
      def approve_button(self) -> Locator:
          """Approve button."""
          return self.page.get_by_role("button", name="Approve")

      @property
      def reject_button(self) -> Locator:
          """Reject button."""
          return self.page.get_by_role("button", name="Reject")

      @property
      def enhance_button(self) -> Locator:
          """Enhance button."""
          return self.page.get_by_role("button", name="Enhance")

      @property
      def recommendations_table(self) -> Locator:
          """Recommendations table."""
          return self.page.locator("table").first

      @property
      def recommendation_checkboxes(self) -> Locator:
          """Recommendation selection checkboxes."""
          return self.page.locator("input[type='checkbox']")

      @property
      def enhance_selected_button(self) -> Locator:
          """Enhance selected recommendations button."""
          return self.page.get_by_role("button", name="Enhance Selected")

      @property
      def generate_recommendations_button(self) -> Locator:
          """Generate recommendations button."""
          return self.page.get_by_role("button", name="Generate")

      def approve_validation(self) -> None:
          """Approve the validation."""
          self.approve_button.click()
          self.page.wait_for_load_state("networkidle")

      def reject_validation(self) -> None:
          """Reject the validation."""
          self.reject_button.click()
          self.page.wait_for_load_state("networkidle")

      def select_recommendation(self, index: int) -> None:
          """Select a recommendation by index."""
          self.recommendation_checkboxes.nth(index).check()

      def select_recommendations(self, indices: list) -> None:
          """Select multiple recommendations."""
          for i in indices:
              self.select_recommendation(i)

      def enhance_selected(self) -> None:
          """Enhance selected recommendations."""
          self.enhance_selected_button.click()
          self.page.wait_for_load_state("networkidle")

      def get_status(self) -> str:
          """Get current validation status."""
          return self.status_badge.inner_text()
  ```
- Full file: `tests/ui/pages/recommendations_page.py`:
  ```python
  """Recommendations list page object model."""
  from playwright.sync_api import Locator, expect
  from .base_page import BasePage

  class RecommendationsPage(BasePage):
      """Recommendations list page with filtering and bulk actions."""

      URL_PATH = "/dashboard/recommendations"

      @property
      def status_filter(self) -> Locator:
          """Status filter dropdown."""
          return self.page.locator("select[name='status'], select[id*='status']").first

      @property
      def type_filter(self) -> Locator:
          """Type filter dropdown."""
          return self.page.locator("select[name='type'], select[id*='type']").first

      @property
      def recommendations_table(self) -> Locator:
          """Recommendations table."""
          return self.page.locator("table").first

      @property
      def table_rows(self) -> Locator:
          """Table body rows."""
          return self.recommendations_table.locator("tbody tr")

      @property
      def checkboxes(self) -> Locator:
          """Row selection checkboxes."""
          return self.page.locator("input[type='checkbox']")

      @property
      def select_all_checkbox(self) -> Locator:
          """Select all checkbox."""
          return self.page.locator("thead input[type='checkbox']").first

      @property
      def bulk_approve_button(self) -> Locator:
          """Bulk approve button."""
          return self.page.get_by_role("button", name="Approve")

      @property
      def bulk_reject_button(self) -> Locator:
          """Bulk reject button."""
          return self.page.get_by_role("button", name="Reject")

      def filter_by_status(self, status: str) -> None:
          """Filter by status."""
          self.status_filter.select_option(status)
          self.page.wait_for_load_state("networkidle")

      def filter_by_type(self, rec_type: str) -> None:
          """Filter by recommendation type."""
          self.type_filter.select_option(rec_type)
          self.page.wait_for_load_state("networkidle")

      def select_row(self, index: int) -> None:
          """Select a row by index."""
          self.table_rows.nth(index).locator("input[type='checkbox']").check()

      def select_all(self) -> None:
          """Select all rows."""
          self.select_all_checkbox.check()

      def bulk_approve(self) -> None:
          """Bulk approve selected."""
          self.bulk_approve_button.click()
          self.page.wait_for_load_state("networkidle")

      def bulk_reject(self) -> None:
          """Bulk reject selected."""
          self.bulk_reject_button.click()
          self.page.wait_for_load_state("networkidle")

      def click_view_button(self, row_index: int = 0) -> None:
          """Click view button on a row."""
          self.table_rows.nth(row_index).get_by_role("link", name="View").click()
  ```
- Full file: `tests/ui/pages/recommendation_detail.py`:
  ```python
  """Recommendation detail page object model."""
  from playwright.sync_api import Locator, expect
  from .base_page import BasePage

  class RecommendationDetailPage(BasePage):
      """Recommendation detail page with review form."""

      URL_PATH = "/dashboard/recommendations/{id}"

      def navigate_to(self, recommendation_id: int) -> "RecommendationDetailPage":
          """Navigate to a specific recommendation."""
          self.page.goto(f"{self.base_url}/dashboard/recommendations/{recommendation_id}")
          self.page.wait_for_load_state("networkidle")
          return self

      @property
      def status_badge(self) -> Locator:
          """Status badge."""
          return self.page.locator(".badge, .status, [class*='badge']").first

      @property
      def source_context(self) -> Locator:
          """Source file context viewer."""
          return self.page.locator("pre, code, [class*='source']").first

      @property
      def related_recommendations(self) -> Locator:
          """Related recommendations section."""
          return self.page.locator("[class*='related']").first

      @property
      def review_form(self) -> Locator:
          """Review form."""
          return self.page.locator("form").first

      @property
      def approve_radio(self) -> Locator:
          """Approve radio button."""
          return self.page.get_by_label("Approve")

      @property
      def reject_radio(self) -> Locator:
          """Reject radio button."""
          return self.page.get_by_label("Reject")

      @property
      def notes_field(self) -> Locator:
          """Notes textarea."""
          return self.page.locator("textarea[name='notes'], textarea[id*='notes']").first

      @property
      def submit_button(self) -> Locator:
          """Submit review button."""
          return self.page.get_by_role("button", name="Submit")

      def approve_recommendation(self, notes: str = "") -> None:
          """Approve the recommendation."""
          self.approve_radio.check()
          if notes:
              self.notes_field.fill(notes)
          self.submit_button.click()
          self.page.wait_for_load_state("networkidle")

      def reject_recommendation(self, notes: str = "") -> None:
          """Reject the recommendation."""
          self.reject_radio.check()
          if notes:
              self.notes_field.fill(notes)
          self.submit_button.click()
          self.page.wait_for_load_state("networkidle")

      def get_status(self) -> str:
          """Get current status."""
          return self.status_badge.inner_text()
  ```
- Full file: `tests/ui/pages/workflows_page.py`:
  ```python
  """Workflows list page object model."""
  from playwright.sync_api import Locator, expect
  from .base_page import BasePage

  class WorkflowsPage(BasePage):
      """Workflows list page with state filtering."""

      URL_PATH = "/dashboard/workflows"

      @property
      def state_filter(self) -> Locator:
          """State filter dropdown."""
          return self.page.locator("select[name='state'], select[id*='state']").first

      @property
      def workflows_table(self) -> Locator:
          """Workflows table."""
          return self.page.locator("table").first

      @property
      def table_rows(self) -> Locator:
          """Table body rows."""
          return self.workflows_table.locator("tbody tr")

      @property
      def run_workflow_button(self) -> Locator:
          """Run workflow button."""
          return self.page.get_by_role("button", name="Run Workflow")

      @property
      def run_workflow_modal(self) -> Locator:
          """Run workflow modal."""
          return self.page.locator(".modal, [role='dialog']").first

      def filter_by_state(self, state: str) -> None:
          """Filter by workflow state."""
          self.state_filter.select_option(state)
          self.page.wait_for_load_state("networkidle")

      def get_row_count(self) -> int:
          """Get number of workflow rows."""
          return self.table_rows.count()

      def click_view_button(self, row_index: int = 0) -> None:
          """Click view button on a row."""
          self.table_rows.nth(row_index).get_by_role("link", name="View").click()

      def open_run_workflow_modal(self) -> None:
          """Open run workflow modal."""
          self.run_workflow_button.click()
          expect(self.run_workflow_modal).to_be_visible()
  ```
- Full file: `tests/ui/pages/workflow_detail.py`:
  ```python
  """Workflow detail page object model."""
  from playwright.sync_api import Locator, expect
  from .base_page import BasePage

  class WorkflowDetailPage(BasePage):
      """Workflow detail page with real-time progress."""

      URL_PATH = "/dashboard/workflows/{id}"

      def navigate_to(self, workflow_id: int) -> "WorkflowDetailPage":
          """Navigate to a specific workflow."""
          self.page.goto(f"{self.base_url}/dashboard/workflows/{workflow_id}")
          self.page.wait_for_load_state("networkidle")
          return self

      @property
      def status_badge(self) -> Locator:
          """Status badge."""
          return self.page.locator(".badge, .status, [class*='badge']").first

      @property
      def progress_bar(self) -> Locator:
          """Progress bar element."""
          return self.page.locator("[role='progressbar'], .progress, [class*='progress']").first

      @property
      def websocket_status(self) -> Locator:
          """WebSocket connection status."""
          return self.page.locator("[class*='status'], [class*='connection']").first

      @property
      def validations_table(self) -> Locator:
          """Included validations table."""
          return self.page.locator("table").first

      @property
      def control_buttons(self) -> Locator:
          """Workflow control buttons (pause/resume/cancel)."""
          return self.page.locator("button[class*='control'], button[class*='action']")

      def get_progress_value(self) -> int:
          """Get current progress percentage."""
          aria_value = self.progress_bar.get_attribute("aria-valuenow")
          if aria_value:
              return int(aria_value)
          # Fallback: parse from style or text
          return 0

      def get_status(self) -> str:
          """Get current workflow status."""
          return self.status_badge.inner_text()

      def wait_for_progress_change(self, initial_value: int, timeout: int = 10000) -> None:
          """Wait for progress to change from initial value."""
          self.page.wait_for_function(
              f"() => document.querySelector('[role=\"progressbar\"]')?.getAttribute('aria-valuenow') != '{initial_value}'",
              timeout=timeout
          )
  ```
- Updated `tests/ui/pages/__init__.py`:
  ```python
  """Page Object Models for Playwright UI tests."""
  from .base_page import BasePage
  from .dashboard_home import DashboardHome
  from .validations_page import ValidationsPage
  from .validation_detail import ValidationDetailPage
  from .recommendations_page import RecommendationsPage
  from .recommendation_detail import RecommendationDetailPage
  from .workflows_page import WorkflowsPage
  from .workflow_detail import WorkflowDetailPage

  __all__ = [
      "BasePage",
      "DashboardHome",
      "ValidationsPage",
      "ValidationDetailPage",
      "RecommendationsPage",
      "RecommendationDetailPage",
      "WorkflowsPage",
      "WorkflowDetailPage",
  ]
  ```
- No stubs, no TODO comments

**Hard rules:**
- Windows friendly paths
- All page classes must inherit from BasePage
- Type hints on all public methods
- Docstrings on all classes and public methods
- Use flexible locators (multiple selectors with fallbacks)
- No hardcoded URLs - use base_url parameter

**Self-review (answer yes/no at the end):**
- [ ] All 8 page classes created
- [ ] All classes importable from package
- [ ] Docstrings present
- [ ] Type hints present
- [ ] Locators use flexible selectors

---

## Task Card 4: Navigation Tests

**Status:** PENDING

**Role:** Senior engineer. Produce drop-in, production-ready code.

**Scope (only this):**
- Create: Navigation test suite
- Test: Header links, pagination, view buttons, breadcrumbs
- Allowed paths:
  - `tests/ui/test_navigation.py` (CREATE)
  - `tests/ui/conftest.py` (EXTEND with page fixtures)
- Forbidden: any other file

**Acceptance checks (must pass locally):**
- CLI: `python -m pytest tests/ui/test_navigation.py -v --headed` (visual check)
- CLI: `python -m pytest tests/ui/test_navigation.py -v` (headless)
- All 10 tests pass
- Tests complete in under 60 seconds total

**Deliverables:**
- Full file: `tests/ui/test_navigation.py`:
  ```
  TestHeaderNavigation (5 tests):
  - test_home_link_navigates_to_dashboard
  - test_validations_link_works
  - test_recommendations_link_works
  - test_workflows_link_works
  - test_header_links_visible_on_all_pages

  TestPageNavigation (3 tests):
  - test_validation_view_opens_detail
  - test_recommendation_view_opens_detail
  - test_workflow_view_opens_detail

  TestPagination (2 tests):
  - test_pagination_next_page
  - test_pagination_maintains_filters
  ```
- Extended `tests/ui/conftest.py` with fixtures:
  ```python
  @pytest.fixture
  def dashboard_home(page: Page, dashboard_url: str) -> DashboardHome:
      return DashboardHome(page, dashboard_url.replace("/dashboard", ""))

  @pytest.fixture
  def validations_page(page: Page, dashboard_url: str) -> ValidationsPage:
      return ValidationsPage(page, dashboard_url.replace("/dashboard", ""))

  # ... similar for other pages
  ```
- No stubs, no TODO comments

**Hard rules:**
- Windows friendly paths
- Tests must be independent (can run in any order)
- Use `@pytest.mark.ui` on all test classes
- Each test must clean up browser state
- No flaky waits - use proper Playwright wait methods

**Self-review (answer yes/no at the end):**
- [ ] All 10 tests implemented and passing
- [ ] Tests run headless successfully
- [ ] No flaky tests (run 3x)
- [ ] Page fixtures properly configured
- [ ] Tests complete within timeout

---

## Task Card 5: Validation Flow Tests

**Status:** PENDING

**Role:** Senior engineer. Produce drop-in, production-ready code.

**Scope (only this):**
- Create: Validation workflow test suite
- Test: List view, filtering, detail view, approve/reject/enhance
- Allowed paths:
  - `tests/ui/test_validations_flow.py` (CREATE)
  - `tests/ui/conftest.py` (EXTEND with data fixtures)
- Forbidden: any other file

**Acceptance checks (must pass locally):**
- CLI: `python -m pytest tests/ui/test_validations_flow.py -v`
- All 12 tests pass
- Tests complete in under 90 seconds total

**Deliverables:**
- Full file: `tests/ui/test_validations_flow.py`:
  ```
  TestValidationsList (4 tests):
  - test_list_displays_validations
  - test_filter_by_status_pass
  - test_filter_by_status_fail
  - test_filter_by_severity_high

  TestValidationDetail (5 tests):
  - test_detail_shows_validation_info
  - test_detail_shows_recommendations
  - test_approve_validation_updates_status
  - test_reject_validation_updates_status
  - test_status_badge_reflects_state

  TestValidationEnhancement (3 tests):
  - test_select_recommendations_checkbox
  - test_enhance_selected_recommendations
  - test_enhance_button_disabled_when_not_approved
  ```
- Extended `tests/ui/conftest.py` with data fixtures:
  ```python
  @pytest.fixture
  def seeded_validation(db_manager, mock_file_system):
      """Create a validation for UI tests."""
      return db_manager.create_validation_result(
          file_path=str(mock_file_system / "test.md"),
          status="fail",
          severity="high",
          # ...
      )

  @pytest.fixture
  def approved_validation(seeded_validation, db_manager):
      """Approved validation with recommendations."""
      db_manager.update_validation_status(seeded_validation.id, "approved")
      # Create recommendations
      return seeded_validation
  ```
- No stubs, no TODO comments

**Hard rules:**
- Windows friendly paths
- Use `@pytest.mark.ui` on all test classes
- Tests must seed their own data (use fixtures)
- Tests must not depend on pre-existing database state
- Use explicit waits for status changes

**Self-review (answer yes/no at the end):**
- [ ] All 12 tests implemented and passing
- [ ] Filter tests verify correct filtering
- [ ] Status change tests verify UI updates
- [ ] Data fixtures properly seed database
- [ ] Tests are isolated

---

## Task Card 6: Recommendation Flow Tests

**Status:** PENDING

**Role:** Senior engineer. Produce drop-in, production-ready code.

**Scope (only this):**
- Create: Recommendation workflow test suite
- Test: List view, filtering, detail view, review form
- Allowed paths:
  - `tests/ui/test_recommendations_flow.py` (CREATE)
  - `tests/ui/conftest.py` (EXTEND if needed)
- Forbidden: any other file

**Acceptance checks (must pass locally):**
- CLI: `python -m pytest tests/ui/test_recommendations_flow.py -v`
- All 10 tests pass
- Tests complete in under 60 seconds total

**Deliverables:**
- Full file: `tests/ui/test_recommendations_flow.py`:
  ```
  TestRecommendationsList (4 tests):
  - test_list_displays_recommendations
  - test_filter_by_status_pending
  - test_filter_by_type
  - test_combined_filters

  TestRecommendationDetail (4 tests):
  - test_detail_shows_recommendation_info
  - test_source_context_displays
  - test_review_form_visible
  - test_related_recommendations_section

  TestRecommendationReview (2 tests):
  - test_approve_recommendation_via_form
  - test_reject_recommendation_with_notes
  ```
- No stubs, no TODO comments

**Hard rules:**
- Windows friendly paths
- Use `@pytest.mark.ui` on all test classes
- Tests must seed recommendations via fixtures
- Form submission tests must verify status change
- Tests must be independent

**Self-review (answer yes/no at the end):**
- [ ] All 10 tests implemented and passing
- [ ] Filter tests work correctly
- [ ] Review form tests verify submission
- [ ] Source context test verifies display
- [ ] Tests are isolated

---

## Task Card 7: Form & Modal Tests

**Status:** PENDING

**Role:** Senior engineer. Produce drop-in, production-ready code.

**Scope (only this):**
- Create: Form and modal interaction test suite
- Test: Run Validation modal, Run Workflow modal, form inputs
- Allowed paths:
  - `tests/ui/test_forms_modals.py` (CREATE)
- Forbidden: any other file

**Acceptance checks (must pass locally):**
- CLI: `python -m pytest tests/ui/test_forms_modals.py -v`
- All 15 tests pass
- Tests complete in under 90 seconds total

**Deliverables:**
- Full file: `tests/ui/test_forms_modals.py`:
  ```
  TestRunValidationModal (6 tests):
  - test_modal_opens_on_button_click
  - test_modal_closes_on_escape
  - test_modal_closes_on_backdrop_click
  - test_single_file_mode_form_fields
  - test_batch_mode_form_fields
  - test_form_submission_triggers_validation

  TestRunWorkflowModal (5 tests):
  - test_workflow_modal_opens
  - test_directory_mode_form
  - test_batch_mode_form
  - test_family_dropdown_options
  - test_validation_type_checkboxes

  TestFormValidation (4 tests):
  - test_required_fields_validation
  - test_file_path_format_validation
  - test_form_preserves_input_on_error
  - test_form_clears_on_success
  ```
- No stubs, no TODO comments

**Hard rules:**
- Windows friendly paths
- Use `@pytest.mark.ui` on all test classes
- Modal tests must verify open/close behavior
- Form tests must verify field presence and behavior
- Use keyboard events for ESC key tests

**Self-review (answer yes/no at the end):**
- [ ] All 15 tests implemented and passing
- [ ] Modal open/close tests work
- [ ] Form field tests verify inputs
- [ ] Keyboard interaction tests work
- [ ] Tests are isolated

---

## Task Card 8: Real-time/WebSocket Tests

**Status:** PENDING

**Role:** Senior engineer. Produce drop-in, production-ready code.

**Scope (only this):**
- Create: WebSocket and real-time update test suite
- Test: Connection status, activity feed, progress updates
- Allowed paths:
  - `tests/ui/test_realtime_updates.py` (CREATE)
  - `tests/ui/conftest.py` (EXTEND with WebSocket helpers)
- Forbidden: any other file

**Acceptance checks (must pass locally):**
- CLI: `python -m pytest tests/ui/test_realtime_updates.py -v`
- All 8 tests pass
- Tests complete in under 120 seconds total (WebSocket tests are slower)

**Deliverables:**
- Full file: `tests/ui/test_realtime_updates.py`:
  ```
  TestWebSocketConnection (3 tests):
  - test_dashboard_shows_connection_status
  - test_workflow_detail_shows_connection_status
  - test_connection_recovers_after_disconnect

  TestActivityFeed (3 tests):
  - test_activity_feed_visible_on_home
  - test_activity_feed_updates_on_event
  - test_activity_feed_shows_recent_items

  TestProgressUpdates (2 tests):
  - test_workflow_progress_bar_visible
  - test_progress_updates_during_workflow
  ```
- Extended `tests/ui/conftest.py`:
  ```python
  @pytest.fixture
  def trigger_validation_event(base_url):
      """Helper to trigger a validation event via API."""
      import httpx
      def _trigger(file_path: str = "/test/file.md"):
          httpx.post(f"{base_url}/api/validate", json={
              "file_path": file_path,
              "content": "# Test",
              "family": "Words",
          })
      return _trigger
  ```
- No stubs, no TODO comments

**Hard rules:**
- Windows friendly paths
- Use `@pytest.mark.ui` on all test classes
- Use longer timeouts for WebSocket tests (10-15 seconds)
- Activity feed tests may need to trigger events via API
- Handle WebSocket connection timing carefully

**Self-review (answer yes/no at the end):**
- [ ] All 8 tests implemented and passing
- [ ] WebSocket connection tests reliable
- [ ] Activity feed update tests work
- [ ] Progress update tests handle timing
- [ ] Tests are not flaky (run 3x)

---

## Task Card 9: Bulk Action Tests

**Status:** PENDING

**Role:** Senior engineer. Produce drop-in, production-ready code.

**Scope (only this):**
- Create: Bulk action test suite
- Test: Multi-select, bulk approve/reject, select all
- Allowed paths:
  - `tests/ui/test_bulk_actions.py` (CREATE)
  - `tests/ui/conftest.py` (EXTEND with bulk data fixtures)
- Forbidden: any other file

**Acceptance checks (must pass locally):**
- CLI: `python -m pytest tests/ui/test_bulk_actions.py -v`
- All 10 tests pass
- Tests complete in under 60 seconds total

**Deliverables:**
- Full file: `tests/ui/test_bulk_actions.py`:
  ```
  TestCheckboxSelection (4 tests):
  - test_select_single_checkbox
  - test_select_multiple_checkboxes
  - test_select_all_checkbox
  - test_deselect_clears_selection

  TestBulkRecommendationActions (4 tests):
  - test_bulk_approve_selected
  - test_bulk_reject_selected
  - test_bulk_action_updates_status
  - test_bulk_action_with_no_selection_disabled

  TestBulkValidationActions (2 tests):
  - test_select_recommendations_for_enhance
  - test_bulk_enhance_selected
  ```
- Extended `tests/ui/conftest.py`:
  ```python
  @pytest.fixture
  def multiple_recommendations(db_manager, seeded_validation):
      """Create multiple recommendations for bulk tests."""
      recs = []
      for i in range(5):
          rec = db_manager.create_recommendation(
              validation_id=seeded_validation.id,
              title=f"Recommendation {i}",
              status="pending",
          )
          recs.append(rec)
      return recs
  ```
- No stubs, no TODO comments

**Hard rules:**
- Windows friendly paths
- Use `@pytest.mark.ui` on all test classes
- Create minimum 5 items for bulk tests
- Verify count of selected items matches action result
- Tests must clean up created data

**Self-review (answer yes/no at the end):**
- [ ] All 10 tests implemented and passing
- [ ] Checkbox tests verify selection state
- [ ] Bulk action tests verify status changes
- [ ] Multiple items created for testing
- [ ] Tests are isolated

---

## Task Card 10: CI/CD Integration

**Status:** PENDING

**Role:** Senior engineer. Produce drop-in, production-ready code.

**Scope (only this):**
- Create: GitHub Actions workflow for UI tests
- Create: Local test runner script
- Update: pytest configuration
- Allowed paths:
  - `.github/workflows/ui-tests.yml` (CREATE)
  - `scripts/run_ui_tests.sh` (CREATE)
  - `scripts/run_ui_tests.bat` (CREATE - Windows)
  - `pytest.ini` (EXTEND)
- Forbidden: any other file

**Acceptance checks (must pass locally):**
- CLI (Windows): `scripts\run_ui_tests.bat` runs successfully
- CLI (Unix): `./scripts/run_ui_tests.sh` runs successfully
- GitHub workflow syntax is valid
- UI tests can be run independently with `pytest -m ui`

**Deliverables:**
- Full file: `.github/workflows/ui-tests.yml`:
  ```yaml
  name: UI Tests

  on:
    push:
      branches: [main]
    pull_request:
      branches: [main]

  jobs:
    ui-tests:
      runs-on: ubuntu-latest
      timeout-minutes: 15

      steps:
        - uses: actions/checkout@v4

        - name: Set up Python
          uses: actions/setup-python@v5
          with:
            python-version: '3.11'

        - name: Install dependencies
          run: |
            pip install -e ".[test]"
            playwright install chromium --with-deps

        - name: Run UI tests
          run: |
            pytest tests/ui/ -v --browser chromium --screenshot=only-on-failure

        - name: Upload screenshots on failure
          uses: actions/upload-artifact@v4
          if: failure()
          with:
            name: playwright-screenshots
            path: test-results/
            retention-days: 7
  ```
- Full file: `scripts/run_ui_tests.sh`:
  ```bash
  #!/bin/bash
  set -e

  echo "Installing Playwright browsers..."
  playwright install chromium

  echo "Running UI tests..."
  pytest tests/ui/ -v --browser chromium "$@"

  echo "UI tests completed."
  ```
- Full file: `scripts/run_ui_tests.bat`:
  ```batch
  @echo off
  echo Installing Playwright browsers...
  playwright install chromium

  echo Running UI tests...
  pytest tests/ui/ -v --browser chromium %*

  echo UI tests completed.
  ```
- Updated `pytest.ini`:
  ```ini
  [pytest]
  markers =
      ui: UI/browser tests requiring Playwright
      ui_slow: Slow UI tests (visual regression, full flows)
  ```
- No stubs, no TODO comments

**Hard rules:**
- Windows friendly paths and scripts
- GitHub workflow must use ubuntu-latest
- Scripts must handle errors gracefully
- Playwright must be installed in CI
- Screenshots uploaded only on failure

**Self-review (answer yes/no at the end):**
- [ ] GitHub workflow syntax valid
- [ ] Windows script works
- [ ] Unix script works
- [ ] pytest markers configured
- [ ] CI uploads artifacts on failure

---

## Task Card 11: Documentation Update

**Status:** PENDING

**Role:** Senior engineer. Produce drop-in, production-ready code.

**Scope (only this):**
- Update: Test documentation with UI testing guide
- Update: README with UI test instructions
- Create: UI testing report
- Allowed paths:
  - `tests/README.md` (EXTEND)
  - `reports/playwright_ui_testing.md` (CREATE)
  - `docs/testing/UI_TESTING_GUIDE.md` (CREATE)
- Forbidden: any other file

**Acceptance checks (must pass locally):**
- All documentation files exist and are well-formatted
- Instructions are accurate and can be followed
- Links are valid

**Deliverables:**
- Extended `tests/README.md` with section:
  ```markdown
  ## UI Tests (Playwright)

  Browser-based UI tests using Playwright to simulate user behavior.

  ### Setup
  ```bash
  pip install -e ".[test]"
  playwright install chromium
  ```

  ### Running UI Tests
  ```bash
  # Run all UI tests
  pytest tests/ui/ -v

  # Run with visible browser
  pytest tests/ui/ -v --headed

  # Run specific test file
  pytest tests/ui/test_navigation.py -v

  # Run with screenshots on failure
  pytest tests/ui/ -v --screenshot=only-on-failure
  ```

  ### UI Test Structure
  - `tests/ui/pages/` - Page Object Models
  - `tests/ui/test_*.py` - Test suites
  - `tests/ui/conftest.py` - Fixtures
  ```
- Full file: `reports/playwright_ui_testing.md`:
  ```markdown
  # Playwright UI Testing Implementation Report

  **Date:** [Current Date]
  **Status:** COMPLETE

  ## Summary
  Implemented browser-based UI testing using Playwright...

  ## Test Coverage
  | Test Suite | Tests | Status |
  |------------|-------|--------|
  | Navigation | 10 | Pass |
  | Validations | 12 | Pass |
  | Recommendations | 10 | Pass |
  | Forms/Modals | 15 | Pass |
  | Real-time | 8 | Pass |
  | Bulk Actions | 10 | Pass |
  | **Total** | **65** | **Pass** |

  ## Pages Covered
  - Dashboard Home
  - Validations List/Detail
  - Recommendations List/Detail
  - Workflows List/Detail

  ## Key Features Tested
  - Navigation between pages
  - Filter and pagination
  - Form submissions
  - Modal dialogs
  - WebSocket real-time updates
  - Bulk actions
  ```
- Full file: `docs/testing/UI_TESTING_GUIDE.md`:
  ```markdown
  # UI Testing Guide

  This guide covers the Playwright-based UI testing setup for TBCV.

  ## Overview
  ...

  ## Page Object Model Pattern
  ...

  ## Writing New Tests
  ...

  ## Debugging Failed Tests
  ...

  ## Best Practices
  ...
  ```
- No stubs, no TODO comments

**Hard rules:**
- Windows friendly paths
- Documentation must be accurate
- Include actual test counts and results
- Provide troubleshooting guidance
- Keep documentation concise

**Self-review (answer yes/no at the end):**
- [ ] tests/README.md updated with UI section
- [ ] Implementation report created
- [ ] Testing guide created
- [ ] Instructions are accurate
- [ ] All links valid

---

## Execution Order

```
Task Card 1 (Setup) → Task Card 2 (Infrastructure) → Task Card 3 (POMs)
                                    ↓
Task Card 4 (Navigation) → Task Card 5 (Validations) → Task Card 6 (Recommendations)
                                    ↓
Task Card 7 (Forms) → Task Card 8 (WebSocket) → Task Card 9 (Bulk)
                                    ↓
                    Task Card 10 (CI/CD) → Task Card 11 (Docs)
```

**Dependencies:**
- Task Cards 1-3 must be done in order (foundation)
- Task Cards 4-9 can be done in parallel after TC3
- Task Card 10 can be done after TC4 (needs at least some tests)
- Task Card 11 must be done last

---

## Quick Reference: Test Counts

| Task Card | New Tests | Cumulative |
|-----------|-----------|------------|
| TC1: Setup | 0 | 0 |
| TC2: Infrastructure | 0 | 0 |
| TC3: POMs | 0 | 0 |
| TC4: Navigation | 10 | 10 |
| TC5: Validations | 12 | 22 |
| TC6: Recommendations | 10 | 32 |
| TC7: Forms/Modals | 15 | 47 |
| TC8: Real-time | 8 | 55 |
| TC9: Bulk Actions | 10 | 65 |
| TC10: CI/CD | 0 | 65 |
| TC11: Docs | 0 | 65 |

**Target:** 65 UI tests

---

## Runbook: Execute All Task Cards

```bash
# Task Card 1: Setup
pip install playwright pytest-playwright
playwright install chromium

# Task Card 2: Verify Infrastructure
python -c "from tests.ui.conftest import *; print('OK')"

# Task Card 3: Verify POMs
python -c "from tests.ui.pages import *; print('OK')"

# Task Cards 4-9: Run All UI Tests
pytest tests/ui/ -v --browser chromium

# Task Card 10: Verify CI Scripts
# Windows:
scripts\run_ui_tests.bat

# Unix:
./scripts/run_ui_tests.sh

# Full Test Suite (including UI)
pytest tests/ --ignore=tests/test_endpoints_live.py --ignore=tests/test_truth_llm_validation_real.py --ignore=tests/manual/ -v

# Flakiness Check (run 3x)
for i in 1 2 3; do echo "Run $i"; pytest tests/ui/ -v --browser chromium; done
```
