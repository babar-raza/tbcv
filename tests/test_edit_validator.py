# file: tests/test_edit_validator.py
"""
Unit tests for EditValidator - Phase 2.

Tests cover:
- Edit validation
- Preservation checking
- Pre-enhancement checks
- Post-enhancement checks
- Enhanced safety score calculation
"""

import pytest
from agents.edit_validator import (
    EditValidator,
    PreservationValidation,
    PreEnhancementCheck,
    PostEnhancementCheck,
)
from agents.recommendation_enhancer import PreservationRules


# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def validator():
    """Create EditValidator instance."""
    return EditValidator()


@pytest.fixture
def preservation_rules():
    """Standard preservation rules for testing."""
    return PreservationRules(
        preserve_keywords=["Aspose.Words", "Document", ".NET"],
        preserve_product_names=["Aspose.Words for .NET"],
        preserve_technical_terms=["NuGet", "class", "namespace"],
        preserve_code_blocks=True,
        max_content_reduction_percent=10.0
    )


@pytest.fixture
def sample_content():
    """Sample markdown content."""
    return """---
title: Test Article
---

# Introduction

This guide demonstrates Aspose.Words for .NET usage.

## Prerequisites

- NuGet package manager
- Visual Studio

## Code Example

```csharp
using Aspose.Words;
var doc = new Document();
```

## Features

1. Document processing
2. Format conversion
3. Content manipulation
"""


# ==============================================================================
# EditValidator.validate_edit() Tests
# ==============================================================================

class TestValidateEdit:
    """Tests for validate_edit method."""

    def test_valid_edit_preserves_keywords(self, validator, preservation_rules):
        """Test that valid edits with keywords pass validation."""
        original = "Use Aspose.Words and Document classes with .NET for document processing."
        edited = "Use Aspose.Words and Document classes with .NET for advanced document processing."

        recommendation = {"id": "rec_001", "type": "missing_info"}

        result = validator.validate_edit(original, edited, recommendation, preservation_rules)

        assert result.is_valid is True
        assert "Aspose.Words" in result.keywords_preserved
        assert "Document" in result.keywords_preserved
        assert ".NET" in result.keywords_preserved
        assert len(result.keywords_lost) == 0
        assert result.keyword_preservation_score == 1.0

    def test_invalid_edit_loses_keywords(self, validator, preservation_rules):
        """Test that edits losing keywords fail validation."""
        original = "Use Aspose.Words and Document classes."
        edited = "Use the library and classes."

        recommendation = {"id": "rec_002", "type": "missing_info"}

        result = validator.validate_edit(original, edited, recommendation, preservation_rules)

        assert result.is_valid is False
        assert "Aspose.Words" in result.keywords_lost
        assert "Document" in result.keywords_lost
        assert result.keyword_preservation_score < 1.0
        assert any(v.violation_type == "keyword_loss" for v in result.violations)

    def test_excessive_reduction_fails(self, validator, preservation_rules):
        """Test that excessive content reduction fails validation."""
        original = "This is a long section with lots of content. " * 10
        edited = "Short."

        recommendation = {"id": "rec_003", "type": "missing_info"}

        result = validator.validate_edit(original, edited, recommendation, preservation_rules)

        assert result.is_valid is False
        assert result.content_stability_score < 1.0
        assert any("reduction" in v.violation_type.lower() for v in result.violations)

    def test_expansion_allowed(self, validator, preservation_rules):
        """Test that content expansion is allowed."""
        original = "Short section."
        edited = "Short section with lots of additional helpful information added here. " * 5

        recommendation = {"id": "rec_004", "type": "missing_info"}

        result = validator.validate_edit(original, edited, recommendation, preservation_rules)

        # Expansion should be allowed (warnings OK, but not violations)
        assert result.content_stability_score > 0.7  # Some warning OK
        # Should not have critical violations for expansion
        critical_violations = [v for v in result.violations if v.severity == "critical"]
        assert len(critical_violations) == 0

    def test_code_block_preservation(self, validator):
        """Test that code blocks must be preserved."""
        rules = PreservationRules(
            preserve_code_blocks=True,
            max_content_reduction_percent=10.0
        )

        original = "Example:\n```python\nprint('hello')\n```"
        edited = "Example:\nCode removed."

        recommendation = {"id": "rec_005", "type": "missing_info"}

        result = validator.validate_edit(original, edited, recommendation, rules)

        assert result.is_valid is False
        assert result.structure_preservation_score < 1.0
        assert any("code_block" in v.violation_type for v in result.violations)

    def test_technical_terms_preserved(self, validator, preservation_rules):
        """Test that technical terms are checked."""
        original = "Use NuGet and the namespace for setup."
        edited = "Use the package manager and imports for setup."

        recommendation = {"id": "rec_006", "type": "missing_info"}

        result = validator.validate_edit(original, edited, recommendation, preservation_rules)

        assert result.is_valid is False  # Lost critical technical terms
        assert result.technical_accuracy_score < 1.0


