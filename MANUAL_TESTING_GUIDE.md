# TBCV Manual Testing Guide

## System Preparation Complete ✅

All systems are ready for manual testing!

### System Status

- ✅ Database initialized (`data/tbcv.db`)
- ✅ Ollama LLM available (33 models detected)
- ✅ Cache system ready (L1 + L2)
- ✅ Logs directory ready (`data/logs/`)
- ✅ Reports directory ready (`data/reports/`)

---

## Starting the Server

### Option 1: Using main.py (Recommended)

```bash
python main.py --mode api --host 127.0.0.1 --port 8585
```

**With auto-reload for development:**
```bash
python main.py --mode api --host 127.0.0.1 --port 8585 --reload
```

### Option 2: Using uvicorn directly

```bash
uvicorn api.server:app --host 127.0.0.1 --port 8585 --reload
```

**Note:** Default port is `8585` (not 8080 as mentioned in README)

---

## Access Points

### 🌐 Web Dashboard
**URL:** http://localhost:8585

**Features:**
- Home page with system overview
- Validation results list and detail views
- Workflow monitoring
- Recommendation management
- Real-time WebSocket updates

**Dashboard Endpoints:**
- **Home:** http://localhost:8585
- **Validations List:** http://localhost:8585/dashboard/validations
- **Workflows List:** http://localhost:8585/dashboard/workflows
- **Recommendations List:** http://localhost:8585/dashboard/recommendations

### 📡 REST API
**Base URL:** http://localhost:8585/api

**Key Endpoints:**
- **Health Check:** `GET /health/live`
- **API Index:** `GET /api` (lists all endpoints)
- **Validate File:** `POST /api/validate`
- **List Validations:** `GET /api/validations`
- **Get Validation:** `GET /api/validations/{id}`
- **Recommendations:** `GET /api/recommendations`
- **Enhance Content:** `POST /api/enhance`
- **Workflows:** `GET /workflows`
- **Agent Status:** `GET /agents`

### 📖 API Documentation
**Interactive API Docs (Swagger UI):** http://localhost:8585/docs
**ReDoc:** http://localhost:8585/redoc

### 🔌 WebSocket
**URL:** ws://localhost:8585/ws/{client_id}

Real-time updates for:
- Validation progress
- Workflow status changes
- Agent activity
- System events

---

## Reports and Data Locations

### Reports Directory
**Location:** `./data/reports/`

**Current Status:** Empty (reports will be generated during testing)

**Generated Reports:**
- Validation results (JSON/Markdown)
- Workflow execution reports
- System diagnostics
- Performance metrics

### Database
**Location:** `./data/tbcv.db` (266KB - already initialized)

**Tables:**
- validations
- validation_issues
- workflows
- checkpoints
- recommendations
- recommendation_reviews

### Logs
**Location:** `./data/logs/tbcv.log`

**Format:** Structured JSON logging with rotation

**Log Levels:** DEBUG, INFO, WARNING, ERROR

### Cache
**Location:** `./data/cache/tbcv_cache.db`

**Type:** Two-level caching (L1 in-memory + L2 disk-based)

---

## Manual Testing Checklist

### 1. Server Startup Tests

```bash
# Test health endpoint
curl http://localhost:8585/health/live

# Expected: {"status": "ok", "timestamp": "..."}
```

### 2. Web Dashboard Tests

1. Open http://localhost:8585 in browser
2. Navigate to Validations list
3. Navigate to Workflows list
4. Navigate to Recommendations list
5. Test real-time updates via WebSocket

### 3. API Tests

#### Validate a File

```bash
curl -X POST http://localhost:8585/api/validate \
  -H "Content-Type: application/json" \
  -d '{
    "content": "# Test\nThis is a test markdown file.\n```csharp\nvar doc = new Document();\n```",
    "file_path": "test.md",
    "family": "words"
  }'
```

#### List Validations

```bash
curl http://localhost:8585/api/validations
```

#### Get Validation Details

```bash
curl http://localhost:8585/api/validations/{validation_id}
```

#### Get Recommendations

```bash
curl http://localhost:8585/api/recommendations?validation_id={validation_id}
```

### 4. LLM Validation Tests

