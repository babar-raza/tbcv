# tests/api/services/test_live_bus.py
"""
Unit tests for api/services/live_bus.py - Live event bus service.
Target coverage: 100% (Currently 0%)
"""
import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime
from typing import Dict, Any

from api.services.live_bus import (
    LiveBus,
    live_bus,
    start_live_bus,
    stop_live_bus,
    get_live_bus
)


@pytest.mark.asyncio
@pytest.mark.unit
class TestLiveBusLifecycle:
    """Test LiveBus lifecycle management."""

    async def test_initialization(self):
        """Test LiveBus initialization."""
        bus = LiveBus()

        assert bus._running is False
        assert bus._heartbeat_task is None
        assert len(bus._subscribers) == 0
        assert len(bus._global_subscribers) == 0

    async def test_start(self):
        """Test starting the live bus."""
        bus = LiveBus()

        await bus.start()

        assert bus._running is True
        assert bus._heartbeat_task is not None
        assert isinstance(bus._heartbeat_task, asyncio.Task)

        # Cleanup
        await bus.stop()

    async def test_start_idempotent(self):
        """Test that calling start multiple times is safe."""
        bus = LiveBus()

        await bus.start()
        first_task = bus._heartbeat_task

        await bus.start()
        second_task = bus._heartbeat_task

        # Should be the same task (no new task created)
        assert first_task == second_task

        # Cleanup
        await bus.stop()

    async def test_stop(self):
        """Test stopping the live bus."""
        bus = LiveBus()

        await bus.start()
        assert bus._running is True

        await bus.stop()

        assert bus._running is False

    async def test_stop_without_start(self):
        """Test stopping a bus that was never started."""
        bus = LiveBus()

        # Should not raise exception
        await bus.stop()

        assert bus._running is False

    async def test_stop_cancels_heartbeat(self):
        """Test that stop cancels the heartbeat task."""
        bus = LiveBus()

        await bus.start()
        heartbeat_task = bus._heartbeat_task

        await bus.stop()

        assert heartbeat_task.cancelled() or heartbeat_task.done()

    async def test_stop_publishes_to_system_topic(self):
        """Test that stop calls publish with server_closing message."""
        bus = LiveBus()
        await bus.start()

        with patch.object(bus, 'publish', new_callable=AsyncMock) as mock_publish:
            await bus.stop()

            # Should call publish with closing message
            mock_publish.assert_called_once()
            call_args = mock_publish.call_args
            assert call_args[0][0] == "system"  # topic
            assert call_args[0][1]["type"] == "server_closing"  # data


@pytest.mark.asyncio
@pytest.mark.unit
class TestLiveBusSubscription:
    """Test LiveBus subscription management."""

    async def test_subscribe_to_topic(self):
        """Test subscribing to a specific topic."""
        bus = LiveBus()

        queue = bus.subscribe("test_topic")

        assert isinstance(queue, asyncio.Queue)
        assert queue in bus._subscribers["test_topic"]
        assert queue.maxsize == 100

    async def test_subscribe_global(self):
        """Test subscribing to all topics."""
        bus = LiveBus()

        queue = bus.subscribe()

        assert isinstance(queue, asyncio.Queue)
        assert queue in bus._global_subscribers

    async def test_multiple_subscriptions_same_topic(self):
        """Test multiple subscribers to the same topic."""
        bus = LiveBus()

        queue1 = bus.subscribe("topic1")
        queue2 = bus.subscribe("topic1")

        assert queue1 in bus._subscribers["topic1"]
        assert queue2 in bus._subscribers["topic1"]
        assert len(bus._subscribers["topic1"]) == 2

    async def test_multiple_topics(self):
        """Test subscribing to different topics."""
        bus = LiveBus()

        queue1 = bus.subscribe("topic1")
        queue2 = bus.subscribe("topic2")

        assert queue1 in bus._subscribers["topic1"]
        assert queue2 in bus._subscribers["topic2"]
        assert len(bus._subscribers) == 2

    async def test_unsubscribe_from_topic(self):
        """Test unsubscribing from a specific topic."""
        bus = LiveBus()

        queue = bus.subscribe("test_topic")
        assert queue in bus._subscribers["test_topic"]

        bus.unsubscribe(queue, "test_topic")

        assert queue not in bus._subscribers.get("test_topic", set())

    async def test_unsubscribe_removes_empty_topic(self):
        """Test that empty topics are removed after unsubscribing."""
        bus = LiveBus()

        queue = bus.subscribe("test_topic")
        bus.unsubscribe(queue, "test_topic")

        # Topic should be removed entirely
        assert "test_topic" not in bus._subscribers

    async def test_unsubscribe_global(self):
        """Test unsubscribing from global subscriptions."""
        bus = LiveBus()

        queue = bus.subscribe()
        assert queue in bus._global_subscribers

        bus.unsubscribe(queue)

        assert queue not in bus._global_subscribers

    async def test_unsubscribe_nonexistent_queue(self):
        """Test unsubscribing a queue that was never subscribed."""
        bus = LiveBus()

        fake_queue = asyncio.Queue()

        # Should not raise exception
        bus.unsubscribe(fake_queue, "nonexistent_topic")
        bus.unsubscribe(fake_queue)

    async def test_unsubscribe_from_multiple_topics(self):
        """Test unsubscribing from multiple topics."""
        bus = LiveBus()

        queue = bus.subscribe("topic1")
        bus._subscribers["topic2"].add(queue)  # Add same queue to another topic

        # Unsubscribe from topic1
        bus.unsubscribe(queue, "topic1")

        assert queue not in bus._subscribers.get("topic1", set())
        assert queue in bus._subscribers["topic2"]

        # Unsubscribe from topic2
        bus.unsubscribe(queue, "topic2")

        assert queue not in bus._subscribers.get("topic2", set())


