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

# =============================================================================
# Windows UTF-8 Setup - MUST BE FIRST
# =============================================================================
# Fix Windows cp1252 encoding issues with Unicode symbols (✓, ✗, →, etc.)
# This must happen before any output occurs
if sys.platform == "win32":
    # Set environment variables for Python's default encoding
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

    # Note: Do NOT reconfigure sys.stdout/sys.stderr here as it interferes
    # with pytest's capture mechanism. The PYTHONIOENCODING environment
    # variable handles encoding for new streams, and pytest-capture manages
    # the test output streams properly.

# NOTE: pythonpath = . in pytest.ini handles path setup
# Don't modify sys.path here to avoid duplicate conftest registration

# Helpful in code paths that switch behavior by environment
# Must be set BEFORE any imports that load config
os.environ.setdefault("TBCV_ENV", "test")
os.environ.setdefault("OLLAMA_ENABLED", "false")
os.environ.setdefault("OLLAMA_MODEL", "mistral")

# Workaround for Pydantic nested model validation issue
# Set empty dict environment variables that Pydantic expects
os.environ.setdefault("L1_CONFIG", "{}")
os.environ.setdefault("L2_CONFIG", "{}")

# pytest_plugins moved to root conftest.py per pytest requirements


# =============================================================================
# Event Loop Fixture
# =============================================================================

# Note: We use function-scoped event loops to prevent state contamination
# between tests. pytest-asyncio handles this automatically with asyncio_mode=auto
# in pytest.ini. Do NOT override with session-scoped event_loop as it causes
# "Event loop is closed" errors when running the full test suite.


@pytest.fixture(scope="function", autouse=True)
def reset_global_state(request):
    """Reset global state before and after each test to prevent contamination.

    Skips cleanup for tests marked with 'local_heavy' since they manage their own
    agent registration with module-scoped fixtures.
    """
    # Skip cleanup for local_heavy tests - they manage their own agent lifecycle
    if request.node.get_closest_marker("local_heavy"):
        yield
        return

    _cleanup_global_state()
    yield
    _cleanup_global_state()


def _cleanup_global_state():
    """Helper to thoroughly clean up global state."""
    # Reset live_bus
    try:
        import api.services.live_bus as live_bus_module
        if hasattr(live_bus_module, '_live_bus_instance') and live_bus_module._live_bus_instance:
            live_bus_module._live_bus_instance.enabled = False
        live_bus_module._live_bus_instance = None
    except (ImportError, AttributeError):
        pass

    # Reset agent registry thoroughly
    try:
        from agents.base import agent_registry
        if hasattr(agent_registry, '_agents'):
            agent_registry._agents.clear()
        if hasattr(agent_registry, 'agents') and isinstance(agent_registry.agents, dict):
            agent_registry.agents.clear()
        if hasattr(agent_registry, '_instance'):
            agent_registry._instance = None
    except (ImportError, AttributeError):
        pass

    # Reset CLI agents initialized flag
    try:
        import cli.main as cli_module
        if hasattr(cli_module, '_agents_initialized'):
            cli_module._agents_initialized = False
    except (ImportError, AttributeError):
        pass

    # Reset database manager singleton state
    try:
        from core.database import db_manager
        # Don't fully reset db_manager, but ensure fresh session
        if hasattr(db_manager, '_engine') and db_manager._engine:
            pass  # Keep engine, but sessions will be fresh
    except (ImportError, AttributeError):
        pass

    # Clear any cached settings
    try:
        from core.config import _settings_cache
        if hasattr(_settings_cache, 'clear'):
            _settings_cache.clear()
    except (ImportError, AttributeError):
        pass

    # Reset cache manager state
    try:
        from core.cache import cache_manager
        if hasattr(cache_manager, '_l1_cache'):
            cache_manager._l1_cache.clear() if hasattr(cache_manager._l1_cache, 'clear') else None
    except (ImportError, AttributeError):
        pass

    # Reset ContentEnhancerAgent enhancement cache
    try:
        from agents.content_enhancer import ContentEnhancerAgent
        ContentEnhancerAgent.clear_enhancement_cache()
    except (ImportError, AttributeError):
        pass


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
    # Note: db.close() removed - context managers handle cleanup


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


