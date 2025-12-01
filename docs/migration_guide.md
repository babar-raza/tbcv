# MCP Migration Guide

## Overview

This guide documents the migration to TBCV's MCP-first architecture where all business logic is accessed through a centralized Model Context Protocol (MCP) server. This architectural change provides significant benefits for maintainability, testing, and operational clarity.

### What is MCP-First Architecture?

MCP-first architecture means that **all access** to core business logic (agents, validators, database) flows through a single MCP server. The CLI and API layers become thin clients that exclusively use MCP client wrappers to perform operations.

### Key Benefits

- **Centralized Logic**: Single source of truth for all operations
- **Consistent Interface**: CLI and API use identical MCP methods
- **Better Testing**: Isolated testing of business logic without UI concerns
- **Enhanced Monitoring**: Centralized logging and metrics collection
- **Security**: Enforced architectural boundaries via access guards
- **Maintainability**: Changes to business logic don't require CLI/API updates

## Architecture

### Before Migration (Direct Access)

```
┌─────────────────┐     ┌─────────────────┐
│   CLI Layer     │     │   API Layer     │
└────────┬────────┘     └────────┬────────┘
         │                       │
         │   Direct Imports      │
         │                       │
         ├───────────┬───────────┤
         │           │           │
    ┌────▼────┐ ┌───▼───┐ ┌────▼─────┐
    │ Agents  │ │  DB   │ │ Validators│
    └─────────┘ └───────┘ └──────────┘
```

Problems with this approach:
- Tight coupling between UI and business logic
- Difficult to test in isolation
- Changes propagate across layers
- No centralized monitoring point

### After Migration (MCP-First)

```
┌─────────────────┐     ┌─────────────────┐
│   CLI Layer     │     │   API Layer     │
└────────┬────────┘     └────────┬────────┘
         │                       │
         │    MCP Clients        │
         │                       │
         └───────────┬───────────┘
                     │
         ┌───────────▼───────────┐
         │    MCP Server         │
         │  (56 Methods)         │
         │  + Access Guards      │
         └───────────┬───────────┘
                     │
         ┌───────────▼───────────┐
         │  Business Logic       │
         │  Agents, DB, Validators│
         └───────────────────────┘
```

Benefits:
- Clean separation of concerns
- Single point for monitoring and logging
- Easy to test and maintain
- Enforced architectural boundaries

## Pre-Migration Checklist

Complete these tasks before starting migration:

### Data Backup
- [ ] Backup SQLite database (`data/tbcv.db`)
- [ ] Backup configuration files (`config/*.yaml`)
- [ ] Backup truth data (`truth/*.json`)
- [ ] Document backup location and timestamp

### System Validation
- [ ] Verify all existing tests passing (`pytest tests/ -v`)
- [ ] Document current test coverage (`pytest --cov`)
- [ ] Run system health check (`python cli/main.py health`)
- [ ] Verify no pending database migrations

### Configuration Review
- [ ] Review current configuration in `config/`
- [ ] Document any custom settings or overrides
- [ ] Identify environment-specific configurations
- [ ] Review `.env` file for sensitive settings

### Documentation
- [ ] Document current CLI usage patterns
- [ ] Document current API integrations
- [ ] List any custom scripts or automations
- [ ] Identify stakeholders to notify

### Planning
- [ ] Schedule maintenance window (recommended: 2-4 hours)
- [ ] Identify rollback owner
- [ ] Prepare team communication
- [ ] Define success criteria

## Migration Process

Follow these steps in order. Do not skip steps.

### Step 1: Update Dependencies

Install updated packages with MCP support:

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows

# Update dependencies
pip install -r requirements.txt --upgrade

# Verify installation
python -c "from svc.mcp_server import MCPServer; print('MCP Server OK')"
python -c "from svc.mcp_client import MCPSyncClient; print('MCP Client OK')"
```

**Validation**: Ensure no import errors.

### Step 2: Configure Access Guards

Create or update `config/access_guards.yaml`:

```yaml
# Access Guard Configuration
enforcement_mode: warn  # Start with warn mode for safety

# Allowed callers (do not modify)
allowed_callers:
  - svc.mcp_server
  - svc.mcp_methods
  - tests.
  - <stdin>
  - pytest
  - conftest

# Logging
log_violations: true
log_level: warning
```

**Important**: Start with `warn` mode. This logs violations but doesn't block operations. After validating the system works correctly, switch to `block` mode.

**Validation**:
```bash
python -c "from core.access_guard import is_mcp_enforced; print(f'Enforcement: {is_mcp_enforced()}')"
```

### Step 3: Initialize Database Schema

Ensure database schema is up-to-date:

```bash
# Initialize or migrate database
python -c "from core.database import DatabaseManager; DatabaseManager().init_database()"

