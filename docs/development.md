# TBCV Development Guide

Complete guide for contributing to and extending the TBCV system.

## Development Setup

### Prerequisites

- **Python**: 3.8+ (3.10+ recommended)
- **Ollama**: For LLM validation (optional but recommended)
- **Git**: For version control
- **Virtual environment**: venv or conda

### Initial Setup

**1. Clone Repository**:
```bash
git clone https://github.com/your-org/tbcv.git
cd tbcv
```

**2. Create Virtual Environment**:
```bash
# Using venv
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Or using conda
conda create -n tbcv python=3.10
conda activate tbcv
```

**3. Install Dependencies**:
```bash
# Install all dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e .
```

**4. Setup Ollama** (optional):
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull model
ollama pull llama2

# Verify
ollama list
```

**5. Initialize Database**:
```bash
# Run startup checks
python startup_check.py

# Or manually initialize
python -c "from core.database import db_manager; db_manager.initialize_database()"
```

**6. Verify Installation**:
```bash
# Check CLI
tbcv --help

# Check API
python -m tbcv.api.server &
curl http://localhost:8080/health

# Run tests
pytest tests/ -v
```

### Project Structure

```
tbcv/
├── agents/               # Agent implementations
│   ├── orchestrator.py       # Workflow coordinator
│   ├── truth_manager.py      # Truth data management
│   ├── fuzzy_detector.py     # Plugin detection
│   ├── content_validator.py  # Content validation
│   ├── llm_validator.py      # LLM semantic validation
│   ├── content_enhancer.py   # Content enhancement
│   ├── recommendation_agent.py  # Recommendation generation
│   └── code_analyzer.py      # Code quality analysis
│
├── api/                  # FastAPI application
│   ├── server.py            # Main API server
│   ├── dashboard.py         # Web dashboard routes
│   └── services/            # API service layer
│
├── cli/                  # Command-line interface
│   └── main.py              # CLI commands (Click/Typer)
│
├── core/                 # Core functionality
│   ├── database.py          # SQLAlchemy ORM & DB manager
│   ├── ollama.py            # Ollama client
│   ├── logging.py           # Logging configuration
│   ├── io_win.py            # Windows I/O utilities
│   └── startup_checks.py    # System startup validation
│
├── config/               # Configuration files
│   ├── main.yaml            # Main configuration
│   ├── agent.yaml           # Agent-specific config
│   ├── perf.json            # Performance settings
│   └── tone.json            # LLM tone configuration
│
├── truth/                # Truth data (plugin definitions)
│   ├── words.json           # Aspose.Words plugins
│   ├── cells.json           # Aspose.Cells plugins
│   ├── slides.json          # Aspose.Slides plugins
│   ├── pdf.json             # Aspose.PDF plugins
│   └── words/               # Words plugin combinations
│
├── templates/            # Jinja2 HTML templates
│   ├── base.html
│   ├── dashboard_home.html
│   ├── validations_list.html
│   └── ...
│
├── tests/                # Test suite
│   ├── conftest.py          # Pytest configuration
│   ├── test_*.py            # Test modules
│   └── run_all_tests.py     # Test runner
│
├── docs/                 # Documentation
├── data/                 # Runtime data
│   ├── logs/                # Log files
│   └── cache/               # Cache storage
│
├── main.py               # Application entry point
├── requirements.txt      # Python dependencies
├── tbcv.db              # SQLite database
└── README.md            # Project overview
```

## Development Workflow

### Code Style

**Python Style Guide**:
- **PEP 8**: Follow Python style guide
- **Line length**: 100 characters max
- **Imports**: Use isort for sorting
- **Formatting**: Use black for auto-formatting

**Formatting Commands**:
```bash
# Format code with black
black .

# Sort imports
isort .

# Lint with flake8
flake8 .

# Type checking with mypy
mypy agents/ core/ api/
```

**Pre-commit Checklist**:
```bash
# 1. Format code
black .
isort .

# 2. Lint
flake8 .

# 3. Type check
mypy .

# 4. Run tests
pytest tests/ -v

# 5. Check coverage
pytest tests/ --cov=. --cov-report=html
```

### Git Workflow

**Branching Strategy**:
```bash
# Main branch: production-ready code
main

# Development branch: integration branch
develop

# Feature branches
feature/add-new-validator
feature/improve-fuzzy-detection

