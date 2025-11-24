# file: agents/enhancement_preview.py
"""
Enhancement Preview System - Preview, storage, and approval workflow.

Provides:
- Preview generation without file modification
- Temporary preview storage with expiration
- Approval workflow management
- Diff generation and visualization
"""

from __future__ import annotations

import uuid
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from pathlib import Path
import difflib

from agents.recommendation_enhancer import (
    EnhancementResult,
    SafetyScore,
    AppliedRecommendation,
    SkippedRecommendation
)
from core.logging import get_logger

logger = get_logger(__name__)


# ==============================================================================
# Data Classes
# ==============================================================================

@dataclass
class DiffLine:
    """Represents a single line in a diff."""

    line_number_original: Optional[int]
    line_number_enhanced: Optional[int]
    content: str
    change_type: str  # "unchanged", "added", "removed", "modified"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "line_number_original": self.line_number_original,
            "line_number_enhanced": self.line_number_enhanced,
            "content": self.content,
            "change_type": self.change_type
        }


@dataclass
class DiffStatistics:
    """Statistics about diff changes."""

    lines_added: int = 0
    lines_removed: int = 0
    lines_modified: int = 0
    lines_unchanged: int = 0
    total_lines_original: int = 0
    total_lines_enhanced: int = 0
    change_percentage: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class EnhancementPreview:
    """Complete preview of proposed enhancement."""

    preview_id: str
    validation_id: str
    file_path: str

    # Content
    original_content: str
    enhanced_content: str

    # Diff information
    unified_diff: str
    side_by_side_diff: List[DiffLine] = field(default_factory=list)
    diff_statistics: Optional[DiffStatistics] = None

    # Recommendations
    applied_recommendations: List[Dict[str, Any]] = field(default_factory=list)
    skipped_recommendations: List[Dict[str, Any]] = field(default_factory=list)

    # Safety information
    safety_score: Optional[Dict[str, Any]] = None
    preservation_report: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(minutes=30))
    created_by: str = "system"

    # Status
    status: str = "pending"  # pending, approved, rejected, applied, expired

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "preview_id": self.preview_id,
            "validation_id": self.validation_id,
            "file_path": self.file_path,
            "original_content": self.original_content,
            "enhanced_content": self.enhanced_content,
            "unified_diff": self.unified_diff,
            "side_by_side_diff": [line.to_dict() for line in self.side_by_side_diff],
            "diff_statistics": self.diff_statistics.to_dict() if self.diff_statistics else None,
            "applied_recommendations": self.applied_recommendations,
            "skipped_recommendations": self.skipped_recommendations,
            "safety_score": self.safety_score,
            "preservation_report": self.preservation_report,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "created_by": self.created_by,
            "status": self.status
        }

    def is_expired(self) -> bool:
        """Check if preview has expired."""
        return datetime.now(timezone.utc) > self.expires_at

    def is_safe_to_apply(self) -> bool:
        """Check if preview is safe to apply."""
        if self.safety_score is None:
            return False
        return self.safety_score.get("is_safe_to_apply", False)


# ==============================================================================
# Diff Generation
# ==============================================================================

