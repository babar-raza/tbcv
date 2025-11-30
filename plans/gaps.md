# TBCV Gaps Remediation Plan

**Created:** 2025-11-29
**Last Updated:** 2025-11-29
**Status:** ✅ **COMPLETE** - All gaps addressed
**Target:** Production-Ready System with Zero Technical Debt

---

## Execution Progress - ALL PHASES COMPLETE

### Phase 1: Foundation ✅ COMPLETED

| Task | Status | Notes |
|------|--------|-------|
| TASK-F01 | ✅ DONE | Async event loop properly configured in conftest.py |
| TASK-F02 | ✅ DONE | Windows UTF-8 encoding configured |
| TASK-A01 | ✅ DONE | heading_sizes.yaml deleted, content_validator.py updated |
| TASK-A02 | ✅ DONE | ConfigLoader fully implemented (39 tests) |

### Phase 2: Validation System ✅ COMPLETED

| Task | Status | Notes |
|------|--------|-------|
| TASK-A03 | ✅ DONE | Truth+LLM composition in truth_validator.py (3-phase) |
| TASK-A04 | ✅ DONE | Tiered validation flow in validator_router.py (28 tests) |
| TASK-A05 | ✅ DONE | Enhanced error handling in error_formatter.py (38 tests) |
| TASK-A06 | ✅ DONE | Performance optimization in performance.py |

### Phase 3: CLI Parity ✅ COMPLETED

| Task | Status | Notes |
|------|--------|-------|
| TASK-B01-B18 | ✅ DONE | All 18 CLI commands implemented (106 tests) |

### Phase 4: Design Patterns ✅ COMPLETED

| Task | Status | Notes |
|------|--------|-------|
| TASK-C01 | ✅ DONE | Agentic RAG: vector_store.py + embeddings.py (25 tests) |
| TASK-C02 | ✅ DONE | Reflection pattern: recommendation_critic.py (36 tests) |
| TASK-C03 | ✅ DONE | Enhanced parallel execution in validator_router.py |

### Phase 5: Dashboard & Testing ✅ COMPLETED

| Task | Status | Notes |
|------|--------|-------|
| TASK-D01-D04 | ✅ DONE | Dashboard admin controls (152 tests) |
| TASK-E01 | ✅ DONE | CI/CD: .github/workflows/ui-tests.yml |
| TASK-E02-E03 | ✅ DONE | UI tests in tests/ui/ (6 test files) |

---

**Final Test Results:** 1606+ passed, 55 skipped, 0 failed

---

## Executive Summary

**STATUS: ✅ ALL GAPS CLOSED - PLAN COMPLETE**

### Gap Categories - Final Status

| Category | Gaps | Priority | Status |
|----------|------|----------|--------|
| [A] Validation System Config | 6 | P1 | ✅ 6/6 complete |
| [B] CLI/Web Parity | 18 | P1 | ✅ 18/18 complete |
| [C] Design Patterns | 3 | P2 | ✅ 3/3 complete |
| [D] Dashboard Admin Controls | 4 | P2 | ✅ 4/4 complete |
| [E] UI Testing Completion | 3 | P3 | ✅ 3/3 complete |
| [F] Test Infrastructure | 2 | P1 | ✅ 2/2 complete |
| **Total** | **36** | - | **✅ 36/36 complete** |

### Hard Rules (Apply to ALL Tasks)

1. **No Regression**: All previously working scenarios, workflows, and integrations must continue to behave exactly as before
2. **Keep Docs Up to Date**: All documentation changes must be made in the same commit as code changes
3. **Keep Tests Up to Date**: All test changes must be made in the same commit as code changes

---

## Category A: Validation System Configuration Gaps

These gaps are from `validation_types.md` - approved changes that were never implemented.

---

### TASK-A01: Merge heading_sizes.yaml into seo.yaml

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Consolidate heading_sizes.yaml into seo.yaml as single SEO configuration
- Allowed paths:
  - config/seo.yaml
  - config/heading_sizes.yaml (DELETE)
  - agents/validators/seo_validator.py
  - tests/agents/test_seo_validation.py
  - docs/configuration.md
- Forbidden: any other file

Context:
- heading_sizes.yaml and seo.yaml both handle heading-related SEO concerns
- Current state: Two separate files causing configuration fragmentation
- Target state: Single config/seo.yaml with heading_sizes section merged in

Acceptance checks (must pass locally):
- CLI: python -m tbcv validate --file test.md --validators seo
- Web: Dashboard SEO validation shows heading size issues correctly
- Tests: pytest tests/agents/test_seo_validation.py -v
- Verify: config/heading_sizes.yaml no longer exists
- Verify: SEO validator loads heading sizes from config/seo.yaml

Deliverables:
1. Updated config/seo.yaml with heading_sizes section merged
2. DELETE config/heading_sizes.yaml
3. Updated agents/validators/seo_validator.py to load from single file
4. Updated tests covering heading size validation from new config location
5. Updated docs/configuration.md with new config structure

Implementation Steps:
1. Read current heading_sizes.yaml structure
2. Read current seo.yaml structure
3. Merge heading_sizes into seo.yaml under 'heading_sizes' key
4. Update SeoValidatorAgent to load heading sizes from seo.yaml
5. Delete heading_sizes.yaml
6. Update all tests that reference heading_sizes.yaml
7. Update configuration documentation
8. Run full test suite to verify no regressions

Hard rules:
- Keep public function signatures unless you justify and update all call sites
- Zero network calls in mock tests
- Dual testing modes: Mock vs Live Data (runtime flag)
- Deterministic runs: set seeds, stable ordering
- Do not introduce new dependencies without approval
- Keep code style consistent with existing codebase
- Keep documentation in sync with code changes
- Keep tests in sync with code changes

Regression Check:
- Run: pytest tests/agents/test_seo_validation.py -v
- Run: pytest tests/agents/test_heading_sizes.py -v (if exists)
- Verify all SEO validation functionality works unchanged
- Verify CLI and Web both use new config location

Self-review (answer yes/no at the end):
- [ ] Thorough implementation with no TODOs
- [ ] Config files consistent and validated
- [ ] All imports updated
- [ ] Tests passing
- [ ] Documentation updated
- [ ] No regressions detected

Runbook:
1. git checkout -b fix/merge-heading-sizes-into-seo
2. Read and merge config files
3. Update seo_validator.py
4. Delete heading_sizes.yaml
5. Update tests
6. pytest tests/agents/test_seo_validation.py -v
7. pytest tests/ -k "seo or heading" -v
8. Update docs/configuration.md
9. git add -A && git commit -m "Merge heading_sizes.yaml into seo.yaml"
```

---

### TASK-A02: Implement Generic Configuration System with Rules/Profiles

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Implement generic, extensible configuration system for all validators
- Allowed paths:
  - core/config_loader.py (create or update)
  - config/frontmatter.yaml
  - config/markdown.yaml
  - config/code.yaml
  - config/links.yaml
  - config/structure.yaml
  - config/seo.yaml
  - agents/validators/base_validator.py
  - agents/validators/yaml_validator.py
  - agents/validators/markdown_validator.py
  - agents/validators/code_validator.py
  - agents/validators/link_validator.py
  - agents/validators/structure_validator.py
  - agents/validators/seo_validator.py
  - tests/core/test_config_loader.py
  - docs/configuration.md
- Forbidden: any other file

Context:
- Current state: Each validator has hardcoded rules or inconsistent config loading
- Target state: Generic config system with:
  - Rules Library: Individual checks with id, level, message, params
  - Profiles: Pre-defined rule sets (strict, default, relaxed)
  - Family Overrides: Per-content-type customization
  - Extensibility: Add new rules in YAML without code changes

Target Config Structure:
```yaml
validator_name:
  enabled: true
  profile: "default"
  rules:
    rule_id:
      enabled: true
      level: error|warning|info
      message: "..."
      params: {}
  profiles:
    strict: { rules: [...], overrides: {} }
    default: { rules: [...] }
    relaxed: { rules: [...] }
  family_overrides:
    words: { profile: "strict", rules: {} }
