# TBCV System Architecture

## Overview

TBCV (Truth-Based Content Validation) is a multi-agent **content validation and enhancement system** for technical documentation. The system validates existing markdown files against rules and "truth data" (plugin definitions), detects plugin usage patterns through fuzzy matching, generates actionable recommendations, and applies approved enhancements through a human-in-the-loop workflow.

**Important**: TBCV validates and enhances **existing** content. It does not generate content from scratch.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     User Interfaces                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   CLI       │  │   REST API  │  │   Web Dashboard         │  │
│  │  (Click)    │  │  (FastAPI)  │  │   (Jinja2 Templates)    │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│          Agent Layer (19 Total: 9 Core + 3 Pipeline + 7 Val)      │
│ ┌─────────────────────── CORE AGENTS (9) ──────────────────────┐ │
│ │ OrchestratorAgent  TruthManagerAgent  FuzzyDetectorAgent      │ │
│ │ ContentValidatorAgent  ContentEnhancerAgent  LLMValidatorAgent │ │
│ │ CodeAnalyzerAgent  RecommendationAgent  EnhancementAgent      │ │
│ └──────────────────────────────────────────────────────────────┘ │
│ ┌───────────── PIPELINE AGENTS (3) ──────────────────────────┐  │
│ │ EditValidator  RecommendationEnhancer  RecommendationCritic │  │
│ └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                   Modular Validators (7 Validators)              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │YAML      │ │Markdown  │ │Code      │ │Link      │           │
│  │Validator │ │Validator │ │Validator │ │Validator │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                        │
│  │Structure │ │Truth     │ │SEO       │  ← ValidatorRouter     │
│  │Validator │ │Validator │ │Validator │                        │
│  └──────────┘ └──────────┘ └──────────┘                        │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                     Core Infrastructure                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Database    │  │ Cache       │  │ Config Loader           │  │
│  │ (SQLite)    │  │ (L1+L2)     │  │ (YAML/JSON)             │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Logging     │  │ Validation  │  │ Performance Tracking    │  │
│  │ (JSON)      │  │ Store       │  │                         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Validator   │  │ Error       │  │ Language Utils          │  │
│  │ Router      │  │ Formatter   │  │ (English enforcement)   │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                     External Services                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Ollama LLM  │  │ MCP Server  │  │ Truth Store (JSON)      │  │
│  │ (Optional)  │  │ (JSON-RPC)  │  │                         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Error Handling Architecture

TBCV implements a sophisticated **3-layer error handling system** that transforms errors from internal domain errors to user-friendly outputs across multiple channels (CLI, JSON, HTML, logs).

### Overview

The error handling architecture consists of three distinct layers:

```
┌─────────────────────────────────────────────────┐
│           Layer 1: MCP Errors                   │
│  (Domain-level exceptions with error codes)     │
│  - MCPError (base)                              │
│  - MCPMethodNotFoundError (-32601)              │
│  - MCPInvalidParamsError (-32602)               │
│  - MCPValidationError (-32000)                  │
│  - MCPResourceNotFoundError (-32001)            │
│  - MCPInternalError (-32603)                    │
│  - MCPTimeoutError (custom)                     │
└───────────────────┬─────────────────────────────┘
                    │
                    ↓
┌─────────────────────────────────────────────────┐
│      Layer 2: HTTP Exception Handlers           │
│  (FastAPI handlers - HTTP status mapping)       │
│  - mcp_exception_handler()                      │
│  - validation_exception_handler()               │
│  - generic_exception_handler()                  │
└───────────────────┬─────────────────────────────┘
                    │
                    ↓
┌─────────────────────────────────────────────────┐
│        Layer 3: Error Formatters                │
│  (Multi-format output generation)               │
│  - to_cli() - Colorized terminal output         │
│  - to_json() - API responses                    │
│  - to_html_context() - Web dashboard            │
│  - format_for_log() - Structured logging        │
└─────────────────────────────────────────────────┘
```

### Layer 1: MCP Errors (Domain Layer)

**File:** `svc/mcp_exceptions.py` (84 lines)

**Purpose:** Represent domain-level errors with JSON-RPC error codes

**Exception Hierarchy:**
```python
MCPError (base)
├── MCPMethodNotFoundError (-32601)    # JSON-RPC: Method not found
├── MCPInvalidParamsError (-32602)     # JSON-RPC: Invalid params
├── MCPInternalError (-32603)          # JSON-RPC: Internal error
├── MCPTimeoutError (custom)           # Custom: Request timeout
├── MCPValidationError (-32000)        # Custom: Validation failed
└── MCPResourceNotFoundError (-32001)  # Custom: Resource not found
```

**Base Class:**
```python
class MCPError(Exception):
    """Base exception for all MCP errors."""
    def __init__(
        self,
        message: str,
        code: Optional[int] = None,
        data: Optional[Any] = None
    ):
        super().__init__(message)
        self.code = code      # JSON-RPC error code
        self.data = data      # Additional error data
```

**Error Code Mappings:**

| Error Class | JSON-RPC Code | Description |
|-------------|---------------|-------------|
| MCPMethodNotFoundError | -32601 | Requested method does not exist |
| MCPInvalidParamsError | -32602 | Method parameters are invalid |
| MCPInternalError | -32603 | Internal MCP server error |
| MCPValidationError | -32000 | Content validation failed |
| MCPResourceNotFoundError | -32001 | Requested resource not found |
| MCPTimeoutError | (no code) | Request timed out |

