# file: tbcv/api/services/status_recalculator.py
"""
Service to recalculate aggregate statuses for validations and workflows.
"""

from __future__ import annotations

from typing import Optional

try:
    from core.database import db_manager, ValidationStatus, WorkflowState
    from core.logging import get_logger
except ImportError:
    from core.database import db_manager, ValidationStatus, WorkflowState
    from core.logging import get_logger

logger = get_logger(__name__)


def recalculate_validation_status(validation_id: str) -> Optional[str]:
    """
    Recalculate validation status based on recommendations and results.
    
    Args:
        validation_id: ID of the validation
        
    Returns:
        New status or None if validation not found
    """
    try:
        validation = db_manager.get_validation_result(validation_id)
        if not validation:
            return None
        
        # Get recommendations
        recommendations = db_manager.list_recommendations(validation_id=validation_id)
        
        # Determine status based on recommendations
        if recommendations:
            accepted_count = sum(1 for r in recommendations if r.status.value == "accepted")
            applied_count = sum(1 for r in recommendations if r.status.value == "applied")
            rejected_count = sum(1 for r in recommendations if r.status.value == "rejected")
            
            if applied_count > 0:
                new_status = ValidationStatus.ENHANCED
            elif accepted_count > 0:
                new_status = ValidationStatus.APPROVED
            elif rejected_count == len(recommendations):
                new_status = ValidationStatus.REJECTED
            else:
                # Keep current status
                return validation.status.value
        else:
            # No recommendations - keep validation status based on severity
            validation_results = validation.validation_results or {}
            has_errors = False
            has_warnings = False
            
            if isinstance(validation_results, dict):
                for validator_name, validator_results in validation_results.items():
                    if isinstance(validator_results, dict):
                        issues = validator_results.get('issues', [])
                        for issue in issues:
                            severity = issue.get('severity', '').lower()
                            if severity == 'error':
                                has_errors = True
                            elif severity == 'warning':
                                has_warnings = True
            
            if has_errors:
                new_status = ValidationStatus.FAIL
            elif has_warnings:
                new_status = ValidationStatus.WARNING
            else:
                new_status = ValidationStatus.PASS
        
        # Update validation status
        validation.status = new_status
        db_manager.session.commit()
        
        logger.info(f"Recalculated validation {validation_id} status to {new_status.value}")
        return new_status.value
        
    except Exception:
        logger.exception(f"Failed to recalculate validation status for {validation_id}")
        return None


def recalculate_workflow_status(workflow_id: str) -> Optional[str]:
    """
    Recalculate workflow status based on associated validations.
    
    Args:
        workflow_id: ID of the workflow
        
    Returns:
        New status or None if workflow not found
    """
    try:
        workflow = db_manager.get_workflow(workflow_id)
        if not workflow:
            return None
        
        # Get associated validations
        validations = db_manager.list_validation_results(workflow_id=workflow_id, limit=1000)
        
        if not validations:
            # No validations yet - check current state
            if workflow.state in [WorkflowState.PENDING, WorkflowState.RUNNING]:
                return workflow.state.value
            return workflow.state.value
        
        # Count validation statuses
        total = len(validations)
        enhanced_count = sum(1 for v in validations if v.status == ValidationStatus.ENHANCED)
        failed_count = sum(1 for v in validations if v.status == ValidationStatus.FAIL)
        approved_count = sum(1 for v in validations if v.status == ValidationStatus.APPROVED)
        
        # Determine workflow status
        if workflow.state == WorkflowState.CANCELLED:
            new_state = WorkflowState.CANCELLED
        elif workflow.state == WorkflowState.RUNNING or workflow.state == WorkflowState.PENDING:
            # Keep running/pending if not all complete
            new_state = workflow.state
        elif failed_count > 0 and enhanced_count == 0:
            new_state = WorkflowState.FAILED
        else:
            new_state = WorkflowState.COMPLETED
        
        # Update workflow state
        if workflow.state != new_state:
            workflow.state = new_state
            db_manager.session.commit()
            logger.info(f"Recalculated workflow {workflow_id} status to {new_state.value}")
        
        return new_state.value
        
    except Exception:
        logger.exception(f"Failed to recalculate workflow status for {workflow_id}")
        return None


def on_recommendation_updated(recommendation_id: str):
    """
    Callback when a recommendation is updated.
    Triggers recalculation of related validation and workflow statuses.
    
    Args:
        recommendation_id: ID of the updated recommendation
    """
    try:
        recommendation = db_manager.get_recommendation(recommendation_id)
        if not recommendation:
            return
        
        # Recalculate validation status
        validation_id = recommendation.validation_id
        recalculate_validation_status(validation_id)
        
        # Recalculate workflow status if validation is part of a workflow
        validation = db_manager.get_validation_result(validation_id)
        if validation and validation.workflow_id:
            recalculate_workflow_status(validation.workflow_id)
            
    except Exception:
        logger.exception(f"Failed in on_recommendation_updated for {recommendation_id}")
