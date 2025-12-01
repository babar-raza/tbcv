"""
Tests for checkpoint system.

Tests cover:
- Agent checkpoint creation and restoration
- Data integrity validation
- Checkpoint persistence
- Error handling
"""

import pytest
from agents.base import BaseAgent
from core.database import Checkpoint, db_manager


class TestAgentCheckpoints:
    """Tests for agent checkpoint creation and restoration."""

    @pytest.fixture
    def test_agent(self):
        """Create a test agent for checkpoint testing."""
        from agents.base import AgentCapability, MCPMessage

        class TestCheckpointAgent(BaseAgent):
            def __init__(self):
                super().__init__(agent_id="test_checkpoint_agent")

            def get_contract(self):
                return {
                    "agent_id": self.agent_id,
                    "name": "Test Checkpoint Agent",
                    "description": "Agent for testing checkpoints",
                    "capabilities": []
                }

            def _register_message_handlers(self):
                pass  # No handlers needed for checkpoint testing

        return TestCheckpointAgent()

    def test_create_checkpoint_returns_id(self, test_agent):
        """Creating a checkpoint should return a UUID."""
        checkpoint_id = test_agent.create_checkpoint(
            name="test_checkpoint",
            data={"key": "value"}
        )

        assert checkpoint_id is not None
        assert isinstance(checkpoint_id, str)
        assert len(checkpoint_id) == 36  # UUID format

    def test_create_checkpoint_with_workflow_id(self, test_agent):
        """Checkpoint should accept workflow_id parameter."""
        workflow_id = "wf-test-12345"
        checkpoint_id = test_agent.create_checkpoint(
            name="test_checkpoint",
            data={"key": "value"},
            workflow_id=workflow_id
        )

        # Verify checkpoint was created with correct workflow_id
        with db_manager.get_session() as session:
            checkpoint = session.query(Checkpoint).filter(
                Checkpoint.id == checkpoint_id
            ).first()

            assert checkpoint is not None
            assert checkpoint.workflow_id == workflow_id

    def test_create_checkpoint_without_workflow_id(self, test_agent):
        """Checkpoint should generate workflow_id if not provided."""
        checkpoint_id = test_agent.create_checkpoint(
            name="test_checkpoint",
            data={"key": "value"}
        )

        with db_manager.get_session() as session:
            checkpoint = session.query(Checkpoint).filter(
                Checkpoint.id == checkpoint_id
            ).first()

            assert checkpoint is not None
            assert checkpoint.workflow_id is not None
            assert checkpoint.workflow_id.startswith("agent_")

    def test_create_checkpoint_persists_data(self, test_agent):
        """Checkpoint should persist data to database."""
        test_data = {
            "progress": 50,
            "processed_items": 100,
            "remaining_items": 100,
            "errors": []
        }

        checkpoint_id = test_agent.create_checkpoint(
            name="test_checkpoint",
            data=test_data
        )

        # Verify data was persisted
        with db_manager.get_session() as session:
            checkpoint = session.query(Checkpoint).filter(
                Checkpoint.id == checkpoint_id
            ).first()

            assert checkpoint is not None
            assert checkpoint.state_data is not None
            assert len(checkpoint.state_data) > 0

    def test_create_checkpoint_sets_validation_hash(self, test_agent):
        """Checkpoint should include validation hash."""
        checkpoint_id = test_agent.create_checkpoint(
            name="test_checkpoint",
            data={"key": "value"}
        )

        with db_manager.get_session() as session:
            checkpoint = session.query(Checkpoint).filter(
                Checkpoint.id == checkpoint_id
            ).first()

            assert checkpoint.validation_hash is not None
            assert len(checkpoint.validation_hash) == 32  # MD5 hash

    def test_restore_checkpoint_returns_data(self, test_agent):
        """Restoring checkpoint should return original data."""
        test_data = {
            "progress": 75,
            "status": "in_progress",
            "results": ["item1", "item2", "item3"]
        }

        checkpoint_id = test_agent.create_checkpoint(
            name="test_checkpoint",
            data=test_data
        )

        restored_data = test_agent.restore_checkpoint(checkpoint_id)

        assert restored_data == test_data
        assert restored_data["progress"] == 75
        assert len(restored_data["results"]) == 3

    def test_restore_checkpoint_validates_integrity(self, test_agent):
        """Restoring checkpoint should validate data integrity."""
        checkpoint_id = test_agent.create_checkpoint(
            name="test_checkpoint",
            data={"key": "value"}
        )

        # Restore should succeed with valid data
        restored_data = test_agent.restore_checkpoint(checkpoint_id)
        assert restored_data is not None

    def test_restore_nonexistent_checkpoint_raises_error(self, test_agent):
        """Restoring nonexistent checkpoint should raise ValueError."""
        with pytest.raises(ValueError, match="not found"):
            test_agent.restore_checkpoint("nonexistent-checkpoint-id")

    def test_restore_checkpoint_different_data_types(self, test_agent):
        """Checkpoint should handle various data types."""
        test_data = {
            "string": "hello",
            "int": 42,
            "float": 3.14,
            "bool": True,
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
            "none": None
        }

        checkpoint_id = test_agent.create_checkpoint(
            name="test_checkpoint",
            data=test_data
        )

        restored_data = test_agent.restore_checkpoint(checkpoint_id)

        assert restored_data == test_data
        assert isinstance(restored_data["string"], str)
        assert isinstance(restored_data["int"], int)
        assert isinstance(restored_data["float"], float)
        assert isinstance(restored_data["bool"], bool)
        assert isinstance(restored_data["list"], list)
        assert isinstance(restored_data["dict"], dict)

    def test_create_multiple_checkpoints(self, test_agent):
        """Agent should be able to create multiple checkpoints."""
        checkpoint_ids = []

        for i in range(3):
            checkpoint_id = test_agent.create_checkpoint(
                name=f"checkpoint_{i}",
                data={"step": i}
            )
            checkpoint_ids.append(checkpoint_id)

        # All IDs should be unique
        assert len(checkpoint_ids) == len(set(checkpoint_ids))

        # All checkpoints should be retrievable
        for i, checkpoint_id in enumerate(checkpoint_ids):
            data = test_agent.restore_checkpoint(checkpoint_id)
            assert data["step"] == i

    def test_checkpoint_with_large_data(self, test_agent):
        """Checkpoint should handle reasonably large data."""
        large_list = [f"item_{i}" for i in range(1000)]
        test_data = {
            "large_list": large_list,
            "metadata": {"count": len(large_list)}
        }

        checkpoint_id = test_agent.create_checkpoint(
            name="large_checkpoint",
            data=test_data
        )

        restored_data = test_agent.restore_checkpoint(checkpoint_id)

        assert len(restored_data["large_list"]) == 1000
        assert restored_data["metadata"]["count"] == 1000


