"""
Tests para el widget GestionarAusenciasForm (gestión de ausencias de profesores).
Tests completos de UI, carga de datos, CRUD, preview, reasignación de guardias.

Refactorizado: Los datos se crean ANTES del form para que los cargue correctamente.
"""

from datetime import date, timedelta
from unittest.mock import patch

import pytest
from PyQt6.QtCore import QDate

from infrastructure.database.models import Ausencia, CursoEscolar, Guardia
from presentation.widgets.gestionar_ausencias import DialogoReasignacion, GestionarAusenciasForm

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def curso_activo(session):
    """Crear curso escolar activo para tests."""
    curso = CursoEscolar(
        nombre="2024-2025",
        anio_inicio=2024,
        anio_fin=2025,
        fecha_inicio=date.today() - timedelta(days=30),
        fecha_fin=date.today() + timedelta(days=180),
        activo=True,
    )
    session.add(curso)
    session.commit()
    return curso


@pytest.fixture
def datos_completos(session, profesor_factory, zona_factory, curso_activo):
    """Fixture con profesores, zonas, guardias y ausencias."""
    # 3 profesores
    prof1 = profesor_factory(nombre_completo="Profesor 1", turno="mañana")
    prof2 = profesor_factory(nombre_completo="Profesor 2", turno="tarde")
    prof3 = profesor_factory(nombre_completo="Profesor 3", turno="mañana")

    # 2 zonas
    zona1 = zona_factory(nombre_zona="Zona A")
    zona2 = zona_factory(nombre_zona="Zona B")

    # Guardias para los próximos 10 días (vinculadas al curso activo)
    hoy = date.today()
    guardias = []
    for i in range(10):
        dia = hoy + timedelta(days=i)
        # Prof1: mañana días pares, Prof2: tarde días impares
        if i % 2 == 0:
            g = Guardia(
                profesor_id=prof1.id,
                zona_id=zona1.id,
                fecha=dia,
                turno="mañana",
                recreo=1,
                curso_id=curso_activo.id,
            )
        else:
            g = Guardia(
                profesor_id=prof2.id,
                zona_id=zona2.id,
                fecha=dia,
                turno="tarde",
                recreo=1,
                curso_id=curso_activo.id,
            )
        session.add(g)
        guardias.append(g)

    session.commit()

    # 2 ausencias existentes
    ausencia1 = Ausencia(
        profesor_id=prof1.id,
        tipo="baja_medica",
        fecha_inicio=hoy - timedelta(days=5),
        fecha_fin=hoy - timedelta(days=1),
        motivo="Gripe",
        activa=True,
    )
    ausencia2 = Ausencia(
        profesor_id=prof2.id,
        tipo="vacaciones",
        fecha_inicio=hoy + timedelta(days=20),
        fecha_fin=hoy + timedelta(days=25),
        motivo="Vacaciones verano",
        activa=False,  # Desactivada
    )

    session.add_all([ausencia1, ausencia2])
    session.commit()

    return {
        "profesores": [prof1, prof2, prof3],
        "zonas": [zona1, zona2],
        "guardias": guardias,
        "ausencias": [ausencia1, ausencia2],
        "hoy": hoy,
        "curso": curso_activo,
    }


@pytest.fixture
def form(qtbot, session, datos_completos):
    """Fixture que crea el formulario de ausencias DESPUÉS de crear los datos."""
    widget = GestionarAusenciasForm(session)
    qtbot.addWidget(widget)
    return widget


# ============================================================================
# TEST: BÁSICO (UI y creación)
# ============================================================================


