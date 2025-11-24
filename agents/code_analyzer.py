"""
scripts/tbcv/agents/code_analyzer.py
------------------------------------

Agent: CodeAnalyzerAgent

Purpose:
  Analyze code snippets (C#, Python, JS/TS) for security, performance,
  style, and quality issues; understand document-processing flow (Aspose-*),
  and optionally generate high-confidence auto-fixes.

Design Notes:
  • Uses ABSOLUTE imports (agents.*, core.*) to match your TBCV wiring.
  • Conforms to BaseAgent contract (MCP-style): get_contract(), _register_message_handlers().
  • No network calls at import time (only inside *_fetch_* helpers).
  • Extensively commented for human + LLM readability.
"""

from __future__ import annotations

import re
import ast
import json
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass

# --- Project imports (absolute) ---
from agents.base import BaseAgent, AgentContract, AgentCapability
from core.logging import PerformanceLogger


# ======================================================
# Data Models
# ======================================================

@dataclass
class CodeIssue:
    """
    Represents a detected issue in code.

    Fields:
      type: category, e.g. "security" | "performance" | "style" | "quality" | "dependency"
      severity: "critical" | "high" | "medium" | "low" | "info"
      rule_id: stable identifier of the rule that fired (e.g., "CS001")
      message: human-readable description of the issue
      line_number/column: best-effort source location (1-based)
      suggestion: suggested remediation text (if any)
      auto_fixable: whether an automated patch can be generated
      code_snippet: line-level snippet where the issue was found
    """
    type: str
    severity: str
    rule_id: str
    message: str
    line_number: Optional[int] = None
    column: Optional[int] = None
    suggestion: Optional[str] = None
    auto_fixable: bool = False
    code_snippet: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "severity": self.severity,
            "rule_id": self.rule_id,
            "message": self.message,
            "line_number": self.line_number,
            "column": self.column,
            "suggestion": self.suggestion,
            "auto_fixable": self.auto_fixable,
            "code_snippet": self.code_snippet,
        }


@dataclass
class CodeFix:
    """
    Represents a concrete automatic fix.

    Fields:
      issue_id: rule id associated with this fix
      original_code: text to replace
      fixed_code: proposed replacement text
      confidence: 0..1 confidence score
      description: short rationale/explanation
    """
    issue_id: str
    original_code: str
    fixed_code: str
    confidence: float
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue_id": self.issue_id,
            "original_code": self.original_code,
            "fixed_code": self.fixed_code,
            "confidence": self.confidence,
            "description": self.description,
        }


# ======================================================
# Agent
# ======================================================

