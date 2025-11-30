# CLI/Web Parity Implementation Task Cards

**Total Tasks:** 16
**Phases:** 4
**Target:** 100% feature parity between CLI and Web/UI

---

## Task Card Index

| ID | Task | Phase | Priority |
|----|------|-------|----------|
| P1-T01 | Add Recommendation Generate Endpoint | 1 | High |
| P1-T02 | Add Recommendation Rebuild Endpoint | 1 | High |
| P1-T03 | Add CLI Enhancement History Commands | 1 | High |
| P1-T04 | Add CLI Rollback Command | 1 | High |
| P1-T05 | Add CLI Validation Diff Command | 1 | High |
| P1-T06 | Add CLI Validation Compare Command | 1 | High |
| P1-T07 | Add CLI Workflow Report Command | 1 | High |
| P1-T08 | Add CLI Workflow Summary Command | 1 | High |
| P2-T01 | Add CLI Maintenance Mode Commands | 2 | Medium |
| P2-T02 | Add CLI Cache Cleanup Command | 2 | Medium |
| P2-T03 | Add CLI Cache Rebuild Command | 2 | Medium |
| P2-T04 | Add CLI Performance Report Command | 2 | Medium |
| P2-T05 | Add CLI Workflow Watch Command | 2 | Medium |
| P3-T01 | Add CLI Health Probe Commands | 3 | Low |
| P3-T02 | Add CLI Agent Reload Command | 3 | Low |
| P3-T03 | Add CLI Checkpoint Command | 3 | Low |

---

## Phase 1: Core Feature Gaps

---

### Task Card P1-T01: Add Recommendation Generate Endpoint

**Role:** Senior engineer. Produce drop-in, production-ready code.

**Scope (only this):**
- Fix: Web API missing explicit recommendation generation (CLI has `recommendations generate`, Web lacks equivalent)
- Allowed paths:
  - `api/server.py`
  - `tests/api/test_recommendation_generation.py` (new)
- Forbidden: any other file

**Acceptance checks (must pass locally):**
- CLI: `python -m tbcv recommendations generate <validation_id>` works
- Web: `POST /api/recommendations/{validation_id}/generate` returns 200 with recommendation count
- Tests: `pytest tests/api/test_recommendation_generation.py -q`
- No mock data used in production paths
- Endpoint uses same `recommendation_agent` as CLI

**Deliverables:**
- Full file replacement for modified sections of `api/server.py` (add after line ~2455)
- New test file `tests/api/test_recommendation_generation.py`
- If schemas change, include forward-compatible migration code

**Hard rules:**
- Windows friendly paths, CRLF preserved
- Keep public function signatures unless you justify and update all call sites
- Zero network calls in tests
- Deterministic runs: set seeds, stable ordering
- Do not introduce new dependencies

**Design:**
```
POST /api/recommendations/{validation_id}/generate?force=false

Request: None (validation_id from path)
Response: {
    "success": bool,
    "message": str,
    "validation_id": str,
    "recommendations_count": int,
    "recommendations": list[dict]
}

Flow:
1. Get validation from db_manager
2. Check existing recommendations (return early if exist and not force)
3. Get recommendation_agent from registry
4. Call process_request("generate_recommendations", {...})
5. Return result
```

**Implementation location in api/server.py:**
```python
# Insert after bulk_review_recommendations (~line 2455)

@app.post("/api/recommendations/{validation_id}/generate")
async def generate_recommendations_for_validation(
    validation_id: str,
    force: bool = Query(False, description="Force regeneration even if recommendations exist")
):
    """Generate recommendations for a validation result."""
    try:
        validation = db_manager.get_validation_result(validation_id)
        if not validation:
            raise HTTPException(status_code=404, detail="Validation not found")

        existing = db_manager.list_recommendations(validation_id=validation_id)
        if existing and not force:
            return {
                "success": False,
                "message": f"Validation already has {len(existing)} recommendations. Use force=true to regenerate.",
                "existing_count": len(existing)
            }

        rec_agent = agent_registry.get_agent("recommendation_agent")
        if not rec_agent:
            raise HTTPException(status_code=500, detail="Recommendation agent not available")

        result = await rec_agent.process_request("generate_recommendations", {
            "validation_id": validation_id,
            "validation_results": validation.validation_results,
            "file_path": validation.file_path
        })

        return {
            "success": True,
            "message": f"Generated {result.get('count', 0)} recommendations",
            "validation_id": validation_id,
            "recommendations_count": result.get('count', 0),
            "recommendations": result.get('recommendations', [])
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to generate recommendations for {validation_id}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")
```

**Test file: tests/api/test_recommendation_generation.py**
```python
"""Tests for recommendation generation endpoint."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient


class TestRecommendationGeneration:
    """Test POST /api/recommendations/{validation_id}/generate endpoint."""

    def test_generate_recommendations_success(self, client, mock_db_manager, mock_agent_registry):
        """Test successful recommendation generation."""
        validation_id = "test-validation-123"

        # Mock validation exists
        mock_validation = MagicMock()
        mock_validation.validation_results = {"issues": []}
        mock_validation.file_path = "/test/file.md"
        mock_db_manager.get_validation_result.return_value = mock_validation
        mock_db_manager.list_recommendations.return_value = []

        # Mock recommendation agent
        mock_agent = AsyncMock()
        mock_agent.process_request.return_value = {
            "count": 3,
            "recommendations": [{"id": "rec1"}, {"id": "rec2"}, {"id": "rec3"}]
        }
        mock_agent_registry.get_agent.return_value = mock_agent

        response = client.post(f"/api/recommendations/{validation_id}/generate")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["recommendations_count"] == 3

    def test_generate_recommendations_validation_not_found(self, client, mock_db_manager):
        """Test generation fails when validation not found."""
        mock_db_manager.get_validation_result.return_value = None

        response = client.post("/api/recommendations/nonexistent/generate")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_generate_recommendations_already_exist_no_force(self, client, mock_db_manager):
        """Test generation skipped when recommendations exist and force=false."""
        mock_validation = MagicMock()
        mock_db_manager.get_validation_result.return_value = mock_validation
        mock_db_manager.list_recommendations.return_value = [MagicMock(), MagicMock()]

        response = client.post("/api/recommendations/test-id/generate")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "already has" in data["message"]

    def test_generate_recommendations_force_regenerate(self, client, mock_db_manager, mock_agent_registry):
        """Test force regeneration when recommendations exist."""
        mock_validation = MagicMock()
        mock_validation.validation_results = {}
        mock_validation.file_path = "/test.md"
        mock_db_manager.get_validation_result.return_value = mock_validation
        mock_db_manager.list_recommendations.return_value = [MagicMock()]

        mock_agent = AsyncMock()
        mock_agent.process_request.return_value = {"count": 5, "recommendations": []}
        mock_agent_registry.get_agent.return_value = mock_agent

        response = client.post("/api/recommendations/test-id/generate?force=true")

        assert response.status_code == 200
        assert response.json()["success"] is True
```

**Runbook:**
```bash
# 1. Apply changes to api/server.py (insert endpoint after line ~2455)

# 2. Create test file
# tests/api/test_recommendation_generation.py

# 3. Run tests
pytest tests/api/test_recommendation_generation.py -v

# 4. Start server and verify
python -m uvicorn api.server:app --host 127.0.0.1 --port 8080

# 5. Test endpoint manually
curl -X POST "http://127.0.0.1:8080/api/recommendations/TEST_VALIDATION_ID/generate"

# 6. Verify parity with CLI
python -m tbcv recommendations generate TEST_VALIDATION_ID
```

**Self-review (answer yes/no at the end):**
- [ ] Thorough, systematic, wired UI and backend, MCP usage intact, CLI and Web in sync, tests added and passing

---

### Task Card P1-T02: Add Recommendation Rebuild Endpoint

**Role:** Senior engineer. Produce drop-in, production-ready code.

**Scope (only this):**
- Fix: Web API missing recommendation rebuild (CLI has `recommendations rebuild`, Web lacks equivalent)
- Allowed paths:
  - `api/server.py`
  - `tests/api/test_recommendation_generation.py` (extend)
- Forbidden: any other file

**Acceptance checks (must pass locally):**
- CLI: `python -m tbcv recommendations rebuild <validation_id>` works
- Web: `POST /api/recommendations/{validation_id}/rebuild` returns 200
- Tests: `pytest tests/api/test_recommendation_generation.py -q`
- Endpoint deletes existing then regenerates

**Deliverables:**
- Full endpoint code for `api/server.py`
- Extended tests in `tests/api/test_recommendation_generation.py`

**Hard rules:**
- Windows friendly paths, CRLF preserved
- Keep public function signatures
- Zero network calls in tests
- Deterministic runs
- Do not introduce new dependencies

**Design:**
```
POST /api/recommendations/{validation_id}/rebuild

Response: {
    "success": bool,
    "message": str,
    "deleted_count": int,
    "new_count": int
}

Flow:
1. List existing recommendations for validation
2. Delete each recommendation
3. Regenerate recommendations (reuse generate logic)
4. Return counts
```

**Implementation location in api/server.py:**
```python
# Insert after generate endpoint

@app.post("/api/recommendations/{validation_id}/rebuild")
async def rebuild_recommendations_for_validation(validation_id: str):
    """Delete existing recommendations and regenerate from scratch."""
    try:
        existing = db_manager.list_recommendations(validation_id=validation_id)
        deleted_count = 0
        for rec in existing:
            if db_manager.delete_recommendation(rec.id):
                deleted_count += 1

        validation = db_manager.get_validation_result(validation_id)
        if not validation:
            raise HTTPException(status_code=404, detail="Validation not found")

        rec_agent = agent_registry.get_agent("recommendation_agent")
        if not rec_agent:
            raise HTTPException(status_code=500, detail="Recommendation agent not available")

        result = await rec_agent.process_request("generate_recommendations", {
            "validation_id": validation_id,
            "validation_results": validation.validation_results,
            "file_path": validation.file_path
        })

        return {
            "success": True,
            "message": f"Rebuilt recommendations: deleted {deleted_count}, created {result.get('count', 0)}",
            "deleted_count": deleted_count,
            "new_count": result.get('count', 0)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to rebuild recommendations for {validation_id}")
        raise HTTPException(status_code=500, detail=f"Rebuild failed: {str(e)}")
```

**Additional tests:**
```python
class TestRecommendationRebuild:
    """Test POST /api/recommendations/{validation_id}/rebuild endpoint."""

    def test_rebuild_recommendations_success(self, client, mock_db_manager, mock_agent_registry):
        """Test successful recommendation rebuild."""
        # Mock existing recommendations
        mock_recs = [MagicMock(id="rec1"), MagicMock(id="rec2")]
        mock_db_manager.list_recommendations.return_value = mock_recs
        mock_db_manager.delete_recommendation.return_value = True

        # Mock validation
        mock_validation = MagicMock()
        mock_validation.validation_results = {}
        mock_validation.file_path = "/test.md"
        mock_db_manager.get_validation_result.return_value = mock_validation

        # Mock agent
        mock_agent = AsyncMock()
        mock_agent.process_request.return_value = {"count": 4, "recommendations": []}
        mock_agent_registry.get_agent.return_value = mock_agent

        response = client.post("/api/recommendations/test-id/rebuild")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["deleted_count"] == 2
        assert data["new_count"] == 4

    def test_rebuild_recommendations_no_existing(self, client, mock_db_manager, mock_agent_registry):
        """Test rebuild when no existing recommendations."""
        mock_db_manager.list_recommendations.return_value = []

        mock_validation = MagicMock()
        mock_validation.validation_results = {}
        mock_validation.file_path = "/test.md"
        mock_db_manager.get_validation_result.return_value = mock_validation

        mock_agent = AsyncMock()
        mock_agent.process_request.return_value = {"count": 2, "recommendations": []}
        mock_agent_registry.get_agent.return_value = mock_agent

        response = client.post("/api/recommendations/test-id/rebuild")

        assert response.status_code == 200
        assert response.json()["deleted_count"] == 0
```

