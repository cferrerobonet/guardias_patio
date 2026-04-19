"""Cobertura extra para DistribucionCuotasService."""

import json
import sys
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from services.distribucion_cuotas_service import DistribucionCuotasService


def _p(pid, turno="mixto", jornada=100.0, tutor=False, activo=True, recreos=None):
    return SimpleNamespace(
        id=pid,
        nombre_completo=f"P{pid}",
        activo=activo,
        turno=turno,
        porcentaje_jornada=jornada,
        tutor=tutor,
        recreos_permitidos=recreos,
        fecha_inicio_guardias=None,
    )


def _zona(zid, nombre="Z", fi=None, ff=None):
    return SimpleNamespace(id=zid, nombre=nombre, fecha_inicio=fi, fecha_fin=ff)


class _Q:
    def __init__(self, first=None, allv=None, countv=0):
        self._first = first
        self._all = allv or []
        self._count = countv

    def options(self, *_a, **_k):
        return self

    def filter(self, *_a, **_k):
        return self

    def all(self):
        return self._all

    def first(self):
        return self._first

    def count(self):
        return self._count


class _Session:
    def __init__(self, config=None, profesores=None, zonas=None, activos=0):
        self.config = config
        self.profesores = profesores or []
        self.zonas = zonas or []
        self.activos = activos

    def query(self, model):
        name = getattr(model, "__name__", str(model))
        if "Configuracion" in name:
            return _Q(first=self.config)
        if "Profesor" in name:
            return _Q(allv=self.profesores, countv=self.activos)
        if "Zona" in name:
            return _Q(allv=self.zonas)
        return _Q()


