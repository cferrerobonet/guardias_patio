"""
Servicio de envío de emails para recuperación de contraseña.

Utiliza SMTP para enviar códigos de recuperación a los usuarios.
"""

import html
import logging
import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def generar_plantilla_email_html(
    titulo: str,
    contenido_principal: str,
    secciones: Optional[List[Dict[str, str]]] = None,
    pie_texto: str = "Guardias de Patio - Sistema de Gestión de Guardias",
) -> str:
    """
    Genera una plantilla HTML estándar para emails del sistema.

    Esta función garantiza que todos los emails sigan el mismo diseño elegante
    y profesional, manteniendo consistencia visual en toda la aplicación.

    Args:
        titulo: Título principal del email (aparece en el encabezado)
        contenido_principal: Texto principal del email (puede incluir HTML)
        secciones: Lista opcional de secciones con formato especial. Cada sección es un dict con:
            - 'tipo': 'info' (azul), 'warning' (amarillo), 'success' (verde), 'neutral' (gris)
            - 'contenido': Contenido HTML de la sección
        pie_texto: Texto del footer (por defecto es el nombre del sistema)

    Returns:
        String con el HTML completo del email

    Example:
        >>> html = generar_plantilla_email_html(
        ...     titulo="📅 Calendario de Guardias 2024-2025",
        ...     contenido_principal="<p>Hola <strong>Juan</strong>,</p><p>Adjuntamos tu calendario.</p>",
        ...     secciones=[
        ...         {'tipo': 'info', 'contenido': '<p>📎 Archivos adjuntos incluidos</p>'},
        ...         {'tipo': 'success', 'contenido': '<p>💡 Tip: Guarda este email</p>'}
        ...     ]
        ... )
    """
    # Estilos según tipo de sección
    estilos_secciones = {
        "info": {"bg_color": "#e3f2fd", "border_color": "#2196F3"},
        "warning": {"bg_color": "#fff3e0", "border_color": "#FF9800"},
        "success": {"bg_color": "#e8f5e9", "border_color": "#4CAF50"},
        "neutral": {"bg_color": "#f5f5f5", "border_color": "#9e9e9e"},
    }

    # Construir secciones HTML
    secciones_html = ""
    if secciones:
        for seccion in secciones:
            tipo = seccion.get("tipo", "neutral")
            contenido = seccion.get("contenido", "")
            estilo = estilos_secciones.get(tipo, estilos_secciones["neutral"])

            secciones_html += f"""
      <div style="background-color: {estilo["bg_color"]}; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid {estilo["border_color"]};">
        {contenido}
      </div>
"""

    # Plantilla HTML completa con logo corporativo verde
    html = f"""
<html>
  <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; background-color: #f5f5f5; margin: 0; padding: 20px;">
    <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">

      <!-- Logo corporativo con gradiente verde -->
      <div style="background: linear-gradient(135deg, #4CAF50 0%, #388E3C 100%); padding: 30px 20px; text-align: center;">
        <div style="background-color: white; width: 80px; height: 80px; margin: 0 auto 15px; border-radius: 50%; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
          <span style="font-size: 40px;">🏫</span>
        </div>
        <h1 style="color: white; margin: 0; font-size: 20px; font-weight: 600; letter-spacing: 0.5px;">Guardias de Patio</h1>
        <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0 0; font-size: 13px;">Sistema de Gestión de Guardias</p>
      </div>

      <!-- Contenido principal -->
      <div style="padding: 30px 20px;">
        <h2 style="color: #4CAF50; margin: 0 0 20px 0; font-size: 22px;">{titulo}</h2>

        {contenido_principal}

        {secciones_html}
      </div>

      <!-- Footer -->
      <div style="background-color: #f8f9fa; padding: 20px; text-align: center; border-top: 1px solid #e5e7eb;">
        <p style="font-size: 12px; color: #6b7280; margin: 0;">
          {pie_texto}
        </p>
      </div>
    </div>
  </body>
</html>
    """

    return html.strip()


