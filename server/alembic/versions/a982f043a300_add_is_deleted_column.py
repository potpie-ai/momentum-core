"""Add is_deleted column

Revision ID: a982f043a300
Revises: 754403255064
Create Date: 2024-06-27 16:20:47.697478

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a982f043a300'
down_revision: Union[str, None] = '754403255064'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('projects', sa.Column(
        'is_deleted',
        sa.Boolean(),
        nullable=False,
        server_default=sa.false())
        )

    projects_table = sa.table('projects',
                              sa.column('is_deleted', sa.Boolean()))
    op.execute(projects_table.update().values(is_deleted=False))


def downgrade() -> None:
    op.drop_column('projects', 'is_deleted')