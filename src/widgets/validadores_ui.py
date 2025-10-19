"""
Validadores UI con Feedback Visual en Tiempo Real.

Este módulo proporciona validación inmediata de campos de formulario
con retroalimentación visual clara (colores, iconos, tooltips).

Sprint 8 - Task 8.6: Validaciones UI
"""

from typing import Callable, Optional, Tuple

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QLabel, QLineEdit

from utils.validators import (
    validar_email,
    validar_horas_contrato,
    validar_nombre_completo,
)

# ========== ESTILOS CSS ==========

STYLE_INPUT_VALID = """
    QLineEdit {
        border: 2px solid #4CAF50;
        background-color: #E8F5E9;
        padding: 8px;
        border-radius: 4px;
    }
"""

STYLE_INPUT_INVALID = """
    QLineEdit {
        border: 2px solid #F44336;
        background-color: #FFEBEE;
        padding: 8px;
        border-radius: 4px;
    }
"""

STYLE_INPUT_NEUTRAL = """
    QLineEdit {
        border: 2px solid #CCCCCC;
        background-color: #FFFFFF;
        padding: 8px;
        border-radius: 4px;
    }
"""

STYLE_LABEL_ERROR = """
    QLabel {
        color: #D32F2F;
        font-size: 11px;
        font-weight: bold;
        padding: 2px 4px;
    }
"""

STYLE_LABEL_SUCCESS = """
    QLabel {
        color: #388E3C;
        font-size: 11px;
        font-weight: bold;
        padding: 2px 4px;
    }
"""

STYLE_LABEL_HIDDEN = """
    QLabel {
        color: transparent;
        font-size: 11px;
    }
"""


# ========== VALIDADOR BASE ==========

class ValidadorCampo:
    """
    Validador base para campos de formulario con feedback visual.
    
    Proporciona validación en tiempo real con:
    - Colores de borde (verde/rojo/gris)
    - Mensaje de error/éxito debajo del campo
    - Debouncing para evitar validar en cada tecla
    """

    def __init__(
        self,
        campo: QLineEdit,
        label_error: QLabel,
        validador: Callable[[str], Tuple[bool, Optional[str]]],
        mensaje_exito: str = "✓ Válido",
        debounce_ms: int = 500
    ):
        """
        Inicializar validador de campo.
        
        Args:
            campo: QLineEdit a validar
            label_error: QLabel para mostrar mensajes
            validador: Función (str) -> (bool, str|None) que valida el valor
            mensaje_exito: Mensaje a mostrar cuando es válido
            debounce_ms: Milisegundos de espera antes de validar (default 500)
        """
        self.campo = campo
        self.label_error = label_error
        self.validador = validador
        self.mensaje_exito = mensaje_exito
        self.debounce_ms = debounce_ms

        # Estado
        self.es_valido = False
        self.ultimo_valor = ""

        # Timer para debouncing
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._validar)

        # Conectar señal de cambio de texto
        self.campo.textChanged.connect(self._on_text_changed)

        # Estado inicial
        self._set_estado_neutral()

    def _on_text_changed(self, texto: str):
        """Manejar cambio de texto con debouncing."""
        self.ultimo_valor = texto

        # Si está vacío, neutral inmediatamente
        if not texto.strip():
            self._set_estado_neutral()
            return

        # Restart timer para validar después de debounce
        self.timer.stop()
        self.timer.start(self.debounce_ms)

    def _validar(self):
        """Ejecutar validación y actualizar UI."""
        texto = self.ultimo_valor.strip()

        if not texto:
            self._set_estado_neutral()
            return

        # Ejecutar validador
        valido, mensaje = self.validador(texto)

        if valido:
            self._set_estado_valido()
            self.es_valido = True
        else:
            self._set_estado_invalido(mensaje or "Error de validación")
            self.es_valido = False

    def validar_inmediato(self) -> bool:
        """
        Validar inmediatamente sin debouncing.
        
        Útil para validar antes de guardar.
        
        Returns:
            bool: True si es válido, False si no
        """
        self.timer.stop()
        self._validar()
        return self.es_valido

    def _set_estado_neutral(self):
        """Establecer estado neutral (sin validar)."""
        self.campo.setStyleSheet(STYLE_INPUT_NEUTRAL)
        self.label_error.setStyleSheet(STYLE_LABEL_HIDDEN)
        self.label_error.setText("")
        self.es_valido = False

    def _set_estado_valido(self):
        """Establecer estado válido (verde)."""
        self.campo.setStyleSheet(STYLE_INPUT_VALID)
        self.label_error.setStyleSheet(STYLE_LABEL_SUCCESS)
        self.label_error.setText(self.mensaje_exito)

    def _set_estado_invalido(self, mensaje: str):
        """Establecer estado inválido (rojo)."""
        self.campo.setStyleSheet(STYLE_INPUT_INVALID)
        self.label_error.setStyleSheet(STYLE_LABEL_ERROR)
        self.label_error.setText(f"⚠️ {mensaje}")

    def reset(self):
        """Resetear validador a estado inicial."""
        self.campo.setText("")
        self._set_estado_neutral()
        self.ultimo_valor = ""