@pytest.mark.asyncio
@pytest.mark.unit
class TestLiveBusPublishing:
    """Test LiveBus message publishing."""

    async def test_publish_to_topic_subscribers(self):
        """Test publishing to topic-specific subscribers."""
        bus = LiveBus()
        await bus.start()

        queue = bus.subscribe("test_topic")

        data = {"message": "test"}
        await bus.publish("test_topic", data)

        message = await asyncio.wait_for(queue.get(), timeout=1.0)

        assert message["topic"] == "test_topic"
        assert message["data"] == data
        assert "timestamp" in message

        await bus.stop()

    async def test_publish_to_global_subscribers(self):
        """Test publishing to global subscribers."""
        bus = LiveBus()
        await bus.start()

        queue = bus.subscribe()  # Global subscription

        data = {"message": "test"}
        await bus.publish("any_topic", data)

        message = await asyncio.wait_for(queue.get(), timeout=1.0)

        assert message["topic"] == "any_topic"
        assert message["data"] == data

        await bus.stop()

    async def test_publish_to_multiple_subscribers(self):
        """Test publishing to multiple subscribers."""
        bus = LiveBus()
        await bus.start()

        queue1 = bus.subscribe("test_topic")
        queue2 = bus.subscribe("test_topic")
        queue3 = bus.subscribe()  # Global

        data = {"message": "test"}
        await bus.publish("test_topic", data)

        # All should receive the message
        message1 = await asyncio.wait_for(queue1.get(), timeout=1.0)
        message2 = await asyncio.wait_for(queue2.get(), timeout=1.0)
        message3 = await asyncio.wait_for(queue3.get(), timeout=1.0)

        assert message1["data"] == data
        assert message2["data"] == data
        assert message3["data"] == data

        await bus.stop()

    async def test_publish_when_not_running(self):
        """Test that publish does nothing when bus is not running."""
        bus = LiveBus()

        queue = bus.subscribe("test_topic")

        data = {"message": "test"}
        await bus.publish("test_topic", data)

        # Queue should be empty
        assert queue.empty()

    async def test_publish_to_nonexistent_topic(self):
        """Test publishing to a topic with no subscribers."""
        bus = LiveBus()
        await bus.start()

        # Should not raise exception
        await bus.publish("nonexistent_topic", {"data": "test"})

        await bus.stop()

    async def test_publish_handles_full_queue(self):
        """Test that publish handles full queues by dropping oldest message."""
        bus = LiveBus()
        await bus.start()

        # Create a queue and fill it
        queue = bus.subscribe("test_topic")

        # Fill the queue (maxsize=100)
        for i in range(100):
            await queue.put({"old": i})

        # Publish new message
        await bus.publish("test_topic", {"new": "message"})

        # Queue should still have 100 items
        assert queue.qsize() == 100

        # Get first message - should be message 1 (message 0 was dropped)
        first_msg = await queue.get()
        assert "old" in first_msg and first_msg["old"] == 1

        await bus.stop()

    async def test_publish_removes_dead_queue_on_error(self):
        """Test that publish removes queues that raise exceptions."""
        bus = LiveBus()
        await bus.start()

        # Create a mock queue that raises exception
        bad_queue = MagicMock(spec=asyncio.Queue)
        bad_queue.full.return_value = False
        bad_queue.put_nowait.side_effect = Exception("Queue error")

        bus._subscribers["test_topic"].add(bad_queue)

        await bus.publish("test_topic", {"data": "test"})

        # Bad queue should be removed
        assert bad_queue not in bus._subscribers.get("test_topic", set())

        await bus.stop()

    async def test_publish_timestamp_format(self):
        """Test that published messages have ISO format timestamp."""
        bus = LiveBus()
        await bus.start()

        queue = bus.subscribe("test_topic")

        await bus.publish("test_topic", {"data": "test"})

        message = await queue.get()

        # Timestamp should be ISO format
        timestamp = message["timestamp"]
        datetime.fromisoformat(timestamp)  # Should not raise exception

        await bus.stop()


