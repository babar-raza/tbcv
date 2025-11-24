# Project Organization - Execution Checklist

**Reference**: See [PROJECT_ORGANIZATION_PLAN.md](PROJECT_ORGANIZATION_PLAN.md) for detailed rationale.

---

## Pre-Execution Setup

```bash
# 1. Create backup branch
git checkout -b backup/pre-organization-2025-11-24
git push origin backup/pre-organization-2025-11-24

# 2. Return to main branch
git checkout main

# 3. Ensure clean working directory
git status  # Should show only staged changes from git status

# 4. Run baseline tests
pytest
python -m cli.main --help
python main.py --mode api &  # Start server
curl http://localhost:8080/health/live  # Should return success
# Stop server (Ctrl+C or taskkill)
```

---

## Phase 1: Documentation Consolidation

```bash
# Create new directories
mkdir -p docs/implementation
mkdir -p docs/operations

# Move implementation summaries
git mv ENHANCEMENT_COMPARISON_FEATURE_SUMMARY.md docs/implementation/
git mv IMPLEMENTATION_SUMMARY.md docs/implementation/
git mv LANGUAGE_DETECTION_IMPLEMENTATION.md docs/implementation/
git mv STUB_FIXES_COMPLETE.md docs/implementation/
git mv UI_FILE_UPLOAD_IMPLEMENTATION_SUMMARY.md docs/implementation/
git mv WEBSOCKET_403_INVESTIGATION.md docs/implementation/
git mv WEBSOCKET_FIX_COMPLETE.md docs/implementation/

# Move operational guides
git mv MANUAL_TESTING_GUIDE.md docs/operations/
git mv SERVER_STATUS.md docs/operations/
git mv SYSTEM_TIDINESS_REPORT.md docs/operations/

# Create index files
# (See Phase 1 - Manual Creation Required below)

# Commit
git add -A
git commit -m "docs: Reorganize documentation into implementation/ and operations/ subdirectories"

# Test
pytest tests/test_*.py -k "not live"  # Quick sanity check
```

### Manual Creation Required

Create `docs/implementation/README.md`:
```markdown
# Implementation Documentation

Historical implementation summaries and technical investigations.

## Feature Implementations
- [Enhancement Comparison Feature](ENHANCEMENT_COMPARISON_FEATURE_SUMMARY.md)
- [Implementation Summary](IMPLEMENTATION_SUMMARY.md)
- [Language Detection](LANGUAGE_DETECTION_IMPLEMENTATION.md)
- [UI File Upload](UI_FILE_UPLOAD_IMPLEMENTATION_SUMMARY.md)

## Technical Investigations
- [WebSocket 403 Investigation](WEBSOCKET_403_INVESTIGATION.md)
- [WebSocket Fix Complete](WEBSOCKET_FIX_COMPLETE.md)
- [Stub Fixes Complete](STUB_FIXES_COMPLETE.md)
```

Create `docs/operations/README.md`:
```markdown
# Operations Documentation

Operational guides and system status reports.

## Guides
- [Manual Testing Guide](MANUAL_TESTING_GUIDE.md)

## Status Reports
- [Server Status](SERVER_STATUS.md)
- [System Tidiness Report](SYSTEM_TIDINESS_REPORT.md)
```

---

## Phase 2: Scripts Organization

```bash
# Create directories
mkdir -p scripts/utilities
mkdir -p tests/manual
mkdir -p tests/manual/fixtures

# Move utility scripts to scripts/utilities/
git mv approve_recommendations.py scripts/utilities/
git mv check_all_recs.py scripts/utilities/
git mv check_rec_status.py scripts/utilities/
git mv check_db.py scripts/utilities/
git mv check_schema.py scripts/utilities/

# Move test scripts to tests/manual/
git mv test_enhancement.py tests/manual/
git mv test_language_demo.py tests/manual/
git mv test_minimal_fastapi_ws.py tests/manual/
git mv test_simple_ws.py tests/manual/
git mv test_websocket_connection.py tests/manual/

# Move test fixtures
git mv test_enhancement_article.md tests/manual/fixtures/
git mv test_workflow_2.md tests/manual/fixtures/
git mv test_workflow_article.md tests/manual/fixtures/

# Move E2E test
git mv run_full_e2e_test.py tests/

# Archive obsolete script
git mv delete_redundant_docs.sh archive/scripts/ 2>/dev/null || echo "Already moved or doesn't exist"

# Commit
git add -A
git commit -m "refactor: Reorganize scripts into scripts/utilities/ and tests/manual/"

# Test that imports still work
python scripts/utilities/check_db.py
python tests/manual/test_enhancement.py --help 2>/dev/null || echo "Expected - may need updates"
```

### Manual Creation Required

Create `scripts/utilities/README.md`:
```markdown
# Utility Scripts

Operational utility scripts for database management and system checks.

## Database Utilities
- `check_db.py` - Check database connectivity and schema
- `check_schema.py` - Validate database schema

## Recommendation Utilities
- `approve_recommendations.py` - Bulk approve recommendations
- `check_all_recs.py` - Check all recommendations status
- `check_rec_status.py` - Check specific recommendation status

## Usage

All scripts should be run from the project root:

\`\`\`bash
python scripts/utilities/check_db.py
python scripts/utilities/approve_recommendations.py --help
\`\`\`
```

