# Testing

## Overview

TBCV includes comprehensive test suites covering unit tests, integration tests, UI tests, and end-to-end workflows. Tests are written using pytest with asyncio support and use in-memory SQLite databases for isolation.

**Primary Documentation**: [tests/README.md](../tests/README.md) - Complete testing guide with fixtures, markers, and examples.

## Quick Start

### Run All Tests
```bash
pytest tests/ --ignore=tests/manual/ --ignore=tests/test_endpoints_live.py --ignore=tests/test_truth_llm_validation_real.py -v
```

### Run UI Tests (Playwright)
```bash
pytest tests/ui/ -v --headed
```

### Windows PowerShell
```powershell
python -m pytest tests/ --ignore=tests/manual/ --ignore=tests/test_endpoints_live.py -q --import-mode=importlib -p no:capture
```

See [UI Testing Guide](testing/UI_TESTING_GUIDE.md) for detailed browser testing documentation.

## Test Directory Structure

```
tests/
├── api/                 # API endpoint tests
│   ├── services/        # Service layer tests (live_bus.py)
│   ├── test_dashboard*.py    # Dashboard tests (7 files)
│   ├── test_export*.py       # Export functionality
│   └── test_batch*.py        # Batch enhancement
├── agents/              # Agent behavior tests
│   ├── test_base.py          # BaseAgent tests
│   ├── test_enhancement_agent*.py  # Enhancement agent
│   ├── test_modular_validators.py  # Validator modules
│   └── test_truth_manager.py       # Truth manager
├── cli/                 # CLI command tests
│   ├── test_admin_*.py       # Admin commands
│   ├── test_validation_diff.py
│   └── test_workflow_*.py    # Workflow commands
├── core/                # Core functionality tests
│   ├── test_database.py      # DatabaseManager
│   ├── test_cache.py         # Caching system
│   ├── test_config_loader.py # Configuration
│   └── test_performance.py   # Performance tracking
├── contracts/           # API contract tests
├── e2e/                 # End-to-end workflows
├── ui/                  # Playwright browser tests (65 tests)
│   ├── pages/           # Page Object Models
│   ├── test_navigation.py
│   ├── test_validations_flow.py
│   └── test_recommendations_flow.py
└── manual/              # Interactive testing (excluded from CI)
```

## Test Categories

| Category | Location | Tests | Purpose |
|----------|----------|-------|---------|
| API Tests | `tests/api/` | ~50+ | Endpoint and dashboard tests |
| Agent Tests | `tests/agents/` | ~30+ | Agent behavior and validation |
| Core Tests | `tests/core/` | ~25+ | Database, config, utilities |
| CLI Tests | `tests/cli/` | ~15+ | Command-line interface |
| UI Tests | `tests/ui/` | 65 | Playwright browser tests |
| E2E Tests | `tests/e2e/` | ~10+ | End-to-end workflows |
| Contract Tests | `tests/contracts/` | ~20+ | API response schemas |

## Test Markers

```bash
pytest tests/ -m unit          # Unit tests only
pytest tests/ -m integration   # Integration tests
pytest tests/ -m smoke         # Quick health checks (~30 sec)
pytest tests/ -m ui            # Browser UI tests
pytest tests/ -m websocket     # WebSocket functionality
pytest tests/ -m "not slow"    # Exclude slow tests
```

## Key Fixtures

From `tests/conftest.py`:

| Fixture | Scope | Purpose |
|---------|-------|---------|
| `db_manager` | function | In-memory SQLite database |
| `db_session` | function | Direct database session |
| `api_client` | function | FastAPI TestClient (sync) |
| `async_api_client` | function | HTTPX AsyncClient |
| `sample_validation` | function | Pre-created validation |
| `sample_workflow` | function | Pre-created workflow |
| `mock_ollama` | function | Mocked LLM responses |

## Running Tests by Category