# =============================================================================
# Taskcard 2: Validation Workflow Test Fixtures
# =============================================================================

@pytest.fixture(scope="function")
def mock_file_system(tmp_path):
    """Temp directory with test.md file for validation testing."""
    test_file = tmp_path / "test.md"
    test_file.write_text("""---
title: Test Document
family: words
---

# Test Document

This is a test document for validation testing.

```csharp
// Sample code
Document doc = new Document();
doc.Save("output.pdf");
```
""", encoding="utf-8")

    return {
        "directory": tmp_path,
        "test_file": test_file,
        "file_path": str(test_file)
    }


@pytest.fixture(scope="function")
def validation_with_file(db_manager, mock_file_system):
    """Validation record pointing to real temp file."""
    from core.database import ValidationStatus

    validation = db_manager.create_validation_result(
        file_path=mock_file_system["file_path"],
        rules_applied=["yaml", "markdown", "code"],
        validation_results={
            "passed": True,
            "confidence": 0.85,
            "issues": []
        },
        notes="Test validation with file",
        severity="low",
        status="pass",
        validation_types=["yaml", "markdown", "code"]
    )

    return {
        "validation": validation,
        "file_path": mock_file_system["file_path"],
        "file_system": mock_file_system
    }


@pytest.fixture(scope="function")
def approved_validation(db_manager, mock_file_system):
    """Validation in approved status with recommendations."""
    from core.database import ValidationStatus, RecommendationStatus

    # Create validation with APPROVED status
    validation = db_manager.create_validation_result(
        file_path=mock_file_system["file_path"],
        rules_applied=["yaml", "markdown", "code"],
        validation_results={
            "passed": True,
            "confidence": 0.90,
            "issues": [
                {"category": "markdown", "level": "info", "message": "Consider adding more headers"}
            ]
        },
        notes="Approved validation for testing",
        severity="low",
        status="approved",
        validation_types=["yaml", "markdown", "code"]
    )

    # Create recommendations for this validation
    rec1 = db_manager.create_recommendation(
        validation_id=validation.id,
        type="fix_format",
        title="Fix formatting",
        description="Fix code block formatting",
        original_content="```csharp",
        proposed_content="```cs",
        status=RecommendationStatus.APPROVED,
        scope="line:10"
    )

    rec2 = db_manager.create_recommendation(
        validation_id=validation.id,
        type="add_info_text",
        title="Add description",
        description="Add plugin description",
        original_content="",
        proposed_content="This plugin allows document processing.",
        status=RecommendationStatus.PENDING,
        scope="line:5"
    )

    return {
        "validation": validation,
        "recommendations": [rec1, rec2],
        "file_path": mock_file_system["file_path"],
        "file_system": mock_file_system
    }


@pytest.fixture(scope="function")
def multiple_validations(db_manager, mock_file_system):
    """Multiple validations for bulk operation testing."""
    from core.database import ValidationStatus

    validations = []

    # Create 3 test files and validations
    for i in range(3):
        test_file = mock_file_system["directory"] / f"test_{i}.md"
        test_file.write_text(f"""---
title: Test Document {i}
family: words
---

# Test Document {i}

Content for test {i}.
""", encoding="utf-8")

        validation = db_manager.create_validation_result(
            file_path=str(test_file),
            rules_applied=["yaml", "markdown"],
            validation_results={"passed": True, "confidence": 0.8 + i * 0.05},
            notes=f"Test validation {i}",
            severity="low",
            status="pass",
            validation_types=["yaml", "markdown"]
        )
        validations.append(validation)

    return {
        "validations": validations,
        "file_system": mock_file_system
    }


