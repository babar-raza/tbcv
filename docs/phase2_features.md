# Phase 2 Features Documentation

This document describes the Phase 2 features implemented for the TBCV system, including re-validation with comparison, recommendation requirements, and automated recommendation generation.

## Table of Contents

- [Re-validation with Comparison](#re-validation-with-comparison)
- [Recommendation Requirements](#recommendation-requirements)
- [Automated Recommendation Generation](#automated-recommendation-generation)
- [Database Schema Changes](#database-schema-changes)
- [API Endpoints](#api-endpoints)
- [Configuration](#configuration)

## Re-validation with Comparison

### Overview

The re-validation feature allows you to validate enhanced content and compare the results with the original validation to measure improvement.

### Features

- **Parent-Child Linking**: Re-validations are linked to their original validation via `parent_validation_id`
- **Fuzzy Issue Matching**: Issues are matched between validations based on category and message similarity
- **Improvement Metrics**: Calculates resolved, new, and persistent issues
- **Comparison Storage**: Comparison results are persisted for later retrieval

### API Usage

#### Re-validate Content

```http
POST /api/validations/{original_id}/revalidate
Content-Type: application/json

{
  "enhanced_content": "# Updated Content\n...",
  "compare": true
}
```

**Response:**

```json
{
  "new_validation_id": "uuid-new",
  "original_validation_id": "uuid-original",
  "success": true,
  "comparison": {
    "original_validation_id": "uuid-original",
    "new_validation_id": "uuid-new",
    "original_issues": 10,
    "new_issues": 3,
    "resolved_issues": 7,
    "new_issues_added": 0,
    "persistent_issues": 3,
    "improvement_score": 0.70,
    "resolved_issues_list": [...],
    "new_issues_list": [],
    "persistent_issues_list": [...]
  }
}
```

### Python Usage

```python
from core.database import db_manager

# Compare two validations
comparison = db_manager.compare_validations(
    original_id="uuid-original",
    new_id="uuid-new"
)

print(f"Improvement score: {comparison['improvement_score']}")
print(f"Resolved {comparison['resolved_issues']} issues")
print(f"New issues: {comparison['new_issues_added']}")
```

### Comparison Algorithm

The comparison uses fuzzy matching to identify issues across validations:

1. **Issue Key Generation**: Creates a key from category and first 100 chars of message
2. **Matching**: Compares keys to identify same issues across validations
3. **Categorization**:
   - **Resolved**: In original but not in new validation
   - **New**: In new validation but not in original
   - **Persistent**: In both validations
4. **Scoring**: `improvement_score = resolved_issues / original_issues`

## Recommendation Requirements

### Overview

The recommendation requirement feature allows you to enforce that recommendations must be generated and approved before content can be enhanced.

### Configuration

Global configuration in `config/enhancement.yaml`:

```yaml
enhancement:
  # Require recommendations before allowing enhancement
  require_recommendations: false

  # Minimum number of recommendations required (if require_recommendations is true)
  min_recommendations: 0

  # Auto-generate recommendations if required but missing
  auto_generate_if_missing: true

  # Maximum time to wait for recommendation generation (seconds)
  generation_timeout: 30

  # Confidence threshold for auto-applying recommendations
  auto_apply_confidence_threshold: 0.95
```

### API Usage

#### Enhance with Requirements

```http
POST /api/enhance
Content-Type: application/json

{
  "validation_id": "uuid",
  "require_recommendations": true,
  "min_recommendations": 3,
  "apply_all": true
}
```

**Per-request overrides** take precedence over global configuration.

### Behavior

1. **Check Requirements**: Verifies sufficient approved recommendations exist
2. **Auto-generation**: If enabled and no recommendations exist, attempts to generate them
3. **Enforcement**: Raises error if requirements not met and auto-generation failed
4. **Override**: Per-request parameters override global configuration

### Error Handling

```json
{
  "error": "Enhancement requires at least 3 approved recommendation(s), but only 1 found. Please approve recommendations before enhancement."
}
```

## Automated Recommendation Generation

### Overview

The automated recommendation generation feature runs as a background cron job to generate recommendations for validations that don't have any.

### Cron Script

Location: `scripts/generate_recommendations_cron.py`

**Features:**
- Batch processing of validations
- Configurable age threshold and batch size
- Dry-run mode for testing
- Comprehensive logging
- Error handling and recovery

### Usage

#### Manual Execution

```bash
# Dry run to see what would be processed
python scripts/generate_recommendations_cron.py --dry-run --log-level DEBUG

# Process up to 10 validations (older than 5 minutes)
python scripts/generate_recommendations_cron.py --batch-size 10 --min-age 5

# Process with custom settings
python scripts/generate_recommendations_cron.py \
    --batch-size 20 \
    --min-age 10 \
    --log-level INFO
```

#### Command-Line Options

- `--min-age MINUTES`: Only process validations older than N minutes (default: 5)
- `--batch-size N`: Process at most N validations per run (default: 10)
- `--dry-run`: Show what would be done without actually generating
- `--log-level LEVEL`: Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)

### Scheduling

#### Linux (systemd)

1. **Install service and timer:**
   ```bash
   sudo cp scripts/systemd/tbcv-recommendations.service /etc/systemd/system/
   sudo cp scripts/systemd/tbcv-recommendations.timer /etc/systemd/system/
   sudo systemctl daemon-reload
   ```

2. **Configure service:**
   Edit `/etc/systemd/system/tbcv-recommendations.service` to match your installation paths

3. **Enable and start:**
   ```bash
   sudo systemctl enable tbcv-recommendations.timer
   sudo systemctl start tbcv-recommendations.timer
   ```

4. **Monitor:**
   ```bash
   sudo systemctl status tbcv-recommendations.timer
   sudo journalctl -u tbcv-recommendations.service -f
   ```

See [scripts/systemd/README.md](../scripts/systemd/README.md) for full documentation.

#### Windows (Task Scheduler)

1. **Open PowerShell as Administrator**

2. **Run setup script:**
   ```powershell
   cd C:\path\to\tbcv
   .\scripts\windows\schedule_recommendations.ps1
   ```

3. **Verify task:**
   ```powershell
   Get-ScheduledTask -TaskName "TBCV-RecommendationGeneration"
   ```

See [scripts/windows/README.md](../scripts/windows/README.md) for full documentation.

### Database Helper

The cron job uses a specialized database query:

```python
from core.database import db_manager

# Get validations without recommendations
validations = db_manager.get_validations_without_recommendations(
    min_age_minutes=5,  # Only validations older than 5 minutes
    limit=10            # At most 10 validations
)

for validation in validations:
    # Generate recommendations...
    pass
```

## Database Schema Changes

### New Columns in `validation_results`

#### `parent_validation_id`

- **Type**: TEXT (UUID)
- **Purpose**: Links a re-validation to its original validation
- **Foreign Key**: References `validation_results.id`
- **Nullable**: Yes

#### `comparison_data`

- **Type**: JSON
- **Purpose**: Stores comparison results between validations
- **Structure**:
  ```json
  {
    "original_validation_id": "uuid",
    "new_validation_id": "uuid",
    "original_issues": 10,
    "new_issues": 3,
    "resolved_issues": 7,
    "new_issues_added": 0,
    "persistent_issues": 3,
    "improvement_score": 0.70,
    "resolved_issues_list": [...],
    "new_issues_list": [...],
    "persistent_issues_list": [...]
  }
  ```
- **Nullable**: Yes

### Migrations

Run these migrations to add the new columns:

```bash
# Add parent_validation_id and comparison_data columns
python migrations/add_revalidation_columns.py

# Fix old validation status enum values (if needed)
python migrations/fix_validation_status_enum.py
```

## API Endpoints

### POST `/api/validations/{original_id}/revalidate`

Re-validate enhanced content and optionally compare with original validation.

**Parameters:**
- `original_id` (path): UUID of original validation
- `enhanced_content` (body): The enhanced content to validate
- `compare` (body, optional): Whether to run comparison (default: true)

**Response:** See [Re-validation with Comparison](#re-validation-with-comparison)

### POST `/api/enhance`

Enhanced endpoint with recommendation requirements.

**New Parameters:**
- `require_recommendations` (optional): Override config - require recommendations before enhancement
- `min_recommendations` (optional): Override config - minimum number of approved recommendations required

**Example:**
```json
{
  "validation_id": "uuid",
  "require_recommendations": true,
  "min_recommendations": 3,
  "apply_all": true
}
```

## Configuration

### Enhancement Configuration

File: `config/enhancement.yaml`

```yaml
enhancement:
  # Require recommendations before enhancement
  require_recommendations: false

  # Minimum recommendations needed
  min_recommendations: 0

  # Auto-generate if missing
  auto_generate_if_missing: true

  # Generation timeout (seconds)
  generation_timeout: 30

  # Auto-apply confidence threshold
  auto_apply_confidence_threshold: 0.95
```

**Configuration Priority:**

1. Per-request parameters (highest)
2. Global configuration file
3. Default values (lowest)

## Testing

### Running Tests

```bash
# Run all Phase 2 tests
python -m pytest tests/test_phase2_features.py -v

# Run specific test class
python -m pytest tests/test_phase2_features.py::TestRevalidationComparison -v

# Run with coverage
python -m pytest tests/test_phase2_features.py --cov=core --cov=agents --cov-report=html
```

### Test Coverage

**TestRevalidationComparison** (4 tests):
- ✅ Parent validation linking
- ✅ Comparison with improvements
- ✅ Comparison with regressions
- ✅ Comparison data storage

**TestRecommendationRequirements** (4 tests):
- ✅ Configuration loading
- ✅ Requirements met
- ✅ Requirements not met (error handling)
- ✅ Requirements disabled

**TestCronDatabaseHelpers** (3 tests):
- ✅ Age filtering
- ✅ Exclusion of validations with recommendations
- ✅ Batch size limiting

### Test Results

```
7 passed, 4 skipped, 41 warnings in 0.64s
```

*Note: 4 tests skipped because enhancement agent not registered in test environment.*

## Troubleshooting

### Cron Job Not Running

**Linux:**
```bash
# Check timer status
sudo systemctl status tbcv-recommendations.timer

# Check service logs
sudo journalctl -u tbcv-recommendations.service -n 50

# Manually trigger
sudo systemctl start tbcv-recommendations.service
```

**Windows:**
```powershell
# Check task status
Get-ScheduledTask -TaskName "TBCV-RecommendationGeneration"

# View task history
Get-ScheduledTaskInfo -TaskName "TBCV-RecommendationGeneration"

# Manually trigger
Start-ScheduledTask -TaskName "TBCV-RecommendationGeneration"
```

### Recommendation Requirements Not Working

1. **Check configuration file exists:**
   ```bash
   ls -la config/enhancement.yaml
   ```

2. **Verify configuration syntax:**
   ```bash
   python -c "import yaml; yaml.safe_load(open('config/enhancement.yaml'))"
   ```

3. **Test requirement checking:**
   ```python
   from agents.enhancement_agent import EnhancementAgent
   agent = EnhancementAgent()
   config = agent._load_enhancement_config()
   print(config)
   ```

### Comparison Not Matching Issues

The comparison uses fuzzy matching based on:
- Category (exact match, case-insensitive)
- First 100 characters of message (exact match, case-insensitive)

If issues have slightly different messages, they won't be matched. This is intentional to avoid false matches.

## Performance Considerations

### Cron Job Batch Size

- **Small batch (5-10)**: Lower resource usage, more frequent runs
- **Large batch (50-100)**: Higher throughput, less frequent runs

Recommended: Start with 10, adjust based on:
- Number of validations without recommendations
- System resources available
- LLM API rate limits

### Comparison Performance

Comparison is O(n*m) where n and m are the number of issues in each validation. For validations with many issues (>100), comparison may take a few seconds.

Consider adding pagination for very large validation comparisons.

## Future Enhancements

Potential improvements for future versions:

1. **Smart Issue Matching**: Use fuzzy string matching (Levenshtein distance) for better issue correlation
2. **Trend Analysis**: Track improvement scores over time
3. **Notification System**: Alert when validation quality degrades
4. **Bulk Re-validation**: Re-validate multiple files at once
5. **Recommendation Prioritization**: Rank recommendations by impact
6. **A/B Testing**: Compare different enhancement strategies

## See Also

- [Architecture Documentation](../reference/architecture.md)
- [API Documentation](../api/README.md)
- [Testing Documentation](../tests/README.md)
- [Systemd Setup](../scripts/systemd/README.md)
- [Windows Setup](../scripts/windows/README.md)
