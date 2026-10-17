"""Documento impreso de guardias: PDF individual (el que va en cada aviso) y PDF del mes.

Se lee lo que de verdad se escribe en el PDF interceptando el texto que ReportLab
manda a cada página (posición absoluta, cuerpo y fuente), sin depender de un lector
de PDF. Datos ficticios: «Profesor/a NN», zonas inventadas y octubre de 2026, con
los festivos automáticos del 9 y el 12.
"""

import re
import sys
from datetime import date, time

import pytest
from reportlab.lib.units import mm
from reportlab.pdfgen.textobject import PDFTextObject

from infrastructure.database.models import Configuracion, CursoEscolar, Guardia, Profesor, Zona
from services._pdf_individual_optimizado import exportar_profesor_individual_optimizado
from services._pdf_mes_consolidado import exportar_mes_consolidado
from services.pdf_styles import ajustar

MARGEN_SEGURO = 10 * mm  # lo que cualquier impresora deja sin imprimir, con holgura

ZONAS = [
    ("Patio central", "Bancos, fuente y soportales"),
    ("Pistas deportivas", "Pistas 1 a 3 y gradas"),
    ("Porche y cafetería", "Porche cubierto y acceso a cafetería"),
    ("Entrada principal", "Verja, aparcamiento de bicis y conserjería"),
    ("Jardín norte", None),
    ("Huerto escolar", None),
    ("Biblioteca", "Sala de lectura"),
]

# Destinatario: dos guardias el 15, la de tarde con recreo 1 y la de mañana con recreo 2
GUARDIAS_P01 = [
    (date(2026, 10, 2), "mañana", 1, 0),
    (date(2026, 10, 7), "mañana", 2, 1),
    (date(2026, 10, 15), "tarde", 1, 2),
    (date(2026, 10, 15), "mañana", 2, 2),
    (date(2026, 10, 21), "mañana", 1, 3),
    (date(2026, 10, 27), "tarde", 2, 4),
    (date(2026, 10, 30), "mañana", 1, 0),
]


@pytest.fixture
def texto_pdf(monkeypatch):
    """Cada trozo de texto escrito: página, x e y absolutas, ancho y tamaño de página."""
    registros = []
    original = PDFTextObject._formatText

    def espia(self, text):
        canv = self._canvas
        y_linea = self._y
        if sys._getframe(1).f_code.co_name == "textLine":  # ya bajó el cursor una línea
            y_linea += self._leading
        x, y = canv.absolutePosition(self._x, y_linea)
        registros.append({
            "texto": str(text),
            "x": x,
            "y": y,
            "ancho": canv.stringWidth(str(text), self._fontname, self._fontsize),
            "pagina": canv.getPageNumber(),
            "tam_pagina": tuple(canv._pagesize),
        })
        return original(self, text)

    monkeypatch.setattr(PDFTextObject, "_formatText", espia)
    return registros


def _claustro(session, n_zonas=5):
    curso = CursoEscolar(anio_inicio=2026, anio_fin=2027, fecha_inicio=date(2026, 9, 1),
                         fecha_fin=date(2027, 6, 30), nombre="Curso 2026/2027", activo=True)
    session.add(curso)
    session.flush()
    session.add(Configuracion(
        anio_inicio_curso=2026, fecha_inicio_curso=date(2026, 9, 1),
        fecha_fin_curso=date(2027, 6, 30),
        hora_recreo1_manana=time(10, 30), hora_recreo2_manana=time(12, 20),
        hora_recreo1_tarde=time(16, 50), hora_recreo2_tarde=time(18, 40),
        activar_festivos_automaticos=True, curso_activo_id=curso.id,
    ))
    zonas = [Zona(nombre_zona=n, descripcion=d) for n, d in ZONAS[:n_zonas]]
    session.add_all(zonas)
    profes = [
        Profesor(nombre_completo=f"Profesor/a {i:02d}", email_corporativo=f"p{i:02d}@example.com",
                 horas_contrato=25, porcentaje_jornada=100, turno="completo", tutor=i == 1,
                 activo=True, curso_id=curso.id)
        for i in range(1, 9)
    ]
    session.add_all(profes)
    session.flush()
    for f, turno, recreo, z in GUARDIAS_P01:
        session.add(Guardia(curso_id=curso.id, profesor_id=profes[0].id, fecha=f, turno=turno,
                            recreo=recreo, zona_id=zonas[z].id))
    # Otro día con guardias de varias personas, para el PDF del mes
    for k, z in enumerate(zonas):
        session.add(Guardia(curso_id=curso.id, profesor_id=profes[1 + k % 7].id,
                            fecha=date(2026, 10, 8), turno="mañana", recreo=1, zona_id=z.id))
    session.flush()
    return curso, profes, zonas


