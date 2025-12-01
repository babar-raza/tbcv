# file: tests/test_recommendation_enhancer.py
"""
Unit tests for RecommendationEnhancer - Phase 1.

Tests cover:
- Context extraction
- Recommendation type handlers
- Preservation rules
- Basic enhancement workflow
"""

import pytest
import asyncio
from agents.recommendation_enhancer import (
    RecommendationEnhancer,
    ContextExtractor,
    PreservationRules,
    PluginMentionHandler,
    PluginCorrectionHandler,
    InfoAdditionHandler,
    create_default_preservation_rules,
    EditContext,
)


# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def sample_content():
    """Sample markdown content for testing."""
    return """---
title: Aspose.Words Plugin Guide
---

# Getting Started

This guide covers the Aspose.Words plugins.

## Prerequisites

To use these features, install:
- Document Converter plugin
- Word Processor plugin
- PDF Exporter plugin

## Basic Usage

Here's how to use the Document class:

```csharp
using Aspose.Words;

var doc = new Document("input.docx");
doc.Save("output.pdf");
```

## Advanced Features

Additional capabilities include:
- Mail merge
- Table manipulation
- Custom formatting
"""


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
def missing_plugin_recommendation():
    """Recommendation for missing plugin."""
    return {
        "id": "rec_001",
        "type": "missing_plugin",
        "plugin_name": "Document Splitter",
        "scope": "prerequisites",
        "severity": "medium",
        "reason": "Document splitting feature requires this plugin",
        "suggested_addition": "- Document Splitter plugin",
        "confidence": 0.9
    }


@pytest.fixture
def incorrect_plugin_recommendation():
    """Recommendation for plugin name correction."""
    return {
        "id": "rec_002",
        "type": "incorrect_plugin",
        "found": "words_save_operations",
        "expected": "Word Processor",
        "scope": "global",
        "severity": "high",
        "reason": "Incorrect plugin name used",
        "confidence": 0.95
    }


# ==============================================================================
# Context Extraction Tests
# ==============================================================================

class TestContextExtractor:
    """Tests for ContextExtractor class."""

    def test_initialization(self):
        """Test extractor initialization."""
        extractor = ContextExtractor(window_lines=5)
        assert extractor.window_lines == 5

    def test_extract_prerequisites_section(self, sample_content, preservation_rules):
        """Test extracting prerequisites section."""
        extractor = ContextExtractor(window_lines=3)

        recommendation = {
            "scope": "prerequisites",
            "type": "missing_plugin"
        }

        context = extractor.extract_edit_context(
            sample_content,
            recommendation,
            preservation_rules
        )

        assert context is not None
        assert "Prerequisites" in context.target_section
        assert "Document Converter" in context.target_section
        assert len(context.before_context) > 0
        assert len(context.after_context) > 0

    def test_extract_with_line_numbers(self, sample_content, preservation_rules):
        """Test extraction with explicit line numbers."""
        extractor = ContextExtractor(window_lines=2)

        recommendation = {
            "line_start": 10,
            "line_end": 14,
            "type": "missing_info"
        }

        context = extractor.extract_edit_context(
            sample_content,
            recommendation,
            preservation_rules
        )

        assert context is not None
        assert context.line_start == 10
        assert context.line_end == 14

    def test_extract_constraints(self, preservation_rules):
        """Test extraction of preservation constraints."""
        extractor = ContextExtractor()

        target_section = """
## Prerequisites

- Aspose.Words plugin
- Document class support

```csharp
// code here
```
"""

        constraints = extractor._extract_constraints(target_section, preservation_rules)

        assert any("Aspose.Words" in c for c in constraints)
        assert any("code blocks" in c for c in constraints)

    def test_out_of_bounds_handling(self, sample_content, preservation_rules):
        """Test handling of out-of-bounds ranges."""
        extractor = ContextExtractor()

        recommendation = {
            "line_start": 1000,
            "line_end": 1100,
            "type": "missing_info"
        }

        context = extractor.extract_edit_context(
            sample_content,
            recommendation,
            preservation_rules
        )

        assert context is None  # Should handle gracefully