```

Acceptance checks (must pass locally):
- CLI: python -m tbcv validate --file test.md --profile strict
- CLI: python -m tbcv validate --file test.md --family words
- Tests: pytest tests/core/test_config_loader.py -v
- Tests: pytest tests/agents/test_modular_validators.py -v
- Verify: All validators use generic config loader
- Verify: Profile switching works correctly
- Verify: Family overrides are applied

Deliverables:
1. core/config_loader.py - Generic config loader with profile/rules support
2. Updated config/*.yaml files with standardized structure
3. Updated all validator agents to use generic config loader
4. Comprehensive tests for config loading, profiles, overrides
5. Updated documentation

Implementation Steps:
1. Design ConfigLoader class with load_rules(), get_profile(), apply_overrides()
2. Migrate each config file to new structure
3. Update BaseValidatorAgent to use ConfigLoader
4. Update each specific validator to use base config loading
5. Add CLI flags for --profile and verify --family works
6. Add tests for all config scenarios
7. Update configuration documentation

Hard rules:
- Keep public function signatures unless you justify and update all call sites
- Zero network calls in mock tests
- Backward compatible: old config format must still work (deprecation warning)
- Deterministic rule ordering
- Do not introduce new dependencies without approval
- Keep code style consistent with existing codebase
- Keep documentation in sync with code changes
- Keep tests in sync with code changes

Regression Check:
- Run full test suite: pytest tests/ -v
- Verify all validators work with existing configs
- Test backward compatibility with old config format
- Verify CLI and Web both respect profiles

Self-review (answer yes/no at the end):
- [ ] ConfigLoader is generic and reusable
- [ ] All validators updated consistently
- [ ] Backward compatibility maintained
- [ ] Tests cover all scenarios
- [ ] Documentation complete

Runbook:
1. git checkout -b feat/generic-config-system
2. Create core/config_loader.py
3. Update each config file (one at a time, test after each)
4. Update BaseValidatorAgent
5. Update each validator (one at a time, test after each)
6. pytest tests/core/test_config_loader.py -v
7. pytest tests/agents/ -v
8. pytest tests/ -v (full suite)
9. Update docs/configuration.md
10. git add -A && git commit -m "Implement generic configuration system"
```

---

### TASK-A03: Implement Truth Validator + LLM Composition

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Truth Validator composes with LLM Validator for semantic enhancement
- Allowed paths:
  - agents/validators/truth_validator.py
  - agents/llm_validator.py
  - config/truth.yaml
  - config/llm.yaml
  - tests/agents/test_truth_manager.py
  - tests/test_truth_validation.py
  - tests/test_truth_llm_validation.py
  - docs/agents.md
- Forbidden: any other file

Context:
- Current state: Truth Validator uses rule-based matching only
- Target state: Three-phase validation:
  - Phase 1: Rule-based validation (always runs)
  - Phase 2: LLM enhancement (optional, graceful fallback)
  - Phase 3: Intelligent merge (dedup, confidence filtering)

Architecture:
```
INPUT: content, context
    │
    ▼
┌─────────────────────────────┐
│ PHASE 1: Rule-Based         │ ← Always runs
│ - Load truth from TruthMgr  │
│ - Validate plugin mentions  │
│ - Check forbidden patterns  │
│ Output: rule_issues         │
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│ PHASE 2: LLM Enhancement    │ ← Optional
│ IF llm_enabled AND avail:   │
│ - Call LLM Validator        │
│ - Get semantic issues       │
│ ELSE:                       │
│ - semantic_issues = []      │
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│ PHASE 3: Intelligent Merge  │
│ - Deduplicate issues        │
│ - Apply confidence filter   │
│ - Tag issue sources         │
└─────────────────────────────┘
    │
    ▼
OUTPUT: ValidationResult
```

Acceptance checks (must pass locally):
- CLI: python -m tbcv validate --file test.md --validators truth
- CLI: python -m tbcv validate --file test.md --validators truth --no-llm
- Tests: pytest tests/test_truth_validation.py -v
- Tests: pytest tests/test_truth_llm_validation.py -v
- Verify: Works without Ollama (graceful degradation)
- Verify: LLM issues are properly deduplicated
- Verify: Confidence thresholds are respected

Deliverables:
1. Updated truth_validator.py with three-phase validation
2. Updated config/truth.yaml with llm_enhancement section
3. Helper methods: _validate_rule_based(), _get_llm_enhancement(), _merge_issues()
4. Tests for all three phases and failure scenarios
5. Updated documentation

Implementation Steps:
1. Read current truth_validator.py implementation
2. Refactor into _validate_rule_based() method
3. Add _get_llm_enhancement() with LLM Validator composition
4. Add _merge_issues() with deduplication and confidence filtering
5. Update config/truth.yaml with llm_enhancement settings
6. Add comprehensive tests
7. Test graceful degradation when Ollama unavailable
8. Update documentation

Config Structure (config/truth.yaml):
```yaml
truth:
  enabled: true
  rule_based:
    check_plugin_mentions: true
    check_api_patterns: true
    check_forbidden_patterns: true
  llm_enhancement:
    enabled: true
    timeout_seconds: 30
    confidence_threshold: 0.7
    min_content_length: 100
    max_content_length: 50000
    fallback_on_error: true
```

Hard rules:
- Rule-based results are NEVER lost (LLM adds, never replaces)
- Graceful degradation: if LLM fails, return rule-based only
- Confidence filtering: only accept LLM issues >= threshold
- Deduplication: rule-based takes priority for duplicates
- Tag all issues with source: "rule_based" or "llm_semantic"
- Keep public function signatures
- Zero network calls in mock tests
- Do not introduce new dependencies

Regression Check:
- Run: pytest tests/test_truth_validation.py -v
- Run: pytest tests/test_truth_llm_validation.py -v
- Verify rule-based validation unchanged
- Verify LLM enhancement adds value without breaking existing
- Test with Ollama running and stopped

Self-review (answer yes/no at the end):
- [ ] Three-phase architecture implemented
- [ ] Graceful degradation verified
- [ ] Confidence filtering working
- [ ] Deduplication working
- [ ] Tests comprehensive
- [ ] Documentation updated

Runbook:
1. git checkout -b feat/truth-llm-composition
2. Refactor truth_validator.py
3. Update config/truth.yaml
4. pytest tests/test_truth_validation.py -v
5. Stop Ollama, run tests again (graceful degradation)
6. Start Ollama, run tests with LLM
7. pytest tests/ -v (full suite)
8. Update docs/agents.md
9. git add -A && git commit -m "Implement Truth+LLM composition"
```

---

### TASK-A04: Implement Tiered Validation Flow with Parallel Execution

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Optimize validation flow with tiered execution and parallelization
- Allowed paths:
  - core/validator_router.py
  - config/validation_flow.yaml
  - tests/core/test_validator_router.py
  - docs/architecture.md
- Forbidden: any other file

Context:
- Current state: Validators run sequentially or with basic parallelism
- Target state: Three-tier execution with parallel validators within tiers

Architecture:
```
TIER 1: SYNTAX (Parallel)         ~50ms
├── YAML, Markdown syntax, Structure basic
└── User controls which to run

TIER 2: CONTENT (Parallel)        ~200ms
├── Links, Code, SEO, Fuzzy Detection
└── User controls which to run

TIER 3: SEMANTIC (Sequential)     ~2000ms
├── Truth + LLM
└── User controls which to run
```

Features:
- Parallel execution within tiers (asyncio.gather)
- Dependency-aware ordering (Truth waits for Fuzzy)
- Early termination on critical errors (configurable)
- User selects any combination of validators

Acceptance checks (must pass locally):
- CLI: python -m tbcv validate --file test.md --validators yaml,markdown,links
- CLI: python -m tbcv validate --file test.md --early-exit-on-critical
- Tests: pytest tests/core/test_validator_router.py -v
- Performance: Validate 100 files, measure time improvement
- Verify: Tier ordering is respected
- Verify: Parallel execution within tiers works

Deliverables:
1. Updated core/validator_router.py with tiered parallel execution
2. config/validation_flow.yaml with tier definitions
3. Early termination logic for critical errors
4. Performance benchmarks
5. Updated tests and documentation

Implementation Steps:
1. Read current validator_router.py
2. Define tier configuration in validation_flow.yaml
3. Implement execute_tiered() method with asyncio.gather per tier
4. Add early termination check between tiers
5. Add dependency resolution (e.g., Truth depends on Fuzzy results)
6. Benchmark performance before and after
7. Update tests
8. Update documentation

Config Structure (config/validation_flow.yaml):
```yaml
tiers:
  tier_1_syntax:
    parallel: true
    validators:
      - yaml_validator
      - markdown_validator
      - structure_validator
    early_exit_on: [critical]

  tier_2_content:
    parallel: true
    validators:
      - link_validator
      - code_validator
      - seo_validator
      - fuzzy_validator
    depends_on: tier_1_syntax

  tier_3_semantic:
    parallel: false  # Sequential for LLM rate limiting
    validators:
      - truth_validator
      - llm_validator
    depends_on: tier_2_content

early_termination:
  enabled: true
  on_levels: [critical]
