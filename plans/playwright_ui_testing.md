# Playwright UI Testing Implementation Plan

## Executive Summary

This plan outlines the implementation of Playwright-based UI testing for the TBCV dashboard to simulate real user behavior. The current test infrastructure uses server-side `TestClient` which validates HTTP responses but cannot test actual browser rendering, JavaScript interactions, or visual user experiences.

**Opportunity Assessment**: HIGH VALUE
- 10 dashboard pages with rich UI interactions
- 3 WebSocket endpoints with real-time updates
- Complex forms, modals, and filter systems
- Current gap: No browser-level testing

---

## 1. Current State Analysis

### Existing Test Coverage (Server-Side)
| Area | Coverage | Tool |
|------|----------|------|
| API Endpoints | High | pytest + TestClient |
| Database Operations | High | pytest + SQLite |
| WebSocket Connections | Medium | TestClient WebSocket |
| E2E User Flows | Medium | pytest fixtures |
| Browser Rendering | **None** | - |
| JavaScript Behavior | **None** | - |
| Visual/CSS | **None** | - |

### Pages Requiring UI Testing
| Page | Route | Priority | Complexity |
|------|-------|----------|------------|
| Dashboard Home | `/dashboard/` | High | High (WebSocket) |
| Validations List | `/dashboard/validations` | High | Medium |
| Validation Detail | `/dashboard/validations/{id}` | High | High (forms) |
| Recommendations List | `/dashboard/recommendations` | High | Medium |
| Recommendation Detail | `/dashboard/recommendations/{id}` | High | High (forms) |
| Workflows List | `/dashboard/workflows` | Medium | Medium |
| Workflow Detail | `/dashboard/workflows/{id}` | Medium | High (WebSocket) |

### Key User Interactions to Test
1. **Navigation**: Header links, pagination, "View" buttons
2. **Forms**: Review forms, validation triggers, workflow execution
3. **Modals**: Run Validation modal, Run Workflow modal
4. **Filters**: Status dropdowns, severity filters, type filters
5. **Real-time**: WebSocket activity feed, progress bars
6. **Bulk Actions**: Multi-select checkboxes, bulk approve/reject

---

## 2. Why Playwright?

### Comparison with Alternatives

| Feature | Playwright | Selenium | Cypress |
|---------|------------|----------|---------|
| Python SDK | Yes (native) | Yes | No (JS only) |
| Cross-browser | Chromium, Firefox, WebKit | All browsers | Chromium, Firefox |
| Auto-wait | Built-in | Manual | Built-in |
| WebSocket testing | Native support | Limited | Good |
| Parallel execution | Built-in | Requires Grid | Paid feature |
| Screenshots/Video | Built-in | Manual | Built-in |
| Network interception | Easy | Complex | Easy |
| Headless mode | Default | Available | Available |
| CI/CD integration | Excellent | Good | Good |

### Playwright Advantages for TBCV
1. **Native Python SDK**: Integrates with existing pytest infrastructure
2. **WebSocket Support**: Critical for testing real-time dashboard features
3. **Auto-waiting**: Reduces flaky tests from timing issues
4. **Built-in assertions**: `expect()` API with retry logic
5. **Trace viewer**: Debug failures with full recording
6. **Network mocking**: Test edge cases without backend changes

---

## 3. Implementation Architecture

### Directory Structure
```
tests/
├── ui/                           # Playwright UI tests
│   ├── __init__.py
│   ├── conftest.py              # Playwright fixtures
│   ├── pages/                    # Page Object Models
│   │   ├── __init__.py
│   │   ├── base_page.py
│   │   ├── dashboard_home.py
│   │   ├── validations_page.py
│   │   ├── validation_detail.py
│   │   ├── recommendations_page.py
│   │   ├── recommendation_detail.py
│   │   ├── workflows_page.py
│   │   └── workflow_detail.py
│   ├── test_navigation.py        # Navigation tests
│   ├── test_validations_flow.py  # Validation user flows
│   ├── test_recommendations_flow.py
│   ├── test_workflows_flow.py
│   ├── test_forms_modals.py      # Form and modal interactions
│   ├── test_realtime_updates.py  # WebSocket/real-time tests
│   ├── test_filters_pagination.py
│   └── test_bulk_actions.py
├── e2e/                          # Existing E2E tests
└── ...                           # Existing test directories
```

