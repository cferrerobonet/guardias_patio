# 📧 Configuración Email y SMTP - Guía Completa

**Versión:** 2.9.0  
**Última actualización:** 28 de octubre de 2025  
**Estado:** ✅ Funcional y en producción

> ℹ️ **Este documento consolida:**
> - `tecnico/CONFIGURACION_EMAIL.md`
> - `tecnico/RESUMEN_SMTP_GLOBAL.md`

---

## 📋 Tabla de Contenidos

1. [Visión General](#visión-general)
2. [Configuración Básica](#configuración-básica)
3. [Proveedores de Email](#proveedores-de-email)
4. [Arquitectura del Sistema](#arquitectura-del-sistema)
5. [Exportación e Importación SMTP](#exportación-e-importación-smtp)
6. [Seguridad y Mejores Prácticas](#seguridad-y-mejores-prácticas)
7. [Testing y Validación](#testing-y-validación)
8. [Solución de Problemas](#solución-de-problemas)

---

## 🎯 Visión General

El sistema de email de Guardias de Patio permite enviar códigos de recuperación de contraseña a los usuarios. La configuración SMTP es **GLOBAL** y afecta a todos los usuarios del sistema.

### Características Principales

- ✅ **Recuperación de contraseña** por email
- ✅ **Configuración global** desde archivo `.env`
- ✅ **Múltiples proveedores** soportados (Gmail, Outlook, Yahoo, IONOS)
- ✅ **Plantillas HTML** profesionales
- ✅ **Modo desarrollo** para testing sin SMTP
- ✅ **Exportación/Importación** de configuración SMTP

### Componentes

**Servicio de Email:**
- `src/services/email_service.py` - Envío de emails
- `src/presentation/forms/configuracion_form.py` - UI de configuración

**Exportadores:**
- `src/sync/data_exporter.py` - Exportación SFTP
- `src/services/exportador.py` - Exportación manual

---

## 🔧 Configuración Básica

### Paso 1: Crear archivo .env

Si no existe, crea el archivo `.env` en la raíz del proyecto:

```bash
cp .env.example .env
```

### Paso 2: Configurar variables SMTP

Edita `.env` y agrega estas 4 variables obligatorias:

```env
# Configuración SMTP (GLOBAL)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu_email@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx
```

**⚠️ IMPORTANTE:**
- Esta configuración es **GLOBAL** (afecta a TODOS los usuarios)
- El archivo `.env` NO se sube a Git (protegido por `.gitignore`)
- Necesitas recrearlo en cada instalación nueva

---

## 📮 Proveedores de Email

### Gmail (Recomendado)

**Requisitos:**
1. Cuenta de Gmail activa
2. Autenticación de dos factores (2FA) activada
3. App Password generada

**Pasos:**

1. Activar 2FA en tu cuenta de Google:
   - Ve a https://myaccount.google.com/security
   - Activa "Verificación en dos pasos"

2. Generar App Password:
   - Ve a https://myaccount.google.com/apppasswords
   - Selecciona "Correo" y "Otro (nombre personalizado)"
   - Nombra: "Guardias de Patio"
   - Copia la contraseña de 16 caracteres

3. Configurar `.env`:
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu_email@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop  # App Password (sin espacios)
```

**Ventajas:**
- ✅ Muy confiable
- ✅ Límite alto de envíos diarios
- ✅ Buena entregabilidad

---

### Outlook / Hotmail

**Configuración:**

```env
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USER=tu_email@outlook.com
SMTP_PASSWORD=tu_contraseña
```

**Notas:**
- No requiere App Password (puedes usar contraseña normal)
- Si tienes 2FA, necesitas contraseña de aplicación
- Límite: ~300 emails/día

---

### Yahoo Mail

**Configuración:**

```env
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
SMTP_USER=tu_email@yahoo.com
SMTP_PASSWORD=contraseña_de_aplicacion
```

**Requisitos:**
- Generar contraseña de aplicación en configuración de seguridad
- Ve a: https://login.yahoo.com/account/security

---

### IONOS (1&1)

**Configuración:**

```env
SMTP_SERVER=smtp.ionos.es
SMTP_PORT=587
SMTP_USER=tu_email@tudominio.com
SMTP_PASSWORD=tu_contraseña
```

**Notas:**
- Funciona con dominios propios
- Verificar panel de IONOS para credenciales exactas

---

### Otros Proveedores

Para cualquier otro proveedor SMTP:

1. **Consulta documentación** del proveedor para obtener:
   - Servidor SMTP (ej: `smtp.tuproveedor.com`)
   - Puerto (normalmente `587` para TLS o `465` para SSL)
   
2. **Usa credenciales** de la cuenta de email

**Servicios transaccionales profesionales:**
- SendGrid
- Mailgun
- Amazon SES
- Postmark

---

## 🏗️ Arquitectura del Sistema

### Flujo de Envío de Email

```
Usuario olvida contraseña
    ↓
Click en "¿Olvidaste tu contraseña?"
    ↓
Introduce username o email
    ↓
Sistema genera código de 6 dígitos
    ↓
EmailService.enviar_codigo_recuperacion()
    ↓
Conecta a SMTP (desde .env)
    ↓
Envía email con plantilla HTML
    ↓
Usuario recibe email
    ↓
Introduce código en aplicación
    ↓
Cambio de contraseña completado
```

### Servicio de Email

**Archivo:** `src/services/email_service.py`

**Métodos principales:**

```python
class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
    
    def enviar_codigo_recuperacion(self, destinatario: str, codigo: str) -> bool:
        """Envía código de recuperación por email."""
        # Crear mensaje con plantilla HTML
        # Conectar a SMTP
        # Enviar email
        # Manejar errores
```

### Plantilla de Email

El email se envía con una **plantilla HTML profesional**:

**Características:**
- ✅ Logo y colores corporativos
- ✅ Código destacado en una caja visible
- ✅ Versión texto plano alternativa (fallback)
- ✅ Advertencias de seguridad
- ✅ Responsive (se ve bien en móviles)

**Ejemplo visual:**

```
┌─────────────────────────────────┐
│  📧 GUARDIAS DE PATIO            │
├─────────────────────────────────┤
│                                  │
│  Tu código de recuperación es:   │
│                                  │
│  ┌─────────┐                    │
│  │ 123456  │                    │
│  └─────────┘                    │
│                                  │
│  Este código expira en 15 min   │
│                                  │
│  ⚠️ No compartas este código     │
│                                  │
└─────────────────────────────────┘
```

---

## 📦 Exportación e Importación SMTP

### ⚠️ Configuración SMTP es GLOBAL

**Concepto clave:**
- La configuración SMTP NO es por usuario
- Es **compartida por TODOS los usuarios** del sistema
- Se almacena en `.env` (archivo del sistema)
- Al modificarla, afecta a TODOS inmediatamente

### Exportación en JSON

La configuración SMTP se incluye automáticamente en las exportaciones JSON:

**1. Exportación SFTP** (`DataExporter`):

```python
# src/sync/data_exporter.py
@staticmethod
def _export_smtp_config() -> Optional[Dict[str, str]]:
    """Exporta configuración SMTP desde .env"""
    load_dotenv()
    
    smtp_server = os.getenv("SMTP_SERVER", "")
    smtp_port = os.getenv("SMTP_PORT", "")
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    
    if all([smtp_server, smtp_port, smtp_user, smtp_password]):
        return {
            "smtp_server": smtp_server,
            "smtp_port": smtp_port,
            "smtp_user": smtp_user,
            "smtp_password": smtp_password,
        }
    return None
```

**2. Exportación Manual** (`ExportadorDatos`):

```python
# src/services/exportador.py
def exportar_todo(self):
    # ... exportar profesores, zonas, etc ...
    
    # Exportar SMTP (global)
    smtp_config = {
        "smtp_server": os.getenv("SMTP_SERVER", ""),
        "smtp_port": os.getenv("SMTP_PORT", ""),
        "smtp_user": os.getenv("SMTP_USER", ""),
        "smtp_password": os.getenv("SMTP_PASSWORD", ""),
    }
    
    if all(smtp_config.values()):
        datos_completos["smtp_config"] = smtp_config
```

### Importación desde JSON

Al importar, la configuración SMTP se escribe en el archivo `.env`:

```python
@staticmethod
def _import_smtp_config(smtp_data: Dict[str, str]) -> bool:
    """Importa configuración SMTP GLOBAL al .env"""
    
    # Leer .env actual
    env_path = Path(".env")
    lines = env_path.read_text().splitlines() if env_path.exists() else []
    
    # Actualizar o agregar variables SMTP
    updated_lines = []
    smtp_keys = {"SMTP_SERVER", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD"}
    keys_updated = set()
    
    for line in lines:
        if "=" in line:
            key = line.split("=")[0].strip()
            if key in smtp_keys:
                updated_lines.append(f"{key}={smtp_data[key.lower()]}")
                keys_updated.add(key)
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)
    
    # Agregar variables faltantes
    for key in smtp_keys - keys_updated:
        updated_lines.append(f"{key}={smtp_data[key.lower()]}")
    
    # Escribir .env actualizado
    env_path.write_text("\n".join(updated_lines))
    return True
```

### Modal de Advertencia

**Ubicación:** `src/presentation/forms/configuracion_form.py`

Antes de permitir modificar la configuración SMTP, se muestra un **modal de advertencia**:

```
┌─────────────────────────────────────────┐
│ ⚠️ ADVERTENCIA: Configuración SMTP      │
│    Global                                │
├─────────────────────────────────────────┤
│                                          │
│ La configuración SMTP es compartida     │
│ por TODOS los usuarios del sistema.     │
│                                          │
│ Modificar estos valores puede:          │
│                                          │
│ • Impedir que otros usuarios recuperen  │
│   sus contraseñas por email              │
│ • Afectar a todas las notificaciones    │
│ • Causar errores en envío de emails     │
│                                          │
│ Estos cambios afectarán a TODOS los     │
│ usuarios inmediatamente.                 │
│                                          │
│ ¿Estás seguro de continuar?             │
│                                          │
│  [Entiendo los riesgos, continuar]      │
│  [Cancelar] ← predeterminado             │
└─────────────────────────────────────────┘
```

**Implementación:**

```python
def _mostrar_advertencia_smtp_global(self) -> bool:
    """Muestra advertencia sobre configuración SMTP global."""
    msg = QMessageBox(self)
    msg.setIcon(QMessageBox.Icon.Warning)
    msg.setWindowTitle("⚠️ Configuración SMTP Global")
    msg.setText("<h3>⚠️ ADVERTENCIA: Configuración SMTP Global</h3>")
    msg.setInformativeText(
        "<p><b>La configuración SMTP es compartida por TODOS...</b></p>"
        # ... resto del mensaje ...
    )
    msg.setDefaultButton(QMessageBox.StandardButton.No)
    return msg.exec() == QMessageBox.StandardButton.Yes
```

**Se muestra:**
1. Al hacer clic en "🔓 Modificar Configuración SMTP"
2. Al intentar guardar cambios en SMTP

---

## 🔒 Seguridad y Mejores Prácticas

### Protección del Archivo .env

**Reglas de oro:**

1. ✅ **NUNCA** subir `.env` a Git
   ```bash
   # Verificar .gitignore
   cat .gitignore | grep .env
   # Debe aparecer: .env
   ```

2. ✅ **Usar App Passwords**, no contraseñas normales
   - Gmail: App Password obligatoria
   - Outlook: Recomendada si tienes 2FA
   - Yahoo: Contraseña de aplicación

3. ✅ **Activar 2FA** en tu cuenta de email principal

4. ✅ **Limitar permisos** de la cuenta SMTP
   - Usar cuenta dedicada solo para la aplicación
   - No usar cuenta personal principal

### Cuenta Dedicada (Recomendado para Producción)

**Mejor práctica:**

```
Crear cuenta: guardias.sistema@gmail.com
  ↓
Solo para envío de emails de la app
  ↓
Limitar acceso a esta cuenta
  ↓
Monitorizar uso
```

**Ventajas:**
- ✅ Seguridad: Si credenciales se comprometen, solo afecta a la app
- ✅ Organización: Emails separados de correo personal
- ✅ Límites: Control de rate limiting específico
- ✅ Auditoría: Historial claro de emails enviados

### Rate Limiting

**Límites típicos por proveedor:**

| Proveedor | Emails/día | Emails/hora |
|-----------|------------|-------------|
| Gmail     | 500        | 100         |
| Outlook   | 300        | 30          |
| Yahoo     | 500        | 50          |
| IONOS     | Variable   | Variable    |
| SendGrid  | Ilimitado* | Configurable |

*Según plan contratado

**Implementar en la app (futuro):**

```python
# Contador de emails enviados
emails_enviados_hoy = 0
LIMITE_DIARIO = 400  # Margen de seguridad

def enviar_email():
    global emails_enviados_hoy
    if emails_enviados_hoy >= LIMITE_DIARIO:
        raise Exception("Límite diario alcanzado")
    # ... enviar email ...
    emails_enviados_hoy += 1
```

---

## 🧪 Testing y Validación

### Modo Desarrollo

Si **NO** configuras SMTP, el sistema funciona en **modo desarrollo**:

```python
if not all([smtp_server, smtp_port, smtp_user, smtp_password]):
    # Modo desarrollo: Mostrar código en pantalla
    logger.warning("SMTP no configurado - Modo desarrollo")
    mostrar_dialogo(f"Código de recuperación: {codigo}")
    return True
```

**Características modo desarrollo:**
- ✅ Código se muestra en ventana emergente
- ✅ Útil para pruebas locales
- ✅ No requiere configuración SMTP
- ⚠️ **NO usar en producción**

### Verificar Configuración

**Desde la aplicación:**

1. Ir a configuración SMTP (si existe UI)
2. Click en "Probar configuración"
3. Verifica que se envíe email de prueba

**Desde código:**

```python
# test_smtp.py
from src.services.email_service import EmailService

service = EmailService()
exito = service.enviar_codigo_recuperacion(
    destinatario="tu_email@gmail.com",
    codigo="123456"
)

if exito:
    print("✅ Email enviado correctamente")
else:
    print("❌ Error al enviar email")
```

### Verificar en Producción

**Checklist:**

1. ✅ Archivo `.env` existe y tiene las 4 variables
2. ✅ Credenciales son correctas (probar login en webmail)
3. ✅ Puerto correcto (587 para TLS, 465 para SSL)
4. ✅ Firewall permite conexión al puerto
5. ✅ Aplicación puede leer archivo `.env`
6. ✅ Enviar email de prueba desde la app

---

## 🚨 Solución de Problemas

### Error: "Email no configurado"

**Causa:** Variables SMTP faltantes en `.env`

**Solución:**

```bash
# 1. Verificar que .env existe
ls -la .env

# 2. Ver contenido
cat .env | grep SMTP

# 3. Debe tener las 4 variables:
# SMTP_SERVER=...
# SMTP_PORT=...
# SMTP_USER=...
# SMTP_PASSWORD=...

# 4. Si falta alguna, editar
nano .env
```

---

### Error: "Error de autenticación SMTP"

**Causas posibles:**
- Credenciales incorrectas
- No usar App Password en Gmail
- 2FA no configurado

**Soluciones:**

**Para Gmail:**
1. Verifica que 2FA esté activo
2. Regenera App Password
3. Copia exactamente (sin espacios)

**Para otros:**
1. Prueba login en webmail del proveedor
2. Verifica que sea contraseña correcta
3. Revisa si requiere contraseña de aplicación

---

### Error: "Connection timed out"

**Causas posibles:**
- Sin internet
- Firewall bloqueando puerto
- Servidor SMTP caído

**Diagnóstico:**

```bash
# 1. Verificar conectividad
ping smtp.gmail.com

# 2. Probar puerto
nc -zv smtp.gmail.com 587

# 3. Verificar firewall
# macOS: Preferencias del Sistema > Seguridad > Firewall
# Windows: Panel de Control > Firewall de Windows
```

**Soluciones:**
- Verificar conexión a internet
- Temporalmente desactivar firewall/antivirus
- Cambiar a puerto 465 (SSL) si 587 (TLS) falla
- Contactar administrador de red si en empresa

---

### Error: "SMTPServerDisconnected"

**Causa:** Conexión cerrada inesperadamente

**Solución:**

```python
# Añadir reintentos automáticos
def enviar_con_reintentos(destinatario, codigo, max_intentos=3):
    for intento in range(max_intentos):
        try:
            return enviar_codigo_recuperacion(destinatario, codigo)
        except SMTPServerDisconnected:
            if intento < max_intentos - 1:
                time.sleep(2)  # Esperar antes de reintentar
                continue
            raise
```

---

### Emails no llegan (van a spam)

**Causas:**
- Falta configuración SPF/DKIM
- Email parece spam
- Dominio del remitente no verificado

**Soluciones:**

1. **Verificar carpeta spam** del destinatario

2. **Mejorar contenido del email:**
   - Asunto claro y profesional
   - Contenido relevante
   - Evitar palabras spam ("gratis", "urgente", etc.)

3. **Configurar SPF/DKIM** (si usas dominio propio):
   - Contactar proveedor de hosting
   - Configurar registros DNS

4. **Usar servicio transaccional:**
   - SendGrid, Mailgun, etc.
   - Tienen mejor deliverability

---

## 🔮 Mejoras Futuras

### v3.0 - UI de Configuración SMTP

- [ ] Panel de configuración SMTP en la aplicación
- [ ] Botón "Probar configuración" (envía email de prueba)
- [ ] Validación en tiempo real de credenciales
- [ ] Historial de emails enviados

### v3.1 - Seguridad Avanzada

- [ ] Cifrado de credenciales en `.env`
- [ ] Rotación automática de passwords
- [ ] Auditoría de accesos a configuración SMTP
- [ ] Alertas de uso sospechoso

### v3.2 - Funcionalidades Adicionales

- [ ] Plantillas de email personalizables
- [ ] Múltiples idiomas en emails
- [ ] Attachments (adjuntar PDFs, etc.)
- [ ] Rate limiting configurableconfigurable
- [ ] Cola de emails (retry automático)

### v3.3 - Servicios Transaccionales

- [ ] Integración con SendGrid
- [ ] Integración con Mailgun
- [ ] Integración con Amazon SES
- [ ] Selector de proveedor en UI

---

## 📚 Referencias

### Documentación Oficial

- [Gmail SMTP Settings](https://support.google.com/mail/answer/7126229)
- [Outlook SMTP Settings](https://support.microsoft.com/en-us/office/pop-imap-and-smtp-settings-8361e398-8af4-4e97-b147-6c6c4ac95353)
- [Python smtplib](https://docs.python.org/3/library/smtplib.html)
- [email.mime](https://docs.python.org/3/library/email.mime.html)

### Archivos del Sistema

**Configuración:**
- `.env` - Credenciales SMTP (protegido)
- `.env.example` - Plantilla

**Código:**
- `src/services/email_service.py` - Servicio de envío
- `src/sync/data_exporter.py` - Exportación SFTP
- `src/services/exportador.py` - Exportación manual
- `src/presentation/forms/configuracion_form.py` - UI configuración

---

## ✅ Checklist de Implementación

### Para Desarrolladores

- [x] EmailService implementado
- [x] Plantilla HTML profesional
- [x] Modo desarrollo sin SMTP
- [x] Exportación SMTP en DataExporter
- [x] Exportación SMTP en ExportadorDatos
- [x] Importación SMTP desde JSON
- [x] Modal de advertencia SMTP global
- [x] Logging de envíos
- [x] Manejo de errores
- [x] Documentación completa

### Para Usuarios

- [ ] Crear archivo `.env`
- [ ] Configurar variables SMTP
- [ ] Generar App Password (si Gmail)
- [ ] Probar envío de email
- [ ] Verificar recepción
- [ ] Revisar carpeta spam si no llega
- [ ] Backup de configuración

---

## 🎉 Conclusión

La configuración SMTP está **completamente funcional** y lista para producción.

### Lo Que Funciona ✅

✅ Envío de códigos de recuperación  
✅ Múltiples proveedores soportados  
✅ Plantillas HTML profesionales  
✅ Modo desarrollo para testing  
✅ Exportación/Importación en JSON  
✅ Advertencias de seguridad  
✅ Manejo robusto de errores  

### Próxima Acción

1. **Configurar** `.env` con credenciales SMTP
2. **Probar** recuperación de contraseña
3. **Verificar** que emails lleguen
4. **Exportar** configuración como backup

---

**Estado:** ✅ Completado y Validado  
**Desarrollado:** Octubre 2025  
**Versión:** 2.9.0  
**Última actualización:** 28 de octubre de 2025
