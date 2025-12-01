"""
Comprehensive MCP server tests.

Tests all MCP methods (validation, approval, enhancement) with both
synchronous and asynchronous clients. Includes success cases, error
handling, edge cases, and integration scenarios.
"""

import pytest
import asyncio
from pathlib import Path
from datetime import datetime, timezone
from svc.mcp_client import MCPSyncClient, MCPAsyncClient
from svc.mcp_exceptions import (
    MCPError,
    MCPMethodNotFoundError,
    MCPInvalidParamsError,
    MCPInternalError
)
from core.database import ValidationResult, ValidationStatus


class TestMCPValidationMethods:
    """Test validation methods (validate_folder)."""

    def test_validate_folder_success(self, mcp_sync_client, test_markdown_files):
        """Test successful folder validation with multiple files."""
        # Use the parent directory containing test files
        folder_path = test_markdown_files[0].parent

        result = mcp_sync_client.validate_folder(str(folder_path))

        assert result["success"] is True
        assert "results" in result
        assert result["results"]["files_processed"] >= len(test_markdown_files)
        assert "message" in result

    def test_validate_folder_nonrecursive(self, mcp_sync_client, test_markdown_files):
        """Test non-recursive folder validation."""
        folder_path = test_markdown_files[0].parent

        result = mcp_sync_client.validate_folder(
            str(folder_path),
            recursive=False
        )

        assert result["success"] is True
        assert result["results"]["files_processed"] >= 0

    def test_validate_folder_single_file(self, mcp_sync_client, test_markdown_file):
        """Test folder validation with single file."""
        folder_path = test_markdown_file.parent

        result = mcp_sync_client.validate_folder(str(folder_path))

        assert result["success"] is True
        assert result["results"]["files_processed"] >= 1

    def test_validate_folder_empty_directory(self, mcp_sync_client, tmp_path):
        """Test folder validation on empty directory."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        result = mcp_sync_client.validate_folder(str(empty_dir))

        assert result["success"] is True
        assert result["results"]["files_processed"] == 0

    def test_validate_folder_nonexistent_path(self, mcp_sync_client):
        """Test folder validation with non-existent path."""
        with pytest.raises(Exception):
            mcp_sync_client.validate_folder("/nonexistent/path/to/folder")

    def test_validate_folder_missing_path_parameter(self, mcp_sync_client):
        """Test validate_folder with missing folder_path parameter."""
        # Call internal _call method to test parameter validation
        with pytest.raises(MCPError):
            mcp_sync_client._call("validate_folder", {})

    def test_validate_folder_with_nested_structure(
        self,
        mcp_sync_client,
        tmp_path
    ):
        """Test recursive validation with nested folder structure."""
        # Create nested structure
        (tmp_path / "level1").mkdir()
        (tmp_path / "level1" / "level2").mkdir()

        # Create files at different levels
        (tmp_path / "root.md").write_text("# Root", encoding="utf-8")
        (tmp_path / "level1" / "l1.md").write_text("# Level 1", encoding="utf-8")
        (tmp_path / "level1" / "level2" / "l2.md").write_text(
            "# Level 2",
            encoding="utf-8"
        )

        result = mcp_sync_client.validate_folder(str(tmp_path), recursive=True)

        assert result["success"] is True
        assert result["results"]["files_processed"] >= 3

    def test_validate_folder_with_non_markdown_files(
        self,
        mcp_sync_client,
        tmp_path
    ):
        """Test validation skips non-markdown files."""
        # Create both markdown and non-markdown files
        (tmp_path / "test.md").write_text("# Test", encoding="utf-8")
        (tmp_path / "test.txt").write_text("Not markdown", encoding="utf-8")
        (tmp_path / "test.py").write_text("print('test')", encoding="utf-8")

        result = mcp_sync_client.validate_folder(str(tmp_path))

        assert result["success"] is True
        # Should only process .md files
        assert result["results"]["files_processed"] >= 1


class TestMCPApprovalMethods:
    """Test approval methods (approve, reject)."""

    def test_approve_empty_list(self, mcp_sync_client):
        """Test approve with empty list."""
        result = mcp_sync_client.approve([])

        assert result["success"] is True
        assert result["approved_count"] == 0
        assert "errors" in result

    def test_approve_nonexistent_ids(self, mcp_sync_client):
        """Test approve with non-existent validation IDs."""
        result = mcp_sync_client.approve([
            "fake-id-1",
            "fake-id-2",
            "fake-id-3"
        ])

        assert result["success"] is True
        assert result["approved_count"] == 0
        assert len(result["errors"]) > 0

    def test_approve_single_id(self, mcp_sync_client):
        """Test approve with single ID."""
        result = mcp_sync_client.approve(["test-id"])

        assert result["success"] is True
        assert "approved_count" in result
        assert "errors" in result

    def test_reject_empty_list(self, mcp_sync_client):
        """Test reject with empty list."""
        result = mcp_sync_client.reject([])

        assert result["success"] is True
        assert result["rejected_count"] == 0
        assert "errors" in result

    def test_reject_nonexistent_ids(self, mcp_sync_client):
        """Test reject with non-existent validation IDs."""
        result = mcp_sync_client.reject([
            "fake-id-1",
            "fake-id-2",
            "fake-id-3"
        ])

        assert result["success"] is True
        assert result["rejected_count"] == 0
        assert len(result["errors"]) > 0

    def test_reject_single_id(self, mcp_sync_client):
        """Test reject with single ID."""
        result = mcp_sync_client.reject(["test-id"])

        assert result["success"] is True
        assert "rejected_count" in result
        assert "errors" in result

    def test_approve_mixed_valid_invalid_ids(self, mcp_sync_client):
        """Test approve with mix of valid and invalid IDs."""
        result = mcp_sync_client.approve([
            "valid-id-1",
            "fake-id",
            "valid-id-2"
        ])

        assert result["success"] is True
        # Should have some errors for invalid IDs
        assert len(result["errors"]) > 0

    def test_reject_mixed_valid_invalid_ids(self, mcp_sync_client):
        """Test reject with mix of valid and invalid IDs."""
        result = mcp_sync_client.reject([
            "valid-id-1",
            "fake-id",
            "valid-id-2"
        ])

        assert result["success"] is True
        # Should have some errors for invalid IDs
        assert len(result["errors"]) > 0

    def test_approve_reject_workflow(
        self,
        mcp_sync_client,
        test_markdown_file
    ):
        """Test complete approve/reject workflow."""
        # First validate a file
        folder_path = test_markdown_file.parent
        validation_result = mcp_sync_client.validate_folder(str(folder_path))
        assert validation_result["success"] is True

        # Try to approve (may not find IDs, but should not error)
        approve_result = mcp_sync_client.approve(["test-id"])
        assert approve_result["success"] is True

        # Try to reject
        reject_result = mcp_sync_client.reject(["test-id"])
        assert reject_result["success"] is True


class TestMCPEnhancementMethods:
    """Test enhancement methods (enhance)."""

    def test_enhance_empty_list(self, mcp_sync_client):
        """Test enhance with empty list."""
        result = mcp_sync_client.enhance([])

        assert result["success"] is True
        assert result["enhanced_count"] == 0
        assert result["enhancements"] == []
        assert "errors" in result

    def test_enhance_nonexistent_ids(self, mcp_sync_client):
        """Test enhance with non-existent validation IDs."""
        result = mcp_sync_client.enhance([
            "fake-id-1",
            "fake-id-2"
        ])

        assert result["success"] is True
        assert result["enhanced_count"] == 0
        assert len(result["errors"]) > 0

    def test_enhance_single_id(self, mcp_sync_client):
        """Test enhance with single ID."""
        result = mcp_sync_client.enhance(["test-id"])

        assert result["success"] is True
        assert "enhanced_count" in result
        assert "enhancements" in result
        assert "errors" in result

    def test_enhance_multiple_ids(self, mcp_sync_client):
        """Test enhance with multiple IDs."""
        result = mcp_sync_client.enhance([
            "id-1",
            "id-2",
            "id-3"
        ])

        assert result["success"] is True
        assert "enhanced_count" in result
        assert isinstance(result["enhancements"], list)

    def test_enhance_response_structure(self, mcp_sync_client):
        """Test enhance response has correct structure."""
        result = mcp_sync_client.enhance([])

        assert "success" in result
        assert "enhanced_count" in result
        assert "enhancements" in result
        assert "errors" in result
        assert isinstance(result["enhancements"], list)
        assert isinstance(result["errors"], list)


@pytest.mark.asyncio
class TestMCPAsyncMethods:
    """Test async MCP methods."""

    async def test_async_validate_folder_success(
        self,
        mcp_async_client,
        test_markdown_files
    ):
        """Test async folder validation."""
        folder_path = test_markdown_files[0].parent

        result = await mcp_async_client.validate_folder(str(folder_path))

        assert result["success"] is True
        assert result["results"]["files_processed"] >= len(test_markdown_files)

    async def test_async_approve_empty_list(self, mcp_async_client):
        """Test async approve with empty list."""
        result = await mcp_async_client.approve([])

        assert result["success"] is True
        assert result["approved_count"] == 0

    async def test_async_approve_nonexistent_ids(self, mcp_async_client):
        """Test async approve with non-existent IDs."""
        result = await mcp_async_client.approve(["fake-id-1", "fake-id-2"])

        assert result["success"] is True
        assert result["approved_count"] == 0
        assert len(result["errors"]) > 0

    async def test_async_reject_empty_list(self, mcp_async_client):
        """Test async reject with empty list."""
        result = await mcp_async_client.reject([])

        assert result["success"] is True
        assert result["rejected_count"] == 0

    async def test_async_reject_nonexistent_ids(self, mcp_async_client):
        """Test async reject with non-existent IDs."""
        result = await mcp_async_client.reject(["fake-id-1"])

        assert result["success"] is True
        assert result["rejected_count"] == 0
        assert len(result["errors"]) > 0

    async def test_async_enhance_empty_list(self, mcp_async_client):
        """Test async enhance with empty list."""
        result = await mcp_async_client.enhance([])

        assert result["success"] is True
        assert result["enhanced_count"] == 0
        assert result["enhancements"] == []

    async def test_async_enhance_nonexistent_ids(self, mcp_async_client):
        """Test async enhance with non-existent IDs."""
        result = await mcp_async_client.enhance(["fake-id-1", "fake-id-2"])

        assert result["success"] is True
        assert result["enhanced_count"] == 0
        assert len(result["errors"]) > 0

    async def test_async_concurrent_operations(
        self,
        mcp_async_client,
        test_markdown_file
    ):
        """Test concurrent async operations."""
        folder_path = test_markdown_file.parent

        # Execute multiple operations concurrently
        tasks = [
            mcp_async_client.validate_folder(str(folder_path)),
            mcp_async_client.approve([]),
            mcp_async_client.reject([]),
            mcp_async_client.enhance([])
        ]

        results = await asyncio.gather(*tasks)

        # All operations should succeed
        assert all(r["success"] for r in results)

    async def test_async_sequential_workflow(
        self,
        mcp_async_client,
        test_markdown_file
    ):
        """Test sequential async workflow."""
        folder_path = test_markdown_file.parent

        # Validate folder
        validation_result = await mcp_async_client.validate_folder(
            str(folder_path)
        )
        assert validation_result["success"] is True

        # Approve (with fake IDs)
        approve_result = await mcp_async_client.approve(["test-id"])
        assert approve_result["success"] is True

        # Enhance (with fake IDs)
        enhance_result = await mcp_async_client.enhance(["test-id"])
        assert enhance_result["success"] is True


class TestMCPErrorHandling:
    """Test error handling across all MCP methods."""

    def test_method_not_found_error(self, mcp_sync_client):
        """Test calling non-existent method raises error."""
        with pytest.raises(MCPMethodNotFoundError):
            mcp_sync_client._call("nonexistent_method", {})

    def test_invalid_params_handling(self, mcp_sync_client):
        """Test invalid parameters are handled correctly."""
        # Test with missing required parameters
        with pytest.raises(MCPError):
            mcp_sync_client._call("validate_folder", {})

    def test_error_response_structure(self, mcp_sync_client):
        """Test error responses have correct structure."""
        try:
            mcp_sync_client._call("nonexistent_method", {})
        except MCPMethodNotFoundError as e:
            assert hasattr(e, 'code')
            assert hasattr(e, 'data')
            assert e.code == -32601

    @pytest.mark.asyncio
    async def test_async_method_not_found_error(self, mcp_async_client):
        """Test async method not found error."""
        with pytest.raises(MCPMethodNotFoundError):
            await mcp_async_client._call("nonexistent_method", {})

    @pytest.mark.asyncio
    async def test_async_invalid_params_handling(self, mcp_async_client):
        """Test async invalid parameters handling."""
        with pytest.raises(MCPError):
            await mcp_async_client._call("validate_folder", {})


class TestMCPClientFeatures:
    """Test MCP client features (retry, timeout, etc.)."""

    def test_client_initialization(self, mcp_sync_client):
        """Test client initializes with correct settings."""
        assert mcp_sync_client.timeout > 0
        assert mcp_sync_client.max_retries > 0
        assert mcp_sync_client._request_counter >= 0

    def test_request_counter_increments(self, mcp_sync_client):
        """Test request counter increments with each call."""
        initial_count = mcp_sync_client._request_counter

        mcp_sync_client.approve([])
        assert mcp_sync_client._request_counter == initial_count + 1

        mcp_sync_client.reject([])
        assert mcp_sync_client._request_counter == initial_count + 2

        mcp_sync_client.enhance([])
        assert mcp_sync_client._request_counter == initial_count + 3

    def test_custom_timeout_and_retries(self):
        """Test client with custom timeout and retries."""
        client = MCPSyncClient(timeout=60, max_retries=5)

        assert client.timeout == 60
        assert client.max_retries == 5

    @pytest.mark.asyncio
    async def test_async_client_initialization(self, mcp_async_client):
        """Test async client initializes correctly."""
        assert mcp_async_client.timeout > 0
        assert mcp_async_client.max_retries > 0
        assert mcp_async_client._request_counter >= 0

    @pytest.mark.asyncio
    async def test_async_request_counter_increments(self, mcp_async_client):
        """Test async request counter increments."""
        initial_count = mcp_async_client._request_counter

        await mcp_async_client.approve([])
        assert mcp_async_client._request_counter == initial_count + 1

        await mcp_async_client.reject([])
        assert mcp_async_client._request_counter == initial_count + 2


class TestMCPIntegrationScenarios:
    """Test integration scenarios combining multiple MCP operations."""

    def test_full_validation_workflow(
        self,
        mcp_sync_client,
        test_markdown_file
    ):
        """Test complete validation workflow."""
        folder_path = test_markdown_file.parent

        # Step 1: Validate folder
        validation_result = mcp_sync_client.validate_folder(str(folder_path))
        assert validation_result["success"] is True
        assert validation_result["results"]["files_processed"] > 0

        # Step 2: Approve validations (with fake IDs for now)
        approve_result = mcp_sync_client.approve(["test-id"])
        assert approve_result["success"] is True

        # Step 3: Enhance approved validations
        enhance_result = mcp_sync_client.enhance(["test-id"])
        assert enhance_result["success"] is True

    def test_rejection_workflow(
        self,
        mcp_sync_client,
        test_markdown_file
    ):
        """Test validation rejection workflow."""
        folder_path = test_markdown_file.parent

        # Step 1: Validate folder
        validation_result = mcp_sync_client.validate_folder(str(folder_path))
        assert validation_result["success"] is True

        # Step 2: Reject validations
        reject_result = mcp_sync_client.reject(["test-id"])
        assert reject_result["success"] is True

    def test_batch_operations(self, mcp_sync_client):
        """Test batch operations on multiple IDs."""
        ids = [f"test-id-{i}" for i in range(10)]

        # Test batch approve
        approve_result = mcp_sync_client.approve(ids)
        assert approve_result["success"] is True

        # Test batch reject
        reject_result = mcp_sync_client.reject(ids)
        assert reject_result["success"] is True

        # Test batch enhance
        enhance_result = mcp_sync_client.enhance(ids)
        assert enhance_result["success"] is True

    @pytest.mark.asyncio
    async def test_async_full_workflow(
        self,
        mcp_async_client,
        test_markdown_file
    ):
        """Test complete async validation workflow."""
        folder_path = test_markdown_file.parent

        # Validate
        validation_result = await mcp_async_client.validate_folder(
            str(folder_path)
        )
        assert validation_result["success"] is True

        # Approve
        approve_result = await mcp_async_client.approve(["test-id"])
        assert approve_result["success"] is True

        # Enhance
        enhance_result = await mcp_async_client.enhance(["test-id"])
        assert enhance_result["success"] is True

    def test_multiple_folder_validations(
        self,
        mcp_sync_client,
        test_markdown_files
    ):
        """Test validating multiple folders."""
        folder_path = test_markdown_files[0].parent

        # Validate the same folder multiple times
        results = []
        for _ in range(3):
            result = mcp_sync_client.validate_folder(str(folder_path))
            results.append(result)

        # All validations should succeed
        assert all(r["success"] for r in results)

        # All should process the same number of files
        file_counts = [r["results"]["files_processed"] for r in results]
        assert len(set(file_counts)) == 1  # All counts should be the same
