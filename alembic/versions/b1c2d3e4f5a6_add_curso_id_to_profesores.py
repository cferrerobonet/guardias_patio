"""add curso_id to profesores

Revision ID: b1c2d3e4f5a6
Revises: a0b1c2d3e4f5
Create Date: 2026-04-18
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b1c2d3e4f5a6'
down_revision = 'a0b1c2d3e4f5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("profesores") as batch_op:
        batch_op.add_column(
            sa.Column("curso_id", sa.Integer(), sa.ForeignKey("cursos_escolares.id"), nullable=True)
        )
        batch_op.create_index("ix_profesores_curso_id", ["curso_id"])


def downgrade() -> None:
    with op.batch_alter_table("profesores") as batch_op:
        batch_op.drop_index("ix_profesores_curso_id")
        batch_op.drop_column("curso_id")
