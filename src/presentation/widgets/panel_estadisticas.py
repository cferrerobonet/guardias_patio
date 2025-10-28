"""
Panel de estadísticas para analizar la distribución de guardias.

Muestra métricas, gráficos y análisis de cobertura.
"""

from collections import defaultdict

import matplotlib

matplotlib.use("QtAgg")
import ui_styles as styles
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from models.models import Guardia, Profesor, Zona
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QLabel,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy import func

from presentation.forms.base_form import BaseForm
from presentation.themes.ccleaner_theme import (
    CONTENT_BG_ALT,
    PRIMARY_BLUE,
    SUCCESS_GREEN,
    TEXT_PRIMARY,
    get_table_style,
)


class PanelEstadisticas(BaseForm):
    """Widget para mostrar estadísticas de guardias."""

    def __init__(self, session):
        """
        Inicializar panel de estadísticas.

        Args:
            session: Sesión de base de datos
        """
        super().__init__(session)
        self.setWindowTitle("Estadísticas de Guardias")
        self.setup_ui()

    def setup_ui(self):
        """Construir la interfaz del widget."""
        layout_principal = QVBoxLayout()

        # Título
        titulo = QLabel("📊 ESTADÍSTICAS DE GUARDIAS")
        titulo.setStyleSheet(styles.STYLE_TITLE_MAIN)
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_principal.addWidget(titulo)

        # Botón refrescar
        btn_refrescar = QPushButton("🔄 Actualizar Estadísticas")
        btn_refrescar.clicked.connect(self.actualizar_estadisticas)
        btn_refrescar.setStyleSheet(styles.STYLE_BUTTON_SUCCESS)
        layout_principal.addWidget(btn_refrescar)

        # Pestañas
        self.tabs = QTabWidget()
        self.tabs.addTab(self._crear_tab_resumen(), "📋 Resumen")
        self.tabs.addTab(self._crear_tab_profesores(), "👨‍🏫 Por Profesor")
        self.tabs.addTab(self._crear_tab_zonas(), "🏫 Por Zona")
        self.tabs.addTab(self._crear_tab_graficos(), "📈 Gráficos")

        layout_principal.addWidget(self.tabs)
        self.setLayout(layout_principal)

        # Cargar datos iniciales
        self.actualizar_estadisticas()

    def _crear_tab_resumen(self) -> QWidget:
        """Crear la pestaña de resumen general."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Tarjetas de métricas
        self.label_total_guardias = QLabel("Total Guardias: 0")
        self.label_total_profesores = QLabel("Profesores Activos: 0")
        self.label_total_zonas = QLabel("Zonas Configuradas: 0")
        self.label_cobertura = QLabel("Cobertura: 0%")

        estilo_metrica = f"""
            QLabel {{
                background-color: {CONTENT_BG_ALT};
                padding: 15px;
                border-radius: 8px;
                border: 2px solid {PRIMARY_BLUE};
                font-size: 13px;
                font-weight: bold;
                color: {TEXT_PRIMARY};
            }}
        """

        for label in [
            self.label_total_guardias,
            self.label_total_profesores,
            self.label_total_zonas,
            self.label_cobertura,
        ]:
            label.setStyleSheet(estilo_metrica)
            layout.addWidget(label)

        # Información adicional
        self.label_info = QLabel("")
        self.label_info.setWordWrap(True)
        self.label_info.setStyleSheet("padding: 10px;")
        layout.addWidget(self.label_info)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _crear_tab_profesores(self) -> QWidget:
        """Crear la pestaña de estadísticas por profesor."""
        widget = QWidget()
        layout = QVBoxLayout()

        self.tabla_profesores = QTableWidget()
        self.tabla_profesores.setColumnCount(6)
        self.tabla_profesores.setHorizontalHeaderLabels(
            ["Profesor", "Total", "Mañana", "Tarde", "% Total", "Estado"]
        )
        self.tabla_profesores.horizontalHeader().setStretchLastSection(True)
        self.tabla_profesores.setStyleSheet(get_table_style())

        layout.addWidget(self.tabla_profesores)
        widget.setLayout(layout)
        return widget

    def _crear_tab_zonas(self) -> QWidget:
        """Crear la pestaña de estadísticas por zona."""
        widget = QWidget()
        layout = QVBoxLayout()

        self.tabla_zonas = QTableWidget()
        self.tabla_zonas.setColumnCount(4)
        self.tabla_zonas.setHorizontalHeaderLabels(
            ["Zona", "Total Guardias", "Profesores Diferentes", "% Cobertura"]
        )
        self.tabla_zonas.horizontalHeader().setStretchLastSection(True)
        self.tabla_zonas.setStyleSheet(get_table_style())

        layout.addWidget(self.tabla_zonas)
        widget.setLayout(layout)
        return widget

    def _crear_tab_graficos(self) -> QWidget:
        """Crear la pestaña de gráficos."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Área con scroll para múltiples gráficos
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()

        # Gráfico 1: Distribución por profesor
        self.canvas_profesores = MplCanvas(self, width=8, height=4)
        scroll_layout.addWidget(self.canvas_profesores)

        # Gráfico 2: Distribución por zona
        self.canvas_zonas = MplCanvas(self, width=8, height=4)
        scroll_layout.addWidget(self.canvas_zonas)

        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        widget.setLayout(layout)
        return widget

    def actualizar_estadisticas(self):
        """Actualizar todas las estadísticas."""
        try:
            self.actualizar_resumen()
            self.actualizar_tabla_profesores()
            self.actualizar_tabla_zonas()
            self.actualizar_graficos()
        except Exception as e:
            self.manejar_excepcion(e, "actualizar estadísticas")

    def actualizar_resumen(self):
        """Actualizar el resumen general."""
        # Total guardias
        total_guardias = self.session.query(Guardia).count()
        self.label_total_guardias.setText(f"Total Guardias: {total_guardias}")

        # Total profesores con guardias
        profesores_con_guardias = self.session.query(
            func.count(func.distinct(Guardia.profesor_id))
        ).scalar()
        total_profesores = self.session.query(Profesor).count()
        self.label_total_profesores.setText(
            f"Profesores Activos: {profesores_con_guardias} / {total_profesores}"
        )

        # Total zonas
        total_zonas = self.session.query(Zona).count()
        self.label_total_zonas.setText(f"Zonas Configuradas: {total_zonas}")

        # Cobertura (estimada)
        if total_guardias > 0 and profesores_con_guardias > 0:
            promedio_por_profesor = total_guardias / profesores_con_guardias
            cobertura = min(100, int((promedio_por_profesor / 50) * 100))
            self.label_cobertura.setText(f"Cobertura Estimada: {cobertura}%")

            # Info adicional
            guardias_manana = (
                self.session.query(Guardia).filter(Guardia.turno == "mañana").count()
            )
            guardias_tarde = (
                self.session.query(Guardia).filter(Guardia.turno == "tarde").count()
            )

            porcentaje_manana = int(guardias_manana / total_guardias * 100)
            porcentaje_tarde = int(guardias_tarde / total_guardias * 100)

            info = f"""
            📊 Detalles:
            • Guardias de Mañana: {guardias_manana} ({porcentaje_manana}%)
            • Guardias de Tarde: {guardias_tarde} ({porcentaje_tarde}%)
            • Promedio por profesor: {promedio_por_profesor:.1f} guardias
            """
            self.label_info.setText(info)
        else:
            self.label_cobertura.setText("Cobertura Estimada: 0%")
            self.label_info.setText("No hay guardias generadas todavía.")

    def actualizar_tabla_profesores(self):
        """Actualizar la tabla de estadísticas por profesor."""
        # Consultar guardias agrupadas por profesor
        guardias_por_prof = defaultdict(lambda: {"total": 0, "mañana": 0, "tarde": 0})

        guardias = self.session.query(Guardia).all()
        for g in guardias:
            guardias_por_prof[g.profesor_id]["total"] += 1
            if g.turno == "mañana":
                guardias_por_prof[g.profesor_id]["mañana"] += 1
            else:
                guardias_por_prof[g.profesor_id]["tarde"] += 1

        # Obtener todos los profesores
        profesores = self.session.query(Profesor).all()

        # Calcular total para porcentajes
        total_guardias = sum(stats["total"] for stats in guardias_por_prof.values())

        # Llenar tabla
        self.tabla_profesores.setRowCount(len(profesores))

        for i, profesor in enumerate(profesores):
            stats = guardias_por_prof.get(
                profesor.id, {"total": 0, "mañana": 0, "tarde": 0}
            )

            self.tabla_profesores.setItem(
                i, 0, QTableWidgetItem(profesor.nombre_completo)
            )
            self.tabla_profesores.setItem(i, 1, QTableWidgetItem(str(stats["total"])))
            self.tabla_profesores.setItem(i, 2, QTableWidgetItem(str(stats["mañana"])))
            self.tabla_profesores.setItem(i, 3, QTableWidgetItem(str(stats["tarde"])))

            # Porcentaje
            if total_guardias > 0:
                porcentaje = (stats["total"] / total_guardias) * 100
                self.tabla_profesores.setItem(
                    i, 4, QTableWidgetItem(f"{porcentaje:.1f}%")
                )
            else:
                self.tabla_profesores.setItem(i, 4, QTableWidgetItem("0%"))

            # Estado
            if stats["total"] == 0:
                estado = "❌ Sin guardias"
            elif stats["total"] < 5:
                estado = "⚠️ Pocas guardias"
            else:
                estado = "✅ Asignado"
            self.tabla_profesores.setItem(i, 5, QTableWidgetItem(estado))

    def actualizar_tabla_zonas(self):
        """Actualizar la tabla de estadísticas por zona."""
        zonas = self.session.query(Zona).all()
        self.tabla_zonas.setRowCount(len(zonas))

        for i, zona in enumerate(zonas):
            self.tabla_zonas.setItem(i, 0, QTableWidgetItem(zona.nombre_zona))

            total = (
                self.session.query(Guardia).filter(Guardia.zona_id == zona.id).count()
            )
            self.tabla_zonas.setItem(i, 1, QTableWidgetItem(str(total)))

            profesores_diferentes = (
                self.session.query(func.count(func.distinct(Guardia.profesor_id)))
                .filter(Guardia.zona_id == zona.id)
                .scalar()
            )
            self.tabla_zonas.setItem(i, 2, QTableWidgetItem(str(profesores_diferentes)))
            self.tabla_zonas.setItem(i, 3, QTableWidgetItem("N/A"))

    def actualizar_graficos(self):
        """Actualizar los gráficos."""
        # Gráfico de distribución por profesor
        guardias_por_prof = defaultdict(int)
        guardias = self.session.query(Guardia).all()
        for g in guardias:
            guardias_por_prof[g.profesor_id] += 1

        if guardias_por_prof:
            profesores = self.session.query(Profesor).all()
            nombres = []
            cantidades = []

            for prof in profesores:
                count = guardias_por_prof.get(prof.id, 0)
                if count > 0:  # Solo mostrar profesores con guardias
                    nombre = prof.nombre_completo
                    if "," in nombre:
                        apellido = nombre.split(",")[0]
                        nombres.append(apellido[:15])
                    else:
                        nombres.append(nombre[:15])
                    cantidades.append(count)

            # Dibujar gráfico de barras
            self.canvas_profesores.axes.clear()
            self.canvas_profesores.axes.bar(nombres, cantidades, color=SUCCESS_GREEN)
            self.canvas_profesores.axes.set_xlabel("Profesor")
            self.canvas_profesores.axes.set_ylabel("Guardias")
            self.canvas_profesores.axes.set_title(
                "Distribución de Guardias por Profesor"
            )
            self.canvas_profesores.axes.tick_params(axis="x", rotation=45)
            self.canvas_profesores.figure.tight_layout()
            self.canvas_profesores.draw()

        # Gráfico de distribución por zona
        guardias_por_zona = defaultdict(int)
        for g in guardias:
            guardias_por_zona[g.zona_id] += 1

        if guardias_por_zona:
            zonas = self.session.query(Zona).all()
            nombres_zonas = []
            cantidades_zonas = []

            for zona in zonas:
                count = guardias_por_zona.get(zona.id, 0)
                if count > 0:
                    nombres_zonas.append(zona.nombre_zona[:20])
                    cantidades_zonas.append(count)

            # Dibujar gráfico de pastel
            self.canvas_zonas.axes.clear()
            self.canvas_zonas.axes.pie(
                cantidades_zonas,
                labels=nombres_zonas,
                autopct="%1.1f%%",
                startangle=90,
            )
            self.canvas_zonas.axes.set_title("Distribución de Guardias por Zona")
            self.canvas_zonas.figure.tight_layout()
            self.canvas_zonas.draw()

    def refrescar(self):
        """Refrescar las estadísticas (útil después de generar guardias)."""
        self.actualizar_estadisticas()


class MplCanvas(FigureCanvasQTAgg):
    """Canvas de Matplotlib para integrar en PyQt."""

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        """
        Inicializar canvas de matplotlib.

        Args:
            parent: Widget padre
            width: Ancho de la figura
            height: Alto de la figura
            dpi: Resolución de la figura
        """
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)
