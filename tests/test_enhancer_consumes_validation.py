# Location: scripts/tbcv/test_enhancer_consumes_validation.py
from fastapi.testclient import TestClient

def _app():
    from api.server import app
    return app

def test_enhancer_reads_validation_and_applies_style_fix():
    app = _app()
    original = "Intro — with em dash."
    with TestClient(app) as client:
        v = client.post("/agents/validate", json={"content": original, "file_path": "/a/b.md"})
        assert v.status_code == 200, v.text
        e = client.post("/agents/enhance", json={"validation_id": "test", "content": original, "file_path": "/a/b.md", "recommendations": [], "preview": True})
        assert e.status_code == 200, e.text
        data = e.json()
        enhanced = data["enhanced_content"]
        assert "—" not in enhanced
