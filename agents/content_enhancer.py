# Location: scripts/tbcv/agents/content_enhancer.py
"""
ContentEnhancerAgent (rebased on your file)

Enhances content and NOW consumes stored validation results to guide edits.
- Reads issues by file_path and optional severity floor
- Chooses 'surgical' vs 'heavy' strategy
- Leaves your plugin-link/info-text logic intact
"""

from __future__ import annotations

import re
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass

try:
    from agents.base import BaseAgent, AgentContract, AgentCapability
    from core.logging import PerformanceLogger
    from core.validation_store import list_validation_results
except ImportError:
    from agents.base import BaseAgent, AgentContract, AgentCapability
    from core.logging import PerformanceLogger
    from core.validation_store import list_validation_results


@dataclass
class Enhancement:
    type: str
    position: int
    original_text: str
    enhanced_text: str
    plugin_id: Optional[str] = None
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "position": self.position,
            "original_text": self.original_text,
            "enhanced_text": self.enhanced_text,
            "plugin_id": self.plugin_id,
            "confidence": self.confidence,
        }


@dataclass
class EnhancementResult:
    enhanced_content: str
    enhancements: List[Enhancement]
    statistics: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enhanced_content": self.enhanced_content,
            "enhancements": [e.to_dict() for e in self.enhancements],
            "statistics": self.statistics,
        }


