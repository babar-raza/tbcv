# TBCV System Architecture

## Overview

TBCV (Truth-Based Content Validation) is a multi-agent system designed for intelligent content validation, enhancement, and code analysis. The system combines fuzzy detection algorithms, plugin pattern matching, and AI-powered code generation to provide comprehensive technical content processing.

## Core Components

### Agent Layer

The heart of TBCV consists of specialized agents, each with distinct responsibilities:

#### TruthManagerAgent (`agents/truth_manager.py`)
**Responsibility**: Plugin truth data management and indexing
- Loads and indexes plugin definitions from JSON truth tables
- Provides B-tree indexing for O(log n) plugin lookups
- Handles SHA-256 versioning for change detection
- Compiles and caches pattern matching rules

#### FuzzyDetectorAgent (`agents/fuzzy_detector.py`)
**Responsibility**: Plugin detection using fuzzy matching algorithms
- Implements Levenshtein and Jaro-Winkler distance algorithms
- Analyzes context windows around potential matches
- Applies confidence scoring for detection accuracy
- Supports combination rules for multi-plugin detection

#### ContentValidatorAgent (`agents/content_validator.py`)
**Responsibility**: Content structure and quality validation
- Validates YAML, Markdown, and code syntax
- Performs link validation and image checking
- Applies rule-based content quality assessment
- Generates detailed validation reports with issues and severity levels

#### ContentEnhancerAgent (`agents/content_enhancer.py`)
**Responsibility**: Automatic content improvement
- Adds plugin links and informational text
- Prevents duplicate links and maintains formatting
- Applies enhancement templates with configurable patterns
- Supports rewrite ratio limits for safety

#### LLMValidatorAgent (`agents/llm_validator.py`)
**Responsibility**: AI-powered validation and enhancement
- Uses Ollama/Llama2 for intelligent code analysis
- Provides fallback to OpenAI/Gemini APIs
- Generates context-aware recommendations
- Supports temperature and token limit configuration

#### CodeAnalyzerAgent (`agents/code_analyzer.py`)
**Responsibility**: Code quality and security analysis
- Analyzes Python, C#, Java, JavaScript code
- Performs security scanning and complexity assessment
- Integrates with LLM for advanced analysis
- Provides performance optimization suggestions

#### OrchestratorAgent (`agents/orchestrator.py`)
**Responsibility**: Workflow coordination and execution
- Manages complex multi-step processing pipelines
- Handles concurrent workflow execution
- Provides checkpointing and recovery mechanisms
- Implements retry logic with exponential backoff

#### RecommendationAgent (`agents/recommendation_agent.py`)
**Responsibility**: Intelligent recommendation generation
- Analyzes validation results to generate improvements
- Applies confidence thresholds for recommendation quality
- Supports approval/rejection workflow
- Persists recommendations in database

#### EnhancementAgent (`agents/enhancement_agent.py`)
**Responsibility**: Recommendation application
- Applies approved recommendations to content
- Provides preview functionality
- Tracks enhancement statistics and success rates
- Maintains audit trail of changes

### Core Services

#### Configuration (`core/config.py`)
- Loads YAML and JSON configuration files
- Provides environment variable override support
- Validates configuration schema
- Supports hot-reloading for some settings

#### Database (`core/database.py`)
- SQLite-based persistent storage
- SQLAlchemy ORM with connection pooling
- Supports workflows, validations, recommendations tables
- Provides audit logging capabilities

#### Logging (`core/logging.py`)
- Structured JSON logging with configurable levels
- File rotation and backup management
- Performance monitoring integration
- Context-aware logging with workflow IDs

#### Caching (`core/cache.py`)
- Two-level caching: L1 (memory) + L2 (disk)
- LRU eviction policies
- TTL-based expiration
- Compression support for large objects

#### Validation Store (`core/validation_store.py`)
- Persistent storage for validation results
- Efficient querying and filtering
- Integration with recommendation system
- Performance metrics tracking

### API Layer

#### FastAPI Server (`api/server.py`)
- RESTful API endpoints for all operations
- WebSocket support for real-time updates
- CORS configuration for web UI
- Health check endpoints (/health/live, /health/ready)

#### Dashboard (`api/dashboard.py`)
- Web-based UI for system monitoring
- Validation results visualization
- Recommendation management interface
- Workflow status tracking

### CLI Interface (`cli/main.py`)

Command-line interface with Rich console output:
- File and directory validation commands
- Agent status checking
- Batch processing capabilities
- Recommendation approval/rejection workflow

## Data Flow

### Ingestion Phase
1. Content is ingested via CLI, API, or file system
2. Initial parsing and format detection
3. Database workflow creation

### Validation Phase
1. ContentValidatorAgent performs structural validation
2. FuzzyDetectorAgent identifies plugin usage patterns
3. LLMValidatorAgent provides AI-powered analysis
4. CodeAnalyzerAgent assesses code quality

### Enhancement Phase
1. RecommendationAgent generates improvement suggestions
2. User reviews and approves recommendations
3. EnhancementAgent applies approved changes
4. ContentEnhancerAgent adds automatic improvements

### Persistence Phase
1. All results stored in SQLite database
2. Caching layers updated
3. Audit logs generated
4. WebSocket notifications sent

## Technology Stack

- **Backend**: Python 3.8+, FastAPI, Uvicorn
- **Database**: SQLite with SQLAlchemy ORM
- **Caching**: Custom two-level cache system
- **APIs**: REST, WebSocket, Server-Sent Events
- **CLI**: Click framework with Rich output
- **Templates**: Jinja2 for HTML generation
- **Async**: asyncio throughout for concurrency

## Deployment Architecture

### Local Development
- Single-process Uvicorn server
- SQLite database in data/ directory
- File-based logging and caching

### Production Deployment
- Gunicorn/Uvicorn with multiple workers
- Docker containerization
- Volume mounts for data persistence
- Environment-based configuration

### Scaling Considerations
- Horizontal scaling through multiple instances
- Shared database for state consistency
- Load balancing for API endpoints
- Caching layers for performance