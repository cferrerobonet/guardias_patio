"""GUA-CON-002: avisos de guardias con plantilla editable y PDF individual e iCal adjuntos.

Ningún test habla con un servidor de correo: `smtplib.SMTP` se sustituye por un
servidor falso que guarda los mensajes (y la barrera `sin_smtp_de_verdad` impide
lo demás).
"""

import datetime
import smtplib
from datetime import time

import pytest

from infrastructure.database.models import Configuracion, CursoEscolar, Guardia, Profesor, Zona
from services import notificador_guardias, plantilla_avisos
from services.plantilla_avisos import Plantilla

LUNES = datetime.date(2026, 9, 7)


class _Servicio:
    smtp_server = "smtp.example.com"
    smtp_port = 587
    smtp_user = "avisos@example.com"
    smtp_password = "x"
    from_name = "Guardias de Patio"
    from_email = "avisos@example.com"


class _Servidor:
    mensajes: list = []

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def starttls(self):
        pass

    def login(self, *a):
        pass

    def send_message(self, mensaje):
        type(self).mensajes.append(mensaje)


@pytest.fixture
def servidor(monkeypatch):
    _Servidor.mensajes = []
    monkeypatch.setattr(smtplib, "SMTP", _Servidor)
    return _Servidor


@pytest.fixture
def claustro(session):
    session.add(CursoEscolar(anio_inicio=2026, anio_fin=2027, fecha_inicio=LUNES,
                             fecha_fin=datetime.date(2027, 6, 30), nombre="Curso 2026/2027",
                             activo=True, cerrado=False))
    session.add(Configuracion(
        anio_inicio_curso=2026, fecha_inicio_curso=LUNES, fecha_fin_curso=datetime.date(2026, 10, 2),
        hora_recreo1_manana=time(10, 45), hora_recreo2_manana=time(12, 35),
        activar_festivos_automaticos=False,
    ))
    zona = Zona(nombre_zona="Patio A", activa=True)
    session.add(zona)
    for nombre, correo in (("Prueba, Ana", "ana@example.com"), ("Prueba, Berta", "berta@example.com")):
        session.add(Profesor(nombre_completo=nombre, email_corporativo=correo, horas_contrato=25,
                             porcentaje_jornada=100, turno="mañana", activo=True))
    session.commit()
    curso = session.query(CursoEscolar).one()
    for i, profesor in enumerate(session.query(Profesor).order_by(Profesor.id)):
        session.add(Guardia(profesor_id=profesor.id, fecha=LUNES + datetime.timedelta(days=i),
                            turno="mañana", recreo=1, zona_id=zona.id, curso_id=curso.id))
    session.commit()
    return session


# --- La plantilla -----------------------------------------------------------


def test_la_de_serie_dice_lo_mismo_que_antes(claustro):
    envio = notificador_guardias.preparar_envios(claustro, "Octubre 2026", Plantilla()).envios[0]

    assert envio.asunto == "Guardias de patio — Octubre 2026"
    assert "<strong>Prueba, Ana</strong>" in envio.html
    assert "Patio A" in envio.html and "Patio A" in envio.texto


def test_la_plantilla_editada_se_usa_y_se_recuerda(claustro):
    plantilla_avisos.guardar(Plantilla(
        asunto="Tus {num_guardias} guardias de {periodo}",
        cuerpo="Hola {nombre}:\n\nEstas son:\n{tabla}\nUn saludo, Jefatura",
    ))

    envio = notificador_guardias.preparar_envios(claustro, "Octubre 2026").envios[0]

    assert envio.asunto == "Tus 1 guardias de Octubre 2026"
    assert envio.texto.startswith("Hola Prueba, Ana:")
    assert "Un saludo, Jefatura" in envio.html
    assert envio.html.index("Patio A") < envio.html.index("Un saludo")


def test_lo_escrito_en_la_plantilla_va_escapado(claustro):
    plantilla = Plantilla(cuerpo="<script>x</script> {nombre}")
    envio = notificador_guardias.preparar_envios(claustro, "Octubre 2026", plantilla).envios[0]
    assert "<script>" not in envio.html
    assert "&lt;script&gt;" in envio.html


def test_sin_marcador_de_tabla_la_lista_va_al_final(claustro):
    envio = notificador_guardias.preparar_envios(
        claustro, "Octubre 2026", Plantilla(cuerpo="Hola {nombre}")
    ).envios[0]
    assert envio.html.index("Hola") < envio.html.index("Patio A")
    assert envio.texto.index("Hola") < envio.texto.index("Patio A")


def test_un_marcador_que_no_existe_no_se_guarda():
    plantilla = Plantilla(asunto="Guardias {mes}")
    assert any("{mes}" in e for e in plantilla.errores())
    with pytest.raises(ValueError, match="no existen"):
        plantilla_avisos.guardar(plantilla)
    assert any("vacío" in e for e in Plantilla(asunto=" ").errores())


def test_una_plantilla_ilegible_deja_la_de_serie(tmp_path):
    plantilla_avisos._ruta().write_text("{roto", encoding="utf-8")
    assert plantilla_avisos.cargar() == Plantilla()


def test_la_plantilla_no_va_a_la_carpeta_de_datos_del_repositorio(tmp_path):
    assert plantilla_avisos._ruta().parent == tmp_path


