# TBCV Troubleshooting Guide

This guide helps resolve common issues when running TBCV.

## Quick Diagnostics

```bash
# Check server is running
curl http://localhost:8080/health/live

# Check all components are ready
curl http://localhost:8080/health/ready

# Check agents are registered
curl http://localhost:8080/agents

# View logs
tail -f data/logs/tbcv.log
```

## Common Issues

### 1. Server Won't Start

**Symptom**: `python main.py --mode api` fails

**Possible Causes & Solutions**:

#### Port Already in Use
```bash
# Check what's using port 8080
netstat -ano | findstr :8080   # Windows
lsof -i :8080                  # Linux/Mac

# Kill process or use different port
python main.py --mode api --port 8081
```

#### Database Lock
```bash
# Check database exists
ls -la data/tbcv.db

# Reset database
rm data/tbcv.db
python -c "from core.database import db_manager; db_manager.initialize_database()"
```

#### Missing Dependencies
```bash
# Reinstall requirements
pip install -r requirements.txt

# Check Python version (needs 3.8+)
python --version
```

#### Import Errors
```bash
# Check PYTHONPATH includes project root
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or run from project root
cd /path/to/tbcv
python main.py --mode api
```

### 2. Ollama/LLM Connection Issues

**Symptom**: LLM validation fails or timeouts

#### Ollama Not Running
```bash
# Check Ollama is accessible
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve

# In another terminal, pull model
ollama pull llama2
```

#### Wrong Model Name
```yaml
# config/agent.yaml
llm_validator:
  model: llama2  # Must match installed model

# List installed models
ollama list
```

#### Timeout Issues
```yaml
# config/agent.yaml
llm_validator:
  timeout_seconds: 60  # Increase if slow
```

#### Disable LLM Validation
```yaml
# config/main.yaml
validation:
  mode: "heuristic_only"  # Skip LLM entirely
```

Or via environment variable:
```bash
export TBCV_LLM__ENABLED=false
python main.py --mode api
```

### 3. Database Errors

#### "Database is locked"
```bash
# Close all connections
pkill -f "python main.py"

# Check for orphaned processes
ps aux | grep tbcv

# Reset database
rm data/tbcv.db
python -c "from core.database import db_manager; db_manager.initialize_database()"
```

#### "No such table"
```bash
# Database schema not initialized
python -c "from core.database import db_manager; db_manager.initialize_database()"
```

#### Corrupted Database
```bash
# Backup old database
mv data/tbcv.db data/tbcv.db.backup

# Create fresh database
python -c "from core.database import db_manager; db_manager.initialize_database()"

# Note: This loses all validation history
```

### 4. Agent Not Responding

**Symptom**: Agent timeouts or "Agent not available"

#### Check Agent Status
```bash
curl http://localhost:8080/agents/<agent_id>
```

#### Agent Busy (Concurrency Limit)
```yaml
# config/main.yaml
orchestrator:
  retry_timeout_s: 300  # Increase timeout
  agent_limits:
    llm_validator: 2    # Allow more concurrent LLM calls
```

#### Agent Crashed
```bash
# Check logs for errors
tail -f data/logs/tbcv.log | grep agent_id

# Restart server
pkill -f "python main.py"
python main.py --mode api
```

#### Clear Agent Cache
```python
from agents.base import agent_registry
agent = agent_registry.get_agent("fuzzy_detector")
if agent:
    agent.clear_cache()
    print("Cache cleared")
```

### 5. Validation Failures

#### "Truth data not found"
```bash
# Check truth files exist
ls -la truth/*.json

# Check family name is correct
python -c "from agents.truth_manager import TruthManagerAgent; print(TruthManagerAgent('tm').get_supported_families())"
```

#### "No plugins detected"
```yaml
# Lower similarity threshold
# config/main.yaml
agents:
  fuzzy_detector:
    similarity_threshold: 0.7  # Default: 0.85
```

#### "Validation timeout"
```yaml
# Increase timeout
# config/main.yaml
content_validator:
  link_timeout_seconds: 10  # Default: 5
```

### 6. Enhancement Issues

#### "Safety gate: rewrite_ratio too high"
```yaml
# Increase threshold
# config/main.yaml
content_enhancer:
  rewrite_ratio_threshold: 0.7  # Default: 0.5 (50%)
```

#### "Recommendation not found"
```bash
# Check recommendation exists
curl http://localhost:8080/api/recommendations/<rec-id>

# Check status is "approved"
curl http://localhost:8080/api/recommendations?status=approved&validation_id=<val-id>
```

#### "No approved recommendations"
```bash
# Approve recommendations first
curl -X POST http://localhost:8080/api/recommendations/<rec-id>/review \
  -H "Content-Type: application/json" \
  -d '{"status": "accepted", "reviewer": "admin"}'
```

### 7. Performance Issues

#### Slow Validation
```yaml
# Enable caching
# config/main.yaml
cache:
  l1:
    enabled: true
  l2:
    enabled: true

# Reduce validation types
validation_types: ["yaml", "markdown"]  # Skip code, links, truth
```

#### High Memory Usage
```yaml
# Reduce workers
# config/main.yaml
orchestrator:
  max_file_workers: 2  # Default: 4

performance:
  memory_limit_per_worker_mb: 256
```

#### Disk Space Issues
```bash
# Clear old cache
rm -rf data/cache/*.db

# Clear old logs
find data/logs -name "*.log" -mtime +7 -delete

# Vacuum database
python -c "from core.database import db_manager; db_manager.vacuum()"
```

### 8. CLI Issues

#### "Command not found"
```bash
# Run as module
python -m cli.main validate-file file.md

# Or install as package
pip install -e .
tbcv validate-file file.md
```

