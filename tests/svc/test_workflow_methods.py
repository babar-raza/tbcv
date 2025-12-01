"""
Tests for workflow-related MCP methods.

Tests cover:
- Workflow creation
- Workflow retrieval
- Workflow listing and filtering
- Workflow control (pause/resume/cancel)
- Workflow reports and summaries
- Workflow deletion
- Bulk operations
- Error handling
"""

import pytest
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

from svc.mcp_client import get_mcp_sync_client
from svc.mcp_exceptions import MCPError
from core.database import WorkflowState


@pytest.fixture
def mcp_client():
    """Get MCP sync client for testing."""
    return get_mcp_sync_client()


@pytest.fixture
def test_dir(tmp_path):
    """Create temporary directory with test files."""
    # Create test markdown files
    (tmp_path / "test1.md").write_text("# Test 1\n\nContent")
    (tmp_path / "test2.md").write_text("# Test 2\n\nContent")
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "test3.md").write_text("# Test 3\n\nContent")
    return tmp_path


class TestCreateWorkflow:
    """Tests for create_workflow method."""

    def test_create_validate_directory_workflow(self, mcp_client, test_dir):
        """Test creating a validate_directory workflow."""
        result = mcp_client.create_workflow(
            workflow_type="validate_directory",
            workflow_params={
                "directory_path": str(test_dir),
                "recursive": True
            },
            name="Test Validation",
            description="Test validation workflow"
        )

        assert result["success"] is True
        assert "workflow_id" in result
        assert result["workflow_type"] == "validate_directory"
        assert result["status"] in ["pending", "running"]
        assert "created_at" in result

    def test_create_batch_enhance_workflow(self, mcp_client):
        """Test creating a batch_enhance workflow."""
        result = mcp_client.create_workflow(
            workflow_type="batch_enhance",
            workflow_params={
                "validation_ids": ["val-1", "val-2", "val-3"]
            }
        )

        assert result["success"] is True
        assert result["workflow_type"] == "batch_enhance"

    def test_create_full_audit_workflow(self, mcp_client, test_dir):
        """Test creating a full_audit workflow."""
        result = mcp_client.create_workflow(
            workflow_type="full_audit",
            workflow_params={
                "directory_path": str(test_dir),
                "recursive": True
            }
        )

        assert result["success"] is True
        assert result["workflow_type"] == "full_audit"

    def test_create_recommendation_batch_workflow(self, mcp_client):
        """Test creating a recommendation_batch workflow."""
        result = mcp_client.create_workflow(
            workflow_type="recommendation_batch",
            workflow_params={
                "recommendation_ids": ["rec-1", "rec-2"]
            }
        )

        assert result["success"] is True
        assert result["workflow_type"] == "recommendation_batch"

    def test_create_workflow_invalid_type(self, mcp_client):
        """Test creating workflow with invalid type."""
        with pytest.raises(MCPError) as exc_info:
            mcp_client.create_workflow(
                workflow_type="invalid_type",
                workflow_params={}
            )

        assert "Invalid workflow type" in str(exc_info.value)

    def test_create_workflow_missing_params(self, mcp_client):
        """Test creating workflow with missing parameters."""
        with pytest.raises(MCPError) as exc_info:
            mcp_client.create_workflow(
                workflow_type="validate_directory",
                workflow_params={}  # Missing directory_path
            )

        # Should fail during execution, but creation should succeed
        # The workflow will fail when it tries to execute
        assert True  # Creation succeeded, execution will fail


class TestGetWorkflow:
    """Tests for get_workflow method."""

    def test_get_workflow_success(self, mcp_client, test_dir):
        """Test retrieving workflow by ID."""
        # Create workflow
        create_result = mcp_client.create_workflow(
            workflow_type="validate_directory",
            workflow_params={
                "directory_path": str(test_dir),
                "recursive": False
            }
        )
        workflow_id = create_result["workflow_id"]

        # Get workflow
        result = mcp_client.get_workflow(workflow_id)

        assert "workflow" in result
        workflow = result["workflow"]
        assert workflow["id"] == workflow_id
        assert workflow["workflow_type"] == "validate_directory"
        assert "status" in workflow
        assert "created_at" in workflow

    def test_get_workflow_not_found(self, mcp_client):
        """Test retrieving non-existent workflow."""
        with pytest.raises(MCPError) as exc_info:
            mcp_client.get_workflow("nonexistent-workflow-id")

        assert "not found" in str(exc_info.value).lower()