**Verify Ollama is running:**
```bash
curl http://localhost:11434/api/tags
```

**Recommended model:** `qwen2.5-coder:7b` (fast, accurate for code)

**Test LLM validation:**
```bash
curl -X POST http://localhost:8585/api/validate \
  -H "Content-Type: application/json" \
  -d '{
    "content": "# Tutorial\n```csharp\nvar doc = new Document();\ndoc.LoadFromFile(\"input.docx\");\n```\nPlugins: None declared",
    "file_path": "llm_test.md",
    "family": "words",
    "enable_llm": true
  }'
```

### 5. CLI Tests

```bash
# Validate a file via CLI
python -m cli.main validate-file path/to/file.md --family words --format json

# Batch validate directory
python -m cli.main validate-directory content/ --pattern "*.md" --workers 4

# Generate recommendations
python -m cli.main recommendations generate validation_id
```

### 6. WebSocket Tests

Use browser console:

```javascript
const ws = new WebSocket('ws://localhost:8585/ws/test-client');

ws.onopen = () => {
  console.log('WebSocket connected');
  ws.send(JSON.stringify({type: 'ping'}));
};

ws.onmessage = (event) => {
  console.log('Received:', event.data);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};
```

### 7. Performance Tests

```bash
# Run performance test suite
pytest tests/test_performance.py -v

# Run with benchmarks
pytest tests/test_performance.py -v --benchmark-only
```

---

## Configuration

### LLM Settings
**File:** `config/main.yaml`

```yaml
llm:
  enabled: true

validation:
  mode: "two_stage"  # Options: two_stage, heuristic_only, llm_only
  llm_thresholds:
    downgrade_threshold: 0.2
    confirm_threshold: 0.5
    upgrade_threshold: 0.8
```

### Agent Settings
**File:** `config/agent.yaml`

Control individual agent behavior (timeouts, concurrency, thresholds)

### Performance Tuning
**File:** `config/perf.json`

Adjust worker pools, memory limits, and concurrency

---

## Troubleshooting

### Server Won't Start

```bash
# Check if port is already in use
netstat -ano | findstr :8585

# Try different port
python main.py --mode api --port 8586
```

### Database Lock Errors

```bash
# Check database status
python -c "from core.database import db_manager; print('Database OK')"

# If needed, reinitialize
rm data/tbcv.db
python main.py --mode api
```

### Ollama Connection Issues

```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# If not running, start Ollama
ollama serve

# Pull a model if needed
ollama pull qwen2.5-coder:7b
```

### View Logs

```bash
# Tail logs in real-time
Get-Content data/logs/tbcv.log -Wait -Tail 50

# Or on Unix-like systems
tail -f data/logs/tbcv.log

# Filter by error level
Get-Content data/logs/tbcv.log | Select-String "error"
```

---

## Expected Test Results

### Validation Response Structure

```json
{
  "validation_id": "uuid-string",
  "file_path": "test.md",
  "family": "words",
  "status": "completed",
  "issues": [
    {
      "type": "truth_validation",
      "severity": "warning",
      "message": "Plugin used but not declared",
      "line": 5,
      "confidence": 0.85
    }
  ],
  "detections": [
    {
      "plugin_name": "some-plugin",
      "pattern": "detected-pattern",
      "confidence": 0.9
    }
  ],
  "recommendations": [
    {
      "title": "Add plugin declaration",
      "description": "...",
      "confidence": 0.8,
      "status": "pending"
    }
  ],
  "created_at": "2025-11-23T09:57:00Z"
}
```

---

## Next Steps

1. **Start the server** using one of the methods above
2. **Open the dashboard** at http://localhost:8585
3. **Test the API** using curl or the Swagger UI at http://localhost:8585/docs
4. **Run validation tests** on sample markdown files
5. **Check reports** in `./data/reports/`
6. **Monitor logs** at `./data/logs/tbcv.log`

---

## Support Files

- **Main README:** [README.md](README.md)
- **Testing Guide:** [docs/testing.md](docs/testing.md)
- **API Reference:** [docs/api_reference.md](docs/api_reference.md)
- **Troubleshooting:** [docs/troubleshooting.md](docs/troubleshooting.md)

---

**System is ready for comprehensive manual testing!** 🚀