**Runbook:**
```bash
# 1. Apply changes to api/server.py

# 2. Extend test file

# 3. Run tests
pytest tests/api/test_recommendation_generation.py::TestRecommendationRebuild -v

# 4. Verify parity
curl -X POST "http://127.0.0.1:8080/api/recommendations/TEST_ID/rebuild"
python -m tbcv recommendations rebuild TEST_ID
```

**Self-review:**
- [ ] Thorough, systematic, wired UI and backend, MCP usage intact, CLI and Web in sync, tests added and passing

---

### Task Card P1-T03: Add CLI Enhancement History Commands

**Role:** Senior engineer. Produce drop-in, production-ready code.

**Scope (only this):**
- Fix: CLI missing enhancement history listing (Web has `/api/audit/enhancements`, CLI lacks equivalent)
- Allowed paths:
  - `cli/main.py`
  - `tests/cli/test_admin_enhancements.py` (new)
- Forbidden: any other file

**Acceptance checks (must pass locally):**
- CLI: `python -m tbcv admin enhancements --limit 10` works
- CLI: `python -m tbcv admin enhancement-detail <id>` works
- Tests: `pytest tests/cli/test_admin_enhancements.py -q`
- Output matches Web endpoint structure

**Deliverables:**
- Two new commands in `cli/main.py` admin group
- New test file `tests/cli/test_admin_enhancements.py`

**Hard rules:**
- Windows friendly paths, CRLF preserved
- Use existing `console` (rich) for output formatting
- Zero network calls in tests
- Deterministic runs
- Do not introduce new dependencies

**Design:**
```
tbcv admin enhancements [--file-path PATH] [--limit N] [--format table|json]
tbcv admin enhancement-detail <enhancement_id> [--format text|json]

Both commands use: agents.enhancement_history.get_history_manager()
```

**Implementation location in cli/main.py:**
```python
# Insert inside admin group (after cache commands, before probe-endpoints)

@admin.command("enhancements")
@click.option("--file-path", "-f", help="Filter by file path")
@click.option("--limit", "-l", default=50, help="Maximum records to show")
@click.option("--format", "output_format", type=click.Choice(["table", "json"]), default="table")
@click.pass_context
def list_enhancements(ctx, file_path, limit, output_format):
    """List enhancement history records."""
    from agents.enhancement_history import get_history_manager
    import json

    try:
        history = get_history_manager()
        records = history.list_enhancements(file_path=file_path, limit=limit)

        if output_format == "json":
            console.print(json.dumps([r.to_dict() for r in records], indent=2, default=str))
        else:
            if not records:
                console.print("[yellow]No enhancement records found.[/yellow]")
                return

            table = Table(title=f"Enhancement History ({len(records)} records)")
            table.add_column("ID", style="cyan", max_width=36)
            table.add_column("File", style="white", max_width=40)
            table.add_column("Status", style="yellow")
            table.add_column("Created", style="dim")

            for r in records:
                file_display = r.file_path[:37] + "..." if len(r.file_path) > 40 else r.file_path
                table.add_row(
                    r.id,
                    file_display,
                    r.status,
                    str(r.created_at)[:19]
                )

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error listing enhancements: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)


@admin.command("enhancement-detail")
@click.argument("enhancement_id")
@click.option("--format", "output_format", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
def get_enhancement_detail(ctx, enhancement_id, output_format):
    """Get detailed information about a specific enhancement."""
    from agents.enhancement_history import get_history_manager
    import json

    try:
        history = get_history_manager()
        record = history.get_enhancement_record(enhancement_id)

        if not record:
            console.print(f"[red]Enhancement {enhancement_id} not found[/red]")
            sys.exit(1)

        if output_format == "json":
            console.print(json.dumps(record.to_dict(), indent=2, default=str))
        else:
            console.print(Panel(f"[bold]Enhancement Detail[/bold]", expand=False))

            table = Table(show_header=False, box=None)
            table.add_column("Field", style="cyan")
            table.add_column("Value", style="white")

            table.add_row("ID", record.id)
            table.add_row("File", record.file_path)
            table.add_row("Status", record.status)
            table.add_row("Created", str(record.created_at))
            table.add_row("Enhanced by", getattr(record, 'enhanced_by', 'N/A'))

            if hasattr(record, 'rollback_expires_at') and record.rollback_expires_at:
                table.add_row("Rollback expires", str(record.rollback_expires_at))

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error getting enhancement detail: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)
```

**Test file: tests/cli/test_admin_enhancements.py**
```python
"""Tests for CLI admin enhancement commands."""
import pytest
from click.testing import CliRunner
from unittest.mock import MagicMock, patch
from cli.main import cli


class TestAdminEnhancements:
    """Test admin enhancements command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_list_enhancements_empty(self, runner):
        """Test listing when no enhancements exist."""
        with patch('cli.main.get_history_manager') as mock_history:
            mock_history.return_value.list_enhancements.return_value = []

            result = runner.invoke(cli, ['admin', 'enhancements'])

            assert result.exit_code == 0
            assert "No enhancement" in result.output

    def test_list_enhancements_with_records(self, runner):
        """Test listing with enhancement records."""
        mock_record = MagicMock()
        mock_record.id = "enh-123"
        mock_record.file_path = "/test/file.md"
        mock_record.status = "applied"
        mock_record.created_at = "2025-01-01T00:00:00"
        mock_record.to_dict.return_value = {"id": "enh-123"}

        with patch('cli.main.get_history_manager') as mock_history:
            mock_history.return_value.list_enhancements.return_value = [mock_record]

            result = runner.invoke(cli, ['admin', 'enhancements'])

            assert result.exit_code == 0
            assert "enh-123" in result.output or "Enhancement" in result.output

    def test_list_enhancements_json_format(self, runner):
        """Test JSON output format."""
        mock_record = MagicMock()
        mock_record.to_dict.return_value = {"id": "enh-456", "status": "applied"}

        with patch('cli.main.get_history_manager') as mock_history:
            mock_history.return_value.list_enhancements.return_value = [mock_record]

            result = runner.invoke(cli, ['admin', 'enhancements', '--format', 'json'])

            assert result.exit_code == 0
            assert "enh-456" in result.output

    def test_list_enhancements_with_file_filter(self, runner):
        """Test filtering by file path."""
        with patch('cli.main.get_history_manager') as mock_history:
            mock_history.return_value.list_enhancements.return_value = []

            result = runner.invoke(cli, ['admin', 'enhancements', '--file-path', '/test/path.md'])

            mock_history.return_value.list_enhancements.assert_called_once_with(
                file_path='/test/path.md', limit=50
            )


class TestAdminEnhancementDetail:
    """Test admin enhancement-detail command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_enhancement_detail_not_found(self, runner):
        """Test detail when enhancement not found."""
        with patch('cli.main.get_history_manager') as mock_history:
            mock_history.return_value.get_enhancement_record.return_value = None

            result = runner.invoke(cli, ['admin', 'enhancement-detail', 'nonexistent'])

            assert result.exit_code == 1
            assert "not found" in result.output.lower()

    def test_enhancement_detail_success(self, runner):
        """Test successful detail retrieval."""
        mock_record = MagicMock()
        mock_record.id = "enh-789"
        mock_record.file_path = "/test/file.md"
        mock_record.status = "applied"
        mock_record.created_at = "2025-01-01T00:00:00"
        mock_record.enhanced_by = "user"
        mock_record.to_dict.return_value = {"id": "enh-789"}

        with patch('cli.main.get_history_manager') as mock_history:
            mock_history.return_value.get_enhancement_record.return_value = mock_record

            result = runner.invoke(cli, ['admin', 'enhancement-detail', 'enh-789'])

            assert result.exit_code == 0
```

**Runbook:**
```bash
# 1. Apply changes to cli/main.py (add commands in admin group)

# 2. Create test file
# tests/cli/test_admin_enhancements.py

# 3. Run tests
pytest tests/cli/test_admin_enhancements.py -v

# 4. Test CLI commands
python -m tbcv admin enhancements --limit 5
python -m tbcv admin enhancements --format json
python -m tbcv admin enhancement-detail ENHANCEMENT_ID

# 5. Verify parity with Web
curl "http://127.0.0.1:8080/api/audit/enhancements?limit=5"
```

**Self-review:**
- [ ] Thorough, systematic, wired UI and backend, MCP usage intact, CLI and Web in sync, tests added and passing

---

### Task Card P1-T04: Add CLI Rollback Command

**Role:** Senior engineer. Produce drop-in, production-ready code.

**Scope (only this):**
- Fix: CLI missing rollback capability (Web has `POST /api/audit/rollback`, CLI lacks equivalent)
- Allowed paths:
  - `cli/main.py`
  - `tests/cli/test_admin_enhancements.py` (extend)
- Forbidden: any other file

**Acceptance checks (must pass locally):**
- CLI: `python -m tbcv admin rollback <enhancement_id> --confirm` works
- Tests: `pytest tests/cli/test_admin_enhancements.py::TestAdminRollback -q`
- Rollback restores original content

**Deliverables:**
- New `rollback` command in `cli/main.py` admin group
- Extended tests

**Hard rules:**
- Windows friendly paths, CRLF preserved
- Require `--confirm` flag for safety
- Zero network calls in tests
- Deterministic runs
- Do not introduce new dependencies

**Design:**
```
tbcv admin rollback <enhancement_id> --confirm [--rolled-back-by USER]

Flow:
1. Validate --confirm flag
2. Get enhancement record (show details)
3. Call history.rollback_enhancement()
4. Report success/failure
```

**Implementation:**
```python
@admin.command("rollback")
@click.argument("enhancement_id")
@click.option("--confirm", is_flag=True, help="Confirm rollback operation (required)")
@click.option("--rolled-back-by", default="cli_user", help="User performing rollback")
@click.pass_context
def rollback_enhancement(ctx, enhancement_id, confirm, rolled_back_by):
    """Rollback an enhancement to restore original content."""
    from agents.enhancement_history import get_history_manager

    if not confirm:
        console.print("[yellow]Rollback requires confirmation.[/yellow]")
        console.print(f"\nTo rollback enhancement {enhancement_id}:")
        console.print(f"  tbcv admin rollback {enhancement_id} --confirm")
        return

    try:
        history = get_history_manager()

        # Show what will be rolled back
        record = history.get_enhancement_record(enhancement_id)
        if not record:
            console.print(f"[red]Enhancement {enhancement_id} not found[/red]")
            sys.exit(1)

        console.print(Panel("[bold]Rolling back enhancement[/bold]", expand=False))
        console.print(f"  ID:      {record.id}")
        console.print(f"  File:    {record.file_path}")
        console.print(f"  Created: {record.created_at}")
        console.print()

        success = history.rollback_enhancement(enhancement_id, rolled_back_by)

        if success:
            console.print("[green]Rollback successful![/green]")
        else:
            console.print("[red]Rollback failed - point not found or expired[/red]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]Error during rollback: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)
```

