"""
Wiring automático del contenedor DI (ARQ-04 Phase 2)

Este módulo configura e inyecta dependencias mediante dependency-injector.
Proporciona funciones para:
1. Configurar el container con una SessionFactory  
2. Obtener servicios/repositorios previamente configurados
3. Permitir acceso global al container sin imports circulares

Uso:
    from database.db_manager import initialize_user_database
    from infrastructure.wiring import setup_container, get_container

    # Después de login y auth
    engine, SessionFactory = initialize_user_database(username)
    
    # Configurar container
    setup_container(SessionFactory)
    
    # Acceder a servicios
    container = get_container()
    profesor_repo = container.profesor_repository()
    stats_service = container.estadisticas_service()

Nota: Esta es la "fase 2 opcional" de ARQ-04. Main.py todavía usa Session
directamente (backward compatible). Wiring DI es opt-in por ahora.
"""

from typing import Callable, Optional

from core.logging import get_logger

logger = get_logger(__name__)

# Global container instance (singleton)
_container_instance = None


def setup_container(session_factory: Callable) -> None:
    """
    Configura el contenedor DI con una SessionFactory específica.
    
    Debe llamarse DESPUÉS de initialize_user_database() en main.py.
    
    Args:
        session_factory: Callable que devuelve una nueva sesión de SQLAlchemy
    """
    global _container_instance
    
    try:
        from infrastructure.container import Container
        
        # Crear instancia del container
        _container_instance = Container()
        
        # Configurar el provider de sesión
        _container_instance.config.from_dict({
            "db_session_factory": session_factory
        })
        
        logger.info("✅ Contenedor DI configurado exitosamente")
        
    except ImportError as e:
        logger.error(f"⚠ dependency-injector no disponible. Wiring deshabilitado: {e}")
        _container_instance = None


def get_container() -> Optional["Container"]:
    """
    Devuelve la instancia global del contenedor.
    
    Returns:
        Container configurado, o None si no ha sido inicializado
    """
    global _container_instance
    
    if _container_instance is None:
        logger.warning(
            "⚠ Contenedor no inicializado. Llama a setup_container() después de login."
        )
        return None
    
    return _container_instance


def get_profesor_repository():
    """Factory para repositorio de profesores (con DI)."""
    container = get_container()
    if not container:
        return None
    return container.profesor_repository()


def get_guardia_repository():
    """Factory para repositorio de guardias (con DI)."""
    container = get_container()
    if not container:
        return None
    return container.guardia_repository()


def get_ausencia_repository():
    """Factory para repositorio de ausencias (con DI)."""
    container = get_container()
    if not container:
        return None
    return container.ausencia_repository()


def get_zona_repository():
    """Factory para repositorio de zonas (con DI)."""
    container = get_container()
    if not container:
        return None
    return container.zona_repository()


def get_configuracion_repository():
    """Factory para repositorio de configuración (con DI)."""
    container = get_container()
    if not container:
        return None
    return container.configuracion_repository()


def get_curso_repository():
    """Factory para repositorio de cursos (con DI)."""
    container = get_container()
    if not container:
        return None
    return container.curso_escolar_repository()


def get_repository_factory():
    """Factory para RepositoryFactory (con DI)."""
    container = get_container()
    if not container:
        return None
    return container.repository_factory()


# FUTURE: Agregar más servicios según sea necesario
# def get_estadisticas_service():
#     container = get_container()
#     if not container:
#         return None
#     return container.estadisticas_service()
