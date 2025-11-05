# TBCV Operations Guide

| **Title** | Operations Guide |
|---|---|
| **Version** | auto |
| **Source** | Logging and error handling analysis @ 2025-11-03T07:43:18Z |

## Overview

This guide provides comprehensive operational procedures for monitoring, troubleshooting, and maintaining the TBCV system in production environments. It covers logging strategies, error handling patterns, performance monitoring, and routine maintenance tasks.

---

## Logging & Monitoring

### Structured Logging System (`core/logging.py:1-432`)

#### Log Configuration

**Default Setup** (`config/main.yaml:137-145`):
```yaml
logging:
  level: "INFO"
  format: "json"
  file_path: "./data/logs/tbcv.log"
  max_file_size_mb: 100
  backup_count: 5
  console_output: true
  structured_logging: true
````

**JSON Log Format** (`core/logging.py:41-81`):

```json
{
  "timestamp": "2025-11-03T07:43:18.200Z",
  "level": "INFO",
  "name": "tbcv.agents.orchestrator",
  "message": "Workflow started",
  "workflow_id": "wf_abc123",
  "workflow_type": "validate_file",
  "file_path": "./content/example.md",
  "agent_id": "orchestrator",
  "processing_time_ms": 245,
  "memory_usage_mb": 15.2
}
```

#### Log Levels & Usage

| Level        | Purpose               | Examples                                     | Typical Volume  |
| ------------ | --------------------- | -------------------------------------------- | --------------- |
| **DEBUG**    | Development debugging | Agent state changes, cache operations        | High (dev only) |
| **INFO**     | Normal operations     | Workflow start/complete, API requests        | Medium          |
| **WARNING**  | Potential issues      | Validation warnings, performance degradation | Low             |
| **ERROR**    | Operation failures    | Agent failures, database errors              | Very Low        |
| **CRITICAL** | System failures       | Service unavailable, data corruption         | Rare            |

#### Key Log Categories

**Workflow Logs**:

```json
{
  "timestamp": "2025-11-03T07:43:18.200Z",
  "level": "INFO",
  "name": "tbcv.agents.orchestrator",
  "message": "Workflow completed successfully",
  "workflow_id": "wf_abc123",
  "workflow_type": "validate_file",
  "total_steps": 5,
  "processing_time_ms": 1245,
  "files_processed": 1,
  "validation_issues": 2,
  "enhancements_applied": 1
}
```

**Performance Logs**:

```json
{
  "timestamp": "2025-11-03T07:43:18.200Z",
  "level": "INFO",
  "name": "tbcv.core.cache",
  "message": "Cache performance metrics",
  "cache_level": "L1",
  "hit_rate": 0.85,
  "miss_rate": 0.15,
  "total_requests": 1000,
  "memory_usage_mb": 128.5,
  "evictions": 15
}
```

**Error Logs**:

```json
{
  "timestamp": "2025-11-03T07:43:18.200Z",
  "level": "ERROR",
  "name": "tbcv.agents.code_analyzer",
  "message": "External code fetch failed",
  "error_type": "HTTPTimeoutError",
  "error_details": "Request timeout after 10 seconds",
  "url": "https://api.github.com/gists/abc123",
  "retry_count": 3,
  "workflow_id": "wf_def456",
  "stack_trace": "..."
}
```

### Log Analysis & Monitoring

#### Real-time Monitoring Commands

```batch
REM Monitor live logs (Windows)
Get-Content -Path "data\logs\tbcv.log" -Wait -Tail 50

REM Filter by log level
findstr "ERROR" data\logs\tbcv.log
findstr "WARNING" data\logs\tbcv.log

REM Monitor specific agent
findstr "orchestrator" data\logs\tbcv.log | findstr "INFO"

REM Monitor workflow performance
findstr "processing_time_ms" data\logs\tbcv.log
```

#### Log Aggregation Queries

**PowerShell Log Analysis**:

```powershell
# Parse JSON logs and analyze
$logs = Get-Content "data\logs\tbcv.log" | ForEach-Object { ConvertFrom-Json $_ }

