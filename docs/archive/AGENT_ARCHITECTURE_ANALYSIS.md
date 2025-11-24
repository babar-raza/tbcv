# Agent Architecture Analysis & Refactoring Plan

## Executive Summary

**CRITICAL FINDINGS**:

1. ⚠️ **ContentValidatorAgent is a GOD OBJECT** - Does 10 different validation types internally instead of coordinating separate agents
2. ❌ **Missing dedicated agents**: SEO, Heading, Markdown, YAML, Links, Structure validators
3. ⚠️ **UI selections DON'T override config** - If agent disabled in config, selecting it in UI has no effect
4. ⚠️ **No clear separation of concerns** - Validation logic mixed with agent coordination

---

## Current Architecture Problems

### Problem 1: ContentValidatorAgent Does Everything

**Current State**: [agents/content_validator.py](agents/content_validator.py)

ContentValidatorAgent has **10 validation methods** that should be separate agents:

```python
class ContentValidatorAgent(BaseAgent):
    # Lines 182-204: Routing validation types
    async def handle_validate_content(self, params):
        for vt in validation_types:
            if vt == "yaml":
                result = await self._validate_yaml_with_truths_and_rules(...)  # Line 183
            elif vt == "markdown":
                result = await self._validate_markdown_with_rules(...)  # Line 185
            elif vt == "code":
                result = await self._validate_code_with_patterns(...)  # Line 187
            elif vt == "links":
                result = await self._validate_links(...)  # Line 189
            elif vt == "structure":
                result = await self._validate_structure(...)  # Line 191
            elif vt in ["seo_heading", "seo", "seo_headings"]:
                result = await self._validate_seo_headings(...)  # Line 193
            elif vt in ["heading_size", "heading_sizes", "size"]:
                result = await self._validate_heading_sizes(...)  # Line 195
            elif vt in ["Truth", "truth"]:
                result = await self._validate_yaml_with_truths_and_rules(...)  # Line 197
            elif vt in ["FuzzyLogic", "fuzzylogic", "fuzzy"]:
                result = await self._validate_with_fuzzy_logic(...)  # Line 199
            elif vt == "llm":
                result = await self._validate_with_llm(...)  # Line 201
```

**Why This Is Wrong**:
- ❌ Violates Single Responsibility Principle
- ❌ 2100+ lines of code in one file
- ❌ Hard to maintain, test, and extend
- ❌ Can't enable/disable individual validators via config
- ❌ Can't have different concurrency limits per validator
- ❌ Can't independently version or update validators

### Problem 2: UI Selections Don't Override Config

**Current Flow**:

```
UI Selection: ["yaml", "FuzzyLogic", "seo"]
    ↓
API Request: {validation_types: ["yaml", "FuzzyLogic", "seo"]}
    ↓
Orchestrator: passes validation_types to ContentValidator
    ↓
ContentValidator: loops through validation_types
    ├─ "yaml" → _validate_yaml() ✅ Runs
    ├─ "FuzzyLogic" → _validate_with_fuzzy_logic()
    │   └─ agent_registry.get_agent("fuzzy_detector")
    │       └─ Returns None (not registered because config: enabled=false)
    │           └─ Returns warning: "FuzzyDetector agent not available" ⚠️
    └─ "seo" → _validate_seo_headings() ✅ Runs (internal method)
```

**The Problem**:
- Selecting "FuzzyLogic" in UI does nothing if `fuzzy_detector.enabled: false` in config
- User has no idea why it doesn't work
- Config **PREVENTS** UI selections from working

**What Should Happen**:
- UI selections should **OVERRIDE** config defaults
- If user selects "FuzzyLogic", it should be enabled for that request
- Config should only set defaults, not hard restrictions

### Problem 3: No Agent Discovery

**Current**: UI has hardcoded checkboxes

```html
<label><input type="checkbox" value="yaml"> YAML</label>
<label><input type="checkbox" value="FuzzyLogic"> FuzzyLogic</label>
<!-- Missing: seo, heading_sizes, llm -->
```

