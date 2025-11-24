# tests/api/services/test_status_recalculator.py
"""
Unit tests for api/services/status_recalculator.py - Status recalculation service.
Target coverage: 100% (Currently 0%)
"""
import pytest
from unittest.mock import MagicMock, patch
from typing import List, Dict, Any

from api.services.status_recalculator import (
    recalculate_validation_status,
    recalculate_workflow_status,
    on_recommendation_updated
)
from core.database import ValidationStatus, WorkflowState


@pytest.mark.unit
class TestRecalculateValidationStatus:
    """Test recalculate_validation_status function."""

    def test_validation_not_found_returns_none(self):
        """Test that non-existent validation returns None."""
        mock_db = MagicMock()
        mock_db.get_validation_result.return_value = None

        with patch('api.services.status_recalculator.db_manager', mock_db):
            result = recalculate_validation_status("nonexistent_id")

            assert result is None
            mock_db.get_validation_result.assert_called_once_with("nonexistent_id")

    def test_validation_with_applied_recommendations(self):
        """Test validation status becomes ENHANCED when recommendations are applied."""
        mock_validation = MagicMock()
        mock_validation.status = ValidationStatus.PASS

        mock_rec1 = MagicMock()
        mock_rec1.status.value = "applied"
        mock_rec2 = MagicMock()
        mock_rec2.status.value = "pending"

        mock_db = MagicMock()
        mock_db.get_validation_result.return_value = mock_validation
        mock_db.list_recommendations.return_value = [mock_rec1, mock_rec2]

        with patch('api.services.status_recalculator.db_manager', mock_db):
            result = recalculate_validation_status("val_123")

            assert result == "enhanced"
            assert mock_validation.status == ValidationStatus.ENHANCED
            mock_db.session.commit.assert_called_once()

    def test_validation_with_accepted_recommendations(self):
        """Test validation status becomes APPROVED when recommendations are accepted."""
        mock_validation = MagicMock()
        mock_validation.status = ValidationStatus.PASS

        mock_rec1 = MagicMock()
        mock_rec1.status.value = "accepted"
        mock_rec2 = MagicMock()
        mock_rec2.status.value = "pending"

        mock_db = MagicMock()
        mock_db.get_validation_result.return_value = mock_validation
        mock_db.list_recommendations.return_value = [mock_rec1, mock_rec2]

        with patch('api.services.status_recalculator.db_manager', mock_db):
            result = recalculate_validation_status("val_123")

            assert result == "approved"
            assert mock_validation.status == ValidationStatus.APPROVED
            mock_db.session.commit.assert_called_once()

    def test_validation_with_all_rejected_recommendations(self):
        """Test validation status becomes REJECTED when all recommendations rejected."""
        mock_validation = MagicMock()
        mock_validation.status = ValidationStatus.PASS

        mock_rec1 = MagicMock()
        mock_rec1.status.value = "rejected"
        mock_rec2 = MagicMock()
        mock_rec2.status.value = "rejected"

        mock_db = MagicMock()
        mock_db.get_validation_result.return_value = mock_validation
        mock_db.list_recommendations.return_value = [mock_rec1, mock_rec2]

        with patch('api.services.status_recalculator.db_manager', mock_db):
            result = recalculate_validation_status("val_123")

            assert result == "rejected"
            assert mock_validation.status == ValidationStatus.REJECTED
            mock_db.session.commit.assert_called_once()

    def test_validation_with_pending_recommendations_keeps_status(self):
        """Test validation keeps current status when only pending recommendations."""
        mock_validation = MagicMock()
        # Create a mock status object that behaves like an enum
        mock_status = MagicMock()
        mock_status.value = "warning"
        mock_validation.status = mock_status

        mock_rec1 = MagicMock()
        mock_rec1.status.value = "pending"
        mock_rec2 = MagicMock()
        mock_rec2.status.value = "pending"

        mock_db = MagicMock()
        mock_db.get_validation_result.return_value = mock_validation
        mock_db.list_recommendations.return_value = [mock_rec1, mock_rec2]

        with patch('api.services.status_recalculator.db_manager', mock_db):
            result = recalculate_validation_status("val_123")

            # Should return current status without changing it
            assert result == "warning"

    def test_validation_priority_applied_over_accepted(self):
        """Test that applied recommendations have priority over accepted."""
        mock_validation = MagicMock()
        mock_validation.status = ValidationStatus.PASS

        mock_rec1 = MagicMock()
        mock_rec1.status.value = "applied"
        mock_rec2 = MagicMock()
        mock_rec2.status.value = "accepted"

        mock_db = MagicMock()
        mock_db.get_validation_result.return_value = mock_validation
        mock_db.list_recommendations.return_value = [mock_rec1, mock_rec2]

        with patch('api.services.status_recalculator.db_manager', mock_db):
            result = recalculate_validation_status("val_123")

            # Should prioritize applied
            assert result == "enhanced"
            assert mock_validation.status == ValidationStatus.ENHANCED

    def test_validation_no_recommendations_with_errors(self):
        """Test validation with no recommendations but errors becomes FAIL."""
        mock_validation = MagicMock()
        mock_validation.status = ValidationStatus.PASS
        mock_validation.validation_results = {
            "validator1": {
                "issues": [
                    {"severity": "error", "message": "Test error"}
                ]
            }
        }

        mock_db = MagicMock()
        mock_db.get_validation_result.return_value = mock_validation
        mock_db.list_recommendations.return_value = []

        with patch('api.services.status_recalculator.db_manager', mock_db):
            result = recalculate_validation_status("val_123")

            assert result == "fail"
            assert mock_validation.status == ValidationStatus.FAIL
            mock_db.session.commit.assert_called_once()

    def test_validation_no_recommendations_with_warnings(self):
        """Test validation with no recommendations but warnings becomes WARNING."""
        mock_validation = MagicMock()
        mock_validation.status = ValidationStatus.PASS
        mock_validation.validation_results = {
            "validator1": {
                "issues": [
                    {"severity": "warning", "message": "Test warning"}
                ]
            }
        }

        mock_db = MagicMock()
        mock_db.get_validation_result.return_value = mock_validation
        mock_db.list_recommendations.return_value = []

        with patch('api.services.status_recalculator.db_manager', mock_db):
            result = recalculate_validation_status("val_123")

            assert result == "warning"
            assert mock_validation.status == ValidationStatus.WARNING
            mock_db.session.commit.assert_called_once()

    def test_validation_no_recommendations_no_issues_becomes_pass(self):
        """Test validation with no recommendations and no issues becomes PASS."""
        mock_validation = MagicMock()
        mock_validation.status = ValidationStatus.WARNING
        mock_validation.validation_results = {
            "validator1": {
                "issues": []
            }
        }

        mock_db = MagicMock()
        mock_db.get_validation_result.return_value = mock_validation
        mock_db.list_recommendations.return_value = []

        with patch('api.services.status_recalculator.db_manager', mock_db):
            result = recalculate_validation_status("val_123")

            assert result == "pass"
            assert mock_validation.status == ValidationStatus.PASS
            mock_db.session.commit.assert_called_once()

    def test_validation_errors_have_priority_over_warnings(self):
        """Test that errors have priority over warnings in status calculation."""
        mock_validation = MagicMock()
        mock_validation.status = ValidationStatus.PASS
        mock_validation.validation_results = {
            "validator1": {
                "issues": [
                    {"severity": "warning", "message": "Warning"},
                    {"severity": "error", "message": "Error"}
                ]
            }
        }

        mock_db = MagicMock()
        mock_db.get_validation_result.return_value = mock_validation
        mock_db.list_recommendations.return_value = []

        with patch('api.services.status_recalculator.db_manager', mock_db):
            result = recalculate_validation_status("val_123")

            assert result == "fail"
            assert mock_validation.status == ValidationStatus.FAIL

    def test_validation_multiple_validators_with_errors(self):
        """Test validation with multiple validators and errors."""
        mock_validation = MagicMock()
        mock_validation.status = ValidationStatus.PASS
        mock_validation.validation_results = {
            "validator1": {
                "issues": [{"severity": "warning", "message": "Warning"}]
            },
            "validator2": {
                "issues": [{"severity": "error", "message": "Error"}]
            }
        }

        mock_db = MagicMock()
        mock_db.get_validation_result.return_value = mock_validation
        mock_db.list_recommendations.return_value = []

        with patch('api.services.status_recalculator.db_manager', mock_db):
            result = recalculate_validation_status("val_123")

            assert result == "fail"

    def test_validation_empty_results_dict(self):
        """Test validation with empty validation_results dict."""
        mock_validation = MagicMock()
        mock_validation.status = ValidationStatus.WARNING
        mock_validation.validation_results = {}

        mock_db = MagicMock()
        mock_db.get_validation_result.return_value = mock_validation
        mock_db.list_recommendations.return_value = []

        with patch('api.services.status_recalculator.db_manager', mock_db):
            result = recalculate_validation_status("val_123")

            assert result == "pass"
            assert mock_validation.status == ValidationStatus.PASS

    def test_validation_null_results(self):
        """Test validation with None validation_results."""
        mock_validation = MagicMock()
        mock_validation.status = ValidationStatus.WARNING
        mock_validation.validation_results = None

        mock_db = MagicMock()
        mock_db.get_validation_result.return_value = mock_validation
        mock_db.list_recommendations.return_value = []

        with patch('api.services.status_recalculator.db_manager', mock_db):
            result = recalculate_validation_status("val_123")

            assert result == "pass"
            assert mock_validation.status == ValidationStatus.PASS

    def test_validation_non_dict_validator_results(self):
        """Test validation with non-dict validator results."""
        mock_validation = MagicMock()
        mock_validation.status = ValidationStatus.PASS
        mock_validation.validation_results = {
            "validator1": "not a dict"
        }

        mock_db = MagicMock()
        mock_db.get_validation_result.return_value = mock_validation
        mock_db.list_recommendations.return_value = []

        with patch('api.services.status_recalculator.db_manager', mock_db):
            result = recalculate_validation_status("val_123")

            # Should handle gracefully and return pass (no errors found)
            assert result == "pass"

    def test_validation_issue_missing_severity(self):
        """Test validation with issue missing severity field."""
        mock_validation = MagicMock()
        mock_validation.status = ValidationStatus.PASS
        mock_validation.validation_results = {
            "validator1": {
                "issues": [
                    {"message": "No severity field"}
                ]
            }
        }

        mock_db = MagicMock()
        mock_db.get_validation_result.return_value = mock_validation
        mock_db.list_recommendations.return_value = []

        with patch('api.services.status_recalculator.db_manager', mock_db):
            result = recalculate_validation_status("val_123")

            # Should handle missing severity gracefully
            assert result == "pass"

    def test_validation_exception_returns_none(self):
        """Test that exceptions during recalculation return None."""
        mock_db = MagicMock()
        mock_db.get_validation_result.side_effect = Exception("Database error")

        with patch('api.services.status_recalculator.db_manager', mock_db):
            result = recalculate_validation_status("val_123")

            assert result is None

    def test_validation_commit_exception_returns_none(self):
        """Test that commit exceptions are handled and return None."""
        mock_validation = MagicMock()
        mock_validation.status = ValidationStatus.PASS

        mock_db = MagicMock()
        mock_db.get_validation_result.return_value = mock_validation
        mock_db.list_recommendations.return_value = []
        mock_db.session.commit.side_effect = Exception("Commit failed")

        with patch('api.services.status_recalculator.db_manager', mock_db):
            result = recalculate_validation_status("val_123")

            assert result is None


