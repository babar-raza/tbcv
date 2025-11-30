# Validation System - Implementation Taskcards

> Generated: 2025-11-26
> Source: plans/validation_types.md (Approved Changes AC-001 through AC-007)
> Status: **✅ ALL TASKS COMPLETED** (2025-11-26)

---

## Implementation Order

| Order | Task ID | Name | Priority | Dependencies | Status |
|-------|---------|------|----------|--------------|--------|
| 1 | TASK-001 | Generic Configuration System | P0 | None | ✅ DONE |
| 2 | TASK-002 | Create Config Files (frontmatter, markdown, code, links, structure) | P1 | TASK-001 | ✅ DONE |
| 3 | TASK-003 | Merge SEO + Heading Sizes Config | P1 | TASK-001 | ✅ DONE |
| 4 | TASK-004 | Create LLM Config | P1 | TASK-001 | ✅ DONE |
| 5 | TASK-005 | Truth Validator + LLM Composition | P0 | TASK-001, TASK-004 | ✅ DONE |
| 6 | TASK-006 | Enhanced Error Handling and Reporting | P1 | TASK-001 | ✅ DONE |
| 7 | TASK-007 | Tiered Validation Flow | P0 | TASK-001, TASK-006 | ✅ DONE |
| 8 | TASK-008 | Performance Optimization | P2 | TASK-007 | ✅ DONE |

### Implementation Summary

- **Total Tests Added**: 185 tests
- **Config Files Created**: 9 YAML configs
- **Core Modules Created**: 4 new modules
- **See**: [reports/validation_types.md](../reports/validation_types.md) for current behaviors

---

## TASK-001: Generic Configuration System

**Source**: AC-003

---

Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Create generic configuration loader supporting rules, profiles, and family overrides
- Allowed paths:
  - `core/config_loader.py` (new)
  - `core/config.py` (update if exists)
  - `tests/core/test_config_loader.py` (new)
- Forbidden: any other file

Acceptance checks (must pass locally):
- CLI: `python -c "from core.config_loader import ConfigLoader; print('OK')"`
- Tests: `pytest tests/core/test_config_loader.py -v`
- No mock data used in production paths
- Configs in ./config/ are enforced end to end

Deliverables:
- Full file replacements only (no diffs, no stubs, no TODO)
- New tests in /tests/core/ covering happy path and a failing path that used to break
- If schemas change, include forward-compatible migration code

Hard rules:
- Windows friendly paths, CRLF preserved
- Keep public function signatures unless you justify and update all call sites
- Zero network calls in tests
- Deterministic runs: set seeds, stable ordering
- Do not introduce new dependencies

Self-review (answer yes/no at the end):
- Thorough, systematic, wired UI and backend, MCP usage intact, CLI and Web in sync, tests added and passing

Now:
1) Show the minimal design for the change
2) Provide the full updated files
3) Provide the tests
4) Provide a short runbook: exact commands in order

### Design Requirements

**ConfigLoader must support:**

```python
class ConfigLoader:
    """Generic configuration loader with rules, profiles, and family overrides."""

    def __init__(self, config_dir: str = "./config")
    def load(self, validator_name: str) -> ValidatorConfig
    def get_rules(self, validator_name: str, profile: str = "default") -> List[Rule]
    def get_profile(self, validator_name: str, profile: str) -> ProfileConfig
    def get_family_override(self, validator_name: str, family: str) -> Optional[Dict]
    def reload(self, validator_name: str = None) -> None
```

**Generic config structure to support:**

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

**Data classes:**

```python
@dataclass
class Rule:
    id: str
    enabled: bool
    level: str  # error, warning, info
    message: str
    params: Dict[str, Any]

@dataclass
class ProfileConfig:
    name: str
    rules: List[str]
    overrides: Dict[str, Any]

@dataclass
class ValidatorConfig:
    enabled: bool
    profile: str
    rules: Dict[str, Rule]
    profiles: Dict[str, ProfileConfig]
    family_overrides: Dict[str, Dict]
```

---

### Taskcard Completion Prompt

Task must be implemented end-to-end, with no TODOs, partial implementations, or skipped edge cases. You must verify that every requirement of TASK-001 is fully addressed and that no related file, code path, or configuration was left in an inconsistent or intermediate state. After implementing TASK-001, you must perform a system-wide impact and regression check to ensure that it does not introduce any regressions: all previously working scenarios, workflows, and integrations must continue to behave exactly as before (or better). If any ripple effects or side-effects are detected, you must identify, fix, and re-verify them before considering TASK-001 complete.

---

## TASK-002: Create Validator Config Files

**Source**: AC-003 (Implementation)

---

Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Create config files for YAML, Markdown, Code, Links, Structure validators using generic format
- Allowed paths:
  - `config/frontmatter.yaml` (new)
  - `config/markdown.yaml` (new)
  - `config/code.yaml` (new)
  - `config/links.yaml` (new)
  - `config/structure.yaml` (new)
  - `agents/validators/yaml_validator.py` (update to use config)
  - `agents/validators/markdown_validator.py` (update to use config)
  - `agents/validators/code_validator.py` (update to use config)
  - `agents/validators/link_validator.py` (update to use config)
  - `agents/validators/structure_validator.py` (update to use config)
  - `tests/agents/validators/test_yaml_validator.py` (update)
  - `tests/agents/validators/test_markdown_validator.py` (update)
  - `tests/agents/validators/test_code_validator.py` (update)
  - `tests/agents/validators/test_link_validator.py` (update)
  - `tests/agents/validators/test_structure_validator.py` (update)
