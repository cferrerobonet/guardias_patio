"""add anio_inicio_curso to configuracion

Revision ID: add_anio_inicio_curso
Revises: bc6f6190db70
Create Date: 2025-11-09 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import date

# revision identifiers, used by Alembic.
revision = 'add_anio_inicio_curso'
down_revision = 'bc6f6190db70'
branch_labels = None
depends_on = None


def upgrade():
    # Añadir columna anio_inicio_curso con valor por defecto 2025
    op.add_column('configuracion', sa.Column('anio_inicio_curso', sa.Integer(), nullable=True))
    
    # Actualizar registros existentes con valor 2025
    op.execute("UPDATE configuracion SET anio_inicio_curso = 2025 WHERE anio_inicio_curso IS NULL")
    
    # Hacer la columna NOT NULL ahora que tiene valores
    op.alter_column('configuracion', 'anio_inicio_curso', nullable=False)


def downgrade():
    op.drop_column('configuracion', 'anio_inicio_curso')
