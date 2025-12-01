# file: tbcv/tests/core/test_import_guard.py
"""
Tests for import-time protection system.
"""
import sys
import pytest
from unittest.mock import Mock, patch
from core.import_guard import (
    ImportGuardError,
    ImportGuardFinder,
    EnforcementMode,
    is_import_allowed,
    install_import_guards,
    uninstall_import_guards,
    is_installed,
    set_enforcement_mode,
    get_enforcement_mode,
    add_protected_module,
    remove_protected_module,
    add_allowed_importer,
    remove_allowed_importer,
    add_blocked_importer,
    remove_blocked_importer,
    get_configuration,
    PROTECTED_MODULES,
    ALLOWED_IMPORTERS,
    BLOCKED_IMPORTERS,
)


class TestImportGuardError:
    """Test ImportGuardError exception."""

    def test_is_import_error(self):
        """ImportGuardError should inherit from ImportError."""
        error = ImportGuardError("test")
        assert isinstance(error, ImportError)

    def test_error_message(self):
        """ImportGuardError should preserve error message."""
        message = "Import not allowed"
        error = ImportGuardError(message)
        assert str(error) == message


class TestIsImportAllowed:
    """Test is_import_allowed() function."""

    def test_unprotected_module_allowed(self):
        """Unprotected modules should always be allowed."""
        allowed, reason = is_import_allowed("os", "api.server")
        assert allowed is True
        assert "not protected" in reason

    def test_protected_module_from_allowed_importer(self):
        """Protected modules should be allowed from allowed importers."""
        allowed, reason = is_import_allowed(
            "agents.orchestrator",
            "svc.mcp_server"
        )
        assert allowed is True
        assert "is allowed" in reason

    def test_protected_module_from_blocked_importer(self):
        """Protected modules should be blocked from blocked importers."""
        allowed, reason = is_import_allowed(
            "agents.content_validator",
            "api.server"
        )
        assert allowed is False
        assert "explicitly blocked" in reason

    def test_protected_module_from_unknown_importer(self):
        """Protected modules should be allowed from unknown importers."""
        allowed, reason = is_import_allowed(
            "agents.truth_manager",
            None
        )
        assert allowed is True
        assert "unknown" in reason

    def test_submodule_protection(self):
        """Submodules of protected modules should be protected."""
        allowed, reason = is_import_allowed(
            "agents.validators.base_validator",
            "api.dashboard"
        )
        assert allowed is False
        assert "explicitly blocked" in reason

    def test_allowed_importer_submodule(self):
        """Submodules of allowed importers should be allowed."""
        allowed, reason = is_import_allowed(
            "agents.orchestrator",
            "svc.mcp_methods.validation"
        )
        assert allowed is True
        assert "is allowed" in reason

    def test_blocked_importer_submodule(self):
        """Submodules of blocked importers should be blocked."""
        allowed, reason = is_import_allowed(
            "core.validation_store",
            "cli.main"
        )
        assert allowed is False
        assert "explicitly blocked" in reason


class TestEnforcementMode:
    """Test enforcement mode management."""

    def test_default_mode_is_block(self):
        """Default enforcement mode should be BLOCK."""
        mode = get_enforcement_mode()
        assert mode == EnforcementMode.BLOCK

    def test_set_enforcement_mode(self):
        """Should be able to set enforcement mode."""
        original = get_enforcement_mode()
        try:
            set_enforcement_mode(EnforcementMode.WARN)
            assert get_enforcement_mode() == EnforcementMode.WARN

            set_enforcement_mode(EnforcementMode.LOG)
            assert get_enforcement_mode() == EnforcementMode.LOG

            set_enforcement_mode(EnforcementMode.DISABLED)
            assert get_enforcement_mode() == EnforcementMode.DISABLED
        finally:
            set_enforcement_mode(original)

    def test_enforcement_mode_enum_values(self):
        """Enforcement mode should have expected values."""
        assert EnforcementMode.BLOCK.value == "block"
        assert EnforcementMode.WARN.value == "warn"
        assert EnforcementMode.LOG.value == "log"
        assert EnforcementMode.DISABLED.value == "disabled"


