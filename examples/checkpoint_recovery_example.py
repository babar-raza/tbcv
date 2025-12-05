"""
Checkpoint Recovery Example

This example demonstrates how to use checkpoint recovery in TBCV workflows.
It shows:
1. Creating workflows with checkpoints
2. Simulating failures
3. Recovering from checkpoints
4. Best practices for checkpoint management

Usage:
    python examples/checkpoint_recovery_example.py
"""

import time
import pickle
from pathlib import Path
from datetime import datetime, timezone

from core.database import DatabaseManager, WorkflowState
from core.workflow_manager import WorkflowManager
from core.checkpoint_manager import CheckpointManager


def example_1_basic_checkpoint_recovery():
    """
    Example 1: Basic checkpoint creation and recovery.

    This example shows how to create a workflow, save checkpoints,
    simulate a failure, and recover.
    """
    print("\n" + "=" * 60)
    print("Example 1: Basic Checkpoint Recovery")
    print("=" * 60)

    # Initialize managers
    db = DatabaseManager()
    workflow_mgr = WorkflowManager(db_manager=db)

    # Create a validation workflow
    workflow_id = db.create_workflow(
        workflow_type="validate_directory",
        input_params={"directory_path": "./docs", "recursive": True}
    )
    print(f"\n1. Created workflow: {workflow_id}")

    # Simulate workflow progress with checkpoints
    print("\n2. Simulating workflow progress...")
    for step in range(1, 4):
        print(f"   - Processing step {step}...")

        # Update workflow progress
        db.update_workflow(
            workflow_id,
            current_step=step,
            total_steps=5,
            progress_percent=step * 20
        )

        # Create checkpoint
        state_data = pickle.dumps({
            "workflow_id": workflow_id,
            "step_number": step,
            "state_data": {
                "files_processed": step * 10,
                "validations_passed": step * 8,
                "validations_failed": step * 2
            }
        })

        checkpoint_id = db.create_checkpoint(
            workflow_id=workflow_id,
            name=f"step_{step}_complete",
            step_number=step,
            state_data=state_data,
            validation_hash=f"hash{step}"
        )
        print(f"   - Created checkpoint: {checkpoint_id}")

    # Simulate failure
    print("\n3. Simulating failure at step 4...")
    db.update_workflow(
        workflow_id,
        state=WorkflowState.FAILED,
        error_message="Simulated failure for demonstration"
    )

    # List available checkpoints
    print("\n4. Listing available checkpoints...")
    with db.get_session() as session:
        from core.database import Checkpoint
        checkpoints = session.query(Checkpoint).filter(
            Checkpoint.workflow_id == workflow_id
        ).order_by(Checkpoint.step_number).all()

        for cp in checkpoints:
            print(f"   - Checkpoint {cp.id}: Step {cp.step_number}, Name: {cp.name}")

    # Recover from last checkpoint
    print("\n5. Recovering from last checkpoint...")
    latest_checkpoint = checkpoints[-1]
    recovered_data = pickle.loads(latest_checkpoint.state_data)

    print(f"   - Recovered state from step {recovered_data['step_number']}")
    print(f"   - Files processed: {recovered_data['state_data']['files_processed']}")
    print(f"   - Validations passed: {recovered_data['state_data']['validations_passed']}")

    # Resume workflow
    db.update_workflow(
        workflow_id,
        state=WorkflowState.RUNNING,
        current_step=latest_checkpoint.step_number,
        error_message=None
    )
    print(f"\n6. Workflow resumed at step {latest_checkpoint.step_number}")

    # Complete the workflow
    for step in range(latest_checkpoint.step_number + 1, 6):
        print(f"   - Processing step {step}...")
        db.update_workflow(
            workflow_id,
            current_step=step,
            progress_percent=step * 20
        )

    db.update_workflow(
        workflow_id,
        state=WorkflowState.COMPLETED,
        completed_at=datetime.now(timezone.utc)
    )
    print("\n7. Workflow completed successfully!")