class DiffGenerator:
    """Generates various diff formats for previews."""

    @staticmethod
    def generate_unified_diff(
        original: str,
        enhanced: str,
        fromfile: str = "original",
        tofile: str = "enhanced"
    ) -> str:
        """
        Generate unified diff format.

        Args:
            original: Original content
            enhanced: Enhanced content
            fromfile: Label for original file
            tofile: Label for enhanced file

        Returns:
            Unified diff string
        """
        diff_lines = list(difflib.unified_diff(
            original.splitlines(keepends=True),
            enhanced.splitlines(keepends=True),
            fromfile=fromfile,
            tofile=tofile,
            lineterm=''
        ))

        return "".join(diff_lines) if diff_lines else "No changes"

    @staticmethod
    def generate_side_by_side_diff(
        original: str,
        enhanced: str
    ) -> List[DiffLine]:
        """
        Generate side-by-side diff with line-by-line comparison.

        Args:
            original: Original content
            enhanced: Enhanced content

        Returns:
            List of DiffLine objects
        """
        original_lines = original.splitlines()
        enhanced_lines = enhanced.splitlines()

        # Use SequenceMatcher for line-by-line comparison
        matcher = difflib.SequenceMatcher(None, original_lines, enhanced_lines)

        diff_lines: List[DiffLine] = []
        orig_line_num = 1
        enh_line_num = 1

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                # Unchanged lines
                for i, j in zip(range(i1, i2), range(j1, j2)):
                    diff_lines.append(DiffLine(
                        line_number_original=orig_line_num,
                        line_number_enhanced=enh_line_num,
                        content=original_lines[i],
                        change_type="unchanged"
                    ))
                    orig_line_num += 1
                    enh_line_num += 1

            elif tag == 'delete':
                # Removed lines
                for i in range(i1, i2):
                    diff_lines.append(DiffLine(
                        line_number_original=orig_line_num,
                        line_number_enhanced=None,
                        content=original_lines[i],
                        change_type="removed"
                    ))
                    orig_line_num += 1

            elif tag == 'insert':
                # Added lines
                for j in range(j1, j2):
                    diff_lines.append(DiffLine(
                        line_number_original=None,
                        line_number_enhanced=enh_line_num,
                        content=enhanced_lines[j],
                        change_type="added"
                    ))
                    enh_line_num += 1

            elif tag == 'replace':
                # Modified lines
                # Mark as removed from original
                for i in range(i1, i2):
                    diff_lines.append(DiffLine(
                        line_number_original=orig_line_num,
                        line_number_enhanced=None,
                        content=original_lines[i],
                        change_type="removed"
                    ))
                    orig_line_num += 1

                # Mark as added in enhanced
                for j in range(j1, j2):
                    diff_lines.append(DiffLine(
                        line_number_original=None,
                        line_number_enhanced=enh_line_num,
                        content=enhanced_lines[j],
                        change_type="added"
                    ))
                    enh_line_num += 1

        return diff_lines

    @staticmethod
    def calculate_diff_statistics(
        original: str,
        enhanced: str,
        side_by_side_diff: List[DiffLine]
    ) -> DiffStatistics:
        """
        Calculate statistics about the diff.

        Args:
            original: Original content
            enhanced: Enhanced content
            side_by_side_diff: Pre-computed diff lines

        Returns:
            DiffStatistics object
        """
        lines_added = sum(1 for line in side_by_side_diff if line.change_type == "added")
        lines_removed = sum(1 for line in side_by_side_diff if line.change_type == "removed")
        lines_unchanged = sum(1 for line in side_by_side_diff if line.change_type == "unchanged")
        lines_modified = min(lines_added, lines_removed)

        total_original = len(original.splitlines())
        total_enhanced = len(enhanced.splitlines())

        change_percentage = 0.0
        if total_original > 0:
            changed_lines = lines_added + lines_removed
            change_percentage = (changed_lines / total_original) * 100

        return DiffStatistics(
            lines_added=lines_added,
            lines_removed=lines_removed,
            lines_modified=lines_modified,
            lines_unchanged=lines_unchanged,
            total_lines_original=total_original,
            total_lines_enhanced=total_enhanced,
            change_percentage=change_percentage
        )


# ==============================================================================
# Preview Storage
# ==============================================================================

