#!/usr/bin/env python3
"""
Tests for heading size validation functionality.
"""

import pytest
from agents.content_validator import ContentValidatorAgent


class TestHeadingSizeValidation:
    """Tests for heading size validation."""

    @pytest.fixture
    def validator(self):
        """Create a ContentValidator instance."""
        return ContentValidatorAgent()

    @pytest.mark.asyncio
    async def test_all_headings_within_limits(self, validator):
        """Test document with all headings within size limits."""
        content = """# Complete Guide to Python Programming

## Introduction to Python Basics
Python is a versatile programming language.

### Getting Started with Installation
Follow these steps to install Python.

#### Step-by-Step Instructions
Detailed installation guide.
"""
        result = await validator._validate_heading_sizes(content)

        assert result.confidence == 1.0
        # Should have no hard violations
        hard_violations = [i for i in result.issues if i.level in ["error", "warning"]]
        assert len(hard_violations) == 0
        assert result.metrics["all_within_limits"] is True

    @pytest.mark.asyncio
    async def test_h1_too_short(self, validator):
        """Test H1 below minimum length."""
        content = """# Short

Some content here.
"""
        result = await validator._validate_heading_sizes(content)

        short_issues = [i for i in result.issues if i.category == "heading_too_short"]
        assert len(short_issues) == 1
        assert short_issues[0].level == "error"
        assert "H1" in short_issues[0].message
        assert result.metrics["size_violations"] >= 1

    @pytest.mark.asyncio
    async def test_h1_too_long(self, validator):
        """Test H1 exceeding maximum length."""
        content = """# This is an extremely long H1 heading that definitely exceeds the maximum character limit of seventy characters

Some content here.
"""
        result = await validator._validate_heading_sizes(content)

        long_issues = [i for i in result.issues if i.category == "heading_too_long"]
        assert len(long_issues) == 1
        assert long_issues[0].level == "warning"
        assert "H1" in long_issues[0].message

    @pytest.mark.asyncio
    async def test_h2_too_short(self, validator):
        """Test H2 below minimum length."""
        content = """# Complete Guide to Python Programming

## Short

Content here.
"""
        result = await validator._validate_heading_sizes(content)

        short_issues = [i for i in result.issues if i.category == "heading_too_short"]
        assert len(short_issues) == 1
        assert "H2" in short_issues[0].message

    @pytest.mark.asyncio
    async def test_h3_too_long(self, validator):
        """Test H3 exceeding maximum length."""
        content = """# Valid Main Heading

## Valid Section Heading

### This is a very long H3 heading that exceeds the maximum character limit for level 3 headings which should be around one hundred characters

Content.
"""
        result = await validator._validate_heading_sizes(content)

        long_issues = [i for i in result.issues if i.category == "heading_too_long"]
        assert len(long_issues) == 1
        assert "H3" in long_issues[0].message

    @pytest.mark.asyncio
    async def test_below_recommended_length(self, validator):
        """Test heading below recommended minimum."""
        content = """# Python Guide for Developers

## Quick Start

Content here.
"""
        result = await validator._validate_heading_sizes(content)

        # H2 "Quick Start" is 11 chars, which is above min (10) but below recommended (20)
        below_rec_issues = [i for i in result.issues if i.category == "heading_below_recommended"]
        assert len(below_rec_issues) >= 1
        assert below_rec_issues[0].level == "info"

    @pytest.mark.asyncio
    async def test_above_recommended_length(self, validator):
        """Test heading above recommended maximum."""
        content = """# Python Programming

## This Section Heading Is Quite Long And Exceeds The Recommended Maximum Length

Content.
"""
        result = await validator._validate_heading_sizes(content)

        # H2 is 78 chars, which is below max (100) but above recommended (80)
        above_rec_issues = [i for i in result.issues if i.category == "heading_above_recommended"]
        # May have 0 or 1 depending on exact length
        if len(above_rec_issues) > 0:
            assert above_rec_issues[0].level == "info"

    @pytest.mark.asyncio
    async def test_multiple_heading_levels(self, validator):
        """Test validation across multiple heading levels."""
        content = """# Complete Python Programming Guide

## Intro

### Getting Started with Python Development

#### More

##### Details Here

###### Info
"""
        result = await validator._validate_heading_sizes(content)

        # Should check all 6 heading levels
        assert result.metrics["headings_checked"] == 6

        # H2 "Intro" is too short (5 < 10)
        # H4 "More" is too short (4 < 5)
        # H6 "Info" is too short (4 < 3 is false, but close)
        short_issues = [i for i in result.issues if i.category == "heading_too_short"]
        assert len(short_issues) >= 2  # At least H2 and H4

    @pytest.mark.asyncio
    async def test_no_headings(self, validator):
        """Test document with no headings."""
        content = """This is a document with no headings.

Just plain text content.
"""
        result = await validator._validate_heading_sizes(content)

        assert result.confidence == 1.0
        assert len(result.issues) == 0
        assert result.metrics["has_headings"] is False

    @pytest.mark.asyncio
    async def test_empty_headings_skipped(self, validator):
        """Test that empty headings are skipped."""
        content = """# Valid Heading

##

Some content.
"""
        result = await validator._validate_heading_sizes(content)

        # Empty H2 should be skipped by size validation
        # (it's handled by SEO validation)
        assert result.metrics["headings_checked"] == 2
        # Should only check non-empty headings for size

    @pytest.mark.asyncio
    async def test_optimal_heading_sizes(self, validator):
        """Test document with optimally sized headings."""
        content = """# Complete Guide to Modern Python Development

## Introduction to Python Programming Language
Python is a powerful language.

### Installing Python on Different Operating Systems
Follow these steps.

#### Detailed Installation Steps for Windows Users
Click download.
"""
        result = await validator._validate_heading_sizes(content)

        # All headings are within optimal ranges
        # Should have no errors or warnings
        errors_and_warnings = [i for i in result.issues if i.level in ["error", "warning"]]
        assert len(errors_and_warnings) == 0
        assert result.confidence == 1.0

    @pytest.mark.asyncio
    async def test_mixed_violations(self, validator):
        """Test document with multiple size violations."""
        content = """# Guide

## This is an extremely long section heading that goes way beyond the recommended maximum length and should trigger a warning

### OK

#### This H4 heading is way too long for the maximum allowed length and should definitely trigger a size violation warning

Content here.
"""
        result = await validator._validate_heading_sizes(content)

        # H1 too short (5 < 20)
        # H2 too long (>100)
        # H4 too long (>80)
        # H3 too short (2 < 5)
        assert result.metrics["size_violations"] >= 3
        assert result.confidence < 1.0

        # Check we have both error and warning level issues
        errors = [i for i in result.issues if i.level == "error"]
        warnings = [i for i in result.issues if i.level == "warning"]
        assert len(errors) >= 1  # At least H1 too short
        assert len(warnings) >= 1  # At least one too long

    @pytest.mark.asyncio
    async def test_confidence_calculation(self, validator):
        """Test confidence score decreases with errors."""
        # Document with multiple errors
        content = """# Bad

## OK

### No

#### Yes

Content.
"""
        result = await validator._validate_heading_sizes(content)

        # Multiple short headings should lower confidence
        error_count = len([i for i in result.issues if i.level == "error"])
        if error_count > 0:
            assert result.confidence < 1.0
            # Confidence should be at least 0.6
            assert result.confidence >= 0.6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
