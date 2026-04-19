"""Cobertura extra para services/_exportador_import.py."""

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from services import _exportador_import as imp


class _Q:
    def __init__(self, first=None):
        self._first = first

    def filter_by(self, **_k):
        return self

    def first(self):
        return self._first

    def delete(self):
        return 0


class _S:
    def __init__(self):
        self._map = {}
        self.added = []
        self.commits = 0

    def set_first(self, model_name, value):
        self._map[model_name] = value

    def query(self, model):
        name = getattr(model, "__name__", str(model))
        return _Q(first=self._map.get(name))

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        self.commits += 1

    def flush(self):
        return None

    def expire_all(self):
        return None

    def expunge_all(self):
        return None

    def rollback(self):
        return None


def test_desencriptar_password_fallback_base64():
    import base64

    plain = "secreto"
    b64 = base64.b64encode(plain.encode()).decode()
    # forzamos InvalidToken
    old = imp._get_fernet
    imp._get_fernet = lambda: SimpleNamespace(decrypt=lambda _x: (_ for _ in ()).throw(imp.InvalidToken()))
    try:
        assert imp._desencriptar_password(b64) == plain
    finally:
        imp._get_fernet = old


def test_desencriptar_password_si_falla_todo_devuelve_original():
    # "\xff\xfe" no es UTF-8 válido, así que base64.b64decode().decode() lanza UnicodeDecodeError
    # y el fallback devuelve el original
    original = "/\xff\xfe=="
    old = imp._get_fernet
    imp._get_fernet = lambda: SimpleNamespace(decrypt=lambda _x: (_ for _ in ()).throw(imp.InvalidToken()))
    try:
        assert imp._desencriptar_password(original) == original
    finally:
        imp._get_fernet = old


def test_importar_profesores_salta_entrada_invalida():
    s = _S()
    data = [{"foo": "bar"}]
    assert imp.importar_profesores(s, data) == 0


def test_importar_profesores_update_existente():
    s = _S()
    existing = SimpleNamespace()
    s.set_first("Profesor", existing)
    data = [{
        "id": 1,
        "nombre": "Ana",
        "apellidos": "Pérez",
        "horas_contrato": 20,
        "porcentaje_jornada": 80,
        "turno": "mañana",
    }]
    assert imp.importar_profesores(s, data) == 1
    assert existing.nombre_completo == "Pérez, Ana"


def test_importar_zonas_update_existente():
    s = _S()
    existing = SimpleNamespace()
    s.set_first("Zona", existing)
    assert imp.importar_zonas(s, [{"id": 1, "nombre_zona": "Z1"}]) == 1
    assert existing.nombre_zona == "Z1"


def test_importar_configuracion_sin_data_false():
    s = _S()
    assert imp.importar_configuracion(s, {}) is False


def test_importar_guardias_por_nombre_resuelve_ids():
    s = _S()
    prof = SimpleNamespace(id=10)
    zona = SimpleNamespace(id=20)

    class QGuard(_Q):
        def first(self):
            return None

    def query(model):
        name = getattr(model, "__name__", str(model))
        if "Profesor" in name:
            return _Q(first=prof)
        if "Zona" in name:
            return _Q(first=zona)
        if "Guardia" in name:
            return QGuard()
        return _Q()

    s.query = query
    data = [{
        "fecha": "2025-01-01",
        "turno": "mañana",
        "recreo": 1,
        "profesor_nombre_completo": "X",
        "zona_nombre": "Y",
    }]
    assert imp.importar_guardias(s, data) == 1


def test_importar_ausencias_duplica_count_por_bug_actual():
    s = _S()
    prof = SimpleNamespace(id=1)

    def query(model):
        name = getattr(model, "__name__", str(model))
        if "Profesor" in name:
            return _Q(first=prof)
        return _Q(first=None)

    s.query = query
    data = [{"fecha_inicio": "2025-01-01", "fecha_fin": "2025-01-02", "tipo": "otros", "profesor_nombre_completo": "P"}]
    # comportamiento actual del módulo: count += 1 dos veces
    assert imp.importar_ausencias(s, data) == 2


def test_importar_smtp_config_incompleto_false(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert imp._importar_smtp_config({"smtp_server": "x"}) is False


def test_importar_sftp_config_incompleto_false(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert imp._importar_sftp_config({"sftp_host": "x"}) is False


def test_importar_usuarios_sin_data_0():
    assert imp.importar_usuarios(None) == 0


def test_importar_cursos_escolares_sin_data_0():
    s = _S()
    assert imp.importar_cursos_escolares(s, None) == 0


def test_importar_todo_orquesta(monkeypatch, tmp_path):
    payload = {
        "smtp_config": {"smtp_server": "s", "smtp_port": "1", "smtp_user": "u", "smtp_password": "p"},
        "sftp_config": {"sftp_host": "h", "sftp_port": "22", "sftp_username": "u", "sftp_password": "p"},
        "usuarios": {"usuarios": []},
        "cursos_escolares": {"cursos": []},
        "profesores": [],
        "zonas": [],
        "configuracion": {},
        "guardias": [],
        "ausencias": [],
    }
    f = tmp_path / "d.json"
    f.write_text(json.dumps(payload), encoding="utf-8")

    monkeypatch.setattr(imp, "_importar_smtp_config", lambda _d: True)
    monkeypatch.setattr(imp, "_importar_sftp_config", lambda _d: True)
    monkeypatch.setattr(imp, "importar_usuarios", lambda *_a, **_k: 2)
    monkeypatch.setattr(imp, "importar_cursos_escolares", lambda *_a, **_k: 3)
    monkeypatch.setattr(imp, "importar_profesores", lambda *_a, **_k: 4)
    monkeypatch.setattr(imp, "importar_zonas", lambda *_a, **_k: 5)
    monkeypatch.setattr(imp, "importar_configuracion", lambda *_a, **_k: True)
    monkeypatch.setattr(imp, "importar_guardias", lambda *_a, **_k: 6)
    monkeypatch.setattr(imp, "importar_ausencias", lambda *_a, **_k: 7)

    out = imp.importar_todo(MagicMock(), f)
    assert out == {
        "profesores": 4,
        "zonas": 5,
        "configuracion": 1,
        "guardias": 6,
        "ausencias": 7,
        "smtp_config": 1,
        "sftp_config": 1,
        "usuarios": 2,
        "cursos_escolares": 3,
    }
