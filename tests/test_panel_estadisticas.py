"""
Tests para PanelEstadisticas.

Coverage objetivo: >70%
"""

from datetime import date, timedelta
from unittest.mock import patch

import pytest

from infrastructure.database.models import Guardia
from presentation.widgets.bar_chart_widget import BarChartWidget, DivergingBarChartWidget
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


@pytest.fixture
def con_cuotas(session, datos_completos):
    """Configuración del curso y cuotas conocidas: 5, 6, 4, 0 y 5 (suman 20)."""
    from datetime import time
    from unittest.mock import patch

    from infrastructure.database.models import Configuracion

    session.add(
        Configuracion(
            anio_inicio_curso=2026, fecha_inicio_curso=date(2026, 9, 7),
            fecha_fin_curso=date(2027, 6, 18), hora_recreo1_manana=time(10, 45),
            hora_recreo2_manana=time(12, 35),
        )
    )
    session.commit()
    ids = [p.id for p in datos_completos["profesores"]]
    cuotas = dict(zip(ids, (5, 6, 4, 0, 5)))
    with patch(
        "services.distribucion_cuotas_service.DistribucionCuotasService.calcular_cuotas",
        return_value=cuotas,
    ):
        yield cuotas


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
        assert panel.tabla_profesores.columnCount() == 11

        assert panel.tabla_zonas is not None
        assert panel.tabla_zonas.columnCount() == 4

    def test_tiene_canvas_graficos(self, panel):
        """Diferencia con la cuota (divergente) y sustituciones (barras): sin tarta."""
        assert isinstance(panel.canvas_diferencias, DivergingBarChartWidget)
        assert isinstance(panel.canvas_sustitutos, BarChartWidget)
        assert not hasattr(panel, "canvas_zonas")

# ============================================================================
# TEST CLASS: RESUMEN
# ============================================================================


