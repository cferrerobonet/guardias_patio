"""
Formulario de cálculo y distribución de guardias.

Permite calcular la distribución teórica de guardias por profesor.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QGridLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.orm import Session

import ui_styles as styles
from application.use_cases.asignacion_guardias import (
    CalcularDistribucionUseCase,
    ObtenerEstadisticasUseCase,
)
from core.exceptions import BusinessLogicError
from presentation.forms.asignacion_widgets import (
    CuotasPanel,
    DistribucionPanel,
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
        self.calcular_distribucion_uc = CalcularDistribucionUseCase(session)

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

        # Instrucciones
        instrucciones = QLabel(
            "Este formulario calcula la distribución teórica de guardias por profesor. "
            "Revisa las estadísticas del curso y pulsa el botón para calcular."
        )
        instrucciones.setWordWrap(True)
        instrucciones.setStyleSheet("""
            QLabel {
                background-color: #EFF6FF;
                border: 1px solid #BFDBFE;
                border-radius: 6px;
                padding: 12px;
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

        # ============ COLUMNA IZQUIERDA ============

        left_container = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        # Paso 1: Estadísticas del Curso
        step1_label = QLabel("1️⃣ Estadísticas del Curso")
        step1_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #1976D2;")
        left_layout.addWidget(step1_label)

        self.estadisticas_panel = EstadisticasPanel()
        left_layout.addWidget(self.estadisticas_panel)

        # Paso 3: Cuotas Calculadas
        step3_label = QLabel("3️⃣ Cuotas Calculadas por Profesor")
        step3_label.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #1976D2; margin-top: 10px;"
        )
        left_layout.addWidget(step3_label)

        self.cuotas_panel = CuotasPanel(self.session)
        left_layout.addWidget(self.cuotas_panel)

        left_container.setLayout(left_layout)
        grid_layout.addWidget(left_container, 0, 0)

        # ============ COLUMNA DERECHA ============

        right_container = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        # Paso 2: Calcular Distribución
        step2_label = QLabel("2️⃣ Calcular Distribución")
        step2_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #1976D2;")
        right_layout.addWidget(step2_label)

        calc_button = QPushButton("📊 Calcular Distribución Teórica")
        calc_button.setStyleSheet(styles.STYLE_BUTTON_PRIMARY)
        calc_button.setMinimumHeight(50)
        calc_button.setMaximumHeight(50)
        calc_button.clicked.connect(self.calcular_distribucion)
        right_layout.addWidget(calc_button)

        # Panel de distribución por profesor (ocupa toda la altura restante)
        self.distribucion_panel = DistribucionPanel(self.session)
        right_layout.addWidget(self.distribucion_panel)

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

    def calcular_distribucion(self):
        """Calcular y mostrar la distribución de guardias"""
        try:
            # Ejecutar Use Case
            distribucion_dto = self.calcular_distribucion_uc.execute()

            # Delegar al widget
            self.distribucion_panel.mostrar_distribucion(distribucion_dto)

            # Actualizar el panel de cuotas (recalcula desde BD)
            self.cuotas_panel.calcular_cuotas()

            self.mostrar_exito(
                "Distribución calculada",
                "La distribución teórica se ha calculado correctamente.\n\n"
                "Ahora puedes ir a 'Generación y Resultados' para crear el calendario."
            )

        except BusinessLogicError as e:
            self.mostrar_error("Error en Cálculo", str(e))
            self.distribucion_panel.mostrar_error(str(e))

        except Exception as e:
            self.manejar_excepcion(e, "calcular distribución")

    def limpiar_formulario(self):
        """Limpiar todos los campos del formulario"""
        self.estadisticas_panel.limpiar()
        self.distribucion_panel.limpiar()
        self.cargar_estadisticas()

    def validar_formulario(self) -> bool:
        """
        Validar el formulario (no necesario, validación en Use Cases).

        Returns:
            True siempre, la validación real ocurre en los Use Cases
        """
        return True