def _texto(registros, desde=None):
    textos = [r["texto"] for r in registros]
    if desde is not None:
        textos = textos[textos.index(desde) + 1:]
    return textos


def _paginas(registros):
    pies = [r["texto"] for r in registros if r["texto"].startswith("Página ")]
    totales = {int(re.search(r"de (\d+)", p).group(1)) for p in pies}
    assert len(totales) == 1
    return totales.pop()


def _dentro_de_margenes(registros):
    fuera = []
    for r in registros:
        ancho, alto = r["tam_pagina"]
        if not (MARGEN_SEGURO <= r["x"] and r["x"] + r["ancho"] <= ancho - MARGEN_SEGURO + 0.5
                and MARGEN_SEGURO <= r["y"] <= alto - MARGEN_SEGURO):
            fuera.append(r)
    return fuera


def _individual(session, profesor, ruta):
    return exportar_profesor_individual_optimizado(
        session, profesor.id, date(2026, 9, 1), date(2027, 6, 30), str(ruta)
    )


class TestPdfIndividual:
    def test_un_mes_cabe_en_una_pagina_a4_vertical(self, session, tmp_path, texto_pdf):
        _, profes, _ = _claustro(session)
        assert _individual(session, profes[0], tmp_path / "p.pdf")
        assert _paginas(texto_pdf) == 1
        ancho, alto = texto_pdf[0]["tam_pagina"]
        assert (round(ancho), round(alto)) == (595, 842)
        datos = (tmp_path / "p.pdf").read_bytes()
        assert b"/Author (EPLA \\267 Guardias de patio)" in datos  # «·» en PDFDocEncoding

    def test_destinatario_resaltado_y_resumen(self, session, tmp_path, texto_pdf):
        _, profes, _ = _claustro(session)
        _individual(session, profes[0], tmp_path / "p.pdf")
        textos = _texto(texto_pdf)
        assert "PROFESOR/A 01" in textos  # nombre en la ficha
        assert "GUARDIAS" in textos and "7" in textos and "en 6 días" in textos
        assert any("5 de mañana · 2 de tarde" in t for t in textos)

    def test_festivos_marcados_en_el_calendario(self, session, tmp_path, texto_pdf):
        _, profes, _ = _claustro(session)
        _individual(session, profes[0], tmp_path / "p.pdf")
        assert _texto(texto_pdf).count("No lectivo") == 2  # 9 y 12 de octubre de 2026
        assert "Festivo o no lectivo" in _texto(texto_pdf)  # y explicados en la leyenda

    def test_mismo_contenido_que_antes(self, session, tmp_path, texto_pdf):
        """Cada guardia sigue con su fecha, día, turno, recreo y hora, zona y descripción."""
        _, profes, zonas = _claustro(session)
        _individual(session, profes[0], tmp_path / "p.pdf")
        detalle = _texto(texto_pdf, desde="Detalle de las guardias")
        unido = " ".join(detalle)
        horas = {("mañana", 1): "10:30", ("mañana", 2): "12:20", ("tarde", 1): "16:50",
                 ("tarde", 2): "18:40"}
        for f, turno, recreo, z in GUARDIAS_P01:
            assert f.strftime("%d/%m/%Y") in detalle
            assert turno.capitalize() in detalle
            assert f"Recreo {recreo} · " in detalle
            assert horas[(turno, recreo)] in detalle
            assert zonas[z].nombre_zona in unido
            if zonas[z].descripcion:
                assert zonas[z].descripcion in unido
        assert sum(1 for t in detalle if t.startswith("Recreo ")) == len(GUARDIAS_P01)
        assert {t for t in detalle if re.fullmatch(r"\d\d/\d\d/2026", t)} == {
            f.strftime("%d/%m/%Y") for f, *_ in GUARDIAS_P01
        }

    def test_dentro_del_dia_por_hora_del_recreo(self, session, tmp_path, texto_pdf):
        _, profes, _ = _claustro(session)
        _individual(session, profes[0], tmp_path / "p.pdf")
        detalle = _texto(texto_pdf, desde="Detalle de las guardias")
        tras_el_15 = detalle[detalle.index("15/10/2026"):]
        # La de mañana (recreo 2, 12:20) antes que la de tarde (recreo 1, 16:50)
        assert tras_el_15.index("12:20") < tras_el_15.index("16:50")

    def test_nada_fuera_de_margenes(self, session, tmp_path, texto_pdf):
        _, profes, _ = _claustro(session)
        _individual(session, profes[0], tmp_path / "p.pdf")
        assert texto_pdf
        assert _dentro_de_margenes(texto_pdf) == []

    def test_nombre_largo_sin_cortar(self, session, tmp_path, texto_pdf):
        _, profes, _ = _claustro(session)
        profes[0].nombre_completo = "Apellidoprimero Apellidosegundo Bastante Largo, Profesor/a 01"
        session.flush()
        _individual(session, profes[0], tmp_path / "p.pdf")
        ficha = " ".join(t for t in _texto(texto_pdf) if t.isupper())
        assert "APELLIDOPRIMERO APELLIDOSEGUNDO BASTANTE LARGO, PROFESOR/A 01" in ficha
        assert _dentro_de_margenes(texto_pdf) == []

    def test_varios_meses_en_rejilla_con_codigos(self, session, tmp_path, texto_pdf):
        curso, profes, zonas = _claustro(session)
        for mes in (11, 12):
            session.add(Guardia(curso_id=curso.id, profesor_id=profes[0].id,
                                fecha=date(2026, mes, 3), turno="tarde", recreo=2,
                                zona_id=zonas[1].id))
        session.flush()
        _individual(session, profes[0], tmp_path / "p.pdf")
        textos = _texto(texto_pdf)
        assert {"Octubre 2026", "Noviembre 2026", "Diciembre 2026"} <= set(textos)
        # Turno y recreo dentro del turno, y la abreviatura real de la zona
        # («Pistas deportivas» → «PD»), explicados en la leyenda
        assert "T2·PD" in textos
        assert "ZONAS" in textos
        assert _dentro_de_margenes(texto_pdf) == []


