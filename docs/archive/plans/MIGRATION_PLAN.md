# TBCV Validator Migration Plan - Systematic & Seamless

**Date**: 2025-11-22
**Version**: 1.0
**Target**: Production Deployment
**Timeline**: 8-10 Weeks
**Strategy**: Phased Rollout with Backward Compatibility

---

## Table of Contents

1. [Migration Overview](#1-migration-overview)
2. [Week-by-Week Timeline](#2-week-by-week-timeline)
3. [Testing Strategy](#3-testing-strategy)
4. [Deployment Procedures](#4-deployment-procedures)
5. [Rollback Procedures](#5-rollback-procedures)
6. [Validation Checklist](#6-validation-checklist)
7. [Team Responsibilities](#7-team-responsibilities)

---

## 1. Migration Overview

### 1.1 Migration Principles

1. **Zero Downtime**: No service interruptions during migration
2. **Backward Compatible**: Old and new systems work side-by-side
3. **Gradual Rollout**: Feature flags control traffic distribution
4. **Easy Rollback**: Multiple rollback points at each phase
5. **Continuous Validation**: Automated tests at every step
6. **Incremental Value**: Each week delivers usable features

### 1.2 Migration Phases

```
Phase 0: Preparation (Week 0)
├─ Environment setup
├─ Feature flag infrastructure
└─ Testing framework

Phase 1: Foundation (Week 1-2)
├─ BaseValidatorAgent
├─ ValidatorRouter
├─ SeoValidatorAgent (proof of concept)
└─ Backward compatibility layer

Phase 2: Core Migration (Week 3-6)
├─ YamlValidatorAgent
├─ MarkdownValidatorAgent
├─ CodeValidatorAgent
├─ LinkValidatorAgent
├─ StructureValidatorAgent
├─ TruthValidatorAgent
└─ Gradual traffic shift (10% → 100%)

Phase 3: Stabilization (Week 7-8)
├─ Monitor production metrics
├─ Fix issues
├─ Documentation updates
└─ Deprecation warnings

Phase 4: Cleanup (Week 9-10+)
├─ Remove legacy code (optional)
├─ Final performance tuning
└─ Future validator template
```

---

## 2. Week-by-Week Timeline

### Week 0: Preparation

**Objectives**:
- Set up infrastructure for phased rollout
- Establish testing baseline
- No code changes to production

**Tasks**:

#### Day 1-2: Feature Flag Infrastructure
```yaml
# config/features.yaml (NEW FILE)
features:
  new_validator_architecture:
    enabled: false  # Start disabled
    rollout_percentage: 0
    validators:
      yaml: 0
      markdown: 0
      code: 0
      links: 0
      structure: 0
      truth: 0
      seo: 0
      heading_sizes: 0
```

```python
# core/feature_flags.py (NEW FILE)
class FeatureFlags:
    """Centralized feature flag management."""

    def __init__(self):
        self.config = self._load_config()

    def is_enabled(self, feature: str) -> bool:
        """Check if feature is enabled."""
        import random
        feature_config = self.config.get(feature, {})
        enabled = feature_config.get("enabled", False)
        percentage = feature_config.get("rollout_percentage", 0)

        return enabled and random.randint(0, 100) < percentage

    def is_validator_enabled(self, validator_type: str) -> bool:
        """Check if specific validator should use new architecture."""
        if not self.is_enabled("new_validator_architecture"):
            return False

        validators = self.config["new_validator_architecture"].get("validators", {})
        percentage = validators.get(validator_type, 0)

        import random
        return random.randint(0, 100) < percentage

feature_flags = FeatureFlags()
```

#### Day 3-4: Testing Framework
```bash
# Create test structure
tests/validators/
├── __init__.py
├── test_base_validator.py
├── test_yaml_validator.py
├── test_seo_validator.py
├── test_validator_router.py
└── fixtures/
    ├── sample_valid.md
    ├── sample_invalid_yaml.md
    └── sample_seo_issues.md
```

```python
# tests/validators/test_base_validator.py
import pytest
from agents.validators.base_validator import BaseValidatorAgent, ValidationResult

class MockValidator(BaseValidatorAgent):
    def get_validation_type(self) -> str:
        return "mock"

    async def validate(self, content: str, context: dict) -> ValidationResult:
        return ValidationResult(confidence=1.0, issues=[], metrics={})

def test_base_validator_interface():
    validator = MockValidator()
    assert validator.get_validation_type() == "mock"
    # ... more tests
```

#### Day 5: Baseline Metrics
```bash
# Run current system metrics
python -m pytest --cov=agents/content_validator tests/ -v

# Capture baseline:
# - Test coverage: X%
# - Performance: Avg Y ms per validation
# - Memory: Z MB
```

**Deliverables**:
- ✅ Feature flag config created
- ✅ Feature flag code implemented
- ✅ Test framework set up
- ✅ Baseline metrics captured
- ✅ Team trained on feature flags

**Success Criteria**:
- All existing tests pass
- Feature flags work (tested manually)
- Baseline documented

---

### Week 1: Foundation Implementation

**Objectives**:
- Create base infrastructure
- Implement first validator (SEO)
- No production traffic yet

**Tasks**:

#### Day 1-2: BaseValidatorAgent
```python
# agents/validators/base_validator.py (190 lines)
# - ValidationIssue dataclass
# - ValidationResult dataclass
# - BaseValidatorAgent abstract class
# - Common utilities (_load_config, _extract_metadata, etc.)

# See IMPLEMENTATION_PLAN_NEW_AGENTS.md for full code
```

**Tests**:
```python
# tests/validators/test_base_validator.py
def test_validation_issue_creation():
    issue = ValidationIssue(
        level="error",
        category="test",
        message="Test message"
    )
    assert issue.level == "error"
    assert issue.to_dict()["category"] == "test"

def test_validation_result_aggregation():
    result = ValidationResult(
        confidence=0.8,
        issues=[...],
        metrics={"count": 5}
    )
    assert result.confidence == 0.8
```

#### Day 3-5: SeoValidatorAgent
```python
# agents/validators/seo_validator.py (400 lines)
# - Load SEO config
# - Load heading sizes config
# - Validate SEO headings
# - Validate heading sizes
# - Extract headings helper

# See IMPLEMENTATION_PLAN_NEW_AGENTS.md for full code
```

**Tests**:
```python
# tests/validators/test_seo_validator.py
@pytest.mark.asyncio
async def test_seo_missing_h1():
    validator = SeoValidatorAgent()
    content = "## H2 only\nNo H1"
    result = await validator.validate(content, {})

    assert any(i.category == "seo_h1_missing" for i in result.issues)
    assert result.confidence < 1.0

@pytest.mark.asyncio
async def test_heading_sizes_too_short():
    validator = SeoValidatorAgent()
    content = "# H1\nShort title"
    result = await validator.validate(content, {"validation_type": "heading_sizes"})

    assert any(i.category == "heading_too_short" for i in result.issues)
```

**Deliverables**:
- ✅ BaseValidatorAgent implemented
- ✅ SeoValidatorAgent implemented
- ✅ Unit tests passing (>90% coverage)
- ✅ Documentation updated
- ✅ Code reviewed

**Success Criteria**:
- All tests pass
- Code review approved
- Can instantiate validators
- No production impact (not deployed yet)

---

### Week 2: Routing Layer

**Objectives**:
- Implement ValidatorRouter
- Connect to orchestrator
- Still no production traffic

**Tasks**:

#### Day 1-3: ValidatorRouter
```python
# agents/validators/router.py (NEW FILE, 300 lines)

class ValidatorRouter:
    """Routes validation requests to appropriate validators."""

    def __init__(self, agent_registry, feature_flags):
        self.agent_registry = agent_registry
        self.feature_flags = feature_flags
        self._build_validator_map()

    def _build_validator_map(self) -> Dict[str, str]:
        """Map validation types to agent IDs."""
        return {
            "yaml": "yaml_validator",
            "markdown": "markdown_validator",
            "code": "code_validator",
            "links": "link_validator",
            "structure": "structure_validator",
            "Truth": "truth_validator",
            "seo": "seo_validator",
            "heading_sizes": "seo_validator",
            "FuzzyLogic": "fuzzy_detector",
            "llm": "llm_validator",
        }

    async def execute(
        self,
        validation_types: List[str],
        content: str,
        context: Dict[str, Any],
        ui_override: bool = False
    ) -> Dict[str, Any]:
        """Execute validations with routing logic."""
        results = {}
        all_issues = []

        for vt in validation_types:
            # Check if should use new validator
            use_new = (
                self.feature_flags.is_validator_enabled(vt) or
                ui_override  # UI always tries new first
            )

            if use_new:
                result = await self._try_new_validator(vt, content, context)
            else:
                result = await self._use_legacy_validator(vt, content, context)

            results[f"{vt}_validation"] = result
            all_issues.extend(result.get("issues", []))

        return {
            "validation_results": results,
            "issues": all_issues,
            "validators_used": self._get_validators_used(results),
            "routing_info": self._get_routing_info(validation_types)
        }

    async def _try_new_validator(self, vt: str, content: str, context: dict):
        """Try new validator, fallback to legacy if unavailable."""
        agent_id = self._validator_map.get(vt)
        validator = self.agent_registry.get_agent(agent_id)

        if validator:
            try:
                return await self._execute_validator(validator, vt, content, context)
            except Exception as e:
                logger.error(f"New validator {vt} failed: {e}")
                # Fallback to legacy
                return await self._use_legacy_validator(vt, content, context)
        else:
            # New validator not available, use legacy
            return await self._use_legacy_validator(vt, content, context)

    async def _use_legacy_validator(self, vt: str, content: str, context: dict):
        """Use legacy ContentValidator."""
        legacy = self.agent_registry.get_agent("content_validator")
        if not legacy:
            return self._create_error_result(vt, "No validator available")

        try:
            result = await legacy.process_request("validate_content", {
                "content": content,
                "file_path": context.get("file_path", "unknown"),
                "family": context.get("family", "words"),
                "validation_types": [vt]
            })

            # Mark as legacy
            result["used_legacy"] = True
            return result
        except Exception as e:
            logger.exception(f"Legacy validator failed for {vt}")
            return self._create_error_result(vt, str(e))

    async def _execute_validator(
        self, validator, vt: str, content: str, context: dict
    ):
        """Execute new validator with metrics."""
        import time
        start = time.time()

        try:
            result = await validator.process_request("validate", {
                "content": content,
                "context": {**context, "validation_type": vt}
            })

            result["execution_time_ms"] = (time.time() - start) * 1000
            result["validator_id"] = validator.agent_id
            result["validator_version"] = validator.get_version()
            result["used_legacy"] = False

            return result

        except Exception as e:
            logger.exception(f"Validator {vt} failed")
            return self._create_error_result(vt, str(e))

    def discover_validators(self) -> List[Dict[str, Any]]:
        """Discover available validators for UI."""
        validators = []

        for vt, agent_id in self._validator_map.items():
            agent = self.agent_registry.get_agent(agent_id)

            if agent and hasattr(agent, 'get_validation_type'):
                # New validator
                validators.append({
                    "id": vt,
                    "name": agent.get_display_name(),
                    "description": agent.get_description(),
                    "category": agent.get_category(),
                    "available": True,
                    "version": agent.get_version(),
                    "type": "new"
                })
            else:
                # Might be in legacy
                validators.append({
                    "id": vt,
                    "name": vt.title(),
                    "description": f"Validate {vt}",
                    "category": "standard",
                    "available": True,  # Via legacy
                    "version": "legacy",
                    "type": "legacy"
                })

        return validators
```

**Tests**:
```python
# tests/validators/test_validator_router.py
@pytest.mark.asyncio
async def test_router_uses_new_validator_when_enabled():
    router = ValidatorRouter(agent_registry, feature_flags)
    feature_flags.set("seo", 100)  # 100% new

    result = await router.execute(["seo"], content, context)

    assert result["routing_info"]["seo"] == "new_validator"
    assert not result["validation_results"]["seo_validation"]["used_legacy"]

@pytest.mark.asyncio
async def test_router_falls_back_to_legacy():
    router = ValidatorRouter(agent_registry, feature_flags)
    # SEO validator not registered

    result = await router.execute(["seo"], content, context)

    assert result["validation_results"]["seo_validation"]["used_legacy"]
```

#### Day 4-5: Integration with Orchestrator
```python
# agents/orchestrator.py (MODIFY)

# Add import
from agents.validators.router import ValidatorRouter
from core.feature_flags import feature_flags

class OrchestratorAgent(BaseAgent):
    def __init__(self, agent_id: Optional[str] = None):
        super().__init__(agent_id)
        self._init_concurrency_controls()
        self.validator_router = ValidatorRouter(agent_registry, feature_flags)  # NEW

    async def _run_validation_pipeline(
        self,
        content: str,
        file_path: str,
        family: str,
        validation_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Run validation pipeline with new routing."""
        # ... existing code ...

        # MODIFY: Content validation section
        if effective_mode in {"two_stage", "heuristic_only"}:
            # ... fuzzy detection ...

            # NEW: Use router instead of calling content_validator directly
            ui_override = validation_types is not None
            validation_result = await self.validator_router.execute(
                validation_types=validation_types if validation_types else default_types,
                content=content,
                context={"file_path": file_path, "family": family},
                ui_override=ui_override
            )

            pipeline_result["content_validation"] = validation_result
            heuristics_issues = validation_result.get("issues", [])
            # ... rest of pipeline ...
```

**Deliverables**:
- ✅ ValidatorRouter implemented
- ✅ Integrated with orchestrator
- ✅ Tests passing
- ✅ Backward compatible (uses legacy by default)

**Success Criteria**:
- Router can find validators
- Fallback to legacy works
- All existing tests still pass
- No production impact

---

### Week 3: First Rollout (SEO Validator)

**Objectives**:
- Deploy to production
- Enable SEO validator for 10% traffic
- Monitor metrics

**Tasks**:

#### Day 1: Pre-Deployment
```bash
# Final checks
python -m pytest tests/ -v --cov
python -m pytest tests/validators/ -v --cov

# Build and test in staging
docker build -t tbcv:new-validators .
docker-compose up -d

# Run smoke tests
curl -X POST http://staging:8000/api/validate \
  -d '{"content":"## Test", "validation_types":["seo"]}'
```

#### Day 2: Deploy to Production
```bash
# Deploy (your deployment process)
git tag v2.1.0-beta1
git push origin v2.1.0-beta1

# Deploy using your CI/CD
# OR manual:
systemctl restart tbcv

# Verify deployment
curl http://localhost:8000/health/ready
```

#### Day 3: Enable 10% Traffic
```yaml
# config/features.yaml (in production)
features:
  new_validator_architecture:
    enabled: true  # Enable!
    rollout_percentage: 100  # Always check per-validator
    validators:
      seo: 10  # 10% of SEO validations use new validator
      heading_sizes: 10
      # Others: 0 (use legacy)
```

```bash
# Reload config (or restart)
systemctl reload tbcv
```

#### Day 4-5: Monitor
```bash
# Check logs for errors
tail -f /var/log/tbcv/tbcv.log | grep -i "seo_validator\|error"

# Check metrics
# - Response times
# - Error rates
# - Validation results comparison
```

**Metrics to Monitor**:
```
Metric                      | Baseline | Target  | Actual
----------------------------|----------|---------|--------
SEO Validation Latency (ms) | 45       | < 50    | __
SEO Error Rate (%)          | 0.1      | < 0.5   | __
H1 Missing Detection Rate   | 92%      | > 90%   | __
Memory Usage (MB)           | 250      | < 300   | __
```

**Deliverables**:
- ✅ Deployed to production
- ✅ 10% traffic on new validator
- ✅ No P0/P1 issues
- ✅ Metrics within targets

**Success Criteria**:
- No increase in errors
- Latency acceptable
- Validation results consistent with legacy

**Rollback Trigger**:
- Error rate > 1%
- Latency > 2x baseline
- P0/P1 bug discovered

---

### Week 4-5: Core Validators Implementation

**Objectives**:
- Implement remaining core validators
- Gradual rollout to 50%
- No production issues

**Week 4 Tasks**:

#### YamlValidatorAgent (Day 1-2)
- Implement validator
- Unit tests
- Deploy to production
- 10% rollout

#### MarkdownValidatorAgent (Day 3-4)
- Implement validator
- Unit tests
- Deploy to production
- 10% rollout

#### CodeValidatorAgent (Day 5)
- Implement validator
- Unit tests
- Deploy to production
- 10% rollout

**Week 5 Tasks**:

#### LinkValidatorAgent (Day 1)
- Implement validator
- Unit tests
- Deploy to production
- 10% rollout

#### StructureValidatorAgent (Day 2)
- Implement validator
- Unit tests
- Deploy to production
- 10% rollout

#### TruthValidatorAgent (Day 3)
- Implement validator
- Unit tests
- Deploy to production
- 10% rollout

#### Increase Rollout to 50% (Day 4-5)
```yaml
# config/features.yaml
validators:
  yaml: 50
  markdown: 50
  code: 50
  links: 50
  structure: 50
  truth: 50
  seo: 50
  heading_sizes: 50
```

**Monitor for 48 hours**

**Deliverables**:
- ✅ All 8 validators implemented
- ✅ All tests passing
- ✅ 50% traffic on new validators
- ✅ No degradation

**Success Criteria**:
- Same as Week 3
- All validators stable at 50%

---

### Week 6: Full Rollout

**Objectives**:
- 100% traffic to new validators
- Legacy as fallback only
- Production stable

**Tasks**:

#### Day 1: Increase to 75%
```yaml
validators:
  # All: 75
```
Monitor for 24 hours

#### Day 2: Increase to 90%
```yaml
validators:
  # All: 90
```
Monitor for 24 hours

#### Day 3: Full Rollout (100%)
```yaml
validators:
  yaml: 100
  markdown: 100
  code: 100
  links: 100
  structure: 100
  truth: 100
  seo: 100
  heading_sizes: 100
```

#### Day 4-5: Stabilization
- Monitor all metrics
- Fix any issues
- Ensure legacy fallback still works

**Deliverables**:
- ✅ 100% traffic on new validators
- ✅ All metrics stable
- ✅ Legacy fallback verified
- ✅ No production issues

**Success Criteria**:
- Same validation results as legacy
- No performance regression
- No new bugs

---

### Week 7-8: Deprecation & Documentation

**Objectives**:
- Add deprecation warnings
- Update documentation
- Plan legacy removal

**Tasks**:

#### Deprecation Warnings
```python
# agents/content_validator.py
async def handle_validate_content(self, params: Dict[str, Any]) -> Dict[str, Any]:
    """DEPRECATED: Use individual validator agents instead."""
    logger.warning(
        "ContentValidator.validate_content is deprecated. "
        "Use individual validator agents via ValidatorRouter."
    )
    # ... existing code ...
```

#### Documentation Updates
- Update README.md
- Update API docs
- Update architecture diagrams
- Create migration guide for custom validators

#### UI Updates
```javascript
// Load validators dynamically from API
fetch('/api/validators/available')
  .then(r => r.json())
  .then(data => {
    // Show all available validators
    renderValidatorCheckboxes(data.validators);
  });
```

**Deliverables**:
- ✅ Deprecation warnings added
- ✅ Documentation updated
- ✅ UI shows dynamic validators
- ✅ Migration guide published

---

### Week 9-10: Cleanup (Optional)

**Objectives**:
- Remove legacy code (optional)
- Performance tuning
- Future-ready template

**Tasks**:

#### Remove Legacy Methods (if approved)
```python
# agents/content_validator.py
# Remove or mark private:
# - _validate_yaml()
# - _validate_markdown()
# - _validate_seo()
# - etc.

# Keep only for absolute backward compat
```

#### Performance Tuning
- Parallel execution optimization
- Caching improvements
- Resource usage optimization

#### Template for Future Validators
```python
# agents/validators/TEMPLATE_validator.py
"""
Template for creating new validators.
Copy this file and modify as needed.
"""

from agents.validators.base_validator import BaseValidatorAgent, ValidationResult

class TemplateValidatorAgent(BaseValidatorAgent):
    """Template validator - describe what it validates."""

    def __init__(self, agent_id: Optional[str] = None):
        super().__init__(agent_id or "template_validator")
        # Load config if needed
        # self.config = self._load_config("config/template.yaml")

    def get_validation_type(self) -> str:
        return "template"

    def get_display_name(self) -> str:
        return "Template Validator"

    def get_description(self) -> str:
        return "Validates template content"

    def get_category(self) -> str:
        return "standard"  # or "advanced", "experimental"

    async def validate(
        self, content: str, context: Dict[str, Any]
    ) -> ValidationResult:
        """Validate content."""
        issues = []

        # TODO: Implement validation logic

        return ValidationResult(
            confidence=1.0,
            issues=issues,
            metrics={"items_checked": 0}
        )
```

**Deliverables**:
- ✅ Legacy code removed (optional)
- ✅ Performance optimized
- ✅ Template created
- ✅ System production-ready

---

## 3. Testing Strategy

### 3.1 Unit Tests

**Coverage Target**: > 90%

```bash
# Run unit tests
python -m pytest tests/validators/ -v --cov --cov-report=html

# Coverage by component:
# - BaseValidatorAgent: 95%+
# - Each validator: 90%+
# - ValidatorRouter: 95%+
```

**Test Cases Per Validator**:
```python
# tests/validators/test_{validator}_validator.py

@pytest.mark.asyncio
async def test_valid_content():
    """Test with valid content - should pass."""
    pass

@pytest.mark.asyncio
async def test_invalid_content():
    """Test with invalid content - should fail with issues."""
    pass

@pytest.mark.asyncio
async def test_edge_cases():
    """Test edge cases (empty, very long, special chars)."""
    pass

@pytest.mark.asyncio
async def test_performance():
    """Test performance - should complete in < 100ms."""
    pass

@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling - should not crash."""
    pass
```

### 3.2 Integration Tests

```python
# tests/integration/test_validator_pipeline.py

@pytest.mark.asyncio
async def test_full_validation_pipeline():
    """Test end-to-end validation through orchestrator."""
    content = read_fixture("sample.md")

    result = await orchestrator.process_request("validate_file", {
        "file_path": "test.md",
        "family": "words",
        "validation_types": ["yaml", "markdown", "seo"]
    })

    assert "validation_results" in result
    assert "yaml_validation" in result["validation_results"]
    assert "seo_validation" in result["validation_results"]

@pytest.mark.asyncio
async def test_fallback_to_legacy():
    """Test fallback when new validator unavailable."""
    # Unregister new validator
    agent_registry.unregister("seo_validator")

    result = await orchestrator.validate(content, ["seo"])

    assert result["seo_validation"]["used_legacy"] is True
```

### 3.3 Load Tests

```python
# tests/performance/test_load.py
import asyncio

@pytest.mark.asyncio
async def test_concurrent_validations():
    """Test 100 concurrent validations."""
    tasks = [
        orchestrator.validate(content, ["yaml", "markdown"])
        for _ in range(100)
    ]

    results = await asyncio.gather(*tasks)

    assert len(results) == 100
    assert all(r["status"] == "success" for r in results)

@pytest.mark.asyncio
async def test_memory_usage():
    """Test memory doesn't grow unbounded."""
    import psutil
    import os

    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB

    for _ in range(1000):
        await orchestrator.validate(content, ["yaml"])

    final_memory = process.memory_info().rss / 1024 / 1024
    growth = final_memory - initial_memory

    assert growth < 50  # Less than 50MB growth
```

### 3.4 Comparison Tests

```python
# tests/validators/test_parity.py

@pytest.mark.asyncio
async def test_new_vs_legacy_parity():
    """Ensure new validators produce same results as legacy."""
    fixtures = load_all_fixtures()

    for fixture in fixtures:
        # Test with legacy
        legacy_result = await legacy_validate(fixture.content, ["yaml"])

        # Test with new
        new_result = await new_validate(fixture.content, ["yaml"])

        # Compare issues
        assert len(legacy_result["issues"]) == len(new_result["issues"])
        assert_issues_equivalent(legacy_result["issues"], new_result["issues"])
```

---

## 4. Deployment Procedures

### 4.1 Pre-Deployment Checklist

```
[ ] All tests passing (unit + integration)
[ ] Code review completed and approved
[ ] Documentation updated
[ ] Feature flags configured
[ ] Rollback plan documented
[ ] Team notified of deployment
[ ] Monitoring alerts configured
[ ] Staging environment tested
```

### 4.2 Deployment Steps

```bash
#!/bin/bash
# deploy.sh - Deployment script

set -e

echo "Starting deployment..."

# 1. Run tests
echo "Running tests..."
python -m pytest tests/ -v --cov
if [ $? -ne 0 ]; then
    echo "Tests failed! Aborting deployment."
    exit 1
fi

# 2. Build
echo "Building..."
docker build -t tbcv:$(git describe --tags) .

# 3. Tag
echo "Tagging release..."
git tag -a v$(date +%Y.%m.%d-%H%M) -m "New validators deployment"
git push origin --tags

# 4. Deploy to staging
echo "Deploying to staging..."
docker-compose -f docker-compose.staging.yml up -d

# 5. Smoke test staging
echo "Smoke testing..."
./scripts/smoke_test.sh staging

# 6. Deploy to production
echo "Deploying to production..."
read -p "Continue to production? (yes/no) " confirm
if [ "$confirm" != "yes" ]; then
    echo "Deployment cancelled."
    exit 0
fi

# Deploy
docker-compose -f docker-compose.prod.yml up -d

# 7. Health check
sleep 10
curl -f http://localhost:8000/health/ready || exit 1

echo "Deployment complete!"
echo "Monitor at: http://monitoring/tbcv"
```

### 4.3 Post-Deployment Verification

```bash
#!/bin/bash
# verify_deployment.sh

# Health checks
curl -f http://localhost:8000/health/live
curl -f http://localhost:8000/health/ready

# Validator discovery
curl -s http://localhost:8000/api/validators/available | jq '.validators | length'

# Test validation
curl -X POST http://localhost:8000/api/validate \
  -H "Content-Type: application/json" \
  -d '{
    "content": "# Test\nContent",
    "validation_types": ["seo"]
  }' | jq '.validation_results.seo_validation.used_legacy'

# Should return: false (using new validator)
```

---

## 5. Rollback Procedures

### 5.1 Rollback Levels

**Level 1: Feature Flag Disable** (Instant)
```yaml
# config/features.yaml
features:
  new_validator_architecture:
    enabled: false  # Disable all new validators
```
```bash
systemctl reload tbcv
```

**Level 2: Reduce Traffic** (1 minute)
```yaml
validators:
  seo: 0  # Reduce to 0%
  # or reduce to lower percentage
```

**Level 3: Code Rollback** (30 minutes)
```bash
# Rollback to previous version
git checkout v2.0.0  # Previous stable version
docker-compose up -d --force-recreate
```

**Level 4: Emergency Fix** (Varies)
- Fix critical bug
- Deploy hotfix
- Re-enable gradually

### 5.2 Rollback Decision Matrix

| Issue | Severity | Rollback Level | Time to Execute |
|-------|----------|----------------|-----------------|
| Error rate > 1% | High | Level 2 | 1 min |
| Latency > 2x | High | Level 2 | 1 min |
| P0 bug | Critical | Level 1 | Instant |
| Memory leak | High | Level 3 | 30 min |
| Incorrect validation | Medium | Level 2 | 1 min |
| Missing feature | Low | None (fix forward) | N/A |

---

## 6. Validation Checklist

### 6.1 Before Each Phase

```
Phase Readiness Checklist:

[ ] Code complete and reviewed
[ ] Tests passing (>90% coverage)
[ ] Documentation updated
[ ] Feature flags configured
[ ] Monitoring configured
[ ] Team trained
[ ] Rollback plan ready
[ ] Stakeholders notified
```

### 6.2 After Each Deployment

```
Deployment Validation:

[ ] Health checks passing
[ ] No error spikes in logs
[ ] Metrics within acceptable ranges
[ ] Validators discoverable via API
[ ] UI showing correct validators
[ ] Legacy fallback working
[ ] No P0/P1 bugs reported
[ ] Performance acceptable
```

---

## 7. Team Responsibilities

### 7.1 Roles

**Migration Lead**:
- Overall coordination
- Decision making
- Risk management

**Backend Developer(s)**:
- Implement validators
- Write tests
- Code reviews

**DevOps**:
- Deployment
- Monitoring
- Rollback execution

**QA**:
- Test planning
- Validation testing
- Regression testing

**Documentation**:
- Update docs
- Migration guides
- API documentation

### 7.2 Communication Plan

**Daily Standups** (During active migration weeks):
- Progress updates
- Blockers
- Risk review

**Weekly Status** (To stakeholders):
- Milestone completion
- Metrics review
- Next week plan

**Incident Response**:
- On-call rotation
- Escalation path
- Post-mortem process

---

## Summary

This migration plan provides a **systematic and seamless** path from the current monolithic validator to a modular, extensible architecture.

**Key Success Factors**:
1. ✅ Backward compatible throughout
2. ✅ Gradual rollout with feature flags
3. ✅ Multiple rollback points
4. ✅ Comprehensive testing at each phase
5. ✅ Clear success criteria
6. ✅ Production-safe deployment

**Timeline**: 8-10 weeks
**Risk**: Low (with feature flags and gradual rollout)
**Business Value**: High (extensible, maintainable, production-ready)

---

**Ready to begin?** Start with Week 0 preparation tasks.

**Questions?** Review [ARCHITECTURE_REVIEW.md](ARCHITECTURE_REVIEW.md) for detailed architecture analysis.
