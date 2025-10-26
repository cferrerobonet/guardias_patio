"""
Servicio de envío de emails para recuperación de contraseña.

Utiliza SMTP para enviar códigos de recuperación a los usuarios.
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

logger = logging.getLogger(__name__)


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
    ):
        """
        Inicializa el servicio de email.

        Args:
            smtp_server: Servidor SMTP (ej: smtp.gmail.com)
            smtp_port: Puerto SMTP (ej: 587 para TLS)
            smtp_user: Usuario SMTP
            smtp_password: Contraseña SMTP o App Password
            from_email: Email del remitente
        """
        self.smtp_server = smtp_server or self.DEFAULT_SMTP_SERVER
        self.smtp_port = smtp_port or self.DEFAULT_SMTP_PORT
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_email = from_email or smtp_user

    def send_recovery_code(
        self,
        to_email: str,
        username: str,
        recovery_code: str
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
            msg["From"] = self.from_email
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

            # Contenido del email (HTML)
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9fafb;
        }}
        .header {{
            background-color: #007ACC;
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 8px 8px 0 0;
        }}
        .content {{
            background-color: white;
            padding: 30px;
            border-radius: 0 0 8px 8px;
        }}
        .code-box {{
            background-color: #f3f4f6;
            border: 2px solid #007ACC;
            border-radius: 6px;
            padding: 20px;
            margin: 20px 0;
            text-align: center;
        }}
        .code {{
            font-size: 24px;
            font-weight: bold;
            color: #007ACC;
            letter-spacing: 2px;
            font-family: monospace;
        }}
        .warning {{
            background-color: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 12px;
            margin: 20px 0;
        }}
        .footer {{
            text-align: center;
            margin-top: 20px;
            color: #6b7280;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔑 Recuperación de Contraseña</h1>
        </div>
        <div class="content">
            <p>Hola <strong>{username}</strong>,</p>
            
            <p>Has solicitado recuperar tu contraseña para la aplicación <strong>Guardias de Patio</strong>.</p>
            
            <div class="code-box">
                <p style="margin: 0 0 10px 0; color: #6b7280;">Tu código de recuperación es:</p>
                <div class="code">{recovery_code}</div>
            </div>
            
            <p>Este código es válido para <strong>un solo uso</strong>. Cópialo y pégalo en la ventana de recuperación de contraseña.</p>
            
            <div class="warning">
                ⚠️ Si no has solicitado este código, puedes ignorar este mensaje. Tu contraseña permanecerá sin cambios.
            </div>
        </div>
        <div class="footer">
            <p>Guardias de Patio - Sistema de Gestión de Guardias</p>
        </div>
    </div>
</body>
</html>
            """

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

        except Exception as e:
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
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_server = os.getenv("SMTP_SERVER", EmailService.DEFAULT_SMTP_SERVER)
    smtp_port = int(os.getenv("SMTP_PORT", str(EmailService.DEFAULT_SMTP_PORT)))

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
    )
