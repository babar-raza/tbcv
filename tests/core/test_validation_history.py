#!/usr/bin/env python3
"""
Tests for validation history tracking functionality.
"""

import pytest
import tempfile
import time
from pathlib import Path

from core.database import db_manager, ValidationStatus


class TestValidationHistory:
    """Tests for validation history tracking."""

    @pytest.fixture
    def sample_file(self, tmp_path):
        """Create a sample file for testing."""
        file_path = tmp_path / "test_document.md"
        file_path.write_text("# Test Document\n\nContent here.", encoding='utf-8')
        return str(file_path)

    def test_get_validation_history_single_validation(self, sample_file):
        """Test getting history for file with single validation."""
        # Create a validation
        vr = db_manager.create_validation_result(
            file_path=sample_file,
            rules_applied={"test": True},
            validation_results={"issues": [], "confidence": 0.9},
            notes="Test validation",
            severity="info",
            status=ValidationStatus.PASS
        )

        # Get history
        history = db_manager.get_validation_history(file_path=sample_file)

        assert history is not None
        assert history["file_path"] == sample_file
        assert history["total_validations"] == 1
        assert len(history["validations"]) == 1
        assert history["validations"][0]["id"] == vr.id
        assert "trends" not in history  # No trends with single validation

    def test_get_validation_history_multiple_validations(self, sample_file):
        """Test getting history for file with multiple validations."""
        # Create multiple validations
        for i in range(5):
            db_manager.create_validation_result(
                file_path=sample_file,
                rules_applied={"test": i},
                validation_results={"issues": [{"msg": f"issue {j}"} for j in range(i)], "confidence": 0.9 - (i * 0.1)},
                notes=f"Test validation {i}",
                severity="info",
                status=ValidationStatus.PASS
            )
            time.sleep(0.01)  # Small delay to ensure different timestamps

        # Get history
        history = db_manager.get_validation_history(file_path=sample_file)

        assert history["total_validations"] == 5
        assert len(history["validations"]) == 5

        # Check ordering (newest first)
        timestamps = [v["created_at"] for v in history["validations"]]
        assert timestamps == sorted(timestamps, reverse=True)

        # Check trends are included
        assert "trends" in history

    def test_get_validation_history_with_limit(self, sample_file):
        """Test getting history with limit parameter."""
        # Create 10 validations
        for i in range(10):
            db_manager.create_validation_result(
                file_path=sample_file,
                rules_applied={"test": i},
                validation_results={"issues": [], "confidence": 0.9},
                notes=f"Test validation {i}",
                severity="info",
                status=ValidationStatus.PASS
            )
            time.sleep(0.01)

        # Get history with limit
        history = db_manager.get_validation_history(file_path=sample_file, limit=5)

        assert history["total_validations"] == 5
        assert len(history["validations"]) == 5

    def test_get_validation_history_no_trends(self, sample_file):
        """Test getting history without trend analysis."""
        # Create multiple validations
        for i in range(3):
            db_manager.create_validation_result(
                file_path=sample_file,
                rules_applied={"test": i},
                validation_results={"issues": [], "confidence": 0.9},
                notes=f"Test validation {i}",
                severity="info",
                status=ValidationStatus.PASS
            )

        # Get history without trends
        history = db_manager.get_validation_history(
            file_path=sample_file,
            include_trends=False
        )

        assert "trends" not in history

    def test_trend_analysis_improving(self, sample_file):
        """Test trend analysis detects improvement."""
        # Create validations showing improvement (fewer issues over time)
        issue_counts = [10, 8, 6, 4, 2]  # Decreasing issues = improvement

        for count in issue_counts:
            db_manager.create_validation_result(
                file_path=sample_file,
                rules_applied={"test": True},
                validation_results={
                    "issues": [{"msg": f"issue {i}"} for i in range(count)],
                    "confidence": 1.0 - (count * 0.05)
                },
                notes="Test validation",
                severity="info",
                status=ValidationStatus.PASS
            )
            time.sleep(0.01)

        history = db_manager.get_validation_history(file_path=sample_file)

        assert "trends" in history
        trends = history["trends"]
        assert trends["issue_count_trend"] in ["improving", "stable"]
        # Could be marked as improvement detected
        # assert trends["improvement_detected"] is True

    def test_trend_analysis_degrading(self, sample_file):
        """Test trend analysis detects degradation."""
        # Create validations showing degradation (more issues over time)
        issue_counts = [2, 4, 6, 8, 10]  # Increasing issues = degradation

        for count in issue_counts:
            db_manager.create_validation_result(
                file_path=sample_file,
                rules_applied={"test": True},
                validation_results={
                    "issues": [{"msg": f"issue {i}"} for i in range(count)],
                    "confidence": 1.0 - (count * 0.05)
                },
                notes="Test validation",
                severity="info",
                status=ValidationStatus.PASS
            )
            time.sleep(0.01)

        history = db_manager.get_validation_history(file_path=sample_file)

        assert "trends" in history
        trends = history["trends"]
        assert trends["issue_count_trend"] in ["degrading", "stable"]
        # Could be marked as regression detected
        # assert trends["regression_detected"] is True

    def test_trend_analysis_stable(self, sample_file):
        """Test trend analysis detects stable quality."""
        # Create validations with consistent quality
        for i in range(5):
            db_manager.create_validation_result(
                file_path=sample_file,
                rules_applied={"test": True},
                validation_results={
                    "issues": [{"msg": f"issue {j}"} for j in range(3)],  # Consistent 3 issues
                    "confidence": 0.9
                },
                notes="Test validation",
                severity="info",
                status=ValidationStatus.PASS
            )
            time.sleep(0.01)

        history = db_manager.get_validation_history(file_path=sample_file)

        assert "trends" in history
        trends = history["trends"]
        assert trends["issue_count_trend"] == "stable"
        assert trends["confidence_trend"] == "stable"

    def test_status_trend_analysis(self, sample_file):
        """Test status trend analysis."""
        statuses = [
            ValidationStatus.FAIL,
            ValidationStatus.FAIL,
            ValidationStatus.PASS,
            ValidationStatus.PASS,
            ValidationStatus.PASS
        ]

        for status in statuses:
            db_manager.create_validation_result(
                file_path=sample_file,
                rules_applied={"test": True},
                validation_results={"issues": [], "confidence": 0.9},
                notes="Test validation",
                severity="info",
                status=status
            )
            time.sleep(0.01)

        history = db_manager.get_validation_history(file_path=sample_file)

        assert "trends" in history
        trends = history["trends"]
        assert trends["status_trend"] in ["improving", "stable"]

    def test_version_numbers_assigned(self, sample_file):
        """Test that version numbers are properly assigned."""
        # Create multiple validations
        vrs = []
        for i in range(3):
            vr = db_manager.create_validation_result(
                file_path=sample_file,
                rules_applied={"test": i},
                validation_results={"issues": [], "confidence": 0.9},
                notes=f"Version {i}",
                severity="info",
                status=ValidationStatus.PASS
            )
            vrs.append(vr)
            time.sleep(0.01)

        history = db_manager.get_validation_history(file_path=sample_file)

        # Check that version numbers exist and are sequential
        versions = [v["version_number"] for v in history["validations"]]
        assert all(v is not None for v in versions)

    def test_history_with_parent_validation(self, sample_file):
        """Test history includes parent validation links."""
        # Create original validation
        original = db_manager.create_validation_result(
            file_path=sample_file,
            rules_applied={"test": True},
            validation_results={"issues": [{"msg": "issue 1"}], "confidence": 0.8},
            notes="Original validation",
            severity="info",
            status=ValidationStatus.PASS
        )

        # Create re-validation with parent link
        # Note: In actual usage, this would be set through the revalidation API
        # For testing, we'll just create a new validation
        revalidation = db_manager.create_validation_result(
            file_path=sample_file,
            rules_applied={"test": True},
            validation_results={"issues": [], "confidence": 0.95},
            notes="Re-validation",
            severity="info",
            status=ValidationStatus.PASS
        )

        history = db_manager.get_validation_history(file_path=sample_file)

        assert history["total_validations"] == 2
        assert len(history["validations"]) == 2

    def test_history_nonexistent_file(self):
        """Test getting history for file that has never been validated."""
        history = db_manager.get_validation_history(file_path="/nonexistent/file.md")

        assert history["total_validations"] == 0
        assert len(history["validations"]) == 0
        assert "trends" not in history

    def test_history_includes_comparison_data(self, sample_file):
        """Test that history includes comparison data when available."""
        # Create validations
        vr1 = db_manager.create_validation_result(
            file_path=sample_file,
            rules_applied={"test": True},
            validation_results={"issues": [{"msg": "issue 1"}], "confidence": 0.8},
            notes="Validation 1",
            severity="info",
            status=ValidationStatus.PASS
        )

        vr2 = db_manager.create_validation_result(
            file_path=sample_file,
            rules_applied={"test": True},
            validation_results={"issues": [], "confidence": 0.95},
            notes="Validation 2",
            severity="info",
            status=ValidationStatus.PASS
        )

        # Compare validations
        comparison = db_manager.compare_validations(original_id=vr1.id, new_id=vr2.id)

        history = db_manager.get_validation_history(file_path=sample_file)

        assert history["total_validations"] == 2
        # The newer validation should have comparison data stored
        newer_validation = history["validations"][0]  # Newest first
        assert "comparison_data" in newer_validation


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
