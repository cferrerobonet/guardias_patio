"""
Formulario de calendario de guardias.

Este módulo implementa la UI para visualizar guardias asignadas
por fecha, con filtros por profesor, zona y turno.
"""

from models.models import Guardia
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QCalendarWidget,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableView,
    QVBoxLayout,
)
from utils.icon_manager import IconManager

from presentation.forms.base_form import BaseForm
from presentation.forms.calendario_widgets import (
    DetallesDiaWidget,
    FiltrosGuardiasWidget,
)


class CalendarioGuardiasWidget(QCalendarWidget):
    """Widget de calendario personalizado que muestra información de guardias."""

    def __init__(self, session):
        """
        Inicializar calendario personalizado.

        Args:
            session: Sesión de base de datos
        """
        super().__init__()
        self.session = session
        self._guardias_cache = {}  # Cache de guardias por fecha
        self.setMouseTracking(True)  # Habilitar tracking del mouse para tooltips

        # Hacer el calendario más compacto
        self.setStyleSheet("""
            QCalendarWidget QTableView {
                selection-background-color: #2196F3;
                alternate-background-color: #f9f9f9;
            }
            QCalendarWidget QWidget {
                alternate-background-color: white;
            }
            QCalendarWidget QAbstractItemView:enabled {
                font-size: 11px;
                color: #333;
            }
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background-color: #2196F3;
            }
        """)

        # Instalar filtro de eventos para tooltips en el viewport
        self._table_view = None
        view = self.findChild(QTableView)
        if view:
            self._table_view = view
            view.setMouseTracking(True)
            view.viewport().setMouseTracking(True)
            view.viewport().installEventFilter(self)

        # Variable para tracking del último tooltip mostrado
        self._last_tooltip_date = None

    def paintCell(self, painter, rect, qdate):
        """
        Pintar cada celda del calendario con información de guardias.

        Args:
            painter: QPainter para dibujar
            rect: QRect del área de la celda
            qdate: QDate de la celda
        """
        # Llamar al pintado base
        super().paintCell(painter, rect, qdate)

        # Obtener guardias del día
        fecha_py = qdate.toPyDate()
        num_guardias = self._contar_guardias(fecha_py)

        if num_guardias > 0:
            # Dibujar indicador de guardias
            # Fondo de color según cantidad
            if num_guardias >= 8:
                color = QColor("#4CAF50")  # Verde - muchas guardias
            elif num_guardias >= 4:
                color = QColor("#2196F3")  # Azul - cantidad normal
            else:
                color = QColor("#FF9800")  # Naranja - pocas guardias

            # Dibujar círculo con el número
            painter.save()
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)

            # Círculo en la esquina inferior derecha
            circulo_size = 20
            circulo_x = rect.x() + rect.width() - circulo_size - 4
            circulo_y = rect.y() + rect.height() - circulo_size - 4
            painter.drawEllipse(circulo_x, circulo_y, circulo_size, circulo_size)

            # Número de guardias
            painter.setPen(QColor("white"))
            font = QFont()
            font.setBold(True)
            font.setPixelSize(11)
            painter.setFont(font)
            painter.drawText(
                circulo_x,
                circulo_y,
                circulo_size,
                circulo_size,
                Qt.AlignmentFlag.AlignCenter,
                str(num_guardias),
            )

            painter.restore()

    def eventFilter(self, obj, e):
        """
        Filtrar eventos del viewport para mostrar tooltips en las celdas.

        Args:
            obj: Objeto que generó el evento
            e: Evento
        """
        from PyQt6.QtCore import QEvent
        from PyQt6.QtWidgets import QToolTip

        # Manejar tanto ToolTip como MouseMove para asegurar que funcione
        if e.type() in (QEvent.Type.ToolTip, QEvent.Type.MouseMove):
            if self._table_view and obj == self._table_view.viewport():
                pos = e.pos()
                index = self._table_view.indexAt(pos)

                if index.isValid():
                    # Calcular la fecha basada en el índice
                    row = index.row()
                    col = index.column()

                    # Obtener el primer día del mes visible
                    first_day = QDate(self.yearShown(), self.monthShown(), 1)

                    # Calcular el offset del primer día de la semana
                    day_of_week = first_day.dayOfWeek()
                    # Ajustar: Lunes=1, Domingo=7 -> necesitamos offset para grid
                    # En Qt, Lunes=1, Martes=2, ... Domingo=7
                    # En el grid visual, normalmente Domingo=0, Lunes=1, ..., Sábado=6
                    # Pero QCalendarWidget usa Lunes como primer día por defecto
                    offset = day_of_week - 1  # Lunes será 0, Martes 1, etc.

                    # Calcular el número de día
                    day_number = row * 7 + col - offset + 1

                    # Validar que el día está en el rango del mes
                    if 1 <= day_number <= first_day.daysInMonth():
                        fecha_qdate = QDate(self.yearShown(), self.monthShown(), day_number)
                        fecha_py = fecha_qdate.toPyDate()

                        # Solo actualizar tooltip si cambió la fecha
                        if self._last_tooltip_date != fecha_py:
                            self._last_tooltip_date = fecha_py
                            num_guardias = self._contar_guardias(fecha_py)

                            if num_guardias > 0:
                                try:
                                    guardias = (
                                        self.session.query(Guardia)
                                        .filter(Guardia.fecha == fecha_py)
                                        .all()
                                    )

                                    if guardias:
                                        tooltip_lines = [f"📅 {fecha_py.strftime('%d/%m/%Y')}"]
                                        tooltip_lines.append(f"Total: {num_guardias} guardia(s)")

                                        # Agrupar por turno
                                        guardias_por_turno = {}
                                        for g in guardias:
                                            turno = g.turno if g.turno else "Sin turno"
                                            if turno not in guardias_por_turno:
                                                guardias_por_turno[turno] = []
                                            guardias_por_turno[turno].append(g)

                                        for turno, guardias_grupo in sorted(
                                            guardias_por_turno.items()
                                        ):
                                            tooltip_lines.append("")
                                            tooltip_lines.append(
                                                f"🕐 {turno.upper()}: {len(guardias_grupo)}"
                                            )
                                            # Mostrar primeros 3 profesores
                                            for guardia in guardias_grupo[:3]:
                                                if guardia.profesor:
                                                    tooltip_lines.append(
                                                        f"  • {guardia.profesor.nombre}"
                                                    )
                                            if len(guardias_grupo) > 3:
                                                tooltip_lines.append(
                                                    f"  • ... y {len(guardias_grupo) - 3} más"
                                                )

                                        # Mostrar tooltip
                                        global_pos = self._table_view.viewport().mapToGlobal(pos)
                                        QToolTip.showText(global_pos, "\n".join(tooltip_lines))
                                        if e.type() == QEvent.Type.ToolTip:
                                            return True
                                except Exception as ex:
                                    print(f"Error mostrando tooltip: {ex}")
                            else:
                                # No hay guardias, ocultar tooltip
                                QToolTip.hideText()
                                self._last_tooltip_date = None
                else:
                    # Fuera de una celda válida
                    QToolTip.hideText()
                    self._last_tooltip_date = None

        return super().eventFilter(obj, e)

    def _contar_guardias(self, fecha):
        """
        Contar guardias en una fecha específica.

        Args:
            fecha: Fecha (date object)

        Returns:
            int: Número de guardias
        """
        # Usar cache para evitar consultas repetidas
        if fecha not in self._guardias_cache:
            try:
                count = self.session.query(Guardia).filter(Guardia.fecha == fecha).count()
                self._guardias_cache[fecha] = count
            except Exception:
                self._guardias_cache[fecha] = 0

        return self._guardias_cache[fecha]

    def actualizar_cache(self):
        """Limpiar y actualizar el cache de guardias."""
        self._guardias_cache = {}
        self.updateCells()


