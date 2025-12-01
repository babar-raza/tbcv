# file: tbcv/tests/core/test_import_guard_demo.py
"""
Demonstration of import guard system in action.
Shows how prohibited imports are detected at import time.
"""
import sys
import pytest
from core.import_guard import (
    install_import_guards,
    uninstall_import_guards,
    set_enforcement_mode,
    get_enforcement_mode,
    EnforcementMode,
    ImportGuardError,
    get_configuration,
)


class TestImportGuardDemo:
    """Demonstration tests showing import guard behavior."""

    def setup_method(self):
        """Set up for each test."""
        # Start with guards uninstalled
        uninstall_import_guards()
        # Save original mode
        self.original_mode = get_enforcement_mode()

    def teardown_method(self):
        """Clean up after each test."""
        uninstall_import_guards()
        set_enforcement_mode(self.original_mode)

    def test_demo_block_mode_prevents_import(self):
        """
        DEMO: In BLOCK mode, prohibited imports raise ImportGuardError.

        This simulates what happens when api.server tries to import
        agents.orchestrator - the import is blocked at import time.
        """
        # Configure enforcement
        set_enforcement_mode(EnforcementMode.BLOCK)
        install_import_guards()

        # Show current configuration
        config = get_configuration()
        print("\n=== Import Guard Configuration ===")
        print(f"Enforcement Mode: {config['enforcement_mode']}")
        print(f"Installed: {config['installed']}")
        print(f"Protected Modules: {config['protected_modules'][:3]}...")
        print(f"Blocked Importers: {config['blocked_importers']}")

        # Demonstrate that the protection rules are active
        from unittest.mock import patch
        from core.import_guard import ImportGuardFinder

        finder = ImportGuardFinder()

        # Simulate api.server trying to import agents.orchestrator
        with patch.object(finder, '_get_importer_name', return_value='api.server'):
            print("\n=== Attempting Prohibited Import ===")
            print("Simulating: api.server imports agents.orchestrator")

            with pytest.raises(ImportGuardError) as exc_info:
                finder.find_module("agents.orchestrator")

            error_msg = str(exc_info.value)
            print(f"Result: ImportGuardError raised")
            print(f"Message: {error_msg}")

            assert "api.server" in error_msg
            assert "agents.orchestrator" in error_msg
            assert "blocked" in error_msg.lower()

    def test_demo_warn_mode_allows_with_warning(self, caplog):
        """
        DEMO: In WARN mode, prohibited imports are logged but allowed.

        This is useful during migration periods where you want to
        track violations without breaking the application.
        """
        set_enforcement_mode(EnforcementMode.WARN)
        install_import_guards()

        print("\n=== Warn Mode Demonstration ===")
        print("Enforcement Mode: WARN")

        from unittest.mock import patch
        from core.import_guard import ImportGuardFinder

        finder = ImportGuardFinder()

        with patch.object(finder, '_get_importer_name', return_value='cli.main'):
            print("Simulating: cli.main imports agents.truth_manager")

            # This should NOT raise an error in warn mode
            result = finder.find_module("agents.truth_manager")

            print(f"Result: Import allowed (returned {result})")
            print(f"Warning logged: {'Import blocked' in caplog.text}")

            assert result is None  # Import continues
            assert "cli.main" in caplog.text
            assert "agents.truth_manager" in caplog.text

    def test_demo_allowed_imports_work_normally(self):
        """
        DEMO: Allowed imports work normally without any interference.

        This shows that the import guard only affects prohibited
        combinations and doesn't interfere with legitimate imports.
        """
        set_enforcement_mode(EnforcementMode.BLOCK)
        install_import_guards()

        print("\n=== Allowed Import Demonstration ===")

        from unittest.mock import patch
        from core.import_guard import ImportGuardFinder

        finder = ImportGuardFinder()

        # Test 1: svc.mcp_server importing protected module (ALLOWED)
        with patch.object(finder, '_get_importer_name', return_value='svc.mcp_server'):
            print("Test 1: svc.mcp_server imports agents.content_validator")
            result = finder.find_module("agents.content_validator")
            print(f"Result: Allowed (returned {result})")
            assert result is None  # Import allowed

        # Test 2: tests importing protected module (ALLOWED)
        with patch.object(finder, '_get_importer_name', return_value='tests.test_something'):
            print("\nTest 2: tests.test_something imports agents.orchestrator")
            result = finder.find_module("agents.orchestrator")
            print(f"Result: Allowed (returned {result})")
            assert result is None  # Import allowed

        # Test 3: Any module importing unprotected module (ALLOWED)
        with patch.object(finder, '_get_importer_name', return_value='api.server'):
            print("\nTest 3: api.server imports os (unprotected)")
            result = finder.find_module("os")
            print(f"Result: Allowed (returned {result})")
            assert result is None  # Import allowed

    def test_demo_protection_coverage(self):
        """
        DEMO: Show which modules are protected and who can access them.

        This provides a clear view of the protection boundaries.
        """
        config = get_configuration()

        print("\n=== Protection Coverage ===")
        print("\nProtected Modules:")
        for module in sorted(config['protected_modules']):
            print(f"  - {module}")

        print("\nAllowed Importers:")
        for importer in sorted(config['allowed_importers']):
            print(f"  - {importer}")

        print("\nBlocked Importers:")
        for importer in sorted(config['blocked_importers']):
            print(f"  - {importer}")

        print("\n=== Example Combinations ===")

        test_cases = [
            ("agents.orchestrator", "svc.mcp_server", True),
            ("agents.content_validator", "api.server", False),
            ("agents.truth_manager", "cli.main", False),
            ("core.validation_store", "tests.test_core", True),
            ("os", "api.server", True),
            ("json", "cli.main", True),
        ]

        from core.import_guard import is_import_allowed

        for target, importer, expected in test_cases:
            allowed, reason = is_import_allowed(target, importer)
            status = "[ALLOWED]" if allowed else "[BLOCKED]"
            print(f"\n{status}: {importer} -> {target}")
            print(f"  Reason: {reason}")
            assert allowed == expected

    def test_demo_enforcement_mode_transitions(self):
        """
        DEMO: Show how enforcement modes can be changed at runtime.

        This is useful for different environments (dev, staging, prod)
        or for gradual rollout of protections.
        """
        print("\n=== Enforcement Mode Transitions ===")

        modes = [
            (EnforcementMode.DISABLED, "No enforcement - all imports allowed"),
            (EnforcementMode.LOG, "Log violations only - for monitoring"),
            (EnforcementMode.WARN, "Warn on violations - for testing"),
            (EnforcementMode.BLOCK, "Block violations - for production"),
        ]

        for mode, description in modes:
            set_enforcement_mode(mode)
            current = get_enforcement_mode()

            print(f"\n{mode.value.upper()}: {description}")
            print(f"  Current mode: {current.value}")

            assert current == mode

    def test_demo_installation_lifecycle(self):
        """
        DEMO: Show the complete lifecycle of import guard installation.

        This demonstrates how to properly install, use, and uninstall
        the import guards in an application.
        """
        print("\n=== Import Guard Lifecycle ===")

        # Step 1: Check initial state
        from core.import_guard import is_installed
        print("\n1. Initial State:")
        print(f"   Guards installed: {is_installed()}")
        assert not is_installed()

        # Step 2: Install guards
        print("\n2. Installing Guards:")
        install_import_guards()
        print(f"   Guards installed: {is_installed()}")
        print(f"   sys.meta_path entries: {len(sys.meta_path)}")
        assert is_installed()

        # Step 3: Guards are now active
        print("\n3. Guards Active:")
        print("   Protected imports are now being monitored")

        from core.import_guard import ImportGuardFinder
        has_finder = any(isinstance(f, ImportGuardFinder) for f in sys.meta_path)
        print(f"   ImportGuardFinder in sys.meta_path: {has_finder}")
        assert has_finder

        # Step 4: Uninstall guards
        print("\n4. Uninstalling Guards:")
        uninstall_import_guards()
        print(f"   Guards installed: {is_installed()}")
        assert not is_installed()

        has_finder = any(isinstance(f, ImportGuardFinder) for f in sys.meta_path)
        print(f"   ImportGuardFinder in sys.meta_path: {has_finder}")
        assert not has_finder

        print("\n5. Lifecycle Complete")


if __name__ == "__main__":
    """Run demonstrations with verbose output."""
    pytest.main([__file__, "-v", "-s"])
