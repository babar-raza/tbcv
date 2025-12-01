"""Base classes for MCP method handlers."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from core.logging import get_logger

logger = get_logger(__name__)


class BaseMCPMethod(ABC):
    """Abstract base class for all MCP method handlers."""

    def __init__(self, db_manager, rule_manager, agent_registry):
        """
        Initialize base MCP method handler.

        Args:
            db_manager: Database manager instance
            rule_manager: Rule manager instance
            agent_registry: Agent registry instance
        """
        self.db_manager = db_manager
        self.rule_manager = rule_manager
        self.agent_registry = agent_registry
        self.logger = get_logger(self.__class__.__name__)

    @abstractmethod
    def handle(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle method execution.

        Args:
            params: Method parameters

        Returns:
            Method result dictionary

        Raises:
            ValueError: If parameters are invalid
            Exception: For other errors
        """
        pass

    def validate_params(
        self,
        params: Dict[str, Any],
        required: list,
        optional: Optional[dict] = None
    ) -> None:
        """
        Validate method parameters.

        Args:
            params: Parameters to validate
            required: List of required parameter names
            optional: Dict of optional parameters with default values

        Raises:
            ValueError: If required parameters are missing
        """
        missing = [p for p in required if p not in params]
        if missing:
            raise ValueError(f"Missing required parameters: {', '.join(missing)}")

        # Set defaults for optional parameters
        if optional:
            for key, default in optional.items():
                if key not in params:
                    params[key] = default


class MCPMethodRegistry:
    """Registry for MCP method handlers."""

    def __init__(self):
        """Initialize method registry."""
        self._handlers: Dict[str, Any] = {}
        self.logger = get_logger(__name__)

    def register(self, name: str, handler: Any) -> None:
        """
        Register a method handler.

        Args:
            name: Method name
            handler: Method handler function

        Raises:
            ValueError: If method already registered
        """
        if name in self._handlers:
            raise ValueError(f"Method {name} already registered")
        self._handlers[name] = handler
        self.logger.info(f"Registered MCP method: {name}")

    def get_handler(self, name: str) -> Optional[Any]:
        """
        Get handler for method name.

        Args:
            name: Method name

        Returns:
            Method handler or None if not found
        """
        return self._handlers.get(name)

    def list_methods(self) -> list:
        """
        List all registered method names.

        Returns:
            List of method names
        """
        return list(self._handlers.keys())
