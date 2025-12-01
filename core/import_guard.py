# file: tbcv/core/import_guard.py
"""
Import-time protection for TBCV validation system.
Detects prohibited imports at import time using sys.meta_path hooks.
"""
import sys
import importlib.abc
import importlib.machinery
import inspect
import logging
from enum import Enum
from typing import Optional, Tuple, Set, List

logger = logging.getLogger(__name__)


class EnforcementMode(Enum):
    """Import enforcement modes."""
    BLOCK = "block"    # Raise ImportGuardError on violation
    WARN = "warn"      # Log warning but allow import
    LOG = "log"        # Log info message only
    DISABLED = "disabled"  # No enforcement


class ImportGuardError(ImportError):
    """Raised when a prohibited import is attempted in BLOCK mode."""
    pass


# Protected modules that should only be imported by allowed modules
PROTECTED_MODULES = {
    "agents.orchestrator",
    "agents.content_validator",
    "agents.content_enhancer",
    "agents.recommendation_agent",
    "agents.truth_manager",
    "agents.validators",
    "core.validation_store",
}

# Modules allowed to import protected modules
ALLOWED_IMPORTERS = {
    "svc.mcp_server",
    "svc.mcp_methods",
    "tests",
}

# Modules explicitly blocked from importing protected modules
BLOCKED_IMPORTERS = {
    "api",
    "cli",
}

# Global enforcement mode (can be configured)
_enforcement_mode = EnforcementMode.BLOCK


def set_enforcement_mode(mode: EnforcementMode) -> None:
    """
    Set the global enforcement mode for import guards.

    Args:
        mode: EnforcementMode enum value
    """
    global _enforcement_mode
    _enforcement_mode = mode
    logger.info(f"Import guard enforcement mode set to: {mode.value}")


def get_enforcement_mode() -> EnforcementMode:
    """Get the current enforcement mode."""
    return _enforcement_mode


def _is_module_prefix_match(module_name: str, prefix_set: Set[str]) -> bool:
    """
    Check if module name matches any prefix in the set.

    Args:
        module_name: Full module name (e.g., "api.server")
        prefix_set: Set of module prefixes (e.g., {"api", "cli"})

    Returns:
        True if module_name starts with any prefix in the set
    """
    if not module_name:
        return False

    for prefix in prefix_set:
        if module_name == prefix or module_name.startswith(prefix + "."):
            return True
    return False


def is_import_allowed(
    target_module: str,
    importer_module: Optional[str]
) -> Tuple[bool, str]:
    """
    Check if an import is allowed based on protection rules.

    Args:
        target_module: The module being imported
        importer_module: The module attempting the import

    Returns:
        Tuple of (allowed: bool, reason: str)
    """
    # If target is not protected, always allow
    if not _is_module_prefix_match(target_module, PROTECTED_MODULES):
        return True, "target not protected"

    # If importer is unknown (e.g., interactive shell), allow with warning
    if not importer_module:
        return True, "importer unknown (interactive or __main__)"

    # If importer is in allowed list, allow
    if _is_module_prefix_match(importer_module, ALLOWED_IMPORTERS):
        return True, f"importer '{importer_module}' is allowed"

    # If importer is in blocked list, block
    if _is_module_prefix_match(importer_module, BLOCKED_IMPORTERS):
        return False, f"importer '{importer_module}' is explicitly blocked"

    # Default: allow (could be configured to default-deny)
    return True, "importer not in blocked list"


