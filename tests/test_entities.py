"""
Tests para las entidades del dominio:
- ProfesorEntity
- ZonaEntity
- GuardiaEntity

Comprueban construcción, igualdad por valor y reglas de validación comunes.
"""
from datetime import date

import pytest

from core.exceptions import GuardiaInvalidaError, ValidationError
from src.domain.entities import GuardiaEntity, ProfesorEntity, ZonaEntity
from src.domain.value_objects import Email, HorasContrato, Turno, TurnoEnum, ZonaPreferida


class TestProfesorEntity:
    def test_construccion_y_igualdad(self):
        p1 = ProfesorEntity(
            id=1,
            nombre_completo="Ana López",
            email_corporativo=Email("ana@colegio.com"),
            horas_contrato=HorasContrato(20.0),
            porcentaje_jornada=100.0,
            turno=Turno(TurnoEnum.MANANA),
            zona_preferida=ZonaPreferida.sin_preferencia(),
        )
        p2 = ProfesorEntity(
            id=1,
            nombre_completo="Ana López",
            email_corporativo=Email("ana@colegio.com"),
            horas_contrato=HorasContrato(20.0),
            porcentaje_jornada=100.0,
            turno=Turno(TurnoEnum.MANANA),
            zona_preferida=ZonaPreferida.sin_preferencia(),
        )
        assert p1 == p2

    def test_horas_incompatibles_con_turno(self):
        # Turno mañana no debe llevar horas específicas
        with pytest.raises(ValidationError):
            ProfesorEntity(
                id=2,
                nombre_completo="Juan Pérez",
                email_corporativo=Email("juan@colegio.com"),
                horas_contrato=HorasContrato(30.0),
                porcentaje_jornada=100.0,
                turno=Turno(TurnoEnum.MANANA, horas_manana=10.0),
                zona_preferida=ZonaPreferida.sin_preferencia(),
            )


class TestZonaEntity:
    def test_construccion_nombre_valido(self):
        z = ZonaEntity(id=1, nombre_zona="Patio Norte")
        assert z.nombre_zona == "Patio Norte"

    def test_nombre_vacio_no_raise(self):
        # Actualmente ZonaEntity permite nombre vacío; comprobamos propiedades
        z = ZonaEntity(id=2, nombre_zona="")
        assert z.nombre_zona == ""
        assert z.nombre_display == ""


class TestGuardiaEntity:
    def test_construccion_y_propiedades(self):
        g = GuardiaEntity(
            id=1,
            profesor_id=1,
            zona_id=1,
            fecha=date(2025, 10, 19),
            turno="mañana",
            recreo=2,
        )
        assert g.profesor_id == 1
        assert g.turno == "mañana"

    def test_recreo_invalido(self):
        # recreo debe ser > 0; 0 es inválido
        with pytest.raises(GuardiaInvalidaError):
            GuardiaEntity(
                id=2,
                profesor_id=1,
                zona_id=1,
                fecha=date(2025, 10, 19),
                turno="mañana",
                recreo=0,
            )