Create `tests/manual/README.md`:
```markdown
# Manual Testing Scripts

Ad-hoc testing scripts for development and debugging.

## Test Scripts
- `test_enhancement.py` - Test enhancement functionality
- `test_language_demo.py` - Demo language detection
- `test_websocket_connection.py` - Test WebSocket connectivity
- `test_minimal_fastapi_ws.py` - Minimal WebSocket test
- `test_simple_ws.py` - Simple WebSocket test

## Test Fixtures
Located in `fixtures/` subdirectory.

## Usage

Run from project root:

\`\`\`bash
python tests/manual/test_enhancement.py
python tests/manual/test_language_demo.py
\`\`\`
```

---

## Phase 3: Data and Runtime Files

### 3.1 Move Database (CRITICAL - Test Thoroughly!)

```bash
# BEFORE: Check current database location
ls -lh tbcv.db
sqlite3 tbcv.db "SELECT COUNT(*) FROM validations;"  # Note the count

# Move database
git mv tbcv.db data/tbcv.db

# Update database path in code (Manual - see below)

# AFTER: Test database still works
sqlite3 data/tbcv.db "SELECT COUNT(*) FROM validations;"  # Should match count above

# Test application
python main.py --mode api &
sleep 5
curl http://localhost:8080/health/live
curl http://localhost:8080/api/validations | head -20
# Stop server

# Commit
git add -A
git commit -m "refactor: Move database to data/ directory"
```

### Manual Code Updates Required

**Check and update if needed**:

1. `core/config.py`:
   ```python
   # Search for database path configuration
   # Likely: DB_PATH or DATABASE_URL
   # Update to: "data/tbcv.db"
   ```

2. `core/database.py`:
   ```python
   # Search for hardcoded "tbcv.db"
   # Update any occurrences to "data/tbcv.db"
   ```

3. Search all files:
   ```bash
   grep -r "tbcv\.db" --include="*.py" .
   # Update any hardcoded references found
   ```

### 3.2 Handle Log Files

```bash
# Check if logs are needed
ls -lh srv.log server_output.log 2>/dev/null || echo "Log files not present"

# Option A: Delete if not needed (logs regenerate)
git rm srv.log server_output.log 2>/dev/null || echo "Already gone"

# Option B: Move to data/logs/
mkdir -p data/logs
git mv srv.log data/logs/ 2>/dev/null || echo "File doesn't exist"
git mv server_output.log data/logs/ 2>/dev/null || echo "File doesn't exist"

# Handle data files (likely temporary/generated)
# Option: Delete (can regenerate)
rm validation_analysis.txt 2>/dev/null || echo "Already gone"
rm validation_result.json 2>/dev/null || echo "Already gone"

# Commit
git add -A
git commit -m "chore: Clean up log and temporary data files"
```

### 3.3 Update .gitignore

```bash
# Edit .gitignore and add the following lines at the end:
cat >> .gitignore << 'EOF'

# Additional runtime files
/srv.log
/server_output.log
/validation_*.txt
/validation_*.json
/*.db
/*.sqlite
/*.sqlite3

# Test artifacts at root
/test_*.md
/test_*.py
!tests/
!main.py

# Utility scripts that may be temporarily created
/check_*.py
/approve_*.py
!scripts/
EOF

# Commit
git add .gitignore
git commit -m "chore: Update .gitignore to prevent runtime file clutter"
```

---

## Phase 4: Archive Management

```bash
# Check if root archive/ exists
ls -la archive/ 2>/dev/null || echo "No root archive directory"

# If exists and has unique content, merge with docs/archive/ or reports/archive/
# Review content first:
ls -R archive/ 2>/dev/null

# If redundant, can delete:
# git rm -r archive/
# git commit -m "chore: Remove redundant archive directory"

# Otherwise, merge:
# cp -r archive/* docs/archive/ 2>/dev/null || echo "Skipping"
# git rm -r archive/
# git add docs/archive/
# git commit -m "chore: Consolidate archives into docs/archive/"
```

---

## Phase 5: Root Directory Verification

```bash
# List current root files
ls -1 | wc -l  # Should be significantly reduced

# Verify essential files present
ls README.md CHANGELOG.md requirements.txt main.py .gitignore

# List all root files for review
ls -la | grep -v "^d" | grep -v "^\."

# Expected root structure:
# - README.md
# - CHANGELOG.md
# - requirements.txt
# - pyproject.toml
# - pytest.ini
# - Dockerfile
# - docker-compose.yml
# - tbcv.service
# - main.py
# - __init__.py
# - __main__.py
# - VERSION.txt
# - install.sh
# - setup_ollama.bat
# - restart_server.bat
# - .gitignore
# (and directories: agents/, api/, cli/, core/, config/, data/, docs/, etc.)
```

