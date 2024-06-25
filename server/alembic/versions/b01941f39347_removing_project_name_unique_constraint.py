"""removing project name unique constraint

Revision ID: b01941f39347
Revises: b3242d1b9b45
Create Date: 2024-06-20 00:16:02.395421

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b01941f39347'
down_revision: Union[str, None] = 'b3242d1b9b45'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        'projects_project_name_key',
        'projects',
        type_='unique'
    )


def downgrade() -> None:
    op.create_unique_constraint(
        'projects_project_name_key',
        'projects',
        ['project_name']
    )
