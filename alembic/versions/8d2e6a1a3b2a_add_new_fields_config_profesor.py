"""add new fields to configuracion and profesor

Revision ID: 8d2e6a1a3b2a
Revises: f8c079469533
Create Date: 2025-10-15 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8d2e6a1a3b2a'
down_revision = 'f8c079469533'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Profesores
    prof_cols = {c['name'] for c in inspector.get_columns('profesores')}
    if 'tutor' not in prof_cols:
        op.add_column('profesores', sa.Column('tutor', sa.Boolean(), nullable=False, server_default=sa.text('0')))
    if 'fecha_inicio_guardias' not in prof_cols:
        op.add_column('profesores', sa.Column('fecha_inicio_guardias', sa.Date(), nullable=True))
    if 'dias_semana_permitidos' not in prof_cols:
        op.add_column('profesores', sa.Column('dias_semana_permitidos', sa.Text(), nullable=True))
    if 'recreos_permitidos' not in prof_cols:
        op.add_column('profesores', sa.Column('recreos_permitidos', sa.Text(), nullable=True))

    # Configuración
    conf_cols = {c['name'] for c in inspector.get_columns('configuracion')}
    if 'activar_festivos_automaticos' not in conf_cols:
        op.add_column('configuracion', sa.Column('activar_festivos_automaticos', sa.Boolean(), nullable=False, server_default=sa.text('1')))
    if 'dias_no_lectivos_personalizados' not in conf_cols:
        op.add_column('configuracion', sa.Column('dias_no_lectivos_personalizados', sa.Text(), nullable=True))
    if 'recreos_config' not in conf_cols:
        op.add_column('configuracion', sa.Column('recreos_config', sa.Text(), nullable=True))
    if 'ajuste_tutores' not in conf_cols:
        op.add_column('configuracion', sa.Column('ajuste_tutores', sa.Float(), nullable=False, server_default='1.0'))
    if 'ajuste_no_tutores' not in conf_cols:
        op.add_column('configuracion', sa.Column('ajuste_no_tutores', sa.Float(), nullable=False, server_default='1.0'))

    # Intentar limpiar server_default solo si el dialecto lo soporta (no SQLite)
    if bind.dialect.name != 'sqlite':
        op.alter_column('profesores', 'tutor', server_default=None)
        op.alter_column('configuracion', 'activar_festivos_automaticos', server_default=None)


def downgrade() -> None:
    # Revertir Configuración
    op.drop_column('configuracion', 'ajuste_no_tutores')
    op.drop_column('configuracion', 'ajuste_tutores')
    op.drop_column('configuracion', 'recreos_config')
    op.drop_column('configuracion', 'dias_no_lectivos_personalizados')
    op.drop_column('configuracion', 'activar_festivos_automaticos')

    # Revertir Profesores
    op.drop_column('profesores', 'recreos_permitidos')
    op.drop_column('profesores', 'dias_semana_permitidos')
    op.drop_column('profesores', 'fecha_inicio_guardias')
    op.drop_column('profesores', 'tutor')