@pytest.fixture(scope="function")
def mock_mcp_client():
    """Mock MCP client for testing approve/reject/enhance endpoints."""
    with patch('svc.mcp_server.create_mcp_client') as mock_create:
        mock_client = MagicMock()

        # Default successful response
        mock_client.handle_request.return_value = {
            "result": {
                "success": True,
                "approved_count": 1,
                "rejected_count": 0,
                "enhanced_count": 0,
                "errors": []
            }
        }

        mock_create.return_value = mock_client
        yield mock_client


@pytest.fixture(scope="function")
def mock_websocket_manager():
    """Mock WebSocket connection manager."""
    with patch('api.websocket_endpoints.connection_manager') as mock_manager:
        mock_manager.send_progress_update = AsyncMock()
        yield mock_manager


# =============================================================================
# Taskcard 3: Recommendation Workflow Test Fixtures
# =============================================================================

@pytest.fixture(scope="function")
def recommendations_various_types(db_manager, mock_file_system):
    """Recommendations with link_plugin, fix_format, add_info_text types."""
    from core.database import RecommendationStatus

    # Create a validation to attach recommendations to
    validation = db_manager.create_validation_result(
        file_path=mock_file_system["file_path"],
        rules_applied=["yaml", "markdown", "code"],
        validation_results={"passed": True, "confidence": 0.85},
        notes="Validation for various recommendation types",
        severity="low",
        status="pass",
        validation_types=["yaml", "markdown", "code"]
    )

    recommendations = []

    # Create link_plugin type recommendation
    rec_link = db_manager.create_recommendation(
        validation_id=validation.id,
        type="link_plugin",
        title="Link to Plugin",
        description="Add link to the referenced plugin documentation",
        original_content="See plugin docs",
        proposed_content="See [Plugin Documentation](/plugins/word-processor)",
        status=RecommendationStatus.PENDING,
        scope="line:15"
    )
    recommendations.append(rec_link)

    # Create fix_format type recommendation
    rec_format = db_manager.create_recommendation(
        validation_id=validation.id,
        type="fix_format",
        title="Fix Code Formatting",
        description="Fix code block language identifier",
        original_content="```csharp",
        proposed_content="```cs",
        status=RecommendationStatus.PENDING,
        scope="line:20"
    )
    recommendations.append(rec_format)

    # Create add_info_text type recommendation
    rec_info = db_manager.create_recommendation(
        validation_id=validation.id,
        type="add_info_text",
        title="Add Plugin Description",
        description="Add description text for the plugin",
        original_content="",
        proposed_content="This plugin enables document conversion to PDF format.",
        status=RecommendationStatus.APPROVED,
        scope="line:5"
    )
    recommendations.append(rec_info)

    return {
        "validation": validation,
        "recommendations": recommendations,
        "file_path": mock_file_system["file_path"],
        "file_system": mock_file_system
    }


@pytest.fixture(scope="function")
def approved_recommendation(db_manager, approved_validation):
    """Single approved recommendation ready to apply."""
    from core.database import RecommendationStatus

    # The approved_validation fixture already has recommendations,
    # but we'll create a specific one that's clearly approved and ready
    rec = db_manager.create_recommendation(
        validation_id=approved_validation["validation"].id,
        type="fix_format",
        title="Approved Fix Ready to Apply",
        description="This recommendation is approved and ready to apply",
        original_content="old content",
        proposed_content="new improved content",
        status=RecommendationStatus.APPROVED,
        scope="line:8",
        confidence=0.95
    )

    return {
        "recommendation": rec,
        "validation": approved_validation["validation"],
        "file_path": approved_validation["file_path"],
        "file_system": approved_validation["file_system"]
    }


