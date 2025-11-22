# file: agents/validators/truth_validator.py
"""
Truth Validator Agent - Validates content against truth data.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional

from agents.validators.base_validator import (
    BaseValidatorAgent,
    ValidationIssue,
    ValidationResult
)
from agents.base import agent_registry
from core.logging import get_logger

logger = get_logger(__name__)


class TruthValidatorAgent(BaseValidatorAgent):
    """Validates content against truth data (plugin names, API patterns, etc.)."""

    def __init__(self, agent_id: Optional[str] = None):
        super().__init__(agent_id or "truth_validator")

    def get_validation_type(self) -> str:
        return "Truth"

    async def validate(self, content: str, context: Dict[str, Any]) -> ValidationResult:
        """Validate content against truth data."""
        issues: List[ValidationIssue] = []
        auto_fixable = 0
        family = context.get("family", "words")

        # Get truth manager
        truth_manager = agent_registry.get_agent("truth_manager")
        if not truth_manager:
            logger.warning("TruthManager not available for truth validation")
            return ValidationResult(
                confidence=0.0,
                issues=[ValidationIssue(
                    level="warning",
                    category="truth_manager_unavailable",
                    message="Truth validation unavailable (TruthManager not registered)",
                    suggestion="Ensure TruthManager is properly configured"
                )],
                metrics={"truth_data_loaded": False}
            )

        try:
            # Load truth data
            truth_result = await truth_manager.handle_load_truth_data({"family": family})
            plugin_aliases = truth_result.get("plugin_aliases", [])
            api_patterns = truth_result.get("api_patterns", [])
            truth_data = truth_result.get("truth_data", {})

            # Check for mentions of plugins that aren't in truth data
            plugin_issues = self._validate_plugin_mentions(
                content, plugin_aliases, truth_data
            )
            issues.extend(plugin_issues)

            # Check for API patterns
            api_issues = self._validate_api_patterns(content, api_patterns)
            issues.extend(api_issues)

            confidence = max(0.6, 1.0 - (len(issues) * 0.15))

            return ValidationResult(
                confidence=confidence,
                issues=issues,
                auto_fixable_count=auto_fixable,
                metrics={
                    "truth_data_loaded": True,
                    "known_plugins": len(plugin_aliases),
                    "api_patterns_count": len(api_patterns),
                    "issues_count": len(issues)
                }
            )

        except Exception as e:
            logger.error(f"Error validating truth data: {e}", exc_info=True)
            return ValidationResult(
                confidence=0.0,
                issues=[ValidationIssue(
                    level="error",
                    category="truth_validation_error",
                    message=f"Error during truth validation: {str(e)}",
                    suggestion="Check truth data files and configuration"
                )],
                metrics={"truth_data_loaded": False}
            )

    def _validate_plugin_mentions(
        self,
        content: str,
        known_plugins: List[str],
        truth_data: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """Validate that mentioned plugins exist in truth data."""
        issues = []

        # Convert content to lowercase for case-insensitive matching
        content_lower = content.lower()

        # Check each known plugin
        for plugin in known_plugins:
            plugin_lower = plugin.lower()

            # Check if plugin is mentioned
            if plugin_lower in content_lower:
                # Get plugin details from truth data
                plugin_details = None
                for key, data in truth_data.items():
                    if isinstance(data, dict):
                        name = data.get("name", "")
                        if name.lower() == plugin_lower:
                            plugin_details = data
                            break

                # If plugin details found, could add more validation here
                # For now, just logging that we found a known plugin
                logger.debug(f"Found known plugin mention: {plugin}")

        return issues

    def _validate_api_patterns(
        self,
        content: str,
        api_patterns: List[str]
    ) -> List[ValidationIssue]:
        """Validate API patterns mentioned in content."""
        issues = []

        # This is a basic implementation
        # Could be enhanced to check for outdated API patterns,
        # incorrect usage, etc.

        # For now, just validate that if API code is present,
        # it follows some basic patterns

        lines = content.split('\n')
        in_code_block = False

        for i, line in enumerate(lines):
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                continue

            if in_code_block:
                # Check for potential API usage patterns
                if 'new Document(' in line and ')' in line:
                    # This is a valid pattern, could add more checks
                    pass

        return issues
