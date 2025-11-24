# P3: Test Layout Refactor - Progress Report
**Date**: 2025-11-19
**Status**: IN PROGRESS (Foundation Complete)

## Overview

Phase 3 involves refactoring the test suite to organize tests by module, extract common fixtures, fix broken tests, and establish patterns for comprehensive coverage. This is a foundational phase that enables P4-P8.

## Completed Work

### 1. Directory Structure Created ✅

Created modular test directory structure:
```
tests/
├── agents/          # Agent-specific tests
│   ├── __init__.py
│   ├── test_base.py  ✅ CREATED
│   └── test_enhancement_agent.py  ✅ CREATED
├── core/            # Core module tests
│   └── __init__.py
├── api/             # API endpoint tests
│   └── __init__.py
├── cli/             # CLI command tests
│   └── __init__.py
├── svc/             # MCP server tests
│   └── __init__.py
├── fixtures/        # Test data fixtures
└── conftest.py      ✅ ENHANCED
```

### 2. Enhanced conftest.py ✅

Created comprehensive shared fixtures in `tests/conftest.py`:

**Database Fixtures:**
- `db_manager` - In-memory SQLite database per test
- `db_session` - Database session management

**API Fixtures:**
- `api_client` - FastAPI TestClient
- `async_api_client` - Async HTTP client

**Agent Mocks (NO REAL LLM CALLS):**
- `mock_truth_manager` - Mocked TruthManagerAgent
- `mock_fuzzy_detector` - Mocked FuzzyDetectorAgent
- `mock_content_validator` - Mocked ContentValidatorAgent
- `mock_llm_validator` - **Mocked LLM with NO real calls**
- `mock_recommendation_agent` - Mocked RecommendationAgent
- `mock_enhancement_agent` - Mocked EnhancementAgent
- `mock_orchestrator` - Mocked OrchestratorAgent

**Sample Data Fixtures:**
- `sample_markdown` - Sample markdown content
- `sample_yaml_content` - YAML-only content
- `sample_truth_data` - Plugin truth data
- `sample_validation_result` - Validation result
- `sample_recommendations` - Recommendation data

**File System Fixtures:**
- `temp_dir` - Temporary directory with cleanup
- `temp_file` - Temporary file
- `sample_files_dir` - Directory with multiple test files

**External Service Mocks:**
- `mock_ollama_client` - **Mocked Ollama (NO real LLM calls)**
- `mock_http_requests` - Mocked HTTP requests
- `mock_cache_manager` - Mocked cache

**Configuration Fixtures:**
- `test_config` - Test configuration
- `mock_settings` - Mocked settings

**Utility Fixtures:**
- `assert_valid_mcp_message` - MCP message validation
- `assert_valid_validation_result` - Validation result validation

