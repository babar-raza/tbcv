# file: agents/edit_validator.py
"""
EditValidator - Comprehensive validation for surgical edits.

Provides:
- Pre-enhancement validation
- Post-enhancement validation
- Detailed preservation checking
- Structure integrity validation
- Content quality metrics
"""

from __future__ import annotations

import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone

from agents.recommendation_enhancer import (
    PreservationRules,
    SafetyViolation,
    SafetyScore
)
from core.logging import get_logger

logger = get_logger(__name__)


# ==============================================================================
# Validation Result Classes
# ==============================================================================

@dataclass
class PreservationValidation:
    """Result of preservation rules validation."""

    is_valid: bool
    violations: List[SafetyViolation] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Detailed scores
    keyword_preservation_score: float = 1.0
    structure_preservation_score: float = 1.0
    content_stability_score: float = 1.0
    technical_accuracy_score: float = 1.0

    # Detailed metrics
    keywords_lost: List[str] = field(default_factory=list)
    keywords_preserved: List[str] = field(default_factory=list)
    structure_changes: List[str] = field(default_factory=list)
    size_change_percent: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_valid": self.is_valid,
            "violations": [v.to_dict() for v in self.violations],
            "warnings": self.warnings,
            "keyword_preservation_score": self.keyword_preservation_score,
            "structure_preservation_score": self.structure_preservation_score,
            "content_stability_score": self.content_stability_score,
            "technical_accuracy_score": self.technical_accuracy_score,
            "keywords_lost": self.keywords_lost,
            "keywords_preserved": self.keywords_preserved,
            "structure_changes": self.structure_changes,
            "size_change_percent": self.size_change_percent,
        }


@dataclass
class PreEnhancementCheck:
    """Pre-flight checks before enhancement."""

    can_proceed: bool
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # File checks
    file_readable: bool = True
    valid_markdown: bool = True

    # Recommendation checks
    recommendations_applicable: bool = True
    conflicting_recommendations: List[Tuple[str, str]] = field(default_factory=list)

    # Preservation rules
    rules_extractable: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "can_proceed": self.can_proceed,
            "issues": self.issues,
            "warnings": self.warnings,
            "file_readable": self.file_readable,
            "valid_markdown": self.valid_markdown,
            "recommendations_applicable": self.recommendations_applicable,
            "conflicting_recommendations": self.conflicting_recommendations,
            "rules_extractable": self.rules_extractable,
        }


@dataclass
class PostEnhancementCheck:
    """Post-enhancement safety checks."""

    is_safe: bool
    violations: List[SafetyViolation] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Preservation checks
    all_keywords_present: bool = True
    structure_intact: bool = True
    code_blocks_intact: bool = True
    links_intact: bool = True
    frontmatter_valid: bool = True

    # Content metrics
    size_within_bounds: bool = True
    technical_terms_preserved: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_safe": self.is_safe,
            "violations": [v.to_dict() for v in self.violations],
            "warnings": self.warnings,
            "all_keywords_present": self.all_keywords_present,
            "structure_intact": self.structure_intact,
            "code_blocks_intact": self.code_blocks_intact,
            "links_intact": self.links_intact,
            "frontmatter_valid": self.frontmatter_valid,
            "size_within_bounds": self.size_within_bounds,
            "technical_terms_preserved": self.technical_terms_preserved,
        }


# ==============================================================================
# EditValidator
# ==============================================================================

