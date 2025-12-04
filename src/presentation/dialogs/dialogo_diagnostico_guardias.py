"""
Diálogo para mostrar diagnóstico de problemas y permitir al usuario decidir
entre ajustar manualmente la configuración o continuar con el algoritmo ILP.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.services.diagnosticador_guardias import DiagnosticoCompleto, ProblemaDetectado


class DialogoDiagnosticoGuardias(QDialog):
    """
    Diálogo que muestra el diagnóstico detallado de problemas en la asignación
    y permite al usuario decidir cómo proceder.
    """

    ACCION_AJUSTAR_MANUAL = "ajustar"
    ACCION_CONTINUAR_ILP = "continuar_ilp"
    ACCION_CANCELAR = "cancelar"

    def __init__(self, diagnostico: DiagnosticoCompleto, parent=None):
        super().__init__(parent)
        self.diagnostico = diagnostico
        self.accion_elegida = self.ACCION_CANCELAR

        # Configurar atributos del diálogo ANTES de _init_ui
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)

        self._init_ui()

    def _init_ui(self):
        """Inicializa la interfaz del diálogo."""
        self.setWindowTitle("Diagnóstico de Asignación de Guardias")
        self.setMinimumSize(800, 600)

        layout = QVBoxLayout()

        # Título
        titulo = QLabel("⚠️ Se detectaron problemas en la asignación")
        titulo.setStyleSheet("font-size: 16pt; font-weight: bold; color: #e67e22;")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)

        # Subtítulo con estadísticas
        stats = self.diagnostico.estadisticas
        subtitulo = QLabel(
            f"Cobertura: {stats['cobertura_porcentaje']:.1f}% • "
            f"Profesores: {stats['profesores_con_guardias']}/"
            f"{stats['profesores_activos_totales']} • "
            f"Guardias: {stats['total_guardias_asignadas']}/"
            f"{stats['total_slots_esperados']}"
        )
        subtitulo.setStyleSheet("font-size: 11pt; color: #7f8c8d; margin: 5px;")
        subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitulo)

        # Área de scroll para los problemas
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        contenedor_problemas = QWidget()
        layout_problemas = QVBoxLayout(contenedor_problemas)

        # Mostrar problemas por gravedad
        self._agregar_seccion_problemas(
            layout_problemas,
            "🔴 PROBLEMAS CRÍTICOS",
            self.diagnostico.problemas_criticos,
            "#e74c3c",
        )

        self._agregar_seccion_problemas(
            layout_problemas,
            "🟠 PROBLEMAS IMPORTANTES",
            self.diagnostico.problemas_altos,
            "#e67e22",
        )

        self._agregar_seccion_problemas(
            layout_problemas, "🟡 PROBLEMAS MENORES", self.diagnostico.problemas_medios, "#f39c12"
        )

        layout_problemas.addStretch()
        scroll.setWidget(contenedor_problemas)
        layout.addWidget(scroll, 1)  # Toma espacio expandible

        # Mensaje de recomendación
        if self.diagnostico.puede_continuar_ilp:
            recomendacion = QLabel(
                "💡 Recomendación: Puede ajustar manualmente la configuración o "
                "continuar con el algoritmo ILP avanzado que garantiza la mejor solución posible."
            )
            recomendacion.setWordWrap(True)
            recomendacion.setStyleSheet(
                "background-color: #ecf0f1; padding: 10px; border-radius: 5px; "
                "color: #2c3e50; font-size: 10pt;"
            )
            layout.addWidget(recomendacion)

        # Botones de acción
        layout_botones = QHBoxLayout()

        btn_ajustar = QPushButton("📝 Ajustar Manualmente")
        btn_ajustar.setToolTip(
            "Volver a la configuración para modificar disponibilidades, zonas, recreos o días"
        )
        btn_ajustar.clicked.connect(self._on_ajustar_manual)
        btn_ajustar.setStyleSheet(
            "QPushButton { background-color: #3498db; color: white; "
            "padding: 10px 20px; font-size: 11pt; border-radius: 5px; }"
            "QPushButton:hover { background-color: #2980b9; }"
        )

        btn_continuar_ilp = QPushButton("🎯 Continuar con ILP Avanzado")
        btn_continuar_ilp.setToolTip(
            "Usar algoritmo de Programación Lineal Entera que garantiza "
            "la solución óptima matemáticamente (puede tardar más)"
        )
        btn_continuar_ilp.clicked.connect(self._on_continuar_ilp)
        btn_continuar_ilp.setStyleSheet(
            "QPushButton { background-color: #27ae60; color: white; "
            "padding: 10px 20px; font-size: 11pt; border-radius: 5px; }"
            "QPushButton:hover { background-color: #229954; }"
        )

        # Deshabilitar ILP si no es recomendado
        if not self.diagnostico.puede_continuar_ilp:
            btn_continuar_ilp.setEnabled(False)
            btn_continuar_ilp.setToolTip(
                "Los problemas detectados son menores. No es necesario usar el algoritmo ILP."
            )

        btn_cancelar = QPushButton("❌ Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        btn_cancelar.setStyleSheet(
            "QPushButton { background-color: #95a5a6; color: white; "
            "padding: 10px 20px; font-size: 11pt; border-radius: 5px; }"
            "QPushButton:hover { background-color: #7f8c8d; }"
        )

        layout_botones.addWidget(btn_ajustar)
        layout_botones.addWidget(btn_continuar_ilp)
        layout_botones.addStretch()
        layout_botones.addWidget(btn_cancelar)

        layout.addLayout(layout_botones)

        self.setLayout(layout)

    def _agregar_seccion_problemas(
        self, layout: QVBoxLayout, titulo: str, problemas: list[ProblemaDetectado], color: str
    ):
        """Agrega una sección de problemas al layout."""
        if not problemas:
            return

        # Grupo para esta categoría
        grupo = QGroupBox(titulo)
        grupo.setStyleSheet(
            f"QGroupBox {{ font-weight: bold; font-size: 11pt; "
            f"color: {color}; border: 2px solid {color}; "
            f"border-radius: 5px; margin-top: 10px; padding-top: 10px; }}"
            f"QGroupBox::title {{ subcontrol-origin: margin; left: 10px; }}"
        )

        layout_grupo = QVBoxLayout()

        for problema in problemas:
            # Descripción del problema
            lbl_descripcion = QLabel(f"• {problema.descripcion}")
            lbl_descripcion.setWordWrap(True)
            lbl_descripcion.setStyleSheet("font-size: 10pt; margin-left: 10px;")
            layout_grupo.addWidget(lbl_descripcion)

            # Sugerencias (si las hay)
            if problema.sugerencias:
                for sugerencia in problema.sugerencias[:3]:  # Máximo 3 sugerencias
                    lbl_sugerencia = QLabel(f"   💡 {sugerencia}")
                    lbl_sugerencia.setWordWrap(True)
                    lbl_sugerencia.setStyleSheet(
                        "font-size: 9pt; color: #7f8c8d; margin-left: 30px; "
                        "margin-top: 3px; font-style: italic;"
                    )
                    layout_grupo.addWidget(lbl_sugerencia)

            # Detalles adicionales (si son relevantes para el usuario)
            if "profesores" in problema.detalles:
                profesores = problema.detalles["profesores"]
                if len(profesores) <= 5:
                    # Mostrar nombres si son pocos
                    nombres = [p["nombre"] for p in profesores]
                    lbl_detalle = QLabel(f"   Afectados: {', '.join(nombres)}")
                    lbl_detalle.setStyleSheet("font-size: 9pt; color: #95a5a6; margin-left: 30px;")
                    layout_grupo.addWidget(lbl_detalle)

            # Espaciado entre problemas
            layout_grupo.addSpacing(5)

        grupo.setLayout(layout_grupo)
        layout.addWidget(grupo)

    def _on_ajustar_manual(self):
        """Usuario elige ajustar manualmente."""
        self.accion_elegida = self.ACCION_AJUSTAR_MANUAL
        self.accept()

    def _on_continuar_ilp(self):
        """Usuario elige continuar con ILP."""
        self.accion_elegida = self.ACCION_CONTINUAR_ILP
        self.accept()

    def get_accion_elegida(self) -> str:
        """Retorna la acción elegida por el usuario."""
        return self.accion_elegida
