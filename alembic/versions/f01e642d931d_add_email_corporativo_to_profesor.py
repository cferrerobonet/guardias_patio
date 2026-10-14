"""add email_corporativo to profesor

Revision ID: f01e642d931d
Revises: 8d2e6a1a3b2a
Create Date: 2025-10-15 21:41:23.366310

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f01e642d931d'
down_revision: Union[str, Sequence[str], None] = '8d2e6a1a3b2a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Añadir campo email_corporativo a la tabla profesores
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    prof_cols = {c['name'] for c in inspector.get_columns('profesores')}
    if 'email_corporativo' not in prof_cols:
        op.add_column('profesores', sa.Column('email_corporativo', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Eliminar campo email_corporativo
    op.drop_column('profesores', 'email_corporativo')
