"""
Panel de estadísticas para analizar la distribución de guardias.

Muestra métricas, gráficos y análisis de cobertura.
Utiliza ObtenerEstadisticasPanelUseCase para separar lógica de presentación.
"""

from collections import defaultdict
from datetime import date, timedelta

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QHeaderView,
    QLabel,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from application.use_cases.asignacion_guardias import ObtenerEstadisticasPanelUseCase
from infrastructure.database.models import Guardia, Profesor
from presentation.forms.base_form import BaseForm
from presentation.themes.ccleaner_theme import (
    CONTENT_BG_ALT,
    PRIMARY_BLUE,
    SUCCESS_GREEN,
    TEXT_PRIMARY,
    get_table_style,
)
from utils.icons import icon_for_button

from presentation.widgets.bar_chart_widget import BarChartWidget, PieChartWidget

MplCanvas = BarChartWidget


class PanelEstadisticas(BaseForm):
    """Widget para mostrar estadísticas de guardias."""

    def __init__(self, session):
        """
        Inicializar panel de estadísticas.

        Args:
            session: Sesión de base de datos
        """
        super().__init__(session)
        self.session = session
        self.setWindowTitle("Estadísticas de Guardias")
        self._use_case = ObtenerEstadisticasPanelUseCase(session)
        self.setup_ui()

    def setup_ui(self):
        """Construir la interfaz del widget."""
        layout_principal = QVBoxLayout()

        # Título
        titulo = QLabel("ESTADÍSTICAS DE GUARDIAS")
        titulo.setObjectName("titleMain")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_principal.addWidget(titulo)

        # Botón refrescar
        btn_refrescar = QPushButton("Actualizar Estadísticas")
        btn_refrescar.setIcon(icon_for_button("refresh"))
        btn_refrescar.clicked.connect(self.actualizar_estadisticas)
        btn_refrescar.setProperty("success", "true")
        layout_principal.addWidget(btn_refrescar)

        # Pestañas
        self.tabs = QTabWidget()
        self.tabs.addTab(self._crear_tab_resumen(), "Resumen")
        self.tabs.addTab(self._crear_tab_profesores(), "Por Profesor")
        self.tabs.addTab(self._crear_tab_zonas(), "Por Zona")
        self.tabs.addTab(self._crear_tab_graficos(), "Gráficos")
        self.tabs.addTab(self._crear_tab_heatmap(), "Equidad")

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
        self.tabla_profesores.setColumnCount(8)
        self.tabla_profesores.setHorizontalHeaderLabels(
            [
                "Profesor",
                "Total",
                "Mañana",
                "Tarde",
                "% Total",
                "Estado",
                "Inicio Guardias",
                "Fin Guardias",
            ]
        )
        # Ajustar ancho automático de columnas al contenido
        self.tabla_profesores.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.tabla_profesores.setStyleSheet(get_table_style())
        header = self.tabla_profesores.horizontalHeader()
        header.model().setHeaderData(
            6, Qt.Orientation.Horizontal,
            "Fecha desde la que el profesor tiene guardias asignadas.\n'-' significa sin restricción de período.",
            Qt.ItemDataRole.ToolTipRole,
        )
        header.model().setHeaderData(
            7, Qt.Orientation.Horizontal,
            "Fecha hasta la que el profesor tiene guardias asignadas.\n'-' significa sin restricción de período.",
            Qt.ItemDataRole.ToolTipRole,
        )

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
        # Ajustar ancho automático de columnas al contenido
        self.tabla_zonas.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.tabla_zonas.setStyleSheet(get_table_style())

        layout.addWidget(self.tabla_zonas)
        widget.setLayout(layout)
        return widget

    def _crear_tab_graficos(self) -> QWidget:
        """Crear la pestaña de gráficos."""
        widget = QWidget()
        layout = QVBoxLayout()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()

        self.canvas_profesores = BarChartWidget(titulo="Distribución de Guardias por Profesor", horizontal=True)
        self.canvas_profesores.setMinimumHeight(250)
        scroll_layout.addWidget(self.canvas_profesores)

        self.canvas_zonas = PieChartWidget(titulo="Distribución de Guardias por Zona")
        self.canvas_zonas.setMinimumHeight(300)
        scroll_layout.addWidget(self.canvas_zonas)

        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        widget.setLayout(layout)
        return widget

    def _crear_tab_heatmap(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout()

        leyenda = QLabel("🟢 En cuota  🟡 Ligeramente sobre (+25%)  🔴 Muy sobre (+50%)  ⬜ Sin guardias")
        leyenda.setStyleSheet("padding: 6px; font-size: 11px;")
        layout.addWidget(leyenda)

        self.tabla_heatmap = QTableWidget()
        self.tabla_heatmap.setStyleSheet(get_table_style())
        self.tabla_heatmap.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_heatmap.verticalHeader().setVisible(False)
        layout.addWidget(self.tabla_heatmap)

        widget.setLayout(layout)
        return widget

    def _actualizar_heatmap_ui(self):
        guardias = self.session.query(Guardia).all()
        profesores = self.session.query(Profesor).all()

        if not guardias or not profesores:
            self.tabla_heatmap.setRowCount(0)
            self.tabla_heatmap.setColumnCount(0)
            return

        fechas = [g.fecha for g in guardias if g.fecha]
        if not fechas:
            return

        fecha_min = min(fechas)
        fecha_max = max(fechas)

        # Calcular semanas (lunes de cada semana en el rango)
        semanas = []
        d = fecha_min - timedelta(days=fecha_min.weekday())
        while d <= fecha_max:
            semanas.append(d)
            d += timedelta(days=7)

        # Calcular cuotas totales por profesor (proporcional a horas)
        total_horas = sum(p.horas_contrato for p in profesores if p.horas_contrato)
        total_guardias_global = len(guardias)
        cuota_por_prof = {}
        if total_horas > 0:
            for p in profesores:
                factor = (p.horas_contrato or 0) / total_horas
                cuota_por_prof[p.id] = max(1, round(total_guardias_global * factor))

        # Guardar cuota semanal media
        n_semanas = len(semanas) or 1
        cuota_semanal = {pid: max(1, round(c / n_semanas)) for pid, c in cuota_por_prof.items()}

        # Contar guardias por (profesor_id, semana_lunes)
        conteo: dict = defaultdict(int)
        for g in guardias:
            if g.fecha:
                lunes = g.fecha - timedelta(days=g.fecha.weekday())
                conteo[(g.profesor_id, lunes)] += 1

        # Cabeceras columnas
        col_headers = [f"S{i+1}\n{s.strftime('%d/%m')}" for i, s in enumerate(semanas)]
        self.tabla_heatmap.setColumnCount(len(semanas) + 1)
        self.tabla_heatmap.setHorizontalHeaderLabels(["Profesor"] + col_headers)
        self.tabla_heatmap.setRowCount(len(profesores))

        COLOR_OK = QColor(180, 230, 180)     # verde claro
        COLOR_WARN = QColor(255, 220, 100)   # ámbar
        COLOR_OVER = QColor(255, 140, 140)   # rojo claro
        COLOR_NONE = QColor(240, 240, 240)   # gris claro

        for row, prof in enumerate(sorted(profesores, key=lambda p: p.nombre_completo)):
            nombre_item = QTableWidgetItem(prof.nombre_completo)
            nombre_item.setFlags(nombre_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabla_heatmap.setItem(row, 0, nombre_item)

            cuota_s = cuota_semanal.get(prof.id, 1)
            for col, lunes in enumerate(semanas):
                n = conteo.get((prof.id, lunes), 0)
                item = QTableWidgetItem(str(n) if n > 0 else "")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if n == 0:
                    item.setBackground(COLOR_NONE)
                elif n <= cuota_s * 1.25:
                    item.setBackground(COLOR_OK)
                elif n <= cuota_s * 1.5:
                    item.setBackground(COLOR_WARN)
                else:
                    item.setBackground(COLOR_OVER)
                self.tabla_heatmap.setItem(row, col + 1, item)

    def actualizar_estadisticas(self):
        """Actualizar todas las estadísticas usando el Use Case."""
        try:
            # Obtener todas las estadísticas de forma centralizada
            self._datos = self._use_case.execute()

            # Actualizar cada sección de la UI
            self._actualizar_resumen_ui()
            self._actualizar_tabla_profesores_ui()
            self._actualizar_tabla_zonas_ui()
            self._actualizar_graficos_ui()
            self._actualizar_heatmap_ui()
        except Exception as e:
            self.manejar_excepcion(e, "actualizar estadísticas")

    def _actualizar_resumen_ui(self):
        """Actualizar el resumen general con datos del DTO."""
        resumen = self._datos.resumen

        self.label_total_guardias.setText(f"Total Guardias: {resumen.total_guardias}")
        self.label_total_profesores.setText(
            f"Profesores Activos: {resumen.profesores_con_guardias} / {resumen.total_profesores}"
        )
        self.label_total_zonas.setText(f"Zonas Configuradas: {resumen.total_zonas}")

        if resumen.total_guardias > 0 and resumen.profesores_con_guardias > 0:
            self.label_cobertura.setText(f"Cobertura Estimada: {resumen.cobertura_estimada}%")

            # Info adicional
            porcentaje_manana = int(resumen.guardias_manana / resumen.total_guardias * 100)
            porcentaje_tarde = int(resumen.guardias_tarde / resumen.total_guardias * 100)

            info = f"""
            📊 Detalles:
            • Guardias de Mañana: {resumen.guardias_manana} ({porcentaje_manana}%)
            • Guardias de Tarde: {resumen.guardias_tarde} ({porcentaje_tarde}%)
            • Promedio por profesor: {resumen.promedio_por_profesor:.1f} guardias
            """
            self.label_info.setText(info)
        else:
            self.label_cobertura.setText("Cobertura Estimada: 0%")
            self.label_info.setText("No hay guardias generadas todavía.")

    def _actualizar_tabla_profesores_ui(self):
        """Actualizar la tabla de estadísticas por profesor con datos del DTO."""
        datos_profesor = self._datos.por_profesor

        self.tabla_profesores.setRowCount(len(datos_profesor))

        for i, prof_dto in enumerate(datos_profesor):
            self.tabla_profesores.setItem(i, 0, QTableWidgetItem(prof_dto.nombre_completo))

            # Total (centrado)
            total_item = QTableWidgetItem(str(prof_dto.total))
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_profesores.setItem(i, 1, total_item)

            # Mañana (centrado)
            manana_item = QTableWidgetItem(str(prof_dto.manana))
            manana_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_profesores.setItem(i, 2, manana_item)

            # Tarde (centrado)
            tarde_item = QTableWidgetItem(str(prof_dto.tarde))
            tarde_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_profesores.setItem(i, 3, tarde_item)

            # Porcentaje (centrado)
            porcentaje_item = QTableWidgetItem(f"{prof_dto.porcentaje:.1f}%")
            porcentaje_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_profesores.setItem(i, 4, porcentaje_item)

            # Estado
            self.tabla_profesores.setItem(i, 5, QTableWidgetItem(prof_dto.estado))

            # Fecha Inicio Guardias (centrado)
            fecha_inicio_text = (
                prof_dto.fecha_inicio_guardias.strftime("%d/%m/%Y")
                if prof_dto.fecha_inicio_guardias
                else "-"
            )
            fecha_inicio_item = QTableWidgetItem(fecha_inicio_text)
            fecha_inicio_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_profesores.setItem(i, 6, fecha_inicio_item)

            # Fecha Fin Guardias (centrado)
            fecha_fin_text = (
                prof_dto.fecha_fin_guardias.strftime("%d/%m/%Y")
                if prof_dto.fecha_fin_guardias
                else "-"
            )
            fecha_fin_item = QTableWidgetItem(fecha_fin_text)
            fecha_fin_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_profesores.setItem(i, 7, fecha_fin_item)

    def _actualizar_tabla_zonas_ui(self):
        """Actualizar la tabla de estadísticas por zona con datos del DTO."""
        datos_zona = self._datos.por_zona

        self.tabla_zonas.setRowCount(len(datos_zona))

        todos_na = all(zona_dto.porcentaje_cobertura in ("N/A", "-", "") for zona_dto in datos_zona)
        self.tabla_zonas.setColumnHidden(3, todos_na)

        for i, zona_dto in enumerate(datos_zona):
            self.tabla_zonas.setItem(i, 0, QTableWidgetItem(zona_dto.nombre_zona))
            self.tabla_zonas.setItem(i, 1, QTableWidgetItem(str(zona_dto.total_guardias)))
            self.tabla_zonas.setItem(i, 2, QTableWidgetItem(str(zona_dto.profesores_diferentes)))
            self.tabla_zonas.setItem(i, 3, QTableWidgetItem(zona_dto.porcentaje_cobertura))

    def _actualizar_graficos_ui(self):
        """Actualizar los gráficos con datos del DTO."""
        grafico_prof = self._datos.grafico_profesores
        if grafico_prof.cantidades:
            colores = ["#007ACC"] * len(grafico_prof.nombres)
            datos_prof = list(zip(grafico_prof.nombres, grafico_prof.cantidades, colores))
            self.canvas_profesores.set_datos(datos_prof)

        grafico_zonas = self._datos.grafico_zonas
        if grafico_zonas.cantidades:
            datos_zonas = list(zip(grafico_zonas.nombres, grafico_zonas.cantidades))
            self.canvas_zonas.set_datos(datos_zonas)

    def refrescar(self):
        """Refrescar las estadísticas (útil después de generar guardias)."""
        self.actualizar_estadisticas()


