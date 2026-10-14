"""Formatos de copia que acepta «Importar datos», además del suyo propio."""

from typing import Any, Optional

from sync import cifrado


def normalizar(datos: Any, clave: Optional[bytes]) -> dict:
    """Acepta también el volcado de la nube (`guardias_patio_data.json`).

    Ese fichero trae la configuración y los cursos como listas y las ausencias
    cifradas con la clave de la cuenta; importarlo tumbaba la restauración con
    las tablas ya vaciadas (2026-10-04).
    """
    if not isinstance(datos, dict):
        raise ValueError(f"el archivo debe contener un objeto JSON, no {type(datos).__name__}")
    config = datos.get("configuracion")
    if isinstance(config, list):
        datos["configuracion"] = config[0] if config else None
    cursos = datos.get("cursos_escolares")
    if isinstance(cursos, list):
        datos["cursos_escolares"] = {
            "cursos": [
                {**c, "fecha_creacion": c.get("fecha_creacion") or c.get("created_at")}
                for c in cursos
            ]
        }
    for a_data in datos.get("ausencias") or []:
        a_data["tipo"] = cifrado.descifrar(a_data.get("tipo"), clave)
        a_data["motivo"] = cifrado.descifrar(a_data.get("motivo"), clave)
    return datos
