# file: tbcv\agents\content_validator.py
"""
ContentValidatorAgent - Generic quality and structure validation for content.
Rebased fixes:
- Implement missing public handlers used by message registrations:
  handle_validate_yaml, handle_validate_markdown, handle_validate_code,
  handle_validate_links, handle_validate_structure.
- Normalize rule_manager import to package shim (tbcv.rule_manager).
- Avoid logger.error(..., error=...) patterns that can break Python logging.
- Add checkpoints=[] to AgentContract to satisfy base contract signature.
"""

from __future__ import annotations

import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

try:
    from agents.base import BaseAgent, AgentContract, AgentCapability, agent_registry
    from core.logging import PerformanceLogger
    from core.database import db_manager
    from core.rule_manager import rule_manager  # normalized import
except ImportError:
    from agents.base import BaseAgent, AgentContract, AgentCapability, agent_registry
    from core.logging import PerformanceLogger
    from core.database import db_manager
    from core.rule_manager import rule_manager  # normalized import

# Optional deps
try:
    import bleach
except ImportError:
    bleach = None

try:
    import frontmatter
except ImportError:
    frontmatter = None

@dataclass
class ValidationIssue:
    level: str
    category: str
    message: str
    line_number: Optional[int] = None
    column: Optional[int] = None
    suggestion: Optional[str] = None
    source: str = "validator"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level,
            "category": self.category,
            "message": self.message,
            "line_number": self.line_number,
            "column": self.column,
            "suggestion": self.suggestion,
            "source": self.source
        }

@dataclass
class ValidationResult:
    confidence: float
    issues: List[ValidationIssue]
    auto_fixable_count: int
    metrics: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "confidence": self.confidence,
            "issues": [i.to_dict() for i in self.issues],
            "auto_fixable_count": self.auto_fixable_count,
            "metrics": self.metrics,
        }

