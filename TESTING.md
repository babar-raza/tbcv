# TBCV Testing Quick Reference

## Prerequisites for Full-Stack Tests

```bash
# Start Ollama
ollama serve

# Verify Ollama is running
curl http://localhost:11434/api/tags

# Check model is available (example: mistral)
ollama list
```

## Test Commands

### Run Full-Stack Local Test (Single Command)

```bash
# Test with a specific file
python run_full_stack_test.py path/to/your/file.md

# Test with a folder
python run_full_stack_test.py path/to/folder/

# Run all full-stack tests
python run_full_stack_test.py

# Start server and run tests, then leave server running
KEEP_SERVER_RUNNING=1 python run_full_stack_test.py
```

### Run All Tests

```bash
# Default: unit + integration (skip local_heavy)
python run_all_tests.py

# Run everything including full-stack local tests
python run_all_tests.py --all

# Run only full-stack local tests
python run_all_tests.py --local-only

# Run only unit tests
python run_all_tests.py --unit

# Run only integration tests
python run_all_tests.py --integration

# Quick smoke tests
python run_all_tests.py --quick

# Specific test file
python run_all_tests.py --file tests/test_truth_validation.py
```

### Direct Pytest Commands

```bash
# Run specific full-stack test
pytest tests/test_full_stack_local.py -v -s --local-heavy

# Run only single file test
pytest tests/test_full_stack_local.py::test_full_stack_single_file_workflow -v -s --local-heavy

# Run only directory test
pytest tests/test_full_stack_local.py::test_full_stack_directory_workflow -v -s --local-heavy

# Run only mode switching test
pytest tests/test_full_stack_local.py::test_full_stack_mode_switching -v -s --local-heavy

# Run all tests except local_heavy
pytest tests/ -v -m "not local_heavy"
```

## View Results in Dashboard

After running tests:

```bash
# Start server if not running
python main.py --mode api

# Open dashboard
# Navigate to: http://localhost:8080/
# View validations: http://localhost:8080/validations
```

## Environment Variables

```bash
# Override test file
TEST_FILE=/path/to/custom.md python run_full_stack_test.py

# Override test directory
TEST_DIR=/path/to/custom/folder python run_full_stack_test.py

# Skip server management (assume already running)
SKIP_SERVER_START=1 python run_full_stack_test.py

# Keep server running after tests
KEEP_SERVER_RUNNING=1 python run_full_stack_test.py
```

## Configuration

Set validation mode in `config/main.yaml`:

```yaml
llm:
  enabled: true  # Must be true for LLM validation

validation:
  mode: two_stage  # Options: two_stage, heuristic_only, llm_only
  llm_thresholds:
    downgrade_threshold: 0.2
    confirm_threshold: 0.5
    upgrade_threshold: 0.8
```

## Test Categories

- **Unit tests**: Fast, with mocks, no external dependencies
- **Integration tests**: Real agents but mocked LLM (for two-stage pipeline testing)
- **Local/heavy tests**: Full-stack with real Ollama, real database, real everything

## Troubleshooting

### Ollama not found
```bash
# Install Ollama
curl https://ollama.ai/install.sh | sh

# Start Ollama
ollama serve

# Pull a model
ollama pull mistral
```

### Database errors
```bash
# Reset database
rm data/tbcv.db
python -c "from core.database import db_manager; db_manager.init_db()"
```

### Port already in use
```bash
# Find process using port 8080
lsof -i :8080

# Kill process
kill -9 <PID>
```
