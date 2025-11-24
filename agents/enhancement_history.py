# file: agents/enhancement_history.py
"""
Enhancement History and Rollback System - Phase 4.

Provides:
- Enhancement history tracking in database
- Rollback mechanism with content snapshots
- Audit trail queries
"""

from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from pathlib import Path

from core.logging import get_logger
from core.database import db_manager

logger = get_logger(__name__)


@dataclass
class EnhancementRecord:
    """Complete record of an enhancement operation."""

    enhancement_id: str
    validation_id: str
    file_path: str

    # Content snapshots
    original_content: str
    enhanced_content: str
    original_hash: str
    enhanced_hash: str

    # Recommendations
    recommendations_applied: List[str]  # IDs
    recommendations_count: int

    # Safety metrics
    safety_score: float
    keyword_preservation: float
    structure_preservation: float

    # Metadata
    applied_by: str
    applied_at: datetime
    model_used: str
    processing_time_ms: int

    # Rollback info
    rollback_available: bool
    rolled_back: bool = False
    rolled_back_at: Optional[datetime] = None
    rolled_back_by: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "enhancement_id": self.enhancement_id,
            "validation_id": self.validation_id,
            "file_path": self.file_path,
            "original_hash": self.original_hash,
            "enhanced_hash": self.enhanced_hash,
            "recommendations_applied": self.recommendations_applied,
            "recommendations_count": self.recommendations_count,
            "safety_score": self.safety_score,
            "keyword_preservation": self.keyword_preservation,
            "structure_preservation": self.structure_preservation,
            "applied_by": self.applied_by,
            "applied_at": self.applied_at.isoformat(),
            "model_used": self.model_used,
            "processing_time_ms": self.processing_time_ms,
            "rollback_available": self.rollback_available,
            "rolled_back": self.rolled_back,
            "rolled_back_at": self.rolled_back_at.isoformat() if self.rolled_back_at else None,
            "rolled_back_by": self.rolled_back_by
        }


@dataclass
class RollbackPoint:
    """Rollback point with content snapshot."""

    rollback_id: str
    enhancement_id: str
    file_path: str
    content_backup: str
    file_hash: str
    created_at: datetime
    expires_at: datetime  # 30 days default

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "rollback_id": self.rollback_id,
            "enhancement_id": self.enhancement_id,
            "file_path": self.file_path,
            "file_hash": self.file_hash,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat()
        }


