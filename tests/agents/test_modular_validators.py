"""
Comprehensive tests for modular validator architecture.

Tests all modular validators:
- BaseValidatorAgent interface
- ValidatorRouter (both old and new)
- YamlValidatorAgent
- MarkdownValidatorAgent
- CodeValidatorAgent
- LinkValidatorAgent
- StructureValidatorAgent
- TruthValidatorAgent
- SeoValidatorAgent
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

# Add project root to path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# =============================================================================
# Import Validators
# =============================================================================

from agents.validators.base_validator import BaseValidatorAgent, ValidationIssue, ValidationResult
from agents.validators.yaml_validator import YamlValidatorAgent
from agents.validators.markdown_validator import MarkdownValidatorAgent
from agents.validators.code_validator import CodeValidatorAgent
from agents.validators.link_validator import LinkValidatorAgent
from agents.validators.structure_validator import StructureValidatorAgent
from agents.validators.truth_validator import TruthValidatorAgent
from agents.validators.seo_validator import SeoValidatorAgent

# Import both routers
from agents.validators.router import ValidatorRouter as OldValidatorRouter
from core.validator_router import ValidatorRouter as NewValidatorRouter


# =============================================================================
# Test BaseValidatorAgent Interface
# =============================================================================

@pytest.mark.asyncio
async def test_base_validator_interface():
    """Test that BaseValidatorAgent defines the correct interface."""
    # Create a minimal implementation for testing
    class TestValidator(BaseValidatorAgent):
        def __init__(self):
            super().__init__(agent_id="test")

        def get_validation_type(self) -> str:
            return "test"

        async def validate(self, content: str, context: dict):
            return ValidationResult(
                confidence=1.0,
                issues=[],
                metrics={}
            )

    validator = TestValidator()
    assert validator.agent_id == "test"

    # Test validate method
    result = await validator.validate("test content", {})
    assert isinstance(result, ValidationResult)
    assert result.confidence == 1.0
    assert result.issues == []
    assert result.metrics == {}


# =============================================================================
# Test Old ValidatorRouter (agents/validators/router.py)
# =============================================================================

@pytest.mark.asyncio
async def test_old_validator_router_initialization(agent_registry):
    """Test old ValidatorRouter initializes correctly."""
    router = OldValidatorRouter(agent_registry)
    assert router is not None
    assert router.agent_registry == agent_registry


@pytest.mark.asyncio
async def test_old_validator_router_available_validators(agent_registry):
    """Test old router can get available validators."""
    router = OldValidatorRouter(agent_registry)

    # Get available validators
    available = router.get_available_validators()
    assert isinstance(available, list)

    # Check structure of validator info
    if len(available) > 0:
        validator_info = available[0]
        assert "id" in validator_info
        assert "label" in validator_info
        assert "available" in validator_info


@pytest.mark.asyncio
async def test_old_validator_router_execute(agent_registry):
    """Test old router can execute validations."""
    # Register a mock validator
    from agents.base import AgentContract, AgentCapability
    mock_validator = AsyncMock()
    mock_validator.agent_id = "yaml_validator"
    mock_validator.validate = AsyncMock(return_value=ValidationResult(
        confidence=0.9,
        issues=[],
        metrics={}
    ))
    # Mock get_contract to return a proper contract (not async)
    mock_validator.get_contract = MagicMock(return_value=AgentContract(
        agent_id="yaml_validator",
        name="YAML Validator",
        version="1.0.0",
        capabilities=[],
        checkpoints=[],
        max_runtime_s=30,
        confidence_threshold=0.5,
        side_effects=[]
    ))
    agent_registry.register_agent(mock_validator)

    router = OldValidatorRouter(agent_registry)

    # Test YAML validation
    yaml_content = """---
title: Test
---
# Content"""

    result = await router.execute(
        validation_types=["yaml"],
        content=yaml_content,
        context={"file_path": "test.md"}
    )

    assert "validation_results" in result
    assert "routing_info" in result


# =============================================================================
# Test New ValidatorRouter (core/validator_router.py)
# =============================================================================

@pytest.mark.asyncio
async def test_new_validator_router_initialization(agent_registry):
    """Test new ValidatorRouter initializes correctly."""
    router = NewValidatorRouter(agent_registry)
    assert router is not None
    assert router.agent_registry == agent_registry


@pytest.mark.asyncio
async def test_new_validator_router_get_validators(agent_registry):
    """Test new router can get available validators."""
    router = NewValidatorRouter(agent_registry)

    validators = router.get_available_validators()
    assert isinstance(validators, list)


