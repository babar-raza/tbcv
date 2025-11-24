# file: api/services/live_bus.py
"""
Live event bus for real-time updates.

This module provides a publish/subscribe event bus for real-time updates
to connected clients via WebSocket. It integrates with the WebSocket
connection manager to broadcast events.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timezone
from core.logging import get_logger

logger = get_logger(__name__)


class LiveBus:
    """
    Live event bus that forwards events to WebSocket clients.
    Integrates with the WebSocket connection_manager for real-time updates.
    """

    def __init__(self):
        self.enabled = True
        self._connection_manager = None

    def _get_connection_manager(self):
        """Lazy-load connection manager to avoid circular imports."""
        if self._connection_manager is None:
            try:
                from api.websocket_endpoints import connection_manager
                self._connection_manager = connection_manager
                logger.info("LiveBus connected to WebSocket connection manager")
            except Exception as e:
                logger.error(f"Failed to import connection_manager: {e}")
                self.enabled = False
        return self._connection_manager

    async def publish(self, topic: str, message: Dict[str, Any]):
        """
        Publish message to topic.

        Args:
            topic: The topic/channel to publish to (e.g., "validation_updates")
            message: The message payload to send
        """
        if not self.enabled:
            return

        try:
            cm = self._get_connection_manager()
            if cm:
                await cm.send_progress_update(topic, message)
        except Exception as e:
            logger.error(f"Failed to publish message to topic '{topic}': {e}")

    async def publish_validation_update(self, validation_id: str, event_type: str, data: Dict[str, Any]):
        """
        Publish a validation-related update.

        Args:
            validation_id: ID of the validation
            event_type: Type of event (e.g., "validation_created", "validation_approved")
            data: Additional data about the event
        """
        message = {
            "type": event_type,
            "validation_id": validation_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **data
        }

        # Send to global validation_updates channel
        await self.publish("validation_updates", message)

        # Also send to validation-specific channel if clients are listening
        await self.publish(f"validation_{validation_id}", message)

    async def publish_recommendation_update(self, recommendation_id: str, event_type: str, data: Dict[str, Any]):
        """
        Publish a recommendation-related update.

        Args:
            recommendation_id: ID of the recommendation
            event_type: Type of event (e.g., "recommendation_created", "recommendation_approved")
            data: Additional data about the event
        """
        message = {
            "type": event_type,
            "recommendation_id": recommendation_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **data
        }

        # Send to global validation_updates channel (dashboard listens here)
        await self.publish("validation_updates", message)

        # Also send to recommendation-specific channel
        await self.publish(f"recommendation_{recommendation_id}", message)

    async def publish_workflow_update(self, workflow_id: str, event_type: str, data: Dict[str, Any]):
        """
        Publish a workflow-related update.

        Args:
            workflow_id: ID of the workflow
            event_type: Type of event (e.g., "workflow_started", "workflow_completed")
            data: Additional data about the event
        """
        message = {
            "type": event_type,
            "workflow_id": workflow_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **data
        }

        # Send to workflow-specific channel
        await self.publish(workflow_id, message)

        # Also send to global validation_updates channel for dashboard
        await self.publish("validation_updates", message)

    async def subscribe(self, topic: str):
        """
        Subscribe to topic (WebSocket connections handle their own subscriptions).
        This method is maintained for API compatibility.
        """
        logger.debug(f"Subscribe called for topic '{topic}' (handled by WebSocket)")

    async def unsubscribe(self, queue, topic: str):
        """
        Unsubscribe from topic (WebSocket connections handle their own cleanup).
        This method is maintained for API compatibility.
        """
        logger.debug(f"Unsubscribe called for topic '{topic}' (handled by WebSocket)")


_live_bus_instance: Optional[LiveBus] = None


async def start_live_bus():
    """Start the live event bus."""
    global _live_bus_instance
    _live_bus_instance = LiveBus()
    logger.info("Live event bus started")


async def stop_live_bus():
    """Stop the live event bus."""
    global _live_bus_instance
    if _live_bus_instance:
        _live_bus_instance.enabled = False
    _live_bus_instance = None
    logger.info("Live event bus stopped")


def get_live_bus() -> LiveBus:
    """Get the live event bus instance."""
    global _live_bus_instance
    if _live_bus_instance is None:
        _live_bus_instance = LiveBus()
    return _live_bus_instance