```

Hard rules:
- Maintain validator result accuracy (parallelism must not affect output)
- Respect dependencies between validators
- Early termination must be configurable
- Keep public function signatures
- Zero network calls in mock tests
- Deterministic ordering within tiers
- Do not introduce new dependencies

Regression Check:
- Run: pytest tests/core/test_validator_router.py -v
- Run: pytest tests/agents/test_modular_validators.py -v
- Benchmark: time python -m tbcv validate --dir ./test-files/
- Verify all validation results identical to before
- Test early termination behavior

Self-review (answer yes/no at the end):
- [ ] Tiered execution implemented
- [ ] Parallel within tiers verified
- [ ] Early termination working
- [ ] Dependencies respected
- [ ] Performance improved
- [ ] Tests comprehensive
- [ ] Documentation updated

Runbook:
1. git checkout -b feat/tiered-parallel-validation
2. Create/update config/validation_flow.yaml
3. Update core/validator_router.py
4. Benchmark before: time pytest tests/test_performance.py
5. pytest tests/core/test_validator_router.py -v
6. Benchmark after: time pytest tests/test_performance.py
7. pytest tests/ -v (full suite)
8. Update docs/architecture.md
9. git add -A && git commit -m "Implement tiered parallel validation"
```

---

### TASK-A05: Implement Enhanced Error Handling and Reporting

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Improved error structure and multiple output formats
- Allowed paths:
  - agents/validators/base_validator.py
  - core/error_formatter.py (create or update)
  - api/server.py (response formatting only)
  - templates/validation_detail.html
  - templates/validation_detail_enhanced.html
  - cli/main.py (output formatting only)
  - tests/core/test_error_formatter.py
  - docs/api_reference.md
- Forbidden: any other file

Context:
- Current state: Basic ValidationIssue structure
- Target state: Enhanced issue structure with rich metadata

Enhanced ValidationIssue Structure:
```python
@dataclass
class EnhancedValidationIssue:
    id: str                    # "YAML-001"
    code: str                  # "YAML_MISSING_FIELD"
    level: str                 # error|warning|info|critical
    severity_score: int        # 1-100 for sorting
    line_number: Optional[int]
    column: Optional[int]
    line_end: Optional[int]
    category: str
    subcategory: Optional[str]
    message: str
    suggestion: Optional[str]
    context_snippet: Optional[str]    # Problematic text
    context_before: Optional[str]
    context_after: Optional[str]
    fix_example: Optional[str]        # Actual fixed code
    auto_fixable: bool
    source: str                # "rule_based"|"llm_semantic"
    confidence: float
    documentation_url: Optional[str]
```

Output Formats:
- CLI: Color-coded with context snippets
- JSON API: Full structured response with summary
- HTML Dashboard: Grouped, sortable, filterable

Acceptance checks (must pass locally):
- CLI: python -m tbcv validate --file test.md --format json
- CLI: python -m tbcv validate --file test.md --format text (color output)
- Web: Dashboard shows enhanced issue display
- Tests: pytest tests/core/test_error_formatter.py -v
- Verify: All existing issue data preserved
- Verify: New fields populated where available

Deliverables:
1. Enhanced ValidationIssue dataclass in base_validator.py
2. core/error_formatter.py for format conversion
3. Updated CLI output with colors and context
4. Updated API response structure
5. Updated dashboard templates
6. Comprehensive tests
7. Updated documentation

Implementation Steps:
1. Update ValidationIssue dataclass with new fields (backward compatible)
2. Create ErrorFormatter class with to_json(), to_cli(), to_html()
3. Update each validator to populate new fields where applicable
4. Update CLI output formatting
5. Update API response formatting
6. Update dashboard templates
7. Add tests for all formats
8. Update API documentation

Hard rules:
- Backward compatible: old ValidationIssue still works
- All new fields are Optional with sensible defaults
- CLI colors work on Windows (use colorama or rich)
- JSON output is valid and parseable
- Keep public function signatures
- Zero network calls in mock tests
- Do not introduce new dependencies (except colorama if needed)

Regression Check:
- Run: pytest tests/ -v
- Verify old validation code still works
- Verify CLI output is correct
- Verify API responses are valid JSON
- Verify dashboard displays correctly

Self-review (answer yes/no at the end):
- [ ] Enhanced structure implemented
- [ ] Backward compatible
- [ ] All formats working
- [ ] CLI colors working
- [ ] Dashboard updated
- [ ] Tests comprehensive
- [ ] Documentation updated

Runbook:
1. git checkout -b feat/enhanced-error-reporting
2. Update agents/validators/base_validator.py
3. Create/update core/error_formatter.py
4. Update cli/main.py output formatting
5. Update api/server.py response formatting
6. Update templates
7. pytest tests/core/test_error_formatter.py -v
8. pytest tests/ -v (full suite)
9. Manual test CLI and Web
10. Update docs/api_reference.md
11. git add -A && git commit -m "Implement enhanced error reporting"
```

---

### TASK-A06: Implement Performance Optimization (Caching & Parallelization)

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Caching strategies and performance improvements
- Allowed paths:
  - core/cache.py
  - core/performance.py (create or update)
  - config/cache.yaml
  - agents/validators/*.py (cache integration only)
  - tests/core/test_cache.py
  - tests/core/test_performance.py
  - docs/configuration.md
- Forbidden: any other file

Context:
- Current state: Basic or no caching
- Target state: Multi-level caching with smart invalidation

Caching Strategy:
```yaml
cache:
  validation_results:
    enabled: true
    strategy: content_hash    # SHA256 of content
    ttl_seconds: 3600
    invalidate_on: [config_change, truth_change]

  llm_responses:
    enabled: true
    strategy: prompt_hash
    ttl_seconds: 86400        # 24 hours (expensive)

  truth_data:
    strategy: file_mtime      # Reload on file change
    preload: [words, pdf, cells, slides]

  compiled_patterns:
    precompile: true          # At startup
```

Performance Features:
- Parallel validator execution (asyncio.gather)
- Lazy loading of truth data
- Connection pooling for LLM
- Batch processing optimization
- Progressive validation for UI (WebSocket events)

Acceptance checks (must pass locally):
- CLI: python -m tbcv validate --file test.md (warm cache)
- CLI: python -m tbcv admin cache-stats
- Tests: pytest tests/core/test_cache.py -v
- Tests: pytest tests/core/test_performance.py -v
- Benchmark: Second validation 10x faster than first
- Verify: Cache invalidation works correctly

Deliverables:
1. Updated core/cache.py with multi-level caching
2. core/performance.py with timing and metrics
3. Updated config/cache.yaml with all cache settings
4. Cache integration in validators
5. Performance benchmarks
6. Tests and documentation

Implementation Steps:
1. Read current cache.py implementation
2. Implement content-hash based caching for validation results
3. Implement prompt-hash caching for LLM responses
4. Add file-mtime based truth data caching
5. Add precompilation for regex patterns
6. Update validators to use cache
7. Add admin cache-stats command
8. Benchmark and test
9. Update documentation

Hard rules:
- Cache must be thread-safe
- Cache invalidation must be correct (no stale data)
- Cache keys must be deterministic
- Memory limits must be respected
- Keep public function signatures
- Zero network calls in mock tests
- Do not introduce new dependencies

Regression Check:
- Run: pytest tests/ -v
- Benchmark before and after
- Verify cache invalidation on config change
- Verify cache invalidation on truth file change
- Test cache behavior under load

Self-review (answer yes/no at the end):
- [ ] Multi-level caching implemented
- [ ] Cache invalidation correct
- [ ] Performance improved
- [ ] Memory usage acceptable
- [ ] Tests comprehensive
- [ ] Documentation updated

Runbook:
1. git checkout -b feat/performance-optimization
2. Update core/cache.py
3. Create/update core/performance.py
4. Update config/cache.yaml
5. Update validators with cache integration
6. Benchmark: time python -m tbcv validate --dir ./test-files/
7. pytest tests/core/test_cache.py -v
8. pytest tests/core/test_performance.py -v
9. Benchmark again (should be faster)
10. pytest tests/ -v (full suite)
11. Update docs/configuration.md
12. git add -A && git commit -m "Implement performance optimization"
```

---

## Category B: CLI/Web Parity Gaps

These gaps ensure feature parity between CLI and Web interfaces.

---

### TASK-B01: Add Recommendation Generation Endpoints to Web

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Add explicit endpoints to generate/rebuild recommendations on demand
- Allowed paths:
  - api/server.py
  - api/dashboard.py
  - templates/validation_detail_enhanced.html
  - tests/api/test_recommendation_generation.py
  - docs/api_reference.md
