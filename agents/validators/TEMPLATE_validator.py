# file: agents/validators/TEMPLATE_validator.py
"""
TEMPLATE Validator Agent - Template for creating new validators.

INSTRUCTIONS:
1. Copy this file to a new file: {name}_validator.py
2. Replace TEMPLATE with your validator name (e.g., Accessibility, Performance, etc.)
3. Implement the validate() method with your validation logic
4. Update get_validation_type() to return your validator's ID
5. Register in api/server.py
6. Add to config/main.yaml validators section
7. Write tests in tests/validators/test_{name}_validator.py

ESTIMATED TIME: 2-4 hours for a basic validator
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional

from agents.validators.base_validator import (
    BaseValidatorAgent,
    ValidationIssue,
    ValidationResult
)
from core.logging import get_logger

logger = get_logger(__name__)


class TEMPLATEValidatorAgent(BaseValidatorAgent):
    """
    Validates [DESCRIPTION OF WHAT THIS VALIDATOR CHECKS].

    Example:
        validator = TEMPLATEValidatorAgent("template_validator")
        result = await validator.validate(content, {"file_path": "test.md"})
    """

    def __init__(self, agent_id: Optional[str] = None):
        """
        Initialize the TEMPLATE validator.

        Args:
            agent_id: Optional agent ID (defaults to 'template_validator')
        """
        super().__init__(agent_id or "template_validator")

        # Load any configuration needed
        # self.config = self._load_config()

    def get_validation_type(self) -> str:
        """
        Return the validation type identifier.

        This should match the ID used in:
        - config/main.yaml validators section
        - ValidatorRouter mapping
        - API validation_types parameter

        Returns:
            str: Validator type ID (e.g., 'template', 'accessibility', 'performance')
        """
        return "template"

    async def validate(self, content: str, context: Dict[str, Any]) -> ValidationResult:
        """
        Validate content according to TEMPLATE rules.

        Args:
            content: The content to validate (usually Markdown)
            context: Additional context containing:
                - file_path: Path to the file being validated
                - family: Content family (e.g., 'words', 'pdf', 'cells')
                - validation_type: Specific validation type requested

        Returns:
            ValidationResult containing:
                - confidence: Validation confidence (0.0-1.0)
                - issues: List of ValidationIssue objects
                - auto_fixable_count: Number of auto-fixable issues
                - metrics: Dict of validation metrics

        Example:
            result = await validator.validate(
                content="# Test\\nContent here",
                context={"file_path": "test.md", "family": "words"}
            )
        """
        issues: List[ValidationIssue] = []
        auto_fixable = 0

        # Extract useful context
        file_path = context.get("file_path", "unknown")
        family = context.get("family", "words")

        # TODO: Implement your validation logic here
        # Example validation checks:

        # 1. Check for specific patterns
        if "TODO" in content:
            issues.append(ValidationIssue(
                level="warning",
                category="template_todo_found",
                message="Content contains TODO markers",
                suggestion="Complete or remove TODO items before publishing",
                line_number=self._find_line_number(content, "TODO")
            ))

        # 2. Validate content structure
        if len(content.strip()) == 0:
            issues.append(ValidationIssue(
                level="error",
                category="template_empty_content",
                message="Content is empty",
                suggestion="Add content to the document"
            ))

        # 3. Check for specific requirements
        lines = content.split('\n')
        for i, line in enumerate(lines):
            # Example: Check each line for issues
            if line.strip().startswith("FIXME"):
                issues.append(ValidationIssue(
                    level="warning",
                    category="template_fixme_found",
                    message=f"FIXME marker found at line {i + 1}",
                    line_number=i + 1,
                    suggestion="Address the FIXME comment"
                ))

        # 4. Calculate confidence based on issues found
        # Higher confidence = fewer/less severe issues
        if not issues:
            confidence = 1.0
        elif all(issue.level == "info" for issue in issues):
            confidence = 0.9
        elif all(issue.level in ["info", "warning"] for issue in issues):
            confidence = 0.7
        else:  # Has errors
            confidence = max(0.3, 1.0 - (len(issues) * 0.15))

        # 5. Return validation result
        return ValidationResult(
            confidence=confidence,
            issues=issues,
            auto_fixable_count=auto_fixable,
            metrics={
                "lines_checked": len(lines),
                "issues_count": len(issues),
                "file_path": file_path,
                "family": family
            }
        )

    def _find_line_number(self, content: str, search_text: str) -> Optional[int]:
        """
        Helper method to find line number of text.

        Args:
            content: Content to search
            search_text: Text to find

        Returns:
            Line number (1-indexed) or None if not found
        """
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if search_text in line:
                return i + 1
        return None

    # Add any other helper methods you need


# =============================================================================
# REGISTRATION INSTRUCTIONS
# =============================================================================

"""
STEP 1: Add to api/server.py imports (top of file):
    from agents.validators.template_validator import TEMPLATEValidatorAgent

STEP 2: Add to api/server.py register_agents() function:
    if getattr(settings.validators.template, "enabled", True):
        template_validator = TEMPLATEValidatorAgent("template_validator")
        agent_registry.register_agent(template_validator)
        logger.info("TEMPLATE validator registered")

STEP 3: Add to config/main.yaml validators section:
    validators:
      template:
        enabled: true
        # Add any validator-specific config here

STEP 4: Add to agents/validators/router.py validator_map:
    def _build_validator_map(self) -> Dict[str, str]:
        return {
            # ... existing mappings ...
            "template": "template_validator",
        }

STEP 5: Update agents/validators/router.py get_available_validators():
    validator_definitions = [
        # ... existing validators ...
        {"id": "template", "label": "TEMPLATE", "description": "Validate TEMPLATE rules", "category": "advanced"},
    ]

STEP 6: Create tests in tests/validators/test_template_validator.py:
    import pytest
    from agents.validators.template_validator import TEMPLATEValidatorAgent

    @pytest.mark.asyncio
    async def test_template_validator_basic():
        validator = TEMPLATEValidatorAgent("test")
        result = await validator.validate("# Test", {})
        assert result.confidence > 0.5

    @pytest.mark.asyncio
    async def test_template_validator_finds_issues():
        validator = TEMPLATEValidatorAgent("test")
        result = await validator.validate("TODO: finish this", {})
        assert len(result.issues) > 0

STEP 7: Run tests:
    python -m pytest tests/validators/test_template_validator.py -v

STEP 8: Test via test suite:
    Add to test_validators_direct.py:

    async def test_template_validator():
        print("\\n=== Testing TEMPLATEValidatorAgent ===")
        validator = TEMPLATEValidatorAgent("test_template")
        content = "# Test\\nTODO: Complete"
        result = await validator.validate(content, {})
        print(f"[OK] TEMPLATE Validator executed")
        print(f"  - Confidence: {result.confidence:.2f}")
        print(f"  - Issues found: {len(result.issues)}")
        return result

That's it! Your validator is now integrated into the TBCV system.
"""
