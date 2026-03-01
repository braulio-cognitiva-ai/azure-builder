"""Add budget_limit to projects

Revision ID: 001_budget_limit
Revises: 
Create Date: 2026-03-01 16:58:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_budget_limit'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add budget_limit column to projects table."""
    op.add_column('projects', 
        sa.Column('budget_limit', sa.Numeric(precision=10, scale=2), nullable=True)
    )


def downgrade() -> None:
    """Remove budget_limit column from projects table."""
    op.drop_column('projects', 'budget_limit')
