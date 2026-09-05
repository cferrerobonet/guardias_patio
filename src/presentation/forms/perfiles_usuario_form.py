"""
Formulario Profesional de Gestión de Perfiles de Usuario - CRUD Completo.

CRUD Profesional con:
- Tabla moderna con iconos y colores
- Modales de confirmación elegantes
- Botones con iconos solo (compactos)
- Validaciones completas con Use Cases
- Gestión de logos corporativos
- Cambio de contraseña seguro (solo perfil actual)
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)
from sqlalchemy.exc import SQLAlchemyError

from application.use_cases.perfil import (
    ActualizarLogoUseCase,
    ActualizarPerfilUseCase,
    CambiarPasswordUseCase,
    CrearPerfilUseCase,
    EliminarPerfilUseCase,
    ListarPerfilesUseCase,
)
from core.exceptions import NotFoundError, ValidationError
from database.db_manager import get_current_user_id
from presentation.dialogs.modales_perfil import (
    DialogoCambiarPasswordProfesional,
    DialogoCrearPerfilProfesional,
    DialogoEditarPerfilProfesional,
)
from presentation.forms.base_form import BaseForm
from presentation.theme import legacy_styles as styles
from presentation.widgets.toast_notification import ToastNotification
from sync.sync_manager import UserAuth
from utils.icons import icon_for_button


class PerfilesUsuarioForm(BaseForm):
    """
    CRUD Profesional de Perfiles de Usuario.

    Funcionalidades:
    - Listar todos los perfiles (tabla moderna)
    - Crear nuevos perfiles con BD automática
    - Editar email de perfiles
    - Eliminar perfiles con confirmación
    - Cambiar contraseña (solo perfil actual)
    - Gestionar logos corporativos
    - Indicadores visuales (BD, Logo, Activo)
    """

    def __init__(self, session, parent=None):
        """
        Inicializa el formulario.

        Args:
            session: Sesión de SQLAlchemy (no se usa, pero se mantiene para compatibilidad)
            parent: Widget padre
        """
        super().__init__(session, parent)

        self.user_auth = UserAuth()
        self.current_username = get_current_user_id()

        # Inicializar Use Cases
        self._init_use_cases()

        # Configurar UI
        self._setup_ui()

        # Cargar datos
        self.refrescar()

    def _init_use_cases(self):
        """Inicializa los use cases."""
        self.uc_listar = ListarPerfilesUseCase(self.user_auth)
        self.uc_crear = CrearPerfilUseCase(self.user_auth)
        self.uc_actualizar = ActualizarPerfilUseCase(self.user_auth)
        self.uc_eliminar = EliminarPerfilUseCase(self.user_auth)
        self.uc_cambiar_password = CambiarPasswordUseCase(self.user_auth)
        self.uc_actualizar_logo = ActualizarLogoUseCase(self.user_auth)

    def _setup_ui(self):
        """Configura la interfaz profesional."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # ===== DESCRIPCIÓN =====
        descripcion = QLabel(
            "Administra todos los perfiles del sistema. Cada perfil tiene su propia "
            "base de datos y configuración independiente. Solo puedes cambiar la contraseña "
            "de tu propio perfil."
        )
        descripcion.setWordWrap(True)
        descripcion.setObjectName("formDescription")
        layout.addWidget(descripcion)

        # ===== BARRA DE ACCIONES =====
        acciones_layout = QHBoxLayout()
        acciones_layout.setSpacing(8)

        # Espaciador al inicio para empujar botones a la derecha
        acciones_layout.addStretch()

        # Botón Crear (verde)
        self.btn_crear = QPushButton("Crear")
        self.btn_crear.setAccessibleName("Botón crear nuevo perfil")
        self.btn_crear.setIcon(icon_for_button("add"))
        self.btn_crear.setStyleSheet(
            styles.STYLE_BUTTON_SUCCESS + "font-size: 12px; padding: 8px 16px; font-weight: bold;"
        )
        self.btn_crear.setToolTip("Crear nuevo perfil con su base de datos")
        self.btn_crear.clicked.connect(self._on_crear)
        acciones_layout.addWidget(self.btn_crear)

        # Botón Editar (azul)
        self.btn_editar = QPushButton("Editar")
        self.btn_editar.setAccessibleName("Botón editar perfil seleccionado")
        self.btn_editar.setIcon(icon_for_button("edit"))
        self.btn_editar.setStyleSheet(
            styles.STYLE_BUTTON_PRIMARY + "font-size: 12px; padding: 8px 16px;"
        )
        self.btn_editar.setToolTip("Editar email del perfil seleccionado")
        self.btn_editar.setEnabled(False)
        self.btn_editar.clicked.connect(self._on_editar)
        acciones_layout.addWidget(self.btn_editar)

        # Botón Eliminar (rojo)
        self.btn_eliminar = QPushButton("Eliminar")
        self.btn_eliminar.setAccessibleName("Botón eliminar perfil")
        self.btn_eliminar.setIcon(icon_for_button("delete"))
        self.btn_eliminar.setStyleSheet(
            styles.STYLE_BUTTON_DANGER + "font-size: 12px; padding: 8px 16px;"
        )
        self.btn_eliminar.setToolTip("Eliminar perfil y todos sus datos")
        self.btn_eliminar.setEnabled(False)
        self.btn_eliminar.clicked.connect(self._on_eliminar)
        acciones_layout.addWidget(self.btn_eliminar)

        # Separador
        acciones_layout.addSpacing(20)

        # Botón Logo (azul)
        self.btn_logo = QPushButton("Logo")
        self.btn_logo.setAccessibleName("Botón cambiar logo corporativo")
        self.btn_logo.setIcon(icon_for_button("open"))
        self.btn_logo.setStyleSheet(
            styles.STYLE_BUTTON_PRIMARY + "font-size: 12px; padding: 8px 16px;"
        )
        self.btn_logo.setToolTip("Cambiar logo corporativo")
        self.btn_logo.setEnabled(False)
        self.btn_logo.clicked.connect(self._on_logo)
        acciones_layout.addWidget(self.btn_logo)

        # Botón Contraseña (naranja)
        self.btn_password = QPushButton("Contraseña")
        self.btn_password.setAccessibleName("Botón cambiar contraseña")
        self.btn_password.setIcon(icon_for_button("key"))
        self.btn_password.setStyleSheet(
            styles.STYLE_BUTTON_WARNING + "font-size: 12px; padding: 8px 16px;"
        )
        self.btn_password.setToolTip("Cambiar contraseña (solo tu perfil)")
        self.btn_password.setEnabled(False)
        self.btn_password.clicked.connect(self._on_password)
        acciones_layout.addWidget(self.btn_password)

        # Separador
        acciones_layout.addSpacing(20)

        # Botón Refrescar (gris)
        btn_refrescar = QPushButton()
        btn_refrescar.setIcon(icon_for_button("refresh"))
        btn_refrescar.setStyleSheet("""
            QPushButton {
                background-color: #607D8B;
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #546E7A;
            }
        """)
        btn_refrescar.setToolTip("Refrescar tabla")
        btn_refrescar.clicked.connect(self.refrescar)
        acciones_layout.addWidget(btn_refrescar)

        layout.addLayout(acciones_layout)

        # ===== TABLA =====
        self.tabla = QTableWidget()
        self.tabla.setAccessibleName("Tabla de perfiles de usuario")
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels(
            ["Usuario", "Email", "BD", "Logo", "Actual", "Acciones"]
        )

        # Configurar header con anchos optimizados
        header = self.tabla.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Usuario - más espacio
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Email - más espacio

        # Columnas con ancho fijo estrecho
        self.tabla.setColumnWidth(2, 60)  # BD - más estrecho
        self.tabla.setColumnWidth(3, 70)  # Logo - más estrecho
        self.tabla.setColumnWidth(4, 80)  # Actual - más estrecho
        self.tabla.setColumnWidth(5, 100)  # Acciones - ancho legible

        # Configurar tabla
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setMinimumHeight(400)

        # Conectar señal de selección
        self.tabla.itemSelectionChanged.connect(self._on_seleccion_cambiada)

        layout.addWidget(self.tabla)

    def refrescar(self):
        """Refresca la tabla de perfiles."""
        try:
            # Usar use case para obtener perfiles
            perfiles = self.uc_listar.execute()

            # Limpiar tabla
            self.tabla.setRowCount(0)

            # Llenar tabla
            for perfil in perfiles:
                row = self.tabla.rowCount()
                self.tabla.insertRow(row)

                # Usuario
                item_usuario = QTableWidgetItem(perfil.username)
                if perfil.es_actual:
                    item_usuario.setBackground(Qt.GlobalColor.yellow)
                    item_usuario.setForeground(Qt.GlobalColor.black)
                self.tabla.setItem(row, 0, item_usuario)

                # Email
                self.tabla.setItem(row, 1, QTableWidgetItem(perfil.email))

                # BD
                bd_item = QTableWidgetItem("✅" if perfil.tiene_bd else "❌")
                bd_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla.setItem(row, 2, bd_item)

                # Logo
                logo_item = QTableWidgetItem("🖼️" if perfil.tiene_logo else "➖")
                logo_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla.setItem(row, 3, logo_item)

                # Actual
                actual_item = QTableWidgetItem("⭐" if perfil.es_actual else "")
                actual_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla.setItem(row, 4, actual_item)

                # Acciones (vacío, se usan botones de arriba)
                self.tabla.setItem(row, 5, QTableWidgetItem(""))

        except (SQLAlchemyError, ValueError, TypeError, OSError) as e:
            self.mostrar_error("Error al cargar perfiles", str(e))

    def _on_seleccion_cambiada(self):
        """Actualiza estado de botones según selección."""
        hay_seleccion = len(self.tabla.selectedItems()) > 0

        if hay_seleccion:
            row = self.tabla.currentRow()
            es_actual = self.tabla.item(row, 4).text() == "⭐"

            # Habilitar botones según contexto
            self.btn_editar.setEnabled(True)
            self.btn_eliminar.setEnabled(not es_actual)  # No eliminar perfil actual
            self.btn_logo.setEnabled(True)
            self.btn_password.setEnabled(es_actual)  # Solo cambiar password del actual
        else:
            self.btn_editar.setEnabled(False)
            self.btn_eliminar.setEnabled(False)
            self.btn_logo.setEnabled(False)
            self.btn_password.setEnabled(False)

    def _on_crear(self):
        """Crea un nuevo perfil."""
        try:
            dialogo = DialogoCrearPerfilProfesional(self)
            if dialogo.exec():
                dto = dialogo.get_data()

                # Ejecutar use case
                perfil = self.uc_crear.execute(dto)

                # Refrescar tabla
                self.refrescar()

                ToastNotification(self.window(), f"Perfil '{perfil.username}' creado correctamente", "success")

        except ValidationError as e:
            ToastNotification(self.window(), str(e), "error")
        except (ValueError, TypeError) as e:
            self.mostrar_error("Error al crear perfil", str(e))

    def _on_editar(self):
        """Edita el perfil seleccionado."""
        row = self.tabla.currentRow()
        if row < 0:
            return

        try:
            username = self.tabla.item(row, 0).text()
            email_actual = self.tabla.item(row, 1).text()

            dialogo = DialogoEditarPerfilProfesional(username, email_actual, self)
            if dialogo.exec():
                dto = dialogo.get_data()

                # Ejecutar use case
                perfil = self.uc_actualizar.execute(dto)

                # Refrescar tabla
                self.refrescar()

                ToastNotification(self.window(), f"Perfil '{perfil.username}' actualizado", "success")

        except ValidationError as e:
            ToastNotification(self.window(), str(e), "error")
        except NotFoundError as e:
            ToastNotification(self.window(), str(e), "error")
        except (ValueError, TypeError) as e:
            self.mostrar_error("Error al actualizar perfil", str(e))

    def _on_eliminar(self):
        """Elimina el perfil seleccionado."""
        row = self.tabla.currentRow()
        if row < 0:
            return

        try:
            username = self.tabla.item(row, 0).text()
            email = self.tabla.item(row, 1).text()

            # Crear diálogo personalizado para confirmación
            dialog = QDialog(self)
            dialog.setWindowTitle("Confirmar Eliminación")
            dialog.setMinimumWidth(450)
            dialog.setModal(True)

            layout = QVBoxLayout(dialog)
            layout.setSpacing(15)
            layout.setContentsMargins(20, 20, 20, 20)

            # Título
            titulo = QLabel(f"<h3>¿Eliminar el perfil '{username}'?</h3>")
            titulo.setWordWrap(True)
            layout.addWidget(titulo)

            # Email
            email_label = QLabel(f"<b>Email:</b> {email}")
            layout.addWidget(email_label)

            # Advertencia
            advertencia = QLabel(
                "<p style='color: #d32f2f; font-weight: bold;'>⚠️ ADVERTENCIA: Se eliminará:</p>"
                "<ul style='margin-left: 20px;'>"
                "<li>El perfil de usuario</li>"
                "<li>Su base de datos completa</li>"
                "<li>Su logo corporativo (si existe)</li>"
                "</ul>"
            )
            advertencia.setWordWrap(True)
            layout.addWidget(advertencia)

            # Mensaje final
            final = QLabel("<p><b>Esta acción NO se puede deshacer.</b></p>")
            final.setStyleSheet("color: #d32f2f;")
            layout.addWidget(final)

            # Espaciador
            layout.addSpacing(10)

            # Botones
            button_box = QDialogButtonBox()

            btn_cancelar = QPushButton("Cancelar")
            btn_cancelar.setObjectName("secondaryButton")
            btn_cancelar.setMinimumWidth(100)
            btn_cancelar.setMinimumHeight(35)

            btn_eliminar = QPushButton("Eliminar Perfil")
            btn_eliminar.setIcon(icon_for_button("delete"))
            btn_eliminar.setMinimumWidth(140)
            btn_eliminar.setMinimumHeight(35)
            btn_eliminar.setProperty("danger", "true")

            button_box.addButton(btn_cancelar, QDialogButtonBox.ButtonRole.RejectRole)
            button_box.addButton(btn_eliminar, QDialogButtonBox.ButtonRole.AcceptRole)

            btn_cancelar.clicked.connect(dialog.reject)
            btn_eliminar.clicked.connect(dialog.accept)

            layout.addWidget(button_box)

            # Mostrar diálogo
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # Ejecutar use case
                self.uc_eliminar.execute(username)

                # Refrescar tabla
                self.refrescar()

                ToastNotification(self.window(), f"Perfil '{username}' eliminado", "success")

        except ValidationError as e:
            ToastNotification(self.window(), str(e), "error")
        except NotFoundError as e:
            ToastNotification(self.window(), str(e), "error")
        except (ValueError, TypeError) as e:
            self.mostrar_error("Error al eliminar perfil", str(e))

    def _on_logo(self):
        """Cambia el logo del perfil seleccionado."""
        row = self.tabla.currentRow()
        if row < 0:
            return

        try:
            username = self.tabla.item(row, 0).text()

            # Seleccionar archivo
            archivo, _ = QFileDialog.getOpenFileName(
                self, "Seleccionar Logo Corporativo", "", "Imágenes (*.png *.jpg *.jpeg *.bmp)"
            )

            if not archivo:
                return

            # Ejecutar use case
            ruta_guardada = self.uc_actualizar_logo.execute(username, archivo)
            self.logger.info(f"Logo actualizado para {username}: {ruta_guardada}")

            # Refrescar tabla
            self.refrescar()

            ToastNotification(self.window(), f"Logo del perfil '{username}' actualizado", "success")

        except ValidationError as e:
            ToastNotification(self.window(), str(e), "error")
        except NotFoundError as e:
            ToastNotification(self.window(), str(e), "error")
        except (ValueError, TypeError) as e:
            self.mostrar_error("Error al actualizar logo", str(e))

    def _on_password(self):
        """Cambia la contraseña del perfil actual (solo el logueado)."""
        row = self.tabla.currentRow()
        if row < 0:
            return

        try:
            username = self.tabla.item(row, 0).text()

            # Verificar que es el usuario actual
            if username != self.current_username:
                ToastNotification(self.window(), "Solo puedes cambiar la contraseña de tu propio perfil", "error")
                return

            dialogo = DialogoCambiarPasswordProfesional(username, self)
            if dialogo.exec():
                dto = dialogo.get_data()

                # Ejecutar use case
                self.uc_cambiar_password.execute(dto)

                ToastNotification(self.window(), "Contraseña cambiada correctamente", "success")

        except ValidationError as e:
            ToastNotification(self.window(), str(e), "error")
        except (ValueError, TypeError) as e:
            self.mostrar_error("Error al cambiar contraseña", str(e))