**What Should Happen**:
- UI should dynamically query available validators from backend
- Backend returns list of registered validator agents
- UI shows checkboxes only for available validators
- Disabled/missing validators don't show up (or show as disabled)

---

## Proposed Architecture

### Agent Hierarchy

```
BaseAgent (abstract)
├─ TruthManagerAgent (data management)
├─ FuzzyDetectorAgent (plugin detection)
├─ OrchestratorAgent (workflow coordination)
│
├─ Validators (NEW HIERARCHY)
│   ├─ BaseValidatorAgent (abstract, shared logic)
│   │   ├─ YamlValidatorAgent
│   │   ├─ MarkdownValidatorAgent
│   │   ├─ CodeValidatorAgent
│   │   ├─ LinkValidatorAgent
│   │   ├─ StructureValidatorAgent
│   │   ├─ SeoValidatorAgent (SEO headings + heading sizes)
│   │   └─ TruthValidatorAgent (Truth validation)
│   │
│   └─ LLMValidatorAgent (already exists, separate)
│
├─ Enhancers
│   ├─ ContentEnhancerAgent
│   └─ EnhancementAgent
│
└─ Generators
    ├─ RecommendationAgent
    └─ CodeAnalyzerAgent
```

### Validation Type → Agent Mapping

| UI Type | Agent | Config Key | File |
|---------|-------|-----------|------|
| `yaml` | YamlValidatorAgent | `validators.yaml.enabled` | `agents/validators/yaml_validator.py` |
| `markdown` | MarkdownValidatorAgent | `validators.markdown.enabled` | `agents/validators/markdown_validator.py` |
| `code` | CodeValidatorAgent | `validators.code.enabled` | `agents/validators/code_validator.py` |
| `links` | LinkValidatorAgent | `validators.links.enabled` | `agents/validators/link_validator.py` |
| `structure` | StructureValidatorAgent | `validators.structure.enabled` | `agents/validators/structure_validator.py` |
| `Truth` | TruthValidatorAgent | `validators.truth.enabled` | `agents/validators/truth_validator.py` |
| `FuzzyLogic` | FuzzyDetectorAgent | `agents.fuzzy_detector.enabled` | `agents/fuzzy_detector.py` (exists) |
| `seo` | SeoValidatorAgent | `validators.seo.enabled` | `agents/validators/seo_validator.py` |
| `heading_sizes` | SeoValidatorAgent | `validators.seo.heading_sizes_enabled` | `agents/validators/seo_validator.py` |
| `llm` | LLMValidatorAgent | `agents.llm_validator.enabled` | `agents/llm_validator.py` (exists) |

### New Base Validator Agent

```python
# agents/validators/base_validator.py
from abc import abstractmethod
from agents.base import BaseAgent, AgentContract, AgentCapability
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class ValidationIssue:
    level: str  # "error", "warning", "info"
    category: str
    message: str
    line_number: Optional[int] = None
    column: Optional[int] = None
    suggestion: Optional[str] = None
    source: str = "validator"

@dataclass
class ValidationResult:
    confidence: float
    issues: List[ValidationIssue]
    auto_fixable_count: int
    metrics: Dict[str, Any]

class BaseValidatorAgent(BaseAgent):
    """Base class for all validator agents."""

    @abstractmethod
    def get_validation_type(self) -> str:
        """Return the validation type this agent handles (e.g., 'yaml', 'markdown')."""
        pass

    @abstractmethod
    async def validate(self, content: str, context: Dict[str, Any]) -> ValidationResult:
        """Validate content and return issues."""
        pass

    def get_contract(self) -> AgentContract:
        return AgentContract(
            agent_id=self.agent_id,
            name=self.__class__.__name__,
            version="1.0.0",
            capabilities=[
                AgentCapability(
                    name="validate",
                    description=f"Validate {self.get_validation_type()} content",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "content": {"type": "string"},
                            "context": {"type": "object"}
                        },
                        "required": ["content"]
                    },
                    output_schema={"type": "object"},
                    side_effects=["read"]
                )
            ],
            checkpoints=[]
        )
```

---

## New Orchestrator Logic

