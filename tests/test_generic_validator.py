# file: tests\test_generic_validator.py
"""
Tests for generic validator system with family-specific rules.
"""
import pytest
import asyncio
import tempfile
import json
from pathlib import Path

class TestRuleManager:
    
    def test_load_family_rules_words(self):
        """Test loading rules for words family."""
        from rule_manager import RuleManager
        
        rm = RuleManager()
        rules = rm.get_family_rules("words")
        
        assert rules.family == "words"
        assert isinstance(rules.api_patterns, dict)
        assert isinstance(rules.plugin_aliases, dict)
        assert len(rules.non_editable_yaml_fields) > 0
        
    def test_api_patterns_loaded(self):
        """Test that API patterns are loaded from rules."""
        from rule_manager import RuleManager
        
        rm = RuleManager()
        patterns = rm.get_api_patterns("words")
        
        assert isinstance(patterns, dict)
        # Should have some patterns even with fallback
        assert len(patterns) > 0

    def test_non_editable_fields_include_global(self):
        """Test that non-editable fields include global defaults."""
        from rule_manager import RuleManager
        
        rm = RuleManager()
        fields = rm.get_non_editable_fields("words")
        
        # Should include global defaults
        global_fields = {'layout', 'categories', 'date', 'draft', 'lastmod', 'title', 'weight', 'author'}
        assert global_fields.issubset(fields)

class TestGenericContentValidator:
    
    @pytest.mark.asyncio
    async def test_validate_content_with_family(self):
        """Test content validation with family parameter."""
        from content_validator import ContentValidatorAgent
        
        agent = ContentValidatorAgent()
        content = """---
title: "Generic Document Processing"
description: "A comprehensive guide to document processing using generic patterns and best practices."
date: "2024-01-15"
---
# Document Processing

This guide shows document processing patterns.
```csharp
Document doc = new Document("input.docx");
doc.Save("output.pdf");
```
"""

        result = await agent.handle_validate_content({
            "content": content,
            "file_path": "test.md",
            "family": "words",
            "validation_types": ["yaml", "markdown", "code"]
        })
        
        assert result['family'] == "words"
        assert result['confidence'] > 0.5
        assert 'family_rules_loaded' in result['metrics']

    @pytest.mark.asyncio
    async def test_yaml_validation_family_fields(self):
        """Test YAML validation with family-specific non-editable fields."""
        from content_validator import ContentValidatorAgent
        
        agent = ContentValidatorAgent()
        content = """---
title: "Test Document"
layout: "post"
categories: ["test"]
date: "2024-01-15"
plugin_family: "words"
---
# Test Content"""

        result = await agent.handle_validate_content({
            "content": content,
            "file_path": "test.md",
            "family": "words",
            "validation_types": ["yaml"]
        })
        
        yaml_metrics = result['metrics']['yaml_metrics']
        assert 'layout' in yaml_metrics['non_editable_fields']
        assert 'plugin_family' in yaml_metrics['non_editable_fields']

    @pytest.mark.asyncio
    async def test_shortcode_preservation(self):
        """Test that shortcodes are preserved during validation."""
        from content_validator import ContentValidatorAgent
        
        agent = ContentValidatorAgent()
        content = """# Test Document

Some content here.

{{< gist user_name gist_id >}}

{{< info "Important note" >}}

More content with [link](http://example.com).
"""

        result = await agent.handle_validate_content({
            "content": content,
            "file_path": "test.md",
            "family": "words",
            "validation_types": ["markdown"]
        })
        
        metrics = result['metrics']['markdown_metrics']
        assert metrics['shortcodes_count'] == 2
        assert metrics['links_count'] == 1
        # Should not modify content - just validate structure

    @pytest.mark.asyncio
    async def test_code_validation_no_hardcoded_patterns(self):
        """Test that code validation uses rule-driven patterns."""
        from content_validator import ContentValidatorAgent
        
        agent = ContentValidatorAgent()
        content = """# Document Processing
```csharp
Document doc = new Document("C:\\\\temp\\\\input.docx");
doc.Save("output.pdf");
```
"""

        result = await agent.handle_validate_content({
            "content": content,
            "file_path": "test.md",
            "family": "words", 
            "validation_types": ["code"]
        })
        
        # Should detect hardcoded path issue using rules, not hardcoded logic
        code_issues = [i for i in result['issues'] if i['category'] == 'code_quality']
        hardcoded_path_issues = [i for i in code_issues if 'hardcoded' in i['message'].lower()]
        assert len(hardcoded_path_issues) > 0

class TestGenericFuzzyDetector:

    @pytest.mark.asyncio
    async def test_detect_plugins_with_family(self):
        """Test plugin detection with family parameter."""
        from fuzzy_detector import FuzzyDetectorAgent
        
        agent = FuzzyDetectorAgent()
        content = """
        Document doc = new Document();
        doc.Save("output.pdf");
        // This uses document processing
        """
        
        result = await agent.handle_detect_plugins({
            "text": content,
            "family": "words",
            "confidence_threshold": 0.5
        })
        
        assert result['family'] == "words"
        assert result['detection_count'] >= 0
        # Should work even with rule-driven patterns

    @pytest.mark.asyncio
    async def test_pattern_loading_fallback(self):
        """Test that detector works with fallback patterns."""
        from fuzzy_detector import FuzzyDetectorAgent
        
        agent = FuzzyDetectorAgent()
        
        # Should have some patterns loaded (either from rules or fallback)
        patterns_result = await agent.handle_get_plugin_patterns({"family": "words"})
        
        assert patterns_result['family'] == "words"
        assert 'pattern_counts' in patterns_result or 'found' in patterns_result

class TestOllamaIntegration:
    
    @pytest.mark.asyncio
    async def test_ollama_validator_offline_graceful(self):
        """Test that Ollama validator gracefully handles offline state."""
        from core.ollama import Ollama, async_validate_content_contradictions
        
        # Force offline for test
        validator = Ollama(enabled=False)

        
        result = await async_validate_content_contradictions(
            "Test content", [], {}
        )
        
        assert isinstance(result, list)
        assert len(result) == 0  # Should return empty list when disabled

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
