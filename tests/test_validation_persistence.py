# Location: scripts/tbcv/tests/test_validation_persistence.py
import sys
from pathlib import Path
from fastapi.testclient import TestClient
import pytest

# Ensure scripts dir importable
SCRIPTS_DIR = Path(__file__).resolve().parents[2]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from api.server import app  # noqa: E402

pytestmark = pytest.mark.smoke

def test_validation_persist_and_consume():
    client = TestClient(app)

    content = """---
title: X
---
no h1 here
link [x](bad url)
code
"""
    # validate -> should persist
    res = client.post("/agents/validate", json={"content": content, "file_path": "tests/foo.md", "run_id": "it-1"})
    assert res.status_code == 200, res.text
    payload = res.json()
    assert payload["success"] is True
    assert payload["file_path"] == "tests/foo.md"
    # fetch notes
    res2 = client.get("/validation-notes", params={"file_path": "tests/foo.md"})
    assert res2.status_code == 200, res2.text
    data = res2.json()
    assert data["count"] >= 1
    assert any(r.get("validation_results") for r in data["results"])

    # enhancer reads notes
    res3 = client.post("/enhance", json={"content": content, "file_path": "tests/foo.md", "severity_floor": "low", "preview_only": True})
    assert res3.status_code == 200, res3.text
    enh = res3.json()
    assert enh["success"] is True
    assert enh["used_validation_issues"] >= 1