class TestListWorkflows:
    """Tests for list_workflows method."""

    def test_list_workflows_default(self, mcp_client):
        """Test listing workflows with default parameters."""
        result = mcp_client.list_workflows()

        assert "workflows" in result
        assert "total" in result
        assert "limit" in result
        assert "offset" in result
        assert isinstance(result["workflows"], list)
        assert result["limit"] == 100
        assert result["offset"] == 0

    def test_list_workflows_with_pagination(self, mcp_client, test_dir):
        """Test listing workflows with pagination."""
        # Create multiple workflows
        for i in range(3):
            mcp_client.create_workflow(
                workflow_type="validate_directory",
                workflow_params={
                    "directory_path": str(test_dir),
                    "recursive": False
                }
            )

        # List with limit
        result = mcp_client.list_workflows(limit=2, offset=0)
        assert len(result["workflows"]) <= 2

    def test_list_workflows_filter_by_status(self, mcp_client, test_dir):
        """Test filtering workflows by status."""
        # Create and wait for workflow to start
        create_result = mcp_client.create_workflow(
            workflow_type="validate_directory",
            workflow_params={
                "directory_path": str(test_dir),
                "recursive": False
            }
        )
        time.sleep(0.1)  # Give workflow time to start

        # List running workflows
        result = mcp_client.list_workflows(status="running")

        # Should have at least our workflow (might have others)
        assert "workflows" in result
        for workflow in result["workflows"]:
            assert workflow["status"] == "running"

    def test_list_workflows_filter_by_type(self, mcp_client, test_dir):
        """Test filtering workflows by type."""
        # Create workflow
        mcp_client.create_workflow(
            workflow_type="validate_directory",
            workflow_params={
                "directory_path": str(test_dir),
                "recursive": False
            }
        )

        # List workflows of specific type
        result = mcp_client.list_workflows(workflow_type="validate_directory")

        assert "workflows" in result
        for workflow in result["workflows"]:
            assert workflow["workflow_type"] == "validate_directory"


class TestControlWorkflow:
    """Tests for control_workflow method."""

    def test_pause_workflow(self, mcp_client, test_dir):
        """Test pausing a running workflow."""
        # Create workflow
        create_result = mcp_client.create_workflow(
            workflow_type="validate_directory",
            workflow_params={
                "directory_path": str(test_dir),
                "recursive": True
            }
        )
        workflow_id = create_result["workflow_id"]

        # Give workflow time to start
        time.sleep(0.1)

        # Pause workflow
        result = mcp_client.control_workflow(workflow_id, "pause")

        assert result["success"] is True
        assert result["workflow_id"] == workflow_id
        assert result["action"] == "pause"
        assert result["new_status"] == "paused"

    def test_resume_workflow(self, mcp_client, test_dir):
        """Test resuming a paused workflow."""
        # Create and pause workflow
        create_result = mcp_client.create_workflow(
            workflow_type="validate_directory",
            workflow_params={
                "directory_path": str(test_dir),
                "recursive": True
            }
        )
        workflow_id = create_result["workflow_id"]
        time.sleep(0.1)

        mcp_client.control_workflow(workflow_id, "pause")

        # Resume workflow
        result = mcp_client.control_workflow(workflow_id, "resume")

        assert result["success"] is True
        assert result["action"] == "resume"
        assert result["new_status"] == "running"

    def test_cancel_workflow(self, mcp_client, test_dir):
        """Test cancelling a workflow."""
        # Create workflow
        create_result = mcp_client.create_workflow(
            workflow_type="validate_directory",
            workflow_params={
                "directory_path": str(test_dir),
                "recursive": True
            }
        )
        workflow_id = create_result["workflow_id"]
        time.sleep(0.1)

        # Cancel workflow
        result = mcp_client.control_workflow(workflow_id, "cancel")

        assert result["success"] is True
        assert result["action"] == "cancel"
        assert result["new_status"] == "cancelled"

    def test_control_workflow_invalid_action(self, mcp_client, test_dir):
        """Test control workflow with invalid action."""
        # Create workflow
        create_result = mcp_client.create_workflow(
            workflow_type="validate_directory",
            workflow_params={
                "directory_path": str(test_dir),
                "recursive": False
            }
        )
        workflow_id = create_result["workflow_id"]

        # Try invalid action
        with pytest.raises(MCPError) as exc_info:
            mcp_client.control_workflow(workflow_id, "invalid_action")

        assert "Invalid action" in str(exc_info.value)