# Error frequency by agent
$logs | Where-Object { $_.level -eq "ERROR" } | Group-Object name | Sort-Object Count -Descending

# Average processing time by workflow type
$logs | Where-Object { $_.processing_time_ms } | Group-Object workflow_type | ForEach-Object {
    $avg = ($_.Group | Measure-Object processing_time_ms -Average).Average
    [PSCustomObject]@{ WorkflowType = $_.Name; AvgTimeMs = [math]::Round($avg, 2) }
}

# Cache hit rates
$logs | Where-Object { $_.hit_rate } | Select-Object timestamp, cache_level, hit_rate, memory_usage_mb
```

#### Performance Metrics Collection

**Built-in Metrics Endpoint** (`api/server.py:850-900`):

```batch
REM System metrics
curl http://localhost:8080/metrics

REM Sample response:
REM {
REM   "system": {
REM     "uptime_seconds": 3600,
REM     "memory_usage_mb": 256.5,
REM     "cpu_percent": 15.2,
REM     "disk_usage_percent": 45.8
REM   },
REM   "application": {
REM     "total_workflows": 1250,
REM     "active_workflows": 5,
REM     "completed_workflows": 1200,
REM     "failed_workflows": 45,
REM     "avg_processing_time_ms": 890
REM   },
REM   "cache": {
REM     "l1_hit_rate": 0.85,
REM     "l2_hit_rate": 0.72,
REM     "total_cache_size_mb": 450.2
REM   },
REM   "database": {
REM     "total_connections": 15,
REM     "active_connections": 3,
REM     "avg_query_time_ms": 12.5,
REM     "database_size_mb": 125.8
REM   }
REM }
```

---

## Error Handling & Recovery

### Error Classification System

#### Severity Levels

**CRITICAL** — System Down:

* Database unavailable
* All agents offline
* Configuration corruption
* Out of disk space

**HIGH** — Service Degraded:

* Individual agent failures
* Cache system down
* External API unavailable
* Memory leaks detected

**MEDIUM** — Functional Issues:

* Validation timeouts
* File processing errors
* Performance degradation
* Cache misses increasing

**LOW** — Operational Warnings:

* Slow response times
* Truth table updates
* Configuration changes
* Maintenance notifications

#### Automatic Recovery Patterns

**Retry Logic** (`agents/base.py:200-250`):

```python
# Exponential backoff with jitter
retry_delays = [1, 2, 4, 8, 16]  # seconds
max_retries = 3
jitter_factor = 0.1

# Retryable error types:
# - HTTPTimeoutError
# - ConnectionError  
# - TemporaryFailure
# - ResourceBusyError
```

**Circuit Breaker Pattern**:

```yaml
circuit_breaker:
  failure_threshold: 5      # failures before opening
  recovery_timeout: 30      # seconds before retry
  half_open_max_calls: 3    # test calls in half-open state
```

**Graceful Degradation**:

* Plugin detection: Fall back to exact matching if fuzzy algorithms fail
* Code analysis: Skip external fetching if network unavailable
* Cache: Bypass cache if L1/L2 systems fail
* Validation: Continue with basic checks if advanced features fail

### Common Error Scenarios

#### Agent Initialization Failures

**Symptoms**:

```json
{
  "level": "ERROR",
  "message": "Agent initialization failed",
  "agent_id": "truth_manager",
  "error_type": "FileNotFoundError",
  "error_details": "Truth file not found: ./truth/words.json"
}
```

**Diagnosis**:

```batch
REM Check truth files
dir truth\*.json

REM Verify file permissions
icacls truth\words.json

REM Test agent initialization
python -c "from agents.truth_manager import TruthManagerAgent; agent = TruthManagerAgent('test')"
```

**Resolution**:

```batch
REM 1. Restore truth files from backup
copy backup\truth\*.json truth\

REM 2. Download latest truth tables
curl -o truth\words.json https://raw.githubusercontent.com/aspose/tbcv/main/truth/words.json

REM 3. Generate minimal truth table
python -c "import json; json.dump({'plugins': {}}, open('truth/words.json', 'w'))"

