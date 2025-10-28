# 🔄 Guía Completa de Sincronización y Multi-usuario

**Versión:** 2.8+  
**Última actualización:** Octubre 2025

---

## 📋 Tabla de Contenidos

1. [Visión General](#visión-general)
2. [Sistema Multi-usuario](#sistema-multi-usuario)
3. [Sistema de Bloqueo de Sesión](#sistema-de-bloqueo-de-sesión)
4. [Lógica de Sincronización](#lógica-de-sincronización)
5. [Formatos y Estructuras JSON](#formatos-y-estructuras-json)
6. [Sincronización SFTP](#sincronización-sftp)
7. [Casos de Uso](#casos-de-uso)
8. [Solución de Problemas](#solución-de-problemas)

---

## 🎯 Visión General

El sistema de Guardias de Patio implementa un **sistema robusto de sincronización multi-usuario** que permite:

- ✅ Múltiples usuarios trabajando con sus propios datos
- ✅ Sincronización automática con servidor SFTP
- ✅ Bloqueo de sesiones concurrentes para prevenir conflictos
- ✅ Recuperación de contraseña por email
- ✅ Aislamiento completo de datos entre usuarios

### Arquitectura de Datos

```
Servidor SFTP
└── users/
    ├── <hash_usuario_1>/
    │   ├── guardias_patio.db
    │   ├── session.lock
    │   └── last_sync.json
    └── <hash_usuario_2>/
        ├── guardias_patio.db
        ├── session.lock
        └── last_sync.json

Local
└── data/
    └── users/
        └── <hash_usuario>/
            ├── guardias_patio.db
            ├── session.lock (copia local)
            └── sync/
                ├── last_sync.json
                └── pending_uploads/
```

---

## 👥 Sistema Multi-usuario

### Registro de Usuarios

Cada usuario debe registrarse con:
- **Username**: Identificador único (alfanumérico, 3-50 caracteres)
- **Email**: Obligatorio para recuperación de contraseña (validado con @ y .)
- **Password**: Mínimo 4 caracteres, hasheada con SHA-256

**Archivo:** `users.json` (raíz del proyecto)

```json
{
  "users": [
    {
      "username": "cferrerobonet",
      "password_hash": "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",
      "email": "cferrerobonet@gmail.com",
      "created_at": "2025-10-20T10:30:00"
    }
  ]
}
```

### Hash de Usuario

Cada usuario tiene un **hash único** generado a partir de su username:

```python
import hashlib
user_hash = hashlib.sha256(username.encode()).hexdigest()[:16]
# Ejemplo: "cferrerobonet" → "66f06c9433d74e80"
```

Este hash se usa para:
- Nombrar carpetas de datos locales: `data/users/66f06c9433d74e80/`
- Carpetas en SFTP: `users/66f06c9433d74e80/`
- Aislamiento completo de datos entre usuarios

### Base de Datos por Usuario

Cada usuario tiene su propia base de datos SQLite:

**Ruta local:** `data/users/<hash>/guardias_patio.db`  
**Ruta SFTP:** `users/<hash>/guardias_patio.db`

Contiene:
- Profesores
- Zonas
- Guardias
- Configuración del curso
- Festivos

**Total aislamiento**: Un usuario NO puede ver datos de otro usuario.

---

## 🔒 Sistema de Bloqueo de Sesión

### Prevención de Sesiones Concurrentes

Para evitar conflictos de datos cuando un usuario intenta iniciar sesión en **múltiples dispositivos simultáneamente**, el sistema implementa un **bloqueo de sesión**.

### Archivo session.lock

**Ubicación SFTP:** `users/<hash>/session.lock`

```json
{
  "username": "cferrerobonet",
  "machine_name": "MacBook-Pro-de-CarlosFB.local",
  "ip_address": "192.168.1.44",
  "locked_at": "2025-10-26T10:30:00.123456",
  "last_heartbeat": "2025-10-26T10:35:00.456789",
  "process_id": 12345
}
```

### Flujo de Bloqueo

1. **Usuario intenta iniciar sesión**
2. **Sistema descarga** `session.lock` del servidor SFTP
3. **Verifica si hay un bloqueo activo**:
   - Si `last_heartbeat` < 5 minutos → Sesión activa, **denegar acceso**
   - Si `last_heartbeat` > 5 minutos → Sesión caduca, **permitir acceso**
4. **Si se permite**, el sistema:
   - Crea nuevo `session.lock` con datos actuales
   - Sube el archivo al servidor SFTP
   - Inicia **heartbeat** cada 30 segundos

### Heartbeat

Cada 30 segundos, la aplicación **actualiza** `last_heartbeat` en el servidor para indicar que la sesión sigue activa.

**Timer en:** `SessionLock._start_heartbeat_timer()`

```python
self.heartbeat_timer = QTimer()
self.heartbeat_timer.timeout.connect(self._heartbeat)
self.heartbeat_timer.start(30000)  # 30 segundos
```

### Liberación del Bloqueo

Al cerrar la aplicación correctamente:
1. **Detiene el heartbeat** timer
2. **Elimina** `session.lock` del servidor SFTP
3. **Permite** que otro dispositivo pueda iniciar sesión

### Forzar Liberación (Opcional)

Si un usuario cierra la app abruptamente (crash, apagado forzado), el bloqueo queda activo. Para liberarlo:

**Opción 1:** Esperar 5 minutos (timeout automático)  
**Opción 2:** Eliminar manualmente `session.lock` del servidor SFTP

---

## 🔄 Lógica de Sincronización

### Inicialización

Al iniciar sesión, el sistema:

1. **Descarga la base de datos** del servidor SFTP (si existe)
2. **Sobrescribe la BD local** con la versión del servidor
3. **Crea session.lock** para bloquear la sesión
4. **Inicia heartbeat** timer

### Sincronización Continua

Durante el uso de la aplicación:

- **Cada 30 segundos**: Heartbeat (actualiza `last_heartbeat`)
- **Al guardar cambios**: No se sube automáticamente (solo local)
- **Al cerrar sesión**: Sube la BD actualizada al servidor

### Cierre de Sesión

Al cerrar la aplicación:

1. **Sube la base de datos** local al servidor SFTP
2. **Elimina** `session.lock` del servidor
3. **Detiene** el heartbeat timer
4. **Cierra** conexión SFTP

### Conflictos

**El sistema PREVIENE conflictos** mediante el bloqueo de sesión. No es posible que dos usuarios modifiquen la misma BD simultáneamente.

---

## 📄 Formatos y Estructuras JSON

### Configuración SFTP

**Archivo:** `.env` (raíz del proyecto)

```env
SFTP_HOST=home491590459.1and1-data.host
SFTP_PORT=22
SFTP_USERNAME=u109936159
SFTP_PASSWORD=tu_password_aqui
SFTP_BASE_DIR=/guardias_patio
```

### Metadatos de Sincronización

**Archivo:** `users/<hash>/last_sync.json`

```json
{
  "last_sync_time": "2025-10-26T10:45:00.123456",
  "sync_type": "full",
  "status": "success",
  "files_synced": [
    "guardias_patio.db"
  ]
}
```

### Importar/Exportar Datos

El sistema permite **exportar todos los datos** a JSON para backup o migración:

**Estructura del JSON de exportación:**

```json
{
  "version": "2.8.0",
  "exported_at": "2025-10-26T10:50:00",
  "user": "cferrerobonet",
  
  "configuracion": {
    "fecha_inicio": "2024-09-09",
    "fecha_fin": "2025-06-20",
    "recreos_manana": 2,
    "recreos_tarde": 2,
    "festivos": ["2024-12-25", "2025-01-01"]
  },
  
  "profesores": [
    {
      "nombre_completo": "García López, Juan",
      "email_corporativo": "juan.garcia@epla.es",
      "horas_contrato": 30,
      "porcentaje_jornada": 100.0,
      "turno": "completo",
      "restricciones": {
        "dias_bloqueados": [],
        "recreos_bloqueados": []
      }
    }
  ],
  
  "zonas": [
    {
      "nombre": "Patio Central",
      "descripcion": "Zona principal del centro"
    }
  ],
  
  "guardias": [
    {
      "profesor": "García López, Juan",
      "zona": "Patio Central",
      "fecha": "2024-10-15",
      "recreo": "M1",
      "es_sustitucion": false
    }
  ]
}
```

---

## ☁️ Sincronización SFTP

### Configuración

El sistema usa **SFTP (SSH File Transfer Protocol)** para sincronización segura.

**Servidor recomendado:** IONOS (home491590459.1and1-data.host:22)

### Estructura de Carpetas

```
/guardias_patio/              # Base dir configurado en .env
└── users/
    └── <hash_usuario>/
        ├── guardias_patio.db  # Base de datos
        ├── session.lock       # Bloqueo de sesión
        └── last_sync.json     # Metadatos de sync
```

### Operaciones SFTP

#### Descarga de Base de Datos

```python
def download_database(self, local_path: Path):
    remote_path = f"{self.base_dir}/users/{self.user_hash}/guardias_patio.db"
    self.sftp.get(str(remote_path), str(local_path))
```

#### Subida de Base de Datos

```python
def upload_database(self, local_path: Path):
    remote_path = f"{self.base_dir}/users/{self.user_hash}/guardias_patio.db"
    self.sftp.put(str(local_path), str(remote_path))
```

#### Gestión de session.lock

```python
# Descargar
def download_lock(self) -> dict:
    remote_path = f"{self.base_dir}/users/{self.user_hash}/session.lock"
    content = self.sftp.file(str(remote_path)).read()
    return json.loads(content)

# Subir
def upload_lock(self, lock_data: dict):
    remote_path = f"{self.base_dir}/users/{self.user_hash}/session.lock"
    content = json.dumps(lock_data, indent=2)
    self.sftp.file(str(remote_path)).write(content)

# Eliminar
def delete_lock(self):
    remote_path = f"{self.base_dir}/users/{self.user_hash}/session.lock"
    self.sftp.remove(str(remote_path))
```

### Documentación Detallada SFTP

Para información más detallada sobre la implementación SFTP, ver:

📁 **[documentacion/sftp/](sftp/)** - Documentación completa de SFTP:
- GUIA_SINCRONIZACION_SFTP.md
- INTEGRACION_COMPLETA_SFTP.md
- NOTA_RUTAS_SFTP.md
- RESUMEN_INTEGRACION_SFTP.md

---

## 📚 Casos de Uso

### Caso 1: Usuario trabajando en casa y en el trabajo

**Escenario:**
- Usuario `carlos` trabaja en MacBook en casa
- Quiere continuar en PC del trabajo

**Flujo:**

1. **En casa (MacBook)**:
   - Inicia sesión → Descarga BD del servidor
   - Trabaja, hace cambios
   - Cierra sesión → Sube BD al servidor

2. **En el trabajo (PC)**:
   - Inicia sesión → Descarga BD actualizada del servidor
   - Trabaja con los datos más recientes
   - Cierra sesión → Sube cambios al servidor

3. **De vuelta en casa**:
   - Inicia sesión → Descarga BD con cambios del trabajo
   - Continúa trabajando

✅ **Datos siempre sincronizados entre dispositivos**

### Caso 2: Intento de sesión concurrente

**Escenario:**
- Usuario `carlos` tiene sesión abierta en MacBook
- Intenta abrir sesión en PC simultáneamente

**Flujo:**

1. **MacBook**: Sesión activa (heartbeat cada 30s)
2. **PC**: Intenta iniciar sesión
3. **Sistema**: Detecta `session.lock` activo (last_heartbeat < 5 min)
4. **PC**: **Muestra mensaje de error** y denieg acceso

```
❌ Sesión bloqueada
Usuario 'carlos' ya está activo en:
  Equipo: MacBook-Pro-de-Carlos.local
  IP: 192.168.1.44
  Desde: 2025-10-26T10:30:00
  Último heartbeat: 2025-10-26T10:35:00
```

5. **Solución**: Cerrar sesión en MacBook primero

✅ **Prevención de conflictos de datos**

### Caso 3: Aplicación crashea sin cerrar sesión

**Escenario:**
- Usuario cierra MacBook abruptamente
- Session.lock queda activo en servidor

**Solución Automática:**
- Esperar **5 minutos**
- Sistema detecta `last_heartbeat` antiguo
- Permite nueva sesión (timeout automático)

**Solución Manual:**
- Eliminar `session.lock` del servidor SFTP manualmente

---

## 🛠️ Solución de Problemas

### Error: "No se puede conectar al servidor SFTP"

**Causa:** Configuración SFTP incorrecta en `.env`

**Solución:**
1. Verificar credenciales en `.env`
2. Probar conexión SFTP con cliente (FileZilla, Cyberduck)
3. Verificar firewall/VPN

### Error: "Sesión bloqueada"

**Causa:** Sesión activa en otro dispositivo

**Solución:**
1. Cerrar sesión en el otro dispositivo
2. O esperar 5 minutos (timeout automático)
3. O eliminar `session.lock` manualmente del servidor

### Error: "No se pudo descargar la base de datos"

**Causa:** Archivo no existe en servidor (primer uso) o error de conexión

**Solución:**
1. **Primer uso**: Normal, se creará BD nueva local
2. **Usuario existente**: Verificar ruta SFTP y permisos

### Base de datos corrupta

**Causa:** Interrupción durante sincronización

**Solución:**
1. Descargar BD del servidor SFTP manualmente
2. Reemplazar BD local en `data/users/<hash>/guardias_patio.db`
3. Reiniciar aplicación

### Datos perdidos después de sincronizar

**Causa:** Sobrescritura accidental

**Prevención:**
- El sistema **siempre descarga** del servidor al iniciar sesión
- Si trabajas offline, **no cierres sesión** hasta tener conexión

**Recuperación:**
1. Buscar backups en `data/users/<hash>/backups/` (si existen)
2. Contactar soporte para recuperar del servidor

---

## 🔐 Seguridad

### Passwords

- Hasheadas con **SHA-256**
- Nunca se almacenan en texto plano
- Recuperación por email con código temporal

### Transmisión de Datos

- **SFTP con TLS** (conexión cifrada)
- Puerto 22 (SSH)
- Autenticación por usuario/password

### Aislamiento de Datos

- Cada usuario tiene su propio hash único
- Carpetas separadas en servidor y local
- Imposible acceder a datos de otros usuarios

---

## 📊 Estadísticas de Uso

**Implementación completada:** Sprint 8 (Octubre 2025)

**Características:**
- ✅ Autenticación de usuarios
- ✅ Registro con email obligatorio
- ✅ Recuperación de contraseña por email
- ✅ Sistema multi-usuario completo
- ✅ Sincronización SFTP automática
- ✅ Bloqueo de sesiones concurrentes
- ✅ Heartbeat de sesión
- ✅ Importar/Exportar JSON

**Archivos de código:**
- `src/auth/user_auth.py` - Autenticación
- `src/sync/session_lock.py` - Bloqueo de sesión
- `src/sync/sync_manager.py` - Gestor de sincronización
- `src/sync/backend_factory.py` - Factory de backends
- `src/sync/sftp_backend.py` - Backend SFTP
- `src/services/email_service.py` - Servicio de email
- `src/presentation/forms/login_dialog.py` - Diálogo de login
- `src/presentation/forms/forgot_password_dialog.py` - Recuperar contraseña
- `src/presentation/forms/reset_password_dialog.py` - Resetear contraseña

---

**Última actualización:** 26 de Octubre de 2025  
**Versión del sistema:** 2.8+  
**Estado:** ✅ Producción - Estable
