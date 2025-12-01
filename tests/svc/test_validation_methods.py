"""Comprehensive tests for MCP validation methods."""

import pytest
import tempfile
from pathlib import Path
from svc.mcp_client import MCPSyncClient, get_mcp_sync_client
from svc.mcp_exceptions import MCPError


class TestValidateFile:
    """Tests for validate_file method."""

    def test_validate_file_success(self, tmp_path):
        """Test successful file validation."""
        # Create test file
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test Document\n\nSome content here.")

        client = get_mcp_sync_client()
        result = client.validate_file(str(test_file))

        assert result["success"] is True
        assert "validation_id" in result
        assert "status" in result
        assert result["file_path"] == str(test_file)
        assert "issues" in result

    def test_validate_file_not_found(self):
        """Test validation fails for non-existent file."""
        client = get_mcp_sync_client()

        with pytest.raises(Exception) as exc_info:
            client.validate_file("/nonexistent/file.md")

        assert "File not found" in str(exc_info.value) or "not found" in str(exc_info.value).lower()

    def test_validate_file_with_validation_types(self, tmp_path):
        """Test validation with specific validation types."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test\n\nContent")

        client = get_mcp_sync_client()
        result = client.validate_file(
            str(test_file),
            validation_types=["markdown", "seo"]
        )

        assert result["success"] is True
        assert "validation_id" in result


class TestValidateContent:
    """Tests for validate_content method."""

    def test_validate_content_success(self):
        """Test successful content validation."""
        client = get_mcp_sync_client()
        result = client.validate_content("# Test Document\n\nContent here.")

        assert result["success"] is True
        assert "validation_id" in result
        assert "status" in result
        assert "issues" in result

    def test_validate_content_with_virtual_path(self):
        """Test content validation with virtual file path."""
        client = get_mcp_sync_client()
        result = client.validate_content(
            "# Test\n\nContent",
            file_path="virtual/document.md"
        )

        assert result["success"] is True
        assert "validation_id" in result

    def test_validate_content_empty(self):
        """Test validation of empty content."""
        client = get_mcp_sync_client()
        result = client.validate_content("")

        assert result["success"] is True
        assert "validation_id" in result

    def test_validate_content_with_validation_types(self):
        """Test content validation with specific types."""
        client = get_mcp_sync_client()
        result = client.validate_content(
            "# Test\n\nContent",
            validation_types=["markdown"]
        )

        assert result["success"] is True


class TestGetValidation:
    """Tests for get_validation method."""

    def test_get_validation_success(self, tmp_path):
        """Test retrieving validation by ID."""
        # Create and validate file
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test Document")

        client = get_mcp_sync_client()
        create_result = client.validate_file(str(test_file))
        validation_id = create_result["validation_id"]

        # Retrieve validation
        result = client.get_validation(validation_id)

        assert "validation" in result
        assert result["validation"]["id"] == validation_id
        assert "file_path" in result["validation"]
        assert "status" in result["validation"]

    def test_get_validation_not_found(self):
        """Test error when validation not found."""
        client = get_mcp_sync_client()

        with pytest.raises(Exception) as exc_info:
            client.get_validation("nonexistent-id")

        assert "not found" in str(exc_info.value).lower()

    def test_get_validation_has_all_fields(self, tmp_path):
        """Test that retrieved validation has all expected fields."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test")

        client = get_mcp_sync_client()
        create_result = client.validate_file(str(test_file))
        validation_id = create_result["validation_id"]

        result = client.get_validation(validation_id)
        validation = result["validation"]

        # Check all expected fields
        expected_fields = [
            "id", "file_path", "status", "severity",
            "rules_applied", "validation_results", "notes",
            "created_at"
        ]
        for field in expected_fields:
            assert field in validation, f"Missing field: {field}"


