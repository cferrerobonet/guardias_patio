"""Datos mínimos para la pantalla de guardias del patio (la web de la smart TV).

Tras cada subida se deja en `web/datos/<cuenta>.json` un resumen con lo único que
muestra la pantalla: recreos, zonas y quién tiene cada guardia. La web lo lee y no
escribe nada. Nunca debe romper la sincronización: cualquier fallo queda en el registro.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

RUTA_REMOTA = "web/datos/{cuenta}.json"
NOMBRE_LOCAL = "pantalla_guardias.json"

_RECREOS_POR_DEFECTO = (
    (1, "Recreo 1 Mañana", "mañana", "hora_recreo1_manana"),
    (2, "Recreo 2 Mañana", "mañana", "hora_recreo2_manana"),
    (3, "Recreo 1 Tarde", "tarde", "hora_recreo1_tarde"),
    (4, "Recreo 2 Tarde", "tarde", "hora_recreo2_tarde"),
)


def _recreos(configuracion: dict) -> list:
    """Recreos con su hora: los configurados a mano o, si no, los de las cuatro horas fijas."""
    try:
        configurados = json.loads(configuracion.get("recreos_config") or "[]")
    except (TypeError, ValueError):
        configurados = []
    recreos = [
        {k: r.get(k) for k in ("id", "etiqueta", "turno", "hora")}
        for r in configurados
        if isinstance(r, dict) and "id" in r
    ]
    if recreos:
        return recreos
    return [
        {"id": id_, "etiqueta": etiqueta, "turno": turno, "hora": configuracion.get(campo)}
        for id_, etiqueta, turno, campo in _RECREOS_POR_DEFECTO
        if configuracion.get(campo)
    ]


def resumen_para_pantalla(datos: dict) -> dict:
    """Reduce el volcado completo a lo que la pantalla necesita."""
    configuracion = (datos.get("configuracion") or [{}])[0] or {}
    nombres = {p["id"]: p.get("nombre_completo", "") for p in datos.get("profesores", [])}
    return {
        "publicado": datetime.now().isoformat(timespec="seconds"),
        "recreos": _recreos(configuracion),
        "zonas": [
            {"id": z["id"], "nombre": z.get("nombre_zona"), "descripcion": z.get("descripcion")}
            for z in datos.get("zonas", [])
        ],
        "guardias": [
            {
                "fecha": g["fecha"],
                "turno": g["turno"],
                "recreo": g["recreo"],
                "zona_id": g["zona_id"],
                "profesor": nombres.get(g["profesor_id"], ""),
            }
            for g in datos.get("guardias", [])
            if nombres.get(g.get("profesor_id"))
        ],
    }


def publicar_pantalla(gestor, volcado: Path) -> None:
    """Sube el resumen de la pantalla. `gestor` es el `SyncManager`; `volcado`, el JSON subido."""
    ruta_local: Optional[Path] = None
    try:
        datos = json.loads(volcado.read_text(encoding="utf-8"))
        ruta_local = gestor.local_data_dir / NOMBRE_LOCAL
        ruta_local.write_text(
            json.dumps(resumen_para_pantalla(datos), ensure_ascii=False), encoding="utf-8"
        )
        if not gestor.backend.upload_file(ruta_local, RUTA_REMOTA.format(cuenta=gestor.user_hash)):
            logger.warning("No se pudo publicar el resumen de la pantalla de guardias")
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as e:
        logger.warning(f"No se pudo publicar el resumen de la pantalla de guardias: {e}")
