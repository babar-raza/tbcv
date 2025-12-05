"""Test workflow pause/resume functionality.

Comprehensive tests for pausing and resuming workflows, including:
- Basic pause/resume operations
- Progress preservation
- State validation
- Concurrent operations
- Error handling
"""

import os
import sys
import pytest
import asyncio
import threading
import time
import uuid
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock

# Set environment before imports
os.environ.setdefault("TBCV_ENV", "test")
os.environ.setdefault("OLLAMA_ENABLED", "false")

# Import after environment
from core.database import db_manager, WorkflowState
from core.workflow_manager import WorkflowManager
from core.logging import get_logger

logger = get_logger(__name__)


@pytest.fixture
def workflow_manager(db_manager):
    """Create a fresh workflow manager for each test."""
    return WorkflowManager(db_manager)


@pytest.fixture
def sample_workflow_id(db_manager):
    """Create a sample workflow and return its ID."""
    workflow_id = f"test_workflow_{uuid.uuid4().hex[:8]}"

    with db_manager.get_session() as session:
        from core.database import Workflow

        workflow = Workflow(
            id=workflow_id,
            type="validate_directory",
            state=WorkflowState.RUNNING,
            input_params={"directory_path": "/test"},
            created_at=datetime.now(timezone.utc),
            progress_percent=0,
            current_step=0,
            total_steps=10
        )
        session.add(workflow)
        session.commit()

    return workflow_id


class TestPauseResumeBasics:
    """Test basic pause and resume operations."""

    def test_pause_running_workflow(self, workflow_manager, sample_workflow_id):
        """Test pausing a running workflow."""
        # Pause workflow
        result_state = workflow_manager.pause_workflow(sample_workflow_id)

        # Verify paused state returned
        assert result_state == WorkflowState.PAUSED

        # Verify workflow state in database
        workflow = db_manager.get_workflow(sample_workflow_id)
        assert workflow.state == WorkflowState.PAUSED

    def test_pause_sets_pause_flag(self, workflow_manager, sample_workflow_id):
        """Test that pause sets the control flag."""
        # Initialize control state as if workflow was running
        with workflow_manager._lock:
            workflow_manager._workflow_control[sample_workflow_id] = {
                "should_pause": False,
                "should_cancel": False,
                "is_running": True
            }

        # Pause workflow
        workflow_manager.pause_workflow(sample_workflow_id)

        # Verify flag is set
        with workflow_manager._lock:
            assert workflow_manager._workflow_control[sample_workflow_id]["should_pause"] is True

    def test_resume_paused_workflow(self, workflow_manager, sample_workflow_id):
        """Test resuming a paused workflow."""
        # First pause it
        workflow_manager.pause_workflow(sample_workflow_id)

        # Then resume
        result_state = workflow_manager.resume_workflow(sample_workflow_id)

        # Verify running state returned
        assert result_state == WorkflowState.RUNNING

        # Verify workflow state in database
        workflow = db_manager.get_workflow(sample_workflow_id)
        assert workflow.state == WorkflowState.RUNNING

    def test_resume_clears_pause_flag(self, workflow_manager, sample_workflow_id):
        """Test that resume clears the pause flag."""
        # Pause first
        workflow_manager.pause_workflow(sample_workflow_id)

        # Initialize control state
        with workflow_manager._lock:
            workflow_manager._workflow_control[sample_workflow_id] = {
                "should_pause": True,
                "should_cancel": False,
                "is_running": True
            }

        # Resume
        workflow_manager.resume_workflow(sample_workflow_id)

        # Verify flag is cleared
        with workflow_manager._lock:
            assert workflow_manager._workflow_control[sample_workflow_id]["should_pause"] is False


