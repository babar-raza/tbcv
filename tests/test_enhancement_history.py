# file: tests/test_enhancement_history.py
"""Unit tests for Enhancement History - Phase 4."""

import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path
import tempfile
import shutil

from agents.enhancement_history import (
    EnhancementHistory,
    EnhancementRecord,
    RollbackPoint,
    get_history_manager
)


@pytest.fixture
def temp_history_dir():
    """Create temporary history directory."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


class TestEnhancementHistory:
    """Tests for EnhancementHistory."""

    def test_record_enhancement(self, temp_history_dir):
        """Test recording an enhancement."""
        history = EnhancementHistory(temp_history_dir)

        record = history.record_enhancement(
            enhancement_id="enh_test001",
            validation_id="val_001",
            file_path="/path/to/file.md",
            original_content="original",
            enhanced_content="enhanced",
            recommendations_applied=["rec_001", "rec_002"],
            safety_score=0.95,
            keyword_preservation=1.0,
            structure_preservation=0.9,
            applied_by="test_user",
            processing_time_ms=100
        )

        assert record.enhancement_id == "enh_test001"
        assert len(record.recommendations_applied) == 2
        assert record.safety_score == 0.95

    def test_create_rollback_point(self, temp_history_dir):
        """Test creating rollback point."""
        history = EnhancementHistory(temp_history_dir)

        rollback = history.create_rollback_point(
            enhancement_id="enh_test001",
            file_path="/path/to/file.md",
            content="original content",
            retention_days=30
        )

        assert rollback.rollback_id == "rb_enh_test001"
        assert rollback.content_backup == "original content"

    def test_rollback_enhancement(self, temp_history_dir, tmp_path):
        """Test rollback functionality."""
        history = EnhancementHistory(temp_history_dir)

        # Create test file
        test_file = tmp_path / "test.md"
        test_file.write_text("original", encoding='utf-8')

        # Record enhancement
        history.record_enhancement(
            enhancement_id="enh_test001",
            validation_id="val_001",
            file_path=str(test_file),
            original_content="original",
            enhanced_content="enhanced",
            recommendations_applied=["rec_001"],
            safety_score=0.95,
            keyword_preservation=1.0,
            structure_preservation=1.0
        )

        # Create rollback point
        history.create_rollback_point(
            enhancement_id="enh_test001",
            file_path=str(test_file),
            content="original"
        )

        # Modify file
        test_file.write_text("enhanced", encoding='utf-8')
        assert test_file.read_text(encoding='utf-8') == "enhanced"

        # Rollback
        success = history.rollback_enhancement("enh_test001", "test_user")
        assert success is True
        assert test_file.read_text(encoding='utf-8') == "original"

    def test_list_enhancements(self, temp_history_dir):
        """Test listing enhancements."""
        history = EnhancementHistory(temp_history_dir)

        # Create multiple records
        for i in range(3):
            history.record_enhancement(
                enhancement_id=f"enh_test{i:03d}",
                validation_id=f"val_{i}",
                file_path=f"/path/to/file{i}.md",
                original_content="original",
                enhanced_content="enhanced",
                recommendations_applied=[f"rec_{i}"],
                safety_score=0.95,
                keyword_preservation=1.0,
                structure_preservation=1.0
            )

        records = history.list_enhancements(limit=10)
        assert len(records) == 3

    def test_cleanup_expired_rollbacks(self, temp_history_dir):
        """Test cleanup of expired rollbacks."""
        history = EnhancementHistory(temp_history_dir)

        # Create expired rollback
        rollback = RollbackPoint(
            rollback_id="rb_expired",
            enhancement_id="enh_expired",
            file_path="/path/to/file.md",
            content_backup="content",
            file_hash="hash",
            created_at=datetime.now(timezone.utc) - timedelta(days=31),
            expires_at=datetime.now(timezone.utc) - timedelta(days=1)
        )

        # Save manually
        import json
        meta_file = history._rollback_dir / f"{rollback.rollback_id}.json"
        with open(meta_file, 'w') as f:
            json.dump(rollback.to_dict(), f)

        content_file = history._rollback_dir / f"{rollback.rollback_id}.txt"
        content_file.write_text("content")

        # Cleanup
        count = history.cleanup_expired_rollbacks()
        assert count == 1
        assert not meta_file.exists()
        assert not content_file.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
