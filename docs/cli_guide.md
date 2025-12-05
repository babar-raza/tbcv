# TBCV Command Line Interface Guide

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Core Commands](#core-commands)
4. [Command Groups](#command-groups)
5. [Common Workflows](#common-workflows)
6. [Advanced Usage](#advanced-usage)
7. [Troubleshooting](#troubleshooting)

## Overview

TBCV (Truth-Based Content Validation System) is a comprehensive CLI tool for validating, enhancing, and managing content quality using truth-based validation principles and AI-powered recommendations.

### Key Features

- **Single-file validation**: Validate individual files with detailed reporting
- **Batch processing**: Process entire directories with parallel workers
- **Smart recommendations**: AI-generated content improvement suggestions
- **Workflow management**: Track and manage validation and enhancement workflows
- **Rich formatting**: Beautiful terminal output with tables and progress indicators
- **JSON/YAML export**: Machine-readable output for integration and scripting

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd tbcv

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```bash
# Show all available commands
tbcv --help

# Validate a single file
tbcv validate-file myfile.md

# Run full validation with recommendations
tbcv validate myfile.md

# Check system status
tbcv check-agents

# Run a test to verify installation
tbcv test
```

### Global Options

All commands support these global options:

```bash
tbcv [OPTIONS] COMMAND [ARGS]

  -v, --verbose      Enable verbose logging for debugging
  -c, --config TEXT  Path to custom configuration file
  -q, --quiet        Minimal console output
  --mcp-debug        Enable MCP client debug logging
  --help             Show help message
```

Examples:

```bash
# Verbose output for debugging
tbcv -v validate-file content.md

# Use custom configuration
tbcv -c production.yaml validate-file content.md

# Quiet mode (minimal output)
tbcv -q batch ./docs

# Enable MCP debugging
tbcv --mcp-debug check-agents
```

## Core Commands

### validate-file

Validate a single file for content quality issues.

```bash
tbcv validate-file FILE_PATH [OPTIONS]
```

**Arguments:**
- `FILE_PATH`: Path to the file to validate (must exist)

**Options:**
- `-f, --family`: Plugin family to use (default: words)
- `-t, --types`: Comma-separated validation types (yaml, markdown, Truth, etc.)
- `-o, --output`: Save results to file
- `--format`: Output format - json (default) or text

**Examples:**

```bash
# Basic validation
tbcv validate-file myfile.md

# Validate with specific types and save results
tbcv validate-file content.md --types markdown,Truth -o results.json

# Get text output
tbcv validate-file myfile.md --format text

# Validate YAML file with custom plugin family
tbcv validate-file config.yaml -f yaml -o report.json
```

**Output:**
Validation ID, status (pass/fail/warning), detected issues with severity levels, and confidence scores.

### validate-directory

Batch validate all files in a directory.

```bash
tbcv validate-directory DIRECTORY_PATH [OPTIONS]
```

**Arguments:**
- `DIRECTORY_PATH`: Path to directory containing files to validate

**Options:**
- `-p, --pattern`: Glob pattern for matching (default: *.md)
- `-f, --family`: Plugin family to use (default: words)
- `-t, --types`: Comma-separated validation types
- `-w, --workers`: Number of concurrent workers (default: 4)
- `-o, --output`: Save results to file
- `--format`: Output format - json (default), text, or summary
- `-r, --recursive`: Include subdirectories

**Examples:**

```bash
# Validate all Markdown files in a directory
tbcv validate-directory ./docs

# Recursive validation with custom pattern
tbcv validate-directory ./content -p "*.md" -r -w 8

# Get summary statistics only
tbcv validate-directory ./docs --format summary

# Validate YAML and JSON files with 2 workers
tbcv validate-directory ./config -p "*.{yaml,json}" -w 2 -o results.json
```

**Performance Tips:**
- Increase `--workers` for faster processing on multi-core systems
- Use `--pattern` to validate only specific file types
- Higher worker count = more CPU/memory usage

### validate

Run full validation workflow on a file.

```bash
tbcv validate FILE_PATH [OPTIONS]
```

Performs comprehensive validation using the orchestrator workflow, including fuzzy detection, content validation, and LLM-based analysis.

**Arguments:**
- `FILE_PATH`: Path to the file to validate

**Options:**
- `--type`: Validation type - basic, full (default), or enhanced
- `--confidence`: Confidence threshold 0.0-1.0 (default: 0.6)
- `--output`: Output format - table (default), json, or yaml
- `--fix`: Apply automatic fixes to detected issues
- `--no-cache`: Skip cache lookup for fresh validation

**Examples:**

```bash
# Run full validation with table output
tbcv validate myfile.md

# Run basic validation only
tbcv validate myfile.md --type basic

# Enhanced validation with JSON output
tbcv validate myfile.md --type enhanced --output json

# Validate with high confidence threshold
tbcv validate myfile.md --confidence 0.8

# Apply automatic fixes
tbcv validate myfile.md --fix

# Skip cache for fresh analysis
tbcv validate myfile.md --no-cache
```

**Validation Types:**
- `basic`: Quick syntax and structure checks only
- `full`: Comprehensive validation with all agents and analysis
- `enhanced`: Full validation plus content enhancement recommendations

### batch

Batch validate files in a directory.

```bash
tbcv batch DIRECTORY_PATH [OPTIONS]
```

Creates and executes a batch validation workflow for multiple files with comprehensive reporting.

**Arguments:**
- `DIRECTORY_PATH`: Path to the directory containing files to process

**Options:**
- `--pattern`: File glob pattern (default: *.md)
- `-r, --recursive`: Recursively process subdirectories
- `--report-file`: Save detailed JSON report to file
- `--summary-only`: Show only aggregate statistics

**Examples:**

```bash
# Process all Markdown files
tbcv batch ./docs

# Recursive processing with report
tbcv batch ./content -r --report-file report.json

# Show summary statistics only
tbcv batch ./docs --summary-only

# Process specific file pattern
tbcv batch ./src -p "*.py" -r --report-file python_report.json
```

### enhance

Apply enhancements to validated content.

```bash
tbcv enhance VALIDATION_IDS... [OPTIONS]
```

Applies approved recommendations to enhance content quality. Can preview changes before applying.

**Arguments:**
- `VALIDATION_IDS`: One or more validation IDs to enhance

**Options:**
- `--preview`: Preview changes without actually applying them
- `--threshold`: Confidence threshold for recommendations (default: 0.7)

**Examples:**

```bash
# Preview enhancement for a validation
tbcv enhance abc123def456 --preview

# Apply enhancement with custom threshold
tbcv enhance abc123def456 --threshold 0.8

# Enhance multiple validations
tbcv enhance abc123def456 xyz789uvw012

# Preview before applying (recommended workflow)
tbcv enhance abc123def456 --preview
# ... review output ...
tbcv enhance abc123def456
```

**Recommended Workflow:**
1. Run validation: `tbcv validate myfile.md`
2. Preview enhancement: `tbcv enhance <ID> --preview`
3. Review the diff output
4. Apply enhancement: `tbcv enhance <ID>`

### check-agents

Check system health and agent status.

```bash
tbcv check-agents [OPTIONS]
```

Displays operational status of all system components and agents, including resource usage and metrics.

**Options:**
- `--format`: Output format - text (default) or json

**Examples:**

```bash
# Get human-readable system status
tbcv check-agents

# Get JSON output for scripting
tbcv check-agents --format json

# Check with verbose output
tbcv -v check-agents
```

### status

Display detailed system and agent status.

```bash
tbcv status
```

Shows operational status of all agents, request processing counts, and performance metrics.

**Examples:**

```bash
# Show agent status
tbcv status

# Show status with verbose output
tbcv -v status
```

### test

Run a test validation workflow.

```bash
tbcv test
```

Creates sample content with various issues and runs full validation to demonstrate functionality and verify installation.

**Examples:**

```bash
# Run test
tbcv test

# Run test with verbose logging
tbcv -v test

# Run test with quiet mode
tbcv -q test
```

**Use Cases:**
- Testing system installation
- Learning the validation workflow
- Verifying configuration
- Testing after upgrades

## Command Groups

### validations

Manage validation results and content validation history.

```bash
tbcv validations [SUBCOMMAND] [OPTIONS]
```

**Subcommands:**

#### validations list

List validation results with optional filtering.

```bash
tbcv validations list [OPTIONS]
```

**Options:**
- `--status`: Filter by status (pass, fail, warning, approved, rejected, enhanced)
- `--severity`: Filter by severity level
- `--limit`: Maximum results to show (default: 50)
- `--format`: Output format (table, json)

**Examples:**

```bash
# List recent validations
tbcv validations list

# List failed validations
tbcv validations list --status fail

# Get JSON output
tbcv validations list --format json --limit 100
```

#### validations show

Show detailed validation information.

```bash
tbcv validations show VALIDATION_ID [OPTIONS]
```

**Options:**
- `--format`: Output format (text, json)

#### validations history

Show validation history for a file.

```bash
tbcv validations history FILE_PATH [OPTIONS]
```

**Options:**
- `--limit`: Maximum history entries (default: 50)
- `--format`: Output format (table, json)

#### validations approve

Approve a validation result.

```bash
tbcv validations approve VALIDATION_ID [OPTIONS]
```

**Options:**
- `--notes`: Optional approval notes

#### validations reject

Reject a validation result.

```bash
tbcv validations reject VALIDATION_ID [OPTIONS]
```

**Options:**
- `--notes`: Optional rejection notes

#### validations revalidate

Re-validate content from a previous validation.

```bash
tbcv validations revalidate VALIDATION_ID
```

#### validations diff

Show content diff for an enhanced validation.

```bash
tbcv validations diff VALIDATION_ID
```

#### validations compare

Show comprehensive enhancement comparison.

```bash
tbcv validations compare VALIDATION_ID [OPTIONS]
```

**Options:**
- `--format`: Output format (text, json)

### recommendations

Manage recommendations for content improvements.

```bash
tbcv recommendations [SUBCOMMAND] [OPTIONS]
```

**Subcommands:**

#### recommendations list

List recommendations with optional filtering.

```bash
tbcv recommendations list [OPTIONS]
```

**Options:**
- `--status`: Filter by status (proposed, pending, approved, rejected, applied)
- `--validation-id`: Filter by validation ID
- `--limit`: Maximum results (default: 50)
- `--format`: Output format (table, json)

**Examples:**

```bash
# List all pending recommendations
tbcv recommendations list --status pending

# List recommendations for a specific validation
tbcv recommendations list --validation-id VAL_ID

# Get JSON output
tbcv recommendations list --format json
```

#### recommendations show

Show detailed recommendation information.

```bash
tbcv recommendations show RECOMMENDATION_ID [OPTIONS]
```

**Options:**
- `--format`: Output format (text, json)

#### recommendations approve

Approve one or more recommendations.

```bash
tbcv recommendations approve RECOMMENDATION_IDS... [OPTIONS]
```

**Options:**
- `--reviewer`: Reviewer name/ID
- `--notes`: Optional approval notes

#### recommendations reject

Reject one or more recommendations.

```bash
tbcv recommendations reject RECOMMENDATION_IDS... [OPTIONS]
```

**Options:**
- `--reviewer`: Reviewer name/ID
- `--notes`: Optional rejection notes

#### recommendations generate

Generate recommendations for a validation.

```bash
tbcv recommendations generate VALIDATION_ID [OPTIONS]
```

**Options:**
- `--force`: Force regeneration even if already exists

#### recommendations auto-apply

Auto-apply high-confidence recommendations.

```bash
tbcv recommendations auto-apply VALIDATION_ID [OPTIONS]
```

**Options:**
- `--threshold`: Confidence threshold (default: 0.7)
- `--dry-run`: Show what would be applied without applying

#### recommendations rebuild

Rebuild recommendations for a validation.

```bash
tbcv recommendations rebuild VALIDATION_ID
```

Deletes and regenerates recommendations.

#### recommendations delete

Delete one or more recommendations.

```bash
tbcv recommendations delete RECOMMENDATION_IDS... [OPTIONS]
```

**Options:**
- `--confirm`: Skip confirmation prompt

#### recommendations enhance

Enhance content by applying approved recommendations.

```bash
tbcv recommendations enhance FILE_PATH VALIDATION_ID [OPTIONS]
```

**Options:**
- `--preview`: Preview changes without applying
- `--backup`: Create backup before applying
- `--output`: Output file for enhanced content

### workflows

Manage workflow execution and monitoring.

```bash
tbcv workflows [SUBCOMMAND] [OPTIONS]
```

**Subcommands:**

#### workflows list

List workflows with optional state filtering.

```bash
tbcv workflows list [OPTIONS]
```

**Options:**
- `--state`: Filter by state (pending, running, paused, completed, failed, cancelled)
- `--limit`: Maximum results (default: 50)
- `--format`: Output format (table, json)

**Examples:**

```bash
# List all workflows
tbcv workflows list

# List only completed workflows
tbcv workflows list --state completed

# List failed workflows for diagnosis
tbcv workflows list --state failed --format json
```

**Workflow States:**
- `pending`: Awaiting execution
- `running`: Currently executing
- `paused`: Temporarily halted
- `completed`: Successfully finished
- `failed`: Failed during execution
- `cancelled`: Manually cancelled

#### workflows show

Show detailed workflow information and logs.

```bash
tbcv workflows show WORKFLOW_ID [OPTIONS]
```

**Options:**
- `--format`: Output format (text, json)

### migrate

Database migration commands using Alembic.

```bash
tbcv migrate [SUBCOMMAND] [OPTIONS]
```

**Subcommands:**

#### migrate current

Show the current migration revision.

```bash
tbcv migrate current [-v]
```

**Options:**
- `-v, --verbose`: Show detailed information

#### migrate history

Show migration history.

```bash
tbcv migrate history [-v] [-r RANGE]
```

**Options:**
- `-v, --verbose`: Show detailed information
- `-r, --range`: Range to show (e.g., base:head)

#### migrate upgrade

Upgrade database to target revision.

```bash
tbcv migrate upgrade [-r REVISION] [--sql]
```

**Options:**
- `-r, --revision`: Target revision (default: head for latest)
- `--sql`: Preview SQL without executing

#### migrate downgrade

Downgrade database to target revision.

```bash
tbcv migrate downgrade -r REVISION [--sql] [--yes]
```

**Options:**
- `-r, --revision`: Target revision (REQUIRED)
- `--sql`: Preview SQL without executing
- `-y, --yes`: Skip confirmation prompt

#### migrate create

Create a new migration.

```bash
tbcv migrate create MESSAGE [--autogenerate | --no-autogenerate] [--sql]
```

**Options:**
- `--autogenerate`: Auto-detect changes (default: True)
- `--no-autogenerate`: Create empty migration for manual editing
- `--sql`: Show generated SQL without creating file

#### migrate stamp

Stamp the database with a specific revision.

```bash
tbcv migrate stamp REVISION [--sql]
```

**Options:**
- `--sql`: Show operations without executing

### rag

Manage RAG (Retrieval-Augmented Generation) for semantic truth search.

```bash
tbcv rag [SUBCOMMAND] [OPTIONS]
```

**Subcommands:**

#### rag index

Build vector indices for truth families.

```bash
tbcv rag index [-f FAMILY] [--all-families] [--clear]
```

**Options:**
- `-f, --family`: Index specific family (default: words)
- `--all-families`: Index all available families
- `--clear`: Clear existing index before rebuilding (default: True)

**Examples:**

```bash
# Index all families
tbcv rag index --all-families

# Index specific family
tbcv rag index -f validation_rules

# Rebuild without clearing first
tbcv rag index --no-clear
```

#### rag search

Search truth data by semantic similarity.

```bash
tbcv rag search QUERY [-f FAMILY] [-k TOP_K] [-t THRESHOLD] [--format FORMAT]
```

**Options:**
- `-f, --family`: Truth family to search (default: words)
- `-k, --top-k`: Number of results (default: 5)
- `-t, --threshold`: Minimum similarity score 0.0-1.0 (default: 0.7)
- `--format`: Output format (table or json)

**Examples:**

```bash
# Find similar truths
tbcv rag search "user permissions"

# Return more results
tbcv rag search "content guidelines" -k 10

# Lower threshold for broader results
tbcv rag search "security validation" -t 0.5

# Get JSON output
tbcv rag search "testing" --format json
```

#### rag status

Show RAG indexing and search status.

```bash
tbcv rag status
```

Displays which families are indexed, total documents, and last update time.

#### rag clear

Clear the RAG vector index.

```bash
tbcv rag clear [-f FAMILY] [--confirm]
```

**Options:**
- `-f, --family`: Clear specific family (default: all)
- `--confirm`: Skip confirmation prompt

**Examples:**

```bash
# Clear all indices
tbcv rag clear --confirm

# Clear specific family
tbcv rag clear -f words

# Clear and rebuild
tbcv rag clear --confirm
tbcv rag index --all-families
```

## Common Workflows

### Basic File Validation

Validate a single file and review results:

```bash
# 1. Validate the file
tbcv validate myfile.md

# 2. Check validation history
tbcv validations history myfile.md

# 3. View detailed results
tbcv validations show <VALIDATION_ID>
```

### Recommendation and Enhancement Workflow

Validate, review recommendations, and apply enhancements:

```bash
# 1. Validate file
VALIDATION_ID=$(tbcv validate myfile.md --output json | jq -r '.validation_id')

# 2. Generate recommendations
tbcv recommendations generate $VALIDATION_ID

# 3. List recommendations
tbcv recommendations list --validation-id $VALIDATION_ID

# 4. Preview enhancement
tbcv enhance $VALIDATION_ID --preview

# 5. Apply enhancement (after reviewing preview)
tbcv enhance $VALIDATION_ID --threshold 0.8
```

### Batch Directory Processing

Process entire documentation directory:

```bash
# 1. Process all Markdown files
tbcv batch ./docs -r --report-file report.json

# 2. View summary
cat report.json | jq '.metrics'

# 3. Check failed validations
tbcv validations list --status fail

# 4. Reprocess failed files individually
tbcv validations revalidate <VALIDATION_ID>
```

### Quality Assurance Workflow

Complete validation and enhancement pipeline:

```bash
# 1. Create batch validation
tbcv batch ./content -r --report-file pre-check.json

# 2. Review results
tbcv validations list --status fail

# 3. Auto-apply low-risk recommendations
tbcv recommendations auto-apply <VALIDATION_ID> --threshold 0.9 --dry-run

# 4. Apply enhancements selectively
for REC_ID in $(tbcv recommendations list --status proposed --format json | jq -r '.[]._id'); do
  tbcv recommendations approve $REC_ID
done

# 5. Generate final report
tbcv batch ./content -r --report-file post-check.json --summary-only
```

## Advanced Usage

### Configuration Management

Use custom configuration files:

```bash
# Create custom config
cp config.example.yaml myconfig.yaml
# ... edit myconfig.yaml ...

# Use in commands
tbcv -c myconfig.yaml validate myfile.md

# For all subsequent commands
export TBCV_CONFIG=myconfig.yaml
tbcv validate myfile.md
```

### Output Formatting

Process output for integration with other tools:

```bash
# Get JSON output for scripting
tbcv validate myfile.md --output json | jq '.issues'

# Export to CSV (using jq)
tbcv validations list --format json | \
  jq -r '.[] | [.id, .status, .file_path] | @csv' > validations.csv

# Pretty-print YAML
tbcv validate myfile.md --output yaml | yq eval -P '.'
```

### Parallel Processing

Speed up large batch operations:

```bash
# Use maximum workers for fast processing
tbcv validate-directory ./docs -w $(nproc) --recursive

# Process multiple directories in parallel
for dir in docs/ content/ articles/; do
  tbcv validate-directory ./$dir -r --report-file ${dir}_report.json &
done
wait
```

### System Monitoring

Monitor system health and performance:

```bash
# Check system status
tbcv check-agents

# Get JSON for monitoring systems
tbcv check-agents --format json > health.json

# Monitor agent performance
tbcv status

# View workflow metrics
tbcv workflows list --format json | jq '.[] | {type, state, progress}'
```

### Troubleshooting Commands

```bash
# Enable debug logging
tbcv -v validate myfile.md

# Use MCP debug output
tbcv --mcp-debug validate myfile.md

# Test system configuration
tbcv test

# Check component health
tbcv check-agents --format json | jq '.components'
```

## Troubleshooting

### Common Issues and Solutions

#### Issue: "File not found" error

```bash
# Solution: Use absolute paths
tbcv validate-file /absolute/path/to/file.md

# Or use relative path from correct directory
cd /path/containing/file
tbcv validate-file ./file.md
```

#### Issue: Non-English content error

```
Error: Non-English content detected
Only English content can be processed.
```

**Solution:** TBCV only processes English content. Translate to English first or use original English files.

#### Issue: Worker process errors during batch

```bash
# Solution: Reduce worker count
tbcv validate-directory ./docs -w 2

# Or check system resources
tbcv check-agents
```

#### Issue: Cache inconsistencies

```bash
# Solution: Skip cache for fresh validation
tbcv validate myfile.md --no-cache

# Or clear cache entirely
tbcv admin cache-clear

# Rebuild cache
tbcv admin cache-rebuild
```

#### Issue: MCP connection errors

```bash
# Solution: Enable MCP debug logging
tbcv --mcp-debug validate-file myfile.md

# Check system status
tbcv check-agents --format json
```

### Getting Help

```bash
# Show main help
tbcv --help

# Show command-specific help
tbcv validate --help
tbcv validate-directory --help

# Show command group help
tbcv validations --help
tbcv recommendations --help
tbcv workflows --help

# Run test to verify installation
tbcv test
```

### Support Resources

- Run `tbcv --help` for command reference
- Run `tbcv COMMAND --help` for detailed command options
- Enable verbose logging: `tbcv -v COMMAND`
- Check system status: `tbcv check-agents`
- Review logs in verbose mode for detailed error information

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error or validation failure |
| 2 | Invalid command or argument |
| 3 | Configuration error |
| 4 | System/resource error |

## Performance Considerations

### Memory Usage

- Batch operations with many files may require significant memory
- Increase `--workers` gradually to monitor memory usage
- Use `--pattern` to limit file scope

### Processing Time

- Validation time depends on file size and complexity
- Use `--no-cache` for first run, then rely on cache for speed
- Parallel workers (higher `--workers`) speed up batch processing
- Confidence thresholds affect processing time (higher = slower)

### Caching

- Results are cached by default for faster subsequent runs
- Use `--no-cache` to force fresh analysis
- View cache stats: `tbcv admin cache-stats`
- Clear cache: `tbcv admin cache-clear`

## Examples Repository

See the `examples/` directory for complete workflow examples and scripts.

## Version Information

Run `tbcv --version` to see current version and component information.
