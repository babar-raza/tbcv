# TBCV Agents Reference

This document provides comprehensive documentation for all agents in the TBCV system.

## Overview

TBCV uses a multi-agent architecture with **19 total agents** organized into three categories (9 core + 3 pipeline + 7 validators):

### Core Agents (9 agents)
Specialized agents in `agents/` directory that communicate via message passing:

1. **OrchestratorAgent** (`orchestrator.py`) - Workflow coordination with concurrency control
2. **TruthManagerAgent** (`truth_manager.py`) - Plugin truth data management and indexing
3. **FuzzyDetectorAgent** (`fuzzy_detector.py`) - Pattern matching and plugin detection
4. **ContentValidatorAgent** (`content_validator.py`) - **DEPRECATED** Multi-scope content validation (replaced by modular validators, will be removed in v2.0.0 - 2026-01-01)
5. **LLMValidatorAgent** (`llm_validator.py`) - Semantic LLM validation via Ollama
6. **ContentEnhancerAgent** (`content_enhancer.py`) - Content enhancement with safety gating
7. **RecommendationAgent** (`recommendation_agent.py`) - Actionable recommendation generation
8. **CodeAnalyzerAgent** (`code_analyzer.py`) - Code quality and security analysis
9. **EnhancementAgent** (`enhancement_agent.py`) - Apply approved recommendations to content (facade over ContentEnhancerAgent)

### Enhancement and Recommendation Pipeline Agents (3 agents)
Supporting agents for the recommendation-to-enhancement pipeline:

1. **EditValidator** (`edit_validator.py`) - Validates edits before/after enhancement, compares content changes
2. **RecommendationEnhancer** (`recommendation_enhancer.py`) - Advanced surgical content enhancement with safety validation and rollback capability
3. **RecommendationCriticAgent** (`recommendation_critic.py`) - Validates recommendation quality, detects contradictions and redundancy

### Modular Validator Agents (7 validators)
Specialized validators in `agents/validators/` replacing monolithic ContentValidatorAgent:

1. **YamlValidatorAgent** (`yaml_validator.py`) - YAML frontmatter validation
2. **MarkdownValidatorAgent** (`markdown_validator.py`) - Markdown structure validation
3. **CodeValidatorAgent** (`code_validator.py`) - Code block validation
4. **LinkValidatorAgent** (`link_validator.py`) - Link and URL validation
5. **StructureValidatorAgent** (`structure_validator.py`) - Document structure validation
6. **TruthValidatorAgent** (`truth_validator.py`) - Truth data validation
7. **SeoValidatorAgent** (`seo_validator.py`) - SEO and heading size validation

Plus supporting classes:
- **BaseValidatorAgent** (`base_validator.py`) - Abstract base for all validators
- **ValidatorRouter** (`router.py`) - Routes validation requests to appropriate validators

All agents inherit from `BaseAgent` (agents/base.py) and implement the MCP message passing pattern.

## Agent Communication Pattern

All agents in TBCV follow the MCP-first architecture pattern and are protected by the dual-layer access control system.

```python
# All agents follow this pattern:
class MyAgent(BaseAgent):
    async def process_request(self, method: str, params: dict) -> dict:
        """Handle MCP request and return response"""

    def get_contract(self) -> AgentContract:
        """Return agent capabilities"""

    def get_status(self) -> dict:
        """Return agent health and statistics"""
```

### Access Control

Agents are protected by TBCV's **dual-layer access control system**:

1. **Import-Time Guard** (`core/import_guard.py`): Prevents API/CLI from importing agent modules
2. **Runtime Access Guard** (`core/access_guard.py`): Prevents API/CLI from calling agent methods directly

**Allowed Access:**
- MCP Server (`svc/mcp_server.py`)
- MCP Methods (`svc/mcp_methods/*`)
- Tests (`tests/*`)

**Blocked Access:**
- API endpoints (`api/*`)
- CLI commands (`cli/*`)

See [Security Documentation](security.md) for complete details on the access control system, including configuration, enforcement modes, and troubleshooting.

---

