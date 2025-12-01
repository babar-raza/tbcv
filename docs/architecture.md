# TBCV System Architecture

## Overview

TBCV (Truth-Based Content Validation) is a multi-agent **content validation and enhancement system** for technical documentation. The system validates existing markdown files against rules and "truth data" (plugin definitions), detects plugin usage patterns through fuzzy matching, generates actionable recommendations, and applies approved enhancements through a human-in-the-loop workflow.

**Important**: TBCV validates and enhances **existing** content. It does not generate content from scratch.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     User Interfaces                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   CLI       │  │   REST API  │  │   Web Dashboard         │  │
│  │  (Click)    │  │  (FastAPI)  │  │   (Jinja2 Templates)    │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                     Agent Layer (11 Core Agents)                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐  │
│  │ OrchestratorAgent│  │ TruthManagerAgent│  │FuzzyDetector  │  │
│  └──────────────────┘  └──────────────────┘  │   Agent       │  │
│  ┌──────────────────┐  ┌──────────────────┐  └───────────────┘  │
│  │ContentValidator  │  │ContentEnhancer   │  ┌───────────────┐  │
│  │   Agent (legacy) │  │   Agent          │  │ LLMValidator  │  │
│  └──────────────────┘  └──────────────────┘  │Agent (opt)    │  │
│  ┌──────────────────┐  ┌──────────────────┐  └───────────────┘  │
│  │RecommendationAgent│ │EnhancementAgent  │  ┌───────────────┐  │
│  └──────────────────┘  └──────────────────┘  │CodeAnalyzer   │  │
│  ┌──────────────────┐  ┌──────────────────┐  │   Agent       │  │
│  │EditValidatorAgent│  │RecommendationEnh.│  └───────────────┘  │
│  └──────────────────┘  └──────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                  Modular Validators (7-8 Validators)             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │YAML      │ │Markdown  │ │Code      │ │Link      │           │
│  │Validator │ │Validator │ │Validator │ │Validator │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                        │
│  │Structure │ │Truth     │ │SEO       │  ← ValidatorRouter     │
│  │Validator │ │Validator │ │Validator │                        │
│  └──────────┘ └──────────┘ └──────────┘                        │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                     Core Infrastructure                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Database    │  │ Cache       │  │ Config Loader           │  │
│  │ (SQLite)    │  │ (L1+L2)     │  │ (YAML/JSON)             │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Logging     │  │ Validation  │  │ Performance Tracking    │  │
│  │ (JSON)      │  │ Store       │  │                         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Validator   │  │ Error       │  │ Language Utils          │  │
│  │ Router      │  │ Formatter   │  │ (English enforcement)   │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                     External Services                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Ollama LLM  │  │ MCP Server  │  │ Truth Store (JSON)      │  │
│  │ (Optional)  │  │ (JSON-RPC)  │  │                         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Agents (11 Agents)

### OrchestratorAgent (`agents/orchestrator.py`)
**Responsibility**: Workflow coordination and execution
- Manages complex multi-step validation pipelines
- Handles concurrent workflow execution with per-agent semaphores
- Provides checkpointing and recovery mechanisms
- Implements retry logic with exponential backoff
- Supports workflow types: `validate_file`, `validate_directory`, `full_validation`, `content_update`

### TruthManagerAgent (`agents/truth_manager.py`)
**Responsibility**: Plugin truth data management and indexing
- Loads and indexes plugin definitions from JSON truth tables (`truth/` directory)
- Provides 6 indexes: by_id, by_slug, by_name, by_alias, by_pattern, by_family
- Uses Generic TruthDataAdapter to normalize various JSON schemas
- Handles SHA-256 versioning for change detection
- Cache TTL: 7 days (604800 seconds)

### FuzzyDetectorAgent (`agents/fuzzy_detector.py`)
**Responsibility**: Plugin detection using fuzzy matching algorithms
- Implements Levenshtein and Jaro-Winkler distance algorithms
- Analyzes context windows around potential matches
- Applies confidence scoring for detection accuracy
- Supports combination rules for multi-plugin detection
- Default similarity threshold: 0.85 (configurable)

