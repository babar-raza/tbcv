# Phase 1 Implementation Plan: High-Priority User-Facing Features

**Date:** 2025-11-20
**Estimated Effort:** 4-7 hours
**Target:** Week 1
**Priority:** HIGH

---

## Overview

Phase 1 focuses on the most critical user-facing features that will immediately improve the TBCV user experience. These features expose existing functionality and add essential database tracking.

### Goals
1. Give users control over recommendation generation
2. Allow users to select specific validation types
3. Persist validation types in database for tracking
4. Enable comprehensive workflow/job reporting

---

## Task Breakdown

### Task 1: On-Demand Recommendation Generation API ⭐
**Priority:** CRITICAL
**Effort:** 2-3 hours
**Status:** READY TO IMPLEMENT

#### What & Why
**Problem:** Currently recommendations are only auto-generated during validation, which is:
- Unreliable (can fail silently)
- Blocks validation flow
- No user control
- Can't regenerate if unsatisfactory

**Solution:** Add API endpoints for on-demand recommendation generation

#### Implementation Steps

**Step 1.1: Add API Endpoints (30 min)**

File: `api/server.py`

Add three new endpoints:

```python
@app.post("/api/validations/{validation_id}/recommendations/generate")
async def generate_recommendations(validation_id: str, force: bool = False):
    """
    Generate recommendations for a validation.

    Args:
        validation_id: Validation ID to generate recommendations for
        force: If True, regenerate even if recommendations exist

    Returns:
        {
            "validation_id": "uuid",
            "recommendations_generated": 5,
            "recommendations": [...]
        }
    """
    # 1. Get validation from database
    # 2. Check if recommendations already exist (skip if not force)
    # 3. Call RecommendationAgent to generate
    # 4. Return results
    pass

@app.get("/api/validations/{validation_id}/recommendations")
async def get_recommendations(validation_id: str):
    """Get all recommendations for a validation."""
    # 1. Get recommendations from database
    # 2. Return as JSON
    pass

@app.delete("/api/validations/{validation_id}/recommendations/{rec_id}")
async def delete_recommendation(validation_id: str, rec_id: str):
    """Delete a specific recommendation."""
    # 1. Verify recommendation belongs to validation
    # 2. Delete from database
    # 3. Return success
    pass
```

**Step 1.2: Verify RecommendationAgent Works (30 min)**

File: `agents/recommendation_agent.py`

Ensure `generate_recommendations` method:
- Takes validation_id parameter
- Loads validation from database
- Analyzes issues
- Calls LLM (Ollama) to generate recommendations
- Stores recommendations in database
- Returns results

If broken, fix it.

**Step 1.3: Add Tests (1 hour)**

File: `tests/api/test_recommendation_endpoints.py` (NEW)

```python
import pytest
from api.server import app
from fastapi.testclient import client

@pytest.mark.asyncio
async def test_generate_recommendations():
    # 1. Create validation with issues
    # 2. POST to /api/validations/{id}/recommendations/generate
    # 3. Assert recommendations created
    # 4. Assert stored in database
    pass

@pytest.mark.asyncio
async def test_generate_recommendations_force():
    # 1. Create validation with existing recommendations
    # 2. POST with force=true
    # 3. Assert recommendations regenerated
    pass

@pytest.mark.asyncio
async def test_get_recommendations():
    # 1. Create validation with recommendations
    # 2. GET /api/validations/{id}/recommendations
    # 3. Assert all recommendations returned
    pass

@pytest.mark.asyncio
async def test_delete_recommendation():
    # 1. Create recommendation
    # 2. DELETE /api/validations/{id}/recommendations/{rec_id}
    # 3. Assert recommendation deleted
    pass
```

**Step 1.4: Manual Testing (30 min)**

```bash
# 1. Start API server
python api/server.py

# 2. Create a validation with issues
curl -X POST http://localhost:8000/api/validate \
  -H "Content-Type: application/json" \
  -d '{"content": "...", "file_path": "test.md"}'

# 3. Generate recommendations
curl -X POST http://localhost:8000/api/validations/{id}/recommendations/generate

# 4. Get recommendations
curl http://localhost:8000/api/validations/{id}/recommendations

# 5. Delete a recommendation
curl -X DELETE http://localhost:8000/api/validations/{id}/recommendations/{rec_id}
```

#### Acceptance Criteria
- ✅ POST /recommendations/generate creates recommendations
- ✅ POST with force=true regenerates recommendations
- ✅ GET /recommendations returns all recommendations
- ✅ DELETE removes specific recommendation
- ✅ All endpoints tested
- ✅ Manual testing successful

---