```bash
# API tests
pytest tests/api/ -v

# Agent tests with mocked Ollama
pytest tests/agents/ -v

# Dashboard-specific tests
pytest tests/api/test_dashboard*.py -v

# UI tests with visible browser
pytest tests/ui/ -v --headed

# E2E workflows
pytest tests/e2e/ -v

# Contract tests
pytest tests/contracts/ -v
```

## Coverage

```bash
# Generate HTML coverage report
pytest tests/ --cov=. --cov-report=html

# Terminal report with missing lines
pytest tests/ --cov=. --cov-report=term-missing

# Coverage for specific module
pytest tests/core/ --cov=core --cov-report=term-missing
```

## Tests Excluded from CI

These tests require external dependencies or manual interaction:

- `tests/manual/` - Interactive testing scripts
- `tests/test_endpoints_live.py` - Requires live server
- `tests/test_truth_llm_validation_real.py` - Requires Ollama

## Writing New Tests

Example test structure:

```python
import pytest
from unittest.mock import Mock, patch

class TestMyFeature:
    """Tests for MyFeature functionality."""

    @pytest.fixture
    def feature_instance(self, db_manager):
        """Create feature instance with dependencies."""
        return MyFeature(db=db_manager)

    def test_basic_functionality(self, feature_instance):
        """Test basic operation."""
        result = feature_instance.do_something()
        assert result.success is True

    @pytest.mark.asyncio
    async def test_async_operation(self, feature_instance):
        """Test async functionality."""
        result = await feature_instance.async_do_something()
        assert result is not None

    @pytest.mark.slow
    def test_expensive_operation(self, feature_instance):
        """Test that takes a long time."""
        # ...
```

## MCP Testing

### Overview

TBCV's MCP (Model Context Protocol) implementation provides a JSON-RPC interface for external tools to interact with validation operations. The testing infrastructure ensures reliability of server-client communication, error handling, and integration with core components.

### Architecture

```
┌─────────────────────┐
│   MCP Test Suite   │
└─────────┬───────────┘
          │
    ┌─────┴─────┐
    │           │
┌───▼───┐   ┌──▼────┐
│Server │   │Client │
│ Tests │   │ Tests │
└───┬───┘   └──┬────┘
    │          │
    └────┬─────┘
         │
    ┌────▼────┐
    │Database │
    │  Tests  │
    └─────────┘
```

### Test Categories

| Category | Files | Coverage |
|----------|-------|----------|
| Server Architecture | `test_mcp_server_architecture.py` | JSON-RPC protocol, method registry, routing |
| Client Wrappers | `test_mcp_client.py` | Sync/async clients, retry logic, error handling |
| Integration | Future: `tests/integration/` | End-to-end MCP workflows |

### Available Test Fixtures

From `tests/svc/conftest.py`:

```python
# Database
temp_db                    # Isolated SQLite database

# Server & Clients
mcp_server                 # MCPServer instance
mcp_sync_client            # Synchronous client (MCPSyncClient)
mcp_async_client           # Asynchronous client (MCPAsyncClient)

# Test Data
test_markdown_file         # Single markdown file
test_markdown_files        # Multiple markdown files (batch testing)
test_validation_record     # Pre-created validation record
sample_validation_data     # Sample validation dictionary
sample_recommendation_data # Sample recommendation dictionary

# Environment
clean_env                  # Clean test environment
```

### Writing MCP Tests

#### Example 1: Synchronous Client Test

```python
def test_validate_folder(mcp_sync_client, test_markdown_file):
    """Test folder validation via sync client."""
    folder_path = str(test_markdown_file.parent)

    result = mcp_sync_client.validate_folder(folder_path, recursive=False)

    assert result["success"] is True
    assert result["results"]["files_processed"] > 0
    assert "validations" in result["results"]
```

#### Example 2: Asynchronous Client Test

```python
@pytest.mark.asyncio
async def test_approve_validations(mcp_async_client, test_validation_record):
    """Test validation approval via async client."""
    validation_ids = [test_validation_record]

    result = await mcp_async_client.approve(validation_ids)

    assert result["success"] is True
    assert result["approved_count"] == len(validation_ids)
```

