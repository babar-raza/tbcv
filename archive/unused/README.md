# Archive: Unused Code

This directory contains code that was removed from the main codebase but preserved for reference.

## Files

### ollama_validator.py
- **Original Location:** `core/ollama_validator.py`
- **Date Archived:** 2025-11-23
- **Reason:** Unused in production code, only referenced by its own test
- **Description:** Alternative Ollama LLM integration implementation with contradiction and omission detection
- **Why Kept:** Contains potentially useful patterns for async LLM validation that could be referenced in future implementations
- **Related Test:** `test_ollama_validator.py`

### test_ollama_validator.py
- **Original Location:** `tests/core/test_ollama_validator.py`
- **Date Archived:** 2025-11-23
- **Reason:** Tests archived `ollama_validator.py` module
- **Description:** Unit tests for the archived OllamaValidator class

## Notes

The actual LLM validation functionality is implemented in:
- `core/ollama.py` - Low-level Ollama API client
- `agents/llm_validator.py` - Agent-level LLM validation for plugin requirements

These archived files represent an alternative implementation that was never integrated into the main system.
