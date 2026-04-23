"""
Tests para GestorSustituciones.

Coverage objetivo: >70%
"""

from datetime import date, timedelta
from unittest.mock import patch

import pytest
from infrastructure.database.models import Guardia, Profesor, Zona
from domain.entities.guardia_entity import GuardiaEntity
from presentation.widgets.gestor_sustituciones import GestorSustituciones
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def gestor(qapp, session):
    """Fixture para GestorSustituciones."""
    widget = GestorSustituciones(session)
    return widget


@pytest.fixture
def profesores_test(session, profesor_factory):
    """Fixture con 3 profesores para tests."""
    prof1 = profesor_factory(nombre_completo="Ana García", horas_contrato=25.0)
    prof2 = profesor_factory(nombre_completo="Carlos Ruiz", horas_contrato=25.0)
    prof3 = profesor_factory(nombre_completo="María López", horas_contrato=25.0)
    session.add_all([prof1, prof2, prof3])
    session.commit()
    return [prof1, prof2, prof3]


@pytest.fixture
def guardias_test(session, profesores_test, zona_factory):
    """Fixture con guardias de prueba."""
    zona = zona_factory(nombre_zona="Patio Principal")
    session.add(zona)
    session.commit()

    hoy = date.today()
    guardias = []

    # Profesor 1: guardia hoy mañana recreo 1
    g1 = Guardia(
        fecha=hoy,
        turno="mañana",
        recreo=1,
        profesor_id=profesores_test[0].id,
        zona_id=zona.id,
    )
    # Profesor 2: guardia hoy tarde recreo 1
    g2 = Guardia(
        fecha=hoy,
        turno="tarde",
        recreo=1,
        profesor_id=profesores_test[1].id,
        zona_id=zona.id,
    )
    # Profesor 1: guardia mañana mañana recreo 2
    g3 = Guardia(
        fecha=hoy + timedelta(days=1),
        turno="mañana",
        recreo=2,
        profesor_id=profesores_test[0].id,
        zona_id=zona.id,
    )

    guardias = [g1, g2, g3]
    session.add_all(guardias)
    session.commit()

    return guardias


# ============================================================================
# TEST CLASS: BÁSICO
# ============================================================================


class TestGestorSustitucionesBasico:
    """Tests básicos de creación e inicialización."""

    def test_crear_gestor(self, qapp, session):
        """Test que el gestor se crea correctamente."""
        gestor = GestorSustituciones(session)

        assert gestor is not None
        assert gestor.session == session
        assert gestor.windowTitle() == "Gestión de Sustituciones"

    def test_tiene_widgets_principales(self, gestor):
        """Test que el gestor tiene los widgets principales."""
        # Sección buscar
        assert gestor.fecha_buscar is not None
        assert gestor.combo_profesor_original is not None
        assert gestor.btn_buscar is not None

        # Tabla guardias
        assert gestor.tabla_guardias is not None
        assert gestor.tabla_guardias.columnCount() == 5

        # Sección sustituir
        assert gestor.combo_profesor_sustituto is not None
        assert gestor.btn_buscar_disponibles is not None
        assert gestor.text_observaciones is not None
        assert gestor.btn_confirmar_sustitucion is not None
        assert gestor.btn_cancelar is not None

        # Historial (audit log embebido)
        assert gestor._historial_audit is not None
        assert gestor._historial_audit.tabla.columnCount() == 6

    def test_boton_confirmar_deshabilitado_inicialmente(self, gestor):
        """Test que el botón confirmar está deshabilitado al inicio."""
        assert not gestor.btn_confirmar_sustitucion.isEnabled()

    def test_fecha_inicial_es_hoy(self, gestor):
        """Test que la fecha inicial es hoy."""
        fecha_widget = gestor.fecha_buscar.date().toPyDate()
        assert fecha_widget == date.today()

    def test_combo_profesor_original_tiene_opcion_todos(self, gestor):
        """Test que el combo tiene opción 'Todos'."""
        assert gestor.combo_profesor_original.count() > 0
        assert "Todos" in gestor.combo_profesor_original.itemText(0)


# ============================================================================
# TEST CLASS: CARGAR PROFESORES
# ============================================================================


