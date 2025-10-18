"""
Formulario de calendario de guardias.

Este módulo implementa la UI para visualizar guardias asignadas
por fecha, con filtros por profesor, zona y turno.
"""

import ui_styles as styles
from models.models import Guardia, Profesor, Zona
from PyQt6.QtWidgets import (
    QCalendarWidget,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from presentation.forms.base_form import BaseForm


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

        calendar_label = QLabel("Selecciona una fecha:")
        calendar_label.setStyleSheet(styles.STYLE_LABEL_FIELD + " margin-top: 10px;")
        panel.addWidget(calendar_label)

        self.calendario = QCalendarWidget()
        self.calendario.setGridVisible(True)
        self.calendario.clicked.connect(self.actualizar_guardias_dia)
        panel.addWidget(self.calendario)

        return panel

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
