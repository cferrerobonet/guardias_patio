"""
DTOs y Schemas con Pydantic para validación de datos.

Este módulo contiene los Data Transfer Objects (DTOs) definidos con Pydantic
para validación estricta de tipos y datos en las fronteras del sistema.

Uso:
    Los schemas se usan principalmente en:
    - APIs REST (entrada/salida)
    - Importación/exportación de datos
    - Validación de configuraciones
    - Conversión entre capas (presentation <-> application)

Notas:
    - Los schemas NO reemplazan las entidades de dominio
    - Las entidades contienen lógica de negocio, los schemas son solo datos
    - Usar .model_validate() para validar dicts
    - Usar .model_dump() para serializar a dict
"""

from .configuracion_schema import ConfiguracionSchema
from .guardia_schema import GuardiaCreateSchema, GuardiaSchema, GuardiaUpdateSchema
from .profesor_schema import ProfesorCreateSchema, ProfesorSchema, ProfesorUpdateSchema

__all__ = [
    # Profesor schemas
    "ProfesorSchema",
    "ProfesorCreateSchema",
    "ProfesorUpdateSchema",
    # Guardia schemas
    "GuardiaSchema",
    "GuardiaCreateSchema",
    "GuardiaUpdateSchema",
    # Configuración schema
    "ConfiguracionSchema",
]
