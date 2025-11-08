"""Widget para mostrar la distribución de guardias por profesor.

Muestra el cálculo de distribución objetivo antes de generar guardias.
"""

import ui_styles as styles
from models.models import Profesor
from PyQt6.QtWidgets import QGroupBox, QTextEdit, QVBoxLayout
from sqlalchemy.orm import Session
from ui_styles import (
    format_terminal_error,
    format_terminal_info,
    format_terminal_label,
    format_terminal_number,
    format_terminal_profesor,
    format_terminal_success,
    format_terminal_warning,
    wrap_terminal_html,
)


class DistribucionPanel(QGroupBox):
    """Panel para mostrar la distribución objetivo de guardias.

    Muestra la distribución estimada de guardias por profesor basada
    en sus porcentajes de jornada y turnos.

    Señales:
        No emite señales (solo visualización).
    """

    def __init__(self, session: Session, parent=None):
        """Inicializa el panel de distribución.

        Args:
            session: Sesión de SQLAlchemy para consultas.
            parent: Widget padre opcional.
        """
        super().__init__("📋 Distribución por Profesor", parent)
        self.session = session
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 2px solid #10b981;
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
                color: #047857;
            }
        """)
        self._setup_ui()

    def _setup_ui(self):
        """Crea la interfaz del widget."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 8, 6, 8)
        layout.setSpacing(4)

        # Área de texto con estilo terminal
        self.distribucion_text = QTextEdit()
        self.distribucion_text.setReadOnly(True)
        self.distribucion_text.setMinimumHeight(280)
        self.distribucion_text.setStyleSheet(styles.STYLE_TERMINAL_RETRO)
        self.distribucion_text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)

        layout.addWidget(self.distribucion_text)
        self.setLayout(layout)

    def mostrar_distribucion(self, distribucion_dto):
        """Muestra la distribución de guardias.

        Args:
            distribucion_dto: DTO con la distribución calculada con atributos:
                - distribucion (dict): {profesor_id: num_guardias}
                - total_guardias (int): Total de guardias a asignar
                - slots_totales (int): Slots disponibles
                - es_exacta (bool): Si la distribución es exacta
                - diferencia (int): Diferencia entre guardias y slots
        """
        texto = f"{format_terminal_success('📊 Distribución OBJETIVO (estimada):')}\n\n"

        info_msg1 = "ℹ️  Esta distribución es el objetivo ideal basado en porcentajes."
        info_msg2 = "El algoritmo puede ajustar ligeramente para cubrir todos los slots."
        texto += f"{format_terminal_info(info_msg1)}\n"
        texto += f"{format_terminal_info(info_msg2)}\n\n"

        # Ordenar por número de guardias (descendente)
        profesores_ordenados = sorted(
            distribucion_dto.distribucion.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        for profesor_id, guardias in profesores_ordenados:
            profesor = self.session.query(Profesor).get(profesor_id)
            if profesor:
                porcentaje_jornada = f"{profesor.porcentaje_jornada * 100:.0f}%"
                info_prof = f"({profesor.turno}, {porcentaje_jornada})"
                texto += (
                    f"• {format_terminal_profesor(profesor.nombre_completo)} "
                    f"{format_terminal_info(info_prof)}: "
                    f"{format_terminal_number(f'{guardias} guardias')}\n"
                )

        total_msg = f"✅ TOTAL: {distribucion_dto.total_guardias} guardias"
        texto += f"\n{format_terminal_success(total_msg)}"

        slots_label = format_terminal_label("📌 Slots disponibles:")
        slots_num = format_terminal_number(distribucion_dto.slots_totales)
        texto += f"\n{slots_label} {slots_num}"

        if distribucion_dto.es_exacta:
            texto += f"\n\n{format_terminal_success('✅ La distribución es exacta')}"
        else:
            diferencia_abs = abs(distribucion_dto.diferencia)
            dif_msg = f"⚠️  Diferencia: {diferencia_abs}"
            texto += f"\n\n{format_terminal_warning(dif_msg)}"

        msg_resultados = '💡 Tras generar, verifica el reparto real en "Resultados"'
        texto += f"\n\n{format_terminal_info(msg_resultados)}"

        self.distribucion_text.setHtml(wrap_terminal_html(texto))

    def mostrar_error(self, mensaje: str):
        """Muestra un mensaje de error.

        Args:
            mensaje: Mensaje de error a mostrar.
        """
        error_msg = format_terminal_error(f"❌ Error: {mensaje}")
        self.distribucion_text.setHtml(wrap_terminal_html(error_msg))

    def limpiar(self):
        """Limpia el contenido del panel."""
        self.distribucion_text.clear()
