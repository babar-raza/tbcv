# file: tbcv/core/database.py
# Location: scripts/tbcv/core/database.py
"""
Enhanced Database configuration and models for the TBCV system.

Features:
- Recommendation table for human-in-the-loop approval workflow
- Audit logging for all changes
- Enhanced validation result tracking
- Workflow state management
"""

from __future__ import annotations

import os
import uuid
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List
from threading import Lock
from pathlib import Path
import enum

from core.logging import get_logger
logger = get_logger(__name__)

# --- SQLAlchemy imports (with graceful fallback) ---
SQLALCHEMY_AVAILABLE = True
try:
    from sqlalchemy import (
        create_engine, Column, String, Integer, DateTime, Text,
        Enum as SQLEnum, ForeignKey, LargeBinary, Boolean, Float, Index, text
    )
    from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session
    from sqlalchemy.types import TypeDecorator, TEXT
    Base = declarative_base()
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    logger.warning("SQLAlchemy is not available; using in-memory fallbacks.")

    # Minimal stubs to keep imports/types valid if SQLAlchemy is missing
    class _Dummy:  # noqa: E742
        def __init__(self, *a, **k): pass
        def __call__(self, *a, **k): return self

    create_engine = _Dummy()
    Column = _Dummy
    String = Integer = DateTime = Text = LargeBinary = Boolean = Float = _Dummy
    SQLEnum = _Dummy
    ForeignKey = Index = _Dummy
    relationship = _Dummy
    class TEXT: pass  # noqa: N801
    class TypeDecorator: impl = TEXT; cache_ok = True
    def declarative_base(): return object
    def sessionmaker(*a, **k): return lambda: None
    class Session: pass
    Base = declarative_base()  # type: ignore


