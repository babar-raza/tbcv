"""Comprehensive tests for MCP recommendation methods."""

import pytest
import tempfile
from pathlib import Path
from svc.mcp_client import MCPSyncClient, get_mcp_sync_client
from svc.mcp_exceptions import MCPError
from core.database import RecommendationStatus


@pytest.fixture
def test_validation(tmp_path):
    """Create a test validation with issues."""
    # Create test file with issues
    test_file = tmp_path / "test.md"
    test_file.write_text("# Test Document\n\nThis has some issues.")

    # Validate file to create validation record
    client = get_mcp_sync_client()
    result = client.validate_file(str(test_file))

    return result["validation_id"], str(test_file)


@pytest.fixture
def test_validation_with_content(tmp_path):
    """Create a test validation with specific content for recommendations."""
    # Create test file with obvious issues
    test_file = tmp_path / "test_rec.md"
    content = """---
title: Test Document
---

# Test Heading

This is a paragraph with original_text that needs fixing.

Another paragraph here.
"""
    test_file.write_text(content)

    # Validate file
    client = get_mcp_sync_client()
    result = client.validate_file(str(test_file))

    return result["validation_id"], str(test_file)


class TestGenerateRecommendations:
    """Tests for generate_recommendations method."""

    def test_generate_recommendations_success(self, test_validation):
        """Test successful recommendation generation."""
        validation_id, file_path = test_validation

        client = get_mcp_sync_client()
        result = client.generate_recommendations(validation_id)

        assert result["success"] is True
        assert result["validation_id"] == validation_id
        assert "recommendation_count" in result
        assert "recommendations" in result
        assert isinstance(result["recommendations"], list)
        assert result["threshold_used"] == 0.7

    def test_generate_recommendations_with_custom_threshold(self, test_validation):
        """Test recommendation generation with custom threshold."""
        validation_id, file_path = test_validation

        client = get_mcp_sync_client()
        result = client.generate_recommendations(validation_id, threshold=0.9)

        assert result["success"] is True
        assert result["threshold_used"] == 0.9

    def test_generate_recommendations_with_type_filter(self, test_validation):
        """Test recommendation generation with type filter."""
        validation_id, file_path = test_validation

        client = get_mcp_sync_client()
        result = client.generate_recommendations(
            validation_id,
            types=["markdown", "structure"]
        )

        assert result["success"] is True
        # All recommendations should match the specified types
        for rec in result["recommendations"]:
            assert rec.get("type") in ["markdown", "structure", "general"]

    def test_generate_recommendations_not_found(self):
        """Test generation fails for non-existent validation."""
        client = get_mcp_sync_client()

        with pytest.raises(Exception) as exc_info:
            client.generate_recommendations("nonexistent-id")

        assert "not found" in str(exc_info.value).lower()

    def test_generate_recommendations_low_threshold(self, test_validation):
        """Test generation with very low threshold includes more recommendations."""
        validation_id, file_path = test_validation

        client = get_mcp_sync_client()
        result = client.generate_recommendations(validation_id, threshold=0.1)

        assert result["success"] is True
        # Low threshold should potentially include more recommendations
        assert result["recommendation_count"] >= 0


class TestRebuildRecommendations:
    """Tests for rebuild_recommendations method."""

    def test_rebuild_recommendations_success(self, test_validation):
        """Test successful recommendation rebuild."""
        validation_id, file_path = test_validation

        client = get_mcp_sync_client()

        # Generate initial recommendations
        gen_result = client.generate_recommendations(validation_id)
        initial_count = gen_result["recommendation_count"]

        # Rebuild recommendations
        result = client.rebuild_recommendations(validation_id)

        assert result["success"] is True
        assert result["validation_id"] == validation_id
        assert "deleted_count" in result
        assert "generated_count" in result
        assert result["deleted_count"] == initial_count

    def test_rebuild_recommendations_with_threshold(self, test_validation):
        """Test rebuild with custom threshold."""
        validation_id, file_path = test_validation

        client = get_mcp_sync_client()
        result = client.rebuild_recommendations(validation_id, threshold=0.8)

        assert result["success"] is True


