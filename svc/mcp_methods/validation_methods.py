"""Validation method handlers for MCP server."""

import os
import tempfile
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime, timezone
from .base import BaseMCPMethod
from core.database import ValidationResult, ValidationStatus
from core.logging import get_logger

logger = get_logger(__name__)


class ValidationMethods(BaseMCPMethod):
    """Handler for validation-related MCP methods."""

    def handle(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle validation method execution.

        Args:
            params: Method parameters

        Returns:
            Validation results

        Raises:
            ValueError: If parameters are invalid
        """
        # This is called via registry, specific methods are called directly
        raise NotImplementedError("Use specific validation methods via registry")

    def validate_folder(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate all markdown files in a folder.

        Args:
            params: Parameters containing folder_path and optional recursive flag

        Returns:
            Validation results with success status and file count

        Raises:
            ValueError: If folder_path is missing
        """
        self.validate_params(params, required=["folder_path"])

        folder_path = params.get("folder_path")
        recursive = params.get("recursive", True)

        self.logger.info(f"Validating folder: {folder_path} (recursive={recursive})")

        # Run ingestion using the MarkdownIngestion instance
        from core.ingestion import MarkdownIngestion
        ingestion = MarkdownIngestion(self.db_manager, self.rule_manager)
        results = ingestion.ingest_folder(folder_path, recursive=recursive)

        self.logger.info(f"Validated {results['files_processed']} files")

        return {
            "success": True,
            "message": f"Validated {results['files_processed']} files",
            "results": results
        }

    def validate_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a single file.

        Args:
            params: {
                "file_path": str (required),
                "family": str (optional, default "words"),
                "validation_types": List[str] (optional)
            }

        Returns:
            {
                "success": bool,
                "validation_id": str,
                "status": str,
                "issues": List[Dict],
                "file_path": str
            }

        Raises:
            ValueError: If file not found or parameters invalid
        """
        self.validate_params(
            params,
            required=["file_path"],
            optional={"family": "words", "validation_types": None}
        )

        file_path = params["file_path"]
        family = params["family"]
        validation_types = params["validation_types"]

        # Validate file exists
        if not Path(file_path).exists():
            raise ValueError(f"File not found: {file_path}")

        self.logger.info(f"Validating file: {file_path}")

        # Run ingestion on single file
        from core.ingestion import MarkdownIngestion
        ingestion = MarkdownIngestion(self.db_manager, self.rule_manager)

        # Process single file (uses internal _process_file method)
        file_result = ingestion._process_file(Path(file_path))

        # Always create a new validation record for each validation request
        validation = self.db_manager.create_validation_result(
            file_path=file_path,
            rules_applied=validation_types or [],
            validation_results=file_result,
            notes="Validated via MCP",
            severity=self._determine_severity(file_result),
            status=ValidationStatus.PASS,
            content="",
            validation_types=validation_types or []
        )

        # Extract issues from validation results
        issues = []
        if isinstance(validation.validation_results, dict):
            issues = validation.validation_results.get("issues", [])

        return {
            "success": True,
            "validation_id": validation.id,
            "status": validation.status.value,
            "issues": issues,
            "file_path": file_path
        }

    def validate_content(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate content string.

        Args:
            params: {
                "content": str (required),
                "file_path": str (optional, default "temp.md"),
                "validation_types": List[str] (optional)
            }

        Returns:
            {
                "success": bool,
                "validation_id": str,
                "status": str,
                "issues": List[Dict]
            }

        Raises:
            ValueError: If content parameter is missing
        """
        self.validate_params(
            params,
            required=["content"],
            optional={"file_path": "temp.md", "validation_types": None}
        )

        content = params["content"]
        file_path = params["file_path"]
        validation_types = params["validation_types"]

        self.logger.info(f"Validating content for virtual path: {file_path}")

        # Create temp file for validation
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # Run validation on temp file
            from core.ingestion import MarkdownIngestion
            ingestion = MarkdownIngestion(self.db_manager, self.rule_manager)
            file_result = ingestion._process_file(Path(tmp_path))

            # Store in database with virtual path
            validation = self.db_manager.create_validation_result(
                file_path=file_path,
                rules_applied=validation_types or [],
                validation_results=file_result,
                notes="Content validation via MCP",
                severity=self._determine_severity(file_result),
                status=ValidationStatus.PASS,
                content=content,
                validation_types=validation_types or []
            )

            # Extract issues
            issues = []
            if isinstance(file_result, dict):
                issues = file_result.get("issues", [])

            return {
                "success": True,
                "validation_id": validation.id,
                "status": validation.status.value,
                "issues": issues
            }

        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except Exception as e:
                self.logger.warning(f"Failed to delete temp file {tmp_path}: {e}")

    def get_validation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get validation by ID.

        Args:
            params: {
                "validation_id": str (required)
            }

        Returns:
            {
                "validation": Dict (validation record)
            }

        Raises:
            ValueError: If validation not found
        """
        self.validate_params(params, required=["validation_id"])

        validation_id = params["validation_id"]

        # Get all validation records and find the one we need
        records = self.db_manager.list_validation_results(limit=10000)
        validation = None
        for record in records:
            if record.id == validation_id:
                validation = record
                break

        if not validation:
            raise ValueError(f"Validation {validation_id} not found")

        return {
            "validation": self._serialize_validation(validation)
        }

    def list_validations(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        List validations with filters.

        Args:
            params: {
                "limit": int (optional, default 100),
                "offset": int (optional, default 0),
                "status": str (optional),
                "file_path": str (optional)
            }

        Returns:
            {
                "validations": List[Dict],
                "total": int
            }
        """
        self.validate_params(
            params,
            required=[],
            optional={"limit": 100, "offset": 0, "status": None, "file_path": None}
        )

        limit = params["limit"]
        offset = params["offset"]
        status = params["status"]
        file_path = params["file_path"]

        # Get validations from database
        all_validations = self.db_manager.list_validation_results(limit=10000)

        # Apply filters
        filtered = all_validations
        if status:
            filtered = [v for v in filtered if v.status.value == status]
        if file_path:
            filtered = [v for v in filtered if v.file_path == file_path]

        # Apply pagination
        total = len(filtered)
        paginated = filtered[offset:offset + limit]

        return {
            "validations": [self._serialize_validation(v) for v in paginated],
            "total": total
        }

    def update_validation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update validation metadata.

        Args:
            params: {
                "validation_id": str (required),
                "notes": str (optional),
                "status": str (optional)
            }

        Returns:
            {
                "success": bool,
                "validation_id": str
            }

        Raises:
            ValueError: If validation not found
        """
        self.validate_params(
            params,
            required=["validation_id"],
            optional={"notes": None, "status": None}
        )

        validation_id = params["validation_id"]
        notes = params["notes"]
        status = params["status"]

        # Verify validation exists
        records = self.db_manager.list_validation_results(limit=10000)
        validation = None
        for record in records:
            if record.id == validation_id:
                validation = record
                break

        if not validation:
            raise ValueError(f"Validation {validation_id} not found")

        # Update fields
        with self.db_manager.get_session() as session:
            db_record = session.query(ValidationResult).filter(
                ValidationResult.id == validation_id
            ).first()

            if db_record:
                if notes is not None:
                    db_record.notes = notes
                if status is not None:
                    # Convert string to enum
                    try:
                        db_record.status = ValidationStatus[status.upper()]
                    except KeyError:
                        raise ValueError(f"Invalid status: {status}")

                db_record.updated_at = datetime.now(timezone.utc)
                session.commit()

        self.logger.info(f"Updated validation {validation_id}")

        return {
            "success": True,
            "validation_id": validation_id
        }

    def delete_validation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Delete validation record.

        Args:
            params: {
                "validation_id": str (required)
            }

        Returns:
            {
                "success": bool,
                "validation_id": str
            }
        """
        self.validate_params(params, required=["validation_id"])

        validation_id = params["validation_id"]

        with self.db_manager.get_session() as session:
            db_record = session.query(ValidationResult).filter(
                ValidationResult.id == validation_id
            ).first()

            if db_record:
                session.delete(db_record)
                session.commit()
                self.logger.info(f"Deleted validation {validation_id}")

        return {
            "success": True,
            "validation_id": validation_id
        }

    def revalidate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Re-run validation for a file.

        Args:
            params: {
                "validation_id": str (required)
            }

        Returns:
            {
                "success": bool,
                "new_validation_id": str,
                "original_validation_id": str
            }

        Raises:
            ValueError: If validation not found
        """
        self.validate_params(params, required=["validation_id"])

        validation_id = params["validation_id"]

        # Get original validation
        records = self.db_manager.list_validation_results(limit=10000)
        validation = None
        for record in records:
            if record.id == validation_id:
                validation = record
                break

        if not validation:
            raise ValueError(f"Validation {validation_id} not found")

        # Re-run validation on same file
        result = self.validate_file({
            "file_path": validation.file_path,
            "validation_types": validation.validation_types or []
        })

        self.logger.info(
            f"Revalidated {validation.file_path}: "
            f"original={validation_id}, new={result['validation_id']}"
        )

        return {
            "success": True,
            "new_validation_id": result["validation_id"],
            "original_validation_id": validation_id
        }

    # Helper methods

    def _serialize_validation(self, validation: ValidationResult) -> Dict[str, Any]:
        """Serialize validation record to dictionary."""
        return {
            "id": validation.id,
            "file_path": validation.file_path,
            "status": validation.status.value if isinstance(validation.status, ValidationStatus) else validation.status,
            "severity": validation.severity,
            "rules_applied": validation.rules_applied,
            "validation_results": validation.validation_results,
            "validation_types": validation.validation_types,
            "notes": validation.notes,
            "created_at": validation.created_at.isoformat() if validation.created_at else None,
            "updated_at": validation.updated_at.isoformat() if validation.updated_at else None
        }

    def _determine_severity(self, results: Dict[str, Any]) -> str:
        """
        Determine severity level from validation results.

        Args:
            results: Validation results dictionary

        Returns:
            Severity level string (error, warning, info)
        """
        if not isinstance(results, dict):
            return "info"

        issues = results.get("issues", [])
        if not issues:
            return "info"

        # Check for errors
        for issue in issues:
            if isinstance(issue, dict):
                severity = issue.get("severity", "").lower()
                if severity in ["error", "critical"]:
                    return "error"

        # Check for warnings
        for issue in issues:
            if isinstance(issue, dict):
                severity = issue.get("severity", "").lower()
                if severity == "warning":
                    return "warning"

        return "info"
