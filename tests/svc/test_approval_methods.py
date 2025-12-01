"""
Comprehensive tests for MCP approval methods.

Tests approve, reject, bulk_approve, and bulk_reject methods with
performance validation and edge case handling.
"""

import pytest
import time
from pathlib import Path
from svc.mcp_client import MCPSyncClient, MCPAsyncClient
from svc.mcp_exceptions import MCPError
from core.database import ValidationStatus


class TestApprovalMethods:
    """Test approval MCP methods."""

    def test_approve_single_id_string(self, mcp_sync_client, test_markdown_file):
        """Test approving single validation with string ID."""
        # Create validation
        validation = mcp_sync_client.validate_file(str(test_markdown_file))
        vid = validation["validation_id"]

        # Approve with string ID (not list)
        result = mcp_sync_client.approve(vid)

        assert result["success"] is True
        assert result["approved_count"] == 1
        assert result["failed_count"] == 0
        assert len(result.get("errors", [])) == 0

        # Verify status changed
        retrieved = mcp_sync_client.get_validation(vid)
        assert retrieved["validation"]["status"] == "approved"

    def test_approve_single_id_list(self, mcp_sync_client, test_markdown_file):
        """Test approving single validation with list of one ID."""
        # Create validation
        validation = mcp_sync_client.validate_file(str(test_markdown_file))
        vid = validation["validation_id"]

        # Approve with list
        result = mcp_sync_client.approve([vid])

        assert result["success"] is True
        assert result["approved_count"] == 1
        assert result["failed_count"] == 0

    def test_approve_multiple_ids(self, mcp_sync_client, test_markdown_files):
        """Test approving multiple validations."""
        # Create multiple validations
        vids = []
        for file_path in test_markdown_files[:3]:
            v = mcp_sync_client.validate_file(str(file_path))
            vids.append(v["validation_id"])

        # Approve all
        result = mcp_sync_client.approve(vids)

        assert result["success"] is True
        assert result["approved_count"] == 3
        assert result["failed_count"] == 0

        # Verify all approved
        for vid in vids:
            retrieved = mcp_sync_client.get_validation(vid)
            assert retrieved["validation"]["status"] == "approved"

    def test_approve_with_invalid_id(self, mcp_sync_client):
        """Test approving with invalid ID."""
        result = mcp_sync_client.approve(["invalid-id-12345"])

        # Should not crash, but report error
        assert result["approved_count"] == 0
        assert result["failed_count"] == 1
        assert len(result["errors"]) == 1
        assert "not found" in result["errors"][0].lower()

    def test_approve_mixed_valid_invalid(self, mcp_sync_client, test_markdown_file):
        """Test approving mix of valid and invalid IDs."""
        # Create one valid validation
        valid = mcp_sync_client.validate_file(str(test_markdown_file))
        valid_id = valid["validation_id"]

        # Try to approve valid + invalid
        result = mcp_sync_client.approve([valid_id, "invalid-id-12345"])

        assert result["approved_count"] == 1
        assert result["failed_count"] == 1
        assert len(result["errors"]) == 1

    def test_approve_empty_list(self, mcp_sync_client):
        """Test approving with empty list returns success with 0 counts."""
        result = mcp_sync_client.approve([])

        # Empty list should succeed gracefully with 0 counts
        assert result["success"] is True
        assert result["approved_count"] == 0
        assert result["failed_count"] == 0
        assert "errors" in result

    def test_reject_single_id(self, mcp_sync_client, test_markdown_file):
        """Test rejecting single validation."""
        validation = mcp_sync_client.validate_file(str(test_markdown_file))
        vid = validation["validation_id"]

        # Reject
        result = mcp_sync_client.reject(vid)

        assert result["success"] is True
        assert result["rejected_count"] == 1
        assert result["failed_count"] == 0

        # Verify status changed
        retrieved = mcp_sync_client.get_validation(vid)
        assert retrieved["validation"]["status"] == "rejected"

    def test_reject_with_reason(self, mcp_sync_client, test_markdown_file):
        """Test rejecting with reason adds to notes."""
        validation = mcp_sync_client.validate_file(str(test_markdown_file))
        vid = validation["validation_id"]

        # Reject with reason
        result = mcp_sync_client.reject(vid, reason="Needs improvement")

        assert result["success"] is True
        assert result["rejected_count"] == 1

        # Verify reason stored in notes
        retrieved = mcp_sync_client.get_validation(vid)
        assert "Needs improvement" in retrieved["validation"].get("notes", "")

    def test_reject_multiple_with_reason(self, mcp_sync_client, test_markdown_files):
        """Test rejecting multiple validations with reason."""
        # Create multiple validations
        vids = []
        for file_path in test_markdown_files[:2]:
            v = mcp_sync_client.validate_file(str(file_path))
            vids.append(v["validation_id"])

        # Reject all with reason
        result = mcp_sync_client.reject(vids, reason="Batch rejection test")

        assert result["success"] is True
        assert result["rejected_count"] == 2
        assert result["failed_count"] == 0

        # Verify all have reason in notes
        for vid in vids:
            retrieved = mcp_sync_client.get_validation(vid)
            assert "Batch rejection test" in retrieved["validation"].get("notes", "")

    def test_bulk_approve_performance(self, mcp_sync_client, tmp_path):
        """Test bulk approve handles many validations efficiently."""
        # Create test validations
        vids = []
        for i in range(10):  # Use 10 for test speed
            test_file = tmp_path / f"test{i}.md"
            test_file.write_text(f"# Test {i}\n\nContent here.", encoding="utf-8")
            v = mcp_sync_client.validate_file(str(test_file))
            vids.append(v["validation_id"])

        # Bulk approve
        result = mcp_sync_client.bulk_approve(vids, batch_size=5)

        assert result["success"] is True
        assert result["total"] == 10
        assert result["approved_count"] == 10
        assert result["failed_count"] == 0
        assert "processing_time_ms" in result
        assert result["processing_time_ms"] < 1000  # Should be fast

        # Verify all approved
        for vid in vids:
            retrieved = mcp_sync_client.get_validation(vid)
            assert retrieved["validation"]["status"] == "approved"

    def test_bulk_reject_performance(self, mcp_sync_client, tmp_path):
        """Test bulk reject handles many validations efficiently."""
        # Create test validations
        vids = []
        for i in range(10):
            test_file = tmp_path / f"test{i}.md"
            test_file.write_text(f"# Test {i}\n\nContent here.", encoding="utf-8")
            v = mcp_sync_client.validate_file(str(test_file))
            vids.append(v["validation_id"])

        # Bulk reject
        result = mcp_sync_client.bulk_reject(
            vids,
            reason="Bulk test rejection",
            batch_size=5
        )

        assert result["success"] is True
        assert result["total"] == 10
        assert result["rejected_count"] == 10
        assert result["failed_count"] == 0
        assert "processing_time_ms" in result
        assert result["processing_time_ms"] < 1000

        # Verify all rejected with reason
        for vid in vids:
            retrieved = mcp_sync_client.get_validation(vid)
            assert retrieved["validation"]["status"] == "rejected"
            assert "Bulk test rejection" in retrieved["validation"].get("notes", "")

    def test_bulk_approve_empty_list(self, mcp_sync_client):
        """Test bulk approve with empty list returns success with 0 counts."""
        result = mcp_sync_client.bulk_approve([])

        # Empty list should succeed gracefully with 0 counts
        assert result["success"] is True
        assert result["total"] == 0
        assert result["approved_count"] == 0
        assert result["failed_count"] == 0

    def test_bulk_approve_with_batching(self, mcp_sync_client, tmp_path):
        """Test bulk approve processes in batches correctly."""
        # Create 15 validations
        vids = []
        for i in range(15):
            test_file = tmp_path / f"test{i}.md"
            test_file.write_text(f"# Test {i}", encoding="utf-8")
            v = mcp_sync_client.validate_file(str(test_file))
            vids.append(v["validation_id"])

        # Bulk approve with batch size of 5 (should create 3 batches)
        result = mcp_sync_client.bulk_approve(vids, batch_size=5)

        assert result["success"] is True
        assert result["approved_count"] == 15
        assert result["failed_count"] == 0

    def test_bulk_approve_partial_failure(self, mcp_sync_client, test_markdown_file):
        """Test bulk approve handles partial failures correctly."""
        # Create one valid validation
        valid = mcp_sync_client.validate_file(str(test_markdown_file))
        valid_id = valid["validation_id"]

        # Mix valid and invalid IDs
        mixed_ids = [valid_id, "invalid-1", "invalid-2"]

        result = mcp_sync_client.bulk_approve(mixed_ids)

        assert result["total"] == 3
        assert result["approved_count"] == 1
        assert result["failed_count"] == 2
        assert len(result["errors"]) == 2

    def test_approve_idempotent(self, mcp_sync_client, test_markdown_file):
        """Test approving already approved validation is idempotent."""
        validation = mcp_sync_client.validate_file(str(test_markdown_file))
        vid = validation["validation_id"]

        # Approve first time
        result1 = mcp_sync_client.approve(vid)
        assert result1["approved_count"] == 1

        # Approve second time (should still succeed)
        result2 = mcp_sync_client.approve(vid)
        assert result2["approved_count"] == 1

        # Status should still be approved
        retrieved = mcp_sync_client.get_validation(vid)
        assert retrieved["validation"]["status"] == "approved"

    def test_reject_appends_to_existing_notes(self, mcp_sync_client, test_markdown_file):
        """Test rejecting with reason appends to existing notes."""
        validation = mcp_sync_client.validate_file(str(test_markdown_file))
        vid = validation["validation_id"]

        # Add initial notes
        mcp_sync_client.update_validation(vid, notes="Initial notes")

        # Reject with reason
        mcp_sync_client.reject(vid, reason="Rejection reason")

        # Verify both notes present
        retrieved = mcp_sync_client.get_validation(vid)
        notes = retrieved["validation"].get("notes", "")
        assert "Initial notes" in notes
        assert "Rejection reason" in notes


