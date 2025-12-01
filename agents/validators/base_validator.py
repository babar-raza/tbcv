# file: agents/validators/base_validator.py
"""
Base validator agent - foundation for all content validators.
Includes enhanced ValidationIssue with comprehensive fields for error reporting.
"""

from __future__ import annotations
from abc import abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import uuid

from agents.base import BaseAgent, AgentContract, AgentCapability
from core.logging import get_logger

logger = get_logger(__name__)

# Severity scoring constants
SEVERITY_SCORES = {
    "critical": 100,
    "error": 75,
    "warning": 50,
    "info": 25
}


@dataclass
class ValidationIssue:
    """
    Represents a single validation issue with enhanced fields.

    Supports comprehensive error reporting with:
    - Identification (id, code)
    - Severity (level, severity_score)
    - Location (line_number, column, line_end)
    - Classification (category, subcategory)
    - Context (snippets before/after)
    - Fix information (suggestion, fix_example, auto_fixable)
    - Traceability (source, confidence, rule_id)
    """
    # Required fields (maintain backward compatibility)
    level: str  # "error", "warning", "info", "critical"
    category: str
    message: str

    # Identification
    id: str = ""  # Auto-generated unique ID like "YAML-001"
    code: str = ""  # Issue code like "YAML_MISSING_FIELD"

    # Severity
    severity_score: int = 50  # 1-100 for sorting

    # Location
    line_number: Optional[int] = None
    column: Optional[int] = None
    line_end: Optional[int] = None

    # Classification
    subcategory: str = ""

    # Messages
    suggestion: Optional[str] = None

    # Context
    context_snippet: str = ""  # The problematic text
    context_before: str = ""  # 2-3 lines before
    context_after: str = ""  # 2-3 lines after

    # Fix information
    fix_example: str = ""  # Actual corrected code
    auto_fixable: bool = False

    # Traceability
    source: str = "rule_based"  # "rule_based" | "llm_semantic" | "validator"
    confidence: float = 1.0
    rule_id: str = ""  # Which rule triggered this

    # Documentation
    documentation_url: str = ""

    def __post_init__(self):
        """Initialize computed fields after creation."""
        # Auto-generate ID if not provided
        if not self.id:
            prefix = self.category.split("_")[0].upper()[:4] if self.category else "VAL"
            short_uuid = str(uuid.uuid4())[:8]
            self.id = f"{prefix}-{short_uuid}"

        # Auto-generate code if not provided
        if not self.code:
            self.code = self.category.upper().replace("-", "_") if self.category else "UNKNOWN"

        # Set severity score based on level if not explicitly set
        if self.severity_score == 50:  # Default value
            self.severity_score = SEVERITY_SCORES.get(self.level, 50)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            # Identification
            "id": self.id,
            "code": self.code,
            # Severity
            "level": self.level,
            "severity_score": self.severity_score,
            # Location
            "line_number": self.line_number,
            "column": self.column,
            "line_end": self.line_end,
            # Classification
            "category": self.category,
            "subcategory": self.subcategory,
            # Messages
            "message": self.message,
            "suggestion": self.suggestion,
            # Context
            "context_snippet": self.context_snippet,
            "context_before": self.context_before,
            "context_after": self.context_after,
            # Fix information
            "fix_example": self.fix_example,
            "auto_fixable": self.auto_fixable,
            # Traceability
            "source": self.source,
            "confidence": self.confidence,
            "rule_id": self.rule_id,
            # Documentation
            "documentation_url": self.documentation_url
        }

    def to_compact_dict(self) -> Dict[str, Any]:
        """Convert to compact dictionary with only non-empty fields."""
        full = self.to_dict()
        return {k: v for k, v in full.items() if v or v == 0 or v is False}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ValidationIssue":
        """Create ValidationIssue from dictionary."""
        return cls(
            level=data.get("level", "warning"),
            category=data.get("category", ""),
            message=data.get("message", ""),
            id=data.get("id", ""),
            code=data.get("code", ""),
            severity_score=data.get("severity_score", 50),
            line_number=data.get("line_number"),
            column=data.get("column"),
            line_end=data.get("line_end"),
            subcategory=data.get("subcategory", ""),
            suggestion=data.get("suggestion"),
            context_snippet=data.get("context_snippet", ""),
            context_before=data.get("context_before", ""),
            context_after=data.get("context_after", ""),
            fix_example=data.get("fix_example", ""),
            auto_fixable=data.get("auto_fixable", False),
            source=data.get("source", "rule_based"),
            confidence=data.get("confidence", 1.0),
            rule_id=data.get("rule_id", ""),
            documentation_url=data.get("documentation_url", "")
        )


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

    def get_issues_by_level(self) -> Dict[str, List[ValidationIssue]]:
        """Group issues by severity level."""
        result: Dict[str, List[ValidationIssue]] = {
            "critical": [],
            "error": [],
            "warning": [],
            "info": []
        }
        for issue in self.issues:
            if issue.level in result:
                result[issue.level].append(issue)
        return result

    def get_issues_by_category(self) -> Dict[str, List[ValidationIssue]]:
        """Group issues by category."""
        result: Dict[str, List[ValidationIssue]] = {}
        for issue in self.issues:
            if issue.category not in result:
                result[issue.category] = []
            result[issue.category].append(issue)
        return result

    def get_sorted_issues(self, by: str = "severity") -> List[ValidationIssue]:
        """Get issues sorted by specified criteria."""
        if by == "severity":
            return sorted(self.issues, key=lambda i: -i.severity_score)
        elif by == "line":
            return sorted(self.issues, key=lambda i: i.line_number or 0)
        elif by == "category":
            return sorted(self.issues, key=lambda i: i.category)
        return self.issues


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

    def _create_issue(
        self,
        level: str,
        category: str,
        message: str,
        **kwargs
    ) -> ValidationIssue:
        """
        Helper method to create a ValidationIssue with defaults.

        Args:
            level: Issue level (error, warning, info, critical)
            category: Issue category
            message: Issue message
            **kwargs: Additional fields

        Returns:
            ValidationIssue instance
        """
        # Set source to validator type by default
        if "source" not in kwargs:
            kwargs["source"] = "rule_based"

        return ValidationIssue(
            level=level,
            category=category,
            message=message,
            **kwargs
        )
