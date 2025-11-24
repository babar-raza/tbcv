# file: agents/recommendation_enhancer.py
"""
Production-ready RecommendationEnhancer - Surgical content enhancement with safety.

This module provides recommendation-driven content enhancement with:
- Surgical precision (targeted edits only)
- Preservation rules enforcement (keywords, structure, SEO)
- Safety validation before/after edits
- Preview-approve-apply workflow
- Full audit trail and rollback capability
"""

from __future__ import annotations

import re
import difflib
import asyncio
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime, timezone
from pathlib import Path

from core.logging import get_logger
from core.ollama import Ollama

logger = get_logger(__name__)

# Initialize Ollama client
_ollama_client = None

def get_ollama_client() -> Ollama:
    """Get or create Ollama client."""
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = Ollama()
    return _ollama_client

# Import EditValidator (lazy to avoid circular imports)
_edit_validator = None

def get_edit_validator():
    """Get or create EditValidator."""
    global _edit_validator
    if _edit_validator is None:
        from agents.edit_validator import EditValidator
        _edit_validator = EditValidator()
    return _edit_validator


# ==============================================================================
# Data Classes
# ==============================================================================

@dataclass
class PreservationRules:
    """Rules for what must be preserved during enhancement."""

    # SEO critical elements
    preserve_keywords: List[str] = field(default_factory=list)
    preserve_product_names: List[str] = field(default_factory=list)
    preserve_technical_terms: List[str] = field(default_factory=list)

    # Structure preservation
    preserve_code_blocks: bool = True
    preserve_yaml_frontmatter: bool = True
    preserve_heading_hierarchy: bool = True
    preserve_internal_links: bool = True

    # Content constraints
    max_content_reduction_percent: float = 10.0  # Max 10% reduction
    min_content_expansion_percent: float = 0.0
    preserve_numbered_lists: bool = True
    preserve_tables: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "preserve_keywords": self.preserve_keywords,
            "preserve_product_names": self.preserve_product_names,
            "preserve_technical_terms": self.preserve_technical_terms,
            "preserve_code_blocks": self.preserve_code_blocks,
            "preserve_yaml_frontmatter": self.preserve_yaml_frontmatter,
            "preserve_heading_hierarchy": self.preserve_heading_hierarchy,
            "preserve_internal_links": self.preserve_internal_links,
            "max_content_reduction_percent": self.max_content_reduction_percent,
            "min_content_expansion_percent": self.min_content_expansion_percent,
            "preserve_numbered_lists": self.preserve_numbered_lists,
            "preserve_tables": self.preserve_tables,
        }


@dataclass
class EditContext:
    """Context window for a surgical edit."""

    target_section: str  # The section to edit
    before_context: str  # Lines before (for flow preservation)
    after_context: str   # Lines after (for continuity)
    line_start: int      # Starting line number
    line_end: int        # Ending line number
    preservation_constraints: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "target_section": self.target_section,
            "before_context": self.before_context,
            "after_context": self.after_context,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "preservation_constraints": self.preservation_constraints,
        }


@dataclass
class SafetyViolation:
    """Represents a safety rule violation."""

    severity: str  # "critical", "high", "medium", "low"
    violation_type: str
    description: str
    detail: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "severity": self.severity,
            "violation_type": self.violation_type,
            "description": self.description,
            "detail": self.detail,
        }


@dataclass
class SafetyScore:
    """Safety score for enhancement result."""

    overall_score: float  # 0.0 to 1.0
    keyword_preservation: float
    structure_preservation: float
    content_stability: float
    technical_accuracy: float

    violations: List[SafetyViolation] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def is_safe_to_apply(self) -> bool:
        """True if score > 0.8 and no critical violations."""
        return self.overall_score > 0.8 and not any(
            v.severity == "critical" for v in self.violations
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "overall_score": self.overall_score,
            "keyword_preservation": self.keyword_preservation,
            "structure_preservation": self.structure_preservation,
            "content_stability": self.content_stability,
            "technical_accuracy": self.technical_accuracy,
            "violations": [v.to_dict() for v in self.violations],
            "warnings": self.warnings,
            "is_safe_to_apply": self.is_safe_to_apply(),
        }


