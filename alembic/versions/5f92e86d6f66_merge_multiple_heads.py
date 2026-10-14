"""merge multiple heads

Revision ID: 5f92e86d6f66
Revises: 00ccb064f341, d1e2f3a4b5c6
Create Date: 2025-11-16 21:49:04.689058

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5f92e86d6f66'
down_revision: Union[str, Sequence[str], None] = ('00ccb064f341', 'd1e2f3a4b5c6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
