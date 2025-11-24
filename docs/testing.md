# Testing

## Overview

TBCV includes comprehensive test suites covering unit tests, integration tests, performance tests, and end-to-end workflows. Tests ensure system reliability, validate agent interactions, and measure performance characteristics.

## Test Structure

### Directory Layout
```
tests/
├── __init__.py
├── conftest.py                    # Pytest configuration and fixtures
├── run_all_tests.py              # Test runner script
├── test_cli_web_parity.py        # CLI vs API parity tests
├── test_endpoints_live.py        # Live API endpoint tests
├── test_endpoints_offline.py     # Offline API endpoint tests
├── test_enhancer_consumes_validation.py  # Enhancement workflow tests
├── test_everything.py             # Comprehensive system tests
├── test_framework.py              # Test framework utilities
├── test_full_stack_local.py       # Full stack local tests
├── test_fuzzy_logic.py            # Fuzzy detection algorithm tests
├── test_generic_validator.py      # Generic validation tests
├── test_idempotence_and_schemas.py # Idempotency and schema tests
├── test_performance.py            # Performance benchmark tests
├── test_recommendations.py        # Recommendation system tests
├── test_smoke_agents.py           # Agent smoke tests
├── test_truth_validation.py       # Truth validation tests
├── fixtures/                      # Test data fixtures
│   ├── multi_plugin_content.md
│   ├── truths_and_rules_test.md
│   └── yaml_only_content.md
└── reports/                       # Test reports
    └── comprehensive_test_report.json
```

## Running Tests

### All Tests
```bash
# Run complete test suite
pytest tests/

# With coverage report
pytest tests/ --cov=tbcv --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_smoke_agents.py -v

# Run specific test
pytest tests/test_fuzzy_logic.py::test_fuzzy_detection -v
```

### Test Categories

#### Unit Tests
```bash
# Agent-specific tests
pytest tests/test_smoke_agents.py
pytest tests/test_fuzzy_logic.py
pytest tests/test_truth_validation.py

# Core component tests
pytest tests/test_framework.py
pytest tests/test_idempotence_and_schemas.py
```

#### Integration Tests
```bash
# API endpoint tests
pytest tests/test_endpoints_live.py
pytest tests/test_endpoints_offline.py

# CLI tests
pytest tests/test_cli_web_parity.py

# Workflow tests
pytest tests/test_full_stack_local.py
pytest tests/test_enhancer_consumes_validation.py
```

#### Performance Tests
```bash
# Performance benchmarks
pytest tests/test_performance.py --benchmark

# Memory profiling
pytest tests/test_performance.py --memory

# Load testing
pytest tests/test_performance.py --load
```

#### End-to-End Tests
```bash
# Full system tests
pytest tests/test_everything.py

# Recommendation workflow
pytest tests/test_recommendations.py

# Generic validation
pytest tests/test_generic_validator.py
```

### Custom Test Runner
```bash
# Use the custom test runner
python tests/run_all_tests.py

# With options
python tests/run_all_tests.py --verbose --coverage --performance
```

## Test Configuration

### pytest.ini
```ini
[tool:pytest.ini_options]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --strict-markers
    --strict-config
    --verbose
    --cov=tbcv
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=95
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    performance: marks tests as performance tests
asyncio_mode = auto
```

### Coverage Configuration
```ini
[tool.coverage.run]
source = tbcv
omit =
    */tests/*
    */test_*.py
    */__pycache__/*
    */conftest.py

[tool.coverage.report]
exclude_lines =
    pragma: no cover
    def __repr__
    if self.debug:
    if settings.DEBUG
    raise AssertionError
    raise NotImplementedError
    if 0:
    if __name__ == .__main__.:
    class .*\\bProtocol\\):
    @(abc\\.)?abstractmethod
```

## Test Fixtures

### conftest.py
```python
import pytest
import asyncio
from pathlib import Path
from core.database import db_manager
from agents.base import agent_registry

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Initialize test database."""
    db_manager.init_database()
    yield
    # Cleanup after tests

@pytest.fixture(scope="function")
async def initialized_agents():
    """Initialize agents for testing."""
    from core.config import get_settings
    settings = get_settings()

    # Register test agents
    yield
    # Cleanup agents

@pytest.fixture
def sample_markdown():
    """Sample markdown content for testing."""
    return """
# Sample Document

This is a test document with some content.

```csharp
// Sample code
Document doc = new Document();
doc.Save("output.pdf");
```
"""

@pytest.fixture
def sample_truth_data():
    """Sample truth data for testing."""
    return {
        "plugin_name": "Aspose.Words",
        "patterns": ["Document.Save", "Document.Load"],
        "family": "words"
    }
```

