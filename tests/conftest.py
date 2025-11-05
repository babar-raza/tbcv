# scripts/tbcv/tests/conftest.py
import os
import sys
import pytest
import asyncio
from pathlib import Path

# Put the project root (the folder that contains the "tbcv" package) on sys.path.
ROOT = Path(__file__).resolve().parents[1]  # .../scripts/tbcv
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Helpful in code paths that switch behavior by environment
os.environ.setdefault("TBCV_ENV", "test")
os.environ.setdefault("OLLAMA_ENABLED", "false")
os.environ.setdefault("OLLAMA_MODEL", "mistral")

# Fix Windows encoding issues - disable problematic encoding fixes for pytest
# if sys.platform == "win32":
#     import codecs
#     import io
#     # Use a more robust approach for Windows encoding
#     try:
#         sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
#         sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
#     except AttributeError:
#         # Fallback if buffer not available
#         sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
#         sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

# Configure pytest-asyncio
pytest_plugins = ("pytest_asyncio",)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def db_manager():
    """Provide database manager for tests."""
    try:
        from core.database import db_manager
        db_manager.init_database()
        yield db_manager
    except ImportError:
        from core.database import db_manager
        db_manager.init_database()
        yield db_manager

@pytest.fixture
async def agent_registry():
    """Provide agent registry for tests."""
    try:
        from agents.base import agent_registry
        yield agent_registry
    except ImportError:
        from agents.base import agent_registry
        yield agent_registry
