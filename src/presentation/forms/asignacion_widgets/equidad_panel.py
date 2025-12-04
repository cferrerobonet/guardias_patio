"""Widget para mostrar análisis de equidad de guardias usando Domain Services.

Integra AnalisisEquidadUseCase para mostrar métricas y recomendaciones.
"""

import ui_styles as styles
from application.dtos.domain_services_dtos import AnalisisEquidadRequest
from application.use_cases.analisis_equidad_use_case import AnalisisEquidadUseCase
from PyQt6.QtWidgets import QGroupBox, QPushButton, QTextEdit, QVBoxLayout
from sqlalchemy.orm import Session
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


class EquidadPanel(QGroupBox):
    """Panel para análisis de equidad usando Domain Services.

    Muestra:
    - Índice de equidad global
    - Nivel de equidad (EXCELENTE/BUENO/ACEPTABLE/DEFICIENTE)
    - Métricas estadísticas
    - Desbalances detectados
    - Recomendaciones automáticas
    - Top profesores con déficit/exceso

    Señales:
        No emite señales (solo visualización).
    """

    def __init__(self, session: Session, parent=None):
        """Inicializa el panel de equidad.

        Args:
            session: Sesión de SQLAlchemy para consultas.
            parent: Widget padre opcional.
        """
        super().__init__("⚖️ Análisis de Equidad (Domain Services)", parent)
        self.session = session
        self.analisis_uc = AnalisisEquidadUseCase(session)

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

        # Botón para analizar equidad
        self.analizar_button = QPushButton("🔍 Analizar Equidad")
        self.analizar_button.setStyleSheet(styles.STYLE_BUTTON_PRIMARY)
        self.analizar_button.setMinimumHeight(35)
        self.analizar_button.clicked.connect(self.analizar_equidad)
        layout.addWidget(self.analizar_button)

        # Área de texto con estilo terminal
        self.equidad_text = QTextEdit()
        self.equidad_text.setReadOnly(True)
        self.equidad_text.setMinimumHeight(320)
        self.equidad_text.setStyleSheet(styles.STYLE_TERMINAL_RETRO)
        self.equidad_text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)

        layout.addWidget(self.equidad_text)
        self.setLayout(layout)

        # Mostrar mensaje inicial
        self._mostrar_mensaje_inicial()

    def _mostrar_mensaje_inicial(self):
        """Muestra mensaje inicial antes del análisis."""
        texto = format_terminal_info(
            "💡 Presiona 'Analizar Equidad' después de generar guardias\n"
            "para ver métricas detalladas de distribución."
        )
        self.equidad_text.setHtml(wrap_terminal_html(texto))

    def analizar_equidad(self):
        """Ejecuta el análisis de equidad usando el Use Case."""
        try:
            # Deshabilitar botón durante análisis
            self.analizar_button.setEnabled(False)
            self.analizar_button.setText("⏳ Analizando...")

            # Ejecutar Use Case
            request = AnalisisEquidadRequest(
                configuracion_id=None,  # Analizar todas las guardias del curso
                incluir_detalle=True,
                umbral_desbalance=0.15,  # 15% de desviación
            )
            response = self.analisis_uc.execute(request)

            if response.exitoso:
                self._mostrar_analisis(response)
            else:
                self._mostrar_error(response.mensaje)

        except Exception as e:
            self._mostrar_error(f"Error en análisis: {str(e)}")
        finally:
            # Rehabilitar botón
            self.analizar_button.setEnabled(True)
            self.analizar_button.setText("🔍 Analizar Equidad")

    def _mostrar_analisis(self, response):
        """Muestra los resultados del análisis.

        Args:
            response: AnalisisEquidadResponse con métricas y recomendaciones.
        """
        metricas = response.metricas

        # Elegir emoji según nivel
        nivel_emoji = {"EXCELENTE": "🌟", "BUENO": "✅", "ACEPTABLE": "⚠️", "DEFICIENTE": "❌"}
        emoji = nivel_emoji.get(metricas.nivel_equidad, "📊")

        # Formatear métricas principales
        lineas = [
            format_terminal_success(f"{emoji} NIVEL DE EQUIDAD: {metricas.nivel_equidad}"),
            "",
            f"{format_terminal_label('Índice de Equidad:')} "
            f"{format_terminal_value(f'{metricas.indice_equidad:.2%}')}",
            f"{format_terminal_label('Coeficiente de Variación:')} "
            f"{format_terminal_number(f'{metricas.coeficiente_variacion:.3f}')}",
            f"{format_terminal_label('Desviación Estándar:')} "
            f"{format_terminal_number(f'{metricas.desviacion_estandar:.3f}')}",
            "",
        ]

        # Desbalances
        if metricas.desbalances_detectados > 0:
            lineas.append(
                format_terminal_warning(
                    f"⚠️  {metricas.desbalances_detectados} desbalances detectados"
                )
            )
        else:
            lineas.append(format_terminal_success("✅ Sin desbalances significativos"))

        # Profesores con problemas
        if metricas.profesores_con_deficit > 0:
            lineas.append(
                f"{format_terminal_label('Profesores con déficit:')} "
                f"{format_terminal_number(metricas.profesores_con_deficit)}"
            )

        if metricas.profesores_con_exceso > 0:
            lineas.append(
                f"{format_terminal_label('Profesores con exceso:')} "
                f"{format_terminal_number(metricas.profesores_con_exceso)}"
            )

        # Top profesores con mayor déficit/exceso
        if response.cuotas:
            lineas.append("")
            lineas.append(format_terminal_info("📋 Top 5 Profesores con Mayor Desbalance:"))

            # Ordenar por déficit absoluto descendente
            cuotas_ordenadas = sorted(response.cuotas, key=lambda c: abs(c.deficit), reverse=True)[
                :5
            ]

            for cuota in cuotas_ordenadas:
                if cuota.deficit != 0:
                    simbolo = "⬇️" if cuota.deficit > 0 else "⬆️"
                    tipo = "déficit" if cuota.deficit > 0 else "exceso"
                    deficit_str = abs(cuota.deficit)

                    lineas.append(
                        f"  {simbolo} {cuota.profesor_nombre}: "
                        f"{format_terminal_warning(f'{tipo} de {deficit_str}')}"
                        f" ({cuota.cuota_asignada}/{cuota.cuota_esperada})"
                    )

        # Recomendaciones
        if response.recomendaciones:
            lineas.append("")
            lineas.append(format_terminal_info("💡 Recomendaciones:"))
            for rec in response.recomendaciones:
                lineas.append(f"  • {rec}")

        texto = "\n".join(lineas)
        self.equidad_text.setHtml(wrap_terminal_html(texto))

    def _mostrar_error(self, mensaje: str):
        """Muestra un mensaje de error.

        Args:
            mensaje: Mensaje de error a mostrar.
        """
        error_html = wrap_terminal_html(format_terminal_error(f"⚠️  {mensaje}"))
        self.equidad_text.setHtml(error_html)

    def limpiar(self):
        """Limpia el contenido del panel."""
        self._mostrar_mensaje_inicial()

    def actualizar_despues_generacion(self):
        """Actualiza automáticamente después de generar guardias."""
        self.analizar_equidad()