# Verify tables exist
python -c "from core.database import DatabaseManager; dm = DatabaseManager(); print(f'Tables: {len(dm.get_session().execute(\"SELECT name FROM sqlite_master WHERE type=\'table\';\").fetchall())}')"
```

**Validation**: Should see multiple tables (ValidationResults, Workflows, Recommendations, etc.)

### Step 4: Test MCP Server

Verify MCP server initializes and responds:

```bash
# Test MCP server initialization
python -c "from svc.mcp_server import create_mcp_client; server = create_mcp_client(); print('MCP Server initialized')"

# Test basic MCP method
python -c "
from svc.mcp_client import MCPSyncClient
client = MCPSyncClient()
result = client.get_stats()
print(f'System stats: {result}')
"
```

**Validation**: Should see system statistics without errors.

### Step 5: Test CLI Commands

Test all CLI commands with MCP integration:

```bash
# Test validation command
python cli/main.py validate-file README.md
echo "Exit code: $?"  # Should be 0

# Test listing validations
python cli/main.py validations list --limit 10

# Test system health
python cli/main.py admin stats

# Test cache management
python cli/main.py admin cache-stats
```

**Validation**: All commands should complete without `RuntimeError: Direct access` errors.

If you see access errors in warn mode, check logs for violations:
```bash
grep "access violation" logs/tbcv.log
```

### Step 6: Test API Endpoints

Start the API server and test key endpoints:

```bash
# Start server in background
python main.py &
SERVER_PID=$!

# Wait for server to start
sleep 5

# Test health endpoint
curl http://localhost:8000/api/health
# Expected: {"status": "healthy", ...}

# Test validation endpoint
curl -X POST http://localhost:8000/api/validate/file \
  -H "Content-Type: application/json" \
  -d '{"file_path": "README.md"}'
# Expected: {"success": true, "validation_id": "...", ...}

# Test list validations
curl http://localhost:8000/api/validations?limit=10
# Expected: {"validations": [...], "total": ...}

# Test stats endpoint
curl http://localhost:8000/api/stats
# Expected: {"validations_total": ..., ...}

# Stop server
kill $SERVER_PID
```

**Validation**: All endpoints should return 200 status codes with valid JSON.

### Step 7: Run Full Test Suite

Execute comprehensive test suite:

```bash
# Run all tests with coverage
pytest tests/ -v --tb=short --cov=svc --cov=core --cov=api --cov=cli

# Expected: All tests pass, coverage >90%
```

**Validation**:
- 500+ tests passing
- No test failures
- Coverage reports generated
- No deprecation warnings

If tests fail:
1. Check logs in `logs/tbcv.log`
2. Review test output for specific failures
3. Check access guard configuration
4. Verify database is initialized

### Step 8: Enable Block Mode

After validating everything works in warn mode, enable strict enforcement:

Update `config/access_guards.yaml`:

```yaml
enforcement_mode: block  # Enable strict enforcement
log_violations: true
log_level: error
```

**Test with block mode enabled**:

```bash
# This should work (via MCP)
python cli/main.py validate-file README.md

# This would fail if attempted (direct access blocked)
python -c "from core.database import DatabaseManager; DatabaseManager()"
# Expected: RuntimeError: Direct access to DatabaseManager is not allowed
```

**Validation**: Direct access attempts should be blocked, MCP access should work.

## Post-Migration Validation

Complete this checklist after migration:

### CLI Validation
- [ ] All CLI commands execute successfully
- [ ] No "direct access" errors in output
- [ ] Commands produce expected results
- [ ] Help text displays correctly
- [ ] Error handling works properly

### API Validation
- [ ] All API endpoints respond (200 status)
- [ ] WebSocket connections stable
- [ ] Validation operations complete
- [ ] Approval/rejection workflows work
- [ ] Enhancement operations work
- [ ] Workflow creation and monitoring work

### Performance Validation
- [ ] API response times <100ms for simple operations
- [ ] MCP overhead <5ms per operation
- [ ] Database queries performant
- [ ] No memory leaks detected
- [ ] Concurrent operations stable

### Security Validation
- [ ] Access guards blocking direct access (block mode)
- [ ] MCP operations allowed
- [ ] Violations logged correctly
- [ ] No bypass mechanisms found

### Monitoring Validation
- [ ] Logs capture MCP operations
- [ ] Metrics collected correctly
- [ ] Error tracking functional
- [ ] Performance metrics available

## Rollback Procedures

If issues are encountered, follow these rollback steps:

### Emergency Rollback (Immediate)

If system is completely broken:

1. **Disable Access Guards**:
   ```bash
   export MCP_ENFORCE=false
   # OR edit config/access_guards.yaml
   enforcement_mode: disabled
   ```

2. **Restart Services**:
   ```bash
   # Restart API server
   kill $(pgrep -f "python main.py")
   python main.py &
   ```

3. **Verify System Operational**:
   ```bash
   python cli/main.py health
   curl http://localhost:8000/api/health
   ```

### Full Rollback (Planned)

If MCP migration needs to be reversed:

1. **Stop All Services**:
   ```bash
   kill $(pgrep -f "python main.py")
   ```

2. **Revert Code Changes**:
   ```bash
   git log --oneline | grep "MCP"  # Find migration commit
   git revert <migration-commit-hash>
   git push origin main
   ```

3. **Restore Database** (if needed):
   ```bash
   # Stop any processes using database
   cp backup/tbcv.db.backup data/tbcv.db
   ```

4. **Reinstall Dependencies**:
   ```bash
   pip install -r requirements.txt --force-reinstall
   ```

5. **Validate Rollback**:
   ```bash
   pytest tests/ -v
   python main.py &
   python cli/main.py validate-file README.md
   ```

### Partial Rollback (Selective)

If only specific components have issues:

1. **Disable Access Guards** (keep MCP infrastructure):
   ```yaml
   enforcement_mode: disabled
   ```

2. **Allow Direct Access Temporarily**:
   ```bash
   export MCP_ENFORCE=false
   ```

3. **Fix Issues While System Runs**

4. **Re-enable When Fixed**

## Troubleshooting

### Issue: AccessGuardError in Block Mode

**Symptoms**:
```
RuntimeError: Direct access to DatabaseManager is not allowed.
All operations must go through MCP server.
```

**Cause**: Code attempting direct access to business logic.

**Solution 1**: Verify MCP client is used:
```python
# Wrong (direct access)
from core.database import db_manager
results = db_manager.list_validation_results()

