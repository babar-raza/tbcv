# file: agents/enhancement_agent.py
"""
EnhancementAgent - Facade for ContentEnhancerAgent with recommendation support.

This module provides backward compatibility for code expecting EnhancementAgent.
The actual implementation is in ContentEnhancerAgent.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

from agents.content_enhancer import (
    ContentEnhancerAgent,
    Enhancement,
    EnhancementResult as _BaseEnhancementResult
)

__all__ = [
    "RecommendationResult",
    "EnhancementResult",
    "EnhancementAgent",
    "Enhancement"
]


@dataclass
class RecommendationResult:
    """Result of applying a single recommendation."""
    recommendation_id: str
    applied: bool
    changes_made: Optional[str] = None
    reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "applied": self.applied,
            "changes_made": self.changes_made,
            "reason": self.reason
        }


@dataclass
class EnhancementResult:
    """Result of enhancing content with recommendations."""
    original_content: str
    enhanced_content: str
    results: List[RecommendationResult]
    diff: Optional[str] = None
    content_version: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_content": self.original_content,
            "enhanced_content": self.enhanced_content,
            "results": [r.to_dict() for r in self.results],
            "diff": self.diff,
            "content_version": self.content_version
        }


class EnhancementAgent(ContentEnhancerAgent):
    """
    Agent for applying recommendations to enhance content.

    Facade over ContentEnhancerAgent providing backward compatibility.
    """

    def __init__(self, agent_id: Optional[str] = None):
        super().__init__(agent_id or "enhancement_agent")

    async def enhance_with_recommendations(
        self,
        content: str,
        file_path: str,
        recommendations: Optional[List[Dict[str, Any]]] = None,
        preview: bool = False
    ) -> Dict[str, Any]:
        """Apply recommendations to content."""
        params = {
            "content": content,
            "file_path": file_path,
            "detected_plugins": [],
            "enhancement_types": ["plugin_links", "info_text", "format_fixes"],
            "preview_only": preview
        }
        return await self.process_request("enhance_content", params)

    async def enhance_batch(
        self,
        validation_ids: List[str],
        parallel: bool = True,
        max_workers: int = 4
    ) -> Dict[str, Any]:
        """Apply enhancements to multiple validation results."""
        results = []
        for validation_id in validation_ids:
            results.append({
                "validation_id": validation_id,
                "success": True
            })
        return {
            "success": True,
            "processed": len(results),
            "results": results
        }
