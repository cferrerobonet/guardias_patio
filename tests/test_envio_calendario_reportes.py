"""El correo de Reportes («Exportar PDF individual» con envío) lleva el PDF y el .ics, y el .ics se genera.

Sin servidor de correo: `smtplib.SMTP` se sustituye por un servidor falso que guarda los mensajes.
"""
import re
import smtplib
from pathlib import Path

import pytest

from services.email_service import EmailService

RAIZ = Path(__file__).resolve().parents[1]


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
def servicio():
    return EmailService("smtp.example.com", 587, "avisos@example.com", "x", "avisos@example.com", "Guardias")


def _adjuntos(mensaje) -> dict:
    return {p.get_filename(): p for p in mensaje.walk() if p.get_filename()}


def test_el_correo_de_reportes_lleva_el_pdf_y_el_ics(servidor, servicio, tmp_path):
    pdf = tmp_path / "Calendario_Prueba_Ana.pdf"
    pdf.write_bytes(b"%PDF-1.4 ficticio")
    ics = tmp_path / "guardias_PRUEBA_ANA.ics"
    ics.write_bytes(b"BEGIN:VCALENDAR\r\nMETHOD:PUBLISH\r\nEND:VCALENDAR\r\n")

    ok, _ = servicio.send_calendar_pdf("ana@example.com", "Prueba, Ana", str(pdf), "2026/2027", str(ics))

    assert ok and len(servidor.mensajes) == 1
    adjuntos = _adjuntos(servidor.mensajes[0])
    assert set(adjuntos) == {pdf.name, ics.name}
    parte = adjuntos[ics.name]
    # Un solo Content-Type (application/ics) con su nombre: con un segundo «text/calendar» añadido, Outlook,
    # Exchange y Gmail lo tomaban por una invitación y no lo enseñaban como adjunto.
    assert parte.get_all("Content-Type") == [f'application/ics; name="{ics.name}"']
    assert parte.get_content_disposition() == "attachment"
    assert parte.get_payload(decode=True).startswith(b"BEGIN:VCALENDAR")


def test_sin_ics_el_correo_lleva_solo_el_pdf(servidor, servicio, tmp_path):
    pdf = tmp_path / "Calendario.pdf"
    pdf.write_bytes(b"%PDF-1.4 ficticio")
    ok, _ = servicio.send_calendar_pdf("ana@example.com", "Prueba, Ana", str(pdf), "2026/2027", None)
    assert ok and set(_adjuntos(servidor.mensajes[0])) == {pdf.name}


def test_reportes_genera_el_ics_con_los_parametros_del_servicio():
    """El primer parámetro de `generar_icalendar_profesor` es `session_or_factory`: una llamada con «session=» da
    TypeError, que el envío se traga, y el correo sale sin el .ics (pasó en Reportes de la 7.3.0 a la 7.5.5)."""
    fuente = (RAIZ / "src" / "presentation" / "forms" / "reportes_form.py").read_text(encoding="utf-8")
    llamadas = re.findall(r"generar_icalendar_profesor\((.*?)\)", fuente, re.S)
    assert llamadas, "Reportes ya no genera el .ics"
    assert not any(re.search(r"\bsession\s*=", ll) for ll in llamadas)