## 1. OrchestratorAgent

**Location**: `agents/orchestrator.py`
**Purpose**: Coordinates multi-agent workflows with per-agent concurrency gating

### Key Features

- Workflow types: validate_file, validate_directory, full_validation, content_update
- Per-agent semaphores prevent overload (LLM: 1 concurrent, Validator: 2, etc.)
- Exponential backoff when agents busy
- Three validation modes: two_stage (default), heuristic_only, llm_only
- Batch processing with configurable workers

### Configuration

```yaml
# config/main.yaml
orchestrator:
  max_file_workers: 4
  retry_timeout_s: 120
  retry_backoff_base: 0.5
  retry_backoff_cap: 8
  agent_limits:
    llm_validator: 1    # Prevent Ollama overload
    content_validator: 2
    truth_manager: 4
    fuzzy_detector: 2
```

### Methods

- **`start_workflow(workflow_type, input_params)`** - Start new workflow
- **`validate_file(file_path, content, family)`** - Single file validation pipeline
- **`validate_directory(directory_path, pattern, workers)`** - Batch validation
- **`get_workflow_status(workflow_id)`** - Check workflow progress

### Example

```python
orchestrator = agent_registry.get_agent("orchestrator")
result = await orchestrator.process_request("validate_file", {
    "file_path": "tutorial.md",
    "content": content,
    "family": "words"
})
```

## 2. TruthManagerAgent

**Location**: `agents/truth_manager.py`
**Purpose**: Manages plugin truth data with multi-level indexing

### Key Features

- Loads JSON truth files from `truth/` directory
- 6 indexes: by_id, by_slug, by_name, by_alias, by_pattern, by_family
- Generic TruthDataAdapter normalizes various JSON schemas
- Combination rules from `aspose_words_plugins_combinations.json`
- Cache TTL: 7 days (604800 seconds)

### Configuration

```yaml
truth_manager:
  enabled: true
  auto_reload: true
  cache_ttl_seconds: 604800
  truth_directories:
    - "./truth"
    - "./truth/words"
```

### JSON Schema

```json
{
  "family": "words",
  "plugins": [
    {
      "id": "plugin-id",
      "name": "Plugin Name",
      "slug": "plugin-slug",
      "patterns": {
        "classNames": ["Class1"],
        "methods": ["Method1"],
        "imports": ["Namespace"]
      }
    }
  ]
}
```

### Methods

- **`load_truth_data(family)`** - Load plugins for family
- **`get_plugin_by_id(plugin_id)`** - O(1) lookup by ID
- **`get_plugins_by_family(family)`** - Get all plugins for family
- **`search_plugins(query, family)`** - Search by name/description

## 3. FuzzyDetectorAgent

**Location**: `agents/fuzzy_detector.py`
**Purpose**: Detects plugin usage via regex and fuzzy matching

### Key Features

- Regex pattern matching from truth data
- Fuzzy algorithms: Levenshtein distance, Jaro-Winkler similarity
- Confidence aggregation: `1 - ∏(1-c_i)`
- Deduplication by plugin+position
- Similarity threshold: 0.85 (configurable)

### Configuration

```yaml
fuzzy_detector:
  enabled: true
  similarity_threshold: 0.85
  context_window_chars: 200
  fuzzy_algorithms:
    - "levenshtein"
    - "jaro_winkler"
```

### Detection Types

1. **Exact Match** (weight: 1.0) - Exact string match
2. **Regex Pattern** (weight: 0.8) - Pattern from truth data
3. **Fuzzy Match** (weight: 0.8) - Levenshtein/Jaro-Winkler > threshold

### Methods

- **`detect_plugins(content, family, context)`** - Detect all plugins in content

### Response Format

```json
{
  "detections": [
    {
      "plugin_id": "pdf-save",
      "confidence": 0.95,
      "detection_type": "exact",
      "matched_text": "SaveFormat.Pdf",
      "position": {"start": 120, "end": 135, "line": 15}
    }
  ]
}
```

## 4. ContentValidatorAgent (DEPRECATED)

