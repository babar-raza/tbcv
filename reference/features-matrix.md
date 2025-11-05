# TBCV Features ↔ Modules Matrix

| **Title** | Feature Module Mapping |
|---|---|
| **Version** | auto |
| **Source** | Code analysis @ 2025-11-03T07:43:18Z |

## Features to Modules Matrix

This matrix shows how TBCV's capabilities are implemented across the system's modules and components.

### Core Features Mapping

| Feature | Primary Module | Supporting Modules | Evidence |
|---|---|---|---|
| **Plugin Detection** | `agents/fuzzy_detector.py` | `agents/truth_manager.py`, `core/cache.py` | `FuzzyDetectorAgent.detect_plugins():67-81` |
| **Content Validation** | `agents/content_validator.py` | `core/validation_store.py`, `core/rule_manager.py` | `ContentValidatorAgent.validate_content():115-496` |
| **Code Analysis** | `agents/code_analyzer.py` | `core/ollama.py`, `core/cache.py` | `CodeAnalyzerAgent.analyze_code():247-1020` |
| **Content Enhancement** | `agents/content_enhancer.py` | `agents/content_validator.py` | `ContentEnhancerAgent.enhance_content():106-439` |
| **Workflow Orchestration** | `agents/orchestrator.py` | `core/database.py`, `agents/base.py` | `OrchestratorAgent._validate_configuration():64-356` |
| **Truth Data Management** | `agents/truth_manager.py` | `truth/words.json`, `rules/words.json` | `TruthManagerAgent.adapt_plugin_data():121-686` |
| **REST API** | `api/server.py` | `api/dashboard.py`, `api/export_endpoints.py` | FastAPI app definition:23-1012 |
| **WebSocket Support** | `api/websocket_endpoints.py` | `api/server.py` | WebSocket endpoint handlers |
| **Database Persistence** | `core/database.py` | `core/validation_store.py` | `DatabaseManager` class |
| **Configuration Management** | `core/config.py` | `config/main.yaml` | Configuration loading and validation |
| **Logging & Monitoring** | `core/logging.py` | `data/logs/tbcv.log` | Structured logging setup |
| **Caching System** | `core/cache.py` | `data/cache/` | Two-level caching implementation |
| **CLI Interface** | `cli/main.py` | `__main__.py` | Command-line entry points |
| **External Code Integration** | `agents/code_analyzer.py` | `core/utilities.py` | GitHub/Gist fetching methods |
| **Batch Processing** | `agents/orchestrator.py` | `api/server.py` | Batch workflow coordination |

### Detailed Feature Implementation

#### 1) Content Processing Features

| Capability | Implementation | Module | Key Classes/Functions |
|---|---|---|---|
| **YAML Validation** | Frontmatter parsing and validation | `agents/content_validator.py` | `ValidationIssue`, `validate_yaml()` |
| **Markdown Analysis** | Structure and heading hierarchy | `agents/content_validator.py` | `validate_markdown()` |
| **Code Quality Checks** | Multi-language syntax and style | `agents/content_validator.py` | `validate_code()` |
| **Link Validation** | URL accessibility verification | `agents/content_validator.py` | `validate_links()` |
| **Plugin Linking** | First-occurrence intelligent linking | `agents/content_enhancer.py` | `add_plugin_links()` |
| **Format Fixes** | Heading, code block, list normalization | `agents/content_enhancer.py` | `apply_format_fixes()` |

#### 2) Intelligence & Detection Features

| Algorithm | Implementation | Module | Evidence |
|---|---|---|---|
| **Fuzzy Matching** | Levenshtein, Jaro-Winkler, Ratio | `agents/fuzzy_detector.py` | Multiple algorithm support:76-196 |
| **Pattern Recognition** | Regex-based plugin detection | `agents/fuzzy_detector.py` | `detect_by_patterns()` |
| **Confidence Scoring** | Weighted combination algorithms | `agents/fuzzy_detector.py` | `calculate_confidence()` |
| **Truth Table Indexing** | B-tree plugin organization | `agents/truth_manager.py` | O(log n) lookup performance |
| **Document Flow Analysis** | Aspose processing pattern detection | `agents/code_analyzer.py` | `_analyze_document_processing_flow()` |
| **Security Scanning** | Vulnerability detection in code | `agents/code_analyzer.py` | `check_security()` |

#### 3) Data Management Features

| Data Type | Storage | Module | Schema/Format |
|---|---|---|---|
| **Validation Results** | SQLite database | `core/database.py` | Structured JSON with metrics |
| **Plugin Truth Data** | JSON files | `truth/words.json`, `rules/words.json` | Hierarchical plugin definitions |
| **Workflow State** | Database + in-memory | `core/database.py` | State machine tracking |
| **Cache Data** | L1 memory + L2 persistent | `core/cache.py` | LRU eviction + SHA-256 versioning |
| **Configuration** | YAML + environment | `core/config.py` | Hierarchical settings |
| **Audit Logs** | Structured file logging | `core/logging.py` | JSON-formatted log entries |

#### 4) Interface & Integration Features

