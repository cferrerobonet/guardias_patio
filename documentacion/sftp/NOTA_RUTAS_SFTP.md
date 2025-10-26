# 📝 Nota Importante: Rutas en el Sistema SFTP

## ⚠️ Problema Resuelto: Duplicación de Rutas

**Problema detectado**: Las rutas se duplicaban en el servidor SFTP:
```
❌ INCORRECTO: /aplicaciones/guardias_patio/aplicaciones/guardias_patio/test_connection
```

**Causa**: El `remote_path` pasado a los métodos del backend incluía `base_dir`, y el backend lo añadía otra vez.

---

## ✅ Solución: Rutas Relativas

### Configuración en `.env`

```env
SFTP_BASE_DIR=/aplicaciones/guardias_patio
```

Este es el **directorio base** en el servidor SFTP donde se almacenarán todos los datos.

### Uso Correcto de los Métodos del Backend

Los métodos del backend (`upload_file`, `download_file`, `file_exists`, `get_last_modified`) esperan **rutas RELATIVAS** al `base_dir`:

```python
# ✅ CORRECTO: Rutas relativas al base_dir
backend = SFTPSyncBackend(
    host="...",
    port=22,
    username="...",
    password="...",
    base_dir="/aplicaciones/guardias_patio"  # Base configurado
)

# Usar rutas RELATIVAS (sin incluir base_dir)
backend.upload_file(local_file, "users/abc123/guardias_patio.db")
backend.upload_file(local_file, "test_connection/test.txt")
backend.file_exists("users/abc123/config.json")

# El backend construye automáticamente:
# /aplicaciones/guardias_patio/users/abc123/guardias_patio.db
# /aplicaciones/guardias_patio/test_connection/test.txt
# /aplicaciones/guardias_patio/users/abc123/config.json
```

```python
# ❌ INCORRECTO: NO incluir base_dir en el remote_path
backend.upload_file(local_file, "/aplicaciones/guardias_patio/users/abc123/guardias_patio.db")
# Resultado: /aplicaciones/guardias_patio/aplicaciones/guardias_patio/users/abc123/guardias_patio.db
#                                        ⬆️ DUPLICADO
```

---

## 📂 Estructura Final en el Servidor

```
/aplicaciones/guardias_patio/           ← base_dir configurado
├── users.json
└── users/
    ├── abc123def456/                   ← Hash del usuario 1
    │   ├── guardias_patio.db
    │   ├── config.json
    │   └── last_sync.json
    └── xyz789ghi012/                   ← Hash del usuario 2
        ├── guardias_patio.db
        ├── config.json
        └── last_sync.json
```

---

## 🔧 Ejemplo de SyncManager

El `SyncManager` ya usa correctamente las rutas relativas:

```python
class SyncManager:
    def __init__(self, backend: SyncBackend, user_id: str):
        self.backend = backend
        self.user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:16]
        # ...
    
    def sync_on_startup(self) -> bool:
        # ✅ Ruta relativa: "users/{hash}/guardias_patio.db"
        remote_db_path = f"users/{self.user_hash}/guardias_patio.db"
        
        # El backend construye: /aplicaciones/guardias_patio/users/{hash}/guardias_patio.db
        if self.backend.file_exists(remote_db_path):
            self.backend.download_file(remote_db_path, local_db)
```

---

## 🎯 Resumen

**Regla simple**: 

1. **`base_dir`** se configura **una sola vez** en `.env`
2. **Todos los `remote_path`** son **relativos** a `base_dir`
3. **Nunca** incluyas `base_dir` en los `remote_path`

```python
# ✅ BIEN
backend.upload_file(file, "users/abc123/data.db")

# ❌ MAL
backend.upload_file(file, "/aplicaciones/guardias_patio/users/abc123/data.db")
```

---

**Problema resuelto** ✅ - Las rutas ahora funcionan correctamente sin duplicación.
