# Implementation Plan: New Validator Agents

## Overview

This document provides ready-to-implement code for the missing validator agents.

---

## Agent 1: BaseValidatorAgent (Foundation)

**File**: `agents/validators/base_validator.py`

```python
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
            checkpoints=[]
        )
```

**File**: `agents/validators/__init__.py`

```python
# file: agents/validators/__init__.py
"""Validator agents package."""

from agents.validators.base_validator import (
    BaseValidatorAgent,
    ValidationIssue,
    ValidationResult
)

__all__ = [
    "BaseValidatorAgent",
    "ValidationIssue",
    "ValidationResult"
]
```

---

## Agent 2: SeoValidatorAgent (PRIORITY - Missing from UI)

**File**: `agents/validators/seo_validator.py`

```python
# file: agents/validators/seo_validator.py
"""
SEO Validator Agent - Validates SEO-friendly content structure.
Handles both SEO headings and heading sizes validation.
"""

from __future__ import annotations
import os
import re
import yaml
from typing import Dict, Any, List, Optional

from agents.validators.base_validator import (
    BaseValidatorAgent,
    ValidationIssue,
    ValidationResult
)
from core.logging import get_logger

logger = get_logger(__name__)


class SeoValidatorAgent(BaseValidatorAgent):
    """Validates SEO headings and heading sizes."""

    def __init__(self, agent_id: Optional[str] = None):
        super().__init__(agent_id or "seo_validator")
        self.seo_config = self._load_seo_config()
        self.heading_sizes_config = self._load_heading_sizes_config()

    def get_validation_type(self) -> str:
        return "seo"

    def _load_seo_config(self) -> Dict[str, Any]:
        """Load SEO configuration from config/seo.yaml."""
        config_path = os.path.join("config", "seo.yaml")
        default_config = {
            "seo": {
                "headings": {
                    "h1": {
                        "required": True,
                        "unique": True,
                        "min_length": 20,
                        "max_length": 70,
                        "recommended_min": 30,
                        "recommended_max": 60
                    },
                    "allow_empty_headings": False,
                    "enforce_hierarchy": True,
                    "max_depth": 6,
                    "h1_must_be_first": True
                },
                "strictness": {
                    "h1_violations": "error",
                    "hierarchy_skip": "error",
                    "empty_heading": "warning",
                    "h1_length": "warning"
                }
            }
        }

        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    loaded_config = yaml.safe_load(f)
                    if loaded_config and "seo" in loaded_config:
                        return loaded_config
            except Exception as e:
                logger.warning(f"Failed to load SEO config: {e}, using defaults")

        return default_config

    def _load_heading_sizes_config(self) -> Dict[str, Any]:
        """Load heading sizes configuration from config/heading_sizes.yaml."""
        config_path = os.path.join("config", "heading_sizes.yaml")
        default_config = {
            "heading_sizes": {
                "h1": {"min_length": 20, "max_length": 70, "recommended_min": 30, "recommended_max": 60},
                "h2": {"min_length": 10, "max_length": 100, "recommended_min": 20, "recommended_max": 80},
                "h3": {"min_length": 5, "max_length": 100, "recommended_min": 15, "recommended_max": 70},
                "h4": {"min_length": 5, "max_length": 80, "recommended_min": 10, "recommended_max": 60},
                "h5": {"min_length": 3, "max_length": 70, "recommended_min": 8, "recommended_max": 50},
                "h6": {"min_length": 3, "max_length": 60, "recommended_min": 8, "recommended_max": 40},
                "severity": {
                    "below_min": "error",
                    "above_max": "warning",
                    "below_recommended": "info",
                    "above_recommended": "info"
                }
            }
        }

        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    loaded_config = yaml.safe_load(f)
                    if loaded_config and "heading_sizes" in loaded_config:
                        return loaded_config
            except Exception as e:
                logger.warning(f"Failed to load heading sizes config: {e}, using defaults")

        return default_config

    async def validate(self, content: str, context: Dict[str, Any]) -> ValidationResult:
        """Validate SEO headings and/or heading sizes based on context."""
        validation_type = context.get("validation_type", "seo")

        if validation_type == "heading_sizes":
            return await self._validate_heading_sizes(content)
        else:
            return await self._validate_seo_headings(content)

    async def _validate_seo_headings(self, content: str) -> ValidationResult:
        """Validate SEO-friendly heading structure."""
        issues: List[ValidationIssue] = []
        auto_fixable = 0

        heading_config = self.seo_config["seo"]["headings"]
        strictness = self.seo_config["seo"]["strictness"]

        # Extract headings
        headings = self._extract_headings(content)

        if not headings:
            return ValidationResult(
                confidence=0.5,
                issues=[ValidationIssue(
                    level="warning",
                    category="no_headings",
                    message="No headings found in content",
                    suggestion="Add headings to structure your content"
                )],
                metrics={"headings_count": 0}
            )

        # Check H1 requirements
        h1_headings = [h for h in headings if h["level"] == 1]

        if heading_config["h1"]["required"] and not h1_headings:
            issues.append(ValidationIssue(
                level=strictness.get("h1_violations", "error"),
                category="seo_h1_missing",
                message="H1 heading is required for SEO",
                suggestion="Add an H1 heading at the beginning of the document"
            ))

        if heading_config["h1"]["unique"] and len(h1_headings) > 1:
            issues.append(ValidationIssue(
                level=strictness.get("h1_violations", "error"),
                category="seo_h1_not_unique",
                message=f"Found {len(h1_headings)} H1 headings, should be unique",
                suggestion="Keep only one H1 heading per document"
            ))

        # Check H1 must be first
        if heading_config.get("h1_must_be_first") and headings and headings[0]["level"] != 1:
            issues.append(ValidationIssue(
                level=strictness.get("h1_violations", "warning"),
                category="seo_h1_not_first",
                message="H1 heading should be the first heading",
                suggestion="Move H1 heading to the beginning"
            ))

        # Check heading hierarchy
        if heading_config.get("enforce_hierarchy"):
            for i in range(1, len(headings)):
                prev_level = headings[i-1]["level"]
                curr_level = headings[i]["level"]

                if curr_level > prev_level + 1:
                    issues.append(ValidationIssue(
                        level=strictness.get("hierarchy_skip", "error"),
                        category="seo_hierarchy_skip",
                        message=f"Heading hierarchy skip: H{prev_level} → H{curr_level} (line {headings[i]['line']})",
                        line_number=headings[i]['line'],
                        suggestion=f"Use H{prev_level + 1} instead of H{curr_level}"
                    ))

        # Check empty headings
        if not heading_config.get("allow_empty_headings"):
            for h in headings:
                if not h["text"].strip():
                    issues.append(ValidationIssue(
                        level=strictness.get("empty_heading", "warning"),
                        category="seo_empty_heading",
                        message=f"Empty H{h['level']} heading at line {h['line']}",
                        line_number=h['line'],
                        suggestion="Add descriptive text to the heading"
                    ))

        # Check H1 length
        for h1 in h1_headings:
            h1_len = len(h1["text"])
            h1_config = heading_config["h1"]

            if h1_len < h1_config["min_length"]:
                issues.append(ValidationIssue(
                    level=strictness.get("h1_length", "warning"),
                    category="seo_h1_too_short",
                    message=f"H1 is too short ({h1_len} chars, minimum: {h1_config['min_length']})",
                    line_number=h1['line'],
                    suggestion=f"Add at least {h1_config['min_length'] - h1_len} more characters"
                ))
            elif h1_len > h1_config["max_length"]:
                issues.append(ValidationIssue(
                    level=strictness.get("h1_length", "warning"),
                    category="seo_h1_too_long",
                    message=f"H1 is too long ({h1_len} chars, maximum: {h1_config['max_length']})",
                    line_number=h1['line'],
                    suggestion=f"Shorten by at least {h1_len - h1_config['max_length']} characters"
                ))

        confidence = max(0.3, 1.0 - (len(issues) * 0.1))

        return ValidationResult(
            confidence=confidence,
            issues=issues,
            auto_fixable_count=auto_fixable,
            metrics={
                "headings_count": len(headings),
                "h1_count": len(h1_headings),
                "issues_count": len(issues)
            }
        )

    async def _validate_heading_sizes(self, content: str) -> ValidationResult:
        """Validate heading text lengths."""
        issues: List[ValidationIssue] = []
        auto_fixable = 0

        size_config = self.heading_sizes_config["heading_sizes"]
        severity = size_config.get("severity", {})

        headings = self._extract_headings(content)

        if not headings:
            return ValidationResult(
                confidence=1.0,
                metrics={"headings_count": 0}
            )

        for h in headings:
            h_level = f"h{h['level']}"
            if h_level not in size_config:
                continue

            limits = size_config[h_level]
            text_len = len(h["text"])

            # Check minimum
            if text_len < limits["min_length"]:
                issues.append(ValidationIssue(
                    level=severity.get("below_min", "error"),
                    category="heading_too_short",
                    message=f"H{h['level']} heading is only {text_len} characters (minimum: {limits['min_length']})",
                    line_number=h["line"],
                    suggestion=f"Add at least {limits['min_length'] - text_len} more characters to meet minimum length"
                ))

            # Check maximum
            elif text_len > limits["max_length"]:
                issues.append(ValidationIssue(
                    level=severity.get("above_max", "warning"),
                    category="heading_too_long",
                    message=f"H{h['level']} heading is {text_len} characters (maximum: {limits['max_length']})",
                    line_number=h["line"],
                    suggestion=f"Shorten by at least {text_len - limits['max_length']} characters"
                ))

            # Check recommended range
            elif text_len < limits.get("recommended_min", 0):
                issues.append(ValidationIssue(
                    level=severity.get("below_recommended", "info"),
                    category="heading_below_recommended",
                    message=f"H{h['level']} heading is {text_len} characters (recommended: {limits['recommended_min']}+)",
                    line_number=h["line"],
                    suggestion=f"Consider adding more context"
                ))

            elif text_len > limits.get("recommended_max", 9999):
                issues.append(ValidationIssue(
                    level=severity.get("above_recommended", "info"),
                    category="heading_above_recommended",
                    message=f"H{h['level']} heading is {text_len} characters (recommended: <{limits['recommended_max']})",
                    line_number=h["line"],
                    suggestion=f"Consider making more concise"
                ))

        confidence = max(0.5, 1.0 - (len([i for i in issues if i.level == "error"]) * 0.2))

        return ValidationResult(
            confidence=confidence,
            issues=issues,
            auto_fixable_count=auto_fixable,
            metrics={
                "headings_count": len(headings),
                "issues_count": len(issues)
            }
        )

    def _extract_headings(self, content: str) -> List[Dict[str, Any]]:
        """Extract headings from markdown content."""
        headings = []
        lines = content.split('\n')

        for i, line in enumerate(lines):
            # Match markdown headings: # Heading, ## Heading, etc.
            match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                headings.append({
                    "level": level,
                    "text": text,
                    "line": i + 1
                })

        return headings
```

