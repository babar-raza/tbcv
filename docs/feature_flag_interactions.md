# Feature Flag Interactions and Dependencies

This document describes the feature flags in TBCV, their interactions, dependencies, and conflict resolution rules.

## Overview

TBCV has 100+ configuration flags organized into logical groups:

- **Validators** (7 flags): seo, yaml, markdown, code, links, structure, truth
- **Agents** (5 flags): fuzzy_detector, content_validator, content_enhancer, orchestrator, truth_manager
- **Cache** (12 flags): l1 settings (enabled, max_entries, memory, ttl, cleanup, eviction) + l2 settings (enabled, path, size, cleanup, compression)
- **Validation** (6+ flags): mode (two_stage/heuristic_only/llm_only), llm_thresholds (downgrade, confirm, upgrade)
- **LLM** (15+ flags): enabled, model settings, retry policy, rules, parsing, profiles, family_overrides
- **Performance** (7+ flags): worker pool, max concurrent, memory/cpu limits, file sizes, response targets
- **System** (8 flags): name, version, environment, debug, log_level, timezone, data/temp directories

## Flag Conflicts

### Critical Conflicts (Must Be Resolved)

#### 1. LLM-Only Validation Without LLM Enabled

**Conflict:**
```yaml
validation.mode: "llm_only"
llm.enabled: false
```

**Issue:** Cannot run LLM-only validation when LLM is disabled.

**Resolution:** Either:
- Enable LLM: `llm.enabled: true`
- Switch mode: `validation.mode: "heuristic_only"`

**Default Priority:** Mode takes precedence. If `llm_only` mode is set, LLM will be automatically enabled if available.

---

#### 2. LLM-Only Validation Without Truth Validator

**Conflict:**
```yaml
validation.mode: "llm_only"
validators.truth.enabled: false
```

**Issue:** LLM validation benefits from truth context. Without truth validator, context quality decreases.

**Resolution:** Either:
- Enable truth validator: `validators.truth.enabled: true`
- Switch mode: `validation.mode: "two_stage"` (includes heuristics)
- Use mode: `validation.mode: "heuristic_only"` (completely different approach)

**Default Priority:** Truth validator is recommended but optional. Heuristic-only mode bypasses this.

---

#### 3. Both Cache Levels Disabled

**Conflict:**
```yaml
cache.l1.enabled: false
cache.l2.enabled: false
```

**Issue:** No caching at all = severe performance degradation.

**Resolution:** Enable at least one:
- L1 (fast, in-memory): Good for high-frequency access
- L2 (persistent, disk): Good for data that survives restarts
- Both (recommended): Hybrid approach with best performance

**Default Priority:** At least L1 should be enabled. L1 is faster but L2 is more durable.

---

#### 4. Content Enhancer Without Orchestrator

**Conflict:**
```yaml
agents.content_enhancer.enabled: true
orchestrator.enabled: false
```

**Issue:** Content enhancer requires orchestrator for workflow coordination.

**Resolution:** Either:
- Enable orchestrator: `orchestrator.enabled: true`
- Disable enhancer: `agents.content_enhancer.enabled: false`

**Default Priority:** Orchestrator enables all agents. Disabling it disables dependent features.

---

### Threshold Conflicts

#### 5. Invalid Threshold Ordering

**Conflict:**
```yaml
validation.llm_thresholds:
  downgrade_threshold: 0.7
  confirm_threshold: 0.5
  upgrade_threshold: 0.3
```

**Issue:** Thresholds must be ordered: `downgrade < confirm < upgrade`

**Valid Range Example:**
```yaml
validation.llm_thresholds:
  downgrade_threshold: 0.2  # Issues below this are downgraded
  confirm_threshold: 0.5    # Issues between thresholds are confirmed
  upgrade_threshold: 0.8    # Issues above this are escalated
```

**Resolution:** Set thresholds in correct order (all between 0.0 and 1.0).

**Default Priority:** Thresholds are validated at startup.

---

#### 6. Very High Fuzzy Threshold + Strict Truth Mode

**Conflict:**
```yaml
agents.fuzzy_detector.similarity_threshold: 0.99
agents.truth_manager.validation_strict: true
```

**Issue:** Very high threshold (99%) means very few patterns match. Combined with strict truth validation, almost no issues detected.

**Resolution:**
- For high sensitivity: lower threshold to 0.70-0.85
- For strict mode: pair with lower threshold (0.60-0.75)
- For high threshold: use relaxed truth mode

**Recommended Combinations:**
- High threshold (0.95+) + relaxed truth mode
- Low threshold (0.70-0.80) + strict truth mode

---

### Resource Conflicts

#### 7. Max Concurrent Workflows > Worker Pool * 10

**Conflict:**
```yaml
performance.max_concurrent_workflows: 100
performance.worker_pool_size: 2
```

**Issue:** Worker pool too small to handle max concurrent workflows.

**Rule:** `worker_pool_size >= max_concurrent_workflows / 10`