@pytest.fixture(scope="function")
def rejected_recommendation(db_manager, mock_file_system):
    """Recommendation in rejected status."""
    from core.database import RecommendationStatus

    # Create a validation first
    validation = db_manager.create_validation_result(
        file_path=mock_file_system["file_path"],
        rules_applied=["yaml", "markdown"],
        validation_results={"passed": True, "confidence": 0.80},
        notes="Validation with rejected recommendation",
        severity="low",
        status="pass",
        validation_types=["yaml", "markdown"]
    )

    rec = db_manager.create_recommendation(
        validation_id=validation.id,
        type="fix_format",
        title="Rejected Recommendation",
        description="This recommendation was rejected by reviewer",
        original_content="original",
        proposed_content="proposed change",
        status=RecommendationStatus.REJECTED,
        scope="line:10"
    )

    return {
        "recommendation": rec,
        "validation": validation,
        "file_path": mock_file_system["file_path"],
        "file_system": mock_file_system
    }


@pytest.fixture(scope="function")
def multiple_recommendations(db_manager, mock_file_system):
    """Multiple recommendations for bulk operation testing."""
    from core.database import RecommendationStatus

    # Create a validation
    validation = db_manager.create_validation_result(
        file_path=mock_file_system["file_path"],
        rules_applied=["yaml", "markdown"],
        validation_results={"passed": True},
        notes="Validation with multiple recommendations",
        severity="low",
        status="pass",
        validation_types=["yaml", "markdown"]
    )

    recommendations = []
    for i in range(5):
        rec = db_manager.create_recommendation(
            validation_id=validation.id,
            type="fix_format" if i % 2 == 0 else "add_info_text",
            title=f"Recommendation {i}",
            description=f"Description for recommendation {i}",
            original_content=f"original_{i}",
            proposed_content=f"proposed_{i}",
            status=RecommendationStatus.PENDING,
            scope=f"line:{10 + i}"
        )
        recommendations.append(rec)

    return {
        "validation": validation,
        "recommendations": recommendations,
        "file_path": mock_file_system["file_path"],
        "file_system": mock_file_system
    }


# =============================================================================
# Taskcard 4: Workflow Operations Test Fixtures
# =============================================================================

@pytest.fixture(scope="function")
def test_directory(tmp_path):
    """Directory with multiple .md files for workflow testing."""
    # Create main directory with test files
    for i in range(5):
        test_file = tmp_path / f"document_{i}.md"
        test_file.write_text(f"""---
title: Test Document {i}
family: words
---

# Test Document {i}

This is test document {i} for workflow testing.

## Features

- Feature {i}.1
- Feature {i}.2
- Feature {i}.3

```csharp
// Code sample {i}
Document doc = new Document();
doc.Save("output_{i}.pdf");
```
""", encoding="utf-8")

    # Create a subdirectory with more files
    subdir = tmp_path / "subdocs"
    subdir.mkdir()
    for i in range(3):
        sub_file = subdir / f"subdoc_{i}.md"
        sub_file.write_text(f"""---
title: Subdocument {i}
family: cells
---

# Subdocument {i}

Content for subdocument {i}.
""", encoding="utf-8")

    return {
        "directory": tmp_path,
        "path": str(tmp_path),
        "file_count": 5,
        "subdir": subdir,
        "total_files": 8
    }


@pytest.fixture(scope="function")
def running_workflow(db_manager):
    """Workflow in running state with progress."""
    from core.database import WorkflowState

    workflow = db_manager.create_workflow(
        workflow_type="batch_validation",
        input_params={
            "directory_path": "/test/path",
            "file_pattern": "*.md",
            "max_workers": 4
        },
        metadata={
            "source": "test",
            "file_count": 10
        }
    )

    # Update to running state with progress
    db_manager.update_workflow(
        workflow_id=workflow.id,
        state="running",
        total_steps=10,
        current_step=5,
        progress_percent=50
    )

    # Refresh to get updated state
    workflow = db_manager.get_workflow(workflow.id)

    return {
        "workflow": workflow,
        "workflow_id": workflow.id
    }