class TestListValidations:
    """Tests for list_validations method."""

    def test_list_validations_default(self, tmp_path):
        """Test listing validations with default parameters."""
        # Create some validations
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test")

        client = get_mcp_sync_client()
        client.validate_file(str(test_file))

        # List validations
        result = client.list_validations()

        assert "validations" in result
        assert "total" in result
        assert isinstance(result["validations"], list)
        assert result["total"] >= 0

    def test_list_validations_with_limit(self, tmp_path):
        """Test pagination with limit."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test")

        client = get_mcp_sync_client()
        client.validate_file(str(test_file))

        result = client.list_validations(limit=5)

        assert "validations" in result
        assert len(result["validations"]) <= 5

    def test_list_validations_with_offset(self):
        """Test pagination with offset."""
        client = get_mcp_sync_client()
        result = client.list_validations(limit=10, offset=0)

        assert "validations" in result
        assert "total" in result

    def test_list_validations_with_status_filter(self, tmp_path):
        """Test filtering by status."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test")

        client = get_mcp_sync_client()
        client.validate_file(str(test_file))

        result = client.list_validations(status="pass")

        assert "validations" in result
        for validation in result["validations"]:
            assert validation["status"] in ["pass", "PASS"]

    def test_list_validations_with_file_path_filter(self, tmp_path):
        """Test filtering by file path."""
        test_file = tmp_path / "specific.md"
        test_file.write_text("# Test")

        client = get_mcp_sync_client()
        client.validate_file(str(test_file))

        result = client.list_validations(file_path=str(test_file))

        assert "validations" in result
        for validation in result["validations"]:
            assert validation["file_path"] == str(test_file)

    def test_list_validations_empty_result(self):
        """Test listing with filters that return no results."""
        client = get_mcp_sync_client()
        result = client.list_validations(
            file_path="/nonexistent/path.md"
        )

        assert "validations" in result
        assert result["total"] == 0
        assert len(result["validations"]) == 0


class TestUpdateValidation:
    """Tests for update_validation method."""

    def test_update_validation_notes(self, tmp_path):
        """Test updating validation notes."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test")

        client = get_mcp_sync_client()
        create_result = client.validate_file(str(test_file))
        validation_id = create_result["validation_id"]

        # Update notes
        update_result = client.update_validation(
            validation_id,
            notes="Updated notes"
        )

        assert update_result["success"] is True
        assert update_result["validation_id"] == validation_id

        # Verify update
        validation = client.get_validation(validation_id)
        assert validation["validation"]["notes"] == "Updated notes"

    def test_update_validation_status(self, tmp_path):
        """Test updating validation status."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test")

        client = get_mcp_sync_client()
        create_result = client.validate_file(str(test_file))
        validation_id = create_result["validation_id"]

        # Update status
        update_result = client.update_validation(
            validation_id,
            status="approved"
        )

        assert update_result["success"] is True

        # Verify update
        validation = client.get_validation(validation_id)
        assert validation["validation"]["status"] == "approved"

    def test_update_validation_both_fields(self, tmp_path):
        """Test updating both notes and status."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test")

        client = get_mcp_sync_client()
        create_result = client.validate_file(str(test_file))
        validation_id = create_result["validation_id"]

        # Update both
        update_result = client.update_validation(
            validation_id,
            notes="New notes",
            status="rejected"
        )

        assert update_result["success"] is True

        # Verify updates
        validation = client.get_validation(validation_id)
        assert validation["validation"]["notes"] == "New notes"
        assert validation["validation"]["status"] == "rejected"

    def test_update_validation_not_found(self):
        """Test error when updating non-existent validation."""
        client = get_mcp_sync_client()

        with pytest.raises(Exception) as exc_info:
            client.update_validation("nonexistent-id", notes="Test")

        assert "not found" in str(exc_info.value).lower()

    def test_update_validation_invalid_status(self, tmp_path):
        """Test error with invalid status value."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test")

        client = get_mcp_sync_client()
        create_result = client.validate_file(str(test_file))
        validation_id = create_result["validation_id"]

        # Try to update with invalid status
        with pytest.raises(Exception) as exc_info:
            client.update_validation(validation_id, status="invalid_status")

        assert "invalid" in str(exc_info.value).lower() or "status" in str(exc_info.value).lower()


class TestDeleteValidation:
    """Tests for delete_validation method."""

    def test_delete_validation_success(self, tmp_path):
        """Test deleting validation."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test")

        client = get_mcp_sync_client()
        create_result = client.validate_file(str(test_file))
        validation_id = create_result["validation_id"]

        # Delete validation
        delete_result = client.delete_validation(validation_id)

        assert delete_result["success"] is True
        assert delete_result["validation_id"] == validation_id

        # Verify deletion
        with pytest.raises(Exception):
            client.get_validation(validation_id)

    def test_delete_validation_idempotent(self, tmp_path):
        """Test deleting same validation twice is idempotent."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test")

        client = get_mcp_sync_client()
        create_result = client.validate_file(str(test_file))
        validation_id = create_result["validation_id"]

        # Delete twice
        client.delete_validation(validation_id)
        result = client.delete_validation(validation_id)

        # Should still return success
        assert result["success"] is True


