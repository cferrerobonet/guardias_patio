"""add missing columns for profesores.activo and configuracion fields

Revision ID: a1b2c3d4e5f6
Revises: 5f92e86d6f66
Create Date: 2025-12-11 10:00:00.000000

Esta migración añade columnas que pueden faltar en bases de datos antiguas:
- profesores.activo (Boolean, default True)
- configuracion.anio_inicio_curso (Integer)
- configuracion.curso_activo_id (Integer, FK)
- guardias.curso_id (Integer, FK)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '5f92e86d6f66'
branch_labels = None
depends_on = None


def column_exists(table_name: str, column_name: str) -> bool:
    """Verifica si una columna existe en una tabla."""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def table_exists(table_name: str) -> bool:
    """Verifica si una tabla existe."""
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade():
    """Añade columnas faltantes de forma segura."""
    
    # 1. Añadir profesores.activo si no existe
    if not column_exists('profesores', 'activo'):
        with op.batch_alter_table('profesores') as batch_op:
            batch_op.add_column(
                sa.Column('activo', sa.Boolean(), nullable=False, server_default='1')
            )
        print("✓ Añadida columna profesores.activo")
    
    # 2. Crear tabla cursos_escolares si no existe
    if not table_exists('cursos_escolares'):
        op.create_table(
            "cursos_escolares",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("nombre", sa.String(), nullable=False),
            sa.Column("anio_inicio", sa.Integer(), nullable=False),
            sa.Column("anio_fin", sa.Integer(), nullable=False),
            sa.Column("fecha_inicio", sa.Date(), nullable=False),
            sa.Column("fecha_fin", sa.Date(), nullable=False),
            sa.Column("activo", sa.Boolean(), nullable=False, server_default="1"),
            sa.Column("archivado", sa.Boolean(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("id"),
        )
        print("✓ Creada tabla cursos_escolares")
    
    # 3. Añadir configuracion.anio_inicio_curso si no existe
    if not column_exists('configuracion', 'anio_inicio_curso'):
        with op.batch_alter_table('configuracion') as batch_op:
            batch_op.add_column(
                sa.Column('anio_inicio_curso', sa.Integer(), nullable=True)
            )
        # Poblar desde fecha_inicio_curso
        op.execute("""
            UPDATE configuracion 
            SET anio_inicio_curso = CAST(strftime('%Y', fecha_inicio_curso) AS INTEGER)
            WHERE anio_inicio_curso IS NULL AND fecha_inicio_curso IS NOT NULL
        """)
        print("✓ Añadida columna configuracion.anio_inicio_curso")
    
    # 4. Añadir configuracion.curso_activo_id si no existe
    if not column_exists('configuracion', 'curso_activo_id'):
        with op.batch_alter_table('configuracion') as batch_op:
            batch_op.add_column(
                sa.Column('curso_activo_id', sa.Integer(), nullable=True)
            )
        print("✓ Añadida columna configuracion.curso_activo_id")
    
    # 5. Añadir guardias.curso_id si no existe
    if not column_exists('guardias', 'curso_id'):
        with op.batch_alter_table('guardias') as batch_op:
            batch_op.add_column(
                sa.Column('curso_id', sa.Integer(), nullable=True)
            )
        print("✓ Añadida columna guardias.curso_id")


def downgrade():
    """No elimina columnas para evitar pérdida de datos."""
    pass