class TestPdfDelMes:
    def test_mismo_contenido_que_antes(self, session, tmp_path, texto_pdf):
        """Todas las guardias del mes, cada una con su día, recreo, persona y zona."""
        _, _, zonas = _claustro(session)
        assert exportar_mes_consolidado(session, 10, 2026, str(tmp_path / "m.pdf"))
        guardias = session.query(Guardia).all()
        textos = _texto(texto_pdf)
        assert f"{len(guardias)}" in textos and "guardias" in textos
        dia_a_dia = _texto(texto_pdf, desde="Guardias día a día")
        nombres = [t.removeprefix("• ") for t in dia_a_dia if "Profesor/a" in t]
        assert len(nombres) == len(guardias)
        for g in guardias:
            assert g.profesor.nombre_completo in nombres
        for z in zonas:
            assert z.nombre_zona in dia_a_dia
        assert "Jueves 8 de octubre" in dia_a_dia and "Jueves 15 de octubre" in dia_a_dia
        assert "Mañana · R1 · " in dia_a_dia and "16:50" in dia_a_dia

    def test_festivos_en_el_calendario_y_en_el_dia_a_dia(self, session, tmp_path, texto_pdf):
        _claustro(session)
        exportar_mes_consolidado(session, 10, 2026, str(tmp_path / "m.pdf"))
        textos = _texto(texto_pdf)
        assert textos.count("No lectivo") == 2
        assert "Viernes 9 de octubre · festivo o no lectivo" in textos
        assert "Lunes 12 de octubre · festivo o no lectivo" in textos

    def test_vertical_hasta_seis_zonas(self, session, tmp_path, texto_pdf):
        _claustro(session, n_zonas=5)
        exportar_mes_consolidado(session, 10, 2026, str(tmp_path / "m.pdf"))
        ancho, alto = texto_pdf[0]["tam_pagina"]
        assert ancho < alto
        assert _dentro_de_margenes(texto_pdf) == []

    def test_apaisado_con_mas_de_seis_zonas(self, session, tmp_path, texto_pdf):
        _claustro(session, n_zonas=7)
        exportar_mes_consolidado(session, 10, 2026, str(tmp_path / "m.pdf"))
        ancho, alto = texto_pdf[0]["tam_pagina"]
        assert (round(ancho), round(alto)) == (842, 595)
        assert {"Huerto escolar", "Biblioteca"} <= set(_texto(texto_pdf))
        assert _dentro_de_margenes(texto_pdf) == []


class TestAjustar:
    @pytest.mark.parametrize("texto", [
        "Porche cubierto y acceso a cafetería",
        "Apellidoprimero Apellidosegundo Bastante Largo, Profesor/a 01",
        "Gimnasio cubierto y vestuarios del pabellón deportivo",
    ])
    def test_nunca_mas_ancho_que_el_hueco(self, texto):
        from reportlab.pdfbase.pdfmetrics import stringWidth

        from services.pdf_styles import Papel

        for ancho in (15 * mm, 25 * mm, 60 * mm):
            for lineas in (1, 2):
                partes, tam = ajustar(texto, Papel.TEXTO, 9, 4.5, ancho, lineas)
                assert len(partes) <= lineas
                assert all(stringWidth(p, Papel.TEXTO, tam) <= ancho + 0.01 for p in partes)


