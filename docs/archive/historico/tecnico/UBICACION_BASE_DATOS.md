# Ubicación de la Base de Datos SQLite

## ⚠️ IMPORTANTE: Única BD Válida

La aplicación **solo debe usar** la base de datos ubicada en:

```
data/users/{user_hash}/guardias_patio.db
```

Donde `{user_hash}` es el hash SHA256 del `user_id` (primeros 16 caracteres).

### Ejemplo para usuario "Jefatura_FpBach":
```
data/users/0db13e2857239ed8/guardias_patio.db
```

## 🚫 Ubicaciones INCORRECTAS (NO USAR)

Las siguientes ubicaciones son **obsoletas** y deben eliminarse si existen:

- ❌ `guardias_patio.db` (raíz del proyecto)
- ❌ `src/guardias_patio.db` (dentro de src/)
- ❌ `data/{hash}/guardias_patio.db` (estructura antigua)
- ❌ `data/users/{hash}/guardias.db` (nombre incorrecto)

## 📁 Estructura Correcta del Usuario

```
data/users/0db13e2857239ed8/
├── guardias_patio.db          ← BD SQLite (ÚNICA FUENTE DE VERDAD)
└── guardias_patio_data.json   ← Export/Import/Backup/Sync
```

## 🔧 Cómo Funciona

### 1. Inicialización de BD
```python
from database.db_manager import initialize_user_database

engine, SessionFactory = initialize_user_database(user_id)
# Crea automáticamente: data/users/{hash}/guardias_patio.db
```

### 2. Función de Hash
```python
def _hash_user_id(user_id: str) -> str:
    return hashlib.sha256(user_id.encode()).hexdigest()[:16]
```

### 3. Path Resultante
```python
user_hash = _hash_user_id("Jefatura_FpBach")
# → "0db13e2857239ed8"

db_path = USER_DATA_DIR / user_hash / "guardias_patio.db"
# → data/users/0db13e2857239ed8/guardias_patio.db
```

## 🧹 Limpieza de BDs Obsoletas

Si encuentras bases de datos en ubicaciones incorrectas, elimínalas:

```bash
# Desde la raíz del proyecto
rm -f guardias_patio.db
rm -f src/guardias_patio.db
rm -f data/0db13e2857239ed8/guardias_patio.db
rm -f data/users/0db13e2857239ed8/guardias.db
```

**✅ Solo debe quedar:**
```bash
data/users/0db13e2857239ed8/guardias_patio.db
```

## 📝 Historial de Cambios

### 2025-11-01: Limpieza de BDs Duplicadas
- **Problema**: Existían 5 archivos `.db` en diferentes ubicaciones
- **Causa**: Scripts antiguos creaban BDs en ubicaciones incorrectas
- **Solución**: Eliminadas 4 BDs obsoletas, solo se mantiene la de `data/users/{hash}/`
- **BDs eliminadas**:
  - `guardias_patio.db` (raíz, 4KB, vacía)
  - `src/guardias_patio.db` (64KB, obsoleta)
  - `data/0db13e2857239ed8/guardias_patio.db` (0B, vacía)
  - `data/users/0db13e2857239ed8/guardias.db` (0B, nombre incorrecto)
- **BD activa**: `data/users/0db13e2857239ed8/guardias_patio.db` (80KB, 67 profesores)

## 🔍 Verificación

Para verificar que solo existe una BD:

```bash
find . -name "*.db" -type f
# Debe mostrar SOLO: ./data/users/0db13e2857239ed8/guardias_patio.db
```

Para verificar que funciona correctamente:

```python
from database.db_manager import initialize_user_database
from models.models import Profesor

engine, SessionFactory = initialize_user_database('Jefatura_FpBach')
session = SessionFactory()

print(f"BD activa: {engine.url}")
print(f"Total profesores: {session.query(Profesor).count()}")

session.close()
```

**Salida esperada:**
```
BD activa: sqlite:////path/to/data/users/0db13e2857239ed8/guardias_patio.db
Total profesores: 67
```

## ⚙️ Configuración de Git

El archivo `.gitignore` ya está configurado para ignorar archivos `.db`:

```gitignore
# Base de datos de desarrollo
guardias_patio.db
*.db

# Archivos temporales de SQLite
*.db-shm
*.db-wal
```

Sin embargo, si un archivo `.db` ya fue commiteado previamente a git, debes eliminarlo del índice:

```bash
# Eliminar del índice de git (pero mantener el archivo local)
git rm --cached guardias_patio.db
git rm --cached src/guardias_patio.db
git commit -m "chore: Eliminar BDs del control de versiones"
```

## 🎯 Mejores Prácticas

1. **Scripts**: Siempre usar `initialize_user_database(user_id)` en lugar de `SessionLocal()`
2. **Testing**: Usar BDs de prueba en memoria: `sqlite:///:memory:`
3. **Backups**: Usar el sistema de export/import JSON, no copiar el `.db`
4. **Sync**: El sync con la nube usa JSON, no la BD directamente
5. **Multi-usuario**: Cada usuario tiene su propia BD en `data/users/{hash}/`

## 📚 Referencias

- `src/database/db_manager.py`: Gestión de BDs por usuario
- `src/core/paths.py`: Función `get_user_data_directory()`
- `documentacion/PLAN_MIGRACION_SOLO_BD.md`: Plan de arquitectura BD-céntrica
