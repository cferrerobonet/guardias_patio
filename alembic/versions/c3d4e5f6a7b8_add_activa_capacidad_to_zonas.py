"""add activa and capacidad_profesores to zonas

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-04-18
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "zonas",
        sa.Column(
            "activa",
            sa.Boolean(),
            nullable=False,
            server_default="1",
        ),
    )
    op.add_column(
        "zonas",
        sa.Column(
            "capacidad_profesores",
            sa.Integer(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("zonas", "capacidad_profesores")
    op.drop_column("zonas", "activa")