class TestImportGuardFinder:
    """Test ImportGuardFinder meta path finder."""

    def test_finder_creation(self):
        """Should be able to create ImportGuardFinder."""
        finder = ImportGuardFinder()
        assert isinstance(finder, ImportGuardFinder)

    @patch('core.import_guard.ImportGuardFinder._get_importer_name')
    def test_find_module_allowed_import(self, mock_get_importer):
        """find_module should return None for allowed imports."""
        mock_get_importer.return_value = "svc.mcp_server"
        finder = ImportGuardFinder()

        result = finder.find_module("agents.orchestrator")
        assert result is None

    @patch('core.import_guard.ImportGuardFinder._get_importer_name')
    def test_find_module_blocked_import_block_mode(self, mock_get_importer):
        """find_module should raise ImportGuardError in BLOCK mode."""
        mock_get_importer.return_value = "api.server"
        original_mode = get_enforcement_mode()
        try:
            set_enforcement_mode(EnforcementMode.BLOCK)
            finder = ImportGuardFinder()

            with pytest.raises(ImportGuardError) as exc_info:
                finder.find_module("agents.content_validator")

            assert "api.server" in str(exc_info.value)
            assert "agents.content_validator" in str(exc_info.value)
        finally:
            set_enforcement_mode(original_mode)

    @patch('core.import_guard.ImportGuardFinder._get_importer_name')
    def test_find_module_blocked_import_warn_mode(self, mock_get_importer):
        """find_module should return None in WARN mode."""
        mock_get_importer.return_value = "cli.main"
        original_mode = get_enforcement_mode()
        try:
            set_enforcement_mode(EnforcementMode.WARN)
            finder = ImportGuardFinder()

            result = finder.find_module("agents.truth_manager")
            assert result is None
        finally:
            set_enforcement_mode(original_mode)

    @patch('core.import_guard.ImportGuardFinder._get_importer_name')
    def test_find_module_disabled_mode(self, mock_get_importer):
        """find_module should do nothing in DISABLED mode."""
        mock_get_importer.return_value = "api.server"
        original_mode = get_enforcement_mode()
        try:
            set_enforcement_mode(EnforcementMode.DISABLED)
            finder = ImportGuardFinder()

            result = finder.find_module("agents.orchestrator")
            assert result is None
        finally:
            set_enforcement_mode(original_mode)

    @patch('core.import_guard.ImportGuardFinder._get_importer_name')
    def test_find_spec_delegates_to_find_module(self, mock_get_importer):
        """find_spec should use same logic as find_module."""
        mock_get_importer.return_value = "svc.mcp_methods"
        finder = ImportGuardFinder()

        result = finder.find_spec("agents.content_enhancer")
        assert result is None


class TestInstallUninstall:
    """Test install/uninstall functions."""

    def test_install_import_guards(self):
        """Should install import guards into sys.meta_path."""
        # Make sure guards are not installed
        uninstall_import_guards()

        assert not is_installed()

        install_import_guards()
        assert is_installed()
        assert any(isinstance(f, ImportGuardFinder) for f in sys.meta_path)

        # Cleanup
        uninstall_import_guards()

    def test_uninstall_import_guards(self):
        """Should remove import guards from sys.meta_path."""
        install_import_guards()
        assert is_installed()

        uninstall_import_guards()
        assert not is_installed()
        assert not any(isinstance(f, ImportGuardFinder) for f in sys.meta_path)

    def test_double_install_warning(self, caplog):
        """Installing twice should log a warning."""
        uninstall_import_guards()

        install_import_guards()
        install_import_guards()

        assert "already installed" in caplog.text

        # Cleanup
        uninstall_import_guards()

    def test_double_uninstall_warning(self, caplog):
        """Uninstalling twice should log a warning."""
        install_import_guards()
        uninstall_import_guards()
        uninstall_import_guards()

        assert "not installed" in caplog.text

    def test_is_installed_status(self):
        """is_installed should reflect actual installation status."""
        uninstall_import_guards()
        assert is_installed() is False

        install_import_guards()
        assert is_installed() is True

        uninstall_import_guards()
        assert is_installed() is False


class TestConfigurationHelpers:
    """Test configuration helper functions."""

    def test_add_protected_module(self):
        """Should be able to add protected modules."""
        original_count = len(PROTECTED_MODULES)

        add_protected_module("test.module")
        assert "test.module" in PROTECTED_MODULES

        # Cleanup
        remove_protected_module("test.module")
        assert len(PROTECTED_MODULES) == original_count

    def test_remove_protected_module(self):
        """Should be able to remove protected modules."""
        add_protected_module("test.module")
        assert "test.module" in PROTECTED_MODULES

        remove_protected_module("test.module")
        assert "test.module" not in PROTECTED_MODULES

    def test_add_allowed_importer(self):
        """Should be able to add allowed importers."""
        original_count = len(ALLOWED_IMPORTERS)

        add_allowed_importer("test.importer")
        assert "test.importer" in ALLOWED_IMPORTERS

        # Cleanup
        remove_allowed_importer("test.importer")
        assert len(ALLOWED_IMPORTERS) == original_count

    def test_remove_allowed_importer(self):
        """Should be able to remove allowed importers."""
        add_allowed_importer("test.importer")
        assert "test.importer" in ALLOWED_IMPORTERS

        remove_allowed_importer("test.importer")
        assert "test.importer" not in ALLOWED_IMPORTERS

    def test_add_blocked_importer(self):
        """Should be able to add blocked importers."""
        original_count = len(BLOCKED_IMPORTERS)

        add_blocked_importer("test.blocked")
        assert "test.blocked" in BLOCKED_IMPORTERS

        # Cleanup
        remove_blocked_importer("test.blocked")
        assert len(BLOCKED_IMPORTERS) == original_count

    def test_remove_blocked_importer(self):
        """Should be able to remove blocked importers."""
        add_blocked_importer("test.blocked")
        assert "test.blocked" in BLOCKED_IMPORTERS

        remove_blocked_importer("test.blocked")
        assert "test.blocked" not in BLOCKED_IMPORTERS

    def test_get_configuration(self):
        """Should return current configuration."""
        config = get_configuration()

        assert "enforcement_mode" in config
        assert "installed" in config
        assert "protected_modules" in config
        assert "allowed_importers" in config
        assert "blocked_importers" in config

        assert isinstance(config["protected_modules"], list)
        assert isinstance(config["allowed_importers"], list)
        assert isinstance(config["blocked_importers"], list)

        # Check expected protected modules
        assert "agents.orchestrator" in config["protected_modules"]
        assert "agents.content_validator" in config["protected_modules"]
        assert "core.validation_store" in config["protected_modules"]

        # Check expected allowed importers
        assert "svc.mcp_server" in config["allowed_importers"]
        assert "tests" in config["allowed_importers"]

        # Check expected blocked importers
        assert "api" in config["blocked_importers"]
        assert "cli" in config["blocked_importers"]