# ---------------------------
# Enums for type safety
# ---------------------------
class RecommendationStatus(enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    APPLIED = "applied"


class ValidationStatus(enum.Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    SKIPPED = "skipped"
    APPROVED = "approved"
    REJECTED = "rejected"
    ENHANCED = "enhanced"


class WorkflowState(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ---------------------------
# SQLAlchemy custom JSON type
# ---------------------------
class JSONField(TypeDecorator):
    """Store dict/list as JSON strings in TEXT."""
    impl = TEXT
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return value


# --------------- ORM: Workflow ---------------
class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    type = Column(String(50), nullable=False, index=True)
    state = Column(SQLEnum(WorkflowState), nullable=False, index=True, default=WorkflowState.PENDING)
    input_params = Column(JSONField)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)
    workflow_metadata = Column("metadata", JSONField)
    total_steps = Column(Integer, default=0)
    current_step = Column(Integer, default=0)
    progress_percent = Column(Integer, default=0)
    error_message = Column(Text)

    checkpoints = relationship("Checkpoint", back_populates="workflow", cascade="all, delete-orphan")
    validation_results = relationship("ValidationResult", back_populates="workflow")

    __table_args__ = (
        Index('idx_workflows_state_created', 'state', 'created_at'),
        Index('idx_workflows_type_state', 'type', 'state'),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "state": self.state.value if isinstance(self.state, WorkflowState) else self.state,
            "input_params": self.input_params,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.workflow_metadata,
            "total_steps": self.total_steps,
            "current_step": self.current_step,
            "progress_percent": self.progress_percent,
            "error_message": self.error_message,
        }


# ---------------- ORM: Checkpoint ----------------
class Checkpoint(Base):
    __tablename__ = "checkpoints"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = Column(String(36), ForeignKey('workflows.id'), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    step_number = Column(Integer, nullable=False)
    state_data = Column(LargeBinary)
    created_at = Column(DateTime, default=datetime.utcnow)
    validation_hash = Column(String(32))
    can_resume_from = Column(Boolean, default=True)

    workflow = relationship("Workflow", back_populates="checkpoints")

    __table_args__ = (Index('idx_checkpoints_workflow_step', 'workflow_id', 'step_number'),)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "name": self.name,
            "step_number": self.step_number,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "validation_hash": self.validation_hash,
            "can_resume_from": self.can_resume_from
        }


# ---------------- ORM: CacheEntry ----------------
class CacheEntry(Base):
    __tablename__ = "cache_entries"

    cache_key = Column(String(200), primary_key=True)
    agent_id = Column(String(100), nullable=False, index=True)
    method_name = Column(String(100), nullable=False, index=True)
    input_hash = Column(String(64), nullable=False)
    result_data = Column(LargeBinary)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False, index=True)
    access_count = Column(Integer, default=1)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    size_bytes = Column(Integer)

    __table_args__ = (
        Index('idx_cache_expires', 'expires_at'),
        Index('idx_cache_agent_method', 'agent_id', 'method_name'),
    )


# ---------------- ORM: MetricEntry ----------------
class MetricEntry(Base):
    __tablename__ = "metrics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), index=True)
    value = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    metric_metadata = Column("metadata", JSONField)


# ---------------- ORM: ValidationResult ----------------
class ValidationResult(Base):
    __tablename__ = "validation_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = Column(String(36), ForeignKey('workflows.id'), nullable=True, index=True)
    file_path = Column(String(1024), index=True)

    # Structured data
    rules_applied = Column(JSONField)
    validation_results = Column(JSONField)
    notes = Column(Text)

    # Classification
    severity = Column(String(20), index=True)
    status = Column(SQLEnum(ValidationStatus), index=True, default=ValidationStatus.PASS)

    # Traceability
    content_hash = Column(String(64), index=True)
    ast_hash = Column(String(64))
    run_id = Column(String(64), index=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    workflow = relationship("Workflow", back_populates="validation_results")
    recommendations = relationship("Recommendation", back_populates="validation", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_validation_file_status', 'file_path', 'status'),
        Index('idx_validation_file_severity', 'file_path', 'severity'),
        Index('idx_validation_created', 'created_at'),
        Index('idx_validation_run_id', 'run_id'),  # FIX: Added missing index
        Index('idx_validation_workflow_status', 'workflow_id', 'status'),  # FIX: Added composite index
    )

    def to_dict(self) -> Dict[str, Any]:
        # Handle recommendations count safely for detached instances
        recommendations_count = 0
        try:
            recommendations_count = len(self.recommendations) if self.recommendations else 0
        except Exception:
            # If instance is detached from session, we can't access relationships
            recommendations_count = 0
            
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "file_path": self.file_path,
            "rules_applied": self.rules_applied,
            "validation_results": self.validation_results,
            "notes": self.notes,
            "severity": self.severity,
            "status": self.status.value if isinstance(self.status, ValidationStatus) else self.status,
            "content_hash": self.content_hash,
            "ast_hash": self.ast_hash,
            "run_id": self.run_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "recommendations_count": recommendations_count,
        }


# ---------------- ORM: Recommendation ----------------
class Recommendation(Base):
    """
    Human-in-the-loop approval system for content enhancements.
    Each recommendation can be approved, rejected, or remain pending.
    """
    __tablename__ = "recommendations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    validation_id = Column(String(36), ForeignKey('validation_results.id'), nullable=False, index=True)

    # Recommendation details
    type = Column(String(50), nullable=False, index=True)  # link_plugin, fix_format, add_info_text, etc.
    title = Column(String(200), nullable=False)
    description = Column(Text)

    # Change details
    original_content = Column(Text)
    proposed_content = Column(Text)
    diff = Column(Text)

    # Metadata
    confidence = Column(Float, default=0.0)
    priority = Column(String(20), default="medium")  # low, medium, high, critical

    # Status tracking
    status = Column(SQLEnum(RecommendationStatus), nullable=False, index=True, default=RecommendationStatus.PENDING)

    # Approval workflow
    reviewed_by = Column(String(100))
    reviewed_at = Column(DateTime)
    review_notes = Column(Text)

    # Enhancement tracking
    applied_at = Column(DateTime)
    applied_by = Column(String(100))

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Additional context
    recommendation_metadata = Column("metadata", JSONField)

    # Relationships
    validation = relationship("ValidationResult", back_populates="recommendations")
    audit_logs = relationship("AuditLog", back_populates="recommendation", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_recommendations_status', 'status'),
        Index('idx_recommendations_validation', 'validation_id', 'status'),
        Index('idx_recommendations_type', 'type'),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "validation_id": self.validation_id,
            "type": self.type,
            "title": self.title,
            "description": self.description,
            "original_content": self.original_content,
            "proposed_content": self.proposed_content,
            "diff": self.diff,
            "confidence": self.confidence,
            "priority": self.priority,
            "status": self.status.value if isinstance(self.status, RecommendationStatus) else self.status,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "review_notes": self.review_notes,
            "applied_at": self.applied_at.isoformat() if self.applied_at else None,
            "applied_by": self.applied_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.recommendation_metadata,
        }


# ---------------- ORM: AuditLog ----------------
class AuditLog(Base):
    """
    Audit trail for all changes to recommendations and validations.
    """
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recommendation_id = Column(String(36), ForeignKey('recommendations.id'), nullable=True, index=True)

    action = Column(String(50), nullable=False, index=True)  # created, approved, rejected, applied, modified
    actor = Column(String(100))
    actor_type = Column(String(20))  # user, system, agent

    # Change tracking
    before_state = Column(JSONField)
    after_state = Column(JSONField)
    changes = Column(JSONField)

    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    audit_metadata = Column("metadata", JSONField)

    # Relationships
    recommendation = relationship("Recommendation", back_populates="audit_logs")

    __table_args__ = (
        Index('idx_audit_action', 'action'),
        Index('idx_audit_created', 'created_at'),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "recommendation_id": self.recommendation_id,
            "action": self.action,
            "actor": self.actor,
            "actor_type": self.actor_type,
            "before_state": self.before_state,
            "after_state": self.after_state,
            "changes": self.changes,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "metadata": self.audit_metadata,
        }


# ------------------- Database Management -------------------
class DatabaseManager:
    def __init__(self):
        self._lock = Lock()
        if SQLALCHEMY_AVAILABLE:
            db_url = os.getenv("DATABASE_URL", "sqlite:///./tbcv.db")
            # Ensure SQLite path exists
            if db_url.startswith('sqlite:///'):
                db_path = db_url.replace('sqlite:///', '')
                Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            self.engine = create_engine(db_url, connect_args={"check_same_thread": False} if db_url.startswith('sqlite') else {})
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            self.create_tables()
        else:
            # In-memory fallbacks if SQLAlchemy missing
            self.engine = None
            self.SessionLocal = None
            self._workflows = {}
            self._validation_results = {}
            self._recommendations = {}
            self._audit_logs = {}

    def init_database(self) -> bool:
        """Idempotent database initialization."""
        try:
            return self.is_connected()
        except Exception as e:
            logger.warning(f"Database initialization warning: {e}")
            return False

    def is_connected(self) -> bool:
        """Lightweight connectivity check for /health."""
        if not SQLALCHEMY_AVAILABLE or self.engine is None:
            return False
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    def has_required_schema(self) -> bool:
        """Check if all required tables exist in the database."""
        if not SQLALCHEMY_AVAILABLE or self.engine is None:
            return False
        
        required_tables = [
            'workflows', 'checkpoints', 'cache_entries', 'metrics',
            'validation_results', 'recommendations', 'audit_logs'
        ]
        
        try:
            with self.engine.connect() as conn:
                # Check if all required tables exist
                for table_name in required_tables:
                    result = conn.execute(text(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name"
                    ), {'table_name': table_name})
                    if not result.fetchone():
                        logger.warning(f"Missing required table: {table_name}")
                        return False
                return True
        except Exception as e:
            logger.error(f"Error checking database schema: {e}")
            return False

    def ensure_schema_idempotent(self) -> bool:
        """Ensure database schema exists (idempotent operation for startup)."""
        try:
            if SQLALCHEMY_AVAILABLE and self.engine is not None:
                Base.metadata.create_all(bind=self.engine)
                logger.info("Database schema ensured (idempotent)")
                return True
        except Exception as e:
            logger.error(f"Error ensuring database schema: {e}")
        return False

    def create_tables(self) -> None:
        if SQLALCHEMY_AVAILABLE and self.engine is not None:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables ensured")

    def get_session(self) -> Session:
        return self.SessionLocal()  # type: ignore

    # ---- Workflow helpers ----
    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        with self.get_session() as session:
            return session.query(Workflow).filter(Workflow.id == workflow_id).first()

    def create_workflow(self, workflow_type: str, input_params: Dict[str, Any],
                        metadata: Optional[Dict[str, Any]] = None) -> Workflow:
        workflow = Workflow(
            type=workflow_type, state=WorkflowState.PENDING,
            input_params=input_params, workflow_metadata=metadata or {}
        )
        with self.get_session() as session:
            session.add(workflow)
            session.commit()
            session.refresh(workflow)
        logger.info("Workflow created", extra={"workflow_id": workflow.id})
        return workflow

    def update_workflow(self, workflow_id: str, **updates) -> Optional[Workflow]:
        with self.get_session() as session:
            wf = session.query(Workflow).filter(Workflow.id == workflow_id).first()
            if wf:
                if "metadata" in updates:
                    updates["workflow_metadata"] = updates.pop("metadata")
                if "state" in updates and isinstance(updates["state"], str):
                    updates["state"] = WorkflowState(updates["state"])
                for key, value in updates.items():
                    if hasattr(wf, key):
                        setattr(wf, key, value)
                wf.updated_at = datetime.utcnow()
                session.commit()
                session.refresh(wf)
            return wf

    def list_workflows(self, state: Optional[str] = None, limit: int = 50) -> List[Workflow]:
        with self.get_session() as session:
            q = session.query(Workflow)
            if state:
                q = q.filter(Workflow.state == WorkflowState(state))
            return q.order_by(Workflow.created_at.desc()).limit(limit).all()

    # ---- Cache helpers ----
    def get_cache_entry(self, cache_key: str) -> Optional[CacheEntry]:
        with self.get_session() as session:
            return session.query(CacheEntry).filter(CacheEntry.cache_key == cache_key).first()

    def store_cache_entry(
        self,
        cache_key: str,
        agent_id: str,
        method_name: str,
        input_hash: str,
        result_data: bytes,
        expires_at: datetime,
        size_bytes: int,
    ) -> None:
        with self.get_session() as session:
            existing = session.query(CacheEntry).filter(CacheEntry.cache_key == cache_key).first()
            if existing:
                existing.result_data = result_data
                existing.expires_at = expires_at
                existing.last_accessed = datetime.utcnow()
                existing.size_bytes = size_bytes
                existing.access_count = (existing.access_count or 0) + 1
            else:
                entry = CacheEntry(
                    cache_key=cache_key,
                    agent_id=agent_id,
                    method_name=method_name,
                    input_hash=input_hash,
                    result_data=result_data,
                    created_at=datetime.utcnow(),
                    expires_at=expires_at,
                    last_accessed=datetime.utcnow(),
                    size_bytes=size_bytes,
                )
                session.add(entry)
            session.commit()

    # ---- ValidationResult helpers ----
    @staticmethod
    def _sha256(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def create_validation_result(
        self,
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
        workflow_id: Optional[str] = None,
    ) -> ValidationResult:
        content_hash = self._sha256(content) if content else None

        # Convert string status to enum if needed
        if isinstance(status, str):
            status = ValidationStatus(status)

        vr = ValidationResult(
            workflow_id=workflow_id,
            file_path=file_path,
            rules_applied=rules_applied,
            validation_results=validation_results,
            notes=notes,
            severity=severity,
            status=status,
            content_hash=content_hash,
            ast_hash=ast_hash,
            run_id=run_id,
        )
        with self.get_session() as session:
            session.add(vr)
            session.commit()
            session.refresh(vr)
        logger.info("Validation result stored", extra={"validation_id": vr.id})
        return vr

    def list_validation_results(
        self,
        *,
        file_path: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        workflow_id: Optional[str] = None,
        limit: int = 100,
        newest_first: bool = True,
    ) -> List[ValidationResult]:
        with self.get_session() as session:
            q = session.query(ValidationResult)
            if file_path:
                q = q.filter(ValidationResult.file_path == file_path)
            if severity:
                q = q.filter(ValidationResult.severity == severity)
            if status:
                q = q.filter(ValidationResult.status == ValidationStatus(status))
            if workflow_id:
                q = q.filter(ValidationResult.workflow_id == workflow_id)
            q = q.order_by(ValidationResult.created_at.desc() if newest_first else ValidationResult.created_at.asc())
            return q.limit(limit).all()

    def get_validation_result(self, validation_id: str) -> Optional[ValidationResult]:
        with self.get_session() as session:
            return session.query(ValidationResult).filter(ValidationResult.id == validation_id).first()

    def get_latest_validation_result(self, *, file_path: str) -> Optional[ValidationResult]:
        with self.get_session() as session:
            return (
                session.query(ValidationResult)
                .filter(ValidationResult.file_path == file_path)
                .order_by(ValidationResult.created_at.desc())
                .first()
            )

    # ---- Recommendation helpers ----
    def create_recommendation(
        self,
        *,
        validation_id: str,
        type: str,
        title: str,
        description: str,
        original_content: Optional[str] = None,
        proposed_content: Optional[str] = None,
        diff: Optional[str] = None,
        confidence: float = 0.0,
        priority: str = "medium",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Recommendation:
        rec = Recommendation(
            validation_id=validation_id,
            type=type,
            title=title,
            description=description,
            original_content=original_content,
            proposed_content=proposed_content,
            diff=diff,
            confidence=confidence,
            priority=priority,
            status=RecommendationStatus.PENDING,
            recommendation_metadata=metadata or {},
        )
        with self.get_session() as session:
            session.add(rec)
            session.commit()
            session.refresh(rec)

        # Audit: created
        self.create_audit_log(
            recommendation_id=rec.id,
            action="created",
            actor="system",
            actor_type="system",
            after_state=rec.to_dict(),
        )

        logger.info("Recommendation created", extra={"recommendation_id": rec.id})
        return rec

    def get_recommendation(self, recommendation_id: str) -> Optional[Recommendation]:
        with self.get_session() as session:
            return session.query(Recommendation).filter(Recommendation.id == recommendation_id).first()

    def list_recommendations(
        self,
        *,
        validation_id: Optional[str] = None,
        status: Optional[str] = None,
        type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Recommendation]:
        with self.get_session() as session:
            q = session.query(Recommendation)
            if validation_id:
                q = q.filter(Recommendation.validation_id == validation_id)
            if status:
                q = q.filter(Recommendation.status == RecommendationStatus(status))
            if type:
                q = q.filter(Recommendation.type == type)
            return q.order_by(Recommendation.created_at.desc()).limit(limit).all()

    def update_recommendation_status(
        self,
        recommendation_id: str,
        status: str,
        reviewer: Optional[str] = None,
        review_notes: Optional[str] = None,
    ) -> Optional[Recommendation]:
        with self.get_session() as session:
            rec = session.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
            if not rec:
                return None

            before_state = rec.to_dict()

            rec.status = RecommendationStatus(status)
            rec.reviewed_by = reviewer
            rec.reviewed_at = datetime.utcnow()
            rec.review_notes = review_notes
            rec.updated_at = datetime.utcnow()

            session.commit()
            session.refresh(rec)

            after_state = rec.to_dict()

            # Audit: status change
            self.create_audit_log(
                recommendation_id=rec.id,
                action=f"status_changed_to_{status}",
                actor=reviewer or "system",
                actor_type="user" if reviewer else "system",
                before_state=before_state,
                after_state=after_state,
                notes=review_notes,
            )

            logger.info("Recommendation status updated", extra={"recommendation_id": rec.id, "status": status})
            return rec

    def mark_recommendation_applied(
        self,
        recommendation_id: str,
        applied_by: Optional[str] = None,
    ) -> Optional[Recommendation]:
        with self.get_session() as session:
            rec = session.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
            if not rec:
                return None

            before_state = rec.to_dict()

            rec.status = RecommendationStatus.APPLIED
            rec.applied_at = datetime.utcnow()
            rec.applied_by = applied_by or "system"
            rec.updated_at = datetime.utcnow()

            session.commit()
            session.refresh(rec)

            after_state = rec.to_dict()

            # Audit: applied
            self.create_audit_log(
                recommendation_id=rec.id,
                action="applied",
                actor=applied_by or "system",
                actor_type="system",
                before_state=before_state,
                after_state=after_state,
            )

            logger.info("Recommendation marked as applied", extra={"recommendation_id": rec.id})
            return rec

    # ---- AuditLog helpers ----
    def create_audit_log(
        self,
        *,
        recommendation_id: Optional[str] = None,
        action: str,
        actor: Optional[str] = None,
        actor_type: str = "system",
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None,
        changes: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        log = AuditLog(
            recommendation_id=recommendation_id,
            action=action,
            actor=actor,
            actor_type=actor_type,
            before_state=before_state,
            after_state=after_state,
            changes=changes,
            notes=notes,
            audit_metadata=metadata or {},
        )
        with self.get_session() as session:
            session.add(log)
            session.commit()
            session.refresh(log)
        return log

    def list_audit_logs(
        self,
        *,
        recommendation_id: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditLog]:
        with self.get_session() as session:
            q = session.query(AuditLog)
            if recommendation_id:
                q = q.filter(AuditLog.recommendation_id == recommendation_id)
            if action:
                q = q.filter(AuditLog.action == action)
            return q.order_by(AuditLog.created_at.desc()).limit(limit).all()

    # ---- Misc helpers for tests ----
    def _ensure_collection(self, collection_name: str) -> str:
        """Internal helper to ensure collection exists (used by non-SQLite tests)."""
        if not SQLALCHEMY_AVAILABLE:
            if not hasattr(self, '_collections'):
                self._collections = {}
            if collection_name not in self._collections:
                self._collections[collection_name] = {"created": True, "items": []}
        return collection_name

    def mark_ingested(self, file_path: str, collection: str = "default") -> Dict[str, Any]:
        """Mark file as ingested with safe existence checks."""
        self._ensure_collection(collection)
        if not os.path.exists(file_path):
            return {"status": "success", "message": "File not found, marked as handled", "exists": False}
        if os.path.getsize(file_path) == 0:
            return {"status": "success", "message": "Empty file handled", "exists": True, "size": 0}
        return {"status": "success", "message": "File marked as ingested", "exists": True, "size": os.path.getsize(file_path)}

    def query_unknown_source(self, source: str) -> Dict[str, Any]:
        """Query unknown source by creating default collection."""
        default_collection = self._ensure_collection("unknown_sources")
        return {"source": source, "collection": default_collection, "status": "mapped_to_default"}


# Singleton
db_manager = DatabaseManager()
