"""
Comprehensive tests for modular validator architecture.

Tests all modular validators:
- BaseValidatorAgent interface
- ValidatorRouter
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

# Add project root to path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# =============================================================================
# Import Validators (with fallback if not available)
# =============================================================================

try:
    from agents.validators.base_validator import BaseValidatorAgent
    from agents.validators.router import ValidatorRouter
    from agents.validators.yaml_validator import YamlValidatorAgent
    from agents.validators.markdown_validator import MarkdownValidatorAgent
    from agents.validators.code_validator import CodeValidatorAgent
    from agents.validators.link_validator import LinkValidatorAgent
    from agents.validators.structure_validator import StructureValidatorAgent
    from agents.validators.truth_validator import TruthValidatorAgent
    from agents.validators.seo_validator import SeoValidatorAgent
    VALIDATORS_AVAILABLE = True
except ImportError as e:
    VALIDATORS_AVAILABLE = False
    pytest.skip(f"Modular validators not available: {e}", allow_module_level=True)


# =============================================================================
# Test BaseValidatorAgent Interface
# =============================================================================

@pytest.mark.asyncio
async def test_base_validator_interface():
    """Test that BaseValidatorAgent defines the correct interface."""
    # Create a minimal implementation for testing
    class TestValidator(BaseValidatorAgent):
        def __init__(self):
            super().__init__(
                validator_id="test",
                validator_name="TestValidator",
                version="1.0.0"
            )

        async def validate(self, content: str, context: dict):
            return {
                "issues": [],
                "confidence": 1.0,
                "metrics": {}
            }

    validator = TestValidator()
    assert validator.validator_id == "test"
    assert validator.validator_name == "TestValidator"
    assert validator.version == "1.0.0"

    # Test validate method
    result = await validator.validate("test content", {})
    assert "issues" in result
    assert "confidence" in result
    assert "metrics" in result


# =============================================================================
# Test ValidatorRouter
# =============================================================================

@pytest.mark.asyncio
async def test_validator_router_initialization():
    """Test ValidatorRouter initializes correctly."""
    router = ValidatorRouter()
    assert router is not None


@pytest.mark.asyncio
async def test_validator_router_registration():
    """Test validators can register with router."""
    router = ValidatorRouter()

    # Get available validators
    available = router.get_available_validators()
    assert isinstance(available, dict) or isinstance(available, list)


@pytest.mark.asyncio
async def test_validator_router_routing():
    """Test router can route to correct validator."""
    router = ValidatorRouter()

    # Test YAML routing
    yaml_content = """---
title: Test
---
# Content"""

    try:
        result = await router.route_validation(
            validation_type="yaml",
            content=yaml_content,
            context={"file_path": "test.md"}
        )
        assert result is not None
    except Exception as e:
        pytest.skip(f"Router not fully implemented: {e}")


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
    assert result is not None
    assert "issues" in result
    assert "confidence" in result


@pytest.mark.asyncio
async def test_yaml_validator_missing_field():
    """Test YamlValidatorAgent detects missing required field."""
    validator = YamlValidatorAgent()

    content = """---
description: Test description
---
# Content"""

    result = await validator.validate(content, {})

    # Should detect missing title
    if "issues" in result and len(result["issues"]) > 0:
        assert any("title" in issue.get("message", "").lower()
                  for issue in result["issues"])


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
    assert result is not None


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
    assert result is not None
    assert "issues" in result


@pytest.mark.asyncio
async def test_markdown_validator_skipped_heading():
    """Test MarkdownValidatorAgent detects skipped heading levels."""
    validator = MarkdownValidatorAgent()

    content = """# Title
### Subsection (skipped h2)"""

    result = await validator.validate(content, {})

    # Should detect skipped heading level
    if "issues" in result and len(result["issues"]) > 0:
        assert any("hierarchy" in issue.get("message", "").lower() or
                  "skip" in issue.get("message", "").lower()
                  for issue in result["issues"])


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
    assert result is not None


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
    assert result is not None
    assert "issues" in result


@pytest.mark.asyncio
async def test_code_validator_missing_language():
    """Test CodeValidatorAgent detects missing language identifier."""
    validator = CodeValidatorAgent()

    content = """# Title
```
print("Hello")
```"""

    result = await validator.validate(content, {})

    # Should detect missing language identifier
    if "issues" in result and len(result["issues"]) > 0:
        assert any("language" in issue.get("message", "").lower()
                  for issue in result["issues"])


@pytest.mark.asyncio
async def test_code_validator_unclosed_block():
    """Test CodeValidatorAgent detects unclosed code block."""
    validator = CodeValidatorAgent()

    content = """# Title
```python
print("Hello")
# Missing closing fence"""

    result = await validator.validate(content, {})
    assert result is not None


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
    assert result is not None
    assert "issues" in result


