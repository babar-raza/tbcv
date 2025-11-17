# file: truth_manager.py
"""
scripts/tbcv/agents/truth_manager.py
------------------------------------

Agent: TruthManagerAgent

Purpose:
    Loads and manages plugin "truth" data (source of truth for validation,
    dependency resolution, and plugin relationships). It exposes async
    handlers for orchestrator workflows via the MCP-compatible interface.

Highlights:
    [OK] Absolute imports (no relative paths)
    [OK] Full BaseAgent compliance (implements get_contract + async handlers)
    [OK] Uses cache_result decorator for efficient repeat lookups
    [OK] Generic JSON structure handling with safe fallbacks
    [OK] Family-agnostic truth data loading
"""

import json
import hashlib
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass

# ---------- Project Imports (absolute) ----------
from agents.base import BaseAgent, AgentContract, AgentCapability
from core.logging import PerformanceLogger
from core.cache import cache_result
from core.rule_manager import rule_manager


# =======================================================
# Data Models
# =======================================================

@dataclass
class PluginInfo:
    """Metadata representation of a plugin entry."""
    id: str
    name: str
    slug: str
    description: str
    patterns: Dict[str, List[str]]
    family: str
    version: str
    dependencies: List[str]
    capabilities: List[str]
    plugin_type: str = "processor"
    load_formats: List[str] = None
    save_formats: List[str] = None

    def __post_init__(self):
        if self.load_formats is None:
            self.load_formats = []
        if self.save_formats is None:
            self.save_formats = []

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "patterns": self.patterns,
            "family": self.family,
            "version": self.version,
            "dependencies": self.dependencies,
            "capabilities": self.capabilities,
            "plugin_type": self.plugin_type,
            "load_formats": self.load_formats,
            "save_formats": self.save_formats
        }


@dataclass
class CombinationRule:
    """Represents combination or dependency rules between plugins."""
    name: str
    plugins: List[str]
    trigger_patterns: List[str]
    confidence_boost: float
    required_all: bool

    def to_dict(self):
        return {
            "name": self.name,
            "plugins": self.plugins,
            "trigger_patterns": self.trigger_patterns,
            "confidence_boost": self.confidence_boost,
            "required_all": self.required_all,
        }


@dataclass
class TruthDataIndex:
    """In-memory structure for all loaded truths for fast lookup."""
    # Primary plugin lookups
    by_id: Dict[str, PluginInfo]
    by_slug: Dict[str, PluginInfo]
    by_name: Dict[str, PluginInfo]
    # Alias lookup maps a normalized alias to one or more plugins
    by_alias: Dict[str, List[PluginInfo]]
    # Family grouping
    by_family: Dict[str, List[PluginInfo]]
    # Pattern lookup by group:type and pattern string (lower-case)
    by_pattern: Dict[str, List[PluginInfo]]
    # Combination rules loaded for this family
    combination_rules: List[CombinationRule]
    # Combination index mapping sorted plugin id tuple → list[CombinationRule]
    combination_index: Dict[tuple, List[CombinationRule]]
    # Dependencies lookup for each plugin id
    dependencies: Dict[str, List[str]]
    # Unique hash of loaded truth data for change detection
    version_hash: str
    last_updated: datetime


# =======================================================
# Generic Truth Data Adapter
# =======================================================

