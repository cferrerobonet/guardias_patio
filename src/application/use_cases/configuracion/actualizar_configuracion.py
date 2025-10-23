"""
Use Case: Actualizar Configuración.

Crea o actualiza la configuración del curso escolar.
Con invalidación de cache automática.
"""

from core.logging import get_logger
from core.observability import with_metrics
from models.models import Configuracion
from sqlalchemy.orm import Session
from utils.repository_cache import invalidate_configuracion_cache

from application.dtos.configuracion_dto import ActualizarConfiguracionDTO, ConfiguracionDTO

logger = get_logger(__name__)


class ActualizarConfiguracionUseCase:
    """
    Use Case para crear o actualizar la configuración del curso.

    Solo puede existir una configuración en el sistema.
    Si ya existe, se actualiza; si no, se crea nueva.
    """

    def __init__(self, session: Session):
        """
        Inicializa el use case.

        Args:
            session: Sesión de SQLAlchemy
        """
        self.session = session

    @with_metrics("actualizar_configuracion")
    def execute(self, dto: ActualizarConfiguracionDTO) -> ConfiguracionDTO:
        """
        Crea o actualiza la configuración.

        Args:
            dto: Datos de configuración a guardar

        Returns:
            ConfiguracionDTO con la configuración guardada
        """
        try:
            # Buscar configuración existente
            config = self.session.query(Configuracion).first()

            if config:
                # Actualizar existente
                logger.info(f"Actualizando configuración existente (ID: {config.id})")

                if dto.fecha_inicio_curso is not None:
                    config.fecha_inicio_curso = dto.fecha_inicio_curso
                if dto.fecha_fin_curso is not None:
                    config.fecha_fin_curso = dto.fecha_fin_curso
                if dto.hora_recreo1_manana is not None:
                    config.hora_recreo1_manana = dto.hora_recreo1_manana
                if dto.hora_recreo2_manana is not None:
                    config.hora_recreo2_manana = dto.hora_recreo2_manana
                if dto.hora_recreo1_tarde is not None:
                    config.hora_recreo1_tarde = dto.hora_recreo1_tarde
                if dto.hora_recreo2_tarde is not None:
                    config.hora_recreo2_tarde = dto.hora_recreo2_tarde
                if dto.ajuste_tutores is not None:
                    config.ajuste_tutores = dto.ajuste_tutores
                if dto.ajuste_no_tutores is not None:
                    config.ajuste_no_tutores = dto.ajuste_no_tutores
                if dto.activar_festivos_automaticos is not None:
                    config.activar_festivos_automaticos = dto.activar_festivos_automaticos
                if dto.dias_no_lectivos_personalizados is not None:
                    config.dias_no_lectivos_personalizados = dto.dias_no_lectivos_personalizados
                if dto.recreos_config is not None:
                    config.recreos_config = dto.recreos_config

                accion = "actualizada"
            else:
                # Crear nueva
                logger.info("Creando nueva configuración")

                config = Configuracion(
                    fecha_inicio_curso=dto.fecha_inicio_curso,
                    fecha_fin_curso=dto.fecha_fin_curso,
                    hora_recreo1_manana=dto.hora_recreo1_manana,
                    hora_recreo2_manana=dto.hora_recreo2_manana,
                    hora_recreo1_tarde=dto.hora_recreo1_tarde,
                    hora_recreo2_tarde=dto.hora_recreo2_tarde,
                    ajuste_tutores=dto.ajuste_tutores or 1.0,
                    ajuste_no_tutores=dto.ajuste_no_tutores or 1.0,
                    activar_festivos_automaticos=dto.activar_festivos_automaticos or True,
                    dias_no_lectivos_personalizados=dto.dias_no_lectivos_personalizados or "",
                    recreos_config=dto.recreos_config or ""
                )
                self.session.add(config)
                accion = "creada"

            # Guardar cambios
            self.session.commit()

            # Refrescar para obtener ID si es nuevo
            self.session.refresh(config)

            # Invalidar cache de configuración
            invalidate_configuracion_cache()

            logger.info(
                f"Configuración {accion} exitosamente: "
                f"{config.fecha_inicio_curso} - {config.fecha_fin_curso}"
            )

            # Retornar DTO
            return ConfiguracionDTO(
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
                recreos_config=config.recreos_config
            )

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error al actualizar configuración: {e}")
            raise
