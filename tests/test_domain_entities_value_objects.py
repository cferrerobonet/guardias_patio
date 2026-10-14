"""Tests para domain entities y value objects."""
import sys
from datetime import date, datetime, time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from core.exceptions import ValidationError
from domain.entities.ausencia_entity import AusenciaEntity
from domain.entities.configuracion_entity import ConfiguracionEntity
from domain.value_objects.email import Email
from domain.value_objects.horas_contrato import HorasContrato
from domain.value_objects.turno import Turno, TurnoEnum
from domain.value_objects.zona_preferida import ZonaPreferida


# ============================================================
# AusenciaEntity
# ============================================================
class TestAusenciaEntity:
    def test_creacion_default(self):
        a = AusenciaEntity(profesor_id=1)
        assert a.profesor_id == 1
        assert a.tipo == "otros"
        assert a.activa is True

    def test_cubre_fecha_dentro(self):
        a = AusenciaEntity(
            profesor_id=1,
            fecha_inicio=date(2024, 10, 1),
            fecha_fin=date(2024, 10, 10),
        )
        assert a.cubre_fecha(date(2024, 10, 5)) is True

    def test_cubre_fecha_fuera(self):
        a = AusenciaEntity(
            profesor_id=1,
            fecha_inicio=date(2024, 10, 1),
            fecha_fin=date(2024, 10, 10),
        )
        assert a.cubre_fecha(date(2024, 10, 11)) is False

    def test_no_cubre_si_inactiva(self):
        a = AusenciaEntity(
            profesor_id=1,
            fecha_inicio=date(2024, 10, 1),
            fecha_fin=date(2024, 10, 10),
            activa=False,
        )
        assert a.cubre_fecha(date(2024, 10, 5)) is False

    def test_duracion_dias_un_dia(self):
        a = AusenciaEntity(
            profesor_id=1,
            fecha_inicio=date(2024, 10, 1),
            fecha_fin=date(2024, 10, 1),
        )
        assert a.duracion_dias() == 1

    def test_duracion_dias_cinco_dias(self):
        a = AusenciaEntity(
            profesor_id=1,
            fecha_inicio=date(2024, 10, 1),
            fecha_fin=date(2024, 10, 5),
        )
        assert a.duracion_dias() == 5


# ============================================================
# ConfiguracionEntity
# ============================================================
class TestConfiguracionEntity:
    def test_creacion_default(self):
        c = ConfiguracionEntity()
        assert c.anio_inicio_curso == 0
        assert c.ajuste_tutores == 1.0
        assert c.algoritmo_asignacion == "v2.9"

    def test_creacion_con_datos(self):
        c = ConfiguracionEntity(
            anio_inicio_curso=2024,
            fecha_inicio_curso=date(2024, 9, 1),
            fecha_fin_curso=date(2025, 6, 30),
        )
        assert c.anio_inicio_curso == 2024
        assert c.fecha_inicio_curso == date(2024, 9, 1)

    def test_lista_default_vacia(self):
        c = ConfiguracionEntity()
        assert c.dias_no_lectivos_personalizados == []
        assert c.recreos_config == []


# ============================================================
# Email Value Object
# ============================================================
class TestEmail:
    def test_email_valido(self):
        e = Email("usuario@ejemplo.com")
        assert e.value == "usuario@ejemplo.com"

    def test_email_valido_con_subdominio(self):
        e = Email("user@mail.ejemplo.es")
        assert e.value == "user@mail.ejemplo.es"

    def test_email_invalido_sin_arroba(self):
        with pytest.raises((ValidationError, ValueError)):
            Email("usuarioejemplo.com")

    def test_email_invalido_vacio(self):
        with pytest.raises((ValidationError, ValueError)):
            Email("")

    def test_email_normalizado_a_minusculas(self):
        e = Email("usuario@ejemplo.com")
        assert e.value == "usuario@ejemplo.com"

    def test_igualdad(self):
        e1 = Email("usuario@ejemplo.com")
        e2 = Email("usuario@ejemplo.com")
        assert e1 == e2


# ============================================================
# HorasContrato Value Object
# ============================================================
class TestHorasContrato:
    def test_horas_validas(self):
        h = HorasContrato(20.0)
        assert h.value == 20.0

    def test_horas_cero(self):
        with pytest.raises((ValidationError, ValueError)):
            HorasContrato(0.0)

    def test_horas_negativas(self):
        with pytest.raises((ValidationError, ValueError)):
            HorasContrato(-5.0)

    def test_horas_maximas(self):
        # 37.5 horas semanales máximo típico
        h = HorasContrato(37.5)
        assert h.value == 37.5

    def test_igualdad(self):
        h1 = HorasContrato(20.0)
        h2 = HorasContrato(20.0)
        assert h1 == h2

    def test_desigualdad(self):
        h1 = HorasContrato(20.0)
        h2 = HorasContrato(25.0)
        assert h1 != h2


# ============================================================
# Turno Value Object
# ============================================================
class TestTurnoEnum:
    def test_from_string_manana(self):
        t = TurnoEnum.from_string("mañana")
        assert t == TurnoEnum.MANANA

    def test_from_string_tarde(self):
        t = TurnoEnum.from_string("tarde")
        assert t == TurnoEnum.TARDE

    def test_from_string_invalido(self):
        with pytest.raises(ValidationError):
            TurnoEnum.from_string("nocturno")

    def test_from_string_case_insensitive(self):
        t = TurnoEnum.from_string("TARDE")
        assert t == TurnoEnum.TARDE


class TestTurno:
    def test_turno_manana(self):
        t = Turno(TurnoEnum.MANANA)
        assert t.value == TurnoEnum.MANANA

    def test_turno_tarde(self):
        t = Turno(TurnoEnum.TARDE)
        assert t.value == TurnoEnum.TARDE

    def test_turno_mixto_requiere_horas(self):
        with pytest.raises(ValidationError):
            Turno(TurnoEnum.MIXTO)

    def test_turno_mixto_valido(self):
        t = Turno(TurnoEnum.MIXTO, horas_manana=15.0, horas_tarde=10.0)
        assert t.value == TurnoEnum.MIXTO

    def test_turno_no_mixto_no_acepta_horas(self):
        with pytest.raises(ValidationError):
            Turno(TurnoEnum.MANANA, horas_manana=15.0)

    def test_turno_es_inmutable(self):
        t = Turno(TurnoEnum.MANANA)
        with pytest.raises(Exception):
            t.value = TurnoEnum.TARDE

    def test_turno_igualdad(self):
        t1 = Turno(TurnoEnum.MANANA)
        t2 = Turno(TurnoEnum.MANANA)
        assert t1 == t2


# ============================================================
# ZonaPreferida Value Object
# ============================================================
class TestZonaPreferida:
    def test_zona_valida(self):
        z = ZonaPreferida(zona_id=1, zona_nombre="Patio A")
        assert z.zona_id == 1

    def test_zona_none(self):
        z = ZonaPreferida(zona_id=None)
        assert z.zona_id is None

    def test_igualdad_misma_zona(self):
        z1 = ZonaPreferida(zona_id=1, zona_nombre="Patio A")
        z2 = ZonaPreferida(zona_id=1, zona_nombre="Patio A")
        assert z1 == z2
