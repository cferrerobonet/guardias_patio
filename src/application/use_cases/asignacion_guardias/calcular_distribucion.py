"""
Use Case: Calcular distribución de guardias por profesor.

Calcula cuántas guardias debe hacer cada profesor según su jornada y otros factores.
"""

from services.calculador_guardias import (
    calcular_guardias_por_profesor as calcular_servicio,
)
from services.calculador_guardias import (
    obtener_estadisticas,
)
from sqlalchemy.orm import Session
from utils.exceptions import BusinessLogicError

from application.dtos.asignacion_guardias_dto import DistribucionDTO


class CalcularDistribucionUseCase:
    """
    Caso de uso para calcular la distribución de guardias entre profesores.

    Calcula cuántas guardias debe hacer cada profesor basándose en:
    - Porcentaje de jornada
    - Turno de trabajo (mañana, tarde, completo)
    - Factor de ajuste por tutoría
    - Total de slots disponibles
    """

    def __init__(self, session: Session):
        """
        Inicializar el caso de uso.

        Args:
            session: Sesión de SQLAlchemy para acceso a base de datos
        """
        self.session = session

    def execute(self) -> DistribucionDTO:
        """
        Ejecutar el cálculo de distribución.

        Returns:
            DistribucionDTO con la distribución calculada

        Raises:
            BusinessLogicError: Si no hay datos suficientes para calcular
        """
        # Validar que hay datos
        stats = obtener_estadisticas(self.session)
        if not stats or stats.get("slots_totales", 0) == 0:
            raise BusinessLogicError(
                "Debe configurar el curso, profesores y zonas antes de calcular."
            )

        try:
            # Usar el servicio existente que ya tiene toda la lógica
            distribucion = calcular_servicio(self.session)

            # Calcular total de guardias
            total_guardias = sum(distribucion.values())

            return DistribucionDTO(
                distribucion=distribucion,
                total_guardias=total_guardias,
                slots_totales=stats.get("slots_totales", 0),
            )

        except ValueError as e:
            raise BusinessLogicError(
                f"Error al calcular la distribución: {str(e)}"
            ) from e
