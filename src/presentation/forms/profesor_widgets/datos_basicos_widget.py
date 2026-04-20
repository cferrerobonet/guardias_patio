"""
Widget de datos básicos del profesor.

Este widget encapsula los campos fundamentales del profesor:
- Nombre completo
- Email
- Checkbox de tutor
"""

from typing import Tuple

from presentation.theme import legacy_styles as styles
from PyQt6.QtCore import QRegularExpression, pyqtSignal
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtWidgets import QCheckBox, QGroupBox, QLabel, QLineEdit, QVBoxLayout
from utils.validators import validar_email, validar_nombre_completo


class DatosBasicosWidget(QGroupBox):
    """
    Widget para gestionar datos básicos del profesor.

    Señales:
        datos_changed: Se emite cuando cambian los datos del widget
    """

    # Señales
    datos_changed = pyqtSignal()

    def __init__(self, parent=None):
        """
        Inicializar widget de datos básicos.

        Args:
            parent: Widget padre (opcional)
        """
        super().__init__("📋 Datos Básicos", parent)
        self._setup_ui()
        self._conectar_senales()

    def _setup_ui(self):
        """Crear la interfaz de usuario del widget."""
        layout = QVBoxLayout()
        layout.setSpacing(4)  # Reducido de 6 a 4

        # Nombre completo
        label_nombre = QLabel("Nombre completo (formato: APELLIDOS, NOMBRE):")
        label_nombre.setObjectName("fieldLabel")
        layout.addWidget(label_nombre)

        self.nombre_completo_input = QLineEdit()
        self.nombre_completo_input.setPlaceholderText("GARCÍA LÓPEZ, JUAN")
        self.nombre_completo_input.setMaximumWidth(350)
        self.nombre_completo_input.setValidator(
            QRegularExpressionValidator(QRegularExpression(r".{2,100}"))
        )
        self.nombre_completo_input.setToolTip(
            "Formato requerido: APELLIDOS, NOMBRE\n"
            "Ejemplo: GARCÍA LÓPEZ, JUAN\n"
            "Debe contener una coma separando apellidos y nombre"
        )
        layout.addWidget(self.nombre_completo_input)

        # Email
        label_email = QLabel("Email corporativo:")
        label_email.setObjectName("fieldLabel")
        layout.addWidget(label_email)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("profesor@colegio.edu")
        self.email_input.setMaximumWidth(350)
        self.email_input.setValidator(
            QRegularExpressionValidator(
                QRegularExpression(r"([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})?")
            )
        )
        self.email_input.setToolTip(
            "Email corporativo del profesor (opcional)\n"
            "Se usará para enviar calendarios y notificaciones"
        )
        layout.addWidget(self.email_input)

        # Tutor
        self.tutor_checkbox = QCheckBox("✓ Es tutor/a")
        self.tutor_checkbox.setStyleSheet(
            "font-size: 13px; margin-top: 2px;"
        )  # Reducido de 5px a 2px
        self.tutor_checkbox.setToolTip(
            "Marca si el profesor es tutor de un grupo\n"
            "Los tutores pueden tener un ajuste de carga diferente"
        )
        layout.addWidget(self.tutor_checkbox)

        self.setLayout(layout)

    def _conectar_senales(self):
        """Conectar señales de los campos al signal de cambios."""
        self.nombre_completo_input.textChanged.connect(self.datos_changed.emit)
        self.email_input.textChanged.connect(self.datos_changed.emit)
        self.tutor_checkbox.stateChanged.connect(self.datos_changed.emit)

    def get_nombre_completo(self) -> str:
        """
        Obtener el nombre completo del profesor.

        Returns:
            Nombre completo del profesor
        """
        return self.nombre_completo_input.text().strip()

    def set_nombre_completo(self, nombre: str):
        """
        Establecer el nombre completo del profesor.

        Args:
            nombre: Nombre completo del profesor
        """
        self.nombre_completo_input.setText(nombre if nombre else "")

    def get_email(self) -> str:
        """
        Obtener el email del profesor.

        Returns:
            Email del profesor
        """
        return self.email_input.text().strip()

    def set_email(self, email: str):
        """
        Establecer el email del profesor.

        Args:
            email: Email del profesor
        """
        self.email_input.setText(email if email else "")

    def get_es_tutor(self) -> bool:
        """
        Verificar si el profesor es tutor.

        Returns:
            True si el profesor es tutor, False en caso contrario
        """
        return self.tutor_checkbox.isChecked()

    def set_es_tutor(self, es_tutor: bool):
        """
        Establecer si el profesor es tutor.

        Args:
            es_tutor: True si el profesor es tutor, False en caso contrario
        """
        self.tutor_checkbox.setChecked(es_tutor)

    def get_datos(self) -> dict:
        """
        Obtener todos los datos del widget.

        Returns:
            Diccionario con nombre_completo, email y es_tutor
        """
        return {
            "nombre_completo": self.get_nombre_completo(),
            "email": self.get_email(),
            "es_tutor": self.get_es_tutor(),
        }

    def set_datos(self, datos: dict):
        """
        Establecer todos los datos del widget.

        Args:
            datos: Diccionario con nombre_completo, email, es_tutor
        """
        if "nombre_completo" in datos:
            self.set_nombre_completo(datos["nombre_completo"])
        if "email" in datos:
            self.set_email(datos["email"])
        if "es_tutor" in datos:
            self.set_es_tutor(datos["es_tutor"])

    def limpiar(self):
        """Limpiar todos los campos del widget."""
        self.nombre_completo_input.clear()
        self.email_input.clear()
        self.tutor_checkbox.setChecked(False)

    def validar(self) -> Tuple[bool, str]:
        """
        Validar los datos del widget.

        Returns:
            Tupla (es_valido, mensaje_error)
            es_valido: True si los datos son válidos
            mensaje_error: Mensaje de error si no es válido, vacío si es válido
        """
        nombre = self.get_nombre_completo()

        # Validar nombre completo (obligatorio)
        if not nombre:
            return False, "El nombre completo es obligatorio"

        es_valido_nombre, mensaje_nombre = validar_nombre_completo(nombre)
        if not es_valido_nombre:
            return False, mensaje_nombre

        # Validar email (opcional, pero si está debe ser válido)
        email = self.get_email()
        if email:
            es_valido_email, mensaje_email = validar_email(email)
            if not es_valido_email:
                return False, mensaje_email

        return True, ""

    def enfocar_primer_campo(self):
        """Poner el foco en el primer campo del widget."""
        self.nombre_completo_input.setFocus()
        self.nombre_completo_input.selectAll()