# Correct (via MCP)
from svc.mcp_client import get_mcp_sync_client
client = get_mcp_sync_client()
results = client.list_validations()
```

**Solution 2**: Temporarily disable guards for debugging:
```bash
export MCP_ENFORCE=false
```

**Solution 3**: Add exception for legitimate caller:
Edit `core/access_guard.py`:
```python
ALLOWED_CALLERS = [
    # ... existing callers ...
    "your_module_name.",
]
```

### Issue: MCP Method Not Found

**Symptoms**:
```
MCPMethodNotFoundError: Method 'some_method' not found
```

**Cause**: Calling MCP method that doesn't exist.

**Solution**: Verify method exists in MCP server:
```python
from svc.mcp_server import create_mcp_client
server = create_mcp_client()
print(server.registry.methods.keys())  # List all available methods
```

Check documentation: `docs/mcp_integration.md` for complete method list.

### Issue: MCP Timeout

**Symptoms**:
```
TimeoutError: MCP operation timed out after 10s
```

**Cause**: Operation taking longer than timeout setting.

**Solution 1**: Increase timeout:
```python
from svc.mcp_client import MCPSyncClient
client = MCPSyncClient(timeout=30)  # 30 second timeout
```

**Solution 2**: Check if operation is truly hanging:
```bash
# Check logs for stuck operations
tail -f logs/tbcv.log | grep "operation"
```

**Solution 3**: Break operation into smaller chunks if processing large datasets.

### Issue: Import Error for MCP Modules

**Symptoms**:
```
ImportError: cannot import name 'MCPSyncClient'
```

**Cause**: MCP dependencies not installed correctly.

**Solution**:
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Verify installation
python -c "import svc.mcp_client; print('OK')"
```

### Issue: Database Connection Errors

**Symptoms**:
```
OperationalError: unable to open database file
```

**Cause**: Database file missing or inaccessible.

**Solution 1**: Reinitialize database:
```bash
python -c "from core.database import DatabaseManager; DatabaseManager().init_database()"
```

**Solution 2**: Check file permissions:
```bash
ls -la data/tbcv.db
# Should be readable and writable
```

**Solution 3**: Restore from backup:
```bash
cp backup/tbcv.db.backup data/tbcv.db
```

### Issue: Tests Failing After Migration

**Symptoms**: Tests that previously passed now fail.

**Cause**: Tests may be using direct access patterns.

**Solution 1**: Update test to use MCP fixtures:
```python
# Update test signature to use mcp_sync_client fixture
def test_something(mcp_sync_client):
    result = mcp_sync_client.validate_file("test.md")
    assert result["success"]
```

**Solution 2**: Disable guards for specific tests:
```python
import pytest
from core.access_guard import set_enforcement_mode

@pytest.fixture(autouse=True)
def disable_guards():
    set_enforcement_mode("disabled")
    yield
    set_enforcement_mode("block")
```

### Issue: Performance Degradation

**Symptoms**: Operations slower after migration.

**Cause**: MCP adds minimal overhead, but may be cumulative.

