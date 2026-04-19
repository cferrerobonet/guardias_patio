"""Widget para mostrar resultados de la generación de guardias.

Muestra el resumen de guardias generadas, cobertura y métricas de equidad.
Estilo terminal negro consistente con otros widgets.
"""

from presentation.theme import legacy_styles as styles
from presentation.theme.tokens import Spacing
from application.dtos.domain_services_dtos import AnalisisEquidadRequest
from application.use_cases.analisis_equidad_use_case import AnalisisEquidadUseCase
from infrastructure.database.models import Profesor
from PyQt6.QtWidgets import QGroupBox, QTextEdit, QVBoxLayout
from sqlalchemy.orm import Session
from presentation.theme.legacy_styles import (
    format_terminal_info,
    format_terminal_label,
    format_terminal_number,
    format_terminal_profesor,
    format_terminal_success,
    format_terminal_value,
    format_terminal_warning,
    wrap_terminal_html,
)


class ResultadosPanel(QGroupBox):
    """Panel para mostrar resultados de generación de guardias con equidad.

    Muestra:
    - Guardias generadas vs slots esperados
    - Estado de cobertura
    - Métricas de equidad integradas
    - Top profesores con más/menos guardias

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
        self.analisis_equidad_uc = AnalisisEquidadUseCase(session)
        self._ultimo_resumen = None

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
        self.resultado_text.setMinimumHeight(350)
        self.resultado_text.setStyleSheet(styles.STYLE_TERMINAL_RETRO)
        self.resultado_text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)

        layout.addWidget(self.resultado_text)
        self.setLayout(layout)

        # Mensaje inicial
        self._mostrar_mensaje_inicial()

    def _mostrar_mensaje_inicial(self):
        """Muestra mensaje inicial."""
        texto = format_terminal_info(
            "💡 Los resultados se mostrarán aquí después de\n"
            "   generar el calendario de guardias.\n\n"
            "   Pulsa 'Generar Asignación' para comenzar."
        )
        self.resultado_text.setHtml(wrap_terminal_html(texto))

    def mostrar_resultados(self, resumen):
        """Muestra los resultados de generación con métricas de equidad.

        Args:
            resumen: ResumenGeneracionDTO con atributos:
                - guardias_generadas (int)
                - slots_esperados (int)
                - cobertura_completa (bool)
                - slots_sin_cubrir (int)
                - resumen_por_profesor (dict): {profesor_id: count}
        """
        self._ultimo_resumen = resumen
        lineas = []

        # ======= SECCIÓN 1: COBERTURA =======
        lineas.append(format_terminal_success("📊 RESUMEN DE GENERACIÓN"))
        lineas.append(format_terminal_info("─" * 45))
        lineas.append("")

        # Métricas principales
        guardias_label = format_terminal_label("Guardias generadas:")
        guardias_num = format_terminal_number(str(resumen.guardias_generadas))
        lineas.append(f"{guardias_label} {guardias_num}")

        slots_label = format_terminal_label("Slots esperados:")
        slots_num = format_terminal_number(str(resumen.slots_esperados))
        lineas.append(f"{slots_label} {slots_num}")

        # Cobertura
        cobertura_pct = (
            resumen.guardias_generadas / resumen.slots_esperados * 100
            if resumen.slots_esperados > 0
            else 0
        )
        if resumen.cobertura_completa:
            cobertura_msg = f"✅ Cobertura: {cobertura_pct:.1f}% (completa)"
            lineas.append(format_terminal_success(cobertura_msg))
        elif resumen.slots_sin_cubrir > 0:
            warning_msg = (
                f"⚠️ Cobertura: {cobertura_pct:.1f}% "
                f"({resumen.slots_sin_cubrir} sin cubrir)"
            )
            lineas.append(format_terminal_warning(warning_msg))
        lineas.append("")

        # ======= SECCIÓN 2: EQUIDAD =======
        lineas.append(format_terminal_info("─" * 45))
        lineas.append(format_terminal_success("⚖️ ANÁLISIS DE EQUIDAD"))
        lineas.append("")

        # Obtener métricas de equidad
        try:
            request = AnalisisEquidadRequest(
                configuracion_id=None,
                incluir_detalle=True,
                umbral_desbalance=0.15,
            )
            response = self.analisis_equidad_uc.execute(request)

            if response.exitoso:
                metricas = response.metricas

                # Nivel de equidad con emoji
                nivel_emoji = {
                    "EXCELENTE": "🌟",
                    "BUENO": "✅",
                    "ACEPTABLE": "⚠️",
                    "DEFICIENTE": "❌",
                }
                emoji = nivel_emoji.get(metricas.nivel_equidad, "📊")

                is_good = metricas.nivel_equidad in ["EXCELENTE", "BUENO"]
                nivel_color = format_terminal_success if is_good else format_terminal_warning
                lineas.append(
                    f"{format_terminal_label('Nivel:')} "
                    f"{nivel_color(f'{emoji} {metricas.nivel_equidad}')}"
                )

                lineas.append(
                    f"{format_terminal_label('Índice de equidad:')} "
                    f"{format_terminal_value(f'{metricas.indice_equidad:.1%}')}"
                )

                lineas.append(
                    f"{format_terminal_label('Coef. variación:')} "
                    f"{format_terminal_number(f'{metricas.coeficiente_variacion:.3f}')}"
                )

                if metricas.desbalances_detectados > 0:
                    lineas.append(
                        format_terminal_warning(
                            f"⚠️ {metricas.desbalances_detectados} desbalances detectados"
                        )
                    )
                else:
                    lineas.append(format_terminal_success("✅ Sin desbalances significativos"))
            else:
                lineas.append(format_terminal_info("(análisis de equidad no disponible)"))
        except (ValueError, TypeError, OSError) as e:
            lineas.append(format_terminal_info("(análisis de equidad no disponible)"))

        lineas.append("")

        # ======= SECCIÓN 3: DISTRIBUCIÓN POR TURNO =======
        if resumen.resumen_por_profesor:
            lineas.append(format_terminal_info("─" * 45))
            lineas.append(format_terminal_label("👥 DISTRIBUCIÓN DE GUARDIAS ASIGNADAS:"))
            lineas.append("")

            # Obtener todos los profesores con sus turnos
            profesores_info = []
            for pid, cnt in resumen.resumen_por_profesor.items():
                from application.app_services import AppServices
                prof = AppServices(self.session).profesores.get_by_id(pid)
                if prof:
                    turno = str(prof.turno).lower().strip()
                    # Normalizar turno
                    if turno in ("mañana", "manana", "morning"):
                        turno_norm = "mañana"
                    elif turno in ("tarde", "afternoon"):
                        turno_norm = "tarde"
                    else:
                        turno_norm = "mixto"
                    profesores_info.append((prof.nombre_completo, cnt, turno_norm))

            # Separar por turno
            turno_manana = [(n, c) for n, c, t in profesores_info if t == "mañana"]
            turno_tarde = [(n, c) for n, c, t in profesores_info if t == "tarde"]
            turno_mixto = [(n, c) for n, c, t in profesores_info if t == "mixto"]

            # Ordenar cada grupo alfabéticamente
            turno_manana.sort(key=lambda x: x[0])
            turno_tarde.sort(key=lambda x: x[0])
            turno_mixto.sort(key=lambda x: x[0])

            # Mostrar TURNO MAÑANA
            if turno_manana:
                lineas.append(format_terminal_success("☀️ TURNO MAÑANA"))
                lineas.append("")
                for nombre, cnt in turno_manana:
                    prof_name = format_terminal_profesor(nombre)
                    cnt_num = format_terminal_number(str(cnt))
                    lineas.append(f"  • {prof_name}: {cnt_num} guardias")
                lineas.append("")

            # Mostrar TURNO TARDE
            if turno_tarde:
                lineas.append(format_terminal_success("🌙 TURNO TARDE"))
                lineas.append("")
                for nombre, cnt in turno_tarde:
                    prof_name = format_terminal_profesor(nombre)
                    cnt_num = format_terminal_number(str(cnt))
                    lineas.append(f"  • {prof_name}: {cnt_num} guardias")
                lineas.append("")

            # Mostrar TURNO MIXTO
            if turno_mixto:
                lineas.append(format_terminal_success("🔄 TURNO MIXTO"))
                lineas.append("")
                for nombre, cnt in turno_mixto:
                    prof_name = format_terminal_profesor(nombre)
                    cnt_num = format_terminal_number(str(cnt))
                    lineas.append(f"  • {prof_name}: {cnt_num} guardias")

        texto = "\n".join(lineas)
        self.resultado_text.setHtml(wrap_terminal_html(texto))

    def limpiar(self):
        """Limpia el contenido del panel."""
        self._mostrar_mensaje_inicial()
        self._ultimo_resumen = None
