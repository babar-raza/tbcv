---
title: "Advanced Document Processing with Multiple Plugins"
description: "Comprehensive guide showing how to use multiple plugins together for complex document workflows including conversion, merging, and watermarking."
date: "2024-01-15"
layout: "tutorial"
categories: ["documentation", "advanced"]
plugin_family: "words"
---

# Advanced Document Processing

This guide demonstrates complex workflows using multiple plugins for comprehensive document processing.

## Document Conversion and Merging

The following example shows document conversion combined with merging:
```csharp
// Load multiple Word documents
Document doc1 = new Document("input1.docx");
Document doc2 = new Document("input2.docx");

// Merge documents using Document Merger plugin
doc1.AppendDocument(doc2, ImportFormatMode.KeepSourceFormatting);

// Add watermark using Document Watermark plugin  
TextWatermarkOptions options = new TextWatermarkOptions();
options.Text = "CONFIDENTIAL";
doc1.Watermark.SetText(options);

// Convert to PDF using PDF Processor + Converter plugins
PdfSaveOptions pdfOptions = new PdfSaveOptions();
doc1.Save("merged_output.pdf", pdfOptions);
```

## Plugin Dependencies

This workflow requires:
- **Word Processor** (base functionality)
- **Document Merger** (for combining documents)
- **Document Watermark** (for adding watermarks)
- **PDF Processor** (for PDF output)
- **Document Converter** (for format conversion)

## External Code Reference

{{< gist microsoft-samples 12345abcdef "DocumentProcessor.cs" >}}

For more examples, see our [plugin gallery](https://example.com/plugins).

{{< info "This example demonstrates multi-plugin dependencies and proper resource disposal patterns." >}}