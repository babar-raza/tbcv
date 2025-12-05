# Contributing to TBCV

Thank you for your interest in contributing to TBCV (Truth-Based Content Validation System)! We welcome contributions from developers, documentation writers, and testers at all experience levels. This guide will help you understand our contribution process and standards.

## Table of Contents

1. [Welcome](#welcome)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Types of Contributions](#types-of-contributions)
5. [Code Standards](#code-standards)
6. [Testing](#testing)
7. [Pull Request Process](#pull-request-process)
8. [Agent Development](#agent-development)
9. [Release Process](#release-process)
10. [Community](#community)
11. [Code of Conduct](#code-of-conduct)
12. [Development Resources](#development-resources)

---

## Welcome

TBCV is an open-source intelligent content validation and enhancement system for technical documentation. We're building a comprehensive platform that validates markdown files, detects plugin usage patterns, generates actionable recommendations, and applies approved enhancements through a human-in-the-loop workflow.

### Contribution Types We Value

We accept contributions in many forms:

- **Code Contributions**: Bug fixes, new features, performance improvements, refactoring
- **Documentation**: README improvements, guide updates, code examples, API documentation
- **Bug Reports**: Issues with clear reproduction steps and context
- **Feature Requests**: Ideas for new validators, agents, or system capabilities
- **Testing**: Adding test coverage, writing integration tests, E2E testing
- **Agent Development**: Creating custom agents that extend TBCV's capabilities
- **Translations**: Help localizing documentation (future support)

### Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](##code-of-conduct). By participating, you agree to uphold this code. Please report unacceptable behavior to the maintainers.

---

## Getting Started

### Prerequisites

Before you start contributing, ensure you have:

- **Python 3.8+** installed ([Download Python](https://www.python.org/downloads/))
- **Git** for version control ([Download Git](https://git-scm.com/))
- **pip** or **pipenv** for package management
- **Text editor or IDE**: We recommend VS Code, PyCharm, or similar

Optional but recommended:
- **Ollama** for LLM-based validation testing ([Download Ollama](https://ollama.ai))
- **Docker** for containerized development
- **Linux/Mac preferred** for development (Windows support available via WSL2)

### Fork and Clone Repository

1. **Fork the repository**:
   - Visit https://github.com/your-org/tbcv
   - Click "Fork" in the top-right corner
   - This creates your own copy to work on

2. **Clone your fork locally**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/tbcv.git
   cd tbcv
   ```

3. **Add upstream remote** (to stay in sync with main repo):
   ```bash
   git remote add upstream https://github.com/your-org/tbcv.git
   git remote -v  # Verify both origin and upstream are set
   ```

### Development Environment Setup

1. **Create a Python virtual environment**:
   ```bash
   # Using venv (built-in)
   python -m venv venv

   # Or using conda
   conda create -n tbcv python=3.8
   conda activate tbcv
   ```

2. **Activate the environment**:
   ```bash
   # On Windows
   venv\Scripts\activate

   # On Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   # Core dependencies
   pip install -r requirements.txt

   # Development dependencies (testing, linting, formatting)
   pip install -r requirements-dev.txt  # if available

   # Or install manually
   pip install pytest pytest-asyncio pytest-cov black flake8 isort mypy
   ```

4. **Initialize the database**:
   ```bash
   python -c "from core.database import db_manager; db_manager.initialize_database()"
   ```

5. **Verify installation**:
   ```bash
   # Run health check
   python -c "from agents.base import agent_registry; print('Agents loaded:', len(agent_registry))"

   # Run a quick test
   pytest tests/core/test_config.py -v
   ```

### Running Tests Locally

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=. --cov-report=html

# Run specific test category
pytest -m unit
pytest -m integration
pytest -m e2e

# Run tests for a specific module
pytest tests/agents/test_fuzzy_detector.py -v

# Run in parallel (faster)
pytest -n auto
```

---

## Development Workflow

### Creating a Branch

Always create a feature branch from the latest `main`:

```bash
# Update local main from upstream
git fetch upstream
git checkout main
git merge upstream/main

# Create feature branch with descriptive name
git checkout -b feature/your-feature-name
# or for bug fixes
git checkout -b fix/issue-description
# or for documentation
git checkout -b docs/update-readme
```

#### Branch Naming Convention

- `feature/*` - New features or enhancements
- `fix/*` - Bug fixes
- `docs/*` - Documentation updates
- `test/*` - Test additions or improvements
- `refactor/*` - Code refactoring without behavior changes
- `perf/*` - Performance improvements
- `chore/*` - Dependencies, tooling, configuration

### Commit Message Conventions

We follow [Conventional Commits](https://www.conventionalcommits.org/) for clear commit history:

```
<type>(<scope>): <subject>

<body>

<footer>
```

#### Commit Types

- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, missing semicolons, etc.)
- **refactor**: Code refactoring without changing behavior
- **perf**: Performance improvements
- **test**: Adding or updating tests
- **chore**: Build configuration, dependencies, tooling

#### Examples

```bash
# Feature
git commit -m "feat(validator): add support for JSON schema validation"

# Bug fix
git commit -m "fix(fuzzy_detector): correct levenshtein distance calculation"

# Documentation
git commit -m "docs(readme): add quick start guide for MacOS"

# With body and footer
git commit -m "feat(agents): implement RecommendationCriticAgent

Add new agent to validate recommendation quality before processing.
Implements scoring algorithm based on confidence metrics.

Closes #123
Related to #456"
```

### Code Style and Linting

TBCV follows **PEP 8** with custom project conventions. We use automated tools to enforce consistency:

#### Black (Code Formatter)

```bash
# Format all Python files
black .

# Format specific directory
black agents/

# Check without modifying
black --check .
```

Configuration in `pyproject.toml`:
```toml
[tool.black]
line-length = 100
target-version = ['py38', 'py39', 'py310']
```

#### isort (Import Sorting)

```bash
# Sort imports in all files
isort .

# Sort specific file
isort agents/base.py

# Check without modifying
isort --check-only .
```

#### Flake8 (Linting)

```bash
# Check for style issues
flake8 .

# Ignore specific rules
flake8 . --ignore=E501,W503
```

Configuration in `.flake8`:
```ini
[flake8]
max-line-length = 100
exclude = .git,__pycache__,venv,.venv
ignore = E203,W503
```

#### Pre-commit Setup (Recommended)

Create `.pre-commit-config.yaml` to run checks automatically:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black

  - repo: https://github.com/PyCQA/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/PyCQA/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
```

Setup:
```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

### Type Hints and Mypy

All new code should include type hints. We use **mypy** for static type checking:

```python
# Good: Type hints for all parameters and return values
def validate_content(content: str, file_path: str, family: str) -> Dict[str, Any]:
    """Validate markdown content against multiple validators."""
    results: Dict[str, Any] = {}
    # ... implementation
    return results

# Run mypy
mypy . --ignore-missing-imports
```

Type hints benefits:
- Better IDE autocomplete and error detection
- Clearer function contracts
- Fewer runtime errors
- Better documentation

### Documentation Requirements

All public functions, classes, and modules must have docstrings:

```python
def fuzzy_match_plugins(
    text: str,
    plugins: List[str],
    threshold: float = 0.8
) -> List[Tuple[str, float]]:
    """
    Find fuzzy matches for plugin references in text.

    Uses Levenshtein distance and Jaro-Winkler similarity for matching.

    Args:
        text: The content to search for plugin references
        plugins: List of known plugin names
        threshold: Minimum similarity score (0.0-1.0)

    Returns:
        List of tuples (plugin_name, confidence_score) sorted by confidence

    Raises:
        ValueError: If threshold is not between 0.0 and 1.0

    Example:
        >>> matches = fuzzy_match_plugins("Using DocumentBuilder", ["DocumentBuilder"])
        >>> matches
        [("DocumentBuilder", 0.95)]
    """
    if not 0.0 <= threshold <= 1.0:
        raise ValueError(f"Threshold must be between 0.0 and 1.0, got {threshold}")
    # ... implementation
```

---

## Types of Contributions

### Bug Reports

If you find a bug, please open an issue using our bug report template:

#### Using GitHub Issue Template

1. Go to **Issues** → **New Issue**
2. Select **Bug Report** template
3. Fill in the required sections

#### What to Include

- **Clear title**: Concise description of the bug
- **Reproduction steps**: Exact steps to reproduce the issue
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Environment**:
  - Python version
  - OS (Windows/Mac/Linux)
  - TBCV version (if released)
  - Any relevant configuration
- **Logs**: Relevant error messages and stack traces
- **Screenshots**: Visual issues or error displays
- **Severity**: Critical/High/Medium/Low

#### Bug Report Template

```markdown
## Description
Brief description of the bug.

## Reproduction Steps
1. Step one
2. Step two
3. ...

## Expected Behavior
What should happen?

## Actual Behavior
What actually happens?

## Environment
- Python version: 3.8/3.9/3.10
- OS: Windows/Mac/Linux
- TBCV version: [version or main branch]

## Error Logs
```
<paste error messages and stack trace here>
```

## Severity
- [ ] Critical (system broken, data loss)
- [ ] High (major feature broken)
- [ ] Medium (feature works but with issues)
- [ ] Low (minor issue, workaround available)
```

### Feature Requests

Help shape TBCV's future! Share your ideas:

1. Go to **Issues** → **New Issue**
2. Select **Feature Request** template
3. Describe your idea with context

#### Feature Request Template

```markdown
## Feature Description
What feature would you like to see?

## Motivation
Why is this feature important? What problem does it solve?

## Proposed Solution
How should this feature work?

## Design Considerations
- Backward compatibility concerns?
- Performance implications?
- Configuration needs?

## Examples
How would this feature be used?

## Additional Context
Links to related issues, discussions, or external references
```

### Code Contributions

#### Small Fixes (Good for First-Time Contributors)

Good starter issues to look for:
- Typos in documentation or comments
- Small bug fixes with clear reproduction steps
- Adding missing docstrings
- Improving error messages
- Updating dependencies

Steps:
1. Find an issue labeled `good-first-issue`
2. Comment on the issue to claim it
3. Make the fix following the development workflow
4. Submit a pull request

#### Large Features

For significant features:

1. **Open a discussion first**
   - Create a GitHub Discussion or issue
   - Explain the feature and implementation approach
   - Get feedback from maintainers
   - Ensure alignment with project vision

2. **Design phase**
   - Document architecture
   - List affected components
   - Plan backward compatibility

3. **Implementation**
   - Follow development workflow
   - Write comprehensive tests
   - Update documentation
   - Add example usage

4. **Review and iterate**
   - Address code review feedback
   - Ensure tests pass
   - Update based on community input

#### Pull Request Checklist

Before submitting:

- [ ] Code follows project style guidelines (Black, isort, flake8)
- [ ] Type hints added for all public functions
- [ ] Docstrings added/updated
- [ ] Tests written and passing (`pytest` passes)
- [ ] Coverage maintained or improved
- [ ] No console warnings or errors
- [ ] Documentation updated (if needed)
- [ ] Commit messages follow conventions
- [ ] Branch is up-to-date with main
- [ ] No merge conflicts

### Documentation

Documentation improvements are highly valued! Areas to contribute:

- **README**: Installation guides, quick start examples
- **Architecture docs**: System design explanations
- **API docs**: Endpoint descriptions and examples
- **Troubleshooting**: Common issues and solutions
- **Code examples**: Usage patterns and snippets
- **Deployment guides**: Setup for different environments
- **Tutorial guides**: Step-by-step walkthroughs

#### Documentation Style Guide

- Use clear, concise language
- Write for the target audience (beginners, advanced users, operators)
- Include code examples with expected output
- Add diagrams or flowcharts for complex concepts
- Link to related documentation
- Keep line length around 100 characters for readability
- Use consistent formatting for code blocks

Example:

```markdown
## Validating Files

To validate a markdown file, use the `validate-file` command:

\`\`\`bash
python -m cli.main validate-file path/to/file.md --family words
\`\`\`

This will:
1. Load the file content
2. Check YAML frontmatter
3. Validate markdown syntax
4. Check for plugin references
5. Generate a report

The output will show:
- Validation results with severity levels
- Recommended improvements
- Links to relevant documentation
\`\`\`
```

---

## Code Standards

### Python Style Guide (PEP 8)

Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with these highlights:

- **Indentation**: 4 spaces (never tabs)
- **Line length**: Maximum 100 characters (enforced by Black)
- **Imports**: Group by standard library, third-party, local (isort)
- **Naming**:
  - Functions/variables: `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPER_SNAKE_CASE`
  - Private: prefix with `_` (e.g., `_private_method()`)

```python
# Good
def validate_yaml_frontmatter(content: str) -> bool:
    """Check if content has valid YAML frontmatter."""
    REQUIRED_FIELDS = {"title", "description"}
    # ... implementation

class YamlValidatorAgent:
    """Validates YAML frontmatter in markdown files."""

    def __init__(self):
        self._config = self._load_config()
```

### Project-Specific Conventions

#### Agent Development

- All agents inherit from `BaseAgent` in `agents/base.py`
- Implement `execute()` method
- Register in agent registry
- Follow agent naming: `*Agent` suffix

#### Validator Implementation

- Validators inherit from `BaseValidator`
- Return `ValidationResult` objects
- Support async execution
- Include confidence scores

#### Error Handling

```python
from svc.mcp_exceptions import MCPError, MCPValidationError

try:
    result = validate(content)
except ValueError as e:
    raise MCPValidationError(f"Validation failed: {str(e)}")
except Exception as e:
    raise MCPError(f"Internal error: {str(e)}")
```

### Testing Standards

#### Unit Tests

- Test individual functions/methods
- Mock external dependencies
- Aim for >80% coverage
- Use descriptive names: `test_<function>_<scenario>`

```python
import pytest
from agents.fuzzy_detector import FuzzyDetectorAgent

class TestFuzzyDetectorAgent:
    @pytest.fixture
    def agent(self):
        return FuzzyDetectorAgent()

    def test_fuzzy_match_returns_closest_match(self, agent):
        """Test that fuzzy matcher returns the closest match."""
        plugins = ["DocumentBuilder", "PageBuilder", "FileBuilder"]
        result = agent.find_matches("Document Builder", plugins, threshold=0.7)

        assert len(result) > 0
        assert result[0][0] == "DocumentBuilder"
        assert result[0][1] > 0.9

    def test_fuzzy_match_respects_threshold(self, agent):
        """Test that fuzzy matcher respects similarity threshold."""
        plugins = ["DocumentBuilder"]
        result = agent.find_matches("xyz", plugins, threshold=0.9)

        assert len(result) == 0
```

#### Integration Tests

- Test component interactions
- Use test fixtures and data
- Verify end-to-end workflows

```python
@pytest.mark.integration
async def test_validation_workflow():
    """Test complete validation workflow."""
    content = "# Test Document\n\nUsing DocumentBuilder..."

    validator = ContentValidatorAgent()
    result = await validator.validate(content, family="words")

    assert result.status == "success"
    assert len(result.issues) > 0
```

#### E2E Tests

- Test real-world scenarios
- Use actual files and databases
- Verify CLI and API behavior

```python
@pytest.mark.e2e
def test_cli_validate_file_integration(tmp_path):
    """Test CLI validate-file command with real file."""
    test_file = tmp_path / "test.md"
    test_file.write_text("# Test\nUsing DocumentBuilder")

    runner = CliRunner()
    result = runner.invoke(
        validate_file,
        [str(test_file), "--family", "words"]
    )

    assert result.exit_code == 0
    assert "validation" in result.output.lower()
```

---

## Testing

### Running the Test Suite

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/agents/test_fuzzy_detector.py

# Run specific test class
pytest tests/agents/test_fuzzy_detector.py::TestFuzzyDetectorAgent

# Run specific test method
pytest tests/agents/test_fuzzy_detector.py::TestFuzzyDetectorAgent::test_fuzzy_match_returns_closest_match

# Run tests matching pattern
pytest -k "fuzzy" -v

# Run tests with coverage
pytest --cov=. --cov-report=html --cov-report=term

# Run in parallel for speed
pip install pytest-xdist
pytest -n auto
```

### Writing New Tests

1. **Create test file** in appropriate `tests/` subdirectory
2. **Follow naming convention**: `test_*.py` or `*_test.py`
3. **Use descriptive test names**: `test_<function>_<scenario>`
4. **Use fixtures for setup**:
   ```python
   @pytest.fixture
   def sample_content():
       return "# Title\n\nContent here"
   ```
5. **Use parametrize for multiple cases**:
   ```python
   @pytest.mark.parametrize("input,expected", [
       ("test", True),
       ("", False),
       ("123", False),
   ])
   def test_is_valid(input, expected):
       assert is_valid(input) == expected
   ```

### Test Coverage Requirements

- **Minimum**: 70% overall coverage
- **Critical paths**: 90%+ coverage
- **View coverage report**: `open htmlcov/index.html` (after running with `--cov-report=html`)

### Integration Testing

To run integration tests requiring services:

```bash
# With Ollama running (for LLM validator tests)
TBCV_LLM_VALIDATOR__ENABLED=true pytest -m integration

# With live API
pytest -m integration --api-url http://localhost:8080
```

### E2E Testing

End-to-end tests verify complete workflows:

```bash
# Start server first
python main.py --mode api &

# Run E2E tests
pytest -m e2e --base-url http://localhost:8080

# Run specific E2E test
pytest tests/e2e/test_validation_workflow.py -v
```

---

## Pull Request Process

### Before You Submit

1. **Update your branch**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run tests locally**:
   ```bash
   pytest --cov=.
   mypy .
   flake8 .
   black --check .
   isort --check .
   ```

3. **Check for conflicts**:
   ```bash
   git status  # Should show no conflicts
   ```

### Submitting Your PR

1. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Open PR on GitHub**:
   - Go to https://github.com/your-org/tbcv
   - Click **New Pull Request**
   - Select your branch
   - Fill in the PR template

### PR Description Template

```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)
- [ ] Documentation update

## Related Issues
Closes #(issue number)

## Testing
- [ ] Added new tests
- [ ] All tests pass locally
- [ ] Existing tests still pass
- [ ] Coverage: __% (current) -> __% (after change)

## Documentation
- [ ] Updated README (if needed)
- [ ] Updated/added docstrings
- [ ] Updated related documentation

## Checklist
- [ ] Code follows style guidelines (Black, isort, flake8)
- [ ] Type hints added
- [ ] No console warnings
- [ ] Commit messages follow conventions
- [ ] Branch is up-to-date with main
- [ ] No merge conflicts
- [ ] Screenshots (if UI changes)

## Screenshots (if applicable)
Insert relevant screenshots here.
```

### Review Process

Your PR will be reviewed by maintainers:

1. **Automated checks**:
   - Tests run via CI/CD
   - Code style checked
   - Coverage verified

2. **Code review**:
   - One or more maintainers review code
   - Feedback provided as comments
   - Request changes if needed

3. **Addressing feedback**:
   ```bash
   # Make changes locally
   git add <files>
   git commit -m "Address review feedback"
   git push origin feature/your-feature-name
   # Push updates automatically to existing PR
   ```

4. **Approval and merge**:
   - PR approved when ready
   - Squashed and merged to main
   - Branch deleted

### Merging Criteria

A PR can be merged when:

- All tests pass
- Code review approved
- Coverage maintained/improved
- No conflicts with main branch
- Documentation updated (if needed)
- Commit messages follow conventions

---

## Agent Development

### Creating a Custom Agent

TBCV uses a multi-agent architecture. Here's how to create a new agent:

1. **Understand the base agent interface**:
   ```python
   # agents/base.py
   from abc import ABC, abstractmethod

   class BaseAgent(ABC):
       def __init__(self, agent_id: str, config: Dict[str, Any] = None):
           self.agent_id = agent_id
           self.config = config or {}

       @abstractmethod
       async def execute(self, **kwargs) -> Dict[str, Any]:
           """Execute the agent logic."""
           pass
   ```

2. **Create your agent**:
   ```python
   # agents/my_custom_agent.py
   from agents.base import BaseAgent
   from typing import Dict, Any, Optional

   class MyCustomAgent(BaseAgent):
       """Description of what your agent does."""

       def __init__(self, config: Optional[Dict[str, Any]] = None):
           super().__init__("my_custom_agent", config)

       async def execute(self, content: str, **kwargs) -> Dict[str, Any]:
           """
           Execute custom logic on content.

           Args:
               content: The markdown content to process
               **kwargs: Additional arguments

           Returns:
               Dictionary with results
           """
           try:
               # Your logic here
               result = self._process_content(content)
               return {
                   "status": "success",
                   "data": result
               }
           except Exception as e:
               return {
                   "status": "error",
                   "error": str(e)
               }

       def _process_content(self, content: str) -> Dict[str, Any]:
           """Helper method for content processing."""
           # Implementation
           pass
   ```

3. **Register your agent**:
   ```python
   # In agents/__init__.py
   from agents.my_custom_agent import MyCustomAgent
   from agents.base import agent_registry

   my_agent = MyCustomAgent()
   agent_registry.register(my_agent)
   ```

4. **Add tests**:
   ```python
   # tests/agents/test_my_custom_agent.py
   import pytest
   from agents.my_custom_agent import MyCustomAgent

   @pytest.mark.asyncio
   async def test_my_custom_agent_executes():
       agent = MyCustomAgent()
       result = await agent.execute("# Test content")

       assert result["status"] == "success"
       assert "data" in result
   ```

5. **Add to workflows** (if needed):
   - Update `agents/orchestrator.py` to include your agent
   - Add configuration to `config/agent.yaml`
   - Update documentation

### Agent Contract Requirements

All agents must:

- Inherit from `BaseAgent`
- Implement `execute()` method
- Return consistent response format
- Handle errors gracefully
- Include comprehensive logging
- Support async operations
- Have test coverage >80%
- Include docstrings

### Testing Custom Agents

```bash
# Run agent tests
pytest tests/agents/ -v

# Run specific agent tests
pytest tests/agents/test_my_custom_agent.py -v

# With coverage
pytest tests/agents/ --cov=agents --cov-report=html
```

---

## Release Process

### Versioning (SemVer)

TBCV follows [Semantic Versioning](https://semver.org/):

- **MAJOR** (X.0.0): Breaking changes
- **MINOR** (0.X.0): New features (backward compatible)
- **PATCH** (0.0.X): Bug fixes

Examples:
- `2.0.0` → `2.1.0` (new feature)
- `2.1.0` → `2.1.1` (bug fix)
- `2.1.1` → `3.0.0` (breaking changes)

### Release Notes

Create detailed release notes for each version:

```markdown
## Version 2.1.0 - 2024-03-15

### Features
- Add support for JSON schema validation
- Implement new RecommendationCriticAgent
- Improve fuzzy matching accuracy

### Bug Fixes
- Fix link validator timeout issues
- Correct levenshtein distance calculation
- Handle edge case in YAML validation

### Breaking Changes
- Remove deprecated CLI command `validate-batch`

### Deprecations
- `LegacyValidator` deprecated, use `ModularValidatorRouter` instead

### Contributors
- @contributor1
- @contributor2
```

### Changelog Maintenance

Keep `CHANGELOG.md` updated with each PR:

```markdown
# Changelog

All notable changes to this project are documented here.

## [Unreleased]
### Added
- New fuzzy matching algorithm with improved accuracy
- Support for custom validation rules

### Fixed
- Bug in link validation timeout handling

### Deprecated
- Old CLI command format (use new format instead)

## [2.0.0] - 2024-01-10
### Added
- Initial release with 19 agents
- Multi-tier validation system
- Web dashboard

### Fixed
- Various security issues
```

### Version Bumping Checklist

1. Update version in `__init__.py` or version file
2. Update `CHANGELOG.md`
3. Update `README.md` if needed
4. Create git tag: `git tag v2.1.0`
5. Push tags: `git push origin --tags`
6. Create GitHub release with release notes
7. Publish to PyPI (if applicable)

---

## Community

### Communication Channels

- **GitHub Issues**: Report bugs and request features
- **GitHub Discussions**: Ask questions and share ideas
- **Pull Requests**: Discuss implementation details
- **Discord** (if available): Real-time chat with community
- **Email**: Contact maintainers for private concerns

### Getting Help

- **Search existing issues** before asking
- **Check documentation** in `/docs` directory
- **Review examples** in `/examples` directory
- **Ask in Discussions** for general questions
- **Create an Issue** for reproducible bugs

### Contributor Recognition

We recognize contributors in:
- `CONTRIBUTORS.md` file
- Release notes
- Project README
- GitHub contributors page

### How to Get Recognized

Make any contribution:
- Commit code
- Write documentation
- Report and test bugs
- Answer questions in discussions
- Create tutorials or examples

---

## Code of Conduct

### Our Commitment

We are committed to providing a welcoming and inspiring community for all. We expect all contributors and community members to adhere to this code of conduct.

### Expected Behavior

- **Be respectful**: Respect differing opinions, viewpoints, and experiences
- **Be inclusive**: Welcome people of all backgrounds and identities
- **Be collaborative**: Work together to achieve common goals
- **Be honest**: Communicate openly and transparently
- **Be patient**: Remember that everyone is learning
- **Use inclusive language**: Avoid assumptions about people's backgrounds

### Unacceptable Behavior

We do not tolerate:
- Harassment or bullying in any form
- Discrimination based on race, ethnicity, religion, gender, sexual orientation, disability, age, or any other characteristic
- Offensive comments or slurs
- Deliberate intimidation or threats
- Unwanted sexual attention or advances
- Trolling or deliberately disruptive behavior
- Publishing others' private information without consent

### Reporting Issues

If you experience or witness unacceptable behavior:

1. **Document the incident**: Take screenshots, notes, or URLs if possible
2. **Report to maintainers**:
   - Email: [maintainer-email]
   - GitHub: Create private issue or contact directly
   - Discord: DM a moderator

3. **What happens next**:
   - Report is reviewed confidentially
   - Investigation conducted if necessary
   - Appropriate action taken
   - Follow-up with reporter when resolved

### Enforcement

Violations may result in:
- Request for apology or clarification
- Warning or temporary suspension
- Permanent ban from community

### Acknowledgment

This Code of Conduct is adapted from the [Contributor Covenant](https://www.contributor-covenant.org/).

---

## Development Resources

### Documentation

- [Architecture](docs/architecture.md) - System design and components
- [Configuration](docs/configuration.md) - System configuration guide
- [API Reference](docs/api_reference.md) - REST endpoints documentation
- [Security](docs/security.md) - Security architecture and best practices
- [Agents](docs/agents.md) - Detailed agent descriptions
- [Testing](docs/testing.md) - Test structure and guides

### Tools and Setup

- **Python**: https://www.python.org/
- **Git**: https://git-scm.com/
- **VS Code**: https://code.visualstudio.com/
- **PyCharm**: https://www.jetbrains.com/pycharm/
- **Ollama** (optional): https://ollama.ai

### Recommended Reading

- [PEP 8 Style Guide](https://www.python.org/dev/peps/pep-0008/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

### Useful Commands

```bash
# Code formatting
black .
isort .
flake8 .
mypy .

# Testing
pytest
pytest --cov=. --cov-report=html
pytest -m unit
pytest -m integration
pytest -m e2e

# Development
python main.py --mode api --reload
python -m cli.main --help

# Database
python -c "from core.database import db_manager; db_manager.initialize_database()"

# Cleaning
rm -rf __pycache__ .pytest_cache .mypy_cache htmlcov
find . -name "*.pyc" -delete
```

---

## Additional Resources

- **GitHub Project**: https://github.com/your-org/tbcv
- **Issue Tracker**: https://github.com/your-org/tbcv/issues
- **Discussions**: https://github.com/your-org/tbcv/discussions
- **Documentation**: https://github.com/your-org/tbcv/tree/main/docs

---

## Questions?

Don't hesitate to reach out! We're here to help. Start with:
1. Check the documentation
2. Search existing issues/discussions
3. Ask in GitHub Discussions
4. Contact maintainers

Thank you for being part of the TBCV community!
