---
title: Getting Started with Apose.Words
family: Words
---

# Getting Started with Apose.Words

This guide will help you get started with Aspose.Word for .NET.

#### Installation Steps

You can install Apose.Words using NuGet Package Manager.

```
Install-Package Aspose.Words
```

### Basic Usage

Here's how to create a simple document using Aspose.Word:

```
Document doc = new Document();
DocumentBuilder builder = new DocumentBuilder(doc);
builder.Writeln("Hello World!");
doc.Save("output.docx");
```

## Advanced Features

Aspose.Word provides many advanced features for document manipulation including:

- Mail merge functionality
- Document conversion
- Working with tables and images
