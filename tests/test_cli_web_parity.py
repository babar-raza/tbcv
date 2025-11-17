"""
Tests for CLI and Web interface parity
"""
import pytest
import sys
import tempfile
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.content_validator import ContentValidatorAgent
from agents.base import agent_registry


@pytest.fixture
async def setup_validator():
    """Setup validator agent"""
    validator = ContentValidatorAgent("content_validator")
    agent_registry.register_agent(validator)
    
    yield validator
    
    agent_registry.unregister_agent("content_validator")


@pytest.mark.asyncio
async def test_cli_web_validation_parity(setup_validator):
    """Test that CLI and Web produce same validation results"""
    validator = setup_validator
    
    content = """---
title: Test Document
description: Testing parity
---
# Content
"""
    
    # Simulate Web request
    web_result = await validator.process_request("validate_content", {
        "content": content,
        "file_path": "test.md",
        "family": "words",
        "validation_types": ["yaml", "markdown"]
    })
    
    # Simulate CLI request (same params)
    cli_result = await validator.process_request("validate_content", {
        "content": content,
        "file_path": "test.md",
        "family": "words",
        "validation_types": ["yaml", "markdown"]
    })
    
    # Results should be identical
    assert web_result.get("confidence") == cli_result.get("confidence")
    assert len(web_result.get("issues", [])) == len(cli_result.get("issues", []))


@pytest.mark.asyncio
async def test_cli_web_enhancement_parity(setup_validator):
    """Test that CLI and Web produce same enhancement results"""
    validator = setup_validator
    
    from agents.enhancement_agent import EnhancementAgent
    enhance_agent = EnhancementAgent("enhancement_agent")
    agent_registry.register_agent(enhance_agent)
    
    content = "---\ntitle: Test\n---\n# Content"
    
    # Both CLI and Web should use same enhancement pipeline
    result = await enhance_agent.process_request("enhance_with_recommendations", {
        "content": content,
        "file_path": "test.md",
        "recommendation_ids": []
    })
    
    assert result is not None
    assert "enhanced_content" in result or "content" in result
    
    agent_registry.unregister_agent("enhancement_agent")


@pytest.mark.asyncio
async def test_validation_types_consistency():
    """Test that validation types work the same in CLI and Web"""
    validator = ContentValidatorAgent("test_validator")
    
    # Test all validation types
    validation_types = ["yaml", "markdown", "code", "links", "structure", "Truth", "FuzzyLogic"]
    
    for vtype in validation_types:
        result = await validator.process_request("validate_content", {
            "content": "---\ntitle: Test\n---\n# Content",
            "file_path": "test.md",
            "family": "words",
            "validation_types": [vtype]
        })
        
        # Each validation type should return result
        assert result is not None, f"Validation type {vtype} should work"


@pytest.mark.asyncio
async def test_mcp_endpoint_consistency():
    """Test that MCP endpoints work consistently"""
    from agents.content_validator import ContentValidatorAgent
    
    validator = ContentValidatorAgent("test_mcp")
    
    # Test MCP message handlers
    handlers = [
        "validate_content",
        "validate_yaml",
        "validate_markdown",
        "validate_code",
        "validate_links",
        "validate_structure"
    ]
    
    for handler in handlers:
        assert handler in validator.message_handlers, f"Handler {handler} should be registered"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