# Bug fix branches
fix/yaml-parsing-error
fix/database-connection-timeout

# Release branches
release/v2.1.0
```

**Commit Messages**:
```bash
# Format: <type>(<scope>): <subject>

# Types: feat, fix, docs, style, refactor, test, chore

# Good examples:
feat(fuzzy): add Jaro-Winkler similarity algorithm
fix(database): resolve connection pool exhaustion
docs(api): update endpoint documentation
refactor(orchestrator): simplify workflow coordination
test(validation): add edge cases for YAML parsing
```

**Pull Request Process**:
1. Create feature branch from `develop`
2. Implement changes with tests
3. Ensure all tests pass
4. Update documentation
5. Create pull request to `develop`
6. Address code review feedback
7. Merge after approval

### Testing

**Test Structure**:
```
tests/
├── conftest.py                    # Fixtures and configuration
├── test_framework.py              # Framework/MCP tests
├── test_smoke_agents.py           # Agent smoke tests
├── test_generic_validator.py      # Generic validation tests
├── test_validation_persistence.py # Database persistence tests
├── test_enhancer_consumes_validation.py  # Enhancement tests
├── test_truths_and_rules.py       # Truth validation tests
├── test_fuzzy_logic.py            # Fuzzy detection tests
├── test_recommendations.py        # Recommendation tests
├── test_truth_validation.py       # Truth data validation
├── test_cli_web_parity.py         # CLI vs API parity
├── test_endpoints_live.py         # Live API endpoint tests
├── test_endpoints_offline.py      # Offline endpoint tests
├── test_websocket.py              # WebSocket tests
├── test_performance.py            # Performance benchmarks
├── test_full_stack_local.py       # Full integration tests
├── test_idempotence_and_schemas.py # Idempotence tests
└── test_everything.py             # Comprehensive test suite
```

**Running Tests**:
```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_fuzzy_logic.py -v

# Run specific test
pytest tests/test_fuzzy_logic.py::test_plugin_detection -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
open htmlcov/index.html

# Run tests in parallel
pytest tests/ -n auto

# Run only failed tests
pytest --lf

# Run tests matching pattern
pytest -k "fuzzy or validation"
```

**Writing Tests**:

```python
# tests/test_example.py
import pytest
from agents.fuzzy_detector import FuzzyDetectorAgent

@pytest.fixture
def fuzzy_agent():
    """Create fuzzy detector agent for testing."""
    return FuzzyDetectorAgent()

def test_plugin_detection_exact_match(fuzzy_agent):
    """Test exact plugin name detection."""
    content = "Enable the AutoSave plugin."
    result = fuzzy_agent.detect_plugins(content, family="words")

    assert len(result["plugins"]) > 0
    assert "AutoSave" in [p["name"] for p in result["plugins"]]
    assert result["plugins"][0]["confidence"] > 0.9

def test_plugin_detection_fuzzy_match(fuzzy_agent):
    """Test fuzzy plugin name detection."""
    content = "Enable auto save feature."
    result = fuzzy_agent.detect_plugins(content, family="words")

    # Should detect "AutoSave" with fuzzy matching
    assert len(result["plugins"]) > 0
    assert result["plugins"][0]["confidence"] > 0.7

@pytest.mark.asyncio
async def test_async_validation():
    """Test async validation workflow."""
    from agents.orchestrator import OrchestratorAgent

    orchestrator = OrchestratorAgent()
    result = await orchestrator.execute_workflow(
        workflow_type="validate_file",
        file_path="test.md",
        content="Sample content"
    )

    assert result["status"] in ["completed", "failed"]
```

**Test Fixtures** (`conftest.py`):
```python
import pytest
from core.database import db_manager

@pytest.fixture(scope="session")
def test_database():
    """Create test database."""
    db_manager.initialize_database()
    yield db_manager
    # Cleanup after tests
    db_manager.close()

@pytest.fixture
def sample_validation():
    """Create sample validation result."""
    return {
        "file_path": "test.md",
        "status": "completed",
        "confidence": 0.85,
        "issues": []
    }
```

### Adding a New Agent

**Step 1: Create Agent Class**:
```python
# agents/custom_agent.py
from __future__ import annotations
from typing import Dict, Any
from agents.base import BaseAgent