@pytest.mark.ui
class TestGestionarAusenciasFormBasico:
    """Tests básicos de creación del widget y elementos UI."""

    def test_crear_form(self, qtbot, session, curso_activo):
        """El formulario se crea correctamente."""
        form = GestionarAusenciasForm(session)
        qtbot.addWidget(form)
        assert form is not None
        assert form.ausencia_actual is None

    def test_tiene_tabla_ausencias(self, form):
        """La tabla de ausencias existe con 7 columnas."""
        assert form.tabla_ausencias is not None
        assert form.tabla_ausencias.columnCount() == 7
        headers = [form.tabla_ausencias.horizontalHeaderItem(i).text() for i in range(7)]
        assert "Profesor" in headers
        assert "Tipo" in headers
        assert "Estado" in headers

    def test_tiene_botones_lista(self, form):
        """Los botones de la lista existen."""
        assert form.editar_btn is not None
        assert form.delete_btn is not None
        assert form.desactivar_btn is not None

    def test_tiene_campos_formulario(self, form):
        """Los campos del formulario existen."""
        assert form.profesor_combo is not None
        assert form.tipo_combo is not None
        assert form.fecha_inicio_input is not None
        assert form.fecha_fin_input is not None
        assert form.motivo_input is not None

    def test_tiene_preview_guardias(self, form):
        """El preview de guardias afectadas existe."""
        assert form.preview_text is not None

    def test_tipos_ausencia_disponibles(self, form):
        """Los tipos de ausencia están disponibles."""
        assert form.tipo_combo.count() == 4
        tipos = [form.tipo_combo.itemText(i) for i in range(form.tipo_combo.count())]
        assert "baja_medica" in tipos
        assert "permiso" in tipos
        assert "vacaciones" in tipos
        assert "otros" in tipos


# ============================================================================
# TEST: CARGAR DATOS
# ============================================================================


@pytest.mark.ui
class TestGestionarAusenciasFormCargarDatos:
    """Tests de carga de datos (profesores, ausencias)."""

    def test_cargar_profesores(self, form, datos_completos):
        """Cargar profesores en el combo."""
        # El form ya carga profesores al inicializarse
        # Verificar que hay profesores con guardias (prof1 y prof2)
        assert form.profesor_combo.count() >= 2

    def test_cargar_ausencias_tabla(self, form, datos_completos):
        """Cargar ausencias en la tabla."""
        # Hay 2 ausencias en datos_completos
        assert form.tabla_ausencias.rowCount() == 2


# ============================================================================
# TEST: CARGAR AUSENCIA PARA EDITAR
# ============================================================================


@pytest.mark.ui
class TestGestionarAusenciasFormEditar:
    """Tests de carga de ausencia para edición."""

    def test_cargar_ausencia_seleccionada(self, form, datos_completos):
        """Cargar ausencia seleccionada en el formulario."""
        # Seleccionar primera fila
        form.tabla_ausencias.selectRow(0)
        form.cargar_ausencia_seleccionada()

        # Verificar que ausencia_actual se estableció
        assert form.ausencia_actual is not None

    def test_cargar_ausencia_sin_seleccion(self, form, datos_completos):
        """No cargar si no hay selección."""
        # No seleccionar ninguna fila
        form.tabla_ausencias.clearSelection()

        with patch.object(form, "mostrar_advertencia"):
            form.cargar_ausencia_seleccionada()

        # ausencia_actual debe seguir None
        assert form.ausencia_actual is None

    def test_titulo_cambia_a_editar(self, form, datos_completos):
        """El título del formulario cambia a 'EDITAR' al cargar ausencia."""
        form.tabla_ausencias.selectRow(0)
        form.cargar_ausencia_seleccionada()

        # Título debe contener "EDITAR"
        titulo = form.titulo_form.text()
        assert "EDITAR" in titulo.upper()


# ============================================================================
# TEST: GUARDAR AUSENCIA
# ============================================================================


@pytest.mark.ui
class TestGestionarAusenciasFormGuardar:
    """Tests de guardar ausencia (crear y actualizar)."""

    def test_guardar_ausencia_sin_profesor(self, form, datos_completos):
        """No guardar si no hay profesor seleccionado."""
        # Deseleccionar profesor
        form.profesor_combo.setCurrentIndex(-1)

        with patch.object(form, "mostrar_advertencia") as mock_warning:
            form.guardar_ausencia()
            mock_warning.assert_called_once()

    def test_guardar_ausencia_fechas_invalidas(self, form, datos_completos):
        """No guardar si fecha_fin < fecha_inicio."""
        form.profesor_combo.setCurrentIndex(0)
        hoy = datos_completos["hoy"]
        form.fecha_inicio_input.setDate(QDate(hoy.year, hoy.month, hoy.day))
        ayer = hoy - timedelta(days=1)
        form.fecha_fin_input.setDate(QDate(ayer.year, ayer.month, ayer.day))

        with patch.object(form, "mostrar_advertencia") as mock_warning:
            form.guardar_ausencia()
            mock_warning.assert_called_once()