#### Example 3: Server Method Test

```python
def test_json_rpc_compliance(mcp_server):
    """Test JSON-RPC 2.0 protocol compliance."""
    request = {
        "jsonrpc": "2.0",
        "method": "validate_folder",
        "params": {"folder_path": "/test"},
        "id": 1
    }

    response = mcp_server.handle_request(request)

    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 1
    assert "result" in response or "error" in response
```

#### Example 4: Error Handling Test

```python
def test_method_not_found(mcp_sync_client):
    """Test error handling for nonexistent method."""
    from svc.mcp_exceptions import MCPMethodNotFoundError

    with pytest.raises(MCPMethodNotFoundError) as exc_info:
        mcp_sync_client._call_method("invalid_method", {})

    assert exc_info.value.code == -32601
    assert "not found" in str(exc_info.value).lower()
```

#### Example 5: Full Workflow Test

```python
@pytest.mark.asyncio
async def test_validation_workflow(mcp_async_client, test_markdown_file):
    """Test complete validation → approval → enhancement workflow."""
    folder = str(test_markdown_file.parent)

    # Step 1: Validate
    val_result = await mcp_async_client.validate_folder(folder)
    assert val_result["success"]

    # Step 2: Extract validation IDs
    val_ids = [v["id"] for v in val_result["results"]["validations"]]

    # Step 3: Approve
    approve_result = await mcp_async_client.approve(val_ids)
    assert approve_result["approved_count"] == len(val_ids)

    # Step 4: Enhance
    enhance_result = await mcp_async_client.enhance(val_ids)
    assert enhance_result["success"]
```

### Running MCP Tests

```bash
# All MCP tests
pytest tests/svc/ -v

# Specific test file
pytest tests/svc/test_mcp_client.py -v

# Specific test class
pytest tests/svc/test_mcp_server_architecture.py::TestJSONRPCUtilities -v

# Only sync client tests
pytest tests/svc/ -k "sync" -v

# Only async client tests
pytest tests/svc/ -k "async" -v

# With coverage
pytest tests/svc/ --cov=svc --cov-report=html
```

### Best Practices

#### 1. Always Use Fixtures for Database Isolation

```python
# ✅ Correct - uses temp_db for isolation
def test_with_database(temp_db, mcp_sync_client):
    result = mcp_sync_client.validate_folder("/path")
    # Database is isolated and cleaned up automatically

# ❌ Incorrect - missing temp_db may cause database locks
def test_without_database(mcp_sync_client):
    result = mcp_sync_client.validate_folder("/path")
    # May fail with "database is locked" error
```

#### 2. Mark Async Tests Properly

```python
# ✅ Correct - properly marked as async
@pytest.mark.asyncio
async def test_async_operation(mcp_async_client):
    result = await mcp_async_client.validate_folder("/path")
    assert result["success"]

# ❌ Incorrect - missing @pytest.mark.asyncio
async def test_async_operation(mcp_async_client):
    # Test will not run properly
    result = await mcp_async_client.validate_folder("/path")
```

#### 3. Follow JSON-RPC 2.0 Specification

```python
# ✅ Correct - valid JSON-RPC 2.0 request
request = {
    "jsonrpc": "2.0",      # Required: version
    "method": "approve",    # Required: method name
    "params": {"ids": []},  # Optional: parameters
    "id": 1                 # Required: request ID
}

# ❌ Incorrect - missing required fields
request = {
    "method": "approve",
    "params": {"ids": []}
}  # Missing jsonrpc version and id
```

#### 4. Test Error Cases

```python
def test_error_handling(mcp_sync_client):
    """Test error handling for various failure scenarios."""
    from svc.mcp_exceptions import MCPInvalidParamsError

    # Test invalid parameters
    with pytest.raises(MCPInvalidParamsError):
        mcp_sync_client.approve([])  # Empty list

    # Test method not found
    with pytest.raises(MCPMethodNotFoundError):
        mcp_sync_client._call_method("nonexistent", {})

    # Test internal errors
    # (Mock internal failures as needed)
```

