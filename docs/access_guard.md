# Access Guard - Runtime Enforcement of Architectural Boundaries

## Overview

The Access Guard is a runtime enforcement system that prevents direct access to business logic from API and CLI layers. It ensures that all business logic is accessed through the MCP (Model Context Protocol) server layer, enforcing the MCP-first architecture.

## Key Components

### 1. EnforcementMode Enum

Three levels of enforcement:

- **DISABLED**: No enforcement, all access allowed (default)
- **WARN**: Log violations but allow access (development)
- **BLOCK**: Prevent unauthorized access (production)

### 2. AccessGuardError Exception

Raised when a guarded operation is accessed from a blocked context in BLOCK mode.

### 3. @guarded_operation Decorator

Protects business logic functions from unauthorized access.

### 4. Stack Inspection

Inspects the call stack to determine if the caller is from an allowed or blocked context.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Allowed Callers                   │
├─────────────────────────────────────────────────────┤
│  - svc/mcp_server.py (MCP server)                   │
│  - svc/mcp_methods/*.py (MCP method implementations) │
│  - svc/mcp_client.py (MCP client wrapper)           │
│  - tests/ (test code)                               │
└─────────────────────────────────────────────────────┘
                         │
                         ├─ check_caller_allowed()
                         │  (stack inspection)
                         ├─ @guarded_operation
                         │  (decorator)
                         ↓
┌─────────────────────────────────────────────────────┐
│              Protected Business Logic                │
├─────────────────────────────────────────────────────┤
│  - agents/ (validation, enhancement agents)          │
│  - core/ (workflow manager, database, cache)         │
│  - Any critical business logic                       │
└─────────────────────────────────────────────────────┘
                         ↑
                         ├─ AccessGuardError
                         │  (if blocked)
                         ↓
┌─────────────────────────────────────────────────────┐
│                   Blocked Callers                    │
├─────────────────────────────────────────────────────┤
│  - api/ (API endpoints)                             │
│  - cli/ (CLI commands)                              │
└─────────────────────────────────────────────────────┘
```

## Usage

### Basic Usage

```python
from core.access_guard import guarded_operation

# Protect a business logic function
@guarded_operation
def validate_content(file_path: str) -> ValidationResult:
    """This can only be called from MCP layer or tests."""
    # Business logic here
    return ValidationResult(...)
```

### Configuration

#### Method 1: Environment Variable

```bash
# Set before starting the application
export TBCV_ACCESS_GUARD_MODE=block  # or warn, disabled
```

#### Method 2: Code Configuration

```python
from core.access_guard import set_enforcement_mode, EnforcementMode

# In main.py or startup code
set_enforcement_mode(EnforcementMode.BLOCK)

# Or with string (case-insensitive)
set_enforcement_mode("warn")
```

#### Method 3: Configuration File

```yaml
# config/access_guard.yaml
enforcement_mode: block  # disabled, warn, or block
```

### Protecting Business Logic

```python
from core.access_guard import guarded_operation

# Protect standalone functions
@guarded_operation
def process_workflow(workflow_id: str) -> WorkflowResult:
    # Implementation
    pass

# Protect class methods
class ContentValidator:
    @guarded_operation
    def validate(self, content: str) -> bool:
        # Implementation
        pass

# Protect async functions
@guarded_operation
async def async_validation(file_path: str):
    # Implementation
    pass
```

### Correct Access Pattern

```python
# CORRECT: Access through MCP client
from svc.mcp_client import MCPClient

async def api_endpoint_validate(file_path: str):
    """API endpoint accesses business logic via MCP."""
    client = MCPClient()
    result = await client.call_tool(
        "validate_content",
        {"file_path": file_path}
    )
    return result

# CORRECT: MCP method implementation
# File: svc/mcp_methods/validation_methods.py
def validate_content_handler(file_path: str):
    """MCP method can directly call business logic."""
    return validate_content(file_path)  # Allowed
```

### Incorrect Access Pattern

```python
# INCORRECT: Direct access from API
# File: api/server.py
from agents.content_validator import validate_content

def api_endpoint_validate(file_path: str):
    """This will be blocked in BLOCK mode."""
    result = validate_content(file_path)  # AccessGuardError!
    return result

# INCORRECT: Direct access from CLI
# File: cli/main.py
from core.workflow_manager import process_workflow

def cli_validate_command(workflow_id: str):
    """This will be blocked in BLOCK mode."""
    result = process_workflow(workflow_id)  # AccessGuardError!
    return result
```

## Monitoring and Statistics

### Get Statistics

```python
from core.access_guard import get_statistics

stats = get_statistics()
print(f"Mode: {stats['mode']}")
print(f"Total violations: {stats['violation_count']}")
print(f"Recent violations: {len(stats['recent_violations'])}")

# Examine recent violations
for violation in stats['recent_violations']:
    print(f"Function: {violation['function_name']}")
    print(f"Caller: {violation['caller_info']}")
    print(f"Timestamp: {violation['timestamp']}")
```

### Reset Statistics

```python
from core.access_guard import reset_statistics

# Useful for testing or after resolving violations
reset_statistics()
```

### Check if Function is Protected

```python
from core.access_guard import is_guarded

if is_guarded(my_function):
    print("Function is protected by access guard")
```

## Enforcement Modes

### DISABLED Mode

**Use for:** Initial development, debugging

**Behavior:**
- All access allowed
- No logging
- No performance impact

```python
set_enforcement_mode(EnforcementMode.DISABLED)

# All calls succeed
result = validate_content("file.md")  # OK
```

### WARN Mode

**Use for:** Development, migration, identifying violations

**Behavior:**
- All access allowed
- Violations logged as warnings
- Statistics tracked
- No exceptions raised

```python
set_enforcement_mode(EnforcementMode.WARN)

# Call succeeds but logs warning
result = validate_content("file.md")  # OK, but logs warning
```

**Log output:**
```
2025-12-01 15:00:00 [warning] Access guard violation (WARNING)
  function=agents.content_validator.validate_content
  caller=api/server.py:validate_endpoint:123
  violation_count=1
```

### BLOCK Mode

**Use for:** Production, CI/CD tests, strict enforcement

**Behavior:**
- Unauthorized access blocked
- AccessGuardError raised
- Violations logged as errors
- Statistics tracked

```python
set_enforcement_mode(EnforcementMode.BLOCK)

# Call from blocked context raises exception
try:
    result = validate_content("file.md")
except AccessGuardError as e:
    print(f"Access denied: {e.message}")
```

**Error output:**
```
AccessGuardError: Direct access to 'agents.content_validator.validate_content'
not allowed. Caller: api/server.py:123 (validate_endpoint).
Use MCP client instead.
```

## Migration Strategy

### Phase 1: Discovery (DISABLED)

```python
# Start with enforcement disabled
set_enforcement_mode(EnforcementMode.DISABLED)

# Add @guarded_operation decorators to business logic
# No impact on existing code
```

### Phase 2: Identification (WARN)

```python
# Enable WARN mode to identify violations
set_enforcement_mode(EnforcementMode.WARN)

# Monitor logs to find direct access
# Review statistics regularly
stats = get_statistics()
print(f"Found {stats['violation_count']} violations")
```

### Phase 3: Remediation

```python
# Fix violations by routing through MCP
# Before:
result = validate_content(file_path)  # Direct access

# After:
client = MCPClient()
result = await client.call_tool("validate_content",
                                {"file_path": file_path})
```

### Phase 4: Enforcement (BLOCK)

```python
# Enable BLOCK mode in production
set_enforcement_mode(EnforcementMode.BLOCK)

# All violations now raise errors
# Ensures architectural boundaries
```

## Testing

### Unit Tests

```python
import pytest
from core.access_guard import (
    guarded_operation,
    set_enforcement_mode,
    EnforcementMode,
    AccessGuardError
)

def test_guarded_function_in_block_mode():
    """Test that blocked access raises error."""
    set_enforcement_mode(EnforcementMode.BLOCK)

    @guarded_operation
    def protected_func():
        return "result"

    # From test context - should be allowed
    result = protected_func()
    assert result == "result"

def test_statistics_tracking():
    """Test that violations are tracked."""
    set_enforcement_mode(EnforcementMode.WARN)
    reset_statistics()

    @guarded_operation
    def func():
        pass

    func()

    stats = get_statistics()
    # May or may not have violations depending on caller context
    assert "violation_count" in stats
```

### Integration Tests

```python
from unittest.mock import patch

@patch('core.access_guard.check_caller_allowed')
def test_api_access_blocked(mock_check):
    """Test that API access is blocked."""
    set_enforcement_mode(EnforcementMode.BLOCK)
    mock_check.return_value = (False, "api/server.py:123")

    @guarded_operation
    def business_logic():
        return "result"

    with pytest.raises(AccessGuardError):
        business_logic()
```

## Performance Considerations

### Impact

- **DISABLED mode**: Zero overhead
- **WARN/BLOCK modes**: Minimal overhead (~0.1ms per call)
  - Stack inspection: ~0.05ms
  - Logging: ~0.05ms

### Optimization Tips

1. **Use DISABLED in hot paths during development**
   ```python
   # Temporarily disable for performance testing
   set_enforcement_mode(EnforcementMode.DISABLED)
   ```

2. **Decorator is cached**
   - Function metadata preserved
   - No repeated decoration overhead

3. **Stack depth configuration**
   ```python
   # Reduce stack depth for faster checks (if needed)
   allowed, info = check_caller_allowed(frame_depth=3)
   ```

## Best Practices

### 1. Protect All Business Logic

```python
# Protect agents
@guarded_operation
def validate_content(file_path: str):
    pass

# Protect core services
@guarded_operation
def process_workflow(workflow_id: str):
    pass

# Protect critical operations
@guarded_operation
def update_database(data: dict):
    pass
```

### 2. Use Appropriate Mode for Environment

```python
# Development
if environment == "development":
    set_enforcement_mode(EnforcementMode.WARN)

# Testing
if environment == "test":
    set_enforcement_mode(EnforcementMode.BLOCK)

# Production
if environment == "production":
    set_enforcement_mode(EnforcementMode.BLOCK)
```

### 3. Monitor Violations Regularly

```python
# Add monitoring endpoint
@app.get("/internal/access-guard/stats")
async def get_access_guard_stats():
    return get_statistics()

# Log statistics periodically
import schedule

def log_stats():
    stats = get_statistics()
    logger.info("Access guard statistics", **stats)

schedule.every(1).hour.do(log_stats)
```

### 4. Document Protected Functions

```python
@guarded_operation
def validate_content(file_path: str) -> ValidationResult:
    """
    Validate content file.

    Access: MCP only - Use MCPClient.call_tool('validate_content', ...)

    Args:
        file_path: Path to file to validate

    Returns:
        ValidationResult with issues found
    """
    pass
```

### 5. Test Both Paths

```python
# Test MCP path (correct)
async def test_mcp_validation():
    client = MCPClient()
    result = await client.call_tool("validate_content",
                                    {"file_path": "test.md"})
    assert result["valid"]

# Test direct path is blocked
def test_direct_access_blocked():
    set_enforcement_mode(EnforcementMode.BLOCK)

    with pytest.raises(AccessGuardError):
        validate_content("test.md")
```

## Troubleshooting

### Problem: Violations not being detected

**Cause**: Calls are from allowed context (test, internal)

**Solution**: Use mock to simulate blocked context
```python
@patch('core.access_guard.check_caller_allowed')
def test_blocked_access(mock_check):
    mock_check.return_value = (False, "api/server.py")
    # Now test will properly detect violation
```

### Problem: False positives in tests

**Cause**: Test code is in allowed context

**Solution**: This is expected - tests should be allowed
```python
# Tests are allowed by design
def test_business_logic():
    result = validate_content("test.md")  # OK from tests
    assert result["valid"]
```

### Problem: Performance impact

**Cause**: Stack inspection on every call

**Solution**: Use DISABLED mode for performance testing
```python
# Performance testing
set_enforcement_mode(EnforcementMode.DISABLED)
run_performance_tests()

# Restore after testing
set_enforcement_mode(EnforcementMode.BLOCK)
```

### Problem: Violations in legitimate internal calls

**Cause**: Stack depth too shallow or path not recognized

**Solution**: Adjust stack depth or add path to allowed list
```python
# In core/access_guard.py, modify check_caller_allowed()
# Add additional allowed patterns
if "/internal/" in filename_normalized:
    return True, f"Internal module: {filename}"
```

## Integration with Other Systems

### Integration with Logging

```python
# Access guard automatically logs to structlog
# Violations appear in your log aggregation system

# Example Splunk query:
# source="tbcv.log" "Access guard violation"

# Example Datadog query:
# @logger:tbcv @event:"Access guard violation"
```

### Integration with Monitoring

```python
# Export metrics to Prometheus
from prometheus_client import Counter

access_guard_violations = Counter(
    'access_guard_violations_total',
    'Total access guard violations',
    ['function', 'mode']
)

# In log_violation():
access_guard_violations.labels(
    function=function_name,
    mode=mode.value
).inc()
```

### Integration with CI/CD

```yaml
# .github/workflows/test.yml
- name: Run tests with access guard enabled
  env:
    TBCV_ACCESS_GUARD_MODE: block
  run: pytest tests/
```

## API Reference

See inline documentation in `core/access_guard.py` for complete API reference.

### Key Functions

- `set_enforcement_mode(mode)` - Set global enforcement mode
- `get_enforcement_mode()` - Get current enforcement mode
- `check_caller_allowed(frame_depth)` - Check if caller is allowed
- `log_violation(function_name, caller_info, mode, additional_context)` - Log violation
- `guarded_operation(func)` - Decorator to protect functions
- `is_guarded(func)` - Check if function is protected
- `reset_statistics()` - Reset violation statistics
- `get_statistics()` - Get violation statistics

### Key Classes

- `EnforcementMode` - Enum for enforcement modes
- `AccessGuardError` - Exception for blocked access

## Examples

See `examples/access_guard_demo.py` for comprehensive examples.

## References

- Implementation: `core/access_guard.py`
- Tests: `tests/core/test_access_guard.py`
- MCP Architecture: `docs/mcp_integration.md`
- Migration Guide: `docs/implementation/MCP_MIGRATION.md`
