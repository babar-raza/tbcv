# Parallel Execution Pattern Implementation

## Overview

TBCV implements a **Tiered Parallel Execution** pattern for content validation. This pattern enables efficient validation by running independent validators concurrently within tiers while maintaining dependency ordering between tiers.

## Architecture

```
                    ┌─────────────────┐
                    │     ROUTER      │
                    │  (file type →   │
                    │   validators)   │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
   ┌─────────┐         ┌─────────┐         ┌─────────┐
   │ TIER 1  │         │ TIER 2  │         │ TIER 3  │
   │(parallel)│   ──►  │(parallel)│   ──►  │(sequential)│
   │ yaml    │         │ code    │         │ fuzzy   │
   │ markdown│         │ links   │         │ truth   │
   │ structure         │ seo     │         │ llm     │
   └─────────┘         └─────────┘         └─────────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
                    ┌────────▼────────┐
                    │   AGGREGATOR    │
                    │  (merge results)│
                    └─────────────────┘
```

## Key Components

### ValidatorRouter (`core/validator_router.py`)

The main orchestrator for tiered validation:

```python
class ValidatorRouter:
    async def execute(self, content: str, context: Dict) -> FlowResult:
        """Execute full tiered validation flow."""
        for tier_key in ["tier1", "tier2", "tier3"]:
            tier_result = await self._execute_tier(...)
            if tier_result.terminated_early:
                break
        return flow_result

    async def _execute_tier(self, tier_key: str, ...) -> TierResult:
        """Execute validators in parallel within a tier."""
        if parallel:
            results = await asyncio.gather(*tasks)
        else:
            # Sequential with dependency ordering
            for validator in ready_validators:
                result = await self._execute_validator(...)
```

### Configuration (`config/validation_flow.yaml`)

Tiers and validators are fully configurable:

```yaml
tiers:
  tier1:
    name: "Quick Checks"
    parallel: true
    validators:
      - yaml
      - markdown
      - structure

  tier2:
    name: "Content Analysis"
    parallel: true
    validators:
      - code
      - links
      - seo

  tier3:
    name: "Advanced Validation"
    parallel: false  # Sequential due to dependencies
    validators:
      - FuzzyLogic
      - Truth
      - llm

dependencies:
  Truth:
    - FuzzyLogic  # Truth must wait for FuzzyLogic
  llm:
    - Truth
```

## Features

### 1. Tiered Execution

Validators are grouped into tiers that execute sequentially:

| Tier | Name | Validators | Parallel | Purpose |
|------|------|------------|----------|---------|
| 1 | Quick Checks | yaml, markdown, structure | Yes | Fast rule-based checks |
| 2 | Content Analysis | code, links, seo | Yes | Deeper content analysis |
| 3 | Advanced | FuzzyLogic, Truth, llm | No | Semantic validation |

### 2. Parallel Execution Within Tiers

Validators in the same tier with no dependencies run concurrently:

```python
# All tier 1 validators run in parallel
tasks = [
    self._execute_validator("yaml", content, context),
    self._execute_validator("markdown", content, context),
    self._execute_validator("structure", content, context)
]
results = await asyncio.gather(*tasks)
```

### 3. Dependency Resolution

Tier 3 respects validator dependencies:

```python
# FuzzyLogic runs first, then Truth (which depends on FuzzyLogic), then llm
while pending:
    ready = [v for v in pending if self._check_dependencies_met(v, completed)]
    for v in ready:
        await self._execute_validator(v, content, context)
        completed.add(v)
```

### 4. Early Termination

Validation stops early when critical error threshold is reached:

```yaml
settings:
  early_termination_on_critical: true
  max_critical_errors: 3
```

```python
if tier_result.critical_count >= max_critical:
    flow_result.terminated_early = True
    flow_result.termination_reason = f"Critical errors in {tier_key}"
    break
```

### 5. Timeout Handling

Each validator has configurable timeouts:

```yaml
settings:
  validator_timeout: 60  # seconds
  tier_timeout: 180

tiers:
  tier1:
    settings:
      timeout: 30  # Override for fast tier
```

```python
result = await asyncio.wait_for(
    agent.validate(content, context),
    timeout=timeout
)
```

### 6. Profile-Based Configuration

Different validation profiles for different use cases:

```yaml
profiles:
  strict:
    settings:
      max_critical_errors: 1
    validators:
      llm:
        enabled: true

  quick:
    validators:
      yaml:
        enabled: true
      markdown:
        enabled: true
      code:
        enabled: false
      links:
        enabled: false
```

### 7. Family-Specific Overrides

Product families can customize validation:

```yaml
family_overrides:
  words:
    profile: "strict"
    validators:
      Truth:
        enabled: true
      llm:
        enabled: true

  pdf:
    validators:
      code:
        enabled: false  # PDF docs rarely have code
```

## Data Flow

### FlowResult

Complete validation flow result:

```python
@dataclass
class FlowResult:
    tiers_executed: List[TierResult]
    validation_results: Dict[str, Any]  # validator_id -> result
    routing_info: Dict[str, str]        # validator_id -> "tiered_execution" | "skipped"
    total_critical: int
    total_errors: int
    total_warnings: int
    terminated_early: bool
    termination_reason: str
    total_duration_ms: float
```

### TierResult

Result from a single tier:

```python
@dataclass
class TierResult:
    tier_name: str
    tier_number: int
    validators_run: List[str]
    results: Dict[str, Any]
    errors: List[Dict[str, Any]]
    critical_count: int
    error_count: int
    warning_count: int
    duration_ms: float
    terminated_early: bool
```

## Usage

### Basic Execution

```python
from core.validator_router import ValidatorRouter
from agents.base import agent_registry

router = ValidatorRouter(agent_registry)
result = await router.execute(
    content="# My Document\n\nContent here...",
    context={"file_path": "doc.md", "family": "words"}
)

print(f"Executed {len(result.tiers_executed)} tiers")
print(f"Total errors: {result.total_errors}")
```

### With User Selection

```python
result = await router.execute(
    content=content,
    context=context,
    user_selection=["yaml", "markdown", "links"]  # Only these validators
)
```

### With Profile

```python
result = await router.execute(
    content=content,
    context=context,
    profile="quick"  # Use quick profile
)
```

## Performance Characteristics

| Metric | Value | Notes |
|--------|-------|-------|
| Tier 1 parallelism | 3 validators | ~100ms total for 3x100ms validators |
| Tier 2 parallelism | 3-4 validators | Link checking may be slower |
| Tier 3 sequential | 3 validators | Dependencies require ordering |
| Early termination | Configurable | Default: 3 critical errors |
| Timeout per validator | 60s default | Configurable per tier |

## Testing

Comprehensive tests in `tests/core/test_validator_router.py`:

```bash
# Run all router tests
pytest tests/core/test_validator_router.py -v

# Run specific test classes
pytest tests/core/test_validator_router.py::TestParallelExecution -v
pytest tests/core/test_validator_router.py::TestEarlyTermination -v
pytest tests/core/test_validator_router.py::TestDependencyExecution -v
```

## Configuration Reference

See `config/validation_flow.yaml` for complete configuration options.

## Related Documentation

- [Agentic AI Design Patterns](../../plans/design_patterns.md)
- [Validator Development Guide](../development/validators.md)
- [Testing Guide](../testing.md)
