# TBCV Component Reference
> Title: Component Details
> Version: auto
> Source: Code analysis @ 2025-11-03T08:43:00Z

## Agent Components

### TruthManagerAgent
**Module**: `agents/truth_manager.py`
**Purpose**: Manages plugin truth data, indexes patterns, and provides efficient lookup mechanisms
**Key APIs**:
- `load_truth_table()`: Loads plugin definitions from JSON (`agents/truth_manager.py:200-250`)
- `build_index()`: Creates B-tree index for O(log n) lookups (`agents/truth_manager.py:260-320`)
- `get_plugin_info()`: Retrieves plugin metadata and patterns (`agents/truth_manager.py:400-450`)
- `check_version()`: SHA-256 based change detection (`agents/truth_manager.py:500-520`)

**Dependencies**: `json`, `hashlib`, `bisect`, `pathlib`
**I/O**: Reads from `truth/*.json`, maintains in-memory index

### FuzzyDetectorAgent  
**Module**: `agents/fuzzy_detector.py`
**Purpose**: Performs intelligent pattern matching using multiple fuzzy algorithms
**Key APIs**:
- `detect_plugins()`: Main detection interface (`agents/fuzzy_detector.py:90-150`)
- `calculate_similarity()`: Multi-algorithm scoring (`agents/fuzzy_detector.py:60-85`)
- `apply_context_window()`: Context-aware pattern search (`agents/fuzzy_detector.py:160-180`)

**Dependencies**: `fuzzywuzzy`, `Levenshtein`, `difflib`
**I/O**: Takes content strings, returns `PluginDetection` objects with confidence scores

### ContentValidatorAgent
**Module**: `agents/content_validator.py`
**Purpose**: Validates content structure, frontmatter, and code quality
**Key APIs**:
- `validate_content()`: Full validation pipeline (`agents/content_validator.py:100-200`)
- `validate_yaml()`: YAML frontmatter checks (`agents/content_validator.py:250-350`)
- `validate_markdown()`: Structure and heading analysis (`agents/content_validator.py:400-450`)
- `validate_code()`: Language-specific quality checks (`agents/content_validator.py:460-496`)

**Dependencies**: `yaml`, `markdown`, `ast`, `asyncio`
**I/O**: Processes markdown/code files, returns `ValidationResult` with issues

### ContentEnhancerAgent
**Module**: `agents/content_enhancer.py`
**Purpose**: Enhances content with plugin links, formatting fixes, and information insertion
**Key APIs**:
- `enhance_content()`: Main enhancement workflow (`agents/content_enhancer.py:80-150`)
- `add_plugin_links()`: First-occurrence linking (`agents/content_enhancer.py:200-280`)
- `fix_formatting()`: Heading and list normalization (`agents/content_enhancer.py:300-350`)
- `insert_info_text()`: Contextual information addition (`agents/content_enhancer.py:360-400`)

**Dependencies**: `markdown`, `re`, `ast`
**I/O**: Takes raw content, returns `EnhancementResult` with modified text

### CodeAnalyzerAgent
**Module**: `agents/code_analyzer.py`
**Purpose**: Advanced code analysis with Aspose document flow understanding
**Key APIs**:
- `analyze_code()`: Main analysis pipeline (`agents/code_analyzer.py:150-300`)
- `detect_document_flow()`: Aspose pattern detection (`agents/code_analyzer.py:400-600`)
- `fetch_external_code()`: GitHub/gist integration (`agents/code_analyzer.py:700-800`)
- `detect_security_issues()`: Vulnerability scanning (`agents/code_analyzer.py:850-950`)

**Dependencies**: `ast`, `requests`, `github`, `bandit`
**I/O**: Analyzes code samples, returns `CodeAnalysisResult` with issues/fixes

### OrchestratorAgent
**Module**: `agents/orchestrator.py`
**Purpose**: Coordinates multi-agent workflows with dependency management
**Key APIs**:
- `execute_workflow()`: Main workflow engine (`agents/orchestrator.py:100-200`)
- `manage_dependencies()`: Step ordering logic (`agents/orchestrator.py:220-280`)
- `handle_retries()`: Exponential backoff implementation (`agents/orchestrator.py:290-320`)
- `save_state()`: Workflow persistence (`agents/orchestrator.py:330-356`)

**Dependencies**: All other agents, `core.database`
**I/O**: Manages workflow states in database, returns `WorkflowResult`

## API Components