### Page Object Model (POM) Pattern
```python
# tests/ui/pages/base_page.py
from playwright.sync_api import Page, expect

class BasePage:
    def __init__(self, page: Page):
        self.page = page
        self.base_url = "http://localhost:8585"

    def navigate(self, path: str = ""):
        self.page.goto(f"{self.base_url}{path}")

    def get_header_nav(self):
        return self.page.locator("header nav")

    def click_nav_link(self, text: str):
        self.page.get_by_role("link", name=text).click()

    def wait_for_page_load(self):
        self.page.wait_for_load_state("networkidle")
```

---

## 4. Test Categories & Specifications

### 4.1 Navigation Tests (`test_navigation.py`)

| Test Case | Description | Priority |
|-----------|-------------|----------|
| `test_header_navigation_links` | All header links navigate correctly | High |
| `test_breadcrumb_navigation` | Breadcrumbs work on detail pages | Medium |
| `test_view_button_navigation` | "View" buttons open correct detail pages | High |
| `test_pagination_navigation` | Page numbers and arrows work | High |
| `test_back_navigation` | Browser back button preserves state | Medium |

### 4.2 Validation Flow Tests (`test_validations_flow.py`)

| Test Case | Description | Priority |
|-----------|-------------|----------|
| `test_view_validation_list` | List renders with correct columns | High |
| `test_filter_by_status` | Status filter updates results | High |
| `test_filter_by_severity` | Severity filter updates results | High |
| `test_combined_filters` | Multiple filters work together | Medium |
| `test_open_validation_detail` | Detail page shows all info | High |
| `test_approve_validation` | Approve button updates status | High |
| `test_reject_validation` | Reject button updates status | High |
| `test_enhance_validation` | Enhance flow completes | High |
| `test_rebuild_recommendations` | Rebuild triggers regeneration | Medium |

### 4.3 Recommendation Flow Tests (`test_recommendations_flow.py`)

| Test Case | Description | Priority |
|-----------|-------------|----------|
| `test_view_recommendations_list` | List renders correctly | High |
| `test_filter_by_recommendation_status` | Status filter works | High |
| `test_filter_by_type` | Type filter works | High |
| `test_open_recommendation_detail` | Detail page shows all info | High |
| `test_approve_recommendation` | Approve updates status | High |
| `test_reject_recommendation` | Reject updates status | High |
| `test_view_source_context` | Source file context displays | Medium |
| `test_view_related_recommendations` | Related section works | Low |

### 4.4 Form & Modal Tests (`test_forms_modals.py`)

| Test Case | Description | Priority |
|-----------|-------------|----------|
| `test_run_validation_modal_opens` | Modal opens on button click | High |
| `test_validation_form_single_mode` | Single file mode form works | High |
| `test_validation_form_batch_mode` | Batch mode form works | High |
| `test_validation_form_submission` | Form submits correctly | High |
| `test_run_workflow_modal_opens` | Workflow modal opens | High |
| `test_workflow_form_directory_mode` | Directory mode works | High |
| `test_workflow_form_batch_mode` | Batch mode works | High |
| `test_review_form_validation` | Form validates required fields | Medium |
| `test_modal_close_on_escape` | ESC key closes modals | Low |
| `test_modal_close_on_backdrop` | Clicking outside closes modal | Low |

### 4.5 Real-time/WebSocket Tests (`test_realtime_updates.py`)

| Test Case | Description | Priority |
|-----------|-------------|----------|
| `test_websocket_connection_status` | Connection indicator shows status | High |
| `test_activity_feed_updates` | Feed receives new events | High |
| `test_metrics_auto_update` | Dashboard metrics update | High |
| `test_workflow_progress_updates` | Progress bar updates in real-time | High |
| `test_reconnection_after_disconnect` | WebSocket reconnects | Medium |

### 4.6 Bulk Action Tests (`test_bulk_actions.py`)

| Test Case | Description | Priority |
|-----------|-------------|----------|
| `test_select_single_checkbox` | Single selection works | High |
| `test_select_all_checkbox` | Select all works | High |
| `test_bulk_approve_recommendations` | Bulk approve works | High |
| `test_bulk_reject_recommendations` | Bulk reject works | High |
| `test_bulk_enhance_validations` | Bulk enhance works | Medium |
| `test_deselect_clears_action` | Deselection clears bulk actions | Low |

---

## 5. Implementation Tasks

### Phase 1: Setup & Infrastructure (Est. Effort: Small)

#### Task 1.1: Install Playwright Dependencies
```bash
pip install playwright pytest-playwright
playwright install chromium  # or --with-deps for all browsers
```

