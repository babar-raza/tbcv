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
    def __init__(self, agent_id: Optional[str] = None):
        self.linked_plugins: Set[str] = set()
        super().__init__(agent_id)

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

            stats["enhanced_length"] = len(enhanced_content)
            stats["total_enhancements"] = len(enhancements)
            stats["unique_plugins_linked"] = len(self.linked_plugins)

            result = EnhancementResult(enhanced_content, enhancements, stats)
            perf.add_context(total=len(enhancements), change=len(enhanced_content) - len(content))
            return result.to_dict()

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
