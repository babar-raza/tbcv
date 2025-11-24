# Configuration

## Overview

TBCV uses YAML and JSON configuration files to control system behavior. Configuration is hierarchical with environment variable overrides and hot-reloading support.

## Configuration Files

### config/main.yaml
Primary system configuration file.

```yaml
# System settings
system:
  name: "TBCV"
  version: "2.0.0"
  environment: "development"
  debug: true
  log_level: "info"
  timezone: "UTC"
  data_directory: "./data"
  temp_directory: "./data/temp"

# Server configuration
server:
  host: "localhost"
  port: 8080
  enable_cors: true
  cors_origins:
    - "http://localhost:3000"
    - "http://localhost:8080"
  request_timeout_seconds: 30
  max_request_size_mb: 50
  websocket_ping_interval: 30
  websocket_ping_timeout: 10

# Agent configurations
agents:
  fuzzy_detector:
    enabled: true
    similarity_threshold: 0.85
    context_window_chars: 200
    max_patterns: 500
    fuzzy_algorithms:
      - "levenshtein"
      - "jaro_winkler"
    pattern_cache_size: 1000

  content_validator:
    enabled: true
    html_sanitization: true
    link_validation: true
    link_timeout_seconds: 5
    image_validation: false
    yaml_strict_mode: false
    markdown_extensions:
      - "tables"
      - "fenced_code"
      - "codehilite"

  content_enhancer:
    enabled: true
    auto_link_plugins: true
    add_info_text: true
    prevent_duplicate_links: true
    link_template: "https://products.aspose.com/words/net/plugins/{slug}/"
    info_text_template: "*This code requires the **{plugin_name}** plugin.*"
    rewrite_ratio_threshold: 0.5
    blocked_topics:
      - "forbidden"

  orchestrator:
    enabled: true
    max_concurrent_workflows: 50
    workflow_timeout_seconds: 3600
    checkpoint_interval_seconds: 30
    retry_attempts: 3
    retry_backoff_base: 1.0

  truth_manager:
    enabled: true
    auto_reload: true
    validation_strict: false
    cache_ttl_seconds: 604800
    truth_directories:
      - "./truth"
      - "./truth/words"
      - "./truth/pdf"
      - "./truth/cells"

# Caching configuration
cache:
  l1:
    enabled: true
    max_entries: 1000
    max_memory_mb: 256
    ttl_seconds: 3600
    cleanup_interval_seconds: 300
    eviction_policy: "LRU"

  l2:
    enabled: true
    database_path: "./data/cache/tbcv_cache.db"
    max_size_mb: 1024
    cleanup_interval_hours: 24
    compression_enabled: true
    compression_threshold_bytes: 1024

# Truth data configuration
truth:
  default_family: "words"
  truth_files:
    words: "./truth/aspose_words_plugins_truth.json"
    combinations: "./truth/aspose_words_plugins_combinations.json"
  pattern_types:
    - "format"
    - "api"
    - "method"
  confidence_weights:
    exact_match: 1.0
    fuzzy_match: 0.8
    context_match: 0.1

# Performance settings
performance:
  max_concurrent_workflows: 50
  worker_pool_size: 4
  memory_limit_mb: 2048
  cpu_limit_percent: 80
  file_size_limits:
    small_kb: 5
    medium_kb: 50
    large_kb: 1000
  response_time_targets:
    small_file_ms: 300
    medium_file_ms: 1000
    large_file_ms: 3000

# Workflow definitions
workflows:
  types:
    - "validate_file"
    - "validate_directory"
    - "full_validation"
    - "content_update"
  checkpoints:
    - "workflow_start"
    - "detection_start"
    - "fuzzy_analysis"
    - "context_analysis"
    - "detection_complete"
    - "validation_start"
    - "validation_complete"
    - "enhancement_start"
    - "enhancement_complete"
    - "workflow_complete"

# Logging configuration
logging:
  level: "INFO"
  format: "json"
  file_path: "./data/logs/tbcv.log"
  max_file_size_mb: 100
  backup_count: 5
  console_output: true
  structured_logging: true

# Monitoring settings
monitoring:
  enabled: true
  metrics_endpoint: "/metrics"
  health_endpoint: "/health"
  collect_system_metrics: true
  collect_application_metrics: true
  prometheus_port: 9090

# Database configuration
database:
  url: "sqlite:///./data/tbcv.db"
  echo: false
  pool_size: 20
  max_overflow: 30
  pool_timeout: 30
  pool_recycle: 3600
  connect_args:
    check_same_thread: false

# Batch processing settings
batch_processing:
  default_workers: 4
  max_workers: 16
  worker_timeout_seconds: 300
  queue_size_limit: 1000
  memory_limit_per_worker_mb: 256
  progress_reporting_interval_seconds: 5
  file_patterns:
    - "*.md"
    - "*.markdown"
  exclude_patterns:
    - ".git/*"
    - "node_modules/*"
    - "*.tmp"
    - "*~"

# Orchestrator concurrency limits
orchestrator:
  max_file_workers: 4
  retry_timeout_s: 120
  retry_backoff_base: 0.5
  retry_backoff_cap: 8
  agent_limits:
    llm_validator: 1
    content_validator: 2
    truth_manager: 4
    fuzzy_detector: 2
```