class TestGestorSustitucionesCargarProfesores:
    """Tests de carga de profesores."""

    def test_cargar_profesores_exitoso(self, gestor, profesores_test):
        """Test que carga profesores correctamente."""
        gestor.cargar_profesores()

        # Combo original: "-- Todos --" + 3 profesores = 4 items
        assert gestor.combo_profesor_original.count() == 4
        assert gestor.combo_profesor_original.itemText(0) == "-- Todos --"

        # Combo sustituto: 3 profesores (sin opción "Todos")
        assert gestor.combo_profesor_sustituto.count() == 3

        # Verificar nombres
        nombres_original = [
            gestor.combo_profesor_original.itemText(i)
            for i in range(1, gestor.combo_profesor_original.count())
        ]
        assert "Ana García" in nombres_original
        assert "Carlos Ruiz" in nombres_original
        assert "María López" in nombres_original

    def test_cargar_profesores_sin_datos(self, gestor):
        """Test cargar profesores cuando no hay profesores."""
        gestor.cargar_profesores()

        # Solo "-- Todos --"
        assert gestor.combo_profesor_original.count() == 1
        assert gestor.combo_profesor_sustituto.count() == 0

    def test_cargar_profesores_maneja_excepciones(self, gestor):
        """Test que maneja excepciones al cargar profesores."""
        with patch.object(gestor.session, "query", side_effect=Exception("DB Error")):
            with patch.object(gestor, "manejar_excepcion") as mock_manejar:
                gestor.cargar_profesores()
                mock_manejar.assert_called_once()


# ============================================================================
# TEST CLASS: BUSCAR GUARDIAS
# ============================================================================


class TestGestorSustitucionesBuscarGuardias:
    """Tests de búsqueda de guardias."""

    def test_buscar_guardias_todas(self, gestor, guardias_test):
        """Test buscar todas las guardias de una fecha."""
        # Configurar: "-- Todos --" (None)
        gestor.combo_profesor_original.setCurrentIndex(0)
        gestor.fecha_buscar.setDate(date.today())

        gestor.buscar_guardias()

        # Debe encontrar 2 guardias de hoy
        assert gestor.tabla_guardias.rowCount() == 2

    def test_buscar_guardias_por_profesor(self, gestor, guardias_test, profesores_test):
        """Test buscar guardias de un profesor específico."""
        # Cargar profesores primero
        gestor.cargar_profesores()

        # Seleccionar profesor 1 (Ana García)
        for i in range(gestor.combo_profesor_original.count()):
            if gestor.combo_profesor_original.itemData(i) == profesores_test[0].id:
                gestor.combo_profesor_original.setCurrentIndex(i)
                break

        gestor.fecha_buscar.setDate(date.today())
        gestor.buscar_guardias()

        # Ana tiene 1 guardia hoy
        assert gestor.tabla_guardias.rowCount() == 1

    def test_buscar_guardias_sin_resultados(self, gestor):
        """Test buscar guardias cuando no hay resultados."""
        # Fecha sin guardias
        fecha_futura = date.today() + timedelta(days=30)
        gestor.fecha_buscar.setDate(fecha_futura)

        gestor.buscar_guardias()

        assert gestor.tabla_guardias.rowCount() == 0

    def test_buscar_guardias_llena_tabla_correctamente(
        self, gestor, guardias_test, profesores_test
    ):
        """Test que la tabla se llena con datos correctos."""
        gestor.combo_profesor_original.setCurrentIndex(0)  # Todos
        gestor.fecha_buscar.setDate(date.today())

        gestor.buscar_guardias()

        # Verificar primera fila
        assert gestor.tabla_guardias.item(0, 0) is not None  # ID
        assert "Ana García" in gestor.tabla_guardias.item(0, 1).text()  # Profesor
        assert gestor.tabla_guardias.item(0, 2).text() == "mañana"  # Turno
        assert gestor.tabla_guardias.item(0, 3).text() == "1"  # Recreo
        assert "Patio" in gestor.tabla_guardias.item(0, 4).text()  # Zona

    def test_buscar_guardias_guarda_objeto_en_item(self, gestor, guardias_test):
        """Test que guarda el objeto Guardia en el item."""
        gestor.fecha_buscar.setDate(date.today())
        gestor.buscar_guardias()

        # Obtener objeto guardado
        item = gestor.tabla_guardias.item(0, 0)
        guardia = item.data(Qt.ItemDataRole.UserRole)

        assert isinstance(guardia, GuardiaEntity)
        assert guardia.fecha == date.today()

    def test_buscar_guardias_maneja_excepciones(self, gestor):
        """Test que maneja excepciones al buscar."""
        with patch.object(gestor.session, "query", side_effect=Exception("DB Error")):
            with patch.object(gestor, "manejar_excepcion") as mock_manejar:
                gestor.buscar_guardias()
                mock_manejar.assert_called_once()


