# TBCV Glossary
> Title: Glossary
> Version: auto
> Source: System documentation @ 2025-11-03T08:43:00Z

## A

**Agent**
A specialized component in TBCV responsible for specific processing tasks. Each agent has a defined scope and communicates via the Model Context Protocol.

**API Endpoint**
A specific URL path that accepts HTTP requests and returns responses. TBCV exposes REST and WebSocket endpoints.

**AST (Abstract Syntax Tree)**
A tree representation of source code structure used by CodeAnalyzerAgent for deep code analysis.

**Aspose**
A family of document processing APIs that TBCV specializes in detecting and documenting (Words, Cells, Slides, PDF, Email).

**Async/Await**
Python's asynchronous programming model used throughout TBCV for concurrent I/O operations.

**Audit Log**
A chronological record of system activities stored in the database for compliance and debugging.

## B

**Batch Processing**
The ability to validate or enhance multiple files in a single operation.

**B-tree Index**
A self-balancing tree data structure used by TruthManagerAgent for O(log n) plugin lookups.

**Background Task**
Long-running operations executed asynchronously without blocking the main request.

## C

**Cache**
Two-level storage system (L1 memory + L2 persistent) for improving performance by storing frequently accessed data.

**Combination Rule**
Logic that defines how multiple plugin patterns combine to identify complex plugin usage.

**Confidence Score**
A value between 0 and 1 indicating the certainty of plugin detection.

**Content Enhancement**
The process of improving content by adding links, fixing formatting, and inserting information.

**Content Validation**
Checking content against defined rules for structure, syntax, and quality issues.

**Context Window**
The surrounding text area analyzed when detecting plugin patterns.

**CRLF**
Carriage Return + Line Feed (\\r\\n), the Windows line ending format.

## D

**Dashboard**
Web-based UI for monitoring and managing TBCV operations.

**Database Manager**
Core component handling all SQLite database operations.

**Dependency**
A step or component that must complete before another can begin.

**Detection Pattern**
Regular expression or string pattern used to identify plugin usage.

**Document Flow**
The sequence of operations performed on a document in Aspose APIs (load → process → save).

## E

**Enhancement**
A modification made to content to improve quality or add information.

**Enhancement Result**
Data structure containing modified content and metadata about changes made.

**Event-Driven**
Architecture pattern where components react to events rather than polling.

**Export Service**
API functionality for downloading validation results in various formats.

## F

**FastAPI**
The Python web framework used for TBCV's REST API implementation.

**First-Occurrence Linking**
Strategy of adding hyperlinks only to the first mention of a plugin to avoid over-linking.

**Frontmatter**
YAML metadata at the beginning of Markdown files.

**Fuzzy Detection**
Approximate pattern matching using algorithms like Levenshtein distance.

**Fuzzy Matching**
Finding patterns that approximately match rather than exactly match.

## G

**GitHub Gist**
External code snippets that can be fetched and analyzed by TBCV.

## H

**Health Check**
Endpoint that reports system status and component readiness.

## I

**Index**
Data structure for fast lookups, particularly the B-tree index for plugins.

**Integration Test**
Test that verifies multiple components working together.

## J

**Jaro-Winkler**
String similarity algorithm used in fuzzy detection.

**JSON**
JavaScript Object Notation, used for API communication and configuration.

## L

**L1 Cache**
In-memory cache for fastest access to frequently used data.

**L2 Cache**
Persistent SQLite-based cache for expensive computations.

**Levenshtein Distance**
Algorithm measuring the minimum edits needed to transform one string into another.

**Logging System**
Structured logging infrastructure for debugging and monitoring.

## M

**Markdown**
Lightweight markup language used for documentation.

**MCP (Model Context Protocol)**
Communication protocol used between TBCV agents.

**Metrics**
Performance and usage statistics collected by the system.

**Multi-Agent**
Architecture pattern where specialized agents collaborate on tasks.

## O

**Orchestrator**
Agent responsible for coordinating workflows between other agents.

**ORM (Object-Relational Mapping)**
SQLAlchemy's approach to database interaction using Python objects.

## P

**Pattern Compilation**
Pre-processing regex patterns for improved performance.

**Plugin**
An Aspose product or feature detected in content.

**Plugin Detection**
The process of identifying Aspose product usage in content.

**Plugin Family**
A group of related Aspose products (e.g., Words, Cells, Slides).

**Plugin Info**
Metadata about a detected plugin including patterns and documentation links.

**Pydantic**
Python library for data validation using type annotations.

## Q

**Queue**
Data structure for managing background tasks and batch operations.

## R

**Recommendation**
Suggested improvement for content based on validation results.

**Retry Logic**
Automatic re-execution of failed operations with exponential backoff.

**Rule**
A validation criterion with pattern, severity, and message.

**Runbook**
Operational procedures for running and maintaining TBCV.

## S

**SHA-256**
Cryptographic hash function used for version detection.

**SQLAlchemy**
Python SQL toolkit and ORM used for database operations.

**SQLite**
Embedded database engine used for persistence.

**Step**
Individual operation in a workflow with defined inputs/outputs.

**Streaming Parser**
Technique for processing large files without loading entirely into memory.

## T

**TBCV**
Truth-Based Content Validation, the system name.

**Template**
Jinja2 HTML file for web UI rendering or text template for content insertion.

**Truth Data**
Authoritative plugin definitions and patterns.

**Truth Manager**
Agent responsible for loading and indexing plugin truth tables.

**Truth Table**
JSON file containing plugin patterns and metadata.

**Two-Level Cache**
Caching strategy with memory (L1) and disk (L2) layers.

## U

**Uvicorn**
ASGI server running the FastAPI application.

## V

**Validation Issue**
Problem identified during content validation with severity and location.

**Validation Result**
Complete output of validation including issues and metrics.

**Validation Rule**
Specific check performed on content with associated pattern and message.

**Version Detection**
Using SHA-256 hashes to identify when truth tables change.

## W

**WebSocket**
Protocol for real-time bidirectional communication.

**Workflow**
Multi-step process coordinated by OrchestratorAgent.

**Workflow Result**
Final output of a complete workflow execution.

**Workflow State**
Persisted progress information for workflow recovery.

**Worker Pool**
Set of concurrent processors for batch operations.

## Y

**YAML**
Data serialization format used for configuration and frontmatter.

---

For more detailed information, see:
- [System Overview](system.md) - High-level description
- [Architecture](architecture.md) - Technical design
- [Components](components.md) - Module details
- [FAQ](faq.md) - Common questions
