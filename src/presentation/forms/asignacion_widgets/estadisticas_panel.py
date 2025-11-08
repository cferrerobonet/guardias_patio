"""Widget para mostrar estadísticas del curso.

Muestra información sobre días lectivos, recreos, zonas y slots totales.
"""

import ui_styles as styles
from PyQt6.QtWidgets import QGroupBox, QTextEdit, QVBoxLayout
from ui_styles import (
    format_terminal_error,
    format_terminal_info,
    format_terminal_label,
    format_terminal_number,
    format_terminal_success,
    format_terminal_value,
    format_terminal_warning,
    wrap_terminal_html,
)


class EstadisticasPanel(QGroupBox):
    """Panel para mostrar estadísticas del curso.

    Muestra:
    - Días lectivos
    - Recreos (mañana/tarde)
    - Número de zonas
    - Número de profesores
    - Slots totales disponibles
    - Diferencia entre slots teóricos y reales

    Señales:
        No emite señales (solo visualización).
    """

    def __init__(self, parent=None):
        """Inicializa el panel de estadísticas."""
        super().__init__("📊 Estadísticas del Curso", parent)
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 2px solid #3b82f6;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 2px 8px;
                left: 10px;
                top: -7px;
                background-color: white;
                color: #1e40af;
            }
        """)
        self._setup_ui()

    def _setup_ui(self):
        """Crea la interfaz del widget."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 8, 6, 8)
        layout.setSpacing(4)

        # Área de texto con estilo terminal
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMinimumHeight(280)
        self.stats_text.setStyleSheet(styles.STYLE_TERMINAL_RETRO)
        self.stats_text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)

        layout.addWidget(self.stats_text)
        self.setLayout(layout)

    def mostrar_estadisticas(self, stats):
        """Muestra las estadísticas del curso.

        Args:
            stats: DTO con estadísticas del curso con atributos:
                - dias_lectivos (int)
                - recreos_manana (int)
                - recreos_tarde (int)
                - num_zonas (int)
                - num_profesores (int)
                - slots_totales (int)
        """
        # Calcular slots teóricos
        slots_teoricos = (
            stats.dias_lectivos * (stats.recreos_manana + stats.recreos_tarde) * stats.num_zonas
        )

        # Formatear texto
        dias_val = format_terminal_value(f"{stats.dias_lectivos} días (L-V)")
        total_recreos = stats.recreos_manana + stats.recreos_tarde

        texto = f"""
{format_terminal_label("Días lectivos:")} {dias_val}
{format_terminal_label("Recreos mañana:")} {format_terminal_number(stats.recreos_manana)}
{format_terminal_label("Recreos tarde:")} {format_terminal_number(stats.recreos_tarde)}
{format_terminal_label("Total recreos/día:")} {format_terminal_number(total_recreos)}
{format_terminal_label("Número de zonas:")} {format_terminal_number(stats.num_zonas)}
{format_terminal_label("Número de profesores:")} {format_terminal_number(stats.num_profesores)}

{format_terminal_success(f"📌 SLOTS TOTALES: {stats.slots_totales} guardias")}
"""

        # Añadir explicación si hay diferencia
        if stats.slots_totales < slots_teoricos:
            diferencia = slots_teoricos - stats.slots_totales
            porcentaje = (diferencia / slots_teoricos * 100) if slots_teoricos > 0 else 0
            info_sin_fechas = (
                f"(sin fechas: {stats.dias_lectivos} × {total_recreos} × {stats.num_zonas})"
            )
            reduccion_msg = f"{diferencia} slots ({porcentaje:.1f}%)"

            texto += f"""
   {format_terminal_label("• Slots teóricos:")} {format_terminal_number(slots_teoricos)}
     {format_terminal_info(info_sin_fechas)}
   {format_terminal_label("• Slots reales:")} {format_terminal_number(stats.slots_totales)}
   {format_terminal_label("• Reducción:")} {format_terminal_warning(reduccion_msg)}

   {format_terminal_info("ℹ️  Hay zonas con fechas de inicio/fin que reducen")}
   {format_terminal_info("el número total de slots disponibles.")}
"""
        else:
            formula = f"{stats.dias_lectivos} × {total_recreos} × {stats.num_zonas}"
            texto += f"""   {format_terminal_info(f"(días × recreos × zonas = {formula})")}
"""

        self.stats_text.setHtml(wrap_terminal_html(texto.strip()))

    def mostrar_error(self, mensaje: str):
        """Muestra un mensaje de error.

        Args:
            mensaje: Mensaje de error a mostrar.
        """
        error_html = wrap_terminal_html(format_terminal_error(f"⚠️  {mensaje}"))
        self.stats_text.setHtml(error_html)

    def limpiar(self):
        """Limpia el contenido del panel."""
        self.stats_text.clear()
