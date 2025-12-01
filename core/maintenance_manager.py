"""System maintenance mode management."""

import os
import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime, timezone
from core.logging import get_logger

logger = get_logger(__name__)


class MaintenanceManager:
    """Manages system maintenance mode state."""

    def __init__(self, state_file: str = ".maintenance_mode"):
        """
        Initialize maintenance manager.

        Args:
            state_file: Path to maintenance state file
        """
        self.state_file = Path(state_file)
        self._load_state()

    def _load_state(self) -> None:
        """Load maintenance state from file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self._enabled = state.get("enabled", False)
                    self._enabled_at = state.get("enabled_at")
                    self._enabled_by = state.get("enabled_by", "system")
                    self._reason = state.get("reason", "")
            except Exception as e:
                logger.warning(f"Failed to load maintenance state: {e}")
                self._enabled = False
                self._enabled_at = None
                self._enabled_by = None
                self._reason = ""
        else:
            self._enabled = False
            self._enabled_at = None
            self._enabled_by = None
            self._reason = ""

    def _save_state(self) -> None:
        """Save maintenance state to file."""
        state = {
            "enabled": self._enabled,
            "enabled_at": self._enabled_at,
            "enabled_by": self._enabled_by,
            "reason": self._reason
        }
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save maintenance state: {e}")

    def is_maintenance_mode(self) -> bool:
        """Check if system is in maintenance mode."""
        return self._enabled

    def enable(self, reason: str = "", enabled_by: str = "system") -> None:
        """
        Enable maintenance mode.

        Args:
            reason: Reason for maintenance
            enabled_by: User/system that enabled maintenance
        """
        self._enabled = True
        self._enabled_at = datetime.now(timezone.utc).isoformat()
        self._enabled_by = enabled_by
        self._reason = reason
        self._save_state()
        logger.warning(f"Maintenance mode ENABLED: {reason}")

    def disable(self) -> None:
        """Disable maintenance mode."""
        self._enabled = False
        self._enabled_at = None
        self._enabled_by = None
        self._reason = ""
        self._save_state()
        logger.info("Maintenance mode DISABLED")

    def get_status(self) -> Dict[str, Any]:
        """
        Get maintenance mode status.

        Returns:
            Status dictionary with details
        """
        return {
            "enabled": self._enabled,
            "enabled_at": self._enabled_at,
            "enabled_by": self._enabled_by,
            "reason": self._reason
        }
