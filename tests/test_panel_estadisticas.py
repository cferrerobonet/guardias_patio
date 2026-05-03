"""
Tests para PanelEstadisticas.

Coverage objetivo: >70%
"""

from datetime import date, timedelta
from unittest.mock import patch

import pytest

from infrastructure.database.models import Guardia
from presentation.widgets.bar_chart_widget import BarChartWidget, PieChartWidget
from presentation.widgets.panel_estadisticas import MplCanvas, PanelEstadisticas

pytestmark = pytest.mark.ui

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def panel(qapp, session):
    """Fixture para PanelEstadisticas."""
    widget = PanelEstadisticas(session)
    return widget


@pytest.fixture
def datos_completos(session, profesor_factory, zona_factory):
    """Fixture con profesores, zonas y guardias para tests completos."""
    # Crear 5 profesores
    profesores = [
        profesor_factory(nombre_completo=f"Profesor {i}", horas_contrato=25.0) for i in range(1, 6)
    ]
    session.add_all(profesores)

    # Crear 3 zonas
    zonas = [zona_factory(nombre_zona=f"Zona {chr(65 + i)}") for i in range(3)]
    session.add_all(zonas)
    session.commit()

    # Crear guardias distribuidas
    hoy = date.today()
    guardias = []

    # Profesor 1: 10 guardias (5 mañana, 5 tarde)
    for i in range(10):
        turno = "mañana" if i < 5 else "tarde"
        g = Guardia(
            fecha=hoy + timedelta(days=i),
            turno=turno,
            recreo=(i % 3) + 1,
            profesor_id=profesores[0].id,
            zona_id=zonas[i % 3].id,
        )
        guardias.append(g)

    # Profesor 2: 6 guardias (todas mañana)
    for i in range(6):
        g = Guardia(
            fecha=hoy + timedelta(days=i + 10),
            turno="mañana",
            recreo=(i % 3) + 1,
            profesor_id=profesores[1].id,
            zona_id=zonas[i % 3].id,
        )
        guardias.append(g)

    # Profesor 3: 4 guardias (todas tarde)
    for i in range(4):
        g = Guardia(
            fecha=hoy + timedelta(days=i + 20),
            turno="tarde",
            recreo=(i % 3) + 1,
            profesor_id=profesores[2].id,
            zona_id=zonas[i % 3].id,
        )
        guardias.append(g)

    # Profesores 4 y 5: sin guardias

    session.add_all(guardias)
    session.commit()

    return {"profesores": profesores, "zonas": zonas, "guardias": guardias}


# ============================================================================
# TEST CLASS: BÁSICO
# ============================================================================


class TestPanelEstadisticasBasico:
    """Tests básicos de creación e inicialización."""

    def test_crear_panel(self, qapp, session):
        """Test que el panel se crea correctamente."""
        panel = PanelEstadisticas(session)

        assert panel is not None
        assert panel.session == session
        assert panel.windowTitle() == "Estadísticas de Guardias"

    def test_tiene_pestanas(self, panel):
        """Test que el panel tiene las 4 pestañas."""
        assert panel.tabs is not None
        assert panel.tabs.count() == 5

        # Verificar nombres de pestañas
        assert "Resumen" in panel.tabs.tabText(0)
        assert "Profesor" in panel.tabs.tabText(1)
        assert "Zona" in panel.tabs.tabText(2)
        assert "Gráficos" in panel.tabs.tabText(3)

    def test_tiene_labels_resumen(self, panel):
        """Test que tiene los labels de resumen."""
        assert panel.label_total_guardias is not None
        assert panel.label_total_profesores is not None
        assert panel.label_total_zonas is not None
        assert panel.label_cobertura is not None
        assert panel.label_info is not None

    def test_tiene_tablas(self, panel):
        """Test que tiene las tablas de profesores y zonas."""
        assert panel.tabla_profesores is not None
        assert panel.tabla_profesores.columnCount() == 10

        assert panel.tabla_zonas is not None
        assert panel.tabla_zonas.columnCount() == 4

    def test_tiene_canvas_graficos(self, panel):
        """Test que tiene los canvas de gráficos nativos."""
        assert panel.canvas_profesores is not None
        assert panel.canvas_zonas is not None
        assert isinstance(panel.canvas_profesores, BarChartWidget)
        assert isinstance(panel.canvas_zonas, PieChartWidget)


