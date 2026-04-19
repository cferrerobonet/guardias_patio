"""
Formulario de asignación de guardias.

Permite calcular distribución y generar el calendario completo de guardias.
"""

import ui_styles as styles
from application.use_cases.asignacion_guardias import (
    CalcularDistribucionUseCase,
    GenerarGuardiasUseCase,
    ObtenerEstadisticasUseCase,
)
from application.use_cases.guardia import LimpiarGuardiasUseCase
from core.exceptions import BusinessLogicError
from infrastructure.database.models import Guardia
from infrastructure.repositories import SQLAlchemyGuardiaRepository
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.orm import Session
from utils.icons import icon_for_button

from presentation.forms.asignacion_widgets import (
    CuotasPanel,
    EstadisticasPanel,
    IncidenciasPanel,
    ResultadosPanel,
)
from presentation.forms.base_form import BaseForm
from presentation.widgets.progress_indicators import ejecutar_con_progreso


class AsignacionGuardiasForm(BaseForm):
    """
    Formulario para calcular y asignar guardias.

    Permite:
    - Ver estadísticas del curso
    - Calcular distribución de guardias por profesor
    - Generar el calendario completo de guardias
    """

    # =============== PROPIEDADES DE COMPATIBILIDAD ===============
    # Estas propiedades permiten acceso directo a los widgets internos de los paneles
    # para mantener compatibilidad con tests existentes.

    @property
    def stats_text(self):
        """Acceso al QTextEdit de estadísticas (delegado al panel)."""
        return self.estadisticas_panel.stats_text

    @property
    def cuotas_text(self):
        """Acceso al QTextEdit de cuotas (delegado al panel)."""
        return self.cuotas_panel.cuotas_text

    @property
    def resultado_text(self):
        """Acceso al QTextEdit de resultados (delegado al panel)."""
        return self.resultados_panel.resultado_text

    # =============================================================

    def __init__(self, session: Session, sync_manager=None):
        """
        Inicializar el formulario de asignación de guardias.

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
        # Usar algoritmo v4.0 Híbrido (5 fases)
        self.generar_guardias_uc = GenerarGuardiasUseCase(session)

        # Repositorio para limpiar guardias
        guardia_repo = SQLAlchemyGuardiaRepository(session)
        self.limpiar_guardias_uc = LimpiarGuardiasUseCase(guardia_repo)

        self.setWindowTitle("Asignación de Guardias")
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
        titulo = QLabel("ASIGNACIÓN DE GUARDIAS")
        titulo.setStyleSheet(styles.STYLE_TITLE_MAIN)
        main_layout.addWidget(titulo)

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

        # ============ FILA 0: ESTADÍSTICAS Y CUOTAS ============

        # Panel de estadísticas (izquierda)
        self.estadisticas_panel = EstadisticasPanel()
        grid_layout.addWidget(self.estadisticas_panel, 0, 0)

        # Panel de cuotas (derecha) - incluye botón "Calcular Cuotas"
        self.cuotas_panel = CuotasPanel(self.session)
        grid_layout.addWidget(self.cuotas_panel, 0, 1)

        # ============ FILA 1: RESULTADOS E INCIDENCIAS ============

        # Panel de resultados (izquierda) - incluye métricas de equidad
        self.resultados_panel = ResultadosPanel(self.session)
        grid_layout.addWidget(self.resultados_panel, 1, 0)

        # Panel de incidencias (derecha)
        self.incidencias_panel = IncidenciasPanel(self.session)
        grid_layout.addWidget(self.incidencias_panel, 1, 1)

        # ============ FILA 2: BOTONES DE ACCIÓN ============

        # Contenedor de botones
        button_container = QWidget()
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 10)
        button_layout.setSpacing(15)
        button_container.setLayout(button_layout)

        button_layout.addStretch()

        # Botón generar
        self.generar_button = QPushButton("Generar Asignación")
        self.generar_button.setIcon(icon_for_button("target"))
        self.generar_button.setStyleSheet(styles.STYLE_BUTTON_PRIMARY)
        self.generar_button.setMinimumWidth(220)
        self.generar_button.setMinimumHeight(40)
        self.generar_button.setMaximumHeight(40)
        self.generar_button.clicked.connect(self.generar_guardias)
        button_layout.addWidget(self.generar_button)

        # Botón limpiar
        self.limpiar_button = QPushButton("Limpiar Guardias")
        self.limpiar_button.setIcon(icon_for_button("delete"))
        self.limpiar_button.setStyleSheet(styles.STYLE_BUTTON_DANGER)
        self.limpiar_button.setMinimumWidth(220)
        self.limpiar_button.setMinimumHeight(40)
        self.limpiar_button.setMaximumHeight(40)
        self.limpiar_button.clicked.connect(self.limpiar_guardias)
        button_layout.addWidget(self.limpiar_button)

        button_layout.addStretch()

        grid_layout.addWidget(button_container, 2, 0, 1, 2)

        # Configurar proporciones de columnas
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
        except (ValueError, TypeError, OSError) as e:
            self.manejar_excepcion(e, "cargar estadísticas")

    def calcular_distribucion(self):
        """Calcular y mostrar la distribución de guardias (delegado a cuotas_panel)"""
        # Ahora la funcionalidad está integrada en CuotasPanel
        self.cuotas_panel.calcular_cuotas()

    def generar_guardias(self):
        """Generar el calendario completo de guardias"""
        try:
            # Verificar si ya existen guardias
            from application.app_services import AppServices
            count_guardias = AppServices(self.session).contar_guardias()

            eliminar_existentes = True  # Por defecto, eliminar

            if count_guardias > 0:
                from PyQt6.QtWidgets import QMessageBox
                from utils.ui_helpers import show_question_with_cancel

                respuesta = show_question_with_cancel(
                    self,
                    "⚠️ Guardias Existentes",
                    f"Ya existen {count_guardias} guardias en la base de datos.\n\n"
                    f"¿Deseas ELIMINAR todas las guardias existentes "
                    f"antes de generar nuevas?\n\n"
                    f"• SÍ: Eliminará todas y generará desde cero (recomendado)\n"
                    f"• NO: Agregará nuevas guardias a las existentes "
                    f"(puede crear duplicados)",
                    default_button="Yes",
                )

                if respuesta == QMessageBox.StandardButton.Cancel:
                    return

                eliminar_existentes = respuesta == QMessageBox.StandardButton.Yes

                if eliminar_existentes:
                    self.mostrar_exito(
                        "Limpieza completada",
                        f"{count_guardias} guardias eliminadas. Generando calendario nuevo...",
                    )

            # Función para ejecutar con progreso
            def tarea_generacion(progress_callback):
                """Ejecuta la generación de guardias con callback de progreso."""

                # Adapter para convertir (mensaje, porcentaje) a formato esperado por ProgressDialog
                def adapted_callback(mensaje: str, porcentaje: int):
                    # El dialog espera (actual, total, detalle)
                    # Convertimos porcentaje (0-100) a actual/total
                    progress_callback(porcentaje, 100, mensaje)

                return self.generar_guardias_uc.execute(
                    eliminar_existentes=eliminar_existentes,
                    progress_callback=adapted_callback,
                )

            # Ejecutar con indicador de progreso mejorado
            resumen = ejecutar_con_progreso(
                self,  # parent debe ser el primer argumento
                tarea_generacion,
                titulo="Generando Guardias",
                mensaje="Preparando generación de calendario...",
            )

            # Verificar si hubo cancelación o error
            if resumen is None:
                self.logger.warning("Generación cancelada o con error")
                return

            if resumen:
                # Delegar a los widgets (equidad integrada en resultados_panel)
                self.resultados_panel.mostrar_resultados(resumen)
                self.incidencias_panel.analizar_incidencias(resumen)

                self.mostrar_exito(
                    "Asignación generada",
                    resumen.mensaje or "Guardias generadas y guardadas en la base de datos.",
                )

                # Sincronizar con la nube si está disponible
                if self.sync_manager:
                    try:
                        from utils.logger import get_logger

                        logger = get_logger(__name__)
                        logger.info("Sincronizando guardias generadas con la nube...")
                        if self.sync_manager.sync_on_shutdown(session=self.session):
                            logger.info("✓ Guardias sincronizadas con la nube")
                            self.mostrar_exito(
                                "Sincronización completada",
                                "Las guardias generadas se han guardado en la nube correctamente.",
                            )
                        else:
                            logger.warning("⚠ Problemas al sincronizar con la nube")
                    except (ValueError, TypeError, OSError) as e:
                        from utils.logger import get_logger

                        logger = get_logger(__name__)
                        logger.error(f"Error al sincronizar: {e}")
                        # No mostrar error al usuario, solo logging

        except BusinessLogicError as e:
            self.mostrar_error("Error en Generación", str(e))

        except (ValueError, TypeError, OSError) as e:
            self.manejar_excepcion(e, "generar guardias")

    def limpiar_formulario(self):
        """Limpiar todos los campos del formulario"""
        self.estadisticas_panel.limpiar()
        self.cuotas_panel.limpiar()
        self.resultados_panel.limpiar()
        self.incidencias_panel.limpiar()
        self.cargar_estadisticas()

    def limpiar_guardias(self):
        """Eliminar todas las guardias del sistema"""
        try:
            # Contar guardias actuales
            from application.app_services import AppServices
            count_actual = AppServices(self.session).contar_guardias()

            if count_actual == 0:
                self.mostrar_advertencia(
                    "Sin guardias", "No hay guardias en el sistema para eliminar."
                )
                return

            # Confirmar con el usuario
            confirmado = self.confirmar_accion(
                "⚠️  LIMPIAR TODAS LAS GUARDIAS",
                f"¿Estás seguro de que deseas eliminar TODAS las {count_actual} guardias?\n\n"
                "Esta acción:\n"
                "• Eliminará todas las asignaciones de guardias\n"
                "• Liberará a todos los profesores\n"
                "• Liberará todas las zonas\n"
                "• NO se puede deshacer\n\n"
                "¿Deseas continuar?",
            )

            if not confirmado:
                return

            # Ejecutar limpieza
            count = self.limpiar_guardias_uc.execute()

            # Actualizar UI
            self.limpiar_formulario()

            self.mostrar_exito(
                "Limpieza completada",
                f"Se han eliminado {count} guardias del sistema.\n\n"
                "Ahora puedes:\n"
                "• Eliminar zonas o profesores\n"
                "• Generar nuevas guardias desde cero",
            )

        except (ValueError, TypeError, OSError) as e:
            self.manejar_excepcion(e, "limpiar guardias")

    def validar_formulario(self) -> bool:
        """
        Validar el formulario (no necesario, validación en Use Cases).

        Returns:
            True siempre, la validación real ocurre en los Use Cases
        """
        return True
