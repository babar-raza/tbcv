# Quick integration test for ConfigLoader with validators
import asyncio
import pytest

from agents.validators.yaml_validator import YamlValidatorAgent
from agents.validators.markdown_validator import MarkdownValidatorAgent
from agents.validators.code_validator import CodeValidatorAgent
from agents.validators.link_validator import LinkValidatorAgent
from agents.validators.structure_validator import StructureValidatorAgent
from agents.validators.seo_validator import SeoValidatorAgent
from agents.validators.truth_validator import TruthValidatorAgent


@pytest.mark.asyncio
async def test_yaml_validator_with_config():
    """Test YAML validator uses config properly."""
    validator = YamlValidatorAgent()
    result = await validator.validate(
        "---\ntitle: Test\n---\n# Hello",
        {"profile": "strict", "family": "words"}
    )
    assert result.confidence > 0
    assert result.metrics.get("profile") == "strict"
    assert result.metrics.get("family") == "words"


@pytest.mark.asyncio
async def test_markdown_validator_with_config():
    """Test Markdown validator uses config properly."""
    validator = MarkdownValidatorAgent()
    result = await validator.validate(
        "# Hello\n\n```\ncode\n```",
        {"profile": "default"}
    )
    assert result.confidence > 0
    assert result.metrics.get("profile") == "default"


@pytest.mark.asyncio
async def test_code_validator_with_config():
    """Test Code validator uses config properly."""
    validator = CodeValidatorAgent()
    result = await validator.validate(
        "# Title\n```python\nprint('hello')\n```",
        {"profile": "strict"}
    )
    assert result.confidence > 0
    assert result.metrics.get("profile") == "strict"


@pytest.mark.asyncio
async def test_link_validator_with_config():
    """Test Link validator uses config properly."""
    validator = LinkValidatorAgent()
    result = await validator.validate(
        "[test](https://example.com)",
        {"profile": "default"}
    )
    assert result.confidence > 0
    assert result.metrics.get("profile") == "default"


@pytest.mark.asyncio
async def test_structure_validator_with_config():
    """Test Structure validator uses config properly."""
    validator = StructureValidatorAgent()
    result = await validator.validate(
        "# Title\n\nSome content here that is long enough to pass validation.\n\n## Section 1\n\nMore content.",
        {"profile": "default"}
    )
    assert result.confidence > 0
    assert result.metrics.get("profile") == "default"


@pytest.mark.asyncio
async def test_family_override_applies():
    """Test that family overrides are applied correctly."""
    validator = YamlValidatorAgent()

    # With 'words' family (which has strict profile override)
    result_words = await validator.validate(
        "---\ntitle: Test\n---\n# Hello",
        {"profile": "default", "family": "words"}
    )

    # Without family
    result_no_family = await validator.validate(
        "---\ntitle: Test\n---\n# Hello",
        {"profile": "default"}
    )

    # Both should work
    assert result_words.confidence > 0
    assert result_no_family.confidence > 0


@pytest.mark.asyncio
async def test_seo_validator_with_config():
    """Test SEO validator uses config properly."""
    validator = SeoValidatorAgent()
    # Long enough H1 to pass validation
    result = await validator.validate(
        "# This is a good heading that is long enough\n\n## Section heading here\n\nContent here.",
        {"profile": "default"}
    )
    assert result.confidence > 0
    assert result.metrics.get("profile") == "default"


@pytest.mark.asyncio
async def test_seo_validator_heading_sizes_mode():
    """Test SEO validator in heading sizes mode."""
    validator = SeoValidatorAgent()
    result = await validator.validate(
        "# Short\n\n## Section\n\nContent.",
        {"profile": "heading_sizes_only", "mode": "heading_sizes"}
    )
    assert result.confidence > 0
    # Short H1 should be flagged
    assert any("too_short" in i.category for i in result.issues)


@pytest.mark.asyncio
async def test_seo_validator_strict_profile():
    """Test SEO validator with strict profile."""
    validator = SeoValidatorAgent()
    result = await validator.validate(
        "## Section without H1 first\n\n# H1 after H2\n\nContent.",
        {"profile": "strict", "family": "words"}
    )
    assert result.confidence > 0
    # Multiple SEO issues expected
    assert result.metrics.get("profile") == "strict"


@pytest.mark.asyncio
async def test_truth_validator_with_config():
    """Test Truth validator uses config properly."""
    validator = TruthValidatorAgent()
    result = await validator.validate(
        "# Document about Word processing\n\nThis document explains how to use DOCX files.",
        {"profile": "default", "family": "words"}
    )
    assert result.confidence > 0
    assert result.metrics.get("profile") == "default"
    assert result.metrics.get("family") == "words"
    # Phase tracking
    assert "phase1_issues" in result.metrics
    assert "phase2_issues" in result.metrics


@pytest.mark.asyncio
async def test_truth_validator_3phase_flow():
    """Test Truth validator 3-phase flow structure."""
    validator = TruthValidatorAgent()
    result = await validator.validate(
        "# Document with forbidden pattern hardcoded_path\n\nContent here.",
        {"profile": "strict", "family": "words"}
    )
    assert result.confidence > 0
    # Should have metrics for all phases
    assert "phase1_issues" in result.metrics
    assert "phase2_issues" in result.metrics
    assert "merged_issues" in result.metrics
    assert "llm_enabled" in result.metrics


@pytest.mark.asyncio
async def test_truth_validator_rule_based_only():
    """Test Truth validator in rule-based only mode."""
    validator = TruthValidatorAgent()
    result = await validator.validate(
        "# Simple document\n\nNo special content.",
        {"profile": "rule_based_only"}
    )
    assert result.confidence > 0
    assert result.metrics.get("profile") == "rule_based_only"
