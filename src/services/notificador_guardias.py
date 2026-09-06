"""Preparación y envío de los avisos de guardias al profesorado (FUN-006).

Separa el trabajo en dos mitades: **preparar** los mensajes, que sólo lee de la
base de datos y se puede enseñar antes de mandar nada, y **enviarlos**, que
habla con el servidor SMTP y se puede llevar a un hilo aparte.

Antes se hacía todo de una vez, en el hilo de la interfaz, abriendo una conexión
SMTP por profesor y sin poder ver qué se iba a mandar ni a quién había llegado.
"""

import smtplib
from dataclasses import dataclass, field
from datetime import date
from typing import Callable, Optional

from core.logging import get_logger
from infrastructure.database.models import Guardia, Profesor

logger = get_logger(__name__)


@dataclass
class Envio:
    """Un mensaje ya redactado, listo para enseñar y para mandar."""

    profesor_id: int
    nombre: str
    email: str
    guardias: int
    asunto: str
    html: str
    texto: str


@dataclass
class Excluido:
    """Un profesor que no recibirá nada, y por qué."""

    nombre: str
    motivo: str


@dataclass
class Preparacion:
    envios: list = field(default_factory=list)
    excluidos: list = field(default_factory=list)


@dataclass
class Resultado:
    profesor_id: int
    nombre: str
    email: str
    enviado: bool
    detalle: str


def preparar_envios(session, mes_anio: Optional[str] = None) -> Preparacion:
    """Redacta el aviso de cada profesor activo con guardias y correo válido."""
    if mes_anio is None:
        mes_anio = date.today().strftime("%B %Y").capitalize()

    preparacion = Preparacion()
    profesores = (
        session.query(Profesor)
        .filter(Profesor.activo.is_(True))
        .order_by(Profesor.nombre_completo)
        .all()
    )

    for profesor in profesores:
        correo = (profesor.email_corporativo or "").strip()
        if "@" not in correo:
            preparacion.excluidos.append(Excluido(profesor.nombre_completo, "sin correo"))
            continue

        guardias = (
            session.query(Guardia)
            .filter(Guardia.profesor_id == profesor.id)
            .order_by(Guardia.fecha, Guardia.recreo)
            .all()
        )
        if not guardias:
            preparacion.excluidos.append(Excluido(profesor.nombre_completo, "sin guardias"))
            continue

        asunto, cuerpo_html, cuerpo_texto = redactar(profesor.nombre_completo, guardias, mes_anio)
        preparacion.envios.append(
            Envio(
                profesor_id=profesor.id,
                nombre=profesor.nombre_completo,
                email=correo,
                guardias=len(guardias),
                asunto=asunto,
                html=cuerpo_html,
                texto=cuerpo_texto,
            )
        )

    logger.info(
        f"Preparados {len(preparacion.envios)} avisos "
        f"({len(preparacion.excluidos)} profesores fuera)"
    )
    return preparacion


