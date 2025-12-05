# TBCV System Map

**Generated:** 2025-12-03
**Purpose:** Comprehensive inventory of the TBCV codebase structure with coverage tracking for systematic exploration.

---

## System Overview

**TBCV (Truth-Based Content Validation)** is a Python-based intelligent content validation and enhancement system for technical documentation (primarily Aspose product documentation). It validates existing markdown files against rules and "truth data" (plugin definitions), generates actionable recommendations, and applies approved enhancements through a human-in-the-loop workflow.

**Tech Stack:**
- **Language:** Python 3.8+
- **Web Framework:** FastAPI + Uvicorn
- **Database:** SQLite with SQLAlchemy ORM
- **CLI:** Click framework with Rich output
- **Caching:** Custom two-level cache (L1 memory + L2 disk)
- **Templates:** Jinja2
- **LLM Integration:** Ollama (optional, disabled by default)
- **Testing:** Pytest with coverage, async, and Playwright for UI tests
- **Deployment:** Docker, systemd (Linux), Windows services

---

## Top-Level Structure

```
tbcv/
├── agents/              # Multi-agent system (11 core + 7 modular validators)
├── api/                 # FastAPI REST API server
├── cli/                 # Command-line interface (Click)
├── core/                # Core infrastructure (DB, config, cache, logging)
├── svc/                 # Background services (MCP server)
├── config/              # YAML/JSON configuration files
├── truth/               # Plugin truth data (JSON)
├── tests/               # Comprehensive test suite
├── docs/                # Documentation
├── scripts/             # Utility scripts (maintenance, testing, deployment)
├── templates/           # Jinja2 web UI templates
├── data/                # Runtime data (DB, logs, cache)
├── migrations/          # Database migrations
├── prompts/             # LLM prompts
├── rules/               # Validation rules
├── examples/            # Example files
├── main.py              # Application entry point
└── [other files]        # Config, setup, deployment files
```

---

## Coverage Table

**Status Legend:**
- **Not started** = No files from this area have been opened yet
- **Skimmed** = Listed files and reviewed 1-2 representative files to understand what lives here
- **Deep-read** = Opened multiple files, followed cross-references, understand how this fits into the system
- **Skipped** = Intentionally not exploring (generated/cache/vendor files)

