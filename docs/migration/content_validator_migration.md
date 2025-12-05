# ContentValidatorAgent Migration Guide

## Overview

**ContentValidatorAgent is deprecated and will be removed in version 2.0.0 (January 2026).**

This guide will help you migrate from the legacy monolithic `ContentValidatorAgent` to the new modular validator architecture.

## Why Migrate?

The new modular validator architecture provides several benefits:

1. **Better Separation of Concerns**: Each validator focuses on a specific validation domain
2. **Easier to Test**: Smaller, focused validators are easier to test in isolation
3. **More Flexible Configuration**: Configure and use only the validators you need
4. **Better Performance**: Run validators in parallel and skip unnecessary validations
5. **Easier Maintenance**: Update one validator without affecting others
6. **Clearer Dependencies**: Each validator has explicit, minimal dependencies

## Migration Timeline

- **2025-12-03**: Deprecation warning added to ContentValidatorAgent
- **2026-01-01**: ContentValidatorAgent will be removed (version 2.0.0)

## Migration Mapping

| ContentValidatorAgent Method | New Modular Validator | Location |
|------------------------------|----------------------|----------|
| `handle_validate_yaml()` | `YamlValidatorAgent` | `agents/validators/yaml_validator.py` |
| `handle_validate_markdown()` | `MarkdownValidatorAgent` | `agents/validators/markdown_validator.py` |
| `handle_validate_code()` | `CodeValidatorAgent` | `agents/validators/code_validator.py` |
| `handle_validate_links()` | `LinkValidatorAgent` | `agents/validators/link_validator.py` |
| `handle_validate_structure()` | `StructureValidatorAgent` | `agents/validators/structure_validator.py` |
| Truth validation | `TruthValidatorAgent` | `agents/validators/truth_validator.py` |
| SEO validation | `SeoValidatorAgent` | `agents/validators/seo_validator.py` |

## Migration Examples

### Example 1: Basic YAML Validation

**Before (Deprecated):**
```python
from agents.content_validator import ContentValidatorAgent

# This will issue a deprecation warning
validator = ContentValidatorAgent()
result = await validator.handle_validate_yaml({
    "content": content,
    "file_path": "example.md",
    "family": "words"
})
```

**After (Recommended):**
```python
from agents.validators.yaml_validator import YamlValidatorAgent

validator = YamlValidatorAgent()
result = await validator.validate({
    "content": content,
    "file_path": "example.md",
    "family": "words"
})
```

### Example 2: Multiple Validations

**Before (Deprecated):**
```python
from agents.content_validator import ContentValidatorAgent

validator = ContentValidatorAgent()

# Run all validations
result = await validator.handle_validate_content({
    "content": content,
    "file_path": "example.md",
    "family": "words",
    "validation_types": ["yaml", "markdown", "code", "links", "structure"]
})
```

**After (Recommended - Option 1: Manual):**
```python
from agents.validators import (
    YamlValidatorAgent,
    MarkdownValidatorAgent,
    CodeValidatorAgent,
    LinkValidatorAgent,
    StructureValidatorAgent
)

# Create validators
yaml_validator = YamlValidatorAgent()
markdown_validator = MarkdownValidatorAgent()
code_validator = CodeValidatorAgent()
link_validator = LinkValidatorAgent()
structure_validator = StructureValidatorAgent()

# Run validations in parallel
yaml_result = await yaml_validator.validate({"content": content, "family": "words"})
markdown_result = await markdown_validator.validate({"content": content})
code_result = await code_validator.validate({"content": content, "family": "words"})
link_result = await link_validator.validate({"content": content})
structure_result = await structure_validator.validate({"content": content})

# Combine results
all_issues = []
all_issues.extend(yaml_result["issues"])
all_issues.extend(markdown_result["issues"])
all_issues.extend(code_result["issues"])
all_issues.extend(link_result["issues"])
all_issues.extend(structure_result["issues"])
```

