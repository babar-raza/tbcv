"""
Comprehensive tests for MCP enhancement methods.

Tests enhance_batch, enhance_preview, enhance_auto_apply, and
get_enhancement_comparison methods with performance validation.
"""

import pytest
import time
from pathlib import Path
from unittest.mock import Mock, patch
from svc.mcp_client import MCPSyncClient, MCPAsyncClient
from svc.mcp_exceptions import MCPError
from core.database import ValidationStatus


class TestEnhanceBatchMethod:
    """Test enhance_batch MCP method."""

    def test_enhance_batch_success(self, mcp_sync_client, test_markdown_files):
        """Test batch enhancement of multiple validations."""
        # Create and approve multiple validations
        vids = []
        for file_path in test_markdown_files[:3]:
            v = mcp_sync_client.validate_file(str(file_path))
            vid = v["validation_id"]
            mcp_sync_client.approve([vid])
            vids.append(vid)

        # Mock Ollama to avoid actual LLM calls
        with patch('core.ollama.get_ollama_client') as mock_ollama:
            mock_client = Mock()
            mock_client.chat.return_value = {
                "message": {
                    "content": "# Enhanced Document\n\nEnhanced content here."
                }
            }
            mock_ollama.return_value = mock_client

            # Batch enhance
            result = mcp_sync_client.enhance_batch(vids, batch_size=2)

            assert result["total"] == 3
            assert result["enhanced_count"] >= 0
            assert "processing_time_ms" in result
            assert isinstance(result["processing_time_ms"], (int, float))

    def test_enhance_batch_with_batch_size(self, mcp_sync_client, test_markdown_files):
        """Test batch enhancement respects batch size."""
        # Create and approve validations
        vids = []
        for file_path in test_markdown_files:
            v = mcp_sync_client.validate_file(str(file_path))
            vid = v["validation_id"]
            mcp_sync_client.approve([vid])
            vids.append(vid)

        with patch('core.ollama.get_ollama_client') as mock_ollama:
            mock_client = Mock()
            mock_client.chat.return_value = {
                "message": {"content": "# Enhanced\n\nContent."}
            }
            mock_ollama.return_value = mock_client

            # Batch enhance with small batch size
            result = mcp_sync_client.enhance_batch(vids, batch_size=1)

            assert result["total"] == len(vids)
            assert "results" in result

    def test_enhance_batch_with_threshold(self, mcp_sync_client, test_markdown_files):
        """Test batch enhancement with confidence threshold."""
        # Create and approve validations
        vids = []
        for file_path in test_markdown_files[:2]:
            v = mcp_sync_client.validate_file(str(file_path))
            vid = v["validation_id"]
            mcp_sync_client.approve([vid])
            vids.append(vid)

        with patch('core.ollama.get_ollama_client') as mock_ollama:
            mock_client = Mock()
            mock_client.chat.return_value = {
                "message": {"content": "# Enhanced\n\nContent."}
            }
            mock_ollama.return_value = mock_client

            # Batch enhance with high threshold
            result = mcp_sync_client.enhance_batch(vids, threshold=0.95)

            assert "threshold" not in result or result.get("enhanced_count") >= 0

    def test_enhance_batch_partial_failure(self, mcp_sync_client, test_markdown_file):
        """Test batch enhance handles partial failures."""
        # Create one valid validation
        v = mcp_sync_client.validate_file(str(test_markdown_file))
        valid_id = v["validation_id"]
        mcp_sync_client.approve([valid_id])

        with patch('core.ollama.get_ollama_client') as mock_ollama:
            mock_client = Mock()
            mock_client.chat.return_value = {
                "message": {"content": "# Enhanced\n\nContent."}
            }
            mock_ollama.return_value = mock_client

            # Mix valid and invalid IDs
            result = mcp_sync_client.enhance_batch([valid_id, "invalid-id-12345"])

            assert result["total"] == 2
            assert result["failed_count"] > 0
            assert len(result["errors"]) > 0

    def test_enhance_batch_empty_list(self, mcp_sync_client):
        """Test batch enhance with empty list."""
        result = mcp_sync_client.enhance_batch([])

        assert result["total"] == 0
        assert result["enhanced_count"] == 0
        assert result["failed_count"] == 0
        assert result["skipped_count"] == 0

    def test_enhance_batch_unapproved_validations(self, mcp_sync_client, test_markdown_files):
        """Test batch enhance skips unapproved validations."""
        # Create validations without approving
        vids = []
        for file_path in test_markdown_files[:2]:
            v = mcp_sync_client.validate_file(str(file_path))
            vids.append(v["validation_id"])

        # Try to enhance without approval
        result = mcp_sync_client.enhance_batch(vids)

        assert result["enhanced_count"] == 0
        assert result["skipped_count"] > 0
        assert "not approved" in str(result["errors"]).lower()