- Forbidden: any other file

Acceptance checks (must pass locally):
- CLI: `python -c "from agents.validators.yaml_validator import YamlValidatorAgent; print('OK')"`
- Tests: `pytest tests/agents/validators/ -v`
- Each validator loads its config from `config/{name}.yaml`
- No hardcoded values remain in validator code
- Configs in ./config/ are enforced end to end

Deliverables:
- Full file replacements only (no diffs, no stubs, no TODO)
- New tests covering config loading, profile switching, and family overrides
- All 5 config files with rules, profiles (strict/default/relaxed), and family_overrides

Hard rules:
- Windows friendly paths, CRLF preserved
- Keep public function signatures unless you justify and update all call sites
- Zero network calls in tests
- Deterministic runs: set seeds, stable ordering
- Do not introduce new dependencies

Self-review (answer yes/no at the end):
- Thorough, systematic, wired UI and backend, MCP usage intact, CLI and Web in sync, tests added and passing

Now:
1) Show the minimal design for the change
2) Provide the full updated files
3) Provide the tests
4) Provide a short runbook: exact commands in order

### Design Requirements

**config/frontmatter.yaml:**
```yaml
frontmatter:
  enabled: true
  profile: "default"
  rules:
    required_title:
      enabled: true
      level: error
      message: "Missing required field: title"
      params:
        field: title
    # ... more rules
  profiles:
    strict:
      rules: [required_title, required_description, field_length]
    default:
      rules: [required_title]
    relaxed:
      rules: []
  family_overrides:
    words:
      profile: "strict"
```

**config/markdown.yaml:**
```yaml
markdown:
  enabled: true
  profile: "default"
  rules:
    unclosed_code_block:
      enabled: true
      level: error
      message: "Unclosed code block detected"
    empty_link_url:
      enabled: true
      level: error
      message: "Link has empty URL"
    missing_alt_text:
      enabled: true
      level: warning
      message: "Image missing alt text"
    # ... more rules
```

**config/code.yaml:**
```yaml
code:
  enabled: true
  profile: "default"
  rules:
    code_block_too_long:
      enabled: true
      level: info
      message: "Code block exceeds maximum lines"
      params:
        max_lines: 100
    no_language_specified:
      enabled: true
      level: warning
      message: "Code block has no language specified"
    hardcoded_path:
      enabled: true
      level: warning
      message: "Hardcoded path detected in code"
      params:
        patterns: ['C:\\', '/home/', '/Users/']
```

**config/links.yaml:**
```yaml
links:
  enabled: true
  profile: "default"
  rules:
    empty_url:
      enabled: true
      level: error
      message: "Link has empty URL"
    localhost_link:
      enabled: true
      level: warning
      message: "Link points to localhost"
    placeholder_url:
      enabled: true
      level: warning
      message: "Link contains placeholder"
      params:
        patterns: ['#$', 'TODO', 'FIXME', 'example.com']
    invalid_scheme:
      enabled: true
      level: error
      message: "Invalid URL scheme"
      params:
        allowed: [http, https, mailto, ftp, tel]
```

**config/structure.yaml:**
```yaml
structure:
  enabled: true
  profile: "default"
  rules:
    content_too_short:
      enabled: true
      level: warning
      message: "Content below minimum length"
      params:
        min_chars: 100
    content_too_long:
      enabled: true
      level: info
      message: "Content exceeds maximum length"
      params:
        max_chars: 50000
    no_headings:
      enabled: true
      level: warning
      message: "Document has no headings"
    empty_section:
      enabled: true
      level: warning
      message: "Empty section detected"
```

---

### Taskcard Completion Prompt

Task must be implemented end-to-end, with no TODOs, partial implementations, or skipped edge cases. You must verify that every requirement of TASK-002 is fully addressed and that no related file, code path, or configuration was left in an inconsistent or intermediate state. After implementing TASK-002, you must perform a system-wide impact and regression check to ensure that it does not introduce any regressions: all previously working scenarios, workflows, and integrations must continue to behave exactly as before (or better). If any ripple effects or side-effects are detected, you must identify, fix, and re-verify them before considering TASK-002 complete.

---

## TASK-003: Merge SEO + Heading Sizes Config

**Source**: AC-002

---

Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Merge heading_sizes.yaml into seo.yaml as single unified SEO configuration
- Allowed paths:
  - `config/seo.yaml` (update)
  - `config/heading_sizes.yaml` (delete after merge)
  - `agents/validators/seo_validator.py` (update to use merged config)
  - `tests/agents/validators/test_seo_validator.py` (update)
- Forbidden: any other file