**Usage Example:**
```python
from svc.mcp_exceptions import MCPValidationError

# In agent code
if not valid:
    raise MCPValidationError(
        "Content validation failed",
        code=-32000,
        data={
            "file_path": file_path,
            "issues": [
                {"line": 5, "message": "Invalid YAML frontmatter"}
            ]
        }
    )
```

**Factory Function:**
```python
from svc.mcp_exceptions import exception_from_error_code

# Create exception from JSON-RPC error code
exc = exception_from_error_code(
    code=-32000,
    message="Validation failed",
    data={"issues_count": 5}
)
# Returns: MCPValidationError instance
```

### Layer 2: HTTP Exception Handlers (Transport Layer)

**File:** `api/error_handlers.py` (380 lines)

**Purpose:** Convert MCP errors to HTTP responses with appropriate status codes

**Handler Functions:**

1. **mcp_exception_handler()** - Handles all MCP-specific errors
2. **validation_exception_handler()** - Handles Pydantic validation errors
3. **generic_exception_handler()** - Catch-all for unexpected errors

**Status Code Mapping:**

| MCP Error | HTTP Status | Code | Description |
|-----------|-------------|------|-------------|
| MCPMethodNotFoundError | 501 Not Implemented | -32601 | Method doesn't exist |
| MCPInvalidParamsError | 400 Bad Request | -32602 | Invalid parameters |
| MCPResourceNotFoundError | 404 Not Found | -32001 | Resource not found |
| MCPTimeoutError | 504 Gateway Timeout | - | Request timeout |
| MCPValidationError | 422 Unprocessable Entity | -32000 | Validation failed |
| MCPInternalError | 500 Internal Server Error | -32603 | Server error |
| MCPError (generic) | 500 Internal Server Error | - | Generic error |
| ValidationError (Pydantic) | 422 Unprocessable Entity | - | Request validation failed |
| Exception (generic) | 500 Internal Server Error | - | Unexpected error |

**Response Format:**
```json
{
  "error": "Content validation failed",
  "type": "MCPValidationError",
  "code": -32000,
  "data": {
    "issues": [...]
  },
  "meta": {
    "path": "/api/validate",
    "method": "POST",
    "timestamp": "2025-12-03T10:30:00Z"
  }
}
```

**Handler Registration:**
```python
from fastapi import FastAPI
from api.error_handlers import register_error_handlers

app = FastAPI()
register_error_handlers(app)  # Registers all handlers
```

**MCP Exception Handler:**
```python
@app.exception_handler(MCPError)
async def mcp_exception_handler(request: Request, exc: MCPError):
    """
    Convert MCP errors to HTTP responses.

    - Maps MCP error types to HTTP status codes
    - Includes error code and additional data
    - Logs error for monitoring
    - Adds request metadata (path, method, timestamp)
    """
    http_exc = mcp_error_to_http_exception(exc)
    # ... builds response with error details and metadata
    return JSONResponse(status_code=http_exc.status_code, content=error_response)
```

**Validation Exception Handler:**
```python
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle Pydantic validation errors.

    - Returns 422 Unprocessable Entity
    - Includes detailed validation error information
    - Lists all validation failures with locations
    """
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation failed",
            "type": "ValidationError",
            "validation_errors": exc.errors()
        }
    )
```

**Generic Exception Handler:**
```python
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Handle unexpected exceptions.

    - Returns 500 Internal Server Error
    - Logs full exception with traceback
    - Provides safe error message to clients
    - Handles Unicode encoding errors in logging
    """
    # Safe error handling with Unicode fallback
    try:
        error_msg = str(exc)
    except Exception:
        error_msg = repr(exc)

    # Log with Unicode safety
    try:
        logger.exception(f"Unexpected error: {error_msg}")
    except (UnicodeEncodeError, UnicodeDecodeError):
        logger.error("Unexpected error (encoding issue)")
```

### Layer 3: Error Formatters (Presentation Layer)

**File:** `core/error_formatter.py` (362 lines)

**Purpose:** Format errors for different output channels (CLI, API, Web, Logs)

**Output Formats:**

#### 1. CLI Output (Colorized Terminal)

**Features:**
- ANSI color codes (red for errors, yellow for warnings, cyan for info)
- Severity icons: `!!!` (critical), `[X]` (error), `[!]` (warning), `[i]` (info)
- Context snippets with line numbers
- Fix suggestions and examples
- Auto-fixable indicators
- Summary statistics by severity

**Usage:**
```python
from core.error_formatter import ErrorFormatter

output = ErrorFormatter.to_cli(
    issues,
    colorized=True,
    show_context=True,
    show_suggestions=True,
    max_issues=50
)
print(output)
```

**Example Output:**
```
Validation Results
Total: 5 issues
  Critical: 1
  Errors: 2
  Warnings: 2

------------------------------------------------------------
1. !!! CRITICAL [YAML-001] at line 2:5
   Invalid YAML frontmatter syntax
   Category: yaml | Confidence: 100%
   Context: title: "My Document...
   Suggestion: Add closing quote for title field
   Example: title: "My Document"

2. [X] ERROR [MD-042] at line 15
   Broken internal link
   Category: markdown
   Suggestion: Fix link target or remove link
   [Auto-fixable]
```

**ANSI Color Codes:**
```python
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    CRITICAL = "\033[91m"  # Bright red
    ERROR = "\033[31m"     # Red
    WARNING = "\033[33m"   # Yellow
    INFO = "\033[36m"      # Cyan
    GREEN = "\033[32m"     # Green
```

#### 2. JSON Output (API Responses)

**Features:**
- Complete issue details
- Summary statistics (by level, category, source)
- Severity breakdown
- Category grouping
- Auto-fixable count
- Compact mode available

