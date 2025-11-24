# file: tests/test_enhancement_preview.py
"""
Unit tests for Enhancement Preview System - Phase 3.

Tests cover:
- Diff generation (unified and side-by-side)
- Preview storage and retrieval
- Preview expiration
- Approval workflow
- Preview manager
"""

import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path
import tempfile
import shutil

from agents.enhancement_preview import (
    DiffGenerator,
    DiffLine,
    DiffStatistics,
    EnhancementPreview,
    PreviewStorage,
    PreviewManager,
    get_preview_manager
)
from agents.recommendation_enhancer import (
    EnhancementResult,
    AppliedRecommendation,
    SkippedRecommendation,
    SafetyScore,
    SafetyViolation
)


# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def sample_original():
    """Sample original content."""
    return """# Test Document

## Section 1

This is the original content.
It has multiple lines.

## Section 2

More content here.
"""


@pytest.fixture
def sample_enhanced():
    """Sample enhanced content."""
    return """# Test Document

## Section 1

This is the enhanced content with improvements.
It has multiple lines.
Additional information added.

## Section 2

More content here with updates.
"""


@pytest.fixture
def temp_storage_dir():
    """Create temporary storage directory."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    # Cleanup
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


@pytest.fixture
def sample_enhancement_result(sample_original, sample_enhanced):
    """Create sample EnhancementResult."""
    return EnhancementResult(
        original_content=sample_original,
        enhanced_content=sample_enhanced,
        applied_recommendations=[
            AppliedRecommendation(
                recommendation_id="rec_001",
                recommendation_type="missing_info",
                applied=True,
                changes_made="Added information",
                confidence=0.9
            )
        ],
        skipped_recommendations=[],
        unified_diff="...",
        lines_added=2,
        lines_removed=0,
        safety_score=SafetyScore(
            overall_score=0.95,
            keyword_preservation=1.0,
            structure_preservation=1.0,
            content_stability=0.9,
            technical_accuracy=1.0,
            violations=[],
            warnings=[]
        ),
        enhancement_id="enh_test123",
        processing_time_ms=100
    )


# ==============================================================================
# DiffGenerator Tests
# ==============================================================================

class TestDiffGenerator:
    """Tests for DiffGenerator class."""

    def test_generate_unified_diff(self, sample_original, sample_enhanced):
        """Test unified diff generation."""
        generator = DiffGenerator()

        diff = generator.generate_unified_diff(
            sample_original,
            sample_enhanced,
            fromfile="original.md",
            tofile="enhanced.md"
        )

        assert len(diff) > 0
        assert "original.md" in diff
        assert "enhanced.md" in diff
        assert "enhanced content with improvements" in diff

    def test_generate_unified_diff_no_changes(self):
        """Test unified diff with no changes."""
        generator = DiffGenerator()
        content = "Same content"

        diff = generator.generate_unified_diff(content, content)

        assert diff == "No changes"

    def test_generate_side_by_side_diff(self, sample_original, sample_enhanced):
        """Test side-by-side diff generation."""
        generator = DiffGenerator()

        diff_lines = generator.generate_side_by_side_diff(
            sample_original,
            sample_enhanced
        )

        assert len(diff_lines) > 0

        # Check for different change types
        unchanged = [line for line in diff_lines if line.change_type == "unchanged"]
        added = [line for line in diff_lines if line.change_type == "added"]
        removed = [line for line in diff_lines if line.change_type == "removed"]

        assert len(unchanged) > 0  # Some lines should be unchanged
        assert len(added) > 0  # Some lines should be added

    def test_diff_line_structure(self, sample_original, sample_enhanced):
        """Test DiffLine structure."""
        generator = DiffGenerator()
        diff_lines = generator.generate_side_by_side_diff(
            sample_original,
            sample_enhanced
        )

        for line in diff_lines:
            assert isinstance(line, DiffLine)
            assert line.change_type in ["unchanged", "added", "removed"]
            assert isinstance(line.content, str)

            # Line numbers should be consistent
            if line.change_type == "unchanged":
                assert line.line_number_original is not None
                assert line.line_number_enhanced is not None
            elif line.change_type == "added":
                assert line.line_number_original is None
                assert line.line_number_enhanced is not None
            elif line.change_type == "removed":
                assert line.line_number_original is not None
                assert line.line_number_enhanced is None

    def test_calculate_diff_statistics(self, sample_original, sample_enhanced):
        """Test diff statistics calculation."""
        generator = DiffGenerator()

        diff_lines = generator.generate_side_by_side_diff(
            sample_original,
            sample_enhanced
        )

        stats = generator.calculate_diff_statistics(
            sample_original,
            sample_enhanced,
            diff_lines
        )

        assert isinstance(stats, DiffStatistics)
        assert stats.total_lines_original == len(sample_original.splitlines())
        assert stats.total_lines_enhanced == len(sample_enhanced.splitlines())
        assert stats.lines_added >= 0
        assert stats.lines_removed >= 0
        assert stats.lines_unchanged >= 0
        assert stats.change_percentage >= 0.0


# ==============================================================================
# PreviewStorage Tests
# ==============================================================================

class TestPreviewStorage:
    """Tests for PreviewStorage class."""

    def test_storage_initialization(self, temp_storage_dir):
        """Test storage initialization."""
        storage = PreviewStorage(temp_storage_dir)

        assert storage._storage_dir == temp_storage_dir
        assert temp_storage_dir.exists()

    def test_store_and_retrieve_preview(self, temp_storage_dir):
        """Test storing and retrieving a preview."""
        storage = PreviewStorage(temp_storage_dir)

        preview = EnhancementPreview(
            preview_id="test_preview_001",
            validation_id="val_001",
            file_path="/path/to/file.md",
            original_content="original",
            enhanced_content="enhanced",
            unified_diff="diff",
            side_by_side_diff=[],
            diff_statistics=DiffStatistics(),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )

        # Store
        preview_id = storage.store(preview)
        assert preview_id == "test_preview_001"

        # Retrieve
        retrieved = storage.get(preview_id)
        assert retrieved is not None
        assert retrieved.preview_id == preview_id
        assert retrieved.validation_id == "val_001"
        assert retrieved.original_content == "original"

    def test_get_nonexistent_preview(self, temp_storage_dir):
        """Test retrieving non-existent preview."""
        storage = PreviewStorage(temp_storage_dir)

        preview = storage.get("nonexistent_id")
        assert preview is None

    def test_delete_preview(self, temp_storage_dir):
        """Test deleting a preview."""
        storage = PreviewStorage(temp_storage_dir)

        preview = EnhancementPreview(
            preview_id="test_delete",
            validation_id="val_001",
            file_path="/path/to/file.md",
            original_content="original",
            enhanced_content="enhanced",
            unified_diff="diff",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )

        storage.store(preview)
        assert storage.get("test_delete") is not None

        # Delete
        deleted = storage.delete("test_delete")
        assert deleted is True
        assert storage.get("test_delete") is None

    def test_expired_preview_not_retrieved(self, temp_storage_dir):
        """Test that expired previews are not retrieved."""
        storage = PreviewStorage(temp_storage_dir)

        preview = EnhancementPreview(
            preview_id="test_expired",
            validation_id="val_001",
            file_path="/path/to/file.md",
            original_content="original",
            enhanced_content="enhanced",
            unified_diff="diff",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1)  # Expired
        )

        storage.store(preview)

        # Should return None for expired preview
        retrieved = storage.get("test_expired")
        assert retrieved is None

    def test_cleanup_expired(self, temp_storage_dir):
        """Test cleanup of expired previews."""
        storage = PreviewStorage(temp_storage_dir)

        # Add non-expired preview
        preview1 = EnhancementPreview(
            preview_id="preview_valid",
            validation_id="val_001",
            file_path="/path/to/file.md",
            original_content="original",
            enhanced_content="enhanced",
            unified_diff="diff",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        storage.store(preview1)

        # Add expired preview
        preview2 = EnhancementPreview(
            preview_id="preview_expired",
            validation_id="val_002",
            file_path="/path/to/file2.md",
            original_content="original",
            enhanced_content="enhanced",
            unified_diff="diff",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1)
        )
        storage.store(preview2)

        # Cleanup
        count = storage.cleanup_expired()
        assert count == 1

        # Valid preview should still exist
        assert storage.get("preview_valid") is not None
        # Expired preview should be gone
        assert storage.get("preview_expired") is None

    def test_list_previews(self, temp_storage_dir):
        """Test listing previews with filters."""
        storage = PreviewStorage(temp_storage_dir)

        # Add multiple previews
        for i in range(3):
            preview = EnhancementPreview(
                preview_id=f"preview_{i}",
                validation_id=f"val_{i % 2}",  # Alternate validation IDs
                file_path=f"/path/to/file{i}.md",
                original_content="original",
                enhanced_content="enhanced",
                unified_diff="diff",
                status="pending" if i < 2 else "approved",
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
            )
            storage.store(preview)

        # List all
        all_previews = storage.list_previews()
        assert len(all_previews) == 3

        # Filter by validation_id
        val_0_previews = storage.list_previews(validation_id="val_0")
        assert len(val_0_previews) == 2  # preview_0 and preview_2

        # Filter by status
        pending_previews = storage.list_previews(status="pending")
        assert len(pending_previews) == 2  # preview_0 and preview_1


# ==============================================================================
# EnhancementPreview Tests
# ==============================================================================

class TestEnhancementPreview:
    """Tests for EnhancementPreview class."""

    def test_preview_creation(self):
        """Test creating an enhancement preview."""
        preview = EnhancementPreview(
            preview_id="test_001",
            validation_id="val_001",
            file_path="/path/to/file.md",
            original_content="original",
            enhanced_content="enhanced",
            unified_diff="diff"
        )

        assert preview.preview_id == "test_001"
        assert preview.status == "pending"
        assert not preview.is_expired()

    def test_preview_expiration_check(self):
        """Test expiration checking."""
        # Non-expired
        preview = EnhancementPreview(
            preview_id="test_001",
            validation_id="val_001",
            file_path="/path/to/file.md",
            original_content="original",
            enhanced_content="enhanced",
            unified_diff="diff",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        assert not preview.is_expired()

        # Expired
        expired_preview = EnhancementPreview(
            preview_id="test_002",
            validation_id="val_002",
            file_path="/path/to/file.md",
            original_content="original",
            enhanced_content="enhanced",
            unified_diff="diff",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1)
        )
        assert expired_preview.is_expired()

    def test_is_safe_to_apply(self):
        """Test safety check."""
        # Safe preview
        safe_preview = EnhancementPreview(
            preview_id="test_001",
            validation_id="val_001",
            file_path="/path/to/file.md",
            original_content="original",
            enhanced_content="enhanced",
            unified_diff="diff",
            safety_score={"overall_score": 0.9, "is_safe_to_apply": True}
        )
        assert safe_preview.is_safe_to_apply()

        # Unsafe preview
        unsafe_preview = EnhancementPreview(
            preview_id="test_002",
            validation_id="val_002",
            file_path="/path/to/file.md",
            original_content="original",
            enhanced_content="enhanced",
            unified_diff="diff",
            safety_score={"overall_score": 0.5, "is_safe_to_apply": False}
        )
        assert not unsafe_preview.is_safe_to_apply()

    def test_to_dict_serialization(self):
        """Test serialization to dictionary."""
        preview = EnhancementPreview(
            preview_id="test_001",
            validation_id="val_001",
            file_path="/path/to/file.md",
            original_content="original",
            enhanced_content="enhanced",
            unified_diff="diff",
            side_by_side_diff=[
                DiffLine(1, 1, "line 1", "unchanged"),
                DiffLine(2, 2, "line 2", "unchanged")
            ],
            diff_statistics=DiffStatistics(
                lines_added=1,
                lines_removed=0,
                total_lines_original=10,
                total_lines_enhanced=11
            )
        )

        data = preview.to_dict()

        assert data["preview_id"] == "test_001"
        assert data["validation_id"] == "val_001"
        assert "side_by_side_diff" in data
        assert len(data["side_by_side_diff"]) == 2
        assert "diff_statistics" in data
        assert data["diff_statistics"]["lines_added"] == 1


# ==============================================================================
# PreviewManager Tests
# ==============================================================================

class TestPreviewManager:
    """Tests for PreviewManager class."""

    def test_manager_initialization(self, temp_storage_dir):
        """Test manager initialization."""
        manager = PreviewManager(temp_storage_dir)

        assert manager.storage is not None
        assert manager.diff_generator is not None

    def test_create_preview(self, temp_storage_dir, sample_enhancement_result):
        """Test creating a preview."""
        manager = PreviewManager(temp_storage_dir)

        preview = manager.create_preview(
            validation_id="val_001",
            file_path="/path/to/file.md",
            enhancement_result=sample_enhancement_result,
            created_by="test_user",
            expiration_minutes=30
        )

        assert preview.preview_id.startswith("prev_")
        assert preview.validation_id == "val_001"
        assert preview.file_path == "/path/to/file.md"
        assert len(preview.side_by_side_diff) > 0
        assert preview.diff_statistics is not None
        assert preview.created_by == "test_user"

    def test_get_preview(self, temp_storage_dir, sample_enhancement_result):
        """Test getting a preview."""
        manager = PreviewManager(temp_storage_dir)

        # Create preview
        preview = manager.create_preview(
            validation_id="val_001",
            file_path="/path/to/file.md",
            enhancement_result=sample_enhancement_result
        )

        # Retrieve it
        retrieved = manager.get_preview(preview.preview_id)
        assert retrieved is not None
        assert retrieved.preview_id == preview.preview_id

    def test_approve_preview(self, temp_storage_dir, sample_enhancement_result):
        """Test approving a preview."""
        manager = PreviewManager(temp_storage_dir)

        # Create preview
        preview = manager.create_preview(
            validation_id="val_001",
            file_path="/path/to/file.md",
            enhancement_result=sample_enhancement_result
        )

        assert preview.status == "pending"

        # Approve
        approved = manager.approve_preview(preview.preview_id, "test_user")
        assert approved is True

        # Check status
        retrieved = manager.get_preview(preview.preview_id)
        assert retrieved.status == "approved"

    def test_reject_preview(self, temp_storage_dir, sample_enhancement_result):
        """Test rejecting a preview."""
        manager = PreviewManager(temp_storage_dir)

        # Create preview
        preview = manager.create_preview(
            validation_id="val_001",
            file_path="/path/to/file.md",
            enhancement_result=sample_enhancement_result
        )

        # Reject
        rejected = manager.reject_preview(
            preview.preview_id,
            "test_user",
            "Not ready"
        )
        assert rejected is True

        # Check status
        retrieved = manager.get_preview(preview.preview_id)
        assert retrieved.status == "rejected"

    def test_mark_applied(self, temp_storage_dir, sample_enhancement_result):
        """Test marking preview as applied."""
        manager = PreviewManager(temp_storage_dir)

        # Create and approve preview
        preview = manager.create_preview(
            validation_id="val_001",
            file_path="/path/to/file.md",
            enhancement_result=sample_enhancement_result
        )
        manager.approve_preview(preview.preview_id, "test_user")

        # Mark as applied
        marked = manager.mark_applied(preview.preview_id)
        assert marked is True

        # Check status
        retrieved = manager.get_preview(preview.preview_id)
        assert retrieved.status == "applied"


# ==============================================================================
# Integration Tests
# ==============================================================================

class TestPreviewIntegration:
    """Integration tests for complete preview workflow."""

    def test_full_preview_workflow(self, temp_storage_dir, sample_enhancement_result):
        """Test complete workflow from creation to application."""
        manager = PreviewManager(temp_storage_dir)

        # 1. Create preview
        preview = manager.create_preview(
            validation_id="val_001",
            file_path="/path/to/file.md",
            enhancement_result=sample_enhancement_result,
            created_by="user1",
            expiration_minutes=30
        )

        assert preview.status == "pending"
        assert not preview.is_expired()
        assert preview.is_safe_to_apply()

        # 2. Retrieve preview
        retrieved = manager.get_preview(preview.preview_id)
        assert retrieved is not None
        assert retrieved.preview_id == preview.preview_id

        # 3. Approve preview
        approved = manager.approve_preview(preview.preview_id, "user2")
        assert approved is True

        # 4. Mark as applied
        applied = manager.mark_applied(preview.preview_id)
        assert applied is True

        # 5. Verify final state
        final = manager.get_preview(preview.preview_id)
        assert final.status == "applied"

    def test_rejection_workflow(self, temp_storage_dir, sample_enhancement_result):
        """Test rejection workflow."""
        manager = PreviewManager(temp_storage_dir)

        # Create preview
        preview = manager.create_preview(
            validation_id="val_001",
            file_path="/path/to/file.md",
            enhancement_result=sample_enhancement_result
        )

        # Reject
        rejected = manager.reject_preview(
            preview.preview_id,
            "user1",
            "Changes not acceptable"
        )
        assert rejected is True

        # Verify cannot approve rejected preview
        retrieved = manager.get_preview(preview.preview_id)
        assert retrieved.status == "rejected"

        # Trying to approve should fail (preview status check)
        approved = manager.approve_preview(preview.preview_id, "user2")
        assert approved is False  # Cannot approve rejected preview


# ==============================================================================
# Run tests
# ==============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