Acceptance checks (must pass locally):
- CLI: `python -c "from agents.validators.seo_validator import SeoValidatorAgent; print('OK')"`
- Tests: `pytest tests/agents/validators/test_seo_validator.py -v`
- SEO validator loads all settings from single `config/seo.yaml`
- `config/heading_sizes.yaml` no longer exists
- All heading size validation still works
- Configs in ./config/ are enforced end to end

Deliverables:
- Full file replacements only (no diffs, no stubs, no TODO)
- Updated tests covering H1 validation, hierarchy checks, AND heading sizes
- Merged config file with rules/profiles structure

Hard rules:
- Windows friendly paths, CRLF preserved
- Keep public function signatures unless you justify and update all call sites
- Zero network calls in tests
- Deterministic runs: set seeds, stable ordering
- Do not introduce new dependencies

Self-review (answer yes/no at the end):
- Thorough, systematic, wired UI and backend, MCP usage intact, CLI and Web in sync, tests added and passing

Now:
1) Show the minimal design for the change
2) Provide the full updated files
3) Provide the tests
4) Provide a short runbook: exact commands in order

### Design Requirements

**Merged config/seo.yaml:**
```yaml
seo:
  enabled: true
  profile: "default"

  rules:
    h1_required:
      enabled: true
      level: error
      message: "Document must have exactly one H1 heading"
    h1_unique:
      enabled: true
      level: error
      message: "Multiple H1 headings found"
    h1_first:
      enabled: true
      level: warning
      message: "H1 should be the first heading"
    hierarchy_skip:
      enabled: true
      level: error
      message: "Heading hierarchy skip detected (e.g., H1 to H3)"
    empty_heading:
      enabled: true
      level: warning
      message: "Empty heading detected"
    heading_too_short:
      enabled: true
      level: warning
      message: "Heading below minimum length"
    heading_too_long:
      enabled: true
      level: warning
      message: "Heading exceeds maximum length"

  # Heading size parameters (merged from heading_sizes.yaml)
  heading_sizes:
    h1: { min: 20, max: 70, recommended_min: 30, recommended_max: 60 }
    h2: { min: 10, max: 100, recommended_min: 20, recommended_max: 80 }
    h3: { min: 5, max: 100, recommended_min: 15, recommended_max: 70 }
    h4: { min: 5, max: 80, recommended_min: 10, recommended_max: 60 }
    h5: { min: 3, max: 70, recommended_min: 8, recommended_max: 50 }
    h6: { min: 3, max: 60, recommended_min: 8, recommended_max: 40 }

  profiles:
    strict:
      rules: [h1_required, h1_unique, h1_first, hierarchy_skip, empty_heading, heading_too_short, heading_too_long]
      overrides:
        heading_too_short: { level: error }
        heading_too_long: { level: error }
    default:
      rules: [h1_required, h1_unique, hierarchy_skip, empty_heading, heading_too_short, heading_too_long]
    relaxed:
      rules: [h1_required, empty_heading]

  family_overrides:
    words:
      profile: "strict"
```

---

### Taskcard Completion Prompt

Task must be implemented end-to-end, with no TODOs, partial implementations, or skipped edge cases. You must verify that every requirement of TASK-003 is fully addressed and that no related file, code path, or configuration was left in an inconsistent or intermediate state. After implementing TASK-003, you must perform a system-wide impact and regression check to ensure that it does not introduce any regressions: all previously working scenarios, workflows, and integrations must continue to behave exactly as before (or better). If any ripple effects or side-effects are detected, you must identify, fix, and re-verify them before considering TASK-003 complete.

---

## TASK-004: Create LLM Config

**Source**: AC-004

---

Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Externalize LLM validator configuration to config/llm.yaml
- Allowed paths:
  - `config/llm.yaml` (new)
  - `agents/llm_validator.py` (update to load config)
  - `tests/agents/test_llm_validator.py` (update)
- Forbidden: any other file

Acceptance checks (must pass locally):
- CLI: `python -c "from agents.llm_validator import LLMValidatorAgent; print('OK')"`
- Tests: `pytest tests/agents/test_llm_validator.py -v`
- LLM validator loads all settings from `config/llm.yaml`
- No hardcoded model params, URLs, or thresholds in code
- Graceful fallback when Ollama unavailable
- Configs in ./config/ are enforced end to end

Deliverables:
- Full file replacements only (no diffs, no stubs, no TODO)
- New tests covering config loading and fallback behavior
- Config file with connection, model_params, confidence settings

Hard rules:
- Windows friendly paths, CRLF preserved
- Keep public function signatures unless you justify and update all call sites
- Zero network calls in tests
- Deterministic runs: set seeds, stable ordering
- Do not introduce new dependencies

Self-review (answer yes/no at the end):
- Thorough, systematic, wired UI and backend, MCP usage intact, CLI and Web in sync, tests added and passing

Now:
1) Show the minimal design for the change
2) Provide the full updated files
3) Provide the tests
4) Provide a short runbook: exact commands in order

### Design Requirements