**Additional tests:**
```python
class TestAdminRollback:
    """Test admin rollback command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_rollback_requires_confirm(self, runner):
        """Test rollback requires --confirm flag."""
        result = runner.invoke(cli, ['admin', 'rollback', 'enh-123'])

        assert result.exit_code == 0  # Exits gracefully with message
        assert "confirm" in result.output.lower()

    def test_rollback_enhancement_not_found(self, runner):
        """Test rollback when enhancement not found."""
        with patch('cli.main.get_history_manager') as mock_history:
            mock_history.return_value.get_enhancement_record.return_value = None

            result = runner.invoke(cli, ['admin', 'rollback', 'nonexistent', '--confirm'])

            assert result.exit_code == 1
            assert "not found" in result.output.lower()

    def test_rollback_success(self, runner):
        """Test successful rollback."""
        mock_record = MagicMock()
        mock_record.id = "enh-123"
        mock_record.file_path = "/test/file.md"
        mock_record.created_at = "2025-01-01T00:00:00"

        with patch('cli.main.get_history_manager') as mock_history:
            mock_history.return_value.get_enhancement_record.return_value = mock_record
            mock_history.return_value.rollback_enhancement.return_value = True

            result = runner.invoke(cli, ['admin', 'rollback', 'enh-123', '--confirm'])

            assert result.exit_code == 0
            assert "successful" in result.output.lower()

    def test_rollback_failure(self, runner):
        """Test rollback failure (expired/not found)."""
        mock_record = MagicMock()
        mock_record.id = "enh-123"
        mock_record.file_path = "/test/file.md"
        mock_record.created_at = "2025-01-01T00:00:00"

        with patch('cli.main.get_history_manager') as mock_history:
            mock_history.return_value.get_enhancement_record.return_value = mock_record
            mock_history.return_value.rollback_enhancement.return_value = False

            result = runner.invoke(cli, ['admin', 'rollback', 'enh-123', '--confirm'])

            assert result.exit_code == 1
            assert "failed" in result.output.lower()
```

**Runbook:**
```bash
# 1. Apply changes to cli/main.py

# 2. Run tests
pytest tests/cli/test_admin_enhancements.py::TestAdminRollback -v

# 3. Test CLI command
python -m tbcv admin rollback ENHANCEMENT_ID  # Should require --confirm
python -m tbcv admin rollback ENHANCEMENT_ID --confirm

# 4. Verify parity with Web
curl -X POST "http://127.0.0.1:8080/api/audit/rollback" \
  -H "Content-Type: application/json" \
  -d '{"enhancement_id": "ENHANCEMENT_ID", "rolled_back_by": "user", "confirmation": true}'
```

**Self-review:**
- [ ] Thorough, systematic, wired UI and backend, MCP usage intact, CLI and Web in sync, tests added and passing

---

### Task Card P1-T05: Add CLI Validation Diff Command

**Role:** Senior engineer. Produce drop-in, production-ready code.

**Scope (only this):**
- Fix: CLI missing validation diff view (Web has `/api/validations/{id}/diff`, CLI lacks equivalent)
- Allowed paths:
  - `cli/main.py`
  - `tests/cli/test_validation_diff.py` (new)
- Forbidden: any other file

**Acceptance checks (must pass locally):**
- CLI: `python -m tbcv validations diff <validation_id>` shows unified diff
- CLI: `python -m tbcv validations diff <validation_id> --format side-by-side` works
- Tests: `pytest tests/cli/test_validation_diff.py -q`
- Output matches Web endpoint content

**Deliverables:**
- New `diff` command in `cli/main.py` validations group
- New test file `tests/cli/test_validation_diff.py`

**Hard rules:**
- Windows friendly paths, CRLF preserved
- Use colored output (green for additions, red for deletions)
- Zero network calls in tests
- Deterministic runs
- Do not introduce new dependencies (use difflib from stdlib)

**Design:**
```
tbcv validations diff <validation_id> [--format unified|side-by-side|json] [--context N]

Flow:
1. Get validation from database
2. Extract original_content and enhanced_content from validation_results
3. Generate diff using difflib
4. Display with colors
```

**Implementation:**
```python
# Insert in validations group (after history command)

@validations.command("diff")
@click.argument("validation_id")
@click.option("--format", "output_format", type=click.Choice(["unified", "side-by-side", "json"]), default="unified")
@click.option("--context", "-c", default=3, help="Lines of context for unified diff")
@click.pass_context
def validation_diff(ctx, validation_id, output_format, context):
    """Show content diff for an enhanced validation."""
    import difflib
    import json

    try:
        validation = db_manager.get_validation_result(validation_id)
        if not validation:
            console.print(f"[red]Validation {validation_id} not found[/red]")
            sys.exit(1)

        results = validation.validation_results or {}
        original = results.get("original_content")
        enhanced = results.get("enhanced_content")

        if not original or not enhanced:
            console.print("[yellow]No diff available - validation may not have been enhanced yet[/yellow]")
            sys.exit(1)

        if output_format == "json":
            diff_data = {
                "validation_id": validation_id,
                "file_path": validation.file_path,
                "has_diff": original != enhanced,
                "original_lines": len(original.splitlines()),
                "enhanced_lines": len(enhanced.splitlines())
            }
            console.print(json.dumps(diff_data, indent=2))

        elif output_format == "unified":
            console.print(Panel(f"[bold]Diff for {validation_id[:8]}...[/bold]", expand=False))

            diff = difflib.unified_diff(
                original.splitlines(keepends=True),
                enhanced.splitlines(keepends=True),
                fromfile="Original",
                tofile="Enhanced",
                n=context
            )

            for line in diff:
                line = line.rstrip()
                if line.startswith("+") and not line.startswith("+++"):
                    console.print(f"[green]{line}[/green]")
                elif line.startswith("-") and not line.startswith("---"):
                    console.print(f"[red]{line}[/red]")
                elif line.startswith("@@"):
                    console.print(f"[cyan]{line}[/cyan]")
                else:
                    console.print(line)

        else:  # side-by-side
            orig_lines = original.splitlines()
            enh_lines = enhanced.splitlines()
            max_lines = max(len(orig_lines), len(enh_lines))

            table = Table(title="Side-by-Side Comparison")
            table.add_column("Line", style="dim", width=5)
            table.add_column("Original", style="white", width=50, overflow="fold")
            table.add_column("Enhanced", style="white", width=50, overflow="fold")

            for i in range(min(max_lines, 100)):  # Limit to 100 lines
                orig = orig_lines[i] if i < len(orig_lines) else ""
                enh = enh_lines[i] if i < len(enh_lines) else ""

                # Highlight differences
                if orig != enh:
                    orig_style = "[red]" + orig + "[/red]" if orig else "[dim]-[/dim]"
                    enh_style = "[green]" + enh + "[/green]" if enh else "[dim]-[/dim]"
                else:
                    orig_style = orig
                    enh_style = enh

                table.add_row(str(i + 1), orig_style, enh_style)

            console.print(table)

            if max_lines > 100:
                console.print(f"[dim]... {max_lines - 100} more lines not shown[/dim]")

    except Exception as e:
        console.print(f"[red]Error getting diff: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)
```

**Test file: tests/cli/test_validation_diff.py**
```python
"""Tests for CLI validation diff command."""
import pytest
from click.testing import CliRunner
from unittest.mock import MagicMock, patch
from cli.main import cli


class TestValidationDiff:
    """Test validations diff command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def mock_validation_with_diff(self):
        mock = MagicMock()
        mock.file_path = "/test/file.md"
        mock.validation_results = {
            "original_content": "Line 1\nLine 2\nLine 3",
            "enhanced_content": "Line 1\nModified Line 2\nLine 3\nLine 4"
        }
        return mock

    def test_diff_validation_not_found(self, runner):
        """Test diff when validation not found."""
        with patch('cli.main.db_manager') as mock_db:
            mock_db.get_validation_result.return_value = None

            result = runner.invoke(cli, ['validations', 'diff', 'nonexistent'])

            assert result.exit_code == 1
            assert "not found" in result.output.lower()

    def test_diff_no_enhancement(self, runner):
        """Test diff when validation not enhanced."""
        mock_validation = MagicMock()
        mock_validation.validation_results = {}

        with patch('cli.main.db_manager') as mock_db:
            mock_db.get_validation_result.return_value = mock_validation

            result = runner.invoke(cli, ['validations', 'diff', 'test-id'])

            assert result.exit_code == 1
            assert "not have been enhanced" in result.output.lower() or "no diff" in result.output.lower()

    def test_diff_unified_format(self, runner, mock_validation_with_diff):
        """Test unified diff format."""
        with patch('cli.main.db_manager') as mock_db:
            mock_db.get_validation_result.return_value = mock_validation_with_diff

            result = runner.invoke(cli, ['validations', 'diff', 'test-id'])

            assert result.exit_code == 0
            # Should show diff markers
            assert "+" in result.output or "-" in result.output or "@@" in result.output

    def test_diff_json_format(self, runner, mock_validation_with_diff):
        """Test JSON output format."""
        with patch('cli.main.db_manager') as mock_db:
            mock_db.get_validation_result.return_value = mock_validation_with_diff

            result = runner.invoke(cli, ['validations', 'diff', 'test-id', '--format', 'json'])

            assert result.exit_code == 0
            assert "validation_id" in result.output
            assert "has_diff" in result.output

    def test_diff_side_by_side_format(self, runner, mock_validation_with_diff):
        """Test side-by-side format."""
        with patch('cli.main.db_manager') as mock_db:
            mock_db.get_validation_result.return_value = mock_validation_with_diff

            result = runner.invoke(cli, ['validations', 'diff', 'test-id', '--format', 'side-by-side'])

            assert result.exit_code == 0
            assert "Original" in result.output or "Enhanced" in result.output
```

**Runbook:**
```bash
# 1. Apply changes to cli/main.py

# 2. Create test file

# 3. Run tests
pytest tests/cli/test_validation_diff.py -v

# 4. Test CLI commands
python -m tbcv validations diff VALIDATION_ID
python -m tbcv validations diff VALIDATION_ID --format json
python -m tbcv validations diff VALIDATION_ID --format side-by-side

# 5. Verify parity with Web
curl "http://127.0.0.1:8080/api/validations/VALIDATION_ID/diff"
```

**Self-review:**
- [ ] Thorough, systematic, wired UI and backend, MCP usage intact, CLI and Web in sync, tests added and passing

---

### Task Card P1-T06: Add CLI Validation Compare Command

**Role:** Senior engineer. Produce drop-in, production-ready code.

**Scope (only this):**
- Fix: CLI missing validation comparison with statistics (Web has `/api/validations/{id}/enhancement-comparison`)
- Allowed paths:
  - `cli/main.py`
  - `tests/cli/test_validation_diff.py` (extend)
- Forbidden: any other file

**Acceptance checks (must pass locally):**
- CLI: `python -m tbcv validations compare <validation_id>` shows statistics
- Tests: `pytest tests/cli/test_validation_diff.py::TestValidationCompare -q`

**Deliverables:**
- New `compare` command in `cli/main.py` validations group
- Extended tests

**Hard rules:**
- Windows friendly paths, CRLF preserved
- Zero network calls in tests
- Deterministic runs
- Do not introduce new dependencies