# ============================================================================
# TEST CLASS: SELECCIÓN DE GUARDIA
# ============================================================================


class TestGestorSustitucionesSeleccion:
    """Tests de selección de guardia."""

    def test_seleccionar_guardia_habilita_boton(self, gestor, guardias_test):
        """Test que seleccionar una guardia habilita el botón confirmar."""
        gestor.fecha_buscar.setDate(date.today())
        gestor.buscar_guardias()

        # Seleccionar primera fila
        gestor.tabla_guardias.selectRow(0)

        assert gestor.btn_confirmar_sustitucion.isEnabled()

    def test_deseleccionar_guardia_deshabilita_boton(self, gestor, guardias_test):
        """Test que deseleccionar deshabilita el botón."""
        gestor.fecha_buscar.setDate(date.today())
        gestor.buscar_guardias()

        gestor.tabla_guardias.selectRow(0)
        assert gestor.btn_confirmar_sustitucion.isEnabled()

        gestor.tabla_guardias.clearSelection()
        assert not gestor.btn_confirmar_sustitucion.isEnabled()


# ============================================================================
# TEST CLASS: PROFESORES DISPONIBLES
# ============================================================================


class TestGestorSustitucionesProfesoresDisponibles:
    """Tests de búsqueda de profesores disponibles."""

    def test_buscar_disponibles_sin_seleccion(self, gestor):
        """Test que muestra advertencia si no hay selección."""
        with patch.object(gestor, "mostrar_advertencia") as mock_adv:
            gestor.buscar_profesores_disponibles()
            mock_adv.assert_called_once()
            assert "Selección Requerida" in mock_adv.call_args[0][0]

    def test_buscar_disponibles_muestra_profesores(self, gestor, guardias_test, profesores_test):
        """Test que muestra profesores disponibles."""
        gestor.fecha_buscar.setDate(date.today())
        gestor.buscar_guardias()
        gestor.tabla_guardias.selectRow(0)

        # El código crea un QMessageBox manualmente, mockeamos exec() para evitar bloqueo
        with patch.object(QMessageBox, "exec", return_value=None) as mock_exec:
            gestor.buscar_profesores_disponibles()
            # Verificamos que se llamó a exec() (significa que se creó el diálogo)
            mock_exec.assert_called()

    def test_buscar_disponibles_sin_profesores(self, gestor, guardias_test, session):
        """Test cuando no hay profesores disponibles."""
        # Agregar guardia para María López (ahora todos ocupados)
        maria = session.query(Profesor).filter_by(nombre_completo="María López").first()
        zona = session.query(Zona).first()

        nueva_guardia = Guardia(
            fecha=date.today(),
            turno="mañana",
            recreo=2,
            profesor_id=maria.id,
            zona_id=zona.id,
        )
        session.add(nueva_guardia)
        session.commit()

        gestor.fecha_buscar.setDate(date.today())
        gestor.buscar_guardias()
        gestor.tabla_guardias.selectRow(0)

        with patch.object(gestor, "mostrar_advertencia") as mock_adv:
            gestor.buscar_profesores_disponibles()
            mock_adv.assert_called_once()
            assert "Sin Disponibles" in mock_adv.call_args[0][0]

    def test_buscar_disponibles_maneja_excepciones(self, gestor, guardias_test):
        """Test que maneja excepciones al buscar disponibles."""
        gestor.fecha_buscar.setDate(date.today())
        gestor.buscar_guardias()
        gestor.tabla_guardias.selectRow(0)

        with patch.object(gestor.session, "query", side_effect=Exception("DB Error")):
            with patch.object(gestor, "manejar_excepcion") as mock_manejar:
                gestor.buscar_profesores_disponibles()
                mock_manejar.assert_called_once()


# ============================================================================
# TEST CLASS: CONFIRMAR SUSTITUCIÓN
# ============================================================================


