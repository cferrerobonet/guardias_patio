"""merge_heads

Revision ID: 2a0ba39df96a
Revises: b1c2d3e4f5a6, c3d4e5f6a7b8
Create Date: 2026-04-19 13:26:07.825603

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2a0ba39df96a'
down_revision: Union[str, Sequence[str], None] = ('b1c2d3e4f5a6', 'c3d4e5f6a7b8')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
