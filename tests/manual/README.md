# Manual Testing Scripts

Ad-hoc testing scripts for development, debugging, and manual verification of system functionality.

## Purpose

These scripts are for:
- Quick manual testing during development
- Debugging specific features or issues
- Demonstrating functionality
- One-off verification tasks

**Not** for:
- Automated test suites (use `tests/test_*.py`)
- Production operations (use `scripts/`)
- CI/CD pipelines (use pytest)

## Test Scripts

### Enhancement Testing

#### test_enhancement.py
Test content enhancement functionality with approval workflow.

```bash
python tests/manual/test_enhancement.py
```

Tests:
- Plugin detection
- Content validation
- Recommendation generation
- Content enhancement with approved recommendations

Uses fixtures from `fixtures/test_enhancement_article.md`.

### Language Detection

#### test_language_demo.py
Demonstrate automatic programming language detection.

```bash
python tests/manual/test_language_demo.py
```

Shows:
- Language detection for various code blocks
- Confidence scores
- Fallback behavior

### WebSocket Testing

#### test_websocket_connection.py
Test WebSocket connection and real-time updates.

```bash
python tests/manual/test_websocket_connection.py
```

Verifies:
- WebSocket connection establishment
- Authentication/authorization
- Real-time message delivery
- Connection stability

#### test_minimal_fastapi_ws.py
Minimal WebSocket test with FastAPI.

```bash
python tests/manual/test_minimal_fastapi_ws.py
```

Minimal test for:
- Basic WebSocket connectivity
- FastAPI WebSocket routes
- CORS configuration

#### test_simple_ws.py
Simple standalone WebSocket test.

```bash
python tests/manual/test_simple_ws.py
```

Basic WebSocket test without FastAPI dependencies.

## Test Fixtures

Located in [fixtures/](fixtures/) subdirectory:

- **test_enhancement_article.md** - Sample markdown content for enhancement testing
- **test_workflow_2.md** - Workflow test fixture
- **test_workflow_article.md** - Article workflow fixture

## Usage

### Running Tests

All scripts should be run from the project root:

```bash
# Good
python tests/manual/test_enhancement.py

# Bad (may cause import errors)
cd tests/manual && python test_enhancement.py
```

### Prerequisites

- Virtual environment activated
- Database initialized
- API server running (for some tests)
- Ollama running (for LLM tests, optional)

### Environment Variables

Some tests support environment variables:

```bash
# Enable verbose logging
TBCV_LOG_LEVEL=debug python tests/manual/test_enhancement.py

# Use specific configuration
TBCV_CONFIG=config/test.yaml python tests/manual/test_enhancement.py

# Enable LLM validation
TBCV_LLM__ENABLED=true python tests/manual/test_language_demo.py
```

## Adding New Manual Tests

When creating new manual test scripts:

1. Place in this directory
2. Prefix filename with `test_`
3. Add entry to this README
4. Include docstring explaining purpose
5. Add test fixtures to `fixtures/` if needed
6. Use existing patterns for consistency

### Template

```python
"""
Manual test for [feature name].

Usage:
    python tests/manual/test_[feature].py

Prerequisites:
    - [list prerequisites]

Expected output:
    - [describe expected results]
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Your test code here
def main():
    # Test implementation
    pass

if __name__ == "__main__":
    main()
```

## Related Documentation

- **Automated tests**: [tests/](../) - Pytest test suite
- **Test fixtures**: [fixtures/](fixtures/) - Test data files
- **Testing guide**: [docs/testing.md](../../docs/testing.md) - Comprehensive testing documentation
- **Manual testing guide**: [docs/operations/MANUAL_TESTING_GUIDE.md](../../docs/operations/MANUAL_TESTING_GUIDE.md) - Step-by-step testing procedures

## Notes

- These scripts may require manual setup or configuration
- May not have comprehensive error handling
- Output may be verbose for debugging purposes
- May require user interaction
- Not included in CI/CD pipelines
