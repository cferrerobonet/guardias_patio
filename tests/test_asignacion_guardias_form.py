"""
Tests para AsignacionGuardiasForm.

Pruebas del formulario de asignación de guardias que incluyen:
- Carga de estadísticas
- Cálculo de distribución
- Generación de calendario de guardias
- Validación de flujos completos
"""

from datetime import date, time
from unittest.mock import Mock, patch

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox

from models.models import Configuracion, Guardia
from presentation.forms.asignacion_guardias_form import AsignacionGuardiasForm
from utils.exceptions import BusinessLogicError

# ========================================
# FIXTURES
# ========================================


@pytest.fixture
def configuracion(session):
    """Crear configuración básica para tests"""
    config = Configuracion(
        fecha_inicio_curso=date(2024, 9, 1),
        fecha_fin_curso=date(2025, 6, 30),
        hora_recreo1_manana=time(11, 0),
        hora_recreo2_manana=time(11, 30),
        hora_recreo1_tarde=time(16, 0),
        hora_recreo2_tarde=time(16, 30),
        activar_festivos_automaticos=True,
        dias_no_lectivos_personalizados="[]",
        recreos_config=(
            '[{"id": 1, "etiqueta": "Recreo 1", "turno": "manana", '
            '"hora": "11:00", "zonas": 2}]'
        ),
        ajuste_tutores=1.0,
        ajuste_no_tutores=1.0
    )
    session.add(config)
    session.commit()
    return config


@pytest.fixture
def zonas(session, zona_factory):
    """Crear zonas de prueba"""
    zona1 = zona_factory(nombre_zona="Patio Principal")
    zona2 = zona_factory(nombre_zona="Patio Deportivo")
    return [zona1, zona2]


@pytest.fixture
def profesores(session, profesor_factory):
    """Crear profesores de prueba"""
    prof1 = profesor_factory(
        nombre_completo="Juan García",
        horas_contrato=25.0,
        turno="mañana",
    )
    prof2 = profesor_factory(
        nombre_completo="María López",
        horas_contrato=12.5,
        turno="mañana",
    )
    return [prof1, prof2]


@pytest.fixture
def guardias_existentes(session, profesores, zonas, configuracion):
    """Crear guardias existentes para tests de limpieza"""
    guardias = []
    for i in range(5):
        guardia = Guardia(
            profesor_id=profesores[0].id,
            zona_id=zonas[0].id,
            fecha=date(2024, 9, 2 + i),
            turno="mañana",
            recreo=1,
        )
        guardias.append(guardia)
        session.add(guardia)
    session.commit()
    return guardias


# ========================================
# TESTS BÁSICOS
# ========================================


class TestAsignacionGuardiasFormBasico:
    """Tests básicos de creación y componentes del formulario"""

    def test_crear_form(self, qapp, session):
        """Test crear formulario correctamente"""
        form = AsignacionGuardiasForm(session)

        assert form is not None
        assert form.windowTitle() == "Asignación de Guardias"
        assert hasattr(form, "session")
        assert form.session == session

    def test_has_use_cases(self, qapp, session):
        """Test que el formulario tiene los Use Cases necesarios"""
        form = AsignacionGuardiasForm(session)

        assert hasattr(form, "obtener_estadisticas_uc")
        assert hasattr(form, "calcular_distribucion_uc")
        assert hasattr(form, "generar_guardias_uc")

    def test_has_widgets(self, qapp, session):
        """Test que el formulario tiene los widgets necesarios"""
        form = AsignacionGuardiasForm(session)

        assert hasattr(form, "stats_text")
        assert hasattr(form, "distribucion_text")
        assert hasattr(form, "resultado_text")
        assert hasattr(form, "generar_button")

        # Texto de solo lectura
        assert form.stats_text.isReadOnly()
        assert form.distribucion_text.isReadOnly()
        assert form.resultado_text.isReadOnly()

    def test_generar_button_disabled_initially(self, qapp, session):
        """Test que el botón generar está deshabilitado inicialmente"""
        form = AsignacionGuardiasForm(session)

        assert not form.generar_button.isEnabled()


# ========================================
# TESTS DE ESTADÍSTICAS
# ========================================


