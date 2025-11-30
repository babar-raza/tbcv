# CLI/Web Parity Implementation Plan

**Goal:** Achieve 1:1 feature parity between CLI and Web/UI surfaces
**Current Parity:** 60% full, 33% partial, 7% CLI-only, 7% Web-only
**Target Parity:** 100%

---

## Executive Summary

This plan addresses 13 identified gaps between CLI and Web/UI surfaces. Implementation is organized into 4 phases:

| Phase | Focus | Gaps Addressed | Estimated Tasks |
|-------|-------|----------------|-----------------|
| Phase 1 | Core Feature Gaps | 4 | 12 tasks |
| Phase 2 | Operational Gaps | 4 | 10 tasks |
| Phase 3 | Admin & Monitoring | 3 | 8 tasks |
| Phase 4 | Developer Tools | 2 | 4 tasks |

---

## Phase 1: Core Feature Gaps (High Priority)

### 1.1 Add Recommendation Generation Endpoints to Web (GAP_006)

**Current State:** CLI has `recommendations generate` and `recommendations rebuild` commands. Web only auto-generates during validation.

**Target State:** Web has explicit endpoints to generate/rebuild recommendations on demand.

#### Task 1.1.1: Add POST /api/recommendations/generate endpoint

**File:** `api/server.py`
**Location:** After line 2455 (after bulk_review_recommendations)

```python
@app.post("/api/recommendations/{validation_id}/generate")
async def generate_recommendations_for_validation(
    validation_id: str,
    force: bool = Query(False, description="Force regeneration even if recommendations exist")
):
    """
    Generate recommendations for a validation result.

    Args:
        validation_id: The validation to generate recommendations for
        force: If True, regenerate even if recommendations already exist
    """
    try:
        # Get validation
        validation = db_manager.get_validation_result(validation_id)
        if not validation:
            raise HTTPException(status_code=404, detail="Validation not found")

        # Check existing recommendations
        existing = db_manager.list_recommendations(validation_id=validation_id)
        if existing and not force:
            return {
                "success": False,
                "message": f"Validation already has {len(existing)} recommendations. Use force=true to regenerate.",
                "existing_count": len(existing)
            }

        # Get recommendation agent
        rec_agent = agent_registry.get_agent("recommendation_agent")
        if not rec_agent:
            raise HTTPException(status_code=500, detail="Recommendation agent not available")

        # Generate recommendations
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

#### Task 1.1.2: Add POST /api/recommendations/{id}/rebuild endpoint

**File:** `api/server.py`
**Location:** After the generate endpoint

```python
@app.post("/api/recommendations/{validation_id}/rebuild")
async def rebuild_recommendations_for_validation(validation_id: str):
    """
    Delete existing recommendations and regenerate from scratch.
    """
    try:
        # Delete existing recommendations
        existing = db_manager.list_recommendations(validation_id=validation_id)
        deleted_count = 0
        for rec in existing:
            if db_manager.delete_recommendation(rec.id):
                deleted_count += 1

        # Generate new recommendations (reuse generate endpoint logic)
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

#### Task 1.1.3: Add UI button for recommendation generation

**File:** `templates/validation_detail_enhanced.html`
**Change:** Add "Generate Recommendations" button in the recommendations section

---

### 1.2 Add Audit/Rollback Commands to CLI (GAP_007)

**Current State:** Web has `/api/audit/enhancements` and `/api/audit/rollback`. CLI has no equivalent.

**Target State:** CLI has `admin enhancements` and `admin rollback` commands.

#### Task 1.2.1: Add `admin enhancements` command

**File:** `cli/main.py`
**Location:** Inside `admin` group (after line 2012)

