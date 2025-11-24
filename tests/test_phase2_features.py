#!/usr/bin/env python3
"""
Tests for Phase 2 features:
- Re-validation with comparison
- Recommendation requirement configuration
- Database helpers for cron job
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

from core.database import db_manager, ValidationResult, Recommendation, RecommendationStatus, ValidationStatus
from agents.enhancement_agent import EnhancementAgent
from agents.base import agent_registry


class TestRevalidationComparison:
    """Tests for re-validation and comparison functionality."""

    @pytest.fixture
    def sample_validation_data(self):
        """Create sample validation data."""
        return {
            "file_path": "test_revalidation.md",
            "validation_results": {
                "issues": [
                    {"category": "spelling", "message": "Misspelled word 'teh'", "line": 1},
                    {"category": "grammar", "message": "Missing punctuation", "line": 2},
                    {"category": "style", "message": "Inconsistent heading style", "line": 5}
                ]
            },
            "validation_types": ["yaml", "markdown", "Truth"],
            "status": ValidationStatus.FAIL
        }

    @pytest.fixture
    def create_validation(self, sample_validation_data):
        """Helper to create a validation result."""
        def _create(**overrides):
            data = sample_validation_data.copy()
            data.update(overrides)

            result = ValidationResult(
                workflow_id="test-workflow",
                file_path=data["file_path"],
                validation_results=data["validation_results"],
                validation_types=data["validation_types"],
                status=data["status"]
            )

            with db_manager.get_session() as session:
                session.add(result)
                session.commit()
                session.refresh(result)
                validation_id = result.id

            return db_manager.get_validation_result(validation_id)

        return _create

    def test_parent_validation_link(self, create_validation):
        """Test linking re-validation to original validation."""
        # Create original validation
        original = create_validation()
        assert original is not None

        # Create re-validation
        revalidation = create_validation(
            file_path="test_revalidation_v2.md"
        )

        # Link to parent
        with db_manager.get_session() as session:
            result = session.query(ValidationResult).filter_by(id=revalidation.id).first()
            result.parent_validation_id = original.id
            session.commit()

        # Verify link was set
        revalidation_refreshed = db_manager.get_validation_result(revalidation.id)
        assert revalidation_refreshed.parent_validation_id == original.id

        # Verify we can query by parent
        with db_manager.get_session() as session:
            child = session.query(ValidationResult).filter_by(
                parent_validation_id=original.id
            ).first()
            assert child is not None
            assert child.id == revalidation.id

    def test_compare_validations_improvement(self, create_validation):
        """Test comparing validations with improvements."""
        # Create original validation with 3 issues
        original = create_validation()

        # Create improved validation with only 1 issue (2 resolved)
        improved = create_validation(
            file_path="test_improved.md",
            validation_results={
                "issues": [
                    {"category": "style", "message": "Inconsistent heading style", "line": 5}
                ]
            }
        )

        # Compare validations
        comparison = db_manager.compare_validations(original.id, improved.id)

        assert comparison["original_issues"] == 3
        assert comparison["new_issues"] == 1
        assert comparison["resolved_issues"] == 2
        assert comparison["new_issues_added"] == 0
        assert comparison["persistent_issues"] == 1
        assert comparison["improvement_score"] == pytest.approx(0.67, rel=0.01)

    def test_compare_validations_regression(self, create_validation):
        """Test comparing validations with regressions."""
        # Create original validation with 2 issues
        original = create_validation(
            validation_results={
                "issues": [
                    {"category": "spelling", "message": "Misspelled word 'teh'", "line": 1},
                    {"category": "grammar", "message": "Missing punctuation", "line": 2}
                ]
            }
        )

        # Create regressed validation with 3 issues (1 new issue added)
        regressed = create_validation(
            file_path="test_regressed.md",
            validation_results={
                "issues": [
                    {"category": "spelling", "message": "Misspelled word 'teh'", "line": 1},
                    {"category": "grammar", "message": "Missing punctuation", "line": 2},
                    {"category": "style", "message": "Bad formatting", "line": 10}
                ]
            }
        )

        # Compare validations
        comparison = db_manager.compare_validations(original.id, regressed.id)

        assert comparison["original_issues"] == 2
        assert comparison["new_issues"] == 3
        assert comparison["resolved_issues"] == 0
        assert comparison["new_issues_added"] == 1
        assert comparison["persistent_issues"] == 2
        assert comparison["improvement_score"] == 0.0

    def test_store_comparison_data(self, create_validation):
        """Test storing comparison data in validation result."""
        original = create_validation()
        improved = create_validation(file_path="test_improved.md")

        # Compare and store
        comparison = db_manager.compare_validations(original.id, improved.id)

        with db_manager.get_session() as session:
            result = session.query(ValidationResult).filter_by(id=improved.id).first()
            result.comparison_data = comparison
            session.commit()

        # Retrieve and verify
        retrieved = db_manager.get_validation_result(improved.id)
        assert retrieved.comparison_data is not None
        assert retrieved.comparison_data["original_validation_id"] == original.id
        assert "improvement_score" in retrieved.comparison_data


class TestRecommendationRequirements:
    """Tests for recommendation requirement configuration."""

    @pytest.fixture
    def enhancement_agent(self):
        """Get enhancement agent instance."""
        agent = agent_registry.get_agent("enhancement_agent")
        if agent is None:
            pytest.skip("Enhancement agent not available")
        return agent

    @pytest.fixture
    def validation_with_recommendations(self):
        """Create a validation with approved recommendations."""
        # Create validation
        validation = ValidationResult(
            workflow_id="test-workflow",
            file_path="test_enhancement.md",
            validation_results={"issues": []},
            status=ValidationStatus.PASS
        )

        with db_manager.get_session() as session:
            session.add(validation)
            session.commit()
            session.refresh(validation)
            validation_id = validation.id

        # Create approved recommendations
        rec1 = Recommendation(
            validation_id=validation_id,
            type="improvement",
            title="Test recommendation 1",
            description="Test recommendation 1 description",
            instruction="Fix 1",
            confidence=0.9,
            status=RecommendationStatus.APPROVED
        )
        rec2 = Recommendation(
            validation_id=validation_id,
            type="improvement",
            title="Test recommendation 2",
            description="Test recommendation 2 description",
            instruction="Fix 2",
            confidence=0.85,
            status=RecommendationStatus.APPROVED
        )

        with db_manager.get_session() as session:
            session.add(rec1)
            session.add(rec2)
            session.commit()

        return validation_id

    def test_load_enhancement_config(self, enhancement_agent):
        """Test loading enhancement configuration."""
        config = enhancement_agent._load_enhancement_config()

        assert isinstance(config, dict)
        assert "require_recommendations" in config
        assert "min_recommendations" in config
        assert "auto_generate_if_missing" in config
        assert "generation_timeout" in config

    @pytest.mark.asyncio
    async def test_check_requirements_met(self, enhancement_agent, validation_with_recommendations):
        """Test requirement check passes with sufficient recommendations."""
        # Should not raise with 2 approved recommendations
        await enhancement_agent._check_recommendation_requirements(
            validation_id=validation_with_recommendations,
            require_recommendations=True,
            min_recommendations=2
        )

    @pytest.mark.asyncio
    async def test_check_requirements_not_met(self, enhancement_agent, validation_with_recommendations):
        """Test requirement check fails with insufficient recommendations."""
        # Should raise ValueError with min 5 recommendations but only have 2
        with pytest.raises(ValueError) as exc_info:
            await enhancement_agent._check_recommendation_requirements(
                validation_id=validation_with_recommendations,
                require_recommendations=True,
                min_recommendations=5
            )

        assert "requires at least 5" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_check_requirements_disabled(self, enhancement_agent, validation_with_recommendations):
        """Test requirement check skipped when disabled."""
        # Should not raise even with high minimum when disabled
        await enhancement_agent._check_recommendation_requirements(
            validation_id=validation_with_recommendations,
            require_recommendations=False,
            min_recommendations=100
        )


class TestCronDatabaseHelpers:
    """Tests for database helper methods used by cron job."""

    @pytest.fixture
    def create_old_validation(self):
        """Create a validation that is old enough to be processed."""
        def _create(minutes_ago=10):
            validation = ValidationResult(
                workflow_id="test-workflow",
                file_path=f"test_old_{minutes_ago}.md",
                validation_results={"issues": []},
                status=ValidationStatus.PASS,
                created_at=datetime.utcnow() - timedelta(minutes=minutes_ago)
            )

            with db_manager.get_session() as session:
                session.add(validation)
                session.commit()
                session.refresh(validation)
                validation_id = validation.id

            return db_manager.get_validation_result(validation_id)

        return _create

    def test_get_validations_without_recommendations_age_filter(self, create_old_validation):
        """Test age filtering for validations without recommendations."""
        # Create recent validation (2 minutes old)
        recent = create_old_validation(minutes_ago=2)

        # Create old validation (10 minutes old)
        old = create_old_validation(minutes_ago=10)

        # Query with min_age_minutes=5 should only return old one
        results = db_manager.get_validations_without_recommendations(
            min_age_minutes=5,
            limit=100
        )

        result_ids = [r.id for r in results]
        assert old.id in result_ids
        assert recent.id not in result_ids

    def test_get_validations_without_recommendations_excludes_with_recs(self, create_old_validation):
        """Test that validations with recommendations are excluded."""
        # Create validation without recommendations
        without_rec = create_old_validation(minutes_ago=10)

        # Create validation with recommendation
        with_rec = create_old_validation(minutes_ago=10)
        rec = Recommendation(
            validation_id=with_rec.id,
            type="test",
            title="Test recommendation",
            description="Test description",
            instruction="Fix",
            confidence=0.9,
            status=RecommendationStatus.PENDING
        )
        with db_manager.get_session() as session:
            session.add(rec)
            session.commit()

        # Query should only return validation without recommendations
        results = db_manager.get_validations_without_recommendations(
            min_age_minutes=5,
            limit=100
        )

        result_ids = [r.id for r in results]
        assert without_rec.id in result_ids
        assert with_rec.id not in result_ids

    def test_get_validations_without_recommendations_limit(self, create_old_validation):
        """Test batch size limit for validations query."""
        # Create 5 old validations without recommendations
        for i in range(5):
            create_old_validation(minutes_ago=10)

        # Query with limit=3 should return only 3
        results = db_manager.get_validations_without_recommendations(
            min_age_minutes=5,
            limit=3
        )

        assert len(results) <= 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