| Interface Type | Implementation | Module | Capabilities |
|---|---|---|---|
| **REST Endpoints** | FastAPI with Pydantic models | `api/server.py` | Content validation, batch processing |
| **WebSocket Streams** | Real-time progress updates | `api/websocket_endpoints.py` | Live workflow monitoring |
| **Dashboard UI** | HTML templates with Jinja2 | `api/dashboard.py` | Workflow visualization and control |
| **Export Services** | CSV/JSON data export | `api/export_endpoints.py` | Results and metrics export |
| **Command Line** | Argparse-based CLI | `cli/main.py` | Direct file/directory processing |
| **GitHub Integration** | API-based code fetching | `agents/code_analyzer.py` | Gist and repository content |

### Cross-Cutting Concerns

#### Performance & Scalability

| Concern | Solution | Modules | Implementation |
|---|---|---|---|
| **Async Processing** | AsyncIO throughout | All agents | Non-blocking I/O operations |
| **Background Tasks** | FastAPI background jobs | `api/server.py` | Long-running workflow execution |
| **Worker Pooling** | Configurable concurrency | `agents/orchestrator.py` | Parallel batch processing |
| **Connection Pooling** | SQLAlchemy pools | `core/database.py` | Database efficiency |
| **Memory Management** | LRU caching | `core/cache.py` | Bounded memory usage |
| **Resource Limits** | Configurable timeouts | `core/config.py` | Prevent resource exhaustion |

#### Error Handling & Reliability

| Pattern | Implementation | Modules | Capabilities |
|---|---|---|---|
| **Retry Logic** | Exponential backoff | `agents/orchestrator.py` | Transient failure recovery |
| **Circuit Breakers** | Failure threshold monitoring | `agents/base.py` | Cascade failure prevention |
| **Graceful Degradation** | Partial result handling | All agents | Best-effort processing |
| **State Persistence** | Checkpoint creation | `core/database.py` | Workflow resumption |
| **Input Validation** | Pydantic model validation | `api/server.py` | Type safety and constraints |
| **Exception Logging** | Structured error reporting | `core/logging.py` | Debugging and monitoring |

### Feature Dependencies Graph

```mermaid
graph TD
    subgraph "Core Features"
        A[Plugin Detection]
        B[Content Validation]
        C[Code Analysis]
        D[Content Enhancement]
    end

    subgraph "Supporting Systems"
        E[Truth Data Management]
        F[Database Persistence]
        G[Caching System]
        H[Configuration]
    end

    subgraph "Interfaces"
        I[REST API]
        J[WebSocket API]
        K[CLI Interface]
        L[Dashboard UI]
    end

    A --> E
    A --> G
    B --> F
    B --> H
    C --> G
    C --> F
    D --> B
    D --> A

    I --> B
    I --> C
    I --> D
    J --> I
    K --> B
    L --> I

    style A fill:#e3f2fd
    style B fill:#e3f2fd
    style C fill:#e3f2fd
    style D fill:#e3f2fd
````

### Module Interaction Frequency

| Source Module                | Target Module                 | Interaction Type     | Frequency | Evidence                  |
| ---------------------------- | ----------------------------- | -------------------- | --------- | ------------------------- |
| `api/server.py`              | `agents/orchestrator.py`      | Workflow initiation  | High      | Every API request         |
| `agents/orchestrator.py`     | `agents/content_validator.py` | Task delegation      | High      | Every validation workflow |
| `agents/fuzzy_detector.py`   | `agents/truth_manager.py`     | Plugin lookup        | High      | Every detection request   |
| `agents/content_enhancer.py` | `agents/content_validator.py` | Result consumption   | Medium    | Enhancement workflows     |
| `agents/code_analyzer.py`    | `core/cache.py`               | Result caching       | Medium    | Code analysis operations  |
| `core/database.py`           | All agents                    | State persistence    | High      | Workflow tracking         |
| `core/logging.py`            | All modules                   | Event logging        | Very High | Every operation           |
| `core/config.py`             | All modules                   | Configuration access | Medium    | Startup and runtime       |

### Testing Coverage by Feature

| Feature                   | Test Module                                                       | Coverage Type      | Evidence                    |
| ------------------------- | ----------------------------------------------------------------- | ------------------ | --------------------------- |
| **Plugin Detection**      | `tests/test_truths_and_rules.py`                                  | Unit + Integration | Pattern matching validation |
| **Content Validation**    | `tests/test_generic_validator.py`                                 | Unit               | Validation logic testing    |
| **Code Analysis**         | `tests/test_smoke_agents.py`                                      | Smoke              | Agent initialization        |
| **Enhancement Workflows** | `tests/test_enhancer_consumes_validation.py`                      | Integration        | End-to-end enhancement      |
| **API Endpoints**         | `tests/test_endpoints_live.py`, `tests/test_endpoints_offline.py` | Integration        | REST API testing            |
| **Batch Processing**      | `tests/test_performance.py`                                       | Performance        | Scalability validation      |
| **Database Operations**   | `tests/test_validation_persistence.py`                            | Unit               | Data consistency            |
| **System Integration**    | `tests/test_framework.py`                                         | System             | Full workflow testing       |
| **Idempotency**           | `tests/test_idempotence_and_schemas.py`                           | Unit               | Operation repeatability     |

---

This matrix provides a comprehensive view of how TBCV's features are distributed across its modular architecture, enabling efficient maintenance, testing, and future enhancements.