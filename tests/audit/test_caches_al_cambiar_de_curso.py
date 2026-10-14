"""ESC-005 — que ninguna caché sirva datos del curso anterior.

Había dos cachés distintas: la de `utils.cache`, que la ventana vaciaba al
recargar, y las tres `TTLCache` de `application/use_cases/configuracion/
cache_service.py`, que nadie tocaba. Esas guardan la configuración, las zonas y
los profesores durante cinco minutos, así que tras cambiar de curso la
generación podía trabajar con las fechas del curso anterior.

Además se llegaba a `activar_curso` desde tres sitios y sólo uno avisaba a la
interfaz, así que vaciar únicamente desde la ventana no bastaba.
"""

import datetime
import inspect

from application.use_cases.configuracion import cache_service
from infrastructure.database.models import Configuracion, CursoEscolar, Zona
from services.gestor_cursos import GestorCursos
from utils.cache import cache_query, clear_all_cache, registrar_limpieza


def _curso(session, anio):
    curso = CursoEscolar(
        anio_inicio=anio,
        anio_fin=anio + 1,
        fecha_inicio=datetime.date(anio, 9, 1),
        fecha_fin=datetime.date(anio + 1, 6, 30),
        nombre=f"{anio}/{anio + 1}",
        activo=False,
        cerrado=False,
    )
    session.add(curso)
    session.commit()
    return curso


def test_vaciar_la_cache_general_vacia_tambien_las_registradas(session):
    session.add(Zona(nombre_zona="Patio A", activa=True))
    session.commit()

    cache_service.cache_zonas_activas(session)
    assert len(cache_service._cache_zonas) == 1

    clear_all_cache()

    assert len(cache_service._cache_zonas) == 0


def test_una_limpieza_que_falla_no_impide_las_demas(session):
    def explota():
        raise RuntimeError("caché rota")

    registrar_limpieza(explota)
    session.add(Zona(nombre_zona="Patio B", activa=True))
    session.commit()
    cache_service.cache_zonas_activas(session)

    clear_all_cache()

    assert len(cache_service._cache_zonas) == 0
    from utils.cache import _LIMPIEZAS_REGISTRADAS

    _LIMPIEZAS_REGISTRADAS.remove(explota)


def test_activar_un_curso_tira_la_configuracion_cacheada(session):
    viejo = _curso(session, 2025)
    nuevo = _curso(session, 2026)
    session.add(
        Configuracion(
            anio_inicio_curso=2025,
            fecha_inicio_curso=datetime.date(2025, 9, 1),
            fecha_fin_curso=datetime.date(2026, 6, 30),
            hora_recreo1_manana=datetime.time(11, 0),
            hora_recreo2_manana=datetime.time(12, 0),
            curso_activo_id=viejo.id,
        )
    )
    session.commit()

    cacheada = cache_service.cache_configuracion(session)
    assert cacheada.anio_inicio_curso == 2025

    GestorCursos.from_session(session).activar_curso(nuevo.id)

    assert cache_service.cache_configuracion(session).anio_inicio_curso == 2026


def test_la_limpieza_se_hace_en_el_servicio_y_no_solo_en_la_ventana():
    """A `activar_curso` se llega desde el selector, la gestión y la creación."""
    fuente = inspect.getsource(GestorCursos.activar_curso)
    assert "_vaciar_las_caches" in fuente


def test_utils_no_importa_la_capa_de_aplicacion():
    """El registro es al revés a propósito: `utils` no puede conocer `application`."""
    import utils.cache as modulo

    fuente = inspect.getsource(modulo)
    assert "from application" not in fuente
    assert "import application" not in fuente


def test_la_cache_de_consultas_sigue_funcionando(session):
    llamadas = []

    @cache_query(ttl=60, prefijo="prueba")
    def contar(session):
        llamadas.append(1)
        return len(llamadas)

    contar(session)
    contar(session)
    assert len(llamadas) == 1

    clear_all_cache()
    contar(session)
    assert len(llamadas) == 2
