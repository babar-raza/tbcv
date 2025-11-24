"""
Tests for LLM-based truth validation.

This module tests the semantic validation capabilities of ContentValidatorAgent
when using LLM (Ollama) to validate content against truth data.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.content_validator import ContentValidatorAgent, ValidationIssue
from agents.truth_manager import TruthManagerAgent
from agents.base import agent_registry


@pytest.fixture
def setup_agents():
    """Setup validator and truth manager agents"""
    truth_manager = TruthManagerAgent("truth_manager")
    agent_registry.register_agent(truth_manager)

    validator = ContentValidatorAgent("content_validator")
    agent_registry.register_agent(validator)

    yield validator, truth_manager

    agent_registry.unregister_agent("truth_manager")
    agent_registry.unregister_agent("content_validator")


@pytest.mark.asyncio
async def test_llm_truth_validation_plugin_requirement(setup_agents):
    """Test LLM detects missing plugin requirements"""

    content = """---
title: Convert DOCX to PDF
plugins: []
---
# How to Convert
Load DOCX and save as PDF.
"""

    validator, _ = setup_agents

    with patch('core.ollama.ollama') as mock_ollama:
        mock_ollama.enabled = True
        mock_ollama.is_available = MagicMock(return_value=True)
        mock_ollama.async_generate = AsyncMock(return_value={
            'response': '''{
              "semantic_issues": [{
                "level": "error",
                "category": "plugin_requirement",
                "message": "DOCX to PDF conversion requires Document processor, PDF processor, and Document Converter plugins",
                "suggestion": "Add plugins: [document, pdf-processor, document-converter] to frontmatter",
                "confidence": 0.95
              }],
              "overall_confidence": 0.95
            }'''
        })

        result = await validator.process_request("validate_content", {
            "content": content,
            "file_path": "test.md",
            "family": "words",
            "validation_types": ["Truth"]
        })

        issues = result.get("issues", [])
        semantic_issues = [i for i in issues if i.get("source") == "llm_truth"]

        assert len(semantic_issues) > 0, "Should detect missing plugin requirement"
        assert any("Document" in i.get("message", "") for i in semantic_issues), \
            "Should mention Document processor in error message"


@pytest.mark.asyncio
async def test_llm_truth_validation_invalid_combination(setup_agents):
    """Test LLM detects invalid plugin combinations"""

    content = """---
title: Merge Documents
plugins: [document-merger]
---
Use Merger to combine files.
"""

    validator, _ = setup_agents

    with patch('core.ollama.ollama') as mock_ollama:
        mock_ollama.enabled = True
        mock_ollama.is_available = MagicMock(return_value=True)
        mock_ollama.async_generate = AsyncMock(return_value={
            'response': '''{
              "semantic_issues": [{
                "level": "error",
                "category": "plugin_combination",
                "message": "Document Merger is a feature plugin and requires a processor plugin (e.g., Document) to load files",
                "suggestion": "Add Document processor to plugins list: plugins: [document, document-merger]",
                "confidence": 0.98
              }],
              "overall_confidence": 0.98
            }'''
        })

        result = await validator.process_request("validate_content", {
            "content": content,
            "file_path": "test.md",
            "family": "words",
            "validation_types": ["Truth"]
        })

        issues = result.get("issues", [])
        semantic_issues = [i for i in issues if i.get("source") == "llm_truth"]

        assert len(semantic_issues) > 0, "Should detect invalid plugin combination"
        assert any("processor" in i.get("message", "").lower() for i in semantic_issues), \
            "Should mention need for processor plugin"


@pytest.mark.asyncio
async def test_llm_truth_validation_technical_accuracy(setup_agents):
    """Test LLM validates technical accuracy against truth"""

    content = """---
