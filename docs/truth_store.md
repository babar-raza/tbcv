# Truth Store and Plugins

## Overview

The Truth Store is TBCV's authoritative knowledge base containing plugin definitions, usage patterns, and validation rules. It enables intelligent detection of third-party library usage in technical documentation and code samples.

## Truth Data Structure

### Plugin Families

TBCV supports multiple plugin families, each representing a different Aspose product:

- **words**: Aspose.Words for document processing
- **cells**: Aspose.Cells for spreadsheet processing
- **slides**: Aspose.Slides for presentation processing
- **pdf**: Aspose.PDF for PDF processing
- **email**: Aspose.Email for email processing

### Truth File Format

Truth data is stored in JSON files with the following structure:

```json
{
  "name": "Aspose.Words",
  "family": "words",
  "version": "24.1.0",
  "description": "Word document processing library",
  "plugins": [
    {
      "name": "Document.Save",
      "slug": "save-document",
      "patterns": [
        "Document.Save",
        "document.Save",
        "doc.Save"
      ],
      "contexts": [
        "Save document to file",
        "Export document",
        "Write document"
      ],
      "examples": [
        "doc.Save(filename)",
        "document.Save(outputPath)"
      ],
      "confidence_weights": {
        "exact_match": 1.0,
        "fuzzy_match": 0.8,
        "context_match": 0.6
      }
    }
  ],
  "combinations": [
    {
      "name": "Document Processing",
      "plugins": ["Document.Save", "Document.Load"],
      "description": "Complete document load and save workflow"
    }
  ]
}
```

### Combination Rules

Combination rules detect multi-plugin usage patterns:

```json
{
  "name": "Document Conversion",
  "plugins": ["Document.Load", "Document.Save"],
  "required_plugins": ["Document.Load"],
  "optional_plugins": ["Document.Save"],
  "min_plugins": 2,
  "description": "Document format conversion workflow"
}
```

## Truth Store Architecture

### Directory Structure
```
truth/
├── words/
│   ├── aspose_words_plugins_truth.json
│   └── aspose_words_plugins_combinations.json
├── cells/
│   ├── aspose_cells_plugins_truth.json
│   └── aspose_cells_plugins_combinations.json
├── slides/
├── pdf/
└── email/
```

### TruthManagerAgent

The TruthManagerAgent handles truth data management:

**Key Responsibilities**:
- Load and parse truth JSON files
- Build in-memory indexes for fast lookups
- Handle versioning and change detection
- Provide plugin metadata and validation

**Configuration**:
```yaml
truth_manager:
  enabled: true
  auto_reload: true
  validation_strict: false
  cache_ttl_seconds: 604800
  truth_directories:
    - "./truth"
    - "./truth/words"
    - "./truth/pdf"
    - "./truth/cells"
```

### Indexing Strategy

Truth data uses multiple indexing approaches:

#### B-Tree Indexing
- Plugin names indexed for O(log n) lookups
- Pattern arrays indexed for fast searching
- Family-based partitioning for scalability

#### Pattern Compilation
- Regular expressions pre-compiled for performance
- Fuzzy matching patterns optimized
- Context keywords indexed

#### Caching Layers
- L1: Memory cache for active patterns
- L2: Disk cache for full truth data
- TTL-based expiration and refresh

## Plugin Detection Process

### 1. Content Analysis
```python
# Extract code blocks and text content
content_blocks = extract_code_blocks(content)
text_content = extract_text_content(content)
```

### 2. Pattern Matching
```python
# Exact pattern matching
exact_matches = find_exact_patterns(content_blocks, truth_patterns)

# Fuzzy pattern matching
fuzzy_matches = find_fuzzy_patterns(content_blocks, truth_patterns, threshold=0.85)

# Context-aware matching
context_matches = find_context_patterns(text_content, context_keywords)
```

### 3. Confidence Scoring
```python
# Calculate confidence scores
confidence = calculate_confidence(exact_matches, fuzzy_matches, context_matches)

# Apply family-specific weights
weighted_confidence = apply_family_weights(confidence, family)
```

### 4. Combination Detection
```python
# Detect plugin combinations
combinations = detect_combinations(detected_plugins, combination_rules)

# Validate combination requirements
valid_combinations = validate_combinations(combinations)
```

## Fuzzy Detection Algorithms

### Levenshtein Distance
Measures edit distance between strings:
- Insertions, deletions, substitutions
- Normalized score (0.0 to 1.0)
- Used for typo detection

### Jaro-Winkler Distance
Optimized for short strings and prefixes:
- Better for plugin method names
- Higher weight for common prefixes
- Used for method name variations

### Context Window Analysis
Analyzes surrounding text for relevance:
- Keyword proximity scoring
- Semantic context validation
- False positive reduction

## Plugin Metadata

### Plugin Information Structure
```python
@dataclass
class PluginInfo:
    name: str
    slug: str
    family: str
    description: str
    patterns: List[str]
    contexts: List[str]
    examples: List[str]
    documentation_url: str
    version_added: str
    deprecated: bool
```

### Plugin Categories

#### Core Plugins
Essential functionality for the product family:
- Document loading/saving
- Basic formatting
- Standard operations

#### Advanced Plugins
Complex or specialized features:
- Mail merge
- Digital signatures
- OCR capabilities

#### Legacy Plugins
Deprecated but still supported:
- Old API methods
- Backwards compatibility
- Migration guidance

## Truth Data Management