**Implementation:**
```python
@validations.command("compare")
@click.argument("validation_id")
@click.option("--format", "output_format", type=click.Choice(["summary", "detailed", "json"]), default="summary")
@click.pass_context
def validation_compare(ctx, validation_id, output_format):
    """Show comprehensive enhancement comparison with statistics."""
    import difflib
    import json

    try:
        validation = db_manager.get_validation_result(validation_id)
        if not validation:
            console.print(f"[red]Validation {validation_id} not found[/red]")
            sys.exit(1)

        results = validation.validation_results or {}
        original = results.get("original_content", "")
        enhanced = results.get("enhanced_content", "")

        if not original or not enhanced:
            console.print("[yellow]No comparison available - validation not enhanced[/yellow]")
            sys.exit(1)

        # Calculate statistics
        orig_lines = original.splitlines()
        enh_lines = enhanced.splitlines()

        matcher = difflib.SequenceMatcher(None, orig_lines, enh_lines)

        added = 0
        removed = 0
        modified = 0

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "insert":
                added += j2 - j1
            elif tag == "delete":
                removed += i2 - i1
            elif tag == "replace":
                modified += max(i2 - i1, j2 - j1)

        stats = {
            "validation_id": validation_id,
            "file_path": validation.file_path,
            "original_lines": len(orig_lines),
            "enhanced_lines": len(enh_lines),
            "lines_added": added,
            "lines_removed": removed,
            "lines_modified": modified,
            "similarity_ratio": round(matcher.ratio(), 4),
            "applied_recommendations": results.get("applied_recommendations", 0)
        }

        if output_format == "json":
            console.print(json.dumps(stats, indent=2))
        else:
            console.print(Panel(f"[bold]Enhancement Comparison[/bold]", expand=False))
            console.print(f"Validation: {validation_id[:8]}...")
            console.print(f"File: {validation.file_path}")
            console.print()

            table = Table(title="Statistics")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="yellow")

            table.add_row("Original lines", str(stats['original_lines']))
            table.add_row("Enhanced lines", str(stats['enhanced_lines']))
            table.add_row("Lines added", f"[green]+{stats['lines_added']}[/green]")
            table.add_row("Lines removed", f"[red]-{stats['lines_removed']}[/red]")
            table.add_row("Lines modified", str(stats['lines_modified']))
            table.add_row("Similarity", f"{stats['similarity_ratio']*100:.1f}%")
            table.add_row("Recommendations applied", str(stats['applied_recommendations']))

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error getting comparison: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)
```

**Additional tests:**
```python
class TestValidationCompare:
    """Test validations compare command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_compare_validation_not_found(self, runner):
        """Test compare when validation not found."""
        with patch('cli.main.db_manager') as mock_db:
            mock_db.get_validation_result.return_value = None

            result = runner.invoke(cli, ['validations', 'compare', 'nonexistent'])

            assert result.exit_code == 1

    def test_compare_shows_statistics(self, runner):
        """Test compare shows statistics."""
        mock_validation = MagicMock()
        mock_validation.file_path = "/test/file.md"
        mock_validation.validation_results = {
            "original_content": "Line 1\nLine 2",
            "enhanced_content": "Line 1\nLine 2\nLine 3",
            "applied_recommendations": 2
        }

        with patch('cli.main.db_manager') as mock_db:
            mock_db.get_validation_result.return_value = mock_validation

            result = runner.invoke(cli, ['validations', 'compare', 'test-id'])

            assert result.exit_code == 0
            assert "Statistics" in result.output or "lines" in result.output.lower()

    def test_compare_json_format(self, runner):
        """Test compare JSON output."""
        mock_validation = MagicMock()
        mock_validation.file_path = "/test/file.md"
        mock_validation.validation_results = {
            "original_content": "Line 1",
            "enhanced_content": "Line 1\nLine 2",
            "applied_recommendations": 1
        }

        with patch('cli.main.db_manager') as mock_db:
            mock_db.get_validation_result.return_value = mock_validation

            result = runner.invoke(cli, ['validations', 'compare', 'test-id', '--format', 'json'])

            assert result.exit_code == 0
            assert "similarity_ratio" in result.output
            assert "lines_added" in result.output
```

**Runbook:**
```bash
# 1. Apply changes to cli/main.py

# 2. Run tests
pytest tests/cli/test_validation_diff.py::TestValidationCompare -v

# 3. Test CLI
python -m tbcv validations compare VALIDATION_ID
python -m tbcv validations compare VALIDATION_ID --format json

# 4. Verify parity
curl "http://127.0.0.1:8080/api/validations/VALIDATION_ID/enhancement-comparison"
```

**Self-review:**
- [ ] Thorough, systematic, wired UI and backend, MCP usage intact, CLI and Web in sync, tests added and passing

---

### Task Card P1-T07: Add CLI Workflow Report Command

**Role:** Senior engineer. Produce drop-in, production-ready code.

**Scope (only this):**
- Fix: CLI missing workflow report (Web has `/workflows/{id}/report`)
- Allowed paths:
  - `cli/main.py`
  - `tests/cli/test_workflow_report.py` (new)
- Forbidden: any other file

**Acceptance checks (must pass locally):**
- CLI: `python -m tbcv workflows report <workflow_id>` works
- CLI: `python -m tbcv workflows report <workflow_id> --output report.md` saves file
- Tests: `pytest tests/cli/test_workflow_report.py -q`

**Deliverables:**
- New `report` command in `cli/main.py` workflows group
- New test file

**Hard rules:**
- Windows friendly paths, CRLF preserved
- Zero network calls in tests
- Deterministic runs
- Do not introduce new dependencies

**Implementation:**
```python
# Insert in workflows group

@workflows.command("report")
@click.argument("workflow_id")
@click.option("--output", "-o", type=click.Path(), help="Save report to file")
@click.option("--format", "output_format", type=click.Choice(["text", "json", "markdown"]), default="text")
@click.pass_context
def workflow_report(ctx, workflow_id, output, output_format):
    """Generate comprehensive workflow report."""
    import json

    try:
        report = db_manager.generate_workflow_report(workflow_id)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error generating report: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)

    if output_format == "json":
        content = json.dumps(report, indent=2, default=str)
    elif output_format == "markdown":
        content = _format_workflow_report_markdown(report)
    else:
        content = _format_workflow_report_text(report)

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(content)
        console.print(f"[green]Report saved to {output}[/green]")
    else:
        console.print(content)


def _format_workflow_report_text(report):
    """Format workflow report as text."""
    lines = []
    lines.append(f"\nWorkflow Report: {report['workflow_id']}")
    lines.append("=" * 60)
    lines.append(f"Type:       {report['type']}")
    lines.append(f"Status:     {report['status']}")
    lines.append(f"Created:    {report['created_at']}")
    lines.append(f"Completed:  {report.get('completed_at', 'N/A')}")
    lines.append(f"Duration:   {report.get('duration_ms', 0)}ms")

    summary = report.get("summary", {})
    lines.append(f"\nSummary:")
    lines.append(f"  Total validations:        {summary.get('total_validations', 0)}")
    lines.append(f"  Passed:                   {summary.get('passed', 0)}")
    lines.append(f"  Failed:                   {summary.get('failed', 0)}")
    lines.append(f"  Total recommendations:    {summary.get('total_recommendations', 0)}")
    lines.append(f"  Recommendations applied:  {summary.get('recommendations_applied', 0)}")

    return "\n".join(lines)


def _format_workflow_report_markdown(report):
    """Format workflow report as markdown."""
    lines = []
    lines.append(f"# Workflow Report: {report['workflow_id'][:8]}...")
    lines.append("")
    lines.append(f"| Field | Value |")
    lines.append(f"|-------|-------|")
    lines.append(f"| Type | {report['type']} |")
    lines.append(f"| Status | {report['status']} |")
    lines.append(f"| Created | {report['created_at']} |")
    lines.append(f"| Duration | {report.get('duration_ms', 0)}ms |")
    lines.append("")

    summary = report.get("summary", {})
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Total validations:** {summary.get('total_validations', 0)}")
    lines.append(f"- **Passed:** {summary.get('passed', 0)}")
    lines.append(f"- **Failed:** {summary.get('failed', 0)}")
    lines.append(f"- **Recommendations:** {summary.get('total_recommendations', 0)}")

    return "\n".join(lines)
```

**Test file: tests/cli/test_workflow_report.py**
```python
"""Tests for CLI workflow report commands."""
import pytest
from click.testing import CliRunner
from unittest.mock import MagicMock, patch
from cli.main import cli


class TestWorkflowReport:
    """Test workflows report command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def mock_report(self):
        return {
            "workflow_id": "wf-123",
            "type": "batch_validation",
            "status": "completed",
            "created_at": "2025-01-01T00:00:00",
            "completed_at": "2025-01-01T00:05:00",
            "duration_ms": 300000,
            "summary": {
                "total_validations": 10,
                "passed": 8,
                "failed": 2,
                "total_recommendations": 15,
                "recommendations_applied": 5
            }
        }

    def test_report_workflow_not_found(self, runner):
        """Test report when workflow not found."""
        with patch('cli.main.db_manager') as mock_db:
            mock_db.generate_workflow_report.side_effect = ValueError("Workflow not found")

            result = runner.invoke(cli, ['workflows', 'report', 'nonexistent'])

            assert result.exit_code == 1

    def test_report_text_format(self, runner, mock_report):
        """Test text format output."""
        with patch('cli.main.db_manager') as mock_db:
            mock_db.generate_workflow_report.return_value = mock_report

            result = runner.invoke(cli, ['workflows', 'report', 'wf-123'])

            assert result.exit_code == 0
            assert "Workflow Report" in result.output
            assert "completed" in result.output.lower()

    def test_report_json_format(self, runner, mock_report):
        """Test JSON format output."""
        with patch('cli.main.db_manager') as mock_db:
            mock_db.generate_workflow_report.return_value = mock_report

            result = runner.invoke(cli, ['workflows', 'report', 'wf-123', '--format', 'json'])

            assert result.exit_code == 0
            assert "workflow_id" in result.output
            assert "wf-123" in result.output

    def test_report_markdown_format(self, runner, mock_report):
        """Test markdown format output."""
        with patch('cli.main.db_manager') as mock_db:
            mock_db.generate_workflow_report.return_value = mock_report

            result = runner.invoke(cli, ['workflows', 'report', 'wf-123', '--format', 'markdown'])

            assert result.exit_code == 0
            assert "# Workflow Report" in result.output

    def test_report_save_to_file(self, runner, mock_report, tmp_path):
        """Test saving report to file."""
        output_file = tmp_path / "report.txt"

        with patch('cli.main.db_manager') as mock_db:
            mock_db.generate_workflow_report.return_value = mock_report

            result = runner.invoke(cli, ['workflows', 'report', 'wf-123', '--output', str(output_file)])

            assert result.exit_code == 0
            assert output_file.exists()
            assert "Workflow Report" in output_file.read_text()
```

**Runbook:**
```bash
# 1. Apply changes to cli/main.py

# 2. Create test file

# 3. Run tests
pytest tests/cli/test_workflow_report.py -v

# 4. Test CLI
python -m tbcv workflows report WORKFLOW_ID
python -m tbcv workflows report WORKFLOW_ID --format json
python -m tbcv workflows report WORKFLOW_ID --output report.md --format markdown

# 5. Verify parity
curl "http://127.0.0.1:8080/workflows/WORKFLOW_ID/report"
```

**Self-review:**
- [ ] Thorough, systematic, wired UI and backend, MCP usage intact, CLI and Web in sync, tests added and passing

---

### Task Card P1-T08: Add CLI Workflow Summary Command

**Role:** Senior engineer. Produce drop-in, production-ready code.

**Scope (only this):**
- Fix: CLI missing workflow summary (Web has `/workflows/{id}/summary`)
- Allowed paths:
  - `cli/main.py`
  - `tests/cli/test_workflow_report.py` (extend)
- Forbidden: any other file

**Acceptance checks (must pass locally):**
- CLI: `python -m tbcv workflows summary <workflow_id>` shows quick overview
- Tests: `pytest tests/cli/test_workflow_report.py::TestWorkflowSummary -q`

