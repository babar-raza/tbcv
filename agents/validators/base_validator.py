# file: agents/validators/base_validator.py
"""
Base validator agent - foundation for all content validators.
"""

from __future__ import annotations
from abc import abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from agents.base import BaseAgent, AgentContract, AgentCapability
from core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ValidationIssue:
    """Represents a single validation issue."""
    level: str  # "error", "warning", "info", "critical"
    category: str
    message: str
    line_number: Optional[int] = None
    column: Optional[int] = None
    suggestion: Optional[str] = None
    source: str = "validator"
    auto_fixable: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level,
            "category": self.category,
            "message": self.message,
            "line_number": self.line_number,
            "column": self.column,
            "suggestion": self.suggestion,
            "source": self.source,
            "auto_fixable": self.auto_fixable
        }


@dataclass
class ValidationResult:
    """Result of a validation operation."""
    confidence: float
    issues: List[ValidationIssue] = field(default_factory=list)
    auto_fixable_count: int = 0
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "confidence": self.confidence,
            "issues": [issue.to_dict() for issue in self.issues],
            "auto_fixable_count": self.auto_fixable_count,
            "metrics": self.metrics
        }


class BaseValidatorAgent(BaseAgent):
    """
    Abstract base class for all validator agents.
    Provides common validation infrastructure and interface.
    """

    @abstractmethod
    def get_validation_type(self) -> str:
        """Return the validation type identifier (e.g., 'yaml', 'markdown', 'seo')."""
        pass

    @abstractmethod
    async def validate(self, content: str, context: Dict[str, Any]) -> ValidationResult:
        """
        Validate content and return issues.

        Args:
            content: The content to validate
            context: Additional context (file_path, family, etc.)

        Returns:
            ValidationResult with issues and metrics
        """
        pass

    def _register_message_handlers(self):
        """Register MCP message handlers."""
        self.register_handler("ping", self.handle_ping)
        self.register_handler("get_status", self.handle_get_status)
        self.register_handler("get_contract", self.get_contract)
        self.register_handler("validate", self.handle_validate)

    async def handle_validate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle validate request."""
        content = params.get("content", "")
        context = params.get("context", {})

        result = await self.validate(content, context)
        return result.to_dict()

    def get_contract(self) -> AgentContract:
        """Return agent contract."""
        return AgentContract(
            agent_id=self.agent_id,
            name=self.__class__.__name__,
            version="1.0.0",
            capabilities=[
                AgentCapability(
                    name="validate",
                    description=f"Validate {self.get_validation_type()} content",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "content": {"type": "string"},
                            "context": {
                                "type": "object",
                                "properties": {
                                    "file_path": {"type": "string"},
                                    "family": {"type": "string"},
                                    "validation_type": {"type": "string"}
                                }
                            }
                        },
                        "required": ["content"]
                    },
                    output_schema={
                        "type": "object",
                        "properties": {
                            "confidence": {"type": "number"},
                            "issues": {"type": "array"},
                            "metrics": {"type": "object"}
                        }
                    },
                    side_effects=["read"]
                )
            ],
            checkpoints=[],
            max_runtime_s=30,
            confidence_threshold=0.5,
            side_effects=["read"]
        )