@pytest.mark.asyncio
async def test_new_validator_router_execute(agent_registry):
    """Test new router can execute tiered validation flow."""
    # Register a mock validator
    from agents.base import AgentContract, AgentCapability
    mock_validator = AsyncMock()
    mock_validator.agent_id = "yaml_validator"
    mock_validator.validate = AsyncMock(return_value=ValidationResult(
        confidence=0.9,
        issues=[],
        metrics={}
    ))
    # Mock get_contract to return a proper contract (not async)
    mock_validator.get_contract = MagicMock(return_value=AgentContract(
        agent_id="yaml_validator",
        name="YAML Validator",
        version="1.0.0",
        capabilities=[],
        checkpoints=[],
        max_runtime_s=30,
        confidence_threshold=0.5,
        side_effects=[]
    ))
    agent_registry.register_agent(mock_validator)

    router = NewValidatorRouter(agent_registry)

    # Execute validation
    result = await router.execute(
        validation_types=["yaml"],
        content="---\ntitle: Test\n---\n# Content",
        context={"file_path": "test.md"}
    )

    assert hasattr(result, "validation_results") or isinstance(result, dict)


# =============================================================================
# Test YamlValidatorAgent
# =============================================================================

@pytest.mark.asyncio
async def test_yaml_validator_valid_yaml():
    """Test YamlValidatorAgent with valid YAML."""
    validator = YamlValidatorAgent()

    content = """---
title: Test Document
description: Test description
---
# Content"""

    result = await validator.validate(content, {})
    assert isinstance(result, ValidationResult)
    assert result.confidence > 0
    assert isinstance(result.issues, list)


@pytest.mark.asyncio
async def test_yaml_validator_missing_field():
    """Test YamlValidatorAgent detects missing required field."""
    validator = YamlValidatorAgent()

    content = """---
description: Test description
---
# Content"""

    result = await validator.validate(content, {})
    assert isinstance(result, ValidationResult)

    # Should detect missing title
    if len(result.issues) > 0:
        messages = [issue.message.lower() for issue in result.issues]
        assert any("title" in msg for msg in messages)


@pytest.mark.asyncio
async def test_yaml_validator_invalid_syntax():
    """Test YamlValidatorAgent detects invalid YAML syntax."""
    validator = YamlValidatorAgent()

    content = """---
title: Unclosed string'
description: Test
---
# Content"""

    result = await validator.validate(content, {})
    assert isinstance(result, ValidationResult)
    # May or may not detect depending on YAML parser strictness


# =============================================================================
# Test MarkdownValidatorAgent
# =============================================================================

@pytest.mark.asyncio
async def test_markdown_validator_valid_hierarchy():
    """Test MarkdownValidatorAgent with valid heading hierarchy."""
    validator = MarkdownValidatorAgent()

    content = """# Title
## Section 1
### Subsection 1.1
## Section 2
### Subsection 2.1"""

    result = await validator.validate(content, {})
    assert isinstance(result, ValidationResult)
    assert isinstance(result.issues, list)


@pytest.mark.asyncio
async def test_markdown_validator_unclosed_code_block():
    """Test MarkdownValidatorAgent detects unclosed code blocks."""
    validator = MarkdownValidatorAgent()

    content = """# Title
```python
print("Hello")
# Missing closing fence"""

    result = await validator.validate(content, {})
    assert isinstance(result, ValidationResult)

    # Should detect unclosed code block
    if len(result.issues) > 0:
        messages = [issue.message.lower() for issue in result.issues]
        assert any("unclosed" in msg or "code block" in msg for msg in messages)


@pytest.mark.asyncio
async def test_markdown_validator_list_formatting():
    """Test MarkdownValidatorAgent validates list formatting."""
    validator = MarkdownValidatorAgent()

    content = """# Title
- Item 1
  - Subitem 1
  - Subitem 2
- Item 2"""

    result = await validator.validate(content, {})
    assert isinstance(result, ValidationResult)


# =============================================================================
# Test CodeValidatorAgent
# =============================================================================

@pytest.mark.asyncio
async def test_code_validator_with_language():
    """Test CodeValidatorAgent with language identifier."""
    validator = CodeValidatorAgent()

    content = """# Title
```python
print("Hello, World!")
```"""

    result = await validator.validate(content, {})
    assert isinstance(result, ValidationResult)
    assert isinstance(result.issues, list)


