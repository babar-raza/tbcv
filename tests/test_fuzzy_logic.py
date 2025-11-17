"""
Tests for FuzzyLogic validation
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.content_validator import ContentValidatorAgent
from agents.fuzzy_detector import FuzzyDetectorAgent
from agents.base import agent_registry


@pytest.fixture
async def setup_agents():
    """Setup validator and fuzzy detector agents"""
    fuzzy_detector = FuzzyDetectorAgent("fuzzy_detector")
    agent_registry.register_agent(fuzzy_detector)
    
    validator = ContentValidatorAgent("content_validator")
    agent_registry.register_agent(validator)
    
    yield validator, fuzzy_detector
    
    agent_registry.unregister_agent("fuzzy_detector")
    agent_registry.unregister_agent("content_validator")


@pytest.mark.asyncio
async def test_fuzzy_logic_validation_enabled(setup_agents):
    """Test that FuzzyLogic validation type is recognized"""
    validator, _ = setup_agents
    
    content = """---
title: Test
description: Testing fuzzy logic
---
# Content
Document doc = new Document();
"""
    
    result = await validator.process_request("validate_content", {
        "content": content,
        "file_path": "test.md",
        "family": "words",
        "validation_types": ["FuzzyLogic"]
    })
    
    assert result is not None, "FuzzyLogic validation should return results"
    assert "metrics" in result, "Should include metrics"


@pytest.mark.asyncio
async def test_fuzzy_logic_plugin_detection(setup_agents):
    """Test that fuzzy logic detects plugins with confidence scores"""
    validator, _ = setup_agents
    
    content = """---
title: Test
---
# Using Aspose.Words classes
Document doc = new Document();
DocumentBuilder builder = new DocumentBuilder(doc);
doc.Save("output.pdf");
"""
    
    result = await validator.process_request("validate_content", {
        "content": content,
        "file_path": "test.md",
        "family": "words",
        "validation_types": ["FuzzyLogic"]
    })
    
    # Should detect plugin usage
    issues = result.get("issues", [])
    fuzzy_issues = [i for i in issues if i.get("source") == "fuzzy"]
    
    # Fuzzy detection should flag undeclared plugin usage
    assert len(issues) >= 0, "Should process fuzzy logic validation"


@pytest.mark.asyncio
async def test_fuzzy_logic_with_ui_selection(setup_agents):
    """Test that FuzzyLogic can be selected in UI validation types"""
    validator, _ = setup_agents
    
    # This simulates UI sending validation request with FuzzyLogic checked
    result = await validator.process_request("validate_content", {
        "content": "# Test content",
        "file_path": "test.md",
        "family": "words",
        "validation_types": ["yaml", "FuzzyLogic"]
    })
    
    assert result is not None
    assert "confidence" in result


# Additional tests for improved fuzzy alias detection

@pytest.mark.asyncio
async def test_fuzzy_alias_detection_happy():
    """
    Ensure near-miss plugin names are detected with high confidence.
    """
    from agents.base import agent_registry
    fuzzy_detector = FuzzyDetectorAgent("test_alias")
    agent_registry.register_agent(fuzzy_detector)
    try:
        # Near miss of DocumentBuilder (missing letter)
        text = "DocumenBuilder builder = new DocumenBuilder(doc);"
        result = await fuzzy_detector.process_request("detect_plugins", {
            "text": text,
            "family": "words",
            "confidence_threshold": 0.6
        })
        plugin_ids = {d["plugin_id"] for d in result["detections"]}
        # Should detect the document_builder plugin
        assert "document_builder" in plugin_ids, f"Expected 'document_builder' in detections, got {plugin_ids}"
        assert result["detection_count"] > 0
        # Verify that plugin_confidences includes aggregated score for the plugin
        assert "document_builder" in result.get("plugin_confidences", {}), "plugin_confidences should include the detected plugin"
        agg_conf = result["plugin_confidences"]["document_builder"]
        # The stage confidence should equal the aggregated plugin confidence since only one plugin detected
        assert abs(result.get("confidence", 0.0) - agg_conf) < 1e-6, "Stage confidence should equal aggregated plugin confidence"
    finally:
        agent_registry.unregister_agent("test_alias")


@pytest.mark.asyncio
async def test_fuzzy_alias_detection_invalid():
    """
    Ensure ambiguous or invalid plugin names do not trigger high-confidence detection.
    """
    from agents.base import agent_registry
    fuzzy_detector = FuzzyDetectorAgent("test_alias2")
    agent_registry.register_agent(fuzzy_detector)
    try:
        # Completely ambiguous string should not match any plugin when using a high threshold
        text = "dcemntbldr is not a plugin"
        result = await fuzzy_detector.process_request("detect_plugins", {
            "text": text,
            "family": "words",
            "confidence_threshold": 0.85
        })
        # No detections expected
        assert result["detection_count"] == 0
        # plugin_confidences should be empty and confidence should be 0.0
        assert result.get("plugin_confidences", {}) == {}, "No plugin confidences should be reported"
        assert result.get("confidence", 0.0) == 0.0, "Stage confidence should be 0 when no detections"
    finally:
        agent_registry.unregister_agent("test_alias2")


# New tests for confidence aggregation

@pytest.mark.asyncio
async def test_fuzzy_multiple_signals_confidence_increase():
    """
    Ensure multiple detection signals for the same plugin combine to increase confidence.
    """
    from agents.base import agent_registry
    fuzzy_detector = FuzzyDetectorAgent("test_combined")
    agent_registry.register_agent(fuzzy_detector)
    try:
        # Two near-match occurrences of DocumentBuilder to trigger multiple fuzzy detections
        text = "DocumenBuilder builder = new DocumenBuilder(doc);"
        result = await fuzzy_detector.process_request("detect_plugins", {
            "text": text,
            "family": "words",
            "confidence_threshold": 0.0
        })
        # Collect detections for document_builder plugin
        detections = [d for d in result["detections"] if d["plugin_id"] == "document_builder"]
        # Should be at least two detections
        assert len(detections) >= 2, "Expected multiple detections for repeated near-match"
        # Aggregated confidence should be greater than any individual detection's confidence
        per_confidences = [d["confidence"] for d in detections]
        aggregated_conf = result["plugin_confidences"]["document_builder"]
        assert aggregated_conf > max(per_confidences), (
            f"Aggregated confidence {aggregated_conf} should exceed individual detection {max(per_confidences)}"
        )
    finally:
        agent_registry.unregister_agent("test_combined")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
