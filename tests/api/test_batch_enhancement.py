#!/usr/bin/env python3
"""
Tests for batch enhancement API functionality.
"""

import pytest
import tempfile
import os

from agents.enhancement_agent import EnhancementAgent
from core.database import db_manager, ValidationStatus, RecommendationStatus


class TestBatchEnhancement:
    """Tests for batch enhancement functionality."""

    @pytest.fixture
    def enhancement_agent(self):
        """Create an EnhancementAgent instance."""
        return EnhancementAgent()

    @pytest.fixture
    def sample_validations(self, tmp_path):
        """Create sample validations with recommendations for testing."""
        db_manager.init_database()
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
                rules_applied=["test"],
                validation_results={"issues": [], "confidence": 0.85},
                notes="Test validation",
                severity="info",
                status="pass"
            )
            validation_id = validation_result.id

            # Create some recommendations
            for j in range(2):
                rec = db_manager.create_recommendation(
                    validation_id=validation_id,
                    type="content_improvement",
                    title=f"Test recommendation {j}",
                    description=f"Test recommendation {j} for document {i}",
                    scope="global",
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
            parallel=True
        )

        assert result is not None
        assert result["success"] is True
        assert result["processed"] == 3
        assert "results" in result
        assert len(result["results"]) == 3

    @pytest.mark.asyncio
    async def test_batch_enhance_sequential(self, enhancement_agent, sample_validations):
        """Test batch enhancement in sequential mode."""
        result = await enhancement_agent.enhance_batch(
            validation_ids=sample_validations,
            parallel=False
        )

        assert result is not None
        assert result["success"] is True
        assert result["processed"] == 3
        assert len(result["results"]) == 3

        # All should have attempted processing
        for validation_result in result["results"]:
            assert "validation_id" in validation_result
            assert "success" in validation_result
            assert validation_result["validation_id"] in sample_validations

    @pytest.mark.asyncio
    async def test_batch_enhance_with_failures(self, enhancement_agent):
        """Test batch enhancement handles failures gracefully."""
        db_manager.init_database()

        # Create one valid and two invalid validation IDs
        valid_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
        valid_file.write("# Test\n\nContent here.")
        valid_file.close()

        try:
            valid_result = db_manager.create_validation_result(
                file_path=valid_file.name,
                rules_applied=["test"],
                validation_results={"issues": [], "confidence": 0.9},
                notes="Valid test validation",
                severity="info",
                status="pass"
            )
            valid_id = valid_result.id

            invalid_ids = ["invalid-id-1", "invalid-id-2"]
            validation_ids = [valid_id] + invalid_ids

            result = await enhancement_agent.enhance_batch(
                validation_ids=validation_ids,
                parallel=True
            )

            assert result["processed"] == 3
            # Check that all validation IDs were processed
            assert len(result["results"]) == 3

        finally:
            os.unlink(valid_file.name)

    @pytest.mark.asyncio
    async def test_batch_enhance_empty_list(self, enhancement_agent):
        """Test batch enhancement with empty validation list."""
        result = await enhancement_agent.enhance_batch(
            validation_ids=[],
            parallel=True
        )

        assert result["success"] is True
        assert result["processed"] == 0
        assert len(result["results"]) == 0

    @pytest.mark.asyncio
    async def test_batch_enhance_specific_recommendations(self, enhancement_agent, sample_validations):
        """Test batch enhancement processes validations correctly."""
        result = await enhancement_agent.enhance_batch(
            validation_ids=sample_validations[:1],
            parallel=True
        )

        assert result is not None
        assert result["processed"] == 1

    @pytest.mark.asyncio
    async def test_batch_enhance_performance(self, enhancement_agent, sample_validations):
        """Test that both parallel and sequential modes complete successfully."""
        # Run sequential
        sequential_result = await enhancement_agent.enhance_batch(
            validation_ids=sample_validations,
            parallel=False
        )

        # Run parallel
        parallel_result = await enhancement_agent.enhance_batch(
            validation_ids=sample_validations,
            parallel=True
        )

        # Both should complete successfully
        assert sequential_result["success"] is True
        assert parallel_result["success"] is True
        assert sequential_result["processed"] == parallel_result["processed"]

    @pytest.mark.asyncio
    async def test_batch_enhance_result_structure(self, enhancement_agent, sample_validations):
        """Test that batch enhancement returns proper result structure."""
        result = await enhancement_agent.enhance_batch(
            validation_ids=sample_validations[:1],
            parallel=True
        )

        # Check top-level structure
        required_fields = ["success", "processed", "results"]
        for field in required_fields:
            assert field in result, f"Missing field: {field}"

        # Check validation result structure
        if result["results"]:
            validation_result = result["results"][0]
            required_validation_fields = ["validation_id", "success"]
            for field in required_validation_fields:
                assert field in validation_result, f"Missing validation field: {field}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
