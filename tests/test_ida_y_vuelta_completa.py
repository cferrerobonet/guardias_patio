"""
Ida y vuelta completa de los datos: sincronización con la nube y copia JSON.

La descarga de la nube reconstruye la base local desde cero, así que una
columna que no viaja se pierde en cada arranque sin que nadie lo note. Pasó
con la zona preferida del profesor (2026-10-03) y, al revisarlo, con los datos
de sustitución de las guardias, el curso activo, la capacidad de las zonas y
los cursos escolares de la copia manual.

Cada tabla se rellena con valores distintos de los de por defecto en todas sus
columnas y se compara columna a columna tras exportar e importar en una base
vacía con las claves foráneas activadas, como en la aplicación. Si se añade
una columna al modelo y no a estas filas, el test lo dice: hay que darle valor
aquí y hacerla viajar en los dos caminos.
"""

import json
from datetime import date, datetime, time

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from infrastructure.database.models import (
    Ausencia,
    Base,
    Configuracion,
    CursoEscolar,
    Guardia,
    Profesor,
    Zona,
)

CLAVE = Fernet.generate_key()

#: Tablas que no viajan, a propósito.
TABLAS_LOCALES = {"guardias_audit_log"}

#: Columnas que no suben a la nube, a propósito: la ruta del justificante médico
#: es de este equipo y es dato de salud (PRIV-001). La copia manual sí la lleva.
SOLO_EN_LOCAL = {("ausencias", "documento_path")}


def _filas():
    return {
        CursoEscolar: [
            dict(id=3, anio_inicio=2025, anio_fin=2026, fecha_inicio=date(2025, 9, 8),
                 fecha_fin=date(2026, 6, 19), nombre="Curso 2025/2026", activo=False,
                 cerrado=True, created_at=datetime(2025, 7, 1, 10, 30, 15)),
            dict(id=7, anio_inicio=2026, anio_fin=2027, fecha_inicio=date(2026, 9, 7),
                 fecha_fin=date(2027, 6, 18), nombre="Curso 2026/2027", activo=True,
                 cerrado=False, created_at=datetime(2026, 7, 2, 9, 5, 0)),
        ],
        Zona: [
            dict(id=11, nombre_zona="Patio norte", descripcion="Junto a la pista",
                 fecha_inicio=date(2026, 9, 14), fecha_fin=date(2027, 5, 28), activa=False),
            dict(id=12, nombre_zona="Porche", descripcion=None, fecha_inicio=None,
                 fecha_fin=None, activa=True),
        ],
        Profesor: [
            dict(id=21, nombre_completo="PRIMERO, Uno", email_corporativo="uno@epla.es",
                 horas_contrato=23.5, porcentaje_jornada=78.3, turno="mixto",
                 horas_manana=13.5, horas_tarde=10.0, tutor=True, activo=False,
                 fecha_inicio_guardias=date(2026, 10, 1), fecha_fin_guardias=date(2027, 5, 31),
                 guardias_voluntarias=4, zona_preferida_id=11, curso_id=7,
                 dias_semana_permitidos="[0, 2, 4]",
                 recreos_permitidos='{"0": [1], "2": [1, 2], "4": [2]}'),
            dict(id=22, nombre_completo="SEGUNDO, Dos", email_corporativo=None,
                 horas_contrato=30.0, porcentaje_jornada=100.0, turno="tarde",
                 horas_manana=None, horas_tarde=None, tutor=False, activo=True,
                 fecha_inicio_guardias=None, fecha_fin_guardias=None, guardias_voluntarias=0,
                 zona_preferida_id=None, curso_id=None, dias_semana_permitidos=None,
                 recreos_permitidos=None),
        ],
        Configuracion: [
            dict(id=1, anio_inicio_curso=2026, fecha_inicio_curso=date(2026, 9, 7),
                 fecha_fin_curso=date(2027, 6, 18), fecha_inicio_reparto_oficial=date(2026, 9, 21),
                 hora_recreo1_manana=time(10, 45), hora_recreo2_manana=time(12, 35),
                 hora_recreo1_tarde=time(16, 50), hora_recreo2_tarde=time(18, 40),
                 activar_festivos_automaticos=False,
                 dias_no_lectivos_personalizados='["2026-10-09", "2026-12-07"]',
                 recreos_config='[{"id": 1, "etiqueta": "R1", "turno": "manana"}]',
                 ajuste_tutores=0.8, ajuste_no_tutores=1.2, algoritmo_asignacion="v3.0",
                 curso_activo_id=7),
        ],
        Guardia: [
            dict(id=31, curso_id=7, profesor_id=21, fecha=date(2026, 10, 5), turno="tarde",
                 recreo=2, zona_id=11, es_sustitucion=True, profesor_sustituido_id=22,
                 notas="Cubre la baja"),
            dict(id=32, curso_id=None, profesor_id=22, fecha=date(2026, 10, 6), turno="mañana",
                 recreo=1, zona_id=12, es_sustitucion=False, profesor_sustituido_id=None,
                 notas=None),
        ],
        Ausencia: [
            dict(id=41, profesor_id=22, fecha_inicio=date(2026, 10, 5),
                 fecha_fin=date(2026, 10, 9), tipo="baja_medica", motivo="Gripe",
                 documento_path="justificantes/41.pdf", activa=False,
                 created_at=datetime(2026, 10, 4, 8, 15, 30),
                 updated_at=datetime(2026, 10, 4, 9, 0, 0)),
        ],
    }