# --- Recreos de tarde y zonas con nombre corto (2026-10-17) -----------------------

RECREOS_DE_AJUSTES = [
    {"id": 1, "etiqueta": "Recreo 1 Mañana", "turno": "mañana", "hora": "10:30"},
    {"id": 2, "etiqueta": "Recreo 2 Mañana", "turno": "mañana", "hora": "12:20"},
    {"id": 3, "etiqueta": "Recreo 1 Tarde", "turno": "tarde", "hora": "16:30"},
    {"id": 4, "etiqueta": "Recreo 2 Tarde", "turno": "tarde", "hora": "18:30"},
]


def _centro_de_tarde(session, meses=(10,)):
    """Zonas «Z2» y «Z3», recreos de Ajustes (3 y 4 de tarde) y un profesor de tarde."""
    import json

    curso = CursoEscolar(anio_inicio=2026, anio_fin=2027, fecha_inicio=date(2026, 9, 1),
                         fecha_fin=date(2027, 6, 30), nombre="Curso 2026/2027", activo=True)
    session.add(curso)
    session.flush()
    session.add(Configuracion(
        anio_inicio_curso=2026, fecha_inicio_curso=date(2026, 9, 1),
        fecha_fin_curso=date(2027, 6, 30),
        hora_recreo1_manana=time(10, 30), hora_recreo2_manana=time(12, 20),
        hora_recreo1_tarde=time(16, 30), hora_recreo2_tarde=time(18, 30),
        recreos_config=json.dumps(RECREOS_DE_AJUSTES),
        activar_festivos_automaticos=True, curso_activo_id=curso.id,
    ))
    zonas = [Zona(nombre_zona="Z2", descripcion="Patio delantero"),
             Zona(nombre_zona="Z3", descripcion="Pistas del fondo")]
    profe = Profesor(nombre_completo="Profesor/a Tarde", email_corporativo="t@example.com",
                     horas_contrato=25, porcentaje_jornada=100, turno="tarde", tutor=False,
                     activo=True, curso_id=curso.id)
    session.add_all(zonas + [profe])
    session.flush()
    for mes in meses:
        session.add_all([
            Guardia(curso_id=curso.id, profesor_id=profe.id, fecha=date(2026, mes, 6),
                    turno="tarde", recreo=3, zona_id=zonas[0].id),
            Guardia(curso_id=curso.id, profesor_id=profe.id, fecha=date(2026, mes, 14),
                    turno="tarde", recreo=4, zona_id=zonas[1].id),
        ])
    session.flush()
    return profe


class TestRecreoDeTardeYZonas:
    def test_la_guardia_de_tarde_sale_con_su_numero_y_su_hora(self, session, tmp_path,
                                                               texto_pdf):
        profe = _centro_de_tarde(session)
        _individual(session, profe, tmp_path / "p.pdf")
        textos = _texto(texto_pdf)
        todo = " ".join(textos)

        assert "R1 · 16:30" in textos and "R2 · 18:30" in textos  # calendario
        assert "Recreo 1 ·" in todo and "Recreo 2 ·" in todo      # tabla
        assert "Recreo 3" not in todo and "Recreo 4" not in todo
        assert "R3" not in todo and "T3" not in todo
        # La leyenda dice lo mismo que se pinta
        assert "R1 16:30" in todo and "R2 18:30" in todo

    def test_una_zona_z2_no_sale_como_z1_z2(self, session, tmp_path, texto_pdf):
        profe = _centro_de_tarde(session, meses=(10, 11, 12))
        _individual(session, profe, tmp_path / "p.pdf")
        textos = _texto(texto_pdf)
        todo = " ".join(textos)

        assert "T1·Z2" in textos and "T2·Z3" in textos   # calendario compacto
        assert "Z1" not in todo
        assert not re.search(r"Z\d\s*·\s*Z\d", todo)
        # Tabla: «nombre — descripción»; leyenda: cada zona una vez
        assert textos.count("Z2") >= 1
        assert todo.count("Patio delantero") >= 1
        assert "En el calendario," in todo and "T2" in todo

    def test_pdf_del_mes_con_la_tarde_numerada_y_con_hora(self, session, tmp_path, texto_pdf):
        _centro_de_tarde(session)
        assert exportar_mes_consolidado(session, 10, 2026, str(tmp_path / "m.pdf"))
        todo = " ".join(_texto(texto_pdf))

        assert "Tarde · R1" in todo and "Tarde · R2" in todo
        assert "16:30" in todo and "18:30" in todo
        assert "R3" not in todo and "R4" not in todo
