"""
Application Factories - Dependency Injection

Este módulo proporciona funciones factory para crear Use Cases
con las implementaciones correctas de repositorios inyectadas.

Esto respeta el principio de Inversión de Dependencias (DIP):
- Use Cases dependen de interfaces (domain/repositories)
- Factories inyectan las implementaciones (infrastructure/repositories)

Uso:
    from application.factories import crear_listar_profesores_use_case

    use_case = crear_listar_profesores_use_case(session)
    resultado = use_case.execute()
"""

from infrastructure.mappers import ProfesorMapper
from infrastructure.repositories import (
    SQLAlchemyGuardiaRepository,
    SQLAlchemyProfesorRepository,
    SQLAlchemyZonaRepository,
)
from sqlalchemy.orm import Session


def crear_obtener_profesor_use_case(session: Session):
    """
    Factory para ObtenerProfesorUseCase.

    Args:
        session: Sesión de SQLAlchemy

    Returns:
        ObtenerProfesorUseCase configurado
    """
    from application.use_cases.profesor.obtener_profesor import ObtenerProfesorUseCase

    repository = SQLAlchemyProfesorRepository(session)
    return ObtenerProfesorUseCase(repository)


def crear_listar_profesores_use_case(session: Session):
    """
    Factory para ListarProfesoresUseCase.

    Args:
        session: Sesión de SQLAlchemy

    Returns:
        ListarProfesoresUseCase configurado
    """
    from application.use_cases.profesor.listar_profesores import ListarProfesoresUseCase

    repository = SQLAlchemyProfesorRepository(session)
    return ListarProfesoresUseCase(repository)


def crear_crear_profesor_use_case(session: Session):
    """
    Factory para CrearProfesorUseCase.

    Args:
        session: Sesión de SQLAlchemy

    Returns:
        CrearProfesorUseCase configurado
    """
    from application.use_cases.profesor.crear_profesor import CrearProfesorUseCase

    repository = SQLAlchemyProfesorRepository(session)
    mapper = ProfesorMapper()
    return CrearProfesorUseCase(session, repository, mapper)


def crear_obtener_guardias_use_case(session: Session):
    """
    Factory para ObtenerGuardiasUseCase.

    Args:
        session: Sesión de SQLAlchemy

    Returns:
        ObtenerGuardiasUseCase configurado
    """
    from application.use_cases.guardia.obtener_guardias import ObtenerGuardiasUseCase

    guardia_repo = SQLAlchemyGuardiaRepository(session)
    profesor_repo = SQLAlchemyProfesorRepository(session)
    zona_repo = SQLAlchemyZonaRepository(session)
    return ObtenerGuardiasUseCase(guardia_repo, profesor_repo, zona_repo)


def crear_asignar_guardia_use_case(session: Session):
    """
    Factory para AsignarGuardiaUseCase.

    Args:
        session: Sesión de SQLAlchemy

    Returns:
        AsignarGuardiaUseCase configurado
    """
    from application.use_cases.guardia.asignar_guardia import AsignarGuardiaUseCase

    profesor_repo = SQLAlchemyProfesorRepository(session)
    zona_repo = SQLAlchemyZonaRepository(session)
    guardia_repo = SQLAlchemyGuardiaRepository(session)
    return AsignarGuardiaUseCase(session, profesor_repo, zona_repo, guardia_repo)
