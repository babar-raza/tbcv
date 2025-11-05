# TBCV System Runbook

| **Title** | System Runbook |
|---|---|
| **Version** | auto |
| **Source** | CLI analysis @ 2025-11-03T07:43:18Z |

## Overview

This runbook provides comprehensive instructions for running, configuring, and operating the TBCV (Truth-Based Content Validation) system across different environments and interfaces.

---

## Quick Start (Windows)

### Prerequisites

**Python Environment**
- Python 3.12+ (required)
- `pip` (Python package manager)
- Virtual environment (recommended)

**System Requirements**
- Windows 10/11
- 4 GB RAM minimum (8 GB recommended)
- 2 GB disk space for data and cache
- Network access for external code integration (optional)

### Installation Steps

```batch
REM 1. Create and activate virtual environment
python -m venv tbcv-env
tbcv-env\Scripts\activate

REM 2. Install dependencies
pip install -r requirements.txt

REM 3. Create data directories
mkdir data\logs
mkdir data\cache
mkdir data\temp
mkdir data\reports

REM 4. Initialize database
python -c "from core.database import db_manager; db_manager.initialize_database()"

REM 5. Validate configuration
python -m tbcv.cli check-agents
````

### 30-Second Smoke Test (No Network Required)

```batch
REM Test 1: Validate configuration
python main.py --mode api --help

REM Test 2: CLI agent check
python -m tbcv.cli check-agents

REM Test 3: Single file validation (use any existing .md file)
echo # Test Content > test.md
python -m tbcv.cli validate-file test.md --family words --format text

REM Test 4: Start API server (Ctrl+C to stop)
python main.py --mode api --port 8080
REM In browser: http://localhost:8080/health/live

REM Cleanup
del test.md
```

**Expected Results**

* Configuration loads without errors
* All agents initialize successfully
* File validation completes with results
* API server responds with `{"status": "healthy"}`

---

## Running the Application

### API Server Mode

#### Basic Startup (`main.py:139-189`)

```batch
REM Production mode
python main.py --mode api --host 0.0.0.0 --port 8080

REM Development mode with auto-reload
python main.py --mode api --host localhost --port 8080 --reload

REM Debug mode with verbose logging
python main.py --mode api --host localhost --port 8080 --log-level debug

REM Custom configuration
python main.py --mode api --host localhost --port 8080 --config config\custom.yaml
```

#### Server Configuration Options (`main.py:191-208`)

| Parameter     | Default     | Description                   | Example                             |
| ------------- | ----------- | ----------------------------- | ----------------------------------- |
| `--host`      | `127.0.0.1` | Server bind address           | `0.0.0.0` for external access       |
| `--port`      | `8080`      | Server port                   | `8000`, `8080`, `9000`              |
| `--reload`    | `False`     | Auto-reload on code changes   | Development only                    |
| `--log-level` | `info`      | Logging verbosity             | `debug`, `info`, `warning`, `error` |
| `--no-clean`  | `False`     | Skip cache cleanup on startup | For debugging                       |

#### Health Check Endpoints

```batch
REM Liveness check (basic connectivity)
curl http://localhost:8080/health/live
REM Expected: {"status": "healthy", "timestamp": "..."}

REM Readiness check (full system status)
curl http://localhost:8080/health/ready
REM Expected: {"status": "ready", "agents": {...}, "database": "connected"}

REM Detailed metrics
curl http://localhost:8080/metrics
```

### Command Line Interface

#### CLI Global Options (`cli/main.py:86-109`)

```batch
REM Global CLI options (apply to all commands)
python -m tbcv.cli --verbose [command]     REM Enable debug logging
python -m tbcv.cli --quiet [command]       REM Minimal output
python -m tbcv.cli --config path\to\config.yaml [command]  REM Custom config
```

#### Single File Validation (`cli/main.py:115-173`)

```batch
REM Basic file validation
python -m tbcv.cli validate-file content\example.md

REM Specify plugin family
python -m tbcv.cli validate-file content\example.md --family words

REM JSON output to file
python -m tbcv.cli validate-file content\example.md --output results.json --format json

REM Human-readable text output
python -m tbcv.cli validate-file content\example.md --format text
```

**`validate-file` Parameters**

| Parameter   | Required | Default | Description                                       |
| ----------- | -------- | ------- | ------------------------------------------------- |
| `file_path` | Yes      | –       | Path to file for validation                       |
| `--family`  | No       | `words` | Plugin family (`words`, `cells`, `slides`, `pdf`) |
| `--output`  | No       | stdout  | Output file path                                  |
| `--format`  | No       | `json`  | Output format (`json`, `text`)                    |

#### Directory Validation (`cli/main.py:179-250`)

```batch
REM Validate all .md files in directory
python -m tbcv.cli validate-directory content\