class ImportGuardFinder(importlib.abc.MetaPathFinder):
    """
    Meta path finder that intercepts imports to enforce access rules.

    This finder checks imports against the protection rules before
    allowing them to proceed through the normal import system.
    """

    def find_module(self, fullname: str, path: Optional[List[str]] = None) -> None:
        """
        Check if import should be allowed (Python 2-style API for compatibility).

        Args:
            fullname: Full name of the module being imported
            path: Parent package's path (if any)

        Returns:
            None (we don't actually load modules, just check access)

        Raises:
            ImportGuardError: If import is prohibited and mode is BLOCK
        """
        # Get enforcement mode
        mode = get_enforcement_mode()

        # If disabled, don't do anything
        if mode == EnforcementMode.DISABLED:
            return None

        # Get the importer module name from the call stack
        importer_name = self._get_importer_name()

        # Check if import is allowed
        allowed, reason = is_import_allowed(fullname, importer_name)

        if not allowed:
            message = (
                f"Import blocked: '{importer_name}' attempted to import "
                f"protected module '{fullname}'. Reason: {reason}"
            )

            if mode == EnforcementMode.BLOCK:
                logger.error(message)
                raise ImportGuardError(message)
            elif mode == EnforcementMode.WARN:
                logger.warning(message)
            elif mode == EnforcementMode.LOG:
                logger.info(message)

        # Return None to let the import continue through normal channels
        return None

    def find_spec(
        self,
        fullname: str,
        path: Optional[List[str]] = None,
        target: Optional[object] = None
    ) -> None:
        """
        Check if import should be allowed (Python 3-style API).

        Args:
            fullname: Full name of the module being imported
            path: Parent package's path (if any)
            target: Target module (for reloading)

        Returns:
            None (we don't actually load modules, just check access)

        Raises:
            ImportGuardError: If import is prohibited and mode is BLOCK
        """
        # Use same logic as find_module
        self.find_module(fullname, path)
        return None

    def _get_importer_name(self) -> Optional[str]:
        """
        Get the name of the module performing the import from the call stack.

        Returns:
            Module name or None if not found
        """
        try:
            # Walk up the stack to find the first frame outside this module
            frame = inspect.currentframe()
            while frame:
                frame_globals = frame.f_globals
                frame_name = frame_globals.get("__name__")

                # Skip our own module and importlib internals
                if frame_name and not frame_name.startswith(("importlib", "__main__")):
                    if frame_name != __name__:
                        return frame_name

                frame = frame.f_back

            return None
        except Exception as e:
            logger.debug(f"Error getting importer name: {e}")
            return None


# Global reference to installed finder
_installed_finder: Optional[ImportGuardFinder] = None


def install_import_guards() -> None:
    """
    Install import guard hooks into sys.meta_path.

    This should be called early in application startup, before
    any protected modules are imported.
    """
    global _installed_finder

    if _installed_finder is not None:
        logger.warning("Import guards already installed")
        return

    _installed_finder = ImportGuardFinder()
    sys.meta_path.insert(0, _installed_finder)
    logger.info("Import guards installed")


def uninstall_import_guards() -> None:
    """
    Remove import guard hooks from sys.meta_path.

    Useful for testing or when import protection is no longer needed.
    """
    global _installed_finder

    if _installed_finder is None:
        logger.warning("Import guards not installed")
        return

    try:
        sys.meta_path.remove(_installed_finder)
        _installed_finder = None
        logger.info("Import guards uninstalled")
    except ValueError:
        logger.error("Import guard finder not found in sys.meta_path")
        _installed_finder = None


def is_installed() -> bool:
    """Check if import guards are currently installed."""
    return _installed_finder is not None


# Convenience functions for testing and configuration


def add_protected_module(module_name: str) -> None:
    """Add a module to the protected set."""
    PROTECTED_MODULES.add(module_name)
    logger.debug(f"Added protected module: {module_name}")


def remove_protected_module(module_name: str) -> None:
    """Remove a module from the protected set."""
    PROTECTED_MODULES.discard(module_name)
    logger.debug(f"Removed protected module: {module_name}")


def add_allowed_importer(module_name: str) -> None:
    """Add a module to the allowed importers set."""
    ALLOWED_IMPORTERS.add(module_name)
    logger.debug(f"Added allowed importer: {module_name}")


def remove_allowed_importer(module_name: str) -> None:
    """Remove a module from the allowed importers set."""
    ALLOWED_IMPORTERS.discard(module_name)
    logger.debug(f"Removed allowed importer: {module_name}")


def add_blocked_importer(module_name: str) -> None:
    """Add a module to the blocked importers set."""
    BLOCKED_IMPORTERS.add(module_name)
    logger.debug(f"Added blocked importer: {module_name}")


def remove_blocked_importer(module_name: str) -> None:
    """Remove a module from the blocked importers set."""
    BLOCKED_IMPORTERS.discard(module_name)
    logger.debug(f"Removed blocked importer: {module_name}")


def get_configuration() -> dict:
    """
    Get current import guard configuration.

    Returns:
        Dict with protected modules, allowed/blocked importers, and mode
    """
    return {
        "enforcement_mode": _enforcement_mode.value,
        "installed": is_installed(),
        "protected_modules": sorted(PROTECTED_MODULES),
        "allowed_importers": sorted(ALLOWED_IMPORTERS),
        "blocked_importers": sorted(BLOCKED_IMPORTERS),
    }
