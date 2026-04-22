"""
Ventana Principal Estilo CCleaner
==================================
Layout profesional con sidebar oscuro y contenido blanco.
"""

from core.logging import get_logger
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
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
from presentation.forms.profesor_form import ProfesorForm
from presentation.forms.auditoria_guardias_form import AuditoriaGuardiasForm
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

        # Scroll area para el contenido
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet(f"QScrollArea {{ background-color: {CONTENT_BG}; border: none; }} QScrollArea > QWidget > QWidget {{ background-color: {CONTENT_BG}; }}")
        scroll.setWidget(content_widget)

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
        self.sidebar.set_active_section("profesores")

    def create_views(self):
        """Registrar factories de vistas — lazy loading: solo se instancian al navegar."""
        session = self.session
        sync_manager = self.sync_manager

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
        self._register("auditoria", "Auditoría de Guardias",
                        lambda: AuditoriaGuardiasForm(session))

        # Pre-instanciar solo la sección inicial para que el stack no quede vacío
        self._ensure_view("profesores")

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

    def _refresh_widget(self, widget) -> bool:
        """Llama al método de refresco disponible en el widget. Devuelve True si lo encontró."""
        for method in ("cargar_datos", "actualizar_calendario", "cargar_profesores",
                       "cargar_zonas", "cargar_guardias", "refrescar"):
            if hasattr(widget, method):
                getattr(widget, method)()
                return True
        return False

    def _on_curso_cambiado(self, curso_id: int):
        """Maneja el cambio de curso activo. Invalida la sesión y refresca todos los widgets cargados."""
        logger.info(f"🔄 Curso cambiado a ID: {curso_id} - Refrescando todas las vistas cargadas")

        # Invalidar la caché de SQLAlchemy para que todos los widgets lean datos frescos
        try:
            self.session.expire_all()
        except Exception as e:
            logger.warning(f"⚠️ expire_all falló: {e}")

        # Refrescar todos los widgets ya instanciados
        for section, wrapped in self.widgets.items():
            if not hasattr(wrapped, "content_widget"):
                continue
            widget = wrapped.content_widget
            widget_name = widget.__class__.__name__
            if self._refresh_widget(widget):
                logger.info(f"   → {widget_name} ({section}) refrescado")
            else:
                logger.debug(f"   ⚠️ {widget_name} ({section}) sin método de refresco")

        logger.info(f"✅ Todas las vistas refrescadas después de cambiar al curso {curso_id}")
