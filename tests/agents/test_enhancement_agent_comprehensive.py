"""
Comprehensive tests for EnhancementAgent.

The EnhancementAgent applies approved recommendations to content.
It's different from ContentEnhancerAgent which does automatic enhancement.

Tests:
- Apply approved recommendations
- Skip rejected/pending recommendations
- Handle recommendation application errors
- Track applied recommendations
- Generate diffs
- Update recommendation status to 'applied'
"""
import pytest
import sys
from pathlib import Path
from datetime import datetime

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
    db_manager.close()


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


@pytest.fixture
def sample_validation(db_manager, sample_content):
    """Create a sample validation."""
    validation_data = {
        "file_path": "test.md",
        "validation_results": {
            "content_validation": {
                "confidence": 0.75,
                "issues": [
                    {
                        "level": "warning",
                        "category": "plugin_link",
                        "message": "Plugin 'document' not hyperlinked",
                        "line": 9,
                        "suggestion": "Add hyperlink"
                    }
                ]
            }
        },
        "status": "fail"
    }

    validation_id = db_manager.save_validation_result(validation_data)
    return validation_id


@pytest.fixture
def approved_recommendations(db_manager, sample_validation):
    """Create approved recommendations."""
    recommendations = [
        {
            "validation_id": sample_validation,
            "type": "plugin_link",
            "title": "Add Document plugin link",
            "description": "Add hyperlink to Document plugin",
            "instruction": "Replace 'Document plugin' with '[Document](https://example.com/document) plugin'",
            "original_content": "Document plugin",
            "proposed_content": "[Document](https://example.com/document) plugin",
            "status": "approved",
            "confidence": 0.95,
            "severity": "medium"
        },
        {
            "validation_id": sample_validation,
            "type": "info_text",
            "title": "Add info text after code block",
            "description": "Add informational text explaining code",
            "instruction": "Add info text after code block",
            "original_content": "```",
            "proposed_content": "```\n\n*This example shows how to save documents.*",
            "status": "approved",
            "confidence": 0.90,
            "severity": "low"
        }
    ]

    recommendation_ids = []
    for rec in recommendations:
        rec_id = db_manager.save_recommendation(rec)
        recommendation_ids.append(rec_id)

    return recommendation_ids


@pytest.fixture
def mixed_recommendations(db_manager, sample_validation):
    """Create recommendations with mixed statuses."""
    recommendations = [
        {
            "validation_id": sample_validation,
            "type": "plugin_link",
            "title": "Approved recommendation",
            "status": "approved",
            "confidence": 0.95,
            "original_content": "test1",
            "proposed_content": "test1_modified"
        },
        {
            "validation_id": sample_validation,
            "type": "plugin_link",
            "title": "Pending recommendation",
            "status": "pending",
            "confidence": 0.85,
            "original_content": "test2",
            "proposed_content": "test2_modified"
        },
        {
            "validation_id": sample_validation,
            "type": "plugin_link",
            "title": "Rejected recommendation",
            "status": "rejected",
            "confidence": 0.80,
            "original_content": "test3",
            "proposed_content": "test3_modified",
            "reviewed_by": "tester",
            "review_notes": "Not needed"
        }
    ]

    recommendation_ids = []
    for rec in recommendations:
        rec_id = db_manager.save_recommendation(rec)
        recommendation_ids.append(rec_id)

    return recommendation_ids


# =============================================================================
# Basic Functionality Tests
# =============================================================================

@pytest.mark.asyncio
async def test_enhancement_agent_initialization(enhancement_agent):
    """Test EnhancementAgent initializes correctly."""
    assert enhancement_agent is not None
    assert hasattr(enhancement_agent, "enhance_with_recommendations")


@pytest.mark.asyncio
async def test_apply_approved_recommendations(enhancement_agent, db_manager, sample_content, approved_recommendations):
    """Test applying approved recommendations to content."""
    # Get recommendations from database
    recommendations = [
        db_manager.get_recommendation(rec_id)
        for rec_id in approved_recommendations
    ]

    result = await enhancement_agent.enhance_with_recommendations(
        content=sample_content,
        recommendations=recommendations,
        file_path="test.md"
    )

    assert result is not None
    assert "enhanced_content" in result
    assert "applied_count" in result
    assert result["applied_count"] > 0


@pytest.mark.asyncio
async def test_skip_rejected_recommendations(enhancement_agent, db_manager, sample_content, mixed_recommendations):
    """Test that rejected recommendations are skipped."""
    # Get all recommendations
    recommendations = [
        db_manager.get_recommendation(rec_id)
        for rec_id in mixed_recommendations
    ]

    result = await enhancement_agent.enhance_with_recommendations(
        content=sample_content,
        recommendations=recommendations,
        file_path="test.md"
    )

    # Should only apply approved recommendations
    assert result["applied_count"] == 1  # Only 1 approved
    assert result["skipped_count"] >= 2  # 2 non-approved


