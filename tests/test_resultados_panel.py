"""
Tests para ResultadosPanel.

Este módulo contiene tests para la funcionalidad de mostrar resultados
de generación de guardias con métricas de equidad.
"""

from dataclasses import dataclass

import pytest
from presentation.forms.asignacion_widgets.resultados_panel import ResultadosPanel
from PyQt6.QtWidgets import QTextEdit


@dataclass
class MockResumenGeneracion:
    """Mock del DTO de resumen de generación."""

    guardias_generadas: int = 0
    slots_esperados: int = 0
    cobertura_completa: bool = False
    slots_sin_cubrir: int = 0
    resumen_por_profesor: dict = None

    def __post_init__(self):
        if self.resumen_por_profesor is None:
            self.resumen_por_profesor = {}


@pytest.fixture
def panel(qtbot, session):
    """Fixture que crea un ResultadosPanel."""
    panel = ResultadosPanel(session)
    qtbot.addWidget(panel)
    return panel


@pytest.fixture
def panel_con_profesores(qtbot, session, profesor_factory):
    """Fixture con profesores para testear top 10."""
    profesores = []
    for i in range(15):
        prof = profesor_factory(nombre_completo=f"Profesor Test {i+1}")
        profesores.append(prof)

    panel = ResultadosPanel(session)
    qtbot.addWidget(panel)
    return panel, profesores


# ========================================
# TESTS DE ESTRUCTURA DEL PANEL
# ========================================


class TestResultadosPanelEstructura:
    """Tests de estructura básica del panel."""

    def test_panel_se_crea(self, panel):
        """Test: El panel se crea correctamente."""
        assert panel is not None
        assert isinstance(panel, ResultadosPanel)

    def test_texto_resultado_presente(self, panel):
        """Test: El área de texto está presente."""
        assert panel.resultado_text is not None
        assert isinstance(panel.resultado_text, QTextEdit)
        assert panel.resultado_text.isReadOnly()

    def test_titulo_panel(self, panel):
        """Test: El panel tiene título."""
        assert "Resultados" in panel.title() or "📈" in panel.title()

    def test_mensaje_inicial(self, panel):
        """Test: El panel muestra mensaje inicial."""
        texto = panel.resultado_text.toPlainText()
        assert "Generar Asignación" in texto or "resultados" in texto.lower()


# ========================================
# TESTS DE MOSTRAR RESULTADOS
# ========================================


class TestResultadosPanelMostrarResultados:
    """Tests para el método mostrar_resultados."""

    def test_mostrar_resultados_cobertura_completa(self, panel):
        """Test: Resumen con cobertura completa se muestra correctamente."""
        mock_resumen = MockResumenGeneracion(
            guardias_generadas=100,
            slots_esperados=100,
            cobertura_completa=True,
            slots_sin_cubrir=0,
            resumen_por_profesor={},
        )

        panel.mostrar_resultados(mock_resumen)

        texto = panel.resultado_text.toPlainText()
        # Debe mostrar guardias generadas
        assert "100" in texto
        # Debe mostrar cobertura completa
        assert "✅" in texto or "completa" in texto.lower()

    def test_mostrar_resultados_sin_cobertura_completa(self, panel):
        """Test: Resumen sin cobertura completa muestra advertencia."""
        mock_resumen = MockResumenGeneracion(
            guardias_generadas=80,
            slots_esperados=100,
            cobertura_completa=False,
            slots_sin_cubrir=20,
            resumen_por_profesor={},
        )

        panel.mostrar_resultados(mock_resumen)

        texto = panel.resultado_text.toPlainText()
        # Debe mostrar advertencia por slots sin cubrir
        assert "⚠️" in texto or "20" in texto

    def test_mostrar_resultados_top_10_profesores(self, panel_con_profesores):
        """Test: Resumen muestra top 10 profesores."""
        panel, profesores = panel_con_profesores

        # Crear resumen con 15 profesores
        resumen_por_profesor = {p.id: 10 - (i % 10) for i, p in enumerate(profesores)}
        mock_resumen = MockResumenGeneracion(
            guardias_generadas=100,
            slots_esperados=100,
            cobertura_completa=True,
            slots_sin_cubrir=0,
            resumen_por_profesor=resumen_por_profesor,
        )

        panel.mostrar_resultados(mock_resumen)

        texto = panel.resultado_text.toPlainText()
        # Debe mostrar sección de profesores
        assert "Profesor" in texto or "profesor" in texto.lower() or "top" in texto.lower()

    def test_mostrar_resultados_actualiza_texto(self, panel):
        """Test: mostrar_resultados actualiza el texto."""
        mock_resumen = MockResumenGeneracion(
            guardias_generadas=50,
            slots_esperados=100,
            cobertura_completa=False,
            slots_sin_cubrir=50,
        )

        panel.mostrar_resultados(mock_resumen)

        # El texto no debe estar vacío
        texto = panel.resultado_text.toPlainText()
        assert texto != ""
        assert "50" in texto

    def test_limpiar(self, panel):
        """Test: limpiar restaura el mensaje inicial."""
        mock_resumen = MockResumenGeneracion(
            guardias_generadas=50,
            slots_esperados=100,
        )
        panel.mostrar_resultados(mock_resumen)

        panel.limpiar()

        # Debe mostrar mensaje inicial (no vacío)
        texto = panel.resultado_text.toPlainText()
        assert "Generar Asignación" in texto or "resultados" in texto.lower()


# ========================================
# TESTS DE ROBUSTEZ
# ========================================


class TestResultadosPanelRobustez:
    """Tests de robustez."""

    def test_resumen_vacio(self, panel):
        """Test: Funciona con resumen vacío."""
        mock_resumen = MockResumenGeneracion()

        panel.mostrar_resultados(mock_resumen)

        texto = panel.resultado_text.toPlainText()
        assert texto != ""
        assert "0" in texto

    def test_resumen_sin_profesores(self, panel):
        """Test: Funciona sin profesores en el resumen."""
        mock_resumen = MockResumenGeneracion(
            guardias_generadas=10,
            slots_esperados=10,
            cobertura_completa=True,
        )

        panel.mostrar_resultados(mock_resumen)

        texto = panel.resultado_text.toPlainText()
        assert texto != ""


# ========================================
# TESTS DE INTEGRACIÓN DE EQUIDAD
# ========================================


class TestResultadosPanelEquidad:
    """Tests para la integración de métricas de equidad."""

    def test_muestra_seccion_equidad(self, panel):
        """Test: Muestra sección de análisis de equidad."""
        mock_resumen = MockResumenGeneracion(
            guardias_generadas=100,
            slots_esperados=100,
            cobertura_completa=True,
        )

        panel.mostrar_resultados(mock_resumen)

        texto = panel.resultado_text.toPlainText()
        # Debe intentar mostrar la sección de equidad
        assert "EQUIDAD" in texto.upper() or "equidad" in texto.lower() or "⚖️" in texto