def _sesion():
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def _claves_foraneas(conexion, _):
        conexion.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


@pytest.fixture
def origen():
    sesion = _sesion()
    for modelo, filas in _filas().items():
        for fila in filas:
            sesion.add(modelo(**fila))
    sesion.commit()
    yield sesion
    sesion.close()


@pytest.fixture
def destino():
    sesion = _sesion()
    yield sesion
    sesion.close()


def _volcado(sesion, sin=frozenset()):
    return {
        modelo.__tablename__: sorted(
            (
                {
                    c.name: getattr(fila, c.name)
                    for c in modelo.__table__.columns
                    if (modelo.__tablename__, c.name) not in sin
                }
                for fila in sesion.query(modelo).all()
            ),
            key=lambda f: f["id"],
        )
        for modelo in _filas()
    }


def test_las_filas_cubren_todas_las_columnas_y_tablas():
    filas = _filas()
    tablas = {m.__tablename__ for m in filas}
    assert tablas | TABLAS_LOCALES == set(Base.metadata.tables), (
        "Tabla nueva: añadirla a _filas() y a la sincronización, o a TABLAS_LOCALES"
    )
    for modelo, lista in filas.items():
        columnas = {c.name for c in modelo.__table__.columns}
        for fila in lista:
            assert set(fila) == columnas, f"{modelo.__tablename__}: {columnas ^ set(fila)}"


def test_sincronizacion_con_la_nube(origen, destino, tmp_path):
    from sync.data_exporter import DataExporter

    ruta = tmp_path / "guardias_patio_data.json"
    assert DataExporter.export_to_json(origen, ruta, clave=CLAVE)
    assert DataExporter.import_from_json(
        destino, ruta, clear_existing=True, clave=CLAVE
    )
    destino.expire_all()
    assert _volcado(destino, SOLO_EN_LOCAL) == _volcado(origen, SOLO_EN_LOCAL)


def test_la_descarga_sustituye_lo_que_habia(origen, destino, tmp_path):
    from sync.data_exporter import DataExporter

    ruta = tmp_path / "guardias_patio_data.json"
    assert DataExporter.export_to_json(origen, ruta, clave=CLAVE)
    for _ in range(2):
        assert DataExporter.import_from_json(destino, ruta, clear_existing=True, clave=CLAVE)
    destino.expire_all()
    assert _volcado(destino, SOLO_EN_LOCAL) == _volcado(origen, SOLO_EN_LOCAL)


def test_la_nube_no_lleva_datos_de_salud_en_claro(origen, tmp_path):
    from sync.data_exporter import DataExporter

    ruta = tmp_path / "guardias_patio_data.json"
    assert DataExporter.export_to_json(origen, ruta, clave=CLAVE)
    texto = ruta.read_text(encoding="utf-8")
    assert "Gripe" not in texto
    assert "justificantes/41.pdf" not in texto


def _copia_manual(origen, ruta, monkeypatch):
    from services.exportador import ExportadorDatos

    monkeypatch.setattr(ExportadorDatos, "exportar_usuarios", staticmethod(lambda: None))
    ExportadorDatos.exportar_todo(origen, ruta)


