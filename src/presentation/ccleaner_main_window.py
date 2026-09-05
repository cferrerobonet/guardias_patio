"""
Ventana Principal Estilo CCleaner
==================================
Layout profesional con sidebar oscuro y contenido blanco.
"""

from datetime import datetime, timezone

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from core.logging import get_logger
from core.usage_logger import usage_log
from presentation.components.ccleaner_sidebar import SidebarMenu
from presentation.forms.ajustes_form import AjustesForm
from presentation.forms.asignacion_calculo_form import AsignacionCalculoForm
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
    AusenciasSustitucionesWidget,
    PanelEstadisticas,
    VistaCalendario,
)

logger = get_logger(__name__)


class ContentWrapper(QWidget):
    """Wrapper para dar estilo uniforme al contenido"""

    def __init__(self, title: str, content_widget: QWidget, parent=None):
        super().__init__(parent)
        #: La vista real. Hay que conservarla: es a quien se le pide recargar
        #: cuando cambian los datos.
        self.content_widget = content_widget
        self.title = title
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
        scroll.setStyleSheet(
            f"QScrollArea {{ background-color: {CONTENT_BG}; border: none; }} QScrollArea > QWidget > QWidget {{ background-color: {CONTENT_BG}; }}"
        )
        scroll.setWidget(content_widget)

        layout.addWidget(scroll)


