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
from infrastructure.database.models import Configuracion, Guardia, Profesor
from services import plantilla_avisos
from services.recreos import configuracion_de, resolver
from utils.orden import clave_alfabetica

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
class Adjunto:
    """Un archivo que viaja con el aviso: el PDF individual o el iCal."""

    nombre: str
    datos: bytes
    tipo: str  # «application/pdf», «application/ics»


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


def preparar_envios(
    session, mes_anio: Optional[str] = None, plantilla: Optional[plantilla_avisos.Plantilla] = None
) -> Preparacion:
    """Redacta el aviso de cada profesor activo con guardias y correo válido.

    Con la plantilla guardada (GUA-CON-002) si no se pasa otra.
    """
    if mes_anio is None:
        mes_anio = date.today().strftime("%B %Y").capitalize()
    if plantilla is None:
        plantilla = plantilla_avisos.cargar()

    preparacion = Preparacion()
    config = configuracion_de(session)
    profesores = (
        session.query(Profesor)
        .filter(Profesor.activo.is_(True))
        .all()
    )
    profesores.sort(key=lambda p: clave_alfabetica(p.nombre_completo))

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

        asunto, cuerpo_html, cuerpo_texto = redactar(
            profesor.nombre_completo, guardias, mes_anio, plantilla, config=config
        )
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


def redactar(
    nombre: str,
    guardias: list,
    mes_anio: str,
    plantilla: Optional[plantilla_avisos.Plantilla] = None,
    config=None,
) -> tuple:
    """Devuelve `(asunto, html, texto)` del aviso de un profesor.

    El recreo sale como «Recreo 1 de tarde · 16:30», con su hora (`services.recreos`).
    """
    import html as _html

    plantilla = plantilla or plantilla_avisos.Plantilla()

    from services.email_service import generar_plantilla_email_html

    filas = ""
    for guardia in guardias:
        fecha = guardia.fecha.strftime("%d/%m/%Y") if guardia.fecha else "—"
        celda = "padding:6px 10px;border-bottom:1px solid #e5e7eb"
        filas += (
            f"<tr><td style='{celda}'>{fecha}</td>"
            f"<td style='{celda}'>{_html.escape(str(guardia.turno))}</td>"
            f"<td style='{celda}'>"
            f"{_html.escape(resolver(config, guardia.recreo, guardia.turno).etiqueta_con_hora)}</td>"
            f"<td style='{celda}'>{_html.escape(nombre_de_zona(guardia))}</td></tr>"
        )

    cabecera = "padding:8px 10px;text-align:left"
    tabla = (
        "<table style='border-collapse:collapse;width:100%;font-size:13px'>"
        "<thead><tr style='background:#2C7A3A;color:white'>"
        f"<th style='{cabecera}'>Día</th><th style='{cabecera}'>Turno</th>"
        f"<th style='{cabecera}'>Recreo</th><th style='{cabecera}'>Zona</th>"
        "</tr></thead><tbody>" + filas + "</tbody></table>"
    )

    valores = {"nombre": nombre, "periodo": mes_anio, "num_guardias": len(guardias)}
    contenido = plantilla_avisos.rellenar_html(plantilla, valores, tabla)
    asunto = plantilla_avisos.rellenar_asunto(plantilla, valores)
    cuerpo_html = generar_plantilla_email_html(titulo=asunto, contenido_principal=contenido)

    lista = "\n".join(
        f"- {g.fecha} | {g.turno} | {resolver(config, g.recreo, g.turno).etiqueta_con_hora} | "
        f"{nombre_de_zona(g)}"
        for g in guardias
    )
    cuerpo_texto = plantilla_avisos.rellenar_texto(plantilla, valores, lista) + "\n\nGuardias de Patio"
    return asunto, cuerpo_html, cuerpo_texto


