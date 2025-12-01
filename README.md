# TBCV - Truth-Based Content Validation System

**Version 2.0.0** | Content Validation and Enhancement Platform

## Overview

TBCV is an intelligent **content validation and enhancement system** for technical documentation. It validates existing markdown files against rules and "truth data" (plugin definitions), generates actionable recommendations for improvements, and applies approved enhancements through a human-in-the-loop workflow.

**TBCV does NOT generate content from scratch.** It validates, analyzes, and enhances **existing** markdown documentation for Aspose product families (Words, PDF, Cells, Slides, etc.).

### What TBCV Does

✅ **Validates** existing markdown content against:
- YAML frontmatter requirements
- Markdown syntax and structure
- Code block formatting
- Link validity
- SEO best practices
- Truth data (plugin references and technical accuracy)

✅ **Detects** plugin usage via fuzzy matching algorithms (Levenshtein, Jaro-Winkler)

✅ **Generates** actionable recommendations with confidence scores

✅ **Enhances** content by applying approved recommendations:
- Adds plugin hyperlinks
- Inserts informational text
- Fixes validation issues

✅ **Tracks** validation history, recommendations, and enhancement audit trails

---

## Key Features

### Multi-Agent Architecture
TBCV uses specialized agents coordinating through workflows:

**Core Agents** (11 agents):
- **OrchestratorAgent** - Workflow coordination with concurrency control
- **TruthManagerAgent** - Plugin truth data management with multi-level indexing
- **FuzzyDetectorAgent** - Pattern matching and fuzzy plugin detection
- **ContentValidatorAgent** - Multi-scope validation (legacy, being replaced by modular validators)
- **ContentEnhancerAgent** - Content enhancement with safety gating
- **LLMValidatorAgent** - Optional semantic validation via Ollama (disabled by default)
- **CodeAnalyzerAgent** - Code quality and security analysis
- **RecommendationAgent** - Actionable recommendation generation
- **EnhancementAgent** - Applies approved recommendations
- **EditValidatorAgent** - Validates before/after enhancement
- **RecommendationEnhancerAgent** - Recommendation application engine

**Modular Validator Agents** (7-8 validators):
- **YamlValidatorAgent** - YAML frontmatter validation
- **MarkdownValidatorAgent** - Markdown syntax validation
- **CodeValidatorAgent** - Code block validation
- **LinkValidatorAgent** - Link and URL validation
- **StructureValidatorAgent** - Document structure validation
- **TruthValidatorAgent** - Truth data validation (plugin references)
- **SeoValidatorAgent** - SEO and heading size validation

### Validation Types

**Standard Validators** (Fast):
- **yaml** - Frontmatter syntax, required fields, field types
- **markdown** - Heading hierarchy, list formatting, inline formatting
- **code** - Language identifiers, fence closure, syntax
- **links** - HTTP status checks, anchor validation, broken link detection
- **structure** - Document organization, section ordering, completeness
- **seo** - Meta descriptions, title optimization, heading length limits

**Advanced Validators** (Optional):
- **fuzzy** - Fuzzy pattern matching for plugin detection
- **truth** - Validation against plugin truth data
- **llm** - Semantic validation via Ollama (disabled by default, requires setup)

### Tiered Validation Flow

Configurable validation execution in 3 tiers via `config/validation_flow.yaml`:

**Tier 1** (Quick Checks):
- YAML, Markdown, Structure validators run in parallel

**Tier 2** (Content Analysis):
- Code, Links, SEO validators run in parallel

**Tier 3** (Advanced, Optional):
- Fuzzy detection → Truth validation → LLM validation (if enabled)
- Sequential execution with dependencies

### Recommendation Workflow

1. **Generation**: System analyzes validation failures and generates recommendations
2. **Review**: Human reviews recommendations (via CLI or Web UI)
3. **Approval/Rejection**: User approves or rejects each recommendation
4. **Application**: System applies only approved recommendations
5. **Audit Trail**: All changes tracked in database with rollback capability