### ContentValidatorAgent (`agents/content_validator.py`)
**Responsibility**: Legacy monolithic content validation (being replaced by modular validators)
- Validates YAML, Markdown, and code syntax
- Performs link validation and image checking
- Applies rule-based content quality assessment
- Generates detailed validation reports with issues and severity levels
- Supports two-stage truth validation (heuristic + optional LLM)

### ContentEnhancerAgent (`agents/content_enhancer.py`)
**Responsibility**: Content enhancement with safety gating
- Adds plugin hyperlinks to first mentions
- Inserts informational text after code blocks
- Prevents duplicate links and maintains formatting
- **Safety checks**: rewrite_ratio < 0.5, blocked topics detection
- Supports backup and rollback capabilities

### LLMValidatorAgent (`agents/llm_validator.py`)
**Responsibility**: AI-powered semantic validation (optional, disabled by default)
- Uses Ollama (llama2/mistral) for semantic plugin analysis
- Provides fallback to OpenAI/Gemini APIs
- Verifies fuzzy detector findings semantically
- Identifies missing plugins based on code semantics
- Graceful degradation when Ollama unavailable
- Timeout: 30 seconds

### CodeAnalyzerAgent (`agents/code_analyzer.py`)
**Responsibility**: Code quality and security analysis
- Analyzes Python, C#, Java, JavaScript code blocks
- Performs security scanning and complexity assessment
- Integrates with LLM for advanced analysis (optional)
- Provides performance optimization suggestions

### RecommendationAgent (`agents/recommendation_agent.py`)
**Responsibility**: Intelligent recommendation generation
- Analyzes validation results to generate improvements
- Type-specific templates (yaml, markdown, code, links, truth)
- Applies confidence thresholds (default: 0.7)
- Generates actionable instructions with rationale
- Persists recommendations in database with "proposed" status

### EnhancementAgent (`agents/enhancement_agent.py`)
**Responsibility**: Facade over ContentEnhancerAgent
- Applies approved recommendations to content
- Provides preview functionality
- Tracks enhancement statistics and success rates
- Maintains audit trail of changes

### EditValidatorAgent (`agents/edit_validator.py`)
**Responsibility**: Validates edits before/after enhancement
- Compares original and enhanced content
- Validates that enhancements are safe to apply
- Generates diff reports
- Supports rollback validation

### RecommendationEnhancerAgent (`agents/recommendation_enhancer.py`)
**Responsibility**: Recommendation application engine
- Applies approved recommendations to content
- Handles different recommendation types (yaml, markdown, code, link, truth)
- Generates diffs for applied changes
- Creates audit log entries

---

## Modular Validator Agents (7-8 Validators)

The modular validator architecture replaces the legacy monolithic ContentValidatorAgent with specialized, focused validators. See [modular_validators.md](modular_validators.md) for detailed documentation.

### ValidatorRouter (`agents/validators/router.py`)
Routes validation requests to appropriate modular validators with fallback to legacy ContentValidator.

### BaseValidatorAgent (`agents/validators/base_validator.py`)
Abstract base class defining the validator interface.

### Individual Validators

| Validator | File | Purpose |
|-----------|------|---------|
| **YamlValidatorAgent** | `yaml_validator.py` | YAML frontmatter validation |
| **MarkdownValidatorAgent** | `markdown_validator.py` | Markdown structure and syntax |
| **CodeValidatorAgent** | `code_validator.py` | Code block validation |
| **LinkValidatorAgent** | `link_validator.py` | Link and URL validation |
| **StructureValidatorAgent** | `structure_validator.py` | Document structure validation |
| **TruthValidatorAgent** | `truth_validator.py` | Truth data validation |
| **SeoValidatorAgent** | `seo_validator.py` | SEO metadata and heading size validation |

---

## Core Infrastructure Modules

