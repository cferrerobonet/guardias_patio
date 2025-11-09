"""
Base Form

Clase base para todos los formularios de la aplicación.
Proporciona funcionalidad común y establece el patrón MVP.
"""

from PyQt6.QtWidgets import QMessageBox, QWidget
from sqlalchemy.orm import Session

from core.exceptions import BusinessLogicError, NotFoundError, ValidationError
from utils.logger import get_logger
from utils.ui_helpers import (
    MESSAGEBOX_STYLE,
    apply_corporate_icon_to_messagebox,
    get_corporate_icon,
    get_corporate_pixmap,
)


class BaseForm(QWidget):
    """
    Clase base para todos los formularios.

    Proporciona:
    - Gestión de sesión de BD
    - Métodos comunes para mostrar mensajes
    - Manejo de excepciones estandarizado
    - Logging estructurado
    """

    def __init__(self, session: Session, parent=None):
        """
        Inicializa el formulario base.

        Args:
            session: Sesión de SQLAlchemy para Use Cases
            parent: Widget padre (opcional)
        """
        super().__init__(parent)
        self.session = session
        # Cada formulario tiene su propio logger estructurado
        self.logger = get_logger(self.__class__.__name__)

    def mostrar_exito(self, titulo: str, mensaje: str) -> None:
        """
        Muestra un mensaje de éxito al usuario.

        Args:
            titulo: Título del mensaje
            mensaje: Contenido del mensaje (puede contener HTML)
        """
        from PyQt6.QtCore import Qt

        self.logger.info(f"Mensaje de éxito mostrado: {titulo} - {mensaje}")
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(titulo)
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        msg_box.setText(mensaje)
        msg_box.setWindowIcon(get_corporate_icon())

        # Aplicar icono corporativo
        apply_corporate_icon_to_messagebox(msg_box)

        # Aplicar estilos directamente
        msg_box.setStyleSheet(MESSAGEBOX_STYLE)

        msg_box.exec()

    def mostrar_error(self, titulo: str, mensaje: str) -> None:
        """
        Muestra un mensaje de error al usuario.

        Args:
            titulo: Título del error
            mensaje: Descripción del error (puede contener HTML)
        """
        from PyQt6.QtCore import Qt

        self.logger.error(f"Error mostrado al usuario: {titulo} - {mensaje}")
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(titulo)
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        msg_box.setText(mensaje)
        msg_box.setWindowIcon(get_corporate_icon())

        # Aplicar icono corporativo
        apply_corporate_icon_to_messagebox(msg_box)

        # Aplicar estilos directamente
        msg_box.setStyleSheet(MESSAGEBOX_STYLE)

        msg_box.exec()

    def mostrar_advertencia(self, titulo: str, mensaje: str) -> None:
        """
        Muestra una advertencia al usuario.

        Args:
            titulo: Título de la advertencia
            mensaje: Contenido de la advertencia (puede contener HTML)
        """
        from PyQt6.QtCore import Qt

        self.logger.warning(f"Advertencia mostrada: {titulo} - {mensaje}")
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(titulo)
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        msg_box.setText(mensaje)
        msg_box.setWindowIcon(get_corporate_icon())

        # Aplicar icono corporativo
        apply_corporate_icon_to_messagebox(msg_box)

        # Aplicar estilos directamente
        msg_box.setStyleSheet(MESSAGEBOX_STYLE)

        msg_box.exec()

    def mostrar_informacion(self, titulo: str, mensaje: str) -> None:
        """
        Muestra un mensaje informativo al usuario.

        Args:
            titulo: Título del mensaje
            mensaje: Contenido del mensaje (puede contener HTML)
        """
        from PyQt6.QtCore import Qt

        self.logger.info(f"Información mostrada: {titulo} - {mensaje}")
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(titulo)
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        msg_box.setText(mensaje)
        msg_box.setWindowIcon(get_corporate_icon())

        # Aplicar icono corporativo
        apply_corporate_icon_to_messagebox(msg_box)

        # Aplicar estilos directamente
        msg_box.setStyleSheet(MESSAGEBOX_STYLE)

        msg_box.exec()

    def confirmar_accion(self, titulo: str, mensaje: str) -> bool:
        """
        Solicita confirmación al usuario para una acción.

        Args:
            titulo: Título del diálogo
            mensaje: Pregunta de confirmación (puede contener HTML)

        Returns:
            True si el usuario confirma, False en caso contrario
        """
        from PyQt6.QtCore import Qt

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(titulo)
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        msg_box.setText(mensaje)
        msg_box.setWindowIcon(get_corporate_icon())

        # Aplicar icono corporativo
        apply_corporate_icon_to_messagebox(msg_box)

        msg_box.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)

        # Aplicar estilos directamente a los botones
        msg_box.setStyleSheet(MESSAGEBOX_STYLE)
        respuesta = msg_box.exec()
        confirmado = respuesta == QMessageBox.StandardButton.Yes.value
        self.logger.info(f"Confirmación solicitada: {titulo} - Confirmado: {confirmado}")
        return confirmado

    def mostrar_pregunta(self, titulo: str, mensaje: str,
                         botones=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No):
        """
        Muestra una pregunta al usuario con icono corporativo.

        Args:
            titulo: Título del diálogo
            mensaje: Pregunta (puede contener HTML)
            botones: Botones a mostrar (por defecto Yes|No)

        Returns:
            StandardButton presionado por el usuario
        """
        from PyQt6.QtCore import Qt

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(titulo)
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        msg_box.setText(mensaje)
        msg_box.setWindowIcon(get_corporate_icon())

        # Usar logo corporativo en lugar del icono estándar
        pixmap = get_corporate_pixmap(64)
        if pixmap:
            msg_box.setIconPixmap(pixmap)
        else:
            msg_box.setIcon(QMessageBox.Icon.Question)

        msg_box.setStandardButtons(botones)

        # Aplicar estilo corporativo a los botones
        msg_box.setStyleSheet(MESSAGEBOX_STYLE)

        return msg_box.exec()

    def manejar_excepcion(self, exception: Exception, operacion: str) -> None:
        """
        Maneja excepciones de forma estandarizada.

        Args:
            exception: La excepción capturada
            operacion: Descripción de la operación que falló
        """
        if isinstance(exception, ValidationError):
            self.mostrar_error(
                "Error de Validación",
                f"Los datos ingresados no son válidos:\n\n{str(exception)}"
            )
        elif isinstance(exception, NotFoundError):
            self.mostrar_error(
                "No Encontrado",
                f"El elemento solicitado no existe:\n\n{str(exception)}"
            )
        elif isinstance(exception, BusinessLogicError):
            self.mostrar_error(
                "Error de Negocio",
                f"No se puede completar la operación:\n\n{str(exception)}"
            )
        else:
            self.mostrar_error(
                f"Error en {operacion}",
                f"Ha ocurrido un error inesperado:\n\n{str(exception)}"
            )
            self.logger.exception(
                f"Excepción no manejada en {operacion}: {type(exception).__name__}"
            )

    def limpiar_formulario(self) -> None:
        """
        Limpia todos los campos del formulario.

        Este método debe ser sobrescrito por las clases hijas.
        """
        raise NotImplementedError("Subclases deben implementar limpiar_formulario()")

    def validar_formulario(self) -> tuple[bool, str]:
        """
        Valida los datos del formulario antes de enviarlos.

        Este método debe ser sobrescrito por las clases hijas.

        Returns:
            Tupla (es_valido, mensaje_error)
        """
        raise NotImplementedError("Subclases deben implementar validar_formulario()")