### Task 2: Validation Type Selection API/CLI ⭐
**Priority:** HIGH
**Effort:** 1-2 hours
**Status:** READY TO IMPLEMENT

#### What & Why
**Problem:** All validation types run every time:
- Wastes time on unnecessary validations
- No way to run only specific checks
- Slower validation

**Solution:** Allow users to select which validation types to run

#### Implementation Steps

**Step 2.1: Update API Endpoint (15 min)**

File: `api/server.py`

Update `/api/validate` endpoint:

```python
@app.post("/api/validate")
async def validate_content(
    content: str,
    file_path: str,
    family: str = "words",
    validation_types: List[str] = None  # NEW PARAMETER
):
    """
    Validate content with optional type selection.

    Args:
        validation_types: List of validation types to run
                         Options: ["Markdown", "YAML", "Truth", "Code", "Links", "Structure"]
                         Default: All types
    """
    # Default to all types if not specified
    if validation_types is None:
        validation_types = ["Markdown", "YAML", "Truth", "Code", "Links", "Structure"]

    # Pass to content validator
    result = await validator.process_request("validate_content", {
        "content": content,
        "file_path": file_path,
        "family": family,
        "validation_types": validation_types  # NEW
    })

    return result
```

**Step 2.2: Update ContentValidator to Filter Types (30 min)**

File: `agents/content_validator.py`

Update `validate_content` method:

```python
async def validate_content(
    self,
    content: str,
    file_path: str,
    family: str = "words",
    validation_types: List[str] = None  # NEW
) -> Dict[str, Any]:
    """Validate content with optional type filtering."""

    # Default to all types
    if validation_types is None:
        validation_types = ["Markdown", "YAML", "Truth", "Code", "Links", "Structure"]

    all_results = []

    # Run only selected types
    if "Markdown" in validation_types:
        md_result = await self._validate_markdown(content, ...)
        all_results.append(md_result)

    if "YAML" in validation_types:
        yaml_result = await self._validate_yaml(content, ...)
        all_results.append(yaml_result)

    if "Truth" in validation_types:
        truth_result = await self._validate_truth(content, ...)
        all_results.append(truth_result)

    # ... etc for other types

    # Aggregate results
    return self._aggregate_results(all_results, validation_types)
```

**Step 2.3: Add CLI Support (15 min)**

File: `cli/main.py`

Add `--types` argument:

```python
@click.command()
@click.argument("file_path")
@click.option("--types", "-t", default=None,
              help="Validation types to run (comma-separated). Example: markdown,yaml,truth")
def validate(file_path: str, types: str):
    """Validate a file with optional type selection."""

    # Parse types
    validation_types = None
    if types:
        validation_types = [t.strip() for t in types.split(",")]

    # Run validation
    result = orchestrator.validate_file(file_path, validation_types=validation_types)

    print_results(result)
```

**Step 2.4: Add Tests (30 min)**

File: `tests/api/test_validation_type_selection.py` (NEW)

```python
@pytest.mark.asyncio
async def test_validate_with_type_selection():
    # 1. Validate with only "Markdown" type
    result = await validator.validate_content(
        content="# Test",
        file_path="test.md",
        validation_types=["Markdown"]
    )
    # 2. Assert only Markdown validation ran
    assert "Markdown_metrics" in result["metrics"]
    assert "YAML_metrics" not in result["metrics"]

@pytest.mark.asyncio
async def test_validate_default_all_types():
    # 1. Validate without specifying types
    result = await validator.validate_content(content="...", file_path="test.md")
    # 2. Assert all types ran
    assert "Markdown_metrics" in result["metrics"]
    assert "YAML_metrics" in result["metrics"]
```

#### Acceptance Criteria
- ✅ API accepts validation_types parameter
- ✅ CLI accepts --types flag
- ✅ Only specified types execute
- ✅ Default runs all types
- ✅ Tests pass

---

### Task 3: Add validation_types Field to Database ⭐
**Priority:** HIGH
**Effort:** 1-2 hours
**Status:** READY TO IMPLEMENT

#### What & Why
**Problem:** No record of which validation types were run
- Can't track what was validated
- Can't reproduce validation
- No audit trail

**Solution:** Add validation_types field to ValidationResult table

#### Implementation Steps

**Step 3.1: Create Migration (15 min)**

File: `migrations/add_validation_types_field.py` (NEW)

