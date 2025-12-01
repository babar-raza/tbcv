# file: tbcv/examples/import_guard_integration.py
"""
Example: Integrating Import Guard with MCP Server

This demonstrates how to use the import guard system to protect
agent imports in a production application.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.import_guard import (
    install_import_guards,
    uninstall_import_guards,
    set_enforcement_mode,
    get_enforcement_mode,
    get_configuration,
    EnforcementMode,
    ImportGuardError,
)


def setup_import_protection(environment: str = "production") -> None:
    """
    Set up import guards based on environment.

    Args:
        environment: One of "production", "staging", "development", "test"
    """
    # Map environment to enforcement mode
    mode_map = {
        "production": EnforcementMode.BLOCK,
        "staging": EnforcementMode.WARN,
        "development": EnforcementMode.LOG,
        "test": EnforcementMode.WARN,
    }

    mode = mode_map.get(environment, EnforcementMode.DISABLED)

    # Set mode and install guards
    set_enforcement_mode(mode)
    install_import_guards()

    # Log configuration
    config = get_configuration()
    print(f"\n{'='*60}")
    print(f"Import Guard Initialized")
    print(f"{'='*60}")
    print(f"Environment:       {environment}")
    print(f"Enforcement Mode:  {config['enforcement_mode']}")
    print(f"Guards Installed:  {config['installed']}")
    print(f"Protected Modules: {len(config['protected_modules'])} modules")
    print(f"Allowed Importers: {len(config['allowed_importers'])} modules")
    print(f"Blocked Importers: {len(config['blocked_importers'])} modules")
    print(f"{'='*60}\n")


def demonstrate_blocked_import():
    """
    Demonstrate what happens when a blocked module tries to import.

    This simulates the scenario where api.server tries to import
    agents.orchestrator, which should be blocked.
    """
    print("\n" + "="*60)
    print("Demonstration: Blocked Import")
    print("="*60)

    # Set up guards in BLOCK mode
    setup_import_protection("production")

    print("\nAttempting prohibited import...")
    print("Scenario: 'api.server' tries to import 'agents.orchestrator'\n")

    # We can't actually simulate this perfectly without creating a real module,
    # but we can show the configuration that would block it
    from core.import_guard import is_import_allowed

    allowed, reason = is_import_allowed("agents.orchestrator", "api.server")

    if not allowed:
        print(f"[X] BLOCKED: Import would be blocked")
        print(f"  Reason: {reason}")
        print(f"\n  In production, this would raise:")
        print(f"  ImportGuardError: Import blocked: 'api.server' attempted to")
        print(f"  import protected module 'agents.orchestrator'")
    else:
        print(f"[OK] ALLOWED: Import would be allowed")

    # Cleanup
    uninstall_import_guards()


def demonstrate_allowed_import():
    """
    Demonstrate what happens when an allowed module imports.

    This shows that svc.mcp_server can import protected modules normally.
    """
    print("\n" + "="*60)
    print("Demonstration: Allowed Import")
    print("="*60)

    # Set up guards in BLOCK mode
    setup_import_protection("production")

    print("\nAttempting legitimate import...")
    print("Scenario: 'svc.mcp_server' tries to import 'agents.orchestrator'\n")

    from core.import_guard import is_import_allowed

    allowed, reason = is_import_allowed("agents.orchestrator", "svc.mcp_server")

    if allowed:
        print(f"[OK] ALLOWED: Import succeeds")
        print(f"  Reason: {reason}")
        print(f"\n  In production, this import would work normally:")
        print(f"  from agents.orchestrator import Orchestrator")
    else:
        print(f"[X] BLOCKED: Import would be blocked")

    # Cleanup
    uninstall_import_guards()


def demonstrate_enforcement_modes():
    """
    Demonstrate different enforcement modes.
    """
    print("\n" + "="*60)
    print("Demonstration: Enforcement Modes")
    print("="*60)

    modes = [
        (EnforcementMode.BLOCK, "Raises ImportGuardError"),
        (EnforcementMode.WARN, "Logs warning, allows import"),
        (EnforcementMode.LOG, "Logs info, allows import"),
        (EnforcementMode.DISABLED, "No enforcement"),
    ]

    for mode, description in modes:
        set_enforcement_mode(mode)
        current = get_enforcement_mode()

        print(f"\n{mode.value.upper():12} - {description}")
        print(f"{'Current mode:':15} {current.value}")


def demonstrate_configuration():
    """
    Show the current protection configuration.
    """
    print("\n" + "="*60)
    print("Demonstration: Protection Configuration")
    print("="*60)

    # Install guards
    install_import_guards()

    config = get_configuration()

    print("\nProtected Modules:")
    for module in sorted(config['protected_modules']):
        print(f"  - {module}")

    print("\nAllowed Importers:")
    for importer in sorted(config['allowed_importers']):
        print(f"  - {importer}")

    print("\nBlocked Importers:")
    for importer in sorted(config['blocked_importers']):
        print(f"  - {importer}")

    print("\n" + "="*60)
    print("Protection Rules Summary")
    print("="*60)

    test_cases = [
        ("agents.orchestrator", "svc.mcp_server"),
        ("agents.content_validator", "api.server"),
        ("agents.truth_manager", "cli.main"),
        ("core.validation_store", "tests.test_core"),
        ("os", "api.server"),
    ]

    from core.import_guard import is_import_allowed

    for target, importer in test_cases:
        allowed, reason = is_import_allowed(target, importer)
        status = "ALLOWED" if allowed else "BLOCKED"
        print(f"\n[{status:^7}] {importer:25} -> {target}")
        print(f"{'':10}Reason: {reason}")

    # Cleanup
    uninstall_import_guards()


def mcp_server_example():
    """
    Example: How to use import guards in MCP Server.

    This shows the recommended pattern for production use.
    """
    print("\n" + "="*60)
    print("Example: MCP Server Integration")
    print("="*60)

    print("""
