"""
Domain Layer - Capa de Dominio

Esta capa contiene la lógica de negocio pura, independiente de frameworks
y detalles de implementación.

Estructura:
- entities/: Entidades del dominio con identidad y lógica de negocio
- value_objects/: Objetos de valor inmutables sin identidad
- repositories/: Interfaces de repositorios (abstracciones)
- services/: Servicios de dominio con lógica compleja
"""

from . import entities, repositories, value_objects

__all__ = [
    "entities",
    "value_objects",
    "repositories",
]