# ==============================================================================
# Pre-Enhancement Checks
# ==============================================================================

class TestPreEnhancementCheck:
    """Tests for validate_before_enhancement method."""

    def test_valid_content_and_recommendations(self, validator, sample_content, preservation_rules):
        """Test pre-checks with valid inputs."""
        recommendations = [
            {"id": "rec_001", "type": "missing_plugin"},
            {"id": "rec_002", "type": "incorrect_plugin"},
        ]

        result = validator.validate_before_enhancement(
            sample_content,
            recommendations,
            preservation_rules
        )

        assert result.can_proceed is True
        assert result.file_readable is True
        assert result.valid_markdown is True
        assert result.recommendations_applicable is True
        assert len(result.issues) == 0

    def test_empty_content_fails(self, validator, preservation_rules):
        """Test that empty content fails pre-checks."""
        result = validator.validate_before_enhancement(
            "",
            [{"id": "rec_001"}],
            preservation_rules
        )

        assert result.can_proceed is False
        assert result.file_readable is False
        assert "empty" in result.issues[0].lower()

    def test_no_recommendations_issue(self, validator, sample_content, preservation_rules):
        """Test that no recommendations is flagged."""
        result = validator.validate_before_enhancement(
            sample_content,
            [],
            preservation_rules
        )

        assert result.can_proceed is False
        assert result.recommendations_applicable is False
        assert any("no recommendations" in issue.lower() for issue in result.issues)

    def test_conflicting_recommendations_detected(self, validator, sample_content, preservation_rules):
        """Test detection of conflicting recommendations."""
        recommendations = [
            {
                "id": "rec_001",
                "type": "missing_info",
                "line_start": 5,
                "line_end": 10
            },
            {
                "id": "rec_002",
                "type": "missing_info",
                "line_start": 8,
                "line_end": 12
            }
        ]

        result = validator.validate_before_enhancement(
            sample_content,
            recommendations,
            preservation_rules
        )

        assert len(result.conflicting_recommendations) > 0
        assert any("conflicting" in warning.lower() for warning in result.warnings)

    def test_incomplete_frontmatter_warning(self, validator, preservation_rules):
        """Test warning for incomplete YAML frontmatter."""
        incomplete_content = "---\ntitle: Test\n\nNo closing delimiter"

        result = validator.validate_before_enhancement(
            incomplete_content,
            [{"id": "rec_001"}],
            preservation_rules
        )

        assert any("frontmatter" in warning.lower() for warning in result.warnings)


# ==============================================================================
# Post-Enhancement Checks
# ==============================================================================