class ContentValidatorAgent(BaseAgent):
    def __init__(self, agent_id: Optional[str] = None):
        self.validation_rules: Dict[str, Any] = {}
        self.allowed_html_tags = ['code', 'pre', 'em', 'strong', 'a', 'img', 'br', 'p']
        self.shortcode_pattern = re.compile(r'\{\{<\s*(\w+).*?\>\}\}', re.DOTALL)
        self.link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
        super().__init__(agent_id)

    def get_contract(self) -> AgentContract:
        return AgentContract(
            agent_id=self.agent_id,
            name="ContentValidatorAgent",
            version="1.0.0",
            capabilities=[
                AgentCapability(
                    name="validate_content",
                    description="Generic content validation using truths and rules",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "content": {"type": "string"},
                            "file_path": {"type": "string"},
                            "family": {"type": "string", "default": "words"},
                            "validation_types": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["content"]
                    },
                    output_schema={"type": "object"},
                    side_effects=["read", "cache", "db_write", "network"]
                )
            ],
            max_runtime_s=120,
            confidence_threshold=0.6,
            side_effects=["read", "cache", "db_write", "network"],
            dependencies=["truth_manager", "fuzzy_detector"],
            checkpoints=[]  # <-- required by Base.AgentContract
        )

    def _register_message_handlers(self) -> None:
        self.register_handler("ping", self.handle_ping)
        self.register_handler("get_status", self.handle_get_status)
        self.register_handler("get_contract", self.get_contract)
        self.register_handler("validate_content", self.handle_validate_content)
        # public per-scope handlers required by API and tests
        self.register_handler("validate_yaml", self.handle_validate_yaml)
        self.register_handler("validate_markdown", self.handle_validate_markdown)
        self.register_handler("validate_code", self.handle_validate_code)
        self.register_handler("validate_links", self.handle_validate_links)
        self.register_handler("validate_structure", self.handle_validate_structure)

    def _validate_configuration(self) -> None:
        config = self.settings.content_validator
        self._setup_validation_rules()
        if getattr(config, "html_sanitization", False) and bleach is not None:
            self.allowed_html_tags = getattr(config, "allowed_html_tags", self.allowed_html_tags)

    def _setup_validation_rules(self) -> None:
        self.validation_rules = {
            "title": {"min_length": 10, "max_length": 80},
            "description": {"min_length": 50, "max_length": 300, "required_sentences": 2},
            "structure": {"min_introduction_length": 100, "min_section_length": 50, "max_heading_depth": 4},
        }

    # ----------------------
    # Composite entry point
    # ----------------------
    async def handle_validate_content(self, params: Dict[str, Any]) -> Dict[str, Any]:
        with PerformanceLogger(self.logger, "validate_content"):
            content = params.get("content", "")
            file_path = params.get("file_path", "unknown")
            family = params.get("family", "words")
            validation_types = params.get("validation_types", ["yaml", "markdown", "code", "links", "structure"])

            all_issues: List[ValidationIssue] = []
            all_metrics: Dict[str, Any] = {
                "file_path": file_path,
                "content_length": len(content),
                "family": family
            }
            total_auto_fixable = 0

            truth_context = await self._load_truth_context(family)
            rule_context = await self._load_rule_context(family)
            plugin_context = await self._get_plugin_context(content, family)

            for vt in validation_types:
                try:
                    if vt == "yaml":
                        result = await self._validate_yaml_with_truths_and_rules(content, family, truth_context, rule_context)
                    elif vt == "markdown":
                        result = await self._validate_markdown_with_rules(content, plugin_context, family, rule_context)
                    elif vt == "code":
                        result = await self._validate_code_with_patterns(content, plugin_context, family, rule_context)
                    elif vt == "links":
                        result = await self._validate_links(content)
                    elif vt == "structure":
                        result = await self._validate_structure(content)
                    elif vt == "llm":
                        result = await self._validate_with_llm(content, plugin_context, rule_context, truth_context)
                    else:
                        self.logger.warning("Unknown validation type %s", vt)
                        continue

                    all_issues.extend(result.issues)
                    all_metrics[f"{vt}_metrics"] = result.metrics
                    total_auto_fixable += result.auto_fixable_count

                except Exception:
                    self.logger.exception("Validation type failed")
                    all_issues.append(ValidationIssue(
                        level="error", category="system",
                        message=f"Validation failed for {vt}"
                    ))

            overall_confidence = self._calculate_content_confidence(all_issues, all_metrics)

            await self._store_validation_result(
                file_path, len(content), validation_types,
                all_issues, overall_confidence, all_metrics, family
            )

            return {
                "confidence": overall_confidence,
                "issues": [issue.to_dict() for issue in all_issues],
                "auto_fixable_count": total_auto_fixable,
                "metrics": all_metrics,
                "file_path": file_path,
                "family": family
            }

    # ----------------------
    # Public per-scope APIs
    # ----------------------
    async def handle_validate_yaml(self, params: Dict[str, Any]) -> Dict[str, Any]:
        content = params.get("content", "")
        file_path = params.get("file_path", "unknown")
        family = params.get("family", "words")
        truth_context = await self._load_truth_context(family)
        rule_context = await self._load_rule_context(family)
        result = await self._validate_yaml_with_truths_and_rules(content, family, truth_context, rule_context)
        confidence = self._calculate_content_confidence(result.issues, result.metrics)
        await self._store_validation_result(file_path, len(content), ["yaml"], result.issues, confidence, result.metrics, family)
        return {
            "confidence": confidence,
            "issues": [i.to_dict() for i in result.issues],
            "auto_fixable_count": result.auto_fixable_count,
            "metrics": result.metrics,
            "file_path": file_path,
            "family": family
        }

    async def handle_validate_markdown(self, params: Dict[str, Any]) -> Dict[str, Any]:
        content = params.get("content", "")
        file_path = params.get("file_path", "unknown")
        family = params.get("family", "words")
        rule_context = await self._load_rule_context(family)
        plugin_context = await self._get_plugin_context(content, family)
        result = await self._validate_markdown_with_rules(content, plugin_context, family, rule_context)
        confidence = self._calculate_content_confidence(result.issues, result.metrics)
        await self._store_validation_result(file_path, len(content), ["markdown"], result.issues, confidence, result.metrics, family)
        return {
            "confidence": confidence,
            "issues": [i.to_dict() for i in result.issues],
            "auto_fixable_count": result.auto_fixable_count,
            "metrics": result.metrics,
            "file_path": file_path,
            "family": family
        }

    async def handle_validate_code(self, params: Dict[str, Any]) -> Dict[str, Any]:
        content = params.get("content", "")
        file_path = params.get("file_path", "unknown")
        family = params.get("family", "words")
        rule_context = await self._load_rule_context(family)
        plugin_context = await self._get_plugin_context(content, family)
        result = await self._validate_code_with_patterns(content, plugin_context, family, rule_context)
        confidence = self._calculate_content_confidence(result.issues, result.metrics)
        await self._store_validation_result(file_path, len(content), ["code"], result.issues, confidence, result.metrics, family)
        return {
            "confidence": confidence,
            "issues": [i.to_dict() for i in result.issues],
            "auto_fixable_count": result.auto_fixable_count,
            "metrics": result.metrics,
            "file_path": file_path,
            "family": family
        }

    async def handle_validate_links(self, params: Dict[str, Any]) -> Dict[str, Any]:
        content = params.get("content", "")
        file_path = params.get("file_path", "unknown")
        family = params.get("family", "words")
        result = await self._validate_links(content)
        confidence = self._calculate_content_confidence(result.issues, result.metrics)
        await self._store_validation_result(file_path, len(content), ["links"], result.issues, confidence, result.metrics, family)
        return {
            "confidence": confidence,
            "issues": [i.to_dict() for i in result.issues],
            "auto_fixable_count": result.auto_fixable_count,
            "metrics": result.metrics,
            "file_path": file_path,
            "family": family
        }

    async def handle_validate_structure(self, params: Dict[str, Any]) -> Dict[str, Any]:
        content = params.get("content", "")
        file_path = params.get("file_path", "unknown")
        family = params.get("family", "words")
        result = await self._validate_structure(content)
        confidence = self._calculate_content_confidence(result.issues, result.metrics)
        await self._store_validation_result(file_path, len(content), ["structure"], result.issues, confidence, result.metrics, family)
        return {
            "confidence": confidence,
            "issues": [i.to_dict() for i in result.issues],
            "auto_fixable_count": result.auto_fixable_count,
            "metrics": result.metrics,
            "file_path": file_path,
            "family": family
        }

    # ----------------------
    # Context loaders (stubs)
    # ----------------------
    async def _load_truth_context(self, family: str) -> Dict[str, Any]:
        try:
            truth_manager = agent_registry.get_agent("truth_manager")
            if truth_manager:
                load_result = await truth_manager.process_request("load_truth_data", {"family": family})
                search_result = await truth_manager.process_request("search_plugins", {"query": "", "family": family})
                return {
                    "loaded": load_result.get("success", False),
                    "plugins_count": load_result.get("plugins_count", 0),
                    "plugins": search_result.get("results", []),
                    "version_hash": load_result.get("version_hash", "")
                }
        except Exception as e:
            self.logger.warning(f"Failed to load truth context: {e}")
        return {"loaded": False, "plugins_count": 0, "plugins": []}

    async def _load_rule_context(self, family: str) -> Dict[str, Any]:
        try:
            family_rules = rule_manager.get_family_rules(family)
            patterns_count = sum(len(patterns) for patterns in getattr(family_rules, "api_patterns", {}).values())
            return {
                "loaded": True,
                "family_rules": family_rules,
                "patterns_count": patterns_count,
                "api_patterns": getattr(family_rules, "api_patterns", {}),
                "plugin_aliases": getattr(family_rules, "plugin_aliases", {}),
                "validation_requirements": getattr(family_rules, "validation_requirements", {}),
                "non_editable_fields": getattr(family_rules, "non_editable_yaml_fields", {}),
                "code_quality_rules": getattr(family_rules, "code_quality_rules", {})
            }
        except Exception as e:
            self.logger.warning(f"Failed to load rule context: {e}")
            return {"loaded": False, "patterns_count": 0}

    async def _get_plugin_context(self, content: str, family: str) -> Dict[str, Any]:
        try:
            fuzzy_detector = agent_registry.get_agent("fuzzy_detector")
            if fuzzy_detector:
                result = await fuzzy_detector.process_request("detect_plugins", {
                    "text": content,
                    "family": family,
                    "confidence_threshold": 0.6
                })
                return {"plugins": result.get("detections", []), "confidence": result.get("confidence", 0.0)}
        except Exception as e:
            self.logger.warning(f"Failed to get plugin context: {e}")
        return {"plugins": [], "confidence": 0.0}

    # ----------------------
    # Stub validators (safe)
    # ----------------------
    async def _validate_yaml_with_truths_and_rules(self, content: str, family: str, truth_context: Dict, rule_context: Dict) -> ValidationResult:
        """Validate YAML front-matter against truth and rule constraints."""
        issues: List[ValidationIssue] = []
        auto_fixable = 0
        
        # Parse front-matter
        if not frontmatter:
            issues.append(ValidationIssue(
                level="warning",
                category="yaml_parser_unavailable",
                message="frontmatter library not available for YAML validation",
                suggestion="Install python-frontmatter: pip install python-frontmatter"
            ))
            return ValidationResult(confidence=0.5, issues=issues, auto_fixable_count=0, metrics={"yaml_valid": False})
        
        try:
            post = frontmatter.loads(content)
            yaml_data = post.metadata
        except Exception as e:
            issues.append(ValidationIssue(
                level="error",
                category="yaml_parse_error",
                message=f"Failed to parse YAML front-matter: {str(e)}",
                line_number=1,
                suggestion="Check YAML syntax: ensure proper indentation, no tabs, balanced quotes"
            ))
            return ValidationResult(confidence=0.0, issues=issues, auto_fixable_count=0, metrics={"yaml_valid": False, "parse_error": str(e)})
        
        # Get validation rules from rule_context
        family_rules = rule_context.get("family_rules", {})
        allowed_fields = family_rules.get("allowed_yaml_fields", [])
        required_fields = family_rules.get("required_yaml_fields", [])
        field_types = family_rules.get("yaml_field_types", {})
        non_editable = rule_context.get("non_editable_fields", [])
        
        # Get truth constraints
        truth_data = truth_context.get("truth_data", {})
        valid_categories = truth_data.get("valid_categories", [])
        valid_tags = truth_data.get("valid_tags", [])
        
        # Check for unknown fields
        if allowed_fields:
            for key in yaml_data.keys():
                if key not in allowed_fields:
                    issues.append(ValidationIssue(
                        level="warning",
                        category="unknown_yaml_field",
                        message=f"Field '{key}' is not in the allowed fields list",
                        suggestion=f"Remove '{key}' or add it to allowed_yaml_fields in rules/{family}.json"
                    ))
        
        # Check for missing required fields
        for req_field in required_fields:
            if req_field not in yaml_data:
                issues.append(ValidationIssue(
                    level="error",
                    category="missing_required_field",
                    message=f"Required field '{req_field}' is missing from front-matter",
                    suggestion=f"Add '{req_field}: <value>' to the YAML front-matter",
                    source="rule"
                ))
            elif not yaml_data[req_field]:
                issues.append(ValidationIssue(
                    level="error",
                    category="empty_required_field",
                    message=f"Required field '{req_field}' is empty",
                    suggestion=f"Provide a value for '{req_field}'",
                    source="rule"
                ))
        
        # Check field types
        for field_name, expected_type in field_types.items():
            if field_name in yaml_data:
                value = yaml_data[field_name]
                if expected_type == "string" and not isinstance(value, str):
                    issues.append(ValidationIssue(
                        level="error",
                        category="field_type_mismatch",
                        message=f"Field '{field_name}' should be a string, got {type(value).__name__}",
                        suggestion=f"Change '{field_name}' to a quoted string value"
                    ))
                elif expected_type == "array" and not isinstance(value, list):
                    issues.append(ValidationIssue(
                        level="error",
                        category="field_type_mismatch",
                        message=f"Field '{field_name}' should be an array, got {type(value).__name__}",
                        suggestion=f"Change '{field_name}' to a YAML array format: [item1, item2]"
                    ))
                elif expected_type == "date":
                    # Basic date format check
                    if isinstance(value, str) and not re.match(r'\d{4}-\d{2}-\d{2}', value):
                        issues.append(ValidationIssue(
                            level="warning",
                            category="invalid_date_format",
                            message=f"Field '{field_name}' should be in YYYY-MM-DD format",
                            suggestion=f"Use ISO date format: YYYY-MM-DD"
                        ))
        
        # Check category constraints (if applicable)
        if "category" in yaml_data and valid_categories:
            if yaml_data["category"] not in valid_categories:
                issues.append(ValidationIssue(
                    level="warning",
                    category="invalid_category",
                    message=f"Category '{yaml_data['category']}' is not in the valid categories list",
                    suggestion=f"Use one of: {', '.join(valid_categories[:5])}",
                    source="truth"
                ))
                auto_fixable += 1
        
        # Check tags constraints (if applicable)
        if "tags" in yaml_data and valid_tags and isinstance(yaml_data["tags"], list):
            for tag in yaml_data["tags"]:
                if tag not in valid_tags:
                    issues.append(ValidationIssue(
                        level="info",
                        category="unknown_tag",
                        message=f"Tag '{tag}' is not in the known tags list",
                        suggestion=f"Consider using a tag from the standard list",
                        source="truth"
                    ))
                    auto_fixable += 1
        
        # Calculate confidence
        confidence = 1.0 if not issues else max(0.3, 1.0 - (len([i for i in issues if i.level == "error"]) * 0.2))
        
        return ValidationResult(
            confidence=confidence,
            issues=issues,
            auto_fixable_count=auto_fixable,
            metrics={
                "yaml_valid": len([i for i in issues if i.level == "error"]) == 0,
                "fields_checked": len(yaml_data),
                "required_fields_count": len(required_fields),
                "issues_count": len(issues)
            }
        )

    async def _validate_markdown_with_rules(self, content: str, plugin_context: Dict, family: str, rule_context: Dict) -> ValidationResult:
        """Validate Markdown structure and formatting."""
        issues: List[ValidationIssue] = []
        auto_fixable = 0
        
        lines = content.split('\n')
        
        # Extract headings
        headings = []
        for i, line in enumerate(lines, 1):
            if line.strip().startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                text = line.lstrip('#').strip()
                headings.append({"level": level, "text": text, "line": i})
        
        # Check for skipped heading levels
        for i in range(1, len(headings)):
            prev_level = headings[i-1]["level"]
            curr_level = headings[i]["level"]
            if curr_level > prev_level + 1:
                issues.append(ValidationIssue(
                    level="warning",
                    category="skipped_heading_level",
                    message=f"Heading level jumped from {prev_level} to {curr_level} at line {headings[i]['line']}",
                    line_number=headings[i]["line"],
                    suggestion=f"Use heading level {prev_level + 1} instead of {curr_level}"
                ))
                auto_fixable += 1
        
        # Check for duplicate headings
        heading_texts = [h["text"].lower() for h in headings]
        seen = set()
        for h in headings:
            if h["text"].lower() in seen:
                issues.append(ValidationIssue(
                    level="info",
                    category="duplicate_heading",
                    message=f"Duplicate heading '{h['text']}' at line {h['line']}",
                    line_number=h["line"],
                    suggestion="Consider using unique heading text for better navigation"
                ))
            seen.add(h["text"].lower())
        
        # Check code block balance
        code_block_delimiters = [i for i, line in enumerate(lines, 1) if line.strip().startswith('```')]
        if len(code_block_delimiters) % 2 != 0:
            issues.append(ValidationIssue(
                level="error",
                category="unbalanced_code_blocks",
                message="Unbalanced code blocks (odd number of ``` delimiters)",
                line_number=code_block_delimiters[-1] if code_block_delimiters else None,
                suggestion="Ensure every ``` opening has a matching ``` closing"
            ))
        
        # Check for broken shortcodes
        shortcodes = self.shortcode_pattern.findall(content)
        for sc in shortcodes:
            # Basic shortcode validation
            if not sc.isalnum() and sc not in ['note', 'warning', 'tip', 'info']:
                issues.append(ValidationIssue(
                    level="warning",
                    category="unknown_shortcode",
                    message=f"Unknown shortcode: {{{{< {sc} >}}}}",
                    suggestion="Verify shortcode name against available shortcodes"
                ))
        
        # Check minimum content length (from rules)
        structure_rules = self.validation_rules.get("structure", {})
        min_intro_length = structure_rules.get("min_introduction_length", 100)
        
        # Find content before first heading or between YAML and first heading
        if '---' in content:
            parts = content.split('---', 2)
            if len(parts) >= 3:
                intro_content = parts[2].split('#', 1)[0] if '#' in parts[2] else parts[2]
            else:
                intro_content = ""
        else:
            intro_content = content.split('#', 1)[0] if '#' in content else content
        
        intro_length = len(intro_content.strip())
        if intro_length < min_intro_length:
            issues.append(ValidationIssue(
                level="info",
                category="short_introduction",
                message=f"Introduction is only {intro_length} characters (minimum {min_intro_length})",
                suggestion=f"Add at least {min_intro_length - intro_length} more characters to the introduction"
            ))
            auto_fixable += 1
        
        confidence = 1.0 if not issues else max(0.5, 1.0 - (len([i for i in issues if i.level == "error"]) * 0.15))
        
        return ValidationResult(
            confidence=confidence,
            issues=issues,
            auto_fixable_count=auto_fixable,
            metrics={
                "markdown_valid": len([i for i in issues if i.level == "error"]) == 0,
                "headings_count": len(headings),
                "code_blocks_count": len(code_block_delimiters) // 2,
                "introduction_length": intro_length
            }
        )

    async def _validate_code_with_patterns(self, content: str, plugin_context: Dict, family: str, rule_context: Dict) -> ValidationResult:
        """Validate code snippets and API patterns."""
        issues: List[ValidationIssue] = []
        auto_fixable = 0
        
        # Extract code blocks
        code_blocks = re.findall(r'```(\w+)?\n(.*?)```', content, re.DOTALL)
        
        # Get API patterns from rules
        api_patterns = rule_context.get("api_patterns", {})
        plugin_aliases = rule_context.get("plugin_aliases", {})
        
        # Check for common code issues
        for lang, code in code_blocks:
            # Check for incomplete code (very short blocks)
            if len(code.strip()) < 10:
                issues.append(ValidationIssue(
                    level="info",
                    category="short_code_block",
                    message=f"Code block is very short ({len(code.strip())} chars)",
                    suggestion="Consider adding more context or removing if it's not useful"
                ))
            
            # Check for missing language specifier
            if not lang:
                issues.append(ValidationIssue(
                    level="info",
                    category="missing_language_specifier",
                    message="Code block is missing language specifier",
                    suggestion="Add language after opening ```, e.g., ```python or ```java"
                ))
                auto_fixable += 1
        
        # Check for plugin mentions in text but not in code
        plugins_in_context = plugin_context.get("plugins", [])
        for plugin in plugins_in_context:
            plugin_name = plugin.get("plugin_name", "")
            plugin_id = plugin.get("plugin_id", "")
            
            # Check if plugin is mentioned but no code example provided
            if plugin_name.lower() in content.lower() and len(code_blocks) == 0:
                issues.append(ValidationIssue(
                    level="info",
                    category="missing_code_example",
                    message=f"Plugin '{plugin_name}' is mentioned but no code examples provided",
                    suggestion=f"Add a code example showing how to use {plugin_name}"
                ))
        
        confidence = 1.0 if not issues else max(0.6, 1.0 - (len(issues) * 0.1))
        
        return ValidationResult(
            confidence=confidence,
            issues=issues,
            auto_fixable_count=auto_fixable,
            metrics={
                "code_valid": len([i for i in issues if i.level == "error"]) == 0,
                "code_blocks_count": len(code_blocks),
                "languages_used": list(set([lang for lang, _ in code_blocks if lang]))
            }
        )

    async def _validate_links(self, content: str) -> ValidationResult:
        """Validate markdown links."""
        issues: List[ValidationIssue] = []
        auto_fixable = 0
        
        # Extract all markdown links
        links = self.link_pattern.findall(content)
        
        for link_text, link_url in links:
            # Check for empty links
            if not link_url or link_url.strip() == "":
                issues.append(ValidationIssue(
                    level="error",
                    category="empty_link",
                    message=f"Link '{link_text}' has an empty URL",
                    suggestion=f"Provide a valid URL for the link '{link_text}'"
                ))
            
            # Check for placeholder links
            elif link_url in ["#", "TODO", "FIXME", "..."]:
                issues.append(ValidationIssue(
                    level="warning",
                    category="placeholder_link",
                    message=f"Link '{link_text}' points to placeholder '{link_url}'",
                    suggestion=f"Replace placeholder with actual URL"
                ))
                auto_fixable += 1
            
            # Check for broken relative links (basic check)
            elif link_url.startswith("./") or link_url.startswith("../"):
                issues.append(ValidationIssue(
                    level="info",
                    category="relative_link",
                    message=f"Link '{link_text}' uses relative path: {link_url}",
                    suggestion="Verify the relative path is correct for your deployment structure"
                ))
            
            # Check for suspicious patterns
            elif "localhost" in link_url or "127.0.0.1" in link_url:
                issues.append(ValidationIssue(
                    level="warning",
                    category="localhost_link",
                    message=f"Link '{link_text}' points to localhost: {link_url}",
                    suggestion="Replace with production URL before publishing"
                ))
                auto_fixable += 1
        
        confidence = 1.0 if not issues else max(0.6, 1.0 - (len([i for i in issues if i.level == "error"]) * 0.15))
        
        return ValidationResult(
            confidence=confidence,
            issues=issues,
            auto_fixable_count=auto_fixable,
            metrics={
                "links_valid": len([i for i in issues if i.level == "error"]) == 0,
                "links_count": len(links),
                "placeholder_count": len([i for i in issues if i.category == "placeholder_link"])
            }
        )

    async def _validate_structure(self, content: str) -> ValidationResult:
        """Validate content structure and organization."""
        issues: List[ValidationIssue] = []
        auto_fixable = 0
        
        structure_rules = self.validation_rules.get("structure", {})
        min_section_length = structure_rules.get("min_section_length", 50)
        max_heading_depth = structure_rules.get("max_heading_depth", 4)
        
        lines = content.split('\n')
        
        # Extract headings with their content
        headings = []
        for i, line in enumerate(lines):
            if line.strip().startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                text = line.lstrip('#').strip()
                headings.append({"level": level, "text": text, "line_index": i})
        
        # Check heading depth
        for h in headings:
            if h["level"] > max_heading_depth:
                issues.append(ValidationIssue(
                    level="warning",
                    category="excessive_heading_depth",
                    message=f"Heading '{h['text']}' uses level {h['level']} (max recommended: {max_heading_depth})",
                    line_number=h["line_index"] + 1,
                    suggestion=f"Consider restructuring to use heading levels 1-{max_heading_depth}"
                ))
                auto_fixable += 1
        
        # Check section lengths
        for i, h in enumerate(headings):
            start_idx = h["line_index"] + 1
            end_idx = headings[i + 1]["line_index"] if i + 1 < len(headings) else len(lines)
            
            section_content = '\n'.join(lines[start_idx:end_idx]).strip()
            section_length = len(section_content)
            
            if section_length < min_section_length and section_length > 0:
                issues.append(ValidationIssue(
                    level="info",
                    category="short_section",
                    message=f"Section '{h['text']}' is only {section_length} characters (min recommended: {min_section_length})",
                    line_number=h["line_index"] + 1,
                    suggestion=f"Add at least {min_section_length - section_length} more characters of content"
                ))
                auto_fixable += 1
        
        # Check for empty sections
        for i, h in enumerate(headings):
            start_idx = h["line_index"] + 1
            end_idx = headings[i + 1]["line_index"] if i + 1 < len(headings) else len(lines)
            
            section_content = '\n'.join(lines[start_idx:end_idx]).strip()
            if not section_content:
                issues.append(ValidationIssue(
                    level="warning",
                    category="empty_section",
                    message=f"Section '{h['text']}' has no content",
                    line_number=h["line_index"] + 1,
                    suggestion=f"Add content to the section or remove the heading"
                ))
        
        confidence = 1.0 if not issues else max(0.6, 1.0 - (len([i for i in issues if i.level == "error"]) * 0.15))
        
        return ValidationResult(
            confidence=confidence,
            issues=issues,
            auto_fixable_count=auto_fixable,
            metrics={
                "structure_valid": len([i for i in issues if i.level == "error"]) == 0,
                "sections_count": len(headings),
                "max_depth_found": max([h["level"] for h in headings]) if headings else 0
            }
        )

    async def _validate_with_llm(self, content: str, plugin_context: Dict, rule_context: Dict, truth_context: Dict) -> ValidationResult:
        """Validate content using Ollama LLM with mistral model."""
        try:
            from core.ollama import async_validate_content_contradictions, async_validate_content_omissions, ollama

            # Get plugin information for context
            plugin_info = plugin_context.get("plugins", [])
            family_rules = rule_context.get("family_rules", {})

            # Run both contradiction and omission validation
            contradictions = await async_validate_content_contradictions(
                content, plugin_info, family_rules
            )
            omissions = await async_validate_content_omissions(
                content, plugin_info, family_rules
            )

            # Combine issues from both validations
            all_issues = []
            auto_fixable = 0

            for contradiction in contradictions:
                issue = ValidationIssue(
                    level=contradiction.get("level", "warning"),
                    category=contradiction.get("category", "llm_contradiction"),
                    message=contradiction.get("message", "Content contradiction detected"),
                    suggestion=contradiction.get("suggestion", "Review and correct the identified contradiction"),
                    source="ollama_mistral"
                )
                all_issues.append(issue)
                if contradiction.get("level") in ["info", "warning"]:
                    auto_fixable += 1

            for omission in omissions:
                issue = ValidationIssue(
                    level=omission.get("level", "info"),
                    category=omission.get("category", "llm_omission"),
                    message=omission.get("message", "Missing information detected"),
                    suggestion=omission.get("suggestion", "Consider adding the missing information"),
                    source="ollama_mistral"
                )
                all_issues.append(issue)
                if omission.get("level") in ["info", "warning"]:
                    auto_fixable += 1

            # Calculate confidence based on issues found
            confidence = max(0.3, 1.0 - (len(all_issues) * 0.1))

            return ValidationResult(
                confidence=confidence,
                issues=all_issues,
                auto_fixable_count=auto_fixable,
                metrics={
                    "llm_valid": len(all_issues) == 0,
                    "contradictions_found": len(contradictions),
                    "omissions_found": len(omissions),
                    "ollama_model": ollama.model,
                    "ollama_enabled": ollama.enabled
                }
            )

        except Exception as e:
            self.logger.warning(f"LLM validation failed: {e}")
            return ValidationResult(
                confidence=0.5,
                issues=[ValidationIssue(
                    level="warning",
                    category="llm_error",
                    message=f"LLM validation unavailable: {str(e)}",
                    suggestion="Ensure Ollama is running with mistral model",
                    source="ollama_mistral"
                )],
                auto_fixable_count=0,
                metrics={"llm_valid": False, "llm_error": str(e)}
            )

    # ----------------------
    # Utility helpers
    # ----------------------
    def _calculate_content_confidence(self, issues: List[ValidationIssue], metrics: Dict[str, Any]) -> float:
        if not issues:
            return 1.0
        return 0.8

    async def _store_validation_result(
        self,
        file_path: str,
        content_length: int,
        validation_types: List[str],
        issues: List[ValidationIssue],
        confidence: float,
        metrics: Dict[str, Any],
        family: str
    ) -> None:
        """Store validation results in database (best effort)."""
        try:
            # Store validation results in database and create recommendations
            validation_result = db_manager.create_validation_result(
                file_path=file_path,
                rules_applied=validation_types,
                validation_results={"confidence": confidence, "issues_count": len(issues), "issues": [issue.to_dict() for issue in issues], "metrics": metrics},
                notes=f"Validation completed with {len(issues)} issues",
                severity="info" if confidence > 0.7 else "warning" if confidence > 0.5 else "error",
                status="pass" if confidence > 0.7 else "warning" if confidence > 0.5 else "fail",
                content=f"Content length: {content_length}",
                run_id=f"validation_{family}_{file_path.replace('/', '_').replace('\\', '_')}"
            )

            # Create recommendations for high-value issues
            for issue in issues:
                if issue.level in ["error", "warning"] and issue.suggestion:
                    db_manager.create_recommendation(
                        validation_id=validation_result.id,
                        type="validation_fix",
                        title=f"Fix {issue.category}: {issue.message[:50]}...",
                        description=issue.message,
                        suggestion=issue.suggestion,
                        confidence=confidence,
                        auto_apply=issue.level == "info",
                        metadata={
                            "issue_level": issue.level,
                            "issue_category": issue.category,
                            "line_number": issue.line_number,
                            "column": issue.column,
                            "source": issue.source
                        }
                    )

            self.logger.debug("Validation results and recommendations stored for %s", file_path)
        except Exception as e:
            self.logger.exception("Failed to store validation results: %s", e)
