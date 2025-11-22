# file: agents/validators/link_validator.py
"""
Link Validator Agent - Validates links in content.
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
from core.logging import get_logger

logger = get_logger(__name__)


class LinkValidatorAgent(BaseValidatorAgent):
    """Validates links and URLs in content."""

    def __init__(self, agent_id: Optional[str] = None):
        super().__init__(agent_id or "link_validator")

    def get_validation_type(self) -> str:
        return "links"

    async def validate(self, content: str, context: Dict[str, Any]) -> ValidationResult:
        """Validate links in content."""
        issues: List[ValidationIssue] = []
        auto_fixable = 0
        lines = content.split('\n')

        # Extract all links
        links = self._extract_links(lines)

        # Validate each link
        for link in links:
            link_issues = self._validate_link(link)
            issues.extend(link_issues)

        confidence = max(0.6, 1.0 - (len(issues) * 0.15))

        return ValidationResult(
            confidence=confidence,
            issues=issues,
            auto_fixable_count=auto_fixable,
            metrics={
                "links_found": len(links),
                "issues_count": len(issues)
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

    def _validate_link(self, link: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate a single link."""
        issues = []
        url = link['url']
        line = link['line']

        # Check for empty URL
        if not url.strip():
            issues.append(ValidationIssue(
                level="error",
                category="link_empty_url",
                message=f"Empty URL at line {line}",
                line_number=line,
                suggestion="Add a valid URL"
            ))
            return issues

        # Check for malformed URLs
        try:
            parsed = urlparse(url)

            # Check for missing protocol (http/https)
            if parsed.scheme and parsed.scheme not in ['http', 'https', 'ftp', 'mailto']:
                if not url.startswith('#') and not url.startswith('/'):  # Allow anchors and relative paths
                    issues.append(ValidationIssue(
                        level="warning",
                        category="link_unknown_protocol",
                        message=f"Unknown protocol '{parsed.scheme}' at line {line}",
                        line_number=line,
                        suggestion="Use http:// or https:// for web links"
                    ))

            # Check for spaces in URL
            if ' ' in url:
                issues.append(ValidationIssue(
                    level="error",
                    category="link_spaces_in_url",
                    message=f"Spaces in URL at line {line}",
                    line_number=line,
                    suggestion="Replace spaces with %20 or hyphens"
                ))

            # Check for localhost/development URLs
            if parsed.netloc in ['localhost', '127.0.0.1'] or parsed.netloc.startswith('localhost:'):
                issues.append(ValidationIssue(
                    level="warning",
                    category="link_localhost",
                    message=f"Localhost URL at line {line}",
                    line_number=line,
                    suggestion="Replace with production URL before publishing"
                ))

            # Check for broken reference style links
            if url.startswith('[') and url.endswith(']'):
                issues.append(ValidationIssue(
                    level="error",
                    category="link_broken_reference",
                    message=f"Broken reference-style link at line {line}",
                    line_number=line,
                    suggestion="Define the reference or use direct URL"
                ))

        except Exception as e:
            issues.append(ValidationIssue(
                level="error",
                category="link_malformed",
                message=f"Malformed URL at line {line}: {str(e)}",
                line_number=line,
                suggestion="Check URL syntax"
            ))

        return issues
