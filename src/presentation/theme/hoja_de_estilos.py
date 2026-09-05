"""Construye la hoja de estilos de la aplicación a partir de los tokens.

`light.qss` no lleva colores escritos a mano: lleva marcadores `@TOKEN@` que se
sustituyen aquí por el valor de `tokens.Colors`. Así el color vive en un único
sitio y cambiar el primario no obliga a repasar la hoja (VIS-001, VIS-002).
"""

from __future__ import annotations

import re
from pathlib import Path

from presentation.theme.tokens import Colors, familias_del_sistema
from utils import get_logger

logger = get_logger(__name__)

RUTA_QSS = Path(__file__).parent / "light.qss"
_MARCADOR = re.compile(r"@([A-Z_]+)@")


def _valores() -> dict:
    valores = {
        nombre: valor
        for nombre, valor in vars(Colors).items()
        if isinstance(valor, str) and valor.startswith("#")
    }
    # La familia tipográfica depende del sistema operativo (VIS-003).
    valores["FONT_FAMILY"] = ", ".join(f'"{f}"' for f in familias_del_sistema())
    return valores


def construir_hoja_de_estilos(ruta: Path | None = None) -> str:
    """Devuelve el QSS con los marcadores ya resueltos."""
    ruta = ruta or RUTA_QSS
    if not ruta.exists():
        logger.warning(f"Hoja de estilos no encontrada: {ruta}")
        return ""

    valores = _valores()
    desconocidos = set()

    def sustituir(m):
        nombre = m.group(1)
        if nombre in valores:
            return valores[nombre]
        desconocidos.add(nombre)
        return m.group(0)

    hoja = _MARCADOR.sub(sustituir, ruta.read_text(encoding="utf-8"))
    if desconocidos:
        logger.error(f"Marcadores sin token en la hoja de estilos: {sorted(desconocidos)}")
    return hoja
