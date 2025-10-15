"""unificar_nombre_apellidos_en_nombre_completo

Revision ID: 5fc6681ada26
Revises: f01e642d931d
Create Date: 2025-10-15 22:36:10.648633

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5fc6681ada26'
down_revision: Union[str, Sequence[str], None] = 'f01e642d931d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Unifica nombre y apellidos en un solo campo nombre_completo (APELLIDOS, NOMBRE)."""
    # SQLite no soporta ALTER COLUMN, usamos batch operations
    with op.batch_alter_table('profesores') as batch_op:
        # 1. Añadir nueva columna nombre_completo
        batch_op.add_column(sa.Column('nombre_completo', sa.String(), nullable=True))
    
    # 2. Migrar datos existentes: concatenar apellidos + ', ' + nombre
    connection = op.get_bind()
    connection.execute(sa.text(
        "UPDATE profesores SET nombre_completo = apellidos || ', ' || nombre"
    ))
    
    # 3. Recrear tabla con nombre_completo NOT NULL y sin nombre/apellidos
    with op.batch_alter_table('profesores') as batch_op:
        # Primero hacer NOT NULL
        batch_op.alter_column('nombre_completo', nullable=False)
        # Eliminar columnas antiguas
        batch_op.drop_column('nombre')
        batch_op.drop_column('apellidos')


def downgrade() -> None:
    """Revierte la unificación separando nombre_completo en nombre y apellidos."""
    # SQLite requiere batch operations
    with op.batch_alter_table('profesores') as batch_op:
        # 1. Añadir columnas antiguas
        batch_op.add_column(sa.Column('nombre', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('apellidos', sa.String(), nullable=True))
    
    # 2. Intentar separar nombre_completo en apellidos y nombre
    connection = op.get_bind()
    connection.execute(sa.text("""
        UPDATE profesores 
        SET apellidos = SUBSTR(nombre_completo, 1, INSTR(nombre_completo, ', ') - 1),
            nombre = SUBSTR(nombre_completo, INSTR(nombre_completo, ', ') + 2)
        WHERE INSTR(nombre_completo, ', ') > 0
    """))
    
    # Para registros sin coma, poner todo en apellidos
    connection.execute(sa.text("""
        UPDATE profesores 
        SET apellidos = nombre_completo,
            nombre = ''
        WHERE INSTR(nombre_completo, ', ') = 0
    """))
    
    # 3. Hacer campos NOT NULL y eliminar nombre_completo
    with op.batch_alter_table('profesores') as batch_op:
        batch_op.alter_column('nombre', nullable=False)
        batch_op.alter_column('apellidos', nullable=False)
        batch_op.drop_column('nombre_completo')