class CalendarioGuardiasForm(BaseForm):
    """Formulario para visualizar calendario de guardias."""

    def __init__(self, session):
        """
        Inicializar formulario de calendario.

        Args:
            session: Sesión de base de datos
        """
        super().__init__(session)
        self.setWindowTitle("Calendario de Guardias")
        self.setup_ui()

        # Cargar datos iniciales
        self.filtros_widget.cargar_datos()
        self.actualizar_estadisticas()
        self.actualizar_guardias_dia(self.calendario.selectedDate())

    def setup_ui(self):
        """Construir la interfaz del formulario."""
        layout = QVBoxLayout()

        # Título
        titulo = QLabel("Calendario de Guardias")
        titulo.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(titulo)

        # Descripción
        desc = QLabel(
            "Visualiza las guardias asignadas por fecha. "
            "Selecciona un día en el calendario para ver los detalles."
        )
        layout.addWidget(desc)

        # Layout horizontal para calendario y filtros
        main_horizontal = QHBoxLayout()
        main_horizontal.setSpacing(20)
        main_horizontal.setContentsMargins(10, 10, 10, 10)

        # Panel izquierdo: Calendario
        calendario_layout = self._crear_panel_calendario()
        main_horizontal.addLayout(calendario_layout, stretch=2)

        # Panel derecho: Filtros y detalles
        filtros_layout = self._crear_panel_filtros()
        main_horizontal.addLayout(filtros_layout, stretch=1)

        layout.addLayout(main_horizontal)
        self.setLayout(layout)

    def _crear_panel_calendario(self) -> QVBoxLayout:
        """Crear panel con calendario."""
        panel = QVBoxLayout()

        # Barra de navegación de mes/año
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(10)
        nav_layout.setContentsMargins(0, 0, 0, 15)

        # Botón mes anterior
        self.btn_mes_anterior = QPushButton("  ◀  Anterior")
        icon_manager = IconManager()
        self.btn_mes_anterior.setIcon(icon_manager.get_icon("chevron-left", "white", 20))
        self.btn_mes_anterior.setFixedSize(120, 40)
        self.btn_mes_anterior.setToolTip("Mes anterior")
        self.btn_mes_anterior.clicked.connect(self._mes_anterior)
        self.btn_mes_anterior.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: 2px solid #1976D2;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
                border: 2px solid #0D47A1;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        nav_layout.addWidget(self.btn_mes_anterior)

        # Label mes/año actual
        self.label_mes_anio = QLabel()
        self.label_mes_anio.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2196F3;
            background-color: #E3F2FD;
            padding: 8px;
            border-radius: 4px;
        """)
        self.label_mes_anio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nav_layout.addWidget(self.label_mes_anio, 1)

        # Botón mes siguiente
        self.btn_mes_siguiente = QPushButton("Siguiente  ▶")
        self.btn_mes_siguiente.setIcon(icon_manager.get_icon("chevron-right", "white", 20))
        self.btn_mes_siguiente.setFixedSize(120, 40)
        self.btn_mes_siguiente.setToolTip("Mes siguiente")
        self.btn_mes_siguiente.clicked.connect(self._mes_siguiente)
        self.btn_mes_siguiente.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: 2px solid #1976D2;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
                border: 2px solid #0D47A1;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        nav_layout.addWidget(self.btn_mes_siguiente)

        # Botón hoy
        self.btn_hoy = QPushButton("📅 Hoy")
        self.btn_hoy.setIcon(icon_manager.get_icon("calendar-month", "white", 20))
        self.btn_hoy.setFixedSize(100, 40)
        self.btn_hoy.setToolTip("Ir a la fecha de hoy")
        self.btn_hoy.clicked.connect(self._ir_a_hoy)
        self.btn_hoy.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: 2px solid #388E3C;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
                border: 2px solid #2E7D32;
            }
            QPushButton:pressed {
                background-color: #2E7D32;
            }
        """)
        nav_layout.addWidget(self.btn_hoy)

        panel.addLayout(nav_layout)

        # Calendario con formato mejorado y tamaño compacto
        self.calendario = CalendarioGuardiasWidget(self.session)
        self.calendario.setGridVisible(True)
        self.calendario.setVerticalHeaderFormat(
            QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader
        )
        # Hacer calendario más compacto - altura fija de 280px
        self.calendario.setFixedHeight(280)
        # Ocultar la barra de navegación nativa del calendario (usamos la nuestra)
        self.calendario.setNavigationBarVisible(False)
        # Estilo para hacer las celdas más compactas
        self.calendario.setStyleSheet("""
            QCalendarWidget QWidget {
                alternate-background-color: #f0f0f0;
            }
            QCalendarWidget QAbstractItemView:enabled {
                font-size: 10px;
                selection-background-color: #2196F3;
            }
            QCalendarWidget QTableView {
                gridline-color: #d0d0d0;
            }
        """)
        self.calendario.clicked.connect(self._on_fecha_clicked)
        self.calendario.currentPageChanged.connect(self._actualizar_label_mes_anio)
        panel.addWidget(self.calendario)

        # Actualizar label inicial
        self._actualizar_label_mes_anio()

        return panel

    def _mes_anterior(self):
        """Navegar al mes anterior."""
        fecha_actual = self.calendario.selectedDate()
        nueva_fecha = fecha_actual.addMonths(-1)
        self.calendario.setSelectedDate(nueva_fecha)
        self.calendario.showSelectedDate()

    def _mes_siguiente(self):
        """Navegar al mes siguiente."""
        fecha_actual = self.calendario.selectedDate()
        nueva_fecha = fecha_actual.addMonths(1)
        self.calendario.setSelectedDate(nueva_fecha)
        self.calendario.showSelectedDate()

    def _ir_a_hoy(self):
        """Ir a la fecha de hoy."""
        hoy = QDate.currentDate()
        self.calendario.setSelectedDate(hoy)
        self.calendario.showSelectedDate()

    def _actualizar_label_mes_anio(self):
        """Actualizar el label con el mes y año actual del calendario."""
        fecha = self.calendario.selectedDate()
        meses_es = [
            "Enero",
            "Febrero",
            "Marzo",
            "Abril",
            "Mayo",
            "Junio",
            "Julio",
            "Agosto",
            "Septiembre",
            "Octubre",
            "Noviembre",
            "Diciembre",
        ]
        mes_nombre = meses_es[fecha.month() - 1]
        self.label_mes_anio.setText(f"{mes_nombre} {fecha.year()}")

    def _on_fecha_clicked(self, qdate):
        """Manejar clic en una fecha del calendario."""
        self.actualizar_guardias_dia(qdate)

    def _crear_panel_filtros(self) -> QVBoxLayout:
        """Crear panel con filtros y detalles."""
        panel = QVBoxLayout()
        panel.setSpacing(10)
        panel.setContentsMargins(0, 0, 0, 0)

        # Widget de filtros
        self.filtros_widget = FiltrosGuardiasWidget(self.session)
        self.filtros_widget.filtros_cambiados.connect(self.aplicar_filtros)
        panel.addWidget(self.filtros_widget)

        # Widget de detalles del día y estadísticas
        self.detalles_widget = DetallesDiaWidget(self.session)
        panel.addWidget(self.detalles_widget)

        return panel

    def limpiar_filtros(self):
        """Limpiar todos los filtros."""
        self.filtros_widget.limpiar()

    def aplicar_filtros(self):
        """Aplicar filtros y actualizar visualización."""
        self.calendario.actualizar_cache()
        self.actualizar_guardias_dia(self.calendario.selectedDate())
        self.actualizar_estadisticas()

    def actualizar_guardias_dia(self, qdate):
        """
        Actualizar visualización de guardias para el día seleccionado.

        Args:
            qdate: Fecha seleccionada (QDate)
        """
        fecha = qdate.toPyDate()
        filtros = self.filtros_widget.get_datos()
        self.detalles_widget.actualizar_guardias_dia(fecha, filtros)

    def actualizar_estadisticas(self):
        """Actualizar estadísticas generales."""
        filtros = self.filtros_widget.get_datos()
        self.detalles_widget.actualizar_estadisticas(filtros)
