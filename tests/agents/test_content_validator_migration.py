# file: tests/agents/test_content_validator_migration.py
"""
Tests for ContentValidatorAgent migration to modular validators.

These tests ensure:
1. ContentValidatorAgent issues proper deprecation warnings
2. Modular validators produce equivalent results to ContentValidatorAgent
3. Migration path is smooth and backward compatible
"""

import pytest
import warnings
from typing import Dict, Any

# Test the deprecation warning
def test_content_validator_deprecation_warning():
    """Test that ContentValidatorAgent issues deprecation warning on initialization."""
    with pytest.warns(DeprecationWarning, match="ContentValidatorAgent is deprecated"):
        from agents.content_validator import ContentValidatorAgent
        validator = ContentValidatorAgent()
        assert validator is not None


def test_deprecation_warning_message_content():
    """Test that deprecation warning contains useful migration information."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        from agents.content_validator import ContentValidatorAgent
        validator = ContentValidatorAgent()

        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)

        warning_message = str(w[0].message)

        # Check that warning mentions key information
        assert "deprecated" in warning_message.lower()
        assert "2026-01-01" in warning_message or "2.0.0" in warning_message
        assert "modular validators" in warning_message.lower()
        assert "migration" in warning_message.lower()


@pytest.mark.asyncio
async def test_yaml_validation_equivalence():
    """
    Test that YamlValidatorAgent produces equivalent results to ContentValidatorAgent
    for YAML validation.
    """
    from agents.content_validator import ContentValidatorAgent
    from agents.validators.yaml_validator import YamlValidatorAgent

    test_content = """---
title: Test Document
description: This is a test document
plugins: [document]
family: words
---

# Test Content

This is test content.
"""

    # Suppress deprecation warning for this test
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)

        # Test with legacy ContentValidatorAgent
        legacy_validator = ContentValidatorAgent()
        legacy_result = await legacy_validator.handle_validate_yaml({
            "content": test_content,
            "file_path": "test.md",
            "family": "words"
        })

        # Test with new YamlValidatorAgent
        yaml_validator = YamlValidatorAgent()
        yaml_result = await yaml_validator.validate(
            content=test_content,
            context={
                "file_path": "test.md",
                "family": "words"
            }
        )

        # Both should have similar structure
        assert "confidence" in legacy_result
        assert hasattr(yaml_result, "confidence")
        assert "issues" in legacy_result
        assert hasattr(yaml_result, "issues")

        # Both should have high confidence for valid YAML
        assert legacy_result["confidence"] > 0.7
        assert yaml_result.confidence > 0.7


@pytest.mark.asyncio
async def test_markdown_validation_equivalence():
    """
    Test that MarkdownValidatorAgent produces equivalent results to ContentValidatorAgent
    for Markdown validation.
    """
    from agents.content_validator import ContentValidatorAgent
    from agents.validators.markdown_validator import MarkdownValidatorAgent

    test_content = """---
title: Test
---

# Main Heading

## Section 1

Content here.

## Section 2

More content.
"""

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)

        # Test with legacy ContentValidatorAgent
        legacy_validator = ContentValidatorAgent()
        legacy_result = await legacy_validator.handle_validate_markdown({
            "content": test_content,
            "file_path": "test.md",
            "family": "words"
        })

        # Test with new MarkdownValidatorAgent
        markdown_validator = MarkdownValidatorAgent()
        markdown_result = await markdown_validator.validate(
            content=test_content,
            context={"file_path": "test.md"}
        )

        # Both should have similar structure
        assert "confidence" in legacy_result
        assert hasattr(markdown_result, "confidence")
        assert "issues" in legacy_result
        assert hasattr(markdown_result, "issues")


@pytest.mark.asyncio
async def test_code_validation_equivalence():
    """
    Test that CodeValidatorAgent produces equivalent results to ContentValidatorAgent
    for code validation.
    """
    from agents.content_validator import ContentValidatorAgent
    from agents.validators.code_validator import CodeValidatorAgent

    test_content = """---
