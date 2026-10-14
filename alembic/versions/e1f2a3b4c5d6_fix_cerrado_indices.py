"""fix cerrado column and add performance indices

Revision ID: e1f2a3b4c5d6
Revises: c1d2e3f4a5b6
Create Date: 2026-04-17

Corrige inconsistencia cerrado/archivado en cursos_escolares y añade índices
de rendimiento en profesores y guardias.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "e1f2a3b4c5d6"
down_revision: Union[str, Sequence[str], None] = "c1d2e3f4a5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    # ── cursos_escolares: renombrar archivado → cerrado si procede ──────────
    cursos_cols = [c["name"] for c in inspector.get_columns("cursos_escolares")]
    if "archivado" in cursos_cols and "cerrado" not in cursos_cols:
        op.alter_column("cursos_escolares", "archivado", new_column_name="cerrado")
    elif "cerrado" not in cursos_cols:
        op.add_column(
            "cursos_escolares",
            sa.Column("cerrado", sa.Boolean(), nullable=False, server_default="0"),
        )

    # ── Índices en profesores ───────────────────────────────────────────────
    existing_indices = {i["name"] for i in inspector.get_indexes("profesores")}
    if "ix_profesores_activo" not in existing_indices:
        op.create_index("ix_profesores_activo", "profesores", ["activo"])
    if "ix_profesores_turno" not in existing_indices:
        op.create_index("ix_profesores_turno", "profesores", ["turno"])

    # ── Índices en guardias ─────────────────────────────────────────────────
    existing_indices = {i["name"] for i in inspector.get_indexes("guardias")}
    if "ix_guardias_curso_id" not in existing_indices:
        op.create_index("ix_guardias_curso_id", "guardias", ["curso_id"])
    if "ix_guardias_turno" not in existing_indices:
        op.create_index("ix_guardias_turno", "guardias", ["turno"])
    if "ix_guardias_fecha_turno_recreo" not in existing_indices:
        op.create_index("ix_guardias_fecha_turno_recreo", "guardias", ["fecha", "turno", "recreo"])


def downgrade() -> None:
    pass
