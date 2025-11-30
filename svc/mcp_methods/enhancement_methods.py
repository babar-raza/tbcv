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
