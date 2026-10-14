"""
Tests para application/app_services.py.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from application.app_services import AppServices as ApplicationServices


class TestApplicationServicesRepositories:
    """Tests de los repositorios lazy-init de ApplicationServices."""

    def setup_method(self):
        self.session = MagicMock()
        self.svc = ApplicationServices(self.session)

    def test_profesores_repo_lazy(self):
        repo = self.svc.profesores
        assert repo is not None
        # Segunda llamada devuelve el mismo objeto
        assert self.svc.profesores is repo

    def test_zonas_repo_lazy(self):
        repo = self.svc.zonas
        assert repo is not None
        assert self.svc.zonas is repo

    def test_guardias_repo_lazy(self):
        repo = self.svc.guardias
        assert repo is not None
        assert self.svc.guardias is repo

    def test_ausencias_repo_lazy(self):
        repo = self.svc.ausencias
        assert repo is not None
        assert self.svc.ausencias is repo

    def test_configuracion_repo_lazy(self):
        repo = self.svc.configuracion_repo
        assert repo is not None
        assert self.svc.configuracion_repo is repo

    def test_cursos_repo_lazy(self):
        repo = self.svc.cursos
        assert repo is not None
        assert self.svc.cursos is repo


class TestApplicationServicesUseCases:
    """Tests de los factory methods de use cases."""

    def setup_method(self):
        self.session = MagicMock()
        self.svc = ApplicationServices(self.session)

    def test_obtener_configuracion(self):
        uc = self.svc.obtener_configuracion()
        assert uc is not None

    def test_actualizar_configuracion(self):
        uc = self.svc.actualizar_configuracion()
        assert uc is not None

    def test_listar_profesores(self):
        uc = self.svc.listar_profesores()
        assert uc is not None

    def test_obtener_profesor(self):
        uc = self.svc.obtener_profesor()
        assert uc is not None

    def test_crear_profesor(self):
        uc = self.svc.crear_profesor()
        assert uc is not None

    def test_actualizar_profesor(self):
        uc = self.svc.actualizar_profesor()
        assert uc is not None

    def test_eliminar_profesor(self):
        uc = self.svc.eliminar_profesor()
        assert uc is not None

    def test_buscar_profesores(self):
        uc = self.svc.buscar_profesores()
        assert uc is not None

    def test_listar_zonas(self):
        uc = self.svc.listar_zonas()
        assert uc is not None

    def test_obtener_zona(self):
        uc = self.svc.obtener_zona()
        assert uc is not None

    def test_crear_zona(self):
        uc = self.svc.crear_zona()
        assert uc is not None

    def test_actualizar_zona(self):
        uc = self.svc.actualizar_zona()
        assert uc is not None

    def test_eliminar_zona(self):
        uc = self.svc.eliminar_zona()
        assert uc is not None

    def test_obtener_guardias(self):
        uc = self.svc.obtener_guardias()
        assert uc is not None

    def test_asignar_guardia(self):
        uc = self.svc.asignar_guardia()
        assert uc is not None

    def test_limpiar_guardias(self):
        uc = self.svc.limpiar_guardias()
        assert uc is not None


class TestApplicationServicesHelpers:
    """Tests de helpers de conteo."""

    def setup_method(self):
        self.session = MagicMock()
        self.svc = ApplicationServices(self.session)

    def _setup_repos(self, n_profesores=3, n_activos=2, n_zonas=1, n_guardias=4):
        mock_profesores = [MagicMock(activo=True)] * n_activos + [
            MagicMock(activo=False)
        ] * (n_profesores - n_activos)
        self.svc.profesores.get_all = MagicMock(return_value=mock_profesores)
        self.svc.profesores.count = MagicMock(return_value=n_profesores)
        self.svc.zonas.count = MagicMock(return_value=n_zonas)
        self.svc.guardias.count = MagicMock(return_value=n_guardias)
        self.svc.guardias.get_all = MagicMock(return_value=[])
        self.svc.cursos.count = MagicMock(return_value=1)
        self.svc.configuracion_repo.count = MagicMock(return_value=1)

    def test_contar_profesores_activos(self):
        self._setup_repos(n_profesores=3, n_activos=2)
        assert self.svc.contar_profesores_activos() == 2

    def test_contar_profesores_inactivos(self):
        self._setup_repos(n_profesores=3, n_activos=2)
        assert self.svc.contar_profesores_inactivos() == 1

    def test_contar_zonas(self):
        self._setup_repos()
        assert self.svc.contar_zonas() == 1

    def test_contar_guardias(self):
        self._setup_repos(n_guardias=4)
        assert self.svc.contar_guardias() == 4

    def test_contar_profesores(self):
        self._setup_repos(n_profesores=3)
        assert self.svc.contar_profesores() == 3

    def test_contar_cursos(self):
        self._setup_repos()
        assert self.svc.contar_cursos() == 1

    def test_contar_configuraciones(self):
        self._setup_repos()
        assert self.svc.contar_configuraciones() == 1

    def test_fecha_min_guardias_sin_guardias(self):
        self.svc.guardias.get_all = MagicMock(return_value=[])
        assert self.svc.fecha_min_guardias() is None

    def test_fecha_min_guardias_con_guardias(self):
        from datetime import date

        g1 = MagicMock(fecha=date(2024, 1, 15))
        g2 = MagicMock(fecha=date(2024, 1, 5))
        self.svc.guardias.get_all = MagicMock(return_value=[g1, g2])
        assert self.svc.fecha_min_guardias() == date(2024, 1, 5)

    def test_fecha_max_guardias_sin_guardias(self):
        self.svc.guardias.get_all = MagicMock(return_value=[])
        assert self.svc.fecha_max_guardias() is None

    def test_fecha_max_guardias_con_guardias(self):
        from datetime import date

        g1 = MagicMock(fecha=date(2024, 1, 5))
        g2 = MagicMock(fecha=date(2024, 1, 20))
        self.svc.guardias.get_all = MagicMock(return_value=[g1, g2])
        assert self.svc.fecha_max_guardias() == date(2024, 1, 20)


class TestApplicationServicesGestorCursos:
    def test_gestor_cursos_lazy(self):
        session = MagicMock()
        svc = ApplicationServices(session)
        gc = svc.gestor_cursos
        assert gc is not None
        assert svc.gestor_cursos is gc


class TestApplicationServicesCrossAggregate:
    """Tests de los métodos cross-aggregate."""

    def setup_method(self):
        self.session = MagicMock()
        self.svc = ApplicationServices(self.session)

    def test_profesores_con_guardias_en_curso_vacio(self):
        self.session.query.return_value.join.return_value.filter.return_value.distinct.return_value.order_by.return_value.all.return_value = []
        result = self.svc.profesores_con_guardias_en_curso(1)
        assert result == []

    def test_ausencias_de_profesores_en_curso_sin_profesores(self):
        # Sin guardias en el curso → lista vacía
        self.session.query.return_value.filter.return_value.distinct.return_value.all.return_value = []
        result = self.svc.ausencias_de_profesores_en_curso(1)
        assert result == []

    def test_profesores_activos_con_fechas_especiales_vacio(self):
        self.session.query.return_value.filter.return_value.all.return_value = []
        result = self.svc.profesores_activos_con_fechas_especiales()
        assert result == []
