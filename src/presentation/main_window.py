"""
Ventana principal de la aplicación.

Módulo que define la clase MainWindow de la aplicación de gestión de guardias de patio.
"""

from core.qt_imports import (
    QHBoxLayout,
    QKeySequence,
    QPushButton,
    QShortcut,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from database.db_manager import SessionLocal

from presentation.forms import (
    AsignacionGuardiasForm,
    CalendarioGuardiasForm,
    ConfiguracionForm,
    ImportExportForm,
    ProfesorForm,
    ZonaForm,
)
from presentation.widgets import (
    GestionarAusenciasForm,
    GestorSustituciones,
    PanelEstadisticas,
    VistaCalendario,
)
from presentation.widgets.observability_dashboard import ObservabilityDashboard


class MainWindow(QWidget):
    """Ventana principal de la aplicación."""

    def __init__(self):
        """Inicializa la ventana principal."""
        super().__init__()
        self.setWindowTitle("Guardias de Patio - Sistema de Gestión")
        self.setMinimumSize(1200, 800)

        # Aplicar logo corporativo a la ventana principal
        from utils.ui_helpers import get_corporate_icon
        self.setWindowIcon(get_corporate_icon())

        self.layout = QVBoxLayout()

        # Crear sesión para widgets que la necesiten
        self.session = SessionLocal()

        # Configurar atajos de teclado globales
        self._configurar_atajos_globales()

        # Pestañas para profesores y zonas
        self.tabs = QTabWidget()
        self.tabs.addTab(ProfesorForm(self.session), "👨‍🏫 Profesores")
        self.tabs.addTab(ZonaForm(self.session), "🏫 Zonas")
        self.tabs.addTab(ConfiguracionForm(self.session), "⚙️ Configuración")
        self.tabs.addTab(
            AsignacionGuardiasForm(self.session),
            "🎯 Asignación de Guardias",
        )

        # Widgets refactorizados (Sprint 5)
        self.vista_calendario = VistaCalendario(self.session)
        self.gestionar_ausencias = GestionarAusenciasForm(self.session)
        self.tabs.addTab(self.gestionar_ausencias, "🏥 Ausencias")
        self.tabs.addTab(self.vista_calendario, "📅 Vista Calendario")

        self.panel_estadisticas = PanelEstadisticas(self.session)
        self.tabs.addTab(self.panel_estadisticas, "📊 Estadísticas")

        self.gestor_sustituciones = GestorSustituciones(self.session)
        self.tabs.addTab(self.gestor_sustituciones, "🔄 Sustituciones")

        self.tabs.addTab(CalendarioGuardiasForm(self.session), "📆 Calendario")
        self.tabs.addTab(ImportExportForm(self.session), "💾 Importar / Exportar")

        self.layout.addWidget(self.tabs)

        # Botón para abrir Dashboard de Observabilidad (Sprint 7)
        btn_observability = QPushButton("📊 Observabilidad")
        btn_observability.setToolTip("Ver métricas, health checks y performance del sistema")
        btn_observability.clicked.connect(self._abrir_observabilidad)
        btn_observability.setMaximumWidth(200)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_observability)
        self.layout.addLayout(btn_layout)

        self.setLayout(self.layout)

        # Conectar señal de cambio de pestaña para refrescar widgets
        self.tabs.currentChanged.connect(self.on_tab_changed)

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

    def _abrir_observabilidad(self):
        """Abre el dashboard de observabilidad."""
        dashboard = ObservabilityDashboard(self)
        dashboard.exec()

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

    def closeEvent(self, event):
        """Cierra la sesión al cerrar la ventana."""
        self.session.close()
        event.accept()
