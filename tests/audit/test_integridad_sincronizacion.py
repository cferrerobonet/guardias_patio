"""Lote 20 — integridad de la sincronización (SYNC-018, 019, 020, 021, 022).

Lo que se fija aquí:
- el bloqueo de sesión aguanta latidos perdidos y se suelta al cerrar;
- el volcado viaja con su huella y un fichero dañado no se acepta;
- la rotación de copias funciona también en un servidor SFTP sin `posix-rename`;
- la segunda subida sin cambios no toca el servidor.
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from infrastructure.database.models import Base, Zona
from sync.backends import LocalSyncBackend, SFTPSyncBackend
from sync.integridad import NOMBRE_HUELLA, huella_del_fichero
from sync.session_lock import SessionLock
from sync.sync_manager import SyncManager

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"


def _base_de_datos():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()


@pytest.fixture
def nube(tmp_path):
    return LocalSyncBackend(tmp_path / "nube")


@pytest.fixture
def equipo(tmp_path, nube):
    def _crear(nombre: str, backend=None):
        carpeta = tmp_path / nombre
        carpeta.mkdir(parents=True, exist_ok=True)
        with patch("sync.sync_manager.get_user_data_directory", return_value=carpeta):
            gestor = SyncManager(backend or nube, "jefatura")
        return gestor, _base_de_datos()

    return _crear


@pytest.fixture
def bloqueo(tmp_path, nube):
    def _crear(nombre: str, backend=None):
        carpeta = tmp_path / f"lock_{nombre}"
        carpeta.mkdir(parents=True, exist_ok=True)
        with patch("sync.session_lock.get_user_data_directory", return_value=carpeta):
            candado = SessionLock(backend or nube, "jefatura", "hash")
        candado._get_local_lock_path = lambda: carpeta / "hash" / "session.lock"
        return candado

    return _crear


def _subir_bloqueo(nube, tmp_path, candado, **campos):
    datos = {
        "username": "jefatura",
        "hostname": "otro",
        "ip_address": "10.0.0.2",
        "pid": 1,
        "started_at": datetime.now().isoformat(),
        "last_heartbeat": datetime.now().isoformat(),
    }
    datos.update(campos)
    fichero = tmp_path / "ajeno.lock"
    fichero.write_text(json.dumps(datos), encoding="utf-8")
    nube.upload_file(fichero, candado._get_remote_lock_path())


# ---------------------------------------------------------------------------
# SYNC-018 · caducidad del bloqueo
# ---------------------------------------------------------------------------
def test_la_caducidad_del_bloqueo_da_margen_a_tres_latidos(bloqueo):
    candado = bloqueo("a")
    assert candado.lock_timeout >= 3 * candado.heartbeat_interval


def test_un_latido_perdido_no_deja_entrar_a_otro_equipo(bloqueo, nube, tmp_path):
    candado = bloqueo("b")
    retraso = candado.heartbeat_interval * 1.5
    _subir_bloqueo(
        nube, tmp_path, candado,
        last_heartbeat=(datetime.now() - timedelta(seconds=retraso)).isoformat(),
    )
    assert candado.acquire_lock() is False


def test_un_bloqueo_ilegible_cuenta_como_caducado(bloqueo, nube, tmp_path):
    """Antes `fromisoformat("")` reventaba el arranque; ahora se entra."""
    candado = bloqueo("c")
    _subir_bloqueo(nube, tmp_path, candado, last_heartbeat="")
    assert candado.acquire_lock() is True


# ---------------------------------------------------------------------------
# SYNC-019 · liberación remota al cerrar
# ---------------------------------------------------------------------------
def test_al_cerrar_el_siguiente_equipo_entra_sin_esperar(bloqueo, nube):
    primero, segundo = bloqueo("d1"), bloqueo("d2")
    assert primero.acquire_lock() is True
    assert segundo.acquire_lock() is False

    primero.release_lock()

    assert not nube.file_exists(primero._get_remote_lock_path())
    assert segundo.acquire_lock() is True


def test_si_el_backend_no_sabe_borrar_el_bloqueo_queda_marcado_como_liberado(bloqueo, tmp_path):
    class SinBorrado(LocalSyncBackend):
        def delete_file(self, remote_path):
            return False

    servidor = SinBorrado(tmp_path / "servidor_viejo")
    primero, segundo = bloqueo("e1", servidor), bloqueo("e2", servidor)
    assert primero.acquire_lock() is True
    primero.release_lock()

    assert servidor.file_exists(primero._get_remote_lock_path())
    assert segundo.acquire_lock() is True


def test_soltar_un_bloqueo_que_no_se_tenia_no_toca_el_servidor(bloqueo, nube):
    ajeno, mio = bloqueo("f1"), bloqueo("f2")
    ajeno.acquire_lock()
    assert mio.release_lock() is True
    assert nube.file_exists(ajeno._get_remote_lock_path())


# ---------------------------------------------------------------------------
# SYNC-020 · huella junto al volcado
# ---------------------------------------------------------------------------
def _primer_curso(equipo, nombre="portatil"):
    gestor, bd = equipo(nombre)
    assert gestor.sync_on_startup(session=bd) is True
    bd.add(Zona(nombre_zona="Patio"))
    bd.commit()
    assert gestor.sync_on_shutdown(session=bd) is True
    return gestor, bd


def test_la_huella_viaja_junto_al_volcado(equipo, nube, tmp_path):
    gestor, _ = _primer_curso(equipo)
    remota = gestor.get_remote_path(NOMBRE_HUELLA)
    assert nube.file_exists(remota)

    destino = tmp_path / "huella.json"
    nube.download_file(remota, destino)
    huella = json.loads(destino.read_text(encoding="utf-8"))
    volcado = tmp_path / "volcado.json"
    nube.download_file(gestor.get_remote_path("guardias_patio_data.json"), volcado)
    assert huella["sync_version"] == gestor.version_descargada
    assert huella["sha256"] == huella_del_fichero(volcado)


def test_un_volcado_danado_con_una_seccion_valida_no_se_acepta(equipo, nube, tmp_path):
    gestor, bd = _primer_curso(equipo)
    otro, bd_otro = equipo("sobremesa")

    # El fichero del servidor pierde casi todo pero sigue siendo un JSON con una
    # sección conocida: la comprobación estructural lo daba por bueno.
    dañado = tmp_path / "danado.json"
    dañado.write_text(
        json.dumps({"sync_version": gestor.version_descargada, "zonas": []}), encoding="utf-8"
    )
    nube.upload_file(dañado, gestor.get_remote_path("guardias_patio_data.json"))

    assert otro.sync_on_startup(session=bd_otro) is False
    assert otro.puede_subir is False
    assert "huella" in (otro.motivo_bloqueo or "")


def test_una_huella_de_otra_version_no_bloquea(equipo, nube, tmp_path):
    """Si falló subir la huella, la del servidor es de la versión anterior: se ignora."""
    gestor, bd = _primer_curso(equipo)
    vieja = tmp_path / "vieja.json"
    vieja.write_text(
        json.dumps({"sync_version": gestor.version_descargada - 1, "sha256": "0" * 64}),
        encoding="utf-8",
    )
    nube.upload_file(vieja, gestor.get_remote_path(NOMBRE_HUELLA))

    otro, bd_otro = equipo("sobremesa")
    assert otro.sync_on_startup(session=bd_otro) is True
    assert [z.nombre_zona for z in bd_otro.query(Zona).all()] == ["Patio"]


def test_sin_huella_en_el_servidor_se_sigue_aceptando(equipo, nube, tmp_path):
    """Subidas anteriores a esta versión no dejaron huella y tienen que poder bajarse."""
    gestor, _ = _primer_curso(equipo)
    nube.delete_file(gestor.get_remote_path(NOMBRE_HUELLA))

    otro, bd_otro = equipo("sobremesa")
    assert otro.sync_on_startup(session=bd_otro) is True


# ---------------------------------------------------------------------------
# SYNC-022 · la metadata local no se pisa tras subir
# ---------------------------------------------------------------------------
def test_la_segunda_subida_sin_cambios_no_toca_el_servidor(equipo, nube):
    gestor, bd = _primer_curso(equipo)
    metadata = gestor._leer_metadata_local()
    assert metadata.get("huella_subida"), "la huella tiene que sobrevivir al cierre"
    assert metadata.get("sync_version") == gestor.version_descargada

    with patch.object(LocalSyncBackend, "upload_file", wraps=nube.upload_file) as subida:
        assert gestor.sync_on_shutdown(session=bd) is True
    assert subida.call_count == 0


# ---------------------------------------------------------------------------
# SYNC-021 · rotación de copias en un servidor SFTP real (sin posix-rename)
# ---------------------------------------------------------------------------
class _ServidorSFTPFalso:
    """Imita lo justo de `paramiko.SFTPClient` con la semántica estricta de SFTP:
    `rename` falla si el destino existe y `posix-rename` no está soportado."""

    def __init__(self, base_dir):
        self.ficheros = {}
        self.carpetas = {base_dir}

    def stat(self, ruta):
        if ruta not in self.ficheros and ruta not in self.carpetas:
            raise FileNotFoundError(ruta)
        return object()

    def mkdir(self, ruta):
        self.carpetas.add(ruta)

    def put(self, local, remoto):
        self.ficheros[remoto] = Path(local).read_bytes()

    def get(self, remoto, local):
        if remoto not in self.ficheros:
            raise FileNotFoundError(remoto)
        Path(local).write_bytes(self.ficheros[remoto])

    def posix_rename(self, origen, destino):
        raise OSError("Operation unsupported")

    def rename(self, origen, destino):
        if origen not in self.ficheros:
            raise FileNotFoundError(origen)
        if destino in self.ficheros:
            raise OSError("Failure")
        self.ficheros[destino] = self.ficheros.pop(origen)

    def remove(self, ruta):
        if ruta not in self.ficheros:
            raise FileNotFoundError(ruta)
        del self.ficheros[ruta]


@pytest.fixture
def sftp_falso():
    backend = SFTPSyncBackend.__new__(SFTPSyncBackend)
    backend.base_dir = "/guardias_patio"
    backend.client = None
    backend.sftp = _ServidorSFTPFalso(backend.base_dir)
    return backend


def test_la_rotacion_deja_copias_en_un_servidor_sftp_sin_posix_rename(equipo, sftp_falso):
    gestor, bd = equipo("portatil", sftp_falso)
    assert gestor.sync_on_startup(session=bd) is True
    for nombre in ("Primera", "Segunda", "Tercera"):
        bd.add(Zona(nombre_zona=nombre))
        bd.commit()
        assert gestor.sync_on_shutdown(session=bd) is True

    nombres = set(sftp_falso.sftp.ficheros)
    base = f"{sftp_falso.base_dir}/{gestor.get_remote_path('guardias_patio_data.json')}"
    assert base in nombres
    assert f"{base}.1" in nombres and f"{base}.2" in nombres
    assert not any(n.endswith(".tmp") for n in nombres), "no pueden quedar temporales"


def test_el_bloqueo_se_borra_tambien_por_sftp(bloqueo, sftp_falso):
    candado = bloqueo("g", sftp_falso)
    assert candado.acquire_lock() is True
    ruta = f"{sftp_falso.base_dir}/{candado._get_remote_lock_path()}"
    assert ruta in sftp_falso.sftp.ficheros
    candado.release_lock()
    assert ruta not in sftp_falso.sftp.ficheros


# ---------------------------------------------------------------------------
# CHK-K-08 · ficheros de estado en UTF-8 (COD-010, parte de sync)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("modulo", ["sync/session_lock.py", "sync/sync_manager.py"])
def test_los_ficheros_de_estado_de_sync_se_escriben_en_utf8(modulo):
    fuente = (SRC / modulo).read_text(encoding="utf-8")
    sin_codificacion = [
        linea.strip()
        for linea in fuente.splitlines()
        if re.search(r"\bopen\(|fdopen\(", linea)
        and "os.open(" not in linea
        and "encoding=" not in linea
    ]
    assert sin_codificacion == [], sin_codificacion
