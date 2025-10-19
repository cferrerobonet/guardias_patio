"""
Panel de estadísticas para analizar la distribución de guardias.
Muestra métricas, gráficos y análisis de cobertura.
"""

from collections import defaultdict

import matplotlib

matplotlib.use('QtAgg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
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
from sqlalchemy.orm import Session

from models.models import Guardia, Profesor, Zona


class PanelEstadisticas(QWidget):
    """Widget para mostrar estadísticas de guardias."""

    def __init__(self, session: Session):
        super().__init__()
        self.session = session
        self.init_ui()

    def init_ui(self):
        """Inicializa la interfaz de usuario."""
        layout_principal = QVBoxLayout()

        # Título
        titulo = QLabel("📊 Estadísticas de Guardias")
        titulo.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_principal.addWidget(titulo)

        # Botón refrescar
        btn_refrescar = QPushButton("🔄 Actualizar Estadísticas")
        btn_refrescar.clicked.connect(self.actualizar_estadisticas)
        btn_refrescar.setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            """
        )
        layout_principal.addWidget(btn_refrescar)

        # Pestañas
        self.tabs = QTabWidget()

        # Tab 1: Resumen General
        self.tab_resumen = self.crear_tab_resumen()
        self.tabs.addTab(self.tab_resumen, "📋 Resumen")

        # Tab 2: Por Profesor
        self.tab_profesores = self.crear_tab_profesores()
        self.tabs.addTab(self.tab_profesores, "👨‍🏫 Por Profesor")

        # Tab 3: Por Zona
        self.tab_zonas = self.crear_tab_zonas()
        self.tabs.addTab(self.tab_zonas, "🏫 Por Zona")

        # Tab 4: Gráficos
        self.tab_graficos = self.crear_tab_graficos()
        self.tabs.addTab(self.tab_graficos, "📈 Gráficos")

        layout_principal.addWidget(self.tabs)
        self.setLayout(layout_principal)

        # Cargar datos iniciales
        self.actualizar_estadisticas()

    def crear_tab_resumen(self) -> QWidget:
        """Crea la pestaña de resumen general."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Tarjetas de métricas
        self.label_total_guardias = QLabel("Total Guardias: 0")
        self.label_total_profesores = QLabel("Profesores Activos: 0")
        self.label_total_zonas = QLabel("Zonas Configuradas: 0")
        self.label_cobertura = QLabel("Cobertura: 0%")

        for label in [
            self.label_total_guardias,
            self.label_total_profesores,
            self.label_total_zonas,
            self.label_cobertura,
        ]:
            label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            label.setStyleSheet(
                """
                background-color: #e3f2fd;
                padding: 15px;
                border-radius: 8px;
                border: 1px solid #90caf9;
                """
            )
            layout.addWidget(label)

        # Información adicional
        self.label_info = QLabel("")
        self.label_info.setWordWrap(True)
        self.label_info.setStyleSheet("padding: 10px;")
        layout.addWidget(self.label_info)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def crear_tab_profesores(self) -> QWidget:
        """Crea la pestaña de estadísticas por profesor."""
        widget = QWidget()
        layout = QVBoxLayout()

        self.tabla_profesores = QTableWidget()
        self.tabla_profesores.setColumnCount(6)
        self.tabla_profesores.setHorizontalHeaderLabels(
            ["Profesor", "Total", "Mañana", "Tarde", "% Total", "Estado"]
        )
        self.tabla_profesores.horizontalHeader().setStretchLastSection(True)

        layout.addWidget(self.tabla_profesores)
        widget.setLayout(layout)
        return widget

    def crear_tab_zonas(self) -> QWidget:
        """Crea la pestaña de estadísticas por zona."""
        widget = QWidget()
        layout = QVBoxLayout()

        self.tabla_zonas = QTableWidget()
        self.tabla_zonas.setColumnCount(4)
        self.tabla_zonas.setHorizontalHeaderLabels(
            ["Zona", "Total Guardias", "Profesores Diferentes", "% Cobertura"]
        )
        self.tabla_zonas.horizontalHeader().setStretchLastSection(True)

        layout.addWidget(self.tabla_zonas)
        widget.setLayout(layout)
        return widget

    def crear_tab_graficos(self) -> QWidget:
        """Crea la pestaña de gráficos."""
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
        """Actualiza todas las estadísticas."""
        self.actualizar_resumen()
        self.actualizar_tabla_profesores()
        self.actualizar_tabla_zonas()
        self.actualizar_graficos()

    def actualizar_resumen(self):
        """Actualiza el resumen general."""
        # Total guardias
        total_guardias = self.session.query(Guardia).count()
        self.label_total_guardias.setText(f"Total Guardias: {total_guardias}")

        # Total profesores con guardias
        profesores_con_guardias = (
            self.session.query(func.count(func.distinct(Guardia.profesor_id)))
            .scalar()
        )
        total_profesores = self.session.query(Profesor).count()
        self.label_total_profesores.setText(
            f"Profesores Activos: {profesores_con_guardias} / {total_profesores}"
        )

        # Total zonas
        total_zonas = self.session.query(Zona).count()
        self.label_total_zonas.setText(f"Zonas Configuradas: {total_zonas}")

        # Cobertura (estimada)
        if total_guardias > 0 and total_profesores > 0:
            promedio_por_profesor = total_guardias / profesores_con_guardias
            cobertura = min(100, int((promedio_por_profesor / 50) * 100))
            self.label_cobertura.setText(f"Cobertura Estimada: {cobertura}%")
        else:
            self.label_cobertura.setText("Cobertura Estimada: 0%")

        # Info adicional
        if total_guardias > 0:
            guardias_manana = (
                self.session.query(Guardia)
                .filter(Guardia.turno == "mañana")
                .count()
            )
            guardias_tarde = (
                self.session.query(Guardia)
                .filter(Guardia.turno == "tarde")
                .count()
            )

            info = f"""
            📊 Detalles:
            • Guardias de Mañana: {guardias_manana} ({int(guardias_manana/total_guardias*100)}%)
            • Guardias de Tarde: {guardias_tarde} ({int(guardias_tarde/total_guardias*100)}%)
            • Promedio por profesor: {promedio_por_profesor:.1f} guardias
            """
            self.label_info.setText(info)
        else:
            self.label_info.setText("No hay guardias generadas todavía.")

    def actualizar_tabla_profesores(self):
        """Actualiza la tabla de estadísticas por profesor."""
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
            stats = guardias_por_prof.get(profesor.id, {"total": 0, "mañana": 0, "tarde": 0})

            # Nombre
            self.tabla_profesores.setItem(i, 0, QTableWidgetItem(profesor.nombre_completo))

            # Total
            self.tabla_profesores.setItem(i, 1, QTableWidgetItem(str(stats["total"])))

            # Mañana
            self.tabla_profesores.setItem(i, 2, QTableWidgetItem(str(stats["mañana"])))

            # Tarde
            self.tabla_profesores.setItem(i, 3, QTableWidgetItem(str(stats["tarde"])))

            # Porcentaje
            if total_guardias > 0:
                porcentaje = (stats["total"] / total_guardias) * 100
                self.tabla_profesores.setItem(i, 4, QTableWidgetItem(f"{porcentaje:.1f}%"))
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
        """Actualiza la tabla de estadísticas por zona."""
        zonas = self.session.query(Zona).all()
        self.tabla_zonas.setRowCount(len(zonas))

        for i, zona in enumerate(zonas):
            # Nombre zona
            self.tabla_zonas.setItem(i, 0, QTableWidgetItem(zona.nombre_zona))

            # Total guardias
            total = (
                self.session.query(Guardia)
                .filter(Guardia.zona_id == zona.id)
                .count()
            )
            self.tabla_zonas.setItem(i, 1, QTableWidgetItem(str(total)))

            # Profesores diferentes
            profesores_diferentes = (
                self.session.query(func.count(func.distinct(Guardia.profesor_id)))
                .filter(Guardia.zona_id == zona.id)
                .scalar()
            )
            self.tabla_zonas.setItem(i, 2, QTableWidgetItem(str(profesores_diferentes)))

            # Cobertura (estimada como porcentaje de días cubiertos)
            self.tabla_zonas.setItem(i, 3, QTableWidgetItem("N/A"))

    def actualizar_graficos(self):
        """Actualiza los gráficos."""
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
                    # Abreviar nombre
                    nombre = prof.nombre_completo
                    if "," in nombre:
                        apellido = nombre.split(",")[0]
                        nombres.append(apellido[:15])
                    else:
                        nombres.append(nombre[:15])
                    cantidades.append(count)

            # Dibujar gráfico de barras
            self.canvas_profesores.axes.clear()
            self.canvas_profesores.axes.bar(nombres, cantidades, color='#4CAF50')
            self.canvas_profesores.axes.set_xlabel('Profesor')
            self.canvas_profesores.axes.set_ylabel('Guardias')
            self.canvas_profesores.axes.set_title('Distribución de Guardias por Profesor')
            self.canvas_profesores.axes.tick_params(axis='x', rotation=45)
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
                autopct='%1.1f%%',
                startangle=90
            )
            self.canvas_zonas.axes.set_title('Distribución de Guardias por Zona')
            self.canvas_zonas.figure.tight_layout()
            self.canvas_zonas.draw()

    def refrescar(self):
        """Refresca las estadísticas (útil después de generar guardias)."""
        self.actualizar_estadisticas()


class MplCanvas(FigureCanvasQTAgg):
    """Canvas de Matplotlib para integrar en PyQt."""

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)
