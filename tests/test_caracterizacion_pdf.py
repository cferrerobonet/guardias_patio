"""Caracterización de los PDF impresos: fija byte a byte lo que se genera hoy.

Con ReportLab en modo invariante y el reloj del pie fijo, el mismo contenido da el
mismo fichero. Sirve de red para partir las funciones que los construyen sin cambiar
nada del documento. Si un cambio en el PDF es intencionado, las huellas se recalculan
a propósito. Datos ficticios: «Profesor/a NN», zonas inventadas y el curso 2026/2027.
"""

import hashlib
import json
from datetime import date, datetime, time

import pytest
from reportlab import rl_config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from infrastructure.database.models import (
    Base,
    Configuracion,
    CursoEscolar,
    Guardia,
    Profesor,
    Zona,
)

RECREOS_DE_AJUSTES = json.dumps([
    {"id": 1, "etiqueta": "Recreo 1 Mañana", "turno": "mañana", "hora": "10:30"},
    {"id": 2, "etiqueta": "Recreo 2 Mañana", "turno": "mañana", "hora": "12:20"},
    {"id": 3, "etiqueta": "Recreo 1 Tarde", "turno": "tarde", "hora": "16:30"},
    {"id": 4, "etiqueta": "Recreo 2 Tarde", "turno": "tarde", "hora": "18:30"},
])
ZONAS = [
    ("Patio central", "Bancos y fuente"),
    ("Pistas deportivas", "Pistas 1 a 3"),
    ("Porche", None),
    ("Entrada principal", "Verja y conserjería"),
    ("Jardín norte", None),
    ("Huerto escolar", None),
    ("Biblioteca", "Sala de lectura"),
]


class _Reloj(datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 10, 20, 9, 30)


@pytest.fixture
def sesion():
    motor = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(motor)
    s = sessionmaker(bind=motor)()
    yield s
    s.close()
    motor.dispose()


@pytest.fixture
def invariante(monkeypatch):
    import services._pdf_individual_optimizado as individual
    import services._pdf_mes_consolidado as mes

    monkeypatch.setattr(rl_config, "invariant", 1)
    monkeypatch.setattr(individual, "datetime", _Reloj)
    monkeypatch.setattr(mes, "datetime", _Reloj)


def _centro(sesion, n_zonas=5, recreos=None, curso_activo=True):
    curso = CursoEscolar(anio_inicio=2026, anio_fin=2027, fecha_inicio=date(2026, 9, 1),
                         fecha_fin=date(2027, 6, 30), nombre="Curso 2026/2027",
                         activo=curso_activo)
    sesion.add(curso)
    sesion.flush()
    sesion.add(Configuracion(
        anio_inicio_curso=2026, fecha_inicio_curso=date(2026, 9, 1),
        fecha_fin_curso=date(2027, 6, 30),
        hora_recreo1_manana=time(10, 30), hora_recreo2_manana=time(12, 20),
        hora_recreo1_tarde=time(16, 50), hora_recreo2_tarde=time(18, 40),
        recreos_config=recreos, activar_festivos_automaticos=True, curso_activo_id=curso.id,
    ))
    zonas = [Zona(nombre_zona=n, descripcion=d) for n, d in ZONAS[:n_zonas]]
    sesion.add_all(zonas)
    profes = [
        Profesor(nombre_completo=f"Profesor/a {i:02d}", email_corporativo=f"p{i:02d}@example.com",
                 horas_contrato=25, porcentaje_jornada=100,
                 turno=("mañana", "tarde", "completo")[i % 3], tutor=i == 1, activo=True,
                 curso_id=curso.id)
        for i in range(1, 9)
    ]
    sesion.add_all(profes)
    sesion.flush()
    return curso, profes, zonas


def _guardia(sesion, curso, profe, f, turno, recreo, zona):
    sesion.add(Guardia(curso_id=curso.id, profesor_id=profe.id if profe else None, fecha=f,
                       turno=turno, recreo=recreo, zona_id=zona.id if zona else None))


def _guardias_de_un_mes(sesion, curso, profes, zonas, mes=10):
    filas = [
        (0, 2, "mañana", 1, 0), (0, 7, "mañana", 2, 1), (0, 15, "tarde", 1, 2),
        (0, 15, "mañana", 2, 2), (0, 21, "mañana", 1, 3), (0, 27, "tarde", 2, 4),
        (0, 30, "mañana", 1, 0),
    ]
    for p, dia, turno, recreo, z in filas:
        _guardia(sesion, curso, profes[p], date(2026, mes, dia), turno, recreo,
                 zonas[z % len(zonas)])


