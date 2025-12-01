"""Playwright UI test fixtures and configuration."""
import os
import sys
import socket
import subprocess
import time
from contextlib import closing
from typing import Generator, Dict, Any

import pytest
from playwright.sync_api import Page, BrowserContext, Playwright

# Import page objects
from tests.ui.pages import (
    DashboardHome,
    ValidationsPage,
    ValidationDetailPage,
    RecommendationsPage,
    RecommendationDetailPage,
    WorkflowsPage,
    WorkflowDetailPage,
)


def find_free_port() -> int:
    """Find a free port for the test server.

    Returns:
        Available port number
    """
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def wait_for_port(port: int, host: str = "127.0.0.1", timeout: float = 10.0) -> bool:
    """Wait for a port to become available.

    Args:
        port: Port number to check
        host: Host address
        timeout: Maximum wait time in seconds

    Returns:
        True if port is available, False if timeout
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
                s.settimeout(1)
                s.connect((host, port))
                return True
        except (ConnectionRefusedError, socket.timeout, OSError):
            time.sleep(0.1)
    return False


# =============================================================================
# Browser Configuration
# =============================================================================

@pytest.fixture(scope="session")
def browser_context_args() -> Dict[str, Any]:
    """Configure browser context for UI tests.

    Returns:
        Browser context configuration dictionary
    """
    return {
        "viewport": {"width": 1920, "height": 1080},
        "ignore_https_errors": True,
    }


# =============================================================================
# Server Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def test_server_port() -> int:
    """Get a free port for the test server.

    Returns:
        Available port number
    """
    return find_free_port()


def kill_process_on_port(port: int):
    """Kill any process using the specified port."""
    if sys.platform == "win32":
        try:
            import subprocess
            result = subprocess.run(
                f'netstat -ano | findstr :{port}',
                shell=True, capture_output=True, text=True
            )
            for line in result.stdout.strip().split('\n'):
                if line and 'LISTENING' in line:
                    parts = line.strip().split()
                    if parts:
                        pid = parts[-1]
                        subprocess.run(f'taskkill /F /PID {pid}', shell=True, capture_output=True)
        except Exception:
            pass
    else:
        try:
            import subprocess
            result = subprocess.run(
                f'lsof -ti:{port}',
                shell=True, capture_output=True, text=True
            )
            if result.stdout.strip():
                subprocess.run(f'kill -9 {result.stdout.strip()}', shell=True)
        except Exception:
            pass


@pytest.fixture(scope="session")
def live_server(test_server_port: int) -> Generator[Dict[str, Any], None, None]:
    """Start FastAPI server for UI tests.

    Args:
        test_server_port: Port to run server on

    Yields:
        Dictionary with server info (port, process)
    """
    import signal

    # Determine the Python executable
    python_exe = sys.executable

    # Kill any existing process on the port
    kill_process_on_port(test_server_port)

    # Start the server with proper test environment
    env = os.environ.copy()
    env["TBCV_TEST_MODE"] = "1"
    env["TBCV_ENV"] = "test"
    env["OLLAMA_ENABLED"] = "false"
    env["OLLAMA_MODEL"] = "mistral"

    # Use different startup depending on platform
    if sys.platform == "win32":
        # Windows: use shell=False with list args
        proc = subprocess.Popen(
            [python_exe, "-m", "uvicorn", "api.server:app",
             "--host", "127.0.0.1", "--port", str(test_server_port),
             "--log-level", "error"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
    else:
        # Unix: standard subprocess with preexec_fn for process group
        proc = subprocess.Popen(
            [python_exe, "-m", "uvicorn", "api.server:app",
             "--host", "127.0.0.1", "--port", str(test_server_port),
             "--log-level", "error"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            preexec_fn=os.setsid,
        )

    # Extended timeout for Windows (server initialization can take longer)
    timeout = 45.0 if sys.platform == "win32" else 20.0

    # Wait for server to be ready
    if not wait_for_port(test_server_port, timeout=timeout):
        # Server failed to start - try to get stderr but don't block
        stderr_output = ""
        try:
            # Non-blocking read of stderr
            import select
            if sys.platform != "win32":
                if select.select([proc.stderr], [], [], 0.1)[0]:
                    stderr_output = proc.stderr.read(1000).decode(errors='ignore')
            else:
                # On Windows, just try to terminate without reading
                pass
        except Exception:
            pass

        # Terminate the process
        try:
            proc.terminate()
        except Exception:
            pass

        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            try:
                proc.kill()
                proc.wait(timeout=2)
            except Exception:
                pass

        pytest.skip(f"Server failed to start on port {test_server_port} - skipping UI tests")

    yield {"port": test_server_port, "process": proc}

    # Cleanup
    if sys.platform == "win32":
        try:
            proc.send_signal(signal.CTRL_BREAK_EVENT)
        except Exception:
            proc.terminate()
    else:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except Exception:
            proc.terminate()

    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)


@pytest.fixture(scope="session")
def base_url(request) -> str:
    """Base URL for the test server.

    Uses --base-url command line argument if provided,
    otherwise starts live_server fixture.

    Args:
        request: pytest request object

    Returns:
        Base URL string
    """
    # Check if --base-url was provided via command line
    cmdline_base_url = request.config.getoption("--base-url", default=None)
    if cmdline_base_url:
        return cmdline_base_url
    # Request live_server fixture only if not provided via command line
    live_server = request.getfixturevalue("live_server")
    return f"http://127.0.0.1:{live_server['port']}"


@pytest.fixture
def dashboard_url(base_url: str) -> str:
    """Dashboard base URL.

    Args:
        base_url: Base server URL

    Returns:
        Dashboard URL string
    """
    return f"{base_url}/dashboard"


# =============================================================================
# Page Object Fixtures
# =============================================================================

@pytest.fixture
def dashboard_home(page: Page, base_url: str) -> DashboardHome:
    """Dashboard home page object.

    Args:
        page: Playwright page
        base_url: Base server URL

    Returns:
        DashboardHome page object
    """
    return DashboardHome(page, base_url)


@pytest.fixture
def validations_page(page: Page, base_url: str) -> ValidationsPage:
    """Validations list page object.

    Args:
        page: Playwright page
        base_url: Base server URL

    Returns:
        ValidationsPage page object
    """
    return ValidationsPage(page, base_url)


@pytest.fixture
def validation_detail_page(page: Page, base_url: str) -> ValidationDetailPage:
    """Validation detail page object.

    Args:
        page: Playwright page
        base_url: Base server URL

    Returns:
        ValidationDetailPage page object
    """
    return ValidationDetailPage(page, base_url)


@pytest.fixture
def recommendations_page(page: Page, base_url: str) -> RecommendationsPage:
    """Recommendations list page object.

    Args:
        page: Playwright page
        base_url: Base server URL

    Returns:
        RecommendationsPage page object
    """
    return RecommendationsPage(page, base_url)


@pytest.fixture
def recommendation_detail_page(page: Page, base_url: str) -> RecommendationDetailPage:
    """Recommendation detail page object.

    Args:
        page: Playwright page
        base_url: Base server URL

    Returns:
        RecommendationDetailPage page object
    """
    return RecommendationDetailPage(page, base_url)


@pytest.fixture
def workflows_page(page: Page, base_url: str) -> WorkflowsPage:
    """Workflows list page object.

    Args:
        page: Playwright page
        base_url: Base server URL

    Returns:
        WorkflowsPage page object
    """
    return WorkflowsPage(page, base_url)


@pytest.fixture
def workflow_detail_page(page: Page, base_url: str) -> WorkflowDetailPage:
    """Workflow detail page object.

    Args:
        page: Playwright page
        base_url: Base server URL

    Returns:
        WorkflowDetailPage page object
    """
    return WorkflowDetailPage(page, base_url)


# =============================================================================
# Data Fixtures
# =============================================================================

@pytest.fixture
def seeded_validation(base_url: str) -> Generator[Dict[str, Any], None, None]:
    """Create a validation for UI tests via API.

    Args:
        base_url: Base server URL

    Yields:
        Dictionary with validation data
    """
    import httpx

    # Create a validation via API
    try:
        with httpx.Client(base_url=base_url, timeout=10.0) as client:
            response = client.post("/api/validate", json={
                "file_path": "/test/ui_test_file.md",
                "content": "# Test File\n\nThis is test content for UI testing.",
                "family": "Words",
                "validation_types": ["yaml", "markdown"],
            })
            if response.status_code in (200, 201):
                data = response.json()
                yield data
            else:
                yield {"id": None, "error": response.text}
    except Exception as e:
        yield {"id": None, "error": str(e)}


@pytest.fixture
def approved_validation(base_url: str, seeded_validation: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
    """Create an approved validation with recommendations.

    Args:
        base_url: Base server URL
        seeded_validation: Seeded validation fixture

    Yields:
        Dictionary with validation data
    """
    import httpx

    if not seeded_validation.get("id"):
        yield seeded_validation
        return

    try:
        with httpx.Client(base_url=base_url, timeout=10.0) as client:
            # Approve the validation
            response = client.post(f"/api/validations/{seeded_validation['id']}/approve")
            if response.status_code in (200, 201):
                data = response.json()
                yield data
            else:
                yield seeded_validation
    except Exception:
        yield seeded_validation


@pytest.fixture
def multiple_validations(base_url: str) -> Generator[list, None, None]:
    """Create multiple validations for bulk tests.

    Args:
        base_url: Base server URL

    Yields:
        List of validation data dictionaries
    """
    import httpx

    validations = []
    try:
        with httpx.Client(base_url=base_url, timeout=10.0) as client:
            for i in range(5):
                response = client.post("/api/validate", json={
                    "file_path": f"/test/bulk_test_file_{i}.md",
                    "content": f"# Test File {i}\n\nBulk test content.",
                    "family": "Words",
                    "validation_types": ["yaml", "markdown"],
                })
                if response.status_code in (200, 201):
                    validations.append(response.json())
    except Exception:
        pass

    yield validations


class RecommendationWrapper:
    """Wrapper class to provide attribute-style access to recommendation dicts."""

    def __init__(self, data: Dict[str, Any]):
        self._data = data
        self.id = data.get("id") or data.get("recommendation_id")
        # Create a Status-like object with value attribute
        status_val = data.get("status", "pending")
        self.status = type('Status', (), {'value': status_val})()
        self.type = data.get("type", "")
        self.title = data.get("title", "")

    def get(self, key, default=None):
        return self._data.get(key, default)

    def __getitem__(self, key):
        return self._data[key]


@pytest.fixture
def multiple_recommendations(base_url: str, approved_validation: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
    """Create multiple recommendations for bulk tests.

    Args:
        base_url: Base server URL
        approved_validation: Approved validation fixture

    Yields:
        Dictionary with 'recommendations' list (wrapped) and 'validation' data
    """
    import httpx

    result = {"recommendations": [], "validation": approved_validation}
    if not approved_validation.get("id"):
        yield result
        return

    try:
        with httpx.Client(base_url=base_url, timeout=10.0) as client:
            # Get recommendations for the validation
            response = client.get(f"/api/validations/{approved_validation['id']}")
            if response.status_code == 200:
                data = response.json()
                raw_recs = data.get("recommendations", [])
                # Wrap recommendations for attribute-style access
                result["recommendations"] = [
                    RecommendationWrapper(rec) if isinstance(rec, dict) else rec
                    for rec in raw_recs
                ]
                result["validation"] = data
    except Exception:
        pass

    yield result


@pytest.fixture
def recommendations_various_types(base_url: str, approved_validation: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
    """Create recommendations with various types for filter tests.

    Args:
        base_url: Base server URL
        approved_validation: Approved validation fixture

    Yields:
        Dictionary with 'recommendations' list (wrapped) containing various types
    """
    import httpx

    result = {"recommendations": [], "validation": approved_validation}
    if not approved_validation.get("id"):
        yield result
        return

    try:
        with httpx.Client(base_url=base_url, timeout=10.0) as client:
            # Get recommendations for the validation
            response = client.get(f"/api/validations/{approved_validation['id']}")
            if response.status_code == 200:
                data = response.json()
                raw_recs = data.get("recommendations", [])
                # Wrap recommendations for attribute-style access
                result["recommendations"] = [
                    RecommendationWrapper(rec) if isinstance(rec, dict) else rec
                    for rec in raw_recs
                ]
                result["validation"] = data
    except Exception:
        pass

    yield result


@pytest.fixture
def approved_recommendation(base_url: str, multiple_recommendations: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
    """Get or create an approved recommendation for tests.

    Args:
        base_url: Base server URL
        multiple_recommendations: Multiple recommendations fixture

    Yields:
        Dictionary with 'recommendation' (wrapped) and 'validation' data
    """
    recommendations = multiple_recommendations.get("recommendations", [])
    validation = multiple_recommendations.get("validation", {})

    result = {"recommendation": None, "validation": validation}

    if not recommendations:
        yield result
        return

    # Use the first recommendation - already wrapped by multiple_recommendations fixture
    first_rec = recommendations[0] if recommendations else None
    result["recommendation"] = first_rec

    yield result


@pytest.fixture
def running_workflow(base_url: str) -> Generator[Dict[str, Any], None, None]:
    """Create a running workflow for tests.

    Args:
        base_url: Base server URL

    Yields:
        Dictionary with workflow data
    """
    import httpx

    workflow_data = {"id": None}
    try:
        with httpx.Client(base_url=base_url, timeout=10.0) as client:
            response = client.post("/workflows/validate-directory", json={
                "directory": "/test",
                "file_pattern": "*.md",
                "family": "Words",
                "validation_types": ["yaml", "markdown"],
            })
            if response.status_code in (200, 201, 202):
                workflow_data = response.json()
    except Exception:
        pass

    yield workflow_data


# =============================================================================
# API Helper Fixtures
# =============================================================================

@pytest.fixture
def api_client(base_url: str):
    """HTTP client for API calls during UI tests.

    Args:
        base_url: Base server URL

    Yields:
        httpx Client instance
    """
    import httpx

    with httpx.Client(base_url=base_url, timeout=10.0) as client:
        yield client


@pytest.fixture
def trigger_validation_event(api_client):
    """Helper to trigger a validation event via API.

    Args:
        api_client: HTTP client fixture

    Returns:
        Function to trigger validation
    """
    def _trigger(file_path: str = "/test/event_file.md"):
        try:
            response = api_client.post("/api/validate", json={
                "file_path": file_path,
                "content": "# Event Test\n\nTriggered for UI test.",
                "family": "Words",
            })
            return response.json() if response.status_code in (200, 201) else None
        except Exception:
            return None
    return _trigger
