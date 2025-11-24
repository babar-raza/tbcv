# P2: Detailed Coverage Plan per Module
**Date**: 2025-11-19
**Status**: COMPLETED

## Overview

This document provides a detailed test coverage plan for each Tier A and Tier B module, specifying:
- Public functions/classes/methods to test
- Key branches and conditional logic
- Test types: Unit (with/without mocks) and Integration
- Specific test scenarios for each module

---

## TIER A MODULES (~100% Coverage Required)

### 1. agents/base.py (Current: 70%)

**Public API:**
- `AgentStatus` enum
- `MessageType` enum
- `MCPMessage` dataclass (from_dict, to_dict, __post_init__)
- `AgentCapability` dataclass
- `AgentContract` dataclass
- `BaseAgent` abstract class (process_request, get_contract, get_status, etc.)

**Unit Tests (No Mocks):**
- `MCPMessage` creation with auto-generated ID and timestamp
- `MCPMessage.to_dict()` serialization
- `MCPMessage.from_dict()` deserialization
- `AgentCapability` creation with side_effects defaulting
- `AgentContract` creation
- Enum value validation for `AgentStatus` and `MessageType`

**Unit Tests (With Mocks):**
- `BaseAgent` lifecycle (start, stop, pause, resume)
- `BaseAgent.process_request()` with valid/invalid methods
- `BaseAgent` error handling with cache failures (mock cache_manager)
- `BaseAgent` performance logging (mock PerformanceLogger)
- `BaseAgent` status transitions (STARTING → READY → BUSY → ERROR → STOPPED)

**Integration Tests:**
- BaseAgent subclass instantiation and contract generation
- End-to-end message handling via orchestrator

**Coverage Goal**: 100%
**Priority**: HIGH

---

### 2. agents/truth_manager.py (Current: 72%)

**Public API:**
- `PluginInfo` dataclass
- `CombinationRule` dataclass
- `TruthDataIndex` dataclass
- `TruthManagerAgent` class (load_truth, lookup_plugin, search_plugins, check_combination, etc.)

**Unit Tests (No Mocks):**
- `PluginInfo` creation and to_dict()
- `CombinationRule` creation and to_dict()
- B-tree indexing logic for plugin lookup
- SHA-256 versioning for change detection
- Pattern matching rule compilation

**Unit Tests (With Mocks):**
- Truth file loading with missing/corrupted files (mock Path, file I/O)
- Cache hits/misses (mock cache_manager)
- Database lookup failures (mock db_manager)
- Missing truth directory handling

**Integration Tests:**
- End-to-end truth loading from truth/ directory
- Plugin lookup via orchestrator
- Combination validation against real truth data

**Coverage Goal**: 100%
**Priority**: HIGH (business-critical)

---

### 3. agents/fuzzy_detector.py (Current: 83%)

**Public API:**
- `FuzzyDetectorAgent` class (detect_plugins, apply_fuzzy_matching, calculate_similarity, etc.)
- Levenshtein distance calculation
- Jaro-Winkler similarity
- Context window analysis

**Unit Tests (No Mocks):**
- Exact pattern matching
- Fuzzy matching with varying thresholds
- Levenshtein distance edge cases (empty strings, identical strings, single character)
- Jaro-Winkler similarity calculations
- Context window extraction
- Confidence scoring algorithm

**Unit Tests (With Mocks):**
- TruthManager integration (mock truth data)
- Cache behavior (mock cache_manager)
- Performance under heavy load

**Integration Tests:**
- Detection across real markdown files
- Multi-plugin detection scenarios
- Combination rule triggering

**Coverage Goal**: 100%
**Priority**: CRITICAL (already 83%, push to 100%)

---

### 4. agents/content_validator.py (Current: 52%)

**Public API:**
- `ContentValidatorAgent` class (validate_content, validate_yaml, validate_markdown, validate_code, validate_links, etc.)
- YAML frontmatter validation
- Markdown structure validation
- Code quality checks
- Link validation

