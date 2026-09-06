"""COD-008 — módulos que habían crecido demasiado.

`sync_manager.py` pasaba de las 1.200 líneas y mezclaba dos cosas que no tienen
por qué ir juntas: *cómo* se sube un fichero —por SFTP, o a una carpeta local
cuando se prueba— y *qué* se sube y cuándo. Lo primero se ha llevado a
`sync/backends.py`.

El resto de módulos grandes son vistas: partir una vista por tamaño reparte el
mismo código entre dos ficheros que sólo se usan juntos, así que sólo compensa
cuando hay una costura real como ésta.
"""

from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
SRC = RAIZ / "src"

#: Sólo puede bajar. Era 1.227 antes de sacar los backends.
TECHO_SYNC_MANAGER = 730

#: Cuántos módulos pasan de 778 líneas. Era 7 con `sync_manager` dentro.
MODULOS_GRANDES = 6


def _lineas(ruta: Path) -> int:
    return len(ruta.read_text(encoding="utf-8", errors="ignore").splitlines())


def test_sync_manager_ya_no_lleva_los_backends():
    assert _lineas(SRC / "sync" / "sync_manager.py") <= TECHO_SYNC_MANAGER


def test_los_backends_viven_en_su_modulo():
    backends = SRC / "sync" / "backends.py"
    texto = backends.read_text(encoding="utf-8")
    for clase in ("class SyncBackend(ABC):", "class LocalSyncBackend", "class SFTPSyncBackend"):
        assert clase in texto


@pytest.mark.parametrize(
    "nombre",
    ["SyncBackend", "LocalSyncBackend", "SFTPSyncBackend", "ERRORES_DE_TRANSPORTE"],
)
def test_se_siguen_importando_desde_donde_estaban(nombre):
    """Medio programa los importa de `sync_manager`: mover no puede romper eso."""
    import sync.sync_manager as modulo

    assert hasattr(modulo, nombre)


def test_no_crecen_los_modulos_grandes():
    grandes = [
        str(f.relative_to(SRC))
        for f in SRC.rglob("*.py")
        if "__pycache__" not in f.parts and "egg-info" not in str(f) and _lineas(f) > 778
    ]
    assert len(grandes) <= MODULOS_GRANDES, f"Módulos por encima de 778 líneas: {grandes}"