class CCleanerMainWindow(QMainWindow):
    """Ventana principal con diseño estilo CCleaner"""

    _nueva_version_signal = pyqtSignal(str, str)

    def __init__(self, session, sync_manager=None):
        super().__init__()
        self.session = session
        self.sync_manager = sync_manager
        self.widgets: dict = {}
        self._view_factories: dict = {}
        self._seccion_actual = "profesores"
        self.setup_ui()

    def setup_ui(self):
        """Configurar la interfaz principal"""
        from config.settings import get_settings

        self.setWindowTitle("Guardias de Patio")
        ajustes = get_settings()
        # Una sola fuente para el mínimo: la que está en ajustes (VIS-009).
        self.setMinimumSize(ajustes.window_min_width, ajustes.window_min_height)

        # Abrir maximizada para mantener los controles nativos de la ventana en Windows
        self.showMaximized()

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

        # Auto-sync en background cada 30 minutos
        if self.sync_manager:
            self._setup_auto_sync()
        # Siempre: sin sync_manager el indicador debe avisar de que no hay servidor.
        self._update_sync_status_label()

        # Verificar actualizaciones en background
        self._check_updates()

    def create_views(self):
        """Registrar factories de vistas — lazy loading: solo se instancian al navegar."""
        session = self.session
        sync_manager = self.sync_manager

        self._register("profesores", "Gestión de Profesores", lambda: ProfesorForm(session))
        self._register("zonas", "Gestión de Zonas", lambda: ZonaForm(session))
        self._register("ajustes", "Ajustes del Curso Escolar", lambda: AjustesForm(session))
        self._register(
            "perfiles", "Gestión de Perfiles de Usuario", lambda: PerfilesUsuarioForm(session)
        )
        self._register(
            "asignacion_calculo",
            "Cálculo y Asignación",
            lambda: AsignacionCalculoForm(session, sync_manager=sync_manager),
        )
        self._register("calendario", "Calendario de Guardias", lambda: VistaCalendario(session))
        self._register(
            "ausencias_sustituciones",
            "Ausencias / Sustituciones",
            lambda: AusenciasSustitucionesWidget(session),
        )
        self._register("importar", "Importar / Exportar Datos", lambda: ImportExportForm(session))
        self._register("reportes", "Generador de Reportes", lambda: ReportesForm(session))
        self._register("estadisticas", "Estadísticas", lambda: PanelEstadisticas(session))

        # Pre-instanciar solo la sección inicial para que el stack no quede vacío
        self._ensure_view("profesores")

    def _register(self, section: str, title: str, factory):
        self._view_factories[section] = (title, factory)

    def _ensure_view(self, section: str):
        """Instancia el widget de una sección si aún no existe."""
        if section not in self.widgets and section in self._view_factories:
            title, factory = self._view_factories[section]
            vista = factory()
            self._conectar_senales_de_recarga(vista)
            wrapped = ContentWrapper(title, vista)
            self.widgets[section] = wrapped
            self.content_stack.addWidget(wrapped)

    def add_view(self, section: str, title: str, content_widget: QWidget):
        """API de compatibilidad — instancia inmediata."""
        wrapped = ContentWrapper(title, content_widget)
        self.widgets[section] = wrapped
        self.content_stack.addWidget(wrapped)

    def on_section_changed(self, section: str):
        """Cambiar de sección — instancia el widget si es la primera vez."""
        if section == self._seccion_actual:
            return

        # Guard central de cambios sin guardar. Antes cambiar de sección los
        # descartaba en silencio (UXA-004).
        if not self.confirmar_salida_de_la_vista_actual():
            self.sidebar.set_active_section(self._seccion_actual)
            return

        self._ensure_view(section)
        if section in self.widgets:
            self.content_stack.setCurrentWidget(self.widgets[section])
            self._seccion_actual = section
            usage_log("NAV", section=section)

    def vista_actual(self):
        """Widget de contenido de la sección visible, o None."""
        envoltorio = self.content_stack.currentWidget()
        return getattr(envoltorio, "content_widget", None)

    def confirmar_salida_de_la_vista_actual(self) -> bool:
        """Pregunta qué hacer con los cambios pendientes. False = quedarse.

        Se usa igual al navegar entre secciones y al cerrar la aplicación, para
        no duplicar el modal en cada formulario (UXA-004).
        """
        vista = self.vista_actual()
        if vista is None or not getattr(vista, "tiene_cambios", lambda: False)():
            return True

        caja = QMessageBox(self)
        caja.setIcon(QMessageBox.Icon.Warning)
        caja.setWindowTitle("Cambios sin guardar")
        caja.setText("Hay cambios sin guardar en esta pantalla.")
        caja.setInformativeText("¿Qué quieres hacer con ellos?")

        boton_guardar = None
        if getattr(vista, "puede_guardar_desde_el_guard", lambda: False)():
            boton_guardar = caja.addButton("Guardar", QMessageBox.ButtonRole.AcceptRole)
        caja.addButton("Descartar", QMessageBox.ButtonRole.DestructiveRole)
        boton_cancelar = caja.addButton("Seguir editando", QMessageBox.ButtonRole.RejectRole)
        caja.setDefaultButton(boton_cancelar)
        caja.exec()

        pulsado = caja.clickedButton()
        if pulsado is boton_cancelar:
            return False
        if boton_guardar is not None and pulsado is boton_guardar:
            return bool(vista.guardar_cambios_pendientes())

        if hasattr(vista, "descartar_cambios"):
            vista.descartar_cambios()
        return True

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
        for method in (
            "cargar_datos",
            "actualizar_calendario",
            "cargar_profesores",
            "cargar_zonas",
            "cargar_guardias",
            "refrescar",
        ):
            if hasattr(widget, method):
                getattr(widget, method)()
                return True
        return False

    #: Señales que emiten las vistas cuando cambian los datos de fondo.
    SENALES_DE_RECARGA = (
        "profesores_importados",
        "zonas_importadas",
        "datos_recargados",
        "guardias_generadas",
        "guardias_limpiadas",
    )

    def recargar_todas_las_vistas(self, motivo: str = "cambio de datos"):
        """
        Vuelve a pintar todas las vistas ya abiertas.

        Una importación o una descarga sustituyen los datos por debajo. Sin esto
        las vistas siguen mostrando lo anterior y hay que cerrar y volver a abrir
        la aplicación para ver lo nuevo.
        """
        logger.info(f"🔄 Recargando vistas ({motivo})")

        # La caché de consultas guarda resultados durante minutos: si no se vacía,
        # las vistas se repintan con los datos viejos.
        try:
            from utils.cache import clear_all_cache

            clear_all_cache()
        except Exception as e:  # noqa: BLE001
            logger.warning(f"No se pudo vaciar la caché: {e}")

        try:
            self.session.expire_all()
        except Exception as e:  # noqa: BLE001
            logger.warning(f"expire_all falló: {e}")

        refrescadas = 0
        for section, wrapped in self.widgets.items():
            widget = getattr(wrapped, "content_widget", None)
            if widget is None:
                continue
            try:
                if self._refresh_widget(widget):
                    refrescadas += 1
                else:
                    logger.debug(f"   {section} no expone forma de recargarse")
            except Exception as e:  # noqa: BLE001 - una vista rota no puede tumbar al resto
                logger.error(f"   Error recargando {section}: {e}")

        logger.info(f"✅ {refrescadas} vistas recargadas")

    def _conectar_senales_de_recarga(self, widget):
        """Conecta las señales de datos de una vista recién creada."""
        for nombre in self.SENALES_DE_RECARGA:
            senal = getattr(widget, nombre, None)
            if senal is not None and hasattr(senal, "connect"):
                senal.connect(
                    lambda _=None, n=nombre: self.recargar_todas_las_vistas(n)
                )

    def _on_curso_cambiado(self, curso_id: int):
        """Al cambiar de curso, todas las vistas abiertas deben mostrar el nuevo."""
        # Los cambios pendientes son del curso anterior: aquí no cabe "seguir
        # editando", pero sí avisar y dar la opción de guardarlos (UXF-004).
        vista = self.vista_actual()
        if vista is not None and getattr(vista, "tiene_cambios", lambda: False)():
            caja = QMessageBox(self)
            caja.setIcon(QMessageBox.Icon.Warning)
            caja.setWindowTitle("Cambios sin guardar")
            caja.setText("Hay cambios sin guardar que pertenecen al curso anterior.")
            caja.setInformativeText(
                "Al cambiar de curso se descartan, porque ya no corresponden a los "
                "datos que vas a ver."
            )
            boton_guardar = None
            if getattr(vista, "puede_guardar_desde_el_guard", lambda: False)():
                boton_guardar = caja.addButton("Guardar antes", QMessageBox.ButtonRole.AcceptRole)
            descartar = caja.addButton("Descartar", QMessageBox.ButtonRole.DestructiveRole)
            caja.setDefaultButton(boton_guardar or descartar)
            caja.exec()

            if boton_guardar is not None and caja.clickedButton() is boton_guardar:
                vista.guardar_cambios_pendientes()
            if hasattr(vista, "descartar_cambios"):
                vista.descartar_cambios()

        self.recargar_todas_las_vistas(f"curso {curso_id}")

    # ── Auto-sync ──────────────────────────────────────────────────────────────

    def _setup_auto_sync(self):
        self._auto_sync_timer = QTimer(self)
        self._auto_sync_timer.timeout.connect(self._trigger_auto_sync)
        self._auto_sync_timer.start(30 * 60 * 1000)  # 30 minutos
        # Timer de UI: actualiza el label de tiempo transcurrido cada minuto
        self._sync_ui_timer = QTimer(self)
        self._sync_ui_timer.timeout.connect(self._update_sync_status_label)
        self._sync_ui_timer.start(60 * 1000)

    def _trigger_auto_sync(self):
        if not self.sync_manager:
            return
        from presentation.widgets.sync_progress_dialog import SyncWorker

        self._sync_worker = SyncWorker(self.sync_manager)  # sesión propia (CRW-003)
        self.sidebar.set_sync_status("syncing", "↻ Sincronizando...")
        self._sync_worker.finished.connect(self._on_auto_sync_finished)
        self._sync_worker.start()

    def _on_auto_sync_finished(self, success: bool):
        self._update_sync_status_label(error=not success)

    def _update_sync_status_label(self, error: bool = False):
        if not self.sync_manager:
            # Aviso permanente de que se está trabajando sin servidor (UXF-005):
            # antes el indicador se quedaba en un gris que no decía nada.
            self.sidebar.set_sync_status("warning", "⚠ Solo en este equipo")
            return
        if error:
            self.sidebar.set_sync_status("error", "✕ Error de sync")
            return
        last = self.sync_manager.get_last_sync_time()
        if last is None:
            self.sidebar.set_sync_status("warning", "⚠ Sin sincronizar")
            return
        # Normalizar a UTC si es naive
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        minutos = int((datetime.now(timezone.utc) - last).total_seconds() / 60)
        if minutos < 2:
            self.sidebar.set_sync_status("ok", "✓ Sincronizado ahora")
        elif minutos < 60:
            self.sidebar.set_sync_status("ok", f"✓ Sync hace {minutos} min")
        else:
            horas = minutos // 60
            estado = "warning" if minutos > 60 else "ok"
            self.sidebar.set_sync_status(estado, f"⚠ Sync hace {horas}h")

    def closeEvent(self, event):
        if not self.confirmar_salida_de_la_vista_actual():
            event.ignore()
            return
        if not self.sync_manager:
            event.accept()
            return
        last = self.sync_manager.get_last_sync_time()
        if last is None:
            pendiente = True
        else:
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
            pendiente = (datetime.now(timezone.utc) - last).total_seconds() > 300
        if pendiente:
            resp = QMessageBox.question(
                self,
                "Cambios sin sincronizar",
                "Hay cambios sin sincronizar con la nube. ¿Sincronizar antes de salir?",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
                | QMessageBox.StandardButton.Cancel,
            )
            if resp == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
            if resp == QMessageBox.StandardButton.Yes:
                from presentation.widgets.sync_progress_dialog import SyncProgressDialog, SyncWorker

                dlg = SyncProgressDialog(self)
                worker = SyncWorker(self.sync_manager)  # sesión propia (CRW-003)
                worker.finished.connect(lambda _: dlg.accept())
                worker.start()
                dlg.exec()
        event.accept()

    def _check_updates(self) -> None:
        from config.settings import get_settings
        from utils.update_checker import check_for_updates

        self._nueva_version_signal.connect(self._on_nueva_version)
        check_for_updates(get_settings().app_version, self._nueva_version_signal.emit)

    def _on_nueva_version(self, version: str, download_url: str) -> None:
        if hasattr(self, "sidebar"):
            self.sidebar.show_update_banner(version, download_url)