def example_2_system_checkpoint():
    """
    Example 2: System-level checkpoint creation and recovery.

    This example shows how to create system checkpoints that include
    the entire database state.
    """
    print("\n" + "=" * 60)
    print("Example 2: System Checkpoint")
    print("=" * 60)

    # Create checkpoint manager
    checkpoint_mgr = CheckpointManager()

    # Create system checkpoint
    print("\n1. Creating system checkpoint...")
    checkpoint_id = checkpoint_mgr.create_checkpoint(
        name="pre_maintenance_backup",
        metadata={
            "reason": "Before system maintenance",
            "user": "admin",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )
    print(f"   - Created system checkpoint: {checkpoint_id}")

    # List system checkpoints
    print("\n2. Listing system checkpoints...")
    checkpoints = checkpoint_mgr.list_checkpoints()
    for cp in checkpoints:
        print(f"   - {cp['id']}: {cp['name']} (Created: {cp['created_at']})")

    # Validate checkpoint
    print("\n3. Validating checkpoint...")
    is_valid = checkpoint_mgr.validate_checkpoint(checkpoint_id)
    print(f"   - Checkpoint valid: {is_valid}")

    if is_valid:
        print("\n4. Checkpoint is ready for recovery if needed")
    else:
        print("\n4. WARNING: Checkpoint validation failed!")


def example_3_rollback_scenario():
    """
    Example 3: Rollback to previous checkpoint.

    This example shows how to rollback a workflow to an earlier
    checkpoint when something goes wrong.
    """
    print("\n" + "=" * 60)
    print("Example 3: Rollback to Previous Checkpoint")
    print("=" * 60)

    # Initialize managers
    db = DatabaseManager()

    # Create workflow
    workflow_id = db.create_workflow(
        workflow_type="batch_enhance",
        input_params={"validation_ids": [f"val_{i}" for i in range(20)]}
    )
    print(f"\n1. Created enhancement workflow: {workflow_id}")

    # Create multiple checkpoints
    checkpoint_ids = []
    print("\n2. Processing with checkpoints...")
    for step in range(1, 6):
        db.update_workflow(
            workflow_id,
            current_step=step,
            total_steps=10,
            progress_percent=step * 10
        )

        state_data = pickle.dumps({
            "workflow_id": workflow_id,
            "step_number": step,
            "state_data": {
                "files_enhanced": step * 2,
                "quality_score": 0.8 + (step * 0.02)
            }
        })

        cp_id = db.create_checkpoint(
            workflow_id=workflow_id,
            name=f"enhance_step_{step}",
            step_number=step,
            state_data=state_data,
            validation_hash=f"enhance{step}"
        )
        checkpoint_ids.append(cp_id)
        print(f"   - Step {step} complete, checkpoint: {cp_id}")

    # Simulate problem detected
    print("\n3. Problem detected at step 5 - quality score dropped!")
    print("   - Rolling back to step 3...")

    # Get checkpoint at step 3
    target_checkpoint_id = checkpoint_ids[2]  # Step 3 (0-indexed)

    with db.get_session() as session:
        from core.database import Checkpoint
        target_checkpoint = session.query(Checkpoint).filter(
            Checkpoint.id == target_checkpoint_id
        ).first()

        recovered_data = pickle.loads(target_checkpoint.state_data)
        print(f"   - Recovered state: {recovered_data['state_data']}")

    # Rollback workflow
    db.update_workflow(
        workflow_id,
        current_step=3,
        progress_percent=30,
        state=WorkflowState.RUNNING
    )
    print("\n4. Workflow rolled back to step 3")
    print("   - Can now re-process steps 4 and 5 with corrections")


def example_4_checkpoint_validation():
    """
    Example 4: Checkpoint validation and error handling.

    This example shows how to validate checkpoints before recovery
    and handle corrupted checkpoints.
    """
    print("\n" + "=" * 60)
    print("Example 4: Checkpoint Validation")
    print("=" * 60)

    # Initialize managers
    db = DatabaseManager()
    checkpoint_mgr = CheckpointManager()

    # Create workflow
    workflow_id = db.create_workflow(
        workflow_type="validate_directory",
        input_params={"directory_path": "./tests"}
    )
    print(f"\n1. Created workflow: {workflow_id}")

    # Create checkpoint
    state_data = pickle.dumps({
        "workflow_id": workflow_id,
        "step_number": 1,
        "state_data": {"files_scanned": 100, "issues_found": 5}
    })

    checkpoint_id = db.create_checkpoint(
        workflow_id=workflow_id,
        name="validation_checkpoint",
        step_number=1,
        state_data=state_data,
        validation_hash="valid123"
    )
    print(f"   - Created checkpoint: {checkpoint_id}")

    # Validate checkpoint before recovery
    print("\n2. Validating checkpoint before recovery...")
    with db.get_session() as session:
        from core.database import Checkpoint
        checkpoint = session.query(Checkpoint).filter(
            Checkpoint.id == checkpoint_id
        ).first()

        if checkpoint:
            print("   - Checkpoint exists in database: ✓")

            # Verify required fields
            checks = {
                "Has workflow_id": checkpoint.workflow_id is not None,
                "Has name": checkpoint.name is not None,
                "Has step_number": checkpoint.step_number is not None,
                "Has state_data": checkpoint.state_data is not None,
                "Has validation_hash": checkpoint.validation_hash is not None,
                "Can resume from": checkpoint.can_resume_from
            }

            print("\n3. Checkpoint validation checks:")
            for check_name, result in checks.items():
                status = "✓" if result else "✗"
                print(f"   - {check_name}: {status}")

            # Try to deserialize state data
            try:
                recovered_data = pickle.loads(checkpoint.state_data)
                print("\n4. State data deserialization: ✓")
                print(f"   - Recovered: {recovered_data}")
            except Exception as e:
                print(f"\n4. State data deserialization: ✗")
                print(f"   - Error: {e}")
        else:
            print("   - Checkpoint not found in database: ✗")


def example_5_checkpoint_cleanup():
    """
    Example 5: Checkpoint cleanup and retention.

    This example shows how to manage checkpoint retention and
    cleanup old checkpoints.
    """
    print("\n" + "=" * 60)
    print("Example 5: Checkpoint Cleanup")
    print("=" * 60)

    # Initialize managers
    db = DatabaseManager()

    # Create workflow
    workflow_id = db.create_workflow(
        workflow_type="validate_directory",
        input_params={"directory_path": "./docs"}
    )
    print(f"\n1. Created workflow: {workflow_id}")

    # Create many checkpoints
    print("\n2. Creating 10 checkpoints...")
    for step in range(1, 11):
        state_data = pickle.dumps({
            "workflow_id": workflow_id,
            "step_number": step,
            "state_data": {"step": step}
        })

        db.create_checkpoint(
            workflow_id=workflow_id,
            name=f"step_{step}",
            step_number=step,
            state_data=state_data,
            validation_hash=f"hash{step}"
        )

    # Count checkpoints
    with db.get_session() as session:
        from core.database import Checkpoint
        count = session.query(Checkpoint).filter(
            Checkpoint.workflow_id == workflow_id
        ).count()
        print(f"   - Total checkpoints: {count}")

    # Cleanup old checkpoints (keep last 3)
    print("\n3. Cleaning up old checkpoints (keeping last 3)...")
    with db.get_session() as session:
        checkpoints = session.query(Checkpoint).filter(
            Checkpoint.workflow_id == workflow_id
        ).order_by(Checkpoint.step_number).all()

        to_delete = checkpoints[:-3]
        for cp in to_delete:
            print(f"   - Deleting checkpoint: {cp.id} (Step {cp.step_number})")
            session.delete(cp)

        session.commit()

    # Verify remaining checkpoints
    with db.get_session() as session:
        remaining = session.query(Checkpoint).filter(
            Checkpoint.workflow_id == workflow_id
        ).order_by(Checkpoint.step_number).all()

        print(f"\n4. Remaining checkpoints: {len(remaining)}")
        for cp in remaining:
            print(f"   - {cp.id}: Step {cp.step_number}")


def main():
    """Run all checkpoint recovery examples."""
    print("\n" + "=" * 60)
    print("TBCV Checkpoint Recovery Examples")
    print("=" * 60)

    examples = [
        ("Basic Checkpoint Recovery", example_1_basic_checkpoint_recovery),
        ("System Checkpoint", example_2_system_checkpoint),
        ("Rollback Scenario", example_3_rollback_scenario),
        ("Checkpoint Validation", example_4_checkpoint_validation),
        ("Checkpoint Cleanup", example_5_checkpoint_cleanup),
    ]

    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"{i}. {name}")

    print("\nRunning all examples...")

    for name, example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"\nError in {name}: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)
    print("\nFor more information, see:")
    print("- docs/workflow_recovery.md - Complete recovery guide")
    print("- docs/workflows.md - Workflow documentation")
    print("- tests/workflows/test_checkpoint_recovery.py - Test examples")


if __name__ == "__main__":
    main()
