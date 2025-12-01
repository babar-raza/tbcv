# file: tbcv/agents/recommendation_agent.py
"""
RecommendationAgent: Generates concrete, actionable recommendations from validation failures.

Input: Single validation + full content/context
Output: One or more concrete recommendations with rationale and confidence

Implements the Reflection pattern via RecommendationCriticAgent for quality improvement.
"""

from __future__ import annotations

import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from agents.base import BaseAgent, AgentCapability, AgentContract
from core.logging import get_logger
from core.database import db_manager
from core.config_loader import get_config_loader

logger = get_logger(__name__)


class RecommendationAgent(BaseAgent):
    """
    Agent that generates concrete, actionable recommendations from validation failures.
    
    Recommendations should:
    - Be specific and actionable (not generic advice)
    - Include clear rationale for why the recommendation would help
    - Have confidence scores based on evidence
    - Be scoped to the exact part of content that needs fixing
    """
    
    def __init__(self, agent_id: str = "recommendation_agent"):
        self._critic = None
        self._reflection_config = None
        super().__init__(agent_id)
        self._load_reflection_config()
        self.capabilities = [
            AgentCapability(
                name="generate_recommendations",
                description="Generate actionable recommendations from validation failures",
                input_schema={
                    "type": "object",
                    "properties": {
                        "validation": {"type": "object"},
                        "content": {"type": "string"},
                        "context": {"type": "object"}
                    },
                    "required": ["validation", "content"]
                },
                output_schema={
                    "type": "array",
                    "items": {"type": "object"}
                },
                side_effects=["database_write"]
            ),
        ]
    
    def get_contract(self) -> AgentContract:
        """Return agent contract for registration."""
        return AgentContract(
            agent_id=self.agent_id,
            name="RecommendationAgent",
            version="1.0.0",
            capabilities=self.capabilities,
            checkpoints=[],
            max_runtime_s=30,
            confidence_threshold=0.7,
            side_effects=["database_write"],
            dependencies=[],
        )
    
    def _load_reflection_config(self):
        """Load reflection configuration."""
        try:
            config_loader = get_config_loader()
            config = config_loader.load("reflection")
            self._reflection_config = config.get("reflection", {}) if config else {}
        except Exception as e:
            logger.warning(f"Failed to load reflection config: {e}")
            self._reflection_config = {}

    def _get_critic(self):
        """Lazy-load the recommendation critic agent."""
        if self._critic is None and self._reflection_enabled():
            try:
                from agents.recommendation_critic import RecommendationCriticAgent
                self._critic = RecommendationCriticAgent()
                logger.debug("Initialized RecommendationCriticAgent for reflection")
            except Exception as e:
                logger.warning(f"Failed to initialize critic: {e}")
        return self._critic

    def _reflection_enabled(self) -> bool:
        """Check if reflection pattern is enabled."""
        return self._reflection_config.get("enabled", False)

    def _register_message_handlers(self):
        """Register MCP message handlers."""
        self.register_handler("generate_recommendations", self.handle_generate_recommendations)
        self.register_handler("generate_recommendations_with_reflection", self.handle_generate_with_reflection)
    
    async def handle_generate_recommendations(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP request to generate recommendations."""
        validation = params.get("validation", {})
        content = params.get("content", "")
        context = params.get("context", {})
        use_reflection = params.get("use_reflection", self._reflection_enabled())

        recommendations = await self.generate_recommendations(
            validation=validation,
            content=content,
            context=context
        )

        # Apply reflection pattern if enabled
        reflection_stats = {}
        if use_reflection and recommendations:
            recommendations, reflection_stats = await self._apply_reflection(
                recommendations, validation, context
            )

        # Optionally persist
        if params.get("persist", True):
            rec_ids = await self.persist_recommendations(recommendations, context)
            return {
                "recommendations": recommendations,
                "persisted_ids": rec_ids,
                "count": len(recommendations),
                "reflection": reflection_stats
            }
        else:
            return {
                "recommendations": recommendations,
                "count": len(recommendations),
                "reflection": reflection_stats
            }

    async def handle_generate_with_reflection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP request to generate recommendations with explicit reflection."""
        params["use_reflection"] = True
        return await self.handle_generate_recommendations(params)
    
    async def generate_recommendations(
        self,
        validation: Dict[str, Any],
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate recommendations for a single validation failure.
        
        Args:
            validation: The validation result dict
            content: Full content being validated
            context: Additional context (file path, family, etc.)
            
        Returns:
            List of recommendation dicts with structure:
            {
                "validation_id": str,
                "scope": str (e.g., "line:42", "section:intro", "global"),
                "instruction": str (concrete action to take),
                "rationale": str (why this would fix the issue),
                "severity": str (critical|high|medium|low),
                "confidence": float (0.0-1.0),
            }
        """
        context = context or {}
        recommendations = []
        
        # Extract validation details
        validation_id = validation.get("id", "unknown")
        validation_type = validation.get("validation_type", "unknown")
        status = validation.get("status", "unknown")
        message = validation.get("message", "")
        details = validation.get("details", {})
        
        # Only generate recommendations for failures
        if status not in ["fail", "FAIL", "warning", "WARNING"]:
            logger.debug(f"Skipping recommendation generation for passing validation {validation_id}")
            return recommendations
        
        logger.info(f"Generating recommendations for validation {validation_id} (type: {validation_type})")
        
        # Generate recommendations based on validation type
        if validation_type == "yaml":
            recommendations.extend(self._generate_yaml_recommendations(
                validation_id, message, details, content, context
            ))
        elif validation_type == "markdown":
            recommendations.extend(self._generate_markdown_recommendations(
                validation_id, message, details, content, context
            ))
        elif validation_type == "code":
            recommendations.extend(self._generate_code_recommendations(
                validation_id, message, details, content, context
            ))
        elif validation_type == "links":
            recommendations.extend(self._generate_link_recommendations(
                validation_id, message, details, content, context
            ))
        elif validation_type == "structure":
            recommendations.extend(self._generate_structure_recommendations(
                validation_id, message, details, content, context
            ))
        elif validation_type == "truth":
            recommendations.extend(self._generate_truth_recommendations(
                validation_id, message, details, content, context
            ))
        else:
            # Generic fallback
            recommendations.extend(self._generate_generic_recommendations(
                validation_id, message, details, content, context
            ))
        
        logger.info(f"Generated {len(recommendations)} recommendations for validation {validation_id}")
        return recommendations

    async def _apply_reflection(
        self,
        recommendations: List[Dict[str, Any]],
        validation: Dict[str, Any],
        context: Dict[str, Any]
    ) -> tuple:
        """
        Apply the reflection pattern to improve recommendation quality.

        Args:
            recommendations: Raw recommendations to process
            validation: Original validation result
            context: Additional context

        Returns:
            Tuple of (processed_recommendations, reflection_stats)
        """
        critic = self._get_critic()
        if not critic:
            logger.debug("Critic not available, skipping reflection")
            return recommendations, {"enabled": False}

        try:
            # Build context for critic with validation info
            critique_context = {
                **context,
                "issue_type": validation.get("validation_type", "unknown"),
                "issue_message": validation.get("message", ""),
                "validation_id": validation.get("id", "")
            }

            # Process recommendations through the full reflection pipeline
            result = await critic.handle_process_recommendations({
                "recommendations": recommendations,
                "context": critique_context
            })

            processed = result.get("recommendations", recommendations)
            stats = {
                "enabled": True,
                "discarded_count": result.get("discarded_count", 0),
                "refined_count": result.get("refined_count", 0),
                "deduplicated_count": result.get("deduplicated_count", 0),
                "original_count": len(recommendations),
                "final_count": len(processed)
            }

            logger.info(
                f"Reflection complete: {stats['original_count']} -> {stats['final_count']} "
                f"(discarded={stats['discarded_count']}, refined={stats['refined_count']}, "
                f"deduped={stats['deduplicated_count']})"
            )

            return processed, stats

        except Exception as e:
            logger.error(f"Reflection failed: {e}", exc_info=True)
            return recommendations, {"enabled": False, "error": str(e)}

    def _generate_yaml_recommendations(
        self,
        validation_id: str,
        message: str,
        details: Dict[str, Any],
        content: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate recommendations for YAML validation failures."""
        recommendations = []
        
        if "missing" in message.lower() or "required" in message.lower():
            # Missing required field
            field_name = details.get("field", "unknown")
            recommendations.append({
                "validation_id": validation_id,
                "scope": "frontmatter",
                "instruction": f"Add required field '{field_name}' to the YAML frontmatter with an appropriate value",
                "rationale": f"Field '{field_name}' is required for proper content processing and categorization",
                "severity": "high",
                "confidence": 0.95,
            })
        elif "invalid" in message.lower() or "malformed" in message.lower():
            # Invalid YAML syntax
            line = details.get("line")
            scope = f"line:{line}" if line else "frontmatter"
            recommendations.append({
                "validation_id": validation_id,
                "scope": scope,
                "instruction": "Fix YAML syntax errors in frontmatter (check indentation, colons, quotes)",
                "rationale": "Valid YAML syntax is required for the document to be parsed correctly",
                "severity": "critical",
                "confidence": 0.98,
            })
        else:
            # Generic YAML issue
            recommendations.append({
                "validation_id": validation_id,
                "scope": "frontmatter",
                "instruction": "Review and fix YAML frontmatter according to schema requirements",
                "rationale": "Ensures content metadata conforms to expected structure",
                "severity": "medium",
                "confidence": 0.70,
            })
        
        return recommendations
    
    def _generate_markdown_recommendations(
        self,
        validation_id: str,
        message: str,
        details: Dict[str, Any],
        content: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate recommendations for Markdown validation failures."""
        recommendations = []
        
        if "heading" in message.lower():
            line = details.get("line")
            scope = f"line:{line}" if line else "global"
            recommendations.append({
                "validation_id": validation_id,
                "scope": scope,
                "instruction": "Ensure heading levels follow sequential order (h1 -> h2 -> h3, no skipping)",
                "rationale": "Proper heading hierarchy improves document structure and accessibility",
                "severity": "medium",
                "confidence": 0.85,
            })
        elif "list" in message.lower():
            recommendations.append({
                "validation_id": validation_id,
                "scope": "global",
                "instruction": "Fix list formatting (consistent indentation, proper markers)",
                "rationale": "Proper list syntax ensures correct rendering and readability",
                "severity": "low",
                "confidence": 0.80,
            })
        else:
            recommendations.append({
                "validation_id": validation_id,
                "scope": "global",
                "instruction": "Review markdown syntax and fix any formatting issues",
                "rationale": "Valid markdown ensures proper rendering and maintainability",
                "severity": "medium",
                "confidence": 0.75,
            })
        
        return recommendations
    
    def _generate_code_recommendations(
        self,
        validation_id: str,
        message: str,
        details: Dict[str, Any],
        content: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate recommendations for code block validation failures."""
        recommendations = []
        
        if "language" in message.lower():
            block_line = details.get("line")
            scope = f"line:{block_line}" if block_line else "code_blocks"
            recommendations.append({
                "validation_id": validation_id,
                "scope": scope,
                "instruction": "Add language identifier to code fence (e.g., ```python, ```csharp)",
                "rationale": "Language identifiers enable syntax highlighting and improve code readability",
                "severity": "medium",
                "confidence": 0.90,
            })
        elif "syntax" in message.lower() or "error" in message.lower():
            recommendations.append({
                "validation_id": validation_id,
                "scope": "code_blocks",
                "instruction": "Fix syntax errors in code examples and verify they compile/run correctly",
                "rationale": "Working code examples are essential for user trust and documentation quality",
                "severity": "high",
                "confidence": 0.85,
            })
        else:
            recommendations.append({
                "validation_id": validation_id,
                "scope": "code_blocks",
                "instruction": "Review code blocks for quality, correctness, and best practices",
                "rationale": "High-quality code examples improve user experience and reduce support burden",
                "severity": "medium",
                "confidence": 0.70,
            })
        
        return recommendations
    
    def _generate_link_recommendations(
        self,
        validation_id: str,
        message: str,
        details: Dict[str, Any],
        content: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate recommendations for link validation failures."""
        recommendations = []
        
        broken_url = details.get("url", "")
        link_text = details.get("text", "")
        
        if "broken" in message.lower() or "404" in message.lower():
            recommendations.append({
                "validation_id": validation_id,
                "scope": f"url:{broken_url}" if broken_url else "links",
                "instruction": f"Fix or remove broken link: {broken_url}. Verify the target page exists or update to correct URL",
                "rationale": "Broken links harm user experience and SEO rankings",
                "severity": "high",
                "confidence": 0.95,
            })
        elif "anchor" in message.lower():
            recommendations.append({
                "validation_id": validation_id,
                "scope": "links",
                "instruction": "Verify that anchor links point to existing heading IDs in the target document",
                "rationale": "Invalid anchors lead to 404 errors and poor user experience",
                "severity": "medium",
                "confidence": 0.85,
            })
        else:
            recommendations.append({
                "validation_id": validation_id,
                "scope": "links",
                "instruction": "Review and test all links to ensure they point to valid, accessible resources",
                "rationale": "Valid links are essential for navigation and content discoverability",
                "severity": "medium",
                "confidence": 0.80,
            })
        
        return recommendations
    
    def _generate_structure_recommendations(
        self,
        validation_id: str,
        message: str,
        details: Dict[str, Any],
        content: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate recommendations for document structure validation failures."""
        recommendations = []
        
        if "title" in message.lower():
            recommendations.append({
                "validation_id": validation_id,
                "scope": "document",
                "instruction": "Add a clear, descriptive title (h1) at the top of the document",
                "rationale": "Document title is essential for SEO, navigation, and user comprehension",
                "severity": "high",
                "confidence": 0.95,
            })
        elif "section" in message.lower():
            recommendations.append({
                "validation_id": validation_id,
                "scope": "document",
                "instruction": "Organize content into logical sections with appropriate headings",
                "rationale": "Clear structure improves readability and helps users find information",
                "severity": "medium",
                "confidence": 0.80,
            })
        else:
            recommendations.append({
                "validation_id": validation_id,
                "scope": "document",
                "instruction": "Review document structure to ensure it follows organizational best practices",
                "rationale": "Well-structured content improves comprehension and maintainability",
                "severity": "medium",
                "confidence": 0.75,
            })
        
        return recommendations
    
    def _generate_truth_recommendations(
        self,
        validation_id: str,
        message: str,
        details: Dict[str, Any],
        content: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate recommendations for truth/terminology validation failures."""
        recommendations = []
        
        incorrect_term = details.get("found", "")
        correct_term = details.get("expected", "")
        
        if incorrect_term and correct_term:
            recommendations.append({
                "validation_id": validation_id,
                "scope": "global",
                "instruction": f"Replace '{incorrect_term}' with '{correct_term}' throughout the document",
                "rationale": f"Consistent use of correct terminology ('{correct_term}') ensures accuracy and professionalism",
                "severity": "high",
                "confidence": 0.95,
            })
        else:
            recommendations.append({
                "validation_id": validation_id,
                "scope": "global",
                "instruction": "Review terminology usage and align with approved terminology standards",
                "rationale": "Consistent, accurate terminology improves clarity and maintains brand standards",
                "severity": "medium",
                "confidence": 0.80,
            })
        
        return recommendations
    
    def _generate_generic_recommendations(
        self,
        validation_id: str,
        message: str,
        details: Dict[str, Any],
        content: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate generic recommendations when specific type is unknown."""
        recommendations = []
        
        # Provide a generic actionable recommendation
        recommendations.append({
            "validation_id": validation_id,
            "scope": "global",
            "instruction": f"Address validation issue: {message}",
            "rationale": "Resolving this validation failure will improve content quality and compliance",
            "severity": "medium",
            "confidence": 0.60,
        })
        
        return recommendations
    
    async def persist_recommendations(
        self,
        recommendations: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Persist recommendations to database with proposed status.
        
        Returns:
            List of created recommendation IDs
        """
        recommendation_ids = []
        
        for rec_data in recommendations:
            try:
                # Ensure required fields
                if "validation_id" not in rec_data:
                    logger.warning("Skipping recommendation without validation_id")
                    continue
                
                # Create recommendation in database with proposed status
                rec = db_manager.create_recommendation(
                    validation_id=rec_data["validation_id"],
                    type="automated",
                    title=rec_data.get("instruction", "")[:200],  # Truncate to reasonable length
                    description=rec_data.get("rationale", ""),
                    scope=rec_data.get("scope", "global"),
                    instruction=rec_data.get("instruction", ""),
                    rationale=rec_data.get("rationale", ""),
                    severity=rec_data.get("severity", "medium"),
                    confidence=rec_data.get("confidence", 0.5),
                    status="proposed",  # All start as proposed
                    metadata=rec_data.get("metadata", {}),
                )
                
                if rec:
                    recommendation_ids.append(rec.id)
                    logger.debug(f"Persisted recommendation {rec.id} for validation {rec_data['validation_id']}")

                    # Broadcast recommendation creation event
                    try:
                        from api.services.live_bus import get_live_bus
                        live_bus = get_live_bus()
                        await live_bus.publish_recommendation_update(
                            rec.id,
                            "recommendation_created",
                            {
                                "validation_id": rec_data["validation_id"],
                                "title": rec_data.get("instruction", "")[:100],
                                "type": "automated",
                                "status": "proposed"
                            }
                        )
                    except Exception as broadcast_error:
                        logger.warning(f"Failed to broadcast recommendation_created event: {broadcast_error}")
                
            except Exception as e:
                logger.error(f"Failed to persist recommendation: {e}", exc_info=True)
        
        logger.info(f"Persisted {len(recommendation_ids)} recommendations")
        return recommendation_ids
