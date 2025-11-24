# Enhancement Workflow Guide

This guide covers the complete enhancement workflow in TBCV, from validation through recommendation generation to content enhancement with before/after comparison.

## Table of Contents

1. [Overview](#overview)
2. [Workflow Steps](#workflow-steps)
3. [CLI Usage](#cli-usage)
4. [Web UI Usage](#web-ui-usage)
5. [API Reference](#api-reference)
6. [Enhancement Comparison](#enhancement-comparison)
7. [Best Practices](#best-practices)

## Overview

The TBCV enhancement workflow allows you to:

1. **Validate** content against truth data and quality rules
2. **Generate** actionable recommendations for issues found
3. **Review and approve** recommendations
4. **Enhance** content by applying approved recommendations
5. **Compare** original vs. enhanced content with detailed diff visualization

## Workflow Steps

### Step 1: Content Validation

Validate content files to identify issues, plugin usage, and areas for improvement.

**What happens:**
- Content is scanned for plugin mentions
- Validation rules are applied (YAML, Markdown, Truth, etc.)
- LLM-based semantic validation checks for missing plugins or incorrect usage
- Issues are categorized by severity

**Output:**
- Validation result with PASS/FAIL status
- List of detected issues
- Confidence scores
- Plugin detection data

### Step 2: Recommendation Generation

Automatically generate actionable recommendations based on validation failures.

**What happens:**
- Each validation issue is analyzed
- Concrete, specific recommendations are generated
- Recommendations include:
  - Clear instruction for fixing the issue
  - Rationale explaining why it's needed
  - Severity level (critical, high, medium, low)
  - Confidence score
- Recommendations are stored with "proposed" status

**Types of recommendations:**
- **YAML fixes**: Missing fields, syntax errors
- **Markdown fixes**: Heading hierarchy, list formatting
- **Code fixes**: Language identifiers, syntax errors
- **Link fixes**: Broken links, invalid anchors
- **Truth fixes**: Plugin terminology corrections
- **Structure fixes**: Missing sections, document organization

### Step 3: Recommendation Review

Review and approve/reject recommendations before applying them.

**Actions available:**
- **Approve**: Mark recommendation for application
- **Reject**: Dismiss recommendation
- **Modify**: Edit recommendation before approval (future feature)

### Step 4: Content Enhancement

Apply approved recommendations to enhance the content.

**What happens:**
- Approved recommendations are retrieved
- Content is systematically modified according to each recommendation
- Original content is preserved
- Enhanced content is generated
- Detailed diff is computed
- Applied recommendations are marked as "actioned"

**Output:**
- Enhanced content
- Structured diff (line-by-line)
- Unified diff (Git-style)
- Enhancement statistics
- List of applied recommendations

### Step 5: Enhancement Comparison

View side-by-side comparison of original vs. enhanced content.

**Features:**
- **Side-by-side view**: Original and enhanced content displayed in parallel
- **Unified diff view**: Traditional Git-style diff
- **Color-coded changes**:
  - Green: Added lines
  - Red: Removed lines
  - Yellow: Modified lines
  - White: Unchanged lines
- **Statistics dashboard**: Lines added/removed/modified, recommendations applied
- **Synchronized scrolling**: Scroll both panels together
- **Line numbering**: Easy reference to specific lines

## CLI Usage

### Validate Content

```bash
# Validate a single file
python -m cli.main validate-file path/to/article.md --family words

# Validate with specific validation types
python -m cli.main validate-file path/to/article.md --types yaml,markdown,truth

# Output to JSON file
python -m cli.main validate-file path/to/article.md --output results.json --format json
```

### List Recommendations

```bash
# List recommendations for a validation
python -m cli.main recommendations list --validation-id <validation-id> --format table

# Filter by status
python -m cli.main recommendations list --status proposed --limit 20
```

### Generate Recommendations

```bash
# Generate recommendations for a validation
python -m cli.main recommendations generate <validation-id>

# Force regeneration
python -m cli.main recommendations generate <validation-id> --force
```

### Review Recommendations

```bash
# Approve multiple recommendations
python -m cli.main recommendations review <rec-id-1> <rec-id-2> --action approve

# Reject a recommendation
python -m cli.main recommendations review <rec-id> --action reject
```

### Enhance Content

```bash
# Enhance content with approved recommendations
python -m cli.main recommendations enhance path/to/article.md \\
  --validation-id <validation-id> \\
  --backup

# Preview changes without applying
python -m cli.main recommendations enhance path/to/article.md \\
  --validation-id <validation-id> \\
  --preview

# Specify output file
python -m cli.main recommendations enhance path/to/article.md \\
  --validation-id <validation-id> \\
  --output enhanced_article.md
```

## Web UI Usage

### 1. Navigate to Validations

1. Open browser to `http://localhost:8080`
2. Click "Validations" in the navigation menu
3. Find your validation in the list

### 2. View Validation Details

Click on a validation to see:
- Validation status and metadata
- Detected issues
- Generated recommendations
- Action buttons (Approve, Reject, Enhance)

### 3. Generate/Rebuild Recommendations

If recommendations haven't been generated:
1. Click **"Generate Recommendations"** button
2. Wait for recommendations to be created
3. Recommendations will appear in the list

To regenerate recommendations:
1. Click **"Rebuild"** button
2. Existing recommendations will be deleted
3. New recommendations will be generated

### 4. Review Recommendations

For each recommendation:
1. Review the **instruction** and **rationale**
2. Check the **confidence score**
3. Select checkbox to mark for enhancement
4. Click **"Review"** to see full details

### 5. Enhance Content

**Prerequisites:**
- Validation must be approved
- At least one recommendation must be approved/accepted

**Steps:**
1. Navigate to validation detail page
2. Click **"Enhance"** button
3. Wait for enhancement to complete
4. Status will update to "enhanced"

### 6. View Enhancement Comparison

Once content is enhanced:

#### Side-by-Side View

1. Click **"Side-by-Side View"** button
2. View original content (left) and enhanced content (right)
3. Color-coded lines show:
   - **Green background**: Added content
   - **Red background**: Removed content
   - **Yellow background**: Modified content
   - **White background**: Unchanged content
4. Scroll panels together (synchronized scrolling)
5. Line numbers help identify specific changes

#### Unified Diff View

1. Click **"Unified Diff"** button
2. View traditional Git-style diff
3. Format:
   - Lines starting with `+`: Added
   - Lines starting with `-`: Removed
   - Lines starting with `@@`: Location markers
   - Regular lines: Context

#### Enhancement Statistics

The statistics card shows:
- **Lines Added**: Number of new lines in enhanced content
- **Lines Removed**: Number of deleted lines
- **Lines Modified**: Number of changed lines
- **Recommendations Applied**: How many recommendations were successfully applied

#### Applied Recommendations

See a list of all recommendations that were applied, including:
- Title and instruction
- Confidence score
- Current status

## API Reference

### Get Enhancement Comparison

```http
GET /api/validations/{validation_id}/enhancement-comparison
```

**Response:**

```json
{
  "success": true,
  "validation_id": "uuid",
  "file_path": "path/to/file.md",
  "original_content": "...",
  "enhanced_content": "...",
  "diff_lines": [
    {
      "line_number_original": 5,
      "line_number_enhanced": 5,
      "content": "line text",
      "change_type": "modified",
      "recommendation_ids": ["rec1"]
    }
  ],
  "stats": {
    "original_length": 1000,
    "enhanced_length": 1200,
    "lines_added": 15,
    "lines_removed": 5,
    "lines_modified": 10,
    "recommendations_applied": 3,
    "recommendations_total": 5,
    "enhancement_timestamp": "2025-01-23T10:30:00"
  },
  "applied_recommendations": [
    {
      "id": "rec1",
      "title": "Fix plugin name",
      "instruction": "Replace 'Apose' with 'Aspose'",
      "confidence": 0.95,
      "status": "applied"
    }
  ],
  "unified_diff": "--- original\\n+++ enhanced\\n...",
  "status": "success"
}
```

### Enhance Validation

```http
POST /api/enhance/{validation_id}
```

Triggers enhancement for a validation with approved recommendations.

**Response:**

```json
{
  "success": true,
  "message": "Enhancement completed",
  "validation_id": "uuid",
  "enhancements_applied": 3
}
```

### Get Validation Diff (Legacy)

```http
GET /api/validations/{validation_id}/diff
```

Returns unified diff only (simpler endpoint for backward compatibility).

## Best Practices

### 1. Review Before Enhancing

Always review recommendations before enhancing:
- Check confidence scores (higher is better)
- Verify instructions make sense for your content
- Reject recommendations that don't apply
- Approve only recommendations you trust

### 2. Use Preview Mode

For CLI enhancement, use `--preview` first:
- See changes without modifying files
- Review the diff output
- Verify recommendations work as expected

### 3. Create Backups

Always use `--backup` flag in CLI or ensure you have version control:
- Enhancements modify content directly
- Backups allow easy rollback if needed
- Keep original content safe

### 4. Iterative Enhancement

For large files:
1. Start with high-confidence recommendations only
2. Apply and review results
3. Generate new validation
4. Apply medium-confidence recommendations
5. Repeat as needed

### 5. Monitor Statistics

Use enhancement statistics to:
- Gauge impact of changes
- Identify overly aggressive recommendations
- Track improvement metrics
- Validate enhancement quality

### 6. Validate After Enhancement

After enhancing content:
1. Re-run validation on enhanced content
2. Verify issues were fixed
3. Check for new issues introduced
4. Iterate if necessary

## Troubleshooting

### No Recommendations Generated

**Cause**: Validation passed with no issues
**Solution**: Content is already good! No enhancement needed.

### Enhancement Failed

**Causes**:
- No approved recommendations
- File permissions issue
- Content encoding problem

**Solutions**:
- Approve at least one recommendation
- Check file write permissions
- Verify file encoding (should be UTF-8)

### Comparison Not Loading

**Causes**:
- Content not enhanced yet
- WebSocket connection issue
- Server error

**Solutions**:
- Ensure validation status is "enhanced"
- Check browser console for errors
- Verify server is running
- Check API endpoint responds

### Changes Not Visible in Diff

**Causes**:
- Recommendations were skipped during enhancement
- Content identical to original
- Diff computation error

**Solutions**:
- Check applied recommendations list
- Verify enhancement stats show changes
- Try regenerating enhancement

## Example Workflow

Complete example from start to finish:

```bash
# 1. Validate content
python -m cli.main validate-file docs/tutorial.md --family words --output validation.json

# Extract validation ID from output
VALIDATION_ID=$(cat validation.json | python -c "import sys, json; print(json.load(sys.stdin)['validation_id'])")

# 2. List recommendations
python -m cli.main recommendations list --validation-id $VALIDATION_ID --format table

# 3. Review and approve recommendations (use web UI or programmatically)
# ... approve recommendations in UI ...

# 4. Enhance content
python -m cli.main recommendations enhance docs/tutorial.md \\
  --validation-id $VALIDATION_ID \\
  --backup \\
  --output docs/tutorial_enhanced.md

# 5. View comparison in web UI
# Open http://localhost:8080/dashboard/validations/{validation_id}
# Click "Side-by-Side View"
```

## Related Documentation

- [Web Dashboard Guide](web_dashboard.md)
- [CLI Usage](cli_usage.md)
- [API Reference](api_reference.md)
- [Agents Architecture](agents.md)
- [Truth Store Configuration](truth_store.md)
