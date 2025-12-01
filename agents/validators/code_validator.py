# file: agents/validators/code_validator.py
"""
Code Validator Agent - Validates code blocks in content.
Uses ConfigLoader for configuration-driven validation.
"""

from __future__ import annotations
import re
from typing import Dict, Any, List, Optional, Tuple

from agents.validators.base_validator import (
    BaseValidatorAgent,
    ValidationIssue,
    ValidationResult
)
from core.config_loader import ConfigLoader, get_config_loader
from core.logging import get_logger

logger = get_logger(__name__)


class CodeValidatorAgent(BaseValidatorAgent):
    """Validates code blocks and code-related content."""

    def __init__(self, agent_id: Optional[str] = None, config_loader: Optional[ConfigLoader] = None):
        super().__init__(agent_id or "code_validator")
        self._config_loader = config_loader or get_config_loader()
        self._config = self._config_loader.load("code")

    def get_validation_type(self) -> str:
        return "code"

    async def validate(self, content: str, context: Dict[str, Any]) -> ValidationResult:
        """Validate code blocks and inline code."""
        issues: List[ValidationIssue] = []
        auto_fixable = 0
        lines = content.split('\n')

        # Get profile and family from context
        profile = context.get("profile", self._config.profile)
        family = context.get("family")

        # Get active rules for this profile/family
        active_rules = self._config_loader.get_rules("code", profile=profile, family=family)
        active_rule_ids = {r.id for r in active_rules}
        rule_levels = {r.id: r.level for r in active_rules}
        rule_params = {r.id: r.params for r in active_rules}

        # Extract code blocks
        code_blocks = self._extract_code_blocks(lines)

        # Validate code blocks
        for block in code_blocks:
            block_issues = self._validate_code_block(block, active_rule_ids, rule_levels, rule_params)
            issues.extend(block_issues)

        # Check for inline code issues
        if "inline_code_too_long" in active_rule_ids:
            max_chars = rule_params.get("inline_code_too_long", {}).get("max_chars", 50)
            level = rule_levels.get("inline_code_too_long", "info")
            inline_issues = self._check_inline_code(lines, max_chars, level)
            issues.extend(inline_issues)

        confidence = max(0.6, 1.0 - (len(issues) * 0.1))

        return ValidationResult(
            confidence=confidence,
            issues=issues,
            auto_fixable_count=auto_fixable,
            metrics={
                "code_blocks_found": len(code_blocks),
                "issues_count": len(issues),
                "profile": profile,
                "family": family
            }
        )

    def _extract_code_blocks(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Extract all code blocks from content."""
        code_blocks = []
        in_code_block = False
        current_block = None

        for i, line in enumerate(lines):
            if line.strip().startswith('```'):
                if in_code_block:
                    # End of code block
                    current_block['end_line'] = i + 1
                    code_blocks.append(current_block)
                    current_block = None
                    in_code_block = False
                else:
                    # Start of code block
                    language = line.strip()[3:].strip()
                    current_block = {
                        'start_line': i + 1,
                        'language': language,
                        'lines': []
                    }
                    in_code_block = True
            elif in_code_block and current_block is not None:
                current_block['lines'].append(line)

        return code_blocks

    def _validate_code_block(
        self,
        block: Dict[str, Any],
        active_rule_ids: set,
        rule_levels: Dict[str, str],
        rule_params: Dict[str, Dict]
    ) -> List[ValidationIssue]:
        """Validate a single code block."""
        issues = []

        # Check if language is specified
        if "no_language_specified" in active_rule_ids and not block['language']:
            level = rule_levels.get("no_language_specified", "warning")
            issues.append(ValidationIssue(
                level=level,
                category="code_no_language",
                message=f"Code block at line {block['start_line']} missing language specifier",
                line_number=block['start_line'],
                suggestion="Add language after opening ```: ```csharp, ```python, etc."
            ))

        # Check for empty code blocks
        if "empty_code_block" in active_rule_ids:
            if not block['lines'] or all(not line.strip() for line in block['lines']):
                level = rule_levels.get("empty_code_block", "warning")
                issues.append(ValidationIssue(
                    level=level,
                    category="code_empty_block",
                    message=f"Empty code block at line {block['start_line']}",
                    line_number=block['start_line'],
                    suggestion="Add code content or remove the empty block"
                ))

        # Check for very long code blocks
        if "code_block_too_long" in active_rule_ids:
            max_lines = rule_params.get("code_block_too_long", {}).get("max_lines", 100)
            if len(block['lines']) > max_lines:
                level = rule_levels.get("code_block_too_long", "info")
                issues.append(ValidationIssue(
                    level=level,
                    category="code_block_too_long",
                    message=f"Very long code block ({len(block['lines'])} lines) at line {block['start_line']}",
                    line_number=block['start_line'],
                    suggestion="Consider splitting into smaller, more focused examples"
                ))

        # Check for hardcoded paths
        if "hardcoded_path" in active_rule_ids:
            patterns = rule_params.get("hardcoded_path", {}).get("patterns", ["C:\\", "/home/", "/Users/"])
            level = rule_levels.get("hardcoded_path", "warning")
            code_content = '\n'.join(block['lines'])
            for pattern in patterns:
                if pattern in code_content:
                    issues.append(ValidationIssue(
                        level=level,
                        category="code_hardcoded_path",
                        message=f"Hardcoded path detected at line {block['start_line']}: {pattern}",
                        line_number=block['start_line'],
                        suggestion="Use relative paths or environment variables"
                    ))
                    break  # Only report once per block

        return issues

    def _check_inline_code(self, lines: List[str], max_chars: int, level: str) -> List[ValidationIssue]:
        """Check for inline code issues."""
        issues = []
        # Match inline code: `code`
        inline_pattern = re.compile(r'`([^`]+)`')

        for i, line in enumerate(lines):
            # Skip lines that are in code blocks
            if line.strip().startswith('```'):
                continue

            matches = inline_pattern.findall(line)
            for code_text in matches:
                # Check for very long inline code
                if len(code_text) > max_chars:
                    issues.append(ValidationIssue(
                        level=level,
                        category="code_inline_too_long",
                        message=f"Long inline code ({len(code_text)} chars) at line {i + 1}",
                        line_number=i + 1,
                        suggestion="Consider using a code block instead"
                    ))

        return issues
