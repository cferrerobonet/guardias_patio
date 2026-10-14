"""add sustitucion fields to guardias

Añade es_sustitucion, profesor_sustituido_id y notas a la tabla guardias
para soporte completo del sistema de sustituciones.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f7
Create Date: 2026-04-18

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("guardias") as batch_op:
        batch_op.add_column(
            sa.Column("es_sustitucion", sa.Boolean(), nullable=False, server_default="0")
        )
        batch_op.add_column(
            sa.Column("profesor_sustituido_id", sa.Integer(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("notas", sa.Text(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_guardias_profesor_sustituido",
            "profesores",
            ["profesor_sustituido_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    with op.batch_alter_table("guardias") as batch_op:
        batch_op.drop_constraint("fk_guardias_profesor_sustituido", type_="foreignkey")
        batch_op.drop_column("notas")
        batch_op.drop_column("profesor_sustituido_id")
        batch_op.drop_column("es_sustitucion")