class EnhancementHistory:
    """Manages enhancement history and audit trail."""

    def __init__(self, storage_dir: Optional[Path] = None):
        """Initialize history manager."""
        self._storage_dir = storage_dir or Path("./data/enhancement_history")
        self._storage_dir.mkdir(parents=True, exist_ok=True)

        self._rollback_dir = self._storage_dir / "rollback_points"
        self._rollback_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized EnhancementHistory (dir={self._storage_dir})")

    @staticmethod
    def _calculate_hash(content: str) -> str:
        """Calculate SHA256 hash of content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def record_enhancement(
        self,
        enhancement_id: str,
        validation_id: str,
        file_path: str,
        original_content: str,
        enhanced_content: str,
        recommendations_applied: List[str],
        safety_score: float,
        keyword_preservation: float,
        structure_preservation: float,
        applied_by: str = "system",
        model_used: str = "llama3.2",
        processing_time_ms: int = 0
    ) -> EnhancementRecord:
        """
        Record an enhancement operation.

        Args:
            enhancement_id: Unique enhancement ID
            validation_id: Associated validation ID
            file_path: Path to enhanced file
            original_content: Content before enhancement
            enhanced_content: Content after enhancement
            recommendations_applied: List of recommendation IDs applied
            safety_score: Overall safety score
            keyword_preservation: Keyword preservation score
            structure_preservation: Structure preservation score
            applied_by: User/system that applied
            model_used: LLM model used
            processing_time_ms: Processing time

        Returns:
            EnhancementRecord
        """
        record = EnhancementRecord(
            enhancement_id=enhancement_id,
            validation_id=validation_id,
            file_path=file_path,
            original_content=original_content,
            enhanced_content=enhanced_content,
            original_hash=self._calculate_hash(original_content),
            enhanced_hash=self._calculate_hash(enhanced_content),
            recommendations_applied=recommendations_applied,
            recommendations_count=len(recommendations_applied),
            safety_score=safety_score,
            keyword_preservation=keyword_preservation,
            structure_preservation=structure_preservation,
            applied_by=applied_by,
            applied_at=datetime.now(timezone.utc),
            model_used=model_used,
            processing_time_ms=processing_time_ms,
            rollback_available=True
        )

        # Persist to disk
        record_file = self._storage_dir / f"{enhancement_id}.json"
        with open(record_file, 'w', encoding='utf-8') as f:
            json.dump(record.to_dict(), f, indent=2)

        logger.info(
            f"Recorded enhancement {enhancement_id} for {file_path} "
            f"({len(recommendations_applied)} recommendations, safety={safety_score:.2f})"
        )

        return record

    def create_rollback_point(
        self,
        enhancement_id: str,
        file_path: str,
        content: str,
        retention_days: int = 30
    ) -> RollbackPoint:
        """
        Create rollback point before applying enhancement.

        Args:
            enhancement_id: Enhancement ID
            file_path: File path
            content: Original content to backup
            retention_days: Days to retain rollback point

        Returns:
            RollbackPoint
        """
        rollback_point = RollbackPoint(
            rollback_id=f"rb_{enhancement_id}",
            enhancement_id=enhancement_id,
            file_path=file_path,
            content_backup=content,
            file_hash=self._calculate_hash(content),
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=retention_days)
        )

        # Save rollback content
        rollback_file = self._rollback_dir / f"{rollback_point.rollback_id}.txt"
        rollback_file.write_text(content, encoding='utf-8')

        # Save metadata
        meta_file = self._rollback_dir / f"{rollback_point.rollback_id}.json"
        with open(meta_file, 'w', encoding='utf-8') as f:
            json.dump(rollback_point.to_dict(), f, indent=2)

        logger.info(f"Created rollback point {rollback_point.rollback_id} for {file_path}")

        return rollback_point

    def rollback_enhancement(
        self,
        enhancement_id: str,
        rolled_back_by: str = "user"
    ) -> bool:
        """
        Rollback an enhancement.

        Args:
            enhancement_id: Enhancement ID to rollback
            rolled_back_by: User performing rollback

        Returns:
            True if successful, False if failed
        """
        rollback_id = f"rb_{enhancement_id}"

        # Load rollback point
        rollback_file = self._rollback_dir / f"{rollback_id}.txt"
        meta_file = self._rollback_dir / f"{rollback_id}.json"

        if not rollback_file.exists() or not meta_file.exists():
            logger.error(f"Rollback point {rollback_id} not found")
            return False

        # Load metadata
        with open(meta_file, 'r', encoding='utf-8') as f:
            meta = json.load(f)

        # Check expiration
        expires_at = datetime.fromisoformat(meta["expires_at"])
        if datetime.now(timezone.utc) > expires_at:
            logger.error(f"Rollback point {rollback_id} has expired")
            return False

        # Restore content
        file_path = Path(meta["file_path"])
        original_content = rollback_file.read_text(encoding='utf-8')

        # Create backup of current state before rollback
        current_backup = file_path.with_suffix(f"{file_path.suffix}.pre_rollback_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        if file_path.exists():
            current_backup.write_text(file_path.read_text(encoding='utf-8'), encoding='utf-8')

        # Write original content back
        file_path.write_text(original_content, encoding='utf-8')

        # Update enhancement record
        record_file = self._storage_dir / f"{enhancement_id}.json"
        if record_file.exists():
            with open(record_file, 'r', encoding='utf-8') as f:
                record_data = json.load(f)

            record_data["rolled_back"] = True
            record_data["rolled_back_at"] = datetime.now(timezone.utc).isoformat()
            record_data["rolled_back_by"] = rolled_back_by
            record_data["rollback_available"] = False

            with open(record_file, 'w', encoding='utf-8') as f:
                json.dump(record_data, f, indent=2)

        logger.info(
            f"Rolled back enhancement {enhancement_id} to original state "
            f"(by {rolled_back_by})"
        )

        return True

    def get_enhancement_record(self, enhancement_id: str) -> Optional[EnhancementRecord]:
        """Get enhancement record by ID."""
        record_file = self._storage_dir / f"{enhancement_id}.json"

        if not record_file.exists():
            return None

        with open(record_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Reconstruct record
        return EnhancementRecord(
            enhancement_id=data["enhancement_id"],
            validation_id=data["validation_id"],
            file_path=data["file_path"],
            original_content="",  # Not stored in summary
            enhanced_content="",  # Not stored in summary
            original_hash=data["original_hash"],
            enhanced_hash=data["enhanced_hash"],
            recommendations_applied=data["recommendations_applied"],
            recommendations_count=data["recommendations_count"],
            safety_score=data["safety_score"],
            keyword_preservation=data["keyword_preservation"],
            structure_preservation=data["structure_preservation"],
            applied_by=data["applied_by"],
            applied_at=datetime.fromisoformat(data["applied_at"]),
            model_used=data["model_used"],
            processing_time_ms=data["processing_time_ms"],
            rollback_available=data["rollback_available"],
            rolled_back=data.get("rolled_back", False),
            rolled_back_at=datetime.fromisoformat(data["rolled_back_at"]) if data.get("rolled_back_at") else None,
            rolled_back_by=data.get("rolled_back_by")
        )

    def list_enhancements(
        self,
        file_path: Optional[str] = None,
        limit: int = 50
    ) -> List[EnhancementRecord]:
        """List enhancement records with optional filtering."""
        records = []

        for record_file in self._storage_dir.glob("*.json"):
            if record_file.name.startswith("rb_"):
                continue  # Skip rollback metadata

            try:
                with open(record_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Filter by file_path if specified
                if file_path and data["file_path"] != file_path:
                    continue

                record = EnhancementRecord(
                    enhancement_id=data["enhancement_id"],
                    validation_id=data["validation_id"],
                    file_path=data["file_path"],
                    original_content="",
                    enhanced_content="",
                    original_hash=data["original_hash"],
                    enhanced_hash=data["enhanced_hash"],
                    recommendations_applied=data["recommendations_applied"],
                    recommendations_count=data["recommendations_count"],
                    safety_score=data["safety_score"],
                    keyword_preservation=data["keyword_preservation"],
                    structure_preservation=data["structure_preservation"],
                    applied_by=data["applied_by"],
                    applied_at=datetime.fromisoformat(data["applied_at"]),
                    model_used=data["model_used"],
                    processing_time_ms=data["processing_time_ms"],
                    rollback_available=data["rollback_available"],
                    rolled_back=data.get("rolled_back", False),
                    rolled_back_at=datetime.fromisoformat(data["rolled_back_at"]) if data.get("rolled_back_at") else None,
                    rolled_back_by=data.get("rolled_back_by")
                )

                records.append(record)

            except Exception as e:
                logger.warning(f"Failed to load record {record_file}: {e}")

        # Sort by applied_at (newest first)
        records.sort(key=lambda r: r.applied_at, reverse=True)

        return records[:limit]

    def cleanup_expired_rollbacks(self) -> int:
        """Remove expired rollback points."""
        now = datetime.now(timezone.utc)
        count = 0

        for meta_file in self._rollback_dir.glob("rb_*.json"):
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    meta = json.load(f)

                expires_at = datetime.fromisoformat(meta["expires_at"])
                if now > expires_at:
                    # Delete rollback files
                    rollback_id = meta["rollback_id"]
                    content_file = self._rollback_dir / f"{rollback_id}.txt"

                    if content_file.exists():
                        content_file.unlink()
                    meta_file.unlink()

                    count += 1
                    logger.debug(f"Deleted expired rollback {rollback_id}")

            except Exception as e:
                logger.warning(f"Failed to cleanup {meta_file}: {e}")

        if count > 0:
            logger.info(f"Cleaned up {count} expired rollback points")

        return count


# Global instance
_history_manager: Optional[EnhancementHistory] = None


def get_history_manager(storage_dir: Optional[Path] = None) -> EnhancementHistory:
    """Get or create global history manager."""
    global _history_manager
    if _history_manager is None:
        _history_manager = EnhancementHistory(storage_dir)
    return _history_manager
