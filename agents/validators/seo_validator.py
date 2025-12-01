# file: agents/validators/seo_validator.py
"""
SEO Validator Agent - Validates SEO-friendly content structure.
Handles both SEO headings and heading sizes validation.
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


class SeoValidatorAgent(BaseValidatorAgent):
    """Validates SEO headings and heading sizes."""

    def __init__(self, agent_id: Optional[str] = None, config_loader: Optional[ConfigLoader] = None):
        super().__init__(agent_id or "seo_validator")
        self._config_loader = config_loader or get_config_loader()
        self._config = self._config_loader.load("seo")

    def get_validation_type(self) -> str:
        return "seo"

    def _get_heading_sizes(self) -> Dict[str, Dict[str, Any]]:
        """Get heading size limits from config."""
        return self._config.get("heading_sizes", {
            "h1": {"min_length": 20, "max_length": 70, "recommended_min": 30, "recommended_max": 60},
            "h2": {"min_length": 10, "max_length": 100, "recommended_min": 20, "recommended_max": 80},
            "h3": {"min_length": 5, "max_length": 100, "recommended_min": 15, "recommended_max": 70},
            "h4": {"min_length": 5, "max_length": 80, "recommended_min": 10, "recommended_max": 60},
            "h5": {"min_length": 3, "max_length": 70, "recommended_min": 8, "recommended_max": 50},
            "h6": {"min_length": 3, "max_length": 60, "recommended_min": 8, "recommended_max": 40},
        })

    def _get_settings(self) -> Dict[str, Any]:
        """Get general SEO settings from config."""
        return self._config.get("settings", {
            "allow_empty_headings": False,
            "enforce_hierarchy": True,
            "max_depth": 6,
            "h1_must_be_first": True
        })

    async def validate(self, content: str, context: Dict[str, Any]) -> ValidationResult:
        """Validate SEO headings and/or heading sizes based on context."""
        issues: List[ValidationIssue] = []
        auto_fixable = 0

        # Get profile and family from context
        profile = context.get("profile", self._config.profile)
        family = context.get("family")
        validation_mode = context.get("mode", context.get("validation_type", "seo"))

        # Get active rules
        active_rules = self._config_loader.get_rules("seo", profile=profile, family=family)
        active_rule_ids = {r.id for r in active_rules}
        rule_levels = {r.id: r.level for r in active_rules}

        # Extract headings
        headings = self._extract_headings(content)

        if not headings:
            return ValidationResult(
                confidence=0.5,
                issues=[ValidationIssue(
                    level="warning",
                    category="no_headings",
                    message="No headings found in content",
                    suggestion="Add headings to structure your content"
                )],
                metrics={
                    "headings_count": 0,
                    "profile": profile,
                    "family": family,
                    "mode": validation_mode
                }
            )

        # Run SEO heading validations (unless mode is heading_sizes_only)
        if validation_mode != "heading_sizes":
            seo_issues = self._validate_seo_rules(headings, active_rule_ids, rule_levels)
            issues.extend(seo_issues)

        # Run heading size validations
        if validation_mode in ("heading_sizes", "seo", "all"):
            size_issues = self._validate_heading_sizes(headings, active_rule_ids, rule_levels)
            issues.extend(size_issues)

        confidence = max(0.3, 1.0 - (len(issues) * 0.1))
        h1_count = len([h for h in headings if h["level"] == 1])

        return ValidationResult(
            confidence=confidence,
            issues=issues,
            auto_fixable_count=auto_fixable,
            metrics={
                "headings_count": len(headings),
                "h1_count": h1_count,
                "issues_count": len(issues),
                "profile": profile,
                "family": family,
                "mode": validation_mode
            }
        )

    def _validate_seo_rules(
        self,
        headings: List[Dict[str, Any]],
        active_rule_ids: set,
        rule_levels: Dict[str, str]
    ) -> List[ValidationIssue]:
        """Validate SEO-specific heading rules."""
        issues = []
        settings = self._get_settings()

        h1_headings = [h for h in headings if h["level"] == 1]

        # H1 required
        if "h1_required" in active_rule_ids and not h1_headings:
            level = rule_levels.get("h1_required", "error")
            issues.append(ValidationIssue(
                level=level,
                category="seo_h1_missing",
                message="H1 heading is required for SEO",
                suggestion="Add an H1 heading at the beginning of the document"
            ))

        # H1 unique
        if "h1_unique" in active_rule_ids and len(h1_headings) > 1:
            level = rule_levels.get("h1_unique", "error")
            issues.append(ValidationIssue(
                level=level,
                category="seo_h1_not_unique",
                message=f"Found {len(h1_headings)} H1 headings, should be unique",
                suggestion="Keep only one H1 heading per document"
            ))

        # H1 must be first
        if "h1_first" in active_rule_ids and settings.get("h1_must_be_first"):
            if headings and headings[0]["level"] != 1:
                level = rule_levels.get("h1_first", "warning")
                issues.append(ValidationIssue(
                    level=level,
                    category="seo_h1_not_first",
                    message="H1 heading should be the first heading",
                    suggestion="Move H1 heading to the beginning"
                ))

        # Heading hierarchy
        if "hierarchy_skip" in active_rule_ids and settings.get("enforce_hierarchy"):
            for i in range(1, len(headings)):
                prev_level = headings[i-1]["level"]
                curr_level = headings[i]["level"]

                if curr_level > prev_level + 1:
                    level = rule_levels.get("hierarchy_skip", "error")
                    issues.append(ValidationIssue(
                        level=level,
                        category="seo_hierarchy_skip",
                        message=f"Heading hierarchy skip: H{prev_level} → H{curr_level} (line {headings[i]['line']})",
                        line_number=headings[i]['line'],
                        suggestion=f"Use H{prev_level + 1} instead of H{curr_level}"
                    ))

        # Empty headings
        if "empty_heading" in active_rule_ids and not settings.get("allow_empty_headings"):
            for h in headings:
                if not h["text"].strip():
                    level = rule_levels.get("empty_heading", "warning")
                    issues.append(ValidationIssue(
                        level=level,
                        category="seo_empty_heading",
                        message=f"Empty H{h['level']} heading at line {h['line']}",
                        line_number=h['line'],
                        suggestion="Add descriptive text to the heading"
                    ))

        return issues

    def _validate_heading_sizes(
        self,
        headings: List[Dict[str, Any]],
        active_rule_ids: set,
        rule_levels: Dict[str, str]
    ) -> List[ValidationIssue]:
        """Validate heading text lengths."""
        issues = []
        size_config = self._get_heading_sizes()

        for h in headings:
            h_level = f"h{h['level']}"
            if h_level not in size_config:
                continue

            limits = size_config[h_level]
            text_len = len(h["text"])

            # Check minimum
            if "heading_too_short" in active_rule_ids and text_len < limits.get("min_length", 0):
                level = rule_levels.get("heading_too_short", "error")
                issues.append(ValidationIssue(
                    level=level,
                    category="heading_too_short",
                    message=f"H{h['level']} heading is only {text_len} characters (minimum: {limits['min_length']})",
                    line_number=h["line"],
                    suggestion=f"Add at least {limits['min_length'] - text_len} more characters to meet minimum length"
                ))

            # Check maximum
            elif "heading_too_long" in active_rule_ids and text_len > limits.get("max_length", 9999):
                level = rule_levels.get("heading_too_long", "warning")
                issues.append(ValidationIssue(
                    level=level,
                    category="heading_too_long",
                    message=f"H{h['level']} heading is {text_len} characters (maximum: {limits['max_length']})",
                    line_number=h["line"],
                    suggestion=f"Shorten by at least {text_len - limits['max_length']} characters"
                ))

            # Check recommended range
            elif "heading_below_recommended" in active_rule_ids and text_len < limits.get("recommended_min", 0):
                level = rule_levels.get("heading_below_recommended", "info")
                issues.append(ValidationIssue(
                    level=level,
                    category="heading_below_recommended",
                    message=f"H{h['level']} heading is {text_len} characters (recommended: {limits['recommended_min']}+)",
                    line_number=h["line"],
                    suggestion="Consider adding more context"
                ))

            elif "heading_above_recommended" in active_rule_ids and text_len > limits.get("recommended_max", 9999):
                level = rule_levels.get("heading_above_recommended", "info")
                issues.append(ValidationIssue(
                    level=level,
                    category="heading_above_recommended",
                    message=f"H{h['level']} heading is {text_len} characters (recommended: <{limits['recommended_max']})",
                    line_number=h["line"],
                    suggestion="Consider making more concise"
                ))

        return issues

    def _extract_headings(self, content: str) -> List[Dict[str, Any]]:
        """Extract headings from markdown content."""
        headings = []
        lines = content.split('\n')

        for i, line in enumerate(lines):
            # Match markdown headings: # Heading, ## Heading, etc.
            match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                headings.append({
                    "level": level,
                    "text": text,
                    "line": i + 1
                })

        return headings