@pytest.mark.unit
class TestRecalculateWorkflowStatus:
    """Test recalculate_workflow_status function."""

    def test_workflow_not_found_returns_none(self):
        """Test that non-existent workflow returns None."""
        mock_db = MagicMock()
        mock_db.get_workflow.return_value = None

        with patch('api.services.status_recalculator.db_manager', mock_db):
            result = recalculate_workflow_status("nonexistent_id")

            assert result is None
            mock_db.get_workflow.assert_called_once_with("nonexistent_id")

    def test_workflow_no_validations_pending_state(self):
        """Test workflow with no validations keeps PENDING state."""
        mock_workflow = MagicMock()
        # Create a mock state object that behaves like an enum
        mock_state = MagicMock()
        mock_state.value = "pending"
        mock_workflow.state = mock_state

        mock_db = MagicMock()
        mock_db.get_workflow.return_value = mock_workflow
        mock_db.list_validation_results.return_value = []

        with patch('api.services.status_recalculator.db_manager', mock_db):
            result = recalculate_workflow_status("wf_123")

            assert result == "pending"
            # State should not change
            assert mock_workflow.state == mock_state

    def test_workflow_no_validations_running_state(self):
        """Test workflow with no validations keeps RUNNING state."""
        mock_workflow = MagicMock()
        # Create a mock state object that behaves like an enum
        mock_state = MagicMock()
        mock_state.value = "running"
        mock_workflow.state = mock_state

        mock_db = MagicMock()
        mock_db.get_workflow.return_value = mock_workflow
        mock_db.list_validation_results.return_value = []

        with patch('api.services.status_recalculator.db_manager', mock_db):
            result = recalculate_workflow_status("wf_123")

            assert result == "running"

    def test_workflow_with_failed_validations_becomes_failed(self):
        """Test workflow with failed validations becomes FAILED."""
        mock_workflow = MagicMock()
        mock_workflow.state = WorkflowState.COMPLETED

        mock_val1 = MagicMock()
        mock_val1.status = ValidationStatus.FAIL
        mock_val2 = MagicMock()
        mock_val2.status = ValidationStatus.PASS

        mock_db = MagicMock()
        mock_db.get_workflow.return_value = mock_workflow
        mock_db.list_validation_results.return_value = [mock_val1, mock_val2]

        with patch('api.services.status_recalculator.db_manager', mock_db):
            result = recalculate_workflow_status("wf_123")

            assert result == "failed"
            assert mock_workflow.state == WorkflowState.FAILED
            mock_db.session.commit.assert_called_once()

    def test_workflow_with_enhanced_and_failed_becomes_completed(self):
        """Test workflow with enhanced validations becomes COMPLETED (if not RUNNING/PENDING)."""
        # RUNNING/PENDING workflows stay in their state, so use COMPLETED state initially
        mock_workflow = MagicMock()
        mock_workflow.state = WorkflowState.COMPLETED

        mock_val1 = MagicMock()
        mock_val1.status = ValidationStatus.ENHANCED
        mock_val2 = MagicMock()
        mock_val2.status = ValidationStatus.FAIL

        mock_db = MagicMock()
        mock_db.get_workflow.return_value = mock_workflow
        mock_db.list_validation_results.return_value = [mock_val1, mock_val2]

        with patch('api.services.status_recalculator.db_manager', mock_db):
            result = recalculate_workflow_status("wf_123")

            # Enhanced overrides failed
            assert result == "completed"
            # State unchanged (already completed)
            assert mock_workflow.state == WorkflowState.COMPLETED

    def test_workflow_cancelled_stays_cancelled(self):
        """Test cancelled workflow stays CANCELLED."""
        mock_workflow = MagicMock()
        mock_workflow.state = WorkflowState.CANCELLED

        mock_val1 = MagicMock()
        mock_val1.status = ValidationStatus.PASS

        mock_db = MagicMock()
        mock_db.get_workflow.return_value = mock_workflow
        mock_db.list_validation_results.return_value = [mock_val1]

        with patch('api.services.status_recalculator.db_manager', mock_db):
            result = recalculate_workflow_status("wf_123")

            assert result == "cancelled"
            assert mock_workflow.state == WorkflowState.CANCELLED

    def test_workflow_running_stays_running(self):
        """Test running workflow with validations stays RUNNING."""
        mock_workflow = MagicMock()
        mock_workflow.state = WorkflowState.RUNNING

        mock_val1 = MagicMock()
        mock_val1.status = ValidationStatus.PASS

        mock_db = MagicMock()
        mock_db.get_workflow.return_value = mock_workflow
        mock_db.list_validation_results.return_value = [mock_val1]

        with patch('api.services.status_recalculator.db_manager', mock_db):
            result = recalculate_workflow_status("wf_123")

            assert result == "running"
            # State unchanged
            assert mock_workflow.state == WorkflowState.RUNNING

    def test_workflow_pending_stays_pending(self):
        """Test pending workflow with validations stays PENDING."""
        mock_workflow = MagicMock()
        mock_workflow.state = WorkflowState.PENDING

        mock_val1 = MagicMock()
        mock_val1.status = ValidationStatus.PASS

        mock_db = MagicMock()
        mock_db.get_workflow.return_value = mock_workflow
        mock_db.list_validation_results.return_value = [mock_val1]

        with patch('api.services.status_recalculator.db_manager', mock_db):
            result = recalculate_workflow_status("wf_123")

            assert result == "pending"

    def test_workflow_all_pass_becomes_completed(self):
        """Test workflow with all passing validations becomes COMPLETED."""
        mock_workflow = MagicMock()
        mock_workflow.state = WorkflowState.COMPLETED

        mock_val1 = MagicMock()
        mock_val1.status = ValidationStatus.PASS
        mock_val2 = MagicMock()
        mock_val2.status = ValidationStatus.APPROVED

        mock_db = MagicMock()
        mock_db.get_workflow.return_value = mock_workflow
        mock_db.list_validation_results.return_value = [mock_val1, mock_val2]

        with patch('api.services.status_recalculator.db_manager', mock_db):
            result = recalculate_workflow_status("wf_123")

            assert result == "completed"
            # State unchanged (already completed)
            mock_db.session.commit.assert_not_called()

    def test_workflow_state_change_commits(self):
        """Test workflow state change triggers commit."""
        # Use PAUSED state (not RUNNING/PENDING) so it can actually change
        mock_workflow = MagicMock()
        mock_workflow.state = WorkflowState.PAUSED

        mock_val1 = MagicMock()
        mock_val1.status = ValidationStatus.FAIL

        mock_db = MagicMock()
        mock_db.get_workflow.return_value = mock_workflow
        mock_db.list_validation_results.return_value = [mock_val1]

        with patch('api.services.status_recalculator.db_manager', mock_db):
            result = recalculate_workflow_status("wf_123")

            assert result == "failed"
            # Should commit because state changed from PAUSED to FAILED
            mock_db.session.commit.assert_called_once()

    def test_workflow_no_state_change_no_commit(self):
        """Test workflow with no state change does not commit."""
        mock_workflow = MagicMock()
        mock_workflow.state = WorkflowState.COMPLETED

        mock_val1 = MagicMock()
        mock_val1.status = ValidationStatus.PASS

        mock_db = MagicMock()
        mock_db.get_workflow.return_value = mock_workflow
        mock_db.list_validation_results.return_value = [mock_val1]

        with patch('api.services.status_recalculator.db_manager', mock_db):
            result = recalculate_workflow_status("wf_123")

            assert result == "completed"
            # Should not commit (no change)
            mock_db.session.commit.assert_not_called()

    def test_workflow_exception_returns_none(self):
        """Test that exceptions during workflow recalculation return None."""
        mock_db = MagicMock()
        mock_db.get_workflow.side_effect = Exception("Database error")

        with patch('api.services.status_recalculator.db_manager', mock_db):
            result = recalculate_workflow_status("wf_123")

            assert result is None

    def test_workflow_commit_exception_returns_none(self):
        """Test that commit exceptions are handled and return None."""
        # Use PAUSED so state actually changes and triggers commit
        mock_workflow = MagicMock()
        mock_workflow.state = WorkflowState.PAUSED

        mock_val1 = MagicMock()
        mock_val1.status = ValidationStatus.FAIL

        mock_db = MagicMock()
        mock_db.get_workflow.return_value = mock_workflow
        mock_db.list_validation_results.return_value = [mock_val1]
        mock_db.session.commit.side_effect = Exception("Commit failed")

        with patch('api.services.status_recalculator.db_manager', mock_db):
            result = recalculate_workflow_status("wf_123")

            assert result is None


