"""Por qué un hueco de guardia se queda sin nadie (FUN-013).

Cuando ningún profesor puede cubrir un slot, el registro decía sólo cuántos
huecos había. Eso no sirve para arreglarlo: hay que saber qué regla dejó fuera a
cada profesor y qué cambio mínimo lo resolvería.

Las reglas duras son las mismas que aplica `_es_elegible_basico`; aquí, en vez
de parar en la primera que falla, se recogen todas.
"""

from collections import Counter
from dataclasses import dataclass
from typing import List

from core.logging import get_logger

logger = get_logger(__name__)

TURNO = "turno incompatible"
AUSENTE = "ausente ese día"
FUERA_DE_RANGO = "fuera de su periodo de guardias"
RECREO = "ese recreo no lo tiene permitido"

#: Qué hacer para desbloquear el hueco, según lo que dejó fuera a más gente.
REMEDIOS = {
    TURNO: "no hay profesorado de ese turno: mueve el recreo de turno o cambia el turno de alguien",
    AUSENTE: "casi todo el mundo está ausente: revisa las ausencias de ese día",
    FUERA_DE_RANGO: "las fechas de guardias del profesorado no llegan a ese día: amplía alguna",
    RECREO: "nadie tiene permitido ese recreo: habilítalo a alguien en su ficha",
}


@dataclass
class HuecoSinCubrir:
    fecha: object
    turno: str
    recreo: int
    zona_id: int
    motivos: Counter
    sugerencia: str

    def describir(self) -> str:
        detalle = ", ".join(f"{cuantos} {motivo}" for motivo, cuantos in self.motivos.most_common())
        return (
            f"{self.fecha} · {self.turno} · recreo {self.recreo} · zona {self.zona_id}: "
            f"{detalle}. {self.sugerencia}"
        )


def motivos_de_exclusion(profesor, slot, session) -> List[str]:
    """Todas las reglas duras que impiden a un profesor cubrir un slot."""
    from services._asignador_cpsat_helpers import _parse_json_field, _profesor_ausente

    motivos = []

    if profesor.turno and profesor.turno not in ("completo", "mixto", "ambos"):
        if profesor.turno != slot.turno:
            motivos.append(TURNO)

    if _profesor_ausente(session, profesor.id, slot.fecha):
        motivos.append(AUSENTE)

    fuera_por_abajo = profesor.fecha_inicio_guardias and slot.fecha < profesor.fecha_inicio_guardias
    fuera_por_arriba = profesor.fecha_fin_guardias and slot.fecha > profesor.fecha_fin_guardias
    if fuera_por_abajo or fuera_por_arriba:
        motivos.append(FUERA_DE_RANGO)

    permitidos = _parse_json_field(profesor.recreos_permitidos, [1, 2, 3, 4])
    if isinstance(permitidos, dict):
        del_dia = permitidos.get(str(slot.fecha.weekday()), [])
        if slot.recreo_id not in del_dia:
            motivos.append(RECREO)
    elif isinstance(permitidos, list) and slot.recreo_id not in permitidos:
        motivos.append(RECREO)

    return motivos


def diagnosticar(profesores, slots_sin_cubrir, session) -> List[HuecoSinCubrir]:
    """Un informe por hueco: cuántos profesores excluyó cada regla y qué hacer."""
    informe = []
    for slot in slots_sin_cubrir:
        motivos: Counter = Counter()
        for profesor in profesores:
            for motivo in motivos_de_exclusion(profesor, slot, session):
                motivos[motivo] += 1

        principal = motivos.most_common(1)[0][0] if motivos else None
        sugerencia = REMEDIOS.get(principal, "revisa las restricciones del profesorado ese día")
        if not profesores:
            sugerencia = "no hay ningún profesor activo: da de alta el claustro"

        informe.append(
            HuecoSinCubrir(
                fecha=slot.fecha,
                turno=slot.turno,
                recreo=slot.recreo_id,
                zona_id=slot.zona_id,
                motivos=motivos,
                sugerencia=sugerencia,
            )
        )
    return informe


def registrar(informe: List[HuecoSinCubrir], maximo: int = 10) -> None:
    """Deja el informe en el registro, que es lo que ve el panel de progreso."""
    if not informe:
        return
    logger.warning(f"⚠️ {len(informe)} huecos sin ningún profesor elegible:")
    for hueco in informe[:maximo]:
        logger.warning(f"   · {hueco.describir()}")
    if len(informe) > maximo:
        logger.warning(f"   · y {len(informe) - maximo} huecos más con el mismo problema")