### Current (Wrong):
```python
# orchestrator.py:394-416
content_validator = agent_registry.get_agent("content_validator")
if content_validator:
    result = await content_validator.process_request("validate_content", {
        "content": content,
        "validation_types": validation_types or default_types
    })
```

### Proposed (Correct):
```python
# orchestrator.py (NEW)
async def _run_validation_pipeline(self, content: str, file_path: str, family: str, validation_types: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Run validation pipeline by calling individual validator agents.
    UI selections OVERRIDE config defaults.
    """
    # If validation_types provided (from UI), use them
    # Otherwise, get enabled validators from config
    if validation_types is None:
        validation_types = self._get_enabled_validators_from_config()

    results = {}
    issues = []

    # Map validation types to agent IDs
    validator_map = {
        "yaml": "yaml_validator",
        "markdown": "markdown_validator",
        "code": "code_validator",
        "links": "link_validator",
        "structure": "structure_validator",
        "Truth": "truth_validator",
        "FuzzyLogic": "fuzzy_detector",
        "seo": "seo_validator",
        "heading_sizes": "seo_validator",  # Same agent, different mode
        "llm": "llm_validator"
    }

    for vt in validation_types:
        agent_id = validator_map.get(vt)
        if not agent_id:
            logger.warning(f"Unknown validation type: {vt}")
            continue

        # Get agent from registry
        agent = agent_registry.get_agent(agent_id)

        if not agent:
            # Agent not registered - provide clear feedback
            issues.append({
                "level": "warning",
                "category": f"{vt}_unavailable",
                "message": f"{vt} validator not available (disabled in config or not installed)",
                "suggestion": f"Enable {agent_id} in config or check agent registration"
            })
            continue

        # Call validator agent
        try:
            result = await self._call_agent_gated(agent_id, "validate", {
                "content": content,
                "context": {
                    "file_path": file_path,
                    "family": family,
                    "validation_type": vt
                }
            })
            results[f"{vt}_validation"] = result
            issues.extend(result.get("issues", []))
        except Exception as e:
            logger.exception(f"Validation {vt} failed: {e}")
            issues.append({
                "level": "error",
                "category": f"{vt}_error",
                "message": f"Validation failed: {str(e)}"
            })

    return {
        "validation_results": results,
        "issues": issues,
        "file_path": file_path,
        "family": family
    }

def _get_enabled_validators_from_config(self) -> List[str]:
    """Get list of enabled validators from config."""
    settings = get_settings()
    enabled = []

    # Check each validator in config
    validator_configs = {
        "yaml": ("validators.yaml.enabled", True),
        "markdown": ("validators.markdown.enabled", True),
        "code": ("validators.code.enabled", True),
        "links": ("validators.links.enabled", True),
        "structure": ("validators.structure.enabled", True),
        "Truth": ("validators.truth.enabled", True),
        "FuzzyLogic": ("agents.fuzzy_detector.enabled", False),
        "seo": ("validators.seo.enabled", True),
        "heading_sizes": ("validators.seo.heading_sizes_enabled", True),
        "llm": ("agents.llm_validator.enabled", False)
    }

    for vt, (config_path, default) in validator_configs.items():
        if self._get_config_value(config_path, default):
            enabled.append(vt)

    return enabled
```

---

## UI Dynamic Discovery

### New API Endpoint

