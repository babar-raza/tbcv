# TBCV Frequently Asked Questions
> Title: FAQ
> Version: auto  
> Source: System documentation @ 2025-11-03T08:43:00Z

## General Questions

### What is TBCV?
TBCV (Truth-Based Content Validation) is an intelligent content processing system that validates, analyzes, and enhances technical documentation. It specializes in detecting Aspose product usage patterns and ensuring documentation quality through multi-agent processing.

### What types of content can TBCV process?
TBCV processes:
- Markdown documentation files (.md)
- Code samples (C#, Python, JavaScript, Java, C++)
- YAML configuration files
- External code from GitHub repositories and gists
- JSON data structures

### How does TBCV detect plugins?
TBCV uses a sophisticated multi-algorithm approach:
1. Truth tables define plugin patterns (`truth/*.json`)
2. Fuzzy matching algorithms (Levenshtein, Jaro-Winkler) detect variations
3. Context windows analyze surrounding content
4. Combination rules identify multi-plugin usage
5. Confidence scoring ranks detection accuracy

## Installation & Setup

### What are the system requirements?
- **OS**: Windows 10/11
- **Python**: 3.12.x or higher
- **Memory**: Minimum 4GB RAM recommended
- **Storage**: 500MB for application + data
- **Network**: Required only for external code fetching

### How do I install TBCV?
```bash
# Clone repository
git clone <repository_url>

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -m tbcv init

# Run server
python -m uvicorn api.server:app --reload
```

### Where are configuration files located?
- Main config: `config/settings.yaml`
- Plugin patterns: `truth/*.json`
- Validation rules: `rules/*.yaml`
- Database: `tbcv.db`

## Usage Questions

### How do I validate a single file?
**Via CLI:**
```bash
python -m cli.main validate path/to/file.md
```

**Via API:**
```bash
curl -X POST http://localhost:8000/validate/content \
  -H "Content-Type: application/json" \
  -d '{"content": "...", "filename": "example.md"}'
```

### How do I process multiple files?
Use the batch endpoint:
```bash
python -m cli.main batch input_dir/ output_dir/
```

Or via API:
```bash
curl -X POST http://localhost:8000/validate/batch \
  -F "files=@file1.md" \
  -F "files=@file2.md"
```

### How do I enhance content with plugin links?
```bash
python -m cli.main enhance file.md --output enhanced_file.md
```

The enhancer will:
- Add links on first plugin occurrence
- Insert informational text
- Fix formatting issues

### Can I customize validation rules?
Yes, edit `rules/validation_rules.yaml`:
```yaml
rules:
  - id: custom_rule
    severity: warning
    pattern: "pattern_regex"
    message: "Custom validation message"
```

## Performance & Scaling

### How does TBCV handle large files?
- Streaming parser for files >10MB
- Chunked processing for batch operations
- Async I/O for concurrent file handling
- Two-level caching reduces redundant processing

### What are the performance characteristics?
- Single file validation: ~100-500ms
- Batch processing: ~10-50 files/second
- Plugin detection: O(log n) with B-tree indexing
- Cache hit ratio: typically >80%

### How can I improve performance?
1. Enable caching in `config/settings.yaml`
2. Increase worker count for batch processing
3. Use SSD storage for database
4. Allocate more memory for L1 cache
5. Run background tasks with separate workers

## Troubleshooting

### Why are plugins not being detected?
Check:
1. Truth tables loaded correctly (`truth/*.json`)
2. Confidence threshold in config (default 0.7)
3. Plugin patterns are up-to-date
4. Context window size is appropriate

### How do I debug validation issues?
Enable debug logging:
```python
# In config/settings.yaml
logging:
  level: DEBUG
  file: debug.log
```

Check logs for:
- Pattern matching attempts
- Confidence scores
- Rule evaluation results

### What if external code fetching fails?
TBCV will:
1. Log the error with details
2. Continue processing other content
3. Mark external code as unavailable
4. Provide partial results

To debug:
- Check network connectivity
- Verify GitHub token if using private repos
- Review rate limits

### How do I handle database corruption?
```bash
# Backup current database
cp tbcv.db tbcv.db.backup

# Rebuild database
python -m tbcv rebuild-db

# Restore workflow states if needed
python -m tbcv import-backup tbcv.db.backup
```

## API Questions

### What authentication is required?
Current version uses optional API key authentication:
```python
headers = {"X-API-Key": "your-api-key"}
```

Configure in `config/settings.yaml`:
```yaml
api:
  require_auth: true
  api_key: "your-secure-key"
```

### What are the rate limits?
Default limits:
- 100 requests/minute per IP
- 10 concurrent validations
- 1000 batch items per request

Configurable in `config/settings.yaml`

### How do I monitor API health?
Health endpoint: `GET /health`
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "cache": "active",
  "agents": {
    "truth_manager": "ready",
    "fuzzy_detector": "ready",
    ...
  }
}
```

## Data Management

### Where is data stored?
- **Database**: `tbcv.db` (SQLite)
- **Cache**: Memory + `cache.db`
- **Logs**: `logs/` directory
- **Exports**: `exports/` directory

### How do I backup TBCV data?
```bash
# Full backup
python -m tbcv backup --output backup.tar.gz

# Database only
cp tbcv.db backups/tbcv_$(date +%Y%m%d).db

# Configuration backup
tar -czf config_backup.tar.gz config/ truth/ rules/
```

### Can I export validation results?
Yes, multiple formats available:
```bash
# CSV export
curl http://localhost:8000/export/csv?workflow_id=xxx

# JSON export  
curl http://localhost:8000/export/json?workflow_id=xxx

# Custom report
curl -X POST http://localhost:8000/report/generate \
  -d '{"format": "pdf", "workflow_ids": ["id1", "id2"]}'
```

## Development Questions

### How do I add a new agent?
1. Create agent class extending `BaseAgent` (`agents/base.py`)
2. Implement required methods
3. Register in `agents/__init__.py`
4. Add to orchestrator workflow
5. Write tests in `tests/`

### How do I extend plugin detection?
1. Add patterns to `truth/[plugin_family].json`
2. Define combination rules if needed
3. Update confidence thresholds
4. Test with sample content

### Where do I contribute?
- Fork repository
- Create feature branch
- Add tests for new functionality
- Update documentation
- Submit pull request

---

For detailed technical information, see:
- [Architecture](architecture.md) - System design
- [Components](components.md) - Module details
- [Runbook](runbook.md) - Operational procedures
- [Operations](operations.md) - Maintenance guide