**Usage:**
```python
json_output = ErrorFormatter.to_json(
    issues,
    include_summary=True,
    compact=False
)
return JSONResponse(content=json_output)
```

**Example Output:**
```json
{
  "issues": [
    {
      "level": "error",
      "category": "yaml",
      "code": "YAML-001",
      "message": "Invalid YAML frontmatter",
      "line_number": 2,
      "column": 5,
      "severity_score": 100,
      "context_snippet": "title: \"My Document...",
      "suggestion": "Add closing quote",
      "fix_example": "title: \"My Document\"",
      "auto_fixable": true,
      "source": "rule_based",
      "confidence": 1.0
    }
  ],
  "summary": {
    "total": 5,
    "by_level": {
      "critical": 1,
      "error": 2,
      "warning": 2,
      "info": 0
    },
    "by_category": {
      "yaml": 1,
      "markdown": 2,
      "code": 1,
      "truth": 1
    },
    "by_source": {
      "rule_based": 4,
      "llm": 1
    },
    "auto_fixable": 2,
    "severity_score_avg": 65.8
  }
}
```

**Compact Format:**
```python
# Compact mode omits empty fields for smaller payload
json_output = ErrorFormatter.to_json(issues, compact=True)
```

#### 3. HTML Context (Web Dashboard)

**Features:**
- Bootstrap CSS classes
- Grouped by severity or category
- Badge styling
- Template-ready data structure
- Boolean flags for conditional rendering

**Usage:**
```python
html_context = ErrorFormatter.to_html_context(
    issues,
    group_by="level"  # or "category" or "none"
)
return render_template("validation_detail.html", **html_context)
```

**Example Output:**
```python
{
  "summary": {...},
  "issues": [...],
  "grouped_issues": {
    "critical": [...],
    "error": [...],
    "warning": [...],
    "info": [...]
  },
  "severity_icons": {
    "critical": "!!!",
    "error": "[X]",
    "warning": "[!]",
    "info": "[i]"
  },
  "has_critical": True,
  "has_errors": True,
  "has_warnings": True,
  "auto_fixable_count": 2
}
```

**CSS Classes:**
```python
# Severity color classes
get_severity_color_class("critical")  # → "text-danger fw-bold"
get_severity_color_class("error")     # → "text-danger"
get_severity_color_class("warning")   # → "text-warning"
get_severity_color_class("info")      # → "text-info"

# Badge classes
get_severity_badge_class("critical")  # → "bg-danger"
get_severity_badge_class("warning")   # → "bg-warning text-dark"
```

#### 4. Log Format (Structured Logging)

**Features:**
- Single line per issue
- Grep-friendly format
- Truncated messages (100 chars)
- Location indicators
- Severity prefix

**Usage:**
```python
log_output = ErrorFormatter.format_for_log(issues)
logger.error(log_output)
```

**Example Output:**
```
[ERROR] YAML-001 @ L2: Invalid YAML frontmatter syntax
[ERROR] MD-042 @ L15: Broken internal link to /docs/missing.md
[WARNING] TRUTH-001 @ L20: Plugin 'AutoSave' used but not declared in frontmatter
[WARNING] CODE-050 @ L45: Code block missing language identifier
[INFO] SEO-010 @ L1: Consider adding meta description
```

### Error Flow Example

**Complete flow from agent to user:**

```python
# ============================================================
# Step 1: Agent raises MCP error (Domain Layer)
# File: agents/content_validator.py
# ============================================================
from svc.mcp_exceptions import MCPValidationError

async def validate_content(file_path: str, content: str):
    issues = []
    # ... validation logic ...

    if issues:
        raise MCPValidationError(
            "Content validation failed",
            code=-32000,
            data={
                "file_path": file_path,
                "issues_count": len(issues),
                "issues": [issue.to_dict() for issue in issues]
            }
        )

# ============================================================
# Step 2: FastAPI handler catches error (Transport Layer)
# File: api/error_handlers.py
# ============================================================
@app.exception_handler(MCPError)
async def mcp_exception_handler(request: Request, exc: MCPError):
    # Map to HTTP status code
    status_code = 422  # For MCPValidationError

    # Build response
    error_response = {
        "error": str(exc),
        "type": exc.__class__.__name__,
        "code": exc.code,
        "data": exc.data,
        "meta": {
            "path": str(request.url.path),
            "method": request.method,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }

    # Log error
    logger.error(
        f"MCP error on {request.method} {request.url.path}: {exc}",
        extra={"error_type": type(exc).__name__, "error_code": exc.code}
    )

    return JSONResponse(status_code=status_code, content=error_response)

# ============================================================
# Step 3: Client receives HTTP response
# ============================================================
# HTTP 422 Unprocessable Entity
# {
#   "error": "Content validation failed",
#   "type": "MCPValidationError",
#   "code": -32000,
#   "data": {
#     "file_path": "tutorial.md",
#     "issues_count": 5,
#     "issues": [...]
#   },
#   "meta": {
#     "path": "/api/validate",
#     "method": "POST",
#     "timestamp": "2025-12-03T10:30:00Z"
#   }
# }

# ============================================================
# Step 4: CLI formats for user (Presentation Layer)
# File: cli/main.py
# ============================================================
from core.error_formatter import ErrorFormatter

response = requests.post(url, json=payload)

if response.status_code != 200:
    error_data = response.json()

    # Extract issues from error data
    issues_data = error_data.get("data", {}).get("issues", [])
    issues = [ValidationIssue(**i) for i in issues_data]

    # Format for CLI output
    formatted = ErrorFormatter.to_cli(
        issues,
        colorized=True,
        show_context=True,
        show_suggestions=True
    )

    click.echo(formatted, err=True)
    sys.exit(1)
```

