# Project Organization Plan for GitHub/GitLab Deployment

**Goal**: Transform the TBCV repository into a professional, well-organized structure suitable for organizational GitHub/GitLab deployment without breaking any functionality.

**Status**: Planning Phase
**Created**: 2025-11-24
**Risk Level**: Medium (requires careful migration and testing)

---

## Executive Summary

The project currently has **significant organizational debt** with many stray files at the root level. This plan reorganizes the repository into a clean, professional structure while maintaining 100% backward compatibility.

### Current State Issues

1. **14 markdown documentation files** scattered at root
2. **14+ utility Python scripts** at root that belong in scripts/ or tests/
3. **Log and data files** at root that should be in data/ or ignored
4. **Database file (tbcv.db)** at root instead of data/
5. **Test markdown files** at root for ad-hoc testing
6. **Redundant/outdated documentation** not archived

### Target State

- Clean root directory with only essential files (README, CHANGELOG, requirements, config, main.py)
- All documentation properly organized in docs/
- All scripts categorized in scripts/ subdirectories
- All reports archived or consolidated
- All runtime data in data/ directory
- Updated .gitignore to prevent future clutter

---

## Phase 1: Documentation Consolidation

### 1.1 Move Implementation Summaries to docs/implementation/

**Action**: Create `docs/implementation/` directory and move technical summaries

**Files to Move**:
```
ROOT → docs/implementation/
├── ENHANCEMENT_COMPARISON_FEATURE_SUMMARY.md
├── IMPLEMENTATION_SUMMARY.md
├── LANGUAGE_DETECTION_IMPLEMENTATION.md
├── STUB_FIXES_COMPLETE.md
├── UI_FILE_UPLOAD_IMPLEMENTATION_SUMMARY.md
├── WEBSOCKET_403_INVESTIGATION.md
└── WEBSOCKET_FIX_COMPLETE.md
```

**Rationale**: These are technical implementation documents that provide context for developers but shouldn't clutter the root.

### 1.2 Move Operational Documents to docs/operations/

**Action**: Create `docs/operations/` directory for operational guides

**Files to Move**:
```
ROOT → docs/operations/
├── MANUAL_TESTING_GUIDE.md
├── SERVER_STATUS.md
└── SYSTEM_TIDINESS_REPORT.md
```

**Rationale**: Operational guides should be separate from architectural/API documentation.

### 1.3 Update Documentation Index

**Action**: Update README.md to add new documentation sections

**Add to README**:
```markdown
### Implementation History
- [Implementation Summaries](docs/implementation/) - Feature implementation details
- [Operations Guides](docs/operations/) - Manual testing and server operations
```

---

## Phase 2: Scripts Organization

### 2.1 Move Utility Scripts to scripts/utilities/

**Files to Move**:
```
ROOT → scripts/utilities/
├── approve_recommendations.py
├── check_all_recs.py
├── check_rec_status.py
├── check_db.py
├── check_schema.py
└── delete_redundant_docs.sh (archive - likely obsolete)
```

**Rationale**: These are operational utilities, not core application code.

### 2.2 Move Test Scripts to tests/manual/ or tests/integration/

**Files to Move**:
```
ROOT → tests/manual/
├── test_enhancement.py
├── test_language_demo.py
├── test_minimal_fastapi_ws.py
├── test_simple_ws.py
└── test_websocket_connection.py

ROOT → tests/manual/fixtures/
├── test_enhancement_article.md
├── test_workflow_2.md
└── test_workflow_article.md
```

**Rationale**: Ad-hoc test scripts should be organized with the test suite.

### 2.3 Move E2E Test to tests/

**Files to Move**:
```
ROOT → tests/
└── run_full_e2e_test.py
```

**Rationale**: Major test scripts should be in tests/ directory.

---

## Phase 3: Data and Runtime Files

### 3.1 Move Database to data/

**Action**: Move tbcv.db to data/ and update all references

**Files to Move**:
```
ROOT → data/
└── tbcv.db
```

**Code Changes Required**:
- Update `core/database.py` - check for hardcoded database path
- Update `core/config.py` - ensure DB_PATH points to data/tbcv.db
- Update documentation mentioning database location

**Testing Required**: ⚠️ High Priority
- Test database connectivity after move
- Test all database operations (read, write, migrations)
- Test CLI and API modes

### 3.2 Move/Archive Log Files

**Action**: Move logs to data/logs/ or delete if redundant

**Files to Handle**:
```
ROOT → data/logs/ (or DELETE if redundant)
├── srv.log
└── server_output.log

ROOT → data/ (or DELETE if temporary)
├── validation_analysis.txt
└── validation_result.json
```

**Rationale**: Runtime logs and data should not be committed to git.

### 3.3 Update .gitignore