@pytest.fixture(scope="function")
def completed_workflow(db_manager):
    """Workflow in completed state."""
    from core.database import WorkflowState
    from datetime import datetime, timezone

    workflow = db_manager.create_workflow(
        workflow_type="directory_validation",
        input_params={
            "directory_path": "/test/completed",
            "file_pattern": "*.md"
        },
        metadata={
            "source": "test",
            "file_count": 5
        }
    )

    # Update to completed state
    db_manager.update_workflow(
        workflow_id=workflow.id,
        state="completed",
        total_steps=5,
        current_step=5,
        progress_percent=100
    )

    # Refresh to get updated state
    workflow = db_manager.get_workflow(workflow.id)

    return {
        "workflow": workflow,
        "workflow_id": workflow.id
    }


@pytest.fixture(scope="function")
def multiple_workflows(db_manager):
    """Multiple workflows for bulk operation testing."""
    from core.database import WorkflowState

    workflows = []

    # Create workflows in various states
    states = ["pending", "running", "completed", "failed", "completed"]
    for i, state in enumerate(states):
        workflow = db_manager.create_workflow(
            workflow_type="batch_validation",
            input_params={
                "directory_path": f"/test/path_{i}",
                "file_pattern": "*.md"
            },
            metadata={
                "source": "test",
                "index": i
            }
        )

        if state != "pending":
            db_manager.update_workflow(
                workflow_id=workflow.id,
                state=state,
                progress_percent=100 if state == "completed" else 50
            )

        workflow = db_manager.get_workflow(workflow.id)
        workflows.append(workflow)

    return {
        "workflows": workflows,
        "workflow_ids": [w.id for w in workflows]
    }


# =============================================================================
# Taskcard 5: Enhancement Workflow Test Fixtures
# =============================================================================

@pytest.fixture(scope="function")
def enhanced_validation(db_manager, mock_file_system):
    """Validation that has been enhanced with content changes."""
    from core.database import ValidationStatus, RecommendationStatus

    # Create validation in ENHANCED status
    validation = db_manager.create_validation_result(
        file_path=mock_file_system["file_path"],
        rules_applied=["yaml", "markdown", "code"],
        validation_results={
            "passed": True,
            "confidence": 0.95,
            "issues": []
        },
        notes="Enhanced validation for testing",
        severity="low",
        status="enhanced",
        validation_types=["yaml", "markdown", "code"],
        content="""---
title: Test Document
family: words
---

# Test Document

This is a test document for validation testing.

```csharp
// Sample code
Document doc = new Document();
doc.Save("output.pdf");
```
"""
    )

    # Create applied recommendations
    rec = db_manager.create_recommendation(
        validation_id=validation.id,
        type="fix_format",
        title="Applied Enhancement",
        description="This recommendation was applied",
        original_content="```csharp",
        proposed_content="```cs",
        status=RecommendationStatus.APPLIED,
        scope="line:10"
    )

    return {
        "validation": validation,
        "validation_id": validation.id,
        "recommendations": [rec],
        "file_path": mock_file_system["file_path"],
        "file_system": mock_file_system
    }


@pytest.fixture(scope="function")
def validation_ready_for_enhancement(db_manager, mock_file_system):
    """Approved validation with approved recommendations ready for enhancement."""
    from core.database import RecommendationStatus

    # Read the test file content
    original_content = mock_file_system["test_file"].read_text(encoding="utf-8")

    # Create approved validation with content stored
    validation = db_manager.create_validation_result(
        file_path=mock_file_system["file_path"],
        rules_applied=["yaml", "markdown", "code"],
        validation_results={
            "passed": True,
            "confidence": 0.88,
            "issues": [
                {"category": "code", "level": "warning", "message": "Code block language mismatch"}
            ]
        },
        notes="Validation ready for enhancement",
        severity="low",
        status="approved",
        validation_types=["yaml", "markdown", "code"],
        content=original_content
    )

    # Create approved recommendations ready to apply
    recs = []
    rec1 = db_manager.create_recommendation(
        validation_id=validation.id,
        type="fix_format",
        title="Fix Code Block",
        description="Change csharp to cs for consistency",
        original_content="```csharp",
        proposed_content="```cs",
        status=RecommendationStatus.APPROVED,
        scope="line:10"
    )
    recs.append(rec1)

    rec2 = db_manager.create_recommendation(
        validation_id=validation.id,
        type="add_info_text",
        title="Add Comment",
        description="Add explanatory comment",
        original_content="// Sample code",
        proposed_content="// Sample code demonstrating document creation",
        status=RecommendationStatus.APPROVED,
        scope="line:11"
    )
    recs.append(rec2)

    return {
        "validation": validation,
        "validation_id": validation.id,
        "recommendations": recs,
        "recommendation_ids": [r.id for r in recs],
        "file_path": mock_file_system["file_path"],
        "file_system": mock_file_system,
        "original_content": original_content
    }


