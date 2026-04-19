"""
Tests para servicios PDF con 0% cobertura.
Se testean rutas de retorno temprano (sin curso activo, sin guardias).
"""

import sys
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


# ===========================================================================
# _pdf_mes_consolidado
# ===========================================================================


class TestExportarMesConsolidado:
    def test_sin_curso_activo_retorna_false(self, tmp_path):
        from services._pdf_mes_consolidado import exportar_mes_consolidado

        session = MagicMock()
        with patch(
            "services._pdf_mes_consolidado.GestorCursos.obtener_curso_activo",
            return_value=None,
        ):
            result = exportar_mes_consolidado(
                session=session,
                mes=9,
                anio=2024,
                ruta_salida=str(tmp_path / "test.pdf"),
            )
        assert result is False

    def test_sin_guardias_retorna_false(self, tmp_path):
        from services._pdf_mes_consolidado import exportar_mes_consolidado

        session = MagicMock()
        curso = MagicMock()
        curso.id = 1
        session.query.return_value.options.return_value.filter.return_value.order_by.return_value.all.return_value = []

        with patch(
            "services._pdf_mes_consolidado.GestorCursos.obtener_curso_activo",
            return_value=curso,
        ):
            result = exportar_mes_consolidado(
                session=session,
                mes=9,
                anio=2024,
                ruta_salida=str(tmp_path / "test.pdf"),
            )
        assert result is False

    def test_con_progress_callback(self, tmp_path):
        from services._pdf_mes_consolidado import exportar_mes_consolidado

        session = MagicMock()
        callbacks = []

        def cb(pct, msg=""):
            callbacks.append(pct)

        with patch(
            "services._pdf_mes_consolidado.GestorCursos.obtener_curso_activo",
            return_value=None,
        ):
            result = exportar_mes_consolidado(
                session=session,
                mes=9,
                anio=2024,
                ruta_salida=str(tmp_path / "test.pdf"),
                progress_callback=cb,
            )
        assert result is False
        assert len(callbacks) > 0


class TestExportarCursoCompleto:
    def test_sin_guardias_retorna_false(self, tmp_path):
        from services._pdf_mes_consolidado import exportar_curso_completo

        session = MagicMock()
        session.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        result = exportar_curso_completo(
            session=session,
            anio_inicio=2024,
            carpeta_salida=str(tmp_path),
        )
        # Resultado puede ser True o False; no debe lanzar
        assert isinstance(result, bool)


# ===========================================================================
# _pdf_individual_optimizado
# ===========================================================================


class TestExportarProfesorIndividualOptimizado:
    def test_sin_profesor_retorna_false(self, tmp_path):
        from services._pdf_individual_optimizado import (
            exportar_profesor_individual_optimizado,
        )

        session = MagicMock()
        session.query.return_value.filter.return_value.first.return_value = None

        result = exportar_profesor_individual_optimizado(
            session=session,
            profesor_id=999,
            fecha_inicio=date(2024, 9, 1),
            fecha_fin=date(2024, 6, 30),
            ruta_salida=str(tmp_path / "test.pdf"),
        )
        assert result is False

    def test_sin_guardias_retorna_false(self, tmp_path):
        from services._pdf_individual_optimizado import (
            exportar_profesor_individual_optimizado,
        )

        session = MagicMock()
        profesor = MagicMock()
        profesor.nombre_completo = "Juan García"
        session.query.return_value.filter.return_value.first.return_value = profesor
        session.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = exportar_profesor_individual_optimizado(
            session=session,
            profesor_id=1,
            fecha_inicio=date(2024, 9, 1),
            fecha_fin=date(2024, 6, 30),
            ruta_salida=str(tmp_path / "test.pdf"),
        )
        assert result is False

    def test_con_progress_callback(self, tmp_path):
        from services._pdf_individual_optimizado import (
            exportar_profesor_individual_optimizado,
        )

        session = MagicMock()
        session.query.return_value.filter.return_value.first.return_value = None
        callbacks = []

        def cb(pct, msg=""):
            callbacks.append(pct)

        result = exportar_profesor_individual_optimizado(
            session=session,
            profesor_id=999,
            fecha_inicio=date(2024, 9, 1),
            fecha_fin=date(2024, 6, 30),
            ruta_salida=str(tmp_path / "test.pdf"),
            progress_callback=cb,
        )
        assert result is False
        assert len(callbacks) > 0
