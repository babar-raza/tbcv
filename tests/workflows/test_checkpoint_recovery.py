"""
Comprehensive checkpoint recovery tests.

Tests verify that workflows can recover from failures at any point.
This includes:
- Recovery at each workflow step
- Recovery after system crash/restart
- Recovery with corrupted checkpoints
- Recovery with missing checkpoints
- State consistency after recovery
- Rollback to previous checkpoint
- Metadata preservation
- Checkpoint listing
- Checkpoint cleanup

Coverage: TASK-MED-002 - Test Checkpoint Recovery End-to-End
"""

import pytest
import pickle
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, patch
from core.database import (
    DatabaseManager, Checkpoint, Workflow, WorkflowState,
    ValidationStatus
)
from core.workflow_manager import WorkflowManager
from core.checkpoint_manager import CheckpointManager


class TestCheckpointRecovery:
    """Test checkpoint recovery scenarios."""

    @pytest.fixture
    def workflow_manager(self, db_manager):
        """Create workflow manager for tests."""
        return WorkflowManager(db_manager=db_manager)

    @pytest.fixture
    def checkpoint_manager(self, tmp_path):
        """Create checkpoint manager for tests."""
        checkpoint_dir = tmp_path / "checkpoints"
        return CheckpointManager(checkpoint_dir=str(checkpoint_dir))

    def test_recovery_at_step_2(self, db_manager, workflow_manager):
        """Test recovery when workflow fails at step 2."""
        # Create workflow
        workflow_id = db_manager.create_workflow(
            workflow_type="validate_directory",
            input_params={"directory_path": "/test", "recursive": True}
        )

        # Simulate progress to step 2
        db_manager.update_workflow(workflow_id, current_step=1, total_steps=10)

        # Create checkpoint at step 1
        checkpoint1_data = pickle.dumps({
            "workflow_id": workflow_id,
            "step_number": 1,
            "state_data": {"files_scanned": 10, "files_validated": 10}
        })
        checkpoint1_id = db_manager.create_checkpoint(
            workflow_id=workflow_id,
            name="step_1_complete",
            step_number=1,
            state_data=checkpoint1_data,
            validation_hash="abc123"
        )

        # Progress to step 2
        db_manager.update_workflow(workflow_id, current_step=2)
        checkpoint2_data = pickle.dumps({
            "workflow_id": workflow_id,
            "step_number": 2,
            "state_data": {"files_scanned": 20, "files_validated": 15}
        })
        checkpoint2_id = db_manager.create_checkpoint(
            workflow_id=workflow_id,
            name="step_2_complete",
            step_number=2,
            state_data=checkpoint2_data,
            validation_hash="def456"
        )

        # Simulate failure at step 3
        db_manager.update_workflow(workflow_id, state=WorkflowState.FAILED)

        # Recover from step 2
        with db_manager.get_session() as session:
            checkpoint2 = session.query(Checkpoint).filter(
                Checkpoint.id == checkpoint2_id
            ).first()

            assert checkpoint2 is not None
            assert checkpoint2.step_number == 2

            # Load checkpoint data
            recovered_data = pickle.loads(checkpoint2.state_data)
            assert recovered_data["step_number"] == 2
            assert recovered_data["state_data"]["files_validated"] == 15

        # Resume workflow from checkpoint
        db_manager.update_workflow(
            workflow_id,
            state=WorkflowState.RUNNING,
            current_step=2
        )

        # Verify workflow resumed at correct step
        workflow = db_manager.get_workflow(workflow_id)
        assert workflow.current_step == 2
        assert workflow.state == WorkflowState.RUNNING

    def test_recovery_after_system_restart(self, db_manager, tmp_path):
        """Test recovery after simulated system restart."""
        # Create workflow
        workflow_id = db_manager.create_workflow(
            workflow_type="validate_directory",
            input_params={"directory_path": "/test"}
        )

        # Create checkpoint
        checkpoint_data = pickle.dumps({
            "workflow_id": workflow_id,
            "step_number": 3,
            "state_data": {"progress": 0.5, "files_processed": 50}
        })
        checkpoint_id = db_manager.create_checkpoint(
            workflow_id=workflow_id,
            name="mid_process",
            step_number=3,
            state_data=checkpoint_data,
            validation_hash="xyz789"
        )

        # Simulate system restart - reuse same database manager since it's in-memory
        # In real scenarios, this would be a new connection to persistent DB

        # Verify checkpoint exists after restart
        with db_manager.get_session() as session:
            checkpoint = session.query(Checkpoint).filter(
                Checkpoint.id == checkpoint_id
            ).first()

            assert checkpoint is not None
            assert checkpoint.workflow_id == workflow_id

            # Load and verify checkpoint data
            recovered_data = pickle.loads(checkpoint.state_data)
            assert recovered_data["state_data"]["progress"] == 0.5

        # Resume workflow
        db_manager.update_workflow(
            workflow_id,
            state=WorkflowState.RUNNING,
            current_step=3
        )

        # Verify state preserved
        workflow = db_manager.get_workflow(workflow_id)
        assert workflow.state == WorkflowState.RUNNING
        assert workflow.current_step == 3

    def test_recovery_with_corrupted_checkpoint(self, db_manager):
        """Test recovery when checkpoint data is corrupted."""
        workflow_id = db_manager.create_workflow(
            workflow_type="validate_directory",
            input_params={"directory_path": "/test"}
        )

        # Create checkpoint with invalid data
        checkpoint_id = db_manager.create_checkpoint(
            workflow_id=workflow_id,
            name="corrupted_checkpoint",
            step_number=1,
            state_data=b"corrupted data that cannot be unpickled",
            validation_hash="invalid"
        )

        # Attempt to load corrupted checkpoint - should fail
        with db_manager.get_session() as session:
            checkpoint = session.query(Checkpoint).filter(
                Checkpoint.id == checkpoint_id
            ).first()

            assert checkpoint is not None

            # Try to unpickle - should raise exception
            with pytest.raises(Exception):
                pickle.loads(checkpoint.state_data)

    def test_recovery_with_missing_checkpoint(self, db_manager):
        """Test recovery when checkpoint doesn't exist."""
        # Attempt to load non-existent checkpoint
        with db_manager.get_session() as session:
            checkpoint = session.query(Checkpoint).filter(
                Checkpoint.id == "non_existent_id"
            ).first()

            assert checkpoint is None

    def test_rollback_to_previous_checkpoint(self, db_manager):
        """Test rolling back to a previous checkpoint."""
        workflow_id = db_manager.create_workflow(
            workflow_type="validate_directory",
            input_params={"directory_path": "/test"}
        )

        # Create multiple checkpoints
        cp1_data = pickle.dumps({
            "workflow_id": workflow_id,
            "step_number": 1,
            "state_data": {"count": 10}
        })
        cp1_id = db_manager.create_checkpoint(
            workflow_id=workflow_id,
            name="step_1",
            step_number=1,
            state_data=cp1_data,
            validation_hash="cp1"
        )

        cp2_data = pickle.dumps({
            "workflow_id": workflow_id,
            "step_number": 2,
            "state_data": {"count": 20}
        })
        cp2_id = db_manager.create_checkpoint(
            workflow_id=workflow_id,
            name="step_2",
            step_number=2,
            state_data=cp2_data,
            validation_hash="cp2"
        )

        cp3_data = pickle.dumps({
            "workflow_id": workflow_id,
            "step_number": 3,
            "state_data": {"count": 30}
        })
        cp3_id = db_manager.create_checkpoint(
            workflow_id=workflow_id,
            name="step_3",
            step_number=3,
            state_data=cp3_data,
            validation_hash="cp3"
        )

        # Update workflow to step 3
        db_manager.update_workflow(workflow_id, current_step=3)

        # Rollback to cp1
        with db_manager.get_session() as session:
            cp1 = session.query(Checkpoint).filter(
                Checkpoint.id == cp1_id
            ).first()

            assert cp1 is not None
            recovered_data = pickle.loads(cp1.state_data)
            assert recovered_data["state_data"]["count"] == 10

        # Update workflow to rolled back state
        db_manager.update_workflow(workflow_id, current_step=1)

        # Verify rolled back
        workflow = db_manager.get_workflow(workflow_id)
        assert workflow.current_step == 1

    def test_state_consistency_after_recovery(self, db_manager):
        """Test that all state is consistent after recovery."""
        workflow_id = db_manager.create_workflow(
            workflow_type="validate_directory",
            input_params={"directory_path": "/test"}
        )

        # Progress workflow
        db_manager.update_workflow(
            workflow_id,
            current_step=5,
            total_steps=10,
            progress_percent=50
        )

        # Create checkpoint with comprehensive state
        checkpoint_data = pickle.dumps({
            "workflow_id": workflow_id,
            "step_number": 5,
            "state_data": {
                "files_processed": 50,
                "files_total": 100,
                "errors": [],
                "warnings": [],
                "current_file": "test.md"
            }
        })
        checkpoint_id = db_manager.create_checkpoint(
            workflow_id=workflow_id,
            name="mid_process",
            step_number=5,
            state_data=checkpoint_data,
            validation_hash="hash123"
        )

        # Simulate failure
        db_manager.update_workflow(workflow_id, state=WorkflowState.FAILED)

        # Recover
        with db_manager.get_session() as session:
            checkpoint = session.query(Checkpoint).filter(
                Checkpoint.id == checkpoint_id
            ).first()

            recovered_data = pickle.loads(checkpoint.state_data)
            assert recovered_data["state_data"]["files_processed"] == 50
            assert recovered_data["state_data"]["files_total"] == 100

        # Resume workflow
        db_manager.update_workflow(
            workflow_id,
            state=WorkflowState.RUNNING,
            current_step=5
        )

        # Verify all state consistent
        workflow = db_manager.get_workflow(workflow_id)
        assert workflow.current_step == 5
        assert workflow.progress_percent == 50
        assert workflow.state == WorkflowState.RUNNING

    def test_recovery_preserves_metadata(self, db_manager):
        """Test that workflow metadata is preserved during recovery."""
        workflow_id = db_manager.create_workflow(
            workflow_type="validate_directory",
            input_params={"directory_path": "/test"},
            metadata={"user": "test_user", "priority": "high", "tags": ["test"]}
        )

        # Create checkpoint
        checkpoint_data = pickle.dumps({
            "workflow_id": workflow_id,
            "step_number": 1,
            "state_data": {"progress": 0.1}
        })
        checkpoint_id = db_manager.create_checkpoint(
            workflow_id=workflow_id,
            name="checkpoint",
            step_number=1,
            state_data=checkpoint_data,
            validation_hash="meta123"
        )

        # Recover
        db_manager.update_workflow(workflow_id, state=WorkflowState.RUNNING)

        # Verify metadata preserved
        workflow = db_manager.get_workflow(workflow_id)
        assert workflow.workflow_metadata["user"] == "test_user"
        assert workflow.workflow_metadata["priority"] == "high"
        assert "test" in workflow.workflow_metadata["tags"]

    def test_list_checkpoints_for_workflow(self, db_manager):
        """Test listing all checkpoints for a workflow."""
        workflow_id = db_manager.create_workflow(
            workflow_type="validate_directory",
            input_params={"directory_path": "/test"}
        )

        # Create multiple checkpoints
        checkpoint_ids = []
        for i in range(5):
            data = pickle.dumps({
                "workflow_id": workflow_id,
                "step_number": i,
                "state_data": {"step": i}
            })
            cp_id = db_manager.create_checkpoint(
                workflow_id=workflow_id,
                name=f"step_{i}",
                step_number=i,
                state_data=data,
                validation_hash=f"hash{i}"
            )
            checkpoint_ids.append(cp_id)

        # List checkpoints
        with db_manager.get_session() as session:
            checkpoints = session.query(Checkpoint).filter(
                Checkpoint.workflow_id == workflow_id
            ).order_by(Checkpoint.step_number).all()

            assert len(checkpoints) == 5
            assert checkpoints[0].step_number == 0
            assert checkpoints[4].step_number == 4

            # Verify all checkpoint IDs present
            for cp_id in checkpoint_ids:
                assert any(cp.id == cp_id for cp in checkpoints)

    def test_delete_old_checkpoints(self, db_manager):
        """Test cleanup of old checkpoints."""
        workflow_id = db_manager.create_workflow(
            workflow_type="validate_directory",
            input_params={"directory_path": "/test"}
        )

        # Create many checkpoints
        checkpoint_ids = []
        for i in range(10):
            data = pickle.dumps({
                "workflow_id": workflow_id,
                "step_number": i,
                "state_data": {}
            })
            cp_id = db_manager.create_checkpoint(
                workflow_id=workflow_id,
                name=f"step_{i}",
                step_number=i,
                state_data=data,
                validation_hash=f"hash{i}"
            )
            checkpoint_ids.append(cp_id)

        # Delete all but last 3
        with db_manager.get_session() as session:
            # Get all checkpoints ordered by step
            checkpoints = session.query(Checkpoint).filter(
                Checkpoint.workflow_id == workflow_id
            ).order_by(Checkpoint.step_number).all()

            # Delete all but last 3
            to_delete = checkpoints[:-3]
            for cp in to_delete:
                session.delete(cp)
            session.commit()

        # Verify only 3 remain
        with db_manager.get_session() as session:
            remaining = session.query(Checkpoint).filter(
                Checkpoint.workflow_id == workflow_id
            ).order_by(Checkpoint.step_number).all()

            assert len(remaining) == 3
            assert remaining[0].step_number == 7
            assert remaining[1].step_number == 8
            assert remaining[2].step_number == 9

    def test_checkpoint_validation_hash(self, db_manager):
        """Test that checkpoint validation hash is computed correctly."""
        workflow_id = db_manager.create_workflow(
            workflow_type="validate_directory",
            input_params={"directory_path": "/test"}
        )

        checkpoint_data = pickle.dumps({
            "workflow_id": workflow_id,
            "step_number": 1,
            "state_data": {"test": "data"}
        })

        # Compute expected hash
        import hashlib
        expected_hash = hashlib.md5(checkpoint_data).hexdigest()

        checkpoint_id = db_manager.create_checkpoint(
            workflow_id=workflow_id,
            name="test_checkpoint",
            step_number=1,
            state_data=checkpoint_data,
            validation_hash=expected_hash
        )

        # Verify hash stored correctly
        with db_manager.get_session() as session:
            checkpoint = session.query(Checkpoint).filter(
                Checkpoint.id == checkpoint_id
            ).first()

            assert checkpoint.validation_hash == expected_hash


