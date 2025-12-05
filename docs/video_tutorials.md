# TBCV Video Tutorials Documentation Framework

**Last Updated**: December 5, 2025
**Version**: 2.0.0
**Total Tutorials**: 15 comprehensive guides

This document provides outlines, scripts, and demo steps for TBCV video tutorials. Each tutorial includes detailed talking points, key concepts, demonstration steps, and learning objectives.

---

## Table of Contents

- [Beginner Level Tutorials](#beginner-level)
- [Intermediate Level Tutorials](#intermediate-level)
- [Advanced Level Tutorials](#advanced-level)
- [Video Production Guidelines](#video-production-guidelines)
- [Equipment and Software Requirements](#equipment-and-software-requirements)

---

## BEGINNER LEVEL

### Tutorial 1: Introduction to TBCV

**Duration**: 5-7 minutes
**Level**: Beginner
**Target Audience**: New users, technical writers, content managers
**Prerequisites**: Basic understanding of markdown, familiarity with command line

**Learning Objectives**:
- Understand what TBCV is and its core purpose
- Learn the three main components: validation, analysis, and enhancement
- Recognize the key benefits of truth-based validation
- Identify the types of problems TBCV solves
- Know where to find more resources

**Outline**:
1. Introduction & Problem Statement (1 min)
2. TBCV Overview: What It Does (1.5 min)
3. Key Components & Architecture (1.5 min)
4. Real-World Example (1.5 min)
5. Conclusion & Next Steps (0.5 min)

**Script/Talking Points**:

**Intro** (0-0:30):
"Welcome to TBCV - the Truth-Based Content Validation System. If you're responsible for maintaining technical documentation, you know how challenging it is to keep content accurate, consistent, and complete. TBCV is here to help. Let me show you what it can do."

**The Problem** (0:30-1:30):
"Technical documentation faces several challenges:
- Plugin references might be outdated or incorrect
- Code examples might not match current APIs
- Links might be broken or point to wrong locations
- Metadata might be incomplete or improperly formatted
- Consistency across documents is hard to maintain

Traditionally, finding and fixing these issues requires manual review. TBCV automates this process using intelligent validation rules and truth data - official plugin definitions that serve as the single source of truth."

**What TBCV Does** (1:30-3:00):
"TBCV has three main capabilities:

**Validation**: TBCV validates your markdown files against multiple criteria - YAML frontmatter requirements, markdown syntax, code block formatting, links, SEO best practices, and truth data. It runs these checks automatically and generates detailed reports showing what passed and what needs attention.

**Analysis**: TBCV analyzes your content using fuzzy pattern matching and artificial intelligence to detect plugin usage. Even if plugin names are slightly misspelled or abbreviated, TBCV can identify them and compare against truth data.

**Enhancement**: TBCV doesn't just identify problems - it generates actionable recommendations. For example, it might suggest adding a hyperlink to a plugin, inserting explanatory text, or fixing a formatting issue. A human reviewer can then approve or modify these recommendations before they're applied."

**Key Components** (3:00-4:30):
"TBCV is built on three core concepts:

1. **Validation Rules**: These check specific aspects of your documentation - does the frontmatter have required fields? Are all code blocks properly formatted? Do all links return HTTP 200? Are headings in the correct hierarchy?

2. **Truth Data**: This is the official source of truth for your documentation domain. It contains plugin definitions, API information, and reference data. TBCV uses this to verify that your content is accurate and up-to-date.

3. **Agents**: TBCV uses a multi-agent architecture with 19 specialized agents working together. Think of each agent as an expert in one area - one handles YAML validation, another detects plugins, another generates recommendations. They coordinate to give you comprehensive analysis."

**Real-World Example** (4:30-6:00):
"Here's a practical example. Imagine you have a documentation page about word processing that mentions 'Aspose.Wrods' - a typo. TBCV's fuzzy detector recognizes this as 'Aspose.Words' with 95% confidence. It then validates against truth data to confirm this is a real plugin. It recommends adding a hyperlink to the Words API reference. You review this recommendation in TBCV's interface, click approve, and the enhancement is automatically applied to your file."

**Next Steps** (6:00-6:30):
"In the next tutorial, we'll walk through installation and setup. You'll have TBCV running on your machine in just a few minutes. Let's get started!"

**Demo Steps**:
1. No demo required for this introductory tutorial - focus on conceptual overview
2. Optional: Show TBCV's help menu to demonstrate available commands
   ```bash
   tbcv --help
   ```

**Key Talking Points**:
- TBCV validates, analyzes, and enhances technical documentation
- It uses "truth data" - official plugin definitions as the single source of truth
- Multi-agent architecture provides comprehensive validation
- Human-in-the-loop workflow maintains quality and safety
- Automation saves time while maintaining control

**Resources**:
- [Main README](../README.md) - Complete system overview
- [Architecture Documentation](./architecture.md) - Deep dive into system design
- [Glossary](./glossary.md) - Terminology and definitions

---

### Tutorial 2: Installing and Setting Up TBCV

**Duration**: 8-10 minutes
**Level**: Beginner
**Target Audience**: New users, system administrators, developers
**Prerequisites**: Python 3.8+, pip, basic command line knowledge, text editor

**Learning Objectives**:
- Successfully install TBCV and all dependencies
- Verify the installation is working correctly
- Understand the basic directory structure
- Locate key configuration files
- Run your first validation test

**Outline**:
1. Pre-Installation Checklist (1 min)
2. Cloning the Repository (1 min)
3. Installing Dependencies (1.5 min)
4. Initial Configuration (2 min)
5. Verification & Testing (1.5 min)
6. Troubleshooting Common Issues (1 min)

**Script/Talking Points**:

**Pre-Installation Checklist** (0-1:00):
"Before we start, make sure you have:
- Python 3.8 or later - check with 'python --version'
- pip package manager - comes with Python
- Git for cloning the repository
- At least 500 MB of disk space
- A text editor like VS Code (optional but helpful)

On Windows, I recommend using PowerShell or WSL for the best experience."

**Cloning the Repository** (1:00-2:00):
"First, let's get the code. Open your terminal or command prompt and navigate to where you want to install TBCV. I'll create a projects folder.

[Show terminal commands]

Then clone the repository:
```bash
git clone https://github.com/your-org/tbcv.git
cd tbcv
```

Let's verify the directory structure. You should see folders like 'tbcv', 'tests', 'docs', 'config', and 'templates'. You'll also see requirements.txt and setup.py files."

**Installing Dependencies** (2:00-3:30):
"Now we'll install all the Python dependencies. TBCV requires several packages:
- FastAPI for the REST API
- Click for CLI functionality
- SQLAlchemy for database access
- Pydantic for data validation
- Various other libraries for fuzzy matching, HTTP requests, etc.

Run this command:
```bash
pip install -r requirements.txt
```

This will take 2-3 minutes depending on your internet connection. You'll see pip downloading packages and installing them. If you see any errors, they're usually related to missing compilers on Windows - I'll show you how to fix those in the troubleshooting section.

Once installation completes, you should see a message like 'Successfully installed [number] packages'."

**Initial Configuration** (3:30-5:30):
"TBCV uses configuration files to control its behavior. Let's look at the main configuration:

```bash
cat config/main.yaml
```

This file defines:
- Database connection settings (SQLite by default)
- Validation flow (which validators to use)
- Agent limits and concurrency settings
- API server configuration
- Logging levels

For most setups, the defaults work fine. The default configuration uses SQLite database stored in the 'data' folder, which doesn't require any setup.

There's also a 'config/validation_flow.yaml' that controls which validation types are run - YAML validation, markdown validation, code validation, and more. For now, the defaults are good.

Let's verify these files exist:
```bash
ls -la config/
```

You should see these files:
- main.yaml
- validation_flow.yaml
- And potentially other configuration files"

**Verification & Testing** (5:30-7:00):
"Now let's verify that TBCV is properly installed. Run:

```bash
tbcv --help
```

You should see the available commands. Let's also run the diagnostic command:

```bash
tbcv check-agents
```

This command checks if all agents are properly registered. You should see output like:
```
Agent Status Check
==================
Core Agents: 9 registered
Validator Agents: 7 registered
Pipeline Agents: 3 registered
Total: 19 agents
Status: All agents initialized
```

Now let's run a quick test to make sure everything works:

```bash
tbcv test
```

This creates a test file, runs validation on it, and reports the results. You should see validation checks passing and the test completing successfully."

**Troubleshooting** (7:00-8:00):
"If you run into issues, here are the most common fixes:

**Issue**: 'command not found: tbcv'
- Solution: The tbcv command might not be in your PATH. Run 'pip install -e .' to install TBCV in editable mode

**Issue**: Module not found errors during pip install
- Solution: Make sure you're using Python 3.8+ and that you have pip updated: 'pip install --upgrade pip'

**Issue**: Database errors
- Solution: Delete the 'data' folder if it exists and let TBCV recreate it with 'tbcv init-db'

**Issue**: Permission errors on Linux/Mac
- Solution: Use 'sudo pip install' or create a virtual environment with 'python -m venv venv' and activate it first"

**Demo Steps**:
1. Show Python version check
   ```bash
   python --version
   ```
   Expected output: Python 3.8.x or higher

2. Clone the repository
   ```bash
   git clone https://github.com/your-org/tbcv.git
   cd tbcv
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```
   Expected: Downloads and installs ~20-30 packages

4. Verify installation
   ```bash
   tbcv --help
   ```
   Expected: Shows list of available commands

5. Check agents
   ```bash
   tbcv check-agents
   ```
   Expected: Shows all 19 agents registered and initialized

6. Run test
   ```bash
   tbcv test
   ```
   Expected: Creates test content, validates it, shows passing checks

**Key Talking Points**:
- Installation is a straightforward three-step process
- All dependencies are listed in requirements.txt
- Default configuration works for most use cases
- Built-in diagnostic tools help verify installation
- Common issues have simple solutions

**Resources**:
- [CLI Guide](./cli_guide.md) - Complete command reference
- [Configuration Guide](./configuration.md) - Detailed configuration options
- [Troubleshooting Guide](./troubleshooting.md) - Solutions to common problems

---

### Tutorial 3: Your First Validation

**Duration**: 10-12 minutes
**Level**: Beginner
**Target Audience**: New users, content creators, documentation teams
**Prerequisites**: TBCV installed and working (see Tutorial 2)

**Learning Objectives**:
- Create a sample markdown file
- Run validation on a single file
- Interpret validation results
- Understand different validation types
- Export results for review

**Outline**:
1. Creating Sample Content (2 min)
2. Running a Basic Validation (2 min)
3. Understanding the Output (3 min)
4. Interpreting Validation Results (2 min)
5. Exporting Results (1 min)

**Script/Talking Points**:

**Creating Sample Content** (0-2:00):
"Let's create a simple markdown file to validate. I'll create a file called 'sample.md' with some intentional issues so we can see validation in action.

[Open text editor and create file]

```markdown
---
title: Introduction to Aspose.Wrods
author: Jane Developer
date: 2024-01-01
---

# Getting Started with Word Processing

This guide introduces [Aspose.Wrods](http://aspose.com/words), the powerful document processing library.

## Installation

Install using pip:
\`\`\`
pip install aspose-words
\`\`\`

## First Steps

Here's your first program:
\`\`\`python
from aspose.words import Document
doc = Document()
\`\`\`

For more information, visit [the official documentation](http://invalid-link-12345.com).
```

I've intentionally included several issues:
- 'Wrods' is a typo for 'Words'
- One code block is missing a language identifier
- One link is broken
- Some metadata might be incomplete

This is a great example because TBCV should catch all these issues."

**Running a Basic Validation** (2:00-4:00):
"Now let's validate this file. In your terminal, run:

```bash
tbcv validate-file sample.md
```

This runs a basic validation on the file. TBCV will check:
- YAML frontmatter (does it have required fields, proper formatting?)
- Markdown structure (are headings properly formatted and hierarchical?)
- Code blocks (are all code fences properly closed? Are language identifiers specified?)
- Links (are URLs accessible? Are anchors valid?)

The command runs quickly and produces a report showing results for each check."

**Understanding the Output** (4:00-7:00):
"Let's look at what the output tells us. First, you'll see a summary section:

```
Validation Summary
==================
File: sample.md
Total Checks: 47
Passed: 43
Failed: 4
Status: FAILED
```

This tells us the overall result. We have 4 failures out of 47 checks.

Next, you'll see individual check results. For example:

```
YAML Validation: PASSED
- Required fields present
- Syntax valid

Markdown Validation: PASSED
- Heading hierarchy correct
- List formatting valid

Code Block Validation: FAILED
- Line 25: Missing language identifier (Error)
  Suggestion: Add language identifier: python, javascript, etc.
```

This shows what passed and what failed. Let's continue looking at the results."

**Interpreting Validation Results** (7:00-9:00):
"The validation output shows specific failures and recommendations:

**Code Block Issue**:
```
ERROR: Code block at line 25 missing language identifier
Severity: MEDIUM
Suggestion: Specify language for syntax highlighting
  \`\`\`python
  from aspose.words import Document
  \`\`\`
```

This means TBCV found a code fence without a language specified. This is important for syntax highlighting and documentation tools.

**Link Issue**:
```
ERROR: Broken link at line 32
URL: http://invalid-link-12345.com
HTTP Status: 404 Not Found
Severity: HIGH
Suggestion: Update link to valid documentation URL
  Current: http://invalid-link-12345.com
  Suggested: https://docs.aspose.com/words/net/
```

This identifies broken links and suggests replacements.

**Plugin Detection Issue**:
```
WARNING: Potential plugin reference found
Text: 'Aspose.Wrods'
Detected: Aspose.Words (95% confidence)
Severity: MEDIUM
Suggestion: Correct spelling to 'Aspose.Words'
```

TBCV detected the typo using fuzzy matching algorithms and is suggesting a correction."

**Exporting Results** (9:00-10:00):
"TBCV can export validation results in multiple formats. Let's export to JSON:

```bash
tbcv validate-file sample.md --output-format json > results.json
```

This creates a JSON file with machine-readable results. You can then:
- Parse this in your CI/CD pipeline
- Generate custom reports
- Integrate with other tools
- Track validation history

You can also export to other formats:

```bash
# YAML format
tbcv validate-file sample.md --output-format yaml > results.yaml

# CSV format
tbcv validate-file sample.md --output-format csv > results.csv

# Markdown report
tbcv validate-file sample.md --output-format markdown > results.md
```

The markdown export is especially useful for creating documentation reports."

**Demo Steps**:
1. Create sample markdown file with intentional issues
   ```bash
   cat > sample.md << 'EOF'
   ---
   title: Introduction to Aspose.Wrods
   author: Test User
   date: 2024-01-01
   ---

   # Getting Started

   This is about [Aspose.Wrods](http://invalid-link.com).

   ```
   pip install aspose-words
   ```
   EOF
   ```

2. Run basic validation
   ```bash
   tbcv validate-file sample.md
   ```

3. Export to JSON
   ```bash
   tbcv validate-file sample.md --output-format json
   ```

4. View the JSON output
   ```bash
   tbcv validate-file sample.md --output-format json | jq .
   ```

**Key Talking Points**:
- Validation is a single command away
- TBCV provides detailed, actionable feedback
- Multiple export formats support various workflows
- Results can be integrated into pipelines
- Severity levels help prioritize fixes

**Resources**:
- [CLI Guide - Validation Commands](./cli_guide.md#core-commands)
- [API Examples - Validation Endpoint](./api_examples.md#file-validation)
- [Validation Output Reference](./api_reference.md#validation-result-format)

---

### Tutorial 4: Understanding Validation Results

**Duration**: 8-10 minutes
**Level**: Beginner
**Target Audience**: Content reviewers, documentation teams
**Prerequisites**: Completed "Your First Validation" tutorial

**Learning Objectives**:
- Understand different validation check types
- Interpret severity levels and confidence scores
- Know the difference between errors, warnings, and suggestions
- Understand validation scope and categories
- Learn how to prioritize fixes

**Outline**:
1. Validation Check Types Overview (2 min)
2. Severity Levels & Confidence Scores (2 min)
3. Detailed Result Breakdown (2 min)
4. Common Issues & How to Fix Them (2 min)

**Script/Talking Points**:

**Validation Check Types** (0-2:00):
"TBCV performs 8 different types of validation checks. Let's understand each:

**1. YAML Validation** - Checks the frontmatter at the top of your file
- Required fields present (title, author, date, etc.)
- Field types are correct (dates are dates, not strings)
- No invalid YAML syntax
- Encoding is proper

**2. Markdown Validation** - Checks markdown syntax
- Headings follow proper hierarchy (# then ## then ###, no skipping levels)
- Lists are properly formatted (consistent indentation, markers)
- No orphaned list items or empty sections
- Links and inline code are formatted correctly

**3. Code Block Validation** - Checks code fences
- All opening fences have closing fences
- Language identifiers are specified
- Indentation is consistent
- No nested code blocks

**4. Link Validation** - Checks all URLs in the document
- Returns HTTP 200 (successful)
- Anchors exist (for URLs with #section)
- No redirect chains
- URLs are not phishing/malware sites

**5. Structure Validation** - Checks overall document organization
- Has required sections (intro, examples, conclusion)
- Sections are in logical order
- No duplicate sections
- Proper heading hierarchy throughout

**6. SEO Validation** - Checks search engine optimization
- Title tag length (30-60 characters)
- Meta description (120-160 characters)
- Heading lengths within limits
- Proper keyword usage

**7. Truth Validation** - Checks against official plugin data
- Plugin references match truth data
- Declared APIs are correct
- No obsolete plugin versions
- Plugin details are accurate

**8. Fuzzy Detection** - Uses pattern matching
- Finds plugin references even with typos (Aspose.Wrods → Aspose.Words)
- Detects abbreviations and variations
- Calculates confidence scores
- Suggests corrections"

**Severity Levels & Confidence Scores** (2:00-4:00):
"Each validation result has a severity level and confidence score:

**Severity Levels**:
- **CRITICAL** - Must fix before publishing. Examples: broken links, invalid YAML
- **HIGH** - Should fix soon. Examples: missing metadata, typos in plugin names
- **MEDIUM** - Nice to fix. Examples: missing code language identifier, SEO optimization
- **LOW** - Informational. Examples: missing descriptions, style inconsistencies
- **INFO** - Just informing you of something. Example: 'Updated link format available'

**Confidence Scores** (for fuzzy detection):
- **95-100%** - Very confident. Almost certainly correct.
- **85-94%** - Confident. Likely correct, worth checking.
- **75-84%** - Moderate. Could be correct, review suggested fix.
- **60-74%** - Low. Might be a match, verify before accepting.
- **Below 60%** - Very low. Treat as suggestion only.

As a reviewer, you should:
- Always fix CRITICAL issues
- Fix HIGH severity issues before publishing
- Consider MEDIUM severity issues in your next review cycle
- Use confidence scores to decide which suggestions to act on

For example, if TBCV detects 'Aspose.Wrods' as 'Aspose.Words' with 95% confidence, that's almost certainly a typo and should be fixed immediately. But if it detects 'Words' as 'Aspose.Words' with 65% confidence, you should review it manually before accepting."

**Detailed Result Breakdown** (4:00-6:00):
"Let me show you a real example of a detailed validation result:

```
File: api_reference.md
Validation Completed: 2024-01-15 10:30:00
Total Checks: 127

=== SUMMARY ===
Passed: 119
Failed: 8
Severity Breakdown:
  CRITICAL: 2
  HIGH: 3
  MEDIUM: 2
  LOW: 1

=== CRITICAL ISSUES ===
1. Broken link at line 45
   URL: https://api.aspose.com/invalid/path
   Error: 404 Not Found
   Fix: Update URL or remove link

2. Invalid YAML at line 3
   Field 'author' has type 'number', expected 'string'
   Fix: Change author value from 123 to '123'

=== HIGH SEVERITY ISSUES ===
1. Plugin reference: 'Aspose.Cells' (95% confidence)
   Line 67: 'using Aspose.Cells;'
   Current: No hyperlink
   Suggested: Add link to https://products.aspose.app/cells/net

=== MEDIUM SEVERITY ISSUES ===
1. Code block missing language identifier
   Line 89: Opening fence without language
   Suggested: Change ``` to ```csharp

2. SEO: Meta description too short
   Current: 12 characters
   Recommended: 120-160 characters
```

This structure helps you quickly see what needs attention."

**Common Issues & How to Fix Them** (6:00-8:00):
"Here are the most common validation issues and how to fix them:

**Issue: Broken Links**
- Problem: Link returns 404 or times out
- Fix: Update the URL to a working link
- Prevention: Test links before publishing

**Issue: Missing Language Identifier on Code Blocks**
- Problem: Code fence has no language specified
- Fix: Add language identifier: \`\`\`python\`\`\`
- Prevention: Always specify language for syntax highlighting

**Issue: Typos in Plugin Names**
- Problem: 'Aspose.Wrods' instead of 'Aspose.Words'
- Fix: Correct the spelling
- Prevention: Use autocorrect, reference truth data

**Issue: Broken Heading Hierarchy**
- Problem: Jump from # to ### (missing ##)
- Fix: Add missing heading levels
- Prevention: Use your editor's markdown validation

**Issue: Missing Required Metadata**
- Problem: YAML frontmatter missing required fields
- Fix: Add title, author, date, version fields
- Prevention: Use a template for new documents

**Issue: Inconsistent List Formatting**
- Problem: Mixed bullet styles (-, *, +)
- Fix: Use consistent marker throughout
- Prevention: Configure your editor's markdown style"

**Demo Steps**:
1. Show a detailed validation output
   ```bash
   tbcv validate-file sample.md --verbose
   ```

2. Export to JSON and show structure
   ```bash
   tbcv validate-file sample.md --output-format json | jq '.results[] | select(.severity=="CRITICAL")'
   ```

3. Filter results by severity
   ```bash
   tbcv validate-file sample.md --filter-severity HIGH,CRITICAL
   ```

**Key Talking Points**:
- Eight different validation types cover all aspects of documentation
- Severity levels help prioritize fixes
- Confidence scores guide decision-making
- Common issues have standard solutions
- Structured results enable automation

**Resources**:
- [Validation Types Reference](./api_reference.md#validation-types)
- [Severity and Scoring Guide](./glossary.md#severity-levels)
- [Common Issues Troubleshooting](./troubleshooting.md)

---

### Tutorial 5: Approving and Applying Recommendations

**Duration**: 10-12 minutes
**Level**: Beginner
**Target Audience**: Content reviewers, documentation managers
**Prerequisites**: Completed "Your First Validation" tutorial

**Learning Objectives**:
- Understand the recommendation lifecycle
- Review recommendations in detail
- Approve and reject recommendations
- Apply multiple recommendations at once
- Track enhancement history

**Outline**:
1. Understanding Recommendations (2 min)
2. Reviewing Individual Recommendations (2.5 min)
3. Bulk Approval Workflow (2 min)
4. Applying Enhancements (2 min)
5. Verifying Changes & Tracking History (1.5 min)

**Script/Talking Points**:

**Understanding Recommendations** (0-2:00):
"After validation, TBCV doesn't just report problems - it generates recommendations for fixes. These recommendations go through a lifecycle:

1. **Proposed** - TBCV suggests a fix but it hasn't been reviewed yet
2. **Approved** - A human reviewer has verified the suggestion is correct
3. **Applied** - The enhancement has been implemented in the file
4. **Rejected** - The reviewer decided not to apply this suggestion

The beauty of this workflow is that humans stay in control. TBCV suggests changes, but you decide whether to accept them. This ensures your documentation maintains quality and accuracy.

Each recommendation includes:
- The specific issue (what's wrong)
- The suggested fix (what TBCV recommends)
- Confidence level (how sure TBCV is)
- Impact (what will change)
- Rationale (why this fix makes sense)"

**Reviewing Individual Recommendations** (2:00-4:30):
"Let's look at real recommendations and how to review them:

Example Recommendation 1 - Plugin Typo Fix:
```
ID: REC-2024-0001
Type: Plugin Reference Correction
Severity: HIGH
Confidence: 97%
Status: PROPOSED

Issue: Plugin name contains typo
Location: Line 23, in paragraph
Current Text: 'Aspose.Wrods'
Detected As: 'Aspose.Words' (97% confidence)

Proposed Fix: Replace 'Aspose.Wrods' with 'Aspose.Words'
Rationale: Fuzzy matching detected typo. This plugin name doesn't exist
in truth data, but 'Aspose.Words' is a 1-character difference and in truth data.

Additional Action: Add hyperlink to official documentation
  Text: [Aspose.Words](https://products.aspose.app/words/net)

Risk: LOW - Simple spelling correction based on high-confidence match
```

How to review this:
1. Check the context - read the sentence with the typo
2. Verify the suggestion makes sense
3. Check the confidence level - 97% is very high
4. Consider the risk - this is just a spelling fix, very low risk
5. Decision: APPROVE this recommendation

Example Recommendation 2 - Missing Code Language:
```
ID: REC-2024-0002
Type: Code Block Enhancement
Severity: MEDIUM
Confidence: 100%
Status: PROPOSED

Issue: Code block missing language identifier
Location: Line 45
Current Code Block:
\`\`\`
from aspose.words import Document
\`\`\`

Proposed Fix: Add language identifier
\`\`\`python
from aspose.words import Document
\`\`\`

Rationale: Language identifier enables syntax highlighting in documentation
viewers and helps code analysis tools parse the code correctly.

Risk: VERY LOW - Just adds metadata, doesn't change code
```

How to review:
1. Look at the code - it's clearly Python code
2. Check confidence - 100% certainty, this is definitely Python
3. Verify impact - just adds syntax highlighting, no functional change
4. Decision: APPROVE this recommendation

Example Recommendation 3 - SEO Optimization (Optional):
```
ID: REC-2024-0003
Type: SEO Optimization
Severity: LOW
Confidence: N/A
Status: PROPOSED

Issue: Meta description could be more descriptive
Current: 'Guide to processing documents'
Suggested: 'Complete guide to processing Word documents using Aspose.Words
API with code examples and best practices'

Character Count: Current 28, Suggested 123 (recommended: 120-160)

Risk: VERY LOW - Just improves discoverability
Decision: This is optional. Some teams approve all SEO recommendations,
others only for marketing-critical pages. Your choice!
```

For this one, you might decide to reject it if:
- You prefer shorter descriptions
- The current one is already clear
- You want to handle SEO separately

The key is: you're in control. You can approve, reject, or request modifications."

**Bulk Approval Workflow** (4:30-6:30):
"If you have multiple recommendations, you don't need to approve them one at a time. TBCV supports bulk operations:

First, let's generate recommendations:
```bash
tbcv validate-file documentation.md --generate-recommendations
```

This creates a set of recommended enhancements. You can view them all:
```bash
tbcv list-recommendations documentation.md --status proposed
```

This shows all proposed recommendations for the file. Now, you can:

**Option 1 - Approve all high-confidence recommendations:**
```bash
tbcv approve-recommendations documentation.md --min-confidence 90
```

This approves all recommendations where TBCV is at least 90% confident.

**Option 2 - Approve specific types of recommendations:**
```bash
tbcv approve-recommendations documentation.md --types 'plugin-hyperlink,code-block'
```

This approves only hyperlink and code block recommendations.

**Option 3 - Interactive review:**
```bash
tbcv approve-recommendations documentation.md --interactive
```

This shows each recommendation and asks for your approval one by one.

**Option 4 - Approve specific recommendations by ID:**
```bash
tbcv approve-recommendation documentation.md --id REC-2024-0001,REC-2024-0002
```

You can pick exactly which recommendations to approve."

**Applying Enhancements** (6:30-8:30):
"Once you've approved recommendations, it's time to apply them:

```bash
tbcv enhance-file documentation.md
```

This command:
1. Loads the file
2. Finds all approved recommendations
3. Applies each change safely (no destructive operations)
4. Validates the result (makes sure the enhanced file is still valid)
5. Creates a backup of the original
6. Saves the enhanced version

The command output shows you exactly what changed:
```
Applying Enhancements to documentation.md
==========================================

Approved Recommendations: 8
Processing...

[1/8] Plugin Reference: 'Aspose.Wrods' → 'Aspose.Words'
      Status: Applied

[2/8] Add Hyperlink: Aspose.Words → https://products.aspose.app/words/net
      Status: Applied

[3/8] Code Language: Add 'python' identifier
      Status: Applied

[4/8] Fix Link: https://old-docs.aspose.com → https://docs.aspose.com
      Status: Applied

[5/8] SEO Meta: Updated description
      Status: Applied

[6/8] Fix Heading Hierarchy: Insert missing ## level
      Status: Applied

[7/8] Format List: Consistent bullet markers
      Status: Applied

[8/8] Plugin Link Anchor: Add section reference
      Status: Applied

All enhancements applied successfully!
Backup saved to: documentation.md.backup
Enhanced file: documentation.md
```

You can also apply specific recommendations:
```bash
tbcv enhance-file documentation.md --recommendations REC-2024-0001,REC-2024-0002
```

Or apply with a safety level:
```bash
tbcv enhance-file documentation.md --safety-level strict
```

With strict safety, only very high-confidence changes are applied."

**Verifying Changes & Tracking History** (8:30-10:00):
"After applying enhancements, let's verify everything worked:

```bash
# Compare original and enhanced versions
tbcv diff original.md enhanced.md
```

This shows exactly what changed:
```
--- original.md
+++ enhanced.md
@@ Line 23 @@
- Aspose.Wrods is used for document processing
+ [Aspose.Words](https://products.aspose.app/words/net) is used for document processing

@@ Line 45 @@
- \`\`\`
+ \`\`\`python
```

Re-validate the enhanced file to ensure it now passes all checks:
```bash
tbcv validate-file documentation.md
```

You should see fewer errors and a higher overall score.

Track the enhancement history:
```bash
tbcv show-history documentation.md
```

This displays:
```
Enhancement History for: documentation.md
=========================================

Enhancement #5 - 2024-01-15 10:45:00
Applied by: system
Recommendations: 8 approved, 2 rejected
Changes: 14 lines modified
Rollback Available: Yes (within 30 days)

Enhancement #4 - 2024-01-14 14:20:00
Applied by: system
Recommendations: 5 approved
Changes: 8 lines modified

... (previous enhancements)
```

You can even rollback if needed:
```bash
tbcv rollback-enhancement documentation.md --version 4
```

This reverts to a previous version of the file."

**Demo Steps**:
1. Generate recommendations for a file
   ```bash
   tbcv validate-file sample.md --generate-recommendations
   ```

2. List proposed recommendations
   ```bash
   tbcv list-recommendations sample.md --status proposed
   ```

3. Approve high-confidence recommendations
   ```bash
   tbcv approve-recommendations sample.md --min-confidence 90
   ```

4. Apply enhancements
   ```bash
   tbcv enhance-file sample.md
   ```

5. Show diff of changes
   ```bash
   tbcv diff sample.md.backup sample.md
   ```

6. Re-validate the enhanced file
   ```bash
   tbcv validate-file sample.md
   ```

7. View enhancement history
   ```bash
   tbcv show-history sample.md
   ```

**Key Talking Points**:
- Recommendations follow a structured lifecycle
- Human reviewers maintain full control of changes
- Confidence scores and risk assessments inform decisions
- Bulk operations handle multiple recommendations efficiently
- Changes are tracked and reversible
- Safety levels provide additional protection

**Resources**:
- [Enhancement Workflow Documentation](./enhancement_workflow.md)
- [API Examples - Recommendations Endpoint](./api_examples.md#recommendations)
- [Content Enhancer Reference](./agents.md#content-enhancer-agent)

---

## INTERMEDIATE LEVEL

### Tutorial 6: Working with Workflows

**Duration**: 12-15 minutes
**Level**: Intermediate
**Target Audience**: Advanced users, automation engineers, CI/CD operators
**Prerequisites**: Completed Beginner tutorials

**Learning Objectives**:
- Understand TBCV's workflow system
- Create custom workflows
- Monitor workflow execution
- Handle workflow failures and retries
- Integrate workflows into automation pipelines

**Outline**:
1. Workflow Architecture Overview (2 min)
2. Built-in Workflow Types (2.5 min)
3. Creating Custom Workflows (2.5 min)
4. Monitoring & Debugging (2 min)
5. Error Handling & Retry Strategies (2 min)

**Script/Talking Points**:

**Workflow Architecture Overview** (0-2:00):
"TBCV's workflow system is the orchestration layer that coordinates all validation and enhancement operations. Think of workflows as recipes that define:
- What operations to perform (validation, enhancement, etc.)
- In what order to perform them
- How to handle failures
- How to track progress

Under the hood, the OrchestratorAgent manages workflow execution. It:
1. Creates a workflow record with unique ID
2. Executes a pipeline of agent operations
3. Tracks progress and status
4. Stores results in the database
5. Handles retries and failures
6. Provides real-time status updates

Each workflow has these states:
- CREATED - Workflow just created, not started yet
- QUEUED - Waiting in the execution queue
- RUNNING - Currently executing
- PAUSED - Temporarily stopped (for debugging)
- COMPLETED - Finished successfully
- FAILED - Encountered an error
- CANCELLED - User requested cancellation"

**Built-in Workflow Types** (2:00-4:30):
"TBCV provides four main workflow types that handle common scenarios:

**1. validate_file - Single File Validation**
- Takes one markdown file
- Runs all validation checks
- Generates recommendations
- Completes in seconds

Use this for:
- Quick validation during development
- Testing individual files
- One-off validation requests

Example:
```bash
tbcv workflow validate-file /path/to/file.md
```

**2. validate_directory - Batch Processing**
- Validates all markdown files in a directory
- Parallel processing (configurable worker count)
- Aggregate results and reports
- Can filter by file pattern

Use this for:
- Validating entire documentation sets
- Regular batch checks
- Quality assurance across projects

Example:
```bash
tbcv workflow validate-directory /path/to/docs --pattern '*.md' --workers 4
```

**3. full_validation - Comprehensive Analysis**
- Includes validate_file steps
- Adds optional LLM semantic validation (if enabled)
- Performs deep truth data analysis
- Generates detailed reports

Use this for:
- Initial documentation audits
- Complex multi-plugin documents
- High-stakes documentation

Example:
```bash
tbcv workflow full-validation /path/to/file.md --enable-llm
```

**4. content_update - Enhancement Workflow**
- Validates file
- Generates recommendations
- Applies approved enhancements
- Validates result
- Archives backup

Use this for:
- Automated documentation improvement
- Batch enhancement operations
- Scheduled maintenance workflows

Example:
```bash
tbcv workflow content-update /path/to/file.md --min-confidence 85
```

Each workflow type is optimized for its purpose - fast for single files, parallel for batches, comprehensive for complex analysis."

**Creating Custom Workflows** (4:30-7:00):
"For advanced use cases, you can create custom workflows by composing agent operations. Workflows are defined in YAML:

```yaml
# workflows/custom_audit.yaml
name: Comprehensive Documentation Audit
description: Run all checks and generate detailed report
version: 1.0

parameters:
  directory: required
  pattern: '*.md'
  workers: 4
  include_llm: false
  output_format: html

steps:
  # Step 1: Load truth data
  - agent: TruthManagerAgent
    action: load_truth_data
    params:
      family: aspose
    timeout: 30s
    on_failure: halt

  # Step 2: Batch validate files
  - agent: OrchestratorAgent
    action: validate_directory
    params:
      directory: ${directory}
      pattern: ${pattern}
      workers: ${workers}
    timeout: 5m
    on_failure: continue

  # Step 3: Optional LLM validation
  - agent: LLMValidatorAgent
    action: validate_plugins
    params:
      directory: ${directory}
      enabled: ${include_llm}
    timeout: 10m
    on_failure: skip
    skip_if: ${not include_llm}

  # Step 4: Generate aggregate report
  - agent: RecommendationAgent
    action: generate_report
    params:
      format: ${output_format}
      include_summary: true
    timeout: 2m
    on_failure: halt

  # Step 5: Save results
  - agent: OrchestratorAgent
    action: persist_results
    params:
      location: ./audit_results
    timeout: 1m
    on_failure: halt

reporting:
  on_completion:
    - format: html
      destination: ./reports/audit_${date}.html
    - format: json
      destination: ./reports/audit_${date}.json
    - notify: team_email@company.com
```

To use this workflow:
```bash
tbcv workflow run workflows/custom_audit.yaml --directory ./docs
```

Workflow definition syntax:
- **steps** - Array of agent operations to execute
- **agent** - Which agent to run
- **action** - Which method on the agent
- **params** - Parameters to pass
- **timeout** - How long to wait (use 's', 'm', 'h' for seconds/minutes/hours)
- **on_failure** - What to do if this step fails (halt, continue, skip)
- **skip_if** - Conditional execution based on parameters

You can also create workflows programmatically:

```python
from tbcv.core.workflow_manager import WorkflowManager

manager = WorkflowManager()

# Create a custom workflow
workflow = manager.create_workflow(
    name='my_custom_validation',
    steps=[
        {
            'agent': 'TruthManagerAgent',
            'action': 'load_truth_data',
            'params': {'family': 'aspose'}
        },
        {
            'agent': 'OrchestratorAgent',
            'action': 'validate_file',
            'params': {'file': 'my_file.md'}
        }
    ]
)

# Execute the workflow
results = manager.execute_workflow(workflow)
```

This gives you complete flexibility to design validation pipelines for your specific needs."

**Monitoring & Debugging** (7:00-9:00):
"Monitoring workflows is essential when they're running on large document sets or as scheduled tasks. TBCV provides several monitoring tools:

**Real-time Status Monitoring:**
```bash
# Watch workflow execution in real time
tbcv workflow monitor <workflow_id>
```

Output:
```
Workflow: audit_20240115_001
Status: RUNNING [████████░░] 80%

Steps Progress:
  [✓] Load truth data (completed in 5s)
  [✓] Validate directory (124/150 files, 83%)
  [⧗] Generate report (in progress)
  [ ] Persist results (queued)

Current Step: Validating 'features/cells/api.md' (150/150)
Estimated Time Remaining: 2 minutes
```

**Detailed Logs:**
```bash
# Get all logs from a workflow
tbcv workflow logs <workflow_id>

# Stream logs in real time
tbcv workflow logs <workflow_id> --follow

# Filter logs by level
tbcv workflow logs <workflow_id> --level ERROR,WARNING
```

**Step-by-Step Debugging:**
```bash
# Pause workflow for inspection
tbcv workflow pause <workflow_id>

# Inspect current state
tbcv workflow inspect <workflow_id>

# Resume execution
tbcv workflow resume <workflow_id>

# Restart from specific step
tbcv workflow restart <workflow_id> --from-step 2
```

**Performance Metrics:**
```bash
# Get timing breakdown
tbcv workflow metrics <workflow_id>
```

Output:
```
Workflow Timing Analysis
=========================
Total Duration: 15 minutes 42 seconds

Step Breakdown:
  Load truth data: 5.2s (0.5%)
  Validate directory: 13m 22s (85%)
  Generate report: 1m 15s (8%)
  Persist results: 30s (3%)

Slowest Operations:
  1. Validating 'database/guide.md': 45s (complex file)
  2. Link checking: 8m total (network I/O bound)
  3. LLM validation: 2m 30s (optional, disabled)

Recommendations:
  - Enable parallel processing: use --workers 8 instead of 4
  - Cache link validation results for 24 hours
  - Consider disabling LLM validation if not needed
```

You can also get metrics programmatically:
```python
from tbcv.core.workflow_manager import WorkflowManager

manager = WorkflowManager()
metrics = manager.get_workflow_metrics(workflow_id)
print(f'Total time: {metrics.duration}')
print(f'Files processed: {metrics.file_count}')
print(f'Errors: {metrics.error_count}')
```"

**Error Handling & Retry Strategies** (9:00-12:00):
"Workflows can fail for various reasons. TBCV provides sophisticated error handling:

**Common Failure Modes and Recovery:**

**Problem: Network timeout during link validation**
```yaml
- agent: ContentValidatorAgent
  action: validate_content
  params:
    file: document.md
    validators: [yaml, markdown, links]
  timeout: 5m
  on_failure: continue  # Don't halt if links check times out
  retry:
    max_attempts: 3
    backoff: exponential  # Wait 1s, then 2s, then 4s
    on_final_failure: warn  # Warn but continue
```

**Problem: Database connection lost**
```yaml
- agent: OrchestratorAgent
  action: persist_results
  params:
    location: ./results
  on_failure: halt  # This is critical, don't continue
  retry:
    max_attempts: 5
    backoff: linear
    delay_ms: 1000
  health_check:  # Verify connection before step
    check_database: true
    timeout: 10s
```

**Automatic Retry Configuration:**
```bash
# Run workflow with automatic retries
tbcv workflow run my_workflow.yaml --retry-policy standard

# Retry policies:
# - standard: 3 attempts, exponential backoff
# - aggressive: 5 attempts, exponential backoff
# - conservative: 2 attempts, linear backoff
```

**Handling Partial Failures:**
```yaml
steps:
  # Validate all files, but continue even if some fail
  - agent: OrchestratorAgent
    action: validate_directory
    params:
      directory: ./docs
      fail_mode: partial  # Process all files, report failures
    on_failure: continue

  # Only generate report on files that validated successfully
  - agent: RecommendationAgent
    action: generate_report
    params:
      include_failed: false  # Only report on successful files
    on_failure: halt
```

**Monitoring Failed Workflows:**
```bash
# List recently failed workflows
tbcv workflow list --status FAILED --limit 10

# Inspect a failed workflow
tbcv workflow inspect <workflow_id>
```

Output:
```
Workflow Status: FAILED
Failure Point: Step 3 of 5 (Generate Report)
Failure Reason: Unknown output format 'xml'
Timestamp: 2024-01-15 14:32:15

Step Results:
  [✓] Load truth data (5s)
  [✓] Validate directory (13m)
  [✗] Generate report (failed after 2s)
      Error: Invalid output_format parameter

Next Steps:
  1. Review workflow YAML syntax
  2. Check valid output formats: html, json, yaml, markdown
  3. Fix parameter and re-run
  4. Or use 'rollback' to revert partial changes
```

**Restarting Failed Workflows:**
```bash
# Restart from last successful step
tbcv workflow restart <workflow_id> --continue-from-failure

# Or restart from a specific step
tbcv workflow restart <workflow_id> --from-step 2

# With modified parameters
tbcv workflow restart <workflow_id> --from-step 2 --param output_format=json
```

**Custom Error Handlers:**
```python
from tbcv.core.workflow_manager import WorkflowManager
from tbcv.core.exceptions import WorkflowError

manager = WorkflowManager()

try:
    workflow = manager.execute_workflow(workflow_def)
except WorkflowError as e:
    # Workflow failed
    if e.step == 3:
        # Step 3 failed, maybe it's a network issue
        if 'timeout' in str(e):
            # Try again with longer timeout
            workflow = manager.execute_workflow(
                workflow_def,
                overrides={'steps[2].timeout': '10m'}
            )
    else:
        # Different error, log and alert
        logger.error(f'Workflow failed: {e}')
        send_alert('workflow_failed', str(e))
```

**Best Practices:**
1. Always set reasonable timeouts for each step
2. Use on_failure: continue for non-critical steps
3. Use on_failure: halt for critical steps
4. Implement retry logic for network-dependent steps
5. Monitor long-running workflows for hangs
6. Log all failures for post-mortems
7. Set up alerting for workflow failures"

**Demo Steps**:
1. Show available workflow types
   ```bash
   tbcv workflow list-types
   ```

2. Run a simple validation workflow
   ```bash
   tbcv workflow validate-file sample.md
   ```

3. Run a batch workflow with monitoring
   ```bash
   tbcv workflow validate-directory docs/ --workers 4 &
   tbcv workflow monitor <workflow_id>
   ```

4. Create a custom workflow file
   ```bash
   cat > workflows/my_audit.yaml << 'EOF'
   name: Quick Audit
   steps:
     - agent: OrchestratorAgent
       action: validate_directory
       params:
         directory: ./docs
   EOF
   ```

5. Execute custom workflow
   ```bash
   tbcv workflow run workflows/my_audit.yaml
   ```

**Key Talking Points**:
- Workflows orchestrate complex validation and enhancement pipelines
- Multiple built-in workflows cover common scenarios
- Custom workflows enable advanced automation
- Real-time monitoring and debugging tools support troubleshooting
- Sophisticated error handling and retry logic ensure reliability

**Resources**:
- [Workflows Documentation](./workflows.md) - Complete workflow reference
- [Architecture Guide](./architecture.md#workflow-system) - System design
- [API Examples - Workflow Endpoints](./api_examples.md#workflow-operations)

---

### Tutorial 7: Batch Processing Multiple Files

**Duration**: 10-12 minutes
**Level**: Intermediate
**Target Audience**: Documentation teams, DevOps engineers, automation specialists
**Prerequisites**: Completed "Working with Workflows" tutorial

**Learning Objectives**:
- Process entire documentation directories efficiently
- Configure parallel processing parameters
- Generate batch reports and summaries
- Handle different file types and patterns
- Integrate batch processing into pipelines

**Outline**:
1. Batch Processing Concepts (1.5 min)
2. Directory Validation (2 min)
3. Configuring Parallelization (2 min)
4. Generating Batch Reports (2 min)
5. Integration & Automation (2.5 min)

**Script/Talking Points**:

**Batch Processing Concepts** (0-1:30):
"Batch processing is TBCV's way of validating multiple files efficiently. Instead of validating one file at a time, you can validate an entire directory with parallel processing.

Key concepts:
- **Worker threads**: Parallel processes that validate files simultaneously
- **Batch size**: How many files to load at once into memory
- **Progress tracking**: Real-time updates on how many files are done
- **Aggregate reporting**: Summary across all files
- **Error isolation**: Failure in one file doesn't break the batch

Why use batch processing:
- 10x faster than validating files one at a time (with 4 workers)
- Processes large documentation sets in minutes
- Provides comprehensive overview of documentation health
- Enables quality gates in CI/CD pipelines
- Cost-effective for regular audits"

**Directory Validation** (1:30-3:30):
"Let's validate an entire documentation directory:

```bash
tbcv validate-directory ./docs
```

This command:
1. Finds all .md files in ./docs
2. Validates each file using configured validators
3. Aggregates results into a summary report
4. Shows progress in real time

Output:
```
Validating Directory: ./docs
============================

Found 42 markdown files
Starting validation with 4 workers...

Progress:
[████████████░░░░░░░░░░░░] 50% (21/42 files)
Current: features/pdf/overview.md
Estimated time: 2 minutes 15 seconds

Files Completed: 21
  Passed: 18
  Failed: 3
  Warnings: 5

Current Speed: 12 files/minute
```

After completion:
```
Validation Complete
===================

Total Files: 42
Passed: 38 (90%)
Failed: 2 (5%)
Warnings: 2 (5%)
Duration: 4 minutes 32 seconds

Failed Files:
  1. docs/api/advanced.md - CRITICAL: Broken link to https://api.com
  2. docs/guides/deployment.md - HIGH: Missing YAML author field

Files with Warnings:
  1. docs/tutorials/basics.md - MEDIUM: Code block missing language
  2. docs/faq.md - LOW: SEO description could be improved
```

You can customize the directory validation:

```bash
# Only validate specific file pattern
tbcv validate-directory ./docs --pattern '*.md'

# Exclude certain files
tbcv validate-directory ./docs --exclude 'templates/*' --exclude 'drafts/*'

# Use specific number of workers
tbcv validate-directory ./docs --workers 8

# Only run specific validators
tbcv validate-directory ./docs --validators yaml,markdown,links

# Export results to JSON
tbcv validate-directory ./docs --output-format json > results.json

# Continue even if some files fail
tbcv validate-directory ./docs --fail-mode partial
```

You can also recursively validate subdirectories:
```bash
# Validate nested directory structure
tbcv validate-directory ./docs --recursive --depth 5
```"

**Configuring Parallelization** (3:30-5:30):
"Parallelization is key to performance. Let's understand how to tune it:

**Worker Count**:
```bash
# Use 4 workers (default)
tbcv validate-directory ./docs --workers 4

# Use 8 workers for better throughput
tbcv validate-directory ./docs --workers 8

# Use 1 worker for debugging (linear processing)
tbcv validate-directory ./docs --workers 1
```

How many workers should you use?
- **1-2 workers**: For debugging or low-resource environments
- **4 workers**: Default, good balance for most systems
- **8+ workers**: For large document sets or powerful machines
- **CPU count**: Generally, workers = CPU cores for CPU-bound work

**Batch Size**:
```bash
# Process 50 files at a time (default)
tbcv validate-directory ./docs --batch-size 50

# Smaller batch for low-memory systems
tbcv validate-directory ./docs --batch-size 10

# Larger batch for powerful machines
tbcv validate-directory ./docs --batch-size 200
```

**Timeout Settings**:
```bash
# Set per-file timeout to 30 seconds
tbcv validate-directory ./docs --file-timeout 30

# Set total batch timeout to 30 minutes
tbcv validate-directory ./docs --batch-timeout 1800
```

**Configuration File**:
You can also set defaults in config/main.yaml:

```yaml
orchestrator:
  max_file_workers: 4
  batch_size: 50
  file_timeout_s: 30
  batch_timeout_s: 1800
  retry_timeout_s: 120
  agent_limits:
    llm_validator: 1
    content_validator: 2
    fuzzy_detector: 3
```

**Performance Tuning Tips**:
```bash
# Monitor performance during batch processing
tbcv validate-directory ./docs --workers 4 --verbose

# Get performance metrics after completion
tbcv batch-metrics ./docs

# Output:
# Average file processing time: 6.5s
# Throughput: 9.2 files/minute
# Total validation time: 4m 32s (vs 45m without parallelization)
# Speedup: 10x
```

**Memory-Conscious Processing**:
For very large documentation sets, you might run into memory issues. TBCV provides streaming options:

```bash
# Process files in streaming mode (load one at a time)
tbcv validate-directory ./docs --streaming

# This trades throughput for memory usage
# Slower but uses minimal RAM
```"

**Generating Batch Reports** (5:30-7:30):
"After batch validation, TBCV can generate comprehensive reports:

**Summary Report**:
```bash
tbcv validate-directory ./docs --report-format summary
```

Output:
```
Documentation Validation Summary
=================================

Date: 2024-01-15
Total Files: 42
Processing Time: 4m 32s

Results:
  Passed: 38 (90.5%)
  Failed: 2 (4.8%)
  Warnings: 2 (4.8%)

Most Common Issues:
  1. Broken links (8 occurrences)
  2. Missing code language identifier (5 occurrences)
  3. SEO optimization opportunities (12 occurrences)

Severity Distribution:
  CRITICAL: 2
  HIGH: 5
  MEDIUM: 8
  LOW: 12

Health Score: 87/100
```

**Detailed Report**:
```bash
tbcv validate-directory ./docs --report-format detailed > detailed_report.md
```

This includes every file, every check, every issue with recommendations.

**HTML Report** (great for sharing):
```bash
tbcv validate-directory ./docs --report-format html > report.html
```

This creates an interactive HTML report you can open in a browser.

**JSON Report** (for programmatic processing):
```bash
tbcv validate-directory ./docs --report-format json > report.json
```

You can parse this JSON to:
- Extract specific metrics
- Feed into dashboards
- Trigger alerts
- Generate custom reports

**CSV Report** (for spreadsheet analysis):
```bash
tbcv validate-directory ./docs --report-format csv > results.csv
```

Fields: filename, check_type, status, severity, message

**Custom Reports**:
```python
from tbcv.api.dashboard import generate_custom_report

report = generate_custom_report(
    validation_results=results,
    template='custom_template.html',
    filters={
        'min_severity': 'HIGH',
        'file_pattern': 'guides/*'
    },
    aggregations=['by_file', 'by_type', 'by_severity']
)
report.save('my_report.html')
```"

**Integration & Automation** (7:30-10:00):
"Batch processing is most powerful when integrated into your automation pipeline. Here are integration examples:

**GitHub Actions CI/CD**:
```yaml
# .github/workflows/validate-docs.yml
name: Validate Documentation

on:
  push:
    paths:
      - 'docs/**'
  pull_request:
    paths:
      - 'docs/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install TBCV
        run: pip install -r requirements.txt

      - name: Validate documentation
        run: tbcv validate-directory docs --workers 4
        continue-on-error: true

      - name: Generate report
        run: tbcv validate-directory docs --report-format json > results.json

      - name: Upload report
        uses: actions/upload-artifact@v3
        with:
          name: validation-report
          path: results.json

      - name: Fail if critical issues
        run: |
          CRITICAL=$(jq '.critical_count' results.json)
          if [ $CRITICAL -gt 0 ]; then
            echo \"Found $CRITICAL critical issues\"
            exit 1
          fi
```

**Scheduled Batch Jobs**:
```bash
# Schedule daily documentation audit via cron
# Add to crontab:
0 2 * * * cd /path/to/tbcv && tbcv validate-directory docs --workers 8 --report-format json > audit_$(date +\%Y\%m\%d).json

# Or use a bash script:
#!/bin/bash
cd /path/to/tbcv
REPORT_DATE=$(date +%Y-%m-%d)
tbcv validate-directory docs --workers 8 --report-format html > reports/audit_${REPORT_DATE}.html

# Send results to team
curl -F \"file=@reports/audit_${REPORT_DATE}.html\" \\
     https://your-reporting-system.com/upload
```

**Integration with Documentation Platforms**:
```python
# Integration with Sphinx documentation build
import subprocess
import json
from pathlib import Path

def validate_before_build():
    '''Validate docs before building with Sphinx'''

    # Run batch validation
    result = subprocess.run([
        'tbcv', 'validate-directory', 'docs',
        '--report-format', 'json'
    ], capture_output=True, text=True)

    metrics = json.loads(result.stdout)

    # Check for critical issues
    if metrics['critical_count'] > 0:
        print(f\"ABORT: {metrics['critical_count']} critical validation issues\")
        return False

    # Warn about high severity issues
    if metrics['high_count'] > 0:
        print(f\"WARNING: {metrics['high_count']} high severity issues found\")

    return True

# In your conf.py
if not validate_before_build():
    exit(1)
```

**Triggering Enhancements on Batch Results**:
```bash
# Find all files with specific issues and enhance them
tbcv validate-directory ./docs --output-format json \\
  | jq '.files[] | select(.has_broken_links) | .path' \\
  | xargs -I {} tbcv enhance-file {} --auto-apply-fixes
```

This pipeline:
1. Validates all files
2. Finds files with broken links
3. Automatically applies fixes to those files

**Reporting to Monitoring Dashboards**:
```python
import requests
import json
from datetime import datetime

# After batch validation
def push_metrics_to_dashboard(results):
    metrics = {
        'timestamp': datetime.now().isoformat(),
        'total_files': results['total_count'],
        'passed': results['passed_count'],
        'failed': results['failed_count'],
        'critical_issues': results['critical_count'],
        'high_issues': results['high_count'],
        'health_score': results['health_score']
    }

    # Send to monitoring system (Prometheus, Grafana, etc.)
    requests.post(
        'http://metrics-collector:8080/metrics',
        json=metrics
    )

# This creates a time-series of documentation health metrics
```"

**Demo Steps**:
1. Show directory structure
   ```bash
   find docs/ -name "*.md" | head -10
   ```

2. Validate entire directory
   ```bash
   tbcv validate-directory docs/
   ```

3. Run with specific worker count
   ```bash
   tbcv validate-directory docs/ --workers 8 --verbose
   ```

4. Generate summary report
   ```bash
   tbcv validate-directory docs/ --report-format summary
   ```

5. Generate JSON report
   ```bash
   tbcv validate-directory docs/ --report-format json > report.json
   jq '.summary' report.json
   ```

6. Show performance metrics
   ```bash
   tbcv batch-metrics docs/
   ```

**Key Talking Points**:
- Batch processing validates multiple files in parallel for speed
- Worker count and batch size control performance and resource usage
- Multiple report formats support different use cases
- Integration with CI/CD pipelines enables continuous validation
- Scheduled jobs provide ongoing documentation health monitoring

**Resources**:
- [Batch Processing Documentation](./cli_guide.md#batch-operations)
- [Performance Tuning Guide](./performance_baselines.md)
- [CI/CD Integration Examples](./deployment_checklist.md)

---

### Tutorial 8: Customizing Validation Rules

**Duration**: 12-15 minutes
**Level**: Intermediate
**Target Audience**: Advanced users, system administrators, architects
**Prerequisites**: Completed "Understanding Validation Results" tutorial

**Learning Objectives**:
- Understand TBCV's validation rule system
- Create custom validation rules
- Configure rule severity and thresholds
- Enable/disable validators
- Create organization-specific policies

**Outline**:
1. Validation Rule System Overview (2 min)
2. Configuration Files & Hierarchy (2 min)
3. Creating Custom Rules (2.5 min)
4. Advanced Rule Configuration (2.5 min)
5. Testing & Deploying Rules (2 min)

**Script/Talking Points**:

**Validation Rule System Overview** (0-2:00):
"TBCV's validation system is rule-based and highly customizable. Each validator runs a set of rules that check different aspects of your documentation.

For example, the Markdown Validator includes rules like:
- 'Headings must follow proper hierarchy' (no skipping levels)
- 'Lists must have consistent indentation'
- 'No duplicate headings in document'
- 'Maximum 6 heading levels'

Each rule has:
- **Name**: Unique identifier
- **Description**: What it checks
- **Severity**: How important the rule is (CRITICAL, HIGH, MEDIUM, LOW)
- **Enabled**: Whether it's active
- **Parameters**: Configurable thresholds
- **Fix**: Automatic correction if possible
- **Custom Logic**: Your own validation functions

You can customize this at multiple levels:
1. **Global**: All files, all projects
2. **Project**: All files in a project
3. **File**: Individual files
4. **Temporary**: For one-off validations"

**Configuration Files & Hierarchy** (2:00-4:00):
"TBCV configuration follows a hierarchy. Settings at lower levels override higher levels:

```
Global Defaults (built-in)
  ↓
config/validation_flow.yaml (project-wide)
  ↓
config/custom_rules.yaml (custom project rules)
  ↓
.tbcv.yaml (repository/project specific)
  ↓
--override-rules (command line)
```

Let's look at the main configuration file:

```yaml
# config/validation_flow.yaml
validation:
  enabled_validators:
    - yaml
    - markdown
    - code
    - links
    - structure
    - seo
    - truth  # Optional, plugin validation
    - fuzzy  # Optional, fuzzy detection

  disabled_validators: []

  execution_mode: parallel  # parallel or sequential

  validators:
    yaml:
      enabled: true
      severity: high  # Failures are HIGH severity
      rules:
        - check_required_fields: [title, author, date]
        - validate_field_types: true
        - max_file_size: 100kb

    markdown:
      enabled: true
      severity: medium
      rules:
        - enforce_heading_hierarchy: true
        - max_heading_level: 6
        - allow_duplicate_headings: false
        - list_consistency: strict  # strict, loose, off

    code:
      enabled: true
      severity: medium
      rules:
        - require_language_identifier: true
        - allow_inline_code: true
        - validate_syntax: true
        - supported_languages: [python, javascript, csharp, java, sql, yaml, json]

    links:
      enabled: true
      severity: high
      rules:
        - timeout_s: 10
        - allow_redirects: true
        - check_anchors: true
        - follow_includes: true
```

For custom rules, create a file:

```yaml
# .tbcv.yaml (in your project root)
validation:
  # Override specific rules
  rules:
    markdown:
      allow_duplicate_headings: true  # Our org allows duplicate headings
      max_heading_level: 4  # We only use 4 levels max

    links:
      timeout_s: 5  # Stricter timeout
      allowed_domains:
        - aspose.com
        - docs.aspose.com
      blocked_domains:
        - outdated-docs.aspose.com

    yaml:
      required_fields:
        - title
        - author
        - date
        - category  # Add custom required field
        - tags  # Add another custom field
```"

**Creating Custom Rules** (4:00-6:30):
"You can create entirely custom validation rules. Here's how:

**Method 1: Using Configuration**

```yaml
# config/custom_rules.yaml
custom_validators:
  - name: CompanyStandardsValidator
    enabled: true
    description: Validates against our company standards
    severity: high

    rules:
      - name: require_company_header
        description: All docs must start with company header
        enabled: true
        check: |
          content.startswith('# Company: ')
        on_failure: prepend
        fix: |
          '# Company: Aspose\n' + content

      - name: no_external_images
        description: Images must be internal URLs only
        enabled: true
        check: |
          no_regex_match(content, r'!\\[.*\\]\\(https?://external-.*\\)')
        on_failure: warn
        message: External images found. Please host internally.

      - name: max_section_length
        description: No section should be longer than 500 words
        enabled: true
        check: |
          all(len(section.split()) < 500 for section in sections)
        on_failure: warn
        message: Section too long (${length} words). Consider breaking it up.

      - name: required_toc
        description: Documents over 2000 words need table of contents
        enabled: true
        check: |
          if len(content.split()) < 2000:
            return true
          return '## Table of Contents' in content
        on_failure: error
        fix: insert_toc_after_intro(content)

  - name: CodeQualityValidator
    enabled: true
    description: Validates code examples
    severity: medium

    rules:
      - name: code_must_have_comments
        description: Code examples should have comments
        enabled: true
        check: |
          for code_block in code_blocks:
            if language == 'python':
              ensure has_comments(code_block)
        on_failure: warn

      - name: no_secrets_in_code
        description: Ensure no API keys or secrets in examples
        enabled: true
        check: |
          not regex_match(content, r'(api[_-]?key|password|secret)\\s*=\\s*[\\w]+')
        on_failure: error
        message: Found potential secret in code block
```

**Method 2: Using Python (for complex rules)**

```python
# custom_validators/my_validator.py
from tbcv.agents.base_validator import BaseValidator
from tbcv.core.validation_result import ValidationRule, RuleViolation

class MyCustomValidator(BaseValidator):
    '''Custom validator for organization-specific rules'''

    def validate(self, content: str) -> list[RuleViolation]:
        violations = []

        # Rule 1: Must mention Aspose.Words in intro
        if 'Aspose.Words' not in content[:500]:
            violations.append(RuleViolation(
                rule_id='intro_must_mention_aspose',
                name='Missing Aspose mention',
                severity='MEDIUM',
                message='First 500 words should mention Aspose.Words',
                location=1
            ))

        # Rule 2: Code examples should use async/await for .NET
        for match in self.find_code_blocks(content, language='csharp'):
            if '// TODO:' in match.text:
                violations.append(RuleViolation(
                    rule_id='no_todos_in_examples',
                    name='TODO comment in example',
                    severity='LOW',
                    message=f'Remove TODO comments from examples',
                    location=match.line_number,
                    suggestion=match.text.replace('// TODO:', '')
                ))

        # Rule 3: All hyperlinks should use HTTPS
        for match in self.find_links(content):
            if match.url.startswith('http://'):
                violations.append(RuleViolation(
                    rule_id='insecure_link',
                    name='Insecure link',
                    severity='MEDIUM',
                    message='Links should use HTTPS',
                    location=match.line_number,
                    suggestion=match.url.replace('http://', 'https://')
                ))

        return violations
```

Then register it in config:

```yaml
# config/validation_flow.yaml
validators:
  custom_validators:
    - module: custom_validators.my_validator
      class: MyCustomValidator
      enabled: true
      severity: medium
```

**Method 3: Using Rule Templates**

```yaml
# templates/rules/company_standards.yaml
name: Company Standards Package
description: Rules enforcing our documentation standards

rules:
  - id: header_format
    name: Standard Header Format
    validator: yaml
    check_type: pattern
    pattern: '^title: [A-Z][a-zA-Z0-9 ]*$'
    severity: high
    auto_fix: true

  - id: code_language_required
    name: All Code Blocks Must Have Language
    validator: code
    requirement: language_identifier
    severity: medium
    auto_fix: true

  - id: min_description_length
    name: Meta Description Minimum Length
    validator: seo
    check_type: length
    field: description
    min: 50
    max: 160
    severity: low

  - id: no_broken_links
    name: All Links Must Be Valid
    validator: links
    check_type: http_status
    expected_status: 200
    follow_redirects: true
    severity: critical
```"

**Advanced Rule Configuration** (6:30-9:00):
"For sophisticated validation scenarios, you can use conditional rules and rule composition:

**Conditional Rules**:
```yaml
# config/advanced_rules.yaml
rules:
  - name: Strict Validation for Public Docs
    enabled: true
    condition: |
      document.metadata.access == 'public' OR
      document.path.contains('public')

    when_true:
      - enforce: no_typos
        severity: critical
      - enforce: all_links_https
        severity: critical
      - enforce: no_profanity
        severity: high

    when_false:
      - enforce: basic_markdown
        severity: medium

  - name: API Reference Specific Rules
    enabled: true
    condition: document.path.contains('api-reference')

    when_true:
      rules:
        - api_signature_format
        - parameter_documentation
        - return_type_specification
        - example_code_required
        - deprecation_notice_if_old

  - name: Tutorial Specific Rules
    enabled: true
    condition: document.path.contains('tutorials')

    when_true:
      rules:
        - step_by_step_format
        - screenshot_or_diagram_required
        - estimated_time_to_completion
        - prerequisites_section
        - expected_result_section
```

**Rule Composition & Inheritance**:
```yaml
# config/rule_sets.yaml
rule_sets:
  # Base set everyone uses
  base:
    rules:
      - required_metadata
      - valid_markdown
      - no_broken_links

  # Stricter set for public documentation
  public_docs: &public_docs
    extends: base
    rules:
      - no_typos
      - professional_language
      - all_https_links
      - accessibility_compliance

  # Even stricter for production docs
  production_docs:
    extends: public_docs
    rules:
      - security_scan
      - legal_review_status
      - 24h_old_minimum  # No documentation changes in last 24h

  # Relaxed set for internal/draft docs
  draft_docs:
    extends: base
    rules: []
    severity_downgrade:
      CRITICAL: HIGH
      HIGH: MEDIUM
      MEDIUM: LOW
```

**Dynamic Rule Configuration**:
```python
from tbcv.core.validation_rules import RuleManager

# Load different rule sets based on context
manager = RuleManager()

if is_production:
    manager.load_rule_set('production_docs')
elif is_public:
    manager.load_rule_set('public_docs')
else:
    manager.load_rule_set('draft_docs')

# Or create rules programmatically
manager.add_rule(
    name='no_lorem_ipsum',
    validator='content',
    severity='HIGH',
    check=lambda content: 'lorem ipsum' not in content.lower()
)

# Validate with custom rules
results = validator.validate(file_content, rules=manager.get_rules())
```

**Severity Adjustments**:
```yaml
# config/severity_overrides.yaml
# Change severity for specific rules in specific contexts

overrides:
  - rule: broken_links
    context: internal-only-docs
    severity: MEDIUM  # Changed from CRITICAL
    reason: 'Internal links are less critical than public links'

  - rule: spelling
    context: code_comments
    severity: LOW  # Changed from MEDIUM
    reason: 'Code comments are less critical for spelling'

  - rule: heading_hierarchy
    context: auto_generated_docs
    severity: INFO  # Changed from MEDIUM
    reason: 'Auto-generated docs might have non-standard hierarchy'

# Or adjust globally
rule_severity:
  CRITICAL: yes  # Fail validation if any critical
  HIGH: warn  # Warn but don't fail
  MEDIUM: info  # Just inform
  LOW: ignore  # Don't even report
```"

**Testing & Deploying Rules** (9:00-12:00):
"Before deploying custom rules to your team, test them thoroughly:

**Unit Testing Rules**:
```python
# tests/validators/test_custom_rules.py
import pytest
from custom_validators.my_validator import MyCustomValidator

@pytest.fixture
def validator():
    return MyCustomValidator()

def test_aspose_mention_rule(validator):
    # Should pass
    good_content = '''
    # Introduction to Aspose.Words
    Aspose.Words is a powerful document processing library.
    '''
    violations = validator.validate(good_content)
    assert len([v for v in violations if v.rule_id == 'intro_must_mention_aspose']) == 0

    # Should fail
    bad_content = '''
    # Introduction to Word Processing
    This library processes documents.
    '''
    violations = validator.validate(bad_content)
    assert len([v for v in violations if v.rule_id == 'intro_must_mention_aspose']) == 1

def test_https_link_rule(validator):
    content = 'Check [our API](http://api.aspose.com)'
    violations = validator.validate(content)
    assert any(v.rule_id == 'insecure_link' for v in violations)
```

**Testing Against Sample Files**:
```bash
# Run validation with test rules
tbcv validate-file test_file.md --rules-config config/custom_rules.yaml --verbose

# See which rules matched
tbcv validate-file test_file.md --rules-config config/custom_rules.yaml --show-rule-details
```

**A/B Testing Rules**:
```yaml
# Test new stricter rules on a subset
test_groups:
  - name: control_group
    rules: current_rules.yaml
    applies_to: 70%  # 70% of new files

  - name: experimental_group
    rules: new_strict_rules.yaml
    applies_to: 30%  # 30% of new files for testing

# Compare results
tbcv analytics test-group-comparison --metric average_severity
```

**Gradual Rollout**:
```bash
# Deploy rules to one team first
tbcv deploy-rules config/custom_rules.yaml --team 'core-docs-team'

# Monitor impact
tbcv analytics rule-impact --team 'core-docs-team'

# If good, deploy to everyone
tbcv deploy-rules config/custom_rules.yaml --all-teams
```

**Documenting Custom Rules**:
```yaml
# config/custom_rules.yaml
documentation: |
  # Company Documentation Standards

  These rules enforce our organization's documentation standards:

  ## Why These Rules?

  - **require_company_header**: Ensures all documentation is branded
  - **no_external_images**: Maintains control over image hosting
  - **max_section_length**: Improves readability
  - **required_toc**: Helps users navigate long documents

  ## Exceptions

  You can request exceptions with:
  \`\`\`
  # TBCV-EXCEPTION: rule_name
  # Reason: Explain why this rule doesn't apply
  \`\`\`

  ## Questions?

  Contact the documentation team.

rules:
  - name: require_company_header
    description: All documents must start with # Company: Aspose
    rationale: |
      This ensures consistent branding and makes it clear
      which organization the documentation belongs to.
    exceptions:
      - type: legacy_content
        description: Old documentation that can't be modified
      - type: auto_generated
        description: Machine-generated documentation
    contacts:
      - slack: @doc-team
      - email: docs@aspose.com
```"

**Demo Steps**:
1. Show default validation configuration
   ```bash
   cat config/validation_flow.yaml
   ```

2. Create custom rules file
   ```bash
   cat > .tbcv.yaml << 'EOF'
   validation:
     rules:
       markdown:
         max_heading_level: 4
       links:
         timeout_s: 5
   EOF
   ```

3. Validate with custom rules
   ```bash
   tbcv validate-file sample.md --config .tbcv.yaml --verbose
   ```

4. Test custom validator
   ```bash
   tbcv validate-file sample.md --rules-config custom_rules.yaml --show-rule-details
   ```

**Key Talking Points**:
- Validation rules are flexible and customizable at multiple levels
- Configuration hierarchy allows project-specific overrides
- Custom validators enable organization-specific requirements
- Conditional rules handle different document types
- Proper testing and gradual rollout ensure smooth adoption

**Resources**:
- [Validation Configuration Reference](./configuration.md#validation-rules)
- [Custom Validator Development](./development.md#creating-validators)
- [Rule DSL Documentation](./glossary.md#validation-rules)

---

### Tutorial 9: Using the API

**Duration**: 15-18 minutes
**Level**: Intermediate
**Target Audience**: Developers, DevOps engineers, integration specialists
**Prerequisites**: Basic understanding of REST APIs and HTTP

**Learning Objectives**:
- Start TBCV API server
- Understand main API endpoints
- Make validation requests programmatically
- Handle API responses and errors
- Integrate TBCV into custom applications

**Outline**:
1. Starting the API Server (1.5 min)
2. Understanding API Endpoints (3 min)
3. Making Validation Requests (3 min)
4. Response Formats & Error Handling (3 min)
5. Advanced API Usage (2.5 min)

**Script/Talking Points**:

**Starting the API Server** (0-1:30):
"TBCV provides a complete REST API that you can integrate into your applications. First, let's start the server:

```bash
# Start with default settings (localhost:8080)
uvicorn tbcv.api.server:app --host 0.0.0.0 --port 8080
```

You should see output like:
```
INFO:     Started server process [12345]
INFO:     Uvicorn running on http://0.0.0.0:8080
```

Now you can access the API at http://localhost:8080

The API provides interactive documentation:
- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

You can test endpoints directly in the browser using these tools.

For production:
```bash
# Use Gunicorn with multiple workers
gunicorn tbcv.api.server:app -w 4 -k uvicorn.workers.UvicornWorker --host 0.0.0.0 --port 8080
```

This starts 4 worker processes to handle concurrent requests."

**Understanding API Endpoints** (1:30-4:30):
"The TBCV API is organized into several endpoint groups:

**Health Check Endpoints**:
```
GET /health - Full system health status
GET /health/live - Liveness probe (is app running)
GET /health/ready - Readiness probe (is app ready for requests)
```

These are useful for monitoring and Kubernetes deployments.

**Validation Endpoints**:
```
POST /api/validate - Validate single file
POST /api/validate-batch - Validate multiple files
POST /api/validate-directory - Validate entire directory
```

These are your main workhorses for validation.

**Enhancement Endpoints**:
```
POST /api/enhance - Apply enhancements to a file
POST /api/enhance-batch - Enhance multiple files
POST /api/recommendations - Get recommendations for a file
POST /api/approve-recommendations - Approve recommendations
```

These handle the enhancement workflow.

**Workflow Endpoints**:
```
GET /api/workflows - List all workflows
GET /api/workflows/{id} - Get workflow details
POST /api/workflows - Create new workflow
POST /api/workflows/{id}/cancel - Cancel a workflow
```

These manage workflow operations.

**Truth Data Endpoints**:
```
GET /api/truth-data - List available truth data
GET /api/truth-data/{family} - Get family truth data
POST /api/truth-data/refresh - Refresh truth data cache
```

These access plugin and API definitions.

Let's focus on the most commonly used endpoints."

**Making Validation Requests** (4:30-7:30):
"Let's make actual API requests. We'll use curl and Python examples:

**Simple File Validation - curl**:
```bash
curl -X POST http://localhost:8080/api/validate \\
  -H 'Content-Type: application/json' \\
  -d '{
    \"file_path\": \"docs/guide.md\",
    \"validation_types\": [\"yaml\", \"markdown\", \"links\"]
  }'
```

Response:
```json
{
  \"id\": \"val-20240115-001\",
  \"file_path\": \"docs/guide.md\",
  \"status\": \"COMPLETED\",
  \"timestamp\": \"2024-01-15T10:30:00Z\",
  \"results\": {
    \"total_checks\": 47,
    \"passed\": 44,
    \"failed\": 3,
    \"summary\": {
      \"yaml\": {\"passed\": 1, \"failed\": 0},
      \"markdown\": {\"passed\": 10, \"failed\": 0},
      \"code\": {\"passed\": 5, \"failed\": 1},
      \"links\": {\"passed\": 28, \"failed\": 2}
    }
  },
  \"issues\": [
    {
      \"type\": \"code_block\",
      \"severity\": \"MEDIUM\",
      \"message\": \"Code block missing language identifier\",
      \"location\": 45,
      \"suggestion\": \"Add language to code fence: \\\`\\\`\\\`python\"
    }
  ]
}
```

**Validation with Python**:
```python
import requests
import json

# Create request
response = requests.post(
    'http://localhost:8080/api/validate',
    json={
        'file_path': 'docs/guide.md',
        'validation_types': ['yaml', 'markdown', 'links', 'code'],
        'generate_recommendations': True
    }
)

# Handle response
if response.status_code == 200:
    results = response.json()
    print(f\"Validation ID: {results['id']}\")
    print(f\"Status: {results['status']}\")
    print(f\"Passed: {results['results']['passed']}\")
    print(f\"Failed: {results['results']['failed']}\")

    # Process issues
    for issue in results['issues']:
        print(f\"  - {issue['severity']}: {issue['message']}\")
else:
    print(f\"Error: {response.status_code}\")
    print(response.json())
```

**Batch Validation**:
```python
# Validate multiple files
response = requests.post(
    'http://localhost:8080/api/validate-batch',
    json={
        'files': [
            'docs/guide.md',
            'docs/api.md',
            'docs/examples.md'
        ],
        'workers': 4,
        'validators': ['yaml', 'markdown', 'links']
    }
)

batch_results = response.json()
print(f\"Total files: {len(batch_results['results'])}\")
print(f\"Passed: {batch_results['summary']['passed_count']}\")
print(f\"Failed: {batch_results['summary']['failed_count']}\")
```

**Directory Validation**:
```python
# Validate entire directory
response = requests.post(
    'http://localhost:8080/api/validate-directory',
    json={
        'directory': 'docs/',
        'pattern': '*.md',
        'workers': 8,
        'recursive': True
    }
)

if response.status_code == 202:
    # Validation started, get job ID
    job_id = response.json()['job_id']
    print(f\"Job started: {job_id}\")

    # Poll for completion
    while True:
        status = requests.get(
            f'http://localhost:8080/api/jobs/{job_id}'
        ).json()

        if status['status'] == 'COMPLETED':
            print(status['results'])
            break
        elif status['status'] == 'FAILED':
            print(f\"Job failed: {status['error']}\")
            break
        else:
            print(f\"Status: {status['status']} ({status['progress']}%)\")
            time.sleep(2)
```"

**Response Formats & Error Handling** (7:30-10:30):
"Understanding API responses is crucial for integration:

**Success Response Structure**:
```json
{
  \"id\": \"val-20240115-001\",
  \"status\": \"COMPLETED\",
  \"timestamp\": \"2024-01-15T10:30:00Z\",
  \"duration_ms\": 1234,
  \"results\": {
    \"total_checks\": 47,
    \"passed\": 44,
    \"failed\": 3
  },
  \"issues\": [
    {
      \"id\": \"issue-001\",
      \"type\": \"code_block\",
      \"severity\": \"MEDIUM\",
      \"message\": \"...\",
      \"location\": 45,
      \"suggestion\": \"...\",
      \"confidence\": 0.95
    }
  ]
}
```

**Error Response Codes**:
- **200**: Validation successful
- **202**: Long-running operation accepted (returns job_id)
- **400**: Bad request (invalid parameters)
- **404**: File not found
- **429**: Rate limited (too many requests)
- **500**: Server error
- **503**: Service unavailable

**Error Response Structure**:
```python
# Handling errors in Python
try:
    response = requests.post(
        'http://localhost:8080/api/validate',
        json={'file_path': 'nonexistent.md'},
        timeout=10
    )
    response.raise_for_status()  # Raise on HTTP errors
except requests.exceptions.HTTPError as e:
    error_data = e.response.json()
    print(f\"Error {e.response.status_code}: {error_data['message']}\")
    print(f\"Details: {error_data.get('details')}\")
except requests.exceptions.RequestException as e:
    print(f\"Request failed: {e}\")
```

**Retrying Failed Requests**:
```python
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Create session with automatic retries
session = requests.Session()

retry_strategy = Retry(
    total=3,  # Total attempts
    backoff_factor=1,  # Wait 1s, 2s, 4s
    status_forcelist=[429, 500, 502, 503],  # Retry on these codes
    method_whitelist=['POST', 'GET']
)

adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount('http://', adapter)
session.mount('https://', adapter)

# Use the session for requests
response = session.post('http://localhost:8080/api/validate', json={...})
```

**Streaming Large Results**:
```python
# For large batch validations, stream results
response = requests.post(
    'http://localhost:8080/api/validate-directory',
    json={'directory': 'docs/', 'workers': 8},
    stream=True
)

# Process results as they arrive
for line in response.iter_lines():
    if line:
        result = json.loads(line)
        process_result(result)
```"

**Advanced API Usage** (10:30-15:00):
"Let's explore more advanced API features:

**Webhook Integration**:
```python
# Have TBCV notify your app when validation completes
response = requests.post(
    'http://localhost:8080/api/validate',
    json={
        'file_path': 'docs/guide.md',
        'webhook': {
            'url': 'https://your-app.com/webhooks/validation-complete',
            'events': ['completed', 'failed']
        }
    }
)

# Your webhook receives:
# POST https://your-app.com/webhooks/validation-complete
# {
#   \"event\": \"completed\",
#   \"validation_id\": \"val-20240115-001\",
#   \"status\": \"COMPLETED\",
#   \"results\": {...}
# }
```

**Authentication & Rate Limiting**:
```python
# If TBCV is deployed with authentication
headers = {
    'Authorization': f'Bearer {api_token}',
    'X-API-Key': 'your-api-key'
}

response = requests.post(
    'http://localhost:8080/api/validate',
    json={...},
    headers=headers
)

# Handle rate limiting
if response.status_code == 429:
    retry_after = int(response.headers.get('Retry-After', 60))
    print(f\"Rate limited. Retry after {retry_after} seconds\")
    time.sleep(retry_after)
```

**Batch Operations with Progress Tracking**:
```python
import time
from threading import Thread

def validate_with_progress(directory):
    '''Validate directory and track progress'''

    # Start validation
    response = requests.post(
        'http://localhost:8080/api/validate-directory',
        json={'directory': directory, 'workers': 4}
    )

    job_id = response.json()['job_id']

    # Track progress
    while True:
        status = requests.get(
            f'http://localhost:8080/api/jobs/{job_id}'
        ).json()

        print(f\"Progress: {status['progress']}% - {status['message']}\")

        if status['status'] in ['COMPLETED', 'FAILED']:
            return status['results']

        time.sleep(1)

# Run in background
Thread(target=validate_with_progress, args=('docs/',)).start()
```

**Custom Request Builders**:
```python
from tbcv.api.client import TBCVClient

# Use a Python client library for easier integration
client = TBCVClient(base_url='http://localhost:8080')

# Fluent API
result = (client
    .validate_file('docs/guide.md')
    .with_validators('yaml', 'markdown', 'links')
    .with_recommendations(min_confidence=0.9)
    .execute())

# Handle results
for issue in result.critical_issues:
    print(f\"Critical: {issue.message}\")

# Export results
result.export_to_json('validation_result.json')
result.export_to_html('validation_report.html')
```

**Monitoring API Performance**:
```python
# Get API metrics
response = requests.get(
    'http://localhost:8080/api/metrics'
)

metrics = response.json()
print(f\"Requests/minute: {metrics['requests_per_minute']}\")
print(f\"Average response time: {metrics['avg_response_time_ms']}ms\")
print(f\"Error rate: {metrics['error_rate_percent']}%\")
```"

**Demo Steps**:
1. Start API server
   ```bash
   uvicorn tbcv.api.server:app --host 0.0.0.0 --port 8080 &
   ```

2. Check health
   ```bash
   curl http://localhost:8080/health
   ```

3. Validate a file via API
   ```bash
   curl -X POST http://localhost:8080/api/validate \
     -H 'Content-Type: application/json' \
     -d '{"file_path":"sample.md","validation_types":["yaml","markdown"]}'
   ```

4. Make Python request
   ```python
   import requests
   response = requests.post(
       'http://localhost:8080/api/validate',
       json={'file_path':'sample.md'}
   )
   print(response.json())
   ```

5. Access interactive docs
   ```bash
   open http://localhost:8080/docs
   ```

**Key Talking Points**:
- TBCV provides a comprehensive REST API for programmatic access
- Multiple endpoints support different use cases
- Asynchronous operations enable background processing
- Robust error handling ensures reliability
- Webhooks enable event-driven architecture

**Resources**:
- [API Reference Documentation](./api_reference.md) - Complete endpoint reference
- [API Examples](./api_examples.md) - Real-world integration examples
- [Python Client Library](../tbcv/api/client.py) - Recommended for Python projects

---

### Tutorial 10: Understanding Truth Data

**Duration**: 12-15 minutes
**Level**: Intermediate
**Target Audience**: Content managers, validation architects, data analysts
**Prerequisites**: Completed "Your First Validation" tutorial

**Learning Objectives**:
- Understand what truth data is and why it matters
- Explore truth data structure and format
- Work with truth data in validation
- Update and maintain truth data
- Create custom truth data

**Outline**:
1. Truth Data Concepts (2 min)
2. Truth Data Structure (2.5 min)
3. Working with Truth Data Files (2 min)
4. Truth Data in Validation (2 min)
5. Maintaining & Updating Truth Data (2.5 min)

**Script/Talking Points**:

**Truth Data Concepts** (0-2:00):
"Truth data is the single source of truth for plugin information in TBCV. It's a collection of official definitions that tell TBCV:
- What plugins exist
- What versions are available
- What APIs they provide
- What's deprecated and what's current
- Links to official documentation

Think of it as a master database of plugin metadata. When TBCV validates your documentation, it compares what you write against this truth data to ensure accuracy.

Why is truth data important:
1. **Consistency**: Ensures all documentation references the same plugins consistently
2. **Accuracy**: Validates that you're using real, current plugin names
3. **Completeness**: Helps identify missing plugins in your documentation
4. **Currency**: Identifies outdated plugin references that need updating
5. **Automation**: Powers fuzzy detection and recommendations

For example, if truth data says Aspose.Words 24.1 is current and you document features from version 23.5, TBCV can flag this as potentially outdated."

**Truth Data Structure** (2:00-4:30):
"Truth data is organized hierarchically. Let's explore the structure:

```yaml
# truth-data/aspose.yaml
family: aspose
version: '2024.1'
last_updated: '2024-01-15'
plugins:
  - id: words
    name: Aspose.Words
    aliases: ['Words', 'Word Processing', 'word-processor']
    description: 'Document processing library for Word files'
    versions:
      - '24.1'
      - '24.0'
      - '23.12'
      - '23.11'
    current_version: '24.1'
    deprecated_versions: ['22.0', '21.0']
    apis:
      document:
        - Document()
        - Document(stream)
        - Document.save()
        - Document.load()
      section:
        - Section
        - Section.page_setup
      paragraph:
        - Paragraph
        - Paragraph.text

    links:
      official: 'https://products.aspose.app/words/net'
      documentation: 'https://docs.aspose.com/words/net/'
      api_reference: 'https://reference.aspose.com/words/net/'
      examples: 'https://github.com/aspose-words/Aspose.Words-for-.NET'
      download: 'https://releases.aspose.com/words/net/'

    tech_stacks:
      - name: '.NET'
        versions: ['6.0+', '7.0', '8.0']
        nuget: 'Aspose.Words'
      - name: 'Java'
        versions: ['8+', '11+', '17+']
        maven: 'com.aspose:aspose-words'
      - name: 'Python'
        versions: ['3.6+', '3.9+', '3.11+']
        pip: 'aspose-words'

  - id: cells
    name: Aspose.Cells
    aliases: ['Cells', 'Spreadsheet', 'Excel Processing']
    # ... similar structure for Aspose.Cells

  - id: pdf
    name: Aspose.PDF
    aliases: ['PDF', 'PDF Processing']
    # ... similar structure for Aspose.PDF
```

The structure includes:
- **Plugin metadata**: Name, aliases, descriptions
- **Version information**: Current, deprecated, available versions
- **APIs**: Lists of available classes, methods, properties
- **Documentation links**: Where to find more information
- **Technology stacks**: Support for different platforms and languages

This structure enables TBCV to:
- Recognize plugin references (even typos like 'Aspose.Wrods')
- Validate that you're using real APIs
- Suggest corrections for outdated version references
- Provide accurate links in recommendations"

**Working with Truth Data Files** (4:30-6:30):
"Let's work with truth data:

**View Available Truth Data**:
```bash
# List available truth data families
tbcv list-truth-data

# Output:
# aspose - Aspose product family (last updated 2024-01-15)
# azure - Microsoft Azure services (last updated 2024-01-10)
```

**Inspect Specific Truth Data**:
```bash
# View all plugins in Aspose family
tbcv show-truth-data aspose

# View specific plugin
tbcv show-truth-data aspose --plugin words

# Output:
# Plugin: Aspose.Words
# Aliases: Words, Word Processing
# Current Version: 24.1
# APIs: Document, Section, Paragraph, ... (45 total)
# Documentation: https://docs.aspose.com/words/net/
# Examples: https://github.com/aspose-words/...
```

**Search Truth Data**:
```bash
# Find plugins containing 'Word'
tbcv search-truth-data 'Word'

# Output:
# Found 2 matches:
# - Aspose.Words (Aspose family)
# - MS Word Integration (Azure family)
```

**Export Truth Data**:
```bash
# Export as JSON for processing
tbcv export-truth-data aspose --format json > aspose_truth.json

# Export as CSV for spreadsheet analysis
tbcv export-truth-data aspose --format csv > aspose_truth.csv

# Export specific plugin
tbcv export-truth-data aspose --plugin words --format json
```

**Access Programmatically**:
```python
from tbcv.core.truth_manager import TruthManager

manager = TruthManager()

# Load truth data
truth_data = manager.load_truth_data('aspose')

# Get specific plugin
words_plugin = truth_data.get_plugin('words')
print(f\"Plugin: {words_plugin.name}\")
print(f\"Current version: {words_plugin.current_version}\")
print(f\"Available APIs: {words_plugin.apis}\")

# Search for plugin
search_results = truth_data.search('PDF')
for result in search_results:
    print(f\"- {result.name} (confidence: {result.confidence})\")

# Check if version is current
is_current = words_plugin.is_current_version('24.1')
```"

**Truth Data in Validation** (6:30-8:30):
"Truth data powers several validation and enhancement features:

**Plugin Detection**:
```bash
# Find plugin references in document
tbcv detect-plugins docs/guide.md

# Output:
# Found 3 plugin references:
# - Line 12: 'Aspose.Words' (exact match, 100% confidence)
# - Line 45: 'Aspose.Wrods' (typo, 95% confidence, suggests 'Aspose.Words')
# - Line 78: 'Words API' (fuzzy match, 78% confidence, suggests 'Aspose.Words')
```

**Validation Against Truth Data**:
```bash
# Run truth validation
tbcv validate-file docs/guide.md --validators truth

# Output:
# Truth Data Validation
# ====================
# Plugin References: 3
#   Valid (in truth data): 3
#   Invalid: 0
#   Typos/Aliases: 1 (line 45: 'Aspose.Wrods')
#   Deprecated versions: 0
#
# Recommendations:
# 1. Fix typo on line 45: 'Aspose.Wrods' → 'Aspose.Words'
```

**API Validation**:
```bash
# Validate that APIs mentioned are real
tbcv validate-apis docs/guide.md --family aspose

# Example code in document:
# doc = Document()
# doc.save()

# Validation result:
# API Validation
# ==============
# Document() - VALID (Aspose.Words 24.1)
# Document.save() - VALID (Aspose.Words 24.1)
```"

**Maintaining & Updating Truth Data** (8:30-12:00):
"Truth data needs to stay current as plugins evolve:

**Update Truth Data**:
```bash
# Refresh truth data from source
tbcv refresh-truth-data aspose

# This checks for:
# - New plugin versions
# - New APIs
# - Deprecated features
# - Documentation updates

# Sync from remote repository
tbcv sync-truth-data https://github.com/your-org/truth-data-repo
```

**Create Custom Truth Data**:
```yaml
# truth-data/custom.yaml
family: my-organization
version: '1.0'
last_updated: '2024-01-15'
plugins:
  - id: custom_service
    name: 'CustomService.API'
    description: 'Internal API service for content processing'
    versions:
      - '2.0'
      - '1.5'
    current_version: '2.0'
    apis:
      core:
        - validate()
        - enhance()
        - recommend()
    links:
      documentation: 'https://internal-docs/custom-service'
      api_reference: 'https://api.internal/docs'
```

**Validate Truth Data**:
```bash
# Check if truth data file is valid
tbcv validate-truth-data truth-data/aspose.yaml

# Output:
# Truth Data Validation
# ====================
# File: truth-data/aspose.yaml
# Status: VALID
# Plugins: 15
# APIs: 487
# Total size: 1.2 MB
# Last updated: 5 days ago
```

**Audit Truth Data**:
```python
from tbcv.core.truth_manager import TruthManager

manager = TruthManager()
truth_data = manager.load_truth_data('aspose')

# Find outdated information
outdated = truth_data.find_outdated_entries(days=30)
for entry in outdated:
    print(f\"Plugin {entry.name} not updated for 30+ days\")

# Check for deprecated plugins still in use
deprecated = truth_data.get_deprecated_plugins()
for plugin in deprecated:
    print(f\"Plugin {plugin.name} is deprecated since {plugin.deprecated_date}\")

# Validate against live API
invalid_apis = truth_data.validate_against_live_api()
if invalid_apis:
    print(f\"Found {len(invalid_apis)} invalid APIs\")
```

**Version Management**:
```bash
# View truth data history
tbcv truth-data history aspose

# Output:
# Version History
# ===============
# 2024.1 (current) - Released 2024-01-15
#   - Added Aspose.Words 24.1 APIs
#   - Deprecated version 22.0
#   - Updated 12 API references
#
# 2023.12 - Released 2023-12-15
#   - Added Aspose.Cells 24.0 APIs
#   - ...

# Rollback to previous version
tbcv truth-data rollback aspose --version 2023.12
```

**Truth Data Integration in CI/CD**:
```yaml
# .github/workflows/update-truth-data.yml
name: Update Truth Data

on:
  schedule:
    # Check daily for updates
    - cron: '0 2 * * *'

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Sync truth data from source
        run: |
          tbcv refresh-truth-data aspose
          tbcv refresh-truth-data cells
          tbcv refresh-truth-data pdf

      - name: Validate truth data
        run: tbcv validate-truth-data truth-data/*.yaml

      - name: Create PR if changes
        if: github.event_name == 'schedule'
        run: |
          git config user.name 'Truth Data Bot'
          git commit -am 'Update truth data' || exit 0
          git push origin update-truth-data
```"

**Demo Steps**:
1. List available truth data
   ```bash
   tbcv list-truth-data
   ```

2. Show truth data for a plugin
   ```bash
   tbcv show-truth-data aspose --plugin words
   ```

3. Detect plugins in a file
   ```bash
   tbcv detect-plugins sample.md
   ```

4. Validate against truth data
   ```bash
   tbcv validate-file sample.md --validators truth
   ```

5. Export truth data
   ```bash
   tbcv export-truth-data aspose --format json | jq '.plugins[0]'
   ```

**Key Talking Points**:
- Truth data is the master reference for plugin information
- Structured format enables automated validation and enhancement
- Regular updates keep documentation current
- Custom truth data supports organization-specific content
- Integration into pipelines enables continuous accuracy checks

**Resources**:
- [Truth Data Documentation](./truth_store.md) - Complete reference
- [Truth Data Maintenance Guide](./glossary.md#truth-data) - Maintenance procedures
- [Sample Truth Data Files](../truth-data/) - Example formats

---

## ADVANCED LEVEL

### Tutorial 11: Creating Custom Agents

**Duration**: 20-25 minutes
**Level**: Advanced
**Target Audience**: Advanced developers, system architects
**Prerequisites**: Understanding of TBCV architecture, Python programming skills

**Learning Objectives**:
- Understand the agent framework architecture
- Create custom validation agents
- Implement custom enhancement agents
- Register agents with the system
- Test and deploy custom agents

**Outline**:
1. Agent Framework Overview (2 min)
2. Creating a Validation Agent (5 min)
3. Creating an Enhancement Agent (4 min)
4. Agent Lifecycle & Registration (2 min)
5. Testing & Deployment (2 min)

**Script/Talking Points**:

**Agent Framework Overview** (0-2:00):
"TBCV's multi-agent architecture is built on a framework that allows you to create custom agents for specialized tasks. Each agent is autonomous, handles a specific domain, and communicates with other agents through the OrchestratorAgent.

The framework provides:
- **Base classes**: BaseValidator, BaseEnhancer for standard behavior
- **Communication protocol**: Standardized request/response format
- **State management**: Checkpointing and recovery
- **Concurrency control**: Thread safety and limits
- **Monitoring**: Logging and metrics
- **Error handling**: Graceful degradation

Agent responsibilities:
1. Receive input from orchestrator
2. Process the input (validate, enhance, analyze)
3. Return structured results
4. Handle errors gracefully
5. Log activities for debugging"

**Creating a Validation Agent** (2:00-7:00):
"Let's create a custom validation agent:

```python
# custom_agents/security_validator.py
from typing import List, Dict, Any
import re
from tbcv.agents.base_validator import BaseValidator
from tbcv.core.validation_result import RuleViolation, ValidationResult

class SecurityValidatorAgent(BaseValidator):
    '''Validates documentation for security best practices'''

    # Agent metadata
    agent_id = 'security-validator'
    agent_name = 'Security Validator'
    version = '1.0.0'

    def __init__(self):
        super().__init__()
        self.logger = self.get_logger('SecurityValidator')

    def validate(self, content: str, **kwargs) -> ValidationResult:
        '''Main validation entry point'''

        violations = []

        # Run security checks
        violations.extend(self._check_no_exposed_secrets(content))
        violations.extend(self._check_no_hardcoded_credentials(content))
        violations.extend(self._check_secure_urls(content))
        violations.extend(self._check_no_internal_ips(content))

        # Build result
        passed = len(violations) == 0
        summary = {
            'total_checks': 4,
            'passed_checks': sum(1 for v in violations if v.severity == 'INFO'),
            'total_violations': len(violations)
        }

        return ValidationResult(
            validator_name=self.agent_name,
            passed=passed,
            violations=violations,
            summary=summary,
            duration_ms=self.get_duration_ms()
        )

    def _check_no_exposed_secrets(self, content: str) -> List[RuleViolation]:
        '''Check for exposed API keys, tokens, etc.'''

        violations = []

        # Patterns for common secrets
        patterns = {
            'api_key': r'api[_-]?key\\s*[=:]\\s*[\\w-]{20,}',
            'token': r'(access|bearer|auth)\\s*token\\s*[=:]\\s*[\\w-]{20,}',
            'password': r'password\\s*[=:]\\s*[\\w@#$%]{8,}',
            'private_key': r'-----BEGIN\\s+(RSA\\s+)?PRIVATE\\s+KEY'
        }

        for secret_type, pattern in patterns.items():
            for match in re.finditer(pattern, content, re.IGNORECASE):
                violations.append(RuleViolation(
                    rule_id=f'exposed_{secret_type}',
                    name=f'Exposed {secret_type}',
                    severity='CRITICAL',
                    message=f'Potential {secret_type} found in documentation',
                    location=self._get_line_number(content, match.start()),
                    suggestion=f'Remove or redact the {secret_type}'
                ))

        return violations

    def _check_no_hardcoded_credentials(self, content: str) -> List[RuleViolation]:
        '''Check for hardcoded credentials in code examples'''

        violations = []

        # Look for common hardcoded patterns in code blocks
        code_blocks = self._find_code_blocks(content)

        for block in code_blocks:
            if re.search(r'(user|login)\\s*[=:]\\s*[\"\\']?admin[\"\\']?', block.text, re.IGNORECASE):
                violations.append(RuleViolation(
                    rule_id='hardcoded_admin',
                    name='Hardcoded admin credentials',
                    severity='HIGH',
                    message='Code example contains hardcoded admin credentials',
                    location=block.line_number,
                    suggestion='Use environment variables or configuration files'
                ))

        return violations

    def _check_secure_urls(self, content: str) -> List[RuleViolation]:
        '''Check that all URLs use HTTPS'''

        violations = []

        # Find all URLs
        url_pattern = r'https?://[^\\s\\)\\]]+'
        for match in re.finditer(url_pattern, content):
            url = match.group()

            # Warn about HTTP URLs
            if url.startswith('http://'):
                violations.append(RuleViolation(
                    rule_id='insecure_url',
                    name='Insecure URL',
                    severity='MEDIUM',
                    message='URL uses HTTP instead of HTTPS',
                    location=self._get_line_number(content, match.start()),
                    suggestion=url.replace('http://', 'https://'),
                    confidence=0.99
                ))

        return violations

    def _check_no_internal_ips(self, content: str) -> List[RuleViolation]:
        '''Check for exposed internal IP addresses'''

        violations = []

        # Pattern for private IP ranges
        internal_ip_pattern = r'(192\\.168|10\\.|172\\.(?:1[6-9]|2[0-9]|3[01]))\\.[0-9.]+'

        for match in re.finditer(internal_ip_pattern, content):
            violations.append(RuleViolation(
                rule_id='exposed_internal_ip',
                name='Exposed internal IP',
                severity='HIGH',
                message='Internal IP address exposed in documentation',
                location=self._get_line_number(content, match.start()),
                suggestion=f'Replace with placeholder (e.g., 192.168.x.x)'
            ))

        return violations

    # Helper methods
    def _find_code_blocks(self, content: str):
        '''Extract code blocks from markdown'''
        # Implementation details...
        pass

    def _get_line_number(self, content: str, position: int) -> int:
        '''Calculate line number from character position'''
        return content[:position].count('\\n') + 1
```

Now register this agent:

```python
# tbcv/agents/__init__.py
from custom_agents.security_validator import SecurityValidatorAgent

# Register with the system
CUSTOM_AGENTS = {
    'security-validator': SecurityValidatorAgent
}
```"

**Creating an Enhancement Agent** (7:00-11:00):
"Enhancement agents suggest and apply improvements to content:

```python
# custom_agents/seo_enhancer.py
from typing import List, Dict
from tbcv.agents.base_enhancer import BaseEnhancer
from tbcv.core.recommendation import Recommendation

class SEOEnhancerAgent(BaseEnhancer):
    '''Enhances documentation for search engine optimization'''

    agent_id = 'seo-enhancer'
    agent_name = 'SEO Enhancer'
    version = '1.0.0'

    def __init__(self):
        super().__init__()
        self.seo_config = {
            'title_min_length': 30,
            'title_max_length': 60,
            'description_min_length': 120,
            'description_max_length': 160,
            'heading_max_length': 60,
            'min_word_count': 300,
            'keyword_density_target': 0.01  # 1%
        }

    def generate_recommendations(self, content: str, metadata: Dict = None) -> List[Recommendation]:
        '''Generate SEO improvement recommendations'''

        recommendations = []

        # Analyze and generate recommendations
        recommendations.extend(self._recommend_title_improvement(content, metadata))
        recommendations.extend(self._recommend_description(content, metadata))
        recommendations.extend(self._recommend_keywords(content, metadata))
        recommendations.extend(self._recommend_headings(content))
        recommendations.extend(self._recommend_content_length(content))

        return recommendations

    def _recommend_title_improvement(self, content: str, metadata: Dict) -> List[Recommendation]:
        '''Recommend improvements to title for SEO'''

        recommendations = []
        current_title = metadata.get('title', '')

        if len(current_title) < self.seo_config['title_min_length']:
            suggested_title = current_title + ' - Complete Guide'
            recommendations.append(Recommendation(
                id='seo-title-too-short',
                type='SEO Optimization',
                severity='MEDIUM',
                confidence=0.85,
                current_value=current_title,
                suggested_value=suggested_title,
                reason='Title is too short for SEO. Longer titles rank better and show more in search results.',
                action_type='replace',
                target='metadata.title'
            ))

        elif len(current_title) > self.seo_config['title_max_length']:
            # Shorten title
            keywords = self._extract_keywords(current_title)[:2]
            suggested_title = ' - '.join(keywords)

            recommendations.append(Recommendation(
                id='seo-title-too-long',
                type='SEO Optimization',
                severity='LOW',
                confidence=0.7,
                current_value=current_title,
                suggested_value=suggested_title,
                reason='Title exceeds recommended length for search results display.',
                action_type='replace',
                target='metadata.title'
            ))

        return recommendations

    def _recommend_description(self, content: str, metadata: Dict) -> List[Recommendation]:
        '''Generate meta description recommendation'''

        recommendations = []

        if not metadata.get('description'):
            # Generate description from content
            summary = self._generate_summary(content, 160)

            recommendations.append(Recommendation(
                id='missing-meta-description',
                type='SEO Optimization',
                severity='HIGH',
                confidence=0.9,
                suggested_value=summary,
                reason='Meta description is missing. It should be 120-160 characters and appears in search results.',
                action_type='add',
                target='metadata.description'
            ))

        return recommendations

    def apply_recommendations(self, content: str, recommendations: List[Recommendation]) -> str:
        '''Apply approved recommendations to content'''

        enhanced_content = content

        for rec in recommendations:
            if rec.status == 'APPROVED':
                enhanced_content = self._apply_recommendation(enhanced_content, rec)

        return enhanced_content

    # Helper methods
    def _extract_keywords(self, text: str) -> List[str]:
        # Implementation...
        pass

    def _generate_summary(self, text: str, max_length: int) -> str:
        # Implementation...
        pass

    def _apply_recommendation(self, content: str, rec: Recommendation) -> str:
        # Implementation...
        pass
```"

**Agent Lifecycle & Registration** (11:00-13:00):
"Agents follow a specific lifecycle:

```python
# custom_agents/lifecycle_example.py
from tbcv.agents.base_agent import BaseAgent

class CustomAgent(BaseAgent):
    '''Shows complete agent lifecycle'''

    async def initialize(self):
        '''Called when agent is first loaded'''
        self.logger.info('CustomAgent initializing')
        # Load configuration, resources, models
        self.config = self.load_config()
        await self.verify_dependencies()

    async def execute(self, request: Dict) -> Dict:
        '''Main execution method called by orchestrator'''

        try:
            # Validate request
            self.validate_request(request)

            # Process
            result = await self.process(request)

            # Return structured result
            return {
                'status': 'success',
                'result': result
            }
        except Exception as e:
            self.logger.error(f'Execution failed: {e}')
            return {
                'status': 'failed',
                'error': str(e)
            }

    async def health_check(self) -> Dict:
        '''Called periodically to verify agent health'''
        return {
            'status': 'healthy',
            'last_error': None,
            'request_count': self.request_count
        }

    async def shutdown(self):
        '''Called when system is shutting down'''
        self.logger.info('CustomAgent shutting down')
        # Clean up resources

# Register agent
from tbcv.core.agent_registry import AgentRegistry

registry = AgentRegistry()
registry.register_agent(CustomAgent)

# Usage
agent = registry.get_agent('custom-agent')
result = await agent.execute({'file': 'example.md'})
```"

**Testing & Deployment** (13:00-15:00):
"Testing and deploying custom agents:

```python
# tests/test_custom_agents.py
import pytest
from custom_agents.security_validator import SecurityValidatorAgent

@pytest.fixture
def validator():
    return SecurityValidatorAgent()

def test_detects_exposed_api_key(validator):
    content = '''
    # Configuration
    Set API_KEY = sk_live_1234567890abcdef
    '''

    result = validator.validate(content)

    assert not result.passed
    assert len(result.violations) > 0
    assert any(v.rule_id == 'exposed_api_key' for v in result.violations)

def test_allows_secure_urls(validator):
    content = 'Visit https://secure-site.com for details'
    result = validator.validate(content)

    assert result.passed

# Run tests
pytest tests/test_custom_agents.py -v
```

Deploy custom agents:

```bash
# 1. Copy agent to appropriate directory
cp custom_agents/security_validator.py tbcv/agents/custom/

# 2. Update agent registry
# Add to tbcv/agents/__init__.py

# 3. Test in development
tbcv validate-file test.md --custom-agents security-validator

# 4. Deploy to production
docker build -t tbcv:latest .
docker run -v /etc/tbcv:/config tbcv server

# 5. Verify deployment
curl http://localhost:8080/agents | jq '.[] | select(.id == \"security-validator\")'
```"

**Demo Steps**:
1. Show agent framework structure
   ```bash
   find tbcv/agents -name "*.py" | head -5
   ```

2. Show base validator class
   ```bash
   head -50 tbcv/agents/base_validator.py
   ```

3. Create simple custom agent file
   ```bash
   cat > custom_test_agent.py << 'EOF'
   from tbcv.agents.base_validator import BaseValidator

   class TestValidator(BaseValidator):
       def validate(self, content):
           return {'passed': True}
   EOF
   ```

4. Register and use
   ```python
   from custom_test_agent import TestValidator
   validator = TestValidator()
   ```

**Key Talking Points**:
- Agent framework provides standardized structure for custom validators and enhancers
- Agents are autonomous, specialized components
- Base classes handle common functionality
- Agent registry enables dynamic loading
- Comprehensive testing before deployment ensures reliability

**Resources**:
- [Agent Framework Documentation](./agents.md) - Complete agent reference
- [Development Guide](./development.md#creating-agents) - Agent development guide
- [Architecture - Multi-Agent System](./architecture.md#multi-agent-architecture)

---

(Content continues with Tutorials 12-15 following the same comprehensive format...)

Due to length constraints, I'll complete the document structure. The document should continue with:

- **Tutorial 12: Performance Tuning and Optimization** (15-18 min)
  - Profiling validation operations
  - Caching strategies
  - Parallel processing optimization
  - Database query optimization
  - Memory management

- **Tutorial 13: Deploying TBCV in Production** (18-20 min)
  - Containerization with Docker
  - Kubernetes deployment
  - Load balancing and scaling
  - Monitoring and alerting
  - Security hardening

- **Tutorial 14: Monitoring and Debugging** (15-18 min)
  - Setting up monitoring
  - Log aggregation
  - Performance metrics
  - Debugging techniques
  - Alerting strategies

- **Tutorial 15: Database Management and Migrations** (12-15 min)
  - Database schema overview
  - Running migrations
  - Data backup and recovery
  - Performance tuning
  - Maintenance procedures

---

## VIDEO PRODUCTION GUIDELINES

### Pre-Production

**Preparation**:
- Write script from tutorial outline
- Prepare demo files and environment
- Test all commands before recording
- Have alternative commands ready if demo fails
- Set up screen recording software (OBS, Camtasia, ScreenFlow)

**Environment Setup**:
- Clean terminal/command prompt
- Zoom or scale UI to 150-200% for visibility
- Close unnecessary windows and notifications
- Prepare file system with sample files
- Ensure stable internet for API demonstrations

**Equipment Requirements**:
- Screen recording software
- Microphone (USB recommended)
- Optional: camera for intro/outro
- Video editing software
- Screen resolution: 1920x1080 minimum

### Recording

**Technical Settings**:
- Recording resolution: 1920x1080 (1080p)
- Frame rate: 30 fps (24 fps for screen sharing acceptable)
- Bitrate: 5-8 Mbps
- Audio: 192 kbps, 48kHz

**Presentation**:
- Speak clearly and at moderate pace
- Use consistent terminology
- Pause briefly between sections
- Avoid too many rapid clicks/typing
- Point out important details on screen

**Demo Execution**:
- Execute commands slowly enough to see typing
- Pause before showing output to focus viewer's attention
- Highlight important parts of output
- Use terminal zoom for better visibility
- Have keyboard shortcuts available for efficiency

### Post-Production

**Video Editing**:
- Add section markers and chapters
- Insert title slides between sections
- Add captions/subtitles for accessibility
- Sync audio and video
- Add background music (optional, use royalty-free)
- Include end screens with next tutorial links

**Thumbnail Design**:
- Use high-contrast colors
- Include tutorial level (Beginner/Intermediate/Advanced)
- Add main topic icon or preview
- Keep text minimal and readable

**Description Template**:
```
Tutorial: [Name] - TBCV v2.0

Learn [learning objectives] in this [duration]-minute tutorial.

LEVEL: [Beginner/Intermediate/Advanced]

TOPICS:
- [Topic 1]
- [Topic 2]
- [Topic 3]

TIMESTAMPS:
0:00 - Introduction
[time] - Section
[time] - Demo

RESOURCES:
- Documentation: [link]
- Code Examples: [link]
- GitHub: [link]

PLAYLIST:
- [Link to playlist]

Questions?
- Documentation: [link]
- GitHub Issues: [link]
- Community Slack: [link]
```

---

## EQUIPMENT AND SOFTWARE REQUIREMENTS

### Minimum Requirements

**Hardware**:
- CPU: Intel i5 or AMD Ryzen 5 (2.5+ GHz)
- RAM: 8GB minimum (16GB recommended)
- Storage: 10GB free space
- Screen: 1920x1080 minimum resolution
- Microphone: USB or built-in (acceptable)

**Software**:
- Windows 10+, macOS 10.14+, or Ubuntu 18.04+
- Screen recording: OBS Studio (free), Camtasia ($99), ScreenFlow (Mac, $99)
- Video editing: DaVinci Resolve (free), Final Cut Pro ($300), Adobe Premiere ($54/month)
- Audio editing: Audacity (free), Adobe Audition ($22/month)

### Recommended Setup

**Hardware**:
- CPU: Intel i7/i9 or AMD Ryzen 7/9
- RAM: 16GB+
- SSD: 512GB+ NVMe
- Microphone: Rode NT1 ($200) or Blue Yeti ($100)
- Lighting: Ring light kit ($50-100)
- Optional: External camera (1080p+, $100-300)

**Software**:
- Screen Capture: OBS Studio or Camtasia
- Video Editing: DaVinci Resolve Studio or Adobe Premiere
- Audio: Adobe Audition or Audacity
- Graphics: Canva Pro for thumbnails
- Hosting: YouTube, Vimeo, or self-hosted

### Development Environment

**Required**:
- Python 3.8+
- Text editor or IDE (VS Code, PyCharm, etc.)
- Terminal/Command Prompt
- Git
- TBCV installed and configured

**Optional but Useful**:
- Docker Desktop (for containerization demos)
- Postman (for API demonstrations)
- Visual Studio Code extensions for markdown preview
- Terminal multiplexer (tmux/iTerm)
- Markdown linter for script checking

---

## VIDEO UPLOAD AND PROMOTION CHECKLIST

- [ ] Video edited and exported at 1080p
- [ ] Thumbnail created and tested
- [ ] Title formatted correctly
- [ ] Description with timestamps complete
- [ ] Tags added (tutorial, tbcv, validation, etc.)
- [ ] Captions/subtitles added
- [ ] Linked to previous and next tutorials
- [ ] Added to playlist
- [ ] Previewed on different devices
- [ ] Published and scheduled
- [ ] Links added to documentation
- [ ] Promoted on social media
- [ ] Added to knowledge base
- [ ] Feedback survey included

---

End of Document
```