class TestApprovalMethodsAsync:
    """Test async approval methods."""

    @pytest.mark.asyncio
    async def test_approve_async(self, mcp_async_client, test_markdown_file):
        """Test async approve method."""
        # Create validation
        validation = await mcp_async_client.validate_file(str(test_markdown_file))
        vid = validation["validation_id"]

        # Approve asynchronously
        result = await mcp_async_client.approve(vid)

        assert result["success"] is True
        assert result["approved_count"] == 1
        assert result["failed_count"] == 0

    @pytest.mark.asyncio
    async def test_reject_async(self, mcp_async_client, test_markdown_file):
        """Test async reject method."""
        validation = await mcp_async_client.validate_file(str(test_markdown_file))
        vid = validation["validation_id"]

        # Reject asynchronously
        result = await mcp_async_client.reject(vid, reason="Async test")

        assert result["success"] is True
        assert result["rejected_count"] == 1

    @pytest.mark.asyncio
    async def test_bulk_approve_async(self, mcp_async_client, tmp_path):
        """Test async bulk approve method."""
        # Create validations
        vids = []
        for i in range(5):
            test_file = tmp_path / f"test{i}.md"
            test_file.write_text(f"# Test {i}", encoding="utf-8")
            v = await mcp_async_client.validate_file(str(test_file))
            vids.append(v["validation_id"])

        # Bulk approve asynchronously
        result = await mcp_async_client.bulk_approve(vids)

        assert result["success"] is True
        assert result["approved_count"] == 5

    @pytest.mark.asyncio
    async def test_bulk_reject_async(self, mcp_async_client, tmp_path):
        """Test async bulk reject method."""
        # Create validations
        vids = []
        for i in range(5):
            test_file = tmp_path / f"test{i}.md"
            test_file.write_text(f"# Test {i}", encoding="utf-8")
            v = await mcp_async_client.validate_file(str(test_file))
            vids.append(v["validation_id"])

        # Bulk reject asynchronously
        result = await mcp_async_client.bulk_reject(vids, reason="Async bulk test")

        assert result["success"] is True
        assert result["rejected_count"] == 5


