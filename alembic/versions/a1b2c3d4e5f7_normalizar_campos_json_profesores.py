"""Normalizar campos JSON de profesores a tablas relacionales

Revision ID: a1b2c3d4e5f7
Revises: e1f2a3b4c5d6
Create Date: 2026-04-17

Crea tablas `profesor_dias_semana` y `profesor_recreos` para normalizar
los campos JSON `dias_semana_permitidos` y `recreos_permitidos` de la
tabla `profesores` (violación de 1NF). Los datos existentes se migran
automáticamente. Las columnas JSON originales se mantienen como fallback
hasta que toda la capa de servicios use las nuevas tablas.
"""

import ast
import json

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f7"
down_revision = "e1f2a3b4c5d6"
branch_labels = None
depends_on = None


def _parse_json_field(value) -> list:
    """Parsea un campo JSON de forma defensiva."""
    if not value:
        return []
    if isinstance(value, list):
        return value
    try:
        result = json.loads(value)
        if isinstance(result, list):
            return result
    except (json.JSONDecodeError, TypeError):
        pass
    try:
        result = ast.literal_eval(value)
        if isinstance(result, list):
            return result
    except (ValueError, SyntaxError):
        pass
    return []


def upgrade() -> None:
    conn = op.get_bind()

    # ── 1. Crear tabla profesor_dias_semana ──────────────────────────────────
    if not _table_exists(conn, "profesor_dias_semana"):
        op.create_table(
            "profesor_dias_semana",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column(
                "profesor_id",
                sa.Integer,
                sa.ForeignKey("profesores.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("dia_semana", sa.Integer, nullable=False),  # 0=lunes … 6=domingo
        )
        op.create_index(
            "ix_prof_dias_semana_profesor_id",
            "profesor_dias_semana",
            ["profesor_id"],
        )

    # ── 2. Crear tabla profesor_recreos ──────────────────────────────────────
    if not _table_exists(conn, "profesor_recreos"):
        op.create_table(
            "profesor_recreos",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column(
                "profesor_id",
                sa.Integer,
                sa.ForeignKey("profesores.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("recreo_numero", sa.Integer, nullable=False),  # 1, 2, …
        )
        op.create_index(
            "ix_prof_recreos_profesor_id",
            "profesor_recreos",
            ["profesor_id"],
        )

    # ── 3. Migrar datos existentes ───────────────────────────────────────────
    profesores = conn.execute(
        sa.text("SELECT id, dias_semana_permitidos, recreos_permitidos FROM profesores")
    ).fetchall()

    for row in profesores:
        prof_id = row[0]
        dias = _parse_json_field(row[1])
        recreos_raw = row[2]

        # dias_semana_permitidos: list[int]
        for dia in dias:
            try:
                dia_int = int(dia)
                existing = conn.execute(
                    sa.text(
                        "SELECT id FROM profesor_dias_semana "
                        "WHERE profesor_id = :pid AND dia_semana = :dia"
                    ),
                    {"pid": prof_id, "dia": dia_int},
                ).fetchone()
                if not existing:
                    conn.execute(
                        sa.text(
                            "INSERT INTO profesor_dias_semana (profesor_id, dia_semana) "
                            "VALUES (:pid, :dia)"
                        ),
                        {"pid": prof_id, "dia": dia_int},
                    )
            except (ValueError, TypeError):
                pass

        # recreos_permitidos: puede ser list[int] o dict {"turno": [recreos]}
        recreos_list: list[int] = []
        raw = recreos_raw
        if raw:
            parsed = _parse_json_field(raw) if isinstance(raw, str) else raw
            if isinstance(parsed, list):
                recreos_list = [int(r) for r in parsed if str(r).isdigit()]
            elif isinstance(parsed, dict):
                for val in parsed.values():
                    if isinstance(val, list):
                        recreos_list.extend([int(r) for r in val if str(r).isdigit()])

        for recreo in set(recreos_list):
            existing = conn.execute(
                sa.text(
                    "SELECT id FROM profesor_recreos "
                    "WHERE profesor_id = :pid AND recreo_numero = :recreo"
                ),
                {"pid": prof_id, "recreo": recreo},
            ).fetchone()
            if not existing:
                conn.execute(
                    sa.text(
                        "INSERT INTO profesor_recreos (profesor_id, recreo_numero) "
                        "VALUES (:pid, :recreo)"
                    ),
                    {"pid": prof_id, "recreo": recreo},
                )


def downgrade() -> None:
    op.drop_index("ix_prof_recreos_profesor_id", table_name="profesor_recreos")
    op.drop_table("profesor_recreos")
    op.drop_index("ix_prof_dias_semana_profesor_id", table_name="profesor_dias_semana")
    op.drop_table("profesor_dias_semana")


def _table_exists(conn, table_name: str) -> bool:
    result = conn.execute(
        sa.text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=:name"
        ),
        {"name": table_name},
    ).fetchone()
    return result is not None
