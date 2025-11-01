"""Widget para mostrar análisis de incidencias y recomendaciones.

Analiza problemas en la generación y sugiere soluciones.
"""

import ui_styles as styles
from models.models import Profesor, Zona
from PyQt6.QtWidgets import QGroupBox, QTextEdit, QVBoxLayout
from sqlalchemy.orm import Session
from ui_styles import (
    format_terminal_error,
    format_terminal_info,
    format_terminal_label,
    format_terminal_number,
    format_terminal_success,
    format_terminal_warning,
    wrap_terminal_html,
)


class IncidenciasPanel(QGroupBox):
    """Panel para mostrar análisis de incidencias y recomendaciones.
    
    Analiza:
    - Estado de cobertura
    - Causas de slots sin cubrir
    - Distribución de carga
    - Ratio profesor/zona
    - Recomendaciones específicas
    
    Señales:
        No emite señales (solo visualización).
    """

    def __init__(self, session: Session, parent=None):
        """Inicializa el panel de incidencias.
        
        Args:
            session: Sesión de SQLAlchemy para consultas.
            parent: Widget padre opcional.
        """
        super().__init__("⚠️ Análisis de Incidencias y Recomendaciones", parent)
        self.session = session
        self._setup_ui()

    def _setup_ui(self):
        """Crea la interfaz del widget."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 8, 6, 8)
        layout.setSpacing(4)

        # Área de texto con estilo terminal
        self.incidencias_text = QTextEdit()
        self.incidencias_text.setReadOnly(True)
        self.incidencias_text.setMinimumHeight(320)
        self.incidencias_text.setStyleSheet(styles.STYLE_TERMINAL_RETRO)
        self.incidencias_text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.incidencias_text.setPlaceholderText(
            "Las incidencias y recomendaciones se mostrarán aquí después de generar guardias..."
        )

        layout.addWidget(self.incidencias_text)
        self.setLayout(layout)

    def analizar_incidencias(self, resumen):
        """Analiza incidencias y muestra recomendaciones.
        
        Args:
            resumen: ResumenGeneracionDTO con atributos:
                - cobertura_completa (bool)
                - slots_esperados (int)
                - slots_sin_cubrir (int)
                - guardias_generadas (int)
                - resumen_por_profesor (dict)
        """
        incidencias = []

        if resumen.cobertura_completa:
            # Sin incidencias
            incidencias.extend(self._formato_sin_incidencias(resumen))
        else:
            # Con incidencias
            incidencias.extend(self._formato_con_incidencias(resumen))

        self.incidencias_text.setHtml(wrap_terminal_html("\n".join(incidencias)))

    def _formato_sin_incidencias(self, resumen) -> list:
        """Formatea mensaje para generación exitosa."""
        incidencias = []
        incidencias.append(format_terminal_success("✅ SIN INCIDENCIAS"))
        incidencias.append("")
        incidencias.append(format_terminal_info("La generación se completó exitosamente:"))
        success_msg1 = f'Todos los {resumen.slots_esperados} slots fueron cubiertos'
        incidencias.append(f"• {format_terminal_success(success_msg1)}")
        incidencias.append(f"• {format_terminal_success('La distribución de guardias es óptima')}")
        incidencias.append("")
        incidencias.append(format_terminal_info("🎯 Recomendaciones:"))
        msg_calendario = 'Revisa el calendario generado en la sección "Calendario"'
        incidencias.append(f"• {format_terminal_info(msg_calendario)}")
        msg_exportar = 'Puedes exportar los resultados para compartir con el equipo'
        incidencias.append(f"• {format_terminal_info(msg_exportar)}")
        return incidencias

    def _formato_con_incidencias(self, resumen) -> list:
        """Formatea análisis de incidencias detectadas."""
        incidencias = []
        slots_sin_cubrir = resumen.slots_sin_cubrir
        porcentaje_sin_cubrir = (
            (slots_sin_cubrir / resumen.slots_esperados * 100)
            if resumen.slots_esperados > 0
            else 0
        )

        # Cabecera
        incidencias.append(format_terminal_error("⚠️ INCIDENCIAS DETECTADAS"))
        incidencias.append("")
        incidencias.append(format_terminal_label("📊 Resumen:"))
        warning_msg = (
            f'{slots_sin_cubrir} de {resumen.slots_esperados} '
            f'({porcentaje_sin_cubrir:.1f}%)'
        )
        slots_label = format_terminal_label('Slots sin cubrir:')
        warning_val = format_terminal_warning(warning_msg)
        incidencias.append(f"• {slots_label} {warning_val}")
        guardias_label = format_terminal_label('Guardias generadas:')
        guardias_num = format_terminal_number(resumen.guardias_generadas)
        incidencias.append(f"• {guardias_label} {guardias_num}")
        incidencias.append("")

        # Causas
        incidencias.append(format_terminal_warning("🔍 CAUSAS PRINCIPALES:"))
        incidencias.append("")

        # 1. Elegibilidad
        incidencias.extend(self._analizar_elegibilidad())

        # 2. Recursos
        incidencias.extend(self._analizar_recursos())

        # 3. Distribución
        if resumen.resumen_por_profesor:
            incidencias.extend(self._analizar_distribucion(resumen))

        # Recomendaciones
        incidencias.extend(self._generar_recomendaciones())

        return incidencias

    def _analizar_elegibilidad(self) -> list:
        """Analiza problemas de elegibilidad."""
        lineas = []
        lineas.append(format_terminal_label("1️⃣ FALTA DE ELEGIBILIDAD DE PROFESORES"))
        lineas.append("")
        lineas.append(
            format_terminal_info(
                "   Algunos slots no tienen profesores disponibles porque:"
            )
        )
        lineas.append(format_terminal_info("   • Restricciones de horario muy estrictas"))
        lineas.append(
            format_terminal_info("   • Fechas de inicio/fin de guardias limitadas")
        )
        lineas.append(
            format_terminal_info(
                "   • Turnos incompatibles (profesores de mañana no cubren tarde)"
            )
        )
        lineas.append(
            format_terminal_info(
                "   • Profesores con jornada reducida ya asignados al máximo"
            )
        )
        lineas.append("")
        return lineas

    def _analizar_recursos(self) -> list:
        """Analiza ratio de recursos profesor/zona."""
        lineas = []
        num_zonas = self.session.query(Zona).count()
        num_profesores = self.session.query(Profesor).count()

        lineas.append(format_terminal_label("2️⃣ ANÁLISIS DE RECURSOS"))
        lineas.append("")
        prof_label = format_terminal_label('Profesores activos:')
        prof_num = format_terminal_number(num_profesores)
        lineas.append(f"   • {prof_label} {prof_num}")
        zonas_label = format_terminal_label('Zonas configuradas:')
        zonas_num = format_terminal_number(num_zonas)
        lineas.append(f"   • {zonas_label} {zonas_num}")

        if num_zonas > 0:
            ratio = num_profesores / num_zonas
            ratio_label = format_terminal_label('Ratio profesor/zona:')
            ratio_num = format_terminal_number(f'{ratio:.2f}')
            lineas.append(f"   • {ratio_label} {ratio_num}")
        else:
            lineas.append(f"   • {format_terminal_warning('Ratio: N/A (no hay zonas)')}")

        if num_zonas > 0 and num_profesores / num_zonas < 3:
            lineas.append("")
            warning_msg = (
                "   ⚠️ El ratio profesor/zona es bajo. Recomendado: mínimo 3:1"
            )
            lineas.append(format_terminal_warning(warning_msg))
        lineas.append("")
        return lineas

    def _analizar_distribucion(self, resumen) -> list:
        """Analiza distribución de carga entre profesores."""
        lineas = []
        guardias_por_prof = list(resumen.resumen_por_profesor.values())
        if not guardias_por_prof:
            return lineas

        max_guardias = max(guardias_por_prof)
        min_guardias = min(guardias_por_prof)
        diferencia = max_guardias - min_guardias

        lineas.append(format_terminal_label("3️⃣ DISTRIBUCIÓN DE CARGA"))
        lineas.append("")
        max_label = format_terminal_label('Máximo de guardias asignadas:')
        max_num = format_terminal_number(max_guardias)
        lineas.append(f"   • {max_label} {max_num}")
        min_label = format_terminal_label('Mínimo de guardias asignadas:')
        min_num = format_terminal_number(min_guardias)
        lineas.append(f"   • {min_label} {min_num}")
        dif_label = format_terminal_label('Diferencia:')
        dif_num = format_terminal_number(diferencia)
        lineas.append(f"   • {dif_label} {dif_num}")

        if diferencia > 20:
            lineas.append("")
            lineas.append(
                format_terminal_warning("   ⚠️ Distribución muy desigual detectada")
            )
        lineas.append("")
        return lineas

    def _generar_recomendaciones(self) -> list:
        """Genera recomendaciones para solucionar incidencias."""
        lineas = []
        num_zonas = self.session.query(Zona).count()
        num_profesores = self.session.query(Profesor).count()

        lineas.append("")
        lineas.append(format_terminal_success("💡 SOLUCIONES RECOMENDADAS:"))
        lineas.append("")
        lineas.append(format_terminal_info("1. Revisar restricciones de profesores:"))
        lineas.append(
            format_terminal_info(
                "   • Ve a 'Profesores' y revisa las restricciones de horario"
            )
        )
        lineas.append(
            format_terminal_info("   • Considera flexibilizar los recreos permitidos")
        )
        lineas.append(format_terminal_info("   • Verifica fechas de inicio/fin de guardias"))
        lineas.append("")
        lineas.append(format_terminal_info("2. Ajustar recursos:"))
        if num_zonas > 0 and num_profesores / num_zonas < 3:
            lineas.append(format_terminal_info("   • Añadir más profesores al sistema"))
            lineas.append(format_terminal_info("   • O reducir el número de zonas a vigilar"))
        else:
            lineas.append(
                format_terminal_info("   • La cantidad de profesores parece adecuada")
            )
        lineas.append("")
        lineas.append(format_terminal_info("3. Verificar configuración:"))
        lineas.append(format_terminal_info("   • Revisa días lectivos en 'Configuración'"))
        lineas.append(format_terminal_info("   • Verifica número de recreos por turno"))
        lineas.append(
            format_terminal_info("   • Asegúrate de que las zonas estén bien configuradas")
        )
        lineas.append("")
        lineas.append(format_terminal_info("4. Alternativas:"))
        lineas.append(
            format_terminal_info(
                "   • Permite que profesores de mañana cubran tarde (o viceversa)"
            )
        )
        lineas.append(
            format_terminal_info("   • Aumenta las horas de contrato de algunos profesores")
        )
        lineas.append(format_terminal_info("   • Considera contratar profesores de apoyo"))
        return lineas

    def limpiar(self):
        """Limpia el contenido del panel."""
        self.incidencias_text.clear()
