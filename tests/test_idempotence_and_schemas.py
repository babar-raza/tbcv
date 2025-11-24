# file: tbcv/tests/test_idempotence_and_schemas.py
"""
Tests for idempotence (A04, A23) and schema validation (A03).
Ensures deterministic execution and proper JSON Schema enforcement.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from agents.content_enhancer import ContentEnhancerAgent
from main import _validate_schemas


@pytest.fixture
def sample_content():
    """Sample markdown content for testing."""
    return """---
title: Test Document
author: Test Author
---

# Test Document

This document uses Document class for operations.

```csharp
Document doc = new Document();
doc.Save("output.docx");
```

This requires the Document Converter plugin.
"""

@pytest.fixture 
def detected_plugins():
    """Sample detected plugins."""
    return [
        {
            "plugin_id": "document_converter",
            "plugin_name": "Document Converter",
            "confidence": 0.9,
            "matched_text": "Document",
            "position": 50
        }
    ]

@pytest.fixture
def enhancer_agent():
    """Create content enhancer agent."""
    return ContentEnhancerAgent("test_enhancer")

@pytest.mark.asyncio
async def test_idempotent_enhancement_a04(sample_content, detected_plugins, enhancer_agent):
    """
    Test A04: Ensure enhancement operations are idempotent.
    Running the same enhancement twice should produce no additional changes.
    """
    enhancement_params = {
        "content": sample_content,
        "detected_plugins": detected_plugins,
        "enhancement_types": ["plugin_links", "info_text"]
    }
    
    # First enhancement run
    result1 = await enhancer_agent.handle_enhance_content(enhancement_params)
    enhanced_content1 = result1["enhanced_content"]
    
    # Second enhancement run on already enhanced content
    enhancement_params["content"] = enhanced_content1
    result2 = await enhancer_agent.handle_enhance_content(enhancement_params)
    enhanced_content2 = result2["enhanced_content"]
    
    # Should detect that content was already enhanced
    assert result2["statistics"].get("already_enhanced", False), "Second run should detect content was already enhanced"
    assert enhanced_content1 == enhanced_content2, "Second enhancement should produce identical content"
    assert result2["statistics"]["total_enhancements"] == 0, "Second run should make no additional enhancements"
    
    print("A04 Idempotent enhancement verified")

@pytest.mark.asyncio 
async def test_deterministic_hashing_a23(sample_content, detected_plugins, enhancer_agent):
    """
    Test A23: Ensure deterministic hashing for idempotence checks.
    Same inputs should always produce the same hash.
    """
    # Compute hash multiple times with same inputs
    hash1 = enhancer_agent._compute_content_hash(sample_content, detected_plugins, ["plugin_links"])
    hash2 = enhancer_agent._compute_content_hash(sample_content, detected_plugins, ["plugin_links"])
    hash3 = enhancer_agent._compute_content_hash(sample_content, detected_plugins, ["plugin_links"])
    
    assert hash1 == hash2 == hash3, "Same inputs should produce identical hashes"
    
    # Different inputs should produce different hashes
    different_content = sample_content + "\nExtra content"
    hash4 = enhancer_agent._compute_content_hash(different_content, detected_plugins, ["plugin_links"])
    
    assert hash1 != hash4, "Different inputs should produce different hashes"
    
    # Different plugin order should produce same hash (deterministic sorting)
    shuffled_plugins = detected_plugins[::-1]  # Reverse order
    hash5 = enhancer_agent._compute_content_hash(sample_content, shuffled_plugins, ["plugin_links"])
    
    assert hash1 == hash5, "Plugin order should not affect hash (deterministic sorting)"
    
    print("A23 Deterministic hashing verified")

@pytest.mark.asyncio
async def test_enhancement_marker_tracking(sample_content, detected_plugins, enhancer_agent):
    """
    Test that enhancement markers are properly added and detected.
    """
    # Check marker detection on unenhanced content
    test_hash = "abc123"
    assert not enhancer_agent._is_already_enhanced(sample_content, test_hash)
    
    # Add marker and verify detection
    marked_content = enhancer_agent._add_enhancement_marker(sample_content, test_hash)
    assert enhancer_agent._is_already_enhanced(marked_content, test_hash)
    
    # Different hash should not be detected
    different_hash = "xyz789"
    assert not enhancer_agent._is_already_enhanced(marked_content, different_hash)
    
    # Adding same marker twice should not duplicate
    double_marked = enhancer_agent._add_enhancement_marker(marked_content, test_hash)
    marker_count = double_marked.count(f"<!-- TBCV:enhanced:{test_hash} -->")
    assert marker_count == 1, "Marker should only appear once even when added multiple times"
    
    print("Enhancement marker tracking verified")

def test_schema_validation_success_a03():
    """
    Test A03: Proper JSON Schema validation should pass for valid truth tables.
    """
    # Create temporary valid truth table file
    valid_truth_data = {
        "plugins": [
            {
                "plugin_id": "document_converter",
                "plugin_name": "Document Converter",
                "aliases": ["Document", "Doc"],
                "confidence_threshold": 0.8
            }
        ]
    }
    
    valid_rule_data = {
        "rules": [
            {
                "rule_id": "check_plugins",
                "description": "Check for plugin usage",
                "severity": "medium",
                "enabled": True
            }
        ]
    }
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create truth and rule files
        truth_file = temp_path / "truth" / "test_truth.json"
        truth_file.parent.mkdir(exist_ok=True)
        truth_file.write_text(json.dumps(valid_truth_data, indent=2))
        
        rule_file = temp_path / "rules" / "test_rules.json" 
        rule_file.parent.mkdir(exist_ok=True)
        rule_file.write_text(json.dumps(valid_rule_data, indent=2))
        
        # Mock the project root to point to our temp directory
        with patch('tbcv.main.Path') as mock_path:
            mock_path.__file__ = temp_path / "tbcv" / "main.py"
            mock_path.return_value.parent.parent = temp_path
            
            # Should validate successfully
            result = _validate_schemas()
            assert result, "Valid schemas should pass validation"
    
    print("A03 Schema validation success verified")

def test_schema_validation_failure_a03():
    """
    Test A03: Schema validation should fail for invalid truth tables.
    """
    # Create temporary invalid truth table file
    invalid_truth_data = {
        "plugins": [
            {
                # Missing required plugin_id
                "plugin_name": "Document Converter",
                "confidence_threshold": "invalid_number"  # Should be number
            }
        ]
    }
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create invalid truth file
        truth_file = temp_path / "truth" / "invalid_truth.json"
        truth_file.parent.mkdir(exist_ok=True)
        truth_file.write_text(json.dumps(invalid_truth_data, indent=2))
        
        # Mock the project root
        with patch('tbcv.main.Path') as mock_path:
            mock_path.__file__ = temp_path / "tbcv" / "main.py"  
            mock_path.return_value.parent.parent = temp_path
            
            # Should fail validation
            result = _validate_schemas()
            assert not result, "Invalid schemas should fail validation"
    
    print("A03 Schema validation failure detection verified")

def test_schema_validation_json_error_a03():
    """
    Test A03: Schema validation should handle JSON syntax errors.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create invalid JSON file
        truth_file = temp_path / "truth" / "syntax_error.json"
        truth_file.parent.mkdir(exist_ok=True)
        truth_file.write_text('{"invalid": json syntax}')  # Invalid JSON
        
        # Mock the project root
        with patch('tbcv.main.Path') as mock_path:
            mock_path.__file__ = temp_path / "tbcv" / "main.py"
            mock_path.return_value.parent.parent = temp_path
            
            # Should fail validation due to JSON syntax error
            result = _validate_schemas()
            assert not result, "JSON syntax errors should fail validation"
    
    print("A03 JSON syntax error handling verified")