**Unit Tests (No Mocks):**
- YAML parsing (valid, invalid, missing)
- Markdown structure validation (headings, lists, code blocks)
- Code snippet extraction
- Validation rule application
- Issue severity classification

**Unit Tests (With Mocks):**
- Link validation with HTTP failures (mock requests)
- Image checking with missing files (mock file I/O)
- Rule manager failures (mock rule_manager)
- Truth manager integration (mock TruthManagerAgent)

**Integration Tests:**
- Full content validation workflow
- Multi-stage validation (YAML + Markdown + Code)
- Validation persistence to database

**Coverage Goal**: 100%
**Priority**: CRITICAL

---

### 5. agents/content_enhancer.py (Current: 49%)

**Public API:**
- `ContentEnhancerAgent` class (enhance_content, add_plugin_links, apply_templates, etc.)
- Plugin link insertion
- Informational text addition
- Duplicate prevention
- Rewrite ratio limits

**Unit Tests (No Mocks):**
- Link insertion logic
- Duplicate detection
- Formatting preservation
- Template application
- Rewrite ratio calculation

**Unit Tests (With Mocks):**
- Truth manager integration (mock plugin data)
- Safety gating (mock rewrite ratio checks)
- Template rendering failures (mock template engine)

**Integration Tests:**
- End-to-end enhancement workflow
- Enhancement with fuzzy-detected plugins
- Enhancement idempotence testing

**Coverage Goal**: 100%
**Priority**: HIGH

---

### 6. agents/llm_validator.py (Current: 34%)

**Public API:**
- `LLMValidatorAgent` class (validate_with_llm, call_ollama, parse_llm_response, etc.)
- Ollama integration
- Fallback to OpenAI/Gemini
- Temperature and token limit configuration

**Unit Tests (No Mocks):**
- Response parsing logic
- Error message extraction
- Configuration validation

**Unit Tests (With Mocks):**
- **ALL Ollama calls mocked** (no real LLM calls)
- HTTP timeout handling (mock requests)
- Retry logic with exponential backoff (mock time.sleep)
- Fallback provider switching (mock multiple providers)
- Response payload construction

**Integration Tests:**
- Mocked end-to-end LLM validation flow
- Integration with ContentValidatorAgent (mocked LLM)

**Coverage Goal**: 100%
**Priority**: CRITICAL (must fully mock all LLM calls)

---

### 7. agents/code_analyzer.py (Current: 57%)

**Public API:**
- `CodeAnalyzerAgent` class (analyze_code, check_security, assess_complexity, etc.)
- Python, C#, Java, JavaScript analysis
- Security scanning
- Complexity assessment
- LLM integration for advanced analysis

**Unit Tests (No Mocks):**
- Code parsing (valid/invalid syntax)
- Security pattern detection
- Complexity metrics calculation
- Language detection

**Unit Tests (With Mocks):**
- LLM integration (mock LLMValidatorAgent)
- File I/O failures (mock Path operations)
- Performance optimization suggestions

**Integration Tests:**
- Multi-language code analysis
- Integration with validation workflow

**Coverage Goal**: 100%
**Priority**: HIGH

---

### 8. agents/recommendation_agent.py (Current: 50%)

**Public API:**
- `RecommendationAgent` class (generate_recommendations, apply_confidence_thresholds, persist_recommendations, etc.)
- Validation result analysis
- Confidence scoring
- Approval workflow support

**Unit Tests (No Mocks):**
- Recommendation generation logic
- Confidence threshold application
- Issue categorization
- Recommendation prioritization

**Unit Tests (With Mocks):**
- Database persistence (mock db_manager)
- Validation store lookups (mock validation_store)
- Cache behavior (mock cache_manager)

**Integration Tests:**
- End-to-end recommendation workflow
- Human approval simulation
- Recommendation-to-enhancement pipeline

**Coverage Goal**: 100%
**Priority**: HIGH

---

### 9. agents/enhancement_agent.py (Current: 21% - CRITICAL)

