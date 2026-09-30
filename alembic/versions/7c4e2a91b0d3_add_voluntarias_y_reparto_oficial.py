"""add guardias_voluntarias a profesores y fecha_inicio_reparto_oficial a configuracion

Revision ID: 7c4e2a91b0d3
Revises: 9defacb2c7e9
Create Date: 2026-09-30
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "7c4e2a91b0d3"
down_revision: Union[str, Sequence[str], None] = "9defacb2c7e9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "profesores",
        sa.Column("guardias_voluntarias", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "configuracion",
        sa.Column("fecha_inicio_reparto_oficial", sa.Date(), nullable=True),
    )


def downgrade() -> None:
    with op.batch_alter_table("configuracion", schema=None) as batch_op:
        batch_op.drop_column("fecha_inicio_reparto_oficial")
    with op.batch_alter_table("profesores", schema=None) as batch_op:
        batch_op.drop_column("guardias_voluntarias")