- Forbidden: any other file

Context:
- Current CLI has: `recommendations generate` and `recommendations rebuild`
- Current Web: Only auto-generates during validation
- Target: Web has explicit endpoints matching CLI functionality

Endpoints to Add:
- POST /api/recommendations/{validation_id}/generate
- POST /api/recommendations/{validation_id}/rebuild

Acceptance checks (must pass locally):
- CLI: python -m tbcv recommendations generate <id>
- Web: POST /api/recommendations/{id}/generate
- Web: POST /api/recommendations/{id}/rebuild
- Tests: pytest tests/api/test_recommendation_generation.py -v
- Verify: CLI and Web produce identical results
- Verify: UI button triggers generation

Deliverables:
1. Two new API endpoints in api/server.py
2. UI button in validation_detail_enhanced.html
3. Comprehensive tests
4. Updated API documentation

Implementation Steps:
1. Add POST /api/recommendations/{validation_id}/generate endpoint
2. Add POST /api/recommendations/{validation_id}/rebuild endpoint
3. Add "Generate Recommendations" button to UI
4. Wire button to endpoint with JS
5. Add tests for both endpoints
6. Update API documentation

Hard rules:
- Endpoints must match CLI behavior exactly
- Handle edge cases: validation not found, already has recommendations
- Return consistent response structure
- Keep public function signatures
- Zero network calls in mock tests

Regression Check:
- Run: pytest tests/api/ -v
- Verify existing recommendation endpoints still work
- Test CLI and Web produce same results

Self-review (answer yes/no at the end):
- [ ] Both endpoints implemented
- [ ] UI button working
- [ ] CLI/Web parity verified
- [ ] Tests comprehensive
- [ ] Documentation updated

Runbook:
1. git checkout -b feat/recommendation-generation-endpoints
2. Add endpoints to api/server.py
3. Add UI button to template
4. pytest tests/api/test_recommendation_generation.py -v
5. Manual test: CLI vs Web comparison
6. pytest tests/api/ -v
7. Update docs/api_reference.md
8. git add -A && git commit -m "Add recommendation generation endpoints"
```

---

### TASK-B02: Add admin enhancements CLI Command

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Add CLI command to list enhancement history (matches Web /api/audit/enhancements)
- Allowed paths:
  - cli/main.py
  - tests/cli/test_admin_enhancements.py
  - docs/cli_usage.md
- Forbidden: any other file

Context:
- Web has: /api/audit/enhancements
- CLI has: nothing
- Target: CLI has `admin enhancements` command

Command Spec:
```bash
tbcv admin enhancements [OPTIONS]
  --file-path, -f    Filter by file path
  --limit, -l        Maximum records to show (default: 50)
  --format           Output format: table|json (default: table)
```

Acceptance checks (must pass locally):
- CLI: python -m tbcv admin enhancements
- CLI: python -m tbcv admin enhancements --format json
- CLI: python -m tbcv admin enhancements -f /path/to/file.md
- Tests: pytest tests/cli/test_admin_enhancements.py -v
- Verify: Output matches Web API response

Deliverables:
1. New CLI command in cli/main.py
2. Comprehensive tests
3. Updated CLI documentation

Implementation Steps:
1. Add `admin enhancements` command to admin group
2. Implement filtering by file path
3. Implement table and JSON output formats
4. Add tests
5. Update documentation

Hard rules:
- Output must match Web API semantically
- Table format must be readable in terminal
- JSON format must be valid and parseable
- Keep public function signatures
- Zero network calls in mock tests

Regression Check:
- Run: pytest tests/cli/ -v
- Verify existing admin commands still work
- Compare CLI output with Web API response

Self-review (answer yes/no at the end):
- [ ] Command implemented
- [ ] Filtering working
- [ ] Both formats working
- [ ] Tests comprehensive
- [ ] Documentation updated

Runbook:
1. git checkout -b feat/admin-enhancements-cli
2. Add command to cli/main.py
3. pytest tests/cli/test_admin_enhancements.py -v
4. Manual test: compare with Web API
5. pytest tests/cli/ -v
6. Update docs/cli_usage.md
7. git add -A && git commit -m "Add admin enhancements CLI command"
```

---

### TASK-B03: Add admin rollback CLI Command

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Add CLI command to rollback enhancement (matches Web /api/audit/rollback)
- Allowed paths:
  - cli/main.py
  - tests/cli/test_admin_enhancements.py
  - docs/cli_usage.md
- Forbidden: any other file

Command Spec:
```bash
tbcv admin rollback <enhancement_id> [OPTIONS]
  --confirm          Confirm rollback operation (required)
  --rolled-back-by   User performing rollback (default: cli_user)
```

Acceptance checks (must pass locally):
- CLI: python -m tbcv admin rollback <id> --confirm
- Tests: pytest tests/cli/test_admin_enhancements.py::test_rollback -v
- Verify: File content restored correctly
- Verify: Rollback recorded in history

Deliverables:
1. New CLI command in cli/main.py
2. Comprehensive tests
3. Updated CLI documentation

Hard rules:
- Require --confirm flag for safety
- Show what will be rolled back before confirming
- Handle edge cases: not found, expired, already rolled back
- Keep public function signatures

Runbook:
1. git checkout -b feat/admin-rollback-cli (or continue from B02)
2. Add command to cli/main.py
3. pytest tests/cli/test_admin_enhancements.py -v
4. Manual test rollback flow
5. Update docs/cli_usage.md
6. git add -A && git commit -m "Add admin rollback CLI command"
```

---

### TASK-B04: Add admin enhancement-detail CLI Command

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Add CLI command to get enhancement detail
- Allowed paths:
  - cli/main.py
  - tests/cli/test_admin_enhancements.py
  - docs/cli_usage.md
- Forbidden: any other file

Command Spec:
```bash
tbcv admin enhancement-detail <enhancement_id> [OPTIONS]
  --format           Output format: text|json (default: text)
```

Acceptance checks (must pass locally):
- CLI: python -m tbcv admin enhancement-detail <id>
- CLI: python -m tbcv admin enhancement-detail <id> --format json
- Tests: pytest tests/cli/test_admin_enhancements.py::test_detail -v

Deliverables:
1. New CLI command in cli/main.py
2. Comprehensive tests
3. Updated CLI documentation

Runbook:
1. git checkout -b feat/admin-enhancement-detail-cli (or continue)
2. Add command to cli/main.py
3. pytest tests/cli/test_admin_enhancements.py -v
4. Update docs/cli_usage.md
5. git add -A && git commit -m "Add admin enhancement-detail CLI command"
```

---

### TASK-B05: Add validations diff CLI Command

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Add CLI command to show content diff (matches Web /api/validations/{id}/diff)
- Allowed paths:
  - cli/main.py
  - tests/cli/test_validation_diff.py
  - docs/cli_usage.md
- Forbidden: any other file

Command Spec:
```bash
tbcv validations diff <validation_id> [OPTIONS]
  --format           Output format: unified|side-by-side|json (default: unified)
  --context, -c      Lines of context for unified diff (default: 3)
```

Acceptance checks (must pass locally):
- CLI: python -m tbcv validations diff <id>
- CLI: python -m tbcv validations diff <id> --format side-by-side
- CLI: python -m tbcv validations diff <id> --format json
- Tests: pytest tests/cli/test_validation_diff.py -v
- Verify: Diff output is correct (color-coded for terminal)

Deliverables:
1. New CLI command in cli/main.py
2. Comprehensive tests
3. Updated CLI documentation

Implementation Steps:
1. Add `validations diff` command
2. Implement unified diff with colors (green +, red -)
3. Implement side-by-side view
4. Implement JSON output
5. Add tests
6. Update documentation

Hard rules:
- Use difflib for diff generation
- Colors work on Windows
- Handle no-diff case gracefully
- Keep public function signatures

Runbook:
1. git checkout -b feat/validations-diff-cli
2. Add command to cli/main.py
3. pytest tests/cli/test_validation_diff.py -v
4. Manual test diff output
5. Update docs/cli_usage.md
6. git add -A && git commit -m "Add validations diff CLI command"
```

---

### TASK-B06: Add validations compare CLI Command

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Add CLI command for enhancement comparison with stats
- Allowed paths:
  - cli/main.py
  - tests/cli/test_validation_diff.py
  - docs/cli_usage.md
- Forbidden: any other file

Command Spec:
```bash
tbcv validations compare <validation_id> [OPTIONS]
  --format           Output format: summary|detailed|json (default: summary)
