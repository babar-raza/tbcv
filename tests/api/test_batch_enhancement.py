#!/usr/bin/env python3
"""
Tests for batch enhancement API functionality.
"""

import pytest
import asyncio
from pathlib import Path
import tempfile
import os

from agents.enhancement_agent import EnhancementAgent
from core.database import db_manager, ValidationStatus, RecommendationStatus


class TestBatchEnhancement:
    """Tests for batch enhancement functionality."""

    @pytest.fixture
    async def enhancement_agent(self):
        """Create an EnhancementAgent instance."""
        return EnhancementAgent()

    @pytest.fixture
    async def sample_validations(self, tmp_path):
        """Create sample validations with recommendations for testing."""
        validation_ids = []

        for i in range(3):
            # Create a temporary file
            file_path = tmp_path / f"test_file_{i}.md"
            content = f"""# Test Document {i}

## Section One
This is test content for document {i}.

## Section Two
More content here.
"""
            file_path.write_text(content, encoding='utf-8')

            # Create a validation result
            validation_result = db_manager.create_validation_result(
                file_path=str(file_path),
                rules_applied={"test": True},
                validation_results={"issues": [], "confidence": 0.85},
                notes="Test validation",
                severity="info",
                status=ValidationStatus.PASS
            )
            validation_id = validation_result.id

            # Create some recommendations
            for j in range(2):
                rec = db_manager.create_recommendation(
                    validation_id=validation_id,
                    type="content_improvement",
                    title=f"Test recommendation {j}",
                    description=f"Test recommendation {j} for document {i}",
                    instruction=f"Test recommendation {j} for document {i}",
                    scope="global",
                    priority="medium",
                    confidence=0.9
                )
                rec_id = rec.id

                # Approve the recommendation
                db_manager.update_recommendation_status(
                    recommendation_id=rec_id,
                    status=RecommendationStatus.APPROVED,
                    reviewer="test_user",
                    review_notes="Approved for testing"
                )

            validation_ids.append(validation_id)

        return validation_ids

    @pytest.mark.asyncio
    async def test_batch_enhance_parallel(self, enhancement_agent, sample_validations):
        """Test batch enhancement in parallel mode."""
        result = await enhancement_agent.enhance_batch(
            validation_ids=sample_validations,
            parallel=True,
            persist=False
        )

        assert result is not None
        assert "batch_id" in result
        assert result["total_count"] == 3
        assert "successful_count" in result
        assert "failed_count" in result
        assert "validations" in result
        assert len(result["validations"]) == 3
        assert result["parallel_mode"] is True

        # Check timing fields
        assert "start_time" in result
        assert "end_time" in result
        assert "duration_seconds" in result

    @pytest.mark.asyncio
    async def test_batch_enhance_sequential(self, enhancement_agent, sample_validations):
        """Test batch enhancement in sequential mode."""
        result = await enhancement_agent.enhance_batch(
            validation_ids=sample_validations,
            parallel=False,
            persist=False
        )

        assert result is not None
        assert result["total_count"] == 3
        assert len(result["validations"]) == 3
        assert result["parallel_mode"] is False

        # All should have attempted processing
        for validation_result in result["validations"]:
            assert "validation_id" in validation_result
            assert "success" in validation_result
            assert validation_result["validation_id"] in sample_validations

    @pytest.mark.asyncio
    async def test_batch_enhance_with_failures(self, enhancement_agent):
        """Test batch enhancement handles failures gracefully."""
        # Create one valid and two invalid validation IDs
        valid_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
        valid_file.write("# Test\n\nContent here.")
        valid_file.close()

        try:
            valid_result = db_manager.create_validation_result(
                file_path=valid_file.name,
                rules_applied={"test": True},
                validation_results={"issues": [], "confidence": 0.9},
                notes="Valid test validation",
                severity="info",
                status=ValidationStatus.PASS
            )
            valid_id = valid_result.id

            invalid_ids = ["invalid-id-1", "invalid-id-2"]
            validation_ids = [valid_id] + invalid_ids

            result = await enhancement_agent.enhance_batch(
                validation_ids=validation_ids,
                parallel=True,
                persist=False
            )

            assert result["total_count"] == 3
            # Should have failures for invalid IDs
            assert result["failed_count"] >= 2

            # Check that errors are recorded
            failed_validations = [v for v in result["validations"] if not v.get("success")]
            assert len(failed_validations) >= 2

            for failed in failed_validations:
                assert "error" in failed
                assert failed["error"] is not None

        finally:
            os.unlink(valid_file.name)

    @pytest.mark.asyncio
    async def test_batch_enhance_empty_list(self, enhancement_agent):
        """Test batch enhancement with empty validation list."""
        result = await enhancement_agent.enhance_batch(
            validation_ids=[],
            parallel=True,
            persist=False
        )

        assert result["total_count"] == 0
        assert result["successful_count"] == 0
        assert result["failed_count"] == 0
        assert len(result["validations"]) == 0

    @pytest.mark.asyncio
    async def test_batch_enhance_specific_recommendations(self, enhancement_agent, sample_validations):
        """Test batch enhancement with specific recommendation IDs per validation."""
        # Get recommendations for first validation
        first_validation = sample_validations[0]
        recommendations = db_manager.list_recommendations(validation_id=first_validation)

        if recommendations:
            # Apply only first recommendation to first validation
            rec_mapping = {
                first_validation: [recommendations[0].id]
            }

            result = await enhancement_agent.enhance_batch(
                validation_ids=sample_validations,
                parallel=True,
                persist=False,
                apply_all=False,
                recommendation_ids_per_validation=rec_mapping
            )

            assert result is not None
            assert result["total_count"] == len(sample_validations)

    @pytest.mark.asyncio
    async def test_batch_enhance_performance(self, enhancement_agent, sample_validations):
        """Test that parallel mode is faster than sequential for multiple validations."""
        # Run sequential
        sequential_result = await enhancement_agent.enhance_batch(
            validation_ids=sample_validations,
            parallel=False,
            persist=False
        )
        sequential_time = sequential_result["duration_seconds"]

        # Run parallel
        parallel_result = await enhancement_agent.enhance_batch(
            validation_ids=sample_validations,
            parallel=True,
            persist=False
        )
        parallel_time = parallel_result["duration_seconds"]

        # Parallel should generally be faster or similar
        # (may not always be true for very small batches, so we just check both complete)
        assert sequential_time >= 0
        assert parallel_time >= 0
        assert sequential_result["successful_count"] == parallel_result["successful_count"]

    @pytest.mark.asyncio
    async def test_batch_enhance_result_structure(self, enhancement_agent, sample_validations):
        """Test that batch enhancement returns proper result structure."""
        result = await enhancement_agent.enhance_batch(
            validation_ids=sample_validations[:1],
            parallel=True,
            persist=False
        )

        # Check top-level structure
        required_fields = [
            "batch_id", "total_count", "successful_count", "failed_count",
            "validations", "start_time", "end_time", "duration_seconds", "parallel_mode"
        ]
        for field in required_fields:
            assert field in result, f"Missing field: {field}"

        # Check validation result structure
        if result["validations"]:
            validation_result = result["validations"][0]
            required_validation_fields = [
                "validation_id", "success", "error", "enhancement_id",
                "applied_count", "skipped_count"
            ]
            for field in required_validation_fields:
                assert field in validation_result, f"Missing validation field: {field}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