---

## Agent 3: YamlValidatorAgent (Example)

**File**: `agents/validators/yaml_validator.py`

```python
# file: agents/validators/yaml_validator.py
"""
YAML Validator Agent - Validates YAML frontmatter.
"""

from __future__ import annotations
import yaml
import frontmatter
from typing import Dict, Any, List, Optional

from agents.validators.base_validator import (
    BaseValidatorAgent,
    ValidationIssue,
    ValidationResult
)
from core.logging import get_logger

logger = get_logger(__name__)


class YamlValidatorAgent(BaseValidatorAgent):
    """Validates YAML frontmatter in markdown files."""

    def __init__(self, agent_id: Optional[str] = None):
        super().__init__(agent_id or "yaml_validator")

    def get_validation_type(self) -> str:
        return "yaml"

    async def validate(self, content: str, context: Dict[str, Any]) -> ValidationResult:
        """Validate YAML frontmatter."""
        issues: List[ValidationIssue] = []
        auto_fixable = 0

        # Extract YAML frontmatter
        try:
            post = frontmatter.loads(content)
            metadata = post.metadata
        except Exception as e:
            return ValidationResult(
                confidence=0.0,
                issues=[ValidationIssue(
                    level="error",
                    category="yaml_parse_error",
                    message=f"Failed to parse YAML frontmatter: {str(e)}",
                    suggestion="Check YAML syntax"
                )],
                metrics={"yaml_valid": False}
            )

        # Validate required fields
        required_fields = ["title"]  # Could be from config
        for field in required_fields:
            if field not in metadata or not metadata[field]:
                issues.append(ValidationIssue(
                    level="error",
                    category="yaml_missing_required",
                    message=f"Required field '{field}' is missing",
                    suggestion=f"Add '{field}' to YAML frontmatter"
                ))

        # Validate field types
        if "title" in metadata and not isinstance(metadata["title"], str):
            issues.append(ValidationIssue(
                level="error",
                category="yaml_invalid_type",
                message="Field 'title' must be a string",
                suggestion="Wrap title value in quotes"
            ))

        confidence = max(0.5, 1.0 - (len(issues) * 0.15))

        return ValidationResult(
            confidence=confidence,
            issues=issues,
            auto_fixable_count=auto_fixable,
            metrics={
                "yaml_valid": True,
                "fields_checked": len(metadata),
                "issues_count": len(issues)
            }
        )
```

