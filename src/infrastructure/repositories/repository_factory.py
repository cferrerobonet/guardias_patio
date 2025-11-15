"""
Repository Factory

Factoría centralizada para crear instancias de repositorios.
Facilita la inyección de dependencias y el testing.
"""

from sqlalchemy.orm import Session

from infrastructure.repositories import (
    SQLAlchemyAusenciaRepository,
    SQLAlchemyConfiguracionRepository,
    SQLAlchemyCursoEscolarRepository,
    SQLAlchemyGuardiaRepository,
    SQLAlchemyProfesorRepository,
    SQLAlchemyZonaRepository,
)


class RepositoryFactory:
    """
    Factoría para crear repositorios con SQLAlchemy.

    Centraliza la creación de repositorios para facilitar:
    - Inyección de dependencias
    - Testing con mocks
    - Cambio de implementación
    """

    def __init__(self, session: Session):
        """
        Inicializa la factoría con una sesión de SQLAlchemy.

        Args:
            session: Sesión activa de SQLAlchemy
        """
        self.session = session

    def create_profesor_repository(self) -> SQLAlchemyProfesorRepository:
        """Crea repositorio de profesores."""
        return SQLAlchemyProfesorRepository(self.session)

    def create_zona_repository(self) -> SQLAlchemyZonaRepository:
        """Crea repositorio de zonas."""
        return SQLAlchemyZonaRepository(self.session)

    def create_guardia_repository(self) -> SQLAlchemyGuardiaRepository:
        """Crea repositorio de guardias."""
        return SQLAlchemyGuardiaRepository(self.session)

    def create_ausencia_repository(self) -> SQLAlchemyAusenciaRepository:
        """Crea repositorio de ausencias."""
        return SQLAlchemyAusenciaRepository(self.session)

    def create_configuracion_repository(self) -> SQLAlchemyConfiguracionRepository:
        """Crea repositorio de configuración."""
        return SQLAlchemyConfiguracionRepository(self.session)

    def create_curso_escolar_repository(self) -> SQLAlchemyCursoEscolarRepository:
        """Crea repositorio de cursos escolares."""
        return SQLAlchemyCursoEscolarRepository(self.session)