**config/llm.yaml:**
```yaml
llm:
  enabled: true
  profile: "default"

  connection:
    base_url: "http://localhost:11434"
    model: "mistral"
    timeout_seconds: 60
    retry_attempts: 3
    retry_backoff_seconds: 1.0

  model_params:
    temperature: 0.1
    top_p: 0.9
    num_predict: 2000
    seed: 42  # For deterministic outputs

  content:
    max_excerpt_length: 2000
    min_content_length: 50
    max_content_length: 50000

  confidence:
    min_plugin_confidence: 0.7
    min_issue_confidence: 0.8
    high_confidence_threshold: 0.9

  prompts:
    system_prompt_path: "./prompts/llm_validator_system.txt"
    use_chain_of_thought: true

  fallback:
    on_unavailable: "skip"      # skip | error | warn
    on_timeout: "skip"
    on_error: "skip"
    return_empty_on_skip: true

  profiles:
    strict:
      overrides:
        confidence:
          min_plugin_confidence: 0.8
          min_issue_confidence: 0.9
        fallback:
          on_unavailable: "warn"
    default: {}
    relaxed:
      overrides:
        confidence:
          min_plugin_confidence: 0.6
          min_issue_confidence: 0.7
```

**LLMValidatorAgent updates:**
```python
class LLMValidatorAgent:
    def __init__(self, ...):
        self.config = ConfigLoader().load("llm")
        self.base_url = self.config.get("connection", {}).get("base_url", "http://localhost:11434")
        self.model = self.config.get("connection", {}).get("model", "mistral")
        self.timeout = self.config.get("connection", {}).get("timeout_seconds", 60)
        # ... etc
```

---

### Taskcard Completion Prompt

Task must be implemented end-to-end, with no TODOs, partial implementations, or skipped edge cases. You must verify that every requirement of TASK-004 is fully addressed and that no related file, code path, or configuration was left in an inconsistent or intermediate state. After implementing TASK-004, you must perform a system-wide impact and regression check to ensure that it does not introduce any regressions: all previously working scenarios, workflows, and integrations must continue to behave exactly as before (or better). If any ripple effects or side-effects are detected, you must identify, fix, and re-verify them before considering TASK-004 complete.

---

## TASK-005: Truth Validator + LLM Composition

**Source**: AC-001 (Option 2)

---

Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Truth Validator composes with LLM Validator for semantic enhancement (3-phase flow)
- Allowed paths:
  - `config/truth.yaml` (new)
  - `agents/validators/truth_validator.py` (update)
  - `tests/agents/validators/test_truth_validator.py` (update)
- Forbidden: any other file

Acceptance checks (must pass locally):
- CLI: `python -c "from agents.validators.truth_validator import TruthValidatorAgent; print('OK')"`
- Tests: `pytest tests/agents/validators/test_truth_validator.py -v`
- Phase 1 (rule-based) always runs and returns results
- Phase 2 (LLM) runs when enabled and available, gracefully skips otherwise
- Phase 3 (merge) deduplicates and tags issue sources
- Rule-based results are NEVER lost
- Configs in ./config/ are enforced end to end

Deliverables:
- Full file replacements only (no diffs, no stubs, no TODO)
- New tests covering: rule-based only, rule-based + LLM, LLM failure fallback, deduplication
- Config file with rule_based and llm_enhancement sections

Hard rules:
- Windows friendly paths, CRLF preserved
- Keep public function signatures unless you justify and update all call sites
- Zero network calls in tests
- Deterministic runs: set seeds, stable ordering
- Do not introduce new dependencies

Self-review (answer yes/no at the end):
- Thorough, systematic, wired UI and backend, MCP usage intact, CLI and Web in sync, tests added and passing

Now:
1) Show the minimal design for the change
2) Provide the full updated files
3) Provide the tests
4) Provide a short runbook: exact commands in order

### Design Requirements

**config/truth.yaml:**
```yaml
truth:
  enabled: true
  profile: "default"

  # Phase 1: Rule-based validation (always runs)
  rule_based:
    check_plugin_mentions: true
    check_api_patterns: true
    check_forbidden_patterns: true
    check_required_fields: true

  # Phase 2: LLM enhancement (optional)
  llm_enhancement:
    enabled: true
    timeout_seconds: 30
    confidence_threshold: 0.7

    # Content limits
    min_content_length: 100
    max_content_length: 50000

    # Fallback behavior
    fallback_on_error: true
    fallback_on_timeout: true

    # What to check with LLM
    check_plugin_requirements: true
    check_plugin_combinations: true
    check_missing_plugins: true
    check_format_compatibility: true

  # Phase 3: Merge settings
  merge:
    dedup_strategy: "rule_based_priority"
    tag_sources: true

  # Strictness levels
  strictness:
    unknown_plugin: error
    forbidden_pattern: error
    missing_required_field: warning
    missing_prerequisite: warning    # LLM-detected
    invalid_combination: warning     # LLM-detected

  profiles:
    strict:
      overrides:
        llm_enhancement:
          confidence_threshold: 0.8
        strictness:
          missing_prerequisite: error
          invalid_combination: error
    default: {}
    relaxed:
      overrides:
        llm_enhancement:
          enabled: false
```

**3-Phase Flow Implementation:**