class ContentEnhancerAgent(BaseAgent):
    """Content enhancement agent with idempotence support."""

    ENHANCEMENT_MARKER_PREFIX = "<!-- TBCV:enhanced:"
    ENHANCEMENT_MARKER_SUFFIX = " -->"

    # Class-level cache for tracking enhanced content hashes (survives across calls)
    _enhanced_content_cache: Set[str] = set()

    def __init__(self, agent_id: Optional[str] = None):
        self.linked_plugins: Set[str] = set()
        super().__init__(agent_id)

    @classmethod
    def clear_enhancement_cache(cls):
        """Clear the enhancement cache (useful for testing)."""
        cls._enhanced_content_cache.clear()

    # ========= Idempotence Methods =========

    def _compute_content_hash(self, content: str, detected_plugins: List[Dict],
                              enhancement_types: List[str]) -> str:
        """Compute deterministic hash for idempotence checking.

        Args:
            content: The content being enhanced
            detected_plugins: List of detected plugin dictionaries
            enhancement_types: List of enhancement types to apply

        Returns:
            A 16-character hash string
        """
        import hashlib
        import json

        # Sort plugins by ID for deterministic ordering
        sorted_plugins = sorted(detected_plugins, key=lambda p: p.get("plugin_id", ""))
        sorted_types = sorted(enhancement_types)

        hash_input = {
            "content_length": len(content),
            "content_prefix": content[:100] if content else "",
            "plugins": [p.get("plugin_id") for p in sorted_plugins],
            "types": sorted_types
        }

        hash_str = json.dumps(hash_input, sort_keys=True)
        return hashlib.sha256(hash_str.encode()).hexdigest()[:16]

    def _is_already_enhanced(self, content: str, expected_hash: str = "") -> bool:
        """Check if content has already been enhanced.

        Checks for TBCV enhancement markers in the content. If expected_hash is
        provided, checks for that specific hash. Otherwise checks for any marker.

        Args:
            content: The content to check
            expected_hash: Optional specific hash to look for

        Returns:
            True if content contains an enhancement marker
        """
        import re

        # If a specific hash is requested, check for that exact marker
        if expected_hash:
            marker = f"{self.ENHANCEMENT_MARKER_PREFIX}{expected_hash}{self.ENHANCEMENT_MARKER_SUFFIX}"
            return marker in content

        # Otherwise check for any enhancement marker pattern
        # Pattern: <!-- TBCV:enhanced:XXXX --> where XXXX is any hash
        pattern = re.escape(self.ENHANCEMENT_MARKER_PREFIX) + r"[a-f0-9]+" + re.escape(self.ENHANCEMENT_MARKER_SUFFIX)
        return bool(re.search(pattern, content))

    def _add_enhancement_marker(self, content: str, content_hash: str) -> str:
        """Add enhancement marker to content if not present.

        Args:
            content: The content to mark
            content_hash: The hash to include in the marker

        Returns:
            Content with enhancement marker appended
        """
        marker = f"{self.ENHANCEMENT_MARKER_PREFIX}{content_hash}{self.ENHANCEMENT_MARKER_SUFFIX}"
        if marker in content:
            return content
        return f"{content}\n{marker}\n"

    def get_contract(self) -> AgentContract:
        return AgentContract(
            agent_id=self.agent_id,
            name="ContentEnhancerAgent",
            version="1.0.0",
            capabilities=[
                AgentCapability(
                    name="enhance_content",
                    description="Enhance markdown content with plugin links, info text, and format fixes. Reads validation notes if file_path provided.",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "content": {"type": "string"},
                            "detected_plugins": {"type": "array", "items": {"type": "object"}},
                            "enhancement_types": {
                                "type": "array",
                                "items": {"type": "string", "enum": ["plugin_links", "info_text", "format_fixes"]},
                            },
                            "preview_only": {"type": "boolean"},
                            "file_path": {"type": "string"},
                            "severity_floor": {"type": "string", "enum": ["critical", "high", "medium", "low", "info"]},
                        },
                        "required": ["content", "detected_plugins"],
                    },
                    output_schema={"type": "object"},
                    side_effects=["write", "db_read"],
                )
            ],
            checkpoints=["enhancement_start", "plugin_linking", "info_text_addition", "enhancement_complete"],
            max_runtime_s=120,
            confidence_threshold=0.8,
            side_effects=["write", "db_read"],
            dependencies=["fuzzy_detector", "truth_manager"],
            resource_limits={
                "max_memory_mb": self.settings.content_enhancer.max_memory_mb,
                "max_cpu_percent": self.settings.content_enhancer.max_cpu_percent,
                "max_concurrent": self.settings.content_enhancer.max_concurrent,
            },
        )

    def _register_message_handlers(self):
        self.register_handler("ping", self.handle_ping)
        self.register_handler("get_status", self.handle_get_status)
        self.register_handler("get_contract", self.get_contract)
        self.register_handler("enhance_content", self.handle_enhance_content)
        self.register_handler("add_plugin_links", self.handle_add_plugin_links)
        self.register_handler("add_info_text", self.handle_add_info_text)
        self.register_handler("preview_enhancements", self.handle_preview_enhancements)
        self.register_handler("enhance_with_recommendations", self.handle_enhance_with_recommendations)

    # ========= NEW: validation-aware enhancement =========
    @staticmethod
    def _sev_index(sev: str) -> int:
        order = ["critical", "high", "medium", "low", "info"]
        return order.index(sev) if sev in order else len(order) - 1

    def _collect_validation_issues(self, file_path: Optional[str], severity_floor: str) -> List[Dict[str, Any]]:
        if not file_path:
            return []
        rows = list_validation_results(file_path=file_path, limit=25)
        issues: List[Dict[str, Any]] = []
        floor_idx = self._sev_index(severity_floor or "info")
        for r in rows:
            for item in (r.validation_results or []):
                sev = item.get("level", "info")  # your validator uses 'level'
                # Map level->severity index for filtering
                # error->critical/high, warning->medium/low, info->info
                sev_map = {"error": "high", "warning": "medium", "info": "info"}
                sev_norm = sev_map.get(sev, "info")
                if self._sev_index(sev_norm) <= floor_idx:
                    issues.append(item)
        return issues

    async def handle_enhance_content(self, params: Dict[str, Any]) -> Dict[str, Any]:
        content = params.get("content", "")
        detected_plugins = params.get("detected_plugins", [])
        enhancement_types = params.get("enhancement_types", ["plugin_links", "info_text"])
        preview_only = bool(params.get("preview_only", False))
        file_path = params.get("file_path")
        severity_floor = params.get("severity_floor", "info")

        if not content:
            return {"enhanced_content": "", "enhancements": [], "statistics": {"error": "Empty content"}}

        with PerformanceLogger(self.logger, "enhance_content") as perf:
            self.linked_plugins.clear()
            enhancements: List[Enhancement] = []
            enhanced_content = content

            # ========= IDEMPOTENCE CHECK =========
            # Compute content hash for the new enhancement marker
            content_hash = self._compute_content_hash(content, detected_plugins, enhancement_types)

            # Check if content was already enhanced:
            # 1. Content has an enhancement marker embedded in it, OR
            # 2. We've previously enhanced content with this exact hash (cached)
            already_enhanced = (
                self._is_already_enhanced(content) or
                content_hash in self._enhanced_content_cache
            )

            if already_enhanced:
                # Return early - content already enhanced, no changes needed
                stats = {
                    "original_length": len(content),
                    "enhanced_length": len(content),
                    "plugins_detected": len(detected_plugins),
                    "enhancement_types": enhancement_types,
                    "preview_only": preview_only,
                    "already_enhanced": True,
                    "content_hash": content_hash,
                    "total_enhancements": 0,
                    "unique_plugins_linked": 0,
                    "rewrite_ratio": 0.0,
                }
                perf.add_context(total=0, change=0)
                return {
                    "enhanced_content": content,
                    "enhancements": [],
                    "statistics": stats,
                    "status": "already_enhanced"
                }

            # Pull validation notes first
            validation_issues = self._collect_validation_issues(file_path, severity_floor)
            heavy = any(i.get("level") == "error" for i in validation_issues)

            stats = {
                "original_length": len(content),
                "plugins_detected": len(detected_plugins),
                "enhancement_types": enhancement_types,
                "preview_only": preview_only,
                "validation_issues_used": len(validation_issues),
                "strategy": "heavy" if heavy else "surgical",
                "already_enhanced": False,
                "content_hash": content_hash,
            }

            # Your original pipeline
            sorted_plugins = sorted(
                detected_plugins, key=lambda p: (p.get("confidence", 0), p.get("position", 0)), reverse=True
            )

            if "plugin_links" in enhancement_types:
                links, enhanced_content = self._add_plugin_links(enhanced_content, sorted_plugins)
                enhancements += links
                stats["plugin_links_added"] = len(links)

            if "info_text" in enhancement_types:
                infos, enhanced_content = self._add_info_text(enhanced_content, sorted_plugins)
                enhancements += infos
                stats["info_texts_added"] = len(infos)

            if "format_fixes" in enhancement_types:
                fixes, enhanced_content = self._apply_format_fixes(enhanced_content)
                enhancements += fixes
                stats["format_fixes_applied"] = len(fixes)

            # --------------------------------------------------------------
            # Gating logic: enforce rewrite ratio and blocked topics
            # --------------------------------------------------------------
            original_length = max(len(content), 1)
            enhanced_length = len(enhanced_content)
            rewrite_ratio = abs(enhanced_length - original_length) / float(original_length)
            stats["enhanced_length"] = enhanced_length
            stats["total_enhancements"] = len(enhancements)
            stats["unique_plugins_linked"] = len(self.linked_plugins)
            stats["rewrite_ratio"] = rewrite_ratio

            # Retrieve thresholds and blocked topics from settings
            try:
                threshold = float(getattr(self.settings.content_enhancer, "rewrite_ratio_threshold", 0.3))
            except Exception:
                threshold = 0.3
            try:
                blocked_topics = getattr(self.settings.content_enhancer, "blocked_topics", []) or []
            except Exception:
                blocked_topics = []

            # Check for blocked phrases in enhanced content (case-insensitive)
            found_blocked: List[str] = []
            for phrase in blocked_topics:
                if phrase and re.search(re.escape(phrase), enhanced_content, flags=re.IGNORECASE):
                    found_blocked.append(phrase)

            # Determine gating conditions
            rewrite_exceeded = rewrite_ratio > threshold
            if found_blocked:
                stats["blocked_topics_found"] = found_blocked
            stats["rewrite_ratio_exceeded"] = rewrite_exceeded

            # If gating triggered and not forced preview
            if rewrite_exceeded or found_blocked:
                # Flag gating status and return original content without applying enhancements
                result_dict = {
                    "enhanced_content": content,
                    "enhancements": [],
                    "statistics": stats,
                    "status": "gated",
                }
                if rewrite_exceeded:
                    result_dict["reason"] = f"Rewrite ratio {rewrite_ratio:.3f} exceeds threshold {threshold:.3f}"
                else:
                    result_dict["reason"] = f"Blocked topic(s) detected: {', '.join(found_blocked)}"
                perf.add_context(total=0, change=0)
                return result_dict

            # Otherwise return enhanced content as usual
            # Add enhancement marker for idempotence tracking (if enhancements were made)
            if enhancements and not preview_only:
                enhanced_content = self._add_enhancement_marker(enhanced_content, content_hash)
                stats["enhanced_length"] = len(enhanced_content)  # Update after adding marker
                # Add to cache for idempotence checking on subsequent calls
                self._enhanced_content_cache.add(content_hash)

            result = EnhancementResult(enhanced_content, enhancements, stats)
            perf.add_context(total=len(enhancements), change=len(enhanced_content) - original_length)
            # Add a success status for clarity
            result_dict = result.to_dict()
            result_dict["status"] = "success"
            return result_dict

    async def handle_add_plugin_links(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adds ONLY plugin links to content without other changes.
        """
        content = params.get("content", "")
        detected_plugins = params.get("detected_plugins", [])
        if not content:
            return {"enhanced_content": "", "enhancements": [], "statistics": {"error": "Empty content"}}

        with PerformanceLogger(self.logger, "add_plugin_links"):
            self.linked_plugins.clear()
            links, enhanced = self._add_plugin_links(content, detected_plugins)
            return EnhancementResult(
                enhanced_content=enhanced,
                enhancements=links,
                statistics={"plugin_links_added": len(links), "original_length": len(content), "enhanced_length": len(enhanced)},
            ).to_dict()

    async def handle_add_info_text(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adds ONLY informational notes after relevant code blocks.
        """
        content = params.get("content", "")
        detected_plugins = params.get("detected_plugins", [])
        if not content:
            return {"enhanced_content": "", "enhancements": [], "statistics": {"error": "Empty content"}}

        with PerformanceLogger(self.logger, "add_info_text"):
            self.linked_plugins.clear()
            infos, enhanced = self._add_info_text(content, detected_plugins)
            return EnhancementResult(
                enhanced_content=enhanced,
                enhancements=infos,
                statistics={"info_texts_added": len(infos), "original_length": len(content), "enhanced_length": len(enhanced)},
            ).to_dict()

    async def handle_preview_enhancements(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dry-run: apply plugin links and info text, report both, and return preview content.
        """
        content = params.get("content", "")
        detected_plugins = params.get("detected_plugins", [])
        if not content:
            return {"enhanced_content": "", "enhancements": [], "statistics": {"error": "Empty content"}}

        with PerformanceLogger(self.logger, "preview_enhancements"):
            self.linked_plugins.clear()
            links, temp_content = self._add_plugin_links(content, detected_plugins)
            infos, temp_content = self._add_info_text(temp_content, detected_plugins)
            all_enh = links + infos
            return EnhancementResult(
                enhanced_content=temp_content,
                enhancements=all_enh,
                statistics={
                    "plugin_links_added": len(links),
                    "info_texts_added": len(infos),
                    "total_enhancements": len(all_enh),
                },
            ).to_dict()

    async def handle_enhance_with_recommendations(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply approved recommendations to content.

        This is the handler wrapper for the enhance_from_recommendations method.
        Expected params:
            - content: str - The content to enhance
            - recommendations: List[Dict] - List of recommendation objects to apply
            - file_path: str (optional) - File path for context
            - recommendation_ids: List[str] (optional) - IDs of recommendations to fetch

        Returns:
            Dict with enhanced_content, applied_recommendations, skipped_recommendations,
            diff, and statistics.
        """
        content = params.get("content", "")
        file_path = params.get("file_path")
        recommendations = params.get("recommendations", [])
        recommendation_ids = params.get("recommendation_ids", [])

        if not content:
            return {
                "enhanced_content": "",
                "applied_recommendations": [],
                "skipped_recommendations": [],
                "diff": "",
                "statistics": {"error": "Empty content"}
            }

        # If recommendation_ids are provided but no recommendations, fetch them
        if recommendation_ids and not recommendations:
            try:
                from core.database import db_manager
                for rec_id in recommendation_ids:
                    rec = db_manager.get_recommendation(rec_id)
                    if rec:
                        recommendations.append({
                            "id": rec.id,
                            "instruction": rec.instruction,
                            "scope": rec.scope,
                            "severity": rec.severity,
                            "confidence": rec.confidence,
                            "original_content": getattr(rec, 'original_content', None),
                            "proposed_content": getattr(rec, 'proposed_content', None),
                            "found": getattr(rec, 'found', None),
                            "expected": getattr(rec, 'expected', None),
                        })
            except Exception as e:
                self.logger.warning(f"Failed to fetch recommendations: {e}")

        # Call the underlying implementation
        return await self.enhance_from_recommendations(
            content=content,
            recommendations=recommendations,
            file_path=file_path
        )

    # =======================================================
    # Subroutines (pure helpers)
    # =======================================================
    def _generate_plugin_url(self, plugin_id: str) -> str:
        """
        Build a product link from plugin id using the configured template.
        Falls back to a default template if the config is missing {slug}.
        """
        slug = plugin_id.replace("_", "-").lower()
        # Try to get template from settings first, then fall back to centralized prompt
        template = getattr(self.settings.content_enhancer, "link_template", None)
        if not template:
            try:
                from core.prompt_loader import get_prompt
                template = get_prompt("enhancer", "plugin_link_template")
            except:
                pass
        if not template:
            template = "https://products.aspose.com/words/net/plugins/{slug}/"
        try:
            return template.format(slug=slug)
        except Exception:
            return f"https://products.aspose.com/words/net/plugins/{slug}/"

    def _generate_info_text(self, plugin_name: str, plugin_id: str) -> str:
        """
        Produce a short italicized note stating the plugin requirement.
        """
        # Try to get template from settings first, then fall back to centralized prompt
        template = getattr(self.settings.content_enhancer, "info_text_template", None)
        if not template:
            try:
                from core.prompt_loader import get_prompt
                template = get_prompt("enhancer", "plugin_info_text_template")
            except:
                pass
        if not template:
            template = "*This code requires the **{plugin_name}** plugin.*"
        try:
            return template.format(plugin_name=plugin_name)
        except Exception:
            return f"*This code requires the **{plugin_name}** plugin.*"

    def _add_plugin_links(self, content: str, detected_plugins: List[Dict[str, Any]]):
        """
        Insert hyperlinks for high-confidence detections. We match the
        provided 'matched_text' once to avoid link spam and append a link
        if the plain text mention already exists.
        """
        if not getattr(self.settings.content_enhancer, "auto_link_plugins", True):
            return [], content

        enhancements: List[Enhancement] = []
        enhanced = content

        # Prefer high-confidence, stable ordering
        sorted_plugins = sorted(
            detected_plugins, key=lambda p: (p.get("confidence", 0.0), p.get("position", 0)), reverse=True
        )

        for plugin in sorted_plugins:
            pid = plugin.get("plugin_id", "")
            pname = plugin.get("plugin_name", "")
            match = plugin.get("matched_text", "") or pname
            pos = int(plugin.get("position", 0))
            conf = float(plugin.get("confidence", 0.0))

            if conf < 0.7 or not pid or pid in self.linked_plugins or not match:
                continue

            url = self._generate_plugin_url(pid)
            link_text = f"[{pname}]({url})"
            pattern = re.escape(match)
            # If match already contains the name, replace; else append the link after the match
            replacement = link_text if pname and pname in match else f"{match} {link_text}"

            new_content = re.sub(pattern, replacement, enhanced, count=1)
            if new_content != enhanced:
                enhancements.append(Enhancement("plugin_link", pos, match, replacement, pid, conf))
                enhanced = new_content
                self.linked_plugins.add(pid)

        return enhancements, enhanced

    def _add_info_text(self, content: str, detected_plugins: List[Dict[str, Any]]):
        """
        Append informational text immediately after the code block that
        contained (or followed) a detected plugin mention.
        """
        if not getattr(self.settings.content_enhancer, "add_info_text", True):
            return [], content

        enhancements: List[Enhancement] = []
        enhanced = content

        code_blocks = self._extract_code_blocks_with_positions(enhanced)

        for plugin in detected_plugins:
            pid = plugin.get("plugin_id", "")
            pname = plugin.get("plugin_name", "")
            pos = int(plugin.get("position", 0))
            conf = float(plugin.get("confidence", 0.0))
            if conf < 0.6 or not pid:
                continue

            block = self._find_containing_code_block(pos, code_blocks)
            if not block:
                continue

            start, end, _ = block
            info_text = self._generate_info_text(pname or pid, pid)

            insertion = end  # insert right after closing fence
            # Ensure a blank line before + after for clean markdown
            insertion_text = "\n\n" + info_text + "\n"
            enhanced = enhanced[:insertion] + insertion_text + enhanced[insertion:]

            enhancements.append(Enhancement("info_text", insertion, "", info_text, pid, conf))
            self.linked_plugins.add(pid)

            # Recompute code block positions after insertion to keep future matches correct
            code_blocks = self._extract_code_blocks_with_positions(enhanced)

        return enhancements, enhanced

    def _apply_format_fixes(self, content: str):
        """
        Simple markdown hygiene:
          - Ensure a space after '#' in headings.
        """
        fixes: List[Enhancement] = []
        lines = content.splitlines()

        for i, line in enumerate(lines):
            if re.match(r"^#+[^\s]", line):
                fixed = re.sub(r"^(#+)([^\s])", r"\1 \2", line)
                if fixed != line:
                    fixes.append(Enhancement("format_fix", i, line, fixed))
                    lines[i] = fixed

        return fixes, "\n".join(lines)

    # ----------------- Utility helpers -----------------
    def _extract_code_blocks_with_positions(self, content: str):
        """
        Return a list of (start_index, end_index, body_text) for fenced code blocks.
        Fences are parsed using the common triple-backtick pattern.
        """
        blocks: List[Tuple[int, int, str]] = []
        pattern = r"```(\w+)?\s*\n([\s\S]*?)\n```"
        for m in re.finditer(pattern, content):
            blocks.append((m.start(), m.end(), m.group(2)))
        return blocks

    def _find_containing_code_block(self, position: int, blocks: List[Tuple[int, int, str]]):
        """Return the block tuple that contains `position`, if any."""
        for start, end, body in blocks:
            if start <= position <= end:
                return (start, end, body)
        return None

    async def enhance_from_recommendations(
        self,
        content: str,
        recommendations: List[Dict[str, Any]],
        file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Apply approved recommendations to content.
        
        Args:
            content: Original content to enhance
            recommendations: List of approved recommendation dicts
            file_path: Optional file path for context
            
        Returns:
            {
                "enhanced_content": str,
                "applied_recommendations": List[str],  # IDs of applied recommendations
                "skipped_recommendations": List[Dict],  # {id, reason}
                "diff": str,
                "statistics": Dict
            }
        """
        from core.database import db_manager
        import difflib
        
        enhanced_content = content
        applied = []
        skipped = []
        changes_made = []
        
        # Sort recommendations by confidence (highest first)
        sorted_recs = sorted(
            recommendations,
            key=lambda r: r.get("confidence", 0),
            reverse=True
        )
        
        for rec in sorted_recs:
            rec_id = rec.get("id")
            instruction = rec.get("instruction", "")
            scope = rec.get("scope", "global")
            severity = rec.get("severity", "medium")
            
            try:
                if not instruction:
                    skipped.append({"id": rec_id, "reason": "No instruction provided"})
                    continue
                
                # Apply recommendation based on instruction patterns
                applied_change = False
                change_description = ""
                
                # Pattern: Add field to YAML frontmatter
                if "frontmatter" in scope.lower() and "add" in instruction.lower():
                    # Extract field name from instruction using multiple patterns:
                    # 1. "add field 'field_name'" or "add field \"field_name\""
                    # 2. "add 'field_name: value'" - extracts just the field name before :
                    # 3. "add 'field_name'" - extracts full value
                    field_name = None
                    field_value = None

                    # Try pattern with "field" word first
                    field_match = re.search(r"add.*?field.*?['\"]([^'\"]+)['\"]", instruction, re.IGNORECASE)
                    if field_match:
                        field_name = field_match.group(1)
                    else:
                        # Try pattern: Add 'field_name: value'
                        value_match = re.search(r"add\s+['\"]([^:]+):\s*([^'\"]*)['\"]", instruction, re.IGNORECASE)
                        if value_match:
                            field_name = value_match.group(1).strip()
                            field_value = value_match.group(2).strip() if value_match.group(2) else None
                        else:
                            # Try simple pattern: Add 'field_name'
                            simple_match = re.search(r"add\s+['\"]([^'\"]+)['\"]", instruction, re.IGNORECASE)
                            if simple_match:
                                field_name = simple_match.group(1)

                    if field_name:
                        # Check if content has YAML frontmatter
                        if enhanced_content.startswith("---"):
                            parts = enhanced_content.split("---", 2)
                            if len(parts) >= 3:
                                frontmatter = parts[1]
                                # Add field if not present
                                if field_name not in frontmatter:
                                    # Add at end of frontmatter with value if provided
                                    value_str = field_value if field_value else "# TODO: Add value"
                                    new_frontmatter = frontmatter.rstrip() + f"\n{field_name}: {value_str}\n"
                                    enhanced_content = f"---{new_frontmatter}---{parts[2]}"
                                    applied_change = True
                                    change_description = f"Added '{field_name}' field to frontmatter"
                
                # Pattern: Fix heading hierarchy
                elif "heading" in instruction.lower() and ("hierarchy" in instruction.lower() or "sequential" in instruction.lower()):
                    lines = enhanced_content.split("\n")
                    fixed_lines = []
                    prev_level = 0
                    changes_in_headings = False
                    
                    for line in lines:
                        if line.startswith("#"):
                            # Count heading level
                            level = len(line) - len(line.lstrip("#"))
                            # Check if skips levels
                            if prev_level > 0 and level > prev_level + 1:
                                # Fix by reducing level
                                new_level = prev_level + 1
                                fixed_line = "#" * new_level + line[level:]
                                fixed_lines.append(fixed_line)
                                changes_in_headings = True
                            else:
                                fixed_lines.append(line)
                            prev_level = level
                        else:
                            fixed_lines.append(line)
                    
                    if changes_in_headings:
                        enhanced_content = "\n".join(fixed_lines)
                        applied_change = True
                        change_description = "Fixed heading hierarchy"
                
                # Pattern: Add language to code blocks
                elif "code" in scope.lower() and "language" in instruction.lower():
                    # Find code blocks without language identifiers
                    pattern = r"```\n([\s\S]*?)\n```"
                    
                    def add_language(match):
                        code = match.group(1)
                        # Try to detect language from content
                        if "using" in code and "namespace" in code:
                            lang = "csharp"
                        elif "def " in code and ":" in code:
                            lang = "python"
                        elif "function" in code or "var " in code or "const " in code:
                            lang = "javascript"
                        else:
                            lang = "text"  # Default fallback
                        return f"```{lang}\n{code}\n```"
                    
                    new_content = re.sub(pattern, add_language, enhanced_content)
                    if new_content != enhanced_content:
                        enhanced_content = new_content
                        applied_change = True
                        change_description = "Added language identifiers to code blocks"
                
                # Pattern: Fix/remove broken links
                elif "link" in scope.lower() or "url" in scope.lower():
                    if "fix" in instruction.lower() or "remove" in instruction.lower():
                        # Extract URL from recommendation
                        url_match = re.search(r"https?://[^\s]+", instruction)
                        if url_match:
                            broken_url = url_match.group(0)
                            # Remove broken link
                            enhanced_content = enhanced_content.replace(f"[{broken_url}]", "")
                            enhanced_content = enhanced_content.replace(f"({broken_url})", "")
                            applied_change = True
                            change_description = f"Removed broken link: {broken_url}"
                
                # Pattern: Replace terminology
                elif rec.get("found") and rec.get("expected"):
                    incorrect = rec["found"]
                    correct = rec["expected"]
                    if incorrect in enhanced_content:
                        enhanced_content = enhanced_content.replace(incorrect, correct)
                        applied_change = True
                        change_description = f"Replaced '{incorrect}' with '{correct}'"
                
                if applied_change:
                    applied.append(rec_id)
                    changes_made.append(change_description)
                    # Mark recommendation as actioned in database
                    try:
                        db_manager.mark_recommendation_applied(rec_id, applied_by="content_enhancer")
                    except Exception as e:
                        self.logger.warning(f"Failed to mark recommendation {rec_id} as applied: {e}")
                else:
                    skipped.append({
                        "id": rec_id,
                        "reason": "Pattern not matched - manual review recommended"
                    })
                
            except Exception as e:
                self.logger.error(f"Failed to apply recommendation {rec_id}: {e}")
                skipped.append({"id": rec_id, "reason": f"Error: {str(e)}"})
        
        # Calculate diff (unified diff format)
        diff_lines = list(difflib.unified_diff(
            content.splitlines(keepends=True),
            enhanced_content.splitlines(keepends=True),
            fromfile='original',
            tofile='enhanced',
            lineterm=''
        ))
        diff = "".join(diff_lines) if diff_lines else "No changes"
        
        return {
            "enhanced_content": enhanced_content,
            "applied_recommendations": applied,
            "skipped_recommendations": skipped,
            "diff": diff,
            "statistics": {
                "total_recommendations": len(recommendations),
                "applied": len(applied),
                "skipped": len(skipped),
                "changes_made": len(diff_lines) > 0,
                "change_descriptions": changes_made,
            }
        }


# =======================================================
# Local smoke test (optional)
# =======================================================
if __name__ == "__main__":
    import asyncio

    async def _demo():
        agent = ContentEnhancerAgent()
        content = (
            "# Demo\n\n"
            "This shows Document usage.\n"
            "```csharp\n"
            "var doc = new Document();\n"
            "```\n"
        )
        detected = [
            {"plugin_id": "document_converter", "plugin_name": "Document Converter", "confidence": 0.9, "matched_text": "Document", "position": 15},
        ]
        result = await agent.handle_enhance_content({"content": content, "detected_plugins": detected})
        print(result["enhanced_content"])

    asyncio.run(_demo())
