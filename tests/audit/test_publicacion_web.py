"""FUN-009 — que cada profesor pueda consultar sus guardias desde el navegador.

Decisión de producto de CarlosFB (2026-09-06): páginas estáticas subidas al
hosting del centro, con una dirección propia por profesor. No hay servidor, ni
base de datos compartida, ni contraseñas: eso era la otra opción (lote 17) y
supone migrar de una base SQLite por usuario a un servidor de verdad.

Lo que aquí se fija es que la dirección de cada uno sea estable —si cambiara,
las suscripciones al calendario se romperían cada vez que se publica— y que no
haya ninguna página que las liste todas.
"""

import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from infrastructure.database.models import Base, Configuracion, Guardia, Profesor, Zona
from services import publicador_web

LUNES = datetime.date(2025, 10, 6)


@pytest.fixture
def sesion(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'guardias_patio.db'}")
    Base.metadata.create_all(engine)
    s = sessionmaker(bind=engine)()
    s.add(
        Configuracion(
            anio_inicio_curso=2025,
            fecha_inicio_curso=datetime.date(2025, 9, 1),
            fecha_fin_curso=datetime.date(2026, 6, 30),
            hora_recreo1_manana=datetime.time(11, 0),
            hora_recreo2_manana=datetime.time(12, 0),
        )
    )
    s.add(Zona(nombre_zona="Patio A", activa=True))
    s.add_all(
        [
            Profesor(
                nombre_completo="García, Ana",
                email_corporativo="ana@epla.es",
                horas_contrato=25.0,
                porcentaje_jornada=100.0,
                turno="mañana",
                tutor=False,
                activo=True,
            ),
            Profesor(
                nombre_completo="Sin Guardias, Luis",
                horas_contrato=25.0,
                porcentaje_jornada=100.0,
                turno="mañana",
                tutor=False,
                activo=True,
            ),
        ]
    )
    s.commit()
    ana = s.query(Profesor).filter_by(email_corporativo="ana@epla.es").one()
    zona = s.query(Zona).first()
    s.add(
        Guardia(
            profesor_id=ana.id, fecha=LUNES, turno="mañana", recreo=1, zona_id=zona.id
        )
    )
    s.commit()
    yield s
    s.close()
    engine.dispose()


def test_se_publica_una_pagina_por_profesor_con_guardias(sesion, tmp_path):
    resumen = publicador_web.publicar(sesion, tmp_path / "web")

    assert resumen["publicados"] == 1
    assert resumen["sin_guardias"] == 1
    assert len(list((tmp_path / "web").glob("*.html"))) == 1


def test_cada_pagina_lleva_su_calendario_suscribible(sesion, tmp_path):
    publicador_web.publicar(sesion, tmp_path / "web")

    assert len(list((tmp_path / "web").glob("*.ics"))) == 1


def test_la_direccion_no_cambia_al_republicar(sesion, tmp_path):
    """Si cambiara, quien se hubiera suscrito al calendario lo perdería."""
    primera = publicador_web.publicar(sesion, tmp_path / "web")["enlaces"][0][2]
    segunda = publicador_web.publicar(sesion, tmp_path / "web")["enlaces"][0][2]

    assert primera == segunda


def test_la_direccion_no_se_puede_adivinar(sesion, tmp_path):
    resumen = publicador_web.publicar(sesion, tmp_path / "web")
    fichero = resumen["enlaces"][0][2]

    identificador = fichero.removesuffix(".html")
    assert len(identificador) == publicador_web.LARGO_DEL_ENLACE
    # Saber el número de profesor no basta: sin la clave del centro no sale.
    assert publicador_web.enlace_de(1, b"otra clave") != identificador
    assert "garcia" not in identificador.lower()


def test_dos_profesores_no_comparten_direccion(sesion, tmp_path):
    clave = publicador_web.clave_de_publicacion(sesion)

    assert publicador_web.enlace_de(1, clave) != publicador_web.enlace_de(2, clave)


def test_no_se_escribe_ninguna_pagina_que_liste_a_todos(sesion, tmp_path):
    """Un índice con todas las direcciones anularía el motivo de que sean secretas."""
    publicador_web.publicar(sesion, tmp_path / "web")

    nombres = {f.name for f in (tmp_path / "web").iterdir()}
    assert "index.html" not in nombres
    assert "indice.html" not in nombres


def test_la_pagina_pide_a_los_buscadores_que_no_la_indexen(sesion, tmp_path):
    publicador_web.publicar(sesion, tmp_path / "web")
    pagina = next((tmp_path / "web").glob("*.html")).read_text(encoding="utf-8")

    assert 'name="robots"' in pagina
    assert "noindex" in pagina


def test_la_pagina_muestra_los_datos_de_la_guardia(sesion, tmp_path):
    publicador_web.publicar(sesion, tmp_path / "web")
    pagina = next((tmp_path / "web").glob("*.html")).read_text(encoding="utf-8")

    assert "García, Ana" in pagina
    assert "Patio A" in pagina
    assert "lunes 6 de octubre" in pagina


def test_el_nombre_va_escapado(sesion, tmp_path):
    profesor = sesion.query(Profesor).filter_by(email_corporativo="ana@epla.es").one()
    profesor.nombre_completo = "<script>alerta</script>"
    sesion.commit()

    publicador_web.publicar(sesion, tmp_path / "web")
    pagina = next((tmp_path / "web").glob("*.html")).read_text(encoding="utf-8")

    assert "<script>alerta" not in pagina


def test_la_lista_de_enlaces_sirve_para_avisar_a_cada_uno(sesion, tmp_path):
    resumen = publicador_web.publicar(sesion, tmp_path / "web")

    nombre, correo, fichero = resumen["enlaces"][0]
    assert nombre == "García, Ana"
    assert correo == "ana@epla.es"
    assert fichero.endswith(".html")


def test_sin_clave_estable_no_se_publica(session, tmp_path):
    """En memoria no hay dónde guardarla: publicar daría direcciones distintas cada vez."""
    with pytest.raises(ValueError, match="clave estable"):
        publicador_web.publicar(session, tmp_path / "web")


def test_la_clave_solo_la_lee_su_dueno(sesion, tmp_path):
    import stat

    publicador_web.clave_de_publicacion(sesion)
    ruta = tmp_path / publicador_web.NOMBRE_DE_LA_CLAVE

    assert ruta.exists()
    assert stat.S_IMODE(ruta.stat().st_mode) & 0o077 == 0


def test_la_vista_de_informes_ofrece_publicar():
    import inspect

    from presentation.forms.reportes_form import ReportesForm

    from presentation.forms.reportes_widgets.publicacion_web import publicar_desde

    assert "_publicar_en_la_web" in inspect.getsource(ReportesForm)
    assert "publicador_web.publicar" in inspect.getsource(publicar_desde)


def test_publicar_no_deja_la_ventana_con_un_error_sin_explicar():
    """Un disco lleno o una carpeta sin permisos tienen que decirse, no reventar."""
    import inspect

    from presentation.forms.reportes_form import ReportesForm

    from presentation.forms.reportes_widgets.publicacion_web import publicar_desde

    fuente = inspect.getsource(publicar_desde)
    assert "except (OSError, ValueError)" in fuente
    assert "mostrar_error" in fuente
