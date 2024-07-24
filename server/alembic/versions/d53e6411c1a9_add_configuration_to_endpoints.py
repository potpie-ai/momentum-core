"""Add configuration to endpoints

Revision ID: d53e6411c1a9
Revises: fbc3da27ae0c
Create Date: 2024-07-16 19:05:47.886532

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd53e6411c1a9'
down_revision: Union[str, None] = '0d03ae5e3938'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column('endpoints', sa.Column('configuration', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade():
    op.drop_column('endpoints', 'configuration')