class TruthDataAdapter:
    """Adapter to normalize various truth data structures."""
    
    def __init__(self, family: str):
        self.family = family
        self.family_rules = rule_manager.get_family_rules(family)
        
    def adapt_plugin_data(self, truth_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert any truth JSON structure to normalized plugin data."""
        adapted = {"plugins": []}
        
        # Handle different possible structures
        plugins = truth_data.get("plugins", [])
        if not plugins:
            # Try alternative keys
            plugins = truth_data.get("components", [])
        if not plugins:
            plugins = truth_data.get("items", [])
            
        for plugin in plugins:
            adapted_plugin = self._adapt_single_plugin(plugin)
            if adapted_plugin:
                adapted["plugins"].append(adapted_plugin)
                
        return adapted
    
    def _adapt_single_plugin(self, plugin: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Adapt a single plugin to normalized structure."""
        try:
            # Extract name from various possible fields
            name = plugin.get("name") or plugin.get("title") or plugin.get("id", "")
            if not name:
                return None
                
            # Generate ID and slug
            plugin_id = self._generate_id(name)
            slug = self._generate_slug(name)
            
            # Extract or generate patterns
            patterns = self._extract_or_generate_patterns(plugin)
            
            # Extract capabilities and type
            plugin_type = plugin.get("type", "processor")
            capabilities = self._extract_capabilities(plugin)
            
            # Extract formats
            load_formats = plugin.get("load_formats", [])
            save_formats = plugin.get("save_formats", [])
            
            # Extract dependencies
            dependencies = self._extract_dependencies(plugin)
            
            adapted = {
                "id": plugin_id,
                "name": name,
                "slug": slug,
                "description": self._extract_description(plugin),
                "patterns": patterns,
                "family": self.family,
                "version": plugin.get("version", "1.0.0"),
                "dependencies": dependencies,
                "capabilities": capabilities,
                "plugin_type": plugin_type,
                "load_formats": load_formats,
                "save_formats": save_formats
            }
            
            return adapted
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to adapt plugin {plugin}: {e}")
            return None
    
    def _generate_id(self, name: str) -> str:
        """Generate consistent ID from name."""
        return name.lower().replace(" ", "_").replace("-", "_").replace(".", "_")
    
    def _generate_slug(self, name: str) -> str:
        """Generate URL-friendly slug from name."""
        return name.lower().replace(" ", "-").replace("_", "-")
    
    def _extract_or_generate_patterns(self, plugin: Dict[str, Any]) -> Dict[str, List[str]]:
        """Extract existing patterns or generate from plugin metadata."""
        # First try to use existing patterns
        existing_patterns = plugin.get("patterns", {})
        if existing_patterns:
            return existing_patterns
            
        # Generate patterns from plugin metadata
        name = plugin.get("name", "")
        plugin_type = plugin.get("type", "")
        load_formats = plugin.get("load_formats", [])
        save_formats = plugin.get("save_formats", [])
        
        patterns = {"format": [], "api": [], "method": []}
        
        # Format patterns from supported formats
        all_formats = list(set(load_formats + save_formats))
        for fmt in all_formats:
            if fmt:
                patterns["format"].extend([
                    f"\\b{fmt}\\b",
                    f"SaveFormat\\.{fmt}",
                    f"LoadFormat\\.{fmt}",
                    f"\\.{fmt.lower()}\\b"
                ])
        
        # API patterns from family rules and plugin name
        family_api_patterns = self.family_rules.api_patterns
        
        # Match plugin name to family patterns
        name_lower = name.lower()
        for pattern_group, pattern_list in family_api_patterns.items():
            if any(keyword in name_lower for keyword in ["document", "word", "pdf", "convert"]):
                if pattern_group in ["document_creation", "save_operations", "load_operations"]:
                    patterns["api"].extend(pattern_list)
        
        # Type-specific patterns
        if plugin_type == "processor":
            patterns["method"].extend(["Load", "Save", "new"])
        elif plugin_type == "feature":
            if "converter" in name_lower:
                patterns["method"].extend(["Convert", "Save"])
            elif "printer" in name_lower:
                patterns["method"].extend(["Print"])
            elif "merge" in name_lower:
                patterns["method"].extend(["Append", "Merge"])
                
        return patterns
    
    def _extract_description(self, plugin: Dict[str, Any]) -> str:
        """Extract description from various possible fields."""
        desc = plugin.get("description")
        if desc:
            return desc
            
        # Try to build from notes or other fields
        notes = plugin.get("notes", [])
        if notes:
            return " ".join(notes) if isinstance(notes, list) else str(notes)
            
        # Fallback to name-based description
        name = plugin.get("name", "")
        return f"{name} plugin for document processing"
    
    def _extract_capabilities(self, plugin: Dict[str, Any]) -> List[str]:
        """Extract capabilities from plugin metadata."""
        caps = plugin.get("capabilities", [])
        if caps:
            return caps
            
        # Infer from other fields
        caps = []
        if plugin.get("load_formats"):
            caps.append("load")
        if plugin.get("save_formats"):
            caps.append("save")
        if plugin.get("type") == "feature":
            caps.append("process")
            
        return caps or ["process"]
    
    def _extract_dependencies(self, plugin: Dict[str, Any]) -> List[str]:
        """Extract dependencies from plugin metadata."""
        # Direct dependencies
        deps = plugin.get("dependencies", [])
        if deps:
            return [self._generate_id(dep) for dep in deps]
            
        # Infer from requires field
        requires = plugin.get("requires", "")
        if requires and isinstance(requires, str):
            deps = []
            # Look for common dependency patterns
            if "processor" in requires.lower():
                # This is a feature plugin that needs a processor
                if "word" in requires.lower():
                    deps.append("word_processor")
                if "pdf" in requires.lower():
                    deps.append("pdf_processor")
            return deps
            
        return []


# =======================================================
# Main Agent
# =======================================================

class TruthManagerAgent(BaseAgent):
    """Agent responsible for loading, caching, and serving truth data."""

    def __init__(self, agent_id: Optional[str] = None):
        self.truth_index: Optional[TruthDataIndex] = None
        self.truth_directories: List[Path] = []
        self.validation_issues: List[str] = []
        self.supported_families = ["words"]  # Can be extended
        super().__init__(agent_id)

    # ---------------------------------------------------
    # Handler Registration
    # ---------------------------------------------------
    def _register_message_handlers(self):
        """Map MCP methods to async handler functions."""
        self.register_handler("ping", self.handle_ping)
        self.register_handler("get_status", self.handle_get_status)
        self.register_handler("get_contract", self.handle_get_contract)
        self.register_handler("load_truth_data", self.handle_load_truth_data)
        self.register_handler("get_plugin_info", self.handle_get_plugin_info)
        self.register_handler("search_plugins", self.handle_search_plugins)
        self.register_handler("get_combination_rules", self.handle_get_combination_rules)
        self.register_handler("validate_truth_data", self.handle_validate_truth_data)
        self.register_handler("get_truth_statistics", self.handle_get_truth_statistics)
        self.register_handler("reload_truth_data", self.handle_reload_truth_data)

        # Additional handler: check whether a set of plugins constitutes a valid combination
        self.register_handler("check_plugin_combination", self.handle_check_plugin_combination)

    # ---------------------------------------------------
    # Agent Contract (required by BaseAgent)
    # ---------------------------------------------------
    def get_contract(self):
        """Return static capability and resource metadata for orchestrator."""
        return AgentContract(
            agent_id=self.agent_id,
            name="TruthManagerAgent",
            version="1.0.0",
            capabilities=[
                AgentCapability(
                    name="load_truth_data",
                    description="Loads and indexes plugin truth data for any family.",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "family": {"type": "string", "default": "words"}
                        }
                    },
                    output_schema={"type": "object"},
                    side_effects=["read", "cache"],
                ),
                AgentCapability(
                    name="get_plugin_info",
                    description="Returns plugin metadata by ID or slug.",
                    input_schema={"type": "object"},
                    output_schema={"type": "object"},
                ),
                AgentCapability(
                    name="search_plugins",
                    description="Performs fuzzy search for plugins.",
                    input_schema={"type": "object"},
                    output_schema={"type": "object"},
                ),
            ],
            checkpoints=["truth_load_start", "truth_index_build", "truth_load_complete"],
            max_runtime_s=60,
            confidence_threshold=0.9,
            side_effects=["read", "cache"],
            dependencies=[],
            resource_limits={
                "max_memory_mb": 512,
                "max_cpu_percent": 80,
                "max_concurrent": 3,
            },
        )

    # ---------------------------------------------------
    # Configuration and Initialization
    # ---------------------------------------------------
    def _validate_configuration(self):
        """Validate and prepare truth directories."""
        cfg = self.settings.truth_manager
        for directory in cfg.truth_directories:
            p = Path(directory)
            self.truth_directories.append(p)
            if not p.exists():
                self.logger.warning("Truth directory missing", path=str(p))
        # auto-load once on startup
        self._load_truth_data()

    # ===================================================
    # Core Logic (Generic and family-agnostic)
    # ===================================================
    def _load_truth_data(self, family: str = "words") -> bool:
        """Internal synchronous loader for truth JSON files."""
        try:
            plugins = {}
            combination_rules = []

            # Load plugins for the specified family
            family_plugins = self._load_family_truth_data(family)
            plugins.update(family_plugins)

            # Load combination rules
            combination_rules.extend(self._load_combination_rules(family))

            self.truth_index = self._build_index(plugins, combination_rules)
            self.logger.info(
                "Truth data loaded successfully",
                family=family,
                plugins_count=len(plugins),
                combination_rules_count=len(combination_rules),
                version_hash=self.truth_index.version_hash,
            )
            return True
        except Exception as e:
            self.logger.error("Truth load failed", family=family, error=str(e))
            self.validation_issues.append(str(e))
            return False

    def _load_family_truth_data(self, family: str) -> Dict[str, PluginInfo]:
        """Load truth data for a specific family."""
        plugins = {}
        adapter = TruthDataAdapter(family)
        
        # Determine candidate truth files. Prefer the Aspose-specific truth definitions located
        # within the /truth directory, as those contain the canonical plugin IDs used by
        # combination rules. Fallback to generic family truth files if no Aspose file exists.
        truth_file_candidates: List[str] = []

        # 1) Configured path via main configuration
        try:
            configured_path = getattr(self.settings, 'truth_files', {}).get(family)
        except Exception:
            configured_path = None
        if configured_path:
            truth_file_candidates.append(configured_path)

        # 2) Aspose-specific truth file inside the truth directory
        truth_file_candidates.append(str(Path("truth") / f"aspose_{family}_plugins_truth.json"))

        # 3) Generic family truth file inside the truth directory
        truth_file_candidates.append(str(Path("truth") / f"{family}.json"))

        # 4) Root-level Aspose truth file (legacy)
        truth_file_candidates.append(f"aspose_{family}_plugins_truth.json")

        # 5) Generic family plugins truth at root
        truth_file_candidates.append(f"{family}_plugins_truth.json")

        truth_file: Optional[str] = None
        for candidate in truth_file_candidates:
            if candidate and Path(candidate).exists():
                truth_file = candidate
                break

        # Load plugin definitions from the first existing truth file
        if truth_file:
            try:
                with open(truth_file, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
                # Normalize the JSON structure
                adapted_data = adapter.adapt_plugin_data(raw_data)
                self._parse_plugins_data(adapted_data, family, plugins)
                self.logger.info(f"Loaded {len(plugins)} plugins from {truth_file}")
            except Exception as e:
                self.logger.error(f"Failed to load truth file {truth_file}: {e}")
        else:
            # No truth file found; continue with empty plugin set
            self.logger.warning(f"No truth file found for family '{family}', using empty plugin set")

        return plugins

    def _load_combination_rules(self, family: str) -> List[CombinationRule]:
        """Load combination rules for a family."""
        rules = []
        
        # Determine candidate combination files. Prefer Aspose-specific combinations within
        # the truth directory, which correspond to the detailed plugin definitions.
        combo_file_candidates: List[str] = []

        # 1) Configured combinations path via main configuration
        try:
            configured_path = getattr(self.settings, 'truth_files', {}).get("combinations")
        except Exception:
            configured_path = None
        if configured_path:
            combo_file_candidates.append(configured_path)

        # 2) Aspose-specific combinations file inside the truth directory
        combo_file_candidates.append(str(Path("truth") / f"aspose_{family}_plugins_combinations.json"))

        # 3) Generic combinations file inside the truth directory
        combo_file_candidates.append(str(Path("truth") / f"{family}_combinations.json"))

        # 4) Root-level Aspose combinations file
        combo_file_candidates.append(f"aspose_{family}_plugins_combinations.json")

        # 5) Generic family plugins combinations at root
        combo_file_candidates.append(f"{family}_plugins_combinations.json")

        combo_file: Optional[str] = None
        for candidate in combo_file_candidates:
            if candidate and Path(candidate).exists():
                combo_file = candidate
                break

        if combo_file:
            try:
                with open(combo_file, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)

                # Adapt combination data - support both "suites" and "combinations" keys
                suites = raw_data.get("suites", [])
                if not suites:
                    suites = raw_data.get("combinations", [])

                for suite in suites:
                    try:
                        # Accept both "includes" and "plugins" keys for plugin list
                        plugins_list = suite.get("includes", suite.get("plugins", []))
                        rule = CombinationRule(
                            name=suite.get("name", ""),
                            plugins=[self._normalize_plugin_id(name) for name in plugins_list],
                            trigger_patterns=suite.get("trigger_patterns", self._generate_trigger_patterns(suite)),
                            confidence_boost=suite.get("confidence_boost", 0.2),
                            required_all=suite.get("required_all", False)
                        )
                        rules.append(rule)
                    except Exception as e:
                        self.logger.warning(f"Failed to parse combination rule {suite}: {e}")

                self.logger.info(f"Loaded {len(rules)} combination rules from {combo_file}")
            except Exception as e:
                self.logger.error(f"Failed to load combinations file {combo_file}: {e}")

        return rules

    def _normalize_plugin_id(self, name: str) -> str:
        """Normalize plugin name to ID format."""
        return name.lower().replace(" ", "_").replace("-", "_")

    def _generate_trigger_patterns(self, suite: Dict[str, Any]) -> List[str]:
        """Generate trigger patterns from suite metadata."""
        patterns = []
        
        name = suite.get("name", "")
        if name:
            patterns.append(name.lower())
            
        # Add some format patterns
        formats = suite.get("allowed_save_formats", [])[:3]  # Limit to avoid too many
        for fmt in formats:
            if fmt:
                patterns.append(fmt.lower())
                
        return patterns

    def _parse_plugins_data(self, data: Dict[str, Any], family: str, plugins: Dict[str, PluginInfo]):
        """Parse adapted plugin data into PluginInfo objects."""
        for entry in data.get("plugins", []):
            try:
                plugin = PluginInfo(
                    id=entry.get("id", ""),
                    name=entry.get("name", entry.get("id", "")),
                    slug=entry.get("slug", entry.get("id", "").replace("_", "-")),
                    description=entry.get("description", ""),
                    patterns=entry.get("patterns", {}),
                    family=entry.get("family", family),
                    version=entry.get("version", "1.0.0"),
                    dependencies=entry.get("dependencies", []),
                    capabilities=entry.get("capabilities", []),
                    plugin_type=entry.get("plugin_type", "processor"),
                    load_formats=entry.get("load_formats", []),
                    save_formats=entry.get("save_formats", [])
                )
                
                if plugin.id:  # Only add plugins with valid IDs
                    plugins[plugin.id] = plugin
                    
            except Exception as e:
                self.logger.warning(f"Failed to parse plugin {entry}: {e}")

    def _build_index(self, plugins: Dict[str, PluginInfo], combination_rules: List[CombinationRule]) -> TruthDataIndex:
        # Build primary lookup maps
        by_id: Dict[str, PluginInfo] = plugins.copy()
        by_slug: Dict[str, PluginInfo] = {p.slug: p for p in plugins.values() if p.slug}
        by_name: Dict[str, PluginInfo] = {p.name.lower(): p for p in plugins.values() if p.name}

        by_family: Dict[str, List[PluginInfo]] = {}
        by_pattern: Dict[str, List[PluginInfo]] = {}
        by_alias: Dict[str, List[PluginInfo]] = {}
        dependencies: Dict[str, List[str]] = {}

        # Gather alias definitions from rule manager
        # Use default empty dict if no rules for family
        alias_overrides: Dict[str, List[str]] = {}
        try:
            # Build an alias override map per plugin id; there may be multiple families loaded but alias overrides apply by id
            for fam in set(p.family for p in plugins.values()):
                fr = rule_manager.get_family_rules(fam)
                if fr.plugin_aliases:
                    for pid, aliases in fr.plugin_aliases.items():
                        alias_overrides.setdefault(pid, []).extend(aliases)
        except Exception:
            pass

        for p in plugins.values():
            # family grouping
            by_family.setdefault(p.family, []).append(p)

            # pattern indexing by group and pattern string
            for group, patterns in p.patterns.items():
                for pat in patterns:
                    if pat:
                        key = f"{group}:{pat.lower()}"
                        by_pattern.setdefault(key, []).append(p)

            # alias indexing: include id, slug, name, and rule manager aliases
            aliases: List[str] = [p.id, p.slug, p.name]
            # Additional alias sources: plugin type, version names etc. Not used for now
            overrides = alias_overrides.get(p.id, [])
            if overrides:
                aliases.extend(overrides)
            for alias in aliases:
                if not alias:
                    continue
                alias_norm = alias.lower().replace(" ", "").replace("-", "").replace("_", "")
                by_alias.setdefault(alias_norm, []).append(p)

            # dependencies map
            dependencies[p.id] = p.dependencies or []

        # Build combination index: map sorted tuple of plugin ids → list of rules
        combination_index: Dict[tuple, List[CombinationRule]] = {}
        for rule in combination_rules:
            try:
                # Use sorted tuple of plugin ids as key
                key = tuple(sorted(rule.plugins))
                combination_index.setdefault(key, []).append(rule)
            except Exception:
                continue

        # Generate version hash from plugins and combination rules for change detection
        try:
            plugins_serialized = {k: v.to_dict() for k, v in plugins.items()}
            combos_serialized = [r.to_dict() for r in combination_rules]
            version_blob = {
                "plugins": plugins_serialized,
                "combinations": combos_serialized,
            }
            version_hash = hashlib.sha256(
                json.dumps(version_blob, sort_keys=True).encode()
            ).hexdigest()[:16]
        except Exception:
            version_hash = "unknown"

        return TruthDataIndex(
            by_id=by_id,
            by_slug=by_slug,
            by_name=by_name,
            by_alias=by_alias,
            by_family=by_family,
            by_pattern=by_pattern,
            combination_rules=combination_rules,
            combination_index=combination_index,
            dependencies=dependencies,
            version_hash=version_hash,
            last_updated=datetime.now(timezone.utc),
        )

    # ===================================================
    # Public async handlers (MCP API)
    # ===================================================

    @cache_result(ttl_seconds=3600)
    async def handle_load_truth_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Reload truth data on demand (used by orchestrator)."""
        family = params.get("family", "words")
        success = self._load_truth_data(family)
        return {
            "success": success,
            "family": family,
            "plugins_count": len(self.truth_index.by_id) if self.truth_index else 0,
            "combination_rules_count": len(self.truth_index.combination_rules) if self.truth_index else 0,
            "version_hash": getattr(self.truth_index, "version_hash", None),
        }

    async def handle_get_plugin_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch plugin info by id or slug."""
        pid = params.get("plugin_id")
        slug = params.get("slug")
        name = params.get("name")
        query = None
        plugin = None
        # If truth index is not loaded, return not found
        if not self.truth_index:
            return {"found": False, "plugin": None}

        # Normalize queries
        if pid:
            query = pid
        elif slug:
            query = slug
        elif name:
            query = name

        if query:
            # Direct lookups by id, slug, or name
            if query in self.truth_index.by_id:
                plugin = self.truth_index.by_id.get(query)
            elif query in self.truth_index.by_slug:
                plugin = self.truth_index.by_slug.get(query)
            elif query.lower() in self.truth_index.by_name:
                plugin = self.truth_index.by_name.get(query.lower())
            else:
                # Fallback to alias lookup: normalize query by removing separators
                alias_norm = query.lower().replace(" ", "").replace("-", "").replace("_", "")
                matches = self.truth_index.by_alias.get(alias_norm, [])
                # If multiple matches, select the one with exact id match or first
                if matches:
                    plugin = matches[0]

        return {"found": plugin is not None, "plugin": plugin.to_dict() if plugin else None}

    async def handle_search_plugins(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search plugins with family-aware aliases. If query is empty, returns all plugins for the family."""
        # Normalise query and family
        query_raw = params.get("query", "") or ""
        family = params.get("family", "words")
        # Early exit if truth index is not loaded
        if not self.truth_index:
            return {"results": [], "matches_count": 0}
        # If no query, return all plugins for the family
        if not query_raw:
            family_plugins = self.truth_index.by_family.get(family, [])
            # Sort results by plugin name for stable ordering
            results = [p.to_dict() for p in sorted(family_plugins, key=lambda x: x.name.lower())]
            return {"results": results, "matches_count": len(results)}

        query_lower = query_raw.lower()
        # Normalised query for alias matching (remove separators)
        query_norm = query_lower.replace(" ", "").replace("-", "").replace("_", "")

        matched_plugins: Dict[str, PluginInfo] = {}

        # Search by id, name and slug
        for plugin in self.truth_index.by_id.values():
            if plugin.family != family:
                continue
            if query_lower in plugin.id.lower() or query_lower in plugin.name.lower() or query_lower in plugin.slug.lower():
                matched_plugins[plugin.id] = plugin

        # Search by alias map
        for alias_key, plugin_list in self.truth_index.by_alias.items():
            if query_norm in alias_key:
                for plugin in plugin_list:
                    if plugin.family == family:
                        matched_plugins[plugin.id] = plugin

        # Convert to list of dicts with stable ordering
        results = [p.to_dict() for p in sorted(matched_plugins.values(), key=lambda x: x.name.lower())]
        return {"results": results, "matches_count": len(results)}

    async def handle_get_combination_rules(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Return all loaded combination rules."""
        if not self.truth_index:
            return {"rules": []}
        return {"rules": [r.to_dict() for r in self.truth_index.combination_rules]}

    async def handle_validate_truth_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Simple structural validation of truth index."""
        issues = []
        if not self.truth_index:
            issues.append("Truth data not loaded")
        else:
            for plugin in self.truth_index.by_id.values():
                if not plugin.patterns:
                    issues.append(f"Plugin {plugin.id} missing patterns")
        return {"issues": issues, "valid": len(issues) == 0}

    async def handle_get_truth_statistics(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Provide statistics and metadata."""
        if not self.truth_index:
            return {"loaded": False}
        return {
            "loaded": True,
            "plugins_count": len(self.truth_index.by_id),
            "families_count": len(self.truth_index.by_family),
            "rules_count": len(self.truth_index.combination_rules),
            "version_hash": self.truth_index.version_hash,
            "supported_families": self.supported_families
        }

    async def handle_reload_truth_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Forces a reload bypassing cache."""
        family = params.get("family", "words")
        self.clear_cache()
        success = self._load_truth_data(family)
        return {"success": success, "reloaded": True, "family": family}

    async def handle_check_plugin_combination(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check whether a given set of plugin IDs constitutes a defined combination rule.

        Parameters:
            plugins: List[str] - list of plugin IDs or aliases
            family: str - optional family to constrain search

        Returns:
            {
                "valid": bool,
                "rules": List[str],  # names of matched combination rules
                "unknown_plugins": List[str]  # any plugin IDs that were not found in the truth index
            }
        """
        if not self.truth_index:
            return {"valid": False, "rules": [], "unknown_plugins": []}

        plugin_ids_raw = params.get("plugins", []) or []
        if not isinstance(plugin_ids_raw, list):
            plugin_ids_raw = [plugin_ids_raw]
        family = params.get("family", None)

        # Resolve plugin IDs and detect unknown aliases
        resolved_ids: List[str] = []
        unknown_plugins: List[str] = []
        for item in plugin_ids_raw:
            if not item:
                continue
            # Normalize plugin id/name/alias
            key = str(item)
            found_plugin: Optional[PluginInfo] = None
            # Check by id, slug, name
            if key in self.truth_index.by_id:
                found_plugin = self.truth_index.by_id[key]
            elif key in self.truth_index.by_slug:
                found_plugin = self.truth_index.by_slug[key]
            elif key.lower() in self.truth_index.by_name:
                found_plugin = self.truth_index.by_name[key.lower()]
            else:
                # Alias lookup
                alias_norm = key.lower().replace(" ", "").replace("-", "").replace("_", "")
                matches = self.truth_index.by_alias.get(alias_norm)
                if matches:
                    found_plugin = matches[0]
            if found_plugin:
                # Optionally enforce family constraint
                if not family or found_plugin.family == family:
                    resolved_ids.append(found_plugin.id)
                else:
                    # Wrong family counts as unknown for this context
                    unknown_plugins.append(key)
            else:
                unknown_plugins.append(key)

        # If any unknown plugins, return invalid
        if unknown_plugins:
            return {"valid": False, "rules": [], "unknown_plugins": unknown_plugins}

        # Sort plugin IDs for combination index lookup
        sorted_ids = tuple(sorted(resolved_ids))
        rules = []
        if sorted_ids in self.truth_index.combination_index:
            rules = [r.name for r in self.truth_index.combination_index[sorted_ids]]
        return {"valid": bool(rules), "rules": rules, "unknown_plugins": []}

# =======================================================
# Local Smoke Test
# =======================================================
if __name__ == "__main__":
    import asyncio

    async def _demo():
        agent = TruthManagerAgent()
        result = await agent.handle_load_truth_data({"family": "words"})
        print("[OK] Truth data load result:", result)

    asyncio.run(_demo())