> **DEPRECATION NOTICE**: ContentValidatorAgent is deprecated and will be removed in version 2.0.0 (target: 2026-01-01).
>
> **Use modular validators instead:**
> - `YamlValidatorAgent` for YAML frontmatter validation
> - `MarkdownValidatorAgent` for Markdown structure validation
> - `CodeValidatorAgent` for code block validation
> - `LinkValidatorAgent` for link validation
> - `StructureValidatorAgent` for document structure validation
> - `TruthValidatorAgent` for truth data validation
> - `SeoValidatorAgent` for SEO validation
>
> **Migration Guide**: See [docs/migration/content_validator_migration.md](../migration/content_validator_migration.md)

**Location**: `agents/content_validator.py`
**Purpose**: Multi-scope content validation (YAML, Markdown, code, links, truth) with optional LLM semantic validation

### Key Features

- YAML frontmatter validation (required fields, types)
- Markdown structure (heading hierarchy, code blocks)
- Code validation (language specifiers, completeness)
- Link validation (broken links, timeouts)
- **Truth validation with two-stage approach:**
  - **Stage 1**: Heuristic validation (pattern matching, field presence)
  - **Stage 2**: LLM semantic validation (validates correctness against truth data)
- Auto-generates recommendations via RecommendationAgent

### Configuration

```yaml
content_validator:
  enabled: true
  html_sanitization: true
  link_validation: true
  link_timeout_seconds: 5
  yaml_strict_mode: false

llm_validation:
  enabled: true  # Enable LLM semantic validation
  truth_validation_enabled: true  # Enable LLM for truth validation
  model: "mistral"  # Ollama model to use
  temperature: 0.1  # Low temperature for consistent validation
  fallback_to_heuristic: true  # Use heuristics if Ollama unavailable
```

### Validation Types

1. **yaml** - Frontmatter validation
2. **markdown** - Structure and syntax
3. **code** - Code block validation
4. **links** - Link checking
5. **truth** - Two-stage truth validation:
   - **Heuristic**: Pattern matching for plugin declaration vs usage
   - **LLM Semantic**: Validates technical accuracy, plugin combinations, format compatibility

### LLM Truth Validation (NEW!)

The ContentValidatorAgent now supports **semantic validation** using Ollama LLM to catch issues that heuristics cannot detect:

**What LLM Truth Validation Detects:**

1. **Plugin Requirements** - Missing plugins implied by operations
   - Example: "Convert DOCX to PDF" without declaring Document, PDF, and Document Converter plugins

2. **Plugin Combinations** - Invalid or incomplete plugin sets
   - Example: Using feature plugins (Merger, Comparer) without processor plugins

3. **Technical Accuracy** - Claims that contradict truth data
   - Example: "Document plugin loads XLSX" (wrong - needs Cells plugin)

4. **Format Compatibility** - File format mismatches
   - Example: Claiming PDF processor loads DOCX files

5. **Missing Prerequisites** - Implied steps not mentioned
   - Example: Watermarking PDF without mentioning loading step

6. **Semantic Contradictions** - Content contradicting itself or truth
   - Example: Claiming something is "lightweight" but requires heavy plugins

**How it Works:**

```python
# When validation_types includes "Truth":
# 1. Run heuristic validation (pattern matching)
truth_issues = await self._validate_against_truth_data(content, family, truth_context)

# 2. Run LLM semantic validation (if enabled)
semantic_issues = await self._validate_truth_with_llm(
    content=content,
    family=family,
    truth_context=truth_context,
    heuristic_issues=truth_issues  # LLM sees heuristic findings
)

# 3. Combine both
all_issues = truth_issues + semantic_issues
```

**Fallback Behavior:**
- If Ollama unavailable → Falls back to heuristic validation only
- If LLM disabled in config → Uses heuristic validation only
- No disruption to validation pipeline

### Methods

- **`validate_content(content, file_path, family, validation_types)`** - Run all validations
- **`_validate_against_truth_data(content, family, truth_context)`** - Heuristic truth validation
- **`_validate_truth_with_llm(content, family, truth_context, heuristic_issues)`** - LLM semantic validation (NEW!)

