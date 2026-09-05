"""ESC-007: la clave de caché no puede depender de la dirección de memoria.

`_generate_cache_key` construía la clave con `str(arg)`. Un objeto sin `__str__`
propio se representa como `<Clase object at 0x7f...>`, y Python reutiliza
direcciones: instancias creadas y destruidas en serie producían la misma clave, de
modo que un caso de uso podía recibir el resultado cacheado de otro anterior
durante todo el TTL (3 minutos en profesores).
"""

import re

import pytest

from utils.cache import _generate_cache_key, _representacion_estable


class _CasoDeUsoFalso:
    """Objeto sin `__str__` propio, como los casos de uso reales."""


def _funcion(self, argumento):
    pass


def test_la_clave_no_contiene_direcciones_de_memoria():
    clave = _generate_cache_key(_funcion, (_CasoDeUsoFalso(), 7), {})
    assert not re.search(r"0x[0-9a-fA-F]+", clave), clave


def test_dos_instancias_de_la_misma_clase_dan_la_misma_clave():
    """Y por tanto comparten caché a propósito, no por casualidad."""
    primera = _generate_cache_key(_funcion, (_CasoDeUsoFalso(), 7), {})
    segunda = _generate_cache_key(_funcion, (_CasoDeUsoFalso(), 7), {})
    assert primera == segunda


def test_argumentos_distintos_siguen_dando_claves_distintas():
    """Lo que no puede pasar es que la corrección lo colapse todo en una clave."""
    a = _generate_cache_key(_funcion, (_CasoDeUsoFalso(), 7), {})
    b = _generate_cache_key(_funcion, (_CasoDeUsoFalso(), 8), {})
    assert a != b


def test_clases_distintas_no_comparten_clave():
    class OtroCaso:
        pass

    a = _generate_cache_key(_funcion, (_CasoDeUsoFalso(), 7), {})
    b = _generate_cache_key(_funcion, (OtroCaso(), 7), {})
    assert a != b


def test_el_prefijo_llega_a_la_clave():
    """ESC-007 (segunda parte): `cache_key_prefix` se aceptaba y no se usaba."""
    sin_prefijo = _generate_cache_key(_funcion, (_CasoDeUsoFalso(), 7), {})
    con_prefijo = _generate_cache_key(_funcion, (_CasoDeUsoFalso(), 7), {}, "profesor")

    assert con_prefijo != sin_prefijo
    assert con_prefijo.startswith("profesor:")


def test_el_decorador_de_repositorios_propaga_el_prefijo():
    import inspect

    from utils import repository_cache

    fuente = inspect.getsource(repository_cache.cache_repository_query)
    assert "prefijo=cache_key_prefix" in fuente, "el prefijo vuelve a perderse por el camino"


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [(42, "42"), ("hola", "hola"), (None, "None"), ((1, 2), "(1, 2)")],
)
def test_los_argumentos_normales_no_cambian(valor, esperado):
    assert _representacion_estable(valor) == esperado


def test_las_sesiones_siguen_fuera_de_la_clave():
    """Incluirlas haría la caché inútil: cada sesión tendría la suya."""

    class SesionFalsa:
        def query(self, *_):
            return None

    con_sesion = _generate_cache_key(_funcion, (SesionFalsa(), 7), {})
    assert "SesionFalsa" not in con_sesion