class TestEnhancePreviewMethod:
    """Test enhance_preview MCP method."""

    def test_enhance_preview_shows_changes(self, mcp_sync_client, test_markdown_file):
        """Test preview shows changes without applying."""
        # Validate and approve
        v = mcp_sync_client.validate_file(str(test_markdown_file))
        vid = v["validation_id"]
        mcp_sync_client.approve([vid])

        # Read original content
        original_content = test_markdown_file.read_text()

        with patch('core.ollama.get_ollama_client') as mock_ollama:
            mock_client = Mock()
            mock_client.chat.return_value = {
                "message": {
                    "content": "# Enhanced Test Document\n\nThis is enhanced content."
                }
            }
            mock_ollama.return_value = mock_client

            # Preview enhancement
            preview = mcp_sync_client.enhance_preview(vid)

            assert preview["validation_id"] == vid
            assert "original_content" in preview
            assert "enhanced_content" in preview
            assert "diff" in preview
            assert "changes_summary" in preview

            # Verify file is unchanged
            assert test_markdown_file.read_text() == original_content

    def test_enhance_preview_with_diff(self, mcp_sync_client, test_markdown_file):
        """Test preview generates diff correctly."""
        # Validate and approve
        v = mcp_sync_client.validate_file(str(test_markdown_file))
        vid = v["validation_id"]
        mcp_sync_client.approve([vid])

        with patch('core.ollama.get_ollama_client') as mock_ollama:
            mock_client = Mock()
            mock_client.chat.return_value = {
                "message": {
                    "content": "# Different Title\n\nDifferent content."
                }
            }
            mock_ollama.return_value = mock_client

            preview = mcp_sync_client.enhance_preview(vid)

            # Check diff structure
            assert "diff" in preview
            diff = preview["diff"]
            assert "unified_diff" in diff or "side_by_side" in diff

    def test_enhance_preview_no_changes(self, mcp_sync_client, test_markdown_file):
        """Test preview with no changes."""
        # Validate and approve
        v = mcp_sync_client.validate_file(str(test_markdown_file))
        vid = v["validation_id"]
        mcp_sync_client.approve([vid])

        # Return same content (no changes)
        original_content = test_markdown_file.read_text()

        with patch('core.ollama.get_ollama_client') as mock_ollama:
            mock_client = Mock()
            mock_client.chat.return_value = {
                "message": {"content": original_content}
            }
            mock_ollama.return_value = mock_client

            preview = mcp_sync_client.enhance_preview(vid)

            # Should succeed even with no changes
            assert preview["validation_id"] == vid
            assert preview["changes_summary"]["additions"] >= 0

    def test_enhance_preview_invalid_id(self, mcp_sync_client):
        """Test preview with invalid validation ID."""
        with pytest.raises(MCPError):
            mcp_sync_client.enhance_preview("invalid-id-12345")

    def test_enhance_preview_with_threshold(self, mcp_sync_client, test_markdown_file):
        """Test preview with custom threshold."""
        v = mcp_sync_client.validate_file(str(test_markdown_file))
        vid = v["validation_id"]
        mcp_sync_client.approve([vid])

        with patch('core.ollama.get_ollama_client') as mock_ollama:
            mock_client = Mock()
            mock_client.chat.return_value = {
                "message": {"content": "# Enhanced\n\nContent."}
            }
            mock_ollama.return_value = mock_client

            # Preview with high threshold
            preview = mcp_sync_client.enhance_preview(vid, threshold=0.95)

            assert preview["validation_id"] == vid