class TestPostEnhancementCheck:
    """Tests for validate_after_enhancement method."""

    def test_safe_enhancement(self, validator, preservation_rules):
        """Test validation of safe enhancement."""
        original = """# Guide

Use Aspose.Words for document processing.

```csharp
var doc = new Document();
```
"""

        enhanced = """# Guide

Use Aspose.Words for advanced document processing with .NET.

```csharp
var doc = new Document();
```

Additional features available.
"""

        result = validator.validate_after_enhancement(
            original,
            enhanced,
            [],
            preservation_rules
        )

        assert result.is_safe is True
        assert result.all_keywords_present is True
        assert result.structure_intact is True
        assert result.code_blocks_intact is True
        assert result.size_within_bounds is True
        assert len([v for v in result.violations if v.severity == "critical"]) == 0

    def test_keyword_loss_detected(self, validator, preservation_rules):
        """Test detection of lost keywords."""
        original = "Use Aspose.Words and Document classes."
        enhanced = "Use the library and classes."

        result = validator.validate_after_enhancement(
            original,
            enhanced,
            [],
            preservation_rules
        )

        assert result.is_safe is False
        assert result.all_keywords_present is False
        assert any(v.violation_type == "keyword_loss" for v in result.violations)

    def test_code_block_loss_detected(self, validator, preservation_rules):
        """Test detection of removed code blocks."""
        original = "Example:\n```python\ncode\n```\nMore text."
        enhanced = "Example: Code removed. More text."

        result = validator.validate_after_enhancement(
            original,
            enhanced,
            [],
            preservation_rules
        )

        assert result.is_safe is False
        assert result.code_blocks_intact is False
        assert any("code_block" in v.violation_type for v in result.violations)

    def test_excessive_reduction_detected(self, validator, preservation_rules):
        """Test detection of excessive content reduction."""
        original = "Long content " * 100
        enhanced = "Short content"

        result = validator.validate_after_enhancement(
            original,
            enhanced,
            [],
            preservation_rules
        )

        assert result.is_safe is False
        assert result.size_within_bounds is False
        assert any("reduction" in v.violation_type for v in result.violations)

    def test_structure_loss_detected(self, validator, preservation_rules):
        """Test detection of lost major structure."""
        original = """# Main Title

## Section 1

Content 1

## Section 2

Content 2

## Section 3

Content 3
"""

        enhanced = """# Main Title

Some content
"""

        result = validator.validate_after_enhancement(
            original,
            enhanced,
            [],
            preservation_rules
        )

        assert result.is_safe is False
        assert result.structure_intact is False
        assert any("structure" in v.violation_type for v in result.violations)

    def test_link_loss_warning(self, validator, preservation_rules):
        """Test warning for significant link loss."""
        original = """
[Link1](url1) [Link2](url2) [Link3](url3) [Link4](url4) [Link5](url5)
"""

        enhanced = "No links here."

        result = validator.validate_after_enhancement(
            original,
            enhanced,
            [],
            preservation_rules
        )

        assert result.links_intact is False
        assert len(result.warnings) > 0

    def test_frontmatter_validation(self, validator, preservation_rules):
        """Test frontmatter validation."""
        original = "---\ntitle: Test\n---\n\nContent"
        enhanced = "---\ntitle: Test\n\nContent"  # Missing closing delimiter

        result = validator.validate_after_enhancement(
            original,
            enhanced,
            [],
            preservation_rules
        )

        assert result.frontmatter_valid is False
        assert any("frontmatter" in v.violation_type for v in result.violations)


# ==============================================================================
# Enhanced Safety Score
# ==============================================================================

