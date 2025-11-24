#!/usr/bin/env python3
"""
Tests for recommendation confidence scoring functionality.
"""

import pytest
from core.database import db_manager, ValidationStatus, RecommendationStatus


class TestConfidenceScoring:
    """Tests for multi-factor confidence scoring."""

    def test_calculate_confidence_all_factors_high(self):
        """Test confidence calculation with all high-quality factors."""
        confidence_data = db_manager.calculate_recommendation_confidence(
            issue_severity="critical",
            recommendation_type="link_plugin",
            has_original_content=True,
            has_proposed_content=True,
            has_diff=True,
            has_rationale=True,
            validation_confidence=0.95
        )

        assert confidence_data is not None
        assert "confidence" in confidence_data
        assert "factors" in confidence_data
        assert "explanation" in confidence_data

        # With all high factors, should have very high confidence
        assert confidence_data["confidence"] >= 0.8

        # Check factors are present
        factors = confidence_data["factors"]
        assert "severity" in factors
        assert "completeness" in factors
        assert "validation_confidence" in factors
        assert "type_specificity" in factors
        assert "additional" in factors

    def test_calculate_confidence_minimal_factors(self):
        """Test confidence calculation with minimal factors."""
        confidence_data = db_manager.calculate_recommendation_confidence(
            issue_severity="low",
            recommendation_type="info",
            has_original_content=False,
            has_proposed_content=False,
            has_diff=False,
            has_rationale=False,
            validation_confidence=0.5
        )

        assert confidence_data["confidence"] >= 0.0
        assert confidence_data["confidence"] <= 1.0

        # With minimal factors, confidence should be low
        assert confidence_data["confidence"] < 0.5

    def test_calculate_confidence_medium_factors(self):
        """Test confidence calculation with medium-quality factors."""
        confidence_data = db_manager.calculate_recommendation_confidence(
            issue_severity="medium",
            recommendation_type="fix_format",
            has_original_content=True,
            has_proposed_content=True,
            has_diff=False,
            has_rationale=True,
            validation_confidence=0.75
        )

        # Should be in moderate range
        assert 0.5 <= confidence_data["confidence"] <= 0.85

    def test_confidence_capped_at_one(self):
        """Test that confidence score is capped at 1.0."""
        confidence_data = db_manager.calculate_recommendation_confidence(
            issue_severity="critical",
            recommendation_type="link_plugin",
            has_original_content=True,
            has_proposed_content=True,
            has_diff=True,
            has_rationale=True,
            validation_confidence=1.0,
            additional_factors={"custom1": 0.5, "custom2": 0.5}  # Try to exceed 1.0
        )

        assert confidence_data["confidence"] <= 1.0

    def test_severity_factor_scoring(self):
        """Test that severity affects confidence score appropriately."""
        critical = db_manager.calculate_recommendation_confidence(
            issue_severity="critical",
            recommendation_type="fix_format",
            validation_confidence=0.8
        )

        low = db_manager.calculate_recommendation_confidence(
            issue_severity="low",
            recommendation_type="fix_format",
            validation_confidence=0.8
        )

        # Critical severity should contribute more to confidence
        assert critical["factors"]["severity"] > low["factors"]["severity"]

    def test_completeness_factor_scoring(self):
        """Test that completeness affects confidence score."""
        complete = db_manager.calculate_recommendation_confidence(
            issue_severity="medium",
            recommendation_type="fix_format",
            has_original_content=True,
            has_proposed_content=True,
            has_diff=True,
            has_rationale=True,
            validation_confidence=0.8
        )

        incomplete = db_manager.calculate_recommendation_confidence(
            issue_severity="medium",
            recommendation_type="fix_format",
            has_original_content=False,
            has_proposed_content=False,
            has_diff=False,
            has_rationale=False,
            validation_confidence=0.8
        )

        assert complete["factors"]["completeness"] > incomplete["factors"]["completeness"]
        assert complete["confidence"] > incomplete["confidence"]

    def test_explanation_generation_high_confidence(self):
        """Test explanation for high confidence recommendations."""
        confidence_data = db_manager.calculate_recommendation_confidence(
            issue_severity="critical",
            recommendation_type="link_plugin",
            has_original_content=True,
            has_proposed_content=True,
            has_diff=True,
            has_rationale=True,
            validation_confidence=0.95
        )

        explanation = confidence_data["explanation"]
        assert explanation is not None
        assert len(explanation) > 0

        # High confidence should be mentioned
        assert "high confidence" in explanation.lower() or "very high" in explanation.lower()

    def test_explanation_generation_low_confidence(self):
        """Test explanation for low confidence recommendations."""
        confidence_data = db_manager.calculate_recommendation_confidence(
            issue_severity="low",
            recommendation_type="info",
            has_original_content=False,
            has_proposed_content=False,
            validation_confidence=0.3
        )

        explanation = confidence_data["explanation"]
        assert explanation is not None
        assert "low confidence" in explanation.lower()

    def test_update_recommendation_confidence(self, tmp_path):
        """Test updating a recommendation's confidence."""
        # Create a validation
        file_path = tmp_path / "test.md"
        file_path.write_text("# Test", encoding='utf-8')

        vr = db_manager.create_validation_result(
            file_path=str(file_path),
            rules_applied={"test": True},
            validation_results={"issues": [], "confidence": 0.9},
            notes="Test",
            severity="info",
            status=ValidationStatus.PASS
        )

        # Create a recommendation
        rec = db_manager.create_recommendation(
            validation_id=vr.id,
            type="fix_format",
            title="Test recommendation",
            description="Test description",
            confidence=0.5  # Initial confidence
        )

        # Calculate new confidence
        confidence_data = db_manager.calculate_recommendation_confidence(
            issue_severity="high",
            recommendation_type="fix_format",
            has_original_content=True,
            has_proposed_content=True,
            has_diff=True,
            validation_confidence=0.9
        )

        # Update the recommendation
        updated_rec = db_manager.update_recommendation_confidence(
            recommendation_id=rec.id,
            confidence_data=confidence_data
        )

        assert updated_rec is not None
        assert updated_rec.confidence == confidence_data["confidence"]
        assert updated_rec.confidence != 0.5  # Changed from initial

        # Check that breakdown is stored in metadata
        assert updated_rec.recommendation_metadata is not None
        assert "confidence_breakdown" in updated_rec.recommendation_metadata

        breakdown = updated_rec.recommendation_metadata["confidence_breakdown"]
        assert "confidence" in breakdown
        assert "factors" in breakdown
        assert "explanation" in breakdown

    def test_confidence_breakdown_in_metadata(self, tmp_path):
        """Test that confidence breakdown is properly stored and retrievable."""
        # Create validation
        file_path = tmp_path / "test.md"
        file_path.write_text("# Test", encoding='utf-8')

        vr = db_manager.create_validation_result(
            file_path=str(file_path),
            rules_applied={"test": True},
            validation_results={"issues": [], "confidence": 0.9},
            notes="Test",
            severity="info",
            status=ValidationStatus.PASS
        )

        # Create recommendation
        rec = db_manager.create_recommendation(
            validation_id=vr.id,
            type="fix_format",
            title="Test",
            description="Test"
        )

        # Calculate and update confidence
        confidence_data = db_manager.calculate_recommendation_confidence(
            issue_severity="critical",
            recommendation_type="fix_format",
            has_proposed_content=True,
            validation_confidence=0.9
        )

        db_manager.update_recommendation_confidence(
            recommendation_id=rec.id,
            confidence_data=confidence_data
        )

        # Retrieve and verify
        retrieved_rec = db_manager.get_recommendation(rec.id)
        assert retrieved_rec is not None

        breakdown = retrieved_rec.recommendation_metadata.get("confidence_breakdown")
        assert breakdown is not None
        assert breakdown["confidence"] == confidence_data["confidence"]
        assert breakdown["factors"] == confidence_data["factors"]
        assert breakdown["explanation"] == confidence_data["explanation"]

    def test_additional_factors(self):
        """Test that additional custom factors are included correctly."""
        confidence_data = db_manager.calculate_recommendation_confidence(
            issue_severity="medium",
            recommendation_type="fix_format",
            validation_confidence=0.8,
            additional_factors={
                "user_feedback": 0.03,
                "historical_accuracy": 0.04,
                "complexity": 0.02
            }
        )

        assert "additional" in confidence_data["factors"]
        # Additional factors should be capped appropriately
        assert confidence_data["factors"]["additional"] <= 0.2

    def test_type_specificity_mapping(self):
        """Test that recommendation types are mapped correctly."""
        link_plugin = db_manager.calculate_recommendation_confidence(
            issue_severity="medium",
            recommendation_type="link_plugin",  # Should map to fix_specific
            validation_confidence=0.8
        )

        content_improvement = db_manager.calculate_recommendation_confidence(
            issue_severity="medium",
            recommendation_type="content_improvement",  # Should map to enhancement
            validation_confidence=0.8
        )

        # link_plugin (fix_specific) should have higher type specificity than content_improvement (enhancement)
        assert link_plugin["factors"]["type_specificity"] > content_improvement["factors"]["type_specificity"]

    def test_validation_confidence_contribution(self):
        """Test that validation confidence contributes to overall score."""
        high_validation = db_manager.calculate_recommendation_confidence(
            issue_severity="medium",
            recommendation_type="fix_format",
            validation_confidence=0.95
        )

        low_validation = db_manager.calculate_recommendation_confidence(
            issue_severity="medium",
            recommendation_type="fix_format",
            validation_confidence=0.4
        )

        assert high_validation["factors"]["validation_confidence"] > low_validation["factors"]["validation_confidence"]
        assert high_validation["confidence"] > low_validation["confidence"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