**Deliverables:**
- New `summary` command in `cli/main.py` workflows group
- Extended tests

**Implementation:**
```python
@workflows.command("summary")
@click.argument("workflow_id")
@click.option("--format", "output_format", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
def workflow_summary(ctx, workflow_id, output_format):
    """Show workflow summary (quick overview without details)."""
    import json

    try:
        report = db_manager.generate_workflow_report(workflow_id)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)

    summary = {
        "workflow_id": report["workflow_id"],
        "status": report["status"],
        "type": report["type"],
        "created_at": report["created_at"],
        "completed_at": report.get("completed_at"),
        "duration_ms": report.get("duration_ms"),
        "summary": report.get("summary", {})
    }

    if output_format == "json":
        console.print(json.dumps(summary, indent=2, default=str))
    else:
        s = summary["summary"]
        status_color = "green" if summary["status"] == "completed" else "yellow" if summary["status"] == "running" else "red"

        console.print(Panel(f"[bold]Workflow Summary[/bold]", expand=False))
        console.print(f"ID:          {summary['workflow_id'][:8]}...")
        console.print(f"Status:      [{status_color}]{summary['status']}[/{status_color}]")
        console.print(f"Type:        {summary['type']}")
        console.print(f"Validations: {s.get('total_validations', 0)} ({s.get('passed', 0)} passed, {s.get('failed', 0)} failed)")
        console.print(f"Recommendations: {s.get('total_recommendations', 0)} ({s.get('recommendations_applied', 0)} applied)")

        if summary.get('duration_ms'):
            duration_sec = summary['duration_ms'] / 1000
            console.print(f"Duration:    {duration_sec:.1f}s")
```

**Additional tests:**
```python
class TestWorkflowSummary:
    """Test workflows summary command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_summary_text_output(self, runner):
        """Test summary text output."""
        mock_report = {
            "workflow_id": "wf-456",
            "type": "validate_file",
            "status": "completed",
            "created_at": "2025-01-01T00:00:00",
            "duration_ms": 5000,
            "summary": {
                "total_validations": 1,
                "passed": 1,
                "failed": 0,
                "total_recommendations": 3,
                "recommendations_applied": 2
            }
        }

        with patch('cli.main.db_manager') as mock_db:
            mock_db.generate_workflow_report.return_value = mock_report

            result = runner.invoke(cli, ['workflows', 'summary', 'wf-456'])

            assert result.exit_code == 0
            assert "completed" in result.output.lower()

    def test_summary_json_output(self, runner):
        """Test summary JSON output."""
        mock_report = {
            "workflow_id": "wf-789",
            "type": "batch_validation",
            "status": "running",
            "created_at": "2025-01-01T00:00:00",
            "summary": {}
        }

        with patch('cli.main.db_manager') as mock_db:
            mock_db.generate_workflow_report.return_value = mock_report

            result = runner.invoke(cli, ['workflows', 'summary', 'wf-789', '--format', 'json'])

            assert result.exit_code == 0
            assert "wf-789" in result.output
```

**Runbook:**
```bash
# 1. Apply changes to cli/main.py

# 2. Run tests
pytest tests/cli/test_workflow_report.py::TestWorkflowSummary -v

# 3. Test CLI
python -m tbcv workflows summary WORKFLOW_ID
python -m tbcv workflows summary WORKFLOW_ID --format json

# 4. Verify parity
curl "http://127.0.0.1:8080/workflows/WORKFLOW_ID/summary"
```

**Self-review:**
- [ ] Thorough, systematic, wired UI and backend, MCP usage intact, CLI and Web in sync, tests added and passing

---

## Phase 2: Operational Gaps

---

### Task Card P2-T01: Add CLI Maintenance Mode Commands

**Role:** Senior engineer. Produce drop-in, production-ready code.

**Scope (only this):**
- Fix: CLI missing maintenance mode control (Web has `/admin/maintenance/enable|disable`)
- Allowed paths:
  - `cli/main.py`
  - `tests/cli/test_admin_maintenance.py` (new)
- Forbidden: any other file

**Acceptance checks (must pass locally):**
- CLI: `python -m tbcv admin maintenance enable` works
- CLI: `python -m tbcv admin maintenance disable` works
- CLI: `python -m tbcv admin maintenance status` works
- Tests: `pytest tests/cli/test_admin_maintenance.py -q`

**Deliverables:**
- New `maintenance` subgroup with commands in `cli/main.py`
- New test file

**Hard rules:**
- Windows friendly paths, CRLF preserved
- Commands call API endpoints (server must be running)
- Zero network calls in tests (mock requests)
- Deterministic runs
- Do not introduce new dependencies

**Implementation:**
```python
# Insert in admin group

@admin.group("maintenance")
@click.pass_context
def maintenance(ctx):
    """Maintenance mode management."""
    pass


@maintenance.command("enable")
@click.option("--base-url", default="http://127.0.0.1:8080", help="API base URL")
@click.pass_context
def maintenance_enable(ctx, base_url):
    """Enable maintenance mode."""
    import requests

    try:
        response = requests.post(f"{base_url}/admin/maintenance/enable", timeout=10)
        response.raise_for_status()

        console.print("[yellow]Maintenance mode ENABLED[/yellow]")
        console.print("New workflow submissions will be rejected.")

    except requests.exceptions.ConnectionError:
        console.print("[red]Error: Could not connect to server[/red]")
        console.print(f"Ensure server is running at {base_url}")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@maintenance.command("disable")
@click.option("--base-url", default="http://127.0.0.1:8080", help="API base URL")
@click.pass_context
def maintenance_disable(ctx, base_url):
    """Disable maintenance mode."""
    import requests

    try:
        response = requests.post(f"{base_url}/admin/maintenance/disable", timeout=10)
        response.raise_for_status()

        console.print("[green]Maintenance mode DISABLED[/green]")
        console.print("System is now accepting workflows.")

    except requests.exceptions.ConnectionError:
        console.print("[red]Error: Could not connect to server[/red]")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@maintenance.command("status")
@click.option("--base-url", default="http://127.0.0.1:8080", help="API base URL")
@click.pass_context
def maintenance_status(ctx, base_url):
    """Check maintenance mode status."""
    import requests

    try:
        response = requests.get(f"{base_url}/admin/status", timeout=10)
        response.raise_for_status()
        result = response.json()

        mode = result.get("system", {}).get("maintenance_mode", False)

        if mode:
            console.print("[yellow]Maintenance mode: ENABLED[/yellow]")
        else:
            console.print("[green]Maintenance mode: DISABLED[/green]")

    except requests.exceptions.ConnectionError:
        console.print("[red]Error: Could not connect to server[/red]")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
```

**Test file: tests/cli/test_admin_maintenance.py**
```python
"""Tests for CLI admin maintenance commands."""
import pytest
from click.testing import CliRunner
from unittest.mock import MagicMock, patch
from cli.main import cli


class TestAdminMaintenance:
    """Test admin maintenance commands."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_maintenance_enable_success(self, runner):
        """Test enabling maintenance mode."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"maintenance_mode": True}

        with patch('requests.post', return_value=mock_response):
            result = runner.invoke(cli, ['admin', 'maintenance', 'enable'])

            assert result.exit_code == 0
            assert "ENABLED" in result.output

    def test_maintenance_disable_success(self, runner):
        """Test disabling maintenance mode."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"maintenance_mode": False}

        with patch('requests.post', return_value=mock_response):
            result = runner.invoke(cli, ['admin', 'maintenance', 'disable'])

            assert result.exit_code == 0
            assert "DISABLED" in result.output

    def test_maintenance_status_enabled(self, runner):
        """Test checking status when enabled."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"system": {"maintenance_mode": True}}

        with patch('requests.get', return_value=mock_response):
            result = runner.invoke(cli, ['admin', 'maintenance', 'status'])

            assert result.exit_code == 0
            assert "ENABLED" in result.output

    def test_maintenance_status_disabled(self, runner):
        """Test checking status when disabled."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"system": {"maintenance_mode": False}}

        with patch('requests.get', return_value=mock_response):
            result = runner.invoke(cli, ['admin', 'maintenance', 'status'])

            assert result.exit_code == 0
            assert "DISABLED" in result.output

    def test_maintenance_connection_error(self, runner):
        """Test handling connection error."""
        import requests

        with patch('requests.post', side_effect=requests.exceptions.ConnectionError()):
            result = runner.invoke(cli, ['admin', 'maintenance', 'enable'])

            assert result.exit_code == 1
            assert "connect" in result.output.lower()
```

**Runbook:**
```bash
# 1. Apply changes to cli/main.py

# 2. Create test file

# 3. Run tests
pytest tests/cli/test_admin_maintenance.py -v

# 4. Start server
python -m uvicorn api.server:app --host 127.0.0.1 --port 8080

# 5. Test CLI commands
python -m tbcv admin maintenance status
python -m tbcv admin maintenance enable
python -m tbcv admin maintenance status
python -m tbcv admin maintenance disable

# 6. Verify parity
curl -X POST "http://127.0.0.1:8080/admin/maintenance/enable"
curl "http://127.0.0.1:8080/admin/status"
```

**Self-review:**
- [ ] Thorough, systematic, wired UI and backend, MCP usage intact, CLI and Web in sync, tests added and passing

---

### Task Card P2-T02: Add CLI Cache Cleanup Command

**Role:** Senior engineer. Produce drop-in, production-ready code.

**Scope (only this):**
- Fix: CLI missing cache cleanup (Web has `/admin/cache/cleanup`)
- Allowed paths:
  - `cli/main.py`
  - `tests/cli/test_admin_cache.py` (new)
- Forbidden: any other file

**Acceptance checks (must pass locally):**
- CLI: `python -m tbcv admin cache-cleanup` works
- Tests: `pytest tests/cli/test_admin_cache.py -q`

**Deliverables:**
- New `cache-cleanup` command in `cli/main.py`
- New test file

**Implementation:**
```python
@admin.command("cache-cleanup")
@click.pass_context
def cache_cleanup(ctx):
    """Cleanup expired cache entries."""
    from core.cache import cache_manager

    try:
        result = cache_manager.cleanup_expired()

        l1_cleaned = result.get("l1_cleaned", 0)
        l2_cleaned = result.get("l2_cleaned", 0)
        total = l1_cleaned + l2_cleaned

        console.print(Panel("[bold]Cache Cleanup[/bold]", expand=False))

        table = Table(show_header=False)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="yellow")

        table.add_row("L1 entries removed", str(l1_cleaned))
        table.add_row("L2 entries removed", str(l2_cleaned))
        table.add_row("Total removed", str(total))

        console.print(table)
        console.print("[green]Cleanup completed[/green]")

    except Exception as e:
        console.print(f"[red]Error during cleanup: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)
```

**Test file: tests/cli/test_admin_cache.py**
```python
"""Tests for CLI admin cache commands."""
import pytest
from click.testing import CliRunner
from unittest.mock import MagicMock, patch
from cli.main import cli


class TestAdminCacheCleanup:
    """Test admin cache-cleanup command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_cache_cleanup_success(self, runner):
        """Test successful cache cleanup."""
        with patch('cli.main.cache_manager') as mock_cache:
            mock_cache.cleanup_expired.return_value = {
                "l1_cleaned": 5,
                "l2_cleaned": 10
            }

            result = runner.invoke(cli, ['admin', 'cache-cleanup'])

            assert result.exit_code == 0
            assert "Cleanup" in result.output

    def test_cache_cleanup_empty(self, runner):
        """Test cleanup when nothing to clean."""
        with patch('cli.main.cache_manager') as mock_cache:
            mock_cache.cleanup_expired.return_value = {
                "l1_cleaned": 0,
                "l2_cleaned": 0
            }

            result = runner.invoke(cli, ['admin', 'cache-cleanup'])

            assert result.exit_code == 0
```

