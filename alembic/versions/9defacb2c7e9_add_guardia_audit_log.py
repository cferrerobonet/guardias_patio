"""add_guardia_audit_log

Revision ID: 9defacb2c7e9
Revises: 6a4c776e7fb0
Create Date: 2026-04-22 13:36:42.957617

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '9defacb2c7e9'
down_revision: Union[str, Sequence[str], None] = '6a4c776e7fb0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'guardias_audit_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('guardia_id', sa.Integer(), nullable=True),
        sa.Column('accion', sa.String(), nullable=False),
        sa.Column('profesor_id', sa.Integer(), nullable=True),
        sa.Column('usuario', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('detalle', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['profesor_id'], ['profesores.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('guardias_audit_log', schema=None) as batch_op:
        batch_op.create_index('ix_audit_log_accion', ['accion'], unique=False)
        batch_op.create_index('ix_audit_log_profesor_id', ['profesor_id'], unique=False)
        batch_op.create_index('ix_audit_log_timestamp', ['timestamp'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('guardias_audit_log', schema=None) as batch_op:
        batch_op.drop_index('ix_audit_log_timestamp')
        batch_op.drop_index('ix_audit_log_profesor_id')
        batch_op.drop_index('ix_audit_log_accion')
    op.drop_table('guardias_audit_log')
