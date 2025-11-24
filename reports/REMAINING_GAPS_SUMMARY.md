# TBCV Remaining Gaps - Prioritized Summary

**Date:** 2025-11-20
**Status:** Current gaps after LLM truth validation completion
**Total Gaps:** 13 remaining

---

## Executive Summary

With the completion of LLM-based truth validation, the TBCV system now has strong core functionality. The remaining gaps are primarily in:
1. **API/CLI enhancements** - Exposing existing functionality
2. **Workflow improvements** - Better tracking and reporting
3. **Recommendation system** - Better generation and management
4. **Validation enhancements** - Minor improvements to existing validators

---

## Gap Overview by Priority

| Priority | Gaps | Est. Hours | Impact |
|----------|------|-----------|--------|
| **High** | 4 | 8-10h | High - User-facing features |
| **Medium** | 3 | 6-8h | Medium - Workflow improvements |
| **Low** | 6 | 6-8h | Low - Nice-to-have features |
| **TOTAL** | **13** | **20-26h** | |

---

## High Priority Gaps (8-10 hours)

### 1. On-Demand Recommendation Generation API 🔴
**Current State:** Auto-generation attempted but unreliable
**Impact:** HIGH - Blocks user control over recommendation workflow

**What's Missing:**
```python
POST /api/validations/{validation_id}/generate-recommendations
GET /api/validations/{validation_id}/recommendations
DELETE /api/validations/{validation_id}/recommendations/{rec_id}
```

**Expected Behavior:**
- User can trigger recommendation generation on-demand
- Can re-generate if results unsatisfactory
- Can fetch existing recommendations
- Can delete specific recommendations

**Effort:** 2-3 hours

**Acceptance Criteria:**
- ✅ POST endpoint triggers LLM recommendation generation
- ✅ GET endpoint returns all recommendations for validation
- ✅ Recommendations stored in database
- ✅ Error handling for LLM failures
- ✅ Tests for all endpoints

**Files to Modify:**
- `api/server.py` - Add new endpoints
- `agents/recommendation_agent.py` - Ensure handle_generate_recommendations works
- `tests/api/test_recommendation_endpoints.py` - New test file

---

### 2. Validation Type Selection API/CLI 🔴
**Current State:** All validation types run by default
**Impact:** HIGH - Users can't customize validation scope

**What's Missing:**
```python
# API
POST /api/validate
{
    "content": "...",
    "validation_types": ["markdown", "yaml", "truth"]  # NEW
}

# CLI
tbcv validate file.md --types markdown,yaml,truth
```

**Expected Behavior:**
- User specifies which validation types to run
- Default: all available types
- Results tagged by validation type
- Faster validation when fewer types selected

**Effort:** 1-2 hours

**Acceptance Criteria:**
- ✅ API accepts validation_types parameter
- ✅ CLI accepts --types flag
- ✅ Only specified types execute
- ✅ Results include validation_types metadata
- ✅ Tests for selection logic

**Files to Modify:**
- `api/server.py` - Update /validate endpoint
- `cli/main.py` - Add --types argument
- `agents/content_validator.py` - Filter validation types
- `tests/api/test_validation_selection.py` - New test file

---

### 3. Job/Workflow Reports API 🔴
**Current State:** Data exists, no report endpoint
**Impact:** HIGH - Users can't see summary of batch operations

**What's Missing:**
```python
GET /api/workflows/{workflow_id}/report
GET /api/validations/{validation_id}/report
GET /api/workflows/{workflow_id}/summary
```

**Expected Report Format:**
```json
{
    "workflow_id": "uuid",
    "status": "completed",
    "created_at": "2025-11-20T...",
    "duration_ms": 12345,
    "summary": {
        "total_files": 10,
        "files_passed": 7,
        "files_failed": 3,
        "total_issues": 24,
        "critical_issues": 3
    },
    "validations": [...]
}
```

**Effort:** 2-3 hours

