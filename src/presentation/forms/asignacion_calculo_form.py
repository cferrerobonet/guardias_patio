"""
Formulario de cálculo y asignación de guardias.

Permite calcular la distribución teórica de guardias por profesor.
"""

import ui_styles as styles
from application.use_cases.asignacion_guardias import (
    ObtenerEstadisticasUseCase,
)
from core.exceptions import BusinessLogicError
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QGridLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.orm import Session

from presentation.forms.asignacion_widgets import CalculoPanel
from presentation.forms.base_form import BaseForm


class AsignacionCalculoForm(BaseForm):
    """
    Formulario para calcular distribución de guardias.

    Permite:
    - Ver estadísticas del curso
    - Calcular distribución teórica de guardias por profesor
    - Visualizar cuotas y disponibilidad
    """

    def __init__(self, session: Session, sync_manager=None):
        """
        Inicializar el formulario de cálculo de distribución.

        Args:
            session: Sesión de SQLAlchemy para acceso a base de datos
            sync_manager: Gestor de sincronización con la nube (opcional)
        """
        super().__init__(session)

        # Guardar sync_manager
        self.sync_manager = sync_manager

        # Inicializar Use Cases
        self.obtener_estadisticas_uc = ObtenerEstadisticasUseCase(session)

        self.setWindowTitle("Cálculo y Asignación")
        self.setup_ui()
        self.cargar_estadisticas()

    def cargar_datos(self):
        """
        Recargar estadísticas cuando cambia el curso activo.

        Este método es llamado automáticamente por el sistema de señales
        cuando el usuario cambia de curso escolar.
        """
        self.logger.info("🔄 Recargando estadísticas para el curso activo")
        self.session.expire_all()  # Limpiar caché de SQLAlchemy
        self.cargar_estadisticas()

    def setup_ui(self):
        """Configurar la interfaz de usuario del formulario"""
        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Título principal
        titulo = QLabel("📊 CÁLCULO Y ASIGNACIÓN")
        titulo.setStyleSheet(styles.STYLE_TITLE_MAIN)
        main_layout.addWidget(titulo)

        # Instrucciones compactas
        instrucciones = QLabel(
            "Revisa las estadísticas del curso y calcula las cuotas de distribución "
            "antes de generar el calendario de guardias."
        )
        instrucciones.setWordWrap(True)
        instrucciones.setStyleSheet("""
            QLabel {
                background-color: #EFF6FF;
                border: 1px solid #BFDBFE;
                border-radius: 6px;
                padding: 10px;
                color: #1E40AF;
                font-size: 13px;
            }
        """)
        main_layout.addWidget(instrucciones)

        # Crear el contenedor con scroll
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Widget contenedor del contenido
        content_widget = QWidget()
        grid_layout = QGridLayout()
        grid_layout.setSpacing(12)
        grid_layout.setVerticalSpacing(12)
        grid_layout.setContentsMargins(10, 10, 10, 10)
        content_widget.setLayout(grid_layout)

        # ============ COLUMNA IZQUIERDA: Panel combinado ============

        left_container = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        # Panel combinado de estadísticas y cuotas
        self.calculo_panel = CalculoPanel(self.session)
        left_layout.addWidget(self.calculo_panel, 1)

        left_container.setLayout(left_layout)
        grid_layout.addWidget(left_container, 0, 0)

        # ============ COLUMNA DERECHA: Espacio para futuro widget ============

        right_container = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        # Placeholder para futuro widget
        placeholder = QLabel("📌 Espacio reservado para futuro widget")
        placeholder.setStyleSheet("""
            QLabel {
                background-color: #f3f4f6;
                border: 2px dashed #d1d5db;
                border-radius: 6px;
                padding: 40px;
                color: #6b7280;
                font-size: 14px;
                font-style: italic;
            }
        """)
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setMinimumHeight(400)
        right_layout.addWidget(placeholder, 1)

        right_container.setLayout(right_layout)
        grid_layout.addWidget(right_container, 0, 1)

        # Configurar proporciones de columnas (50-50)
        grid_layout.setColumnStretch(0, 1)
        grid_layout.setColumnStretch(1, 1)

        # Agregar el widget al scroll area
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

        self.setLayout(main_layout)

    def cargar_estadisticas(self):
        """Cargar y mostrar estadísticas del curso"""
        try:
            # Ejecutar Use Case
            stats = self.obtener_estadisticas_uc.execute()

            # Delegar al panel combinado
            self.calculo_panel.mostrar_estadisticas(stats)

        except BusinessLogicError as e:
            self.calculo_panel.mostrar_error(str(e))
        except Exception as e:
            self.manejar_excepcion(e, "cargar estadísticas")

    def limpiar_formulario(self):
        """Limpiar todos los campos del formulario"""
        self.calculo_panel.limpiar()
        self.cargar_estadisticas()

    def validar_formulario(self) -> bool:
        """
        Validar el formulario (no necesario, validación en Use Cases).

        Returns:
            True siempre, la validación real ocurre en los Use Cases
        """
        return True