class EditValidator:
    """
    Validates edits before and after application.

    Provides comprehensive safety checks for:
    - Keyword preservation
    - Structure maintenance
    - Content stability
    - Technical accuracy
    """

    def __init__(self):
        """Initialize validator."""
        logger.info("Initialized EditValidator")

    def validate_edit(
        self,
        original_section: str,
        edited_section: str,
        recommendation: Dict[str, Any],
        rules: PreservationRules
    ) -> PreservationValidation:
        """
        Validate a single edit against preservation rules.

        Args:
            original_section: Original content section
            edited_section: Edited content section
            recommendation: Recommendation being applied
            rules: Preservation rules to enforce

        Returns:
            PreservationValidation with detailed results
        """
        violations: List[SafetyViolation] = []
        warnings: List[str] = []

        # Check keyword preservation
        keywords_lost: List[str] = []
        keywords_preserved: List[str] = []

        for keyword in rules.preserve_keywords:
            if keyword in original_section:
                if keyword in edited_section:
                    keywords_preserved.append(keyword)
                else:
                    keywords_lost.append(keyword)
                    violations.append(SafetyViolation(
                        severity="high",
                        violation_type="keyword_loss",
                        description=f"Keyword lost: '{keyword}'",
                        detail=f"Keyword was present in original but missing in edited section"
                    ))

        keyword_score = 1.0
        if rules.preserve_keywords:
            keyword_score = len(keywords_preserved) / len(rules.preserve_keywords)

        # Check structure preservation
        structure_changes: List[str] = []
        structure_score = self._check_structure_preservation(
            original_section, edited_section, rules, structure_changes, violations
        )

        # Check content stability
        size_change_percent, content_score = self._check_content_stability(
            original_section, edited_section, rules, warnings, violations
        )

        # Check technical accuracy
        technical_score = self._check_technical_accuracy(
            original_section, edited_section, rules, violations
        )

        # Determine if valid
        is_valid = (
            len([v for v in violations if v.severity == "critical"]) == 0
            and keyword_score >= 0.8
            and structure_score >= 0.8
            and content_score >= 0.7
        )

        return PreservationValidation(
            is_valid=is_valid,
            violations=violations,
            warnings=warnings,
            keyword_preservation_score=keyword_score,
            structure_preservation_score=structure_score,
            content_stability_score=content_score,
            technical_accuracy_score=technical_score,
            keywords_lost=keywords_lost,
            keywords_preserved=keywords_preserved,
            structure_changes=structure_changes,
            size_change_percent=size_change_percent
        )

    def _check_structure_preservation(
        self,
        original: str,
        edited: str,
        rules: PreservationRules,
        changes: List[str],
        violations: List[SafetyViolation]
    ) -> float:
        """Check structure preservation (headings, lists, tables, code blocks)."""
        score = 1.0

        # Check code blocks
        if rules.preserve_code_blocks:
            orig_code_blocks = len(re.findall(r'```[\s\S]*?```', original))
            edit_code_blocks = len(re.findall(r'```[\s\S]*?```', edited))

            if orig_code_blocks != edit_code_blocks:
                changes.append(f"Code blocks changed: {orig_code_blocks} -> {edit_code_blocks}")
                score -= 0.2
                violations.append(SafetyViolation(
                    severity="high",
                    violation_type="code_block_change",
                    description="Number of code blocks changed",
                    detail=f"Original: {orig_code_blocks}, Edited: {edit_code_blocks}"
                ))

        # Check heading hierarchy
        if rules.preserve_heading_hierarchy:
            orig_headings = re.findall(r'^(#{1,6})\s+', original, re.MULTILINE)
            edit_headings = re.findall(r'^(#{1,6})\s+', edited, re.MULTILINE)

            if len(orig_headings) != len(edit_headings):
                changes.append(f"Heading count changed: {len(orig_headings)} -> {len(edit_headings)}")
                score -= 0.1
                warnings_msg = f"Heading structure modified"
                # Don't add violation for minor heading changes

        # Check numbered lists
        if rules.preserve_numbered_lists:
            orig_lists = len(re.findall(r'^\d+\.', original, re.MULTILINE))
            edit_lists = len(re.findall(r'^\d+\.', edited, re.MULTILINE))

            if orig_lists > 0 and edit_lists == 0:
                changes.append("Numbered list removed")
                score -= 0.15
                violations.append(SafetyViolation(
                    severity="medium",
                    violation_type="list_structure_loss",
                    description="Numbered list structure lost"
                ))

        # Check tables
        if rules.preserve_tables:
            orig_table_rows = len(re.findall(r'^\|.*\|$', original, re.MULTILINE))
            edit_table_rows = len(re.findall(r'^\|.*\|$', edited, re.MULTILINE))

            if orig_table_rows > 0 and edit_table_rows == 0:
                changes.append("Table removed")
                score -= 0.2
                violations.append(SafetyViolation(
                    severity="high",
                    violation_type="table_loss",
                    description="Table structure lost"
                ))

        return max(0.0, score)

    def _check_content_stability(
        self,
        original: str,
        edited: str,
        rules: PreservationRules,
        warnings: List[str],
        violations: List[SafetyViolation]
    ) -> Tuple[float, float]:
        """Check content size and stability."""
        original_len = max(len(original), 1)
        edited_len = len(edited)

        size_change_percent = ((edited_len - original_len) / original_len) * 100

        score = 1.0

        # Check reduction
        if edited_len < original_len:
            reduction_percent = ((original_len - edited_len) / original_len) * 100

            if reduction_percent > rules.max_content_reduction_percent:
                score = 0.5
                violations.append(SafetyViolation(
                    severity="critical",
                    violation_type="excessive_reduction",
                    description=f"Content reduced by {reduction_percent:.1f}%",
                    detail=f"Exceeds maximum allowed reduction of {rules.max_content_reduction_percent}%"
                ))
            elif reduction_percent > rules.max_content_reduction_percent * 0.7:
                warnings.append(f"Content reduced by {reduction_percent:.1f}% (close to limit)")

        # Check excessive expansion (warn but don't fail)
        elif size_change_percent > 50:
            warnings.append(f"Content expanded by {size_change_percent:.1f}% (large change)")
            score = 0.9  # Slight reduction for very large expansions

        return size_change_percent, score

    def _check_technical_accuracy(
        self,
        original: str,
        edited: str,
        rules: PreservationRules,
        violations: List[SafetyViolation]
    ) -> float:
        """Check technical terms preservation."""
        score = 1.0
        terms_lost = []

        for term in rules.preserve_technical_terms:
            if term in original and term not in edited:
                terms_lost.append(term)
                score -= 0.1
                violations.append(SafetyViolation(
                    severity="medium",
                    violation_type="technical_term_loss",
                    description=f"Technical term lost: '{term}'"
                ))

        # Check product names
        for product in rules.preserve_product_names:
            if product in original and product not in edited:
                score -= 0.2
                violations.append(SafetyViolation(
                    severity="high",
                    violation_type="product_name_loss",
                    description=f"Product name lost: '{product}'"
                ))

        return max(0.0, score)

    def validate_before_enhancement(
        self,
        content: str,
        recommendations: List[Dict[str, Any]],
        rules: PreservationRules
    ) -> PreEnhancementCheck:
        """
        Pre-flight checks before enhancement.

        Args:
            content: Original content to enhance
            recommendations: List of recommendations to apply
            rules: Preservation rules

        Returns:
            PreEnhancementCheck with validation results
        """
        issues: List[str] = []
        warnings: List[str] = []
        conflicting_recs: List[Tuple[str, str]] = []

        # Check file is readable and valid
        file_readable = len(content) > 0
        if not file_readable:
            issues.append("Content is empty")

        # Check valid markdown (basic)
        valid_markdown = True
        if content and not content.strip():
            valid_markdown = False
            issues.append("Content is whitespace only")

        # Check YAML frontmatter if present
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) < 3:
                warnings.append("Incomplete YAML frontmatter detected")

        # Check recommendations are applicable
        recommendations_applicable = len(recommendations) > 0
        if not recommendations_applicable:
            issues.append("No recommendations provided")

        # Check for conflicting recommendations
        for i, rec1 in enumerate(recommendations):
            for rec2 in recommendations[i+1:]:
                if self._are_recommendations_conflicting(rec1, rec2):
                    conflicting_recs.append((rec1.get("id", "?"), rec2.get("id", "?")))

        if conflicting_recs:
            warnings.append(f"Found {len(conflicting_recs)} potentially conflicting recommendation pairs")

        # Check rules are extractable
        rules_extractable = len(rules.preserve_keywords) > 0 or not rules.preserve_code_blocks

        can_proceed = (
            file_readable
            and valid_markdown
            and len(issues) == 0
        )

        return PreEnhancementCheck(
            can_proceed=can_proceed,
            issues=issues,
            warnings=warnings,
            file_readable=file_readable,
            valid_markdown=valid_markdown,
            recommendations_applicable=recommendations_applicable,
            conflicting_recommendations=conflicting_recs,
            rules_extractable=rules_extractable
        )

    def _are_recommendations_conflicting(
        self,
        rec1: Dict[str, Any],
        rec2: Dict[str, Any]
    ) -> bool:
        """Check if two recommendations might conflict."""
        # Check if they target the same line/section
        r1_start = rec1.get("line_start")
        r1_end = rec1.get("line_end")
        r2_start = rec2.get("line_start")
        r2_end = rec2.get("line_end")

        if all([r1_start, r1_end, r2_start, r2_end]):
            # Check for overlap
            if (r1_start <= r2_end and r2_start <= r1_end):
                return True

        # Check if they have contradictory actions
        if rec1.get("type") == "incorrect_plugin" and rec2.get("type") == "missing_plugin":
            if rec1.get("expected") == rec2.get("plugin_name"):
                return True

        return False

    def validate_after_enhancement(
        self,
        original: str,
        enhanced: str,
        recommendations: List[Dict[str, Any]],
        rules: PreservationRules
    ) -> PostEnhancementCheck:
        """
        Post-enhancement safety checks.

        Args:
            original: Original content
            enhanced: Enhanced content
            recommendations: Recommendations that were applied
            rules: Preservation rules

        Returns:
            PostEnhancementCheck with validation results
        """
        violations: List[SafetyViolation] = []
        warnings: List[str] = []

        # Check all keywords present
        all_keywords_present = True
        for keyword in rules.preserve_keywords:
            if keyword in original and keyword not in enhanced:
                all_keywords_present = False
                violations.append(SafetyViolation(
                    severity="critical",
                    violation_type="keyword_loss",
                    description=f"Critical keyword lost: '{keyword}'"
                ))

        # Check structure intact
        structure_intact = self._check_post_structure(original, enhanced, rules, violations)

        # Check code blocks intact
        code_blocks_intact = True
        if rules.preserve_code_blocks:
            orig_blocks = re.findall(r'```[\s\S]*?```', original)
            edit_blocks = re.findall(r'```[\s\S]*?```', enhanced)

            if len(orig_blocks) > len(edit_blocks):
                code_blocks_intact = False
                violations.append(SafetyViolation(
                    severity="high",
                    violation_type="code_block_loss",
                    description="Code blocks were removed"
                ))

        # Check links intact
        links_intact = self._check_links_intact(original, enhanced, warnings)

        # Check frontmatter valid
        frontmatter_valid = self._check_frontmatter_valid(enhanced, violations)

        # Check size within bounds
        size_within_bounds = True
        if len(enhanced) < len(original):
            reduction = ((len(original) - len(enhanced)) / len(original)) * 100
            if reduction > rules.max_content_reduction_percent:
                size_within_bounds = False
                violations.append(SafetyViolation(
                    severity="critical",
                    violation_type="excessive_reduction",
                    description=f"Content reduced by {reduction:.1f}%"
                ))

        # Check technical terms preserved
        technical_terms_preserved = True
        for term in rules.preserve_technical_terms:
            if term in original and term not in enhanced:
                technical_terms_preserved = False
                violations.append(SafetyViolation(
                    severity="medium",
                    violation_type="technical_term_loss",
                    description=f"Technical term lost: '{term}'"
                ))

        # Overall safety determination
        is_safe = (
            all_keywords_present
            and structure_intact
            and code_blocks_intact
            and size_within_bounds
            and len([v for v in violations if v.severity == "critical"]) == 0
        )

        return PostEnhancementCheck(
            is_safe=is_safe,
            violations=violations,
            warnings=warnings,
            all_keywords_present=all_keywords_present,
            structure_intact=structure_intact,
            code_blocks_intact=code_blocks_intact,
            links_intact=links_intact,
            frontmatter_valid=frontmatter_valid,
            size_within_bounds=size_within_bounds,
            technical_terms_preserved=technical_terms_preserved
        )

    def _check_post_structure(
        self,
        original: str,
        enhanced: str,
        rules: PreservationRules,
        violations: List[SafetyViolation]
    ) -> bool:
        """Check that structure is preserved post-enhancement."""
        # Check major structure elements
        orig_sections = len(re.findall(r'^#{1,2}\s+', original, re.MULTILINE))
        edit_sections = len(re.findall(r'^#{1,2}\s+', enhanced, re.MULTILINE))

        if orig_sections > 0 and edit_sections < orig_sections - 1:
            violations.append(SafetyViolation(
                severity="high",
                violation_type="structure_loss",
                description="Major sections were removed"
            ))
            return False

        return True

    def _check_links_intact(
        self,
        original: str,
        enhanced: str,
        warnings: List[str]
    ) -> bool:
        """Check that internal links are preserved."""
        orig_links = set(re.findall(r'\[([^\]]+)\]\(([^\)]+)\)', original))
        edit_links = set(re.findall(r'\[([^\]]+)\]\(([^\)]+)\)', enhanced))

        # Check if significant links were lost
        lost_links = orig_links - edit_links
        if len(lost_links) > 3:
            warnings.append(f"{len(lost_links)} links were removed")
            return False

        return True

    def _check_frontmatter_valid(
        self,
        content: str,
        violations: List[SafetyViolation]
    ) -> bool:
        """Check that YAML frontmatter is valid if present."""
        if not content.startswith("---"):
            return True  # No frontmatter, so valid

        parts = content.split("---", 2)
        if len(parts) < 3:
            violations.append(SafetyViolation(
                severity="high",
                violation_type="invalid_frontmatter",
                description="YAML frontmatter is incomplete or malformed"
            ))
            return False

        return True

    def calculate_enhanced_safety_score(
        self,
        original: str,
        enhanced: str,
        rules: PreservationRules,
        applied_recommendations: List[Dict[str, Any]]
    ) -> SafetyScore:
        """
        Calculate comprehensive safety score.

        Args:
            original: Original content
            enhanced: Enhanced content
            rules: Preservation rules
            applied_recommendations: List of applied recommendations

        Returns:
            SafetyScore with detailed sub-scores
        """
        violations: List[SafetyViolation] = []
        warnings: List[str] = []

        # Run comprehensive validation
        post_check = self.validate_after_enhancement(
            original, enhanced, applied_recommendations, rules
        )

        violations.extend(post_check.violations)
        warnings.extend(post_check.warnings)

        # Calculate sub-scores
        keyword_score = 1.0 if post_check.all_keywords_present else 0.6
        structure_score = 1.0 if post_check.structure_intact else 0.7
        content_score = 1.0 if post_check.size_within_bounds else 0.5
        technical_score = 1.0 if post_check.technical_terms_preserved else 0.8

        # Reduce scores based on violations
        for violation in violations:
            if violation.severity == "critical":
                if "keyword" in violation.violation_type:
                    keyword_score -= 0.3
                elif "structure" in violation.violation_type:
                    structure_score -= 0.3
                elif "reduction" in violation.violation_type:
                    content_score -= 0.3
            elif violation.severity == "high":
                if "keyword" in violation.violation_type:
                    keyword_score -= 0.2
                elif "structure" in violation.violation_type:
                    structure_score -= 0.2

        # Ensure scores are in valid range
        keyword_score = max(0.0, min(1.0, keyword_score))
        structure_score = max(0.0, min(1.0, structure_score))
        content_score = max(0.0, min(1.0, content_score))
        technical_score = max(0.0, min(1.0, technical_score))

        # Calculate overall score (weighted average)
        overall_score = (
            keyword_score * 0.35 +      # Keywords most important
            structure_score * 0.25 +
            content_score * 0.25 +
            technical_score * 0.15
        )

        return SafetyScore(
            overall_score=overall_score,
            keyword_preservation=keyword_score,
            structure_preservation=structure_score,
            content_stability=content_score,
            technical_accuracy=technical_score,
            violations=violations,
            warnings=warnings
        )