**Public API:**
- `RecommendationResult` class
- `EnhancementResult` class
- `EnhancementAgent` class (enhance_with_recommendations, apply_recommendation, generate_diff, etc.)
- Approved recommendation application
- Diff generation
- Content versioning

**Unit Tests (No Mocks):**
- `RecommendationResult` creation and to_dict()
- `EnhancementResult` creation and to_dict()
- Diff generation (difflib integration)
- Content version calculation
- Applied/skipped counting

**Unit Tests (With Mocks):**
- Database operations (mock db_manager for fetching recommendations)
- Recommendation status updates (mock status transitions)
- File I/O for backups (mock Path operations)

**Integration Tests:**
- Full enhancement workflow (validation → recommendations → approval → enhancement)
- Enhancement with multiple recommendations
- Enhancement rollback scenarios

**Coverage Goal**: 100%
**Priority**: CRITICAL (lowest current coverage at 21%)

---

### 10. agents/orchestrator.py (Current: 68%)

**Public API:**
- `OrchestratorAgent` class (coordinate_workflow, execute_step, checkpoint, recover, retry, etc.)
- Multi-step workflow coordination
- Concurrency control
- Checkpointing and recovery
- Retry with exponential backoff

**Unit Tests (No Mocks):**
- Workflow step execution order
- Checkpoint creation and restoration
- Retry logic with backoff calculation
- Concurrency limiting

**Unit Tests (With Mocks):**
- Agent communication (mock all agent types)
- Database workflow persistence (mock db_manager)
- Cache integration (mock cache_manager)
- Error propagation across steps

**Integration Tests:**
- Full multi-step workflow (validation → recommendation → enhancement)
- Workflow recovery from checkpoint
- Concurrent workflow execution
- Workflow cancellation

**Coverage Goal**: 100%
**Priority**: CRITICAL (orchestration backbone)

---

## TIER A: Core Modules

### 11. core/config.py (Current: 66%)

**Public API:**
- `get_settings()` function
- Settings classes (Pydantic models)
- YAML configuration loading
- Environment variable overrides
- Configuration validation

**Unit Tests (No Mocks):**
- Settings instantiation with defaults
- YAML parsing (valid/invalid structures)
- Environment variable override logic
- Configuration schema validation
- Nested configuration access

**Unit Tests (With Mocks):**
- Missing configuration files (mock Path)
- Environment variable loading (mock os.environ)
- Hot-reload functionality (mock file watchers)

**Integration Tests:**
- Full configuration loading from config/main.yaml
- Agent-specific config loading from config/agent.yaml

**Coverage Goal**: 100%

---

### 12. core/validation_store.py (Current: 43%)

**Public API:**
- `ValidationStore` class
- Validation result storage
- Querying and filtering
- Performance metrics tracking

**Unit Tests (No Mocks):**
- Result serialization/deserialization
- Query building
- Filter application
- Metrics calculation

**Unit Tests (With Mocks):**
- Database operations (mock db_manager)
- Cache integration (mock cache_manager)
- Concurrent access handling

**Integration Tests:**
- End-to-end validation storage and retrieval
- Integration with recommendation system

**Coverage Goal**: 100%

---

### 13. core/rule_manager.py (Current: 25%)

**Public API:**
- `RuleManager` class (load_rules, apply_rule, validate_rule, etc.)
- Rule loading from JSON
- Rule application
- Rule validation

**Unit Tests (No Mocks):**
- Rule parsing from JSON
- Rule validation logic
- Rule prioritization
- Rule matching

**Unit Tests (With Mocks):**
- Missing rule files (mock Path)
- Corrupted rule data (mock JSON parsing)
- Cache behavior (mock cache_manager)

**Integration Tests:**
- Rule application in validation workflow
- Rule combination with truth data

**Coverage Goal**: 100%
**Priority**: HIGH (currently only 25%)

---

### 14. core/family_detector.py (Current: 50%)

**Public API:**
- `FamilyDetector` class
- Product family detection (words, cells, slides, pdf)
- Pattern matching for family identification

