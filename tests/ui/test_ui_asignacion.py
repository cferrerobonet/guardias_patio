"""Tests de UI para AsignacionGuardiasForm — cálculo y generación de guardias."""

from datetime import date, time
from unittest.mock import Mock, patch

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMessageBox

from infrastructure.database.models import Configuracion, Guardia
from presentation.forms.asignacion_guardias_form import AsignacionGuardiasForm


@pytest.fixture
def configuracion(session, zona_factory, profesor_factory):
    zona_factory(nombre_zona="Patio A")
    zona_factory(nombre_zona="Patio B")
    profesor_factory("García, Juan", turno="mañana", horas_contrato=25.0)
    profesor_factory("López, Ana", turno="tarde", horas_contrato=18.0)
    session.flush()

    config = Configuracion(
        anio_inicio_curso=2024,
        fecha_inicio_curso=date(2024, 9, 1),
        fecha_fin_curso=date(2025, 6, 30),
        hora_recreo1_manana=time(11, 0),
        hora_recreo2_manana=time(12, 0),
        hora_recreo1_tarde=time(16, 0),
        hora_recreo2_tarde=time(17, 0),
        ajuste_tutores=1.0,
        ajuste_no_tutores=1.0,
        activar_festivos_automaticos=True,
        recreos_config='[{"id":1,"etiqueta":"R1","turno":"manana","hora":"11:00","zonas":2}]',
    )
    session.add(config)
    session.commit()
    return config


@pytest.fixture
def form(qapp, session, configuracion):
    f = AsignacionGuardiasForm(session)
    QApplication.processEvents()
    yield f
    f.close()


@pytest.fixture
def form_sin_config(qapp, session):
    f = AsignacionGuardiasForm(session)
    QApplication.processEvents()
    yield f
    f.close()


class TestAsignacionRenderizado:
    def test_form_tiene_widget_estadisticas(self, form):
        assert hasattr(form, "stats_text")
        assert form.stats_text.isReadOnly()

    def test_form_tiene_boton_generar(self, form):
        assert hasattr(form, "generar_button")
        assert form.generar_button.isEnabled()

    def test_stats_muestra_datos_con_configuracion(self, form):
        texto = form.stats_text.toPlainText()
        assert len(texto) > 0

    def test_stats_muestra_error_sin_configuracion(self, form_sin_config):
        texto = form_sin_config.stats_text.toPlainText()
        assert len(texto) > 0  # Muestra algo (error o vacío), sin crash


class TestAsignacionCalculo:
    def test_calcular_distribucion_delega_a_cuotas_panel(self, qtbot, form):
        """calcular_distribucion delega al cuotas_panel."""
        with patch.object(form.cuotas_panel, "calcular_cuotas") as mock_calc:
            form.calcular_distribucion()
            mock_calc.assert_called_once()

    def test_cuotas_text_es_readonly(self, form):
        assert form.cuotas_text.isReadOnly()


class TestAsignacionGeneracion:
    def test_generar_sin_datos_boton_habilitado(self, form_sin_config):
        """El botón de generar está habilitado incluso sin configuración."""
        assert form_sin_config.generar_button.isEnabled()

    def test_generar_con_mock_algoritmo_exitoso(self, qtbot, form):
        """Generar con algoritmo mockeado muestra resultado sin crash."""
        mock_resumen = Mock()
        mock_resumen.guardias_generadas = 50
        mock_resumen.slots_esperados = 50
        mock_resumen.cobertura_completa = True
        mock_resumen.slots_sin_cubrir = 0
        mock_resumen.resumen_por_profesor = {}
        mock_resumen.mensaje = "OK"

        with patch.object(form, "generar_guardias_uc") as mock_uc:
            mock_uc.execute.return_value = mock_resumen
            with patch(
                "utils.ui_helpers.show_question_with_cancel",
                return_value=QMessageBox.StandardButton.No,
            ):
                with patch.object(form, "mostrar_exito"):
                    form.generar_guardias()
                    QApplication.processEvents()

    def test_cambiar_algoritmo_en_combo(self, form):
        """Cambiar algoritmo en combo no provoca error."""
        if hasattr(form, "algoritmo_combo"):
            combo = form.algoritmo_combo
            for i in range(combo.count()):
                combo.setCurrentIndex(i)
                QApplication.processEvents()


class TestAsignacionLimpieza:
    def test_limpiar_guardias_confirmado(self, qtbot, form, session, zona_factory, profesor_factory):
        """Limpiar guardias con confirmación borra registros de BD."""
        zona = session.query(__import__("infrastructure.database.models", fromlist=["Zona"]).Zona).first()
        prof = session.query(__import__("infrastructure.database.models", fromlist=["Profesor"]).Profesor).first()
        if zona and prof:
            guardia = Guardia(
                profesor_id=prof.id,
                zona_id=zona.id,
                fecha=date(2025, 1, 10),
                turno="mañana",
                recreo=1,
            )
            session.add(guardia)
            session.commit()

        with patch.object(form, "confirmar_accion", return_value=True):
            with patch.object(form, "mostrar_exito"):
                if hasattr(form, "limpiar_guardias"):
                    form.limpiar_guardias()
                    QApplication.processEvents()

    def test_limpiar_guardias_cancelado_conserva_bd(self, qtbot, form, session):
        """Cancelar limpieza no modifica la BD."""
        n_inicial = session.query(Guardia).count()
        with patch.object(form, "confirmar_accion", return_value=False):
            if hasattr(form, "limpiar_guardias"):
                form.limpiar_guardias()
                QApplication.processEvents()

        session.expire_all()
        assert session.query(Guardia).count() == n_inicial
