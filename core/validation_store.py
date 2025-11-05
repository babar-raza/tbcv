# Location: scripts/tbcv/core/validation_store.py
"""
Validation results persistence for TBCV (canonical).

Why this file:
- Keep validation persistence isolated from your large core/database.py.
- Define a single, canonical table name: 'validation_records'.
- Provide small helper functions the agents and API can call.

Important:
- Use ONLY absolute 'tbcv.core.*' imports to avoid loading the same module twice
  under different names (which can re-declare tables in the same MetaData).
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
import hashlib

from core.database import Base, db_manager, JSONField, Column, String, DateTime, Text, Index, Session


class ValidationRecord(Base):
    __tablename__ = "validation_records"  # single canonical table name

    id = Column(String(36), primary_key=True)
    file_path = Column(String(1024), nullable=False, index=True)
    family = Column(String(100), nullable=True, index=True)  # detected document family

    # Structured payload
    rules_applied = Column(JSONField)        # list[str] or dict
    validation_results = Column(JSONField)   # list[dict] (per-rule outcomes)
    notes = Column(Text)                     # freeform notes/suggestions

    # Classification
    severity = Column(String(20), index=True)  # critical|high|medium|low|info
    status = Column(String(20), index=True)    # pass|fail|skipped|warning

    # Traceability
    content_hash = Column(String(64), index=True, nullable=True)
    ast_hash = Column(String(64), nullable=True)
    run_id = Column(String(64), index=True, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_val_file_status', 'file_path', 'status'),
        Index('idx_val_file_sev', 'file_path', 'severity'),
        Index('idx_val_created', 'created_at'),
        {'extend_existing': True}
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "file_path": self.file_path,
            "family": self.family,
            "rules_applied": self.rules_applied,
            "validation_results": self.validation_results,
            "notes": self.notes,
            "severity": self.severity,
            "status": self.status,
            "content_hash": self.content_hash,
            "ast_hash": self.ast_hash,
            "run_id": self.run_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def create_validation_record(
    *,
    file_path: str,
    rules_applied: Any,
    validation_results: Any,
    notes: str,
    severity: str,
    status: str,
    content: Optional[str] = None,
    ast_hash: Optional[str] = None,
    run_id: Optional[str] = None,
    family: Optional[str] = None,
) -> ValidationRecord:
    row = ValidationRecord(
        id=str(uuid.uuid4()),
        file_path=file_path,
        family=family,
        rules_applied=rules_applied,
        validation_results=validation_results,
        notes=notes,
        severity=severity,
        status=status,
        content_hash=_sha256(content) if content else None,
        ast_hash=ast_hash,
        run_id=run_id,
    )
    with db_manager.get_session() as session:  # type: Session
        session.add(row)
        session.commit()
        session.refresh(row)
    return row


def list_validation_records(
    *,
    file_path: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    newest_first: bool = True,
) -> List[ValidationRecord]:
    with db_manager.get_session() as session:  # type: Session
        q = session.query(ValidationRecord)
        if file_path:
            q = q.filter(ValidationRecord.file_path == file_path)
        if severity:
            q = q.filter(ValidationRecord.severity == severity)
        if status:
            q = q.filter(ValidationRecord.status == status)
        if newest_first:
            q = q.order_by(ValidationRecord.created_at.desc())
        return q.limit(limit).all()


def latest_validation_record(*, file_path: str) -> Optional[ValidationRecord]:
    with db_manager.get_session() as session:  # type: Session
        return (
            session.query(ValidationRecord)
            .filter(ValidationRecord.file_path == file_path)
            .order_by(ValidationRecord.created_at.desc())
            .first()
        )

# --- Ensure table exists even if DB was initialized before this module imported ---
try:
    # Safe to call multiple times; will only create missing tables.
    Base.metadata.create_all(bind=db_manager.engine)
except Exception:
    # Do not crash module import on environments where engine isn’t ready yet.
    pass


def list_validation_results(
    *,
    file_path: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    newest_first: bool = True,
):
    """
    Back-compat alias expected by API server.
    Delegates to list_validation_records(...) to avoid ripple changes.
    """
    return list_validation_records(
        file_path=file_path,
        severity=severity,
        status=status,
        limit=limit,
        newest_first=newest_first,
    )


__all__ = [
    "ValidationRecord",
    "create_validation_record",
    "list_validation_records",
    "list_validation_results",
    "latest_validation_record",
]
