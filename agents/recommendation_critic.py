# file: agents/recommendation_critic.py
"""
RecommendationCriticAgent: Critiques and refines recommendations before persistence.

Implements the Reflection pattern for recommendation quality improvement:
1. Critique: Evaluate recommendation quality on multiple dimensions
2. Refine: Improve recommendations that don't meet quality threshold
3. Deduplicate: Remove semantically similar recommendations

This agent can operate in two modes:
- LLM mode: Uses LLM for semantic critique (higher quality, slower)
- Rule mode: Uses heuristic rules (faster, no LLM dependency)
"""

from __future__ import annotations

import json
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from agents.base import BaseAgent, AgentCapability, AgentContract
from core.logging import get_logger
from core.config_loader import get_config_loader

logger = get_logger(__name__)


@dataclass
class CritiqueResult:
    """Result of critiquing a recommendation."""
    actionable: bool = True
    actionable_reason: str = ""
    fixes_issue: bool = True
    fixes_issue_reason: str = ""
    specific: bool = True
    specific_reason: str = ""
    side_effects: List[str] = field(default_factory=list)
    quality_score: float = 0.8
    should_discard: bool = False
    needs_refinement: bool = False
    refinement_suggestions: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "actionable": self.actionable,
            "actionable_reason": self.actionable_reason,
            "fixes_issue": self.fixes_issue,
            "fixes_issue_reason": self.fixes_issue_reason,
            "specific": self.specific,
            "specific_reason": self.specific_reason,
            "side_effects": self.side_effects,
            "quality_score": self.quality_score,
            "should_discard": self.should_discard,
            "needs_refinement": self.needs_refinement,
            "refinement_suggestions": self.refinement_suggestions
        }


