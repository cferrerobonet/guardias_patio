"""
Tests para _exportador_import.py con sesión real SQLite in-memory.
"""

import sys
from datetime import date, time
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


# ===========================================================================
# Funciones helper internas
# ===========================================================================


class TestHelpers:
    def test_deserializar_fecha_none(self):
        from services._exportador_import import _deserializar_fecha

        assert _deserializar_fecha(None) is None

    def test_deserializar_fecha_ok(self):
        from services._exportador_import import _deserializar_fecha

        result = _deserializar_fecha("2024-09-01")
        assert result == date(2024, 9, 1)

    def test_deserializar_hora_none(self):
        from services._exportador_import import _deserializar_hora

        assert _deserializar_hora(None) is None

    def test_deserializar_hora_ok(self):
        from services._exportador_import import _deserializar_hora

        result = _deserializar_hora("10:30")
        assert result == time(10, 30)

    def test_desencriptar_vacio(self):
        from services._exportador_import import _desencriptar_password

        assert _desencriptar_password("") == ""

    def test_desencriptar_fallback(self):
        from services._exportador_import import _desencriptar_password

        # Token inválido → fallback a base64 o texto plano
        result = _desencriptar_password("texto_plano_no_encriptado")
        assert isinstance(result, str)

    def test_get_fernet_genera_clave(self):
        import os

        from services._exportador_import import _get_fernet

        with patch.dict(os.environ, {}, clear=False):
            # Sin la variable de entorno debe crear/leer la clave
            fernet = _get_fernet()
            assert fernet is not None


# ===========================================================================
# importar_zonas
# ===========================================================================


class TestImportarZonas:
    def test_lista_vacia(self, session):
        from services._exportador_import import importar_zonas

        count = importar_zonas(session, [])
        assert count == 0

    def test_importar_una_zona_nueva(self, session):
        from services._exportador_import import importar_zonas

        data = [{"nombre_zona": "Patio Central", "descripcion": "Zona principal"}]
        count = importar_zonas(session, data)
        assert count == 1

    def test_importar_zona_con_id(self, session):
        from services._exportador_import import importar_zonas

        data = [{"id": 100, "nombre_zona": "Patio Sur"}]
        count = importar_zonas(session, data)
        assert count == 1


# ===========================================================================
# importar_profesores
# ===========================================================================


class TestImportarProfesores:
    def test_lista_vacia(self, session):
        from services._exportador_import import importar_profesores

        count = importar_profesores(session, [])
        assert count == 0

    def test_importar_profesor_minimo(self, session):
        from services._exportador_import import importar_profesores

        data = [
            {
                "nombre": "Juan",
                "apellidos": "García López",
                "email_corporativo": "juan@test.com",
                "activo": True,
                "tutor": False,
                "horas_contrato": 18,
                "porcentaje_jornada": 100,
                "turno": "mañana",
            }
        ]
        count = importar_profesores(session, data)
        assert count == 1


# ===========================================================================
# importar_configuracion
# ===========================================================================


class TestImportarConfiguracion:
    def test_config_vacia(self, session):
        from services._exportador_import import importar_configuracion

        result = importar_configuracion(session, {})
        assert result is False

    def test_config_minima(self, session):
        from services._exportador_import import importar_configuracion

        data = {
            "id": 200,
            "anio_inicio_curso": 2024,
            "fecha_inicio_curso": "2024-09-01",
            "fecha_fin_curso": "2025-06-30",
            "hora_recreo1_manana": "10:30",
            "hora_recreo2_manana": "12:00",
        }
        result = importar_configuracion(session, data)
        assert result is True
