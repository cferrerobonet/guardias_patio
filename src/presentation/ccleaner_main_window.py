"""
Ventana Principal Estilo CCleaner
==================================
Layout profesional con sidebar oscuro y contenido blanco.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.orm import Session

from presentation.components.ccleaner_sidebar import SidebarMenu
from presentation.forms.asignacion_guardias_form import AsignacionGuardiasForm
from presentation.forms.configuracion_form import ConfiguracionForm
from presentation.forms.import_export_form import ImportExportForm

# Importar formularios existentes (los vamos a wrapper)
from presentation.forms.profesor_form import ProfesorForm
from presentation.forms.zona_form import ZonaForm
from presentation.themes.ccleaner_theme import (
    CONTENT_BG,
    get_complete_stylesheet,
)
from presentation.widgets import (
    DashboardResumen,
    GestionarAusenciasForm,
    GestorSustituciones,
    PanelEstadisticas,
    ReportesForm,
    VistaCalendario,
)


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
        scroll.setStyleSheet(f"background-color: {CONTENT_BG}; border: none;")
        scroll.setWidget(container)

        layout.addWidget(scroll)


class CCleanerMainWindow(QMainWindow):
    """Ventana principal con diseño estilo CCleaner"""

    def __init__(self, session: Session, sync_manager=None):
        super().__init__()
        self.session = session
        self.sync_manager = sync_manager
        self.widgets = {}
        self.setup_ui()

    def setup_ui(self):
        """Configurar la interfaz principal"""
        self.setWindowTitle("Guardias de Patio")
        self.setMinimumSize(1400, 900)

        # Abrir en pantalla completa (fullscreen)
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

        # Sidebar
        self.sidebar = SidebarMenu()
        self.sidebar.section_changed.connect(self.on_section_changed)
        content_layout.addWidget(self.sidebar)

        # Stacked widget para el contenido
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet(f"background-color: {CONTENT_BG};")
        content_layout.addWidget(self.content_stack)

        main_layout.addLayout(content_layout)

        # Crear todas las vistas
        self.create_views()

        # Conectar señales de los widgets
        self.connect_signals()

        # Activar la primera sección (Dashboard)
        self.sidebar.set_active_section("dashboard")

    def create_views(self):
        """Crear todas las vistas/páginas de la aplicación"""

        # INICIO
        self.add_view("dashboard", "Dashboard", DashboardResumen())

        # GESTIÓN
        self.add_view("profesores", "Gestión de Profesores", ProfesorForm(self.session))
        self.add_view("zonas", "Gestión de Zonas", ZonaForm(self.session))
        self.add_view(
            "configuracion",
            "Configuración del Sistema",
            ConfiguracionForm(self.session),
        )

        # GUARDIAS
        self.add_view(
            "asignacion",
            "Asignación de Guardias",
            AsignacionGuardiasForm(self.session, sync_manager=self.sync_manager),
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
        self.add_view("reportes", "Generador de Reportes", ReportesForm())
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
        # Dashboard - conectar botones de acceso rápido
        dashboard_widget = None

        # Buscar los widgets dentro de los wrappers
        for key, wrapper in self.widgets.items():
            if key == "dashboard":
                # El ContentWrapper tiene un scroll con un container
                scroll = wrapper.findChild(QScrollArea)
                if scroll and scroll.widget():
                    container = scroll.widget()
                    dashboard_widget = container.findChild(DashboardResumen)

        if dashboard_widget:
            dashboard_widget.btn_generar.boton.clicked.connect(
                lambda: self.sidebar.set_active_section("asignacion")
            )
            dashboard_widget.btn_calendario.boton.clicked.connect(
                lambda: self.sidebar.set_active_section("calendario")
            )
            dashboard_widget.btn_ausencias.boton.clicked.connect(
                lambda: self.sidebar.set_active_section("ausencias")
            )
            dashboard_widget.btn_profesores.boton.clicked.connect(
                lambda: self.sidebar.set_active_section("profesores")
            )
            dashboard_widget.btn_exportar.boton.clicked.connect(
                lambda: self.sidebar.set_active_section("importar")
            )
            dashboard_widget.btn_reportes.boton.clicked.connect(
                lambda: self.sidebar.set_active_section("reportes")
            )