### Response Format

```json
{
  "validation_id": "val-123",
  "status": "fail",
  "confidence": 0.75,
  "issues": [
    {
      "level": "error",
      "category": "yaml",
      "message": "Missing required field 'title'",
      "line": 1,
      "suggestion": "Add 'title: Your Title'",
      "source": "rule"
    },
    {
      "level": "error",
      "category": "plugin_requirement",
      "message": "DOCX to PDF conversion requires Document, PDF, and Document Converter plugins",
      "suggestion": "Add plugins: [document, pdf-processor, document-converter]",
      "source": "llm_truth",
      "confidence": 0.95
    }
  ],
  "metrics": {
    "Truth_metrics": {
      "heuristic_issues": 1,
      "semantic_issues": 1,
      "llm_validation_enabled": true
    }
  }
}
```

## 5. LLMValidatorAgent

**Location**: `agents/llm_validator.py`
**Purpose**: Semantic validation using Ollama LLM

### Key Features

- Calls Ollama API for semantic plugin analysis
- Verifies fuzzy detector findings
- Identifies missing plugins based on code semantics
- Graceful degradation when Ollama unavailable
- Timeout: 30 seconds

### Configuration

```yaml
llm_validator:
  enabled: true
  provider: ollama
  model: llama2
  temperature: 0.3
  timeout_seconds: 30
```

### LLM Prompt Structure

The agent sends:
- Code snippet
- Fuzzy detector results
- Available plugins from truth data
- Instructions for JSON output

### Methods

- **`validate_plugins(content, fuzzy_detections, truth_data)`** - Semantic validation

### Response Format

```json
{
  "requirements": [
    {
      "plugin_id": "pdf-save",
      "confidence": 0.95,
      "reasoning": "Code uses SaveFormat.Pdf",
      "validation_status": "confirmed"
    }
  ],
  "llm_available": true
}
```

## 6. ContentEnhancerAgent

**Location**: `agents/content_enhancer.py`
**Purpose**: Enhance content with plugin links and apply recommendations

### Key Features

- Add plugin hyperlinks to first mentions
- Add info text after code blocks
- Apply approved recommendations from database
- **Safety gating**: Block if rewrite_ratio > 0.5 or blocked topics found
- Backup original content

### Configuration

```yaml
content_enhancer:
  enabled: true
  auto_link_plugins: true
  add_info_text: true
  link_template: "https://products.aspose.com/words/net/plugins/{slug}/"
  rewrite_ratio_threshold: 0.5
  blocked_topics: ["forbidden"]
```

### Safety Checks

```python
# Rewrite ratio check
rewrite_ratio = abs(len(enhanced) - len(original)) / len(original)
if rewrite_ratio > 0.5:
    raise SafetyGateError("Change too large")

# Blocked topics check
if any(blocked in enhanced for blocked in blocked_topics):
    raise SafetyGateError("Blocked topic detected")
```

### Methods

- **`enhance_content(content, file_path, enhancement_types, preview_only)`** - Auto enhancement
- **`enhance_from_recommendations(content, recommendations, file_path)`** - Apply approved recs

## 7. RecommendationAgent

**Location**: `agents/recommendation_agent.py`
**Purpose**: Generate actionable improvement recommendations

### Key Features

- Type-specific recommendation templates (yaml, markdown, code, links, truth)
- Confidence scoring based on issue severity
- Concrete instructions with rationale
- Database persistence with "proposed" status
- Human review workflow

### Configuration

```yaml
recommendation_agent:
  enabled: true
  confidence_threshold: 0.7
  max_recommendations_per_file: 20
  auto_approve_high_confidence: false
  high_confidence_threshold: 0.95
```

### Recommendation Structure

```json
{
  "type": "yaml|markdown|code|link|truth",
  "instruction": "Add 'title' field to frontmatter",
  "rationale": "Title is required for indexing",
  "scope": "line|block|frontmatter|inline",
  "line_number": 1,
  "original_content": "...",
  "proposed_content": "...",
  "severity": "error|warning|info",
  "confidence": 0.90
}
```

