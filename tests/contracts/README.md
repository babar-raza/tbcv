# API Contract Tests

## Purpose

API contract tests verify that critical public interfaces remain stable across code refactorings. These tests helped catch API drift that caused 147+ test failures in the TBCV project.

## What They Test

Contract tests verify **interface stability**, not implementation details. They ensure:

1. **Methods exist** - Required public methods are present
2. **Signatures match** - Method parameters haven't changed
3. **Return types are correct** - Methods return expected types
4. **Enums are stable** - Enumeration values remain consistent

## Test Files

### `test_database_contract.py`
Verifies the `DatabaseManager` public API:
- Connection methods: `init_database()`, `is_connected()`, `create_tables()`
- Workflow CRUD: `create_workflow()`, `get_workflow()`, `update_workflow()`, `list_workflows()`
- Validation CRUD: `create_validation_result()`, `get_validation_result()`, `list_validation_results()`
- Recommendation CRUD: `create_recommendation()`, `get_recommendation()`, `update_recommendation_status()`
- AuditLog methods: `create_audit_log()`, `list_audit_logs()`
- ORM models: `ValidationResult`, `Recommendation`, `Workflow`, `AuditLog`, `Checkpoint`
- Enums: `ValidationStatus`, `RecommendationStatus`, `WorkflowState`

**77 assertions** covering all critical database operations.

### `test_cache_contract.py`
Verifies the `CacheManager` public API:
- Core operations: `get()`, `put()`, `delete()`
- Clear operations: `clear_l1()`, `clear_l2()`, `clear()`, `clear_agent_cache()`
- Maintenance: `cleanup_expired()`, `get_statistics()`
- LRU Cache: `size()`, `hit_rate()`, `stats()`
- ValidationCache: `content_hash()`, `get_validation_result()`, `put_llm_response()`

**52 assertions** covering all cache layers and operations.

### `test_agent_contract.py`
Verifies the `BaseAgent` public API:
- Core methods: `get_contract()`, `handle_message()`, `register_handler()`
- Built-in handlers: `handle_ping()`, `handle_get_status()`, `handle_get_contract()`
- Cache integration: `get_cached_result()`, `cache_result()`, `clear_cache()`
- Checkpoints: `create_checkpoint()`, `restore_checkpoint()`
- Utilities: `validate_input()`, `calculate_confidence()`, `heartbeat()`
- MCP protocol: `MCPMessage`, `MessageType`, `AgentStatus`
- Registry: `AgentRegistry` with `register_agent()`, `list_agents()`, `broadcast_message()`

**26 assertions** covering the agent framework.

## Running the Tests

```powershell
# Run all contract tests
python -m pytest tests/contracts/ -v

# Run specific contract test file
python -m pytest tests/contracts/test_database_contract.py -v

# Run with coverage
python -m pytest tests/contracts/ --cov=core --cov=agents
```

## Expected Results

All tests should:
- **PASS** - Interfaces are stable
- **Execute in <1s** - Fast verification
- **Require no fixtures** - Self-contained

Example output:
```
tests/contracts/test_agent_contract.py .................... [ 33%]
tests/contracts/test_cache_contract.py ..................... [ 67%]
tests/contracts/test_database_contract.py .................. [100%]

77 passed in 0.69s
```

## Why This Matters

### Problem: API Drift
Without contract tests, refactoring can accidentally break public interfaces:
- Renamed methods → 50+ import errors
- Changed signatures → 30+ parameter mismatches
- Missing methods → 67+ attribute errors

**Total: 147+ cascading test failures from one refactoring**

### Solution: Contract Tests
Contract tests catch breaking changes immediately:
- ✅ Fast feedback (runs in <1s)
- ✅ Clear error messages (exactly which method/signature broke)
- ✅ CI/CD integration (fails build on API drift)
- ✅ Refactoring confidence (internal changes are safe)

## What They DON'T Test

Contract tests intentionally **do not test**:
- Implementation logic (covered by unit tests)
- Integration behavior (covered by integration tests)
- Edge cases (covered by functional tests)
- Performance (covered by benchmark tests)

They only verify the **shape** of the API remains stable.

## When to Update

Update contract tests when you **intentionally** change a public API:

1. **Adding a new method** - Add assertion to verify it exists
2. **Changing a signature** - Update parameter checks
3. **Removing deprecated method** - Remove from required list (with major version bump)
4. **Renaming** - Update expected name AND add migration notes

Never update contract tests to "make tests pass" without understanding the API change.

## Integration with CI/CD

Contract tests should:
- Run on **every commit** (fast execution makes this feasible)
- **Block merges** if failing (API stability is critical)
- Run **before integration tests** (catch issues early)
- Generate **coverage reports** for interface completeness

## Design Principles

1. **No mocking** - Test against real class definitions
2. **No fixtures** - Self-contained and fast
3. **No side effects** - Read-only verification
4. **Clear assertions** - One concept per test
5. **Informative failures** - Explicitly state what's missing

## Maintenance

Review contract tests when:
- Planning a major version bump (acceptable breaking changes)
- Deprecating features (mark as optional before removal)
- Refactoring core modules (verify interfaces remain stable)
- Onboarding new developers (explain API stability importance)

## Example: Catching API Drift

Before contract tests:
```python
# Someone refactors database.py
class DatabaseManager:
    def store_validation(self, ...):  # Renamed from create_validation_result
        ...

# 67 tests fail with AttributeError: 'DatabaseManager' has no attribute 'create_validation_result'
```

After contract tests:
```python
# Contract test fails immediately
def test_database_manager_interface():
    assert hasattr(DatabaseManager, 'create_validation_result')
    # FAIL: DatabaseManager missing required method: create_validation_result

# Developer realizes the rename breaks the API
# Either: revert the rename, or add alias for backward compatibility
```

## Success Metrics

Contract tests are successful if they:
- ✅ Catch 100% of breaking API changes
- ✅ Execute in <1 second total
- ✅ Require no database/network/fixtures
- ✅ Have zero false positives
- ✅ Provide clear error messages

Current status: **77 tests, 100% pass rate, 0.69s execution time**
