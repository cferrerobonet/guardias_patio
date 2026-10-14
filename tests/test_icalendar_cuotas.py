"""
Tests para ICalendarService y CalcularCuotasUseCase.
"""

import sys
import tempfile
from datetime import date, time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from infrastructure.database.models import Base, Configuracion, Guardia, Profesor, Zona
from services.icalendar_service import ICalendarService


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def engine_ical():
    eng = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture
def session_ical(engine_ical) -> Session:
    conn = engine_ical.connect()
    txn = conn.begin()
    sess = sessionmaker(bind=conn)()
    yield sess
    sess.rollback()
    sess.close()
    if txn.is_active:
        txn.rollback()
    conn.close()


@pytest.fixture
def datos_ical(session_ical: Session):
    """Sesión con datos mínimos para tests iCalendar."""
    config = Configuracion(
        anio_inicio_curso=2025,
        fecha_inicio_curso=date(2025, 9, 1),
        fecha_fin_curso=date(2026, 6, 30),
        hora_recreo1_manana=time(10, 30),
        hora_recreo2_manana=time(12, 30),
    )
    session_ical.add(config)

    prof = Profesor(
        nombre_completo="GARCÍA LÓPEZ, JUAN",
        activo=True,
        turno="mañana",
        horas_contrato=25.0,
        porcentaje_jornada=100.0,
    )
    zona = Zona(nombre_zona="Patio Principal")
    session_ical.add_all([prof, zona])
    session_ical.flush()

    guardia = Guardia(
        profesor_id=prof.id,
        zona_id=zona.id,
        fecha=date(2025, 10, 15),
        turno="mañana",
        recreo=1,
    )
    session_ical.add(guardia)
    session_ical.flush()

    return session_ical, prof, config


# ─────────────────────────────────────────────────────────────────────────────
# ICalendarService — métodos estáticos (sin BD)
# ─────────────────────────────────────────────────────────────────────────────


class TestICalendarServiceEstaticos:
    def test_formatear_datetime_ical(self):
        from datetime import datetime

        dt = datetime(2025, 10, 15, 10, 30, 0)
        resultado = ICalendarService._formatear_datetime_ical(dt)
        assert resultado == "20251015T103000"

    def test_escapar_texto_ical_basico(self):
        texto = "Guardia, patio; especial\nnueva línea"
        resultado = ICalendarService._escapar_texto_ical(texto)
        assert "\\," in resultado
        assert "\\;" in resultado
        assert "\\n" in resultado

    def test_escapar_texto_ical_sin_especiales(self):
        assert ICalendarService._escapar_texto_ical("Normal") == "Normal"

    def test_obtener_nombre_archivo_ics(self):
        nombre = ICalendarService.obtener_nombre_archivo_ics("GARCÍA LÓPEZ, JUAN")
        assert nombre.startswith("guardias_")
        assert nombre.endswith(".ics")
        assert " " not in nombre

    def test_obtener_nombre_archivo_ics_normaliza_tildes(self):
        nombre = ICalendarService.obtener_nombre_archivo_ics("MARTÍNEZ, JOSÉ")
        assert "í" not in nombre
        assert "É" not in nombre.upper() or "e" in nombre.lower()

    def test_obtener_hora_recreo_manana_1(self):
        config = MagicMock()
        config.hora_recreo1_manana = time(10, 30)
        config.hora_recreo2_manana = time(12, 30)
        hora = ICalendarService._obtener_hora_recreo(config, "mañana", 1)
        assert hora == time(10, 30)

    def test_obtener_hora_recreo_manana_2(self):
        config = MagicMock()
        config.hora_recreo1_manana = time(10, 30)
        config.hora_recreo2_manana = time(12, 30)
        hora = ICalendarService._obtener_hora_recreo(config, "mañana", 2)
        assert hora == time(12, 30)

    def test_obtener_hora_recreo_tarde_1(self):
        config = MagicMock()
        config.hora_recreo1_tarde = time(16, 30)
        hora = ICalendarService._obtener_hora_recreo(config, "tarde", 1)
        assert hora == time(16, 30)

    def test_obtener_hora_recreo_no_configurado_devuelve_none(self):
        config = MagicMock()
        config.hora_recreo1_manana = None
        hora = ICalendarService._obtener_hora_recreo(config, "mañana", 1)
        assert hora is None

    def test_obtener_hora_recreo_turno_desconocido(self):
        config = MagicMock()
        hora = ICalendarService._obtener_hora_recreo(config, "nocturno", 1)
        assert hora is None


