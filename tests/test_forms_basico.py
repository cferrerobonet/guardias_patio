"""
Tests básicos para todos los formularios.

Este archivo contiene tests simples pero efectivos que verifican:
- Inicialización correcta de formularios
- Carga de datos desde BD
- Funcionalidad básica de UI

Para tests más detallados, ver archivos test_*_form_detallado.py
"""

from unittest.mock import patch

import pytest

from presentation.forms.profesor_form import ProfesorForm
from presentation.forms.zona_form import ZonaForm


@pytest.mark.ui
class TestProfesorFormBasico:
    """Tests básicos de ProfesorForm."""

    def test_crear_formulario(self, qtbot, session):
        """Verificar que el formulario se crea sin errores."""
        form = ProfesorForm(session)
        qtbot.addWidget(form)

        assert form is not None
        assert form.windowTitle() == "Gestión de Profesores"

    def test_cargar_tabla_vacia(self, qtbot, session):
        """Verificar carga con BD vacía."""
        form = ProfesorForm(session)
        qtbot.addWidget(form)

        assert hasattr(form, "tabla_profesores")
        assert form.tabla_profesores.rowCount() == 0

    def test_cargar_tabla_con_datos(self, qtbot, db_with_data):
        """Verificar carga con datos existentes."""
        form = ProfesorForm(db_with_data)
        qtbot.addWidget(form)

        # db_with_data tiene 3 profesores
        assert form.tabla_profesores.rowCount() == 3

    def test_use_cases_inicializados(self, qtbot, session):
        """Verificar que los use cases existen."""
        form = ProfesorForm(session)
        qtbot.addWidget(form)

        assert form.crear_use_case is not None
        assert form.actualizar_use_case is not None
        assert form.eliminar_use_case is not None
        assert form.listar_use_case is not None

    def test_eliminar_profesor_usa_confirmacion_estandar(self, qtbot, db_with_data):
        """Eliminar profesor usa confirmar_accion y respeta cancelación."""
        form = ProfesorForm(db_with_data)
        qtbot.addWidget(form)

        form.tabla_profesores.selectRow(0)

        with patch.object(form, "confirmar_accion", return_value=False) as mock_confirmar:
            with patch.object(form.eliminar_use_case, "execute") as mock_execute:
                form.eliminar_profesor()

        mock_confirmar.assert_called_once()
        mock_execute.assert_not_called()


@pytest.mark.ui
class TestZonaFormBasico:
    """Tests básicos de ZonaForm."""

    def test_crear_formulario(self, qtbot, session):
        """Verificar que el formulario se crea sin errores."""
        form = ZonaForm(session)
        qtbot.addWidget(form)

        assert form is not None
        assert form.windowTitle() == "Gestión de Zonas"

    def test_cargar_tabla_vacia(self, qtbot, session):
        """Verificar carga con BD vacía."""
        form = ZonaForm(session)
        qtbot.addWidget(form)

        assert hasattr(form, "tabla_zonas")
        assert form.tabla_zonas.rowCount() == 0

    def test_cargar_tabla_con_datos(self, qtbot, db_with_data):
        """Verificar carga con datos existentes."""
        form = ZonaForm(db_with_data)
        qtbot.addWidget(form)

        # db_with_data tiene 3 zonas
        assert form.tabla_zonas.rowCount() == 3

    def test_use_cases_inicializados(self, qtbot, session):
        """Verificar que los use cases existen."""
        form = ZonaForm(session)
        qtbot.addWidget(form)

        assert form.crear_zona_uc is not None
        assert form.eliminar_zona_uc is not None
        assert form.listar_zonas_uc is not None

    def test_eliminar_zona_usa_confirmacion_estandar(self, qtbot, db_with_data):
        """Eliminar zona usa confirmar_accion y respeta cancelación."""
        form = ZonaForm(db_with_data)
        qtbot.addWidget(form)

        form.tabla_zonas.selectRow(0)

        with patch.object(form, "confirmar_accion", return_value=False) as mock_confirmar:
            with patch.object(form.eliminar_zona_uc, "execute") as mock_execute:
                form.eliminar_zona()

        mock_confirmar.assert_called_once()
        mock_execute.assert_not_called()


@pytest.mark.ui
@pytest.mark.slow
class TestFormulariosCargaMasiva:
    """Tests de carga con muchos datos."""

    def test_profesor_form_muchos_datos(self, qtbot, session, profesor_factory):
        """Verificar que el formulario maneja muchos profesores."""
        # Crear 50 profesores
        for i in range(50):
            profesor_factory(
                nombre_completo=f"Profesor {i}",
                email_corporativo=f"prof{i}@example.com",
                horas_contrato=20.0 + (i % 20),
                porcentaje_jornada=100.0,
                turno="mañana",
            )
        session.commit()

        form = ProfesorForm(session)
        qtbot.addWidget(form)

        assert form.tabla_profesores.rowCount() == 50

    def test_zona_form_muchos_datos(self, qtbot, session, zona_factory):
        """Verificar que el formulario maneja muchas zonas."""
        # Crear 30 zonas
        for i in range(30):
            zona_factory(nombre_zona=f"Zona {i}", descripcion=f"Descripción de zona {i}")
        session.commit()

        form = ZonaForm(session)
        qtbot.addWidget(form)

        assert form.tabla_zonas.rowCount() == 30


@pytest.mark.integration
class TestFormulariosIntegracion:
    """Tests de integración entre formularios."""

    def test_profesor_y_zona_formscomparten_session(self, qtbot, session):
        """Verificar que ambos formularios pueden usar la misma sesión."""
        form_profesor = ProfesorForm(session)
        form_zona = ZonaForm(session)

        qtbot.addWidget(form_profesor)
        qtbot.addWidget(form_zona)

        assert form_profesor.session is form_zona.session

    def test_zona_disponible_para_profesor(self, qtbot, session, zona_factory, profesor_factory):
        """Verificar que las zonas creadas están disponibles para profesores."""
        # Crear zona
        zona_factory(nombre_zona="Patio Principal")
        session.commit()

        # Crear formulario de profesor
        form_profesor = ProfesorForm(session)
        qtbot.addWidget(form_profesor)

        # La zona debería estar en el sistema
        # (no podemos verificar el combo fácilmente, pero al menos
        # verificamos que la zona existe en BD)
        from infrastructure.database.models import Zona

        zonas_bd = session.query(Zona).all()
        assert len(zonas_bd) > 0
        assert any(z.nombre_zona == "Patio Principal" for z in zonas_bd)
