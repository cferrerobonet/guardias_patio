"""BLD-010 — ningún nombre de fichero con acentos dentro de la aplicación.

macOS escribe los nombres descompuestos dentro del DMG y compuestos al copiar la
aplicación a Aplicaciones. La firma sella los nombres tal cual estaban, así que
uno solo con acento hace que el sello deje de cuadrar y el sistema diga que la
aplicación está dañada. Le pasó a la v6.0.1 con una migración de Alembic.
"""

import sys
import unicodedata
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "scripts" / "build"))

from nombres_ascii import a_ascii, copia_con_nombres_ascii, tiene_nombres_ambiguos  # noqa: E402


def test_quita_los_acentos_del_nombre():
    assert a_ascii("880e0e1ef795_añadir_campo.py") == "880e0e1ef795_anadir_campo.py"
    assert a_ascii("normal.py") == "normal.py"
    assert a_ascii("ñ") == "n"
    assert a_ascii("日本語") == "sin_nombre"


def test_da_igual_como_venga_escrita_la_ene():
    """Las dos formas de escribir «ñ» tienen que acabar en el mismo nombre."""
    compuesta = unicodedata.normalize("NFC", "añadir.py")
    descompuesta = unicodedata.normalize("NFD", "añadir.py")
    assert compuesta != descompuesta, "el caso a evitar es justo que difieran"
    assert a_ascii(compuesta) == a_ascii(descompuesta) == "anadir.py"


def test_la_copia_conserva_el_contenido_y_la_estructura(tmp_path):
    origen = tmp_path / "alembic"
    (origen / "versions").mkdir(parents=True)
    (origen / "env.py").write_text("# entorno", encoding="utf-8")
    (origen / "versions" / "abc_añadir.py").write_text("revision = 'abc'", encoding="utf-8")

    copia = Path(copia_con_nombres_ascii(origen, destino=tmp_path / "salida"))

    assert (copia / "env.py").read_text(encoding="utf-8") == "# entorno"
    migracion = copia / "versions" / "abc_anadir.py"
    assert migracion.read_text(encoding="utf-8") == "revision = 'abc'"
    assert tiene_nombres_ambiguos(copia) == []


def test_el_paquete_no_lleva_ningun_nombre_con_acentos(tmp_path):
    """El caso real: la carpeta de migraciones del proyecto, tal como se empaqueta."""
    ambiguos = tiene_nombres_ambiguos(RAIZ / "alembic")
    assert ambiguos, "si ya no hay ninguno, este test deja de proteger de nada"

    copia = copia_con_nombres_ascii(RAIZ / "alembic", destino=tmp_path)
    assert tiene_nombres_ambiguos(copia) == []


def test_las_revisiones_siguen_siendo_las_mismas(tmp_path):
    """Alembic va por la variable `revision`, no por el nombre del fichero."""
    import re

    def revisiones(carpeta):
        encontradas = set()
        for f in Path(carpeta).rglob("*.py"):
            patron = r"^revision:?\s*(?::\s*str\s*)?=\s*['\"]([^'\"]+)"
            m = re.search(patron, f.read_text(encoding="utf-8"), re.M)
            if m:
                encontradas.add(m.group(1))
        return encontradas

    originales = revisiones(RAIZ / "alembic" / "versions")
    assert originales, "no se han encontrado migraciones"
    copia = copia_con_nombres_ascii(RAIZ / "alembic", destino=tmp_path)
    assert revisiones(Path(copia) / "versions") == originales


def test_el_spec_usa_la_copia_sin_acentos():
    fuente = (RAIZ / "GuardiasDePatio.spec").read_text(encoding="utf-8")
    assert "copia_con_nombres_ascii('alembic')" in fuente
    assert "('alembic', 'alembic')" not in fuente, "así se empaquetaba antes, con la «ñ»"


def test_no_se_ha_tocado_la_migracion_protegida():
    """`alembic/versions/` es zona protegida: el renombrado ocurre sólo al empaquetar."""
    assert (RAIZ / "alembic/versions/880e0e1ef795_añadir_campo_algoritmo_asignacion_a_.py").exists()
