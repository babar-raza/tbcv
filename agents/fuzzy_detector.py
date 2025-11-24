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
from typing import Dict, Any, List, Optional, Tuple, Set
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
from agents.validators.base_validator import ValidationResult, ValidationIssue
from core.config import load_config_from_yaml
import difflib
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
        # Cache of plugin alias data per family
        self.alias_cache: Dict[str, Dict[str, Any]] = {}
        # Determine project root based on file location (two levels up: /project)
        try:
            self.project_root = Path(__file__).resolve().parents[1]
        except Exception:
            self.project_root = Path('.')
        # Load detector configuration on initialization
        self._load_settings()
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

    # ----------------------------------------------------------------------
    # Configuration and helper methods
    # ----------------------------------------------------------------------
    def _load_settings(self) -> None:
        """
        Load fuzzy detector configuration and truth confidence weights from YAML.
        If loading fails, default values are used.
        """
        # Defaults
        self.similarity_threshold: float = 0.85
        self.context_window_chars: int = 200
        self.fuzzy_algorithms: List[str] = ["levenshtein", "jaro_winkler"]
        # Confidence weights
        self.weight_exact: float = 1.0
        self.weight_fuzzy: float = 0.8
        self.weight_context: float = 0.1

        try:
            # Attempt to load from project root config directory
            config_path = str((self.project_root / "config" / "main.yaml").resolve())
            cfg = load_config_from_yaml(config_path) or {}
            agents_cfg = cfg.get("agents", {})
            fuzzy_cfg = agents_cfg.get("fuzzy_detector", {}) if isinstance(agents_cfg, dict) else {}
            truth_cfg = cfg.get("truth", {}) if isinstance(cfg, dict) else {}

            # Thresholds and algorithms
            self.similarity_threshold = float(fuzzy_cfg.get("similarity_threshold", self.similarity_threshold))
            self.context_window_chars = int(fuzzy_cfg.get("context_window_chars", self.context_window_chars))
            algos = fuzzy_cfg.get("fuzzy_algorithms", self.fuzzy_algorithms)
            if isinstance(algos, list):
                # Normalize algorithm names
                self.fuzzy_algorithms = [str(a).lower() for a in algos]

            # Confidence weights
            weights = truth_cfg.get("confidence_weights", {}) if isinstance(truth_cfg, dict) else {}
            self.weight_exact = float(weights.get("exact_match", self.weight_exact))
            self.weight_fuzzy = float(weights.get("fuzzy_match", self.weight_fuzzy))
            self.weight_context = float(weights.get("context_match", self.weight_context))
        except Exception:
            # Silently fallback to defaults
            pass

    def _normalize(self, s: str) -> str:
        """Normalize strings by removing non-alphanumeric characters and lowering case."""
        return re.sub(r"[^a-zA-Z0-9]", "", s or "").lower()

    def _get_truth_plugins(self, family: str) -> List[Dict[str, Any]]:
        """
        Load plugin definitions from truth files based on configuration.
        Falls back to default truth/{family}.json if mapping not provided.
        """
        # Determine truth file path based on main config
        truth_plugins: List[Dict[str, Any]] = []
        # Load config relative to project root
        config_path = str((self.project_root / "config" / "main.yaml").resolve())
        cfg = load_config_from_yaml(config_path) or {}
        truth_cfg = cfg.get("truth", {}) if isinstance(cfg, dict) else {}
        truth_files = truth_cfg.get("truth_files", {}) if isinstance(truth_cfg, dict) else {}
        # Mapping may not use family keys directly (e.g. 'words': path)
        truth_path = truth_files.get(family)
        if not truth_path:
            # Fallback: try truth/{family}.json within project root
            truth_path = str(self.project_root / "truth" / f"{family}.json")
        else:
            # Resolve relative paths against project root
            truth_path = str((self.project_root / Path(truth_path)).resolve())

        try:
            p = Path(truth_path)
            if p.exists():
                with p.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                    plugins = data.get("plugins", [])
                    if isinstance(plugins, list):
                        truth_plugins = plugins
        except Exception:
            pass
        return truth_plugins

    def _build_family_aliases(self, family: str) -> Dict[str, Any]:
        """
        Build alias dictionaries for each plugin in a family.
        Returns mapping of plugin_id -> {"name": plugin_name, "aliases": [alias strings]}.
        """
        alias_map: Dict[str, Any] = {}
        # Get plugin alias overrides from rules
        try:
            family_rules = rule_manager.get_family_rules(family)
            plugin_aliases_overrides = getattr(family_rules, "plugin_aliases", {})
        except Exception:
            plugin_aliases_overrides = {}

        # Load truth plugins
        truth_plugins = self._get_truth_plugins(family)

        for plugin in truth_plugins:
            plugin_id = plugin.get("id") or plugin.get("slug") or plugin.get("name") or "unknown"
            plugin_name = plugin.get("name") or plugin_id
            aliases: Set[str] = set()

            # Core identifiers
            if plugin.get("slug"):
                aliases.add(plugin.get("slug"))
            if plugin.get("id"):
                aliases.add(plugin.get("id"))
            if plugin.get("name"):
                aliases.add(plugin.get("name"))
            if plugin.get("short_name"):
                aliases.add(plugin.get("short_name"))

            # Include pattern values as aliases
            patterns = plugin.get("patterns", {}) or {}
            for key, values in patterns.items():
                if isinstance(values, list):
                    for v in values:
                        if isinstance(v, str):
                            aliases.add(v)

            # Include plugin alias overrides
            override_aliases = plugin_aliases_overrides.get(plugin_id, [])
            for a in override_aliases:
                aliases.add(a)

            # Normalize and dedupe aliases
            normalized_aliases = []
            for a in aliases:
                norm = self._normalize(a)
                if norm:
                    normalized_aliases.append(norm)

            alias_map[plugin_id] = {
                "name": plugin_name,
                "aliases": sorted(set(normalized_aliases))
            }

        return alias_map

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

        # ------------------------------------------------------------------
        # 1. Regex-based detection using compiled API patterns from rules
        # ------------------------------------------------------------------
        family_patterns = self.compiled_patterns.get(family, {})
        for pattern_type in ["api"]:
            for pattern_data in family_patterns.get(pattern_type, []):
                compiled_pattern = pattern_data["compiled"]

                for match in compiled_pattern.finditer(text):
                    # Assign confidence using fuzzy weight
                    detection_conf = self.weight_fuzzy
                    detection = PluginDetection(
                        plugin_id=pattern_data["plugin_id"],
                        plugin_name=pattern_data["plugin_name"],
                        confidence=detection_conf,
                        detection_type="regex",
                        matched_text=match.group(),
                        context=text[max(0, match.start()-self.context_window_chars): match.end()+self.context_window_chars],
                        position=match.start(),
                        family=family
                    )
                    all_detections.append(detection)

        # ------------------------------------------------------------------
        # 2. Alias-based detection using fuzzy algorithms and similarity ratios
        # ------------------------------------------------------------------
        # Load alias data for the family if not cached
        if family not in self.alias_cache:
            try:
                self.alias_cache[family] = self._build_family_aliases(family)
            except Exception:
                self.alias_cache[family] = {}
        alias_data = self.alias_cache.get(family, {})

        # Precompute tokens and their positions in the text
        token_matches = list(re.finditer(r"\b\w+\b", text))
        tokens = []  # list of (token, start_idx, end_idx)
        for m in token_matches:
            tokens.append((m.group(), m.start(), m.end()))

        for plugin_id, info in alias_data.items():
            plugin_name = info.get("name", plugin_id)
            aliases = info.get("aliases", [])
            for alias_norm in aliases:
                # Skip overly long aliases to avoid performance issues
                if not alias_norm:
                    continue
                for token, start_idx, end_idx in tokens:
                    token_norm = self._normalize(token)
                    if not token_norm:
                        continue
                    # Exact match
                    if alias_norm == token_norm:
                        conf = self.weight_exact
                        detection_type = "exact"
                        matched_text = token
                    else:
                        # Calculate similarity scores using selected algorithms
                        scores: List[float] = []
                        for algo in self.fuzzy_algorithms:
                            try:
                                if algo == "levenshtein" and textdistance and hasattr(textdistance, "levenshtein"):
                                    # Normalized Levenshtein similarity
                                    distance = textdistance.levenshtein.distance(alias_norm, token_norm)
                                    max_len = max(len(alias_norm), len(token_norm)) or 1
                                    score = 1.0 - (distance / max_len)
                                elif algo == "jaro_winkler" and textdistance and hasattr(textdistance, "jaro_winkler"):
                                    score = textdistance.jaro_winkler.normalized_similarity(alias_norm, token_norm)
                                elif algo == "fuzzy" and fuzz:
                                    score = fuzz.ratio(alias_norm, token_norm) / 100.0
                                else:
                                    # Fallback: SequenceMatcher ratio
                                    score = difflib.SequenceMatcher(None, alias_norm, token_norm).ratio()
                                scores.append(score)
                            except Exception:
                                continue
                        if not scores:
                            continue
                        best_score = max(scores)
                        if best_score < self.similarity_threshold:
                            continue
                        conf = best_score * self.weight_fuzzy
                        detection_type = "fuzzy"
                        matched_text = token

                    # Apply confidence threshold later; collect detection now
                    detection = PluginDetection(
                        plugin_id=plugin_id,
                        plugin_name=plugin_name,
                        confidence=conf,
                        detection_type=detection_type,
                        matched_text=matched_text,
                        context=text[max(0, start_idx - self.context_window_chars): min(len(text), end_idx + self.context_window_chars)],
                        position=start_idx,
                        family=family
                    )
                    all_detections.append(detection)

        # ------------------------------------------------------------------
        # 3. Deduplicate detections: keep highest-confidence detection per plugin at each position
        # ------------------------------------------------------------------
        deduped: Dict[Tuple[str, int], PluginDetection] = {}
        for det in all_detections:
            key = (det.plugin_id, det.position)
            existing = deduped.get(key)
            if existing is None or det.confidence > existing.confidence:
                deduped[key] = det

        # Filter by confidence
        filtered_detections: List[PluginDetection] = [d for d in deduped.values() if d.confidence >= confidence_threshold]
        # Sort detections by position then plugin name for determinism
        filtered_detections.sort(key=lambda d: (d.position, d.plugin_name))

        # ------------------------------------------------------------------
        # 4. Compute aggregated confidence per plugin and stage-level confidence
        # ------------------------------------------------------------------
        from math import prod

        plugin_scores: Dict[str, List[float]] = {}
        for det in filtered_detections:
            plugin_scores.setdefault(det.plugin_id, []).append(det.confidence)

        plugin_confidences: Dict[str, float] = {}
        for pid, confs in plugin_scores.items():
            # Combine multiple detection confidences for a plugin.
            # Use 1 - product(1 - c) to reflect multiple independent signals.
            try:
                combined = 1.0 - prod([(1.0 - c) for c in confs])
            except Exception:
                # fallback: sum but cap at 1.0
                combined = sum(confs)
                if combined > 1.0:
                    combined = 1.0
            # Round for deterministic output
            plugin_confidences[pid] = float(round(combined, 4))

        # Stage-level confidence is the maximum of all plugin confidences
        if plugin_confidences:
            stage_confidence = max(plugin_confidences.values())
        else:
            stage_confidence = 0.0

        return {
            "detections": [d.to_dict() for d in filtered_detections],
            "detection_count": len(filtered_detections),
            "plugin_confidences": plugin_confidences,
            "confidence": float(round(stage_confidence, 4)),
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

    async def validate(self, content: str, context: Dict[str, Any]) -> ValidationResult:
        """
        Validate content for plugin usage via fuzzy detection.
        Implements the validator interface expected by ValidatorRouter.

        Args:
            content: The content to validate
            context: Validation context (file_path, family, etc.)

        Returns:
            ValidationResult with plugin detection results as issues
        """
        family = context.get("family", "words")
        confidence_threshold = context.get("confidence_threshold", 0.6)

        # Run plugin detection
        detection_result = await self.handle_detect_plugins({
            "text": content,
            "family": family,
            "confidence_threshold": confidence_threshold
        })

        # Convert detections to validation issues
        issues: List[ValidationIssue] = []
        detections = detection_result.get("detections", [])

        for detection in detections:
            # Create informational issue for each detected plugin
            issue = ValidationIssue(
                level="info",
                category="plugin_detection",
                message=f"Detected plugin: {detection['plugin_name']} (confidence: {detection['confidence']:.2%})",
                line_number=None,  # Position is character-based, not line-based
                suggestion=f"Plugin detected via {detection['detection_type']} match: '{detection['matched_text']}'",
                source="fuzzy_detector",
                auto_fixable=False
            )
            issues.append(issue)

        # Extract metrics from detection result
        metrics = {
            "detection_count": detection_result.get("detection_count", 0),
            "plugin_confidences": detection_result.get("plugin_confidences", {}),
            "family": family,
            "confidence_threshold": confidence_threshold
        }

        # Overall confidence is the max confidence from all detections
        overall_confidence = detection_result.get("confidence", 0.0)

        return ValidationResult(
            confidence=overall_confidence,
            issues=issues,
            auto_fixable_count=0,
            metrics=metrics
        )
