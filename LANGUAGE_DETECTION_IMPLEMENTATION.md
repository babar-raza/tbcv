# Language Detection Implementation Summary

## Overview

The TBCV system now enforces mandatory English-only content processing. Non-English content is automatically detected and rejected at all entry points (CLI, API, and orchestrator).

## Implementation Details

### Language Detection Rules

#### Standard Subdomains (all except blog.aspose.net)
- **English Content**: MUST contain `/en/` in the file path
  - ✅ Example: `/docs/en/words/index.md`
  - ✅ Example: `/api/en/reference.md`
  - ❌ Example: `/docs/fr/words/index.md` (French - rejected)
  - ❌ Example: `/api/de/reference.md` (German - rejected)

#### Blog Subdomain (blog.aspose.net)
- **English Content**: Filename must be `index.md`
  - ✅ Example: `/blog.aspose.net/post/index.md`
  - ❌ Example: `/blog.aspose.net/post/index.fr.md` (French - rejected)
  - ❌ Example: `/blog.aspose.net/post/index.es.md` (Spanish - rejected)

- **Fallback**: Blog paths can also use `/en/` pattern
  - ✅ Example: `/blog/en/post/article.md`

### Files Modified

#### 1. New Core Module: `core/language_utils.py`
Created a new utility module with three main functions:

- **`is_english_content(file_path: str) -> tuple[bool, str]`**
  - Determines if a file contains English content based on its path
  - Returns a tuple with (is_english, reason)
  - Handles both Windows and Unix path separators
  - Case-insensitive blog detection

- **`validate_english_content_batch(file_paths: list[str]) -> tuple[list[str], list[tuple[str, str]]]`**
  - Validates a batch of file paths
  - Returns valid English paths and rejected paths with reasons
  - Used for directory and batch validation

- **`log_language_rejection(file_path: str, reason: str, logger_instance: Optional[logging.Logger])`**
  - Logs rejections with consistent formatting
  - Helps track which files are being filtered out

#### 2. CLI Integration: `cli/main.py`
Added language checks to:

- **`validate_file` command**
  - Checks if the file is English before processing
  - Returns error code 1 if non-English content is detected
  - Displays clear error message to user

- **`validate_directory` command**
  - Filters files during directory scanning
  - Only English files are passed to the orchestrator

#### 3. Orchestrator Integration: `agents/orchestrator.py`
Added language checks to:

- **`handle_validate_file` method**
  - Validates language before reading file content
  - Returns structured error response with error_type='language_rejection'
  - Logs rejections for monitoring

- **`handle_validate_directory` method**
  - Filters all discovered files before processing
  - Logs summary of filtered files (e.g., "Filtered out 5 non-English files")
  - Includes rejected file info in workflow result errors
  - Updates file counts to reflect only English files

#### 4. API Integration: `api/server.py`
Added language checks to:

- **`run_batch_validation` function**
  - Filters file list before processing
  - Logs rejected files with reasons
  - Updates workflow metrics to reflect filtered file count
  - Includes rejection info in error list

### Test Coverage

Created comprehensive test suite: `tests/test_language_detection.py`

**Test Statistics:**
- ✅ 10 test methods
- ✅ 100% pass rate
- ✅ 40+ test cases covered

**Test Categories:**
1. Standard subdomain English paths
2. Standard subdomain non-English paths (fr, es, de, it, pt, ru, ja, zh)
3. Blog subdomain English patterns
4. Blog subdomain non-English patterns
5. Blog with /en/ fallback
6. Windows path support
7. Edge cases (empty paths, no language indicators)
8. Batch validation
9. Realistic Aspose documentation paths
10. Case sensitivity

## Usage Examples

### CLI Usage

#### Single File Validation
```bash
# English file - will be processed
tbcv validate-file /docs/en/words/index.md

# French file - will be rejected
tbcv validate-file /docs/fr/words/index.md
# Output: Error: Non-English content detected - File path contains '/fr/' indicating non-English content
```

