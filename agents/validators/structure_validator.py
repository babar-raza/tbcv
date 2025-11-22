# file: agents/validators/structure_validator.py
"""
Structure Validator Agent - Validates document structure.
"""

from __future__ import annotations
import re
from typing import Dict, Any, List, Optional

from agents.validators.base_validator import (
    BaseValidatorAgent,
    ValidationIssue,
    ValidationResult
)
from core.logging import get_logger

logger = get_logger(__name__)


class StructureValidatorAgent(BaseValidatorAgent):
    """Validates document structure and organization."""

    def __init__(self, agent_id: Optional[str] = None):
        super().__init__(agent_id or "structure_validator")

    def get_validation_type(self) -> str:
        return "structure"

    async def validate(self, content: str, context: Dict[str, Any]) -> ValidationResult:
        """Validate document structure."""
        issues: List[ValidationIssue] = []
        auto_fixable = 0
        lines = content.split('\n')

        # Check content length
        length_issues = self._check_content_length(content)
        issues.extend(length_issues)

        # Check heading structure
        heading_issues = self._check_heading_structure(lines)
        issues.extend(heading_issues)

        # Check for common structural problems
        structure_issues = self._check_structure_issues(lines)
        issues.extend(structure_issues)

        confidence = max(0.6, 1.0 - (len(issues) * 0.1))

        return ValidationResult(
            confidence=confidence,
            issues=issues,
            auto_fixable_count=auto_fixable,
            metrics={
                "lines_count": len(lines),
                "character_count": len(content),
                "issues_count": len(issues)
            }
        )

    def _check_content_length(self, content: str) -> List[ValidationIssue]:
        """Check if content length is appropriate."""
        issues = []
        char_count = len(content)
        word_count = len(content.split())

        # Check for very short content
        if char_count < 100:
            issues.append(ValidationIssue(
                level="warning",
                category="structure_content_too_short",
                message=f"Content is very short ({char_count} characters)",
                suggestion="Add more content to provide value to readers"
            ))

        # Check for very long content
        if char_count > 50000:
            issues.append(ValidationIssue(
                level="info",
                category="structure_content_too_long",
                message=f"Content is very long ({char_count} characters, ~{word_count} words)",
                suggestion="Consider breaking into multiple documents"
            ))

        return issues

    def _check_heading_structure(self, lines: List[str]) -> List[ValidationIssue]:
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
        if not headings:
            issues.append(ValidationIssue(
                level="warning",
                category="structure_no_headings",
                message="Document has no headings",
                suggestion="Add headings to organize content"
            ))
            return issues

        # Check for too many top-level headings
        h1_count = sum(1 for h in headings if h['level'] == 1)
        if h1_count > 3:
            issues.append(ValidationIssue(
                level="warning",
                category="structure_too_many_h1",
                message=f"Document has {h1_count} H1 headings",
                suggestion="Consider using H2-H6 for subsections"
            ))

        # Check for sections without content
        for i in range(len(headings) - 1):
            current = headings[i]
            next_heading = headings[i + 1]

            # Calculate lines between headings
            lines_between = next_heading['line'] - current['line'] - 1

            if lines_between < 2:  # Headings with no/minimal content
                issues.append(ValidationIssue(
                    level="warning",
                    category="structure_empty_section",
                    message=f"Section '{current['text']}' (line {current['line']}) has no content",
                    line_number=current['line'],
                    suggestion="Add content or remove the heading"
                ))

        return issues

    def _check_structure_issues(self, lines: List[str]) -> List[ValidationIssue]:
        """Check for common structural issues."""
        issues = []

        # Check for content before first heading
        first_heading_line = None
        for i, line in enumerate(lines):
            if re.match(r'^#{1,6}\s+.+$', line.strip()):
                first_heading_line = i
                break

        if first_heading_line is not None and first_heading_line > 0:
            # Check if there's substantive content before first heading
            preamble = '\n'.join(lines[:first_heading_line]).strip()
            if len(preamble) > 200:
                issues.append(ValidationIssue(
                    level="info",
                    category="structure_long_preamble",
                    message="Long content before first heading",
                    suggestion="Consider adding an introductory heading"
                ))

        # Check for consecutive headings (no content between)
        prev_was_heading = False
        for i, line in enumerate(lines):
            is_heading = bool(re.match(r'^#{1,6}\s+.+$', line.strip()))

            if is_heading and prev_was_heading:
                issues.append(ValidationIssue(
                    level="warning",
                    category="structure_consecutive_headings",
                    message=f"Consecutive headings at line {i + 1}",
                    line_number=i + 1,
                    suggestion="Add content between headings or merge them"
                ))

            prev_was_heading = is_heading

        return issues