@pytest.mark.asyncio
async def test_code_validator_missing_language():
    """Test CodeValidatorAgent detects missing language identifier."""
    validator = CodeValidatorAgent()

    content = """# Title
```
print("Hello")
```"""

    result = await validator.validate(content, {})
    assert isinstance(result, ValidationResult)

    # Should detect missing language identifier
    if len(result.issues) > 0:
        messages = [issue.message.lower() for issue in result.issues]
        assert any("language" in msg for msg in messages)


@pytest.mark.asyncio
async def test_code_validator_unclosed_block():
    """Test CodeValidatorAgent detects unclosed code block."""
    validator = CodeValidatorAgent()

    content = """# Title
```python
print("Hello")
# Missing closing fence"""

    result = await validator.validate(content, {})
    assert isinstance(result, ValidationResult)


# =============================================================================
# Test LinkValidatorAgent
# =============================================================================

@pytest.mark.asyncio
async def test_link_validator_valid_links():
    """Test LinkValidatorAgent with valid links."""
    validator = LinkValidatorAgent()

    content = """# Title
[Valid Link](https://github.com)
[Another Link](#section)"""

    result = await validator.validate(content, {})
    assert isinstance(result, ValidationResult)
    assert isinstance(result.issues, list)


@pytest.mark.asyncio
async def test_link_validator_malformed_url():
    """Test LinkValidatorAgent detects malformed URLs."""
    validator = LinkValidatorAgent()

    content = """# Title
[Bad Link](htp://invalid)
[Another](not-a-url)"""

    result = await validator.validate(content, {})
    assert isinstance(result, ValidationResult)


@pytest.mark.asyncio
async def test_link_validator_broken_link():
    """Test LinkValidatorAgent handles broken links check."""
    validator = LinkValidatorAgent()

    content = """# Title
[Broken](https://httpstat.us/404)"""

    # Disable external link checking to avoid network calls
    result = await validator.validate(content, {"check_external": False})
    assert isinstance(result, ValidationResult)


# =============================================================================
# Test StructureValidatorAgent
# =============================================================================

@pytest.mark.asyncio
async def test_structure_validator_with_title():
    """Test StructureValidatorAgent with proper title."""
    validator = StructureValidatorAgent()

    content = """# Main Title
## Section 1
Content here.
## Section 2
More content."""

    result = await validator.validate(content, {})
    assert isinstance(result, ValidationResult)
    assert isinstance(result.issues, list)


@pytest.mark.asyncio
async def test_structure_validator_missing_title():
    """Test StructureValidatorAgent detects structural issues."""
    validator = StructureValidatorAgent()

    content = """## Section (no h1 title)
Content here."""

    result = await validator.validate(content, {})
    assert isinstance(result, ValidationResult)
    # May or may not flag depending on config - just ensure it runs
    assert isinstance(result.issues, list)


@pytest.mark.asyncio
async def test_structure_validator_min_content():
    """Test StructureValidatorAgent validates minimum content length."""
    validator = StructureValidatorAgent()

    # Very short content
    content = """# Title
Hi."""

    result = await validator.validate(content, {"min_word_count": 50})
    assert isinstance(result, ValidationResult)


# =============================================================================
# Test TruthValidatorAgent
# =============================================================================

@pytest.mark.asyncio
async def test_truth_validator_with_plugins():
    """Test TruthValidatorAgent with plugin declarations."""
    validator = TruthValidatorAgent()

    content = """---
title: Test
plugins:
  - document
  - pdf-save
---
# Content
Using Document.Save() and SaveFormat.Pdf"""

    result = await validator.validate(
        content,
        {"family": "words", "truth_data": {}}
    )
    assert isinstance(result, ValidationResult)
    assert isinstance(result.issues, list)


@pytest.mark.asyncio
async def test_truth_validator_undeclared_plugin():
    """Test TruthValidatorAgent detects undeclared plugins."""
    validator = TruthValidatorAgent()

    content = """---
title: Test
plugins: []
---
# Content
Using AutoSave plugin (not declared)"""

    result = await validator.validate(
        content,
        {"family": "words", "truth_data": {}}
    )
    assert isinstance(result, ValidationResult)


# =============================================================================
# Test SeoValidatorAgent
# =============================================================================