```python
"""
Add validation_types field to validation_results table.

Migration: 2025-11-20-001
"""

def upgrade(db_manager):
    """Add validation_types column."""
    db_manager.execute("""
        ALTER TABLE validation_results
        ADD COLUMN validation_types TEXT;
    """)

    # Set default for existing records
    db_manager.execute("""
        UPDATE validation_results
        SET validation_types = '["Markdown","YAML","Truth","Code","Links","Structure"]'
        WHERE validation_types IS NULL;
    """)

def downgrade(db_manager):
    """Remove validation_types column."""
    db_manager.execute("""
        ALTER TABLE validation_results
        DROP COLUMN validation_types;
    """)

if __name__ == "__main__":
    from core.database import DatabaseManager
    db = DatabaseManager()
    upgrade(db)
    print("Migration complete")
```

**Step 3.2: Update DatabaseManager (30 min)**

File: `core/database.py`

Update `store_validation_result` method:

```python
def store_validation_result(
    self,
    file_path: str,
    validation_results: Dict,
    validation_types: List[str] = None,  # NEW
    **kwargs
) -> str:
    """Store validation result with types."""

    # Serialize validation_types to JSON
    types_json = json.dumps(validation_types) if validation_types else None

    # Insert into database
    cursor.execute("""
        INSERT INTO validation_results
        (id, file_path, validation_results, validation_types, ...)
        VALUES (?, ?, ?, ?, ...)
    """, (id, file_path, results_json, types_json, ...))

    return validation_id
```

**Step 3.3: Update ContentValidator Storage (15 min)**

File: `agents/content_validator.py`

Pass validation_types to storage:

```python
# Store validation result
validation_id = self.db_manager.store_validation_result(
    file_path=file_path,
    validation_results=results,
    validation_types=validation_types,  # NEW
    ...
)
```

**Step 3.4: Run Migration (5 min)**

```bash
python migrations/add_validation_types_field.py
```

**Step 3.5: Add Tests (30 min)**

File: `tests/core/test_validation_types_persistence.py` (NEW)

```python
def test_store_validation_with_types():
    # 1. Store validation with specific types
    vid = db.store_validation_result(
        file_path="test.md",
        validation_results={...},
        validation_types=["Markdown", "YAML"]
    )

    # 2. Retrieve validation
    validation = db.get_validation_result(vid)

    # 3. Assert types persisted
    assert validation.validation_types == ["Markdown", "YAML"]

def test_store_validation_default_types():
    # 1. Store without types
    vid = db.store_validation_result(
        file_path="test.md",
        validation_results={...}
    )

    # 2. Assert all types stored
    validation = db.get_validation_result(vid)
    assert len(validation.validation_types) == 6
```

#### Acceptance Criteria
- ✅ Migration adds validation_types column
- ✅ Existing records have default types
- ✅ New validations store types
- ✅ Can retrieve types from database
- ✅ Tests pass

---

### Task 4: Job/Workflow Reports API ⭐
**Priority:** HIGH
**Effort:** 2-3 hours
**Status:** READY TO IMPLEMENT

#### What & Why
**Problem:** No way to get summary of batch operations
- Users can't see overall progress
- No aggregated statistics
- No comprehensive report

**Solution:** Add report generation endpoints

#### Implementation Steps

**Step 4.1: Add Report Generation Methods (1 hour)**

File: `core/database.py`

```python
def generate_workflow_report(self, workflow_id: str) -> Dict:
    """Generate comprehensive workflow report."""

    # Get workflow
    workflow = self.get_workflow(workflow_id)

    # Get all validations for this workflow
    validations = self.get_validations_by_workflow(workflow_id)

    # Calculate summary statistics
    total_files = len(validations)
    files_passed = len([v for v in validations if v.status == "pass"])
    files_failed = total_files - files_passed

    total_issues = sum(len(v.issues) for v in validations)
    critical_issues = sum(
        len([i for i in v.issues if i.level == "error"])
        for v in validations
    )

    # Build report
    return {
        "workflow_id": workflow_id,
        "status": workflow.state,
        "created_at": workflow.created_at,
        "completed_at": workflow.completed_at,
        "duration_ms": (workflow.completed_at - workflow.created_at).total_seconds() * 1000
                       if workflow.completed_at else None,
        "summary": {
            "total_files": total_files,
            "files_passed": files_passed,
            "files_failed": files_failed,
            "total_issues": total_issues,
            "critical_issues": critical_issues
        },
        "validations": [
            {
                "file_path": v.file_path,
                "validation_types": v.validation_types,
                "status": v.status,
                "confidence": v.confidence,
                "issues_count": len(v.issues),
                "recommendations_count": len(v.recommendations)
            }
            for v in validations
        ]
    }

def generate_validation_report(self, validation_id: str) -> Dict:
    """Generate detailed validation report."""

    validation = self.get_validation_result(validation_id)
    recommendations = self.get_recommendations_by_validation(validation_id)

    return {
        "validation_id": validation_id,
        "file_path": validation.file_path,
        "created_at": validation.created_at,
        "validation_types": validation.validation_types,
        "status": validation.status,
        "confidence": validation.confidence,
        "metrics": validation.metrics,
        "issues": [
            {
                "level": i.level,
                "category": i.category,
                "message": i.message,
                "line": i.line_number,
                "suggestion": i.suggestion
            }
            for i in validation.issues
        ],
        "recommendations": [
            {
                "id": r.id,
                "type": r.type,
                "title": r.title,
                "status": r.status,
                "priority": r.priority
            }
            for r in recommendations
        ]
    }
```