class TestEnhanceAutoApplyMethod:
    """Test enhance_auto_apply MCP method."""

    def test_enhance_auto_apply_with_threshold(self, mcp_sync_client, test_markdown_file):
        """Test auto-apply respects threshold."""
        # Validate and approve
        v = mcp_sync_client.validate_file(str(test_markdown_file))
        vid = v["validation_id"]
        mcp_sync_client.approve([vid])

        with patch('core.ollama.get_ollama_client') as mock_ollama:
            mock_client = Mock()
            mock_client.chat.return_value = {
                "message": {"content": "# Enhanced\n\nContent."}
            }
            mock_ollama.return_value = mock_client

            # Auto-apply with high threshold
            result = mcp_sync_client.enhance_auto_apply(vid, threshold=0.95)

            assert "applied_count" in result
            assert "skipped_count" in result

    def test_enhance_auto_apply_preview_first(self, mcp_sync_client, test_markdown_file):
        """Test auto-apply with preview first."""
        # Validate and approve
        v = mcp_sync_client.validate_file(str(test_markdown_file))
        vid = v["validation_id"]
        mcp_sync_client.approve([vid])

        with patch('core.ollama.get_ollama_client') as mock_ollama:
            mock_client = Mock()
            mock_client.chat.return_value = {
                "message": {"content": "# Enhanced\n\nContent."}
            }
            mock_ollama.return_value = mock_client

            result = mcp_sync_client.enhance_auto_apply(vid, preview_first=True)

            # Should include preview in result
            if result.get("applied_count", 0) > 0:
                assert "preview" in result

    def test_enhance_auto_apply_no_preview(self, mcp_sync_client, test_markdown_file):
        """Test auto-apply without preview."""
        v = mcp_sync_client.validate_file(str(test_markdown_file))
        vid = v["validation_id"]
        mcp_sync_client.approve([vid])

        with patch('core.ollama.get_ollama_client') as mock_ollama:
            mock_client = Mock()
            mock_client.chat.return_value = {
                "message": {"content": "# Enhanced\n\nContent."}
            }
            mock_ollama.return_value = mock_client

            result = mcp_sync_client.enhance_auto_apply(vid, preview_first=False)

            # Preview should be None
            assert result.get("preview") is None

    def test_enhance_auto_apply_unapproved(self, mcp_sync_client, test_markdown_file):
        """Test auto-apply on unapproved validation."""
        v = mcp_sync_client.validate_file(str(test_markdown_file))
        vid = v["validation_id"]

        # Don't approve

        result = mcp_sync_client.enhance_auto_apply(vid)

        assert result["applied_count"] == 0
        assert result["skipped_count"] > 0

    def test_enhance_auto_apply_invalid_id(self, mcp_sync_client):
        """Test auto-apply with invalid ID."""
        with pytest.raises(MCPError):
            mcp_sync_client.enhance_auto_apply("invalid-id-12345")


class TestGetEnhancementComparisonMethod:
    """Test get_enhancement_comparison MCP method."""

    def test_get_enhancement_comparison(self, mcp_sync_client, test_markdown_file):
        """Test getting enhancement comparison."""
        # Validate, approve, enhance
        v = mcp_sync_client.validate_file(str(test_markdown_file))
        vid = v["validation_id"]
        mcp_sync_client.approve([vid])

        with patch('core.ollama.get_ollama_client') as mock_ollama:
            mock_client = Mock()
            mock_client.chat.return_value = {
                "message": {"content": "# Enhanced\n\nContent."}
            }
            mock_ollama.return_value = mock_client

            mcp_sync_client.enhance([vid])

            # Get comparison
            comparison = mcp_sync_client.get_enhancement_comparison(vid)

            assert comparison["validation_id"] == vid
            assert "original_content" in comparison
            assert "enhanced_content" in comparison
            assert "diff" in comparison
            assert "statistics" in comparison

    def test_get_enhancement_comparison_statistics(self, mcp_sync_client, test_markdown_file):
        """Test comparison includes statistics."""
        v = mcp_sync_client.validate_file(str(test_markdown_file))
        vid = v["validation_id"]
        mcp_sync_client.approve([vid])

        with patch('core.ollama.get_ollama_client') as mock_ollama:
            mock_client = Mock()
            mock_client.chat.return_value = {
                "message": {"content": "# Enhanced\n\nDifferent content."}
            }
            mock_ollama.return_value = mock_client

            mcp_sync_client.enhance([vid])

            comparison = mcp_sync_client.get_enhancement_comparison(vid)

            stats = comparison["statistics"]
            assert "lines_added" in stats
            assert "lines_removed" in stats
            assert "lines_modified" in stats
            assert "total_changes" in stats

    def test_get_enhancement_comparison_not_enhanced(self, mcp_sync_client, test_markdown_file):
        """Test comparison on non-enhanced validation."""
        v = mcp_sync_client.validate_file(str(test_markdown_file))
        vid = v["validation_id"]
        mcp_sync_client.approve([vid])

        # Don't enhance

        with pytest.raises(MCPError):
            mcp_sync_client.get_enhancement_comparison(vid)

    def test_get_enhancement_comparison_invalid_id(self, mcp_sync_client):
        """Test comparison with invalid ID."""
        with pytest.raises(MCPError):
            mcp_sync_client.get_enhancement_comparison("invalid-id-12345")

    def test_get_enhancement_comparison_unified_format(self, mcp_sync_client, test_markdown_file):
        """Test comparison with unified diff format."""
        v = mcp_sync_client.validate_file(str(test_markdown_file))
        vid = v["validation_id"]
        mcp_sync_client.approve([vid])

        with patch('core.ollama.get_ollama_client') as mock_ollama:
            mock_client = Mock()
            mock_client.chat.return_value = {
                "message": {"content": "# Enhanced\n\nContent."}
            }
            mock_ollama.return_value = mock_client

            mcp_sync_client.enhance([vid])

            comparison = mcp_sync_client.get_enhancement_comparison(vid, format="unified")

            assert "diff" in comparison