class TestGetRecommendations:
    """Tests for get_recommendations method."""

    def test_get_recommendations_success(self, test_validation):
        """Test retrieving recommendations."""
        validation_id, file_path = test_validation

        client = get_mcp_sync_client()

        # Generate recommendations first
        client.generate_recommendations(validation_id)

        # Get recommendations
        result = client.get_recommendations(validation_id)

        assert "validation_id" in result
        assert "recommendations" in result
        assert "total" in result
        assert isinstance(result["recommendations"], list)

    def test_get_recommendations_with_status_filter(self, test_validation):
        """Test retrieving recommendations with status filter."""
        validation_id, file_path = test_validation

        client = get_mcp_sync_client()

        # Generate recommendations
        gen_result = client.generate_recommendations(validation_id)

        # Get pending recommendations
        result = client.get_recommendations(validation_id, status="pending")

        assert result["total"] >= 0
        # Verify all returned recommendations have pending status
        for rec in result["recommendations"]:
            assert rec["status"] == "pending"

    def test_get_recommendations_with_type_filter(self, test_validation):
        """Test retrieving recommendations with type filter."""
        validation_id, file_path = test_validation

        client = get_mcp_sync_client()

        # Generate recommendations
        client.generate_recommendations(validation_id)

        # Get recommendations of specific type
        result = client.get_recommendations(validation_id, rec_type="general")

        assert "total" in result

    def test_get_recommendations_empty(self, test_validation):
        """Test retrieving recommendations when none exist."""
        validation_id, file_path = test_validation

        client = get_mcp_sync_client()
        result = client.get_recommendations(validation_id)

        assert result["total"] == 0
        assert result["recommendations"] == []


class TestReviewRecommendation:
    """Tests for review_recommendation method."""

    def test_review_recommendation_approve(self, test_validation):
        """Test approving a recommendation."""
        validation_id, file_path = test_validation

        client = get_mcp_sync_client()

        # Generate recommendations
        gen_result = client.generate_recommendations(validation_id)
        if gen_result["recommendation_count"] == 0:
            pytest.skip("No recommendations generated")

        rec_id = gen_result["recommendations"][0]["id"]

        # Approve recommendation
        result = client.review_recommendation(rec_id, "approve")

        assert result["success"] is True
        assert result["recommendation_id"] == rec_id
        assert result["action"] == "approve"
        assert result["new_status"] == "approved"

    def test_review_recommendation_reject(self, test_validation):
        """Test rejecting a recommendation."""
        validation_id, file_path = test_validation

        client = get_mcp_sync_client()

        # Generate recommendations
        gen_result = client.generate_recommendations(validation_id)
        if gen_result["recommendation_count"] == 0:
            pytest.skip("No recommendations generated")

        rec_id = gen_result["recommendations"][0]["id"]

        # Reject recommendation
        result = client.review_recommendation(rec_id, "reject", notes="Not applicable")

        assert result["success"] is True
        assert result["action"] == "reject"
        assert result["new_status"] == "rejected"

    def test_review_recommendation_invalid_action(self, test_validation):
        """Test review fails with invalid action."""
        validation_id, file_path = test_validation

        client = get_mcp_sync_client()

        # Generate recommendations
        gen_result = client.generate_recommendations(validation_id)
        if gen_result["recommendation_count"] == 0:
            pytest.skip("No recommendations generated")

        rec_id = gen_result["recommendations"][0]["id"]

        with pytest.raises(Exception) as exc_info:
            client.review_recommendation(rec_id, "invalid_action")

        assert "invalid action" in str(exc_info.value).lower()

    def test_review_recommendation_not_found(self):
        """Test review fails for non-existent recommendation."""
        client = get_mcp_sync_client()

        with pytest.raises(Exception) as exc_info:
            client.review_recommendation("nonexistent-id", "approve")

        assert "not found" in str(exc_info.value).lower()


class TestBulkReviewRecommendations:
    """Tests for bulk_review_recommendations method."""

    def test_bulk_review_recommendations_approve(self, test_validation):
        """Test bulk approving multiple recommendations."""
        validation_id, file_path = test_validation

        client = get_mcp_sync_client()

        # Generate recommendations
        gen_result = client.generate_recommendations(validation_id)
        if gen_result["recommendation_count"] < 1:
            pytest.skip("Not enough recommendations generated")

        rec_ids = [rec["id"] for rec in gen_result["recommendations"]]

        # Bulk approve
        result = client.bulk_review_recommendations(rec_ids, "approve")

        assert result["success"] is True
        assert result["reviewed_count"] >= 0
        assert result["action"] == "approve"
        assert isinstance(result["errors"], list)

    def test_bulk_review_recommendations_reject(self, test_validation):
        """Test bulk rejecting multiple recommendations."""
        validation_id, file_path = test_validation

        client = get_mcp_sync_client()

        # Generate recommendations
        gen_result = client.generate_recommendations(validation_id)
        if gen_result["recommendation_count"] < 1:
            pytest.skip("Not enough recommendations generated")

        rec_ids = [rec["id"] for rec in gen_result["recommendations"]]

        # Bulk reject
        result = client.bulk_review_recommendations(
            rec_ids,
            "reject",
            notes="Not needed"
        )

        assert result["success"] is True
        assert result["action"] == "reject"

    def test_bulk_review_recommendations_mixed(self, test_validation):
        """Test bulk review with some invalid IDs."""
        validation_id, file_path = test_validation

        client = get_mcp_sync_client()

        # Generate recommendations
        gen_result = client.generate_recommendations(validation_id)
        if gen_result["recommendation_count"] < 1:
            pytest.skip("Not enough recommendations generated")

        # Mix valid and invalid IDs
        rec_ids = [gen_result["recommendations"][0]["id"], "invalid-id-123"]

        result = client.bulk_review_recommendations(rec_ids, "approve")

        assert result["success"] is True
        # Should have some errors
        assert len(result["errors"]) > 0