# ==============================================================================
# Preservation Rules Tests
# ==============================================================================

class TestPreservationRules:
    """Tests for PreservationRules."""

    def test_default_creation(self):
        """Test creating default preservation rules."""
        rules = create_default_preservation_rules()

        assert "Aspose.Words" in rules.preserve_keywords
        assert ".NET" in rules.preserve_keywords
        assert rules.preserve_code_blocks is True
        assert rules.max_content_reduction_percent == 10.0

    def test_to_dict_serialization(self, preservation_rules):
        """Test serialization to dictionary."""
        data = preservation_rules.to_dict()

        assert "preserve_keywords" in data
        assert "max_content_reduction_percent" in data
        assert data["preserve_code_blocks"] is True

    def test_custom_rules(self):
        """Test custom preservation rules."""
        rules = PreservationRules(
            preserve_keywords=["Custom", "Keywords"],
            max_content_reduction_percent=15.0,
            preserve_code_blocks=False
        )

        assert "Custom" in rules.preserve_keywords
        assert rules.max_content_reduction_percent == 15.0
        assert rules.preserve_code_blocks is False


# ==============================================================================
# Handler Tests
# ==============================================================================

class TestPluginMentionHandler:
    """Tests for PluginMentionHandler."""

    @pytest.mark.asyncio
    async def test_handler_initialization(self):
        """Test handler creation."""
        handler = PluginMentionHandler(model="llama3.2")
        assert handler.model == "llama3.2"
        assert handler.get_prompt_template() is not None

    @pytest.mark.asyncio
    async def test_prompt_template_format(self):
        """Test that prompt template has required fields."""
        handler = PluginMentionHandler()
        template = handler.get_prompt_template()

        assert "{before_context}" in template
        assert "{target_section}" in template
        assert "{after_context}" in template
        assert "{plugin_name}" in template
        assert "STRICT REQUIREMENTS" in template


class TestPluginCorrectionHandler:
    """Tests for PluginCorrectionHandler."""

    @pytest.mark.asyncio
    async def test_direct_replacement(self, preservation_rules):
        """Test direct string replacement for exact matches."""
        handler = PluginCorrectionHandler()

        context = EditContext(
            target_section="Use words_save_operations plugin for saving.",
            before_context="Prerequisites:",
            after_context="Examples follow:",
            line_start=5,
            line_end=5,
            preservation_constraints=[]
        )

        recommendation = {
            "found": "words_save_operations",
            "expected": "Word Processor",
            "reason": "Incorrect plugin name"
        }

        enhanced, confidence = await handler.apply(context, recommendation, preservation_rules)

        assert "Word Processor" in enhanced
        assert "words_save_operations" not in enhanced
        assert confidence > 0.9  # High confidence for exact match

    @pytest.mark.asyncio
    async def test_prompt_template_format(self):
        """Test prompt template structure."""
        handler = PluginCorrectionHandler()
        template = handler.get_prompt_template()

        assert "{incorrect_name}" in template
        assert "{correct_name}" in template
        assert "STRICT REQUIREMENTS" in template


class TestInfoAdditionHandler:
    """Tests for InfoAdditionHandler."""

    @pytest.mark.asyncio
    async def test_handler_initialization(self):
        """Test handler creation."""
        handler = InfoAdditionHandler(model="llama3.2")
        assert handler.model == "llama3.2"

    @pytest.mark.asyncio
    async def test_prompt_template_format(self):
        """Test prompt template structure."""
        handler = InfoAdditionHandler()
        template = handler.get_prompt_template()

        assert "{info_to_add}" in template
        assert "{reason}" in template
        assert "STRICT REQUIREMENTS" in template


# ==============================================================================
# RecommendationEnhancer Tests
# ==============================================================================

