# TBCV - Truth-Based Content Validation System

**Version 2.0.0** | Multi-Agent Content Validation and Enhancement Platform

## Overview

TBCV is an intelligent content processing system that validates, analyzes, and enhances technical documentation through a sophisticated multi-agent architecture. It specializes in detecting plugin usage patterns, ensuring documentation quality, and providing AI-powered recommendations through a human-in-the-loop approval workflow.

### Key Features

- **8-Agent Architecture**: Specialized agents coordinate via Model Context Protocol (MCP)
- **Intelligent Plugin Detection**: Fuzzy matching algorithms with 50+ Aspose plugin patterns
- **Two-Stage Truth Validation**:
  - **Heuristic Layer**: Pattern matching for plugin declaration vs usage
  - **LLM Semantic Layer** (NEW!): AI-powered validation of technical accuracy, plugin combinations, and format compatibility
- **Multi-Stage Validation**: YAML frontmatter, Markdown structure, code quality, and semantic LLM validation
- **Recommendation Workflow**: Human-approved enhancement suggestions with confidence scoring
- **Re-validation & Comparison** (Phase 2): Compare validation results before/after enhancement with improvement metrics
- **Recommendation Requirements** (Phase 2): Enforce approval requirements before content enhancement
- **Automated Background Processing** (Phase 2): Cron job for automatic recommendation generation
- **Workflow Orchestration**: Complex multi-step processing with checkpointing and recovery
- **Multiple Interfaces**: REST API, CLI, WebSocket real-time updates, and web dashboard
- **Persistent Storage**: SQLite database with two-level caching (L1 in-memory + L2 disk)
- **External Integration**: Ollama LLM for semantic validation, GitHub repository analysis

## Quick Start

### Prerequisites