---

## Registration in api/server.py

**Update**: `api/server.py` (startup section)

```python
# api/server.py
from agents.validators.seo_validator import SeoValidatorAgent
from agents.validators.yaml_validator import YamlValidatorAgent

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan handler."""
    try:
        logger.info("Starting TBCV API server...")
        setup_logging()

        # ... existing code ...

        # Register validators
        if getattr(settings.validators.seo, "enabled", True):
            seo_validator = SeoValidatorAgent("seo_validator")
            agent_registry.register_agent(seo_validator)
            logger.info("SEO validator registered")

        if getattr(settings.validators.yaml, "enabled", True):
            yaml_validator = YamlValidatorAgent("yaml_validator")
            agent_registry.register_agent(yaml_validator)
            logger.info("YAML validator registered")

        # ... rest of startup code ...

        yield

    finally:
        # ... shutdown code ...
```

---

## Updated config/main.yaml

```yaml
agents:
  fuzzy_detector:
    enabled: true  # FIX: Enable fuzzy detector

  llm_validator:
    enabled: false  # Requires Ollama

validators:
  yaml:
    enabled: true

  markdown:
    enabled: true

  code:
    enabled: true

  links:
    enabled: true

  structure:
    enabled: true

  truth:
    enabled: true

  seo:
    enabled: true
    heading_sizes_enabled: true
```