## Writing Tests

### Unit Test Example
```python
import pytest
from agents.fuzzy_detector import FuzzyDetectorAgent

class TestFuzzyDetector:
    def test_exact_match(self):
        """Test exact pattern matching."""
        agent = FuzzyDetectorAgent("test_detector")
        content = "Document.Save(filename)"
        patterns = ["Document.Save"]

        result = agent.detect_plugins(content, patterns)

        assert len(result) == 1
        assert result[0]["pattern"] == "Document.Save"
        assert result[0]["confidence"] > 0.9

    def test_fuzzy_match(self):
        """Test fuzzy pattern matching."""
        agent = FuzzyDetectorAgent("test_detector")
        content = "doc.Save(file)"  # Slight variation
        patterns = ["Document.Save"]

        result = agent.detect_plugins(content, patterns)

        assert len(result) == 1
        assert result[0]["confidence"] > 0.7  # Fuzzy match confidence

    @pytest.mark.asyncio
    async def test_async_detection(self):
        """Test asynchronous plugin detection."""
        agent = FuzzyDetectorAgent("test_detector")
        content = "Document doc = new Document(); doc.Save();"

        result = await agent.process_request("detect_plugins", {
            "content": content,
            "patterns": ["Document.Save"]
        })

        assert result["success"] is True
        assert len(result["detections"]) > 0
```

### Integration Test Example
```python
import pytest
from fastapi.testclient import TestClient
from tbcv.api.server import app

class TestAPIEndpoints:
    def setup_method(self):
        """Setup test client."""
        self.client = TestClient(app)

    def test_health_check(self):
        """Test health check endpoint."""
        response = self.client.get("/health/live")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "alive"
        assert "timestamp" in data

    def test_validation_endpoint(self):
        """Test content validation endpoint."""
        payload = {
            "content": "# Test Document\n\nSome content.",
            "file_path": "test.md",
            "family": "words"
        }

        response = self.client.post("/api/validate", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "validation_result" in data
        assert data["validation_result"]["content_validation"]["confidence"] >= 0

    @pytest.mark.asyncio
    async def test_workflow_creation(self):
        """Test workflow creation and monitoring."""
        payload = {
            "directory_path": "./tests/fixtures",
            "file_pattern": "*.md",
            "max_workers": 2,
            "family": "words"
        }

        response = self.client.post("/workflows/validate-directory", json=payload)
        assert response.status_code == 200

        data = response.json()
        workflow_id = data["workflow_id"]

        # Check workflow status
        status_response = self.client.get(f"/workflows/{workflow_id}")
        assert status_response.status_code == 200

        status_data = status_response.json()
        assert status_data["state"] in ["pending", "running", "completed"]
```

### Performance Test Example
```python
import pytest
import time
from agents.content_validator import ContentValidatorAgent

class TestPerformance:
    @pytest.mark.benchmark
    def test_validation_performance(self, benchmark, sample_markdown):
        """Benchmark content validation performance."""
        agent = ContentValidatorAgent("perf_test")

        def validate():
            return agent.validate_content(sample_markdown, "test.md")

        result = benchmark(validate)

        # Assert performance requirements
        assert result.stats.mean < 1.0  # Less than 1 second average
        assert result.stats.max < 5.0   # Less than 5 seconds max

    @pytest.mark.memory
    def test_memory_usage(self, sample_markdown):
        """Test memory usage during validation."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        agent = ContentValidatorAgent("memory_test")
        agent.validate_content(sample_markdown, "test.md")

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Assert memory usage is reasonable
        assert memory_increase < 50  # Less than 50MB increase

    @pytest.mark.load
    def test_concurrent_validations(self):
        """Test concurrent validation handling."""
        import asyncio
        import aiohttp

        async def validate_concurrent():
            async with aiohttp.ClientSession() as session:
                tasks = []
                for i in range(10):
                    payload = {
                        "content": f"# Document {i}\n\nContent {i}",
                        "file_path": f"test{i}.md"
                    }
                    tasks.append(session.post(
                        "http://localhost:8080/api/validate",
                        json=payload
                    ))

                responses = await asyncio.gather(*tasks)
                return [r.status for r in responses]

        statuses = asyncio.run(validate_concurrent())
        assert all(status == 200 for status in statuses)
```

## Test Data Management

### Fixtures Directory
```
tests/fixtures/
├── multi_plugin_content.md     # Content with multiple plugins
├── truths_and_rules_test.md   # Truth data validation content
├── yaml_only_content.md       # YAML-only test content
└── large_document.md          # Large document for performance testing
```

