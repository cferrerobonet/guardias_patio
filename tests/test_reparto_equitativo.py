"""Equidad primero en el reparto por turnos (2026-10-06).

Con todo el claustro de tarde y tres mixtos, los mixtos recibían cuotas de 494 y
248 guardias y una guardia diaria todo el curso. Decisión de CarlosFB: la equidad
va primero y es aceptable que queden patios sin cubrir.
"""

import pytest

from services.reparto_equitativo import reparto_equitativo

H = {"mañana": 878, "tarde": 878}


def test_sin_mixtos_cada_turno_se_reparte_entero_entre_los_suyos():
    r = reparto_equitativo(H, {"mañana": 39, "tarde": 30}, 0)
    assert r["mañana"].cubiertos == pytest.approx(878)
    assert r["tarde"].cubiertos == pytest.approx(878)
    assert r["mañana"].de_mixtos == r["tarde"].de_mixtos == 0


def test_sin_fijos_de_un_turno_los_mixtos_no_pasan_del_nivel_de_los_demas():
    r = reparto_equitativo(H, {"mañana": 0, "tarde": 28}, 3)
    nivel_tarde = 878 / 28
    assert r["tarde"].cubiertos == pytest.approx(878)
    assert r["mañana"].de_mixtos / 3 == pytest.approx(nivel_tarde, rel=1e-6)
    assert r["mañana"].cubiertos < 878, "lo que no cabe queda sin cubrir a propósito"


def test_con_los_dos_turnos_los_mixtos_solo_ponen_lo_que_falta_al_mismo_nivel():
    r = reparto_equitativo(H, {"mañana": 39, "tarde": 30}, 4)
    assert r["mañana"].cubiertos == pytest.approx(878)
    assert r["tarde"].cubiertos == pytest.approx(878)
    assert r["mañana"].de_mixtos == pytest.approx(0)
    nivel_mixtos = r["tarde"].de_mixtos / 4
    assert nivel_mixtos == pytest.approx(r["tarde"].nivel_fijos, rel=1e-6), (
        "antes cobraban la parte de los dos turnos: unas 46 frente a 23-29"
    )


def test_solo_mixtos_se_cubre_todo():
    r = reparto_equitativo(H, {"mañana": 0, "tarde": 0}, 31)
    assert r["mañana"].cubiertos == pytest.approx(878)
    assert r["tarde"].cubiertos == pytest.approx(878)


def test_las_voluntarias_cuentan_en_el_nivel():
    """La parte del curso incluye las voluntarias hechas, también al comparar con los mixtos."""
    sin = reparto_equitativo(H, {"mañana": 0, "tarde": 28}, 3)
    con = reparto_equitativo(H, {"mañana": 0, "tarde": 28}, 3, {"tarde": 230}, 0)
    assert con["mañana"].de_mixtos / 3 == pytest.approx((878 + 230) / 28, rel=1e-6)
    assert con["mañana"].de_mixtos > sin["mañana"].de_mixtos
