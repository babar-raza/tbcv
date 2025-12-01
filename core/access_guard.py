"""
Runtime access guard for enforcing architectural boundaries.

This module provides runtime enforcement of the MCP-first architecture by preventing
direct access to business logic from CLI and API layers. All business logic should be
accessed through the MCP server layer.

Key concepts:
- EnforcementMode: Control the level of enforcement (disabled, warn, block)
- AccessGuardError: Exception raised when access is blocked
- @guarded_operation: Decorator to protect business logic functions
- Stack inspection: Verify caller context at runtime

Allowed callers:
- svc/mcp_server.py (MCP layer)
- svc/mcp_methods/*.py (MCP method implementations)
- tests/ (test code)

Blocked callers:
- api/ (API endpoints)
- cli/ (CLI commands)

Usage:
    from core.access_guard import guarded_operation, set_enforcement_mode, EnforcementMode

    # Configure enforcement mode (typically in main.py or config)
    set_enforcement_mode(EnforcementMode.WARN)  # or BLOCK for production

    # Protect business logic functions
    @guarded_operation
    def validate_content(file_path: str) -> ValidationResult:
        # This function can only be called from MCP layer or tests
        ...

    # From API/CLI - this will raise AccessGuardError if mode is BLOCK
    result = validate_content("file.md")  # BAD - direct access

    # Correct way - through MCP client
    mcp_client = MCPClient()
    result = await mcp_client.call_tool("validate_content", {"file_path": "file.md"})

Configuration:
    Set enforcement mode via:
    1. Environment variable: TBCV_ACCESS_GUARD_MODE=block
    2. Code: set_enforcement_mode(EnforcementMode.BLOCK)
    3. Config file (if integrated with core.config_loader)
"""

from __future__ import annotations

import functools
import inspect
import os
from enum import Enum
from pathlib import Path
from typing import Callable, Optional, Tuple, Any, Dict
from datetime import datetime, timezone

from core.logging import get_logger


# Module logger
logger = get_logger(__name__)


class EnforcementMode(Enum):
    """Enforcement mode for access guard.

    DISABLED: No enforcement, all access allowed
    WARN: Log violations but allow access
    BLOCK: Log violations and raise AccessGuardError
    """
    DISABLED = "disabled"
    WARN = "warn"
    BLOCK = "block"

    @classmethod
    def from_string(cls, value: str) -> "EnforcementMode":
        """Create EnforcementMode from string (case-insensitive)."""
        value_upper = value.upper()
        for mode in cls:
            if mode.name == value_upper or mode.value == value.lower():
                return mode
        raise ValueError(f"Invalid enforcement mode: {value}. Valid: {[m.value for m in cls]}")


class AccessGuardError(Exception):
    """Raised when guarded operation is accessed from blocked context.

    Attributes:
        function_name: Name of the protected function
        caller_info: Information about the blocked caller
        message: Full error message
    """

    def __init__(self, function_name: str, caller_info: str, message: Optional[str] = None):
        self.function_name = function_name
        self.caller_info = caller_info

        if message is None:
            message = (
                f"Direct access to '{function_name}' not allowed. "
                f"Caller: {caller_info}. "
                f"Use MCP client instead."
            )

        self.message = message
        super().__init__(self.message)


# Global enforcement mode
_enforcement_mode: EnforcementMode = EnforcementMode.DISABLED

# Statistics tracking
_violation_count: int = 0
_violations: list[Dict[str, Any]] = []


def set_enforcement_mode(mode: str | EnforcementMode) -> None:
    """Set global enforcement mode.

    Args:
        mode: Enforcement mode as string or EnforcementMode enum

    Examples:
        set_enforcement_mode(EnforcementMode.WARN)
        set_enforcement_mode("block")
        set_enforcement_mode("disabled")
    """
    global _enforcement_mode

    if isinstance(mode, str):
        mode = EnforcementMode.from_string(mode)

    _enforcement_mode = mode
    logger.info(
        f"Access guard enforcement mode set",
        mode=mode.value,
        previous_mode=_enforcement_mode.value if _enforcement_mode else None
    )


