# file: agents/validators/truth_validator.py
"""
Truth Validator Agent - Validates content against truth data.
Implements 3-phase validation:
  Phase 1: Rule-based validation (always runs)
  Phase 2: LLM enhancement (optional)
  Phase 3: Merge and deduplicate results
Uses ConfigLoader for configuration-driven validation.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional, Set
import asyncio

from agents.validators.base_validator import (
    BaseValidatorAgent,
    ValidationIssue,
    ValidationResult
)
from agents.base import agent_registry
from core.config_loader import ConfigLoader, get_config_loader
from core.logging import get_logger

logger = get_logger(__name__)


class TruthValidatorAgent(BaseValidatorAgent):
    """Validates content against truth data with optional LLM enhancement."""

    def __init__(self, agent_id: Optional[str] = None, config_loader: Optional[ConfigLoader] = None):
        # Initialize config BEFORE calling super().__init__()
        self._config_loader = config_loader or get_config_loader()
        self._config = self._config_loader.load("truth")
        super().__init__(agent_id or "truth_validator")

    def get_validation_type(self) -> str:
        return "truth"

    def _get_rule_based_settings(self) -> Dict[str, Any]:
        """Get Phase 1 rule-based settings."""
        return self._config.get("rule_based", {
            "check_plugin_mentions": True,
            "check_api_patterns": True,
            "check_forbidden_patterns": True,
            "case_insensitive": True
        })

    def _get_llm_settings(self, family: Optional[str] = None) -> Dict[str, Any]:
        """Get Phase 2 LLM enhancement settings."""
        defaults = {
            "enabled": True,
            "timeout_seconds": 30,
            "confidence_threshold": 0.7,
            "min_content_length": 100,
            "max_content_length": 50000,
            "fallback_on_error": True,
            "fallback_on_timeout": True,
            "fallback_on_unavailable": True,
            "check_plugin_requirements": True,
            "check_plugin_combinations": True,
            "check_missing_plugins": True,
            "check_format_compatibility": True
        }

        settings = {**defaults, **self._config.get("llm_enhancement", {})}

        # Apply family override
        if family:
            family_override = self._config_loader.get_family_override("truth", family)
            if family_override and "llm_enhancement" in family_override:
                settings.update(family_override["llm_enhancement"])

        return settings

    def _get_merge_settings(self) -> Dict[str, Any]:
        """Get Phase 3 merge settings."""
        return self._config.get("merge", {
            "dedup_strategy": "rule_based_priority",
            "tag_sources": True,
            "combine_suggestions": True
        })

    async def validate(self, content: str, context: Dict[str, Any]) -> ValidationResult:
        """
        Validate content using 3-phase flow:
        Phase 1: Rule-based validation (always runs)
        Phase 2: LLM enhancement (when enabled and available)
        Phase 3: Merge and deduplicate results
        """
        family = context.get("family", "words")
        profile = context.get("profile", self._config.profile)

        # Get active rules
        active_rules = self._config_loader.get_rules("truth", profile=profile, family=family)
        active_rule_ids = {r.id for r in active_rules}
        rule_levels = {r.id: r.level for r in active_rules}

        # Get settings
        rule_based_settings = self._get_rule_based_settings()
        llm_settings = self._get_llm_settings(family)
        merge_settings = self._get_merge_settings()

        # Phase 1: Rule-based validation (always runs)
        phase1_issues, phase1_metrics = await self._phase1_rule_based(
            content, context, active_rule_ids, rule_levels, rule_based_settings
        )

        # Phase 2: LLM enhancement (optional)
        phase2_issues = []
        phase2_metrics = {"llm_enabled": False, "llm_ran": False}

        if llm_settings.get("enabled", True):
            phase2_metrics["llm_enabled"] = True

            # Check content length limits
            content_len = len(content)
            min_len = llm_settings.get("min_content_length", 100)
            max_len = llm_settings.get("max_content_length", 50000)

            if content_len >= min_len and content_len <= max_len:
                phase2_issues, phase2_result = await self._phase2_llm_enhancement(
                    content, context, active_rule_ids, rule_levels, llm_settings
                )
                phase2_metrics.update(phase2_result)

        # Phase 3: Merge and deduplicate
        merged_issues = self._phase3_merge(
            phase1_issues, phase2_issues, merge_settings
        )

        # Calculate confidence
        error_count = len([i for i in merged_issues if i.level == "error"])
        warning_count = len([i for i in merged_issues if i.level == "warning"])
        confidence = max(0.3, 1.0 - (error_count * 0.2) - (warning_count * 0.1))

        return ValidationResult(
            confidence=confidence,
            issues=merged_issues,
            auto_fixable_count=sum(1 for i in merged_issues if i.auto_fixable),
            metrics={
                "profile": profile,
                "family": family,
                "phase1_issues": len(phase1_issues),
                "phase2_issues": len(phase2_issues),
                "merged_issues": len(merged_issues),
                **phase1_metrics,
                **phase2_metrics
            }
        )

    async def _phase1_rule_based(
        self,
        content: str,
        context: Dict[str, Any],
        active_rule_ids: Set[str],
        rule_levels: Dict[str, str],
        settings: Dict[str, Any]
    ) -> tuple[List[ValidationIssue], Dict[str, Any]]:
        """Phase 1: Rule-based validation against truth data."""
        issues: List[ValidationIssue] = []
        metrics = {"truth_data_loaded": False, "known_plugins": 0, "api_patterns_count": 0}
        family = context.get("family", "words")

        # Get truth manager
        truth_manager = agent_registry.get_agent("truth_manager")
        if not truth_manager:
            logger.warning("TruthManager not available for truth validation")
            return [ValidationIssue(
                level="warning",
                category="truth_manager_unavailable",
                message="Truth validation unavailable (TruthManager not registered)",
                suggestion="Ensure TruthManager is properly configured",
                source="rule_based"
            )], metrics

        try:
            # Load truth data
            truth_result = await truth_manager.handle_load_truth_data({"family": family})
            plugin_aliases = truth_result.get("plugin_aliases", [])
            api_patterns = truth_result.get("api_patterns", [])
            truth_data = truth_result.get("truth_data", {})

            metrics["truth_data_loaded"] = True
            metrics["known_plugins"] = len(plugin_aliases)
            metrics["api_patterns_count"] = len(api_patterns)

            # Check required fields
            required_issues = self._validate_required_fields(
                content, truth_data, rule_levels
            )
            issues.extend(required_issues)

            # Check plugin mentions
            if settings.get("check_plugin_mentions") and "check_plugin_mentions" in active_rule_ids:
                plugin_issues = self._validate_plugin_mentions(
                    content, plugin_aliases, truth_data, rule_levels, settings
                )
                issues.extend(plugin_issues)

            # Check API patterns
            if settings.get("check_api_patterns") and "check_api_patterns" in active_rule_ids:
                api_issues = self._validate_api_patterns(
                    content, api_patterns, rule_levels
                )
                issues.extend(api_issues)

            # Check forbidden patterns
            if settings.get("check_forbidden_patterns") and "check_forbidden_patterns" in active_rule_ids:
                forbidden_issues = self._validate_forbidden_patterns(
                    content, rule_levels
                )
                issues.extend(forbidden_issues)

        except Exception as e:
            logger.error(f"Error in Phase 1 validation: {e}", exc_info=True)
            issues.append(ValidationIssue(
                level="error",
                category="truth_validation_error",
                message=f"Error during truth validation: {str(e)}",
                suggestion="Check truth data files and configuration",
                source="rule_based"
            ))

        # Tag all Phase 1 issues
        for issue in issues:
            if not hasattr(issue, 'source') or not issue.source:
                issue.source = "rule_based"

        return issues, metrics

    async def _phase2_llm_enhancement(
        self,
        content: str,
        context: Dict[str, Any],
        active_rule_ids: Set[str],
        rule_levels: Dict[str, str],
        settings: Dict[str, Any]
    ) -> tuple[List[ValidationIssue], Dict[str, Any]]:
        """Phase 2: LLM-based semantic enhancement."""
        issues: List[ValidationIssue] = []
        metrics = {"llm_ran": False, "llm_confidence": 0.0}
        family = context.get("family", "words")

        # Get LLM validator
        llm_validator = agent_registry.get_agent("llm_validator")
        if not llm_validator:
            if not settings.get("fallback_on_unavailable", True):
                issues.append(ValidationIssue(
                    level="warning",
                    category="llm_validator_unavailable",
                    message="LLM enhancement unavailable",
                    source="llm"
                ))
            return issues, metrics

        try:
            # Build fuzzy detections from content (simplified extraction)
            fuzzy_detections = self._extract_fuzzy_detections(content)

            # Call LLM validator with timeout
            timeout = settings.get("timeout_seconds", 30)
            try:
                result = await asyncio.wait_for(
                    llm_validator.handle_validate_plugins({
                        "content": content,
                        "fuzzy_detections": fuzzy_detections,
                        "family": family,
                        "profile": context.get("profile", "default")
                    }),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                if not settings.get("fallback_on_timeout", True):
                    issues.append(ValidationIssue(
                        level="warning",
                        category="llm_timeout",
                        message=f"LLM validation timed out after {timeout}s",
                        source="llm"
                    ))
                return issues, {"llm_ran": False, "llm_timeout": True}

            metrics["llm_ran"] = True
            metrics["llm_confidence"] = result.get("confidence", 0.0)

            # Process LLM issues
            confidence_threshold = settings.get("confidence_threshold", 0.7)

            for llm_issue in result.get("issues", []):
                # Apply confidence threshold
                if result.get("confidence", 0) < confidence_threshold:
                    continue

                # Map LLM issue to ValidationIssue
                category = llm_issue.get("category", "llm_detected")
                level = rule_levels.get(category, llm_issue.get("level", "warning"))

                # Check if this rule is active
                if category in ["missing_plugin", "missing_prerequisite"] and "missing_plugin" not in active_rule_ids:
                    continue
                if category == "invalid_combination" and "invalid_combination" not in active_rule_ids:
                    continue

                issues.append(ValidationIssue(
                    level=level,
                    category=category,
                    message=llm_issue.get("message", "LLM-detected issue"),
                    suggestion=llm_issue.get("fix_suggestion"),
                    auto_fixable=llm_issue.get("auto_fixable", False),
                    source="llm"
                ))

            # Process missing plugins from requirements
            for req in result.get("requirements", []):
                if req.get("validation_status") == "missing_required":
                    if "missing_plugin" in active_rule_ids:
                        level = rule_levels.get("missing_plugin", "warning")
                        rec = req.get("recommendation", {})
                        issues.append(ValidationIssue(
                            level=level,
                            category="missing_plugin",
                            message=rec.get("message", f"Missing plugin: {req.get('plugin_name')}"),
                            suggestion=rec.get("suggested_addition"),
                            auto_fixable=True,
                            source="llm"
                        ))

        except Exception as e:
            logger.warning(f"Phase 2 LLM enhancement failed: {e}")
            if not settings.get("fallback_on_error", True):
                issues.append(ValidationIssue(
                    level="warning",
                    category="llm_error",
                    message=f"LLM enhancement error: {str(e)}",
                    source="llm"
                ))
            metrics["llm_error"] = str(e)

        return issues, metrics

    def _phase3_merge(
        self,
        phase1_issues: List[ValidationIssue],
        phase2_issues: List[ValidationIssue],
        settings: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """Phase 3: Merge and deduplicate issues from both phases."""
        strategy = settings.get("dedup_strategy", "rule_based_priority")
        tag_sources = settings.get("tag_sources", True)

        # Start with all Phase 1 issues (rule-based always preserved)
        merged: List[ValidationIssue] = list(phase1_issues)

        # Build a set of existing issue signatures for deduplication
        seen_signatures: Set[str] = set()
        for issue in phase1_issues:
            sig = f"{issue.category}:{issue.message[:50]}"
            seen_signatures.add(sig)

        # Add Phase 2 issues based on strategy
        for issue in phase2_issues:
            sig = f"{issue.category}:{issue.message[:50]}"

            if strategy == "rule_based_priority":
                # Only add LLM issue if no similar rule-based issue exists
                if sig not in seen_signatures:
                    if tag_sources:
                        issue.message = f"[LLM] {issue.message}"
                    merged.append(issue)
                    seen_signatures.add(sig)

            elif strategy == "llm_priority":
                # Replace rule-based with LLM if exists
                if sig in seen_signatures:
                    # Find and replace
                    for i, existing in enumerate(merged):
                        existing_sig = f"{existing.category}:{existing.message[:50]}"
                        if existing_sig == sig:
                            if tag_sources:
                                issue.message = f"[LLM] {issue.message}"
                            merged[i] = issue
                            break
                else:
                    if tag_sources:
                        issue.message = f"[LLM] {issue.message}"
                    merged.append(issue)
                    seen_signatures.add(sig)

            else:  # "both"
                if tag_sources:
                    issue.message = f"[LLM] {issue.message}"
                merged.append(issue)

        return merged

    def _validate_required_fields(
        self,
        content: str,
        truth_data: Dict[str, Any],
        rule_levels: Dict[str, str]
    ) -> List[ValidationIssue]:
        """Validate that required frontmatter fields are present."""
        import re
        issues = []

        # Get required fields from config or use defaults
        required_fields = self._config.get("required_fields", ["title", "description"])

        # Extract frontmatter
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        if not frontmatter_match:
            # No frontmatter - if required fields exist, report missing
            if required_fields:
                level = rule_levels.get("check_required_fields", "warning")
                issues.append(ValidationIssue(
                    level=level,
                    category="truth_presence",
                    message="Content missing YAML frontmatter (required fields expected)",
                    suggestion=f"Add frontmatter with required fields: {', '.join(required_fields)}",
                    auto_fixable=True,
                    source="truth"
                ))
            return issues

        frontmatter = frontmatter_match.group(1)
        level = rule_levels.get("check_required_fields", "warning")

        # Check each required field
        for field in required_fields:
            # Check if field exists in frontmatter
            field_pattern = rf'^{re.escape(field)}\s*:'
            if not re.search(field_pattern, frontmatter, re.MULTILINE):
                issues.append(ValidationIssue(
                    level=level,
                    category="truth_presence",
                    message=f"Required field '{field}' is missing from frontmatter",
                    suggestion=f"Add '{field}:' to the YAML frontmatter",
                    auto_fixable=True,
                    source="truth"
                ))

        return issues

    def _validate_plugin_mentions(
        self,
        content: str,
        known_plugins: List[str],
        truth_data: Dict[str, Any],
        rule_levels: Dict[str, str],
        settings: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """Validate that mentioned plugins exist in truth data and are declared."""
        issues = []
        case_insensitive = settings.get("case_insensitive", True)

        # Convert content for matching
        content_check = content.lower() if case_insensitive else content

        # Extract frontmatter plugins if present
        declared_plugins = set()
        import re
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        if frontmatter_match:
            frontmatter = frontmatter_match.group(1)
            # Look for plugins field
            plugins_match = re.search(r'plugins?:\s*\[([^\]]*)\]', frontmatter)
            if plugins_match:
                plugins_str = plugins_match.group(1)
                for p in plugins_str.split(','):
                    declared_plugins.add(p.strip().strip('"\'').lower())
            # Also check for plugin_ids or similar fields
            plugin_id_match = re.search(r'plugin_?ids?:\s*\[([^\]]*)\]', frontmatter)
            if plugin_id_match:
                for p in plugin_id_match.group(1).split(','):
                    declared_plugins.add(p.strip().strip('"\'').lower())

        # Check for plugin mentions in content that are not declared
        level = rule_levels.get("check_plugin_mentions", "warning")
        for plugin in known_plugins:
            plugin_check = plugin.lower() if case_insensitive else plugin
            if plugin_check in content_check:
                # Check if this plugin is declared in frontmatter
                if plugin_check not in declared_plugins:
                    issues.append(ValidationIssue(
                        level=level,
                        category="plugin_undeclared",
                        message=f"Plugin '{plugin}' is used in content but not declared in frontmatter",
                        suggestion=f"Add '{plugin}' to the plugins list in frontmatter",
                        auto_fixable=True,
                        source="truth"
                    ))
                    logger.debug(f"Found undeclared plugin mention: {plugin}")

        return issues

    def _validate_api_patterns(
        self,
        content: str,
        api_patterns: List[str],
        rule_levels: Dict[str, str]
    ) -> List[ValidationIssue]:
        """Validate API patterns mentioned in content."""
        issues = []
        lines = content.split('\n')
        in_code_block = False

        for i, line in enumerate(lines):
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                continue

            if in_code_block:
                # Check for API patterns
                for pattern in api_patterns:
                    if pattern in line:
                        logger.debug(f"Found API pattern: {pattern} at line {i+1}")

        return issues

    def _validate_forbidden_patterns(
        self,
        content: str,
        rule_levels: Dict[str, str]
    ) -> List[ValidationIssue]:
        """Check for forbidden patterns in content."""
        issues = []
        forbidden_params = self._config.get("rules", {}).get("check_forbidden_patterns", {}).get("params", {})
        patterns = forbidden_params.get("patterns", [])

        # Add common forbidden patterns if none configured
        if not patterns:
            patterns = ["deprecated_api", "insecure_method", "obsolete_function"]

        content_lower = content.lower()
        for pattern in patterns:
            if pattern.lower() in content_lower:
                level = rule_levels.get("check_forbidden_patterns", "error")
                issues.append(ValidationIssue(
                    level=level,
                    category="forbidden_pattern",
                    message=f"Forbidden pattern detected: {pattern}",
                    suggestion=f"Remove or replace '{pattern}' usage",
                    source="truth"  # Changed from "rule_based" to "truth"
                ))

        return issues

    def _extract_fuzzy_detections(self, content: str) -> List[Dict[str, Any]]:
        """Extract potential plugin mentions for LLM validation."""
        detections = []

        # Simple keyword-based detection
        keywords = [
            ("word_processor", "Word Processor", ["docx", "doc", "word"]),
            ("pdf_processor", "PDF Processor", ["pdf"]),
            ("document_converter", "Document Converter", ["convert", "conversion"]),
            ("watermark", "Watermark", ["watermark"]),
            ("merger", "Document Merger", ["merge", "merger"]),
            ("comparer", "Document Comparer", ["compare", "comparer"]),
        ]

        content_lower = content.lower()
        for plugin_id, plugin_name, triggers in keywords:
            for trigger in triggers:
                if trigger in content_lower:
                    detections.append({
                        "plugin_id": plugin_id,
                        "plugin_name": plugin_name,
                        "trigger": trigger
                    })
                    break

        return detections
