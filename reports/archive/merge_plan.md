# Validator Merge Plan - Implementation Details

**Date:** 2025-11-01
**Strategy:** Option A - Restore & Enhance content_validator
**Approach:** Surgical composition, preserve public interfaces

## Architecture Decision

```
┌─────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR                              │
│         (coordinates multi-agent workflows)                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ├──> truth_manager (loads truth data)
                     ├──> fuzzy_detector (pattern matching)
                     │
                     ├──> content_validator (PRIMARY)
                     │     ├── validate_content (main entry)
                     │     │   ├─> _validate_yaml_with_truths_and_rules ✅ RESTORE
                     │     │   ├─> _validate_markdown_with_rules ✅ RESTORE
                     │     │   ├─> _validate_code_with_patterns ✅ RESTORE
                     │     │   ├─> _validate_links ✅ RESTORE
                     │     │   ├─> _validate_structure ✅ RESTORE
                     │     │   └─> _validate_with_llm ✅ EXISTS
                     │     │
                     │     └── _store_validation_result (DB writes)
                     │          ├─> create_validation_result
                     │          └─> create_recommendation (per issue)
                     │
                     └──> llm_validator (OPTIONAL ENRICHMENT)
                           └── validate_plugins
                               ├─> _build_validation_prompt
                               └─> _parse_llm_response
```

**Key Principle:** content_validator remains the single source of truth for validation results and DB persistence. LLM validation is an optional enrichment step.

## Call Graph

### Current Flow (Orchestrator → Validators)
```python
# orchestrator.py _run_validation_pipeline (line 255)
1. truth_manager.load_truth_data()
2. fuzzy_detector.detect_plugins()
3. llm_validator.validate_plugins()  # ⚠️ Results NOT persisted
4. content_validator.validate_content()  # Writes to DB but logic stubbed
```

### After Merge Flow
```python
# orchestrator.py _run_validation_pipeline (unchanged externally)
1. truth_manager.load_truth_data()
2. fuzzy_detector.detect_plugins()
3. llm_validator.validate_plugins()  # Still called for compatibility
4. content_validator.validate_content()
   └─> Internally:
       a. Run rule-based validations (YAML, Markdown, Code, Links, Structure)
       b. Optionally call _validate_with_llm (LLM semantic checks)
       c. Merge all issues
       d. _store_validation_result(issues=[...])
          └─> For each issue with suggestion:
              - db_manager.create_recommendation(...)
```

## Implementation Steps

### STEP 1: Restore YAML Validation (CRITICAL)

**File:** `agents/content_validator.py`
**Method:** `_validate_yaml_with_truths_and_rules` (line 350)

**Current (STUB):**
```python
async def _validate_yaml_with_truths_and_rules(self, content: str, family: str, truth_context: Dict, rule_context: Dict) -> ValidationResult:
    return ValidationResult(confidence=0.8, issues=[], auto_fixable_count=0, metrics={"yaml_valid": True})
```

