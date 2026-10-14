"""
Panel de estadísticas para analizar la distribución de guardias.

Muestra métricas, gráficos y análisis de cobertura.
Utiliza ObtenerEstadisticasPanelUseCase para separar lógica de presentación.
"""

from collections import defaultdict
from datetime import timedelta

from PyQt6.QtCore import Qt
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
from presentation.theme.modo_oscuro import color_fondo, color_texto
from presentation.themes.tema_aplicacion import (
    BORDER_LIGHT,
    CONTENT_BG,
    TEXT_PRIMARY,
    get_table_style,
)
from presentation.widgets.bar_chart_widget import BarChartWidget, DivergingBarChartWidget
from utils.icons import icon_for_button
from utils.orden import clave_alfabetica
from utils.ui_helpers import dotar_de_contrato

MplCanvas = BarChartWidget


class PanelEstadisticas(BaseForm):
    #: Cuota y diferencia en lugar del «% del total», que no dice si el reparto es
    #: justo: un profesor a media jornada tiene la mitad y está bien (2026-10-03).
    COLUMNAS_PROFESORES = (
        ("Profesor", ""),
        ("Cuota", "Guardias que le corresponden en el reparto oficial, ya descontadas "
                  "sus voluntarias."),
        ("Asignadas", "Guardias que tiene en el calendario del curso activo, "
                      "sustituciones incluidas."),
        ("Diferencia", "Asignadas menos cuota. Hasta ±1 es redondeo del reparto."),
        ("Mañana", ""),
        ("Tarde", ""),
        ("Estado", ""),
        ("Inicio guardias", "Fecha desde la que tiene guardias. «-» sin restricción."),
        ("Fin guardias", "Fecha hasta la que tiene guardias. «-» sin restricción."),
        ("Veces sustituto", "Guardias que ha cubierto en lugar de otro."),
        ("Veces sustituido", "Guardias suyas que ha cubierto otro."),
    )

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
        layout_principal.addWidget(btn_refrescar, alignment=Qt.AlignmentFlag.AlignLeft)

        # Pestañas
        self.tabs = QTabWidget()
        self.tabs.addTab(self._crear_tab_resumen(), "Resumen")
        self.tabs.addTab(self._crear_tab_profesores(), "Por Profesor")
        self.tabs.addTab(self._crear_tab_zonas(), "Por Zona")
        # La equidad está en los gráficos (diferencia con la cuota); el mapa de
        # calor enseña la carga de cada semana, y así se llamaba al revés.
        self.tabs.addTab(self._crear_tab_graficos(), "Gráficos de equidad")
        self.tabs.addTab(self._crear_tab_heatmap(), "Carga semanal")

        layout_principal.addWidget(self.tabs)
        self.setLayout(layout_principal)

        # Cargar datos iniciales
        self.actualizar_estadisticas()

    def _crear_tab_resumen(self) -> QWidget:
        """Crear la pestaña de resumen general."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Tarjetas de métricas
        self.label_total_guardias = QLabel("Guardias del curso: 0")
        self.label_total_profesores = QLabel("Profesores con guardias: 0")
        self.label_total_zonas = QLabel("Reparto: sin datos")
        self.label_cobertura = QLabel("Cobertura: 0%")

        estilo_metrica = f"""
            QLabel {{
                background-color: {CONTENT_BG};
                padding: 12px;
                border-radius: 10px;
                border: 1px solid {BORDER_LIGHT};
                font-size: 14px;
                font-weight: 600;
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
        dotar_de_contrato(
            self.tabla_profesores,
            "Reparto por profesor",
            "Guardias asignadas a cada profesor frente a la cuota que le corresponde",
        )
        self.tabla_profesores.setColumnCount(len(self.COLUMNAS_PROFESORES))
        self.tabla_profesores.setHorizontalHeaderLabels(
            [titulo for titulo, _ in self.COLUMNAS_PROFESORES]
        )
        # Ajustar ancho automático de columnas al contenido
        self.tabla_profesores.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.tabla_profesores.setStyleSheet(get_table_style())
        modelo = self.tabla_profesores.horizontalHeader().model()
        for columna, (_, ayuda) in enumerate(self.COLUMNAS_PROFESORES):
            if ayuda:
                modelo.setHeaderData(
                    columna, Qt.Orientation.Horizontal, ayuda, Qt.ItemDataRole.ToolTipRole
                )

        layout.addWidget(self.tabla_profesores)
        widget.setLayout(layout)
        return widget

    def _crear_tab_zonas(self) -> QWidget:
        """Crear la pestaña de estadísticas por zona."""
        widget = QWidget()
        layout = QVBoxLayout()

        self.tabla_zonas = QTableWidget()
        dotar_de_contrato(
            self.tabla_zonas,
            "Reparto por zona",
            "Guardias de cada zona, cuántos profesores distintos pasan por ella y su cobertura",
        )
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

        # ¿Es justo el reparto? Lo que importa es la distancia de cada uno a su
        # cuota, no el número bruto de guardias. La tarta por zona salía siempre
        # en porciones iguales: cada recreo cubre todas las zonas (2026-10-03).
        self.canvas_diferencias = DivergingBarChartWidget(
            titulo="Diferencia de cada profesor con su cuota",
            rotulos=("Por debajo de su cuota", "Por encima de su cuota"),
        )
        scroll_layout.addWidget(self.canvas_diferencias)

        self.canvas_sustitutos = BarChartWidget(
            titulo="Quién ha cubierto más sustituciones", horizontal=True
        )
        scroll_layout.addWidget(self.canvas_sustitutos)

        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        widget.setLayout(layout)
        return widget

    def _crear_tab_heatmap(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout()

        leyenda = QLabel(
            "Guardias de cada profesor en cada semana del curso activo. Cuanto más "
            "oscuro, más guardias esa semana: 1 · 2 · 3 o más."
        )
        leyenda.setWordWrap(True)
        leyenda.setStyleSheet("padding: 6px; font-size: 12px;")
        layout.addWidget(leyenda)

        self.tabla_heatmap = QTableWidget()
        dotar_de_contrato(
            self.tabla_heatmap,
            "Mapa de calor de guardias",
            "Guardias de cada profesor en cada semana del curso activo",
            ordenable=False,
        )
        self.tabla_heatmap.setStyleSheet(get_table_style())
        # Nombre entero y semanas de ancho fijo con desplazamiento: estirarlo todo
        # dejaba los nombres en «B…» con un curso de cuarenta semanas.
        cabecera = self.tabla_heatmap.horizontalHeader()
        cabecera.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        cabecera.setDefaultSectionSize(52)
        self.tabla_heatmap.verticalHeader().setVisible(False)
        layout.addWidget(self.tabla_heatmap)

        widget.setLayout(layout)
        return widget

    #: Escala de un solo tono para 1, 2 y 3 o más guardias en la semana (validada:
    #: monótona y con contraste). Antes se pintaba en verde, ámbar y rojo frente a
    #: una cuota que sólo miraba las horas de contrato (2026-10-03).
    ESCALA_SEMANAL = (("#9FCFA7", "#1D2A20"), ("#2C7A3A", "#FFFFFF"), ("#1C5226", "#FFFFFF"))

    def _actualizar_heatmap_ui(self):
        from infrastructure.database.models import CursoEscolar

        consulta = self.session.query(Guardia)
        curso = self.session.query(CursoEscolar).filter_by(activo=True).first()
        if curso is not None:
            consulta = consulta.filter(Guardia.curso_id == curso.id)
        guardias = [g for g in consulta.all() if g.fecha]
        profesores = self.session.query(Profesor).all()

        if not guardias or not profesores:
            self.tabla_heatmap.setRowCount(0)
            self.tabla_heatmap.setColumnCount(0)
            return

        fecha_min = min(g.fecha for g in guardias)
        fecha_max = max(g.fecha for g in guardias)

        # Lunes de cada semana en el rango
        semanas = []
        d = fecha_min - timedelta(days=fecha_min.weekday())
        while d <= fecha_max:
            semanas.append(d)
            d += timedelta(days=7)

        conteo: dict = defaultdict(int)
        for g in guardias:
            conteo[(g.profesor_id, g.fecha - timedelta(days=g.fecha.weekday()))] += 1

        col_headers = [f"S{i + 1}\n{s.strftime('%d/%m')}" for i, s in enumerate(semanas)]
        self.tabla_heatmap.setColumnCount(len(semanas) + 1)
        self.tabla_heatmap.setHorizontalHeaderLabels(["Profesor"] + col_headers)
        self.tabla_heatmap.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.tabla_heatmap.setRowCount(len(profesores))

        ordenados = sorted(profesores, key=lambda p: clave_alfabetica(p.nombre_completo))
        for row, prof in enumerate(ordenados):
            nombre_item = QTableWidgetItem(prof.nombre_completo)
            nombre_item.setFlags(nombre_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabla_heatmap.setItem(row, 0, nombre_item)

            for col, lunes in enumerate(semanas):
                n = conteo.get((prof.id, lunes), 0)
                item = QTableWidgetItem(str(n) if n > 0 else "")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if n > 0:
                    fondo, texto = self.ESCALA_SEMANAL[min(n, 3) - 1]
                    item.setBackground(color_fondo(fondo))
                    item.setForeground(color_texto(texto))
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
        """Cifras que responden a «¿está cubierto el curso?» y «¿es justo el reparto?»."""
        resumen = self._datos.resumen

        if resumen.ranuras_curso:
            self.label_total_guardias.setText(
                f"Guardias del curso: {resumen.total_guardias} de {resumen.ranuras_curso} "
                "ranuras del reparto oficial"
            )
        else:
            self.label_total_guardias.setText(f"Guardias del curso: {resumen.total_guardias}")
        self.label_total_profesores.setText(
            f"Profesores con guardias: {resumen.profesores_con_guardias} "
            f"de {resumen.total_profesores}"
        )

        if resumen.total_guardias == 0:
            self.label_total_zonas.setText("Reparto: no hay guardias generadas en este curso")
        elif resumen.ranuras_curso is None:
            self.label_total_zonas.setText(
                "Reparto: sin configuración del curso no se puede comparar con las cuotas"
            )
        elif resumen.fuera_de_cuota == 0:
            self.label_total_zonas.setText(
                "Reparto: todos los profesores están en su cuota (±1)"
            )
        else:
            self.label_total_zonas.setText(
                f"Reparto: {resumen.fuera_de_cuota} profesores se separan más de 1 de su "
                f"cuota. Mayor diferencia: {resumen.mayor_diferencia:+d} "
                f"({resumen.profesor_mayor_diferencia})"
            )

        if resumen.total_guardias > 0:
            if resumen.ranuras_curso:
                cobertura = round(resumen.total_guardias / resumen.ranuras_curso * 100)
                self.label_cobertura.setText(f"Cobertura del curso: {cobertura}%")
            else:
                self.label_cobertura.setText("Cobertura del curso: sin ranuras con que comparar")
            porcentaje_manana = round(resumen.guardias_manana / resumen.total_guardias * 100)
            porcentaje_sust = round(resumen.sustituciones / resumen.total_guardias * 100)
            self.label_info.setText(
                f"Mañana: {resumen.guardias_manana} ({porcentaje_manana}%) · "
                f"Tarde: {resumen.guardias_tarde} ({100 - porcentaje_manana}%)\n"
                f"Sustituciones: {resumen.sustituciones} ({porcentaje_sust}% de las guardias)\n"
                f"Zonas: {resumen.total_zonas}"
            )
        else:
            self.label_cobertura.setText("Cobertura del curso: 0%")
            self.label_info.setText("No hay guardias generadas todavía.")

    def _actualizar_tabla_profesores_ui(self):
        """Actualizar la tabla de estadísticas por profesor con datos del DTO."""
        datos_profesor = self._datos.por_profesor
        self.tabla_profesores.setSortingEnabled(False)
        self.tabla_profesores.setRowCount(len(datos_profesor))

        def _fecha(valor):
            return valor.strftime("%d/%m/%Y") if valor else "-"

        def _numero(valor, con_signo=False):
            if valor is None:
                return "—"
            return f"{valor:+d}" if con_signo and valor else str(valor)

        for i, prof in enumerate(datos_profesor):
            valores = (
                prof.nombre_completo,
                _numero(prof.cuota),
                str(prof.total),
                _numero(prof.diferencia, con_signo=True),
                str(prof.manana),
                str(prof.tarde),
                prof.estado,
                _fecha(prof.fecha_inicio_guardias),
                _fecha(prof.fecha_fin_guardias),
                str(prof.veces_sustituto) if prof.veces_sustituto else "—",
                str(prof.veces_sustituido) if prof.veces_sustituido else "—",
            )
            for columna, texto in enumerate(valores):
                item = QTableWidgetItem(texto)
                if columna not in (0, 6):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla_profesores.setItem(i, columna, item)

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
        diferencias = self._datos.grafico_diferencias
        self.canvas_diferencias.set_datos(list(zip(diferencias.nombres, diferencias.cantidades)))

        sustitutos = self._datos.grafico_sustitutos
        self.canvas_sustitutos.set_datos(
            [(n, c, "") for n, c in zip(sustitutos.nombres, sustitutos.cantidades)]
        )

    def refrescar(self):
        """Refrescar las estadísticas (útil después de generar guardias)."""
        self.actualizar_estadisticas()