@pytest.fixture(scope="function")
def multiple_validations_for_enhancement(db_manager, mock_file_system):
    """Multiple approved validations for batch enhancement testing."""
    from core.database import RecommendationStatus

    validations = []

    # Create multiple test files and validations
    for i in range(3):
        test_file = mock_file_system["directory"] / f"enhance_test_{i}.md"
        content = f"""---
title: Enhancement Test {i}
family: words
---

# Enhancement Test Document {i}

This is test document {i} for batch enhancement.

```csharp
// Code sample {i}
Document doc{i} = new Document();
doc{i}.Save("output_{i}.pdf");
```
"""
        test_file.write_text(content, encoding="utf-8")

        validation = db_manager.create_validation_result(
            file_path=str(test_file),
            rules_applied=["yaml", "markdown", "code"],
            validation_results={"passed": True, "confidence": 0.85 + i * 0.03},
            notes=f"Validation {i} for batch enhancement",
            severity="low",
            status="approved",
            validation_types=["yaml", "markdown", "code"],
            content=content
        )

        # Add an approved recommendation for each
        rec = db_manager.create_recommendation(
            validation_id=validation.id,
            type="fix_format",
            title=f"Enhancement {i}",
            description=f"Enhancement recommendation {i}",
            original_content=f"```csharp",
            proposed_content=f"```cs",
            status=RecommendationStatus.APPROVED,
            scope="line:12"
        )

        validations.append({
            "validation": validation,
            "validation_id": validation.id,
            "recommendation": rec,
            "file_path": str(test_file),
            "content": content
        })

    return {
        "validations": validations,
        "validation_ids": [v["validation_id"] for v in validations],
        "file_system": mock_file_system
    }


# =============================================================================
# Task Card 1: WebSocket Test Fixtures
# =============================================================================

@pytest.fixture(scope="function")
def websocket_client(api_client):
    """
    Provide WebSocket client for testing WebSocket connections.
    Uses the TestClient's websocket_connect context manager.
    """
    from fastapi.testclient import TestClient
    from api.server import app

    client = TestClient(app)

    def connect(path: str):
        """Connect to WebSocket endpoint and return context manager."""
        return client.websocket_connect(path)

    return connect


@pytest.fixture(scope="function")
def workflow_websocket_client(running_workflow):
    """
    Provide WebSocket client pre-configured for a running workflow.
    Returns a context manager for the WebSocket connection.
    """
    from fastapi.testclient import TestClient
    from api.server import app

    client = TestClient(app)
    workflow_id = running_workflow["workflow_id"]

    def connect():
        """Connect to workflow WebSocket endpoint."""
        return client.websocket_connect(f"/ws/{workflow_id}")

    return {
        "connect": connect,
        "workflow_id": workflow_id,
        "workflow": running_workflow["workflow"]
    }


# =============================================================================
# Task Card 2: Modal Form Test Fixtures
# =============================================================================

