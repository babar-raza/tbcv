# file: agents/validators/code_validator.py
"""
Code Validator Agent - Validates code blocks in content.
"""

from __future__ import annotations
import re
from typing import Dict, Any, List, Optional, Tuple

from agents.validators.base_validator import (
    BaseValidatorAgent,
    ValidationIssue,
    ValidationResult
)
from core.logging import get_logger

logger = get_logger(__name__)


class CodeValidatorAgent(BaseValidatorAgent):
    """Validates code blocks and code-related content."""

    def __init__(self, agent_id: Optional[str] = None):
        super().__init__(agent_id or "code_validator")

    def get_validation_type(self) -> str:
        return "code"

    async def validate(self, content: str, context: Dict[str, Any]) -> ValidationResult:
        """Validate code blocks and inline code."""
        issues: List[ValidationIssue] = []
        auto_fixable = 0
        lines = content.split('\n')

        # Extract code blocks
        code_blocks = self._extract_code_blocks(lines)

        # Validate code blocks
        for block in code_blocks:
            block_issues = self._validate_code_block(block)
            issues.extend(block_issues)

        # Check for inline code issues
        inline_issues = self._check_inline_code(lines)
        issues.extend(inline_issues)

        confidence = max(0.6, 1.0 - (len(issues) * 0.1))

        return ValidationResult(
            confidence=confidence,
            issues=issues,
            auto_fixable_count=auto_fixable,
            metrics={
                "code_blocks_found": len(code_blocks),
                "issues_count": len(issues)
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

    def _validate_code_block(self, block: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate a single code block."""
        issues = []

        # Check if language is specified
        if not block['language']:
            issues.append(ValidationIssue(
                level="warning",
                category="code_no_language",
                message=f"Code block at line {block['start_line']} missing language specifier",
                line_number=block['start_line'],
                suggestion="Add language after opening ```: ```csharp, ```python, etc."
            ))

        # Check for empty code blocks
        if not block['lines'] or all(not line.strip() for line in block['lines']):
            issues.append(ValidationIssue(
                level="warning",
                category="code_empty_block",
                message=f"Empty code block at line {block['start_line']}",
                line_number=block['start_line'],
                suggestion="Add code content or remove the empty block"
            ))

        # Check for very long code blocks (over 100 lines)
        if len(block['lines']) > 100:
            issues.append(ValidationIssue(
                level="info",
                category="code_block_too_long",
                message=f"Very long code block ({len(block['lines'])} lines) at line {block['start_line']}",
                line_number=block['start_line'],
                suggestion="Consider splitting into smaller, more focused examples"
            ))

        return issues

    def _check_inline_code(self, lines: List[str]) -> List[ValidationIssue]:
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
                # Check for very long inline code (over 50 chars)
                if len(code_text) > 50:
                    issues.append(ValidationIssue(
                        level="info",
                        category="code_inline_too_long",
                        message=f"Long inline code ({len(code_text)} chars) at line {i + 1}",
                        line_number=i + 1,
                        suggestion="Consider using a code block instead"
                    ))

        return issues