@dataclass
class AppliedRecommendation:
    """Result of applying a single recommendation."""

    recommendation_id: str
    recommendation_type: str
    applied: bool
    original_section: Optional[str] = None
    enhanced_section: Optional[str] = None
    changes_made: Optional[str] = None
    confidence: float = 1.0
    reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "recommendation_id": self.recommendation_id,
            "recommendation_type": self.recommendation_type,
            "applied": self.applied,
            "original_section": self.original_section,
            "enhanced_section": self.enhanced_section,
            "changes_made": self.changes_made,
            "confidence": self.confidence,
            "reason": self.reason,
        }


@dataclass
class SkippedRecommendation:
    """Recommendation that was skipped."""

    recommendation_id: str
    recommendation_type: str
    reason: str
    severity: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "recommendation_id": self.recommendation_id,
            "recommendation_type": self.recommendation_type,
            "reason": self.reason,
            "severity": self.severity,
        }


@dataclass
class EnhancementResult:
    """Complete result of enhancement operation."""

    original_content: str
    enhanced_content: str

    # Applied/skipped recommendations
    applied_recommendations: List[AppliedRecommendation] = field(default_factory=list)
    skipped_recommendations: List[SkippedRecommendation] = field(default_factory=list)

    # Diff information
    unified_diff: str = ""
    lines_added: int = 0
    lines_removed: int = 0
    lines_modified: int = 0

    # Safety information
    safety_score: Optional[SafetyScore] = None

    # Metadata
    enhancement_id: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    processing_time_ms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "original_content": self.original_content,
            "enhanced_content": self.enhanced_content,
            "applied_recommendations": [r.to_dict() for r in self.applied_recommendations],
            "skipped_recommendations": [r.to_dict() for r in self.skipped_recommendations],
            "unified_diff": self.unified_diff,
            "lines_added": self.lines_added,
            "lines_removed": self.lines_removed,
            "lines_modified": self.lines_modified,
            "safety_score": self.safety_score.to_dict() if self.safety_score else None,
            "enhancement_id": self.enhancement_id,
            "created_at": self.created_at.isoformat(),
            "processing_time_ms": self.processing_time_ms,
        }


# ==============================================================================
# Context Extraction
# ==============================================================================