class TestRevalidate:
    """Tests for revalidate method."""

    def test_revalidate_success(self, tmp_path):
        """Test re-running validation."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test Document")

        client = get_mcp_sync_client()
        original = client.validate_file(str(test_file))
        original_id = original["validation_id"]

        # Revalidate
        result = client.revalidate(original_id)

        assert result["success"] is True
        assert "new_validation_id" in result
        assert "original_validation_id" in result
        assert result["original_validation_id"] == original_id
        assert result["new_validation_id"] != original_id

    def test_revalidate_creates_new_record(self, tmp_path):
        """Test that revalidate creates a new validation record."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test")

        client = get_mcp_sync_client()
        original = client.validate_file(str(test_file))
        original_id = original["validation_id"]

        # Revalidate
        result = client.revalidate(original_id)
        new_id = result["new_validation_id"]

        # Both records should exist
        original_record = client.get_validation(original_id)
        new_record = client.get_validation(new_id)

        assert original_record["validation"]["id"] == original_id
        assert new_record["validation"]["id"] == new_id

    def test_revalidate_not_found(self):
        """Test error when revalidating non-existent validation."""
        client = get_mcp_sync_client()

        with pytest.raises(Exception) as exc_info:
            client.revalidate("nonexistent-id")

        assert "not found" in str(exc_info.value).lower()

    def test_revalidate_same_file_path(self, tmp_path):
        """Test that revalidate uses same file path."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test")

        client = get_mcp_sync_client()
        original = client.validate_file(str(test_file))
        original_id = original["validation_id"]

        # Revalidate
        result = client.revalidate(original_id)
        new_id = result["new_validation_id"]

        # Check file paths match
        original_record = client.get_validation(original_id)
        new_record = client.get_validation(new_id)

        assert original_record["validation"]["file_path"] == new_record["validation"]["file_path"]


class TestValidationWorkflow:
    """Integration tests for complete validation workflows."""

    def test_complete_validation_lifecycle(self, tmp_path):
        """Test full validation lifecycle: create -> update -> revalidate -> delete."""
        # Create test file
        test_file = tmp_path / "document.md"
        test_file.write_text("# Test Document\n\nContent here.")

        client = get_mcp_sync_client()

        # Step 1: Validate file
        validation = client.validate_file(str(test_file))
        validation_id = validation["validation_id"]
        assert validation["success"] is True

        # Step 2: Retrieve validation
        retrieved = client.get_validation(validation_id)
        assert retrieved["validation"]["id"] == validation_id

        # Step 3: Update validation
        client.update_validation(validation_id, notes="Test notes")
        updated = client.get_validation(validation_id)
        assert updated["validation"]["notes"] == "Test notes"

        # Step 4: Revalidate
        revalidated = client.revalidate(validation_id)
        assert revalidated["new_validation_id"] != validation_id

        # Step 5: Delete original validation
        client.delete_validation(validation_id)

        # Step 6: Verify deletion
        with pytest.raises(Exception):
            client.get_validation(validation_id)

    def test_content_validation_workflow(self):
        """Test workflow with content validation."""
        client = get_mcp_sync_client()

        # Validate content
        content = "# Title\n\nSome content here."
        result = client.validate_content(content, file_path="virtual.md")
        validation_id = result["validation_id"]

        # List validations
        validations = client.list_validations(limit=100)
        assert any(v["id"] == validation_id for v in validations["validations"])

        # Clean up
        client.delete_validation(validation_id)

    def test_multiple_validations_same_file(self, tmp_path):
        """Test multiple validations of the same file."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test")

        client = get_mcp_sync_client()

        # Create multiple validations
        v1 = client.validate_file(str(test_file))
        v2 = client.validate_file(str(test_file))

        assert v1["validation_id"] != v2["validation_id"]

        # List validations for this file
        validations = client.list_validations(file_path=str(test_file))
        assert validations["total"] >= 2


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_list_validations_large_limit(self):
        """Test listing with very large limit."""
        client = get_mcp_sync_client()
        result = client.list_validations(limit=10000)

        assert "validations" in result
        assert isinstance(result["validations"], list)

    def test_update_validation_no_changes(self, tmp_path):
        """Test update with no actual changes."""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test")

        client = get_mcp_sync_client()
        create_result = client.validate_file(str(test_file))
        validation_id = create_result["validation_id"]

        # Update with no parameters (should still succeed)
        result = client.update_validation(validation_id)
        assert result["success"] is True