### Unicode Safety

All error handlers implement **Unicode safety** to prevent crashes on encoding errors, especially important for international content and Windows console output.

**Implementation:**

```python
# Safe error message extraction
try:
    error_msg = str(exc)
except Exception:
    error_msg = repr(exc)  # Fallback to repr

# Safe logging with Unicode handling
try:
    logger.exception(f"Error: {error_msg}")
except (UnicodeEncodeError, UnicodeDecodeError):
    # Fallback: log without exception details
    logger.error("Error occurred (encoding issue)")
```

**Why This Matters:**
- Windows console may not support UTF-8
- Error messages may contain non-ASCII characters from file content
- Prevents error handler from crashing when reporting errors
- Ensures logging always succeeds even with encoding problems

### Best Practices

#### 1. Always Use MCP Errors in Agent Code

**Good:**
```python
from svc.mcp_exceptions import MCPValidationError

if not valid:
    raise MCPValidationError(
        "Validation failed",
        code=-32000,
        data={"issues": issues}
    )
```

**Bad:**
```python
# Don't use generic exceptions in agent code
if not valid:
    raise ValueError("Validation failed")  # Won't be properly handled
```

#### 2. Let FastAPI Handlers Do HTTP Conversion

**Good:**
```python
# Agent code - raise MCP error
raise MCPValidationError("Validation failed", code=-32000)

# FastAPI automatically converts to HTTP 422
```

**Bad:**
```python
# Don't manually create HTTP responses in agent code
from fastapi.responses import JSONResponse

return JSONResponse(  # Bypasses error handling system
    status_code=422,
    content={"error": "Validation failed"}
)
```

#### 3. Use Appropriate Error Formatter

**CLI:**
```python
# Use to_cli() with colorization
output = ErrorFormatter.to_cli(issues, colorized=True)
```

**API:**
```python
# Use to_json() for structured responses
json_output = ErrorFormatter.to_json(issues, include_summary=True)
```

**Dashboard:**
```python
# Use to_html_context() for templates
html_context = ErrorFormatter.to_html_context(issues, group_by="level")
```

**Logs:**
```python
# Use format_for_log() for single-line output
log_output = ErrorFormatter.format_for_log(issues)
logger.error(log_output)
```

#### 4. Include Context in Error Data

**Good:**
```python
raise MCPValidationError(
    "Validation failed",
    code=-32000,
    data={
        "file_path": file_path,
        "issues_count": len(issues),
        "issues": [issue.to_dict() for issue in issues],
        "validation_types": validation_types
    }
)
```

**Minimal:**
```python
raise MCPValidationError("Validation failed", code=-32000)  # Less helpful
```

#### 5. Use Specific Error Types

**Good:**
```python
# Use specific error types for different scenarios
raise MCPResourceNotFoundError("Validation not found", code=-32001)
raise MCPTimeoutError("Request timed out after 30s")
raise MCPInvalidParamsError("Missing required parameter 'family'", code=-32602)
```

**Bad:**
```python
# Don't use generic MCPError for everything
raise MCPError("Something went wrong")  # Too generic
```

### Testing Error Handling

**Test MCP Exceptions:**
```python
import pytest
from svc.mcp_exceptions import MCPValidationError

def test_mcp_validation_error():
    exc = MCPValidationError(
        "Validation failed",
        code=-32000,
        data={"issues": []}
    )
    assert exc.code == -32000
    assert "Validation failed" in str(exc)
```

**Test HTTP Handlers:**
```python
from fastapi.testclient import TestClient
from api.server import app

def test_validation_error_returns_422():
    client = TestClient(app)
    response = client.post("/api/validate", json={"invalid": "data"})
    assert response.status_code == 422
    assert "error" in response.json()
```

**Test Error Formatter:**
```python
from core.error_formatter import ErrorFormatter
from agents.validators.base_validator import ValidationIssue

def test_cli_formatter():
    issues = [
        ValidationIssue(
            level="error",
            category="yaml",
            message="Invalid YAML",
            line_number=5
        )
    ]
    output = ErrorFormatter.to_cli(issues, colorized=False)
    assert "Invalid YAML" in output
    assert "line 5" in output
```

### Troubleshooting