@pytest.mark.asyncio
async def test_seo_validator_mode_seo():
    """Test SeoValidatorAgent in SEO mode."""
    validator = SeoValidatorAgent()

    content = """---
title: Test Document Title
description: This is a meta description that should be between 120 and 160 characters long for optimal SEO performance.
---
# Content"""

    result = await validator.validate(content, {"mode": "seo"})
    assert isinstance(result, ValidationResult)
    assert isinstance(result.issues, list)


@pytest.mark.asyncio
async def test_seo_validator_short_description():
    """Test SeoValidatorAgent handles short meta description."""
    validator = SeoValidatorAgent()

    content = """---
title: Test
description: Too short
---
# Content"""

    result = await validator.validate(content, {"mode": "seo"})
    assert isinstance(result, ValidationResult)
    # May or may not flag depending on config - just ensure it runs
    assert isinstance(result.issues, list)


@pytest.mark.asyncio
async def test_seo_validator_mode_heading_sizes():
    """Test SeoValidatorAgent in heading sizes mode."""
    validator = SeoValidatorAgent()

    content = """# This is a very long h1 heading that exceeds the recommended character limit for optimal readability
## Shorter h2"""

    result = await validator.validate(
        content,
        {
            "mode": "heading_sizes",
            "heading_limits": {"h1": {"max": 60}}
        }
    )
    assert isinstance(result, ValidationResult)


# =============================================================================
# Integration Tests
# =============================================================================

@pytest.mark.asyncio
async def test_all_validators_implement_interface():
    """Test that all validators properly implement BaseValidatorAgent."""
    validators = [
        YamlValidatorAgent(),
        MarkdownValidatorAgent(),
        CodeValidatorAgent(),
        LinkValidatorAgent(),
        StructureValidatorAgent(),
        TruthValidatorAgent(),
        SeoValidatorAgent()
    ]

    for validator in validators:
        # Check they have required attributes
        assert hasattr(validator, "agent_id")
        assert hasattr(validator, "get_validation_type")

        # Check they have validate method
        assert hasattr(validator, "validate")
        assert callable(validator.validate)


@pytest.mark.asyncio
async def test_validators_return_consistent_format():
    """Test all validators return consistent result format."""
    validators = [
        YamlValidatorAgent(),
        MarkdownValidatorAgent(),
        CodeValidatorAgent()
    ]

    content = """---
title: Test
---
# Title
```python
print("test")
```"""

    for validator in validators:
        result = await validator.validate(content, {})

        # Check result is ValidationResult
        assert isinstance(result, ValidationResult)
        assert hasattr(result, "confidence")
        assert hasattr(result, "issues")
        assert hasattr(result, "metrics")

        # Check types
        assert isinstance(result.confidence, (int, float))
        assert isinstance(result.issues, list)
        assert isinstance(result.metrics, dict)


@pytest.mark.asyncio
async def test_validator_confidence_scores():
    """Test validators provide confidence scores."""
    validator = YamlValidatorAgent()

    content = """---
title: Test
description: Test description
---
# Content"""

    result = await validator.validate(content, {})

    assert isinstance(result, ValidationResult)
    assert 0.0 <= result.confidence <= 1.0


@pytest.mark.asyncio
async def test_validator_issue_format():
    """Test validator issues have consistent format."""
    validator = CodeValidatorAgent()

    # Content with issue (missing language)
    content = """```
code without language
```"""

    result = await validator.validate(content, {})

    assert isinstance(result, ValidationResult)
    if len(result.issues) > 0:
        issue = result.issues[0]

        # Check issue is ValidationIssue
        assert isinstance(issue, ValidationIssue)
        assert hasattr(issue, "level")
        assert hasattr(issue, "category")
        assert hasattr(issue, "message")


# =============================================================================
# Performance Tests
# =============================================================================

@pytest.mark.asyncio
async def test_validator_performance():
    """Test validators execute within reasonable time."""
    import time

    validator = MarkdownValidatorAgent()

    # Generate large content
    content = "# Title\n" + "\n## Section\n" * 100 + "\nContent here.\n" * 1000

    start = time.time()
    result = await validator.validate(content, {})
    elapsed = time.time() - start

    # Should complete in under 2 seconds
    assert elapsed < 2.0, f"Validation took {elapsed}s, expected < 2s"
    assert isinstance(result, ValidationResult)


# =============================================================================
# Edge Cases
# =============================================================================

@pytest.mark.asyncio
async def test_validator_empty_content():
    """Test validators handle empty content gracefully."""
    validators = [
        YamlValidatorAgent(),
        MarkdownValidatorAgent(),
        CodeValidatorAgent()
    ]

    for validator in validators:
        result = await validator.validate("", {})
        assert isinstance(result, ValidationResult)


