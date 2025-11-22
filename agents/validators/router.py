# file: agents/validators/router.py
"""
ValidatorRouter - Routes validation requests to appropriate validator agents.
Provides fallback to legacy ContentValidator when new validators are unavailable.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional
from core.logging import get_logger

logger = get_logger(__name__)


class ValidatorRouter:
    """Routes validation requests to appropriate validators with fallback support."""

    def __init__(self, agent_registry, feature_flags=None):
        """
        Initialize the validator router.

        Args:
            agent_registry: The agent registry to look up validators
            feature_flags: Optional feature flags for gradual rollout (not used if None)
        """
        self.agent_registry = agent_registry
        self.feature_flags = feature_flags
        self.validator_map = self._build_validator_map()

    def _build_validator_map(self) -> Dict[str, str]:
        """Map validation types to agent IDs."""
        return {
            # Standard validators
            "yaml": "yaml_validator",
            "markdown": "markdown_validator",
            "code": "code_validator",
            "links": "link_validator",
            "structure": "structure_validator",
            "Truth": "truth_validator",
            "FuzzyLogic": "fuzzy_detector",

            # SEO validator handles both seo and heading_sizes
            "seo": "seo_validator",
            "heading_sizes": "seo_validator",

            # LLM validator
            "llm": "llm_validator"
        }

    async def execute(
        self,
        validation_types: List[str],
        content: str,
        context: Dict[str, Any],
        ui_override: bool = False
    ) -> Dict[str, Any]:
        """
        Execute validations using new validator agents with fallback to legacy.

        Args:
            validation_types: List of validation types to run
            content: Content to validate
            context: Validation context (file_path, family, etc.)
            ui_override: If True, use UI-selected validators regardless of config

        Returns:
            Dict with validation results and routing info
        """
        results = {
            "validation_results": {},
            "routing_info": {}
        }

        for val_type in validation_types:
            try:
                # Get agent ID for this validation type
                agent_id = self.validator_map.get(val_type)

                if not agent_id:
                    logger.warning(f"No validator mapping for type: {val_type}")
                    results["routing_info"][val_type] = "unknown_type"
                    continue

                # Check if new validator is available
                agent = self.agent_registry.get_agent(agent_id)

                if agent:
                    # Use new validator agent
                    logger.debug(f"Using new validator agent for {val_type}: {agent_id}")

                    # Update context with validation type (needed for SEO dual validation)
                    validation_context = {**context, "validation_type": val_type}

                    # Call validator
                    validation_result = await agent.validate(content, validation_context)

                    results["validation_results"][f"{val_type}_validation"] = {
                        "confidence": validation_result.confidence,
                        "issues": [issue.to_dict() for issue in validation_result.issues],
                        "metrics": validation_result.metrics,
                        "used_legacy": False
                    }
                    results["routing_info"][val_type] = "new_validator"
                else:
                    # Fallback to legacy ContentValidator
                    logger.info(f"New validator not available for {val_type}, using legacy")
                    legacy_result = await self._use_legacy_validator(val_type, content, context)
                    results["validation_results"][f"{val_type}_validation"] = legacy_result
                    results["routing_info"][val_type] = "legacy_fallback"

            except Exception as e:
                logger.error(f"Error validating {val_type}: {e}", exc_info=True)
                results["validation_results"][f"{val_type}_validation"] = {
                    "error": str(e),
                    "used_legacy": False
                }
                results["routing_info"][val_type] = "error"

        return results

    async def _use_legacy_validator(
        self,
        validation_type: str,
        content: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Fallback to legacy ContentValidator for this validation type.

        Args:
            validation_type: The validation type
            content: Content to validate
            context: Validation context

        Returns:
            Validation result from legacy validator
        """
        # Get legacy content validator
        content_validator = self.agent_registry.get_agent("content_validator")

        if not content_validator:
            logger.error("Legacy ContentValidator not available!")
            return {
                "confidence": 0.0,
                "issues": [{
                    "level": "error",
                    "category": "validator_unavailable",
                    "message": f"No validator available for {validation_type}",
                    "suggestion": "Check agent registry and validator configuration"
                }],
                "used_legacy": True
            }

        try:
            # Call legacy validator with specific validation type
            result = await content_validator.handle_validate_content({
                "content": content,
                "file_path": context.get("file_path", ""),
                "family": context.get("family", ""),
                "validation_types": [validation_type]
            })

            # Extract relevant validation from result
            validation_key = f"{validation_type}_validation"
            legacy_result = result.get(validation_key, {})
            legacy_result["used_legacy"] = True

            return legacy_result

        except Exception as e:
            logger.error(f"Error in legacy validator for {validation_type}: {e}", exc_info=True)
            return {
                "confidence": 0.0,
                "issues": [{
                    "level": "error",
                    "category": "legacy_validator_error",
                    "message": f"Error in legacy validator: {str(e)}",
                    "suggestion": "Check logs for details"
                }],
                "used_legacy": True
            }

    def get_available_validators(self) -> List[Dict[str, Any]]:
        """
        Get list of all available validators (both new and legacy).

        Returns:
            List of validator info dicts
        """
        validators = []

        # Define all known validators
        validator_definitions = [
            {"id": "yaml", "label": "YAML", "description": "Validate YAML frontmatter", "category": "standard"},
            {"id": "markdown", "label": "Markdown", "description": "Validate Markdown syntax", "category": "standard"},
            {"id": "code", "label": "Code", "description": "Validate code blocks", "category": "standard"},
            {"id": "links", "label": "Links", "description": "Check link validity", "category": "standard"},
            {"id": "structure", "label": "Structure", "description": "Validate document structure", "category": "standard"},
            {"id": "Truth", "label": "Truth", "description": "Validate against truth data", "category": "standard"},
            {"id": "FuzzyLogic", "label": "Fuzzy Logic", "description": "Fuzzy plugin detection", "category": "standard"},
            {"id": "seo", "label": "SEO Headings", "description": "Validate SEO-friendly heading structure", "category": "advanced"},
            {"id": "heading_sizes", "label": "Heading Sizes", "description": "Validate heading length limits", "category": "advanced"},
            {"id": "llm", "label": "LLM Analysis", "description": "Semantic validation via LLM", "category": "advanced"}
        ]

        for validator_def in validator_definitions:
            val_id = validator_def["id"]
            agent_id = self.validator_map.get(val_id)

            # Check if new validator is available
            available = False
            if agent_id:
                agent = self.agent_registry.get_agent(agent_id)
                available = agent is not None

            validators.append({
                **validator_def,
                "available": available,
                "enabled_by_default": available and validator_def["category"] == "standard"
            })

        return validators
