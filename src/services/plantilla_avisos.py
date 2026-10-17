"""Plantilla editable de los avisos de guardias por correo (GUA-CON-002).

Asunto y cuerpo los escribe Jefatura con unos pocos marcadores, y se elige si cada
aviso lleva adjuntos el calendario individual en PDF y el archivo iCal para el
calendario del móvil. Se guarda en `plantilla_avisos.json` de la carpeta de datos,
con la fecha de su última edición, y viaja con la sincronización: gana la edición
más reciente (`sync/plantilla_sync.py`, GUA-CON-004).

Marcadores: `{nombre}`, `{periodo}`, `{num_guardias}` y `{tabla}` (dónde va la
lista de guardias; si no está, va al final).
"""

from __future__ import annotations

import html as _html
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from core.logging import get_logger

logger = get_logger(__name__)

MARCADORES = {
    "nombre": "Nombre del profesor",
    "periodo": "Periodo del aviso (p. ej., «Octubre 2026»)",
    "num_guardias": "Cuántas guardias se le comunican",
    "tabla": "La lista de sus guardias (día, turno, recreo y zona)",
}

ASUNTO_DE_SERIE = "Guardias de patio — {periodo}"
CUERPO_DE_SERIE = (
    "Estimado/a {nombre},\n\n"
    "A continuación encontrarás tus guardias de patio asignadas para {periodo}:\n\n"
    "{tabla}\n\n"
    "Si tienes alguna duda, contacta con la dirección del centro."
)

_MARCADOR = re.compile(r"\{([^{}\s]*)\}")


@dataclass
class Plantilla:
    asunto: str = ASUNTO_DE_SERIE
    cuerpo: str = CUERPO_DE_SERIE
    adjuntar_pdf: bool = True
    adjuntar_ical: bool = True

    def errores(self) -> list[str]:
        """Lo que impide guardarla (vacío si vale)."""
        errores = []
        if not self.asunto.strip():
            errores.append("El asunto no puede quedar vacío.")
        if not self.cuerpo.strip():
            errores.append("El mensaje no puede quedar vacío.")
        desconocidos = sorted(
            {m for m in _MARCADOR.findall(self.asunto + self.cuerpo) if m not in MARCADORES}
        )
        if desconocidos:
            lista = ", ".join("{" + m + "}" for m in desconocidos)
            errores.append(
                f"Marcadores que no existen: {lista}. Valen: "
                + ", ".join("{" + m + "}" for m in MARCADORES)
                + "."
            )
        return errores


def _ruta() -> Path:
    from core.paths import get_data_directory

    return get_data_directory() / "plantilla_avisos.json"


def cargar() -> Plantilla:
    """La plantilla guardada, o la de serie si no hay o no se puede leer."""
    try:
        datos = json.loads(_ruta().read_text(encoding="utf-8"))
    except FileNotFoundError:
        return Plantilla()
    except (OSError, ValueError) as e:
        logger.warning(f"No se pudo leer la plantilla de avisos; se usa la de serie: {e}")
        return Plantilla()
    if not isinstance(datos, dict):
        return Plantilla()
    serie = Plantilla()
    plantilla = Plantilla(
        asunto=str(datos.get("asunto") or serie.asunto),
        cuerpo=str(datos.get("cuerpo") or serie.cuerpo),
        adjuntar_pdf=bool(datos.get("adjuntar_pdf", serie.adjuntar_pdf)),
        adjuntar_ical=bool(datos.get("adjuntar_ical", serie.adjuntar_ical)),
    )
    return serie if plantilla.errores() else plantilla


def guardar(plantilla: Plantilla, editada: str | None = None) -> None:
    """Guarda la plantilla con la fecha de edición (ahora, si no se da otra)."""
    errores = plantilla.errores()
    if errores:
        raise ValueError("\n".join(errores))
    ruta = _ruta()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    datos = {**asdict(plantilla), "editada": editada or datetime.now(timezone.utc).isoformat()}
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")


# --- Rellenar ---------------------------------------------------------------


def _sustituir(texto: str, valores: dict, envolver: Callable[[str], str]) -> str:
    def poner(m: re.Match) -> str:
        clave = m.group(1)
        return envolver(str(valores[clave])) if clave in valores else m.group(0)

    return _MARCADOR.sub(poner, texto)


def rellenar_asunto(plantilla: Plantilla, valores: dict) -> str:
    return _sustituir(plantilla.asunto, valores, str).replace("\n", " ").strip()


def rellenar_texto(plantilla: Plantilla, valores: dict, tabla_texto: str) -> str:
    """El cuerpo en texto plano, con la lista de guardias donde va `{tabla}`."""
    cuerpo = plantilla.cuerpo
    if "{tabla}" not in cuerpo:
        cuerpo = cuerpo.rstrip() + "\n\n{tabla}"
    return _sustituir(cuerpo, {**valores, "tabla": tabla_texto}, str)


def rellenar_html(plantilla: Plantilla, valores: dict, tabla_html: str) -> str:
    """El cuerpo en HTML: lo escrito va escapado, párrafo a párrafo."""
    cuerpo = plantilla.cuerpo
    if "{tabla}" not in cuerpo:
        cuerpo = cuerpo.rstrip() + "\n\n{tabla}"
    partes = cuerpo.split("{tabla}")
    trozos = []
    for i, parte in enumerate(partes):
        trozos.append(_parrafos(parte, valores))
        if i < len(partes) - 1:
            trozos.append(tabla_html)
    return "".join(trozos)


def _parrafos(texto: str, valores: dict) -> str:
    salida = []
    for bloque in re.split(r"\n\s*\n", texto.strip()):
        if not bloque.strip():
            continue
        escapado = _html.escape(bloque)
        # Los marcadores sobreviven al escape (no llevan caracteres especiales)
        relleno = _sustituir(escapado, valores, lambda v: f"<strong>{_html.escape(v)}</strong>")
        salida.append("<p>" + relleno.replace("\n", "<br>") + "</p>")
    return "".join(salida)