| Area / Path | Type | Status | Notes |
|-------------|------|--------|-------|
| **Core Code** |
| `agents/` | Core code | Not started | Multi-agent system: orchestrator, truth manager, fuzzy detector, validators, enhancers, etc. 11 core agents + validators subdirectory |
| `agents/validators/` | Core code | Not started | Modular validator agents: YAML, Markdown, Code, Links, Structure, Truth, SEO (7-8 validators) |
| `api/` | Core code | Not started | FastAPI server with 40+ endpoints, dashboard, websocket, error handlers, export endpoints |
| `api/services/` | Core code | Not started | Background services like live event bus |
| `cli/` | Core code | Not started | Click-based CLI with 15+ commands, MCP helpers |
| `core/` | Core code | Not started | Core infrastructure: database, cache, logging, config loader, file utils, performance tracking, etc. (~27 modules) |
| `svc/` | Core code | Not started | Background services: MCP server, MCP client, MCP methods |
| `svc/mcp_methods/` | Core code | Not started | MCP server method implementations |
| **Infrastructure / Config** |
| `config/` | Infrastructure | Not started | YAML/JSON config files: main, agent, validation flow, cache, validators (12+ config files) |
| `Dockerfile` | Infrastructure | Not started | Docker container configuration |
| `docker-compose.yml` | Infrastructure | Not started | Docker Compose orchestration |
| `tbcv.service` | Infrastructure | Not started | Systemd service definition |
| `.github/` | Infrastructure | Not started | GitHub Actions workflows for CI/CD |
| `.github/workflows/` | Infrastructure | Not started | CI/CD workflow definitions |
| `migrations/` | Infrastructure | Not started | Database migration scripts |
| **Tests / Fixtures** |
| `tests/` | Tests | Not started | Comprehensive test suite with ~40+ test files at root level |
| `tests/agents/` | Tests | Not started | Agent-specific tests |
| `tests/api/` | Tests | Not started | API endpoint tests |
| `tests/cli/` | Tests | Not started | CLI command tests |
| `tests/core/` | Tests | Not started | Core infrastructure tests |
| `tests/contracts/` | Tests | Not started | Contract/interface tests |
| `tests/e2e/` | Tests | Not started | End-to-end workflow tests |
| `tests/fixtures/` | Tests | Not started | Test fixture data |
| `tests/integration/` | Tests | Not started | Integration tests |
| `tests/manual/` | Tests | Not started | Manual test scripts |
| `tests/performance/` | Tests | Not started | Performance/benchmark tests |
| `tests/startup/` | Tests | Not started | Startup validation tests |
| `tests/svc/` | Tests | Not started | Service tests (MCP) |
| `tests/ui/` | Tests | Not started | UI tests (Playwright) |
| `tests/utils/` | Tests | Not started | Test utility functions |
| `tests/reports/` | Tests | Not started | Test reports |
| `conftest.py` | Tests | Not started | Pytest configuration and fixtures (~53KB) |
| `pytest.ini` | Tests | Not started | Pytest settings |
| **Docs / Plans / Reports** |
| `docs/` | Docs | Not started | Comprehensive documentation (~35 markdown files) |
| `docs/implementation/` | Docs | Not started | Technical implementation notes |
| `docs/operations/` | Docs | Not started | Operational guides |
| `docs/testing/` | Docs | Not started | Testing guides |
| `docs/archive/` | Docs | Not started | Archived documentation |
| `reports/` | Reports | Not started | Analysis reports (sessions, tests, coverage, organization, archive) |
| `reports/sessions/` | Reports | Not started | Session reports |
| `reports/tests/` | Reports | Not started | Test execution reports |
| `reports/coverage/` | Reports | Not started | Coverage reports |
| `reports/organization/` | Reports | Not started | Organization/architecture reports |
| `reports/archive/` | Reports | Not started | Archived reports |
| `plans/` | Plans | Not started | Planning documents |
| `plans/tasks/` | Plans | Not started | Task-specific plans |
| `README.md` | Docs | Skimmed | Main project documentation - comprehensive overview of TBCV |
| `CHANGELOG.md` | Docs | Not started | Version history and release notes |
| **Tools / Scripts / Utilities** |
| `scripts/` | Tools | Not started | Utility scripts for maintenance, testing, deployment |
| `scripts/maintenance/` | Tools | Not started | System diagnostics and maintenance |
| `scripts/manual_tests/` | Tools | Not started | Manual testing scripts |
| `scripts/systemd/` | Tools | Not started | Linux service management |
| `scripts/testing/` | Tools | Not started | Test runners |
| `scripts/utilities/` | Tools | Not started | Database utilities |
| `scripts/windows/` | Tools | Not started | Windows service management |
| `tools/` | Tools | Not started | Development tools |
| `*.sh` files | Tools | Not started | Shell scripts (install, delete_redundant_docs) |
| `*.bat` files | Tools | Not started | Windows batch scripts (run, restart_server, cleanup, setup_ollama) |
| **Data / Truth / Config Data** |
| `truth/` | Data | Not started | Plugin truth data (JSON files for Aspose products: Words, PDF, Cells, Slides) |
| `truth/words/` | Data | Not started | Family-specific truth files for Words product |
| `rules/` | Data | Not started | Validation rule definitions |
| `prompts/` | Data | Not started | LLM prompt templates |
| `examples/` | Data | Not started | Example usage files |
| `templates/` | Data | Not started | Jinja2 templates for web dashboard |
| **Runtime / Generated / Cache** |
| `data/` | Runtime | Not started | Runtime data directory (DB, logs, cache, temp, validated files, reports) |
| `data/cache/` | Runtime | Not started | L2 disk cache storage |
| `data/logs/` | Runtime | Not started | Application log files |
| `data/temp/` | Runtime | Not started | Temporary files |
| `data/reports/` | Runtime | Not started | Runtime-generated reports |
| `data/validated_files/` | Runtime | Not started | Processed/validated files |
| `logs/` | Runtime | Not started | Additional log directory |
| `output/` | Runtime | Not started | Processing output files |
| `jobs/` | Runtime | Not started | Background job data |
| `.checkpoints/` | Runtime | Skipped | Checkpoint backups - autogenerated/runtime data |
| `__pycache__/` | Generated | Skipped | Python bytecode cache - autogenerated |
| `.pytest_cache/` | Generated | Skipped | Pytest cache - autogenerated |
| `tbcv.egg-info/` | Generated | Skipped | Python package metadata - autogenerated |
| `htmlcov/` | Generated | Skipped | HTML coverage reports - autogenerated |
| `.git/` | Generated | Skipped | Git metadata - standard VCS |
| **Special / Investigation Needed** |
| `en/` | Unknown | Not started | English test data? Contains test_full_stack_dir subdirectory |
| `en/test_full_stack_dir/` | Unknown | Not started | Test data directory - needs investigation |
| `test_full_stack_dir/` | Unknown | Not started | Test data directory at root - needs investigation |
| `archive/` | Archive | Not started | Archived/unused code |
| `archive/unused/` | Archive | Not started | Explicitly unused code |
| `.claude/` | Infrastructure | Not started | Claude Code configuration |
| **Entry Points / Main Files** |
| `main.py` | Core code | Skimmed | Application entry point: API mode launcher with startup checks, schema validation, bytecode cleanup (~257 lines) |
| `__init__.py` | Core code | Not started | Package initialization |
| `__main__.py` | Core code | Not started | Package entry point for `python -m tbcv` |
| `rule_manager.py` | Core code | Not started | Rule management at root level |
| **Build / Package Config** |
| `pyproject.toml` | Infrastructure | Skimmed | Python project config: build system, dependencies, tools (pytest, black, isort, mypy), package metadata |
| `requirements.txt` | Infrastructure | Not started | Python package dependencies |
| `setup_ollama.bat` | Infrastructure | Not started | Ollama LLM setup script |
| **Operational Files** |
| `.gitignore` | Infrastructure | Not started | Git ignore patterns |
| `.coverage` | Generated | Skipped | Coverage data file - autogenerated |
| `.audit_log.jsonl` | Runtime | Not started | Audit log file |
| `.performance_metrics.jsonl` | Runtime | Not started | Performance metrics log |
| `.maintenance_mode` | Runtime | Not started | Maintenance mode flag |
| `server_output.log` | Runtime | Not started | Server output log |
| `VERSION.txt` | Infrastructure | Not started | Version identifier |
| `nul` | Unknown | Not started | Empty/placeholder file? |