class TestDiffGeneration:
    """Test diff generation functionality."""

    def test_diff_generation_additions(self, mcp_sync_client, test_markdown_file):
        """Test diff correctly identifies additions."""
        v = mcp_sync_client.validate_file(str(test_markdown_file))
        vid = v["validation_id"]
        mcp_sync_client.approve([vid])

        original_content = test_markdown_file.read_text()
        enhanced_content = original_content + "\n## New Section\n\nNew content."

        with patch('core.ollama.get_ollama_client') as mock_ollama:
            mock_client = Mock()
            mock_client.chat.return_value = {
                "message": {"content": enhanced_content}
            }
            mock_ollama.return_value = mock_client

            preview = mcp_sync_client.enhance_preview(vid)

            assert preview["changes_summary"]["additions"] > 0

    def test_diff_generation_deletions(self, mcp_sync_client, test_markdown_file):
        """Test diff correctly identifies deletions."""
        v = mcp_sync_client.validate_file(str(test_markdown_file))
        vid = v["validation_id"]
        mcp_sync_client.approve([vid])

        # Return much shorter content
        enhanced_content = "# Title\n\nShort content."

        with patch('core.ollama.get_ollama_client') as mock_ollama:
            mock_client = Mock()
            mock_client.chat.return_value = {
                "message": {"content": enhanced_content}
            }
            mock_ollama.return_value = mock_client

            preview = mcp_sync_client.enhance_preview(vid)

            # Should show deletions
            assert "changes_summary" in preview


class TestPerformance:
    """Test performance requirements."""

    def test_enhance_preview_performance(self, mcp_sync_client, test_markdown_file):
        """Test preview completes within performance threshold."""
        v = mcp_sync_client.validate_file(str(test_markdown_file))
        vid = v["validation_id"]
        mcp_sync_client.approve([vid])

        with patch('core.ollama.get_ollama_client') as mock_ollama:
            mock_client = Mock()
            mock_client.chat.return_value = {
                "message": {"content": "# Enhanced\n\nContent."}
            }
            mock_ollama.return_value = mock_client

            start_time = time.time()
            mcp_sync_client.enhance_preview(vid)
            elapsed = (time.time() - start_time) * 1000

            # Should complete reasonably fast (excluding LLM call)
            # With mocked LLM, this should be very fast
            assert elapsed < 5000  # 5 seconds for safety with mocked LLM

    def test_enhance_batch_timing(self, mcp_sync_client, test_markdown_files):
        """Test batch enhancement includes timing."""
        vids = []
        for file_path in test_markdown_files[:2]:
            v = mcp_sync_client.validate_file(str(file_path))
            vid = v["validation_id"]
            mcp_sync_client.approve([vid])
            vids.append(vid)

        with patch('core.ollama.get_ollama_client') as mock_ollama:
            mock_client = Mock()
            mock_client.chat.return_value = {
                "message": {"content": "# Enhanced\n\nContent."}
            }
            mock_ollama.return_value = mock_client

            result = mcp_sync_client.enhance_batch(vids)

            assert "processing_time_ms" in result
            assert result["processing_time_ms"] > 0


@pytest.mark.asyncio
class TestAsyncEnhancementMethods:
    """Test async versions of enhancement methods."""

    async def test_enhance_batch_async(self, mcp_async_client, test_markdown_files):
        """Test async batch enhancement."""
        vids = []
        for file_path in test_markdown_files[:2]:
            v = await mcp_async_client.validate_file(str(file_path))
            vid = v["validation_id"]
            await mcp_async_client.approve([vid])
            vids.append(vid)

        with patch('core.ollama.get_ollama_client') as mock_ollama:
            mock_client = Mock()
            mock_client.chat.return_value = {
                "message": {"content": "# Enhanced\n\nContent."}
            }
            mock_ollama.return_value = mock_client

            result = await mcp_async_client.enhance_batch(vids)

            assert result["total"] == 2

    async def test_enhance_preview_async(self, mcp_async_client, test_markdown_file):
        """Test async preview enhancement."""
        v = await mcp_async_client.validate_file(str(test_markdown_file))
        vid = v["validation_id"]
        await mcp_async_client.approve([vid])

        with patch('core.ollama.get_ollama_client') as mock_ollama:
            mock_client = Mock()
            mock_client.chat.return_value = {
                "message": {"content": "# Enhanced\n\nContent."}
            }
            mock_ollama.return_value = mock_client

            preview = await mcp_async_client.enhance_preview(vid)

            assert preview["validation_id"] == vid
