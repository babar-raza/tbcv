# file: tests/core/test_error_formatter.py
"""Tests for ErrorFormatter class."""

import pytest
from agents.validators.base_validator import ValidationIssue
from core.error_formatter import ErrorFormatter, Colors, SEVERITY_ICONS


# --- Test Fixtures ---

@pytest.fixture
def sample_issues():
    """Create sample ValidationIssue list for testing."""
    return [
        ValidationIssue(
            level="error",
            category="syntax",
            message="Missing closing bracket",
            code="SYN_BRACKET",
            line_number=10,
            column=5,
            suggestion="Add closing bracket",
            context_snippet="function test() {",
            auto_fixable=True
        ),
        ValidationIssue(
            level="warning",
            category="style",
            message="Line too long",
            code="STYLE_LINE_LEN",
            line_number=25,
            suggestion="Break line into multiple lines",
            fix_example="const x = \\n    longValue;"
        ),
        ValidationIssue(
            level="critical",
            category="security",
            message="SQL injection vulnerability",
            code="SEC_SQL_INJ",
            line_number=42,
            context_snippet="query = 'SELECT * FROM users WHERE id=' + user_input"
        ),
        ValidationIssue(
            level="info",
            category="documentation",
            message="Missing docstring",
            code="DOC_MISSING",
            line_number=1
        )
    ]


@pytest.fixture
def empty_issues():
    """Empty issue list."""
    return []


# --- CLI Output Tests ---

class TestToCli:
    """Tests for to_cli method."""

    def test_empty_issues_returns_no_issues_message(self, empty_issues):
        """Empty list should return 'No issues found'."""
        result = ErrorFormatter.to_cli(empty_issues)
        assert result == "No issues found."

    def test_colorized_output_includes_ansi_codes(self, sample_issues):
        """Colorized output should include ANSI escape codes."""
        result = ErrorFormatter.to_cli(sample_issues, colorized=True)
        assert "\033[" in result  # ANSI escape sequence

    def test_non_colorized_output_excludes_ansi_codes(self, sample_issues):
        """Non-colorized output should not include ANSI codes."""
        result = ErrorFormatter.to_cli(sample_issues, colorized=False)
        assert "\033[" not in result

    def test_sorted_by_severity(self, sample_issues):
        """Issues should be sorted by severity (critical first)."""
        result = ErrorFormatter.to_cli(sample_issues, colorized=False)
        lines = result.split("\n")
        # Find issue lines (start with number and period)
        issue_lines = [l for l in lines if l and l[0].isdigit() and ". " in l]
        # First issue should be critical
        assert "CRITICAL" in issue_lines[0]

    def test_max_issues_limits_output(self, sample_issues):
        """max_issues should limit displayed issues."""
        result = ErrorFormatter.to_cli(sample_issues, max_issues=2, colorized=False)
        assert "... and 2 more issues" in result

    def test_show_context_includes_snippet(self, sample_issues):
        """show_context should include context snippets."""
        result = ErrorFormatter.to_cli(sample_issues, show_context=True, colorized=False)
        assert "Context:" in result

    def test_hide_context_excludes_snippet(self, sample_issues):
        """show_context=False should exclude context snippets."""
        result = ErrorFormatter.to_cli(sample_issues, show_context=False, colorized=False)
        # Count context occurrences - should be 0 when hidden
        assert result.count("Context:") == 0

    def test_show_suggestions_includes_suggestion(self, sample_issues):
        """show_suggestions should include suggestions."""
        result = ErrorFormatter.to_cli(sample_issues, show_suggestions=True, colorized=False)
        assert "Suggestion:" in result

    def test_hide_suggestions_excludes_suggestion(self, sample_issues):
        """show_suggestions=False should exclude suggestions."""
        result = ErrorFormatter.to_cli(sample_issues, show_suggestions=False, colorized=False)
        assert result.count("Suggestion:") == 0

    def test_auto_fixable_indicator(self, sample_issues):
        """Auto-fixable issues should be marked."""
        result = ErrorFormatter.to_cli(sample_issues, colorized=False)
        assert "[Auto-fixable]" in result

    def test_summary_header(self, sample_issues):
        """Output should include summary header."""
        result = ErrorFormatter.to_cli(sample_issues, colorized=False)
        assert "Validation Results" in result
        assert "Total: 4 issues" in result

    def test_line_column_location(self, sample_issues):
        """Location should show line and column."""
        result = ErrorFormatter.to_cli(sample_issues, colorized=False)
        assert "at line 10:5" in result

    def test_issue_code_displayed(self, sample_issues):
        """Issue code should be displayed."""
        result = ErrorFormatter.to_cli(sample_issues, colorized=False)
        assert "[SYN_BRACKET]" in result