**New Implementation:**
```python
async def _validate_yaml_with_truths_and_rules(self, content: str, family: str, truth_context: Dict, rule_context: Dict) -> ValidationResult:
    """Validate YAML front-matter against truth and rule constraints."""
    issues: List[ValidationIssue] = []
    auto_fixable = 0
    
    # Parse front-matter
    if not frontmatter:
        issues.append(ValidationIssue(
            level="warning",
            category="yaml_parser_unavailable",
            message="frontmatter library not available for YAML validation",
            suggestion="Install python-frontmatter: pip install python-frontmatter"
        ))
        return ValidationResult(confidence=0.5, issues=issues, auto_fixable_count=0, metrics={"yaml_valid": False})
    
    try:
        post = frontmatter.loads(content)
        yaml_data = post.metadata
    except Exception as e:
        issues.append(ValidationIssue(
            level="error",
            category="yaml_parse_error",
            message=f"Failed to parse YAML front-matter: {str(e)}",
            line_number=1,
            suggestion="Check YAML syntax: ensure proper indentation, no tabs, balanced quotes"
        ))
        return ValidationResult(confidence=0.0, issues=issues, auto_fixable_count=0, metrics={"yaml_valid": False, "parse_error": str(e)})
    
    # Get validation rules from rule_context
    family_rules = rule_context.get("family_rules", {})
    allowed_fields = family_rules.get("allowed_yaml_fields", [])
    required_fields = family_rules.get("required_yaml_fields", [])
    field_types = family_rules.get("yaml_field_types", {})
    non_editable = rule_context.get("non_editable_fields", [])
    
    # Get truth constraints
    truth_data = truth_context.get("truth_data", {})
    valid_categories = truth_data.get("valid_categories", [])
    valid_tags = truth_data.get("valid_tags", [])
    
    # Check for unknown fields
    if allowed_fields:
        for key in yaml_data.keys():
            if key not in allowed_fields:
                issues.append(ValidationIssue(
                    level="warning",
                    category="unknown_yaml_field",
                    message=f"Field '{key}' is not in the allowed fields list",
                    suggestion=f"Remove '{key}' or add it to allowed_yaml_fields in rules/{family}.json"
                ))
    
    # Check for missing required fields
    for req_field in required_fields:
        if req_field not in yaml_data:
            issues.append(ValidationIssue(
                level="error",
                category="missing_required_field",
                message=f"Required field '{req_field}' is missing from front-matter",
                suggestion=f"Add '{req_field}: <value>' to the YAML front-matter",
                source="rule"
            ))
        elif not yaml_data[req_field]:
            issues.append(ValidationIssue(
                level="error",
                category="empty_required_field",
                message=f"Required field '{req_field}' is empty",
                suggestion=f"Provide a value for '{req_field}'",
                source="rule"
            ))
    
    # Check field types
    for field_name, expected_type in field_types.items():
        if field_name in yaml_data:
            value = yaml_data[field_name]
            if expected_type == "string" and not isinstance(value, str):
                issues.append(ValidationIssue(
                    level="error",
                    category="field_type_mismatch",
                    message=f"Field '{field_name}' should be a string, got {type(value).__name__}",
                    suggestion=f"Change '{field_name}' to a quoted string value"
                ))
            elif expected_type == "array" and not isinstance(value, list):
                issues.append(ValidationIssue(
                    level="error",
                    category="field_type_mismatch",
                    message=f"Field '{field_name}' should be an array, got {type(value).__name__}",
                    suggestion=f"Change '{field_name}' to a YAML array format: [item1, item2]"
                ))
            elif expected_type == "date":
                # Basic date format check
                if isinstance(value, str) and not re.match(r'\d{4}-\d{2}-\d{2}', value):
                    issues.append(ValidationIssue(
                        level="warning",
                        category="invalid_date_format",
                        message=f"Field '{field_name}' should be in YYYY-MM-DD format",
                        suggestion=f"Use ISO date format: YYYY-MM-DD"
                    ))
    
    # Check category constraints (if applicable)
    if "category" in yaml_data and valid_categories:
        if yaml_data["category"] not in valid_categories:
            issues.append(ValidationIssue(
                level="warning",
                category="invalid_category",
                message=f"Category '{yaml_data['category']}' is not in the valid categories list",
                suggestion=f"Use one of: {', '.join(valid_categories[:5])}",
                source="truth"
            ))
            auto_fixable += 1
    
    # Check tags constraints (if applicable)
    if "tags" in yaml_data and valid_tags and isinstance(yaml_data["tags"], list):
        for tag in yaml_data["tags"]:
            if tag not in valid_tags:
                issues.append(ValidationIssue(
                    level="info",
                    category="unknown_tag",
                    message=f"Tag '{tag}' is not in the known tags list",
                    suggestion=f"Consider using a tag from the standard list",
                    source="truth"
                ))
                auto_fixable += 1
    
    # Calculate confidence
    confidence = 1.0 if not issues else max(0.3, 1.0 - (len([i for i in issues if i.level == "error"]) * 0.2))
    
    return ValidationResult(
        confidence=confidence,
        issues=issues,
        auto_fixable_count=auto_fixable,
        metrics={
            "yaml_valid": len([i for i in issues if i.level == "error"]) == 0,
            "fields_checked": len(yaml_data),
            "required_fields_count": len(required_fields),
            "issues_count": len(issues)
        }
    )
```

