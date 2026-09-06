"""Lote 18 — privacidad (PRIV-001, PRIV-002).

- Los datos de salud de las ausencias (tipo y motivo) viajan cifrados al servidor
  con una clave derivada de la contraseña de la cuenta; la ruta del justificante
  no viaja.
- Los registros no llevan correos ni nombres completos.
"""

import re
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.privacidad import enmascarar_correo, enmascarar_nombre
from infrastructure.database.models import Ausencia, Base, Profesor
from sync import cifrado
from sync.backends import LocalSyncBackend
from sync.data_exporter import DataExporter
from sync.sync_manager import SyncManager

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
CLAVE = cifrado.derivar_clave("jefatura", "Secreta-2026!", iteraciones=1_000)
OTRA = cifrado.derivar_clave("jefatura", "Otra-2026!", iteraciones=1_000)


def _bd():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()


def _con_una_baja(bd):
    bd.add(
        Profesor(
            id=1, nombre_completo="García, Ana", horas_contrato=25.0, porcentaje_jornada=100,
            turno="mañana",
        )
    )
    bd.add(
        Ausencia(
            id=1, profesor_id=1, fecha_inicio=date(2026, 9, 1), fecha_fin=date(2026, 9, 5),
            tipo="baja_medica", motivo="Intervención quirúrgica", documento_path="/tmp/parte.pdf",
        )
    )
    bd.commit()
    return bd


# ---------------------------------------------------------------------------
# PRIV-001 · cifrado
# ---------------------------------------------------------------------------
def test_la_clave_es_la_misma_en_cualquier_equipo_y_distinta_por_cuenta():
    assert cifrado.derivar_clave("jefatura", "Secreta-2026!", 1_000) == CLAVE
    assert cifrado.derivar_clave("otra", "Secreta-2026!", 1_000) != CLAVE
    assert OTRA != CLAVE


def test_cifrar_y_descifrar_devuelve_el_texto():
    token = cifrado.cifrar("baja_medica", CLAVE)
    assert cifrado.esta_cifrado(token) and "baja_medica" not in token
    assert cifrado.descifrar(token, CLAVE) == "baja_medica"
    assert cifrado.cifrar(None, CLAVE) is None


def test_el_volcado_no_lleva_datos_de_salud_en_claro(tmp_path):
    ruta = tmp_path / "volcado.json"
    assert DataExporter.export_to_json(_con_una_baja(_bd()), ruta, clave=CLAVE)
    texto = ruta.read_text(encoding="utf-8")
    assert "baja_medica" not in texto
    assert "quirúrgica" not in texto
    assert "documento_path" not in texto and "parte.pdf" not in texto


def test_el_volcado_cifrado_se_restaura_en_otro_equipo(tmp_path):
    ruta = tmp_path / "volcado.json"
    DataExporter.export_to_json(_con_una_baja(_bd()), ruta, clave=CLAVE)
    otro = _bd()
    assert DataExporter.import_from_json(otro, ruta, clear_existing=True, clave=CLAVE)
    ausencia = otro.query(Ausencia).one()
    assert (ausencia.tipo, ausencia.motivo) == ("baja_medica", "Intervención quirúrgica")


def test_sin_la_clave_no_se_puede_leer_y_se_dice(tmp_path):
    ruta = tmp_path / "volcado.json"
    DataExporter.export_to_json(_con_una_baja(_bd()), ruta, clave=CLAVE)
    with pytest.raises(ValueError, match="cifrados"):
        DataExporter.import_from_json(_bd(), ruta, clear_existing=True, clave=None)
    with pytest.raises(ValueError, match="contraseña"):
        DataExporter.import_from_json(_bd(), ruta, clear_existing=True, clave=OTRA)


def test_los_volcados_antiguos_en_claro_se_siguen_leyendo(tmp_path):
    ruta = tmp_path / "volcado.json"
    DataExporter.export_to_json(_con_una_baja(_bd()), ruta)  # sin clave: como antes
    assert "baja_medica" in ruta.read_text(encoding="utf-8")
    otro = _bd()
    assert DataExporter.import_from_json(otro, ruta, clear_existing=True, clave=CLAVE)
    assert otro.query(Ausencia).one().tipo == "baja_medica"