class TestGestorSustitucionesConfirmar:
    """Tests de confirmación de sustitución."""

    def test_confirmar_sin_seleccion_no_hace_nada(self, gestor):
        """Test que no hace nada si no hay guardia seleccionada."""
        # No debería lanzar excepción
        gestor.confirmar_sustitucion()
        # Solo verificar que no crashea

    def test_confirmar_sin_profesor_sustituto(self, gestor, guardias_test):
        """Test que muestra advertencia si no hay sustituto."""
        gestor.fecha_buscar.setDate(date.today())
        gestor.buscar_guardias()
        gestor.tabla_guardias.selectRow(0)

        # No hay opción None en combo sustituto, solo profesores
        # Simular que no hay currentData válido
        gestor.combo_profesor_sustituto.setCurrentIndex(0)
        # Forzar currentData a None con setItemData
        gestor.combo_profesor_sustituto.setItemData(0, None)

        with patch.object(gestor, "mostrar_advertencia") as mock_adv:
            gestor.confirmar_sustitucion()
            mock_adv.assert_called_once()
            assert "Profesor Requerido" in mock_adv.call_args[0][0]

    def test_confirmar_con_profesor_ocupado(self, gestor, guardias_test, profesores_test):
        """Test que valida que el sustituto no tenga guardia."""
        gestor.cargar_profesores()  # Asegurar que profesores están cargados
        gestor.fecha_buscar.setDate(date.today())
        gestor.buscar_guardias()
        gestor.tabla_guardias.selectRow(0)  # Guardia de Ana

        # Seleccionar Carlos como sustituto (ya tiene guardia hoy)
        for i in range(gestor.combo_profesor_sustituto.count()):
            if gestor.combo_profesor_sustituto.itemData(i) == profesores_test[1].id:
                gestor.combo_profesor_sustituto.setCurrentIndex(i)
                break

        with patch.object(gestor, "mostrar_advertencia") as mock_adv:
            gestor.confirmar_sustitucion()
            mock_adv.assert_called_once()
            assert "Profesor Ocupado" in mock_adv.call_args[0][0]

    def test_confirmar_sustitucion_exitosa(self, gestor, guardias_test, profesores_test):
        """Test que confirma sustitución exitosamente."""
        gestor.cargar_profesores()  # Cargar profesores
        gestor.fecha_buscar.setDate(date.today())
        gestor.buscar_guardias()
        gestor.tabla_guardias.selectRow(0)  # Guardia de Ana

        # Seleccionar María como sustituta (disponible)
        for i in range(gestor.combo_profesor_sustituto.count()):
            if gestor.combo_profesor_sustituto.itemData(i) == profesores_test[2].id:
                gestor.combo_profesor_sustituto.setCurrentIndex(i)
                break

        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
            with patch.object(gestor, "mostrar_exito") as mock_exito:
                gestor.confirmar_sustitucion()
                mock_exito.assert_called_once()

        # Verificar que la guardia cambió de profesor
        guardia = guardias_test[0]
        gestor.session.refresh(guardia)
        assert guardia.profesor_id == profesores_test[2].id

    def test_confirmar_sustitucion_cancelada(self, gestor, guardias_test, profesores_test):
        """Test que respeta la cancelación del usuario."""
        gestor.cargar_profesores()
        gestor.fecha_buscar.setDate(date.today())
        gestor.buscar_guardias()
        gestor.tabla_guardias.selectRow(0)

        for i in range(gestor.combo_profesor_sustituto.count()):
            if gestor.combo_profesor_sustituto.itemData(i) == profesores_test[2].id:
                gestor.combo_profesor_sustituto.setCurrentIndex(i)
                break

        profesor_original_id = guardias_test[0].profesor_id

        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.No):
            gestor.confirmar_sustitucion()

        # Verificar que NO cambió
        gestor.session.refresh(guardias_test[0])
        assert guardias_test[0].profesor_id == profesor_original_id

    def test_confirmar_muestra_dialogo_confirmacion(self, gestor, guardias_test, profesores_test):
        """Test que muestra diálogo de confirmación con info correcta."""
        gestor.cargar_profesores()
        gestor.fecha_buscar.setDate(date.today())
        gestor.buscar_guardias()
        gestor.tabla_guardias.selectRow(0)

        for i in range(gestor.combo_profesor_sustituto.count()):
            if gestor.combo_profesor_sustituto.itemData(i) == profesores_test[2].id:
                gestor.combo_profesor_sustituto.setCurrentIndex(i)
                break

        with patch.object(
            QMessageBox, "question", return_value=QMessageBox.StandardButton.No
        ) as mock_question:
            gestor.confirmar_sustitucion()

            # Verificar contenido del diálogo
            mensaje = mock_question.call_args[0][2]
            assert "Ana García" in mensaje  # Profesor original
            assert "María López" in mensaje  # Sustituto
            assert "mañana" in mensaje  # Turno
            assert "Recreo 1" in mensaje  # Recreo

    def test_confirmar_limpia_formulario_despues(self, gestor, guardias_test, profesores_test):
        """Test que limpia el formulario después de confirmar."""
        gestor.cargar_profesores()
        gestor.fecha_buscar.setDate(date.today())
        gestor.buscar_guardias()
        gestor.tabla_guardias.selectRow(0)

        for i in range(gestor.combo_profesor_sustituto.count()):
            if gestor.combo_profesor_sustituto.itemData(i) == profesores_test[2].id:
                gestor.combo_profesor_sustituto.setCurrentIndex(i)
                break

        gestor.text_observaciones.setText("Test observación")

        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
            with patch.object(gestor, "mostrar_exito"):
                gestor.confirmar_sustitucion()

        # Verificar limpieza
        assert gestor.text_observaciones.toPlainText() == ""
        assert not gestor.btn_confirmar_sustitucion.isEnabled()

    def test_confirmar_maneja_excepciones(self, gestor, guardias_test, profesores_test):
        """Test que maneja excepciones al confirmar."""
        gestor.cargar_profesores()
        gestor.fecha_buscar.setDate(date.today())
        gestor.buscar_guardias()
        gestor.tabla_guardias.selectRow(0)

        for i in range(gestor.combo_profesor_sustituto.count()):
            if gestor.combo_profesor_sustituto.itemData(i) == profesores_test[2].id:
                gestor.combo_profesor_sustituto.setCurrentIndex(i)
                break

        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
            with patch.object(gestor.session, "commit", side_effect=Exception("Commit Error")):
                with patch.object(gestor, "manejar_excepcion") as mock_manejar:
                    gestor.confirmar_sustitucion()
                    mock_manejar.assert_called_once()