```python
# api/server.py
@app.get("/api/validators/available")
async def get_available_validators():
    """Return list of available validators for UI."""
    validators = []

    validator_map = {
        "yaml_validator": {"id": "yaml", "label": "YAML", "description": "Validate YAML frontmatter"},
        "markdown_validator": {"id": "markdown", "label": "Markdown", "description": "Validate Markdown syntax"},
        "code_validator": {"id": "code", "label": "Code", "description": "Validate code blocks"},
        "link_validator": {"id": "links", "label": "Links", "description": "Check link validity"},
        "structure_validator": {"id": "structure", "label": "Structure", "description": "Validate document structure"},
        "truth_validator": {"id": "Truth", "label": "Truth", "description": "Validate against truth data"},
        "fuzzy_detector": {"id": "FuzzyLogic", "label": "Fuzzy Logic", "description": "Fuzzy plugin detection"},
        "seo_validator": [
            {"id": "seo", "label": "SEO Headings", "description": "Validate SEO-friendly heading structure"},
            {"id": "heading_sizes", "label": "Heading Sizes", "description": "Validate heading length limits"}
        ],
        "llm_validator": {"id": "llm", "label": "LLM Analysis", "description": "Semantic validation via LLM"}
    }

    for agent_id, info in validator_map.items():
        agent = agent_registry.get_agent(agent_id)
        if agent:
            if isinstance(info, list):
                validators.extend([{**i, "available": True, "enabled_by_default": True} for i in info])
            else:
                validators.append({**info, "available": True, "enabled_by_default": True})
        else:
            # Not available
            if isinstance(info, list):
                validators.extend([{**i, "available": False, "enabled_by_default": False} for i in info])
            else:
                validators.append({**info, "available": False, "enabled_by_default": False})

    return {"validators": validators}
```

### Updated UI Template

```html
<!-- templates/validations_list.html -->
<div id="validationTypesContainer" style="margin-bottom: 15px;">
    <label style="display: block; margin-bottom: 5px; font-weight: 600;">Validation Types:</label>
    <div id="validationTypesList" style="display: flex; flex-wrap: wrap; gap: 10px;">
        <!-- Dynamically populated via JavaScript -->
        <div class="spinner">Loading validators...</div>
    </div>
</div>

<script>
// Load available validators from API
async function loadValidators() {
    const response = await fetch('/api/validators/available');
    const data = await response.json();

    const container = document.getElementById('validationTypesList');
    container.innerHTML = '';

    data.validators.forEach(validator => {
        const label = document.createElement('label');
        label.style.opacity = validator.available ? '1' : '0.5';
        label.title = validator.description;

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.value = validator.id;
        checkbox.className = 'validation-type';
        checkbox.checked = validator.enabled_by_default && validator.available;
        checkbox.disabled = !validator.available;

        label.appendChild(checkbox);
        label.appendChild(document.createTextNode(' ' + validator.label));

        if (!validator.available) {
            label.appendChild(document.createTextNode(' (unavailable)'));
        }

        container.appendChild(label);
    });
}

// Load on page load
document.addEventListener('DOMContentLoaded', loadValidators);
</script>
```

---

## Migration Plan

### Phase 1: Create Base Infrastructure (Week 1)

#### Files to Create:
```
agents/validators/
├── __init__.py
├── base_validator.py (BaseValidatorAgent + shared types)
└── README.md
```

#### Tasks:
- [ ] Create `agents/validators/` directory
- [ ] Implement `BaseValidatorAgent` abstract class
- [ ] Define `ValidationIssue` and `ValidationResult` dataclasses
- [ ] Write unit tests for base validator

### Phase 2: Extract First Validator (Week 1-2)

#### Files to Create:
```
agents/validators/yaml_validator.py
tests/agents/validators/test_yaml_validator.py
```

#### Tasks:
- [ ] Create `YamlValidatorAgent`
- [ ] Extract `_validate_yaml_with_truths_and_rules()` from ContentValidator
- [ ] Register agent in `api/server.py`
- [ ] Add config: `validators.yaml.enabled: true`
- [ ] Update orchestrator to call YamlValidatorAgent
- [ ] Test end-to-end: UI → API → Orchestrator → YamlValidator
- [ ] Verify old ContentValidator method still works (backward compatibility)

### Phase 3: Extract Remaining Validators (Week 2-4)

#### Priority Order:

1. **MarkdownValidatorAgent** (most used)
   - Extract `_validate_markdown_with_rules()`
   - File: `agents/validators/markdown_validator.py`

2. **SeoValidatorAgent** (missing from UI)
   - Extract `_validate_seo_headings()` + `_validate_heading_sizes()`
   - File: `agents/validators/seo_validator.py`
   - Handles both `seo` and `heading_sizes` types

3. **CodeValidatorAgent**
   - Extract `_validate_code_with_patterns()`
   - File: `agents/validators/code_validator.py`

