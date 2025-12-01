# Access Guard Quick Reference

## Quick Start

```python
from core.access_guard import guarded_operation, set_enforcement_mode, EnforcementMode

# 1. Configure enforcement mode
set_enforcement_mode(EnforcementMode.WARN)  # or BLOCK, DISABLED

# 2. Protect business logic
@guarded_operation
def validate_content(file_path: str):
    # Business logic here
    pass

# 3. Access via MCP (correct)
from svc.mcp_client import MCPClient
client = MCPClient()
result = await client.call_tool("validate_content", {"file_path": "file.md"})
```

## Enforcement Modes

| Mode | Behavior | Use Case |
|------|----------|----------|
| **DISABLED** | No enforcement | Development, debugging |
| **WARN** | Log violations, allow access | Migration, discovery |
| **BLOCK** | Raise error on violation | Production, CI/CD |

## Configuration Methods

### Environment Variable
```bash
export TBCV_ACCESS_GUARD_MODE=block
```

### Code
```python
set_enforcement_mode(EnforcementMode.BLOCK)
# or
set_enforcement_mode("block")
```

## Allowed vs Blocked Callers

### Allowed ✓
- `svc/mcp_server.py` - MCP server
- `svc/mcp_methods/*.py` - MCP methods
- `svc/mcp_client.py` - MCP client
- `tests/` - Test code

### Blocked ✗
- `api/*.py` - API endpoints
- `cli/*.py` - CLI commands

## Common Patterns

### Protect Function
```python
@guarded_operation
def my_business_logic(data: dict):
    return process(data)
```

### Protect Method
```python
class MyService:
    @guarded_operation
    def process(self, item: str):
        return result
```

### Protect Async
```python
@guarded_operation
async def async_operation(id: str):
    return await fetch(id)
```

## Monitoring

### Get Statistics
```python
from core.access_guard import get_statistics

stats = get_statistics()
print(stats["violation_count"])
```

### Reset Statistics
```python
from core.access_guard import reset_statistics
reset_statistics()
```

### Check if Protected
```python
from core.access_guard import is_guarded
is_guarded(my_function)  # True/False
```

## Error Handling

```python
from core.access_guard import AccessGuardError

try:
    result = protected_function()
except AccessGuardError as e:
    print(f"Blocked: {e.function_name}")
    print(f"Caller: {e.caller_info}")
    # Use MCP client instead
    client = MCPClient()
    result = await client.call_tool(...)
```

## Testing

### Test with Mocked Caller
```python
from unittest.mock import patch

@patch('core.access_guard.check_caller_allowed')
def test_blocked_access(mock_check):
    set_enforcement_mode(EnforcementMode.BLOCK)
    mock_check.return_value = (False, "api/server.py")

    with pytest.raises(AccessGuardError):
        protected_function()
```

## Migration Steps

1. **Add decorators** - Add `@guarded_operation` to business logic
2. **Enable WARN** - `set_enforcement_mode(EnforcementMode.WARN)`
3. **Find violations** - Check logs and statistics
4. **Fix violations** - Route through MCP client
5. **Enable BLOCK** - `set_enforcement_mode(EnforcementMode.BLOCK)`

## Common Issues

### Issue: False positives in tests
**Solution:** Tests are allowed by design

### Issue: Performance impact
**Solution:** Use DISABLED mode for performance testing

### Issue: Legitimate internal calls blocked
**Solution:** Adjust caller detection logic in `check_caller_allowed()`

## See Also

- Full documentation: `docs/access_guard.md`
- Implementation: `core/access_guard.py`
- Tests: `tests/core/test_access_guard.py`
- Examples: `examples/access_guard_demo.py`
