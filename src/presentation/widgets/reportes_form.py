"""
Generador de Reportes e Informes.

Crea reportes detallados en PDF con estadísticas y gráficos.
"""

from datetime import datetime
from typing import Optional

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
    QWidget,
)
from sqlalchemy.orm import Session

from database.db_manager import SessionLocal


class ReportesForm(QWidget):
    """Formulario para generar reportes e informes."""

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Inicializa formulario de reportes.

        Args:
            parent: Widget padre
        """
        super().__init__(parent)
        self.session: Optional[Session] = None
        self._init_ui()

    def _init_ui(self) -> None:
        """Inicializa interfaz de usuario."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Título
        titulo = QLabel("📊 Generador de Reportes e Informes")
        titulo.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: #2c3e50;"
        )
        layout.addWidget(titulo)

        # Descripción
        desc = QLabel(
            "Genere reportes detallados con estadísticas y gráficos "
            "sobre guardias, carga de trabajo, ausencias y cobertura."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 13px; color: #7f8c8d; margin-bottom: 10px;")
        layout.addWidget(desc)

        # Grupo: Configuración del Reporte
        config_group = QGroupBox("⚙️ Configuración del Reporte")
        config_group.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """
        )
        config_layout = QFormLayout()
        config_layout.setSpacing(12)

        # Tipo de reporte
        self.tipo_combo = QComboBox()
        self.tipo_combo.addItem(
            "📅 Guardias del Mes",
            "guardias_mes"
        )
        self.tipo_combo.addItem(
            "⚖️ Distribución de Carga",
            "distribucion_carga"
        )
        self.tipo_combo.addItem(
            "🏥 Ausencias del Periodo",
            "ausencias"
        )
        self.tipo_combo.addItem(
            "📈 Cobertura Mensual",
            "cobertura"
        )
        self.tipo_combo.addItem(
            "📊 Resumen Completo",
            "resumen_completo"
        )
        config_layout.addRow("Tipo de Reporte:", self.tipo_combo)

        # Periodo: Desde
        self.fecha_desde = QDateEdit()
        self.fecha_desde.setCalendarPopup(True)
        self.fecha_desde.setDate(
            datetime.now().date().replace(day=1)
        )
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
        self.formato_combo.addItem("📄 PDF", "pdf")
        self.formato_combo.addItem("📊 Excel (próximamente)", "excel")
        self.formato_combo.setCurrentIndex(0)
        # Deshabilitar Excel temporalmente
        self.formato_combo.model().item(1).setEnabled(False)
        config_layout.addRow("Formato:", self.formato_combo)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # Botones de acción
        botones_layout = QHBoxLayout()
        botones_layout.addStretch()

        btn_vista_previa = QPushButton("👁️ Vista Previa")
        btn_vista_previa.setStyleSheet(
            """
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
            QPushButton:pressed {
                background-color: #6c7a89;
            }
        """
        )
        btn_vista_previa.clicked.connect(self._vista_previa)
        botones_layout.addWidget(btn_vista_previa)

        btn_generar = QPushButton("📊 Generar Reporte")
        btn_generar.setStyleSheet(
            """
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """
        )
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
        self.tipo_combo.currentIndexChanged.connect(
            self._actualizar_descripcion
        )
        self._actualizar_descripcion()

        layout.addStretch()

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
        texto = descripciones.get(
            tipo,
            "Seleccione un tipo de reporte para ver su descripción."
        )
        self.desc_reporte.setText(texto)

    def _vista_previa(self) -> None:
        """Muestra vista previa del reporte (placeholder)."""
        QMessageBox.information(
            self,
            "Vista Previa",
            "La vista previa estará disponible en una próxima actualización.\n\n"
            "Por ahora, puede generar el reporte directamente en PDF."
        )

    def _generar_reporte(self) -> None:
        """Genera el reporte según la configuración."""
        tipo = self.tipo_combo.currentData()
        formato = self.formato_combo.currentData()
        fecha_desde = self.fecha_desde.date().toPyDate()
        fecha_hasta = self.fecha_hasta.date().toPyDate()

        # Validar fechas
        if fecha_desde > fecha_hasta:
            QMessageBox.warning(
                self,
                "Fechas Inválidas",
                "La fecha 'Desde' no puede ser posterior a la fecha 'Hasta'."
            )
            return

        # Validar formato
        if formato != "pdf":
            QMessageBox.information(
                self,
                "Formato No Disponible",
                "Por ahora solo está disponible el formato PDF.\n\n"
                "El formato Excel estará disponible próximamente."
            )
            return

        # Seleccionar carpeta de destino
        from PyQt6.QtWidgets import QFileDialog

        carpeta = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar Carpeta de Destino",
            "",
            QFileDialog.Option.ShowDirsOnly
        )

        if not carpeta:
            return

        try:
            self.session = SessionLocal()

            # Generar según tipo
            if tipo == "guardias_mes":
                exito = self._generar_guardias_mes(
                    fecha_desde,
                    fecha_hasta,
                    carpeta
                )
            elif tipo == "distribucion_carga":
                exito = self._generar_distribucion_carga(
                    fecha_desde,
                    fecha_hasta,
                    carpeta
                )
            elif tipo == "ausencias":
                exito = self._generar_ausencias(
                    fecha_desde,
                    fecha_hasta,
                    carpeta
                )
            elif tipo == "cobertura":
                exito = self._generar_cobertura(
                    fecha_desde,
                    fecha_hasta,
                    carpeta
                )
            elif tipo == "resumen_completo":
                exito = self._generar_resumen_completo(
                    fecha_desde,
                    fecha_hasta,
                    carpeta
                )
            else:
                exito = False

            if exito:
                QMessageBox.information(
                    self,
                    "Reporte Generado",
                    f"El reporte se ha generado exitosamente en:\n{carpeta}"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "Ocurrió un error al generar el reporte."
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Error generando reporte:\n{str(e)}"
            )
        finally:
            if self.session:
                self.session.close()

    def _generar_guardias_mes(
        self,
        fecha_desde: datetime,
        fecha_hasta: datetime,
        carpeta: str
    ) -> bool:
        """
        Genera reporte de guardias del mes.

        Args:
            fecha_desde: Fecha inicio
            fecha_hasta: Fecha fin
            carpeta: Carpeta destino

        Returns:
            True si fue exitoso
        """
        # Placeholder - implementación futura con reportlab + matplotlib
        QMessageBox.information(
            self,
            "Próximamente",
            "Este tipo de reporte estará disponible en una próxima versión.\n\n"
            "Incluirá:\n"
            "• Listado completo de guardias\n"
            "• Gráfico de distribución por zona\n"
            "• Gráfico de distribución por turno\n"
            "• Estadísticas detalladas"
        )
        return False

    def _generar_distribucion_carga(
        self,
        fecha_desde: datetime,
        fecha_hasta: datetime,
        carpeta: str
    ) -> bool:
        """Genera reporte de distribución de carga (placeholder)."""
        QMessageBox.information(
            self,
            "Próximamente",
            "Este reporte estará disponible en una próxima versión."
        )
        return False

    def _generar_ausencias(
        self,
        fecha_desde: datetime,
        fecha_hasta: datetime,
        carpeta: str
    ) -> bool:
        """Genera reporte de ausencias (placeholder)."""
        QMessageBox.information(
            self,
            "Próximamente",
            "Este reporte estará disponible en una próxima versión."
        )
        return False

    def _generar_cobertura(
        self,
        fecha_desde: datetime,
        fecha_hasta: datetime,
        carpeta: str
    ) -> bool:
        """Genera reporte de cobertura (placeholder)."""
        QMessageBox.information(
            self,
            "Próximamente",
            "Este reporte estará disponible en una próxima versión."
        )
        return False

    def _generar_resumen_completo(
        self,
        fecha_desde: datetime,
        fecha_hasta: datetime,
        carpeta: str
    ) -> bool:
        """Genera reporte resumen completo (placeholder)."""
        QMessageBox.information(
            self,
            "Próximamente",
            "Este reporte estará disponible en una próxima versión."
        )
        return False