class CodeAnalyzerAgent(BaseAgent):
    """
    Advanced code analysis agent with document-processing flow understanding.

    Capabilities:
      - Multi-language checks (C#, Python, JavaScript/TypeScript)
      - Security/performance/style/quality rules
      - Document flow (load/create -> content -> format -> convert -> save)
      - Auto-fix generation for selected rules
      - Optional fetchers (gist/github/url) to analyze remote code
    """

    # -------- Lifecycle --------
    def __init__(self, agent_id: Optional[str] = None):
        # Declare supported languages + which analyzer groups they use.
        self.supported_languages = {
            "csharp": {"extensions": [".cs"], "analyzers": ["security", "performance", "style", "quality"]},
            "python": {"extensions": [".py"], "analyzers": ["security", "performance", "style", "quality"]},
            "javascript": {"extensions": [".js", ".ts"], "analyzers": ["security", "performance", "style", "quality"]},
        }
        # Rule storage populated in _setup_analysis_rules()
        self.analysis_rules: Dict[str, List[Dict[str, Any]]] = {}
        self.custom_rules: Dict[str, Dict[str, Any]] = {}
        super().__init__(agent_id)

    # -------- Contract required by BaseAgent --------
    def get_contract(self) -> AgentContract:
        """
        Returns static metadata the orchestrator/API uses to discover and route.
        """
        return AgentContract(
            agent_id=self.agent_id,
            name="CodeAnalyzerAgent",
            version="1.0.0",
            capabilities=[
                AgentCapability(
                    name="analyze_code",
                    description="Analyze code for security, performance, style, quality, and document flow.",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "code": {"type": "string"},
                            "language": {"type": "string"},
                            "analysis_types": {
                                "type": "array",
                                "items": {"type": "string", "enum": ["security", "performance", "style", "quality", "document_flow", "all"]},
                            },
                            "severity_filter": {"type": "string", "enum": ["critical", "high", "medium", "low", "info"]},
                            "auto_fix": {"type": "boolean"},
                            "source_type": {"type": "string", "enum": ["inline", "gist", "github", "url"]},
                            "source_url": {"type": "string"},
                        },
                        "required": ["code"],
                    },
                    output_schema={
                        "type": "object",
                        "properties": {
                            "language": {"type": "string"},
                            "source_type": {"type": "string"},
                            "main_code_block": {"type": "string"},
                            "document_processing": {"type": "object"},
                            "issues": {"type": "array"},
                            "fixes": {"type": "array"},
                            "metrics": {"type": "object"},
                            "updated_code": {"type": "string"},
                        },
                    },
                    side_effects=["read", "cache", "network"],
                ),
                AgentCapability(
                    name="fix_code",
                    description="Apply high-confidence auto-fixes to known patterns.",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "code": {"type": "string"},
                            "language": {"type": "string"},
                            "fix_types": {"type": "array", "items": {"type": "string"}},
                            "confidence_threshold": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                        },
                        "required": ["code"],
                    },
                    output_schema={
                        "type": "object",
                        "properties": {
                            "original_code": {"type": "string"},
                            "fixed_code": {"type": "string"},
                            "fixes_applied": {"type": "array"},
                            "confidence": {"type": "number"},
                        },
                    },
                ),
                AgentCapability(
                    name="check_security",
                    description="Run security-only analysis.",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "code": {"type": "string"},
                            "language": {"type": "string"},
                            "security_level": {"type": "string", "enum": ["basic", "standard", "strict"]},
                        },
                        "required": ["code"],
                    },
                    output_schema={"type": "object"},
                ),
                AgentCapability(
                    name="optimize_performance",
                    description="Run performance-only analysis (may generate fixes).",
                    input_schema={"type": "object", "properties": {"code": {"type": "string"}, "language": {"type": "string"}}},
                    output_schema={"type": "object"},
                ),
                AgentCapability(
                    name="update_dependencies",
                    description="Analyze code dependencies, detect imports, and suggest improvements.",
                    input_schema={"type": "object", "properties": {"code": {"type": "string"}, "language": {"type": "string"}, "file_path": {"type": "string"}}},
                    output_schema={"type": "object", "properties": {"dependencies": {"type": "array"}, "suggestions": {"type": "array"}, "analyzed": {"type": "boolean"}}},
                ),
                AgentCapability(
                    name="get_supported_languages",
                    description="Return supported languages and rule counts.",
                    input_schema={"type": "object"},
                    output_schema={"type": "object"},
                ),
                AgentCapability(
                    name="add_custom_rule",
                    description="Add a custom rule at runtime.",
                    input_schema={"type": "object", "properties": {"rule_id": {"type": "string"}, "rule_data": {"type": "object"}}, "required": ["rule_id", "rule_data"]},
                    output_schema={"type": "object"},
                ),
            ],
            checkpoints=["analysis_start", "rule_application", "fix_generation", "analysis_complete"],
            max_runtime_s=300,
            confidence_threshold=0.7,
            side_effects=["read", "cache", "network"],
            dependencies=["truth_manager"],
            resource_limits={"max_memory_mb": 1024, "max_cpu_percent": 80, "max_concurrent": 3},
        )

    # -------- Registration & Config --------
    def _register_message_handlers(self):
        """
        Maps MCP method names to async handler functions.
        """
        self.register_handler("ping", self.handle_ping)
        self.register_handler("get_status", self.handle_get_status)
        self.register_handler("get_contract", self.get_contract)

        self.register_handler("analyze_code", self.handle_analyze_code)
        self.register_handler("fix_code", self.handle_fix_code)
        self.register_handler("format_code", self.handle_format_code)

        self.register_handler("check_security", self.handle_check_security)
        self.register_handler("optimize_performance", self.handle_optimize_performance)
        self.register_handler("update_dependencies", self.handle_update_dependencies)

        self.register_handler("get_supported_languages", self.handle_get_supported_languages)
        self.register_handler("add_custom_rule", self.handle_add_custom_rule)

    def _validate_configuration(self):
        """
        Build built-in analysis rules for each language/category.
        Called once during BaseAgent.__init__().
        """
        self._setup_analysis_rules()
        self.logger.info("Code analyzer initialized with rules", rule_count=len(self.analysis_rules))

    # ======================================================
    # Ruleset Setup
    # ======================================================

    def _setup_analysis_rules(self):
        """
        Populate self.analysis_rules[...] with language-specific patterns.

        Structure:
          self.analysis_rules['csharp_security'] = [ { id, type, severity, pattern, message, suggestion? }, ... ]
        """
        # --- C# Security ---
        self.analysis_rules["csharp_security"] = [
            {
                "id": "CS001",
                "type": "security",
                "severity": "high",
                "pattern": r'SqlCommand\s*\(\s*["\'].*?\+.*?["\']',
                "message": "Potential SQL injection vulnerability",
                "suggestion": "Use parameterized queries instead of string concatenation",
            },
            {
                "id": "CS002",
                "type": "security",
                "severity": "medium",
                "pattern": r"Random\s*\(\s*\)",
                "message": "Using non-cryptographic Random for security",
                "suggestion": "Use RNGCryptoServiceProvider/RandomNumberGenerator for cryptographic operations",
            },
            {
                "id": "CS003",
                "type": "security",
                "severity": "high",
                "pattern": r'Process\.Start\s*\(\s*["\'].*?\+.*?["\']',
                "message": "Potential command injection vulnerability",
                "suggestion": "Validate and sanitize input before executing commands",
            },
        ]

        # --- C# Performance ---
        self.analysis_rules["csharp_performance"] = [
            {
                "id": "CP001",
                "type": "performance",
                "severity": "medium",
                "pattern": r'string\s+\w+\s*=\s*["\']["\'];\s*(\w+\s*\+=.*?;.*?){3,}',
                "message": "String concatenation in loop detected",
                "suggestion": "Use StringBuilder for multiple concatenations in loops",
            },
            {
                "id": "CP002",
                "type": "performance",
                "severity": "low",
                "pattern": r"\.ToList\(\)\.Count\(\)",
                "message": "Inefficient count operation",
                "suggestion": "Use .Count() directly instead of .ToList().Count()",
            },
            {
                "id": "CP003",
                "type": "performance",
                "severity": "medium",
                "pattern": r"new\s+List<.*?>\(\)\s*{\s*}",
                "message": "Empty list initialization",
                "suggestion": "Consider Array.Empty<T>() for immutable empty collections",
            },
        ]

        # --- C# Style ---
        self.analysis_rules["csharp_style"] = [
            {
                "id": "CST001",
                "type": "style",
                "severity": "low",
                "pattern": r"public\s+(?!class|interface|enum|struct)\w+\s+\w+\s*{\s*get;\s*set;\s*}",
                "message": "Consider using auto-implemented properties",
                "suggestion": "Use auto-implemented properties when no additional logic is needed",
            },
            {
                "id": "CST002",
                "type": "style",
                "severity": "low",
                "pattern": r"if\s*\(\s*\w+\s*==\s*true\s*\)",
                "message": "Redundant boolean comparison",
                "suggestion": "Use if (condition) instead of if (condition == true)",
            },
        ]

        # --- C# Quality ---
        self.analysis_rules["csharp_quality"] = [
            {
                "id": "CQ001",
                "type": "quality",
                "severity": "high",
                "pattern": r"catch\s*\(\s*Exception\s+\w*\s*\)\s*{\s*}",
                "message": "Empty catch block swallows exceptions",
                "suggestion": "Handle exceptions appropriately or log them",
            },
            {
                "id": "CQ002",
                "type": "quality",
                "severity": "medium",
                "pattern": r"public\s+class\s+\w+\s*{[^}]*public\s+\w+\s+\w+;",
                "message": "Public field detected",
                "suggestion": "Use properties instead of public fields",
            },
        ]

    # ======================================================
    # Public Async Handlers
    # ======================================================

    async def handle_analyze_code(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main analysis entry point.

        Inputs:
          - code (str): code or markdown with fenced code blocks
          - language (str, optional): 'csharp'|'python'|'javascript'; auto-detected if omitted
          - analysis_types (list): any of ["security","performance","style","quality","document_flow","all"]
          - severity_filter (str): minimum severity to include (critical > ... > info)
          - auto_fix (bool): whether to generate fixes for auto-fixable issues
          - source_type/source_url: optional remote fetch (gist/github/url)

        Returns:
          dict with language, main_code_block, document_processing, issues, fixes, metrics, updated_code
        """
        code = params.get("code", "")
        language = (params.get("language") or "").lower()
        analysis_types = params.get("analysis_types", ["all"])
        severity_filter = params.get("severity_filter", "info")
        auto_fix = bool(params.get("auto_fix", False))
        source_type = params.get("source_type", "inline")
        source_url = params.get("source_url", "")

        # Optional external fetch
        if not code and source_url:
            code = await self._fetch_external_code(source_url, source_type)
            if not code:
                return {"error": f"Could not fetch code from {source_url}"}

        if not code:
            return {"error": "No code provided for analysis"}

        # Language auto-detect if missing
        if not language:
            language = self._detect_language(code)

        if language not in self.supported_languages:
            return {"error": f"Unsupported language: {language}"}

        with PerformanceLogger(self.logger, f"analyze_code_{language}") as perf:
            # Extract “main” code block (largest/most significant)
            main_code_block = self._extract_main_code_block(code, language)

            # Document flow (Aspose) understanding
            document_flow = self._analyze_document_processing_flow(main_code_block, language)

            # Expand "all" into explicit list
            if "all" in analysis_types:
                analysis_types = ["security", "performance", "style", "quality", "document_flow"]

            # Traditional rule checks (skip 'document_flow' because handled above)
            issues: List[CodeIssue] = []
            for analysis_type in analysis_types:
                if analysis_type == "document_flow":
                    continue
                issues.extend(self._analyze_by_type(main_code_block, language, analysis_type))

            # Severity filtering (keep >= requested severity)
            severity_levels = ["critical", "high", "medium", "low", "info"]
            min_idx = severity_levels.index(severity_filter)
            filtered = [i for i in issues if severity_levels.index(i.severity) <= min_idx]

            # Generate fixes if requested
            fixes: List[CodeFix] = []
            if auto_fix:
                fixes = self._generate_fixes(main_code_block, language, filtered)

            # Metrics (basic code metrics + flow metrics)
            metrics = self._calculate_metrics(main_code_block, language, filtered)
            metrics.update(document_flow.get("metrics", {}))

            # Apply fixes to produce updated_code
            updated_code = self._apply_fixes(main_code_block, fixes) if fixes else None

            perf.add_context(
                issues_found=len(filtered),
                fixes_generated=len(fixes),
                language=language,
                document_operations=len(document_flow.get("operations", [])),
            )

            return {
                "language": language,
                "source_type": source_type,
                "main_code_block": main_code_block,
                "document_processing": document_flow,
                "issues": [i.to_dict() for i in filtered],
                "fixes": [f.to_dict() for f in fixes],
                "metrics": metrics,
                "updated_code": updated_code,
            }

    async def handle_fix_code(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply high-confidence fixes (>= confidence_threshold) to code.
        """
        code = params.get("code", "")
        language = params.get("language", "")
        fix_types = params.get("fix_types", ["all"])  # forwarded to analyze
        confidence_threshold = float(params.get("confidence_threshold", 0.8))

        analysis = await self.handle_analyze_code(
            {"code": code, "language": language, "analysis_types": fix_types, "auto_fix": True}
        )
        if "error" in analysis:
            return analysis

        fixes = analysis.get("fixes", [])
        high_conf = [f for f in fixes if f.get("confidence", 0.0) >= confidence_threshold]

        fixed_code = code
        for f in high_conf:
            fixed_code = fixed_code.replace(f["original_code"], f["fixed_code"])

        return {
            "original_code": code,
            "fixed_code": fixed_code,
            "fixes_applied": high_conf,
            "confidence": sum(f.get("confidence", 0.0) for f in high_conf) / max(1, len(high_conf)),
        }

    async def handle_format_code(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Very basic formatter: trims trailing whitespace.
        (Hook point for black/clang-format/prettier integration.)
        """
        code = params.get("code", "")
        language = params.get("language", "")
        style = params.get("style", "standard")

        formatted = self._basic_format(code, language)
        return {
            "original_code": code,
            "formatted_code": formatted,
            "style": style,
            "changes_made": self._get_formatting_changes(code, formatted),
        }

    async def handle_check_security(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convenience method: run security-only analysis with low severity threshold.
        """
        code = params.get("code", "")
        language = params.get("language", "")

        result = await self.handle_analyze_code(
            {"code": code, "language": language, "analysis_types": ["security"], "severity_filter": "low"}
        )
        if "error" in result:
            return result

        issues = result.get("issues", [])
        crit = len([i for i in issues if i.get("severity") == "critical"])
        high = len([i for i in issues if i.get("severity") == "high"])
        med = len([i for i in issues if i.get("severity") == "medium"])

        score = max(0, 100 - (crit * 30) - (high * 15) - (med * 5))
        return {"vulnerabilities": issues, "security_score": score, "recommendations": self._get_security_recommendations(issues)}

    async def handle_optimize_performance(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convenience method: performance-only analysis (auto-fix enabled).
        """
        code = params.get("code", "")
        language = params.get("language", "")
        return await self.handle_analyze_code({"code": code, "language": language, "analysis_types": ["performance"], "auto_fix": True})

    async def handle_update_dependencies(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze code dependencies and provide basic suggestions.
        Detects imports/requires and flags common issues.
        """
        code = params.get("code", "")
        language = params.get("language", "").lower()
        file_path = params.get("file_path", "")

        if not code:
            return {"dependencies": [], "suggestions": [], "message": "No code provided"}

        dependencies = []
        suggestions = []

        try:
            if language == "python":
                # Extract Python imports
                import re
                import_patterns = [
                    r'^import\s+(\w+)',
                    r'^from\s+(\w+)',
                ]
                for pattern in import_patterns:
                    for match in re.finditer(pattern, code, re.MULTILINE):
                        dep = match.group(1)
                        dependencies.append({"name": dep, "type": "import", "language": "python"})

                # Check for common outdated patterns
                if "urllib2" in code:
                    suggestions.append({
                        "type": "deprecation",
                        "message": "urllib2 is deprecated in Python 3, use urllib.request instead",
                        "severity": "high"
                    })
                if "imp.load_source" in code:
                    suggestions.append({
                        "type": "deprecation",
                        "message": "imp module is deprecated, use importlib instead",
                        "severity": "high"
                    })

            elif language in ["javascript", "typescript", "js", "ts"]:
                # Extract JS/TS imports
                import re
                patterns = [
                    r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]',
                    r'require\([\'"]([^\'"]+)[\'"]\)',
                ]
                for pattern in patterns:
                    for match in re.finditer(pattern, code):
                        dep = match.group(1)
                        dependencies.append({"name": dep, "type": "import", "language": language})

                # Check for common issues
                if "var " in code:
                    suggestions.append({
                        "type": "best_practice",
                        "message": "Consider using 'const' or 'let' instead of 'var'",
                        "severity": "low"
                    })

            elif language in ["go", "golang"]:
                # Extract Go imports
                import re
                import_pattern = r'import\s+(?:\(([^)]+)\)|"([^"]+)")'
                for match in re.finditer(import_pattern, code):
                    imports_block = match.group(1) or match.group(2)
                    if imports_block:
                        for line in imports_block.split('\n'):
                            dep_match = re.search(r'"([^"]+)"', line)
                            if dep_match:
                                dependencies.append({"name": dep_match.group(1), "type": "import", "language": "go"})

            # Generic suggestions
            if len(dependencies) > 50:
                suggestions.append({
                    "type": "complexity",
                    "message": f"High number of dependencies ({len(dependencies)}). Consider refactoring.",
                    "severity": "medium"
                })

            return {
                "dependencies": dependencies,
                "dependency_count": len(dependencies),
                "suggestions": suggestions,
                "language": language,
                "analyzed": True
            }

        except Exception as e:
            self.logger.error("Dependency analysis failed", error=str(e))
            return {
                "dependencies": [],
                "suggestions": [],
                "error": str(e),
                "analyzed": False
            }

    async def handle_get_supported_languages(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Return analyzer coverage summary.
        """
        return {
            "supported_languages": self.supported_languages,
            "total_rules": sum(len(rules) for rules in self.analysis_rules.values()),
            "analysis_types": ["security", "performance", "style", "quality", "document_flow"],
        }

    async def handle_add_custom_rule(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Install a custom rule at runtime.
        """
        rule_id = params.get("rule_id")
        rule_data = params.get("rule_data")
        if not rule_id or not rule_data:
            return {"error": "rule_id and rule_data required"}
        self.custom_rules[rule_id] = rule_data
        return {"success": True, "rule_id": rule_id, "message": "Custom rule added successfully"}

    # ======================================================
    # Helpers (pure)
    # ======================================================

    def _detect_language(self, code: str) -> str:
        """
        Heuristic language detection based on recognizable tokens.
        """
        if re.search(r"\busing\s+System\b|\bnamespace\b|\bpublic\s+class\b", code):
            return "csharp"
        if re.search(r"\bimport\b|\bdef\s+\w+\s*\(|\bclass\s+\w+\s*:", code):
            return "python"
        if re.search(r"\bfunction\b|\bvar\s+\w+\s*=|\bconsole\.log\b", code):
            return "javascript"
        return "text"

    def _extract_markdown_code_blocks(self, content: str) -> List[Tuple[str, str]]:
        """
        Extract (lang, code) pairs from fenced code blocks in Markdown.
        """
        matches = re.findall(r"```(\w+)?\s*\n(.*?)\n```", content, re.DOTALL | re.MULTILINE)
        blocks: List[Tuple[str, str]] = []
        for lang, code in matches:
            if code.strip():
                blocks.append(((lang or "text").lower(), code.strip()))
        return blocks

    def _extract_largest_markdown_code_block(self, content: str) -> str:
        """
        Fallback: return largest fenced block, else entire content.
        """
        blocks = self._extract_markdown_code_blocks(content)
        return max(blocks, key=lambda x: len(x[1]))[1] if blocks else content.strip()

    def _find_most_significant_code_block(self, code_blocks: List[Tuple[str, str]], target_language: str) -> str:
        """
        Score blocks by language match, size, and keyword density; return the winner.
        """
        if not code_blocks:
            return ""
        scored: List[Tuple[float, str]] = []
        for lang, code in code_blocks:
            score = 0.0
            # Strong bonus for language match
            if lang == target_language or (target_language == "csharp" and lang in {"csharp", "cs", "c#"}):
                score += 100
            # Size bonus
            score += len(code) * 0.1
            # Complexity keywords
            for kw in ["class", "function", "def", "public", "private", "static", "for", "while", "if", "try", "catch", "using", "namespace"]:
                score += code.lower().count(kw) * 5
            # Aspose signal
            for pat in ["Document", "Workbook", "Presentation", "MailMessage", "Aspose.Words", "Aspose.Cells", "Aspose.Slides", "Aspose.Email", "Save", "Load", "Convert"]:
                score += code.count(pat) * 10
            scored.append((score, code))
        return max(scored, key=lambda x: x[0])[1]

    def _extract_main_code_block(self, content: str, language: str) -> str:
        """
        Extract the most relevant code block for analysis.
        """
        if language not in ["csharp", "python", "javascript"]:
            return self._extract_largest_markdown_code_block(content)
        blocks = self._extract_markdown_code_blocks(content)
        return self._find_most_significant_code_block(blocks, language) if blocks else content.strip()

    def _analyze_document_processing_flow(self, code: str, language: str) -> Dict[str, Any]:
        """
        Recognize typical Aspose document workflows (load/create → content → format → convert/save).
        """
        document_info = self._detect_document_type(code)
        operations = self._extract_operations_sequence(code, document_info)
        observations = self._generate_code_observations(operations, document_info)
        metrics = self._calculate_flow_metrics(operations, document_info)
        return {
            "document_type": document_info["type"],
            "main_object": document_info["main_object"],
            "operations": operations,
            "observations": observations[:5],
            "metrics": metrics,
            "processing_pattern": self._identify_processing_pattern(operations),
        }

    def _detect_document_type(self, code: str) -> Dict[str, Any]:
        """
        Score product families by token presence; pick the winner.
        """
        products = {
            "words": {"patterns": ["Document", "DocumentBuilder", "Aspose.Words", "SaveFormat", "LoadFormat"], "main_object": "Document", "file_types": ["docx", "doc", "pdf", "html", "rtf"]},
            "cells": {"patterns": ["Workbook", "Worksheet", "Cell", "Aspose.Cells", "FileFormatType"], "main_object": "Workbook", "file_types": ["xlsx", "xls", "csv", "pdf"]},
            "slides": {"patterns": ["Presentation", "Slide", "Aspose.Slides", "SaveFormat"], "main_object": "Presentation", "file_types": ["pptx", "ppt", "pdf"]},
            "email": {"patterns": ["MailMessage", "Aspose.Email", "SmtpClient"], "main_object": "MailMessage", "file_types": ["msg", "eml", "mbox"]},
            "pdf": {"patterns": ["Document", "Page", "Aspose.Pdf"], "main_object": "Document", "file_types": ["pdf"]},
        }
        scores: Dict[str, int] = {}
        for product, info in products.items():
            s = 0
            for pat in info["patterns"]:
                s += code.count(pat) * 10
                s += code.lower().count(pat.lower()) * 5
            scores[product] = s
        if scores and max(scores.values()) > 0:
            best = max(scores.keys(), key=lambda k: scores[k])
            return {"type": best, "main_object": products[best]["main_object"], "supported_formats": products[best]["file_types"], "confidence": min(1.0, scores[best] / 100)}
        return {"type": "unknown", "main_object": "Object", "supported_formats": [], "confidence": 0.0}

    def _extract_operations_sequence(self, code: str, document_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect load/create/save/content/format/convert operations line-by-line.
        """
        lines = code.split("\n")
        ops: List[Dict[str, Any]] = []
        main_obj = document_info.get("main_object", "Document")
        patterns = {
            "load": {"patterns": [rf'{main_obj}\s*\(\s*["\']([^"\']+)["\']', r'Load\s*\(\s*["\']([^"\']+)["\']'], "type": "load", "description": "Load document from file"},
            "create": {"patterns": [rf"{main_obj}\s*\(\s*\)", rf"new\s+{main_obj}\s*\(\s*\)"], "type": "create", "description": "Create new document"},
            "save": {"patterns": [r'Save\s*\(\s*["\']([^"\']+)["\']', r'SaveAs\s*\(\s*["\']([^"\']+)["\']'], "type": "save", "description": "Save document to file"},
            "add_text": {"patterns": [r"Write\s*\(", r"AppendText\s*\(", r"InsertText\s*\(", r'Write\s*\(\s*["\']([^"\']+)["\']'], "type": "content_add", "description": "Add text content"},
            "add_table": {"patterns": [r"InsertTable\s*\(", r"CreateTable\s*\(", r"AddTable\s*\(", r"Table\s*\("], "type": "content_add", "description": "Add table"},
            "add_image": {"patterns": [r"InsertImage\s*\(", r"AddImage\s*\(", r"DrawImage\s*\("], "type": "content_add", "description": "Add image"},
            "format": {"patterns": [r"Font\s*\.", r"Style\s*\.", r"Format\s*\.", r"SetFont\s*\("], "type": "formatting", "description": "Apply formatting"},
            "convert": {"patterns": [r"SaveFormat\.(\w+)", r"ConvertTo\s*\(", r"ExportTo\s*\("], "type": "convert", "description": "Convert to different format"},
        }
        for line_no, line in enumerate(lines, 1):
            s = line.strip()
            if not s or s.startswith("//") or s.startswith("#"):
                continue
            for opname, info in patterns.items():
                for pat in info["patterns"]:
                    m = re.search(pat, s, re.IGNORECASE)
                    if m:
                        ops.append(
                            {
                                "line": line_no,
                                "type": info["type"],
                                "operation": opname,
                                "description": info["description"],
                                "code": s,
                                "parameters": list(m.groups()) if m.groups() else [],
                            }
                        )
                        break
        return ops

    def _generate_code_observations(self, operations: List[Dict[str, Any]], document_info: Dict[str, Any]) -> List[str]:
        """
        Produce concise human-readable bullets about the workflow.
        """
        obs: List[str] = []
        doc_type = document_info.get("type", "unknown")
        if doc_type != "unknown":
            obs.append(f"This code works with {doc_type.title()} documents using Aspose.{doc_type.title()}")

        load_ops = [o for o in operations if o["type"] == "load"]
        create_ops = [o for o in operations if o["type"] == "create"]
        save_ops = [o for o in operations if o["type"] == "save"]
        content_ops = [o for o in operations if o["type"] == "content_add"]

        if load_ops:
            filenames = [p for o in load_ops for p in o.get("parameters", [])]
            obs.append(f"Loads existing document from file: {', '.join(filenames[:2])}" if filenames else "Loads an existing document from file")
        elif create_ops:
            obs.append("Creates a new blank document")

        if content_ops:
            kinds = set(o["operation"] for o in content_ops)
            labels = []
            if "add_text" in kinds:
                labels.append("text")
            if "add_table" in kinds:
                labels.append("tables")
            if "add_image" in kinds:
                labels.append("images")
            if labels:
                obs.append(f"Adds content to document: {', '.join(labels)}")

        if save_ops:
            fmts: List[str] = []
            for o in save_ops:
                for p in o.get("parameters", []):
                    if "." in p:
                        ext = p.rsplit(".", 1)[-1].lower()
                        if ext in {"pdf", "docx", "doc", "html", "xlsx", "pptx"}:
                            fmts.append(ext.upper())
            obs.append(f"Saves the final document as {fmts[0]}" if len(set(fmts)) == 1 and fmts else ("Saves document in multiple formats: " + ", ".join(sorted(set(fmts)))) if fmts else "Saves the processed document")

        if any(o["type"] == "convert" for o in operations):
            obs.append("Performs document format conversion")

        if len(operations) > 10:
            obs.append("Implements complex document processing workflow with multiple operations")
        elif len(operations) > 5:
            obs.append("Performs multiple document processing steps")

        return obs

    def _calculate_flow_metrics(self, operations: List[Dict[str, Any]], document_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Summarize document-flow characteristics.
        """
        types = [o["type"] for o in operations]
        return {
            "total_operations": len(operations),
            "operation_types": {k: types.count(k) for k in ["load", "create", "save", "content_add", "formatting", "convert"]},
            "document_confidence": document_info.get("confidence", 0.0),
            "complexity_score": min(100, len(operations) * 5),
            "has_input": any(t == "load" for t in types),
            "has_output": any(t == "save" for t in types),
            "is_complete_workflow": (any(t in {"load", "create"} for t in types) and any(t == "save" for t in types)),
        }

    def _identify_processing_pattern(self, operations: List[Dict[str, Any]]) -> str:
        """
        Tag the overall workflow archetype.
        """
        seq = [o["type"] for o in operations]
        if "load" in seq and "save" in seq:
            return "modify_existing" if ("content_add" in seq or "formatting" in seq) else "convert_format"
        if "create" in seq and "save" in seq:
            return "create_new"
        if "load" in seq and "content_add" in seq:
            return "content_generation"
        return "single_operation" if len(set(seq)) == 1 else "complex_workflow"

    def _analyze_by_type(self, code: str, language: str, analysis_type: str) -> List[CodeIssue]:
        """
        Apply regex-style static rules for (language, category).
        """
        issues: List[CodeIssue] = []
        key = f"{language}_{analysis_type}"
        rules = self.analysis_rules.get(key, [])
        lines = code.split("\n")
        for rule in rules:
            pat = rule["pattern"]
            for ln, line in enumerate(lines, 1):
                for m in re.finditer(pat, line, re.IGNORECASE):
                    issues.append(
                        CodeIssue(
                            type=rule["type"],
                            severity=rule["severity"],
                            rule_id=rule["id"],
                            message=rule["message"],
                            line_number=ln,
                            column=m.start() + 1,
                            suggestion=rule.get("suggestion"),
                            auto_fixable=self._is_auto_fixable(rule["id"]),
                            code_snippet=line.strip(),
                        )
                    )
        return issues

    def _is_auto_fixable(self, rule_id: str) -> bool:
        """
        Whitelist which rule IDs can be fixed automatically (high precision).
        """
        return rule_id in {"CST002", "CP002", "CST001"}

    def _generate_fixes(self, code: str, language: str, issues: List[CodeIssue]) -> List[CodeFix]:
        """
        Create CodeFix objects for issues marked auto-fixable.
        """
        fixes: List[CodeFix] = []
        for issue in issues:
            if not issue.auto_fixable:
                continue
            fx = self._generate_fix_for_issue(code, issue)
            if fx:
                fixes.append(fx)
        return fixes

    def _generate_fix_for_issue(self, code: str, issue: CodeIssue) -> Optional[CodeFix]:
        """
        Rule-specific fixers.
        """
        if issue.rule_id == "CST002":  # Redundant boolean comparison
            original = issue.code_snippet or ""
            fixed = re.sub(r"if\s*\(\s*(\w+)\s*==\s*true\s*\)", r"if (\1)", original)
            return CodeFix(issue_id=issue.rule_id, original_code=original, fixed_code=fixed, confidence=0.95, description="Remove redundant boolean comparison")

        if issue.rule_id == "CP002":  # Inefficient .ToList().Count()
            original = issue.code_snippet or ""
            fixed = re.sub(r"\.ToList\(\)\.Count\(\)", ".Count()", original)
            return CodeFix(issue_id=issue.rule_id, original_code=original, fixed_code=fixed, confidence=0.90, description="Optimize count operation")

        # Extend here with more safe transformations…
        return None

    def _apply_fixes(self, code: str, fixes: List[CodeFix]) -> str:
        """
        Apply fixes in descending confidence order.
        """
        updated = code
        for fx in sorted(fixes, key=lambda f: f.confidence, reverse=True):
            if fx.confidence >= 0.8:
                updated = updated.replace(fx.original_code, fx.fixed_code)
        return updated

    def _calculate_metrics(self, code: str, language: str, issues: List[CodeIssue]) -> Dict[str, Any]:
        """
        Simple code metrics + issue distributions.
        """
        lines = code.split("\n")
        metrics: Dict[str, Any] = {
            "total_lines": len(lines),
            "code_lines": len([l for l in lines if l.strip() and not l.strip().startswith("//")]),
            "comment_lines": len([l for l in lines if l.strip().startswith("//")]),
            "blank_lines": len([l for l in lines if not l.strip()]),
            "total_issues": len(issues),
            "issues_by_severity": {},
            "issues_by_type": {},
            "complexity_score": 0,
            "maintainability_index": 0,
        }
        for i in issues:
            metrics["issues_by_severity"][i.severity] = metrics["issues_by_severity"].get(i.severity, 0) + 1
            metrics["issues_by_type"][i.type] = metrics["issues_by_type"].get(i.type, 0) + 1

        complexity_indicators = ["if", "for", "while", "switch", "case", "catch", "foreach"]
        cscore = 0
        for l in lines:
            low = l.lower()
            for ind in complexity_indicators:
                cscore += low.count(ind)
        metrics["complexity_score"] = cscore

        base = 100
        metrics["maintainability_index"] = max(0, base - len(issues) * 2 - cscore * 0.5)
        return metrics

    def _basic_format(self, code: str, language: str) -> str:
        """
        Minimal formatter: trim trailing whitespace lines.
        """
        return "\n".join(l.rstrip() for l in code.split("\n"))

    def _get_formatting_changes(self, original: str, formatted: str) -> List[str]:
        """
        Describe what changed during formatting.
        """
        return ["Removed trailing whitespace"] if original != formatted else []

    # ======================================================
    # Optional External Fetchers (network used only on call)
    # ======================================================

    async def _fetch_external_code(self, source_url: str, source_type: str) -> Optional[str]:
        """
        Dispatch to specific fetchers (gist/github/url). Returns None on failure.
        """
        try:
            if source_type == "gist":
                return await self._fetch_gist_code(source_url)
            if source_type == "github":
                return await self._fetch_github_code(source_url)
            if source_type == "url":
                return await self._fetch_url_code(source_url)
            self.logger.warning("Unsupported source type", source_type=source_type)
            return None
        except Exception as e:
            self.logger.error("Failed to fetch external code", error=str(e))
            return None

    async def _fetch_gist_code(self, gist_url: str) -> Optional[str]:
        """
        GET https://api.github.com/gists/<id> and return the largest code file.
        """
        import aiohttp
        m = re.search(r"gist\.github\.com/.*?/([a-f0-9]+)", gist_url)
        if not m:
            return None
        api_url = f"https://api.github.com/gists/{m.group(1)}"
        async with aiohttp.ClientSession() as s:
            async with s.get(api_url) as r:
                if r.status != 200:
                    return None
                data = await r.json()
                candidates: List[Tuple[str, str]] = []
                for fname, fdata in data.get("files", {}).items():
                    if any(fname.endswith(ext) for ext in [".cs", ".py", ".js", ".ts", ".cpp", ".java"]):
                        candidates.append((fname, fdata.get("content", "")))
                if candidates:
                    return max(candidates, key=lambda x: len(x[1]))[1]
                files = data.get("files", {})
                return list(files.values())[0].get("content", "") if files else None

    async def _fetch_github_code(self, github_url: str) -> Optional[str]:
        """
        Convert https://github.com/.../blob/... → https://raw.githubusercontent.com/... and GET the content.
        """
        import aiohttp
        raw = github_url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/") if ("github.com" in github_url and "/blob/" in github_url) else github_url
        async with aiohttp.ClientSession() as s:
            async with s.get(raw) as r:
                return await r.text() if r.status == 200 else None

    async def _fetch_url_code(self, url: str) -> Optional[str]:
        """
        GET arbitrary URL and return text if appropriate content-type.
        """
        import aiohttp
        async with aiohttp.ClientSession() as s:
            async with s.get(url) as r:
                if r.status != 200:
                    return None
                ctype = r.headers.get("content-type", "")
                if "text" in ctype or "application" in ctype:
                    return await r.text()
                return None

def split_code_into_segments(code: str) -> List[str]:
    """
    Split code into logical segments separated by blank lines.
    Empty input returns exactly one empty segment.
    """
    if code is None or code == "":
        return [""]
    
    segments = [s for s in re.split(r"\n{2,}", code) if s is not None]
    return segments if segments else [""]
# ======================================================
# Local Smoke Test (optional)
# ======================================================
if __name__ == "__main__":
    import asyncio

    async def _demo():
        agent = CodeAnalyzerAgent()
        md = (
            "---\n"
            "title: Document Conversion Tutorial\n"
            "description: Shows how to convert Word documents to PDF\n"
            "---\n\n"
            "```csharp\n"
            "using Aspose.Words;\n"
            "public class DocProc { public void Run(){ var doc = new Document(\"input.docx\"); doc.Save(\"out.pdf\", SaveFormat.Pdf); } }\n"
            "```\n"
        )
        result = await agent.handle_analyze_code({"code": md, "language": "csharp", "analysis_types": ["all"], "auto_fix": True})
        print(json.dumps({k: v for k, v in result.items() if k in ["language", "metrics", "document_processing"]}, indent=2))

    asyncio.run(_demo())