**After (Recommended - Option 2: Using ValidatorRouter):**
```python
from agents.validators.router import ValidatorRouter

router = ValidatorRouter()

# Route to appropriate validators automatically
result = await router.route_validation({
    "content": content,
    "file_path": "example.md",
    "family": "words",
    "validation_types": ["yaml", "markdown", "code", "links", "structure"]
})
```

### Example 3: Using EnhancementAgent (Facade Pattern)

**After (Recommended - Easiest):**
```python
from agents.enhancement_agent import EnhancementAgent

# EnhancementAgent acts as a facade over all modular validators
agent = EnhancementAgent()
result = await agent.validate({
    "file_path": "example.md",
    "family": "words"
})  # Uses all modular validators automatically
```

### Example 4: Truth Validation

**Before (Deprecated):**
```python
from agents.content_validator import ContentValidatorAgent

validator = ContentValidatorAgent()
result = await validator.handle_validate_content({
    "content": content,
    "file_path": "example.md",
    "family": "words",
    "validation_types": ["Truth"]
})
```

**After (Recommended):**
```python
from agents.validators.truth_validator import TruthValidatorAgent

validator = TruthValidatorAgent()
result = await validator.validate({
    "content": content,
    "file_path": "example.md",
    "family": "words"
})
```

### Example 5: SEO Validation

**Before (Deprecated):**
```python
from agents.content_validator import ContentValidatorAgent

validator = ContentValidatorAgent()
result = await validator.handle_validate_content({
    "content": content,
    "file_path": "example.md",
    "validation_types": ["seo_heading", "heading_size"]
})
```

**After (Recommended):**
```python
from agents.validators.seo_validator import SeoValidatorAgent

validator = SeoValidatorAgent()
result = await validator.validate({
    "content": content,
    "file_path": "example.md"
})
```

## API Changes

### Initialization

**Before:**
```python
validator = ContentValidatorAgent(agent_id="my_validator")
```

**After:**
```python
# Each validator can have its own agent_id
yaml_validator = YamlValidatorAgent(agent_id="yaml_validator")
markdown_validator = MarkdownValidatorAgent(agent_id="markdown_validator")
```

### Method Signatures

All modular validators use a consistent interface:

```python
async def validate(self, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate content.

    Args:
        params: Dictionary containing:
            - content (str): Content to validate
            - file_path (str, optional): Path to file being validated
            - family (str, optional): Product family (words, cells, pdf, slides)
            - Additional validator-specific parameters

    Returns:
        Dictionary containing:
            - confidence (float): Validation confidence score (0.0-1.0)
            - issues (List[Dict]): List of validation issues
            - auto_fixable_count (int): Number of auto-fixable issues
            - metrics (Dict): Validation metrics
            - file_path (str): Path to validated file
            - family (str): Product family
    """
```

### Return Value Structure

The return value structure is **identical** between ContentValidatorAgent and modular validators:

```python
{
    "confidence": 0.95,
    "issues": [
        {
            "level": "error",  # or "warning", "info"
            "category": "yaml_parse_error",
            "message": "Failed to parse YAML front-matter",
            "line_number": 1,
            "column": None,
            "suggestion": "Check YAML syntax",
            "source": "yaml_validator"
        }
    ],
    "auto_fixable_count": 3,
    "metrics": {
        "yaml_valid": False,
        "fields_checked": 5
    },
    "file_path": "example.md",
    "family": "words"
}
```

## Testing Migration

### Testing Deprecation Warning

```python
import pytest
import warnings

def test_deprecation_warning():
    """Verify ContentValidatorAgent issues deprecation warning."""
    with pytest.warns(DeprecationWarning, match="ContentValidatorAgent is deprecated"):
        from agents.content_validator import ContentValidatorAgent
        validator = ContentValidatorAgent()
```

### Testing Modular Validators

```python
import pytest
from agents.validators.yaml_validator import YamlValidatorAgent

@pytest.mark.asyncio
async def test_yaml_validator():
    """Test YamlValidatorAgent produces expected results."""
    validator = YamlValidatorAgent()

    content = """---
title: Test Document
plugins: [document]
---
Content here
"""

    result = await validator.validate({
        "content": content,
        "family": "words"
    })

    assert "confidence" in result
    assert "issues" in result
    assert result["confidence"] > 0.0
```