class PreviewStorage:
    """
    Manages temporary storage of enhancement previews.

    Uses in-memory storage with optional file-based persistence.
    """

    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Initialize preview storage.

        Args:
            storage_dir: Optional directory for persistent storage
        """
        self._previews: Dict[str, EnhancementPreview] = {}
        self._storage_dir = storage_dir
        if storage_dir:
            storage_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized PreviewStorage (dir={storage_dir})")

    def store(self, preview: EnhancementPreview) -> str:
        """
        Store a preview.

        Args:
            preview: EnhancementPreview to store

        Returns:
            preview_id
        """
        self._previews[preview.preview_id] = preview

        # Optionally persist to disk
        if self._storage_dir:
            preview_file = self._storage_dir / f"{preview.preview_id}.json"
            try:
                with open(preview_file, 'w', encoding='utf-8') as f:
                    json.dump(preview.to_dict(), f, indent=2)
                logger.debug(f"Persisted preview {preview.preview_id} to disk")
            except Exception as e:
                logger.warning(f"Failed to persist preview to disk: {e}")

        logger.info(f"Stored preview {preview.preview_id} (expires: {preview.expires_at.isoformat()})")
        return preview.preview_id

    def get(self, preview_id: str) -> Optional[EnhancementPreview]:
        """
        Retrieve a preview by ID.

        Args:
            preview_id: Preview ID to retrieve

        Returns:
            EnhancementPreview or None if not found/expired
        """
        preview = self._previews.get(preview_id)

        if preview is None and self._storage_dir:
            # Try loading from disk
            preview_file = self._storage_dir / f"{preview_id}.json"
            if preview_file.exists():
                try:
                    with open(preview_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        preview = self._reconstruct_preview(data)
                        self._previews[preview_id] = preview
                    logger.debug(f"Loaded preview {preview_id} from disk")
                except Exception as e:
                    logger.error(f"Failed to load preview from disk: {e}")

        if preview and preview.is_expired():
            logger.warning(f"Preview {preview_id} has expired")
            self.delete(preview_id)
            return None

        return preview

    def delete(self, preview_id: str) -> bool:
        """
        Delete a preview.

        Args:
            preview_id: Preview ID to delete

        Returns:
            True if deleted, False if not found
        """
        if preview_id in self._previews:
            del self._previews[preview_id]

            if self._storage_dir:
                preview_file = self._storage_dir / f"{preview_id}.json"
                if preview_file.exists():
                    try:
                        preview_file.unlink()
                        logger.debug(f"Deleted preview file {preview_id}")
                    except Exception as e:
                        logger.warning(f"Failed to delete preview file: {e}")

            logger.info(f"Deleted preview {preview_id}")
            return True

        return False

    def cleanup_expired(self) -> int:
        """
        Remove all expired previews.

        Returns:
            Number of previews removed
        """
        now = datetime.now(timezone.utc)
        expired_ids = [
            pid for pid, preview in self._previews.items()
            if preview.expires_at < now
        ]

        for pid in expired_ids:
            self.delete(pid)

        if expired_ids:
            logger.info(f"Cleaned up {len(expired_ids)} expired previews")

        return len(expired_ids)

    def list_previews(
        self,
        validation_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[EnhancementPreview]:
        """
        List previews with optional filters.

        Args:
            validation_id: Filter by validation ID
            status: Filter by status

        Returns:
            List of EnhancementPreview objects
        """
        previews = list(self._previews.values())

        if validation_id:
            previews = [p for p in previews if p.validation_id == validation_id]

        if status:
            previews = [p for p in previews if p.status == status]

        # Sort by creation time (newest first)
        previews.sort(key=lambda p: p.created_at, reverse=True)

        return previews

    def _reconstruct_preview(self, data: Dict[str, Any]) -> EnhancementPreview:
        """Reconstruct EnhancementPreview from dict."""
        # Reconstruct diff lines
        side_by_side_diff = []
        for line_data in data.get("side_by_side_diff", []):
            side_by_side_diff.append(DiffLine(
                line_number_original=line_data.get("line_number_original"),
                line_number_enhanced=line_data.get("line_number_enhanced"),
                content=line_data["content"],
                change_type=line_data["change_type"]
            ))

        # Reconstruct diff statistics
        diff_stats = None
        if data.get("diff_statistics"):
            stats_data = data["diff_statistics"]
            diff_stats = DiffStatistics(
                lines_added=stats_data["lines_added"],
                lines_removed=stats_data["lines_removed"],
                lines_modified=stats_data["lines_modified"],
                lines_unchanged=stats_data["lines_unchanged"],
                total_lines_original=stats_data["total_lines_original"],
                total_lines_enhanced=stats_data["total_lines_enhanced"],
                change_percentage=stats_data["change_percentage"]
            )

        return EnhancementPreview(
            preview_id=data["preview_id"],
            validation_id=data["validation_id"],
            file_path=data["file_path"],
            original_content=data["original_content"],
            enhanced_content=data["enhanced_content"],
            unified_diff=data["unified_diff"],
            side_by_side_diff=side_by_side_diff,
            diff_statistics=diff_stats,
            applied_recommendations=data.get("applied_recommendations", []),
            skipped_recommendations=data.get("skipped_recommendations", []),
            safety_score=data.get("safety_score"),
            preservation_report=data.get("preservation_report", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]),
            created_by=data.get("created_by", "system"),
            status=data.get("status", "pending")
        )


# ==============================================================================
# Preview Manager
# ==============================================================================

class PreviewManager:
    """
    High-level manager for enhancement previews.

    Coordinates preview generation, storage, and approval workflow.
    """

    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Initialize preview manager.

        Args:
            storage_dir: Optional directory for persistent storage
        """
        self.storage = PreviewStorage(storage_dir)
        self.diff_generator = DiffGenerator()

        logger.info("Initialized PreviewManager")

    def create_preview(
        self,
        validation_id: str,
        file_path: str,
        enhancement_result: EnhancementResult,
        created_by: str = "system",
        expiration_minutes: int = 30
    ) -> EnhancementPreview:
        """
        Create a new enhancement preview.

        Args:
            validation_id: Associated validation ID
            file_path: Path to file being enhanced
            enhancement_result: Result from RecommendationEnhancer
            created_by: User/system creating the preview
            expiration_minutes: Minutes until preview expires

        Returns:
            EnhancementPreview object
        """
        # Generate preview ID
        preview_id = f"prev_{uuid.uuid4().hex[:12]}"

        # Generate diffs
        unified_diff = self.diff_generator.generate_unified_diff(
            enhancement_result.original_content,
            enhancement_result.enhanced_content,
            fromfile=file_path,
            tofile=f"{file_path} (enhanced)"
        )

        side_by_side_diff = self.diff_generator.generate_side_by_side_diff(
            enhancement_result.original_content,
            enhancement_result.enhanced_content
        )

        diff_stats = self.diff_generator.calculate_diff_statistics(
            enhancement_result.original_content,
            enhancement_result.enhanced_content,
            side_by_side_diff
        )

        # Create preservation report
        preservation_report = {
            "keywords_checked": True,
            "structure_checked": True,
            "code_blocks_checked": True,
            "safety_threshold_met": enhancement_result.safety_score.is_safe_to_apply() if enhancement_result.safety_score else False
        }

        # Create preview
        preview = EnhancementPreview(
            preview_id=preview_id,
            validation_id=validation_id,
            file_path=file_path,
            original_content=enhancement_result.original_content,
            enhanced_content=enhancement_result.enhanced_content,
            unified_diff=unified_diff,
            side_by_side_diff=side_by_side_diff,
            diff_statistics=diff_stats,
            applied_recommendations=[r.to_dict() for r in enhancement_result.applied_recommendations],
            skipped_recommendations=[r.to_dict() for r in enhancement_result.skipped_recommendations],
            safety_score=enhancement_result.safety_score.to_dict() if enhancement_result.safety_score else None,
            preservation_report=preservation_report,
            created_by=created_by,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=expiration_minutes)
        )

        # Store preview
        self.storage.store(preview)

        logger.info(
            f"Created preview {preview_id} for validation {validation_id} "
            f"(applied={len(preview.applied_recommendations)}, "
            f"skipped={len(preview.skipped_recommendations)})"
        )

        return preview

    def get_preview(self, preview_id: str) -> Optional[EnhancementPreview]:
        """
        Get preview by ID.

        Args:
            preview_id: Preview ID

        Returns:
            EnhancementPreview or None
        """
        return self.storage.get(preview_id)

    def approve_preview(self, preview_id: str, approved_by: str) -> bool:
        """
        Approve a preview for application.

        Args:
            preview_id: Preview ID
            approved_by: User approving

        Returns:
            True if approved, False if not found/invalid
        """
        preview = self.storage.get(preview_id)
        if not preview:
            logger.warning(f"Cannot approve preview {preview_id}: not found")
            return False

        if preview.status != "pending":
            logger.warning(f"Cannot approve preview {preview_id}: status is {preview.status}")
            return False

        preview.status = "approved"
        self.storage.store(preview)  # Update storage

        logger.info(f"Preview {preview_id} approved by {approved_by}")
        return True

    def reject_preview(self, preview_id: str, rejected_by: str, reason: str = "") -> bool:
        """
        Reject a preview.

        Args:
            preview_id: Preview ID
            rejected_by: User rejecting
            reason: Reason for rejection

        Returns:
            True if rejected, False if not found
        """
        preview = self.storage.get(preview_id)
        if not preview:
            logger.warning(f"Cannot reject preview {preview_id}: not found")
            return False

        preview.status = "rejected"
        self.storage.store(preview)  # Update storage

        logger.info(f"Preview {preview_id} rejected by {rejected_by} (reason: {reason})")
        return True

    def mark_applied(self, preview_id: str) -> bool:
        """
        Mark a preview as applied.

        Args:
            preview_id: Preview ID

        Returns:
            True if marked, False if not found
        """
        preview = self.storage.get(preview_id)
        if not preview:
            return False

        preview.status = "applied"
        self.storage.store(preview)

        logger.info(f"Preview {preview_id} marked as applied")
        return True

    def cleanup_expired(self) -> int:
        """
        Clean up expired previews.

        Returns:
            Number of previews cleaned up
        """
        return self.storage.cleanup_expired()


# ==============================================================================
# Global Preview Manager Instance
# ==============================================================================

_preview_manager: Optional[PreviewManager] = None


def get_preview_manager(storage_dir: Optional[Path] = None) -> PreviewManager:
    """
    Get or create global PreviewManager instance.

    Args:
        storage_dir: Optional storage directory (used on first call)

    Returns:
        PreviewManager instance
    """
    global _preview_manager
    if _preview_manager is None:
        if storage_dir is None:
            storage_dir = Path("./data/previews")
        _preview_manager = PreviewManager(storage_dir)
    return _preview_manager
