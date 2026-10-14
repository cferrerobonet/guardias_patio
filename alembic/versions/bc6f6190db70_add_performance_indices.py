"""add_performance_indices

Revision ID: bc6f6190db70
Revises: f9892ba3c3f9
Create Date: 2025-10-19 16:30:35.054824

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bc6f6190db70'
down_revision: Union[str, Sequence[str], None] = 'f9892ba3c3f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Agregar índices de rendimiento."""
    # Índices para tabla guardias (alta prioridad)
    op.create_index('idx_guardias_profesor', 'guardias', ['profesor_id'])
    op.create_index('idx_guardias_zona', 'guardias', ['zona_id'])
    op.create_index('idx_guardias_fecha', 'guardias', ['fecha'])
    op.create_index('idx_guardias_turno', 'guardias', ['turno'])
    op.create_index('idx_guardias_fecha_turno', 'guardias', ['fecha', 'turno'])

    # Índices para tabla ausencias
    op.create_index('idx_ausencias_profesor', 'ausencias', ['profesor_id'])
    op.create_index('idx_ausencias_fechas', 'ausencias', ['fecha_inicio', 'fecha_fin'])
    op.create_index('idx_ausencias_activa', 'ausencias', ['activa'])


def downgrade() -> None:
    """Downgrade schema - Eliminar índices de rendimiento."""
    # Eliminar índices en orden inverso
    op.drop_index('idx_ausencias_activa', 'ausencias')
    op.drop_index('idx_ausencias_fechas', 'ausencias')
    op.drop_index('idx_ausencias_profesor', 'ausencias')
    op.drop_index('idx_guardias_fecha_turno', 'guardias')
    op.drop_index('idx_guardias_turno', 'guardias')
    op.drop_index('idx_guardias_fecha', 'guardias')
    op.drop_index('idx_guardias_zona', 'guardias')
    op.drop_index('idx_guardias_profesor', 'guardias')