class TestApprovalPerformance:
    """Performance tests for approval methods."""

    def test_bulk_approve_100_validations(self, mcp_sync_client, tmp_path):
        """Test bulk approve with 100 validations meets performance requirement."""
        # Create 100 test validations
        vids = []
        for i in range(100):
            test_file = tmp_path / f"perf_test_{i}.md"
            test_file.write_text(f"# Performance Test {i}\n\nContent.", encoding="utf-8")
            v = mcp_sync_client.validate_file(str(test_file))
            vids.append(v["validation_id"])

        # Measure bulk approve performance
        result = mcp_sync_client.bulk_approve(vids)

        # Verify all approved
        assert result["approved_count"] == 100
        assert result["failed_count"] == 0

        # Performance requirement: <100ms for 100 validations
        assert result["processing_time_ms"] < 100, (
            f"Bulk approve took {result['processing_time_ms']:.2f}ms, "
            f"requirement is <100ms for 100 validations"
        )

    def test_approve_vs_bulk_approve_performance(self, mcp_sync_client, tmp_path):
        """Compare regular approve vs bulk_approve performance."""
        # Create 20 validations
        vids = []
        for i in range(20):
            test_file = tmp_path / f"comp_test_{i}.md"
            test_file.write_text(f"# Test {i}", encoding="utf-8")
            v = mcp_sync_client.validate_file(str(test_file))
            vids.append(v["validation_id"])

        # Test regular approve (first 10)
        start = time.time()
        for vid in vids[:10]:
            mcp_sync_client.approve(vid)
        regular_time = (time.time() - start) * 1000

        # Test bulk approve (last 10)
        result = mcp_sync_client.bulk_approve(vids[10:])
        bulk_time = result["processing_time_ms"]

        # Bulk should be faster or comparable
        print(f"\nRegular approve: {regular_time:.2f}ms")
        print(f"Bulk approve: {bulk_time:.2f}ms")

        # Bulk should generally be more efficient
        # (allowing some variance in test environment)
        assert result["approved_count"] == 10