Update `pyproject.toml`:
```toml
[project.optional-dependencies]
test = [
    # ... existing deps
    "playwright>=1.40.0",
    "pytest-playwright>=0.4.0",
]
```

#### Task 1.2: Create Playwright Configuration
Create `pytest.ini` additions or `pyproject.toml`:
```toml
[tool.pytest.ini_options]
markers = [
    "ui: UI/browser tests requiring Playwright",
]

# Playwright-specific
base_url = "http://localhost:8585"
```

Create `playwright.config.py`:
```python
from playwright.sync_api import Playwright

def pytest_configure(config):
    config.addinivalue_line("markers", "ui: mark test as UI test")
```

#### Task 1.3: Create Base Fixtures (`tests/ui/conftest.py`)
```python
import pytest
from playwright.sync_api import Page, BrowserContext
from tests.ui.pages import DashboardHome, ValidationsPage, ...

@pytest.fixture(scope="session")
def browser_context_args():
    return {
        "viewport": {"width": 1920, "height": 1080},
        "record_video_dir": "test-results/videos",
    }

@pytest.fixture
def dashboard_home(page: Page) -> DashboardHome:
    return DashboardHome(page)

@pytest.fixture
def validations_page(page: Page) -> ValidationsPage:
    return ValidationsPage(page)

# ... more page fixtures

@pytest.fixture(scope="session")
def live_server():
    """Start the FastAPI server for UI tests."""
    import subprocess
    import time

    proc = subprocess.Popen(
        ["python", "-m", "uvicorn", "api.server:app",
         "--host", "127.0.0.1", "--port", "8585"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(3)  # Wait for server startup
    yield proc
    proc.terminate()
    proc.wait()

@pytest.fixture
def seeded_database(db_manager):
    """Seed database with test data for UI tests."""
    # Create validations, recommendations, workflows
    validation = db_manager.create_validation_result(
        file_path="/test/file.md",
        status="fail",
        severity="high",
        # ...
    )
    # ... more seeding
    return {"validation": validation, ...}
```

### Phase 2: Page Object Models (Est. Effort: Medium)

#### Task 2.1: Base Page Implementation
```python
# tests/ui/pages/base_page.py
from playwright.sync_api import Page, expect, Locator

class BasePage:
    URL_PATH = "/"

    def __init__(self, page: Page):
        self.page = page

    def navigate(self):
        self.page.goto(f"http://localhost:8585{self.URL_PATH}")
        self.page.wait_for_load_state("networkidle")
        return self

    @property
    def header(self) -> Locator:
        return self.page.locator("header")

    @property
    def nav_links(self) -> Locator:
        return self.header.get_by_role("link")

    def go_to_validations(self):
        self.page.get_by_role("link", name="Validations").click()

    def go_to_recommendations(self):
        self.page.get_by_role("link", name="Recommendations").click()

    def go_to_workflows(self):
        self.page.get_by_role("link", name="Workflows").click()

    def wait_for_toast(self, message: str):
        expect(self.page.locator(".toast")).to_contain_text(message)
```

#### Task 2.2: Dashboard Home Page
```python
# tests/ui/pages/dashboard_home.py
from .base_page import BasePage
from playwright.sync_api import expect

class DashboardHome(BasePage):
    URL_PATH = "/dashboard/"

    @property
    def metrics_grid(self):
        return self.page.locator(".metrics-grid")

    @property
    def total_validations_metric(self):
        return self.metrics_grid.locator("[data-metric='total']")

    @property
    def pending_recommendations_metric(self):
        return self.metrics_grid.locator("[data-metric='pending']")

    @property
    def activity_feed(self):
        return self.page.locator(".activity-feed")

    @property
    def websocket_status(self):
        return self.page.locator(".ws-status")

    @property
    def recent_validations_table(self):
        return self.page.locator("table.recent-validations")

    def wait_for_websocket_connected(self):
        expect(self.websocket_status).to_contain_text("Connected")

    def wait_for_activity_update(self, timeout: int = 10000):
        self.activity_feed.locator(".activity-item").first.wait_for(
            state="visible", timeout=timeout
        )
```