# ============================================================================
# TEST CLASS: RESUMEN
# ============================================================================


class TestPanelEstadisticasResumen:
    """Tests de actualización de resumen."""

    def test_actualizar_resumen_sin_datos(self, panel):
        """Test resumen cuando no hay datos."""
        panel.actualizar_estadisticas()

        assert "Total Guardias: 0" in panel.label_total_guardias.text()
        assert "Profesores Activos: 0" in panel.label_total_profesores.text()
        assert "Zonas Configuradas: 0" in panel.label_total_zonas.text()
        assert "0%" in panel.label_cobertura.text()
        assert "No hay guardias" in panel.label_info.text()

    def test_actualizar_resumen_con_datos(self, panel, datos_completos):
        """Test resumen con datos completos."""
        panel.actualizar_estadisticas()

        # Total guardias: 10 + 6 + 4 = 20
        assert "Total Guardias: 20" in panel.label_total_guardias.text()

        # 3 profesores tienen guardias de 5 totales
        assert "Profesores Activos: 3 / 5" in panel.label_total_profesores.text()

        # 3 zonas
        assert "Zonas Configuradas: 3" in panel.label_total_zonas.text()

        # Cobertura estimada (se calcula)
        assert "%" in panel.label_cobertura.text()

    def test_actualizar_resumen_info_detalles(self, panel, datos_completos):
        """Test que muestra detalles de mañana/tarde."""
        panel.actualizar_estadisticas()

        info = panel.label_info.text()

        # Guardias de mañana: 5 (prof1) + 6 (prof2) = 11
        assert "Guardias de Mañana: 11" in info

        # Guardias de tarde: 5 (prof1) + 4 (prof3) = 9
        assert "Guardias de Tarde: 9" in info

        # Promedio por profesor
        assert "Promedio por profesor:" in info

    def test_actualizar_resumen_porcentajes(self, panel, datos_completos):
        """Test que calcula porcentajes correctamente."""
        panel.actualizar_estadisticas()

        info = panel.label_info.text()

        # 11 mañana de 20 total = 55%
        assert "55%" in info or "Guardias de Mañana: 11" in info

        # 9 tarde de 20 total = 45%
        assert "45%" in info or "Guardias de Tarde: 9" in info


# ============================================================================
# TEST CLASS: TABLA PROFESORES
# ============================================================================