# --- Los adjuntos -----------------------------------------------------------


def test_se_generan_el_pdf_individual_y_el_ical(claustro, tmp_path):
    ana = claustro.query(Profesor).filter_by(nombre_completo="Prueba, Ana").one()

    adjuntos = notificador_guardias.adjuntos_para(
        claustro, ana.id, ana.nombre_completo, Plantilla(), tmp_path
    )

    pdf, ics = adjuntos
    assert pdf.tipo == "application/pdf" and pdf.datos.startswith(b"%PDF")
    assert pdf.nombre.endswith(".pdf")
    assert ics.tipo == "application/ics" and b"BEGIN:VCALENDAR" in ics.datos
    assert ics.nombre.endswith(".ics")


def test_solo_lo_que_pide_la_plantilla(claustro, tmp_path):
    ana = claustro.query(Profesor).filter_by(nombre_completo="Prueba, Ana").one()
    sin_pdf = Plantilla(adjuntar_pdf=False)
    adjuntos = notificador_guardias.adjuntos_para(claustro, ana.id, ana.nombre_completo, sin_pdf, tmp_path)
    assert [a.tipo for a in adjuntos] == ["application/ics"]


def test_el_mensaje_lleva_los_adjuntos(claustro, servidor):
    envios = notificador_guardias.preparar_envios(claustro, "Octubre 2026").envios
    adjunto = [
        notificador_guardias.Adjunto("guardias.pdf", b"%PDF-1.4", "application/pdf"),
        notificador_guardias.Adjunto("guardias.ics", b"BEGIN:VCALENDAR", "application/ics"),
    ]

    resultados = notificador_guardias.enviar(
        envios, servicio=_Servicio(), generar_adjuntos=lambda envio: adjunto
    )

    assert all(r.enviado for r in resultados)
    mensaje = servidor.mensajes[0]
    assert mensaje.get_content_type() == "multipart/mixed"
    partes = {p.get_filename(): p.get_content_type() for p in mensaje.walk() if p.get_filename()}
    assert partes == {"guardias.pdf": "application/pdf", "guardias.ics": "application/ics"}
    # Un solo Content-Type por parte y el nombre también en él: si no, Outlook, Exchange y Gmail
    # se quedan solo con el PDF (el .ics como text/calendar lo toman por una invitación).
    for parte in (p for p in mensaje.walk() if p.get_filename()):
        assert len(parte.get_all("Content-Type")) == 1
        assert parte.get_param("name") == parte.get_filename()
        assert parte.get_content_disposition() == "attachment"
    assert mensaje["To"] == "ana@example.com"


def test_sin_adjuntos_el_mensaje_es_como_antes(claustro, servidor):
    envios = notificador_guardias.preparar_envios(claustro, "Octubre 2026").envios
    notificador_guardias.enviar(envios, servicio=_Servicio())
    assert servidor.mensajes[0].get_content_type() == "multipart/alternative"


def test_si_un_adjunto_falla_ese_no_sale_y_los_demas_si(claustro, servidor):
    envios = notificador_guardias.preparar_envios(claustro, "Octubre 2026").envios

    def adjuntos(envio):
        if envio.nombre == "Prueba, Ana":
            raise ValueError("No se pudo generar el PDF individual")
        return []

    resultados = notificador_guardias.enviar(envios, servicio=_Servicio(), generar_adjuntos=adjuntos)

    assert [r.enviado for r in resultados] == [False, True]
    assert "PDF individual" in resultados[0].detalle
    assert [m["To"] for m in servidor.mensajes] == ["berta@example.com"]


# --- Interfaz ---------------------------------------------------------------


@pytest.mark.ui
def test_el_editor_guarda_la_plantilla(qapp):
    from presentation.dialogs.plantilla_avisos_dialog import PlantillaAvisosDialog

    dialogo = PlantillaAvisosDialog()
    dialogo.asunto.setText("Aviso de {periodo}")
    dialogo.adjuntar_ical.setChecked(False)
    dialogo._guardar()

    guardada = plantilla_avisos.cargar()
    assert guardada.asunto == "Aviso de {periodo}"
    assert guardada.adjuntar_ical is False and guardada.adjuntar_pdf is True


@pytest.mark.ui
def test_el_editor_no_guarda_una_plantilla_mal_escrita(qapp):
    from presentation.dialogs.plantilla_avisos_dialog import PlantillaAvisosDialog

    dialogo = PlantillaAvisosDialog()
    dialogo.asunto.setText("Aviso de {mes}")
    dialogo._guardar()

    assert dialogo.result() != dialogo.DialogCode.Accepted
    assert "{mes}" in dialogo.aviso.text()
    assert plantilla_avisos.cargar() == Plantilla()


@pytest.mark.ui
def test_el_envio_dice_que_adjuntos_lleva_y_lo_ensena_en_la_vista_previa(qapp, claustro):
    from presentation.dialogs.envio_de_emails_dialog import EnvioDeEmailsDialog

    dialogo = EnvioDeEmailsDialog(claustro, mes_anio="Octubre 2026")
    assert "PDF" in dialogo.label_adjuntos.text() and "iCal" in dialogo.label_adjuntos.text()
    assert "Adjuntos:" in dialogo.vista_previa.toHtml()
    assert dialogo.boton_plantilla.text() == "Editar plantilla…"
    dialogo.close()