**Step 4.2: Add API Endpoints (30 min)**

File: `api/server.py`

```python
@app.get("/api/workflows/{workflow_id}/report")
async def get_workflow_report(workflow_id: str):
    """Get comprehensive workflow report."""
    report = db_manager.generate_workflow_report(workflow_id)
    return report

@app.get("/api/workflows/{workflow_id}/summary")
async def get_workflow_summary(workflow_id: str):
    """Get workflow summary statistics only."""
    report = db_manager.generate_workflow_report(workflow_id)
    return report["summary"]

@app.get("/api/validations/{validation_id}/report")
async def get_validation_report(validation_id: str):
    """Get detailed validation report."""
    report = db_manager.generate_validation_report(validation_id)
    return report
```

**Step 4.3: Add Tests (1 hour)**

File: `tests/api/test_reports.py` (NEW)

```python
def test_workflow_report():
    # 1. Create workflow with 3 validations
    # 2. GET /api/workflows/{id}/report
    # 3. Assert report structure
    # 4. Assert summary statistics correct

def test_workflow_summary():
    # 1. Create workflow
    # 2. GET /api/workflows/{id}/summary
    # 3. Assert summary only returned

def test_validation_report():
    # 1. Create validation with issues and recommendations
    # 2. GET /api/validations/{id}/report
    # 3. Assert all details included
```

#### Acceptance Criteria
- ✅ GET /workflows/{id}/report returns complete report
- ✅ GET /workflows/{id}/summary returns summary only
- ✅ GET /validations/{id}/report returns detailed report
- ✅ Reports include all required fields
- ✅ Statistics calculated correctly
- ✅ Tests pass

---

## Implementation Order

### Day 1 (2-3 hours)
1. Task 1: On-Demand Recommendation Generation API
   - Add endpoints
   - Verify RecommendationAgent
   - Write tests

### Day 2 (1-2 hours)
2. Task 2: Validation Type Selection
   - Update API
   - Update ContentValidator
   - Add CLI support
   - Write tests

### Day 3 (1-2 hours)
3. Task 3: Database Schema Update
   - Create migration
   - Update DatabaseManager
   - Update ContentValidator
   - Run migration
   - Write tests

### Day 4 (2-3 hours)
4. Task 4: Job/Workflow Reports
   - Add report generation methods
   - Add API endpoints
   - Write tests

### Day 5 (1 hour)
5. Integration Testing & Documentation
   - Manual end-to-end testing
   - Update API documentation
   - Update user guide

---

## Testing Strategy

### Unit Tests
- Each feature has dedicated test file
- Test success cases
- Test error cases
- Test edge cases

### Integration Tests
- Test features work together
- Test API endpoints end-to-end
- Test CLI commands

### Manual Testing
- Use Postman/curl for API testing
- Use CLI for command testing
- Verify database changes

---

## Success Criteria

Phase 1 is complete when:

1. ✅ Users can trigger recommendation generation on-demand
2. ✅ Users can select specific validation types (API + CLI)
3. ✅ Validation types are persisted in database
4. ✅ Users can view comprehensive workflow/validation reports
5. ✅ All tests pass (>90% coverage for new code)
6. ✅ Documentation updated
7. ✅ Manual testing successful

---

## Risks & Mitigation

### Risk 1: RecommendationAgent Not Working
**Mitigation:** Test early, fix if needed, fallback to simple recommendations

### Risk 2: Database Migration Failure
**Mitigation:** Test migration on copy first, have rollback script ready

### Risk 3: Breaking Changes
**Mitigation:** Make all parameters optional with sensible defaults

### Risk 4: Time Overrun
**Mitigation:** Prioritize tasks, defer Task 4 if needed

---

## Next Steps After Phase 1

### Phase 2 Planning
- Re-validation with comparison
- Cron job for recommendations
- Configuration enhancements

### Phase 3 Planning
- SEO/heading validation
- Batch enhancement
- Export formats

---

**Status:** READY TO START
**Next Action:** Begin Task 1 - On-Demand Recommendation Generation API
