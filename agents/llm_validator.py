# file: tbcv/agents/llm_validator.py
"""
LLMValidatorAgent - Semantic validation using LLM to verify plugin requirements.
Uses Ollama to understand content and detect missing/incorrect plugin mentions.
Uses ConfigLoader for configuration-driven validation.
"""

import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from pathlib import Path

from agents.base import BaseAgent, AgentContract, AgentCapability, agent_registry
from core.config_loader import ConfigLoader, get_config_loader
from core.logging import PerformanceLogger, get_logger
from core.ollama import ollama

logger = get_logger(__name__)


@dataclass
class PluginRequirement:
    """A plugin requirement detected by LLM."""
    plugin_id: str
    plugin_name: str
    confidence: float
    detection_type: str  # "llm_verified", "llm_missing", "llm_suggested"
    reasoning: str
    validation_status: str  # "mentioned_correctly", "missing_required", "mentioned_incorrectly"
    recommendation: Optional[Dict[str, Any]] = None
    matched_context: Optional[str] = None


class LLMValidatorAgent(BaseAgent):
    """Agent that uses LLM to validate plugin requirements semantically."""

    def __init__(self, agent_id: Optional[str] = None, config_loader: Optional[ConfigLoader] = None):
        # Initialize config BEFORE calling super().__init__() since _validate_configuration needs it
        self._config_loader = config_loader or get_config_loader()
        self._config = self._config_loader.load("llm")
        super().__init__(agent_id)

    def _register_message_handlers(self):
        """Expose MCP methods."""
        self.register_handler("ping", self.handle_ping)
        self.register_handler("get_status", self.handle_get_status)
        self.register_handler("get_contract", self.get_contract)
        self.register_handler("validate_plugins", self.handle_validate_plugins)

    def _validate_configuration(self):
        """Validate LLM is available."""
        availability = self._config.get("availability", {})
        if not ollama.is_available():
            if availability.get("log_unavailability", True):
                self.logger.warning("Ollama is not available for LLM validation")

    def _get_model_settings(self, family: Optional[str] = None) -> Dict[str, Any]:
        """Get model settings, with optional family override."""
        base_settings = self._config.get("model", {})
        defaults = {
            "name": "qwen2.5",
            "temperature": 0.1,
            "top_p": 0.9,
            "num_predict": 2000,
            "timeout": 60
        }

        # Merge defaults with config
        settings = {**defaults, **base_settings}

        # Apply family override if available
        if family:
            family_override = self._config_loader.get_family_override("llm", family)
            if family_override and "model" in family_override:
                settings.update(family_override["model"])

        return settings

    def _get_retry_settings(self) -> Dict[str, Any]:
        """Get retry policy settings."""
        defaults = {
            "max_attempts": 3,
            "initial_delay_ms": 1000,
            "max_delay_ms": 10000,
            "backoff_multiplier": 2.0,
            "retry_on_errors": ["Connection", "timeout", "ECONNREFUSED"]
        }
        return {**defaults, **self._config.get("retry", {})}

    def get_contract(self) -> AgentContract:
        """Advertise public methods."""
        model_settings = self._get_model_settings()
        return AgentContract(
            agent_id=self.agent_id,
            name="LLMValidatorAgent",
            version="1.0.0",
            capabilities=[
                AgentCapability(
                    name="validate_plugins",
                    description="Validate plugin requirements using LLM semantic analysis",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "content": {"type": "string"},
                            "fuzzy_detections": {"type": "array"},
                            "family": {"type": "string", "default": "words"},
                            "profile": {"type": "string", "default": "default"}
                        },
                        "required": ["content", "fuzzy_detections"]
                    },
                    output_schema={"type": "object"},
                    side_effects=["read", "network"]
                )
            ],
            max_runtime_s=model_settings.get("timeout", 60),
            confidence_threshold=0.7,
            side_effects=["read", "network"],
            dependencies=["truth_manager"],
            checkpoints=[]
        )

    async def handle_validate_plugins(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate plugin requirements using LLM."""
        content = params.get("content", "")
        fuzzy_detections = params.get("fuzzy_detections", [])
        family = params.get("family", "words")
        profile = params.get("profile", self._config.profile)

        # Get active rules
        active_rules = self._config_loader.get_rules("llm", profile=profile, family=family)
        active_rule_ids = {r.id for r in active_rules}
        rule_levels = {r.id: r.level for r in active_rules}
        rule_params = {r.id: r.params for r in active_rules}

        # Check if validation is enabled
        if not active_rule_ids:
            return {
                "requirements": [],
                "issues": [{
                    "level": "info",
                    "category": "llm_disabled",
                    "message": "LLM validation disabled for this profile"
                }],
                "confidence": 0.0,
                "profile": profile
            }

        # Check Ollama availability
        if not ollama.enabled:
            return {
                "requirements": [],
                "issues": [{
                    "level": "info",
                    "category": "llm_disabled",
                    "message": "LLM validation disabled (set OLLAMA_ENABLED=true to enable)"
                }],
                "confidence": 0.0,
                "profile": profile
            }

        try:
            # Try to connect to Ollama
            ollama.list_models()
        except Exception as e:
            error_msg = str(e)
            availability = self._config.get("availability", {})

            if "Connection" in error_msg or "connect" in error_msg.lower():
                message = f"Cannot connect to Ollama at {ollama.base_url}. Ensure 'ollama serve' is running."
            elif "timeout" in error_msg.lower():
                message = f"Ollama connection timeout at {ollama.base_url}. Check if server is responsive."
            else:
                message = f"Ollama error: {error_msg}"

            if availability.get("fallback_when_unavailable", True):
                return {
                    "requirements": [],
                    "issues": [{
                        "level": "warning",
                        "category": "llm_unavailable",
                        "message": message,
                        "diagnostic": {
                            "ollama_url": ollama.base_url,
                            "ollama_model": ollama.model,
                            "ollama_enabled": ollama.enabled,
                            "error": error_msg
                        }
                    }],
                    "confidence": 0.0,
                    "profile": profile
                }

        # Load truth data for plugin definitions
        truth_data = self._load_truth_data(family)
        core_rules = truth_data.get("core_rules", [])
        plugins = truth_data.get("plugins", [])

        # Get prompt parameters
        validate_params = rule_params.get("validate_plugins", {})
        content_excerpt_length = validate_params.get("content_excerpt_length", 2000)
        max_plugins = validate_params.get("max_plugins_in_prompt", 15)
        max_rules = validate_params.get("max_rules_in_prompt", 10)

        # Build LLM prompt
        prompt = self._build_validation_prompt(
            content, fuzzy_detections, core_rules, plugins,
            content_excerpt_length, max_plugins, max_rules
        )

        try:
            # Get model settings
            model_settings = self._get_model_settings(family)

            # Call LLM
            response = await ollama.async_generate(
                prompt=prompt,
                options={
                    "temperature": model_settings.get("temperature", 0.1),
                    "top_p": model_settings.get("top_p", 0.9),
                    "num_predict": model_settings.get("num_predict", 2000)
                }
            )

            # Parse LLM response
            result = self._parse_llm_response(
                response.get('response', ''),
                plugins,
                active_rule_ids,
                rule_levels,
                rule_params
            )
            result["profile"] = profile

            return result

        except Exception as e:
            self.logger.warning(f"LLM validation failed: {e}")
            return {
                "requirements": [],
                "issues": [{
                    "level": "error",
                    "category": "llm_error",
                    "message": f"LLM validation error: {str(e)}"
                }],
                "confidence": 0.0,
                "profile": profile
            }

    def _load_truth_data(self, family: str) -> Dict[str, Any]:
        """Load truth data for plugin definitions."""
        try:
            truth_path = Path(f"truth/{family}.json")
            if truth_path.exists():
                with open(truth_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Failed to load truth data: {e}")
        return {"core_rules": [], "plugins": []}

    def _build_validation_prompt(
        self,
        content: str,
        fuzzy_detections: List[Dict],
        core_rules: List[str],
        plugins: List[Dict],
        content_excerpt_length: int = 2000,
        max_plugins: int = 15,
        max_rules: int = 10
    ) -> str:
        """Build prompt for LLM validation."""

        # Extract content excerpt
        content_excerpt = content[:content_excerpt_length] if len(content) > content_excerpt_length else content

        # Format fuzzy detections
        fuzzy_list = "\n".join([
            f"- {d.get('plugin_name', 'Unknown')} (ID: {d.get('plugin_id', 'unknown')})"
            for d in fuzzy_detections
        ])

        # Format core rules
        rules_list = "\n".join([f"- {rule}" for rule in core_rules[:max_rules]])

        # Format plugin definitions (only processors and converters)
        plugin_list = []
        for p in plugins:
            if p.get("type") in ["processor", "feature"]:
                plugin_list.append(
                    f"- {p['name']} ({p['type']}): "
                    f"Load={p.get('load_formats', [])}, Save={p.get('save_formats', [])}"
                )
        plugins_text = "\n".join(plugin_list[:max_plugins])

        prompt = f"""You are a technical documentation validator for Aspose.Words plugin system.

CONTENT TO VALIDATE:
{content_excerpt}

FUZZY PATTERN DETECTIONS:
{fuzzy_list if fuzzy_list else "None detected"}

CORE PLUGIN RULES:
{rules_list}

AVAILABLE PLUGINS:
{plugins_text}

TASK:
Analyze the content and determine:
1. Which plugins are REQUIRED based on the operations described
2. Whether the fuzzy detections are correct (verify against actual plugin names)
3. Any MISSING required plugins that should be mentioned
4. Specific recommendations for improving plugin documentation

IMPORTANT RULES:
- Cross-format conversion (e.g., DOCX→PDF) requires: source processor + target processor + Document Converter
- Feature plugins (Watermark, Comparer, Merger, etc.) cannot work alone - they need at least one processor
- Creating from scratch → PDF only needs PDF Processor
- Focus ONLY on plugins explicitly needed for the operations in the content

Respond ONLY with valid JSON in this exact format:
{{
  "required_plugins": [
    {{
      "plugin_id": "word_processor",
      "plugin_name": "Word Processor",
      "confidence": 0.95,
      "reasoning": "Content shows loading DOCX files",
      "validation_status": "mentioned_correctly",
      "matched_context": "The article explains loading .docx files"
    }}
  ],
  "missing_plugins": [
    {{
      "plugin_id": "document_converter",
      "plugin_name": "Document Converter",
      "confidence": 0.9,
      "reasoning": "DOCX to PDF conversion requires Document Converter",
      "validation_status": "missing_required",
      "recommendation": {{
        "type": "add_plugin_mention",
        "severity": "high",
        "message": "Document Converter plugin is required but not mentioned",
        "suggested_addition": "This conversion requires Document Converter plugin",
        "location": "prerequisites_section"
      }}
    }}
  ],
  "incorrect_detections": [
    {{
      "detected_plugin_id": "words_save_operations",
      "issue": "This is not a real plugin ID",
      "correct_plugin_id": "word_processor",
      "correct_plugin_name": "Word Processor"
    }}
  ]
}}"""

        return prompt

    def _parse_llm_response(
        self,
        response: str,
        plugins: List[Dict],
        active_rule_ids: set = None,
        rule_levels: Dict[str, str] = None,
        rule_params: Dict[str, Dict] = None
    ) -> Dict[str, Any]:
        """Parse LLM response and structure results."""
        # Defaults for backward compatibility
        if active_rule_ids is None:
            active_rule_ids = {"validate_plugins", "detect_missing_plugins", "detect_incorrect_plugins"}
        if rule_levels is None:
            rule_levels = {}
        if rule_params is None:
            rule_params = {}

        parsing_config = self._config.get("parsing", {})

        try:
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)

                requirements = []
                issues = []

                # Process required plugins
                for req in data.get('required_plugins', []):
                    requirements.append({
                        "plugin_id": req.get("plugin_id"),
                        "plugin_name": req.get("plugin_name"),
                        "confidence": req.get("confidence", 0.9),
                        "detection_type": "llm_verified",
                        "reasoning": req.get("reasoning", ""),
                        "validation_status": req.get("validation_status", "mentioned_correctly"),
                        "matched_context": req.get("matched_context"),
                        "recommendation": None
                    })

                # Process missing plugins (these become issues)
                if "detect_missing_plugins" in active_rule_ids:
                    missing_params = rule_params.get("detect_missing_plugins", {})
                    confidence_threshold = missing_params.get("confidence_threshold", 0.7)
                    level = rule_levels.get("detect_missing_plugins", "warning")

                    for missing in data.get('missing_plugins', []):
                        if missing.get("confidence", 0) >= confidence_threshold:
                            requirements.append({
                                "plugin_id": missing.get("plugin_id"),
                                "plugin_name": missing.get("plugin_name"),
                                "confidence": missing.get("confidence", 0.85),
                                "detection_type": "llm_missing",
                                "reasoning": missing.get("reasoning", ""),
                                "validation_status": "missing_required",
                                "matched_context": None,
                                "recommendation": missing.get("recommendation")
                            })

                            # Add to issues list
                            rec = missing.get("recommendation", {})
                            issues.append({
                                "level": level,
                                "category": "missing_plugin",
                                "message": rec.get("message", f"{missing.get('plugin_name')} is required but not mentioned"),
                                "plugin_id": missing.get("plugin_id"),
                                "auto_fixable": True,
                                "fix_suggestion": rec.get("suggested_addition", "")
                            })
                else:
                    # Legacy behavior - process all missing plugins
                    for missing in data.get('missing_plugins', []):
                        requirements.append({
                            "plugin_id": missing.get("plugin_id"),
                            "plugin_name": missing.get("plugin_name"),
                            "confidence": missing.get("confidence", 0.85),
                            "detection_type": "llm_missing",
                            "reasoning": missing.get("reasoning", ""),
                            "validation_status": "missing_required",
                            "matched_context": None,
                            "recommendation": missing.get("recommendation")
                        })

                        rec = missing.get("recommendation", {})
                        issues.append({
                            "level": rec.get("severity", "warning"),
                            "category": "missing_plugin",
                            "message": rec.get("message", f"{missing.get('plugin_name')} is required but not mentioned"),
                            "plugin_id": missing.get("plugin_id"),
                            "auto_fixable": True,
                            "fix_suggestion": rec.get("suggested_addition", "")
                        })

                # Process incorrect detections
                if "detect_incorrect_plugins" in active_rule_ids:
                    level = rule_levels.get("detect_incorrect_plugins", "warning")

                    for incorrect in data.get('incorrect_detections', []):
                        issues.append({
                            "level": level,
                            "category": "incorrect_plugin",
                            "message": f"Detected '{incorrect.get('detected_plugin_id')}' is not a real plugin",
                            "fix_suggestion": f"Should be '{incorrect.get('correct_plugin_name')}'",
                            "auto_fixable": False
                        })
                else:
                    # Legacy behavior
                    for incorrect in data.get('incorrect_detections', []):
                        issues.append({
                            "level": "warning",
                            "category": "incorrect_plugin",
                            "message": f"Detected '{incorrect.get('detected_plugin_id')}' is not a real plugin",
                            "fix_suggestion": f"Should be '{incorrect.get('correct_plugin_name')}'",
                            "auto_fixable": False
                        })

                # Calculate overall confidence
                if requirements:
                    avg_confidence = sum(r["confidence"] for r in requirements) / len(requirements)
                else:
                    avg_confidence = 0.5

                return {
                    "requirements": requirements,
                    "issues": issues,
                    "confidence": avg_confidence
                }

        except Exception as e:
            if parsing_config.get("log_raw_responses", False):
                self.logger.debug(f"Raw LLM response: {response}")
            self.logger.debug(f"Failed to parse LLM response: {e}")

        # Fallback response
        if parsing_config.get("fallback_on_parse_error", True):
            return {
                "requirements": [],
                "issues": [{
                    "level": "warning",
                    "category": "parse_error",
                    "message": "Could not parse LLM response"
                }],
                "confidence": 0.0
            }

        raise ValueError("Failed to parse LLM response")
