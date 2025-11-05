# file: tbcv\agents\fuzzy_detector.py
"""
FuzzyDetectorAgent - Generic plugin detection with configurable patterns.

Rebased changes:
- Import rule_manager from core.rule_manager (package shim).
- Register "get_contract" handler to self.get_contract (method exists).
- Provide checkpoints=[] to AgentContract to satisfy base contract signature.
"""

import re
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

try:
    import textdistance
except ImportError:
    textdistance = None

try:
    from fuzzywuzzy import fuzz, process
except ImportError:
    fuzz = None
    process = None

from agents.base import BaseAgent, AgentContract, AgentCapability, agent_registry
from core.logging import PerformanceLogger
from core.rule_manager import rule_manager  # normalized import


@dataclass
class PluginDetection:
    """Single detection instance with context."""
    plugin_id: str
    plugin_name: str
    confidence: float
    detection_type: str
    matched_text: str
    context: str
    position: int
    family: str = "words"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for API/JSON."""
        return {
            "plugin_id": self.plugin_id,
            "plugin_name": self.plugin_name,
            "confidence": self.confidence,
            "detection_type": self.detection_type,
            "matched_text": self.matched_text,
            "context": self.context,
            "position": self.position,
            "family": self.family
        }


class FuzzyDetectorAgent(BaseAgent):
    """Agent that detects plugin usage via patterns loaded from rule system."""

    def __init__(self, agent_id: Optional[str] = None):
        self.compiled_patterns: Dict[str, List[Dict[str, Any]]] = {}
        self.family_cache: Dict[str, bool] = {}
        super().__init__(agent_id)

    def _register_message_handlers(self):
        """Expose MCP methods for orchestrator/API."""
        self.register_handler("ping", self.handle_ping)
        self.register_handler("get_status", self.handle_get_status)
        # FIX: register the existing method (not a non-existent handler)
        self.register_handler("get_contract", self.get_contract)
        self.register_handler("detect_plugins", self.handle_detect_plugins)
        self.register_handler("get_plugin_patterns", self.handle_get_plugin_patterns)

    def _validate_configuration(self):
        """Load patterns from rule system."""
        # Load patterns for default family
        self._compile_family_patterns("words")

    def get_contract(self) -> AgentContract:
        """Advertise public methods + constraints for planning."""
        return AgentContract(
            agent_id=self.agent_id,
            name="FuzzyDetectorAgent",
            version="1.0.0",
            capabilities=[
                AgentCapability(
                    name="detect_plugins",
                    description="Detect plugins in text using rule-driven patterns",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"},
                            "family": {"type": "string", "default": "words"},
                            "confidence_threshold": {"type": "number", "default": 0.6}
                        },
                        "required": ["text"]
                    },
                    output_schema={"type": "object"},
                    side_effects=["read"]
                )
            ],
            max_runtime_s=30,
            confidence_threshold=0.6,
            side_effects=["read"],
            dependencies=["truth_manager"],
            checkpoints=[]  # REQUIRED by your Base AgentContract
        )

    def _compile_family_patterns(self, family: str):
        """Compile patterns for a specific family from rules."""
        try:
            family_rules = rule_manager.get_family_rules(family)
            api_patterns = family_rules.api_patterns
            plugin_aliases = family_rules.plugin_aliases

            # Load actual plugins from truth data
            truth_plugins = self._load_truth_plugins(family)

            family_compiled = {"format": [], "api": [], "method": [], "alias": []}

            # Compile API patterns and map to real plugins
            for pattern_type, patterns in api_patterns.items():
                for pattern_str in patterns:
                    try:
                        compiled = re.compile(pattern_str, re.IGNORECASE)
                        # Map pattern to real plugin instead of generating fake ID
                        plugin_mapping = self._map_pattern_to_plugin(pattern_type, truth_plugins)
                        
                        family_compiled["api"].append({
                            "plugin_id": plugin_mapping["plugin_id"],
                            "plugin_name": plugin_mapping["plugin_name"],
                            "pattern": pattern_str,
                            "compiled": compiled,
                            "family": family,
                            "pattern_type": pattern_type
                        })
                    except re.error as e:
                        self.logger.warning("Invalid regex pattern", pattern=pattern_str, error=str(e))

            self.compiled_patterns[family] = family_compiled
            self.family_cache[family] = True

        except Exception as e:
            self.logger.error(f"Failed to compile patterns for {family}: {e}")
            self.family_cache[family] = False

    def _load_truth_plugins(self, family: str) -> Dict[str, Any]:
        """Load actual plugin definitions from truth data."""
        try:
            truth_path = Path(f"truth/{family}.json")
            if truth_path.exists():
                with open(truth_path, 'r', encoding='utf-8') as f:
                    truth_data = json.load(f)
                    return {p["name"]: p for p in truth_data.get("plugins", [])}
        except Exception as e:
            self.logger.warning(f"Failed to load truth plugins: {e}")
        return {}

    def _map_pattern_to_plugin(self, pattern_type: str, truth_plugins: Dict[str, Any]) -> Dict[str, str]:
        """Map API pattern to actual plugin from truth data."""
        # Mapping rules based on pattern type
        pattern_to_plugin = {
            "save_operations": "Word Processor",
            "pdf_operations": "PDF Processor",
            "format_conversion": "Document Converter",
            "odt_operations": "ODT File Processor",
            "epub_operations": "eBook File Processor",
            "markdown_operations": "Markdown File Processor",
            "html_operations": "Web File Processor",
            "image_operations": "Image File Processor",
            "watermark_operations": "Document Watermark",
            "compare_operations": "Document Comparer",
            "merge_operations": "Document Merger",
            "split_operations": "Document Splitter",
            "printing_operations": "Document Printer",
            "reporting_operations": "LINQ Reporting Engine",
            "mailmerge_operations": "Mail Merge"
        }
        
        plugin_name = pattern_to_plugin.get(pattern_type, pattern_type.replace("_", " ").title())
        
        # Find plugin in truth data
        for name, plugin_data in truth_plugins.items():
            if name == plugin_name:
                # Generate kebab-case ID from name
                plugin_id = name.lower().replace(" ", "_")
                return {"plugin_id": plugin_id, "plugin_name": name}
        
        # Fallback to generated ID if not found
        return {
            "plugin_id": f"unknown_{pattern_type}",
            "plugin_name": plugin_name
        }

    async def handle_detect_plugins(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Detect plugins using rule-driven patterns."""
        text = params.get("text", "")
        family = params.get("family", "words")
        confidence_threshold = params.get("confidence_threshold", 0.6)

        # Ensure patterns are loaded for this family
        if family not in self.compiled_patterns:
            self._compile_family_patterns(family)

        all_detections: List[PluginDetection] = []

        # Simple detection for now
        family_patterns = self.compiled_patterns.get(family, {})
        for pattern_type in ["api"]:
            for pattern_data in family_patterns.get(pattern_type, []):
                compiled_pattern = pattern_data["compiled"]

                for match in compiled_pattern.finditer(text):
                    detection = PluginDetection(
                        plugin_id=pattern_data["plugin_id"],
                        plugin_name=pattern_data["plugin_name"],
                        confidence=0.8,
                        detection_type="fuzzy",  # Changed from "exact" to "fuzzy"
                        matched_text=match.group(),
                        context=text[max(0, match.start()-50):match.end()+50],
                        position=match.start(),
                        family=family
                    )
                    all_detections.append(detection)

        # Filter by confidence
        filtered_detections = [d for d in all_detections if d.confidence >= confidence_threshold]
        overall_confidence = 0.7 if filtered_detections else 0.0

        return {
            "detections": [d.to_dict() for d in filtered_detections],
            "detection_count": len(filtered_detections),
            "confidence": overall_confidence,
            "family": family
        }

    async def handle_get_plugin_patterns(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Expose compiled patterns for inspection."""
        family = params.get("family", "words")

        if family not in self.compiled_patterns:
            return {"family": family, "found": False, "error": "Family not loaded"}

        family_patterns = self.compiled_patterns[family]
        summary = {}
        for pattern_type, patterns in family_patterns.items():
            summary[pattern_type] = len(patterns)
        return {"family": family, "pattern_counts": summary, "total_patterns": sum(summary.values())}
