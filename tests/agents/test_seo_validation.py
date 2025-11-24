#!/usr/bin/env python3
"""
Tests for SEO heading validation functionality.
"""

import pytest
from agents.content_validator import ContentValidatorAgent


class TestSEOHeadingValidation:
    """Tests for SEO-compliant heading validation."""

    @pytest.fixture
    def validator(self):
        """Create a ContentValidator instance."""
        return ContentValidatorAgent()

    @pytest.mark.asyncio
    async def test_valid_seo_headings(self, validator):
        """Test document with proper SEO heading structure."""
        content = """# Complete Guide to Python Programming

## Introduction to Python
Python is a versatile language.

## Getting Started
### Installation Steps
Install Python from python.org.

## Advanced Topics
### Decorators
Decorators are powerful.
"""
        result = await validator._validate_seo_headings(content)

        assert result.confidence >= 0.9
        assert len([i for i in result.issues if i.level == "error"]) == 0
        assert result.metrics["h1_count"] == 1
        assert result.metrics["seo_compliant"] is True
        assert result.metrics["hierarchy_valid"] is True

    @pytest.mark.asyncio
    async def test_missing_h1(self, validator):
        """Test document missing H1 heading."""
        content = """## Introduction
This document has no H1.

### Details
More information here.
"""
        result = await validator._validate_seo_headings(content)

        assert result.confidence < 1.0
        missing_h1_issues = [i for i in result.issues if i.category == "missing_h1"]
        assert len(missing_h1_issues) == 1
        assert missing_h1_issues[0].level == "error"
        assert result.metrics["h1_count"] == 0
        assert result.metrics["seo_compliant"] is False

    @pytest.mark.asyncio
    async def test_multiple_h1(self, validator):
        """Test document with multiple H1 headings."""
        content = """# First Main Heading

Some content here.

# Second Main Heading

More content.
"""
        result = await validator._validate_seo_headings(content)

        assert result.confidence < 1.0
        multiple_h1_issues = [i for i in result.issues if i.category == "multiple_h1"]
        assert len(multiple_h1_issues) == 1
        assert multiple_h1_issues[0].level == "error"
        assert result.metrics["h1_count"] == 2
        assert result.metrics["seo_compliant"] is False

    @pytest.mark.asyncio
    async def test_h1_too_short(self, validator):
        """Test H1 that is too short for SEO."""
        content = """# Short H1

Some content here.

## Section Two
More details.
"""
        result = await validator._validate_seo_headings(content)

        short_h1_issues = [i for i in result.issues if i.category == "h1_too_short"]
        assert len(short_h1_issues) == 1
        assert short_h1_issues[0].level == "warning"

    @pytest.mark.asyncio
    async def test_h1_too_long(self, validator):
        """Test H1 that is too long for SEO."""
        content = """# This is an extremely long H1 heading that exceeds the recommended character limit for SEO optimization

Some content here.

## Section Two
More details.
"""
        result = await validator._validate_seo_headings(content)

        long_h1_issues = [i for i in result.issues if i.category == "h1_too_long"]
        assert len(long_h1_issues) == 1
        assert long_h1_issues[0].level == "warning"

    @pytest.mark.asyncio
    async def test_hierarchy_skip(self, validator):
        """Test document with heading hierarchy skip."""
        content = """# Main Heading

### Skipped H2 Level

This jumps from H1 to H3.
"""
        result = await validator._validate_seo_headings(content)

        hierarchy_issues = [i for i in result.issues if i.category == "heading_hierarchy_skip"]
        assert len(hierarchy_issues) == 1
        assert hierarchy_issues[0].level == "error"
        assert result.metrics["hierarchy_valid"] is False

    @pytest.mark.asyncio
    async def test_empty_heading(self, validator):
        """Test document with empty heading."""
        content = """# Main Heading

##

Some content with empty H2.
"""
        result = await validator._validate_seo_headings(content)

        empty_issues = [i for i in result.issues if i.category == "empty_heading"]
        assert len(empty_issues) == 1
        assert empty_issues[0].level == "warning"

    @pytest.mark.asyncio
    async def test_h1_not_first(self, validator):
        """Test H1 not appearing first."""
        content = """## Introduction

This starts with H2.

# Main Heading

Now the H1 appears.
"""
        result = await validator._validate_seo_headings(content)

        not_first_issues = [i for i in result.issues if i.category == "h1_not_first"]
        assert len(not_first_issues) == 1
        assert not_first_issues[0].level == "info"

    @pytest.mark.asyncio
    async def test_excessive_heading_depth(self, validator):
        """Test heading depth exceeding recommendation."""
        content = """# Level 1
## Level 2
### Level 3
#### Level 4
##### Level 5
###### Level 6
####### Level 7

This has H7 which exceeds recommended depth.
"""
        result = await validator._validate_seo_headings(content)

        depth_issues = [i for i in result.issues if i.category == "excessive_heading_depth"]
        assert len(depth_issues) == 1
        assert depth_issues[0].level == "info"

    @pytest.mark.asyncio
    async def test_no_headings(self, validator):
        """Test document with no headings."""
        content = """This is a document with no headings at all.

Just plain text content.
"""
        result = await validator._validate_seo_headings(content)

        assert result.confidence == 1.0
        assert len(result.issues) == 0
        assert result.metrics["has_headings"] is False

    @pytest.mark.asyncio
    async def test_complex_heading_structure(self, validator):
        """Test complex document with multiple heading issues."""
        content = """## Introduction

Starts with H2 instead of H1.

# Main Heading That Is Way Too Long For SEO Best Practices And Should Be Shortened

#### Skipped H2 and H3

Empty heading below:

###

## Conclusion
"""
        result = await validator._validate_seo_headings(content)

        # Should have multiple issues
        assert len(result.issues) >= 4
        assert len([i for i in result.issues if i.level == "error"]) >= 1
        assert result.confidence <= 0.8

        # Check specific issues exist
        categories = [i.category for i in result.issues]
        assert "h1_not_first" in categories
        assert "h1_too_long" in categories
        assert "heading_hierarchy_skip" in categories
        assert "empty_heading" in categories

    @pytest.mark.asyncio
    async def test_optimal_h1_length(self, validator):
        """Test H1 with optimal length (30-60 chars)."""
        content = """# Complete Guide to Python Programming

## Introduction
Python is great.
"""
        result = await validator._validate_seo_headings(content)

        h1_length_issues = [
            i for i in result.issues
            if i.category in ["h1_too_short", "h1_too_long"]
        ]
        # Should have no length issues as H1 is 39 chars (in optimal range)
        assert len(h1_length_issues) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