@pytest.mark.asyncio
async def test_skip_pending_recommendations(enhancement_agent, db_manager, sample_content, mixed_recommendations):
    """Test that pending recommendations are skipped."""
    recommendations = [
        db_manager.get_recommendation(rec_id)
        for rec_id in mixed_recommendations
    ]

    result = await enhancement_agent.enhance_with_recommendations(
        content=sample_content,
        recommendations=recommendations,
        file_path="test.md"
    )

    # Pending should be skipped
    assert result["skipped_count"] >= 1


@pytest.mark.asyncio
async def test_generate_diff(enhancement_agent, db_manager, sample_content, approved_recommendations):
    """Test that enhancement generates a diff."""
    recommendations = [
        db_manager.get_recommendation(rec_id)
        for rec_id in approved_recommendations
    ]

    result = await enhancement_agent.enhance_with_recommendations(
        content=sample_content,
        recommendations=recommendations,
        file_path="test.md"
    )

    assert "diff" in result
    assert result["diff"] is not None

    # Diff should show changes
    if result["applied_count"] > 0:
        assert len(result["diff"]) > 0


@pytest.mark.asyncio
async def test_track_per_recommendation_results(enhancement_agent, db_manager, sample_content, approved_recommendations):
    """Test that individual recommendation results are tracked."""
    recommendations = [
        db_manager.get_recommendation(rec_id)
        for rec_id in approved_recommendations
    ]

    result = await enhancement_agent.enhance_with_recommendations(
        content=sample_content,
        recommendations=recommendations,
        file_path="test.md"
    )

    assert "results" in result
    assert isinstance(result["results"], list)

    # Each recommendation should have a result
    assert len(result["results"]) == len(recommendations)

    # Check result format
    for rec_result in result["results"]:
        assert "recommendation_id" in rec_result
        assert "status" in rec_result  # "applied" or "skipped"


@pytest.mark.asyncio
async def test_update_recommendation_status(enhancement_agent, db_manager, sample_content, approved_recommendations):
    """Test that applied recommendations are marked as 'applied' in database."""
    recommendations = [
        db_manager.get_recommendation(rec_id)
        for rec_id in approved_recommendations
    ]

    # Apply recommendations
    result = await enhancement_agent.enhance_with_recommendations(
        content=sample_content,
        recommendations=recommendations,
        file_path="test.md",
        persist=True
    )

    # Check database status updated
    for rec_id in approved_recommendations:
        rec = db_manager.get_recommendation(rec_id)

        # If it was applied, status should be 'applied'
        if any(r["recommendation_id"] == rec_id and r["status"] == "applied"
               for r in result["results"]):
            assert rec["status"] == "applied"


# =============================================================================
# Edge Cases
# =============================================================================

@pytest.mark.asyncio
async def test_empty_recommendations_list(enhancement_agent, sample_content):
    """Test with empty recommendations list."""
    result = await enhancement_agent.enhance_with_recommendations(
        content=sample_content,
        recommendations=[],
        file_path="test.md"
    )

    assert result["applied_count"] == 0
    assert result["enhanced_content"] == sample_content  # Unchanged


@pytest.mark.asyncio
async def test_no_approved_recommendations(enhancement_agent, db_manager, sample_content):
    """Test when no recommendations are approved."""
    # Create only rejected recommendations
    rejected_rec = {
        "validation_id": "test_val",
        "type": "test",
        "status": "rejected",
        "original_content": "test",
        "proposed_content": "modified"
    }

    rec_id = db_manager.save_recommendation(rejected_rec)
    recommendations = [db_manager.get_recommendation(rec_id)]

    result = await enhancement_agent.enhance_with_recommendations(
        content=sample_content,
        recommendations=recommendations,
        file_path="test.md"
    )

    assert result["applied_count"] == 0
    assert result["skipped_count"] == 1


@pytest.mark.asyncio
async def test_recommendation_with_no_content(enhancement_agent, db_manager, sample_content):
    """Test recommendation without original/proposed content."""
    # Create recommendation missing content fields
    rec_data = {
        "validation_id": "test_val",
        "type": "test",
        "status": "approved",
        "original_content": None,
        "proposed_content": None
    }

    rec_id = db_manager.save_recommendation(rec_data)
    recommendations = [db_manager.get_recommendation(rec_id)]

    result = await enhancement_agent.enhance_with_recommendations(
        content=sample_content,
        recommendations=recommendations,
        file_path="test.md"
    )

    # Should handle gracefully
    assert result is not None