def test_la_sincronizacion_cifra_de_extremo_a_extremo(tmp_path):
    nube = LocalSyncBackend(tmp_path / "nube")

    def equipo(nombre):
        carpeta = tmp_path / nombre
        carpeta.mkdir()
        with patch("sync.sync_manager.get_user_data_directory", return_value=carpeta):
            return SyncManager(nube, "jefatura", clave_datos=CLAVE)

    portatil, bd = equipo("portatil"), _con_una_baja(_bd())
    assert portatil.sync_on_startup(session=bd) is True
    assert portatil.sync_on_shutdown(session=bd) is True
    remoto = tmp_path / "bajado.json"
    nube.download_file(portatil.get_remote_path("guardias_patio_data.json"), remoto)
    assert "baja_medica" not in remoto.read_text(encoding="utf-8")

    sobremesa, bd2 = equipo("sobremesa"), _bd()
    assert sobremesa.sync_on_startup(session=bd2) is True
    assert bd2.query(Ausencia).one().tipo == "baja_medica"


def test_con_otra_contrasena_la_descarga_se_bloquea_sin_tocar_lo_local(tmp_path):
    nube = LocalSyncBackend(tmp_path / "nube")
    carpeta = tmp_path / "a"
    carpeta.mkdir()
    with patch("sync.sync_manager.get_user_data_directory", return_value=carpeta):
        uno = SyncManager(nube, "jefatura", clave_datos=CLAVE)
    bd = _con_una_baja(_bd())
    uno.sync_on_startup(session=bd)
    uno.sync_on_shutdown(session=bd)

    carpeta2 = tmp_path / "b"
    carpeta2.mkdir()
    with patch("sync.sync_manager.get_user_data_directory", return_value=carpeta2):
        dos = SyncManager(nube, "jefatura", clave_datos=OTRA)
    bd2 = _bd()
    assert dos.sync_on_startup(session=bd2) is False
    assert dos.puede_subir is False
    assert "contraseña" in (dos.motivo_bloqueo or "")


def test_el_login_deriva_la_clave_y_no_guarda_la_contrasena():
    fuente = (SRC / "presentation/forms/login_dialog.py").read_text(encoding="utf-8")
    assert "self.clave_datos = derivar_clave(username, password)" in fuente
    assert not re.search(r"self\.\w*password\w* = password\b", fuente)
    assert "clave_datos=login_dialog.clave_datos" in (SRC / "main.py").read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# PRIV-002 · registros sin datos personales
# ---------------------------------------------------------------------------
def test_enmascarar_correo():
    assert enmascarar_correo("ana.garcia@epla.es") == "a***@epla.es"
    assert enmascarar_correo("") == "(sin correo)"
    assert enmascarar_correo("sinarroba") == "s***"


def test_enmascarar_nombre():
    assert enmascarar_nombre("García López, Ana") == "G. L., A."
    assert enmascarar_nombre("Ana García") == "A. G."
    assert enmascarar_nombre(None) == "(sin nombre)"


def test_ningun_registro_escribe_correos_ni_nombres_en_claro():
    """CHK-I-03: cada `logger.*(...)` que mencione un correo o un nombre lo enmascara."""
    # Un nombre de zona o un mensaje de error no son datos personales: lo que se
    # vigila es el correo, el nombre de una persona y el destinatario de un envío.
    patron = re.compile(
        r"logger\.\w+\(.*(\{[^}]*(email|nombre_completo|destinatario)[^}]*\}"
        r"|\b(email|nombre_completo|destinatario)=(?!\"))"
    )
    culpables = []
    for fichero in SRC.rglob("*.py"):
        for n, linea in enumerate(fichero.read_text(encoding="utf-8").splitlines(), 1):
            if patron.search(linea) and "enmascarar_" not in linea:
                culpables.append(f"{fichero.relative_to(SRC)}:{n}: {linea.strip()}")
    assert culpables == [], "\n".join(culpables)
