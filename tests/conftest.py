# scripts/tbcv/tests/conftest.py
"""
Enhanced pytest configuration and shared fixtures.
Provides common test utilities for all TBCV tests.
"""
import os
import sys
import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, MagicMock, AsyncMock, patch

# Put the project root (the folder that contains the "tbcv" package) on sys.path.
ROOT = Path(__file__).resolve().parents[1]  # .../scripts/tbcv
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Helpful in code paths that switch behavior by environment
# Must be set BEFORE any imports that load config
os.environ.setdefault("TBCV_ENV", "test")
os.environ.setdefault("OLLAMA_ENABLED", "false")
os.environ.setdefault("OLLAMA_MODEL", "mistral")

# Workaround for Pydantic nested model validation issue
# Set empty dict environment variables that Pydantic expects
os.environ.setdefault("L1_CONFIG", "{}")
os.environ.setdefault("L2_CONFIG", "{}")

# Configure pytest-asyncio
pytest_plugins = ("pytest_asyncio",)


# =============================================================================
# Event Loop Fixture
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# Database Fixtures
# =============================================================================

@pytest.fixture(scope="function")
def db_manager():
    """
    Provide database manager with in-memory SQLite for tests.
    Fresh instance per test function.
    """
    from core.database import db_manager

    # Initialize with in-memory database
    db_manager.init_database()
    yield db_manager

    # Cleanup after test
    try:
        db_manager.close()
    except Exception:
        pass


@pytest.fixture(scope="function")
def db_session(db_manager):
    """Provide a database session for tests."""
    session = db_manager.get_session()
    yield session
    session.close()


# =============================================================================
# API/FastAPI Fixtures
# =============================================================================

@pytest.fixture(scope="function")
def api_client():
    """Provide FastAPI TestClient for API endpoint tests."""
    from fastapi.testclient import TestClient
    from api.server import app

    client = TestClient(app)
    yield client


@pytest.fixture(scope="function")
def async_api_client():
    """Provide async TestClient for async API tests."""
    from httpx import AsyncClient
    from api.server import app

    async def _client():
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    return _client


# =============================================================================
# Agent Fixtures
# =============================================================================

@pytest.fixture(scope="function")
def agent_registry():
    """Provide agent registry for tests."""
    from agents.base import agent_registry
    yield agent_registry


@pytest.fixture(scope="function")
def mock_truth_manager():
    """Provide mocked TruthManagerAgent."""
    mock = AsyncMock()
    mock.agent_id = "truth_manager"
    mock.process_request = AsyncMock(return_value={
        "success": True,
        "found": True,
        "plugin": {
            "id": "test_plugin",
            "name": "Test Plugin",
            "patterns": ["TestPattern"],
            "family": "words"
        }
    })
    return mock


@pytest.fixture(scope="function")
def mock_fuzzy_detector():
    """Provide mocked FuzzyDetectorAgent."""
    mock = AsyncMock()
    mock.agent_id = "fuzzy_detector"
    mock.process_request = AsyncMock(return_value={
        "success": True,
        "detections": [
            {
                "pattern": "Document.Save",
                "confidence": 0.95,
                "position": 100
            }
        ]
    })
    return mock


@pytest.fixture(scope="function")
def mock_content_validator():
    """Provide mocked ContentValidatorAgent with realistic validation responses."""
    mock = AsyncMock()
    mock.agent_id = "content_validator"

    # Mock handle_validate_content to return proper validation structure
    async def mock_validate(params):
        return {
            "success": True,
            "confidence": 0.85,
            "issues_count": 0,
            "issues": [],
            "metrics": {
                "yaml_metrics": {"fields_checked": 5},
                "markdown_metrics": {"sections": 3},
                "code_metrics": {"blocks": 1},
                "family_rules_loaded": True
            },
            "family": params.get("family", "words"),
            "validation_types": params.get("validation_types", [])
        }

    mock.handle_validate_content = AsyncMock(side_effect=mock_validate)
    mock.process_request = AsyncMock(side_effect=mock_validate)
    return mock