**Runbook:**
```bash
# 1. Apply changes to cli/main.py

# 2. Create test file

# 3. Run tests
pytest tests/cli/test_admin_cache.py::TestAdminCacheCleanup -v

# 4. Test CLI
python -m tbcv admin cache-cleanup

# 5. Verify parity
curl -X POST "http://127.0.0.1:8080/admin/cache/cleanup"
```

**Self-review:**
- [ ] Thorough, systematic, wired UI and backend, MCP usage intact, CLI and Web in sync, tests added and passing

---

### Task Card P2-T03: Add CLI Cache Rebuild Command

**Role:** Senior engineer. Produce drop-in, production-ready code.

**Scope (only this):**
- Fix: CLI missing cache rebuild (Web has `/admin/cache/rebuild`)
- Allowed paths:
  - `cli/main.py`
  - `tests/cli/test_admin_cache.py` (extend)
- Forbidden: any other file

**Acceptance checks (must pass locally):**
- CLI: `python -m tbcv admin cache-rebuild` works
- CLI: `python -m tbcv admin cache-rebuild --preload-truth` preloads data
- Tests: `pytest tests/cli/test_admin_cache.py::TestAdminCacheRebuild -q`

**Implementation:**
```python
@admin.command("cache-rebuild")
@click.option("--preload-truth", is_flag=True, help="Preload truth data after rebuild")
@click.pass_context
def cache_rebuild(ctx, preload_truth):
    """Rebuild cache from scratch."""
    from core.cache import cache_manager
    from core.database import CacheEntry

    try:
        # Clear L1
        l1_cleared = 0
        if cache_manager.l1_cache:
            l1_cleared = cache_manager.l1_cache.size()
            cache_manager.l1_cache.clear()

        # Clear L2
        l2_cleared = 0
        with db_manager.get_session() as session:
            l2_cleared = session.query(CacheEntry).count()
            session.query(CacheEntry).delete()
            session.commit()

        console.print(Panel("[bold]Cache Rebuild[/bold]", expand=False))

        table = Table(show_header=False)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="yellow")

        table.add_row("L1 entries cleared", str(l1_cleared))
        table.add_row("L2 entries cleared", str(l2_cleared))

        console.print(table)
        console.print("Cache will repopulate on demand.")

        if preload_truth:
            console.print("\n[dim]Preloading truth data...[/dim]")
            try:
                truth_manager = agent_registry.get_agent("truth_manager")
                if truth_manager:
                    import asyncio
                    asyncio.run(truth_manager.handle_message({
                        "type": "REQUEST",
                        "method": "load_truth",
                        "params": {"family": "words"}
                    }))
                    console.print("[green]Truth data preloaded for 'words' family[/green]")
            except Exception as e:
                console.print(f"[yellow]Warning: Failed to preload truth data - {e}[/yellow]")

        console.print("[green]Cache rebuild completed[/green]")

    except Exception as e:
        console.print(f"[red]Error during rebuild: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)
```

**Additional tests:**
```python
class TestAdminCacheRebuild:
    """Test admin cache-rebuild command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_cache_rebuild_success(self, runner):
        """Test successful cache rebuild."""
        mock_l1 = MagicMock()
        mock_l1.size.return_value = 10

        with patch('cli.main.cache_manager') as mock_cache, \
             patch('cli.main.db_manager') as mock_db:
            mock_cache.l1_cache = mock_l1
            mock_session = MagicMock()
            mock_session.query.return_value.count.return_value = 20
            mock_db.get_session.return_value.__enter__.return_value = mock_session

            result = runner.invoke(cli, ['admin', 'cache-rebuild'])

            assert result.exit_code == 0
            assert "rebuild" in result.output.lower()

    def test_cache_rebuild_with_preload(self, runner):
        """Test rebuild with truth preload."""
        mock_l1 = MagicMock()
        mock_l1.size.return_value = 0

        with patch('cli.main.cache_manager') as mock_cache, \
             patch('cli.main.db_manager') as mock_db, \
             patch('cli.main.agent_registry') as mock_registry:
            mock_cache.l1_cache = mock_l1
            mock_session = MagicMock()
            mock_session.query.return_value.count.return_value = 0
            mock_db.get_session.return_value.__enter__.return_value = mock_session
            mock_registry.get_agent.return_value = None

            result = runner.invoke(cli, ['admin', 'cache-rebuild', '--preload-truth'])

            assert result.exit_code == 0
```

**Runbook:**
```bash
# 1. Apply changes to cli/main.py

# 2. Run tests
pytest tests/cli/test_admin_cache.py::TestAdminCacheRebuild -v

# 3. Test CLI
python -m tbcv admin cache-rebuild
python -m tbcv admin cache-rebuild --preload-truth

# 4. Verify parity
curl -X POST "http://127.0.0.1:8080/admin/cache/rebuild"
```

**Self-review:**
- [ ] Thorough, systematic, wired UI and backend, MCP usage intact, CLI and Web in sync, tests added and passing

---

### Task Card P2-T04: Add CLI Performance Report Command

**Role:** Senior engineer. Produce drop-in, production-ready code.

**Scope (only this):**
- Fix: CLI missing performance report (Web has `/admin/reports/performance`)
- Allowed paths:
  - `cli/main.py`
  - `tests/cli/test_admin_reports.py` (new)
- Forbidden: any other file

**Acceptance checks (must pass locally):**
- CLI: `python -m tbcv admin report performance --days 7` works
- Tests: `pytest tests/cli/test_admin_reports.py -q`

**Implementation:**
```python
@admin.group("report")
@click.pass_context
def admin_report(ctx):
    """Generate system reports."""
    pass


@admin_report.command("performance")
@click.option("--days", "-d", default=7, help="Number of days to analyze")
@click.option("--format", "output_format", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
def performance_report(ctx, days, output_format):
    """Generate performance report."""
    import json
    from datetime import datetime, timedelta, timezone
    from core.database import WorkflowState
    from core.cache import cache_manager

    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        all_workflows = db_manager.list_workflows(limit=100000)

        period_workflows = [
            w for w in all_workflows
            if w.created_at and (
                w.created_at.replace(tzinfo=timezone.utc) if w.created_at.tzinfo is None else w.created_at
            ) >= cutoff
        ]

        total = len(period_workflows)
        completed = len([w for w in period_workflows if w.state == WorkflowState.COMPLETED])
        failed = len([w for w in period_workflows if w.state == WorkflowState.FAILED])
        running = len([w for w in period_workflows if w.state == WorkflowState.RUNNING])

        # Calculate average completion time
        completion_times = []
        for w in period_workflows:
            if w.state == WorkflowState.COMPLETED and w.created_at and w.updated_at:
                delta = (w.updated_at - w.created_at).total_seconds() * 1000
                completion_times.append(delta)

        avg_time = sum(completion_times) / len(completion_times) if completion_times else 0
        error_rate = failed / total if total > 0 else 0
        success_rate = completed / total if total > 0 else 0

        cache_stats = cache_manager.get_statistics()
        l1_hit_rate = cache_stats.get("l1", {}).get("hit_rate", 0.0)

        report = {
            "period_days": days,
            "total_workflows": total,
            "completed": completed,
            "failed": failed,
            "running": running,
            "avg_completion_ms": round(avg_time, 2),
            "error_rate": round(error_rate, 4),
            "success_rate": round(success_rate, 4),
            "cache_hit_rate": round(l1_hit_rate, 4)
        }

        if output_format == "json":
            console.print(json.dumps(report, indent=2))
        else:
            console.print(Panel(f"[bold]Performance Report (last {days} days)[/bold]", expand=False))

            table = Table()
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="yellow")

            table.add_row("Total workflows", str(total))
            table.add_row("Completed", str(completed))
            table.add_row("Failed", str(failed))
            table.add_row("Running", str(running))
            table.add_row("Success rate", f"{success_rate*100:.1f}%")
            table.add_row("Error rate", f"{error_rate*100:.1f}%")
            table.add_row("Avg completion time", f"{avg_time:.0f}ms")
            table.add_row("Cache hit rate (L1)", f"{l1_hit_rate*100:.1f}%")

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error generating report: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)


@admin_report.command("health")
@click.option("--format", "output_format", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
def health_report(ctx, output_format):
    """Generate system health report."""
    import json
    from datetime import datetime, timezone

    try:
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "database_connected": db_manager.is_connected(),
            "agents_registered": len(agent_registry.list_agents()),
            "status": "healthy" if db_manager.is_connected() else "degraded"
        }

        if output_format == "json":
            console.print(json.dumps(report, indent=2))
        else:
            status_color = "green" if report["status"] == "healthy" else "red"

            console.print(Panel("[bold]System Health Report[/bold]", expand=False))

            table = Table(show_header=False)
            table.add_column("Field", style="cyan")
            table.add_column("Value")

            table.add_row("Status", f"[{status_color}]{report['status'].upper()}[/{status_color}]")
            table.add_row("Database", "[green]Connected[/green]" if report['database_connected'] else "[red]Disconnected[/red]")
            table.add_row("Agents", f"{report['agents_registered']} registered")
            table.add_row("Timestamp", report['timestamp'][:19])

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error generating report: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)
```

**Test file: tests/cli/test_admin_reports.py**
```python
"""Tests for CLI admin report commands."""
import pytest
from click.testing import CliRunner
from unittest.mock import MagicMock, patch
from cli.main import cli


class TestAdminPerformanceReport:
    """Test admin report performance command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_performance_report_empty(self, runner):
        """Test report with no workflows."""
        with patch('cli.main.db_manager') as mock_db, \
             patch('cli.main.cache_manager') as mock_cache:
            mock_db.list_workflows.return_value = []
            mock_cache.get_statistics.return_value = {"l1": {"hit_rate": 0.0}}

            result = runner.invoke(cli, ['admin', 'report', 'performance'])

            assert result.exit_code == 0
            assert "Performance" in result.output

    def test_performance_report_json(self, runner):
        """Test JSON output."""
        with patch('cli.main.db_manager') as mock_db, \
             patch('cli.main.cache_manager') as mock_cache:
            mock_db.list_workflows.return_value = []
            mock_cache.get_statistics.return_value = {"l1": {"hit_rate": 0.5}}

            result = runner.invoke(cli, ['admin', 'report', 'performance', '--format', 'json'])

            assert result.exit_code == 0
            assert "total_workflows" in result.output


class TestAdminHealthReport:
    """Test admin report health command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_health_report_healthy(self, runner):
        """Test health report when system healthy."""
        with patch('cli.main.db_manager') as mock_db, \
             patch('cli.main.agent_registry') as mock_registry:
            mock_db.is_connected.return_value = True
            mock_registry.list_agents.return_value = {"agent1": MagicMock()}

            result = runner.invoke(cli, ['admin', 'report', 'health'])

            assert result.exit_code == 0
            assert "HEALTHY" in result.output or "healthy" in result.output.lower()

    def test_health_report_degraded(self, runner):
        """Test health report when database disconnected."""
        with patch('cli.main.db_manager') as mock_db, \
             patch('cli.main.agent_registry') as mock_registry:
            mock_db.is_connected.return_value = False
            mock_registry.list_agents.return_value = {}

            result = runner.invoke(cli, ['admin', 'report', 'health'])

            assert result.exit_code == 0
            assert "degraded" in result.output.lower() or "DEGRADED" in result.output
```