### Generating Test Data
```python
def generate_test_content(num_plugins=5, content_length=1000):
    """Generate test content with specified characteristics."""
    plugins = [
        "Document.Save", "Document.Load", "Workbook.Save",
        "Presentation.Save", "PdfDocument.Save"
    ]

    content = "# Test Document\n\n"

    # Add plugin usage
    for i in range(num_plugins):
        plugin = plugins[i % len(plugins)]
        content += f"```csharp\n// Using {plugin}\nvar doc = new Document();\ndoc.{plugin.split('.')[1]}();\n```\n\n"

    # Pad content to desired length
    while len(content) < content_length:
        content += "This is additional content to reach desired length.\n"

    return content
```

## Continuous Integration

### GitHub Actions Example
```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, "3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -e .[dev]

      - name: Run tests
        run: |
          pytest tests/ --cov=tbcv --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: Run tests
        entry: pytest tests/ -x
        language: system
        pass_filenames: false
        always_run: true

  - repo: local
    hooks:
      - id: mypy
        name: Type checking
        entry: mypy tbcv/
        language: system
        pass_filenames: false

  - repo: local
    hooks:
      - id: black
        name: Code formatting
        entry: black tbcv/ tests/
        language: system
        pass_filenames: false
```

## Test Reporting

### Coverage Reports
```bash
# HTML coverage report
pytest tests/ --cov=tbcv --cov-report=html
open htmlcov/index.html

# Terminal coverage
pytest tests/ --cov=tbcv --cov-report=term-missing

# XML for CI
pytest tests/ --cov=tbcv --cov-report=xml
```

### Performance Reports
```bash
# Benchmark report
pytest tests/test_performance.py --benchmark --benchmark-json=benchmark.json

# Memory profiling
pytest tests/test_performance.py --memory --memory-report
```

### Custom Reports
```python
# tests/generate_report.py
import json
import pytest
from pathlib import Path

def generate_comprehensive_report(results):
    """Generate comprehensive test report."""
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "summary": {
            "total_tests": results["summary"]["num_tests"],
            "passed": results["summary"]["passed"],
            "failed": results["summary"]["failed"],
            "skipped": results["summary"]["skipped"],
            "duration": results["summary"]["duration"]
        },
        "coverage": results.get("coverage", {}),
        "performance": results.get("performance", {}),
        "details": results["tests"]
    }

    Path("tests/reports").mkdir(exist_ok=True)
    with open("tests/reports/comprehensive_test_report.json", "w") as f:
        json.dump(report, f, indent=2)

    return report
```

## Debugging Tests

### Verbose Output
```bash
# Detailed test output
pytest tests/test_fuzzy_logic.py -v -s

# Debug specific test
pytest tests/test_fuzzy_logic.py::TestFuzzyDetector::test_exact_match -v -s --pdb
```

### Logging in Tests
```python
import logging

def test_with_logging(caplog):
    """Test with log capture."""
    caplog.set_level(logging.DEBUG)

    # Test code that logs
    agent = FuzzyDetectorAgent("test")
    agent.detect_plugins("content", ["pattern"])

    # Assert logs
    assert "Detected plugin" in caplog.text
    assert caplog.records[0].levelname == "INFO"
```

### Mocking External Services
```python
import pytest
from unittest.mock import patch, MagicMock

def test_with_mocked_ollama():
    """Test LLM validator with mocked Ollama."""
    with patch('core.ollama.OllamaClient') as mock_client:
        mock_client.return_value.generate.return_value = "Mocked response"

        agent = LLMValidatorAgent("test")
        result = agent.validate_with_llm("test content")

        assert result["response"] == "Mocked response"
        mock_client.return_value.generate.assert_called_once()
```

## Test Maintenance

### Keeping Tests Current
```bash
# Update test snapshots
pytest tests/ --snapshot-update

# Regenerate fixtures
python tests/generate_fixtures.py

# Update expected results
pytest tests/ --update-expected
```

### Test Organization
- **Unit tests**: Test individual functions/classes
- **Integration tests**: Test component interactions
- **System tests**: Test end-to-end workflows
- **Performance tests**: Benchmark and profile
- **Regression tests**: Prevent bug reintroduction

### Test Naming Conventions
- `test_function_name`: Unit test for function
- `test_class_method`: Unit test for class method
- `test_integration_feature`: Integration test
- `test_performance_scenario`: Performance test
- `test_regression_issue_123`: Regression test

This comprehensive testing guide ensures TBCV maintains high quality and reliability through systematic testing practices.