REM Custom file pattern
python -m tbcv.cli validate-directory content\ --pattern "*.markdown"

REM Recursive search with multiple workers
python -m tbcv.cli validate-directory content\ --recursive --workers 8

REM Summary output
python -m tbcv.cli validate-directory content\ --format summary --output summary.txt
```

**`validate-directory` Parameters**

| Parameter        | Required | Default | Description                               |
| ---------------- | -------- | ------- | ----------------------------------------- |
| `directory_path` | Yes      | –       | Directory to validate                     |
| `--pattern`      | No       | `*.md`  | File pattern to match                     |
| `--family`       | No       | `words` | Plugin family                             |
| `--workers`      | No       | `4`     | Concurrent workers (1–16)                 |
| `--recursive`    | No       | `False` | Search subdirectories                     |
| `--output`       | No       | stdout  | Output file path                          |
| `--format`       | No       | `json`  | Output format (`json`, `text`, `summary`) |

#### Agent Management

```batch
REM Check agent status
python -m tbcv.cli check-agents

REM Test agent initialization
python -m tbcv.cli test --agent fuzzy-detector

REM Run agent performance tests
python -m tbcv.cli test --performance --duration 30
```

#### Batch Processing

```batch
REM Batch validate multiple files
python -m tbcv.cli batch content\file1.md content\file2.md content\file3.md

REM Batch with custom workers
python -m tbcv.cli batch --workers 8 --family words content\*.md

REM Export results
python -m tbcv.cli batch --export csv --output batch-results.csv content\*.md
```

#### Content Enhancement

```batch
REM Enhance content based on validation results
python -m tbcv.cli enhance content\example.md --validation-id val_abc123

REM Preview enhancements without applying
python -m tbcv.cli enhance content\example.md --preview

REM Apply specific recommendations
python -m tbcv.cli enhance content\example.md --recommendations rec_001,rec_002
```

---

## Environment Variables

### Core Configuration (`core/config.py:139-175`)

```batch
REM Database configuration
set TBCV_DATABASE_URL=sqlite:///C:\tbcv\data\tbcv.db
set TBCV_DATABASE_ECHO=false

REM Server configuration
set TBCV_SERVER_HOST=0.0.0.0
set TBCV_SERVER_PORT=8080
set TBCV_SERVER_ENABLE_CORS=true

REM System configuration
set TBCV_SYSTEM_DEBUG=false
set TBCV_SYSTEM_LOG_LEVEL=info
set TBCV_SYSTEM_ENVIRONMENT=production
set TBCV_SYSTEM_DATA_DIRECTORY=C:\tbcv\data

REM Performance tuning
set TBCV_PERFORMANCE_MAX_CONCURRENT_WORKFLOWS=50
set TBCV_PERFORMANCE_WORKER_POOL_SIZE=8
set TBCV_PERFORMANCE_MEMORY_LIMIT_MB=4096

REM Cache configuration
set TBCV_CACHE_L1_ENABLED=true
set TBCV_CACHE_L1_MAX_ENTRIES=2000
set TBCV_CACHE_L1_MAX_MEMORY_MB=512
set TBCV_CACHE_L2_ENABLED=true
set TBCV_CACHE_L2_MAX_SIZE_MB=2048
```

### Agent-Specific Settings

```batch
REM Fuzzy detector configuration
set TBCV_FUZZY_DETECTOR_SIMILARITY_THRESHOLD=0.85
set TBCV_FUZZY_DETECTOR_CONTEXT_WINDOW_CHARS=200
set TBCV_FUZZY_DETECTOR_MAX_PATTERNS=1000

REM Content validator configuration
set TBCV_CONTENT_VALIDATOR_LINK_VALIDATION=true
set TBCV_CONTENT_VALIDATOR_LINK_TIMEOUT_SECONDS=5
set TBCV_CONTENT_VALIDATOR_YAML_STRICT_MODE=false

REM Content enhancer configuration
set TBCV_CONTENT_ENHANCER_AUTO_LINK_PLUGINS=true
set TBCV_CONTENT_ENHANCER_PREVENT_DUPLICATE_LINKS=true

REM Orchestrator configuration
set TBCV_ORCHESTRATOR_MAX_CONCURRENT_WORKFLOWS=25
set TBCV_ORCHESTRATOR_WORKFLOW_TIMEOUT_SECONDS=3600
set TBCV_ORCHESTRATOR_RETRY_ATTEMPTS=3