class TestEnhancedSafetyScore:
    """Tests for calculate_enhanced_safety_score method."""

    def test_perfect_enhancement_score(self, validator, preservation_rules):
        """Test safety score for perfect enhancement."""
        original = "Use Aspose.Words and Document."
        enhanced = "Use Aspose.Words and Document classes for processing."

        result = validator.calculate_enhanced_safety_score(
            original,
            enhanced,
            preservation_rules,
            []
        )

        assert result.overall_score >= 0.9
        assert result.keyword_preservation >= 0.9
        assert result.structure_preservation >= 0.9
        assert result.is_safe_to_apply() is True

    def test_keyword_loss_reduces_score(self, validator, preservation_rules):
        """Test that keyword loss reduces safety score."""
        original = "Use Aspose.Words and Document."
        enhanced = "Use the library."

        result = validator.calculate_enhanced_safety_score(
            original,
            enhanced,
            preservation_rules,
            []
        )

        assert result.overall_score < 0.8
        assert result.keyword_preservation < 0.8
        assert result.is_safe_to_apply() is False
        assert len(result.violations) > 0

    def test_weighted_scoring(self, validator, preservation_rules):
        """Test that scoring is properly weighted."""
        original = "Use Aspose.Words. " * 50
        enhanced = "Use Aspose.Words."  # Massive reduction but keywords intact

        result = validator.calculate_enhanced_safety_score(
            original,
            enhanced,
            preservation_rules,
            []
        )

        # Keywords are 35% weight, so even with perfect keywords,
        # massive reduction should pull score down
        assert result.keyword_preservation == 1.0
        assert result.content_stability < 0.7
        assert result.overall_score < 0.85  # Pulled down by content instability

    def test_violation_severity_affects_score(self, validator, preservation_rules):
        """Test that violation severity affects scores appropriately."""
        original = "Use Aspose.Words and Document with NuGet."
        enhanced = "Use something else."  # Loses everything

        result = validator.calculate_enhanced_safety_score(
            original,
            enhanced,
            preservation_rules,
            []
        )

        # Should have multiple critical violations
        critical_violations = [v for v in result.violations if v.severity == "critical"]
        assert len(critical_violations) > 0

        # Scores should be significantly reduced
        assert result.keyword_preservation < 0.5
        assert result.technical_accuracy < 0.9
        assert result.overall_score < 0.7

    def test_serialization_to_dict(self, validator, preservation_rules):
        """Test that results can be serialized."""
        original = "Test content with Aspose.Words"
        enhanced = "Test content with Aspose.Words and more"

        result = validator.calculate_enhanced_safety_score(
            original,
            enhanced,
            preservation_rules,
            []
        )

        result_dict = result.to_dict()

        assert "overall_score" in result_dict
        assert "keyword_preservation" in result_dict
        assert "structure_preservation" in result_dict
        assert "violations" in result_dict
        assert "warnings" in result_dict
        assert "is_safe_to_apply" in result_dict


# ==============================================================================
# Integration Tests
# ==============================================================================

class TestValidatorIntegration:
    """Integration tests for complete validation workflows."""

    def test_full_validation_pipeline(self, validator, sample_content, preservation_rules):
        """Test complete validation workflow."""
        recommendations = [
            {"id": "rec_001", "type": "missing_plugin", "severity": "medium"},
        ]

        # Pre-check
        pre_check = validator.validate_before_enhancement(
            sample_content,
            recommendations,
            preservation_rules
        )
        assert pre_check.can_proceed is True

        # Simulate enhancement (minimal change)
        enhanced = sample_content.replace(
            "## Prerequisites",
            "## Prerequisites\n\n- Document Converter plugin"
        )

        # Post-check
        post_check = validator.validate_after_enhancement(
            sample_content,
            enhanced,
            recommendations,
            preservation_rules
        )
        assert post_check.is_safe is True

        # Safety score
        safety_score = validator.calculate_enhanced_safety_score(
            sample_content,
            enhanced,
            preservation_rules,
            []
        )
        assert safety_score.is_safe_to_apply() is True

    def test_validation_catches_destructive_edit(self, validator, sample_content, preservation_rules):
        """Test that validation catches destructive changes."""
        recommendations = []

        # Destructive enhancement (removes most content and keywords)
        enhanced = "# Test\n\nMinimal content."

        # Post-check should fail
        post_check = validator.validate_after_enhancement(
            sample_content,
            enhanced,
            recommendations,
            preservation_rules
        )
        assert post_check.is_safe is False

        # Safety score should be low
        safety_score = validator.calculate_enhanced_safety_score(
            sample_content,
            enhanced,
            preservation_rules,
            []
        )
        assert safety_score.is_safe_to_apply() is False
        assert safety_score.overall_score < 0.6


# ==============================================================================
# Run tests
# ==============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
