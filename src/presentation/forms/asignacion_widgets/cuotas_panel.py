"""Widget para mostrar cuotas calculadas antes de generar guardias.

Integra CalcularCuotasUseCase para preview de distribución esperada.
"""

import ui_styles as styles
from application.dtos.domain_services_dtos import CalcularCuotasRequest
from application.use_cases.calcular_cuotas_use_case import CalcularCuotasUseCase
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)
from sqlalchemy.orm import Session


class CuotasPanel(QGroupBox):
    """Panel para calcular y mostrar cuotas esperadas usando Domain Services.

    Muestra:
    - Tabla con cuotas por profesor
    - Porcentaje de jornada
    - Total de guardias a asignar
    - Botón para recalcular

    Señales:
        cuotas_calculadas: Emitida cuando se calculan cuotas exitosamente.
    """

    cuotas_calculadas = pyqtSignal(dict)  # Emite {profesor_id: cuota}

    def __init__(self, session: Session, parent=None):
        """Inicializa el panel de cuotas.

        Args:
            session: Sesión de SQLAlchemy para consultas.
            parent: Widget padre opcional.
        """
        super().__init__("📐 Cuotas Calculadas (Domain Services)", parent)
        self.session = session
        self.calcular_cuotas_uc = CalcularCuotasUseCase(session)
        self.configuracion_id = None

        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 2px solid #f59e0b;
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
                color: #d97706;
            }
        """)
        self._setup_ui()

    def _setup_ui(self):
        """Crea la interfaz del widget."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 8, 6, 8)
        layout.setSpacing(6)

        # Botón calcular
        button_layout = QHBoxLayout()
        self.calcular_button = QPushButton("🔢 Calcular Cuotas")
        self.calcular_button.setStyleSheet(styles.STYLE_BUTTON_PRIMARY)
        self.calcular_button.setMinimumHeight(35)
        self.calcular_button.clicked.connect(self.calcular_cuotas)
        button_layout.addWidget(self.calcular_button)

        self.total_label = QPushButton("Total: -- guardias")
        self.total_label.setStyleSheet(styles.STYLE_BUTTON_SUCCESS)
        self.total_label.setMinimumHeight(35)
        self.total_label.setEnabled(False)
        button_layout.addWidget(self.total_label)

        layout.addLayout(button_layout)

        # Tabla de cuotas
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels([
            "Profesor",
            "Jornada %",
            "Cuota Esperada",
            "Estado"
        ])
        self.tabla.setMinimumHeight(250)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 4px;
                gridline-color: #e5e7eb;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #f3f4f6;
                padding: 6px;
                border: none;
                border-right: 1px solid #e5e7eb;
                border-bottom: 1px solid #e5e7eb;
                font-weight: bold;
            }
        """)

        # Ajustar tamaño de columnas
        self.tabla.setColumnWidth(0, 200)  # Profesor
        self.tabla.setColumnWidth(1, 100)  # Jornada
        self.tabla.setColumnWidth(2, 120)  # Cuota
        self.tabla.setColumnWidth(3, 100)  # Estado

        layout.addWidget(self.tabla)
        self.setLayout(layout)

    def set_configuracion(self, configuracion_id: int):
        """Establece la configuración para calcular cuotas.

        Args:
            configuracion_id: ID de la configuración activa.
        """
        self.configuracion_id = configuracion_id

    def calcular_cuotas(self):
        """Calcula y muestra las cuotas usando el Use Case."""
        # Obtener configuración activa
        if not self.configuracion_id:
            from models.models import Configuracion

            # Obtener la configuración (solo hay una por usuario)
            configuracion = self.session.query(Configuracion).first()

            if not configuracion:
                from PyQt6.QtWidgets import QMessageBox
                from utils.ui_helpers import MESSAGEBOX_STYLE
                msg = QMessageBox(self)
                msg.setWindowTitle("Sin Configuración")
                msg.setText(
                    "No hay una configuración para el sistema.\n\n"
                    "Debe configurar los parámetros en Ajustes del Curso Escolar."
                )
                msg.setStyleSheet(MESSAGEBOX_STYLE)
                msg.exec()
                return

            # Verificar que haya un curso activo usando el GestorCursos
            from services.gestor_cursos import GestorCursos
            curso_activo = GestorCursos.obtener_curso_activo(self.session)
            if not curso_activo:
                from PyQt6.QtWidgets import QMessageBox
                from utils.ui_helpers import MESSAGEBOX_STYLE
                msg = QMessageBox(self)
                msg.setWindowTitle("Sin Curso Activo")
                msg.setText("No hay un curso escolar activo.\n\nDebe activar un curso en Ajustes.")
                msg.setStyleSheet(MESSAGEBOX_STYLE)
                msg.exec()
                return

            self.configuracion_id = configuracion.id

        try:
            # Deshabilitar botón
            self.calcular_button.setEnabled(False)
            self.calcular_button.setText("⏳ Calculando...")

            # Ejecutar Use Case
            request = CalcularCuotasRequest(
                configuracion_id=self.configuracion_id,
                solo_activos=True
            )
            response = self.calcular_cuotas_uc.execute(request)

            if response.exitoso:
                self._mostrar_cuotas(response)
                # Emitir señal
                self.cuotas_calculadas.emit(response.cuotas)
            else:
                self._mostrar_error(response.mensaje)

        except Exception as e:
            self._mostrar_error(f"Error al calcular cuotas: {str(e)}")
        finally:
            # Rehabilitar botón
            self.calcular_button.setEnabled(True)
            self.calcular_button.setText("🔢 Calcular Cuotas")

    def _mostrar_cuotas(self, response):
        """Muestra las cuotas en la tabla.

        Args:
            response: CalcularCuotasResponse con cuotas detalladas.
        """
        # Actualizar total
        self.total_label.setText(f"Total: {response.total_guardias} guardias")

        # Llenar tabla
        self.tabla.setRowCount(len(response.cuotas_detalle))

        for i, cuota_dto in enumerate(response.cuotas_detalle):
            # Profesor
            item_nombre = QTableWidgetItem(cuota_dto.profesor_nombre)
            item_nombre.setFlags(item_nombre.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabla.setItem(i, 0, item_nombre)

            # Jornada (placeholder - necesitaríamos agregarlo al DTO)
            item_jornada = QTableWidgetItem("--")
            item_jornada.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_jornada.setFlags(item_jornada.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabla.setItem(i, 1, item_jornada)

            # Cuota
            item_cuota = QTableWidgetItem(str(cuota_dto.cuota_esperada))
            item_cuota.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_cuota.setFlags(item_cuota.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabla.setItem(i, 2, item_cuota)

            # Estado
            item_estado = QTableWidgetItem("⏳ Pendiente")
            item_estado.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_estado.setFlags(item_estado.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabla.setItem(i, 3, item_estado)

    def _mostrar_error(self, mensaje: str):
        """Muestra mensaje de error."""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(
            self,
            "Error al Calcular Cuotas",
            mensaje
        )
        self.tabla.setRowCount(0)
        self.total_label.setText("Total: -- guardias")

    def limpiar(self):
        """Limpia el contenido del panel."""
        self.tabla.setRowCount(0)
        self.total_label.setText("Total: -- guardias")

    def actualizar_estado_asignacion(self, cuotas_asignadas: dict):
        """Actualiza el estado después de asignar guardias.

        Args:
            cuotas_asignadas: Diccionario {profesor_id: guardias_asignadas}
        """
        for row in range(self.tabla.rowCount()):
            # Obtener profesor_id del nombre (simplificado)
            # En producción, guardaríamos el ID en el item
            item_estado = self.tabla.item(row, 3)
            item_cuota = self.tabla.item(row, 2)

            if item_cuota and item_estado:
                int(item_cuota.text())
                # Aquí necesitaríamos el profesor_id real
                # Por ahora, marcamos como completado genéricamente
                item_estado.setText("✅ Asignado")
