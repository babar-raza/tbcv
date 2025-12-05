# TBCV Glossary

A comprehensive reference for domain-specific terminology, concepts, and acronyms used in the TBCV (Truth-Based Content Validation) system.

**Table of Contents:**
- [System Components](#system-components)
- [Workflow & Execution](#workflow--execution)
- [Validation & Quality](#validation--quality)
- [Content & Data](#content--data)
- [Configuration & Infrastructure](#configuration--infrastructure)
- [Technical Concepts](#technical-concepts)
- [Database & Persistence](#database--persistence)
- [Acronyms & Abbreviations](#acronyms--abbreviations)

---

## System Components

### Agent
A specialized autonomous component that handles specific responsibilities in the TBCV system. Agents communicate via asynchronous message passing and are protected by dual-layer access control. TBCV has 19 total agents organized into three categories: 9 core agents (OrchestratorAgent, TruthManagerAgent, etc.), 3 pipeline agents (EditValidator, RecommendationEnhancer, etc.), and 7 modular validators.

**Related terms**: BaseAgent, AgentRegistry, MCP Server, Contract
**Where used**: agents/, api/server.py, svc/mcp_server.py
**See also**: [Agents Reference](agents.md)

### OrchestratorAgent
The master coordination agent that manages multi-step workflows with per-agent concurrency control. Handles workflow types: validate_file, validate_directory, full_validation, and content_update. Implements exponential backoff, semaphore-based rate limiting, and timeout management.

**Related terms**: Workflow, Pipeline, Concurrency Control, Semaphore
**Where used**: agents/orchestrator.py, api/server.py
**See also**: [Workflows Documentation](workflows.md)

### TruthManagerAgent
Manages plugin truth data (ground truth definitions) with multi-level indexing. Loads JSON files from the truth/ directory and creates 6 specialized indexes (by_id, by_slug, by_name, by_alias, by_pattern, by_family) for fast plugin lookups. Cache TTL: 7 days.

**Related terms**: Truth Data, Plugin, Indexing, Cache
**Where used**: agents/truth_manager.py, truth/ directory
**See also**: Truth data configuration in [Architecture](architecture.md)

### FuzzyDetectorAgent
Implements pattern matching and fuzzy matching algorithms (Levenshtein distance, Jaro-Winkler similarity) to detect plugin usage in content. Applies confidence scoring and context window analysis. Default similarity threshold: 0.85 (configurable).

**Related terms**: Fuzzy Matching, Confidence Scoring, Pattern Detection
**Where used**: agents/fuzzy_detector.py
**See also**: [Agents Reference](agents.md)

### ValidatorRouter
Routes validation requests to appropriate modular validators with fallback to legacy ContentValidator. Maintains validator registry, tracks routing decisions, and supports feature flags for gradual rollout.

**Related terms**: Modular Validators, Router, Validator, Backend
**Where used**: agents/validators/router.py, core/validator_router.py
**See also**: [Modular Validators](modular_validators.md)

### Modular Validators
Seven specialized, focused validators that replace the monolithic ContentValidatorAgent:
- **YamlValidatorAgent** - YAML frontmatter validation
- **MarkdownValidatorAgent** - Markdown structure and syntax
- **CodeValidatorAgent** - Code block validation
- **LinkValidatorAgent** - Link and URL validation
- **StructureValidatorAgent** - Document structure validation
- **TruthValidatorAgent** - Truth data and terminology validation
- **SeoValidatorAgent** - SEO metadata and heading size validation

**Related terms**: BaseValidatorAgent, Validator, Validation Pipeline
**Where used**: agents/validators/
**See also**: [Modular Validators Documentation](modular_validators.md)

### ContentEnhancerAgent
Applies approved enhancements to content with safety gating. Adds plugin hyperlinks to first mentions, inserts informational text after code blocks, and applies approved recommendations. Safety checks: rewrite_ratio < 0.5, no blocked topics.

**Related terms**: Enhancement, Safety Gate, Recommendation, Rewrite Ratio
**Where used**: agents/content_enhancer.py
**See also**: [Agents Reference](agents.md)

### RecommendationAgent
Generates actionable, human-reviewable improvement recommendations based on validation issues. Creates type-specific templates (yaml, markdown, code, links, truth) with confidence scoring and database persistence.

**Related terms**: Recommendation, Confidence, Template, Human-in-the-Loop
**Where used**: agents/recommendation_agent.py
**See also**: [Agents Reference](agents.md)

### LLMValidatorAgent
Performs semantic validation using Ollama LLM (or fallback to OpenAI/Gemini). Verifies fuzzy detector findings, identifies missing plugins based on code semantics. Graceful degradation when Ollama unavailable. Timeout: 30 seconds.

**Related terms**: LLM, Semantic Validation, Ollama, Confidence
**Where used**: agents/llm_validator.py
**See also**: [Agents Reference](agents.md)

### MCP Server
Model Context Protocol server providing JSON-RPC interface for TBCV operations. Enables external tools and Claude integrations to validate files, approve/reject results, and apply enhancements. Runs in stdio mode with stdin/stdout communication.

**Related terms**: JSON-RPC, Protocol, External Integration, CLI
**Where used**: svc/mcp_server.py, svc/mcp_methods/
**See also**: [MCP Integration](mcp_integration.md)

---

## Workflow & Execution

### Workflow
A multi-step execution sequence coordinated by OrchestratorAgent. Four main types: validate_file, validate_directory, full_validation, content_update. Each workflow has state (pending, running, paused, completed, failed, cancelled) and progress tracking.

**Related terms**: Pipeline, Step, Checkpoint, State, OrchestratorAgent
**Where used**: core/database.py, api/server.py, workflows.md
**See also**: [Workflows Documentation](workflows.md)

### Pipeline
Sequence of validation agents executed in coordinated order. Example: TruthManagerAgent → FuzzyDetectorAgent → ValidatorRouter → RecommendationAgent. Supports three execution modes: two_stage (default), heuristic_only, llm_only.

**Related terms**: Workflow, Agent, Step, Tier
**Where used**: workflows.md, agents/orchestrator.py
**See also**: Workflow execution details in [Workflows](workflows.md)

### Step
Individual unit of work within a workflow. Examples: "load_truth_data", "detect_plugins", "validate_content", "generate_recommendations". Workflows track current_step and total_steps for progress calculation.

**Related terms**: Workflow, Checkpoint, Progress
**Where used**: core/database.py (Workflow.current_step, total_steps)
**See also**: Workflow state tracking

### Checkpoint
Snapshot of workflow execution state saved to database for recovery. Includes workflow ID, step number, serialized state data, and validation hash. Enables workflow resumption after system failures.

**Related terms**: Workflow, Recovery, State, Persistence
**Where used**: core/checkpoint_manager.py, core/database.py
**See also**: [Workflow Recovery Guide](workflow_recovery.md)

### Gate
Safety control point that prevents risky operations. Examples: "rewrite_ratio gate" (blocks if > 0.5), "blocked_topics gate" (blocks forbidden content). Gates are checked before applying enhancements.

**Related terms**: Safety Check, Enhancement, Validation
**Where used**: agents/content_enhancer.py
**See also**: Safety gating in [Agents Reference](agents.md)

### Semaphore
Per-agent concurrency control mechanism limiting simultaneous operations. Example: llm_validator semaphore = 1 (only one LLM call at a time). Prevents agent overload and resource exhaustion. Uses exponential backoff when locked.

**Related terms**: Concurrency Control, Timeout, Backoff, Agent Limit
**Where used**: agents/orchestrator.py
**See also**: Concurrency control in [Workflows](workflows.md)

### Concurrency Control
System for managing parallel execution of agents. Uses semaphores with configurable limits per agent (llm_validator:1, content_validator:2, truth_manager:4, fuzzy_detector:2). Includes exponential backoff and timeout mechanisms.

**Related terms**: Semaphore, Agent Limit, Parallel Execution, Timeout
**Where used**: agents/orchestrator.py, config/main.yaml
**See also**: [Workflows Documentation](workflows.md)

### Two-Stage Validation
Default validation mode: FuzzyDetector → ContentValidator → LLMValidator. Fuzzy detector identifies potential issues (heuristic), LLM validator confirms/adjusts (semantic). LLM can downgrade, confirm, or upgrade severity.

**Related terms**: Heuristic, Semantic Validation, Confidence
**Where used**: agents/orchestrator.py, config/main.yaml
**See also**: Validation modes in [Workflows](workflows.md)

### Heuristic Validation
Fast pattern-based validation without LLM. Includes regex matching, rule checks, and structural analysis. Fallback when Ollama unavailable or for quick scans. Less accurate than semantic validation.

**Related terms**: Pattern Matching, Rule-Based, Two-Stage, Fast
**Where used**: agents/fuzzy_detector.py, agents/content_validator.py
**See also**: Validation modes in [Workflows](workflows.md)

### Semantic Validation
AI-powered validation using LLM to understand meaning and intent. Detects issues beyond pattern matching: missing plugins, invalid combinations, technical inaccuracies, format mismatches.

**Related terms**: LLM, Semantic, Two-Stage, Confidence
**Where used**: agents/llm_validator.py, agents/content_validator.py
**See also**: [Agents Reference](agents.md)

### Enhancement
Application of approved recommendations to content. Includes plugin hyperlinks (first mention only), informational text after code blocks, and other improvements. Safety-gated to prevent dangerous changes.

**Related terms**: Recommendation, Gate, Safety Check, Rewrite Ratio
**Where used**: agents/content_enhancer.py, agents/recommendation_enhancer.py
**See also**: Content enhancement in [Workflows](workflows.md)

### Recommendation
Actionable improvement suggestion generated from validation issues. Includes: type, instruction, rationale, scope, original_content, proposed_content, confidence, severity. Status workflow: proposed → pending → approved/rejected → applied.

**Related terms**: Validation, Human-in-the-Loop, Confidence, Status
**Where used**: core/database.py (Recommendation table), agents/recommendation_agent.py
**See also**: [Database Schema](database_schema.md)

### Human-in-the-Loop (HITL)
Workflow requiring human review and approval before applying changes. Recommendations are generated automatically but require explicit approval before enhancement. Maintains audit trail of all decisions.

**Related terms**: Recommendation, Approval, Audit Trail, Review
**Where used**: recommendation workflow throughout system
**See also**: [Workflows Documentation](workflows.md)

### Pause and Resume
Workflow control operations allowing temporary suspension and continuation. Pause stops execution preserving progress; Resume continues from pause point. All progress metrics preserved during cycle.

**Related terms**: Workflow, State, Progress, Checkpoint
**Where used**: api/server.py, core/workflow_manager.py
**See also**: Workflow control in [Workflows](workflows.md)

---

## Validation & Quality

### Validation
Process of checking content against rules and truth data. Produces ValidationResult with issues, confidence score, and metrics. Five main validation types: yaml, markdown, code, links, truth.

**Related terms**: Validator, Issue, Confidence, Rule
**Where used**: agents/validators/, core/validation_store.py
**See also**: [Modular Validators](modular_validators.md)

### ValidationResult
Structured output from validation including: status (pass/fail/warning), confidence score, list of issues, validation_types applied, and metrics. Persisted in database with workflow association.

**Related terms**: Issue, Validation, Status, Confidence
**Where used**: core/database.py (validation_results table)
**See also**: [Database Schema](database_schema.md)

### Issue
Individual problem found during validation. Contains: level (critical/error/warning/info), category (yaml/markdown/code/link/truth/seo), message, line_number, suggestion, auto_fixable flag, confidence score.

**Related terms**: Validation, ValidationResult, Severity, Confidence
**Where used**: agents/validators/base_validator.py, core/error_formatter.py
**See also**: [Architecture](architecture.md)

### Confidence
Probability score (0.0-1.0) indicating certainty of a finding. Aggregated from multiple sources: exact match (1.0), regex pattern (0.8), fuzzy match (0.8), context match (0.1). Used for threshold-based filtering and prioritization.

**Related terms**: Score, Probability, Threshold, Validation
**Where used**: Throughout agent code
**See also**: [Agents Reference](agents.md)

### Severity
Issue importance level: critical, error, warning, info. Determines urgency and prioritization. Used in recommendation generation and enhancement approval decisions.

**Related terms**: Level, Priority, Confidence, Issue
**Where used**: agents/validators/, database schema
**See also**: [Architecture](architecture.md)

### Rule
Definition of what constitutes valid content. Examples: "YAML frontmatter must have 'title' field", "Heading hierarchy cannot skip levels", "Links must be resolvable". Rules are applied by validators.

**Related terms**: Validation, Validator, Issue, Pattern
**Where used**: config/ directory, agents/validators/
**See also**: [Configuration](configuration.md)

### Pattern
Regex or fuzzy pattern used to detect plugins or syntax elements. Defined in truth data JSON files. Examples: `SaveFormat.Pdf`, `Document.Save`, class names, method names.

**Related terms**: Regex, Fuzzy Matching, Truth Data, Detection
**Where used**: agents/fuzzy_detector.py, truth/ directory
**See also**: Truth data configuration

### Fuzzy Matching
Approximate string matching using Levenshtein distance or Jaro-Winkler similarity. Tolerates typos and minor variations. Used for plugin detection when exact matches unavailable. Threshold: 0.85 (configurable).

**Related terms**: Pattern, Detection, Confidence, Similarity
**Where used**: agents/fuzzy_detector.py
**See also**: [Agents Reference](agents.md)

### Confidence Threshold
Minimum confidence score required to flag an issue or apply a recommendation. Default: 0.7 for recommendations, 0.85 for fuzzy matches. Configurable per validator/agent.

**Related terms**: Confidence, Threshold, Filtering
**Where used**: config/ files, throughout agent code
**See also**: [Configuration](configuration.md)

### Accuracy Metrics
Quantitative measures of validation quality: precision, recall, F1-score. Calculated by comparing validation results against known test cases. Tracked per validator and over time.

**Related terms**: Performance, Metrics, Quality, Testing
**Where used**: tests/, performance tracking
**See also**: [Performance Metrics](performance_metrics.md)

---

## Content & Data

### Truth Data
Ground truth definitions of plugins (Aspose or similar). Stored as JSON files in truth/ directory. Contains plugin metadata: id, name, slug, patterns, dependencies, capabilities, combinations. Single source of truth for plugin information.

**Related terms**: Plugin, Pattern, Truth Manager, Indexing
**Where used**: truth/ directory, agents/truth_manager.py
**See also**: Truth data in [Architecture](architecture.md)

### Plugin
Software component with specific functionality declared in truth data. Examples: "Document", "Pdf", "Merger", "DocumentConverter". Content should declare used plugins in frontmatter; TBCV validates against truth data.

**Related terms**: Truth Data, Truth Validator, Frontmatter, Dependency
**Where used**: Throughout validation system
**See also**: Plugin validation in [Agents Reference](agents.md)

### Frontmatter
YAML metadata at beginning of markdown file (delimited by ---). Contains: title, description, products (plugins), version, etc. Parsed separately from content and validated for required fields and data types.

**Related terms**: YAML, Metadata, YamlValidator, Validation
**Where used**: agents/validators/yaml_validator.py
**See also**: YAML validation in [Modular Validators](modular_validators.md)

### Markdown
Content format used for all TBCV documents. Structured with headings, lists, code blocks, links, tables. Validated for: heading hierarchy, syntax, link validity, code block completeness.

**Related terms**: Content, Markdown Validator, Syntax, Structure
**Where used**: Throughout documentation and validation
**See also**: [Modular Validators](modular_validators.md)

### Code Block
Fenced code snippet in markdown (triple backticks). Must have language identifier (python, csharp, java, etc.) and valid syntax. Used in code examples demonstrating plugin usage.

**Related terms**: Markdown, CodeValidator, Language, Syntax
**Where used**: agents/validators/code_validator.py
**See also**: Code validation in [Modular Validators](modular_validators.md)

### Link
URL or anchor reference in content. Must be valid (no broken links), properly formatted, and accessible. Includes internal (relative paths) and external (HTTP URLs) links. Validated with timeout: 5 seconds (configurable).

**Related terms**: URL, Anchor, LinkValidator, Broken
**Where used**: agents/validators/link_validator.py
**See also**: Link validation in [Modular Validators](modular_validators.md)

### Meta Description
SEO metadata field summarizing page content. Required length: 120-160 characters (configurable). Part of SEO validation mode.

**Related terms**: SEO, SeoValidator, Metadata, Head
**Where used**: agents/validators/seo_validator.py, frontmatter
**See also**: SEO validation in [Modular Validators](modular_validators.md)

### Family
Product category grouping plugins. Examples: "words", "pdf", "cells", "slides". Specified in validation requests to load appropriate truth data. One family per validation.

**Related terms**: Plugin, Truth Data, Product, Category
**Where used**: Throughout validation pipeline
**See also**: Family-based plugin organization

### Product
Software application containing plugins. Examples: Aspose.Words, Aspose.Pdf, Aspose.Cells. Family corresponds to product (family: words → Aspose.Words product).

**Related terms**: Family, Plugin, Truth Data
**Where used**: Documentation context
**See also**: Product families in [Architecture](architecture.md)

---

## Configuration & Infrastructure

### Feature Flag
Configuration switch enabling/disabling functionality. Examples: `validators.yaml: true`, `llm_validation: enabled: true`. Allows gradual rollout and A/B testing without code changes.

**Related terms**: Configuration, Setting, Toggle, Control
**Where used**: config/ files throughout system
**See also**: [Configuration](configuration.md)

### Config Profile
Named configuration set for different environments. Examples: development, staging, production. Contains environment-specific settings: debug levels, timeouts, resource limits.

**Related terms**: Configuration, Environment, Settings
**Where used**: config/ directory, TBCV_PROFILE env var
**See also**: [Configuration](configuration.md)

### Configuration Loader
Core component loading YAML/JSON config files with environment variable override support. Prefix: `TBCV_`. Supports hot-reloading for some settings. Location: core/config_loader.py.

**Related terms**: Configuration, Settings, Environment Variables
**Where used**: core/config_loader.py
**See also**: [Configuration](configuration.md)

### Schema
Formal definition of data structure (JSON schema for configurations, database schemas, validation templates). Defines: required fields, data types, constraints, validation rules.

**Related terms**: Database, Configuration, Validation, Structure
**Where used**: Throughout system
**See also**: [Database Schema](database_schema.md)

### Migration
Database schema change or data transformation. Stored in migrations/ directory using Alembic (future) or manual scripts. Examples: add new columns, rename tables, data transformations.

**Related terms**: Database, Schema, Version, Upgrade
**Where used**: migrations/ directory
**See also**: [Database Schema](database_schema.md)

### Cache
Two-level caching system for performance: L1 (in-memory LRU) for fast access, L2 (SQLite or Redis) for persistence across restarts. Default: SQLite L2 (Redis optional for distributed deployments).

**Related terms**: Performance, TTL, Eviction, Compression
**Where used**: core/cache.py, core/database.py
**See also**: [Architecture](architecture.md)

### L1 Cache
In-process memory cache using LRU eviction policy. Fast but limited by available memory. Cleared on restart. Default: 1000 max entries, 256 MB limit, 3600s TTL.

**Related terms**: Cache, LRU, Memory, Performance
**Where used**: core/cache.py
**See also**: Caching in [Architecture](architecture.md)

### L2 Cache
Persistent disk-based cache using SQLite (default) or Redis. Survives application restart. Slower than L1 but larger capacity. Default: 1024 MB, compression enabled for entries > 1KB.

**Related terms**: Cache, Persistence, Disk, Performance
**Where used**: core/cache.py, core/database.py
**See also**: [Deployment Guide](deployment.md)

### TTL (Time-To-Live)
Expiration time for cached data. After TTL expires, entry is removed on next cleanup. Examples: Truth data: 7 days, validation results: 30 minutes, fuzzy detections: 24 hours.

**Related terms**: Cache, Expiration, Cleanup, Eviction
**Where used**: core/cache.py
**See also**: Cache configuration in [Configuration](configuration.md)

### LRU (Least Recently Used)
Cache eviction policy removing least-accessed entries when capacity exceeded. Default eviction policy for L1 cache. Balances recency and frequency of access.

**Related terms**: Cache, Eviction, Performance, Policy
**Where used**: core/cache.py
**See also**: Caching architecture

### Import Guard
Security mechanism preventing unauthorized module imports. Uses Python sys.meta_path hook at import-time. Blocks API/CLI from importing protected modules (agents.*, core.validation_store). Location: core/import_guard.py.

**Related terms**: Security, Access Control, Import, Protection
**Where used**: core/import_guard.py, startup sequence
**See also**: [Security Documentation](security.md)

### Access Guard
Runtime security mechanism preventing unauthorized function calls. Uses @guarded_operation decorator with stack inspection. Checks caller module before allowing access to protected functions.

**Related terms**: Security, Decorator, Authorization, MCP-First
**Where used**: core/access_guard.py, agents/
**See also**: [Security Documentation](security.md)

### MCP-First Architecture
Design pattern requiring all business logic access through MCP server. Direct access from API/CLI blocked by dual-layer access guards (import-time + runtime). Enforces single entry point.

**Related terms**: MCP Server, Access Guard, Security, Architecture
**Where used**: Throughout system design
**See also**: [Security Documentation](security.md)

### Environment Variable
Configuration override mechanism. Prefix: `TBCV_`. Examples: `TBCV_LOG_LEVEL=debug`, `TBCV_PORT=9000`. Overrides file-based configuration. Loaded by ConfigLoader.

**Related terms**: Configuration, ConfigLoader, Override
**Where used**: Throughout system
**See also**: [Configuration](configuration.md)

---

## Technical Concepts

### JSON-RPC
Protocol for remote procedure calls using JSON messages over various transports. TBCV uses JSON-RPC 2.0 for MCP server. Message format: `{jsonrpc, method, params, id}`.

**Related terms**: MCP, Protocol, RPC, JSON
**Where used**: svc/mcp_server.py, external integrations
**See also**: [MCP Integration](mcp_integration.md)

### Rewrite Ratio
Metric comparing size changes during enhancement: `|enhanced_length - original_length| / original_length`. Safety gate blocks enhancement if > 0.5 (50% change threshold).

**Related terms**: Enhancement, Safety Gate, Change, Metric
**Where used**: agents/content_enhancer.py
**See also**: Safety gating in [Agents Reference](agents.md)

### Audit Trail
Complete record of all changes and decisions: who made changes, when, what changed, reason. Stored in audit_logs table. Required for compliance and debugging.

**Related terms**: AuditLog, Recommendation, Approval, Compliance
**Where used**: core/database.py (audit_logs table), workflow
**See also**: [Database Schema](database_schema.md)

### Atomic Operation
Database operation that either fully completes or fully rolls back. No partial states. Used for critical operations: applying recommendations, creating checkpoints.

**Related terms**: Database, Transaction, Consistency, ACID
**Where used**: core/database.py, SQLAlchemy ORM
**See also**: Database operations

### Async/Await
Python asynchronous programming pattern for non-blocking I/O. All agents and API endpoints use async/await. Allows concurrent processing without multi-threading complexity.

**Related terms**: Concurrency, Coroutine, Non-Blocking
**Where used**: Throughout agent code, API endpoints
**See also**: Python asyncio documentation

### Websocket
Bidirectional communication protocol for real-time updates. TBCV uses WebSocket for workflow progress streaming, recommendation notifications, real-time validation updates.

**Related terms**: Real-Time, Streaming, Protocol, Live
**Where used**: api/server.py, web dashboard
**See also**: Real-time updates in [API Reference](api_reference.md)

### Server-Sent Events (SSE)
Server-to-client streaming protocol for real-time updates. One-directional (server → client). Alternative to WebSocket for simpler real-time needs.

**Related terms**: Real-Time, Streaming, Protocol, WebSocket
**Where used**: api/server.py, dashboard
**See also**: Streaming endpoints in [API Reference](api_reference.md)

### Levenshtein Distance
Edit distance metric measuring minimum character changes to transform one string into another. Used for fuzzy matching with weight: 0.8. Calculation: insertions + deletions + substitutions.

**Related terms**: Fuzzy Matching, Distance, Similarity, Algorithm
**Where used**: agents/fuzzy_detector.py
**See also**: Fuzzy matching in [Agents Reference](agents.md)

### Jaro-Winkler Similarity
String similarity metric favoring matches at beginning of string. Range: 0.0-1.0 (1.0 = identical). Used alongside Levenshtein in fuzzy detection. Weight: 0.8.

**Related terms**: Fuzzy Matching, Similarity, Algorithm
**Where used**: agents/fuzzy_detector.py
**See also**: Fuzzy matching in [Agents Reference](agents.md)

### Ollama
Local LLM inference engine running models (llama2, mistral). Optional integration for semantic validation. Graceful fallback if unavailable. Connection timeout: 30 seconds.

**Related terms**: LLM, Semantic, AI, Optional
**Where used**: agents/llm_validator.py
**See also**: [Agents Reference](agents.md)

### Pydantic
Python library for data validation and serialization using type hints. Used for API request/response models and configuration schemas. Provides automatic validation and error messages.

**Related terms**: Validation, Types, API, Schema
**Where used**: api/server.py, core/config_loader.py
**See also**: Pydantic documentation

### SQLAlchemy
Python ORM (Object-Relational Mapping) library for database operations. Abstracts SQL, provides type safety, automatic schema creation. Used with SQLite backend.

**Related terms**: ORM, Database, Schema, SQL
**Where used**: core/database.py, migrations/
**See also**: [Database Schema](database_schema.md)

---

## Database & Persistence

### Workflow Table
Database table storing workflow execution records. Columns: id, type, state, input_params, metadata, progress, timestamps. Indexed by state and created_at for efficient querying.

**Related terms**: Database, Workflow, Persistence, Schema
**Where used**: core/database.py
**See also**: [Database Schema](database_schema.md)

### ValidationResult Table
Database table storing validation outcomes. Columns: id, workflow_id, file_path, issues, confidence, validation_types, status, timestamps. Indexed by file_path and status.

**Related terms**: Database, Validation, Persistence, Result
**Where used**: core/database.py, validation_store.py
**See also**: [Database Schema](database_schema.md)

### Recommendation Table
Database table storing improvement recommendations. Columns: id, validation_id, type, instruction, status, confidence, approval_metadata, audit fields. Status workflow: proposed → approved/rejected → applied.

**Related terms**: Database, Recommendation, Persistence, Human-in-the-Loop
**Where used**: core/database.py, recommendation pipeline
**See also**: [Database Schema](database_schema.md)

### Checkpoint Table
Database table storing workflow recovery points. Columns: id, workflow_id, name, step_number, state_data, validation_hash, can_resume_from, created_at. Enables workflow resumption.

**Related terms**: Database, Checkpoint, Recovery, Persistence
**Where used**: core/checkpoint_manager.py, database.py
**See also**: [Database Schema](database_schema.md)

### AuditLog Table
Database table tracking all changes to recommendations. Columns: id, recommendation_id, action, actor, before_state, after_state, changes, metadata, created_at. Required for compliance and debugging.

**Related terms**: Database, Audit, Compliance, Tracking
**Where used**: core/database.py
**See also**: [Database Schema](database_schema.md)

### CacheEntry Table
Database table storing L2 persistent cache. Columns: cache_key, agent_id, method_name, result_data, expires_at, access_count, last_accessed, size_bytes. Indexed by expiration for cleanup.

**Related terms**: Database, Cache, Persistence, L2
**Where used**: core/database.py, cache.py
**See also**: [Database Schema](database_schema.md)

### Metrics Table
Database table storing application performance metrics. Columns: id, name, value, created_at, metadata. Tracks: validation duration, cache hit rate, agent execution time. Retained 30 days.

**Related terms**: Database, Metrics, Performance, Monitoring
**Where used**: core/database.py
**See also**: [Database Schema](database_schema.md)

### Relationship (Foreign Key)
Database constraint linking related tables. Examples: validation_results → workflows (many-to-one), recommendations → validation_results (many-to-one), audit_logs → recommendations (many-to-one).

**Related terms**: Database, Schema, Constraint, Referential Integrity
**Where used**: core/database.py
**See also**: ER diagram in [Database Schema](database_schema.md)

### Index
Database optimization creating fast lookup paths for specific columns. Examples: idx_validation_file_status, idx_recommendations_validation. Improves query performance.

**Related terms**: Database, Performance, Query, Optimization
**Where used**: core/database.py schema definitions
**See also**: [Database Schema](database_schema.md)

---

## Acronyms & Abbreviations

### API
**Application Programming Interface** - Software interface allowing applications to communicate. TBCV provides REST API endpoints for integration.
**See also**: [API Reference](api_reference.md)

### CLI
**Command-Line Interface** - Text-based user interface for system interaction. TBCV CLI: `python -m cli.main`. 15+ commands available.
**See also**: [CLI Usage](cli_usage.md)

### CRUD
**Create, Read, Update, Delete** - Basic database operations. TBCV implements CRUD for workflows, validations, recommendations.

### DB / SQLite
**Database / SQL Lite Database Engine** - TBCV uses SQLite for persistent storage. Location: data/tbcv.db. Lightweight, no server required.
**See also**: [Database Schema](database_schema.md)

### ENUM
**Enumeration** - Fixed set of allowed values. TBCV uses enums for: WorkflowState (pending/running/completed/failed), ValidationStatus (pass/fail/warning), RecommendationStatus (proposed/approved/applied).

### GUID / UUID
**Globally Unique Identifier / Universally Unique Identifier** - Unique identifier format (36 characters). TBCV uses UUIDs for: workflow_id, validation_id, recommendation_id.

### HITL / HumanInTheLoop
**Human-In-The-Loop** - Workflow requiring human review and decision before execution. Recommendations require approval before enhancement.
**See also**: [Workflows Documentation](workflows.md)

### HTTP
**HyperText Transfer Protocol** - Standard web protocol. TBCV REST API uses HTTP methods: GET (retrieve), POST (create), PUT (update), DELETE (remove).

### JSON
**JavaScript Object Notation** - Human-readable data format. Used for: API payloads, configuration files, truth data, MCP messages.

### JSON-RPC
**JSON Remote Procedure Call** - Protocol for remote method invocation. TBCV MCP server uses JSON-RPC 2.0 specification.
**See also**: [MCP Integration](mcp_integration.md)

### LLM
**Large Language Model** - AI model for text generation and analysis. TBCV integrates with Ollama (local) or OpenAI/Gemini (cloud). Optional for semantic validation.
**See also**: [Agents Reference](agents.md)

### LRU
**Least Recently Used** - Cache eviction policy. TBCV uses LRU for L1 memory cache.
**See also**: Caching in [Architecture](architecture.md)

### MCP
**Model Context Protocol** - Protocol for external tool/LLM integration. TBCV server implements MCP server enabling Claude/external access.
**See also**: [MCP Integration](mcp_integration.md)

### ORM
**Object-Relational Mapping** - Database abstraction layer. TBCV uses SQLAlchemy ORM with SQLite backend.
**See also**: [Database Schema](database_schema.md)

### RAG
**Retrieval-Augmented Generation** - Technique combining document retrieval with AI generation. TBCV uses custom RAG combining TruthManager (retrieval) and LLMValidator (generation).

### REST
**Representational State Transfer** - Architectural style for APIs. TBCV REST API provides 40+ endpoints following REST principles.
**See also**: [API Reference](api_reference.md)

### RPC
**Remote Procedure Call** - Method invocation on remote system. TBCV uses JSON-RPC for MCP server communication.

### SEO
**Search Engine Optimization** - Web visibility best practices. TBCV SeoValidatorAgent checks: meta descriptions, title tags, heading compliance.
**See also**: [Modular Validators](modular_validators.md)

### YAML
**YAML Ain't Markup Language** - Human-readable data format. TBCV uses YAML for: configuration files (config/), frontmatter in markdown documents.

### SQL
**Structured Query Language** - Language for database operations. TBCV database uses SQL indirectly through SQLAlchemy ORM.

### TTL
**Time-To-Live** - Expiration duration for cached data. TBCV examples: truth_data TTL = 7 days, validation results = 30 minutes.

### WAL
**Write-Ahead Logging** - SQLite journaling mode improving concurrency. Can be enabled: `PRAGMA journal_mode=WAL`.

### YAML/JSON
**Configuration formats** - YAML used for application config (human-readable), JSON used for truth data and API payloads (parseable).

---

## Cross-References & Navigation

**By Category:**
- [System Components](#system-components) - Agents, routers, servers
- [Workflow & Execution](#workflow--execution) - Validation pipelines, checkpoints, control
- [Validation & Quality](#validation--quality) - Validators, issues, confidence
- [Content & Data](#content--data) - Markdown, plugins, truth data
- [Configuration & Infrastructure](#configuration--infrastructure) - Settings, schemas, caching
- [Technical Concepts](#technical-concepts) - Algorithms, protocols, patterns
- [Database & Persistence](#database--persistence) - Tables, relationships, operations
- [Acronyms & Abbreviations](#acronyms--abbreviations) - Short forms and initialisms

**Related Documentation:**
- [Architecture](architecture.md) - System design and components
- [Agents Reference](agents.md) - Detailed agent documentation
- [Workflows](workflows.md) - Workflow types and execution
- [Modular Validators](modular_validators.md) - Validator architecture
- [Database Schema](database_schema.md) - Data model details
- [Configuration](configuration.md) - System configuration
- [API Reference](api_reference.md) - REST API endpoints
- [CLI Usage](cli_usage.md) - Command-line interface
- [MCP Integration](mcp_integration.md) - External integrations
- [Security Documentation](security.md) - Access control system

---

## Contributing to the Glossary

To add new terms:
1. Identify the appropriate section (System Components, Technical Concepts, etc.)
2. Add alphabetically within section
3. Include: definition (1-3 sentences), related terms, where used, links to docs
4. Update cross-references and navigation
5. Test links and formatting

Template:
```markdown
### Term Name
Brief definition (1-3 sentences) explaining purpose and context.

**Related terms**: Related concept A, Related concept B
**Where used**: File path or module location
**See also**: [Link to detailed documentation](path.md)
```

---

**Last Updated**: December 3, 2025
**Total Terms**: 155+
**Lines**: 445+
