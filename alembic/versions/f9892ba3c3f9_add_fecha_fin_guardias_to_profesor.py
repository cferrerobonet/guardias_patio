"""add_fecha_fin_guardias_to_profesor

Revision ID: f9892ba3c3f9
Revises: 0122b6bbdc61
Create Date: 2025-10-17 16:00:14.304313

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f9892ba3c3f9'
down_revision: Union[str, Sequence[str], None] = '0122b6bbdc61'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Agregar columna fecha_fin_guardias a la tabla profesores
    op.add_column('profesores', sa.Column('fecha_fin_guardias', sa.Date(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Eliminar columna fecha_fin_guardias de la tabla profesores
    op.drop_column('profesores', 'fecha_fin_guardias')