REM 4. Restart application
python main.py --mode api --port 8080
```

#### Database Connection Issues

**Symptoms**:

```json
{
  "level": "CRITICAL",
  "message": "Database connection failed",
  "error_type": "OperationalError",
  "error_details": "Unable to open database file",
  "database_path": "./data/tbcv.db"
}
```

**Diagnosis**:

```batch
REM Check database file
dir data\tbcv.db

REM Test database connection
python -c "from core.database import db_manager; print(db_manager.test_connection())"

REM Check disk space
dir data
fsutil volume diskfree C:\
```

**Resolution**:

```batch
REM 1. Create data directory if missing
mkdir data

REM 2. Initialize database
python -c "from core.database import db_manager; db_manager.initialize_database()"

REM 3. Restore from backup
copy backup\tbcv.db data\tbcv.db

REM 4. Check file permissions
icacls data\tbcv.db
```

#### Memory Exhaustion

**Symptoms**:

```json
{
  "level": "ERROR",
  "message": "Memory limit exceeded",
  "memory_usage_mb": 2048,
  "memory_limit_mb": 2048,
  "active_workflows": 25,
  "cache_size_mb": 512
}
```

**Immediate Actions**:

```batch
REM 1. Clear caches
curl -X POST http://localhost:8080/admin/cache/clear

REM 2. Cancel non-critical workflows
curl -X POST http://localhost:8080/workflows/cancel-batch

REM 3. Reduce worker pool
set TBCV_PERFORMANCE_WORKER_POOL_SIZE=2

REM 4. Restart with reduced limits
set TBCV_PERFORMANCE_MEMORY_LIMIT_MB=1024
python main.py --mode api --no-clean
```

#### External API Failures

**Symptoms**:

```json
{
  "level": "WARNING",
  "message": "GitHub API rate limit exceeded",
  "api_endpoint": "https://api.github.com/gists",
  "rate_limit_remaining": 0,
  "rate_limit_reset": "2025-11-03T08:43:18Z",
  "retry_after_seconds": 3600
}
```

**Automatic Handling**:

* Code analysis continues without external fetching
* Results cached to avoid repeated API calls
* Rate limit headers respected automatically
* Graceful degradation to local analysis only

---

## Health Monitoring

### Health Check Endpoints

#### Liveness Check

```batch
curl http://localhost:8080/health/live
REM Expected: {"status": "healthy", "timestamp": "2025-11-03T07:43:18.200Z"}
```

#### Readiness Check

```batch
curl http://localhost:8080/health/ready
```

**Sample Response**:

```json
{
  "status": "ready",
  "timestamp": "2025-11-03T07:43:18.200Z",
  "agents": {
    "truth_manager": "healthy",
    "fuzzy_detector": "healthy", 
    "content_validator": "healthy",
    "content_enhancer": "healthy",
    "code_analyzer": "healthy",
    "orchestrator": "healthy"
  },
  "database": "connected",
  "cache": {
    "l1": "healthy",
    "l2": "healthy"
  },
  "external_services": {
    "github_api": "available"
  }
}
```

#### Detailed Status Check

```batch
curl http://localhost:8080/admin/status
```

**Sample Response**:

```json
{
  "system_info": {
    "version": "2.0.0",
    "uptime_seconds": 7200,
    "python_version": "3.12.0",
    "platform": "Windows-10"
  },
  "resource_usage": {
    "memory_mb": 256.5,
    "cpu_percent": 12.3,
    "disk_usage_gb": 1.2,
    "active_connections": 5
  },
  "workflow_stats": {
    "total_workflows": 1250,
    "active_workflows": 3,
    "queued_workflows": 0,
    "failed_workflows_24h": 2
  }
}
```

### Monitoring Dashboards

#### Web Dashboard Access

```batch
REM Main dashboard
start http://localhost:8080/dashboard

REM Workflow monitoring
start http://localhost:8080/dashboard/workflows

REM Agent status
start http://localhost:8080/dashboard/agents

REM Performance metrics
start http://localhost:8080/dashboard/metrics

REM Audit logs
start http://localhost:8080/dashboard/logs
```

#### CLI Monitoring Commands

```batch
REM System status summary
python -m tbcv.cli status

