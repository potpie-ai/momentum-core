"""Add is_deleted column and remove directory constraint

Revision ID: a982f043a300
Revises: cbd8239ae1b7
Create Date: 2024-06-27 16:20:47.697478

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a982f043a300'
down_revision: Union[str, None] = 'cbd8239ae1b7'
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
    """
        Remove the unique constraint from the 'directory' column, since it is causing issues if we're
        trying to reparse a project after deleting it
    """
    op.drop_constraint('projects_directory_key', 'projects', type_='unique')


def downgrade() -> None:
    op.create_unique_constraint('projects_directory_key', 'projects', ['directory'])
    op.drop_column('projects', 'is_deleted')