**Resolution:** Either:
- Reduce max workflows: `max_concurrent_workflows: 20`
- Increase workers: `worker_pool_size: 16`

**Default Priority:** Worker pool size limits actual concurrency. Settings above this limit are capped.

---

## Flag Dependencies

### Dependency Chain 1: Content Enhancement Pipeline

```
orchestrator.enabled = true
  ├─ content_enhancer.enabled → requires this
  ├─ fuzzy_detector.enabled → used for pattern detection
  ├─ content_validator.enabled → validates enhanced content
  └─ truth_manager.enabled → provides truth data for enhancement
```

**Requirement:** If content enhancement is needed, orchestrator must be enabled and at least one validator must be active.

---

### Dependency Chain 2: Two-Stage Validation

```
validation.mode = "two_stage"
  ├─ llm.enabled = true → required
  ├─ validators.*.enabled → at least one must be true
  └─ llm.rules.* → at least one rule must be enabled
```

**Requirement:** LLM must be available and at least one heuristic validator must be enabled.

---

### Dependency Chain 3: LLM-Only Validation

```
validation.mode = "llm_only"
  ├─ llm.enabled = true → required
  ├─ llm.rules.* → at least one rule must be enabled
  └─ validators.truth.enabled = true → recommended
```

**Requirement:** LLM must be enabled. Truth validator is recommended for context.

---

### Dependency Chain 4: Heuristic-Only Validation

```
validation.mode = "heuristic_only"
  └─ validators.*.enabled → at least one must be true
```

**Requirement:** At least one validator must be enabled.

---

### Dependency Chain 5: Cache L2 Compression

```
cache.l2.compression_enabled = true
  └─ cache.l2.enabled = true → required
```

**Requirement:** L2 cache must be enabled to use compression.

---

### Dependency Chain 6: Truth Manager Strict Mode

```
agents.truth_manager.validation_strict = true
  ├─ agents.truth_manager.enabled = true → required
  └─ validators.truth.enabled = true → recommended
```

**Requirement:** Truth manager must be enabled for strict validation.

---

## Flag Priority and Inheritance

### Priority Levels (Highest to Lowest)

1. **Explicit Overrides** (command-line arguments, environment variables)
2. **Profile Overrides** (strict, default, relaxed profiles)
3. **Family Overrides** (words, pdf, cells families)
4. **Environment-Specific Configs** (production, staging, development)
5. **Base Configuration** (main.yaml defaults)

### Example: Threshold Override Chain

```yaml
# Level 5: Base default
llm.rules.detect_missing_plugins.confidence_threshold: 0.7

# Level 4: Environment override (production.yaml)
llm.rules.detect_missing_plugins.confidence_threshold: 0.75

# Level 3: Family override (words family)
llm.family_overrides.words.rules.detect_missing_plugins.confidence_threshold: 0.6

# Level 2: Profile override (strict profile)
llm.profiles.strict.overrides.detect_missing_plugins.confidence_threshold: 0.5

# Level 1: Runtime override (env var: TBCV_LLM__RULES__DETECT_MISSING_PLUGINS__CONFIDENCE_THRESHOLD=0.4)
# Final effective value: 0.4
```

---

## Validation Rules

### Range Validation

| Flag | Min | Max | Default | Unit |
|------|-----|-----|---------|------|
| `validation.llm_thresholds.*` | 0.0 | 1.0 | varies | ratio |
| `fuzzy_detector.similarity_threshold` | 0.0 | 1.0 | 0.85 | ratio |
| `performance.cpu_limit_percent` | 0 | 100 | 80 | % |
| `content_enhancer.rewrite_ratio_threshold` | 0.0 | 1.0 | 0.5 | ratio |
| `server.port` | 1 | 65535 | 8080 | port number |

### List Validation

| Flag | Min Length | Max Length | Requirement |
|------|-----------|-----------|-------------|
| `fuzzy_detector.fuzzy_algorithms` | 1 | unlimited | At least one algorithm |
| `content_validator.markdown_extensions` | 0 | unlimited | Optional |
| `workflow_types` | 1 | unlimited | At least one type |
| `workflow_checkpoints` | 1 | unlimited | At least one checkpoint |
| `validators` | 0 | 7 | Optional (but at least 1 for validation) |

### String Validation

| Flag | Valid Values | Default |
|------|--------------|---------|
| `system.environment` | development, staging, production | development |
| `validation.mode` | two_stage, heuristic_only, llm_only | two_stage |
| `system.log_level` | debug, info, warning, error, critical | info |
| `database_url` | sqlite://*, postgresql://*, mysql://* | sqlite:///./data/tbcv.db |

---

## Edge Cases and Boundaries

### All Validators Disabled

**Configuration:**
```yaml
validators:
  seo.enabled: false
  yaml.enabled: false
  markdown.enabled: false
  code.enabled: false
  links.enabled: false
  structure.enabled: false
  truth.enabled: false
```

