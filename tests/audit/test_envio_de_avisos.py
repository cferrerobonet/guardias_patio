"""FUN-006 — vista previa y resultado por destinatario en el envío de avisos.

El envío anterior salía sin enseñar nada, con la ventana congelada mientras
hablaba con el servidor —una conexión SMTP por profesor—, y terminaba con un
resumen que recortaba los errores a los cinco primeros.

Además arrastraba un fallo que lo rompía entero: leía la zona como `zona.nombre`
cuando el campo se llama `nombre_zona`, así que el primer profesor con guardias
lanzaba `AttributeError` antes de mandar nada.
"""

import datetime
import inspect
import smtplib

import pytest

from infrastructure.database.models import Guardia, Profesor, Zona
from services import notificador_guardias

LUNES = datetime.date(2025, 10, 6)


class _ServicioFalso:
    smtp_server = "smtp.epla.es"
    smtp_port = 587
    smtp_user = "avisos@epla.es"
    smtp_password = "x"
    from_name = "Guardias de Patio"
    from_email = "avisos@epla.es"


class _ServidorFalso:
    """Sustituye a `smtplib.SMTP`: cuenta conexiones y mensajes."""

    conexiones = 0
    fallar_para = ()

    def __init__(self, *args, **kwargs):
        type(self).conexiones += 1
        self.enviados = []

    def __enter__(self):
        return self

    def __exit__(self, *excepcion):
        return False

    def starttls(self):
        pass

    def login(self, usuario, clave):
        pass

    def send_message(self, mensaje):
        if mensaje["To"] in type(self).fallar_para:
            raise smtplib.SMTPRecipientsRefused({mensaje["To"]: (550, b"no existe")})
        self.enviados.append(mensaje["To"])


@pytest.fixture
def claustro(session):
    session.add(Zona(nombre_zona="Patio A", activa=True))
    session.add_all(
        [
            Profesor(
                nombre_completo="Con Guardias, Ana",
                email_corporativo="ana@epla.es",
                horas_contrato=25.0,
                porcentaje_jornada=100.0,
                turno="mañana",
                tutor=False,
                activo=True,
            ),
            Profesor(
                nombre_completo="Sin Correo, Luis",
                horas_contrato=25.0,
                porcentaje_jornada=100.0,
                turno="mañana",
                tutor=False,
                activo=True,
            ),
            Profesor(
                nombre_completo="Sin Guardias, Marta",
                email_corporativo="marta@epla.es",
                horas_contrato=25.0,
                porcentaje_jornada=100.0,
                turno="mañana",
                tutor=False,
                activo=True,
            ),
        ]
    )
    session.commit()
    ana = session.query(Profesor).filter_by(nombre_completo="Con Guardias, Ana").one()
    zona = session.query(Zona).first()
    session.add(
        Guardia(
            profesor_id=ana.id, fecha=LUNES, turno="mañana", recreo=1, zona_id=zona.id
        )
    )
    session.commit()
    return session


def test_solo_se_prepara_para_quien_puede_recibirlo(claustro):
    preparacion = notificador_guardias.preparar_envios(claustro, "Octubre 2025")

    assert [e.nombre for e in preparacion.envios] == ["Con Guardias, Ana"]
    assert {e.motivo for e in preparacion.excluidos} == {"sin correo", "sin guardias"}


def test_el_mensaje_nombra_la_zona_de_verdad(claustro):
    """`zona.nombre` no existe: leerlo rompía el envío con AttributeError."""
    preparacion = notificador_guardias.preparar_envios(claustro, "Octubre 2025")

    assert "Patio A" in preparacion.envios[0].html
    assert "Patio A" in preparacion.envios[0].texto


def test_una_zona_que_ya_no_esta_no_rompe_el_mensaje():
    class _GuardiaSuelta:
        zona = None

    assert notificador_guardias.nombre_de_zona(_GuardiaSuelta()) == "—"