REM Agent health check
python -m tbcv.cli check-agents --verbose

REM Performance test
python -m tbcv.cli test --performance --duration 60

REM Database statistics
python -c "from core.database import db_manager; print(db_manager.get_statistics())"
```

---

## Routine Maintenance

### Daily Operations

#### Log Rotation & Cleanup

```batch
REM Automatic log rotation (configured in main.yaml)
REM backup_count: 5 keeps 5 previous log files
REM max_file_size_mb: 100 rotates at 100MB

REM Manual log cleanup (if needed)
forfiles /p data\logs /s /m *.log.* /d -7 /c "cmd /c del @path"
```

#### Cache Maintenance

```batch
REM Clear expired cache entries
curl -X POST http://localhost:8080/admin/cache/cleanup

REM Cache statistics
curl http://localhost:8080/admin/cache/stats

REM Force cache rebuild (if needed)
curl -X POST http://localhost:8080/admin/cache/rebuild
```

#### Database Maintenance

```batch
REM Database vacuum (reclaim space)
python -c "from core.database import db_manager; db_manager.vacuum()"

REM Backup database
copy data\tbcv.db backup\tbcv_%date:~-4,4%%date:~-10,2%%date:~-7,2%.db

REM Clean old workflow records (optional)
python -c "from core.database import db_manager; db_manager.cleanup_old_workflows(days=90)"
```

### Weekly Operations

#### Performance Review

```batch
REM Generate performance report
curl http://localhost:8080/admin/reports/performance?days=7 > weekly_performance.json

REM Analyze error trends
findstr "ERROR" data\logs\tbcv.log* | findstr /c:"%date:~-10%" > weekly_errors.txt

REM Check disk usage
dir data /s
dir data\cache /s
dir data\logs /s
```

#### Truth Table Updates

```batch
REM Check for truth table updates
curl -I https://raw.githubusercontent.com/aspose/tbcv/main/truth/words.json

REM Download latest truth tables (if updated)
curl -o truth\words.json https://raw.githubusercontent.com/aspose/tbcv/main/truth/words.json
curl -o rules\words.json https://raw.githubusercontent.com/aspose/tbcv/main/rules/words.json

REM Validate and reload
python -c "from agents.truth_manager import TruthManagerAgent; agent = TruthManagerAgent('test'); agent.validate_truth_data()"
curl -X POST http://localhost:8080/admin/agents/reload/truth_manager
```

### Monthly Operations

#### System Health Assessment

```batch
REM Generate comprehensive health report
curl "http://localhost:8080/admin/reports/health?period=30days" > monthly_health.json

REM Archive old logs
mkdir archive\logs\%date:~-4,4%_%date:~-10,2%
move data\logs\*.log.* archive\logs\%date:~-4,4%_%date:~-10,2%\

REM Database integrity check
python -c "from core.database import db_manager; print(db_manager.integrity_check())"

REM Performance benchmarks
python -m tbcv.cli test --performance --duration 300 --output monthly_benchmark.json
```

#### Configuration Review

```batch
REM Review current configuration
python -c "from core.config import get_settings; import json; print(json.dumps(get_settings().dict(), indent=2))" > current_config.json

REM Compare with baseline
fc /N current_config.json baseline_config.json

REM Update configuration if needed
copy config\production.yaml config\main.yaml
```

---

## Troubleshooting Workflows

### Diagnostic Information Collection

#### System Information

```batch
REM Create diagnostic bundle
mkdir diagnostic_%date:~-4,4%%date:~-10,2%%date:~-7,2%
cd diagnostic_%date:~-4,4%%date:~-10,2%%date:~-7,2%

REM System info
systeminfo > systeminfo.txt
python --version > python_version.txt
dir /s ..\data > data_structure.txt

REM Application info
curl http://localhost:8080/admin/status > app_status.json
curl http://localhost:8080/metrics > metrics.json
python -m tbcv.cli check-agents --verbose > agent_status.txt

REM Logs (last 1000 lines)
tail -1000 ..\data\logs\tbcv.log > recent_logs.json
findstr "ERROR" ..\data\logs\tbcv.log* > error_logs.txt

