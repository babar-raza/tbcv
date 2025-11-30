# TASK-XXX: [Task Name]

## Metadata
- **Priority**: P0/P1/P2
- **Effort**: X days
- **Owner**: TBD
- **Status**: Not Started
- **Dependencies**: [Task IDs]
- **Phase**: Phase N
- **Category**: [Foundation/Core Operations/Advanced/Integration/Enforcement]

## Objective
[Clear, one-sentence objective]

[Detailed description of what this task accomplishes and why it's important]

## Scope

### In Scope
- Specific item 1
- Specific item 2
- Specific item 3

### Out of Scope
- Item 1 (deferred to future)
- Item 2 (not needed)

## Acceptance Criteria
- [ ] All methods implemented with proper error handling
- [ ] Input validation for all parameters
- [ ] JSON-RPC compliant request/response format
- [ ] Unit tests with >90% coverage
- [ ] Integration tests for happy path and error cases
- [ ] Documentation updated with examples
- [ ] Performance validated (<5ms overhead per operation)
- [ ] No regressions in existing functionality
- [ ] Code reviewed and approved
- [ ] All linting/type checking passes

## Implementation Plan

### Architecture Decisions
[Key design decisions and rationale]

### Files to Create
```
path/to/new_file.py - Purpose: [description]
  - Class/Function 1: [purpose]
  - Class/Function 2: [purpose]

path/to/another_file.py - Purpose: [description]
```

### Files to Modify
```
path/to/existing_file.py
  - Add: [what to add]
  - Modify: [what to change]
  - Remove: [what to delete]

path/to/another_existing.py
  - Add: [what to add]
```

### Files to Delete
```
path/to/obsolete_file.py - Reason: [why]
```

## Detailed Implementation

### Step 1: [Step Name]
**What**: [Description]
**Why**: [Rationale]
**How**:
```python
# Code example or pseudocode
```

### Step 2: [Step Name]
**What**: [Description]
**Why**: [Rationale]
**How**:
```python
# Code example or pseudocode
```

## Testing Requirements

### Unit Tests
**File**: `tests/path/test_feature.py`

**Test Cases**:
1. **test_happy_path**: Normal operation succeeds
2. **test_missing_params**: Raises ValueError when required params missing
3. **test_invalid_params**: Handles invalid parameter values
4. **test_not_found**: Handles resource not found gracefully
5. **test_error_handling**: Propagates errors correctly

**Example**:
```python
def test_method_name_happy_path():
    """Test successful method execution."""
    # Arrange
    mcp_server = MCPServer()
    request = {
        "jsonrpc": "2.0",
        "method": "method_name",
        "params": {"param1": "value1"},
        "id": 1
    }

    # Act
    response = mcp_server.handle_request(request)

    # Assert
    assert "result" in response
    assert response["result"]["success"] is True
```

### Integration Tests
**File**: `tests/integration/test_feature_integration.py`

**Test Cases**:
1. **test_end_to_end_flow**: Full workflow from request to database
2. **test_concurrent_operations**: Handle concurrent requests
3. **test_error_propagation**: Errors bubble up correctly

### Manual Testing Checklist
- [ ] Test via MCP stdio mode
- [ ] Test via in-process client
- [ ] Test error conditions
- [ ] Test with real database
- [ ] Test performance under load
- [ ] Test backward compatibility

## Documentation Updates

### Files to Update
- [ ] `docs/mcp_integration.md` - Add method documentation
- [ ] `docs/api_reference.md` - Add API examples
- [ ] `docs/architecture.md` - Update architecture diagram
- [ ] `README.md` - Update if user-facing changes

### Documentation Content
**Method Documentation Template**:
```markdown
### `method_name`

Description of what the method does.

**Parameters**:
- `param1` (type, required): Description
- `param2` (type, optional): Description, default value

**Request Example**:
```json
{
  "jsonrpc": "2.0",
  "method": "method_name",
  "params": {
    "param1": "value1"
  },
  "id": 1
}
```

**Response Example**:
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "data": {...}
  },
  "id": 1
}
```

**Errors**:
- `ValueError`: Missing required parameter
- `NotFoundError`: Resource not found
```

## Runbook

### Development Setup
```bash
# Step 1: Create feature branch
git checkout -b feature/task-xxx-task-name

# Step 2: Set up development environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Implementation
```bash
# Step 3: Run tests continuously during development
pytest tests/path/test_feature.py -v --tb=short

# Step 4: Run linting
black svc/
mypy svc/
```

### Validation
```bash
# Step 5: Run full test suite
pytest -v --cov=svc --cov-report=html

# Step 6: Manual testing
python -m svc.mcp_server

# In another terminal:
echo '{"jsonrpc":"2.0","method":"method_name","params":{},"id":1}' | python -m svc.mcp_server
```

### Deployment
```bash
# Step 7: Commit changes
git add .
git commit -m "feat(mcp): implement task-xxx - [task name]"

# Step 8: Push and create PR
git push origin feature/task-xxx-task-name

# Step 9: After approval, merge
git checkout main
git merge feature/task-xxx-task-name
git push origin main
```

## Rollback Plan

### If Issues Discovered
```bash
# Option 1: Feature flag disable (if implemented)
# Set environment variable
export MCP_FEATURE_XXX_ENABLED=false

# Option 2: Revert commit
git revert <commit-hash>
git push origin main

# Option 3: Rollback to previous tag
git checkout tags/v1.x.x
git checkout -b rollback-task-xxx
# Fix issues, then merge
```

### Validation After Rollback
```bash
# Verify system health
python -m pytest tests/

# Check API endpoints
curl http://localhost:8000/health

# Check CLI
python cli/main.py --help
```

## Definition of Done

### Code Quality
- [ ] All code follows project style guide (black, mypy, pylint)
- [ ] No TODO, FIXME, or placeholder comments
- [ ] No hardcoded values (use config)
- [ ] Proper error handling and logging
- [ ] Type hints on all functions
- [ ] Docstrings on all public functions

### Testing
- [ ] Unit tests written and passing (>90% coverage)
- [ ] Integration tests written and passing
- [ ] Manual testing completed
- [ ] Performance benchmarks run (<5ms overhead)
- [ ] No regressions detected
- [ ] Edge cases covered

### Documentation
- [ ] Method documentation added to docs/mcp_integration.md
- [ ] Examples provided
- [ ] Architecture diagrams updated if needed
- [ ] Runbook tested and accurate
- [ ] Code comments for complex logic

### Review & Approval
- [ ] Code self-reviewed
- [ ] PR created with clear description
- [ ] All CI checks passing
- [ ] Code reviewed by peer
- [ ] Changes approved by tech lead
- [ ] Merged to main branch

### Operational
- [ ] No breaking changes to existing APIs
- [ ] Backward compatibility maintained
- [ ] Error messages clear and actionable
- [ ] Logs sufficient for debugging
- [ ] Monitoring/alerts configured if needed

---

**Status**: Not Started
**Last Updated**: [Date]
**Notes**: [Any additional context or decisions]