See [Troubleshooting Guide](troubleshooting.md#error-handling) for common error handling issues including:
- Error responses not properly formatted
- Unicode encoding errors in logs
- Missing error codes or status codes
- Error handlers not being invoked

### Related Files

**Layer 1 (MCP Errors):**
- `svc/mcp_exceptions.py` - Exception classes and factory function

**Layer 2 (HTTP Handlers):**
- `api/error_handlers.py` - FastAPI exception handlers
- `api/mcp_helpers.py` - MCP-to-HTTP error conversion

**Layer 3 (Formatters):**
- `core/error_formatter.py` - Multi-format error output

**Supporting:**
- `agents/validators/base_validator.py` - ValidationIssue dataclass
- `core/logging.py` - Logging infrastructure

---

## Core Agents (11 Agents)

### OrchestratorAgent (`agents/orchestrator.py`)
**Responsibility**: Workflow coordination and execution
- Manages complex multi-step validation pipelines
- Handles concurrent workflow execution with per-agent semaphores
- Provides checkpointing and recovery mechanisms
- Implements retry logic with exponential backoff
- Supports workflow types: `validate_file`, `validate_directory`, `full_validation`, `content_update`

### TruthManagerAgent (`agents/truth_manager.py`)
**Responsibility**: Plugin truth data management and indexing
- Loads and indexes plugin definitions from JSON truth tables (`truth/` directory)
- Provides 6 indexes: by_id, by_slug, by_name, by_alias, by_pattern, by_family
- Uses Generic TruthDataAdapter to normalize various JSON schemas
- Handles SHA-256 versioning for change detection
- Cache TTL: 7 days (604800 seconds)

### FuzzyDetectorAgent (`agents/fuzzy_detector.py`)
**Responsibility**: Plugin detection using fuzzy matching algorithms
- Implements Levenshtein and Jaro-Winkler distance algorithms
- Analyzes context windows around potential matches
- Applies confidence scoring for detection accuracy
- Supports combination rules for multi-plugin detection
- Default similarity threshold: 0.85 (configurable)

### ContentValidatorAgent (`agents/content_validator.py`)
**Responsibility**: Legacy monolithic content validation (being replaced by modular validators)
- Validates YAML, Markdown, and code syntax
- Performs link validation and image checking
- Applies rule-based content quality assessment
- Generates detailed validation reports with issues and severity levels
- Supports two-stage truth validation (heuristic + optional LLM)

### ContentEnhancerAgent (`agents/content_enhancer.py`)
**Responsibility**: Content enhancement with safety gating
- Adds plugin hyperlinks to first mentions
- Inserts informational text after code blocks
- Prevents duplicate links and maintains formatting
- **Safety checks**: rewrite_ratio < 0.5, blocked topics detection
- Supports backup and rollback capabilities

### LLMValidatorAgent (`agents/llm_validator.py`)
**Responsibility**: AI-powered semantic validation (optional, disabled by default)
- Uses Ollama (llama2/mistral) for semantic plugin analysis
- Provides fallback to OpenAI/Gemini APIs
- Verifies fuzzy detector findings semantically
- Identifies missing plugins based on code semantics
- Graceful degradation when Ollama unavailable
- Timeout: 30 seconds

### CodeAnalyzerAgent (`agents/code_analyzer.py`)
**Responsibility**: Code quality and security analysis
- Analyzes Python, C#, Java, JavaScript code blocks
- Performs security scanning and complexity assessment
- Integrates with LLM for advanced analysis (optional)
- Provides performance optimization suggestions

### RecommendationAgent (`agents/recommendation_agent.py`)
**Responsibility**: Intelligent recommendation generation
- Analyzes validation results to generate improvements
- Type-specific templates (yaml, markdown, code, links, truth)
- Applies confidence thresholds (default: 0.7)
- Generates actionable instructions with rationale
- Persists recommendations in database with "proposed" status

### EnhancementAgent (`agents/enhancement_agent.py`)
**Responsibility**: Facade over ContentEnhancerAgent
- Applies approved recommendations to content
- Provides preview functionality
- Tracks enhancement statistics and success rates
- Maintains audit trail of changes

### EditValidatorAgent (`agents/edit_validator.py`)
**Responsibility**: Validates edits before/after enhancement
- Compares original and enhanced content
- Validates that enhancements are safe to apply
- Generates diff reports
- Supports rollback validation

### RecommendationEnhancerAgent (`agents/recommendation_enhancer.py`)
**Responsibility**: Recommendation application engine
- Applies approved recommendations to content
- Handles different recommendation types (yaml, markdown, code, link, truth)
- Generates diffs for applied changes
- Creates audit log entries

---

## Modular Validator Agents (7-8 Validators)

The modular validator architecture replaces the legacy monolithic ContentValidatorAgent with specialized, focused validators. See [modular_validators.md](modular_validators.md) for detailed documentation.

### ValidatorRouter (`agents/validators/router.py`)
Routes validation requests to appropriate modular validators with fallback to legacy ContentValidator.

### BaseValidatorAgent (`agents/validators/base_validator.py`)
Abstract base class defining the validator interface.

### Individual Validators

| Validator | File | Purpose |
|-----------|------|---------|
| **YamlValidatorAgent** | `yaml_validator.py` | YAML frontmatter validation |
| **MarkdownValidatorAgent** | `markdown_validator.py` | Markdown structure and syntax |
| **CodeValidatorAgent** | `code_validator.py` | Code block validation |
| **LinkValidatorAgent** | `link_validator.py` | Link and URL validation |
| **StructureValidatorAgent** | `structure_validator.py` | Document structure validation |
| **TruthValidatorAgent** | `truth_validator.py` | Truth data validation |
| **SeoValidatorAgent** | `seo_validator.py` | SEO metadata and heading size validation |

---

## Access Control & Security

TBCV implements a **dual-layer access control system** to enforce the MCP-first architecture and prevent direct access to business logic from CLI and API layers.

### Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  CLI Layer (cli/*) & API Layer (api/*)                      │
│  BLOCKED from direct access to business logic                │
└─────────────────────────────────────────────────────────────┘
        │
        │  Dual-Layer Access Control
        │  Layer 1: Import-Time Guard (sys.meta_path hook)
        │  Layer 2: Runtime Access Guard (@guarded_operation)
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│  MCP Server Layer (svc/mcp_server.py, svc/mcp_methods/*)   │
│  ALLOWED to access business logic                            │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│  Business Logic (agents/*, core/validation_store.py)        │
│  Protected by access guards                                  │
└─────────────────────────────────────────────────────────────┘
```

### Layer 1: Import-Time Guard

- **Location**: `core/import_guard.py` (333 lines)
- **Mechanism**: Python `sys.meta_path` hook intercepts imports
- **Protection**: Prevents API/CLI from importing protected modules
- **Configuration**: `config/access_guards.yaml`

**Protected Modules:**
- `agents.orchestrator`, `agents.content_validator`, `agents.content_enhancer`
- `agents.recommendation_agent`, `agents.truth_manager`, `agents.validators`
- `core.validation_store`

**Enforcement Modes:** DISABLED, WARN, BLOCK

### Layer 2: Runtime Access Guard

- **Location**: `core/access_guard.py` (447 lines)
- **Mechanism**: `@guarded_operation` decorator with stack inspection
- **Protection**: Prevents API/CLI from calling protected functions
- **Configuration**: Environment variable `TBCV_ACCESS_GUARD_MODE` or config file

**Stack Inspection:** Walks call stack to identify caller module and enforce access policy.

**Allowed Callers:**
- `svc/mcp_server.py` (MCP server)
- `svc/mcp_methods/*` (MCP method implementations)
- `tests/*` (test code)

**Blocked Callers:**
- `api/*` (API endpoints)
- `cli/*` (CLI commands)

### Enforcement Modes

| Mode | Import Guard | Runtime Guard | Use Case |
|------|-------------|---------------|----------|
| **DISABLED** | No enforcement | No enforcement | Local development |
| **WARN** | Log violations, allow | Log violations, allow | Staging, monitoring |
| **BLOCK** | Raise ImportGuardError | Raise AccessGuardError | Production |

### Configuration Example

```yaml
# config/access_guards.yaml
enforcement_mode: block  # disabled, warn, or block

protected_modules:
  - agents.orchestrator
  - agents.content_validator
  - core.validation_store

allowed_callers:
  - svc.mcp_server
  - svc.mcp_methods
  - tests

blocked_callers:
  - api
  - cli
```

### Usage Example

```python
from core.access_guard import guarded_operation

@guarded_operation
def validate_content(file_path: str) -> ValidationResult:
    """
    Protected function - can only be called from MCP layer or tests.
    Direct calls from API/CLI will be blocked.
    """
    # Business logic here
    return ValidationResult(status="pass")
```

See [Security Documentation](security.md) for complete details on the dual-layer access control system, including:
- Detailed architecture and data flow
- Configuration and installation
- Troubleshooting and best practices
- Security audit procedures

---

## Core Infrastructure Modules

### Database (`core/database.py`)
- SQLite-based persistent storage with SQLAlchemy ORM
- Connection pooling with configurable pool size
- Tables (7 total): Workflows, ValidationResults, Recommendations, Checkpoints, AuditLog, CacheEntries, Metrics
- Provides audit logging capabilities for compliance and debugging
- Performance metrics tracking for monitoring and alerting

### Configuration Loading (`core/config_loader.py`)
- Loads YAML and JSON configuration files
- Provides environment variable override support (`TBCV_` prefix)
- Validates configuration schema
- Supports hot-reloading for some settings

### Caching (`core/cache.py`)
- **Two-level caching**: L1 (memory LRU) + L2 (disk SQLite by default)
- **L1 Cache (Memory)**: In-process LRU cache for fast access
- **L2 Cache (Disk)**: SQLite-based persistent cache across restarts
  - **Default**: SQLite L2 cache (recommended for single-node deployments)
  - **Optional**: Redis L2 cache available for distributed multi-node deployments
  - See [deployment.md](deployment.md#redis-optional---not-default) for when to use Redis vs SQLite
- LRU eviction policies
- TTL-based expiration
- Compression support for large objects
- Graceful fallback if Redis unavailable (when configured)

### Logging (`core/logging.py`)
- Structured JSON logging with configurable levels
- File rotation and backup management
- Performance monitoring integration
- Context-aware logging with workflow IDs

### Validation Store (`core/validation_store.py`)
- Persistent storage for validation results
- Efficient querying and filtering
- Integration with recommendation system
- Performance metrics tracking

### Validator Router (`core/validator_router.py`)
- Routes validation requests to appropriate modular validators
- Maintains validator registry
- Falls back to ContentValidator for unknown types
- Tracks routing decisions for debugging

### Error Formatter (`core/error_formatter.py`)
- Standardizes error formatting for user display
- Formats validation issues with context
- Supports multiple output formats (text, JSON, HTML)

### Language Utils (`core/language_utils.py`)
- Language detection for content
- Enforces English-only content validation
- Rejects non-English content with appropriate error messages

### Performance Tracking (`core/performance.py`)
- Tracks validation and workflow performance
- Records timing metrics per agent
- Provides performance analysis utilities

### File Utils (`core/file_utils.py`)
- Safe file operations
- Path validation and sanitization
- Atomic file writes

---

## API Layer

### FastAPI Server (`api/server.py`)
- 40+ RESTful API endpoints for all operations
- WebSocket support for real-time workflow updates
- Server-Sent Events (SSE) for streaming updates
- CORS configuration for web UI
- Health check endpoints (`/health/live`, `/health/ready`, `/health/detailed`)
- OpenAPI documentation at `/docs`

### Dashboard (`api/dashboard.py`)
- Web-based UI for system monitoring
- Validation results visualization
- Recommendation management interface
- Workflow status tracking
- Jinja2 templates for HTML generation

### Live Event Bus (`api/services/live_bus.py`)
- Real-time event distribution
- WebSocket connection management
- Workflow progress notifications

---

## CLI Interface (`cli/main.py`)

Command-line interface with Rich console output:
- **15+ commands** for validation, recommendations, and admin operations
- File and directory validation commands
- Agent status checking
- Batch processing capabilities
- Recommendation approval/rejection workflow
- Admin commands for cache, health, and system management

---

## External Services

### MCP Server (`svc/mcp_server.py`)
Model Context Protocol server for external integrations:
- JSON-RPC interface for validation operations
- Methods: `validate_folder`, `approve`, `reject`, `enhance`
- Stdin/stdout communication mode (MCPStdioServer)
- Can be used as in-process client

### Ollama LLM Integration (Optional)
- Local LLM inference via Ollama API
- Default models: llama2, mistral
- **Disabled by default** - requires manual setup
- Fallback to OpenAI/Gemini if configured

### LangChain Status (Installed but Not Used for RAG)

**Why Not Used for RAG:**
LangChain is installed as a dependency but **not used** for TBCV's Retrieval-Augmented Generation (RAG) implementation. The rationale:

1. **Simplified Architecture**: Custom RAG implementation provides tighter control over plugin detection logic and truth data retrieval
2. **Reduced Coupling**: Avoids dependency on LangChain's evolving API and abstractions
3. **Performance**: Direct integration with ChromaDB allows optimization specific to TBCV's use case
4. **Maintainability**: Easier to debug and modify plugin matching logic without framework abstractions
5. **Flexibility**: Custom implementation supports specialized fuzzy matching + semantic search hybrid approach

**Custom RAG Implementation:**
TBCV uses a custom RAG approach combining:
- **TruthManagerAgent**: Indexes plugin definitions from JSON truth tables with 6 specialized indexes
- **FuzzyDetectorAgent**: Implements Levenshtein and Jaro-Winkler algorithms for pattern matching
- **LLMValidatorAgent**: Optional semantic validation using Ollama/OpenAI without LangChain framework
- **ChromaDB Integration**: Direct vector database access for semantic plugin search

**Future Uses:**
LangChain is reserved for potential future features such as:
- Complex multi-step agent chains with tool use
- Advanced prompt templates and few-shot learning
- Cross-document semantic understanding
- Integration with additional LLM providers

Currently, the custom implementation satisfies all production requirements for plugin validation and enhancement.

### Truth Store (`truth/` directory)
- JSON files defining plugin "ground truth"
- Supports multiple product families: words, pdf, cells, slides
- Contains plugin metadata: name, slug, patterns, dependencies, capabilities

---

## Data Flow

### Validation Flow

```
Existing Markdown File
        ↓
TruthManagerAgent.load_truth_data(family)
        ↓ (load plugin definitions and indexes)
FuzzyDetectorAgent.detect_plugins(content, family)
        ↓ (pattern matching + fuzzy algorithms)
ValidatorRouter → Modular Validators
        │
        ├── Tier 1 (parallel): YAML, Markdown, Structure
        ├── Tier 2 (parallel): Code, Links, SEO, HeadingSizes
        └── Tier 3 (sequential): FuzzyLogic → Truth → LLM (optional)
        ↓
RecommendationAgent.generate_recommendations()
        ↓ (generate actionable suggestions)
Database (persist validation + recommendations)
        ↓
[Human Review & Approval]
        ↓
ContentEnhancerAgent.enhance_from_recommendations()
        ↓ (apply approved changes with safety checks)
Enhanced Markdown + Audit Trail
```

### Tiered Validation Execution

Validators execute in 3 tiers (configurable in `config/validation_flow.yaml`):

**Tier 1 - Quick Checks** (parallel):
- YAML frontmatter validation
- Markdown syntax validation
- Document structure validation

**Tier 2 - Content Analysis** (parallel):
- Code block validation
- Link validation
- SEO validation
- Heading size validation

**Tier 3 - Advanced Validation** (sequential, optional):
- FuzzyLogic → Truth → LLM
- Dependencies: Truth requires FuzzyLogic, LLM requires Truth
- LLM validation disabled by default

---

## Configuration Architecture

TBCV uses hierarchical configuration:

1. **Base config**: `config/main.yaml` (system settings)
2. **Agent config**: `config/agent.yaml` (per-agent settings)
3. **Validator configs**: 8 modular validator config files
   - `config/cache.yaml`
   - `config/code.yaml`
   - `config/frontmatter.yaml`
   - `config/links.yaml`
   - `config/markdown.yaml`
   - `config/structure.yaml`
   - `config/truth.yaml`
   - `config/seo.yaml`
   - `config/llm.yaml`
4. **Validation flow**: `config/validation_flow.yaml` (tiered execution, profiles)
5. **Performance**: `config/perf.json` (tuning parameters)
6. **Environment overrides**: `TBCV_` prefix

See [configuration.md](configuration.md) for complete reference.

---

## Technology Stack

- **Backend**: Python 3.8+, FastAPI, Uvicorn
- **Database**: SQLite with SQLAlchemy ORM
- **Caching**: Custom two-level cache (L1 memory LRU + L2 disk SQLite)
- **APIs**: REST, WebSocket, Server-Sent Events (SSE)
- **CLI**: Click framework with Rich console output
- **Templates**: Jinja2 for web dashboard
- **LLM Integration** (optional): Ollama (llama2/mistral), with fallback to OpenAI/Gemini
- **Fuzzy Matching**: Levenshtein distance, Jaro-Winkler similarity
- **Logging**: Structured JSON logging with rotation
- **Real-time Updates**: WebSocket via wsproto
- **Async**: asyncio throughout for concurrency

---

## Deployment Architecture

### Local Development
- Single-process Uvicorn server with `--reload`
- SQLite database in `data/` directory
- File-based logging and caching

### Production Deployment
- Gunicorn/Uvicorn with multiple workers
- Volume mounts for data persistence
- Environment-based configuration
- Systemd service (Linux) or Windows Service

See [deployment.md](deployment.md) for detailed deployment guides.

---

## Database Schema

### Core Tables (7 Total)

| Table | Purpose |
|-------|---------|
| **Workflows** | Track workflow execution state (id, type, status, created_at, etc.) |
| **ValidationResults** | Store validation outcomes (id, file_path, status, issues, confidence) |
| **Recommendations** | Store generated recommendations with approval workflow (id, validation_id, type, instruction, status) |
| **Checkpoints** | Track workflow progress for recovery (workflow_id, checkpoint_name, data) |
| **AuditLog** | Audit trail for all changes (id, action, entity_id, user, timestamp) |
| **CacheEntries** | L2 persistent cache for validation results and LLM responses (cache_key, agent_id, result_data, expires_at) |
| **Metrics** | Application performance metrics for monitoring and alerting (id, name, value, created_at, metadata) |

---

## Usage Examples

### Initializing Agents

```python
from agents.orchestrator import OrchestratorAgent
from agents.fuzzy_detector import FuzzyDetectorAgent
from agents.content_validator import ContentValidatorAgent
from agents.base import agent_registry

# Create and register orchestrator agent
orchestrator = OrchestratorAgent()
agent_registry.register_agent(orchestrator)

# Create and register fuzzy detector
fuzzy_detector = FuzzyDetectorAgent()
agent_registry.register_agent(fuzzy_detector)

# Create and register content validator
content_validator = ContentValidatorAgent()
agent_registry.register_agent(content_validator)

# Retrieve agent from registry
orchestrator = agent_registry.get_agent("orchestrator")
```

### Validating Content

```python
import asyncio

async def validate_content():
    """Validate markdown content and get issues."""
    from agents.orchestrator import OrchestratorAgent

    orchestrator = OrchestratorAgent()

    result = await orchestrator.process_request(
        method="validate_file",
        params={
            "file_path": "tutorial.md",
            "content": "# Tutorial\n\nContent here",
            "family": "words",
            "validation_types": ["yaml", "markdown", "truth"]
        }
    )

    return result

# Run async function
result = asyncio.run(validate_content())
print(f"Validation status: {result['status']}")
print(f"Issues found: {len(result['issues'])}")
```

### Using the Error Formatter

```python
from core.error_formatter import ErrorFormatter
from agents.validators.base_validator import ValidationIssue

def format_validation_issues(issues: list) -> str:
    """Format validation issues for CLI output."""
    validation_issues = [
        ValidationIssue(**issue) for issue in issues
    ]

    # Format for colorized terminal output
    cli_output = ErrorFormatter.to_cli(
        validation_issues,
        colorized=True,
        show_context=True,
        show_suggestions=True
    )

    return cli_output

def export_validation_results(issues: list) -> dict:
    """Export validation results as JSON."""
    validation_issues = [
        ValidationIssue(**issue) for issue in issues
    ]

    # Format for API response
    json_output = ErrorFormatter.to_json(
        validation_issues,
        include_summary=True,
        compact=False
    )

    return json_output
```

### Accessing the Database

```python
from core.database import db_manager, ValidationResult, Recommendation

def get_validation_details(validation_id: str) -> dict:
    """Retrieve validation details from database."""
    with db_manager.get_session() as session:
        validation = session.query(ValidationResult).filter_by(
            id=validation_id
        ).first()

        if validation:
            return {
                'id': validation.id,
                'file_path': validation.file_path,
                'status': validation.status,
                'created_at': validation.created_at.isoformat(),
                'validation_results': validation.validation_results
            }
        return None

def get_pending_recommendations(validation_id: str) -> list:
    """Get pending recommendations for a validation."""
    from core.database import RecommendationStatus

    with db_manager.get_session() as session:
        recommendations = session.query(Recommendation).filter(
            Recommendation.validation_id == validation_id,
            Recommendation.status == RecommendationStatus.PENDING
        ).all()

        return [
            {
                'id': rec.id,
                'type': rec.type,
                'instruction': rec.instruction,
                'confidence': rec.confidence
            }
            for rec in recommendations
        ]
```

### Caching Operations

```python
from core.cache import CacheManager

def get_with_caching(key: str, fetch_fn):
    """Get value with L1/L2 caching."""
    cache = CacheManager()

    # Check L1 cache
    value = cache.get(key, level='l1')
    if value is not None:
        return value

    # Check L2 cache
    value = cache.get(key, level='l2')
    if value is not None:
        cache.set(key, value, level='l1')  # Populate L1
        return value

    # Fetch from source
    value = fetch_fn()
    cache.set(key, value, level='l1')
    cache.set(key, value, level='l2')

    return value

# Example usage
def fetch_plugin_data():
    """Fetch from truth manager."""
    from agents.truth_manager import TruthManagerAgent
    manager = TruthManagerAgent()
    return manager.load_truth_data('words')

plugins = get_with_caching('plugins_words', fetch_plugin_data)
```

## Related Documentation

- [Agents Reference](agents.md) - Detailed agent documentation
- [Security Architecture](security.md) - Dual-layer access control system
- [Modular Validators](modular_validators.md) - Validator architecture
- [Workflows](workflows.md) - Workflow types and execution
- [Configuration](configuration.md) - System configuration
- [API Reference](api_reference.md) - REST API endpoints
- [CLI Usage](cli_usage.md) - Command-line interface
- [MCP Integration](mcp_integration.md) - Model Context Protocol server
- [Code Examples](code_examples.md) - Comprehensive code examples
