"""add_horas_manana_tarde_to_profesor

Revision ID: 0122b6bbdc61
Revises: b939a8969a45
Create Date: 2025-10-17 15:31:03.027771

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0122b6bbdc61'
down_revision: Union[str, Sequence[str], None] = 'b939a8969a45'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Agregar columnas horas_manana y horas_tarde a la tabla profesores
    op.add_column('profesores', sa.Column('horas_manana', sa.Float(), nullable=True))
    op.add_column('profesores', sa.Column('horas_tarde', sa.Float(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Eliminar columnas horas_manana y horas_tarde de la tabla profesores
    op.drop_column('profesores', 'horas_tarde')
    op.drop_column('profesores', 'horas_manana')