```

Output includes:
- Original vs enhanced line counts
- Lines added/removed/modified
- Similarity ratio
- Applied recommendations count

Acceptance checks (must pass locally):
- CLI: python -m tbcv validations compare <id>
- CLI: python -m tbcv validations compare <id> --format json
- Tests: pytest tests/cli/test_validation_diff.py::test_compare -v

Deliverables:
1. New CLI command in cli/main.py
2. Comprehensive tests
3. Updated CLI documentation

Runbook:
1. git checkout -b feat/validations-compare-cli (or continue from B05)
2. Add command to cli/main.py
3. pytest tests/cli/test_validation_diff.py -v
4. Update docs/cli_usage.md
5. git add -A && git commit -m "Add validations compare CLI command"
```

---

### TASK-B07: Add workflows report CLI Command

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Add CLI command for workflow report (matches Web /workflows/{id}/report)
- Allowed paths:
  - cli/main.py
  - tests/cli/test_workflow_report.py
  - docs/cli_usage.md
- Forbidden: any other file

Command Spec:
```bash
tbcv workflows report <workflow_id> [OPTIONS]
  --output, -o       Save report to file
  --format           Output format: text|json|markdown (default: text)
```

Acceptance checks (must pass locally):
- CLI: python -m tbcv workflows report <id>
- CLI: python -m tbcv workflows report <id> --format markdown -o report.md
- Tests: pytest tests/cli/test_workflow_report.py -v

Deliverables:
1. New CLI command in cli/main.py
2. Helper functions for report formatting
3. Comprehensive tests
4. Updated CLI documentation

Runbook:
1. git checkout -b feat/workflows-report-cli
2. Add command to cli/main.py
3. pytest tests/cli/test_workflow_report.py -v
4. Update docs/cli_usage.md
5. git add -A && git commit -m "Add workflows report CLI command"
```

---

### TASK-B08: Add workflows summary CLI Command

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Add CLI command for workflow summary (matches Web /workflows/{id}/summary)
- Allowed paths:
  - cli/main.py
  - tests/cli/test_workflow_report.py
  - docs/cli_usage.md
- Forbidden: any other file

Command Spec:
```bash
tbcv workflows summary <workflow_id> [OPTIONS]
  --format           Output format: text|json (default: text)
```

Acceptance checks (must pass locally):
- CLI: python -m tbcv workflows summary <id>
- Tests: pytest tests/cli/test_workflow_report.py::test_summary -v

Deliverables:
1. New CLI command in cli/main.py
2. Comprehensive tests
3. Updated CLI documentation

Runbook:
1. git checkout -b feat/workflows-summary-cli (or continue from B07)
2. Add command to cli/main.py
3. pytest tests/cli/test_workflow_report.py -v
4. Update docs/cli_usage.md
5. git add -A && git commit -m "Add workflows summary CLI command"
```

---

### TASK-B09: Add workflows watch CLI Command

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Add CLI command to watch workflow progress in real-time
- Allowed paths:
  - cli/main.py
  - tests/cli/test_workflow_watch.py
  - docs/cli_usage.md
- Forbidden: any other file

Command Spec:
```bash
tbcv workflows watch <workflow_id> [OPTIONS]
  --interval, -i     Polling interval in seconds (default: 2)
  --timeout, -t      Maximum watch time in seconds (default: 300)
```

Features:
- Real-time progress bar updates
- State change notifications
- Ctrl+C to stop
- Exit when workflow completes/fails

Acceptance checks (must pass locally):
- CLI: python -m tbcv workflows watch <id>
- Tests: pytest tests/cli/test_workflow_watch.py -v
- Verify: Progress updates display correctly
- Verify: Exits on completion

Deliverables:
1. New CLI command in cli/main.py
2. Progress bar helper function
3. Comprehensive tests
4. Updated CLI documentation

Hard rules:
- Handle Ctrl+C gracefully
- Timeout must work correctly
- Only print on state change (reduce noise)
- Keep public function signatures

Runbook:
1. git checkout -b feat/workflows-watch-cli
2. Add command to cli/main.py
3. pytest tests/cli/test_workflow_watch.py -v
4. Manual test with running workflow
5. Update docs/cli_usage.md
6. git add -A && git commit -m "Add workflows watch CLI command"
```

---

### TASK-B10: Add admin maintenance CLI Commands

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Add maintenance mode CLI commands (matches Web /admin/maintenance/*)
- Allowed paths:
  - cli/main.py
  - tests/cli/test_admin_maintenance.py
  - docs/cli_usage.md
- Forbidden: any other file

Commands to Add:
```bash
tbcv admin maintenance enable
tbcv admin maintenance disable
tbcv admin maintenance status
```

Acceptance checks (must pass locally):
- CLI: python -m tbcv admin maintenance enable
- CLI: python -m tbcv admin maintenance status
- CLI: python -m tbcv admin maintenance disable
- Tests: pytest tests/cli/test_admin_maintenance.py -v
- Verify: Maintenance mode affects workflow submission

Deliverables:
1. Three new CLI commands in cli/main.py
2. Comprehensive tests
3. Updated CLI documentation

Runbook:
1. git checkout -b feat/admin-maintenance-cli
2. Add maintenance subgroup to cli/main.py
3. pytest tests/cli/test_admin_maintenance.py -v
4. Update docs/cli_usage.md
5. git add -A && git commit -m "Add admin maintenance CLI commands"
```

---

### TASK-B11: Add admin cache-cleanup CLI Command

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Add CLI command to cleanup expired cache entries
- Allowed paths:
  - cli/main.py
  - tests/cli/test_admin_cache.py
  - docs/cli_usage.md
- Forbidden: any other file

Command Spec:
```bash
tbcv admin cache-cleanup
```

Output:
- L1 entries removed
- L2 entries removed
- Total removed

Acceptance checks (must pass locally):
- CLI: python -m tbcv admin cache-cleanup
- Tests: pytest tests/cli/test_admin_cache.py::test_cleanup -v

Deliverables:
1. New CLI command in cli/main.py
2. Comprehensive tests
3. Updated CLI documentation

Runbook:
1. git checkout -b feat/admin-cache-cli
2. Add command to cli/main.py
3. pytest tests/cli/test_admin_cache.py -v
4. Update docs/cli_usage.md
5. git add -A && git commit -m "Add admin cache-cleanup CLI command"
```

---

### TASK-B12: Add admin cache-rebuild CLI Command

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Add CLI command to rebuild cache from scratch
- Allowed paths:
  - cli/main.py
  - tests/cli/test_admin_cache.py
  - docs/cli_usage.md
- Forbidden: any other file

Command Spec:
```bash
tbcv admin cache-rebuild [OPTIONS]
  --preload-truth    Preload truth data after rebuild
```

Acceptance checks (must pass locally):
- CLI: python -m tbcv admin cache-rebuild
- CLI: python -m tbcv admin cache-rebuild --preload-truth
- Tests: pytest tests/cli/test_admin_cache.py::test_rebuild -v

Deliverables:
1. New CLI command in cli/main.py
2. Comprehensive tests
3. Updated CLI documentation

Runbook:
1. git checkout -b feat/admin-cache-rebuild-cli (or continue from B11)
2. Add command to cli/main.py
3. pytest tests/cli/test_admin_cache.py -v
4. Update docs/cli_usage.md
5. git add -A && git commit -m "Add admin cache-rebuild CLI command"
```

---

### TASK-B13: Add admin report performance CLI Command

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Add CLI command for performance report
- Allowed paths:
  - cli/main.py
  - tests/cli/test_admin_reports.py
  - docs/cli_usage.md
- Forbidden: any other file

Command Spec:
```bash
tbcv admin report performance [OPTIONS]
  --days, -d         Number of days to analyze (default: 7)
  --format           Output format: text|json (default: text)
```

Report includes:
- Total workflows
- Success/failure rates
- Average completion time
- Cache hit rates

Acceptance checks (must pass locally):
- CLI: python -m tbcv admin report performance
- CLI: python -m tbcv admin report performance --days 30 --format json
- Tests: pytest tests/cli/test_admin_reports.py::test_performance -v

Deliverables:
1. New CLI command in cli/main.py
2. Comprehensive tests
3. Updated CLI documentation

Runbook:
1. git checkout -b feat/admin-reports-cli
2. Add report subgroup and command to cli/main.py
3. pytest tests/cli/test_admin_reports.py -v
4. Update docs/cli_usage.md
5. git add -A && git commit -m "Add admin report performance CLI command"
```

---

### TASK-B14: Add admin report health CLI Command

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Add CLI command for health report
- Allowed paths:
  - cli/main.py
  - tests/cli/test_admin_reports.py
  - docs/cli_usage.md
- Forbidden: any other file

Command Spec:
```bash
tbcv admin report health [OPTIONS]
  --format           Output format: text|json (default: text)