#### Task 2.3: Validations Page
```python
# tests/ui/pages/validations_page.py
from .base_page import BasePage
from playwright.sync_api import expect

class ValidationsPage(BasePage):
    URL_PATH = "/dashboard/validations"

    @property
    def status_filter(self):
        return self.page.locator("select[name='status']")

    @property
    def severity_filter(self):
        return self.page.locator("select[name='severity']")

    @property
    def validations_table(self):
        return self.page.locator("table.validations")

    @property
    def run_validation_button(self):
        return self.page.get_by_role("button", name="Run Validation")

    @property
    def run_validation_modal(self):
        return self.page.locator(".modal.run-validation")

    def filter_by_status(self, status: str):
        self.status_filter.select_option(status)
        self.page.wait_for_load_state("networkidle")

    def filter_by_severity(self, severity: str):
        self.severity_filter.select_option(severity)
        self.page.wait_for_load_state("networkidle")

    def get_validation_rows(self):
        return self.validations_table.locator("tbody tr")

    def click_view_validation(self, index: int = 0):
        self.get_validation_rows().nth(index).get_by_role(
            "link", name="View"
        ).click()

    def open_run_validation_modal(self):
        self.run_validation_button.click()
        expect(self.run_validation_modal).to_be_visible()
```

#### Task 2.4: Validation Detail Page
```python
# tests/ui/pages/validation_detail.py
from .base_page import BasePage
from playwright.sync_api import expect

class ValidationDetailPage(BasePage):
    URL_PATH = "/dashboard/validations/{id}"

    def navigate_to(self, validation_id: int):
        self.page.goto(
            f"http://localhost:8585/dashboard/validations/{validation_id}"
        )
        self.page.wait_for_load_state("networkidle")
        return self

    @property
    def status_badge(self):
        return self.page.locator(".status-badge")

    @property
    def approve_button(self):
        return self.page.get_by_role("button", name="Approve")

    @property
    def reject_button(self):
        return self.page.get_by_role("button", name="Reject")

    @property
    def enhance_button(self):
        return self.page.get_by_role("button", name="Enhance")

    @property
    def recommendations_table(self):
        return self.page.locator("table.recommendations")

    @property
    def recommendation_checkboxes(self):
        return self.recommendations_table.locator("input[type='checkbox']")

    def approve_validation(self):
        self.approve_button.click()
        expect(self.status_badge).to_contain_text("Approved")

    def reject_validation(self):
        self.reject_button.click()
        expect(self.status_badge).to_contain_text("Rejected")

    def select_recommendations(self, indices: list[int]):
        for i in indices:
            self.recommendation_checkboxes.nth(i).check()

    def enhance_selected(self):
        self.page.get_by_role("button", name="Enhance Selected").click()
```

*(Similar POMs for Recommendations, Workflows pages)*

### Phase 3: Core Test Implementation (Est. Effort: Large)

#### Task 3.1: Navigation Tests
```python
# tests/ui/test_navigation.py
import pytest
from playwright.sync_api import Page, expect

@pytest.mark.ui
class TestHeaderNavigation:
    def test_home_link_navigates_to_dashboard(self, page: Page, live_server):
        page.goto("http://localhost:8585/dashboard/validations")
        page.get_by_role("link", name="Dashboard").click()
        expect(page).to_have_url("http://localhost:8585/dashboard/")

    def test_validations_link_works(self, page: Page, live_server):
        page.goto("http://localhost:8585/dashboard/")
        page.get_by_role("link", name="Validations").click()
        expect(page).to_have_url("http://localhost:8585/dashboard/validations")

    def test_recommendations_link_works(self, page: Page, live_server):
        page.goto("http://localhost:8585/dashboard/")
        page.get_by_role("link", name="Recommendations").click()
        expect(page).to_have_url(
            "http://localhost:8585/dashboard/recommendations"
        )

    def test_workflows_link_works(self, page: Page, live_server):
        page.goto("http://localhost:8585/dashboard/")
        page.get_by_role("link", name="Workflows").click()
        expect(page).to_have_url("http://localhost:8585/dashboard/workflows")


@pytest.mark.ui
class TestPagination:
    def test_next_page_navigation(
        self, validations_page, seeded_database, live_server
    ):
        validations_page.navigate()
        # Assuming pagination exists
        page_2_link = validations_page.page.get_by_role("link", name="2")
        if page_2_link.is_visible():
            page_2_link.click()
            expect(validations_page.page).to_have_url(re.compile(r"page=2"))

    def test_previous_page_navigation(
        self, validations_page, seeded_database, live_server
    ):
        validations_page.page.goto(
            "http://localhost:8585/dashboard/validations?page=2"
        )
        validations_page.page.get_by_role("link", name="Previous").click()
        expect(validations_page.page).to_have_url(re.compile(r"page=1|(?!page)"))
```

