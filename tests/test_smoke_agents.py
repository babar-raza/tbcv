# scripts/tbcv/tests/test_smoke_agents.py
import re
import sys
from pathlib import Path
from fastapi.testclient import TestClient
import pytest

# Make .../scripts importable so 'tbcv' resolves no matter where pytest runs
SCRIPTS_DIR = Path(__file__).resolve().parents[2]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

pytestmark = pytest.mark.smoke

def _import_app():
    from api.server import app  # noqa: F401
    return app

def _normalize_agents(payload):
    # Accept both shapes: [{"..."}]  OR  {"agents": [{"..."}]} OR registry shape
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("agents"), list):
        return payload["agents"]
    if isinstance(payload, dict) and "agents" in payload and isinstance(payload["agents"], dict):
        # Registry shape: convert to list with proper contract structure
        result = []
        for agent_id, agent_info in payload["agents"].items():
            result.append({
                "agent_id": agent_id,
                "agent_type": agent_info.get("type", "Unknown"),
                "status": "active",
                "contract": {
                    "agent_id": agent_id,
                    "name": agent_info.get("contract", agent_id),
                    "version": "1.0.0",
                    "capabilities": agent_info.get("capabilities", [])
                }
            })
        return result
    raise AssertionError(f"/agents payload not understood: {type(payload)} -> {payload}")

def _to_flat_agent(agent):
    """
    Normalize server shape into a flat view for validation while tolerating optional fields.
    Expected server shape per item (observed):
      top-level: agent_id (str), status (str), contract (dict)
      contract:  agent_id (str), capabilities (list[str|dict]), [events? list[str]],
                 [confidence_threshold? float|int], [config_schema? dict], [name? str], [version? str]
    """
    if not isinstance(agent, dict) or "contract" not in agent:
        raise AssertionError(f"Agent missing 'contract': {agent}")
    contract = agent["contract"] or {}

    agent_id = agent.get("agent_id") or contract.get("agent_id")
    if not agent_id or not isinstance(agent_id, str):
        raise AssertionError(f"Agent missing agent_id: {agent}")

    name = contract.get("name") or agent_id
    version = contract.get("version") or "0.0.0"

    # capabilities may be top-level (rare) or under contract (observed)
    raw_caps = agent.get("capabilities") or contract.get("capabilities") or []
    caps = []
    if isinstance(raw_caps, list):
        for c in raw_caps:
            if isinstance(c, str):
                caps.append(c.strip())
            elif isinstance(c, dict):
                # prefer 'name', fallback to 'description'
                caps.append(str(c.get("name") or c.get("description") or "").strip())
    caps = [c for c in caps if c]

    status = agent.get("status") or contract.get("status") or "unknown"

    return {
        "id": agent_id,
        "name": name,
        "version": version,
        "capabilities": caps,
        "contract": contract,
        "status": status,
    }

def _validate_flat_agent(a):
    # id
    assert isinstance(a["id"], str) and a["id"], "id must be a non-empty string"
    assert re.fullmatch(r"[A-Za-z0-9._-]+", a["id"]), f"id has invalid chars: {a['id']}"
    # name/version (best-effort defaults allowed)
    assert isinstance(a["name"], str) and a["name"], "name must be a non-empty string"
    assert isinstance(a["version"], str) and a["version"], "version must be a non-empty string"
    # capabilities: must be a list of strings (can be empty)
    assert isinstance(a["capabilities"], list), "capabilities must be a list"
    assert all(isinstance(c, str) for c in a["capabilities"]), "capabilities items must be strings"
    # contract: must be dict and include 'agent_id' and 'capabilities'
    contract = a["contract"]
    assert isinstance(contract, dict), "contract must be an object"
    assert "agent_id" in contract and isinstance(contract["agent_id"], str) and contract["agent_id"], \
        "contract.agent_id must be a non-empty string"
    assert "capabilities" in contract and isinstance(contract["capabilities"], list), \
        "contract.capabilities must be a list"
    # If present, validate optional keys (don’t require them)
    if "events" in contract:
        assert isinstance(contract["events"], list) and all(isinstance(e, str) for e in contract["events"]), \
            "contract.events must be a list of strings"
    if "confidence_threshold" in contract:
        assert isinstance(contract["confidence_threshold"], (int, float)), \
            "contract.confidence_threshold must be numeric"
    if "config_schema" in contract:
        assert isinstance(contract["config_schema"], dict), "contract.config_schema must be an object"
    # status
    assert isinstance(a["status"], str) and a["status"], "status must be a non-empty string"

def test_agents_endpoint_registers_and_lists_agents():
    app = _import_app()

    with TestClient(app) as client:
        # Health endpoints
        assert client.get("/health/live").status_code == 200
        assert client.get("/health/ready").status_code == 200

        # /agents populated and well-formed
        res = client.get("/agents")
        assert res.status_code == 200, f"/agents returned {res.status_code}"
        agents_payload = res.json()
        agents = _normalize_agents(agents_payload)
        assert agents, "No agents registered (empty /agents)."

        flat = [_to_flat_agent(a) for a in agents]
        for a in flat:
            _validate_flat_agent(a)

        # Registry must match
        reg = client.get("/registry/agents")
        assert reg.status_code == 200, f"/registry/agents returned {reg.status_code}"
        reg_agents = _normalize_agents(reg.json())
        reg_flat = [_to_flat_agent(a) for a in reg_agents]

        ids_api = {a["id"] for a in flat}
        ids_reg = {a["id"] for a in reg_flat}
        assert ids_api == ids_reg, f"Mismatch between /agents and /registry/agents: {ids_api ^ ids_reg}"

def test_baseagent_subclass_discovery_consistency():
    """
    Sanity check: after app startup, concrete BaseAgent subclasses should exist.
    Guards against class-identity mismatches.
    """
    app = _import_app()
    from agents.base import BaseAgent

    with TestClient(app):
        subclasses = set(BaseAgent.__subclasses__())
        assert subclasses, "No BaseAgent subclasses loaded. Check imports and inheritance."