class TestAsignacionGuardiasFormEstadisticas:
    """Tests de carga y visualización de estadísticas"""

    def test_cargar_estadisticas_success(
        self, qapp, session, configuracion, zonas, profesores
    ):
        """Test cargar estadísticas correctamente"""
        form = AsignacionGuardiasForm(session)

        texto = form.stats_text.toPlainText()

        assert "Días lectivos:" in texto
        assert "días (L-V)" in texto
        assert "Número de zonas: 2" in texto
        assert "Número de profesores: 2" in texto
        assert "SLOTS TOTALES" in texto

    def test_cargar_estadisticas_sin_config(self, qapp, session):
        """Test cargar estadísticas sin configuración"""
        form = AsignacionGuardiasForm(session)

        texto = form.stats_text.toPlainText()

        # Debe mostrar mensaje de error
        assert "⚠️" in texto or "Error" in texto.lower() or "no" in texto.lower()

    def test_cargar_estadisticas_error_handling(self, qapp, session):
        """Test manejo de errores al cargar estadísticas"""
        with patch(
            "presentation.forms.asignacion_guardias_form.ObtenerEstadisticasUseCase"
        ) as mock_uc:
            # Mock que lanza excepción
            mock_instance = Mock()
            mock_instance.execute.side_effect = BusinessLogicError(
                "Error al obtener estadísticas"
            )
            mock_uc.return_value = mock_instance

            form = AsignacionGuardiasForm(session)

            texto = form.stats_text.toPlainText()
            assert "Error al obtener estadísticas" in texto


# ========================================
# TESTS DE CÁLCULO DE DISTRIBUCIÓN
# ========================================


class TestAsignacionGuardiasFormDistribucion:
    """Tests de cálculo de distribución de guardias"""

    def test_calcular_distribucion_success(
        self, qtbot, session, configuracion, zonas, profesores
    ):
        """Test calcular distribución correctamente"""
        form = AsignacionGuardiasForm(session)

        # Simular clic en botón calcular
        with patch.object(form, "calcular_distribucion_uc") as mock_uc:
            # Mock del DTO de respuesta
            mock_distribucion = Mock()
            mock_distribucion.distribucion = {
                profesores[0].id: 100,
                profesores[1].id: 50,
            }
            mock_distribucion.total_guardias = 150
            mock_distribucion.slots_totales = 360
            mock_distribucion.es_exacta = False
            mock_distribucion.diferencia = 210

            mock_uc.execute.return_value = mock_distribucion

            # Ejecutar
            qtbot.mouseClick(
                form.findChild(type(form.generar_button).__bases__[0]),
                Qt.MouseButton.LeftButton,
            )
            form.calcular_distribucion()

            texto = form.distribucion_text.toPlainText()

            assert "Juan García" in texto
            assert "María López" in texto
            assert "100 guardias" in texto
            assert "50 guardias" in texto
            assert "TOTAL: 150" in texto

    def test_calcular_distribucion_habilita_boton(
        self, qtbot, session, configuracion, zonas, profesores
    ):
        """Test que calcular distribución habilita botón de generar"""
        form = AsignacionGuardiasForm(session)

        assert not form.generar_button.isEnabled()

        with patch.object(form, "calcular_distribucion_uc") as mock_uc:
            mock_distribucion = Mock()
            mock_distribucion.distribucion = {profesores[0].id: 100}
            mock_distribucion.total_guardias = 100
            mock_distribucion.slots_totales = 360
            mock_distribucion.es_exacta = True
            mock_distribucion.diferencia = 0

            mock_uc.execute.return_value = mock_distribucion

            form.calcular_distribucion()

            # Botón debe estar habilitado
            assert form.generar_button.isEnabled()

    def test_calcular_distribucion_error(self, qtbot, session):
        """Test error al calcular distribución"""
        form = AsignacionGuardiasForm(session)

        with patch.object(form, "calcular_distribucion_uc") as mock_uc:
            mock_uc.execute.side_effect = BusinessLogicError(
                "No hay profesores suficientes"
            )

            with patch.object(form, "mostrar_error") as mock_error:
                form.calcular_distribucion()

                mock_error.assert_called_once()
                args = mock_error.call_args[0]
                assert "Error en Cálculo" in args[0]
                assert "No hay profesores suficientes" in args[1]

    def test_distribucion_exacta_vs_no_exacta(
        self, qtbot, session, configuracion, zonas, profesores
    ):
        """Test diferencia entre distribución exacta y no exacta"""
        form = AsignacionGuardiasForm(session)

        # Caso 1: Distribución exacta
        with patch.object(form, "calcular_distribucion_uc") as mock_uc:
            mock_distribucion = Mock()
            mock_distribucion.distribucion = {profesores[0].id: 100}
            mock_distribucion.total_guardias = 100
            mock_distribucion.slots_totales = 100
            mock_distribucion.es_exacta = True
            mock_distribucion.diferencia = 0

            mock_uc.execute.return_value = mock_distribucion

            form.calcular_distribucion()
            texto = form.distribucion_text.toPlainText()

            assert "La distribución es exacta" in texto

        # Caso 2: Distribución no exacta
        with patch.object(form, "calcular_distribucion_uc") as mock_uc:
            mock_distribucion = Mock()
            mock_distribucion.distribucion = {profesores[0].id: 100}
            mock_distribucion.total_guardias = 100
            mock_distribucion.slots_totales = 150
            mock_distribucion.es_exacta = False
            mock_distribucion.diferencia = -50

            mock_uc.execute.return_value = mock_distribucion

            form.calcular_distribucion()
            texto = form.distribucion_text.toPlainText()

            assert "Diferencia:" in texto
            assert "50" in texto


