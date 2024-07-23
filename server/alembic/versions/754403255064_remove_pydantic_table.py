"""remove pydantic table

Revision ID: 754403255064
Revises: fbc3da27ae0c
Create Date: 2024-07-05 14:54:38.136079

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '754403255064'
down_revision: Union[str, None] = 'fbc3da27ae0c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table('pydantic')


def downgrade() -> None:
    op.create_table('pydantic',
                    sa.Column('filepath', sa.Text(), nullable=False),
                    sa.Column('classname', sa.Text(), nullable=False),
                    sa.Column('definition', sa.Text(), nullable=True),
                    sa.Column('project_id', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('filepath', 'classname')
                    )
    # ### end Alembic commands ###