```python
@admin.command("enhancements")
@click.option("--file-path", "-f", help="Filter by file path")
@click.option("--limit", "-l", default=50, help="Maximum records to show")
@click.option("--format", "output_format", type=click.Choice(["table", "json"]), default="table")
@click.pass_context
def list_enhancements(ctx, file_path, limit, output_format):
    """List enhancement history records."""
    from agents.enhancement_history import get_history_manager

    history = get_history_manager()
    records = history.list_enhancements(file_path=file_path, limit=limit)

    if output_format == "json":
        import json
        click.echo(json.dumps([r.to_dict() for r in records], indent=2, default=str))
    else:
        if not records:
            click.echo("No enhancement records found.")
            return

        click.echo(f"\nEnhancement History ({len(records)} records):\n")
        click.echo("-" * 100)
        click.echo(f"{'ID':<36} {'File':<30} {'Status':<12} {'Created':<20}")
        click.echo("-" * 100)

        for r in records:
            file_display = r.file_path[:27] + "..." if len(r.file_path) > 30 else r.file_path
            click.echo(f"{r.id:<36} {file_display:<30} {r.status:<12} {str(r.created_at)[:19]:<20}")
```

#### Task 1.2.2: Add `admin rollback` command

**File:** `cli/main.py`
**Location:** After enhancements command

```python
@admin.command("rollback")
@click.argument("enhancement_id")
@click.option("--confirm", is_flag=True, help="Confirm rollback operation")
@click.option("--rolled-back-by", default="cli_user", help="User performing rollback")
@click.pass_context
def rollback_enhancement(ctx, enhancement_id, confirm, rolled_back_by):
    """Rollback an enhancement to restore original content."""
    from agents.enhancement_history import get_history_manager

    if not confirm:
        click.echo("Rollback requires confirmation. Use --confirm flag.")
        click.echo(f"\nTo rollback enhancement {enhancement_id}:")
        click.echo(f"  tbcv admin rollback {enhancement_id} --confirm")
        return

    history = get_history_manager()

    # First show what will be rolled back
    record = history.get_enhancement_record(enhancement_id)
    if not record:
        click.echo(f"Error: Enhancement {enhancement_id} not found", err=True)
        raise SystemExit(1)

    click.echo(f"\nRolling back enhancement:")
    click.echo(f"  ID: {record.id}")
    click.echo(f"  File: {record.file_path}")
    click.echo(f"  Created: {record.created_at}")

    success = history.rollback_enhancement(enhancement_id, rolled_back_by)

    if success:
        click.echo(click.style("\nRollback successful!", fg="green"))
    else:
        click.echo(click.style("\nRollback failed - point not found or expired", fg="red"), err=True)
        raise SystemExit(1)
```

#### Task 1.2.3: Add `admin enhancement-detail` command

**File:** `cli/main.py`

```python
@admin.command("enhancement-detail")
@click.argument("enhancement_id")
@click.option("--format", "output_format", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
def get_enhancement_detail(ctx, enhancement_id, output_format):
    """Get detailed information about a specific enhancement."""
    from agents.enhancement_history import get_history_manager

    history = get_history_manager()
    record = history.get_enhancement_record(enhancement_id)

    if not record:
        click.echo(f"Enhancement {enhancement_id} not found", err=True)
        raise SystemExit(1)

    if output_format == "json":
        import json
        click.echo(json.dumps(record.to_dict(), indent=2, default=str))
    else:
        click.echo(f"\nEnhancement Detail:")
        click.echo("-" * 50)
        click.echo(f"ID:          {record.id}")
        click.echo(f"File:        {record.file_path}")
        click.echo(f"Status:      {record.status}")
        click.echo(f"Created:     {record.created_at}")
        click.echo(f"Enhanced by: {record.enhanced_by}")
        if record.rollback_expires_at:
            click.echo(f"Rollback expires: {record.rollback_expires_at}")
```

---

### 1.3 Add Validation Diff/Compare Commands to CLI (GAP_001)

**Current State:** Web has `/api/validations/{id}/diff` and `/api/validations/{id}/enhancement-comparison`. CLI has no equivalent.

**Target State:** CLI has `validations diff` and `validations compare` commands.

#### Task 1.3.1: Add `validations diff` command

**File:** `cli/main.py`
**Location:** Inside `validations` group (after history command, ~line 1544)

