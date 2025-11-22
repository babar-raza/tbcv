# file: agents/validators/yaml_validator.py
"""
YAML Validator Agent - Validates YAML frontmatter.
"""

from __future__ import annotations
import yaml
import frontmatter
from typing import Dict, Any, List, Optional

from agents.validators.base_validator import (
    BaseValidatorAgent,
    ValidationIssue,
    ValidationResult
)
from core.logging import get_logger

logger = get_logger(__name__)


class YamlValidatorAgent(BaseValidatorAgent):
    """Validates YAML frontmatter in markdown files."""

    def __init__(self, agent_id: Optional[str] = None):
        super().__init__(agent_id or "yaml_validator")

    def get_validation_type(self) -> str:
        return "yaml"

    async def validate(self, content: str, context: Dict[str, Any]) -> ValidationResult:
        """Validate YAML frontmatter."""
        issues: List[ValidationIssue] = []
        auto_fixable = 0

        # Extract YAML frontmatter
        try:
            post = frontmatter.loads(content)
            metadata = post.metadata
        except Exception as e:
            return ValidationResult(
                confidence=0.0,
                issues=[ValidationIssue(
                    level="error",
                    category="yaml_parse_error",
                    message=f"Failed to parse YAML frontmatter: {str(e)}",
                    suggestion="Check YAML syntax (indentation, quotes, colons)"
                )],
                metrics={"yaml_valid": False}
            )

        # Validate required fields
        required_fields = ["title"]  # Could be from config
        for field in required_fields:
            if field not in metadata or not metadata[field]:
                issues.append(ValidationIssue(
                    level="error",
                    category="yaml_missing_required",
                    message=f"Required field '{field}' is missing",
                    suggestion=f"Add '{field}' to YAML frontmatter"
                ))

        # Validate field types
        if "title" in metadata and not isinstance(metadata["title"], str):
            issues.append(ValidationIssue(
                level="error",
                category="yaml_invalid_type",
                message="Field 'title' must be a string",
                suggestion="Wrap title value in quotes"
            ))

        # Validate date format if present
        if "date" in metadata:
            date_value = metadata["date"]
            if not isinstance(date_value, str):
                issues.append(ValidationIssue(
                    level="warning",
                    category="yaml_invalid_date_format",
                    message="Field 'date' should be a string in YYYY-MM-DD format",
                    suggestion="Use format: date: '2025-11-22'"
                ))

        # Validate tags/categories are lists if present
        for list_field in ["tags", "categories"]:
            if list_field in metadata:
                if not isinstance(metadata[list_field], list):
                    issues.append(ValidationIssue(
                        level="warning",
                        category="yaml_invalid_type",
                        message=f"Field '{list_field}' should be a list",
                        suggestion=f"Use format: {list_field}: [item1, item2]"
                    ))

        confidence = max(0.5, 1.0 - (len(issues) * 0.15))

        return ValidationResult(
            confidence=confidence,
            issues=issues,
            auto_fixable_count=auto_fixable,
            metrics={
                "yaml_valid": True,
                "fields_checked": len(metadata),
                "issues_count": len(issues)
            }
        )
