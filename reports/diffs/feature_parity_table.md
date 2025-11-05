# Feature Parity Table: content_validator vs llm_validator

**Analysis Date:** 2025-11-01
**Project:** TBCV (Template-Based Content Validator)

## Executive Summary

The `content_validator` has comprehensive validation capabilities including YAML/front-matter checks, but currently has **stub implementations** (returning empty ValidationResults with confidence=0.8). The `llm_validator` focuses on semantic plugin validation using LLM but **does NOT write to database** or create recommendations.

**Critical Finding:** Current `content_validator` has all the right handlers registered but the actual validation logic is stubbed out. The `llm_validator` generates useful recommendations but doesn't persist them.

## Detailed Feature Comparison

| Feature/Capability | content_validator | llm_validator | Merge Plan |
|-------------------|-------------------|---------------|------------|
| **YAML/Front-matter Validation** | ✅ Handler exists but STUBBED | ❌ Not present | **RESTORE** - Implement actual YAML validation logic in content_validator |
| **Markdown Structure Checks** | ✅ Handler exists but STUBBED | ❌ Not present | **RESTORE** - Implement actual markdown checks |
| **Code Quality Validation** | ✅ Handler exists but STUBBED | ❌ Not present | **RESTORE** - Implement code validation logic |
| **Link Validation** | ✅ Handler exists but STUBBED | ❌ Not present | **RESTORE** - Implement link checking logic |
| **Content Structure Validation** | ✅ Handler exists but STUBBED | ❌ Not present | **RESTORE** - Implement structure validation |
| **LLM-based Semantic Validation** | ✅ Implemented (_validate_with_llm) | ✅ Core functionality | **KEEP** Both - content_validator already has it |
| **Plugin Detection** | ✅ Via fuzzy_detector | ✅ Via fuzzy + LLM verification | **COMPOSE** - Use LLM validation to enrich results |
| **Truth Table Usage** | ✅ Loads via truth_manager | ✅ Directly loads JSON | **KEEP** content_validator approach (via agent) |
| **Rule-based Validation** | ✅ Loads via rule_manager | ✅ Passes to LLM prompt | **KEEP** content_validator approach |
| **Database Writes** | ✅ create_validation_result + create_recommendation | ❌ Not implemented | **KEEP** content_validator only |
| **Recommendation Generation** | ✅ Creates Recommendation records | ✅ Generates but doesn't persist | **MERGE** - Ensure LLM recs are stored via DB |
| **Ollama Integration** | ✅ Via core.ollama | ✅ Via core.ollama | **KEEP** - Already unified |
| **Detailed Error Messages** | ⚠️ Stub returns generic | ✅ LLM provides context | **ENHANCE** - Use LLM for better messages |
| **Auto-fix Suggestions** | ⚠️ Stub logic present | ✅ LLM provides suggestions | **ENHANCE** - Use LLM suggestions |
| **Line/Column Precision** | ✅ ValidationIssue supports it | ❌ No line numbers | **KEEP** structure, add when possible |

## Current Implementation Status

### content_validator Current State
- **Lines of Code:** 496
- **Handlers Registered:** 9 (ping, get_status, get_contract, validate_content, validate_yaml, validate_markdown, validate_code, validate_links, validate_structure)
- **Database Integration:** ✅ Full (_store_validation_result writes ValidationResult + Recommendation records)
- **Validation Logic:** ⚠️ MOSTLY STUBBED (lines 350-363 return empty ValidationResult objects)
- **LLM Integration:** ✅ Implemented in _validate_with_llm (lines 365-439)

### llm_validator Current State
- **Lines of Code:** 351
- **Handlers Registered:** 4 (ping, get_status, get_contract, validate_plugins)
- **Database Integration:** ❌ None
- **Validation Logic:** ✅ Fully implemented semantic plugin validation
- **LLM Integration:** ✅ Core functionality with detailed prompting

## Issues Identified

### Critical Issues
1. **YAML Validation Stubbed:** content_validator's `_validate_yaml_with_truths_and_rules` returns hardcoded `ValidationResult(confidence=0.8, issues=[], ...)` - NO actual checking
2. **Markdown Validation Stubbed:** `_validate_markdown_with_rules` returns empty result
3. **Code Validation Stubbed:** `_validate_code_with_patterns` returns empty result
4. **Link Validation Stubbed:** `_validate_links` returns empty result
5. **Structure Validation Stubbed:** `_validate_structure` returns empty result
6. **LLM Recommendations Not Persisted:** llm_validator generates good recommendations but they never reach the database

### Moderate Issues
7. **Orchestrator Uses Both Separately:** orchestrator.py calls llm_validator and content_validator as separate steps, but content_validator DB write happens in validate_content handler (line 193)
8. **Duplicate LLM Logic:** Both have LLM validation capabilities but they're not unified

## Root Cause Analysis

Looking at content_validator.py lines 350-363:

```python
async def _validate_yaml_with_truths_and_rules(...) -> ValidationResult:
    return ValidationResult(confidence=0.8, issues=[], auto_fixable_count=0, metrics={"yaml_valid": True})

async def _validate_markdown_with_rules(...) -> ValidationResult:
    return ValidationResult(confidence=0.8, issues=[], auto_fixable_count=0, metrics={"markdown_valid": True})
# ... all validation methods are stubs
```