class TestDistribucionExtra:
    def test_calcular_cuotas_sin_profesores(self):
        s = _Session(config=SimpleNamespace())
        d = DistribucionCuotasService(s)
        assert d.calcular_cuotas([]) == {}

    def test_calcular_cuotas_sin_config_lanza(self):
        s = _Session(config=None)
        d = DistribucionCuotasService(s)
        with pytest.raises(ValueError):
            d.calcular_cuotas([_p(1)])

    def test_calcular_cuota_profesor_suma_factores_cero(self):
        cfg = SimpleNamespace(ajuste_tutores=1.0, ajuste_no_tutores=1.0)
        prof = _p(1, activo=False)
        s = _Session(config=cfg)
        d = DistribucionCuotasService(s)
        assert d.calcular_cuota_profesor(prof, 10, [prof]) == 0

    def test_obtener_info_cuota_con_observaciones(self):
        cfg = SimpleNamespace()
        prof = _p(1, turno="mañana")
        prof.fecha_inicio_guardias = date(2024, 9, 1)
        s = _Session(config=cfg, profesores=[prof], zonas=[_zona(1)])
        d = DistribucionCuotasService(s)
        d._calcular_total_slots = lambda _c: 12
        d._calcular_factores_participacion = lambda _p, _c: {1: 1.0}
        d.calcular_cuota_profesor = lambda *_a, **_k: 4
        info = d.obtener_info_cuota(prof)
        assert info.cuota == 4
        assert len(info.observaciones) == 2

    def test_total_slots_cero_por_entradas_vacias(self, monkeypatch):
        s = _Session(zonas=[])
        d = DistribucionCuotasService(s)
        cfg = SimpleNamespace()
        monkeypatch.setattr(
            "services.distribucion_cuotas_service.listar_dias_lectivos", lambda _c: []
        )
        monkeypatch.setattr(
            "services.distribucion_cuotas_service._parse_recreos_config", lambda _c: []
        )
        assert d._calcular_total_slots(cfg) == 0

    def test_total_slots_respeta_fechas_zona(self, monkeypatch):
        z1 = _zona(1, fi=date(2024, 9, 3))
        z2 = _zona(2, ff=date(2024, 9, 2))
        s = _Session(zonas=[z1, z2])
        d = DistribucionCuotasService(s)
        cfg = SimpleNamespace()
        monkeypatch.setattr(
            "services.distribucion_cuotas_service.listar_dias_lectivos",
            lambda _c: [date(2024, 9, 2), date(2024, 9, 3)],
        )
        monkeypatch.setattr(
            "services.distribucion_cuotas_service._parse_recreos_config",
            lambda _c: [{"id": 1, "turno": "mañana", "zonas": 2}],
        )
        assert d._calcular_total_slots(cfg) == 2

    def test_slots_por_turno_default_turno_manana(self, monkeypatch):
        s = _Session(zonas=[_zona(1)])
        d = DistribucionCuotasService(s)
        cfg = SimpleNamespace()
        monkeypatch.setattr(
            "services.distribucion_cuotas_service.listar_dias_lectivos", lambda _c: [date(2024, 9, 2)]
        )
        monkeypatch.setattr(
            "services.distribucion_cuotas_service._parse_recreos_config",
            lambda _c: [{"id": 1}],
        )
        assert d._calcular_slots_por_turno(cfg) == {"mañana": 1, "tarde": 0}

    def test_get_turno_profesor_completo_ambos(self):
        d = DistribucionCuotasService(_Session(config=SimpleNamespace()))
        assert d._get_turno_profesor(_p(1, turno="completo")) == "mixto"
        assert d._get_turno_profesor(_p(2, turno="ambos")) == "mixto"

    def test_factores_participacion_tutor_y_no_tutor(self):
        d = DistribucionCuotasService(_Session(config=SimpleNamespace()))
        cfg = SimpleNamespace(ajuste_tutores=1.2, ajuste_no_tutores=0.8)
        p1 = _p(1, tutor=True, jornada=100)
        p2 = _p(2, tutor=False, jornada=50)
        f = d._calcular_factores_participacion([p1, p2], cfg)
        assert f[1] == pytest.approx(1.2)
        assert f[2] == pytest.approx(0.4)

    def test_distribuir_slots_equitativamente_suma_factores_cero(self):
        d = DistribucionCuotasService(_Session(config=SimpleNamespace()))
        p1 = _p(1)
        p2 = _p(2)
        assert d._distribuir_slots_equitativamente([p1, p2], {1: 0, 2: 0}, 10) == {1: 0, 2: 0}

    def test_distribuir_slots_equitativamente_con_diferencia_redondeo(self):
        d = DistribucionCuotasService(_Session(config=SimpleNamespace()))
        p1 = _p(1)
        p2 = _p(2)
        cuotas = d._distribuir_slots_equitativamente([p1, p2], {1: 1, 2: 1}, 3)
        assert sum(cuotas.values()) == 3

    def test_distribuir_slots_grupo_con_diferencia_negativa(self):
        d = DistribucionCuotasService(_Session(config=SimpleNamespace()))
        p1 = _p(1)
        p2 = _p(2)
        # Forzamos suma redondeada > total_slots
        cuotas = d._distribuir_slots_grupo([p1, p2], {1: 1, 2: 1}, 1, "x")
        assert sum(cuotas.values()) == 1

    def test_distribuir_slots_por_turno_usa_turno_efectivo(self):
        cfg = SimpleNamespace(recreos_config=json.dumps([
            {"id": 1, "turno": "mañana"},
            {"id": 3, "turno": "tarde"},
        ]))
        p_manana = _p(1, turno="mixto", recreos=json.dumps([1]))
        p_tarde = _p(2, turno="mixto", recreos=json.dumps([3]))
        p_ninguno = _p(3, turno="mixto", recreos=json.dumps([99]))
        s = _Session(config=cfg)
        d = DistribucionCuotasService(s)

        cuotas = d._distribuir_slots_por_turno(
            [p_manana, p_tarde, p_ninguno],
            {1: 1.0, 2: 1.0, 3: 1.0},
            {"mañana": 2, "tarde": 2},
        )
        assert cuotas[1] == 2
        assert cuotas[2] == 2
        assert cuotas[3] == 0