title: Working with Spreadsheets
plugins: [document]
---
The Document plugin can load XLSX spreadsheets.
"""

    validator, _ = setup_agents

    with patch('core.ollama.ollama') as mock_ollama:
        mock_ollama.enabled = True
        mock_ollama.is_available = MagicMock(return_value=True)
        mock_ollama.async_generate = AsyncMock(return_value={
            'response': '''{
              "semantic_issues": [{
                "level": "error",
                "category": "technical_accuracy",
                "message": "Document plugin does not support XLSX format. XLSX files require Cells plugin.",
                "suggestion": "Replace 'Document plugin' with 'Cells plugin' or use plugins: [cells]",
                "confidence": 1.0
              }],
              "overall_confidence": 1.0
            }'''
        })

        result = await validator.process_request("validate_content", {
            "content": content,
            "file_path": "test.md",
            "family": "words",
            "validation_types": ["Truth"]
        })

        issues = result.get("issues", [])
        semantic_issues = [i for i in issues if i.get("source") == "llm_truth"]

        assert len(semantic_issues) > 0, "Should detect technical inaccuracy"
        assert any("Cells" in i.get("message", "") for i in semantic_issues), \
            "Should suggest Cells plugin for XLSX"


@pytest.mark.asyncio
async def test_llm_truth_validation_format_mismatch(setup_agents):
    """Test LLM detects format compatibility issues"""

    content = """---
title: PDF Processing
plugins: [document]
---
Load PDF files using Document plugin.
"""

    validator, _ = setup_agents

    with patch('core.ollama.ollama') as mock_ollama:
        mock_ollama.enabled = True
        mock_ollama.is_available = MagicMock(return_value=True)
        mock_ollama.async_generate = AsyncMock(return_value={
            'response': '''{
              "semantic_issues": [{
                "level": "warning",
                "category": "format_mismatch",
                "message": "Document plugin loads word processing formats (DOCX, DOC, RTF), not PDF. Use PDF processor for PDF files.",
                "suggestion": "Change plugins to: [pdf-processor]",
                "confidence": 0.95
              }],
              "overall_confidence": 0.95
            }'''
        })

        result = await validator.process_request("validate_content", {
            "content": content,
            "file_path": "test.md",
            "family": "words",
            "validation_types": ["Truth"]
        })

        issues = result.get("issues", [])
        semantic_issues = [i for i in issues if i.get("source") == "llm_truth"]

        assert len(semantic_issues) > 0, "Should detect format mismatch"
        assert any("PDF" in i.get("message", "") for i in semantic_issues)


@pytest.mark.asyncio
async def test_llm_unavailable_fallback(setup_agents):
    """Test system falls back to heuristic when LLM unavailable"""

    validator, _ = setup_agents

    with patch('core.ollama.ollama') as mock_ollama:
        mock_ollama.enabled = False
        mock_ollama.is_available = MagicMock(return_value=False)

        result = await validator.process_request("validate_content", {
            "content": "---\ntitle: Test\n---\nContent",
            "file_path": "test.md",
            "family": "words",
            "validation_types": ["Truth"]
        })

        # Should still get results (heuristic validation)
        assert result is not None, "Should return results even without LLM"
        assert "issues" in result, "Should have issues field"

        # Metrics should show LLM was not enabled
        metrics = result.get("metrics", {})
        assert metrics.get("llm_validation_enabled") == False or metrics.get("semantic_issues", 0) == 0


@pytest.mark.asyncio
async def test_llm_truth_validation_pass_case(setup_agents):
    """Test that semantically correct content passes LLM validation"""

    content = """---
title: Convert DOCX to PDF
plugins: [document, pdf-processor, document-converter]
---
# How to Convert
1. Load DOCX with Document plugin
2. Convert using Document Converter
3. Save as PDF with PDF processor
"""

    validator, _ = setup_agents

    with patch('core.ollama.ollama') as mock_ollama:
        mock_ollama.enabled = True
        mock_ollama.is_available = MagicMock(return_value=True)
        mock_ollama.async_generate = AsyncMock(return_value={
            'response': '''{
              "semantic_issues": [],
              "overall_confidence": 0.95
            }'''
        })

        result = await validator.process_request("validate_content", {
            "content": content,
            "file_path": "test.md",
            "family": "words",
            "validation_types": ["Truth"]
        })

        semantic_issues = [i for i in result.get("issues", []) if i.get("source") == "llm_truth"]
        assert len(semantic_issues) == 0, "Correct content should pass LLM validation"


@pytest.mark.asyncio
async def test_llm_truth_validation_with_heuristic_issues(setup_agents):
    """Test LLM validation works alongside heuristic validation"""

    content = """---