# ========================================
# TESTS DE GENERACIÓN DE GUARDIAS
# ========================================


class TestAsignacionGuardiasFormGeneracion:
    """Tests de generación de guardias"""

    def test_generar_guardias_sin_existentes(
        self, qtbot, session, configuracion, zonas, profesores
    ):
        """Test generar guardias sin guardias existentes"""
        form = AsignacionGuardiasForm(session)

        with patch.object(form, "generar_guardias_uc") as mock_uc:
            # Mock del resumen
            mock_resumen = Mock()
            mock_resumen.guardias_generadas = 100
            mock_resumen.slots_esperados = 100
            mock_resumen.cobertura_completa = True
            mock_resumen.slots_sin_cubrir = 0
            mock_resumen.resumen_por_profesor = {profesores[0].id: 100}
            mock_resumen.mensaje = "Guardias generadas correctamente"

            mock_uc.execute.return_value = mock_resumen

            with patch.object(form, "mostrar_exito") as mock_exito:
                with patch(
                    "presentation.forms.asignacion_guardias_form.QProgressDialog"
                ) as mock_progress:
                    # Mock del progress dialog
                    mock_progress_instance = Mock()
                    mock_progress.return_value = mock_progress_instance

                    form.generar_guardias()

                    # Verificar que se llamó al use case
                    mock_uc.execute.assert_called_once()

                    # Verificar que se mostró mensaje de éxito
                    mock_exito.assert_called_once()

    def test_generar_guardias_con_existentes_eliminar(
        self, qtbot, session, guardias_existentes, profesores
    ):
        """Test generar guardias con existentes - elegir eliminar"""
        form = AsignacionGuardiasForm(session)

        # Verificar que hay guardias
        assert session.query(Guardia).count() == 5

        with patch.object(form, "generar_guardias_uc") as mock_uc:
            mock_resumen = Mock()
            mock_resumen.guardias_generadas = 100
            mock_resumen.slots_esperados = 100
            mock_resumen.cobertura_completa = True
            mock_resumen.slots_sin_cubrir = 0
            mock_resumen.resumen_por_profesor = {}
            mock_resumen.mensaje = "Guardias generadas"

            mock_uc.execute.return_value = mock_resumen

            # Mock de QMessageBox para simular respuesta "Yes"
            with patch(
                "presentation.forms.asignacion_guardias_form.QMessageBox.question",
                return_value=QMessageBox.StandardButton.Yes,
            ):
                with patch(
                    "presentation.forms.asignacion_guardias_form.QProgressDialog"
                ):
                    with patch.object(form, "mostrar_exito"):
                        form.generar_guardias()

                        # Verificar que se llamó con eliminar_existentes=True
                        call_kwargs = mock_uc.execute.call_args[1]
                        assert call_kwargs["eliminar_existentes"] is True

    def test_generar_guardias_con_existentes_no_eliminar(
        self, qtbot, session, guardias_existentes
    ):
        """Test generar guardias con existentes - elegir NO eliminar"""
        form = AsignacionGuardiasForm(session)

        with patch.object(form, "generar_guardias_uc") as mock_uc:
            mock_resumen = Mock()
            mock_resumen.guardias_generadas = 100
            mock_resumen.slots_esperados = 100
            mock_resumen.cobertura_completa = True
            mock_resumen.slots_sin_cubrir = 0
            mock_resumen.resumen_por_profesor = {}
            mock_resumen.mensaje = "Guardias generadas"

            mock_uc.execute.return_value = mock_resumen

            # Mock de QMessageBox para simular respuesta "No"
            with patch(
                "presentation.forms.asignacion_guardias_form.QMessageBox.question",
                return_value=QMessageBox.StandardButton.No,
            ):
                with patch(
                    "presentation.forms.asignacion_guardias_form.QProgressDialog"
                ):
                    form.generar_guardias()

                    # Verificar que se llamó con eliminar_existentes=False
                    call_kwargs = mock_uc.execute.call_args[1]
                    assert call_kwargs["eliminar_existentes"] is False

    def test_generar_guardias_cancelar(self, qtbot, session, guardias_existentes):
        """Test cancelar generación de guardias"""
        form = AsignacionGuardiasForm(session)

        with patch.object(form, "generar_guardias_uc") as mock_uc:
            # Mock de QMessageBox para simular respuesta "Cancel"
            with patch(
                "presentation.forms.asignacion_guardias_form.QMessageBox.question",
                return_value=QMessageBox.StandardButton.Cancel,
            ):
                form.generar_guardias()

                # No debe llamarse al use case
                mock_uc.execute.assert_not_called()

    def test_generar_guardias_progress_callback(
        self, qtbot, session, configuracion, zonas, profesores
    ):
        """Test que el progress callback se pasa correctamente"""
        form = AsignacionGuardiasForm(session)

        with patch.object(form, "generar_guardias_uc") as mock_uc:
            mock_resumen = Mock()
            mock_resumen.guardias_generadas = 100
            mock_resumen.slots_esperados = 100
            mock_resumen.cobertura_completa = True
            mock_resumen.slots_sin_cubrir = 0
            mock_resumen.resumen_por_profesor = {}
            mock_resumen.mensaje = "Guardias generadas"

            mock_uc.execute.return_value = mock_resumen

            with patch(
                "presentation.forms.asignacion_guardias_form.QProgressDialog"
            ) as mock_progress_cls:
                mock_progress = Mock()
                mock_progress_cls.return_value = mock_progress

                with patch.object(form, "mostrar_exito"):
                    form.generar_guardias()

                    # Verificar que se llamó con progress_callback
                    call_kwargs = mock_uc.execute.call_args[1]
                    assert "progress_callback" in call_kwargs
                    assert callable(call_kwargs["progress_callback"])

    def test_generar_guardias_error(self, qtbot, session):
        """Test error al generar guardias"""
        form = AsignacionGuardiasForm(session)

        with patch.object(form, "generar_guardias_uc") as mock_uc:
            mock_uc.execute.side_effect = BusinessLogicError(
                "No se pueden generar guardias"
            )

            with patch(
                "presentation.forms.asignacion_guardias_form.QProgressDialog"
            ):
                with patch.object(form, "mostrar_error") as mock_error:
                    form.generar_guardias()

                    mock_error.assert_called_once()
                    args = mock_error.call_args[0]
                    assert "Error en Generación" in args[0]