```python
class TruthValidatorAgent(BaseValidatorAgent):
    async def validate(self, content: str, context: Dict[str, Any]) -> ValidationResult:
        # PHASE 1: Rule-based (always runs)
        rule_result = await self._validate_rule_based(content, context)
        rule_issues = rule_result.issues

        # PHASE 2: LLM enhancement (optional)
        llm_issues = []
        if self._should_run_llm(content):
            llm_issues = await self._get_llm_enhancement(content, context, rule_issues)

        # PHASE 3: Intelligent merge
        merged_issues = self._merge_issues(rule_issues, llm_issues)

        return ValidationResult(
            confidence=self._calculate_confidence(rule_result, llm_issues),
            issues=merged_issues,
            metrics={...}
        )

    def _should_run_llm(self, content: str) -> bool:
        """Check if LLM should run based on config and content."""
        cfg = self.config.get("llm_enhancement", {})
        if not cfg.get("enabled", True):
            return False
        length = len(content)
        if length < cfg.get("min_content_length", 100):
            return False
        if length > cfg.get("max_content_length", 50000):
            return False
        return True

    async def _get_llm_enhancement(self, ...) -> List[ValidationIssue]:
        """Get LLM issues with graceful fallback."""
        try:
            llm_validator = agent_registry.get_agent("llm_validator")
            if not llm_validator:
                return []
            result = await asyncio.wait_for(
                llm_validator.handle_validate_plugins(...),
                timeout=self.config.get("llm_enhancement", {}).get("timeout_seconds", 30)
            )
            return self._filter_by_confidence(result.get("issues", []))
        except asyncio.TimeoutError:
            logger.warning("LLM enhancement timed out, using rule-based only")
            return []
        except Exception as e:
            logger.warning(f"LLM enhancement failed: {e}, using rule-based only")
            return []

    def _merge_issues(self, rule_issues: List, llm_issues: List) -> List[ValidationIssue]:
        """Merge issues, tagging sources and deduplicating."""
        # Tag rule-based issues
        for issue in rule_issues:
            issue.source = "rule_based"

        # Tag LLM issues
        for issue in llm_issues:
            issue.source = "llm_semantic"

        # Deduplicate (rule-based takes priority)
        seen = set()
        merged = []
        for issue in rule_issues:
            sig = (issue.category, issue.message[:50])
            seen.add(sig)
            merged.append(issue)

        for issue in llm_issues:
            sig = (issue.category, issue.message[:50])
            if sig not in seen:
                merged.append(issue)

        return merged
```

---

### Taskcard Completion Prompt

Task must be implemented end-to-end, with no TODOs, partial implementations, or skipped edge cases. You must verify that every requirement of TASK-005 is fully addressed and that no related file, code path, or configuration was left in an inconsistent or intermediate state. After implementing TASK-005, you must perform a system-wide impact and regression check to ensure that it does not introduce any regressions: all previously working scenarios, workflows, and integrations must continue to behave exactly as before (or better). If any ripple effects or side-effects are detected, you must identify, fix, and re-verify them before considering TASK-005 complete.

---

## TASK-006: Enhanced Error Handling and Reporting

**Source**: AC-006

---

Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Improve ValidationIssue structure with enhanced fields and multiple output formats
- Allowed paths:
  - `agents/validators/base_validator.py` (update ValidationIssue class)
  - `core/error_formatter.py` (new)
  - `api/server.py` (update response formatting)
  - `templates/validation_detail.html` (update for new fields)
  - `tests/agents/validators/test_base_validator.py` (update)
  - `tests/core/test_error_formatter.py` (new)
- Forbidden: any other file

Acceptance checks (must pass locally):
- CLI: `python -c "from agents.validators.base_validator import ValidationIssue; print('OK')"`
- Tests: `pytest tests/agents/validators/test_base_validator.py tests/core/test_error_formatter.py -v`
- ValidationIssue has all new fields (id, code, severity_score, context_snippet, fix_example, source, etc.)
- API returns enhanced JSON structure
- Dashboard displays new fields
- Configs in ./config/ are enforced end to end

Deliverables:
- Full file replacements only (no diffs, no stubs, no TODO)
- New tests covering enhanced issue creation, formatting, and output modes
- ErrorFormatter class supporting CLI, JSON, and HTML output

Hard rules:
- Windows friendly paths, CRLF preserved
- Keep public function signatures unless you justify and update all call sites
- Zero network calls in tests
- Deterministic runs: set seeds, stable ordering
- Do not introduce new dependencies

Self-review (answer yes/no at the end):
- Thorough, systematic, wired UI and backend, MCP usage intact, CLI and Web in sync, tests added and passing

Now:
1) Show the minimal design for the change
2) Provide the full updated files
3) Provide the tests
4) Provide a short runbook: exact commands in order

### Design Requirements

**Enhanced ValidationIssue:**

```python
@dataclass
class ValidationIssue:
    # Identification
    id: str = ""                      # "YAML-001", "SEO-003"
    code: str = ""                    # "YAML_MISSING_FIELD", "SEO_H1_MISSING"

    # Severity
    level: str = "warning"            # error, warning, info, critical
    severity_score: int = 50          # 1-100 for sorting

    # Location
    line_number: Optional[int] = None
    column: Optional[int] = None
    line_end: Optional[int] = None

    # Classification
    category: str = ""
    subcategory: str = ""

    # Messages
    message: str = ""
    suggestion: str = ""

    # Context
    context_snippet: str = ""         # The problematic text
    context_before: str = ""          # 2-3 lines before
    context_after: str = ""           # 2-3 lines after

    # Fix information
    fix_example: str = ""             # Actual corrected code
    auto_fixable: bool = False

    # Traceability
    source: str = "rule_based"        # "rule_based" | "llm_semantic"
    confidence: float = 1.0
    rule_id: str = ""                 # Which rule triggered this

    # Documentation
    documentation_url: str = ""
```