#### "No module named 'cli'"
```bash
# Ensure PYTHONPATH is set
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or run from project root
cd /path/to/tbcv
python -m cli.main validate-file file.md
```

### 9. API Issues

#### "404 Not Found" on Valid Endpoint
```bash
# Check server is running on correct port
curl http://localhost:8080/health/live

# Check endpoint path is correct
curl http://localhost:8080/  # Lists all endpoints
```

#### "422 Unprocessable Entity"
```bash
# Check request body matches schema
curl -X POST http://localhost:8080/api/validate \
  -H "Content-Type: application/json" \
  -d '{
    "content": "...",
    "file_path": "test.md",
    "family": "words"
  }'

# Required fields: content, file_path, family
```

#### CORS Errors
```yaml
# config/main.yaml
server:
  enable_cors: true
  cors_origins:
    - "http://localhost:3000"
    - "https://your-domain.com"
```

### 10. WebSocket Issues

#### "WebSocket connection failed"
```bash
# Check WebSocket endpoint is correct
ws://localhost:8080/ws/<workflow_id>

# Not wss:// unless using HTTPS
```

#### "Connection timeout"
```yaml
# config/main.yaml
server:
  websocket_ping_interval: 60  # Default: 30
  websocket_ping_timeout: 20   # Default: 10
```

## Debug Mode

Enable debug logging:

```bash
# Via environment variable
export TBCV_LOG_LEVEL=DEBUG
python main.py --mode api

# Via config
# config/main.yaml
system:
  debug: true
  log_level: "debug"
```

View debug logs:
```bash
tail -f data/logs/tbcv.log | grep DEBUG
```

## Health Checks

### System Health
```bash
curl http://localhost:8080/health

# Returns:
# {
#   "status": "healthy",
#   "database_connected": true,
#   "schema_present": true,
#   "agents_registered": 8,
#   "version": "2.0.0"
# }
```

### Readiness Check
```bash
curl http://localhost:8080/health/ready

# Returns:
# {
#   "status": "ready",
#   "checks": {
#     "database": true,
#     "schema": true,
#     "agents": true
#   }
# }
```

### Liveness Check
```bash
curl http://localhost:8080/health/live

# Returns:
# {
#   "status": "alive",
#   "timestamp": "2024-01-15T10:00:00Z"
# }
```

## Log Analysis

### Find Errors
```bash
grep ERROR data/logs/tbcv.log | tail -20
```

### Find Agent Issues
```bash
grep "agent_id.*error" data/logs/tbcv.log
```

### Track Request
```bash
grep "request_id=<id>" data/logs/tbcv.log
```

### Performance Analysis
```bash
grep "response_time_ms" data/logs/tbcv.log | \
  awk '{sum+=$NF; count++} END {print "Avg:", sum/count, "ms"}'
```

## Configuration Validation

Check configuration is valid:

```python
from core.config import get_settings

try:
    settings = get_settings()
    print("Configuration valid!")
    print(f"Environment: {settings.system.environment}")
    print(f"Debug: {settings.system.debug}")
    print(f"LLM enabled: {settings.llm.enabled}")
except Exception as e:
    print(f"Configuration error: {e}")
```

## Testing Connectivity

### Test Database
```python
from core.database import db_manager

print(f"Connected: {db_manager.is_connected()}")
print(f"Schema present: {db_manager.has_required_schema()}")
```

### Test Truth Data
```python
from agents.base import agent_registry
truth_mgr = agent_registry.get_agent("truth_manager")
if truth_mgr:
    result = await truth_mgr.process_request("load_truth_data", {"family": "words"})
    print(f"Loaded {result['plugins_count']} plugins")
```

### Test Ollama
```bash
curl -X POST http://localhost:11434/api/generate \
  -d '{
    "model": "llama2",
    "prompt": "Say hello",
    "stream": false
  }'
```

## Reset Everything

Nuclear option - reset entire system:

```bash
#!/bin/bash
# WARNING: This deletes all data!

# Stop server
pkill -f "python main.py"

# Delete all data
rm -rf data/

# Recreate directories
mkdir -p data/logs data/cache data/temp

# Reinitialize database
python -c "from core.database import db_manager; db_manager.initialize_database()"

# Restart server
python main.py --mode api
```

## Getting Help

1. **Check logs**: `data/logs/tbcv.log`
2. **Check configuration**: Verify `config/main.yaml` and `config/agent.yaml`
3. **Test components**: Use health endpoints and individual agent tests
4. **Enable debug**: Set `TBCV_LOG_LEVEL=DEBUG`
5. **Search issues**: Check GitHub issues for similar problems
6. **Ask for help**: Open new GitHub issue with logs and error details

## Useful Commands Reference

```bash
# Check system status
curl http://localhost:8080/health

# List all agents
curl http://localhost:8080/agents

# View workflow status
curl http://localhost:8080/workflows/<workflow-id>

# List validations
curl http://localhost:8080/api/validations?limit=10

# List recommendations
curl http://localhost:8080/api/recommendations?status=proposed

# Clear cache
curl -X POST http://localhost:8080/admin/cache/clear

# View metrics
curl http://localhost:8080/metrics
```

## When All Else Fails

1. Check Python version: `python --version` (must be 3.8+)
2. Check dependencies: `pip list | grep -E "(fastapi|uvicorn|sqlalchemy|pydantic)"`
3. Check file permissions: `ls -la data/`
4. Check disk space: `df -h`
5. Check memory: `free -m` (Linux) or Task Manager (Windows)
6. Restart everything: Stop server, delete `data/`, reinitialize, restart

If problem persists, open a GitHub issue with:
- Error message from logs
- Configuration files (sanitized)
- Python version and OS
- Steps to reproduce