# ========================================
# TESTS DE FORMATEO DE RESUMEN
# ========================================


class TestAsignacionGuardiasFormFormateoResumen:
    """Tests del método _formatear_resumen"""

    def test_formatear_resumen_cobertura_completa(
        self, qtbot, session, profesores
    ):
        """Test formatear resumen con cobertura completa"""
        form = AsignacionGuardiasForm(session)

        mock_resumen = Mock()
        mock_resumen.guardias_generadas = 100
        mock_resumen.slots_esperados = 100
        mock_resumen.cobertura_completa = True
        mock_resumen.slots_sin_cubrir = 0
        mock_resumen.resumen_por_profesor = {
            profesores[0].id: 60,
            profesores[1].id: 40,
        }

        texto = form._formatear_resumen(mock_resumen)

        assert "Guardias generadas: 100" in texto
        assert "Slots esperados: 100" in texto
        assert "Cobertura completa" in texto
        assert "Juan García: 60" in texto
        assert "María López: 40" in texto

    def test_formatear_resumen_sin_cobertura_completa(
        self, qtbot, session, profesores
    ):
        """Test formatear resumen sin cobertura completa"""
        form = AsignacionGuardiasForm(session)

        mock_resumen = Mock()
        mock_resumen.guardias_generadas = 80
        mock_resumen.slots_esperados = 100
        mock_resumen.cobertura_completa = False
        mock_resumen.slots_sin_cubrir = 20
        mock_resumen.resumen_por_profesor = {profesores[0].id: 80}

        texto = form._formatear_resumen(mock_resumen)

        assert "Guardias generadas: 80" in texto
        assert "Slots esperados: 100" in texto
        assert "20 slots sin cubrir" in texto

    def test_formatear_resumen_top_10_profesores(self, qtbot, session, profesor_factory):
        """Test formatear resumen con top 10 profesores"""
        form = AsignacionGuardiasForm(session)

        # Crear 15 profesores usando la factory
        profesores = []
        for i in range(15):
            prof = profesor_factory(
                nombre_completo=f"Profesor {i}",
                horas_contrato=25.0,
                turno="mañana",
            )
            profesores.append(prof)

        # Crear resumen con distribución
        distribucion = {prof.id: 100 - i * 5 for i, prof in enumerate(profesores)}

        mock_resumen = Mock()
        mock_resumen.guardias_generadas = sum(distribucion.values())
        mock_resumen.slots_esperados = mock_resumen.guardias_generadas
        mock_resumen.cobertura_completa = True
        mock_resumen.slots_sin_cubrir = 0
        mock_resumen.resumen_por_profesor = distribucion

        texto = form._formatear_resumen(mock_resumen)

        # Solo debe mostrar top 10
        assert "top 10" in texto.lower()
        assert "Profesor 0: 100" in texto  # El primero
        assert "Profesor 9:" in texto  # El décimo
        assert "Profesor 14:" not in texto  # El 15 no debe aparecer


