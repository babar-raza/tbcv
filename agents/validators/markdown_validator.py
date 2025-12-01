# file: agents/validators/markdown_validator.py
"""
Markdown Validator Agent - Validates Markdown syntax.
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


class MarkdownValidatorAgent(BaseValidatorAgent):
    """Validates Markdown syntax and common issues."""

    def __init__(self, agent_id: Optional[str] = None, config_loader: Optional[ConfigLoader] = None):
        super().__init__(agent_id or "markdown_validator")
        self._config_loader = config_loader or get_config_loader()
        self._config = self._config_loader.load("markdown")

    def get_validation_type(self) -> str:
        return "markdown"

    async def validate(self, content: str, context: Dict[str, Any]) -> ValidationResult:
        """Validate Markdown syntax."""
        issues: List[ValidationIssue] = []
        auto_fixable = 0
        lines = content.split('\n')

        # Get profile and family from context
        profile = context.get("profile", self._config.profile)
        family = context.get("family")

        # Get active rules for this profile/family
        active_rules = self._config_loader.get_rules("markdown", profile=profile, family=family)
        active_rule_ids = {r.id for r in active_rules}
        rule_levels = {r.id: r.level for r in active_rules}

        # Check for unclosed code blocks
        if "unclosed_code_block" in active_rule_ids:
            level = rule_levels.get("unclosed_code_block", "error")
            code_block_issues = self._check_code_blocks(lines, level)
            issues.extend(code_block_issues)

        # Check for invalid link syntax
        link_issues = self._check_links(lines, active_rule_ids, rule_levels)
        issues.extend(link_issues)

        # Check for missing alt text in images
        image_issues = self._check_images(lines, active_rule_ids, rule_levels)
        issues.extend(image_issues)

        # Check for common formatting issues
        format_issues = self._check_formatting(lines, active_rule_ids, rule_levels)
        issues.extend(format_issues)

        confidence = max(0.5, 1.0 - (len(issues) * 0.1))

        return ValidationResult(
            confidence=confidence,
            issues=issues,
            auto_fixable_count=auto_fixable,
            metrics={
                "lines_checked": len(lines),
                "issues_count": len(issues),
                "profile": profile,
                "family": family
            }
        )

    def _check_code_blocks(self, lines: List[str], level: str = "error") -> List[ValidationIssue]:
        """Check for unclosed code blocks."""
        issues = []
        in_code_block = False
        code_block_start_line = 0

        for i, line in enumerate(lines):
            if line.strip().startswith('```'):
                if in_code_block:
                    in_code_block = False
                else:
                    in_code_block = True
                    code_block_start_line = i + 1

        if in_code_block:
            issues.append(ValidationIssue(
                level=level,
                category="markdown_unclosed_code_block",
                message=f"Unclosed code block starting at line {code_block_start_line}",
                line_number=code_block_start_line,
                suggestion="Add closing ``` to close the code block"
            ))

        return issues

    def _check_links(self, lines: List[str], active_rule_ids: set, rule_levels: Dict[str, str]) -> List[ValidationIssue]:
        """Check for invalid link syntax."""
        issues = []
        # Match markdown links: [text](url)
        link_pattern = re.compile(r'\[([^\]]*)\]\(([^)]*)\)')

        for i, line in enumerate(lines):
            # Find all links in line
            matches = link_pattern.findall(line)
            for text, url in matches:
                # Check for empty link text
                if "empty_link_text" in active_rule_ids and not text.strip():
                    level = rule_levels.get("empty_link_text", "warning")
                    issues.append(ValidationIssue(
                        level=level,
                        category="markdown_empty_link_text",
                        message=f"Empty link text at line {i + 1}",
                        line_number=i + 1,
                        suggestion="Add descriptive text between [brackets]"
                    ))

                # Check for empty URL
                if "empty_link_url" in active_rule_ids and not url.strip():
                    level = rule_levels.get("empty_link_url", "error")
                    issues.append(ValidationIssue(
                        level=level,
                        category="markdown_empty_link_url",
                        message=f"Empty link URL at line {i + 1}",
                        line_number=i + 1,
                        suggestion="Add URL between (parentheses)"
                    ))

        return issues

    def _check_images(self, lines: List[str], active_rule_ids: set, rule_levels: Dict[str, str]) -> List[ValidationIssue]:
        """Check for images without alt text."""
        issues = []
        # Match markdown images: ![alt](url)
        image_pattern = re.compile(r'!\[([^\]]*)\]\(([^)]*)\)')

        for i, line in enumerate(lines):
            matches = image_pattern.findall(line)
            for alt, url in matches:
                # Check for missing alt text
                if "missing_alt_text" in active_rule_ids and not alt.strip():
                    level = rule_levels.get("missing_alt_text", "warning")
                    issues.append(ValidationIssue(
                        level=level,
                        category="markdown_missing_alt_text",
                        message=f"Image missing alt text at line {i + 1}",
                        line_number=i + 1,
                        suggestion="Add descriptive alt text: ![description](url)"
                    ))

                # Check for empty URL
                if "empty_image_url" in active_rule_ids and not url.strip():
                    level = rule_levels.get("empty_image_url", "error")
                    issues.append(ValidationIssue(
                        level=level,
                        category="markdown_empty_image_url",
                        message=f"Image missing URL at line {i + 1}",
                        line_number=i + 1,
                        suggestion="Add image URL between (parentheses)"
                    ))

        return issues

    def _check_formatting(self, lines: List[str], active_rule_ids: set, rule_levels: Dict[str, str]) -> List[ValidationIssue]:
        """Check for common formatting issues."""
        issues = []

        for i, line in enumerate(lines):
            # Check for multiple consecutive blank lines
            if "excessive_whitespace" in active_rule_ids:
                if i > 0 and i < len(lines) - 1:
                    if not line.strip() and not lines[i-1].strip() and not lines[i+1].strip():
                        level = rule_levels.get("excessive_whitespace", "info")
                        issues.append(ValidationIssue(
                            level=level,
                            category="markdown_excessive_whitespace",
                            message=f"Multiple consecutive blank lines at line {i + 1}",
                            line_number=i + 1,
                            suggestion="Remove excessive blank lines"
                        ))

            # Check for trailing whitespace
            if "trailing_whitespace" in active_rule_ids:
                if line != line.rstrip():
                    level = rule_levels.get("trailing_whitespace", "info")
                    issues.append(ValidationIssue(
                        level=level,
                        category="markdown_trailing_whitespace",
                        message=f"Trailing whitespace at line {i + 1}",
                        line_number=i + 1,
                        suggestion="Remove trailing spaces"
                    ))

        return issues
