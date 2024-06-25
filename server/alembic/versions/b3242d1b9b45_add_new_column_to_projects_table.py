"""Add new_column to projects table

Revision ID: b3242d1b9b45
Revises: 6c007877a09d
Create Date: 2024-06-15 19:48:39.455777

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3242d1b9b45'
down_revision: Union[str, None] = '6c007877a09d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('projects', sa.Column('commit_id', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('projects', 'commit_id')
