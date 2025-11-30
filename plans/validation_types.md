# Validation Types - Living Plan

> Last Updated: 2025-11-26
> Status: Active Discussion

This is a living document that tracks discussions, approved changes, and planned improvements to the validation system.

---

## Table of Contents

1. [Current State](#current-state)
2. [Discussion Log](#discussion-log)
3. [Pending Decisions](#pending-decisions)
4. [Option 2 Implementation Plan](#option-2-implementation-plan)
5. [Configuration Proposals](#configuration-proposals)

---

## Current State

### Validation Types (10 total)

| # | Type | Config File | Status |
|---|------|-------------|--------|
| 1 | YAML | `config/frontmatter.yaml` (proposed) | Hardcoded |
| 2 | Markdown | `config/markdown.yaml` (proposed) | Hardcoded |
| 3 | Code | `config/code.yaml` (proposed) | Hardcoded |
| 4 | Links | `config/links.yaml` (proposed) | Hardcoded |
| 5 | Structure | `config/structure.yaml` (proposed) | Hardcoded |
| 6 | Truth | `truth/{family}.json` + LLM | **APPROVED: Option 2** |
| 7 | FuzzyLogic | `config/main.yaml` + `truth/{family}.json` | Configured |
| 8 | SEO | `config/seo.yaml` | Configured |
| 9 | Heading Sizes | `config/seo.yaml` (merge proposed) | Configured |
| 10 | LLM | `config/llm.yaml` (proposed) | Hardcoded |

---

## Discussion Log

### Session: 2025-11-26

**Topic**: Configuration standardization for all validators

**Key Decisions**:
- Each validator gets its own config file in `config/`
- Truth Validator MUST use LLM (Option 2 selected)
- SEO + Heading Sizes should be merged into single `seo.yaml`

---

### Session: 2025-11-26 (Continued)

**Topic**: Truth Validator + LLM Integration

**Requirement**: Truth Validator MUST also use LLM for semantic validation

**Selected Approach**: **Option 2 - Compose with LLM Validator**

**Rationale**:
- Reuses existing LLM Validator code (no duplication)
- Clear separation of concerns
- LLM enhances rule-based findings
- Graceful degradation when LLM unavailable

---

## Approved Changes

### [AC-001] - Truth Validator + LLM Composition (Option 2)

- **Date Approved**: 2025-11-26
- **Description**: Truth Validator will compose with LLM Validator for semantic enhancement
- **Implementation**:
  - Phase 1: Rule-based validation (always runs)
  - Phase 2: LLM enhancement (optional, graceful fallback)
  - Phase 3: Intelligent merge (dedup, confidence filtering)
- **Files Affected**:
  - `agents/validators/truth_validator.py`
  - `config/truth.yaml` (new)
- **Status**: Pending Implementation

### [AC-002] - Merge heading_sizes.yaml into seo.yaml

- **Date Approved**: 2025-11-26
- **Description**: Consolidate heading_sizes.yaml into seo.yaml as a single SEO configuration
- **Rationale**: Both are heading-related SEO concerns, single file is cleaner
- **Implementation**:
  - Move `heading_sizes` section into `config/seo.yaml`
  - Update `SeoValidatorAgent` to load from single file
  - Delete `config/heading_sizes.yaml`
- **Files Affected**:
  - `config/seo.yaml` (update)
  - `config/heading_sizes.yaml` (delete)
  - `agents/validators/seo_validator.py` (update)
- **Status**: Pending Implementation

### [AC-003] - Generic Configuration System with Rules & Profiles

- **Date Approved**: 2025-11-26
- **Description**: Implement a generic, extensible configuration system for all validators
- **Key Features**:
  - **Rules Library**: Individual checks with id, level, message, params
  - **Profiles**: Pre-defined rule sets (strict, default, relaxed)
  - **Family Overrides**: Per-content-type customization
  - **Extensibility**: Add new rules in YAML without code changes
- **Structure**:
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
- **Files Affected**:
  - All config files (frontmatter, markdown, code, links, structure)
  - `core/config_loader.py` (new generic loader)
  - All validator agents (to use generic loader)
- **Status**: Pending Implementation

### [AC-004] - Create config/llm.yaml

- **Date Approved**: 2025-11-26
- **Description**: Externalize LLM validator configuration
- **Implementation**:
  - Create `config/llm.yaml` with connection, model_params, confidence settings
  - Update `LLMValidatorAgent` to load from config file
- **Files Affected**:
  - `config/llm.yaml` (new)
  - `agents/llm_validator.py` (update)
- **Status**: Pending Implementation

### [AC-005] - Tiered Validation Flow with Parallel Execution

- **Date Approved**: 2025-11-26
- **Description**: Optimize validation flow with tiered execution and parallelization
- **Key Principle**: ALL validators are user-controllable. Nothing is forced optional.
- **Implementation**:
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
- **Features**:
  - Parallel execution within tiers (for speed)
  - Dependency-aware ordering (Truth waits for Fuzzy)
  - Early termination on critical errors (configurable)
  - User selects any combination of validators
- **Files Affected**:
  - `core/validator_router.py` (update)
  - `config/validation_flow.yaml` (new)
- **Status**: Pending Implementation

### [AC-006] - Enhanced Error Handling and Reporting

- **Date Approved**: 2025-11-26
- **Description**: Improved error structure and multiple output formats
- **Enhanced Issue Structure**:
  ```python
  EnhancedValidationIssue:
    id: str                    # "YAML-001"
    code: str                  # "YAML_MISSING_FIELD"
    level: str                 # error|warning|info|critical
    severity_score: int        # 1-100 for sorting
    line_number, column, line_end
    category, subcategory
    message, suggestion
    context_snippet            # Problematic text
    context_before, context_after
    fix_example               # Actual fixed code
    auto_fixable: bool
    source: str               # "rule_based"|"llm_semantic"
    confidence: float
    documentation_url
  ```
- **Output Formats**:
  - CLI: Color-coded with context snippets
  - JSON API: Full structured response with summary
  - HTML Dashboard: Grouped, sortable, filterable
- **Files Affected**:
  - `agents/validators/base_validator.py` (update ValidationIssue)
  - `api/server.py` (response formatting)
  - `templates/` (dashboard display)
- **Status**: Pending Implementation

### [AC-007] - Performance Optimization (Caching & Parallelization)

- **Date Approved**: 2025-11-26
- **Description**: Caching strategies and performance improvements
- **Caching Strategy**:
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
- **Performance Features**:
  - Parallel validator execution (asyncio.gather)
  - Lazy loading of truth data
  - Connection pooling for LLM
  - Batch processing optimization
  - Progressive validation for UI (WebSocket events)
- **Files Affected**:
  - `core/cache.py` (new/update)
  - `config/cache.yaml` (new)
  - All validator agents (async optimization)
- **Status**: Pending Implementation

---

## Pending Decisions

### ~~[PD-001] - Merge heading_sizes.yaml into seo.yaml~~ → MOVED TO AC-002
- **Status**: ✅ APPROVED
- **Decision**: Merge heading_sizes.yaml into seo.yaml

---

## Option 2 Implementation Plan (APPROVED)

### Overview

**Goal**: Truth Validator composes with LLM Validator to provide semantic enhancement of rule-based validation.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Truth Validator Flow                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  INPUT: content, context (family, file_path, etc.)                  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ PHASE 1: Rule-Based Validation (Always runs)                 │   │
│  │                                                               │   │
│  │  1. Load truth data from TruthManager                        │   │
│  │  2. Validate plugin mentions against known plugins           │   │
│  │  3. Validate API patterns                                    │   │
│  │  4. Check forbidden patterns                                 │   │
│  │  5. Collect rule_based_issues                                │   │
│  │                                                               │   │
│  │  Output: rule_based_issues, detected_plugins, truth_context  │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                              │                                       │
│                              ▼                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ PHASE 2: LLM Enhancement (Optional, configurable)            │   │
│  │                                                               │   │
│  │  IF llm_enabled AND ollama_available:                        │   │
│  │    1. Get LLM Validator from agent_registry                  │   │
│  │    2. Call llm_validator.handle_validate_plugins() with:     │   │
│  │       - content                                              │   │
│  │       - detected_plugins (from Phase 1)                      │   │
│  │       - rule_based_issues (for context)                      │   │
│  │       - truth_context                                        │   │
│  │    3. Receive semantic_issues from LLM                       │   │
│  │                                                               │   │
│  │  ELSE:                                                        │   │
│  │    semantic_issues = [] (graceful fallback)                  │   │
│  │                                                               │   │
│  │  Output: semantic_issues                                     │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                              │                                       │
│                              ▼                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ PHASE 3: Intelligent Merge                                   │   │
│  │                                                               │   │
│  │  1. Deduplicate issues (rule-based takes priority)           │   │
│  │  2. Apply confidence thresholds to LLM issues                │   │
│  │  3. Tag issue sources: "rule_based" vs "llm_semantic"        │   │
│  │  4. Calculate combined confidence score                      │   │
│  │                                                               │   │
│  │  Output: merged_issues, combined_confidence                  │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  OUTPUT: ValidationResult(issues, confidence, metrics)              │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

### How This Improves Results

#### 1. **Rule-Based Catches What Patterns Can Detect**
- Plugin name misspellings
- Unknown plugin references
- Forbidden API patterns
- Missing required fields

#### 2. **LLM Catches Semantic Issues Patterns Cannot**
- Missing prerequisites: "DOCX→PDF conversion needs Document Converter"
- Incorrect plugin combinations: "Mail Merge requires Word Processor"
- Logical inconsistencies: "Document says 'converts to PDF' but only mentions Word Processor"
- Context-aware validation: Understanding what the document is trying to achieve

#### 3. **Combined Strength**
| Issue Type | Rule-Based | LLM | Combined |
|------------|------------|-----|----------|
| Misspelled plugin name | ✅ Fast, accurate | ❌ Overkill | ✅ Rule-based |
| Unknown plugin | ✅ Pattern match | ❌ May hallucinate | ✅ Rule-based |
| Missing prerequisite | ❌ No semantic understanding | ✅ Understands context | ✅ LLM |
| Invalid combination | ❌ Would need all combos | ✅ Reasons about rules | ✅ LLM |
| Format compatibility | ❌ Needs explicit rules | ✅ Understands formats | ✅ LLM |

---

### How This Prevents Degradation

#### 1. **Rule-Based Results Are NEVER Lost**
```python
# Phase 1 results are always included
final_issues = rule_based_issues.copy()

# LLM issues are ADDED, not replaced
if llm_available:
    semantic_issues = await self._get_llm_enhancement(...)
    final_issues.extend(semantic_issues)
```

#### 2. **Graceful Degradation When LLM Unavailable**
```python
async def _get_llm_enhancement(self, ...) -> List[ValidationIssue]:
    """Get LLM enhancement with graceful fallback."""
    try:
        llm_validator = agent_registry.get_agent("llm_validator")
        if not llm_validator:
            logger.info("LLM Validator not available, using rule-based only")
            return []

        result = await llm_validator.handle_validate_plugins(params)
        return self._convert_llm_issues(result.get("issues", []))

    except Exception as e:
        logger.warning(f"LLM enhancement failed: {e}, continuing with rule-based")
        return []  # Never fail, just return empty
```

#### 3. **Confidence Thresholds Filter Low-Quality LLM Suggestions**
```python
def _filter_llm_issues(self, issues: List[Dict], threshold: float = 0.7) -> List[ValidationIssue]:
    """Only accept LLM issues above confidence threshold."""
    filtered = []
    for issue in issues:
        confidence = issue.get("confidence", 0.0)
        if confidence >= threshold:
            filtered.append(ValidationIssue(
                level=issue.get("level", "warning"),
                category=issue.get("category", "llm_semantic"),
                message=issue.get("message"),
                suggestion=issue.get("fix_suggestion"),
                source="llm_semantic",  # Tag the source
                auto_fixable=issue.get("auto_fixable", False)
            ))
        else:
            logger.debug(f"Filtered low-confidence LLM issue: {issue.get('message')} ({confidence})")
    return filtered
```

#### 4. **Deduplication Prevents Double-Reporting**
```python
def _deduplicate_issues(
    self,
    rule_based: List[ValidationIssue],
    llm_semantic: List[ValidationIssue]
) -> List[ValidationIssue]:
    """Merge issues, preferring rule-based for duplicates."""
    seen_signatures = set()
    merged = []

    # Rule-based issues take priority
    for issue in rule_based:
        signature = (issue.category, issue.message[:50])
        seen_signatures.add(signature)
        merged.append(issue)

    # Only add LLM issues that don't duplicate
    for issue in llm_semantic:
        signature = (issue.category, issue.message[:50])
        if signature not in seen_signatures:
            merged.append(issue)

    return merged
```

#### 5. **Performance Protection**
```python
# Configuration in config/truth.yaml or config/llm.yaml
truth:
  llm_enhancement:
    enabled: true                    # Master switch
    timeout_seconds: 30              # Don't wait forever
    min_content_length: 100          # Skip LLM for tiny files
    max_content_length: 50000        # Skip LLM for huge files
    confidence_threshold: 0.7        # Filter low-confidence
    fallback_on_error: true          # Never fail, just skip
```

---

### Implementation Changes to `truth_validator.py`

```python
# Proposed structure for truth_validator.py

class TruthValidatorAgent(BaseValidatorAgent):
    """Validates content against truth data with optional LLM enhancement."""

    def __init__(self, agent_id: Optional[str] = None):
        super().__init__(agent_id or "truth_validator")
        self.config = self._load_config()  # Load from config/truth.yaml

    async def validate(self, content: str, context: Dict[str, Any]) -> ValidationResult:
        """Validate with rule-based checks + optional LLM enhancement."""
        family = context.get("family", "words")

        # PHASE 1: Rule-based validation (always runs)
        rule_result = await self._validate_rule_based(content, family)
        rule_issues = rule_result.issues
        detected_plugins = rule_result.metrics.get("detected_plugins", [])
        truth_context = rule_result.metrics.get("truth_context", {})

        # PHASE 2: LLM enhancement (optional)
        llm_issues = []
        if self.config.get("llm_enhancement", {}).get("enabled", True):
            llm_issues = await self._get_llm_enhancement(
                content=content,
                family=family,
                detected_plugins=detected_plugins,
                rule_issues=rule_issues,
                truth_context=truth_context
            )

        # PHASE 3: Intelligent merge
        all_issues = self._merge_issues(rule_issues, llm_issues)

        # Calculate combined confidence
        rule_confidence = rule_result.confidence
        llm_confidence = self._calculate_llm_confidence(llm_issues)
        combined_confidence = self._combine_confidences(rule_confidence, llm_confidence)

        return ValidationResult(
            confidence=combined_confidence,
            issues=all_issues,
            auto_fixable_count=sum(1 for i in all_issues if i.auto_fixable),
            metrics={
                **rule_result.metrics,
                "llm_enhanced": len(llm_issues) > 0,
                "llm_issues_count": len(llm_issues),
                "total_issues": len(all_issues)
            }
        )

    async def _validate_rule_based(self, content: str, family: str) -> ValidationResult:
        """Existing rule-based validation logic."""
        # Current implementation moved here
        ...

    async def _get_llm_enhancement(self, ...) -> List[ValidationIssue]:
        """Get semantic issues from LLM Validator."""
        # Compose with LLM Validator
        ...

    def _merge_issues(self, rule: List, llm: List) -> List[ValidationIssue]:
        """Deduplicate and merge issues."""
        ...
```

---

### Configuration for Truth Validator

```yaml
# config/truth.yaml (or add to main.yaml under validators.truth)
truth:
  enabled: true

  # Rule-based validation
  rule_based:
    check_plugin_mentions: true
    check_api_patterns: true
    check_forbidden_patterns: true
    check_required_fields: true

  # LLM enhancement settings
  llm_enhancement:
    enabled: true                    # Enable LLM semantic validation
    timeout_seconds: 30              # Timeout for LLM call
    confidence_threshold: 0.7        # Min confidence for LLM issues

    # Content limits (skip LLM for edge cases)
    min_content_length: 100          # Skip if content too short
    max_content_length: 50000        # Skip if content too long

    # Fallback behavior
    fallback_on_error: true          # If LLM fails, return rule-based only
    fallback_on_timeout: true        # If LLM times out, return rule-based only

    # What to check with LLM
    check_plugin_requirements: true
    check_plugin_combinations: true
    check_missing_plugins: true
    check_format_compatibility: true

  # Strictness levels
  strictness:
    unknown_plugin: error
    forbidden_pattern: error
    missing_required_field: warning
    missing_prerequisite: warning    # LLM-detected
    invalid_combination: warning     # LLM-detected
```

---

### Quality Guarantees Summary

| Guarantee | How It's Achieved |
|-----------|-------------------|
| Rule-based results never lost | LLM issues are ADDED, not replaced |
| Graceful degradation | try/except with empty list fallback |
| No false positives from LLM | Confidence threshold filtering (0.7+) |
| No duplicate issues | Deduplication with rule-based priority |
| Performance protected | Timeout + content length limits |
| Configurable | All settings in config/truth.yaml |
| Transparent | Issue source tagged ("rule_based" vs "llm_semantic") |

---

## Implementation Backlog

| Priority | Item | Description | Status |
|----------|------|-------------|--------|
| P0 | Implement Truth+LLM composition (AC-001) | Option 2 as designed | **✅ APPROVED** |
| P0 | Generic Config System (AC-003) | Rules, Profiles, Family Overrides | **✅ APPROVED** |
| P0 | Tiered Validation Flow (AC-005) | Parallel execution, user control | **✅ APPROVED** |
| P1 | Create `config/truth.yaml` | Truth validator + LLM config | **✅ APPROVED** |
| P1 | Create `config/llm.yaml` (AC-004) | LLM validator configuration | **✅ APPROVED** |
| P1 | Create `config/validation_flow.yaml` | Flow control, tiers, dependencies | **✅ APPROVED** |
| P1 | Merge seo.yaml + heading_sizes (AC-002) | Consolidate SEO configs | **✅ APPROVED** |
| P1 | Create `config/frontmatter.yaml` | With generic rules/profiles | **✅ APPROVED** |
| P1 | Create `config/markdown.yaml` | With generic rules/profiles | **✅ APPROVED** |
| P1 | Create `config/code.yaml` | With generic rules/profiles | **✅ APPROVED** |
| P1 | Create `config/links.yaml` | With generic rules/profiles | **✅ APPROVED** |
| P1 | Create `config/structure.yaml` | With generic rules/profiles | **✅ APPROVED** |
| P1 | Create `core/config_loader.py` | Generic config loader for rules/profiles | **✅ APPROVED** |
| P1 | Enhanced Error Reporting (AC-006) | Better issue structure, formats | **✅ APPROVED** |
| P1 | Create `config/cache.yaml` | Caching configuration | **✅ APPROVED** |
| P2 | Performance Optimization (AC-007) | Caching, parallelization | **✅ APPROVED** |

---

## Still To Discuss

All major topics have been addressed:

1. ~~**Config file details for each validator**~~ ✅ Generic system approved (AC-003)
2. ~~**PD-001**: Merge heading_sizes.yaml into seo.yaml?~~ ✅ APPROVED (AC-002)
3. ~~**Validation flow changes**~~ ✅ APPROVED (AC-005)
4. ~~**Error handling and reporting**~~ ✅ APPROVED (AC-006)
5. ~~**Performance optimization**~~ ✅ APPROVED (AC-007)

**All design discussions complete. Ready for implementation.**

---

## Configuration Proposals

Detailed configuration structures proposed for each validator. These need review/approval.

### 1. YAML Validation - `config/frontmatter.yaml`

```yaml
frontmatter:
  enabled: true

  required_fields:
    - title

  optional_fields:
    - description
    - date
    - author
    - tags
    - categories

  field_types:
    title: string
    description: string
    date: date           # YYYY-MM-DD format
    tags: list
    categories: list

  field_lengths:
    title:
      min: 5
      max: 100
    description:
      min: 50
      max: 300

  date_format: "%Y-%m-%d"
  allow_extra_fields: true

  strictness:
    missing_required: error
    invalid_type: error
    empty_field: warning
    length_violation: warning
```

### 2. Markdown Validation - `config/markdown.yaml`

```yaml
markdown:
  enabled: true

  code_blocks:
    check_unclosed: true
    require_language: false

  links:
    check_empty_text: true
    check_empty_url: true

  images:
    require_alt_text: true

  whitespace:
    check_trailing: true
    check_consecutive_blanks: true
    max_consecutive_blank_lines: 2

  strictness:
    unclosed_code_block: error
    empty_link_url: error
    missing_alt_text: warning
    trailing_whitespace: info
```

### 3. Code Validation - `config/code.yaml`

```yaml
code:
  enabled: true

  blocks:
    require_language: true
    allowed_languages: []    # Empty = all allowed
    min_lines: 1
    max_lines: 100
    check_hardcoded_paths: true
    hardcoded_path_patterns:
      - 'C:\\'
      - '/home/'
      - '/Users/'

  inline:
    max_length: 80
    warn_long_inline: true

  strictness:
    no_language: warning
    empty_block: warning
    too_long: info
    hardcoded_path: warning

  # Note: GIST handling is separate (future gist_validator)
```

### 4. Links Validation - `config/links.yaml`

```yaml
links:
  enabled: true

  schemes:
    allowed: [http, https, mailto, ftp, tel]
    allow_relative: true
    allow_anchors: true

  content_checks:
    check_empty_url: true
    check_localhost: true
    check_placeholder: true
    placeholder_patterns:
      - '#$'
      - 'TODO'
      - 'FIXME'
      - 'example.com'

  domains:
    blocked: [localhost, 127.0.0.1]

  security:
    prefer_https: true
    require_https: false

  live_check:
    enabled: false           # Disabled by default (slow)
    timeout_seconds: 5

  strictness:
    empty_url: error
    localhost: warning
    placeholder: warning
    http_not_https: info
```

### 5. Structure Validation - `config/structure.yaml`

```yaml
structure:
  enabled: true

  length:
    min_characters: 100
    max_characters: 50000
    min_words: 50

  headings:
    require_headings: true
    max_h1_count: 1

  sections:
    min_content_lines: 2
    check_empty_sections: true
    check_consecutive_headings: true

  preamble:
    max_length: 200

  strictness:
    too_short: warning
    too_long: info
    no_headings: warning
    empty_section: warning
```

### 6. SEO Validation - `config/seo.yaml` (merged with heading_sizes)

```yaml
seo:
  enabled: true

  h1:
    required: true
    unique: true
    must_be_first: true

  hierarchy:
    enforce: true
    max_depth: 6
    allow_empty_headings: false

  # Merged from heading_sizes.yaml
  heading_sizes:
    h1: { min: 20, max: 70, recommended_min: 30, recommended_max: 60 }
    h2: { min: 10, max: 100, recommended_min: 20, recommended_max: 80 }
    h3: { min: 5, max: 100, recommended_min: 15, recommended_max: 70 }
    h4: { min: 5, max: 80, recommended_min: 10, recommended_max: 60 }
    h5: { min: 3, max: 70, recommended_min: 8, recommended_max: 50 }
    h6: { min: 3, max: 60, recommended_min: 8, recommended_max: 40 }

  strictness:
    h1_violations: error
    hierarchy_skip: error
    empty_heading: warning
    heading_below_min: error
    heading_above_max: warning
```

### 7. LLM Validation - `config/llm.yaml`

```yaml
llm:
  enabled: true

  connection:
    base_url: "http://localhost:11434"
    model: "mistral"
    timeout_seconds: 60

  model_params:
    temperature: 0.1
    top_p: 0.9
    num_predict: 2000

  content:
    max_excerpt_length: 2000

  confidence:
    min_plugin_confidence: 0.7
    min_issue_confidence: 0.8

  fallback:
    on_unavailable: skip
    on_timeout: skip
```

---

## Notes

- This document is updated during discussions
- All approved changes should be implemented and tracked
- Config files follow the pattern: `config/{validator_name}.yaml`
- Use [AC-XXX] for approved changes, [PD-XXX] for pending decisions