# --- JSON Output Tests ---

class TestToJson:
    """Tests for to_json method."""

    def test_returns_dict_with_issues(self, sample_issues):
        """Should return dict with issues key."""
        result = ErrorFormatter.to_json(sample_issues)
        assert "issues" in result
        assert len(result["issues"]) == 4

    def test_includes_summary(self, sample_issues):
        """Should include summary when requested."""
        result = ErrorFormatter.to_json(sample_issues, include_summary=True)
        assert "summary" in result
        assert result["summary"]["total"] == 4

    def test_excludes_summary(self, sample_issues):
        """Should exclude summary when requested."""
        result = ErrorFormatter.to_json(sample_issues, include_summary=False)
        assert "summary" not in result

    def test_summary_by_level(self, sample_issues):
        """Summary should count issues by level."""
        result = ErrorFormatter.to_json(sample_issues)
        by_level = result["summary"]["by_level"]
        assert by_level["critical"] == 1
        assert by_level["error"] == 1
        assert by_level["warning"] == 1
        assert by_level["info"] == 1

    def test_summary_by_category(self, sample_issues):
        """Summary should count issues by category."""
        result = ErrorFormatter.to_json(sample_issues)
        by_category = result["summary"]["by_category"]
        assert "syntax" in by_category
        assert "security" in by_category

    def test_summary_auto_fixable_count(self, sample_issues):
        """Summary should count auto-fixable issues."""
        result = ErrorFormatter.to_json(sample_issues)
        assert result["summary"]["auto_fixable"] == 1

    def test_compact_mode(self, sample_issues):
        """Compact mode should use compact dict representation."""
        result = ErrorFormatter.to_json(sample_issues, compact=True)
        # Compact dicts should exist
        assert len(result["issues"]) == 4

    def test_empty_issues(self, empty_issues):
        """Empty issues should return empty list."""
        result = ErrorFormatter.to_json(empty_issues)
        assert result["issues"] == []
        assert result["summary"]["total"] == 0


# --- HTML Context Tests ---

class TestToHtmlContext:
    """Tests for to_html_context method."""

    def test_returns_dict_with_required_keys(self, sample_issues):
        """Should return dict with all required keys."""
        result = ErrorFormatter.to_html_context(sample_issues)
        assert "summary" in result
        assert "issues" in result
        assert "grouped_issues" in result
        assert "severity_icons" in result
        assert "has_critical" in result
        assert "has_errors" in result
        assert "has_warnings" in result
        assert "auto_fixable_count" in result

    def test_group_by_level(self, sample_issues):
        """Grouping by level should create level keys."""
        result = ErrorFormatter.to_html_context(sample_issues, group_by="level")
        grouped = result["grouped_issues"]
        assert "critical" in grouped
        assert "error" in grouped
        assert "warning" in grouped
        assert "info" in grouped

    def test_group_by_category(self, sample_issues):
        """Grouping by category should create category keys."""
        result = ErrorFormatter.to_html_context(sample_issues, group_by="category")
        grouped = result["grouped_issues"]
        assert "syntax" in grouped
        assert "security" in grouped

    def test_group_by_none(self, sample_issues):
        """Grouping by 'none' should put all in 'all' key."""
        result = ErrorFormatter.to_html_context(sample_issues, group_by="none")
        grouped = result["grouped_issues"]
        assert "all" in grouped
        assert len(grouped["all"]) == 4

    def test_has_critical_flag(self, sample_issues):
        """has_critical should be True when critical issues exist."""
        result = ErrorFormatter.to_html_context(sample_issues)
        assert result["has_critical"] is True

    def test_has_errors_flag(self, sample_issues):
        """has_errors should be True when error issues exist."""
        result = ErrorFormatter.to_html_context(sample_issues)
        assert result["has_errors"] is True

    def test_has_warnings_flag(self, sample_issues):
        """has_warnings should be True when warning issues exist."""
        result = ErrorFormatter.to_html_context(sample_issues)
        assert result["has_warnings"] is True

    def test_severity_icons_included(self, sample_issues):
        """Severity icons dict should be included."""
        result = ErrorFormatter.to_html_context(sample_issues)
        icons = result["severity_icons"]
        assert "critical" in icons
        assert "error" in icons