```python
@validations.command("diff")
@click.argument("validation_id")
@click.option("--format", "output_format", type=click.Choice(["unified", "side-by-side", "json"]), default="unified")
@click.option("--context", "-c", default=3, help="Lines of context for unified diff")
@click.pass_context
def validation_diff(ctx, validation_id, output_format, context):
    """Show content diff for an enhanced validation."""
    import difflib
    import json

    validation = db_manager.get_validation_result(validation_id)
    if not validation:
        click.echo(f"Validation {validation_id} not found", err=True)
        raise SystemExit(1)

    results = validation.validation_results or {}
    original = results.get("original_content")
    enhanced = results.get("enhanced_content")

    if not original or not enhanced:
        click.echo("No diff available - validation may not have been enhanced yet", err=True)
        raise SystemExit(1)

    if output_format == "json":
        diff_data = {
            "validation_id": validation_id,
            "file_path": validation.file_path,
            "has_diff": original != enhanced,
            "original_lines": len(original.splitlines()),
            "enhanced_lines": len(enhanced.splitlines())
        }
        click.echo(json.dumps(diff_data, indent=2))
    elif output_format == "unified":
        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            enhanced.splitlines(keepends=True),
            fromfile="Original",
            tofile="Enhanced",
            n=context
        )
        for line in diff:
            if line.startswith("+") and not line.startswith("+++"):
                click.echo(click.style(line.rstrip(), fg="green"))
            elif line.startswith("-") and not line.startswith("---"):
                click.echo(click.style(line.rstrip(), fg="red"))
            elif line.startswith("@@"):
                click.echo(click.style(line.rstrip(), fg="cyan"))
            else:
                click.echo(line.rstrip())
    else:  # side-by-side
        # Simple side-by-side implementation
        orig_lines = original.splitlines()
        enh_lines = enhanced.splitlines()
        max_lines = max(len(orig_lines), len(enh_lines))

        click.echo(f"{'ORIGINAL':<40} | {'ENHANCED':<40}")
        click.echo("-" * 83)

        for i in range(max_lines):
            orig = orig_lines[i][:37] + "..." if i < len(orig_lines) and len(orig_lines[i]) > 40 else (orig_lines[i] if i < len(orig_lines) else "")
            enh = enh_lines[i][:37] + "..." if i < len(enh_lines) and len(enh_lines[i]) > 40 else (enh_lines[i] if i < len(enh_lines) else "")
            click.echo(f"{orig:<40} | {enh:<40}")
```

#### Task 1.3.2: Add `validations compare` command

**File:** `cli/main.py`

```python
@validations.command("compare")
@click.argument("validation_id")
@click.option("--format", "output_format", type=click.Choice(["summary", "detailed", "json"]), default="summary")
@click.pass_context
def validation_compare(ctx, validation_id, output_format):
    """Show comprehensive enhancement comparison with statistics."""
    import json

    validation = db_manager.get_validation_result(validation_id)
    if not validation:
        click.echo(f"Validation {validation_id} not found", err=True)
        raise SystemExit(1)

    results = validation.validation_results or {}
    original = results.get("original_content", "")
    enhanced = results.get("enhanced_content", "")

    if not original or not enhanced:
        click.echo("No comparison available - validation not enhanced", err=True)
        raise SystemExit(1)

    # Calculate statistics
    orig_lines = original.splitlines()
    enh_lines = enhanced.splitlines()

    import difflib
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
        click.echo(json.dumps(stats, indent=2))
    else:
        click.echo(f"\nEnhancement Comparison for {validation_id[:8]}...")
        click.echo("=" * 50)
        click.echo(f"File: {validation.file_path}")
        click.echo(f"\nStatistics:")
        click.echo(f"  Original lines:    {stats['original_lines']}")
        click.echo(f"  Enhanced lines:    {stats['enhanced_lines']}")
        click.echo(f"  Lines added:       {click.style(f'+{stats['lines_added']}', fg='green')}")
        click.echo(f"  Lines removed:     {click.style(f'-{stats['lines_removed']}', fg='red')}")
        click.echo(f"  Lines modified:    {stats['lines_modified']}")
        click.echo(f"  Similarity:        {stats['similarity_ratio']*100:.1f}%")
        click.echo(f"  Recommendations:   {stats['applied_recommendations']} applied")
```