class EmailService:
    """Servicio para envío de emails."""

    # Configuración SMTP por defecto (Gmail)
    # Los usuarios pueden modificar esto según su proveedor
    DEFAULT_SMTP_SERVER = "smtp.gmail.com"
    DEFAULT_SMTP_PORT = 587

    def __init__(
        self,
        smtp_server: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
    ):
        """
        Inicializa el servicio de email.

        Args:
            smtp_server: Servidor SMTP (ej: smtp.gmail.com)
            smtp_port: Puerto SMTP (ej: 587 para TLS)
            smtp_user: Usuario SMTP
            smtp_password: Contraseña SMTP o App Password
            from_email: Email del remitente
            from_name: Nombre del remitente que aparecerá en los emails
        """
        self.smtp_server = smtp_server or self.DEFAULT_SMTP_SERVER
        self.smtp_port = smtp_port or self.DEFAULT_SMTP_PORT
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_email = from_email or smtp_user
        self.from_name = from_name or "Guardias de Patio"

    def send_recovery_code(
        self, to_email: str, username: str, recovery_code: str
    ) -> tuple[bool, str]:
        """
        Envía un código de recuperación por email.

        Args:
            to_email: Email del destinatario
            username: Nombre de usuario
            recovery_code: Código de recuperación

        Returns:
            Tupla (éxito, mensaje)
        """
        if not self.smtp_user or not self.smtp_password:
            return False, "Email no configurado. Por favor contacta al administrador."

        try:
            # Crear mensaje
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "🔑 Código de Recuperación - Guardias de Patio"
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email

            # Contenido del email (texto plano)
            text_content = f"""
Hola {username},

Has solicitado recuperar tu contraseña para la aplicación Guardias de Patio.

Tu código de recuperación es:

{recovery_code}

Este código es válido para un solo uso. Cópialo y pégalo en la ventana de recuperación de contraseña.

Si no has solicitado este código, puedes ignorar este mensaje.

---
Guardias de Patio
Sistema de Gestión de Guardias
            """

            # Contenido del email (HTML) - Usando plantilla estándar
            safe_username = html.escape(username)
            contenido_principal = f"""
      <p>Hola <strong>{safe_username}</strong>,</p>
      <p>Has solicitado recuperar tu contraseña para la aplicación <strong>Guardias de Patio</strong>.</p>
            """

            secciones = [
                {
                    "tipo": "info",
                    "contenido": f"""
        <div style="text-align: center; background-color: #e8f5e9; border: 2px solid #4CAF50; border-radius: 6px; padding: 20px; margin: 20px 0;">
          <p style="margin: 0 0 10px 0; color: #2e7d32;">Tu código de recuperación es:</p>
          <div style="font-size: 24px; font-weight: bold; color: #4CAF50; letter-spacing: 2px; font-family: monospace;">
            {recovery_code}
          </div>
        </div>
        <p style="margin-top: 15px;">Este código es válido para <strong>un solo uso</strong>. Cópialo y pégalo en la ventana de recuperación de contraseña.</p>
                    """,
                },
                {
                    "tipo": "warning",
                    "contenido": """
        <p style="margin: 5px 0;">⚠️ Si no has solicitado este código, puedes ignorar este mensaje. Tu contraseña permanecerá sin cambios.</p>
                    """,
                },
            ]

            html_content = generar_plantilla_email_html(
                titulo="🔑 Recuperación de Contraseña",
                contenido_principal=contenido_principal,
                secciones=secciones,
            )

            # Adjuntar ambas versiones
            part1 = MIMEText(text_content, "plain")
            part2 = MIMEText(html_content, "html")
            msg.attach(part1)
            msg.attach(part2)

            # Enviar email
            logger.info(f"Enviando código de recuperación a {to_email}")

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # Seguridad TLS
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Código de recuperación enviado exitosamente a {to_email}")
            return True, f"Código enviado a {to_email}"

        except smtplib.SMTPAuthenticationError:
            error_msg = "Error de autenticación SMTP. Verifica usuario y contraseña."
            logger.error(error_msg)
            return False, error_msg

        except smtplib.SMTPException as e:
            error_msg = f"Error SMTP: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

        except (ValueError, TypeError, OSError) as e:
            error_msg = f"Error al enviar email: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def send_calendar_pdf(
        self,
        to_email: str,
        profesor_nombre: str,
        pdf_path: str,
        curso_escolar: str,
        ics_path: Optional[str] = None,
    ) -> tuple[bool, str]:
        """
        Envía un calendario de guardias en PDF por email.

        Args:
            to_email: Email del destinatario
            profesor_nombre: Nombre completo del profesor
            pdf_path: Ruta al archivo PDF
            curso_escolar: Curso escolar (ej: "2024/2025")
            ics_path: Ruta opcional al archivo .ics (iCalendar)

        Returns:
            Tupla (éxito, mensaje)
        """
        if not self.smtp_user or not self.smtp_password:
            return False, "Email no configurado. Por favor contacta al administrador."

        if not os.path.exists(pdf_path):
            return False, f"El archivo PDF no existe: {pdf_path}"

        try:
            # Crear mensaje principal (mixed para adjuntos)
            msg = MIMEMultipart("mixed")
            msg["Subject"] = f"📅 Calendario de Guardias {curso_escolar} - Guardias de Patio"
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email

            # Contenido del email (texto plano)
            text_content = f"""
Hola {profesor_nombre},

Te adjuntamos tu calendario personalizado de guardias de patio para el curso escolar {curso_escolar}.

📎 ADJUNTOS:
• PDF: Calendario visual con todas tus guardias
• ICS: Archivo para importar a tu calendario digital

📱 IMPORTAR A TU CALENDARIO:
El archivo .ics se puede abrir con Google Calendar, Apple Calendar, Outlook, etc.
Simplemente abre el archivo desde tu móvil, tablet u ordenador.

📅 CARACTERÍSTICAS:
• Visualización mensual con mini calendarios
• Colores según la zona asignada
• Formas geométricas según el recreo
• Tabla detallada con todas las guardias

Si tienes alguna duda o consulta, por favor contacta con el coordinador.

---
Guardias de Patio
Sistema de Gestión de Guardias
            """

            # Contenido del email (HTML) - Usando plantilla estándar
            safe_nombre = html.escape(profesor_nombre)
            contenido_principal = f"""
      <p>Hola <strong>{safe_nombre}</strong>,</p>
      <p>Te adjuntamos tu calendario personalizado de guardias de patio para el curso escolar <strong>{curso_escolar}</strong>.</p>
            """

            secciones = [
                {
                    "tipo": "info",
                    "contenido": """
        <p style="margin: 5px 0; font-weight: bold;">📎 Archivos adjuntos:</p>
        <p style="margin: 5px 0;">• <strong>PDF:</strong> Calendario visual con todas tus guardias</p>
        <p style="margin: 5px 0;">• <strong>ICS:</strong> Para importar a tu calendario digital</p>
                    """,
                },
                {
                    "tipo": "warning",
                    "contenido": """
        <p style="margin: 5px 0; font-weight: bold;">📱 Importar a tu calendario:</p>
        <p style="margin: 5px 0;">El archivo <strong>.ics</strong> se puede abrir directamente con:</p>
        <p style="margin: 5px 0;">• Google Calendar</p>
        <p style="margin: 5px 0;">• Apple Calendar (iPhone, iPad, Mac)</p>
        <p style="margin: 5px 0;">• Microsoft Outlook</p>
        <p style="margin: 5px 0; color: #92400e; font-size: 14px; margin-top: 10px;">
          <em>Solo tienes que abrir el archivo desde tu dispositivo y se añadirán automáticamente todas las guardias.</em>
        </p>
                    """,
                },
                {
                    "tipo": "neutral",
                    "contenido": """
        <p style="margin: 5px 0; font-weight: bold;">📅 Características del calendario PDF:</p>
        <p style="margin: 8px 0;">✓ Visualización mensual con mini calendarios</p>
        <p style="margin: 8px 0;">✓ Colores según la zona asignada</p>
        <p style="margin: 8px 0;">✓ Formas geométricas según el recreo</p>
        <p style="margin: 8px 0;">✓ Tabla detallada con todas las guardias</p>
                    """,
                },
                {
                    "tipo": "success",
                    "contenido": """
        <p style="margin: 5px 0;">💡 Tip: Puedes imprimir el PDF o guardarlo en tu dispositivo para tenerlo siempre a mano.</p>
                    """,
                },
            ]

            # Añadir texto final
            contenido_principal += """
      <p style="margin-top: 30px;">Si tienes alguna duda o consulta, por favor contacta con el coordinador.</p>
            """

            html_content = generar_plantilla_email_html(
                titulo=f"📅 Calendario de Guardias {curso_escolar}",
                contenido_principal=contenido_principal,
                secciones=secciones,
            )

            # Crear contenedor alternativo para texto plano y HTML
            msg_alternative = MIMEMultipart("alternative")
            part1 = MIMEText(text_content, "plain", "utf-8")
            part2 = MIMEText(html_content, "html", "utf-8")
            msg_alternative.attach(part1)
            msg_alternative.attach(part2)

            # Adjuntar el contenedor alternativo al mensaje principal
            msg.attach(msg_alternative)

            # Adjuntar el PDF
            with open(pdf_path, "rb") as f:
                pdf_attachment = MIMEApplication(f.read(), _subtype="pdf")
                pdf_filename = os.path.basename(pdf_path)
                pdf_attachment.add_header(
                    "Content-Disposition", "attachment", filename=pdf_filename
                )
                msg.attach(pdf_attachment)

            # Adjuntar el archivo .ics si está disponible
            if ics_path and os.path.exists(ics_path):
                with open(ics_path, "rb") as f:
                    ics_attachment = MIMEApplication(f.read(), _subtype="ics")
                    ics_filename = os.path.basename(ics_path)
                    ics_attachment.add_header(
                        "Content-Disposition",
                        "attachment",
                        filename=ics_filename,
                    )
                    # Agregar header específico para calendarios
                    ics_attachment.add_header("Content-Type", "text/calendar", charset="utf-8")
                    msg.attach(ics_attachment)
                    logger.info(f"Archivo iCalendar adjunto: {ics_filename}")

            # Enviar email
            logger.info(f"Enviando calendario PDF a {to_email}")

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # Seguridad TLS
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Calendario PDF enviado exitosamente a {to_email}")
            return True, f"Calendario enviado a {to_email}"

        except smtplib.SMTPAuthenticationError:
            error_msg = "Error de autenticación SMTP. Verifica usuario y contraseña."
            logger.error(error_msg)
            return False, error_msg

        except smtplib.SMTPException as e:
            error_msg = f"Error SMTP: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

        except FileNotFoundError:
            error_msg = f"Archivo PDF no encontrado: {pdf_path}"
            logger.error(error_msg)
            return False, error_msg

        except (ValueError, TypeError, OSError) as e:
            error_msg = f"Error al enviar email: {str(e)}"
            logger.error(error_msg)
            return False, error_msg