**Unit Tests (No Mocks):**
- Family detection from file paths
- Family detection from content
- Multi-family detection
- Edge cases (no family, multiple families)

**Unit Tests (With Mocks):**
- TruthManager integration (mock truth data)
- Cache behavior

**Integration Tests:**
- Family detection in full validation workflow

**Coverage Goal**: 100%

---

### 15. core/ingestion.py (Current: 0% - UNTESTED)

**Public API:**
- Content ingestion functions
- File parsing
- Format detection

**Unit Tests (No Mocks):**
- File parsing (various formats)
- Format detection logic
- Content extraction

**Unit Tests (With Mocks):**
- File I/O failures (mock Path operations)
- Unsupported formats (error handling)

**Integration Tests:**
- Ingestion via CLI
- Ingestion via API

**Coverage Goal**: 100%
**Priority**: CRITICAL (0% current coverage)

---

### 16. core/path_validator.py (Current: 34%)

**Public API:**
- `PathValidator` class
- Path validation and normalization
- Security checks (traversal prevention)

**Unit Tests (No Mocks):**
- Valid path normalization
- Path traversal detection
- Windows/Unix path handling
- Relative vs absolute path resolution

**Unit Tests (With Mocks):**
- File existence checking (mock Path.exists)
- Permission checks (mock file permissions)

**Integration Tests:**
- Path validation in file validation workflow

**Coverage Goal**: 100%

---

### 17. core/startup_checks.py (Current: 23%)

**Public API:**
- System health check functions
- Dependency validation
- Configuration verification

**Unit Tests (No Mocks):**
- Health check logic
- Dependency version checking

**Unit Tests (With Mocks):**
- Missing dependencies (mock import failures)
- Database connectivity failures (mock db_manager)
- Ollama availability checks (mock HTTP requests)

**Integration Tests:**
- Full system startup sequence

**Coverage Goal**: 100%

---

### 18. core/prompt_loader.py (Current: 0% - UNTESTED)

**Public API:**
- LLM prompt loading
- Template rendering

**Unit Tests (No Mocks):**
- Prompt template loading
- Variable substitution
- Prompt validation

**Unit Tests (With Mocks):**
- Missing prompt files (mock Path)
- Template rendering errors

**Integration Tests:**
- Prompt loading in LLM validation workflow

**Coverage Goal**: 100%
**Priority**: CRITICAL (0% current coverage)

---

### 19. core/utilities.py (Current: 21%)

**Public API:**
- Utility functions (string manipulation, date formatting, etc.)
- Helper functions used across modules

**Unit Tests (No Mocks):**
- All utility functions with edge cases
- String manipulation edge cases
- Date/time formatting
- Data structure utilities

**Unit Tests (With Mocks):**
- Functions that interact with external systems (if any)

**Coverage Goal**: 100%

---

## TIER A: API Modules

### 20-28. API Modules

See separate sections for:
- `api/server.py`
- `api/websocket_endpoints.py`
- `api/additional_endpoints.py`
- `api/export_endpoints.py`
- `api/services/mcp_client.py`
- `api/services/recommendation_consolidator.py`
- `api/services/status_recalculator.py`
- `api/services/live_bus.py`

All API modules require:
- **Unit tests with FastAPI TestClient** (no real HTTP calls)
- **Mock all agent interactions**
- **Mock database operations**
- **Test request/response schemas**
- **Test error handling (404, 500, 422, etc.)**

**Coverage Goal**: 100% for all

---

### 29. cli/main.py (Current: 35%)

**Public API:**
- Click command definitions
- CLI commands (validate-file, validate-directory, recommendations, etc.)
- Rich console output

**Unit Tests (No Mocks):**
- Command parsing
- Argument validation
- Help text generation

**Unit Tests (With Mocks):**
- Agent invocations (mock all agents)
- File I/O (mock Path operations)
- Rich console output (mock console)

**Integration Tests:**
- CLI command execution via subprocess
- CLI-API parity verification

**Coverage Goal**: 100%

---

### 30. svc/mcp_server.py (Current: Not measured)

