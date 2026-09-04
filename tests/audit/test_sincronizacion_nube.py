"""Regresión de los hallazgos SYNC (subida y descarga en la nube).

Los tests marcados xfail(strict=True) describen el comportamiento que hace falta para que
un mismo usuario maneje los mismos datos desde cualquier equipo. Ver auditoria/12.
"""

import inspect
import json
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from infrastructure.database.models import Base, Profesor, Zona
from sync.data_exporter import DataExporter

ROOT = Path(__file__).resolve().parents[2]


def _sesion_nueva():
    """Simula un equipo distinto: su propia base de datos, con sus propios identificadores."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()


# ---------------------------------------------------------------------------
# SYNC-001: no caer a modo local en silencio
# ---------------------------------------------------------------------------
@pytest.mark.xfail(
    strict=True,
    reason="SYNC-001: get_default_backend() devuelve un backend local cuando el servidor "
    "no está configurado o falla, sin que nada se lo comunique al usuario",
)
def test_no_hay_caida_silenciosa_a_local():
    from sync import backend_factory

    fuente = inspect.getsource(backend_factory.get_default_backend)
    assert "create_sync_backend(\"local\")" not in fuente, (
        "el reserva a local debe ser una decisión explícita del usuario, no un efecto colateral"
    )


def test_la_caida_a_local_al_menos_queda_registrada():
    """Comportamiento actual que debe conservarse hasta que se corrija SYNC-001."""
    from sync import backend_factory

    fuente = inspect.getsource(backend_factory.get_default_backend)
    assert "NO se sincronizará con la nube" in fuente


# ---------------------------------------------------------------------------
# SYNC-005: identificadores locales que colisionan entre equipos
# ---------------------------------------------------------------------------
@pytest.mark.xfail(
    strict=True,
    reason="SYNC-005: la fusión empareja por id autoincremental, así que dos zonas distintas "
    "creadas en equipos distintos se consideran la misma",
)
def test_zonas_de_dos_equipos_no_se_mezclan(tmp_path):
    equipo_a = _sesion_nueva()
    equipo_a.add(Zona(nombre_zona="Patio Principal"))
    equipo_a.commit()

    equipo_b = _sesion_nueva()
    equipo_b.add(Zona(nombre_zona="Cafetería"))
    equipo_b.commit()

    # Ambas zonas recibieron el id 1 en su propia base de datos.
    assert equipo_a.query(Zona).one().id == equipo_b.query(Zona).one().id == 1

    exportado = tmp_path / "datos.json"
    assert DataExporter.export_to_json(equipo_a, exportado)
    assert DataExporter.import_from_json(equipo_b, exportado, clear_existing=False)

    nombres = sorted(z.nombre_zona for z in equipo_b.query(Zona).all())
    assert nombres == ["Cafetería", "Patio Principal"], (
        f"se esperaban las dos zonas y quedaron: {nombres}"
    )


# ---------------------------------------------------------------------------
# SYNC-006: las bajas deben propagarse
# ---------------------------------------------------------------------------
@pytest.mark.xfail(
    strict=True,
    reason="SYNC-006: la importación solo crea y actualiza, así que un registro eliminado "
    "en otro equipo reaparece en la siguiente sincronización",
)
def test_un_profesor_eliminado_no_reaparece(tmp_path):
    equipo_a = _sesion_nueva()
    equipo_a.add_all(
        [
            Profesor(nombre_completo="García, Ana", horas_contrato=25.0, turno="mañana"),
            Profesor(nombre_completo="López, Luis", horas_contrato=20.0, turno="tarde"),
        ]
    )
    equipo_a.commit()

    exportado = tmp_path / "datos.json"
    assert DataExporter.export_to_json(equipo_a, exportado)

    # El equipo A da de baja a uno y vuelve a sincronizar más tarde.
    equipo_a.delete(equipo_a.query(Profesor).filter_by(nombre_completo="López, Luis").one())
    equipo_a.commit()

    # El equipo B ya tenía el fichero anterior y lo importa.
    assert DataExporter.import_from_json(equipo_a, exportado, clear_existing=False)

    nombres = sorted(p.nombre_completo for p in equipo_a.query(Profesor).all())
    assert nombres == ["García, Ana"], f"el profesor dado de baja ha vuelto: {nombres}"


# ---------------------------------------------------------------------------
# SYNC-007: la subida debe ser atómica
# ---------------------------------------------------------------------------
@pytest.mark.xfail(
    strict=True,
    reason="SYNC-007: sftp.put escribe directamente sobre la ruta final; un corte deja "
    "truncado el único fichero del servidor",
)
def test_la_subida_es_atomica():
    from sync.sync_manager import SFTPSyncBackend

    fuente = inspect.getsource(SFTPSyncBackend.upload_file)
    assert "rename" in fuente or "posix_rename" in fuente, (
        "subir a un nombre temporal y renombrar al final, que en SFTP es atómico"
    )


# ---------------------------------------------------------------------------
# SYNC-013: las credenciales no deben viajar en el fichero de datos
# ---------------------------------------------------------------------------
@pytest.mark.xfail(
    strict=True,
    reason="SYNC-013: el JSON incluye la configuración de correo y de servidor, cifrada "
    "con una clave propia de cada equipo, así que ni sirve fuera ni debería estar ahí",
)
def test_el_fichero_sincronizado_no_lleva_credenciales(tmp_path):
    sesion = _sesion_nueva()
    exportado = tmp_path / "datos.json"
    assert DataExporter.export_to_json(sesion, exportado)

    datos = json.loads(exportado.read_text(encoding="utf-8"))
    presentes = [c for c in ("smtp_config", "sftp_config") if c in datos]
    assert not presentes, f"el fichero de datos incluye credenciales: {presentes}"


# ---------------------------------------------------------------------------
# SYNC-009: la cuenta debe poder usarse desde otro equipo
# ---------------------------------------------------------------------------
def test_las_cuentas_no_salen_del_equipo():
    """Deja constancia de por qué hoy no se puede entrar con la misma cuenta desde otro equipo."""
    from sync.sync_manager import UserAuth

    fuente = inspect.getsource(UserAuth)
    assert "users.json" in fuente
    exportador = (ROOT / "src" / "sync" / "data_exporter.py").read_text(encoding="utf-8")
    if "usuarios" not in exportador:
        pytest.xfail(
            "SYNC-009: users.json vive en cada equipo y no se sincroniza, así que la cuenta "
            "no existe en los demás; y la carpeta remota depende solo del nombre de usuario"
        )