class TestPanelEstadisticasResumen:
    """Tests de actualización de resumen."""

    def test_actualizar_resumen_sin_datos(self, panel):
        """Test resumen cuando no hay datos."""
        panel.actualizar_estadisticas()

        assert "Guardias del curso: 0" in panel.label_total_guardias.text()
        assert "Profesores con guardias: 0" in panel.label_total_profesores.text()
        assert "no hay guardias" in panel.label_total_zonas.text()
        assert "0%" in panel.label_cobertura.text()
        assert "No hay guardias" in panel.label_info.text()

    def test_actualizar_resumen_con_datos(self, panel, datos_completos):
        """Sin configuración no hay cuotas: se dice, en vez de inventar una cobertura."""
        panel.actualizar_estadisticas()

        assert "Guardias del curso: 20" in panel.label_total_guardias.text()
        assert "Profesores con guardias: 3 de 5" in panel.label_total_profesores.text()
        assert "sin configuración" in panel.label_total_zonas.text()
        assert "sin ranuras" in panel.label_cobertura.text()

    def test_actualizar_resumen_info_detalles(self, panel, datos_completos):
        """Test que muestra detalles de mañana/tarde y sustituciones."""
        panel.actualizar_estadisticas()

        info = panel.label_info.text()
        assert "Mañana: 11 (55%)" in info
        assert "Tarde: 9 (45%)" in info
        assert "Sustituciones: 0" in info

    def test_resumen_con_cuotas(self, panel, datos_completos, con_cuotas):
        """Con cuotas: ranuras del curso, cobertura real y quién se separa más."""
        panel.actualizar_estadisticas()

        assert "20 de 20 ranuras" in panel.label_total_guardias.text()
        assert "Cobertura del curso: 100%" in panel.label_cobertura.text()
        reparto = panel.label_total_zonas.text()
        assert "2 profesores se separan" in reparto and "+5 (Profesor 1)" in reparto

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

        assert "Profesor 1" in panel.tabla_profesores.item(0, 0).text()
        assert panel.tabla_profesores.item(0, 1).text() == "—"  # Cuota: sin configuración
        assert panel.tabla_profesores.item(0, 2).text() == "10"  # Asignadas
        assert panel.tabla_profesores.item(0, 4).text() == "5"  # Mañana
        assert panel.tabla_profesores.item(0, 5).text() == "5"  # Tarde

    def test_tabla_profesores_cuota_y_diferencia(self, panel, datos_completos, con_cuotas):
        """La tabla compara con la cuota de cada uno, no con el total."""
        panel.actualizar_estadisticas()

        fila = {
            panel.tabla_profesores.item(r, 0).text(): r
            for r in range(panel.tabla_profesores.rowCount())
        }
        uno, cinco = fila["Profesor 1"], fila["Profesor 5"]
        assert panel.tabla_profesores.item(uno, 1).text() == "5"
        assert panel.tabla_profesores.item(uno, 3).text() == "+5"
        assert "5 por encima" in panel.tabla_profesores.item(uno, 6).text()
        assert panel.tabla_profesores.item(cinco, 3).text() == "-5"
        assert "5 por debajo" in panel.tabla_profesores.item(cinco, 6).text()
        assert "En su cuota" in panel.tabla_profesores.item(fila["Profesor 3"], 6).text()

    def test_tabla_profesores_estados(self, panel, datos_completos):
        """Test que asigna estados correctamente."""
        panel.actualizar_estadisticas()

        # Profesor 1: 10 guardias → "✅ Asignado"
        assert "✅" in panel.tabla_profesores.item(0, 6).text()

        # Profesor 4: 0 guardias → "❌ Sin guardias"
        assert "❌" in panel.tabla_profesores.item(3, 6).text()

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
                estado = panel.tabla_profesores.item(row, 6).text()
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

    def test_actualizar_graficos_con_datos(self, panel, datos_completos, con_cuotas):
        """El gráfico de diferencias va de más por debajo a más por encima."""
        panel.actualizar_estadisticas()

        valores = [valor for _, valor in panel.canvas_diferencias._datos]
        assert valores == sorted(valores)
        assert valores[0] == -5 and valores[-1] == 5

    def test_sin_cuotas_no_hay_grafico_de_diferencias(self, panel, datos_completos):
        """Sin configuración no se puede comparar: el gráfico dice que no hay datos."""
        panel.actualizar_estadisticas()

        assert panel.canvas_diferencias._datos == []
        assert "sin datos" in panel.canvas_diferencias.accessibleDescription()

    def test_grafico_de_sustitutos(self, panel, session, datos_completos):
        """Quién ha cubierto más sustituciones, de un solo color."""
        profesores = datos_completos["profesores"]
        guardia = datos_completos["guardias"][0]
        guardia.es_sustitucion = True
        guardia.profesor_sustituido_id = profesores[3].id
        session.commit()

        panel.actualizar_estadisticas()

        assert panel.canvas_sustitutos._datos == [("Profesor 1", 1, "")]
        assert "Sustituciones: 1 (5% de las guardias)" in panel.label_info.text()

    def test_grafico_diferencias_incluye_a_todos_los_que_tienen_cuota(
        self, panel, datos_completos, con_cuotas
    ):
        """También los que no tienen guardias: son los que más importan."""
        panel.actualizar_estadisticas()

        assert len(panel.canvas_diferencias._datos) == 5

    def test_grafico_lleva_el_nombre_completo(self, panel, datos_completos, con_cuotas):
        """Nombres completos: recortar el apellido a 15 letras repetía nombres."""
        panel.actualizar_estadisticas()

        nombres = {nombre for nombre, _ in panel.canvas_diferencias._datos}
        assert "Profesor 1" in nombres

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
        assert "Guardias del curso: 0" in panel.label_total_guardias.text()

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
        assert "Guardias del curso: 5" in panel.label_total_guardias.text()
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
