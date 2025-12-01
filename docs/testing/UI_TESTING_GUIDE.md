# UI Testing Guide

This guide covers the Playwright-based UI testing setup for the TBCV dashboard.

## Overview

TBCV uses [Playwright](https://playwright.dev/python/) for browser-based UI testing. These tests simulate real user interactions with the dashboard to ensure the web interface works correctly.

### Why Playwright?

- **Native Python SDK**: Integrates seamlessly with our pytest infrastructure
- **Cross-browser support**: Test on Chromium, Firefox, and WebKit
- **Auto-waiting**: Built-in intelligent waiting reduces flaky tests
- **WebSocket support**: Essential for testing our real-time dashboard features
- **Screenshots/Videos**: Capture evidence on test failures

## Quick Start

### Installation

```bash
# Install test dependencies
pip install -e ".[test]"

# Install Playwright browsers
playwright install chromium
```

### Running Tests

```bash
# Run all UI tests
pytest tests/ui/ -v

# Run with visible browser (for debugging)
pytest tests/ui/ -v --headed

# Run specific test file
pytest tests/ui/test_navigation.py -v

# Run with screenshots on failure
pytest tests/ui/ -v --screenshot=only-on-failure

# Run with video recording
pytest tests/ui/ -v --video=on
```

### Using the Helper Scripts

**Windows:**
```batch
scripts\run_ui_tests.bat
```

**Linux/macOS:**
```bash
./scripts/run_ui_tests.sh
```

## Project Structure

```
tests/ui/
   __init__.py
   conftest.py              # Fixtures (server, pages, data)
   pages/                   # Page Object Models
      __init__.py
      base_page.py          # Common page functionality
      dashboard_home.py     # Dashboard home page
      validations_page.py   # Validations list page
      validation_detail.py  # Validation detail page
      recommendations_page.py
      recommendation_detail.py
      workflows_page.py
      workflow_detail.py
   test_navigation.py       # Navigation tests
   test_validations_flow.py # Validation workflow tests
   test_recommendations_flow.py
   test_forms_modals.py     # Form and modal tests
   test_realtime_updates.py # WebSocket/real-time tests
   test_bulk_actions.py     # Bulk action tests
```

## Page Object Model (POM)

We use the Page Object Model pattern to encapsulate page interactions.

### Base Page

All page objects inherit from `BasePage`:

```python
from tests.ui.pages import BasePage

class MyPage(BasePage):
    URL_PATH = "/my-page"

    @property
    def my_element(self):
        return self.page.locator(".my-element")

    def do_action(self):
        self.my_element.click()
        self.page.wait_for_load_state("networkidle")
```

### Using Page Objects in Tests

```python
import pytest
from playwright.sync_api import expect

@pytest.mark.ui
class TestMyPage:
    def test_element_visible(self, my_page, live_server):
        my_page.navigate()
        expect(my_page.my_element).to_be_visible()
```

## Writing Tests

### Test Structure

```python
import pytest
from playwright.sync_api import Page, expect

@pytest.mark.ui
class TestFeature:
    """Test class for feature X."""

    def test_basic_functionality(self, page_object, live_server):
        """Test that basic functionality works."""
        # Arrange
        page_object.navigate()

        # Act
        page_object.do_action()

        # Assert
        expect(page_object.result_element).to_be_visible()
```

### Best Practices

1. **Use `@pytest.mark.ui`** on all UI test classes
2. **Use page objects** for all page interactions
3. **Use `expect()` assertions** for better error messages
4. **Handle missing data gracefully** with `pytest.skip()`
5. **Use proper waits** - avoid `time.sleep()`, use Playwright waits

### Waiting for Elements

```python
# Good - Playwright auto-waits
element.click()

# Good - Explicit wait when needed
page.wait_for_load_state("networkidle")

# Good - Wait for specific condition
expect(element).to_be_visible(timeout=10000)

# Bad - Never use sleep
time.sleep(2)  # Don't do this!
```

### Handling Dynamic Content

```python
# Wait for text to appear
page.get_by_text("Success").wait_for(state="visible", timeout=5000)

# Wait for element count
expect(page.locator("tr")).to_have_count(5)

# Wait for URL change
expect(page).to_have_url(re.compile(r"/validations/\d+"))
```

## Fixtures

### Core Fixtures

| Fixture | Scope | Purpose |
|---------|-------|---------|
| `live_server` | session | Starts FastAPI server |
| `base_url` | function | Server base URL |
| `page` | function | Playwright page (from pytest-playwright) |

### Page Object Fixtures

| Fixture | Returns |
|---------|---------|
| `dashboard_home` | DashboardHome |
| `validations_page` | ValidationsPage |
| `validation_detail_page` | ValidationDetailPage |
| `recommendations_page` | RecommendationsPage |
| `recommendation_detail_page` | RecommendationDetailPage |
| `workflows_page` | WorkflowsPage |
| `workflow_detail_page` | WorkflowDetailPage |

### Data Fixtures

| Fixture | Purpose |
|---------|---------|
| `seeded_validation` | Creates a validation via API |
| `approved_validation` | Creates an approved validation |
| `multiple_validations` | Creates 5 validations |
| `multiple_recommendations` | Creates recommendations |
| `running_workflow` | Creates a running workflow |

## Debugging

### Run with Visible Browser

```bash
pytest tests/ui/test_navigation.py -v --headed
```

### Slow Motion

```bash
pytest tests/ui/ -v --headed --slowmo=500
```

### Pause on Failure

```python
def test_debugging(page):
    page.goto("/dashboard")
    page.pause()  # Opens Playwright Inspector
```

### Screenshots

```bash
# Screenshot on failure
pytest tests/ui/ -v --screenshot=only-on-failure

# Screenshot always
pytest tests/ui/ -v --screenshot=on
```

### Trace Viewer

```bash
# Record trace
pytest tests/ui/ -v --tracing=on

# View trace
playwright show-trace test-results/trace.zip
```

## CI/CD Integration

UI tests run automatically in GitHub Actions:

- **On push to main**: Runs on Chromium
- **Cross-browser**: Runs on Firefox and WebKit (main branch only)

### Running in CI

The GitHub Actions workflow (`.github/workflows/ui-tests.yml`) handles:
- Installing dependencies
- Installing Playwright browsers
- Running tests
- Uploading screenshots on failure

## Troubleshooting

### Server Won't Start

```python
# Check if port is in use
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex(('127.0.0.1', 8585))
print(f"Port in use: {result == 0}")
```

### Tests Timing Out

1. Increase timeout: `--timeout=120`
2. Check server is running
3. Use `--headed` to see what's happening

### Flaky Tests

1. Use explicit waits instead of implicit
2. Ensure test data isolation
3. Run multiple times: `pytest tests/ui/ --count=3`

### WebSocket Tests Failing

WebSocket tests are designed to be lenient:
- They skip if WebSocket features aren't available
- Use longer timeouts (10-15 seconds)
- Check connection status indicators

## Additional Resources

- [Playwright Python Documentation](https://playwright.dev/python/)
- [pytest-playwright Plugin](https://github.com/microsoft/playwright-pytest)
- [Playwright Locators](https://playwright.dev/python/docs/locators)
- [Playwright Assertions](https://playwright.dev/python/docs/test-assertions)