**ErrorFormatter class:**

```python
class ErrorFormatter:
    """Formats validation issues for different output modes."""

    @staticmethod
    def to_cli(issues: List[ValidationIssue], colorized: bool = True) -> str:
        """Format for CLI with colors and context snippets."""
        ...

    @staticmethod
    def to_json(issues: List[ValidationIssue], include_summary: bool = True) -> Dict:
        """Format for JSON API response."""
        return {
            "summary": {
                "total": len(issues),
                "by_level": {...},
                "by_category": {...},
                "auto_fixable": sum(1 for i in issues if i.auto_fixable)
            },
            "issues": [asdict(i) for i in issues]
        }

    @staticmethod
    def to_html_context(issues: List[ValidationIssue]) -> Dict:
        """Format for Jinja2 template context."""
        ...
```

**Severity scoring:**
```python
SEVERITY_SCORES = {
    "critical": 100,
    "error": 75,
    "warning": 50,
    "info": 25
}
```

---

### Taskcard Completion Prompt

Task must be implemented end-to-end, with no TODOs, partial implementations, or skipped edge cases. You must verify that every requirement of TASK-006 is fully addressed and that no related file, code path, or configuration was left in an inconsistent or intermediate state. After implementing TASK-006, you must perform a system-wide impact and regression check to ensure that it does not introduce any regressions: all previously working scenarios, workflows, and integrations must continue to behave exactly as before (or better). If any ripple effects or side-effects are detected, you must identify, fix, and re-verify them before considering TASK-006 complete.

---

## TASK-007: Tiered Validation Flow

**Source**: AC-005

---

Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Implement tiered validation flow with parallel execution and user control
- Allowed paths:
  - `config/validation_flow.yaml` (new)
  - `core/validator_router.py` (update)
  - `tests/core/test_validator_router.py` (update)
- Forbidden: any other file

Acceptance checks (must pass locally):
- CLI: `python -c "from core.validator_router import ValidatorRouter; print('OK')"`
- Tests: `pytest tests/core/test_validator_router.py -v`
- Tier 1, 2, 3 execute in order with parallel execution within tiers
- User can enable/disable any validator
- Early termination on critical errors (configurable)
- Dependencies respected (e.g., Truth waits for Fuzzy)
- Configs in ./config/ are enforced end to end

Deliverables:
- Full file replacements only (no diffs, no stubs, no TODO)
- New tests covering tier execution, parallelization, early termination, and user selection
- Config file with tier definitions, dependencies, and flow control

Hard rules:
- Windows friendly paths, CRLF preserved
- Keep public function signatures unless you justify and update all call sites
- Zero network calls in tests
- Deterministic runs: set seeds, stable ordering
- Do not introduce new dependencies

Self-review (answer yes/no at the end):
- Thorough, systematic, wired UI and backend, MCP usage intact, CLI and Web in sync, tests added and passing

Now:
1) Show the minimal design for the change
2) Provide the full updated files
3) Provide the tests
4) Provide a short runbook: exact commands in order

### Design Requirements

**Key Principle**: ALL validators are user-controllable. Nothing is forced optional.

**config/validation_flow.yaml:**
```yaml
validation_flow:
  enabled: true

  # Tier definitions
  tiers:
    tier1_syntax:
      name: "Syntax Validation"
      order: 1
      parallel: true
      validators:
        - yaml_validator
        - markdown_validator
        - structure_validator
      timeout_ms: 500

    tier2_content:
      name: "Content Validation"
      order: 2
      parallel: true
      validators:
        - link_validator
        - code_validator
        - seo_validator
        - fuzzy_detector
      timeout_ms: 2000

    tier3_semantic:
      name: "Semantic Validation"
      order: 3
      parallel: false  # Sequential due to dependencies
      validators:
        - truth_validator  # Composes with LLM internally
      timeout_ms: 30000

  # Dependencies between validators
  dependencies:
    truth_validator:
      requires: [fuzzy_detector]
      wait_for: true

  # Flow control
  flow_control:
    early_termination:
      enabled: true
      on_critical: true
      on_error_count: 10  # Stop after 10 errors

    continue_on_tier_failure: true
    collect_all_results: true

  # User selection (runtime override)
  default_validators:
    - yaml_validator
    - markdown_validator
    - structure_validator
    - link_validator
    - code_validator
    - seo_validator
    - fuzzy_detector
    - truth_validator
```

**ValidatorRouter updates:**