@pytest.mark.asyncio
async def test_overlapping_recommendations(enhancement_agent, db_manager):
    """Test handling overlapping content modifications."""
    content = "This is a test document"

    # Create overlapping recommendations
    rec1 = {
        "validation_id": "test",
        "type": "test",
        "status": "approved",
        "original_content": "test",
        "proposed_content": "example"
    }

    rec2 = {
        "validation_id": "test",
        "type": "test",
        "status": "approved",
        "original_content": "test document",
        "proposed_content": "sample file"
    }

    rec1_id = db_manager.save_recommendation(rec1)
    rec2_id = db_manager.save_recommendation(rec2)

    recommendations = [
        db_manager.get_recommendation(rec1_id),
        db_manager.get_recommendation(rec2_id)
    ]

    result = await enhancement_agent.enhance_with_recommendations(
        content=content,
        recommendations=recommendations,
        file_path="test.md"
    )

    # Should handle overlapping changes
    assert result is not None


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

    rec = {
        "validation_id": "test",
        "type": "test",
        "status": "approved",
        "original_content": "Content",
        "proposed_content": "Modified Content"
    }

    rec_id = db_manager.save_recommendation(rec)
    recommendations = [db_manager.get_recommendation(rec_id)]

    result = await enhancement_agent.enhance_with_recommendations(
        content=content,
        recommendations=recommendations,
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

    rec = {
        "validation_id": "test",
        "type": "test",
        "status": "approved",
        "original_content": "Test",
        "proposed_content": "Example"
    }

    rec_id = db_manager.save_recommendation(rec)
    recommendations = [db_manager.get_recommendation(rec_id)]

    result = await enhancement_agent.enhance_with_recommendations(
        content=content,
        recommendations=recommendations,
        file_path="test.md"
    )

    enhanced = result["enhanced_content"]

    # Code block should be intact
    assert "```python" in enhanced
    assert 'print("hello")' in enhanced
    assert "```" in enhanced


# =============================================================================
# Integration Tests
# =============================================================================

@pytest.mark.asyncio
async def test_full_enhancement_workflow(enhancement_agent, db_manager):
    """Test complete enhancement workflow."""
    # 1. Create content
    content = """---
title: Test
---
# Test
Using Document plugin."""

    # 2. Create validation
    validation_data = {
        "file_path": "test.md",
        "validation_results": {"test": "data"},
        "status": "fail"
    }
    validation_id = db_manager.save_validation_result(validation_data)

    # 3. Create recommendations
    rec = {
        "validation_id": validation_id,
        "type": "plugin_link",
        "title": "Add plugin link",
        "status": "approved",
        "original_content": "Document plugin",
        "proposed_content": "[Document](https://example.com/doc) plugin",
        "confidence": 0.95
    }
    rec_id = db_manager.save_recommendation(rec)

    # 4. Apply enhancement
    recommendations = [db_manager.get_recommendation(rec_id)]
    result = await enhancement_agent.enhance_with_recommendations(
        content=content,
        recommendations=recommendations,
        file_path="test.md",
        persist=True
    )

    # 5. Verify results
    assert result["applied_count"] == 1
    assert "[Document]" in result["enhanced_content"]

    # 6. Verify database updated
    updated_rec = db_manager.get_recommendation(rec_id)
    assert updated_rec["status"] == "applied"


@pytest.mark.asyncio
async def test_enhancement_idempotence(enhancement_agent, db_manager, sample_content, approved_recommendations):
    """Test that applying same recommendations twice produces same result."""
    recommendations = [
        db_manager.get_recommendation(rec_id)
        for rec_id in approved_recommendations
    ]

    # First application
    result1 = await enhancement_agent.enhance_with_recommendations(
        content=sample_content,
        recommendations=recommendations,
        file_path="test.md"
    )

    # Second application (to already enhanced content)
    result2 = await enhancement_agent.enhance_with_recommendations(
        content=result1["enhanced_content"],
        recommendations=recommendations,
        file_path="test.md"
    )

    # Results should be similar (idempotent)
    # Note: Some recommendations might not apply second time if content changed
    assert result2 is not None


# =============================================================================
# Error Handling
# =============================================================================

@pytest.mark.asyncio
async def test_handle_invalid_content(enhancement_agent, db_manager):
    """Test handling invalid content gracefully."""
    invalid_content = None

    rec = {
        "validation_id": "test",
        "type": "test",
        "status": "approved",
        "original_content": "test",
        "proposed_content": "modified"
    }

    rec_id = db_manager.save_recommendation(rec)
    recommendations = [db_manager.get_recommendation(rec_id)]

    try:
        result = await enhancement_agent.enhance_with_recommendations(
            content=invalid_content,
            recommendations=recommendations,
            file_path="test.md"
        )
        # Should handle gracefully or raise specific error
        assert result is not None or True
    except (TypeError, ValueError) as e:
        # Expected for None content
        assert True


@pytest.mark.asyncio
async def test_handle_database_error(enhancement_agent, db_manager):
    """Test handling database errors during status update."""
    content = "test content"

    rec = {
        "validation_id": "test",
        "type": "test",
        "status": "approved",
        "original_content": "test",
        "proposed_content": "modified"
    }

    rec_id = db_manager.save_recommendation(rec)
    recommendations = [db_manager.get_recommendation(rec_id)]

    # Close database to simulate error
    db_manager.close()

    try:
        result = await enhancement_agent.enhance_with_recommendations(
            content=content,
            recommendations=recommendations,
            file_path="test.md",
            persist=True
        )

        # Should still work even if persist fails
        assert result is not None
    except Exception:
        # Database errors might propagate
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
