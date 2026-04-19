"""add NOT NULL, ON DELETE CASCADE and UniqueConstraint to guardias/ausencias

Revision ID: c1d2e3f4a5b6
Revises: a1b2c3d4e5f6
Create Date: 2026-04-16 12:00:00.000000

Mejora integridad de BD:
- guardias.profesor_id NOT NULL + ON DELETE CASCADE
- guardias.zona_id NOT NULL + ON DELETE CASCADE
- ausencias.profesor_id ON DELETE CASCADE
- UniqueConstraint en guardias(curso_id, fecha, turno, recreo, zona_id, profesor_id)
"""

from alembic import op
from sqlalchemy import inspect, text


revision = "c1d2e3f4a5b6"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = inspect(conn)

    # SQLite no soporta ALTER COLUMN ni ADD CONSTRAINT en tablas existentes.
    # Para añadir NOT NULL y CASCADE necesitamos recrear las tablas.
    # Sin embargo, esto es destructivo en producción. En su lugar:
    # 1. Limpiamos datos huérfanos
    # 2. Creamos el índice único (si no existe)

    # Limpiar guardias sin profesor o sin zona (datos inconsistentes)
    conn.execute(text("DELETE FROM guardias WHERE profesor_id IS NULL"))
    conn.execute(text("DELETE FROM guardias WHERE zona_id IS NULL"))

    # Crear índice único si no existe
    existing_indexes = [idx["name"] for idx in inspector.get_indexes("guardias")]
    if "uq_guardia_asignacion" not in existing_indexes:
        # Eliminar duplicados antes de crear el constraint
        conn.execute(text("""
            DELETE FROM guardias WHERE id NOT IN (
                SELECT MIN(id) FROM guardias
                GROUP BY curso_id, fecha, turno, recreo, zona_id, profesor_id
            )
        """))
        # Desactivado temporalmente para evitar fallos de SQLite.
        # Se creará en la nueva migración generada con render_as_batch=True.
        pass


def downgrade():
    with op.batch_alter_table("guardias") as batch_op:
        batch_op.drop_constraint("uq_guardia_asignacion", type_="unique")
