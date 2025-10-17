"""
Sistema centralizado de excepciones personalizadas.

Proporciona una jerarquía completa de excepciones con contexto rico,
traceback mejorado y soporte para logging estructurado.

Jerarquía:
    GuardiasBaseException
    ├── ValidationError
    │   ├── InvalidEmailError
    │   ├── InvalidHorasContratoError
    │   └── InvalidNombreError
    ├── NotFoundError
    │   ├── ProfesorNotFoundError
    │   ├── ZonaNotFoundError
    │   └── GuardiaNotFoundError
    ├── BusinessLogicError
    │   ├── MaxGuardiasDiaExceededError
    │   ├── ProfesorAusenteError
    │   └── NoDisponibilidadError
    ├── DatabaseError
    │   ├── ConnectionError
    │   ├── TransactionError
    │   └── IntegrityError
    └── InfrastructureError
        ├── CacheError
        └── ExportError

Uso:
    from core.exceptions import ProfesorNotFoundError

    raise ProfesorNotFoundError(
        profesor_id=123,
        message="Profesor no encontrado en la base de datos"
    )
"""

from typing import Any, Optional


class GuardiasBaseException(Exception):
    """
    Excepción base para todas las excepciones de la aplicación.

    Attributes:
        message: Mensaje descriptivo del error
        code: Código de error único (para i18n y tracking)
        context: Contexto adicional del error (dict)
        original_error: Excepción original si es wrapping
    """

    default_message = "Ha ocurrido un error en la aplicación"
    default_code = "GUARDIAS_ERROR"

    def __init__(
        self,
        message: Optional[str] = None,
        code: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
        **kwargs,
    ):
        self.message = message or self.default_message
        self.code = code or self.default_code
        self.context = context or {}
        self.original_error = original_error

        # Añadir kwargs al contexto
        self.context.update(kwargs)

        super().__init__(self.message)

    def __str__(self) -> str:
        """Representación string con contexto."""
        base_msg = f"[{self.code}] {self.message}"
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            base_msg += f" ({context_str})"
        return base_msg

    def __repr__(self) -> str:
        """Representación para debugging."""
        return (
            f"{self.__class__.__name__}("
            f"message='{self.message}', "
            f"code='{self.code}', "
            f"context={self.context})"
        )

    def to_dict(self) -> dict[str, Any]:
        """Convierte la excepción a diccionario (útil para APIs/logging)."""
        return {
            "error_type": self.__class__.__name__,
            "code": self.code,
            "message": self.message,
            "context": self.context,
        }


# ============================================================================
# EXCEPCIONES DE VALIDACIÓN
# ============================================================================


class ValidationError(GuardiasBaseException):
    """Error de validación de datos."""

    default_message = "Error de validación"
    default_code = "VALIDATION_ERROR"


class InvalidEmailError(ValidationError):
    """Email inválido."""

    default_message = "El email proporcionado no es válido"
    default_code = "INVALID_EMAIL"


class InvalidHorasContratoError(ValidationError):
    """Horas de contrato inválidas."""

    default_message = "Las horas de contrato no son válidas"
    default_code = "INVALID_HORAS_CONTRATO"


class InvalidNombreError(ValidationError):
    """Nombre inválido."""

    default_message = "El nombre proporcionado no es válido"
    default_code = "INVALID_NOMBRE"


class InvalidTurnoError(ValidationError):
    """Turno inválido."""

    default_message = "El turno especificado no es válido"
    default_code = "INVALID_TURNO"


class InvalidFechaError(ValidationError):
    """Fecha inválida."""

    default_message = "La fecha proporcionada no es válida"
    default_code = "INVALID_FECHA"


class InvalidMatrizHorarioError(ValidationError):
    """Matriz horario día×recreo inválida."""

    default_message = "La matriz de horario no es válida"
    default_code = "INVALID_MATRIZ_HORARIO"


# ============================================================================
# EXCEPCIONES DE NOT FOUND
# ============================================================================


class NotFoundError(GuardiasBaseException):
    """Entidad no encontrada."""

    default_message = "El elemento solicitado no fue encontrado"
    default_code = "NOT_FOUND"


class ProfesorNotFoundError(NotFoundError):
    """Profesor no encontrado."""

    default_message = "El profesor no fue encontrado"
    default_code = "PROFESOR_NOT_FOUND"

    def __init__(self, profesor_id: Optional[int] = None, **kwargs):
        if profesor_id:
            kwargs["profesor_id"] = profesor_id
        super().__init__(**kwargs)