4. **LinkValidatorAgent**
   - Extract `_validate_links()`
   - File: `agents/validators/link_validator.py`

5. **StructureValidatorAgent**
   - Extract `_validate_structure()`
   - File: `agents/validators/structure_validator.py`

6. **TruthValidatorAgent**
   - Extract `_validate_against_truth_data()`
   - File: `agents/validators/truth_validator.py`

### Phase 4: Update Orchestrator (Week 4)

#### Tasks:
- [ ] Update `_run_validation_pipeline()` to call individual validators
- [ ] Implement `_get_enabled_validators_from_config()`
- [ ] Add validator discovery logic
- [ ] Remove dependency on ContentValidator's `validate_content` method
- [ ] Test all validation types work independently

### Phase 5: Update UI & API (Week 5)

#### Tasks:
- [ ] Create `/api/validators/available` endpoint
- [ ] Update `validations_list.html` to load validators dynamically
- [ ] Add tooltips/descriptions for each validator
- [ ] Show disabled validators as unavailable
- [ ] Test UI updates in real-time when agent is enabled/disabled

### Phase 6: Update Configuration (Week 5)

#### Update `config/main.yaml`:

```yaml
agents:
  fuzzy_detector:
    enabled: true  # FIX: Enable by default

  llm_validator:
    enabled: false  # Requires Ollama

validators:
  yaml:
    enabled: true
    strict_mode: false

  markdown:
    enabled: true
    extensions:
      - tables
      - fenced_code
      - codehilite

  code:
    enabled: true
    patterns_enabled: true

  links:
    enabled: true
    timeout_seconds: 5
    check_external: true

  structure:
    enabled: true
    min_sections: 2

  truth:
    enabled: true
    strict_validation: false

  seo:
    enabled: true
    heading_sizes_enabled: true
    config_file: "config/seo.yaml"
```

### Phase 7: Deprecate Old ContentValidator (Week 6)

#### Tasks:
- [ ] Mark `ContentValidatorAgent.handle_validate_content()` as deprecated
- [ ] Add deprecation warnings in logs
- [ ] Update all callers to use orchestrator directly
- [ ] Remove old validation methods from ContentValidator (or mark private)
- [ ] Update documentation

### Phase 8: Testing & Documentation (Week 6-7)

#### Tasks:
- [ ] End-to-end tests for all 10 validation types
- [ ] Test UI selections override config
- [ ] Test agent availability detection
- [ ] Test backward compatibility
- [ ] Update RUNBOOK.md
- [ ] Update API documentation
- [ ] Create migration guide for users

---

## Configuration Override Mechanism

### Current Problem:
```yaml
# config/main.yaml
agents:
  fuzzy_detector:
    enabled: false  # ← Prevents UI selection from working
```

### Solution: UI Override

```python
# orchestrator.py
async def _run_validation_pipeline(self, content, file_path, family, validation_types=None):
    # If validation_types provided (from UI), it OVERRIDES config
    if validation_types is not None:
        # UI selection - try to run even if disabled in config
        requested_validators = validation_types
    else:
        # No UI selection - use config defaults
        requested_validators = self._get_enabled_validators_from_config()

    for vt in requested_validators:
        agent = agent_registry.get_agent(validator_map[vt])

        if not agent:
            # Agent not registered - provide helpful error
            if validation_types is not None:
                # User requested it via UI but agent not available
                issues.append({
                    "level": "error",
                    "category": f"{vt}_not_available",
                    "message": f"{vt} validator not available. Enable '{validator_map[vt]}' in config and restart server.",
                    "suggestion": f"Set agents.{validator_map[vt]}.enabled: true in config/main.yaml"
                })
            else:
                # Config enabled it but agent not registered - log warning
                logger.warning(f"Validator {vt} enabled in config but agent not registered")
            continue

        # Run validation
        result = await agent.validate(content, context)
```

---

## File Structure (After Migration)