class TestIntegration:
    """Integration tests for import guard system."""

    def test_full_lifecycle(self):
        """Test complete install, enforce, uninstall lifecycle."""
        # Start clean
        uninstall_import_guards()
        original_mode = get_enforcement_mode()

        try:
            # Configure
            set_enforcement_mode(EnforcementMode.BLOCK)

            # Install
            install_import_guards()
            assert is_installed()

            # Verify protection works (we can't actually test blocking
            # because the modules are already imported in the test environment)
            allowed, _ = is_import_allowed("agents.orchestrator", "api.server")
            assert not allowed

            # Uninstall
            uninstall_import_guards()
            assert not is_installed()

        finally:
            set_enforcement_mode(original_mode)
            uninstall_import_guards()

    def test_mode_transitions(self):
        """Test switching between enforcement modes."""
        original_mode = get_enforcement_mode()

        try:
            # Block mode
            set_enforcement_mode(EnforcementMode.BLOCK)
            assert get_enforcement_mode() == EnforcementMode.BLOCK

            # Warn mode
            set_enforcement_mode(EnforcementMode.WARN)
            assert get_enforcement_mode() == EnforcementMode.WARN

            # Log mode
            set_enforcement_mode(EnforcementMode.LOG)
            assert get_enforcement_mode() == EnforcementMode.LOG

            # Disabled
            set_enforcement_mode(EnforcementMode.DISABLED)
            assert get_enforcement_mode() == EnforcementMode.DISABLED

        finally:
            set_enforcement_mode(original_mode)

    def test_configuration_persistence(self):
        """Test that configuration changes persist."""
        original_protected = PROTECTED_MODULES.copy()
        original_allowed = ALLOWED_IMPORTERS.copy()

        try:
            # Add custom configuration
            add_protected_module("custom.protected")
            add_allowed_importer("custom.allowed")

            # Verify in configuration
            config = get_configuration()
            assert "custom.protected" in config["protected_modules"]
            assert "custom.allowed" in config["allowed_importers"]

            # Verify import checking uses new config
            allowed, _ = is_import_allowed("custom.protected", "api.server")
            assert not allowed  # Should be blocked

            allowed, _ = is_import_allowed("custom.protected", "custom.allowed")
            assert allowed  # Should be allowed

        finally:
            # Cleanup
            PROTECTED_MODULES.clear()
            PROTECTED_MODULES.update(original_protected)
            ALLOWED_IMPORTERS.clear()
            ALLOWED_IMPORTERS.update(original_allowed)


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_module_names(self):
        """Test handling of empty module names."""
        allowed, reason = is_import_allowed("", "api.server")
        assert allowed is True
        assert "not protected" in reason

    def test_none_module_names(self):
        """Test handling of None module names."""
        allowed, reason = is_import_allowed("agents.orchestrator", None)
        assert allowed is True  # Unknown importer

    def test_exact_match_vs_prefix(self):
        """Test exact match vs prefix matching."""
        # Exact match
        allowed, _ = is_import_allowed("api", "svc.mcp_server")
        assert allowed is True  # "api" itself is not protected

        # Prefix match
        allowed, _ = is_import_allowed("agents.orchestrator", "api")
        assert allowed is False  # "api" is blocked importer

    def test_partial_name_collision(self):
        """Test that partial name matches don't trigger false positives."""
        # "apiary" should not match "api"
        allowed, _ = is_import_allowed("agents.orchestrator", "apiary.server")
        assert allowed is True  # Not in blocked list

    def test_get_importer_name_error_handling(self):
        """Test that _get_importer_name handles errors gracefully."""
        finder = ImportGuardFinder()

        # Should not crash even if stack inspection fails
        with patch('inspect.currentframe', side_effect=Exception("test error")):
            result = finder._get_importer_name()
            assert result is None