class CustomAgent(BaseAgent):
    """
    Custom agent for specialized validation.

    Capabilities:
    - capability_1: Description
    - capability_2: Description
    """

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(agent_id="custom_agent")
        self.config = config or {}

    async def process_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Process MCP request."""
        if method == "custom_validate":
            return await self.custom_validate(params)
        else:
            raise ValueError(f"Unknown method: {method}")

    async def custom_validate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform custom validation."""
        content = params.get("content", "")

        # Validation logic here
        issues = []
        confidence = 1.0

        return {
            "status": "success",
            "issues": issues,
            "confidence": confidence
        }

    def get_contract(self) -> Dict[str, Any]:
        """Return agent contract."""
        return {
            "name": "CustomAgent",
            "version": "1.0",
            "capabilities": [
                "custom_validate"
            ]
        }
```

**Step 2: Register Agent**:
```python
# api/server.py
def register_agents():
    """Register all agents."""
    from agents.custom_agent import CustomAgent

    # ... existing agents ...

    custom_agent = CustomAgent()
    agent_registry.register(custom_agent)
```

**Step 3: Add Configuration**:
```yaml
# config/agent.yaml
custom_agent:
  enabled: true
  timeout_seconds: 30
  custom_setting: value
```

**Step 4: Add Tests**:
```python
# tests/test_custom_agent.py
import pytest
from agents.custom_agent import CustomAgent

@pytest.fixture
def custom_agent():
    return CustomAgent()

def test_custom_validate(custom_agent):
    """Test custom validation."""
    result = await custom_agent.custom_validate({
        "content": "Test content"
    })

    assert result["status"] == "success"
    assert "issues" in result
```

**Step 5: Update Documentation**:
```markdown
# docs/agents.md

## 9. CustomAgent

**Location**: `agents/custom_agent.py`
**Purpose**: Specialized validation for custom use cases

### Configuration
...
```

### Adding a New Endpoint

**Step 1: Define Endpoint**:
```python
# api/server.py or api/additional_endpoints.py

@app.post("/api/custom/validate")
async def custom_validate(
    request: CustomValidateRequest
) -> CustomValidateResponse:
    """
    Custom validation endpoint.

    Args:
        request: Custom validation request

    Returns:
        CustomValidateResponse: Validation results
    """
    try:
        # Get agent
        custom_agent = agent_registry.get("custom_agent")
        if not custom_agent:
            raise HTTPException(status_code=503, detail="Agent unavailable")

        # Process request
        result = await custom_agent.process_request(
            method="custom_validate",
            params=request.dict()
        )

        return CustomValidateResponse(**result)

    except Exception as e:
        logger.exception("Custom validation failed")
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 2: Define Pydantic Models**:
```python
# api/server.py
from pydantic import BaseModel, Field

class CustomValidateRequest(BaseModel):
    """Custom validation request."""
    content: str = Field(..., description="Content to validate")
    options: Dict[str, Any] = Field(default_factory=dict)

class CustomValidateResponse(BaseModel):
    """Custom validation response."""
    status: str
    issues: List[Dict[str, Any]]
    confidence: float
```

**Step 3: Add Tests**:
```python
# tests/test_endpoints_live.py
def test_custom_validate_endpoint(client):
    """Test custom validation endpoint."""
    response = client.post("/api/custom/validate", json={
        "content": "Test content",
        "options": {}
    })

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "issues" in data
```

**Step 4: Update API Documentation**:
```markdown
# docs/api_reference.md

## Custom Validation

### POST /api/custom/validate
...
```

### Adding a New CLI Command

**Step 1: Define Command**:
```python
# cli/main.py

@app.command()
def custom_validate(
    file_path: Path = typer.Argument(..., help="File to validate"),
    option: str = typer.Option("default", "--option", "-o", help="Custom option"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output")
):
    """
    Custom validation command.

    Example:
        tbcv custom-validate tutorial.md --option advanced
    """
    console = Console()

    try:
        # Read file
        content = file_path.read_text(encoding="utf-8")

        # Call agent or API
        from agents.custom_agent import CustomAgent
        agent = CustomAgent()
        result = agent.custom_validate({
            "content": content,
            "option": option
        })

        # Display results
        if verbose:
            console.print(Panel(
                f"[bold]Validation Results[/bold]\n"
                f"Status: {result['status']}\n"
                f"Issues: {len(result['issues'])}\n"
                f"Confidence: {result['confidence']:.2%}"
            ))
        else:
            console.print(f"✓ Validation completed: {result['status']}")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
```