### Adding New Plugins
```python
# 1. Create plugin definition
new_plugin = {
    "name": "Document.Protect",
    "slug": "protect-document",
    "patterns": ["Document.Protect", "doc.Protect"],
    "contexts": ["password protection", "document security"],
    "examples": ["doc.Protect(password)"],
    "family": "words"
}

# 2. Add to truth file
update_truth_file("truth/words/aspose_words_plugins_truth.json", new_plugin)

# 3. Reload truth manager
await truth_manager.reload_truth_data()
```

### Updating Plugin Patterns
```python
# Update existing patterns
update_plugin_patterns("Document.Save", [
    "Document.Save",
    "document.Save",
    "doc.Save",
    "SaveDocument"
])

# Add new pattern variations
add_pattern_variations("Document.Save", ["saveDoc", "exportDoc"])
```

### Version Management
```python
# Check for updates
latest_version = check_truth_updates()
if latest_version > current_version:
    download_truth_update(latest_version)
    reload_truth_data()
```

## Validation Rules

### Content Validation
Rules for validating documentation content:

#### YAML Front Matter
```yaml
rules:
  - name: "valid_yaml"
    type: "yaml_syntax"
    severity: "error"
    message: "Invalid YAML front matter"

  - name: "required_fields"
    type: "yaml_fields"
    fields: ["title", "description"]
    severity: "warning"
```

#### Markdown Structure
```yaml
rules:
  - name: "heading_hierarchy"
    type: "markdown_headings"
    max_depth: 6
    severity: "info"

  - name: "code_block_language"
    type: "code_language"
    required: true
    severity: "warning"
```

#### Code Quality
```yaml
rules:
  - name: "syntax_check"
    type: "code_syntax"
    languages: ["csharp", "python", "java"]
    severity: "error"

  - name: "plugin_usage"
    type: "plugin_reference"
    required: true
    severity: "warning"
```

### Rule Engine

The rule engine processes validation rules:

```python
class RuleEngine:
    def __init__(self, rules_config):
        self.rules = self.load_rules(rules_config)
        self.validators = {
            "yaml_syntax": YamlSyntaxValidator(),
            "markdown_headings": MarkdownHeadingValidator(),
            "code_syntax": CodeSyntaxValidator(),
            "plugin_reference": PluginReferenceValidator()
        }

    def validate_content(self, content, file_path):
        issues = []
        for rule in self.rules:
            validator = self.validators.get(rule.type)
            if validator:
                rule_issues = validator.validate(content, rule)
                issues.extend(rule_issues)
        return issues
```

## Plugin Linking System

### Automatic Link Generation
```python
def generate_plugin_links(content, detected_plugins):
    """Generate markdown links for detected plugins."""
    linked_content = content
    for plugin in detected_plugins:
        if plugin.confidence > 0.8:
            link = f"[{plugin.name}]({plugin.documentation_url})"
            linked_content = linked_content.replace(plugin.name, link)
    return linked_content
```

### Link Templates
Configurable link templates for different outputs:

```yaml
link_templates:
  markdown: "[{name}]({url})"
  html: '<a href="{url}">{name}</a>'
  confluence: "[{name}|{url}]"
```

### Link Validation
```python
def validate_plugin_links(content):
    """Validate that plugin links are accessible."""
    links = extract_links(content)
    invalid_links = []
    
    for link in links:
        if not is_plugin_link_accessible(link):
            invalid_links.append(link)
    
    return invalid_links
```

## Truth Data Sources

### Official Documentation
- Product API references
- Code examples from documentation
- SDK repositories

### Community Contributions
- User-reported patterns
- GitHub issues and PRs
- Community forums

### Automated Discovery
- Code analysis of repositories
- Pattern mining from existing content
- ML-based pattern detection

## Performance Optimization

### Caching Strategies
```python
# Pattern caching
pattern_cache = LRUCache(maxsize=10000)

# Truth data caching
truth_cache = TTLCache(ttl=3600)

# Index caching
index_cache = PersistentCache("truth_indexes.db")
```

### Parallel Processing
```python
async def detect_plugins_parallel(content, patterns, max_workers=4):
    """Parallel plugin detection."""
    chunks = split_content(content, chunk_size=1000)
    
    tasks = []
    for chunk in chunks:
        task = asyncio.create_task(detect_in_chunk(chunk, patterns))
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    return combine_results(results)
```

### Memory Management
```python
# Streaming for large files
def process_large_file(file_path, chunk_size=8192):
    with open(file_path, 'r') as f:
        while chunk := f.read(chunk_size):
            yield process_chunk(chunk)
```

## Monitoring and Maintenance

### Truth Data Health
```python
def check_truth_health():
    """Monitor truth data quality and completeness."""
    metrics = {
        "total_plugins": count_plugins(),
        "patterns_per_plugin": avg_patterns_per_plugin(),
        "coverage_score": calculate_coverage(),
        "last_updated": get_last_update_time()
    }
    return metrics
```

### Pattern Effectiveness
```python
def analyze_pattern_effectiveness():
    """Analyze which patterns are most effective."""
    pattern_stats = {
        pattern: {
            "matches": count_matches(pattern),
            "false_positives": count_false_positives(pattern),
            "confidence": avg_confidence(pattern)
        }
        for pattern in all_patterns
    }
    return sorted(pattern_stats.items(), key=lambda x: x[1]["matches"])
```

### Update Process
```python
async def update_truth_data():
    """Automated truth data updates."""
    # Check for new versions
    updates = await check_for_updates()
    
    # Download and validate
    for update in updates:
        await download_update(update)
        validate_update(update)
    
    # Apply updates
    await apply_updates(updates)
    
    # Reload agents
    await reload_agents()
    
    # Validate system
    await run_validation_tests()
```

This comprehensive truth store system enables accurate plugin detection and provides the foundation for TBCV's intelligent content validation capabilities.