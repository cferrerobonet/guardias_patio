"""
Dependency Injection Container

Contenedor centralizado para la inyección de dependencias usando dependency-injector.
Gestiona el lifecycle de sesiones, repositorios y servicios.

Ejemplo de uso:
    from infrastructure.container import Container

    # Inicializar el contenedor con una SessionFactory
    container = Container()
    container.config.from_dict({"db_session_factory": SessionFactory})

    # Obtener un repositorio
    profesor_repo = container.profesor_repository()

    # Obtener la factoría de repositorios
    factory = container.repository_factory()
"""

from dependency_injector import containers, providers

from infrastructure.repositories import (
    SQLAlchemyAusenciaRepository,
    SQLAlchemyConfiguracionRepository,
    SQLAlchemyCursoEscolarRepository,
    SQLAlchemyGuardiaRepository,
    SQLAlchemyProfesorRepository,
    SQLAlchemyZonaRepository,
)
from infrastructure.repositories.repository_factory import RepositoryFactory


class Container(containers.DeclarativeContainer):
    """
    Contenedor de inyección de dependencias.

    Gestiona el lifecycle de:
    - Sesiones de base de datos
    - Repositorios
    - Factoría de repositorios
    """

    config = providers.Configuration()

    # ==================== Base de Datos ====================

    db_session = providers.Callable(config.db_session_factory)
    """
    Proveedor de sesiones de base de datos.

    Forma de uso:
        container.config.from_dict({"db_session_factory": SessionFactory})
        session = container.db_session()
    """

    # ==================== Repositorios ====================

    profesor_repository = providers.Factory(
        SQLAlchemyProfesorRepository,
        session=db_session,
    )
    """Repositorio de profesores."""

    zona_repository = providers.Factory(
        SQLAlchemyZonaRepository,
        session=db_session,
    )
    """Repositorio de zonas."""

    guardia_repository = providers.Factory(
        SQLAlchemyGuardiaRepository,
        session=db_session,
    )
    """Repositorio de guardias."""

    ausencia_repository = providers.Factory(
        SQLAlchemyAusenciaRepository,
        session=db_session,
    )
    """Repositorio de ausencias."""

    configuracion_repository = providers.Factory(
        SQLAlchemyConfiguracionRepository,
        session=db_session,
    )
    """Repositorio de configuración."""

    curso_escolar_repository = providers.Factory(
        SQLAlchemyCursoEscolarRepository,
        session=db_session,
    )
    """Repositorio de cursos escolares."""

    # ==================== Factoría de Repositorios ====================

    repository_factory = providers.Factory(
        RepositoryFactory,
        session=db_session,
    )
    """Factoría centralizada de repositorios (compatible con código legacy)."""