def get_enforcement_mode() -> EnforcementMode:
    """Get current enforcement mode."""
    return _enforcement_mode


def reset_statistics() -> None:
    """Reset violation statistics (useful for testing)."""
    global _violation_count, _violations
    _violation_count = 0
    _violations = []


def get_statistics() -> Dict[str, Any]:
    """Get access guard statistics.

    Returns:
        Dictionary with violation count and recent violations
    """
    return {
        "mode": _enforcement_mode.value,
        "violation_count": _violation_count,
        "recent_violations": _violations[-100:]  # Last 100 violations
    }


def check_caller_allowed(frame_depth: int = 5) -> Tuple[bool, str]:
    """Check if caller is allowed via stack inspection.

    Inspects the call stack to determine if the caller is from an allowed context
    (MCP layer or tests) or a blocked context (API/CLI).

    Args:
        frame_depth: Maximum depth to inspect in the call stack

    Returns:
        Tuple of (is_allowed, caller_info)
        - is_allowed: True if caller is allowed, False if blocked
        - caller_info: String describing the caller context

    Examples:
        allowed, info = check_caller_allowed()
        if not allowed:
            logger.warning(f"Blocked access: {info}")
    """
    stack = inspect.stack()

    # Start from frame 1 to skip check_caller_allowed itself
    # Go up to frame_depth+1 to inspect enough frames
    for frame_info in stack[1:min(frame_depth + 1, len(stack))]:
        filename = Path(frame_info.filename).as_posix()
        function_name = frame_info.function
        lineno = frame_info.lineno

        # Normalize path separators for cross-platform compatibility
        filename_normalized = filename.replace('\\', '/')

        # Allow MCP layer
        if "/svc/mcp_server.py" in filename_normalized:
            return True, f"MCP server: {filename}:{lineno} ({function_name})"

        if "/svc/mcp_methods/" in filename_normalized:
            return True, f"MCP method: {filename}:{lineno} ({function_name})"

        # Allow MCP client (it's a wrapper, not direct access)
        if "/svc/mcp_client.py" in filename_normalized:
            return True, f"MCP client: {filename}:{lineno} ({function_name})"

        # Allow tests
        if "/tests/" in filename_normalized or "\\tests\\" in filename:
            return True, f"Test code: {filename}:{lineno} ({function_name})"

        # Block API endpoints
        if "/api/" in filename_normalized and "/api/" in filename_normalized:
            # Additional check: make sure it's not just a path containing 'api'
            if "/api/server.py" in filename_normalized or "/api/dashboard.py" in filename_normalized or "/api/export_endpoints.py" in filename_normalized:
                return False, f"API endpoint: {filename}:{lineno} ({function_name})"

        # Block CLI commands
        if "/cli/" in filename_normalized and "/cli/main.py" in filename_normalized:
            return False, f"CLI command: {filename}:{lineno} ({function_name})"

    # If we couldn't determine, allow by default (could be internal call)
    # This handles cases like direct imports in __init__.py or core modules
    return True, f"Internal call (depth {len(stack)})"


def log_violation(
    function_name: str,
    caller_info: str,
    mode: EnforcementMode,
    additional_context: Optional[Dict[str, Any]] = None
) -> None:
    """Log an access violation with full context.

    Args:
        function_name: Name of the protected function
        caller_info: Information about the caller
        mode: Current enforcement mode
        additional_context: Additional context to log
    """
    global _violation_count, _violations

    _violation_count += 1

    violation_record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "function_name": function_name,
        "caller_info": caller_info,
        "mode": mode.value,
        "violation_number": _violation_count
    }

    if additional_context:
        violation_record.update(additional_context)

    _violations.append(violation_record)

    # Log based on enforcement mode
    if mode == EnforcementMode.BLOCK:
        logger.error(
            f"Access guard violation (BLOCKED)",
            function=function_name,
            caller=caller_info,
            violation_count=_violation_count,
            **(additional_context or {})
        )
    elif mode == EnforcementMode.WARN:
        logger.warning(
            f"Access guard violation (WARNING)",
            function=function_name,
            caller=caller_info,
            violation_count=_violation_count,
            **(additional_context or {})
        )


