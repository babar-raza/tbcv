"""Recommendation-related MCP methods."""

import os
import shutil
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime, timezone
from .base import BaseMCPMethod
from core.database import RecommendationStatus
from core.logging import get_logger

logger = get_logger(__name__)


class RecommendationMethods(BaseMCPMethod):
    """Handler for recommendation-related MCP methods."""

    def handle(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle recommendation method execution.

        Args:
            params: Method parameters

        Returns:
            Recommendation results

        Raises:
            ValueError: If parameters are invalid
        """
        # This is called via registry, specific methods are called directly
        raise NotImplementedError("Use specific recommendation methods via registry")

    def generate_recommendations(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate recommendations for a validation.

        Args:
            params: {
                "validation_id": str (required),
                "threshold": float (optional, default 0.7),
                "types": List[str] (optional - filter recommendation types)
            }

        Returns:
            {
                "success": bool,
                "validation_id": str,
                "recommendation_count": int,
                "recommendations": List[Dict],
                "threshold_used": float
            }
        """
        self.validate_params(
            params,
            required=["validation_id"],
            optional={"threshold": 0.7, "types": None}
        )

        validation_id = params["validation_id"]
        threshold = params["threshold"]
        types = params["types"]

        self.logger.info(f"Generating recommendations for validation: {validation_id}")

        # Get validation record
        validation = self._get_validation_by_id(validation_id)
        if not validation:
            raise ValueError(f"Validation {validation_id} not found")

        # Get recommendation agent
        from agents.recommendation_agent import RecommendationAgent
        rec_agent = RecommendationAgent()

        # Build validation dict for agent
        validation_dict = {
            "id": validation.id,
            "validation_type": validation.validation_types[0] if validation.validation_types else "unknown",
            "status": validation.status.value if hasattr(validation.status, 'value') else str(validation.status),
            "message": str(validation.validation_results.get("message", "")) if isinstance(validation.validation_results, dict) else "",
            "details": validation.validation_results.get("details", {}) if isinstance(validation.validation_results, dict) else {}
        }

        # Get content from file if not stored in validation
        content = getattr(validation, 'content', None) or ""
        if not content and validation.file_path:
            try:
                from pathlib import Path
                file_path = Path(validation.file_path)
                if file_path.exists():
                    content = file_path.read_text(encoding='utf-8')
            except Exception as e:
                self.logger.warning(f"Could not read content from {validation.file_path}: {e}")

        # Generate recommendations using the agent
        recommendations = asyncio.run(rec_agent.generate_recommendations(
            validation=validation_dict,
            content=content,
            context={"file_path": validation.file_path}
        ))

        # Filter by confidence threshold
        filtered_recs = [
            r for r in recommendations
            if r.get("confidence", 0.0) >= threshold
        ]

        # Filter by types if specified
        if types:
            filtered_recs = [
                r for r in filtered_recs
                if r.get("type", "") in types
            ]

        # Store in database
        stored_ids = []
        for rec in filtered_recs:
            try:
                db_rec = self.db_manager.create_recommendation(
                    validation_id=validation_id,
                    type=rec.get("type", "general"),
                    title=rec.get("instruction", "")[:200],
                    description=rec.get("rationale", ""),
                    scope=rec.get("scope", "global"),
                    instruction=rec.get("instruction", ""),
                    rationale=rec.get("rationale", ""),
                    severity=rec.get("severity", "medium"),
                    confidence=rec.get("confidence", 0.0),
                    status="pending",
                    metadata=rec.get("metadata", {})
                )
                if db_rec:
                    stored_ids.append(db_rec.id)
                    # Add ID to recommendation dict
                    rec["id"] = db_rec.id
            except Exception as e:
                self.logger.error(f"Failed to store recommendation: {e}")

        self.logger.info(f"Generated {len(filtered_recs)} recommendations")

        return {
            "success": True,
            "validation_id": validation_id,
            "recommendation_count": len(filtered_recs),
            "recommendations": filtered_recs,
            "threshold_used": threshold
        }

    def rebuild_recommendations(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Rebuild recommendations for a validation.

        Args:
            params: {
                "validation_id": str (required),
                "threshold": float (optional, default 0.7)
            }

        Returns:
            {
                "success": bool,
                "validation_id": str,
                "deleted_count": int,
                "generated_count": int
            }
        """
        self.validate_params(
            params,
            required=["validation_id"],
            optional={"threshold": 0.7}
        )

        validation_id = params["validation_id"]
        threshold = params["threshold"]

        self.logger.info(f"Rebuilding recommendations for validation: {validation_id}")

        # Get existing recommendations
        existing_recs = self.db_manager.list_recommendations(
            validation_id=validation_id,
            limit=10000
        )
        deleted_count = len(existing_recs)

        # Delete existing recommendations
        for rec in existing_recs:
            self.db_manager.delete_recommendation(rec.id)

        # Generate new recommendations
        result = self.generate_recommendations({
            "validation_id": validation_id,
            "threshold": threshold
        })

        return {
            "success": True,
            "validation_id": validation_id,
            "deleted_count": deleted_count,
            "generated_count": result["recommendation_count"]
        }

    def get_recommendations(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get recommendations for a validation.

        Args:
            params: {
                "validation_id": str (required),
                "status": str (optional - filter by status),
                "type": str (optional - filter by type)
            }

        Returns:
            {
                "validation_id": str,
                "recommendations": List[Dict],
                "total": int
            }
        """
        self.validate_params(
            params,
            required=["validation_id"],
            optional={"status": None, "type": None}
        )

        validation_id = params["validation_id"]
        status = params["status"]
        rec_type = params["type"]

        self.logger.info(f"Retrieving recommendations for validation: {validation_id}")

        # Get recommendations from database
        recommendations = self.db_manager.list_recommendations(
            validation_id=validation_id,
            status=status,
            type=rec_type,
            limit=10000
        )

        return {
            "validation_id": validation_id,
            "recommendations": [self._serialize_recommendation(r) for r in recommendations],
            "total": len(recommendations)
        }

    def review_recommendation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Review (approve/reject) a recommendation.

        Args:
            params: {
                "recommendation_id": str (required),
                "action": str (required - "approve" or "reject"),
                "notes": str (optional)
            }

        Returns:
            {
                "success": bool,
                "recommendation_id": str,
                "action": str,
                "new_status": str
            }
        """
        self.validate_params(
            params,
            required=["recommendation_id", "action"],
            optional={"notes": None}
        )

        recommendation_id = params["recommendation_id"]
        action = params["action"]
        notes = params["notes"]

        if action not in ["approve", "reject"]:
            raise ValueError(f"Invalid action: {action}. Must be 'approve' or 'reject'")

        self.logger.info(f"Reviewing recommendation {recommendation_id}: {action}")

        # Get recommendation
        recommendation = self.db_manager.get_recommendation(recommendation_id)
        if not recommendation:
            raise ValueError(f"Recommendation {recommendation_id} not found")

        # Update status
        new_status = "approved" if action == "approve" else "rejected"
        self.db_manager.update_recommendation_status(
            recommendation_id,
            new_status,
            review_notes=notes
        )

        return {
            "success": True,
            "recommendation_id": recommendation_id,
            "action": action,
            "new_status": new_status
        }

    def bulk_review_recommendations(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Bulk review multiple recommendations.

        Args:
            params: {
                "recommendation_ids": List[str] (required),
                "action": str (required - "approve" or "reject"),
                "notes": str (optional)
            }

        Returns:
            {
                "success": bool,
                "reviewed_count": int,
                "errors": List[Dict],
                "action": str
            }
        """
        self.validate_params(
            params,
            required=["recommendation_ids", "action"],
            optional={"notes": None}
        )

        recommendation_ids = params["recommendation_ids"]
        action = params["action"]
        notes = params["notes"]

        if action not in ["approve", "reject"]:
            raise ValueError(f"Invalid action: {action}")

        self.logger.info(f"Bulk reviewing {len(recommendation_ids)} recommendations: {action}")

        reviewed_count = 0
        errors = []

        for rec_id in recommendation_ids:
            try:
                self.review_recommendation({
                    "recommendation_id": rec_id,
                    "action": action,
                    "notes": notes
                })
                reviewed_count += 1
            except Exception as e:
                errors.append({
                    "recommendation_id": rec_id,
                    "error": str(e)
                })

        return {
            "success": True,
            "reviewed_count": reviewed_count,
            "errors": errors,
            "action": action
        }

    def apply_recommendations(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply recommendations to content.

        Args:
            params: {
                "validation_id": str (required),
                "recommendation_ids": List[str] (optional - specific IDs to apply),
                "dry_run": bool (optional, default False),
                "create_backup": bool (optional, default True)
            }

        Returns:
            {
                "success": bool,
                "validation_id": str,
                "applied_count": int,
                "skipped_count": int,
                "errors": List[Dict],
                "backup_path": str (if backup created),
                "dry_run": bool (if dry run mode)
            }
        """
        self.validate_params(
            params,
            required=["validation_id"],
            optional={"recommendation_ids": None, "dry_run": False, "create_backup": True}
        )

        validation_id = params["validation_id"]
        recommendation_ids = params["recommendation_ids"]
        dry_run = params["dry_run"]
        create_backup = params["create_backup"]

        self.logger.info(f"Applying recommendations for validation: {validation_id} (dry_run={dry_run})")

        # Get validation
        validation = self._get_validation_by_id(validation_id)
        if not validation:
            raise ValueError(f"Validation {validation_id} not found")

        # Get recommendations
        if recommendation_ids:
            recommendations = []
            for rec_id in recommendation_ids:
                rec = self.db_manager.get_recommendation(rec_id)
                if rec:
                    recommendations.append(rec)
        else:
            recommendations = self.db_manager.list_recommendations(
                validation_id=validation_id,
                limit=10000
            )

        # Filter to approved recommendations only
        approved_recs = [
            r for r in recommendations
            if r.status == RecommendationStatus.APPROVED or r.status.value == "approved"
        ]

        if not approved_recs:
            return {
                "success": True,
                "validation_id": validation_id,
                "applied_count": 0,
                "skipped_count": len(recommendations),
                "errors": [],
                "message": "No approved recommendations to apply"
            }

        # Create backup if requested and not dry run
        backup_path = None
        if create_backup and not dry_run and validation.file_path:
            file_path = Path(validation.file_path)
            if file_path.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = str(file_path) + f".bak_{timestamp}"
                try:
                    shutil.copy2(str(file_path), backup_path)
                    self.logger.info(f"Created backup: {backup_path}")
                except Exception as e:
                    self.logger.error(f"Failed to create backup: {e}")
                    backup_path = None

        # Apply recommendations
        applied_count = 0
        skipped_count = 0
        errors = []

        if not dry_run:
            # Read current file content
            file_path = Path(validation.file_path)
            if file_path.exists():
                try:
                    content = file_path.read_text(encoding='utf-8')

                    # Apply each recommendation
                    for rec in approved_recs:
                        try:
                            # Simple text replacement for now
                            # In a production system, this would be more sophisticated
                            if rec.original_content and rec.proposed_content:
                                if rec.original_content in content:
                                    content = content.replace(
                                        rec.original_content,
                                        rec.proposed_content,
                                        1  # Replace only first occurrence
                                    )
                                    applied_count += 1

                                    # Mark as applied
                                    self.db_manager.update_recommendation_status(
                                        rec.id,
                                        "applied"
                                    )
                                else:
                                    skipped_count += 1
                                    errors.append({
                                        "recommendation_id": rec.id,
                                        "error": "Original content not found in file"
                                    })
                            else:
                                skipped_count += 1
                                errors.append({
                                    "recommendation_id": rec.id,
                                    "error": "Recommendation missing original/proposed content"
                                })
                        except Exception as e:
                            errors.append({
                                "recommendation_id": rec.id,
                                "error": str(e)
                            })
                            skipped_count += 1

                    # Write modified content back
                    if applied_count > 0:
                        file_path.write_text(content, encoding='utf-8')
                        self.logger.info(f"Applied {applied_count} recommendations to {file_path}")

                except Exception as e:
                    self.logger.error(f"Failed to apply recommendations: {e}")
                    errors.append({
                        "error": f"Failed to read/write file: {e}"
                    })
            else:
                errors.append({
                    "error": f"File not found: {validation.file_path}"
                })
        else:
            # Dry run - just count what would be applied
            for rec in approved_recs:
                if rec.original_content and rec.proposed_content:
                    applied_count += 1
                else:
                    skipped_count += 1

        result = {
            "success": True,
            "validation_id": validation_id,
            "applied_count": applied_count,
            "skipped_count": skipped_count,
            "errors": errors
        }

        if backup_path:
            result["backup_path"] = backup_path

        if dry_run:
            result["dry_run"] = True

        return result

    def delete_recommendation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Delete a recommendation.

        Args:
            params: {
                "recommendation_id": str (required)
            }

        Returns:
            {
                "success": bool,
                "recommendation_id": str
            }
        """
        self.validate_params(params, required=["recommendation_id"])

        recommendation_id = params["recommendation_id"]

        self.logger.info(f"Deleting recommendation: {recommendation_id}")

        # Check if exists
        recommendation = self.db_manager.get_recommendation(recommendation_id)
        if not recommendation:
            raise ValueError(f"Recommendation {recommendation_id} not found")

        # Delete
        success = self.db_manager.delete_recommendation(recommendation_id)

        if not success:
            raise RuntimeError(f"Failed to delete recommendation {recommendation_id}")

        return {
            "success": True,
            "recommendation_id": recommendation_id
        }

    def mark_recommendations_applied(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mark recommendations as applied.

        Args:
            params: {
                "recommendation_ids": List[str] (required)
            }

        Returns:
            {
                "success": bool,
                "marked_count": int,
                "errors": List[Dict]
            }
        """
        self.validate_params(params, required=["recommendation_ids"])

        recommendation_ids = params["recommendation_ids"]

        self.logger.info(f"Marking {len(recommendation_ids)} recommendations as applied")

        marked_count = 0
        errors = []

        for rec_id in recommendation_ids:
            try:
                # Check if recommendation exists
                rec = self.db_manager.get_recommendation(rec_id)
                if not rec:
                    errors.append({
                        "recommendation_id": rec_id,
                        "error": "Recommendation not found"
                    })
                    continue

                self.db_manager.update_recommendation_status(rec_id, "applied")
                marked_count += 1
            except Exception as e:
                errors.append({
                    "recommendation_id": rec_id,
                    "error": str(e)
                })

        return {
            "success": True,
            "marked_count": marked_count,
            "errors": errors
        }

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _serialize_recommendation(self, recommendation) -> Dict[str, Any]:
        """Serialize recommendation record to dictionary."""
        return {
            "id": recommendation.id,
            "validation_id": recommendation.validation_id,
            "type": recommendation.type,
            "title": recommendation.title,
            "description": recommendation.description,
            "scope": recommendation.scope,
            "instruction": recommendation.instruction,
            "rationale": recommendation.rationale,
            "severity": recommendation.severity,
            "original_content": recommendation.original_content,
            "proposed_content": recommendation.proposed_content,
            "diff": recommendation.diff,
            "confidence": recommendation.confidence,
            "priority": recommendation.priority,
            "status": recommendation.status.value if hasattr(recommendation.status, 'value') else str(recommendation.status),
            "reviewed_by": recommendation.reviewed_by,
            "reviewed_at": recommendation.reviewed_at.isoformat() if recommendation.reviewed_at else None,
            "review_notes": recommendation.review_notes,
            "applied_at": recommendation.applied_at.isoformat() if recommendation.applied_at else None,
            "applied_by": recommendation.applied_by,
            "metadata": recommendation.recommendation_metadata,
            "created_at": recommendation.created_at.isoformat() if recommendation.created_at else None,
            "updated_at": recommendation.updated_at.isoformat() if recommendation.updated_at else None
        }

    def _get_validation_by_id(self, validation_id: str):
        """Get validation by ID from database."""
        records = self.db_manager.list_validation_results(limit=10000)
        for record in records:
            if record.id == validation_id:
                return record
        return None