def _huella(ruta) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


# --------------------------------------------------------------------- individual
def _individual(sesion, profe_id, ruta, mensajes=None):
    from services._pdf_individual_optimizado import exportar_profesor_individual_optimizado

    callback = (lambda pct, msg: mensajes.append((pct, msg))) if mensajes is not None else None
    return exportar_profesor_individual_optimizado(
        sesion, profe_id, date(2026, 9, 1), date(2027, 6, 30), str(ruta), callback
    )


HUELLAS_INDIVIDUAL = {
    "un_mes": ("e25a99dc08ba673f7c0684d4d56a25b9a20320405ef975c7b01a103feca9a728", 7),
    "tres_meses": ("a168260dc1f2e9b33002ee0bb64c7f6b4e2f4ebc4c17acde555cba5917a9bd7b", 11),
    "cinco_meses": ("395b96bf63e2a5158028a17d861bc323c309ef6b859e0085e92b5b866ac46e66", 15),
    "tarde_ajustes": ("253f87efdcf8f12fdebd15365904c823896e5ffc755171855f480cd95a9da3ed", 9),
}


@pytest.mark.parametrize("caso", ["un_mes", "tres_meses", "cinco_meses", "tarde_ajustes"])
def test_pdf_individual_igual_byte_a_byte(sesion, tmp_path, invariante, caso):
    recreos = RECREOS_DE_AJUSTES if caso == "tarde_ajustes" else None
    curso, profes, zonas = _centro(sesion, recreos=recreos)
    _guardias_de_un_mes(sesion, curso, profes, zonas)
    meses = {"un_mes": [], "tres_meses": [11, 12], "cinco_meses": [11, 12, 1, 2],
             "tarde_ajustes": [11]}[caso]
    for k, m in enumerate(meses):
        anio = 2026 if m >= 9 else 2027
        _guardia(sesion, curso, profes[0], date(anio, m, 3 + k), "tarde", 4 if recreos else 2,
                 zonas[1])
        _guardia(sesion, curso, profes[0], date(anio, m, 10 + k), "mañana", 1, zonas[k % 5])
    sesion.flush()
    mensajes = []
    assert _individual(sesion, profes[0].id, tmp_path / "p.pdf", mensajes)
    huella, n_guardias = HUELLAS_INDIVIDUAL[caso]
    assert _huella(tmp_path / "p.pdf") == huella
    assert mensajes == [
        (0, "Preparando exportación individual..."),
        (10, "Consultando guardias de Profesor/a 01..."),
        (30, f"Encontradas {n_guardias} guardias..."),
        (40, "Generando calendarios..."),
        (60, "Generando tabla de guardias..."),
        (90, "Construyendo PDF..."),
        (100, "PDF generado exitosamente"),
    ]


def test_pdf_individual_sin_datos(sesion, tmp_path, invariante):
    mensajes = []
    curso, profes, zonas = _centro(sesion, curso_activo=False)
    assert not _individual(sesion, profes[0].id, tmp_path / "a.pdf", mensajes)
    curso.activo = True
    sesion.flush()
    assert not _individual(sesion, 999, tmp_path / "b.pdf", mensajes)
    assert not _individual(sesion, profes[1].id, tmp_path / "c.pdf", mensajes)
    assert not any(p.exists() for p in tmp_path.iterdir())
    assert mensajes == [
        (0, "Preparando exportación individual..."),
        (0, "Preparando exportación individual..."),
        (0, "Preparando exportación individual..."),
        (10, "Consultando guardias de Profesor/a 02..."),
        (100, "No hay guardias en este periodo"),
    ]


def test_pdf_individual_error_al_escribir(sesion, tmp_path, invariante):
    curso, profes, zonas = _centro(sesion)
    _guardias_de_un_mes(sesion, curso, profes, zonas)
    sesion.flush()
    mensajes = []
    assert not _individual(sesion, profes[0].id, tmp_path / "no" / "existe.pdf", mensajes)
    assert mensajes[-1][0] == 0 and mensajes[-1][1].startswith("Error: ")
    assert [m for m in mensajes[:-1]] == [
        (0, "Preparando exportación individual..."),
        (10, "Consultando guardias de Profesor/a 01..."),
        (30, "Encontradas 7 guardias..."),
        (40, "Generando calendarios..."),
        (60, "Generando tabla de guardias..."),
        (90, "Construyendo PDF..."),
    ]
