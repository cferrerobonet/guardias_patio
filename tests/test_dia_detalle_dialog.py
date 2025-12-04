"""
Tests para DiaDetalleDialog - ventana de detalle de guardias del día.
"""

from datetime import date

from infrastructure.database.models import Ausencia, Guardia
from presentation.dialogs.dia_detalle_dialog import DiaDetalleDialog


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

    def test_crear_dialogo_con_guardias(self, qapp, session, profesor_factory, zona_factory):
        """Crear diálogo con guardias."""
        fecha_test = date(2024, 11, 8)

        # Crear profesor y zona usando factories
        profesor = profesor_factory(nombre_completo="García, Juan")
        zona = zona_factory(nombre_zona="Patio Principal")

        # Crear guardia con los campos correctos
        guardia = Guardia(
            fecha=fecha_test,
            recreo=1,  # Correcto: 'recreo' no 'numero_recreo'
            turno="mañana",
            profesor_id=profesor.id,
            zona_id=zona.id,
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
        assert dialog.guardias[0].profesor.nombre_completo == "García, Juan"

    def test_crear_dialogo_con_ausencias(self, qapp, session, profesor_factory):
        """Crear diálogo con ausencias."""
        fecha_test = date(2024, 11, 8)

        # Crear profesor usando factory
        profesor = profesor_factory(nombre_completo="López, Ana")

        # Crear ausencia con los campos correctos
        ausencia = Ausencia(
            profesor_id=profesor.id,
            fecha_inicio=fecha_test,
            fecha_fin=fecha_test,
            tipo="permiso",
            motivo="Test ausencia",
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

    def test_crear_dialogo_con_sustituciones(self, qapp, session, profesor_factory, zona_factory):
        """Crear diálogo con sustituciones."""
        fecha_test = date(2024, 11, 8)

        # Crear profesor y zona usando factories
        profesor = profesor_factory(nombre_completo="Martínez, Carlos")
        zona = zona_factory(nombre_zona="Zona Deportiva")

        # Crear sustitución (es una guardia normal, se identifica por la lista donde se pasa)
        sustitucion = Guardia(
            fecha=fecha_test,
            recreo=1,
            turno="mañana",
            profesor_id=profesor.id,
            zona_id=zona.id,
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

    def test_resumen_con_multiples_guardias(self, qapp, session, profesor_factory, zona_factory):
        """Verificar resumen con múltiples guardias."""
        fecha_test = date(2024, 11, 8)

        # Crear profesor y zona usando factories
        profesor = profesor_factory(nombre_completo="Pérez, Luis")
        zona = zona_factory(nombre_zona="Cafetería")

        # Crear 3 guardias en diferentes recreos
        guardias = []
        for recreo in [1, 2]:
            guardia = Guardia(
                fecha=fecha_test,
                recreo=recreo,
                turno="mañana",
                profesor_id=profesor.id,
                zona_id=zona.id,
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
        assert len(dialog.guardias) == 2


class TestDiaDetalleDialogIntegracion:
    """Tests de integración del diálogo completo."""

    def test_dialogo_completo_con_todos_los_datos(
        self, qapp, session, profesor_factory, zona_factory
    ):
        """Crear diálogo con guardias, ausencias y sustituciones."""
        fecha_test = date(2024, 11, 8)

        # Crear profesor y zona usando factories
        profesor = profesor_factory(nombre_completo="González, María")
        zona = zona_factory(nombre_zona="Biblioteca")

        # Crear guardia
        guardia = Guardia(
            fecha=fecha_test,
            recreo=1,
            turno="mañana",
            profesor_id=profesor.id,
            zona_id=zona.id,
        )

        # Crear ausencia
        ausencia = Ausencia(
            profesor_id=profesor.id,
            fecha_inicio=fecha_test,
            fecha_fin=fecha_test,
            tipo="otros",
            motivo="Test completo",
        )

        # Crear sustitución (es una guardia normal, se identifica por la lista donde se pasa)
        sustitucion = Guardia(
            fecha=fecha_test,
            recreo=2,
            turno="mañana",
            profesor_id=profesor.id,
            zona_id=zona.id,
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