```python
class ValidatorRouter:
    """Routes validation requests through tiered execution."""

    async def validate(
        self,
        content: str,
        context: Dict[str, Any],
        selected_validators: Optional[List[str]] = None
    ) -> ValidationResult:
        """Execute validation with tiered flow."""
        # Use user selection or defaults
        validators_to_run = selected_validators or self.config.get("default_validators", [])

        all_issues = []
        all_metrics = {}

        for tier_name, tier_config in sorted(
            self.config.get("tiers", {}).items(),
            key=lambda x: x[1].get("order", 0)
        ):
            # Filter validators in this tier that user selected
            tier_validators = [
                v for v in tier_config.get("validators", [])
                if v in validators_to_run
            ]

            if not tier_validators:
                continue

            # Execute tier (parallel or sequential)
            if tier_config.get("parallel", True):
                tier_results = await self._execute_parallel(
                    tier_validators, content, context,
                    timeout_ms=tier_config.get("timeout_ms", 5000)
                )
            else:
                tier_results = await self._execute_sequential(
                    tier_validators, content, context
                )

            # Collect results
            for result in tier_results:
                all_issues.extend(result.issues)
                all_metrics.update(result.metrics)

            # Check early termination
            if self._should_terminate(all_issues):
                break

        return ValidationResult(
            confidence=self._calculate_overall_confidence(all_issues),
            issues=all_issues,
            metrics=all_metrics
        )

    async def _execute_parallel(self, validators, content, context, timeout_ms):
        """Execute validators in parallel using asyncio.gather."""
        tasks = [
            self._run_validator(v, content, context)
            for v in validators
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if not isinstance(r, Exception)]

    def _should_terminate(self, issues: List[ValidationIssue]) -> bool:
        """Check if validation should stop early."""
        flow_cfg = self.config.get("flow_control", {})
        term_cfg = flow_cfg.get("early_termination", {})

        if not term_cfg.get("enabled", True):
            return False

        # Check for critical issues
        if term_cfg.get("on_critical", True):
            if any(i.level == "critical" for i in issues):
                return True

        # Check error count
        max_errors = term_cfg.get("on_error_count", 0)
        if max_errors > 0:
            error_count = sum(1 for i in issues if i.level == "error")
            if error_count >= max_errors:
                return True

        return False
```

---

### Taskcard Completion Prompt

Task must be implemented end-to-end, with no TODOs, partial implementations, or skipped edge cases. You must verify that every requirement of TASK-007 is fully addressed and that no related file, code path, or configuration was left in an inconsistent or intermediate state. After implementing TASK-007, you must perform a system-wide impact and regression check to ensure that it does not introduce any regressions: all previously working scenarios, workflows, and integrations must continue to behave exactly as before (or better). If any ripple effects or side-effects are detected, you must identify, fix, and re-verify them before considering TASK-007 complete.

---

## TASK-008: Performance Optimization

**Source**: AC-007

---

Role: Senior engineer. Produce drop-in, production-ready code.

Scope (only this):
- Fix: Implement caching strategies and performance optimizations
- Allowed paths:
  - `config/cache.yaml` (new)
  - `core/cache.py` (update or new)
  - `core/performance.py` (new)
  - `agents/validators/base_validator.py` (add caching hooks)
  - `tests/core/test_cache.py` (update or new)
  - `tests/core/test_performance.py` (new)
- Forbidden: any other file

Acceptance checks (must pass locally):
- CLI: `python -c "from core.cache import ValidationCache; print('OK')"`
- Tests: `pytest tests/core/test_cache.py tests/core/test_performance.py -v`
- Validation results cached by content hash
- LLM responses cached by prompt hash
- Truth data preloaded at startup
- Cache invalidation on config/truth file changes
- Configs in ./config/ are enforced end to end

Deliverables:
- Full file replacements only (no diffs, no stubs, no TODO)
- New tests covering cache hits, misses, invalidation, and TTL expiry
- Config file with caching strategies per data type

Hard rules:
- Windows friendly paths, CRLF preserved
- Keep public function signatures unless you justify and update all call sites
- Zero network calls in tests
- Deterministic runs: set seeds, stable ordering
- Do not introduce new dependencies

Self-review (answer yes/no at the end):
- Thorough, systematic, wired UI and backend, MCP usage intact, CLI and Web in sync, tests added and passing

Now:
1) Show the minimal design for the change
2) Provide the full updated files
3) Provide the tests
4) Provide a short runbook: exact commands in order

### Design Requirements

**config/cache.yaml:**
```yaml
cache:
  enabled: true

  validation_results:
    enabled: true
    strategy: "content_hash"      # SHA256 of content
    ttl_seconds: 3600             # 1 hour
    max_entries: 1000
    invalidate_on:
      - config_change
      - truth_change

  llm_responses:
    enabled: true
    strategy: "prompt_hash"       # SHA256 of prompt
    ttl_seconds: 86400            # 24 hours (expensive calls)
    max_entries: 500
    invalidate_on:
      - model_change
      - config_change

  truth_data:
    strategy: "file_mtime"        # Reload on file change
    preload:
      - words
      - pdf
      - cells
      - slides
    watch_files: true

  compiled_patterns:
    precompile: true              # At startup
    cache_regex: true

  # Memory limits
  limits:
    max_memory_mb: 256
    eviction_policy: "LRU"
```

**ValidationCache class:**

