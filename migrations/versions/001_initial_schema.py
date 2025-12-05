"""Initial schema with 7 core tables

Revision ID: 001
Revises:
Create Date: 2025-12-03 21:00:00.000000

This is the initial migration that creates all 7 core TBCV database tables:
1. workflows - Workflow execution tracking
2. checkpoints - Workflow state checkpoints
3. validation_results - Validation outcomes
4. recommendations - Content improvement suggestions
5. audit_logs - Change audit trail
6. cache_entries - L2 cache storage
7. metrics - System metrics
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables."""
    from sqlalchemy import inspect

    # Get connection to check existing tables
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_tables = set(inspector.get_table_names())

    # Create workflows table
    if 'workflows' not in existing_tables:
        op.create_table(
        'workflows',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('state', sa.String(20), nullable=False),
        sa.Column('input_params', sa.Text, nullable=True),
        sa.Column('metadata', sa.Text, nullable=True),
        sa.Column('total_steps', sa.Integer, nullable=True),
        sa.Column('current_step', sa.Integer, nullable=True),
        sa.Column('progress_percent', sa.Integer, nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=True),
        sa.Column('updated_at', sa.DateTime, nullable=True),
        sa.Column('completed_at', sa.DateTime, nullable=True),
    )
        op.create_index('idx_workflows_state_created', 'workflows', ['state', 'created_at'])
        op.create_index('idx_workflows_type_state', 'workflows', ['type', 'state'])
        op.create_index('ix_workflows_state', 'workflows', ['state'])
        op.create_index('ix_workflows_type', 'workflows', ['type'])

    # Create checkpoints table
    if 'checkpoints' not in existing_tables:
        op.create_table(
        'checkpoints',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('workflow_id', sa.String(36), sa.ForeignKey('workflows.id'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('step_number', sa.Integer, nullable=False),
        sa.Column('state_data', sa.LargeBinary, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=True),
        sa.Column('validation_hash', sa.String(32), nullable=True),
        sa.Column('can_resume_from', sa.Boolean, default=True),
    )
    op.create_index('idx_checkpoints_workflow_step', 'checkpoints', ['workflow_id', 'step_number'])
    op.create_index('ix_checkpoints_workflow_id', 'checkpoints', ['workflow_id'])

    # Create validation_results table
    op.create_table(
        'validation_results',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('workflow_id', sa.String(36), sa.ForeignKey('workflows.id'), nullable=True),
        sa.Column('file_path', sa.String(1024), nullable=True),
        sa.Column('rules_applied', sa.Text, nullable=True),
        sa.Column('validation_results', sa.Text, nullable=True),
        sa.Column('validation_types', sa.Text, nullable=True),
        sa.Column('parent_validation_id', sa.String(36), sa.ForeignKey('validation_results.id'), nullable=True),
        sa.Column('comparison_data', sa.Text, nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('severity', sa.String(20), nullable=True),
        sa.Column('status', sa.String(20), nullable=True),
        sa.Column('content_hash', sa.String(64), nullable=True),
        sa.Column('ast_hash', sa.String(64), nullable=True),
        sa.Column('run_id', sa.String(64), nullable=True),
        sa.Column('file_hash', sa.String(64), nullable=True),
        sa.Column('version_number', sa.Integer, default=1),
        sa.Column('created_at', sa.DateTime, nullable=True),
        sa.Column('updated_at', sa.DateTime, nullable=True),
    )
    op.create_index('idx_validation_file_status', 'validation_results', ['file_path', 'status'])
    op.create_index('idx_validation_file_severity', 'validation_results', ['file_path', 'severity'])
    op.create_index('idx_validation_created', 'validation_results', ['created_at'])
    op.create_index('ix_validation_results_content_hash', 'validation_results', ['content_hash'])
    op.create_index('ix_validation_results_created_at', 'validation_results', ['created_at'])
    op.create_index('ix_validation_results_file_hash', 'validation_results', ['file_hash'])
    op.create_index('ix_validation_results_file_path', 'validation_results', ['file_path'])
    op.create_index('ix_validation_results_run_id', 'validation_results', ['run_id'])
    op.create_index('ix_validation_results_severity', 'validation_results', ['severity'])
    op.create_index('ix_validation_results_status', 'validation_results', ['status'])
    op.create_index('ix_validation_results_workflow_id', 'validation_results', ['workflow_id'])

    # Create recommendations table
    op.create_table(
        'recommendations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('validation_id', sa.String(36), sa.ForeignKey('validation_results.id'), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('scope', sa.String(200), nullable=True),
        sa.Column('instruction', sa.Text, nullable=True),
        sa.Column('rationale', sa.Text, nullable=True),
        sa.Column('severity', sa.String(20), default='medium'),
        sa.Column('original_content', sa.Text, nullable=True),
        sa.Column('proposed_content', sa.Text, nullable=True),
        sa.Column('diff', sa.Text, nullable=True),
        sa.Column('confidence', sa.Float, default=0.0),
        sa.Column('priority', sa.String(20), default='medium'),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('reviewed_by', sa.String(100), nullable=True),
        sa.Column('reviewed_at', sa.DateTime, nullable=True),
        sa.Column('review_notes', sa.Text, nullable=True),
        sa.Column('applied_at', sa.DateTime, nullable=True),
        sa.Column('applied_by', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=True),
        sa.Column('updated_at', sa.DateTime, nullable=True),
        sa.Column('metadata', sa.Text, nullable=True),
    )
    op.create_index('idx_recommendations_status', 'recommendations', ['status'])
    op.create_index('idx_recommendations_validation', 'recommendations', ['validation_id', 'status'])
    op.create_index('idx_recommendations_type', 'recommendations', ['type'])
    op.create_index('ix_recommendations_created_at', 'recommendations', ['created_at'])
    op.create_index('ix_recommendations_type', 'recommendations', ['type'])
    op.create_index('ix_recommendations_status', 'recommendations', ['status'])
    op.create_index('ix_recommendations_validation_id', 'recommendations', ['validation_id'])

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('recommendation_id', sa.String(36), sa.ForeignKey('recommendations.id'), nullable=True),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('actor', sa.String(100), nullable=True),
        sa.Column('actor_type', sa.String(20), nullable=True),
        sa.Column('before_state', sa.Text, nullable=True),
        sa.Column('after_state', sa.Text, nullable=True),
        sa.Column('changes', sa.Text, nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=True),
        sa.Column('metadata', sa.Text, nullable=True),
    )
    op.create_index('idx_audit_action', 'audit_logs', ['action'])
    op.create_index('idx_audit_created', 'audit_logs', ['created_at'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])
    op.create_index('ix_audit_logs_recommendation_id', 'audit_logs', ['recommendation_id'])

    # Create cache_entries table
    op.create_table(
        'cache_entries',
        sa.Column('cache_key', sa.String(200), primary_key=True),
        sa.Column('agent_id', sa.String(100), nullable=False),
        sa.Column('method_name', sa.String(100), nullable=False),
        sa.Column('input_hash', sa.String(64), nullable=False),
        sa.Column('result_data', sa.LargeBinary, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=True),
        sa.Column('expires_at', sa.DateTime, nullable=False),
        sa.Column('access_count', sa.Integer, default=1),
        sa.Column('last_accessed', sa.DateTime, nullable=True),
        sa.Column('size_bytes', sa.Integer, nullable=True),
    )
    op.create_index('idx_cache_expires', 'cache_entries', ['expires_at'])
    op.create_index('idx_cache_agent_method', 'cache_entries', ['agent_id', 'method_name'])
    op.create_index('ix_cache_entries_agent_id', 'cache_entries', ['agent_id'])
    op.create_index('ix_cache_entries_expires_at', 'cache_entries', ['expires_at'])
    op.create_index('ix_cache_entries_method_name', 'cache_entries', ['method_name'])

    # Create metrics table
    op.create_table(
        'metrics',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(100), nullable=True),
        sa.Column('value', sa.Float, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=True),
        sa.Column('metadata', sa.Text, nullable=True),
    )
    op.create_index('ix_metrics_created_at', 'metrics', ['created_at'])
    op.create_index('ix_metrics_name', 'metrics', ['name'])


def downgrade() -> None:
    """Drop all tables."""

    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('metrics')
    op.drop_table('cache_entries')
    op.drop_table('audit_logs')
    op.drop_table('recommendations')
    op.drop_table('validation_results')
    op.drop_table('checkpoints')
    op.drop_table('workflows')
