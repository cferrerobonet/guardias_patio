"""
Formulario de cálculo y distribución de guardias.

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

from presentation.forms.asignacion_widgets import (
    CuotasPanel,
    EstadisticasPanel,
)
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

        self.setWindowTitle("Cálculo y Distribución")
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
        titulo = QLabel("📊 CÁLCULO Y DISTRIBUCIÓN")
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

        # ============ COLUMNA IZQUIERDA: Estadísticas ============

        left_container = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        # Paso 1: Estadísticas del Curso
        step1_label = QLabel("1️⃣ Estadísticas del Curso")
        step1_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #1976D2;")
        left_layout.addWidget(step1_label)

        self.estadisticas_panel = EstadisticasPanel()
        left_layout.addWidget(self.estadisticas_panel)

        left_layout.addStretch()  # Empuja hacia arriba
        left_container.setLayout(left_layout)
        grid_layout.addWidget(left_container, 0, 0)

        # ============ COLUMNA DERECHA: Cuotas ============

        right_container = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        # Paso 2: Cuotas Calculadas (con botón integrado)
        step2_label = QLabel("2️⃣ Distribución de Cuotas")
        step2_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #1976D2;")
        right_layout.addWidget(step2_label)

        self.cuotas_panel = CuotasPanel(self.session)
        right_layout.addWidget(self.cuotas_panel)

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

            # Delegar al widget
            self.estadisticas_panel.mostrar_estadisticas(stats)

        except BusinessLogicError as e:
            self.estadisticas_panel.mostrar_error(str(e))
        except Exception as e:
            self.manejar_excepcion(e, "cargar estadísticas")

    def limpiar_formulario(self):
        """Limpiar todos los campos del formulario"""
        self.estadisticas_panel.limpiar()
        self.cuotas_panel.limpiar()
        self.cargar_estadisticas()

    def validar_formulario(self) -> bool:
        """
        Validar el formulario (no necesario, validación en Use Cases).

        Returns:
            True siempre, la validación real ocurre en los Use Cases
        """
        return True