def test_copia_json_manual(origen, destino, tmp_path, monkeypatch):
    from services.exportador import ExportadorDatos

    ruta = tmp_path / "copia.json"
    _copia_manual(origen, ruta, monkeypatch)
    resultado = ExportadorDatos.importar_todo(destino, ruta)
    destino.expire_all()
    assert resultado["cursos_escolares"] == 2
    assert _volcado(destino) == _volcado(origen)


def test_copia_json_manual_sobre_datos_existentes(origen, destino, tmp_path, monkeypatch):
    from services.exportador import ExportadorDatos

    ruta = tmp_path / "copia.json"
    _copia_manual(origen, ruta, monkeypatch)
    ExportadorDatos.importar_todo(destino, ruta)
    ExportadorDatos.importar_todo(destino, ruta, limpiar=True)
    destino.expire_all()
    assert _volcado(destino) == _volcado(origen)


def test_copia_json_manual_antigua_sin_campos_nuevos(origen, destino, tmp_path, monkeypatch):
    from services.exportador import ExportadorDatos

    ruta = tmp_path / "copia.json"
    _copia_manual(origen, ruta, monkeypatch)
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    for curso in datos["cursos_escolares"]["cursos"]:
        for clave in ("id", "anio_inicio", "anio_fin", "fecha_inicio", "fecha_fin"):
            curso.pop(clave, None)
    ruta.write_text(json.dumps(datos), encoding="utf-8")

    resultado = ExportadorDatos.importar_todo(destino, ruta)
    assert resultado["profesores"] == 2
    assert resultado["guardias"] == 2


#: Claves que no traen los volcados subidos por versiones anteriores (la v15 de
#: la nube, 2026-09-06, no traía ninguna de estas).
CLAVES_NUEVAS = {
    "profesores": ("guardias_voluntarias", "zona_preferida_id", "curso_id"),
    "zonas": ("activa",),
    "configuracion": ("fecha_inicio_reparto_oficial", "curso_activo_id"),
    "guardias": ("es_sustitucion", "profesor_sustituido_id", "notas"),
}


def test_el_volcado_de_la_nube_de_una_version_anterior_carga(origen, destino, tmp_path):
    from sync.data_exporter import DataExporter

    ruta = tmp_path / "guardias_patio_data.json"
    assert DataExporter.export_to_json(origen, ruta, clave=CLAVE)
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    for tabla, claves in CLAVES_NUEVAS.items():
        for fila in datos[tabla]:
            for clave in claves:
                fila.pop(clave)
    ruta.write_text(json.dumps(datos), encoding="utf-8")

    assert DataExporter.import_from_json(destino, ruta, clear_existing=True, clave=CLAVE)
    destino.expire_all()
    volcado = _volcado(destino)
    esperado = {t: len(f) for t, f in _volcado(origen).items()}
    assert {t: len(f) for t, f in volcado.items()} == esperado
    profesor = destino.get(Profesor, 21)
    assert profesor.zona_preferida_id is None and profesor.guardias_voluntarias == 0
    assert destino.get(Zona, 11).activa is True
    assert destino.get(Guardia, 31).es_sustitucion is False


def test_una_referencia_huerfana_no_tumba_la_descarga(origen, destino, tmp_path):
    from sync.data_exporter import DataExporter

    ruta = tmp_path / "guardias_patio_data.json"
    assert DataExporter.export_to_json(origen, ruta, clave=CLAVE)
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    datos["profesores"][0].update(zona_preferida_id=999, curso_id=999)
    datos["configuracion"][0]["curso_activo_id"] = 999
    datos["guardias"][0]["profesor_sustituido_id"] = 999
    datos["cursos_escolares"][0]["created_at"] = "ilegible"
    ruta.write_text(json.dumps(datos), encoding="utf-8")

    assert DataExporter.import_from_json(destino, ruta, clear_existing=True, clave=CLAVE)
    profesor = destino.get(Profesor, 21)
    assert profesor.zona_preferida_id is None and profesor.curso_id is None
    assert destino.get(Configuracion, 1).curso_activo_id is None
    assert destino.get(Guardia, 31).profesor_sustituido_id is None
