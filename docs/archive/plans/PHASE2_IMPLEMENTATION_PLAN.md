# Phase 2 Implementation Plan - Workflow Improvements

**Date:** 2025-11-20
**Status:** 🔵 READY TO START
**Priority:** Medium
**Estimated Time:** 6-8 hours
**Dependencies:** Phase 1 Complete ✅

---

## Overview

Phase 2 focuses on workflow improvements and better tracking/reporting capabilities. These features enhance the user experience and enable better validation workflows.

---

## Tasks

### Task 1: Re-validation with Comparison 🟡

**Priority:** HIGH
**Estimated Time:** 3-4 hours
**Complexity:** Medium

#### Description
Allow users to re-validate enhanced content and compare results with the original validation to verify that enhancements actually fixed the issues.

#### Current State
- Users can validate content
- Validations are stored in database
- No comparison logic exists

#### What's Needed

**1. API Endpoint:**
```python
POST /api/validations/{original_id}/revalidate
{
    "enhanced_content": "...",
    "compare": true
}

Response:
{
    "new_validation_id": "uuid",
    "comparison": {
        "original_issues": 5,
        "new_issues": 0,
        "resolved_issues": 5,
        "new_issues_list": [],
        "improvement_score": 1.0,
        "issues_resolved": [
            {"category": "yaml", "message": "Missing plugin field", "status": "resolved"},
            ...
        ]
    }
}
```

**2. Comparison Logic:**
- Store reference to original validation
- Run validation on enhanced content
- Compare issue lists (by category + message similarity)
- Calculate improvement metrics:
  - Resolved issues: Issues in original but not in new
  - New issues: Issues in new but not in original
  - Persistent issues: Issues in both
  - Improvement score: (resolved / total_original) * 100

**3. Database Updates:**
```python
# Add to ValidationResult model
parent_validation_id = Column(String(36), ForeignKey('validation_results.id'), nullable=True)
comparison_data = Column(JSONField, nullable=True)
```

#### Implementation Steps

1. **Update Database Schema** (30 min)
   - Add parent_validation_id column to ValidationResult
   - Add comparison_data column
   - Create migration script

2. **Implement Comparison Logic** (1.5 hours)
   - Create `compare_validations()` method in DatabaseManager
   - Implement issue matching algorithm (fuzzy match by category + message)
   - Calculate improvement metrics
   - Location: [core/database.py](../core/database.py)

3. **Add API Endpoint** (1 hour)
   - Add POST `/api/validations/{original_id}/revalidate` endpoint
   - Call ContentValidator with enhanced content
   - Run comparison if requested
   - Store comparison data
   - Location: [api/server.py](../api/server.py)

4. **Testing** (1 hour)
   - Create test with original content having 3 issues
   - Enhance content to fix 2 issues
   - Verify comparison shows 2 resolved, 1 persistent
   - Test edge cases (all resolved, none resolved, new issues)

#### Files to Modify
- `core/database.py` - Add comparison methods
- `api/server.py` - Add revalidate endpoint
- `migrations/add_revalidation_columns.py` - New migration
- `tests/api/test_revalidation.py` - New test file

#### Acceptance Criteria
- ✅ Re-validation endpoint implemented
- ✅ Comparison logic correctly identifies resolved/new/persistent issues
- ✅ Both validations stored with link
- ✅ Improvement metrics calculated
- ✅ Tests passing

---

### Task 2: Recommendation Requirement Configuration 🟡

**Priority:** MEDIUM
**Estimated Time:** 1-2 hours
**Complexity:** Low

#### Description
Allow configuration of whether recommendations are required before enhancement, either globally or per-request.

#### Current State
- Recommendations are always optional
- Enhancement can proceed without recommendations
- No enforcement mechanism

#### What's Needed

**1. Configuration:**
```yaml
# config/enhancement.yaml
enhancement:
  require_recommendations: false  # Global default
  min_recommendations: 0  # Minimum number required
  auto_generate_if_missing: true  # Auto-generate if required but missing
```

**2. Per-Request Override:**
```python
POST /api/enhance
{
    "validation_id": "uuid",
    "require_recommendations": true,  # Override global setting
    "min_recommendations": 2
}
```

**3. Enforcement Logic:**
- Check if recommendations required (global or per-request)
- If required, check if recommendations exist
- If missing and auto_generate enabled, generate them
- If missing and auto_generate disabled, return error

#### Implementation Steps

1. **Add Configuration** (15 min)
   - Add enhancement section to config
   - Define default values
   - Location: Create `config/enhancement.yaml`

2. **Update Enhancement Agent** (30 min)
   - Add requirement checking logic to `handle_enhance_content()`
   - Check for existing recommendations
   - Auto-generate if needed
   - Return clear error if requirements not met
   - Location: [agents/enhancement_agent.py](../agents/enhancement_agent.py)

3. **Update API Endpoint** (15 min)
   - Add optional parameters to enhance endpoint
   - Pass to enhancement agent
   - Location: [api/server.py](../api/server.py)

4. **Testing** (30 min)
   - Test with requirements enabled, recommendations exist → success
   - Test with requirements enabled, no recommendations, auto-gen on → generates and succeeds
   - Test with requirements enabled, no recommendations, auto-gen off → error
   - Test per-request override

#### Files to Modify
- `config/enhancement.yaml` - New config file
- `agents/enhancement_agent.py` - Add enforcement logic
- `api/server.py` - Update enhance endpoint
- `tests/agents/test_enhancement_requirements.py` - New test file

