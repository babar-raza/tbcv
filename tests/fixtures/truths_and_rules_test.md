---
title: "Comprehensive Truths and Rules Test Document"
description: "This document tests the integration of truth data and validation rules across multiple validation types including YAML frontmatter validation, plugin detection, code quality checks, and structure analysis."
date: "2024-01-15"
layout: "test"
categories: ["testing", "validation"]
plugins: ["Word Processor", "PDF Processor", "Document Converter"]
family: "words"
---

# Truths and Rules Integration Test

This document demonstrates how truth data and validation rules work together to provide comprehensive content validation.

## Truth Data Usage

The truth data provides ground facts about plugins:
- Plugin names and IDs
- Supported formats
- Dependencies
- Capabilities

## Rules Usage

The validation rules provide:
- API patterns for code detection
- Non-editable YAML fields
- Code quality requirements
- Plugin combination rules

## Code Example with API Patterns
```csharp
using Aspose.Words;

// Create document - should be detected by document_creation pattern
Document doc = new Document("input.docx");

// Configure PDF options
PdfSaveOptions options = new PdfSaveOptions();
options.Compliance = PdfCompliance.PdfA1b;

// Save with format conversion - should trigger converter requirements
doc.Save("output.pdf", options);

// Resource disposal - should validate against best practices
doc.Dispose();
```

## Plugin Dependencies

This example demonstrates:
1. **Word Processor** - for document loading and manipulation
2. **PDF Processor** - for PDF output format
3. **Document Converter** - for cross-format conversion

## External References

Check out this example: {{< gist example-user abcd1234 "DocumentConverter.cs" >}}

For more information, visit [Aspose.Words Documentation](https://docs.aspose.com/words/).

{{< info "This document tests both truth validation and rule-driven pattern matching." >}}

## Validation Coverage

This document should trigger validation across:
- YAML frontmatter (truths check plugin existence, rules check non-editable fields)
- Code blocks (rules detect API patterns, truths verify plugin combinations)
- Markdown structure (rules validate shortcodes and links)
- Plugin alignment (truths provide dependency info, rules enforce requirements)