REM Truth manager configuration
set TBCV_TRUTH_MANAGER_AUTO_RELOAD=true
set TBCV_TRUTH_MANAGER_CACHE_TTL_SECONDS=604800
```

### Logging Configuration

```batch
REM Logging settings
set TBCV_LOG_LEVEL=INFO
set TBCV_LOG_FORMAT=json
set TBCV_LOG_FILE_PATH=C:\tbcv\logs\tbcv.log
set TBCV_LOG_MAX_FILE_SIZE_MB=100
set TBCV_LOG_BACKUP_COUNT=5
```

---

## Configuration Files

### Main Configuration (`config/main.yaml`)

**Location:** `config/main.yaml`
**Priority:** Environment variables override YAML settings

**Key Sections**

* `system`: Core system settings (debug, environment, data paths)
* `server`: API server configuration (host, port, CORS)
* `agents`: Agent-specific configuration for all 7 agents
* `cache`: Two-level cache settings (L1 memory + L2 persistent)
* `truth`: Truth table and rule configuration
* `performance`: Resource limits and worker configuration
* `workflows`: Workflow types and checkpoint definitions
* `logging`: Structured logging configuration
* `database`: SQLite connection and pooling settings
* `batch_processing`: Batch operation parameters

### Custom Configuration

```yaml
# config/production.yaml
system:
  environment: production
  debug: false
  log_level: info
  data_directory: "C:\\tbcv\\data"

server:
  host: "0.0.0.0"
  port: 8080
  enable_cors: false
  request_timeout_seconds: 60

performance:
  max_concurrent_workflows: 100
  worker_pool_size: 16
  memory_limit_mb: 8192

cache:
  l1:
    max_entries: 5000
    max_memory_mb: 1024
  l2:
    max_size_mb: 4096
    database_path: "C:\\tbcv\\cache\\production.db"
```

**Usage**

```batch
python main.py --mode api --config config\production.yaml
```

---

## Directory Structure

```
tbcv/
├── main.py                     # Primary application entry point
├── __main__.py                 # Package execution entry point
├── config/
│   └── main.yaml              # Main configuration file
├── agents/                     # Agent implementations
│   ├── base.py                # Agent base classes and MCP
│   ├── truth_manager.py       # Plugin truth data management
│   ├── fuzzy_detector.py      # Plugin detection algorithms
│   ├── content_validator.py   # Content quality validation
│   ├── content_enhancer.py    # Content improvement
│   ├── code_analyzer.py       # Code analysis and flow detection
│   └── orchestrator.py        # Workflow coordination
├── api/                        # REST API and web interfaces
│   ├── server.py              # FastAPI application
│   ├── dashboard.py           # Web dashboard
│   ├── websocket_endpoints.py # Real-time communication
│   └── export_endpoints.py    # Data export services
├── cli/
│   └── main.py                # Command-line interface
├── core/                       # Core infrastructure
│   ├── config.py              # Configuration management
│   ├── database.py            # Data persistence
│   ├── cache.py               # Two-level caching
│   ├── logging.py             # Structured logging
│   └── utilities.py           # Helper functions
├── data/                       # Data storage (created at runtime)
│   ├── tbcv.db                # Main SQLite database
│   ├── cache/                 # L2 persistent cache
│   ├── logs/                  # Application logs
│   ├── temp/                  # Temporary files
│   └── reports/               # Generated reports
├── truth/                      # Plugin truth tables
│   └── words.json             # Word plugin definitions
├── rules/                      # Combination rules
│   └── words.json             # Word plugin rules
├── templates/                  # HTML templates for dashboard
├── tests/                      # Test suites
├── requirements.txt            # Python dependencies
├── pyproject.toml              # Project metadata
└── README.md                  # Project documentation
```

---

## Required Arguments Summary

### Main Application (`main.py`)

| Command  | Required Args | Optional Args                                               | Example                                 |
| -------- | ------------- | ----------------------------------------------------------- | --------------------------------------- |
| API Mode | `--mode api`  | `--host`, `--port`, `--reload`, `--log-level`, `--no-clean` | `python main.py --mode api --port 8080` |

### CLI Commands (`cli/main.py`)

| Command              | Required Args    | Optional Args                                                               | Description          |
| -------------------- | ---------------- | --------------------------------------------------------------------------- | -------------------- |
| `validate-file`      | `file_path`      | `--family`, `--output`, `--format`                                          | Validate single file |
| `validate-directory` | `directory_path` | `--pattern`, `--family`, `--workers`, `--recursive`, `--output`, `--format` | Validate directory   |
| `check-agents`       | None             | None                                                                        | Check agent status   |
| `batch`              | `files...`       | `--workers`, `--family`, `--export`, `--output`                             | Batch validation     |
| `enhance`            | `file_path`      | `--validation-id`, `--preview`, `--recommendations`                         | Content enhancement  |
| `test`               | None             | `--agent`, `--performance`, `--duration`                                    | Run tests            |
| `status`             | None             | None                                                                        | System status        |

---

## Error Codes & Exit Status

| Exit Code | Meaning             | Common Causes                                  | Resolution                          |
| --------- | ------------------- | ---------------------------------------------- | ----------------------------------- |
| 0         | Success             | Operation completed successfully               | –                                   |
| 1         | General Error       | Validation failed, agent error, file not found | Check logs, verify file paths       |
| 2         | Configuration Error | Invalid arguments, missing config              | Verify command syntax, config files |
| 3         | Database Error      | Cannot connect to database, schema issues      | Check database path, permissions    |
| 4         | Network Error       | External API failure, timeout                  | Check connectivity, retry           |
| 5         | Resource Error      | Out of memory, disk space                      | Check system resources              |

---

## Performance Tuning

### Resource Optimization

**Memory Usage**

```batch
REM For systems with limited memory (< 4GB RAM)
set TBCV_PERFORMANCE_MEMORY_LIMIT_MB=1024
set TBCV_CACHE_L1_MAX_MEMORY_MB=128
set TBCV_CACHE_L2_MAX_SIZE_MB=512
set TBCV_PERFORMANCE_WORKER_POOL_SIZE=2