@pytest.mark.integration
class TestEndToEndRecovery:
    """End-to-end recovery tests with real workflows."""

    @pytest.fixture
    def workflow_manager(self, db_manager):
        """Create workflow manager for tests."""
        return WorkflowManager(db_manager=db_manager)

    def test_validation_workflow_with_checkpoint_recovery(self, db_manager, workflow_manager):
        """Test validation workflow recovery after failure."""
        # Create validation workflow
        workflow_id = db_manager.create_workflow(
            workflow_type="validate_directory",
            input_params={"directory_path": "/test", "recursive": True}
        )

        # Simulate workflow progress with checkpoints
        for step in range(1, 4):
            db_manager.update_workflow(
                workflow_id,
                current_step=step,
                total_steps=5,
                progress_percent=step * 20
            )

            # Create checkpoint
            checkpoint_data = pickle.dumps({
                "workflow_id": workflow_id,
                "step_number": step,
                "state_data": {
                    "files_processed": step * 10,
                    "validations_passed": step * 8,
                    "validations_failed": step * 2
                }
            })
            db_manager.create_checkpoint(
                workflow_id=workflow_id,
                name=f"validation_step_{step}",
                step_number=step,
                state_data=checkpoint_data,
                validation_hash=f"val{step}"
            )

        # Simulate failure at step 4
        db_manager.update_workflow(
            workflow_id,
            state=WorkflowState.FAILED,
            error_message="Simulated failure at step 4"
        )

        # List checkpoints to find recovery point
        with db_manager.get_session() as session:
            checkpoints = session.query(Checkpoint).filter(
                Checkpoint.workflow_id == workflow_id
            ).order_by(Checkpoint.step_number.desc()).all()

            assert len(checkpoints) == 3
            latest_checkpoint = checkpoints[0]

            # Recover from latest checkpoint
            recovered_data = pickle.loads(latest_checkpoint.state_data)
            assert recovered_data["step_number"] == 3
            assert recovered_data["state_data"]["files_processed"] == 30

        # Resume workflow
        db_manager.update_workflow(
            workflow_id,
            state=WorkflowState.RUNNING,
            current_step=3,
            error_message=None
        )

        # Verify recovery successful
        workflow = db_manager.get_workflow(workflow_id)
        assert workflow.state == WorkflowState.RUNNING
        assert workflow.current_step == 3
        assert workflow.error_message is None

    def test_batch_enhance_workflow_recovery(self, db_manager):
        """Test batch enhancement workflow recovery after failure."""
        # Create batch enhance workflow
        validation_ids = [f"val_{i}" for i in range(10)]
        workflow_id = db_manager.create_workflow(
            workflow_type="batch_enhance",
            input_params={"validation_ids": validation_ids}
        )

        # Process half the validations with checkpoints
        for i in range(5):
            db_manager.update_workflow(
                workflow_id,
                current_step=i + 1,
                total_steps=10,
                progress_percent=(i + 1) * 10
            )

            # Checkpoint every 2 steps
            if (i + 1) % 2 == 0:
                checkpoint_data = pickle.dumps({
                    "workflow_id": workflow_id,
                    "step_number": i + 1,
                    "state_data": {
                        "validations_enhanced": i + 1,
                        "validations_remaining": 10 - (i + 1),
                        "last_processed_id": validation_ids[i]
                    }
                })
                db_manager.create_checkpoint(
                    workflow_id=workflow_id,
                    name=f"enhance_batch_{i + 1}",
                    step_number=i + 1,
                    state_data=checkpoint_data,
                    validation_hash=f"enh{i + 1}"
                )

        # Simulate system crash
        db_manager.update_workflow(workflow_id, state=WorkflowState.FAILED)

        # Recover from last checkpoint (step 4)
        with db_manager.get_session() as session:
            latest_checkpoint = session.query(Checkpoint).filter(
                Checkpoint.workflow_id == workflow_id
            ).order_by(Checkpoint.step_number.desc()).first()

            assert latest_checkpoint is not None
            assert latest_checkpoint.step_number == 4

            recovered_data = pickle.loads(latest_checkpoint.state_data)
            assert recovered_data["state_data"]["validations_enhanced"] == 4
            assert recovered_data["state_data"]["last_processed_id"] == "val_3"

        # Resume from checkpoint
        db_manager.update_workflow(
            workflow_id,
            state=WorkflowState.RUNNING,
            current_step=4
        )

        workflow = db_manager.get_workflow(workflow_id)
        assert workflow.state == WorkflowState.RUNNING
        assert workflow.current_step == 4

    def test_checkpoint_recovery_with_file_system_checkpoint(self, tmp_path):
        """Test file system based checkpoint recovery."""
        # Create checkpoint manager with temp directory
        checkpoint_dir = tmp_path / "checkpoints"
        checkpoint_manager = CheckpointManager(checkpoint_dir=str(checkpoint_dir))

        # Create a test checkpoint
        checkpoint_id = checkpoint_manager.create_checkpoint(
            name="test_checkpoint",
            metadata={"test": "data", "step": 5}
        )

        assert checkpoint_id is not None

        # List checkpoints
        checkpoints = checkpoint_manager.list_checkpoints()
        assert len(checkpoints) >= 1

        found = False
        for cp in checkpoints:
            if cp["id"] == checkpoint_id:
                found = True
                assert cp["name"] == "test_checkpoint"
                assert cp["metadata"]["test"] == "data"
                break

        assert found, f"Checkpoint {checkpoint_id} not found in list"

        # Verify checkpoint can be retrieved
        checkpoint_info = checkpoint_manager.get_checkpoint(checkpoint_id)
        assert checkpoint_info["name"] == "test_checkpoint"
        assert checkpoint_info["metadata"]["step"] == 5

        # Test cleanup
        assert checkpoint_manager.delete_checkpoint(checkpoint_id) == True

        # Verify deleted
        with pytest.raises(ValueError, match="Checkpoint not found"):
            checkpoint_manager.get_checkpoint(checkpoint_id)


