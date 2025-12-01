"""
Demonstration of the Access Guard runtime enforcement system.

This example shows how to use the access guard to enforce architectural boundaries
in the TBCV system, preventing direct access to business logic from API/CLI layers.

Run this script to see the access guard in action:
    python examples/access_guard_demo.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.access_guard import (
    guarded_operation,
    set_enforcement_mode,
    get_enforcement_mode,
    EnforcementMode,
    AccessGuardError,
    get_statistics,
    reset_statistics
)
from core.logging import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger("access_guard_demo")


# Example 1: Protected business logic
@guarded_operation
def validate_content(file_path: str) -> dict:
    """Example business logic function that should only be called via MCP."""
    logger.info(f"Validating content", file_path=file_path)
    return {
        "file_path": file_path,
        "valid": True,
        "issues": []
    }


@guarded_operation
def process_workflow(workflow_id: str) -> dict:
    """Example workflow processing that should go through MCP."""
    logger.info(f"Processing workflow", workflow_id=workflow_id)
    return {
        "workflow_id": workflow_id,
        "status": "completed"
    }


# Example 2: Simulated API endpoint (blocked caller)
def api_endpoint_validate(file_path: str):
    """Simulated API endpoint that tries to call business logic directly."""
    logger.info("API endpoint called", file_path=file_path)

    # This will be blocked if enforcement is enabled
    return validate_content(file_path)


# Example 3: Simulated MCP method (allowed caller)
def mcp_method_validate(file_path: str):
    """Simulated MCP method that can call business logic."""
    logger.info("MCP method called", file_path=file_path)

    # This will be allowed
    return validate_content(file_path)


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def demo_disabled_mode():
    """Demonstrate DISABLED mode - all access allowed."""
    print_section("Demo 1: DISABLED Mode")

    set_enforcement_mode(EnforcementMode.DISABLED)
    reset_statistics()

    print(f"Current mode: {get_enforcement_mode().value}")
    print("In DISABLED mode, all access is allowed.\n")

    # Direct call from anywhere
    result = validate_content("test.md")
    print(f"Direct call result: {result}\n")

    stats = get_statistics()
    print(f"Violations: {stats['violation_count']}")


def demo_warn_mode():
    """Demonstrate WARN mode - log violations but allow access."""
    print_section("Demo 2: WARN Mode")

    set_enforcement_mode(EnforcementMode.WARN)
    reset_statistics()

    print(f"Current mode: {get_enforcement_mode().value}")
    print("In WARN mode, violations are logged but execution continues.\n")

    # This will log a warning (we're calling from demo script, not test/MCP)
    result = validate_content("test.md")
    print(f"Call succeeded despite violation: {result}\n")

    stats = get_statistics()
    print(f"Violations logged: {stats['violation_count']}")

    if stats['recent_violations']:
        violation = stats['recent_violations'][0]
        print(f"Latest violation:")
        print(f"  Function: {violation['function_name']}")
        print(f"  Caller: {violation['caller_info']}")


def demo_block_mode():
    """Demonstrate BLOCK mode - prevent unauthorized access."""
    print_section("Demo 3: BLOCK Mode")

    set_enforcement_mode(EnforcementMode.BLOCK)
    reset_statistics()

    print(f"Current mode: {get_enforcement_mode().value}")
    print("In BLOCK mode, unauthorized access raises AccessGuardError.\n")

    print("Attempting direct call to protected function...")
    try:
        result = validate_content("test.md")
        print(f"ERROR: Call should have been blocked!")
    except AccessGuardError as e:
        print(f"[BLOCKED] Access denied as expected!")
        print(f"  Function: {e.function_name}")
        print(f"  Caller: {e.caller_info}")
        print(f"  Message: {e.message}\n")

    stats = get_statistics()
    print(f"Violations blocked: {stats['violation_count']}")


def demo_multiple_functions():
    """Demonstrate protecting multiple functions."""
    print_section("Demo 4: Multiple Protected Functions")

    set_enforcement_mode(EnforcementMode.WARN)
    reset_statistics()

    print("Calling multiple protected functions...\n")

    # Call different protected functions
    validate_content("file1.md")
    process_workflow("workflow-123")
    validate_content("file2.md")

    stats = get_statistics()
    print(f"\nTotal violations: {stats['violation_count']}")
    print(f"Protected functions called: {len(set(v['function_name'] for v in stats['recent_violations']))}")


def demo_statistics():
    """Demonstrate statistics tracking."""
    print_section("Demo 5: Statistics Tracking")

    set_enforcement_mode(EnforcementMode.WARN)
    reset_statistics()

    print("Generating multiple violations...\n")

    # Generate violations
    for i in range(5):
        validate_content(f"file{i}.md")

    stats = get_statistics()
    print(f"Statistics:")
    print(f"  Mode: {stats['mode']}")
    print(f"  Total violations: {stats['violation_count']}")
    print(f"  Recent violations tracked: {len(stats['recent_violations'])}")

    print(f"\nRecent violations:")
    for i, violation in enumerate(stats['recent_violations'][:3], 1):
        print(f"  {i}. {violation['function_name']} at {violation['timestamp']}")


def demo_configuration():
    """Demonstrate configuration options."""
    print_section("Demo 6: Configuration Options")

    print("Access guard can be configured via:\n")

    # Via enum
    print("1. Using EnforcementMode enum:")
    set_enforcement_mode(EnforcementMode.BLOCK)
    print(f"   set_enforcement_mode(EnforcementMode.BLOCK)")
    print(f"   Current: {get_enforcement_mode().value}\n")

    # Via string
    print("2. Using string (case-insensitive):")
    set_enforcement_mode("warn")
    print(f"   set_enforcement_mode('warn')")
    print(f"   Current: {get_enforcement_mode().value}\n")

    print("3. Using environment variable:")
    print(f"   export TBCV_ACCESS_GUARD_MODE=block")
    print(f"   (Set before starting the application)\n")


def demo_best_practices():
    """Show best practices for using access guard."""
    print_section("Demo 7: Best Practices")

    print("Best practices for using access guard:\n")

    print("1. Development: Use WARN mode")
    print("   - Log violations without breaking functionality")
    print("   - Identify architectural violations early")
    print("   - Good for gradual migration\n")

    print("2. Testing: Use BLOCK mode")
    print("   - Ensure tests go through proper channels")
    print("   - Catch direct access attempts in CI/CD")
    print("   - Verify architectural boundaries\n")

    print("3. Production: Use BLOCK mode")
    print("   - Enforce architectural boundaries strictly")
    print("   - Prevent accidental direct access")
    print("   - Ensure all business logic goes through MCP\n")

    print("4. Monitoring: Check statistics regularly")
    print("   - Track violation patterns")
    print("   - Identify problematic code paths")
    print("   - Measure migration progress\n")


def main():
    """Run all demonstrations."""
    print("\n" + "="*70)
    print("  ACCESS GUARD DEMONSTRATION")
    print("  Runtime enforcement of architectural boundaries")
    print("="*70)

    # Run all demos
    demo_disabled_mode()
    demo_warn_mode()
    demo_block_mode()
    demo_multiple_functions()
    demo_statistics()
    demo_configuration()
    demo_best_practices()

    print("\n" + "="*70)
    print("  DEMONSTRATION COMPLETE")
    print("="*70)
    print("\nFor more information, see:")
    print("  - core/access_guard.py (implementation)")
    print("  - tests/core/test_access_guard.py (comprehensive tests)")
    print("  - docs/mcp_integration.md (architecture documentation)")
    print()


if __name__ == "__main__":
    main()