@pytest.mark.asyncio
async def test_enhancement_preserves_structure(sample_content, detected_plugins, enhancer_agent):
    """
    Test that enhancement preserves document structure (A16, P07).
    """
    enhancement_params = {
        "content": sample_content,
        "detected_plugins": detected_plugins,
        "enhancement_types": ["plugin_links", "info_text"],
        "preview_only": True
    }
    
    result = await enhancer_agent.handle_enhance_content(enhancement_params)
    enhanced_content = result["enhanced_content"]
    
    # Check that key structural elements are preserved
    original_headers = sample_content.count('#')
    enhanced_headers = enhanced_content.count('#')
    assert original_headers == enhanced_headers, "Header count should be preserved"
    
    original_code_blocks = sample_content.count('```')
    enhanced_code_blocks = enhanced_content.count('```')
    assert original_code_blocks == enhanced_code_blocks, "Code block count should be preserved"
    
    # YAML frontmatter should be preserved
    assert enhanced_content.startswith('---'), "YAML frontmatter should be preserved"
    
    # Original content structure should be identifiable in enhanced version
    import re
    original_structure = re.sub(r'\s+', ' ', sample_content).strip()
    enhanced_structure = re.sub(r'\s+', ' ', enhanced_content).strip()
    
    # Most of the original text should still be present
    original_words = set(original_structure.split())
    enhanced_words = set(enhanced_structure.split())
    preservation_ratio = len(original_words & enhanced_words) / len(original_words)
    
    assert preservation_ratio >= 0.8, f"At least 80% of original words should be preserved, got {preservation_ratio:.1%}"
    
    print("Structure preservation verified")

@pytest.mark.asyncio
async def test_multiple_enhancement_runs_consistency(sample_content, detected_plugins, enhancer_agent):
    """
    Test that multiple enhancement runs with same parameters produce consistent results.
    """
    enhancement_params = {
        "content": sample_content,
        "detected_plugins": detected_plugins,
        "enhancement_types": ["plugin_links", "info_text"]
    }
    
    # Run enhancement multiple times
    results = []
    for i in range(3):
        result = await enhancer_agent.handle_enhance_content(enhancement_params.copy())
        results.append(result)
    
    # First run should perform enhancements
    assert results[0]["statistics"]["total_enhancements"] > 0
    
    # Subsequent runs should detect already enhanced content
    for i in range(1, 3):
        assert results[i]["statistics"].get("already_enhanced", False), f"Run {i+1} should detect already enhanced content"
        assert results[i]["statistics"]["total_enhancements"] == 0, f"Run {i+1} should make no additional enhancements"
    
    print("Multiple enhancement run consistency verified")

if __name__ == "__main__":
    # Run tests directly
    import sys
    pytest.main([__file__, "-v"] + sys.argv[1:])