@pytest.mark.unit
class TestOnRecommendationUpdated:
    """Test on_recommendation_updated callback function."""

    def test_recommendation_not_found_returns_silently(self):
        """Test that non-existent recommendation returns silently."""
        mock_db = MagicMock()
        mock_db.get_recommendation.return_value = None

        with patch('api.services.status_recalculator.db_manager', mock_db):
            # Should not raise exception
            on_recommendation_updated("nonexistent_id")

            mock_db.get_recommendation.assert_called_once_with("nonexistent_id")

    def test_recommendation_triggers_validation_recalculation(self):
        """Test that recommendation update triggers validation recalculation."""
        mock_recommendation = MagicMock()
        mock_recommendation.validation_id = "val_123"

        mock_validation = MagicMock()
        mock_validation.workflow_id = None
        mock_validation.status = ValidationStatus.PASS

        mock_db = MagicMock()
        mock_db.get_recommendation.return_value = mock_recommendation
        mock_db.get_validation_result.return_value = mock_validation
        mock_db.list_recommendations.return_value = []

        with patch('api.services.status_recalculator.db_manager', mock_db):
            on_recommendation_updated("rec_123")

            # Should call get_validation_result twice (once in recalculate, once to check workflow)
            assert mock_db.get_validation_result.call_count == 2

    def test_recommendation_triggers_workflow_recalculation(self):
        """Test that recommendation update triggers workflow recalculation if validation has workflow."""
        mock_recommendation = MagicMock()
        mock_recommendation.validation_id = "val_123"

        mock_validation = MagicMock()
        mock_validation.workflow_id = "wf_456"
        mock_validation.status = ValidationStatus.PASS

        mock_workflow = MagicMock()
        mock_workflow.state = WorkflowState.RUNNING

        mock_db = MagicMock()
        mock_db.get_recommendation.return_value = mock_recommendation
        mock_db.get_validation_result.return_value = mock_validation
        mock_db.list_recommendations.return_value = []
        mock_db.get_workflow.return_value = mock_workflow
        mock_db.list_validation_results.return_value = []

        with patch('api.services.status_recalculator.db_manager', mock_db):
            on_recommendation_updated("rec_123")

            # Should call get_workflow for workflow recalculation
            mock_db.get_workflow.assert_called_once_with("wf_456")

    def test_recommendation_no_workflow_only_validation_recalculation(self):
        """Test that recommendation update without workflow only recalculates validation."""
        mock_recommendation = MagicMock()
        mock_recommendation.validation_id = "val_123"

        mock_validation = MagicMock()
        mock_validation.workflow_id = None
        mock_validation.status = ValidationStatus.PASS

        mock_db = MagicMock()
        mock_db.get_recommendation.return_value = mock_recommendation
        mock_db.get_validation_result.return_value = mock_validation
        mock_db.list_recommendations.return_value = []

        with patch('api.services.status_recalculator.db_manager', mock_db):
            on_recommendation_updated("rec_123")

            # Should not call get_workflow
            mock_db.get_workflow.assert_not_called()

    def test_recommendation_exception_handled_silently(self):
        """Test that exceptions during callback are handled silently."""
        mock_db = MagicMock()
        mock_db.get_recommendation.side_effect = Exception("Database error")

        with patch('api.services.status_recalculator.db_manager', mock_db):
            # Should not raise exception
            on_recommendation_updated("rec_123")

    def test_recommendation_validation_none_handled(self):
        """Test that None validation is handled gracefully."""
        mock_recommendation = MagicMock()
        mock_recommendation.validation_id = "val_123"

        mock_db = MagicMock()
        mock_db.get_recommendation.return_value = mock_recommendation
        mock_db.get_validation_result.side_effect = [None, None]  # First for recalc, second for workflow check

        with patch('api.services.status_recalculator.db_manager', mock_db):
            # Should not raise exception
            on_recommendation_updated("rec_123")