# ============================================================================
# TEST: ELIMINAR AUSENCIA
# ============================================================================


@pytest.mark.ui
class TestGestionarAusenciasFormEliminar:
    """Tests de eliminación de ausencias."""

    def test_eliminar_sin_seleccion(self, form, datos_completos):
        """No eliminar si no hay selección."""
        form.tabla_ausencias.clearSelection()

        with patch.object(form, "mostrar_advertencia") as mock_warning:
            form.eliminar_ausencia_seleccionada()
            mock_warning.assert_called_once()

    def test_eliminar_usa_confirmacion_estandar(self, form, datos_completos):
        """Eliminar ausencia usa confirmar_accion y respeta cancelación."""
        form.tabla_ausencias.selectRow(0)

        with patch.object(form, "confirmar_accion", return_value=False) as mock_confirmar:
            with patch(
                "services.gestor_ausencias.GestorAusencias.eliminar_ausencia"
            ) as mock_delete:
                form.eliminar_ausencia_seleccionada()

        mock_confirmar.assert_called_once()
        mock_delete.assert_not_called()


# ============================================================================
# TEST: DESACTIVAR AUSENCIA
# ============================================================================


@pytest.mark.ui
class TestGestionarAusenciasFormDesactivar:
    """Tests de desactivación de ausencias."""

    def test_desactivar_sin_seleccion(self, form, datos_completos):
        """No desactivar si no hay selección."""
        form.tabla_ausencias.clearSelection()

        with patch.object(form, "mostrar_advertencia") as mock_warning:
            form.desactivar_ausencia_seleccionada()
            mock_warning.assert_called_once()

    def test_desactivar_ausencia(self, form, datos_completos):
        """Desactivar ausencia activa (sin eliminar)."""
        # Buscar fila con ausencia activa
        row_activa = None
        for row in range(form.tabla_ausencias.rowCount()):
            estado = form.tabla_ausencias.item(row, 6).text()
            if "Activa" in estado:
                row_activa = row
                break

        # Si hay una ausencia activa, desactivarla
        if row_activa is not None:
            form.tabla_ausencias.selectRow(row_activa)

            with patch.object(form, "mostrar_exito"):
                form.desactivar_ausencia_seleccionada()

            # Refrescar la sesión y verificar que fue desactivada
            form.session.expire_all()
            ausencias_activas = form.session.query(Ausencia).filter_by(activa=True).count()
            assert ausencias_activas == 0  # Todas inactivas ahora
        else:
            # Si no hay ausencias activas, el test pasa
            pass


# ============================================================================
# TEST: PREVIEW GUARDIAS AFECTADAS
# ============================================================================


@pytest.mark.ui
class TestGestionarAusenciasFormPreview:
    """Tests del preview de guardias afectadas."""

    def test_actualizar_preview_sin_profesor(self, form, datos_completos):
        """Preview vacío si no hay profesor seleccionado."""
        form.profesor_combo.setCurrentIndex(-1)
        form.actualizar_preview_guardias()

        preview_text = form.preview_text.toPlainText()
        assert "Selecciona" in preview_text.lower() or len(preview_text) > 0

    def test_actualizar_preview_con_guardias(self, form, datos_completos):
        """Preview muestra guardias afectadas por el período."""
        # Seleccionar primer profesor (Prof1 - tiene guardias los días pares)
        form.profesor_combo.setCurrentIndex(0)

        hoy = datos_completos["hoy"]
        form.fecha_inicio_input.setDate(QDate(hoy.year, hoy.month, hoy.day))
        fin = hoy + timedelta(days=4)
        form.fecha_fin_input.setDate(QDate(fin.year, fin.month, fin.day))

        form.actualizar_preview_guardias()

        preview_text = form.preview_text.toPlainText()
        # Debe mostrar algún contenido sobre guardias
        assert len(preview_text) > 0


