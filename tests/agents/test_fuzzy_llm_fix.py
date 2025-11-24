"""
Test script to verify fuzzy and LLM validation are working via the UI endpoint.
"""

import requests
import json

# Test content with plugin references
test_content = """---
title: How to Add Images in Word Documents using C#
ShowOnHomePage: false
url: /net/how-to-add-images-word-documents-csharp
type: article
---

# How to Add Images in Word Documents using C#

In this article, you will learn how to add images to Word documents using Aspose.Words for .NET.

## Introduction

Adding images to Word documents programmatically is a common requirement.

## Step-by-Step Guide to Adding an Image in a Word Document

First, install Aspose.Words for .NET via NuGet.

```csharp
// Create a document
Document doc = new Document();
DocumentBuilder builder = new DocumentBuilder(doc);

// Insert an image
builder.InsertImage("image.jpg");

// Save the document
doc.Save("output.docx");
```

## Conclusion

You have successfully learned how to add images to Word documents.
"""

# Make request to the validation endpoint
url = "http://127.0.0.1:8000/api/validate"
payload = {
    "content": test_content,
    "file_path": "test-add-images-word.md",
    "family": "words",
    "validation_types": ["yaml", "markdown", "code", "links", "structure", "Truth", "FuzzyLogic"]
}

print("=" * 80)
print("Testing /api/validate endpoint with fuzzy and LLM validation...")
print("=" * 80)
print()

try:
    response = requests.post(url, json=payload, timeout=60)

    print(f"Status Code: {response.status_code}")
    print()

    if response.status_code == 200:
        result = response.json()

        print("✓ Validation completed successfully!")
        print()

        # Check for validation ID
        if "id" in result or "validation_id" in result:
            validation_id = result.get("id") or result.get("validation_id")
            print(f"✓ Validation ID: {validation_id}")
            print()

        # Check for validation mode
        if "validation_mode" in result:
            print(f"✓ Validation Mode: {result['validation_mode']}")

        # Check for LLM enabled
        if "llm_enabled" in result:
            print(f"✓ LLM Enabled: {result['llm_enabled']}")

        print()

        # Check for fuzzy detection
        if "plugin_detection" in result:
            fuzzy_result = result["plugin_detection"]
            detections = fuzzy_result.get("detections", [])
            confidence = fuzzy_result.get("confidence", 0.0)
            print(f"✓ Fuzzy Detection:")
            print(f"  - Detections: {len(detections)}")
            print(f"  - Confidence: {confidence:.2f}")
            if detections:
                for det in detections[:3]:  # Show first 3
                    print(f"    • {det.get('plugin', 'unknown')}: {det.get('match_text', '')[:50]}")
        else:
            print("⚠ No fuzzy detection results (may be disabled or no plugins detected)")

        print()

        # Check for LLM validation
        if "llm_validation" in result:
            llm_result = result["llm_validation"]
            requirements = llm_result.get("requirements", [])
            issues = llm_result.get("issues", [])
            confidence = llm_result.get("confidence", 0.0)
            print(f"✓ LLM Validation:")
            print(f"  - Requirements: {len(requirements)}")
            print(f"  - Issues: {len(issues)}")
            print(f"  - Confidence: {confidence:.2f}")
        else:
            print("⚠ No LLM validation results (may be disabled)")

        print()

        # Check for content validation
        if "content_validation" in result:
            content_val = result["content_validation"]
            issues = content_val.get("issues", [])
            print(f"✓ Content Validation:")
            print(f"  - Issues: {len(issues)}")

        print()

        # Check for final issues
        if "final_issues" in result:
            final_issues = result["final_issues"]
            print(f"✓ Final Issues (combined and gated): {len(final_issues)}")

            # Show breakdown
            by_level = {}
            by_source = {}
            for issue in final_issues:
                level = issue.get("level", "unknown")
                source = issue.get("source_stage", "unknown")
                by_level[level] = by_level.get(level, 0) + 1
                by_source[source] = by_source.get(source, 0) + 1

            print(f"  By Level: {by_level}")
            print(f"  By Source: {by_source}")

        print()

        # Check for overall confidence
        if "overall_confidence" in result:
            print(f"✓ Overall Confidence: {result['overall_confidence']:.2f}")

        if "gating_score" in result:
            print(f"✓ Gating Score: {result['gating_score']:.2f}")

        print()

        # Check for the fuzzy unavailable warning
        all_issues = result.get("final_issues", []) + result.get("content_validation", {}).get("issues", [])
        fuzzy_unavailable = any(
            "fuzzy" in issue.get("category", "").lower() and "unavailable" in issue.get("message", "").lower()
            for issue in all_issues
        )

        if fuzzy_unavailable:
            print("✗ WARNING: Fuzzy detector still showing as unavailable!")
        else:
            print("✓ No fuzzy unavailable warnings")

        print()
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)

        has_fuzzy = "plugin_detection" in result
        has_llm = "llm_validation" in result
        has_validation_id = "id" in result or "validation_id" in result

        if has_fuzzy and has_llm and has_validation_id:
            print("✓✓✓ FIX VERIFIED: Fuzzy and LLM validation are both working!")
        elif has_fuzzy and not has_llm:
            print("⚠ Fuzzy is working but LLM validation is not running (check LLM config)")
        elif not has_fuzzy and has_llm:
            print("⚠ LLM is working but fuzzy detection is not running (check fuzzy agent)")
        else:
            print("✗ Neither fuzzy nor LLM validation is working")

        print()

        # Save full result for inspection
        with open("validation_test_result.json", "w") as f:
            json.dump(result, f, indent=2)
        print("Full result saved to: validation_test_result.json")

    else:
        print(f"✗ Request failed with status {response.status_code}")
        print(response.text)

except requests.exceptions.Timeout:
    print("✗ Request timed out (validation may be taking too long)")
except requests.exceptions.ConnectionError:
    print("✗ Could not connect to server (is it running?)")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
