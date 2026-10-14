"""
Tests para repositorios SQLAlchemy con cobertura baja:
- sqlalchemy_ausencia_repository.py (44%)
- sqlalchemy_configuracion_repository.py (47%)
- sqlalchemy_curso_escolar_repository.py (50%)
- sqlalchemy_zona_repository.py (62%)
"""

import sys
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


# ===========================================================================
# SQLAlchemyAusenciaRepository
# ===========================================================================


class TestSQLAlchemyAusenciaRepository:
    def setup_method(self):
        self.session = MagicMock()
        from infrastructure.repositories.sqlalchemy_ausencia_repository import (
            SQLAlchemyAusenciaRepository,
        )

        self.repo = SQLAlchemyAusenciaRepository(self.session)

    def test_constructor(self):
        assert self.repo is not None
        assert self.repo.session is self.session

    def test_get_by_id_none(self):
        self.session.query.return_value.get.return_value = None
        result = self.repo.get_by_id(999)
        assert result is None

    def test_get_all_vacio(self):
        self.session.query.return_value.all.return_value = []
        result = self.repo.get_all()
        assert result == []

    def test_delete_no_encontrado(self):
        self.session.query.return_value.get.return_value = None
        result = self.repo.delete(999)
        assert result is False

    def test_exists_no_encontrado(self):
        self.session.query.return_value.filter_by.return_value.first.return_value = None
        result = self.repo.exists(999)
        assert result is False

    def test_count_cero(self):
        self.session.query.return_value.count.return_value = 0
        result = self.repo.count()
        assert result == 0

    def test_find_by_profesor_and_date_none(self):
        self.session.query.return_value.filter.return_value.first.return_value = None
        result = self.repo.find_by_profesor_and_date(1, date(2024, 1, 15))
        assert result is None

    def test_find_active_in_date_vacio(self):
        self.session.query.return_value.filter.return_value.all.return_value = []
        result = self.repo.find_active_in_date(date(2024, 1, 15))
        assert result == []

    def test_find_active_in_rango_vacio(self):
        self.session.query.return_value.filter.return_value.all.return_value = []
        result = self.repo.find_active_in_rango(date(2024, 1, 1), date(2024, 1, 31))
        assert result == []

    def test_count_by_profesor_cero(self):
        self.session.query.return_value.filter.return_value.count.return_value = 0
        result = self.repo.count_by_profesor(1)
        assert result == 0

    def test_find_by_profesor_and_period_vacio(self):
        self.session.query.return_value.filter.return_value.all.return_value = []
        result = self.repo.find_by_profesor_and_period(1, date(2024, 1, 1), date(2024, 1, 31))
        assert result == []


# ===========================================================================
# SQLAlchemyConfiguracionRepository
# ===========================================================================


class TestSQLAlchemyConfiguracionRepository:
    def setup_method(self):
        self.session = MagicMock()
        from infrastructure.repositories.sqlalchemy_configuracion_repository import (
            SQLAlchemyConfiguracionRepository,
        )

        self.repo = SQLAlchemyConfiguracionRepository(self.session)

    def test_constructor(self):
        assert self.repo is not None

    def test_get_by_id_none(self):
        self.session.query.return_value.get.return_value = None
        result = self.repo.get_by_id(999)
        assert result is None

    def test_get_all_vacio(self):
        self.session.query.return_value.all.return_value = []
        result = self.repo.get_all()
        assert result == []

    def test_delete_no_encontrado(self):
        self.session.query.return_value.get.return_value = None
        result = self.repo.delete(999)
        assert result is False

    def test_exists_no_encontrado(self):
        self.session.query.return_value.filter_by.return_value.first.return_value = None
        result = self.repo.exists(999)
        assert result is False

    def test_count_cero(self):
        self.session.query.return_value.count.return_value = 0
        result = self.repo.count()
        assert result == 0

    def test_get_active_none(self):
        self.session.query.return_value.first.return_value = None
        result = self.repo.get_active()
        assert result is None

    def test_get_first_none(self):
        self.session.query.return_value.first.return_value = None
        result = self.repo.get_first()
        assert result is None

    def test_find_by_curso_activo_id_none(self):
        self.session.query.return_value.filter_by.return_value.first.return_value = None
        result = self.repo.find_by_curso_activo_id(1)
        assert result is None


# ===========================================================================
# SQLAlchamyCursoEscolarRepository
# ===========================================================================


class TestSQLAlchemyCursoEscolarRepository:
    def setup_method(self):
        self.session = MagicMock()
        from infrastructure.repositories.sqlalchemy_curso_escolar_repository import (
            SQLAlchemyCursoEscolarRepository,
        )

        self.repo = SQLAlchemyCursoEscolarRepository(self.session)

    def test_constructor(self):
        assert self.repo is not None

    def test_get_by_id_none(self):
        self.session.query.return_value.get.return_value = None
        result = self.repo.get_by_id(999)
        assert result is None

    def test_get_all_vacio(self):
        self.session.query.return_value.all.return_value = []
        result = self.repo.get_all()
        assert result == []

    def test_delete_no_encontrado(self):
        self.session.query.return_value.get.return_value = None
        result = self.repo.delete(999)
        assert result is False

    def test_exists_no_encontrado(self):
        self.session.query.return_value.filter_by.return_value.first.return_value = None
        result = self.repo.exists(999)
        assert result is False

    def test_count_cero(self):
        self.session.query.return_value.count.return_value = 0
        result = self.repo.count()
        assert result == 0

    def test_find_active_none(self):
        self.session.query.return_value.filter_by.return_value.first.return_value = None
        result = self.repo.find_active()
        assert result is None

    def test_find_by_year_none(self):
        self.session.query.return_value.filter_by.return_value.first.return_value = None
        result = self.repo.find_by_year(2024)
        assert result is None

    def test_deactivate_all(self):
        self.session.query.return_value.update.return_value = 0
        self.repo.deactivate_all()  # No debe lanzar

    def test_find_by_date_range_vacio(self):
        self.session.query.return_value.filter.return_value.all.return_value = []
        result = self.repo.find_by_date_range("2024-09-01", "2025-06-30")
        assert result == []


# ===========================================================================
# SQLAlchemyZonaRepository
# ===========================================================================


class TestSQLAlchemyZonaRepository:
    def setup_method(self):
        self.session = MagicMock()
        from infrastructure.repositories.sqlalchemy_zona_repository import (
            SQLAlchemyZonaRepository,
        )

        self.repo = SQLAlchemyZonaRepository(self.session)

    def test_constructor(self):
        assert self.repo is not None

    def test_get_by_id_none(self):
        self.session.query.return_value.filter.return_value.first.return_value = None
        result = self.repo.get_by_id(999)
        assert result is None

    def test_get_all_vacio(self):
        self.session.query.return_value.all.return_value = []
        result = self.repo.get_all()
        assert result == []

    def test_delete_no_encontrado(self):
        self.session.query.return_value.filter.return_value.first.return_value = None
        result = self.repo.delete(999)
        assert result is False

    def test_exists_no_encontrado(self):
        self.session.query.return_value.filter.return_value.first.return_value = None
        result = self.repo.exists(999)
        assert result is False

    def test_count_cero(self):
        self.session.query.return_value.count.return_value = 0
        result = self.repo.count()
        assert result == 0

    def test_find_active_vacio(self):
        self.session.query.return_value.filter_by.return_value.all.return_value = []
        result = self.repo.find_activas()
        assert result == []

    def test_find_by_nombre_none(self):
        self.session.query.return_value.filter.return_value.first.return_value = None
        result = self.repo.find_by_nombre("Zona X")
        assert result is None