# --- Summary Tests ---

class TestGetSummary:
    """Tests for _get_summary static method."""

    def test_total_count(self, sample_issues):
        """Total should equal issue count."""
        result = ErrorFormatter._get_summary(sample_issues)
        assert result["total"] == 4

    def test_severity_score_avg(self, sample_issues):
        """Average severity score should be calculated."""
        result = ErrorFormatter._get_summary(sample_issues)
        assert "severity_score_avg" in result
        assert result["severity_score_avg"] > 0

    def test_by_source(self, sample_issues):
        """Should count by source."""
        result = ErrorFormatter._get_summary(sample_issues)
        assert "by_source" in result
        assert "rule_based" in result["by_source"]

    def test_empty_issues_avg_zero(self, empty_issues):
        """Empty issues should have zero average."""
        result = ErrorFormatter._get_summary(empty_issues)
        assert result["severity_score_avg"] == 0


# --- Log Format Tests ---

class TestFormatForLog:
    """Tests for format_for_log static method."""

    def test_single_line_per_issue(self, sample_issues):
        """Each issue should be on single line."""
        result = ErrorFormatter.format_for_log(sample_issues)
        lines = result.strip().split("\n")
        assert len(lines) == 4

    def test_includes_level(self, sample_issues):
        """Log line should include level."""
        result = ErrorFormatter.format_for_log(sample_issues)
        assert "[ERROR]" in result
        assert "[WARNING]" in result

    def test_includes_code(self, sample_issues):
        """Log line should include issue code."""
        result = ErrorFormatter.format_for_log(sample_issues)
        assert "SYN_BRACKET" in result

    def test_includes_line_number(self, sample_issues):
        """Log line should include line number."""
        result = ErrorFormatter.format_for_log(sample_issues)
        assert "L10" in result

    def test_truncates_message(self):
        """Long messages should be truncated."""
        issues = [
            ValidationIssue(
                level="error",
                category="test",
                message="A" * 200  # Very long message
            )
        ]
        result = ErrorFormatter.format_for_log(issues)
        # Should be truncated to 100 chars
        assert len(result.split(": ")[-1]) <= 100


# --- CSS Class Tests ---

class TestSeverityColorClass:
    """Tests for get_severity_color_class method."""

    def test_critical_class(self):
        """Critical should return danger bold class."""
        result = ErrorFormatter.get_severity_color_class("critical")
        assert "text-danger" in result
        assert "fw-bold" in result

    def test_error_class(self):
        """Error should return danger class."""
        result = ErrorFormatter.get_severity_color_class("error")
        assert "text-danger" in result

    def test_warning_class(self):
        """Warning should return warning class."""
        result = ErrorFormatter.get_severity_color_class("warning")
        assert "text-warning" in result

    def test_info_class(self):
        """Info should return info class."""
        result = ErrorFormatter.get_severity_color_class("info")
        assert "text-info" in result

    def test_unknown_class(self):
        """Unknown level should return secondary class."""
        result = ErrorFormatter.get_severity_color_class("unknown")
        assert "text-secondary" in result


class TestSeverityBadgeClass:
    """Tests for get_severity_badge_class method."""

    def test_critical_badge(self):
        """Critical should return danger badge."""
        result = ErrorFormatter.get_severity_badge_class("critical")
        assert "bg-danger" in result

    def test_error_badge(self):
        """Error should return danger badge."""
        result = ErrorFormatter.get_severity_badge_class("error")
        assert "bg-danger" in result

    def test_warning_badge(self):
        """Warning should return warning badge."""
        result = ErrorFormatter.get_severity_badge_class("warning")
        assert "bg-warning" in result

    def test_info_badge(self):
        """Info should return info badge."""
        result = ErrorFormatter.get_severity_badge_class("info")
        assert "bg-info" in result


# --- Constants Tests ---

class TestConstants:
    """Tests for module constants."""

    def test_colors_has_reset(self):
        """Colors should have RESET code."""
        assert Colors.RESET == "\033[0m"

    def test_severity_icons_complete(self):
        """All severity levels should have icons."""
        assert "critical" in SEVERITY_ICONS
        assert "error" in SEVERITY_ICONS
        assert "warning" in SEVERITY_ICONS
        assert "info" in SEVERITY_ICONS
