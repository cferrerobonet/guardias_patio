"""
Ventana principal de la aplicación.

Módulo que define la clase MainWindow de la aplicación de gestión de guardias de patio.
"""

from core.qt_imports import (
    QHBoxLayout,
    QKeySequence,
    QShortcut,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from database.db_manager import SessionLocal

from presentation.forms import (
    AsignacionGuardiasForm,
    ImportExportForm,
    ProfesorForm,
    ZonaForm,
)
from presentation.forms.ajustes_form import AjustesForm
from presentation.forms.conectividad_form import ConectividadForm
from presentation.forms.perfiles_usuario_form import PerfilesUsuarioForm
from presentation.widgets import (
    GestionarAusenciasForm,
    GestorSustituciones,
    PanelEstadisticas,
    SelectorCursoWidget,
    VistaCalendario,
)


class MainWindow(QWidget):
    """Ventana principal de la aplicación."""

    def __init__(self):
        """Inicializa la ventana principal."""
        super().__init__()
        self.setWindowTitle("Guardias de Patio - Sistema de Gestión")
        self.setMinimumSize(1200, 800)

        # Abrir en pantalla completa (maximizada) por defecto
        self.showMaximized()

        # Aplicar logo corporativo a la ventana principal
        from utils.ui_helpers import get_corporate_icon

        self.setWindowIcon(get_corporate_icon())

        self.layout = QVBoxLayout()

        # Crear sesión para widgets que la necesiten
        self.session = SessionLocal()

        # Barra superior con selector de curso
        barra_superior = QHBoxLayout()
        barra_superior.addStretch()

        self.selector_curso = SelectorCursoWidget(self.session)
        self.selector_curso.curso_cambiado.connect(self._on_curso_cambiado)
        barra_superior.addWidget(self.selector_curso)

        self.layout.addLayout(barra_superior)

        # Configurar atajos de teclado globales
        self._configurar_atajos_globales()

        # Pestañas para profesores y zonas
        self.tabs = QTabWidget()

        # Crear formularios y guardar referencias
        self.profesor_form = ProfesorForm(self.session)
        self.zona_form = ZonaForm(self.session)
        self.import_export_form = ImportExportForm(self.session)

        self.tabs.addTab(self.profesor_form, "👨‍🏫 Profesores")
        self.tabs.addTab(self.zona_form, "🏫 Zonas")
        self.tabs.addTab(AjustesForm(self.session), "⚙️ Ajustes")
        self.tabs.addTab(ConectividadForm(self.session), "🌐 Conectividad")
        self.tabs.addTab(PerfilesUsuarioForm(self.session), "👤 Perfiles de Usuario")
        self.tabs.addTab(
            AsignacionGuardiasForm(self.session),
            "🎯 Asignación de Guardias",
        )

        # Widgets refactorizados (Sprint 5)
        self.gestionar_ausencias = GestionarAusenciasForm(self.session)
        self.tabs.addTab(self.gestionar_ausencias, "🏥 Ausencias")

        # Calendario mejorado
        self.vista_calendario = VistaCalendario(self.session)
        self.tabs.addTab(self.vista_calendario, "📆 Calendario de Guardias")

        self.panel_estadisticas = PanelEstadisticas(self.session)
        self.tabs.addTab(self.panel_estadisticas, "📊 Estadísticas")

        self.gestor_sustituciones = GestorSustituciones(self.session)
        self.tabs.addTab(self.gestor_sustituciones, "🔄 Sustituciones")

        self.tabs.addTab(self.import_export_form, "💾 Importar / Exportar")

        # Conectar señales para actualización automática
        self._conectar_senales_actualizacion()

        self.layout.addWidget(self.tabs)

        self.setLayout(self.layout)

        # Conectar señal de cambio de pestaña para refrescar widgets
        self.tabs.currentChanged.connect(self.on_tab_changed)

    def _conectar_senales_actualizacion(self):
        """Conectar señales para actualización automática de listas."""
        # Cuando se modifican profesores, actualizar lista de profesores
        self.profesor_form.datos_modificados.connect(self.profesor_form.cargar_profesores)

        # Cuando se modifican zonas, actualizar lista de zonas
        self.zona_form.datos_modificados.connect(self.zona_form.cargar_zonas)

        # Cuando se importan profesores, actualizar lista de profesores
        self.import_export_form.profesores_importados.connect(self.profesor_form.cargar_profesores)

        # Cuando se importan zonas, actualizar lista de zonas
        self.import_export_form.zonas_importadas.connect(self.zona_form.cargar_zonas)

    def _configurar_atajos_globales(self):
        """Configurar atajos de teclado globales"""
        # Ctrl+Tab: Siguiente pestaña
        atajo_siguiente = QShortcut(QKeySequence("Ctrl+Tab"), self)
        atajo_siguiente.activated.connect(self._siguiente_pestana)

        # Ctrl+Shift+Tab: Pestaña anterior
        atajo_anterior = QShortcut(QKeySequence("Ctrl+Shift+Tab"), self)
        atajo_anterior.activated.connect(self._pestana_anterior)

        # Ctrl+Q: Salir
        atajo_salir = QShortcut(QKeySequence("Ctrl+Q"), self)
        atajo_salir.activated.connect(self.close)

    def _siguiente_pestana(self):
        """Cambiar a la siguiente pestaña"""
        index_actual = self.tabs.currentIndex()
        siguiente = (index_actual + 1) % self.tabs.count()
        self.tabs.setCurrentIndex(siguiente)

    def _pestana_anterior(self):
        """Cambiar a la pestaña anterior"""
        index_actual = self.tabs.currentIndex()
        anterior = (index_actual - 1) % self.tabs.count()
        self.tabs.setCurrentIndex(anterior)

    def on_tab_changed(self, index):
        """Refresca los widgets cuando se cambia de pestaña."""
        # Refrescar calendario si se muestra
        if self.tabs.widget(index) == self.vista_calendario:
            self.vista_calendario.refrescar()
        # Refrescar estadísticas si se muestran
        elif self.tabs.widget(index) == self.panel_estadisticas:
            self.panel_estadisticas.refrescar()
        # Refrescar sustituciones si se muestran
        elif self.tabs.widget(index) == self.gestor_sustituciones:
            self.gestor_sustituciones.refrescar()

    def _on_curso_cambiado(self, curso_id: int):
        """Callback cuando se cambia el curso activo."""
        # Refrescar todos los widgets que dependan del curso
        self.vista_calendario.refrescar()
        self.panel_estadisticas.refrescar()
        self.gestor_sustituciones.refrescar()

    def closeEvent(self, event):
        """Cierra la sesión al cerrar la ventana."""
        self.session.close()
        event.accept()
