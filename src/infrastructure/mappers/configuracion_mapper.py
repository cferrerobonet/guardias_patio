"""
Configuracion Mapper

Convierte entre el modelo SQLAlchemy Configuracion y la entidad ConfiguracionEntity.
"""

import ast
import json
from typing import Optional

from domain.entities.configuracion_entity import ConfiguracionEntity
from infrastructure.database.models import Configuracion


def _parse_json_list(value: Optional[str], default: list) -> list:
    """Parsea un campo Text JSON de forma defensiva."""
    if not value:
        return default
    try:
        result = json.loads(value)
        if isinstance(result, list):
            return result
    except (json.JSONDecodeError, TypeError):
        try:
            result = ast.literal_eval(value)
            if isinstance(result, list):
                return result
        except (ValueError, SyntaxError):
            pass
    return default


class ConfiguracionMapper:
    """Mapper para convertir entre Configuracion (ORM) y ConfiguracionEntity (Domain)."""

    @staticmethod
    def to_entity(model: Configuracion) -> ConfiguracionEntity:
        return ConfiguracionEntity(
            id=model.id,
            anio_inicio_curso=model.anio_inicio_curso or 0,
            fecha_inicio_curso=model.fecha_inicio_curso,
            fecha_fin_curso=model.fecha_fin_curso,
            hora_recreo1_manana=model.hora_recreo1_manana,
            hora_recreo2_manana=model.hora_recreo2_manana,
            hora_recreo1_tarde=model.hora_recreo1_tarde,
            hora_recreo2_tarde=model.hora_recreo2_tarde,
            activar_festivos_automaticos=model.activar_festivos_automaticos,
            dias_no_lectivos_personalizados=_parse_json_list(
                model.dias_no_lectivos_personalizados, []
            ),
            recreos_config=_parse_json_list(model.recreos_config, []),
            ajuste_tutores=model.ajuste_tutores or 1.0,
            ajuste_no_tutores=model.ajuste_no_tutores or 1.0,
            algoritmo_asignacion=model.algoritmo_asignacion or "v2.9",
            curso_activo_id=model.curso_activo_id,
        )

    @staticmethod
    def to_model(
        entity: ConfiguracionEntity, model: Optional[Configuracion] = None
    ) -> Configuracion:
        if model is None:
            model = Configuracion()
        model.anio_inicio_curso = entity.anio_inicio_curso
        model.fecha_inicio_curso = entity.fecha_inicio_curso
        model.fecha_fin_curso = entity.fecha_fin_curso
        model.hora_recreo1_manana = entity.hora_recreo1_manana
        model.hora_recreo2_manana = entity.hora_recreo2_manana
        model.hora_recreo1_tarde = entity.hora_recreo1_tarde
        model.hora_recreo2_tarde = entity.hora_recreo2_tarde
        model.activar_festivos_automaticos = entity.activar_festivos_automaticos
        model.dias_no_lectivos_personalizados = (
            json.dumps(entity.dias_no_lectivos_personalizados)
            if entity.dias_no_lectivos_personalizados
            else None
        )
        model.recreos_config = (
            json.dumps(entity.recreos_config) if entity.recreos_config else None
        )
        model.ajuste_tutores = entity.ajuste_tutores
        model.ajuste_no_tutores = entity.ajuste_no_tutores
        model.algoritmo_asignacion = entity.algoritmo_asignacion
        model.curso_activo_id = entity.curso_activo_id
        if entity.id is not None:
            model.id = entity.id
        return model
