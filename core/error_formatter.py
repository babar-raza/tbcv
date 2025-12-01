# file: core/error_formatter.py
"""
Error Formatter - Formats validation issues for different output modes.
Supports CLI (colorized), JSON, and HTML output formats.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional
from dataclasses import asdict

from agents.validators.base_validator import ValidationIssue, SEVERITY_SCORES


# ANSI color codes for CLI output
class Colors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Severity colors
    CRITICAL = "\033[91m"  # Bright red
    ERROR = "\033[31m"  # Red
    WARNING = "\033[33m"  # Yellow
    INFO = "\033[36m"  # Cyan

    # Additional colors
    GREEN = "\033[32m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    WHITE = "\033[37m"


# Severity icons for CLI
SEVERITY_ICONS = {
    "critical": "!!!",
    "error": "[X]",
    "warning": "[!]",
    "info": "[i]"
}


class ErrorFormatter:
    """
    Formats validation issues for different output modes.

    Supports:
    - CLI output with colors and context snippets
    - JSON output for API responses
    - HTML context for Jinja2 templates
    """

    @staticmethod
    def to_cli(
        issues: List[ValidationIssue],
        colorized: bool = True,
        show_context: bool = True,
        show_suggestions: bool = True,
        max_issues: Optional[int] = None
    ) -> str:
        """
        Format issues for CLI output with colors and context snippets.

        Args:
            issues: List of ValidationIssue objects
            colorized: Whether to use ANSI colors
            show_context: Whether to show context snippets
            show_suggestions: Whether to show fix suggestions
            max_issues: Maximum number of issues to display

        Returns:
            Formatted string for terminal display
        """
        if not issues:
            return "No issues found."

        # Sort by severity
        sorted_issues = sorted(issues, key=lambda i: -i.severity_score)

        if max_issues:
            sorted_issues = sorted_issues[:max_issues]

        lines = []

        # Summary header
        summary = ErrorFormatter._get_summary(issues)
        if colorized:
            lines.append(f"{Colors.BOLD}Validation Results{Colors.RESET}")
            lines.append(f"Total: {summary['total']} issues")
            if summary['by_level'].get('critical', 0) > 0:
                lines.append(f"  {Colors.CRITICAL}Critical: {summary['by_level']['critical']}{Colors.RESET}")
            if summary['by_level'].get('error', 0) > 0:
                lines.append(f"  {Colors.ERROR}Errors: {summary['by_level']['error']}{Colors.RESET}")
            if summary['by_level'].get('warning', 0) > 0:
                lines.append(f"  {Colors.WARNING}Warnings: {summary['by_level']['warning']}{Colors.RESET}")
            if summary['by_level'].get('info', 0) > 0:
                lines.append(f"  {Colors.INFO}Info: {summary['by_level']['info']}{Colors.RESET}")
        else:
            lines.append("Validation Results")
            lines.append(f"Total: {summary['total']} issues")
            for level, count in summary['by_level'].items():
                if count > 0:
                    lines.append(f"  {level.capitalize()}: {count}")

        lines.append("")
        lines.append("-" * 60)

        # Format each issue
        for i, issue in enumerate(sorted_issues, 1):
            lines.append(ErrorFormatter._format_cli_issue(
                issue, i, colorized, show_context, show_suggestions
            ))
            lines.append("")

        if max_issues and len(issues) > max_issues:
            lines.append(f"... and {len(issues) - max_issues} more issues")

        return "\n".join(lines)

    @staticmethod
    def _format_cli_issue(
        issue: ValidationIssue,
        index: int,
        colorized: bool,
        show_context: bool,
        show_suggestions: bool
    ) -> str:
        """Format a single issue for CLI output."""
        lines = []

        # Get color and icon based on level
        if colorized:
            color = getattr(Colors, issue.level.upper(), Colors.WHITE)
            icon = SEVERITY_ICONS.get(issue.level, "[?]")
            level_str = f"{color}{icon} {issue.level.upper()}{Colors.RESET}"
        else:
            icon = SEVERITY_ICONS.get(issue.level, "[?]")
            level_str = f"{icon} {issue.level.upper()}"

        # Header line
        location = ""
        if issue.line_number:
            location = f" at line {issue.line_number}"
            if issue.column:
                location += f":{issue.column}"

        lines.append(f"{index}. {level_str} [{issue.code}]{location}")
        lines.append(f"   {issue.message}")

        # Category/source info
        source_info = f"   Category: {issue.category}"
        if issue.source != "rule_based":
            source_info += f" | Source: {issue.source}"
        if issue.confidence < 1.0:
            source_info += f" | Confidence: {issue.confidence:.0%}"
        lines.append(source_info)

        # Context snippet
        if show_context and issue.context_snippet:
            lines.append(f"   Context: {issue.context_snippet[:80]}...")

        # Suggestion
        if show_suggestions and issue.suggestion:
            if colorized:
                lines.append(f"   {Colors.GREEN}Suggestion: {issue.suggestion}{Colors.RESET}")
            else:
                lines.append(f"   Suggestion: {issue.suggestion}")

        # Fix example
        if show_suggestions and issue.fix_example:
            if colorized:
                lines.append(f"   {Colors.DIM}Example: {issue.fix_example[:60]}...{Colors.RESET}")
            else:
                lines.append(f"   Example: {issue.fix_example[:60]}...")

        # Auto-fixable indicator
        if issue.auto_fixable:
            if colorized:
                lines.append(f"   {Colors.BLUE}[Auto-fixable]{Colors.RESET}")
            else:
                lines.append("   [Auto-fixable]")

        return "\n".join(lines)

    @staticmethod
    def to_json(
        issues: List[ValidationIssue],
        include_summary: bool = True,
        compact: bool = False
    ) -> Dict[str, Any]:
        """
        Format issues for JSON API response.

        Args:
            issues: List of ValidationIssue objects
            include_summary: Whether to include summary statistics
            compact: Whether to use compact format (omit empty fields)

        Returns:
            Dictionary suitable for JSON serialization
        """
        summary = ErrorFormatter._get_summary(issues) if include_summary else None

        if compact:
            issue_dicts = [i.to_compact_dict() for i in issues]
        else:
            issue_dicts = [i.to_dict() for i in issues]

        result: Dict[str, Any] = {"issues": issue_dicts}

        if include_summary:
            result["summary"] = summary

        return result

    @staticmethod
    def to_html_context(
        issues: List[ValidationIssue],
        group_by: str = "level"
    ) -> Dict[str, Any]:
        """
        Format issues for Jinja2 template context.

        Args:
            issues: List of ValidationIssue objects
            group_by: How to group issues ('level', 'category', 'none')

        Returns:
            Dictionary for template context
        """
        summary = ErrorFormatter._get_summary(issues)

        # Convert issues to dicts
        issue_dicts = [i.to_dict() for i in issues]

        # Group issues
        grouped: Dict[str, List[Dict]] = {}
        if group_by == "level":
            for level in ["critical", "error", "warning", "info"]:
                grouped[level] = [
                    i for i in issue_dicts if i["level"] == level
                ]
        elif group_by == "category":
            for issue in issue_dicts:
                cat = issue["category"]
                if cat not in grouped:
                    grouped[cat] = []
                grouped[cat].append(issue)
        else:
            grouped["all"] = issue_dicts

        return {
            "summary": summary,
            "issues": issue_dicts,
            "grouped_issues": grouped,
            "severity_icons": SEVERITY_ICONS,
            "has_critical": summary["by_level"].get("critical", 0) > 0,
            "has_errors": summary["by_level"].get("error", 0) > 0,
            "has_warnings": summary["by_level"].get("warning", 0) > 0,
            "auto_fixable_count": summary["auto_fixable"]
        }

    @staticmethod
    def _get_summary(issues: List[ValidationIssue]) -> Dict[str, Any]:
        """Generate summary statistics for issues."""
        by_level: Dict[str, int] = {
            "critical": 0,
            "error": 0,
            "warning": 0,
            "info": 0
        }
        by_category: Dict[str, int] = {}
        by_source: Dict[str, int] = {}

        auto_fixable = 0

        for issue in issues:
            # Count by level
            if issue.level in by_level:
                by_level[issue.level] += 1

            # Count by category
            if issue.category not in by_category:
                by_category[issue.category] = 0
            by_category[issue.category] += 1

            # Count by source
            if issue.source not in by_source:
                by_source[issue.source] = 0
            by_source[issue.source] += 1

            # Count auto-fixable
            if issue.auto_fixable:
                auto_fixable += 1

        return {
            "total": len(issues),
            "by_level": by_level,
            "by_category": by_category,
            "by_source": by_source,
            "auto_fixable": auto_fixable,
            "severity_score_avg": (
                sum(i.severity_score for i in issues) / len(issues)
                if issues else 0
            )
        }

    @staticmethod
    def format_for_log(issues: List[ValidationIssue]) -> str:
        """
        Format issues for log output (single line per issue).

        Args:
            issues: List of ValidationIssue objects

        Returns:
            Formatted string for logging
        """
        lines = []
        for issue in issues:
            location = f"L{issue.line_number}" if issue.line_number else "?"
            lines.append(
                f"[{issue.level.upper()}] {issue.code} @ {location}: {issue.message[:100]}"
            )
        return "\n".join(lines)

    @staticmethod
    def get_severity_color_class(level: str) -> str:
        """
        Get CSS class name for severity level.

        Args:
            level: Issue severity level

        Returns:
            CSS class name string
        """
        return {
            "critical": "text-danger fw-bold",
            "error": "text-danger",
            "warning": "text-warning",
            "info": "text-info"
        }.get(level, "text-secondary")

    @staticmethod
    def get_severity_badge_class(level: str) -> str:
        """
        Get Bootstrap badge class for severity level.

        Args:
            level: Issue severity level

        Returns:
            Bootstrap badge class string
        """
        return {
            "critical": "bg-danger",
            "error": "bg-danger",
            "warning": "bg-warning text-dark",
            "info": "bg-info text-dark"
        }.get(level, "bg-secondary")