**Custom Pytest Markers:**
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.slow` - Slow tests
- `@pytest.mark.live` - Tests requiring live services
- `@pytest.mark.performance` - Performance tests

### 3. Initial Module Tests Created ✅

**tests/agents/test_base.py** (NEW)
- Comprehensive tests for `agents/base.py`
- Coverage for all enums, dataclasses, and BaseAgent
- Tests for MCP message handling
- Tests for agent lifecycle
- Edge case and error handling tests
- **Target**: 100% coverage of base.py

**tests/agents/test_enhancement_agent.py** (NEW)
- Comprehensive tests for `agents/enhancement_agent.py`
- Tests for RecommendationResult and EnhancementResult
- Tests for recommendation application
- Tests for diff generation
- Tests for status updates
- Mock-based unit tests
- Integration test placeholders
- **Target**: Raise coverage from 21% to 100%

## Remaining Work

### Critical Test Files Needed (0% Coverage Modules)

**Tier A - Priority 1 (0% coverage):**
1. ❌ `tests/core/test_ingestion.py`
2. ❌ `tests/core/test_prompt_loader.py`
3. ❌ `tests/api/test_export_endpoints.py`
4. ❌ `tests/api/services/test_status_recalculator.py`
5. ❌ `tests/api/services/test_live_bus.py`

**Tier A - Priority 2 (Low coverage <30%):**
6. ❌ `tests/core/test_rule_manager.py` (25% -> 100%)
7. ❌ `tests/core/test_startup_checks.py` (23% -> 100%)
8. ❌ `tests/core/test_utilities.py` (21% -> 100%)
9. ❌ `tests/api/test_additional_endpoints.py` (22% -> 100%)
10. ❌ `tests/api/services/test_recommendation_consolidator.py` (26% -> 100%)

**Tier A - Priority 3 (Medium coverage):**
11. ❌ `tests/agents/test_truth_manager.py` (72% -> 100%)
12. ❌ `tests/agents/test_content_validator.py` (52% -> 100%)
13. ❌ `tests/agents/test_content_enhancer.py` (49% -> 100%)
14. ❌ `tests/agents/test_llm_validator.py` (34% -> 100%) - **MUST MOCK ALL LLM CALLS**
15. ❌ `tests/agents/test_code_analyzer.py` (57% -> 100%)
16. ❌ `tests/agents/test_recommendation_agent.py` (50% -> 100%)
17. ❌ `tests/agents/test_orchestrator.py` (68% -> 100%)
18. ❌ `tests/agents/test_fuzzy_detector.py` (83% -> 100%) - Already high, push to 100%

**Tier A - Other Core:**
19. ❌ `tests/core/test_config.py` (66% -> 100%)
20. ❌ `tests/core/test_validation_store.py` (43% -> 100%)
21. ❌ `tests/core/test_family_detector.py` (50% -> 100%)
22. ❌ `tests/core/test_path_validator.py` (34% -> 100%)

**Tier A - API:**
23. ❌ `tests/api/test_server.py` (30% -> 100%)
24. ❌ `tests/api/test_websocket_endpoints.py` (58% -> 100%)
25. ❌ `tests/api/services/test_mcp_client.py` (64% -> 100%)

**Tier A - CLI/SVC:**
26. ❌ `tests/cli/test_main.py` (35% -> 100%)
27. ❌ `tests/svc/test_mcp_server.py` (Not measured -> 100%)

**Tier A - Top-level:**
28. ❌ `tests/test_startup_check.py`
29. ❌ `tests/test_validate_system.py`
30. ❌ `tests/test_health.py`

### Tier B Test Files Needed (≥90-95% Target)

**Tier B - Priority 1 (0% coverage):**
31. ❌ `tests/core/test_ollama.py` (0% -> 95%) - **MUST MOCK ALL LLM CALLS**
32. ❌ `tests/core/test_ollama_validator.py` (0% -> 95%) - **MUST MOCK ALL LLM CALLS**
33. ❌ `tests/api/test_server_extensions.py` (0% -> 90%)

**Tier B - Priority 2 (Low-medium coverage):**
34. ❌ `tests/core/test_database.py` (55% -> 95%)
35. ❌ `tests/core/test_cache.py` (55% -> 95%)
36. ❌ `tests/core/test_logging.py` (61% -> 95%)
37. ❌ `tests/core/test_io_win.py` (16% -> 90%)
38. ❌ `tests/api/test_dashboard.py` (26% -> 90%)

### Existing Test Migration

**Existing tests to reorganize/fix:**
1. ❌ Fix import errors in `test_truths_and_rules.py` (missing `agents.` prefix)
2. ❌ Fix fixture issues in `test_cli_web_parity.py` (await on non-async fixtures)
3. ❌ Fix API response assertions in `test_everything.py`
4. ❌ Move/split integration tests to appropriate locations
5. ❌ Update all tests to use new fixtures from enhanced conftest.py

## Test Pattern Established

The following pattern has been established for all tests:

### Unit Test Pattern (No Mocks)
```python
@pytest.mark.unit
class TestModuleName:
    def test_function_name(self):
        # Test pure logic
        result = function(input)
        assert result == expected
```

### Unit Test Pattern (With Mocks)
```python
@pytest.mark.unit
class TestModuleNameWithMocks:
    @pytest.mark.asyncio
    async def test_with_mock(self, mock_dependency):
        # Test with mocked external dependencies
        with patch('module.external_dep', mock_dependency):
            result = await function(input)
            assert result == expected
```

### Integration Test Pattern
```python
@pytest.mark.integration
class TestModuleNameIntegration:
    @pytest.mark.asyncio
    async def test_integration(self, db_manager, api_client):
        # Test with real components
        result = await full_workflow()
        assert result == expected
```

## Key Principles Established

1. **No Real External Calls**: All LLM, HTTP, and external service calls MUST be mocked
2. **In-Memory Database**: Use in-memory SQLite for all database tests
3. **Fixture Reuse**: Leverage shared fixtures from conftest.py
4. **Deterministic Tests**: No time-based flakiness, no real network calls
5. **Clear Markers**: Use pytest markers to categorize tests
6. **Comprehensive Coverage**: Test happy paths, edge cases, and error handling

## Next Steps (P3 Completion)

To complete P3, the following work is needed:

1. **Create remaining test files** for all Tier A modules
2. **Fix existing test failures** (41 failing tests)
3. **Migrate existing tests** to new structure
4. **Run full test suite** to ensure no regressions
5. **Verify test organization** is complete

Then proceed to:
- **P4**: Execute tests and raise Tier A coverage to 100%
- **P5**: Execute tests and raise Tier B coverage to 90-95%
- **P6**: Add Tier C best-effort tests
- **P7**: Stabilize suite (deterministic, no flakes)
- **P8**: Final validation and runbook

## Estimated Remaining Test Files

- **Total test files needed**: ~41 files
- **Created so far**: 2 files (base.py, enhancement_agent.py)
- **Remaining**: ~39 files
- **Estimated effort**: Each file requires:
  - 10-30 test functions
  - Happy path, edge cases, error handling
  - Mock setup and teardown
  - Integration test scenarios

## Status Summary

✅ **Foundation Complete**:
- Directory structure created
- Enhanced conftest.py with comprehensive fixtures
- Test patterns established
- Initial examples created

⏳ **In Progress**:
- Creating remaining 39 test files
- Fixing existing test failures
- Migrating existing tests

❌ **Not Started**:
- P4-P8 execution phases

---
**Report Generated**: 2025-11-19
**Phase**: P3 - Test Layout Refactor
**Status**: FOUNDATION COMPLETE, DETAILED WORK IN PROGRESS
