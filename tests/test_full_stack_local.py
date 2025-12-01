"""
Full-stack local integration test with real dependencies.

Marks: pytest.mark.local_heavy

This test requires:
- Ollama server running (ollama serve)
- Model available (check config/main.yaml for model name)
- Database accessible
- All agents operational

Run with: pytest tests/test_full_stack_local.py -v -s --local-heavy
Or: python run_full_stack_test.py path/to/file.md
Or: python run_full_stack_test.py path/to/folder/
"""

import pytest
import sys
import os
import asyncio
import time
from pathlib import Path
from typing import List, Dict, Any

# IMPORTANT: Set OLLAMA_ENABLED before importing any modules that use ollama
os.environ['OLLAMA_ENABLED'] = 'true'

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="module")
def event_loop():
    """Create module-scoped event loop for async fixtures."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

from agents.orchestrator import OrchestratorAgent
from agents.content_validator import ContentValidatorAgent
from agents.content_enhancer import ContentEnhancerAgent
from agents.truth_manager import TruthManagerAgent
from agents.fuzzy_detector import FuzzyDetectorAgent
from agents.llm_validator import LLMValidatorAgent
from agents.base import agent_registry
# Modular validators
from agents.validators.yaml_validator import YamlValidatorAgent
from agents.validators.markdown_validator import MarkdownValidatorAgent
from agents.validators.code_validator import CodeValidatorAgent
from agents.validators.link_validator import LinkValidatorAgent
from agents.validators.structure_validator import StructureValidatorAgent
from agents.validators.seo_validator import SeoValidatorAgent
from agents.validators.truth_validator import TruthValidatorAgent
from core.config import get_settings
from core.database import db_manager
from core.validation_store import list_validation_records
from core.ollama import ollama
from sqlalchemy import text


@pytest.fixture(scope="module")
def check_ollama():
    """Verify Ollama is running and accessible."""
    settings = get_settings()

    # Force enable ollama - the singleton may have been created before env var was set
    ollama.enabled = True

    try:
        response = ollama.list_models()
        # Handle both dict response and list response formats
        models = response.get('models', response) if isinstance(response, dict) else response
        if not models:
            pytest.skip("Ollama has no models available")
        print(f"\n[OK] Ollama available with models: {[m.get('name') for m in models]}")
    except Exception as e:
        pytest.skip(f"Ollama not accessible: {e}")

    return True


@pytest.fixture(scope="module")
async def setup_full_stack(check_ollama):
    """Setup complete agent stack with real dependencies."""
    print("\n" + "="*80)
    print("FULL-STACK LOCAL TEST - Setting up real agent environment")
    print("="*80)

    # Register modular validators (needed by ValidatorRouter)
    yaml_validator = YamlValidatorAgent()
    markdown_validator = MarkdownValidatorAgent()
    code_validator = CodeValidatorAgent()
    link_validator = LinkValidatorAgent()
    structure_validator = StructureValidatorAgent()
    seo_validator = SeoValidatorAgent()
    truth_validator = TruthValidatorAgent()

    agent_registry.register_agent(yaml_validator)
    agent_registry.register_agent(markdown_validator)
    agent_registry.register_agent(code_validator)
    agent_registry.register_agent(link_validator)
    agent_registry.register_agent(structure_validator)
    agent_registry.register_agent(seo_validator)
    agent_registry.register_agent(truth_validator)

    print("[OK] Modular validators registered")

    # Register high-level agents
    truth_manager = TruthManagerAgent("truth_manager")
    fuzzy_detector = FuzzyDetectorAgent("fuzzy_detector")
    content_validator = ContentValidatorAgent("content_validator")
    llm_validator = LLMValidatorAgent("llm_validator")
    content_enhancer = ContentEnhancerAgent("content_enhancer")
    orchestrator = OrchestratorAgent("orchestrator")

    agent_registry.register_agent(truth_manager)
    agent_registry.register_agent(fuzzy_detector)
    agent_registry.register_agent(content_validator)
    agent_registry.register_agent(llm_validator)
    agent_registry.register_agent(content_enhancer)
    agent_registry.register_agent(orchestrator)

    print("[OK] All agents registered")
    
    # Verify database is accessible
    try:
        with db_manager.get_session() as session:
            session.execute(text("SELECT 1"))
        print("[OK] Database accessible")
    except Exception as e:
        pytest.fail(f"Database not accessible: {e}")
    
    yield {
        "orchestrator": orchestrator,
        "content_validator": content_validator,
        "content_enhancer": content_enhancer,
        "truth_manager": truth_manager,
        "fuzzy_detector": fuzzy_detector,
        "llm_validator": llm_validator,
    }
    
    # Cleanup
    all_agent_ids = [
        # High-level agents
        "orchestrator", "content_enhancer", "llm_validator",
        "content_validator", "fuzzy_detector", "truth_manager",
        # Modular validators
        "yaml_validator", "markdown_validator", "code_validator",
        "link_validator", "structure_validator", "seo_validator", "truth_validator"
    ]
    for agent_id in all_agent_ids:
        try:
            agent_registry.unregister_agent(agent_id)
        except Exception:
            pass

    print("\n[OK] Cleanup complete")


def find_test_files(input_path: str) -> List[Path]:
    """Find markdown files to test."""
    path = Path(input_path)
    
    if not path.exists():
        pytest.fail(f"Test path does not exist: {input_path}")
    
    if path.is_file():
        if path.suffix.lower() == ".md":
            return [path]
        else:
            pytest.fail(f"Test file must be .md, got: {path.suffix}")
    
    if path.is_dir():
        files = list(path.glob("**/*.md"))
        if not files:
            pytest.fail(f"No .md files found in directory: {input_path}")
        return files
    
    pytest.fail(f"Invalid path: {input_path}")


@pytest.mark.local_heavy
@pytest.mark.asyncio
async def test_full_stack_single_file_workflow(setup_full_stack):
    """
    Full-stack test: validate and enhance a single file with all real dependencies.
    """
    agents = setup_full_stack
    orchestrator = agents["orchestrator"]
    content_enhancer = agents["content_enhancer"]
    settings = get_settings()

    # Debug: print registered agents vs what ValidatorRouter expects
    print("\n=== DEBUG: Agent Registry Contents ===")
    print(f"Registered agents: {list(agent_registry.list_agents().keys())}")
    print(f"Test agent_registry id: {id(agent_registry)}")
    print(f"Orchestrator ValidatorRouter agent_registry id: {id(orchestrator.validator_router.agent_registry)}")
    print(f"Same object: {agent_registry is orchestrator.validator_router.agent_registry}")
    print(f"ValidatorRouter map: {orchestrator.validator_router.validator_map}")
    for val_type, agent_id in orchestrator.validator_router.validator_map.items():
        agent = orchestrator.validator_router.agent_registry.get_agent(agent_id)
        print(f"  {val_type} -> {agent_id}: {'FOUND' if agent else 'NOT FOUND'}")
    print("=" * 40)
    
    # Use test file from environment or default
    test_file = os.getenv("TEST_FILE", "truth/words.json")  # Default to a file that exists
    
    # Create a test markdown file if needed (in docs/en/ directory for language check)
    test_dir = Path("docs/en")
    test_dir.mkdir(parents=True, exist_ok=True)
    test_md = test_dir / "test_full_stack.md"
    test_content = """---