**Action**: Add patterns to prevent future log/data file clutter

**Add to .gitignore**:
```gitignore
# Runtime data files at root (should be in data/)
/srv.log
/server_output.log
/*.db
/*.sqlite
/*.sqlite3
/validation_*.json
/validation_*.txt

# Test fixtures at root (should be in tests/)
/test_*.md
/test_*.py
!main.py
!setup.py

# Utility scripts that may be generated
check_*.py
approve_*.py
```

---

## Phase 4: Archive Management

### 4.1 Review and Clean archive/ Directory

**Action**: Decide if archive/ at root should be moved or deleted

**Options**:
1. **Move to docs/archive/** - If contains useful historical docs
2. **Delete entirely** - If redundant with docs/archive/ and reports/archive/
3. **Merge with existing archives** - Consolidate into one location

**Decision Criteria**:
- Check for unique content not in docs/archive/ or reports/archive/
- Assess value for new developers
- Consider age and relevance

### 4.2 Clean reports/ Directory

**Action**: Archive or consolidate old session reports

**Current State**: reports/ has 30+ report files including many session summaries

**Strategy**:
- Keep latest summary reports at reports/ root
- Move all session-specific reports to reports/sessions/
- Move all completion reports to reports/completions/
- Create reports/README.md index

---

## Phase 5: Root Directory Cleanup

### 5.1 Final Root Directory Structure

**Files That SHOULD Stay at Root**:
```
tbcv/
├── README.md                    # Main documentation entry point
├── CHANGELOG.md                 # Version history
├── LICENSE                      # License file (add if missing)
├── .gitignore                   # Git ignore rules
├── requirements.txt             # Python dependencies
├── pyproject.toml              # Python project metadata
├── pytest.ini                  # Test configuration
├── setup.py                    # Package setup (if needed)
├── Dockerfile                  # Container definition
├── docker-compose.yml          # Container orchestration
├── tbcv.service               # Systemd service file
├── main.py                     # Application entry point
├── __init__.py                 # Package initialization
├── __main__.py                 # Direct execution support
├── VERSION.txt                 # Version tracking
├── install.sh                  # Quick install script
├── setup_ollama.bat           # Ollama setup for Windows
├── restart_server.bat         # Windows server restart
└── plans/                     # Project planning (this document)
```

**Directories**:
```
├── agents/                     # Core agents
├── api/                        # API server
├── cli/                        # CLI interface
├── core/                       # Core infrastructure
├── config/                     # Configuration files
├── data/                       # Runtime data (logs, db, cache)
├── docs/                       # All documentation
│   ├── implementation/        # NEW: Technical summaries
│   ├── operations/            # NEW: Operational guides
│   └── archive/               # Historical docs
├── migrations/                 # Database migrations
├── prompts/                    # LLM prompts
├── reports/                    # Analysis reports
│   ├── sessions/              # Session-specific
│   └── archive/               # Historical reports
├── rules/                      # Validation rules
├── scripts/                    # All scripts organized by type
│   ├── maintenance/           # System maintenance
│   ├── testing/               # Test runners
│   ├── utilities/             # NEW: Utility scripts
│   └── systemd/               # Service management
├── svc/                        # Background services
├── templates/                  # Jinja2 templates
├── tests/                      # Test suite
│   ├── manual/                # NEW: Ad-hoc tests
│   └── fixtures/              # Test data
├── tools/                      # Development tools
└── truth/                      # Plugin truth data
```

---

## Phase 6: Verification and Testing

### 6.1 Pre-Migration Checklist

- [ ] Commit all current changes
- [ ] Create backup branch: `git checkout -b backup/pre-organization`
- [ ] Document current working state
- [ ] Run full test suite: `pytest`
- [ ] Test CLI mode: `python -m cli.main --help`
- [ ] Test API mode: `python main.py --mode api` + health check
- [ ] Note current database location and size

### 6.2 Migration Execution Checklist

For each phase:
- [ ] Create new directories if needed
- [ ] Move files (use `git mv` to preserve history)
- [ ] Update import statements in code
- [ ] Update references in documentation
- [ ] Test affected functionality
- [ ] Commit changes with descriptive message

### 6.3 Post-Migration Testing

**Critical Tests** (MUST PASS):
- [ ] `pytest` - Full test suite passes
- [ ] Database connectivity works
- [ ] CLI validate-file works: `python -m cli.main validate-file <test.md>`
- [ ] API server starts: `python main.py --mode api`
- [ ] API health check: `curl http://localhost:8080/health/live`
- [ ] Dashboard loads: `http://localhost:8080/`
- [ ] WebSocket connection works
- [ ] Database operations (create, read, update, delete)
- [ ] File uploads work
- [ ] Recommendations workflow works

**Regression Tests**:
- [ ] Run E2E test: `python tests/run_full_e2e_test.py`
- [ ] Test all CLI commands
- [ ] Test all API endpoints
- [ ] Check MCP server integration
- [ ] Verify Ollama integration (if configured)

---

## Phase 7: Documentation Updates

### 7.1 Update All Documentation

**Files to Update**:
- [ ] README.md - Update file paths and structure
- [ ] docs/architecture.md - Update directory structure
- [ ] docs/development.md - Update development setup
- [ ] docs/testing.md - Update test execution paths
- [ ] docs/deployment.md - Update deployment instructions
- [ ] docs/troubleshooting.md - Update file paths

### 7.2 Create New Documentation

**New Docs to Create**:
- [ ] docs/implementation/README.md - Index of implementation docs
- [ ] docs/operations/README.md - Index of operational guides
- [ ] scripts/utilities/README.md - Utility scripts documentation
- [ ] tests/manual/README.md - Manual testing guide

---

## Risk Mitigation

### High-Risk Changes

1. **Moving tbcv.db**
   - Risk: Database path hardcoded in multiple places
   - Mitigation: Grep for all references, update systematically
   - Rollback: Keep backup, revert via git

2. **Moving scripts with dependencies**
   - Risk: Import paths may break
   - Mitigation: Use relative imports, test each script
   - Rollback: Git revert specific commits

3. **Archive cleanup**
   - Risk: Deleting potentially important historical docs
   - Mitigation: Review all files before deletion, move to archive first
   - Rollback: Keep full backup before deletion

### Medium-Risk Changes

- Moving documentation files (low code impact)
- Reorganizing test files (isolated to tests/)
- Cleaning up logs (can be regenerated)

---

## Execution Timeline

### Estimated Effort

- **Phase 1**: 15 minutes (documentation moves)
- **Phase 2**: 30 minutes (script organization + testing)
- **Phase 3**: 45 minutes (data files + database move + testing)
- **Phase 4**: 20 minutes (archive review)
- **Phase 5**: 15 minutes (root cleanup)
- **Phase 6**: 60 minutes (comprehensive testing)
- **Phase 7**: 30 minutes (documentation updates)

**Total**: ~3.5 hours

### Recommended Approach

**Option A: Incremental (Safer)**
- Execute one phase per session
- Test thoroughly between phases
- Commit after each phase
- Lower risk, easier rollback

**Option B: Batch (Faster)**
- Execute all phases in one session
- Test comprehensively at end
- Single large commit
- Higher risk, harder to pinpoint issues

**Recommendation**: **Option A** for production-bound repositories

---

## Success Criteria

The reorganization is complete and successful when:

1. ✅ Root directory has ≤15 files (down from current 50+)
2. ✅ All tests pass (`pytest` returns 100% success)
3. ✅ API server starts and responds to health checks
4. ✅ CLI commands work without path errors
5. ✅ Database operations function correctly
6. ✅ No broken imports or module errors
7. ✅ Documentation paths all valid
8. ✅ Git history preserved (files moved with `git mv`)
9. ✅ .gitignore prevents future clutter
10. ✅ README.md accurately reflects new structure

---

## Rollback Plan

If issues arise:

1. **Immediate Rollback**: `git reset --hard HEAD~1` (last commit)
2. **Full Rollback**: `git checkout backup/pre-organization`
3. **Selective Rollback**: `git revert <commit-hash>` (specific changes)
4. **File-Level Rollback**: `git checkout HEAD~1 -- <file-path>`

**Before Starting**: Always create backup branch!

---

## Post-Organization Best Practices

### Prevent Future Clutter

1. **CI/CD Check**: Add linter to check root directory file count
2. **PR Template**: Checklist for file organization
3. **Developer Guide**: Document where new files should go
4. **Automated Cleanup**: Script to detect misplaced files

### File Placement Guidelines

**Add to docs/development.md**:
```markdown
## File Organization Guidelines

- **Root**: Only essential config, entry points, and install scripts
- **docs/**: All user-facing documentation
- **docs/implementation/**: Technical design docs, implementation summaries
- **docs/operations/**: Runbooks, manual testing guides
- **scripts/**: All utility scripts, organized by purpose
- **tests/**: All test code, including manual tests
- **data/**: Runtime data (logs, database, cache)
- **reports/**: Generated reports and analysis
```

---

## Appendix A: File-by-File Migration Map

### Documentation Files
| Current Location | New Location | Reason |
|-----------------|--------------|--------|
| `ENHANCEMENT_COMPARISON_FEATURE_SUMMARY.md` | `docs/implementation/` | Implementation detail |
| `IMPLEMENTATION_SUMMARY.md` | `docs/implementation/` | Implementation detail |
| `LANGUAGE_DETECTION_IMPLEMENTATION.md` | `docs/implementation/` | Implementation detail |
| `MANUAL_TESTING_GUIDE.md` | `docs/operations/` | Operational guide |
| `SERVER_STATUS.md` | `docs/operations/` | Operational guide |
| `STUB_FIXES_COMPLETE.md` | `docs/implementation/` | Implementation detail |
| `SYSTEM_TIDINESS_REPORT.md` | `docs/operations/` | Operational guide |
| `UI_FILE_UPLOAD_IMPLEMENTATION_SUMMARY.md` | `docs/implementation/` | Implementation detail |
| `WEBSOCKET_403_INVESTIGATION.md` | `docs/implementation/` | Implementation detail |
| `WEBSOCKET_FIX_COMPLETE.md` | `docs/implementation/` | Implementation detail |

### Python Scripts
| Current Location | New Location | Reason |
|-----------------|--------------|--------|
| `approve_recommendations.py` | `scripts/utilities/` | Utility script |
| `check_all_recs.py` | `scripts/utilities/` | Utility script |
| `check_db.py` | `scripts/utilities/` | Utility script |
| `check_rec_status.py` | `scripts/utilities/` | Utility script |
| `check_schema.py` | `scripts/utilities/` | Utility script |
| `run_full_e2e_test.py` | `tests/` | Test script |
| `test_enhancement.py` | `tests/manual/` | Manual test |
| `test_language_demo.py` | `tests/manual/` | Manual test |
| `test_minimal_fastapi_ws.py` | `tests/manual/` | Manual test |
| `test_simple_ws.py` | `tests/manual/` | Manual test |
| `test_websocket_connection.py` | `tests/manual/` | Manual test |

### Test Fixtures
| Current Location | New Location | Reason |
|-----------------|--------------|--------|
| `test_enhancement_article.md` | `tests/manual/fixtures/` | Test fixture |
| `test_workflow_2.md` | `tests/manual/fixtures/` | Test fixture |
| `test_workflow_article.md` | `tests/manual/fixtures/` | Test fixture |

### Data Files
| Current Location | Action | Reason |
|-----------------|--------|--------|
| `tbcv.db` | Move to `data/` | Runtime data |
| `srv.log` | Move to `data/logs/` or DELETE | Log file |
| `server_output.log` | Move to `data/logs/` or DELETE | Log file |
| `validation_analysis.txt` | Move to `data/` or DELETE | Runtime data |
| `validation_result.json` | Move to `data/` or DELETE | Runtime data |

### Scripts
| Current Location | Action | Reason |
|-----------------|--------|--------|
| `delete_redundant_docs.sh` | Archive or DELETE | Likely obsolete |
| `restart_server.bat` | Keep at root | Quick access |
| `setup_ollama.bat` | Keep at root | Quick access |
| `install.sh` | Keep at root | Quick access |

---

## Appendix B: Code Changes Required

### Files Requiring Import Updates

1. **core/database.py**
   ```python
   # OLD
   DB_PATH = "tbcv.db"

   # NEW
   DB_PATH = "data/tbcv.db"
   ```

2. **core/config.py**
   ```python
   # Check for any hardcoded paths:
   # - Database paths
   # - Log file paths
   # - Report output paths
   ```

3. **Documentation Files**
   - Update all file path references
   - Update directory structure diagrams
   - Update command examples with new paths

### Potential Import Errors

After moving scripts, check for:
```python
# Relative imports may break
from ..core.database import db_manager

# May need to become
import sys
sys.path.insert(0, '../..')
from core.database import db_manager
```

---

## Appendix C: Git Commands

### Safe File Moving

```bash
# Create backup branch
git checkout -b backup/pre-organization

# Switch to main branch
git checkout main

# Create new directories
mkdir -p docs/implementation
mkdir -p docs/operations
mkdir -p scripts/utilities
mkdir -p tests/manual/fixtures

# Move files (preserves git history)
git mv ENHANCEMENT_COMPARISON_FEATURE_SUMMARY.md docs/implementation/
git mv IMPLEMENTATION_SUMMARY.md docs/implementation/
git mv LANGUAGE_DETECTION_IMPLEMENTATION.md docs/implementation/
# ... etc

# Commit phase by phase
git add -A
git commit -m "docs: Reorganize implementation summaries to docs/implementation/"
```

### Verification After Move

```bash
# Check no files were lost
git status

# Check history preserved
git log --follow docs/implementation/IMPLEMENTATION_SUMMARY.md

# Check diff
git diff HEAD~1
```

---

## Sign-Off

**Plan Author**: Claude (AI Assistant)
**Plan Reviewer**: [To be assigned]
**Approval Required**: Project Lead/Maintainer

**Questions or Concerns**: Please review and provide feedback before execution.
