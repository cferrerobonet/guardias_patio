"""
Formulario de calendario de guardias.

Este módulo implementa la UI para visualizar guardias asignadas
por fecha, con filtros por profesor, zona y turno.
"""

from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QCalendarWidget,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableView,
    QTextEdit,
    QVBoxLayout,
)

import ui_styles as styles
from models.models import Guardia, Profesor, Zona
from presentation.forms.base_form import BaseForm
from utils.icon_manager import IconManager


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
                circulo_x, circulo_y, circulo_size, circulo_size,
                Qt.AlignmentFlag.AlignCenter,
                str(num_guardias)
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
                    first_day = QDate(
                        self.yearShown(),
                        self.monthShown(),
                        1
                    )

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
                        fecha_qdate = QDate(
                            self.yearShown(),
                            self.monthShown(),
                            day_number
                        )
                        fecha_py = fecha_qdate.toPyDate()

                        # Solo actualizar tooltip si cambió la fecha
                        if self._last_tooltip_date != fecha_py:
                            self._last_tooltip_date = fecha_py
                            num_guardias = self._contar_guardias(fecha_py)

                            if num_guardias > 0:
                                try:
                                    guardias = self.session.query(Guardia).filter(
                                        Guardia.fecha == fecha_py
                                    ).all()

                                    if guardias:
                                        tooltip_lines = [
                                            f"📅 {fecha_py.strftime('%d/%m/%Y')}"
                                        ]
                                        tooltip_lines.append(
                                            f"Total: {num_guardias} guardia(s)"
                                        )

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
                                                f"🕐 {turno.upper()}: "
                                                f"{len(guardias_grupo)}"
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
                                        QToolTip.showText(
                                            global_pos,
                                            "\n".join(tooltip_lines)
                                        )
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
                count = self.session.query(Guardia).filter(
                    Guardia.fecha == fecha
                ).count()
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
        self.cargar_filtros()
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

        # Panel izquierdo: Calendario
        main_horizontal.addLayout(self._crear_panel_calendario())

        # Panel derecho: Filtros y detalles
        main_horizontal.addLayout(self._crear_panel_filtros())

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
        self.btn_mes_anterior.setIcon(
            icon_manager.get_icon("chevron-left", "white", 20)
        )
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
        self.btn_mes_siguiente.setIcon(
            icon_manager.get_icon("chevron-right", "white", 20)
        )
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
        self.btn_hoy.setIcon(
            icon_manager.get_icon("calendar-month", "white", 20)
        )
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
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
        mes_nombre = meses_es[fecha.month() - 1]
        self.label_mes_anio.setText(f"{mes_nombre} {fecha.year()}")

    def _on_fecha_clicked(self, qdate):
        """Manejar clic en una fecha del calendario."""
        self.actualizar_guardias_dia(qdate)

    def _crear_panel_filtros(self) -> QVBoxLayout:
        """Crear panel con filtros y detalles."""
        panel = QVBoxLayout()

        # Filtros
        filtros_label = QLabel("Filtros:")
        filtros_label.setStyleSheet(styles.STYLE_LABEL_FIELD + " margin-top: 10px;")
        panel.addWidget(filtros_label)

        # Filtro por profesor
        label_profesor_filtro = QLabel("Profesor:")
        label_profesor_filtro.setStyleSheet(styles.STYLE_LABEL_FIELD)
        panel.addWidget(label_profesor_filtro)

        self.filtro_profesor = QComboBox()
        self.filtro_profesor.addItem("Todos los profesores", None)
        self.filtro_profesor.currentIndexChanged.connect(self.aplicar_filtros)
        panel.addWidget(self.filtro_profesor)

        # Filtro por zona
        label_zona_filtro = QLabel("Zona:")
        label_zona_filtro.setStyleSheet(styles.STYLE_LABEL_FIELD)
        panel.addWidget(label_zona_filtro)

        self.filtro_zona = QComboBox()
        self.filtro_zona.addItem("Todas las zonas", None)
        self.filtro_zona.currentIndexChanged.connect(self.aplicar_filtros)
        panel.addWidget(self.filtro_zona)

        # Filtro por turno
        label_turno_filtro = QLabel("Turno:")
        label_turno_filtro.setStyleSheet(styles.STYLE_LABEL_FIELD)
        panel.addWidget(label_turno_filtro)

        self.filtro_turno = QComboBox()
        self.filtro_turno.addItems(["Todos", "mañana", "tarde"])
        self.filtro_turno.currentIndexChanged.connect(self.aplicar_filtros)
        panel.addWidget(self.filtro_turno)

        # Botón para limpiar filtros
        self.limpiar_filtros_btn = QPushButton("Limpiar filtros")
        self.limpiar_filtros_btn.clicked.connect(self.limpiar_filtros)
        panel.addWidget(self.limpiar_filtros_btn)

        # Detalles del día seleccionado
        detalles_label = QLabel("Guardias del día seleccionado:")
        detalles_label.setStyleSheet(styles.STYLE_LABEL_FIELD + " margin-top: 20px;")
        panel.addWidget(detalles_label)

        self.guardias_dia_text = QTextEdit()
        self.guardias_dia_text.setReadOnly(True)
        self.guardias_dia_text.setMaximumHeight(400)
        panel.addWidget(self.guardias_dia_text)

        # Estadísticas
        stats_label = QLabel("Estadísticas:")
        stats_label.setStyleSheet(styles.STYLE_LABEL_FIELD + " margin-top: 10px;")
        panel.addWidget(stats_label)

        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(150)
        panel.addWidget(self.stats_text)

        return panel

    def cargar_filtros(self):
        """Cargar opciones de filtros desde la base de datos."""
        try:
            # Cargar profesores
            profesores = self.session.query(Profesor).all()
            self.filtro_profesor.clear()
            self.filtro_profesor.addItem("Todos los profesores", None)
            for prof in profesores:
                self.filtro_profesor.addItem(prof.nombre_completo, prof.id)

            # Cargar zonas
            zonas = self.session.query(Zona).all()
            self.filtro_zona.clear()
            self.filtro_zona.addItem("Todas las zonas", None)
            for zona in zonas:
                self.filtro_zona.addItem(zona.nombre_zona, zona.id)

        except Exception as e:
            self.manejar_excepcion(e, "cargar filtros")

    def limpiar_filtros(self):
        """Limpiar todos los filtros."""
        self.filtro_profesor.setCurrentIndex(0)
        self.filtro_zona.setCurrentIndex(0)
        self.filtro_turno.setCurrentIndex(0)

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
        try:
            fecha = qdate.toPyDate()

            # Construir query con filtros
            query = self.session.query(Guardia).filter(Guardia.fecha == fecha)

            profesor_id = self.filtro_profesor.currentData()
            if profesor_id is not None:
                query = query.filter(Guardia.profesor_id == profesor_id)

            zona_id = self.filtro_zona.currentData()
            if zona_id is not None:
                query = query.filter(Guardia.zona_id == zona_id)

            turno_filtro = self.filtro_turno.currentText()
            if turno_filtro != "Todos":
                query = query.filter(Guardia.turno == turno_filtro)

            guardias = query.all()

            # Formatear y mostrar
            if not guardias:
                self.guardias_dia_text.setText(
                    f"📅 {fecha.strftime('%d/%m/%Y')}\n\n"
                    "No hay guardias asignadas para este día con los filtros aplicados."
                )
            else:
                lineas = [f"📅 {fecha.strftime('%d/%m/%Y')} - {len(guardias)} guardia(s)\n"]

                # Agrupar por turno y recreo
                guardias_por_turno = {}
                for g in guardias:
                    key = (g.turno, g.recreo)
                    if key not in guardias_por_turno:
                        guardias_por_turno[key] = []
                    guardias_por_turno[key].append(g)

                # Mostrar organizadas
                for (turno, recreo), guardias_grupo in sorted(guardias_por_turno.items()):
                    lineas.append(f"\n🕐 {turno.upper()} - Recreo {recreo}")
                    lineas.append("─" * 40)
                    for g in guardias_grupo:
                        prof_nombre = (
                            g.profesor.nombre_completo if g.profesor else "Sin profesor"
                        )
                        zona_nombre = g.zona.nombre_zona if g.zona else "Sin zona"
                        lineas.append(f"  • {prof_nombre} → {zona_nombre}")

                self.guardias_dia_text.setText("\n".join(lineas))

        except Exception as e:
            self.manejar_excepcion(e, "actualizar guardias del día")

    def actualizar_estadisticas(self):
        """Actualizar estadísticas generales."""
        try:
            # Construir query con filtros
            query = self.session.query(Guardia)

            profesor_id = self.filtro_profesor.currentData()
            if profesor_id is not None:
                query = query.filter(Guardia.profesor_id == profesor_id)

            zona_id = self.filtro_zona.currentData()
            if zona_id is not None:
                query = query.filter(Guardia.zona_id == zona_id)

            turno_filtro = self.filtro_turno.currentText()
            if turno_filtro != "Todos":
                query = query.filter(Guardia.turno == turno_filtro)

            total_guardias = query.count()

            # Contar por turno
            guardias_manana = (
                query.filter(Guardia.turno == "mañana").count()
                if turno_filtro == "Todos"
                else (total_guardias if turno_filtro == "mañana" else 0)
            )
            guardias_tarde = (
                query.filter(Guardia.turno == "tarde").count()
                if turno_filtro == "Todos"
                else (total_guardias if turno_filtro == "tarde" else 0)
            )

            lineas = [
                f"📊 Total guardias: {total_guardias}",
                f"🌅 Mañana: {guardias_manana}",
                f"🌆 Tarde: {guardias_tarde}",
            ]

            # Si hay filtro de profesor, mostrar estadísticas personales
            if profesor_id is not None:
                profesor = self.session.query(Profesor).get(profesor_id)
                if profesor:
                    lineas.append(f"\n👤 {profesor.nombre_completo}")
                    lineas.append(f"   Turno: {profesor.turno}")
                    lineas.append(f"   Tutor: {'Sí' if profesor.tutor else 'No'}")

            self.stats_text.setText("\n".join(lineas))

        except Exception as e:
            self.manejar_excepcion(e, "actualizar estadísticas")