class TestPauseResumeValidation:
    """Test state validation for pause/resume operations."""

    def test_cannot_pause_completed_workflow(self, workflow_manager, db_manager):
        """Test that completed workflows cannot be paused."""
        # Create a completed workflow
        wf_id = f"test_completed_{uuid.uuid4().hex[:8]}"
        with db_manager.get_session() as session:
            from core.database import Workflow

            workflow = Workflow(
                id=wf_id,
                type="validate_directory",
                state=WorkflowState.COMPLETED,
                input_params={"directory_path": "/test"},
                created_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                progress_percent=100,
                current_step=10,
                total_steps=10
            )
            session.add(workflow)
            session.commit()

        # Attempt to pause - should fail
        with pytest.raises(ValueError, match="Cannot pause workflow"):
            workflow_manager.pause_workflow(wf_id)

    def test_cannot_pause_failed_workflow(self, workflow_manager, db_manager):
        """Test that failed workflows cannot be paused."""
        # Create a failed workflow
        wf_id = f"test_failed_{uuid.uuid4().hex[:8]}"
        with db_manager.get_session() as session:
            from core.database import Workflow

            workflow = Workflow(
                id=wf_id,
                type="validate_directory",
                state=WorkflowState.FAILED,
                input_params={"directory_path": "/test"},
                created_at=datetime.now(timezone.utc),
                error_message="Test error",
                progress_percent=50,
                current_step=5,
                total_steps=10
            )
            session.add(workflow)
            session.commit()

        # Attempt to pause - should fail
        with pytest.raises(ValueError, match="Cannot pause workflow"):
            workflow_manager.pause_workflow(wf_id)

    def test_cannot_pause_cancelled_workflow(self, workflow_manager, db_manager):
        """Test that cancelled workflows cannot be paused."""
        # Create a cancelled workflow
        wf_id = f"test_cancelled_{uuid.uuid4().hex[:8]}"
        with db_manager.get_session() as session:
            from core.database import Workflow

            workflow = Workflow(
                id=wf_id,
                type="validate_directory",
                state=WorkflowState.CANCELLED,
                input_params={"directory_path": "/test"},
                created_at=datetime.now(timezone.utc),
                progress_percent=30,
                current_step=3,
                total_steps=10
            )
            session.add(workflow)
            session.commit()

        # Attempt to pause - should fail
        with pytest.raises(ValueError, match="Cannot pause workflow"):
            workflow_manager.pause_workflow(wf_id)

    def test_cannot_resume_running_workflow(self, workflow_manager, sample_workflow_id):
        """Test that running workflows cannot be resumed."""
        # Try to resume a running workflow - should fail
        with pytest.raises(ValueError, match="is not paused"):
            workflow_manager.resume_workflow(sample_workflow_id)

    def test_cannot_resume_completed_workflow(self, workflow_manager, db_manager):
        """Test that completed workflows cannot be resumed."""
        # Create a completed workflow
        wf_id = f"test_completed_resume_{uuid.uuid4().hex[:8]}"
        with db_manager.get_session() as session:
            from core.database import Workflow

            workflow = Workflow(
                id=wf_id,
                type="validate_directory",
                state=WorkflowState.COMPLETED,
                input_params={"directory_path": "/test"},
                created_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                progress_percent=100,
                current_step=10,
                total_steps=10
            )
            session.add(workflow)
            session.commit()

        # Attempt to resume - should fail
        with pytest.raises(ValueError, match="is not paused"):
            workflow_manager.resume_workflow(wf_id)


