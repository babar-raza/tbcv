# file: tbcv/tests/test_language_detection.py
"""
Tests for language detection functionality.

These tests verify that the system correctly identifies English content
and rejects non-English content based on file paths.
"""

import pytest
from core.language_utils import is_english_content, validate_english_content_batch


class TestLanguageDetection:
    """Test suite for language detection based on file paths."""

    def test_standard_subdomain_english_paths(self):
        """Test that paths with /en/ are correctly identified as English."""
        test_cases = [
            "/docs/en/words/index.md",
            "/products/en/cells/features.md",
            "C:\\projects\\docs\\en\\api\\reference.md",
            "docs/en/getting-started.md",
            "/api/en/v1/documentation.md",
        ]

        for path in test_cases:
            is_english, reason = is_english_content(path)
            assert is_english, f"Path should be English: {path} - {reason}"
            assert "/en/" in reason.lower()

    def test_standard_subdomain_non_english_paths(self):
        """Test that paths without /en/ are correctly rejected."""
        test_cases = [
            ("/docs/fr/words/index.md", "fr"),
            ("/products/es/cells/features.md", "es"),
            ("/api/de/reference.md", "de"),
            ("/docs/it/tutorial.md", "it"),
            ("/guides/pt/quickstart.md", "pt"),
            ("/api/ru/docs.md", "ru"),
            ("/help/ja/guide.md", "ja"),
            ("/support/zh/faq.md", "zh"),
        ]

        for path, expected_lang in test_cases:
            is_english, reason = is_english_content(path)
            assert not is_english, f"Path should be non-English: {path}"
            # Reason should mention the language or missing /en/
            assert expected_lang in reason.lower() or "does not contain" in reason.lower()

    def test_blog_subdomain_english(self):
        """Test that blog paths with index.md are identified as English."""
        test_cases = [
            "/blog.aspose.net/post/index.md",
            "/blog/article/index.md",
            "blog.aspose.net/2024/january/index.md",
            "C:\\blog.aspose.net\\updates\\index.md",
        ]

        for path in test_cases:
            is_english, reason = is_english_content(path)
            assert is_english, f"Blog path should be English: {path} - {reason}"
            assert "index.md" in reason.lower()

    def test_blog_subdomain_non_english(self):
        """Test that blog paths with index.{lang}.md are rejected."""
        test_cases = [
            ("/blog.aspose.net/post/index.fr.md", "fr"),
            ("/blog/article/index.es.md", "es"),
            ("blog.aspose.net/news/index.de.md", "de"),
            ("/blog/updates/index.pt.md", "pt"),
            ("/blog/guides/index.it.md", "it"),
            ("/blog/tutorials/index.ja.md", "ja"),
        ]

        for path, expected_lang in test_cases:
            is_english, reason = is_english_content(path)
            assert not is_english, f"Blog path should be non-English: {path}"
            assert expected_lang in reason.lower()

    def test_blog_with_en_fallback(self):
        """Test that blog paths can also use /en/ pattern as fallback."""
        test_cases = [
            "/blog/en/post/article.md",
            "blog.aspose.net/en/updates/news.md",
        ]

        for path in test_cases:
            is_english, reason = is_english_content(path)
            assert is_english, f"Blog path with /en/ should be English: {path} - {reason}"

    def test_windows_paths(self):
        """Test that Windows-style paths work correctly."""
        test_cases_english = [
            "C:\\Users\\docs\\en\\words\\index.md",
            "D:\\projects\\blog.aspose.net\\post\\index.md",
        ]

        test_cases_non_english = [
            "C:\\Users\\docs\\fr\\words\\index.md",
            "D:\\projects\\blog.aspose.net\\post\\index.fr.md",
        ]

        for path in test_cases_english:
            is_english, reason = is_english_content(path)
            assert is_english, f"Windows path should be English: {path} - {reason}"

        for path in test_cases_non_english:
            is_english, reason = is_english_content(path)
            assert not is_english, f"Windows path should be non-English: {path}"

    def test_edge_cases(self):
        """Test edge cases and special scenarios."""
        # Empty path
        is_english, reason = is_english_content("")
        assert not is_english
        assert "empty" in reason.lower()

        # Path with no language indicators
        is_english, reason = is_english_content("/docs/readme.md")
        assert not is_english
        assert "does not contain" in reason.lower()

        # Path with 'en' as part of filename (not as segment)
        is_english, reason = is_english_content("/docs/fr/english-guide.md")
        assert not is_english  # Should still be rejected because /fr/ is present

    def test_batch_validation(self):
        """Test batch validation of multiple file paths."""
        file_paths = [
            "/docs/en/index.md",  # English - accept
            "/docs/fr/index.md",  # French - reject
            "/blog.aspose.net/post/index.md",  # English blog - accept
            "/blog.aspose.net/post/index.es.md",  # Spanish blog - reject
            "/api/en/reference.md",  # English - accept
            "/api/de/reference.md",  # German - reject
        ]

        valid_paths, rejected = validate_english_content_batch(file_paths)

        assert len(valid_paths) == 3, f"Expected 3 valid paths, got {len(valid_paths)}"
        assert len(rejected) == 3, f"Expected 3 rejected paths, got {len(rejected)}"

        # Check that correct paths are in valid list
        assert "/docs/en/index.md" in valid_paths
        assert "/blog.aspose.net/post/index.md" in valid_paths
        assert "/api/en/reference.md" in valid_paths

        # Check that rejected paths have reasons
        rejected_paths = [path for path, reason in rejected]
        assert "/docs/fr/index.md" in rejected_paths
        assert "/blog.aspose.net/post/index.es.md" in rejected_paths
        assert "/api/de/reference.md" in rejected_paths

    def test_realistic_paths(self):
        """Test with realistic Aspose documentation paths."""
        realistic_paths = [
            # English paths that should be accepted
            ("/home/docs/en/words/net/developer-guide/programming-with-documents/working-with-images/index.md", True),
            ("/var/www/products/en/cells/java/conversion/xlsx-to-pdf.md", True),
            ("C:\\Aspose\\docs\\en\\slides\\cpp\\getting-started\\index.md", True),
            ("/blog.aspose.net/2024/march/aspose-words-features/index.md", True),

            # Non-English paths that should be rejected
            ("/home/docs/fr/words/net/developer-guide/index.md", False),
            ("/var/www/products/de/cells/java/index.md", False),
            ("C:\\Aspose\\docs\\zh\\slides\\cpp\\index.md", False),
            ("/blog.aspose.net/2024/march/aspose-words-features/index.zh.md", False),
        ]

        for path, expected_is_english in realistic_paths:
            is_english, reason = is_english_content(path)
            assert is_english == expected_is_english, (
                f"Path: {path}\n"
                f"Expected: {expected_is_english}\n"
                f"Got: {is_english}\n"
                f"Reason: {reason}"
            )

    def test_case_sensitivity(self):
        """Test that blog detection is case-insensitive."""
        test_cases = [
            "/BLOG.ASPOSE.NET/post/index.md",
            "/Blog.Aspose.Net/article/index.md",
            "/BLOG/post/index.md",
        ]

        for path in test_cases:
            is_english, reason = is_english_content(path)
            assert is_english, f"Path should be recognized as blog (case-insensitive): {path}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
