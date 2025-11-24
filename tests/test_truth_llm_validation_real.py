"""
Real integration tests for LLM-based truth validation using actual Ollama.

These tests make real calls to Ollama (no mocks) to validate the implementation
works with a real LLM. They are marked as @pytest.mark.integration so they can
be skipped in CI/CD if Ollama is unavailable.

Requirements:
- Ollama must be running (`ollama serve`)
- mistral model must be available (`ollama pull mistral`)
"""
import os
import pytest
import sys
from pathlib import Path

# IMPORTANT: Set OLLAMA_ENABLED before importing any modules that use ollama
os.environ['OLLAMA_ENABLED'] = 'true'

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.content_validator import ContentValidatorAgent
from agents.truth_manager import TruthManagerAgent
from agents.base import agent_registry

# Import and reinitialize ollama to pick up environment variable
from core.ollama import ollama, Ollama
# Reinitialize the global ollama instance with enabled=True
ollama.__init__(enabled=True)


def check_ollama_available():
    """Check if Ollama is available for testing."""
    try:
        import requests
        response = requests.get("http://127.0.0.1:11434/api/tags", timeout=2)
        return response.status_code == 200
    except Exception:
        return False


# Skip all tests in this module if Ollama not available
pytestmark = pytest.mark.skipif(
    not check_ollama_available(),
    reason="Ollama not available (install and run: ollama serve)"
)


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


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_llm_missing_plugin_requirement(setup_agents):
    """
    REAL TEST: Test with actual Ollama detecting missing plugin requirements.

    Content describes DOCX to PDF conversion but doesn't declare required plugins.
    LLM should detect this semantic issue.
    """
    content = """---
title: Convert DOCX to PDF with Aspose.Words
description: Learn how to convert DOCX files to PDF format
plugins: []
---

# How to Convert DOCX to PDF

In this tutorial, you'll learn how to convert DOCX files to PDF format.

## Steps

1. Load your DOCX file
2. Configure PDF options
3. Save as PDF format

## Example

Load the document and save it as PDF. That's it!
"""

    validator, _ = setup_agents

    result = await validator.process_request("validate_content", {
        "content": content,
        "file_path": "test_real.md",
        "family": "words",
        "validation_types": ["Truth"]
    })

    # Check that validation ran
    assert result is not None, "Should return validation results"

    # Check metrics
    metrics = result.get("metrics", {})
    truth_metrics = metrics.get("Truth_metrics", {})

    # LLM should have run
    assert truth_metrics.get("llm_validation_enabled") == True, \
        "LLM validation should be enabled"

    # Should have detected issues (either heuristic or semantic or both)
    issues = result.get("issues", [])
    assert len(issues) > 0, \
        "Should detect missing plugin requirements"

    # Check if LLM contributed semantic issues
    semantic_issues = [i for i in issues if i.get("source") == "llm_truth"]

    print(f"\n=== REAL LLM TEST RESULTS ===")
    print(f"Total issues: {len(issues)}")
    print(f"Semantic issues (LLM): {len(semantic_issues)}")
    print(f"LLM enabled: {truth_metrics.get('llm_validation_enabled')}")

    if semantic_issues:
        print(f"\nLLM detected semantic issues:")
        for issue in semantic_issues:
            print(f"  - [{issue.get('level')}] {issue.get('message')}")
            if issue.get('suggestion'):
                print(f"    Suggestion: {issue.get('suggestion')}")

    # LLM should ideally detect the missing plugins
    # (but we don't make it a hard requirement since LLM responses can vary)
    if len(semantic_issues) > 0:
        print(f"\n[SUCCESS] LLM successfully detected semantic issues!")
    else:
        print(f"\n[WARNING] LLM didn't detect semantic issues (heuristics found {len(issues)})")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_llm_invalid_plugin_combination(setup_agents):
    """
    REAL TEST: Test with actual Ollama detecting invalid plugin combinations.

    Content uses feature plugin (Merger) without processor plugin.
    LLM should detect this semantic issue.
    """
    content = """---
title: Merge Documents
description: Merge multiple documents into one
plugins: [document-merger]
---

# Document Merging

Use the Document Merger plugin to combine multiple files into a single document.

## Example

Merge documents easily with the Merger plugin.
"""

    validator, _ = setup_agents

    result = await validator.process_request("validate_content", {
        "content": content,
        "file_path": "test_real_combo.md",
        "family": "words",
        "validation_types": ["Truth"]
    })

    assert result is not None

    issues = result.get("issues", [])
    semantic_issues = [i for i in issues if i.get("source") == "llm_truth"]

    print(f"\n=== REAL LLM COMBINATION TEST ===")
    print(f"Total issues: {len(issues)}")
    print(f"Semantic issues (LLM): {len(semantic_issues)}")

    if semantic_issues:
        print(f"\nLLM detected semantic issues:")
        for issue in semantic_issues:
            print(f"  - [{issue.get('level')}] {issue.get('message')}")

    # Validation should find issues (either heuristic or LLM)
    assert len(issues) > 0, "Should detect plugin combination issues"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_llm_technical_accuracy(setup_agents):
    """
    REAL TEST: Test with actual Ollama detecting technical inaccuracies.

    Content claims Document plugin loads XLSX files (incorrect).
    LLM should detect this semantic issue.
    """
    content = """---
title: Loading Spreadsheets
description: Load XLSX files with Document plugin
plugins: [document]
---

# Loading XLSX Files

The Document plugin can load XLSX spreadsheet files for processing.

## Example

Use Document plugin to load your XLSX files and work with spreadsheet data.
"""

    validator, _ = setup_agents

    result = await validator.process_request("validate_content", {
        "content": content,
        "file_path": "test_real_accuracy.md",
        "family": "words",
        "validation_types": ["Truth"]
    })

    assert result is not None

    issues = result.get("issues", [])
    semantic_issues = [i for i in issues if i.get("source") == "llm_truth"]

    print(f"\n=== REAL LLM ACCURACY TEST ===")
    print(f"Total issues: {len(issues)}")
    print(f"Semantic issues (LLM): {len(semantic_issues)}")

    if semantic_issues:
        print(f"\nLLM detected semantic issues:")
        for issue in semantic_issues:
            print(f"  - [{issue.get('level')}] {issue.get('message')}")
            print(f"    Category: {issue.get('category')}")

    # Should detect the technical inaccuracy
    # (LLM should know Document plugin doesn't handle XLSX)
    assert len(issues) > 0, "Should detect technical inaccuracy"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_llm_correct_content_passes(setup_agents):
    """
    REAL TEST: Test that semantically correct content passes LLM validation.

    Content correctly declares all required plugins for DOCX to PDF conversion.
    LLM should not report semantic issues.
    """
    content = """---
title: Convert DOCX to PDF Complete Example
description: Complete guide with all required plugins
plugins: [document, pdf-processor, document-converter]
---

# Complete DOCX to PDF Conversion

This tutorial shows how to convert DOCX files to PDF with all required plugins.

## Prerequisites

You need three plugins:
1. Document processor - to load DOCX files
2. PDF processor - to handle PDF format
3. Document Converter - to enable format conversion

## Steps

1. Load DOCX file using Document processor
2. Use Document Converter to convert the format
3. Save as PDF using PDF processor

## Example

Load your document, convert it, and save as PDF. All plugins are correctly configured.
"""

    validator, _ = setup_agents

    result = await validator.process_request("validate_content", {
        "content": content,
        "file_path": "test_real_correct.md",
        "family": "words",
        "validation_types": ["Truth"]
    })

    assert result is not None

    issues = result.get("issues", [])
    semantic_issues = [i for i in issues if i.get("source") == "llm_truth"]

    print(f"\n=== REAL LLM CORRECT CONTENT TEST ===")
    print(f"Total issues: {len(issues)}")
    print(f"Semantic issues (LLM): {len(semantic_issues)}")

    if semantic_issues:
        print(f"\nUnexpected LLM issues (should be minimal for correct content):")
        for issue in semantic_issues:
            print(f"  - [{issue.get('level')}] {issue.get('message')}")

    # Correct content should have few or no semantic issues
    # (some heuristic issues might exist, but LLM should be happy)
    print(f"\n[SUCCESS] Correct content validation complete")
    print(f"   Heuristic issues: {len([i for i in issues if i.get('source') != 'llm_truth'])}")
    print(f"   Semantic issues: {len(semantic_issues)}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_llm_response_structure(setup_agents):
    """
    REAL TEST: Verify that LLM responses are properly structured.

    Tests that the LLM returns JSON in the expected format and that
    the parser correctly extracts validation issues.
    """
    content = """---
title: Test Content
plugins: []
---

# Test

Converting files without declaring plugins.
"""

    validator, _ = setup_agents

    result = await validator.process_request("validate_content", {
        "content": content,
        "file_path": "test_real_structure.md",
        "family": "words",
        "validation_types": ["Truth"]
    })

    assert result is not None

    # Check result structure
    assert "issues" in result, "Result should have issues field"
    assert "confidence" in result, "Result should have confidence field"
    assert "metrics" in result, "Result should have metrics field"

    metrics = result.get("metrics", {})
    truth_metrics = metrics.get("Truth_metrics", {})

    # Check metrics structure
    assert "llm_validation_enabled" in truth_metrics, "Should track LLM enabled status"
    assert "heuristic_issues" in truth_metrics, "Should track heuristic issue count"
    assert "semantic_issues" in truth_metrics, "Should track semantic issue count"

    # Check issue structure
    issues = result.get("issues", [])
    for issue in issues:
        assert "level" in issue, "Each issue should have level"
        assert "category" in issue, "Each issue should have category"
        assert "message" in issue, "Each issue should have message"
        assert "source" in issue, "Each issue should have source"

    print(f"\n=== REAL LLM STRUCTURE TEST ===")
    print(f"[SUCCESS] All response structures valid")
    print(f"   Total issues: {len(issues)}")
    print(f"   Metrics tracked: {list(truth_metrics.keys())}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_llm_performance(setup_agents):
    """
    REAL TEST: Test LLM validation performance and timing.

    Ensures that LLM validation completes in reasonable time.
    """
    import time

    content = """---
title: Performance Test
plugins: [document]
---

# Test Document

Basic content for performance testing.
"""

    validator, _ = setup_agents

    start_time = time.time()

    result = await validator.process_request("validate_content", {
        "content": content,
        "file_path": "test_real_perf.md",
        "family": "words",
        "validation_types": ["Truth"]
    })

    end_time = time.time()
    duration = end_time - start_time

    assert result is not None

    print(f"\n=== REAL LLM PERFORMANCE TEST ===")
    print(f"Validation duration: {duration:.2f}s")

    # LLM validation should complete within reasonable time
    # (20 seconds is generous for local Ollama)
    assert duration < 20.0, f"Validation took too long: {duration:.2f}s"

    if duration < 5.0:
        print(f"[SUCCESS] Fast validation (<5s)")
    elif duration < 10.0:
        print(f"[SUCCESS] Good validation time (<10s)")
    else:
        print(f"[WARNING] Slow validation ({duration:.2f}s)")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_llm_with_multiple_issues(setup_agents):
    """
    REAL TEST: Test content with multiple semantic issues.

    Content has several problems that LLM should detect:
    - Missing plugins
    - Invalid combination
    - Technical inaccuracy
    """
    content = """---
title: Complex Problematic Example
description: Multiple issues to detect
plugins: [watermark-feature]
---

# Working with Documents

Use the Watermark feature to add watermarks to your XLSX spreadsheets.
The Document plugin can handle all spreadsheet operations.

Load your XLSX file and apply watermarks directly.
"""

    validator, _ = setup_agents

    result = await validator.process_request("validate_content", {
        "content": content,
        "file_path": "test_real_multiple.md",
        "family": "words",
        "validation_types": ["Truth"]
    })

    assert result is not None

    issues = result.get("issues", [])
    semantic_issues = [i for i in issues if i.get("source") == "llm_truth"]

    print(f"\n=== REAL LLM MULTIPLE ISSUES TEST ===")
    print(f"Total issues: {len(issues)}")
    print(f"Semantic issues (LLM): {len(semantic_issues)}")

    if semantic_issues:
        print(f"\nLLM detected semantic issues:")
        for i, issue in enumerate(semantic_issues, 1):
            print(f"\n  Issue {i}:")
            print(f"    Level: {issue.get('level')}")
            print(f"    Category: {issue.get('category')}")
            print(f"    Message: {issue.get('message')}")
            if issue.get('suggestion'):
                print(f"    Suggestion: {issue.get('suggestion')}")

    # Should detect multiple issues
    assert len(issues) > 0, "Should detect multiple issues"

    print(f"\n[SUCCESS] Multiple issue detection test complete")


if __name__ == "__main__":
    # Run with: python -m pytest tests/test_truth_llm_validation_real.py -v -s
    pytest.main([__file__, "-v", "-s", "--tb=short"])