```python
class ValidationCache:
    """Caching layer for validation results."""

    def __init__(self, config_path: str = "./config/cache.yaml"):
        self.config = self._load_config(config_path)
        self._result_cache: Dict[str, CacheEntry] = {}
        self._llm_cache: Dict[str, CacheEntry] = {}
        self._truth_cache: Dict[str, Any] = {}
        self._file_mtimes: Dict[str, float] = {}

    def get_result(self, content: str, validators: List[str]) -> Optional[ValidationResult]:
        """Get cached validation result."""
        if not self.config.get("validation_results", {}).get("enabled", True):
            return None

        cache_key = self._make_result_key(content, validators)
        entry = self._result_cache.get(cache_key)

        if entry and not entry.is_expired():
            return entry.value
        return None

    def set_result(self, content: str, validators: List[str], result: ValidationResult):
        """Cache validation result."""
        if not self.config.get("validation_results", {}).get("enabled", True):
            return

        cache_key = self._make_result_key(content, validators)
        ttl = self.config.get("validation_results", {}).get("ttl_seconds", 3600)
        self._result_cache[cache_key] = CacheEntry(value=result, ttl_seconds=ttl)
        self._enforce_limits()

    def get_llm_response(self, prompt_hash: str) -> Optional[Dict]:
        """Get cached LLM response."""
        ...

    def set_llm_response(self, prompt_hash: str, response: Dict):
        """Cache LLM response."""
        ...

    def invalidate_on_config_change(self):
        """Clear caches when config changes."""
        self._result_cache.clear()
        self._llm_cache.clear()

    def invalidate_on_truth_change(self):
        """Clear caches when truth data changes."""
        self._result_cache.clear()
        self._truth_cache.clear()

    def preload_truth_data(self, families: List[str]):
        """Preload truth data at startup."""
        ...

    def _make_result_key(self, content: str, validators: List[str]) -> str:
        """Create cache key from content hash + validator list."""
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        validator_hash = hashlib.sha256(",".join(sorted(validators)).encode()).hexdigest()[:8]
        return f"{content_hash}:{validator_hash}"

    def _enforce_limits(self):
        """Enforce memory limits using LRU eviction."""
        max_entries = self.config.get("validation_results", {}).get("max_entries", 1000)
        while len(self._result_cache) > max_entries:
            # Remove oldest entry (LRU)
            oldest_key = min(self._result_cache, key=lambda k: self._result_cache[k].created_at)
            del self._result_cache[oldest_key]


@dataclass
class CacheEntry:
    value: Any
    ttl_seconds: int
    created_at: float = field(default_factory=time.time)

    def is_expired(self) -> bool:
        return time.time() - self.created_at > self.ttl_seconds
```

**Performance utilities:**

```python
# core/performance.py

class PerformanceMonitor:
    """Monitor and optimize validation performance."""

    @staticmethod
    def precompile_patterns(truth_data: Dict) -> Dict[str, re.Pattern]:
        """Precompile regex patterns at startup."""
        ...

    @staticmethod
    def batch_optimize(files: List[str], batch_size: int = 10) -> Iterator[List[str]]:
        """Yield optimized batches for parallel processing."""
        ...

    @staticmethod
    def measure_time(func):
        """Decorator to measure function execution time."""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = await func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            logger.debug(f"{func.__name__} took {elapsed:.3f}s")
            return result
        return wrapper
```

---

### Taskcard Completion Prompt

Task must be implemented end-to-end, with no TODOs, partial implementations, or skipped edge cases. You must verify that every requirement of TASK-008 is fully addressed and that no related file, code path, or configuration was left in an inconsistent or intermediate state. After implementing TASK-008, you must perform a system-wide impact and regression check to ensure that it does not introduce any regressions: all previously working scenarios, workflows, and integrations must continue to behave exactly as before (or better). If any ripple effects or side-effects are detected, you must identify, fix, and re-verify them before considering TASK-008 complete.

---

## Quick Reference: Runbook Template

Each task should follow this runbook pattern:

```bash
# 1. Verify starting state
pytest tests/ -v --tb=short

# 2. Create/update files
# (implement changes)

# 3. Run specific tests
pytest tests/path/to/test_file.py -v

# 4. Run full test suite
pytest tests/ -v --tb=short

# 5. Manual verification
python -c "from module import Class; print('OK')"

# 6. Check for regressions
python start_web.py  # Test web UI
python ucop_cli.py run --workflow default_blog  # Test CLI (if applicable)
```

---

## Dependency Graph

```
TASK-001 (Generic Config)
    │
    ├──► TASK-002 (Config Files)
    │
    ├──► TASK-003 (SEO Config Merge)
    │
    ├──► TASK-004 (LLM Config)
    │        │
    │        └──► TASK-005 (Truth+LLM)
    │
    └──► TASK-006 (Error Handling)
             │
             └──► TASK-007 (Tiered Flow)
                      │
                      └──► TASK-008 (Performance)
```

---

## Notes

- Tasks should be completed in order due to dependencies
- Each task is self-contained with clear acceptance criteria
- All tasks use the generic configuration system from TASK-001
- Backward compatibility must be maintained throughout
- Tests must pass at each step before proceeding
