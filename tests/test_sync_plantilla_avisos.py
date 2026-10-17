"""GUA-CON-004: la plantilla de los avisos viaja con la sincronización.

Va dentro del volcado que se sube a la nube y, al descargar, gana la edición más
reciente. Un equipo que ya tenía la suya la conserva la primera vez y la sube, y
ningún equipo pierde su plantilla: si la nube trae una más reciente, la local se
guarda antes en `plantilla_avisos.anterior.json`.
"""

import json
import os
from datetime import datetime, timedelta, timezone

import pytest

from services import plantilla_avisos
from services.plantilla_avisos import Plantilla
from sync import plantilla_sync
from sync.data_exporter import DataExporter
from sync.sync_manager import SyncManager

AHORA = datetime(2026, 10, 17, 9, 0, tzinfo=timezone.utc)


@pytest.fixture
def equipos(monkeypatch, tmp_path):
    """Dos equipos con su carpeta de datos; `usar("a")` hace de ese el actual."""
    carpetas = {nombre: tmp_path / nombre for nombre in ("a", "b")}
    for carpeta in carpetas.values():
        carpeta.mkdir()

    def usar(nombre):
        monkeypatch.setattr(
            plantilla_avisos, "_ruta", lambda: carpetas[nombre] / "plantilla_avisos.json"
        )
        return carpetas[nombre]

    usar("a")
    return usar


def _propia(asunto: str, editada: datetime | None = None) -> Plantilla:
    plantilla = Plantilla(asunto=asunto, cuerpo="Hola {nombre}:\n\n{tabla}", adjuntar_pdf=False)
    plantilla_avisos.guardar(plantilla, editada=editada.isoformat() if editada else None)
    return plantilla


def _antigua(asunto: str, modificada: datetime) -> None:
    """Una plantilla guardada antes de la 7.5.2: sin fecha de edición."""
    ruta = plantilla_avisos._ruta()
    ruta.write_text(
        json.dumps({"asunto": asunto, "cuerpo": "Hola {nombre}", "adjuntar_pdf": True}),
        encoding="utf-8",
    )
    os.utime(ruta, (modificada.timestamp(), modificada.timestamp()))


def _volcado(session, ruta, version=1) -> dict:
    assert DataExporter.export_to_json(session, ruta, sync_version=version)
    return json.loads(ruta.read_text(encoding="utf-8"))


def _descargar(session, ruta) -> None:
    assert DataExporter.import_from_json(session, ruta, clear_existing=True)


# --- Sube con los datos -------------------------------------------------------


def test_la_plantilla_viaja_en_el_volcado(session, equipos, tmp_path):
    _propia("Tus guardias de {periodo}", AHORA)

    datos = _volcado(session, tmp_path / "nube.json")

    assert datos["plantilla_avisos"]["asunto"] == "Tus guardias de {periodo}"
    assert datos["plantilla_avisos"]["adjuntar_pdf"] is False
    assert datos["plantilla_avisos"]["editada"] == AHORA.isoformat()


def test_sin_plantilla_propia_no_se_sube_la_de_serie(session, equipos, tmp_path):
    assert "plantilla_avisos" not in _volcado(session, tmp_path / "nube.json")


def test_editar_la_plantilla_cambia_la_huella_y_se_sube(session, equipos, tmp_path):
    _propia("Primera", AHORA)
    ruta = tmp_path / "nube.json"
    _volcado(session, ruta)
    antes = SyncManager.huella_del_contenido(ruta)

    _propia("Segunda", AHORA + timedelta(minutes=5))
    _volcado(session, ruta)

    assert SyncManager.huella_del_contenido(ruta) != antes


# --- La primera vez -------------------------------------------------------------


def test_la_primera_vez_el_equipo_conserva_la_suya_y_la_sube(session, equipos, tmp_path):
    """La nube tiene un volcado de una versión anterior, sin plantilla."""
    ruta = tmp_path / "nube.json"
    _volcado(session, ruta)
    _antigua("La de este equipo", AHORA - timedelta(days=3))

    _descargar(session, ruta)

    assert plantilla_avisos.cargar().asunto == "La de este equipo"
    subida = _volcado(session, ruta, version=2)["plantilla_avisos"]
    assert subida["asunto"] == "La de este equipo"
    assert plantilla_sync._fecha(subida["editada"]) == AHORA - timedelta(days=3)


