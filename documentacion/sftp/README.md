# 📁 Documentación SFTP

Documentación detallada sobre la implementación y uso del sistema de sincronización SFTP en Guardias de Patio.

---

## 📚 Archivos Disponibles

### 1. [GUIA_SINCRONIZACION_SFTP.md](GUIA_SINCRONIZACION_SFTP.md)

**Guía completa de sincronización SFTP**

- ✅ Configuración del servidor SFTP
- ✅ Estructura de carpetas
- ✅ Operaciones de sincronización
- ✅ Manejo de errores
- ✅ Ejemplos de código

**Cuándo consultar:** Para entender cómo funciona la sincronización SFTP y cómo configurarla.

---

### 2. [INTEGRACION_COMPLETA_SFTP.md](INTEGRACION_COMPLETA_SFTP.md)

**Integración completa del sistema SFTP**

- ✅ Arquitectura del sistema de sincronización
- ✅ Implementación de SFTPBackend
- ✅ Integración con SessionLock
- ✅ Casos de uso completos
- ✅ Testing y validación

**Cuándo consultar:** Para entender la arquitectura completa de la integración SFTP en el proyecto.

---

### 3. [NOTA_RUTAS_SFTP.md](NOTA_RUTAS_SFTP.md)

**Notas sobre rutas y paths SFTP**

- ✅ Estructura de rutas local vs servidor
- ✅ Conversión de rutas Windows/Unix
- ✅ Manejo de rutas relativas/absolutas
- ✅ Problemas comunes y soluciones

**Cuándo consultar:** Para resolver problemas con rutas de archivos en SFTP.

---

### 4. [RESUMEN_INTEGRACION_SFTP.md](RESUMEN_INTEGRACION_SFTP.md)

**Resumen ejecutivo de la integración SFTP**

- ✅ Resumen de implementación
- ✅ Características principales
- ✅ Estado del proyecto
- ✅ Próximos pasos

**Cuándo consultar:** Para obtener un overview rápido del estado de la integración SFTP.

---

## 🎯 Navegación Rápida

| Necesitas... | Consulta |
|-------------|----------|
| **Configurar SFTP** | [GUIA_SINCRONIZACION_SFTP.md](GUIA_SINCRONIZACION_SFTP.md) |
| **Entender arquitectura** | [INTEGRACION_COMPLETA_SFTP.md](INTEGRACION_COMPLETA_SFTP.md) |
| **Resolver problemas de rutas** | [NOTA_RUTAS_SFTP.md](NOTA_RUTAS_SFTP.md) |
| **Ver resumen ejecutivo** | [RESUMEN_INTEGRACION_SFTP.md](RESUMEN_INTEGRACION_SFTP.md) |

---

## 🔗 Documentación Relacionada

- 📋 [Guía de Sincronización](../GUIA_SINCRONIZACION.md) - Guía completa de sincronización multi-usuario
- 📋 [Configuración Email](../CONFIGURACION_EMAIL.md) - Configurar servidor SMTP
- 📋 [Requisitos Sistema](../REQUISITOS_SISTEMA.md) - Requisitos mínimos

---

## 🛠️ Configuración Rápida

### 1. Variables de Entorno

Crear archivo `.env` en la raíz del proyecto:

```env
SFTP_HOST=home491590459.1and1-data.host
SFTP_PORT=22
SFTP_USERNAME=u109936159
SFTP_PASSWORD=tu_password_aqui
SFTP_BASE_DIR=/guardias_patio
```

### 2. Estructura en Servidor

```
/guardias_patio/              # Base dir configurado en .env
└── users/
    └── <hash_usuario>/
        ├── guardias_patio.db  # Base de datos
        ├── session.lock       # Bloqueo de sesión
        └── last_sync.json     # Metadatos de sync
```

### 3. Verificar Conexión

```python
from src.sync.sftp_backend import SFTPBackend
from pathlib import Path

# Test de conexión
backend = SFTPBackend()
backend.connect()
print("✅ Conexión SFTP exitosa")
backend.disconnect()
```

---

## ⚠️ Problemas Comunes

### Error: "No se puede conectar al servidor SFTP"

**Solución:**
1. Verificar credenciales en `.env`
2. Verificar que el servidor esté accesible
3. Verificar firewall/VPN

**Ver:** [GUIA_SINCRONIZACION_SFTP.md](GUIA_SINCRONIZACION_SFTP.md#solución-de-problemas)

### Error: "FileNotFoundError" en rutas

**Solución:**
1. Verificar estructura de carpetas en servidor
2. Verificar permisos de lectura/escritura
3. Usar rutas absolutas en configuración

**Ver:** [NOTA_RUTAS_SFTP.md](NOTA_RUTAS_SFTP.md)

### Error: "Sesión bloqueada"

**Solución:**
1. Cerrar sesión en otro dispositivo
2. Esperar 5 minutos (timeout automático)
3. Eliminar `session.lock` manualmente del servidor

**Ver:** [GUIA_SINCRONIZACION.md](../GUIA_SINCRONIZACION.md#sistema-de-bloqueo-de-sesión)

---

## 📊 Estado de Implementación

| Característica | Estado |
|---------------|--------|
| **Conexión SFTP** | ✅ Completo |
| **Upload/Download DB** | ✅ Completo |
| **Session Lock** | ✅ Completo |
| **Heartbeat** | ✅ Completo |
| **Manejo de errores** | ✅ Completo |
| **Tests unitarios** | ✅ Completo |
| **Documentación** | ✅ Completo |

---

**Proyecto:** Guardias de Patio  
**Versión:** 2.8+  
**Última actualización:** 26 de Octubre de 2025
