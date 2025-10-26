"""add_fecha_inicio_fin_to_zona

Revision ID: 36b14ee8a76d
Revises: bc6f6190db70
Create Date: 2025-10-25 19:52:50.664389

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '36b14ee8a76d'
down_revision: Union[str, Sequence[str], None] = 'bc6f6190db70'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Añadir columnas de fecha opcional a la tabla zonas
    op.add_column('zonas', sa.Column('fecha_inicio', sa.Date(), nullable=True))
    op.add_column('zonas', sa.Column('fecha_fin', sa.Date(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Eliminar columnas de fecha de la tabla zonas
    op.drop_column('zonas', 'fecha_fin')
    op.drop_column('zonas', 'fecha_inicio')