REM Configuration
copy ..\config\main.yaml current_config.yaml
set > environment_variables.txt

REM Package bundle
tar -czf tbcv_diagnostic_%date:~-4,4%%date:~-10,2%%date:~-7,2%.tar.gz *
cd ..
```

### Performance Troubleshooting

#### Slow Response Times

**Investigation Steps**:

```batch
REM 1. Check system resources
wmic cpu get loadpercentage /value
wmic OS get TotalVisibleMemorySize,FreePhysicalMemory /value

REM 2. Monitor database performance
python -c "from core.database import db_manager; print(db_manager.get_slow_queries())"

REM 3. Check cache performance
curl http://localhost:8080/admin/cache/stats

REM 4. Analyze workflow bottlenecks
findstr "processing_time_ms" data\logs\tbcv.log | sort /r
```

**Common Solutions**:

```batch
REM Increase cache sizes
set TBCV_CACHE_L1_MAX_ENTRIES=2000
set TBCV_CACHE_L1_MAX_MEMORY_MB=512

REM Reduce concurrent workloads
set TBCV_ORCHESTRATOR_MAX_CONCURRENT_WORKFLOWS=25
set TBCV_PERFORMANCE_WORKER_POOL_SIZE=4

REM Enable performance monitoring
set TBCV_SYSTEM_DEBUG=true
set TBCV_LOG_LEVEL=DEBUG
```

#### High Memory Usage

**Memory Analysis**:

```batch
REM Monitor memory usage over time
for /l %%i in (1,1,60) do (
    curl -s http://localhost:8080/metrics | findstr memory_usage_mb
    timeout /t 10 /nobreak
)

REM Check for memory leaks
python -c "import gc; gc.collect(); print(f'Objects: {len(gc.get_objects())}')"
```

**Memory Optimization**:

```batch
REM Force garbage collection
curl -X POST http://localhost:8080/admin/system/gc

REM Reduce cache sizes
set TBCV_CACHE_L1_MAX_MEMORY_MB=128
set TBCV_CACHE_L2_MAX_SIZE_MB=512

REM Limit concurrent workflows
set TBCV_ORCHESTRATOR_MAX_CONCURRENT_WORKFLOWS=10
```

---

## Recovery Procedures

### Graceful Shutdown

```batch
REM 1. Stop accepting new requests
curl -X POST http://localhost:8080/admin/maintenance/enable

REM 2. Wait for active workflows to complete
curl http://localhost:8080/admin/workflows/active | findstr "count"

REM 3. Save system state
curl -X POST http://localhost:8080/admin/system/checkpoint

REM 4. Shutdown application
taskkill /f /im python.exe /fi "WINDOWTITLE eq tbcv*"
```

### Emergency Recovery

```batch
REM 1. Stop all TBCV processes
taskkill /f /im python.exe

REM 2. Backup current state
copy data\tbcv.db backup\emergency_%date:~-4,4%%date:~-10,2%%date:~-7,2%.db
copy data\logs\tbcv.log backup\emergency_%date:~-4,4%%date:~-10,2%%date:~-7,2%.log

REM 3. Clear problematic state
del data\cache\*.db
del data\temp\*

REM 4. Restart with minimal configuration
set TBCV_SYSTEM_DEBUG=true
set TBCV_CACHE_L1_ENABLED=false
set TBCV_CACHE_L2_ENABLED=false
python main.py --mode api --port 8080 --log-level debug
```

### Data Recovery

```batch
REM Restore from backup
copy backup\tbcv_latest.db data\tbcv.db

REM Rebuild indexes
python -c "from core.database import db_manager; db_manager.rebuild_indexes()"

REM Validate data integrity
python -c "from core.database import db_manager; print(db_manager.validate_integrity())"

REM Restart with full functionality
python main.py --mode api --port 8080
```

---

**Operational Support Resources**

* **[Runbook](runbook.md)** — Application startup and configuration
* **[Data Flow](dataflow.md)** — Understanding data management and schemas
* **[Architecture](architecture.md)** — System component interactions and dependencies