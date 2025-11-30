"""Approval method handlers for MCP server."""

from typing import Dict, Any, List
from datetime import datetime, timezone
from .base import BaseMCPMethod
from core.database import ValidationResult, ValidationStatus
from core.logging import get_logger

logger = get_logger(__name__)


class ApprovalMethods(BaseMCPMethod):
    """Handler for approval-related MCP methods."""

    def handle(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle approval method execution.

        Args:
            params: Method parameters

        Returns:
            Approval results

        Raises:
            ValueError: If parameters are invalid
        """
        # This is called via registry, specific methods are called directly
        raise NotImplementedError("Use specific approval methods via registry")

    def approve(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Approve validation records.

        Args:
            params: Parameters containing ids list

        Returns:
            Approval results with count and any errors

        Raises:
            ValueError: If ids parameter is missing
        """
        self.validate_params(params, required=["ids"])

        ids = params.get("ids", [])
        if not isinstance(ids, list):
            raise ValueError("ids must be a list")

        approved_count = 0
        errors = []

        self.logger.info(f"Approving {len(ids)} validation records")

        for validation_id in ids:
            try:
                # Get all validation records and find the one we need
                records = self.db_manager.list_validation_results(limit=1000)
                validation = None
                for record in records:
                    if record.id == validation_id:
                        validation = record
                        break

                if not validation:
                    errors.append(f"Validation {validation_id} not found")
                    continue

                # Update status directly in database
                with self.db_manager.get_session() as session:
                    db_record = session.query(ValidationResult).filter(
                        ValidationResult.id == validation_id
                    ).first()
                    if db_record:
                        db_record.status = ValidationStatus.APPROVED
                        db_record.updated_at = datetime.now(timezone.utc)
                        session.commit()
                        approved_count += 1
                        self.logger.debug(f"Approved validation {validation_id}")
                    else:
                        errors.append(f"Validation {validation_id} not found in database")

            except Exception as e:
                error_msg = f"Error approving {validation_id}: {str(e)}"
                errors.append(error_msg)
                self.logger.error(error_msg)

        self.logger.info(f"Approved {approved_count} of {len(ids)} validation records")

        return {
            "success": True,
            "approved_count": approved_count,
            "errors": errors
        }

    def reject(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reject validation records.

        Args:
            params: Parameters containing ids list

        Returns:
            Rejection results with count and any errors

        Raises:
            ValueError: If ids parameter is missing
        """
        self.validate_params(params, required=["ids"])

        ids = params.get("ids", [])
        if not isinstance(ids, list):
            raise ValueError("ids must be a list")

        rejected_count = 0
        errors = []

        self.logger.info(f"Rejecting {len(ids)} validation records")

        for validation_id in ids:
            try:
                # Get all validation records and find the one we need
                records = self.db_manager.list_validation_results(limit=1000)
                validation = None
                for record in records:
                    if record.id == validation_id:
                        validation = record
                        break

                if not validation:
                    errors.append(f"Validation {validation_id} not found")
                    continue

                # Update status directly in database
                with self.db_manager.get_session() as session:
                    db_record = session.query(ValidationResult).filter(
                        ValidationResult.id == validation_id
                    ).first()
                    if db_record:
                        db_record.status = ValidationStatus.REJECTED
                        db_record.updated_at = datetime.now(timezone.utc)
                        session.commit()
                        rejected_count += 1
                        self.logger.debug(f"Rejected validation {validation_id}")
                    else:
                        errors.append(f"Validation {validation_id} not found in database")

            except Exception as e:
                error_msg = f"Error rejecting {validation_id}: {str(e)}"
                errors.append(error_msg)
                self.logger.error(error_msg)

        self.logger.info(f"Rejected {rejected_count} of {len(ids)} validation records")

        return {
            "success": True,
            "rejected_count": rejected_count,
            "errors": errors
        }