class ZonaNotFoundError(NotFoundError):
    """Zona no encontrada."""

    default_message = "La zona no fue encontrada"
    default_code = "ZONA_NOT_FOUND"

    def __init__(self, zona_id: Optional[int] = None, **kwargs):
        if zona_id:
            kwargs["zona_id"] = zona_id
        super().__init__(**kwargs)


class GuardiaNotFoundError(NotFoundError):
    """Guardia no encontrada."""

    default_message = "La guardia no fue encontrada"
    default_code = "GUARDIA_NOT_FOUND"

    def __init__(self, guardia_id: Optional[int] = None, **kwargs):
        if guardia_id:
            kwargs["guardia_id"] = guardia_id
        super().__init__(**kwargs)


class AusenciaNotFoundError(NotFoundError):
    """Ausencia no encontrada."""

    default_message = "La ausencia no fue encontrada"
    default_code = "AUSENCIA_NOT_FOUND"

    def __init__(self, ausencia_id: Optional[int] = None, **kwargs):
        if ausencia_id:
            kwargs["ausencia_id"] = ausencia_id
        super().__init__(**kwargs)


# ============================================================================
# EXCEPCIONES DE LÓGICA DE NEGOCIO
# ============================================================================


class BusinessLogicError(GuardiasBaseException):
    """Error en reglas de negocio."""

    default_message = "Error en la lógica de negocio"
    default_code = "BUSINESS_LOGIC_ERROR"


class MaxGuardiasDiaExceededError(BusinessLogicError):
    """Excedido el máximo de guardias por día."""

    default_message = "Se ha excedido el máximo de guardias permitidas por día"
    default_code = "MAX_GUARDIAS_DIA_EXCEEDED"

    def __init__(self, profesor_id: Optional[int] = None, fecha: Optional[str] = None, **kwargs):
        if profesor_id:
            kwargs["profesor_id"] = profesor_id
        if fecha:
            kwargs["fecha"] = fecha
        super().__init__(**kwargs)


class ProfesorAusenteError(BusinessLogicError):
    """Profesor ausente en la fecha solicitada."""

    default_message = "El profesor está ausente en la fecha indicada"
    default_code = "PROFESOR_AUSENTE"

    def __init__(
        self,
        profesor_id: Optional[int] = None,
        fecha: Optional[str] = None,
        ausencia_id: Optional[int] = None,
        **kwargs,
    ):
        if profesor_id:
            kwargs["profesor_id"] = profesor_id
        if fecha:
            kwargs["fecha"] = fecha
        if ausencia_id:
            kwargs["ausencia_id"] = ausencia_id
        super().__init__(**kwargs)


class NoDisponibilidadError(BusinessLogicError):
    """No hay profesores disponibles."""

    default_message = "No hay profesores disponibles para la asignación"
    default_code = "NO_DISPONIBILIDAD"


class GuardiaDuplicadaError(BusinessLogicError):
    """Guardia duplicada detectada."""

    default_message = "Ya existe una guardia para este profesor en esta fecha/recreo"
    default_code = "GUARDIA_DUPLICADA"


class AsignacionImpossibleError(BusinessLogicError):
    """No se pudo completar la asignación."""

    default_message = "No se pudo completar la asignación de guardias"
    default_code = "ASIGNACION_IMPOSSIBLE"


class GuardiaConflictError(BusinessLogicError):
    """Conflicto en asignación de guardia."""

    default_message = "Conflicto al asignar guardia (profesor u zona ya ocupados)"
    default_code = "GUARDIA_CONFLICT"

    def __init__(
        self,
        guardia_id: Optional[int] = None,
        fecha: Optional[str] = None,
        **kwargs,
    ):
        if guardia_id:
            kwargs["guardia_id"] = guardia_id
        if fecha:
            kwargs["fecha"] = fecha
        super().__init__(**kwargs)


class GuardiaInvalidaError(BusinessLogicError):
    """Guardia inválida."""

    default_message = "La guardia no es válida (faltan datos requeridos)"
    default_code = "GUARDIA_INVALIDA"

    def __init__(self, guardia_id: Optional[int] = None, **kwargs):
        if guardia_id:
            kwargs["guardia_id"] = guardia_id
        super().__init__(**kwargs)


# ============================================================================
# EXCEPCIONES DE BASE DE DATOS
# ============================================================================


class DatabaseError(GuardiasBaseException):
    """Error de base de datos."""

    default_message = "Error al acceder a la base de datos"
    default_code = "DATABASE_ERROR"


class ConnectionError(DatabaseError):
    """Error de conexión a base de datos."""

    default_message = "No se pudo conectar a la base de datos"
    default_code = "DB_CONNECTION_ERROR"


