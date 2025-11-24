Here’s a cleaned, properly formatted version—same content, clearer structure and readable Markdown.

````md
# TBCV System Architecture

| **Title** | System Architecture |
|---|---|
| **Version** | auto |
| **Source** | Code analysis @ 2025-11-03T07:43:18Z |

## Overview

TBCV employs a multi-agent architecture where specialized agents collaborate through the Model Context Protocol (MCP) to process, validate, and enhance content. The system is designed around event-driven processing with clear separation of concerns.

## Core Components

### Agent Layer

The heart of TBCV consists of specialized agents, each with distinct responsibilities:

#### 1) TruthManagerAgent (`agents/truth_manager.py:41-686`)
**Responsibility:** Plugin truth data management and indexing  
**Key Classes:** `PluginInfo`, `CombinationRule`, `TruthDataIndex`  
**Primary Functions:**
- Load and index plugin definitions from JSON truth tables
- B-tree indexing for O(log n) plugin lookups
- SHA-256 versioning for change detection
- Pattern compilation and caching

#### 2) FuzzyDetectorAgent (`agents/fuzzy_detector.py:34-196`)
**Responsibility:** Intelligent plugin detection using fuzzy algorithms  
**Key Classes:** `PluginDetection`, `FuzzyDetectorAgent`  
**Primary Functions:**
- Multi-algorithm fuzzy matching (Levenshtein, Jaro-Winkler, Ratio)
- Context-aware detection with configurable windows
- Confidence scoring with combination rules

#### 3) ContentValidatorAgent (`agents/content_validator.py:42-496`)
**Responsibility:** Comprehensive content quality validation  
**Key Classes:** `ValidationIssue`, `ValidationResult`, `ContentValidatorAgent`  
**Primary Functions:**
- YAML frontmatter validation with field classification
- Markdown structure analysis and heading hierarchy
- Code quality checks for multiple languages
- Link validation with timeout handling

#### 4) ContentEnhancerAgent (`agents/content_enhancer.py:28-439`)
**Responsibility:** Intelligent content enhancement and plugin link