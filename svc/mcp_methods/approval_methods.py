"""Approval method handlers for MCP server."""

import time
from typing import Dict, Any, List, Optional, Tuple
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

    def _batch_update_status(
        self,
        validation_ids: List[str],
        status: ValidationStatus,
        session,
        notes: Optional[str] = None
    ) -> Tuple[int, List[str]]:
        """
        Batch update validation status efficiently.

        Args:
            validation_ids: List of validation IDs to update
            status: New status to set
            session: Database session
            notes: Optional notes to add

        Returns:
            Tuple of (success_count, error_messages)
        """
        success_count = 0
        errors = []

        # Batch query - get all validations in one query
        validations = session.query(ValidationResult).filter(
            ValidationResult.id.in_(validation_ids)
        ).all()

        # Create lookup for found validations
        found_ids = {v.id for v in validations}

        # Track not found IDs
        for vid in validation_ids:
            if vid not in found_ids:
                errors.append(f"Validation {vid} not found")

        # Batch update all found validations
        try:
            for validation in validations:
                validation.status = status
                validation.updated_at = datetime.now(timezone.utc)

                if notes:
                    # Append to existing notes
                    if validation.notes:
                        validation.notes += f"\n{notes}"
                    else:
                        validation.notes = notes

                success_count += 1

            # Commit all changes in single transaction
            session.commit()

        except Exception as e:
            session.rollback()
            self.logger.error(f"Batch update failed: {e}")
            errors.append(f"Database error: {str(e)}")
            success_count = 0

        return success_count, errors

    def approve(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Approve validation(s).

        Args:
            params: {
                "ids": Union[str, List[str]] (required) - Single ID or list of IDs
            }

        Returns:
            {
                "success": bool,
                "approved_count": int,
                "failed_count": int,
                "errors": List[str]
            }
        """
        self.validate_params(params, required=["ids"])

        ids = params["ids"]

        # Normalize to list
        if isinstance(ids, str):
            ids = [ids]

        if not ids:
            self.logger.info("No validation IDs provided for approval")
            return {
                "success": True,
                "approved_count": 0,
                "failed_count": 0,
                "errors": []
            }

        self.logger.info(f"Approving {len(ids)} validation(s)")

        # Use batch processing
        with self.db_manager.get_session() as session:
            approved_count, errors = self._batch_update_status(
                ids,
                ValidationStatus.APPROVED,
                session
            )

        self.logger.info(f"Approved {approved_count}/{len(ids)} validations")

        return {
            "success": True,  # Operation succeeded even if no validations were found
            "approved_count": approved_count,
            "failed_count": len(ids) - approved_count,
            "errors": errors
        }

    def reject(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reject validation(s).

        Args:
            params: {
                "ids": Union[str, List[str]] (required) - Single ID or list of IDs,
                "reason": str (optional) - Rejection reason
            }

        Returns:
            {
                "success": bool,
                "rejected_count": int,
                "failed_count": int,
                "errors": List[str]
            }
        """
        self.validate_params(params, required=["ids"], optional={"reason": None})

        ids = params["ids"]
        reason = params.get("reason")

        # Normalize to list
        if isinstance(ids, str):
            ids = [ids]

        if not ids:
            self.logger.info("No validation IDs provided for rejection")
            return {
                "success": True,
                "rejected_count": 0,
                "failed_count": 0,
                "errors": []
            }

        self.logger.info(f"Rejecting {len(ids)} validation(s)")

        # Use batch processing
        with self.db_manager.get_session() as session:
            rejected_count, errors = self._batch_update_status(
                ids,
                ValidationStatus.REJECTED,
                session,
                notes=reason
            )

        self.logger.info(f"Rejected {rejected_count}/{len(ids)} validations")

        return {
            "success": True,  # Operation succeeded even if no validations were found
            "rejected_count": rejected_count,
            "failed_count": len(ids) - rejected_count,
            "errors": errors
        }

    def bulk_approve(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Bulk approve multiple validations efficiently.

        Args:
            params: {
                "ids": List[str] (required) - List of validation IDs,
                "batch_size": int (optional, default 100) - Processing batch size
            }

        Returns:
            {
                "success": bool,
                "total": int,
                "approved_count": int,
                "failed_count": int,
                "errors": List[str],
                "processing_time_ms": float
            }
        """
        start_time = time.time()

        self.validate_params(params, required=["ids"], optional={"batch_size": 100})

        ids = params["ids"]
        batch_size = params.get("batch_size", 100)

        if not isinstance(ids, list):
            raise ValueError("bulk_approve requires a list of IDs")

        total = len(ids)

        if total == 0:
            self.logger.info("No validation IDs provided for bulk approval")
            return {
                "success": True,
                "total": 0,
                "approved_count": 0,
                "failed_count": 0,
                "errors": [],
                "processing_time_ms": 0.0
            }

        self.logger.info(f"Bulk approving {total} validations in batches of {batch_size}")

        # Process in batches to avoid transaction timeout
        total_approved = 0
        all_errors = []

        for i in range(0, total, batch_size):
            batch_ids = ids[i:i + batch_size]

            with self.db_manager.get_session() as session:
                approved, errors = self._batch_update_status(
                    batch_ids,
                    ValidationStatus.APPROVED,
                    session
                )

                total_approved += approved
                all_errors.extend(errors)

            self.logger.info(f"Batch {i//batch_size + 1}: approved {approved}/{len(batch_ids)}")

        processing_time = (time.time() - start_time) * 1000

        self.logger.info(
            f"Bulk approve complete: {total_approved}/{total} in {processing_time:.2f}ms"
        )

        return {
            "success": total_approved > 0,
            "total": total,
            "approved_count": total_approved,
            "failed_count": total - total_approved,
            "errors": all_errors,
            "processing_time_ms": processing_time
        }

    def bulk_reject(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Bulk reject multiple validations efficiently.

        Args:
            params: {
                "ids": List[str] (required) - List of validation IDs,
                "reason": str (optional) - Rejection reason,
                "batch_size": int (optional, default 100) - Processing batch size
            }

        Returns:
            {
                "success": bool,
                "total": int,
                "rejected_count": int,
                "failed_count": int,
                "errors": List[str],
                "processing_time_ms": float
            }
        """
        start_time = time.time()

        self.validate_params(
            params,
            required=["ids"],
            optional={"reason": None, "batch_size": 100}
        )

        ids = params["ids"]
        reason = params.get("reason")
        batch_size = params.get("batch_size", 100)

        if not isinstance(ids, list):
            raise ValueError("bulk_reject requires a list of IDs")

        total = len(ids)

        if total == 0:
            self.logger.info("No validation IDs provided for bulk rejection")
            return {
                "success": True,
                "total": 0,
                "rejected_count": 0,
                "failed_count": 0,
                "errors": [],
                "processing_time_ms": 0.0
            }

        self.logger.info(f"Bulk rejecting {total} validations in batches of {batch_size}")

        total_rejected = 0
        all_errors = []

        for i in range(0, total, batch_size):
            batch_ids = ids[i:i + batch_size]

            with self.db_manager.get_session() as session:
                rejected, errors = self._batch_update_status(
                    batch_ids,
                    ValidationStatus.REJECTED,
                    session,
                    notes=reason
                )

                total_rejected += rejected
                all_errors.extend(errors)

            self.logger.info(f"Batch {i//batch_size + 1}: rejected {rejected}/{len(batch_ids)}")

        processing_time = (time.time() - start_time) * 1000

        self.logger.info(
            f"Bulk reject complete: {total_rejected}/{total} in {processing_time:.2f}ms"
        )

        return {
            "success": total_rejected > 0,
            "total": total,
            "rejected_count": total_rejected,
            "failed_count": total - total_rejected,
            "errors": all_errors,
            "processing_time_ms": processing_time
        }