class TransactionError(DatabaseError):
    """Error en transacción."""

    default_message = "Error al ejecutar la transacción"
    default_code = "DB_TRANSACTION_ERROR"


class IntegrityError(DatabaseError):
    """Error de integridad de datos."""

    default_message = "Violación de restricción de integridad"
    default_code = "DB_INTEGRITY_ERROR"


class QueryError(DatabaseError):
    """Error al ejecutar query."""

    default_message = "Error al ejecutar la consulta"
    default_code = "DB_QUERY_ERROR"


# ============================================================================
# EXCEPCIONES DE INFRAESTRUCTURA
# ============================================================================


class InfrastructureError(GuardiasBaseException):
    """Error de infraestructura."""

    default_message = "Error en la infraestructura"
    default_code = "INFRASTRUCTURE_ERROR"


class CacheError(InfrastructureError):
    """Error en el sistema de cache."""

    default_message = "Error al acceder al cache"
    default_code = "CACHE_ERROR"


class ExportError(InfrastructureError):
    """Error al exportar datos."""

    default_message = "Error al exportar los datos"
    default_code = "EXPORT_ERROR"

    def __init__(self, format: Optional[str] = None, **kwargs):
        if format:
            kwargs["format"] = format
        super().__init__(**kwargs)


class ImportError(InfrastructureError):
    """Error al importar datos."""

    default_message = "Error al importar los datos"
    default_code = "IMPORT_ERROR"

    def __init__(self, format: Optional[str] = None, **kwargs):
        if format:
            kwargs["format"] = format
        super().__init__(**kwargs)


class FileSystemError(InfrastructureError):
    """Error del sistema de archivos."""

    default_message = "Error al acceder al sistema de archivos"
    default_code = "FILESYSTEM_ERROR"


# ============================================================================
# UTILIDADES
# ============================================================================


def wrap_exception(
    original_error: Exception, new_exception_class: type[GuardiasBaseException], **kwargs
) -> GuardiasBaseException:
    """
    Envuelve una excepción externa en una excepción de la aplicación.

    Args:
        original_error: Excepción original
        new_exception_class: Clase de excepción destino
        **kwargs: Contexto adicional

    Returns:
        Nueva excepción con contexto

    Example:
        try:
            session.query(Profesor).get(id)
        except SQLAlchemyError as e:
            raise wrap_exception(e, DatabaseError, profesor_id=id)
    """
    return new_exception_class(
        message=str(original_error), original_error=original_error, context=kwargs
    )


def format_exception_for_user(error: Exception) -> str:
    """
    Formatea una excepción para mostrar al usuario.

    Args:
        error: Excepción a formatear

    Returns:
        Mensaje amigable para el usuario

    Example:
        try:
            # código
        except Exception as e:
            QMessageBox.warning(self, "Error", format_exception_for_user(e))
    """
    if isinstance(error, GuardiasBaseException):
        return error.message

    # Excepciones genéricas
    return f"Error inesperado: {str(error)}"


def is_user_error(error: Exception) -> bool:
    """
    Determina si un error es causado por el usuario (vs sistema).

    Args:
        error: Excepción a evaluar

    Returns:
        True si es error de usuario (validación, not found)

    Example:
        try:
            # código
        except Exception as e:
            if is_user_error(e):
                level = "warning"
            else:
                level = "error"
                notify_sentry(e)
    """
    return isinstance(error, (ValidationError, NotFoundError))


__all__ = [
    # Base
    "GuardiasBaseException",
    # Validación
    "ValidationError",
    "InvalidEmailError",
    "InvalidHorasContratoError",
    "InvalidNombreError",
    "InvalidTurnoError",
    "InvalidFechaError",
    "InvalidMatrizHorarioError",
    # Not Found
    "NotFoundError",
    "ProfesorNotFoundError",
    "ZonaNotFoundError",
    "GuardiaNotFoundError",
    "AusenciaNotFoundError",
    # Business Logic
    "BusinessLogicError",
    "MaxGuardiasDiaExceededError",
    "ProfesorAusenteError",
    "NoDisponibilidadError",
    "GuardiaDuplicadaError",
    "AsignacionImpossibleError",
    # Database
    "DatabaseError",
    "ConnectionError",
    "TransactionError",
    "IntegrityError",
    "QueryError",
    # Infrastructure
    "InfrastructureError",
    "CacheError",
    "ExportError",
    "ImportError",
    "FileSystemError",
    # Utilities
    "wrap_exception",
    "format_exception_for_user",
    "is_user_error",
]
