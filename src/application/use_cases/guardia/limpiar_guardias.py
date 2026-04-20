"""
Limpiar Guardias Use Case

Permite eliminar todas las guardias del sistema.
Útil para empezar de cero o liberar zonas/profesores.
"""

from core.logging import get_logger
from core.observability import with_metrics
from core.observability import business_metrics
from domain.repositories import IGuardiaRepository

logger = get_logger(__name__)


class LimpiarGuardiasUseCase:
    """
    Use Case para eliminar todas las guardias del sistema.

    Esta operación es útil cuando se necesita:
    - Empezar de cero con la generación de guardias
    - Liberar zonas y profesores para poder eliminarlos
    - Limpiar datos de prueba
    """

    def __init__(self, guardia_repository: IGuardiaRepository):
        """
        Inicializa el use case.

        Args:
            guardia_repository: Repositorio de guardias
        """
        self.guardia_repository = guardia_repository

    @with_metrics(operation="limpiar_guardias")
    def execute(self) -> int:
        """
        Elimina todas las guardias del sistema.

        Returns:
            Número de guardias eliminadas

        Raises:
            DatabaseError: Si hay un error en la base de datos
        """
        logger.info("Iniciando limpieza de guardias")

        # Eliminar todas las guardias
        count = self.guardia_repository.delete_all()

        logger.info(f"Limpieza completada: {count} guardias eliminadas")
        business_metrics.guardias_limpiadas(total=count)

        return count
