# TBCV Setup Guide

## Quick Start (5 minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Validate Setup
```bash
python startup_check.py
```

### 3. Initialize Database
```bash
python -c "from core.database import db_manager; db_manager.initialize_database()"
```

### 4. Start Server
```bash
python main.py --mode api --port 8080
```

### 5. Open Dashboard
Visit: http://localhost:8080/dashboard

## What's Fixed in This Version

### Critical Bugs Fixed ✅
1. **Enhancement Button Error** - Fixed undefined `enhancements` variable
2. **Context Loading** - Completed stub implementations
3. **Database Indexes** - Added missing indexes for performance
4. **Path Validation** - Added security checks for file operations

### New Features ✅
1. **Path Validator** - Prevents directory traversal attacks
2. **Startup Validation** - Checks system health before starting
3. **Enhanced Configuration** - More configurable settings
4. **Better Error Handling** - Comprehensive error messages

### Documentation Updates ✅
1. Fixed agent count (7 → 6)
2. Added setup guide
3. Added security notes
4. Enhanced inline documentation

## System Architecture

### 6 Specialized Agents
1. **Truth Manager** - Loads plugin/entity definitions
2. **Fuzzy Detector** - Detects entities using pattern matching
3. **Content Validator** - Validates content quality
4. **Code Analyzer** - Analyzes code patterns
5. **Content Enhancer** - Enhances content automatically
6. **Orchestrator** - Coordinates workflows

### Core Components
- **FastAPI Server** - REST API and web dashboard
- **SQLite Database** - Validation results and workflows
- **MCP Server** - JSON-RPC interface
- **Two-Level Cache** - Performance optimization

## Configuration

Edit `config/main.yaml` to customize:
- Server host and port
- Database settings
- Agent behavior
- Security settings
- Logging configuration

## Security Notes

### File Path Validation
All file operations now validate paths to prevent:
- Directory traversal attacks (..)
- Access to system directories (/etc, C:\Windows)
- Writing outside allowed directories

### API Security (Optional)
To enable API key authentication:
1. Set `security.enable_api_keys: true` in config/main.yaml
2. Pass API key in `X-API-Key` header

## Testing

### Run All Tests
```bash
pytest tests/
```

### Run Smoke Tests
```bash
python -m tbcv.cli check-agents
```

### Test Validation
```bash
python -m tbcv.cli validate-file content/example.md --family words
```

## Troubleshooting

### Database Locked Error
```bash
# Reset database
rm tbcv.db
python -c "from core.database import db_manager; db_manager.initialize_database()"
```

### Enhancement Not Working
1. Check Ollama is running: `ollama list`
2. Verify model exists: `ollama pull llama2`
3. Check logs: `data/logs/tbcv.log`

### Agent Not Available
```bash
python -m tbcv.cli check-agents --verbose
```

## API Endpoints

### Validation
- `POST /api/validate/content` - Validate content
- `POST /api/validate/file` - Validate file
- `GET /api/validations` - List validations

### Enhancement
- `POST /api/enhance/{id}` - Enhance validation
- `POST /api/validations/bulk/enhance` - Bulk enhance

### Workflows
- `POST /api/approve/{id}` - Approve validation
- `POST /api/reject/{id}` - Reject validation

## Dashboard Pages

- `/dashboard` - Main dashboard
- `/dashboard/workflows` - Workflow monitor
- `/dashboard/agents` - Agent status
- `/dashboard/logs` - Audit logs

## Next Steps

1. **Test the System**
   - Run startup validation
   - Try a sample validation
   - Test enhancement feature

2. **Customize Configuration**
   - Edit config/main.yaml
   - Set appropriate security settings
   - Configure Ollama if using LLM features

3. **Add Your Families**
   - Create truth/your-family.json
   - Create rules/your-family.json
   - Test with sample content

## Support

For issues or questions:
1. Check the logs: `data/logs/tbcv.log`
2. Run diagnostics: `python diagnose.py`
3. Review the analysis docs in this package