REM For high-memory systems (> 8GB RAM)
set TBCV_PERFORMANCE_MEMORY_LIMIT_MB=8192
set TBCV_CACHE_L1_MAX_MEMORY_MB=1024
set TBCV_CACHE_L2_MAX_SIZE_MB=4096
set TBCV_PERFORMANCE_WORKER_POOL_SIZE=16
```

**CPU Optimization**

```batch
REM For CPU-intensive workloads
set TBCV_PERFORMANCE_WORKER_POOL_SIZE=8
set TBCV_ORCHESTRATOR_MAX_CONCURRENT_WORKFLOWS=25

REM For I/O-intensive workloads
set TBCV_PERFORMANCE_WORKER_POOL_SIZE=16
set TBCV_ORCHESTRATOR_MAX_CONCURRENT_WORKFLOWS=100
```

### Batch Processing Optimization

```batch
REM Small files (< 5KB each)
python -m tbcv.cli validate-directory content\ --workers 16 --pattern "*.md"

REM Large files (> 1MB each)
python -m tbcv.cli validate-directory content\ --workers 4 --pattern "*.md"

REM Mixed file sizes with progress monitoring
python -m tbcv.cli batch --workers 8 --export progress content\*.md
```

---

## Troubleshooting Common Issues

### `"Agent not available"` Error

```batch
REM Diagnosis
python -m tbcv.cli check-agents

REM Resolution
REM 1. Check agent configuration
set TBCV_SYSTEM_DEBUG=true
python -m tbcv.cli check-agents --verbose

REM 2. Reinitialize agents
python -c "from agents.base import agent_registry; agent_registry.clear(); print('Agents cleared')"
```

### Database Connection Issues

```batch
REM Diagnosis
set TBCV_DATABASE_ECHO=true
python -c "from core.database import db_manager; print(db_manager.test_connection())"

REM Resolution
REM 1. Check database path
dir data\tbcv.db

REM 2. Reinitialize database
python -c "from core.database import db_manager; db_manager.initialize_database(force=True)"
```

### Cache Performance Issues

```batch
REM Clear all caches
python -c "from core.cache import cache_manager; cache_manager.clear_all()"

REM Check cache statistics
curl http://localhost:8080/metrics | findstr cache
```

### Memory Usage Issues

```batch
REM Reduce memory footprint
set TBCV_CACHE_L1_MAX_ENTRIES=500
set TBCV_CACHE_L1_MAX_MEMORY_MB=64
set TBCV_PERFORMANCE_WORKER_POOL_SIZE=2
set TBCV_ORCHESTRATOR_MAX_CONCURRENT_WORKFLOWS=10

REM Enable memory monitoring
set TBCV_SYSTEM_DEBUG=true
python main.py --mode api --log-level debug
```

---

**Next Steps**

* **[Operations Guide](operations.md)** — Monitoring and maintenance
* **[Data Flow](dataflow.md)** — Understanding data management
* **[Architecture](architecture.md)** — System component interactions