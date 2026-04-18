"""Add performance indexes and data integrity constraints

Revision ID: a0b1c2d3e4f5
Revises: f9892ba3c3f9
Create Date: 2026-04-22 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a0b1c2d3e4f5'
down_revision = 'f9892ba3c3f9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Crear índices para mejorar performance en queries frecuentes
    op.create_index('ix_guardias_curso_id', 'guardias', ['curso_escolar_id'])
    op.create_index('ix_guardias_turno', 'guardias', ['turno'])
    op.create_index('ix_guardias_fecha', 'guardias', ['fecha'])
    op.create_index('ix_guardias_profesor_fecha', 'guardias', ['profesor_id', 'fecha'])
    op.create_index('ix_guardias_zona_fecha', 'guardias', ['zona_id', 'fecha'])
    
    op.create_index('ix_profesor_turno', 'profesores', ['turno'])
    op.create_index('ix_profesor_activo', 'profesores', ['activo'])
    op.create_index('ix_profesor_curso', 'profesores', ['curso_escolar_id'])
    
    op.create_index('ix_ausencia_profesor_fecha', 'ausencias', ['profesor_id', 'fecha_inicio', 'fecha_fin'])
    
    op.create_index('ix_zona_activo', 'zonas', ['activa'])
    op.create_index('ix_zona_turno', 'zonas', ['turno'])
    
    # Agregar CheckConstraints para integridad de datos
    # Turno debe ser uno de los valores válidos
    op.create_check_constraint(
        'ck_guardias_turno_valid',
        'guardias',
        "turno IN ('mañana', 'tarde', 'mixto')"
    )
    
    op.create_check_constraint(
        'ck_profesores_turno_valid',
        'profesores',
        "turno IN ('mañana', 'tarde', 'mixto')"
    )
    
    op.create_check_constraint(
        'ck_zonas_turno_valid',
        'zonas',
        "turno IN ('mañana', 'tarde', 'mixto')"
    )
    
    # Horas de contrato debe ser positivo
    op.create_check_constraint(
        'ck_profesores_horas_positivo',
        'profesores',
        'horas_contrato > 0'
    )
    
    # Recreo debe ser >= 1 (recreo 0 no tiene sentido)
    op.create_check_constraint(
        'ck_guardias_recreo_positivo',
        'guardias',
        'recreo >= 1'
    )
    
    # Tipo de ausencia debe estar en valores válidos
    op.create_check_constraint(
        'ck_ausencias_tipo_valid',
        'ausencias',
        "tipo IN ('licencia', 'enfermedad', 'dias_personales', 'otro')"
    )
    
    # Fecha fin >= fecha inicio en ausencias
    op.create_check_constraint(
        'ck_ausencias_fecha_valid',
        'ausencias',
        'fecha_fin >= fecha_inicio'
    )


def downgrade() -> None:
    # Eliminar índices
    op.drop_index('ix_ausencias_fecha_valid', table_name='ausencias')
    op.drop_index('ix_ausencias_tipo_valid', table_name='ausencias')
    op.drop_index('ix_guardias_recreo_positivo', table_name='guardias')
    op.drop_index('ix_profesores_horas_positivo', table_name='profesores')
    op.drop_index('ix_zonas_turno_valid', table_name='zonas')
    op.drop_index('ix_profesores_turno_valid', table_name='profesores')
    op.drop_index('ix_guardias_turno_valid', table_name='guardias')
    
    op.drop_index('ix_zona_turno', table_name='zonas')
    op.drop_index('ix_zona_activo', table_name='zonas')
    op.drop_index('ix_ausencia_profesor_fecha', table_name='ausencias')
    op.drop_index('ix_profesor_curso', table_name='profesores')
    op.drop_index('ix_profesor_activo', table_name='profesores')
    op.drop_index('ix_profesor_turno', table_name='profesores')
    op.drop_index('ix_guardias_zona_fecha', table_name='guardias')
    op.drop_index('ix_guardias_profesor_fecha', table_name='guardias')
    op.drop_index('ix_guardias_fecha', table_name='guardias')
    op.drop_index('ix_guardias_turno', table_name='guardias')
    op.drop_index('ix_guardias_curso_id', table_name='guardias')