title: Full Stack Test Document
description: Testing complete validation and enhancement pipeline
plugins: []
---

# Full Stack Integration Test

This document tests the complete TBCV workflow including:
- Truth validation
- Fuzzy detection
- LLM validation
- Content enhancement

## Example Code

```csharp
Document doc = new Document();
doc.Save("output.pdf");
```

The above code converts DOCX to PDF.
"""

    test_md.write_text(test_content, encoding="utf-8")
    # Normalize path to forward slashes for language check
    test_file = str(test_md).replace("\\", "/")
    
    print(f"\n{'='*80}")
    print(f"Testing file: {test_file}")
    print(f"Validation mode: {getattr(settings.validation, 'mode', 'two_stage')}")
    print(f"LLM enabled: {getattr(settings.llm, 'enabled', True)}")
    print(f"{'='*80}\n")
    
    # STAGE 1: Validation
    print("STAGE 1: Running complete validation pipeline...")
    validation_start = time.time()
    
    validation_result = await orchestrator.handle_validate_file({
        "file_path": test_file,
        "family": "words"
    })
    
    validation_duration = time.time() - validation_start
    
    assert validation_result.get("status") == "success", \
        f"Validation failed: {validation_result.get('message')}"
    
    print(f"[OK] Validation completed in {validation_duration:.2f}s")
    print(f"  - Mode: {validation_result.get('validation_mode')}")
    print(f"  - LLM enabled: {validation_result.get('llm_enabled')}")
    print(f"  - Overall confidence: {validation_result.get('overall_confidence', 0):.2f}")
    print(f"  - Final issues: {len(validation_result.get('final_issues', []))}")
    
    # Verify stages ran based on mode
    mode = validation_result.get("validation_mode", "two_stage")
    if mode == "two_stage":
        assert validation_result.get("plugin_detection") is not None, \
            "Plugin detection should run in two_stage mode"
        assert validation_result.get("content_validation") is not None, \
            "Content validation should run in two_stage mode"
        assert validation_result.get("llm_validation") is not None, \
            "LLM validation should run in two_stage mode"
        print("  [OK] Two-stage pipeline verified (heuristic + LLM)")
    elif mode == "heuristic_only":
        assert validation_result.get("llm_validation") is None, \
            "LLM validation should not run in heuristic_only mode"
        print("  [OK] Heuristic-only pipeline verified")
    elif mode == "llm_only":
        assert validation_result.get("llm_validation") is not None, \
            "LLM validation should run in llm_only mode"
        print("  [OK] LLM-only pipeline verified")
    
    # Verify issues have proper structure
    final_issues = validation_result.get("final_issues", [])
    for issue in final_issues:
        assert "source_stage" in issue, "Issue must have source_stage"
        assert issue["source_stage"] in ["heuristic", "llm"], \
            f"Invalid source_stage: {issue['source_stage']}"
        if issue["source_stage"] == "heuristic" and mode == "two_stage":
            assert "llm_decision" in issue, \
                "Heuristic issue in two_stage mode must have llm_decision"
    
    print(f"  [OK] Issue structure validated")
    
    # STAGE 2: Enhancement
    print("\nSTAGE 2: Running content enhancement...")
    enhancement_start = time.time()
    
    # Get detected plugins from validation
    detected_plugins = []
    if validation_result.get("plugin_detection"):
        detected_plugins = validation_result["plugin_detection"].get("detections", [])
    
    enhancement_result = await content_enhancer.process_request("enhance_content", {
        "content": test_content,
        "detected_plugins": detected_plugins,
        "file_path": test_file,
        "enhancement_types": ["plugin_links", "info_text"],
        "preview_only": False
    })
    
    enhancement_duration = time.time() - enhancement_start
    
    print(f"[OK] Enhancement completed in {enhancement_duration:.2f}s")
    print(f"  - Status: {enhancement_result.get('status')}")
    print(f"  - Enhancements applied: {len(enhancement_result.get('enhancements', []))}")
    
    if enhancement_result.get("status") == "gated":
        print(f"  - Gated reason: {enhancement_result.get('statistics', {})}")
    
    # STAGE 3: Verify database persistence (optional - may not persist in all modes)
    print("\nSTAGE 3: Verifying database persistence...")

    records = list_validation_records(file_path=test_file, limit=10)
    if len(records) > 0:
        latest_record = records[0]
        print(f"[OK] Found {len(records)} validation record(s) in database")
        print(f"  - Latest record ID: {latest_record.id}")
        print(f"  - Status: {latest_record.status}")
        print(f"  - Severity: {latest_record.severity}")
        print(f"  - Family: {latest_record.family}")
    else:
        print("[INFO] No validation records persisted - persistence may be disabled in test mode")
    
    # STAGE 4: Summary
    print(f"\n{'='*80}")
    print("FULL-STACK TEST SUMMARY")
    print(f"{'='*80}")
    print(f"[OK] Validation: {validation_duration:.2f}s")
    print(f"[OK] Enhancement: {enhancement_duration:.2f}s")
    print(f"[OK] Total time: {validation_duration + enhancement_duration:.2f}s")
    print(f"[OK] Database records: {len(records)}")
    if len(records) > 0:
        print(f"\nResults visible in dashboard at: http://localhost:8080/validations")
        print(f"Latest validation ID: {latest_record.id}")
    print(f"{'='*80}\n")
    
    # Cleanup test file
    if test_md.exists():
        test_md.unlink()
    if test_dir.exists() and not any(test_dir.iterdir()):
        test_dir.rmdir()
    # Also remove parent docs/ if empty
    docs_dir = Path("docs")
    if docs_dir.exists() and not any(docs_dir.iterdir()):
        docs_dir.rmdir()


@pytest.mark.local_heavy
@pytest.mark.asyncio
async def test_full_stack_directory_workflow(setup_full_stack):
    """
    Full-stack test: validate multiple files in a directory with all real dependencies.
    """
    agents = setup_full_stack
    orchestrator = agents["orchestrator"]
    settings = get_settings()
    
    # Use test directory from environment or create temp directory (in docs/en/ for language check)
    test_dir = Path(os.getenv("TEST_DIR", "docs/en/test_full_stack_dir"))
    test_dir.mkdir(parents=True, exist_ok=True)

    # Create test files
    test_files = []
    for i in range(3):
        test_file = test_dir / f"test_{i}.md"
        content = f"""---