---

### 1.4 Add Workflow Report/Summary Commands to CLI (GAP_002)

**Current State:** Web has `/workflows/{id}/report` and `/workflows/{id}/summary`. CLI only has `workflows show`.

**Target State:** CLI has `workflows report` and `workflows summary` commands.

#### Task 1.4.1: Add `workflows report` command

**File:** `cli/main.py`
**Location:** Inside `workflows` group (after show command, ~line 1650)

```python
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
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)

    if output_format == "json":
        content = json.dumps(report, indent=2, default=str)
    elif output_format == "markdown":
        content = _format_workflow_report_markdown(report)
    else:
        content = _format_workflow_report_text(report)

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(content)
        click.echo(f"Report saved to {output}")
    else:
        click.echo(content)


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

    return "\n".join(lines)
```

#### Task 1.4.2: Add `workflows summary` command

**File:** `cli/main.py`

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
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)

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
        click.echo(json.dumps(summary, indent=2, default=str))
    else:
        s = summary["summary"]
        click.echo(f"\nWorkflow Summary: {workflow_id[:8]}...")
        click.echo("-" * 40)
        click.echo(f"Status:          {summary['status']}")
        click.echo(f"Validations:     {s.get('total_validations', 0)} ({s.get('passed', 0)} passed, {s.get('failed', 0)} failed)")
        click.echo(f"Recommendations: {s.get('total_recommendations', 0)} ({s.get('recommendations_applied', 0)} applied)")
```

---

## Phase 2: Operational Gaps (Medium Priority)

### 2.1 Add Maintenance Mode Commands to CLI (GAP_008)

**File:** `cli/main.py`
**Location:** Inside `admin` group

#### Task 2.1.1: Add maintenance subgroup

```python
@admin.group("maintenance")
@click.pass_context
def maintenance(ctx):
    """Maintenance mode management."""
    pass


@maintenance.command("enable")
@click.pass_context
def maintenance_enable(ctx):
    """Enable maintenance mode."""
    import requests

    base_url = ctx.obj.get("base_url", "http://127.0.0.1:8080")
    try:
        response = requests.post(f"{base_url}/admin/maintenance/enable")
        response.raise_for_status()
        result = response.json()
        click.echo(click.style("Maintenance mode ENABLED", fg="yellow"))
        click.echo("New workflow submissions will be rejected.")
    except requests.RequestException as e:
        click.echo(f"Error: Could not connect to server - {e}", err=True)
        raise SystemExit(1)


@maintenance.command("disable")
@click.pass_context
def maintenance_disable(ctx):
    """Disable maintenance mode."""
    import requests

    base_url = ctx.obj.get("base_url", "http://127.0.0.1:8080")
    try:
        response = requests.post(f"{base_url}/admin/maintenance/disable")
        response.raise_for_status()
        click.echo(click.style("Maintenance mode DISABLED", fg="green"))
        click.echo("System is now accepting workflows.")
    except requests.RequestException as e:
        click.echo(f"Error: Could not connect to server - {e}", err=True)
        raise SystemExit(1)


@maintenance.command("status")
@click.pass_context
def maintenance_status(ctx):
    """Check maintenance mode status."""
    import requests

    base_url = ctx.obj.get("base_url", "http://127.0.0.1:8080")
    try:
        response = requests.get(f"{base_url}/admin/status")
        response.raise_for_status()
        result = response.json()
        mode = result.get("system", {}).get("maintenance_mode", False)

        if mode:
            click.echo(click.style("Maintenance mode: ENABLED", fg="yellow"))
        else:
            click.echo(click.style("Maintenance mode: DISABLED", fg="green"))
    except requests.RequestException as e:
        click.echo(f"Error: Could not connect to server - {e}", err=True)
        raise SystemExit(1)
