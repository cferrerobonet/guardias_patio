"""
Excepciones personalizadas para la aplicación de Guardias de Patio.

Define excepciones específicas del dominio para facilitar el manejo
de errores y proporcionar mensajes más claros.
"""


class GuardiasBaseException(Exception):
    """Excepción base para todas las excepciones de la aplicación."""

    def __init__(self, message: str, detalles: str | None = None):
        self.message = message
        self.detalles = detalles
        super().__init__(self.message)

    def __str__(self):
        if self.detalles:
            return f"{self.message}: {self.detalles}"
        return self.message


class ValidationError(GuardiasBaseException):
    """Error de validación de datos de entrada."""

    pass


class NotFoundError(GuardiasBaseException):
    """Error cuando no se encuentra un recurso solicitado."""

    pass


class BusinessLogicError(GuardiasBaseException):
    """Error en la lógica de negocio de la aplicación."""

    pass


class DatabaseError(GuardiasBaseException):
    """Error relacionado con operaciones de base de datos."""

    pass


class ConfiguracionError(GuardiasBaseException):
    """Error en la configuración de la aplicación."""

    pass


class ProfesorNotFoundError(GuardiasBaseException):
    """Profesor no encontrado en la base de datos."""

    def __init__(self, profesor_id: int):
        super().__init__(
            f"Profesor con ID {profesor_id} no encontrado",
            f"No existe un profesor con el ID {profesor_id} en la base de datos",
        )
        self.profesor_id = profesor_id


class ZonaNotFoundError(GuardiasBaseException):
    """Zona no encontrada en la base de datos."""

    def __init__(self, zona_id: int):
        super().__init__(
            f"Zona con ID {zona_id} no encontrada",
            f"No existe una zona con el ID {zona_id} en la base de datos",
        )
        self.zona_id = zona_id


class GuardiaConflictError(GuardiasBaseException):
    """Conflicto al asignar una guardia."""

    pass


class MaxGuardiasExceededError(GuardiaConflictError):
    """Se excedió el máximo de guardias permitidas por día."""

    def __init__(self, profesor_nombre: str, fecha: str):
        super().__init__(
            f"Máximo de guardias excedido para {profesor_nombre}",
            f"El profesor {profesor_nombre} ya tiene asignada una guardia el {fecha}",
        )


class DuplicateGuardiaError(GuardiaConflictError):
    """Se intentó crear una guardia duplicada."""

    def __init__(self, profesor_nombre: str, fecha: str, turno: str, recreo: int):
        super().__init__(
            "Guardia duplicada detectada",
            f"El profesor {profesor_nombre} ya tiene una guardia el {fecha} "
            f"en turno {turno}, recreo {recreo}",
        )


class InsufficientProfesoresError(GuardiasBaseException):
    """No hay suficientes profesores disponibles."""

    pass


class ExportError(GuardiasBaseException):
    """Error durante la exportación de datos."""

    pass


class ImportError(GuardiasBaseException):
    """Error durante la importación de datos."""

    pass