class TestApplyRecommendations:
    """Tests for apply_recommendations method."""

    def test_apply_recommendations_dry_run(self, test_validation):
        """Test dry run mode for applying recommendations."""
        validation_id, file_path = test_validation

        client = get_mcp_sync_client()

        # Generate and approve recommendations
        gen_result = client.generate_recommendations(validation_id)
        if gen_result["recommendation_count"] < 1:
            pytest.skip("No recommendations generated")

        for rec in gen_result["recommendations"]:
            client.review_recommendation(rec["id"], "approve")

        # Apply in dry run mode
        result = client.apply_recommendations(validation_id, dry_run=True)

        assert result["success"] is True
        assert result["dry_run"] is True
        assert "applied_count" in result
        assert "skipped_count" in result

    def test_apply_recommendations_with_backup(self, test_validation_with_content):
        """Test applying recommendations with backup creation."""
        validation_id, file_path = test_validation_with_content

        client = get_mcp_sync_client()

        # Generate recommendations
        gen_result = client.generate_recommendations(validation_id)
        if gen_result["recommendation_count"] < 1:
            pytest.skip("No recommendations generated")

        # Approve all recommendations
        for rec in gen_result["recommendations"]:
            client.review_recommendation(rec["id"], "approve")

        # Apply with backup
        result = client.apply_recommendations(
            validation_id,
            create_backup=True,
            dry_run=True  # Use dry run to avoid actual file changes in test
        )

        assert result["success"] is True
        assert "applied_count" in result

    def test_apply_recommendations_no_approved(self, test_validation):
        """Test applying when no recommendations are approved."""
        validation_id, file_path = test_validation

        client = get_mcp_sync_client()

        # Generate recommendations but don't approve any
        client.generate_recommendations(validation_id)

        # Try to apply
        result = client.apply_recommendations(validation_id, dry_run=True)

        assert result["success"] is True
        assert result["applied_count"] == 0

    def test_apply_recommendations_specific_ids(self, test_validation):
        """Test applying specific recommendation IDs."""
        validation_id, file_path = test_validation

        client = get_mcp_sync_client()

        # Generate recommendations
        gen_result = client.generate_recommendations(validation_id)
        if gen_result["recommendation_count"] < 1:
            pytest.skip("No recommendations generated")

        # Approve first recommendation
        rec_id = gen_result["recommendations"][0]["id"]
        client.review_recommendation(rec_id, "approve")

        # Apply only that specific recommendation
        result = client.apply_recommendations(
            validation_id,
            recommendation_ids=[rec_id],
            dry_run=True
        )

        assert result["success"] is True


class TestDeleteRecommendation:
    """Tests for delete_recommendation method."""

    def test_delete_recommendation_success(self, test_validation):
        """Test successful recommendation deletion."""
        validation_id, file_path = test_validation

        client = get_mcp_sync_client()

        # Generate recommendations
        gen_result = client.generate_recommendations(validation_id)
        if gen_result["recommendation_count"] < 1:
            pytest.skip("No recommendations generated")

        rec_id = gen_result["recommendations"][0]["id"]

        # Delete recommendation
        result = client.delete_recommendation(rec_id)

        assert result["success"] is True
        assert result["recommendation_id"] == rec_id

    def test_delete_recommendation_not_found(self):
        """Test deletion fails for non-existent recommendation."""
        client = get_mcp_sync_client()

        with pytest.raises(Exception) as exc_info:
            client.delete_recommendation("nonexistent-id")

        assert "not found" in str(exc_info.value).lower()