#### Directory Validation
```bash
# Validates only English files in directory
tbcv validate-directory /docs --pattern "**/*.md" --recursive

# Non-English files are automatically filtered out and logged
```

### API Usage

#### Batch Validation
```python
# POST /api/validations/batch
{
    "files": [
        "/docs/en/index.md",      # Will be processed
        "/docs/fr/index.md",      # Will be skipped
        "/blog/post/index.md",    # Will be processed
        "/blog/post/index.es.md"  # Will be skipped
    ],
    "family": "words"
}

# Response includes:
# - files_total: 2 (only English files)
# - errors: ["Skipped (non-English): /docs/fr/index.md - ...", ...]
```

### Programmatic Usage

```python
from core.language_utils import is_english_content, validate_english_content_batch

# Check single file
is_english, reason = is_english_content("/docs/en/words/index.md")
if is_english:
    # Process file
    pass
else:
    print(f"Rejected: {reason}")

# Check multiple files
file_paths = [
    "/docs/en/index.md",
    "/docs/fr/index.md",
    "/blog/post/index.md"
]
valid_paths, rejected = validate_english_content_batch(file_paths)

print(f"Valid: {len(valid_paths)}")
print(f"Rejected: {len(rejected)}")
for path, reason in rejected:
    print(f"  - {path}: {reason}")
```

## Benefits

1. **Prevents Translation Conflicts**: Ensures only English source content is processed
2. **Automatic Filtering**: No manual intervention needed - non-English files are automatically skipped
3. **Clear Feedback**: Users receive detailed reasons for rejections
4. **Comprehensive Coverage**: All entry points (CLI, API, orchestrator) enforce the rule
5. **Logging**: All rejections are logged for monitoring and auditing
6. **Performance**: Early rejection prevents unnecessary processing of non-English content
7. **Maintainability**: Centralized logic in `core/language_utils.py`

## Supported Language Codes Detected

The system can detect and reject the following language codes:
- `fr` (French)
- `es` (Spanish)
- `de` (German)
- `it` (Italian)
- `pt` (Portuguese)
- `ru` (Russian)
- `ja` (Japanese)
- `zh` (Chinese)
- `ko` (Korean)
- `ar` (Arabic)
- `hi` (Hindi)
- `nl` (Dutch)
- `pl` (Polish)
- `tr` (Turkish)
- `vi` (Vietnamese)
- `th` (Thai)

## Error Responses

### CLI Error Format
```
Error: Non-English content detected - File path contains '/fr/' indicating non-English content
File: /docs/fr/words/index.md
Only English content can be processed. Translations are done automatically from English source.
```

### API Error Format
```json
{
    "status": "error",
    "error_type": "language_rejection",
    "message": "Non-English content rejected: File path contains '/fr/' indicating non-English content",
    "file_path": "/docs/fr/words/index.md",
    "reason": "File path contains '/fr/' indicating non-English content"
}
```

## Future Enhancements (Optional)

Potential improvements that could be added:

1. **Configuration**: Make language detection rules configurable via settings
2. **Additional Patterns**: Support more blog filename patterns if needed
3. **Language-Specific Handlers**: Different handling for different language types
4. **Statistics**: Track rejection statistics in dashboard
5. **Whitelist**: Allow specific non-English files via whitelist configuration

## Testing

Run the language detection tests:

```bash
# Run all language detection tests
python -m pytest tests/test_language_detection.py -v

# Run specific test
python -m pytest tests/test_language_detection.py::TestLanguageDetection::test_realistic_paths -v

# Run with coverage
python -m pytest tests/test_language_detection.py --cov=core.language_utils --cov-report=html
```

## Conclusion

The language detection feature is now fully integrated and tested. The system will automatically:
- ✅ Accept only English content
- ✅ Reject non-English content with clear reasons
- ✅ Log all rejections for monitoring
- ✅ Work consistently across CLI, API, and orchestrator
- ✅ Handle both standard and blog subdomain patterns

All entry points are protected, and the implementation is thoroughly tested with 10 test methods covering 40+ scenarios.