```

Report includes:
- Database connection status
- Agents registered
- Overall system status

Acceptance checks (must pass locally):
- CLI: python -m tbcv admin report health
- Tests: pytest tests/cli/test_admin_reports.py::test_health -v

Deliverables:
1. New CLI command in cli/main.py
2. Comprehensive tests
3. Updated CLI documentation

Runbook:
1. git checkout -b feat/admin-health-report-cli (or continue from B13)
2. Add command to cli/main.py
3. pytest tests/cli/test_admin_reports.py -v
4. Update docs/cli_usage.md
5. git add -A && git commit -m "Add admin report health CLI command"
```

---

### TASK-B15: Add admin health-live CLI Command (K8s Probe)

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Add Kubernetes-style liveness probe command
- Allowed paths:
  - cli/main.py
  - tests/cli/test_admin_health.py
  - docs/cli_usage.md
- Forbidden: any other file

Command Spec:
```bash
tbcv admin health-live
# Exits 0 if alive, non-zero otherwise
```

Acceptance checks (must pass locally):
- CLI: python -m tbcv admin health-live && echo "alive"
- Tests: pytest tests/cli/test_admin_health.py::test_live -v

Deliverables:
1. New CLI command in cli/main.py
2. Comprehensive tests
3. Updated CLI documentation

Runbook:
1. git checkout -b feat/admin-health-probes-cli
2. Add command to cli/main.py
3. pytest tests/cli/test_admin_health.py -v
4. Update docs/cli_usage.md
5. git add -A && git commit -m "Add admin health-live CLI command"
```

---

### TASK-B16: Add admin health-ready CLI Command (K8s Probe)

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Add Kubernetes-style readiness probe command
- Allowed paths:
  - cli/main.py
  - tests/cli/test_admin_health.py
  - docs/cli_usage.md
- Forbidden: any other file

Command Spec:
```bash
tbcv admin health-ready
# Exits 0 if ready to serve, non-zero otherwise
# Checks: database connected, agents registered
```

Acceptance checks (must pass locally):
- CLI: python -m tbcv admin health-ready && echo "ready"
- Tests: pytest tests/cli/test_admin_health.py::test_ready -v

Deliverables:
1. New CLI command in cli/main.py
2. Comprehensive tests
3. Updated CLI documentation

Runbook:
1. Continue from B15
2. Add command to cli/main.py
3. pytest tests/cli/test_admin_health.py -v
4. Update docs/cli_usage.md
5. git add -A && git commit -m "Add admin health-ready CLI command"
```

---

### TASK-B17: Add admin agent-reload CLI Command

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Add CLI command to reload a specific agent
- Allowed paths:
  - cli/main.py
  - tests/cli/test_admin_agents.py
  - docs/cli_usage.md
- Forbidden: any other file

Command Spec:
```bash
tbcv admin agent-reload <agent_id>
```

Actions performed:
- Clear agent's cache
- Reload config (if applicable)
- Reset state (if applicable)

Acceptance checks (must pass locally):
- CLI: python -m tbcv admin agent-reload truth_manager
- Tests: pytest tests/cli/test_admin_agents.py::test_reload -v

Deliverables:
1. New CLI command in cli/main.py
2. Comprehensive tests
3. Updated CLI documentation

Runbook:
1. git checkout -b feat/admin-agent-reload-cli
2. Add command to cli/main.py
3. pytest tests/cli/test_admin_agents.py -v
4. Update docs/cli_usage.md
5. git add -A && git commit -m "Add admin agent-reload CLI command"
```

---

### TASK-B18: Add admin checkpoint CLI Command

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Add CLI command to create system checkpoint
- Allowed paths:
  - cli/main.py
  - tests/cli/test_admin_checkpoint.py
  - docs/cli_usage.md
- Forbidden: any other file

Command Spec:
```bash
tbcv admin checkpoint [OPTIONS]
  --name, -n         Custom checkpoint name
```

Checkpoint includes:
- Workflow states
- Agent registry
- Cache statistics
- Timestamp

Acceptance checks (must pass locally):
- CLI: python -m tbcv admin checkpoint
- CLI: python -m tbcv admin checkpoint --name "pre-upgrade"
- Tests: pytest tests/cli/test_admin_checkpoint.py -v

Deliverables:
1. New CLI command in cli/main.py
2. Comprehensive tests
3. Updated CLI documentation

Runbook:
1. git checkout -b feat/admin-checkpoint-cli
2. Add command to cli/main.py
3. pytest tests/cli/test_admin_checkpoint.py -v
4. Update docs/cli_usage.md
5. git add -A && git commit -m "Add admin checkpoint CLI command"
```

---

## Category C: Design Pattern Gaps

These gaps implement advanced architectural patterns from `design_patterns.md`.

---

### TASK-C01: Implement Agentic RAG for Truth Lookups

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Add vector-based retrieval for truth data with LLM-augmented validation
- Allowed paths:
  - core/vector_store.py (create)
  - core/embeddings.py (create)
  - agents/truth_manager.py
  - config/rag.yaml
  - cli/main.py (index command only)
  - tests/core/test_vector_store.py (create)
  - docs/architecture.md
- Forbidden: any other file

Context:
- Current: Truth validation uses exact/fuzzy matching
- Target: Vector-based semantic retrieval with LLM validation

Architecture:
```
Content → Extract Claims → Vector Search → Retrieve Relevant Truths → LLM Validates
```

Acceptance checks (must pass locally):
- CLI: python -m tbcv admin index-truths --family words
- CLI: python -m tbcv validate --file test.md --validators truth (uses RAG)
- Tests: pytest tests/core/test_vector_store.py -v
- Verify: Semantic matches found that exact matching misses
- Verify: Fallback to exact matching when RAG unavailable

Deliverables:
1. core/vector_store.py - TruthVectorStore class
2. core/embeddings.py - Embedding generation via Ollama
3. Updated truth_manager.py with validate_with_rag()
4. config/rag.yaml with configuration
5. CLI command: admin index-truths
6. Comprehensive tests
7. Updated documentation

Implementation Steps:
1. Create core/embeddings.py with get_embedding() function
2. Create core/vector_store.py with TruthVectorStore class
3. Implement index_truths() to embed and store truth data
4. Implement search() for semantic retrieval
5. Update TruthManager with validate_with_rag()
6. Add fallback to exact matching
7. Add CLI command for indexing
8. Add tests
9. Update documentation

Config Structure (config/rag.yaml):
```yaml
rag:
  enabled: true
  embedding_model: "nomic-embed-text"
  vector_store: "in_memory"  # or "chromadb", "faiss"
  top_k: 5
  similarity_threshold: 0.7
  fallback_to_exact_match: true
  index_path: "data/truth_index"
```

Hard rules:
- Fallback to exact matching when RAG unavailable
- Do not require external vector store (in-memory default)
- Embeddings cached to avoid repeated Ollama calls
- Index persistence between runs
- Keep public function signatures
- Zero network calls in mock tests (mock Ollama)
- Do not introduce chromadb/faiss as required dependency (optional)

Regression Check:
- Run: pytest tests/test_truth_validation.py -v
- Verify exact matching still works
- Test with Ollama running and stopped
- Benchmark retrieval quality vs exact matching

Self-review (answer yes/no at the end):
- [ ] Vector store implemented
- [ ] Embeddings working
- [ ] RAG integration in TruthManager
- [ ] Fallback working
- [ ] CLI indexing command working
- [ ] Tests comprehensive
- [ ] Documentation updated

