"""Qué recreo es cada guardia: turno, número dentro del turno, etiqueta y hora.

Las guardias guardan el id **global** del recreo. Con `recreos_config` (lo que
escribe Ajustes) los ids son fijos: 1 y 2 de mañana, 3 y 4 de tarde. Sin él, el
reparto numera de forma compacta los recreos que tienen hora, en ese orden
(`_asignador_cpsat_helpers._generar_recreos_fallback`). Los PDF, el .ics, la web,
el correo y los diálogos trataban el id como si fuera el número dentro del turno:
la tarde salía como «Recreo 3» sin hora y el .ics la descartaba.

Toda salida que enseñe un recreo usa `resolver` (o `recreos_de` para la leyenda).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, time
from typing import Optional

MANANA = "mañana"
TARDE = "tarde"

#: Campo de hora de cada recreo, por turno y número dentro del turno.
CAMPOS_DE_HORA = (
    (MANANA, 1, "hora_recreo1_manana"),
    (MANANA, 2, "hora_recreo2_manana"),
    (TARDE, 1, "hora_recreo1_tarde"),
    (TARDE, 2, "hora_recreo2_tarde"),
)
#: Ids fijos que escribe Ajustes en `recreos_config`.
IDS_DE_AJUSTES = {1: (MANANA, 1), 2: (MANANA, 2), 3: (TARDE, 1), 4: (TARDE, 2)}


@dataclass(frozen=True)
class Recreo:
    id: int
    turno: str
    ordinal: int
    hora: Optional[time] = None

    @property
    def hora_texto(self) -> str:
        return self.hora.strftime("%H:%M") if self.hora else ""

    @property
    def corta(self) -> str:
        """«R1»: el número dentro de su turno, como en la leyenda de los PDF."""
        return f"R{self.ordinal}"

    @property
    def codigo(self) -> str:
        """«M1», «T2»: turno y número, para los calendarios compactos."""
        return f"{self.turno[:1].upper()}{self.ordinal}"

    @property
    def etiqueta(self) -> str:
        """«Recreo 1 de tarde»."""
        return f"Recreo {self.ordinal} de {self.turno}"

    @property
    def etiqueta_con_hora(self) -> str:
        """«Recreo 1 de tarde · 16:30» (sin la hora si no está configurada)."""
        return f"{self.etiqueta} · {self.hora_texto}" if self.hora else self.etiqueta

    @property
    def corta_con_hora(self) -> str:
        """«R1 · 16:30»."""
        return f"{self.corta} · {self.hora_texto}" if self.hora else self.corta


def normalizar_turno(turno) -> Optional[str]:
    texto = str(turno or "").strip().lower()
    if texto.startswith("t"):
        return TARDE
    if texto.startswith("m"):
        return MANANA
    return None


def _hora(valor) -> Optional[time]:
    if isinstance(valor, time):
        return valor
    if isinstance(valor, datetime):
        return valor.time()
    if isinstance(valor, str) and valor.strip():
        for formato in ("%H:%M", "%H:%M:%S"):
            try:
                return datetime.strptime(valor.strip(), formato).time()
            except ValueError:
                continue
    return None


def _hora_del_campo(config, turno: str, ordinal: int) -> Optional[time]:
    if config is None:
        return None
    for t, n, campo in CAMPOS_DE_HORA:
        if (t, n) == (turno, ordinal):
            return _hora(getattr(config, campo, None))
    return None


def _configurados(config) -> list:
    datos = getattr(config, "recreos_config", None) if config is not None else None
    if isinstance(datos, str):
        try:
            datos = json.loads(datos) if datos.strip() else []
        except ValueError:
            datos = []
    return [r for r in datos if isinstance(r, dict) and "id" in r] if isinstance(datos, list) else []


def recreos_de(config) -> list[Recreo]:
    """Los recreos del centro, ordenados por id, con su turno, número y hora."""
    configurados = _configurados(config)
    if configurados:
        recreos = []
        vistos = {MANANA: 0, TARDE: 0}
        for r in sorted(configurados, key=lambda r: int(r["id"])):
            try:
                id_ = int(r["id"])
            except (TypeError, ValueError):
                continue
            turno = normalizar_turno(r.get("turno")) or MANANA
            vistos[turno] += 1
            fijo = IDS_DE_AJUSTES.get(id_)
            ordinal = fijo[1] if fijo and fijo[0] == turno else vistos[turno]
            hora = _hora(r.get("hora")) or _hora_del_campo(config, turno, ordinal)
            recreos.append(Recreo(id_, turno, ordinal, hora))
        return recreos
    # Sin lista guardada: la misma numeración compacta que usa el reparto
    recreos, id_ = [], 0
    for turno, ordinal, campo in CAMPOS_DE_HORA:
        hora = _hora(getattr(config, campo, None)) if config is not None else None
        if hora:
            id_ += 1
            recreos.append(Recreo(id_, turno, ordinal, hora))
    return recreos


def resolver(config, recreo_id, turno=None) -> Recreo:
    """El recreo de una guardia a partir de su id global (y de su turno)."""
    try:
        id_ = int(recreo_id)
    except (TypeError, ValueError):
        id_ = 0
    t = normalizar_turno(turno)
    recreos = recreos_de(config)
    for r in recreos:
        if r.id == id_ and (t is None or r.turno == t):
            return r
    if t is not None:
        # Datos antiguos numerados dentro del turno (1 y 2 también de tarde)
        for r in recreos:
            if r.turno == t and r.ordinal == id_:
                return r
    fijo = IDS_DE_AJUSTES.get(id_)
    if fijo and (t is None or fijo[0] == t):
        turno_fijo, ordinal = fijo
    else:
        turno_fijo, ordinal = t or MANANA, id_ if id_ in (1, 2) else max(id_, 1)
    return Recreo(id_, turno_fijo, ordinal, _hora_del_campo(config, turno_fijo, ordinal))


def configuracion_de(session):
    """La configuración del centro, o None (sin sesión o sin configurar)."""
    if session is None:
        return None
    from infrastructure.database.models import Configuracion

    return session.query(Configuracion).first()


def de_guardia(guardia, config=None) -> Recreo:
    """El recreo de una guardia; sin `config`, la de la sesión de la guardia."""
    if config is None:
        from sqlalchemy.exc import SQLAlchemyError
        from sqlalchemy.orm import object_session
        from sqlalchemy.orm.exc import UnmappedInstanceError

        try:
            config = configuracion_de(object_session(guardia))
        except (UnmappedInstanceError, SQLAlchemyError):  # objeto suelto o de prueba
            config = None
    return resolver(config, getattr(guardia, "recreo", 0), getattr(guardia, "turno", None))
