"""add_horas_manana_tarde_to_profesor

Revision ID: b939a8969a45
Revises: 3605cca11581
Create Date: 2025-10-17 15:30:54.541952

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b939a8969a45'
down_revision: Union[str, Sequence[str], None] = '3605cca11581'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