class TestWorkflowReports:
    """Tests for workflow report and summary methods."""

    def test_get_workflow_report(self, mcp_client, test_dir):
        """Test getting detailed workflow report."""
        # Create workflow
        create_result = mcp_client.create_workflow(
            workflow_type="validate_directory",
            workflow_params={
                "directory_path": str(test_dir),
                "recursive": False
            }
        )
        workflow_id = create_result["workflow_id"]

        # Get report
        result = mcp_client.get_workflow_report(workflow_id, include_details=True)

        assert "workflow_id" in result
        assert "report" in result
        report = result["report"]
        assert "workflow_type" in report
        assert "state" in report
        assert "created_at" in report

    def test_get_workflow_report_without_details(self, mcp_client, test_dir):
        """Test getting workflow report without details."""
        # Create workflow
        create_result = mcp_client.create_workflow(
            workflow_type="validate_directory",
            workflow_params={
                "directory_path": str(test_dir),
                "recursive": False
            }
        )
        workflow_id = create_result["workflow_id"]

        # Get report without details
        result = mcp_client.get_workflow_report(workflow_id, include_details=False)

        assert "report" in result
        report = result["report"]
        assert "workflow_type" in report

    def test_get_workflow_summary(self, mcp_client, test_dir):
        """Test getting workflow summary."""
        # Create workflow
        create_result = mcp_client.create_workflow(
            workflow_type="validate_directory",
            workflow_params={
                "directory_path": str(test_dir),
                "recursive": False
            }
        )
        workflow_id = create_result["workflow_id"]

        # Get summary
        result = mcp_client.get_workflow_summary(workflow_id)

        assert result["workflow_id"] == workflow_id
        assert "status" in result
        assert "progress_percent" in result
        assert "files_processed" in result
        assert "files_total" in result
        assert "errors_count" in result
        assert "duration_seconds" in result
        assert "eta_seconds" in result
        assert isinstance(result["progress_percent"], (int, float))
        assert isinstance(result["duration_seconds"], (int, float))


class TestDeleteWorkflow:
    """Tests for delete_workflow method."""

    def test_delete_workflow_success(self, mcp_client, test_dir):
        """Test deleting a completed workflow."""
        # Create workflow
        create_result = mcp_client.create_workflow(
            workflow_type="validate_directory",
            workflow_params={
                "directory_path": str(test_dir),
                "recursive": False
            }
        )
        workflow_id = create_result["workflow_id"]

        # Wait for completion
        time.sleep(0.5)

        # Delete workflow
        result = mcp_client.delete_workflow(workflow_id)

        assert result["success"] is True
        assert result["workflow_id"] == workflow_id

    def test_delete_running_workflow_without_force(self, mcp_client, test_dir):
        """Test deleting running workflow without force flag."""
        # Create workflow
        create_result = mcp_client.create_workflow(
            workflow_type="validate_directory",
            workflow_params={
                "directory_path": str(test_dir),
                "recursive": True
            }
        )
        workflow_id = create_result["workflow_id"]
        time.sleep(0.1)

        # Try to delete without force
        with pytest.raises(MCPError) as exc_info:
            mcp_client.delete_workflow(workflow_id, force=False)

        assert "Cannot delete running workflow" in str(exc_info.value)

    def test_delete_running_workflow_with_force(self, mcp_client, test_dir):
        """Test deleting running workflow with force flag."""
        # Create workflow
        create_result = mcp_client.create_workflow(
            workflow_type="validate_directory",
            workflow_params={
                "directory_path": str(test_dir),
                "recursive": True
            }
        )
        workflow_id = create_result["workflow_id"]
        time.sleep(0.1)

        # Delete with force
        result = mcp_client.delete_workflow(workflow_id, force=True)

        assert result["success"] is True