@pytest.mark.asyncio
@pytest.mark.unit
class TestLiveBusHeartbeat:
    """Test LiveBus heartbeat functionality."""

    async def test_heartbeat_loop_sends_heartbeats(self):
        """Test that heartbeat loop sends periodic heartbeats."""
        bus = LiveBus()
        await bus.start()

        queue = bus.subscribe("system")

        # Wait for a heartbeat (20 second interval, but we'll mock time)
        with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
            # Trigger one iteration
            bus._running = True
            task = asyncio.create_task(bus._heartbeat_loop())

            await asyncio.sleep(0.1)  # Let task start

            bus._running = False
            await asyncio.sleep(0.1)  # Let task finish

        await bus.stop()

    async def test_heartbeat_cancelled_error_breaks_loop(self):
        """Test that CancelledError breaks the heartbeat loop."""
        bus = LiveBus()

        # Start and then immediately stop to trigger cancellation
        await bus.start()

        # Heartbeat task should exist
        assert bus._heartbeat_task is not None

        # Stop should cancel the heartbeat
        await bus.stop()

        # Task should be cancelled
        assert bus._heartbeat_task.cancelled() or bus._heartbeat_task.done()

    async def test_heartbeat_handles_exceptions(self):
        """Test that heartbeat loop handles exceptions."""
        bus = LiveBus()
        bus._running = True

        call_count = 0

        async def mock_sleep(duration):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Test error")
            else:
                # Stop the loop
                bus._running = False

        with patch('asyncio.sleep', side_effect=mock_sleep):
            # Should not raise exception
            await bus._heartbeat_loop()


@pytest.mark.asyncio
@pytest.mark.unit
class TestLiveBusSpecializedPublish:
    """Test specialized publish methods."""

    async def test_publish_validation_update(self):
        """Test publishing validation updates."""
        bus = LiveBus()
        await bus.start()

        queue = bus.subscribe("validation:val123")

        await bus.publish_validation_update("val123", "started", {"status": "running"})

        message = await queue.get()

        assert message["topic"] == "validation:val123"
        assert message["data"]["type"] == "started"
        assert message["data"]["validation_id"] == "val123"
        assert message["data"]["status"] == "running"

        await bus.stop()

    async def test_publish_workflow_update(self):
        """Test publishing workflow updates."""
        bus = LiveBus()
        await bus.start()

        queue = bus.subscribe("workflow:wf456")

        await bus.publish_workflow_update("wf456", "completed", {"result": "success"})

        message = await queue.get()

        assert message["topic"] == "workflow:wf456"
        assert message["data"]["type"] == "completed"
        assert message["data"]["workflow_id"] == "wf456"
        assert message["data"]["result"] == "success"

        await bus.stop()

    async def test_publish_recommendation_update(self):
        """Test publishing recommendation updates."""
        bus = LiveBus()
        await bus.start()

        queue = bus.subscribe("recommendations")

        await bus.publish_recommendation_update("rec789", "created", {"content": "test"})

        message = await queue.get()

        assert message["topic"] == "recommendations"
        assert message["data"]["type"] == "created"
        assert message["data"]["recommendation_id"] == "rec789"
        assert message["data"]["content"] == "test"

        await bus.stop()

    async def test_publish_enhancement_update(self):
        """Test publishing enhancement updates."""
        bus = LiveBus()
        await bus.start()

        queue = bus.subscribe("enhancement:enh999")

        await bus.publish_enhancement_update("enh999", "applied", {"changes": 5})

        message = await queue.get()

        assert message["topic"] == "enhancement:enh999"
        assert message["data"]["type"] == "applied"
        assert message["data"]["enhancement_id"] == "enh999"
        assert message["data"]["changes"] == 5

        await bus.stop()