def test_el_nombre_va_escapado(claustro):
    profesor = claustro.query(Profesor).filter_by(email_corporativo="ana@epla.es").one()
    profesor.nombre_completo = "<script>alerta</script>"
    claustro.commit()

    preparacion = notificador_guardias.preparar_envios(claustro, "Octubre 2025")
    assert "<script>" not in preparacion.envios[0].html


def test_una_sola_conexion_para_todos(monkeypatch, claustro):
    """Abrir una conexión SMTP por profesor era lo que congelaba la ventana."""
    _ServidorFalso.conexiones = 0
    _ServidorFalso.fallar_para = ()
    monkeypatch.setattr(smtplib, "SMTP", _ServidorFalso)
    envios = notificador_guardias.preparar_envios(claustro, "Octubre 2025").envios * 3

    resultados = notificador_guardias.enviar(envios, servicio=_ServicioFalso())

    assert _ServidorFalso.conexiones == 1
    assert all(r.enviado for r in resultados)


def test_un_destinatario_rechazado_no_corta_el_resto(monkeypatch, claustro):
    _ServidorFalso.conexiones = 0
    _ServidorFalso.fallar_para = ("ana@epla.es",)
    monkeypatch.setattr(smtplib, "SMTP", _ServidorFalso)
    envio = notificador_guardias.preparar_envios(claustro, "Octubre 2025").envios[0]
    otro = notificador_guardias.Envio(99, "Otro, Profesor", "otro@epla.es", 1, "a", "b", "c")

    resultados = notificador_guardias.enviar([envio, otro], servicio=_ServicioFalso())

    assert [r.enviado for r in resultados] == [False, True]
    assert "rechazada" in resultados[0].detalle.lower()
    _ServidorFalso.fallar_para = ()


def test_sin_credenciales_cada_destinatario_recibe_su_motivo(monkeypatch, claustro):
    def explota(*args, **kwargs):
        raise smtplib.SMTPAuthenticationError(535, b"mal")

    monkeypatch.setattr(smtplib, "SMTP", explota)
    envios = notificador_guardias.preparar_envios(claustro, "Octubre 2025").envios

    resultados = notificador_guardias.enviar(envios, servicio=_ServicioFalso())

    assert len(resultados) == len(envios)
    assert all(not r.enviado for r in resultados)
    assert "contraseña" in resultados[0].detalle


def test_sin_smtp_configurado_no_lanza_excepcion(monkeypatch, claustro):
    """Sin servicio explícito se pregunta al de la aplicación, nunca a la red aquí."""
    import services.email_service as email_service

    monkeypatch.setattr(email_service, "get_email_service", lambda: None)
    envios = notificador_guardias.preparar_envios(claustro, "Octubre 2025").envios

    resultados = notificador_guardias.enviar(envios)

    assert all(not r.enviado for r in resultados)
    assert "SMTP no configurado" in resultados[0].detalle


def test_se_puede_cancelar_a_medias(monkeypatch, claustro):
    import threading

    _ServidorFalso.conexiones = 0
    monkeypatch.setattr(smtplib, "SMTP", _ServidorFalso)
    envios = notificador_guardias.preparar_envios(claustro, "Octubre 2025").envios * 4
    cancelacion = threading.Event()

    def avisar(numero, total, nombre):
        if numero == 2:
            cancelacion.set()

    resultados = notificador_guardias.enviar(
        envios, servicio=_ServicioFalso(), progreso=avisar, cancelacion=cancelacion
    )

    assert len(resultados) < len(envios)


def test_el_envio_no_ocurre_en_el_hilo_de_la_interfaz():
    """El botón sólo abre el diálogo; el envío pasa por `ejecutar_con_progreso`."""
    from presentation.dialogs.envio_de_emails_dialog import EnvioDeEmailsDialog
    from presentation.forms.asignacion_widgets.generacion_panel import GeneracionPanel

    boton = inspect.getsource(GeneracionPanel._enviar_notificaciones)
    assert "EnvioDeEmailsDialog" in boton
    assert "send_message" not in boton

    envio = inspect.getsource(EnvioDeEmailsDialog._enviar)
    assert "ejecutar_con_progreso" in envio