**Acceptance Criteria:**
- ✅ GET /workflows/{id}/report returns comprehensive report
- ✅ Report includes summary statistics
- ✅ Report includes all validation details
- ✅ JSON format (extensible to HTML/PDF later)
- ✅ Tests for report generation

**Files to Modify:**
- `api/server.py` - Add report endpoints
- `core/database.py` - Add report generation methods
- `tests/api/test_reports.py` - New test file

---

### 4. Validation Type Field in Database 🔴
**Current State:** Validation types not persisted
**Impact:** MEDIUM-HIGH - Can't track which validations ran

**What's Missing:**
- `validation_types` field in ValidationResult table
- Migration to add field
- Update storage logic

**Expected Schema Change:**
```sql
ALTER TABLE validation_results
ADD COLUMN validation_types TEXT;  -- JSON array
```

**Effort:** 1-2 hours

**Acceptance Criteria:**
- ✅ Migration script adds validation_types column
- ✅ Content validator stores validation_types
- ✅ API returns validation_types in results
- ✅ Tests verify persistence

**Files to Modify:**
- `core/database.py` - Update ValidationResult model
- `migrations/add_validation_types.py` - New migration
- `agents/content_validator.py` - Store validation_types
- `tests/core/test_validation_persistence.py` - Update tests

---

## Medium Priority Gaps (6-8 hours)

### 5. Re-validation with Comparison 🟡
**Current State:** Can validate, no before/after comparison
**Impact:** MEDIUM - Users can't verify enhancements worked

**What's Missing:**
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
        "improvement_score": 1.0
    }
}
```

**Expected Behavior:**
- Store original validation results
- Run validation on enhanced content
- Compare results
- Generate improvement report

**Effort:** 3-4 hours

**Acceptance Criteria:**
- ✅ Re-validation endpoint implemented
- ✅ Comparison logic implemented
- ✅ Both validations stored
- ✅ Improvement metrics calculated
- ✅ Tests for comparison logic

**Files to Modify:**
- `api/server.py` - Add revalidate endpoint
- `agents/content_validator.py` - Add comparison method
- `tests/api/test_revalidation.py` - New test file

---

### 6. Cron Job for Recommendation Generation 🟡
**Current State:** No background processing
**Impact:** MEDIUM - Recommendations delayed if not real-time

**What's Missing:**
- Background job runner
- Cron job script
- Job scheduler integration

**Expected Implementation:**
```python
# scripts/generate_recommendations_cron.py
# Run every 5 minutes: */5 * * * *

async def process_pending_validations():
    # 1. Find validations without recommendations
    pending = db.get_validations_without_recommendations()

    # 2. For each validation with issues:
    for validation in pending:
        if validation.has_issues():
            # Generate recommendations
            await recommendation_agent.generate(validation.id)
```

**Effort:** 2-3 hours

**Acceptance Criteria:**
- ✅ Cron script implemented
- ✅ Finds pending validations
- ✅ Generates recommendations asynchronously
- ✅ Error handling and logging
- ✅ Tests for background processing

**Files to Create:**
- `scripts/generate_recommendations_cron.py` - New cron script
- `tests/scripts/test_cron_jobs.py` - New test file

---

### 7. Recommendation Requirement Configuration 🟡
**Current State:** Always optional
**Impact:** LOW-MEDIUM - Can't enforce recommendation review

**What's Missing:**
```python
# Global config
config.enhancement.require_recommendations = False  # Current
config.enhancement.min_recommendations = 0

