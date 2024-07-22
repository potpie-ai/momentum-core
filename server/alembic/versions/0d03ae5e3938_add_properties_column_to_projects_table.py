"""add properties column to projects table

Revision ID: 0d03ae5e3938
Revises: cbd8239ae1b7
Create Date: 2024-07-08 15:24:29.258881

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0d03ae5e3938'
down_revision: Union[str, None] = '754403255064'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column('projects', sa.Column('properties', sa.LargeBinary()))


def downgrade():
    op.drop_column('projects', 'properties')
