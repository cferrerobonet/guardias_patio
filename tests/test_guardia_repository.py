"""
Tests para sqlalchemy_guardia_repository.py (200 stmts, ~50% coverage).
"""

import sys
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class TestSQLAlchemyGuardiaRepository:
    def setup_method(self):
        self.session = MagicMock()
        from infrastructure.repositories.sqlalchemy_guardia_repository import (
            SQLAlchemyGuardiaRepository,
        )

        self.repo = SQLAlchemyGuardiaRepository(self.session)

    def test_constructor(self):
        assert self.repo is not None

    def test_get_by_id_none(self):
        self.session.query.return_value.filter.return_value.first.return_value = None
        result = self.repo.get_by_id(999)
        assert result is None

    def test_get_all_vacio(self):
        self.session.query.return_value.options.return_value.all.return_value = []
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

    def test_find_by_fecha_vacio(self):
        self.session.query.return_value.options.return_value.filter.return_value.all.return_value = []
        result = self.repo.find_by_fecha(date(2024, 1, 15))
        assert result == []

    def test_find_by_profesor_vacio(self):
        self.session.query.return_value.options.return_value.filter_by.return_value.all.return_value = []
        result = self.repo.find_by_profesor(1)
        assert result == []

    def test_find_by_zona_vacio(self):
        self.session.query.return_value.options.return_value.filter_by.return_value.all.return_value = []
        result = self.repo.find_by_zona(1)
        assert result == []

    def test_find_by_rango_fechas_vacio(self):
        q = self.session.query.return_value
        q.options.return_value.filter.return_value.all.return_value = []
        result = self.repo.find_by_rango_fechas(date(2024, 1, 1), date(2024, 1, 31))
        assert result == []

    def test_contar_guardias_profesor_cero(self):
        self.session.query.return_value.filter.return_value.count.return_value = 0
        result = self.repo.contar_guardias_profesor(1)
        assert result == 0

    def test_find_by_curso_vacio(self):
        self.session.query.return_value.options.return_value.filter_by.return_value.all.return_value = []
        result = self.repo.find_by_curso(1)
        assert result == []

    def test_count_by_curso_cero(self):
        self.session.query.return_value.filter_by.return_value.count.return_value = 0
        result = self.repo.count_by_curso(1)
        assert result == 0

    def test_delete_all_cero(self):
        self.session.query.return_value.count.return_value = 0
        self.session.query.return_value.delete.return_value = 0
        result = self.repo.delete_all()
        assert result == 0

    def test_existe_guardia_profesor_false(self):
        self.session.query.return_value.filter.return_value.first.return_value = None
        result = self.repo.existe_guardia_profesor_en_momento(
            profesor_id=1, fecha=date(2024, 1, 15), turno="M", recreo=1
        )
        assert result is False

    def test_existe_guardia_zona_false(self):
        self.session.query.return_value.filter.return_value.first.return_value = None
        result = self.repo.existe_guardia_zona_en_momento(
            zona_id=1, fecha=date(2024, 1, 15), turno="M", recreo=1
        )
        assert result is False