```

---

### 2.2 Add Cache Cleanup/Rebuild Commands to CLI (GAP_004)

**File:** `cli/main.py`
**Location:** Inside `admin` group, after existing cache commands

#### Task 2.2.1: Add `cache-cleanup` command

```python
@admin.command("cache-cleanup")
@click.pass_context
def cache_cleanup(ctx):
    """Cleanup expired cache entries."""
    from core.cache import cache_manager

    result = cache_manager.cleanup_expired()

    l1_cleaned = result.get("l1_cleaned", 0)
    l2_cleaned = result.get("l2_cleaned", 0)
    total = l1_cleaned + l2_cleaned

    click.echo(f"Cache cleanup completed:")
    click.echo(f"  L1 entries removed: {l1_cleaned}")
    click.echo(f"  L2 entries removed: {l2_cleaned}")
    click.echo(f"  Total removed:      {total}")
```

#### Task 2.2.2: Add `cache-rebuild` command

```python
@admin.command("cache-rebuild")
@click.option("--preload-truth", is_flag=True, help="Preload truth data after rebuild")
@click.pass_context
def cache_rebuild(ctx, preload_truth):
    """Rebuild cache from scratch."""
    from core.cache import cache_manager
    from core.database import CacheEntry

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

    click.echo(f"Cache rebuild completed:")
    click.echo(f"  L1 entries cleared: {l1_cleared}")
    click.echo(f"  L2 entries cleared: {l2_cleared}")
    click.echo("  Cache will repopulate on demand.")

    if preload_truth:
        click.echo("\nPreloading truth data...")
        try:
            truth_manager = agent_registry.get_agent("truth_manager")
            if truth_manager:
                import asyncio
                asyncio.run(truth_manager.handle_message({
                    "type": "REQUEST",
                    "method": "load_truth",
                    "params": {"family": "words"}
                }))
                click.echo("  Truth data preloaded for 'words' family.")
        except Exception as e:
            click.echo(f"  Warning: Failed to preload truth data - {e}")
```

---

### 2.3 Add Performance/Health Report Commands to CLI (GAP_010)

**File:** `cli/main.py`
**Location:** Inside `admin` group

#### Task 2.3.1: Add `report` subgroup

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

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    all_workflows = db_manager.list_workflows(limit=100000)

    period_workflows = [
        w for w in all_workflows
        if w.created_at and w.created_at.replace(tzinfo=timezone.utc) >= cutoff
    ]

    total = len(period_workflows)
    completed = len([w for w in period_workflows if w.state == WorkflowState.COMPLETED])
    failed = len([w for w in period_workflows if w.state == WorkflowState.FAILED])

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
        "avg_completion_ms": round(avg_time, 2),
        "error_rate": round(error_rate, 4),
        "success_rate": round(success_rate, 4),
        "cache_hit_rate": round(l1_hit_rate, 4)
    }

    if output_format == "json":
        click.echo(json.dumps(report, indent=2))
    else:
        click.echo(f"\nPerformance Report (last {days} days)")
        click.echo("=" * 40)
        click.echo(f"Total workflows:     {total}")
        click.echo(f"Completed:           {completed}")
        click.echo(f"Failed:              {failed}")
        click.echo(f"Success rate:        {success_rate*100:.1f}%")
        click.echo(f"Error rate:          {error_rate*100:.1f}%")
        click.echo(f"Avg completion time: {avg_time:.0f}ms")
        click.echo(f"Cache hit rate (L1): {l1_hit_rate*100:.1f}%")


@admin_report.command("health")
@click.option("--format", "output_format", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
def health_report(ctx, output_format):
    """Generate system health report."""
    import json
    from datetime import datetime, timezone

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database_connected": db_manager.is_connected(),
        "agents_registered": len(agent_registry.list_agents()),
        "status": "healthy" if db_manager.is_connected() else "degraded"
    }

    if output_format == "json":
        click.echo(json.dumps(report, indent=2))
    else:
        status_color = "green" if report["status"] == "healthy" else "red"
        click.echo(f"\nSystem Health Report")
        click.echo("=" * 30)
        click.echo(f"Status:     {click.style(report['status'].upper(), fg=status_color)}")
        click.echo(f"Database:   {'Connected' if report['database_connected'] else 'Disconnected'}")
        click.echo(f"Agents:     {report['agents_registered']} registered")
```

---

### 2.4 Add Workflow Watch Command to CLI (GAP_012)