---

## Phase 6: Comprehensive Testing

### 6.1 Unit Tests

```bash
# Run full test suite
pytest -v

# Run specific test categories
pytest -m unit
pytest -m integration
pytest tests/test_fuzzy_logic.py
pytest tests/test_generic_validator.py
```

### 6.2 CLI Testing

```bash
# Test CLI mode
python -m cli.main --help
python -m cli.main validate-file tests/manual/fixtures/test_enhancement_article.md --family words --format text
```

### 6.3 API Testing

```bash
# Start server
python main.py --mode api --port 8080 &
SERVER_PID=$!
sleep 5

# Test health endpoint
curl http://localhost:8080/health/live

# Test API endpoints
curl http://localhost:8080/
curl http://localhost:8080/api/validations
curl http://localhost:8080/agents

# Stop server
kill $SERVER_PID 2>/dev/null || taskkill /PID $SERVER_PID /F
```

### 6.4 Database Testing

```bash
# Test database operations
python -c "from core.database import db_manager; db_manager.initialize_database()"
python scripts/utilities/check_db.py
python scripts/utilities/check_schema.py
```

### 6.5 E2E Testing

```bash
# Run E2E test
python tests/run_full_e2e_test.py
```

---

## Phase 7: Documentation Updates

### Update Main README.md

Update the "Project Structure" section in README.md to reflect new organization:

```markdown
## Project Structure

```
tbcv/
├── agents/              # Multi-agent system (8 agents)
├── api/                # FastAPI server
├── cli/                # Command-line interface
├── core/               # Core infrastructure
├── config/             # Configuration files
├── data/               # Runtime data (database, logs, cache)
│   ├── logs/          # Application logs
│   ├── cache/         # Two-level cache
│   └── tbcv.db        # SQLite database
├── docs/               # Documentation
│   ├── implementation/ # Technical implementation summaries
│   ├── operations/     # Operational guides
│   └── archive/        # Historical documentation
├── migrations/         # Database migrations
├── prompts/            # LLM prompts
├── reports/            # Analysis reports and session summaries
│   ├── sessions/      # Session-specific reports
│   └── archive/        # Historical reports
├── rules/              # Validation rules
├── scripts/            # Utility scripts
│   ├── maintenance/   # System maintenance
│   ├── testing/       # Test runners
│   ├── utilities/     # Database and system utilities
│   ├── systemd/       # Service management
│   └── windows/       # Windows-specific scripts
├── svc/                # Background services
├── templates/          # Jinja2 templates for web UI
├── tests/              # Test suite
│   ├── manual/        # Ad-hoc manual tests
│   │   └── fixtures/  # Test data files
│   ├── agents/        # Agent-specific tests
│   ├── api/           # API tests
│   ├── cli/           # CLI tests
│   └── core/          # Core infrastructure tests
├── tools/              # Development tools
├── truth/              # Plugin truth data
├── main.py             # Application entry point
├── requirements.txt    # Python dependencies
└── README.md           # This file
```
```

### Update Other Documentation

```bash
# Update file paths in documentation
grep -r "tbcv\.db" docs/*.md
grep -r "test_.*\.md" docs/*.md
grep -r "check_.*\.py" docs/*.md

# Update docs/architecture.md, docs/development.md, docs/testing.md
# (Manual review and updates required)
```

---

## Final Verification Checklist

- [ ] All tests pass: `pytest`
- [ ] CLI works: `python -m cli.main --help`
- [ ] API starts: `python main.py --mode api`
- [ ] Health check passes: `curl http://localhost:8080/health/live`
- [ ] Database operations work
- [ ] WebSocket connections work
- [ ] Dashboard loads successfully
- [ ] No broken imports in Python files
- [ ] No broken links in documentation
- [ ] .gitignore prevents log/data file commits
- [ ] Root directory has ≤20 files (excluding directories)
- [ ] Git history preserved (check with `git log --follow`)

---

## Rollback Procedure

If anything breaks:

```bash
# Option 1: Reset to last commit
git reset --hard HEAD~1

# Option 2: Full rollback to backup
git checkout backup/pre-organization-2025-11-24

# Option 3: Selective file rollback
git checkout HEAD~1 -- path/to/file

# Option 4: Revert specific commit
git revert <commit-hash>
```

---

## Post-Execution

```bash
# Push changes to remote
git push origin main

# Tag the organization milestone
git tag -a v2.1.0-organized -m "Project organization complete"
git push origin v2.1.0-organized

# Clean up backup branch (after confirming everything works)
# git branch -D backup/pre-organization-2025-11-24
# git push origin --delete backup/pre-organization-2025-11-24
```

---

## Notes

- Always run commands from project root
- Test after each phase before committing
- Use `git mv` instead of `mv` to preserve git history
- Keep backup branch until organization is fully validated
- Update any CI/CD pipelines with new paths
- Notify team members of new structure

---

**Estimated Time**: 3-4 hours including testing
**Risk Level**: Medium (database move requires careful testing)
**Reversibility**: High (git history preserved, backup branch created)