**Solution 1**: Profile operations:
```python
import time
from svc.mcp_client import MCPSyncClient

client = MCPSyncClient()
start = time.perf_counter()
result = client.validate_file("test.md")
duration = time.perf_counter() - start
print(f"Operation took {duration*1000:.2f}ms")
```

**Solution 2**: Check for N+1 query patterns:
```python
# Bad: Multiple MCP calls in loop
for validation_id in validation_ids:
    result = client.get_validation(validation_id)  # N calls

# Good: Single bulk operation
results = client.list_validations(ids=validation_ids)  # 1 call
```

**Solution 3**: Use async client for concurrent operations:
```python
import asyncio
from svc.mcp_client import MCPAsyncClient

async def process_files(files):
    client = MCPAsyncClient()
    tasks = [client.validate_file(f) for f in files]
    return await asyncio.gather(*tasks)
```

## Common Migration Patterns

### Pattern 1: Converting CLI Commands

**Before**:
```python
# cli/main.py
from agents.base import agent_registry
from core.database import db_manager

@cli.command()
def validate(file_path):
    orchestrator = agent_registry.get_agent("orchestrator")
    result = await orchestrator.validate_file(file_path)
    return result
```

**After**:
```python
# cli/main.py
from svc.mcp_client import get_mcp_sync_client

@cli.command()
def validate(file_path):
    mcp = get_mcp_sync_client()
    result = mcp.validate_file(file_path)
    return result
```

### Pattern 2: Converting API Endpoints

**Before**:
```python
# api/server.py
from core.database import db_manager

@app.get("/api/validations")
async def list_validations():
    results = db_manager.list_validation_results()
    return results
```

**After**:
```python
# api/server.py
from svc.mcp_client import get_mcp_async_client

@app.get("/api/validations")
async def list_validations():
    mcp = get_mcp_async_client()
    result = await mcp.list_validations()
    return result["validations"]
```

### Pattern 3: Converting Tests

**Before**:
```python
def test_validation(temp_db):
    from core.database import DatabaseManager
    db = DatabaseManager()
    result = db.create_validation_result(...)
    assert result
```

**After**:
```python
def test_validation(mcp_sync_client):
    result = mcp_sync_client.validate_file("test.md")
    assert result["success"]
```

## Best Practices

### DO:
- Always use MCP client for business logic access
- Use sync client (`MCPSyncClient`) for CLI and simple scripts
- Use async client (`MCPAsyncClient`) for API and concurrent operations
- Handle `MCPError` exceptions appropriately
- Log MCP operations for debugging
- Use fixtures in tests for MCP clients
- Start with warn mode before enabling block mode

### DON'T:
- Import business logic directly in CLI/API code
- Bypass access guards in production
- Ignore access violation warnings
- Skip rollback procedure testing
- Disable guards permanently
- Use sync client in async contexts
- Create multiple client instances unnecessarily

## Migration Timeline

Recommended migration schedule:

| Day | Activities | Duration |
|-----|-----------|----------|
| 1 | Pre-migration checklist, backups | 2-4 hours |
| 1 | Steps 1-4 (Dependencies, configuration, database, MCP server) | 2-3 hours |
| 2 | Steps 5-6 (CLI and API testing in warn mode) | 3-4 hours |
| 2 | Step 7 (Full test suite) | 1-2 hours |
| 3 | Step 8 (Enable block mode), Post-migration validation | 2-3 hours |
| 3 | Monitor system, address issues | 2-4 hours |

**Total**: 2-3 days with testing and validation.

## Support and Resources

### Documentation
- **MCP Integration Guide**: `docs/mcp_integration.md` - Complete method reference
- **Architecture Overview**: `docs/architecture.md` - System architecture
- **API Reference**: `docs/api_reference.md` - REST API documentation
- **CLI Usage**: `docs/cli_usage.md` - Command-line interface guide

### Code Examples
- **MCP Server**: `svc/mcp_server.py` - Server implementation
- **MCP Clients**: `svc/mcp_client.py` - Client implementations
- **Tests**: `tests/svc/` - Comprehensive test examples

### Troubleshooting
- **Logs**: `logs/tbcv.log` - System logs
- **Test Output**: Run `pytest -v` for detailed test information
- **Health Check**: `python cli/main.py health` for system status

## Success Criteria

Migration is successful when:

1. ✅ All 500+ tests passing
2. ✅ All CLI commands working via MCP
3. ✅ All API endpoints working via MCP
4. ✅ Access guards enforcing boundaries (block mode)
5. ✅ Performance within targets (<5ms MCP overhead)
6. ✅ No direct access to business logic from CLI/API
7. ✅ System stable under load
8. ✅ Rollback procedures tested and documented

---

**Document Version**: 1.0
**Last Updated**: 2025-12-01
**Maintained By**: TBCV Team