class TestProgressPreservation:
    """Test that pause/resume preserves workflow progress."""

    def test_pause_preserves_progress(self, workflow_manager, db_manager):
        """Test that pause preserves workflow progress metrics."""
        # Create a workflow with progress
        wf_id = f"test_progress_{uuid.uuid4().hex[:8]}"
        with db_manager.get_session() as session:
            from core.database import Workflow

            workflow = Workflow(
                id=wf_id,
                type="validate_directory",
                state=WorkflowState.RUNNING,
                input_params={"directory_path": "/test"},
                created_at=datetime.now(timezone.utc),
                progress_percent=50,
                current_step=5,
                total_steps=10
            )
            session.add(workflow)
            session.commit()

        # Pause workflow
        workflow_manager.pause_workflow(wf_id)

        # Verify progress is preserved
        workflow = db_manager.get_workflow(wf_id)
        assert workflow.progress_percent == 50
        assert workflow.current_step == 5
        assert workflow.total_steps == 10

    def test_resume_preserves_progress(self, workflow_manager, db_manager):
        """Test that resume preserves workflow progress metrics."""
        # Create and pause a workflow with progress
        wf_id = f"test_resume_progress_{uuid.uuid4().hex[:8]}"
        with db_manager.get_session() as session:
            from core.database import Workflow

            workflow = Workflow(
                id=wf_id,
                type="validate_directory",
                state=WorkflowState.PAUSED,
                input_params={"directory_path": "/test"},
                created_at=datetime.now(timezone.utc),
                progress_percent=75,
                current_step=7,
                total_steps=10
            )
            session.add(workflow)
            session.commit()

        # Resume workflow
        workflow_manager.resume_workflow(wf_id)

        # Verify progress is still preserved
        workflow = db_manager.get_workflow(wf_id)
        assert workflow.progress_percent == 75
        assert workflow.current_step == 7
        assert workflow.total_steps == 10

    def test_pause_resume_cycle_preserves_progress(self, workflow_manager, db_manager):
        """Test that multiple pause/resume cycles preserve progress."""
        # Create a workflow
        wf_id = f"test_cycle_progress_{uuid.uuid4().hex[:8]}"
        with db_manager.get_session() as session:
            from core.database import Workflow

            workflow = Workflow(
                id=wf_id,
                type="validate_directory",
                state=WorkflowState.RUNNING,
                input_params={"directory_path": "/test"},
                created_at=datetime.now(timezone.utc),
                progress_percent=25,
                current_step=2,
                total_steps=10
            )
            session.add(workflow)
            session.commit()

        # Perform multiple pause/resume cycles
        for i in range(3):
            # Pause
            workflow_manager.pause_workflow(wf_id)

            # Simulate progress update
            db_manager.update_workflow(
                wf_id,
                progress_percent=25 + (i * 15),
                current_step=2 + (i * 1)
            )

            # Resume
            workflow_manager.resume_workflow(wf_id)

        # Verify final progress is preserved
        workflow = db_manager.get_workflow(wf_id)
        # i=0: 25+0=25, i=1: 25+15=40, i=2: 25+30=55
        assert workflow.progress_percent == 55
        # i=0: 2+0=2, i=1: 2+1=3, i=2: 2+2=4
        assert workflow.current_step == 4


class TestMultiplePauseResumeCycles:
    """Test multiple pause/resume cycles."""

    def test_multiple_pause_resume_cycles(self, workflow_manager, sample_workflow_id):
        """Test multiple pause/resume cycles on same workflow."""
        for cycle in range(3):
            # Pause
            pause_state = workflow_manager.pause_workflow(sample_workflow_id)
            assert pause_state == WorkflowState.PAUSED

            workflow = db_manager.get_workflow(sample_workflow_id)
            assert workflow.state == WorkflowState.PAUSED

            # Resume
            resume_state = workflow_manager.resume_workflow(sample_workflow_id)
            assert resume_state == WorkflowState.RUNNING

            workflow = db_manager.get_workflow(sample_workflow_id)
            assert workflow.state == WorkflowState.RUNNING

    def test_pause_resume_cycle_updates_state_correctly(self, workflow_manager, db_manager):
        """Test that each cycle properly updates workflow state."""
        # Create workflow
        wf_id = f"test_cycle_state_{uuid.uuid4().hex[:8]}"
        with db_manager.get_session() as session:
            from core.database import Workflow

            workflow = Workflow(
                id=wf_id,
                type="validate_directory",
                state=WorkflowState.RUNNING,
                input_params={"directory_path": "/test"},
                created_at=datetime.now(timezone.utc)
            )
            session.add(workflow)
            session.commit()

        states_observed = []

        # Cycle 1
        workflow_manager.pause_workflow(wf_id)
        states_observed.append(db_manager.get_workflow(wf_id).state)

        workflow_manager.resume_workflow(wf_id)
        states_observed.append(db_manager.get_workflow(wf_id).state)

        # Cycle 2
        workflow_manager.pause_workflow(wf_id)
        states_observed.append(db_manager.get_workflow(wf_id).state)

        workflow_manager.resume_workflow(wf_id)
        states_observed.append(db_manager.get_workflow(wf_id).state)

        # Verify state sequence
        expected = [
            WorkflowState.PAUSED,
            WorkflowState.RUNNING,
            WorkflowState.PAUSED,
            WorkflowState.RUNNING
        ]
        assert states_observed == expected


