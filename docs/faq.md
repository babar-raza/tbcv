# TBCV Frequently Asked Questions (FAQ)

**Last Updated**: December 2025
**TBCV Version**: 2.0.0

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Configuration](#configuration)
3. [Usage](#usage)
4. [Agents](#agents)
5. [API](#api)
6. [Database](#database)
7. [Performance](#performance)
8. [Troubleshooting](#troubleshooting)
9. [Development](#development)
10. [Deployment](#deployment)

---

## Getting Started

### What is TBCV and what does it do?

**TBCV** (Truth-Based Content Validation System) is an intelligent content validation and enhancement platform for technical documentation. It doesn't generate content from scratch—instead, it validates existing markdown files against rules and "truth data" (plugin definitions), detects plugin usage patterns, generates actionable recommendations for improvements, and applies approved enhancements through a human-in-the-loop workflow.

The system specializes in validating Aspose product documentation by fuzzy-matching code references to plugin definitions, ensuring documentation quality and consistency, and providing automated enhancement suggestions with audit trails.

**See also**: [Architecture Overview](architecture.md), [What TBCV Does (README)](../README.md#what-tbcv-does)

---

### What are the system requirements for TBCV?

TBCV has minimal system requirements and can run on most development machines:

- **Operating System**: Windows 10+, Linux (any distribution), or macOS
- **Python**: 3.8+ (3.11+ recommended for better performance)
- **RAM**: 2GB minimum, 4GB+ recommended
- **Storage**: 500MB for application code + database + logs
- **Network**: Internet access optional (only for external code fetching, link validation, Ollama/LLM)

Optional dependencies:
- **Ollama** (for semantic LLM validation): Requires ~8GB RAM for running LLM models
- **PostgreSQL** (for production deployments): Any recent version
- **Redis** (for distributed caching): Version 5.0+

TBCV uses SQLite by default, so PostgreSQL is not required for development or single-node deployments.

**See also**: [Deployment Prerequisites](deployment.md#prerequisites), [Configuration Guide](configuration.md)

---

### How do I install and set up TBCV?

Installation is straightforward—follow these steps:

```bash
# 1. Clone the repository
git clone <repository-url>
cd tbcv

# 2. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialize the database
python -c "from core.database import db_manager; db_manager.initialize_database()"

# 5. Verify installation
python main.py --help
```

After installation, you can start the server:

```bash
# Start API server
python main.py --mode api --host localhost --port 8080

# Access the application
# - API docs: http://localhost:8080/docs
# - Web dashboard: http://localhost:8080/dashboard
# - Health check: http://localhost:8080/health
```

**See also**: [Quick Start (README)](../README.md#quick-start), [Deployment Guide](deployment.md)

---

### How do I run my first validation?

After starting the server, you can validate a file via CLI or API:

**Via CLI**:
```bash
python -m cli.main validate-file docs/tutorial.md --family words --format text
```

**Via API (curl)**:
```bash
curl -X POST http://localhost:8080/api/validate \
  -H "Content-Type: application/json" \
  -d '{
    "content": "# My Documentation\n\nUse Document.Save() to save.",
    "file_path": "tutorial.md",
    "family": "words"
  }'
```

**Via Web Dashboard**:
1. Open http://localhost:8080/dashboard
2. Click "New Validation"
3. Select a file or paste markdown content
4. Choose product family (words, pdf, cells, slides)
5. Click "Validate"

The system will return validation results with any issues found and recommendations for improvements.

**See also**: [CLI Usage](cli_usage.md), [API Reference](api_reference.md), [Common Use Cases (README)](../README.md#common-use-cases)

---

### What documentation families does TBCV support?

TBCV has built-in support for the following Aspose product families:

| Family | Products | Example Plugin | Truth File |
|--------|----------|----------------|-----------|
| **words** | Aspose.Words for .NET, Java, C++, Python, JavaScript | Document.Save() | aspose_words_plugins_truth.json |
| **pdf** | Aspose.PDF for .NET, Java, C++, Python | Document.Save() | aspose_pdf_plugins_truth.json |
| **cells** | Aspose.Cells for .NET, Java, C++, Python | Workbook.Save() | aspose_cells_plugins_truth.json |
| **slides** | Aspose.Slides for .NET, Java, C++, Python | Presentation.Save() | aspose_slides_plugins_truth.json |
| **email** | Aspose.Email for .NET, Java, Python | MailMessage.Save() | aspose_email_plugins_truth.json |

Each family has its own truth data file in `truth/` directory. You can extend TBCV to support additional families by creating new truth files.

**See also**: [Truth Store Documentation](truth_store.md), [Project Structure (README)](../README.md#project-structure)

---

## Configuration

### Where are TBCV configuration files located?

Configuration files are organized in the `config/` directory:

| File | Purpose |
|------|---------|
| **config/main.yaml** | Master system configuration (server, agents, cache, database) |
| **config/agent.yaml** | Per-agent settings and thresholds |
| **config/validation_flow.yaml** | Validation orchestration, tiers, profiles, family overrides |
| **config/cache.yaml** | L1 (memory) and L2 (disk) cache settings |
| **config/seo.yaml** | SEO validation rules (title length, heading limits) |
| **config/truth.yaml** | Truth validation configuration |
| **config/llm.yaml** | LLM settings (optional, disabled by default) |
| **config/code.yaml** | Code block validation rules |
| **config/links.yaml** | Link validation settings |
| **config/markdown.yaml** | Markdown syntax rules |
| **config/structure.yaml** | Document structure validation rules |
| **config/frontmatter.yaml** | YAML frontmatter validation |

Plus runtime data:
- **data/tbcv.db** - SQLite database
- **data/logs/** - Application logs
- **data/cache/** - L2 cache storage

**See also**: [Configuration Guide](configuration.md), [Validation Flow](validation_flow.yaml)

---

### How do I enable/disable validators or features?

Validators and features can be controlled via two methods:

**Method 1: Configuration Files**

Edit `config/validation_flow.yaml` to enable/disable validators:

```yaml
validation_flow:
  tiers:
    tier_1:
      validators:
        - yaml       # ✓ Enabled
        - markdown   # ✓ Enabled
    tier_2:
      validators:
        - code       # ✓ Enabled
        - links      # ✓ Enabled (slow, can disable)
    tier_3:
      validators:
        - fuzzy      # ✓ Optional, slower
        - truth      # ✓ Optional
        - llm        # ✗ Disabled by default (requires Ollama)
```

**Method 2: Environment Variables**

Override any config setting via environment variables with `TBCV_` prefix:

```bash
# Enable LLM validation
export TBCV_LLM_VALIDATOR__ENABLED=true

# Change Fuzzy detector threshold
export TBCV_FUZZY_DETECTOR__SIMILARITY_THRESHOLD=0.9

# Disable link validation
export TBCV_LINK_VALIDATOR__ENABLED=false

# Increase server timeout
export TBCV_SERVER__REQUEST_TIMEOUT_SECONDS=60
```

**Method 3: CLI Flags**

Some CLI commands accept flags to override validation settings:

```bash
python -m cli.main validate-file file.md \
  --validators yaml,markdown,code \
  --skip-llm \
  --skip-links
```

**See also**: [Configuration Guide](configuration.md), [Validation Flow Configuration](validation_flow.yaml), [CLI Usage](cli_usage.md)

---

### How do I configure validation profiles (strict/default/quick)?

TBCV supports validation profiles for different use cases. Configure in `config/validation_flow.yaml`:

```yaml
validation_flow:
  profiles:
    quick:
      # Fast validation: only syntax checks
      validators: [yaml, markdown]
      timeout_seconds: 5

    default:
      # Balanced: syntax + content analysis
      validators: [yaml, markdown, code, links, structure, seo]
      timeout_seconds: 30

    strict:
      # Comprehensive: all validators including semantic checks
      validators: [yaml, markdown, code, links, structure, seo, fuzzy, truth, llm]
      timeout_seconds: 120
```

Then use in CLI or API:

```bash
# CLI
python -m cli.main validate-file file.md --profile strict

# API
curl -X POST http://localhost:8080/api/validate \
  -H "Content-Type: application/json" \
  -d '{"content": "...", "file_path": "file.md", "profile": "strict"}'
```

Family-specific overrides:

```yaml
validation_flow:
  family_overrides:
    words:
      profile: strict        # Always use strict for Words
    pdf:
      validators: [yaml, markdown]  # Limited validation for PDF
```

**See also**: [Validation Flow Configuration](../config/validation_flow.yaml), [Configuration Guide](configuration.md#validation-tiers)

---

### How do I configure feature flags and performance settings?

Feature flags control optional functionality. Configure in `config/main.yaml`:

```yaml
system:
  features:
    fuzzy_detection: true        # Enable plugin pattern matching
    truth_validation: true       # Validate against plugin definitions
    content_enhancement: true    # Allow content improvements
    llm_validation: false        # Disable LLM (requires Ollama)
    html_sanitization: true      # Security feature
    link_validation: true        # Check link validity
    cache_enabled: true          # Use caching

performance:
  max_concurrent_workflows: 50   # Max simultaneous validations
  worker_pool_size: 4            # Worker threads for batch processing
  memory_limit_mb: 2048          # Max memory usage
  cpu_limit_percent: 80          # Max CPU usage
  cache:
    max_entries: 1000            # Max cached items
    ttl_seconds: 3600            # Cache time-to-live
```

Performance tuning tips:

- **Increase workers** for batch processing: `worker_pool_size: 8`
- **Reduce memory** for constrained systems: `memory_limit_mb: 512`
- **Disable expensive validators**: Set `link_validation: false` or use "quick" profile
- **Increase cache TTL** for repeated validations: `ttl_seconds: 86400` (24 hours)
- **Enable fuzzy caching** to reuse plugin detections

**See also**: [Performance Metrics](performance_metrics.md), [Configuration Reference](configuration.md#performance)

---

### How do I set environment-specific configurations?

TBCV supports multiple configuration environments:

**Method 1: Environment Variable**

```bash
# Development (debug enabled, LLM allowed)
export TBCV_ENVIRONMENT=development
python main.py --mode api

# Staging (validation warnings logged)
export TBCV_ENVIRONMENT=staging
python main.py --mode api

# Production (strict validation, security enforced)
export TBCV_ENVIRONMENT=production
python main.py --mode api
```

**Method 2: Separate Config Files**

Create environment-specific configs:

```
config/
├── main.yaml                 # Shared defaults
├── main.development.yaml     # Development overrides
├── main.staging.yaml         # Staging overrides
└── main.production.yaml      # Production overrides
```

Load specific environment:

```bash
TBCV_CONFIG_ENVIRONMENT=production python main.py --mode api
```

**Method 3: Config Hierarchy**

TBCV loads configuration in this order (later overrides earlier):

1. `config/main.yaml` (base)
2. `config/main.{environment}.yaml` (environment-specific)
3. Environment variables (highest priority)
4. CLI flags

Example production-safe configuration:

```yaml
# config/main.production.yaml
system:
  debug: false
  log_level: "warning"
  environment: "production"

server:
  request_timeout_seconds: 60
  max_concurrent_workflows: 100

security:
  access_control: "BLOCK"     # Enforce MCP-first architecture
  require_api_key: true       # Require authentication
```

**See also**: [Configuration Guide](configuration.md), [Deployment Guide](deployment.md#production-deployment)

---

## Usage

### How do I validate a single markdown file?

You can validate a file via CLI, API, or web dashboard:

**CLI Method** (Recommended for local development):

```bash
# Basic validation
python -m cli.main validate-file docs/tutorial.md --family words

# With specific validators
python -m cli.main validate-file docs/tutorial.md --validators yaml,markdown,code

# With output format
python -m cli.main validate-file docs/tutorial.md --format json > results.json

# Verbose mode with detailed output
python -m cli.main validate-file docs/tutorial.md --verbose --debug
```

**API Method** (Recommended for integrations):

```bash
# File content validation
curl -X POST http://localhost:8080/api/validate \
  -H "Content-Type: application/json" \
  -d '{
    "content": "# Title\n\nContent here",
    "file_path": "tutorial.md",
    "family": "words"
  }'

# Response includes:
# - validation_id: Unique identifier
# - status: "valid" or "invalid"
# - errors: List of issues found
# - warnings: Non-critical issues
# - recommendations: Improvement suggestions
```

**Web Dashboard Method** (Best for non-technical users):

1. Open http://localhost:8080/dashboard
2. Click "New Validation" or drag-and-drop file
3. Select product family
4. Click "Validate"
5. Review results and recommendations

The validation result includes severity levels (error/warning/info), line numbers, and actionable recommendations.

**See also**: [CLI Usage](cli_usage.md), [API Reference](api_reference.md), [Web Dashboard](web_dashboard.md)

---

### How do I validate multiple files in batch?

For processing multiple files efficiently:

**CLI - Batch Directory Validation**:

```bash
# Validate all markdown files in a directory
python -m cli.main validate-directory docs/ \
  --pattern "*.md" \
  --family words \
  --workers 4 \
  --output results.json

# Options:
# --pattern: File glob pattern (*.md, *.py, etc.)
# --workers: Parallel workers (default: 4)
# --output: Save results to file
# --profile: Use validation profile (quick, default, strict)
```

**API - Batch Workflow**:

```bash
# Start batch validation workflow
curl -X POST http://localhost:8080/workflows/validate-directory \
  -H "Content-Type: application/json" \
  -d '{
    "directory_path": "./docs",
    "file_pattern": "*.md",
    "family": "words",
    "max_workers": 4
  }'

# Response includes workflow_id for monitoring
# {
#   "workflow_id": "wf_123456",
#   "status": "running",
#   "progress": {"processed": 5, "total": 20}
# }

# Check progress
curl http://localhost:8080/workflows/wf_123456

# Get results when complete
curl http://localhost:8080/workflows/wf_123456/results
```

**Performance Tips**:

- Adjust `--workers` based on CPU cores (2-4 for average machine)
- Use "quick" profile for fast results: `--profile quick`
- Process files in smaller batches if memory-constrained
- Enable caching to reuse results: `--cache`

**See also**: [Batch Processing](cli_usage.md#batch-operations), [Workflows](workflows.md)

---

### How do I review and approve recommendations?

TBCV generates suggestions for improvements, which you must review before applying:

**List Recommendations**:

```bash
# CLI: List all recommendations for a validation
python -m cli.main recommendations list --validation-id abc123

# API: Get recommendations
curl http://localhost:8080/api/recommendations?validation_id=abc123
```

**Review Process**:

1. **List recommendations** for a validation
2. **Review each suggestion** (automatic or manual)
3. **Approve** recommendations you want to apply
4. **Reject** recommendations you disagree with
5. **Apply** approved recommendations to content

**CLI Workflow**:

```bash
# 1. Validate file
python -m cli.main validate-file file.md --family words

# 2. List recommendations from validation
python -m cli.main recommendations list --validation-id <id>

# 3. Review each recommendation
# Shows: recommendation ID, type, confidence, proposed change

# 4. Approve recommendation
python -m cli.main recommendations review <rec-id> --status approved --notes "LGTM"

# 5. Apply approved recommendations
python -m cli.main recommendations enhance file.md \
  --validation-id <id> \
  --backup \
  --output enhanced.md
```

**API Workflow**:

```bash
# Review a recommendation
curl -X POST http://localhost:8080/api/recommendations/<rec-id>/review \
  -H "Content-Type: application/json" \
  -d '{
    "status": "accepted",
    "reviewer": "john.doe",
    "notes": "Looks good, approved for enhancement"
  }'

# Apply all approved recommendations
curl -X POST http://localhost:8080/api/enhance \
  -H "Content-Type: application/json" \
  -d '{
    "validation_id": "<id>",
    "file_path": "file.md",
    "preview": true
  }'
```

**Recommendation Types**:

- **Plugin Link**: Add hyperlink to plugin documentation
- **Info Text**: Insert explanatory text about plugins
- **Fix Formatting**: Correct markdown or YAML issues
- **Add Examples**: Suggest code examples
- **Improve Clarity**: Reword unclear sections

**See also**: [Enhancement Workflow](enhancement_workflow.md), [Recommendation Management](cli_usage.md#recommendations)

---

### How do I apply enhancements to my content?

After approving recommendations, apply them to create enhanced versions:

**Preview Before Applying**:

```bash
# CLI: Preview changes without saving
python -m cli.main recommendations enhance file.md \
  --validation-id <id> \
  --preview

# Shows proposed changes without writing to file
```

**Apply Enhancements**:

```bash
# CLI: Apply with automatic backup
python -m cli.main recommendations enhance file.md \
  --validation-id <id> \
  --backup \
  --output enhanced.md

# API: Apply enhancements
curl -X POST http://localhost:8080/api/enhance \
  -H "Content-Type: application/json" \
  -d '{
    "validation_id": "<id>",
    "file_path": "file.md",
    "content": "existing markdown content",
    "preview": false,
    "create_backup": true,
    "output_path": "enhanced.md"
  }'
```

**Compare Original vs Enhanced**:

```bash
# View enhancement comparison
python -m cli.main recommendations compare \
  --original-file file.md \
  --enhanced-file enhanced.md

# Shows side-by-side diff
```

**Rollback if Needed**:

```bash
# Restore from backup if enhancement didn't work as expected
cp file.md.bak file.md
```

**Enhancement Safety**:

- Always use `--backup` flag to create backups
- Preview changes first with `--preview`
- Review diffs before committing
- Test in non-production environment first
- TBCV tracks all enhancements in database for audit trail

**See also**: [Enhancement Workflow](enhancement_workflow.md), [Recommendation Enhancer](agents.md#recommendation-enhancer)

---

### What validation types are available?

TBCV supports 8 different validation types organized in tiers:

**Tier 1 - Fast Structural Validators** (Run in parallel):

| Validator | Purpose | Speed | What It Checks |
|-----------|---------|-------|----------------|
| **yaml** | Frontmatter validation | <50ms | YAML syntax, required fields, data types |
| **markdown** | Markdown syntax | <50ms | Heading hierarchy, list formatting, inline formatting |
| **structure** | Document organization | <100ms | Section ordering, completeness, required sections |

**Tier 2 - Content Analysis Validators** (Run in parallel):

| Validator | Purpose | Speed | What It Checks |
|-----------|---------|-------|----------------|
| **code** | Code block validation | <100ms | Language tags, fence closure, syntax highlighting |
| **links** | Link validation | 1-5s | HTTP status codes, anchor validity, broken links |
| **seo** | SEO optimization | <50ms | Meta titles, heading lengths, keyword density |

**Tier 3 - Advanced Validators** (Sequential, optional):

| Validator | Purpose | Speed | What It Checks | Requirements |
|-----------|---------|-------|----------------|--------------|
| **fuzzy** | Plugin pattern detection | 100-500ms | Fuzzy matching against plugin truth data | Truth files loaded |
| **truth** | Plugin validation | 100-500ms | Validates detected plugins against definitions | Fuzzy detector run first |
| **llm** | Semantic validation | 5-30s | LLM semantic understanding of plugin usage | Ollama running (optional) |

**Run Specific Validators**:

```bash
# CLI: Use only certain validators
python -m cli.main validate-file file.md --validators yaml,markdown,code

# Skip validators
python -m cli.main validate-file file.md --skip-llm --skip-links

# Use validation profile
python -m cli.main validate-file file.md --profile quick  # yaml, markdown only
```

**See also**: [Modular Validators](modular_validators.md), [Validation Flow](../config/validation_flow.yaml)

---

### How do I handle special cases like code blocks or frontmatter?

TBCV has specialized handling for different content types:

**Code Blocks**:

```markdown
# Markdown with code blocks

## Example with language tag (GOOD)
```python
# This gets validated for syntax
import aspose.words as aw
doc = aw.Document()
```

## Example without language tag (WARNING)
```
code here - can't validate syntax
```

# Code block validation checks:
# - Language identifier present
# - Opening and closing fences matched
# - Syntax highlighting available
# - Indentation consistent
```

**YAML Frontmatter**:

```markdown
---
title: "Documentation Title"
description: "Brief description"
author: "Author Name"
date: 2025-12-03
tags: [tutorial, advanced]
product: words
---

# Content starts here
```

TBCV validates:
- YAML syntax correctness
- Required fields present
- Data types correct
- No duplicate keys
- Proper YAML escaping

**Inline Code**:

```markdown
# Inline code with backticks

Use `Document.Save()` method to save documents.
The `Document` class has these members:
- `Document()` - constructor
- `Save()` - save method
```

Inline code is analyzed for:
- Plugin references
- Method/class names
- Consistency across document

**Links and References**:

```markdown
# Different link formats

## External link
See [plugin documentation](https://products.aspose.com/words/net)

## Relative link
See [tutorial](./tutorial.md)

## Anchor link
Jump to [section](#heading)
```

Link validation checks:
- Valid HTTP/HTTPS URLs
- Anchors exist in local files
- No broken links
- Performance (redirects, timeouts)

**Tables**:

```markdown
| Feature | Status | Notes |
|---------|--------|-------|
| Validation | ✓ | All content types |
| Enhancement | ✓ | Approved recommendations |
```

**See also**: [Markdown Validator](agents.md#markdown-validator), [Code Validator](agents.md#code-validator), [YAML Validator](agents.md#yaml-validator)

---

## Agents

### What are TBCV agents and how do they work?

TBCV uses a **multi-agent architecture** with 19 specialized agents that coordinate via message passing to validate and enhance content. Each agent handles a specific aspect of validation:

**Core Agents** (9 agents):
- **OrchestratorAgent**: Coordinates workflows, manages concurrency
- **TruthManagerAgent**: Loads and indexes plugin definitions
- **FuzzyDetectorAgent**: Detects plugin usage via fuzzy matching
- **ContentValidatorAgent**: Legacy validator (deprecated)
- **ContentEnhancerAgent**: Applies content improvements
- **LLMValidatorAgent**: Optional semantic validation via Ollama
- **CodeAnalyzerAgent**: Analyzes code quality and security
- **RecommendationAgent**: Generates improvement suggestions
- **EnhancementAgent**: Applies approved recommendations

**Validator Agents** (7 agents):
- YamlValidatorAgent, MarkdownValidatorAgent, CodeValidatorAgent
- LinkValidatorAgent, StructureValidatorAgent, TruthValidatorAgent, SeoValidatorAgent

**Pipeline Agents** (3 agents):
- EditValidator, RecommendationEnhancer, RecommendationCriticAgent

**How Agents Coordinate**:

1. **Input**: User submits file for validation
2. **Orchestrator**: Coordinates the validation workflow
3. **Truth Manager**: Loads plugin definitions
4. **Validators**: Run in parallel/sequence based on configuration
5. **Fuzzy Detector**: Detects plugin usage patterns
6. **LLM Validator**: Optional semantic validation
7. **Recommendation Agent**: Generates improvement suggestions
8. **Enhancement**: Applies approved changes
9. **Output**: Returns enhanced content + audit trail

All agents follow the **MCP-first architecture** and are protected by access control guards.

**See also**: [Agents Reference](agents.md), [Architecture Overview](architecture.md)

---

### How does the fuzzy detector work?

The **FuzzyDetectorAgent** uses advanced pattern matching to detect plugin usage even when code doesn't exactly match plugin definitions:

**Algorithm**:

1. **Parse plugin truth data**: Load all known plugins from `truth/*.json`
2. **Build pattern library**: Create search patterns (method names, class names, etc.)
3. **Scan content**: Find references in markdown/code
4. **Fuzzy matching**: Use multiple similarity algorithms:
   - **Levenshtein distance**: String edit distance (handles typos)
   - **Jaro-Winkler**: Weighted similarity (handles prefixes)
5. **Confidence scoring**: Calculate match probability (0-100%)
6. **Context analysis**: Check surrounding text for relevance
7. **Return detections**: List detected plugins with confidence scores

**Example**:

```markdown
# Input content:
# "Use the Doucment.Sav() method to save files."

Truth data has plugin "Document.Save()"

Fuzzy detection output:
- "Doucment.Sav()" matches "Document.Save()" with 92% confidence
  (catches typo: "Doucment" vs "Document")
```

**Configuration**:

```yaml
fuzzy_detector:
  enabled: true
  similarity_threshold: 0.85      # Min confidence to report match
  context_window_chars: 200       # Text before/after to analyze
  max_patterns: 500               # Cache optimization
  fuzzy_algorithms:
    - "levenshtein"
    - "jaro_winkler"
```

**Confidence Thresholds**:

- **>90%**: Likely match (show as high confidence)
- **80-90%**: Probable match (show as medium confidence)
- **<80%**: Uncertain (show as low confidence)
- **<threshold**: Ignored (not reported)

**Tips for Better Detection**:

- Use consistent naming conventions
- Avoid excessive typos (fuzzy matching helps, but has limits)
- Include context around plugin references
- Keep plugin definitions up-to-date in truth files

**See also**: [Fuzzy Detector Agent](agents.md#fuzzy-detector-agent), [Truth Store](truth_store.md)

---

### How do I customize or extend agents?

TBCV agents are designed for extension and customization:

**Create Custom Agent**:

```python
# agents/custom_agent.py
from agents.base import BaseAgent, AgentContract

class CustomAgent(BaseAgent):
    """Custom validation agent"""

    def __init__(self):
        super().__init__("custom_agent")

    async def process_request(self, method: str, params: dict) -> dict:
        """Handle MCP requests"""
        if method == "validate":
            return await self.validate_content(params)
        return {"error": "Unknown method"}

    async def validate_content(self, params: dict) -> dict:
        """Custom validation logic"""
        content = params.get("content", "")
        # Your validation logic here
        return {
            "status": "success",
            "errors": [],
            "warnings": []
        }

    def get_contract(self) -> AgentContract:
        """Define agent capabilities"""
        return AgentContract(
            methods=["validate"],
            parameters={"validate": {"content": {"type": "string"}}}
        )

    def get_status(self) -> dict:
        """Health check"""
        return {"status": "ready", "processed": 0}
```

**Register Custom Agent**:

```python
# agents/__init__.py
from agents.custom_agent import CustomAgent

AGENTS = {
    "custom_agent": CustomAgent(),
    # ... other agents
}
```

**Create Custom Validator**:

```python
# agents/validators/custom_validator.py
from agents.validators.base_validator import BaseValidatorAgent

class CustomValidatorAgent(BaseValidatorAgent):
    """Custom validator for specific needs"""

    async def validate(self, content: str, file_path: str, config: dict) -> dict:
        """Custom validation logic"""
        issues = []

        if "forbidden_term" in content:
            issues.append({
                "type": "error",
                "message": "Forbidden term detected",
                "severity": "high"
            })

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": []
        }

    def get_validator_name(self) -> str:
        return "custom"

    def get_description(self) -> str:
        return "Custom validation for specific domain"
```

**Customize Validation Rules**:

```yaml
# config/validation_flow.yaml
custom_validator:
  enabled: true
  rules:
    - id: rule_1
      pattern: "forbidden_term"
      severity: "error"
      message: "This term is forbidden"
    - id: rule_2
      pattern: "deprecated_method"
      severity: "warning"
      message: "This method is deprecated"
```

**Best Practices**:

- Inherit from BaseAgent or BaseValidatorAgent
- Implement required methods: `process_request`, `get_contract`, `get_status`
- Add configuration support via config files
- Write unit tests for new logic
- Follow MCP-first architecture (no direct CLI/API access)
- Document custom agents in docstrings

**See also**: [Agents Reference](agents.md), [Contributing Guide](development.md), [Architecture Overview](architecture.md)

---

### How do I troubleshoot agent issues?

When agents aren't working correctly:

**Check Agent Status**:

```bash
# CLI: Check all agents
python -m cli.main agents status

# API: Get agent list and status
curl http://localhost:8080/agents

# Response includes:
# - Agent name and ID
# - Status (ready/busy/error)
# - Methods available
# - Statistics (requests processed, errors)
```

**View Agent Logs**:

```bash
# View real-time logs for specific agent
tail -f data/logs/tbcv.log | grep "FuzzyDetectorAgent"

# Search for errors
grep "ERROR" data/logs/tbcv.log | tail -20

# Enable debug logging
export TBCV_LOG_LEVEL=DEBUG
python main.py --mode api
```

**Common Agent Issues**:

| Issue | Symptom | Solution |
|-------|---------|----------|
| **Agent not registered** | 503 Service Unavailable | Check agent initialization in config |
| **Plugin detection failing** | No fuzzy matches found | Verify truth files loaded, check threshold |
| **LLM validation timeout** | Requests hang at 30s | Ensure Ollama running, increase timeout in config |
| **Memory error** | Out of memory during processing | Reduce worker count, enable L2 cache |
| **Database lock** | "database is locked" error | Restart server, check concurrent access |

**Restart Agents**:

```bash
# Restart server (restarts all agents)
# Kill the process
pkill -f "python main.py"

# Restart
python main.py --mode api

# Or reload specific agent
curl -X POST http://localhost:8080/admin/agents/fuzzy-detector/reload
```

**Test Individual Agent**:

```bash
# Via MCP Server (testing interface)
python -m svc.mcp_server --test-agent fuzzy_detector

# Check agent can process requests
curl -X POST http://localhost:8080/agents/fuzzy-detector/test \
  -H "Content-Type: application/json" \
  -d '{"content": "Test content with Document.Save()"}'
```

**See also**: [Agents Reference](agents.md), [Troubleshooting Guide](troubleshooting.md)

---

## API

### What REST endpoints does TBCV provide?

TBCV provides 40+ REST endpoints organized by function:

**Health & Status** (3 endpoints):
- `GET /health` - Full system health check
- `GET /health/live` - Liveness probe (Kubernetes)
- `GET /health/ready` - Readiness probe (Kubernetes)

**Agent Management** (3 endpoints):
- `GET /agents` - List all agents
- `GET /agents/{agent-id}` - Get specific agent info
- `POST /agents/{agent-id}/reload` - Reload agent

**Validation** (8 endpoints):
- `POST /api/validate` - Validate file content
- `POST /api/validate-file` - Validate from file path
- `POST /api/validate-batch` - Batch validation
- `GET /workflows/{id}` - Get workflow status
- `GET /workflows/{id}/results` - Get validation results
- `DELETE /workflows/{id}` - Cancel workflow
- `POST /workflows/validate-directory` - Validate directory
- `GET /workflows` - List all workflows

**Recommendations** (5 endpoints):
- `GET /api/recommendations` - List recommendations
- `GET /api/recommendations/{id}` - Get specific recommendation
- `POST /api/recommendations/{id}/review` - Review recommendation
- `GET /api/recommendations/{id}/details` - Full recommendation details
- `DELETE /api/recommendations/{id}` - Delete recommendation

**Enhancement** (4 endpoints):
- `POST /api/enhance` - Apply enhancements
- `GET /api/enhance/{id}/preview` - Preview enhancement
- `POST /api/enhance/{id}/apply` - Apply enhancement
- `GET /api/enhance/{id}/history` - Enhancement history

**Admin** (8+ endpoints):
- `GET /admin/system` - System info
- `POST /admin/cache/clear` - Clear cache
- `GET /admin/cache/stats` - Cache statistics
- `GET /admin/logs` - View application logs
- `POST /admin/db/backup` - Backup database
- `POST /admin/db/restore` - Restore from backup
- `GET /admin/audit-log` - View audit trail
- `POST /admin/config/reload` - Reload configuration

**Discovery** (2 endpoints):
- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc documentation

**See also**: [API Reference](api_reference.md), [Admin API](admin_api.md)

---

### How do I authenticate with the API?

TBCV supports optional API key authentication:

**Enable Authentication**:

```yaml
# config/main.yaml
server:
  require_api_key: true
  api_key: "your-secure-api-key-here"
```

Or via environment variable:

```bash
export TBCV_SERVER__REQUIRE_API_KEY=true
export TBCV_SERVER__API_KEY="your-api-key"
```

**Use API Key in Requests**:

```bash
# Include X-API-Key header
curl -X POST http://localhost:8080/api/validate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"content": "...", "file_path": "file.md"}'

# Or as query parameter (less secure)
curl http://localhost:8080/api/validate?api_key=your-api-key
```

**Python Example**:

```python
import requests

headers = {
    "X-API-Key": "your-api-key",
    "Content-Type": "application/json"
}

response = requests.post(
    "http://localhost:8080/api/validate",
    headers=headers,
    json={"content": "...", "file_path": "file.md"}
)
```

**JavaScript Example**:

```javascript
const response = await fetch('http://localhost:8080/api/validate', {
    method: 'POST',
    headers: {
        'X-API-Key': 'your-api-key',
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        content: "...",
        file_path: "file.md"
    })
});
```

**Note**: In production, always use HTTPS and rotate API keys regularly. Store keys securely (not in code).

**See also**: [Security Documentation](security.md), [API Reference](api_reference.md)

---

### What are the API rate limits?

TBCV enforces rate limits to protect the system:

**Default Limits**:

```yaml
# config/main.yaml
server:
  rate_limiting:
    enabled: true
    requests_per_minute: 100     # Per IP address
    concurrent_validations: 10   # Max parallel validations
    batch_items_per_request: 1000 # Max files in batch
```

**Rate Limit Headers**:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1701619200
```

**When Limit Exceeded**:

```
HTTP 429 Too Many Requests

{
  "error": "Rate limit exceeded",
  "retry_after": 60,
  "limit": 100,
  "window": "1 minute"
}
```

**Best Practices**:

- Batch requests: Use `/api/validate-batch` instead of multiple `/api/validate` calls
- Respect Retry-After headers
- Implement exponential backoff on 429 responses
- Cache validation results to reduce duplicate requests
- Use batch processing with 4-8 workers for optimal throughput

**For High-Volume Use**:

```yaml
# Increase limits for trusted clients
server:
  rate_limiting:
    enabled: true
    requests_per_minute: 500        # Higher for batch jobs
    concurrent_validations: 50
    per_endpoint_limits:
      "/api/validate": 100
      "/workflows/validate-directory": 500
```

**See also**: [Configuration Guide](configuration.md), [Performance Tuning](performance_metrics.md)

---

### How do I handle long-running validations?

For large files or complex validation:

**Check Workflow Status**:

```bash
# Start validation
VALIDATION_ID=$(curl -s -X POST http://localhost:8080/api/validate \
  -H "Content-Type: application/json" \
  -d '{"content": "...", "file_path": "large_file.md"}' | jq -r '.validation_id')

# Poll status
while true; do
  STATUS=$(curl -s "http://localhost:8080/workflows/${VALIDATION_ID}" | jq -r '.status')
  if [ "$STATUS" = "completed" ]; then
    break
  fi
  echo "Status: $STATUS"
  sleep 2
done

# Get results
curl "http://localhost:8080/workflows/${VALIDATION_ID}/results"
```

**WebSocket Real-Time Updates** (Recommended):

```javascript
// Connect to WebSocket for real-time updates
const ws = new WebSocket('ws://localhost:8080/ws/validation');

ws.onmessage = function(event) {
  const update = JSON.parse(event.data);
  console.log(`Progress: ${update.progress}/${update.total}`);
  console.log(`Status: ${update.status}`);
  if (update.status === 'completed') {
    console.log(update.results);
  }
};
```

**Cancel Long-Running Validation**:

```bash
curl -X DELETE http://localhost:8080/workflows/validation-id-here
```

**Timeout Configuration**:

```yaml
# config/main.yaml
server:
  request_timeout_seconds: 300    # 5 minutes

agents:
  orchestrator:
    workflow_timeout_seconds: 3600  # 1 hour
```

**See also**: [Workflows Documentation](workflows.md), [Performance Optimization](performance_metrics.md)

---

## Database

### What database does TBCV use?

TBCV uses **SQLite by default** for simple, zero-configuration storage:

- **Default**: SQLite (`data/tbcv.db`)
- **Production Alternative**: PostgreSQL (recommended for multi-node deployments)
- **Optional Cache**: Redis (for distributed caching)

**SQLite Characteristics**:

- Zero configuration needed
- Perfect for development and single-node deployments
- Embedded in Python (no external service required)
- File-based storage (easy backups)
- Supports concurrent reads, limited writes
- Good for 1000s of validations

**When to Use SQLite**:
- Local development
- Small-to-medium deployments (<100k validations)
- Single server setup
- Simplicity preferred

**When to Use PostgreSQL**:
- Production deployments
- Multi-node/clustered setups
- High concurrency (many simultaneous validations)
- Advanced features (replication, sharding)
- Existing PostgreSQL infrastructure

**Database Location**:

```
data/
├── tbcv.db              # SQLite database
├── logs/                # Application logs
└── cache/               # L2 cache (disk-based)
```

**See also**: [Database Schema](database_schema.md), [Deployment Guide](deployment.md)

---

### What's stored in the TBCV database?

TBCV stores all validation history and audit data:

**Database Tables**:

| Table | Purpose | Example Data |
|-------|---------|--------------|
| **workflows** | Validation job information | ID, status, file path, start/end times |
| **validation_results** | Validation output | Errors, warnings, validator results |
| **recommendations** | Improvement suggestions | Type, confidence score, proposed change |
| **enhancement_history** | Applied changes | What was changed, when, by whom |
| **checkpoints** | Workflow state | Snapshots for recovery |
| **audit_log** | Activity tracking | User actions, API calls, system events |

**Data Retention**:

```yaml
# config/main.yaml
database:
  retention:
    workflow_retention_days: 90    # Keep workflows 90 days
    audit_log_retention_days: 365  # Keep audit logs 1 year
    cache_ttl_seconds: 86400       # Cache data 24 hours
    auto_cleanup_enabled: true
```

**Example Queries**:

```python
from core.database import db_manager, Workflow

# Get recent validations
recent = db_manager.query(Workflow).filter(
    Workflow.created_at > datetime.now() - timedelta(days=7)
).all()

# Count validations by status
stats = db_manager.query(Workflow.status, func.count()).group_by(Workflow.status).all()

# Find validations with errors
with_errors = db_manager.query(Workflow).filter(
    Workflow.error_count > 0
).all()
```

**See also**: [Database Schema](database_schema.md)

---

### How do I backup and restore the database?

Regular backups are essential:

**Create Backup**:

```bash
# Manual backup (SQLite)
cp data/tbcv.db data/tbcv.db.backup.$(date +%Y%m%d-%H%M%S)

# Full backup including logs and cache
tar -czf tbcv-backup-$(date +%Y%m%d).tar.gz data/ config/ truth/

# API backup endpoint
curl -X POST http://localhost:8080/admin/db/backup \
  -H "X-API-Key: your-api-key" \
  -o tbcv-backup.tar.gz
```

**Automated Backups**:

```bash
# Create backup script
#!/bin/bash
BACKUP_DIR="/backups/tbcv"
DATE=$(date +%Y%m%d-%H%M%S)
cp data/tbcv.db "$BACKUP_DIR/tbcv-$DATE.db"
# Keep only last 30 backups
ls -t $BACKUP_DIR/tbcv-*.db | tail -n +31 | xargs rm -f

# Schedule with cron (daily at 2 AM)
0 2 * * * /path/to/backup-script.sh
```

**Restore from Backup**:

```bash
# Stop server first
pkill -f "python main.py"

# Restore database
cp data/tbcv.db.backup data/tbcv.db

# Restart server
python main.py --mode api

# Or via API (if server is running)
curl -X POST http://localhost:8080/admin/db/restore \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -F "backup_file=@tbcv-backup.db"
```

**Verify Backup**:

```bash
# Check SQLite database integrity
sqlite3 data/tbcv.db "PRAGMA integrity_check;"

# Should output: "ok"
```

**Backup Strategy**:

- Daily automated backups
- Keep 30 days of backups
- Weekly archival to offsite storage
- Monthly verification of restores
- Document recovery procedure

**See also**: [Deployment Guide](deployment.md#backup-and-recovery), [Database Schema](database_schema.md)

---

### How do I migrate from SQLite to PostgreSQL?

To move to PostgreSQL for production:

**Setup PostgreSQL**:

```bash
# Create database and user
createdb tbcv
createuser tbcv_user -P  # Set password when prompted

# Configure PostgreSQL connection
export DATABASE_URL=postgresql://tbcv_user:password@localhost:5432/tbcv
```

**Migrate Data**:

```bash
# Export from SQLite
python -m scripts.db_migrate export --source sqlite --output dump.json

# Import to PostgreSQL
python -m scripts.db_migrate import --target postgresql --input dump.json

# Verify migration
curl http://localhost:8080/health
```

**Update Configuration**:

```yaml
# config/main.yaml
database:
  type: postgresql
  url: postgresql://tbcv_user:password@localhost:5432/tbcv
  pool_size: 20
  echo: false
```

**Verify Data Integrity**:

```bash
# Compare row counts
python -m scripts.db_verify --source sqlite --target postgresql

# Check for migration issues
python -m scripts.db_validate
```

**See also**: [Deployment Guide](deployment.md#database-setup), [Migration Guide](migration_guide.md)

---

## Performance

### How can I optimize TBCV performance?

TBCV is designed for speed but can be further optimized:

**Caching Strategy** (Biggest impact):

```yaml
# config/main.yaml
cache:
  l1:
    enabled: true
    max_entries: 5000        # Increase from default 1000
    max_memory_mb: 512       # More memory for cache
    ttl_seconds: 86400       # 24 hours (increase from 3600)
  l2:
    enabled: true
    db_path: "./data/cache"
    ttl_seconds: 604800      # 7 days for truth data
```

**Validator Optimization**:

```yaml
# Skip slow validators for quick validation
validation_flow:
  profiles:
    quick:
      validators: [yaml, markdown]      # Skip code, links
      timeout_seconds: 5

# Disable expensive validators
agents:
  link_validator:
    enabled: false              # Link checking is slowest
  llm_validator:
    enabled: false              # LLM validation is optional
```

**Batch Processing**:

```bash
# Use batch processing instead of single file validation
python -m cli.main validate-directory docs/ \
  --workers 8 \           # More workers
  --cache \               # Enable caching
  --profile quick         # Fast validation
```

**Database Optimization**:

```yaml
# config/main.yaml
database:
  pool_size: 20           # Connection pooling
  echo: false             # Disable query logging
```

**Fuzzy Detector Tuning**:

```yaml
# config/main.yaml
fuzzy_detector:
  enabled: true
  similarity_threshold: 0.9     # Stricter = faster
  context_window_chars: 100     # Smaller = faster
  max_patterns: 1000            # More caching
```

**Performance Tuning Tips**:

1. **Increase cache TTL** from 3600s to 86400s (24h) for stable content
2. **Use validation profiles**: `quick` for development, `strict` for release
3. **Disable link validation** (slowest) if not needed: ~1-5s per file
4. **Enable L2 cache** for repeated validations
5. **Use batch processing** with 4-8 workers
6. **Disable LLM validation** unless semantics matter
7. **Adjust fuzzy detector threshold** (higher = faster but fewer matches)
8. **Run on SSD** (database performance critical)

**Monitoring Performance**:

```bash
# Check performance metrics
curl http://localhost:8080/admin/performance

# View cache hit rate
curl http://localhost:8080/admin/cache/stats

# Benchmark a validation
time python -m cli.main validate-file file.md
```

**See also**: [Performance Metrics](performance_metrics.md), [Configuration Guide](configuration.md#performance)

---

### What are typical performance characteristics?

Actual performance depends on file size and validators:

**Small Files** (<5KB, quick profile):
- Validation time: 100-300ms
- Throughput: 3-10 files/second

**Medium Files** (5-50KB, default profile):
- Validation time: 500-1500ms
- Throughput: 1-3 files/second

**Large Files** (50KB-1MB, strict profile with LLM):
- Validation time: 3-10 seconds
- Throughput: 0.1-0.3 files/second

**Batch Processing** (1000 files):
- Total time: 10-30 minutes with 4 workers
- Throughput: 1-2 files/second per worker

**Caching Impact**:
- Cache hit: 10-50ms (no validation)
- Cache miss: Full validation time
- Hit rate: Typically 60-80% for stable content

**Bottleneck Analysis**:

| Slowest Component | Time | Optimization |
|-------------------|------|--------------|
| **Link validation** | 1-5s | Disable if not needed |
| **LLM validation** | 5-30s | Disable by default |
| **Large file parsing** | 1-2s | Use quicker profile |
| **Database writes** | 100-500ms | Use batch inserts |
| **Fuzzy detection** | 100-500ms | Higher threshold |

**See also**: [Performance Baselines](performance_baselines.md), [Performance Metrics](performance_metrics.md)

---

### How do I scale TBCV for high-volume validations?

For processing thousands of files:

**Horizontal Scaling** (Multiple servers):

```yaml
# Use PostgreSQL for shared database
database:
  type: postgresql
  url: postgresql://user:pass@db-server:5432/tbcv
  pool_size: 20

# Use Redis for distributed cache
cache:
  l2:
    type: redis
    host: redis-server
    port: 6379
```

**Worker Pool Scaling**:

```yaml
# config/main.yaml
performance:
  worker_pool_size: 16        # Increase from default 4
  max_concurrent_workflows: 100  # Handle more simultaneous jobs
  batch_size: 100             # Process 100 files per batch
```

**Load Balancing** (Nginx example):

```nginx
upstream tbcv {
    server localhost:8080;
    server localhost:8081;
    server localhost:8082;
}

server {
    listen 80;
    location / {
        proxy_pass http://tbcv;
    }
}
```

**Asynchronous Processing**:

```bash
# Submit batch job
JOB_ID=$(curl -s -X POST http://localhost:8080/workflows/validate-directory \
  -H "Content-Type: application/json" \
  -d '{
    "directory_path": "./docs",
    "file_pattern": "*.md",
    "max_workers": 16,
    "async": true
  }' | jq -r '.job_id')

# Check status later
curl http://localhost:8080/jobs/$JOB_ID/status

# Get results when ready
curl http://localhost:8080/jobs/$JOB_ID/results
```

**Container Deployment** (Docker example):

```yaml
# docker-compose.yml
version: '3.8'
services:
  tbcv-1:
    image: tbcv:latest
    ports: ["8080:8080"]
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/tbcv
      - CACHE_REDIS_URL=redis://redis:6379

  tbcv-2:
    image: tbcv:latest
    ports: ["8081:8080"]
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/tbcv
      - CACHE_REDIS_URL=redis://redis:6379

  postgres:
    image: postgres:14
    environment:
      - POSTGRES_DB=tbcv
      - POSTGRES_USER=tbcv_user
      - POSTGRES_PASSWORD=secure_password

  redis:
    image: redis:7-alpine
```

**Scaling Recommendations**:

- **<1000 files/day**: Single server with SQLite
- **1000-10000 files/day**: Single server with PostgreSQL + Redis
- **10000+ files/day**: Multiple servers with load balancer
- **Real-time validation**: WebSocket + async processing

**See also**: [Deployment Guide](deployment.md), [Performance Tuning](performance_metrics.md)

---

## Troubleshooting

### Server won't start - what do I do?

**Check for common startup issues**:

**1. Port Already in Use**:

```bash
# Find what's using port 8080 (Windows)
netstat -ano | findstr :8080

# Find what's using port 8080 (Linux/Mac)
lsof -i :8080

# Kill the process or use different port
python main.py --mode api --port 8081
```

**2. Database Lock**:

```bash
# Check database exists and is accessible
ls -la data/tbcv.db

# Remove corrupted database
rm data/tbcv.db

# Reinitialize
python -c "from core.database import db_manager; db_manager.initialize_database()"
```

**3. Missing Dependencies**:

```bash
# Reinstall requirements
pip install -r requirements.txt --upgrade

# Check Python version
python --version  # Must be 3.8+

# Check imports work
python -c "import fastapi; print(fastapi.__version__)"
```

**4. Import/Path Errors**:

```bash
# Ensure PYTHONPATH is set
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Run from project root
cd /path/to/tbcv
python main.py --mode api

# Or use python module syntax
python -m main
```

**5. Configuration Errors**:

```bash
# Check configuration files for YAML errors
python -c "from core.config_loader import load_config; load_config()"

# View parsed configuration
python -c "from core.config_loader import load_config; import json; print(json.dumps(load_config(), indent=2))"
```

**6. Permission Errors** (Linux/Mac):

```bash
# Check file permissions
ls -la data/
ls -la config/

# Make directories writable
chmod -R 755 data/
chmod -R 755 config/
```

**View Startup Logs**:

```bash
# Run with verbose output
python main.py --mode api --debug

# Check logs directory
tail -f data/logs/tbcv.log
```

**See also**: [Troubleshooting Guide](troubleshooting.md#server-won-t-start)

---

### How do I fix validation errors?

When validations fail or produce unexpected errors:

**Check Agent Status**:

```bash
# Ensure all agents are running
curl http://localhost:8080/agents

# Look for agents with status "error"
# Restart agent if needed
curl -X POST http://localhost:8080/admin/agents/fuzzy-detector/reload
```

**Enable Debug Logging**:

```bash
# Restart server with debug logging
export TBCV_LOG_LEVEL=DEBUG
python main.py --mode api

# View detailed logs
tail -f data/logs/tbcv.log | grep "ERROR\|DEBUG"
```

**Common Validation Errors**:

| Error | Cause | Solution |
|-------|-------|----------|
| "No plugins detected" | Fuzzy detector disabled or threshold too high | Lower `similarity_threshold` or enable fuzzy validation |
| "YAML parse error" | Invalid frontmatter | Fix YAML syntax, check indentation |
| "Database locked" | Concurrent writes | Restart server, check for zombie processes |
| "LLM timeout" | Ollama not running | Start Ollama: `ollama serve` |
| "Out of memory" | Too many workers | Reduce `worker_pool_size` in config |

**Reset Validation Cache**:

```bash
# Clear cache if results seem stale
curl -X POST http://localhost:8080/admin/cache/clear \
  -H "X-API-Key: your-api-key"

# Retry validation
python -m cli.main validate-file file.md --no-cache
```

**Validate Configuration**:

```bash
# Test if configuration loads correctly
python -c "from core.config_loader import load_config; config = load_config(); print('Config OK')"

# Check specific validator config
python -c "from core.config_loader import get_validator_config; print(get_validator_config('fuzzy_detector'))"
```

**See also**: [Troubleshooting Guide](troubleshooting.md)

---

### How do I debug performance issues?

When validations are slow:

**Profile Validation Time**:

```bash
# Time individual components
time python -m cli.main validate-file file.md --profile quick
time python -m cli.main validate-file file.md --profile default

# Get timing breakdown
curl http://localhost:8080/admin/performance/profile \
  -H "Content-Type: application/json" \
  -d '{"file_path": "file.md"}'
```

**Check Cache Statistics**:

```bash
# View cache hit rate
curl http://localhost:8080/admin/cache/stats

# Response:
# {
#   "l1_hits": 150,
#   "l1_misses": 50,
#   "l1_hit_rate": 0.75,
#   "l2_hits": 20,
#   "total_entries": 170
# }

# Low hit rate (<50%) means cache not effective
# Increase TTL or file pattern consistency
```

**Identify Slow Validators**:

```bash
# Enable validator timing
export TBCV_VALIDATORS__ENABLE_TIMING=true

# Check logs for timing info
grep "validator_timing" data/logs/tbcv.log

# Find slowest validators
grep "validator_timing" data/logs/tbcv.log | sort -t'=' -k2 -rn | head -10
```

**Monitor Resource Usage**:

```bash
# Check memory usage
ps aux | grep "python main.py"

# Monitor CPU during validation
top -p $(pgrep -f "python main.py")
```

**Optimize Configuration**:

```yaml
# config/main.yaml
# For slow performance:

cache:
  l1:
    ttl_seconds: 86400        # Increase cache duration
    max_entries: 5000         # More entries

fuzzy_detector:
  similarity_threshold: 0.9   # Higher threshold = faster

validation_flow:
  profiles:
    quick:
      validators: [yaml, markdown]  # Skip slow validators
```

**See also**: [Performance Optimization](performance_metrics.md), [Configuration Guide](configuration.md)

---

### How do I check and repair database issues?

If you suspect database corruption:

**Database Health Check**:

```bash
# Check SQLite integrity
sqlite3 data/tbcv.db "PRAGMA integrity_check;"

# Should output "ok"
# If not, database is corrupted
```

**Backup Before Any Repair**:

```bash
# Always backup first!
cp data/tbcv.db data/tbcv.db.corrupted.backup
```

**Repair Corrupted Database**:

```bash
# Method 1: Rebuild from dump
sqlite3 data/tbcv.db ".dump" | sqlite3 data/tbcv.db.repaired
mv data/tbcv.db.repaired data/tbcv.db

# Method 2: Use recovery script
python -m scripts.db_repair --database data/tbcv.db

# Method 3: Reinitialize (loses data)
rm data/tbcv.db
python -c "from core.database import db_manager; db_manager.initialize_database()"
```

**Verify Repair**:

```bash
# Check integrity again
sqlite3 data/tbcv.db "PRAGMA integrity_check;"

# Restart server
python main.py --mode api

# Test basic operations
curl http://localhost:8080/health
```

**Prevent Corruption**:

- Regular backups
- Graceful shutdown (don't kill process)
- Adequate disk space
- Proper file permissions
- Monitor disk health

**See also**: [Database Schema](database_schema.md), [Troubleshooting Guide](troubleshooting.md)

---

## Development

### How do I set up a development environment?

**Clone and Setup**:

```bash
# Clone repository
git clone <repository-url>
cd tbcv

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt
pip install pytest pytest-cov black flake8 mypy

# Initialize database
python -c "from core.database import db_manager; db_manager.initialize_database()"
```

**Development Mode**:

```bash
# Run with auto-reload
python main.py --mode api --reload --debug

# Or using Uvicorn directly
uvicorn api.server:app --reload --host 127.0.0.1 --port 8080
```

**Run Tests**:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/agents/test_fuzzy_detector.py

# Run with coverage
pytest --cov=. --cov-report=html

# Run tests matching pattern
pytest -k "test_validation" -v

# Run integration tests only
pytest -m integration
```

**Code Quality**:

```bash
# Format code
black . --line-length 100

# Check style
flake8 . --max-line-length 100

# Type checking
mypy . --ignore-missing-imports

# All checks
black . && flake8 . && mypy . && pytest
```

**Debug Specific Code**:

```python
# Add debugging in Python code
import pdb; pdb.set_trace()  # Breakpoint

# Or use debugger in VS Code
# Add .vscode/launch.json:
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Main",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/main.py",
            "console": "integratedTerminal"
        }
    ]
}
```

**See also**: [Development Guide](development.md), [Testing Guide](testing.md)

---

### How do I add a new validator?

Creating custom validators:

**Create Validator Class**:

```python
# agents/validators/custom_validator.py
from agents.validators.base_validator import BaseValidatorAgent
from core.models import ValidationIssue

class CustomValidatorAgent(BaseValidatorAgent):
    """Validates custom business rules"""

    async def validate(self, content: str, file_path: str, config: dict):
        """Main validation method"""
        issues = []

        # Your validation logic
        if "forbidden_word" in content:
            issues.append(
                ValidationIssue(
                    type="error",
                    message="Forbidden word detected",
                    line=self._find_line_number(content, "forbidden_word"),
                    severity="high"
                )
            )

        return {
            "valid": len(issues) == 0,
            "issues": issues
        }

    def get_validator_name(self) -> str:
        return "custom"

    def get_description(self) -> str:
        return "Validates custom business rules"
```

**Register Validator**:

```python
# agents/validators/router.py
from agents.validators.custom_validator import CustomValidatorAgent

VALIDATORS = {
    "custom": CustomValidatorAgent(),
    # ... other validators
}
```

**Add Configuration**:

```yaml
# config/validation_flow.yaml
custom_validator:
  enabled: true
  rules:
    - pattern: "forbidden_word"
      message: "This word is not allowed"
      severity: "error"
```

**Write Tests**:

```python
# tests/validators/test_custom_validator.py
import pytest
from agents.validators.custom_validator import CustomValidatorAgent

@pytest.mark.asyncio
async def test_custom_validator_detects_forbidden_word():
    validator = CustomValidatorAgent()
    result = await validator.validate(
        content="This has forbidden_word in it",
        file_path="test.md",
        config={}
    )

    assert not result["valid"]
    assert len(result["issues"]) == 1
    assert "forbidden_word" in result["issues"][0].message
```

**See also**: [Contributing Guide](development.md), [Modular Validators](modular_validators.md)

---

### How do I contribute to TBCV?

Contributing guidelines:

**Fork and Branch**:

```bash
# Fork repository on GitHub
# Clone your fork
git clone https://github.com/YOUR-USERNAME/tbcv.git
cd tbcv

# Create feature branch
git checkout -b feature/my-feature
```

**Make Changes**:

```bash
# Write code following style guide
# Run tests to ensure nothing breaks
pytest

# Check code quality
black . && flake8 . && mypy .
```

**Write Tests**:

```python
# Every new feature needs tests
# tests/test_my_feature.py
import pytest

def test_my_feature():
    # Arrange
    input_data = "test"

    # Act
    result = my_function(input_data)

    # Assert
    assert result == "expected"
```

**Update Documentation**:

```bash
# Document your changes
# Update README.md if needed
# Add docstrings to code
# Update relevant docs/ files

# Example docstring:
"""
Validate content against custom rules.

Args:
    content: Markdown content to validate
    rules: List of validation rules

Returns:
    dict: {
        "valid": bool,
        "issues": List[ValidationIssue]
    }

Raises:
    ValueError: If rules are invalid
"""
```

**Commit and Push**:

```bash
# Commit with clear message
git add .
git commit -m "feat: Add new validator for business rules"

# Push to your fork
git push origin feature/my-feature
```

**Submit Pull Request**:

1. Go to GitHub
2. Click "New Pull Request"
3. Select your branch
4. Write descriptive PR description
5. Link related issues
6. Submit PR

**PR Checklist**:

- [ ] Tests pass (`pytest`)
- [ ] Code formatted (`black .`)
- [ ] No style issues (`flake8`)
- [ ] Type checks pass (`mypy`)
- [ ] Documentation updated
- [ ] Commit messages clear
- [ ] No breaking changes (if patch/minor)

**See also**: [Development Guide](development.md), [Testing Guide](testing.md)

---

### How do I run and write tests?

**Running Tests**:

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/validators/test_yaml_validator.py

# Run tests matching pattern
pytest -k "test_fuzzy" -v

# Run with coverage
pytest --cov=. --cov-report=html

# Run only fast tests
pytest -m "not slow"

# Run specific test
pytest tests/test_validation.py::test_validate_file -v
```

**Test Structure**:

```
tests/
├── agents/                  # Agent tests
│   ├── test_orchestrator.py
│   ├── test_fuzzy_detector.py
│   └── validators/
│       ├── test_yaml_validator.py
│       └── test_markdown_validator.py
├── api/                     # API tests
│   ├── test_validation_endpoints.py
│   └── test_recommendations.py
├── cli/                     # CLI tests
│   └── test_cli_commands.py
├── core/                    # Core functionality tests
│   ├── test_config_loader.py
│   └── test_database.py
├── e2e/                     # End-to-end tests
│   └── test_validation_workflow.py
└── fixtures/                # Test data and fixtures
    ├── sample_markdown.md
    └── sample_truth_data.json
```

**Writing Tests**:

```python
# tests/test_example.py
import pytest
from agents.example import ExampleAgent

class TestExampleAgent:
    @pytest.fixture
    def agent(self):
        """Setup agent for testing"""
        return ExampleAgent()

    def test_initialization(self, agent):
        """Test agent initializes correctly"""
        assert agent is not None
        assert agent.name == "example"

    @pytest.mark.asyncio
    async def test_process_request(self, agent):
        """Test async request processing"""
        result = await agent.process_request(
            method="validate",
            params={"content": "test"}
        )
        assert result["status"] == "success"

    @pytest.mark.parametrize("input,expected", [
        ("test1", "result1"),
        ("test2", "result2"),
    ])
    def test_multiple_cases(self, agent, input, expected):
        """Test multiple input cases"""
        result = agent.process(input)
        assert result == expected
```

**Test Fixtures**:

```python
# tests/conftest.py
import pytest
import tempfile
import os

@pytest.fixture
def temp_markdown_file():
    """Create temporary markdown file for testing"""
    content = """---
title: Test
---

# Test Document

Some content here.
"""
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.md',
        delete=False
    ) as f:
        f.write(content)
        temp_file = f.name

    yield temp_file

    # Cleanup
    os.unlink(temp_file)
```

**See also**: [Testing Guide](testing.md), [Development Guide](development.md)

---

## Deployment

### How do I deploy TBCV to production?

**Production Checklist**:

```yaml
Before deployment:
  - [ ] Disable debug mode
  - [ ] Set environment to "production"
  - [ ] Configure HTTPS/SSL
  - [ ] Set up database backups
  - [ ] Configure monitoring/logging
  - [ ] Set strong API keys
  - [ ] Review security settings
  - [ ] Load test the system
  - [ ] Document deployment
  - [ ] Prepare rollback plan
```

**System Requirements**:

- **OS**: Linux recommended (CentOS 8+, Ubuntu 20.04+)
- **Python**: 3.10+
- **Memory**: 8GB+ recommended
- **CPU**: 2+ cores
- **Disk**: 10GB+ for data/logs
- **Database**: PostgreSQL 12+ recommended

**Install on Linux**:

```bash
# 1. Install system dependencies
sudo apt update
sudo apt install python3.10 python3-pip git postgresql

# 2. Clone and setup
git clone <repo> /opt/tbcv
cd /opt/tbcv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Create service user
sudo useradd -m -s /bin/bash tbcv

# 4. Fix permissions
sudo chown -R tbcv:tbcv /opt/tbcv

# 5. Initialize database
sudo -u tbcv python -c "from core.database import db_manager; db_manager.initialize_database()"
```

**Production Configuration**:

```yaml
# config/main.production.yaml
system:
  environment: "production"
  debug: false
  log_level: "warning"

server:
  host: "0.0.0.0"
  port: 8080
  enable_cors: true
  cors_origins:
    - "https://yourdomain.com"
  require_api_key: true

security:
  access_control: "BLOCK"     # Enforce MCP-first

database:
  type: "postgresql"
  url: "postgresql://user:pass@db-host:5432/tbcv"
  pool_size: 20

cache:
  l2:
    type: "redis"
    host: "redis-host"
```

**Systemd Service**:

```ini
# /etc/systemd/system/tbcv.service
[Unit]
Description=TBCV Validation Service
After=network.target postgresql.service

[Service]
Type=notify
User=tbcv
WorkingDirectory=/opt/tbcv
ExecStart=/opt/tbcv/venv/bin/python main.py --mode api --host 0.0.0.0 --port 8080
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable tbcv
sudo systemctl start tbcv
sudo systemctl status tbcv
```

**Nginx Reverse Proxy**:

```nginx
# /etc/nginx/sites-available/tbcv
upstream tbcv_backend {
    server 127.0.0.1:8080;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://tbcv_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

**Monitoring**:

```bash
# Check service status
sudo systemctl status tbcv

# View logs
sudo journalctl -u tbcv -f

# Monitor health
curl https://api.yourdomain.com/health
```

**See also**: [Deployment Guide](deployment.md), [Production Readiness](production_readiness.md)

---

### How do I deploy using Docker?

**Docker Setup**:

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 tbcv
RUN chown -R tbcv:tbcv /app
USER tbcv

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run application
CMD ["python", "main.py", "--mode", "api", "--host", "0.0.0.0", "--port", "8080"]

EXPOSE 8080
```

**Docker Compose**:

```yaml
# docker-compose.yml
version: '3.8'

services:
  tbcv:
    build: .
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=postgresql://tbcv:password@postgres:5432/tbcv
      - CACHE_REDIS_URL=redis://redis:6379
      - TBCV_ENVIRONMENT=production
    depends_on:
      - postgres
      - redis
    volumes:
      - ./data:/app/data
      - ./config:/app/config:ro
    restart: always

  postgres:
    image: postgres:14-alpine
    environment:
      - POSTGRES_DB=tbcv
      - POSTGRES_USER=tbcv
      - POSTGRES_PASSWORD=secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: always

volumes:
  postgres_data:
  redis_data:
```

**Build and Deploy**:

```bash
# Build image
docker build -t tbcv:latest .

# Run container
docker run -d \
  --name tbcv \
  -p 8080:8080 \
  -e DATABASE_URL=postgresql://... \
  -v ./config:/app/config:ro \
  tbcv:latest

# Or use Docker Compose
docker-compose up -d

# Check logs
docker logs -f tbcv
```

**See also**: [Deployment Guide](deployment.md), [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

---

### How do I monitor and maintain a running TBCV instance?

**Health Monitoring**:

```bash
# Check system health
curl http://localhost:8080/health

# Check readiness (for load balancers)
curl http://localhost:8080/health/ready

# Check liveness (for Kubernetes)
curl http://localhost:8080/health/live

# View agent status
curl http://localhost:8080/agents
```

**Performance Monitoring**:

```bash
# Get performance metrics
curl http://localhost:8080/admin/performance

# View cache statistics
curl http://localhost:8080/admin/cache/stats

# Check database status
curl http://localhost:8080/admin/system
```

**Logging**:

```bash
# View recent logs
tail -f data/logs/tbcv.log

# Filter errors
grep ERROR data/logs/tbcv.log | tail -20

# Filter specific agent
grep "FuzzyDetectorAgent" data/logs/tbcv.log

# View with timestamp
tail -f data/logs/tbcv.log | grep "$(date +%Y-%m-%d)"
```

**Database Maintenance**:

```bash
# Backup database
cp data/tbcv.db data/tbcv.db.backup

# Check database integrity
sqlite3 data/tbcv.db "PRAGMA integrity_check;"

# Optimize database
sqlite3 data/tbcv.db "VACUUM;"
```

**Configuration Updates**:

```bash
# Reload configuration without restart
curl -X POST http://localhost:8080/admin/config/reload

# Changes take effect immediately
```

**Scaling and Performance**:

```bash
# Monitor resource usage
ps aux | grep "python main.py"

# Adjust if needed
# Edit config/main.yaml to increase workers/cache
# Restart service: sudo systemctl restart tbcv
```

**Security Audit**:

```bash
# View audit log
curl http://localhost:8080/admin/audit-log?limit=100

# Check for violations
grep "VIOLATION\|BLOCKED" data/logs/tbcv.log
```

**See also**: [Production Readiness](production_readiness.md), [Troubleshooting Guide](troubleshooting.md)

---

## Index of Related Documentation

- **[Architecture](architecture.md)** - System design and data flow
- **[Agents Reference](agents.md)** - Detailed agent documentation
- **[API Reference](api_reference.md)** - Complete REST API documentation
- **[CLI Usage](cli_usage.md)** - Command-line interface guide
- **[Configuration](configuration.md)** - Configuration files and settings
- **[Database Schema](database_schema.md)** - Data model documentation
- **[Deployment](deployment.md)** - Production deployment guide
- **[Enhancement Workflow](enhancement_workflow.md)** - Content enhancement process
- **[Modular Validators](modular_validators.md)** - Validator architecture
- **[Security](security.md)** - Access control and security measures
- **[Testing](testing.md)** - Test structure and running tests
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions
- **[Truth Store](truth_store.md)** - Plugin definitions and detection
- **[Web Dashboard](web_dashboard.md)** - Web UI documentation
- **[Workflows](workflows.md)** - Workflow orchestration
- **[Development Guide](development.md)** - Contributing and extending

---

## Questions Not Covered?

For additional help:

- **Issues**: [GitHub Issues](https://github.com/your-org/tbcv/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/tbcv/discussions)
- **Documentation**: Full documentation available in [docs/](../docs/)
- **Email**: [support email if applicable]

---

**Last Updated**: December 2025
**Version**: TBCV 2.0.0
**Maintainer**: TBCV Development Team
