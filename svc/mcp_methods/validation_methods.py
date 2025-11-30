"""Validation method handlers for MCP server."""

from typing import Dict, Any
from pathlib import Path
from .base import BaseMCPMethod
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
