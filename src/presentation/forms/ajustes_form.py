"""
Ajustes Form - Refactorizado.

Form para gestionar los ajustes del curso escolar.
Sigue el patrón MVP usando Use Cases.
"""

from presentation.theme import legacy_styles as styles
from presentation.theme.tokens import Spacing
from application.dtos.configuracion_dto import ActualizarConfiguracionDTO
from application.use_cases.configuracion import (
    ActualizarConfiguracionUseCase,
    ObtenerConfiguracionUseCase,
)
from core.exceptions import NotFoundError
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from utils.icons import icon_for_button

from presentation.forms.base_form import BaseForm
from presentation.forms.config_widgets import (
    AjustesWidget,
    FechasRecreosWidget,
    FestivosWidget,
)


class AjustesForm(BaseForm):
    """
    Formulario para gestionar los ajustes del curso.

    Permite configurar:
    - Fechas del curso
    - Horarios de recreos
    - Ajustes de tutores/no tutores
    - Festivos y días no lectivos
    - Gestión de cursos escolares
    """

    def __init__(self, session, parent=None):
        """
        Inicializa el formulario de configuración.

        Args:
            session: Sesión de SQLAlchemy
            parent: Widget padre
        """
        super().__init__(session, parent)

        # Inicializar Use Cases
        self.obtener_config_uc = ObtenerConfiguracionUseCase(session)
        self.actualizar_config_uc = ActualizarConfiguracionUseCase(session)

        # Control de cambios sin guardar
        self._dirty = False

        # Configurar UI
        self.setup_ui()

        # Cargar configuración existente si hay
        self.cargar_configuracion()

        # Conectar señales de cambio DESPUÉS de cargar (para no marcar dirty en carga inicial)
        self._conectar_senales_cambio()

    # ===== PROPIEDADES DE COMPATIBILIDAD PARA TESTS =====
    # Delegan a los widgets internos para mantener la API anterior

    @property
    def fecha_inicio_input(self):
        """Acceso al campo fecha_inicio del widget fechas_recreos."""
        return self.fechas_recreos_widget.fecha_inicio_input

    @property
    def fecha_fin_input(self):
        """Acceso al campo fecha_fin del widget fechas_recreos."""
        return self.fechas_recreos_widget.fecha_fin_input

    @property
    def recreo1_manana_input(self):
        """Acceso al campo recreo1_manana del widget fechas_recreos."""
        return self.fechas_recreos_widget.recreo1_manana_input

    @property
    def recreo2_manana_input(self):
        """Acceso al campo recreo2_manana del widget fechas_recreos."""
        return self.fechas_recreos_widget.recreo2_manana_input

    @property
    def recreo1_tarde_input(self):
        """Acceso al campo recreo1_tarde del widget fechas_recreos."""
        return self.fechas_recreos_widget.recreo1_tarde_input

    @property
    def recreo2_tarde_input(self):
        """Acceso al campo recreo2_tarde del widget fechas_recreos."""
        return self.fechas_recreos_widget.recreo2_tarde_input

    @property
    def ajuste_tutores_input(self):
        """Acceso al campo ajuste_tutores del widget ajustes."""
        return self.ajustes_widget.ajuste_tutores_input

    @property
    def ajuste_no_tutores_input(self):
        """Acceso al campo ajuste_no_tutores del widget ajustes."""
        return self.ajustes_widget.ajuste_no_tutores_input

    @property
    def algoritmo_combo(self):
        """Acceso al campo algoritmo_combo del widget ajustes."""
        return self.ajustes_widget.algoritmo_combo

    @property
    def festivos_auto_input(self):
        """Acceso al campo festivos_auto del widget festivos."""
        return self.festivos_widget.festivos_auto_input

    @property
    def no_lectivos_input(self):
        """Acceso al campo no_lectivos del widget festivos."""
        return self.festivos_widget.no_lectivos_input

    def setup_ui(self) -> None:
        """Configura la interfaz de usuario."""
        self.setWindowTitle("Configuración del Curso")

        # Layout principal que contendrá el scroll area
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Crear el contenedor con scroll
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Widget contenedor del contenido
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        content_layout.setSpacing(Spacing.SM)

        # Título principal
        titulo = QLabel("AJUSTES DEL CURSO ESCOLAR")
        titulo.setObjectName("titleMain")
        content_layout.addWidget(titulo)

        # Indicador de cambios sin guardar
        self._dirty_label = QLabel("● Cambios sin guardar")
        self._dirty_label.setStyleSheet("color: #D97706; font-size: 11px; font-weight: bold;")
        self._dirty_label.setVisible(False)
        content_layout.addWidget(self._dirty_label)

        # ===== FILA 1: Fechas y Recreos =====
        self.fechas_recreos_widget = FechasRecreosWidget(self)
        content_layout.addWidget(self.fechas_recreos_widget)

        # ===== FILA 2: Ajustes + Festivos (2 columnas) =====
        fila2_layout = QHBoxLayout()
        fila2_layout.setSpacing(6)

        self.ajustes_widget = AjustesWidget(self)
        fila2_layout.addWidget(self.ajustes_widget)

        self.festivos_widget = FestivosWidget(self)
        fila2_layout.addWidget(self.festivos_widget)

        content_layout.addLayout(fila2_layout)

        # ===== GESTIÓN DE CURSOS ESCOLARES =====
        from presentation.widgets.gestion_cursos_widget import GestionCursosWidget

        self.gestion_cursos_widget = GestionCursosWidget(self.session, self)
        content_layout.addWidget(self.gestion_cursos_widget)

        # Espacio flexible antes de los botones
        content_layout.addStretch()

        # Botones al final
        btn_layout = self._crear_botones()
        content_layout.addLayout(btn_layout)

        # Establecer el layout en el widget contenedor
        content_widget.setLayout(content_layout)

        # Agregar el widget al scroll area
        scroll_area.setWidget(content_widget)

        # Agregar contenido en pestañas
        from presentation.forms.conectividad_form import ConectividadForm

        tab_widget = QTabWidget()
        tab_widget.addTab(scroll_area, "Ajustes")
        tab_widget.addTab(ConectividadForm(self.session), "Conectividad")
        main_layout.addWidget(tab_widget)

        self.setLayout(main_layout)

    def _crear_botones(self) -> QHBoxLayout:
        """Crea los botones de acción."""
        layout = QHBoxLayout()
        layout.setSpacing(10)

        self.save_btn = QPushButton("Guardar Configuración")
        self.save_btn.setIcon(icon_for_button("save"))
        self.save_btn.setProperty("success", "true")
        self.save_btn.clicked.connect(self.guardar_configuracion)
        self.save_btn.setShortcut(QKeySequence("Ctrl+S"))
        self.save_btn.setToolTip("Guardar configuración (Ctrl+S)")

        self.load_btn = QPushButton("Cargar Actual")
        self.load_btn.setIcon(icon_for_button("refresh"))
        self.load_btn.clicked.connect(self.cargar_configuracion)

        layout.addWidget(self.save_btn)
        layout.addWidget(self.load_btn)
        layout.addStretch()

        return layout

    def guardar_configuracion(self) -> None:
        """
        Guarda la configuración usando el Use Case.

        Valida los datos y ejecuta ActualizarConfiguracionUseCase.
        También guarda la configuración SMTP si fue modificada.
        """
        try:
            # Validar formulario
            es_valido, mensaje = self.validar_formulario()
            if not es_valido:
                self.mostrar_advertencia("Validación", mensaje)
                return

            # Crear DTO con recreos_config generado automáticamente
            fechas = self.fechas_recreos_widget.get_fechas()
            recreos_manana = self.fechas_recreos_widget.get_recreos_manana()
            recreos_tarde = self.fechas_recreos_widget.get_recreos_tarde()
            ajustes = self.ajustes_widget.get_ajustes()
            festivos_config = self.festivos_widget.get_festivos_config()

            dto = ActualizarConfiguracionDTO(
                fecha_inicio_curso=fechas["fecha_inicio"],
                fecha_fin_curso=fechas["fecha_fin"],
                hora_recreo1_manana=recreos_manana["recreo1"],
                hora_recreo2_manana=recreos_manana["recreo2"],
                hora_recreo1_tarde=recreos_tarde["recreo1"],
                hora_recreo2_tarde=recreos_tarde["recreo2"],
                ajuste_tutores=ajustes["tutores"],
                ajuste_no_tutores=ajustes["no_tutores"],
                activar_festivos_automaticos=festivos_config["activar_automaticos"],
                dias_no_lectivos_personalizados=festivos_config["dias_no_lectivos"],
                recreos_config=self._generar_recreos_config_json(),
                algoritmo_asignacion=ajustes["algoritmo"],
            )

            # Ejecutar Use Case
            config = self.actualizar_config_uc.execute(dto)

            # Mostrar éxito
            # Extraer solo los años de las fechas
            año_inicio = config.fecha_inicio_curso.year
            año_fin = config.fecha_fin_curso.year

            mensaje_exito = (
                f"La configuración del curso "
                f"<span style='color: #007ACC; font-style: italic;'>{año_inicio}-{año_fin}</span> "
                f"ha sido guardada correctamente."
            )

            self.mostrar_exito("Configuración Guardada", mensaje_exito)
            self._marcar_guardado()

        except (ValueError, TypeError, OSError) as e:
            self.manejar_excepcion(e, "guardar configuración")

    def cargar_configuracion(self) -> None:
        """
        Carga la configuración actual usando el Use Case.

        Si no existe configuración, muestra valores por defecto.
        """
        try:
            # Ejecutar Use Case
            config = self.obtener_config_uc.execute()

            # Cargar fechas y recreos en el widget
            self.fechas_recreos_widget.set_fechas(config.fecha_inicio_curso, config.fecha_fin_curso)
            self.fechas_recreos_widget.set_recreos_manana(
                config.hora_recreo1_manana, config.hora_recreo2_manana
            )

            if config.hora_recreo1_tarde and config.hora_recreo2_tarde:
                self.fechas_recreos_widget.set_recreos_tarde(
                    config.hora_recreo1_tarde, config.hora_recreo2_tarde
                )

            # Cargar ajustes
            algoritmo = getattr(config, "algoritmo_asignacion", "v2.9")
            self.ajustes_widget.set_ajustes(
                tutores=config.ajuste_tutores,
                no_tutores=config.ajuste_no_tutores,
                algoritmo=algoritmo,
            )

            # Cargar festivos
            self.festivos_widget.set_festivos_config(
                activar_automaticos=config.activar_festivos_automaticos,
                dias_no_lectivos=config.dias_no_lectivos_personalizados or "",
            )

            self.logger.info("Configuración cargada correctamente")
            self._marcar_guardado()

        except NotFoundError:
            # No hay configuración, usar valores por defecto
            self.logger.info("No hay configuración guardada, usando valores por defecto")
        except (ValueError, TypeError, OSError) as e:
            self.manejar_excepcion(e, "cargar configuración")

    def limpiar_formulario(self) -> None:
        """Limpia el formulario (no usado en configuración)."""
        # No aplica para configuración ya que solo hay un registro
        pass

    def _conectar_senales_cambio(self) -> None:
        """Conecta señales para detectar cambios sin guardar."""
        self.fechas_recreos_widget.config_changed.connect(self._marcar_pendiente)
        self.ajustes_widget.config_changed.connect(self._marcar_pendiente)
        self.festivos_widget.config_changed.connect(self._marcar_pendiente)

    def _marcar_pendiente(self) -> None:
        """Marca que hay cambios sin guardar."""
        self._dirty = True
        self._dirty_label.setVisible(True)

    def _marcar_guardado(self) -> None:
        """Marca que todos los cambios han sido guardados."""
        self._dirty = False
        if hasattr(self, "_dirty_label"):
            self._dirty_label.setVisible(False)


        """
        Genera el JSON de configuración de recreos basado en los valores del formulario.

        El número de zonas se obtiene automáticamente contando las zonas en la tabla Zona.

        Returns:
            str: JSON con la configuración de recreos, o cadena vacía si no hay recreos.
        """
        import json
        from datetime import time

        from application.app_services import AppServices

        # Obtener número de zonas
        num_zonas = AppServices(self.session).contar_zonas()

        # Si no hay zonas, usar 4 por defecto (compatibilidad)
        if num_zonas == 0:
            num_zonas = 4

        recreos = []

        # Obtener recreos del widget
        recreos_manana = self.fechas_recreos_widget.get_recreos_manana()
        recreos_tarde = self.fechas_recreos_widget.get_recreos_tarde()

        # Recreo 1 Mañana
        hora_r1_manana = recreos_manana["recreo1"]
        if hora_r1_manana != time(0, 0):  # Si no es 00:00 (valor por defecto)
            recreos.append(
                {
                    "id": 1,
                    "etiqueta": "Recreo 1 Mañana",
                    "turno": "mañana",
                    "hora": hora_r1_manana.strftime("%H:%M"),
                    "zonas": num_zonas,
                }
            )

        # Recreo 2 Mañana
        hora_r2_manana = recreos_manana["recreo2"]
        if hora_r2_manana != time(0, 0):
            recreos.append(
                {
                    "id": 2,
                    "etiqueta": "Recreo 2 Mañana",
                    "turno": "mañana",
                    "hora": hora_r2_manana.strftime("%H:%M"),
                    "zonas": num_zonas,
                }
            )

        # Recreo 1 Tarde
        hora_r1_tarde = recreos_tarde["recreo1"]
        if hora_r1_tarde != time(0, 0):
            recreos.append(
                {
                    "id": 3,
                    "etiqueta": "Recreo 1 Tarde",
                    "turno": "tarde",
                    "hora": hora_r1_tarde.strftime("%H:%M"),
                    "zonas": num_zonas,
                }
            )

        # Recreo 2 Tarde
        hora_r2_tarde = recreos_tarde["recreo2"]
        if hora_r2_tarde != time(0, 0):
            recreos.append(
                {
                    "id": 4,
                    "etiqueta": "Recreo 2 Tarde",
                    "turno": "tarde",
                    "hora": hora_r2_tarde.strftime("%H:%M"),
                    "zonas": num_zonas,
                }
            )

        return json.dumps(recreos) if recreos else ""

    def validar_formulario(self) -> tuple[bool, str]:
        """
        Valida los datos del formulario.

        Returns:
            Tupla (es_valido, mensaje_error)
        """
        # Validar fechas y recreos usando el widget
        es_valido, mensaje = self.fechas_recreos_widget.validar()
        if not es_valido:
            return False, mensaje

        # Validar ajustes usando el widget
        es_valido, mensaje = self.ajustes_widget.validar()
        if not es_valido:
            return False, mensaje

        # Validar festivos usando el widget
        es_valido, mensaje = self.festivos_widget.validar()
        if not es_valido:
            return False, mensaje

        return True, ""

    def _guardar_email_interno(self) -> bool:
        """Guarda el email del usuario actual internamente.

        Returns:
            bool: True si se guardó correctamente o no hubo cambios,
                  False si hay error de validación.
        """
        try:
            nuevo_email = self.email_input.text().strip()

            # Validar email
            if not nuevo_email:
                return False

            if "@" not in nuevo_email or "." not in nuevo_email:
                return False

            # Verificar si el email cambió
            user_data = self.user_auth.users.get(self.current_username, {})
            email_actual = user_data.get("email", "")

            if nuevo_email == email_actual:
                return False  # No hubo cambios

            # Actualizar email en users.json
            if self.current_username in self.user_auth.users:
                self.user_auth.users[self.current_username]["email"] = nuevo_email
                self.user_auth._save_users()
                self.logger.info(f"Email actualizado para usuario {self.current_username}")
                return True
            else:
                return False

        except (ValueError, TypeError, OSError) as e:
            self.logger.error(f"Error al guardar email: {str(e)}")
            return False

    def guardar_email(self) -> None:
        """Guarda el email del usuario actual."""
        try:
            nuevo_email = self.email_input.text().strip()

            # Validar email
            if not nuevo_email:
                self.mostrar_advertencia("Email vacío", "El email no puede estar vacío")
                return

            if "@" not in nuevo_email or "." not in nuevo_email:
                self.mostrar_advertencia(
                    "Email inválido", "Por favor introduce un email válido (debe contener @ y .)"
                )
                return

            # Actualizar email en users.json
            if self.current_username in self.user_auth.users:
                self.user_auth.users[self.current_username]["email"] = nuevo_email
                self.user_auth._save_users()

                self.mostrar_exito(
                    "Email Actualizado", f"Tu email ha sido actualizado a: {nuevo_email}"
                )
                self.logger.info(f"Email actualizado para usuario {self.current_username}")
            else:
                self.mostrar_advertencia("Error", "No se encontró el usuario actual")

        except (ValueError, TypeError, OSError) as e:
            self.manejar_excepcion(e, "actualizar email")

    def cambiar_contrasena(self) -> None:
        """Abre diálogo para cambiar la contraseña."""
        try:
            from presentation.forms.change_password_dialog import ChangePasswordDialog

            dialog = ChangePasswordDialog(self.current_username, self)
            dialog.exec()

        except (ValueError, TypeError, OSError) as e:
            self.manejar_excepcion(e, "abrir diálogo de cambio de contraseña")