def redactar(nombre: str, guardias: list, mes_anio: str) -> tuple:
    """Devuelve `(asunto, html, texto)` del aviso de un profesor."""
    import html as _html

    from services.email_service import generar_plantilla_email_html

    filas = ""
    for guardia in guardias:
        fecha = guardia.fecha.strftime("%d/%m/%Y") if guardia.fecha else "—"
        celda = "padding:6px 10px;border-bottom:1px solid #e5e7eb"
        filas += (
            f"<tr><td style='{celda}'>{fecha}</td>"
            f"<td style='{celda}'>{_html.escape(str(guardia.turno))}</td>"
            f"<td style='{celda}'>{guardia.recreo}</td>"
            f"<td style='{celda}'>{_html.escape(nombre_de_zona(guardia))}</td></tr>"
        )

    cabecera = "padding:8px 10px;text-align:left"
    tabla = (
        "<table style='border-collapse:collapse;width:100%;font-size:13px'>"
        "<thead><tr style='background:#0E5FA8;color:white'>"
        f"<th style='{cabecera}'>Día</th><th style='{cabecera}'>Turno</th>"
        f"<th style='{cabecera}'>Recreo</th><th style='{cabecera}'>Zona</th>"
        "</tr></thead><tbody>" + filas + "</tbody></table>"
    )

    seguro = _html.escape(nombre)
    contenido = (
        f"<p>Estimado/a <strong>{seguro}</strong>,</p>"
        f"<p>A continuación encontrarás tus guardias de patio asignadas para "
        f"<strong>{_html.escape(mes_anio)}</strong>:</p>"
        f"{tabla}"
        "<p style='margin-top:20px'>Si tienes alguna duda, contacta con la dirección "
        "del centro.</p>"
    )
    asunto = f"Guardias de patio — {mes_anio}"
    cuerpo_html = generar_plantilla_email_html(titulo=asunto, contenido_principal=contenido)

    cuerpo_texto = (
        f"Hola {nombre},\n\nTus guardias de patio para {mes_anio}:\n\n"
        + "\n".join(
            f"- {g.fecha} | {g.turno} | Recreo {g.recreo} | {nombre_de_zona(g)}"
            for g in guardias
        )
        + "\n\nGuardias de Patio"
    )
    return asunto, cuerpo_html, cuerpo_texto


def nombre_de_zona(guardia) -> str:
    """La zona de una guardia, o un guion si ya no existe.

    El campo se llama `nombre_zona`; leerlo como `nombre` rompía el envío entero
    con un `AttributeError` antes siquiera de abrir la conexión.
    """
    zona = getattr(guardia, "zona", None)
    return getattr(zona, "nombre_zona", None) or "—"


def enviar(
    envios: list,
    servicio=None,
    progreso: Optional[Callable] = None,
    cancelacion=None,
) -> list:
    """Manda los avisos por una sola conexión SMTP y cuenta qué pasó con cada uno.

    Si la conexión no se puede abrir, devuelve un resultado fallido por cada
    destinatario en vez de una excepción: así la vista puede decir qué no llegó.
    """
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    from services.email_service import get_email_service

    servicio = servicio or get_email_service()
    if servicio is None:
        return [_fallo(e, "SMTP no configurado") for e in envios]

    resultados = []
    try:
        with smtplib.SMTP(servicio.smtp_server, servicio.smtp_port) as servidor:
            servidor.starttls()
            servidor.login(servicio.smtp_user, servicio.smtp_password)

            for numero, envio in enumerate(envios, start=1):
                if cancelacion is not None and cancelacion.is_set():
                    break
                if progreso:
                    progreso(numero, len(envios), envio.nombre)

                mensaje = MIMEMultipart("alternative")
                mensaje["Subject"] = envio.asunto
                mensaje["From"] = f"{servicio.from_name} <{servicio.from_email}>"
                mensaje["To"] = envio.email
                mensaje.attach(MIMEText(envio.texto, "plain", "utf-8"))
                mensaje.attach(MIMEText(envio.html, "html", "utf-8"))

                try:
                    servidor.send_message(mensaje)
                    resultados.append(
                        Resultado(envio.profesor_id, envio.nombre, envio.email, True, "Enviado")
                    )
                except smtplib.SMTPRecipientsRefused:
                    resultados.append(_fallo(envio, "Dirección rechazada por el servidor"))
                except smtplib.SMTPException as e:
                    # Un destinatario que falla no debe cortar el resto del envío.
                    resultados.append(_fallo(envio, f"Error SMTP: {e}"))
    except smtplib.SMTPAuthenticationError:
        pendientes = envios[len(resultados):]
        return resultados + [_fallo(e, "Usuario o contraseña SMTP incorrectos") for e in pendientes]
    except (smtplib.SMTPException, OSError) as e:
        pendientes = envios[len(resultados):]
        return resultados + [_fallo(p, f"No se pudo conectar: {e}") for p in pendientes]

    logger.info(f"Avisos enviados: {sum(1 for r in resultados if r.enviado)}/{len(envios)}")
    return resultados


def _fallo(envio, detalle: str) -> Resultado:
    return Resultado(envio.profesor_id, envio.nombre, envio.email, False, detalle)