### Database (`core/database.py`)
- SQLite-based persistent storage with SQLAlchemy ORM
- Connection pooling with configurable pool size
- Tables: Workflows, ValidationResults, Recommendations, Checkpoints, EnhancementHistory, AuditLog
- Provides audit logging capabilities

### Configuration Loading (`core/config_loader.py`)
- Loads YAML and JSON configuration files
- Provides environment variable override support (`TBCV_` prefix)
- Validates configuration schema
- Supports hot-reloading for some settings

### Caching (`core/cache.py`)
- Two-level caching: L1 (memory LRU) + L2 (disk SQLite)
- LRU eviction policies
- TTL-based expiration
- Compression support for large objects

### Logging (`core/logging.py`)
- Structured JSON logging with configurable levels
- File rotation and backup management
- Performance monitoring integration
- Context-aware logging with workflow IDs

### Validation Store (`core/validation_store.py`)
- Persistent storage for validation results
- Efficient querying and filtering
- Integration with recommendation system
- Performance metrics tracking

### Validator Router (`core/validator_router.py`)
- Routes validation requests to appropriate modular validators
- Maintains validator registry
- Falls back to ContentValidator for unknown types
- Tracks routing decisions for debugging

### Error Formatter (`core/error_formatter.py`)
- Standardizes error formatting for user display
- Formats validation issues with context
- Supports multiple output formats (text, JSON, HTML)

### Language Utils (`core/language_utils.py`)
- Language detection for content
- Enforces English-only content validation
- Rejects non-English content with appropriate error messages

### Performance Tracking (`core/performance.py`)
- Tracks validation and workflow performance
- Records timing metrics per agent
- Provides performance analysis utilities

### File Utils (`core/file_utils.py`)
- Safe file operations
- Path validation and sanitization
- Atomic file writes

---

## API Layer

### FastAPI Server (`api/server.py`)
- 40+ RESTful API endpoints for all operations
- WebSocket support for real-time workflow updates
- Server-Sent Events (SSE) for streaming updates
- CORS configuration for web UI
- Health check endpoints (`/health/live`, `/health/ready`, `/health/detailed`)
- OpenAPI documentation at `/docs`

### Dashboard (`api/dashboard.py`)
- Web-based UI for system monitoring
- Validation results visualization
- Recommendation management interface
- Workflow status tracking
- Jinja2 templates for HTML generation

### Live Event Bus (`api/services/live_bus.py`)
- Real-time event distribution
- WebSocket connection management
- Workflow progress notifications

---

## CLI Interface (`cli/main.py`)

Command-line interface with Rich console output:
- **15+ commands** for validation, recommendations, and admin operations
- File and directory validation commands
- Agent status checking
- Batch processing capabilities
- Recommendation approval/rejection workflow
- Admin commands for cache, health, and system management

---

## External Services

### MCP Server (`svc/mcp_server.py`)
Model Context Protocol server for external integrations:
- JSON-RPC interface for validation operations
- Methods: `validate_folder`, `approve`, `reject`, `enhance`
- Stdin/stdout communication mode (MCPStdioServer)
- Can be used as in-process client

### Ollama LLM Integration (Optional)
- Local LLM inference via Ollama API
- Default models: llama2, mistral
- **Disabled by default** - requires manual setup
- Fallback to OpenAI/Gemini if configured

### Truth Store (`truth/` directory)
- JSON files defining plugin "ground truth"
- Supports multiple product families: words, pdf, cells, slides
- Contains plugin metadata: name, slug, patterns, dependencies, capabilities

---

## Data Flow

### Validation Flow

```
Existing Markdown File
        ↓
TruthManagerAgent.load_truth_data(family)
        ↓ (load plugin definitions and indexes)
FuzzyDetectorAgent.detect_plugins(content, family)
        ↓ (pattern matching + fuzzy algorithms)
ValidatorRouter → Modular Validators
        │
        ├── Tier 1 (parallel): YAML, Markdown, Structure
        ├── Tier 2 (parallel): Code, Links, SEO, HeadingSizes
        └── Tier 3 (sequential): FuzzyLogic → Truth → LLM (optional)
        ↓
RecommendationAgent.generate_recommendations()
        ↓ (generate actionable suggestions)
Database (persist validation + recommendations)
        ↓
[Human Review & Approval]
        ↓
ContentEnhancerAgent.enhance_from_recommendations()
        ↓ (apply approved changes with safety checks)
Enhanced Markdown + Audit Trail
```