Runbook:
1. git checkout -b feat/agentic-rag-truth
2. Create core/embeddings.py
3. Create core/vector_store.py
4. Update agents/truth_manager.py
5. Create config/rag.yaml
6. Add CLI command
7. pytest tests/core/test_vector_store.py -v
8. pytest tests/test_truth_validation.py -v
9. Manual test: semantic retrieval quality
10. Update docs/architecture.md
11. git add -A && git commit -m "Implement Agentic RAG for truth lookups"
```

---

### TASK-C02: Implement Reflection Pattern for Recommendations

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Add critique-and-refine loop before persisting recommendations
- Allowed paths:
  - agents/recommendation_critic.py (create or update)
  - agents/recommendation_agent.py
  - prompts/recommendation_critique.json (create)
  - config/reflection.yaml
  - tests/agents/test_recommendation_critic.py
  - docs/agents.md
- Forbidden: any other file

Context:
- Current: Recommendations generated in single pass, no quality check
- Target: Critique → Refine → Deduplicate before persistence

Architecture:
```
Raw Recommendations → Critic → Refinement (if needed) → Deduplication → Final
```

Acceptance checks (must pass locally):
- CLI: python -m tbcv validate --file test.md (recommendations refined)
- Tests: pytest tests/agents/test_recommendation_critic.py -v
- Verify: Low-quality recommendations filtered out
- Verify: Refined recommendations have higher quality
- Verify: Duplicates removed

Deliverables:
1. agents/recommendation_critic.py with critique() and refine()
2. prompts/recommendation_critique.json with critique prompts
3. Updated recommendation_agent.py with reflection loop
4. config/reflection.yaml with settings
5. Comprehensive tests
6. Updated documentation

Implementation Steps:
1. Create RecommendationCriticAgent class
2. Implement critique() with quality scoring
3. Implement refine() for low-quality recommendations
4. Create critique prompts
5. Integrate into RecommendationAgent
6. Add deduplication
7. Add tests
8. Update documentation

Config Structure (config/reflection.yaml):
```yaml
reflection:
  enabled: true
  max_iterations: 2
  quality_threshold: 0.7
  discard_threshold: 0.3
  deduplicate: true
  similarity_threshold: 0.85
```

Hard rules:
- Never discard all recommendations (minimum 1 if any exist)
- Track refinement history for debugging
- Configurable thresholds
- Keep public function signatures
- Zero network calls in mock tests (mock LLM)
- Graceful degradation if critic unavailable

Regression Check:
- Run: pytest tests/test_recommendations.py -v
- Verify recommendation generation still works
- Test with reflection enabled and disabled
- Measure false positive reduction

Self-review (answer yes/no at the end):
- [ ] Critic agent implemented
- [ ] Refinement working
- [ ] Deduplication working
- [ ] Integration complete
- [ ] Tests comprehensive
- [ ] Documentation updated

Runbook:
1. git checkout -b feat/recommendation-reflection
2. Create agents/recommendation_critic.py
3. Create prompts/recommendation_critique.json
4. Update agents/recommendation_agent.py
5. Update config/reflection.yaml
6. pytest tests/agents/test_recommendation_critic.py -v
7. pytest tests/test_recommendations.py -v
8. Manual test: recommendation quality
9. Update docs/agents.md
10. git add -A && git commit -m "Implement reflection pattern for recommendations"
```

---

### TASK-C03: Implement Enhanced Parallel Execution (Full)

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Aggressive parallelization with validator-level concurrency
- Allowed paths:
  - core/validator_router.py
  - config/validation_flow.yaml
  - tests/core/test_validator_router.py
  - tests/core/test_performance.py
  - docs/architecture.md
- Forbidden: any other file

Context:
- Current: File-level parallelism only
- Target: Validator-level parallelism within each file

Architecture:
```
File 1 ─┬─ Tier 1 validators (parallel) ─┬─ Tier 2 (parallel) ─┬─ Tier 3
        │                                  │                      │
File 2 ─┼─ Tier 1 validators (parallel) ─┼─ Tier 2 (parallel) ─┼─ Tier 3
        │                                  │                      │
File 3 ─┴─ Tier 1 validators (parallel) ─┴─ Tier 2 (parallel) ─┴─ Tier 3
```

Acceptance checks (must pass locally):
- Performance: 100 files validated 2x faster than sequential
- Tests: pytest tests/core/test_validator_router.py -v
- Tests: pytest tests/core/test_performance.py -v
- Verify: Results identical to sequential execution
- Verify: Dependencies respected

Deliverables:
1. Updated core/validator_router.py with full parallel execution
2. Updated config/validation_flow.yaml with dependencies
3. Performance benchmarks
4. Comprehensive tests
5. Updated documentation

