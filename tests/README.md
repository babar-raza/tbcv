# TBCV Test Suite Documentation

This document provides comprehensive guidance on writing, running, and maintaining tests in the TBCV (Truth-Based Content Validation) project.

## Table of Contents

- [Running Tests](#running-tests)
- [UI Tests (Playwright)](#ui-tests-playwright)
- [Test Organization](#test-organization)
- [Available Fixtures](#available-fixtures)
- [Mocking Guidelines](#mocking-guidelines)
- [Naming Conventions](#naming-conventions)
- [Test Markers](#test-markers)
- [Writing Tests](#writing-tests)
- [Coverage Requirements](#coverage-requirements)

## Running Tests

### Basic Test Execution

```bash
# Run all tests (excluding manual and live tests)
pytest tests/ --ignore=tests/manual/ --ignore=tests/test_endpoints_live.py --ignore=tests/test_truth_llm_validation_real.py

# Run specific test file
pytest tests/api/test_dashboard.py

# Run specific test function
pytest tests/api/test_dashboard.py::test_specific_function

# Run with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=. --cov-report=html
```

### Running Tests by Marker

```bash
# Run only unit tests
pytest tests/ -m unit

# Run only integration tests
pytest tests/ -m integration

# Run smoke tests (quick boot and API checks)
pytest tests/ -m smoke

# Run WebSocket tests
pytest tests/ -m websocket

# Exclude slow tests
pytest tests/ -m "not slow"
```

### Windows PowerShell Command

```powershell
# Recommended test run command for Windows
powershell -NoProfile -Command "cd 'c:\Users\prora\OneDrive\Documents\GitHub\tbcv'; C:\Users\prora\anaconda3\shell\condabin\conda-hook.ps1; conda activate llm; python -m pytest tests/ --ignore=tests/manual/ --ignore=tests/test_endpoints_live.py --ignore=tests/test_truth_llm_validation_real.py -q --import-mode=importlib -p no:capture"
```

## UI Tests (Playwright)

Browser-based UI tests using Playwright to simulate real user behavior on the dashboard.

### Setup

```bash
# Install test dependencies (includes Playwright)
pip install -e ".[test]"

# Install Playwright browsers
playwright install chromium
```

### Running UI Tests

```bash
# Run all UI tests
pytest tests/ui/ -v

# Run with visible browser (for debugging)
pytest tests/ui/ -v --headed

# Run specific test file
pytest tests/ui/test_navigation.py -v

# Run with screenshots on failure
pytest tests/ui/ -v --screenshot=only-on-failure

# Run with video recording
pytest tests/ui/ -v --video=on

# Run only UI tests from full suite
pytest tests/ -m ui -v
```

### Using Helper Scripts

```bash
# Windows
scripts\run_ui_tests.bat

# Linux/macOS
./scripts/run_ui_tests.sh
```

### UI Test Structure

```
tests/ui/
   conftest.py           # Server and page fixtures
   pages/                # Page Object Models
      base_page.py
      dashboard_home.py
      validations_page.py
      validation_detail.py
      recommendations_page.py
      recommendation_detail.py
      workflows_page.py
      workflow_detail.py
   test_navigation.py       # Navigation tests (10)
   test_validations_flow.py # Validation workflow tests (12)
   test_recommendations_flow.py # Recommendation tests (10)
   test_forms_modals.py     # Form and modal tests (15)
   test_realtime_updates.py # WebSocket/real-time tests (8)
   test_bulk_actions.py     # Bulk action tests (10)
```

### UI Test Coverage

| Test Suite | Tests | Description |
|------------|-------|-------------|
| Navigation | 10 | Header links, pagination, view buttons |
| Validations | 12 | List, filter, approve, reject, enhance |
| Recommendations | 10 | List, filter, review forms |
| Forms/Modals | 15 | Run validation/workflow modals |
| Real-time | 8 | WebSocket, activity feed, progress |
| Bulk Actions | 10 | Checkbox selection, bulk operations |
| **Total** | **65** | |

For detailed UI testing documentation, see [docs/testing/UI_TESTING_GUIDE.md](../docs/testing/UI_TESTING_GUIDE.md).

## MCP Testing Infrastructure

### Overview

TBCV includes comprehensive MCP (Model Context Protocol) testing infrastructure for the JSON-RPC server and client implementations. MCP provides a standard interface for external tools and integrations to interact with TBCV programmatically.

**Key Components:**
- MCP Server (`svc/mcp_server.py`) - JSON-RPC server with modular method registry
- MCP Clients (`svc/mcp_client.py`) - Synchronous and asynchronous client wrappers
- MCP Methods (`svc/mcp_methods.py`) - Modular method handlers for validation, approval, enhancement

### Test Fixtures

Available MCP fixtures in `tests/svc/conftest.py`:

#### Database Fixtures
- **`temp_db`** - Temporary SQLite database for each test
  - Creates isolated database for testing
  - Auto-cleanup after test completion
  - Usage: `def test_example(temp_db): ...`

#### Server and Client Fixtures
- **`mcp_server`** - MCP server instance configured with test database
  - Returns: `MCPServer` instance
  - Usage: `def test_server(mcp_server): ...`

- **`mcp_sync_client`** - Synchronous MCP client
  - Returns: `MCPSyncClient` with 10s timeout, 2 retries
  - Usage: `def test_sync_ops(mcp_sync_client): ...`

- **`mcp_async_client`** - Asynchronous MCP client
  - Returns: `MCPAsyncClient` with 10s timeout, 2 retries
  - Usage: `async def test_async_ops(mcp_async_client): ...`

#### Test Data Fixtures
- **`test_markdown_file`** - Single markdown file with comprehensive content
  - Returns: `Path` to temporary .md file
  - Contains: YAML frontmatter, headings, code blocks, links, tables
  - Usage: `def test_validation(test_markdown_file): ...`

- **`test_markdown_files`** - Multiple markdown files for batch testing
  - Returns: `list[Path]` with 3 test files
  - Usage: `def test_batch(test_markdown_files): ...`

- **`test_validation_record`** - Pre-created validation record
  - Returns: Validation ID string
  - Usage: `def test_approval(test_validation_record): ...`

- **`sample_validation_data`** - Sample validation data dictionary
  - Contains: file_path, status, issues, metadata
  - Usage: `def test_data_processing(sample_validation_data): ...`

- **`sample_recommendation_data`** - Sample recommendation data
  - Contains: validation_id, recommendations list
  - Usage: `def test_recommendations(sample_recommendation_data): ...`

#### Environment Fixtures
- **`clean_env`** - Clean environment for tests
  - Saves and restores environment variables
  - Sets test-specific environment (LOG_LEVEL=ERROR, CACHE_ENABLED=false)
  - Usage: `def test_isolated(clean_env): ...`

### Running MCP Tests

```bash
# Run all MCP tests
pytest tests/svc/ -v

# Run specific test file
pytest tests/svc/test_mcp_server_architecture.py -v

# Run specific test class
pytest tests/svc/test_mcp_client.py::TestMCPSyncClient -v

# Run with coverage
pytest tests/svc/ --cov=svc --cov-report=html

# Run MCP tests with detailed output
pytest tests/svc/ -vv -s

# Run only synchronous client tests
pytest tests/svc/test_mcp_client.py -k "sync" -v

# Run only async client tests
pytest tests/svc/test_mcp_client.py -k "async" -v
```

### Writing MCP Tests

#### Synchronous Client Tests

```python
def test_validate_folder(mcp_sync_client, test_markdown_file):
    """Test folder validation via MCP sync client."""
    # Arrange
    folder_path = str(test_markdown_file.parent)

    # Act
    result = mcp_sync_client.validate_folder(folder_path, recursive=False)

    # Assert
    assert result["success"] is True
    assert result["results"]["files_processed"] > 0
```

#### Asynchronous Client Tests

```python
@pytest.mark.asyncio
async def test_approve_validation(mcp_async_client, test_validation_record):
    """Test validation approval via MCP async client."""
    # Arrange
    validation_ids = [test_validation_record]

    # Act
    result = await mcp_async_client.approve(validation_ids)

    # Assert
    assert result["success"] is True
    assert result["approved_count"] == 1
```

#### Server Method Tests

```python
def test_json_rpc_request_handling(mcp_server):
    """Test JSON-RPC request validation and routing."""
    # Arrange
    request = {
        "jsonrpc": "2.0",
        "method": "validate_folder",
        "params": {"folder_path": "/test", "recursive": True},
        "id": 1
    }

    # Act
    response = mcp_server.handle_request(request)

    # Assert
    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 1
    assert "result" in response or "error" in response
```

#### Testing Error Handling

```python
def test_invalid_method_error(mcp_sync_client):
    """Test error handling for invalid method."""
    from svc.mcp_exceptions import MCPMethodNotFoundError

    with pytest.raises(MCPMethodNotFoundError):
        mcp_sync_client._call_method("nonexistent_method", {})
```

### Common Test Patterns

#### Pattern 1: Validate → Approve → Enhance Workflow

```python
@pytest.mark.asyncio
async def test_full_workflow(mcp_async_client, test_markdown_file):
    """Test complete validation-approval-enhancement workflow."""
    folder = str(test_markdown_file.parent)

    # 1. Validate
    val_result = await mcp_async_client.validate_folder(folder)
    assert val_result["success"]

    # 2. Get validation IDs
    val_ids = [v["id"] for v in val_result["results"]["validations"]]

    # 3. Approve
    approve_result = await mcp_async_client.approve(val_ids)
    assert approve_result["approved_count"] == len(val_ids)

    # 4. Enhance
    enhance_result = await mcp_async_client.enhance(val_ids)
    assert enhance_result["success"]
```

#### Pattern 2: Batch Operations

```python
def test_batch_validation(mcp_sync_client, test_markdown_files):
    """Test batch validation of multiple files."""
    folder = str(test_markdown_files[0].parent)

    result = mcp_sync_client.validate_folder(folder, recursive=False)

    assert result["results"]["files_processed"] == len(test_markdown_files)
```

#### Pattern 3: Error Recovery with Retry

```python
@pytest.mark.asyncio
async def test_retry_on_failure(mcp_async_client):
    """Test retry logic on transient failures."""
    # Client configured with max_retries=2
    # Test will retry on network errors or timeouts
    result = await mcp_async_client.validate_folder("/path")
    # Assertions...
```

### Troubleshooting MCP Tests

#### Test fails with "Database is locked"
**Solution**: Ensure `temp_db` fixture is used. The fixture provides isolated in-memory database for each test.

```python
# Correct
def test_example(temp_db, mcp_sync_client):
    # temp_db ensures database isolation
    pass

# Incorrect - may cause database locks
def test_example(mcp_sync_client):
    # Missing temp_db fixture
    pass
```

#### Async tests not running
**Solution**: Ensure `pytest-asyncio` is installed and test is marked with `@pytest.mark.asyncio`.

```python
# Correct
@pytest.mark.asyncio
async def test_async_feature(mcp_async_client):
    result = await mcp_async_client.validate_folder("/path")
    assert result["success"]

# Incorrect - missing decorator
async def test_async_feature(mcp_async_client):
    # Will fail: test not recognized as async
    pass
```

#### JSON-RPC validation errors
**Solution**: Ensure requests follow JSON-RPC 2.0 specification with required fields.

```python
# Correct JSON-RPC request
request = {
    "jsonrpc": "2.0",        # Required: version
    "method": "validate_folder",  # Required: method name
    "params": {...},         # Optional: parameters
    "id": 1                  # Required: request ID
}

# Incorrect - missing required fields
request = {
    "method": "validate_folder"  # Missing jsonrpc and id
}
```

#### Fixture dependency errors
**Solution**: Ensure fixtures are declared in correct dependency order.

```python
# Correct - proper fixture dependency chain
def test_example(temp_db, mcp_server, mcp_sync_client):
    # temp_db -> mcp_server -> mcp_sync_client
    pass

# Incorrect - may cause initialization errors
def test_example(mcp_sync_client):
    # Missing temp_db dependency
    pass
```

### MCP Test Examples

See the following test files for comprehensive examples:

- **`tests/svc/test_mcp_server_architecture.py`** - Server architecture and JSON-RPC compliance
- **`tests/svc/test_mcp_client.py`** - Sync/async client implementations and error handling

## Test Organization

The test suite is organized into the following directories:

```
tests/
 api/              # API endpoint and FastAPI tests
    services/     # API service layer tests
    test_dashboard*.py  # Dashboard-specific tests
    test_export*.py     # Export functionality tests
    test_websocket*.py  # WebSocket tests
 agents/           # Agent behavior tests
 core/             # Core functionality tests
 cli/              # CLI command tests
 svc/              # MCP service layer tests
    conftest.py   # MCP-specific fixtures
    test_mcp_server_architecture.py  # MCP server tests
    test_mcp_client.py               # MCP client tests
 integration/      # Integration tests (MCP + API + Database)
 e2e/              # End-to-end workflow tests
 manual/           # Manual testing scripts (not run in CI)
 utils/            # Test utilities and helpers
 conftest.py       # Shared fixtures and configuration
```

### Excluded from Standard Test Runs

- `tests/manual/` - Interactive manual testing scripts
- `tests/test_endpoints_live.py` - Requires live external services
- `tests/test_truth_llm_validation_real.py` - Requires real LLM connection

## Available Fixtures

### Database Fixtures

#### `db_manager`
- **Scope:** function
- **Purpose:** Provides in-memory SQLite database for tests
- **Usage:**
  ```python
  def test_database_operation(db_manager):
      validation = db_manager.create_validation_result(...)
      assert validation.id is not None
  ```

#### `db_session`
- **Scope:** function
- **Purpose:** Provides database session for direct SQL operations
- **Usage:**
  ```python
  def test_with_session(db_session):
      result = db_session.query(Validation).first()
  ```

### API Fixtures

#### `api_client`
- **Scope:** function
- **Purpose:** FastAPI TestClient for synchronous endpoint testing
- **Usage:**
  ```python
  def test_endpoint(api_client):
      response = api_client.get("/api/validations")
      assert response.status_code == 200
  ```

#### `async_api_client`
- **Scope:** function
- **Purpose:** Async HTTP client for testing async endpoints
- **Usage:**
  ```python
  async def test_async_endpoint(async_api_client):
      async with async_api_client() as client:
          response = await client.get("/api/validations")
          assert response.status_code == 200
  ```

#### `websocket_client`
- **Scope:** function
- **Purpose:** WebSocket client for testing WS connections
- **Usage:**
  ```python
  def test_websocket(websocket_client):
      with websocket_client("/ws/workflow_123") as ws:
          data = ws.receive_json()
          assert data["type"] == "progress"
  ```

### Mock Agent Fixtures

#### `mock_content_validator`
- **Scope:** function
- **Purpose:** Mocked ContentValidatorAgent - NO real validation
- **Returns:** Realistic validation response structure
- **Usage:**
  ```python
  async def test_validation(mock_content_validator):
      result = await mock_content_validator.process_request({
          "file_path": "test.md",
          "family": "words"
      })
      assert result["success"] is True
  ```

#### `mock_llm_validator`
- **Scope:** function
- **Purpose:** Mocked LLMValidatorAgent - NO real LLM calls
- **Usage:**
  ```python
  async def test_llm(mock_llm_validator):
      result = await mock_llm_validator.process_request({})
      assert "llm_response" in result
  ```

#### Other Mock Agents:
- `mock_truth_manager` - Truth data lookups
- `mock_fuzzy_detector` - Pattern detection
- `mock_recommendation_agent` - Recommendation generation
- `mock_enhancement_agent` - Content enhancement
- `mock_orchestrator` - Workflow orchestration

### Sample Data Fixtures

#### `sample_markdown`
- **Purpose:** Complete markdown file with YAML frontmatter and code blocks
- **Usage:**
  ```python
  def test_parser(sample_markdown):
      parsed = parse_markdown(sample_markdown)
      assert "title" in parsed.frontmatter
  ```

#### `sample_validation_result`
- **Purpose:** Realistic validation result dictionary
- **Usage:**
  ```python
  def test_result_processing(sample_validation_result):
      assert sample_validation_result["confidence"] > 0
  ```

#### Other Sample Fixtures:
- `sample_yaml_content` - YAML-only content
- `sample_truth_data` - Plugin truth data
- `sample_recommendations` - Recommendation list

### File System Fixtures

#### `temp_dir`
- **Scope:** function
- **Purpose:** Temporary directory for file operations
- **Auto-cleanup:** Yes
- **Usage:**
  ```python
  def test_file_ops(temp_dir):
      test_file = temp_dir / "test.md"
      test_file.write_text("content")
      assert test_file.exists()
  ```

#### `temp_file`
- **Purpose:** Pre-created temporary file
- **Usage:**
  ```python
  def test_read_file(temp_file):
      content = temp_file.read_text()
      assert content == "Test content"
  ```

#### `sample_files_dir`
- **Purpose:** Directory with multiple test markdown files
- **Usage:**
  ```python
  def test_batch_processing(sample_files_dir):
      files = list(sample_files_dir.glob("*.md"))
      assert len(files) == 3
  ```

### Workflow Test Fixtures

#### `validation_with_file`
- **Purpose:** Validation record pointing to real temp file
- **Contains:** validation record, file_path, file_system
- **Usage:**
  ```python
  def test_validation_workflow(validation_with_file):
      val = validation_with_file["validation"]
      assert Path(validation_with_file["file_path"]).exists()
  ```

#### `approved_validation`
- **Purpose:** Validation in approved status with recommendations
- **Contains:** validation, recommendations list, file_path
- **Usage:**
  ```python
  def test_approval(approved_validation):
      val = approved_validation["validation"]
      assert val.status == "approved"
      assert len(approved_validation["recommendations"]) > 0
  ```

#### `running_workflow`
- **Purpose:** Workflow in running state with progress
- **Usage:**
  ```python
  def test_progress(running_workflow):
      workflow = running_workflow["workflow"]
      assert workflow.state == "running"
      assert workflow.progress_percent == 50
  ```

### External Service Mocks

#### `mock_ollama_client`
- **Purpose:** Prevents real LLM API calls
- **Usage:**
  ```python
  def test_llm_integration(mock_ollama_client):
      response = mock_ollama_client.generate("prompt")
      assert response["model"] == "mistral"
  ```

#### `mock_http_requests`
- **Purpose:** Mocks HTTP requests for link validation
- **Returns:** 200 OK responses
- **Usage:**
  ```python
  def test_link_check(mock_http_requests):
      # All HTTP requests return 200
      pass
  ```

#### `mock_cache_manager`
- **Purpose:** Mocks cache operations
- **Usage:**
  ```python
  def test_caching(mock_cache_manager):
      mock_cache_manager.get.return_value = cached_data
  ```

## Mocking Guidelines

### When to Mock

1. **External Services:** Always mock LLM APIs, HTTP requests, external databases
2. **File System:** Use temp fixtures instead of real file paths
3. **Time-Dependent Code:** Mock datetime for consistent test results
4. **Heavy Operations:** Mock expensive computations

### How to Mock

#### Using unittest.mock

```python
from unittest.mock import Mock, MagicMock, AsyncMock, patch

# Mock function
@patch('module.function_name')
def test_with_mock(mock_func):
    mock_func.return_value = "mocked"
    result = call_function()
    assert result == "mocked"

# Mock async function
async def test_async_mock():
    mock = AsyncMock(return_value={"success": True})
    result = await mock()
    assert result["success"]

# Mock class method
with patch.object(MyClass, 'method_name') as mock_method:
    mock_method.return_value = "value"
```

#### Using Fixture Mocks

```python
# Prefer using provided fixture mocks
def test_with_fixture_mock(mock_content_validator):
    # mock_content_validator is already configured
    # Just customize behavior if needed
    mock_content_validator.process_request.return_value = custom_value
```

### Mocking Best Practices

1. **Mock at Boundaries:** Mock external dependencies, not internal logic
2. **Verify Calls:** Use `assert_called_with()` to verify mock interactions
3. **Reset Mocks:** Mocks are function-scoped and reset automatically
4. **Don't Over-Mock:** Test real code paths when possible

## Naming Conventions

### Test Files

- **Pattern:** `test_<module_name>.py`
- **Examples:**
  - `test_dashboard.py` - Dashboard tests
  - `test_content_validator.py` - Content validator tests
  - `test_database.py` - Database operations tests

### Test Functions

- **Pattern:** `test_<what_is_being_tested>`
- **Use descriptive names:** Tests should read like documentation
- **Examples:**
  ```python
  def test_validation_creates_database_record():
      """Test that validation creates a record in database."""
      pass

  def test_approval_updates_status_and_sends_notification():
      """Test approval workflow updates status and notifies."""
      pass

  def test_invalid_file_path_raises_validation_error():
      """Test that invalid paths raise ValidationError."""
      pass
  ```

### Test Classes (Optional)

- **Pattern:** `TestClassName`
- **Use for grouping related tests:**
  ```python
  class TestValidationWorkflow:
      def test_create_validation(self):
          pass

      def test_approve_validation(self):
          pass

      def test_reject_validation(self):
          pass
  ```

### Async Tests

- **Pattern:** `async def test_<name>()`
- **Example:**
  ```python
  async def test_async_validation_processing(mock_content_validator):
      result = await mock_content_validator.process_request({})
      assert result["success"]
  ```

## Test Markers

Markers categorize tests for selective execution. Defined in `pytest.ini` and `conftest.py`.

### Available Markers

| Marker | Purpose | Usage |
|--------|---------|-------|
| `@pytest.mark.unit` | Unit tests - single component | Fast, isolated tests |
| `@pytest.mark.integration` | Integration tests - multiple components | Database + API tests |
| `@pytest.mark.e2e` | End-to-end workflow tests | Full system flows |
| `@pytest.mark.smoke` | Quick boot and API checks | CI health checks |
| `@pytest.mark.websocket` | WebSocket connection tests | May require async |
| `@pytest.mark.slow` | Tests taking >5 seconds | Run separately |
| `@pytest.mark.live` | Requires live external services | Local dev only |
| `@pytest.mark.performance` | Performance benchmarking | Optional runs |
| `@pytest.mark.admin` | Admin control tests | Admin workflows |
| `@pytest.mark.bulk` | Bulk action tests | Batch operations |

### Using Markers

```python
import pytest

@pytest.mark.unit
def test_parse_frontmatter():
    """Fast unit test."""
    pass

@pytest.mark.integration
def test_validation_saves_to_database(db_manager):
    """Integration test with database."""
    pass

@pytest.mark.slow
@pytest.mark.e2e
async def test_full_validation_workflow(api_client, db_manager):
    """End-to-end test that takes time."""
    pass

# Multiple markers
@pytest.mark.smoke
@pytest.mark.websocket
def test_websocket_connection(websocket_client):
    """Quick WebSocket smoke test."""
    pass
```

## Writing Tests

### Test Structure (AAA Pattern)

```python
def test_example(fixture):
    # Arrange - Set up test data and conditions
    test_data = {"key": "value"}
    expected_result = "expected"

    # Act - Execute the code under test
    result = function_to_test(test_data)

    # Assert - Verify the results
    assert result == expected_result
```

### Testing API Endpoints

```python
def test_get_validations_endpoint(api_client, db_manager):
    # Arrange - Create test data
    validation = db_manager.create_validation_result(
        file_path="test.md",
        rules_applied=["yaml"],
        validation_results={"passed": True}
    )

    # Act - Call endpoint
    response = api_client.get("/api/validations")

    # Assert - Verify response
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert any(v["id"] == validation.id for v in data)
```

### Testing Database Operations

```python
def test_create_validation(db_manager):
    # Arrange
    file_path = "test.md"

    # Act
    validation = db_manager.create_validation_result(
        file_path=file_path,
        rules_applied=["yaml", "markdown"],
        validation_results={"passed": True, "confidence": 0.95}
    )

    # Assert
    assert validation.id is not None
    assert validation.file_path == file_path
    assert validation.confidence == 0.95

    # Verify persistence
    retrieved = db_manager.get_validation(validation.id)
    assert retrieved.id == validation.id
```

### Testing Async Code

```python
@pytest.mark.asyncio
async def test_async_validation(mock_content_validator):
    # Arrange
    params = {"file_path": "test.md", "family": "words"}

    # Act
    result = await mock_content_validator.process_request(params)

    # Assert
    assert result["success"] is True
    assert "metrics" in result
```

### Testing Exceptions

```python
def test_invalid_input_raises_error():
    # Arrange
    invalid_data = None

    # Act & Assert
    with pytest.raises(ValueError, match="Input cannot be None"):
        process_data(invalid_data)
```

### Parametrized Tests

```python
@pytest.mark.parametrize("input_value,expected", [
    ("test.md", True),
    ("test.txt", False),
    ("document.markdown", True),
])
def test_file_extension_validation(input_value, expected):
    result = is_valid_markdown_file(input_value)
    assert result == expected
```

## Coverage Requirements

### Current Coverage Target

- **Minimum Coverage:** 70% (enforced in pytest.ini with --cov-fail-under=70)
- **Target Coverage:** 80%+ for new modules
- **Critical Paths:** 90%+ coverage required

### Running Coverage Reports

```bash
# Generate HTML coverage report
pytest tests/ --cov=. --cov-report=html

# View report
# Open htmlcov/index.html in browser

# Generate terminal coverage report
pytest tests/ --cov=. --cov-report=term-missing

# Fail if coverage below threshold
pytest tests/ --cov=. --cov-fail-under=70
```

### Coverage Best Practices

1. **Focus on Critical Paths:** Ensure validation, database, and API endpoints are well covered
2. **Don't Chase 100%:** Diminishing returns above 90%
3. **Test Behavior, Not Lines:** Coverage is a metric, not a goal
4. **Exclude Generated Code:** Use `.coveragerc` to exclude auto-generated files

### What to Cover

- **Must Cover:**
  - Core business logic
  - API endpoints
  - Database operations
  - Error handling paths
  - Validation rules

- **Optional Coverage:**
  - Configuration loading
  - Logging statements
  - Development utilities
  - Type annotations

## Troubleshooting

### Common Issues

#### Import Errors
```bash
# Solution: Use importlib mode
pytest tests/ --import-mode=importlib
```

#### Database Locks
```bash
# Solution: db_manager fixture uses in-memory database
# If issues persist, check for unclosed sessions
```

#### Async Test Failures
```python
# Ensure tests are marked with @pytest.mark.asyncio
# Or use async fixtures properly
```

#### UTF-8 Encoding Issues (Windows)
- Already handled in conftest.py for Windows
- If issues persist, check file encoding

### Debugging Tests

```bash
# Run with print statements visible
pytest tests/test_file.py -s

# Drop into debugger on failure
pytest tests/test_file.py --pdb

# Show local variables on failure
pytest tests/test_file.py -l

# Verbose output
pytest tests/test_file.py -vv
```

## Contributing Tests

When adding new features:

1. **Write Tests First:** Consider TDD approach
2. **Update Fixtures:** Add reusable fixtures to conftest.py
3. **Add Markers:** Mark tests appropriately
4. **Document Complex Tests:** Add docstrings explaining what's being tested
5. **Run Full Suite:** Ensure new tests don't break existing ones
6. **Check Coverage:** Maintain or improve coverage percentage

## Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- Project-specific docs in `docs/` directory
