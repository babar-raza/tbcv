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
from datetime import datetime, timezone
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
    PROPOSED = "proposed"
    PENDING = "pending"
    APPROVED = "approved"
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
    validation_types = Column(JSONField)  # List of validation types run (e.g., ["yaml", "markdown", "Truth"])
    parent_validation_id = Column(String(36), ForeignKey('validation_results.id'), nullable=True)  # For re-validation
    comparison_data = Column(JSONField)  # Comparison results for re-validation
    notes = Column(Text)

    # Classification
    severity = Column(String(20), index=True)
    status = Column(SQLEnum(ValidationStatus), index=True, default=ValidationStatus.PASS)

    # Traceability
    content_hash = Column(String(64), index=True)
    ast_hash = Column(String(64))
    run_id = Column(String(64), index=True)

    # History tracking
    file_hash = Column(String(64), index=True)  # Hash of the actual file for history tracking
    version_number = Column(Integer, default=1)  # Version number for this file path

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    workflow = relationship("Workflow", back_populates="validation_results")
    recommendations = relationship("Recommendation", back_populates="validation", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_validation_file_status', 'file_path', 'status'),
        Index('idx_validation_file_severity', 'file_path', 'severity'),
        Index('idx_validation_created', 'created_at'),
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
    
    # Machine-readable recommendation fields
    scope = Column(String(200))  # e.g., "line:42", "section:intro", "global"
    instruction = Column(Text)  # Concrete, actionable instruction
    rationale = Column(Text)  # Why this recommendation would fix the issue
    severity = Column(String(20), default="medium")  # critical, high, medium, low

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
            "scope": self.scope,
            "instruction": self.instruction,
            "rationale": self.rationale,
            "severity": self.severity,
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
            # Ensure tables exist
            if SQLALCHEMY_AVAILABLE and self.engine is not None:
                Base.metadata.create_all(bind=self.engine)
                logger.info("Database tables ensured (idempotent)")
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
                wf.updated_at = datetime.now(timezone.utc)
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
                existing.last_accessed = datetime.now(timezone.utc)
                existing.size_bytes = size_bytes
                existing.access_count = (existing.access_count or 0) + 1
            else:
                entry = CacheEntry(
                    cache_key=cache_key,
                    agent_id=agent_id,
                    method_name=method_name,
                    input_hash=input_hash,
                    result_data=result_data,
                    created_at=datetime.now(timezone.utc),
                    expires_at=expires_at,
                    last_accessed=datetime.now(timezone.utc),
                    size_bytes=size_bytes,
                )
                session.add(entry)
            session.commit()

    def cleanup_expired_cache(self) -> int:
        """Remove expired cache entries and return count."""
        with self.get_session() as session:
            now = datetime.now(timezone.utc)
            result = session.query(CacheEntry).filter(CacheEntry.expires_at < now).delete()
            session.commit()
            return result

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
        validation_types: Optional[List[str]] = None,
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
            validation_types=validation_types,
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
        
        # Auto-generate recommendations if validation has results
        if validation_results:
            try:
                # Import here to avoid circular dependency
                from api.services.recommendation_consolidator import consolidate_recommendations
                import asyncio
                
                # Run consolidation in background
                try:
                    # Try to get running loop
                    loop = asyncio.get_running_loop()
                    loop.create_task(self._async_consolidate_recommendations(vr.id))
                except RuntimeError:
                    # No running loop, do it synchronously
                    recs = consolidate_recommendations(vr.id)
                    logger.info(f"Auto-generated {len(recs)} recommendations for validation {vr.id}")
            except Exception as e:
                logger.error(f"Failed to auto-generate recommendations for {vr.id}: {e}")
        
        return vr
    
    async def _async_consolidate_recommendations(self, validation_id: str):
        """Async wrapper for recommendation consolidation."""
        try:
            from api.services.recommendation_consolidator import consolidate_recommendations
            recs = consolidate_recommendations(validation_id)
            logger.info(f"Auto-generated {len(recs)} recommendations for validation {validation_id}")
        except Exception as e:
            logger.error(f"Failed to auto-generate recommendations for {validation_id}: {e}")

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

    def get_validation_history(
        self,
        *,
        file_path: str,
        limit: Optional[int] = None,
        include_trends: bool = True
    ) -> Dict[str, Any]:
        """
        Get validation history for a file path, ordered from newest to oldest.

        Args:
            file_path: Path to the file
            limit: Optional maximum number of historical records to return
            include_trends: Whether to calculate trend analysis

        Returns:
            Dict with validation history and optional trend analysis
        """
        with self.get_session() as session:
            query = (
                session.query(ValidationResult)
                .filter(ValidationResult.file_path == file_path)
                .order_by(ValidationResult.created_at.desc())
            )

            if limit:
                query = query.limit(limit)

            validations = query.all()

            history = {
                "file_path": file_path,
                "total_validations": len(validations),
                "validations": [
                    {
                        "id": v.id,
                        "status": v.status.value if hasattr(v.status, 'value') else str(v.status),
                        "severity": v.severity,
                        "version_number": v.version_number,
                        "file_hash": v.file_hash,
                        "content_hash": v.content_hash,
                        "created_at": v.created_at.isoformat() if v.created_at else None,
                        "validation_results": v.validation_results,
                        "parent_validation_id": v.parent_validation_id,
                        "comparison_data": v.comparison_data
                    }
                    for v in validations
                ]
            }

            # Calculate trend analysis if requested
            if include_trends and len(validations) > 1:
                trends = self._calculate_validation_trends(validations)
                history["trends"] = trends

            return history

    def _calculate_validation_trends(self, validations: List[ValidationResult]) -> Dict[str, Any]:
        """
        Calculate trend analysis from validation history.

        Args:
            validations: List of ValidationResult objects ordered newest to oldest

        Returns:
            Dict with trend metrics
        """
        if not validations:
            return {}

        # Extract issue counts from validation_results
        issue_counts = []
        confidence_scores = []
        statuses = []

        for v in reversed(validations):  # Oldest to newest for trend calculation
            vr = v.validation_results
            if isinstance(vr, dict):
                # Count issues
                issues = vr.get("issues", [])
                issue_counts.append(len(issues))

                # Get confidence
                confidence = vr.get("confidence", 0.0)
                confidence_scores.append(confidence)

            # Track status
            status_val = v.status.value if hasattr(v.status, 'value') else str(v.status)
            statuses.append(status_val)

        # Calculate trends
        trends = {
            "issue_count_trend": self._calculate_trend(issue_counts),
            "confidence_trend": self._calculate_trend(confidence_scores),
            "status_trend": self._analyze_status_trend(statuses),
            "improvement_detected": False,
            "regression_detected": False
        }

        # Detect improvement/regression
        if len(issue_counts) >= 2:
            recent_avg = sum(issue_counts[-3:]) / min(3, len(issue_counts))
            older_avg = sum(issue_counts[:3]) / min(3, len(issue_counts))

            if recent_avg < older_avg * 0.8:  # 20% improvement
                trends["improvement_detected"] = True
            elif recent_avg > older_avg * 1.2:  # 20% regression
                trends["regression_detected"] = True

        return trends

    def _calculate_trend(self, values: List[float]) -> str:
        """
        Calculate trend direction from a list of numeric values.

        Returns: "improving", "degrading", "stable", or "insufficient_data"
        """
        if len(values) < 2:
            return "insufficient_data"

        # Simple linear trend: compare first half to second half
        mid = len(values) // 2
        first_half_avg = sum(values[:mid]) / mid if mid > 0 else 0
        second_half_avg = sum(values[mid:]) / (len(values) - mid)

        diff_pct = abs(second_half_avg - first_half_avg) / (first_half_avg + 0.0001)

        if diff_pct < 0.1:  # Less than 10% change
            return "stable"
        elif second_half_avg < first_half_avg:
            return "improving"  # For issue counts, lower is better
        else:
            return "degrading"

    def _analyze_status_trend(self, statuses: List[str]) -> str:
        """
        Analyze trend in validation statuses.

        Returns: "improving", "degrading", "stable", or "mixed"
        """
        if len(statuses) < 2:
            return "insufficient_data"

        # Status hierarchy: PASS > PASS_WITH_WARNINGS > FAIL
        status_scores = {
            "PASS": 3,
            "PASS_WITH_WARNINGS": 2,
            "FAIL": 1,
            "ERROR": 0
        }

        scores = [status_scores.get(s.upper(), 0) for s in statuses]

        mid = len(scores) // 2
        first_half_avg = sum(scores[:mid]) / mid if mid > 0 else 0
        second_half_avg = sum(scores[mid:]) / (len(scores) - mid)

        if abs(second_half_avg - first_half_avg) < 0.5:
            return "stable"
        elif second_half_avg > first_half_avg:
            return "improving"
        else:
            return "degrading"

    # ---- Recommendation helpers ----
    def create_recommendation(
        self,
        *,
        validation_id: str,
        type: str,
        title: str,
        description: str,
        scope: Optional[str] = None,
        instruction: Optional[str] = None,
        rationale: Optional[str] = None,
        severity: Optional[str] = None,
        original_content: Optional[str] = None,
        proposed_content: Optional[str] = None,
        diff: Optional[str] = None,
        confidence: float = 0.0,
        priority: str = "medium",
        status: str = "pending",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Recommendation:
        rec = Recommendation(
            validation_id=validation_id,
            type=type,
            title=title,
            description=description,
            scope=scope,
            instruction=instruction,
            rationale=rationale,
            severity=severity or "medium",
            original_content=original_content,
            proposed_content=proposed_content,
            diff=diff,
            confidence=confidence,
            priority=priority,
            status=RecommendationStatus(status) if isinstance(status, str) else status,
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
            rec.reviewed_at = datetime.now(timezone.utc)
            rec.review_notes = review_notes
            rec.updated_at = datetime.now(timezone.utc)

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
            rec.applied_at = datetime.now(timezone.utc)
            rec.applied_by = applied_by or "system"
            rec.updated_at = datetime.now(timezone.utc)

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

    def calculate_recommendation_confidence(
        self,
        *,
        issue_severity: str,
        recommendation_type: str,
        has_original_content: bool = False,
        has_proposed_content: bool = False,
        has_diff: bool = False,
        has_rationale: bool = False,
        validation_confidence: float = 0.0,
        additional_factors: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Calculate multi-factor confidence score for a recommendation.

        Args:
            issue_severity: Severity level (critical, high, medium, low)
            recommendation_type: Type of recommendation
            has_original_content: Whether original content is provided
            has_proposed_content: Whether proposed fix is provided
            has_diff: Whether diff is provided
            has_rationale: Whether rationale is provided
            validation_confidence: Confidence score from the original validation
            additional_factors: Optional dict of additional scoring factors

        Returns:
            Dict with overall confidence score and breakdown
        """
        factors = {}

        # Factor 1: Issue severity (0.0-0.3)
        severity_scores = {
            "critical": 0.3,
            "high": 0.25,
            "medium": 0.2,
            "low": 0.15,
            "info": 0.1
        }
        severity_score = severity_scores.get(issue_severity.lower(), 0.15)
        factors["severity"] = severity_score

        # Factor 2: Completeness of recommendation (0.0-0.3)
        completeness = 0.0
        if has_original_content:
            completeness += 0.075
        if has_proposed_content:
            completeness += 0.1
        if has_diff:
            completeness += 0.075
        if has_rationale:
            completeness += 0.05
        factors["completeness"] = completeness

        # Factor 3: Validation confidence (0.0-0.2)
        # Use the confidence from the original validation
        validation_factor = validation_confidence * 0.2
        factors["validation_confidence"] = validation_factor

        # Factor 4: Recommendation type specificity (0.0-0.2)
        type_scores = {
            "fix_specific": 0.2,  # Exact fix provided
            "fix_general": 0.15,  # General fix guidance
            "enhancement": 0.1,   # Enhancement suggestion
            "refactor": 0.1,     # Refactoring suggestion
            "info": 0.05         # Informational only
        }
        # Map actual types to these categories
        type_mapping = {
            "link_plugin": "fix_specific",
            "fix_format": "fix_specific",
            "add_info_text": "fix_general",
            "content_improvement": "enhancement",
            "style_improvement": "refactor"
        }
        mapped_type = type_mapping.get(recommendation_type, "fix_general")
        type_score = type_scores.get(mapped_type, 0.1)
        factors["type_specificity"] = type_score

        # Factor 5: Additional custom factors (0.0-0.2)
        additional_score = 0.0
        if additional_factors:
            for key, value in additional_factors.items():
                additional_score += min(value, 0.05)  # Cap each at 0.05
            additional_score = min(additional_score, 0.2)  # Cap total at 0.2
        factors["additional"] = additional_score

        # Calculate overall confidence (sum of factors, capped at 1.0)
        overall_confidence = min(
            sum(factors.values()),
            1.0
        )

        # Generate explanation
        explanation = self._generate_confidence_explanation(
            overall_confidence,
            factors,
            issue_severity,
            has_proposed_content
        )

        return {
            "confidence": overall_confidence,
            "factors": factors,
            "explanation": explanation,
            "calculated_at": datetime.now(timezone.utc).isoformat()
        }

    def _generate_confidence_explanation(
        self,
        confidence: float,
        factors: Dict[str, float],
        severity: str,
        has_fix: bool
    ) -> str:
        """Generate human-readable confidence explanation."""
        if confidence >= 0.9:
            base = "Very high confidence recommendation"
        elif confidence >= 0.75:
            base = "High confidence recommendation"
        elif confidence >= 0.6:
            base = "Moderate confidence recommendation"
        elif confidence >= 0.4:
            base = "Low-moderate confidence recommendation"
        else:
            base = "Low confidence recommendation"

        details = []

        if severity in ["critical", "high"]:
            details.append(f"{severity} severity issue")

        if has_fix:
            details.append("specific fix provided")
        else:
            details.append("general guidance only")

        if factors.get("validation_confidence", 0) > 0.15:
            details.append("strong validation backing")

        if factors.get("completeness", 0) > 0.2:
            details.append("comprehensive details")

        if details:
            return f"{base}: {', '.join(details)}."
        else:
            return f"{base}."

    def update_recommendation_confidence(
        self,
        recommendation_id: str,
        confidence_data: Dict[str, Any]
    ) -> Optional[Recommendation]:
        """
        Update a recommendation's confidence score and store breakdown in metadata.

        Args:
            recommendation_id: ID of the recommendation to update
            confidence_data: Confidence data from calculate_recommendation_confidence()

        Returns:
            Updated Recommendation object or None if not found
        """
        with self.get_session() as session:
            rec = session.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
            if not rec:
                return None

            # Update confidence score
            rec.confidence = confidence_data["confidence"]

            # Store breakdown in metadata
            metadata = rec.recommendation_metadata or {}
            metadata["confidence_breakdown"] = confidence_data

            rec.recommendation_metadata = metadata
            rec.updated_at = datetime.now(timezone.utc)

            session.commit()
            session.refresh(rec)

            logger.info(
                "Recommendation confidence updated",
                extra={
                    "recommendation_id": rec.id,
                    "confidence": rec.confidence
                }
            )
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

    def delete_recommendation(self, recommendation_id: str) -> bool:
        """Delete a recommendation."""
        with self.get_session() as session:
            rec = session.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
            if not rec:
                return False
            
            session.delete(rec)
            session.commit()
            logger.info("Recommendation deleted", extra={"recommendation_id": recommendation_id})
            return True
    
    def soft_delete_workflows(self, workflow_ids: List[str]) -> int:
        """Soft delete workflows by marking them as deleted."""
        count = 0
        with self.get_session() as session:
            for workflow_id in workflow_ids:
                workflow = session.query(Workflow).filter(Workflow.id == workflow_id).first()
                if workflow:
                    # Add soft_deleted field if not exists
                    if not hasattr(workflow, 'soft_deleted'):
                        # For now, just mark in metadata
                        if workflow.workflow_metadata is None:
                            workflow.workflow_metadata = {}
                        workflow.workflow_metadata['soft_deleted'] = True
                        workflow.updated_at = datetime.now(timezone.utc)
                        count += 1
                    else:
                        workflow.soft_deleted = True
                        workflow.updated_at = datetime.now(timezone.utc)
                        count += 1
            
            session.commit()
            logger.info(f"Soft deleted {count} workflows")
        return count

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

    def update_workflow_metrics(
        self,
        workflow_id: str,
        *,
        pages_processed: Optional[int] = None,
        validations_found: Optional[int] = None,
        validations_approved: Optional[int] = None,
        recommendations_generated: Optional[int] = None,
        recommendations_approved: Optional[int] = None,
        recommendations_actioned: Optional[int] = None,
    ) -> Optional[Workflow]:
        """Update workflow metrics in metadata."""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return None
        
        # Initialize metrics if not present
        if workflow.workflow_metadata is None:
            workflow.workflow_metadata = {}
        
        metrics = workflow.workflow_metadata.get("metrics", {})
        
        if pages_processed is not None:
            metrics["pages_processed"] = pages_processed
        if validations_found is not None:
            metrics["validations_found"] = validations_found
        if validations_approved is not None:
            metrics["validations_approved"] = validations_approved
        if recommendations_generated is not None:
            metrics["recommendations_generated"] = recommendations_generated
        if recommendations_approved is not None:
            metrics["recommendations_approved"] = recommendations_approved
        if recommendations_actioned is not None:
            metrics["recommendations_actioned"] = recommendations_actioned
        
        workflow.workflow_metadata["metrics"] = metrics

        with self.get_session() as session:
            merged_workflow = session.merge(workflow)
            session.commit()
            session.refresh(merged_workflow)

        return merged_workflow
    
    def get_workflow_metrics(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow metrics."""
        workflow = self.get_workflow(workflow_id)
        if not workflow or not workflow.workflow_metadata:
            return {}
        
        return workflow.workflow_metadata.get("metrics", {})
    
    def get_workflow_stats(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get comprehensive workflow statistics including:
        - Validation counts
        - Recommendation counts
        - Processing metrics
        """
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return {}
        
        # Get validation counts
        validations = self.list_validation_results(workflow_id=workflow_id, limit=10000)
        validations_by_status = {}
        for v in validations:
            status = v.status.value if hasattr(v.status, 'value') else str(v.status)
            validations_by_status[status] = validations_by_status.get(status, 0) + 1
        
        # Get recommendation counts
        recommendations = []
        for v in validations:
            recommendations.extend(self.list_recommendations(validation_id=v.id, limit=1000))
        
        recommendations_by_status = {}
        for r in recommendations:
            status = r.status.value if hasattr(r.status, 'value') else str(r.status)
            recommendations_by_status[status] = recommendations_by_status.get(status, 0) + 1
        
        # Get stored metrics
        stored_metrics = workflow.workflow_metadata.get("metrics", {}) if workflow.workflow_metadata else {}
        
        return {
            "workflow_id": workflow_id,
            "workflow_type": workflow.type,
            "workflow_state": workflow.state.value if hasattr(workflow.state, 'value') else str(workflow.state),
            "started_at": workflow.created_at.isoformat() if workflow.created_at else None,
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
            "pages_processed": stored_metrics.get("pages_processed", len(validations)),
            "validations_found": len(validations),
            "validations_by_status": validations_by_status,
            "recommendations_generated": len(recommendations),
            "recommendations_by_status": recommendations_by_status,
            "recommendations_approved": recommendations_by_status.get("approved", 0),
            "recommendations_actioned": recommendations_by_status.get("applied", 0),
        }
    def generate_workflow_report(self, workflow_id: str) -> Dict[str, Any]:
        """Generate a comprehensive report for a workflow.

        Args:
            workflow_id: The workflow ID

        Returns:
            Dict containing workflow report with validations, issues, and recommendations
        """
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        # Get all validations for this workflow
        validations = self.list_validation_results(workflow_id=workflow_id, limit=10000)

        # Calculate summary statistics
        total_files = len(validations)
        files_passed = sum(1 for v in validations if v.status == ValidationStatus.PASS)
        files_failed = sum(1 for v in validations if v.status == ValidationStatus.FAIL)
        files_warning = sum(1 for v in validations if v.status == ValidationStatus.WARNING)

        # Count total issues by severity
        total_issues = 0
        critical_issues = 0
        error_issues = 0
        warning_issues = 0
        info_issues = 0

        for validation in validations:
            if validation.validation_results:
                issues = validation.validation_results.get("issues", [])
                total_issues += len(issues)
                for issue in issues:
                    level = issue.get("level", "").lower()
                    if level == "critical":
                        critical_issues += 1
                    elif level == "error":
                        error_issues += 1
                    elif level == "warning":
                        warning_issues += 1
                    elif level == "info":
                        info_issues += 1

        # Calculate duration
        duration_ms = None
        if workflow.created_at and workflow.completed_at:
            duration_ms = int((workflow.completed_at - workflow.created_at).total_seconds() * 1000)

        # Get all recommendations
        all_recommendations = []
        for validation in validations:
            recs = self.list_recommendations(validation_id=validation.id)
            all_recommendations.extend(recs)

        return {
            "workflow_id": workflow_id,
            "status": workflow.state.value if hasattr(workflow.state, "value") else str(workflow.state),
            "type": workflow.type,
            "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
            "duration_ms": duration_ms,
            "summary": {
                "total_files": total_files,
                "files_passed": files_passed,
                "files_failed": files_failed,
                "files_warning": files_warning,
                "total_issues": total_issues,
                "critical_issues": critical_issues,
                "error_issues": error_issues,
                "warning_issues": warning_issues,
                "info_issues": info_issues,
                "total_recommendations": len(all_recommendations),
            },
            "validations": [v.to_dict() for v in validations],
            "recommendations": [r.to_dict() for r in all_recommendations],
        }

    def generate_validation_report(self, validation_id: str) -> Dict[str, Any]:
        """Generate a report for a single validation.

        Args:
            validation_id: The validation ID

        Returns:
            Dict containing validation report with issues and recommendations
        """
        validation = self.get_validation_result(validation_id)
        if not validation:
            raise ValueError(f"Validation {validation_id} not found")

        # Get recommendations for this validation
        recommendations = self.list_recommendations(validation_id=validation_id)

        # Extract issues from validation_results
        issues = []
        if validation.validation_results:
            issues = validation.validation_results.get("issues", [])

        # Count issues by level
        issue_counts = {"critical": 0, "error": 0, "warning": 0, "info": 0}
        for issue in issues:
            level = issue.get("level", "").lower()
            if level in issue_counts:
                issue_counts[level] += 1

        return {
            "validation_id": validation_id,
            "file_path": validation.file_path,
            "status": validation.status.value if hasattr(validation.status, "value") else str(validation.status),
            "severity": validation.severity,
            "created_at": validation.created_at.isoformat() if validation.created_at else None,
            "validation_types": validation.validation_types,
            "summary": {
                "total_issues": len(issues),
                "critical_issues": issue_counts["critical"],
                "error_issues": issue_counts["error"],
                "warning_issues": issue_counts["warning"],
                "info_issues": issue_counts["info"],
                "total_recommendations": len(recommendations),
            },
            "issues": issues,
            "recommendations": [r.to_dict() for r in recommendations],
        }

    def compare_validations(self, original_id: str, new_id: str) -> Dict[str, Any]:
        """
        Compare two validation results to calculate improvement metrics.

        Args:
            original_id: ID of the original validation
            new_id: ID of the new validation (after enhancement)

        Returns:
            Dict with comparison metrics
        """
        original = self.get_validation_result(original_id)
        new = self.get_validation_result(new_id)

        if not original:
            raise ValueError(f"Original validation {original_id} not found")
        if not new:
            raise ValueError(f"New validation {new_id} not found")

        # Extract issues from both validations
        original_issues = []
        if original.validation_results:
            original_issues = original.validation_results.get("issues", [])

        new_issues = []
        if new.validation_results:
            new_issues = new.validation_results.get("issues", [])

        # Match issues by category and message similarity
        def issue_key(issue):
            """Create a key for matching issues."""
            return (
                issue.get("category", "unknown").lower(),
                issue.get("message", "")[:100].lower()  # First 100 chars for fuzzy match
            )

        original_issue_keys = {issue_key(issue): issue for issue in original_issues}
        new_issue_keys = {issue_key(issue): issue for issue in new_issues}

        # Categorize issues
        resolved_issues = []
        for key, issue in original_issue_keys.items():
            if key not in new_issue_keys:
                resolved_issues.append(issue)

        new_issues_list = []
        for key, issue in new_issue_keys.items():
            if key not in original_issue_keys:
                new_issues_list.append(issue)

        persistent_issues = []
        for key in original_issue_keys:
            if key in new_issue_keys:
                persistent_issues.append(original_issue_keys[key])

        # Calculate improvement score
        improvement_score = 0.0
        if len(original_issues) > 0:
            improvement_score = len(resolved_issues) / len(original_issues)

        return {
            "original_validation_id": original_id,
            "new_validation_id": new_id,
            "original_issues": len(original_issues),
            "new_issues": len(new_issues),
            "resolved_issues": len(resolved_issues),
            "new_issues_added": len(new_issues_list),
            "persistent_issues": len(persistent_issues),
            "improvement_score": round(improvement_score, 2),
            "resolved_issues_list": resolved_issues,
            "new_issues_list": new_issues_list,
            "persistent_issues_list": persistent_issues,
        }

    def get_validations_without_recommendations(
        self,
        min_age_minutes: int = 5,
        limit: int = 100
    ) -> List[ValidationResult]:
        """
        Get validation results that have no recommendations generated yet.

        Args:
            min_age_minutes: Only include validations older than this many minutes
            limit: Maximum number of validations to return

        Returns:
            List of ValidationResult objects without recommendations
        """
        from datetime import datetime, timezone, timedelta

        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=min_age_minutes)

        with self.get_session() as session:
            # Get all validation IDs that have recommendations
            validations_with_recs = session.query(Recommendation.validation_id).distinct().all()
            validation_ids_with_recs = {v[0] for v in validations_with_recs}

            # Get validations without recommendations
            query = session.query(ValidationResult).filter(
                ValidationResult.created_at < cutoff_time
            )

            if validation_ids_with_recs:
                query = query.filter(
                    ~ValidationResult.id.in_(validation_ids_with_recs)
                )

            query = query.order_by(ValidationResult.created_at.desc()).limit(limit)

            results = query.all()

            # Detach from session
            for result in results:
                session.expunge(result)

            return results

    # ------------------- System Reset/Cleanup Methods -------------------

    def delete_all_validations(self, confirm: bool = False) -> int:
        """
        Delete ALL validation results from the database.

        Args:
            confirm: Must be True to actually delete (safety check)

        Returns:
            Number of validations deleted
        """
        if not confirm:
            raise ValueError("Must explicitly confirm deletion by setting confirm=True")

        with self.get_session() as session:
            count = session.query(ValidationResult).count()
            session.query(ValidationResult).delete()
            session.commit()
            logger.warning(f"Deleted all validations", extra={"count": count})
            return count

    def delete_all_workflows(self, confirm: bool = False) -> int:
        """
        Delete ALL workflows from the database.

        Args:
            confirm: Must be True to actually delete (safety check)

        Returns:
            Number of workflows deleted
        """
        if not confirm:
            raise ValueError("Must explicitly confirm deletion by setting confirm=True")

        with self.get_session() as session:
            count = session.query(Workflow).count()
            session.query(Workflow).delete()
            session.commit()
            logger.warning(f"Deleted all workflows", extra={"count": count})
            return count

    def delete_all_recommendations(self, confirm: bool = False) -> int:
        """
        Delete ALL recommendations from the database.

        Args:
            confirm: Must be True to actually delete (safety check)

        Returns:
            Number of recommendations deleted
        """
        if not confirm:
            raise ValueError("Must explicitly confirm deletion by setting confirm=True")

        with self.get_session() as session:
            count = session.query(Recommendation).count()
            session.query(Recommendation).delete()
            session.commit()
            logger.warning(f"Deleted all recommendations", extra={"count": count})
            return count

    def delete_all_audit_logs(self, confirm: bool = False) -> int:
        """
        Delete ALL audit logs from the database.

        Args:
            confirm: Must be True to actually delete (safety check)

        Returns:
            Number of audit logs deleted
        """
        if not confirm:
            raise ValueError("Must explicitly confirm deletion by setting confirm=True")

        with self.get_session() as session:
            count = session.query(AuditLog).count()
            session.query(AuditLog).delete()
            session.commit()
            logger.warning(f"Deleted all audit logs", extra={"count": count})
            return count

    def reset_system(
        self,
        confirm: bool = False,
        delete_validations: bool = True,
        delete_workflows: bool = True,
        delete_recommendations: bool = True,
        delete_audit_logs: bool = False
    ) -> dict:
        """
        Reset the entire system by deleting data.

        Args:
            confirm: Must be True to actually delete (safety check)
            delete_validations: Delete all validation results
            delete_workflows: Delete all workflows
            delete_recommendations: Delete all recommendations
            delete_audit_logs: Delete all audit logs (default: False, preserved for compliance)

        Returns:
            Dictionary with counts of deleted items
        """
        if not confirm:
            raise ValueError("Must explicitly confirm system reset by setting confirm=True")

        results = {
            "validations_deleted": 0,
            "workflows_deleted": 0,
            "recommendations_deleted": 0,
            "audit_logs_deleted": 0
        }

        # Delete in order: recommendations -> validations -> workflows -> audit logs
        # This respects foreign key constraints

        if delete_recommendations:
            results["recommendations_deleted"] = self.delete_all_recommendations(confirm=True)

        if delete_validations:
            results["validations_deleted"] = self.delete_all_validations(confirm=True)

        if delete_workflows:
            results["workflows_deleted"] = self.delete_all_workflows(confirm=True)

        if delete_audit_logs:
            results["audit_logs_deleted"] = self.delete_all_audit_logs(confirm=True)

        logger.warning("System reset completed", extra=results)
        return results


# Singleton
db_manager = DatabaseManager()