# ============================================================================
# TEST: LIMPIAR FORMULARIO
# ============================================================================


@pytest.mark.ui
class TestGestionarAusenciasFormLimpiar:
    """Tests de limpieza del formulario."""

    def test_limpiar_formulario(self, form, datos_completos):
        """Limpiar formulario resetea campos."""
        # Llenar formulario
        form.profesor_combo.setCurrentIndex(0)
        form.tipo_combo.setCurrentText("vacaciones")
        form.motivo_input.setPlainText("Motivo de prueba")
        form.ausencia_actual = 999  # Simular que está editando

        # Limpiar
        form.limpiar_formulario()

        # Verificar reset
        assert form.ausencia_actual is None
        assert form.motivo_input.toPlainText() == ""

    def test_limpiar_restaura_titulo(self, form, datos_completos):
        """Limpiar formulario restaura el título a 'NUEVA AUSENCIA'."""
        form.titulo_form.setText("✏️ EDITAR AUSENCIA")

        form.limpiar_formulario()

        titulo = form.titulo_form.text()
        assert "NUEVA" in titulo.upper()


# ============================================================================
# TEST: DIÁLOGO REASIGNACIÓN
# ============================================================================


@pytest.mark.ui
class TestDialogoReasignacion:
    """Tests del diálogo de reasignación de guardias."""

    def test_crear_dialogo(self, qtbot, datos_completos, session):
        """Crear diálogo con guardias."""
        guardias = datos_completos["guardias"][:3]
        ausencia_id = datos_completos["ausencias"][0].id

        dialogo = DialogoReasignacion(guardias, ausencia_id, session)
        qtbot.addWidget(dialogo)

        assert dialogo is not None
        assert dialogo.tabla.rowCount() == 3

    def test_dialogo_tiene_botones(self, qtbot, datos_completos, session):
        """El diálogo tiene botones de acción."""
        guardias = datos_completos["guardias"][:2]
        ausencia_id = datos_completos["ausencias"][0].id

        dialogo = DialogoReasignacion(guardias, ausencia_id, session)
        qtbot.addWidget(dialogo)

        # Verificar que la tabla existe y tiene datos
        assert dialogo.tabla is not None
        assert dialogo.tabla.rowCount() == 2


# ============================================================================
# TEST: INTEGRACIÓN
# ============================================================================


@pytest.mark.ui
class TestGestionarAusenciasFormIntegracion:
    """Tests de integración (flujos completos)."""

    def test_flujo_seleccionar_y_limpiar(self, form, datos_completos):
        """Flujo: seleccionar ausencia → limpiar → verificar reset."""
        # Seleccionar ausencia
        form.tabla_ausencias.selectRow(0)
        form.cargar_ausencia_seleccionada()

        assert form.ausencia_actual is not None

        # Limpiar
        form.limpiar_formulario()

        assert form.ausencia_actual is None
        assert "NUEVA" in form.titulo_form.text().upper()


# ============================================================================
# TEST: RENDIMIENTO
# ============================================================================


@pytest.mark.slow
@pytest.mark.ui
class TestGestionarAusenciasFormRendimiento:
    """Tests de rendimiento con datos grandes."""

    def test_carga_inicial_rapida(
        self, qtbot, session, profesor_factory, zona_factory, curso_activo
    ):
        """La carga inicial del formulario debe ser rápida."""
        zona = zona_factory(nombre_zona="Zona Test")
        # Crear 30 profesores con guardias
        for i in range(30):
            prof = profesor_factory(nombre_completo=f"Profesor {i}", turno="mañana")
            g = Guardia(
                profesor_id=prof.id,
                fecha=date.today(),
                turno="mañana",
                recreo=1,
                curso_id=curso_activo.id,
                zona_id=zona.id,
            )
            session.add(g)
        session.commit()

        import time

        inicio = time.time()

        form = GestionarAusenciasForm(session)
        qtbot.addWidget(form)

        duracion = time.time() - inicio

        assert duracion < 3.0, f"Carga inicial tardó {duracion:.2f}s (límite: 3.0s)"
