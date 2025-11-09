"""Widget para mostrar resultados de la generación de guardias.

Muestra el resumen de guardias generadas y cobertura.
"""

from PyQt6.QtWidgets import QGroupBox, QTextEdit, QVBoxLayout
from sqlalchemy.orm import Session

import ui_styles as styles
from models.models import Profesor
from ui_styles import (
    format_terminal_info,
    format_terminal_label,
    format_terminal_number,
    format_terminal_profesor,
    format_terminal_success,
    format_terminal_warning,
    wrap_terminal_html,
)


class ResultadosPanel(QGroupBox):
    """Panel para mostrar resultados de generación de guardias.

    Muestra:
    - Guardias generadas vs slots esperados
    - Estado de cobertura
    - Top 10 profesores con más guardias

    Señales:
        No emite señales (solo visualización).
    """

    def __init__(self, session: Session, parent=None):
        """Inicializa el panel de resultados.

        Args:
            session: Sesión de SQLAlchemy para consultas.
            parent: Widget padre opcional.
        """
        super().__init__("📈 Resultados de Generación", parent)
        self.session = session
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 2px solid #8b5cf6;
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
                color: #6d28d9;
            }
        """)
        self._setup_ui()

    def _setup_ui(self):
        """Crea la interfaz del widget."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 8, 6, 8)
        layout.setSpacing(4)

        # Área de texto con estilo terminal
        self.resultado_text = QTextEdit()
        self.resultado_text.setReadOnly(True)
        self.resultado_text.setMinimumHeight(320)
        self.resultado_text.setStyleSheet(styles.STYLE_TERMINAL_RETRO)
        self.resultado_text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)

        layout.addWidget(self.resultado_text)
        self.setLayout(layout)

    def mostrar_resultados(self, resumen):
        """Muestra los resultados de generación.

        Args:
            resumen: ResumenGeneracionDTO con atributos:
                - guardias_generadas (int)
                - slots_esperados (int)
                - cobertura_completa (bool)
                - slots_sin_cubrir (int)
                - resumen_por_profesor (dict): {profesor_id: count}
        """
        texto = self._formatear_resumen(resumen)
        self.resultado_text.setHtml(wrap_terminal_html(texto))

    def _formatear_resumen(self, resumen) -> str:
        """Formatea el resumen de generación.

        Args:
            resumen: ResumenGeneracionDTO con los resultados.

        Returns:
            Texto formateado (HTML con colores terminal).
        """
        guardias_label = format_terminal_label("Guardias generadas:")
        guardias_num = format_terminal_number(resumen.guardias_generadas)
        slots_label = format_terminal_label("Slots esperados:")
        slots_num = format_terminal_number(resumen.slots_esperados)

        lineas = [
            f"{guardias_label} {guardias_num}",
            f"{slots_label} {slots_num}",
        ]

        if resumen.cobertura_completa:
            lineas.append(format_terminal_success("✅ Cobertura completa"))
        elif resumen.slots_sin_cubrir > 0:
            warning_msg = f"⚠️ {resumen.slots_sin_cubrir} slots sin cubrir (falta elegibilidad)"
            lineas.append(format_terminal_warning(warning_msg))

        # Top profesores (máximo 10)
        if resumen.resumen_por_profesor:
            top = sorted(
                resumen.resumen_por_profesor.items(),
                key=lambda x: x[1],
                reverse=True,
            )[:10]
            lineas.append(f"\n{format_terminal_info('Por profesor (top 10):')}")
            for pid, cnt in top:
                prof = self.session.query(Profesor).get(pid)
                if prof:
                    prof_name = format_terminal_profesor(prof.nombre_completo)
                    cnt_num = format_terminal_number(cnt)
                    lineas.append(f"• {prof_name}: {cnt_num}")

        return "\n".join(lineas)

    def limpiar(self):
        """Limpia el contenido del panel."""
        self.resultado_text.clear()
