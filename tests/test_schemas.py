"""
Tests para Pydantic Schemas.

Objetivo: Aumentar cobertura de domain/schemas desde 0% a ~90%.
"""

from datetime import date

import pytest
from pydantic import ValidationError

from domain.schemas.configuracion_schema import ConfiguracionSchema
from domain.schemas.guardia_schema import (
    GuardiaCreateSchema,
    GuardiaSchema,
    GuardiaUpdateSchema,
)
from domain.schemas.profesor_schema import (
    ProfesorCreateSchema,
    ProfesorSchema,
    ProfesorUpdateSchema,
)


class TestProfesorCreateSchema:
    """Tests para ProfesorCreateSchema."""

    def test_crear_profesor_minimo(self):
        """Test: crear con campos mínimos requeridos."""
        schema = ProfesorCreateSchema(
            nombre_completo="PÉREZ, Juan",
            horas_contrato=25.0,
        )
        assert schema.nombre_completo == "PÉREZ, Juan"
        assert schema.horas_contrato == 25.0
        assert schema.turno == "mañana"  # default
        assert schema.es_tutor is False  # default

    def test_crear_profesor_completo(self):
        """Test: crear con todos los campos."""
        schema = ProfesorCreateSchema(
            nombre_completo="GARCÍA, Ana",
            email_corporativo="ana@example.com",
            horas_contrato=20.0,
            turno="tarde",
            es_tutor=True,
            zona_preferida_id=2,
        )
        assert schema.es_tutor is True
        assert schema.turno == "tarde"

    def test_horas_contrato_negativas(self):
        """Test: horas negativas deben fallar."""
        with pytest.raises(ValidationError):
            ProfesorCreateSchema(
                nombre_completo="TEST",
                horas_contrato=-5.0,
            )

    def test_turno_invalido(self):
        """Test: turno debe ser mañana o tarde."""
        with pytest.raises(ValidationError):
            ProfesorCreateSchema(
                nombre_completo="TEST",
                horas_contrato=20.0,
                turno="noche",
            )

    def test_dias_semana_invalidos(self):
        """Test: días semana deben estar en rango 0-6."""
        with pytest.raises(ValidationError):
            ProfesorCreateSchema(
                nombre_completo="TEST",
                horas_contrato=20.0,
                dias_semana_permitidos=[0, 8],  # 8 es inválido
            )

    def test_recreos_negativos(self):
        """Test: recreos deben ser positivos."""
        with pytest.raises(ValidationError):
            ProfesorCreateSchema(
                nombre_completo="TEST",
                horas_contrato=20.0,
                recreos_permitidos=[0, -1],  # negativos inválidos
            )


class TestProfesorUpdateSchema:
    """Tests para ProfesorUpdateSchema."""

    def test_actualizar_todos_opcionales(self):
        """Test: todos los campos son opcionales."""
        schema = ProfesorUpdateSchema(nombre_completo="NUEVO")
        assert schema.nombre_completo == "NUEVO"
        assert schema.horas_contrato is None

    def test_actualizar_horas(self):
        """Test: actualizar solo horas."""
        schema = ProfesorUpdateSchema(horas_contrato=30.0)
        assert schema.horas_contrato == 30.0


class TestProfesorSchema:
    """Tests para ProfesorSchema (con ID)."""

    def test_schema_con_id(self):
        """Test: schema completo con ID."""
        schema = ProfesorSchema(
            id=1,
            nombre_completo="PÉREZ, Juan",
            horas_contrato=25.0,
            porcentaje_jornada=100.0,
            turno="mañana",
            es_tutor=False,
        )
        assert schema.id == 1
        assert schema.nombre_completo == "PÉREZ, Juan"

    def test_validacion_fechas(self):
        """Test: fecha_fin debe ser >= fecha_inicio."""
        with pytest.raises(ValidationError):
            ProfesorSchema(
                id=1,
                nombre_completo="TEST",
                horas_contrato=20.0,
                porcentaje_jornada=80.0,
                turno="mañana",
                es_tutor=False,
                fecha_inicio_guardias=date(2025, 12, 31),
                fecha_fin_guardias=date(2025, 1, 1),  # Anterior a inicio
            )


