import json
from types import SimpleNamespace

from sync.pantalla import publicar_pantalla, resumen_para_pantalla

VOLCADO = {
    "profesores": [
        {"id": 1, "nombre_completo": "ALIAGA REVERT, JORDI", "email_corporativo": "a@b.c"}
    ],
    "zonas": [{"id": 7, "nombre_zona": "Z1", "descripcion": "Patio", "activa": True}],
    "configuracion": [{"hora_recreo1_manana": "09:40", "hora_recreo2_manana": "10:40"}],
    "guardias": [
        {"fecha": "2026-10-21", "turno": "mañana", "recreo": 1, "zona_id": 7, "profesor_id": 1},
        {"fecha": "2026-10-21", "turno": "mañana", "recreo": 2, "zona_id": 7, "profesor_id": 99},
    ],
}


def test_resumen_solo_lleva_lo_que_muestra_la_pantalla():
    resumen = resumen_para_pantalla(VOLCADO)
    assert resumen["guardias"] == [
        {"fecha": "2026-10-21", "turno": "mañana", "recreo": 1, "zona_id": 7,
         "profesor": "ALIAGA REVERT, JORDI"}
    ]
    assert resumen["zonas"] == [{"id": 7, "nombre": "Z1", "descripcion": "Patio"}]
    assert [r["hora"] for r in resumen["recreos"]] == ["09:40", "10:40"]
    assert "a@b.c" not in json.dumps(resumen)


def test_publicar_sube_a_la_carpeta_de_la_web(tmp_path):
    volcado = tmp_path / "datos.json"
    volcado.write_text(json.dumps(VOLCADO), encoding="utf-8")
    subidas = []
    gestor = SimpleNamespace(
        local_data_dir=tmp_path,
        user_hash="0123456789abcdef",
        backend=SimpleNamespace(upload_file=lambda local, remoto: subidas.append(remoto) or True),
    )
    publicar_pantalla(gestor, volcado)
    assert subidas == ["web/datos/0123456789abcdef.json"]


def test_un_fallo_nunca_rompe_la_sincronizacion(tmp_path):
    gestor = SimpleNamespace(local_data_dir=tmp_path, user_hash="x", backend=None)
    publicar_pantalla(gestor, tmp_path / "no_existe.json")
