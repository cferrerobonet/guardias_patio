"""
Widgets especializados para el formulario de calendario de guardias.

Este módulo contiene los componentes UI para visualizar y filtrar
guardias en el calendario.
"""

import ui_styles as styles
from models.models import Guardia, Profesor, Zona
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class FiltrosGuardiasWidget(QWidget):
    """Widget con controles de filtrado de guardias."""

    # Señal emitida cuando cambian los filtros
    filtros_cambiados = pyqtSignal()

    def __init__(self, session, parent=None):
        """
        Inicializar widget de filtros.

        Args:
            session: Sesión de base de datos
            parent: Widget padre
        """
        super().__init__(parent)
        self.session = session
        self._setup_ui()

    def _setup_ui(self):
        """Construir la interfaz del widget."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)

        # Título de sección
        filtros_label = QLabel("🔍 Filtros")
        filtros_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #1976D2;
            background-color: #E3F2FD;
            padding: 8px;
            border-radius: 4px;
            margin-top: 10px;
        """)
        layout.addWidget(filtros_label)

        # Filtro por profesor
        label_profesor_filtro = QLabel("👤 Profesor:")
        label_profesor_filtro.setStyleSheet("""
            font-size: 12px;
            font-weight: bold;
            color: #333;
            padding: 4px 0px;
        """)
        layout.addWidget(label_profesor_filtro)

        self.filtro_profesor = QComboBox()
        self.filtro_profesor.addItem("Todos los profesores", None)
        self.filtro_profesor.currentIndexChanged.connect(self.filtros_cambiados.emit)
        self.filtro_profesor.setStyleSheet(self._get_combo_style())
        layout.addWidget(self.filtro_profesor)

        # Filtro por zona
        label_zona_filtro = QLabel("📍 Zona:")
        label_zona_filtro.setStyleSheet("""
            font-size: 12px;
            font-weight: bold;
            color: #333;
            padding: 4px 0px;
        """)
        layout.addWidget(label_zona_filtro)

        self.filtro_zona = QComboBox()
        self.filtro_zona.addItem("Todas las zonas", None)
        self.filtro_zona.currentIndexChanged.connect(self.filtros_cambiados.emit)
        self.filtro_zona.setStyleSheet(self._get_combo_style())
        layout.addWidget(self.filtro_zona)

        # Filtro por turno
        label_turno_filtro = QLabel("🕐 Turno:")
        label_turno_filtro.setStyleSheet("""
            font-size: 12px;
            font-weight: bold;
            color: #333;
            padding: 4px 0px;
        """)
        layout.addWidget(label_turno_filtro)

        self.filtro_turno = QComboBox()
        self.filtro_turno.addItem("📋 Todos los turnos", "Todos")
        self.filtro_turno.addItem("☀️ Mañana (máx 8 guardias/día)", "mañana")
        self.filtro_turno.addItem("🌙 Tarde (máx 8 guardias/día)", "tarde")
        self.filtro_turno.currentIndexChanged.connect(self.filtros_cambiados.emit)
        self.filtro_turno.setStyleSheet("""
            QComboBox {
                padding: 6px;
                border: 2px solid #BDBDBD;
                border-radius: 4px;
                background-color: white;
                min-height: 25px;
                min-width: 240px;
            }
            QComboBox:hover {
                border: 2px solid #2196F3;
            }
            QComboBox:focus {
                border: 2px solid #1976D2;
            }
        """)
        layout.addWidget(self.filtro_turno)

        # Botón para limpiar filtros
        self.limpiar_filtros_btn = QPushButton("🗑️ Limpiar filtros")
        self.limpiar_filtros_btn.clicked.connect(self.limpiar)
        self.limpiar_filtros_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: 2px solid #F57C00;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
                padding: 8px;
                min-height: 30px;
            }
            QPushButton:hover {
                background-color: #F57C00;
                border: 2px solid #E65100;
            }
            QPushButton:pressed {
                background-color: #E65100;
            }
        """)
        layout.addWidget(self.limpiar_filtros_btn)

        # Cargar datos iniciales
        self.cargar_datos()

    def _get_combo_style(self) -> str:
        """Obtener estilo CSS para comboboxes."""
        return """
            QComboBox {
                padding: 6px;
                border: 2px solid #BDBDBD;
                border-radius: 4px;
                background-color: white;
                min-height: 25px;
            }
            QComboBox:hover {
                border: 2px solid #2196F3;
            }
            QComboBox:focus {
                border: 2px solid #1976D2;
            }
        """

    def cargar_datos(self):
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
            print(f"Error cargando filtros: {e}")

    def limpiar(self):
        """Limpiar todos los filtros."""
        self.filtro_profesor.setCurrentIndex(0)
        self.filtro_zona.setCurrentIndex(0)
        self.filtro_turno.setCurrentIndex(0)

    def get_datos(self) -> dict:
        """
        Obtener valores actuales de los filtros.

        Returns:
            dict: Diccionario con profesor_id, zona_id, turno
        """
        return {
            "profesor_id": self.filtro_profesor.currentData(),
            "zona_id": self.filtro_zona.currentData(),
            "turno": self.filtro_turno.currentData(),
        }


class DetallesDiaWidget(QWidget):
    """Widget para mostrar detalles de guardias de un día y estadísticas."""

    def __init__(self, session, parent=None):
        """
        Inicializar widget de detalles.

        Args:
            session: Sesión de base de datos
            parent: Widget padre
        """
        super().__init__(parent)
        self.session = session
        self._setup_ui()

    def _setup_ui(self):
        """Construir la interfaz del widget."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)

        # Detalles del día seleccionado
        detalles_label = QLabel("Guardias del día seleccionado:")
        detalles_label.setStyleSheet(styles.STYLE_LABEL_FIELD + " margin-top: 20px;")
        layout.addWidget(detalles_label)

        self.guardias_dia_text = QTextEdit()
        self.guardias_dia_text.setReadOnly(True)
        self.guardias_dia_text.setMaximumHeight(400)
        layout.addWidget(self.guardias_dia_text)

        # Estadísticas
        stats_label = QLabel("Estadísticas:")
        stats_label.setStyleSheet(styles.STYLE_LABEL_FIELD + " margin-top: 10px;")
        layout.addWidget(stats_label)

        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(150)
        layout.addWidget(self.stats_text)

    def actualizar_guardias_dia(self, fecha, filtros: dict):
        """
        Actualizar visualización de guardias para un día específico.

        Args:
            fecha: Fecha Python (date object)
            filtros: Diccionario con filtros (profesor_id, zona_id, turno)
        """
        try:
            # Construir query con filtros
            query = self.session.query(Guardia).filter(Guardia.fecha == fecha)

            if filtros.get("profesor_id") is not None:
                query = query.filter(Guardia.profesor_id == filtros["profesor_id"])

            if filtros.get("zona_id") is not None:
                query = query.filter(Guardia.zona_id == filtros["zona_id"])

            turno = filtros.get("turno")
            if turno and turno != "Todos":
                query = query.filter(Guardia.turno == turno)

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
                        prof_nombre = g.profesor.nombre_completo if g.profesor else "Sin profesor"
                        zona_nombre = g.zona.nombre_zona if g.zona else "Sin zona"
                        lineas.append(f"  • {prof_nombre} → {zona_nombre}")

                self.guardias_dia_text.setText("\n".join(lineas))

        except Exception as e:
            self.guardias_dia_text.setText(f"❌ Error: {e}")

    def actualizar_estadisticas(self, filtros: dict):
        """
        Actualizar estadísticas generales.

        Args:
            filtros: Diccionario con filtros (profesor_id, zona_id, turno)
        """
        try:
            # Construir query con filtros
            query = self.session.query(Guardia)

            if filtros.get("profesor_id") is not None:
                query = query.filter(Guardia.profesor_id == filtros["profesor_id"])

            if filtros.get("zona_id") is not None:
                query = query.filter(Guardia.zona_id == filtros["zona_id"])

            turno = filtros.get("turno")
            if turno and turno != "Todos":
                query = query.filter(Guardia.turno == turno)

            total_guardias = query.count()

            # Contar por turno
            guardias_manana = (
                query.filter(Guardia.turno == "mañana").count()
                if (not turno or turno == "Todos")
                else (total_guardias if turno == "mañana" else 0)
            )
            guardias_tarde = (
                query.filter(Guardia.turno == "tarde").count()
                if (not turno or turno == "Todos")
                else (total_guardias if turno == "tarde" else 0)
            )

            lineas = [
                f"📊 Total guardias: {total_guardias}",
                f"🌅 Mañana: {guardias_manana}",
                f"🌆 Tarde: {guardias_tarde}",
            ]

            # Si hay filtro de profesor, mostrar estadísticas personales
            profesor_id = filtros.get("profesor_id")
            if profesor_id is not None:
                profesor = self.session.query(Profesor).get(profesor_id)
                if profesor:
                    lineas.append(f"\n👤 {profesor.nombre_completo}")
                    lineas.append(f"   Turno: {profesor.turno}")
                    lineas.append(f"   Tutor: {'Sí' if profesor.tutor else 'No'}")

            self.stats_text.setText("\n".join(lineas))

        except Exception as e:
            self.stats_text.setText(f"❌ Error: {e}")
