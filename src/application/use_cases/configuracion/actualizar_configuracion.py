"""
Use Case: Actualizar Configuración.

Crea o actualiza la configuración del curso escolar.
Con invalidación de cache automática.
"""

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from application.dtos.configuracion_dto import ActualizarConfiguracionDTO, ConfiguracionDTO
from core.logging import get_logger
from core.observability import with_metrics
from infrastructure.database.models import Configuracion
from utils.repository_cache import invalidate_configuracion_cache

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

                if dto.anio_inicio_curso is not None:
                    config.anio_inicio_curso = dto.anio_inicio_curso
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
                if dto.algoritmo_asignacion is not None:
                    config.algoritmo_asignacion = dto.algoritmo_asignacion

                accion = "actualizada"
            else:
                # Crear nueva
                logger.info("Creando nueva configuración")

                # Calcular anio_inicio_curso si no se proporciona
                anio = dto.anio_inicio_curso
                if anio is None and dto.fecha_inicio_curso:
                    anio = dto.fecha_inicio_curso.year

                config = Configuracion(
                    anio_inicio_curso=anio,
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
                    recreos_config=dto.recreos_config or "",
                    algoritmo_asignacion=dto.algoritmo_asignacion or "v2.9",
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
                anio_inicio_curso=config.anio_inicio_curso,
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

        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error al actualizar configuración: {e}")
            raise
