# Location: scripts/tbcv/agents/__init__.py
"""
Package initializer for the TBCV agents.

Why this file exists:
- Makes `tbcv.agents` a proper Python package so that dynamic discovery
  (used by the API server) can walk and import submodules (e.g., fuzzy_detector,
  content_validator, content_enhancer, orchestrator, truth_manager, code_analyzer,
  llm_validator).
- Keeps imports light to avoid circular import traps at startup.

Notes for maintainers and LLMs:
- We intentionally DO NOT import all agent modules here (e.g., `from . import fuzzy_detector`),
  because the API server performs on-demand discovery/import to register agents.
- Re-exporting minimal symbols from `base.py` is convenient for callers who want
  to do `from tbcv.agents import BaseAgent, agent_registry` without knowing the file layout.

Structure reminder:
  scripts/
    tbcv/
      agents/
        __init__.py        <-- this file
        base.py
        fuzzy_detector.py
        content_validator.py
        content_enhancer.py
        orchestrator.py
        truth_manager.py
        code_analyzer.py
        llm_validator.py
"""

# Re-export the common base types without importing all agent modules.
# This keeps import cost low and avoids circular dependencies.
try:
    from .base import BaseAgent, AgentContract, AgentCapability, agent_registry  # type: ignore
except Exception:
    # If base imports rely on other subsystems not ready yet during very early
    # interpreter bootstrap, we fail softly here. The API server will still
    # discover/instantiate agents by importing concrete modules later.
    BaseAgent = object  # type: ignore
    AgentContract = object  # type: ignore
    AgentCapability = object  # type: ignore
    agent_registry = None  # type: ignore

# Public API of this package. We intentionally do not list concrete agents here.
__all__ = [
    "BaseAgent",
    "AgentContract",
    "AgentCapability",
    "agent_registry",
]
