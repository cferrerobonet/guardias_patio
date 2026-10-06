"""Cuánto cubre cada turno y cuánto ponen los mixtos, con la equidad primero.

Cada turno repartía sus huecos sólo entre quienes podían cubrirlo, y los mixtos
entraban en los dos repartos. Sin profesorado fijo de un turno, todos sus huecos
caían en los pocos mixtos: con todo el claustro de tarde y tres mixtos, cuotas de
494 y 248 guardias, imposibles, y una guardia diaria para cada mixto durante
todo el curso mientras los demás hacían 40 (2026-10-06).

Decisión de CarlosFB (2026-10-06): la equidad va primero y es aceptable que
queden patios sin cubrir. Por eso:

1. Se busca el nivel común más bajo (guardias por unidad de jornada) con el que
   se cubre todo: cada turno lo cubre su profesorado fijo hasta ese nivel y los
   mixtos sólo ponen lo que falte.
2. Un mixto no carga más que el profesorado fijo más cargado: si para cubrirlo
   todo tendría que pasar de ahí, se queda en ese nivel y lo que falte queda
   como hueco.

Sin mixtos, o con profesorado fijo de sobra en cada turno, el resultado es el
de siempre: cada turno reparte sus huecos entre los suyos.
"""

from dataclasses import dataclass
from typing import Dict, Optional

TURNOS = ("mañana", "tarde")


@dataclass(frozen=True)
class TurnoEquitativo:
    """Lo que se reparte en un turno."""

    #: Huecos que se cubren (los demás quedan sin cubrir a propósito).
    cubiertos: float
    #: Guardias por unidad de jornada del profesorado fijo del turno.
    nivel_fijos: float
    #: Parte de los huecos del turno que ponen los mixtos, entre todos.
    de_mixtos: float


def _oficial_fijos(nivel, huecos, hechas, fijos, t) -> float:
    """Huecos del reparto oficial que cubre el profesorado fijo de un turno a un nivel."""
    return min(huecos[t], max(0.0, nivel * fijos[t] - hechas[t]))


def reparto_equitativo(
    huecos: Dict[str, int],
    fijos: Dict[str, float],
    mixtos: float,
    hechas: Optional[Dict[str, int]] = None,
    hechas_mixtos: int = 0,
) -> Dict[str, TurnoEquitativo]:
    """Reparto por turno con la equidad primero.

    El nivel es la parte del curso por unidad de jornada: cuenta también las
    guardias voluntarias ya hechas, como el resto del cálculo de cuotas.

    Args:
        huecos: huecos del reparto oficial de cada turno.
        fijos: suma de factores de jornada del profesorado fijo de cada turno.
        mixtos: suma de factores de jornada de los mixtos.
        hechas: guardias voluntarias ya hechas por el profesorado fijo de cada turno.
        hechas_mixtos: guardias voluntarias ya hechas por los mixtos.
    """
    huecos = {t: max(0, int(huecos.get(t, 0))) for t in TURNOS}
    fijos = {t: max(0.0, float(fijos.get(t, 0.0))) for t in TURNOS}
    hechas = {t: max(0, int((hechas or {}).get(t, 0))) for t in TURNOS}
    mixtos = max(0.0, float(mixtos))
    hechas_mixtos = max(0, int(hechas_mixtos))

    # Nivel al que cada turno se cubre sólo con su profesorado fijo.
    saturacion = {t: (huecos[t] + hechas[t]) / fijos[t] for t in TURNOS if fijos[t] > 0}

    def faltan(nivel: float) -> float:
        return sum(huecos[t] - _oficial_fijos(nivel, huecos, hechas, fijos, t) for t in TURNOS)

    def pueden(nivel: float) -> float:
        return max(0.0, nivel * mixtos - hechas_mixtos)

    # Nivel común más bajo que lo cubre todo con la ayuda de los mixtos.
    if mixtos > 0:
        bajo = 0.0
        alto = (sum(huecos.values()) + hechas_mixtos) / mixtos + max(
            saturacion.values(), default=0.0
        )
        for _ in range(80):
            medio = (bajo + alto) / 2
            if faltan(medio) <= pueden(medio):
                alto = medio
            else:
                bajo = medio
        nivel = alto
    else:
        nivel = max(saturacion.values(), default=0.0)

    # Equidad primero: un mixto no pasa del profesorado fijo más cargado.
    if saturacion:
        nivel = min(nivel, max(saturacion.values()))

    nivel_fijos = {t: min(nivel, saturacion[t]) if t in saturacion else 0.0 for t in TURNOS}
    oficial = {t: _oficial_fijos(nivel_fijos[t], huecos, hechas, fijos, t) for t in TURNOS}
    resto = {t: huecos[t] - oficial[t] for t in TURNOS}
    total_resto = sum(resto.values())
    capacidad = pueden(nivel) if saturacion else float(sum(huecos.values()))
    proporcion = 1.0 if not total_resto or total_resto <= capacidad else capacidad / total_resto
    resultado = {}
    for t in TURNOS:
        de_mixtos = resto[t] * proporcion if mixtos > 0 else 0.0
        resultado[t] = TurnoEquitativo(
            cubiertos=oficial[t] + de_mixtos,
            nivel_fijos=nivel_fijos[t],
            de_mixtos=de_mixtos,
        )
    return resultado