### config/agent.yaml
Agent-specific configuration file.

```yaml
agents:
  truth_manager:
    enabled: true
    cache_ttl: 3600
    truth_directories:
      - "./truth"
    supported_families:
      - words
      - cells
      - slides
      - pdf
      - email

  fuzzy_detector:
    enabled: true
    similarity_threshold: 0.85
    min_pattern_length: 3
    max_results: 10
    cache_ttl: 1800
    use_levenshtein: true
    use_jaro_winkler: true
    pattern_boost_multiplier: 1.2

  content_validator:
    enabled: true
    validation_types:
      - yaml
      - markdown
      - code
      - links
      - structure
    link_validation_enabled: true
    link_timeout_seconds: 5
    max_concurrent_validations: 10
    cache_ttl: 1800

  content_enhancer:
    enabled: true
    auto_link_plugins: true
    link_format: "[{name}](https://products.aspose.com/{family}/{slug})"
    severity_threshold: medium
    max_enhancements_per_file: 50
    preserve_formatting: true

  llm_validator:
    enabled: true
    provider: ollama
    model: llama2
    temperature: 0.3
    max_tokens: 2048
    timeout_seconds: 30
    retry_attempts: 3
    retry_delay_seconds: 2
    fallback_providers:
      - openai
      - gemini

  code_analyzer:
    enabled: true
    languages:
      - python
      - csharp
      - java
      - javascript
    max_complexity_threshold: 15
    analyze_security: true
    analyze_performance: true
    cache_ttl: 3600

  orchestrator:
    enabled: true
    max_concurrent_workflows: 50
    workflow_timeout_seconds: 600
    checkpoint_interval: 10
    enable_auto_recovery: true
    max_retry_attempts: 3

  recommendation_agent:
    enabled: true
    confidence_threshold: 0.7
    max_recommendations_per_file: 20
    auto_approve_high_confidence: false
    high_confidence_threshold: 0.95

  enhancement_agent:
    enabled: true
    apply_threshold: medium
    backup_original: true
    validate_after_enhancement: true

global:
  message_timeout: 30
  agent_startup_timeout: 10
  health_check_interval: 60
  log_level: info
  enable_performance_metrics: true
```

### config/perf.json
Performance tuning configuration.

```json
{
  "system": {
    "worker_pool_size": 8,
    "max_concurrent_workflows": 100,
    "memory_limit_mb": 4096,
    "cpu_limit_percent": 90,
    "file_size_limits": {
      "small_kb": 5,
      "medium_kb": 50,
      "large_kb": 1000
    },
    "response_time_targets": {
      "small_file_ms": 300,
      "medium_file_ms": 1000,
      "large_file_ms": 3000
    }
  },
  "cache": {
    "l1_max_memory_mb": 512,
    "l2_max_size_mb": 2048,
    "ttl_seconds": 3600,
    "cleanup_interval_seconds": 300
  },
  "database": {
    "pool_size": 30,
    "max_overflow": 50,
    "pool_timeout": 60,
    "pool_recycle": 1800
  },
  "agents": {
    "llm_validator": {
      "concurrency_limit": 1,
      "timeout_seconds": 60,
      "retry_attempts": 3
    },
    "content_validator": {
      "concurrency_limit": 4,
      "batch_size": 10
    },
    "fuzzy_detector": {
      "concurrency_limit": 2,
      "cache_size": 2000
    }
  }
}
```

### config/tone.json
LLM tone and style configuration.

```json
{
  "recommendations": {
    "tone": "professional",
    "style": "concise",
    "language": "en",
    "max_length": 500,
    "include_examples": true,
    "severity_levels": {
      "error": "critical",
      "warning": "important",
      "info": "suggestion"
    }
  },
  "enhancements": {
    "preserve_formatting": true,
    "add_comments": false,
    "link_style": "markdown",
    "info_text_placement": "after_code"
  },
  "validation": {
    "strict_mode": false,
    "tolerance_level": "medium",
    "custom_rules": []
  }
}
```

## Environment Variables

Environment variables override configuration file values. Use `TBCV_` prefix.

### Core System
```bash
export TBCV_SYSTEM_LOG_LEVEL=debug
export TBCV_SYSTEM_DEBUG=true
export TBCV_SYSTEM_ENVIRONMENT=production
export TBCV_DATA_DIRECTORY=/var/tbcv/data
```

