"""
DTOs para la capa de sincronización (ARQ-07 — Anti-corruption layer).

Desacoplan los modelos ORM de la lógica de serialización/deserialización JSON.
El flujo recomendado es:
  Export: ORM model → DTO (from_orm) → dict (to_dict) → JSON
  Import: JSON → dict → DTO (from_dict) → ORM model

Ningún DTO importa modelos de infrastructure.database.models para evitar
el acoplamiento invertido.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Optional

from sync.data_exporter_helpers import serialize_date

# ---------------------------------------------------------------------------
# CursoEscolar
# ---------------------------------------------------------------------------


@dataclass
class CursoEscolarSyncDTO:
    id: int
    anio_inicio: int
    anio_fin: int
    fecha_inicio: Optional[str]
    fecha_fin: Optional[str]
    nombre: str
    activo: bool
    cerrado: bool
    created_at: Optional[str]

    @classmethod
    def from_orm(cls, orm_obj: Any) -> "CursoEscolarSyncDTO":
        return cls(
            id=orm_obj.id,
            anio_inicio=orm_obj.anio_inicio,
            anio_fin=orm_obj.anio_fin,
            fecha_inicio=serialize_date(orm_obj.fecha_inicio),
            fecha_fin=serialize_date(orm_obj.fecha_fin),
            nombre=orm_obj.nombre,
            activo=orm_obj.activo,
            cerrado=orm_obj.cerrado,
            created_at=serialize_date(orm_obj.created_at),
        )

    @classmethod
    def from_dict(cls, data: dict) -> "CursoEscolarSyncDTO":
        return cls(
            id=data["id"],
            anio_inicio=data["anio_inicio"],
            anio_fin=data["anio_fin"],
            fecha_inicio=data.get("fecha_inicio"),
            fecha_fin=data.get("fecha_fin"),
            nombre=data["nombre"],
            activo=data["activo"],
            cerrado=data["cerrado"],
            created_at=data.get("created_at"),
        )

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Profesor
# ---------------------------------------------------------------------------


@dataclass
class ProfesorSyncDTO:
    id: int
    nombre_completo: str
    email_corporativo: Optional[str]
    horas_contrato: float
    porcentaje_jornada: float
    turno: str
    horas_manana: Optional[float]
    horas_tarde: Optional[float]
    tutor: bool
    activo: bool
    fecha_inicio_guardias: Optional[str]
    fecha_fin_guardias: Optional[str]
    dias_semana_permitidos: Optional[str]
    recreos_permitidos: Optional[str]

    @classmethod
    def from_orm(cls, orm_obj: Any) -> "ProfesorSyncDTO":
        return cls(
            id=orm_obj.id,
            nombre_completo=orm_obj.nombre_completo,
            email_corporativo=orm_obj.email_corporativo,
            horas_contrato=float(orm_obj.horas_contrato),
            porcentaje_jornada=float(orm_obj.porcentaje_jornada),
            turno=orm_obj.turno,
            horas_manana=float(orm_obj.horas_manana) if orm_obj.horas_manana is not None else None,
            horas_tarde=float(orm_obj.horas_tarde) if orm_obj.horas_tarde is not None else None,
            tutor=orm_obj.tutor,
            activo=orm_obj.activo,
            fecha_inicio_guardias=serialize_date(orm_obj.fecha_inicio_guardias)
            if orm_obj.fecha_inicio_guardias
            else None,
            fecha_fin_guardias=serialize_date(orm_obj.fecha_fin_guardias)
            if orm_obj.fecha_fin_guardias
            else None,
            dias_semana_permitidos=orm_obj.dias_semana_permitidos,
            recreos_permitidos=orm_obj.recreos_permitidos,
        )

    @classmethod
    def from_dict(cls, data: dict) -> "ProfesorSyncDTO":
        return cls(
            id=data["id"],
            nombre_completo=data["nombre_completo"],
            email_corporativo=data.get("email_corporativo"),
            horas_contrato=float(data["horas_contrato"]),
            porcentaje_jornada=float(data["porcentaje_jornada"]),
            turno=data["turno"],
            horas_manana=float(data["horas_manana"])
            if data.get("horas_manana") is not None
            else None,
            horas_tarde=float(data["horas_tarde"]) if data.get("horas_tarde") is not None else None,
            tutor=data.get("tutor", False),
            activo=data.get("activo", True),
            fecha_inicio_guardias=data.get("fecha_inicio_guardias"),
            fecha_fin_guardias=data.get("fecha_fin_guardias"),
            dias_semana_permitidos=data.get("dias_semana_permitidos"),
            recreos_permitidos=data.get("recreos_permitidos"),
        )

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Zona
# ---------------------------------------------------------------------------


@dataclass
class ZonaSyncDTO:
    id: int
    nombre_zona: str
    descripcion: Optional[str]
    fecha_inicio: Optional[str]
    fecha_fin: Optional[str]

    @classmethod
    def from_orm(cls, orm_obj: Any) -> "ZonaSyncDTO":
        return cls(
            id=orm_obj.id,
            nombre_zona=orm_obj.nombre_zona,
            descripcion=orm_obj.descripcion,
            fecha_inicio=serialize_date(orm_obj.fecha_inicio) if orm_obj.fecha_inicio else None,
            fecha_fin=serialize_date(orm_obj.fecha_fin) if orm_obj.fecha_fin else None,
        )

    @classmethod
    def from_dict(cls, data: dict) -> "ZonaSyncDTO":
        return cls(
            id=data["id"],
            nombre_zona=data["nombre_zona"],
            descripcion=data.get("descripcion"),
            fecha_inicio=data.get("fecha_inicio"),
            fecha_fin=data.get("fecha_fin"),
        )

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Configuracion
# ---------------------------------------------------------------------------


@dataclass
class ConfiguracionSyncDTO:
    id: int
    anio_inicio_curso: Optional[int]
    fecha_inicio_curso: Optional[str]
    fecha_fin_curso: Optional[str]
    hora_recreo1_manana: Optional[str]
    hora_recreo2_manana: Optional[str]
    hora_recreo1_tarde: Optional[str]
    hora_recreo2_tarde: Optional[str]
    activar_festivos_automaticos: bool
    dias_no_lectivos_personalizados: Optional[str]
    recreos_config: Optional[str]
    ajuste_tutores: float
    ajuste_no_tutores: float
    algoritmo_asignacion: Optional[str]

    @classmethod
    def from_orm(cls, orm_obj: Any) -> "ConfiguracionSyncDTO":
        return cls(
            id=orm_obj.id,
            anio_inicio_curso=orm_obj.anio_inicio_curso,
            fecha_inicio_curso=serialize_date(orm_obj.fecha_inicio_curso),
            fecha_fin_curso=serialize_date(orm_obj.fecha_fin_curso),
            hora_recreo1_manana=orm_obj.hora_recreo1_manana.isoformat()
            if orm_obj.hora_recreo1_manana
            else None,
            hora_recreo2_manana=orm_obj.hora_recreo2_manana.isoformat()
            if orm_obj.hora_recreo2_manana
            else None,
            hora_recreo1_tarde=orm_obj.hora_recreo1_tarde.isoformat()
            if orm_obj.hora_recreo1_tarde
            else None,
            hora_recreo2_tarde=orm_obj.hora_recreo2_tarde.isoformat()
            if orm_obj.hora_recreo2_tarde
            else None,
            activar_festivos_automaticos=orm_obj.activar_festivos_automaticos,
            dias_no_lectivos_personalizados=orm_obj.dias_no_lectivos_personalizados,
            recreos_config=orm_obj.recreos_config,
            ajuste_tutores=float(orm_obj.ajuste_tutores) if orm_obj.ajuste_tutores else 1.0,
            ajuste_no_tutores=float(orm_obj.ajuste_no_tutores)
            if orm_obj.ajuste_no_tutores
            else 1.0,
            algoritmo_asignacion=orm_obj.algoritmo_asignacion,
        )

    @classmethod
    def from_dict(cls, data: dict) -> "ConfiguracionSyncDTO":
        return cls(
            id=data["id"],
            anio_inicio_curso=data.get("anio_inicio_curso"),
            fecha_inicio_curso=data.get("fecha_inicio_curso"),
            fecha_fin_curso=data.get("fecha_fin_curso"),
            hora_recreo1_manana=data.get("hora_recreo1_manana"),
            hora_recreo2_manana=data.get("hora_recreo2_manana"),
            hora_recreo1_tarde=data.get("hora_recreo1_tarde"),
            hora_recreo2_tarde=data.get("hora_recreo2_tarde"),
            activar_festivos_automaticos=data.get("activar_festivos_automaticos", True),
            dias_no_lectivos_personalizados=data.get("dias_no_lectivos_personalizados"),
            recreos_config=data.get("recreos_config"),
            ajuste_tutores=float(data.get("ajuste_tutores", 1.0)),
            ajuste_no_tutores=float(data.get("ajuste_no_tutores", 1.0)),
            algoritmo_asignacion=data.get("algoritmo_asignacion"),
        )

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Guardia
# ---------------------------------------------------------------------------


@dataclass
class GuardiaSyncDTO:
    id: int
    curso_id: Optional[int]
    profesor_id: int
    fecha: Optional[str]
    turno: str
    recreo: int
    zona_id: int

    @classmethod
    def from_orm(cls, orm_obj: Any) -> "GuardiaSyncDTO":
        return cls(
            id=orm_obj.id,
            curso_id=orm_obj.curso_id,
            profesor_id=orm_obj.profesor_id,
            fecha=serialize_date(orm_obj.fecha),
            turno=orm_obj.turno,
            recreo=orm_obj.recreo,
            zona_id=orm_obj.zona_id,
        )

    @classmethod
    def from_dict(cls, data: dict) -> "GuardiaSyncDTO":
        return cls(
            id=data["id"],
            curso_id=data.get("curso_id"),
            profesor_id=data["profesor_id"],
            fecha=data.get("fecha"),
            turno=data["turno"],
            recreo=data["recreo"],
            zona_id=data["zona_id"],
        )

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Ausencia
# ---------------------------------------------------------------------------


@dataclass
class AusenciaSyncDTO:
    id: int
    profesor_id: int
    fecha_inicio: Optional[str]
    fecha_fin: Optional[str]
    tipo: str
    motivo: Optional[str]
    documento_path: Optional[str]
    activa: bool
    created_at: Optional[str]
    updated_at: Optional[str]

    @classmethod
    def from_orm(cls, orm_obj: Any) -> "AusenciaSyncDTO":
        return cls(
            id=orm_obj.id,
            profesor_id=orm_obj.profesor_id,
            fecha_inicio=serialize_date(orm_obj.fecha_inicio),
            fecha_fin=serialize_date(orm_obj.fecha_fin),
            tipo=orm_obj.tipo,
            motivo=orm_obj.motivo,
            documento_path=orm_obj.documento_path,
            activa=orm_obj.activa,
            created_at=serialize_date(orm_obj.created_at) if orm_obj.created_at else None,
            updated_at=serialize_date(orm_obj.updated_at) if orm_obj.updated_at else None,
        )

    @classmethod
    def from_dict(cls, data: dict) -> "AusenciaSyncDTO":
        return cls(
            id=data["id"],
            profesor_id=data["profesor_id"],
            fecha_inicio=data.get("fecha_inicio"),
            fecha_fin=data.get("fecha_fin"),
            tipo=data["tipo"],
            motivo=data.get("motivo"),
            documento_path=data.get("documento_path"),
            activa=data.get("activa", True),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    def to_dict(self) -> dict:
        return asdict(self)