@pytest.fixture(scope="function")
def windows_test_path(tmp_path):
    """Create a test file with Windows-style path for modal testing."""
    test_file = tmp_path / "windows_test.md"
    test_file.write_text("""---
title: Windows Path Test
family: words
---

# Windows Path Test Document

This document tests Windows path handling.
""", encoding="utf-8")

    # Return both the actual path and a Windows-style representation
    return {
        "actual_path": test_file,
        "file_path": str(test_file),
        # Simulate Windows path format
        "windows_path": str(test_file).replace("/", "\\") if "/" in str(test_file) else str(test_file)
    }


@pytest.fixture(scope="function")
def unix_test_path(tmp_path):
    """Create a test file with Unix-style path for modal testing."""
    test_file = tmp_path / "unix_test.md"
    test_file.write_text("""---
title: Unix Path Test
family: words
---

# Unix Path Test Document

This document tests Unix path handling.
""", encoding="utf-8")

    return {
        "actual_path": test_file,
        "file_path": str(test_file),
        # Ensure Unix-style forward slashes
        "unix_path": str(test_file).replace("\\", "/")
    }


# =============================================================================
# Task Card 4: Bulk Action Test Fixtures (Extended)
# =============================================================================

@pytest.fixture(scope="function")
def five_validations(db_manager, mock_file_system):
    """Create exactly 5 validations for bulk action testing."""
    from core.database import ValidationStatus

    validations = []

    for i in range(5):
        test_file = mock_file_system["directory"] / f"bulk_test_{i}.md"
        test_file.write_text(f"""---
title: Bulk Test Document {i}
family: words
---

# Bulk Test Document {i}

Content for bulk test {i}.
""", encoding="utf-8")

        validation = db_manager.create_validation_result(
            file_path=str(test_file),
            rules_applied=["yaml", "markdown"],
            validation_results={"passed": True, "confidence": 0.80 + i * 0.03},
            notes=f"Bulk test validation {i}",
            severity="low",
            status="pass",
            validation_types=["yaml", "markdown"]
        )
        validations.append(validation)

    return {
        "validations": validations,
        "validation_ids": [v.id for v in validations],
        "file_system": mock_file_system
    }


@pytest.fixture(scope="function")
def five_recommendations(db_manager, mock_file_system):
    """Create 5 recommendations for bulk action testing."""
    from core.database import RecommendationStatus

    # Create a validation to attach recommendations to
    validation = db_manager.create_validation_result(
        file_path=mock_file_system["file_path"],
        rules_applied=["yaml", "markdown"],
        validation_results={"passed": True},
        notes="Validation for 5 recommendations",
        severity="low",
        status="pass",
        validation_types=["yaml", "markdown"]
    )

    recommendations = []
    for i in range(5):
        rec = db_manager.create_recommendation(
            validation_id=validation.id,
            type="fix_format" if i % 2 == 0 else "add_info_text",
            title=f"Bulk Recommendation {i}",
            description=f"Description for bulk recommendation {i}",
            original_content=f"original_{i}",
            proposed_content=f"proposed_{i}",
            status=RecommendationStatus.PENDING,
            scope=f"line:{10 + i}"
        )
        recommendations.append(rec)

    return {
        "validation": validation,
        "recommendations": recommendations,
        "recommendation_ids": [r.id for r in recommendations],
        "file_system": mock_file_system
    }


@pytest.fixture(scope="function")
def five_workflows(db_manager):
    """Create 5 workflows for bulk action testing."""
    from core.database import WorkflowState

    workflows = []
    states = ["pending", "running", "completed", "failed", "completed"]

    for i, state in enumerate(states):
        workflow = db_manager.create_workflow(
            workflow_type="batch_validation",
            input_params={
                "directory_path": f"/test/bulk_path_{i}",
                "file_pattern": "*.md"
            },
            metadata={
                "source": "bulk_test",
                "index": i
            }
        )

        if state != "pending":
            db_manager.update_workflow(
                workflow_id=workflow.id,
                state=state,
                progress_percent=100 if state == "completed" else 50
            )

        workflow = db_manager.get_workflow(workflow.id)
        workflows.append(workflow)

    return {
        "workflows": workflows,
        "workflow_ids": [w.id for w in workflows]
    }