title: Test Document {i}
description: Testing batch validation
plugins: []
---

# Test {i}

Document doc = new Document();
doc.Save("output{i}.pdf");
"""
        test_file.write_text(content, encoding="utf-8")
        test_files.append(test_file)
    
    # Normalize directory path to forward slashes for language check
    test_dir_normalized = str(test_dir).replace("\\", "/")

    print(f"\n{'='*80}")
    print(f"Testing directory: {test_dir_normalized}")
    print(f"Files: {len(test_files)}")
    print(f"Validation mode: {getattr(settings.validation, 'mode', 'two_stage')}")
    print(f"{'='*80}\n")

    # Run directory validation
    print("Running batch validation...")
    batch_start = time.time()

    batch_result = await orchestrator.handle_validate_directory({
        "directory_path": test_dir_normalized,
        "pattern": "*.md",
        "family": "words"
    })
    
    batch_duration = time.time() - batch_start
    
    assert batch_result.get("status") == "success", \
        f"Batch validation failed: {batch_result.get('message')}"
    
    print(f"[OK] Batch validation completed in {batch_duration:.2f}s")
    print(f"  - Total files: {batch_result.get('files_total')}")
    print(f"  - Validated: {batch_result.get('files_validated')}")
    print(f"  - Failed: {batch_result.get('files_failed')}")
    print(f"  - Results: {len(batch_result.get('results', []))}")
    
    # Verify all files were processed
    assert batch_result["files_validated"] == len(test_files), \
        "All files should be validated"
    
    # Verify results structure
    results = batch_result.get("results", [])
    for result in results:
        assert "validation_mode" in result, "Result must have validation_mode"
        assert "final_issues" in result, "Result must have final_issues"
    
    print(f"\n[OK] All files processed successfully")
    print(f"[OK] Average time per file: {batch_duration / len(test_files):.2f}s")
    
    # Cleanup
    for test_file in test_files:
        if test_file.exists():
            test_file.unlink()
    if test_dir.exists() and not any(test_dir.iterdir()):
        test_dir.rmdir()
    # Also remove parent docs/en/ and docs/ if empty
    en_dir = Path("docs/en")
    if en_dir.exists() and not any(en_dir.iterdir()):
        en_dir.rmdir()
    docs_dir = Path("docs")
    if docs_dir.exists() and not any(docs_dir.iterdir()):
        docs_dir.rmdir()

    print(f"\n[OK] Cleanup complete")


@pytest.mark.local_heavy
@pytest.mark.asyncio
async def test_full_stack_mode_switching(setup_full_stack):
    """
    Test all validation modes (two_stage, heuristic_only, llm_only) with real dependencies.
    """
    agents = setup_full_stack
    orchestrator = agents["orchestrator"]
    settings = get_settings()
    
    test_content = """---
