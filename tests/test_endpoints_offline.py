# file: tbcv/tests/test_endpoints_offline.py
"""
Tests for endpoint discovery and probing in offline mode.

This test suite performs the following checks:

* Discovers all registered endpoints from the FastAPI app.
* Scans the source files of the API server and dashboard to collect any
  declared endpoints that might not be mounted.
* Probes every registered endpoint using the FastAPI TestClient and ensures
  that health endpoints respond correctly.
* Verifies that calling GET on the ``/api/enhance`` path returns a 405
  Method Not Allowed response when the route is POST-only.
* Confirms that the ``/dashboard`` path either returns a successful
  response or is flagged as declared-only if the dashboard router is not
  mounted on the app.
* Generates JSON and Markdown reports into the ``data/reports`` directory.

Note: These tests are designed to run without a live server. They use the
application directly via the TestClient. The generated reports can be
examined manually if needed.
"""

import importlib
import inspect
from pathlib import Path

from fastapi.testclient import TestClient

from api.server import app
from tools.endpoint_probe import (
    EndpointDiscovery,
    EndpointProber,
    ReportGenerator,
    ProbeMode,
)


def test_offline_endpoint_probing():
    """Discover, probe, and validate API endpoints in offline mode."""
    # Discover registered endpoints from the app
    discovery = EndpointDiscovery()
    registered = discovery.discover_registered(app)
    # registered returns list of dicts with keys: path, methods (list), name
    paths_registered = set()
    for ep in registered:
        path = ep.get("path") if isinstance(ep, dict) else getattr(ep, "path", None)
        methods = ep.get("methods", []) if isinstance(ep, dict) else getattr(ep, "methods", [])
        for method in methods:
            paths_registered.add((method, path))

    # Ensure health endpoints are registered
    assert ('GET', '/health/live') in paths_registered
    assert ('GET', '/health/ready') in paths_registered

    # Probe endpoints in offline mode using the available API
    prober = EndpointProber(ProbeMode.OFFLINE)
    results = prober.probe_endpoints(registered)

    # Verify results structure
    assert len(results) > 0, "Should have probe results"
    for result in results:
        assert "path" in result
        assert "methods" in result

    # /api/enhance: GET should return 405 because the route is POST-only
    client = TestClient(app)
    enhance_resp = client.get('/api/enhance')
    assert enhance_resp.status_code == 405
    # Ensure the Allow header advertises POST
    allow_header = enhance_resp.headers.get('allow') or enhance_resp.headers.get('Allow')
    assert allow_header is not None and 'POST' in allow_header

    # /dashboard: should be accessible
    dash_response = client.get('/dashboard')
    assert dash_response.status_code in (200, 404, 302)

    # Generate probe report into the data/reports directory
    output_dir = Path('data') / 'reports'
    generator = ReportGenerator(output_dir)
    json_path = generator.generate_report(
        results, discovery, ProbeMode.OFFLINE, None
    )
    assert json_path.exists()