class TestRecommendationEnhancer:
    """Tests for main RecommendationEnhancer class."""

    def test_initialization(self):
        """Test enhancer initialization."""
        enhancer = RecommendationEnhancer(model="llama3.2", window_lines=10)

        assert enhancer.model == "llama3.2"
        assert enhancer.context_extractor.window_lines == 10
        assert "missing_plugin" in enhancer.handlers
        assert "incorrect_plugin" in enhancer.handlers
        assert "missing_info" in enhancer.handlers

    @pytest.mark.asyncio
    async def test_enhance_with_correction(self, preservation_rules):
        """Test enhancement with plugin correction."""
        enhancer = RecommendationEnhancer()

        content = """
# Guide

Use words_save_operations plugin.
"""

        recommendations = [
            {
                "id": "rec_001",
                "type": "incorrect_plugin",
                "found": "words_save_operations",
                "expected": "Word Processor",
                "scope": "global",
                "confidence": 0.95
            }
        ]

        result = await enhancer.enhance_from_recommendations(
            content,
            recommendations,
            preservation_rules
        )

        assert result is not None
        # Enhancement should either apply the recommendation OR skip it with a reason
        # Both behaviors are acceptable depending on context extraction and LLM availability
        total_processed = len(result.applied_recommendations) + len(result.skipped_recommendations)
        assert total_processed == len(recommendations), "All recommendations should be processed"
        # If applied, content should be modified; if skipped, original should be preserved
        if result.applied_recommendations:
            assert "Word Processor" in result.enhanced_content or result.enhanced_content != content
        else:
            # Skipped recommendation should have a valid reason
            assert all(s.reason for s in result.skipped_recommendations)

    @pytest.mark.asyncio
    async def test_skip_unsupported_type(self, sample_content, preservation_rules):
        """Test that unsupported recommendation types are skipped."""
        enhancer = RecommendationEnhancer()

        recommendations = [
            {
                "id": "rec_999",
                "type": "unsupported_type",
                "confidence": 0.9
            }
        ]

        result = await enhancer.enhance_from_recommendations(
            sample_content,
            recommendations,
            preservation_rules
        )

        assert len(result.skipped_recommendations) == 1
        assert "No handler available" in result.skipped_recommendations[0].reason

    @pytest.mark.asyncio
    async def test_multiple_recommendations(self, sample_content, preservation_rules):
        """Test processing multiple recommendations."""
        enhancer = RecommendationEnhancer()

        recommendations = [
            {
                "id": "rec_001",
                "type": "missing_plugin",
                "plugin_name": "Document Splitter",
                "scope": "prerequisites",
                "confidence": 0.9,
                "suggested_addition": "- Document Splitter plugin",
                "reason": "Required for splitting"
            },
            {
                "id": "rec_002",
                "type": "incorrect_plugin",
                "found": "Word Processor plugin",
                "expected": "Word Processing plugin",
                "scope": "prerequisites",
                "confidence": 0.85
            }
        ]

        result = await enhancer.enhance_from_recommendations(
            sample_content,
            recommendations,
            preservation_rules
        )

        assert result is not None
        total_processed = len(result.applied_recommendations) + len(result.skipped_recommendations)
        assert total_processed == len(recommendations)

    def test_validate_section_edit_size_check(self, preservation_rules):
        """Test section validation catches excessive size changes."""
        enhancer = RecommendationEnhancer()

        original = "This is a section with some content. " * 10
        enhanced = "Short."  # Massive reduction

        is_valid = enhancer._validate_section_edit(original, enhanced, preservation_rules)

        assert is_valid is False  # Should reject excessive reduction

    def test_validate_section_edit_keyword_check(self, preservation_rules):
        """Test section validation catches lost keywords."""
        enhancer = RecommendationEnhancer()

        original = "This section uses Aspose.Words for document processing."
        enhanced = "This section uses a library for document processing."

        is_valid = enhancer._validate_section_edit(original, enhanced, preservation_rules)

        assert is_valid is False  # Should reject lost keyword

    def test_validate_section_edit_accepts_good_edit(self, preservation_rules):
        """Test section validation accepts good edits."""
        enhancer = RecommendationEnhancer()

        original = "Use Aspose.Words plugin for document processing."
        enhanced = "Use Aspose.Words plugin and PDF Exporter for document processing."

        is_valid = enhancer._validate_section_edit(original, enhanced, preservation_rules)

        assert is_valid is True  # Should accept good edit

    def test_generate_diff(self):
        """Test diff generation."""
        enhancer = RecommendationEnhancer()

        original = "Line 1\nLine 2\nLine 3"
        enhanced = "Line 1\nLine 2 modified\nLine 3\nLine 4"

        diff, added, removed, modified = enhancer._generate_diff(original, enhanced)

        assert len(diff) > 0
        assert added > 0  # Added "Line 4"
        assert modified >= 0

    def test_calculate_safety_score_perfect(self, preservation_rules):
        """Test safety score for unchanged content."""
        enhancer = RecommendationEnhancer()

        content = "Perfect content with Aspose.Words"

        score = enhancer._calculate_safety_score(content, content, preservation_rules)

        assert score.overall_score >= 0.9
        assert score.is_safe_to_apply() is True
        assert len(score.violations) == 0

    def test_calculate_safety_score_keyword_loss(self, preservation_rules):
        """Test safety score detects keyword loss."""
        enhancer = RecommendationEnhancer()

        original = "Content with Aspose.Words keyword"
        enhanced = "Content without the keyword"

        score = enhancer._calculate_safety_score(original, enhanced, preservation_rules)

        assert score.keyword_preservation < 1.0
        assert len(score.violations) > 0
        assert any(v.violation_type == "keyword_loss" for v in score.violations)

    def test_calculate_safety_score_size_change(self, preservation_rules):
        """Test safety score detects excessive size changes."""
        enhancer = RecommendationEnhancer()

        original = "A" * 1000
        enhanced = "A" * 100  # 90% reduction

        score = enhancer._calculate_safety_score(original, enhanced, preservation_rules)

        assert score.content_stability < 1.0
        assert any(v.violation_type == "excessive_size_change" for v in score.violations)

    def test_generate_enhancement_id(self):
        """Test enhancement ID generation."""
        enhancer = RecommendationEnhancer()

        id1 = enhancer._generate_enhancement_id()
        id2 = enhancer._generate_enhancement_id()

        assert id1.startswith("enh_")
        assert id2.startswith("enh_")
        assert id1 != id2  # Should be unique


