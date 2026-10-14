"""add_zona_preferida_to_profesor

Revision ID: 00ccb064f341
Revises: 5642dea8340e
Create Date: 2025-11-02 20:48:27.292988

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '00ccb064f341'
down_revision: Union[str, Sequence[str], None] = '5642dea8340e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # SQLite no soporta ALTER TABLE para foreign keys, usar batch mode
    with op.batch_alter_table('profesores', schema=None) as batch_op:
        batch_op.add_column(sa.Column('zona_preferida_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_profesores_zona_preferida',
            'zonas',
            ['zona_preferida_id'],
            ['id'],
            ondelete='SET NULL'
        )


def downgrade() -> None:
    """Downgrade schema."""
    # Usar batch mode para downgrade también
    with op.batch_alter_table('profesores', schema=None) as batch_op:
        batch_op.drop_constraint('fk_profesores_zona_preferida', type_='foreignkey')
        batch_op.drop_column('zona_preferida_id')