class RecommendationCriticAgent(BaseAgent):
    """
    Agent that critiques and refines recommendations using reflection pattern.

    Evaluates recommendations on:
    - Actionability: Can someone implement this?
    - Effectiveness: Does it fix the issue?
    - Specificity: Is it specific enough?
    - Side effects: Could it break something?
    """

    def __init__(self, agent_id: str = "recommendation_critic"):
        self._config = None
        self._prompts = None
        super().__init__(agent_id)
        self._load_config()
        self._load_prompts()

    def _load_config(self):
        """Load reflection configuration."""
        try:
            config_loader = get_config_loader()
            self._config = config_loader.load("reflection")
            if not self._config:
                self._config = self._default_config()
            logger.debug("Loaded reflection config")
        except Exception as e:
            logger.warning(f"Failed to load reflection config, using defaults: {e}")
            self._config = self._default_config()

    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "reflection": {
                "enabled": True,
                "thresholds": {
                    "quality_threshold": 0.7,
                    "discard_threshold": 0.3,
                    "similarity_threshold": 0.85
                },
                "refinement": {
                    "max_iterations": 2,
                    "use_llm": False
                },
                "deduplication": {
                    "enabled": True,
                    "method": "fuzzy"
                },
                "dimensions": {
                    "actionable": {"weight": 0.3},
                    "fixes_issue": {"weight": 0.3},
                    "specific": {"weight": 0.2},
                    "side_effects": {"weight": 0.2}
                },
                "rules": {
                    "require_rationale": True,
                    "min_instruction_length": 20,
                    "max_instruction_length": 500,
                    "banned_phrases": [
                        "review and fix",
                        "check and update",
                        "ensure proper"
                    ]
                }
            }
        }

    def _load_prompts(self):
        """Load critique prompts."""
        try:
            import os
            prompts_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "prompts",
                "recommendation_critique.json"
            )
            if os.path.exists(prompts_path):
                with open(prompts_path, "r", encoding="utf-8") as f:
                    self._prompts = json.load(f)
            else:
                self._prompts = {}
            logger.debug("Loaded critique prompts")
        except Exception as e:
            logger.warning(f"Failed to load critique prompts: {e}")
            self._prompts = {}

    @property
    def config(self) -> Dict[str, Any]:
        """Get reflection config section."""
        return self._config.get("reflection", self._default_config()["reflection"])

    def get_contract(self) -> AgentContract:
        """Return agent contract for registration."""
        return AgentContract(
            agent_id=self.agent_id,
            name="RecommendationCriticAgent",
            version="1.0.0",
            capabilities=[
                AgentCapability(
                    name="critique",
                    description="Evaluate recommendation quality",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "recommendation": {"type": "object"},
                            "context": {"type": "object"}
                        },
                        "required": ["recommendation"]
                    },
                    output_schema={"type": "object"},
                    side_effects=[]
                ),
                AgentCapability(
                    name="refine",
                    description="Improve recommendation based on critique",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "recommendation": {"type": "object"},
                            "critique": {"type": "object"}
                        },
                        "required": ["recommendation", "critique"]
                    },
                    output_schema={"type": "object"},
                    side_effects=[]
                ),
                AgentCapability(
                    name="deduplicate",
                    description="Remove semantically similar recommendations",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "recommendations": {"type": "array"}
                        },
                        "required": ["recommendations"]
                    },
                    output_schema={"type": "array"},
                    side_effects=[]
                )
            ],
            checkpoints=[],
            max_runtime_s=60,
            confidence_threshold=0.7,
            side_effects=[],
            dependencies=[]
        )

    def _register_message_handlers(self):
        """Register MCP message handlers."""
        self.register_handler("critique", self.handle_critique)
        self.register_handler("refine", self.handle_refine)
        self.register_handler("deduplicate", self.handle_deduplicate)
        self.register_handler("process_recommendations", self.handle_process_recommendations)

    async def handle_critique(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP critique request."""
        recommendation = params.get("recommendation", {})
        context = params.get("context", {})
        result = await self.critique(recommendation, context)
        return result.to_dict()

    async def handle_refine(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP refine request."""
        recommendation = params.get("recommendation", {})
        critique = params.get("critique", {})
        return await self.refine(recommendation, critique)

    async def handle_deduplicate(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle MCP deduplicate request."""
        recommendations = params.get("recommendations", [])
        return self.deduplicate(recommendations)

    async def handle_process_recommendations(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a batch of recommendations through the full reflection pipeline.

        Returns:
            Dict with:
            - recommendations: List of refined recommendations
            - discarded_count: Number of discarded recommendations
            - refined_count: Number of refined recommendations
            - deduplicated_count: Number removed as duplicates
        """
        recommendations = params.get("recommendations", [])
        context = params.get("context", {})

        if not self.config.get("enabled", True):
            return {
                "recommendations": recommendations,
                "discarded_count": 0,
                "refined_count": 0,
                "deduplicated_count": 0,
                "reflection_enabled": False
            }

        processed = []
        discarded_count = 0
        refined_count = 0

        thresholds = self.config.get("thresholds", {})
        quality_threshold = thresholds.get("quality_threshold", 0.7)
        max_iterations = self.config.get("refinement", {}).get("max_iterations", 2)

        for rec in recommendations:
            current_rec = rec.copy()
            iterations = 0

            while iterations < max_iterations:
                critique = await self.critique(current_rec, context)

                if critique.should_discard:
                    logger.info(
                        f"Discarding low-quality recommendation: "
                        f"score={critique.quality_score:.2f}"
                    )
                    discarded_count += 1
                    break

                if critique.quality_score >= quality_threshold:
                    current_rec["critique_score"] = critique.quality_score
                    processed.append(current_rec)
                    break

                if critique.needs_refinement:
                    current_rec = await self.refine(current_rec, critique.to_dict())
                    refined_count += 1
                    iterations += 1
                else:
                    current_rec["critique_score"] = critique.quality_score
                    processed.append(current_rec)
                    break

            else:
                # Max iterations reached, keep the last version
                current_rec["critique_score"] = critique.quality_score
                processed.append(current_rec)

        # Deduplicate
        original_count = len(processed)
        if self.config.get("deduplication", {}).get("enabled", True):
            processed = self.deduplicate(processed)
        deduplicated_count = original_count - len(processed)

        return {
            "recommendations": processed,
            "discarded_count": discarded_count,
            "refined_count": refined_count,
            "deduplicated_count": deduplicated_count,
            "reflection_enabled": True
        }

    async def critique(
        self,
        recommendation: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> CritiqueResult:
        """
        Evaluate a recommendation's quality.

        Args:
            recommendation: The recommendation to evaluate
            context: Additional context (file_path, family, issue details)

        Returns:
            CritiqueResult with quality assessment
        """
        context = context or {}
        use_llm = self.config.get("refinement", {}).get("use_llm", False)

        if use_llm and self._prompts.get("critique"):
            return await self._critique_with_llm(recommendation, context)
        else:
            return self._critique_with_rules(recommendation, context)

    def _critique_with_rules(
        self,
        recommendation: Dict[str, Any],
        context: Dict[str, Any]
    ) -> CritiqueResult:
        """Evaluate recommendation using heuristic rules."""
        result = CritiqueResult()
        # Handle None values gracefully
        instruction = recommendation.get("instruction") or ""
        rationale = recommendation.get("rationale") or ""
        scope = recommendation.get("scope") or "global"
        rules = self.config.get("rules", {})
        dimensions = self.config.get("dimensions", {})

        scores = {}

        # Check actionability
        banned_phrases = rules.get("banned_phrases", [])
        instruction_lower = instruction.lower()
        has_banned = any(phrase in instruction_lower for phrase in banned_phrases)

        if has_banned:
            result.actionable = False
            result.actionable_reason = "Contains vague phrases that are not actionable"
            scores["actionable"] = 0.3
        elif len(instruction) < rules.get("min_instruction_length", 20):
            result.actionable = False
            result.actionable_reason = "Instruction is too short to be actionable"
            scores["actionable"] = 0.4
        else:
            result.actionable = True
            result.actionable_reason = "Instruction provides clear action"
            scores["actionable"] = 1.0

        # Check if it addresses the issue
        issue_type = context.get("issue_type", "")
        issue_message = context.get("issue_message", "")

        if issue_type and issue_type.lower() in instruction_lower:
            result.fixes_issue = True
            result.fixes_issue_reason = "Instruction directly addresses the issue type"
            scores["fixes_issue"] = 1.0
        elif rationale and len(rationale) > 20:
            result.fixes_issue = True
            result.fixes_issue_reason = "Rationale explains how it fixes the issue"
            scores["fixes_issue"] = 0.8
        else:
            result.fixes_issue = False
            result.fixes_issue_reason = "Unclear how this fixes the original issue"
            scores["fixes_issue"] = 0.5

        # Check specificity
        if scope != "global" and (":" in scope or scope in ["frontmatter", "code_blocks", "links"]):
            result.specific = True
            result.specific_reason = "Scope is well-defined"
            scores["specific"] = 1.0
        elif "line" in scope or "section" in scope:
            result.specific = True
            result.specific_reason = "Targets specific location"
            scores["specific"] = 0.9
        else:
            result.specific = False
            result.specific_reason = "Scope is too broad"
            scores["specific"] = 0.6

        # Check for potential side effects
        risky_keywords = ["replace all", "remove", "delete", "global", "everywhere"]
        if any(kw in instruction_lower for kw in risky_keywords):
            result.side_effects = ["May affect other parts of the document"]
            scores["side_effects"] = 0.7
        else:
            result.side_effects = []
            scores["side_effects"] = 1.0

        # Calculate weighted quality score
        total_weight = sum(d.get("weight", 0.25) for d in dimensions.values())
        weighted_score = 0.0
        for dim_name, dim_config in dimensions.items():
            weight = dim_config.get("weight", 0.25)
            score = scores.get(dim_name, 0.5)
            weighted_score += (weight / total_weight) * score

        result.quality_score = weighted_score

        # Determine actions
        thresholds = self.config.get("thresholds", {})
        discard_threshold = thresholds.get("discard_threshold", 0.3)
        quality_threshold = thresholds.get("quality_threshold", 0.7)

        if result.quality_score < discard_threshold:
            result.should_discard = True
            result.needs_refinement = False
            result.refinement_suggestions = "Quality too low, consider generating new recommendation"
        elif result.quality_score < quality_threshold:
            result.should_discard = False
            result.needs_refinement = True
            suggestions = []
            if not result.actionable:
                suggestions.append("Make instruction more specific and actionable")
            if not result.fixes_issue:
                suggestions.append("Clarify how this addresses the original issue")
            if not result.specific:
                suggestions.append("Narrow the scope to specific location")
            if result.side_effects:
                suggestions.append("Add guidance to minimize unintended changes")
            result.refinement_suggestions = "; ".join(suggestions) if suggestions else ""
        else:
            result.should_discard = False
            result.needs_refinement = False

        return result

    async def _critique_with_llm(
        self,
        recommendation: Dict[str, Any],
        context: Dict[str, Any]
    ) -> CritiqueResult:
        """Evaluate recommendation using LLM."""
        try:
            from core.ollama import ollama

            prompt_template = self._prompts.get("critique", {}).get("template", "")
            if not prompt_template:
                return self._critique_with_rules(recommendation, context)

            prompt = prompt_template.format(
                instruction=recommendation.get("instruction", ""),
                scope=recommendation.get("scope", "global"),
                severity=recommendation.get("severity", "medium"),
                rationale=recommendation.get("rationale", ""),
                issue_type=context.get("issue_type", "unknown"),
                issue_message=context.get("issue_message", ""),
                file_path=context.get("file_path", ""),
                family=context.get("family", "")
            )

            response = await ollama.async_generate(
                prompt=prompt,
                options={"temperature": 0.3}
            )

            # Parse JSON response
            response_text = response.get("response", "")
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return CritiqueResult(
                    actionable=data.get("actionable", True),
                    actionable_reason=data.get("actionable_reason", ""),
                    fixes_issue=data.get("fixes_issue", True),
                    fixes_issue_reason=data.get("fixes_issue_reason", ""),
                    specific=data.get("specific", True),
                    specific_reason=data.get("specific_reason", ""),
                    side_effects=data.get("side_effects", []),
                    quality_score=data.get("quality_score", 0.7),
                    should_discard=data.get("should_discard", False),
                    needs_refinement=data.get("needs_refinement", False),
                    refinement_suggestions=data.get("refinement_suggestions", "")
                )

        except Exception as e:
            logger.warning(f"LLM critique failed, falling back to rules: {e}")

        return self._critique_with_rules(recommendation, context)

    async def refine(
        self,
        recommendation: Dict[str, Any],
        critique: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Improve a recommendation based on critique.

        Args:
            recommendation: Original recommendation
            critique: Critique result with suggestions

        Returns:
            Refined recommendation
        """
        use_llm = self.config.get("refinement", {}).get("use_llm", False)

        if use_llm and self._prompts.get("refine"):
            return await self._refine_with_llm(recommendation, critique)
        else:
            return self._refine_with_rules(recommendation, critique)

    def _refine_with_rules(
        self,
        recommendation: Dict[str, Any],
        critique: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Refine recommendation using heuristic rules."""
        refined = recommendation.copy()
        instruction = refined.get("instruction", "")
        suggestions = critique.get("refinement_suggestions", "")

        # Remove banned phrases
        banned_phrases = self.config.get("rules", {}).get("banned_phrases", [])
        for phrase in banned_phrases:
            if phrase.lower() in instruction.lower():
                # Replace with more specific language
                instruction = re.sub(
                    re.escape(phrase),
                    "specifically address",
                    instruction,
                    flags=re.IGNORECASE
                )

        # Improve scope if too broad
        if not critique.get("specific", True) and refined.get("scope") == "global":
            validation_id = refined.get("validation_id", "")
            if validation_id:
                refined["scope"] = f"issue:{validation_id}"

        # Add rationale if missing
        if not refined.get("rationale") or len(refined.get("rationale", "")) < 10:
            issue_msg = critique.get("issue_message", "the identified issue")
            refined["rationale"] = f"This change will resolve {issue_msg} and improve content quality."

        refined["instruction"] = instruction
        refined["refined"] = True
        refined["refinement_iteration"] = refined.get("refinement_iteration", 0) + 1

        return refined

    async def _refine_with_llm(
        self,
        recommendation: Dict[str, Any],
        critique: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Refine recommendation using LLM."""
        try:
            from core.ollama import ollama

            prompt_template = self._prompts.get("refine", {}).get("template", "")
            if not prompt_template:
                return self._refine_with_rules(recommendation, critique)

            prompt = prompt_template.format(
                instruction=recommendation.get("instruction", ""),
                scope=recommendation.get("scope", "global"),
                severity=recommendation.get("severity", "medium"),
                rationale=recommendation.get("rationale", ""),
                actionable=critique.get("actionable", True),
                actionable_reason=critique.get("actionable_reason", ""),
                fixes_issue=critique.get("fixes_issue", True),
                fixes_issue_reason=critique.get("fixes_issue_reason", ""),
                specific=critique.get("specific", True),
                specific_reason=critique.get("specific_reason", ""),
                side_effects=", ".join(critique.get("side_effects", [])),
                refinement_suggestions=critique.get("refinement_suggestions", ""),
                issue_type=critique.get("issue_type", "unknown"),
                issue_message=critique.get("issue_message", "")
            )

            response = await ollama.async_generate(
                prompt=prompt,
                options={"temperature": 0.4}
            )

            response_text = response.get("response", "")
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                refined = recommendation.copy()
                refined["instruction"] = data.get("instruction", refined["instruction"])
                refined["scope"] = data.get("scope", refined["scope"])
                refined["severity"] = data.get("severity", refined["severity"])
                refined["rationale"] = data.get("rationale", refined["rationale"])
                refined["confidence"] = data.get("confidence", refined.get("confidence", 0.7))
                refined["refined"] = True
                refined["refinement_iteration"] = refined.get("refinement_iteration", 0) + 1
                return refined

        except Exception as e:
            logger.warning(f"LLM refinement failed, falling back to rules: {e}")

        return self._refine_with_rules(recommendation, critique)

    def deduplicate(
        self,
        recommendations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Remove semantically similar recommendations.

        Args:
            recommendations: List of recommendations

        Returns:
            Deduplicated list (keeps highest quality)
        """
        if not recommendations or len(recommendations) <= 1:
            return recommendations

        dedup_config = self.config.get("deduplication", {})
        method = dedup_config.get("method", "fuzzy")
        threshold = self.config.get("thresholds", {}).get("similarity_threshold", 0.85)
        compare_fields = dedup_config.get("compare_fields", ["instruction", "scope"])

        # Sort by quality score (highest first)
        sorted_recs = sorted(
            recommendations,
            key=lambda r: r.get("critique_score", r.get("confidence", 0.5)),
            reverse=True
        )

        unique = []
        for rec in sorted_recs:
            is_duplicate = False
            for existing in unique:
                similarity = self._calculate_similarity(rec, existing, compare_fields, method)
                if similarity >= threshold:
                    is_duplicate = True
                    logger.debug(
                        f"Duplicate found: similarity={similarity:.2f}, "
                        f"keeping higher quality version"
                    )
                    break

            if not is_duplicate:
                unique.append(rec)

        return unique

    def _calculate_similarity(
        self,
        rec1: Dict[str, Any],
        rec2: Dict[str, Any],
        fields: List[str],
        method: str
    ) -> float:
        """Calculate similarity between two recommendations."""
        if method == "exact":
            return 1.0 if all(
                rec1.get(f, "") == rec2.get(f, "") for f in fields
            ) else 0.0

        elif method == "fuzzy":
            similarities = []
            for field in fields:
                val1 = str(rec1.get(field, "")).lower()
                val2 = str(rec2.get(field, "")).lower()
                ratio = SequenceMatcher(None, val1, val2).ratio()
                similarities.append(ratio)
            return sum(similarities) / len(similarities) if similarities else 0.0

        else:  # semantic - would use embeddings
            # Fall back to fuzzy for now
            return self._calculate_similarity(rec1, rec2, fields, "fuzzy")

    def is_enabled(self) -> bool:
        """Check if reflection is enabled."""
        return self.config.get("enabled", True)