# ─────────────────────────────────────────────────────────────────────────────
# ICalendarService — generar_icalendar_profesor
# ─────────────────────────────────────────────────────────────────────────────


class TestICalendarServiceGenerar:
    def test_genera_archivo_ics(self, datos_ical):
        session, prof, _ = datos_ical
        with tempfile.NamedTemporaryFile(suffix=".ics", delete=False) as f:
            ruta = f.name

        result = ICalendarService.generar_icalendar_profesor(session, prof.id, ruta)
        assert result is True
        contenido = Path(ruta).read_text(encoding="utf-8")
        assert "BEGIN:VCALENDAR" in contenido
        assert "BEGIN:VEVENT" in contenido
        assert "END:VCALENDAR" in contenido
        Path(ruta).unlink(missing_ok=True)

    def test_devuelve_false_si_profesor_no_existe(self, datos_ical):
        session, _, _ = datos_ical
        with tempfile.NamedTemporaryFile(suffix=".ics", delete=False) as f:
            ruta = f.name
        result = ICalendarService.generar_icalendar_profesor(session, 99999, ruta)
        assert result is False
        Path(ruta).unlink(missing_ok=True)

    def test_genera_archivo_sin_guardias(self, session_ical):
        """Genera ICS para un profesor sin guardias — debe funcionar sin crash."""
        prof = Profesor(
            nombre_completo="SIN GUARDIAS, PROF",
            activo=True,
            turno="tarde",
            horas_contrato=20.0,
            porcentaje_jornada=80.0,
        )
        session_ical.add(prof)
        session_ical.flush()

        with tempfile.NamedTemporaryFile(suffix=".ics", delete=False) as f:
            ruta = f.name

        result = ICalendarService.generar_icalendar_profesor(session_ical, prof.id, ruta)
        # Sin configuración → devuelve False
        assert isinstance(result, bool)
        Path(ruta).unlink(missing_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# CalcularCuotasUseCase
# ─────────────────────────────────────────────────────────────────────────────


class TestCalcularCuotasUseCase:
    @pytest.fixture
    def session_cuotas(self, engine_ical) -> Session:
        conn = engine_ical.connect()
        txn = conn.begin()
        sess = sessionmaker(bind=conn)()
        yield sess
        sess.rollback()
        sess.close()
        if txn.is_active:
            txn.rollback()
        conn.close()

    def test_falla_si_config_no_existe(self, session_cuotas):
        from application.use_cases.calcular_cuotas_use_case import CalcularCuotasUseCase
        from application.dtos.domain_services_dtos import CalcularCuotasRequest

        uc = CalcularCuotasUseCase(session_cuotas)
        req = CalcularCuotasRequest(configuracion_id=999, solo_activos=True)
        result = uc.execute(req)
        assert result.exitoso is False
        assert "no encontrada" in result.mensaje.lower()

    def test_falla_si_no_hay_profesores(self, session_cuotas):
        from application.use_cases.calcular_cuotas_use_case import CalcularCuotasUseCase
        from application.dtos.domain_services_dtos import CalcularCuotasRequest

        config = Configuracion(
            anio_inicio_curso=2025,
            fecha_inicio_curso=date(2025, 9, 1),
            fecha_fin_curso=date(2026, 6, 30),
            hora_recreo1_manana=time(10, 30),
            hora_recreo2_manana=time(12, 0),
            hora_recreo1_tarde=time(16, 30),
            hora_recreo2_tarde=time(18, 0),
        )
        session_cuotas.add(config)
        session_cuotas.flush()

        uc = CalcularCuotasUseCase(session_cuotas)
        req = CalcularCuotasRequest(configuracion_id=config.id, solo_activos=True)
        result = uc.execute(req)
        assert result.exitoso is False
        assert "profesores" in result.mensaje.lower()