**Step 2: Add Tests**:
```python
# tests/test_cli_web_parity.py
from click.testing import CliRunner
from cli.main import app

def test_custom_validate_command():
    """Test custom validate CLI command."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        # Create test file
        with open("test.md", "w") as f:
            f.write("Test content")

        # Run command
        result = runner.invoke(app, ["custom-validate", "test.md"])

        assert result.exit_code == 0
        assert "Validation completed" in result.output
```

### Database Schema Changes

**Step 1: Create Migration**:
```bash
# Install alembic if not already
pip install alembic

# Initialize alembic (if first time)
alembic init alembic

# Create migration
alembic revision -m "Add custom_field to validations"
```

**Step 2: Edit Migration**:
```python
# alembic/versions/xxx_add_custom_field.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    """Add custom_field column."""
    op.add_column('validation_results',
        sa.Column('custom_field', sa.String(255), nullable=True)
    )

def downgrade():
    """Remove custom_field column."""
    op.drop_column('validation_results', 'custom_field')
```

**Step 3: Update ORM Model**:
```python
# core/database.py
class ValidationResult(Base):
    __tablename__ = "validation_results"

    # ... existing columns ...
    custom_field = Column(String(255), nullable=True)
```

**Step 4: Apply Migration**:
```bash
# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Adding Truth Data

**Step 1: Add Plugin to JSON**:
```json
// truth/words.json
{
  "family": "words",
  "plugins": [
    {
      "name": "NewPlugin",
      "category": "Productivity",
      "description": "Description of new plugin",
      "url": "https://docs.aspose.com/words/new-plugin",
      "aliases": ["New Plugin", "new-plugin"],
      "keywords": ["new", "plugin", "feature"]
    }
  ]
}
```

**Step 2: Validate Schema**:
```bash
python startup_check.py
```

**Step 3: Test Detection**:
```python
# tests/test_truths_and_rules.py
def test_new_plugin_detection():
    """Test detection of new plugin."""
    from agents.fuzzy_detector import FuzzyDetectorAgent

    agent = FuzzyDetectorAgent()
    result = agent.detect_plugins("Enable NewPlugin", family="words")

    assert len(result["plugins"]) > 0
    assert "NewPlugin" in [p["name"] for p in result["plugins"]]
```

## Debugging

### Debug Mode

**Enable Debug Logging**:
```python
# In code
import logging
logging.basicConfig(level=logging.DEBUG)

# Or via environment
export LOG_LEVEL=DEBUG
```

**Debug API Requests**:
```bash
# Start with debug logging
uvicorn tbcv.api.server:app --reload --log-level debug

# Test endpoint with verbose output
curl -v http://localhost:8080/api/validate \
  -H "Content-Type: application/json" \
  -d '{"content":"test","file_path":"test.md"}'
```

**Debug Agent Communication**:
```python
# Add logging to agent
import logging
logger = logging.getLogger(__name__)

async def process_request(self, method, params):
    logger.debug(f"Processing {method} with params: {params}")
    result = await self.some_operation(params)
    logger.debug(f"Result: {result}")
    return result
```

### Common Issues

**Issue: Import Errors**

```bash
# Solution: Install in development mode
pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/tbcv"
```

**Issue: Database Locked**

```bash
# Solution: Close existing connections
rm tbcv.db
python -c "from core.database import db_manager; db_manager.initialize_database()"
```

**Issue: Ollama Connection Failed**

```bash
# Solution: Start Ollama service
ollama serve

# Verify
curl http://localhost:11434/api/tags
```

## Performance Optimization

### Profiling

**Memory Profiling**:
```python
from memory_profiler import profile

@profile
def memory_intensive_function():
    # Function to profile
    pass
```

**Time Profiling**:
```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Code to profile
validate_content(content)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

**Benchmarking**:
```python
# tests/test_performance.py
import pytest
import time

def test_validation_performance():
    """Benchmark validation performance."""
    content = "Sample content " * 1000

    start = time.time()
    for _ in range(100):
        validate_content(content)
    duration = time.time() - start

    avg_time = duration / 100
    assert avg_time < 0.1  # Should complete in <100ms
```

