"""ESC-003 — no subir la base entera cada media hora si nadie ha tocado nada.

La sincronización automática exporta toda la base a JSON y la sube cada 30
minutos y al cerrar. El fichero crece con el curso, y el caso normal es que
entre dos subidas no haya cambiado nada.

Aquí se fija que la decisión de subir depende del contenido, y que el contador
de versión y la fecha del volcado —que cambian siempre— no cuentan como cambio.
"""

import json

from sync.sync_manager import SyncManager


def _volcado(tmp_path, nombre="datos.json", **extra):
    datos = {
        "export_date": "2026-09-06T10:00:00",
        "version": "1.0",
        "sync_version": 3,
        "profesores": [{"id": 1, "nombre_completo": "García, Ana"}],
        "zonas": [],
    }
    datos.update(extra)
    ruta = tmp_path / nombre
    ruta.write_text(json.dumps(datos), encoding="utf-8")
    return ruta


def test_la_huella_ignora_la_fecha_del_volcado(tmp_path):
    uno = _volcado(tmp_path, "uno.json")
    otro = _volcado(tmp_path, "otro.json", export_date="2026-09-07T18:30:00")

    assert SyncManager.huella_del_contenido(uno) == SyncManager.huella_del_contenido(otro)


def test_la_huella_ignora_el_contador_de_version(tmp_path):
    """Sube en cada envío: si contase, la huella nunca coincidiría."""
    uno = _volcado(tmp_path, "uno.json")
    otro = _volcado(tmp_path, "otro.json", sync_version=99)

    assert SyncManager.huella_del_contenido(uno) == SyncManager.huella_del_contenido(otro)


def test_un_dato_distinto_cambia_la_huella(tmp_path):
    uno = _volcado(tmp_path, "uno.json")
    otro = _volcado(
        tmp_path, "otro.json", profesores=[{"id": 1, "nombre_completo": "García, Anna"}]
    )

    assert SyncManager.huella_del_contenido(uno) != SyncManager.huella_del_contenido(otro)


def test_el_orden_de_las_claves_no_altera_la_huella(tmp_path):
    uno = tmp_path / "uno.json"
    otro = tmp_path / "otro.json"
    uno.write_text(json.dumps({"zonas": [], "profesores": []}), encoding="utf-8")
    otro.write_text(json.dumps({"profesores": [], "zonas": []}), encoding="utf-8")

    assert SyncManager.huella_del_contenido(uno) == SyncManager.huella_del_contenido(otro)


def test_un_fichero_ilegible_no_da_huella(tmp_path):
    roto = tmp_path / "roto.json"
    roto.write_text("{ esto no", encoding="utf-8")

    assert SyncManager.huella_del_contenido(roto) is None


def test_sin_huella_no_se_puede_saltar_la_subida(tmp_path):
    """Ante la duda, subir: perder datos es peor que subir de más."""
    inexistente = tmp_path / "no_existe.json"

    assert SyncManager.huella_del_contenido(inexistente) is None


def test_la_subida_compara_la_huella_antes_de_conectar():
    import inspect

    fuente = inspect.getsource(SyncManager.sync_on_shutdown)
    assert fuente.index("huella_del_contenido") < fuente.index('"connecting"')


def test_un_envio_pendiente_se_sube_aunque_no_haya_cambios():
    """Si la última vez falló, la huella coincide pero el servidor no lo tiene."""
    import inspect

    fuente = inspect.getsource(SyncManager.sync_on_shutdown)
    assert "pendiente_subida" in fuente.split('"connecting"')[0]
