"""
Base Form

Clase base para todos los formularios de la aplicación.
Proporciona funcionalidad común y establece el patrón MVP.
"""

from contextlib import contextmanager

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDateTimeEdit,
    QDoubleSpinBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QSpinBox,
    QTextEdit,
    QTimeEdit,
    QWidget,
)

from core.exceptions import BusinessLogicError, NotFoundError, ValidationError
from utils.logger import get_logger
from utils.ui_helpers import (
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
    - Indicador de cambios sin guardar (UX-UNSAVED)
    """

    # Señal emitida cuando el formulario tiene cambios sin guardar
    cambios_sin_guardar = pyqtSignal(bool)

    def __init__(self, session, parent=None):
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
        self._tiene_cambios = False
        self._label_cambios: QLabel | None = None
        #: Mientras es True, rellenar campos no cuenta como edición del usuario.
        self._cargando = False

    #: Señal de cada tipo de campo que indica que el usuario lo ha tocado.
    SENALES_DE_EDICION = (
        (QLineEdit, "textEdited"),
        (QPlainTextEdit, "textChanged"),
        (QTextEdit, "textChanged"),
        (QCheckBox, "toggled"),
        (QComboBox, "currentIndexChanged"),
        (QSpinBox, "valueChanged"),
        (QDoubleSpinBox, "valueChanged"),
        (QDateEdit, "dateChanged"),
        (QTimeEdit, "timeChanged"),
        (QDateTimeEdit, "dateTimeChanged"),
    )

    def vigilar_cambios(self, raiz: QWidget | None = None) -> int:
        """Conecta los campos editables para detectar ediciones sin guardar.

        Llamar al final de la construcción de la interfaz. Devuelve cuántos campos
        quedan vigilados. Los cambios hechos por código —al cargar un registro—
        no cuentan si se envuelven en `cargando()` (UXA-004).
        """
        raiz = raiz or self
        vigilados = 0
        for tipo, nombre_senal in self.SENALES_DE_EDICION:
            for campo in raiz.findChildren(tipo):
                # QDateTimeEdit hereda de QDateEdit y QTimeEdit: evitar duplicados.
                if getattr(campo, "_vigilado_por_base_form", False):
                    continue
                senal = getattr(campo, nombre_senal, None)
                if senal is None:
                    continue
                senal.connect(self._al_editar_campo)
                campo._vigilado_por_base_form = True
                vigilados += 1
        return vigilados

    def _al_editar_campo(self, *_args) -> None:
        if not self._cargando:
            self._mark_dirty()

    @contextmanager
    def cargando(self):
        """Rellena campos por código sin que cuente como edición del usuario."""
        previo = self._cargando
        self._cargando = True
        try:
            yield
        finally:
            self._cargando = previo
            self._mark_clean()

    def descartar_cambios(self) -> None:
        """Olvida el estado de cambios pendientes (tras guardar o descartar)."""
        self._mark_clean()

    def guardar_cambios_pendientes(self) -> bool:
        """Guarda los cambios del formulario.

        Devuelve True si se guardaron. Los formularios que sepan guardarse lo
        redefinen; el guard de navegación sólo ofrece "Guardar" cuando existe.
        """
        return False

    def puede_guardar_desde_el_guard(self) -> bool:
        """True si este formulario implementa `guardar_cambios_pendientes`."""
        return type(self).guardar_cambios_pendientes is not BaseForm.guardar_cambios_pendientes

    def _mark_dirty(self) -> None:
        """Marca el formulario como modificado sin guardar."""
        if not self._tiene_cambios:
            self._tiene_cambios = True
            self._actualizar_indicador_cambios()
            self.cambios_sin_guardar.emit(True)

    def _mark_clean(self) -> None:
        """Marca el formulario como guardado (sin cambios pendientes)."""
        if self._tiene_cambios:
            self._tiene_cambios = False
            self._actualizar_indicador_cambios()
            self.cambios_sin_guardar.emit(False)

    def tiene_cambios(self) -> bool:
        """Devuelve True si hay cambios sin guardar."""
        return self._tiene_cambios

    def registrar_label_cambios(self, label: QLabel) -> None:
        """
        Registra un QLabel externo para mostrar el indicador de cambios sin guardar.

        El label se actualizará automáticamente al llamar a _mark_dirty() / _mark_clean().
        """
        self._label_cambios = label
        self._actualizar_indicador_cambios()

    def _actualizar_indicador_cambios(self) -> None:
        """Actualiza el label de indicador si está registrado."""
        if self._label_cambios is not None:
            if self._tiene_cambios:
                self._label_cambios.setText("● Cambios sin guardar")
                self._label_cambios.setObjectName("unsavedChanges")
                self._label_cambios.setVisible(True)
            else:
                self._label_cambios.setText("")
                self._label_cambios.setVisible(False)

    def mostrar_exito(self, titulo: str, mensaje: str) -> None:
        from html.parser import HTMLParser

        class _StripHTML(HTMLParser):
            def __init__(self):
                super().__init__()
                self._parts = []

            def handle_data(self, data):
                self._parts.append(data)

            def get_text(self):
                return "".join(self._parts)

        parser = _StripHTML()
        parser.feed(mensaje)
        texto_plano = parser.get_text().strip() or titulo

        self.logger.info(f"Mensaje de éxito: {titulo} - {texto_plano}")

        from presentation.widgets.toast_notification import ToastNotification
        ToastNotification(self.window(), f"✓ {texto_plano}", "success")

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

        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)

        # Aplicar estilos directamente a los botones
        respuesta = msg_box.exec()
        confirmado = respuesta == QMessageBox.StandardButton.Yes.value
        self.logger.info(f"Confirmación solicitada: {titulo} - Confirmado: {confirmado}")
        return confirmado

    def mostrar_pregunta(
        self,
        titulo: str,
        mensaje: str,
        botones=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
    ):
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
                "Error de Validación", f"Los datos ingresados no son válidos:\n\n{str(exception)}"
            )
        elif isinstance(exception, NotFoundError):
            self.mostrar_error(
                "No Encontrado", f"El elemento solicitado no existe:\n\n{str(exception)}"
            )
        elif isinstance(exception, BusinessLogicError):
            self.mostrar_error(
                "Error de Negocio", f"No se puede completar la operación:\n\n{str(exception)}"
            )
        else:
            self.mostrar_error(
                f"Error en {operacion}", f"Ha ocurrido un error inesperado:\n\n{str(exception)}"
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