## Common Migration Patterns

### Pattern 1: Test Files

**Before:**
```python
# tests/test_my_feature.py
from agents.content_validator import ContentValidatorAgent

async def test_validation():
    validator = ContentValidatorAgent()
    result = await validator.handle_validate_yaml({"content": content})
```

**After:**
```python
# tests/test_my_feature.py
from agents.validators.yaml_validator import YamlValidatorAgent

async def test_validation():
    validator = YamlValidatorAgent()
    result = await validator.validate({"content": content})
```

### Pattern 2: API Endpoints

**Before:**
```python
# api/server.py
from agents.content_validator import ContentValidatorAgent

@app.post("/validate")
async def validate(content: str):
    validator = ContentValidatorAgent()
    return await validator.handle_validate_content({"content": content})
```

**After:**
```python
# api/server.py
from agents.validators.router import ValidatorRouter

@app.post("/validate")
async def validate(content: str):
    router = ValidatorRouter()
    return await router.route_validation({"content": content})
```

### Pattern 3: CLI Commands

**Before:**
```python
# cli/main.py
from agents.content_validator import ContentValidatorAgent

def validate_command(file_path: str):
    validator = ContentValidatorAgent()
    result = asyncio.run(validator.handle_validate_content({
        "content": read_file(file_path),
        "file_path": file_path
    }))
```

**After:**
```python
# cli/main.py
from agents.validators.router import ValidatorRouter

def validate_command(file_path: str):
    router = ValidatorRouter()
    result = asyncio.run(router.route_validation({
        "content": read_file(file_path),
        "file_path": file_path
    }))
```

## Troubleshooting

### Issue: Getting DeprecationWarning

**Symptom:** Seeing warnings when using ContentValidatorAgent

**Solution:** Migrate to modular validators using this guide

### Issue: Can't find modular validators

**Symptom:** Import errors when trying to use new validators

**Solution:** Ensure you're importing from the correct location:
```python
from agents.validators.yaml_validator import YamlValidatorAgent
from agents.validators.markdown_validator import MarkdownValidatorAgent
# etc.
```

### Issue: Different behavior between old and new validators

**Symptom:** Results differ between ContentValidatorAgent and modular validators

**Solution:**
1. Check that you're passing the same parameters
2. Verify you're combining results correctly if using multiple validators
3. File an issue if behavior is truly incompatible

### Issue: Performance concerns

**Symptom:** Worried about performance when using multiple validators

**Solution:**
1. Use ValidatorRouter to route requests efficiently
2. Run validators in parallel using `asyncio.gather()`
3. Use EnhancementAgent facade for automatic orchestration

## Support and Questions

- **Documentation:** See [docs/agents.md](../agents.md) for complete agent documentation
- **Modular Validators:** See [docs/modular_validators.md](../modular_validators.md) for detailed validator documentation
- **Issues:** File issues on the project's issue tracker
- **Migration Help:** Contact the development team

## Checklist for Migration

Use this checklist to track your migration progress:

- [ ] Identified all ContentValidatorAgent usages in codebase
- [ ] Updated imports to use modular validators
- [ ] Updated method calls from `handle_validate_*` to `validate`
- [ ] Updated parameter passing to new format
- [ ] Tested all updated code paths
- [ ] Updated tests to use modular validators
- [ ] Verified no deprecation warnings in test suite
- [ ] Updated documentation references
- [ ] Reviewed and merged changes

## Additional Resources

- [Modular Validators Documentation](../modular_validators.md)
- [Agent Architecture Documentation](../agents.md)
- [Validator Router Documentation](../agents.md#validatorrouter)
- [EnhancementAgent Documentation](../agents.md#enhancementagent)

---

**Last Updated:** 2025-12-03
**Deprecation Date:** 2025-12-03
**Removal Target:** 2026-01-01 (version 2.0.0)
