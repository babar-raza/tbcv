# TBCV - Truth-Based Content Validation System

> **Intelligent Content Validation & Enhancement Platform**  
> Multi-agent system for automated plugin detection, content validation, and quality enhancement

## Quick Overview

TBCV is a sophisticated Python-based platform that automates the validation and enhancement of technical documentation through intelligent plugin detection, fuzzy matching algorithms, and AI-powered code analysis. The system employs a multi-agent architecture to provide comprehensive content processing capabilities.

### Key Features

- **🤖 Multi-Agent Architecture**: 6 specialized agents coordinating through Model Context Protocol (MCP)
- **🔍 Intelligent Plugin Detection**: Fuzzy matching algorithms with 50+ Aspose plugin patterns
- **📊 Content Validation**: YAML, Markdown, and code quality assessment
- **✨ Automatic Enhancement**: Plugin linking and content improvement
- **🔄 Workflow Orchestration**: Complex multi-step processing pipelines
- **🌐 Multiple Interfaces**: REST API, CLI, WebSocket, and web dashboard
- **💾 Persistent Storage**: SQLite database with two-level caching
- **🔗 External Integration**: GitHub gists and repository analysis

### Quick Start

```batch
REM Install dependencies
pip install -r requirements.txt

REM Initialize database
python -c "from core.database import db_manager; db_manager.initialize_database()"

REM Start API server
python main.py --mode api --port 8080

REM Test single file validation
python -m tbcv.cli validate-file content\example.md --family words
````

**Health Check**: [http://localhost:8080/health/live](http://localhost:8080/health/live)
**Dashboard**: [http://localhost:8080/dashboard](http://localhost:8080/dashboard)

---

## 📚 Documentation Navigation

### Getting Started

| Document                                   | Purpose                                   | For Who                         |
| ------------------------------------------ | ----------------------------------------- | ------------------------------- |
| **[System Overview](reference/system.md)** | Executive summary, capabilities, scope    | Managers, architects, new users |
| **[Runbook](reference/runbook.md)**        | Installation, configuration, CLI commands | Developers, operators           |
| **[Quick Start](#quick-start)**            | 30-second setup and smoke tests           | Everyone                        |

### Architecture & Design

| Document                                                      | Purpose                                     | For Who                       |
| ------------------------------------------------------------- | ------------------------------------------- | ----------------------------- |
| **[Architecture Overview](reference/architecture.md)**        | System components, interactions, containers | Architects, senior developers |
| **[Process Flows](reference/process-flows.md)**               | Workflow sequences, agent coordination      | Developers, integrators       |
| **[Features ↔ Modules Matrix](reference/features-matrix.md)** | Feature implementation mapping              | Developers, maintainers       |

### Operations & Data

| Document                                            | Purpose                                  | For Who                    |
| --------------------------------------------------- | ---------------------------------------- | -------------------------- |
| **[Operations Guide](reference/operations.md)**     | Monitoring, troubleshooting, maintenance | DevOps, support teams      |
| **[Data Flow & Management](reference/dataflow.md)** | Schemas, storage, lifecycle, caching     | Data engineers, developers |

### Development Resources

| Resource              | Purpose                           | Location                                                       |
| --------------------- | --------------------------------- | -------------------------------------------------------------- |
| **Per-File Analysis** | Detailed code analysis (81 files) | [reports/per-file-summaries.md](reports/per-file-summaries.md) |
| **File Inventory**    | Complete project catalog          | [reports/file-inventory.md](reports/file-inventory.md)         |
| **Configuration**     | System configuration reference    | [config/main.yaml](config/main.yaml)                           |
| **API Tests**         | Endpoint testing suites           | [tests/](tests/)                                               |

---

## 🎯 Use Cases

### Content Validation

```batch
REM Validate single Markdown file
python -m tbcv.cli validate-file docs\api-guide.md --format text

REM Validate entire documentation directory
python -m tbcv.cli validate-directory docs\ --recursive --workers 8

REM Batch validate with custom pattern
python -m tbcv.cli validate-directory content\ --pattern "*.markdown" --format summary
```

### Plugin Detection

```batch
REM Detect Aspose plugin usage in code samples
python -m tbcv.cli validate-file examples\word-processing.md --family words

REM API endpoint for plugin detection
curl -X POST http://localhost:8080/validate/content ^
  -H "Content-Type: application/json" ^
  -d "{\"content\":\"Document.Save(filename)\",\"family\":\"words\"}"
```

### Content Enhancement

```batch
REM Enhance content with plugin links
python -m tbcv.cli enhance content\example.md --validation-id val_abc123

REM Preview enhancements without applying
python -m tbcv.cli enhance content\example.md --preview

