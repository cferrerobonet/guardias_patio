"""add_zona_fecha_campos

Revision ID: 5642dea8340e
Revises: 880e0e1ef795
Create Date: 2025-10-31 18:01:47.557863

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5642dea8340e'
down_revision: Union[str, Sequence[str], None] = '880e0e1ef795'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Añadir campos fecha_inicio y fecha_fin a tabla zonas."""
    # Verificar si las columnas ya existen antes de añadirlas
    import sqlite3
    from alembic import context
    
    config = context.config
    # Obtener la conexión actual
    connection = op.get_bind()
    
    # Verificar estructura actual de la tabla zonas
    result = connection.execute(sa.text("PRAGMA table_info(zonas)"))
    columns = [row[1] for row in result]
    
    # Añadir fecha_inicio si no existe
    if 'fecha_inicio' not in columns:
        op.add_column('zonas', sa.Column('fecha_inicio', sa.Date(), nullable=True))
        print("  ✓ Añadida columna fecha_inicio a tabla zonas")
    else:
        print("  ⚠ Columna fecha_inicio ya existe en tabla zonas")
    
    # Añadir fecha_fin si no existe
    if 'fecha_fin' not in columns:
        op.add_column('zonas', sa.Column('fecha_fin', sa.Date(), nullable=True))
        print("  ✓ Añadida columna fecha_fin a tabla zonas")
    else:
        print("  ⚠ Columna fecha_fin ya existe en tabla zonas")


def downgrade() -> None:
    """Downgrade schema - Eliminar campos fecha_inicio y fecha_fin de tabla zonas."""
    # SQLite no soporta DROP COLUMN directamente, requiere recrear la tabla
    # Por simplicidad, dejamos las columnas (no causa problemas si están vacías)
    print("  ⚠ Downgrade no elimina columnas en SQLite (requiere recrear tabla)")
    print("  ⚠ Las columnas fecha_inicio y fecha_fin permanecerán en la tabla")
    pass