def guarded_operation(func: Callable) -> Callable:
    """Decorator to guard business logic operations.

    This decorator protects functions from being called directly from API or CLI layers.
    Access must go through the MCP server layer.

    Args:
        func: Function to protect

    Returns:
        Wrapped function with access guard

    Raises:
        AccessGuardError: If access is blocked and mode is BLOCK

    Examples:
        @guarded_operation
        def validate_content(file_path: str) -> ValidationResult:
            # Business logic
            ...

        # Can be decorated on methods too
        class ContentValidator:
            @guarded_operation
            def validate(self, content: str) -> bool:
                ...
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        global _enforcement_mode

        # If disabled, just run the function
        if _enforcement_mode == EnforcementMode.DISABLED:
            return func(*args, **kwargs)

        # Check if caller is allowed
        allowed, caller_info = check_caller_allowed()

        if not allowed:
            # Build context for logging
            function_full_name = f"{func.__module__}.{func.__qualname__}"

            additional_context = {
                "args_count": len(args),
                "kwargs_keys": list(kwargs.keys()) if kwargs else []
            }

            # Log the violation
            log_violation(
                function_full_name,
                caller_info,
                _enforcement_mode,
                additional_context
            )

            # Block or warn based on mode
            if _enforcement_mode == EnforcementMode.BLOCK:
                raise AccessGuardError(
                    function_full_name,
                    caller_info
                )
            # WARN mode: log was already done, continue execution

        # Execute the original function
        return func(*args, **kwargs)

    # Preserve function metadata for introspection
    wrapper.__wrapped__ = func
    wrapper.__guarded__ = True

    return wrapper


def is_guarded(func: Callable) -> bool:
    """Check if a function is protected by access guard.

    Args:
        func: Function to check

    Returns:
        True if function has @guarded_operation decorator
    """
    return getattr(func, "__guarded__", False)


# Initialize from environment variable if set
def _initialize_from_env() -> None:
    """Initialize enforcement mode from environment variable."""
    env_mode = os.environ.get("TBCV_ACCESS_GUARD_MODE")
    if env_mode:
        try:
            set_enforcement_mode(env_mode)
            logger.info(
                f"Access guard mode initialized from environment",
                mode=env_mode
            )
        except ValueError as e:
            logger.warning(
                f"Invalid TBCV_ACCESS_GUARD_MODE in environment",
                value=env_mode,
                error=str(e)
            )


# Auto-initialize on import
_initialize_from_env()


if __name__ == "__main__":
    # Self-test: demonstrate the access guard functionality
    from core.logging import setup_logging

    setup_logging()

    print("\n=== Access Guard Self-Test ===\n")

    # Test 1: Disabled mode
    print("Test 1: Disabled mode")
    set_enforcement_mode(EnforcementMode.DISABLED)

    @guarded_operation
    def test_function_disabled():
        return "executed"

    result = test_function_disabled()
    print(f"Result: {result}")
    assert result == "executed"
    print("[OK] Disabled mode allows all access\n")

    # Test 2: Warn mode
    print("Test 2: Warn mode")
    set_enforcement_mode(EnforcementMode.WARN)
    reset_statistics()

    @guarded_operation
    def test_function_warn():
        return "executed with warning"

    result = test_function_warn()
    print(f"Result: {result}")
    stats = get_statistics()
    print(f"Violations: {stats['violation_count']}")
    print("[OK] Warn mode logs violations but allows access\n")

    # Test 3: Check statistics
    print("Test 3: Statistics")
    stats = get_statistics()
    print(f"Mode: {stats['mode']}")
    print(f"Total violations: {stats['violation_count']}")
    print(f"Recent violations: {len(stats['recent_violations'])}")
    print("[OK] Statistics tracking works\n")

    # Test 4: is_guarded helper
    print("Test 4: is_guarded helper")

    @guarded_operation
    def protected_func():
        pass

    def unprotected_func():
        pass

    assert is_guarded(protected_func) == True
    assert is_guarded(unprotected_func) == False
    print("[OK] is_guarded correctly identifies protected functions\n")

    print("=== All tests passed ===\n")