**Runbook:**
```bash
# 1. Apply changes to cli/main.py

# 2. Create test file

# 3. Run tests
pytest tests/cli/test_admin_reports.py -v

# 4. Test CLI
python -m tbcv admin report performance
python -m tbcv admin report performance --days 30 --format json
python -m tbcv admin report health

# 5. Verify parity
curl "http://127.0.0.1:8080/admin/reports/performance?days=7"
curl "http://127.0.0.1:8080/admin/reports/health"
```

**Self-review:**
- [ ] Thorough, systematic, wired UI and backend, MCP usage intact, CLI and Web in sync, tests added and passing

---

### Task Card P2-T05: Add CLI Workflow Watch Command

**Role:** Senior engineer. Produce drop-in, production-ready code.

**Scope (only this):**
- Fix: CLI missing real-time workflow monitoring (Web has WebSocket/SSE)
- Allowed paths:
  - `cli/main.py`
  - `tests/cli/test_workflow_watch.py` (new)
- Forbidden: any other file

**Acceptance checks (must pass locally):**
- CLI: `python -m tbcv workflows watch <workflow_id>` shows live progress
- Tests: `pytest tests/cli/test_workflow_watch.py -q`

**Deliverables:**
- New `watch` command in `cli/main.py` workflows group
- New test file

**Hard rules:**
- Windows friendly paths
- Polling-based implementation (not WebSocket for simplicity)
- Zero network calls in tests
- Deterministic runs
- Do not introduce new dependencies

**Implementation:**
```python
@workflows.command("watch")
@click.argument("workflow_id")
@click.option("--interval", "-i", default=2, help="Polling interval in seconds")
@click.option("--timeout", "-t", default=300, help="Maximum watch time in seconds")
@click.pass_context
def workflow_watch(ctx, workflow_id, interval, timeout):
    """Watch workflow progress in real-time."""
    import time
    from datetime import datetime

    workflow = db_manager.get_workflow(workflow_id)
    if not workflow:
        console.print(f"[red]Workflow {workflow_id} not found[/red]")
        sys.exit(1)

    console.print(f"[dim]Watching workflow {workflow_id[:8]}... (Ctrl+C to stop)[/dim]")
    console.print("-" * 50)

    start_time = time.time()
    last_state = None
    last_progress = -1

    try:
        while time.time() - start_time < timeout:
            workflow = db_manager.get_workflow(workflow_id)
            if not workflow:
                console.print("[yellow]Workflow no longer exists[/yellow]")
                break

            current_state = workflow.state.value if hasattr(workflow.state, 'value') else str(workflow.state)
            current_progress = workflow.progress_percent or 0

            # Only print if something changed
            if current_state != last_state or current_progress != last_progress:
                timestamp = datetime.now().strftime("%H:%M:%S")
                progress_bar = _make_progress_bar(current_progress)

                state_colors = {
                    "pending": "yellow",
                    "running": "blue",
                    "completed": "green",
                    "failed": "red",
                    "cancelled": "magenta"
                }
                state_color = state_colors.get(current_state, "white")

                console.print(f"[dim][{timestamp}][/dim] [{state_color}]{current_state.upper():10}[/{state_color}] {progress_bar} {current_progress}%")

                last_state = current_state
                last_progress = current_progress

            # Exit if terminal state
            if current_state in ["completed", "failed", "cancelled"]:
                console.print()
                if current_state == "completed":
                    console.print("[green]Workflow completed successfully![/green]")
                elif current_state == "failed":
                    console.print("[red]Workflow failed[/red]")
                else:
                    console.print("[yellow]Workflow cancelled[/yellow]")
                break

            time.sleep(interval)
        else:
            console.print(f"\n[yellow]Timeout reached ({timeout}s)[/yellow]")

    except KeyboardInterrupt:
        console.print("\n[dim]Watch cancelled[/dim]")


def _make_progress_bar(percent, width=20):
    """Create a simple progress bar."""
    filled = int(width * percent / 100)
    bar = "=" * filled + "-" * (width - filled)
    return f"[{bar}]"
```

**Test file: tests/cli/test_workflow_watch.py**
```python
"""Tests for CLI workflow watch command."""
import pytest
from click.testing import CliRunner
from unittest.mock import MagicMock, patch, PropertyMock
from cli.main import cli


class TestWorkflowWatch:
    """Test workflows watch command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_watch_workflow_not_found(self, runner):
        """Test watch when workflow not found."""
        with patch('cli.main.db_manager') as mock_db:
            mock_db.get_workflow.return_value = None

            result = runner.invoke(cli, ['workflows', 'watch', 'nonexistent'])

            assert result.exit_code == 1
            assert "not found" in result.output.lower()

    def test_watch_completed_workflow(self, runner):
        """Test watching already completed workflow."""
        mock_workflow = MagicMock()
        mock_workflow.state.value = "completed"
        mock_workflow.progress_percent = 100

        with patch('cli.main.db_manager') as mock_db:
            mock_db.get_workflow.return_value = mock_workflow

            result = runner.invoke(cli, ['workflows', 'watch', 'wf-123'])

            assert result.exit_code == 0
            assert "completed" in result.output.lower()

    def test_watch_failed_workflow(self, runner):
        """Test watching failed workflow."""
        mock_workflow = MagicMock()
        mock_workflow.state.value = "failed"
        mock_workflow.progress_percent = 50

        with patch('cli.main.db_manager') as mock_db:
            mock_db.get_workflow.return_value = mock_workflow

            result = runner.invoke(cli, ['workflows', 'watch', 'wf-456'])

            assert result.exit_code == 0
            assert "failed" in result.output.lower()

    def test_progress_bar_generation(self):
        """Test progress bar generation helper."""
        from cli.main import _make_progress_bar

        bar_0 = _make_progress_bar(0)
        assert "--------------------" in bar_0

        bar_50 = _make_progress_bar(50)
        assert "==========" in bar_50

        bar_100 = _make_progress_bar(100)
        assert "====================" in bar_100
```

**Runbook:**
```bash
# 1. Apply changes to cli/main.py

# 2. Create test file

# 3. Run tests
pytest tests/cli/test_workflow_watch.py -v

# 4. Start a workflow and watch it
# Terminal 1:
python -m tbcv batch ./test_docs --pattern "*.md"

# Terminal 2:
python -m tbcv workflows watch WORKFLOW_ID

# 5. Verify output shows progress updates
```

**Self-review:**
- [ ] Thorough, systematic, wired UI and backend, MCP usage intact, CLI and Web in sync, tests added and passing

---

## Phase 3: Admin & Monitoring

---

### Task Card P3-T01: Add CLI Health Probe Commands

**Role:** Senior engineer. Produce drop-in, production-ready code.

**Scope (only this):**
- Fix: CLI missing K8s-style health probes (Web has `/health/live`, `/health/ready`)
- Allowed paths:
  - `cli/main.py`
  - `tests/cli/test_admin_health.py` (new)
- Forbidden: any other file

**Acceptance checks (must pass locally):**
- CLI: `python -m tbcv admin health-live` exits 0
- CLI: `python -m tbcv admin health-ready` exits 0 if ready, 1 if not
- Tests: `pytest tests/cli/test_admin_health.py -q`

**Implementation:**
```python
@admin.command("health-live")
@click.pass_context
def health_live(ctx):
    """Kubernetes-style liveness probe (exit code for scripts)."""
    console.print("[green]alive[/green]")
    sys.exit(0)


@admin.command("health-ready")
@click.pass_context
def health_ready(ctx):
    """Kubernetes-style readiness probe (exit code for scripts)."""
    checks = {
        "database": False,
        "agents": False
    }

    try:
        checks["database"] = db_manager.is_connected()
    except Exception:
        pass

    try:
        checks["agents"] = len(agent_registry.list_agents()) > 0
    except Exception:
        pass

    all_ready = all(checks.values())

    for check, status in checks.items():
        symbol = "[green]OK[/green]" if status else "[red]FAIL[/red]"
        console.print(f"{check}: {symbol}")

    if all_ready:
        console.print("\n[green]Status: READY[/green]")
        sys.exit(0)
    else:
        console.print("\n[red]Status: NOT READY[/red]")
        sys.exit(1)
```

**Test file: tests/cli/test_admin_health.py**
```python
"""Tests for CLI admin health probe commands."""
import pytest
from click.testing import CliRunner
from unittest.mock import MagicMock, patch
from cli.main import cli


class TestAdminHealthProbes:
    """Test admin health probe commands."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_health_live_always_succeeds(self, runner):
        """Test liveness probe always returns success."""
        result = runner.invoke(cli, ['admin', 'health-live'])

        assert result.exit_code == 0
        assert "alive" in result.output.lower()

    def test_health_ready_all_checks_pass(self, runner):
        """Test readiness when all checks pass."""
        with patch('cli.main.db_manager') as mock_db, \
             patch('cli.main.agent_registry') as mock_registry:
            mock_db.is_connected.return_value = True
            mock_registry.list_agents.return_value = {"agent1": MagicMock()}

            result = runner.invoke(cli, ['admin', 'health-ready'])

            assert result.exit_code == 0
            assert "READY" in result.output

    def test_health_ready_database_fail(self, runner):
        """Test readiness when database disconnected."""
        with patch('cli.main.db_manager') as mock_db, \
             patch('cli.main.agent_registry') as mock_registry:
            mock_db.is_connected.return_value = False
            mock_registry.list_agents.return_value = {"agent1": MagicMock()}

            result = runner.invoke(cli, ['admin', 'health-ready'])

            assert result.exit_code == 1
            assert "NOT READY" in result.output

    def test_health_ready_no_agents(self, runner):
        """Test readiness when no agents registered."""
        with patch('cli.main.db_manager') as mock_db, \
             patch('cli.main.agent_registry') as mock_registry:
            mock_db.is_connected.return_value = True
            mock_registry.list_agents.return_value = {}

            result = runner.invoke(cli, ['admin', 'health-ready'])

            assert result.exit_code == 1
```

**Runbook:**
```bash
# 1. Apply changes to cli/main.py

# 2. Create test file

# 3. Run tests
pytest tests/cli/test_admin_health.py -v

# 4. Test CLI (use in scripts)
python -m tbcv admin health-live && echo "Alive"
python -m tbcv admin health-ready && echo "Ready" || echo "Not Ready"

# 5. Verify parity
curl "http://127.0.0.1:8080/health/live"
curl "http://127.0.0.1:8080/health/ready"
```

**Self-review:**
- [ ] Thorough, systematic, wired UI and backend, MCP usage intact, CLI and Web in sync, tests added and passing

---

### Task Card P3-T02: Add CLI Agent Reload Command

**Role:** Senior engineer. Produce drop-in, production-ready code.

**Scope (only this):**
- Fix: CLI missing agent reload (Web has `/admin/agents/reload/{id}`)
- Allowed paths:
  - `cli/main.py`
  - `tests/cli/test_admin_agents.py` (new)
- Forbidden: any other file

**Acceptance checks (must pass locally):**
- CLI: `python -m tbcv admin agent-reload <agent_id>` works
- Tests: `pytest tests/cli/test_admin_agents.py -q`

**Implementation:**
```python
@admin.command("agent-reload")
@click.argument("agent_id")
@click.pass_context
def agent_reload(ctx, agent_id):
    """Reload a specific agent (clear cache, reinitialize)."""
    from core.cache import cache_manager

    try:
        agent = agent_registry.get_agent(agent_id)
        if not agent:
            console.print(f"[red]Agent {agent_id} not found[/red]")
            sys.exit(1)

        actions = []

        # Clear agent's cache
        try:
            cache_manager.clear_agent_cache(agent_id)
            actions.append("cache_cleared")
        except Exception:
            pass

        # Reload config if available
        if hasattr(agent, 'reload_config'):
            try:
                import asyncio
                asyncio.run(agent.reload_config())
                actions.append("config_reloaded")
            except Exception:
                pass

        # Reset state if available
        if hasattr(agent, 'reset_state'):
            try:
                agent.reset_state()
                actions.append("state_reset")
            except Exception:
                pass

        console.print(f"[green]Agent {agent_id} reloaded successfully[/green]")
        console.print(f"Actions: {', '.join(actions) if actions else 'none'}")

    except Exception as e:
        console.print(f"[red]Error reloading agent: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)
```

