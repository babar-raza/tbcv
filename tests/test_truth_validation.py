"""
Tests for Truth validation against /truth/{family}.json files
"""
import pytest
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.content_validator import ContentValidatorAgent
from agents.truth_manager import TruthManagerAgent
from agents.base import agent_registry


@pytest.fixture
async def setup_agents():
    """Setup validator and truth manager agents"""
    truth_manager = TruthManagerAgent("truth_manager")
    agent_registry.register_agent(truth_manager)
    
    validator = ContentValidatorAgent("content_validator")
    agent_registry.register_agent(validator)
    
    yield validator, truth_manager
    
    agent_registry.unregister_agent("truth_manager")
    agent_registry.unregister_agent("content_validator")


@pytest.mark.asyncio
async def test_truth_validation_required_fields(setup_agents):
    """Test that truth validation detects missing required fields"""
    validator, _ = setup_agents
    
    content = """---
title: Test Document
---
# Content without required description field
"""
    
    result = await validator.process_request("validate_content", {
        "content": content,
        "file_path": "test.md",
        "family": "words",
        "validation_types": ["Truth"]
    })
    
    # Check that truth_presence issues are detected
    issues = result.get("issues", [])
    truth_issues = [i for i in issues if i.get("category") == "truth_presence"]
    assert len(truth_issues) > 0, "Should detect missing required fields from truth"


@pytest.mark.asyncio
async def test_truth_validation_plugin_detection(setup_agents):
    """Test that truth validation detects undeclared plugins"""
    validator, _ = setup_agents
    
    content = """---
title: Test Document
description: Testing
---
# Using Aspose.Words
Document doc = new Document();
doc.Save("output.pdf");
"""
    
    result = await validator.process_request("validate_content", {
        "content": content,
        "file_path": "test.md",
        "family": "words",
        "validation_types": ["Truth"]
    })
    
    # Check that plugin mismatch is detected
    issues = result.get("issues", [])
    truth_issues = [i for i in issues if i.get("source") == "truth"]
    assert len(truth_issues) > 0, "Should detect plugin usage without declaration"


@pytest.mark.asyncio
async def test_truth_validation_forbidden_patterns(setup_agents):
    """Test that truth validation detects forbidden patterns"""
    validator, _ = setup_agents
    
    content = """---
title: Test Document
description: Testing deprecated APIs
---
# Using deprecated_api
This uses insecure_method which is forbidden.
"""
    
    result = await validator.process_request("validate_content", {
        "content": content,
        "file_path": "test.md",
        "family": "words",
        "validation_types": ["Truth"]
    })
    
    # Check that forbidden patterns are detected
    issues = result.get("issues", [])
    forbidden_issues = [i for i in issues if i.get("category") == "truth_not_allowed"]
    assert len(forbidden_issues) > 0, "Should detect forbidden patterns from truth"


@pytest.mark.asyncio
async def test_truth_validation_with_metadata(setup_agents):
    """Test that truth validation returns metadata with expected/actual values"""
    validator, _ = setup_agents
    
    content = """---
title: Test
plugins: [wrong-plugin]
---
# Content using Document class
"""
    
    result = await validator.process_request("validate_content", {
        "content": content,
        "file_path": "test.md",
        "family": "words",
        "validation_types": ["Truth"]
    })
    
    # Verify that issues have proper structure
    issues = result.get("issues", [])
    assert len(issues) > 0, "Should have validation issues"
    
    # Check that some issues come from truth validation
    truth_issues = [i for i in issues if i.get("source") == "truth"]
    assert len(truth_issues) > 0, "Should have truth-related issues"


@pytest.mark.asyncio
async def test_truth_validation_pass_case(setup_agents):
    """Test that valid content passes truth validation"""
    validator, _ = setup_agents
    
    content = """---
title: Valid Document
description: This document follows all truth requirements
plugins: [aspose-words-net]
---
# Using Aspose.Words for .NET
Document doc = new Document();
"""
    
    result = await validator.process_request("validate_content", {
        "content": content,
        "file_path": "test.md",
        "family": "words",
        "validation_types": ["Truth"]
    })
    
    # Should have high confidence
    confidence = result.get("confidence", 0)
    assert confidence > 0.7, "Valid content should have high confidence"


# -----------------------------------------------------------------------------
# Additional tests for TruthManagerAgent indexing and combination logic
# -----------------------------------------------------------------------------


@pytest.fixture
async def setup_truth_manager():
    """
    Setup only the truth manager for direct truth-related tests.
    """
    from agents.base import agent_registry
    tm = TruthManagerAgent("truth_manager_test")
    agent_registry.register_agent(tm)
    yield tm
    agent_registry.unregister_agent("truth_manager_test")