**File:** `cli/main.py`
**Location:** Inside `workflows` group

#### Task 2.4.1: Add `workflows watch` command

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
        click.echo(f"Workflow {workflow_id} not found", err=True)
        raise SystemExit(1)

    click.echo(f"Watching workflow {workflow_id[:8]}... (Ctrl+C to stop)")
    click.echo("-" * 50)

    start_time = time.time()
    last_state = None
    last_progress = -1

    try:
        while time.time() - start_time < timeout:
            workflow = db_manager.get_workflow(workflow_id)
            if not workflow:
                click.echo("Workflow no longer exists")
                break

            current_state = workflow.state.value if hasattr(workflow.state, 'value') else str(workflow.state)
            current_progress = workflow.progress_percent or 0

            # Only print if something changed
            if current_state != last_state or current_progress != last_progress:
                timestamp = datetime.now().strftime("%H:%M:%S")
                progress_bar = _make_progress_bar(current_progress)

                state_color = {
                    "pending": "yellow",
                    "running": "blue",
                    "completed": "green",
                    "failed": "red",
                    "cancelled": "magenta"
                }.get(current_state, "white")

                click.echo(f"[{timestamp}] {click.style(current_state.upper(), fg=state_color)} {progress_bar} {current_progress}%")

                last_state = current_state
                last_progress = current_progress

            # Exit if terminal state
            if current_state in ["completed", "failed", "cancelled"]:
                click.echo(f"\nWorkflow finished with state: {current_state}")
                break

            time.sleep(interval)
        else:
            click.echo(f"\nTimeout reached ({timeout}s)")

    except KeyboardInterrupt:
        click.echo("\nWatch cancelled")


def _make_progress_bar(percent, width=20):
    """Create a simple progress bar."""
    filled = int(width * percent / 100)
    bar = "=" * filled + "-" * (width - filled)
    return f"[{bar}]"
```

---

## Phase 3: Admin & Monitoring Gaps (Lower Priority)

### 3.1 Add K8s-style Health Probe Commands (GAP_003)

**File:** `cli/main.py`

```python
@admin.command("health-live")
@click.pass_context
def health_live(ctx):
    """Kubernetes-style liveness probe (exit code for scripts)."""
    # Always return success if CLI can run
    click.echo("alive")
    raise SystemExit(0)


@admin.command("health-ready")
@click.pass_context
def health_ready(ctx):
    """Kubernetes-style readiness probe (exit code for scripts)."""
    checks = {
        "database": db_manager.is_connected(),
        "agents": len(agent_registry.list_agents()) > 0
    }

    all_ready = all(checks.values())

    for check, status in checks.items():
        symbol = click.style("OK", fg="green") if status else click.style("FAIL", fg="red")
        click.echo(f"{check}: {symbol}")

    if all_ready:
        click.echo("\nStatus: READY")
        raise SystemExit(0)
    else:
        click.echo("\nStatus: NOT READY")
        raise SystemExit(1)
```

---

### 3.2 Add Agent Reload Command (GAP_005)

**File:** `cli/main.py`

```python
@admin.command("agent-reload")
@click.argument("agent_id")
@click.pass_context
def agent_reload(ctx, agent_id):
    """Reload a specific agent (clear cache, reinitialize)."""
    from core.cache import cache_manager

    agent = agent_registry.get_agent(agent_id)
    if not agent:
        click.echo(f"Agent {agent_id} not found", err=True)
        raise SystemExit(1)

    actions = []

    # Clear agent's cache
    cache_manager.clear_agent_cache(agent_id)
    actions.append("cache_cleared")

    # Reload config if available
    if hasattr(agent, 'reload_config'):
        import asyncio
        asyncio.run(agent.reload_config())
        actions.append("config_reloaded")

    # Reset state if available
    if hasattr(agent, 'reset_state'):
        agent.reset_state()
        actions.append("state_reset")

    click.echo(f"Agent {agent_id} reloaded successfully")
    click.echo(f"Actions performed: {', '.join(actions)}")