# ============================================================================
# TEST CLASS: LIMPIAR FORMULARIO
# ============================================================================


class TestGestorSustitucionesLimpiar:
    """Tests de limpieza de formulario."""

    def test_limpiar_formulario(self, gestor, guardias_test):
        """Test que limpia el formulario correctamente."""
        # Cargar profesores primero para tener items en combo
        gestor.cargar_profesores()

        # Configurar estado
        gestor.fecha_buscar.setDate(date.today())
        gestor.buscar_guardias()
        gestor.tabla_guardias.selectRow(0)
        gestor.combo_profesor_sustituto.setCurrentIndex(1)
        gestor.text_observaciones.setText("Observación de test")

        # Limpiar
        gestor.limpiar_formulario()

        # Verificar
        assert len(gestor.tabla_guardias.selectedItems()) == 0
        assert gestor.combo_profesor_sustituto.currentIndex() == 0
        assert gestor.text_observaciones.toPlainText() == ""
        assert not gestor.btn_confirmar_sustitucion.isEnabled()


# ============================================================================
# TEST CLASS: REFRESCAR
# ============================================================================


class TestGestorSustitucionesRefrescar:
    """Tests de refresco de datos."""

    def test_refrescar(self, gestor, profesores_test, guardias_test):
        """Test que refresca los datos."""
        # Llenar tabla
        gestor.fecha_buscar.setDate(date.today())
        gestor.buscar_guardias()
        assert gestor.tabla_guardias.rowCount() > 0

        # Refrescar
        gestor.refrescar()

        # Verificar que tabla se limpió
        assert gestor.tabla_guardias.rowCount() == 0
        # Profesores recargados
        assert gestor.combo_profesor_original.count() > 0


# ============================================================================
# TEST CLASS: INTEGRACIÓN
# ============================================================================