@pytest.mark.asyncio
async def test_truth_manager_plugin_lookup_multiple(setup_truth_manager):
    """Ensure repeated plugin lookups are consistent and fast."""
    tm = setup_truth_manager
    # Load truth data for words
    await tm.process_request("load_truth_data", {"family": "words"})
    # Pick a known plugin id from Aspose truth definitions
    plugin_id = "word_processor"
    # Perform multiple lookups
    for _ in range(5):
        res = await tm.process_request("get_plugin_info", {"plugin_id": plugin_id})
        assert res["found"] is True, f"Plugin {plugin_id} should be found"
        assert res["plugin"]["id"] == plugin_id


@pytest.mark.asyncio
async def test_truth_manager_alias_search(setup_truth_manager):
    """Search plugins by alias or slug should return the correct plugin."""
    tm = setup_truth_manager
    await tm.process_request("load_truth_data", {"family": "words"})
    # Search by slug of pdf converter
    res = await tm.process_request("search_plugins", {"query": "pdfsaveoptions", "family": "words"})
    assert res["matches_count"] >= 1
    ids = {p["id"] for p in res["results"]}
    assert "pdf_converter" in ids, f"Expected pdf_converter in search results, got {ids}"


@pytest.mark.asyncio
async def test_truth_manager_unknown_plugin(setup_truth_manager):
    """Unknown plugin ID should return not found."""
    tm = setup_truth_manager
    await tm.process_request("load_truth_data", {"family": "words"})
    res = await tm.process_request("get_plugin_info", {"plugin_id": "nonexistent_plugin"})
    assert res["found"] is False


@pytest.mark.asyncio
async def test_truth_manager_combination_valid(setup_truth_manager):
    """Verify that a known combination of plugins is recognized as valid."""
    tm = setup_truth_manager
    await tm.process_request("load_truth_data", {"family": "words"})
    combo = ["word_processor", "pdf_converter"]
    res = await tm.process_request("check_plugin_combination", {"plugins": combo, "family": "words"})
    assert res["valid"] is True, f"Combination {combo} should be valid"
    assert res["rules"], "Expected at least one matching combination rule"


@pytest.mark.asyncio
async def test_truth_manager_combination_invalid(setup_truth_manager):
    """Ensure invalid combinations or unknown plugins are flagged."""
    tm = setup_truth_manager
    await tm.process_request("load_truth_data", {"family": "words"})
    combo = ["word_processor", "unknown_plugin"]
    res = await tm.process_request("check_plugin_combination", {"plugins": combo, "family": "words"})
    # Should be invalid with unknown plugin reported
    assert res["valid"] is False
    assert res["unknown_plugins"] != []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# -----------------------------------------------------------------------------
# Two-stage gating pipeline tests
# -----------------------------------------------------------------------------

import asyncio
from agents.orchestrator import OrchestratorAgent
from agents.fuzzy_detector import FuzzyDetectorAgent
from agents.llm_validator import LLMValidatorAgent

class MockLLMValidator(LLMValidatorAgent):
    """
    Mock implementation of LLMValidatorAgent for testing two-stage gating.
    It returns a fixed confidence and one issue without using any external calls.
    """
    def __init__(self, agent_id: str = "llm_validator"):
        super().__init__(agent_id)

    async def handle_validate_plugins(self, params):
        # Always return one warning issue and high confidence
        return {
            "requirements": [],
            "issues": [
                {
                    "level": "warning",
                    "category": "mock_llm_issue",
                    "message": "Mock LLM issue",
                }
            ],
            "confidence": 0.9,
        }


@pytest.fixture
async def setup_orchestrator_environment():
    """
    Setup orchestrator with required agents (truth manager, fuzzy detector, content validator, mock LLM) for gating tests.
    Yields orchestrator agent and settings so that tests can modify validation mode and LLM enabled flags.
    """
    from agents.truth_manager import TruthManagerAgent
    from agents.content_validator import ContentValidatorAgent
    from agents.base import agent_registry
    from core.config import get_settings

    # Preserve original settings
    settings = get_settings()
    try:
        orig_mode = getattr(settings.validation, "mode", "two_stage")
    except Exception:
        orig_mode = "two_stage"
    try:
        orig_llm_enabled = getattr(settings.llm, "enabled", True)
    except Exception:
        orig_llm_enabled = True

    # Create agents
    tm = TruthManagerAgent("truth_manager")
    fd = FuzzyDetectorAgent("fuzzy_detector")
    cv = ContentValidatorAgent("content_validator")
    llm = MockLLMValidator("llm_validator")
    orch = OrchestratorAgent("orchestrator")

    # Register agents
    agent_registry.register_agent(tm)
    agent_registry.register_agent(fd)
    agent_registry.register_agent(cv)
    agent_registry.register_agent(llm)
    agent_registry.register_agent(orch)

    try:
        yield orch, settings, orig_mode, orig_llm_enabled
    finally:
        # Unregister agents
        for aid in ["truth_manager", "fuzzy_detector", "content_validator", "llm_validator", "orchestrator"]:
            try:
                agent_registry.unregister_agent(aid)
            except Exception:
                pass
        # Restore original settings
        try:
            settings.validation.mode = orig_mode
        except Exception:
            pass
        try:
            settings.llm.enabled = orig_llm_enabled
        except Exception:
            pass