**Result:** No validation occurs. Files pass through untouched.

**Use Cases:**
- Testing enhancement-only workflows
- Using TBCV as enhancement engine without validation

---

### All Agents Disabled

**Configuration:**
```yaml
agents:
  fuzzy_detector.enabled: false
  content_validator.enabled: false
  content_enhancer.enabled: false
  orchestrator.enabled: false
  truth_manager.enabled: false
```

**Result:** No processing occurs. System cannot run workflows.

**Use Cases:** None recommended. At least orchestrator and one validator are needed.

---

### Minimum Cache Settings

**Configuration:**
```yaml
cache:
  l1:
    enabled: true
    max_entries: 1
    max_memory_mb: 1
    ttl_seconds: 1
  l2:
    enabled: false
```

**Result:** Cache operates but with minimal capacity.

**Use Cases:** Extreme resource constraints, testing purposes.

---

### Maximum Concurrency Settings

**Configuration:**
```yaml
performance:
  max_concurrent_workflows: 1000
  worker_pool_size: 128
```

**Result:** System can handle high-throughput scenarios.

**Use Cases:** High-traffic production environments with sufficient resources.

---

## Recommended Flag Combinations

### Production - Standard

```yaml
system.environment: "production"
system.debug: false
validation.mode: "two_stage"
llm.enabled: true
validators: all enabled
cache.l1.enabled: true
cache.l2.enabled: true
cache.l2.compression_enabled: true
performance.worker_pool_size: 8
performance.max_concurrent_workflows: 100
```

**Characteristics:**
- Balanced performance and accuracy
- Both heuristic and LLM validation
- Full caching with compression
- Moderate resource usage

---

### Production - High Performance

```yaml
system.environment: "production"
system.debug: false
validation.mode: "heuristic_only"
llm.enabled: false
validators: all enabled
cache.l1.enabled: true
cache.l2.enabled: true
cache.l1.ttl_seconds: 7200
cache.l2.compression_enabled: true
performance.worker_pool_size: 16
performance.max_concurrent_workflows: 500
```

**Characteristics:**
- Fastest throughput
- Heuristic-only validation (no LLM overhead)
- Aggressive caching
- High resource usage

---

### Production - Strict Quality

```yaml
system.environment: "production"
system.debug: false
validation.mode: "two_stage"
llm.enabled: true
content_validator.yaml_strict_mode: true
truth_manager.validation_strict: true
validators: all enabled
cache.l1.enabled: true
cache.l2.enabled: true
performance.worker_pool_size: 4
performance.max_concurrent_workflows: 50
validation.llm_thresholds.upgrade_threshold: 0.9
```

**Characteristics:**
- Maximum quality assurance
- Strict validation rules
- Moderate throughput
- Comprehensive validation

---

### Development

```yaml
system.environment: "development"
system.debug: true
system.log_level: "debug"
validation.mode: "heuristic_only"
llm.enabled: false
validators: all enabled
cache.l1.enabled: true
cache.l2.enabled: false
performance.worker_pool_size: 2
performance.max_concurrent_workflows: 10
```

**Characteristics:**
- Fast iteration
- Minimal caching
- Verbose logging
- No LLM overhead

---

### Testing

```yaml
system.environment: "development"
system.debug: true
validation.mode: "heuristic_only"
llm.enabled: false
validators.seo.enabled: true
validators.truth.enabled: true
validators.code.enabled: true
cache.l1.enabled: true
cache.l2.enabled: false
performance.worker_pool_size: 1
performance.max_concurrent_workflows: 1
```

**Characteristics:**
- Single-threaded for predictable behavior
- Minimal caching
- Selected validators
- Full debugging

---

## Testing Feature Flag Combinations

See `tests/config/test_feature_flag_combinations.py` for comprehensive tests covering:

- **Valid Combinations** (7 tests): Production-ready configurations
- **Conflicting Combinations** (7 tests): Invalid flag pairings
- **Priority & Inheritance** (6 tests): Override behavior
- **Validation** (8 tests): Constraint checking
- **Edge Cases** (10 tests): Boundary conditions
- **Complex Scenarios** (4 tests): Real-world situations
- **Documentation** (4 tests): Flag documentation
- **Combination Matrices** (4 tests): Systematic coverage
- **Integration** (3 tests): Full configuration loading
- **Performance** (2 tests): Validation speed

Total: **55 comprehensive tests** ensuring all edge cases are handled.

---

## Configuration File Locations

- **Main Configuration:** `config/main.yaml`
- **Environment Overrides:** `config/environments/{environment}.yaml`
- **LLM Configuration:** `config/llm.yaml`
- **Cache Configuration:** `config/cache.yaml`
- **Validator Configurations:** `config/{validator}.yaml`

---

## Version History

### v1.0 (Initial)
- Documented 100+ feature flags
- Defined 7 major conflicts
- Documented 6 dependency chains
- Added 5 recommended combinations

---