def test_un_equipo_sin_plantilla_toma_la_de_la_nube(session, equipos, tmp_path):
    ruta = tmp_path / "nube.json"
    _propia("La del equipo A", AHORA)
    _volcado(session, ruta)

    equipos("b")
    _descargar(session, ruta)

    plantilla = plantilla_avisos.cargar()
    assert plantilla.asunto == "La del equipo A"
    assert plantilla.adjuntar_pdf is False


# --- Gana la última edición ----------------------------------------------------


def test_gana_la_de_la_nube_si_es_mas_reciente_y_la_local_se_guarda(session, equipos, tmp_path):
    ruta = tmp_path / "nube.json"
    carpeta_b = equipos("b")
    _propia("La vieja de B", AHORA - timedelta(days=1))

    equipos("a")
    _propia("La nueva de A", AHORA)
    _volcado(session, ruta)

    equipos("b")
    _descargar(session, ruta)

    assert plantilla_avisos.cargar().asunto == "La nueva de A"
    anterior = json.loads((carpeta_b / "plantilla_avisos.anterior.json").read_text("utf-8"))
    assert anterior["asunto"] == "La vieja de B"


def test_se_queda_la_local_si_es_mas_reciente(session, equipos, tmp_path):
    ruta = tmp_path / "nube.json"
    _propia("La vieja de A", AHORA - timedelta(days=1))
    _volcado(session, ruta)

    carpeta_b = equipos("b")
    _propia("La nueva de B", AHORA)
    _descargar(session, ruta)

    assert plantilla_avisos.cargar().asunto == "La nueva de B"
    assert not (carpeta_b / "plantilla_avisos.anterior.json").exists()
    assert _volcado(session, ruta, version=2)["plantilla_avisos"]["asunto"] == "La nueva de B"


def test_una_plantilla_antigua_compite_por_la_fecha_del_fichero(session, equipos, tmp_path):
    ruta = tmp_path / "nube.json"
    _propia("La de A", AHORA - timedelta(days=2))
    _volcado(session, ruta)

    equipos("b")
    _antigua("La de B, de antes de la 7.5.2", AHORA - timedelta(days=1))
    _descargar(session, ruta)

    assert plantilla_avisos.cargar().asunto == "La de B, de antes de la 7.5.2"


# --- Nada se pierde -------------------------------------------------------------


@pytest.mark.parametrize(
    "remota",
    [
        None,
        "texto",
        {"asunto": "", "cuerpo": "Hola", "editada": AHORA.isoformat()},
        {"asunto": "Hola {inexistente}", "cuerpo": "Hola", "editada": AHORA.isoformat()},
        {"asunto": "Sin fecha", "cuerpo": "Hola"},
    ],
)
def test_una_plantilla_de_la_nube_que_no_vale_no_toca_la_local(equipos, remota):
    _propia("La de este equipo", AHORA - timedelta(days=30))

    assert plantilla_sync.aplicar_descargada(remota) is False
    assert plantilla_avisos.cargar().asunto == "La de este equipo"


def test_ningun_equipo_pierde_su_plantilla_en_una_vuelta_completa(session, equipos, tmp_path):
    """A edita, sube; B descarga, edita, sube; A descarga: cada edición queda en algún sitio."""
    ruta = tmp_path / "nube.json"
    carpeta_a = equipos("a")
    _propia("A, lunes", AHORA)
    _volcado(session, ruta, version=1)

    equipos("b")
    _descargar(session, ruta)
    assert plantilla_avisos.cargar().asunto == "A, lunes"
    _propia("B, martes", AHORA + timedelta(days=1))
    _volcado(session, ruta, version=2)

    equipos("a")
    _descargar(session, ruta)

    assert plantilla_avisos.cargar().asunto == "B, martes"
    anterior = json.loads((carpeta_a / "plantilla_avisos.anterior.json").read_text("utf-8"))
    assert anterior["asunto"] == "A, lunes"


def test_guardar_anota_la_fecha_de_edicion(equipos):
    plantilla_avisos.guardar(Plantilla(asunto="Con fecha"))

    datos = json.loads(plantilla_avisos._ruta().read_text(encoding="utf-8"))
    editada = plantilla_sync._fecha(datos["editada"])
    assert editada is not None
    assert abs(datetime.now(timezone.utc) - editada) < timedelta(minutes=1)