class TestConcurrentPauseResume:
    """Test concurrent pause/resume operations."""

    def test_concurrent_pause_operations(self, workflow_manager, db_manager):
        """Test pausing multiple workflows concurrently."""
        # Create multiple workflows with unique IDs
        workflow_ids = []
        for i in range(5):
            wf_id = f"test_concurrent_pause_{uuid.uuid4().hex[:8]}"
            with db_manager.get_session() as session:
                from core.database import Workflow

                workflow = Workflow(
                    id=wf_id,
                    type="validate_directory",
                    state=WorkflowState.RUNNING,
                    input_params={"directory_path": f"/test{i}"},
                    created_at=datetime.now(timezone.utc)
                )
                session.add(workflow)
                session.commit()
                workflow_ids.append(wf_id)

        # Pause all workflows in parallel using threads
        def pause_workflow(wf_id):
            workflow_manager.pause_workflow(wf_id)

        threads = []
        for wf_id in workflow_ids:
            t = threading.Thread(target=pause_workflow, args=(wf_id,))
            threads.append(t)
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join()

        # Verify all workflows are paused
        for wf_id in workflow_ids:
            workflow = db_manager.get_workflow(wf_id)
            assert workflow.state == WorkflowState.PAUSED

    def test_concurrent_resume_operations(self, workflow_manager, db_manager):
        """Test resuming multiple workflows concurrently."""
        # Create multiple paused workflows with unique IDs
        workflow_ids = []
        for i in range(5):
            wf_id = f"test_concurrent_resume_{uuid.uuid4().hex[:8]}"
            with db_manager.get_session() as session:
                from core.database import Workflow

                workflow = Workflow(
                    id=wf_id,
                    type="validate_directory",
                    state=WorkflowState.PAUSED,
                    input_params={"directory_path": f"/test{i}"},
                    created_at=datetime.now(timezone.utc)
                )
                session.add(workflow)
                session.commit()
                workflow_ids.append(wf_id)

        # Resume all workflows in parallel using threads
        def resume_workflow(wf_id):
            workflow_manager.resume_workflow(wf_id)

        threads = []
        for wf_id in workflow_ids:
            t = threading.Thread(target=resume_workflow, args=(wf_id,))
            threads.append(t)
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join()

        # Verify all workflows are running
        for wf_id in workflow_ids:
            workflow = db_manager.get_workflow(wf_id)
            assert workflow.state == WorkflowState.RUNNING

    def test_concurrent_pause_resume_cycles(self, workflow_manager, db_manager):
        """Test concurrent pause/resume cycles on different workflows."""
        # Create multiple workflows with unique IDs
        workflow_ids = []
        for i in range(3):
            wf_id = f"test_concurrent_cycle_{uuid.uuid4().hex[:8]}"
            with db_manager.get_session() as session:
                from core.database import Workflow

                workflow = Workflow(
                    id=wf_id,
                    type="validate_directory",
                    state=WorkflowState.RUNNING,
                    input_params={"directory_path": f"/test{i}"},
                    created_at=datetime.now(timezone.utc)
                )
                session.add(workflow)
                session.commit()
                workflow_ids.append(wf_id)

        # Perform pause/resume cycles
        def cycle_workflow(wf_id):
            for _ in range(2):
                workflow_manager.pause_workflow(wf_id)
                time.sleep(0.01)  # Small delay to allow interleaving
                workflow_manager.resume_workflow(wf_id)
                time.sleep(0.01)

        threads = []
        for wf_id in workflow_ids:
            t = threading.Thread(target=cycle_workflow, args=(wf_id,))
            threads.append(t)
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join()

        # Verify all workflows are in a valid state
        for wf_id in workflow_ids:
            workflow = db_manager.get_workflow(wf_id)
            assert workflow.state in [WorkflowState.RUNNING, WorkflowState.PAUSED]