title: Test
---
# Missing description field and plugins
"""

    validator, _ = setup_agents

    with patch('core.ollama.ollama') as mock_ollama:
        mock_ollama.enabled = True
        mock_ollama.is_available = MagicMock(return_value=True)
        mock_ollama.async_generate = AsyncMock(return_value={
            'response': '''{
              "semantic_issues": [{
                "level": "info",
                "category": "missing_prerequisite",
                "message": "Content is very minimal. Consider adding more details about what will be accomplished.",
                "suggestion": "Add a description section explaining the purpose",
                "confidence": 0.7
              }],
              "overall_confidence": 0.7
            }'''
        })

        result = await validator.process_request("validate_content", {
            "content": content,
            "file_path": "test.md",
            "family": "words",
            "validation_types": ["Truth"]
        })

        issues = result.get("issues", [])

        # Should have both heuristic and semantic issues
        heuristic_issues = [i for i in issues if i.get("source") in ["truth", "rule"]]
        semantic_issues = [i for i in issues if i.get("source") == "llm_truth"]

        # Both types should contribute
        assert len(issues) > 0, "Should have validation issues"
        # At least one type should have issues (depending on truth data)
        assert len(heuristic_issues) > 0 or len(semantic_issues) > 0


@pytest.mark.asyncio
async def test_llm_truth_validation_malformed_response(setup_agents):
    """Test graceful handling of malformed LLM responses"""

    validator, _ = setup_agents

    with patch('core.ollama.ollama') as mock_ollama:
        mock_ollama.enabled = True
        mock_ollama.is_available = MagicMock(return_value=True)
        # Return malformed JSON
        mock_ollama.async_generate = AsyncMock(return_value={
            'response': 'This is not valid JSON at all!'
        })

        result = await validator.process_request("validate_content", {
            "content": "---\ntitle: Test\n---\nContent",
            "file_path": "test.md",
            "family": "words",
            "validation_types": ["Truth"]
        })

        # Should not crash
        assert result is not None
        # Should still have heuristic validation results
        assert "issues" in result


@pytest.mark.asyncio
async def test_llm_truth_validation_empty_content(setup_agents):
    """Test LLM validation with empty/minimal content"""

    content = """---
title: Empty
---
"""

    validator, _ = setup_agents

    with patch('core.ollama.ollama') as mock_ollama:
        mock_ollama.enabled = True
        mock_ollama.is_available = MagicMock(return_value=True)
        mock_ollama.async_generate = AsyncMock(return_value={
            'response': '''{
              "semantic_issues": [{
                "level": "warning",
                "category": "missing_prerequisite",
                "message": "Document has no content. Cannot validate completeness.",
                "suggestion": "Add content describing the functionality",
                "confidence": 0.9
              }],
              "overall_confidence": 0.5
            }'''
        })

        result = await validator.process_request("validate_content", {
            "content": content,
            "file_path": "test.md",
            "family": "words",
            "validation_types": ["Truth"]
        })

        # Should handle gracefully
        assert result is not None
        assert "issues" in result


@pytest.mark.asyncio
async def test_llm_truth_validation_metrics(setup_agents):
    """Test that metrics are properly tracked for LLM validation"""

    content = """---
title: Test
plugins: [document]
---
Content
"""

    validator, _ = setup_agents

    with patch('core.ollama.ollama') as mock_ollama:
        mock_ollama.enabled = True
        mock_ollama.is_available = MagicMock(return_value=True)
        mock_ollama.async_generate = AsyncMock(return_value={
            'response': '''{
              "semantic_issues": [{
                "level": "info",
                "category": "plugin_requirement",
                "message": "Test issue",
                "confidence": 0.8
              }],
              "overall_confidence": 0.8
            }'''
        })

        result = await validator.process_request("validate_content", {
            "content": content,
            "file_path": "test.md",
            "family": "words",
            "validation_types": ["Truth"]
        })

        metrics = result.get("metrics", {})

        # Should track LLM validation metrics
        # Metrics are nested under Truth_metrics key
        truth_metrics = metrics.get("Truth_metrics", {})
        assert "llm_validation_enabled" in truth_metrics, f"Metrics structure: {metrics}"
        assert truth_metrics["llm_validation_enabled"] == True
        assert "semantic_issues" in truth_metrics
        assert truth_metrics["semantic_issues"] >= 0
        assert "heuristic_issues" in truth_metrics