REM API endpoint for enhancement
curl -X POST http://localhost:8080/enhance/content ^
  -H "Content-Type: application/json" ^
  -d "{\"validation_id\":\"val_abc123\",\"file_path\":\"example.md\"}"
```

### Code Analysis

```batch
REM Analyze external GitHub gist
curl -X POST http://localhost:8080/analyze/code ^
  -H "Content-Type: application/json" ^
  -d "{\"url\":\"https://gist.github.com/username/abc123\"}"

REM Analyze document processing flow
python -c "from agents.code_analyzer import CodeAnalyzerAgent; agent = CodeAnalyzerAgent('test'); result = agent.analyze_document_flow(code_sample)"
```

---

## 🏗️ System Architecture

### Multi-Agent Design

```
┌─────────────────────────────────────────────────────────────────────┐
│                      TBCV Agent Ecosystem                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐           │
│  │   Truth      │◄──►│    Fuzzy     │◄──►│   Content    │           │
│  │  Manager     │    │  Detector    │    │  Validator   │           │
│  │   Agent      │    │    Agent     │    │    Agent     │           │
│  └──────────────┘    └──────────────┘    └──────────────┘           │
│         ▲                     ▲                     ▲               │
│         │                     │                     │               │
│         ▼                     ▼                     ▼               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐           │
│  │ Orchestrator │◄──►│     Code     │◄──►│   Content    │           │
│  │    Agent     │    │  Analyzer    │    │  Enhancer    │           │
│  │              │    │    Agent     │    │    Agent     │           │
│  └──────────────┘    └──────────────┘    └──────────────┘           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Technology Stack

* **Backend**: Python 3.12+, FastAPI, SQLAlchemy, AsyncIO
* **Database**: SQLite with connection pooling
* **Caching**: Two-level (L1 memory + L2 persistent)
* **APIs**: REST endpoints, WebSocket real-time updates
* **CLI**: Rich console interface with progress tracking
* **Testing**: Pytest with comprehensive coverage
* **Deployment**: Uvicorn ASGI server

---

## ⚙️ Configuration

### Environment Variables

```batch
REM Core system configuration
set TBCV_SERVER_HOST=0.0.0.0
set TBCV_SERVER_PORT=8080
set TBCV_SYSTEM_LOG_LEVEL=info
set TBCV_DATABASE_URL=sqlite:///./data/tbcv.db

REM Performance tuning
set TBCV_PERFORMANCE_WORKER_POOL_SIZE=8
set TBCV_PERFORMANCE_MAX_CONCURRENT_WORKFLOWS=50
set TBCV_CACHE_L1_MAX_MEMORY_MB=512
set TBCV_CACHE_L2_MAX_SIZE_MB=2048

REM Agent configuration
set TBCV_FUZZY_DETECTOR_SIMILARITY_THRESHOLD=0.85
set TBCV_CONTENT_VALIDATOR_LINK_VALIDATION=true
set TBCV_CONTENT_ENHANCER_AUTO_LINK_PLUGINS=true
```

### Custom Configuration

```yaml
# config/production.yaml
system:
  environment: production
  debug: false
  data_directory: "C:\\tbcv\\data"

server:
  host: "0.0.0.0"
  port: 8080
  enable_cors: false

performance:
  max_concurrent_workflows: 100
  worker_pool_size: 16
  memory_limit_mb: 8192
```

**Usage**: `python main.py --mode api --config config\production.yaml`

---

## 🔧 Development

### Project Structure

```
tbcv/
├── agents/           # 7 specialized processing agents
├── api/              # FastAPI server and web interfaces
├── cli/              # Command-line interface
├── core/             # Database, caching, configuration
├── config/           # YAML configuration files
├── data/             # Runtime data (database, logs, cache)
├── truth/            # Plugin truth tables and rules
├── templates/        # HTML templates for dashboard
├── tests/            # Comprehensive test suites
└── reference/        # Complete system documentation
```

### Running Tests

```batch
REM Run all tests
pytest tests/

REM Agent-specific tests
pytest tests/test_smoke_agents.py -v

REM Performance benchmarks
pytest tests/test_performance.py --benchmark

REM API endpoint tests
pytest tests/test_endpoints_live.py tests/test_endpoints_offline.py

REM CLI smoke test
python -m tbcv.cli check-agents
```

### Agent Development

Each agent inherits from `agents.base.BaseAgent` and implements:

* Message handling via Model Context Protocol (MCP)
* Asynchronous processing capabilities
* Automatic retry logic with exponential backoff
* Performance monitoring and caching

**Example Agent Structure**:

```python
from agents.base import BaseAgent, MessageType

class CustomAgent(BaseAgent):
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self._register_message_handlers()
    
    async def process_request(self, request_type: str, data: dict) -> dict:
        # Implementation here
        pass
```

---

## 📊 Monitoring & Health

### Health Endpoints

