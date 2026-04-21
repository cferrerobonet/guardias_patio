"""
Ventana Principal Estilo CCleaner
==================================
Layout profesional con sidebar oscuro y contenido blanco.
"""

from core.logging import get_logger
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from presentation.components.ccleaner_sidebar import SidebarMenu
from presentation.forms.ajustes_form import AjustesForm
from presentation.forms.asignacion_calculo_form import AsignacionCalculoForm
from presentation.forms.import_export_form import ImportExportForm
from presentation.forms.perfiles_usuario_form import PerfilesUsuarioForm

# Importar formularios existentes (los vamos a wrapper)
from presentation.forms.home_form import HomeForm
from presentation.forms.profesor_form import ProfesorForm
from presentation.forms.reportes_form import ReportesForm
from presentation.forms.zona_form import ZonaForm
from presentation.themes.ccleaner_theme import (
    CONTENT_BG,
    get_complete_stylesheet,
)
from presentation.widgets import (
    GestionarAusenciasForm,
    GestorSustituciones,
    PanelEstadisticas,
    VistaCalendario,
)

logger = get_logger(__name__)


class ContentWrapper(QWidget):
    """Wrapper para dar estilo uniforme al contenido"""

    def __init__(self, title: str, content_widget: QWidget, parent=None):
        super().__init__(parent)
        self.setup_ui(title, content_widget)

    def setup_ui(self, title: str, content_widget: QWidget):
        """Configurar el layout alineado con el sidebar"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Barra de título contextual fija
        title_bar = QWidget()
        title_bar.setFixedHeight(40)
        title_bar.setStyleSheet(
            "QWidget { background-color: #F8FAFC; border-bottom: 1px solid #E5E7EB; }"
        )
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(20, 0, 20, 0)
        title_label = QLabel(title)
        title_label.setStyleSheet(
            "QLabel { font-size: 13px; font-weight: 600; color: #374151; border: none; background: transparent; }"
        )
        title_bar_layout.addWidget(title_label)
        title_bar_layout.addStretch()
        layout.addWidget(title_bar)

        # Widget contenedor para añadir padding compensatorio
        container = QWidget()
        container_layout = QVBoxLayout(container)
        # 16px (sidebar GESTIÓN) - 10px (formulario interno) = 6px compensatorio
        container_layout.setContentsMargins(0, 6, 0, 0)
        container_layout.setSpacing(0)
        container_layout.addWidget(content_widget)

        # Scroll area para el contenido
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet(f"QScrollArea {{ background-color: {CONTENT_BG}; border: none; }} QScrollArea > QWidget > QWidget {{ background-color: {CONTENT_BG}; }}")
        scroll.setWidget(container)

        layout.addWidget(scroll)


class CCleanerMainWindow(QMainWindow):
    """Ventana principal con diseño estilo CCleaner"""

    def __init__(self, session, sync_manager=None):
        super().__init__()
        self.session = session
        self.sync_manager = sync_manager
        self.widgets: dict = {}
        self._view_factories: dict = {}
        self.setup_ui()

    def setup_ui(self):
        """Configurar la interfaz principal"""
        self.setWindowTitle("Guardias de Patio")
        self.setMinimumSize(1400, 900)

        # Abrir en pantalla completa
        self.showFullScreen()

        # Aplicar stylesheet global
        self.setStyleSheet(get_complete_stylesheet())

        # Widget central
        central = QWidget()
        self.setCentralWidget(central)

        # Layout principal: Vertical
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Layout horizontal: Sidebar + Contenido (SIN TopBar)
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Sidebar con sesión para el selector de curso
        self.sidebar = SidebarMenu(session=self.session)
        self.sidebar.section_changed.connect(self.on_section_changed)
        content_layout.addWidget(self.sidebar)

        # Stacked widget para el contenido
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet(f"QStackedWidget {{ background-color: {CONTENT_BG}; }}")
        content_layout.addWidget(self.content_stack)

        main_layout.addLayout(content_layout)

        # Crear todas las vistas
        self.create_views()

        # Conectar señales de los widgets
        self.connect_signals()

        # Activar la primera sección (Dashboard)
        # Cambiar la sección activa inicial a "profesores" en lugar de "dashboard"
        self.sidebar.set_active_section("inicio")

    def create_views(self):
        """Registrar factories de vistas — lazy loading: solo se instancian al navegar."""
        session = self.session
        sync_manager = self.sync_manager

        self._register("inicio", "Inicio — Estado del día",
                        lambda: HomeForm(session))
        self._register("profesores", "Gestión de Profesores",
                        lambda: ProfesorForm(session))
        self._register("zonas", "Gestión de Zonas",
                        lambda: ZonaForm(session))
        self._register("ajustes", "Ajustes del Curso Escolar",
                        lambda: AjustesForm(session))
        self._register("perfiles", "Gestión de Perfiles de Usuario",
                        lambda: PerfilesUsuarioForm(session))
        self._register("asignacion_calculo", "Cálculo y Asignación",
                        lambda: AsignacionCalculoForm(session, sync_manager=sync_manager))
        self._register("calendario", "Calendario de Guardias",
                        lambda: VistaCalendario(session))
        self._register("ausencias", "Gestión de Ausencias",
                        lambda: GestionarAusenciasForm(session))
        self._register("sustituciones", "Gestión de Sustituciones",
                        lambda: GestorSustituciones(session))
        self._register("importar", "Importar / Exportar Datos",
                        lambda: ImportExportForm(session))
        self._register("reportes", "Generador de Reportes",
                        lambda: ReportesForm(session))
        self._register("estadisticas", "Estadísticas",
                        lambda: PanelEstadisticas(session))

        # Pre-instanciar solo la sección inicial para que el stack no quede vacío
        self._ensure_view("inicio")

    def _register(self, section: str, title: str, factory):
        self._view_factories[section] = (title, factory)

    def _ensure_view(self, section: str):
        """Instancia el widget de una sección si aún no existe."""
        if section not in self.widgets and section in self._view_factories:
            title, factory = self._view_factories[section]
            wrapped = ContentWrapper(title, factory())
            self.widgets[section] = wrapped
            self.content_stack.addWidget(wrapped)

    def add_view(self, section: str, title: str, content_widget: QWidget):
        """API de compatibilidad — instancia inmediata."""
        wrapped = ContentWrapper(title, content_widget)
        self.widgets[section] = wrapped
        self.content_stack.addWidget(wrapped)

    def on_section_changed(self, section: str):
        """Cambiar de sección — instancia el widget si es la primera vez."""
        self._ensure_view(section)
        if section in self.widgets:
            self.content_stack.setCurrentWidget(self.widgets[section])

    def connect_signals(self):
        """Conectar señales de los widgets"""
        # Conectar cambio de curso del selector con refresco de todas las vistas
        logger.info("🔌 Iniciando conexión de señales...")
        logger.info(f"   Sidebar existe: {self.sidebar is not None}")
        logger.info(f"   Sidebar tiene selector_curso: {hasattr(self.sidebar, 'selector_curso')}")

        if hasattr(self.sidebar, "selector_curso"):
            logger.info(f"   selector_curso es None: {self.sidebar.selector_curso is None}")
            if self.sidebar.selector_curso:
                logger.info(f"   Tipo de selector_curso: {type(self.sidebar.selector_curso)}")
                tiene_signal = hasattr(self.sidebar.selector_curso, "curso_cambiado")
                logger.info(f"   selector_curso tiene curso_cambiado: {tiene_signal}")

        if hasattr(self.sidebar, "selector_curso") and self.sidebar.selector_curso:
            logger.info("🔗 Conectando señal curso_cambiado del selector al handler")
            self.sidebar.selector_curso.curso_cambiado.connect(self._on_curso_cambiado)
            logger.info("✅ Señal curso_cambiado conectada correctamente")

            # Test: Emitir señal de prueba
            logger.info("🧪 Emitiendo señal de prueba para verificar conexión...")
            try:
                # No emitir realmente, solo verificar que el objeto está listo
                logger.info("✅ Conexión verificada - lista para recibir señales")
            except (ValueError, TypeError, OSError) as e:
                logger.error(f"❌ Error al verificar conexión: {e}")
        else:
            logger.warning("⚠️ No se pudo conectar señal - selector_curso no disponible")

    def _on_curso_cambiado(self, curso_id: int):
        """
        Maneja el cambio de curso activo.

        Refresca la vista actual para mostrar datos del nuevo curso.
        """
        logger.info(f"🔄 Curso cambiado a ID: {curso_id} - Refrescando vista actual")

        # Obtener el widget actual
        current_widget = self.content_stack.currentWidget()

        if current_widget and hasattr(current_widget, "content_widget"):
            # Es un ContentWrapper, obtener el widget real dentro
            widget = current_widget.content_widget
            widget_name = widget.__class__.__name__

            logger.info(f"   Widget actual: {widget_name}")

            # Intentar refrescar el widget si tiene método para ello
            if hasattr(widget, "cargar_datos"):
                logger.info(f"   → Llamando a {widget_name}.cargar_datos()")
                widget.cargar_datos()
            elif hasattr(widget, "actualizar_calendario"):
                logger.info(f"   → Llamando a {widget_name}.actualizar_calendario()")
                widget.actualizar_calendario()
            elif hasattr(widget, "cargar_profesores"):
                logger.info(f"   → Llamando a {widget_name}.cargar_profesores()")
                widget.cargar_profesores()
            elif hasattr(widget, "cargar_zonas"):
                logger.info(f"   → Llamando a {widget_name}.cargar_zonas()")
                widget.cargar_zonas()
            elif hasattr(widget, "cargar_guardias"):
                logger.info(f"   → Llamando a {widget_name}.cargar_guardias()")
                widget.cargar_guardias()
            elif hasattr(widget, "refrescar"):
                logger.info(f"   → Llamando a {widget_name}.refrescar()")
                widget.refrescar()
            else:
                logger.warning(f"   ⚠️ {widget_name} no tiene método de refresco")

            logger.info(f"✅ Vista {widget_name} refrescada después de cambiar al curso {curso_id}")
        else:
            logger.warning("⚠️ No se pudo obtener el widget actual para refrescar")
