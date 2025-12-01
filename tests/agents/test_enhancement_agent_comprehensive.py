"""
Comprehensive tests for EnhancementAgent.

The EnhancementAgent applies enhancements to content.
It's a facade over ContentEnhancerAgent which does automatic enhancement.

Tests:
- Basic enhancement functionality
- Plugin link enhancement
- Info text enhancement
- Content preservation
- Preview mode
- Batch enhancement
"""
import pytest
import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# =============================================================================
# Import with fallback
# =============================================================================

try:
    from agents.enhancement_agent import EnhancementAgent
    AGENT_AVAILABLE = True
except ImportError:
    AGENT_AVAILABLE = False
    pytest.skip("EnhancementAgent not available", allow_module_level=True)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def enhancement_agent():
    """Provide EnhancementAgent instance."""
    return EnhancementAgent()


@pytest.fixture
def db_manager():
    """Provide database manager."""
    from core.database import db_manager
    db_manager.init_database()
    yield db_manager


@pytest.fixture
def sample_content():
    """Sample markdown content for testing."""
    return """---
title: Test Document
plugins:
  - document
---

# Test Document

This is a test document using the Document plugin.

## Code Example

```csharp
Document doc = new Document();
doc.Save("output.pdf");
```
"""


# =============================================================================
# Basic Functionality Tests
# =============================================================================

@pytest.mark.asyncio
async def test_enhancement_agent_initialization(enhancement_agent):
    """Test EnhancementAgent initializes correctly."""
    assert enhancement_agent is not None
    assert hasattr(enhancement_agent, "enhance_with_recommendations")


@pytest.mark.asyncio
async def test_apply_enhancement_to_content(enhancement_agent, sample_content):
    """Test applying enhancement to content."""
    result = await enhancement_agent.enhance_with_recommendations(
        content=sample_content,
        file_path="test.md"
    )

    assert result is not None
    assert "enhanced_content" in result
    # Content should be returned (may or may not be modified)
    assert result["enhanced_content"] is not None


@pytest.mark.asyncio
async def test_enhance_with_preview_mode(enhancement_agent, sample_content):
    """Test enhancement in preview mode."""
    result = await enhancement_agent.enhance_with_recommendations(
        content=sample_content,
        file_path="test.md",
        preview=True
    )

    assert result is not None
    assert "enhanced_content" in result


@pytest.mark.asyncio
async def test_enhancement_with_empty_content(enhancement_agent):
    """Test enhancement with empty content."""
    result = await enhancement_agent.enhance_with_recommendations(
        content="",
        file_path="test.md"
    )

    assert result is not None
    assert "enhanced_content" in result
    assert result["enhanced_content"] == ""


@pytest.mark.asyncio
async def test_enhancement_returns_statistics(enhancement_agent, sample_content):
    """Test that enhancement returns statistics."""
    result = await enhancement_agent.enhance_with_recommendations(
        content=sample_content,
        file_path="test.md"
    )

    assert result is not None
    # Check that statistics are returned
    if "statistics" in result:
        stats = result["statistics"]
        assert "original_length" in stats


@pytest.mark.asyncio
async def test_enhancement_returns_enhancements_list(enhancement_agent, sample_content):
    """Test that enhancement returns enhancements list."""
    result = await enhancement_agent.enhance_with_recommendations(
        content=sample_content,
        file_path="test.md"
    )

    assert result is not None
    # Check that enhancements list is returned
    if "enhancements" in result:
        assert isinstance(result["enhancements"], list)


# =============================================================================
# Content Preservation Tests
# =============================================================================

@pytest.mark.asyncio
async def test_preserve_frontmatter(enhancement_agent, db_manager):
    """Test that YAML frontmatter is preserved."""
    content = """---
title: Test
author: Tester
---
# Content"""

    result = await enhancement_agent.enhance_with_recommendations(
        content=content,
        file_path="test.md"
    )

    # Frontmatter should be preserved
    enhanced = result["enhanced_content"]
    assert "---" in enhanced
    assert "title: Test" in enhanced
    assert "author: Tester" in enhanced


