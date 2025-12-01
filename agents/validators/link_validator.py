# file: agents/validators/link_validator.py
"""
Link Validator Agent - Validates links in content.
Uses ConfigLoader for configuration-driven validation.
"""

from __future__ import annotations
import re
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse

from agents.validators.base_validator import (
    BaseValidatorAgent,
    ValidationIssue,
    ValidationResult
)
from core.config_loader import ConfigLoader, get_config_loader
from core.logging import get_logger

logger = get_logger(__name__)


class LinkValidatorAgent(BaseValidatorAgent):
    """Validates links and URLs in content."""

    def __init__(self, agent_id: Optional[str] = None, config_loader: Optional[ConfigLoader] = None):
        super().__init__(agent_id or "link_validator")
        self._config_loader = config_loader or get_config_loader()
        self._config = self._config_loader.load("links")

    def get_validation_type(self) -> str:
        return "links"

    async def validate(self, content: str, context: Dict[str, Any]) -> ValidationResult:
        """Validate links in content."""
        issues: List[ValidationIssue] = []
        auto_fixable = 0
        lines = content.split('\n')

        # Get profile and family from context
        profile = context.get("profile", self._config.profile)
        family = context.get("family")

        # Get active rules for this profile/family
        active_rules = self._config_loader.get_rules("links", profile=profile, family=family)
        active_rule_ids = {r.id for r in active_rules}
        rule_levels = {r.id: r.level for r in active_rules}
        rule_params = {r.id: r.params for r in active_rules}

        # Extract all links
        links = self._extract_links(lines)

        # Validate each link
        for link in links:
            link_issues = self._validate_link(link, active_rule_ids, rule_levels, rule_params)
            issues.extend(link_issues)

        confidence = max(0.6, 1.0 - (len(issues) * 0.15))

        return ValidationResult(
            confidence=confidence,
            issues=issues,
            auto_fixable_count=auto_fixable,
            metrics={
                "links_found": len(links),
                "issues_count": len(issues),
                "profile": profile,
                "family": family
            }
        )

    def _extract_links(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Extract all links from content."""
        links = []
        # Match markdown links: [text](url) and images: ![alt](url)
        link_pattern = re.compile(r'!?\[([^\]]*)\]\(([^)]*)\)')

        for i, line in enumerate(lines):
            matches = link_pattern.finditer(line)
            for match in matches:
                is_image = match.group(0).startswith('!')
                text = match.group(1)
                url = match.group(2)
                links.append({
                    'line': i + 1,
                    'text': text,
                    'url': url,
                    'is_image': is_image
                })

        return links

    def _validate_link(
        self,
        link: Dict[str, Any],
        active_rule_ids: set,
        rule_levels: Dict[str, str],
        rule_params: Dict[str, Dict]
    ) -> List[ValidationIssue]:
        """Validate a single link."""
        issues = []
        url = link['url']
        line = link['line']

        # Check for empty URL
        if "empty_url" in active_rule_ids and not url.strip():
            level = rule_levels.get("empty_url", "error")
            issues.append(ValidationIssue(
                level=level,
                category="link_empty_url",
                message=f"Empty URL at line {line}",
                line_number=line,
                suggestion="Add a valid URL"
            ))
            return issues

        # Check for malformed URLs
        try:
            parsed = urlparse(url)

            # Check for invalid scheme
            if "invalid_scheme" in active_rule_ids:
                allowed_schemes = rule_params.get("invalid_scheme", {}).get("allowed", ["http", "https", "mailto", "ftp", "tel"])
                if parsed.scheme and parsed.scheme not in allowed_schemes:
                    if not url.startswith('#') and not url.startswith('/'):  # Allow anchors and relative paths
                        level = rule_levels.get("invalid_scheme", "warning")
                        issues.append(ValidationIssue(
                            level=level,
                            category="link_unknown_protocol",
                            message=f"Unknown protocol '{parsed.scheme}' at line {line}",
                            line_number=line,
                            suggestion="Use http:// or https:// for web links"
                        ))

            # Check for spaces in URL
            if "spaces_in_url" in active_rule_ids and ' ' in url:
                level = rule_levels.get("spaces_in_url", "error")
                issues.append(ValidationIssue(
                    level=level,
                    category="link_spaces_in_url",
                    message=f"Spaces in URL at line {line}",
                    line_number=line,
                    suggestion="Replace spaces with %20 or hyphens"
                ))

            # Check for localhost/development URLs
            if "localhost_link" in active_rule_ids:
                if parsed.netloc in ['localhost', '127.0.0.1'] or parsed.netloc.startswith('localhost:'):
                    level = rule_levels.get("localhost_link", "warning")
                    issues.append(ValidationIssue(
                        level=level,
                        category="link_localhost",
                        message=f"Localhost URL at line {line}",
                        line_number=line,
                        suggestion="Replace with production URL before publishing"
                    ))

            # Check for broken reference style links
            if "broken_reference" in active_rule_ids:
                if url.startswith('[') and url.endswith(']'):
                    level = rule_levels.get("broken_reference", "error")
                    issues.append(ValidationIssue(
                        level=level,
                        category="link_broken_reference",
                        message=f"Broken reference-style link at line {line}",
                        line_number=line,
                        suggestion="Define the reference or use direct URL"
                    ))

            # Check for placeholder URLs
            if "placeholder_url" in active_rule_ids:
                patterns = rule_params.get("placeholder_url", {}).get("patterns", ["#$", "TODO", "example.com"])
                for pattern in patterns:
                    if pattern.lower() in url.lower():
                        level = rule_levels.get("placeholder_url", "warning")
                        issues.append(ValidationIssue(
                            level=level,
                            category="link_placeholder",
                            message=f"Placeholder URL detected at line {line}",
                            line_number=line,
                            suggestion="Replace placeholder with actual URL"
                        ))
                        break

        except Exception as e:
            issues.append(ValidationIssue(
                level="error",
                category="link_malformed",
                message=f"Malformed URL at line {line}: {str(e)}",
                line_number=line,
                suggestion="Check URL syntax"
            ))

        return issues