@pytest.fixture(scope="function")
def mock_llm_validator():
    """Provide mocked LLMValidatorAgent with NO real LLM calls."""
    mock = AsyncMock()
    mock.agent_id = "llm_validator"
    mock.process_request = AsyncMock(return_value={
        "success": True,
        "llm_response": "Mocked LLM response",
        "issues": []
    })
    return mock


@pytest.fixture(scope="function")
def mock_recommendation_agent():
    """Provide mocked RecommendationAgent."""
    mock = AsyncMock()
    mock.agent_id = "recommendation_agent"
    mock.process_request = AsyncMock(return_value={
        "success": True,
        "recommendations": [
            {
                "id": "rec_001",
                "type": "improvement",
                "confidence": 0.85,
                "suggestion": "Add missing documentation"
            }
        ]
    })
    return mock


@pytest.fixture(scope="function")
def mock_enhancement_agent():
    """Provide mocked EnhancementAgent."""
    mock = AsyncMock()
    mock.agent_id = "enhancement_agent"
    mock.process_request = AsyncMock(return_value={
        "success": True,
        "enhanced_content": "Enhanced content",
        "applied_count": 1,
        "skipped_count": 0
    })
    return mock


@pytest.fixture(scope="function")
def mock_orchestrator():
    """Provide mocked OrchestratorAgent."""
    mock = AsyncMock()
    mock.agent_id = "orchestrator"
    mock.process_request = AsyncMock(return_value={
        "success": True,
        "workflow_id": "wf_001",
        "status": "completed"
    })
    return mock


# =============================================================================
# Sample Data Fixtures
# =============================================================================

@pytest.fixture
def sample_markdown():
    """Sample markdown content for testing."""
    return """---
title: Test Document
family: words
---

# Test Document

This is a test document with sample content.

```csharp
// Sample code
Document doc = new Document();
doc.Save("output.pdf");
```
"""


@pytest.fixture
def sample_yaml_content():
    """Sample YAML-only content for testing."""
    return """---
title: YAML Test
family: words
plugins:
  - word_processor
  - pdf_converter
---
"""


@pytest.fixture
def sample_truth_data():
    """Sample truth data for testing."""
    return {
        "plugins": [
            {
                "id": "word_processor",
                "name": "Word Processor Plugin",
                "slug": "word-processor",
                "description": "Process Word documents",
                "patterns": {
                    "csharp": ["Document.Save", "Document.Load"],
                    "java": ["Document.save", "Document.load"]
                },
                "family": "words",
                "version": "1.0.0",
                "dependencies": [],
                "capabilities": ["read", "write"],
                "plugin_type": "processor"
            },
            {
                "id": "pdf_converter",
                "name": "PDF Converter Plugin",
                "slug": "pdf-converter",
                "description": "Convert to PDF",
                "patterns": {
                    "csharp": ["PdfSaveOptions"]
                },
                "family": "words",
                "version": "1.0.0",
                "dependencies": ["word_processor"],
                "capabilities": ["convert"],
                "plugin_type": "converter"
            }
        ],
        "combinations": [
            {
                "name": "Word to PDF",
                "plugins": ["word_processor", "pdf_converter"],
                "trigger_patterns": ["Document.Save", "PdfSaveOptions"],
                "confidence_boost": 0.1,
                "required_all": True
            }
        ]
    }


@pytest.fixture
def sample_validation_result():
    """Sample validation result for testing."""
    return {
        "validation_id": "val_001",
        "file_path": "test.md",
        "confidence": 0.9,
        "issues_count": 2,
        "issues": [
            {
                "category": "yaml",
                "level": "warning",
                "message": "Missing title",
                "line": 1
            },
            {
                "category": "markdown",
                "level": "info",
                "message": "Consider adding more headers",
                "line": 10
            }
        ],
        "metrics": {
            "lines": 50,
            "words": 200,
            "code_blocks": 1
        }
    }


