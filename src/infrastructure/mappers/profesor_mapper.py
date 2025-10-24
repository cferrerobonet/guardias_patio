"""
Profesor Mapper

Convierte entre el modelo SQLAlchemy Profesor y la entidad ProfesorEntity.
"""

import json
from typing import Optional

from domain.entities import ProfesorEntity
from domain.value_objects import Email, HorasContrato, Turno, ZonaPreferida
from models.models import Profesor


class ProfesorMapper:
    """
    Mapper para convertir entre Profesor (SQLAlchemy) y ProfesorEntity (Domain).

    Separa la capa de persistencia de la capa de dominio.
    """

    @staticmethod
    def to_entity(model: Profesor) -> ProfesorEntity:
        """
        Convierte un modelo SQLAlchemy a una entidad de dominio.

        Args:
            model: Modelo SQLAlchemy Profesor

        Returns:
            ProfesorEntity
        """
        # Email (puede ser None)
        email = None
        if model.email_corporativo:
            email = Email.from_optional(model.email_corporativo)

        # Horas de contrato
        horas = HorasContrato(model.horas_contrato)

        # Turno - manejar casos especiales de datos inconsistentes
        turno_str = model.turno.lower().strip()

        # Si es turno mixto, verificar que tiene horas; si no, usar mañana como fallback
        if turno_str == "mixto":
            if model.horas_manana or model.horas_tarde:
                turno = Turno.from_string(
                    model.turno,
                    horas_manana=model.horas_manana,
                    horas_tarde=model.horas_tarde
                )
            else:
                # Datos inconsistentes: turno mixto sin horas -> fallback a mañana
                turno = Turno.from_string("mañana")
        else:
            # Turnos simples
            turno = Turno.from_string(model.turno)

        # Zona preferida (implementación futura, por ahora None)
        zona_preferida = ZonaPreferida.sin_preferencia()

        # Días y recreos permitidos (desde JSON)
        dias_permitidos = list(range(7))  # Por defecto todos
        if model.dias_semana_permitidos:
            try:
                dias_permitidos = json.loads(model.dias_semana_permitidos)
            except json.JSONDecodeError:
                pass

        recreos_permitidos = [1, 2]  # Por defecto ambos
        if model.recreos_permitidos:
            try:
                parsed = json.loads(model.recreos_permitidos)
                if isinstance(parsed, dict):
                    # Si es dict {"0": [1,2], "1": [2]}, extraer todos los recreos únicos
                    recreos_set = set()
                    for recreos_list in parsed.values():
                        recreos_set.update(recreos_list)
                    recreos_permitidos = sorted(list(recreos_set))
                elif isinstance(parsed, list):
                    recreos_permitidos = parsed
            except json.JSONDecodeError:
                pass

        return ProfesorEntity(
            id=model.id,
            nombre_completo=model.nombre_completo,
            email_corporativo=email,
            horas_contrato=horas,
            porcentaje_jornada=model.porcentaje_jornada,
            turno=turno,
            es_tutor=model.tutor,
            fecha_inicio_guardias=model.fecha_inicio_guardias,
            fecha_fin_guardias=model.fecha_fin_guardias,
            zona_preferida=zona_preferida,
            dias_semana_permitidos=dias_permitidos,
            recreos_permitidos=recreos_permitidos,
        )

    @staticmethod
    def to_model(
        entity: ProfesorEntity,
        model: Optional[Profesor] = None
    ) -> Profesor:
        """
        Convierte una entidad de dominio a un modelo SQLAlchemy.

        Args:
            entity: Entidad de dominio
            model: Modelo existente a actualizar (opcional)

        Returns:
            Modelo SQLAlchemy Profesor
        """
        if model is None:
            model = Profesor()

        # Actualizar campos básicos
        model.nombre_completo = entity.nombre_completo
        model.email_corporativo = (
            str(entity.email_corporativo) if entity.email_corporativo else None
        )
        model.horas_contrato = float(entity.horas_contrato)
        model.porcentaje_jornada = entity.porcentaje_jornada
        model.turno = entity.turno.value.value
        model.horas_manana = entity.turno.horas_manana
        model.horas_tarde = entity.turno.horas_tarde
        model.tutor = entity.es_tutor
        model.fecha_inicio_guardias = entity.fecha_inicio_guardias
        model.fecha_fin_guardias = entity.fecha_fin_guardias

        # Serializar listas a JSON
        model.dias_semana_permitidos = json.dumps(entity.dias_semana_permitidos)
        model.recreos_permitidos = json.dumps(entity.recreos_permitidos)

        return model

    @staticmethod
    def to_entities(models: list[Profesor]) -> list[ProfesorEntity]:
        """
        Convierte una lista de modelos a entidades.

        Args:
            models: Lista de modelos SQLAlchemy

        Returns:
            Lista de entidades de dominio
        """
        return [ProfesorMapper.to_entity(model) for model in models]

    @staticmethod
    def update_model_from_entity(model: Profesor, entity: ProfesorEntity) -> Profesor:
        """
        Actualiza un modelo existente con los datos de una entidad.

        Args:
            model: Modelo a actualizar
            entity: Entidad con los nuevos datos

        Returns:
            Modelo actualizado
        """
        return ProfesorMapper.to_model(entity, model)