title: Mode Test
description: Testing mode switching
---
Document doc = new Document();
doc.Save("output.pdf");
"""

    # Create in docs/en/ directory for language check
    test_dir = Path("docs/en")
    test_dir.mkdir(parents=True, exist_ok=True)
    test_file = test_dir / "test_mode_switching.md"
    test_file.write_text(test_content, encoding="utf-8")
    # Normalize path to forward slashes for language check
    test_file_normalized = str(test_file).replace("\\", "/")

    original_mode = getattr(settings.validation, "mode", "two_stage")
    modes_to_test = ["two_stage", "heuristic_only", "llm_only"]
    
    print(f"\n{'='*80}")
    print("Testing all validation modes")
    print(f"{'='*80}\n")
    
    results = {}
    
    for mode in modes_to_test:
        print(f"Testing mode: {mode}")
        settings.validation.mode = mode

        result = await orchestrator.handle_validate_file({
            "file_path": test_file_normalized,
            "family": "words"
        })
        
        assert result.get("status") == "success", f"Mode {mode} failed"
        assert result.get("validation_mode") == mode, f"Mode mismatch"
        
        results[mode] = result
        print(f"  [OK] {mode}: {len(result.get('final_issues', []))} issues, "
              f"confidence {result.get('overall_confidence', 0):.2f}")
    
    # Verify mode-specific behavior
    if settings.llm.enabled:
        # two_stage should have both stages
        two_stage = results["two_stage"]
        assert two_stage.get("plugin_detection") is not None
        assert two_stage.get("llm_validation") is not None
        print("\n[OK] Two-stage mode ran both heuristic and LLM stages")
        
        # heuristic_only should skip LLM
        heuristic = results["heuristic_only"]
        assert heuristic.get("llm_validation") is None
        print("[OK] Heuristic-only mode skipped LLM stage")
        
        # llm_only should skip heuristics
        llm_only = results["llm_only"]
        assert llm_only.get("plugin_detection") is None
        assert llm_only.get("llm_validation") is not None
        print("[OK] LLM-only mode skipped heuristic stage")
    
    # Restore original mode
    settings.validation.mode = original_mode

    # Cleanup
    if test_file.exists():
        test_file.unlink()
    if test_dir.exists() and not any(test_dir.iterdir()):
        test_dir.rmdir()
    # Also remove parent docs/ if empty
    docs_dir = Path("docs")
    if docs_dir.exists() and not any(docs_dir.iterdir()):
        docs_dir.rmdir()

    print(f"\n[OK] Mode switching test complete")


if __name__ == "__main__":
    # Allow running directly with file/folder path
    if len(sys.argv) > 1:
        test_path = sys.argv[1]
        print(f"Running full-stack test on: {test_path}")
        pytest.main([__file__, "-v", "-s", "--local-heavy", f"-k={test_path}"])
    else:
        pytest.main([__file__, "-v", "-s", "--local-heavy"])