#### Task 3.2: Validation Flow Tests
```python
# tests/ui/test_validations_flow.py
import pytest
from playwright.sync_api import expect

@pytest.mark.ui
class TestValidationsList:
    def test_list_displays_validations(
        self, validations_page, seeded_database, live_server
    ):
        validations_page.navigate()
        rows = validations_page.get_validation_rows()
        expect(rows).to_have_count_greater_than(0)

    def test_filter_by_status_pass(
        self, validations_page, seeded_database, live_server
    ):
        validations_page.navigate()
        validations_page.filter_by_status("pass")

        # All visible rows should have "pass" status
        rows = validations_page.get_validation_rows()
        for i in range(rows.count()):
            expect(rows.nth(i)).to_contain_text("pass", ignore_case=True)

    def test_filter_by_severity_high(
        self, validations_page, seeded_database, live_server
    ):
        validations_page.navigate()
        validations_page.filter_by_severity("high")

        rows = validations_page.get_validation_rows()
        for i in range(rows.count()):
            expect(rows.nth(i)).to_contain_text("high", ignore_case=True)


@pytest.mark.ui
class TestValidationDetail:
    def test_approve_validation_updates_status(
        self, validation_detail_page, seeded_database, live_server
    ):
        validation_id = seeded_database["validation"].id
        validation_detail_page.navigate_to(validation_id)

        validation_detail_page.approve_validation()
        expect(validation_detail_page.status_badge).to_contain_text("Approved")

    def test_reject_validation_updates_status(
        self, validation_detail_page, seeded_database, live_server
    ):
        validation_id = seeded_database["validation"].id
        validation_detail_page.navigate_to(validation_id)

        validation_detail_page.reject_validation()
        expect(validation_detail_page.status_badge).to_contain_text("Rejected")

    def test_enhance_with_selected_recommendations(
        self, validation_detail_page, seeded_database, live_server
    ):
        validation_id = seeded_database["approved_validation"].id
        validation_detail_page.navigate_to(validation_id)

        validation_detail_page.select_recommendations([0, 1])
        validation_detail_page.enhance_selected()

        # Expect status to change or confirmation toast
        expect(validation_detail_page.status_badge).to_contain_text("Enhanced")
```

#### Task 3.3: Form & Modal Tests
```python
# tests/ui/test_forms_modals.py
import pytest
from playwright.sync_api import expect

@pytest.mark.ui
class TestRunValidationModal:
    def test_modal_opens_on_button_click(
        self, validations_page, live_server
    ):
        validations_page.navigate()
        validations_page.open_run_validation_modal()
        expect(validations_page.run_validation_modal).to_be_visible()

    def test_modal_closes_on_escape(self, validations_page, live_server):
        validations_page.navigate()
        validations_page.open_run_validation_modal()
        validations_page.page.keyboard.press("Escape")
        expect(validations_page.run_validation_modal).to_be_hidden()

    def test_single_file_mode_form(self, validations_page, live_server):
        validations_page.navigate()
        validations_page.open_run_validation_modal()

        modal = validations_page.run_validation_modal
        modal.get_by_label("Single File").check()
        modal.get_by_label("File Path").fill("/path/to/file.md")
        modal.get_by_label("Family").select_option("Words")
        modal.get_by_label("YAML").check()
        modal.get_by_label("Markdown").check()

        modal.get_by_role("button", name="Submit").click()
        # Expect redirect or success message

    def test_batch_mode_form(self, validations_page, live_server):
        validations_page.navigate()
        validations_page.open_run_validation_modal()

        modal = validations_page.run_validation_modal
        modal.get_by_label("Batch").check()
        modal.get_by_label("File Paths").fill(
            "/path/to/file1.md\n/path/to/file2.md"
        )
        modal.get_by_role("button", name="Submit").click()


@pytest.mark.ui
class TestReviewForm:
    def test_approve_recommendation_form(
        self, recommendation_detail_page, seeded_database, live_server
    ):
        rec_id = seeded_database["recommendation"].id
        recommendation_detail_page.navigate_to(rec_id)

        page = recommendation_detail_page.page
        page.get_by_label("Approve").check()
        page.get_by_label("Notes").fill("Looks good")
        page.get_by_role("button", name="Submit Review").click()

        expect(page.locator(".status-badge")).to_contain_text("Approved")

    def test_reject_recommendation_with_reason(
        self, recommendation_detail_page, seeded_database, live_server
    ):
        rec_id = seeded_database["recommendation"].id
        recommendation_detail_page.navigate_to(rec_id)

        page = recommendation_detail_page.page
        page.get_by_label("Reject").check()
        page.get_by_label("Notes").fill("Not applicable")
        page.get_by_role("button", name="Submit Review").click()

        expect(page.locator(".status-badge")).to_contain_text("Rejected")
```

