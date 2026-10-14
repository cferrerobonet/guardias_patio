"""Sincronización en la nube: escenarios de dos equipos y hallazgos pendientes.

El modelo es «la copia de la nube es la buena»: una cuenta la usa una persona, que
puede cambiar de equipo, y el flujo es descargar, editar y subir. Ver auditoria/12.

Los tests marcados xfail(strict=True) describen lo que aún falta (Fase 2).
"""

import inspect
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from infrastructure.database.models import Base, Profesor, Zona
from sync.data_exporter import DataExporter
from sync.sync_manager import LocalSyncBackend, SyncManager

ROOT = Path(__file__).resolve().parents[2]


def _base_de_datos():
    """Una base de datos propia, como la que tendría cada equipo."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()


@pytest.fixture
def nube(tmp_path):
    """El servidor compartido por todos los equipos."""
    return LocalSyncBackend(tmp_path / "nube")


@pytest.fixture
def equipo(tmp_path, nube):
    """Fabrica equipos distintos que comparten cuenta y servidor."""

    def _crear(nombre: str, usuario: str = "jefatura"):
        carpeta = tmp_path / nombre
        carpeta.mkdir(parents=True, exist_ok=True)
        with patch("sync.sync_manager.get_user_data_directory", return_value=carpeta):
            gestor = SyncManager(nube, usuario)
        return gestor, _base_de_datos()

    return _crear


# ---------------------------------------------------------------------------
# El escenario que se pide: cambiar de equipo sin perder nada
# ---------------------------------------------------------------------------
def test_cambiar_de_equipo_lleva_los_datos(equipo):
    portatil, bd_portatil = equipo("portatil")
    sobremesa, bd_sobremesa = equipo("sobremesa")

    # En el portátil se da de alta el curso.
    assert portatil.sync_on_startup(session=bd_portatil) is True
    bd_portatil.add(Zona(nombre_zona="Patio Principal"))
    bd_portatil.add(
        Profesor(
            nombre_completo="García, Ana",
            horas_contrato=25.0,
            porcentaje_jornada=100,
            turno="mañana",
        )
    )
    bd_portatil.commit()
    assert portatil.sync_on_shutdown(session=bd_portatil) is True

    # Al día siguiente se sigue desde el sobremesa.
    assert sobremesa.sync_on_startup(session=bd_sobremesa) is True
    assert [z.nombre_zona for z in bd_sobremesa.query(Zona).all()] == ["Patio Principal"]
    assert [p.nombre_completo for p in bd_sobremesa.query(Profesor).all()] == ["García, Ana"]


def test_una_baja_hecha_en_un_equipo_llega_al_otro(equipo):
    """SYNC-006: antes el registro eliminado reaparecía en la siguiente sincronización."""
    portatil, bd_portatil = equipo("portatil")
    sobremesa, bd_sobremesa = equipo("sobremesa")

    portatil.sync_on_startup(session=bd_portatil)
    bd_portatil.add_all(
        [
            Profesor(
                nombre_completo="García, Ana",
                horas_contrato=25.0,
                porcentaje_jornada=100,
                turno="mañana",
            ),
            Profesor(
                nombre_completo="López, Luis",
                horas_contrato=20.0,
                porcentaje_jornada=80,
                turno="tarde",
            ),
        ]
    )
    bd_portatil.commit()
    portatil.sync_on_shutdown(session=bd_portatil)

    # El sobremesa recibe los dos y da de baja a uno.
    sobremesa.sync_on_startup(session=bd_sobremesa)
    assert bd_sobremesa.query(Profesor).count() == 2
    bd_sobremesa.delete(bd_sobremesa.query(Profesor).filter_by(nombre_completo="López, Luis").one())
    bd_sobremesa.commit()
    sobremesa.sync_on_shutdown(session=bd_sobremesa)

    # El portátil vuelve a abrir: la baja está aplicada y no resucita.
    portatil.sync_on_startup(session=bd_portatil)
    assert [p.nombre_completo for p in bd_portatil.query(Profesor).all()] == ["García, Ana"]


def test_dos_equipos_no_mezclan_entidades_distintas(equipo):
    """SYNC-005: los identificadores locales ya no chocan, porque no se fusiona."""
    portatil, bd_portatil = equipo("portatil")
    sobremesa, bd_sobremesa = equipo("sobremesa")

    portatil.sync_on_startup(session=bd_portatil)
    bd_portatil.add(Zona(nombre_zona="Patio Principal"))
    bd_portatil.commit()
    portatil.sync_on_shutdown(session=bd_portatil)

    # El sobremesa tenía otra zona suya, creada sin conexión, con el mismo id 1.
    bd_sobremesa.add(Zona(nombre_zona="Cafetería"))
    bd_sobremesa.commit()
    assert bd_sobremesa.query(Zona).one().id == 1

    sobremesa.sync_on_startup(session=bd_sobremesa)

    # Manda la nube: queda su zona, no una mezcla de las dos.
    zonas = [z.nombre_zona for z in bd_sobremesa.query(Zona).all()]
    assert zonas == ["Patio Principal"]


def test_la_version_crece_en_cada_subida(equipo):
    portatil, bd = equipo("portatil")
    portatil.sync_on_startup(session=bd)
    bd.add(Zona(nombre_zona="Patio"))
    bd.commit()

    portatil.sync_on_shutdown(session=bd)
    assert portatil.version_descargada == 1
    # Sin cambios no se sube (ESC-003); hasta v5.97.0 este test pasaba porque la
    # huella se perdía al guardar la metadata (SYNC-022).
    bd.add(Zona(nombre_zona="Gimnasio"))
    bd.commit()
    portatil.sync_on_shutdown(session=bd)
    assert portatil.version_descargada == 2


# ---------------------------------------------------------------------------
# Las defensas
# ---------------------------------------------------------------------------
def test_sin_descargar_no_se_sube(equipo, nube):
    """El portátil sin cobertura no puede machacar el trabajo bueno."""
    portatil, bd = equipo("portatil")
    otro, bd_otro = equipo("otro")
    otro.sync_on_startup(session=bd_otro)
    bd_otro.add(Zona(nombre_zona="Zona buena"))
    bd_otro.commit()
    otro.sync_on_shutdown(session=bd_otro)

    with patch.object(LocalSyncBackend, "download_file", return_value=False):
        assert portatil.sync_on_startup(session=bd) is False
    assert portatil.puede_subir is False
    assert portatil.sync_on_shutdown(session=bd) is False

    # Lo que hay en la nube sigue intacto.
    comprobador, bd_comprobador = equipo("comprobador")
    comprobador.sync_on_startup(session=bd_comprobador)
    assert [z.nombre_zona for z in bd_comprobador.query(Zona).all()] == ["Zona buena"]


def test_no_se_sobrescribe_lo_que_subio_otro_equipo(equipo):
    portatil, bd_portatil = equipo("portatil")
    sobremesa, bd_sobremesa = equipo("sobremesa")

    portatil.sync_on_startup(session=bd_portatil)
    bd_portatil.add(Zona(nombre_zona="Inicial"))
    bd_portatil.commit()
    portatil.sync_on_shutdown(session=bd_portatil)

    # Los dos abren con la misma versión.
    sobremesa.sync_on_startup(session=bd_sobremesa)
    portatil.sync_on_startup(session=bd_portatil)

    # El sobremesa termina antes y sube.
    bd_sobremesa.add(Zona(nombre_zona="Del sobremesa"))
    bd_sobremesa.commit()
    assert sobremesa.sync_on_shutdown(session=bd_sobremesa) is True

    # El portátil ya no puede sobrescribirlo a ciegas.
    bd_portatil.add(Zona(nombre_zona="Del portatil"))
    bd_portatil.commit()
    assert portatil.sync_on_shutdown(session=bd_portatil) is False
    assert portatil._leer_metadata_local()["pendiente_subida"] is True


def test_un_fichero_corrupto_no_borra_los_datos_locales(equipo):
    portatil, bd = equipo("portatil")
    portatil.sync_on_startup(session=bd)
    bd.add(Zona(nombre_zona="Mis datos"))
    bd.commit()
    portatil.sync_on_shutdown(session=bd)

    def _descarga_corrupta(_remote, destino):
        destino.write_text("{ esto no es json", encoding="utf-8")
        return True

    with patch.object(LocalSyncBackend, "download_file", side_effect=_descarga_corrupta):
        assert portatil.sync_on_startup(session=bd) is False

    assert [z.nombre_zona for z in bd.query(Zona).all()] == ["Mis datos"]


def test_se_conservan_versiones_anteriores_en_el_servidor(equipo, nube):
    portatil, bd = equipo("portatil")
    portatil.sync_on_startup(session=bd)
    bd.add(Zona(nombre_zona="Primera"))
    bd.commit()
    portatil.sync_on_shutdown(session=bd)
    bd.add(Zona(nombre_zona="Segunda"))
    bd.commit()
    portatil.sync_on_shutdown(session=bd)

    anterior = portatil.get_remote_path("guardias_patio_data.json.1")
    assert nube.file_exists(anterior), "debe quedar una copia de la versión anterior"


def test_no_hay_caida_silenciosa_a_local():
    """SYNC-001: si el servidor no sirve, se avisa; nunca se guarda en local fingiendo nube."""
    from sync import backend_factory

    fuente = inspect.getsource(backend_factory.get_default_backend)
    assert 'create_sync_backend("local")' not in fuente
    assert "SyncConfigurationError" in fuente


def test_la_subida_es_atomica():
    """SYNC-007: un corte de conexión no puede dejar truncado el fichero bueno."""
    from sync.sync_manager import LocalSyncBackend as Local
    from sync.sync_manager import SFTPSyncBackend

    assert "posix_rename" in inspect.getsource(SFTPSyncBackend.upload_file)
    assert "os.replace" in inspect.getsource(Local.upload_file)


# ---------------------------------------------------------------------------
# Fase 2: la cuenta vive en el servidor
# ---------------------------------------------------------------------------
def test_el_fichero_sincronizado_no_lleva_credenciales(tmp_path):
    """SYNC-013: las contraseñas de correo y servidor ya no viajan a la nube."""
    sesion = _base_de_datos()
    exportado = tmp_path / "datos.json"
    assert DataExporter.export_to_json(sesion, exportado)

    datos = json.loads(exportado.read_text(encoding="utf-8"))
    presentes = [c for c in ("smtp_config", "sftp_config") if c in datos]
    assert not presentes, f"el fichero de datos incluye credenciales: {presentes}"


def test_la_misma_cuenta_sirve_desde_otro_equipo(tmp_path, nube):
    """SYNC-009: es lo que se pedía, mismo usuario y contraseña desde cualquier equipo."""
    from sync.sync_manager import UserAuth

    en_el_portatil = UserAuth(users_file=tmp_path / "portatil.json", backend=nube)
    assert en_el_portatil.register_user("jefatura", "Guardias2026!", "jefatura@epla.es")

    # Otro equipo, que nunca ha visto esa cuenta.
    en_el_sobremesa = UserAuth(users_file=tmp_path / "sobremesa.json", backend=nube)
    assert en_el_sobremesa.users == {}

    ok, mensaje = en_el_sobremesa.authenticate("jefatura", "Guardias2026!")
    assert ok is True, mensaje

    mal, _ = en_el_sobremesa.authenticate("jefatura", "otra-contraseña")
    assert mal is False


def test_nadie_puede_apropiarse_de_un_nombre_ya_registrado(tmp_path, nube):
    """Antes bastaba con registrar el nombre de otro para quedarse con sus datos."""
    from sync.sync_manager import UserAuth

    legitimo = UserAuth(users_file=tmp_path / "legitimo.json", backend=nube)
    assert legitimo.register_user("jefatura", "Guardias2026!")

    intruso = UserAuth(users_file=tmp_path / "intruso.json", backend=nube)
    assert intruso.register_user("jefatura", "LaMiaPropia1!") is False


def test_una_cuenta_antigua_se_publica_al_entrar(tmp_path, nube):
    """Las cuentas que ya existían en un equipo pasan al servidor en el primer acceso."""
    from sync.sync_manager import RemoteAccounts, UserAuth

    solo_local = UserAuth(users_file=tmp_path / "antiguo.json")
    assert solo_local.register_user("veterano", "Guardias2026!")
    assert RemoteAccounts(nube).fetch("veterano") is None

    con_servidor = UserAuth(users_file=tmp_path / "antiguo.json", backend=nube)
    ok, mensaje = con_servidor.authenticate("veterano", "Guardias2026!")
    assert ok is True, mensaje
    assert RemoteAccounts(nube).fetch("veterano") is not None

    otro_equipo = UserAuth(users_file=tmp_path / "otro.json", backend=nube)
    assert otro_equipo.authenticate("veterano", "Guardias2026!")[0] is True


def test_sin_conexion_se_entra_con_la_copia_local(tmp_path, nube):
    """Perder la red no debe dejar a nadie fuera de su propio equipo."""
    from sync.sync_manager import UserAuth

    equipo = UserAuth(users_file=tmp_path / "equipo.json", backend=nube)
    assert equipo.register_user("jefatura", "Guardias2026!")

    sin_red = UserAuth(users_file=tmp_path / "equipo.json", backend=None)
    ok, mensaje = sin_red.authenticate("jefatura", "Guardias2026!")
    assert ok is True, mensaje


# ---------------------------------------------------------------------------
# Cuentas antiguas y primera subida
# ---------------------------------------------------------------------------
def test_no_se_puede_registrar_un_nombre_con_datos_en_el_servidor(tmp_path, nube, equipo):
    """
    El agujero: el nombre de usuario es público. Antes bastaba con conocerlo y
    registrarlo con cualquier contraseña para bajarse los datos de esa persona.
    """
    from sync.sync_manager import UserAuth

    # Una cuenta antigua: tiene datos en el servidor pero su contraseña nunca se publicó.
    veterano, bd = equipo("veterano", usuario="jefatura")
    veterano.sync_on_startup(session=bd)
    bd.add(Zona(nombre_zona="Datos de la jefatura"))
    bd.commit()
    veterano.sync_on_shutdown(session=bd)

    intruso = UserAuth(users_file=tmp_path / "intruso.json", backend=nube)
    assert intruso.register_user("jefatura", "LaQueSeaMe1!") is False
    assert "ya tiene datos en el servidor" in intruso.ultimo_motivo_registro


def test_un_equipo_con_datos_los_sube_al_abrir(equipo, nube):
    """Si la nube está vacía y el equipo tiene datos, la carpeta se crea al abrir."""
    portatil, bd = equipo("portatil")
    bd.add(Zona(nombre_zona="Patio"))
    bd.add(
        Profesor(
            nombre_completo="García, Ana",
            horas_contrato=25.0,
            porcentaje_jornada=100,
            turno="mañana",
        )
    )
    bd.commit()

    assert nube.file_exists(portatil.get_remote_path("guardias_patio_data.json")) is False
    assert portatil.sync_on_startup(session=bd) is True
    assert nube.file_exists(portatil.get_remote_path("guardias_patio_data.json")) is True

    # Y otro equipo ya puede recibirlos sin esperar a que el primero cierre.
    sobremesa, bd_sobremesa = equipo("sobremesa")
    sobremesa.sync_on_startup(session=bd_sobremesa)
    assert [z.nombre_zona for z in bd_sobremesa.query(Zona).all()] == ["Patio"]


def test_un_equipo_vacio_no_sube_nada(equipo, nube):
    portatil, bd = equipo("portatil")
    assert portatil.sync_on_startup(session=bd) is True
    assert nube.file_exists(portatil.get_remote_path("guardias_patio_data.json")) is False
