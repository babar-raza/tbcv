# P1: Baseline Coverage Report
**Date**: 2025-11-19
**Status**: COMPLETED

## Executive Summary

This report documents the initial state of the TBCV test suite and coverage before beginning the systematic test coverage improvement project.

### Test Execution Results
- **Total Tests Run**: 127
- **Passed**: 73 (57.5%)
- **Failed**: 41 (32.3%)
- **Skipped**: 13 (10.2%)

### Overall Coverage Summary

Based on pytest coverage run targeting `agents`, `core`, `api`, `cli`, and `svc` packages:

**Coverage by Package:**
- **agents/**: ~38-83% (varies by module, average ~56%)
- **core/**: ~0-72% (varies significantly)
- **api/**: ~0-30% (very low coverage)
- **cli/**: Not fully measured
- **svc/**: Not fully measured

## Module Inventory

### Tier A Modules (Target: ~100% Coverage)

#### Agents (agents/)
1. **base.py** - 70% coverage - MCP-compliant base agent
2. **truth_manager.py** - 72% coverage - Plugin truth data indexing
3. **fuzzy_detector.py** - 83% coverage (BEST) - Plugin detection algorithms
4. **content_validator.py** - 52% coverage - Content structure validation
5. **content_enhancer.py** - 49% coverage - Content improvement
6. **llm_validator.py** - 34% coverage - AI-powered validation
7. **code_analyzer.py** - 57% coverage - Code quality analysis
8. **recommendation_agent.py** - 50% coverage - Recommendation generation
9. **enhancement_agent.py** - 21% coverage (WORST) - Recommendation application
10. **orchestrator.py** - 68% coverage - Workflow coordination

#### Core Infrastructure (core/)
1. **config.py** - 66% coverage - Configuration management
2. **validation_store.py** - 43% coverage - Validation result storage
3. **rule_manager.py** - 25% coverage - Validation rules
4. **family_detector.py** - 50% coverage - Product family detection
5. **ingestion.py** - 0% coverage (UNTESTED) - Content ingestion
6. **path_validator.py** - 34% coverage - Path validation
7. **startup_checks.py** - 23% coverage - System health checks
8. **prompt_loader.py** - 0% coverage (UNTESTED) - LLM prompt loading
9. **utilities.py** - 21% coverage - Utility functions

#### API Services (api/)
1. **server.py** - 30% coverage - Main FastAPI application
2. **websocket_endpoints.py** - 58% coverage - WebSocket real-time updates
3. **additional_endpoints.py** - 22% coverage - Additional API endpoints
4. **export_endpoints.py** - 0% coverage (UNTESTED) - Export functionality
5. **services/mcp_client.py** - 64% coverage - MCP client
6. **services/recommendation_consolidator.py** - 26% coverage - Recommendation consolidation
7. **services/status_recalculator.py** - 0% coverage (UNTESTED) - Status recalculation
8. **services/live_bus.py** - 0% coverage (UNTESTED) - Event bus

#### CLI (cli/)
1. **main.py** - 35% coverage - CLI commands and dispatch

#### MCP Server (svc/)
1. **mcp_server.py** - Coverage not measured - JSON-RPC handlers

#### Top-level Scripts
1. **startup_check.py** - Not measured
2. **validate_system.py** - Not measured
3. **health.py** - Not measured

### Tier B Modules (Target: ≥90-95% Coverage)

1. **core/database.py** - 55% coverage - SQLAlchemy ORM
2. **core/cache.py** - 55% coverage - Two-level caching
3. **core/logging.py** - 61% coverage - Structured logging
4. **core/ollama.py** - 0% coverage (UNTESTED) - LLM client
5. **core/ollama_validator.py** - 0% coverage (UNTESTED) - Ollama validation
6. **core/io_win.py** - 16% coverage - Windows I/O utilities
7. **api/dashboard.py** - 26% coverage - Web UI routes
8. **api/server_extensions.py** - 0% coverage (UNTESTED) - Server extensions

### Tier C Modules (Best Effort)

1. **templates/** - Not measured (Jinja templates)
2. **tools/** - Not in scope for current coverage

## Existing Test Files

### Integration/Full-Stack Tests (tests/)
1. **test_cli_web_parity.py** - 2 failures - CLI vs API parity
2. **test_endpoints_offline.py** - 1 failure - Offline endpoint tests
3. **test_endpoints_live.py** - Skipped (requires live server)
4. **test_enhancer_consumes_validation.py** - 1 failure - Enhancement workflow
5. **test_everything.py** - 7 failures - Comprehensive system tests
6. **test_framework.py** - Passing - Test framework utilities
7. **test_full_stack_local.py** - Failures - Full stack tests
8. **test_fuzzy_logic.py** - Passing - Fuzzy detection tests
9. **test_generic_validator.py** - Passing - Generic validation
10. **test_idempotence_and_schemas.py** - Failures - Idempotency tests
11. **test_performance.py** - Skipped (performance benchmarks)
12. **test_recommendations.py** - Failures - Recommendation system
13. **test_smoke_agents.py** - Passing - Agent smoke tests
14. **test_truth_validation.py** - 13 failures - Truth validation
15. **test_truths_and_rules.py** - 4 failures - Truth/rule integration
16. **test_validation_persistence.py** - 1 failure - Validation persistence
17. **test_websocket.py** - Status unknown

### Test Configuration
- **conftest.py** - Fixtures and configuration
- **run_all_tests.py** - Test runner script

## Key Findings

### Coverage Gaps (0% Coverage)
The following critical modules have ZERO coverage:
1. **core/ingestion.py** (Tier A)
2. **core/prompt_loader.py** (Tier A)
3. **core/ollama.py** (Tier B)
4. **core/ollama_validator.py** (Tier B)
5. **api/export_endpoints.py** (Tier A)
6. **api/services/status_recalculator.py** (Tier A)
7. **api/services/live_bus.py** (Tier A)
8. **api/server_extensions.py** (Tier B)

### Low Coverage (<30%)
1. **agents/enhancement_agent.py** - 21% (Tier A - CRITICAL)
2. **core/io_win.py** - 16% (Tier B)
3. **core/startup_checks.py** - 23% (Tier A)
4. **core/utilities.py** - 21% (Tier A)
5. **core/rule_manager.py** - 25% (Tier A)
6. **api/additional_endpoints.py** - 22% (Tier A)
7. **api/dashboard.py** - 26% (Tier B)
8. **api/services/recommendation_consolidator.py** - 26% (Tier A)

### Test Failures Requiring Attention
1. **Fixture Issues**: Several tests fail due to incorrect fixture usage (await on non-async fixtures)
2. **Import Errors**: `test_truths_and_rules.py` has wrong import paths (missing `agents.` prefix)
3. **API Response Mismatches**: Tests expect different status codes/responses than actual
4. **Agent Registration Issues**: Tests failing due to agent registry structure changes

### Test Organization Issues
1. **No per-module test structure**: All tests are in root `tests/` directory
2. **No separation**: Unit vs integration tests are mixed
3. **Mock usage**: Limited use of mocks for external dependencies
4. **Determinism**: Some tests may have non-deterministic behavior

## Recommendations for P2-P8

### Immediate Priorities (P2-P3)
1. Fix test fixture issues (async/await problems)
2. Fix import errors in existing tests
3. Create modular test structure:
   - `tests/agents/`
   - `tests/core/`
   - `tests/api/`
   - `tests/cli/`
   - `tests/svc/`
4. Extract common fixtures to `conftest.py`

### Critical Coverage Additions (P4)
1. **agents/enhancement_agent.py** (21% → 100%)
2. **core/ingestion.py** (0% → 100%)
3. **core/prompt_loader.py** (0% → 100%)
4. **api/export_endpoints.py** (0% → 100%)
5. **api/services/status_recalculator.py** (0% → 100%)
6. **api/services/live_bus.py** (0% → 100%)
7. All other Tier A modules to 100%

### High-Priority Coverage (P5)
1. **core/ollama.py** with full mocking (0% → 95%)
2. **core/ollama_validator.py** with full mocking (0% → 95%)
3. **core/database.py** (55% → 95%)
4. **core/cache.py** (55% → 95%)
5. All other Tier B modules to 90-95%

## Baseline Metrics

### Test Count by Category
- **Unit Tests**: ~40 (estimated, mixed with integration)
- **Integration Tests**: ~25
- **Performance Tests**: ~10 (skipped)
- **End-to-End Tests**: ~15

### Module Count by Tier
- **Tier A**: 34 modules
- **Tier B**: 8 modules
- **Tier C**: Templates + tools (varied)

### Coverage Targets
- **Current Overall**: ~40-50% (estimated weighted average)
- **Target Overall**: ≥90%
- **Tier A Target**: ~100%
- **Tier B Target**: ≥90-95%

## Next Steps

1. **P2**: Create detailed module-by-module coverage plan
2. **P3**: Refactor test layout and fix existing test failures
3. **P4**: Bring all Tier A modules to ~100% coverage
4. **P5**: Raise Tier B modules to ≥90-95% coverage
5. **P6**: Add best-effort Tier C tests
6. **P7**: Stabilize suite (deterministic, no flakes)
7. **P8**: Final validation and acceptance

---
**Report Generated**: 2025-11-19
**Phase**: P1 - Repository Review and Baseline
**Status**: COMPLETE
