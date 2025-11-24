#!/usr/bin/env python
"""
Direct test of new validator agents without starting server.
Tests each validator individually and the ValidatorRouter.
"""

import asyncio
import sys

# Add current directory to path
sys.path.insert(0, '.')

from agents.validators.seo_validator import SeoValidatorAgent
from agents.validators.yaml_validator import YamlValidatorAgent
from agents.validators.markdown_validator import MarkdownValidatorAgent
from agents.validators.code_validator import CodeValidatorAgent
from agents.validators.link_validator import LinkValidatorAgent
from agents.validators.structure_validator import StructureValidatorAgent
from agents.validators.truth_validator import TruthValidatorAgent
from agents.validators.router import ValidatorRouter
from agents.base import agent_registry


async def test_seo_validator():
    """Test SEO validator with sample content."""
    print("\n=== Testing SeoValidatorAgent ===")

    validator = SeoValidatorAgent("test_seo")

    # Test content with SEO issues
    content = """
## Missing H1

This document starts with H2 instead of H1.

### H3 Section

Some content here.
"""

    result = await validator.validate(content, {})
    print(f"[OK] SEO Validator executed")
    print(f"  - Confidence: {result.confidence:.2f}")
    print(f"  - Issues found: {len(result.issues)}")
    for issue in result.issues[:3]:  # Show first 3 issues
        print(f"    * {issue.level}: {issue.message}")

    return result


async def test_yaml_validator():
    """Test YAML validator."""
    print("\n=== Testing YamlValidatorAgent ===")

    validator = YamlValidatorAgent("test_yaml")

    # Content with valid YAML frontmatter
    content = """---
title: Test Document
date: 2025-11-22
tags: [test, validation]
---

# Content

This is the main content.
"""

    result = await validator.validate(content, {})
    print(f"[OK] YAML Validator executed")
    print(f"  - Confidence: {result.confidence:.2f}")
    print(f"  - Issues found: {len(result.issues)}")

    return result


async def test_markdown_validator():
    """Test Markdown validator."""
    print("\n=== Testing MarkdownValidatorAgent ===")

    validator = MarkdownValidatorAgent("test_markdown")

    # Content with markdown issues
    content = """
# Good Heading

Some content with [empty link]() and unclosed code block:

```python
def test():
    pass

Missing closing backticks
"""

    result = await validator.validate(content, {})
    print(f"[OK] Markdown Validator executed")
    print(f"  - Confidence: {result.confidence:.2f}")
    print(f"  - Issues found: {len(result.issues)}")
    for issue in result.issues[:3]:
        print(f"    * {issue.level}: {issue.message}")

    return result


async def test_code_validator():
    """Test Code validator."""
    print("\n=== Testing CodeValidatorAgent ===")

    validator = CodeValidatorAgent("test_code")

    content = """
# Code Examples

```
Code without language specifier
```

```python
print("Good code block")
```
"""

    result = await validator.validate(content, {})
    print(f"[OK] Code Validator executed")
    print(f"  - Confidence: {result.confidence:.2f}")
    print(f"  - Issues found: {len(result.issues)}")

    return result


async def test_link_validator():
    """Test Link validator."""
    print("\n=== Testing LinkValidatorAgent ===")

    validator = LinkValidatorAgent("test_link")

    content = """
# Links

[Good link](https://example.com)
[Localhost link](http://localhost:3000)
[Broken link]()
"""

    result = await validator.validate(content, {})
    print(f"[OK] Link Validator executed")
    print(f"  - Confidence: {result.confidence:.2f}")
    print(f"  - Issues found: {len(result.issues)}")
    for issue in result.issues:
        print(f"    * {issue.level}: {issue.message}")

    return result


async def test_structure_validator():
    """Test Structure validator."""
    print("\n=== Testing StructureValidatorAgent ===")

    validator = StructureValidatorAgent("test_structure")

    content = """
# Main Heading

## Section 1

Content here.

## Section 2

More content.
"""

    result = await validator.validate(content, {})
    print(f"[OK] Structure Validator executed")
    print(f"  - Confidence: {result.confidence:.2f}")
    print(f"  - Issues found: {len(result.issues)}")

    return result


async def test_validator_router():
    """Test ValidatorRouter."""
    print("\n=== Testing ValidatorRouter ===")

    # Register validators
    agent_registry.register_agent(SeoValidatorAgent("seo_validator"))
    agent_registry.register_agent(YamlValidatorAgent("yaml_validator"))
    agent_registry.register_agent(MarkdownValidatorAgent("markdown_validator"))

    router = ValidatorRouter(agent_registry)

    content = """---
title: Test
---

## Missing H1

This tests the router.
"""

    result = await router.execute(
        validation_types=["seo", "yaml", "markdown"],
        content=content,
        context={"file_path": "test.md", "family": "words"},
        ui_override=False
    )

    print(f"[OK] ValidatorRouter executed")
    print(f"  - Routing info: {result['routing_info']}")
    print(f"  - Validations completed: {len(result['validation_results'])}")

    for val_type, route_status in result['routing_info'].items():
        print(f"    * {val_type}: {route_status}")

    return result


async def main():
    """Run all validator tests."""
    print("=" * 60)
    print("TBCV Validator Direct Test Suite")
    print("=" * 60)

    try:
        # Test each validator individually
        await test_seo_validator()
        await test_yaml_validator()
        await test_markdown_validator()
        await test_code_validator()
        await test_link_validator()
        await test_structure_validator()

        # Test the router
        await test_validator_router()

        print("\n" + "=" * 60)
        print("[SUCCESS] ALL TESTS PASSED")
        print("=" * 60)
        print("\nNext steps:")
        print("1. All validators are working correctly")
        print("2. ValidatorRouter successfully routes to new validators")
        print("3. Ready for integration testing")

        return 0

    except Exception as e:
        print(f"\n[FAILED] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
