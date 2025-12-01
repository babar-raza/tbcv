# file: agents/validators/yaml_validator.py
"""
YAML Validator Agent - Validates YAML frontmatter.
Uses ConfigLoader for configuration-driven validation.
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
from core.config_loader import ConfigLoader, get_config_loader
from core.logging import get_logger

logger = get_logger(__name__)


class YamlValidatorAgent(BaseValidatorAgent):
    """Validates YAML frontmatter in markdown files."""

    def __init__(self, agent_id: Optional[str] = None, config_loader: Optional[ConfigLoader] = None):
        super().__init__(agent_id or "yaml_validator")
        self._config_loader = config_loader or get_config_loader()
        self._config = self._config_loader.load("frontmatter")

    def get_validation_type(self) -> str:
        return "yaml"

    async def validate(self, content: str, context: Dict[str, Any]) -> ValidationResult:
        """Validate YAML frontmatter."""
        issues: List[ValidationIssue] = []
        auto_fixable = 0

        # Get profile and family from context
        profile = context.get("profile", self._config.profile)
        family = context.get("family")

        # Get active rules for this profile/family
        active_rules = self._config_loader.get_rules("frontmatter", profile=profile, family=family)
        active_rule_ids = {r.id for r in active_rules}
        rule_levels = {r.id: r.level for r in active_rules}

        # Extract YAML frontmatter
        try:
            post = frontmatter.loads(content)
            metadata = post.metadata
        except Exception as e:
            level = rule_levels.get("yaml_parse_error", "error")
            return ValidationResult(
                confidence=0.0,
                issues=[ValidationIssue(
                    level=level,
                    category="yaml_parse_error",
                    message=f"Failed to parse YAML frontmatter: {str(e)}",
                    suggestion="Check YAML syntax (indentation, quotes, colons)"
                )],
                metrics={"yaml_valid": False}
            )

        # Validate required fields (from config)
        if "required_title" in active_rule_ids:
            if "title" not in metadata or not metadata["title"]:
                level = rule_levels.get("required_title", "error")
                issues.append(ValidationIssue(
                    level=level,
                    category="yaml_missing_required",
                    message="Required field 'title' is missing",
                    suggestion="Add 'title' to YAML frontmatter"
                ))

        if "required_description" in active_rule_ids:
            if "description" not in metadata or not metadata["description"]:
                level = rule_levels.get("required_description", "warning")
                issues.append(ValidationIssue(
                    level=level,
                    category="yaml_missing_recommended",
                    message="Recommended field 'description' is missing",
                    suggestion="Add 'description' to YAML frontmatter for better SEO"
                ))

        # Validate field types (strings)
        if "field_type_string" in active_rule_ids:
            string_rule = next((r for r in active_rules if r.id == "field_type_string"), None)
            string_fields = string_rule.params.get("fields", ["title"]) if string_rule else ["title"]
            for field in string_fields:
                if field in metadata and not isinstance(metadata[field], str):
                    level = rule_levels.get("field_type_string", "error")
                    issues.append(ValidationIssue(
                        level=level,
                        category="yaml_invalid_type",
                        message=f"Field '{field}' must be a string",
                        suggestion=f"Wrap {field} value in quotes"
                    ))

        # Validate field types (lists)
        if "field_type_list" in active_rule_ids:
            list_rule = next((r for r in active_rules if r.id == "field_type_list"), None)
            list_fields = list_rule.params.get("fields", ["tags", "categories"]) if list_rule else ["tags", "categories"]
            for field in list_fields:
                if field in metadata and not isinstance(metadata[field], list):
                    level = rule_levels.get("field_type_list", "warning")
                    issues.append(ValidationIssue(
                        level=level,
                        category="yaml_invalid_type",
                        message=f"Field '{field}' should be a list",
                        suggestion=f"Use format: {field}: [item1, item2]"
                    ))

        # Validate date format if present
        if "field_type_date" in active_rule_ids:
            date_rule = next((r for r in active_rules if r.id == "field_type_date"), None)
            date_fields = date_rule.params.get("fields", ["date"]) if date_rule else ["date"]
            for field in date_fields:
                if field in metadata:
                    date_value = metadata[field]
                    if not isinstance(date_value, str):
                        level = rule_levels.get("field_type_date", "warning")
                        issues.append(ValidationIssue(
                            level=level,
                            category="yaml_invalid_date_format",
                            message=f"Field '{field}' should be a string in YYYY-MM-DD format",
                            suggestion=f"Use format: {field}: '2025-11-22'"
                        ))

        # Validate title length
        if "title_length" in active_rule_ids and "title" in metadata:
            title_rule = next((r for r in active_rules if r.id == "title_length"), None)
            if title_rule:
                min_len = title_rule.params.get("min_length", 10)
                max_len = title_rule.params.get("max_length", 100)
                title_len = len(str(metadata["title"]))
                if title_len < min_len:
                    level = rule_levels.get("title_length", "warning")
                    issues.append(ValidationIssue(
                        level=level,
                        category="yaml_title_too_short",
                        message=f"Title is too short ({title_len} chars, minimum: {min_len})",
                        suggestion=f"Add at least {min_len - title_len} more characters"
                    ))
                elif title_len > max_len:
                    level = rule_levels.get("title_length", "warning")
                    issues.append(ValidationIssue(
                        level=level,
                        category="yaml_title_too_long",
                        message=f"Title is too long ({title_len} chars, maximum: {max_len})",
                        suggestion=f"Shorten by at least {title_len - max_len} characters"
                    ))

        confidence = max(0.5, 1.0 - (len(issues) * 0.15))

        return ValidationResult(
            confidence=confidence,
            issues=issues,
            auto_fixable_count=auto_fixable,
            metrics={
                "yaml_valid": True,
                "fields_checked": len(metadata),
                "issues_count": len(issues),
                "profile": profile,
                "family": family
            }
        )
