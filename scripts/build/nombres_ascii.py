"""Nombres de fichero sin acentos para lo que va dentro de la aplicación (BLD-010).

macOS guarda los nombres de fichero descompuestos dentro del DMG (la «ñ» como
`n` más una tilde suelta) y compuestos cuando el Finder copia la aplicación a la
carpeta Aplicaciones. La firma sella los nombres tal como estaban al firmar, así
que uno solo con acento basta para que el sello deje de cuadrar y macOS diga que
la aplicación **está dañada y hay que llevarla a la papelera**. Pasó con
`880e0e1ef795_añadir_campo_algoritmo_asignacion_a_.py`, una migración de Alembic.

Aquí se hace una copia de esa carpeta con los nombres pasados a ASCII, que es lo
que se empaqueta. Alembic identifica cada revisión por la variable `revision` de
dentro del fichero, nunca por su nombre, así que no cambia nada para él. Los
ficheros del repositorio no se tocan: `alembic/versions/` está protegido.
"""

import shutil
import tempfile
import unicodedata
from pathlib import Path


def a_ascii(nombre: str) -> str:
    """`añadir_campo.py` → `anadir_campo.py`. Sin acentos no hay dos formas de escribirlo."""
    limpio = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode("ascii")
    return limpio or "sin_nombre"


def tiene_nombres_ambiguos(carpeta) -> list:
    """Los ficheros cuyo nombre puede normalizarse de dos maneras. Vacío es lo sano."""
    return [
        str(f)
        for f in sorted(Path(carpeta).rglob("*"))
        if f.is_file() and not f.name.isascii()
    ]


def copia_con_nombres_ascii(carpeta, destino=None) -> str:
    """Copia `carpeta` a un sitio temporal renombrando lo que lleve acentos.

    Devuelve la ruta de la copia, lista para dársela a PyInstaller.
    """
    origen = Path(carpeta)
    raiz = Path(destino or tempfile.mkdtemp(prefix="empaquetado-ascii-")) / origen.name
    if raiz.exists():
        shutil.rmtree(raiz)
    raiz.mkdir(parents=True)

    for actual in sorted(origen.rglob("*")):
        relativa = actual.relative_to(origen)
        final = raiz.joinpath(*[a_ascii(parte) for parte in relativa.parts])
        if actual.is_dir():
            final.mkdir(parents=True, exist_ok=True)
        else:
            final.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(actual, final)
    return str(raiz)