### Optimization Tips

**Database Optimization**:
```python
# Use bulk inserts
db_manager.bulk_insert_validations(validation_list)

# Add indexes
CREATE INDEX idx_validation_file_path ON validation_results(file_path);
CREATE INDEX idx_recommendation_status ON recommendations(status);

# Use connection pooling
from sqlalchemy.pool import QueuePool
engine = create_engine(url, poolclass=QueuePool, pool_size=20)
```

**Caching Optimization**:
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def expensive_computation(param):
    # Expensive operation
    return result
```

**Concurrency Optimization**:
```python
import asyncio

# Use asyncio.gather for parallel execution
results = await asyncio.gather(
    validate_file_1(),
    validate_file_2(),
    validate_file_3()
)
```

## Documentation

### Updating Documentation

**1. Code Documentation**:
```python
def validate_content(content: str, family: str = "words") -> Dict[str, Any]:
    """
    Validate content for plugin usage and formatting.

    Args:
        content: Content to validate
        family: Plugin family (words, cells, slides, pdf)

    Returns:
        Dictionary containing:
            - status: Validation status (pass/fail)
            - issues: List of validation issues
            - confidence: Confidence score (0-1)

    Raises:
        ValueError: If family is invalid

    Example:
        >>> result = validate_content("Enable AutoSave", family="words")
        >>> print(result["status"])
        pass
    """
    pass
```

**2. API Documentation**:
- Update `docs/api_reference.md` for new endpoints
- Add examples and request/response schemas
- Document error codes

**3. User Documentation**:
- Update relevant guides in `docs/`
- Add troubleshooting steps
- Include code examples

### Generating Documentation

**API Docs** (Swagger/ReDoc):
```bash
# Start server
uvicorn tbcv.api.server:app

# Access docs
open http://localhost:8080/docs
open http://localhost:8080/redoc
```

**Code Documentation**:
```bash
# Generate with pdoc
pip install pdoc
pdoc --html --output-dir docs/api agents/ core/ api/

# Or use Sphinx
pip install sphinx
sphinx-quickstart
sphinx-apidoc -o docs/ .
make html
```

## Contributing

### Contribution Guidelines

**Before Contributing**:
1. Read existing documentation
2. Check for existing issues/PRs
3. Discuss major changes first

**Pull Request Checklist**:
- [ ] Code follows style guide (black, isort, flake8)
- [ ] Tests added for new functionality
- [ ] All tests pass (`pytest tests/ -v`)
- [ ] Documentation updated
- [ ] Commit messages follow convention
- [ ] No merge conflicts with main branch

**Code Review Process**:
1. Submit PR with clear description
2. Address automated checks (CI/CD)
3. Respond to reviewer feedback
4. Update based on comments
5. Obtain approval from maintainer
6. Merge after approval

### Getting Help

**Resources**:
- **Documentation**: See `docs/` directory
- **Issues**: GitHub issues for bugs/features
- **Discussions**: GitHub discussions for questions
- **Chat**: Discord/Slack for real-time help

**Reporting Bugs**:
```markdown
## Bug Report

**Description**: Clear description of bug

**Steps to Reproduce**:
1. Step one
2. Step two
3. Step three

**Expected Behavior**: What should happen

**Actual Behavior**: What actually happens

**Environment**:
- OS: Windows 10 / Ubuntu 22.04
- Python: 3.10.5
- TBCV Version: 2.0.0

**Logs**:
```
Paste relevant logs here
```
```

## Release Process

### Versioning

**Semantic Versioning** (MAJOR.MINOR.PATCH):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

**Version Bump**:
```bash
# Update version in VERSION.txt
echo "2.1.0" > VERSION.txt

# Update CHANGELOG.md
# Tag release
git tag -a v2.1.0 -m "Release v2.1.0"
git push origin v2.1.0
```

### Release Checklist

- [ ] All tests pass
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped
- [ ] Release notes written
- [ ] Git tag created
- [ ] PyPI package published (if applicable)

## Related Documentation

- [Architecture](architecture.md) - System architecture
- [Agents](agents.md) - Agent reference
- [API Reference](api_reference.md) - REST API docs
- [Testing](testing.md) - Testing guide
- [Troubleshooting](troubleshooting.md) - Common issues