class ContextExtractor:
    """Extracts context windows for targeted edits."""

    def __init__(self, window_lines: int = 10):
        """
        Initialize context extractor.

        Args:
            window_lines: Number of lines to include before/after target
        """
        self.window_lines = window_lines

    def extract_edit_context(
        self,
        content: str,
        recommendation: Dict[str, Any],
        rules: PreservationRules
    ) -> Optional[EditContext]:
        """
        Extract the relevant section around the recommendation location.

        Args:
            content: Full markdown content
            recommendation: Recommendation with location/scope information
            rules: Preservation rules to apply

        Returns:
            EditContext with target section and surrounding context
        """
        lines = content.splitlines()
        total_lines = len(lines)

        # Determine target line range from recommendation
        line_start, line_end = self._get_recommendation_range(
            recommendation, lines
        )

        if line_start < 0 or line_end >= total_lines:
            logger.warning(
                f"Recommendation range out of bounds: {line_start}-{line_end} "
                f"(total: {total_lines})"
            )
            return None

        # Extract context windows
        before_start = max(0, line_start - self.window_lines)
        before_context = "\n".join(lines[before_start:line_start])

        target_section = "\n".join(lines[line_start:line_end + 1])

        after_end = min(total_lines, line_end + 1 + self.window_lines)
        after_context = "\n".join(lines[line_end + 1:after_end])

        # Extract preservation constraints from target section
        constraints = self._extract_constraints(target_section, rules)

        return EditContext(
            target_section=target_section,
            before_context=before_context,
            after_context=after_context,
            line_start=line_start,
            line_end=line_end,
            preservation_constraints=constraints
        )

    def _get_recommendation_range(
        self,
        recommendation: Dict[str, Any],
        lines: List[str]
    ) -> Tuple[int, int]:
        """
        Determine line range from recommendation metadata.

        Returns:
            (line_start, line_end) - 0-indexed, inclusive
        """
        # Check if recommendation has explicit line numbers
        if "line_start" in recommendation and "line_end" in recommendation:
            return (
                int(recommendation["line_start"]),
                int(recommendation["line_end"])
            )

        # Check for scope-based targeting
        scope = recommendation.get("scope", "").lower()

        if "frontmatter" in scope:
            # Find YAML frontmatter
            if lines and lines[0].strip() == "---":
                for i in range(1, len(lines)):
                    if lines[i].strip() == "---":
                        return (0, i)
            return (0, 0)

        elif "prerequisites" in scope or "requirements" in scope:
            # Find prerequisites/requirements section
            for i, line in enumerate(lines):
                if re.match(r"^#{1,3}\s+(prerequisites|requirements)", line, re.IGNORECASE):
                    # Find end of section (next heading or 10 lines)
                    end = i + 10
                    for j in range(i + 1, min(i + 50, len(lines))):
                        if re.match(r"^#{1,3}\s+", lines[j]):
                            end = j - 1
                            break
                    return (i, end)

        elif "heading" in scope:
            # Find specific heading
            target_text = recommendation.get("target_heading", "")
            if target_text:
                for i, line in enumerate(lines):
                    if target_text.lower() in line.lower() and line.strip().startswith("#"):
                        return (i, i)

        # Default: find text match
        target_text = recommendation.get("target_text", "")
        if target_text:
            for i, line in enumerate(lines):
                if target_text in line:
                    # Include surrounding context
                    start = max(0, i - 2)
                    end = min(len(lines) - 1, i + 2)
                    return (start, end)

        # Fallback: use global scope (first 20% of document)
        return (0, max(0, len(lines) // 5))

    def _extract_constraints(
        self,
        target_section: str,
        rules: PreservationRules
    ) -> List[str]:
        """Extract specific preservation constraints from target section."""
        constraints = []

        # Check for keywords that must be preserved
        for keyword in rules.preserve_keywords:
            if keyword in target_section:
                constraints.append(f"MUST preserve keyword: '{keyword}'")

        # Check for code blocks
        if rules.preserve_code_blocks and "```" in target_section:
            constraints.append("MUST preserve code blocks intact")

        # Check for lists
        if rules.preserve_numbered_lists and re.search(r"^\d+\.", target_section, re.MULTILINE):
            constraints.append("MUST preserve numbered list structure")

        # Check for tables
        if rules.preserve_tables and "|" in target_section:
            constraints.append("MUST preserve table structure")

        return constraints


# ==============================================================================
# Recommendation Type Handlers
# ==============================================================================

class BaseRecommendationHandler:
    """Base class for recommendation type handlers."""

    def __init__(self, model: str = "llama3.2"):
        """Initialize handler with LLM model."""
        self.model = model

    def get_prompt_template(self) -> str:
        """Return the prompt template for this handler type."""
        raise NotImplementedError

    async def apply(
        self,
        context: EditContext,
        recommendation: Dict[str, Any],
        rules: PreservationRules
    ) -> Tuple[str, float]:
        """
        Apply recommendation to context.

        Args:
            context: Edit context window
            recommendation: Recommendation details
            rules: Preservation rules

        Returns:
            (enhanced_section, confidence_score)
        """
        raise NotImplementedError


class PluginMentionHandler(BaseRecommendationHandler):
    """Handles adding missing plugin mentions."""

    def get_prompt_template(self) -> str:
        return """Task: Add mention of required plugin in prerequisites section.

Context Before:
{before_context}

Target Section:
{target_section}

Context After:
{after_context}

Recommendation:
- Plugin: {plugin_name}
- Reason: {reason}
- Suggested addition: {suggested_text}

STRICT REQUIREMENTS:
1. Add ONLY the plugin mention
2. Preserve ALL existing plugin mentions
3. Maintain consistent formatting with existing entries
4. Keep exact technical terms unchanged
5. Do not alter any other section

{preservation_constraints}

Output ONLY the modified target section (no explanations, no markdown formatting)."""

    async def apply(
        self,
        context: EditContext,
        recommendation: Dict[str, Any],
        rules: PreservationRules
    ) -> Tuple[str, float]:
        """Apply plugin mention addition."""
        prompt = self.get_prompt_template().format(
            before_context=context.before_context[-500:],  # Last 500 chars
            target_section=context.target_section,
            after_context=context.after_context[:500],     # First 500 chars
            plugin_name=recommendation.get("plugin_name", ""),
            reason=recommendation.get("reason", ""),
            suggested_text=recommendation.get("suggested_addition", ""),
            preservation_constraints="\n".join(
                f"{i+1}. {c}" for i, c in enumerate(context.preservation_constraints)
            ) if context.preservation_constraints else "No additional constraints"
        )

        try:
            ollama = get_ollama_client()
            response = await asyncio.to_thread(
                ollama.generate,
                model=self.model,
                prompt=prompt,
                options={"temperature": 0.1}  # Low temperature for precision
            )

            enhanced_section = response.get("response", "").strip()
            confidence = 0.9  # High confidence for structured task

            return enhanced_section, confidence

        except Exception as e:
            logger.error(f"Failed to apply plugin mention: {e}")
            return context.target_section, 0.0


class PluginCorrectionHandler(BaseRecommendationHandler):
    """Handles correcting incorrect plugin names."""

    def get_prompt_template(self) -> str:
        return """Task: Replace incorrect plugin name with correct name.

Context Before:
{before_context}

Target Section:
{target_section}

Context After:
{after_context}

Correction:
- Incorrect: {incorrect_name}
- Correct: {correct_name}
- Reason: {reason}

STRICT REQUIREMENTS:
1. Replace ONLY the incorrect plugin name
2. Preserve ALL surrounding context exactly
3. Maintain formatting and punctuation
4. Do not alter any other text

{preservation_constraints}

Output ONLY the modified target section (no explanations, no markdown formatting)."""

    async def apply(
        self,
        context: EditContext,
        recommendation: Dict[str, Any],
        rules: PreservationRules
    ) -> Tuple[str, float]:
        """Apply plugin name correction."""
        # For simple replacements, use direct string replacement
        incorrect = recommendation.get("found", "")
        correct = recommendation.get("expected", "")

        if incorrect and correct and incorrect in context.target_section:
            enhanced_section = context.target_section.replace(incorrect, correct, 1)
            return enhanced_section, 0.95  # Very high confidence for exact match

        # Fallback to LLM if no exact match
        prompt = self.get_prompt_template().format(
            before_context=context.before_context[-500:],
            target_section=context.target_section,
            after_context=context.after_context[:500],
            incorrect_name=incorrect,
            correct_name=correct,
            reason=recommendation.get("reason", ""),
            preservation_constraints="\n".join(
                f"{i+1}. {c}" for i, c in enumerate(context.preservation_constraints)
            ) if context.preservation_constraints else "No additional constraints"
        )

        try:
            ollama = get_ollama_client()
            response = await asyncio.to_thread(
                ollama.generate,
                model=self.model,
                prompt=prompt,
                options={"temperature": 0.1}
            )

            enhanced_section = response.get("response", "").strip()
            confidence = 0.85  # Slightly lower confidence for LLM correction

            return enhanced_section, confidence

        except Exception as e:
            logger.error(f"Failed to correct plugin name: {e}")
            return context.target_section, 0.0


class InfoAdditionHandler(BaseRecommendationHandler):
    """Handles adding missing technical information."""

    def get_prompt_template(self) -> str:
        return """Task: Add missing technical information to section.

Context Before:
{before_context}

Target Section:
{target_section}

Context After:
{after_context}

Information to Add:
{info_to_add}

Reason: {reason}

STRICT REQUIREMENTS:
1. Add the missing information naturally
2. Preserve ALL existing technical terms and details
3. Maintain consistent tone and style
4. Keep section structure intact
5. Do not remove or alter existing content

{preservation_constraints}

Output ONLY the modified target section (no explanations, no markdown formatting)."""

    async def apply(
        self,
        context: EditContext,
        recommendation: Dict[str, Any],
        rules: PreservationRules
    ) -> Tuple[str, float]:
        """Apply information addition."""
        prompt = self.get_prompt_template().format(
            before_context=context.before_context[-500:],
            target_section=context.target_section,
            after_context=context.after_context[:500],
            info_to_add=recommendation.get("suggested_addition", ""),
            reason=recommendation.get("reason", ""),
            preservation_constraints="\n".join(
                f"{i+1}. {c}" for i, c in enumerate(context.preservation_constraints)
            ) if context.preservation_constraints else "No additional constraints"
        )

        try:
            ollama = get_ollama_client()
            response = await asyncio.to_thread(
                ollama.generate,
                model=self.model,
                prompt=prompt,
                options={"temperature": 0.2}  # Slightly higher for creative addition
            )

            enhanced_section = response.get("response", "").strip()
            confidence = 0.80  # Moderate confidence for content addition

            return enhanced_section, confidence

        except Exception as e:
            logger.error(f"Failed to add information: {e}")
            return context.target_section, 0.0


# ==============================================================================
# Main RecommendationEnhancer
# ==============================================================================

class RecommendationEnhancer:
    """
    Applies approved recommendations with surgical precision.

    Features:
    - Recommendation-driven surgical edits
    - Keyword and SEO preservation
    - Structural integrity maintenance
    - Comprehensive validation and safety checks
    """

    def __init__(
        self,
        model: str = "llama3.2",
        window_lines: int = 10
    ):
        """
        Initialize recommendation enhancer.

        Args:
            model: LLM model to use for enhancements
            window_lines: Context window size (lines before/after)
        """
        self.model = model
        self.context_extractor = ContextExtractor(window_lines)

        # Initialize handlers
        self.handlers: Dict[str, BaseRecommendationHandler] = {
            "missing_plugin": PluginMentionHandler(model),
            "incorrect_plugin": PluginCorrectionHandler(model),
            "missing_info": InfoAdditionHandler(model),
        }

        logger.info(f"Initialized RecommendationEnhancer with model={model}")

    async def enhance_from_recommendations(
        self,
        content: str,
        recommendations: List[Dict[str, Any]],
        preservation_rules: PreservationRules,
        file_path: Optional[str] = None
    ) -> EnhancementResult:
        """
        Apply recommendations one by one with context preservation.

        Args:
            content: Original markdown content
            recommendations: Approved recommendations to apply
            preservation_rules: Keywords, structure, SEO elements to preserve
            file_path: Optional file path for logging

        Returns:
            EnhancementResult with edits, diff, safety score
        """
        import time
        start_time = time.time()

        logger.info(
            f"Starting enhancement: {len(recommendations)} recommendations, "
            f"content_length={len(content)}"
        )

        enhanced_content = content
        applied_recs: List[AppliedRecommendation] = []
        skipped_recs: List[SkippedRecommendation] = []

        # Sort recommendations by confidence (highest first)
        sorted_recs = sorted(
            recommendations,
            key=lambda r: r.get("confidence", 0.5),
            reverse=True
        )

        # Apply each recommendation
        for rec in sorted_recs:
            rec_id = rec.get("id", "unknown")
            rec_type = rec.get("type", "unknown")

            # Check if we have a handler for this type
            if rec_type not in self.handlers:
                skipped_recs.append(SkippedRecommendation(
                    recommendation_id=rec_id,
                    recommendation_type=rec_type,
                    reason=f"No handler available for type: {rec_type}",
                    severity=rec.get("severity", "medium")
                ))
                continue

            # Extract edit context
            context = self.context_extractor.extract_edit_context(
                enhanced_content, rec, preservation_rules
            )

            if not context:
                skipped_recs.append(SkippedRecommendation(
                    recommendation_id=rec_id,
                    recommendation_type=rec_type,
                    reason="Could not extract edit context",
                    severity=rec.get("severity", "medium")
                ))
                continue

            # Apply handler
            try:
                handler = self.handlers[rec_type]
                enhanced_section, confidence = await handler.apply(
                    context, rec, preservation_rules
                )

                # Validate the enhanced section using EditValidator
                validator = get_edit_validator()
                validation_result = validator.validate_edit(
                    context.target_section,
                    enhanced_section,
                    rec,
                    preservation_rules
                )

                if validation_result.is_valid:
                    # Replace target section in content
                    lines = enhanced_content.splitlines()
                    lines[context.line_start:context.line_end + 1] = enhanced_section.splitlines()
                    enhanced_content = "\n".join(lines)

                    applied_recs.append(AppliedRecommendation(
                        recommendation_id=rec_id,
                        recommendation_type=rec_type,
                        applied=True,
                        original_section=context.target_section,
                        enhanced_section=enhanced_section,
                        changes_made=f"Applied {rec_type} edit (score: {validation_result.keyword_preservation_score:.2f})",
                        confidence=confidence
                    ))

                    logger.info(
                        f"Applied recommendation {rec_id} (type={rec_type}, "
                        f"confidence={confidence:.2f}, validation_score={validation_result.keyword_preservation_score:.2f})"
                    )
                else:
                    # Get reason from violations
                    reason = validation_result.violations[0].description if validation_result.violations else "Failed safety validation"

                    skipped_recs.append(SkippedRecommendation(
                        recommendation_id=rec_id,
                        recommendation_type=rec_type,
                        reason=reason,
                        severity=rec.get("severity", "medium")
                    ))
                    logger.warning(
                        f"Skipped recommendation {rec_id}: {reason} "
                        f"(score: {validation_result.keyword_preservation_score:.2f})"
                    )

            except Exception as e:
                logger.error(f"Error applying recommendation {rec_id}: {e}")
                skipped_recs.append(SkippedRecommendation(
                    recommendation_id=rec_id,
                    recommendation_type=rec_type,
                    reason=f"Error: {str(e)}",
                    severity=rec.get("severity", "medium")
                ))

        # Generate diff
        unified_diff, lines_added, lines_removed, lines_modified = self._generate_diff(
            content, enhanced_content
        )

        # Calculate comprehensive safety score using EditValidator
        validator = get_edit_validator()
        safety_score = validator.calculate_enhanced_safety_score(
            content, enhanced_content, preservation_rules, applied_recs
        )

        processing_time = int((time.time() - start_time) * 1000)

        logger.info(
            f"Enhancement complete: applied={len(applied_recs)}, "
            f"skipped={len(skipped_recs)}, time={processing_time}ms"
        )

        return EnhancementResult(
            original_content=content,
            enhanced_content=enhanced_content,
            applied_recommendations=applied_recs,
            skipped_recommendations=skipped_recs,
            unified_diff=unified_diff,
            lines_added=lines_added,
            lines_removed=lines_removed,
            lines_modified=lines_modified,
            safety_score=safety_score,
            enhancement_id=self._generate_enhancement_id(),
            processing_time_ms=processing_time
        )

    def _validate_section_edit(
        self,
        original: str,
        enhanced: str,
        rules: PreservationRules
    ) -> bool:
        """Quick validation of section edit."""
        # Check for excessive reduction (expansion is allowed)
        original_len = max(len(original), 1)
        enhanced_len = len(enhanced)

        if enhanced_len < original_len:
            # Content reduction - check if within limit
            reduction_percent = (original_len - enhanced_len) / original_len
            if reduction_percent > rules.max_content_reduction_percent / 100.0:
                logger.warning(f"Section edit reduction too large: {reduction_percent:.1%}")
                return False
        # Expansion is allowed without limit (adding info is good)

        # Check keyword preservation
        for keyword in rules.preserve_keywords:
            if keyword in original and keyword not in enhanced:
                logger.warning(f"Keyword lost: '{keyword}'")
                return False

        return True

    def _generate_diff(
        self,
        original: str,
        enhanced: str
    ) -> Tuple[str, int, int, int]:
        """Generate unified diff and statistics."""
        diff_lines = list(difflib.unified_diff(
            original.splitlines(keepends=True),
            enhanced.splitlines(keepends=True),
            fromfile='original',
            tofile='enhanced',
            lineterm=''
        ))

        unified_diff = "".join(diff_lines) if diff_lines else "No changes"

        # Count changes
        lines_added = sum(1 for line in diff_lines if line.startswith('+') and not line.startswith('+++'))
        lines_removed = sum(1 for line in diff_lines if line.startswith('-') and not line.startswith('---'))
        lines_modified = min(lines_added, lines_removed)

        return unified_diff, lines_added, lines_removed, lines_modified

    def _calculate_safety_score(
        self,
        original: str,
        enhanced: str,
        rules: PreservationRules
    ) -> SafetyScore:
        """Calculate basic safety score (placeholder for Phase 2)."""
        # Simple implementation for Phase 1
        keyword_score = 1.0
        structure_score = 1.0
        content_score = 1.0
        technical_score = 1.0

        violations: List[SafetyViolation] = []
        warnings: List[str] = []

        # Check keywords
        for keyword in rules.preserve_keywords:
            if keyword in original and keyword not in enhanced:
                keyword_score -= 0.1
                violations.append(SafetyViolation(
                    severity="high",
                    violation_type="keyword_loss",
                    description=f"Keyword lost: '{keyword}'"
                ))

        # Check size change
        size_change = abs(len(enhanced) - len(original)) / max(len(original), 1)
        if size_change > rules.max_content_reduction_percent / 100.0:
            content_score -= 0.2
            violations.append(SafetyViolation(
                severity="medium",
                violation_type="excessive_size_change",
                description=f"Content size changed by {size_change:.1%}"
            ))

        overall_score = (
            keyword_score + structure_score + content_score + technical_score
        ) / 4.0

        return SafetyScore(
            overall_score=max(0.0, min(1.0, overall_score)),
            keyword_preservation=keyword_score,
            structure_preservation=structure_score,
            content_stability=content_score,
            technical_accuracy=technical_score,
            violations=violations,
            warnings=warnings
        )

    def _generate_enhancement_id(self) -> str:
        """Generate unique enhancement ID."""
        import uuid
        return f"enh_{uuid.uuid4().hex[:12]}"


# ==============================================================================
# Helper Functions
# ==============================================================================

def create_default_preservation_rules(
    file_path: Optional[str] = None
) -> PreservationRules:
    """
    Create default preservation rules.

    Args:
        file_path: Optional file path to extract context-specific rules

    Returns:
        PreservationRules with defaults
    """
    return PreservationRules(
        preserve_keywords=[
            "Aspose.Words",
            "Aspose.PDF",
            "Aspose.Cells",
            "Aspose.Slides",
            ".NET",
            "C#",
            "DOCX",
            "API",
        ],
        preserve_product_names=[
            "Aspose.Words for .NET",
            "Microsoft Word",
        ],
        preserve_technical_terms=[
            "NuGet",
            "Visual Studio",
            "namespace",
            "class",
            "method",
            "property",
        ],
        preserve_code_blocks=True,
        preserve_yaml_frontmatter=True,
        preserve_heading_hierarchy=True,
        preserve_internal_links=True,
        max_content_reduction_percent=10.0,
        preserve_numbered_lists=True,
        preserve_tables=True
    )
