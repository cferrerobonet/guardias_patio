"""
Ventana principal modernizada con Microsoft Fluent Design.

Usa menú lateral en lugar de pestañas, con navegación moderna,
breadcrumbs, y diseño tipo Microsoft 365.
"""

from core.qt_imports import (
    QHBoxLayout,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from database.db_manager import SessionLocal
from presentation.components.sidebar_menu import MenuCategory, MenuItem, SidebarMenu
from presentation.components.top_bar import TopBar
from presentation.forms import (
    AsignacionGuardiasForm,
    CalendarioGuardiasForm,
    ConfiguracionForm,
    ImportExportForm,
    ProfesorForm,
    ZonaForm,
)
from presentation.themes.fluent_theme import get_complete_fluent_stylesheet
from presentation.widgets import (
    GestionarAusenciasForm,
    GestorSustituciones,
    PanelEstadisticas,
    VistaCalendario,
)
from presentation.widgets.observability_dashboard import ObservabilityDashboard


class FluentMainWindow(QWidget):
    """Ventana principal con diseño Microsoft Fluent."""

    def __init__(self, sync_manager=None):
        """Inicializa la ventana principal moderna.
        
        Args:
            sync_manager: Instancia de SyncManager para sincronización con la nube
        """
        super().__init__()

        self.setWindowTitle("Guardias de Patio - Sistema de Gestión")
        self.setMinimumSize(1280, 720)  # Resolución mínima validada

        # Abrir maximizado
        self.showMaximized()

        # Logo corporativo
        from utils.ui_helpers import get_corporate_icon
        self.setWindowIcon(get_corporate_icon())

        # Guardar sync_manager
        self.sync_manager = sync_manager

        # Crear sesión para widgets
        self.session = SessionLocal()

        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Barra superior
        self.top_bar = TopBar()
        main_layout.addWidget(self.top_bar)

        # Layout horizontal: Sidebar + Contenido
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Menú lateral
        self.sidebar = SidebarMenu()
        self.sidebar.section_changed.connect(self.on_section_changed)
        content_layout.addWidget(self.sidebar)

        # Stack de widgets (contenido principal)
        self.content_stack = QStackedWidget()
        content_layout.addWidget(self.content_stack)

        main_layout.addLayout(content_layout)
        self.setLayout(main_layout)

        # Crear widgets y configurar menú
        self._create_widgets()
        self._setup_menu()

        # Aplicar tema Fluent
        self.setStyleSheet(get_complete_fluent_stylesheet())

        # Conectar acciones de la barra superior
        self._connect_topbar_actions()

    def _create_widgets(self):
        """Crea todos los widgets de contenido."""
        # Diccionario para mapear IDs a widgets
        self.widgets = {}

        # Gestión
        self.widgets['profesores'] = ProfesorForm(self.session)
        self.widgets['zonas'] = ZonaForm(self.session)
        self.widgets['configuracion'] = ConfiguracionForm(self.session)

        # Guardias
        self.widgets['asignacion'] = AsignacionGuardiasForm(self.session, sync_manager=self.sync_manager)
        self.widgets['calendario'] = CalendarioGuardiasForm(self.session)
        self.widgets['vista_calendario'] = VistaCalendario(self.session)
        self.widgets['estadisticas'] = PanelEstadisticas(self.session)

        # Ausencias y Sustituciones
        self.widgets['ausencias'] = GestionarAusenciasForm(self.session)
        self.widgets['sustituciones'] = GestorSustituciones(self.session)

        # Herramientas
        self.widgets['importar_exportar'] = ImportExportForm(self.session)

        # Añadir todos los widgets al stack
        for widget in self.widgets.values():
            self.content_stack.addWidget(widget)

        # Conectar señales para actualización
        self._connect_signals()

    def _setup_menu(self):
        """Configura el menú lateral con categorías y items."""
        # Categoría: Gestión
        gestion_category = MenuCategory(
            "GESTIÓN",
            [
                MenuItem(
                    "profesores",
                    "Profesores",
                    "",
                    lambda: self.show_widget("profesores", ["Gestión", "Profesores"])
                ),
                MenuItem(
                    "zonas",
                    "Zonas",
                    "",
                    lambda: self.show_widget("zonas", ["Gestión", "Zonas"])
                ),
                MenuItem(
                    "configuracion",
                    "Configuración",
                    "",
                    lambda: self.show_widget("configuracion", ["Gestión", "Configuración"])
                ),
            ]
        )

        # Categoría: Guardias
        guardias_category = MenuCategory(
            "GUARDIAS",
            [
                MenuItem(
                    "asignacion",
                    "Asignación",
                    "",
                    lambda: self.show_widget("asignacion", ["Guardias", "Asignación"])
                ),
                MenuItem(
                    "calendario",
                    "Calendario",
                    "",
                    lambda: self.show_widget("calendario", ["Guardias", "Calendario"])
                ),
                MenuItem(
                    "vista_calendario",
                    "Vista Calendario",
                    "",
                    lambda: self.show_widget("vista_calendario", ["Guardias", "Vista Calendario"])
                ),
                MenuItem(
                    "estadisticas",
                    "Estadísticas",
                    "",
                    lambda: self.show_widget("estadisticas", ["Guardias", "Estadísticas"])
                ),
            ]
        )

        # Categoría: Personal
        personal_category = MenuCategory(
            "PERSONAL",
            [
                MenuItem(
                    "ausencias",
                    "Ausencias",
                    "",
                    lambda: self.show_widget("ausencias", ["Personal", "Ausencias"])
                ),
                MenuItem(
                    "sustituciones",
                    "Sustituciones",
                    "",
                    lambda: self.show_widget("sustituciones", ["Personal", "Sustituciones"])
                ),
            ]
        )

        # Categoría: Herramientas
        herramientas_category = MenuCategory(
            "HERRAMIENTAS",
            [
                MenuItem(
                    "importar_exportar",
                    "Importar/Exportar",
                    "",
                    lambda: self.show_widget("importar_exportar", ["Herramientas", "Importar/Exportar"])
                ),
                MenuItem(
                    "panel_estadisticas",
                    "Estadísticas",
                    "",
                    lambda: self.show_widget("panel_estadisticas", ["Herramientas", "Estadísticas"])
                ),
                MenuItem(
                    "observabilidad",
                    "Observabilidad",
                    "",
                    lambda: self.show_widget("observabilidad", ["Herramientas", "Observabilidad"])
                ),
            ]
        )

        # Añadir categorías al menú
        self.sidebar.add_category(gestion_category)
        self.sidebar.add_category(guardias_category)
        self.sidebar.add_category(personal_category)
        self.sidebar.add_category(herramientas_category)

        # Espaciador al final
        self.sidebar.add_spacer()

        # Seleccionar primera sección por defecto
        self.sidebar.set_active_item("profesores")
        self.show_widget("profesores", ["Gestión", "Profesores"])

    def show_widget(self, widget_id: str, breadcrumb: list[str]):
        """
        Muestra un widget y actualiza el breadcrumb.

        Args:
            widget_id: ID del widget a mostrar
            breadcrumb: Lista de items para el breadcrumb
        """
        if widget_id in self.widgets:
            widget = self.widgets[widget_id]
            self.content_stack.setCurrentWidget(widget)
            self.top_bar.set_breadcrumb_path(breadcrumb)

            # Refrescar widget si tiene método refrescar
            if hasattr(widget, 'refrescar'):
                widget.refrescar()

    def on_section_changed(self, section_id: str):
        """
        Callback cuando cambia la sección en el menú.

        Args:
            section_id: ID de la sección seleccionada
        """
        # El callback ya se maneja en los MenuItems
        pass

    def _connect_signals(self):
        """Conecta señales para actualización automática."""
        # Profesores
        prof_form = self.widgets['profesores']
        if hasattr(prof_form, 'datos_modificados'):
            prof_form.datos_modificados.connect(prof_form.cargar_profesores)

        # Zonas
        zona_form = self.widgets['zonas']
        if hasattr(zona_form, 'datos_modificados'):
            zona_form.datos_modificados.connect(zona_form.cargar_zonas)

        # Importar/Exportar
        import_form = self.widgets['importar_exportar']
        if hasattr(import_form, 'profesores_importados'):
            import_form.profesores_importados.connect(prof_form.cargar_profesores)
        if hasattr(import_form, 'zonas_importadas'):
            import_form.zonas_importadas.connect(zona_form.cargar_zonas)

    def _connect_topbar_actions(self):
        """Conecta las acciones de la barra superior."""
        # Botón de configuración
        self.top_bar.settings_btn.clicked.connect(
            lambda: self.show_widget("configuracion", ["Gestión", "Configuración"])
        )

        # Botón de ayuda (placeholder)
        self.top_bar.help_btn.clicked.connect(self._show_help)

    def _open_observability(self):
        """Abre el dashboard de observabilidad."""
        dashboard = ObservabilityDashboard(self)
        dashboard.exec()

    def _show_help(self):
        """Muestra ayuda (placeholder)."""
        from core.qt_imports import QMessageBox, Qt

        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("Ayuda")
        msg.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint |
            Qt.WindowType.WindowTitleHint
        )
        msg.setText(
            "Sistema de Gestión de Guardias de Patio\n\n"
            "Use el menú lateral para navegar entre las diferentes secciones.\n\n"
            "Para más información, consulte la documentación."
        )
        msg.exec()

    def closeEvent(self, event):
        """Cierra la sesión al cerrar la ventana."""
        self.session.close()
        event.accept()
