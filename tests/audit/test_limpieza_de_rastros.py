"""SEC-001 — borrar del equipo lo que dejaron las versiones anteriores.

Actualizar la aplicación no quita nada de lo que ya estaba en disco: el `.env`
con las contraseñas en claro, a veces legible por cualquier cuenta; las carpetas
del esquema de datos antiguo; y los volcados de sincronización con un bloque de
credenciales dentro, en base64 en las versiones más viejas.

La regla que no se salta: si las contraseñas no están todavía a salvo en el
llavero, no se toca nada. Y nunca se borra una carpeta que pueda tener datos.
"""

import json
import os
import stat

import pytest

from core import limpieza_de_rastros as limpieza

VOLCADO_CON_CREDENCIALES = {
    "export_date": "2025-11-03T10:00:00",
    "profesores": [{"id": 1, "nombre_completo": "García, Ana"}],
    "guardias": [{"id": 1}],
    "sftp_config": {"sftp_host": "h", "sftp_password": "c2VjcmV0YQ=="},
    "smtp_config": {"smtp_server": "s", "smtp_password": "b3RyYQ=="},
}


@pytest.fixture
def con_llavero(monkeypatch):
    """El llavero ya tiene las contraseñas: la limpieza puede actuar."""
    monkeypatch.setattr(limpieza, "_es_seguro_limpiar", lambda: (True, None))


@pytest.fixture
def sin_llavero(monkeypatch):
    monkeypatch.setattr(
        limpieza, "_es_seguro_limpiar", lambda: (False, "todavía no hay ninguna contraseña")
    )


def _montar(base, con_datos=False):
    (base / "data" / "users" / ("a" * 16)).mkdir(parents=True)
    heredada = base / "data" / ("b" * 16)
    heredada.mkdir(parents=True)
    (heredada / "guardias_patio.db").write_bytes(b"x" * 100 if con_datos else b"")
    (heredada / "guardias_patio_data.json").write_text(
        json.dumps(VOLCADO_CON_CREDENCIALES), encoding="utf-8"
    )
    return heredada


# ---------------------------------------------------------------------------
# La condición de seguridad
# ---------------------------------------------------------------------------


def test_sin_contrasenas_en_el_llavero_no_se_toca_nada(sin_llavero, tmp_path):
    heredada = _montar(tmp_path)

    informe = limpieza.revisar_y_limpiar(tmp_path)

    assert informe.motivo_de_no_actuar
    assert informe.hecho == []
    assert heredada.exists()


def test_solo_mirar_no_cambia_nada(con_llavero, tmp_path):
    heredada = _montar(tmp_path)

    informe = limpieza.revisar_y_limpiar(tmp_path, solo_mirar=True)

    assert heredada.exists()
    assert informe.pendiente
    assert json.loads((heredada / "guardias_patio_data.json").read_text())["sftp_config"]


# ---------------------------------------------------------------------------
# Nunca se borran datos
# ---------------------------------------------------------------------------


def test_una_carpeta_heredada_con_datos_se_conserva(con_llavero, tmp_path):
    heredada = _montar(tmp_path, con_datos=True)

    informe = limpieza.revisar_y_limpiar(tmp_path)

    assert heredada.exists(), "se ha borrado una carpeta con base de datos"
    assert any("revísala a mano" in aviso for aviso in informe.pendiente)


def test_una_carpeta_heredada_con_datos_igualmente_pierde_las_credenciales(
    con_llavero, tmp_path
):
    """Se conserva la carpeta, pero el volcado no puede seguir con la contraseña."""
    heredada = _montar(tmp_path, con_datos=True)

    limpieza.revisar_y_limpiar(tmp_path)

    contenido = json.loads((heredada / "guardias_patio_data.json").read_text())
    assert "sftp_config" not in contenido
    assert "smtp_config" not in contenido


def test_la_carpeta_heredada_vacia_se_elimina(con_llavero, tmp_path):
    heredada = _montar(tmp_path)

    informe = limpieza.revisar_y_limpiar(tmp_path)

    assert not heredada.exists()
    assert any("heredada" in hecho for hecho in informe.hecho)