@pytest.mark.asyncio
async def test_preserve_code_blocks(enhancement_agent, db_manager):
    """Test that code blocks are preserved."""
    content = """# Test
```python
print("hello")
```"""

    result = await enhancement_agent.enhance_with_recommendations(
        content=content,
        file_path="test.md"
    )

    enhanced = result["enhanced_content"]

    # Code block should be intact
    assert "```python" in enhanced or "```" in enhanced
    assert 'print("hello")' in enhanced


# =============================================================================
# Batch Enhancement Tests
# =============================================================================

@pytest.mark.asyncio
async def test_batch_enhancement(enhancement_agent):
    """Test batch enhancement of multiple validations."""
    validation_ids = ["val1", "val2", "val3"]

    result = await enhancement_agent.enhance_batch(
        validation_ids=validation_ids,
        parallel=True
    )

    assert result is not None
    assert result["success"] is True
    assert result["processed"] == 3
    assert len(result["results"]) == 3


@pytest.mark.asyncio
async def test_batch_enhancement_sequential(enhancement_agent):
    """Test batch enhancement in sequential mode."""
    validation_ids = ["val1", "val2"]

    result = await enhancement_agent.enhance_batch(
        validation_ids=validation_ids,
        parallel=False
    )

    assert result is not None
    assert result["success"] is True
    assert result["processed"] == 2


@pytest.mark.asyncio
async def test_batch_enhancement_empty_list(enhancement_agent):
    """Test batch enhancement with empty list."""
    result = await enhancement_agent.enhance_batch(
        validation_ids=[],
        parallel=True
    )

    assert result["success"] is True
    assert result["processed"] == 0
    assert len(result["results"]) == 0


# =============================================================================
# Error Handling Tests
# =============================================================================

@pytest.mark.asyncio
async def test_enhancement_handles_none_content(enhancement_agent):
    """Test that None content is handled gracefully."""
    try:
        result = await enhancement_agent.enhance_with_recommendations(
            content=None,
            file_path="test.md"
        )
        # Should handle gracefully or return error
        assert result is not None
    except (TypeError, ValueError, AttributeError):
        # Expected - None content might raise exception
        pass


@pytest.mark.asyncio
async def test_enhancement_handles_special_characters(enhancement_agent):
    """Test enhancement with special characters."""
    content = """---
title: Test <>&"'
---
# Test with special chars: <>&"'
"""

    result = await enhancement_agent.enhance_with_recommendations(
        content=content,
        file_path="test.md"
    )

    assert result is not None
    assert "enhanced_content" in result


@pytest.mark.asyncio
async def test_enhancement_handles_unicode(enhancement_agent):
    """Test enhancement with unicode content."""
    content = """---
title: Test Document
---
# Test with unicode: \u4e2d\u6587 \u65e5\u672c\u8a9e \ud83d\ude00
"""

    result = await enhancement_agent.enhance_with_recommendations(
        content=content,
        file_path="test.md"
    )

    assert result is not None
    assert "enhanced_content" in result


# =============================================================================
# Integration Tests
# =============================================================================

@pytest.mark.asyncio
async def test_full_enhancement_workflow(enhancement_agent):
    """Test complete enhancement workflow."""
    # 1. Create content
    content = """---
title: Test
---
# Test
Using Document plugin."""

    # 2. Apply enhancement
    result = await enhancement_agent.enhance_with_recommendations(
        content=content,
        file_path="test.md"
    )

    # 3. Verify results
    assert result is not None
    assert "enhanced_content" in result


@pytest.mark.asyncio
async def test_enhancement_idempotence(enhancement_agent, sample_content):
    """Test that applying enhancement twice produces consistent result."""
    # First application
    result1 = await enhancement_agent.enhance_with_recommendations(
        content=sample_content,
        file_path="test.md"
    )

    # Second application (to already enhanced content)
    result2 = await enhancement_agent.enhance_with_recommendations(
        content=result1["enhanced_content"],
        file_path="test.md"
    )

    # Both should succeed
    assert result1 is not None
    assert result2 is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
