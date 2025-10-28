# Configuración de Email para Recuperación de Contraseña

Este documento explica cómo configurar el envío de emails para el sistema de recuperación de contraseña.

## 📧 Visión General

El sistema de recuperación de contraseña envía códigos de seguridad por email. Para habilitar esta funcionalidad, debes configurar un servidor SMTP.

## 🔧 Configuración

### Paso 1: Crear archivo .env

Si no existe, crea un archivo `.env` en la raíz del proyecto (copia de `.env.example`):

```bash
cp .env.example .env
```

### Paso 2: Configurar variables SMTP

Edita el archivo `.env` y agrega las siguientes variables según tu proveedor de email:

#### Para Gmail

1. Ve a https://myaccount.google.com/apppasswords
2. Genera una "App Password" (contraseña de aplicación)
3. Configura:

```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu_email@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx  # App Password de 16 caracteres
```

#### Para Outlook/Hotmail

```bash
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USER=tu_email@outlook.com
SMTP_PASSWORD=tu_contraseña
```

#### Para Yahoo

```bash
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
SMTP_USER=tu_email@yahoo.com
SMTP_PASSWORD=tu_contraseña_de_aplicacion
```

#### Para IONOS (1&1)

```bash
SMTP_SERVER=smtp.ionos.es
SMTP_PORT=587
SMTP_USER=tu_email@tudominio.com
SMTP_PASSWORD=tu_contraseña
```

#### Para otros proveedores

Consulta la documentación de tu proveedor de email para obtener:
- Servidor SMTP (ejemplo: smtp.tuproveedor.com)
- Puerto (normalmente 587 para TLS o 465 para SSL)
- Credenciales de acceso

## 🔒 Seguridad

### Mejores Prácticas

1. **Nunca** subas el archivo `.env` a Git (está en `.gitignore`)
2. **Usa contraseñas de aplicación** (App Passwords) en lugar de tu contraseña principal
3. **Activa autenticación de dos factores** (2FA) en tu cuenta de email
4. **Limita los permisos** de la cuenta SMTP si es posible

### Gmail: Crear App Password

1. Activa 2FA en tu cuenta de Google
2. Ve a https://myaccount.google.com/apppasswords
3. Selecciona "Correo" y "Otro (nombre personalizado)"
4. Nombra la aplicación (ej: "Guardias de Patio")
5. Copia la contraseña de 16 caracteres generada
6. Úsala en `SMTP_PASSWORD`

## 🧪 Modo Desarrollo

Si **NO** configuras SMTP, el sistema funcionará en "modo desarrollo":
- El código de recuperación se mostrará en pantalla
- Útil para pruebas locales
- **NO recomendado para producción**

## ✅ Verificar Configuración

Para verificar que la configuración funciona:

1. Ejecuta la aplicación
2. En el login, haz clic en "¿Olvidaste tu contraseña?"
3. Introduce tu usuario o email
4. Deberías recibir un email con el código de recuperación

Si recibes un error:
- Verifica que las credenciales sean correctas
- Comprueba que el servidor SMTP y puerto sean correctos
- Revisa los logs en `logs/guardias_patio.log`

## 🎨 Personalización del Email

El email se envía con una plantilla HTML profesional que incluye:
- Logo y colores corporativos
- Código destacado en una caja
- Versión texto plano alternativa
- Advertencias de seguridad

Para personalizar el contenido, edita:
```
src/services/email_service.py
```

## 📝 Ejemplo Completo (.env)

```bash
# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=guardias.sistema@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop
```

## ❓ Problemas Comunes

### "Error de autenticación SMTP"
- Verifica usuario y contraseña
- Para Gmail: usa App Password, no tu contraseña normal
- Comprueba que 2FA esté activo (Gmail)

### "Connection timed out"
- Verifica el servidor SMTP y puerto
- Comprueba tu firewall/antivirus
- Algunos ISP bloquean el puerto 25, usa 587

### "Email no configurado"
- Verifica que las variables estén en `.env`
- Reinicia la aplicación después de editar `.env`
- Comprueba que el archivo se llame exactamente `.env`

## 🚀 Producción

Para despliegue en producción:

1. **Usa una cuenta dedicada** solo para la aplicación
2. **Configura límites** de envío (rate limiting) si es necesario
3. **Monitorea** los logs de envío de emails
4. **Considera usar un servicio** de email transaccional (SendGrid, Mailgun, etc.)

## 📚 Referencias

- [Gmail App Passwords](https://support.google.com/accounts/answer/185833)
- [Outlook SMTP Settings](https://support.microsoft.com/en-us/office/pop-imap-and-smtp-settings-8361e398-8af4-4e97-b147-6c6c4ac95353)
- [Python smtplib Documentation](https://docs.python.org/3/library/smtplib.html)
