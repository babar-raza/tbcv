# file: tbcv/core/language_utils.py
"""
Language detection utilities for TBCV system.

This module provides functions to detect if content is in English based on file paths.
Only English content should be processed by the system, as translations are done
automatically using the English source of truth.
"""

import os
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def is_english_content(file_path: str) -> tuple[bool, str]:
    """
    Determine if a file contains English content based on its path.

    Rules:
    1. For all subdomains EXCEPT blog.aspose.net:
       - English content MUST have '/en/' in the file path
       - Example: /docs/en/index.md (English)
       - Example: /docs/fr/index.md (French - reject)

    2. For blog.aspose.net subdomain:
       - English content has filename 'index.md'
       - Other languages use 'index.{lang}.md' pattern
       - Example: /blog/post/index.md (English)
       - Example: /blog/post/index.fr.md (French - reject)
       - Example: /blog/post/index.es.md (Spanish - reject)

    Args:
        file_path: Path to the file (can be absolute or relative)

    Returns:
        tuple[bool, str]: (is_english, reason)
            - is_english: True if the content is English, False otherwise
            - reason: Explanation of why it was accepted/rejected

    Examples:
        >>> is_english_content('/docs/en/words/index.md')
        (True, "File path contains '/en/' indicating English content")

        >>> is_english_content('/docs/fr/words/index.md')
        (False, "File path contains '/fr/' indicating non-English content (French)")

        >>> is_english_content('/blog.aspose.net/post/index.md')
        (True, "Blog file 'index.md' indicates English content")

        >>> is_english_content('/blog.aspose.net/post/index.fr.md')
        (False, "Blog file 'index.fr.md' indicates non-English content (French)")
    """
    if not file_path:
        return False, "Empty file path provided"

    # Normalize path separators for consistent detection
    normalized_path = file_path.replace('\\', '/')

    # Extract filename
    filename = os.path.basename(normalized_path)

    # Check if this is a blog.aspose.net path
    is_blog = 'blog.aspose.net' in normalized_path.lower() or '/blog/' in normalized_path.lower()

    if is_blog:
        # Blog subdomain: Check filename pattern
        if filename == 'index.md':
            return True, "Blog file 'index.md' indicates English content"
        elif filename.startswith('index.') and filename.endswith('.md'):
            # Extract language code from index.{lang}.md
            lang_code = filename.replace('index.', '').replace('.md', '')
            return False, f"Blog file '{filename}' indicates non-English content ({lang_code})"
        else:
            # For other blog files, check for /en/ in path as fallback
            if '/en/' in normalized_path:
                return True, "Blog file path contains '/en/' indicating English content"
            else:
                return False, f"Blog file '{filename}' does not match English pattern (expected 'index.md' or path with '/en/')"
    else:
        # All other subdomains: Must have /en/ in path
        if '/en/' in normalized_path:
            return True, "File path contains '/en/' indicating English content"
        else:
            # Try to detect language from path segments
            path_segments = normalized_path.split('/')
            # Common language codes
            lang_codes = {'fr', 'es', 'de', 'it', 'pt', 'ru', 'ja', 'zh', 'ko', 'ar', 'hi', 'nl', 'pl', 'tr', 'vi', 'th'}
            detected_langs = [seg for seg in path_segments if seg.lower() in lang_codes]

            if detected_langs:
                lang = detected_langs[0]
                return False, f"File path contains '/{lang}/' indicating non-English content"
            else:
                return False, "File path does not contain '/en/' segment required for English content"


def validate_english_content_batch(file_paths: list[str]) -> tuple[list[str], list[tuple[str, str]]]:
    """
    Validate a batch of file paths for English content.

    Args:
        file_paths: List of file paths to check

    Returns:
        tuple[list[str], list[tuple[str, str]]]:
            - valid_paths: List of file paths that contain English content
            - rejected: List of tuples (file_path, reason) for rejected files

    Example:
        >>> valid, rejected = validate_english_content_batch([
        ...     '/docs/en/index.md',
        ...     '/docs/fr/index.md',
        ...     '/blog/post/index.md'
        ... ])
        >>> len(valid)
        2
        >>> len(rejected)
        1
    """
    valid_paths = []
    rejected = []

    for file_path in file_paths:
        is_english, reason = is_english_content(file_path)
        if is_english:
            valid_paths.append(file_path)
            logger.debug(f"Accepted English content: {file_path} - {reason}")
        else:
            rejected.append((file_path, reason))
            logger.info(f"Rejected non-English content: {file_path} - {reason}")

    return valid_paths, rejected


def log_language_rejection(file_path: str, reason: str, logger_instance: Optional[logging.Logger] = None):
    """
    Log a language rejection with consistent formatting.

    Args:
        file_path: Path to the rejected file
        reason: Reason for rejection
        logger_instance: Optional logger instance to use (defaults to module logger)
    """
    log = logger_instance or logger
    log.warning(f"Language check failed: {file_path} - {reason}")