### FastAPI Server
**Module**: `api/server.py`
**Purpose**: Primary REST API interface
**Key Endpoints**:
- `POST /validate/content`: Single content validation
- `POST /validate/batch`: Batch processing
- `POST /enhance`: Content enhancement
- `GET /health`: System health check
- `GET /metrics`: Performance metrics

**Dependencies**: `fastapi`, `uvicorn`, all agents
**I/O**: HTTP requests/responses, JSON payloads

### Dashboard Interface
**Module**: `api/dashboard.py`
**Purpose**: Web-based management UI
**Key Features**:
- Validation result visualization
- Workflow monitoring dashboard
- Recommendation approval interface
- Audit log viewer

**Dependencies**: `fastapi`, `jinja2`, `htmx`
**I/O**: HTML templates, WebSocket updates

### WebSocket Endpoints
**Module**: `api/websocket_endpoints.py`
**Purpose**: Real-time communication channel
**Key APIs**:
- `ws:/progress/{workflow_id}`: Live progress updates
- `ws:/results`: Real-time validation results
- `ws:/status`: System status broadcasts

**Dependencies**: `fastapi.websocket`, `asyncio`
**I/O**: WebSocket connections, JSON messages

### Export Services
**Module**: `api/export_endpoints.py`
**Purpose**: Data export and reporting
**Key Endpoints**:
- `GET /export/csv`: CSV export
- `GET /export/json`: JSON export
- `POST /report/generate`: Custom reports

**Dependencies**: `pandas`, `csv`, `json`
**I/O**: File downloads, structured data

## Core Infrastructure

### Database Manager
**Module**: `core/database.py`
**Purpose**: Data persistence layer
**Key Classes**:
- `DatabaseManager`: Connection handling (`core/database.py:50-150`)
- `WorkflowState`: State tracking model (`core/database.py:200-300`)
- `ValidationResult`: Result storage (`core/database.py:400-500`)

**Dependencies**: `sqlalchemy`, `sqlite3`
**I/O**: SQLite database operations

### Configuration System
**Module**: `core/config.py`
**Purpose**: Application settings management
**Key APIs**:
- `load_config()`: Environment-based loading
- `get_validation_rules()`: Rule definitions
- `get_plugin_patterns()`: Pattern configurations

**Dependencies**: `pydantic`, `yaml`, `os`
**I/O**: YAML config files, environment variables

### Cache Layer
**Module**: `core/cache.py`
**Purpose**: Two-level caching system
**Key APIs**:
- `L1Cache`: In-memory LRU cache
- `L2Cache`: Persistent SQLite cache
- `invalidate()`: Cache clearing logic

**Dependencies**: `functools.lru_cache`, `sqlite3`
**I/O**: Memory and disk cache operations

### Logging System
**Module**: `core/logging.py`
**Purpose**: Structured logging and monitoring
**Key APIs**:
- `setup_logging()`: Logger configuration
- `log_performance()`: Metric collection
- `audit_log()`: Audit trail recording

**Dependencies**: `logging`, `json`, `datetime`
**I/O**: Log files, stdout/stderr

## CLI Components

### Command Line Interface
**Module**: `cli/main.py`
**Purpose**: Direct command-line access
**Commands**:
- `validate [file/dir]`: Content validation
- `enhance [file]`: Content enhancement
- `batch [input] [output]`: Batch processing
- `config [action]`: Configuration management

**Dependencies**: `click`, all agents
**I/O**: Command-line arguments, file system

## Data Components

### Truth Tables
**Location**: `truth/*.json`
**Purpose**: Plugin pattern definitions
**Structure**: JSON with plugin families, patterns, combination rules

### Validation Rules
**Location**: `rules/*.yaml`
**Purpose**: Content validation configurations
**Structure**: YAML with rule definitions, severity levels

### Templates
**Location**: `templates/*.html`
**Purpose**: Web UI templates
**Structure**: Jinja2 HTML templates

### Database Schema
**Location**: `tbcv.db`
**Purpose**: Persistent data storage
**Tables**: workflows, results, recommendations, audit_logs

## Test Components

### Agent Tests
**Location**: `tests/test_agents_*.py`
**Purpose**: Agent functionality validation
**Coverage**: All agent methods, edge cases

### API Tests
**Location**: `tests/test_api_*.py`
**Purpose**: API endpoint testing
**Coverage**: All endpoints, error handling

### Integration Tests
**Location**: `tests/test_integration_*.py`
**Purpose**: End-to-end workflow testing
**Coverage**: Complete processing pipelines

---

For architecture overview, see [Architecture](architecture.md)
For operational details, see [Operations Guide](operations.md)
