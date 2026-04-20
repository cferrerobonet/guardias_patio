"""
Widget para configurar y generar informes estadísticos.

Genera reportes detallados con estadísticas y gráficos sobre:
- Guardias del mes
- Distribución de carga
- Ausencias del periodo
- Cobertura mensual
- Resumen completo
"""

from datetime import datetime

from presentation.theme import legacy_styles as styles
from presentation.theme.tokens import Spacing
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)
from sqlalchemy.orm import Session
from utils.icons import icon_for_button

from presentation.themes.ccleaner_theme import TEXT_SECONDARY


class InformesEstadisticosWidget(QGroupBox):
    """Widget para generar informes estadísticos."""

    def __init__(self, session: Session, parent=None):
        """
        Inicializar el widget de informes estadísticos.

        Args:
            session: Sesión de base de datos
            parent: Widget padre
        """
        super().__init__("INFORMES ESTADÍSTICOS", parent)
        self.session = session

        self._setup_ui()

    def _setup_ui(self):
        """Construir la interfaz del widget."""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(15, 20, 15, 15)

        # Descripción
        desc = QLabel(
            "Genere reportes detallados con estadísticas y gráficos "
            "sobre guardias, carga de trabajo, ausencias y cobertura."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(
            f"""
            color: {TEXT_SECONDARY};
            font-size: 11px;
            font-weight: normal;
        """
        )
        layout.addWidget(desc)

        # Grupo: Configuración del Reporte
        config_layout = QFormLayout()
        config_layout.setSpacing(Spacing.MD)

        # Tipo de reporte
        self.tipo_combo = QComboBox()
        self.tipo_combo.addItem("Guardias del Mes", "guardias_mes")
        self.tipo_combo.addItem("Distribución de Carga", "distribucion_carga")
        self.tipo_combo.addItem("Ausencias del Periodo", "ausencias")
        self.tipo_combo.addItem("Cobertura Mensual", "cobertura")
        self.tipo_combo.addItem("Resumen Completo", "resumen_completo")
        config_layout.addRow("Tipo de Reporte:", self.tipo_combo)

        # Periodo: Desde
        self.fecha_desde = QDateEdit()
        self.fecha_desde.setCalendarPopup(True)
        self.fecha_desde.setDate(datetime.now().date().replace(day=1))
        self.fecha_desde.setDisplayFormat("dd/MM/yyyy")
        config_layout.addRow("Desde:", self.fecha_desde)

        # Periodo: Hasta
        self.fecha_hasta = QDateEdit()
        self.fecha_hasta.setCalendarPopup(True)
        self.fecha_hasta.setDate(datetime.now().date())
        self.fecha_hasta.setDisplayFormat("dd/MM/yyyy")
        config_layout.addRow("Hasta:", self.fecha_hasta)

        # Formato de salida
        self.formato_combo = QComboBox()
        self.formato_combo.addItem("PDF", "pdf")
        self.formato_combo.addItem("Excel (próximamente)", "excel")
        self.formato_combo.setCurrentIndex(0)
        # Deshabilitar Excel temporalmente
        self.formato_combo.model().item(1).setEnabled(False)
        config_layout.addRow("Formato:", self.formato_combo)

        layout.addLayout(config_layout)

        # Botones de acción
        botones_layout = QHBoxLayout()
        botones_layout.addStretch()

        btn_vista_previa = QPushButton("Vista Previa")
        btn_vista_previa.setIcon(icon_for_button("view"))
        btn_vista_previa.setObjectName("secondaryButton")
        btn_vista_previa.clicked.connect(self._vista_previa)
        botones_layout.addWidget(btn_vista_previa)

        btn_generar = QPushButton("Generar Reporte")
        btn_generar.setIcon(icon_for_button("chart"))
        btn_generar.setMinimumHeight(40)
        btn_generar.setProperty("success", "true")
        btn_generar.clicked.connect(self._generar_reporte)
        botones_layout.addWidget(btn_generar)

        layout.addLayout(botones_layout)

        # Panel de descripción del reporte seleccionado
        self.desc_reporte = QLabel()
        self.desc_reporte.setWordWrap(True)
        self.desc_reporte.setStyleSheet(
            """
            QLabel {
                background-color: #ecf0f1;
                border-radius: 6px;
                padding: 16px;
                font-size: 13px;
                color: #2c3e50;
            }
        """
        )
        layout.addWidget(self.desc_reporte)

        # Conectar señal para actualizar descripción
        self.tipo_combo.currentIndexChanged.connect(self._actualizar_descripcion)
        self._actualizar_descripcion()

        self.setLayout(layout)

    def _actualizar_descripcion(self) -> None:
        """Actualiza la descripción según el tipo de reporte seleccionado."""
        descripciones = {
            "guardias_mes": (
                "📅 <b>Guardias del Mes</b><br><br>"
                "Muestra todas las guardias asignadas en el periodo "
                "seleccionado, organizadas por fecha y profesor. "
                "Incluye gráficos de distribución por zona y turno."
            ),
            "distribucion_carga": (
                "⚖️ <b>Distribución de Carga</b><br><br>"
                "Analiza el reparto de guardias entre profesores. "
                "Identifica desequilibrios, sobrecarga o infracarga. "
                "Incluye gráfico comparativo y estadísticas."
            ),
            "ausencias": (
                "🏥 <b>Ausencias del Periodo</b><br><br>"
                "Lista todas las ausencias registradas en el periodo, "
                "con datos del profesor, motivo y fechas. "
                "Incluye estadísticas de impacto en la cobertura."
            ),
            "cobertura": (
                "📈 <b>Cobertura Mensual</b><br><br>"
                "Analiza el porcentaje de guardias cubiertas vs. "
                "slots disponibles. Muestra evolución diaria y "
                "detecta días con baja cobertura."
            ),
            "resumen_completo": (
                "📊 <b>Resumen Completo</b><br><br>"
                "Reporte integral que combina todas las métricas: "
                "guardias, distribución, ausencias y cobertura. "
                "Ideal para informes mensuales o trimestrales."
            ),
        }

        tipo = self.tipo_combo.currentData()
        texto = descripciones.get(tipo, "Seleccione un tipo de reporte para ver su descripción.")
        self.desc_reporte.setText(texto)

    def _vista_previa(self) -> None:
        """Muestra vista previa del reporte (placeholder)."""
        QMessageBox.information(
            self,
            "Vista Previa",
            "La vista previa estará disponible en una próxima actualización.\n\n"
            "Por ahora, puede generar el reporte directamente en PDF.",
        )

    def _generar_reporte(self) -> None:
        """Genera el reporte según la configuración."""
        # tipo = self.tipo_combo.currentData()
        formato = self.formato_combo.currentData()
        fecha_desde = self.fecha_desde.date().toPyDate()
        fecha_hasta = self.fecha_hasta.date().toPyDate()

        # Validar fechas
        if fecha_desde > fecha_hasta:
            QMessageBox.warning(
                self,
                "Fechas Inválidas",
                "La fecha 'Desde' no puede ser posterior a la fecha 'Hasta'.",
            )
            return

        # Validar formato
        if formato != "pdf":
            QMessageBox.information(
                self,
                "Formato No Disponible",
                "Por ahora solo está disponible el formato PDF.\n\n"
                "El formato Excel estará disponible próximamente.",
            )
            return

        # Seleccionar carpeta de destino
        from PyQt6.QtWidgets import QFileDialog

        carpeta = QFileDialog.getExistingDirectory(
            self, "Seleccionar Carpeta de Destino", "", QFileDialog.Option.ShowDirsOnly
        )

        if not carpeta:
            return

        # Por ahora, todos los reportes son placeholder
        QMessageBox.information(
            self,
            "Próximamente",
            f"Los informes estadísticos estarán disponibles en una próxima versión.\n\n"
            f"Reporte seleccionado: {self.tipo_combo.currentText()}\n"
            f"Periodo: {fecha_desde.strftime('%d/%m/%Y')} - {fecha_hasta.strftime('%d/%m/%Y')}\n"
            f"Formato: {formato.upper()}\n\n"
            "Mientras tanto, puede usar la funcionalidad de Calendarios PDF.",
        )
