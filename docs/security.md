# TBCV Security Architecture

## Table of Contents

- [Overview](#overview)
- [Dual-Layer Access Control](#dual-layer-access-control)
- [Runtime Access Guard](#runtime-access-guard)
- [Import-Time Guard](#import-time-guard)
- [Configuration](#configuration)
- [Path Validation](#path-validation)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Security Audit](#security-audit)

---

## Overview

TBCV implements a comprehensive security architecture with multiple layers of protection to ensure the integrity and safety of content validation operations. The system enforces the **MCP-first architecture** through dual-layer access control, preventing direct access to business logic from CLI and API layers.

### Security Principles

1. **Defense in Depth**: Multiple security layers provide redundancy
2. **Least Privilege**: Components only access what they need
3. **Fail-Safe Defaults**: Secure by default, opt-in for flexibility
4. **Separation of Concerns**: Clear architectural boundaries enforced at runtime
5. **Audit Trail**: All security violations logged and tracked

### Security Layers

TBCV employs five primary security mechanisms:

| Layer | Component | Purpose | Enforcement Point |
|-------|-----------|---------|------------------|
| **Import-Time** | Import Guard | Prevent unauthorized module imports | Python import system (sys.meta_path) |
| **Runtime** | Access Guard | Prevent unauthorized function calls | Function decorator (@guarded_operation) |
| **Input Validation** | Pydantic Models | Validate all API inputs | FastAPI request handling |
| **Path Validation** | File Utils | Prevent directory traversal | File operations |
| **Content Sanitization** | Bleach Library | Sanitize HTML content | Content processing |

This document focuses on the **dual-layer access control system** (Import Guard + Access Guard), which enforces the MCP-first architecture.

---

## Dual-Layer Access Control

TBCV enforces architectural boundaries through two complementary access control mechanisms that work together to prevent unauthorized access to business logic.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interfaces                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  CLI Layer   │  │  API Layer   │  │  Dashboard   │      │
│  │  (cli/*)     │  │  (api/*)     │  │  (api/*)     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
        │                   │                   │
        │  ❌ BLOCKED      │  ❌ BLOCKED      │  ❌ BLOCKED
        ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│            🛡️ Dual-Layer Access Control 🛡️                  │
│                                                               │
│  Layer 1: Import-Time Guard (sys.meta_path hook)            │
│  ├─ Intercepts: import agents.orchestrator                  │
│  ├─ Checks: Is importer in blocked list?                    │
│  └─ Action: Block import or allow based on policy           │
│                                                               │
│  Layer 2: Runtime Access Guard (@guarded_operation)         │
│  ├─ Intercepts: Function execution                          │
│  ├─ Checks: Stack inspection for caller context             │
│  └─ Action: Block execution or allow based on policy        │
│                                                               │
└─────────────────────────────────────────────────────────────┘
        │                   │                   │
        │  ✅ ALLOWED      │  ✅ ALLOWED      │  ✅ ALLOWED
        ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│                     MCP Server Layer                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  MCP Server (svc/mcp_server.py)                      │   │
│  │  MCP Methods (svc/mcp_methods/*)                     │   │
│  │  MCP Client (svc/mcp_client.py)                      │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
        │                   │                   │
        ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│                 Business Logic (Protected)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Orchestrator │  │ Truth Manager│  │ Validators   │      │
│  │ Agent        │  │ Agent        │  │ (agents/*)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### Why Dual Layers?

**Import-Time Guard** catches violations early:
- Prevents module imports before they happen
- Detects architectural violations during startup
- Provides immediate feedback to developers
- Catches violations in static code paths

**Runtime Access Guard** provides fine-grained control:
- Protects individual functions with decorators
- Inspects call stack at execution time
- Handles dynamic code paths
- Provides detailed violation context

Together, these layers provide **comprehensive protection** that catches violations whether they occur during import or execution.

### Enforcement Modes

Both guards support three enforcement modes:

| Mode | Behavior | Use Case |
|------|----------|----------|
| **DISABLED** | No enforcement, all access allowed | Local development, debugging |
| **WARN** | Log violations but allow access | Gradual rollout, monitoring |
| **BLOCK** | Log violations and raise errors | Production, strict enforcement |

---

## Runtime Access Guard

The runtime access guard (`core/access_guard.py`) protects business logic functions from direct access by CLI and API layers through a decorator-based approach with stack inspection.

### How It Works

1. **Decorator Application**: Functions are marked with `@guarded_operation`
2. **Stack Inspection**: When called, the guard inspects the call stack
3. **Caller Identification**: Determines which module/file initiated the call
4. **Policy Enforcement**: Allows or blocks based on caller identity
5. **Violation Logging**: Records all violations with full context

### Stack Inspection Algorithm

```python
def check_caller_allowed(frame_depth: int = 5) -> Tuple[bool, str]:
    """
    Walk the call stack to determine if the caller is allowed.

    Algorithm:
    1. Get call stack using inspect.stack()
    2. Iterate through frames (up to frame_depth)
    3. For each frame:
       - Extract filename, function name, line number
       - Normalize path separators for cross-platform compatibility
       - Check against allowed patterns (MCP layer, tests)
       - Check against blocked patterns (API, CLI)
    4. Return (is_allowed, caller_info)

    Allowed callers:
    - /svc/mcp_server.py - MCP server
    - /svc/mcp_methods/ - MCP method implementations
    - /svc/mcp_client.py - MCP client wrapper
    - /tests/ - Test code

    Blocked callers:
    - /api/server.py - API endpoints
    - /api/dashboard.py - Dashboard routes
    - /api/export_endpoints.py - Export endpoints
    - /cli/main.py - CLI commands
    """
```

### Decorator Usage

#### Basic Function Protection

```python
from core.access_guard import guarded_operation

@guarded_operation
def validate_content(file_path: str, content: str) -> ValidationResult:
    """
    Validate content against rules and truth data.

    This function can only be called from:
    - MCP Server (svc/mcp_server.py)
    - MCP Methods (svc/mcp_methods/*)
    - Tests (tests/*)

    Direct calls from API or CLI will be blocked.
    """
    # Business logic here
    return ValidationResult(status="pass", issues=[])
```

#### Class Method Protection

```python
from core.access_guard import guarded_operation

class ContentValidator:
    @guarded_operation
    def validate(self, content: str) -> bool:
        """Protected method - MCP access only"""
        return self._perform_validation(content)

    def _perform_validation(self, content: str) -> bool:
        """Private method - no guard needed (called internally)"""
        return True
```

#### Async Function Protection

```python
from core.access_guard import guarded_operation

@guarded_operation
async def validate_directory(directory_path: str) -> List[ValidationResult]:
    """Async function with access guard"""
    results = []
    for file in get_markdown_files(directory_path):
        result = await validate_file(file)
        results.append(result)
    return results
```

### Configuration

#### Setting Enforcement Mode

**Method 1: Environment Variable**

```bash
# Set via environment variable (recommended for production)
export TBCV_ACCESS_GUARD_MODE=block

# Start application
python main.py --mode api
```

**Method 2: Code Configuration**

```python
from core.access_guard import set_enforcement_mode, EnforcementMode

# Set during application startup
set_enforcement_mode(EnforcementMode.BLOCK)
# or
set_enforcement_mode("block")  # String also accepted
```

**Method 3: Configuration File**

```yaml
# config/access_guards.yaml
enforcement_mode: block  # disabled, warn, or block
```

#### Checking Current Mode

```python
from core.access_guard import get_enforcement_mode

current_mode = get_enforcement_mode()
print(f"Current enforcement mode: {current_mode.value}")
```

### Violation Tracking

The access guard tracks all violations for monitoring and auditing.

#### Get Violation Statistics

```python
from core.access_guard import get_statistics

stats = get_statistics()
print(f"Enforcement mode: {stats['mode']}")
print(f"Total violations: {stats['violation_count']}")
print(f"Recent violations: {len(stats['recent_violations'])}")

# Example output:
# {
#   "mode": "warn",
#   "violation_count": 42,
#   "recent_violations": [
#     {
#       "timestamp": "2025-12-03T10:30:45.123456Z",
#       "function_name": "agents.orchestrator.validate_file",
#       "caller_info": "API endpoint: /api/server.py:145 (validate_endpoint)",
#       "mode": "warn",
#       "violation_number": 42
#     }
#   ]
# }
```

#### Reset Statistics

```python
from core.access_guard import reset_statistics

# Reset violation counters (useful for testing)
reset_statistics()
```

### Exception Handling

When a violation occurs in BLOCK mode, an `AccessGuardError` is raised:

```python
from core.access_guard import AccessGuardError, guarded_operation

@guarded_operation
def protected_function():
    return "success"

# In API endpoint (BLOCKED)
try:
    result = protected_function()
except AccessGuardError as e:
    print(f"Function: {e.function_name}")
    print(f"Caller: {e.caller_info}")
    print(f"Message: {e.message}")
    # Log error and return appropriate HTTP response
    return JSONResponse(
        status_code=403,
        content={"error": "Direct access not allowed. Use MCP client."}
    )
```

### Checking if Function is Guarded

```python
from core.access_guard import is_guarded

@guarded_operation
def protected():
    pass

def unprotected():
    pass

# Check protection status
assert is_guarded(protected) == True
assert is_guarded(unprotected) == False

# Use in introspection/documentation tools
def list_protected_functions(module):
    for name, obj in inspect.getmembers(module):
        if callable(obj) and is_guarded(obj):
            print(f"Protected: {name}")
```

### Complete Example: Correct vs Incorrect Usage

#### Incorrect: Direct Access (BLOCKED)

```python
# In api/server.py (API endpoint)
from agents.orchestrator import OrchestratorAgent
from core.access_guard import set_enforcement_mode, EnforcementMode

# Set to BLOCK mode
set_enforcement_mode(EnforcementMode.BLOCK)

@app.post("/validate")
async def validate_endpoint(request: ValidationRequest):
    orchestrator = OrchestratorAgent()

    # ❌ This will raise AccessGuardError
    try:
        result = await orchestrator.validate_file(
            file_path=request.file_path,
            content=request.content,
            family=request.family
        )
    except AccessGuardError as e:
        # Violation logged:
        # Access guard violation (BLOCKED)
        # Function: agents.orchestrator.OrchestratorAgent.validate_file
        # Caller: API endpoint: api/server.py:42 (validate_endpoint)
        return JSONResponse(
            status_code=403,
            content={"error": str(e)}
        )
```

#### Correct: MCP Client Access (ALLOWED)

```python
# In api/server.py (API endpoint)
from svc.mcp_client import MCPClient
from core.access_guard import set_enforcement_mode, EnforcementMode

# Set to BLOCK mode
set_enforcement_mode(EnforcementMode.BLOCK)

@app.post("/validate")
async def validate_endpoint(request: ValidationRequest):
    # ✅ Use MCP client instead
    mcp_client = MCPClient()

    # This goes through MCP layer (ALLOWED)
    result = await mcp_client.call_tool(
        tool_name="validate_file",
        arguments={
            "file_path": request.file_path,
            "content": request.content,
            "family": request.family
        }
    )

    return JSONResponse(content=result)
```

---

## Import-Time Guard

The import-time guard (`core/import_guard.py`) prevents unauthorized modules from importing protected business logic modules using Python's `sys.meta_path` hook mechanism.

### How It Works

1. **Meta Path Hook**: Custom finder inserted at position 0 in `sys.meta_path`
2. **Import Interception**: Python's import system calls our finder first
3. **Protection Check**: Finder checks if target module is protected
4. **Caller Identification**: Inspects stack to identify importing module
5. **Policy Enforcement**: Blocks or allows import based on policy
6. **Passthrough**: Returns None to let import continue normally (if allowed)

### Python Import System Integration

```
┌─────────────────────────────────────────────────────────┐
│  Python Import Statement: import agents.orchestrator    │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  sys.meta_path[0]: ImportGuardFinder                    │
│  ├─ find_spec("agents.orchestrator", ...)              │
│  ├─ Check if "agents.orchestrator" is protected        │
│  ├─ Get importer module from stack                     │
│  ├─ Check if importer is allowed/blocked               │
│  └─ Return None (continue) or raise ImportGuardError   │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  sys.meta_path[1..n]: Standard import finders           │
│  (Continue normal import process if guard allowed)      │
└─────────────────────────────────────────────────────────┘
```

### Protected Modules

Default protected modules (defined in `core/import_guard.py`):

```python
PROTECTED_MODULES = {
    "agents.orchestrator",
    "agents.content_validator",
    "agents.content_enhancer",
    "agents.recommendation_agent",
    "agents.truth_manager",
    "agents.validators",
    "core.validation_store",
}
```

### Allowed Importers

Modules allowed to import protected modules:

```python
ALLOWED_IMPORTERS = {
    "svc.mcp_server",     # MCP server
    "svc.mcp_methods",    # MCP method implementations
    "tests",              # Test code
}
```

### Blocked Importers

Modules explicitly blocked from importing protected modules:

```python
BLOCKED_IMPORTERS = {
    "api",   # API endpoints
    "cli",   # CLI commands
}
```

### Installation

The import guard must be installed **early in application startup**, before any protected modules are imported.

#### Installation in main.py

```python
# main.py - Application entry point
from core.import_guard import install_import_guards, set_enforcement_mode, EnforcementMode

def main():
    # Install import guards FIRST (before any other imports)
    install_import_guards()
    set_enforcement_mode(EnforcementMode.BLOCK)

    # Now it's safe to import other modules
    from api.server import app
    from core.database import db_manager

    # Continue startup...
    db_manager.initialize_database()
    uvicorn.run(app, host="0.0.0.0", port=8080)

if __name__ == "__main__":
    main()
```

#### Checking Installation Status

```python
from core.import_guard import is_installed

if is_installed():
    print("Import guards are active")
else:
    print("Import guards not installed")
```

#### Uninstallation

```python
from core.import_guard import uninstall_import_guards

# Remove import guards (for testing or shutdown)
uninstall_import_guards()
```

### Configuration

#### Setting Enforcement Mode

```python
from core.import_guard import set_enforcement_mode, EnforcementMode

# Set enforcement mode
set_enforcement_mode(EnforcementMode.BLOCK)
# or
set_enforcement_mode(EnforcementMode.WARN)
# or
set_enforcement_mode(EnforcementMode.DISABLED)
```

#### Dynamically Managing Protected Modules

```python
from core.import_guard import (
    add_protected_module,
    remove_protected_module,
    add_allowed_importer,
    add_blocked_importer
)

# Add custom protected module
add_protected_module("custom.business_logic")

# Add exception for specific module
add_allowed_importer("custom.trusted_client")

# Block additional modules
add_blocked_importer("external.untrusted")

# Remove protection (if needed)
remove_protected_module("custom.business_logic")
```

#### Getting Current Configuration

```python
from core.import_guard import get_configuration

config = get_configuration()
print(config)

# Example output:
# {
#   "enforcement_mode": "block",
#   "installed": true,
#   "protected_modules": [
#     "agents.content_enhancer",
#     "agents.content_validator",
#     "agents.orchestrator",
#     "agents.recommendation_agent",
#     "agents.truth_manager",
#     "agents.validators",
#     "core.validation_store"
#   ],
#   "allowed_importers": ["svc.mcp_methods", "svc.mcp_server", "tests"],
#   "blocked_importers": ["api", "cli"]
# }
```

### Exception Handling

When a blocked import is attempted in BLOCK mode, an `ImportGuardError` is raised:

```python
from core.import_guard import ImportGuardError

# In api/server.py (BLOCKED)
try:
    from agents.orchestrator import OrchestratorAgent  # ❌ Blocked
except ImportGuardError as e:
    print(f"Import blocked: {e}")
    # Import blocked: 'api' attempted to import protected module
    # 'agents.orchestrator'. Reason: importer 'api' is explicitly blocked
```

### Complete Example: Correct vs Incorrect Usage

#### Incorrect: Direct Import in API (BLOCKED)

```python
# api/server.py
from fastapi import FastAPI
from core.import_guard import install_import_guards, set_enforcement_mode, EnforcementMode

# Install guards first
install_import_guards()
set_enforcement_mode(EnforcementMode.BLOCK)

# ❌ This import will raise ImportGuardError
try:
    from agents.orchestrator import OrchestratorAgent
except ImportGuardError as e:
    print(f"Cannot import: {e}")
    # Log error and exit or use alternative approach
```

#### Correct: Import in MCP Layer (ALLOWED)

```python
# svc/mcp_server.py
from core.import_guard import install_import_guards, set_enforcement_mode, EnforcementMode

# Install guards first
install_import_guards()
set_enforcement_mode(EnforcementMode.BLOCK)

# ✅ This import is ALLOWED (MCP layer)
from agents.orchestrator import OrchestratorAgent
from agents.truth_manager import TruthManagerAgent

class MCPServer:
    def __init__(self):
        self.orchestrator = OrchestratorAgent()
        self.truth_manager = TruthManagerAgent()

    async def handle_request(self, method: str, params: dict):
        if method == "validate_file":
            return await self.orchestrator.validate_file(**params)
        # ...
```

---

## Configuration

The dual-layer access control system is configured through `config/access_guards.yaml`.

### Complete Configuration File

```yaml
# config/access_guards.yaml
# Access Guards Configuration
# Controls access to protected modules from different callers

enforcement_mode: warn  # disabled, warn, or block

# Modules that are protected by access guards
protected_modules:
  - agents.orchestrator
  - agents.content_validator
  - agents.content_enhancer
  - agents.recommendation_agent
  - agents.truth_manager
  - agents.validators
  - core.validation_store
  - core.database

# Callers that are allowed to access protected modules
allowed_callers:
  - svc.mcp_server
  - svc.mcp_methods
  - tests

# Callers that are explicitly blocked
blocked_callers:
  - api
  - cli

# Violation logging settings
logging:
  log_violations: true
  log_level: WARNING
  include_stack_trace: true

# Performance monitoring
performance:
  track_overhead: true
  max_overhead_ms: 1.0  # Maximum acceptable overhead in milliseconds
```

### Configuration Loading

```python
# Load configuration from YAML
from core.config_loader import load_config
from core.access_guard import set_enforcement_mode
from core.import_guard import install_import_guards

def initialize_access_guards():
    config = load_config("config/access_guards.yaml")

    # Set enforcement mode for both guards
    mode = config.get("enforcement_mode", "warn")
    set_enforcement_mode(mode)  # Runtime guard

    # Install import guard
    install_import_guards()

    # Import guard uses same mode
    from core.import_guard import set_enforcement_mode as set_import_mode
    set_import_mode(mode)
```

### Environment-Based Configuration

Different enforcement modes for different environments:

```bash
# Development - Disabled or Warn
export TBCV_ACCESS_GUARD_MODE=disabled

# Staging - Warn mode for monitoring
export TBCV_ACCESS_GUARD_MODE=warn

# Production - Block mode for strict enforcement
export TBCV_ACCESS_GUARD_MODE=block
```

### Migration Path: DISABLED → WARN → BLOCK

**Phase 1: DISABLED (Development)**
```bash
export TBCV_ACCESS_GUARD_MODE=disabled
# No enforcement, all access allowed
# Focus on feature development
```

**Phase 2: WARN (Staging)**
```bash
export TBCV_ACCESS_GUARD_MODE=warn
# Log violations but allow access
# Monitor logs for violation patterns
# Fix architectural violations
```

**Phase 3: BLOCK (Production)**
```bash
export TBCV_ACCESS_GUARD_MODE=block
# Strict enforcement
# All violations blocked
# Clean architecture enforced
```

---

## Path Validation

TBCV includes path validation utilities to prevent directory traversal attacks and ensure file operations stay within allowed boundaries.

### Directory Traversal Prevention

```python
from core.file_utils import validate_path, is_safe_path

# Validate path is safe
try:
    safe_path = validate_path("/content/docs/tutorial.md", base_dir="/content")
    # Returns normalized absolute path
except ValueError as e:
    print(f"Invalid path: {e}")

# Check if path is safe (boolean check)
if is_safe_path("/content/docs/tutorial.md", base_dir="/content"):
    # Safe to use
    with open(path, "r") as f:
        content = f.read()
```

### Blocked Path Patterns

```python
# These paths are automatically rejected:
# - Paths containing ".." (directory traversal)
# - Absolute paths outside base_dir
# - System directories (/etc, /sys, /proc, C:\Windows, etc.)
# - Hidden directories starting with "."

dangerous_paths = [
    "../../../etc/passwd",        # Directory traversal
    "/etc/passwd",                 # System directory
    "content/.git/config",         # Hidden directory
    "C:\\Windows\\System32\\",     # Windows system directory
]

for path in dangerous_paths:
    try:
        validate_path(path, base_dir="/content")
    except ValueError as e:
        print(f"Blocked: {path} - {e}")
```

### Safe File Operations

```python
from core.file_utils import safe_read_file, safe_write_file

# Safe read with path validation
content = safe_read_file(
    file_path="docs/tutorial.md",
    base_dir="/content",
    max_size_mb=10
)

# Safe write with path validation and atomic operations
safe_write_file(
    file_path="docs/tutorial.md",
    content="# Updated content",
    base_dir="/content",
    create_backup=True
)
```

---

## Best Practices

### When to Use Access Guards

**✅ DO Use Access Guards For:**

1. **Business Logic Functions**
   - Orchestration and workflow coordination
   - Content validation logic
   - Truth data management
   - Recommendation generation

2. **Data Access Functions**
   - Database queries that access sensitive data
   - Cache operations
   - File system operations

3. **Critical Operations**
   - Content enhancement and modification
   - Batch processing
   - Workflow checkpointing

**❌ DON'T Use Access Guards For:**

1. **Utility Functions**
   - String formatting
   - Date/time utilities
   - Logging helpers

2. **Internal Functions**
   - Private methods (prefixed with `_`)
   - Functions only called within protected modules

3. **MCP Layer Functions**
   - MCP server methods (already enforcing boundary)
   - MCP client wrapper functions

### Adding New Protected Modules

```python
# Step 1: Identify module to protect
# Example: agents.new_agent

# Step 2: Add to import guard protected list
from core.import_guard import add_protected_module
add_protected_module("agents.new_agent")

# Step 3: Add @guarded_operation decorator to public methods
from core.access_guard import guarded_operation

class NewAgent:
    @guarded_operation
    def process_request(self, method: str, params: dict):
        """Protected entry point"""
        return self._handle_request(method, params)

    def _handle_request(self, method: str, params: dict):
        """Private method - no guard needed"""
        pass
```

### Debugging Violations

**Enable Debug Logging:**

```python
# In main.py or test setup
import logging
from core.logging import setup_logging

# Enable debug logging for access guards
setup_logging(level=logging.DEBUG)

# Now violations will show full stack traces
```

**Check Violation Statistics:**

```python
from core.access_guard import get_statistics

stats = get_statistics()
for violation in stats['recent_violations']:
    print(f"Function: {violation['function_name']}")
    print(f"Caller: {violation['caller_info']}")
    print(f"Time: {violation['timestamp']}")
    print("---")
```

**Test Access Guard in Isolation:**

```python
# Create test file: test_access_guard.py
from core.access_guard import guarded_operation, set_enforcement_mode, EnforcementMode

set_enforcement_mode(EnforcementMode.WARN)

@guarded_operation
def test_function():
    return "success"

# Call and check logs
result = test_function()  # Will log warning if called from blocked context
```

### Performance Considerations

**Access Guard Overhead:**
- Stack inspection: ~0.1-0.5ms per call
- Minimal impact on overall request latency
- Negligible compared to business logic execution

**Import Guard Overhead:**
- One-time check during import
- No runtime performance impact
- Import-time cost is amortized over application lifetime

**Optimization Tips:**
1. Don't over-use guards on frequently-called internal functions
2. Use guards on entry points, not every function in call chain
3. Keep frame_depth reasonable (default: 5 frames)

### Testing with Access Guards

**Approach 1: Disable Guards in Tests**

```python
# conftest.py (pytest)
import pytest
from core.access_guard import set_enforcement_mode, EnforcementMode

@pytest.fixture(autouse=True)
def disable_access_guards():
    """Disable access guards for all tests"""
    set_enforcement_mode(EnforcementMode.DISABLED)
    yield
    # Restore after test if needed
```

**Approach 2: Test Guards Explicitly**

```python
# test_access_control.py
import pytest
from core.access_guard import (
    guarded_operation,
    set_enforcement_mode,
    EnforcementMode,
    AccessGuardError
)

def test_access_guard_blocks_violations():
    set_enforcement_mode(EnforcementMode.BLOCK)

    @guarded_operation
    def protected():
        return "success"

    # This test is in /tests/ so it's ALLOWED
    result = protected()
    assert result == "success"

def test_access_guard_in_warn_mode():
    set_enforcement_mode(EnforcementMode.WARN)

    @guarded_operation
    def protected():
        return "success"

    # Should work in warn mode
    result = protected()
    assert result == "success"
```

---

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: ImportGuardError on Application Startup

**Symptom:**
```
ImportGuardError: 'api' attempted to import protected module 'agents.orchestrator'
```

**Cause:** API or CLI layer importing protected modules directly

**Solution:**
```python
# ❌ WRONG - Direct import in api/server.py
from agents.orchestrator import OrchestratorAgent

# ✅ CORRECT - Use MCP client
from svc.mcp_client import MCPClient
mcp_client = MCPClient()
result = await mcp_client.call_tool("validate_file", params)
```

#### Issue 2: AccessGuardError During Runtime

**Symptom:**
```
AccessGuardError: Direct access to 'agents.orchestrator.validate_file' not allowed.
Caller: API endpoint: api/server.py:145
```

**Cause:** Direct function call from blocked context

**Solution:**
```python
# ❌ WRONG - Direct call in API endpoint
result = await orchestrator.validate_file(path, content, family)

# ✅ CORRECT - Use MCP client
result = await mcp_client.call_tool("validate_file", {
    "file_path": path,
    "content": content,
    "family": family
})
```

#### Issue 3: Guards Not Enforcing (Still in DISABLED Mode)

**Symptom:** No violations logged even though architecture is being violated

**Cause:** Enforcement mode not set or stuck in DISABLED

**Solution:**
```python
# Check current mode
from core.access_guard import get_enforcement_mode
print(f"Current mode: {get_enforcement_mode()}")

# Set to WARN or BLOCK
from core.access_guard import set_enforcement_mode, EnforcementMode
set_enforcement_mode(EnforcementMode.WARN)
```

#### Issue 4: Import Guard Installed Too Late

**Symptom:** Protected modules already imported before guard installed

**Cause:** Import guard not installed early enough in startup sequence

**Solution:**
```python
# main.py - MUST be first thing in main()
def main():
    # 1. Install import guards FIRST
    from core.import_guard import install_import_guards
    install_import_guards()

    # 2. Set enforcement mode
    from core.access_guard import set_enforcement_mode
    set_enforcement_mode("block")

    # 3. NOW safe to import other modules
    from api.server import app
    from core.database import db_manager
```

#### Issue 5: Tests Failing Due to Access Guards

**Symptom:** Tests fail with AccessGuardError in BLOCK mode

**Cause:** Tests trying to call protected functions directly

**Solution:**
```python
# Option 1: Disable guards for tests (conftest.py)
@pytest.fixture(autouse=True)
def disable_guards():
    from core.access_guard import set_enforcement_mode, EnforcementMode
    set_enforcement_mode(EnforcementMode.DISABLED)

# Option 2: Tests are ALLOWED by default (in /tests/ directory)
# Ensure test file is in tests/ directory, not elsewhere
```

#### Issue 6: High Performance Overhead

**Symptom:** Requests are slow, profiling shows time in access guard

**Cause:** Too many guards on frequently-called functions

**Solution:**
```python
# ❌ WRONG - Guard on internal helper
@guarded_operation
def _normalize_text(text: str) -> str:  # Called 1000s of times
    return text.strip().lower()

# ✅ CORRECT - Guard on entry point only
@guarded_operation
def validate_content(content: str) -> ValidationResult:  # Entry point
    normalized = _normalize_text(content)  # No guard needed (internal)
    return self._perform_validation(normalized)
```

### Debugging Steps

**Step 1: Enable Debug Logging**

```bash
# Set log level
export TBCV_LOG_LEVEL=DEBUG

# Start application
python main.py --mode api
```

**Step 2: Check Guard Status**

```python
# Check both guards are installed and configured
from core.access_guard import get_enforcement_mode, get_statistics
from core.import_guard import is_installed, get_configuration

print(f"Runtime Guard Mode: {get_enforcement_mode()}")
print(f"Runtime Guard Stats: {get_statistics()}")
print(f"Import Guard Installed: {is_installed()}")
print(f"Import Guard Config: {get_configuration()}")
```

**Step 3: Review Recent Violations**

```python
from core.access_guard import get_statistics

stats = get_statistics()
print(f"Total violations: {stats['violation_count']}")

# Review last 10 violations
for v in stats['recent_violations'][-10:]:
    print(f"{v['timestamp']}: {v['function_name']} called by {v['caller_info']}")
```

**Step 4: Test in Isolation**

```python
# Create minimal test case
from core.access_guard import guarded_operation, set_enforcement_mode, EnforcementMode

set_enforcement_mode(EnforcementMode.WARN)

@guarded_operation
def test():
    return "ok"

result = test()  # Check logs for violation
print(f"Result: {result}")
```

---

## Security Audit

### Regular Security Checks

**Weekly Checks:**
1. Review violation statistics
2. Check enforcement mode in each environment
3. Verify no unauthorized access patterns

```bash
# Generate security report
curl http://localhost:8080/admin/security-report

# Review violations
curl http://localhost:8080/admin/access-violations?days=7
```

**Monthly Audits:**
1. Review and update protected modules list
2. Audit allowed/blocked importers
3. Review access guard coverage (% of agents protected)
4. Performance impact assessment

### Security Metrics

Track these KPIs:

| Metric | Target | Critical Threshold |
|--------|--------|-------------------|
| Violations per day | 0 | > 10 |
| Access guard coverage | 100% of agents | < 80% |
| Guard overhead | < 1ms per call | > 5ms |
| Enforcement mode (prod) | BLOCK | WARN or DISABLED |

### Security Testing

**Test Coverage Required:**
1. Test each guard mode (DISABLED, WARN, BLOCK)
2. Test allowed caller scenarios
3. Test blocked caller scenarios
4. Test import guard installation/uninstallation
5. Test violation logging and statistics
6. Test error handling

See `tests/test_access_guard.py` and `tests/test_import_guard.py` for examples.

---

## Related Documentation

- [Architecture](architecture.md) - System architecture overview
- [Agents](agents.md) - Agent reference documentation
- [Configuration](configuration.md) - System configuration
- [Development](development.md) - Development guide
- [Troubleshooting](troubleshooting.md) - General troubleshooting

---

## Appendix: Complete Code Examples

### Example 1: Setting Up Access Guards in New Application

```python
# main.py
from core.import_guard import install_import_guards, set_enforcement_mode as set_import_mode
from core.access_guard import set_enforcement_mode, EnforcementMode
from core.logging import setup_logging
import sys

def main():
    # Step 1: Setup logging first
    setup_logging()

    # Step 2: Install import guards (before any protected imports)
    install_import_guards()

    # Step 3: Configure enforcement based on environment
    env = sys.argv[1] if len(sys.argv) > 1 else "dev"

    if env == "prod":
        mode = EnforcementMode.BLOCK
    elif env == "staging":
        mode = EnforcementMode.WARN
    else:
        mode = EnforcementMode.DISABLED

    set_enforcement_mode(mode)
    set_import_mode(mode)

    # Step 4: Now safe to import and start application
    from api.server import app
    import uvicorn

    print(f"Starting TBCV with access guards in {mode.value} mode")
    uvicorn.run(app, host="0.0.0.0", port=8080)

if __name__ == "__main__":
    main()
```

### Example 2: Protecting a New Agent

```python
# agents/my_new_agent.py
from core.access_guard import guarded_operation
from agents.base import BaseAgent

class MyNewAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_id="my_new_agent")

    @guarded_operation
    async def process_request(self, method: str, params: dict) -> dict:
        """
        Main entry point - protected by access guard.
        Can only be called from MCP layer or tests.
        """
        if method == "analyze":
            return await self._analyze(params)
        raise ValueError(f"Unknown method: {method}")

    async def _analyze(self, params: dict) -> dict:
        """
        Internal method - no guard needed.
        Called only from within this class.
        """
        # Implementation
        return {"result": "success"}
```

### Example 3: MCP Client Usage Pattern

```python
# api/server.py (API layer)
from fastapi import FastAPI, HTTPException
from svc.mcp_client import MCPClient
from pydantic import BaseModel

app = FastAPI()
mcp_client = MCPClient()

class ValidationRequest(BaseModel):
    file_path: str
    content: str
    family: str

@app.post("/validate")
async def validate(request: ValidationRequest):
    """
    Correct pattern: Use MCP client to access business logic.
    This respects the access guard architecture.
    """
    try:
        result = await mcp_client.call_tool(
            tool_name="validate_file",
            arguments={
                "file_path": request.file_path,
                "content": request.content,
                "family": request.family
            }
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

**Document Version:** 1.0.0
**Last Updated:** 2025-12-03
**Status:** Complete