def test_la_carpeta_de_datos_viva_no_se_toca(con_llavero, tmp_path):
    _montar(tmp_path)
    viva = tmp_path / "data" / "users" / ("a" * 16)

    limpieza.revisar_y_limpiar(tmp_path)

    assert viva.exists()


# ---------------------------------------------------------------------------
# Los volcados
# ---------------------------------------------------------------------------


def test_el_volcado_pierde_las_credenciales_y_conserva_los_datos(con_llavero, tmp_path):
    viva = tmp_path / "data" / "users" / ("a" * 16)
    viva.mkdir(parents=True)
    volcado = viva / "guardias_patio_data.json"
    volcado.write_text(json.dumps(VOLCADO_CON_CREDENCIALES), encoding="utf-8")

    limpieza.revisar_y_limpiar(tmp_path)

    contenido = json.loads(volcado.read_text(encoding="utf-8"))
    assert "sftp_config" not in contenido and "smtp_config" not in contenido
    assert len(contenido["profesores"]) == 1
    assert len(contenido["guardias"]) == 1
    assert contenido["export_date"] == "2025-11-03T10:00:00"


def test_un_volcado_ya_limpio_no_se_reescribe(con_llavero, tmp_path):
    viva = tmp_path / "data" / "users" / ("a" * 16)
    viva.mkdir(parents=True)
    volcado = viva / "guardias_patio_data.json"
    volcado.write_text(json.dumps({"profesores": []}), encoding="utf-8")

    informe = limpieza.revisar_y_limpiar(tmp_path)

    assert not any("credenciales quitadas" in hecho for hecho in informe.hecho)


def test_un_volcado_ilegible_no_rompe_la_limpieza(con_llavero, tmp_path):
    viva = tmp_path / "data" / "users" / ("a" * 16)
    viva.mkdir(parents=True)
    (viva / "guardias_patio_data.json").write_text("{ roto", encoding="utf-8")

    informe = limpieza.revisar_y_limpiar(tmp_path)

    assert informe.motivo_de_no_actuar is None


# ---------------------------------------------------------------------------
# Permisos
# ---------------------------------------------------------------------------


@pytest.mark.skipif(os.name == "nt", reason="los permisos POSIX no aplican en Windows")
def test_un_env_legible_por_otros_se_cierra(con_llavero, tmp_path):
    env = tmp_path / ".env"
    env.write_text("SFTP_HOST=x\n", encoding="utf-8")
    env.chmod(0o644)

    limpieza.revisar_y_limpiar(tmp_path)

    assert stat.S_IMODE(env.stat().st_mode) & 0o077 == 0


@pytest.mark.skipif(os.name == "nt", reason="los permisos POSIX no aplican en Windows")
def test_un_env_ya_cerrado_no_se_anuncia(con_llavero, tmp_path):
    env = tmp_path / ".env"
    env.write_text("SFTP_HOST=x\n", encoding="utf-8")
    env.chmod(0o600)

    informe = limpieza.revisar_y_limpiar(tmp_path)

    assert not any("permisos" in hecho for hecho in informe.hecho)


def test_en_windows_no_se_miran_los_permisos_posix(monkeypatch, tmp_path):
    """Allí los bits no significan nada: mirarlos daría un aviso falso siempre."""
    monkeypatch.setattr(limpieza.os, "name", "nt")
    env = tmp_path / ".env"
    env.write_text("SFTP_HOST=x\n", encoding="utf-8")

    assert limpieza._permisos_abiertos(env) is False


# ---------------------------------------------------------------------------
# Enganche
# ---------------------------------------------------------------------------


def test_la_limpieza_corre_al_arrancar():
    import inspect

    import main

    assert "revisar_y_limpiar" in inspect.getsource(main)


def test_sobre_una_carpeta_que_no_existe_no_falla(con_llavero, tmp_path):
    informe = limpieza.revisar_y_limpiar(tmp_path / "no_existe")

    assert informe.hecho == []
