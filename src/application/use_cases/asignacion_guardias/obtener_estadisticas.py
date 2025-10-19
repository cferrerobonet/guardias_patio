"""
Use Case: Obtener estadísticas del curso.

Calcula y devuelve estadísticas sobre días lectivos, recreos, zonas y profesores.
"""

from sqlalchemy.orm import Session

from application.dtos.asignacion_guardias_dto import EstadisticasDTO
from core.observability import with_metrics
from services.calculador_guardias import obtener_estadisticas as obtener_stats_servicio
from utils.exceptions import BusinessLogicError


class ObtenerEstadisticasUseCase:
    """
    Caso de uso para obtener estadísticas del curso.

    Calcula información sobre días lectivos, recreos, zonas y profesores
    disponibles para la asignación de guardias.
    """

    def __init__(self, session: Session):
        """
        Inicializar el caso de uso.

        Args:
            session: Sesión de SQLAlchemy para acceso a base de datos
        """
        self.session = session

    @with_metrics("obtener_estadisticas")
    def execute(self) -> EstadisticasDTO:
        """
        Ejecutar la obtención de estadísticas.

        Returns:
            EstadisticasDTO con las estadísticas del curso

        Raises:
            BusinessLogicError: Si no hay configuración o datos insuficientes
        """
        try:
            # Usar el servicio existente que ya tiene toda la lógica
            stats = obtener_stats_servicio(self.session)

            if not stats:
                raise BusinessLogicError(
                    "No hay configuración del curso. "
                    "Por favor, configure primero las fechas y recreos."
                )

            # Convertir a DTO
            return EstadisticasDTO(
                dias_lectivos=stats.get("dias_lectivos", 0),
                recreos_manana=stats.get("recreos_manana", 0),
                recreos_tarde=stats.get("recreos_tarde", 0),
                num_zonas=stats.get("num_zonas", 0),
                num_profesores=stats.get("num_profesores", 0),
                slots_totales=stats.get("slots_totales", 0),
            )

        except ValueError as e:
            raise BusinessLogicError(f"Error al calcular estadísticas: {str(e)}") from e