```

---

### 3.3 Add Checkpoint Command (GAP_009)

**File:** `cli/main.py`

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
        },
        "cache": cache_manager.get_statistics()
    }

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

    click.echo(f"Checkpoint created successfully")
    click.echo(f"  ID:   {checkpoint_id}")
    click.echo(f"  Name: {checkpoint_name}")
    click.echo(f"  Time: {timestamp.isoformat()}")
```

---

## Phase 4: Developer Tools (Optional)

### 4.1 Add Web Endpoint Probing (GAP_013)

**Current State:** CLI has comprehensive `probe-endpoints` command. Web has no equivalent.

**Decision:** Keep as CLI-only developer tool. The CLI is the appropriate surface for endpoint testing/discovery.

**No action required.**

---

### 4.2 Add File Read Endpoint Parity (GAP_011)

**Current State:** Web has `/api/files/read` for dashboard. CLI reads files directly.

**Decision:** Not applicable for CLI - direct file access is preferred.

**No action required.**

---

## Implementation Checklist

### Phase 1: Core Feature Gaps

- [ ] Task 1.1.1: Add `POST /api/recommendations/{id}/generate` endpoint
- [ ] Task 1.1.2: Add `POST /api/recommendations/{id}/rebuild` endpoint
- [ ] Task 1.1.3: Add UI button for recommendation generation
- [ ] Task 1.2.1: Add `admin enhancements` CLI command
- [ ] Task 1.2.2: Add `admin rollback` CLI command
- [ ] Task 1.2.3: Add `admin enhancement-detail` CLI command
- [ ] Task 1.3.1: Add `validations diff` CLI command
- [ ] Task 1.3.2: Add `validations compare` CLI command
- [ ] Task 1.4.1: Add `workflows report` CLI command
- [ ] Task 1.4.2: Add `workflows summary` CLI command

### Phase 2: Operational Gaps

- [ ] Task 2.1.1: Add `admin maintenance enable/disable/status` CLI commands
- [ ] Task 2.2.1: Add `admin cache-cleanup` CLI command
- [ ] Task 2.2.2: Add `admin cache-rebuild` CLI command
- [ ] Task 2.3.1: Add `admin report performance` CLI command
- [ ] Task 2.3.2: Add `admin report health` CLI command
- [ ] Task 2.4.1: Add `workflows watch` CLI command

### Phase 3: Admin & Monitoring

- [ ] Task 3.1.1: Add `admin health-live` CLI command
- [ ] Task 3.1.2: Add `admin health-ready` CLI command
- [ ] Task 3.2.1: Add `admin agent-reload` CLI command
- [ ] Task 3.3.1: Add `admin checkpoint` CLI command

### Phase 4: Developer Tools

- [ ] (No action required - CLI-only tools acceptable)

---

## Testing Requirements

### Unit Tests to Add

1. `tests/cli/test_validation_diff.py` - Test diff/compare commands
2. `tests/cli/test_workflow_report.py` - Test report/summary commands
3. `tests/cli/test_admin_maintenance.py` - Test maintenance commands
4. `tests/cli/test_admin_enhancements.py` - Test enhancement/rollback commands
5. `tests/api/test_recommendation_generation.py` - Test new Web endpoints

### Integration Tests

1. CLI-to-API parity tests - Verify same operations produce same results
2. Maintenance mode tests - Verify workflow rejection when enabled
3. Rollback tests - Verify content restoration works correctly

---

## Post-Implementation Verification

After all tasks are complete, run the parity analysis again:

```bash
# Re-run parity analysis
python -c "from cli.main import probe_endpoints; probe_endpoints()"

# Expected result: 100% parity across all capabilities
```

---

## Appendix: File Modification Summary

| File | Lines Added | Changes |
|------|-------------|---------|
| `cli/main.py` | ~400 | 15 new commands |
| `api/server.py` | ~80 | 2 new endpoints |
| `templates/validation_detail_enhanced.html` | ~20 | 1 UI button |
| `tests/cli/test_*.py` | ~300 | 5 new test files |
| `tests/api/test_recommendation_generation.py` | ~100 | 1 new test file |

**Total estimated new code:** ~900 lines