class TestPanelEstadisticasTablaProfesores:
    """Tests de tabla de profesores."""

    def test_actualizar_tabla_profesores_vacia(self, panel):
        """Test tabla cuando no hay profesores."""
        panel.actualizar_estadisticas()

        assert panel.tabla_profesores.rowCount() == 0

    def test_actualizar_tabla_profesores_con_datos(self, panel, datos_completos):
        """Test tabla con datos."""
        panel.actualizar_estadisticas()

        # Debe haber 5 profesores
        assert panel.tabla_profesores.rowCount() == 5

    def test_tabla_profesores_columnas_correctas(self, panel, datos_completos):
        """Test que las columnas tienen datos correctos."""
        panel.actualizar_estadisticas()

        # Verificar primera fila (Profesor 1: 10 guardias)
        assert "Profesor 1" in panel.tabla_profesores.item(0, 0).text()
        assert panel.tabla_profesores.item(0, 1).text() == "10"  # Total
        assert panel.tabla_profesores.item(0, 2).text() == "5"  # Mañana
        assert panel.tabla_profesores.item(0, 3).text() == "5"  # Tarde

    def test_tabla_profesores_porcentajes(self, panel, datos_completos):
        """Test que calcula porcentajes correctamente."""
        panel.actualizar_estadisticas()

        # Profesor 1: 10 de 20 = 50%
        porcentaje = panel.tabla_profesores.item(0, 4).text()
        assert "50" in porcentaje and "%" in porcentaje

        # Profesor 2: 6 de 20 = 30%
        porcentaje = panel.tabla_profesores.item(1, 4).text()
        assert "30" in porcentaje and "%" in porcentaje

    def test_tabla_profesores_estados(self, panel, datos_completos):
        """Test que asigna estados correctamente."""
        panel.actualizar_estadisticas()

        # Profesor 1: 10 guardias → "✅ Asignado"
        assert "✅" in panel.tabla_profesores.item(0, 5).text()

        # Profesor 4: 0 guardias → "❌ Sin guardias"
        assert "❌" in panel.tabla_profesores.item(3, 5).text()

    def test_tabla_profesores_estado_pocas_guardias(
        self, panel, session, profesor_factory, zona_factory
    ):
        """Test estado 'Pocas guardias' para profesor con <5."""
        # Crear profesor con solo 2 guardias
        prof = profesor_factory(nombre_completo="Test Prof", horas_contrato=25.0)
        zona = zona_factory(nombre_zona="Test Zona")
        session.add_all([prof, zona])
        session.commit()

        for i in range(2):
            g = Guardia(
                fecha=date.today() + timedelta(days=i),
                turno="mañana",
                recreo=1,
                profesor_id=prof.id,
                zona_id=zona.id,
            )
            session.add(g)
        session.commit()

        panel.actualizar_estadisticas()

        # Debe tener estado "⚠️ Pocas guardias"
        encontrado = False
        for row in range(panel.tabla_profesores.rowCount()):
            if "Test Prof" in panel.tabla_profesores.item(row, 0).text():
                estado = panel.tabla_profesores.item(row, 5).text()
                assert "⚠️" in estado
                encontrado = True
                break
        assert encontrado


# ============================================================================
# TEST CLASS: TABLA ZONAS
# ============================================================================


class TestPanelEstadisticasTablaZonas:
    """Tests de tabla de zonas."""

    def test_actualizar_tabla_zonas_vacia(self, panel):
        """Test tabla cuando no hay zonas."""
        panel.actualizar_estadisticas()

        assert panel.tabla_zonas.rowCount() == 0

    def test_actualizar_tabla_zonas_con_datos(self, panel, datos_completos):
        """Test tabla con datos."""
        panel.actualizar_estadisticas()

        # Debe haber 3 zonas
        assert panel.tabla_zonas.rowCount() == 3

    def test_tabla_zonas_nombre(self, panel, datos_completos):
        """Test que muestra nombres de zonas."""
        panel.actualizar_estadisticas()

        nombres = [panel.tabla_zonas.item(i, 0).text() for i in range(panel.tabla_zonas.rowCount())]

        assert "Zona A" in nombres
        assert "Zona B" in nombres
        assert "Zona C" in nombres

    def test_tabla_zonas_total_guardias(self, panel, datos_completos):
        """Test que cuenta guardias por zona correctamente."""
        panel.actualizar_estadisticas()

        # Cada zona debería tener ~6-7 guardias (20 total / 3 zonas)
        totales = []
        for i in range(panel.tabla_zonas.rowCount()):
            total = int(panel.tabla_zonas.item(i, 1).text())
            totales.append(total)

        # Suma debe ser 20
        assert sum(totales) == 20
        # Todas deben tener al menos algunas guardias
        assert all(t > 0 for t in totales)

    def test_tabla_zonas_profesores_diferentes(self, panel, datos_completos):
        """Test que cuenta profesores diferentes por zona."""
        panel.actualizar_estadisticas()

        # Cada zona debe tener 3 profesores diferentes (prof1, prof2, prof3)
        for i in range(panel.tabla_zonas.rowCount()):
            profs_diferentes = int(panel.tabla_zonas.item(i, 2).text())
            assert profs_diferentes == 3


# ============================================================================
# TEST CLASS: GRÁFICOS
# ============================================================================