**Public API:**
- JSON-RPC handler
- MCP protocol implementation

**Unit Tests (No Mocks):**
- JSON-RPC message parsing
- Protocol compliance

**Unit Tests (With Mocks):**
- Agent communication (mock agents)
- Error handling

**Integration Tests:**
- MCP client-server communication

**Coverage Goal**: 100%

---

### 31-33. Top-level Scripts

- `startup_check.py`
- `validate_system.py`
- `health.py`

**Coverage Goal**: 100% each

---

## TIER B MODULES (≥90-95% Coverage)

### 34. core/database.py (Current: 55%)

**Unit Tests (With Mocks):**
- Use in-memory SQLite for all tests
- Schema creation and migration
- CRUD operations for all tables (Workflow, Validation, Recommendation, etc.)
- Connection pooling
- Transaction handling
- Audit logging

**Integration Tests:**
- Multi-table queries
- Foreign key constraints

**Coverage Goal**: 95%

---

### 35. core/cache.py (Current: 55%)

**Unit Tests (No Mocks):**
- L1 (in-memory) cache operations
- LRU eviction
- TTL expiration
- Cache key generation

**Unit Tests (With Mocks):**
- L2 (disk) cache operations (mock file I/O)
- Compression (mock compression library)

**Coverage Goal**: 95%

---

### 36. core/logging.py (Current: 61%)

**Unit Tests (No Mocks):**
- Logger instantiation
- Log level filtering
- Structured JSON formatting
- Performance logger metrics

**Unit Tests (With Mocks):**
- File rotation (mock file operations)
- Log backup (mock file operations)

**Coverage Goal**: 95%

---

### 37. core/ollama.py (Current: 0% - UNTESTED)

**Unit Tests (With Mocks):**
- **ALL tests must mock HTTP/LLM calls**
- Request payload construction
- Success response handling
- Failure response handling
- Retry/backoff behavior
- Timeout handling

**Coverage Goal**: 95%
**Priority**: HIGH (must fully mock)

---

### 38. core/ollama_validator.py (Current: 0% - UNTESTED)

**Unit Tests (With Mocks):**
- **ALL tests must mock Ollama client**
- Validation logic
- Response parsing
- Error handling

**Coverage Goal**: 95%
**Priority**: HIGH (must fully mock)

---

### 39. core/io_win.py (Current: 16%)

**Unit Tests (With Mocks):**
- Windows-specific I/O operations (mock Windows APIs)
- Path handling
- File permissions

**Coverage Goal**: 90%

---

### 40. api/dashboard.py (Current: 26%)

**Unit Tests (With Mocks):**
- Route handlers (use FastAPI TestClient)
- Template rendering (mock Jinja2)
- Data aggregation (mock database)

**Coverage Goal**: 90%

---

### 41. api/server_extensions.py (Current: 0% - UNTESTED)

**Unit Tests (With Mocks):**
- Extension loading
- Middleware registration
- Configuration

**Coverage Goal**: 90%

---

## Summary

### Tier A: 33 modules → 100% each
### Tier B: 8 modules → 90-95% each

### Critical Priorities (0-30% coverage):
1. **agents/enhancement_agent.py** (21%)
2. **core/ingestion.py** (0%)
3. **core/prompt_loader.py** (0%)
4. **core/ollama.py** (0%)
5. **core/ollama_validator.py** (0%)
6. **api/export_endpoints.py** (0%)
7. **api/services/status_recalculator.py** (0%)
8. **api/services/live_bus.py** (0%)
9. **api/server_extensions.py** (0%)
10. **core/rule_manager.py** (25%)

---

## Next Steps (P3-P8)

**P3**: Refactor test layout
**P4**: Execute Tier A coverage plan
**P5**: Execute Tier B coverage plan
**P6**: Tier C best-effort tests
**P7**: Stabilization
**P8**: Final validation

---
**Report Generated**: 2025-11-19
**Phase**: P2 - Detailed Coverage Plan
**Status**: COMPLETE