---

## New API Endpoint: /api/validators/available

```python
# api/server.py

@app.get("/api/validators/available")
async def get_available_validators():
    """Get list of available validator agents."""
    validator_map = {
        "yaml_validator": {"id": "yaml", "label": "YAML", "description": "Validate YAML frontmatter", "category": "standard"},
        "markdown_validator": {"id": "markdown", "label": "Markdown", "description": "Validate Markdown syntax", "category": "standard"},
        "code_validator": {"id": "code", "label": "Code", "description": "Validate code blocks", "category": "standard"},
        "link_validator": {"id": "links", "label": "Links", "description": "Check link validity", "category": "standard"},
        "structure_validator": {"id": "structure", "label": "Structure", "description": "Validate document structure", "category": "standard"},
        "truth_validator": {"id": "Truth", "label": "Truth", "description": "Validate against truth data", "category": "standard"},
        "fuzzy_detector": {"id": "FuzzyLogic", "label": "Fuzzy Logic", "description": "Fuzzy plugin detection", "category": "standard"},
        "seo_validator": [
            {"id": "seo", "label": "SEO Headings", "description": "Validate SEO-friendly heading structure", "category": "advanced"},
            {"id": "heading_sizes", "label": "Heading Sizes", "description": "Validate heading length limits", "category": "advanced"}
        ],
        "llm_validator": {"id": "llm", "label": "LLM Analysis", "description": "Semantic validation via LLM", "category": "advanced"}
    }

    validators = []

    for agent_id, info in validator_map.items():
        agent = agent_registry.get_agent(agent_id)
        available = agent is not None

        if isinstance(info, list):
            for v in info:
                validators.append({
                    **v,
                    "available": available,
                    "enabled_by_default": available
                })
        else:
            validators.append({
                **info,
                "available": available,
                "enabled_by_default": available and info.get("category") == "standard"
            })

    return {"validators": validators}
```

---

## Summary

### Immediate Actions (Today):

1. **Create `agents/validators/` directory**
2. **Implement `BaseValidatorAgent`** (foundation)
3. **Implement `SeoValidatorAgent`** (most impactful - missing from UI)
4. **Register agents in server.py**
5. **Add config section for validators**
6. **Create `/api/validators/available` endpoint**
7. **Enable fuzzy_detector** in config

### Testing:

```bash
# Test SEO validation
curl -X POST http://localhost:8000/api/validate \
  -H "Content-Type: application/json" \
  -d '{
    "content": "## Test\nNo H1 heading",
    "validation_types": ["seo"]
  }'

# Should return error about missing H1

# Test heading sizes
curl -X POST http://localhost:8000/api/validate \
  -H "Content-Type: application/json" \
  -d '{
    "content": "# H1\nContent",
    "validation_types": ["heading_sizes"]
  }'

# Should return error about H1 being too short (3 chars vs 20 min)
```

### Next Validators to Implement:

1. MarkdownValidatorAgent
2. CodeValidatorAgent
3. LinkValidatorAgent
4. StructureValidatorAgent
5. TruthValidatorAgent

Ready to implement?