class TestControlSignalHandling:
    """Test control signal handling during pause."""

    def test_check_control_signals_pause(self, workflow_manager, db_manager):
        """Test that pause signal is properly checked."""
        # Create workflow and initialize control state
        wf_id = f"test_signal_pause_{uuid.uuid4().hex[:8]}"
        with db_manager.get_session() as session:
            from core.database import Workflow

            workflow = Workflow(
                id=wf_id,
                type="validate_directory",
                state=WorkflowState.RUNNING,
                input_params={"directory_path": "/test"},
                created_at=datetime.now(timezone.utc)
            )
            session.add(workflow)
            session.commit()

        with workflow_manager._lock:
            workflow_manager._workflow_control[wf_id] = {
                "should_pause": False,
                "should_cancel": False,
                "is_running": True
            }

        # Verify normal operation continues
        assert workflow_manager._check_control_signals(wf_id) is True

        # Set pause flag
        with workflow_manager._lock:
            workflow_manager._workflow_control[wf_id]["should_pause"] = True

        # Start checking in a thread to avoid blocking
        def check_and_clear():
            # This should sleep while pause is true
            time.sleep(0.1)
            with workflow_manager._lock:
                workflow_manager._workflow_control[wf_id]["should_pause"] = False

        check_thread = threading.Thread(target=check_and_clear)
        check_thread.start()

        # Call check (should block briefly then resume)
        start = time.time()
        result = workflow_manager._check_control_signals(wf_id)
        elapsed = time.time() - start

        check_thread.join()

        # Should have blocked for approximately 0.1 seconds
        assert result is True
        assert elapsed >= 0.05  # Allow some timing variance

    def test_check_control_signals_cancel(self, workflow_manager):
        """Test that cancel signal is properly checked."""
        with workflow_manager._lock:
            workflow_manager._workflow_control["test_signal_cancel_001"] = {
                "should_pause": False,
                "should_cancel": False,
                "is_running": True
            }

        # Should continue normally
        assert workflow_manager._check_control_signals("test_signal_cancel_001") is True

        # Set cancel flag
        with workflow_manager._lock:
            workflow_manager._workflow_control["test_signal_cancel_001"]["should_cancel"] = True

        # Should return False (stop execution)
        assert workflow_manager._check_control_signals("test_signal_cancel_001") is False


