"""Tests de UI del cálculo y la generación de guardias.

Cubren la superficie que la aplicación registra de verdad: `AsignacionCalculoForm`
y sus dos paneles. Antes apuntaban a `AsignacionGuardiasForm`, un formulario que
no está en ninguna vista (QA-003): la cobertura era ilusoria.
"""

from datetime import date, time
from unittest.mock import Mock, patch

import pytest
from PyQt6.QtWidgets import QApplication, QMessageBox

from infrastructure.database.models import Configuracion, Guardia, Profesor, Zona
from presentation.forms.asignacion_calculo_form import AsignacionCalculoForm


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
    f = AsignacionCalculoForm(session)
    QApplication.processEvents()
    yield f
    f.close()


@pytest.fixture
def form_sin_config(qapp, session):
    f = AsignacionCalculoForm(session)
    QApplication.processEvents()
    yield f
    f.close()


class TestAsignacionRenderizado:
    def test_form_tiene_los_dos_paneles(self, form):
        assert form.calculo_panel is not None
        assert form.generacion_panel is not None

    def test_paneles_muestran_texto_de_solo_lectura(self, form):
        assert form.calculo_panel.content_text.isReadOnly()
        assert form.generacion_panel.content_text.isReadOnly()

    def test_estadisticas_se_pintan_con_configuracion(self, form):
        assert form.calculo_panel.content_text.toPlainText().strip()

    def test_sin_configuracion_no_revienta(self, form_sin_config):
        # Muestra el error o el mensaje inicial, pero pinta algo y no lanza.
        assert form_sin_config.calculo_panel.content_text.toPlainText().strip()


class TestGuardarrailDeGeneracion:
    def test_generar_arranca_deshabilitado(self, form):
        """Sin cuotas calculadas no se puede generar."""
        assert not form.generacion_panel.generar_button.isEnabled()
        assert "calcular las cuotas" in form.generacion_panel.generar_button.toolTip()

    def test_calcular_cuotas_habilita_generar(self, form):
        """La señal del panel de cálculo es la que abre la puerta a generar."""
        form.calculo_panel.cuotas_calculadas.emit({})
        QApplication.processEvents()
        assert form.generacion_panel.generar_button.isEnabled()

    def test_boton_calcular_esta_conectado(self, qapp, session, configuracion):
        """El botón dispara `calcular_cuotas`.

        Se parchea antes de construir el panel: Qt guarda el método ya enlazado al
        conectar la señal, así que sustituirlo después no intercepta nada.
        """
        from presentation.forms.asignacion_widgets.calculo_panel import CalculoPanel

        with patch.object(CalculoPanel, "calcular_cuotas") as mock_calc:
            panel = CalculoPanel(session)
            panel.calcular_button.click()
            QApplication.processEvents()

        mock_calc.assert_called_once()
        panel.close()


class TestGeneracion:
    def test_generar_con_caso_de_uso_simulado(self, form):
        """Generar pinta resultados y ofrece el envío de emails, sin tocar el solver."""
        resumen = Mock()
        resumen.guardias_generadas = 50
        resumen.slots_esperados = 50
        resumen.slots_sin_cubrir = 0
        resumen.resumen_por_profesor = {}
        resumen.mensaje = "OK"

        panel = form.generacion_panel
        with patch.object(panel, "generar_guardias_uc") as mock_uc:
            mock_uc.execute.return_value = resumen
            with patch(
                "presentation.forms.asignacion_widgets.generacion_panel.ejecutar_con_progreso",
                return_value=resumen,
                create=True,
            ):
                with patch(
                    "presentation.widgets.progress_indicators.ejecutar_con_progreso",
                    return_value=resumen,
                ):
                    panel._generar_guardias()
                    QApplication.processEvents()

        assert panel.btn_notificar.isVisible() or panel.content_text.toPlainText().strip()

    def test_cambiar_algoritmo_no_rompe(self, form):
        combo = form.generacion_panel.algoritmo_combo
        assert combo.count() > 0
        for i in range(combo.count()):
            combo.setCurrentIndex(i)
            QApplication.processEvents()


class TestLimpieza:
    def _crear_guardia(self, session):
        zona = session.query(Zona).first()
        prof = session.query(Profesor).first()
        session.add(
            Guardia(
                profesor_id=prof.id,
                zona_id=zona.id,
                fecha=date(2025, 1, 10),
                turno="mañana",
                recreo=1,
            )
        )
        session.commit()

    def test_limpiar_confirmado_borra(self, form, session):
        self._crear_guardia(session)
        assert session.query(Guardia).count() == 1

        with patch.object(QMessageBox, "exec", return_value=QMessageBox.StandardButton.Yes):
            form.generacion_panel._limpiar_guardias()
            QApplication.processEvents()

        session.expire_all()
        assert session.query(Guardia).count() == 0

    def test_limpiar_cancelado_conserva(self, form, session):
        self._crear_guardia(session)
        n_inicial = session.query(Guardia).count()

        with patch.object(QMessageBox, "exec", return_value=QMessageBox.StandardButton.No):
            form.generacion_panel._limpiar_guardias()
            QApplication.processEvents()

        session.expire_all()
        assert session.query(Guardia).count() == n_inicial