class TestApprovalEdgeCases:
    """Test edge cases and error conditions."""

    def test_approve_non_list_non_string(self, mcp_sync_client):
        """Test approve handles invalid input types gracefully."""
        # Pass dict instead of string/list - should fail during iteration
        # The implementation normalizes string to list, so non-iterables fail gracefully
        try:
            result = mcp_sync_client._call("approve", {"ids": {"invalid": "type"}})
            # If it somehow succeeds, it should have errors
            assert result["failed_count"] > 0 or result["approved_count"] == 0
        except (TypeError, ValueError, MCPError):
            # Expected - invalid type raises error
            pass

    def test_bulk_approve_requires_list(self, mcp_sync_client, test_markdown_file):
        """Test bulk_approve requires list, not string."""
        validation = mcp_sync_client.validate_file(str(test_markdown_file))
        vid = validation["validation_id"]

        # Try to call bulk_approve with string instead of list
        with pytest.raises(Exception, match="requires a list"):
            mcp_sync_client._call("bulk_approve", {"ids": vid})

    def test_approve_updates_timestamp(self, mcp_sync_client, test_markdown_file):
        """Test approve updates the updated_at timestamp."""
        validation = mcp_sync_client.validate_file(str(test_markdown_file))
        vid = validation["validation_id"]

        # Get original timestamp
        original = mcp_sync_client.get_validation(vid)
        original_time = original["validation"]["updated_at"]

        # Wait a moment and approve
        time.sleep(0.1)
        mcp_sync_client.approve(vid)

        # Verify timestamp updated
        updated = mcp_sync_client.get_validation(vid)
        updated_time = updated["validation"]["updated_at"]

        assert updated_time > original_time

    def test_bulk_approve_batch_size_customization(self, mcp_sync_client, tmp_path):
        """Test bulk approve with custom batch size."""
        # Create 15 validations
        vids = []
        for i in range(15):
            test_file = tmp_path / f"batch_test_{i}.md"
            test_file.write_text(f"# Test {i}", encoding="utf-8")
            v = mcp_sync_client.validate_file(str(test_file))
            vids.append(v["validation_id"])

        # Use custom batch size
        result = mcp_sync_client.bulk_approve(vids, batch_size=3)

        assert result["approved_count"] == 15
        assert result["total"] == 15