#### Task 3.4: Real-time/WebSocket Tests
```python
# tests/ui/test_realtime_updates.py
import pytest
from playwright.sync_api import expect

@pytest.mark.ui
class TestWebSocketConnection:
    def test_connection_status_shows_connected(
        self, dashboard_home, live_server
    ):
        dashboard_home.navigate()
        dashboard_home.wait_for_websocket_connected()
        expect(dashboard_home.websocket_status).to_contain_text("Connected")

    def test_activity_feed_receives_updates(
        self, dashboard_home, live_server, api_client
    ):
        dashboard_home.navigate()
        dashboard_home.wait_for_websocket_connected()

        # Trigger a validation via API
        api_client.post("/api/validate", json={
            "file_path": "/test/new_file.md",
            "content": "# Test",
            "family": "Words",
        })

        # Activity feed should update
        dashboard_home.wait_for_activity_update()
        expect(dashboard_home.activity_feed).to_contain_text("new_file.md")


@pytest.mark.ui
class TestWorkflowProgress:
    def test_progress_bar_updates_realtime(
        self, workflow_detail_page, running_workflow, live_server
    ):
        workflow_detail_page.navigate_to(running_workflow.id)

        initial_progress = workflow_detail_page.progress_bar.get_attribute(
            "aria-valuenow"
        )

        # Wait for progress update
        workflow_detail_page.page.wait_for_timeout(5000)

        new_progress = workflow_detail_page.progress_bar.get_attribute(
            "aria-valuenow"
        )

        # Progress should have increased (or completed)
        assert int(new_progress) >= int(initial_progress)
```

#### Task 3.5: Bulk Action Tests
```python
# tests/ui/test_bulk_actions.py
import pytest
from playwright.sync_api import expect

@pytest.mark.ui
class TestBulkRecommendationActions:
    def test_select_multiple_recommendations(
        self, recommendations_page, seeded_database, live_server
    ):
        recommendations_page.navigate()

        checkboxes = recommendations_page.recommendation_checkboxes
        checkboxes.nth(0).check()
        checkboxes.nth(1).check()

        expect(checkboxes.nth(0)).to_be_checked()
        expect(checkboxes.nth(1)).to_be_checked()

    def test_bulk_approve_recommendations(
        self, recommendations_page, seeded_database, live_server
    ):
        recommendations_page.navigate()

        # Select multiple
        recommendations_page.recommendation_checkboxes.nth(0).check()
        recommendations_page.recommendation_checkboxes.nth(1).check()

        # Click bulk approve
        recommendations_page.page.get_by_role(
            "button", name="Bulk Approve"
        ).click()

        # Confirm in modal if exists
        confirm = recommendations_page.page.get_by_role(
            "button", name="Confirm"
        )
        if confirm.is_visible():
            confirm.click()

        # Verify status updated
        expect(recommendations_page.page).to_contain_text("approved")

    def test_select_all_checkbox(
        self, recommendations_page, seeded_database, live_server
    ):
        recommendations_page.navigate()

        select_all = recommendations_page.page.locator(
            "input[type='checkbox'][data-select-all]"
        )
        select_all.check()

        # All individual checkboxes should be checked
        checkboxes = recommendations_page.recommendation_checkboxes
        for i in range(checkboxes.count()):
            expect(checkboxes.nth(i)).to_be_checked()
```

### Phase 4: CI/CD Integration (Est. Effort: Small)

#### Task 4.1: GitHub Actions Workflow
```yaml
# .github/workflows/ui-tests.yml
name: UI Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  ui-tests:
    runs-on: ubuntu-latest

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

      - name: Start server
        run: |
          python -m uvicorn api.server:app --host 127.0.0.1 --port 8585 &
          sleep 5

      - name: Run UI tests
        run: |
          pytest tests/ui/ -v --browser chromium --screenshot=on --video=on

      - name: Upload test artifacts
        uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-results
          path: test-results/
```

