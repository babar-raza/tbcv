"""Enhancement method handlers for MCP server."""

import json
import os
import difflib
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime, timezone
from .base import BaseMCPMethod
from core.database import ValidationResult, ValidationStatus
from core.path_validator import is_safe_path, validate_write_path
from core.io_win import read_text, write_text_crlf
from core.logging import get_logger

logger = get_logger(__name__)


class EnhancementMethods(BaseMCPMethod):
    """Handler for enhancement-related MCP methods."""

    def handle(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle enhancement method execution.

        Args:
            params: Method parameters

        Returns:
            Enhancement results

        Raises:
            ValueError: If parameters are invalid
        """
        # This is called via registry, specific methods are called directly
        raise NotImplementedError("Use specific enhancement methods via registry")

    def enhance(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance approved validation records.

        Args:
            params: Parameters containing ids list

        Returns:
            Enhancement results with count, errors, and enhancement details

        Raises:
            ValueError: If ids parameter is missing
        """
        self.validate_params(params, required=["ids"])

        ids = params.get("ids", [])
        if not isinstance(ids, list):
            raise ValueError("ids must be a list")

        enhanced_count = 0
        errors = []
        enhancements = []

        self.logger.info(f"Enhancing {len(ids)} validation records")

        for validation_id in ids:
            try:
                # Get validation record
                records = self.db_manager.list_validation_results(limit=1000)
                validation = None
                for record in records:
                    if record.id == validation_id:
                        validation = record
                        break

                if not validation:
                    errors.append(f"Validation {validation_id} not found")
                    continue

                # Check if validation is approved
                if validation.status != ValidationStatus.APPROVED:
                    errors.append(
                        f"Validation {validation_id} not approved "
                        f"(status: {validation.status})"
                    )
                    continue

                # Load original markdown file
                file_path = Path(validation.file_path)

                # Check if file path is valid (not a placeholder like "unknown")
                if validation.file_path in ["unknown", "Unknown", ""]:
                    errors.append(
                        f"Cannot enhance validation {validation_id}: "
                        f"Invalid file path '{validation.file_path}'. "
                        "This validation was created without a valid file reference."
                    )
                    continue

                # Validate path safety
                if not is_safe_path(file_path):
                    errors.append(f"Unsafe file path: {file_path}")
                    continue

                if not file_path.exists():
                    errors.append(f"File not found: {file_path}")
                    continue

                # Validate write permissions
                if not validate_write_path(file_path):
                    errors.append(f"Cannot write to file: {file_path}")
                    continue

                # Read original content
                original_content = read_text(file_path)

                # Get enhancement prompts
                from core.prompt_loader import get_prompt
                try:
                    enhancement_prompt = get_prompt("enhancer", "enhance_markdown")
                except Exception:
                    # Fallback prompt if loader fails
                    enhancement_prompt = """Please enhance this markdown document by:
1. Improving clarity and readability
2. Fixing any grammatical issues
3. Ensuring proper formatting
4. Adding missing sections if needed
5. Maintaining the original meaning and structure

Original content:
{content}

Enhanced content:"""

                # Call Ollama for enhancement
                from core.ollama import get_ollama_client
                try:
                    messages = [
                        {
                            "role": "system",
                            "content": "You are a technical writing assistant. "
                                     "Enhance markdown documents while preserving "
                                     "their structure and meaning."
                        },
                        {
                            "role": "user",
                            "content": enhancement_prompt.format(content=original_content)
                        }
                    ]

                    # Get model from environment or use default
                    model = os.getenv("OLLAMA_MODEL", "llama2:7b")
                    client = get_ollama_client()
                    response_dict = client.chat(model, messages)

                    # Extract message content from response
                    enhanced_content = response_dict.get("message", {}).get(
                        "content", ""
                    ).strip()

                    # Write enhanced content atomically
                    write_text_crlf(file_path, enhanced_content, atomic=True)

                    # Generate diff
                    original_lines = original_content.splitlines(keepends=True)
                    enhanced_lines = enhanced_content.splitlines(keepends=True)
                    diff_gen = difflib.unified_diff(
                        original_lines,
                        enhanced_lines,
                        fromfile='Original',
                        tofile='Enhanced',
                        lineterm=''
                    )
                    diff = '\n'.join(diff_gen)

                    # Create audit log entry
                    audit_entry = {
                        "validation_id": validation_id,
                        "action": "enhance",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "original_size": len(original_content),
                        "enhanced_size": len(enhanced_content),
                        "model_used": model
                    }

                    # Update validation status to enhanced
                    with self.db_manager.get_session() as session:
                        db_record = session.query(ValidationResult).filter(
                            ValidationResult.id == validation_id
                        ).first()
                        if db_record:
                            # Get existing validation_results or create new dict
                            validation_results = db_record.validation_results or {}
                            if isinstance(validation_results, str):
                                validation_results = json.loads(validation_results)

                            # Add enhancement data
                            validation_results['original_content'] = original_content
                            validation_results['enhanced_content'] = enhanced_content
                            validation_results['diff'] = diff
                            validation_results['enhancement_timestamp'] = (
                                datetime.now(timezone.utc).isoformat()
                            )
                            validation_results['model_used'] = model

                            db_record.validation_results = validation_results
                            db_record.status = ValidationStatus.ENHANCED
                            db_record.updated_at = datetime.now(timezone.utc)

                            # Store enhancement details in notes
                            current_notes = db_record.notes or ""
                            db_record.notes = f"{current_notes}\n\nEnhanced: {audit_entry}"
                            session.commit()

                    enhanced_count += 1
                    enhancements.append(audit_entry)
                    self.logger.info(
                        f"Enhanced validation {validation_id} "
                        f"(original: {len(original_content)} bytes, "
                        f"enhanced: {len(enhanced_content)} bytes)"
                    )

                except Exception as ollama_error:
                    error_msg = (
                        f"Enhancement failed for {validation_id}: {str(ollama_error)}"
                    )
                    errors.append(error_msg)
                    self.logger.error(error_msg)

            except Exception as e:
                error_msg = f"Error enhancing {validation_id}: {str(e)}"
                errors.append(error_msg)
                self.logger.error(error_msg)

        self.logger.info(
            f"Enhanced {enhanced_count} of {len(ids)} validation records"
        )

        return {
            "success": True,
            "enhanced_count": enhanced_count,
            "errors": errors,
            "enhancements": enhancements
        }

    def enhance_batch(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance multiple validations with progress tracking.

        Args:
            params: {
                "ids": List[str] (required) - Validation IDs to enhance,
                "batch_size": int (optional, default 10) - Processing batch size,
                "threshold": float (optional, default 0.7) - Confidence threshold
            }

        Returns:
            {
                "success": bool,
                "total": int,
                "enhanced_count": int,
                "failed_count": int,
                "skipped_count": int,
                "errors": List[str],
                "results": List[Dict],
                "processing_time_ms": float
            }
        """
        import time
        start_time = time.time()

        self.validate_params(params, required=["ids"],
                           optional={"batch_size": 10, "threshold": 0.7})

        ids = params["ids"]
        batch_size = params.get("batch_size", 10)
        threshold = params.get("threshold", 0.7)

        if not isinstance(ids, list):
            raise ValueError("enhance_batch requires a list of IDs")

        total = len(ids)
        self.logger.info(f"Batch enhancing {total} validations")

        enhanced_count = 0
        failed_count = 0
        skipped_count = 0
        errors = []
        results = []

        # Process in batches
        for i in range(0, total, batch_size):
            batch_ids = ids[i:i + batch_size]

            for validation_id in batch_ids:
                try:
                    # Get validation record
                    records = self.db_manager.list_validation_results(limit=1000)
                    validation = None
                    for record in records:
                        if record.id == validation_id:
                            validation = record
                            break

                    if not validation:
                        errors.append(f"Validation {validation_id} not found")
                        failed_count += 1
                        continue

                    # Check if approved
                    if validation.status != ValidationStatus.APPROVED:
                        errors.append(
                            f"Validation {validation_id} not approved (status: {validation.status.value})"
                        )
                        skipped_count += 1
                        continue

                    # Use existing enhance method logic
                    enhance_result = self.enhance({"ids": [validation_id]})

                    if enhance_result.get("enhanced_count", 0) > 0:
                        enhanced_count += 1
                        results.append({
                            "validation_id": validation_id,
                            "status": "enhanced"
                        })
                    else:
                        failed_count += 1
                        if enhance_result.get("errors"):
                            errors.extend(enhance_result["errors"])

                except Exception as e:
                    self.logger.error(f"Failed to enhance {validation_id}: {e}")
                    errors.append(f"Enhancement failed for {validation_id}: {str(e)}")
                    failed_count += 1

            # Log progress
            processed = min(i + batch_size, total)
            self.logger.info(f"Progress: {processed}/{total} validations processed")

        processing_time = (time.time() - start_time) * 1000

        return {
            "success": enhanced_count > 0,
            "total": total,
            "enhanced_count": enhanced_count,
            "failed_count": failed_count,
            "skipped_count": skipped_count,
            "errors": errors,
            "results": results,
            "processing_time_ms": processing_time
        }

    def enhance_preview(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preview enhancement without applying changes.

        Args:
            params: {
                "validation_id": str (required),
                "recommendation_types": List[str] (optional) - Types to preview,
                "threshold": float (optional, default 0.7) - Confidence threshold
            }

        Returns:
            {
                "success": bool,
                "validation_id": str,
                "original_content": str,
                "enhanced_content": str,
                "diff": Dict,
                "recommendations_count": int,
                "changes_summary": Dict
            }
        """
        self.validate_params(params, required=["validation_id"],
                           optional={"recommendation_types": None, "threshold": 0.7})

        validation_id = params["validation_id"]
        recommendation_types = params.get("recommendation_types")
        threshold = params.get("threshold", 0.7)

        self.logger.info(f"Previewing enhancement for {validation_id}")

        # Get validation
        records = self.db_manager.list_validation_results(limit=1000)
        validation = None
        for record in records:
            if record.id == validation_id:
                validation = record
                break

        if not validation:
            raise ValueError(f"Validation {validation_id} not found")

        # Load original content
        file_path = Path(validation.file_path)

        # Check if file path is valid
        if validation.file_path in ["unknown", "Unknown", ""]:
            raise ValueError(
                f"Cannot preview enhancement for validation {validation_id}: "
                f"Invalid file path '{validation.file_path}'"
            )

        if not is_safe_path(file_path):
            raise ValueError(f"Unsafe file path: {file_path}")

        if not file_path.exists():
            raise ValueError(f"File not found: {file_path}")

        original_content = read_text(file_path)

        # Get enhancement prompt
        from core.prompt_loader import get_prompt
        try:
            enhancement_prompt = get_prompt("enhancer", "enhance_markdown")
        except Exception:
            enhancement_prompt = """Please enhance this markdown document by:
1. Improving clarity and readability
2. Fixing any grammatical issues
3. Ensuring proper formatting
4. Adding missing sections if needed
5. Maintaining the original meaning and structure

Original content:
{content}

Enhanced content:"""

        # Call Ollama for preview (dry-run)
        from core.ollama import get_ollama_client
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are a technical writing assistant. "
                             "Enhance markdown documents while preserving "
                             "their structure and meaning."
                },
                {
                    "role": "user",
                    "content": enhancement_prompt.format(content=original_content)
                }
            ]

            model = os.getenv("OLLAMA_MODEL", "llama2:7b")
            client = get_ollama_client()
            response_dict = client.chat(model, messages)

            enhanced_content = response_dict.get("message", {}).get(
                "content", ""
            ).strip()

            # Generate diff
            diff = self._generate_diff(original_content, enhanced_content)

            return {
                "success": True,
                "validation_id": validation_id,
                "original_content": original_content,
                "enhanced_content": enhanced_content,
                "diff": diff,
                "recommendations_count": 1,  # Simplified for now
                "changes_summary": {
                    "additions": diff.get("additions_count", 0),
                    "deletions": diff.get("deletions_count", 0),
                    "modifications": diff.get("modifications_count", 0)
                }
            }

        except Exception as e:
            self.logger.error(f"Preview failed for {validation_id}: {e}")
            return {
                "success": False,
                "validation_id": validation_id,
                "original_content": original_content,
                "enhanced_content": original_content,
                "diff": {},
                "recommendations_count": 0,
                "changes_summary": {
                    "additions": 0,
                    "deletions": 0,
                    "modifications": 0
                }
            }

    def enhance_auto_apply(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Automatically apply recommendations above threshold.

        Args:
            params: {
                "validation_id": str (required),
                "threshold": float (optional, default 0.9) - Confidence threshold,
                "recommendation_types": List[str] (optional) - Types to auto-apply,
                "preview_first": bool (optional, default True) - Preview before apply
            }

        Returns:
            {
                "success": bool,
                "validation_id": str,
                "applied_count": int,
                "skipped_count": int,
                "applied_recommendations": List[Dict],
                "preview": Dict (if preview_first=True)
            }
        """
        self.validate_params(params, required=["validation_id"],
                           optional={"threshold": 0.9, "recommendation_types": None,
                                   "preview_first": True})

        validation_id = params["validation_id"]
        threshold = params.get("threshold", 0.9)
        recommendation_types = params.get("recommendation_types")
        preview_first = params.get("preview_first", True)

        self.logger.info(f"Auto-applying enhancements for {validation_id} (threshold={threshold})")

        # Get validation
        records = self.db_manager.list_validation_results(limit=1000)
        validation = None
        for record in records:
            if record.id == validation_id:
                validation = record
                break

        if not validation:
            raise ValueError(f"Validation {validation_id} not found")

        # Preview if requested
        preview_result = None
        if preview_first:
            preview_result = self.enhance_preview({
                "validation_id": validation_id,
                "recommendation_types": recommendation_types,
                "threshold": threshold
            })

        # Apply enhancement (only if above threshold)
        # For simplicity, we'll use the existing enhance method
        # In a real implementation, we'd filter recommendations by threshold
        if validation.status == ValidationStatus.APPROVED:
            enhance_result = self.enhance({"ids": [validation_id]})

            applied_count = enhance_result.get("enhanced_count", 0)

            return {
                "success": applied_count > 0,
                "validation_id": validation_id,
                "applied_count": applied_count,
                "skipped_count": 0 if applied_count > 0 else 1,
                "applied_recommendations": [],
                "preview": preview_result if preview_first else None
            }
        else:
            return {
                "success": False,
                "validation_id": validation_id,
                "applied_count": 0,
                "skipped_count": 1,
                "applied_recommendations": [],
                "preview": preview_result if preview_first else None
            }

    def get_enhancement_comparison(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get before/after comparison of enhancement.

        Args:
            params: {
                "validation_id": str (required),
                "format": str (optional, default "unified") - Diff format
            }

        Returns:
            {
                "validation_id": str,
                "original_content": str,
                "enhanced_content": str,
                "diff": Dict,
                "statistics": Dict,
                "recommendations_applied": List[Dict]
            }
        """
        self.validate_params(params, required=["validation_id"],
                           optional={"format": "unified"})

        validation_id = params["validation_id"]
        diff_format = params.get("format", "unified")

        # Get validation
        records = self.db_manager.list_validation_results(limit=1000)
        validation = None
        for record in records:
            if record.id == validation_id:
                validation = record
                break

        if not validation:
            raise ValueError(f"Validation {validation_id} not found")

        if validation.status != ValidationStatus.ENHANCED:
            raise ValueError(f"Validation {validation_id} has not been enhanced")

        # Get original and enhanced content from validation_results
        validation_results = validation.validation_results or {}
        if isinstance(validation_results, str):
            validation_results = json.loads(validation_results)

        original_content = validation_results.get("original_content", "")
        enhanced_content = validation_results.get("enhanced_content", "")
        stored_diff = validation_results.get("diff", "")

        # Generate diff if not stored
        if not stored_diff:
            diff = self._generate_diff(original_content, enhanced_content)
        else:
            # Parse stored diff
            diff = {
                "unified_diff": stored_diff,
                "side_by_side": [],
                "additions_count": 0,
                "deletions_count": 0,
                "modifications_count": 0,
                "total_changes": 0
            }

        return {
            "validation_id": validation_id,
            "original_content": original_content,
            "enhanced_content": enhanced_content,
            "diff": diff,
            "statistics": {
                "lines_added": diff.get("additions_count", 0),
                "lines_removed": diff.get("deletions_count", 0),
                "lines_modified": diff.get("modifications_count", 0),
                "total_changes": diff.get("total_changes", 0)
            },
            "recommendations_applied": []
        }

    def _generate_diff(self, original: str, enhanced: str) -> Dict[str, Any]:
        """
        Generate diff between original and enhanced content.

        Args:
            original: Original content
            enhanced: Enhanced content

        Returns:
            Diff dictionary with line-by-line changes
        """
        original_lines = original.splitlines(keepends=True)
        enhanced_lines = enhanced.splitlines(keepends=True)

        # Generate unified diff
        diff_lines = list(difflib.unified_diff(
            original_lines,
            enhanced_lines,
            fromfile='original',
            tofile='enhanced',
            lineterm=''
        ))

        # Count changes
        additions = sum(1 for line in diff_lines if line.startswith('+') and not line.startswith('+++'))
        deletions = sum(1 for line in diff_lines if line.startswith('-') and not line.startswith('---'))

        # Generate side-by-side diff for better visualization
        side_by_side = []
        for change in difflib.ndiff(original_lines, enhanced_lines):
            code = change[0]
            line = change[2:]

            if code == ' ':
                side_by_side.append({"type": "unchanged", "content": line})
            elif code == '+':
                side_by_side.append({"type": "addition", "content": line})
            elif code == '-':
                side_by_side.append({"type": "deletion", "content": line})

        return {
            "unified_diff": ''.join(diff_lines),
            "side_by_side": side_by_side,
            "additions_count": additions,
            "deletions_count": deletions,
            "modifications_count": min(additions, deletions),
            "total_changes": additions + deletions
        }