```
agents/
├── __init__.py
├── base.py (BaseAgent, AgentContract, etc.)
├── orchestrator.py (coordinates validators)
├── fuzzy_detector.py (exists)
├── llm_validator.py (exists)
├── truth_manager.py (exists)
├── content_enhancer.py (exists)
├── enhancement_agent.py (exists)
├── recommendation_agent.py (exists)
├── code_analyzer.py (exists)
│
├── validators/ (NEW)
│   ├── __init__.py
│   ├── base_validator.py (BaseValidatorAgent)
│   ├── yaml_validator.py (YamlValidatorAgent)
│   ├── markdown_validator.py (MarkdownValidatorAgent)
│   ├── code_validator.py (CodeValidatorAgent)
│   ├── link_validator.py (LinkValidatorAgent)
│   ├── structure_validator.py (StructureValidatorAgent)
│   ├── truth_validator.py (TruthValidatorAgent)
│   └── seo_validator.py (SeoValidatorAgent - handles seo + heading_sizes)
│
└── content_validator.py (DEPRECATED - kept for backward compatibility)
```

---

## Benefits of New Architecture

1. ✅ **Single Responsibility** - Each validator has one job
2. ✅ **Independent Configuration** - Enable/disable validators individually
3. ✅ **UI Override** - UI selections work regardless of config
4. ✅ **Dynamic Discovery** - UI shows only available validators
5. ✅ **Better Testing** - Test each validator independently
6. ✅ **Easier Maintenance** - Update one validator without affecting others
7. ✅ **Scalability** - Add new validators without modifying existing code
8. ✅ **Clearer Errors** - Know exactly which validator failed and why
9. ✅ **Performance** - Independent concurrency limits per validator
10. ✅ **Versioning** - Version each validator independently

---

## Summary of Required Changes

| Component | Change | Priority | Effort |
|-----------|--------|----------|--------|
| Create `BaseValidatorAgent` | New base class | P0 | 1 day |
| Extract `YamlValidatorAgent` | New agent | P0 | 2 days |
| Extract `SeoValidatorAgent` | New agent (missing in UI) | P0 | 3 days |
| Extract `MarkdownValidatorAgent` | New agent | P1 | 2 days |
| Extract `CodeValidatorAgent` | New agent | P1 | 2 days |
| Extract `LinkValidatorAgent` | New agent | P1 | 1 day |
| Extract `StructureValidatorAgent` | New agent | P1 | 1 day |
| Extract `TruthValidatorAgent` | New agent | P1 | 2 days |
| Update Orchestrator | New validation routing | P0 | 3 days |
| Create `/api/validators/available` | New API endpoint | P0 | 1 day |
| Update UI Template | Dynamic validator loading | P0 | 2 days |
| Update Config Schema | New validators section | P0 | 1 day |
| Enable fuzzy_detector | Config change | P0 | 5 min |
| Deprecate old ContentValidator | Backward compatibility | P2 | 1 day |
| Write Tests | Full coverage | P0 | 5 days |
| Write Documentation | Migration guide | P1 | 2 days |

**Total Effort**: ~4-5 weeks for complete migration

---

## Quick Wins (Can Do Today)

### 1. Enable Fuzzy Detector (5 minutes)

```yaml
# config/main.yaml:27
agents:
  fuzzy_detector:
    enabled: true  # ← Change from false
```

### 2. Add Missing Validators to UI (10 minutes)

```html
<!-- templates/validations_list.html:105 -->
<label><input type="checkbox" value="seo" class="validation-type"> SEO</label>
<label><input type="checkbox" value="heading_sizes" class="validation-type"> Heading Sizes</label>
<label><input type="checkbox" value="llm" class="validation-type"> LLM</label>
```

### 3. Create SeoValidatorAgent Skeleton (1 hour)

See next section for implementation template...

---

## Next Steps

**Immediate**:
1. Review and approve this architecture plan
2. Decide on migration timeline (all at once vs phased)
3. Create SeoValidatorAgent first (most impactful - missing from UI)

**Short Term**:
1. Implement BaseValidatorAgent
2. Extract YamlValidatorAgent as proof of concept
3. Update orchestrator to support both old and new validators

**Long Term**:
1. Complete migration of all validators
2. Deprecate old ContentValidator
3. Update all documentation

Would you like me to start implementing the SeoValidatorAgent as a proof of concept?
