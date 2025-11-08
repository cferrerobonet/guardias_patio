"""
Diálogo para mostrar detalles completos de guardias de un día específico.

Muestra información detallada de todas las guardias, ausencias y sustituciones
del día seleccionado en el calendario.
"""

from datetime import date
from typing import List

from models.models import Ausencia, Guardia
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class DiaDetalleDialog(QDialog):
    """Ventana modal con detalles completos del día seleccionado."""

    def __init__(
        self,
        fecha: date,
        guardias: List[Guardia],
        ausencias: List[Ausencia],
        sustituciones: List[Guardia],
        parent=None,
    ):
        """
        Inicializar diálogo de detalle del día.

        Args:
            fecha: Fecha del día
            guardias: Lista de guardias del día
            ausencias: Lista de ausencias del día
            sustituciones: Lista de sustituciones del día
            parent: Widget padre
        """
        super().__init__(parent)
        self.fecha = fecha
        self.guardias = guardias
        self.ausencias = ausencias
        self.sustituciones = sustituciones

        self.setup_ui()

    def setup_ui(self):
        """Construir interfaz del diálogo."""
        self.setWindowTitle(f"Detalles del {self.fecha.strftime('%d/%m/%Y')}")
        self.setMinimumSize(600, 500)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Encabezado con fecha
        header_layout = QHBoxLayout()

        # Fecha en formato legible
        nombre_dia = self.fecha.strftime("%A").capitalize()
        fecha_formateada = self.fecha.strftime("%d de %B de %Y")

        label_fecha = QLabel(f"📅 {nombre_dia}, {fecha_formateada}")
        font_fecha = QFont()
        font_fecha.setPointSize(14)
        font_fecha.setBold(True)
        label_fecha.setFont(font_fecha)
        header_layout.addWidget(label_fecha)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Separador
        separador = QFrame()
        separador.setFrameShape(QFrame.Shape.HLine)
        separador.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separador)

        # Área de scroll con contenido
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        contenido_widget = QWidget()
        contenido_layout = QVBoxLayout(contenido_widget)
        contenido_layout.setSpacing(10)

        # Resumen estadístico
        stats_group = self._crear_resumen_estadistico()
        contenido_layout.addWidget(stats_group)

        # Sección de guardias
        if self.guardias:
            guardias_group = self._crear_seccion_guardias()
            contenido_layout.addWidget(guardias_group)
        else:
            label_sin_guardias = QLabel("ℹ️ No hay guardias asignadas para este día")
            label_sin_guardias.setStyleSheet(
                "padding: 20px; background-color: #f0f0f0; "
                "border-radius: 5px; color: #666;"
            )
            contenido_layout.addWidget(label_sin_guardias)

        # Sección de ausencias
        if self.ausencias:
            ausencias_group = self._crear_seccion_ausencias()
            contenido_layout.addWidget(ausencias_group)

        # Sección de sustituciones
        if self.sustituciones:
            sustituciones_group = self._crear_seccion_sustituciones()
            contenido_layout.addWidget(sustituciones_group)

        contenido_layout.addStretch()

        scroll_area.setWidget(contenido_widget)
        layout.addWidget(scroll_area)

        # Botón cerrar
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setMinimumHeight(35)
        btn_cerrar.clicked.connect(self.accept)
        layout.addWidget(btn_cerrar)

        self.setLayout(layout)

    def _crear_resumen_estadistico(self) -> QGroupBox:
        """Crear widget con resumen estadístico del día."""
        group = QGroupBox("📊 Resumen")
        layout = QHBoxLayout()
        layout.setSpacing(20)

        # Contadores
        total_guardias = len(self.guardias)
        total_ausencias = len(self.ausencias)
        total_sustituciones = len(self.sustituciones)

        # Recreos únicos
        recreos_unicos = set()
        for guardia in self.guardias:
            recreos_unicos.add(guardia.recreo)

        # Zonas únicas
        zonas_unicas = set()
        for guardia in self.guardias:
            if guardia.zona:
                zonas_unicas.add(guardia.zona.nombre_zona)

        # Labels con estadísticas
        stats = [
            ("Guardias", total_guardias, "🛡️"),
            ("Recreos", len(recreos_unicos), "⏰"),
            ("Zonas", len(zonas_unicas), "📍"),
            ("Ausencias", total_ausencias, "🏥"),
            ("Sustituciones", total_sustituciones, "🔄"),
        ]

        for nombre, valor, icono in stats:
            stat_widget = QWidget()
            stat_layout = QVBoxLayout(stat_widget)
            stat_layout.setSpacing(2)
            stat_layout.setContentsMargins(10, 5, 10, 5)

            label_valor = QLabel(f"{icono} {valor}")
            font_valor = QFont()
            font_valor.setPointSize(16)
            font_valor.setBold(True)
            label_valor.setFont(font_valor)
            label_valor.setAlignment(Qt.AlignmentFlag.AlignCenter)

            label_nombre = QLabel(nombre)
            label_nombre.setStyleSheet("color: #666; font-size: 10px;")
            label_nombre.setAlignment(Qt.AlignmentFlag.AlignCenter)

            stat_layout.addWidget(label_valor)
            stat_layout.addWidget(label_nombre)

            # Estilo según el valor
            color = "#4CAF50" if valor > 0 else "#ccc"
            stat_widget.setStyleSheet(
                f"background-color: {color}15; border-radius: 5px; "
                f"border: 1px solid {color};"
            )

            layout.addWidget(stat_widget)

        layout.addStretch()
        group.setLayout(layout)
        return group

    def _crear_seccion_guardias(self) -> QGroupBox:
        """Crear sección con lista de guardias."""
        group = QGroupBox(f"🛡️ Guardias ({len(self.guardias)})")
        layout = QVBoxLayout()
        layout.setSpacing(5)

        # Agrupar por recreo
        guardias_por_recreo = {}
        for guardia in sorted(self.guardias, key=lambda g: g.recreo):
            if guardia.recreo not in guardias_por_recreo:
                guardias_por_recreo[guardia.recreo] = []
            guardias_por_recreo[guardia.recreo].append(guardia)

        # Crear widget por cada recreo
        for recreo, guardias_recreo in guardias_por_recreo.items():
            recreo_widget = self._crear_widget_recreo(recreo, guardias_recreo)
            layout.addWidget(recreo_widget)

        group.setLayout(layout)
        return group

    def _crear_widget_recreo(self, numero_recreo: int, guardias: List[Guardia]) -> QWidget:
        """Crear widget para un recreo específico."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header del recreo
        header = QLabel(f"⏰ Recreo {numero_recreo} ({len(guardias)} profesores)")
        font_header = QFont()
        font_header.setBold(True)
        header.setFont(font_header)
        header.setStyleSheet(
            "background-color: #e3f2fd; padding: 8px; "
            "border-radius: 4px; color: #1565C0;"
        )
        layout.addWidget(header)

        # Ordenar guardias por zona (Z1, Z2, Z3, Z4)
        guardias_ordenadas = sorted(
            guardias,
            key=lambda g: (
                int(g.zona.nombre_zona[1]) if g.zona and g.zona.nombre_zona.startswith('Z') else 999
            )
        )

        # Lista de guardias ordenadas por zona
        for guardia in guardias_ordenadas:
            guardia_widget = self._crear_widget_guardia(guardia)
            layout.addWidget(guardia_widget)

        return widget

    def _crear_widget_guardia(self, guardia: Guardia) -> QWidget:
        """Crear widget para una guardia individual con mejor diseño."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(15)

        # Zona con badge distintivo
        if guardia.zona:
            zona_label = QLabel(f"{guardia.zona.nombre_zona}")
            zona_label.setStyleSheet("""
                background-color: #1976D2;
                color: white;
                font-weight: bold;
                font-size: 11px;
                padding: 4px 10px;
                border-radius: 3px;
                min-width: 35px;
            """)
            zona_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(zona_label)

        # Nombre del profesor con mejor tipografía
        nombre = guardia.profesor.nombre_completo
        if guardia.profesor.tutor:
            nombre += " 👨‍🏫"  # Icono de tutor más discreto

        label_profesor = QLabel(nombre)
        font_profesor = QFont()
        font_profesor.setPointSize(10)
        label_profesor.setFont(font_profesor)
        label_profesor.setStyleSheet("color: #333; padding-left: 8px;")
        layout.addWidget(label_profesor, 1)  # Stretch factor para que ocupe espacio

        # Turno del profesor con icono más sutil
        turno_icons = {"Mañana": "☀", "Tarde": "🌙", "Ambos": "⏰"}
        icon_turno = turno_icons.get(guardia.profesor.turno, "")
        label_turno = QLabel(f"{icon_turno} {guardia.profesor.turno}")
        label_turno.setStyleSheet(
            "color: #666; font-size: 9px; "
            "background-color: #f5f5f5; padding: 3px 8px; border-radius: 3px;"
        )
        layout.addWidget(label_turno)

        widget.setStyleSheet("""
            QWidget {
                background-color: white;
                border-left: 4px solid #4CAF50;
                border-radius: 4px;
                margin: 2px 0px;
            }
            QWidget:hover {
                background-color: #f8f9fa;
            }
        """)

        return widget

    def _crear_seccion_ausencias(self) -> QGroupBox:
        """Crear sección con lista de ausencias."""
        group = QGroupBox(f"🏥 Ausencias ({len(self.ausencias)})")
        layout = QVBoxLayout()
        layout.setSpacing(5)

        for ausencia in self.ausencias:
            ausencia_widget = self._crear_widget_ausencia(ausencia)
            layout.addWidget(ausencia_widget)

        group.setLayout(layout)
        return group

    def _crear_widget_ausencia(self, ausencia: Ausencia) -> QWidget:
        """Crear widget para una ausencia individual."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(3)
        layout.setContentsMargins(10, 8, 10, 8)

        # Primera línea: Profesor y fechas
        linea1 = QHBoxLayout()
        label_profesor = QLabel(f"👤 {ausencia.profesor.nombre_completo}")
        font_prof = QFont()
        font_prof.setBold(True)
        label_profesor.setFont(font_prof)
        linea1.addWidget(label_profesor)

        # Fechas de ausencia
        fecha_inicio = ausencia.fecha_inicio.strftime("%d/%m/%Y")
        fecha_fin = ausencia.fecha_fin.strftime("%d/%m/%Y")
        label_fechas = QLabel(f"📅 {fecha_inicio} - {fecha_fin}")
        label_fechas.setStyleSheet("color: #666; font-size: 9px;")
        linea1.addWidget(label_fechas)
        linea1.addStretch()

        layout.addLayout(linea1)

        # Segunda línea: Motivo (si existe)
        if ausencia.motivo:
            label_motivo = QLabel(f"💬 {ausencia.motivo}")
            label_motivo.setStyleSheet("color: #555; font-size: 10px; font-style: italic;")
            label_motivo.setWordWrap(True)
            layout.addWidget(label_motivo)

        widget.setStyleSheet(
            "background-color: #fff3e0; border-left: 3px solid #FF9800; "
            "border-radius: 3px;"
        )

        return widget

    def _crear_seccion_sustituciones(self) -> QGroupBox:
        """Crear sección con lista de sustituciones."""
        group = QGroupBox(f"🔄 Sustituciones ({len(self.sustituciones)})")
        layout = QVBoxLayout()
        layout.setSpacing(5)

        for sustitucion in self.sustituciones:
            sust_widget = self._crear_widget_sustitucion(sustitucion)
            layout.addWidget(sust_widget)

        group.setLayout(layout)
        return group

    def _crear_widget_sustitucion(self, guardia: Guardia) -> QWidget:
        """Crear widget para una sustitución individual."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)

        # Sustituto
        label_sustituto = QLabel(f"🔄 {guardia.profesor.nombre_completo} (Sustituto)")
        font_sust = QFont()
        font_sust.setBold(True)
        label_sustituto.setFont(font_sust)
        layout.addWidget(label_sustituto)

        # Zona
        if guardia.zona:
            label_zona = QLabel(f"📍 {guardia.zona.nombre_zona}")
            label_zona.setStyleSheet("color: #1976D2; font-size: 9px;")
            layout.addWidget(label_zona)

        # Recreo
        label_recreo = QLabel(f"⏰ Recreo {guardia.recreo}")
        label_recreo.setStyleSheet("color: #666; font-size: 9px;")
        layout.addWidget(label_recreo)

        layout.addStretch()

        widget.setStyleSheet(
            "background-color: #e8f5e9; border-left: 3px solid #4CAF50; "
            "border-radius: 3px; padding: 2px;"
        )

        return widget