# ========================================
# TESTS DE LIMPIEZA
# ========================================


class TestAsignacionGuardiasFormLimpieza:
    """Tests de limpieza del formulario"""

    def test_limpiar_formulario(self, qtbot, session, configuracion, zonas, profesores):
        """Test limpiar formulario"""
        form = AsignacionGuardiasForm(session)

        # Llenar con datos
        form.distribucion_text.setText("Datos de prueba")
        form.resultado_text.setText("Resultados de prueba")
        form.generar_button.setEnabled(True)

        # Limpiar
        form.limpiar_formulario()

        assert form.distribucion_text.toPlainText() == ""
        assert form.resultado_text.toPlainText() == ""
        assert not form.generar_button.isEnabled()

        # Stats debe recargarse
        assert "Días lectivos" in form.stats_text.toPlainText()

    def test_validar_formulario(self, qtbot, session):
        """Test validar formulario (siempre True)"""
        form = AsignacionGuardiasForm(session)

        # La validación siempre es True
        assert form.validar_formulario() is True


# ========================================
# TESTS DE INTEGRACIÓN
# ========================================


class TestAsignacionGuardiasFormIntegracion:
    """Tests de integración del formulario"""

    def test_flujo_completo_sin_guardias(
        self, qtbot, session, configuracion, zonas, profesores
    ):
        """Test flujo completo: estadísticas → distribución → generación"""
        form = AsignacionGuardiasForm(session)

        # 1. Verificar estadísticas cargadas
        texto_stats = form.stats_text.toPlainText()
        assert "Días lectivos:" in texto_stats
        assert "días (L-V)" in texto_stats
        assert not form.generar_button.isEnabled()

        # 2. Calcular distribución
        with patch.object(form, "calcular_distribucion_uc") as mock_dist_uc:
            mock_distribucion = Mock()
            mock_distribucion.distribucion = {profesores[0].id: 100}
            mock_distribucion.total_guardias = 100
            mock_distribucion.slots_totales = 360
            mock_distribucion.es_exacta = False
            mock_distribucion.diferencia = 260

            mock_dist_uc.execute.return_value = mock_distribucion

            form.calcular_distribucion()

            # Botón debe habilitarse
            assert form.generar_button.isEnabled()
            assert "Juan García" in form.distribucion_text.toPlainText()

        # 3. Generar guardias
        with patch.object(form, "generar_guardias_uc") as mock_gen_uc:
            mock_resumen = Mock()
            mock_resumen.guardias_generadas = 100
            mock_resumen.slots_esperados = 100
            mock_resumen.cobertura_completa = True
            mock_resumen.slots_sin_cubrir = 0
            mock_resumen.resumen_por_profesor = {profesores[0].id: 100}
            mock_resumen.mensaje = "Guardias generadas"

            mock_gen_uc.execute.return_value = mock_resumen

            with patch(
                "presentation.forms.asignacion_guardias_form.QProgressDialog"
            ):
                with patch.object(form, "mostrar_exito"):
                    form.generar_guardias()

                    # Verificar resumen
                    assert (
                        "Guardias generadas: 100"
                        in form.resultado_text.toPlainText()
                    )

    def test_flujo_con_guardias_existentes_completo(
        self, qtbot, session, guardias_existentes, profesores
    ):
        """Test flujo completo con guardias existentes"""
        form = AsignacionGuardiasForm(session)

        # Verificar guardias existentes
        assert session.query(Guardia).count() == 5

        # Generar con confirmación
        with patch.object(form, "generar_guardias_uc") as mock_uc:
            mock_resumen = Mock()
            mock_resumen.guardias_generadas = 100
            mock_resumen.slots_esperados = 100
            mock_resumen.cobertura_completa = True
            mock_resumen.slots_sin_cubrir = 0
            mock_resumen.resumen_por_profesor = {}
            mock_resumen.mensaje = "Guardias generadas"

            mock_uc.execute.return_value = mock_resumen

            with patch(
                "presentation.forms.asignacion_guardias_form.QMessageBox.question",
                return_value=QMessageBox.StandardButton.Yes,
            ):
                with patch(
                    "presentation.forms.asignacion_guardias_form.QProgressDialog"
                ):
                    with patch.object(form, "mostrar_exito") as mock_exito:
                        form.generar_guardias()

                        # Debe mostrar dos mensajes de éxito
                        assert mock_exito.call_count == 2

                        # Primera llamada: limpieza
                        first_call = mock_exito.call_args_list[0][0]
                        assert "Limpieza completada" in first_call[0]

                        # Segunda llamada: generación
                        second_call = mock_exito.call_args_list[1][0]
                        assert "Asignación generada" in second_call[0]