Hard rules:
- Results must be deterministic (same output every run)
- Respect validator dependencies
- Proper error handling in parallel context
- Memory-efficient (don't load all files at once)
- Keep public function signatures

Runbook:
1. git checkout -b feat/enhanced-parallel-execution
2. Update core/validator_router.py
3. Update config/validation_flow.yaml
4. Benchmark before: time pytest tests/test_performance.py
5. pytest tests/core/test_validator_router.py -v
6. Benchmark after
7. pytest tests/ -v
8. Update docs/architecture.md
9. git add -A && git commit -m "Implement enhanced parallel execution"
```

---

## Category D: Dashboard Admin Controls Gaps

These gaps complete Phase 3 from `dashboard_coverage.md` (previously skipped).

---

### TASK-D01: Add Delete All Workflows Endpoint and UI

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Add delete all workflows functionality to dashboard
- Allowed paths:
  - api/server.py
  - api/dashboard.py
  - templates/workflows_list.html
  - tests/api/test_dashboard_workflows.py
  - docs/api_reference.md
- Forbidden: any other file

Endpoint:
- DELETE /api/workflows/delete-all?confirm=true

Acceptance checks (must pass locally):
- Web: DELETE /api/workflows/delete-all?confirm=true
- Web: UI button with confirmation dialog
- Tests: pytest tests/api/test_dashboard_workflows.py::test_delete_all -v
- Verify: Requires confirm=true parameter
- Verify: Returns deleted count

Deliverables:
1. API endpoint in api/server.py
2. UI button in workflows_list.html
3. Comprehensive tests
4. Updated API documentation

Hard rules:
- Require confirmation parameter
- Return accurate deleted count
- Handle empty database gracefully
- Keep public function signatures

Runbook:
1. git checkout -b feat/dashboard-admin-controls
2. Add endpoint to api/server.py
3. Add UI button to template
4. pytest tests/api/test_dashboard_workflows.py -v
5. Update docs/api_reference.md
6. git add -A && git commit -m "Add delete all workflows endpoint"
```

---

### TASK-D02: Add Delete All Validations Endpoint and UI

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Add delete all validations via admin reset
- Allowed paths:
  - api/server.py
  - api/dashboard.py
  - templates/validations_list.html
  - tests/api/test_dashboard_validations.py
  - docs/api_reference.md
- Forbidden: any other file

Endpoint:
- POST /api/admin/reset with selective deletion

Acceptance checks (must pass locally):
- Web: Admin reset with delete_validations=true
- Tests: pytest tests/api/test_dashboard_validations.py::test_delete_all -v

Deliverables:
1. API endpoint enhancement
2. UI integration
3. Comprehensive tests
4. Updated documentation

Runbook:
1. Continue from D01
2. Enhance admin reset endpoint
3. Add UI integration
4. pytest tests/api/test_dashboard_validations.py -v
5. git add -A && git commit -m "Add delete all validations endpoint"
```

---

### TASK-D03: Add System Reset Endpoint and UI

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Add complete system reset functionality
- Allowed paths:
  - api/server.py
  - api/dashboard.py
  - templates/base.html (admin dropdown)
  - tests/api/test_dashboard.py
  - docs/api_reference.md
- Forbidden: any other file

Endpoint:
- POST /api/admin/reset
  - confirm: true (required)
  - delete_validations: bool
  - delete_workflows: bool
  - delete_recommendations: bool
  - delete_audit_logs: bool
  - clear_cache: bool

Acceptance checks (must pass locally):
- Web: Full system reset via admin panel
- Tests: pytest tests/api/test_dashboard.py::test_admin_reset -v
- Verify: Selective deletion works
- Verify: Returns accurate counts

Deliverables:
1. Full admin reset endpoint
2. Admin UI dropdown with reset option
3. Confirmation modal
4. Comprehensive tests
5. Updated documentation

Runbook:
1. Continue from D02
2. Complete admin reset endpoint
3. Add admin UI dropdown
4. pytest tests/api/test_dashboard.py -v
5. Update docs/api_reference.md
6. git add -A && git commit -m "Add system reset endpoint"
```

---

### TASK-D04: Add Admin Edge Case Tests

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Add tests for admin operation edge cases
- Allowed paths:
  - tests/api/test_dashboard.py
  - tests/api/test_dashboard_workflows.py
  - tests/api/test_dashboard_validations.py
- Forbidden: any other file

Test Cases:
- Delete on empty database
- Concurrent delete operations
- Delete during active workflow
- Partial deletion (some succeed, some fail)

Acceptance checks (must pass locally):
- Tests: pytest tests/api/test_dashboard*.py -v

Deliverables:
1. Edge case tests in existing test files
2. Fixtures for edge case scenarios

Runbook:
1. Continue from D03
2. Add edge case tests
3. pytest tests/api/test_dashboard*.py -v
4. git add -A && git commit -m "Add admin edge case tests"
```

---

## Category E: UI Testing Completion Gaps

These gaps complete `playwright_ui_testing.md` implementation.

---

### TASK-E01: Implement CI/CD Integration for UI Tests

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Add GitHub Actions workflow for Playwright UI tests
- Allowed paths:
  - .github/workflows/ui-tests.yml (create)
  - scripts/run_ui_tests.sh
  - scripts/run_ui_tests.bat
  - pyproject.toml (test deps only)
  - docs/testing.md
- Forbidden: any other file

Acceptance checks (must pass locally):
- Local: ./scripts/run_ui_tests.sh (or .bat)
- CI: Workflow runs on PR

Deliverables:
1. .github/workflows/ui-tests.yml
2. scripts/run_ui_tests.sh and .bat
3. Updated pyproject.toml with Playwright deps
4. Updated testing documentation

Runbook:
1. git checkout -b feat/ui-test-ci
2. Create workflow file
3. Create run scripts
4. Update pyproject.toml
5. Test locally
6. Update docs/testing.md
7. git add -A && git commit -m "Add CI/CD for UI tests"
```

---

### TASK-E02: Implement Visual Regression Tests

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Add visual regression testing with screenshot comparison
- Allowed paths:
  - tests/ui/test_visual_regression.py (create)
  - tests/ui/snapshots/ (create dir for baseline images)
  - docs/testing.md
- Forbidden: any other file

Test Cases:
- Dashboard home screenshot
- Validations list screenshot
- Validation detail screenshot
- Recommendation detail screenshot

Acceptance checks (must pass locally):
- Tests: pytest tests/ui/test_visual_regression.py -v
- Update snapshots: pytest tests/ui/test_visual_regression.py --update-snapshots

Deliverables:
1. tests/ui/test_visual_regression.py
2. Baseline snapshot images
3. Updated testing documentation

Hard rules:
- Mask dynamic content (timestamps, activity feed)
- Store snapshots in version control
- Clear instructions for updating snapshots

Runbook:
1. git checkout -b feat/visual-regression-tests
2. Create test file
3. Generate baseline snapshots
4. pytest tests/ui/test_visual_regression.py -v
5. Update docs/testing.md
6. git add -A && git commit -m "Add visual regression tests"
```

---

### TASK-E03: Implement Accessibility Tests

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Add accessibility testing for dashboard
- Allowed paths:
  - tests/ui/test_accessibility.py (create)
  - docs/testing.md
- Forbidden: any other file

Test Cases:
- Proper heading hierarchy
- Forms have labels
- Keyboard navigation works
- Focus indicators visible

Acceptance checks (must pass locally):
- Tests: pytest tests/ui/test_accessibility.py -v

Deliverables:
1. tests/ui/test_accessibility.py
2. Updated testing documentation

Runbook:
1. git checkout -b feat/accessibility-tests
2. Create test file
3. pytest tests/ui/test_accessibility.py -v
4. Update docs/testing.md
5. git add -A && git commit -m "Add accessibility tests"
```

---

## Category F: Test Infrastructure Gaps

These gaps ensure test suite health from `tests_coverage.md` and `failing_tests.md`.

---

### TASK-F01: Fix Async Event Loop Infrastructure

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Fix ~200 tests with async event loop issues
- Allowed paths:
  - tests/conftest.py
  - pytest.ini
  - All test files with async issues (update @pytest.mark.asyncio)
- Forbidden: production code files

Root Cause:
- Tests using asyncio.run() directly
- Missing @pytest.mark.asyncio decorators
- Event loop not properly managed

Acceptance checks (must pass locally):
- Tests: pytest tests/ -v (no event loop errors)
- Verify: All async tests have proper decorators

Deliverables:
1. Updated tests/conftest.py with session-scoped event loop
2. Updated pytest.ini with asyncio_mode
3. All async tests decorated properly

Implementation Steps:
1. Add event_loop fixture to conftest.py
2. Set asyncio_mode = auto in pytest.ini
3. Audit all async tests
4. Add @pytest.mark.asyncio where missing
5. Replace asyncio.run() with proper await

Hard rules:
- Do not modify production code
- All tests must pass after changes
- No test skips to hide issues

Runbook:
1. git checkout -b fix/async-test-infrastructure
2. Update conftest.py
3. Update pytest.ini
4. Audit and fix async tests (batch by directory)
5. pytest tests/ -v
6. git add -A && git commit -m "Fix async event loop infrastructure"
```

---

### TASK-F02: Fix Windows Encoding Issues

```
Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Fix ~43 tests with Windows encoding issues
- Allowed paths:
  - tests/conftest.py
  - pytest.ini
  - Test files with Unicode output
- Forbidden: production code files

Root Cause:
- Windows cp1252 encoding cannot handle Unicode chars like checkmarks
- stdout/stderr not configured for UTF-8

Acceptance checks (must pass locally):
- Tests: pytest tests/ -v (no encoding errors on Windows)
- Verify: Unicode output works correctly

Deliverables:
1. Updated tests/conftest.py with UTF-8 configuration
2. Updated pytest.ini with encoding settings
3. Any test-specific fixes needed

Implementation Steps:
1. Add UTF-8 configuration to conftest.py
2. Set PYTHONIOENCODING in pytest.ini
3. Test on Windows

Hard rules:
- Do not modify production code
- Cross-platform compatible
- No ASCII-only fallback (fix encoding properly)

Runbook:
1. git checkout -b fix/windows-encoding
2. Update conftest.py
3. Update pytest.ini
4. pytest tests/ -v (on Windows)
5. git add -A && git commit -m "Fix Windows encoding issues"
```

---

## Execution Order

### Phase 1: Foundation (Week 1)
Priority: Get tests green and core infrastructure solid

1. TASK-F01: Fix Async Event Loop Infrastructure
2. TASK-F02: Fix Windows Encoding Issues
3. TASK-A01: Merge heading_sizes.yaml into seo.yaml
4. TASK-A02: Implement Generic Configuration System

### Phase 2: Validation System (Week 2)
Priority: Complete validation system configuration

5. TASK-A03: Implement Truth Validator + LLM Composition
6. TASK-A04: Implement Tiered Validation Flow
7. TASK-A05: Implement Enhanced Error Reporting
8. TASK-A06: Implement Performance Optimization

### Phase 3: CLI Parity (Week 3-4)
Priority: Complete CLI/Web feature parity

9-18. TASK-B01 through TASK-B10 (grouped by feature area)
19-28. TASK-B11 through TASK-B18 (admin commands)

### Phase 4: Design Patterns (Week 5)
Priority: Implement advanced patterns

29. TASK-C01: Implement Agentic RAG
30. TASK-C02: Implement Reflection Pattern
31. TASK-C03: Implement Enhanced Parallel Execution

### Phase 5: Dashboard & Testing (Week 6)
Priority: Complete dashboard and testing

32-35. TASK-D01 through TASK-D04 (dashboard admin)
36-38. TASK-E01 through TASK-E03 (UI testing)

---

## Success Criteria

### Per-Task Criteria
- [ ] All acceptance checks pass
- [ ] No regressions detected
- [ ] Documentation updated
- [ ] Tests updated
- [ ] Self-review completed

### Overall Criteria
- [ ] All 38 tasks complete
- [ ] Full test suite passes: pytest tests/ -v
- [ ] CLI/Web parity: 100%
- [ ] Design pattern coverage: 7/7
- [ ] No technical debt in plans/

---

## Appendix A: File Reference

| Directory | Purpose |
|-----------|---------|
| `config/` | Configuration files |
| `agents/` | Agent implementations |
| `agents/validators/` | Validator implementations |
| `core/` | Core infrastructure |
| `api/` | Web API and dashboard |
| `cli/` | CLI implementation |
| `tests/` | All tests |
| `docs/` | Documentation |
| `prompts/` | LLM prompts |

---

## Appendix B: Dependency Graph

```
TASK-F01 ─┬─ TASK-A01 ─┬─ TASK-A02 ─┬─ TASK-A03 ─┬─ TASK-A04
TASK-F02 ─┘            │            │            │
                       └─ TASK-A05 ─┘            └─ TASK-A06

TASK-A04 ─── TASK-C03 (Enhanced Parallel depends on Tiered Flow)
TASK-A03 ─── TASK-C01 (RAG depends on Truth+LLM composition)
TASK-A02 ─── TASK-B* (CLI commands depend on config system)

TASK-C02 ─── Independent (can start after TASK-F*)
TASK-D* ─── Independent (can start after TASK-F*)
TASK-E* ─── Independent (can start after TASK-F*)
```

---

**Document Version:** 1.0
**Last Updated:** 2025-11-29
**Owner:** Engineering Team