- **Python 3.8+**
- **pip** for package management
- **Ollama** (optional, for LLM validation) - [Install Ollama](https://ollama.ai)

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
# Method 1: Using main.py entry point
python main.py --mode api --host 0.0.0.0 --port 8080

# Method 2: Using uvicorn directly
uvicorn api.server:app --host 0.0.0.0 --port 8080 --reload
```

Server will be available at: **http://localhost:8080**

### Test the Installation

```bash
# Check health
curl http://localhost:8080/health/live

# View API index
open http://localhost:8080

# Test validation (CLI)
python -m cli.main validate-file path/to/file.md --family words --format text
```

## System Architecture

TBCV employs a multi-agent architecture where 8 specialized agents collaborate through the Model Context Protocol (MCP):

### Core Agents

1. **TruthManagerAgent** - Manages plugin truth data with multi-level indexing
2. **FuzzyDetectorAgent** - Detects plugin usage via regex patterns and fuzzy matching
3. **ContentValidatorAgent** - Legacy monolithic validator (being replaced by modular validators)
4. **ContentEnhancerAgent** - Enhances content with plugin links and info text (with safety gating)
5. **LLMValidatorAgent** - AI-powered semantic validation using Ollama
6. **CodeAnalyzerAgent** - Analyzes code quality and security
7. **OrchestratorAgent** - Coordinates multi-agent workflows with concurrency control
8. **RecommendationAgent** - Generates actionable improvement recommendations

### Modular Validator Architecture (NEW!)

TBCV 2.1.0 introduces a new modular validator architecture that replaces the monolithic ContentValidatorAgent with specialized validator agents:

**Validator Agents:**
- **SeoValidatorAgent** - SEO headings and heading sizes validation
- **YamlValidatorAgent** - YAML frontmatter validation
- **MarkdownValidatorAgent** - Markdown syntax validation
- **CodeValidatorAgent** - Code block validation
- **LinkValidatorAgent** - Link and URL validation
- **StructureValidatorAgent** - Document structure validation
- **TruthValidatorAgent** - Truth data validation

**Benefits:**
- ✅ Modular design (150-330 lines per validator vs 2100 monolithic)
- ✅ Easy to extend (add new validators in 2-4 hours)
- ✅ Individual enable/disable via configuration
- ✅ Dynamic validator discovery via API
- ✅ Backward compatible with legacy system

### Data Flow

```
Input (Markdown file)
    ↓
TruthManagerAgent (Load plugin definitions)
    ↓
FuzzyDetectorAgent (Detect plugin usage)
    ↓
ContentValidatorAgent (Validate structure + two-stage truth validation)
    ├─ Heuristic validation (pattern matching)
    └─ LLM semantic validation (technical accuracy, combinations)
    ↓
LLMValidatorAgent (Additional semantic validation)
    ↓
RecommendationAgent (Generate suggestions)
    ↓
[Human Review & Approval]
    ↓
ContentEnhancerAgent (Apply approved recommendations)
    ↓
Database (Persist results + audit trail)
```

### Technology Stack

- **Backend**: Python 3.8+, FastAPI, Uvicorn
- **Database**: SQLAlchemy ORM with SQLite (PostgreSQL/MySQL supported)
- **Caching**: Two-level (L1 in-memory LRU + L2 disk-based SQLite)
- **LLM Integration**: Ollama (llama2), with fallback support for OpenAI/Gemini
- **Fuzzy Matching**: Levenshtein distance, Jaro-Winkler similarity
- **CLI**: Click framework with Rich console output
- **WebSocket**: Real-time updates via SSE (Server-Sent Events)
- **Logging**: Structured JSON logging with rotation

## Documentation

### Getting Started
- [Configuration](docs/configuration.md) - Configure agents, caching, and LLM settings
- [Deployment](docs/deployment.md) - Local and production deployment
- [Troubleshooting](docs/troubleshooting.md) - Common issues and solutions

### Core Concepts
- [Architecture](docs/architecture.md) - System design and components
- [Agents](docs/agents.md) - Detailed agent descriptions
- [Workflows](docs/workflows.md) - Validation and enhancement workflows
- [Truth Store](docs/truth_store.md) - Plugin definitions and detection rules

### Usage
- [CLI Usage](docs/cli_usage.md) - Command-line interface reference
- [API Reference](docs/api_reference.md) - REST endpoints and request/response schemas
- [Web Dashboard](docs/web_dashboard.md) - Web UI for managing validations

### Development
- [Development Guide](docs/development.md) - Contributing and extending TBCV
- [Testing](docs/testing.md) - Running tests and test structure

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
    "max_workers": 4
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

## Project Structure

```
tbcv/
├── agents/              # Multi-agent system (8 agents)
│   ├── base.py         # MCP-compliant base agent
│   ├── orchestrator.py # Workflow coordination
│   ├── fuzzy_detector.py  # Plugin detection
│   ├── content_validator.py  # Content validation
│   ├── content_enhancer.py   # Enhancement with gating
│   ├── llm_validator.py      # Ollama integration
│   ├── truth_manager.py      # Truth data indexing
│   ├── code_analyzer.py      # Code analysis
│   ├── recommendation_agent.py  # Recommendation generation
│   └── enhancement_agent.py     # Recommendation application
├── api/                # FastAPI server
│   ├── server.py       # Main API with 40+ endpoints
│   ├── dashboard.py    # Web UI routes
│   ├── websocket_endpoints.py  # Real-time updates
│   └── services/       # Background services
├── cli/                # Command-line interface
│   └── main.py         # Click-based CLI with 10+ commands
├── core/               # Core infrastructure
│   ├── database.py     # SQLAlchemy ORM (6 tables)
│   ├── config.py       # Pydantic settings with env overrides
│   ├── cache.py        # Two-level caching
│   ├── logging.py      # Structured JSON logging
│   ├── ollama.py       # LLM client
│   └── rule_manager.py # Validation rules
├── config/             # Configuration files
│   ├── main.yaml       # Main system configuration
│   └── agent.yaml      # Per-agent configuration
├── data/               # Runtime data (database, logs, cache)
│   ├── tbcv.db        # SQLite database
│   ├── logs/          # Application logs
│   └── cache/         # Two-level cache storage
├── docs/               # Documentation
│   ├── implementation/ # Technical implementation summaries
│   ├── operations/    # Operational guides and procedures
│   └── archive/       # Historical documentation
├── migrations/         # Database migrations
├── prompts/            # LLM prompts
├── reports/            # Analysis reports and session summaries
│   ├── organization/  # Project organization reports
│   ├── sessions/      # Session-specific reports
│   └── archive/       # Historical reports
├── rules/              # Validation rules
├── scripts/            # Utility and maintenance scripts
│   ├── maintenance/   # System diagnostics
│   ├── testing/       # Test runners
│   ├── utilities/     # Database and system utilities
│   ├── systemd/       # Linux service management
│   └── windows/       # Windows service management
├── svc/                # Background services
├── templates/          # Jinja2 templates for web dashboard
├── tests/              # Test suite
│   ├── manual/        # Ad-hoc manual tests
│   │   └── fixtures/  # Test data files
│   ├── agents/        # Agent-specific tests
│   ├── api/           # API tests
│   ├── cli/           # CLI tests
│   └── core/          # Core infrastructure tests
├── tools/              # Development tools
├── truth/              # Plugin truth data
│   ├── aspose_words_plugins_truth.json
│   ├── aspose_words_plugins_combinations.json
│   ├── words.json, cells.json, slides.json, pdf.json
│   └── words/          # Family-specific truth files
├── main.py             # Application entry point
├── requirements.txt    # Python dependencies
├── CHANGELOG.md        # Version history
└── README.md           # This file
```

## Configuration

TBCV uses a hierarchical configuration system:

1. **Base config**: `config/main.yaml`
2. **Agent-specific config**: `config/agent.yaml`
3. **Environment overrides**: Environment variables with `TBCV_` prefix
4. **Runtime config**: Performance tuning in `config/perf.json`

Example environment variable override:

```bash
export TBCV_LLM__ENABLED=true
export TBCV_LLM__MODEL=llama2
export TBCV_FUZZY_DETECTOR__SIMILARITY_THRESHOLD=0.9
```

See [Configuration Guide](docs/configuration.md) for complete reference.

## Testing

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests
pytest -m performance   # Performance benchmarks
pytest -m e2e           # End-to-end tests

# Run with coverage
pytest --cov=. --cov-report=html

# Run tests requiring Ollama
TBCV_LLM__ENABLED=true pytest tests/test_llm_validator.py
```

See [Testing Guide](docs/testing.md) for details.

## Deployment

### Local Development

```bash
python main.py --mode api --host 127.0.0.1 --port 8080 --reload
```

### Production (Systemd)

```bash
# Copy service file
sudo cp tbcv.service /etc/systemd/system/

# Enable and start
sudo systemctl enable tbcv
sudo systemctl start tbcv

# Check status
sudo systemctl status tbcv
```

### Docker

```bash
# Build image
docker build -t tbcv:latest .

# Run container
docker run -p 8080:8080 -v ./data:/app/data tbcv:latest

# Or use docker-compose
docker-compose up -d
```

See [Deployment Guide](docs/deployment.md) for cloud deployment patterns (AWS, Heroku, Railway).

## Performance

TBCV is optimized for high-throughput content validation:

- **Small files (<5KB)**: <300ms validation time
- **Medium files (5-50KB)**: <1000ms validation time
- **Large files (50KB-1MB)**: <3000ms validation time
- **Concurrent workflows**: Up to 50 simultaneous workflows
- **Batch processing**: 4-16 parallel workers (configurable)
- **Cache hit rate**: 80%+ for repeated validations
- **LLM concurrency**: Gated to 1 concurrent request (configurable)

Performance tuning in `config/main.yaml`:

```yaml
performance:
  max_concurrent_workflows: 50
  worker_pool_size: 4
  memory_limit_mb: 2048
  cpu_limit_percent: 80
```

## Security

- **Input validation**: All user input validated via Pydantic models
- **HTML sanitization**: Bleach library for safe HTML processing
- **Link validation**: Timeout-protected HTTP requests
- **Code analysis**: Security scanning for common vulnerabilities
- **SQL injection protection**: SQLAlchemy parameterized queries
- **CORS**: Configurable allowed origins
- **Authentication**: Ready for integration (JWT, OAuth2)

## Troubleshooting

### Ollama Connection Issues

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve

# Pull required model
ollama pull llama2
```

### Database Lock Errors

```bash
# Check for orphaned connections
python -c "from core.database import db_manager; print(db_manager.is_connected())"

# Reset database
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

## Contributing

We welcome contributions! Please see [Development Guide](docs/development.md) for:

- Code style guidelines
- Adding new agents
- Writing tests
- Submitting pull requests

## License

[Add license information]

## Support

- **Issues**: [GitHub Issues](https://github.com/your-org/tbcv/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/tbcv/discussions)
- **Documentation**: [Full Documentation](docs/)

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and release notes.

## Acknowledgments

Built with:
- FastAPI for high-performance API
- Ollama for local LLM inference
- SQLAlchemy for robust data persistence
- Rich for beautiful CLI output
- Click for intuitive command-line interface