### Tiered Validation Execution

Validators execute in 3 tiers (configurable in `config/validation_flow.yaml`):

**Tier 1 - Quick Checks** (parallel):
- YAML frontmatter validation
- Markdown syntax validation
- Document structure validation

**Tier 2 - Content Analysis** (parallel):
- Code block validation
- Link validation
- SEO validation
- Heading size validation

**Tier 3 - Advanced Validation** (sequential, optional):
- FuzzyLogic → Truth → LLM
- Dependencies: Truth requires FuzzyLogic, LLM requires Truth
- LLM validation disabled by default

---

## Configuration Architecture

TBCV uses hierarchical configuration:

1. **Base config**: `config/main.yaml` (system settings)
2. **Agent config**: `config/agent.yaml` (per-agent settings)
3. **Validator configs**: 8 modular validator config files
   - `config/cache.yaml`
   - `config/code.yaml`
   - `config/frontmatter.yaml`
   - `config/links.yaml`
   - `config/markdown.yaml`
   - `config/structure.yaml`
   - `config/truth.yaml`
   - `config/seo.yaml`
   - `config/llm.yaml`
4. **Validation flow**: `config/validation_flow.yaml` (tiered execution, profiles)
5. **Performance**: `config/perf.json` (tuning parameters)
6. **Environment overrides**: `TBCV_` prefix

See [configuration.md](configuration.md) for complete reference.

---

## Technology Stack

- **Backend**: Python 3.8+, FastAPI, Uvicorn
- **Database**: SQLite with SQLAlchemy ORM
- **Caching**: Custom two-level cache (L1 memory LRU + L2 disk SQLite)
- **APIs**: REST, WebSocket, Server-Sent Events (SSE)
- **CLI**: Click framework with Rich console output
- **Templates**: Jinja2 for web dashboard
- **LLM Integration** (optional): Ollama (llama2/mistral), with fallback to OpenAI/Gemini
- **Fuzzy Matching**: Levenshtein distance, Jaro-Winkler similarity
- **Logging**: Structured JSON logging with rotation
- **Real-time Updates**: WebSocket via wsproto
- **Async**: asyncio throughout for concurrency

---

## Deployment Architecture

### Local Development
- Single-process Uvicorn server with `--reload`
- SQLite database in `data/` directory
- File-based logging and caching

### Production Deployment
- Gunicorn/Uvicorn with multiple workers
- Volume mounts for data persistence
- Environment-based configuration
- Systemd service (Linux) or Windows Service

See [deployment.md](deployment.md) for detailed deployment guides.

---

## Database Schema

### Core Tables

| Table | Purpose |
|-------|---------|
| **Workflows** | Track workflow execution state (id, type, status, created_at, etc.) |
| **ValidationResults** | Store validation outcomes (id, file_path, status, issues, confidence) |
| **Recommendations** | Store generated recommendations with approval workflow (id, validation_id, type, instruction, status) |
| **Checkpoints** | Track workflow progress for recovery (workflow_id, checkpoint_name, data) |
| **EnhancementHistory** | Track content enhancements with rollback support (id, file_path, original, enhanced, timestamp) |
| **AuditLog** | Audit trail for all changes (id, action, entity_id, user, timestamp) |

---

## Related Documentation

- [Agents Reference](agents.md) - Detailed agent documentation
- [Modular Validators](modular_validators.md) - Validator architecture
- [Workflows](workflows.md) - Workflow types and execution
- [Configuration](configuration.md) - System configuration
- [API Reference](api_reference.md) - REST API endpoints
- [CLI Usage](cli_usage.md) - Command-line interface
- [MCP Integration](mcp_integration.md) - Model Context Protocol server
