"""Añadir campo algoritmo_asignacion a configuracion

Revision ID: 880e0e1ef795
Revises: 36b14ee8a76d
Create Date: 2025-10-31 17:05:41.002353

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '880e0e1ef795'
down_revision: Union[str, Sequence[str], None] = '36b14ee8a76d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Añadir columna algoritmo_asignacion con valor por defecto "v2.9"
    op.add_column(
        'configuracion',
        sa.Column('algoritmo_asignacion', sa.String(), nullable=False, server_default='v2.9')
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Eliminar columna algoritmo_asignacion
    op.drop_column('configuracion', 'algoritmo_asignacion')
