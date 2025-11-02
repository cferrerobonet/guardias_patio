"""
Use Case: Obtener Configuración.

Obtiene la configuración actual del curso escolar.
Con caching para optimizar lecturas frecuentes.
"""

from core.exceptions import NotFoundError
from core.logging import get_logger
from core.observability import with_metrics
from models.models import Configuracion
from sqlalchemy.orm import Session
from utils.repository_cache import cache_configuracion

from application.dtos.configuracion_dto import ConfiguracionDTO

logger = get_logger(__name__)


class ObtenerConfiguracionUseCase:
    """
    Use Case para obtener la configuración del curso.

    Solo puede haber una configuración en el sistema.
    """

    def __init__(self, session: Session):
        """
        Inicializa el use case.

        Args:
            session: Sesión de SQLAlchemy
        """
        self.session = session

    @with_metrics("obtener_configuracion")
    @cache_configuracion(ttl=600)  # Cache por 10 minutos
    def execute(self) -> ConfiguracionDTO:
        """
        Obtiene la configuración actual (con caching).

        Returns:
            ConfiguracionDTO con los datos de configuración

        Raises:
            NotFoundError: Si no existe configuración
        """
        logger.info("Obteniendo configuración del curso")

        config = self.session.query(Configuracion).first()

        if not config:
            logger.warning("No se encontró configuración")
            raise NotFoundError("No existe configuración. Por favor, créela primero.")

        dto = ConfiguracionDTO(
            id=config.id,
            fecha_inicio_curso=config.fecha_inicio_curso,
            fecha_fin_curso=config.fecha_fin_curso,
            hora_recreo1_manana=config.hora_recreo1_manana,
            hora_recreo2_manana=config.hora_recreo2_manana,
            hora_recreo1_tarde=config.hora_recreo1_tarde,
            hora_recreo2_tarde=config.hora_recreo2_tarde,
            ajuste_tutores=config.ajuste_tutores,
            ajuste_no_tutores=config.ajuste_no_tutores,
            activar_festivos_automaticos=config.activar_festivos_automaticos,
            dias_no_lectivos_personalizados=config.dias_no_lectivos_personalizados,
            recreos_config=config.recreos_config,
            algoritmo_asignacion=getattr(config, "algoritmo_asignacion", "v2.9"),
        )

        logger.info(
            f"Configuración obtenida: {config.fecha_inicio_curso} - {config.fecha_fin_curso}"
        )
        return dto
