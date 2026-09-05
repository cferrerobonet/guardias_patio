"""
Sidebar estilo CCleaner
=======================
Menú lateral oscuro con diseño profesional.
"""

from PyQt6.QtCore import QSettings, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.logging import get_logger
from core.paths import get_data_directory
from presentation.themes.ccleaner_theme import (
    SIDEBAR_BG,
    get_sidebar_style,
)
from utils.icon_manager import get_icon

logger = get_logger(__name__)

_SIDEBAR_EXPANDED = 260
_SIDEBAR_COLLAPSED = 56


class SidebarMenu(QWidget):
    """Menú lateral estilo CCleaner con categorías"""

    section_changed = pyqtSignal(str)

    def __init__(self, parent=None, session=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.active_button = None
        self.logo_label = None
        self.session = session
        self._collapsed = False
        self._menu_items: list[tuple[QPushButton, str]] = []
        self._category_labels: list[QLabel] = []
        self._category_separators: list[QFrame] = []
        settings = QSettings("GuardiasPatio", "Sidebar")
        self._collapsed = settings.value("collapsed", False, type=bool)
        self.setup_ui()

    def setup_ui(self):
        """Configurar la interfaz del sidebar"""
        self.setMinimumWidth(_SIDEBAR_COLLAPSED)
        self.setMaximumWidth(_SIDEBAR_EXPANDED)
        self._apply_width()

        self.setStyleSheet(get_sidebar_style())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        from PyQt6.QtGui import QKeySequence, QShortcut
        from PyQt6.QtWidgets import QHBoxLayout as _QHBoxLayout

        shortcut = QShortcut(QKeySequence("Ctrl+B"), self)
        shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        shortcut.activated.connect(self.toggle_collapse)

        # ========== SECCIÓN SUPERIOR: LOGO ==========
        logo_section = QWidget()
        logo_section.setStyleSheet("""
            QWidget {
                background-color: #E8E8E8;
                border-bottom: 1px solid rgba(0, 0, 0, 0.1);
            }
        """)
        logo_section_layout = QVBoxLayout(logo_section)
        logo_section_layout.setContentsMargins(12, 6, 12, 10)
        logo_section_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_section_layout.setSpacing(8)

        # Fila superior: botón de colapso alineado a la derecha
        top_row = _QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.addStretch()
        self._toggle_btn = QPushButton("◀")
        self._toggle_btn.setFixedSize(24, 24)
        self._toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_btn.setToolTip("Colapsar/expandir sidebar (Ctrl+B)")
        self._toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0,0,0,0.08);
                color: #555;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                padding: 2px;
            }
            QPushButton:hover { background-color: rgba(0,0,0,0.15); }
        """)
        self._toggle_btn.clicked.connect(self.toggle_collapse)
        top_row.addWidget(self._toggle_btn)
        logo_section_layout.addLayout(top_row)

        # ── Logo ──────────────────────────────────────────────────────────
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setMinimumSize(60, 60)
        self.logo_label.setMaximumSize(100, 100)
        self.logo_label.setScaledContents(True)

        self.update_logo()

        logo_section_layout.addWidget(self.logo_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # ========== SELECTOR DE CURSO (centrado en zona clara, sin etiqueta) ==========
        if self.session:
            from presentation.widgets import SelectorCursoWidget

            self.selector_curso = SelectorCursoWidget(self.session)
            self.selector_curso.setMaximumWidth(230)
            self.selector_curso.setStyleSheet("""
                QComboBox {
                    background-color: white;
                    color: #2c3e50;
                    border: 2px solid #3498db;
                    border-radius: 5px;
                    padding: 8px 10px;
                    font-size: 13px;
                    font-weight: bold;
                }
                QComboBox:hover {
                    background-color: #f8f9fa;
                    border: 2px solid #2980b9;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 25px;
                }
                QComboBox::down-arrow {
                    image: none;
                    border-left: 5px solid transparent;
                    border-right: 5px solid transparent;
                    border-top: 6px solid #3498db;
                    margin-right: 8px;
                }
                QComboBox QAbstractItemView {
                    background-color: white;
                    color: #2c3e50;
                    selection-background-color: #3498db;
                    selection-color: white;
                    border: 2px solid #3498db;
                    outline: none;
                }
            """)
            logo_section_layout.addWidget(
                self.selector_curso, alignment=Qt.AlignmentFlag.AlignCenter
            )

        layout.addWidget(logo_section)

        # ========== SECCIÓN INFERIOR: MENÚ ==========
        # Área de scroll para los menús
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet(f"background-color: {SIDEBAR_BG}; border: none;")

        # Widget contenedor del menú (comprimido para que quepan todos los items)
        menu_widget = QWidget()
        menu_layout = QVBoxLayout(menu_widget)
        menu_layout.setContentsMargins(0, 4, 0, 4)
        menu_layout.setSpacing(0)

        # ========== GESTIÓN ==========
        self.add_category(menu_layout, "GESTIÓN")
        self.add_menu_item(menu_layout, "profesores", "Profesores", "profesores", "account-group")
        self.add_menu_item(menu_layout, "zonas", "Zonas", "zonas", "map-marker")
        self.add_menu_item(menu_layout, "ajustes", "Ajustes", "ajustes", "cog")
        self.add_menu_item(menu_layout, "perfiles", "Perfiles de Usuario", "perfiles", "account")

        menu_layout.addSpacing(4)

        # ========== GUARDIAS ==========
        self.add_category(menu_layout, "GUARDIAS")
        self.add_menu_item(
            menu_layout,
            "asignacion_calculo",
            "Cálculo y Asignación",
            "asignacion_calculo",
            "chart-line",
        )
        self.add_menu_item(menu_layout, "calendario", "Calendario", "calendario", "calendar")

        menu_layout.addSpacing(4)

        # ========== PERSONAL ==========
        self.add_category(menu_layout, "PERSONAL")
        self.add_menu_item(
            menu_layout,
            "ausencias_sustituciones",
            "Ausencias/Sustituciones",
            "ausencias_sustituciones",
            "account-switch",
        )

        menu_layout.addSpacing(4)

        # ========== HERRAMIENTAS ==========
        self.add_category(menu_layout, "HERRAMIENTAS")
        self.add_menu_item(
            menu_layout, "importar", "Importar/Exportar", "importar", "database-import-export"
        )
        self.add_menu_item(menu_layout, "reportes", "Reportes", "reportes", "file-chart")
        self.add_menu_item(menu_layout, "estadisticas", "Estadísticas", "estadisticas", "chart-bar")

        # Espaciador flexible antes de la información de la app
        menu_layout.addStretch()

        # ========== INFORMACIÓN DE LA APP ==========
        self.add_app_info_section(menu_layout)

        scroll.setWidget(menu_widget)
        layout.addWidget(scroll)

        # Aplicar estado inicial si estaba colapsado
        if self._collapsed:
            self._collapsed = False
            self.toggle_collapse()

    def update_logo(self):
        """Actualiza el logo mostrado (corporativo o por defecto)"""
        if self.logo_label is None:
            return

        # Buscar logo corporativo del usuario actual
        try:
            from PyQt6.QtGui import QPixmap

            from database.db_manager import get_current_user_id

            current_user = get_current_user_id()
            logo_path = get_data_directory() / "imagenes" / f"{current_user}.png"

            if logo_path.exists():
                # Cargar logo corporativo sin borde (fondo claro ya lo tiene la sección)
                pixmap = QPixmap(str(logo_path))
                if not pixmap.isNull():
                    self.logo_label.setPixmap(pixmap)
                    self.logo_label.setStyleSheet("""
                        QLabel {
                            background-color: transparent;
                            border: none;
                            padding: 0px;
                        }
                    """)
                    return
        except (ValueError, TypeError, OSError) as e:
            logger.warning(f"Error al cargar logo corporativo: {e}")

        # Si no hay logo corporativo, usar icono por defecto (school.svg)
        # En este caso usamos color oscuro porque el fondo es claro
        icon = get_icon("school", "#3a4149", 100)
        pixmap = icon.pixmap(100, 100)
        self.logo_label.setPixmap(pixmap)
        self.logo_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                border: none;
            }
        """)

    def add_category(self, layout: QVBoxLayout, title: str):
        """Añadir etiqueta de categoría"""
        label = QLabel(title)
        label.setObjectName("categoryLabel")
        label.setStyleSheet("""
            QLabel#categoryLabel {
                color: rgba(255, 255, 255, 0.95);
                font-size: 12px;
                font-weight: 700;
                letter-spacing: 1.5px;
                text-transform: uppercase;
                padding: 12px 20px 6px 20px;
                background-color: transparent;
            }
        """)
        layout.addWidget(label)
        self._category_labels.append(label)

        separator = QFrame()
        separator.setObjectName("separator")
        separator.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.2);
                max-height: 1px;
                margin: 0px 16px 8px 16px;
            }
        """)
        layout.addWidget(separator)
        self._category_separators.append(separator)

    def add_menu_item(
        self, layout: QVBoxLayout, object_name: str, text: str, section: str, icon_name: str = None
    ):
        """Añadir botón de menú con icono SVG"""
        btn = QPushButton(f" {text}")  # Espacio para separar icono del texto
        btn.setObjectName(object_name)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setProperty("section", section)
        btn.setProperty("active", "false")
        btn.setMinimumHeight(38)  # Altura moderada

        # Añadir icono si se proporciona
        if icon_name:
            icon = get_icon(icon_name, "white", 20)  # Iconos de 20px
            btn.setIcon(icon)
            from PyQt6.QtCore import QSize

            btn.setIconSize(QSize(20, 20))  # Tamaño fijo de 20x20

        btn.setStyleSheet("""
            QPushButton {
                color: rgba(255, 255, 255, 0.95);
                background-color: transparent;
                text-align: left;
                padding: 10px 28px;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.12);
                color: white;
            }
            QPushButton[active="true"] {
                background-color: #0E5FA8;
                color: white;
                font-weight: 600;
            }
            QPushButton[active="true"]:hover {
                background-color: #0C5291;
            }
        """)
        btn.clicked.connect(lambda: self.on_menu_clicked(btn, section))
        layout.addWidget(btn)
        self._menu_items.append((btn, f" {text}"))

    def on_menu_clicked(self, button: QPushButton, section: str):
        """Manejar clic en un elemento del menú"""
        # Desactivar el botón anterior
        if self.active_button:
            self.active_button.setProperty("active", "false")
            self.active_button.style().unpolish(self.active_button)
            self.active_button.style().polish(self.active_button)

        # Activar el nuevo botón
        button.setProperty("active", "true")
        button.style().unpolish(button)
        button.style().polish(button)
        self.active_button = button

        # Emitir señal
        self.section_changed.emit(section)

    def add_app_info_section(self, layout: QVBoxLayout):
        """Añadir sección de información de la aplicación en la parte inferior"""
        from utils.constants import APP_VERSION

        # Contenedor de información
        info_container = QWidget()
        info_container.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 0.15);
                border-top: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        info_layout = QVBoxLayout(info_container)
        info_layout.setContentsMargins(16, 10, 16, 10)
        info_layout.setSpacing(6)

        # Estado de sincronización
        self.sync_status_label = QLabel("— Sin conexión sync")
        self.sync_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sync_status_label.setWordWrap(True)
        self.sync_status_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.6);
                font-size: 12px;
                background-color: transparent;
                border: none;
            }
        """)
        info_layout.addWidget(self.sync_status_label)

        # Banner de actualización disponible (oculto por defecto)
        self._update_banner = QPushButton("🆕 Actualización disponible")
        self._update_banner.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_banner.setStyleSheet("""
            QPushButton {
                color: #1A237E;
                background-color: #FFF176;
                border: 1px solid #F9A825;
                border-radius: 4px;
                padding: 5px 8px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FDD835;
            }
        """)
        self._update_banner.hide()
        self._update_banner.clicked.connect(self._on_update_banner_clicked)
        info_layout.addWidget(self._update_banner)

        # Versión - centrada
        version_label = QLabel(f"📦 v{APP_VERSION}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.85);
                font-size: 12px;
                font-weight: bold;
                background-color: transparent;
                border: none;
            }
        """)
        info_layout.addWidget(version_label)

        # Botón "Acerca de"
        btn_acerca = QPushButton("ℹ️ Acerca de...")
        btn_acerca.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_acerca.setStyleSheet("""
            QPushButton {
                color: rgba(255, 255, 255, 0.7);
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
            }
        """)
        btn_acerca.clicked.connect(self._show_about_dialog)
        info_layout.addWidget(btn_acerca)

        layout.addWidget(info_container)

    def set_sync_status(self, estado: str, texto: str):
        """Actualiza el indicador de estado de sync en la sidebar.

        estado: 'ok' | 'warning' | 'error' | 'syncing'
        """
        if not hasattr(self, "sync_status_label"):
            return
        colores = {
            "ok": "rgba(100,220,100,0.8)",
            "warning": "rgba(255,200,50,0.8)",
            "error": "rgba(255,80,80,0.8)",
            "syncing": "rgba(100,180,255,0.8)",
        }
        color = colores.get(estado, "rgba(255,255,255,0.6)")
        self.sync_status_label.setText(texto)
        self.sync_status_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 12px;
                background-color: transparent;
                border: none;
            }}
        """)

    def show_update_banner(self, nueva_version: str, download_url: str = "") -> None:
        if not hasattr(self, "_update_banner"):
            return
        self._update_nueva_version = nueva_version
        self._update_download_url = download_url
        self._update_banner.setText(f"🆕 v{nueva_version} disponible")
        self._update_banner.show()

    def _on_update_banner_clicked(self) -> None:
        url = getattr(self, "_update_download_url", "")
        if url:
            self._descargar_e_instalar(url)
        else:
            import webbrowser
            webbrowser.open("https://github.com/cferrerobonet/guardias_patio/releases/latest")

    def _descargar_e_instalar(self, url: str) -> None:
        import subprocess
        import tempfile
        import urllib.request
        from pathlib import Path

        from PyQt6.QtCore import QThread
        from PyQt6.QtCore import pyqtSignal as Signal
        from PyQt6.QtWidgets import QMessageBox, QProgressDialog

        version = getattr(self, "_update_nueva_version", "")
        nombre = url.split("/")[-1]
        destino = Path(tempfile.gettempdir()) / nombre

        progreso = QProgressDialog(
            f"Descargando Guardias de Patio v{version}…", "Cancelar", 0, 100, self
        )
        progreso.setWindowTitle("Actualización")
        progreso.setMinimumDuration(0)
        progreso.setValue(0)

        cancelado = [False]

        def _on_cancel():
            cancelado[0] = True

        progreso.canceled.connect(_on_cancel)

        class _Descargador(QThread):
            progreso_signal = Signal(int)
            error_signal = Signal(str)
            listo_signal = Signal(str)

            def __init__(self, url, destino):
                super().__init__()
                self._url = url
                self._destino = destino

            def run(self):
                try:
                    def _reporthook(count, block_size, total):
                        if total > 0:
                            pct = min(int(count * block_size * 100 / total), 100)
                            self.progreso_signal.emit(pct)

                    urllib.request.urlretrieve(self._url, self._destino, _reporthook)
                    self.listo_signal.emit(str(self._destino))
                except Exception as e:
                    self.error_signal.emit(str(e))

        hilo = _Descargador(url, destino)
        hilo.progreso_signal.connect(lambda v: progreso.setValue(v) if not cancelado[0] else hilo.terminate())
        hilo.listo_signal.connect(lambda path: (progreso.close(), subprocess.run(["open", path])))
        hilo.error_signal.connect(lambda err: (
            progreso.close(),
            QMessageBox.critical(self, "Error de descarga", f"No se pudo descargar la actualización:\n{err}"),
        ))
        hilo.start()

    def _show_about_dialog(self):
        """Mostrar el diálogo Acerca de"""
        from presentation.dialogs.dialogo_acerca_de import DialogoAcercaDe

        dialogo = DialogoAcercaDe(self, session=self.session)
        dialogo.exec()

    def _apply_width(self):
        w = _SIDEBAR_COLLAPSED if self._collapsed else _SIDEBAR_EXPANDED
        self.setMinimumWidth(w)
        self.setMaximumWidth(w)
        self.resize(w, self.height())
        self.updateGeometry()
        if self.parent() and self.parent().layout():
            self.parent().layout().invalidate()
            self.parent().layout().activate()

    def toggle_collapse(self):
        self._collapsed = not self._collapsed
        self._apply_width()

        visible = not self._collapsed
        for label in self._category_labels:
            label.setVisible(visible)
        for sep in self._category_separators:
            sep.setVisible(visible)

        for btn, original_text in self._menu_items:
            btn.setText(original_text if visible else "")
            btn.setToolTip("" if visible else original_text.strip())

        self._toggle_btn.setText("◀" if visible else "▶")

        QSettings("GuardiasPatio", "Sidebar").setValue("collapsed", self._collapsed)

        if hasattr(self, "logo_label") and self.logo_label:
            self.logo_label.setVisible(visible)
        if hasattr(self, "selector_curso"):
            self.selector_curso.setVisible(visible)

    def set_active_section(self, section: str):
        """Establecer sección activa programáticamente"""
        for btn in self.findChildren(QPushButton):
            if btn.property("section") == section:
                self.on_menu_clicked(btn, section)
                break