### Server Configuration
```bash
export TBCV_SERVER_HOST=0.0.0.0
export TBCV_SERVER_PORT=8080
export TBCV_SERVER_ENABLE_CORS=false
export TBCV_REQUEST_TIMEOUT_SECONDS=60
```

### Database
```bash
export TBCV_DATABASE_URL=postgresql://user:pass@localhost/tbcv
export TBCV_DATABASE_ECHO=false
export TBCV_DATABASE_POOL_SIZE=50
```

### Agent Configuration
```bash
export TBCV_FUZZY_DETECTOR_SIMILARITY_THRESHOLD=0.9
export TBCV_CONTENT_VALIDATOR_LINK_VALIDATION=true
export TBCV_LLM_VALIDATOR_PROVIDER=openai
export TBCV_LLM_VALIDATOR_MODEL=gpt-4
```

### Performance Tuning
```bash
export TBCV_PERFORMANCE_WORKER_POOL_SIZE=16
export TBCV_PERFORMANCE_MAX_CONCURRENT_WORKFLOWS=200
export TBCV_CACHE_L1_MAX_MEMORY_MB=1024
export TBCV_CACHE_L2_MAX_SIZE_MB=8192
```

### External Services
```bash
export OLLAMA_BASE_URL=http://localhost:11434
export OPENAI_API_KEY=sk-...
export GEMINI_API_KEY=...
```

## Configuration Loading

### Priority Order
1. Environment variables (highest priority)
2. Command-line arguments
3. Configuration files
4. Default values (lowest priority)

### File Locations
Configuration files are searched in this order:
1. Current working directory
2. User home directory (`~/.tbcv/`)
3. System directory (`/etc/tbcv/`)

### Hot Reloading
Some configuration changes take effect immediately:
- Log levels
- Cache settings
- Agent enable/disable flags

Others require restart:
- Server host/port
- Database connection
- Core agent configurations

## Validation

Configuration files are validated on load:

### Schema Validation
- YAML syntax checking
- Required field validation
- Type checking
- Range validation

### Runtime Validation
- Path existence checks
- Network connectivity tests
- Database connection validation
- Agent dependency checks

## Custom Configuration

### Development Setup
```yaml
# config/development.yaml
system:
  environment: development
  debug: true
  log_level: debug

server:
  host: localhost
  port: 8080

database:
  url: sqlite:///./data/tbcv_dev.db

agents:
  llm_validator:
    enabled: false  # Disable for faster testing
```

### Production Setup
```yaml
# config/production.yaml
system:
  environment: production
  debug: false
  log_level: info

server:
  host: 0.0.0.0
  port: 8080
  enable_cors: false

database:
  url: postgresql://tbcv:password@db:5432/tbcv

performance:
  worker_pool_size: 16
  max_concurrent_workflows: 200
  memory_limit_mb: 8192

cache:
  l1:
    max_memory_mb: 1024
  l2:
    max_size_mb: 4096
```

### Docker Configuration
```yaml
# config/docker.yaml
system:
  data_directory: /app/data

server:
  host: 0.0.0.0
  port: 8080

database:
  url: sqlite:////app/data/tbcv.db

cache:
  l2:
    database_path: /app/data/cache/tbcv_cache.db
```

## Configuration Management

### CLI Configuration
```bash
# Use specific config file
tbcv --config config/production.yaml validate-file example.md

# Override with environment
TBCV_SYSTEM_LOG_LEVEL=debug tbcv validate-file example.md
```

### API Configuration
```bash
# Check current configuration
curl http://localhost:8080/admin/config

# Reload configuration
curl -X POST http://localhost:8080/admin/config/reload
```

### Monitoring Configuration
```bash
# View active configuration
curl http://localhost:8080/admin/config/active

# Validate configuration
curl http://localhost:8080/admin/config/validate
```

## Security Considerations

### Sensitive Data
- API keys stored in environment variables
- Database credentials encrypted
- Configuration files with restricted permissions

### Network Security
- CORS configuration for web UI
- Request size limits
- Timeout settings to prevent DoS

### Access Control
- File system access restrictions
- Database query limits
- Agent execution controls

## Troubleshooting

### Common Issues

**Configuration not loading**:
- Check file permissions
- Verify YAML syntax
- Ensure correct file paths

**Environment variables ignored**:
- Check variable naming (TBCV_ prefix)
- Verify shell environment
- Restart application

**Performance issues**:
- Review worker pool sizes
- Check cache configurations
- Monitor memory usage

**Database connection failures**:
- Verify connection strings
- Check network connectivity
- Review connection pool settings

### Diagnostic Commands
```bash
# Validate configuration
python -c "from core.config import get_settings; print(get_settings())"

# Check environment variables
env | grep TBCV_

# Test configuration loading
python -c "import yaml; yaml.safe_load(open('config/main.yaml'))"