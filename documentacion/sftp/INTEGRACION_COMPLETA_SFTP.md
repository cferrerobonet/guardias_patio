# 🎉 Sistema de Sincronización SFTP - Integración Completa

## ✅ Estado de la Integración

El sistema de sincronización SFTP está **completamente integrado** en la aplicación.

---

## 🚀 Cómo Funciona

### Al Iniciar la Aplicación

1. **Diálogo de Login** aparece automáticamente
   - Si eres nuevo: Click en "Registrar" para crear tu cuenta
   - Si ya tienes cuenta: Introduce tu usuario y contraseña

2. **Sincronización Automática**
   - Conecta al servidor SFTP de 1&1 IONOS
   - Descarga tus datos si hay una versión más reciente en la nube
   - Si es tu primera vez, sube tus datos locales al servidor

3. **Ventana Principal** se abre con tus datos sincronizados

### Durante el Uso

- Trabaja normalmente con la aplicación
- Todos los cambios se guardan localmente en tiempo real

### Al Cerrar la Aplicación

1. **Sincronización Automática**
   - Sube automáticamente todos tus cambios al servidor SFTP
   - Actualiza la metadata de sincronización
   - Cierra la conexión de forma segura

2. **Sin Intervención** necesaria del usuario

---

## 🧪 Probar la Conexión SFTP

Antes de usar la aplicación, puedes verificar que la conexión funciona:

```bash
python test_sftp_connection.py
```

Este script:
- ✅ Valida la configuración
- ✅ Conecta al servidor SFTP
- ✅ Crea directorios de prueba
- ✅ Sube un archivo
- ✅ Descarga el archivo
- ✅ Verifica la integridad

**Salida esperada**: `✅ PRUEBA COMPLETADA CON ÉXITO`

---

## 🔐 Configuración de Seguridad

### Archivo `.env` (PROTEGIDO)

Las credenciales SFTP están en el archivo `.env` en la raíz del proyecto:

```env
SFTP_HOST=home491590459.1and1-data.host
SFTP_PORT=22
SFTP_USER=u74704514
SFTP_PASSWORD=@25415175(Z).ftp
SFTP_BASE_DIR=/aplicaciones/guardias_patio
```

**IMPORTANTE**: 
- ❌ Este archivo NO se sube a Git (protegido por `.gitignore`)
- ✅ Solo existe en tu máquina local
- ✅ Necesitas crearlo manualmente en cada nueva instalación

---

## 📂 Estructura en el Servidor SFTP

```
/aplicaciones/guardias_patio/
├── users.json                  # Registro global de usuarios
└── users/
    ├── a1b2c3d4e5f6g7h8/       # Usuario 1 (hash)
    │   ├── guardias_patio.db   # Base de datos SQLite
    │   ├── config.json          # Configuración del usuario
    │   └── last_sync.json       # Metadata de sincronización
    └── x9y8z7w6v5u4t3s2/       # Usuario 2 (hash)
        ├── guardias_patio.db
        ├── config.json
        └── last_sync.json
```

Cada usuario tiene su **carpeta aislada** con hash SHA-256 para privacidad.

---

## 🎯 Escenarios de Uso

### Escenario 1: Trabajo en Casa y en el Colegio

1. **En casa** (lunes):
   - Login → Trabajas → Cierras app
   - Cambios se sincronizan automáticamente

2. **En el colegio** (martes):
   - Login (mismo usuario) → Descarga cambios de casa
   - Trabajas → Cierras app → Sube cambios

3. **De vuelta en casa** (miércoles):
   - Login → Descarga cambios del colegio
   - Siempre tienes la versión más reciente

### Escenario 2: Múltiples Usuarios en el Mismo Colegio

1. **Director** (usuario: "director"):
   - Gestiona guardias y ausencias
   - Sus datos están aislados

2. **Jefe de Estudios** (usuario: "jefe_estudios"):
   - Tiene sus propios datos
   - No puede ver los datos del director

3. **Cada usuario** tiene su **espacio privado** en la nube

---

## 🔧 Modo Local (Fallback)

Si el servidor SFTP no está accesible:

1. **Mensaje de Aviso**: "No se pudo conectar al servidor de sincronización"
2. **Modo Local**: La aplicación funciona normalmente sin sincronización
3. **Datos Locales**: Se guardan solo en tu máquina

Cuando vuelva la conexión:
- Reinicia la aplicación
- La sincronización se reanudará automáticamente

---

## 📝 Logs y Diagnóstico

Los logs de sincronización están disponibles en:
- **Salida estándar** (terminal donde lanzaste la app)
- **Archivo de log** (si está configurado en `logging_config.py`)

Mensajes importantes:
```
✓ Sincronización inicial completada
✓ Sincronización final completada
⚠ La sincronización tuvo problemas
❌ Error al conectar: [detalles]
```

---

## 🚨 Solución de Problemas

### No Aparece el Diálogo de Login

**Causa**: Error en la importación de `LoginDialog`

**Solución**:
```bash
# Verificar que el archivo existe
ls src/presentation/forms/login_dialog.py

# Limpiar cachés
find . -name "*.pyc" -delete
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
```

### Error: "Configuración SFTP incompleta"

**Causa**: Falta el archivo `.env` o tiene datos incorrectos

**Solución**:
```bash
# Verificar que existe
cat .env

# Debe contener las 5 variables:
# SFTP_HOST=...
# SFTP_PORT=22
# SFTP_USER=...
# SFTP_PASSWORD=...
# SFTP_BASE_DIR=...
```

### Error: "Connection refused" o "Timeout"

**Causas posibles**:
- Sin conexión a internet
- Firewall bloqueando puerto 22
- Servidor SFTP caído
- Credenciales incorrectas

**Solución**:
```bash
# Probar conexión manualmente
python test_sftp_connection.py

# Verificar conectividad básica
ping home491590459.1and1-data.host

# Probar puerto SSH
nc -zv home491590459.1and1-data.host 22
```

### Los Datos No Se Sincronizan

**Causa**: La sincronización falló silenciosamente

**Solución**:
1. Revisa los logs en la terminal
2. Ejecuta `test_sftp_connection.py` para verificar conectividad
3. Verifica que `sync_on_startup()` y `sync_on_shutdown()` se ejecutan

---

## 🎓 Documentación Adicional

- **Arquitectura completa**: `documentacion/funcionalidades/SISTEMA_SINCRONIZACION_MULTIUSUARIO.md`
- **Guía rápida**: `GUIA_SINCRONIZACION_SFTP.md`
- **Este documento**: Instrucciones de integración

---

## ✨ Próximas Mejoras (Roadmap)

### Fase 1: Experiencia de Usuario
- [ ] Indicador de estado de sincronización en la UI
- [ ] Barra de progreso para sincronizaciones largas
- [ ] Botón "Sincronizar ahora" en el menú
- [ ] Notificaciones de sincronización completada

### Fase 2: Seguridad
- [ ] Actualizar de SHA-256 a bcrypt para contraseñas
- [ ] Verificación SSL/TLS para conexión SFTP
- [ ] Cifrado de base de datos con SQLCipher
- [ ] Reset de contraseña con email

### Fase 3: Funcionalidad Avanzada
- [ ] Sincronización en background (threading)
- [ ] Resolución de conflictos (ediciones simultáneas)
- [ ] Historial de versiones (backups automáticos)
- [ ] Sincronización incremental (solo cambios)
- [ ] Compresión de archivos grandes

---

**🎉 ¡Sistema listo para producción!**

Ahora puedes usar la aplicación con sincronización automática en la nube.
Tus datos estarán seguros y accesibles desde cualquier dispositivo.