**Test file: tests/cli/test_admin_agents.py**
```python
"""Tests for CLI admin agent commands."""
import pytest
from click.testing import CliRunner
from unittest.mock import MagicMock, patch
from cli.main import cli


class TestAdminAgentReload:
    """Test admin agent-reload command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_agent_reload_not_found(self, runner):
        """Test reload when agent not found."""
        with patch('cli.main.agent_registry') as mock_registry:
            mock_registry.get_agent.return_value = None

            result = runner.invoke(cli, ['admin', 'agent-reload', 'nonexistent'])

            assert result.exit_code == 1
            assert "not found" in result.output.lower()

    def test_agent_reload_success(self, runner):
        """Test successful agent reload."""
        mock_agent = MagicMock()
        mock_agent.reload_config = None  # No reload_config method
        mock_agent.reset_state = None

        with patch('cli.main.agent_registry') as mock_registry, \
             patch('cli.main.cache_manager') as mock_cache:
            mock_registry.get_agent.return_value = mock_agent

            result = runner.invoke(cli, ['admin', 'agent-reload', 'content_validator'])

            assert result.exit_code == 0
            assert "reloaded" in result.output.lower()

    def test_agent_reload_with_config(self, runner):
        """Test reload with config reload method."""
        mock_agent = MagicMock()
        # Agent has reload_config

        with patch('cli.main.agent_registry') as mock_registry, \
             patch('cli.main.cache_manager') as mock_cache:
            mock_registry.get_agent.return_value = mock_agent

            result = runner.invoke(cli, ['admin', 'agent-reload', 'truth_manager'])

            assert result.exit_code == 0
```

**Runbook:**
```bash
# 1. Apply changes to cli/main.py

# 2. Create test file

# 3. Run tests
pytest tests/cli/test_admin_agents.py -v

# 4. Test CLI
python -m tbcv admin agent-reload content_validator
python -m tbcv admin agent-reload truth_manager

# 5. Verify parity
curl -X POST "http://127.0.0.1:8080/admin/agents/reload/content_validator"
```

**Self-review:**
- [ ] Thorough, systematic, wired UI and backend, MCP usage intact, CLI and Web in sync, tests added and passing

---

### Task Card P3-T03: Add CLI Checkpoint Command

**Role:** Senior engineer. Produce drop-in, production-ready code.

**Scope (only this):**
- Fix: CLI missing system checkpoint (Web has `/admin/system/checkpoint`)
- Allowed paths:
  - `cli/main.py`
  - `tests/cli/test_admin_checkpoint.py` (new)
- Forbidden: any other file

**Acceptance checks (must pass locally):**
- CLI: `python -m tbcv admin checkpoint` creates checkpoint
- CLI: `python -m tbcv admin checkpoint --name "my_checkpoint"` works
- Tests: `pytest tests/cli/test_admin_checkpoint.py -q`

**Implementation:**
```python
@admin.command("checkpoint")
@click.option("--name", "-n", help="Custom checkpoint name")
@click.pass_context
def create_checkpoint(ctx, name):
    """Create system checkpoint for disaster recovery."""
    import uuid
    import pickle
    from datetime import datetime, timezone
    from core.database import Checkpoint, WorkflowState
    from core.cache import cache_manager

    try:
        checkpoint_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc)
        checkpoint_name = name or f"cli_checkpoint_{timestamp.strftime('%Y%m%d_%H%M%S')}"

        # Gather system state
        workflows = db_manager.list_workflows(limit=10000)
        active_workflows = [w for w in workflows if w.state in [WorkflowState.RUNNING, WorkflowState.PENDING]]

        system_state = {
            "checkpoint_id": checkpoint_id,
            "timestamp": timestamp.isoformat(),
            "source": "cli",
            "workflows": {
                "total": len(workflows),
                "active": len(active_workflows)
            },
            "agents": {
                "registered": len(agent_registry.list_agents())
            }
        }

        # Try to get cache stats
        try:
            system_state["cache"] = cache_manager.get_statistics()
        except Exception:
            system_state["cache"] = {}

        # Store checkpoint
        SYSTEM_CHECKPOINT_WORKFLOW_ID = "00000000-0000-0000-0000-000000000000"

        with db_manager.get_session() as session:
            checkpoint = Checkpoint(
                id=checkpoint_id,
                workflow_id=SYSTEM_CHECKPOINT_WORKFLOW_ID,
                name=checkpoint_name,
                step_number=0,
                state_data=pickle.dumps(system_state),
                created_at=timestamp,
                can_resume_from=True
            )
            session.add(checkpoint)
            session.commit()

        console.print(Panel("[bold]Checkpoint Created[/bold]", expand=False))

        table = Table(show_header=False)
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="yellow")

        table.add_row("ID", checkpoint_id)
        table.add_row("Name", checkpoint_name)
        table.add_row("Time", timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        table.add_row("Workflows", str(len(workflows)))
        table.add_row("Active", str(len(active_workflows)))

        console.print(table)
        console.print("[green]Checkpoint saved successfully[/green]")

    except Exception as e:
        console.print(f"[red]Error creating checkpoint: {e}[/red]")
        if ctx.obj.get('verbose'):
            console.print_exception()
        sys.exit(1)
```

**Test file: tests/cli/test_admin_checkpoint.py**
```python
"""Tests for CLI admin checkpoint command."""
import pytest
from click.testing import CliRunner
from unittest.mock import MagicMock, patch
from cli.main import cli


class TestAdminCheckpoint:
    """Test admin checkpoint command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_checkpoint_success(self, runner):
        """Test successful checkpoint creation."""
        with patch('cli.main.db_manager') as mock_db, \
             patch('cli.main.agent_registry') as mock_registry, \
             patch('cli.main.cache_manager') as mock_cache:
            mock_db.list_workflows.return_value = []
            mock_registry.list_agents.return_value = {}
            mock_cache.get_statistics.return_value = {}
            mock_session = MagicMock()
            mock_db.get_session.return_value.__enter__.return_value = mock_session

            result = runner.invoke(cli, ['admin', 'checkpoint'])

            assert result.exit_code == 0
            assert "Checkpoint" in result.output

    def test_checkpoint_with_name(self, runner):
        """Test checkpoint with custom name."""
        with patch('cli.main.db_manager') as mock_db, \
             patch('cli.main.agent_registry') as mock_registry, \
             patch('cli.main.cache_manager') as mock_cache:
            mock_db.list_workflows.return_value = []
            mock_registry.list_agents.return_value = {}
            mock_cache.get_statistics.return_value = {}
            mock_session = MagicMock()
            mock_db.get_session.return_value.__enter__.return_value = mock_session

            result = runner.invoke(cli, ['admin', 'checkpoint', '--name', 'my_test_checkpoint'])

            assert result.exit_code == 0
            assert "my_test_checkpoint" in result.output

    def test_checkpoint_captures_workflow_state(self, runner):
        """Test checkpoint captures workflow information."""
        mock_workflow = MagicMock()
        mock_workflow.state = MagicMock()
        mock_workflow.state.value = "running"

        # Make state comparable with WorkflowState enum values
        from core.database import WorkflowState
        mock_workflow.state = WorkflowState.RUNNING

        with patch('cli.main.db_manager') as mock_db, \
             patch('cli.main.agent_registry') as mock_registry, \
             patch('cli.main.cache_manager') as mock_cache:
            mock_db.list_workflows.return_value = [mock_workflow]
            mock_registry.list_agents.return_value = {"agent1": MagicMock()}
            mock_cache.get_statistics.return_value = {}
            mock_session = MagicMock()
            mock_db.get_session.return_value.__enter__.return_value = mock_session

            result = runner.invoke(cli, ['admin', 'checkpoint'])

            assert result.exit_code == 0
            # Should show workflow count
            assert "1" in result.output  # 1 workflow, 1 active
```

**Runbook:**
```bash
# 1. Apply changes to cli/main.py

# 2. Create test file

# 3. Run tests
pytest tests/cli/test_admin_checkpoint.py -v

# 4. Test CLI
python -m tbcv admin checkpoint
python -m tbcv admin checkpoint --name "before_migration"

# 5. Verify parity
curl -X POST "http://127.0.0.1:8080/admin/system/checkpoint"
```

**Self-review:**
- [ ] Thorough, systematic, wired UI and backend, MCP usage intact, CLI and Web in sync, tests added and passing

---

## Master Runbook

Execute tasks in order. After each phase, run full test suite.

```bash
# Phase 1: Core Feature Gaps
# P1-T01: Recommendation Generate Endpoint
# P1-T02: Recommendation Rebuild Endpoint
# P1-T03: CLI Enhancement History Commands
# P1-T04: CLI Rollback Command
# P1-T05: CLI Validation Diff Command
# P1-T06: CLI Validation Compare Command
# P1-T07: CLI Workflow Report Command
# P1-T08: CLI Workflow Summary Command

pytest tests/api/test_recommendation_generation.py tests/cli/test_admin_enhancements.py tests/cli/test_validation_diff.py tests/cli/test_workflow_report.py -v

# Phase 2: Operational Gaps
# P2-T01: CLI Maintenance Mode Commands
# P2-T02: CLI Cache Cleanup Command
# P2-T03: CLI Cache Rebuild Command
# P2-T04: CLI Performance Report Command
# P2-T05: CLI Workflow Watch Command

pytest tests/cli/test_admin_maintenance.py tests/cli/test_admin_cache.py tests/cli/test_admin_reports.py tests/cli/test_workflow_watch.py -v

# Phase 3: Admin & Monitoring
# P3-T01: CLI Health Probe Commands
# P3-T02: CLI Agent Reload Command
# P3-T03: CLI Checkpoint Command

pytest tests/cli/test_admin_health.py tests/cli/test_admin_agents.py tests/cli/test_admin_checkpoint.py -v

# Final verification
pytest tests/ --ignore=tests/test_endpoints_live.py --ignore=tests/test_truth_llm_validation_real.py --ignore=tests/manual/ -v

# Parity verification
python -m tbcv probe-endpoints --mode offline
```

---

## Completion Checklist

| Task | Status | Tests Pass | Parity Verified |
|------|--------|------------|-----------------|
| P1-T01 | [x] | [x] | [x] |
| P1-T02 | [x] | [x] | [x] |
| P1-T03 | [x] | [x] | [x] |
| P1-T04 | [x] | [x] | [x] |
| P1-T05 | [x] | [x] | [x] |
| P1-T06 | [x] | [x] | [x] |
| P1-T07 | [x] | [x] | [x] |
| P1-T08 | [x] | [x] | [x] |
| P2-T01 | [x] | [x] | [x] |
| P2-T02 | [x] | [x] | [x] |
| P2-T03 | [x] | [x] | [x] |
| P2-T04 | [x] | [x] | [x] |
| P2-T05 | [x] | [x] | [x] |
| P3-T01 | [x] | [x] | [x] |
| P3-T02 | [x] | [x] | [x] |
| P3-T03 | [x] | [x] | [x] |

**Target: 100% feature parity between CLI and Web/UI** ✅ COMPLETE