**Dependencies:**
- Already imported: `frontmatter` (line 37-39, optional)
- Already imported: `re` (line 15)
- Already available: `ValidationIssue`, `ValidationResult` dataclasses

### STEP 2: Restore Markdown Validation

**File:** `agents/content_validator.py`
**Method:** `_validate_markdown_with_rules` (line 353)

**Implementation:**
```python
async def _validate_markdown_with_rules(self, content: str, plugin_context: Dict, family: str, rule_context: Dict) -> ValidationResult:
    """Validate Markdown structure and formatting."""
    issues: List[ValidationIssue] = []
    auto_fixable = 0
    
    lines = content.split('\n')
    
    # Extract headings
    headings = []
    for i, line in enumerate(lines, 1):
        if line.strip().startswith('#'):
            level = len(line) - len(line.lstrip('#'))
            text = line.lstrip('#').strip()
            headings.append({"level": level, "text": text, "line": i})
    
    # Check for skipped heading levels
    for i in range(1, len(headings)):
        prev_level = headings[i-1]["level"]
        curr_level = headings[i]["level"]
        if curr_level > prev_level + 1:
            issues.append(ValidationIssue(
                level="warning",
                category="skipped_heading_level",
                message=f"Heading level jumped from {prev_level} to {curr_level} at line {headings[i]['line']}",
                line_number=headings[i]["line"],
                suggestion=f"Use heading level {prev_level + 1} instead of {curr_level}"
            ))
            auto_fixable += 1
    
    # Check for duplicate headings
    heading_texts = [h["text"].lower() for h in headings]
    seen = set()
    for h in headings:
        if h["text"].lower() in seen:
            issues.append(ValidationIssue(
                level="info",
                category="duplicate_heading",
                message=f"Duplicate heading '{h['text']}' at line {h['line']}",
                line_number=h["line"],
                suggestion="Consider using unique heading text for better navigation"
            ))
        seen.add(h["text"].lower())
    
    # Check code block balance
    code_block_delimiters = [i for i, line in enumerate(lines, 1) if line.strip().startswith('```')]
    if len(code_block_delimiters) % 2 != 0:
        issues.append(ValidationIssue(
            level="error",
            category="unbalanced_code_blocks",
            message="Unbalanced code blocks (odd number of ``` delimiters)",
            line_number=code_block_delimiters[-1] if code_block_delimiters else None,
            suggestion="Ensure every ``` opening has a matching ``` closing"
        ))
    
    # Check for broken shortcodes
    shortcodes = self.shortcode_pattern.findall(content)
    for sc in shortcodes:
        # Basic shortcode validation
        if not sc.isalnum() and sc not in ['note', 'warning', 'tip', 'info']:
            issues.append(ValidationIssue(
                level="warning",
                category="unknown_shortcode",
                message=f"Unknown shortcode: {{{{< {sc} >}}}}",
                suggestion="Verify shortcode name against available shortcodes"
            ))
    
    # Check minimum content length (from rules)
    structure_rules = self.validation_rules.get("structure", {})
    min_intro_length = structure_rules.get("min_introduction_length", 100)
    
    # Find content before first heading or between YAML and first heading
    if '---' in content:
        parts = content.split('---', 2)
        if len(parts) >= 3:
            intro_content = parts[2].split('#', 1)[0] if '#' in parts[2] else parts[2]
        else:
            intro_content = ""
    else:
        intro_content = content.split('#', 1)[0] if '#' in content else content
    
    intro_length = len(intro_content.strip())
    if intro_length < min_intro_length:
        issues.append(ValidationIssue(
            level="info",
            category="short_introduction",
            message=f"Introduction is only {intro_length} characters (minimum {min_intro_length})",
            suggestion=f"Add at least {min_intro_length - intro_length} more characters to the introduction"
        ))
        auto_fixable += 1
    
    confidence = 1.0 if not issues else max(0.5, 1.0 - (len([i for i in issues if i.level == "error"]) * 0.15))
    
    return ValidationResult(
        confidence=confidence,
        issues=issues,
        auto_fixable_count=auto_fixable,
        metrics={
            "markdown_valid": len([i for i in issues if i.level == "error"]) == 0,
            "headings_count": len(headings),
            "code_blocks_count": len(code_block_delimiters) // 2,
            "introduction_length": intro_length
        }
    )