This is how you would integrate import guards into svc/mcp_server.py:

```python
# svc/mcp_server.py
from core.import_guard import install_import_guards, set_enforcement_mode, EnforcementMode

class MCPServer:
    def __init__(self):
        # Install import guards FIRST, before any agent imports
        set_enforcement_mode(EnforcementMode.BLOCK)
        install_import_guards()

        # Now it's safe to import agents - we know we're an allowed importer
        from agents.orchestrator import Orchestrator
        from agents.content_validator import ContentValidator
        from agents.content_enhancer import ContentEnhancer
        from agents.recommendation_agent import RecommendationAgent

        # Initialize components
        self.orchestrator = Orchestrator()
        self.validator = ContentValidator()
        # ... etc
```

Key points:

1. Install guards BEFORE importing agents
2. Use BLOCK mode in production
3. Let guards stay installed for application lifetime
4. No need to uninstall (guards are lightweight)

If api/server.py tries to import agents directly:

```python
# api/server.py
from agents.orchestrator import Orchestrator  # ImportGuardError!
```

This will raise ImportGuardError, preventing the architectural violation.

The correct pattern is to use MCP client:

```python
# api/server.py
from svc.mcp_client import MCPClient

client = MCPClient()
result = await client.call("validate_content", {...})
```

This way, all agent access is centralized through the MCP server,
and import guards enforce the boundary.
""")


def main():
    """
    Run all demonstrations.
    """
    print("\n" + "="*60)
    print("Import Guard System - Integration Examples")
    print("="*60)

    # Run demonstrations
    demonstrate_blocked_import()
    demonstrate_allowed_import()
    demonstrate_enforcement_modes()
    demonstrate_configuration()
    mcp_server_example()

    print("\n" + "="*60)
    print("Demonstrations Complete")
    print("="*60)
    print("\nFor more information:")
    print("  - Implementation: core/import_guard.py")
    print("  - Tests: tests/core/test_import_guard.py")
    print("  - Documentation: docs/implementation/IMPORT_GUARD_USAGE.md")
    print("")


if __name__ == "__main__":
    main()
