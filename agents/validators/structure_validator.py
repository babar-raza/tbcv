# file: agents/validators/structure_validator.py
"""
Structure Validator Agent - Validates document structure.
Uses ConfigLoader for configuration-driven validation.
"""

from __future__ import annotations
import re
from typing import Dict, Any, List, Optional

from agents.validators.base_validator import (
    BaseValidatorAgent,
    ValidationIssue,
    ValidationResult
)
from core.config_loader import ConfigLoader, get_config_loader
from core.logging import get_logger

logger = get_logger(__name__)


class StructureValidatorAgent(BaseValidatorAgent):
    """Validates document structure and organization."""

    def __init__(self, agent_id: Optional[str] = None, config_loader: Optional[ConfigLoader] = None):
        super().__init__(agent_id or "structure_validator")
        self._config_loader = config_loader or get_config_loader()
        self._config = self._config_loader.load("structure")

    def get_validation_type(self) -> str:
        return "structure"

    async def validate(self, content: str, context: Dict[str, Any]) -> ValidationResult:
        """Validate document structure."""
        issues: List[ValidationIssue] = []
        auto_fixable = 0
        lines = content.split('\n')

        # Get profile and family from context
        profile = context.get("profile", self._config.profile)
        family = context.get("family")

        # Get active rules for this profile/family
        active_rules = self._config_loader.get_rules("structure", profile=profile, family=family)
        active_rule_ids = {r.id for r in active_rules}
        rule_levels = {r.id: r.level for r in active_rules}
        rule_params = {r.id: r.params for r in active_rules}

        # Check content length
        length_issues = self._check_content_length(content, active_rule_ids, rule_levels, rule_params)
        issues.extend(length_issues)

        # Check heading structure
        heading_issues = self._check_heading_structure(lines, active_rule_ids, rule_levels, rule_params)
        issues.extend(heading_issues)

        # Check for common structural problems
        structure_issues = self._check_structure_issues(lines, active_rule_ids, rule_levels, rule_params)
        issues.extend(structure_issues)

        confidence = max(0.6, 1.0 - (len(issues) * 0.1))

        return ValidationResult(
            confidence=confidence,
            issues=issues,
            auto_fixable_count=auto_fixable,
            metrics={
                "lines_count": len(lines),
                "character_count": len(content),
                "issues_count": len(issues),
                "profile": profile,
                "family": family
            }
        )

    def _check_content_length(
        self,
        content: str,
        active_rule_ids: set,
        rule_levels: Dict[str, str],
        rule_params: Dict[str, Dict]
    ) -> List[ValidationIssue]:
        """Check if content length is appropriate."""
        issues = []
        char_count = len(content)
        word_count = len(content.split())

        # Check for very short content
        if "content_too_short" in active_rule_ids:
            params = rule_params.get("content_too_short", {})
            min_chars = params.get("min_chars", 100)
            if char_count < min_chars:
                level = rule_levels.get("content_too_short", "warning")
                issues.append(ValidationIssue(
                    level=level,
                    category="structure_content_too_short",
                    message=f"Content is very short ({char_count} characters)",
                    suggestion="Add more content to provide value to readers"
                ))

        # Check for very long content
        if "content_too_long" in active_rule_ids:
            params = rule_params.get("content_too_long", {})
            max_chars = params.get("max_chars", 50000)
            if char_count > max_chars:
                level = rule_levels.get("content_too_long", "info")
                issues.append(ValidationIssue(
                    level=level,
                    category="structure_content_too_long",
                    message=f"Content is very long ({char_count} characters, ~{word_count} words)",
                    suggestion="Consider breaking into multiple documents"
                ))

        return issues

    def _check_heading_structure(
        self,
        lines: List[str],
        active_rule_ids: set,
        rule_levels: Dict[str, str],
        rule_params: Dict[str, Dict]
    ) -> List[ValidationIssue]:
        """Check heading organization."""
        issues = []
        headings = []

        # Extract headings
        for i, line in enumerate(lines):
            match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                headings.append({
                    'line': i + 1,
                    'level': level,
                    'text': text
                })

        # Check for documents without headings
        if "no_headings" in active_rule_ids and not headings:
            level = rule_levels.get("no_headings", "warning")
            issues.append(ValidationIssue(
                level=level,
                category="structure_no_headings",
                message="Document has no headings",
                suggestion="Add headings to organize content"
            ))
            return issues

        # Check for too many top-level headings
        if "too_many_h1" in active_rule_ids:
            params = rule_params.get("too_many_h1", {})
            max_h1 = params.get("max_h1", 3)
            h1_count = sum(1 for h in headings if h['level'] == 1)
            if h1_count > max_h1:
                level = rule_levels.get("too_many_h1", "warning")
                issues.append(ValidationIssue(
                    level=level,
                    category="structure_too_many_h1",
                    message=f"Document has {h1_count} H1 headings",
                    suggestion="Consider using H2-H6 for subsections"
                ))

        # Check for sections without content
        if "empty_section" in active_rule_ids:
            params = rule_params.get("empty_section", {})
            min_lines = params.get("min_lines_between_headings", 2)
            for i in range(len(headings) - 1):
                current = headings[i]
                next_heading = headings[i + 1]

                # Calculate lines between headings
                lines_between = next_heading['line'] - current['line'] - 1

                if lines_between < min_lines:  # Headings with no/minimal content
                    level = rule_levels.get("empty_section", "warning")
                    issues.append(ValidationIssue(
                        level=level,
                        category="structure_empty_section",
                        message=f"Section '{current['text']}' (line {current['line']}) has no content",
                        line_number=current['line'],
                        suggestion="Add content or remove the heading"
                    ))

        return issues

    def _check_structure_issues(
        self,
        lines: List[str],
        active_rule_ids: set,
        rule_levels: Dict[str, str],
        rule_params: Dict[str, Dict]
    ) -> List[ValidationIssue]:
        """Check for common structural issues."""
        issues = []

        # Check for content before first heading
        if "long_preamble" in active_rule_ids:
            first_heading_line = None
            for i, line in enumerate(lines):
                if re.match(r'^#{1,6}\s+.+$', line.strip()):
                    first_heading_line = i
                    break

            if first_heading_line is not None and first_heading_line > 0:
                # Check if there's substantive content before first heading
                preamble = '\n'.join(lines[:first_heading_line]).strip()
                params = rule_params.get("long_preamble", {})
                max_preamble = params.get("max_preamble_chars", 200)
                if len(preamble) > max_preamble:
                    level = rule_levels.get("long_preamble", "info")
                    issues.append(ValidationIssue(
                        level=level,
                        category="structure_long_preamble",
                        message="Long content before first heading",
                        suggestion="Consider adding an introductory heading"
                    ))

        # Check for consecutive headings (no content between)
        if "consecutive_headings" in active_rule_ids:
            prev_was_heading = False
            for i, line in enumerate(lines):
                is_heading = bool(re.match(r'^#{1,6}\s+.+$', line.strip()))

                if is_heading and prev_was_heading:
                    level = rule_levels.get("consecutive_headings", "warning")
                    issues.append(ValidationIssue(
                        level=level,
                        category="structure_consecutive_headings",
                        message=f"Consecutive headings at line {i + 1}",
                        line_number=i + 1,
                        suggestion="Add content between headings or merge them"
                    ))

                prev_was_heading = is_heading

        return issues