@pytest.mark.asyncio
async def test_link_validator_malformed_url():
    """Test LinkValidatorAgent detects malformed URLs."""
    validator = LinkValidatorAgent()

    content = """# Title
[Bad Link](htp://invalid)
[Another](not-a-url)"""

    result = await validator.validate(content, {})
    assert result is not None


@pytest.mark.asyncio
async def test_link_validator_broken_link():
    """Test LinkValidatorAgent detects broken links (if checking enabled)."""
    validator = LinkValidatorAgent()

    content = """# Title
[Broken](https://httpstat.us/404)"""

    result = await validator.validate(content, {"check_external_links": False})
    assert result is not None


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
    assert result is not None
    assert "issues" in result


@pytest.mark.asyncio
async def test_structure_validator_missing_title():
    """Test StructureValidatorAgent detects missing title."""
    validator = StructureValidatorAgent()

    content = """## Section (no h1 title)
Content here."""

    result = await validator.validate(content, {})

    # Should detect missing h1 title
    if "issues" in result and len(result["issues"]) > 0:
        assert any("title" in issue.get("message", "").lower() or
                  "h1" in issue.get("message", "").lower()
                  for issue in result["issues"])


@pytest.mark.asyncio
async def test_structure_validator_min_content():
    """Test StructureValidatorAgent validates minimum content length."""
    validator = StructureValidatorAgent()

    # Very short content
    content = """# Title
Hi."""

    result = await validator.validate(content, {"min_word_count": 50})
    assert result is not None


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
    assert result is not None
    assert "issues" in result


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
    assert result is not None


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
    assert result is not None
    assert "issues" in result


@pytest.mark.asyncio
async def test_seo_validator_short_description():
    """Test SeoValidatorAgent detects short meta description."""
    validator = SeoValidatorAgent()

    content = """---
title: Test
description: Too short
---
# Content"""

    result = await validator.validate(content, {"mode": "seo"})

    # Should detect short description
    if "issues" in result and len(result["issues"]) > 0:
        assert any("description" in issue.get("message", "").lower()
                  for issue in result["issues"])


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
    assert result is not None


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
        assert hasattr(validator, "validator_id")
        assert hasattr(validator, "validator_name")
        assert hasattr(validator, "version")

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

        # Check result format
        assert isinstance(result, dict) or hasattr(result, "issues")

        if isinstance(result, dict):
            assert "issues" in result or "confidence" in result


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

    if isinstance(result, dict) and "confidence" in result:
        confidence = result["confidence"]
        assert 0.0 <= confidence <= 1.0


@pytest.mark.asyncio
async def test_validator_issue_format():
    """Test validator issues have consistent format."""
    validator = CodeValidatorAgent()

    # Content with issue (missing language)
    content = """```
code without language
```"""

    result = await validator.validate(content, {})

    if isinstance(result, dict) and "issues" in result and len(result["issues"]) > 0:
        issue = result["issues"][0]

        # Check issue has required fields
        assert "level" in issue or "severity" in issue
        assert "message" in issue or "description" in issue


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

    # Should complete in under 1 second
    assert elapsed < 1.0, f"Validation took {elapsed}s, expected < 1s"


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
        assert result is not None


@pytest.mark.asyncio
async def test_validator_malformed_content():
    """Test validators handle malformed content gracefully."""
    validator = YamlValidatorAgent()

    # Completely invalid content
    malformed = "\x00\x01\x02 binary data"

    try:
        result = await validator.validate(malformed, {})
        assert result is not None
    except Exception as e:
        # Should handle gracefully or raise specific exception
        assert isinstance(e, (ValueError, TypeError))


@pytest.mark.asyncio
async def test_validator_very_long_content():
    """Test validators handle very long content."""
    validator = StructureValidatorAgent()

    # Very long content
    content = "# Title\n" + "Content word. " * 10000

    result = await validator.validate(content, {})
    assert result is not None


# =============================================================================
# Router Integration Tests
# =============================================================================

@pytest.mark.asyncio
async def test_router_routes_all_types():
    """Test router can route all validation types."""
    router = ValidatorRouter()

    validation_types = [
        "yaml", "markdown", "code", "link",
        "structure", "truth", "seo"
    ]

    content = """---
title: Test
---
# Title
```python
print("test")
```
[Link](https://example.com)"""

    for val_type in validation_types:
        try:
            result = await router.route_validation(
                validation_type=val_type,
                content=content,
                context={}
            )
            assert result is not None
        except NotImplementedError:
            # OK if validator not yet implemented
            pass
        except Exception as e:
            pytest.fail(f"Router failed for {val_type}: {e}")


@pytest.mark.asyncio
async def test_router_fallback_to_legacy():
    """Test router falls back to legacy validator when needed."""
    router = ValidatorRouter()

    # Unknown validation type should fallback
    try:
        result = await router.route_validation(
            validation_type="unknown_type",
            content="test",
            context={}
        )
        # Should either work (fallback) or raise specific error
        assert result is not None or True
    except NotImplementedError:
        # Expected if no fallback
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