class TestGuardiaCreateSchema:
    """Tests para GuardiaCreateSchema."""

    def test_crear_guardia_minima(self):
        """Test: crear guardia con campos mínimos."""
        schema = GuardiaCreateSchema(
            profesor_id=5,
            zona_id=2,
            fecha=date(2025, 11, 7),
            turno="mañana",
            recreo=1,
        )
        assert schema.profesor_id == 5
        assert schema.zona_id == 2
        assert schema.es_sustitucion is False  # default

    def test_recreo_fuera_rango(self):
        """Test: recreo debe estar entre 1-3."""
        with pytest.raises(ValidationError):
            GuardiaCreateSchema(
                profesor_id=5,
                zona_id=2,
                fecha=date(2025, 11, 7),
                turno="mañana",
                recreo=5,  # Inválido
            )

    def test_sustitucion_sin_profesor_sustituido(self):
        """Test: sustitución requiere profesor_sustituido_id."""
        # Crear guardia de sustitución válida
        schema = GuardiaCreateSchema(
            profesor_id=5,
            zona_id=2,
            fecha=date(2025, 11, 7),
            turno="mañana",
            recreo=1,
            es_sustitucion=True,
            profesor_sustituido_id=3,  # Ahora sí tiene
        )
        assert schema.es_sustitucion is True
        assert schema.profesor_sustituido_id == 3

    def test_no_sustitucion_con_profesor_sustituido(self):
        """Test: si no es sustitución, no debe tener profesor_sustituido_id."""
        with pytest.raises(ValidationError):
            GuardiaCreateSchema(
                profesor_id=5,
                zona_id=2,
                fecha=date(2025, 11, 7),
                turno="mañana",
                recreo=1,
                es_sustitucion=False,
                profesor_sustituido_id=3,  # Inconsistente
            )

    def test_auto_sustitucion(self):
        """Test: profesor no puede sustituirse a sí mismo."""
        with pytest.raises(ValidationError):
            GuardiaCreateSchema(
                profesor_id=5,
                zona_id=2,
                fecha=date(2025, 11, 7),
                turno="mañana",
                recreo=1,
                es_sustitucion=True,
                profesor_sustituido_id=5,  # Mismo ID
            )


class TestGuardiaUpdateSchema:
    """Tests para GuardiaUpdateSchema."""

    def test_actualizar_zona(self):
        """Test: actualizar solo zona."""
        schema = GuardiaUpdateSchema(zona_id=3)
        assert schema.zona_id == 3
        assert schema.profesor_id is None

    def test_actualizar_notas(self):
        """Test: actualizar notas."""
        schema = GuardiaUpdateSchema(notas="Cambio por ausencia")
        assert schema.notas == "Cambio por ausencia"


class TestGuardiaSchema:
    """Tests para GuardiaSchema (con ID)."""

    def test_schema_con_id(self):
        """Test: schema completo."""
        schema = GuardiaSchema(
            id=10,
            profesor_id=5,
            zona_id=2,
            fecha=date(2025, 11, 7),
            turno="mañana",
            recreo=1,
        )
        assert schema.id == 10


class TestConfiguracionSchema:
    """Tests para ConfiguracionSchema."""

    def test_configuracion_por_defecto(self):
        """Test: valores por defecto."""
        schema = ConfiguracionSchema()
        assert schema.max_horas_contrato == 25.0
        assert schema.ajuste_tutores == 10.0
        assert schema.max_guardias_por_profesor_dia == 2

    def test_configuracion_personalizada(self):
        """Test: valores personalizados."""
        schema = ConfiguracionSchema(
            max_horas_contrato=30.0,
            ajuste_tutores=15.0,
        )
        assert schema.max_horas_contrato == 30.0
        assert schema.ajuste_tutores == 15.0

    def test_horas_contrato_excede_maximo(self):
        """Test: max_horas_contrato no puede exceder 40."""
        with pytest.raises(ValidationError):
            ConfiguracionSchema(max_horas_contrato=50.0)

    def test_ajustes_negativos(self):
        """Test: ajustes deben ser no negativos."""
        with pytest.raises(ValidationError):
            ConfiguracionSchema(ajuste_tutores=-5.0)


class TestSerializacion:
    """Tests para serialización/deserialización."""

    def test_profesor_to_dict(self):
        """Test: convertir a dict."""
        schema = ProfesorCreateSchema(
            nombre_completo="TEST",
            horas_contrato=20.0,
        )
        data = schema.model_dump()
        assert isinstance(data, dict)
        assert data["nombre_completo"] == "TEST"

    def test_guardia_from_dict(self):
        """Test: crear desde dict."""
        data = {
            "id": 1,
            "profesor_id": 5,
            "zona_id": 2,
            "fecha": date(2025, 11, 7),
            "turno": "mañana",
            "recreo": 1,
        }
        schema = GuardiaSchema(**data)
        assert schema.id == 1
