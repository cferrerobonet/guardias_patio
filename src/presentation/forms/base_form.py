"""
Base Form

Clase base para todos los formularios de la aplicación.
Proporciona funcionalidad común y establece el patrón MVP.
"""

from PyQt6.QtWidgets import QMessageBox, QWidget
from sqlalchemy.orm import Session

from utils.exceptions import BusinessLogicError, NotFoundError, ValidationError
from utils.logger import get_logger
from utils.ui_helpers import get_corporate_icon


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
            mensaje: Contenido del mensaje
        """
        self.logger.info(f"Mensaje de éxito mostrado: {titulo} - {mensaje}")
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(titulo)
        msg_box.setText(mensaje)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowIcon(get_corporate_icon())
        msg_box.exec()

    def mostrar_error(self, titulo: str, mensaje: str) -> None:
        """
        Muestra un mensaje de error al usuario.

        Args:
            titulo: Título del error
            mensaje: Descripción del error
        """
        self.logger.error(f"Error mostrado al usuario: {titulo} - {mensaje}")
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(titulo)
        msg_box.setText(mensaje)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowIcon(get_corporate_icon())
        msg_box.exec()

    def mostrar_advertencia(self, titulo: str, mensaje: str) -> None:
        """
        Muestra una advertencia al usuario.

        Args:
            titulo: Título de la advertencia
            mensaje: Contenido de la advertencia
        """
        self.logger.warning(f"Advertencia mostrada: {titulo} - {mensaje}")
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(titulo)
        msg_box.setText(mensaje)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowIcon(get_corporate_icon())
        msg_box.exec()

    def confirmar_accion(self, titulo: str, mensaje: str) -> bool:
        """
        Solicita confirmación al usuario para una acción.

        Args:
            titulo: Título del diálogo
            mensaje: Pregunta de confirmación

        Returns:
            True si el usuario confirma, False en caso contrario
        """
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(titulo)
        msg_box.setText(mensaje)
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setWindowIcon(get_corporate_icon())
        msg_box.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)
        respuesta = msg_box.exec()
        confirmado = respuesta == QMessageBox.StandardButton.Yes.value
        self.logger.info(f"Confirmación solicitada: {titulo} - Confirmado: {confirmado}")
        return confirmado

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