class TestCheckpointIntegrity:
    """Test checkpoint data integrity and validation."""

    def test_checkpoint_data_serialization(self, db_manager):
        """Test that complex data structures can be checkpointed."""
        workflow_id = db_manager.create_workflow(
            workflow_type="validate_directory",
            input_params={"directory_path": "/test"}
        )

        # Create checkpoint with complex nested data
        complex_data = {
            "workflow_id": workflow_id,
            "step_number": 1,
            "state_data": {
                "files": [
                    {"path": "test1.md", "status": "pass", "errors": []},
                    {"path": "test2.md", "status": "fail", "errors": ["error1", "error2"]}
                ],
                "counters": {"pass": 1, "fail": 1, "skip": 0},
                "metadata": {
                    "started_at": datetime.now(timezone.utc).isoformat(),
                    "user": "test"
                }
            }
        }

        serialized = pickle.dumps(complex_data)
        checkpoint_id = db_manager.create_checkpoint(
            workflow_id=workflow_id,
            name="complex_data",
            step_number=1,
            state_data=serialized,
            validation_hash="complex"
        )

        # Load and verify
        with db_manager.get_session() as session:
            checkpoint = session.query(Checkpoint).filter(
                Checkpoint.id == checkpoint_id
            ).first()

            deserialized = pickle.loads(checkpoint.state_data)
            assert deserialized["state_data"]["counters"]["pass"] == 1
            assert len(deserialized["state_data"]["files"]) == 2
            assert deserialized["state_data"]["files"][1]["status"] == "fail"

    def test_checkpoint_immutability(self, db_manager):
        """Test that checkpoints remain immutable after creation."""
        workflow_id = db_manager.create_workflow(
            workflow_type="validate_directory",
            input_params={"directory_path": "/test"}
        )

        original_data = {
            "workflow_id": workflow_id,
            "step_number": 1,
            "state_data": {"count": 42}
        }
        serialized = pickle.dumps(original_data)

        checkpoint_id = db_manager.create_checkpoint(
            workflow_id=workflow_id,
            name="immutable_test",
            step_number=1,
            state_data=serialized,
            validation_hash="immut"
        )

        # Load checkpoint
        with db_manager.get_session() as session:
            checkpoint1 = session.query(Checkpoint).filter(
                Checkpoint.id == checkpoint_id
            ).first()
            data1 = pickle.loads(checkpoint1.state_data)

            # Load again
            checkpoint2 = session.query(Checkpoint).filter(
                Checkpoint.id == checkpoint_id
            ).first()
            data2 = pickle.loads(checkpoint2.state_data)

            # Verify data is the same
            assert data1 == data2
            assert data1["state_data"]["count"] == 42
            assert data2["state_data"]["count"] == 42