@pytest.fixture
def sample_recommendations():
    """Sample recommendations for testing."""
    return [
        {
            "id": "rec_001",
            "validation_id": "val_001",
            "type": "improvement",
            "category": "documentation",
            "confidence": 0.85,
            "suggestion": "Add missing documentation section",
            "status": "pending"
        },
        {
            "id": "rec_002",
            "validation_id": "val_001",
            "type": "fix",
            "category": "formatting",
            "confidence": 0.95,
            "suggestion": "Fix code formatting",
            "status": "pending"
        }
    ]


# =============================================================================
# File System Fixtures
# =============================================================================

@pytest.fixture(scope="function")
def temp_dir():
    """Provide temporary directory for tests."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    # Cleanup
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture(scope="function")
def temp_file(temp_dir):
    """Provide temporary file for tests."""
    file_path = temp_dir / "test_file.md"
    file_path.write_text("Test content")
    yield file_path


@pytest.fixture(scope="function")
def sample_files_dir(temp_dir, sample_markdown):
    """Create directory with sample files for testing."""
    files_dir = temp_dir / "sample_files"
    files_dir.mkdir()

    # Create multiple test files
    (files_dir / "file1.md").write_text(sample_markdown)
    (files_dir / "file2.md").write_text(sample_markdown)
    (files_dir / "file3.md").write_text(sample_markdown)

    yield files_dir


# =============================================================================
# Mock Fixtures for External Services
# =============================================================================

@pytest.fixture(scope="function")
def mock_ollama_client():
    """Mock Ollama client - NO real LLM calls."""
    with patch('core.ollama.OllamaClient') as mock:
        mock_instance = MagicMock()
        mock_instance.generate.return_value = {
            "response": "Mocked Ollama response",
            "model": "mistral",
            "done": True
        }
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture(scope="function")
def mock_http_requests():
    """Mock HTTP requests for link validation."""
    with patch('requests.get') as mock:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        mock.return_value = mock_response
        yield mock


@pytest.fixture(scope="function")
def mock_cache_manager():
    """Mock cache manager."""
    with patch('core.cache.cache_manager') as mock:
        mock.get.return_value = None
        mock.set.return_value = True
        mock.exists.return_value = False
        yield mock


# =============================================================================
# Configuration Fixtures
# =============================================================================

@pytest.fixture(scope="function")
def test_config():
    """Provide test configuration."""
    return {
        "llm": {
            "enabled": False,
            "model": "mistral",
            "temperature": 0.7,
            "max_tokens": 1000
        },
        "fuzzy_detector": {
            "similarity_threshold": 0.8,
            "context_window": 50
        },
        "cache": {
            "enabled": True,
            "ttl": 3600
        },
        "performance": {
            "max_concurrent_workflows": 10,
            "worker_pool_size": 4
        }
    }


@pytest.fixture(scope="function")
def mock_settings(test_config):
    """Mock settings for tests."""
    with patch('core.config.get_settings') as mock:
        mock_settings = MagicMock()
        for key, value in test_config.items():
            setattr(mock_settings, key, value)
        mock.return_value = mock_settings
        yield mock_settings


# =============================================================================
# Pytest Markers
# =============================================================================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "live: mark test as requiring live services"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )


# =============================================================================
# Utility Functions for Tests
# =============================================================================

@pytest.fixture
def assert_valid_mcp_message():
    """Utility to assert MCP message validity."""
    def _assert(message):
        assert "type" in message
        assert "timestamp" in message
        if message["type"] in ["request", "response"]:
            assert "id" in message
        if message["type"] == "request":
            assert "method" in message
        return True
    return _assert


@pytest.fixture
def assert_valid_validation_result():
    """Utility to assert validation result validity."""
    def _assert(result):
        assert "confidence" in result
        assert "issues_count" in result
        assert "issues" in result
        assert "metrics" in result
        assert isinstance(result["issues"], list)
        assert result["confidence"] >= 0 and result["confidence"] <= 1
        return True
    return _assert
