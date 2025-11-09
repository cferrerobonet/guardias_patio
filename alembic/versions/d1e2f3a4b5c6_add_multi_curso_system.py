"""add multi-curso system

Revision ID: d1e2f3a4b5c6
Revises: bc6f6190db70
Create Date: 2025-11-09 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'd1e2f3a4b5c6'
down_revision = 'bc6f6190db70'
branch_labels = None
depends_on = None


def upgrade():
    """Añade soporte para sistema Multi-Curso."""
    # 1. Crear tabla cursos_escolares
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
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # 2. Añadir anio_inicio_curso a configuracion (si no existe)
    with op.batch_alter_table("configuracion") as batch_op:
        batch_op.add_column(
            sa.Column("anio_inicio_curso", sa.Integer(), nullable=True)
        )

    # 3. Poblar anio_inicio_curso desde fecha_inicio_curso
    op.execute(
        """
        UPDATE configuracion 
        SET anio_inicio_curso = CAST(strftime('%Y', fecha_inicio_curso) AS INTEGER)
        WHERE anio_inicio_curso IS NULL
        """
    )

    # 4. Añadir curso_activo_id a configuracion
    with op.batch_alter_table("configuracion") as batch_op:
        batch_op.add_column(
            sa.Column("curso_activo_id", sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_configuracion_curso_activo",
            "cursos_escolares",
            ["curso_activo_id"],
            ["id"],
        )

    # 5. Añadir curso_id a guardias
    with op.batch_alter_table("guardias") as batch_op:
        batch_op.add_column(sa.Column("curso_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_guardias_curso", "cursos_escolares", ["curso_id"], ["id"]
        )


def downgrade():
    # Eliminar en orden inverso
    op.drop_constraint('fk_guardias_curso', 'guardias', type_='foreignkey')
    op.drop_column('guardias', 'curso_id')
    
    op.drop_constraint('fk_configuracion_curso_activo', 'configuracion', type_='foreignkey')
    op.drop_column('configuracion', 'curso_activo_id')
    
    op.drop_table('cursos_escolares')
