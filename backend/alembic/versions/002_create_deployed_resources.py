"""Create deployed_resources table

Revision ID: 002_deployed_resources
Revises: 001_budget_limit
Create Date: 2026-03-01 18:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002_deployed_resources'
down_revision: Union[str, None] = '001_budget_limit'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create deployed_resources table."""
    op.create_table(
        'deployed_resources',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('deployment_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('deployment_requests.id', ondelete='CASCADE'), 
                  nullable=False, index=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('tenants.id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('projects.id', ondelete='CASCADE'),
                  nullable=False, index=True),
        
        # Azure resource info
        sa.Column('azure_resource_id', sa.String(500), nullable=False, unique=True, index=True),
        sa.Column('resource_type', sa.String(100), nullable=False, index=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('resource_group', sa.String(200), nullable=False),
        sa.Column('region', sa.String(50), nullable=False),
        sa.Column('sku', sa.String(100), nullable=True),
        
        # Status
        sa.Column('status', sa.String(50), nullable=False, default='active', index=True),  # active, deleted, failed, unknown
        
        # Cost tracking
        sa.Column('monthly_cost_estimate', sa.Numeric(10, 2), nullable=True),
        sa.Column('actual_cost_mtd', sa.Numeric(10, 2), nullable=True),  # Month-to-date actual cost
        sa.Column('last_cost_update', sa.DateTime(timezone=True), nullable=True),
        
        # Metadata
        sa.Column('properties', postgresql.JSONB, nullable=False, default={}),
        sa.Column('tags', postgresql.JSONB, nullable=False, default={}),
        
        # Drift detection
        sa.Column('expected_config', postgresql.JSONB, nullable=True),  # What we deployed
        sa.Column('actual_config', postgresql.JSONB, nullable=True),    # What's actually there
        sa.Column('has_drift', sa.Boolean, nullable=False, default=False, index=True),
        sa.Column('drift_detected_at', sa.DateTime(timezone=True), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('deployed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create index for efficient queries
    op.create_index('ix_deployed_resources_tenant_project', 'deployed_resources', ['tenant_id', 'project_id'])
    op.create_index('ix_deployed_resources_status_drift', 'deployed_resources', ['status', 'has_drift'])


def downgrade() -> None:
    """Drop deployed_resources table."""
    op.drop_index('ix_deployed_resources_status_drift')
    op.drop_index('ix_deployed_resources_tenant_project')
    op.drop_table('deployed_resources')