class TestGestorSustitucionesIntegracion:
    """Tests de integración de flujos completos."""

    def test_flujo_completo_sustitucion(self, gestor, guardias_test, profesores_test):
        """Test flujo completo: buscar → seleccionar → confirmar."""
        gestor.cargar_profesores()

        # 1. Buscar guardias
        gestor.fecha_buscar.setDate(date.today())
        gestor.buscar_guardias()
        assert gestor.tabla_guardias.rowCount() == 2

        # 2. Seleccionar primera guardia (Ana)
        gestor.tabla_guardias.selectRow(0)
        assert gestor.btn_confirmar_sustitucion.isEnabled()

        # 3. Ver disponibles
        with patch.object(QMessageBox, "information"):
            gestor.buscar_profesores_disponibles()

        # 4. Seleccionar María como sustituta
        for i in range(gestor.combo_profesor_sustituto.count()):
            if gestor.combo_profesor_sustituto.itemData(i) == profesores_test[2].id:
                gestor.combo_profesor_sustituto.setCurrentIndex(i)
                break

        # 5. Confirmar
        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
            with patch.object(gestor, "mostrar_exito"):
                gestor.confirmar_sustitucion()

        # 6. Verificar cambio
        gestor.session.refresh(guardias_test[0])
        assert guardias_test[0].profesor_id == profesores_test[2].id

    def test_multiples_sustituciones_mismo_dia(self, gestor, guardias_test, profesores_test):
        """Test que permite múltiples sustituciones el mismo día."""
        gestor.cargar_profesores()
        gestor.fecha_buscar.setDate(date.today())

        # Primera sustitución: Ana → María en guardia 1
        gestor.buscar_guardias()
        gestor.tabla_guardias.selectRow(0)

        for i in range(gestor.combo_profesor_sustituto.count()):
            if gestor.combo_profesor_sustituto.itemData(i) == profesores_test[2].id:
                gestor.combo_profesor_sustituto.setCurrentIndex(i)
                break

        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
            with patch.object(gestor, "mostrar_exito"):
                gestor.confirmar_sustitucion()

        # Segunda sustitución: Carlos → Ana en guardia 2
        gestor.buscar_guardias()
        gestor.tabla_guardias.selectRow(1)  # Segunda guardia (Carlos)

        for i in range(gestor.combo_profesor_sustituto.count()):
            if gestor.combo_profesor_sustituto.itemData(i) == profesores_test[0].id:
                gestor.combo_profesor_sustituto.setCurrentIndex(i)
                break

        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
            with patch.object(gestor, "mostrar_exito"):
                gestor.confirmar_sustitucion()

        # Verificar ambos cambios
        gestor.session.refresh(guardias_test[0])
        gestor.session.refresh(guardias_test[1])
        assert guardias_test[0].profesor_id == profesores_test[2].id  # Ana → María
        assert guardias_test[1].profesor_id == profesores_test[0].id  # Carlos → Ana


# ============================================================================
# TEST CLASS: RENDIMIENTO
# ============================================================================


class TestGestorSustitucionesRendimiento:
    """Tests de rendimiento."""

    @pytest.mark.slow
    def test_carga_inicial_rapida(self, qapp, session, profesor_factory):
        """Test que la carga inicial es rápida (<1s)."""
        import time

        # Crear muchos profesores
        for i in range(50):
            prof = profesor_factory(nombre_completo=f"Profesor {i}", horas_contrato=25.0)
            session.add(prof)
        session.commit()

        start = time.time()
        gestor = GestorSustituciones(session)
        elapsed = time.time() - start

        assert gestor.combo_profesor_original.count() > 0
        assert elapsed < 1.0

    @pytest.mark.slow
    def test_busqueda_rapida_con_muchas_guardias(
        self, gestor, profesor_factory, zona_factory, session
    ):
        """Test que la búsqueda es rápida con muchas guardias."""
        import time

        # Crear profesores y zona
        profesores = [
            profesor_factory(nombre_completo=f"Prof {i}", horas_contrato=25.0) for i in range(20)
        ]
        zona = zona_factory(nombre_zona="Zona Test")
        session.add_all(profesores + [zona])
        session.commit()

        # Crear 100 guardias
        hoy = date.today()
        for i in range(100):
            g = Guardia(
                fecha=hoy,
                turno="mañana" if i % 2 == 0 else "tarde",
                recreo=(i % 3) + 1,
                profesor_id=profesores[i % len(profesores)].id,
                zona_id=zona.id,
            )
            session.add(g)
        session.commit()

        gestor.fecha_buscar.setDate(hoy)

        start = time.time()
        gestor.buscar_guardias()
        elapsed = time.time() - start

        assert gestor.tabla_guardias.rowCount() == 100
        assert elapsed < 2.0  # <2s para 100 guardias
