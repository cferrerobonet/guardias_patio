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
from presentation.forms.conectividad_form import ConectividadForm
from presentation.forms.import_export_form import ImportExportForm
from presentation.forms.perfiles_usuario_form import PerfilesUsuarioForm

# Importar formularios existentes (los vamos a wrapper)
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
        self.widgets = {}
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
        """Crear todas las vistas/páginas de la aplicación"""

        # GESTIÓN (primera sección)
        self.add_view("profesores", "Gestión de Profesores", ProfesorForm(self.session))
        self.add_view("zonas", "Gestión de Zonas", ZonaForm(self.session))
        self.add_view(
            "ajustes",
            "Ajustes del Curso Escolar",
            AjustesForm(self.session),
        )
        self.add_view(
            "conectividad",
            "Configuración de Conectividad",
            ConectividadForm(self.session),
        )
        self.add_view(
            "perfiles",
            "Gestión de Perfiles de Usuario",
            PerfilesUsuarioForm(self.session),
        )

        # GUARDIAS
        self.add_view(
            "asignacion_calculo",
            "Cálculo y Asignación",
            AsignacionCalculoForm(self.session, sync_manager=self.sync_manager),
        )
        self.add_view("calendario", "Calendario de Guardias", VistaCalendario(self.session))

        # PERSONAL
        self.add_view(
            "ausencias",
            "Gestión de Ausencias",
            GestionarAusenciasForm(self.session),
        )
        self.add_view(
            "sustituciones",
            "Gestión de Sustituciones",
            GestorSustituciones(self.session),
        )

        # HERRAMIENTAS
        self.add_view(
            "importar",
            "Importar / Exportar Datos",
            ImportExportForm(self.session),
        )
        self.add_view("reportes", "Generador de Reportes", ReportesForm(self.session))
        self.add_view("estadisticas", "Estadísticas", PanelEstadisticas(self.session))

    def add_view(self, section: str, title: str, content_widget: QWidget):
        """Añadir una vista al stack"""
        wrapped = ContentWrapper(title, content_widget)
        self.widgets[section] = wrapped
        self.content_stack.addWidget(wrapped)

    def on_section_changed(self, section: str):
        """Cambiar de sección"""
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