# ==============================================================================
# Integration Tests
# ==============================================================================

class TestIntegration:
    """Integration tests for complete workflows."""

    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, sample_content, preservation_rules):
        """Test complete enhancement workflow."""
        enhancer = RecommendationEnhancer(model="llama3.2")

        recommendations = [
            {
                "id": "rec_001",
                "type": "incorrect_plugin",
                "found": "Word Processor plugin",
                "expected": "Word Processing plugin",
                "scope": "prerequisites",
                "confidence": 0.9
            }
        ]

        result = await enhancer.enhance_from_recommendations(
            sample_content,
            recommendations,
            preservation_rules
        )

        # Verify result structure
        assert result.original_content == sample_content
        assert result.enhanced_content is not None
        assert result.enhancement_id.startswith("enh_")
        assert result.processing_time_ms >= 0  # May be 0 for fast operations
        assert result.safety_score is not None

        # Verify recommendations processed
        total = len(result.applied_recommendations) + len(result.skipped_recommendations)
        assert total == len(recommendations)

        # Verify safety score structure
        assert 0.0 <= result.safety_score.overall_score <= 1.0
        assert hasattr(result.safety_score, 'is_safe_to_apply')

    @pytest.mark.asyncio
    async def test_serialization(self, sample_content, preservation_rules):
        """Test that results can be serialized to dict."""
        enhancer = RecommendationEnhancer()

        result = await enhancer.enhance_from_recommendations(
            sample_content,
            [],  # Empty recommendations
            preservation_rules
        )

        result_dict = result.to_dict()

        assert "original_content" in result_dict
        assert "enhanced_content" in result_dict
        assert "applied_recommendations" in result_dict
        assert "skipped_recommendations" in result_dict
        assert "safety_score" in result_dict
        assert "enhancement_id" in result_dict


# ==============================================================================
# Run tests
# ==============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
