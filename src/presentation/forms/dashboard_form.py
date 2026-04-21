"""
Dashboard de Métricas de Equidad

Panel de visualización con gráficos y métricas en tiempo real
sobre la distribución y equidad de guardias.

Funcionalidades:
- Histograma de guardias por profesor
- Evolución temporal del índice de equidad
- Distribución por turno y zona
- Métricas clave: Total guardias, cobertura, equidad promedio
"""

from datetime import datetime

import matplotlib.pyplot as plt
from application.dtos.domain_services_dtos import AnalisisEquidadRequest
from application.use_cases.analisis_equidad_use_case import AnalisisEquidadUseCase
from application.use_cases.calcular_cuotas_use_case import (
    CalcularCuotasRequest,
    CalcularCuotasUseCase,
)
from core.qt_imports import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from infrastructure.database.models import Configuracion, Guardia, Profesor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from utils import get_logger
from utils.icons import icon_for_button
from presentation.theme.tokens import Spacing

logger = get_logger(__name__)


class MetricaCard(QWidget):
    """Card para mostrar una métrica individual."""

    def __init__(self, titulo: str, valor: str, color: str = "#2196F3"):
        super().__init__()
        self.color = color
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)

        # Título
        titulo_label = QLabel(titulo)
        titulo_label.setStyleSheet("""
            font-size: 12px;
            color: #666;
            font-weight: bold;
        """)

        # Valor
        self.valor_label = QLabel(valor)
        self.valor_label.setStyleSheet(f"""
            font-size: 28px;
            color: {color};
            font-weight: bold;
            margin-top: 5px;
        """)

        layout.addWidget(titulo_label)
        layout.addWidget(self.valor_label)
        layout.addStretch()

        self.setLayout(layout)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: white;
                border: 2px solid {color};
                border-radius: 8px;
            }}
        """)
        self.setMinimumHeight(120)

    def actualizar_valor(self, valor: str):
        """Actualiza el valor de la métrica."""
        self.valor_label.setText(valor)


class GraficoCanvas(FigureCanvas):
    """Canvas para gráficos matplotlib."""

    def __init__(self, parent=None, width=8, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        self.fig.tight_layout(pad=2.0)


class DashboardForm(QWidget):
    """Dashboard principal con métricas y gráficos."""

    def __init__(self, session):
        super().__init__()
        self.session = session
        self.calcular_cuotas_uc = CalcularCuotasUseCase(session)
        self.analisis_equidad_uc = AnalisisEquidadUseCase(session)

        self._init_ui()
        self._cargar_datos()

    def _init_ui(self):
        """Inicializa la interfaz de usuario."""
        layout = QVBoxLayout()
        layout.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
        layout.setSpacing(Spacing.XL)

        # Scroll area para contenido
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        contenedor = QWidget()
        contenedor_layout = QVBoxLayout()
        contenedor_layout.setSpacing(Spacing.XL)

        # Encabezado
        header_layout = QHBoxLayout()
        titulo = QLabel("Dashboard de Equidad")
        titulo.setObjectName("labelTitle")
        header_layout.addWidget(titulo)
        header_layout.addStretch()

        # Botón refrescar
        self.btn_refrescar = QPushButton("Actualizar")
        self.btn_refrescar.setIcon(icon_for_button("refresh"))
        self.btn_refrescar.setStyleSheet("""
            QPushButton {
                background-color: #1976D2;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565C0;
            }
        """)
        self.btn_refrescar.clicked.connect(self._cargar_datos)
        header_layout.addWidget(self.btn_refrescar)

        contenedor_layout.addLayout(header_layout)

        # Cards de métricas principales
        metricas_layout = QHBoxLayout()
        metricas_layout.setSpacing(15)

        self.card_total_guardias = MetricaCard("Total Guardias", "0", "#2196F3")
        self.card_cobertura = MetricaCard("Cobertura", "0%", "#4CAF50")
        self.card_indice_equidad = MetricaCard("Índice Equidad", "0.00", "#FF9800")
        self.card_desbalances = MetricaCard("Desbalances", "0", "#F44336")

        metricas_layout.addWidget(self.card_total_guardias)
        metricas_layout.addWidget(self.card_cobertura)
        metricas_layout.addWidget(self.card_indice_equidad)
        metricas_layout.addWidget(self.card_desbalances)

        contenedor_layout.addLayout(metricas_layout)

        # Gráficos
        graficos_layout = QHBoxLayout()
        graficos_layout.setSpacing(15)

        # Histograma guardias por profesor
        grupo_histograma = QGroupBox("Distribución de Guardias por Profesor")
        grupo_histograma.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        histograma_layout = QVBoxLayout()
        self.canvas_histograma = GraficoCanvas(self, width=6, height=4)
        histograma_layout.addWidget(self.canvas_histograma)
        grupo_histograma.setLayout(histograma_layout)
        graficos_layout.addWidget(grupo_histograma)

        # Gráfico de distribución por turno
        grupo_turnos = QGroupBox("Distribución por Turno")
        grupo_turnos.setStyleSheet(grupo_histograma.styleSheet())
        turnos_layout = QVBoxLayout()
        self.canvas_turnos = GraficoCanvas(self, width=4, height=4)
        turnos_layout.addWidget(self.canvas_turnos)
        grupo_turnos.setLayout(turnos_layout)
        graficos_layout.addWidget(grupo_turnos)

        contenedor_layout.addLayout(graficos_layout)

        # Segunda fila de gráficos
        graficos2_layout = QHBoxLayout()
        graficos2_layout.setSpacing(15)

        # Top profesores con más guardias
        grupo_top = QGroupBox("Top 10 Profesores con Más Guardias")
        grupo_top.setStyleSheet(grupo_histograma.styleSheet())
        top_layout = QVBoxLayout()
        self.canvas_top = GraficoCanvas(self, width=6, height=4)
        top_layout.addWidget(self.canvas_top)
        grupo_top.setLayout(top_layout)
        graficos2_layout.addWidget(grupo_top)

        # Distribución por zona
        grupo_zonas = QGroupBox("Distribución por Zona")
        grupo_zonas.setStyleSheet(grupo_histograma.styleSheet())
        zonas_layout = QVBoxLayout()
        self.canvas_zonas = GraficoCanvas(self, width=4, height=4)
        zonas_layout.addWidget(self.canvas_zonas)
        grupo_zonas.setLayout(zonas_layout)
        graficos2_layout.addWidget(grupo_zonas)

        contenedor_layout.addLayout(graficos2_layout)

        # Información adicional
        self.info_label = QLabel("")
        self.info_label.setObjectName("labelCaption")
        contenedor_layout.addWidget(self.info_label)

        contenedor_layout.addStretch()
        contenedor.setLayout(contenedor_layout)
        scroll.setWidget(contenedor)
        layout.addWidget(scroll)
        self.setLayout(layout)

    def _cargar_datos(self):
        """Carga y visualiza los datos del dashboard."""
        try:
            logger.info("Cargando datos del dashboard...")

            # Obtener configuración activa
            from application.app_services import AppServices
            _svc = AppServices(self.session)
            config = _svc.configuracion_repo.get_first()
            if not config:
                self._mostrar_error("No hay configuración activa")
                return

            # Obtener guardias del curso
            guardias = _svc.guardias.find_by_curso(config.id)

            if not guardias:
                self._mostrar_sin_datos()
                return

            # Calcular cuotas esperadas
            request_cuotas = CalcularCuotasRequest(configuracion_id=config.id)
            response_cuotas = self.calcular_cuotas_uc.execute(request_cuotas)

            # Análisis de equidad
            request_equidad = AnalisisEquidadRequest(
                configuracion_id=config.id, incluir_cuotas_detalle=True
            )
            response_equidad = self.analisis_equidad_uc.execute(request_equidad)

            # Actualizar métricas
            self._actualizar_metricas(guardias, response_cuotas, response_equidad)

            # Actualizar gráficos
            self._actualizar_histograma(guardias)
            self._actualizar_grafico_turnos(guardias)
            self._actualizar_top_profesores(guardias)
            self._actualizar_grafico_zonas(guardias)

            # Actualizar info
            now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            self.info_label.setText(
                f"📅 Última actualización: {now} | "
                f"Total profesores: {len(response_cuotas.cuotas_detalle)} | "
                f"Total guardias: {len(guardias)}"
            )

            logger.info("Dashboard actualizado correctamente")

        except (ValueError, TypeError, OSError) as e:
            logger.error(f"Error cargando dashboard: {e}", exc_info=True)
            self._mostrar_error(f"Error: {str(e)}")

    def _actualizar_metricas(self, guardias, response_cuotas, response_equidad):
        """Actualiza las cards de métricas."""
        total_guardias = len(guardias)
        total_esperado = response_cuotas.total_guardias
        cobertura = (total_guardias / total_esperado * 100) if total_esperado > 0 else 0
        indice_equidad = response_equidad.metricas.indice_equidad
        desbalances = response_equidad.metricas.desbalances_detectados

        self.card_total_guardias.actualizar_valor(str(total_guardias))
        self.card_cobertura.actualizar_valor(f"{cobertura:.1f}%")
        self.card_indice_equidad.actualizar_valor(f"{indice_equidad:.2f}")
        self.card_desbalances.actualizar_valor(str(desbalances))

        # Cambiar colores según valores
        if cobertura >= 90:
            self.card_cobertura.valor_label.setStyleSheet(
                "font-size: 28px; color: #4CAF50; font-weight: bold; margin-top: 5px;"
            )
        elif cobertura >= 70:
            self.card_cobertura.valor_label.setStyleSheet(
                "font-size: 28px; color: #FF9800; font-weight: bold; margin-top: 5px;"
            )
        else:
            self.card_cobertura.valor_label.setStyleSheet(
                "font-size: 28px; color: #F44336; font-weight: bold; margin-top: 5px;"
            )

    def _actualizar_histograma(self, guardias):
        """Actualiza el histograma de guardias por profesor."""
        self.canvas_histograma.axes.clear()

        # Contar guardias por profesor
        guardias_por_profesor = {}
        for guardia in guardias:
            if guardia.profesor_id:
                from application.app_services import AppServices
                prof = AppServices(self.session).profesores.get_by_id(guardia.profesor_id)
                if prof:
                    nombre = prof.nombre_completo
                    guardias_por_profesor[nombre] = guardias_por_profesor.get(nombre, 0) + 1

        if not guardias_por_profesor:
            self.canvas_histograma.axes.text(
                0.5, 0.5, "No hay datos disponibles", ha="center", va="center", fontsize=12
            )
            self.canvas_histograma.draw()
            return

        # Ordenar por cantidad
        items = sorted(guardias_por_profesor.items(), key=lambda x: x[1], reverse=True)
        nombres = [item[0].split(",")[0] for item in items]  # Solo apellido
        cantidades = [item[1] for item in items]

        # Limitar a 15 profesores
        if len(nombres) > 15:
            nombres = nombres[:15]
            cantidades = cantidades[:15]

        # Crear gráfico de barras horizontal
        colores = ["#2196F3" if i % 2 == 0 else "#1976D2" for i in range(len(nombres))]
        self.canvas_histograma.axes.barh(nombres, cantidades, color=colores)
        self.canvas_histograma.axes.set_xlabel("Número de Guardias", fontsize=10)
        self.canvas_histograma.axes.set_title(
            "Guardias por Profesor", fontsize=12, fontweight="bold"
        )
        self.canvas_histograma.axes.tick_params(labelsize=8)
        self.canvas_histograma.axes.invert_yaxis()  # Orden descendente

        # Agregar valores en las barras
        for i, v in enumerate(cantidades):
            self.canvas_histograma.axes.text(v + 0.5, i, str(v), va="center", fontsize=8)

        self.canvas_histograma.fig.tight_layout()
        self.canvas_histograma.draw()

    def _actualizar_grafico_turnos(self, guardias):
        """Actualiza el gráfico de distribución por turno."""
        self.canvas_turnos.axes.clear()

        # Contar por turno
        turnos_count = {"mañana": 0, "tarde": 0}
        for guardia in guardias:
            turno = guardia.turno or "mañana"
            if turno in turnos_count:
                turnos_count[turno] += 1

        if sum(turnos_count.values()) == 0:
            self.canvas_turnos.axes.text(
                0.5, 0.5, "No hay datos", ha="center", va="center", fontsize=12
            )
            self.canvas_turnos.draw()
            return

        # Gráfico de pastel
        labels = [f"{k.capitalize()}\n({v})" for k, v in turnos_count.items()]
        sizes = list(turnos_count.values())
        colores = ["#FFA726", "#42A5F5"]
        explode = (0.05, 0.05)

        self.canvas_turnos.axes.pie(
            sizes, labels=labels, autopct="%1.1f%%", colors=colores, explode=explode, startangle=90
        )
        self.canvas_turnos.axes.set_title("Distribución por Turno", fontsize=12, fontweight="bold")
        self.canvas_turnos.fig.tight_layout()
        self.canvas_turnos.draw()

    def _actualizar_top_profesores(self, guardias):
        """Actualiza el gráfico de top profesores."""
        self.canvas_top.axes.clear()

        # Contar guardias por profesor
        guardias_por_profesor = {}
        for guardia in guardias:
            if guardia.profesor_id:
                from application.app_services import AppServices
                prof = AppServices(self.session).profesores.get_by_id(guardia.profesor_id)
                if prof:
                    nombre = prof.nombre_completo
                    guardias_por_profesor[nombre] = guardias_por_profesor.get(nombre, 0) + 1

        if not guardias_por_profesor:
            self.canvas_top.axes.text(
                0.5, 0.5, "No hay datos", ha="center", va="center", fontsize=12
            )
            self.canvas_top.draw()
            return

        # Top 10
        items = sorted(guardias_por_profesor.items(), key=lambda x: x[1], reverse=True)[:10]
        nombres = [item[0].split(",")[0] for item in items]
        cantidades = [item[1] for item in items]

        # Gráfico de barras vertical con gradiente
        colores = plt.cm.Blues(range(100, 255, int(155 / len(nombres))))
        bars = self.canvas_top.axes.bar(range(len(nombres)), cantidades, color=colores)
        self.canvas_top.axes.set_xticks(range(len(nombres)))
        self.canvas_top.axes.set_xticklabels(nombres, rotation=45, ha="right", fontsize=8)
        self.canvas_top.axes.set_ylabel("Guardias", fontsize=10)
        self.canvas_top.axes.set_title("Top 10 Profesores", fontsize=12, fontweight="bold")

        # Valores en barras
        for bar in bars:
            height = bar.get_height()
            self.canvas_top.axes.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{int(height)}",
                ha="center",
                va="bottom",
                fontsize=8,
            )

        self.canvas_top.fig.tight_layout()
        self.canvas_top.draw()

    def _actualizar_grafico_zonas(self, guardias):
        """Actualiza el gráfico de distribución por zona."""
        self.canvas_zonas.axes.clear()

        # Contar por zona
        from infrastructure.database.models import Zona

        zonas_count = {}
        for guardia in guardias:
            if guardia.zona_id:
                from application.app_services import AppServices
                zona = AppServices(self.session).zonas.get_by_id(guardia.zona_id)
                if zona:
                    zonas_count[zona.nombre_zona] = zonas_count.get(zona.nombre_zona, 0) + 1

        if not zonas_count:
            self.canvas_zonas.axes.text(
                0.5, 0.5, "No hay datos", ha="center", va="center", fontsize=12
            )
            self.canvas_zonas.draw()
            return

        # Gráfico de dona
        labels = [f"{k}\n({v})" for k, v in zonas_count.items()]
        sizes = list(zonas_count.values())
        colores = plt.cm.Set3(range(len(sizes)))

        wedges, texts, autotexts = self.canvas_zonas.axes.pie(
            sizes, labels=labels, autopct="%1.1f%%", colors=colores, startangle=90, pctdistance=0.85
        )

        # Hacer dona
        centre_circle = plt.Circle((0, 0), 0.70, fc="white")
        self.canvas_zonas.axes.add_artist(centre_circle)

        # Ajustar tamaño de texto
        for text in texts:
            text.set_fontsize(8)
        for autotext in autotexts:
            autotext.set_color("white")
            autotext.set_fontweight("bold")
            autotext.set_fontsize(8)

        self.canvas_zonas.axes.set_title("Distribución por Zona", fontsize=12, fontweight="bold")
        self.canvas_zonas.fig.tight_layout()
        self.canvas_zonas.draw()

    def _mostrar_sin_datos(self):
        """Muestra mensaje cuando no hay datos."""
        self.card_total_guardias.actualizar_valor("0")
        self.card_cobertura.actualizar_valor("0%")
        self.card_indice_equidad.actualizar_valor("N/A")
        self.card_desbalances.actualizar_valor("0")

        for canvas in [
            self.canvas_histograma,
            self.canvas_turnos,
            self.canvas_top,
            self.canvas_zonas,
        ]:
            canvas.axes.clear()
            canvas.axes.text(
                0.5,
                0.5,
                "No hay guardias asignadas",
                ha="center",
                va="center",
                fontsize=14,
                color="#999",
            )
            canvas.draw()

        self.info_label.setText("No hay guardias asignadas en el curso actual")

    def _mostrar_error(self, mensaje: str):
        """Muestra mensaje de error."""
        self.info_label.setText(mensaje)

    def refrescar(self):
        """Refresca el dashboard (para compatibilidad con main_window)."""
        self._cargar_datos()