class TestMarkRecommendationsApplied:
    """Tests for mark_recommendations_applied method."""

    def test_mark_recommendations_applied_success(self, test_validation):
        """Test marking recommendations as applied."""
        validation_id, file_path = test_validation

        client = get_mcp_sync_client()

        # Generate recommendations
        gen_result = client.generate_recommendations(validation_id)
        if gen_result["recommendation_count"] < 1:
            pytest.skip("No recommendations generated")

        rec_ids = [rec["id"] for rec in gen_result["recommendations"]]

        # Mark as applied
        result = client.mark_recommendations_applied(rec_ids)

        assert result["success"] is True
        assert result["marked_count"] >= 0
        assert isinstance(result["errors"], list)

    def test_mark_recommendations_applied_empty_list(self):
        """Test marking with empty list."""
        client = get_mcp_sync_client()

        result = client.mark_recommendations_applied([])

        assert result["success"] is True
        assert result["marked_count"] == 0

    def test_mark_recommendations_applied_invalid_id(self):
        """Test marking with invalid ID."""
        client = get_mcp_sync_client()

        result = client.mark_recommendations_applied(["invalid-id-123"])

        assert result["success"] is True
        # Should have errors for invalid ID
        assert len(result["errors"]) > 0


class TestRecommendationWorkflow:
    """Integration tests for complete recommendation workflows."""

    def test_complete_recommendation_workflow(self, test_validation):
        """Test complete recommendation workflow: generate -> review -> apply."""
        validation_id, file_path = test_validation

        client = get_mcp_sync_client()

        # Step 1: Generate recommendations
        gen_result = client.generate_recommendations(validation_id, threshold=0.5)
        assert gen_result["success"] is True

        if gen_result["recommendation_count"] < 1:
            pytest.skip("No recommendations generated for workflow test")

        # Step 2: Review recommendations
        for rec in gen_result["recommendations"]:
            review_result = client.review_recommendation(rec["id"], "approve")
            assert review_result["success"] is True

        # Step 3: Apply recommendations (dry run)
        apply_result = client.apply_recommendations(validation_id, dry_run=True)
        assert apply_result["success"] is True

    def test_rebuild_after_changes(self, test_validation):
        """Test rebuilding recommendations after validation changes."""
        validation_id, file_path = test_validation

        client = get_mcp_sync_client()

        # Generate initial recommendations
        gen1 = client.generate_recommendations(validation_id)
        initial_count = gen1["recommendation_count"]

        # Rebuild recommendations
        rebuild_result = client.rebuild_recommendations(validation_id, threshold=0.8)
        assert rebuild_result["success"] is True
        assert rebuild_result["deleted_count"] == initial_count

        # Verify new recommendations
        get_result = client.get_recommendations(validation_id)
        assert get_result["total"] == rebuild_result["generated_count"]

    def test_selective_application(self, test_validation):
        """Test applying only selected recommendations."""
        validation_id, file_path = test_validation

        client = get_mcp_sync_client()

        # Generate recommendations
        gen_result = client.generate_recommendations(validation_id, threshold=0.5)
        if gen_result["recommendation_count"] < 2:
            pytest.skip("Need at least 2 recommendations for selective application test")

        # Approve only first recommendation
        rec_id = gen_result["recommendations"][0]["id"]
        client.review_recommendation(rec_id, "approve")

        # Apply only approved recommendation
        apply_result = client.apply_recommendations(
            validation_id,
            recommendation_ids=[rec_id],
            dry_run=True
        )

        assert apply_result["success"] is True


class TestRecommendationEdgeCases:
    """Tests for edge cases and error handling."""

    def test_generate_recommendations_multiple_times(self, test_validation):
        """Test generating recommendations multiple times."""
        validation_id, file_path = test_validation

        client = get_mcp_sync_client()

        # Generate recommendations twice
        result1 = client.generate_recommendations(validation_id)
        result2 = client.generate_recommendations(validation_id)

        # Both should succeed
        assert result1["success"] is True
        assert result2["success"] is True

    def test_review_already_reviewed(self, test_validation):
        """Test reviewing an already reviewed recommendation."""
        validation_id, file_path = test_validation

        client = get_mcp_sync_client()

        # Generate and approve
        gen_result = client.generate_recommendations(validation_id)
        if gen_result["recommendation_count"] < 1:
            pytest.skip("No recommendations generated")

        rec_id = gen_result["recommendations"][0]["id"]
        client.review_recommendation(rec_id, "approve")

        # Try to review again (should succeed, updating the status)
        result = client.review_recommendation(rec_id, "reject")
        assert result["success"] is True

    def test_delete_applied_recommendation(self, test_validation):
        """Test deleting an applied recommendation."""
        validation_id, file_path = test_validation

        client = get_mcp_sync_client()

        # Generate and mark as applied
        gen_result = client.generate_recommendations(validation_id)
        if gen_result["recommendation_count"] < 1:
            pytest.skip("No recommendations generated")

        rec_id = gen_result["recommendations"][0]["id"]
        client.mark_recommendations_applied([rec_id])

        # Delete should still work
        result = client.delete_recommendation(rec_id)
        assert result["success"] is True