# Per-request
POST /enhance
{
    "validation_id": "uuid",
    "require_recommendations": true  # Override global
}
```

**Expected Behavior:**
- Configuration option (global + per-request)
- Enhancement agent enforces requirement
- Clear error message if blocked

**Effort:** 1 hour

**Acceptance Criteria:**
- ✅ Config option added
- ✅ Enhancement agent checks requirement
- ✅ Error returned if not met
- ✅ Tests for enforcement

**Files to Modify:**
- `config/config.yaml` - Add enhancement settings
- `agents/enhancement_agent.py` - Add enforcement logic
- `tests/agents/test_enhancement_requirements.py` - New test file

---

## Low Priority Gaps (6-8 hours)

### 8. SEO Heading Validation Rules 🔴
**Current State:** Partial implementation
**Impact:** LOW - Nice-to-have validation

**What's Missing:**
- H1 uniqueness check (should be exactly 1 H1)
- Heading hierarchy validation (no skipped levels)
- SEO-friendly structure enforcement

**Expected Rules:**
```python
rules = [
    "Document must have exactly one H1 heading",
    "H1 should be the first heading",
    "No skipped heading levels (H1→H3 without H2)",
    "Heading text should be descriptive (>5 words)",
]
```

**Effort:** 2-3 hours

**Files to Modify:**
- `agents/content_validator.py` - Add SEO heading validation
- `rules/seo_rules.json` - Define rules
- `tests/agents/test_seo_validation.py` - New test file

---

### 9. Heading Size Validation 🔴
**Current State:** Not implemented
**Impact:** LOW - Nice-to-have validation

**What's Missing:**
- Heading character length rules
- Heading word count rules

**Expected Rules:**
```python
rules = {
    "h1": {"min_chars": 10, "max_chars": 60, "min_words": 3, "max_words": 10},
    "h2": {"min_chars": 10, "max_chars": 80, "min_words": 2, "max_words": 12},
    "h3": {"min_chars": 10, "max_chars": 100, "min_words": 2, "max_words": 15}
}
```

**Effort:** 1-2 hours

**Files to Modify:**
- `agents/content_validator.py` - Add heading size validation
- `rules/heading_rules.json` - Define rules
- `tests/agents/test_heading_size.py` - New test file

---

### 10. Validation History Tracking 🔴
**Current State:** Only current validation stored
**Impact:** LOW - Historical analysis not possible

**What's Missing:**
- Store multiple validations per file
- Track validation history over time
- Compare validation results across runs

**Expected Schema:**
```sql
CREATE TABLE validation_history (
    id UUID PRIMARY KEY,
    file_path TEXT,
    validation_id UUID REFERENCES validations(id),
    created_at TIMESTAMP,
    issues_count INTEGER,
    confidence FLOAT
);
```

**Effort:** 1-2 hours

**Files to Modify:**
- `core/database.py` - Add validation_history table
- `migrations/add_validation_history.py` - New migration
- `tests/core/test_validation_history.py` - New test file

---

### 11. Recommendation Confidence Scoring 🔴
**Current State:** Basic confidence in recommendation
**Impact:** LOW - Affects auto-apply decisions

**What's Missing:**
- Better confidence calculation based on:
  - LLM confidence
  - Issue severity
  - Truth data certainty
  - Historical accuracy

**Expected Logic:**
```python
def calculate_confidence(issue, truth_match, llm_response):
    base = llm_response.confidence

    # Adjust for issue severity
    if issue.severity == "critical":
        base *= 1.2

    # Adjust for truth certainty
    if truth_match and truth_match.certainty > 0.9:
        base *= 1.1

    return min(1.0, base)
```

**Effort:** 1 hour

**Files to Modify:**
- `agents/recommendation_agent.py` - Update confidence logic
- `tests/agents/test_recommendation_confidence.py` - New test file

---

### 12. Batch Enhancement API 🔴
**Current State:** Single file enhancement only
**Impact:** LOW - Manual process for multiple files

**What's Missing:**
```python
POST /api/enhance/batch
{
    "workflow_id": "uuid",
    "auto_approve": false,
    "apply_all_recommendations": true
}