@pytest.mark.asyncio
async def test_two_stage_validation_runs_both_stages(setup_orchestrator_environment):
    """
    Ensure two-stage mode runs both heuristic and LLM stages and applies gating.
    """
    orch, settings, orig_mode, orig_llm_enabled = setup_orchestrator_environment
    # Configure mode and enable LLM
    try:
        settings.validation.mode = "two_stage"
    except Exception:
        pass
    try:
        settings.llm.enabled = True
    except Exception:
        pass
    # Content with missing description triggers heuristic issues
    content = """---
title: Test
---
# Content without description field
"""
    pipeline_result = await orch._run_validation_pipeline(content, "test.md", "words")
    # Final issues should include both heuristic and LLM issues
    final_issues = pipeline_result.get("final_issues", [])
    assert len(final_issues) >= 2, "Two-stage mode should produce combined issues"
    # At least one issue from heuristics with llm_decision
    heuristic_issue = next((i for i in final_issues if i.get("source_stage") == "heuristic"), None)
    assert heuristic_issue is not None, "Heuristic issues should be present in two-stage mode"
    assert heuristic_issue.get("llm_decision") in ["downgrade", "confirm", "upgrade"], "Heuristic issue should have llm_decision"
    # LLM issue should be present
    llm_issue = next((i for i in final_issues if i.get("source_stage") == "llm"), None)
    assert llm_issue is not None, "LLM issue should be present in two-stage mode"


@pytest.mark.asyncio
async def test_heuristic_only_mode_skips_llm(setup_orchestrator_environment):
    """
    Ensure heuristic-only mode skips LLM stage and returns only heuristic issues.
    """
    orch, settings, orig_mode, orig_llm_enabled = setup_orchestrator_environment
    try:
        settings.validation.mode = "heuristic_only"
    except Exception:
        pass
    try:
        settings.llm.enabled = True
    except Exception:
        pass
    content = """---
title: Test
---
# Missing description field
"""
    pipeline_result = await orch._run_validation_pipeline(content, "test.md", "words")
    # LLM validation should not have run
    assert pipeline_result.get("llm_validation") is None, "LLM validation should be skipped in heuristic-only mode"
    # Final issues only from heuristics
    final_issues = pipeline_result.get("final_issues", [])
    assert final_issues, "Heuristic-only mode should produce heuristic issues"
    assert all(i.get("source_stage") == "heuristic" for i in final_issues), "All issues should come from heuristics"


@pytest.mark.asyncio
async def test_llm_only_mode_skips_heuristics(setup_orchestrator_environment):
    """
    Ensure llm-only mode skips heuristic stage and returns only LLM issues.
    """
    orch, settings, orig_mode, orig_llm_enabled = setup_orchestrator_environment
    try:
        settings.validation.mode = "llm_only"
    except Exception:
        pass
    try:
        settings.llm.enabled = True
    except Exception:
        pass
    content = """---
title: Test
---
# Missing description field
"""
    pipeline_result = await orch._run_validation_pipeline(content, "test.md", "words")
    # Plugin detection and content validation should be skipped
    assert pipeline_result.get("plugin_detection") is None, "Plugin detection should be skipped in llm-only mode"
    assert pipeline_result.get("content_validation") is None, "Content validation should be skipped in llm-only mode"
    # LLM validation should run
    assert pipeline_result.get("llm_validation") is not None, "LLM validation should run in llm-only mode"
    final_issues = pipeline_result.get("final_issues", [])
    assert final_issues, "LLM-only mode should produce LLM issues"
    assert all(i.get("source_stage") == "llm" for i in final_issues), "All issues should come from LLM"


@pytest.mark.asyncio
async def test_llm_unavailable_fallback_to_heuristic(setup_orchestrator_environment):
    """
    Ensure that when LLM is disabled globally, two-stage configuration falls back to heuristic-only.
    """
    orch, settings, orig_mode, orig_llm_enabled = setup_orchestrator_environment
    try:
        settings.validation.mode = "two_stage"
    except Exception:
        pass
    try:
        settings.llm.enabled = False
    except Exception:
        pass
    content = """---
title: Test
---
# Missing description field
"""
    pipeline_result = await orch._run_validation_pipeline(content, "test.md", "words")
    # LLM stage should not run
    assert pipeline_result.get("llm_validation") is None, "LLM stage should be skipped when disabled"
    final_issues = pipeline_result.get("final_issues", [])
    assert final_issues, "Heuristic issues should still be present"
    # All issues should be heuristic
    assert all(i.get("source_stage") == "heuristic" for i in final_issues), "All issues should come from heuristics when LLM disabled"