#### 5. Use Proper Fixture Dependencies

```python
# ✅ Correct - proper dependency chain
def test_with_dependencies(temp_db, mcp_server, mcp_sync_client):
    # temp_db → mcp_server → mcp_sync_client
    # All fixtures properly initialized in order
    pass

# ❌ Incorrect - skipping intermediate dependencies
def test_without_dependencies(mcp_sync_client):
    # May fail if temp_db not initialized
    pass
```

### Troubleshooting

#### Database Locked Error

**Problem**: Tests fail with "database is locked" error.

**Solution**: Ensure `temp_db` fixture is included in test parameters.

```python
# Fix by adding temp_db fixture
def test_example(temp_db, mcp_sync_client):
    # Now database is properly isolated
    pass
```

#### Async Test Not Running

**Problem**: Async test appears to be skipped or fails immediately.

**Solution**: Add `@pytest.mark.asyncio` decorator.

```python
@pytest.mark.asyncio
async def test_async_feature(mcp_async_client):
    result = await mcp_async_client.validate_folder("/path")
    assert result["success"]
```

#### JSON-RPC Validation Failed

**Problem**: Request fails with "Invalid JSON-RPC" error.

**Solution**: Ensure request includes all required fields: `jsonrpc`, `method`, and `id`.

```python
request = {
    "jsonrpc": "2.0",
    "method": "validate_folder",
    "params": {"folder_path": "/test"},
    "id": 1
}
```

#### Fixture Dependency Error

**Problem**: Fixture initialization fails.

**Solution**: Check fixture dependency order. `temp_db` must come before `mcp_server`, which must come before clients.

```python
# Correct order
def test_example(temp_db, mcp_server, mcp_sync_client):
    pass
```

### Common Test Patterns

#### Pattern: Batch Validation

```python
def test_batch_validation(mcp_sync_client, test_markdown_files):
    """Test validating multiple files."""
    folder = str(test_markdown_files[0].parent)

    result = mcp_sync_client.validate_folder(folder, recursive=False)

    assert result["results"]["files_processed"] == len(test_markdown_files)
```

#### Pattern: Error Recovery

```python
@pytest.mark.asyncio
async def test_retry_on_transient_failure(mcp_async_client):
    """Test retry logic on transient failures."""
    # Client configured with max_retries=2
    # Will automatically retry on network errors
    result = await mcp_async_client.validate_folder("/path")
    assert result is not None
```

#### Pattern: Mocking External Dependencies

```python
def test_with_mocked_ollama(mcp_sync_client, monkeypatch):
    """Test enhancement with mocked LLM."""
    def mock_enhance(*args, **kwargs):
        return {"success": True, "enhanced_count": 1}

    monkeypatch.setattr("svc.mcp_server.enhance_validations", mock_enhance)

    result = mcp_sync_client.enhance(["val-123"])
    assert result["success"]
```

### Test Coverage Goals

- **Server Methods**: 100% coverage of all JSON-RPC methods
- **Client Wrappers**: 90%+ coverage including error paths
- **Integration**: End-to-end workflows validated
- **Error Handling**: All error codes tested

### Reference Files

- **Server Tests**: `tests/svc/test_mcp_server_architecture.py`
- **Client Tests**: `tests/svc/test_mcp_client.py`
- **Fixtures**: `tests/svc/conftest.py`
- **Implementation**: `svc/mcp_server.py`, `svc/mcp_client.py`, `svc/mcp_methods.py`

## Additional Resources

- [tests/README.md](../tests/README.md) - **Complete testing documentation with MCP section**
- [testing/UI_TESTING_GUIDE.md](testing/UI_TESTING_GUIDE.md) - Playwright UI testing
- [mcp_integration.md](mcp_integration.md) - MCP server integration guide
- [pytest.ini](../pytest.ini) - pytest configuration
- [tests/conftest.py](../tests/conftest.py) - Shared fixtures