Response:
{
    "batch_id": "uuid",
    "files_processed": 10,
    "total_enhancements": 47,
    "files_enhanced": [...]
}
```

**Expected Behavior:**
- Process all files in workflow
- Apply approved recommendations
- Generate batch report
- Store results

**Effort:** 2-3 hours

**Files to Modify:**
- `api/server.py` - Add batch endpoint
- `agents/enhancement_agent.py` - Add batch processing
- `tests/api/test_batch_enhancement.py` - New test file

---

### 13. Export Reports (HTML/PDF) 🔴
**Current State:** JSON only
**Impact:** LOW - Presentation quality

**What's Missing:**
- HTML report generation
- PDF export via wkhtmltopdf or similar
- Email report delivery

**Expected Formats:**
- HTML with CSS styling
- PDF for archiving
- Markdown for documentation

**Effort:** 2-3 hours

**Files to Create:**
- `core/report_generator.py` - Report formatting
- `templates/report.html` - HTML template
- `tests/core/test_report_export.py` - New test file

---

## Recommended Implementation Order

### Phase 1: User-Facing Features (Week 1)
1. ✅ LLM-based truth validation (DONE)
2. On-demand recommendation API (2-3h)
3. Validation type selection (1-2h)
4. Validation types in database (1-2h)

**Total:** 4-7 hours, **Impact:** HIGH

### Phase 2: Workflow & Reports (Week 2)
5. Job/workflow reports API (2-3h)
6. Re-validation with comparison (3-4h)
7. Recommendation requirement config (1h)

**Total:** 6-8 hours, **Impact:** MEDIUM

### Phase 3: Polish & Nice-to-Have (Week 3)
8. Cron job for recommendations (2-3h)
9. SEO heading validation (2-3h)
10. Heading size validation (1-2h)
11. Batch enhancement API (2-3h)

**Total:** 7-11 hours, **Impact:** LOW-MEDIUM

### Phase 4: Advanced Features (Future)
12. Validation history tracking (1-2h)
13. Recommendation confidence (1h)
14. Export reports HTML/PDF (2-3h)

**Total:** 4-6 hours, **Impact:** LOW

---

## Total Effort Estimate

| Phase | Hours | Priority | Completion Target |
|-------|-------|----------|-------------------|
| Phase 1 | 4-7h | HIGH | Week 1 |
| Phase 2 | 6-8h | MEDIUM | Week 2 |
| Phase 3 | 7-11h | LOW-MEDIUM | Week 3 |
| Phase 4 | 4-6h | LOW | Future |
| **TOTAL** | **21-32h** | | **3-4 weeks** |

---

## Gap Analysis by Category

### API/CLI Enhancements (5 gaps, 9-14h)
- On-demand recommendation API
- Validation type selection
- Job/workflow reports API
- Batch enhancement API
- Validation types in database

### Recommendation System (3 gaps, 5-7h)
- On-demand generation
- Cron job processing
- Confidence scoring

### Validation Enhancements (3 gaps, 4-6h)
- SEO heading rules
- Heading size validation
- Re-validation comparison

### Data & Reporting (2 gaps, 3-5h)
- Validation history
- Export reports (HTML/PDF)

---

## Next Steps

### Immediate (This Week)
1. Review this gap analysis
2. Prioritize gaps based on user needs
3. Start Phase 1 implementation:
   - On-demand recommendation API
   - Validation type selection
   - Database schema update

### Near-Term (Next 2 Weeks)
4. Complete Phase 2:
   - Job/workflow reports
   - Re-validation comparison
   - Config enhancements

### Long-Term (Month 2+)
5. Address Phase 3 & 4 based on user feedback
6. Monitor usage patterns
7. Adjust priorities as needed

---

## Success Criteria

### Phase 1 Complete When:
- ✅ Users can trigger recommendation generation on-demand
- ✅ Users can select specific validation types
- ✅ Validation types persisted in database
- ✅ All features tested and documented

### Phase 2 Complete When:
- ✅ Users can view workflow/job reports
- ✅ Users can re-validate and see improvement
- ✅ Enhancement requirements configurable
- ✅ All features tested and documented

### All Gaps Closed When:
- ✅ All 13 gaps implemented
- ✅ All features tested (>90% coverage)
- ✅ Documentation updated
- ✅ User feedback positive
- ✅ System meets all original requirements

---

**Document Status:** CURRENT as of 2025-11-20
**Next Review:** After Phase 1 completion
**Maintainer:** Development Team