# ========== VALIDADORES ESPECÍFICOS ==========

class ValidadorEmail(ValidadorCampo):
    """Validador específico para campos de email."""

    def __init__(self, campo: QLineEdit, label_error: QLabel):
        """
        Inicializar validador de email.
        
        Args:
            campo: QLineEdit para el email
            label_error: QLabel para mensajes
        """
        super().__init__(
            campo=campo,
            label_error=label_error,
            validador=validar_email,  # Usar directamente el validador de utils
            mensaje_exito="✓ Email válido",
            debounce_ms=500
        )


class ValidadorNombreCompleto(ValidadorCampo):
    """Validador específico para nombre completo."""

    def __init__(self, campo: QLineEdit, label_error: QLabel):
        """
        Inicializar validador de nombre completo.
        
        Args:
            campo: QLineEdit para el nombre
            label_error: QLabel para mensajes
        """
        super().__init__(
            campo=campo,
            label_error=label_error,
            validador=validar_nombre_completo,  # Usar directamente el validador de utils
            mensaje_exito="✓ Nombre válido",
            debounce_ms=500
        )


class ValidadorHorasContrato(ValidadorCampo):
    """Validador específico para horas de contrato."""

    def __init__(self, campo: QLineEdit, label_error: QLabel):
        """
        Inicializar validador de horas de contrato.
        
        Args:
            campo: QLineEdit para horas
            label_error: QLabel para mensajes
        """
        super().__init__(
            campo=campo,
            label_error=label_error,
            validador=self._validar_horas,
            mensaje_exito="✓ Horas válidas",
            debounce_ms=300  # Más rápido para números
        )

    @staticmethod
    def _validar_horas(horas_str: str) -> Tuple[bool, Optional[str]]:
        """Validar horas de contrato."""
        try:
            horas = float(horas_str)
            return validar_horas_contrato(horas)
        except ValueError:
            return False, "Debe ser un número válido"


class ValidadorRequerido(ValidadorCampo):
    """Validador genérico para campos requeridos."""

    def __init__(self, campo: QLineEdit, label_error: QLabel, nombre_campo: str = "Campo"):
        """
        Inicializar validador de campo requerido.
        
        Args:
            campo: QLineEdit a validar
            label_error: QLabel para mensajes
            nombre_campo: Nombre del campo para mensajes
        """
        self.nombre_campo = nombre_campo

        super().__init__(
            campo=campo,
            label_error=label_error,
            validador=self._validar_requerido,
            mensaje_exito="✓ Completo",
            debounce_ms=300
        )

    def _validar_requerido(self, valor: str) -> Tuple[bool, Optional[str]]:
        """Validar que el campo no esté vacío."""
        if not valor or not valor.strip():
            return False, f"{self.nombre_campo} es requerido"
        return True, None