def adjuntos_para(
    session, profesor_id: int, nombre: str, plantilla: plantilla_avisos.Plantilla, carpeta
) -> list:
    """El PDF individual y el iCal del profesor, según pida la plantilla.

    Se generan en `carpeta` (una temporal) y se leen enteros: el mensaje no
    depende de que el archivo siga ahí al enviarlo. Si uno no se puede generar,
    `ValueError` con el motivo: mejor no enviar que enviar sin lo prometido.
    """
    from pathlib import Path

    from services.icalendar_service import ICalendarService

    carpeta = Path(carpeta)
    nombre_base = ICalendarService.obtener_nombre_archivo_ics(nombre)[: -len(".ics")]
    adjuntos = []
    if plantilla.adjuntar_pdf:
        from services._pdf_individual_optimizado import exportar_profesor_individual_optimizado

        config = session.query(Configuracion).first()
        if config is None:
            raise ValueError("No hay configuración del curso para hacer el PDF")
        ruta = carpeta / f"{nombre_base}.pdf"
        if not exportar_profesor_individual_optimizado(
            session, profesor_id, config.fecha_inicio_curso, config.fecha_fin_curso, str(ruta)
        ):
            raise ValueError("No se pudo generar el PDF individual")
        adjuntos.append(Adjunto(ruta.name, ruta.read_bytes(), "application/pdf"))
    if plantilla.adjuntar_ical:
        ruta = carpeta / f"{nombre_base}.ics"
        if not ICalendarService.generar_icalendar_profesor(session, profesor_id, str(ruta)):
            raise ValueError("No se pudo generar el archivo iCal")
        # «application/ics», no «text/calendar»: con text/calendar y METHOD:PUBLISH, Outlook,
        # Exchange y Gmail lo toman por una invitación y no lo enseñan como adjunto (solo
        # se veía el PDF). Así llegaba antes de la 7.5 y así se abre con cualquier calendario.
        adjuntos.append(Adjunto(ruta.name, ruta.read_bytes(), "application/ics"))
    return adjuntos


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
    generar_adjuntos: Optional[Callable] = None,
) -> list:
    """Manda los avisos por una sola conexión SMTP y cuenta qué pasó con cada uno.

    Si la conexión no se puede abrir, devuelve un resultado fallido por cada
    destinatario en vez de una excepción: así la vista puede decir qué no llegó.
    """
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

                adjuntos = []
                if generar_adjuntos is not None:
                    try:
                        adjuntos = generar_adjuntos(envio)
                    except (ValueError, OSError) as e:
                        resultados.append(_fallo(envio, f"Sin enviar: {e}"))
                        continue

                mensaje = _mensaje(envio, servicio, adjuntos)

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


def _mensaje(envio, servicio, adjuntos: list):
    """El correo de un aviso: texto y HTML, y los adjuntos si los hay."""
    from email.mime.application import MIMEApplication
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    cuerpo = MIMEMultipart("alternative")
    cuerpo.attach(MIMEText(envio.texto, "plain", "utf-8"))
    cuerpo.attach(MIMEText(envio.html, "html", "utf-8"))
    mensaje = cuerpo
    if adjuntos:
        mensaje = MIMEMultipart("mixed")
        mensaje.attach(cuerpo)
        for adjunto in adjuntos:
            principal, sub = adjunto.tipo.split("/", 1)
            parte = MIMEApplication(adjunto.datos, _subtype=sub)
            if principal != "application":
                parte.replace_header("Content-Type", f"{adjunto.tipo}; charset=utf-8")
            parte.set_param("name", adjunto.nombre)
            parte.add_header("Content-Disposition", "attachment", filename=adjunto.nombre)
            mensaje.attach(parte)
    mensaje["Subject"] = envio.asunto
    mensaje["From"] = f"{servicio.from_name} <{servicio.from_email}>"
    mensaje["To"] = envio.email
    return mensaje


def _fallo(envio, detalle: str) -> Resultado:
    return Resultado(envio.profesor_id, envio.nombre, envio.email, False, detalle)