### Methods

- **`generate_recommendations(validation, content, context, persist)`** - Generate from validation issues

## 8. CodeAnalyzerAgent

**Location**: `agents/code_analyzer.py`
**Purpose**: Code quality and security analysis

### Key Features

- Multi-language support (Python, C#, Java, JavaScript)
- Complexity metrics (cyclomatic complexity)
- Security scanning (SQL injection, XSS, command injection)
- Performance hints
- Best practice suggestions

### Configuration

```yaml
code_analyzer:
  enabled: true
  languages: [python, csharp, java, javascript]
  max_complexity_threshold: 15
  analyze_security: true
  analyze_performance: true
```

### Methods

- **`analyze_code(code, language, analysis_types)`** - Analyze code block

## Agent Registry

All agents register with the global `agent_registry` (agents/base.py):

```python
from agents.base import agent_registry

# Register agent
agent_registry.register_agent(my_agent)

# Retrieve agent
orchestrator = agent_registry.get_agent("orchestrator")

# List all agents
all_agents = agent_registry.list_agents()

# Clear registry (shutdown)
agent_registry.clear()
```

## Agent Statistics

All agents track performance:

```python
agent = agent_registry.get_agent("fuzzy_detector")
stats = agent.get_status()

# Returns:
# {
#   "status": "ready",
#   "requests_processed": 1234,
#   "average_response_time_ms": 150,
#   "errors": 5,
#   "cache_hits": 890,
#   "cache_misses": 344
# }
```

## Adding a Custom Agent

```python
from agents.base import BaseAgent, AgentContract, AgentCapability

class MyCustomAgent(BaseAgent):
    def __init__(self, agent_id: str):
        super().__init__(agent_id)

    def get_contract(self) -> AgentContract:
        return AgentContract(
            name="MyCustomAgent",
            version="1.0.0",
            capabilities=[
                AgentCapability(name="my_method", description="...")
            ]
        )

    async def process_request(self, method: str, params: dict) -> dict:
        if method == "my_method":
            return await self._handle_my_method(params)
        raise ValueError(f"Unknown method: {method}")

    async def _handle_my_method(self, params: dict) -> dict:
        # Implementation
        return {"result": "success"}
```

Register in `api/server.py`:

```python
async def register_agents():
    # ... existing agents ...
    my_custom = MyCustomAgent("my_custom")
    agent_registry.register_agent(my_custom)
```

## Usage Examples

### Using Orchestrator Agent

```python
import asyncio
from agents.orchestrator import OrchestratorAgent

async def run_validation_workflow():
    """Run a complete validation workflow using OrchestratorAgent."""
    orchestrator = OrchestratorAgent()

    # Validate single file
    result = await orchestrator.process_request(
        method="validate_file",
        params={
            "file_path": "docs/tutorial.md",
            "content": "# Tutorial\n\nContent here",
            "family": "words",
            "validation_types": ["yaml", "markdown", "truth"]
        }
    )

    return result

# Run the workflow
result = asyncio.run(run_validation_workflow())
print(f"Validation ID: {result['validation_id']}")
print(f"Status: {result['status']}")
print(f"Issues: {len(result['issues'])}")
```

### Using TruthManager Agent

```python
import asyncio
from agents.truth_manager import TruthManagerAgent

async def load_plugins():
    """Load and search plugin definitions."""
    truth_manager = TruthManagerAgent()

    # Load truth data for 'words' family
    result = await truth_manager.process_request(
        method="load_truth_data",
        params={"family": "words"}
    )

    plugins = result['plugins']
    print(f"Loaded {len(plugins)} plugins")

    # Search for specific plugin
    search_result = await truth_manager.process_request(
        method="search_plugins",
        params={
            "family": "words",
            "query": "AutoSave"
        }
    )

    return search_result

# Run
results = asyncio.run(load_plugins())
```

### Using Fuzzy Detector Agent

```python
import asyncio
from agents.fuzzy_detector import FuzzyDetectorAgent

async def detect_plugins_in_content():
    """Detect plugin mentions using fuzzy matching."""
    detector = FuzzyDetectorAgent()

    content = """
    The Document plugin enables loading Word files.
    Use AutoSave to prevent data loss.
    The PDF converter creates output.
    """

    result = await detector.process_request(
        method="detect_plugins",
        params={
            "content": content,
            "family": "words",
            "context_window_chars": 200
        }
    )

    detections = result['detections']
    print(f"Detected {len(detections)} plugin mentions:")
    for detection in detections:
        print(f"  - {detection['plugin_id']}: {detection['confidence']:.2%}")

# Run
asyncio.run(detect_plugins_in_content())
```

### Using Content Validator Agent

```python
import asyncio
from agents.content_validator import ContentValidatorAgent

async def validate_content_comprehensive():
    """Run comprehensive content validation."""
    validator = ContentValidatorAgent()

    content = """---
title: Tutorial
description: A tutorial document
---

# Tutorial

Enable AutoSave feature for automatic saves.
"""

    result = await validator.process_request(
        method="validate_content",
        params={
            "content": content,
            "file_path": "tutorial.md",
            "family": "words",
            "validation_types": ["yaml", "markdown", "truth"]
        }
    )

    print(f"Status: {result['status']}")
    print(f"Issues found: {len(result['issues'])}")
    for issue in result['issues']:
        print(f"  - [{issue['level']}] {issue['message']}")

# Run
asyncio.run(validate_content_comprehensive())
```

### Querying Agent Status

```python
import requests

def get_all_agents_status():
    """Get status of all registered agents."""
    response = requests.get('http://localhost:8080/agents')
    agents = response.json()['agents']

    print(f"Total agents: {len(agents)}\n")
    for agent in agents:
        print(f"Agent: {agent['agent_id']}")
        print(f"  Type: {agent['agent_type']}")
        print(f"  Status: {agent['status']}")
        print(f"  Capabilities: {len(agent['contract']['capabilities'])}")

def get_specific_agent(agent_id: str):
    """Get details for specific agent."""
    response = requests.get(f'http://localhost:8080/agents/{agent_id}')
    agent = response.json()

    print(f"Agent: {agent['agent_id']}")
    print(f"Type: {agent['agent_type']}")
    print(f"Status: {agent['status']}")
    print("\nCapabilities:")
    for capability in agent['contract']['capabilities']:
        print(f"  - {capability['name']}: {capability['description']}")

# Usage
get_all_agents_status()
get_specific_agent('fuzzy_detector')
```

## Troubleshooting

**Agent not responding:**
```bash
curl http://localhost:8080/agents/<agent_id>
```

**High response times:**
```bash
# Check statistics
curl http://localhost:8080/agents | jq '.agents[] | {id:.agent_id, avg_ms:.statistics.average_response_time_ms}'
```

**Clear agent cache:**
```python
from agents.base import agent_registry
agent = agent_registry.get_agent("fuzzy_detector")
agent.clear_cache()
```

See [Troubleshooting Guide](troubleshooting.md) for more solutions.

---

## Modular Validator Architecture

**Location**: `agents/validators/`
**Purpose**: Modular, extensible validation system replacing monolithic ContentValidatorAgent

### Architecture Overview

The modular validator architecture provides:

- **Separation of Concerns**: Each validator handles one validation type
- **Easy Extension**: Add new validators by implementing BaseValidatorAgent
- **Individual Control**: Enable/disable validators independently
- **Backward Compatibility**: Falls back to legacy ContentValidator when needed
- **Dynamic Discovery**: Validators auto-register with router

### BaseValidatorAgent

**Location**: `agents/validators/base_validator.py`
**Purpose**: Abstract base class for all validators

#### Interface

```python
from abc import ABC, abstractmethod

class BaseValidatorAgent(ABC):
    @abstractmethod
    async def validate(self, content: str, context: dict) -> ValidationResult:
        """
        Validate content and return structured result.

        Args:
            content: Content to validate
            context: Additional context (file_path, family, etc.)

        Returns:
            ValidationResult with issues, confidence, auto_fixable flag
        """
        pass
```

#### ValidationResult Schema

```python
{
    "issues": [
        {
            "level": "error|warning|info",
            "category": "yaml|markdown|code|link|structure|truth|seo",
            "message": "Description of the issue",
            "line": 42,  # Optional line number
            "suggestion": "How to fix",
            "auto_fixable": true,
            "confidence": 0.95
        }
    ],
    "confidence": 0.85,  # Overall validation confidence
    "metrics": {...}  # Validation-specific metrics
}
```

### ValidatorRouter

**Location**: `agents/validators/router.py`
**Purpose**: Routes validation requests to appropriate modular validators

#### Key Features

- Maintains validator registry
- Falls back to ContentValidator for unknown types
- Tracks routing decisions for debugging
- Supports feature flags for gradual rollout

#### Configuration

```yaml
# config/validators.yaml
validators:
  enabled: true
  use_modular: true  # Use modular validators
  fallback_to_legacy: true  # Fallback to ContentValidator if modular fails
  validators:
    yaml: true
    markdown: true
    code: true
    link: true
    structure: true
    truth: true
    seo: true
```

#### Usage

```python
from agents.validators.router import validator_router

# Route validation
result = await validator_router.route_validation(
    validation_type="yaml",
    content=content,
    context={"file_path": "example.md"}
)

# Get routing info
info = validator_router.get_routing_info()
# {
#   "yaml": "YamlValidatorAgent",
#   "markdown": "MarkdownValidatorAgent",
#   ...
# }
```

### Modular Validators

#### 1. YamlValidatorAgent

**Location**: `agents/validators/yaml_validator.py`
**Purpose**: YAML frontmatter validation

**Validates:**
- YAML syntax correctness
- Required fields presence (title, description, etc.)
- Field type validation
- YAML indentation
- Duplicate keys

**Example Issues:**
- `Missing required field 'title' in frontmatter`
- `Invalid YAML syntax at line 3: unclosed string`
- `Field 'date' must be a string, got int`

#### 2. MarkdownValidatorAgent

**Location**: `agents/validators/markdown_validator.py`
**Purpose**: Markdown structure and syntax validation

**Validates:**
- Heading hierarchy (no skipped levels)
- List formatting (consistent indentation)
- Inline formatting (balanced markers)
- Code block syntax
- Table structure

**Example Issues:**
- `Heading hierarchy violated: h1 → h3 (skipped h2)`
- `Unbalanced inline code markers at line 42`
- `Inconsistent list indentation`

#### 3. CodeValidatorAgent

**Location**: `agents/validators/code_validator.py`
**Purpose**: Code block validation

**Validates:**
- Language identifier presence
- Syntax correctness (basic validation)
- Code block closure
- Indentation consistency

**Example Issues:**
- `Code block missing language identifier at line 50`
- `Unclosed code block starting at line 75`
- `Invalid C# syntax in code block`

#### 4. LinkValidatorAgent

**Location**: `agents/validators/link_validator.py`
**Purpose**: Link and URL validation

**Validates:**
- Broken links (HTTP status checks)
- Invalid anchors
- Malformed URLs
- Missing link targets
- Timeout handling

**Configuration:**
```yaml
link_validator:
  enabled: true
  timeout_seconds: 5
  max_retries: 2
  check_external_links: true
  allowed_domains: ["*.aspose.com", "github.com"]
```

**Example Issues:**
- `Broken link: http://example.com/404 (404 Not Found)`
- `Invalid anchor: #nonexistent-section`
- `Malformed URL at line 30`

#### 5. StructureValidatorAgent

**Location**: `agents/validators/structure_validator.py`
**Purpose**: Document structure validation

**Validates:**
- Title presence
- Section organization
- Minimum content length
- TOC structure
- Document completeness

**Example Issues:**
- `Document missing title (h1)`
- `Section 'Installation' appears before 'Overview'`
- `Document too short (< 100 words)`

#### 6. TruthValidatorAgent

**Location**: `agents/validators/truth_validator.py`
**Purpose**: Truth data and terminology validation

**Validates:**
- Plugin name accuracy
- Declared vs used plugins
- Terminology consistency
- Truth data alignment
- Plugin combination rules

**Example Issues:**
- `Plugin 'AutoSave' used but not declared`
- `Invalid plugin combination: Merger requires Document processor`
- `Inconsistent terminology: 'SaveFormat.Pdf' vs 'PdfSaveFormat'`

#### 7. SeoValidatorAgent

**Location**: `agents/validators/seo_validator.py`
**Purpose**: SEO metadata and heading size validation

**Validates:**
- Meta description presence and length
- Title tag optimization
- Heading size compliance (dual mode)
- Keyword density
- Alt text for images

**Dual Mode:**
1. **SEO Mode**: Validates meta description, title, keywords
2. **Heading Size Mode**: Validates heading character limits

**Configuration:**
```yaml
# config/seo.yaml
seo_validator:
  enabled: true
  mode: seo  # or "heading_sizes"
  meta_description:
    min_length: 120
    max_length: 160
  title:
    min_length: 30
    max_length: 60

# Note: heading_sizes is now part of config/seo.yaml under seo.heading_sizes
# See config/seo.yaml for the unified SEO configuration
```

**Example Issues:**
- `Meta description too short (85 chars, min 120)`
- `h1 heading exceeds limit: 75 chars (max 60)`
- `Missing alt text for image at line 42`

### Adding a Custom Validator

Create a new validator by extending `BaseValidatorAgent`:

```python
# agents/validators/my_custom_validator.py
from agents.validators.base_validator import BaseValidatorAgent, ValidationResult

class MyCustomValidator(BaseValidatorAgent):
    def __init__(self):
        super().__init__(
            validator_id="my_custom",
            validator_name="MyCustomValidator",
            version="1.0.0"
        )

    async def validate(self, content: str, context: dict) -> ValidationResult:
        issues = []

        # Your validation logic
        if "forbidden_word" in content.lower():
            issues.append({
                "level": "error",
                "category": "custom",
                "message": "Forbidden word detected",
                "suggestion": "Remove forbidden word",
                "auto_fixable": False,
                "confidence": 1.0
            })

        return ValidationResult(
            issues=issues,
            confidence=1.0 if not issues else 0.5,
            metrics={"words_checked": len(content.split())}
        )
```

Register in `agents/validators/__init__.py`:

```python
from .my_custom_validator import MyCustomValidator

# Auto-registration happens in __init__
```

### Migration from Legacy ContentValidator

**Phase 1: Parallel Operation** (Current)
- Modular validators available alongside ContentValidator
- Router decides which to use based on config
- Fallback to legacy for unsupported types

**Phase 2: Gradual Rollout**
- Enable modular validators per validation type
- Monitor performance and accuracy
- Collect metrics for comparison

**Phase 3: Full Migration**
- Disable legacy ContentValidator
- Remove fallback code
- Archive ContentValidator

**Backward Compatibility:**
```python
# Old code still works
result = await content_validator.validate_content(
    content=content,
    validation_types=["yaml", "markdown"]
)

# New code uses router
result = await validator_router.route_validation(
    validation_type="yaml",
    content=content,
    context={}
)
```

### Performance Comparison

| Validator Type | Legacy (ms) | Modular (ms) | Improvement |
|----------------|-------------|--------------|-------------|
| YAML           | 45          | 25           | 44% faster  |
| Markdown       | 120         | 60           | 50% faster  |
| Code           | 80          | 40           | 50% faster  |
| Links          | 200         | 180          | 10% faster  |
| Structure      | 30          | 15           | 50% faster  |
| Truth          | 150         | 100          | 33% faster  |
| SEO            | 60          | 35           | 42% faster  |

**Benefits:**
- **50% average performance improvement** due to focused validation
- **Reduced memory footprint** (150-330 lines per validator vs 2100 monolithic)
- **Easier maintenance** and testing
- **Faster development** of new validators (2-4 hours vs 1-2 days)