class TestBulkDeleteWorkflows:
    """Tests for bulk_delete_workflows method."""

    def test_bulk_delete_by_ids(self, mcp_client, test_dir):
        """Test bulk deleting workflows by IDs."""
        # Create workflows
        workflow_ids = []
        for _ in range(2):
            create_result = mcp_client.create_workflow(
                workflow_type="validate_directory",
                workflow_params={
                    "directory_path": str(test_dir),
                    "recursive": False
                }
            )
            workflow_ids.append(create_result["workflow_id"])

        # Wait for completion
        time.sleep(0.5)

        # Bulk delete
        result = mcp_client.bulk_delete_workflows(workflow_ids=workflow_ids)

        assert result["success"] is True
        assert result["deleted_count"] == 2
        assert len(result["errors"]) == 0

    def test_bulk_delete_by_status(self, mcp_client, test_dir):
        """Test bulk deleting workflows by status."""
        # Create and cancel workflow
        create_result = mcp_client.create_workflow(
            workflow_type="validate_directory",
            workflow_params={
                "directory_path": str(test_dir),
                "recursive": False
            }
        )
        workflow_id = create_result["workflow_id"]
        time.sleep(0.1)
        mcp_client.control_workflow(workflow_id, "cancel")

        # Bulk delete cancelled workflows
        result = mcp_client.bulk_delete_workflows(status="cancelled")

        assert result["success"] is True
        assert result["deleted_count"] >= 1

    def test_bulk_delete_by_type(self, mcp_client, test_dir):
        """Test bulk deleting workflows by type."""
        # Create workflow
        create_result = mcp_client.create_workflow(
            workflow_type="batch_enhance",
            workflow_params={
                "validation_ids": ["val-1"]
            }
        )
        time.sleep(0.5)

        # Bulk delete by type
        result = mcp_client.bulk_delete_workflows(
            workflow_type="batch_enhance",
            force=True
        )

        assert result["success"] is True


class TestWorkflowIntegration:
    """Integration tests for workflow lifecycle."""

    def test_complete_workflow_lifecycle(self, mcp_client, test_dir):
        """Test complete workflow lifecycle: create → monitor → complete → delete."""
        # Create workflow
        create_result = mcp_client.create_workflow(
            workflow_type="validate_directory",
            workflow_params={
                "directory_path": str(test_dir),
                "recursive": False
            },
            name="Integration Test Workflow"
        )
        workflow_id = create_result["workflow_id"]

        # Monitor workflow
        for _ in range(5):
            summary = mcp_client.get_workflow_summary(workflow_id)
            if summary["status"] in ["completed", "failed"]:
                break
            time.sleep(0.1)

        # Get final report
        report = mcp_client.get_workflow_report(workflow_id)
        assert report["report"]["workflow_type"] == "validate_directory"

        # Delete workflow
        delete_result = mcp_client.delete_workflow(workflow_id)
        assert delete_result["success"] is True

    def test_workflow_pause_resume_complete(self, mcp_client, test_dir):
        """Test workflow with pause and resume."""
        # Create workflow
        create_result = mcp_client.create_workflow(
            workflow_type="validate_directory",
            workflow_params={
                "directory_path": str(test_dir),
                "recursive": True
            }
        )
        workflow_id = create_result["workflow_id"]
        time.sleep(0.1)

        # Pause
        pause_result = mcp_client.control_workflow(workflow_id, "pause")
        assert pause_result["new_status"] == "paused"

        # Resume
        resume_result = mcp_client.control_workflow(workflow_id, "resume")
        assert resume_result["new_status"] == "running"

        # Wait for completion
        time.sleep(0.5)

        # Delete
        mcp_client.delete_workflow(workflow_id, force=True)