```

### STEP 3: Restore Code, Links, Structure Validations

**Similar implementations for:**
- `_validate_code_with_patterns`: Check for API pattern usage, plugin references
- `_validate_links`: Extract and validate markdown links
- `_validate_structure`: Check section lengths, heading depths

*(Abbreviated for brevity - follow same pattern as YAML/Markdown above)*

### STEP 4: Health Endpoint Fix

**File:** `api/server.py`
**Method:** `/health` endpoint

**Current Check:** Verify it requires DB connection
**Expected:** Health returns 200 only if `db_manager.is_connected()` is True

**Implementation:**
```python
@app.get("/health")
async def health_check():
    """Health check endpoint - requires DB connection."""
    health = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {}
    }
    
    # Database check (REQUIRED)
    try:
        if db_manager.is_connected():
            health["components"]["database"] = {"status": "healthy"}
        else:
            health["status"] = "unhealthy"
            health["components"]["database"] = {"status": "disconnected"}
            return JSONResponse(content=health, status_code=503)
    except Exception as e:
        health["status"] = "unhealthy"
        health["components"]["database"] = {"status": "error", "message": str(e)}
        return JSONResponse(content=health, status_code=503)
    
    # Ollama check (OPTIONAL)
    try:
        if ollama.enabled and ollama.is_available():
            health["components"]["ollama"] = {"status": "healthy", "model": ollama.model}
        else:
            health["components"]["ollama"] = {"status": "disabled"}
    except Exception as e:
        health["components"]["ollama"] = {"status": "unavailable", "message": str(e)}
    
    return health
```

### STEP 5: Dashboard Verification

**Files to Check:**
- `api/dashboard.py`
- `api/server.py` (validation detail endpoints)
- `templates/*.html` (if template-based rendering)

**Verification:**
1. Dashboard lists validations → Ensure correct query to validation_results table
2. Per-validation detail page → Ensure validation_id parameter used correctly
3. Recommendations panel → Ensure joining validation_results.recommendations properly

**Expected SQL (conceptual):**
```python
# List validations
validations = session.query(ValidationResult).order_by(ValidationResult.created_at.desc()).all()

# Get validation detail
validation = session.query(ValidationResult).filter_by(id=validation_id).first()
recommendations = validation.recommendations  # via ORM relationship

# Ensure recommendations are actually populated from DB
for rec in recommendations:
    display_recommendation(rec.title, rec.description, rec.suggestion, rec.confidence)
```

## File Changes Summary

| File | Changes | Line Edits | Risk |
|------|---------|------------|------|
| `agents/content_validator.py` | Implement 5 validation methods | ~400 lines | Medium |
| `api/server.py` | Fix /health DB requirement | ~15 lines | Low |
| `api/dashboard.py` | Verify recommendation display | 0-50 lines | Low |

## Testing Strategy

1. **Unit Tests:** Test each validation method independently
2. **Integration Tests:** Test full validate_content flow
3. **API Tests:** Test endpoints return correct data
4. **Manual Tests:** Use test_md_folder for real-world validation

## Rollback Plan

If issues arise:
1. content_validator changes are isolated to private methods
2. Public handlers remain unchanged
3. Can revert to stub implementations temporarily
4. Database schema unchanged - no migrations needed

## Success Criteria

✅ YAML validation catches missing required fields
✅ YAML validation catches type mismatches
✅ Markdown validation catches unbalanced code blocks
✅ Markdown validation catches skipped heading levels
✅ Dashboard shows recommendations
✅ Detail page shows correct validation record
✅ Health endpoint requires DB
✅ All tests pass
✅ CRLF line endings preserved

## Next Actions

1. Implement validation methods in content_validator.py
2. Verify health endpoint
3. Test with sample markdown files
4. Create endpoint checker tool
5. Generate final ZIP

---

**Implementation Notes:**
- Use `newline="\r\n"` on all file writes (Windows CRLF requirement)
- Verify line endings after each file save
- Keep all changes surgical and reversible
- Document any deviations from this plan