# ========================================
# TESTS DE RENDIMIENTO
# ========================================


class TestAsignacionGuardiasFormRendimiento:
    """Tests de rendimiento del formulario"""

    def test_carga_inicial_rapida(self, qtbot, session, configuracion, zonas, profesores):
        """Test que la carga inicial es rápida (<500ms)"""
        import time

        start = time.time()
        form = AsignacionGuardiasForm(session)
        elapsed = time.time() - start

        assert elapsed < 0.5  # Menos de 500ms
        assert "Días lectivos" in form.stats_text.toPlainText()

    def test_calcular_distribucion_rapida(
        self, qtbot, session, configuracion, zonas, profesores
    ):
        """Test que calcular distribución es rápido (<1s)"""
        import time

        form = AsignacionGuardiasForm(session)

        start = time.time()
        with patch.object(form, "calcular_distribucion_uc") as mock_uc:
            mock_distribucion = Mock()
            mock_distribucion.distribucion = {profesores[0].id: 100}
            mock_distribucion.total_guardias = 100
            mock_distribucion.slots_totales = 360
            mock_distribucion.es_exacta = False
            mock_distribucion.diferencia = 260

            mock_uc.execute.return_value = mock_distribucion

            form.calcular_distribucion()

        elapsed = time.time() - start

        assert elapsed < 1.0  # Menos de 1 segundo