#### Task 4.2: Local Test Runner Script
```bash
#!/bin/bash
# scripts/run_ui_tests.sh

# Start server in background
echo "Starting server..."
python -m uvicorn api.server:app --host 127.0.0.1 --port 8585 &
SERVER_PID=$!
sleep 3

# Run tests
echo "Running UI tests..."
pytest tests/ui/ -v --browser chromium "$@"
TEST_EXIT=$?

# Cleanup
kill $SERVER_PID 2>/dev/null

exit $TEST_EXIT
```

### Phase 5: Advanced Features (Est. Effort: Medium)

#### Task 5.1: Visual Regression Testing
```python
# tests/ui/test_visual_regression.py
import pytest
from playwright.sync_api import expect

@pytest.mark.ui
@pytest.mark.visual
class TestVisualRegression:
    def test_dashboard_home_screenshot(self, dashboard_home, live_server):
        dashboard_home.navigate()
        dashboard_home.wait_for_websocket_connected()

        expect(dashboard_home.page).to_have_screenshot(
            "dashboard-home.png",
            full_page=True,
            mask=[dashboard_home.activity_feed],  # Mask dynamic content
        )

    def test_validations_list_screenshot(
        self, validations_page, seeded_database, live_server
    ):
        validations_page.navigate()

        expect(validations_page.page).to_have_screenshot(
            "validations-list.png",
            full_page=True,
        )
```

#### Task 5.2: Accessibility Testing
```python
# tests/ui/test_accessibility.py
import pytest
from playwright.sync_api import expect

@pytest.mark.ui
@pytest.mark.a11y
class TestAccessibility:
    def test_dashboard_has_proper_headings(self, dashboard_home, live_server):
        dashboard_home.navigate()

        h1 = dashboard_home.page.locator("h1")
        expect(h1).to_have_count(1)
        expect(h1).to_be_visible()

    def test_forms_have_labels(self, validations_page, live_server):
        validations_page.navigate()
        validations_page.open_run_validation_modal()

        inputs = validations_page.run_validation_modal.locator("input")
        for i in range(inputs.count()):
            input_el = inputs.nth(i)
            input_id = input_el.get_attribute("id")
            if input_id:
                label = validations_page.page.locator(f"label[for='{input_id}']")
                expect(label).to_be_visible()

    def test_keyboard_navigation(self, validations_page, live_server):
        validations_page.navigate()

        # Tab through interactive elements
        validations_page.page.keyboard.press("Tab")
        focused = validations_page.page.locator(":focus")
        expect(focused).to_be_visible()
```

#### Task 5.3: Performance Testing
```python
# tests/ui/test_performance.py
import pytest
from playwright.sync_api import expect

@pytest.mark.ui
@pytest.mark.performance
class TestPageLoadPerformance:
    def test_dashboard_loads_under_3_seconds(self, page, live_server):
        start = page.evaluate("() => performance.now()")
        page.goto("http://localhost:8585/dashboard/")
        page.wait_for_load_state("networkidle")
        end = page.evaluate("() => performance.now()")

        load_time = end - start
        assert load_time < 3000, f"Page took {load_time}ms to load"

    def test_validations_list_loads_under_2_seconds(self, page, live_server):
        start = page.evaluate("() => performance.now()")
        page.goto("http://localhost:8585/dashboard/validations")
        page.wait_for_load_state("networkidle")
        end = page.evaluate("() => performance.now()")

        load_time = end - start
        assert load_time < 2000, f"Page took {load_time}ms to load"
```

---

## 6. Test Data Strategy

### Seeding Approaches

#### Option A: API-Based Seeding (Recommended)
```python
@pytest.fixture
def seeded_database(api_client):
    """Seed via API calls - tests real endpoints."""
    # Create validation
    resp = api_client.post("/api/validate", json={...})
    validation_id = resp.json()["id"]

    # Approve to generate recommendations
    api_client.post(f"/api/validations/{validation_id}/approve")

    return {"validation_id": validation_id}
```

#### Option B: Direct Database Seeding
```python
@pytest.fixture
def seeded_database(db_manager):
    """Direct DB seeding - faster but bypasses API logic."""
    validation = db_manager.create_validation_result(...)
    recommendations = [
        db_manager.create_recommendation(validation_id=validation.id, ...)
        for _ in range(5)
    ]
    return {"validation": validation, "recommendations": recommendations}
```

### Data Cleanup
```python
@pytest.fixture(autouse=True)
def cleanup_test_data(db_manager):
    """Clean up after each test."""
    yield
    db_manager.session.query(Validation).filter(
        Validation.file_path.like("/test/%")
    ).delete()
    db_manager.session.commit()
```