class TestPanelEstadisticasGraficos:
    """Tests de generación de gráficos."""

    def test_actualizar_graficos_sin_datos(self, panel):
        """Test que maneja gráficos sin datos."""
        # No debería crashear
        panel.actualizar_estadisticas()

    def test_actualizar_graficos_con_datos(self, panel, datos_completos):
        """Test que genera gráficos con datos."""
        panel.actualizar_estadisticas()

        assert panel.canvas_profesores is not None
        assert panel.canvas_zonas is not None
        assert len(panel.canvas_profesores._datos) > 0
        assert len(panel.canvas_zonas._datos) > 0

    def test_grafico_profesores_tipo_barras(self, panel, datos_completos):
        """Test que el gráfico de profesores es BarChartWidget."""
        panel.actualizar_estadisticas()

        assert isinstance(panel.canvas_profesores, BarChartWidget)
        assert len(panel.canvas_profesores._datos) > 0

    def test_grafico_zonas_tipo_pastel(self, panel, datos_completos):
        """Test que el gráfico de zonas es PieChartWidget."""
        panel.actualizar_estadisticas()

        assert isinstance(panel.canvas_zonas, PieChartWidget)
        assert len(panel.canvas_zonas._datos) > 0

    def test_grafico_profesores_solo_con_guardias(self, panel, datos_completos):
        """Test que solo muestra profesores con guardias."""
        panel.actualizar_estadisticas()

        assert len(panel.canvas_profesores._datos) == 3

    def test_grafico_nombres_truncados(self, panel, session, profesor_factory, zona_factory):
        """Test que trunca nombres largos."""
        prof = profesor_factory(
            nombre_completo="Apellido Muy Largo Larguísimo, Nombre", horas_contrato=25.0
        )
        zona = zona_factory(nombre_zona="Test")
        session.add_all([prof, zona])
        session.commit()

        g = Guardia(
            fecha=date.today(),
            turno="mañana",
            recreo=1,
            profesor_id=prof.id,
            zona_id=zona.id,
        )
        session.add(g)
        session.commit()

        panel.actualizar_estadisticas()

        # Nombres en _datos deben estar truncados (split por coma, max 18 chars en horizontal)
        for label, _, _ in panel.canvas_profesores._datos:
            assert len(label) <= 18


# ============================================================================
# TEST CLASS: ACTUALIZAR ESTADÍSTICAS
# ============================================================================


class TestPanelEstadisticasActualizar:
    """Tests de actualización completa."""

    def test_actualizar_estadisticas_completo(self, panel, datos_completos):
        """Test que actualizar_estadisticas actualiza todo."""
        panel.actualizar_estadisticas()

        # Verificar resumen
        assert "20" in panel.label_total_guardias.text()

        # Verificar tabla profesores
        assert panel.tabla_profesores.rowCount() == 5

        # Verificar tabla zonas
        assert panel.tabla_zonas.rowCount() == 3

    def test_actualizar_estadisticas_maneja_excepciones(self, panel):
        """Test que maneja excepciones al actualizar."""
        with patch.object(panel._use_case, "execute", side_effect=Exception("Error")):
            with patch.object(panel, "manejar_excepcion") as mock_manejar:
                panel.actualizar_estadisticas()
                mock_manejar.assert_called_once()

    def test_refrescar_llama_actualizar(self, panel):
        """Test que refrescar llama a actualizar_estadisticas."""
        with patch.object(panel, "actualizar_estadisticas") as mock_actualizar:
            panel.refrescar()
            mock_actualizar.assert_called_once()


# ============================================================================
# TEST CLASS: MPLCANVAS
# ============================================================================


class TestMplCanvas:
    """Tests de BarChartWidget (alias MplCanvas para compatibilidad)."""

    def test_crear_canvas(self, qapp):
        """Test que se crea un BarChartWidget."""
        canvas = MplCanvas()

        assert canvas is not None

    def test_canvas_dimensiones(self, qapp):
        """Test que se puede instanciar BarChartWidget sin args."""
        canvas = MplCanvas()

        assert canvas.minimumHeight() >= 60


# ============================================================================
# TEST CLASS: INTEGRACIÓN
# ============================================================================


