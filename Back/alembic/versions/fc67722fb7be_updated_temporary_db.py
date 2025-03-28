"""updated temporary_db

Revision ID: fc67722fb7be
Revises: bf4907087eb7
Create Date: 2025-03-20 11:48:46.480390

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fc67722fb7be'
down_revision: Union[str, None] = 'bf4907087eb7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('temporary_attendance', 'timetable_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('temporary_attendance', 'timetable_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    # ### end Alembic commands ###
