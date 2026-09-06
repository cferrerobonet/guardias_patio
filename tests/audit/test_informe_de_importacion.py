"""FUN-007 — decir qué va a pasar antes de importar profesores.

La importación escribía directamente: si el mapeo de columnas estaba mal o el
fichero traía nombres repetidos, el usuario se enteraba al final, por el
recuento. Ahora la lectura del fichero está separada de la escritura y se puede
enseñar fila a fila lo que ocurrirá.
"""

import pytest

from infrastructure.database.models import Profesor
from infrastructure.repositories.repository_factory import RepositoryFactory
from services.importador_profesores import analizar_importacion, leer_filas_de_profesores

pd = pytest.importorskip("pandas")

MAPEO = {"nombre": "Nombre", "email": "Correo"}


def _hoja(tmp_path, filas, nombre="claustro.xlsx"):
    ruta = tmp_path / nombre
    pd.DataFrame(filas).to_excel(ruta, index=False)
    return str(ruta)


def test_leer_no_escribe_nada(session, tmp_path):
    ruta = _hoja(tmp_path, [{"Nombre": "Nuevo, Profesor", "Correo": "n@epla.es"}])

    filas, error = leer_filas_de_profesores(ruta, skip_rows=0, column_mapping=MAPEO)

    assert error is None
    assert [f["nombre"] for f in filas] == ["Nuevo, Profesor"]
    assert session.query(Profesor).count() == 0


def test_distingue_nuevos_de_los_que_ya_estan(session, tmp_path):
    session.add(
        Profesor(
            nombre_completo="Ya Estaba, Ana",
            horas_contrato=25.0,
            porcentaje_jornada=100.0,
            turno="mañana",
            tutor=False,
            activo=True,
        )
    )
    session.commit()
    ruta = _hoja(
        tmp_path,
        [
            {"Nombre": "Ya Estaba, Ana", "Correo": "ana@epla.es"},
            {"Nombre": "Nueva, Marta", "Correo": "marta@epla.es"},
        ],
    )

    informe = analizar_importacion(
        RepositoryFactory(session), ruta, skip_rows=0, column_mapping=MAPEO
    )

    assert informe["nuevos"] == 1
    assert informe["existentes"] == 1
    assert [f["estado"] for f in informe["filas"]] == ["existente", "nuevo"]


def test_avisa_de_los_repetidos_dentro_del_fichero(session, tmp_path):
    """Antes se importaba el primero y el segundo se contaba como «ya existente»."""
    ruta = _hoja(
        tmp_path,
        [
            {"Nombre": "Duplicado, Juan", "Correo": "j@epla.es"},
            {"Nombre": "duplicado,  juan", "Correo": "otro@epla.es"},
        ],
    )

    informe = analizar_importacion(
        RepositoryFactory(session), ruta, skip_rows=0, column_mapping=MAPEO
    )

    assert informe["nuevos"] == 1
    assert informe["repetidos"] == 1


def test_un_mapeo_equivocado_se_explica_en_vez_de_romper(session, tmp_path):
    ruta = _hoja(tmp_path, [{"Nombre": "Alguien, Alguno", "Correo": "a@epla.es"}])

    informe = analizar_importacion(
        RepositoryFactory(session),
        ruta,
        skip_rows=0,
        column_mapping={"nombre": "NoExiste", "email": "Correo"},
    )

    assert informe["error"]
    assert informe["nuevos"] == 0


def test_un_fichero_ilegible_no_lanza_excepcion(session, tmp_path):
    roto = tmp_path / "roto.xlsx"
    roto.write_text("esto no es una hoja de cálculo", encoding="utf-8")

    informe = analizar_importacion(
        RepositoryFactory(session), str(roto), skip_rows=0, column_mapping=MAPEO
    )

    assert informe["error"]
    assert informe["filas"] == []


def test_las_filas_vacias_no_cuentan(session, tmp_path):
    ruta = _hoja(
        tmp_path,
        [
            {"Nombre": "Válido, Uno", "Correo": "u@epla.es"},
            {"Nombre": None, "Correo": "vacio@epla.es"},
            {"Nombre": "   ", "Correo": None},
        ],
    )

    informe = analizar_importacion(
        RepositoryFactory(session), ruta, skip_rows=0, column_mapping=MAPEO
    )

    assert len(informe["filas"]) == 1


def test_el_numero_de_fila_apunta_a_la_hoja(session, tmp_path):
    """Sirve para ir a corregirla: cuenta la cabecera y empieza en 1, no en 0."""
    ruta = _hoja(tmp_path, [{"Nombre": "Primera, Fila", "Correo": "p@epla.es"}])

    informe = analizar_importacion(
        RepositoryFactory(session), ruta, skip_rows=0, column_mapping=MAPEO
    )

    assert informe["filas"][0]["fila"] == 2


def test_la_importacion_pasa_por_el_informe():
    """El botón no puede volver a escribir sin enseñar antes qué va a hacer."""
    import inspect

    from presentation.forms.import_export_form import ImportExportForm

    fuente = inspect.getsource(ImportExportForm.importar_profesores)
    assert "InformeImportacionDialog" in fuente
    assert fuente.index("InformeImportacionDialog") < fuente.index("ejecutar_con_progreso")