class TestCheckpointDatabase:
    """Tests for checkpoint database operations."""

    @pytest.fixture
    def test_agent(self):
        """Create a test agent for checkpoint testing."""
        class TestCheckpointAgent(BaseAgent):
            def __init__(self):
                super().__init__(agent_id="test_checkpoint_db_agent")

            def get_contract(self):
                return {
                    "agent_id": self.agent_id,
                    "name": "Test Checkpoint DB Agent",
                    "description": "Agent for testing checkpoints in database",
                    "capabilities": []
                }

            def _register_message_handlers(self):
                pass  # No handlers needed for checkpoint testing

        return TestCheckpointAgent()

    def test_checkpoint_stored_in_database(self, test_agent):
        """Checkpoint should be stored in database."""
        checkpoint_id = test_agent.create_checkpoint(
            name="db_test",
            data={"test": "data"}
        )

        with db_manager.get_session() as session:
            checkpoint = session.query(Checkpoint).filter(
                Checkpoint.id == checkpoint_id
            ).first()

            assert checkpoint is not None
            assert checkpoint.name == "db_test"
            assert checkpoint.can_resume_from is True

    def test_checkpoint_has_timestamp(self, test_agent):
        """Checkpoint should have creation timestamp."""
        checkpoint_id = test_agent.create_checkpoint(
            name="timestamp_test",
            data={"test": "data"}
        )

        with db_manager.get_session() as session:
            checkpoint = session.query(Checkpoint).filter(
                Checkpoint.id == checkpoint_id
            ).first()

            assert checkpoint.created_at is not None

    def test_checkpoint_to_dict(self, test_agent):
        """Checkpoint should have to_dict method."""
        checkpoint_id = test_agent.create_checkpoint(
            name="dict_test",
            data={"test": "data"},
            workflow_id="wf-123"
        )

        with db_manager.get_session() as session:
            checkpoint = session.query(Checkpoint).filter(
                Checkpoint.id == checkpoint_id
            ).first()

            checkpoint_dict = checkpoint.to_dict()

            assert "id" in checkpoint_dict
            assert "workflow_id" in checkpoint_dict
            assert "name" in checkpoint_dict
            assert "created_at" in checkpoint_dict
            assert checkpoint_dict["id"] == checkpoint_id
            assert checkpoint_dict["workflow_id"] == "wf-123"