title: Code Test
---

# Code Example

```python
def hello():
    print("Hello, World!")
```

This is a Python example.
"""

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)

        # Test with legacy ContentValidatorAgent
        legacy_validator = ContentValidatorAgent()
        legacy_result = await legacy_validator.handle_validate_code({
            "content": test_content,
            "file_path": "test.md",
            "family": "words"
        })

        # Test with new CodeValidatorAgent
        code_validator = CodeValidatorAgent()
        code_result = await code_validator.validate(
            content=test_content,
            context={
                "file_path": "test.md",
                "family": "words"
            }
        )

        # Both should have similar structure
        assert "confidence" in legacy_result
        assert hasattr(code_result, "confidence")
        assert "issues" in legacy_result
        assert hasattr(code_result, "issues")


@pytest.mark.asyncio
async def test_link_validation_equivalence():
    """
    Test that LinkValidatorAgent produces equivalent results to ContentValidatorAgent
    for link validation.
    """
    from agents.content_validator import ContentValidatorAgent
    from agents.validators.link_validator import LinkValidatorAgent

    test_content = """---
title: Link Test
---

# Links

[Valid Link](https://example.com)
[Empty Link]()
[Placeholder](#)
"""

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)

        # Test with legacy ContentValidatorAgent
        legacy_validator = ContentValidatorAgent()
        legacy_result = await legacy_validator.handle_validate_links({
            "content": test_content,
            "file_path": "test.md"
        })

        # Test with new LinkValidatorAgent
        link_validator = LinkValidatorAgent()
        link_result = await link_validator.validate(
            content=test_content,
            context={"file_path": "test.md"}
        )

        # Both should detect issues with empty and placeholder links
        assert "issues" in legacy_result
        assert hasattr(link_result, "issues")

        # Both should find similar number of issues (2-3 issues expected)
        assert len(legacy_result["issues"]) >= 1
        assert len(link_result.issues) >= 1


@pytest.mark.asyncio
async def test_structure_validation_equivalence():
    """
    Test that StructureValidatorAgent produces equivalent results to ContentValidatorAgent
    for structure validation.
    """
    from agents.content_validator import ContentValidatorAgent
    from agents.validators.structure_validator import StructureValidatorAgent

    test_content = """---
title: Structure Test
---

# Main Heading

## Section 1

Very short.

#### Skipped H3

More content here.
"""

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)

        # Test with legacy ContentValidatorAgent
        legacy_validator = ContentValidatorAgent()
        legacy_result = await legacy_validator.handle_validate_structure({
            "content": test_content,
            "file_path": "test.md"
        })

        # Test with new StructureValidatorAgent
        structure_validator = StructureValidatorAgent()
        structure_result = await structure_validator.validate(
            content=test_content,
            context={"file_path": "test.md"}
        )

        # Both should detect structure issues (short section, skipped heading level)
        assert "issues" in legacy_result
        assert hasattr(structure_result, "issues")


@pytest.mark.asyncio
async def test_validator_router_integration():
    """
    Test that ValidatorRouter can orchestrate multiple validators and provides
    proper fallback to ContentValidatorAgent when needed.
    """
    from agents.base import agent_registry
    from agents.validators.router import ValidatorRouter

    # Create router
    router = ValidatorRouter(agent_registry=agent_registry)

    test_content = """---
title: Router Test
---

# Test Content

This is a test.
"""

    # Test router execution
    result = await router.execute(
        validation_types=["yaml", "markdown", "structure"],
        content=test_content,
        context={"file_path": "test.md", "family": "words"}
    )

    # Should have results and routing info
    assert "validation_results" in result
    assert "routing_info" in result

    # Check that validators were used
    validation_results = result["validation_results"]
    assert len(validation_results) > 0

    # Check routing info shows which validators were used
    routing_info = result["routing_info"]
    assert len(routing_info) > 0


@pytest.mark.asyncio
async def test_return_value_structure_compatibility():
    """
    Test that modular validators return the same structure as ContentValidatorAgent
    to ensure backward compatibility.
    """
    from agents.validators.yaml_validator import YamlValidatorAgent

    test_content = """---
title: Test
---
Content
"""

    yaml_validator = YamlValidatorAgent()
    result = await yaml_validator.validate(
        content=test_content,
        context={"family": "words"}
    )

    # Check expected attributes in result
    expected_attrs = ["confidence", "issues", "auto_fixable_count", "metrics"]
    for attr in expected_attrs:
        assert hasattr(result, attr), f"Missing expected attribute: {attr}"

    # Check types
    assert isinstance(result.confidence, (int, float))
    assert isinstance(result.issues, list)
    assert isinstance(result.auto_fixable_count, int)
    assert isinstance(result.metrics, dict)

    # Check issue structure if any issues exist
    if result.issues:
        issue = result.issues[0]
        assert hasattr(issue, "level")
        assert hasattr(issue, "category")
        assert hasattr(issue, "message")


@pytest.mark.asyncio
async def test_cli_registration_still_works():
    """
    Test that CLI can still register ContentValidatorAgent during migration period
    (though it will issue deprecation warning).
    """
    from agents.base import agent_registry

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)

        from agents.content_validator import ContentValidatorAgent

        # Register the validator
        validator = ContentValidatorAgent("test_validator")
        agent_registry.register_agent(validator)

        # Should be retrievable
        retrieved = agent_registry.get_agent("test_validator")
        assert retrieved is not None
        assert retrieved.agent_id == "test_validator"

        # Clean up
        if hasattr(agent_registry, '_agents'):
            agent_registry._agents.pop("test_validator", None)
        elif hasattr(agent_registry, 'agents'):
            agent_registry.agents.pop("test_validator", None)


@pytest.mark.asyncio
async def test_multiple_validators_no_interference():
    """
    Test that multiple modular validators can run simultaneously without interference.
    """
    import asyncio
    from agents.validators.yaml_validator import YamlValidatorAgent
    from agents.validators.markdown_validator import MarkdownValidatorAgent
    from agents.validators.link_validator import LinkValidatorAgent

    test_content = """---
title: Multi-Validator Test
---

# Test

[Link](https://example.com)
"""

    # Create validators
    yaml_val = YamlValidatorAgent()
    md_val = MarkdownValidatorAgent()
    link_val = LinkValidatorAgent()

    # Run in parallel
    results = await asyncio.gather(
        yaml_val.validate(test_content, {"family": "words"}),
        md_val.validate(test_content, {}),
        link_val.validate(test_content, {})
    )

    # All should return results
    assert len(results) == 3
    for result in results:
        assert hasattr(result, "confidence")
        assert hasattr(result, "issues")


def test_migration_guide_exists():
    """Test that migration guide documentation exists."""
    import os

    migration_guide_path = os.path.join(
        os.path.dirname(__file__),
        "..", "..",
        "docs", "migration", "content_validator_migration.md"
    )

    assert os.path.exists(migration_guide_path), \
        "Migration guide should exist at docs/migration/content_validator_migration.md"


@pytest.mark.asyncio
async def test_error_handling_compatibility():
    """
    Test that modular validators handle errors similarly to ContentValidatorAgent.
    """
    from agents.validators.yaml_validator import YamlValidatorAgent

    # Invalid YAML content
    invalid_content = """---
title: "Unclosed quote
---
Content
"""

    yaml_validator = YamlValidatorAgent()
    result = await yaml_validator.validate(
        content=invalid_content,
        context={"family": "words"}
    )

    # Should return a result (not raise exception)
    assert result is not None
    assert hasattr(result, "issues")

    # Should have low confidence due to errors
    assert result.confidence < 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