# =============================================================================
# Task Card 5: Navigation & E2E Test Fixtures
# =============================================================================

@pytest.fixture(scope="function")
def validation_ready_for_enhance(db_manager, mock_file_system):
    """Create an approved validation ready for enhancement."""
    from core.database import RecommendationStatus

    original_content = mock_file_system["test_file"].read_text(encoding="utf-8")

    validation = db_manager.create_validation_result(
        file_path=mock_file_system["file_path"],
        rules_applied=["yaml", "markdown", "code"],
        validation_results={
            "passed": True,
            "confidence": 0.88,
            "issues": [{"category": "code", "level": "warning", "message": "Minor issue"}]
        },
        notes="Validation ready for enhancement",
        severity="low",
        status="approved",
        validation_types=["yaml", "markdown", "code"],
        content=original_content
    )

    # Create approved recommendations ready to apply
    recs = []
    rec1 = db_manager.create_recommendation(
        validation_id=validation.id,
        type="fix_format",
        title="Fix Code Block",
        description="Change csharp to cs",
        original_content="```csharp",
        proposed_content="```cs",
        status=RecommendationStatus.APPROVED,
        scope="line:10"
    )
    recs.append(rec1)

    return {
        "validation": validation,
        "validation_id": validation.id,
        "recommendations": recs,
        "recommendation_ids": [r.id for r in recs],
        "file_path": mock_file_system["file_path"],
        "file_system": mock_file_system,
        "original_content": original_content
    }


@pytest.fixture(scope="function")
def complete_validation_chain(db_manager, mock_file_system):
    """
    Create a complete validation chain for E2E testing:
    - Workflow with validations
    - Validations with recommendations
    - Mix of statuses
    """
    from core.database import RecommendationStatus, WorkflowState

    # Create workflow
    workflow = db_manager.create_workflow(
        workflow_type="batch_validation",
        input_params={"directory_path": str(mock_file_system["directory"])},
        metadata={"source": "e2e_test"}
    )

    validations = []
    all_recommendations = []

    # Create 3 validations with different statuses
    statuses = ["pass", "approved", "enhanced"]
    for i, status in enumerate(statuses):
        test_file = mock_file_system["directory"] / f"chain_test_{i}.md"
        content = f"""---
title: Chain Test {i}
family: words
---

# Chain Test Document {i}

Content for E2E chain test {i}.
"""
        test_file.write_text(content, encoding="utf-8")

        validation = db_manager.create_validation_result(
            file_path=str(test_file),
            rules_applied=["yaml", "markdown"],
            validation_results={"passed": True, "confidence": 0.85 + i * 0.05},
            notes=f"Chain validation {i}",
            severity="low",
            status=status,
            validation_types=["yaml", "markdown"],
            workflow_id=workflow.id,
            content=content
        )
        validations.append(validation)

        # Create recommendations for each validation
        rec_statuses = [RecommendationStatus.PENDING, RecommendationStatus.APPROVED, RecommendationStatus.APPLIED]
        for j, rec_status in enumerate(rec_statuses[:2]):  # 2 recs per validation
            rec = db_manager.create_recommendation(
                validation_id=validation.id,
                type="fix_format",
                title=f"Rec {i}-{j}",
                description=f"Recommendation {j} for validation {i}",
                original_content=f"old_{i}_{j}",
                proposed_content=f"new_{i}_{j}",
                status=rec_status,
                scope=f"line:{5 + j}"
            )
            all_recommendations.append(rec)

    # Update workflow to completed
    db_manager.update_workflow(
        workflow_id=workflow.id,
        state="completed",
        progress_percent=100
    )
    workflow = db_manager.get_workflow(workflow.id)

    return {
        "workflow": workflow,
        "workflow_id": workflow.id,
        "validations": validations,
        "validation_ids": [v.id for v in validations],
        "recommendations": all_recommendations,
        "recommendation_ids": [r.id for r in all_recommendations],
        "file_system": mock_file_system
    }