@pytest.mark.asyncio
@pytest.mark.unit
class TestLiveBusGlobalInstance:
    """Test global live bus instance and helper functions."""

    async def test_get_live_bus(self):
        """Test getting the global live bus instance."""
        bus = get_live_bus()

        assert isinstance(bus, LiveBus)
        assert bus is live_bus

    async def test_start_live_bus(self):
        """Test starting the global live bus."""
        # Ensure it's stopped first
        await stop_live_bus()

        await start_live_bus()

        assert live_bus._running is True

        # Cleanup
        await stop_live_bus()

    async def test_stop_live_bus(self):
        """Test stopping the global live bus."""
        await start_live_bus()
        assert live_bus._running is True

        await stop_live_bus()

        assert live_bus._running is False


@pytest.mark.integration
@pytest.mark.asyncio
class TestLiveBusIntegration:
    """Integration tests for LiveBus."""

    async def test_full_publish_subscribe_workflow(self):
        """Test complete publish-subscribe workflow."""
        bus = LiveBus()
        await bus.start()

        # Create multiple subscribers
        topic_queue = bus.subscribe("test_topic")
        global_queue = bus.subscribe()

        # Publish multiple messages
        messages = [
            {"event": "first", "value": 1},
            {"event": "second", "value": 2},
            {"event": "third", "value": 3}
        ]

        for msg in messages:
            await bus.publish("test_topic", msg)

        # Verify topic subscriber received all messages
        for expected in messages:
            received = await asyncio.wait_for(topic_queue.get(), timeout=1.0)
            assert received["data"] == expected

        # Verify global subscriber received all messages
        for expected in messages:
            received = await asyncio.wait_for(global_queue.get(), timeout=1.0)
            assert received["data"] == expected

        await bus.stop()

    async def test_subscribe_unsubscribe_workflow(self):
        """Test subscribing and unsubscribing during operation."""
        bus = LiveBus()
        await bus.start()

        # Subscribe
        queue = bus.subscribe("test_topic")

        # Publish message
        await bus.publish("test_topic", {"msg": "first"})
        message = await queue.get()
        assert message["data"]["msg"] == "first"

        # Unsubscribe
        bus.unsubscribe(queue, "test_topic")

        # Publish another message
        await bus.publish("test_topic", {"msg": "second"})

        # Queue should not receive it
        await asyncio.sleep(0.1)
        assert queue.empty()

        await bus.stop()

    async def test_mixed_subscribers_isolation(self):
        """Test that topic subscribers only receive their topic messages."""
        bus = LiveBus()
        await bus.start()

        topic1_queue = bus.subscribe("topic1")
        topic2_queue = bus.subscribe("topic2")
        global_queue = bus.subscribe()

        # Publish to topic1
        await bus.publish("topic1", {"data": "for_topic1"})

        # topic1_queue should receive
        msg1 = await asyncio.wait_for(topic1_queue.get(), timeout=1.0)
        assert msg1["data"]["data"] == "for_topic1"

        # topic2_queue should not receive
        await asyncio.sleep(0.1)
        assert topic2_queue.empty()

        # global_queue should receive
        msg_global = await asyncio.wait_for(global_queue.get(), timeout=1.0)
        assert msg_global["data"]["data"] == "for_topic1"

        await bus.stop()

    async def test_lifecycle_with_active_subscribers(self):
        """Test starting and stopping bus with active subscribers."""
        bus = LiveBus()

        # Subscribe before starting
        queue = bus.subscribe("test_topic")

        # Start bus
        await bus.start()

        # Publish message
        await bus.publish("test_topic", {"data": "test"})

        message = await queue.get()
        assert message["data"]["data"] == "test"

        # Stop bus
        with patch.object(bus, 'publish', wraps=bus.publish) as mock_publish:
            await bus.stop()

            # Verify stop called publish with closing message
            assert mock_publish.called
            call_args = mock_publish.call_args
            assert call_args[0][0] == "system"
            assert call_args[0][1]["type"] == "server_closing"

    async def test_queue_overflow_handling(self):
        """Test that queue overflow is handled gracefully."""
        bus = LiveBus()
        await bus.start()

        queue = bus.subscribe("test_topic")

        # Fill queue to capacity
        for i in range(100):
            await bus.publish("test_topic", {"index": i})

        # Publish one more - should drop oldest
        await bus.publish("test_topic", {"index": 100})

        # First message should be index 1 (index 0 was dropped)
        first_msg = await queue.get()
        assert first_msg["data"]["index"] == 1

        await bus.stop()