@pytest.mark.integration
class TestStatusRecalculatorIntegration:
    """Integration tests for status recalculator service."""

    def test_full_recommendation_workflow(self):
        """Test complete workflow: recommendation update triggers both validation and workflow recalculation."""
        # Setup mocks
        mock_recommendation = MagicMock()
        mock_recommendation.validation_id = "val_123"
        mock_recommendation.status.value = "applied"

        mock_validation = MagicMock()
        mock_validation.workflow_id = "wf_456"
        mock_validation.status = ValidationStatus.PASS
        mock_validation.validation_results = {}

        # Use PAUSED state (not RUNNING) so it can actually change to COMPLETED
        mock_workflow = MagicMock()
        mock_workflow.state = WorkflowState.PAUSED

        mock_val_for_workflow = MagicMock()
        mock_val_for_workflow.status = ValidationStatus.ENHANCED

        mock_db = MagicMock()
        mock_db.get_recommendation.return_value = mock_recommendation
        mock_db.get_validation_result.return_value = mock_validation
        mock_db.list_recommendations.return_value = [mock_recommendation]
        mock_db.get_workflow.return_value = mock_workflow
        mock_db.list_validation_results.return_value = [mock_val_for_workflow]

        with patch('api.services.status_recalculator.db_manager', mock_db):
            on_recommendation_updated("rec_123")

            # Verify validation status updated to ENHANCED
            assert mock_validation.status == ValidationStatus.ENHANCED

            # Verify workflow status updated to COMPLETED
            assert mock_workflow.state == WorkflowState.COMPLETED

            # Verify commits happened
            assert mock_db.session.commit.call_count >= 2

    def test_cascade_status_changes(self):
        """Test cascading status changes from recommendation to validation to workflow."""
        # Create recommendation that changes validation status
        mock_rec = MagicMock()
        mock_rec.validation_id = "val_1"
        mock_rec.status.value = "applied"

        # Validation should change to ENHANCED
        mock_val = MagicMock()
        mock_val.workflow_id = "wf_1"
        mock_val.status = ValidationStatus.WARNING

        # Workflow should change to COMPLETED (use PAUSED, not RUNNING)
        mock_wf = MagicMock()
        mock_wf.state = WorkflowState.PAUSED

        mock_db = MagicMock()
        mock_db.get_recommendation.return_value = mock_rec
        mock_db.get_validation_result.return_value = mock_val
        mock_db.list_recommendations.return_value = [mock_rec]
        mock_db.get_workflow.return_value = mock_wf

        # Create mock validation with ENHANCED status for workflow calculation
        mock_val_enhanced = MagicMock()
        mock_val_enhanced.status = ValidationStatus.ENHANCED
        mock_db.list_validation_results.return_value = [mock_val_enhanced]

        with patch('api.services.status_recalculator.db_manager', mock_db):
            on_recommendation_updated("rec_1")

            # Trace the cascade
            assert mock_val.status == ValidationStatus.ENHANCED
            assert mock_wf.state == WorkflowState.COMPLETED
