# Fuzzy and LLM Validation Fix

## Problem Summary

When running validations through the UI, fuzzy detection and LLM validation were not being executed, even when selected. The validation result showed:

```json
{
  "FuzzyLogic_metrics": {
    "fuzzy_available": false
  },
  "issues": [
    {
      "level": "warning",
      "category": "fuzzy_logic_unavailable",
      "message": "FuzzyDetector agent not available"
    }
  ]
}
```

## Root Cause

The `/api/validate` endpoint was only calling the **content_validator** agent directly, which runs heuristic checks but does NOT include:
- Fuzzy plugin detection
- LLM validation

The system has a full two-stage validation pipeline in the **orchestrator** agent that includes:
1. **Stage 1 (Heuristic)**: Fuzzy detection + Content validation
2. **Stage 2 (LLM)**: LLM validation with gating
3. **Stage 3**: Combining and gating issues based on confidence scores

## Solution

Updated the `/api/validate` endpoint to:
1. Use the **orchestrator** agent instead of just content_validator
2. Create temporary file for orchestrator to process (since it expects file paths)
3. Store validation results to the database
4. Publish live updates via WebSocket

### Changes Made

**File**: `api/server.py`

1. **Added helper functions** (lines 783-830):
   - `_determine_severity()` - Calculate severity from validation results
   - `_determine_status()` - Calculate status (pass/fail/warning)

2. **Updated `/api/validate` endpoint** (lines 852-920):
   - Now uses orchestrator's full pipeline
   - Creates temporary file for validation
   - Stores results to database
   - Publishes WebSocket updates
   - Falls back to content_validator if orchestrator unavailable

3. **Added ValidationResult import** (line 57):
   - Required for database operations

## What's Fixed

✅ **Fuzzy Detection**: Now runs when "FuzzyLogic" validation type is selected
✅ **LLM Validation**: Now runs as part of the two-stage pipeline
✅ **Issue Gating**: LLM confidence scores now gate and adjust heuristic issues
✅ **Database Storage**: Validation results are now properly stored
✅ **Live Updates**: WebSocket notifications when validation completes

## Validation Pipeline Flow

```
User submits content via UI
   ↓
/api/validate endpoint
   ↓
orchestrator.validate_file()
   ├─→ Stage 1: Fuzzy Detection (if fuzzy_detector available)
   ├─→ Stage 1: Content Validation (heuristic rules)
   ├─→ Stage 2: LLM Validation (if LLM enabled)
   └─→ Stage 3: Combine & gate issues
   ↓
Store to database
   ↓
Publish WebSocket update
   ↓
Return results to UI
```

## Testing

1. Start the server:
   ```bash
   python main.py
   ```

2. Open the dashboard at: http://127.0.0.1:8000/dashboard/validations

3. Click "Run Validation" and select:
   - Single File mode
   - Select a Markdown file
   - Ensure "FuzzyLogic" checkbox is checked
   - Submit

4. View the validation detail page - you should now see:
   - Fuzzy detection results (if applicable)
   - LLM validation results
   - No "FuzzyDetector agent not available" warning

## Validation Result Structure

The new validation results will include:

```json
{
  "file_path": "example.md",
  "family": "words",
  "validation_mode": "two_stage",
  "llm_enabled": true,

  "plugin_detection": {
    "detections": [...],
    "confidence": 0.85
  },

  "content_validation": {
    "issues": [...],
    "confidence": 0.75
  },

  "llm_validation": {
    "requirements": [...],
    "issues": [...],
    "confidence": 0.90
  },

  "final_issues": [
    // Combined and gated issues from all stages
  ],

  "overall_confidence": 0.85,
  "gating_score": 0.90
}
```

## Configuration

The validation mode can be configured in `config/main.yaml`:

```yaml
validation:
  mode: "two_stage"  # Options: two_stage, heuristic_only, llm_only
  llm_thresholds:
    downgrade_threshold: 0.2
    confirm_threshold: 0.5
    upgrade_threshold: 0.8
```

## Notes

- The orchestrator will fallback to content_validator only if it's not available
- LLM validation requires the `llm.enabled: true` setting in config
- Fuzzy detection requires the fuzzy_detector agent to be registered
- The temporary file approach is needed because orchestrator expects file paths, not content strings