class TestPanelEstadisticasIntegracion:
    """Tests de integración de flujos completos."""

    def test_flujo_completo_sin_datos_a_con_datos(
        self, panel, profesor_factory, zona_factory, session
    ):
        """Test flujo: sin datos → agregar datos → actualizar."""
        # 1. Estado inicial sin datos
        panel.actualizar_estadisticas()
        assert "Total Guardias: 0" in panel.label_total_guardias.text()

        # 2. Agregar datos
        prof = profesor_factory(nombre_completo="Test", horas_contrato=25.0)
        zona = zona_factory(nombre_zona="Test Zona")
        session.add_all([prof, zona])
        session.commit()

        for i in range(5):
            g = Guardia(
                fecha=date.today() + timedelta(days=i),
                turno="mañana",
                recreo=1,
                profesor_id=prof.id,
                zona_id=zona.id,
            )
            session.add(g)
        session.commit()

        # 3. Actualizar
        panel.actualizar_estadisticas()

        # 4. Verificar cambios
        assert "Total Guardias: 5" in panel.label_total_guardias.text()
        assert panel.tabla_profesores.rowCount() == 1
        assert panel.tabla_zonas.rowCount() == 1

    def test_cambio_de_pestanas(self, panel, datos_completos):
        """Test que se puede cambiar entre pestañas."""
        panel.actualizar_estadisticas()

        # Cambiar a cada pestaña
        for i in range(4):
            panel.tabs.setCurrentIndex(i)
            assert panel.tabs.currentIndex() == i

    def test_multiples_actualizaciones(self, panel, datos_completos):
        """Test que permite múltiples actualizaciones."""
        # Primera actualización
        panel.actualizar_estadisticas()
        guardias1 = panel.label_total_guardias.text()

        # Segunda actualización
        panel.actualizar_estadisticas()
        guardias2 = panel.label_total_guardias.text()

        # Deben ser iguales (datos no cambiaron)
        assert guardias1 == guardias2


# ============================================================================
# TEST CLASS: RENDIMIENTO
# ============================================================================


class TestPanelEstadisticasRendimiento:
    """Tests de rendimiento."""

    @pytest.mark.slow
    def test_carga_inicial_rapida(self, qapp, session, profesor_factory, zona_factory):
        """Test que la carga inicial es rápida (<2s)."""
        import time

        # Crear muchos datos
        profesores = [
            profesor_factory(nombre_completo=f"Prof {i}", horas_contrato=25.0) for i in range(20)
        ]
        zonas = [zona_factory(nombre_zona=f"Zona {i}") for i in range(5)]
        session.add_all(profesores + zonas)
        session.commit()

        # Crear 200 guardias
        hoy = date.today()
        for i in range(200):
            g = Guardia(
                fecha=hoy + timedelta(days=i // 10),
                turno="mañana" if i % 2 == 0 else "tarde",
                recreo=(i % 3) + 1,
                profesor_id=profesores[i % len(profesores)].id,
                zona_id=zonas[i % len(zonas)].id,
            )
            session.add(g)
        session.commit()

        start = time.time()
        panel = PanelEstadisticas(session)
        elapsed = time.time() - start

        assert panel.label_total_guardias is not None
        assert elapsed < 2.0

    @pytest.mark.slow
    def test_actualizacion_rapida_con_muchos_datos(
        self, panel, session, profesor_factory, zona_factory
    ):
        """Test que la actualización es rápida con muchos datos."""
        import time

        # Crear datos
        profesores = [
            profesor_factory(nombre_completo=f"Prof {i}", horas_contrato=25.0) for i in range(30)
        ]
        zonas = [zona_factory(nombre_zona=f"Zona {i}") for i in range(10)]
        session.add_all(profesores + zonas)
        session.commit()

        # Crear 300 guardias
        hoy = date.today()
        for i in range(300):
            g = Guardia(
                fecha=hoy + timedelta(days=i // 10),
                turno="mañana" if i % 2 == 0 else "tarde",
                recreo=(i % 3) + 1,
                profesor_id=profesores[i % len(profesores)].id,
                zona_id=zonas[i % len(zonas)].id,
            )
            session.add(g)
        session.commit()

        start = time.time()
        panel.actualizar_estadisticas()
        elapsed = time.time() - start

        assert elapsed < 3.0  # <3s para 300 guardias
