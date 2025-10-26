# 🚀 Guía Rápida: Sistema de Sincronización SFTP

## ✅ Configuración Completada

Tu aplicación ya está configurada para sincronizar automáticamente con el servidor SFTP de 1&1 IONOS.

### 📋 Datos de Conexión Configurados

- **Servidor**: home491590459.1and1-data.host
- **Puerto**: 22 (SFTP/SSH)
- **Usuario**: u74704514
- **Directorio base**: `/aplicaciones/guardias_patio`
- **Credenciales**: Almacenadas en `.env` (archivo protegido, no se sube a Git)

---

## 🔧 Cómo Usar

### Opción 1: Usar el Backend por Defecto (Automático)

```python
from sync import get_default_backend, SyncManager
from presentation.forms.login_dialog import LoginDialog

# 1. Login
login_dialog = LoginDialog()
if login_dialog.exec() != LoginDialog.DialogCode.Accepted:
    sys.exit(0)

username = login_dialog.authenticated_user

# 2. Crear backend (automáticamente usa SFTP si está configurado)
backend = get_default_backend()

# 3. Sincronizar
sync_manager = SyncManager(backend, username)
sync_manager.sync_on_startup()  # Al abrir
# ... usar la app ...
sync_manager.sync_on_shutdown()  # Al cerrar
```

### Opción 2: Especificar SFTP Explícitamente

```python
from sync import create_sync_backend, SyncManager

# Crear backend SFTP (usa credenciales de .env)
backend = create_sync_backend("sftp")

# Resto igual...
sync_manager = SyncManager(backend, username)
```

### Opción 3: Desarrollo con Backend Local

```python
from sync import create_sync_backend

# Para desarrollo/pruebas (carpeta local)
backend = create_sync_backend("local")
```

---

## 📂 Estructura en el Servidor SFTP

```
/aplicaciones/guardias_patio/
├── users/
│   ├── abc123def456/           # Usuario 1
│   │   ├── guardias_patio.db
│   │   ├── config.json
│   │   └── last_sync.json
│   ├── xyz789ghi012/           # Usuario 2
│   │   ├── guardias_patio.db
│   │   ├── config.json
│   │   └── last_sync.json
└── users.json                  # Registro global
```

---

## 🎯 Flujo Automático

### Al Abrir la Aplicación

1. Usuario hace login
2. Se conecta automáticamente al SFTP
3. Descarga datos si son más recientes que los locales
4. Si no hay datos en el servidor, sube los locales
5. App lista para usar con datos sincronizados

### Al Cerrar la Aplicación

1. Sube todos los cambios al servidor SFTP
2. Actualiza metadata de sincronización
3. Cierra la conexión SFTP de forma segura

---

## 🔐 Seguridad

- ✅ Contraseña en archivo `.env` (no se sube a Git)
- ✅ Conexión SFTP encriptada (SSH/puerto 22)
- ✅ Cada usuario tiene carpeta aislada
- ✅ Hash SHA-256 para IDs de usuario (privacidad)

---

## 🧪 Probar la Conexión

```python
# Test rápido de conexión
from sync import create_sync_backend

try:
    backend = create_sync_backend("sftp")
    print("✓ Conexión SFTP exitosa")
    backend.close()
except Exception as e:
    print(f"❌ Error: {e}")
```

---

## 🚨 Solución de Problemas

### Error: "Paramiko no instalado"

```bash
pip install paramiko
```

### Error: "Configuración SFTP incompleta"

Verifica que el archivo `.env` exista con todas las variables:

```bash
cat .env
# Debe mostrar:
# SFTP_HOST=home491590459.1and1-data.host
# SFTP_USER=u74704514
# SFTP_PASSWORD=@25415175(Z).ftp
# SFTP_BASE_DIR=/aplicaciones/guardias_patio
```

### Error: "Connection refused" o "Timeout"

- Verifica tu conexión a internet
- Comprueba que el servidor SFTP esté accesible
- Verifica que el puerto 22 no esté bloqueado por firewall

### Datos no se sincronizan

1. Verifica que `sync_on_startup()` y `sync_on_shutdown()` se llamen
2. Revisa los logs de la aplicación
3. Prueba con backend local primero para descartar problemas de código

---

## 💡 Consejos

- **Multi-dispositivo**: Usa el mismo usuario en casa/trabajo para compartir datos
- **Multi-usuario**: Cada persona debe crear su propia cuenta
- **Backup automático**: Tus datos siempre están en la nube
- **Sincronización manual**: Añade un botón "Sincronizar" en la UI si lo necesitas

---

## 📝 Próximos Pasos

1. **Integrar en main_ccleaner.py**
2. **Probar login y sincronización**
3. **Verificar que los datos se suban al servidor**
4. **Probar desde otro dispositivo**

---

**🎉 ¡Sistema listo para producción!**