# ========== VALIDADOR DE FORMULARIO COMPLETO ==========

class ValidadorFormulario:
    """
    Validador de formulario completo.
    
    Agrupa múltiples ValidadorCampo y proporciona validación
    de todo el formulario de una vez.
    """

    def __init__(self):
        """Inicializar validador de formulario."""
        self.validadores = []

    def agregar_validador(self, validador: ValidadorCampo):
        """
        Agregar un validador de campo.
        
        Args:
            validador: ValidadorCampo a agregar
        """
        self.validadores.append(validador)

    def validar_todo(self) -> Tuple[bool, list]:
        """
        Validar todos los campos del formulario.
        
        Returns:
            Tuple[bool, list]: (todos_validos, lista_de_errores)
        """
        errores = []

        for validador in self.validadores:
            if not validador.validar_inmediato():
                # Obtener mensaje de error del label
                mensaje_error = validador.label_error.text()
                if mensaje_error:
                    # Quitar el emoji ⚠️
                    mensaje_limpio = mensaje_error.replace("⚠️", "").strip()
                    errores.append(mensaje_limpio)

        todos_validos = len(errores) == 0
        return todos_validos, errores

    def reset_todo(self):
        """Resetear todos los validadores."""
        for validador in self.validadores:
            validador.reset()

    def son_todos_validos(self) -> bool:
        """
        Verificar si todos los campos son válidos actualmente.
        
        No ejecuta validación, solo verifica el estado actual.
        
        Returns:
            bool: True si todos son válidos, False si no
        """
        return all(v.es_valido for v in self.validadores)


# ========== HELPER FUNCTIONS ==========

def crear_label_error() -> QLabel:
    """
    Crear un QLabel configurado para mostrar mensajes de error.
    
    Returns:
        QLabel: Label configurado
    """
    label = QLabel()
    label.setStyleSheet(STYLE_LABEL_HIDDEN)
    label.setWordWrap(True)
    label.setMaximumHeight(30)
    return label


def aplicar_validacion_email(campo: QLineEdit) -> Tuple[ValidadorEmail, QLabel]:
    """
    Helper para aplicar validación de email a un campo.
    
    Args:
        campo: QLineEdit a validar
    
    Returns:
        Tuple[ValidadorEmail, QLabel]: (validador, label_error)
    """
    label_error = crear_label_error()
    validador = ValidadorEmail(campo, label_error)
    return validador, label_error


def aplicar_validacion_nombre(campo: QLineEdit) -> Tuple[ValidadorNombreCompleto, QLabel]:
    """
    Helper para aplicar validación de nombre completo a un campo.
    
    Args:
        campo: QLineEdit a validar
    
    Returns:
        Tuple[ValidadorNombreCompleto, QLabel]: (validador, label_error)
    """
    label_error = crear_label_error()
    validador = ValidadorNombreCompleto(campo, label_error)
    return validador, label_error


def aplicar_validacion_horas(campo: QLineEdit) -> Tuple[ValidadorHorasContrato, QLabel]:
    """
    Helper para aplicar validación de horas a un campo.
    
    Args:
        campo: QLineEdit a validar
    
    Returns:
        Tuple[ValidadorHorasContrato, QLabel]: (validador, label_error)
    """
    label_error = crear_label_error()
    validador = ValidadorHorasContrato(campo, label_error)
    return validador, label_error


def aplicar_validacion_requerido(
    campo: QLineEdit,
    nombre_campo: str = "Campo"
) -> Tuple[ValidadorRequerido, QLabel]:
    """
    Helper para aplicar validación de campo requerido.
    
    Args:
        campo: QLineEdit a validar
        nombre_campo: Nombre del campo para mensajes
    
    Returns:
        Tuple[ValidadorRequerido, QLabel]: (validador, label_error)
    """
    label_error = crear_label_error()
    validador = ValidadorRequerido(campo, label_error, nombre_campo)
    return validador, label_error
