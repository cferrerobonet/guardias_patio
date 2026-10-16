"""Edición manual del calendario: mover una guardia o asignar un hueco (GUA-CON-001).

La permuta (FUN-003b) cubre el intercambio 1 a 1; esto es la edición libre: llevar una
guardia a otro día, recreo, zona o profesor, o cubrir a mano un hueco que el reparto
dejó vacío. Se valida con **las mismas restricciones que respeta el reparto**:

- el hueco existe en el reparto: día lectivo del reparto oficial, recreo configurado
  y zona activa y en sus fechas, entre las que cubre ese recreo (`_generar_slots`);
- el hueco está libre (cada hueco, como mucho un profesor);
- el profesor está activo y es elegible para ese hueco (`_es_elegible_basico`: turno,
  ausencias, fechas de inicio y fin, días de la semana y recreos permitidos);
- el profesor no tiene otra guardia ese día (máximo una al día).

Cada cambio deja su rastro en el historial de cambios con el estado anterior, y
`deshacer_edicion_manual` lo devuelve tal cual estaba.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from typing import List, Optional, Tuple

from infrastructure.database.models import Configuracion, Guardia, GuardiaAuditLog, Profesor, Zona
from services._asignador_cpsat_helpers import (
    Slot,
    _es_elegible_basico,
    _generar_slots,
    _parse_json_field,
    _profesor_ausente,
)
from utils import get_logger

logger = get_logger(__name__)

ASIGNADA = "ASIGNADA_A_MANO"
MOVIDA = "MOVIDA_A_MANO"
DESHECHA = "EDICION_DESHECHA"

_DIAS = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")


@dataclass(frozen=True)
class Hueco:
    """Un hueco del reparto: un recreo de un día en una zona."""

    fecha: date
    turno: str
    recreo: int
    zona_id: int

    @property
    def slot(self) -> Slot:
        return Slot(fecha=self.fecha, turno=self.turno, recreo_id=self.recreo, zona_id=self.zona_id)

    @classmethod
    def de_guardia(cls, guardia: Guardia) -> "Hueco":
        return cls(guardia.fecha, guardia.turno, int(guardia.recreo), guardia.zona_id)


# --- Consulta ---------------------------------------------------------------


def huecos_del_dia(session, fecha: date) -> List[Hueco]:
    """Los huecos que reparte el algoritmo ese día (vacío si no es día del reparto)."""
    config = session.query(Configuracion).first()
    if config is None:
        return []
    return [
        Hueco(s.fecha, s.turno, s.recreo_id, s.zona_id)
        for s in _generar_slots(config, session, solo_dia=fecha)
    ]


def etiquetas_de_recreos(session) -> dict:
    """{id de recreo: «R1 Mañana»} según la configuración."""
    from services.calculador_guardias import _parse_recreos_config

    config = session.query(Configuracion).first()
    if config is None:
        return {}
    return {
        int(r["id"]): (r.get("etiqueta") or f"Recreo {r['id']}")
        for r in _parse_recreos_config(config)
    }


def guardia_en_hueco(session, hueco: Hueco, salvo_id: Optional[int] = None) -> Optional[Guardia]:
    consulta = session.query(Guardia).filter(
        Guardia.fecha == hueco.fecha,
        Guardia.turno == hueco.turno,
        Guardia.recreo == hueco.recreo,
        Guardia.zona_id == hueco.zona_id,
    )
    if salvo_id is not None:
        consulta = consulta.filter(Guardia.id != salvo_id)
    return consulta.first()


def motivos_del_hueco(session, hueco: Hueco, salvo_id: Optional[int] = None) -> List[str]:
    """Por qué no se puede poner una guardia en ese hueco (vacío si se puede)."""
    if hueco not in set(huecos_del_dia(session, hueco.fecha)):
        return [
            f"El {hueco.fecha:%d/%m/%Y} no tiene ese recreo y esa zona en el reparto "
            "(día no lectivo, recreo sin configurar o zona inactiva o fuera de sus fechas)."
        ]
    ocupada = guardia_en_hueco(session, hueco, salvo_id)
    if ocupada is not None:
        zona = session.get(Zona, hueco.zona_id)
        quien = ocupada.profesor.nombre_completo if ocupada.profesor else "otro profesor"
        nombre_zona = zona.nombre_zona if zona else "Esa zona"
        return [f"{nombre_zona} ya tiene guardia en ese recreo: la hace {quien}."]
    return []


def motivos_del_profesor(
    session, profesor: Profesor, hueco: Hueco, salvo_id: Optional[int] = None
) -> List[str]:
    """Por qué ese profesor no puede hacer la guardia de ese hueco (vacío si puede)."""
    nombre = profesor.nombre_completo
    motivos: List[str] = []
    if not profesor.activo:
        motivos.append(f"{nombre} no está activo.")
    if profesor.turno and profesor.turno not in ("completo", "mixto", "ambos"):
        if profesor.turno != hueco.turno:
            motivos.append(f"{nombre} es de turno de {profesor.turno} y el recreo es de {hueco.turno}.")
    if _profesor_ausente(session, profesor.id, hueco.fecha):
        motivos.append(f"{nombre} está ausente ese día.")
    if profesor.fecha_inicio_guardias and hueco.fecha < profesor.fecha_inicio_guardias:
        motivos.append(f"{nombre} empieza a hacer guardias el {profesor.fecha_inicio_guardias:%d/%m/%Y}.")
    if profesor.fecha_fin_guardias and hueco.fecha > profesor.fecha_fin_guardias:
        motivos.append(f"{nombre} deja de hacer guardias el {profesor.fecha_fin_guardias:%d/%m/%Y}.")
    dias = _parse_json_field(profesor.dias_semana_permitidos, [])
    if dias and hueco.fecha.weekday() not in dias:
        motivos.append(f"{nombre} no hace guardias los {_DIAS[hueco.fecha.weekday()]}.")
    if not motivos and not _es_elegible_basico(profesor, hueco.slot, session):
        motivos.append(f"{nombre} no puede hacer guardia en ese recreo ese día de la semana.")
    otras = session.query(Guardia).filter(
        Guardia.profesor_id == profesor.id, Guardia.fecha == hueco.fecha
    )
    if salvo_id is not None:
        otras = otras.filter(Guardia.id != salvo_id)
    if otras.count():
        motivos.append(f"{nombre} ya tiene otra guardia ese día.")
    return motivos


def candidatos(
    session, hueco: Hueco, salvo_id: Optional[int] = None
) -> List[Tuple[Profesor, List[str]]]:
    """Todos los profesores activos con lo que les impide coger el hueco (vacío = puede)."""
    from utils.orden import clave_alfabetica

    profesores = session.query(Profesor).filter(Profesor.activo.is_(True)).all()
    profesores.sort(key=lambda p: clave_alfabetica(p.nombre_completo))
    return [(p, motivos_del_profesor(session, p, hueco, salvo_id)) for p in profesores]


def guardias_del_profesor(session, profesor_id: int, curso_id: Optional[int]) -> int:
    consulta = session.query(Guardia).filter(Guardia.profesor_id == profesor_id)
    if curso_id is not None:
        consulta = consulta.filter(Guardia.curso_id == curso_id)
    return consulta.count()


def curso_activo_id(session) -> Optional[int]:
    from services.gestor_cursos import GestorCursos

    curso = GestorCursos.from_session(session).obtener_curso_activo()
    return curso.id if curso else None


# --- Cambios ----------------------------------------------------------------


def _comprobar(session, hueco: Hueco, profesor_id: int, salvo_id: Optional[int]) -> Profesor:
    profesor = session.get(Profesor, profesor_id)
    if profesor is None:
        raise ValueError("Ese profesor ya no existe.")
    motivos = motivos_del_hueco(session, hueco, salvo_id) + motivos_del_profesor(
        session, profesor, hueco, salvo_id
    )
    if motivos:
        raise ValueError("\n".join(motivos))
    return profesor


def _estado(guardia: Guardia) -> dict:
    return {
        "profesor_id": guardia.profesor_id,
        "fecha": guardia.fecha.isoformat(),
        "turno": guardia.turno,
        "recreo": int(guardia.recreo),
        "zona_id": guardia.zona_id,
    }


def asignar_guardia(session, hueco: Hueco, profesor_id: int, usuario: Optional[str] = None) -> GuardiaAuditLog:
    """Cubre a mano un hueco vacío. Devuelve la entrada del historial (para deshacer)."""
    curso_id = curso_activo_id(session)
    if curso_id is None:
        raise ValueError("No hay un curso activo: actívalo en Cursos antes de editar el calendario.")
    profesor = _comprobar(session, hueco, profesor_id, None)
    guardia = Guardia(
        profesor_id=profesor.id,
        fecha=hueco.fecha,
        turno=hueco.turno,
        recreo=hueco.recreo,
        zona_id=hueco.zona_id,
        curso_id=curso_id,
    )
    session.add(guardia)
    session.flush()
    entrada = GuardiaAuditLog(
        guardia_id=guardia.id,
        accion=ASIGNADA,
        profesor_id=profesor.id,
        usuario=usuario,
        detalle=json.dumps({"despues": _estado(guardia)}),
    )
    session.add(entrada)
    session.commit()
    logger.info(f"Guardia {guardia.id} asignada a mano al profesor {profesor.id}")
    return entrada


def mover_guardia(
    session, guardia_id: int, hueco: Hueco, profesor_id: int, usuario: Optional[str] = None
) -> GuardiaAuditLog:
    """Lleva una guardia a otro hueco o profesor. Devuelve la entrada del historial."""
    guardia = session.get(Guardia, guardia_id)
    if guardia is None:
        raise ValueError("Esa guardia ya no existe.")
    antes = _estado(guardia)
    if Hueco.de_guardia(guardia) == hueco and guardia.profesor_id == profesor_id:
        raise ValueError("No has cambiado nada: elige otro día, recreo, zona o profesor.")
    profesor = _comprobar(session, hueco, profesor_id, guardia.id)
    guardia.profesor_id = profesor.id
    guardia.fecha = hueco.fecha
    guardia.turno = hueco.turno
    guardia.recreo = hueco.recreo
    guardia.zona_id = hueco.zona_id
    session.flush()
    entrada = GuardiaAuditLog(
        guardia_id=guardia.id,
        accion=MOVIDA,
        profesor_id=profesor.id,
        usuario=usuario,
        detalle=json.dumps({"antes": antes, "despues": _estado(guardia)}),
    )
    session.add(entrada)
    session.commit()
    logger.info(f"Guardia {guardia.id} movida a mano: {antes} → {_estado(guardia)}")
    return entrada


def deshacer_edicion_manual(session, entrada_id: int) -> None:
    """Devuelve la guardia a como estaba antes de esa edición manual.

    Solo si nadie la ha vuelto a tocar después: deshacer encima de otro cambio
    machacaría ese otro cambio sin decirlo.
    """
    entrada = session.get(GuardiaAuditLog, entrada_id)
    if entrada is None or entrada.accion not in (ASIGNADA, MOVIDA):
        raise ValueError("Ese cambio no es una edición manual del calendario.")
    ya = (
        session.query(GuardiaAuditLog)
        .filter(GuardiaAuditLog.accion == DESHECHA, GuardiaAuditLog.guardia_id == entrada.guardia_id)
        .all()
    )
    if any(json.loads(e.detalle or "{}").get("deshace") == entrada.id for e in ya):
        raise ValueError("Ese cambio ya se deshizo.")
    detalle = json.loads(entrada.detalle or "{}")
    guardia = session.get(Guardia, entrada.guardia_id) if entrada.guardia_id else None
    if guardia is None or _estado(guardia) != detalle.get("despues"):
        raise ValueError(
            "La guardia ha cambiado después de esa edición: no se deshace para no "
            "perder lo que se hizo luego."
        )
    if entrada.accion == ASIGNADA:
        session.delete(guardia)
    else:
        antes = detalle["antes"]
        guardia.profesor_id = antes["profesor_id"]
        guardia.fecha = date.fromisoformat(antes["fecha"])
        guardia.turno = antes["turno"]
        guardia.recreo = antes["recreo"]
        guardia.zona_id = antes["zona_id"]
    session.add(
        GuardiaAuditLog(
            guardia_id=entrada.guardia_id,
            accion=DESHECHA,
            profesor_id=entrada.profesor_id,
            detalle=json.dumps({"deshace": entrada.id}),
        )
    )
    session.commit()
    logger.info(f"Edición manual {entrada.id} deshecha")
