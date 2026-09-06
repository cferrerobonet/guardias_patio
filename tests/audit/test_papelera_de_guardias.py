"""FUN-012 — deshacer «Limpiar guardias».

Limpiar borraba el calendario entero sin vuelta atrás inmediata: desde v5.63.0
se hace copia de la base de datos, pero recuperarla obliga a ir a
Importar/Exportar y arrastra consigo todo lo demás. La papelera guarda sólo las
guardias borradas y las devuelve con un botón durante 24 horas.

Estos tests usan una base sobre fichero, no en memoria: la papelera vive junto
al fichero de la base de datos del usuario.
"""

import datetime
import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from infrastructure.database.models import Base, Guardia, Profesor, Zona
from services import papelera_guardias

LUNES = datetime.date(2025, 10, 6)


@pytest.fixture
def sesion_en_fichero(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'guardias_patio.db'}")
    Base.metadata.create_all(engine)
    sesion = sessionmaker(bind=engine)()
    yield sesion
    sesion.close()
    engine.dispose()


@pytest.fixture
def con_guardias(sesion_en_fichero):
    sesion = sesion_en_fichero
    sesion.add_all(
        [
            Profesor(
                nombre_completo=f"Apellido{i}, Nombre",
                horas_contrato=25.0,
                porcentaje_jornada=100.0,
                turno="mañana",
                tutor=False,
                activo=True,
            )
            for i in range(2)
        ]
    )
    sesion.add(Zona(nombre_zona="Patio A", activa=True))
    sesion.commit()
    profesores = sesion.query(Profesor).all()
    zona = sesion.query(Zona).first()
    for i, profesor in enumerate(profesores):
        sesion.add(
            Guardia(
                profesor_id=profesor.id,
                fecha=LUNES + datetime.timedelta(days=i),
                turno="mañana",
                recreo=1,
                zona_id=zona.id,
            )
        )
    sesion.commit()
    return sesion


def test_limpiar_borra_y_deja_rastro(con_guardias):
    assert papelera_guardias.limpiar_guardias(con_guardias) == 2
    assert con_guardias.query(Guardia).count() == 0
    assert papelera_guardias.ruta_de_la_papelera(con_guardias).exists()


def test_deshacer_devuelve_las_guardias(con_guardias):
    papelera_guardias.limpiar_guardias(con_guardias)

    assert papelera_guardias.deshacer_la_limpieza(con_guardias) == 2
    assert con_guardias.query(Guardia).count() == 2


def test_deshacer_conserva_los_datos_de_cada_guardia(con_guardias):
    antes = {
        (g.profesor_id, g.fecha, g.turno, g.recreo, g.zona_id)
        for g in con_guardias.query(Guardia).all()
    }
    papelera_guardias.limpiar_guardias(con_guardias)
    papelera_guardias.deshacer_la_limpieza(con_guardias)

    despues = {
        (g.profesor_id, g.fecha, g.turno, g.recreo, g.zona_id)
        for g in con_guardias.query(Guardia).all()
    }
    assert despues == antes


def test_deshacer_dos_veces_no_duplica(con_guardias):
    papelera_guardias.limpiar_guardias(con_guardias)
    papelera_guardias.deshacer_la_limpieza(con_guardias)

    assert papelera_guardias.deshacer_la_limpieza(con_guardias) == 0
    assert con_guardias.query(Guardia).count() == 2


def test_se_salta_las_de_un_profesor_que_ya_no_existe(con_guardias):
    papelera_guardias.limpiar_guardias(con_guardias)
    borrado = con_guardias.query(Profesor).first()
    con_guardias.delete(borrado)
    con_guardias.commit()

    assert papelera_guardias.deshacer_la_limpieza(con_guardias) == 1


def test_no_pisa_un_hueco_vuelto_a_llenar(con_guardias):
    original = con_guardias.query(Guardia).first()
    hueco = (original.profesor_id, original.fecha, original.zona_id)
    papelera_guardias.limpiar_guardias(con_guardias)

    con_guardias.add(
        Guardia(
            profesor_id=hueco[0], fecha=hueco[1], turno="mañana", recreo=1, zona_id=hueco[2]
        )
    )
    con_guardias.commit()

    assert papelera_guardias.deshacer_la_limpieza(con_guardias) == 1
    assert con_guardias.query(Guardia).count() == 2


def test_la_papelera_caduca_a_las_24_horas(con_guardias):
    papelera_guardias.limpiar_guardias(con_guardias)
    ruta = papelera_guardias.ruta_de_la_papelera(con_guardias)

    contenido = json.loads(ruta.read_text(encoding="utf-8"))
    caducada = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=25)
    contenido["momento"] = caducada.isoformat()
    ruta.write_text(json.dumps(contenido), encoding="utf-8")

    assert papelera_guardias.hay_algo_que_deshacer(con_guardias) is None


def test_recien_limpiado_hay_algo_que_deshacer(con_guardias):
    papelera_guardias.limpiar_guardias(con_guardias)

    pendiente = papelera_guardias.hay_algo_que_deshacer(con_guardias)
    assert pendiente is not None
    assert pendiente["cuantas"] == 2


def test_sin_limpiar_no_hay_nada_que_deshacer(con_guardias):
    assert papelera_guardias.hay_algo_que_deshacer(con_guardias) is None


def test_una_papelera_ilegible_no_rompe_nada(con_guardias):
    papelera_guardias.limpiar_guardias(con_guardias)
    papelera_guardias.ruta_de_la_papelera(con_guardias).write_text("{ roto", encoding="utf-8")

    assert papelera_guardias.hay_algo_que_deshacer(con_guardias) is None
    assert papelera_guardias.deshacer_la_limpieza(con_guardias) == 0


def test_en_memoria_la_limpieza_sigue_funcionando(session):
    """Sin fichero no hay papelera, pero limpiar no debe fallar por eso."""
    assert papelera_guardias.ruta_de_la_papelera(session) is None
    assert papelera_guardias.limpiar_guardias(session) == 0