### Multiple Interfaces

- **REST API**: 40+ endpoints for validation, recommendations, enhancements, workflows
- **CLI**: 15+ commands for file/directory validation, recommendation management, admin operations
- **WebSocket**: Real-time updates for workflow progress
- **Web Dashboard**: Browser-based UI for validation review and recommendation approval
- **MCP Server**: Model Context Protocol server for external integrations

### Persistent Storage

- **SQLite database** with SQLAlchemy ORM
- **Tables**: Workflows, ValidationResults, Recommendations, Checkpoints, EnhancementHistory, AuditLog
- **Two-level caching**: L1 (in-memory LRU) + L2 (disk-based SQLite)
- **Cache TTLs**: Truth data (7 days), fuzzy detection (24 hours), validation (30 minutes)

---

## Quick Start

### Prerequisites

- **Python 3.8+**
- **pip** for package management
- **Ollama** (optional, for LLM semantic validation) - [Install Ollama](https://ollama.ai)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd tbcv

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "from core.database import db_manager; db_manager.initialize_database()"
```

### Start the Server

```bash
# Method 1: Using main.py (recommended)
python main.py --mode api --host 0.0.0.0 --port 8080

# Method 2: Using uvicorn directly
uvicorn api.server:app --host 0.0.0.0 --port 8080 --reload
```

Server will be available at: **http://localhost:8080**

### Test the Installation

```bash
# Check health
curl http://localhost:8080/health/live

# View API documentation
open http://localhost:8080/docs

# Test validation (CLI)
python -m cli.main validate-file path/to/file.md --family words --format text
```

---

## System Architecture

### Data Flow

```
Existing Markdown File
    ↓
TruthManagerAgent (Load plugin definitions)
    ↓
FuzzyDetectorAgent (Detect plugin usage patterns)
    ↓
ValidatorRouter → Modular Validators (YAML, Markdown, Code, Links, Structure, SEO, Truth)
    ↓
LLMValidatorAgent (Optional semantic validation)
    ↓
RecommendationAgent (Generate improvement suggestions)
    ↓
[Human Review & Approval]
    ↓
ContentEnhancerAgent (Apply approved recommendations)
    ↓
Enhanced Markdown + Audit Trail
```

### Technology Stack

- **Backend**: Python 3.8+, FastAPI, Uvicorn
- **Database**: SQLite with SQLAlchemy ORM
- **Caching**: Custom two-level cache (L1 memory + L2 disk)
- **APIs**: REST, WebSocket, Server-Sent Events (SSE)
- **CLI**: Click framework with Rich console output
- **Templates**: Jinja2 for web dashboard
- **LLM Integration** (optional): Ollama (llama2/mistral), with fallback support for OpenAI/Gemini
- **Fuzzy Matching**: Levenshtein distance, Jaro-Winkler similarity
- **Logging**: Structured JSON logging with rotation
- **Real-time Updates**: WebSocket via wsproto

---

## Documentation

### Getting Started
- [Configuration](docs/configuration.md) - System, agent, and validator configuration
- [Deployment](docs/deployment.md) - Local and production deployment
- [Troubleshooting](docs/troubleshooting.md) - Common issues and solutions

### Core Concepts
- [Architecture](docs/architecture.md) - System design and components
- [Agents](docs/agents.md) - Detailed agent descriptions and capabilities
- [Modular Validators](docs/modular_validators.md) - Validator architecture and customization
- [Workflows](docs/workflows.md) - Validation and enhancement workflows
- [Truth Store](docs/truth_store.md) - Plugin definitions and detection rules

### Usage
- [CLI Usage](docs/cli_usage.md) - Command-line interface reference
- [API Reference](docs/api_reference.md) - REST endpoints and schemas
- [Web Dashboard](docs/web_dashboard.md) - Web UI for validation management

### Advanced Features
- [Enhancement Workflow](docs/enhancement_workflow.md) - Detailed enhancement process
- [Checkpoints](docs/checkpoints.md) - Workflow checkpointing and recovery
- [Admin API](docs/admin_api.md) - Administrative endpoints
- [Phase 2 Features](docs/phase2_features.md) - Re-validation, background processing

### Development
- [Development Guide](docs/development.md) - Contributing and extending TBCV
- [Testing](docs/testing.md) - Running tests and test structure

---

## Common Use Cases

### 1. Validate a Single File

```bash
# CLI
python -m cli.main validate-file content/tutorial.md --family words

# API
curl -X POST http://localhost:8080/api/validate \
  -H "Content-Type: application/json" \
  -d '{
    "content": "...",
    "file_path": "tutorial.md",
    "family": "words"
  }'
