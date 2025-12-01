"""Admin and maintenance MCP methods."""

from typing import Dict, Any, Optional, List
import gc
import psutil
from datetime import datetime, timezone
from .base import BaseMCPMethod
from core.maintenance_manager import MaintenanceManager
from core.checkpoint_manager import CheckpointManager
from core.logging import get_logger

logger = get_logger(__name__)


class AdminMethods(BaseMCPMethod):
    """Handler for admin and maintenance MCP methods."""

    def __init__(self, db_manager, rule_manager, agent_registry):
        super().__init__(db_manager, rule_manager, agent_registry)
        self.maintenance_manager = MaintenanceManager()
        self.checkpoint_manager = CheckpointManager()

    def handle(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle admin method execution.

        Args:
            params: Method parameters

        Returns:
            Method result dictionary

        Raises:
            ValueError: If parameters are invalid
        """
        # This is called via registry, specific methods are called directly
        raise NotImplementedError("Use specific admin methods via registry")

    # ========================================================================
    # System Status & Health
    # ========================================================================

    def get_system_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get system health status.

        Args:
            params: {} (no parameters required)

        Returns:
            {
                "status": str,  # "healthy" | "degraded" | "unhealthy"
                "components": {
                    "database": {"status": str, "details": Dict},
                    "cache": {"status": str, "details": Dict},
                    "agents": {"status": str, "details": Dict}
                },
                "resources": {
                    "cpu_percent": float,
                    "memory_percent": float,
                    "disk_percent": float
                },
                "maintenance_mode": bool
            }
        """
        self.logger.info("Getting system status")

        # Check database health
        db_status = self._check_database_health()

        # Check cache health
        cache_status = self._check_cache_health()

        # Check agents health
        agents_status = self._check_agents_health()

        # Get resource usage
        resources = self._get_resource_usage()

        # Determine overall status
        component_statuses = [
            db_status["status"],
            cache_status["status"],
            agents_status["status"]
        ]

        if all(s == "healthy" for s in component_statuses):
            overall_status = "healthy"
        elif any(s == "unhealthy" for s in component_statuses):
            overall_status = "unhealthy"
        else:
            overall_status = "degraded"

        return {
            "status": overall_status,
            "components": {
                "database": db_status,
                "cache": cache_status,
                "agents": agents_status
            },
            "resources": resources,
            "maintenance_mode": self.maintenance_manager.is_maintenance_mode()
        }

    def _check_database_health(self) -> Dict[str, Any]:
        """Check database health."""
        try:
            # Test database connection
            with self.db_manager.get_session() as session:
                from sqlalchemy import text
                session.execute(text("SELECT 1"))

            # Get database stats
            validation_count = self.db_manager.count_validations()

            return {
                "status": "healthy",
                "details": {
                    "connected": True,
                    "validation_count": validation_count
                }
            }
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "details": {"error": str(e)}
            }

    def _check_cache_health(self) -> Dict[str, Any]:
        """Check cache health."""
        try:
            from core.cache import cache_manager
            stats = cache_manager.get_stats()

            return {
                "status": "healthy",
                "details": stats
            }
        except Exception as e:
            self.logger.error(f"Cache health check failed: {e}")
            return {
                "status": "unhealthy",
                "details": {"error": str(e)}
            }

    def _check_agents_health(self) -> Dict[str, Any]:
        """Check agents health."""
        try:
            if self.agent_registry is None:
                return {
                    "status": "healthy",
                    "details": {
                        "agent_count": 0,
                        "agents": [],
                        "note": "Agent registry not initialized"
                    }
                }

            agents = self.agent_registry.list_agents()
            agent_count = len(agents)

            # Get list of agent IDs
            agent_ids = list(agents.keys()) if agents else []

            return {
                "status": "healthy",
                "details": {
                    "agent_count": agent_count,
                    "agents": agent_ids
                }
            }
        except Exception as e:
            self.logger.error(f"Agents health check failed: {e}")
            return {
                "status": "unhealthy",
                "details": {"error": str(e)}
            }

    def _get_resource_usage(self) -> Dict[str, Any]:
        """Get system resource usage."""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('.').percent
            }
        except Exception as e:
            self.logger.warning(f"Failed to get resource usage: {e}")
            return {
                "cpu_percent": 0,
                "memory_percent": 0,
                "disk_percent": 0
            }

    # ========================================================================
    # Cache Management
    # ========================================================================

    def clear_cache(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clear all caches.

        Args:
            params: {
                "cache_types": List[str] (optional) - Specific caches to clear
            }

        Returns:
            {
                "success": bool,
                "cleared_items": int,
                "cache_types_cleared": List[str]
            }
        """
        self.validate_params(params, required=[],
                           optional={"cache_types": None})

        cache_types = params.get("cache_types")

        self.logger.info(f"Clearing cache (types: {cache_types})")

        from core.cache import cache_manager

        # Clear cache
        if cache_types:
            # For specific cache types, we'd need more granular control
            # For now, just clear all
            result = cache_manager.clear()
            cleared_count = result.get("l1_cleared", 0) + result.get("l2_cleared", 0)
        else:
            result = cache_manager.clear()
            cleared_count = result.get("l1_cleared", 0) + result.get("l2_cleared", 0)

        return {
            "success": True,
            "cleared_items": cleared_count,
            "cache_types_cleared": cache_types or ["all"]
        }

    def get_cache_stats(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get cache statistics.

        Args:
            params: {} (no parameters)

        Returns:
            {
                "total_items": int,
                "total_size_bytes": int,
                "hit_rate": float,
                "by_type": Dict[str, Dict]
            }
        """
        self.logger.info("Getting cache statistics")

        from core.cache import cache_manager
        stats = cache_manager.get_stats()

        # Transform stats into expected format
        total_items = 0
        total_size_bytes = 0
        hit_rate = 0.0

        if stats.get("l1", {}).get("enabled"):
            total_items += stats["l1"].get("size", 0)
            hit_rate = stats["l1"].get("hit_rate", 0.0)

        if stats.get("l2", {}).get("enabled"):
            total_items += stats["l2"].get("total_entries", 0)
            total_size_bytes += stats["l2"].get("total_size_bytes", 0)

        return {
            "total_items": total_items,
            "total_size_bytes": total_size_bytes,
            "hit_rate": hit_rate,
            "by_type": stats
        }

    def cleanup_cache(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean up stale cache entries.

        Args:
            params: {
                "max_age_hours": int (optional, default 24)
            }

        Returns:
            {
                "success": bool,
                "cleaned_items": int
            }
        """
        self.validate_params(params, required=[],
                           optional={"max_age_hours": 24})

        max_age_hours = params.get("max_age_hours", 24)

        self.logger.info(f"Cleaning up cache entries older than {max_age_hours} hours")

        from core.cache import cache_manager
        cleaned_count = cache_manager.cleanup(max_age_hours=max_age_hours)

        return {
            "success": True,
            "cleaned_items": cleaned_count
        }

    def rebuild_cache(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Rebuild cache from scratch.

        Args:
            params: {} (no parameters)

        Returns:
            {
                "success": bool,
                "rebuilt_items": int
            }
        """
        self.logger.info("Rebuilding cache from scratch")

        from core.cache import cache_manager

        # Rebuild cache
        rebuilt_count = cache_manager.rebuild()

        return {
            "success": True,
            "rebuilt_items": rebuilt_count
        }

    # ========================================================================
    # Agent Management
    # ========================================================================

    def reload_agent(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reload specific agent.

        Args:
            params: {
                "agent_id": str (required)
            }

        Returns:
            {
                "success": bool,
                "agent_id": str,
                "reloaded_at": str
            }
        """
        self.validate_params(params, required=["agent_id"])

        agent_id = params["agent_id"]

        self.logger.info(f"Reloading agent: {agent_id}")

        if self.agent_registry is None:
            raise ValueError("Agent registry not initialized")

        # Reload agent
        self.agent_registry.reload_agent(agent_id)

        return {
            "success": True,
            "agent_id": agent_id,
            "reloaded_at": datetime.now(timezone.utc).isoformat()
        }

    # ========================================================================
    # System Maintenance
    # ========================================================================

    def run_gc(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run garbage collection.

        Args:
            params: {} (no parameters)

        Returns:
            {
                "success": bool,
                "collected_objects": int,
                "generation": int
            }
        """
        self.logger.info("Running garbage collection")

        # Run full garbage collection
        collected = gc.collect()

        # Get GC stats
        stats = gc.get_stats()

        return {
            "success": True,
            "collected_objects": collected,
            "generation": len(stats) - 1 if stats else 0,
            "stats": stats
        }

    def enable_maintenance_mode(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enable maintenance mode.

        Args:
            params: {
                "reason": str (optional),
                "enabled_by": str (optional, default "system")
            }

        Returns:
            {
                "success": bool,
                "enabled_at": str
            }
        """
        self.validate_params(params, required=[],
                           optional={"reason": "", "enabled_by": "system"})

        reason = params.get("reason", "")
        enabled_by = params.get("enabled_by", "system")

        self.logger.warning(f"Enabling maintenance mode: {reason}")

        self.maintenance_manager.enable(reason=reason, enabled_by=enabled_by)

        return {
            "success": True,
            "enabled_at": datetime.now(timezone.utc).isoformat()
        }

    def disable_maintenance_mode(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Disable maintenance mode.

        Args:
            params: {} (no parameters)

        Returns:
            {
                "success": bool,
                "disabled_at": str
            }
        """
        self.logger.info("Disabling maintenance mode")

        self.maintenance_manager.disable()

        return {
            "success": True,
            "disabled_at": datetime.now(timezone.utc).isoformat()
        }

    def create_checkpoint(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create system checkpoint.

        Args:
            params: {
                "name": str (optional),
                "metadata": Dict (optional)
            }

        Returns:
            {
                "success": bool,
                "checkpoint_id": str,
                "created_at": str
            }
        """
        self.validate_params(params, required=[],
                           optional={"name": None, "metadata": None})

        name = params.get("name")
        metadata = params.get("metadata")

        self.logger.info(f"Creating checkpoint: {name}")

        checkpoint_id = self.checkpoint_manager.create_checkpoint(
            name=name,
            metadata=metadata
        )

        return {
            "success": True,
            "checkpoint_id": checkpoint_id,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
