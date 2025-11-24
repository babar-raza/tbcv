# Project Organization - Quick Reference Card

**One-page guide for executing the project organization.**

---

## Pre-Flight Check

```bash
# 1. Backup
git checkout -b backup/pre-organization-2025-11-24
git checkout main

# 2. Baseline test
pytest && python main.py --mode api & sleep 3 && curl http://localhost:8080/health/live
```

---

## Execution Commands (Copy & Paste)

### Phase 1: Documentation (5 min)
```bash
mkdir -p docs/implementation docs/operations
git mv ENHANCEMENT_COMPARISON_FEATURE_SUMMARY.md IMPLEMENTATION_SUMMARY.md LANGUAGE_DETECTION_IMPLEMENTATION.md STUB_FIXES_COMPLETE.md UI_FILE_UPLOAD_IMPLEMENTATION_SUMMARY.md WEBSOCKET_403_INVESTIGATION.md WEBSOCKET_FIX_COMPLETE.md docs/implementation/
git mv MANUAL_TESTING_GUIDE.md SERVER_STATUS.md SYSTEM_TIDINESS_REPORT.md docs/operations/
git commit -m "docs: Reorganize into implementation/ and operations/"
```

### Phase 2: Scripts (10 min)
```bash
mkdir -p scripts/utilities tests/manual/fixtures
git mv approve_recommendations.py check_all_recs.py check_rec_status.py check_db.py check_schema.py scripts/utilities/
git mv test_enhancement.py test_language_demo.py test_minimal_fastapi_ws.py test_simple_ws.py test_websocket_connection.py tests/manual/
git mv test_enhancement_article.md test_workflow_2.md test_workflow_article.md tests/manual/fixtures/
git mv run_full_e2e_test.py tests/
git commit -m "refactor: Organize scripts and tests"
```

### Phase 3: Database (20 min - TEST CAREFULLY)
```bash
# Check database
sqlite3 tbcv.db "SELECT COUNT(*) FROM validations;"

# Move
git mv tbcv.db data/

# UPDATE CODE: Search for "tbcv.db" in core/config.py and core/database.py
# Change to "data/tbcv.db"

# Test
python main.py --mode api & sleep 3 && curl http://localhost:8080/api/validations
pytest

git commit -m "refactor: Move database to data/ directory"
```

### Phase 4: Cleanup (5 min)
```bash
# Remove temporary files
rm -f srv.log server_output.log validation_*.txt validation_*.json 2>/dev/null

# Update .gitignore
cat >> .gitignore << 'EOF'

# Runtime files at root
/srv.log
/server_output.log
/validation_*.txt
/validation_*.json
/*.db
/*.sqlite
/test_*.md
/test_*.py
!tests/
!main.py
EOF

git add .gitignore
git commit -m "chore: Update .gitignore"
```

---

## Critical Tests

```bash
# After each phase:
pytest -x                                    # Stop on first failure
python -m cli.main --help                    # CLI works
python main.py --mode api & sleep 3          # API starts
curl http://localhost:8080/health/live       # Health check
```

---

## Rollback

```bash
# If anything breaks:
git reset --hard HEAD~1                      # Undo last commit
# OR
git checkout backup/pre-organization-2025-11-24  # Full rollback
```

---

## File Placement Rules (Future)

| File Type | Location |
|-----------|----------|
| Documentation | `docs/` (with subdirectories) |
| Utility scripts | `scripts/utilities/` |
| Test scripts | `tests/` or `tests/manual/` |
| Test data | `tests/fixtures/` or `tests/manual/fixtures/` |
| Logs | `data/logs/` (ignored by git) |
| Database | `data/` |
| Reports | `reports/` |
| Temporary files | `data/temp/` (ignored by git) |

---

## Success Checklist

- [ ] Root has ≤15 files
- [ ] `pytest` passes
- [ ] `python main.py --mode api` starts
- [ ] `curl http://localhost:8080/health/live` succeeds
- [ ] Database operations work
- [ ] No import errors

---

## Files That Should Stay at Root

✅ README.md, CHANGELOG.md, LICENSE, requirements.txt, pyproject.toml
✅ pytest.ini, Dockerfile, docker-compose.yml, .gitignore
✅ main.py, __init__.py, __main__.py, VERSION.txt
✅ install.sh, setup_ollama.bat, restart_server.bat, tbcv.service

❌ Everything else should be in subdirectories

---

## Help

- **Detailed Plan**: [plans/PROJECT_ORGANIZATION_PLAN.md](PROJECT_ORGANIZATION_PLAN.md)
- **Step-by-Step**: [plans/EXECUTION_CHECKLIST.md](EXECUTION_CHECKLIST.md)
- **Visual Guide**: [plans/ORGANIZATION_SUMMARY.md](ORGANIZATION_SUMMARY.md)

---

**Total Time**: ~45 minutes (excluding testing)
**Difficulty**: Medium
**Reversibility**: High (backup + git)