```

### 2. Batch Validate a Directory

```bash
# CLI
python -m cli.main validate-directory content/ --pattern "*.md" --workers 4

# API
curl -X POST http://localhost:8080/workflows/validate-directory \
  -H "Content-Type: application/json" \
  -d '{
    "directory_path": "./content",
    "file_pattern": "*.md",
    "max_workers": 4,
    "family": "words"
  }'
```

### 3. Review and Approve Recommendations

```bash
# List recommendations for a validation
curl http://localhost:8080/api/recommendations?validation_id=<id>

# Approve a recommendation
curl -X POST http://localhost:8080/api/recommendations/<rec-id>/review \
  -H "Content-Type: application/json" \
  -d '{"status": "accepted", "reviewer": "john", "notes": "LGTM"}'
```

### 4. Enhance Content with Approved Recommendations

```bash
# CLI
python -m cli.main recommendations enhance tutorial.md \
  --validation-id <id> \
  --backup \
  --output enhanced.md

# API
curl -X POST http://localhost:8080/api/enhance \
  -H "Content-Type: application/json" \
  -d '{
    "validation_id": "<id>",
    "file_path": "tutorial.md",
    "content": "...",
    "preview": false
  }'
```

---

## Project Structure

```
tbcv/
├── agents/              # Multi-agent system
│   ├── base.py          # Base agent class
│   ├── orchestrator.py  # Workflow coordination
│   ├── truth_manager.py # Truth data indexing
│   ├── fuzzy_detector.py  # Plugin detection
│   ├── content_validator.py  # Legacy monolithic validator
│   ├── content_enhancer.py   # Enhancement with safety gating
│   ├── llm_validator.py      # Ollama LLM integration (optional)
│   ├── code_analyzer.py      # Code analysis
│   ├── recommendation_agent.py  # Recommendation generation
│   ├── enhancement_agent.py     # Recommendation application
│   ├── edit_validator.py        # Edit validation
│   ├── recommendation_enhancer.py  # Enhancement engine
│   └── validators/      # Modular validator agents
│       ├── base_validator.py      # Base validator
│       ├── router.py              # Validator routing
│       ├── yaml_validator.py      # YAML validation
│       ├── markdown_validator.py  # Markdown validation
│       ├── code_validator.py      # Code validation
│       ├── link_validator.py      # Link validation
│       ├── structure_validator.py # Structure validation
│       ├── truth_validator.py     # Truth validation
│       └── seo_validator.py       # SEO validation
├── api/                 # FastAPI server
│   ├── server.py        # Main API (40+ endpoints)
│   ├── dashboard.py     # Web UI routes
│   └── services/        # Background services
│       └── live_bus.py  # Real-time event bus
├── cli/                 # Command-line interface
│   └── main.py          # Click-based CLI (15+ commands)
├── core/                # Core infrastructure
│   ├── database.py      # SQLAlchemy ORM
│   ├── config_loader.py # YAML configuration loading
│   ├── cache.py         # Two-level caching
│   ├── logging.py       # Structured logging
│   ├── validation_store.py  # Validation persistence
│   ├── validator_router.py  # Validator dispatch
│   ├── error_formatter.py   # Error formatting
│   ├── file_utils.py        # File operations
│   ├── performance.py       # Performance tracking
│   └── language_utils.py    # Language enforcement
├── config/              # Configuration files
│   ├── main.yaml            # Master configuration
│   ├── agent.yaml           # Agent-specific settings
│   ├── validation_flow.yaml # Validation orchestration
│   ├── cache.yaml           # Cache configuration
│   ├── code.yaml            # Code validation rules
│   ├── frontmatter.yaml     # Frontmatter validation
│   ├── links.yaml           # Link validation
│   ├── markdown.yaml        # Markdown validation
│   ├── structure.yaml       # Structure validation
│   ├── truth.yaml           # Truth validation
│   ├── seo.yaml             # SEO validation
│   ├── llm.yaml             # LLM configuration (optional)
│   ├── perf.json            # Performance tuning
│   └── tone.json            # LLM tone/style
├── data/                # Runtime data
│   ├── tbcv.db          # SQLite database
│   ├── logs/            # Application logs
│   └── cache/           # Two-level cache storage
├── docs/                # Documentation
│   ├── implementation/  # Technical implementation notes
│   ├── operations/      # Operational guides
│   └── testing/         # Testing guides
├── migrations/          # Database migrations
├── prompts/             # LLM prompts (optional)
├── reports/             # Analysis reports
├── rules/               # Validation rules
├── scripts/             # Utility scripts
│   ├── maintenance/     # System diagnostics
│   ├── testing/         # Test runners
│   ├── utilities/       # Database utilities
│   ├── systemd/         # Linux service management
│   └── windows/         # Windows service management
├── svc/                 # Background services
│   └── mcp_server.py    # Model Context Protocol server
├── templates/           # Jinja2 templates for web dashboard
├── tests/               # Test suite
│   ├── agents/          # Agent tests
│   ├── api/             # API tests
│   ├── cli/             # CLI tests
│   ├── core/            # Core tests
│   ├── contracts/       # Contract tests
│   ├── e2e/             # End-to-end tests
│   ├── manual/          # Manual test scripts
│   ├── startup/         # Startup tests
│   └── ui/              # UI tests (Playwright)
├── truth/               # Plugin truth data
│   ├── aspose_words_plugins_truth.json
│   ├── aspose_words_plugins_combinations.json
│   ├── words.json, cells.json, slides.json, pdf.json
│   └── words/           # Family-specific truth files
├── main.py              # Application entry point
├── requirements.txt     # Python dependencies
├── CHANGELOG.md         # Version history
└── README.md            # This file
```

---

## Configuration

TBCV uses hierarchical YAML/JSON configuration:

1. **Base config**: `config/main.yaml` (system settings)
2. **Agent config**: `config/agent.yaml` (per-agent settings)
3. **Validator configs**: `config/*.yaml` (8 modular validator configs)
4. **Validation flow**: `config/validation_flow.yaml` (tiered execution, profiles)
5. **Performance**: `config/perf.json` (tuning parameters)
6. **Environment overrides**: Environment variables with `TBCV_` prefix

### Key Configuration Files

- **`config/main.yaml`** - System, server, agents, cache, database, workflows
- **`config/validation_flow.yaml`** - Validation tiers, profiles (strict/default/quick), family overrides
- **`config/cache.yaml`** - L1/L2 cache settings
- **`config/seo.yaml`** - SEO and heading size limits
- **`config/truth.yaml`** - Truth validation configuration
- **`config/llm.yaml`** - LLM settings (optional, disabled by default)

### Environment Variable Example

```bash
export TBCV_LLM_VALIDATOR__ENABLED=true  # Enable LLM validation
export TBCV_LLM_VALIDATOR__MODEL=mistral
export TBCV_FUZZY_DETECTOR__SIMILARITY_THRESHOLD=0.9
```

See [Configuration Guide](docs/configuration.md) for complete reference.

---

## Testing

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests
pytest -m e2e           # End-to-end tests

# Run with coverage
pytest --cov=. --cov-report=html

# Run tests requiring Ollama (optional LLM validation)
TBCV_LLM_VALIDATOR__ENABLED=true pytest tests/test_llm_validator.py
```

See [Testing Guide](docs/testing.md) for test structure and details.

---

## Deployment

### Local Development

```bash
python main.py --mode api --host 127.0.0.1 --port 8080 --reload
```

### Production (Systemd on Linux)

```bash
# Copy service file
sudo cp scripts/systemd/tbcv.service /etc/systemd/system/

# Enable and start
sudo systemctl enable tbcv
sudo systemctl start tbcv

# Check status
sudo systemctl status tbcv
```

See [scripts/systemd/README.md](scripts/systemd/README.md) for Linux service management.

### Production (Windows Service)

See [scripts/windows/README.md](scripts/windows/README.md) for Windows service setup.

### Cloud Deployment

See [Deployment Guide](docs/deployment.md) for cloud deployment patterns (AWS, Heroku, Railway, etc.).

---

## Performance

TBCV is optimized for high-throughput validation:

**Typical Performance** (actual results may vary):
- Small files (<5KB): <300ms validation time
- Medium files (5-50KB): <1000ms validation time
- Large files (50KB-1MB): <3000ms validation time
- Concurrent workflows: Up to 50 simultaneous workflows
- Batch processing: 4-16 parallel workers (configurable)
- Cache hit rate: 80%+ for repeated validations
- LLM concurrency: Gated to 1 concurrent request (configurable)

Performance tuning in `config/main.yaml`:

```yaml
performance:
  max_concurrent_workflows: 50
  worker_pool_size: 4
  memory_limit_mb: 2048
  cpu_limit_percent: 80
```

---

## Security

- **Input validation**: All user input validated via Pydantic models
- **HTML sanitization**: Bleach library for safe HTML processing
- **Link validation**: Timeout-protected HTTP requests
- **Code analysis**: Security scanning for common vulnerabilities
- **SQL injection protection**: SQLAlchemy parameterized queries
- **CORS**: Configurable allowed origins
- **File system access**: Restricted to configured directories
- **English-only enforcement**: Language detection prevents non-English content

---

## Troubleshooting

### Ollama Connection Issues (Optional LLM Validation)

```bash
# Check if Ollama is running (if using LLM validation)
curl http://localhost:11434/api/tags

# Start Ollama (if needed)
ollama serve

# Pull required model
ollama pull mistral  # or llama2
```

### Database Lock Errors

```bash
# Check database connection
python -c "from core.database import db_manager; print(db_manager.is_connected())"

# Reset database (WARNING: deletes all data)
rm data/tbcv.db
python -c "from core.database import db_manager; db_manager.initialize_database()"
```

### Agent Not Responding

```bash
# Check agent status
curl http://localhost:8080/agents

# View agent logs
tail -f data/logs/tbcv.log | grep agent_id
```

See [Troubleshooting Guide](docs/troubleshooting.md) for more solutions.

---

## Contributing

We welcome contributions! Please see [Development Guide](docs/development.md) for:

- Code style guidelines
- Adding new validators
- Adding new agents
- Writing tests
- Submitting pull requests

---

## License

[Add license information]

---

## Support

- **Issues**: [GitHub Issues](https://github.com/your-org/tbcv/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/tbcv/discussions)
- **Documentation**: [Full Documentation](docs/)

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and release notes.

---

## Acknowledgments

Built with:
- **FastAPI** for high-performance API
- **Ollama** for local LLM inference (optional)
- **SQLAlchemy** for robust data persistence
- **Rich** for beautiful CLI output
- **Click** for intuitive command-line interface
- **Jinja2** for web templates
- **Pytest** for comprehensive testing