#### Acceptance Criteria
- ✅ Config option added and loaded
- ✅ Enhancement agent enforces requirement
- ✅ Auto-generation works when enabled
- ✅ Clear error when requirements not met
- ✅ Per-request override works
- ✅ Tests passing

---

### Task 3: Cron Job for Recommendation Generation 🟡

**Priority:** LOW-MEDIUM
**Estimated Time:** 2-3 hours
**Complexity:** Medium

#### Description
Background job that periodically checks for validations without recommendations and generates them asynchronously.

#### Current State
- Recommendations generated synchronously during validation
- No background processing
- No automatic retry mechanism

#### What's Needed

**1. Cron Script:**
```python
# scripts/generate_recommendations_cron.py
async def process_pending_validations():
    """Find validations needing recommendations and generate them."""
    # 1. Find validations without recommendations
    pending = db_manager.get_validations_without_recommendations(limit=10)

    # 2. For each validation with issues
    for validation in pending:
        if validation.has_issues():
            try:
                await recommendation_agent.generate_recommendations(validation.id)
                logger.info(f"Generated recommendations for {validation.id}")
            except Exception as e:
                logger.error(f"Failed to generate for {validation.id}: {e}")
```

**2. Database Helper:**
```python
def get_validations_without_recommendations(self, limit=10) -> List[ValidationResult]:
    """Get validations that have issues but no recommendations."""
    with self.get_session() as session:
        query = session.query(ValidationResult).outerjoin(Recommendation)
        query = query.filter(
            ValidationResult.status != ValidationStatus.PASS,
            Recommendation.id == None
        ).limit(limit)
        return query.all()
```

**3. Systemd Service (Linux):**
```ini
# tbcv-recommendations.service
[Unit]
Description=TBCV Recommendation Generator
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /path/to/tbcv/scripts/generate_recommendations_cron.py
WorkingDirectory=/path/to/tbcv

[Install]
WantedBy=multi-user.target
```

**4. Systemd Timer:**
```ini
# tbcv-recommendations.timer
[Unit]
Description=Run TBCV recommendation generator every 5 minutes

[Timer]
OnBootSec=5min
OnUnitActiveSec=5min

[Install]
WantedBy=timers.target
```

#### Implementation Steps

1. **Add Database Helper** (30 min)
   - Add `get_validations_without_recommendations()` method
   - Test query returns correct validations
   - Location: [core/database.py](../core/database.py)

2. **Create Cron Script** (1 hour)
   - Create script with async processing
   - Add error handling and logging
   - Add rate limiting (max N per run)
   - Location: `scripts/generate_recommendations_cron.py`

3. **Create Service Files** (30 min)
   - Create systemd service file
   - Create systemd timer file
   - Add installation instructions
   - Location: `systemd/` directory

4. **Windows Task Scheduler** (30 min)
   - Create PowerShell script wrapper
   - Add Task Scheduler XML template
   - Location: `windows/` directory

5. **Testing** (30 min)
   - Create validation without recommendations
   - Run cron script manually
   - Verify recommendations generated
   - Test error handling

#### Files to Create
- `scripts/generate_recommendations_cron.py` - Main cron script
- `systemd/tbcv-recommendations.service` - Systemd service
- `systemd/tbcv-recommendations.timer` - Systemd timer
- `windows/generate_recommendations.ps1` - Windows wrapper
- `windows/task-scheduler-template.xml` - Task template
- `tests/scripts/test_cron_jobs.py` - Tests

#### Files to Modify
- `core/database.py` - Add helper method
- `README.md` - Add cron job setup instructions

#### Acceptance Criteria
- ✅ Cron script finds pending validations
- ✅ Generates recommendations asynchronously
- ✅ Error handling and logging work
- ✅ Systemd service/timer work on Linux
- ✅ Task Scheduler works on Windows
- ✅ Tests passing

---

## Implementation Order

**Recommended:** Do tasks in order for logical progression:

1. **Task 2** (1-2h) - Easiest, sets up config infrastructure
2. **Task 1** (3-4h) - Core feature, enables verification workflow
3. **Task 3** (2-3h) - Optional background processing

**Alternative:** Parallel implementation possible since tasks are independent.

---

## Total Effort Summary

| Task | Priority | Time | Complexity |
|------|----------|------|------------|
| Re-validation with Comparison | HIGH | 3-4h | Medium |
| Recommendation Requirement Config | MEDIUM | 1-2h | Low |
| Cron Job for Recommendations | LOW-MEDIUM | 2-3h | Medium |
| **TOTAL** | | **6-9h** | |

---

## Testing Strategy

### Unit Tests
- Database comparison logic
- Enhancement requirement checking
- Cron job validation finder

### Integration Tests
- Full re-validation workflow
- Requirement enforcement with auto-generation
- Cron job with actual recommendation generation

### Manual Testing
- Re-validate content through API
- Test config override via API
- Run cron job manually and verify

---

## Success Criteria

Phase 2 is complete when:
- ✅ Users can re-validate and see improvement metrics
- ✅ Recommendation requirements are configurable
- ✅ Background job can generate recommendations automatically
- ✅ All tests passing
- ✅ Documentation updated

---

## Next Phase Preview

**Phase 3: Polish & Nice-to-Have (7-11 hours)**
- SEO heading validation
- Heading size validation
- Batch enhancement API
- Validation history tracking
- Recommendation confidence scoring

---

## Notes

- All Phase 2 features are backward compatible
- No breaking changes to existing APIs
- Can be deployed incrementally
- Each task is independently useful

---

**Document Status:** READY FOR IMPLEMENTATION
**Created By:** Claude Code Agent
**Date:** 2025-11-20