def get_email_service() -> Optional[EmailService]:
    """
    Obtiene una instancia configurada del servicio de email.

    Lee la configuración desde variables de entorno o archivo .env.
    Por ahora retorna None si no está configurado, lo que indica que el
    sistema debe mostrar el código en pantalla.

    Returns:
        EmailService configurado o None si no hay configuración
    """
    import os

    from dotenv import load_dotenv

    # Cargar variables de entorno desde .env
    load_dotenv()

    smtp_user = os.getenv("SMTP_USER")
    from core.credenciales import obtener

    # Del llavero del sistema, con el `.env` de respaldo (SEC-001).
    smtp_password = obtener("SMTP_PASSWORD") or None
    smtp_server = os.getenv("SMTP_SERVER", EmailService.DEFAULT_SMTP_SERVER)
    smtp_port = int(os.getenv("SMTP_PORT", str(EmailService.DEFAULT_SMTP_PORT)))
    smtp_from_name = os.getenv("SMTP_FROM_NAME", "Guardias de Patio")

    if not smtp_user or not smtp_password:
        logger.warning(
            "Configuración SMTP no encontrada. "
            "Define SMTP_USER y SMTP_PASSWORD en archivo .env o variables de entorno."
        )
        return None

    return EmailService(
        smtp_server=smtp_server,
        smtp_port=smtp_port,
        smtp_user=smtp_user,
        smtp_password=smtp_password,
        from_name=smtp_from_name,
    )