class TestErrorHandling:
    """Test error handling for pause/resume operations."""

    def test_pause_nonexistent_workflow(self, workflow_manager):
        """Test pausing a workflow that doesn't exist."""
        with pytest.raises(ValueError, match="not running|not found"):
            workflow_manager.pause_workflow("nonexistent_workflow_id")

    def test_resume_nonexistent_workflow(self, workflow_manager):
        """Test resuming a workflow that doesn't exist."""
        with pytest.raises(ValueError, match="not found"):
            workflow_manager.resume_workflow("nonexistent_workflow_id")

    def test_pause_workflow_not_in_control_dict(self, workflow_manager, db_manager):
        """Test pausing workflow that's not in control dict but exists in DB."""
        # Create a workflow
        wf_id = f"test_not_in_control_{uuid.uuid4().hex[:8]}"
        with db_manager.get_session() as session:
            from core.database import Workflow

            workflow = Workflow(
                id=wf_id,
                type="validate_directory",
                state=WorkflowState.RUNNING,
                input_params={"directory_path": "/test"},
                created_at=datetime.now(timezone.utc)
            )
            session.add(workflow)
            session.commit()

        # Attempt to pause without control state - should succeed since it's in RUNNING state
        # The new implementation allows pausing workflows not in control dict
        result = workflow_manager.pause_workflow(wf_id)
        assert result == WorkflowState.PAUSED


class TestThreadSafety:
    """Test thread safety of pause/resume operations."""

    def test_pause_resume_thread_safety(self, workflow_manager, db_manager):
        """Test that pause/resume operations are thread-safe."""
        # Create a workflow
        wf_id = f"test_thread_safety_{uuid.uuid4().hex[:8]}"
        with db_manager.get_session() as session:
            from core.database import Workflow

            workflow = Workflow(
                id=wf_id,
                type="validate_directory",
                state=WorkflowState.RUNNING,
                input_params={"directory_path": "/test"},
                created_at=datetime.now(timezone.utc),
                progress_percent=0
            )
            session.add(workflow)
            session.commit()

        # Initialize control state
        with workflow_manager._lock:
            workflow_manager._workflow_control[wf_id] = {
                "should_pause": False,
                "should_cancel": False,
                "is_running": True
            }

        errors = []

        def pause_operation():
            try:
                workflow_manager.pause_workflow(wf_id)
            except Exception as e:
                errors.append(("pause", str(e)))

        def resume_operation():
            try:
                # Give pause time to complete first
                time.sleep(0.05)
                workflow_manager.resume_workflow(wf_id)
            except Exception as e:
                errors.append(("resume", str(e)))

        # Run pause and resume concurrently
        t1 = threading.Thread(target=pause_operation)
        t2 = threading.Thread(target=resume_operation)

        t1.start()
        t2.start()

        t1.join()
        t2.join()

        # Should have no errors due to proper locking
        assert len(errors) == 0, f"Unexpected errors: {errors}"


class TestWorkflowStateTransitions:
    """Test valid state transitions for workflows."""

    def test_state_transition_running_to_paused(self, workflow_manager, sample_workflow_id):
        """Test state transition from RUNNING to PAUSED."""
        workflow_manager.pause_workflow(sample_workflow_id)
        workflow = db_manager.get_workflow(sample_workflow_id)
        assert workflow.state == WorkflowState.PAUSED

    def test_state_transition_paused_to_running(self, workflow_manager, sample_workflow_id):
        """Test state transition from PAUSED to RUNNING."""
        workflow_manager.pause_workflow(sample_workflow_id)
        workflow_manager.resume_workflow(sample_workflow_id)
        workflow = db_manager.get_workflow(sample_workflow_id)
        assert workflow.state == WorkflowState.RUNNING

    def test_cannot_transition_paused_to_paused(self, workflow_manager, db_manager):
        """Test that paused workflow cannot be paused again."""
        # Create paused workflow
        wf_id = f"test_paused_paused_{uuid.uuid4().hex[:8]}"
        with db_manager.get_session() as session:
            from core.database import Workflow

            workflow = Workflow(
                id=wf_id,
                type="validate_directory",
                state=WorkflowState.PAUSED,
                input_params={"directory_path": "/test"},
                created_at=datetime.now(timezone.utc)
            )
            session.add(workflow)
            session.commit()

        # Attempt to pause again - should fail
        with pytest.raises(ValueError, match="Cannot pause workflow"):
            workflow_manager.pause_workflow(wf_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