```batch
REM Basic health check
curl http://localhost:8080/health/live

REM Detailed system status
curl http://localhost:8080/health/ready

REM Performance metrics
curl http://localhost:8080/metrics

REM Agent status
curl http://localhost:8080/admin/agents/status
```

### Web Dashboard

* **Main Dashboard**: [http://localhost:8080/dashboard](http://localhost:8080/dashboard)
* **Workflow Monitor**: [http://localhost:8080/dashboard/workflows](http://localhost:8080/dashboard/workflows)
* **Agent Status**: [http://localhost:8080/dashboard/agents](http://localhost:8080/dashboard/agents)
* **Performance Metrics**: [http://localhost:8080/dashboard/metrics](http://localhost:8080/dashboard/metrics)
* **Audit Logs**: [http://localhost:8080/dashboard/logs](http://localhost:8080/dashboard/logs)

### CLI Monitoring

```batch
REM System status overview
python -m tbcv.cli status

REM Agent health check
python -m tbcv.cli check-agents --verbose

REM Performance testing
python -m tbcv.cli test --performance --duration 60
```

---

## 🚀 Deployment

### Production Deployment

```batch
REM Production server startup
python main.py --mode api --host 0.0.0.0 --port 8080 --config config\production.yaml

REM With systemd service (Linux)
sudo systemctl start tbcv
sudo systemctl enable tbcv

REM With Windows Service
python -m pip install pywin32
python service_installer.py install
net start TBCV
```

### Docker Deployment

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["python", "main.py", "--mode", "api", "--host", "0.0.0.0"]
```

```batch
REM Build and run
docker build -t tbcv:latest .
docker run -p 8080:8080 -v tbcv-data:/app/data tbcv:latest
```

---

## 📈 Performance & Scaling

### Optimization Guidelines

**Memory Optimization**

* L1 Cache: 256MB–1GB depending on available RAM
* Worker Pool: 4–16 workers based on CPU cores
* Concurrent Workflows: 25–100 based on system capacity

**I/O Optimization**

* Database connection pooling (20–50 connections)
* Persistent L2 cache for expensive operations
* Async processing for all I/O operations

**Scaling Recommendations**

* **Small Environment**: 2–4 workers, 1GB memory limit
* **Medium Environment**: 8–12 workers, 4GB memory limit
* **Large Environment**: 16+ workers, 8GB+ memory limit

---

## 🛠️ Troubleshooting

### Common Issues

| Issue                     | Symptoms                   | Quick Fix                                   |
| ------------------------- | -------------------------- | ------------------------------------------- |
| **Agent Not Available**   | “Agent not found” errors   | `python -m tbcv.cli check-agents`           |
| **Database Locked**       | Connection timeout errors  | Restart application, check disk space       |
| **High Memory Usage**     | Slow responses, OOM errors | Clear caches, reduce worker count           |
| **Cache Performance**     | Slow validation times      | Check cache hit rates, increase cache sizes |
| **External API Failures** | GitHub fetch errors        | Check network, API rate limits              |

### Diagnostic Commands

```batch
REM Generate diagnostic report
curl "http://localhost:8080/admin/diagnostic" > diagnostic.json

REM Check log errors
findstr "ERROR" data\logs\tbcv.log

REM Performance analysis
findstr "processing_time_ms" data\logs\tbcv.log | sort /r

REM Memory usage trends
findstr "memory_usage_mb" data\logs\tbcv.log
```

---

## 📝 How to Update Documentation

This documentation is designed to be maintainable and current:

1. **Auto-refresh System Stats**: Use the refresh tool to update inventory data

   ```batch
   python tools\refresh_system_md.py --out reference\system.md --inventory reports\file-inventory.json
   ```
2. **Evidence-Based Claims**: All architecture claims include code references (e.g., `agents/orchestrator.py:64-356`)
3. **Mermaid Diagrams**: Update diagrams in `/reference/*.md` files as system evolves
4. **Configuration Changes**: Update `config/main.yaml` and corresponding documentation sections
5. **New Features**: Add to features matrix in `reference/features-matrix.md`

---

## 📄 License & Contributing

**License**: See project license file
**Contributing**: Follow established patterns in `agents/` and `tests/`
**Issues**: Report via project issue tracker
**Documentation**: Update corresponding files in `/reference/` for any changes

---

## 🎉 Getting Help

* **📖 Full Documentation**: Start with [System Overview](reference/system.md)
* **🚀 Quick Setup**: Follow [Runbook](reference/runbook.md) instructions
* **🔧 Operations**: See [Operations Guide](reference/operations.md) for troubleshooting
* **🏗️ Architecture**: Review [Architecture](reference/architecture.md) for system understanding
* **💾 Data Management**: Check [Data Flow](reference/dataflow.md) for schema details