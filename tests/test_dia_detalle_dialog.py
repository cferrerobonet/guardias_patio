"""
Tests para DiaDetalleDialog - ventana de detalle de guardias del día.
"""

from datetime import date

import pytest
from models.models import Ausencia, Configuracion, Guardia, Profesor, Zona
from presentation.dialogs.dia_detalle_dialog import DiaDetalleDialog
from PyQt6.QtWidgets import QApplication


@pytest.fixture
def qapp():
    """Fixture de QApplication para tests de Qt."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def profesor_basico(session):
    """Crear profesor básico para tests."""
    config = Configuracion(
        nombre_centro="Test Centro",
        curso_academico="2024/2025",
        fecha_inicio=date(2024, 9, 1),
        fecha_fin=date(2025, 6, 30),
    )
    session.add(config)
    session.flush()

    profesor = Profesor(
        nombre="García, Juan",
        email="juan@test.com",
        horas_contrato=25.0,
        es_tutor=False,
        turno="Mañana",
        porcentaje_jornada=100,
        configuracion_id=config.id,
    )
    session.add(profesor)
    session.commit()
    return profesor


@pytest.fixture
def zona_basica(session):
    """Crear zona básica para tests."""
    config = session.query(Configuracion).first()
    if not config:
        config = Configuracion(
            nombre_centro="Test Centro",
            curso_academico="2024/2025",
            fecha_inicio=date(2024, 9, 1),
            fecha_fin=date(2025, 6, 30),
        )
        session.add(config)
        session.flush()

    zona = Zona(
        nombre="Patio Principal",
        descripcion="Zona principal del centro",
        configuracion_id=config.id,
    )
    session.add(zona)
    session.commit()
    return zona


class TestDiaDetalleDialogBasico:
    """Tests básicos de creación del diálogo."""

    def test_crear_dialogo_sin_datos(self, qapp):
        """Crear diálogo sin guardias, ausencias ni sustituciones."""
        fecha = date(2024, 11, 8)
        dialog = DiaDetalleDialog(
            fecha=fecha, guardias=[], ausencias=[], sustituciones=[], parent=None
        )

        assert dialog is not None
        assert dialog.fecha == fecha
        assert dialog.guardias == []
        assert dialog.ausencias == []
        assert dialog.sustituciones == []

    def test_titulo_dialogo_correcto(self, qapp):
        """Verificar que el título del diálogo contiene la fecha."""
        fecha = date(2024, 11, 8)
        dialog = DiaDetalleDialog(
            fecha=fecha, guardias=[], ausencias=[], sustituciones=[], parent=None
        )

        titulo = dialog.windowTitle()
        assert "08/11/2024" in titulo

    def test_minimo_size_establecido(self, qapp):
        """Verificar que el diálogo tiene un tamaño mínimo."""
        dialog = DiaDetalleDialog(
            fecha=date(2024, 11, 8),
            guardias=[],
            ausencias=[],
            sustituciones=[],
            parent=None,
        )

        assert dialog.minimumWidth() >= 600
        assert dialog.minimumHeight() >= 500


class TestDiaDetalleDialogConDatos:
    """Tests con datos reales de guardias, ausencias y sustituciones."""

    def test_crear_dialogo_con_guardias(self, qapp, session, profesor_basico, zona_basica):
        """Crear diálogo con guardias."""
        fecha_test = date(2024, 11, 8)

        guardia = Guardia(
            fecha=fecha_test,
            numero_recreo=1,
            profesor_id=profesor_basico.id,
            zona_id=zona_basica.id,
            configuracion_id=profesor_basico.configuracion_id,
        )
        session.add(guardia)
        session.commit()

        dialog = DiaDetalleDialog(
            fecha=fecha_test,
            guardias=[guardia],
            ausencias=[],
            sustituciones=[],
            parent=None,
        )

        assert len(dialog.guardias) == 1
        assert dialog.guardias[0].profesor.nombre == "García, Juan"

    def test_crear_dialogo_con_ausencias(self, qapp, session, profesor_basico):
        """Crear diálogo con ausencias."""
        fecha_test = date(2024, 11, 8)

        ausencia = Ausencia(
            profesor_id=profesor_basico.id,
            fecha_inicio=fecha_test,
            fecha_fin=fecha_test,
            motivo="Test ausencia",
            configuracion_id=profesor_basico.configuracion_id,
        )
        session.add(ausencia)
        session.commit()

        dialog = DiaDetalleDialog(
            fecha=fecha_test,
            guardias=[],
            ausencias=[ausencia],
            sustituciones=[],
            parent=None,
        )

        assert len(dialog.ausencias) == 1
        assert dialog.ausencias[0].motivo == "Test ausencia"

    def test_crear_dialogo_con_sustituciones(
        self, qapp, session, profesor_basico, zona_basica
    ):
        """Crear diálogo con sustituciones."""
        fecha_test = date(2024, 11, 8)

        sustitucion = Guardia(
            fecha=fecha_test,
            numero_recreo=1,
            profesor_id=profesor_basico.id,
            zona_id=zona_basica.id,
            configuracion_id=profesor_basico.configuracion_id,
            es_sustitucion=True,
        )
        session.add(sustitucion)
        session.commit()

        dialog = DiaDetalleDialog(
            fecha=fecha_test,
            guardias=[],
            ausencias=[],
            sustituciones=[sustitucion],
            parent=None,
        )

        assert len(dialog.sustituciones) == 1


class TestDiaDetalleDialogResumen:
    """Tests para el resumen estadístico del diálogo."""

    def test_resumen_con_multiples_guardias(
        self, qapp, session, profesor_basico, zona_basica
    ):
        """Verificar resumen con múltiples guardias."""
        fecha_test = date(2024, 11, 8)

        # Crear 3 guardias en diferentes recreos
        guardias = []
        for recreo in [1, 2, 3]:
            guardia = Guardia(
                fecha=fecha_test,
                numero_recreo=recreo,
                profesor_id=profesor_basico.id,
                zona_id=zona_basica.id,
                configuracion_id=profesor_basico.configuracion_id,
            )
            session.add(guardia)
            guardias.append(guardia)

        session.commit()

        dialog = DiaDetalleDialog(
            fecha=fecha_test,
            guardias=guardias,
            ausencias=[],
            sustituciones=[],
            parent=None,
        )

        # Verificar que se creó el resumen
        assert len(dialog.guardias) == 3


class TestDiaDetalleDialogIntegracion:
    """Tests de integración del diálogo completo."""

    def test_dialogo_completo_con_todos_los_datos(
        self, qapp, session, profesor_basico, zona_basica
    ):
        """Crear diálogo con guardias, ausencias y sustituciones."""
        fecha_test = date(2024, 11, 8)

        # Crear guardia
        guardia = Guardia(
            fecha=fecha_test,
            numero_recreo=1,
            profesor_id=profesor_basico.id,
            zona_id=zona_basica.id,
            configuracion_id=profesor_basico.configuracion_id,
        )

        # Crear ausencia
        ausencia = Ausencia(
            profesor_id=profesor_basico.id,
            fecha_inicio=fecha_test,
            fecha_fin=fecha_test,
            motivo="Test completo",
            configuracion_id=profesor_basico.configuracion_id,
        )

        # Crear sustitución
        sustitucion = Guardia(
            fecha=fecha_test,
            numero_recreo=2,
            profesor_id=profesor_basico.id,
            zona_id=zona_basica.id,
            configuracion_id=profesor_basico.configuracion_id,
            es_sustitucion=True,
        )

        session.add_all([guardia, ausencia, sustitucion])
        session.commit()

        dialog = DiaDetalleDialog(
            fecha=fecha_test,
            guardias=[guardia],
            ausencias=[ausencia],
            sustituciones=[sustitucion],
            parent=None,
        )

        assert len(dialog.guardias) == 1
        assert len(dialog.ausencias) == 1
        assert len(dialog.sustituciones) == 1