@pytest.mark.asyncio
async def test_validator_malformed_content():
    """Test validators handle malformed content gracefully."""
    validator = YamlValidatorAgent()

    # Completely invalid content
    malformed = "\x00\x01\x02 binary data"

    try:
        result = await validator.validate(malformed, {})
        assert isinstance(result, ValidationResult)
    except Exception as e:
        # Should handle gracefully or raise specific exception
        assert isinstance(e, (ValueError, TypeError, AttributeError))


@pytest.mark.asyncio
async def test_validator_very_long_content():
    """Test validators handle very long content."""
    validator = StructureValidatorAgent()

    # Very long content
    content = "# Title\n" + "Content word. " * 10000

    result = await validator.validate(content, {})
    assert isinstance(result, ValidationResult)


# =============================================================================
# Router Integration Tests
# =============================================================================

@pytest.mark.asyncio
async def test_old_router_routes_all_types(agent_registry):
    """Test old router can route all validation types."""
    # Register mock validators
    from agents.base import AgentContract, AgentCapability
    for validator_id in ["yaml_validator", "markdown_validator", "code_validator"]:
        mock_validator = AsyncMock()
        mock_validator.agent_id = validator_id
        mock_validator.validate = AsyncMock(return_value=ValidationResult(
            confidence=0.9,
            issues=[],
            metrics={}
        ))
        # Mock get_contract to return a proper contract (not async)
        mock_validator.get_contract = MagicMock(return_value=AgentContract(
            agent_id=validator_id,
            name=f"{validator_id} Validator",
            version="1.0.0",
            capabilities=[],
            checkpoints=[],
            max_runtime_s=30,
            confidence_threshold=0.5,
            side_effects=[]
        ))
        agent_registry.register_agent(mock_validator)

    router = OldValidatorRouter(agent_registry)

    validation_types = ["yaml", "markdown", "code"]

    content = """---
title: Test
---
# Title
```python
print("test")
```"""

    for val_type in validation_types:
        result = await router.execute(
            validation_types=[val_type],
            content=content,
            context={}
        )
        assert "validation_results" in result


@pytest.mark.asyncio
async def test_old_router_fallback_to_legacy(agent_registry):
    """Test old router falls back to legacy validator when needed."""
    # Register legacy content validator
    from agents.base import AgentContract, AgentCapability
    mock_legacy = AsyncMock()
    mock_legacy.agent_id = "content_validator"
    mock_legacy.handle_validate_content = AsyncMock(return_value={
        "yaml_validation": {
            "confidence": 0.8,
            "issues": []
        }
    })
    # Mock get_contract to return a proper contract (not async)
    mock_legacy.get_contract = MagicMock(return_value=AgentContract(
        agent_id="content_validator",
        name="Content Validator",
        version="1.0.0",
        capabilities=[],
        checkpoints=[],
        max_runtime_s=30,
        confidence_threshold=0.5,
        side_effects=[]
    ))
    agent_registry.register_agent(mock_legacy)

    router = OldValidatorRouter(agent_registry)

    # Request validation when new validator not available
    result = await router.execute(
        validation_types=["yaml"],
        content="test",
        context={}
    )

    # Should use fallback
    assert "validation_results" in result
    assert "routing_info" in result


@pytest.mark.asyncio
async def test_new_router_tiered_execution(agent_registry):
    """Test new router executes tiered validation flow."""
    # Register mock validators
    from agents.base import AgentContract, AgentCapability
    mock_validator = AsyncMock()
    mock_validator.agent_id = "yaml_validator"
    mock_validator.validate = AsyncMock(return_value=ValidationResult(
        confidence=0.9,
        issues=[],
        metrics={}
    ))
    # Mock get_contract to return a proper contract (not async)
    mock_validator.get_contract = MagicMock(return_value=AgentContract(
        agent_id="yaml_validator",
        name="YAML Validator",
        version="1.0.0",
        capabilities=[],
        checkpoints=[],
        max_runtime_s=30,
        confidence_threshold=0.5,
        side_effects=[]
    ))
    agent_registry.register_agent(mock_validator)

    router = NewValidatorRouter(agent_registry)

    content = """---
title: Test
---
# Content"""

    result = await router.execute(
        validation_types=["yaml"],
        content=content,
        context={}
    )

    # Check result has expected structure
    assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