class TestCheckpointErrorHandling:
    """Tests for checkpoint error handling."""

    @pytest.fixture
    def test_agent(self):
        """Create a test agent."""
        class TestCheckpointAgent(BaseAgent):
            def __init__(self):
                super().__init__(agent_id="test_error_agent")

            def get_contract(self):
                return {
                    "agent_id": self.agent_id,
                    "name": "Test Error Agent",
                    "description": "Agent for error testing",
                    "capabilities": []
                }

            def _register_message_handlers(self):
                pass

        return TestCheckpointAgent()

    def test_restore_with_invalid_id_format(self, test_agent):
        """Restore should handle invalid checkpoint ID gracefully."""
        with pytest.raises(ValueError):
            test_agent.restore_checkpoint("invalid-id")

    def test_create_checkpoint_with_empty_name(self, test_agent):
        """Creating checkpoint with empty name should still work."""
        # Empty name is allowed, just not recommended
        checkpoint_id = test_agent.create_checkpoint(
            name="",
            data={"test": "data"}
        )
        assert checkpoint_id is not None

    def test_create_checkpoint_with_empty_data(self, test_agent):
        """Creating checkpoint with empty data should work."""
        checkpoint_id = test_agent.create_checkpoint(
            name="empty_data",
            data={}
        )

        restored = test_agent.restore_checkpoint(checkpoint_id)
        assert restored == {}


class TestCheckpointUseCases:
    """Tests for real-world checkpoint use cases."""

    @pytest.fixture
    def test_agent(self):
        """Create a test agent."""
        class TestWorkflowAgent(BaseAgent):
            def __init__(self):
                super().__init__(agent_id="workflow_agent")

            def get_contract(self):
                return {
                    "agent_id": self.agent_id,
                    "name": "Workflow Agent",
                    "description": "Agent for workflow testing",
                    "capabilities": []
                }

            def _register_message_handlers(self):
                pass

        return TestWorkflowAgent()

    def test_multi_step_workflow_with_checkpoints(self, test_agent):
        """Simulate multi-step workflow with checkpoints."""
        workflow_id = "wf-multi-step-test"

        # Step 1: Initial processing
        checkpoint_1 = test_agent.create_checkpoint(
            name="step_1_complete",
            data={"step": 1, "processed": 100},
            workflow_id=workflow_id
        )

        # Step 2: Further processing
        step_1_data = test_agent.restore_checkpoint(checkpoint_1)
        checkpoint_2 = test_agent.create_checkpoint(
            name="step_2_complete",
            data={
                "step": 2,
                "processed": step_1_data["processed"] + 100
            },
            workflow_id=workflow_id
        )

        # Step 3: Final processing
        step_2_data = test_agent.restore_checkpoint(checkpoint_2)
        checkpoint_3 = test_agent.create_checkpoint(
            name="step_3_complete",
            data={
                "step": 3,
                "processed": step_2_data["processed"] + 100,
                "complete": True
            },
            workflow_id=workflow_id
        )

        # Verify final state
        final_data = test_agent.restore_checkpoint(checkpoint_3)
        assert final_data["step"] == 3
        assert final_data["processed"] == 300
        assert final_data["complete"] is True

    def test_checkpoint_recovery_scenario(self, test_agent):
        """Simulate failure and recovery using checkpoints."""
        workflow_id = "wf-recovery-test"

        # Process some items
        checkpoint_id = test_agent.create_checkpoint(
            name="before_failure",
            data={
                "processed": 50,
                "failed": 0,
                "current_batch": 5
            },
            workflow_id=workflow_id
        )

        # Simulate failure and recovery
        recovered_state = test_agent.restore_checkpoint(checkpoint_id)

        # Continue from where we left off
        assert recovered_state["processed"] == 50
        assert recovered_state["current_batch"] == 5

        # Process remaining items
        final_checkpoint = test_agent.create_checkpoint(
            name="after_recovery",
            data={
                "processed": recovered_state["processed"] + 50,
                "failed": 0,
                "current_batch": 10
            },
            workflow_id=workflow_id
        )

        final_state = test_agent.restore_checkpoint(final_checkpoint)
        assert final_state["processed"] == 100