**The core validation logic was never implemented - only the infrastructure exists.**

## Merge Strategy Decision

**Option A (PREFERRED): Restore & Enhance content_validator**

1. Keep `content_validator` as the primary validator
2. **Restore actual validation logic** for YAML, Markdown, Code, Links, Structure
3. **Enhance with LLM** by calling llm_validator's logic as an optional augmentation step
4. Ensure all findings (rule-based + LLM-based) flow through content_validator's DB write path
5. No breaking changes to public API

### Why Option A?
- content_validator already has the right handlers registered (used by API/orchestrator)
- content_validator already writes to DB correctly
- content_validator already has the ValidationIssue/ValidationResult dataclasses
- We only need to fill in the stubbed methods and optionally call LLM for semantic checks

### Rejected Alternative: Option B (Create merged_validator.py)
Would require:
- Updating orchestrator.py to use new agent
- Updating agent registry initialization
- More extensive refactoring
- Higher risk of breaking existing flows

## Implementation Plan (Option A)

### Phase 1: Restore Core Validations (YAML focus)
1. ✅ Implement `_validate_yaml_with_truths_and_rules`
   - Parse YAML front-matter (use frontmatter lib)
   - Check allowed fields from rule_context
   - Check required fields from truth_context
   - Validate field types (string, date, array, etc.)
   - Check enum constraints (e.g., allowed categories)
   - Generate ValidationIssue objects with line/column when possible
   - Return comprehensive ValidationResult

2. ✅ Implement `_validate_markdown_with_rules`
   - Check heading structure (no skipped levels)
   - Detect duplicate headings
   - Check code block integrity (balanced backticks)
   - Validate shortcode syntax
   - Check minimum content lengths per section
   - Return ValidationResult with issues

3. ✅ Implement `_validate_code_with_patterns`
   - Check code snippets for common issues
   - Validate API patterns from rules
   - Check plugin usage correctness
   - Return ValidationResult

4. ✅ Implement `_validate_links`
   - Extract markdown links
   - Check for broken internal links (if file paths)
   - Detect suspicious external links
   - Return ValidationResult

5. ✅ Implement `_validate_structure`
   - Check introduction length
   - Validate section lengths
   - Check heading depth
   - Return ValidationResult

### Phase 2: Enhance with LLM (Composition)
6. ✅ Modify `handle_validate_content` to:
   - Run rule-based validations first (fast)
   - Optionally run LLM validation (slow, enrichment)
   - Merge issues from both sources
   - Ensure all issues flow through _store_validation_result

7. ✅ Create `_enrich_with_llm_insights` helper:
   - Call llm_validator logic internally
   - Parse LLM recommendations
   - Convert to ValidationIssue objects
   - Add to issues list

### Phase 3: Dashboard Integration
8. ✅ Verify dashboard.py correctly displays recommendations
9. ✅ Verify per-validation detail page matches correct record
10. ✅ Test live refresh (if feature exists)

### Phase 4: Health & DB
11. ✅ Ensure /health requires DB connection
12. ✅ Verify DB schema handles all fields

## Public Interface (Preserved)

### content_validator Handlers (NO CHANGES)
- `ping` → handle_ping
- `get_status` → handle_get_status
- `get_contract` → get_contract
- `validate_content` → handle_validate_content (main entry point)
- `validate_yaml` → handle_validate_yaml
- `validate_markdown` → handle_validate_markdown
- `validate_code` → handle_validate_code
- `validate_links` → handle_validate_links
- `validate_structure` → handle_validate_structure

### Database Schema (NO CHANGES)
- ValidationResult table: No new columns needed
- Recommendation table: No new columns needed
- Existing fields support all required data

### API Endpoints (NO CHANGES)
- GET /health → checks DB connection
- GET /validations → lists validation_results
- GET /validations/{id} → shows detail + recommendations
- WebSocket /ws → live updates

## Expected Outcomes

After merge:
1. ✅ YAML front-matter validation **WORKS** (checks allowed fields, types, required fields)
2. ✅ Markdown structure validation **WORKS** (headings, code blocks, lengths)
3. ✅ Code/Links/Structure validation **WORK** (basic checks)
4. ✅ LLM insights **ENRICH** results (when Ollama available)
5. ✅ Recommendations panel **POPULATED** (from ValidationIssue suggestions)
6. ✅ Dashboard shows **CORRECT** validation records
7. ✅ DB required for **GREEN** /health status
8. ✅ All validations **PERSISTED** to database
9. ✅ **NO breaking changes** to existing API/CLI/workflows

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Breaking existing API | High | Preserve all handler names and signatures |
| Database schema mismatch | Medium | Use existing fields, no migrations needed |
| LLM dependency blocks validation | Low | Make LLM optional, graceful degradation |
| Performance regression | Medium | Run rule-based checks first (fast), LLM async (slow) |
| CRLF line ending issues | Low | Explicit newline="\r\n" on all file writes |

## Next Steps

See `merge_plan.md` for detailed implementation steps and code changes.