---

## 7. Running Tests

### Command Reference

```bash
# Run all UI tests
pytest tests/ui/ -v

# Run specific test file
pytest tests/ui/test_navigation.py -v

# Run with specific browser
pytest tests/ui/ --browser chromium
pytest tests/ui/ --browser firefox
pytest tests/ui/ --browser webkit

# Run headed (see browser)
pytest tests/ui/ --headed

# Run with slow motion (debugging)
pytest tests/ui/ --slowmo 500

# Generate screenshots on failure
pytest tests/ui/ --screenshot=only-on-failure

# Record videos
pytest tests/ui/ --video=on

# Run with trace (for debugging)
pytest tests/ui/ --tracing=on

# View trace
playwright show-trace test-results/trace.zip

# Update visual snapshots
pytest tests/ui/test_visual_regression.py --update-snapshots
```

### pytest Markers
```bash
# Run only UI tests
pytest -m ui

# Run only visual regression tests
pytest -m "ui and visual"

# Run only accessibility tests
pytest -m "ui and a11y"

# Skip slow tests
pytest -m "ui and not slow"
```

---

## 8. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| UI Test Coverage | 80% of user flows | Count of tested flows / total flows |
| Test Reliability | < 2% flaky rate | Flaky runs / total runs |
| Execution Time | < 5 min total | CI pipeline duration |
| Defect Detection | Catch UI bugs pre-release | Bugs found by UI tests |
| Maintenance Effort | < 2 hrs/week | Time spent fixing tests |

---

## 9. Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Flaky tests | Use auto-waiting, explicit waits, retry logic |
| Slow execution | Parallel execution, headless mode, selective testing |
| Test data conflicts | Isolated test databases, cleanup fixtures |
| Browser inconsistencies | Focus on Chromium, periodic cross-browser runs |
| Maintenance burden | Page Object Model, shared fixtures, clear naming |

---

## 10. Implementation Timeline

### Recommended Sequence

1. **Phase 1**: Setup & Infrastructure - START HERE
2. **Phase 2**: Page Object Models - Build foundation
3. **Phase 3**: Core Test Implementation - Main value
4. **Phase 4**: CI/CD Integration - Automate
5. **Phase 5**: Advanced Features - Enhance

### Quick Wins (First 2-3 Tasks)
1. Install Playwright and create base fixtures
2. Implement `BasePage` and `DashboardHome` POMs
3. Write 3-5 navigation tests to validate setup

---

## 11. Dependencies to Add

```toml
# pyproject.toml
[project.optional-dependencies]
test = [
    # Existing
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    # New for Playwright
    "playwright>=1.40.0",
    "pytest-playwright>=0.4.0",
]
```

```bash
# Install commands
pip install playwright pytest-playwright
playwright install chromium  # Minimal
playwright install           # All browsers
playwright install --with-deps  # With system dependencies
```

---

## Appendix A: Locator Strategy Reference

| Element Type | Preferred Locator | Example |
|--------------|-------------------|---------|
| Buttons | `get_by_role("button", name="...")` | `page.get_by_role("button", name="Submit")` |
| Links | `get_by_role("link", name="...")` | `page.get_by_role("link", name="View")` |
| Form inputs | `get_by_label("...")` | `page.get_by_label("File Path")` |
| Text content | `get_by_text("...")` | `page.get_by_text("Success")` |
| Test IDs | `get_by_test_id("...")` | `page.get_by_test_id("submit-btn")` |
| CSS (fallback) | `locator(".class")` | `page.locator(".status-badge")` |

---

## Appendix B: Template Selectors Audit

Based on template analysis, key selectors to target:

| Template | Key Elements | Suggested Test IDs |
|----------|--------------|-------------------|
| `base.html` | Header nav links | `data-testid="nav-{page}"` |
| `validations_list.html` | Filter dropdowns, table rows | `data-testid="status-filter"`, `data-testid="validation-row"` |
| `validation_detail.html` | Approve/Reject buttons, checkboxes | `data-testid="approve-btn"`, `data-testid="rec-checkbox-{id}"` |
| `recommendations_list.html` | Bulk action buttons | `data-testid="bulk-approve"`, `data-testid="bulk-reject"` |
| `workflows_list.html` | State filter, workflow rows | `data-testid="state-filter"`, `data-testid="workflow-row"` |

**Recommendation**: Add `data-testid` attributes to templates for reliable test targeting.