---

## Top-Level Directory Classification Summary

### Core Code (Must explore in Phase 1-2)
- `agents/` (11 core agents)
- `agents/validators/` (7-8 modular validators)
- `api/` (REST API server)
- `cli/` (CLI interface)
- `core/` (infrastructure)
- `svc/` (MCP services)

### Infrastructure (Must explore in Phase 3)
- `config/` (YAML/JSON configs)
- `.github/` (CI/CD)
- `migrations/` (DB)
- Docker files
- Service files

### Data & Truth (Must explore in Phase 2)
- `truth/` (plugin definitions)
- `rules/` (validation rules)
- `prompts/` (LLM prompts)
- `templates/` (web UI)

### Tests (Must explore across phases)
- `tests/` (comprehensive test suite with 13 subdirectories)

### Docs (Reference as needed)
- `docs/` (35+ documentation files)
- `reports/` (analysis reports)
- `plans/` (planning docs)

### Runtime/Generated (Skip or light review)
- `data/` (runtime data)
- `logs/`, `output/`, `jobs/` (runtime)
- `.checkpoints/` (backups)
- Various cache directories

### Archive/Unknown (Investigate as needed)
- `archive/` (old code)
- `en/`, `test_full_stack_dir/` (test data?)
- `examples/` (examples)

---

## Next Steps

**Phase 0 Status:** IN PROGRESS

**Remaining Phase 0 Tasks:**
1. ✅ Discover repo structure with ls/find
2. ✅ Identify all top-level areas
3. ✅ Create coverage table
4. ⏳ Create exploration-phase-00.md report
5. ⏳ Phase 0 self-review

**After Phase 0 Completion:**
- Proceed to Phase 1: Entrypoints & Runtime Surfaces
- Focus on: main.py, api/server.py, cli/main.py, agents/orchestrator.py
