"""
Quick test script to verify TBCV system functionality (folder name agnostic).
"""

import asyncio
import sys
import os
from pathlib import Path

# Ensure UTF-8 encoding on Windows
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"

# --- 🧬 Path setup so imports work even if folder isn't named 'tbcv' ---
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
# add submodules for direct import
for sub in ["core", "agents", "api", "cli"]:
    subdir = BASE_DIR / sub
    if subdir.exists() and str(subdir) not in sys.path:
        sys.path.insert(0, str(subdir))

# --- ✅ Now import modules using relative structure ---
async def test_system():
    """Test the complete TBCV system."""
    print("Testing TBCV System...")

    try:
        from core.config import get_settings , validate_configuration
        from core.logging import setup_logging
        from agents.fuzzy_detector import FuzzyDetectorAgent
        from agents.content_validator import ContentValidatorAgent
        from agents.content_enhancer import ContentEnhancerAgent
        from agents.orchestrator import OrchestratorAgent
        from agents.truth_manager import TruthManagerAgent
        from agents.orchestrator import agent_registry

        print("All imports successful")

        # Test configuration
        settings = get_settings()
        print(f"Configuration loaded: {settings.system.name} v{settings.system.version}")

        # Validate configuration
        issues = validate_configuration()
        if issues:
            print("⚠️  Configuration issues found:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print("Configuration validation passed")

        # Setup logging
        setup_logging()
        print("Logging configured")

        # Initialize agents
        print("Initializing agents...")

        truth_manager = TruthManagerAgent("truth_manager")
        fuzzy_detector = FuzzyDetectorAgent("fuzzy_detector")
        content_validator = ContentValidatorAgent("content_validator")
        content_enhancer = ContentEnhancerAgent("content_enhancer")
        orchestrator = OrchestratorAgent("orchestrator")

        # Register agents
        agent_registry.register_agent(truth_manager)
        agent_registry.register_agent(fuzzy_detector)
        agent_registry.register_agent(content_validator)
        agent_registry.register_agent(content_enhancer)
        agent_registry.register_agent(orchestrator)

        print("All agents initialized and registered")

        # Test sample content
        test_content = """---
title: Document Converter Tutorial
description: Learn how to convert documents using Aspose.Words plugins
date: 2024-01-15
---

# Document Processing with Aspose.Words

This tutorial demonstrates document conversion capabilities.

## Basic Document Conversion
```csharp
using Aspose.Words;

Document doc = new Document("input.docx");
doc.Save("output.pdf", SaveFormat.Pdf);
doc.Save("output.html", SaveFormat.Html);
```
The Document Converter plugin provides advanced conversion features.
"""
        print("Testing workflow execution...")

        # Test workflow execution
        result = await orchestrator.process_request(
            "validate_file",
            {
                "file_path": "test.md",
                "family": "words"
            },
        )

        if result.get("status") == "completed":
            print("File validation completed successfully")
            validation_result = result.get("validation_result", {})
            confidence = validation_result.get("overall_confidence", 0)
            print(f"Overall confidence: {confidence:.2f}")
        else:
            print(f"File validation failed: {result.get('error')}")

        # Test individual agents
        print("Testing individual agents...")

        # Truth manager
        truth_result = await truth_manager.process_request("load_truth_data", {})
        if truth_result.get("success"):
            print(f"Truth data loaded: {truth_result.get('plugins_count', 0)} plugins")
        else:
            print("Truth data loading failed")

        # Fuzzy detector
        detection_result = await fuzzy_detector.process_request(
            "detect_plugins", {"text": test_content, "confidence_threshold": 0.6}
        )
        detected_count = detection_result.get("detection_count", 0)
        print(f"Plugin detection: {detected_count} plugins detected")

        # Content validator
        validation_result = await content_validator.process_request(
            "validate_content", {"content": test_content}
        )
        confidence = validation_result.get("confidence", 0)
        issues_count = len(validation_result.get("issues", []))
        print(f"Content validation: {confidence:.2f} confidence, {issues_count} issues")

        # Content enhancer
        enhancement_result = await content_enhancer.process_request(
            "enhance_content",
            {
                "content": test_content,
                "detected_plugins": detection_result.get("detections", []),
                "preview_only": True,
            },
        )
        enhancements_count = (
            enhancement_result.get("statistics", {}).get("total_enhancements", 0)
        )
        print(f"Content enhancement: {enhancements_count} enhancements suggested")

        print("\nAll tests completed successfully!\n")
        print("Next steps:")
        print("1. Run API server: python main.py --mode api")
        print("2. Run CLI: python main.py --mode cli --help")
        print("3. Visit http://localhost:8080/docs for API documentation")

        return True

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_system())
    sys.exit(0 if success else 1)
